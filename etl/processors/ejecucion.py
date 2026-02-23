"""
Procesador para datos de ejecución
REESCRITO para funcionar igual que siciap_app - Permite NULL en item
"""
import pandas as pd
from sqlalchemy import text
from etl.processors.base_processor import BaseProcessor
import logging

logger = logging.getLogger(__name__)


class EjecucionProcessor(BaseProcessor):
    def process_file(self, file_content, filename):
        try:
            df = pd.read_excel(file_content, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]

            # Mapeo de siciap_app
            column_mapping = {
                'Id. Llamado': 'id_llamado',
                'Id.Llamado': 'id_llamado',
                'Llamado': 'licitacion',
                'Licitación': 'licitacion',
                'Licitacion': 'licitacion',
                'Proveedor': 'proveedor',
                'Codigo': 'codigo',
                'Código': 'codigo',
                'Medicamento': 'medicamento',
                'Producto': 'medicamento',
                'Item': 'item',  # <--- PUEDE SER NULL
                'Cantidad Máxima': 'cantidad_maxima',
                'Cantidad Maxima': 'cantidad_maxima',
                'Cantidad Emitida': 'cantidad_emitida',
                'Cantidad Recepcionada': 'cantidad_recepcionada',
                'Cantidad Distribuida': 'cantidad_distribuida',
                'Monto Adjudicado': 'monto_adjudicado',
                'Monto Emitido': 'monto_emitido',
                'Saldo': 'saldo',
                'Porcentaje Emitido': 'porcentaje_emitido',
                'Ejecucion Mayor al 50': 'ejecucion_mayor_al_50',
                'Estado Stock': 'estado_stock',
                'Estado Contrato': 'estado_contrato',
                'Cantidad Ampliacion': 'cantidad_ampliacion',
                'Porcentaje Ampliado': 'porcentaje_ampliado',
                'Porcentaje Ampliacion Emitido': 'porcentaje_ampliacion_emitido',
                'Obs': 'obs',
                'Observaciones': 'obs'
            }

            df = df.rename(columns=column_mapping)
            valid_cols = [c for c in df.columns if c in column_mapping.values()]
            df = df[valid_cols]

            # --- CORRECCIONES CRÍTICAS ---
            # A) ITEM, CODIGO, ID_LLAMADO -> TEXTO (Evita error '2-2.2' y nulos)
            text_cols = ['item', 'codigo', 'id_llamado', 'licitacion', 'proveedor', 'medicamento', 
                        'estado_stock', 'estado_contrato', 'ejecucion_mayor_al_50', 'obs']
            for col in text_cols:
                if col in df.columns:
                    # Convertir a string, pero manejar NaN correctamente
                    df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) and str(x).strip() not in ['nan', 'NaT', 'None', 'NaN', ''] else None)

            # B) ELIMINAR DUPLICADOS DEL EXCEL (Soluciona error UniqueViolation)
            # Si hay dos filas con el mismo ID, Licitacion, Codigo e Item, borramos la segunda.
            subset_dup = [c for c in ['id_llamado', 'licitacion', 'codigo', 'item'] if c in df.columns]
            if subset_dup:
                filas_antes = len(df)
                df = df.drop_duplicates(subset=subset_dup, keep='first')
                filas_despues = len(df)
                if filas_antes > filas_despues:
                    logger.warning(f"⚠️ Se eliminaron {filas_antes - filas_despues} filas duplicadas en el Excel para evitar errores.")

            # C) NÚMEROS (Limpieza de moneda y cantidades)
            num_cols = ['cantidad_maxima', 'cantidad_emitida', 'cantidad_recepcionada', 'cantidad_distribuida',
                       'monto_adjudicado', 'monto_emitido', 'saldo', 'porcentaje_emitido',
                       'cantidad_ampliacion', 'porcentaje_ampliado', 'porcentaje_ampliacion_emitido']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # --- INSERCIÓN ROBUSTA (Transaction + Delete + Insert) ---
            if not df.empty:
                conn = None
                try:
                    conn = self.get_connection()
                    trans = conn.begin()
                    try:
                        # 1. Borrar tabla completa (como hacía tu app vieja)
                        conn.execute(text("DELETE FROM siciap.ejecucion"))
                        
                        # 2. Insertar nuevos datos
                        # if_exists='append' porque ya borramos manualmente arriba
                        df.to_sql('ejecucion', conn, schema='siciap', if_exists='append', index=False)
                        
                        trans.commit()
                        logger.info(f"✅ Ejecución importada: {len(df)} registros.")
                        return True
                    except Exception as e:
                        # Rollback explícito para limpiar la transacción inválida
                        try:
                            trans.rollback()
                        except Exception as rollback_err:
                            logger.warning(f"Error en rollback (puede ser normal si la transacción ya estaba cerrada): {rollback_err}")
                        logger.error(f"❌ Error insertando en BD: {str(e)}")
                        raise e
                    finally:
                        # Cerrar conexión explícitamente para evitar conexiones "sucias"
                        if conn is not None:
                            try:
                                conn.close()
                            except Exception:
                                pass
                except Exception as e:
                    # Si falla antes de crear la conexión o después de cerrarla
                    logger.error(f"❌ Error de conexión: {str(e)}")
                    raise e
            return False

        except Exception as e:
            logger.error(f"Error procesando ejecucion: {str(e)}")
            raise e
