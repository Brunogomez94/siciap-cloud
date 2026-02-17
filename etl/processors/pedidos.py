"""
Procesador para datos de pedidos
"""
import pandas as pd
import logging
from typing import Dict, List
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class PedidosProcessor(BaseProcessor):
    """Procesador para pedidos"""
    
    def get_table_name(self) -> str:
        """Retorna el nombre de la tabla"""
        return 'siciap.pedidos'
    
    def get_required_columns(self) -> List[str]:
        """Retorna las columnas requeridas"""
        return ['codigo']
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Retorna el mapeo de columnas Excel -> PostgreSQL"""
        return {
            'id_llamado': 'id_llamado',
            'Id.Llamado': 'id_llamado',
            'Id Llamado': 'id_llamado',
            'codigo': 'codigo',
            'Codigo': 'codigo',
            'Código': 'codigo',
            'item': 'item',
            'Item': 'item',
            'cantidad_solicitada': 'cantidad_solicitada',
            'Cantidad Solicitada': 'cantidad_solicitada',
            'cantidad': 'cantidad_solicitada',
            'cantidad_pendiente': 'cantidad_pendiente',
            'Cantidad Pendiente': 'cantidad_pendiente',
            'pendiente': 'cantidad_pendiente',
            'fecha_solicitud': 'fecha_solicitud',
            'Fecha Solicitud': 'fecha_solicitud',
            'fecha_requerida': 'fecha_requerida',
            'Fecha Requerida': 'fecha_requerida',
            'estado': 'estado',
            'Estado': 'estado',
            'observaciones': 'observaciones',
            'Observaciones': 'observaciones',
        }
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas y convierte tipos de datos"""
        mapped_df = super().map_columns(df)
        
        # Convertir tipos de datos
        if 'id_llamado' in mapped_df.columns:
            mapped_df['id_llamado'] = pd.to_numeric(mapped_df['id_llamado'], errors='coerce').astype('Int64')
        
        if 'item' in mapped_df.columns:
            mapped_df['item'] = pd.to_numeric(mapped_df['item'], errors='coerce').astype('Int64')
        
        # Asegurar que codigo sea string
        if 'codigo' in mapped_df.columns:
            mapped_df['codigo'] = mapped_df['codigo'].astype(str)
        
        # Convertir valores numéricos
        numeric_columns = ['cantidad_solicitada', 'cantidad_pendiente']
        for col in numeric_columns:
            if col in mapped_df.columns:
                mapped_df[col] = mapped_df[col].apply(
                    lambda x: self.data_cleaner.safe_to_numeric(x, default=0)
                )
        
        # Convertir fechas
        date_columns = ['fecha_solicitud', 'fecha_requerida']
        for col in date_columns:
            if col in mapped_df.columns:
                mapped_df[col] = self.data_cleaner.safe_date_conversion(mapped_df[col])
        
        # Establecer estado por defecto si no existe
        if 'estado' not in mapped_df.columns or mapped_df['estado'].isna().all():
            mapped_df['estado'] = 'pendiente'
        
        return mapped_df
