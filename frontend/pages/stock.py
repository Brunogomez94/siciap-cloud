"""
Página de Stock Crítico
Solo API REST de Supabase (sin SQLAlchemy).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.utils.db_connection import get_supabase_client, fetch_all_data


@st.cache_data(ttl=300)
def load_stock():
    """Carga todos los datos de stock (paginación interna) y ordena por stock_disponible."""
    try:
        client = get_supabase_client()
        if client is None:
            return pd.DataFrame()
        data = fetch_all_data("stock_critico", client)
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        if "stock_disponible" in df.columns:
            df = df.sort_values("stock_disponible").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error cargando stock: {e}")
        return pd.DataFrame()


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

    # Drill-down: detalle de productos en estado crítico
    if 'estado' in df.columns:
        df_criticos = df[df['estado'] == 'critico']
        with st.expander("🔽 Ver detalle de productos en stock crítico"):
            if df_criticos.empty:
                st.caption("No hay productos en estado crítico.")
            else:
                st.dataframe(df_criticos, use_container_width=True, hide_index=True)
    
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
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla
    st.dataframe(df, width='stretch', hide_index=True)
    
    if st.button("🔄 Refrescar"):
        st.cache_data.clear()
        st.rerun()


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
show()
