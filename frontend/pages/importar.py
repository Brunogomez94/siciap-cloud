"""
Página para importar los 5 Excel a la base local (desde Descargas o cualquier carpeta).
Todo se guarda en PostgreSQL local; Supabase es opcional después.
"""
import streamlit as st
import sys
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
    st.caption("Después de cargar, entrá al Dashboard y a Órdenes / Ejecución / Stock / Pedidos para ver los resultados. Todo funciona en local; Supabase es opcional si más adelante querés sincronizar.")


# Cuando Streamlit ejecuta este archivo directamente (st.Page), ejecutar show()
# st.Page() ejecuta el archivo como script principal, así que llamamos show() siempre
show()
