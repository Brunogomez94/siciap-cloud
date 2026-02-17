# Script para ejecutar la prueba de humo
Write-Host "🧪 Ejecutando Prueba de Humo..." -ForegroundColor Green
Write-Host ""

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Activar venv si existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Ejecutar smoke test
python scripts\smoke_test.py

Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
