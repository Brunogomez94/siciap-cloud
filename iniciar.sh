#!/bin/bash
# Script de inicio rápido para Linux/Mac

echo "========================================"
echo "  SICIAP Cloud - Inicio Rapido"
echo "========================================"
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar que Streamlit esté instalado
if ! python -c "import streamlit" 2>/dev/null; then
    echo "Streamlit no encontrado. Instalando dependencias..."
    pip install -r requirements.txt
fi

# Iniciar aplicación
echo ""
echo "Iniciando aplicación Streamlit..."
echo "La aplicación se abrirá en http://localhost:8501"
echo ""
streamlit run frontend/app.py
