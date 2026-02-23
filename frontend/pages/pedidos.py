"""
Página de Pedidos
"""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection


@st.cache_data(ttl=300)
def load_pedidos():
    """Carga datos de pedidos. Conexión nueva; se cierra al terminar."""
    conn = None
    try:
        conn = get_supabase_connection()
        if conn is None:
            return pd.DataFrame()
        query = text("SELECT * FROM public.pedidos ORDER BY fecha_solicitud DESC LIMIT 1000")
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        st.error(f"Error cargando pedidos: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def show():
    """Muestra la página de pedidos"""
    st.title("🛒 Pedidos")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando pedidos..."):
        df = load_pedidos()
    
    if df.empty:
        st.warning("No hay pedidos disponibles.")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        if 'estado' in df.columns:
            estados = ['Todos'] + list(df['estado'].unique())
            estado_selected = st.selectbox("Filtrar por Estado", estados)
            if estado_selected != "Todos":
                df = df[df['estado'] == estado_selected]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pedidos", len(df))
    with col2:
        if 'cantidad_solicitada' in df.columns:
            total_solicitada = df['cantidad_solicitada'].sum()
            st.metric("Cantidad Solicitada Total", f"{total_solicitada:,.2f}")
    with col3:
        if 'cantidad_pendiente' in df.columns:
            total_pendiente = df['cantidad_pendiente'].sum()
            st.metric("Cantidad Pendiente Total", f"{total_pendiente:,.2f}")
    
    # Tabla
    st.dataframe(df, width='stretch', hide_index=True)
    
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
show()
