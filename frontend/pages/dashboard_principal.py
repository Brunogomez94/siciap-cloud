"""
Dashboard Principal SICIAP Cloud - Dashboard Gerencial (Solo Lectura)
Muestra KPIs, gráficos y análisis de datos sin edición
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection


@st.cache_data(ttl=300)
def load_vista_tablero(limite=10000):
    """Carga datos de la vista tablero principal con límite"""
    conn = None
    try:
        conn = get_supabase_connection()
        if conn is None:
            return pd.DataFrame()
        q = text(f"""
            SELECT * FROM public.vista_tablero_principal 
            ORDER BY id_llamado, licitacion, codigo, item
            LIMIT :limite
        """)
        df = pd.read_sql(q, conn, params={"limite": limite})
        conn.commit()
        return df
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        st.error(f"Error cargando vista: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def show():
    """Muestra el dashboard gerencial (solo lectura)"""
    st.markdown("""
    <div style="width:100%; max-width:100%; box-sizing:border-box; background-color:#f0f2f6; padding:12px 1.5rem; margin-bottom:20px; border-radius:5px; text-align:center;">
        <h1 style="font-size:2.5rem; font-weight:bold; margin:0; color:#262730;">📊 Dashboard Gerencial</h1>
        <p style="margin:8px 0 0 0; opacity:0.8;">Vista de solo lectura - KPIs y análisis</p>
    </div>
    """, unsafe_allow_html=True)

    # Filtros en sidebar
    st.sidebar.markdown("### 🔍 Filtros")
    limite_registros = st.sidebar.number_input(
        "Máx. registros", 
        min_value=1000, 
        max_value=50000, 
        value=10000, 
        step=1000, 
        key="dashboard_limite"
    )

    # Cargar datos
    with st.spinner(f"Cargando hasta {limite_registros:,} registros..."):
        df_vista = load_vista_tablero(limite=limite_registros)
    
    if df_vista.empty:
        st.warning("No hay datos disponibles. Sincronizá primero desde Importar Excel.")
        return
    
    # Normalizar nombres de columnas a minúsculas
    df_vista.columns = [c.lower() if isinstance(c, str) else c for c in df_vista.columns]
    
    # Eliminar duplicados: mantener solo un registro por (id_llamado, licitacion, codigo, item)
    # Prioriza el registro con más datos completos
    if not df_vista.empty:
        # Columnas clave para deduplicación
        key_cols = ['id_llamado', 'licitacion', 'codigo', 'item']
        key_cols = [c for c in key_cols if c in df_vista.columns]
        
        if key_cols:
            # Contar valores no nulos para priorizar registros más completos
            df_vista['_completitud'] = df_vista.notna().sum(axis=1)
            # Eliminar duplicados manteniendo el más completo
            df_vista = df_vista.sort_values('_completitud', ascending=False).drop_duplicates(
                subset=key_cols, 
                keep='first'
            ).drop(columns=['_completitud'], errors='ignore')
    
    # Filtros adicionales
    licitaciones = ["Todas"] + sorted(df_vista['licitacion'].dropna().unique().tolist())[:100]
    licitacion_seleccionada = st.sidebar.selectbox("Licitación", licitaciones, key="dashboard_licitacion")
    
    niveles_stock = ["Todos", "Crítico", "Atención", "Óptimo", "Sin DMP", "Sin Stock"]
    nivel_seleccionado = st.sidebar.selectbox("Nivel Stock", niveles_stock, key="dashboard_nivel")
    
    # Aplicar filtros
    df_filtrado = df_vista.copy()
    if licitacion_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado['licitacion'] == licitacion_seleccionada]
    if nivel_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nivel_stock'] == nivel_seleccionado]

    # KPIs Superiores
    st.markdown("---")
    st.markdown("### 📈 Indicadores Clave (KPIs)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(df_filtrado)
        st.metric("Total Ítems", f"{total_items:,}")
    
    with col2:
        items_criticos = len(df_filtrado[df_filtrado['nivel_stock'].isin(['Crítico', 'Sin Stock'])])
        delta_pct = f"{items_criticos/total_items*100:.1f}%" if total_items > 0 else "0%"
        st.metric("Ítems Críticos", f"{items_criticos:,}", delta=delta_pct)
    
    with col3:
        # Monto total estimado: cantidad_maxima * precio_unitario promedio
        precio_promedio = df_filtrado['precio_unitario'].fillna(0).mean()
        cantidad_total = df_filtrado['cantidad_maxima'].sum()
        monto_total = cantidad_total * precio_promedio if precio_promedio > 0 else 0
        st.metric("Monto Total Estimado", f"${monto_total:,.0f}" if monto_total > 0 else "$0")
    
    with col4:
        cantidad_solicitada_total = df_filtrado['cantidad_solicitada'].sum()
        st.metric("Cantidad Solicitada", f"{cantidad_solicitada_total:,.0f}")
    
    st.markdown("---")
    
    # Gráficos
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📊 Consumo por Licitación")
        consumo_por_lic = df_filtrado.groupby('licitacion').agg({
            'cantidad_maxima': 'sum',
            'cantidad_emitida': 'sum'
        }).reset_index()
        consumo_por_lic = consumo_por_lic.sort_values('cantidad_maxima', ascending=False).head(10)
        
        if not consumo_por_lic.empty:
            fig_bar = px.bar(
                consumo_por_lic,
                x='licitacion',
                y=['cantidad_maxima', 'cantidad_emitida'],
                title="Cantidad Máxima vs Emitida",
                labels={'value': 'Cantidad', 'licitacion': 'Licitación'},
                barmode='group'
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")
    
    with col_chart2:
        st.markdown("#### 🥧 Distribución de Nivel de Stock")
        distribucion_stock = df_filtrado['nivel_stock'].value_counts()
        
        if not distribucion_stock.empty:
            fig_pie = px.pie(
                values=distribucion_stock.values,
                names=distribucion_stock.index,
                title="Nivel de Stock",
                color_discrete_map={
                    'Crítico': 'red',
                    'Sin Stock': 'darkred',
                    'Atención': 'orange',
                    'Óptimo': 'green',
                    'Sin DMP': 'gray'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay datos para mostrar")
    
    st.markdown("---")
    
    # Tabla resumen
    st.markdown("### 📋 Resumen de Datos")
    st.caption(f"Mostrando {len(df_filtrado):,} registros de {len(df_vista):,} totales")
    
    # Columnas principales para mostrar
    columnas_mostrar = [
        'licitacion', 'codigo', 'producto', 'cantidad_maxima', 
        'cantidad_emitida', 'saldo_contrato', 'stock_actual', 
        'dmp_actual', 'nivel_stock', 'cantidad_solicitada', 'cobertura_meses'
    ]
    columnas_mostrar = [c for c in columnas_mostrar if c in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[columnas_mostrar].head(1000),
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Tabla completa en expander
    with st.expander("📊 Ver tabla completa (máx. 1000 registros)"):
        st.dataframe(df_filtrado.head(1000), use_container_width=True, hide_index=True)


show()
