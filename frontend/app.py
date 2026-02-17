"""
Aplicación principal Streamlit para SICIAP Cloud
"""
import streamlit as st
from streamlit_option_menu import option_menu
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from frontend.pages import dashboard, ordenes, ejecucion, stock, pedidos, importar
from frontend.utils.db_connection import test_connection

# Configuración de la página
st.set_page_config(
    page_title="SICIAP Cloud - Sistema Integrado",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #0e4f3c;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .status-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background-color: #28a745;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 1000;
    }
</style>
""", unsafe_allow_html=True)


def is_running_on_streamlit_cloud():
    """Detecta si la app está corriendo en Streamlit Cloud"""
    import os
    # Streamlit Cloud tiene estas variables de entorno
    return os.getenv('STREAMLIT_SHARING_MODE') == 'sharing' or os.getenv('STREAMLIT_SERVER_PORT') is not None


def main():
    """Función principal de la aplicación"""
    
    # Detectar si estamos en Streamlit Cloud
    is_cloud = is_running_on_streamlit_cloud()
    
    # Verificar conexiones
    supabase_connected = test_connection(use_supabase=True)
    local_connected = test_connection(use_supabase=False)
    
    # Indicador de estado
    if supabase_connected:
        st.markdown('<div class="status-indicator">🟢 Supabase Conectado</div>', unsafe_allow_html=True)
    elif local_connected:
        st.markdown('<div class="status-indicator">🟡 Modo Local</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator">🔴 Sin Conexión</div>', unsafe_allow_html=True)
    
    # Título principal
    st.markdown('<h1 class="main-header">🏥 SICIAP Cloud</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Sistema Integrado de Gestión - Arquitectura Híbrida</p>', unsafe_allow_html=True)
    
    # Menú lateral
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/0e4f3c/ffffff?text=SICIAP", width=200)
        st.markdown("---")
        
        # Menú de navegación (solo mostrar "Importar Excel" en local, no en la nube)
        menu_options = ["Dashboard", "Órdenes", "Ejecución", "Stock", "Pedidos"]
        menu_icons = ["speedometer2", "file-text", "check-circle", "box-seam", "cart"]
        
        # Solo agregar "Importar Excel" si estamos en local (no en Streamlit Cloud)
        if not is_cloud and local_connected:
            menu_options.insert(0, "Importar Excel")
            menu_icons.insert(0, "cloud-upload")
        
        selected = option_menu(
            menu_title="Navegación",
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast",
            default_index=0,
        )
        
        st.markdown("---")
        
        # Estado del sistema (local es lo importante; Supabase opcional)
        st.markdown("### 📊 Estado del Sistema")
        if local_connected:
            st.success("🟢 Local: Conectado")
        else:
            st.error("🔴 Local: No disponible")
        if supabase_connected:
            st.success("🟢 Supabase: disponible (opcional)")
        else:
            st.caption("Supabase: no conectado (opcional para sincronizar)")
        
        st.markdown("---")
        
        # Información
        st.markdown("### ℹ️ Información")
        if is_cloud:
            st.info("""
            **Modo Nube:** Esta aplicación lee datos desde Supabase. 
            Para cargar nuevos datos, usa la aplicación local.
            """)
        else:
            st.info("""
            **Trabajo en local:** Importá los Excel y mirá el dashboard. 
            No hace falta internet ni Supabase para el día a día.
            """)
    
    # Contenido principal según selección
    if selected == "Importar Excel":
        importar.show()
    elif selected == "Dashboard":
        dashboard.show()
    elif selected == "Órdenes":
        ordenes.show()
    elif selected == "Ejecución":
        ejecucion.show()
    elif selected == "Stock":
        stock.show()
    elif selected == "Pedidos":
        pedidos.show()


if __name__ == "__main__":
    main()
