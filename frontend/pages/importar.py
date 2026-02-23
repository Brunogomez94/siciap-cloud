"""
Página para importar los 5 Excel a la base local (desde Descargas o cualquier carpeta).
Todo se guarda en PostgreSQL local; Supabase es opcional después.
"""
import streamlit as st
import sys
import pandas as pd
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from etl.processors import (
    OrdenesProcessor,
    EjecucionProcessor,
    StockProcessor,
    PedidosProcessor,
    VencimientosParquesProcessor,
)
from etl.sync.sync_manager import SyncManager
from config.supabase import SupabaseConfig

# Orden: 1 Órdenes, 2 Ejecución, 3 Stock, 4 Pedidos, 5 Vencimientos
CARGA = [
    ("Órdenes", OrdenesProcessor, "ordenes"),
    ("Ejecución", EjecucionProcessor, "ejecucion"),
    ("Stock crítico", StockProcessor, "stock_critico"),
    ("Pedidos", PedidosProcessor, "pedidos"),
    ("Vencimientos (PNC/parques)", VencimientosParquesProcessor, "vencimientos_parques"),
]


def show():
    import os
    # Verificar si estamos en Streamlit Cloud (no debería aparecer aquí, pero por seguridad)
    is_cloud = os.getenv('STREAMLIT_SHARING_MODE') == 'sharing'
    
    if is_cloud:
        st.error("⚠️ Esta funcionalidad solo está disponible en la aplicación local.")
        st.info("""
        **Para importar Excel:**
        1. Abre la aplicación local en tu PC: `scripts\\run_frontend.bat`
        2. Ve a la página "Importar Excel"
        3. Sube tus archivos desde allí
        
        Los datos se guardarán en PostgreSQL local y luego podrás sincronizarlos a Supabase.
        """)
        return
    
    st.title("Importar Excel")
    st.markdown("Subí los 5 archivos Excel (desde Descargas o donde los tengas). Se cargan en la base **local**; el dashboard y las pestañas usan estos datos.")
    st.markdown("---")

    for titulo, ProcessorClass, key_suffix in CARGA:
        with st.expander(f"**{titulo}**", expanded=True):
            # Vencimientos acepta también CSV (ej. Stock_en_PNCs_data.csv)
            tipos = ["xlsx", "xls", "csv"] if key_suffix == "vencimientos_parques" else ["xlsx", "xls"]
            archivo = st.file_uploader(
                f"Archivo para {titulo}" + (" (Excel o CSV)" if key_suffix == "vencimientos_parques" else ""),
                type=tipos,
                key=f"importar_{key_suffix}",
                help="Seleccioná el archivo desde tu PC (ej. Descargas).",
            )
            if archivo is not None:
                if st.button(f"Cargar {titulo}", key=f"btn_{key_suffix}"):
                    with st.spinner(f"Cargando {archivo.name}..."):
                        try:
                            contenido = archivo.getvalue()
                            proc = ProcessorClass()
                            if proc.process_file(contenido, archivo.name):
                                st.cache_data.clear()
                                st.success(f"Listo: {archivo.name} cargado en la base local. Podés ir al Dashboard para ver los datos.")
                            else:
                                st.error(f"No se pudo procesar {archivo.name}. Revisá columnas y formato.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                            st.exception(e)

    st.markdown("---")
    
    # Sección de sincronización con Supabase
    st.markdown("### 🔄 Sincronizar con Supabase")
    st.markdown("Después de cargar los archivos localmente, podés sincronizarlos a Supabase para que aparezcan en la web.")
    
    # Verificar si Supabase está configurado
    supabase_config = SupabaseConfig()
    supabase_configured = supabase_config.is_configured()
    
    if not supabase_configured:
        st.warning("⚠️ Supabase no está configurado. Verificá tu archivo `.env` con las credenciales de Supabase.")
        st.info("""
        **Para configurar Supabase:**
        1. Abrí el archivo `.env` en la raíz del proyecto
        2. Agregá las variables:
           - `SUPABASE_URL=tu_url_de_supabase`
           - `SUPABASE_DB_HOST=aws-1-us-east-1.pooler.supabase.com`
           - `SUPABASE_DB_USER=postgres.tu_project_ref`
           - `SUPABASE_DB_PASSWORD=tu_password`
        3. Reiniciá la aplicación
        """)
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("💡 **Consejo:** Cargá primero todos los archivos Excel localmente, y luego sincronizá todo de una vez.")
        
        with col2:
            if st.button("🔄 Sincronizar todo a Supabase", type="primary"):
                sync_manager = SyncManager()
                
                with st.spinner("Sincronizando datos a Supabase..."):
                    try:
                        # Crear un contenedor para mostrar el progreso
                        progress_container = st.container()
                        status_text = progress_container.empty()
                        
                        # Sincronizar todas las tablas
                        status_text.info("🔄 Iniciando sincronización...")
                        results = sync_manager.sync_all_tables()
                        
                        # Mostrar resultados
                        status_text.empty()
                        
                        st.success("✅ Sincronización completada!")
                        
                        # Mostrar resumen por tabla
                        st.markdown("#### Resumen de sincronización:")
                        summary_data = []
                        for table, result in results.items():
                            status = "✅" if result['success'] else "❌"
                            summary_data.append({
                                "Tabla": table,
                                "Estado": status,
                                "Sincronizado": result.get('synced_at', 'N/A')[:19] if result.get('synced_at') else 'N/A'
                            })
                        
                        if summary_data:
                            df_summary = pd.DataFrame(summary_data)
                            st.dataframe(df_summary, width='stretch', hide_index=True)
                        
                        # Verificar sincronización
                        st.markdown("#### Verificación:")
                        verification_data = []
                        for table in SyncManager.TABLES_TO_SYNC:
                            try:
                                verification = sync_manager.verify_sync(table)
                                if 'error' not in verification:
                                    match_icon = "✅" if verification['match'] else "⚠️"
                                    verification_data.append({
                                        "Tabla": table,
                                        "Estado": match_icon,
                                        "Local": verification['local_count'],
                                        "Supabase": verification['supabase_count'],
                                        "Diferencia": verification['difference']
                                    })
                                else:
                                    verification_data.append({
                                        "Tabla": table,
                                        "Estado": "❌",
                                        "Local": "N/A",
                                        "Supabase": "N/A",
                                        "Diferencia": verification.get('error', 'Error')[:50]
                                    })
                            except Exception as e:
                                verification_data.append({
                                    "Tabla": table,
                                    "Estado": "❌",
                                    "Local": "N/A",
                                    "Supabase": "N/A",
                                    "Diferencia": str(e)[:50]
                                })
                        
                        if verification_data:
                            df_verification = pd.DataFrame(verification_data)
                            st.dataframe(df_verification, width='stretch', hide_index=True)
                        
                        st.info("💡 Los datos ahora deberían aparecer en la aplicación web: https://sistema-compl-siciap.streamlit.app/")
                        
                    except Exception as e:
                        st.error(f"❌ Error al sincronizar: {str(e)}")
                        st.exception(e)
                        st.warning("""
                        **Posibles causas:**
                        - No hay conexión a internet o firewall bloqueando Supabase
                        - Credenciales incorrectas en `.env`
                        - Supabase no está accesible desde tu red
                        
                        **Solución:** Intentá conectarte con el WiFi del celular o verificar las credenciales.
                        """)
    
    st.markdown("---")
    st.caption("Después de cargar, entrá al Dashboard y a Órdenes / Ejecución / Stock / Pedidos para ver los resultados. Todo funciona en local; Supabase es opcional si más adelante querés sincronizar.")


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
# st.Page() ejecuta el archivo como script principal, así que llamamos show() siempre
show()
