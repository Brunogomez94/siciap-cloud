# 🚀 Guía de Inicio Rápido - SICIAP Cloud

Esta guía te ayudará a configurar y ejecutar el proyecto desde cero.

## 📋 Prerrequisitos

1. **Python 3.9+** instalado
2. **PostgreSQL** instalado y corriendo localmente
3. **Cuenta de Supabase** (gratuita en https://supabase.com)
4. **Git** (opcional, para clonar el proyecto)

## 🔧 Paso 1: Configuración del Entorno

### 1.1 Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 1.2 Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🗄️ Paso 2: Configurar Base de Datos Local

### 2.1 Crear base de datos PostgreSQL

```bash
# Conectarse a PostgreSQL
psql -U postgres

# Crear base de datos
CREATE DATABASE siciap_local;

# Salir
\q
```

### 2.2 Ejecutar esquema inicial

```bash
psql -U postgres -d siciap_local -f database/local/schema.sql
```

## ☁️ Paso 3: Configurar Supabase

### 3.1 Crear proyecto en Supabase

1. Ve a https://supabase.com y crea una cuenta (gratuita)
2. Crea un nuevo proyecto
3. Espera a que se complete la configuración (2-3 minutos)

### 3.2 Ejecutar esquema en Supabase

1. En el panel de Supabase, ve a **SQL Editor**
2. Copia el contenido de `database/supabase/schema.sql`
3. Pégalo y ejecuta el script

### 3.3 Obtener credenciales

1. Ve a **Settings** → **Database**
2. Copia los siguientes valores:
   - **Host**: `db.xxxxx.supabase.co`
   - **Database name**: `postgres`
   - **Port**: `5432`
   - **User**: `postgres`
   - **Password**: (la contraseña que configuraste)

3. Ve a **Settings** → **API**
   - Copia la **URL** del proyecto
   - Copia la **anon/public key**

## ⚙️ Paso 4: Configurar Variables de Entorno

### 4.1 Crear archivo .env

```bash
# Copiar el ejemplo
cp .env.example .env
```

### 4.2 Editar .env con tus credenciales

```env
# Base de datos local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=siciap_local
DB_USER=postgres
DB_PASSWORD=tu_password_postgres_local

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_api_key_supabase
SUPABASE_DB_HOST=db.tu-proyecto.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=tu_password_supabase
```

## 🔄 Paso 5: Sincronizar Datos (Opcional)

Si ya tienes datos en tu base de datos local, puedes sincronizarlos a Supabase:

```bash
# Sincronizar todas las tablas
python -m etl.sync.sync_manager

# O sincronizar una tabla específica
python -m etl.sync.sync_manager ordenes
```

## 🚀 Paso 6: Ejecutar la Aplicación

```bash
streamlit run frontend/app.py
```

La aplicación se abrirá en `http://localhost:8501`

## 📝 Estructura del Proyecto

```
siciap-cloud/
├── config/              # Configuración centralizada
├── database/            # Scripts SQL
│   ├── local/          # PostgreSQL local
│   └── supabase/       # Supabase
├── etl/                # Procesamiento ETL
│   ├── processors/    # Procesadores modulares
│   ├── sync/           # Sincronización
│   └── utils/          # Utilidades
├── frontend/           # Aplicación Streamlit
│   ├── pages/         # Páginas modulares
│   └── utils/         # Utilidades frontend
└── requirements.txt    # Dependencias
```

## 🐛 Solución de Problemas

### Error: "No module named 'config'"

Asegúrate de estar en el directorio raíz del proyecto y que Python puede encontrar los módulos:

```bash
# Desde el directorio raíz
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# O en Windows PowerShell
$env:PYTHONPATH = "$(Get-Location);$env:PYTHONPATH"
```

### Error de conexión a PostgreSQL

1. Verifica que PostgreSQL esté corriendo
2. Verifica las credenciales en `.env`
3. Prueba la conexión manualmente:
   ```bash
   psql -U postgres -h localhost -d siciap_local
   ```

### Error de conexión a Supabase

1. Verifica que las credenciales en `.env` sean correctas
2. Verifica que el proyecto de Supabase esté activo
3. Verifica que el esquema se haya ejecutado correctamente

### La aplicación no muestra datos

1. Ejecuta la sincronización primero:
   ```bash
   python -m etl.sync.sync_manager
   ```
2. Verifica que haya datos en la base de datos local
3. Revisa los logs en `logs/sync.log`

## 📚 Próximos Pasos

1. **Importar datos**: Usa los procesadores ETL para importar archivos Excel
2. **Personalizar**: Modifica las páginas en `frontend/pages/` según tus necesidades
3. **Agregar funcionalidades**: Extiende los procesadores en `etl/processors/`
4. **Desplegar**: Considera usar Render, Railway o Streamlit Cloud para el frontend

## 💡 Tips

- Los datos se procesan localmente y se sincronizan a Supabase
- El frontend lee principalmente de Supabase para mejor rendimiento
- Usa `st.cache_data` en Streamlit para mejorar el rendimiento
- Los logs se guardan en `logs/` para debugging

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs en `logs/`
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que las variables de entorno estén configuradas correctamente
