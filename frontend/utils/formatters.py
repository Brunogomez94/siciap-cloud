"""
Utilidades de formateo para el frontend
"""
import pandas as pd
from datetime import datetime
from etl.utils.data_cleaner import DataCleaner

cleaner = DataCleaner()


def format_numeric(value, is_percentage: bool = False, use_currency: bool = False) -> str:
    """
    Formatea valores numéricos
    
    Args:
        value: Valor a formatear
        is_percentage: Si es porcentaje
        use_currency: Si usar símbolo de moneda
    
    Returns:
        String formateado
    """
    return cleaner.format_numeric_value(value, is_percentage, use_currency)


def format_date(date_value, format_str: str = "%d/%m/%Y") -> str:
    """
    Formatea fechas
    
    Args:
        date_value: Valor de fecha
        format_str: Formato de salida
    
    Returns:
        String con fecha formateada
    """
    if pd.isna(date_value) or date_value is None:
        return "-"
    
    try:
        if isinstance(date_value, str):
            date_value = cleaner.safe_date_conversion(date_value)
        
        if isinstance(date_value, pd.Timestamp):
            return date_value.strftime(format_str)
        elif isinstance(date_value, datetime):
            return date_value.strftime(format_str)
        else:
            return str(date_value)
    except Exception:
        return "-"


def format_currency(value) -> str:
    """
    Formatea valores como moneda
    
    Args:
        value: Valor numérico
    
    Returns:
        String con formato de moneda
    """
    return format_numeric(value, use_currency=True)
