"""
Lector robusto de archivos Excel
Basado en read_excel_robust de siciap_app pero mejorado y modular
"""
import pandas as pd
from io import BytesIO
import logging
from typing import Optional, List

try:
    import chardet
except ImportError:
    chardet = None  # opcional: sin chardet se usa utf-8 y fallbacks

logger = logging.getLogger(__name__)


class ExcelReader:
    """Clase para leer archivos Excel de forma robusta"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
    
    def read(self, file_content: bytes, file_name: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lee un archivo Excel de forma robusta, probando múltiples métodos
        
        Args:
            file_content: Contenido del archivo en bytes
            file_name: Nombre del archivo (para determinar extensión)
            sheet_name: Nombre de la hoja a leer (opcional)
        
        Returns:
            DataFrame con los datos leídos
        
        Raises:
            ValueError: Si no se puede leer el archivo
        """
        file_ext = self._get_extension(file_name)
        
        if file_ext == '.csv':
            return self._read_csv(file_content, file_name)
        else:
            return self._read_excel(file_content, file_name, sheet_name)
    
    def _get_extension(self, file_name: str) -> str:
        """Obtiene la extensión del archivo"""
        if '.' not in file_name:
            return '.xlsx'  # Por defecto
        return '.' + file_name.split('.')[-1].lower()
    
    def _read_excel(self, file_content: bytes, file_name: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Lee un archivo Excel"""
        methods = [
            lambda: pd.read_excel(BytesIO(file_content), sheet_name=sheet_name, engine='openpyxl'),
            lambda: pd.read_excel(BytesIO(file_content), sheet_name=sheet_name, engine='openpyxl', data_only=True),
            lambda: pd.read_excel(BytesIO(file_content), sheet_name=sheet_name, engine='openpyxl', skiprows=1),
            lambda: self._find_sheet_with_data(file_content),
            lambda: pd.read_excel(BytesIO(file_content), sheet_name=0, engine='xlrd'),
        ]
        
        for i, method in enumerate(methods):
            try:
                df = method()
                if df is not None and not df.empty:
                    logger.info(f"Archivo leído exitosamente con método {i+1}")
                    return self._clean_headers(df)
            except Exception as e:
                logger.debug(f"Método {i+1} falló: {e}")
                continue
        
        raise ValueError(f"No se pudo leer el archivo Excel: {file_name}")
    
    def _read_csv(self, file_content: bytes, file_name: str) -> pd.DataFrame:
        """Lee un archivo CSV con detección de encoding (chardet si está instalado)."""
        encodings_to_try = ['utf-8']
        if chardet is not None:
            try:
                detected = chardet.detect(file_content)
                enc = detected.get('encoding')
                if enc and enc not in encodings_to_try:
                    encodings_to_try.insert(0, enc)
            except Exception:
                pass
        encodings_to_try += ['latin-1', 'iso-8859-1', 'cp1252']
        last_error = None
        for encoding in encodings_to_try:
            try:
                return pd.read_csv(BytesIO(file_content), encoding=encoding)
            except (UnicodeDecodeError, Exception) as e:
                last_error = e
                continue
        logger.error(f"Error leyendo CSV: {last_error}")
        raise ValueError(f"No se pudo leer el archivo CSV: {file_name}")
    
    def _find_sheet_with_data(self, file_content: bytes) -> Optional[pd.DataFrame]:
        """Busca la primera hoja con datos"""
        try:
            xl_file = pd.ExcelFile(BytesIO(file_content), engine='openpyxl')
            for sheet in xl_file.sheet_names:
                try:
                    df = pd.read_excel(xl_file, sheet_name=sheet, engine='openpyxl')
                    if not df.empty and len(df.columns) > 0:
                        return df
                except Exception:
                    continue
        except Exception:
            pass
        return None
    
    def _clean_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia los headers del DataFrame"""
        # Eliminar filas duplicadas en headers
        if len(df.columns) > 0:
            # Normalizar nombres de columnas
            df.columns = [self._normalize_column_name(col) for col in df.columns]
        
        # Eliminar filas completamente vacías al inicio
        while len(df) > 0 and df.iloc[0].isna().all():
            df = df.iloc[1:].reset_index(drop=True)
        
        return df
    
    def _normalize_column_name(self, col_name: str) -> str:
        """Normaliza el nombre de una columna"""
        if pd.isna(col_name):
            return 'unnamed'
        
        col_str = str(col_name).strip()
        
        # Remover acentos y caracteres especiales
        import unicodedata
        col_str = unicodedata.normalize('NFKD', col_str)
        col_str = col_str.encode('ascii', 'ignore').decode('ascii')
        
        # Convertir a minúsculas y reemplazar espacios
        col_str = col_str.lower().replace(' ', '_')
        
        # Remover caracteres no válidos
        col_str = ''.join(c for c in col_str if c.isalnum() or c == '_')
        
        return col_str if col_str else 'unnamed'
    
    def get_sheet_names(self, file_content: bytes) -> List[str]:
        """Obtiene los nombres de las hojas del archivo Excel"""
        try:
            xl_file = pd.ExcelFile(BytesIO(file_content), engine='openpyxl')
            return xl_file.sheet_names
        except Exception:
            return []
