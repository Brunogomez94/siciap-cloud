"""
Dashboard Editable SICIAP Cloud - Dashboard Operativo (Editar y Anexar)
Permite editar cantidad solicitada y agregar datos de contratos.
Solo API REST de Supabase (sin SQLAlchemy).
"""
import streamlit as st
import pandas as pd
from frontend.utils.db_connection import get_supabase_client, fetch_all_data, fetch_vista_tablero_todos
from datetime import datetime, date
import time

# AgGrid (opcional)
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
    AGGrid_AVAILABLE = True
except ImportError:
    AGGrid_AVAILABLE = False
    JsCode = None


@st.cache_data(ttl=300)
def load_vista_unificada():
    """Carga TODOS los registros de la vista por lotes (40k, 100k+ sin timeout)."""
    try:
        client = get_supabase_client()
        if client is None:
            return pd.DataFrame()
        data = fetch_vista_tablero_todos(client)
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        sort_cols = [c for c in ['id_llamado', 'licitacion', 'codigo', 'item'] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error cargando vista unificada: {e}")
        return pd.DataFrame()


def guardar_cantidad_solicitada(filas_a_guardar):
    """
    Guarda cantidad_solicitada y emitir_en vía API REST (upsert).
    Retorna (cantidad_guardada, mensaje_error).
    """
    if not filas_a_guardar:
        return 0, ""
    try:
        client = get_supabase_client()
        if client is None:
            return 0, "No hay conexión a Supabase."

        registros = []
        for row in filas_a_guardar:
            emitir_en = row.get("emitir_en")
            if hasattr(emitir_en, "date"):
                emitir_en = emitir_en.isoformat() if emitir_en else None
            elif isinstance(emitir_en, str) and emitir_en:
                emitir_en = emitir_en
            elif pd.notna(emitir_en):
                try:
                    emitir_en = pd.to_datetime(emitir_en).strftime("%Y-%m-%d")
                except Exception:
                    emitir_en = None
            else:
                emitir_en = None

            registros.append({
                "id_llamado": int(row["id_llamado"]),
                "licitacion": str(row.get("licitacion", "") or ""),
                "codigo": str(row.get("codigo", "") or ""),
                "item": str(row.get("item", "") or ""),
                "cantidad_solicitada": float(row["cantidad_solicitada"]),
                "emitir_en": emitir_en,
                "actualizado_en": datetime.now().isoformat(),
            })

        client.table("cantidad_solicitada").upsert(registros).execute()
        return len(registros), ""
    except Exception as e:
        return 0, str(e)


def guardar_datosejecucion(id_llamado, licitacion, vigente, dirigido_a, lugares, observaciones):
    """Guarda o actualiza datos de ejecución vía API REST (upsert)."""
    try:
        client = get_supabase_client()
        if client is None:
            return False, "No hay conexión a Supabase."

        registro = {
            "id_llamado": int(id_llamado),
            "licitacion": licitacion or "",
            "vigente": vigente or "SI",
            "dirigido_a": dirigido_a or "",
            "lugares": lugares or "",
            "observaciones_generales": observaciones or "",
            "actualizado_en": datetime.now().isoformat(),
        }
        client.table("datosejecucion").upsert([registro]).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


def _render_gestion_pedidos():
    """Pestaña 1: Gestión de Pedidos (Grilla editable)"""
    st.markdown("### 📋 Gestión de Pedidos")
    st.caption("Editá **Cantidad solicitada** y **Ver en fecha** en la grilla. Las filas con cobertura < 1 mes se muestran en ROJO.")

    if not AGGrid_AVAILABLE:
        st.error("Para usar la grilla editable necesitás **streamlit-aggrid**. Instalalo con: `pip install streamlit-aggrid`")
        return

    if st.button("🔄 Cargar / Actualizar datos", key="pedidos_cargar"):
        st.session_state.pop("pedidos_df", None)
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Cargando todos los registros (por lotes)..."):
        df = load_vista_unificada()

    if df.empty:
        st.info("No hay datos disponibles. Sincronizá primero desde Importar Excel.")
        return

    # Normalizar nombres de columnas
    df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]

    # Eliminar duplicados
    if not df.empty:
        key_cols = ['id_llamado', 'licitacion', 'codigo', 'item']
        key_cols = [c for c in key_cols if c in df.columns]
        if key_cols:
            df['_completitud'] = df.notna().sum(axis=1)
            df = df.sort_values('_completitud', ascending=False).drop_duplicates(
                subset=key_cols,
                keep='first'
            ).drop(columns=['_completitud'], errors='ignore')

    # Renombrar columnas para mostrar (incluir estado_parque y distribucion si existen)
    df_display = df.copy()
    df_display = df_display.rename(columns={
        'codigo': 'COD',
        'producto': 'PRODUCTO',
        'licitacion': 'LICITACION',
        'id_llamado': 'ID LLAMADO',
        'item': 'ITEM',
        'cantidad_solicitada': 'CANTIDAD SOLICITADA',
        'ver_en_fecha': 'VER EN FECHA',
        'cobertura_meses': 'COBERTURA (MESES)',
        'nivel_stock': 'NIVEL STOCK',
        'stock_actual': 'STOCK ACTUAL',
        'dmp_actual': 'DMP',
    })

    if 'VER EN FECHA' not in df_display.columns:
        df_display['VER EN FECHA'] = pd.NaT

    # Sin tope de órdenes: se cargan todas (por lotes). Espacio adaptable.
    total_reg = len(df_display)
    st.caption(f"📊 **{total_reg:,}** registros cargados (sin límite; crece con tus datos).")

    filas_pagina = st.selectbox(
        "Filas por página",
        options=[50, 100, 200, 500],
        index=1,
        key="pedidos_filas_pagina",
        help="Aumentá cuando tengas más órdenes para ver más filas a la vez.",
    )

    # Configurar AgGrid: columnas legibles, sin aplastar; títulos completos y wrap en celdas.
    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=False,
        min_column_width=150,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        wrapText=True,
        autoHeight=True,
    )
    gb.configure_grid_options(rowHeight=40, domLayout="normal")

    # --- Formato numérico profesional (separador de miles) ---
    if JsCode is not None:
        value_formatter_num = JsCode("""
        function(params) {
            if (params.value == null || params.value === '') return '';
            var n = Number(params.value);
            if (isNaN(n)) return params.value;
            return n.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        }
        """)
        for col in ["CANTIDAD SOLICITADA", "COBERTURA (MESES)", "STOCK ACTUAL", "DMP"]:
            if col in df_display.columns:
                gb.configure_column(col, valueFormatter=value_formatter_num)

    # --- Semáforos: estado_parque (si existe con nombre original) o NIVEL STOCK ---
    if JsCode is not None:
        estado_jscode = JsCode("""
        function(params) {
            if (params.value == null || params.value === '') return null;
            var v = String(params.value);
            if (v.indexOf('Requiere') !== -1 || v.indexOf('Crítico') !== -1 || v.indexOf('Sin Stock') !== -1) {
                return { color: '#900000', backgroundColor: '#ffcccc', fontWeight: 'bold' };
            }
            if (v.indexOf('Adecuado') !== -1 || v.indexOf('Normal') !== -1 || v.indexOf('Óptimo') !== -1) {
                return { color: '#005000', backgroundColor: '#ccffcc' };
            }
            if (v.indexOf('Precaución') !== -1 || v.indexOf('Atención') !== -1 || v.indexOf('Sin DMP') !== -1) {
                return { color: '#856404', backgroundColor: '#ffffcc', fontWeight: 'bold' };
            }
            return null;
        }
        """)
        if "estado_parque" in df_display.columns:
            gb.configure_column("estado_parque", cellStyle=estado_jscode)
        if "NIVEL STOCK" in df_display.columns:
            gb.configure_column("NIVEL STOCK", cellStyle=estado_jscode)

        # --- Columna DMP / distribucion: resaltar como indicador clave ---
        if "DMP" in df_display.columns:
            gb.configure_column("DMP", cellStyle={'backgroundColor': '#e8f4f8', 'fontWeight': 'bold'})

    # --- Alertas de fechas: VER EN FECHA (pasada o próximos 15 días → rojo/amarillo), editable con fondo azulado ---
    if "VER EN FECHA" in df_display.columns and JsCode is not None:
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
        gb.configure_column(
            "VER EN FECHA",
            header_name="Ver en fecha",
            editable=True,
            cellEditor="agDateCellEditor",
            filter="agDateColumnFilter",
            cellStyle=fecha_alerta_jscode,
        )

    # --- Columna editable CANTIDAD SOLICITADA: fondo azulado para saber dónde escribir ---
    if "CANTIDAD SOLICITADA" in df_display.columns:
        gb.configure_column("CANTIDAD SOLICITADA", editable=True, cellStyle={'backgroundColor': '#e6f2ff'})

    if JsCode is not None and "COBERTURA (MESES)" in df_display.columns:
        gb.configure_grid_options(
            getRowStyle=JsCode("""
function(params) {
  var cobertura = params.data && params.data["COBERTURA (MESES)"];
  if (cobertura != null && cobertura < 1) {
    return { backgroundColor: '#f8d7da' };
  }
  return null;
}
""")
        )

    # Paginación: filas por página elegidas por el usuario; sin tope total de registros.
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=filas_pagina)
    gb.configure_side_bar(filters_panel=True, columns_panel=True)

    grid_options = gb.build()

    # fit_columns_on_grid_load=False evita que AgGrid aplaste todas las columnas; scroll horizontal legible.
    grid_response = AgGrid(
        df_display,
        gridOptions=grid_options,
        height=700,
        theme="light",
        data_return_mode=DataReturnMode.AS_INPUT,
        update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        key="editable_aggrid_pedidos",
    )

    edited_df = grid_response.get("data")
    if edited_df is None or not isinstance(edited_df, pd.DataFrame):
        edited_df = df_display.copy()

    # Guardar cambios
    col_save, col_refresh = st.columns(2)

    with col_save:
        if st.button("💾 Guardar cambios", type="primary", key="btn_guardar_pedidos"):
            to_save = []
            for _, row in edited_df.iterrows():
                try:
                    id_ll = row.get("ID LLAMADO")
                    lic = row.get("LICITACION")
                    cod = row.get("COD")
                    item = row.get("ITEM")

                    if pd.isna(id_ll) or pd.isna(cod):
                        continue

                    cantidad = float(pd.to_numeric(row.get("CANTIDAD SOLICITADA", 0), errors="coerce") or 0)
                    ver_fecha = row.get("VER EN FECHA")

                    if pd.notna(ver_fecha):
                        try:
                            if isinstance(ver_fecha, str):
                                ver_fecha = pd.to_datetime(ver_fecha).date()
                            elif isinstance(ver_fecha, (pd.Timestamp, datetime)):
                                ver_fecha = ver_fecha.date()
                        except Exception:
                            ver_fecha = None
                    else:
                        ver_fecha = None

                    to_save.append({
                        "id_llamado": int(id_ll),
                        "licitacion": str(lic).strip() if pd.notna(lic) else "",
                        "codigo": str(cod).strip() if pd.notna(cod) else "",
                        "item": str(item).strip() if pd.notna(item) else "",
                        "cantidad_solicitada": cantidad,
                        "emitir_en": ver_fecha,
                    })
                except Exception:
                    continue

            if to_save:
                n, err = guardar_cantidad_solicitada(to_save)
                if err:
                    st.error(f"Error al guardar: {err}")
                else:
                    st.success(f"✅ Guardados {n} registros correctamente.")
                    st.session_state.pop("pedidos_df", None)
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("No hay cambios para guardar.")

    with col_refresh:
        if st.button("🔄 Actualizar datos"):
            st.session_state.pop("pedidos_df", None)
            st.cache_data.clear()
            st.rerun()


