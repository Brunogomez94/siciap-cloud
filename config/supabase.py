"""
Configuración de Supabase (nube)
"""
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


def _resolve_db_host_and_user():
    """Usa Session pooler si .env tiene el host directo (db.xxx.supabase.co) para evitar timeouts."""
    host = os.getenv('SUPABASE_DB_HOST', '')
    user = os.getenv('SUPABASE_DB_USER', 'postgres')
    url = os.getenv('SUPABASE_URL', '')
    # Si el host es conexión directa (suele dar timeout en redes restrictivas), usar pooler
    if host.startswith('db.') and '.supabase.co' in host and url:
        try:
            parsed = urlparse(url if '://' in url else f'https://{url}')
            project_ref = (parsed.hostname or '').split('.')[0]
            if project_ref:
                pooler = os.getenv('SUPABASE_POOLER_HOST', 'aws-1-us-east-1.pooler.supabase.com')
                return pooler, f'postgres.{project_ref}'
        except Exception:
            pass
    return host, user


class SupabaseConfig:
    """Configuración de conexión a Supabase"""
    
    # URL y API Key de Supabase
    URL = os.getenv('SUPABASE_URL', '')
    API_KEY = os.getenv('SUPABASE_KEY', '')
    
    # Configuración de base de datos PostgreSQL en Supabase (puede pasarse a pooler automáticamente)
    _db_host, _db_user = _resolve_db_host_and_user()
    DB_HOST = _db_host or os.getenv('SUPABASE_DB_HOST', '')
    DB_PORT = int(os.getenv('SUPABASE_DB_PORT', '5432'))
    DB_NAME = os.getenv('SUPABASE_DB_NAME', 'postgres')
    DB_USER = _db_user or os.getenv('SUPABASE_DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD', '')
    
    SCHEMA = 'public'  # Supabase usa 'public' por defecto
    
    @classmethod
    def get_connection_string(cls):
        """Retorna la cadena de conexión a PostgreSQL de Supabase"""
        if not all([cls.DB_HOST, cls.DB_NAME, cls.DB_USER, cls.DB_PASSWORD]):
            raise ValueError("Configuración de Supabase incompleta")
        
        return (
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )
    
    @classmethod
    def get_connection_dict(cls):
        """Retorna configuración como diccionario"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD
        }
    
    @classmethod
    def validate(cls):
        """Valida que la configuración esté completa"""
        if not cls.URL:
            raise ValueError("SUPABASE_URL no está configurada en .env")
        if not cls.API_KEY:
            raise ValueError("SUPABASE_KEY no está configurada en .env")
        return True
    
    @classmethod
    def is_configured(cls):
        """Verifica si Supabase está configurado"""
        return bool(cls.URL and cls.API_KEY)
