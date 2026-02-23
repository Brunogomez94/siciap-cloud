"""
Procesador para datos de órdenes
REESCRITO para funcionar igual que siciap_app - Sin restricciones estúpidas
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


class OrdenesProcessor(BaseProcessor):
    def process_file(self, file_content, filename):
        try:
            # Leer como en siciap_app (motor openpyxl)
            df = pd.read_excel(file_content, engine='openpyxl')
            
            # Normalizar columnas
            df.columns = [str(c).strip() for c in df.columns]

            # Mapeo EXACTO de siciap_app
            column_mapping = {
                'Id.Llamado': 'id_llamado',
                'Llamado': 'llamado',
                'P.Unit.': 'p_unit',
                'Fec.Contrato': 'fec_contrato',
                'OC': 'oc',
                'Item': 'item',
                'Codigo': 'codigo',
                'Código': 'codigo',
                'Producto': 'producto',
                'Cant. OC': 'cant_oc',
                'Monto OC': 'monto_oc',
                'Monto Recepcion': 'monto_recepcion',
                'Monto Recepción': 'monto_recepcion',
                'Monto Recepciòn': 'monto_recepcion',
                'Cant. Recep.': 'cant_recep',
                'Monto Saldo': 'monto_saldo',
                'Dias de Atraso': 'dias_de_atraso',
                'Estado': 'estado',
                'Stock': 'stock',
                'Referencia': 'referencia',
                'Proveedor': 'proveedor',
                'Lugar Entrega OC': 'lugar_entrega_oc',
                'Lugar Entrega': 'lugar_entrega_oc',
                'Fec. Ult. Recep.': 'fec_ult_recep',
                'Fecha Recibido Proveedor': 'fecha_recibido_proveedor',
                'Fecha Recibido Poveedor': 'fecha_recibido_proveedor',
                'Fecha OC': 'fecha_oc',
                'Saldo': 'saldo',
                'Plazo Entrega': 'plazo_entrega',
                'Tipo Vigencia': 'tipo_vigencia',
                'Vigencia': 'vigencia',
                'Det. Recep.': 'det_recep'
            }

            df = df.rename(columns=column_mapping)
            valid_cols = [c for c in df.columns if c in column_mapping.values()]
            df = df[valid_cols]

            # --- CORRECCIONES CRÍTICAS ---
            # 1. ITEM, CODIGO, OC -> TEXTO SIEMPRE (acepta "2-2.2")
            text_cols = ['item', 'codigo', 'oc', 'llamado', 'producto', 'estado', 'stock', 
                         'referencia', 'proveedor', 'lugar_entrega_oc', 'plazo_entrega',
                         'tipo_vigencia', 'vigencia', 'det_recep']
            for col in text_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    df[col] = df[col].replace(['nan', 'NaT', 'None', 'NaN'], '')

            # id_llamado como texto también (puede venir con guiones)
            if 'id_llamado' in df.columns:
                df['id_llamado'] = df['id_llamado'].astype(str).str.strip()
                df['id_llamado'] = df['id_llamado'].replace(['nan', 'NaT', 'None', 'NaN'], '')

            # 2. LIMPIEZA DE NÚMEROS (Si falla, pone 0)
            numeric_cols = ['cant_oc', 'monto_oc', 'saldo', 'p_unit', 'cant_recep', 'monto_recepcion', 'monto_saldo', 'dias_de_atraso']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # 3. FECHAS (como VARCHAR en siciap_app, no DATE)
            # Usar safe_date_conversion para evitar warnings y manejar múltiples formatos
            date_cols = ['fecha_oc', 'fec_contrato', 'fec_ult_recep', 'fecha_recibido_proveedor']
            for col in date_cols:
                if col in df.columns:
                    df[col] = safe_date_conversion(df[col])
                    df[col] = df[col].dt.strftime('%d/%m/%Y').replace('NaT', '')

            # 4. DEDUPLICAR: misma OC + ítem + producto/código → una sola fila (la de fecha más reciente)
            # Así no replicamos en la nube los duplicados que vengan del Excel.
            subset_cols = [c for c in ['oc', 'item', 'codigo'] if c in df.columns]
            if len(subset_cols) >= 2:
                antes = len(df)
                if 'fecha_oc' in df.columns:
                    df['_fecha_oc_ord'] = pd.to_datetime(df['fecha_oc'], dayfirst=True, errors='coerce')
                    df = df.sort_values(by='_fecha_oc_ord', ascending=False, na_position='last')
                    df = df.drop(columns=['_fecha_oc_ord'])
                df = df.drop_duplicates(subset=subset_cols, keep='first')
                duplicados_eliminados = antes - len(df)
                if duplicados_eliminados > 0:
                    logger.info(f"🔄 Órdenes: se eliminaron {duplicados_eliminados} filas duplicadas (misma OC + ítem + código).")

            if not df.empty:
                conn = None
                try:
                    conn = self.get_connection()
                    trans = conn.begin()
                    try:
                        conn.execute(text("DELETE FROM siciap.ordenes"))
                        df.to_sql('ordenes', conn, schema='siciap', if_exists='append', index=False)
                        trans.commit()
                        logger.info(f"✅ Órdenes importadas: {len(df)} registros.")
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
            logger.error(f"Error procesando ordenes: {str(e)}")
            raise e
