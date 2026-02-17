"""
Utilidades de conexión a base de datos para Streamlit
"""
import streamlit as st
from sqlalchemy import create_engine, text
from config.database import DatabaseConfig
from config.supabase import SupabaseConfig


def _set_search_path(conn):
    """
    Configura el search_path para que use el esquema siciap por defecto.
    Esto evita errores cuando las tablas están en siciap.* y las consultas
    no especifican el esquema.
    """
    try:
        conn.execute(text("SET search_path TO siciap, public"))
    except Exception:
        # No bloquear si falla; simplemente seguirá usando el search_path por defecto
        pass


# Cache de conexiones
@st.cache_resource
def get_supabase_connection():
    """
    Obtiene conexión a Supabase (para visualización)
    
    Returns:
        Conexión a Supabase
    """
    try:
        supabase_config = SupabaseConfig()
        if not supabase_config.is_configured():
            st.warning("⚠️ Supabase no está configurado. Usando conexión local.")
            return get_local_connection()
        
        conn_str = supabase_config.get_connection_string()
        engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        conn = engine.connect()
        _set_search_path(conn)
        return conn
    except Exception as e:
        err_msg = str(e).split("\n")[0][:120]  # Primera línea, acotada
        st.warning(f"Supabase no disponible ({err_msg}…). Usando PostgreSQL local.")
        return get_local_connection()


@st.cache_resource
def get_local_connection():
    """
    Obtiene conexión a PostgreSQL local (para ETL y modo local)
    
    Returns:
        Conexión a PostgreSQL local
    """
    try:
        db_config = DatabaseConfig()
        conn_str = db_config.get_connection_string()
        engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        conn = engine.connect()
        _set_search_path(conn)
        return conn
    except Exception as e:
        st.error(f"Error conectando a PostgreSQL local: {e}")
        return None


def test_connection(use_supabase: bool = True) -> bool:
    """
    Prueba la conexión a la base de datos
    
    Args:
        use_supabase: Si usar Supabase (True) o local (False)
    
    Returns:
        True si la conexión es exitosa
    """
    try:
        if use_supabase:
            conn = get_supabase_connection()
        else:
            conn = get_local_connection()
        
        if conn is None:
            return False
        
        conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
