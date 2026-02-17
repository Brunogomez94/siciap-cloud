"""
Aplicación principal Streamlit para SICIAP Cloud
Usa navegación nativa (st.navigation) para menú profesional
"""
import streamlit as st
import os
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from frontend.utils.db_connection import test_connection

# Determinar rutas de páginas según el entorno
# En Streamlit Cloud, el directorio de trabajo es la raíz del proyecto
# En local, también ejecutamos desde la raíz
_app_dir = Path(__file__).parent
_pages_dir = _app_dir / "pages"

# Verificar si las páginas están en frontend/pages/ (estructura actual)
if (_pages_dir / "dashboard.py").exists():
    # Estructura: frontend/pages/dashboard.py (relativo a raíz: frontend/pages/)
    PAGE_PREFIX = "frontend/pages/"
else:
    # Fallback: buscar en pages/ en la raíz
    if (root_dir / "pages" / "dashboard.py").exists():
        PAGE_PREFIX = "pages/"
    else:
        PAGE_PREFIX = "frontend/pages/"  # Default

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SICIAP Cloud - Sistema Integrado",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DETECCIÓN DE ENTORNO ---
# Si DB_HOST contiene localhost, estamos en local. Si no, estamos en la nube.
DB_HOST = os.getenv("DB_HOST", "")
ES_LOCAL = "localhost" in DB_HOST or "127.0.0.1" in DB_HOST or DB_HOST == ""

# Verificar conexiones para mostrar estado
supabase_connected = test_connection(use_supabase=True)
local_connected = test_connection(use_supabase=False)

# Indicador de estado en la parte superior
if supabase_connected:
    st.markdown('<div style="position: fixed; top: 10px; right: 10px; background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px; z-index: 1000;">🟢 Supabase Conectado</div>', unsafe_allow_html=True)
elif local_connected:
    st.markdown('<div style="position: fixed; top: 10px; right: 10px; background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 5px; font-size: 12px; z-index: 1000;">🟡 Modo Local</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="position: fixed; top: 10px; right: 10px; background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px; z-index: 1000;">🔴 Sin Conexión</div>', unsafe_allow_html=True)

# Título principal
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #0e4f3c;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🏥 SICIAP Cloud</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Sistema Integrado de Gestión - Arquitectura Híbrida</p>', unsafe_allow_html=True)

# --- DEFINICIÓN DE PÁGINAS ---
# Mapeamos archivos a nombres profesionales con iconos usando la ruta detectada
pg_dashboard = st.Page(f"{PAGE_PREFIX}dashboard.py", title="📊 Dashboard General", icon="📈", default=True)
pg_ordenes = st.Page(f"{PAGE_PREFIX}ordenes.py", title="📋 Órdenes de Compra", icon="📋")
pg_ejecucion = st.Page(f"{PAGE_PREFIX}ejecucion.py", title="📊 Ejecución Contratos", icon="📊")
pg_stock = st.Page(f"{PAGE_PREFIX}stock.py", title="📦 Stock y Parques", icon="📦")
pg_pedidos = st.Page(f"{PAGE_PREFIX}pedidos.py", title="📝 Pedidos", icon="📝")

# Esta es la página conflictiva - solo en local
pg_importar = st.Page(f"{PAGE_PREFIX}importar.py", title="📥 Importar Excel", icon="📥")

# --- LÓGICA DEL MENÚ ---
if ES_LOCAL and local_connected:
    # EN TU PC: Muestra todo, incluyendo Importar
    pg = st.navigation({
        "📊 Principal": [pg_dashboard],
        "📋 Gestión": [pg_ordenes, pg_ejecucion, pg_stock, pg_pedidos],
        "⚙️ Administración": [pg_importar]  # <--- Solo aparece en local
    })
else:
    # EN LA NUBE: Oculta Importar y agrupa bonito
    pg = st.navigation({
        "📊 Principal": [pg_dashboard],
        "📋 Gestión": [pg_ordenes, pg_ejecucion, pg_stock, pg_pedidos]
        # La sección de Importar NO existe aquí
    })

# --- EJECUTAR NAVEGACIÓN ---
pg.run()
