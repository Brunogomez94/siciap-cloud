"""
Conexión a Supabase exclusivamente vía API REST (HTTPS 443).
Cero SQLAlchemy, psycopg2 o puerto 5432.
Credenciales en .streamlit/secrets.toml: SUPABASE_URL y SUPABASE_KEY.
"""
import streamlit as st
from supabase import create_client, Client
from typing import Optional, List, Any


def fetch_all_data(table_name: str, supabase_client: Optional[Client], page_size: int = 1000) -> List[Any]:
    """
    Trae todos los registros de una **tabla** usando paginación interna (.range).
    No usar para vistas pesadas (ej. vista_tablero_principal): usar fetch_vista_tablero().
    """
    if supabase_client is None:
        return []
    all_data = []
    start = 0
    try:
        while True:
            end = start + page_size - 1  # PostgREST: range inclusivo
            response = supabase_client.table(table_name).select("*").range(start, end).execute()
            data = getattr(response, "data", []) or []
            if not data:
                break
            all_data.extend(data)
            if len(data) < page_size:
                break
            start += page_size
    except Exception as e:
        st.error(f"Error paginando {table_name}: {e}")
    return all_data


# Tamaño de cada petición al cargar la vista (solo para no hacer timeout). NO hay tope total.
CHUNK_SIZE_VISTA = 8000
# Límite para una sola petición (solo dashboard_principal/dashboard que no usan lotes).
VISTA_TABLERO_LIMIT = 15000


def fetch_vista_tablero(supabase_client: Optional[Client], limit: Optional[int] = None) -> List[Any]:
    """
    Carga la vista tablero principal en una sola petición (hasta `limit` filas).
    Para cargar TODO usar fetch_vista_tablero_todos().
    """
    if supabase_client is None:
        return []
    cap = min(limit or VISTA_TABLERO_LIMIT, VISTA_TABLERO_LIMIT)
    try:
        response = supabase_client.table("vista_tablero_principal").select("*").limit(cap).execute()
        return getattr(response, "data", []) or []
    except Exception as e:
        st.error(f"Error cargando vista tablero: {e}")
        return []


def fetch_vista_tablero_todos(supabase_client: Optional[Client]) -> List[Any]:
    """
    Carga TODOS los registros de la vista por lotes. Sin límite total: crece con tus datos
    (40k, 100k, 200k...). Solo se limita el tamaño de cada petición (CHUNK_SIZE_VISTA).
    """
    if supabase_client is None:
        return []
    all_data: List[Any] = []
    start = 0
    try:
        while True:
            end = start + CHUNK_SIZE_VISTA - 1  # PostgREST: range inclusivo
            response = (
                supabase_client.table("vista_tablero_principal")
                .select("*")
                .order("id_llamado")
                .order("licitacion")
                .order("codigo")
                .order("item")
                .range(start, end)
                .execute()
            )
            data = getattr(response, "data", []) or []
            if not data:
                break
            all_data.extend(data)
            if len(data) < CHUNK_SIZE_VISTA:
                break
            start += CHUNK_SIZE_VISTA
    except Exception as e:
        st.error(f"Error cargando vista tablero por lotes: {e}")
    return all_data


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
