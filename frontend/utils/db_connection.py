"""
Conexión a Supabase exclusivamente vía API REST (HTTPS 443).
Cero SQLAlchemy, psycopg2 o puerto 5432.
Credenciales en .streamlit/secrets.toml: SUPABASE_URL y SUPABASE_KEY.
"""
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error al configurar cliente Supabase: {e}")
        return None


def test_connection(use_supabase: bool = True) -> bool:
    """Prueba la conexión vía API REST. Compatible con app.py."""
    if not use_supabase:
        return False
    try:
        client = get_supabase_client()
        if client is None:
            return False
        # Prueba mínima: listar una fila de una tabla existente
        r = client.table("vista_tablero_principal").select("id_llamado").limit(1).execute()
        return True
    except Exception:
        return False


# Alias para compatibilidad: el resto del proyecto puede seguir importando este nombre.
# Ahora devuelve el cliente de la API (no una conexión SQLAlchemy).
get_supabase_connection = get_supabase_client
