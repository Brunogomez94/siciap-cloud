"""
Página de Órdenes
"""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection


@st.cache_data(ttl=300)
def load_ordenes():
    """Carga datos de órdenes"""
    try:
        conn = get_supabase_connection()
        query = text("SELECT * FROM ordenes ORDER BY fecha_orden DESC LIMIT 1000")
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error cargando órdenes: {e}")
        return pd.DataFrame()


def show():
    """Muestra la página de órdenes"""
    st.title("📋 Órdenes de Compra")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando órdenes..."):
        df = load_ordenes()
    
    if df.empty:
        st.warning("No hay órdenes disponibles.")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        if 'estado' in df.columns:
            estados = ['Todos'] + list(df['estado'].unique())
            estado_selected = st.selectbox("Filtrar por Estado", estados)
            if estado_selected != "Todos":
                df = df[df['estado'] == estado_selected]
    
    with col2:
        if 'proveedor' in df.columns:
            proveedores = ['Todos'] + list(df['proveedor'].dropna().unique())
            proveedor_selected = st.selectbox("Filtrar por Proveedor", proveedores)
            if proveedor_selected != "Todos":
                df = df[df['proveedor'] == proveedor_selected]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Órdenes", len(df))
    with col2:
        if 'saldo' in df.columns:
            total_saldo = df['saldo'].sum()
            st.metric("Saldo Total", f"${total_saldo:,.2f}")
    with col3:
        if 'estado' in df.columns:
            pendientes = len(df[df['estado'].str.contains('pendiente', case=False, na=False)])
            st.metric("Pendientes", pendientes)
    
    # Tabla
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
show()
