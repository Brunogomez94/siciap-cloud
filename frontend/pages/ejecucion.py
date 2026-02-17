"""
Página de Ejecución
"""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection


@st.cache_data(ttl=300)
def load_ejecucion():
    """Carga datos de ejecución"""
    try:
        conn = get_supabase_connection()
        query = text("SELECT * FROM ejecucion ORDER BY fecha_ejecucion DESC LIMIT 1000")
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error cargando ejecución: {e}")
        return pd.DataFrame()


def show():
    """Muestra la página de ejecución"""
    st.title("✅ Ejecución de Contratos")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos de ejecución..."):
        df = load_ejecucion()
    
    if df.empty:
        st.warning("No hay datos de ejecución disponibles.")
        return
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        if 'licitacion' in df.columns:
            licitaciones = ['Todas'] + list(df['licitacion'].unique())
            licitacion_selected = st.selectbox("Filtrar por Licitación", licitaciones)
            if licitacion_selected != "Todas":
                df = df[df['licitacion'] == licitacion_selected]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Ítems", len(df))
    with col2:
        if 'cantidad_ejecutada' in df.columns:
            total_cantidad = df['cantidad_ejecutada'].sum()
            st.metric("Cantidad Total Ejecutada", f"{total_cantidad:,.2f}")
    with col3:
        if 'monto_total' in df.columns:
            total_monto = df['monto_total'].sum()
            st.metric("Monto Total", f"${total_monto:,.2f}")
    
    # Tabla
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()
