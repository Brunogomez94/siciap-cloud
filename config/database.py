"""
Configuración de base de datos PostgreSQL local
"""
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class DatabaseConfig:
    """Configuración de conexión a PostgreSQL local"""
    
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', '5432'))
    DATABASE = os.getenv('DB_NAME', 'siciap_local')
    USER = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    
    SCHEMA = 'siciap'
    
    @classmethod
    def get_connection_string(cls):
        """Retorna la cadena de conexión a PostgreSQL (con search_path=siciap para encontrar tablas)."""
        base = (
            f"postgresql://{cls.USER}:{cls.PASSWORD}"
            f"@{cls.HOST}:{cls.PORT}/{cls.DATABASE}"
        )
        # Fijar search_path para que SELECT * FROM ordenes etc. resuelva a siciap.ordenes
        return f"{base}?options=-c%20search_path%3Dsiciap%2Cpublic"
    
    @classmethod
    def get_connection_dict(cls):
        """Retorna configuración como diccionario"""
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.DATABASE,
            'user': cls.USER,
            'password': cls.PASSWORD
        }
    
    @classmethod
    def validate(cls):
        """Valida que la configuración esté completa"""
        if not cls.PASSWORD:
            raise ValueError("DB_PASSWORD no está configurada en .env")
        return True
