"""
Procesador para datos de stock crítico
REESCRITO para funcionar igual que siciap_app - Manejo flexible de códigos y lotes
"""
import pandas as pd
from sqlalchemy import text
from etl.processors.base_processor import BaseProcessor
import logging

logger = logging.getLogger(__name__)


class StockProcessor(BaseProcessor):
    def process_file(self, file_content, filename):
        try:
            df = pd.read_excel(file_content, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]

            # Mapeo siciap_app
            column_mapping = {
                'Codigo': 'codigo',
                'Código': 'codigo',
                'Producto': 'producto',
                'Concentracion': 'concentracion',
                'Concentración': 'concentracion',
                'Forma Farmaceutica': 'forma_farmaceutica',
                'Forma Farmacéutica': 'forma_farmaceutica',
                'Presentacion': 'presentacion',
                'Presentación': 'presentacion',
                'Clasificacion': 'clasificacion',
                'Clasificación': 'clasificacion',
                'Meses en Movimiento': 'meses_en_movimiento',
                'Cantidad Distribuida': 'cantidad_distribuida',
                'Stock Actual': 'stock_actual',
                'Stock Reservado': 'stock_reservado',
                'Stock Disponible': 'stock_disponible',
                'DMP': 'dmp',
                'Estado Stock': 'estado_stock',
                'Stock Hosp': 'stock_hosp',
                'OC': 'oc'
            }

            df = df.rename(columns=column_mapping)
            valid_cols = [c for c in df.columns if c in column_mapping.values()]
            df = df[valid_cols]

            # --- CORRECCIONES ---
            # 1. CODIGO como TEXTO (puede tener guiones, letras, etc.)
            if 'codigo' in df.columns:
                df['codigo'] = df['codigo'].astype(str).str.strip()
                df['codigo'] = df['codigo'].replace(['nan', 'NaT', 'None', 'NaN'], '')

            # 2. ELIMINAR DUPLICADOS POR CODIGO (Soluciona error UniqueViolation)
            if 'codigo' in df.columns:
                filas_antes = len(df)
                df = df.drop_duplicates(subset=['codigo'], keep='first')
                filas_despues = len(df)
                if filas_antes > filas_despues:
                    logger.warning(f"⚠️ Se eliminaron {filas_antes - filas_despues} filas duplicadas por código para evitar errores.")

            # 3. AGREGAR COLUMNAS FALTANTES CON VALORES POR DEFECTO
            if 'stock_hosp' not in df.columns:
                df['stock_hosp'] = None
                logger.info("Columna 'stock_hosp' no encontrada, se usará NULL")
            if 'oc' not in df.columns:
                df['oc'] = None
                logger.info("Columna 'oc' no encontrada, se usará NULL")

            # 4. TEXTOS
            text_cols = ['producto', 'concentracion', 'forma_farmaceutica', 'presentacion', 
                        'clasificacion', 'estado_stock', 'oc']
            for col in text_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace(['nan', 'NaT', 'None', 'NaN'], '')
                    # Convertir strings vacíos a None para SQL
                    df[col] = df[col].apply(lambda x: None if x == '' else x)

            # 5. NUMEROS
            num_cols = ['meses_en_movimiento', 'cantidad_distribuida', 'stock_actual', 
                       'stock_reservado', 'stock_disponible', 'dmp', 'stock_hosp']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    # Mantener NaN como None para SQL (no fillna(0))
                    df[col] = df[col].where(pd.notnull(df[col]), None)

            # --- INSERCIÓN ROBUSTA (Transaction + Delete + Insert) ---
            if not df.empty:
                conn = None
                try:
                    conn = self.get_connection()
                    trans = conn.begin()
                    try:
                        # 1. Borrar tabla completa (como hacía tu app vieja)
                        conn.execute(text("DELETE FROM siciap.stock_critico"))
                        
                        # 2. Insertar nuevos datos
                        df.to_sql('stock_critico', conn, schema='siciap', if_exists='append', index=False)
                        
                        trans.commit()
                        logger.info(f"✅ Stock crítico importado: {len(df)} registros.")
                        return True
                    except Exception as e:
                        try:
                            trans.rollback()
                        except Exception as rollback_err:
                            logger.warning(f"Error en rollback (puede ser normal si la transacción ya estaba cerrada): {rollback_err}")
                        logger.error(f"❌ Error insertando en BD: {str(e)}")
                        raise e
                    finally:
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass
                except Exception as e:
                    logger.error(f"❌ Error de conexión: {str(e)}")
                    raise e
            return False

        except Exception as e:
            logger.error(f"Error procesando stock: {str(e)}")
            raise e
