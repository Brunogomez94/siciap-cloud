@echo off
REM Script de inicio rápido para Windows
echo ========================================
echo   SICIAP Cloud - Inicio Rapido
echo ========================================
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    echo Activando entorno virtual...
    call venv\Scripts\activate.bat
)

REM Verificar que Streamlit esté instalado
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Streamlit no encontrado. Instalando dependencias...
    pip install -r requirements.txt
)

REM Iniciar aplicación
echo.
echo Iniciando aplicacion Streamlit...
echo La aplicacion se abrira en http://localhost:8501
echo.
streamlit run frontend/app.py

pause
