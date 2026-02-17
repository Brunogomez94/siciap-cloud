# Abre el frontend en esta ventana; los errores de carga se ven en la consola
Set-Location $PSScriptRoot\..
& .\venv\Scripts\Activate.ps1
Write-Host "Abriendo Streamlit (errores de carga visibles aqui)..." -ForegroundColor Cyan
streamlit run frontend/app.py
