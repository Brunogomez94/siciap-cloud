"""
Función read_excel_robust copiada EXACTAMENTE de siciap_app
"""
import pandas as pd
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


def read_excel_robust(file_content, file_name):
    """Intenta leer un archivo Excel con múltiples métodos - VERSIÓN MEJORADA"""
    logger.info(f"Intentando leer el archivo {file_name} con métodos robustos...")
    
    # Asegurar que file_content es un BytesIO
    if isinstance(file_content, BytesIO):
        buffer = file_content
        buffer.seek(0)
    else:
        try:
            buffer = BytesIO(file_content)
        except Exception as e:
            logger.error(f"Error al convertir contenido a BytesIO: {str(e)}")
            return None
    
    # Métodos priorizados para archivos Excel
    methods = [
        # Método 1: openpyxl con data_only=True (mejor para fórmulas)
        lambda: pd.read_excel(buffer, engine='openpyxl', engine_kwargs={'data_only': True}),
        # Método 2: pandas estándar (más simple)
        lambda: pd.read_excel(buffer),
        # Método 3: openpyxl normal
        lambda: pd.read_excel(buffer, engine='openpyxl'),
        # Método 4: Intentar con xlrd para .xls
        lambda: pd.read_excel(buffer, engine='xlrd') if file_name.lower().endswith('.xls') else None,
        # Método 5: Ignorar filas vacías al inicio
        lambda: pd.read_excel(buffer, skiprows=range(1, 10)),
        # Método 6: Buscar hojas con datos
        lambda: find_sheet_with_data(buffer),
        # Método 7: CSV fallback
        lambda: try_read_as_csv(buffer, file_name)
    ]

    # Intentar cada método
    for i, method in enumerate(methods):
        try:
            logger.info(f"Intentando método {i+1} para leer Excel...")
            buffer.seek(0)  # Resetear posición del buffer
            df = method()
            
            if df is None or df.empty:
                logger.warning(f"El método {i+1} devolvió un DataFrame vacío")
                continue
            
            # Validar si hay datos útiles
            non_null_data = df.dropna(how='all')
            if non_null_data.shape[0] == 0:
                logger.warning(f"El método {i+1} devolvió solo headers sin datos")
                continue

            # Limpieza básica del DataFrame exitoso
            df = clean_downloaded_excel(df)
            
            logger.info(f"ÉXITO con método {i+1}. Encontradas {len(df.columns)} columnas y {df.shape[0]} filas.")
            return df
        
        except Exception as e:
            logger.warning(f"Error con método {i+1}: {str(e)}")
            buffer.seek(0)  # Resetear posición del buffer para siguiente intento

    # Si todos los métodos fallan
    logger.error(f"TODOS LOS MÉTODOS FALLARON para leer el archivo Excel {file_name}")
    return None


def try_read_as_csv(file_content, file_name):
    """Intenta leer como CSV si el Excel está mal formateado"""
    try:
        if hasattr(file_content, 'seek'):
            file_content.seek(0)

        # Leer como texto y verificar si parece CSV
        content_bytes = file_content.read()
        # Detectar encoding
        try:
            import chardet
            encoding_result = chardet.detect(content_bytes)
            encoding = encoding_result['encoding'] if encoding_result['confidence'] > 0.7 else 'utf-8'
        except ImportError:
            encoding = 'utf-8'
        
        try:
            content_text = content_bytes.decode(encoding)
        except:
            content_text = content_bytes.decode('utf-8', errors='ignore')
        
        # Si tiene separadores CSV comunes, intentar leer como CSV
        if ',' in content_text or ';' in content_text or '\t' in content_text:
            logger.info("Archivo parece ser CSV disfrazado de Excel, intentando lectura CSV...")
            
            import io
            # Probar diferentes separadores
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(io.StringIO(content_text), sep=sep, encoding=encoding)
                    if df.shape[1] > 1:  # Si tiene múltiples columnas, probablemente sea correcto
                        return df
                except:
                    continue
        
        return None
    except Exception as e:
        logger.warning(f"Error al intentar leer como CSV: {str(e)}")
        return None


def find_sheet_with_data(file_content):
    """Encuentra la hoja con datos reales en un archivo multi-sheet"""
    try:
        if hasattr(file_content, 'seek'):
            file_content.seek(0)

        # Leer todas las hojas
        all_sheets = pd.read_excel(file_content, sheet_name=None, engine='openpyxl')
        for sheet_name, df in all_sheets.items():
            # Buscar hoja con datos reales
            if not df.empty and df.dropna(how='all').shape[0] > 0:
                logger.info(f"Encontrados datos en la hoja: {sheet_name}")
                return df
        
        return None
    except Exception as e:
        logger.warning(f"Error al buscar hojas con datos: {str(e)}")
        return None


def clean_downloaded_excel(df):
    """Limpia DataFrames de archivos Excel descargados que suelen tener problemas"""
    try:
        # 1. Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # 2. Eliminar columnas completamente vacías
        df = df.dropna(axis=1, how='all')
        
        # 3. Limpiar nombres de columnas problemáticos
        new_columns = []
        for col in df.columns:
            if pd.isna(col) or str(col).strip() == '':
                # Generar nombre para columna sin nombre
                new_columns.append(f"columna_{len(new_columns) + 1}")
            else:
                # Limpiar el nombre de la columna PERO PRESERVAR ACENTOS
                clean_col = str(col).strip()
                # Remover caracteres problemáticos comunes en descargas
                clean_col = clean_col.replace('\n', ' ').replace('\r', ' ')
                clean_col = ' '.join(clean_col.split())  # Normalizar espacios
                new_columns.append(clean_col)
        
        df.columns = new_columns
        
        # 4. Eliminar filas que son headers repetidos (común en descargas web)
        if len(df) > 1:
            # Si la primera fila es igual a los headers, eliminarla
            first_row_as_str = [str(x).strip().lower() for x in df.iloc[0].values]
            headers_as_str = [str(x).strip().lower() for x in df.columns]
            
            if first_row_as_str == headers_as_str:
                df = df.iloc[1:].reset_index(drop=True)
                logger.info("Eliminada fila de headers duplicados")
        
        # 5. Limpiar celdas con valores problemáticos
        df = df.replace(['', ' ', 'NULL', 'null', 'None', '#N/A', '#REF!'], pd.NA)
        
        # 6. Reset index
        df = df.reset_index(drop=True)
        
        logger.info(f"Limpieza completada: {df.shape[0]} filas, {df.shape[1]} columnas")
        return df
    except Exception as e:
        logger.warning(f"Error durante limpieza: {str(e)}")
        return df
