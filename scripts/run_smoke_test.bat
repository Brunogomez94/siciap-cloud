@echo off
REM Script para ejecutar la prueba de humo
echo ========================================
echo   PRUEBA DE HUMO - SICIAP Cloud
echo ========================================
echo.

cd /d "%~dp0\.."
call venv\Scripts\activate.bat
python scripts\smoke_test.py

pause
