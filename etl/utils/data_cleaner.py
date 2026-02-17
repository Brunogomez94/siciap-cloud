"""
Utilidades para limpieza y normalización de datos
"""
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from typing import Optional, Union
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)


class DataCleaner:
    """Clase para limpiar y normalizar datos"""
    
    @staticmethod
    def safe_date_conversion(date_series: Union[pd.Series, str], format_hint: Optional[str] = None) -> Union[pd.Series, datetime, None]:
        """
        Convierte fechas de forma segura sin warnings
        
        Args:
            date_series: Serie de pandas o string con fecha
            format_hint: Formato sugerido (opcional)
        
        Returns:
            Serie de fechas o fecha única
        """
        if date_series is None or (isinstance(date_series, pd.Series) and len(date_series) == 0):
            return date_series
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            if isinstance(date_series, pd.Series):
                # Limpiar valores problemáticos
                date_series = date_series.astype(str).replace(['nan', 'NaT', 'None', '', 'NaN'], None)
                
                # Métodos por orden de preferencia
                methods = [
                    lambda: pd.to_datetime(date_series, dayfirst=True, errors='coerce'),
                    lambda: pd.to_datetime(date_series, format='%d/%m/%Y', errors='coerce'),
                    lambda: pd.to_datetime(date_series, format='%d-%m-%Y', errors='coerce'),
                    lambda: pd.to_datetime(date_series, format='%d/%m/%Y %H:%M:%S', errors='coerce'),
                    lambda: pd.to_datetime(date_series, errors='coerce')
                ]
                
                for method in methods:
                    try:
                        result = method()
                        if not result.isna().all():
                            return result
                    except Exception:
                        continue
                
                return pd.to_datetime(date_series, errors='coerce')
            else:
                # Valor único
                if pd.isna(date_series) or date_series is None:
                    return None
                
                date_str = str(date_series)
                if "CUMPLIMIENTO TOTAL DE LAS OBLIGACIONES" in date_str.upper():
                    return date_str
                
                if date_str.strip() in ['nan', 'NaT', 'None', '', 'NaN']:
                    return None
                
                for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                    try:
                        return pd.to_datetime(date_str, format=fmt, dayfirst=True)
                    except Exception:
                        continue
                
                try:
                    return pd.to_datetime(date_str)
                except Exception:
                    return None
    
    @staticmethod
    def safe_to_numeric(value: Union[str, float, int], default: Optional[float] = None) -> Optional[float]:
        """
        Convierte un valor a numérico de forma segura
        
        Args:
            value: Valor a convertir
            default: Valor por defecto si falla
        
        Returns:
            Valor numérico o default
        """
        if pd.isna(value) or value is None:
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remover caracteres no numéricos excepto punto y coma
            cleaned = re.sub(r'[^\d.,-]', '', str(value))
            cleaned = cleaned.replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                return default
        
        return default
    
    @staticmethod
    def sanitize_text_for_postgres(text: Union[str, None], max_length: int = 10000) -> Optional[str]:
        """
        Sanitiza texto para PostgreSQL
        
        Args:
            text: Texto a sanitizar
            max_length: Longitud máxima
        
        Returns:
            Texto sanitizado
        """
        if text is None or pd.isna(text):
            return None
        
        text_str = str(text)
        
        # Escapar comillas simples
        text_str = text_str.replace("'", "''")
        
        # Limitar longitud
        if len(text_str) > max_length:
            text_str = text_str[:max_length]
        
        return text_str.strip()
    
    @staticmethod
    def clean_column_name(col_name: str) -> str:
        """
        Limpia y normaliza nombres de columnas
        
        Args:
            col_name: Nombre de columna original
        
        Returns:
            Nombre de columna limpio
        """
        if pd.isna(col_name):
            return 'unnamed'
        
        col_str = str(col_name).strip()
        
        # Remover acentos
        col_str = unicodedata.normalize('NFKD', col_str)
        col_str = col_str.encode('ascii', 'ignore').decode('ascii')
        
        # Convertir a minúsculas
        col_str = col_str.lower()
        
        # Reemplazar espacios y caracteres especiales
        col_str = re.sub(r'[^\w\s]', '', col_str)
        col_str = re.sub(r'\s+', '_', col_str)
        
        # Remover números al inicio
        col_str = re.sub(r'^\d+', '', col_str)
        
        # Si está vacío o es palabra reservada SQL, agregar prefijo
        sql_reserved = ['select', 'insert', 'update', 'delete', 'table', 'from', 'where']
        if not col_str or col_str in sql_reserved:
            col_str = f'col_{col_str}' if col_str else 'unnamed'
        
        return col_str
    
    @staticmethod
    def handle_null_value(value: Union[str, float, int, None]) -> Optional[Union[str, float, int]]:
        """
        Maneja valores nulos de forma consistente
        
        Args:
            value: Valor a procesar
        
        Returns:
            Valor procesado o None
        """
        if value is None or pd.isna(value):
            return None
        
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ['nan', 'nat', 'none', '', 'null', 'n/a']:
                return None
        
        return value
    
    @staticmethod
    def format_numeric_value(value: Union[float, int], is_percentage: bool = False, use_currency: bool = False) -> str:
        """
        Formatea valores numéricos de forma consistente
        
        Args:
            value: Valor numérico
            is_percentage: Si es porcentaje
            use_currency: Si usar símbolo de moneda
        
        Returns:
            String formateado
        """
        if pd.isna(value) or value is None:
            return "-"
        
        try:
            num_value = float(value)
            is_integer = num_value == int(num_value)
            
            if is_percentage:
                if is_integer:
                    return f"{int(num_value)}%"
                else:
                    return f"{num_value:.1f}%"
            else:
                if is_integer:
                    int_value = int(num_value)
                    if abs(num_value) >= 1000:
                        formatted = f"{int_value:,}".replace(',', '.')
                    else:
                        formatted = f"{int_value}"
                else:
                    formatted = f"{num_value:.2f}".rstrip('0').rstrip('.')
                    if abs(num_value) >= 1000:
                        parts = formatted.split('.')
                        parts[0] = f"{int(parts[0]):,}".replace(',', '.')
                        formatted = f"{parts[0]}.{parts[1]}" if len(parts) > 1 else parts[0]
                
                if use_currency:
                    return f"${formatted}"
                else:
                    return formatted
        except Exception:
            return "-"
