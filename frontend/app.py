"""
Aplicación principal Streamlit para SICIAP Cloud
Portero: Bloquea Importar Excel en la web, solo disponible en local
"""
import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables locales si existen (solo funciona en tu PC)
load_dotenv()

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from frontend.utils.db_connection import test_connection

st.set_page_config(
    page_title="SICIAP Cloud - Sistema Integrado",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LÓGICA DE DETECCIÓN (EL FILTRO) ---
# En tu PC, DB_HOST suele ser 'localhost' o estar vacío si usa defaults.
# En la Nube, DB_HOST será 'aws-0-us-...' o lo que pusimos en Secrets.
db_host = os.getenv("DB_HOST", "localhost")

# SI EL HOST ES 'localhost', ESTAMOS EN TU PC.
ES_LOCAL = "localhost" in db_host or "127.0.0.1" in db_host

# Verificar conexiones para mostrar estado
supabase_connected = test_connection(use_supabase=True)
local_connected = test_connection(use_supabase=False)

# Indicador de estado
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
# Estas páginas las ve todo el mundo (Jefes, Web, Tú)
# Las rutas son relativas al directorio raíz del proyecto
pages_publicas = [
    st.Page("frontend/pages/dashboard.py", title="📊 Dashboard General", icon="📈", default=True),
    st.Page("frontend/pages/ordenes.py", title="📋 Órdenes de Compra", icon="📋"),
    st.Page("frontend/pages/ejecucion.py", title="📊 Ejecución Contratos", icon="📊"),
    st.Page("frontend/pages/stock.py", title="📦 Stock y Parques", icon="📦"),
    st.Page("frontend/pages/pedidos.py", title="📝 Pedidos", icon="📝"),
]

# Esta página es SOLO PARA TI (Local)
page_admin = st.Page("frontend/pages/importar.py", title="📥 Importar Excel (Local)", icon="💾")

# --- CONSTRUCCIÓN DEL MENÚ ---
if ES_LOCAL:
    # ESTÁS EN TU PC: Se carga todo
    pg = st.navigation({
        "📊 Panel de Control": pages_publicas,
        "⚙️ Zona de Trabajo (Solo Local)": [page_admin] 
    })
else:
    # ESTÁS EN LA WEB: La página de importar NO EXISTE aquí
    pg = st.navigation({
        "📊 Panel de Control": pages_publicas
    })

pg.run()