def _render_datos_contrato():
    """Pestaña 2: Datos del Contrato (Anexar cosas) - Solo API REST."""
    st.markdown("### 📝 Datos del Contrato")
    st.caption("Cargá datos adicionales de contratos: Vigencia, Dirigido A, Lugares de Entrega, Observaciones.")

    try:
        client = get_supabase_client()
        if client is None:
            st.error("No se pudo conectar a la base de datos.")
            return

        # Lista de id_llamado y licitación desde API (todos los registros, luego deduplicar)
        all_ejecucion = fetch_all_data("ejecucion", client)
        if not all_ejecucion:
            st.info("No hay llamados disponibles. Cargá datos de ejecución primero.")
            return

        ids_df = pd.DataFrame(all_ejecucion)
        cols = [c for c in ["id_llamado", "licitacion"] if c in ids_df.columns]
        if not cols:
            st.info("No hay columnas id_llamado/licitacion en ejecución.")
            return
        ids_df = ids_df[cols].drop_duplicates().sort_values("id_llamado", ascending=False)
        ids_df['display'] = ids_df['id_llamado'].astype(str) + " - " + ids_df['licitacion'].astype(str)
        opciones = ["Seleccionar..."] + ids_df['display'].tolist()

        seleccion = st.selectbox("Seleccionar ID Llamado / Licitación", opciones, key="datos_contrato_select")

        if seleccion == "Seleccionar...":
            st.info("Seleccioná un llamado para ver o editar sus datos.")
            return

        id_llamado = int(seleccion.split(" - ")[0])
        licitacion = " - ".join(seleccion.split(" - ")[1:])

        # Cargar datos existentes de datosejecucion vía API
        r_existente = (
            client.table("datosejecucion")
            .select("*")
            .eq("id_llamado", id_llamado)
            .execute()
        )
        datos_existente = pd.DataFrame(r_existente.data) if r_existente.data else pd.DataFrame()

        vigente_actual = datos_existente['vigente'].iloc[0] if not datos_existente.empty and 'vigente' in datos_existente.columns else "SI"
        dirigido_actual = datos_existente['dirigido_a'].iloc[0] if not datos_existente.empty and 'dirigido_a' in datos_existente.columns else ""
        lugares_actual = datos_existente['lugares'].iloc[0] if not datos_existente.empty and 'lugares' in datos_existente.columns else ""
        observaciones_actual = datos_existente['observaciones_generales'].iloc[0] if not datos_existente.empty and 'observaciones_generales' in datos_existente.columns else ""

        st.markdown(f"#### Datos para ID Llamado: {id_llamado}")
        st.caption(f"Licitación: {licitacion}")

        col1, col2 = st.columns(2)
        with col1:
            vigente = st.selectbox(
                "Vigencia",
                options=["SI", "NO", "PENDIENTE DE ADENDA"],
                index=0 if vigente_actual == "SI" else 1 if vigente_actual == "NO" else 2,
                key="datos_vigente"
            )
        with col2:
            st.text_input("ID Llamado", value=str(id_llamado), disabled=True, key="datos_id_llamado")

        dirigido_a = st.text_area(
            "Dirigido A",
            value=dirigido_actual if dirigido_actual else "",
            height=100,
            key="datos_dirigido_a",
            placeholder="Ej: Hospital Central, Dirección de Abastecimiento..."
        )

        lugares = st.text_area(
            "Lugares de Entrega",
            value=lugares_actual if lugares_actual else "",
            height=100,
            key="datos_lugares",
            placeholder="Ej: Almacén Central, Depósito Norte..."
        )

        observaciones = st.text_area(
            "Observaciones Generales",
            value=observaciones_actual if observaciones_actual else "",
            height=150,
            key="datos_observaciones",
            placeholder="Observaciones adicionales sobre el contrato..."
        )

        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("💾 Guardar Datos del Contrato", type="primary", key="btn_guardar_contrato"):
                success, error = guardar_datosejecucion(
                    id_llamado=id_llamado,
                    licitacion=licitacion,
                    vigente=vigente,
                    dirigido_a=dirigido_a,
                    lugares=lugares,
                    observaciones=observaciones
                )
                if success:
                    st.success("✅ Datos guardados correctamente.")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Error al guardar: {error}")
        with col_cancel:
            if st.button("🔄 Recargar datos"):
                st.cache_data.clear()
                st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())


def show():
    """Función principal del dashboard editable"""
    st.markdown("""
    <div style="width:100%; max-width:100%; box-sizing:border-box; background-color:#1e3a5f; color:#fff; padding:14px 1.5rem; margin-bottom:20px; border-radius:8px; text-align:center;">
        <h1 style="font-size:2rem; font-weight:bold; margin:0;">✏️ Dashboard Operativo</h1>
        <p style="margin:8px 0 0 0; opacity:0.9;">Editar pedidos y anexar datos de contratos</p>
    </div>
    """, unsafe_allow_html=True)

    tab_pedidos, tab_contrato = st.tabs([
        "📋 Gestión de Pedidos",
        "📝 Datos del Contrato",
    ])

    with tab_pedidos:
        _render_gestion_pedidos()

    with tab_contrato:
        _render_datos_contrato()


show()
