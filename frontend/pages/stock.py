"""
Página de Stock Crítico
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection


@st.cache_data(ttl=300)
def load_stock():
    """Carga datos de stock. Conexión nueva; se cierra al terminar."""
    conn = None
    try:
        conn = get_supabase_connection()
        if conn is None:
            return pd.DataFrame()
        query = text("SELECT * FROM public.stock_critico ORDER BY stock_disponible ASC")
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        st.error(f"Error cargando stock: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def show():
    """Muestra la página de stock"""
    st.title("📦 Stock Crítico")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos de stock..."):
        df = load_stock()
    
    if df.empty:
        st.warning("No hay datos de stock disponibles.")
        return
    
    # Filtros
    if 'estado' in df.columns:
        estados = ['Todos'] + list(df['estado'].unique())
        estado_selected = st.selectbox("Filtrar por Estado", estados)
        if estado_selected != "Todos":
            df = df[df['estado'] == estado_selected]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Productos", len(df))
    with col2:
        if 'estado' in df.columns:
            criticos = len(df[df['estado'] == 'critico'])
            st.metric("Stock Crítico", criticos, delta=None)
    with col3:
        if 'stock_disponible' in df.columns:
            total_stock = df['stock_disponible'].sum()
            st.metric("Stock Total", f"{total_stock:,.2f}")
    
    # Gráfico
    if 'estado' in df.columns:
        st.subheader("Distribución por Estado")
        estado_counts = df['estado'].value_counts()
        fig = px.bar(
            x=estado_counts.index,
            y=estado_counts.values,
            color=estado_counts.index,
            labels={'x': 'Estado', 'y': 'Cantidad'},
            color_discrete_map={'critico': 'red', 'bajo': 'orange', 'normal': 'green'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla
    st.dataframe(df, width='stretch', hide_index=True)
    
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
show()
