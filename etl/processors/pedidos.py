"""
Procesador para datos de pedidos
REESCRITO para funcionar igual que siciap_app - Sin restricciones de tipos para IDs
"""
import pandas as pd
from sqlalchemy import text
from etl.processors.base_processor import BaseProcessor
import logging
import warnings

logger = logging.getLogger(__name__)


def safe_date_conversion(date_series):
    """
    Convierte fechas de forma segura sin warnings, con soporte mejorado para formatos españoles
    Replicado de siciap_app.py
    """
    if date_series is None or (isinstance(date_series, pd.Series) and len(date_series) == 0):
        return date_series

    # Suprimir warnings temporalmente para esta función
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        # Si date_series es una serie, procesar toda la serie
        if isinstance(date_series, pd.Series):
            # Limpiar valores problemáticos
            date_series = date_series.astype(str).replace(['nan', 'NaT', 'None', '', 'NaN'], None)
            
            # Métodos por orden de preferencia
            methods = [
                # 1. Intentar con dayfirst=True para formato español DD/MM/YYYY
                lambda: pd.to_datetime(date_series, dayfirst=True, errors='coerce'),
                # 2. Formato específico DD/MM/YYYY
                lambda: pd.to_datetime(date_series, format='%d/%m/%Y', errors='coerce'),
                # 3. Formato específico DD-MM-YYYY
                lambda: pd.to_datetime(date_series, format='%d-%m-%Y', errors='coerce'),
                # 4. Formato con horas DD/MM/YYYY HH:MM:SS
                lambda: pd.to_datetime(date_series, format='%d/%m/%Y %H:%M:%S', errors='coerce'),
                # 5. Último recurso: pd.to_datetime genérico
                lambda: pd.to_datetime(date_series, errors='coerce')
            ]
            
            # Intentar cada método
            for method in methods:
                try:
                    result = method()
                    # Si tenemos al menos una fecha válida, usar este método
                    if not result.isna().all():
                        return result
                except Exception:
                    continue
            
            # Si todo falla, usar el método más genérico
            return pd.to_datetime(date_series, errors='coerce')
        else:
            # Si es un valor único, convertirlo a string y procesarlo
            if pd.isna(date_series) or date_series is None:
                return None
            
            date_str = str(date_series)
            if date_str.strip() in ['nan', 'NaT', 'None', '', 'NaN']:
                return None
                
            try:
                return pd.to_datetime(date_str, dayfirst=True)
            except Exception:
                try:
                    return pd.to_datetime(date_str, format='%d/%m/%Y')
                except Exception:
                    try:
                        return pd.to_datetime(date_str, format='%d-%m-%Y')
                    except Exception:
                        try:
                            return pd.to_datetime(date_str)
                        except Exception:
                            return None


class PedidosProcessor(BaseProcessor):
    def process_file(self, file_content, filename):
        try:
            df = pd.read_excel(file_content, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]

            column_mapping = {
                'Nro Pedido': 'nro_pedido',
                'Nro. Pedido': 'nro_pedido',
                'Simese': 'simese',
                'SIMESE': 'simese',
                'Fecha Pedido': 'fecha_pedido',
                'Codigo': 'codigo',
                'Código': 'codigo',
                'Medicamento': 'medicamento',
                'Stock': 'stock',
                'DMP': 'dmp',
                'Cantidad': 'cantidad',
                'Meses Cantidad': 'meses_cantidad',
                'Dias Transcurridos': 'dias_transcurridos',
                'Estado': 'estado',
                'Prioridad': 'prioridad',
                'Nro OC': 'nro_oc',
                'Nro. OC': 'nro_oc',
                'Fecha OC': 'fecha_oc',
                'Opciones': 'opciones'
            }

            df = df.rename(columns=column_mapping)
            valid_cols = [c for c in df.columns if c in column_mapping.values()]
            df = df[valid_cols]

            # --- CORRECCIONES PREVENTIVAS ---
            # A) ELIMINAR DUPLICADOS (preventivo, por si acaso)
            if 'nro_pedido' in df.columns and 'codigo' in df.columns:
                filas_antes = len(df)
                df = df.drop_duplicates(subset=['nro_pedido', 'codigo'], keep='first')
                filas_despues = len(df)
                if filas_antes > filas_despues:
                    logger.warning(f"⚠️ Se eliminaron {filas_antes - filas_despues} filas duplicadas en pedidos.")

            # B) nro_pedido como TEXTO SIEMPRE (puede tener formato especial)
            if 'nro_pedido' in df.columns:
                df['nro_pedido'] = df['nro_pedido'].apply(lambda x: str(x).strip() if pd.notnull(x) and str(x).strip() not in ['nan', 'NaT', 'None', 'NaN', ''] else None)

            # C) TEXTOS
            text_cols = ['simese', 'codigo', 'medicamento', 'estado', 'prioridad', 'nro_oc', 'opciones']
            for col in text_cols:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) and str(x).strip() not in ['nan', 'NaT', 'None', 'NaN', ''] else None)

            # D) NUMEROS (mantener NaN como None para SQL)
            num_cols = ['stock', 'dmp', 'cantidad', 'meses_cantidad', 'dias_transcurridos']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].where(pd.notnull(df[col]), None)

            # E) FECHAS (usar safe_date_conversion para evitar warnings)
            date_cols = ['fecha_pedido', 'fecha_oc']
            for col in date_cols:
                if col in df.columns:
                    df[col] = safe_date_conversion(df[col])
                    df[col] = df[col].where(pd.notnull(df[col]), None)

            # --- INSERCIÓN ROBUSTA ---
            if not df.empty:
                conn = None
                try:
                    conn = self.get_connection()
                    trans = conn.begin()
                    try:
                        conn.execute(text("DELETE FROM siciap.pedidos"))
                        df.to_sql('pedidos', conn, schema='siciap', if_exists='append', index=False)
                        trans.commit()
                        logger.info(f"✅ Pedidos importados: {len(df)} registros.")
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
            logger.error(f"Error procesando pedidos: {str(e)}")
            raise e
