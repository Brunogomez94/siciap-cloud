"""
Clase base para procesadores de datos
"""
import pandas as pd
import logging
from typing import Optional, Dict, List
from sqlalchemy import create_engine, text
from config.database import DatabaseConfig
from etl.utils.excel_reader import ExcelReader
from etl.utils.data_cleaner import DataCleaner
from etl.utils.validators import DataValidator

logger = logging.getLogger(__name__)


class BaseProcessor:
    """Clase base para todos los procesadores"""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        """
        Inicializa el procesador base
        
        Args:
            db_config: Configuración de base de datos (opcional)
        """
        self.db_config = db_config or DatabaseConfig()
        self.excel_reader = ExcelReader()
        self.data_cleaner = DataCleaner()
        self.validator = DataValidator()
        self.engine = None
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        if self.engine is None:
            conn_str = self.db_config.get_connection_string()
            self.engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        return self.engine.connect()
    
    def read_excel(self, file_content: bytes, file_name: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lee un archivo Excel usando el lector robusto
        
        Args:
            file_content: Contenido del archivo en bytes
            file_name: Nombre del archivo
            sheet_name: Nombre de la hoja (opcional)
        
        Returns:
            DataFrame con los datos
        """
        return self.excel_reader.read(file_content, file_name, sheet_name)
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia un DataFrame
        
        Args:
            df: DataFrame a limpiar
        
        Returns:
            DataFrame limpio
        """
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Limpiar nombres de columnas
        df.columns = [self.data_cleaner.clean_column_name(col) for col in df.columns]
        
        return df
    
    def validate_dataframe(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Valida un DataFrame
        
        Args:
            df: DataFrame a validar
            required_columns: Columnas requeridas
        
        Returns:
            True si es válido
        """
        return self.validator.validate_dataframe(df, self.get_table_name(), required_columns)
    
    def get_table_name(self) -> str:
        """Retorna el nombre de la tabla (debe ser implementado por subclases)"""
        raise NotImplementedError("Subclases deben implementar get_table_name()")
    
    def get_required_columns(self) -> List[str]:
        """Retorna las columnas requeridas (debe ser implementado por subclases)"""
        raise NotImplementedError("Subclases deben implementar get_required_columns()")
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Retorna el mapeo de columnas Excel -> PostgreSQL
        Debe ser implementado por subclases
        """
        raise NotImplementedError("Subclases deben implementar get_column_mapping()")
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Mapea las columnas del Excel a las columnas de la base de datos
        
        Args:
            df: DataFrame original
        
        Returns:
            DataFrame con columnas mapeadas
        """
        mapping = self.get_column_mapping()
        mapped_df = pd.DataFrame()
        
        # Normalizar nombres para comparación
        normalized_map = {}
        for excel_name, db_name in mapping.items():
            normalized_key = excel_name.lower().replace(' ', '').replace('.', '').replace('_', '')
            normalized_map[normalized_key] = db_name
        
        # Mapear columnas
        for excel_col in df.columns:
            # Búsqueda exacta
            if excel_col in mapping:
                mapped_df[mapping[excel_col]] = df[excel_col].copy()
                continue
            
            # Búsqueda normalizada
            excel_norm = excel_col.lower().replace(' ', '').replace('.', '').replace('_', '')
            if excel_norm in normalized_map:
                mapped_df[normalized_map[excel_norm]] = df[excel_col].copy()
                continue
            
            # Búsqueda por similitud
            matched = False
            for excel_key_norm, db_name in normalized_map.items():
                if excel_norm in excel_key_norm or excel_key_norm in excel_norm:
                    mapped_df[db_name] = df[excel_col].copy()
                    matched = True
                    break
            
            if not matched:
                logger.warning(f"No se encontró mapeo para columna '{excel_col}'")
        
        # Asegurar columnas requeridas
        required_cols = self.get_required_columns()
        for col in required_cols:
            if col not in mapped_df.columns:
                mapped_df[col] = None
        
        return mapped_df
    
    def process_file(self, file_content: bytes, file_name: str) -> bool:
        """
        Procesa un archivo y lo importa a la base de datos
        
        Args:
            file_content: Contenido del archivo en bytes
            file_name: Nombre del archivo
        
        Returns:
            True si el procesamiento fue exitoso
        """
        try:
            # Leer Excel
            df = self.read_excel(file_content, file_name)
            
            if df.empty:
                logger.error(f"El archivo {file_name} está vacío")
                return False
            
            # Limpiar DataFrame
            df = self.clean_dataframe(df)
            
            # Mapear columnas
            mapped_df = self.map_columns(df)
            
            # Validar datos
            required_cols = self.get_required_columns()
            if not self.validate_dataframe(mapped_df, required_cols):
                errors = self.validator.get_errors()
                for error in errors:
                    logger.error(error)
                return False
            
            # Insertar en base de datos
            return self.insert_data(mapped_df)
        
        except Exception as e:
            logger.error(f"Error procesando archivo {file_name}: {e}", exc_info=True)
            return False
    
    def _get_table_columns(self, conn, schema: str, table: str):
        """Obtiene las columnas que existen en la tabla (para insertar solo esas)."""
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            ORDER BY ordinal_position
        """), {"schema": schema, "table": table})
        return [row[0] for row in result]

    def insert_data(self, df: pd.DataFrame) -> bool:
        """
        Inserta datos en la base de datos. Solo se insertan columnas que existen en la tabla.
        """
        table_name = self.get_table_name()
        schema, table = table_name.split('.') if '.' in table_name else ('siciap', table_name)
        # Columnas que la tabla rellena sola (no las enviamos)
        skip = {'id', 'creado_en', 'actualizado_en'}
        try:
            with self.get_connection() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text(f"DELETE FROM {schema}.{table}"))
                    table_cols = [c for c in self._get_table_columns(conn, schema, table) if c not in skip]
                    valid = [c for c in df.columns if c in table_cols]
                    if not valid:
                        logger.error(f"Ninguna columna del DataFrame existe en {schema}.{table}. Tabla: {table_cols}")
                        trans.rollback()
                        return False
                    missing = set(table_cols) - set(valid)
                    if missing:
                        logger.info(f"Columnas omitidas (no vienen en el Excel): {missing}")
                    df_insert = df[valid].copy()
                    df_insert.to_sql(
                        table, conn, schema=schema,
                        if_exists='append', index=False, method='multi'
                    )
                    trans.commit()
                    logger.info(f"Datos insertados en {table_name}: {len(df_insert)} filas")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Error insertando datos: {e}", exc_info=True)
                    return False
        except Exception as e:
            logger.error(f"Error de conexión: {e}", exc_info=True)
            return False
