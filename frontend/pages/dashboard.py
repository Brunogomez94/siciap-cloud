"""
Dashboard SICIAP - Vencimientos y Distribución.
Solo API REST de Supabase (sin SQLAlchemy). Columnas obligatorias de diseño:
distribucion, parque_regentes, estado_parque, estado_administrativo.
UI: semáforos de stock, alertas de vencimientos, formato numérico profesional.
"""
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from frontend.utils.db_connection import get_supabase_client, fetch_vista_tablero
from datetime import datetime

supabase = get_supabase_client()

st.title("Dashboard SICIAP - Vencimientos y Distribución")

@st.cache_data(ttl=300)
def load_data():
    if not supabase:
        return pd.DataFrame()
    try:
        data = fetch_vista_tablero(supabase)
        if data:
            return pd.DataFrame(data)
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

    # --- Formato numérico (separador de miles) ---
    value_formatter_num = JsCode("""
    function(params) {
        if (params.value == null || params.value === '') return '';
        var n = Number(params.value);
        if (isNaN(n)) return params.value;
        return n.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    }
    """)
    columnas_numericas = ['cantidad_solicitada', 'cantidad_maxima', 'cantidad_emitida', 'saldo_contrato',
                          'stock_actual', 'dmp_actual', 'cobertura_meses', 'distribucion', 'parque_regentes']
    for col in columnas_numericas:
        if col in df.columns:
            gb.configure_column(col, valueFormatter=value_formatter_num)

    # --- Semáforos: estado_parque (Requiere/Crítico → rojo, Adecuado/Normal → verde, Precaución → amarillo) ---
    estado_parque_jscode = JsCode("""
    function(params) {
        if (params.value == null || params.value === '') return null;
        var v = String(params.value);
        if (v.indexOf('Requiere') !== -1 || v.indexOf('Crítico') !== -1) {
            return { color: '#900000', backgroundColor: '#ffcccc', fontWeight: 'bold' };
        }
        if (v.indexOf('Adecuado') !== -1 || v.indexOf('Normal') !== -1) {
            return { color: '#005000', backgroundColor: '#ccffcc' };
        }
        if (v.indexOf('Precaución') !== -1 || v.indexOf('Atención') !== -1) {
            return { color: '#856404', backgroundColor: '#ffffcc', fontWeight: 'bold' };
        }
        return null;
    }
    """)
    if 'estado_parque' in df.columns:
        gb.configure_column('estado_parque', cellStyle=estado_parque_jscode)

    # --- Columna distribucion (DMP): resaltar como indicador clave ---
    if 'distribucion' in df.columns:
        gb.configure_column('distribucion', cellStyle={'backgroundColor': '#e8f4f8', 'fontWeight': 'bold'})

    # --- Alertas de fechas: ver_en_fecha (pasada o próximos 15 días → rojo/amarillo) ---
    fecha_alerta_jscode = JsCode("""
    function(params) {
        if (!params.value) return { backgroundColor: '#e6f2ff' };
        var d = new Date(params.value);
        if (isNaN(d.getTime())) return { backgroundColor: '#e6f2ff' };
        var today = new Date(); today.setHours(0,0,0,0);
        var check = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        var diffDays = Math.round((check - today) / (1000*60*60*24));
        if (diffDays < 0) {
            return { backgroundColor: '#ffcccc', color: '#721c24', fontWeight: 'bold' };
        }
        if (diffDays <= 15) {
            return { backgroundColor: '#fff3cd', color: '#856404', fontWeight: 'bold' };
        }
        return { backgroundColor: '#d4edda', color: '#155724' };
    }
    """)

    # --- Columnas editables: fondo azulado para identificar dónde escribir ---
    if 'cantidad_solicitada' in df.columns:
        gb.configure_column('cantidad_solicitada', editable=True, type=["numericColumn"],
                            cellStyle={'backgroundColor': '#e6f2ff'})
    if 'ver_en_fecha' in df.columns:
        gb.configure_column('ver_en_fecha', editable=True, cellStyle=fecha_alerta_jscode)

    # Columnas fijas
    columnas_fijas = ['id_llamado', 'codigo', 'producto']
    for col in columnas_fijas:
        if col in df.columns:
            gb.configure_column(col, pinned='left')

    # Columnas de gestión (parque_regentes, estado_administrativo mantienen estilo neutro)
    for col in ['parque_regentes', 'estado_administrativo']:
        if col in df.columns:
            gb.configure_column(col, cellStyle={'backgroundColor': '#f0f2f6'})

    # Paginación para no congelar el navegador con miles de filas
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)

    gridOptions = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=False,
        theme='streamlit',
        height=700,
        allow_unsafe_jscode=True,
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
