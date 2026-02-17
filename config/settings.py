"""
Configuración general del sistema
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Settings:
    """Configuración centralizada de la aplicación"""
    
    # Directorios del proyecto
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / os.getenv('ETL_DATA_DIR', 'data')
    LOG_DIR = BASE_DIR / 'logs'
    
    # Configuración ETL
    ETL_BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '1000'))
    ETL_LOG_LEVEL = os.getenv('ETL_LOG_LEVEL', 'INFO')
    
    # Configuración Streamlit
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
    
    # Crear directorios si no existen
    DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_data_dir(cls):
        """Retorna el directorio de datos"""
        return cls.DATA_DIR
    
    @classmethod
    def get_log_dir(cls):
        """Retorna el directorio de logs"""
        return cls.LOG_DIR
