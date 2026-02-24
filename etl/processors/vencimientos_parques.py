"""
Procesador para vencimientos en parques (vencimientos_parques / vencimientos_pnc)
REESCRITO para funcionar igual que siciap_app - Sin restricciones estúpidas
"""
import csv
import io
import pandas as pd
from sqlalchemy import text
from etl.processors.base_processor import BaseProcessor
import logging
import warnings

logger = logging.getLogger(__name__)


def _read_csv_safe(file_content) -> pd.DataFrame:
    """Lee CSV sin usar pd.read_csv (evita problemas con argumento 'errors' en algunas versiones)."""
    buf = file_content if isinstance(file_content, (bytes, bytearray)) else file_content.read()
    text_content = None
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            text_content = buf.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text_content is None:
        text_content = buf.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text_content))
    rows = list(reader)
    if not rows:
        return pd.DataFrame()
    headers = [str(h).strip() for h in rows[0]]
    data = rows[1:]
    return pd.DataFrame(data, columns=headers)


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


class VencimientosParquesProcessor(BaseProcessor):
    """Procesador para vencimientos de productos en parques"""

    def process_file(self, file_content, filename):
        try:
            # Este proceso no carga desde stock_critico ni ejecución; solo desde el archivo subido.
            logger.info(
                "Vencimientos (PNC/parques): carga desde archivo subido; "
                "no se usa stock_critico ni ejecución."
            )
            # Leer CSV: pd.read_csv() NO tiene parámetro "errors". Solo encoding= y, si acaso, on_bad_lines=.
            if filename.lower().endswith('.csv'):
                buf = io.BytesIO(file_content) if isinstance(file_content, bytes) else file_content
                try:
                    df = pd.read_csv(buf, encoding="utf-8")
                except UnicodeDecodeError:
                    buf = io.BytesIO(file_content) if isinstance(file_content, bytes) else file_content
                    df = pd.read_csv(buf, encoding="latin-1")
            else:
                buf = io.BytesIO(file_content) if isinstance(file_content, bytes) else file_content
                df = pd.read_excel(buf, engine='openpyxl')
            
            df.columns = [str(c).strip() for c in df.columns]

            # Mapeo de columnas
            column_mapping = {
                "codigo": "codigo",
                "Codigo": "codigo",
                "Código": "codigo",
                "codigo_producto": "codigo",
                "descripcion": "descripcion",
                "Descripcion": "descripcion",
                "Descripción": "descripcion",
                "nombre_producto": "descripcion",
                "producto_completo": "descripcion",
                "fec_vencimiento": "fec_vencimiento",
                "fecha_vencimiento": "fec_vencimiento",
                "Fecha Vencimiento": "fec_vencimiento",
                "Vencimiento": "fec_vencimiento",
                "stock_disponible": "stock_disponible",
                "Stock": "stock_disponible",
                "stock": "stock_disponible",
                "valores_de_medidas": "stock_disponible",
                "parque": "parque",
                "Parque": "parque",
                "nombre_sucursal": "parque",
                "observaciones": "observaciones",
                "Observaciones": "observaciones",
            }

            # CSV tipo Stock_en_PNCs: filtrar solo "Stock Disponible"
            col_medidas = None
            for c in ["Nombres de medidas", "nombres_de_medidas", "nombres de medidas"]:
                if c in df.columns:
                    col_medidas = c
                    break
            col_valores = None
            for c in ["Valores de medidas", "valores_de_medidas", "valores de medidas"]:
                if c in df.columns:
                    col_valores = c
                    break
            if col_medidas is not None and col_valores is not None:
                df = df[df[col_medidas].astype(str).str.strip().str.upper() == "STOCK DISPONIBLE"].copy()
                df = df.rename(columns={col_valores: "stock_disponible"})

            df = df.rename(columns=column_mapping)
            valid_cols = [c for c in df.columns if c in column_mapping.values()]
            df = df[valid_cols]

            # --- CORRECCIONES PREVENTIVAS ---
            # A) ELIMINAR DUPLICADOS (por codigo + parque + fecha)
            subset_dup = [c for c in ['codigo', 'parque', 'fec_vencimiento'] if c in df.columns]
            if subset_dup:
                filas_antes = len(df)
                df = df.drop_duplicates(subset=subset_dup, keep='first')
                filas_despues = len(df)
                if filas_antes > filas_despues:
                    logger.warning(f"⚠️ Se eliminaron {filas_antes - filas_despues} filas duplicadas en vencimientos.")

            # B) CODIGO como TEXTO
            if 'codigo' in df.columns:
                df['codigo'] = df['codigo'].apply(lambda x: str(x).strip() if pd.notnull(x) and str(x).strip() not in ['nan', 'NaT', 'None', 'NaN', ''] else None)

            # C) TEXTOS
            text_cols = ['descripcion', 'parque', 'observaciones']
            for col in text_cols:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: str(x).strip() if pd.notnull(x) and str(x).strip() not in ['nan', 'NaT', 'None', 'NaN', ''] else None)

            # D) NUMEROS
            if 'stock_disponible' in df.columns:
                df['stock_disponible'] = pd.to_numeric(df['stock_disponible'], errors='coerce')
                df['stock_disponible'] = df['stock_disponible'].where(pd.notnull(df['stock_disponible']), 0)

            # E) FECHAS (usar safe_date_conversion para evitar warnings)
            if 'fec_vencimiento' in df.columns:
                df['fec_vencimiento'] = safe_date_conversion(df['fec_vencimiento'])
                df['fec_vencimiento'] = df['fec_vencimiento'].where(pd.notnull(df['fec_vencimiento']), None)

            # --- INSERCIÓN ROBUSTA ---
            if not df.empty:
                conn = None
                try:
                    conn = self.get_connection()
                    trans = conn.begin()
                    try:
                        conn.execute(text("DELETE FROM siciap.vencimientos_parques"))
                        df.to_sql('vencimientos_parques', conn, schema='siciap', if_exists='append', index=False)
                        trans.commit()
                        logger.info(f"✅ Vencimientos importados: {len(df)} registros.")
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
            logger.error(f"Error procesando vencimientos: {str(e)}")
            raise e
