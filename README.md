# 🏥 SICIAP Cloud - Sistema Integrado de Gestión

Sistema híbrido para gestión de datos logísticos con arquitectura Local/Supabase.

## 🏗️ Arquitectura

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────┐
│   Excel/CSV     │  ────>  │  PostgreSQL  │  ────>  │  Supabase   │
│   (Archivos)    │  ETL    │   (Local)     │  Sync   │   (Nube)    │
└─────────────────┘         └──────────────┘         └─────────────┘
                                      │                      │
                                      │                      │
                                      v                      v
                              ┌──────────────┐      ┌──────────────┐
                              │  Streamlit   │      │  Streamlit   │
                              │   (Local)    │      │   (Cloud)    │
                              └──────────────┘      └──────────────┘
```

## 📋 Características

- ✅ **ETL Robusto:** Procesa Excel/CSV complejos con mapeo automático de columnas
- ✅ **Almacenamiento Local:** PostgreSQL local para trabajo diario sin internet
- ✅ **Sincronización Opcional:** Sync a Supabase cuando tengas conexión
- ✅ **Dashboard Interactivo:** Visualizaciones con Plotly y filtros avanzados
- ✅ **Arquitectura Híbrida:** Funciona offline y online

## 🚀 Inicio Rápido

### 1. Instalación

```bash
# Clonar repositorio
git clone https://github.com/USERNAME/siciap-cloud.git
cd siciap-cloud

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración

Copia `.env.example` a `.env` y configura:

```env
# PostgreSQL Local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siciap_local
DB_USER=postgres
DB_PASSWORD=tu_password

# Supabase (Opcional)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_api_key
SUPABASE_DB_HOST=aws-1-us-east-1.pooler.supabase.com
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.tu_proyecto
SUPABASE_DB_PASSWORD=tu_password
```

### 3. Crear Base de Datos

```bash
# Aplicar schema local
psql -U postgres -d siciap_local -f database\local\schema.sql

# Aplicar schema Supabase (desde Supabase SQL Editor)
# Copia y pega el contenido de database\supabase\schema.sql
```

### 4. Ejecutar Aplicación

```bash
# Opción 1: Script batch (Windows)
scripts\run_frontend.bat

# Opción 2: PowerShell
scripts\run_frontend.ps1

# Opción 3: Manual
streamlit run frontend/app.py
```

## 📊 Uso

### Importar Datos

1. Abre la aplicación Streamlit
2. Ve a "Importar Excel"
3. Sube los 5 archivos:
   - `ordenes.xlsx`
   - `ejecucion.xlsx`
   - `stock_critico.xlsx`
   - `pedidos.xlsx`
   - `vencimientos_parques.csv` (o Excel)

### Sincronizar a Supabase

```bash
# Desde terminal
python etl/sync/sync_manager.py

# O sincronizar tabla específica
python etl/sync/sync_manager.py ordenes
```

### Prueba de Humo

```bash
# Verificar que todo funciona
python scripts/smoke_test.py

# O usar el script
scripts\run_smoke_test.bat
```

## 🧪 Prueba de Humo

El script `smoke_test.py` verifica:

1. ✅ Conexión a PostgreSQL local
2. ✅ Conexión a Supabase (si está configurado)
3. ✅ Datos en PostgreSQL local
4. ✅ Sincronización Local → Supabase
5. ✅ Datos en Supabase

Ejecuta antes de desplegar para asegurar que todo funciona.

## 🚀 Despliegue

Ver `DEPLOY.md` para instrucciones completas de despliegue a Streamlit Cloud.

**Resumen:**
1. Sube código a GitHub
2. Crea app en Streamlit Cloud
3. Configura variables de entorno en Streamlit Cloud Secrets
4. ¡Listo! Tu app estará pública

## 📁 Estructura del Proyecto

```
siciap-cloud/
├── config/              # Configuración (database, supabase)
├── etl/
│   ├── processors/      # Procesadores ETL (ordenes, ejecucion, etc.)
│   ├── sync/           # Sincronización Local → Supabase
│   └── utils/          # Utilidades (excel_reader, validators)
├── frontend/
│   ├── pages/          # Páginas Streamlit (dashboard, ordenes, etc.)
│   └── utils/          # Utilidades frontend (db_connection)
├── database/
│   ├── local/          # Schema PostgreSQL local
│   └── supabase/       # Schema Supabase
├── scripts/            # Scripts auxiliares
└── requirements.txt    # Dependencias Python
```

## 🔧 Troubleshooting

### Error: "No module named X"
```bash
pip install -r requirements.txt
```

### Error: "Table does not exist"
Aplica el schema SQL correspondiente (local o Supabase).

### Error: "Supabase no disponible"
- Verifica `.env` con credenciales correctas
- Usa Session Pooler si estás en red restrictiva
- El sistema funciona en modo local sin Supabase

## 📝 Documentación Adicional

- `AUDITORIA_TECNICA.md` - Análisis técnico completo del proyecto
- `DEPLOY.md` - Guía de despliegue a Streamlit Cloud
- `ORDEN_PASOS.md` - Orden de pasos para setup inicial
- `CHECKLIST_INSTALACION.md` - Checklist de instalación

## 📄 Licencia

Este proyecto es de uso interno.

## 👥 Autor

Desarrollado para gestión logística del MSPBS.

---

**Estado:** ✅ Listo para Producción (95% completo)
