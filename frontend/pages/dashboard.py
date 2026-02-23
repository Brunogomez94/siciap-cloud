"""
Dashboard SICIAP - Vencimientos y Distribución.
Solo API REST de Supabase (sin SQLAlchemy). Columnas obligatorias de diseño:
distribucion, parque_regentes, estado_parque, estado_administrativo.
"""
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from frontend.utils.db_connection import get_supabase_client
from datetime import datetime

supabase = get_supabase_client()

st.title("Dashboard SICIAP - Vencimientos y Distribución")

@st.cache_data(ttl=300)
def load_data():
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table("vista_tablero_principal").select("*").limit(10000).execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error cargando datos de la API: {e}")
        return pd.DataFrame()

df = load_data()

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()

if df.empty:
    st.warning("No hay datos disponibles. Ejecuta la sincronización primero o verifica la conexión.")
else:
    st.write("### Tabla de Gestión de Pedidos (~3 meses aproximados)")
    
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(editable=False, filter=True, sortable=True)
    
    # Columnas editables
    if 'cantidad_solicitada' in df.columns:
        gb.configure_column('cantidad_solicitada', editable=True, type=["numericColumn"])
    if 'ver_en_fecha' in df.columns:
        gb.configure_column('ver_en_fecha', editable=True)

    # Columnas fijas
    columnas_fijas = ['id_llamado', 'codigo', 'producto']
    for col in columnas_fijas:
        if col in df.columns:
            gb.configure_column(col, pinned='left')

    # Columnas de gestión requeridas (diseño anterior)
    columnas_gestion = ['parque_regentes', 'estado_parque', 'estado_administrativo', 'distribucion']
    for col in columnas_gestion:
        if col in df.columns:
            gb.configure_column(col, cellStyle={'backgroundColor': '#f0f2f6'})

    gridOptions = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=False,
        theme='streamlit',
        height=600
    )

    if st.button("💾 Guardar cambios"):
        df_editado = pd.DataFrame(grid_response['data'])
        df_cambios = df_editado.compare(df, keep_shape=False, keep_equal=False)
        
        if df_cambios.empty:
            st.info("No se detectaron cambios para guardar.")
        else:
            registros_a_guardar = []
            filas_modificadas = df_cambios.index.unique()
            
            for idx in filas_modificadas:
                fila_actual = df_editado.loc[idx]
                
                fecha_emitir = fila_actual.get('ver_en_fecha')
                if isinstance(fecha_emitir, pd.Timestamp):
                    fecha_emitir = fecha_emitir.strftime('%Y-%m-%d')
                
                registro = {
                    "id_llamado": int(fila_actual['id_llamado']),
                    "licitacion": str(fila_actual.get('licitacion', '')),
                    "codigo": str(fila_actual['codigo']),
                    "item": str(fila_actual.get('item', '')),
                    "cantidad_solicitada": float(fila_actual['cantidad_solicitada']),
                    "emitir_en": fecha_emitir,
                    "actualizado_en": datetime.now().isoformat()
                }
                registros_a_guardar.append(registro)

            try:
                resultado = supabase.table("cantidad_solicitada").upsert(registros_a_guardar).execute()
                st.success(f"¡Se guardaron {len(registros_a_guardar)} registros correctamente!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar los cambios en la API: {e}")
