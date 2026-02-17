"""
Procesador para datos de stock crítico
"""
import pandas as pd
import logging
from typing import Dict, List
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class StockProcessor(BaseProcessor):
    """Procesador para stock crítico"""
    
    def get_table_name(self) -> str:
        """Retorna el nombre de la tabla"""
        return 'siciap.stock_critico'
    
    def get_required_columns(self) -> List[str]:
        """Retorna las columnas requeridas"""
        return ['codigo']
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Mapeo Excel -> PostgreSQL. Referencia: siciap_app stock_critico."""
        return {
            'codigo': 'codigo', 'Codigo': 'codigo', 'Código': 'codigo', 'CODIGO': 'codigo',
            'descripcion': 'descripcion', 'Descripcion': 'descripcion', 'Descripción': 'descripcion',
            'producto': 'descripcion', 'Producto': 'descripcion', 'Medicamento': 'descripcion',
            'stock_disponible': 'stock_disponible', 'Stock Disponible': 'stock_disponible',
            'stock': 'stock_disponible', 'Stock': 'stock_disponible',
            'stock_minimo': 'stock_minimo', 'Stock Minimo': 'stock_minimo', 'Stock Mínimo': 'stock_minimo',
            'minimo': 'stock_minimo', 'Mínimo': 'stock_minimo',
            'dmp': 'dmp', 'DMP': 'dmp', 'Dias Medicamento Pendiente': 'dmp', 'Días Medicamento Pendiente': 'dmp',
            'estado': 'estado', 'Estado': 'estado',
        }
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas y convierte tipos de datos"""
        mapped_df = super().map_columns(df)
        
        # Asegurar que codigo sea string
        if 'codigo' in mapped_df.columns:
            mapped_df['codigo'] = mapped_df['codigo'].astype(str)
        
        # Convertir valores numéricos
        numeric_columns = ['stock_disponible', 'stock_minimo', 'dmp']
        for col in numeric_columns:
            if col in mapped_df.columns:
                mapped_df[col] = mapped_df[col].apply(
                    lambda x: self.data_cleaner.safe_to_numeric(x, default=0)
                )
        
        # Calcular estado si no existe
        if 'estado' not in mapped_df.columns or mapped_df['estado'].isna().all():
            mapped_df['estado'] = mapped_df.apply(self._calculate_estado, axis=1)
        
        return mapped_df
    
    def _calculate_estado(self, row: pd.Series) -> str:
        """Calcula el estado del stock basado en disponibilidad y mínimo"""
        stock = row.get('stock_disponible', 0) or 0
        minimo = row.get('stock_minimo', 0) or 0
        
        if stock <= 0:
            return 'critico'
        elif stock <= minimo:
            return 'bajo'
        else:
            return 'normal'
