"""
Dashboard Editable SICIAP Cloud - Dashboard Operativo (Editar y Anexar)
Permite editar cantidad solicitada y agregar datos de contratos
"""
import streamlit as st
import pandas as pd
from sqlalchemy import text
from frontend.utils.db_connection import get_supabase_connection
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
def load_vista_unificada(limite=10000):
    """Carga la vista unificada con límite para optimizar rendimiento"""
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
        st.error(f"Error cargando vista unificada: {e}")
        return pd.DataFrame()
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def guardar_cantidad_solicitada(filas_a_guardar):
    """
    Guarda cantidad_solicitada y emitir_en en la base de datos.
    Retorna (cantidad_guardada, mensaje_error).
    """
    if not filas_a_guardar:
        return 0, ""
    conn = None
    try:
        conn = get_supabase_connection()
        if conn is None:
            return 0, "No hay conexión a Supabase."
        
        upsert = text("""
            INSERT INTO public.cantidad_solicitada
                (id_llamado, licitacion, codigo, item, cantidad_solicitada, emitir_en)
            VALUES
                (:id_llamado, :licitacion, :codigo, :item, :cantidad_solicitada, :emitir_en)
            ON CONFLICT (id_llamado, licitacion, codigo, item)
            DO UPDATE SET
                cantidad_solicitada = EXCLUDED.cantidad_solicitada,
                emitir_en = EXCLUDED.emitir_en,
                actualizado_en = now()
        """)
        
        for row in filas_a_guardar:
            emitir_en = row.get("emitir_en")
            if hasattr(emitir_en, "date"):
                emitir_en = emitir_en.date()
            if pd.isna(emitir_en) or emitir_en is None:
                emitir_en = None
            
            conn.execute(upsert, {
                "id_llamado": row["id_llamado"],
                "licitacion": row["licitacion"],
                "codigo": row["codigo"],
                "item": row["item"],
                "cantidad_solicitada": row["cantidad_solicitada"],
                "emitir_en": emitir_en,
            })
        conn.commit()
        return len(filas_a_guardar), ""
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return 0, str(e)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def guardar_datosejecucion(id_llamado, licitacion, vigente, dirigido_a, lugares, observaciones):
    """Guarda o actualiza datos de ejecución"""
    conn = None
    try:
        conn = get_supabase_connection()
        if conn is None:
            return False, "No hay conexión a Supabase."
        
        upsert = text("""
            INSERT INTO public.datosejecucion
                (id_llamado, licitacion, vigente, dirigido_a, lugares, observaciones_generales, actualizado_en)
            VALUES
                (:id_llamado, :licitacion, :vigente, :dirigido_a, :lugares, :observaciones, now())
            ON CONFLICT (id_llamado)
            DO UPDATE SET
                licitacion = EXCLUDED.licitacion,
                vigente = EXCLUDED.vigente,
                dirigido_a = EXCLUDED.dirigido_a,
                lugares = EXCLUDED.lugares,
                observaciones_generales = EXCLUDED.observaciones_generales,
                actualizado_en = now()
        """)
        
        conn.execute(upsert, {
            "id_llamado": id_llamado,
            "licitacion": licitacion or "",
            "vigente": vigente or "SI",
            "dirigido_a": dirigido_a or "",
            "lugares": lugares or "",
            "observaciones": observaciones or "",
        })
        conn.commit()
        return True, ""
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return False, str(e)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _render_gestion_pedidos():
    """Pestaña 1: Gestión de Pedidos (Grilla editable)"""
    st.markdown("### 📋 Gestión de Pedidos")
    st.caption("Editá **Cantidad solicitada** y **Ver en fecha** en la grilla. Las filas con cobertura < 1 mes se muestran en ROJO.")
    
    if not AGGrid_AVAILABLE:
        st.error("Para usar la grilla editable necesitás **streamlit-aggrid**. Instalalo con: `pip install streamlit-aggrid`")
        return
    
    limite_registros = st.number_input(
        "Máximo de registros a cargar",
        min_value=1000,
        max_value=50000,
        value=10000,
        step=1000,
        key="pedidos_limite"
    )
    
    if st.button("🔄 Cargar / Actualizar datos", key="pedidos_cargar"):
        st.session_state.pop("pedidos_df", None)
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner(f"Cargando hasta {limite_registros:,} registros..."):
        df = load_vista_unificada(limite=limite_registros)
    
    if df.empty:
        st.info("No hay datos disponibles. Sincronizá primero desde Importar Excel.")
        return
    
    # Normalizar nombres de columnas
    df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]
    
    # Eliminar duplicados: mantener solo un registro por (id_llamado, licitacion, codigo, item)
    if not df.empty:
        key_cols = ['id_llamado', 'licitacion', 'codigo', 'item']
        key_cols = [c for c in key_cols if c in df.columns]
        
        if key_cols:
            # Contar valores no nulos para priorizar registros más completos
            df['_completitud'] = df.notna().sum(axis=1)
            # Eliminar duplicados manteniendo el más completo
            df = df.sort_values('_completitud', ascending=False).drop_duplicates(
                subset=key_cols, 
                keep='first'
            ).drop(columns=['_completitud'], errors='ignore')
    
    # Mapear nombres de columnas
    column_mapping = {
        'codigo': 'codigo',
        'producto': 'producto',
        'licitacion': 'licitacion',
        'id_llamado': 'id_llamado',
        'item': 'item',
        'cantidad_solicitada': 'cantidad_solicitada',
        'ver_en_fecha': 'ver_en_fecha',
        'cobertura_meses': 'cobertura_meses',
        'nivel_stock': 'nivel_stock',
    }
    
    # Renombrar columnas para mostrar
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
    
    # Preparar columna de fecha
    if 'VER EN FECHA' not in df_display.columns:
        df_display['VER EN FECHA'] = pd.NaT
    
    # Configurar AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(resizable=True, filterable=True, sortable=True, editable=False, min_column_width=70)
    gb.configure_grid_options(rowHeight=40, domLayout="normal")
    
    # Columnas editables
    if "CANTIDAD SOLICITADA" in df_display.columns:
        gb.configure_column("CANTIDAD SOLICITADA", editable=True)
    
    if "VER EN FECHA" in df_display.columns and JsCode is not None:
        gb.configure_column(
            "VER EN FECHA",
            header_name="Ver en fecha",
            editable=True,
            cellEditor="agDateCellEditor",
            filter="agDateColumnFilter",
            cellStyle=JsCode("""
function(params) {
  if (!params.value) return null;
  var d = new Date(params.value);
  if (isNaN(d.getTime())) return null;
  var today = new Date(); today.setHours(0,0,0,0);
  var check = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  if (check < today) {
    return { backgroundColor: '#f8d7da', color: '#721c24', fontWeight: 'bold' };
  }
  if (check.getTime() === today.getTime()) {
    return { backgroundColor: '#fff3cd', color: '#000000', fontWeight: 'bold' };
  }
  return { backgroundColor: '#d4edda', color: '#155724', fontWeight: 'bold' };
}
"""),
        )
    
    # Pintar filas con cobertura < 1 mes en ROJO
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
    
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=50)
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    
    grid_options = gb.build()
    
    grid_response = AgGrid(
        df_display,
        gridOptions=grid_options,
        height=600,
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
    """Pestaña 2: Datos del Contrato (Anexar cosas)"""
    st.markdown("### 📝 Datos del Contrato")
    st.caption("Cargá datos adicionales de contratos: Vigencia, Dirigido A, Lugares de Entrega, Observaciones.")
    
    conn = None
    try:
        conn = get_supabase_connection()
        if conn is None:
            st.error("No se pudo conectar a la base de datos.")
            return
        
        # Obtener lista de id_llamado y licitaciones
        q_ids = text("""
            SELECT DISTINCT e.id_llamado, e.licitacion 
            FROM public.ejecucion e
            WHERE e.id_llamado IS NOT NULL
            ORDER BY e.id_llamado DESC
            LIMIT 1000
        """)
        ids_df = pd.read_sql(q_ids, conn)
        
        if ids_df.empty:
            st.info("No hay llamados disponibles. Cargá datos de ejecución primero.")
            return
        
        # Selector de ID Llamado / Licitación
        ids_df['display'] = ids_df['id_llamado'].astype(str) + " - " + ids_df['licitacion'].astype(str)
        opciones = ["Seleccionar..."] + ids_df['display'].tolist()
        
        seleccion = st.selectbox("Seleccionar ID Llamado / Licitación", opciones, key="datos_contrato_select")
        
        if seleccion == "Seleccionar...":
            st.info("Seleccioná un llamado para ver o editar sus datos.")
            return
        
        # Extraer id_llamado y licitacion
        id_llamado = int(seleccion.split(" - ")[0])
        licitacion = " - ".join(seleccion.split(" - ")[1:])
        
        # Cargar datos existentes si existen
        q_existente = text("""
            SELECT * FROM public.datosejecucion 
            WHERE id_llamado = :id_llamado
        """)
        datos_existente = pd.read_sql(q_existente, conn, params={"id_llamado": id_llamado})
        
        # Valores por defecto
        vigente_actual = datos_existente['vigente'].iloc[0] if not datos_existente.empty and 'vigente' in datos_existente.columns else "SI"
        dirigido_actual = datos_existente['dirigido_a'].iloc[0] if not datos_existente.empty and 'dirigido_a' in datos_existente.columns else ""
        lugares_actual = datos_existente['lugares'].iloc[0] if not datos_existente.empty and 'lugares' in datos_existente.columns else ""
        observaciones_actual = datos_existente['observaciones_generales'].iloc[0] if not datos_existente.empty and 'observaciones_generales' in datos_existente.columns else ""
        
        # Formulario
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
        
        # Botón Guardar
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
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


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
