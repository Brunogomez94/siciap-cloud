"""
Procesador para datos de ejecución
"""
import pandas as pd
import logging
from typing import Dict, List
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class EjecucionProcessor(BaseProcessor):
    """Procesador para ejecución de contratos"""
    
    def get_table_name(self) -> str:
        """Retorna el nombre de la tabla"""
        return 'siciap.ejecucion'
    
    def get_required_columns(self) -> List[str]:
        """Retorna las columnas requeridas"""
        return ['id_llamado', 'licitacion', 'codigo', 'item']
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Mapeo Excel -> PostgreSQL. Referencia: siciap_app ejecucion."""
        return {
            'id_llamado': 'id_llamado', 'Id.Llamado': 'id_llamado', 'Id Llamado': 'id_llamado',
            'licitacion': 'licitacion', 'Licitacion': 'licitacion', 'Licitación': 'licitacion',
            'codigo': 'codigo', 'Codigo': 'codigo', 'Código': 'codigo',
            'item': 'item', 'Item': 'item',
            'cantidad_ejecutada': 'cantidad_ejecutada', 'Cantidad Ejecutada': 'cantidad_ejecutada',
            'cantidad': 'cantidad_ejecutada', 'Cantidad Emitida': 'cantidad_ejecutada',
            'Cantidad Maxima': 'cantidad_ejecutada', 'Cantidad Máxima': 'cantidad_ejecutada',
            'cantidad_emitida': 'cantidad_ejecutada', 'cantidad_maxima': 'cantidad_ejecutada',
            'precio_unitario': 'precio_unitario', 'Precio Unitario': 'precio_unitario', 'P.Unit.': 'precio_unitario',
            'monto_total': 'monto_total', 'Monto Total': 'monto_total', 'monto': 'monto_total',
            'Monto Adjudicado': 'monto_total', 'Monto Emitido': 'monto_total',
            'fecha_ejecucion': 'fecha_ejecucion', 'Fecha Ejecucion': 'fecha_ejecucion', 'Fecha Ejecución': 'fecha_ejecucion',
            'fecha': 'fecha_ejecucion',
            'observaciones': 'observaciones', 'Observaciones': 'observaciones', 'Obs.': 'observaciones',
        }
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas y convierte tipos de datos"""
        mapped_df = super().map_columns(df)
        
        # Convertir tipos de datos críticos
        if 'id_llamado' in mapped_df.columns:
            mapped_df['id_llamado'] = pd.to_numeric(mapped_df['id_llamado'], errors='coerce').astype('Int64')
        
        if 'item' in mapped_df.columns:
            mapped_df['item'] = pd.to_numeric(mapped_df['item'], errors='coerce').astype('Int64')
        
        # Asegurar que licitacion y codigo sean strings
        if 'licitacion' in mapped_df.columns:
            mapped_df['licitacion'] = mapped_df['licitacion'].astype(str)
        
        if 'codigo' in mapped_df.columns:
            mapped_df['codigo'] = mapped_df['codigo'].astype(str)
        
        # Convertir valores numéricos
        numeric_columns = ['cantidad_ejecutada', 'precio_unitario', 'monto_total']
        for col in numeric_columns:
            if col in mapped_df.columns:
                mapped_df[col] = mapped_df[col].apply(
                    lambda x: self.data_cleaner.safe_to_numeric(x)
                )
        
        # Convertir fechas
        if 'fecha_ejecucion' in mapped_df.columns:
            mapped_df['fecha_ejecucion'] = self.data_cleaner.safe_date_conversion(mapped_df['fecha_ejecucion'])
        
        return mapped_df
