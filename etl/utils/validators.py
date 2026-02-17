"""
Validadores de datos
"""
import pandas as pd
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Clase para validar datos antes de insertar en BD"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_dataframe(self, df: pd.DataFrame, table_name: str, required_columns: List[str]) -> bool:
        """
        Valida un DataFrame antes de insertar
        
        Args:
            df: DataFrame a validar
            table_name: Nombre de la tabla destino
            required_columns: Columnas requeridas
        
        Returns:
            True si es válido, False en caso contrario
        """
        self.errors = []
        self.warnings = []
        
        # Validar que el DataFrame no esté vacío
        if df.empty:
            self.errors.append(f"DataFrame para {table_name} está vacío")
            return False
        
        # Validar columnas requeridas
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            self.errors.append(
                f"Faltan columnas requeridas en {table_name}: {', '.join(missing_cols)}"
            )
        
        # Validar tipos de datos básicos
        self._validate_types(df, table_name)
        
        # Validar valores nulos en columnas críticas
        self._validate_nulls(df, table_name, required_columns)
        
        return len(self.errors) == 0
    
    def _validate_types(self, df: pd.DataFrame, table_name: str):
        """Valida tipos de datos"""
        # Validar que id_llamado sea numérico si existe
        if 'id_llamado' in df.columns:
            non_numeric = df['id_llamado'].apply(
                lambda x: pd.notna(x) and not isinstance(x, (int, float))
            ).sum()
            if non_numeric > 0:
                self.warnings.append(
                    f"{table_name}: {non_numeric} valores no numéricos en id_llamado"
                )
        
        # Validar que item sea numérico si existe
        if 'item' in df.columns:
            non_numeric = df['item'].apply(
                lambda x: pd.notna(x) and not isinstance(x, (int, float))
            ).sum()
            if non_numeric > 0:
                self.warnings.append(
                    f"{table_name}: {non_numeric} valores no numéricos en item"
                )
    
    def _validate_nulls(self, df: pd.DataFrame, table_name: str, required_columns: List[str]):
        """Valida valores nulos en columnas requeridas"""
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    self.warnings.append(
                        f"{table_name}: {null_count} valores nulos en columna requerida '{col}'"
                    )
    
    def get_errors(self) -> List[str]:
        """Retorna lista de errores"""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Retorna lista de advertencias"""
        return self.warnings
    
    def clear(self):
        """Limpia errores y advertencias"""
        self.errors = []
        self.warnings = []
    
    @staticmethod
    def validate_id_llamado(id_llamado: Union[int, float, str]) -> Optional[int]:
        """
        Valida y normaliza id_llamado
        
        Args:
            id_llamado: ID del llamado
        
        Returns:
            ID normalizado como entero o None
        """
        if pd.isna(id_llamado) or id_llamado is None:
            return None
        
        try:
            # Convertir a float primero para manejar strings numéricos
            id_float = float(id_llamado)
            return int(id_float)
        except (ValueError, TypeError):
            logger.warning(f"id_llamado inválido: {id_llamado}")
            return None
