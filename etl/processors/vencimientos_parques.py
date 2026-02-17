"""
Procesador para vencimientos en parques (vencimientos_parques / vencimientos_pnc)
"""
import pandas as pd
import logging
from typing import Dict, List
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class VencimientosParquesProcessor(BaseProcessor):
    """Procesador para vencimientos de productos en parques"""

    def get_table_name(self) -> str:
        return "siciap.vencimientos_parques"

    def get_required_columns(self) -> List[str]:
        return ["codigo"]

    def get_column_mapping(self) -> Dict[str, str]:
        return {
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

    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        # CSV tipo Stock_en_PNCs: una fila por (producto, parque, fecha, tipo medida, valor).
        # Nos quedamos con filas "Stock Disponible" y usamos Valores de medidas como stock.
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

        mapped_df = super().map_columns(df)
        if "codigo" in mapped_df.columns:
            mapped_df["codigo"] = mapped_df["codigo"].astype(str)
        for col in ["stock_disponible"]:
            if col in mapped_df.columns:
                mapped_df[col] = mapped_df[col].apply(
                    lambda x: self.data_cleaner.safe_to_numeric(x, default=0)
                )
        if "fec_vencimiento" in mapped_df.columns:
            mapped_df["fec_vencimiento"] = self.data_cleaner.safe_date_conversion(
                mapped_df["fec_vencimiento"]
            )
        return mapped_df
