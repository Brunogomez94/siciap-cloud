"""
Procesador para datos de órdenes
"""
import pandas as pd
import logging
from typing import Dict, List
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class OrdenesProcessor(BaseProcessor):
    """Procesador para órdenes de compra"""
    
    def get_table_name(self) -> str:
        """Retorna el nombre de la tabla"""
        return 'siciap.ordenes'
    
    def get_required_columns(self) -> List[str]:
        """Retorna las columnas requeridas"""
        return ['id_llamado', 'codigo']
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Mapeo Excel -> PostgreSQL. Referencia: siciap_app. Solo columnas de siciap.ordenes."""
        return {
            'Id.Llamado': 'id_llamado', 'id_llamado': 'id_llamado', 'Id Llamado': 'id_llamado',
            'Llamado': 'llamado', 'llamado': 'llamado',
            'Proveedor': 'proveedor', 'proveedor': 'proveedor',
            'Codigo': 'codigo', 'codigo': 'codigo', 'Código': 'codigo',
            'Item': 'item', 'item': 'item',
            'Monto Saldo': 'saldo', 'Saldo': 'saldo', 'saldo': 'saldo', 'monto_saldo': 'saldo',
            'Estado': 'estado', 'estado': 'estado',
            'Fecha OC': 'fecha_orden', 'fecha_orden': 'fecha_orden', 'fecha_oc': 'fecha_orden',
            'Fec. Ult. Recep.': 'fecha_vencimiento', 'fecha_vencimiento': 'fecha_vencimiento',
            'Fecha Recibido Proveedor': 'fecha_vencimiento', 'Fecha Recibido Poveedor': 'fecha_vencimiento',
            'Producto': 'observaciones', 'producto': 'observaciones',
            'OC': 'observaciones', 'oc': 'observaciones',
            'Referencia': 'observaciones', 'Lugar Entrega OC': 'observaciones', 'Lugar Entrega': 'observaciones',
        }
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas y convierte tipos (solo las que tiene siciap.ordenes)."""
        mapped_df = super().map_columns(df)
        if 'id_llamado' in mapped_df.columns:
            mapped_df['id_llamado'] = pd.to_numeric(mapped_df['id_llamado'], errors='coerce').astype('Int64')
        if 'item' in mapped_df.columns:
            mapped_df['item'] = pd.to_numeric(mapped_df['item'], errors='coerce').astype('Int64')
        for col in ['fecha_orden', 'fecha_vencimiento']:
            if col in mapped_df.columns:
                mapped_df[col] = self.data_cleaner.safe_date_conversion(mapped_df[col])
        if 'saldo' in mapped_df.columns:
            mapped_df['saldo'] = mapped_df['saldo'].apply(
                lambda x: self.data_cleaner.safe_to_numeric(x, default=0)
            )
        if 'codigo' in mapped_df.columns:
            mapped_df['codigo'] = mapped_df['codigo'].astype(str)
        return mapped_df
