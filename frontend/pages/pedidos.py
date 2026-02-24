"""
Página de Pedidos
Solo API REST de Supabase (sin SQLAlchemy).
"""
import streamlit as st
import pandas as pd
from frontend.utils.db_connection import get_supabase_client, fetch_all_data


@st.cache_data(ttl=300)
def load_pedidos():
    """Carga todos los datos de pedidos (paginación interna) y ordena por fecha."""
    try:
        client = get_supabase_client()
        if client is None:
            return pd.DataFrame()
        data = fetch_all_data("pedidos", client)
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        if "fecha_solicitud" in df.columns:
            df = df.sort_values("fecha_solicitud", ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error cargando pedidos: {e}")
        return pd.DataFrame()


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

    # Drill-down: detalle de pedidos con pendiente
    if 'cantidad_pendiente' in df.columns:
        df_pendientes = df[(df['cantidad_pendiente'].fillna(0) > 0)]
        with st.expander("🔽 Ver detalle de registros con cantidad pendiente"):
            if df_pendientes.empty:
                st.caption("No hay registros con cantidad pendiente.")
            else:
                st.dataframe(df_pendientes, use_container_width=True, hide_index=True)
    
    # Tabla
    st.dataframe(df, width='stretch', hide_index=True)
    
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
show()
