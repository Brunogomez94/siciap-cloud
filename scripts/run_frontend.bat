@echo off
cd /d "%~dp0.."
call venv\Scripts\activate.bat
echo Abriendo Streamlit (los errores de carga se ven en esta ventana)...
streamlit run frontend/app.py
pause
