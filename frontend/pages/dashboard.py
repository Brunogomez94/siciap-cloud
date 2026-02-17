"""
Página de Dashboard principal
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection
from frontend.utils.formatters import format_numeric, format_date, format_currency


@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_dashboard_data():
    """Carga datos para el dashboard"""
    try:
        conn = get_supabase_connection()

        # Intentar usar vista materializada si existe
        try:
            query = text("SELECT * FROM vista_unificada LIMIT 10000")
            df = pd.read_sql(query, conn)
        except Exception:
            # Si no existe la vista u ocurre un error, hacer rollback
            # para limpiar la transacción fallida y luego usar query manual.
            try:
                # conn puede ser un objeto Connection de SQLAlchemy
                conn.exec_driver_sql("ROLLBACK")
            except Exception:
                # Si falla el rollback, continuamos igualmente con la consulta manual
                pass

            # Construir query manual
            query = text("""
                SELECT 
                    e.id_llamado,
                    e.licitacion,
                    e.codigo,
                    e.item,
                    COALESCE(e.precio_unitario, de.precio_unitario) as precio_unitario,
                    e.cantidad_ejecutada,
                    COALESCE(cs.cantidad_solicitada, 0) as cantidad_solicitada,
                    cs.emitir_en,
                    de.vigente,
                    de.dirigido_a,
                    de.lugares,
                    de.descripcion_llamado,
                    s.stock_disponible as stock_actual,
                    s.estado as estado_stock,
                    o.estado as estado_orden,
                    o.saldo as saldo_orden
                FROM ejecucion e
                LEFT JOIN datosejecucion de ON e.id_llamado = de.id_llamado
                LEFT JOIN cantidad_solicitada cs 
                    ON e.id_llamado = cs.id_llamado 
                    AND e.licitacion = cs.licitacion 
                    AND e.codigo = cs.codigo 
                    AND e.item = cs.item
                LEFT JOIN stock_critico s ON e.codigo = s.codigo
                LEFT JOIN ordenes o 
                    ON e.id_llamado = o.id_llamado 
                    AND e.codigo = o.codigo
                LIMIT 10000
            """)
            df = pd.read_sql(query, conn)
        
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()


def show():
    """Muestra la página del dashboard"""
    st.title("📊 Dashboard Principal")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        df = load_dashboard_data()
    
    if df.empty:
        st.warning("No hay datos disponibles. Ejecuta la sincronización primero.")
        return
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(df)
        st.metric("Total de Ítems", f"{total_items:,}")
    
    with col2:
        total_llamados = df['id_llamado'].nunique()
        st.metric("Llamados Activos", f"{total_llamados:,}")
    
    with col3:
        vigentes = df['vigente'].sum() if 'vigente' in df.columns else 0
        st.metric("Contratos Vigentes", f"{vigentes:,}")
    
    with col4:
        stock_critico = len(df[df.get('estado_stock', pd.Series()) == 'critico']) if 'estado_stock' in df.columns else 0
        st.metric("Stock Crítico", f"{stock_critico:,}", delta=None)
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ejecución por Licitación")
        if 'licitacion' in df.columns and 'cantidad_ejecutada' in df.columns:
            ejecucion_by_licitacion = df.groupby('licitacion')['cantidad_ejecutada'].sum().reset_index()
            ejecucion_by_licitacion = ejecucion_by_licitacion.sort_values('cantidad_ejecutada', ascending=False).head(10)
            
            fig = px.bar(
                ejecucion_by_licitacion,
                x='licitacion',
                y='cantidad_ejecutada',
                labels={'licitacion': 'Licitación', 'cantidad_ejecutada': 'Cantidad Ejecutada'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Estado de Stock")
        if 'estado_stock' in df.columns:
            estado_counts = df['estado_stock'].value_counts()
            fig = px.pie(
                values=estado_counts.values,
                names=estado_counts.index,
                title="Distribución de Estados de Stock"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de datos
    st.markdown("---")
    st.subheader("Vista de Datos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        if 'vigente' in df.columns:
            filtro_vigente = st.selectbox("Filtrar por Vigencia", ["Todos", "Vigentes", "No Vigentes"])
            if filtro_vigente == "Vigentes":
                df = df[df['vigente'] == True]
            elif filtro_vigente == "No Vigentes":
                df = df[df['vigente'] == False]
    
    with col2:
        if 'estado_stock' in df.columns:
            filtro_stock = st.selectbox("Filtrar por Estado de Stock", ["Todos", "Crítico", "Bajo", "Normal"])
            if filtro_stock != "Todos":
                df = df[df['estado_stock'] == filtro_stock.lower()]
    
    # Mostrar tabla
    st.dataframe(
        df.head(100),
        use_container_width=True,
        hide_index=True
    )
    
    # Botón para refrescar
    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()
