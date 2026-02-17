# Script para inicializar Git y preparar para GitHub
# Ejecutar: .\scripts\init_git.ps1

Write-Host "🚀 Inicializando repositorio Git..." -ForegroundColor Green

# Cambiar al directorio del proyecto
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Verificar si ya existe .git
if (Test-Path ".git") {
    Write-Host "⚠️  Ya existe un repositorio Git. Continuando..." -ForegroundColor Yellow
} else {
    Write-Host "📦 Inicializando repositorio Git..." -ForegroundColor Cyan
    git init
}

# Agregar todos los archivos
Write-Host "📝 Agregando archivos..." -ForegroundColor Cyan
git add .

# Verificar si hay cambios para commit
$status = git status --porcelain
if ($status) {
    Write-Host "💾 Creando commit inicial..." -ForegroundColor Cyan
    git commit -m "Initial commit: SICIAP Cloud - Sistema híbrido Local/Supabase"
    Write-Host "✅ Commit creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No hay cambios para commitear" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "1. Crea un repositorio en GitHub (github.com/new)" -ForegroundColor White
Write-Host "2. Ejecuta estos comandos (reemplaza USERNAME con tu usuario):" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/USERNAME/siciap-cloud.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Luego sigue las instrucciones en DEPLOY.md" -ForegroundColor White
