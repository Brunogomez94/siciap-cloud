# 🚀 GUÍA DE DESPLIEGUE - SICIAP Cloud

## 📋 Pre-requisitos

1. ✅ Código completo y funcional (verificado con `smoke_test.py`)
2. ✅ Cuenta en [GitHub](https://github.com)
3. ✅ Cuenta en [Streamlit Cloud](https://streamlit.io/cloud) (gratis)

---

## Paso 1: Preparar el Repositorio Git

### 1.1 Inicializar Git (si no está inicializado)

```bash
cd "c:\Users\User\Desktop\BRUNO ESCRITORIO\PROYECTOS VARIOS\siciap-cloud"
git init
git add .
git commit -m "Initial commit: SICIAP Cloud - Sistema híbrido Local/Supabase"
```

### 1.2 Crear repositorio en GitHub

1. Ve a [github.com/new](https://github.com/new)
2. Nombre del repositorio: `siciap-cloud` (o el que prefieras)
3. **NO** marques "Initialize with README" (ya tienes archivos)
4. Clic en "Create repository"

### 1.3 Conectar repositorio local con GitHub

```bash
# Reemplaza USERNAME con tu usuario de GitHub
git remote add origin https://github.com/USERNAME/siciap-cloud.git
git branch -M main
git push -u origin main
```

---

## Paso 2: Configurar Variables de Entorno en Streamlit Cloud

### 2.1 Crear aplicación en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Clic en "New app"
3. Conecta tu repositorio de GitHub
4. Configura:
   - **Repository:** `USERNAME/siciap-cloud`
   - **Branch:** `main`
   - **Main file path:** `frontend/app.py`

### 2.2 Agregar Secrets (Variables de Entorno)

En Streamlit Cloud, ve a "Settings" → "Secrets" y agrega:

```toml
# .streamlit/secrets.toml (esto se crea automáticamente en Streamlit Cloud)

# PostgreSQL Local (si quieres que Streamlit también pueda escribir)
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "siciap_local"
DB_USER = "postgres"
DB_PASSWORD = "tu_password_local"

# Supabase (OBLIGATORIO para que funcione en la nube)
SUPABASE_URL = "https://hbuencwjgfzypgmwinlp.supabase.co"
SUPABASE_KEY = "tu_api_key_supabase"
SUPABASE_DB_HOST = "aws-1-us-east-1.pooler.supabase.com"
SUPABASE_DB_PORT = "5432"
SUPABASE_DB_NAME = "postgres"
SUPABASE_DB_USER = "postgres.hbuencwjgfzypgmwinlp"
SUPABASE_DB_PASSWORD = "Dggies12345db"
```

**⚠️ IMPORTANTE:** 
- Streamlit Cloud **NO puede** conectarse a tu PostgreSQL local (localhost no funciona desde la nube)
- Por eso el frontend **debe** leer de Supabase
- El ETL y sync se ejecutan **solo en tu PC local**

---

## Paso 3: Verificar Despliegue

### 3.1 Verificar que la app se despliega

1. Streamlit Cloud mostrará un link público: `https://USERNAME-siciap-cloud-app-XXXXX.streamlit.app`
2. Abre el link y verifica que carga sin errores
3. Debería mostrar "Supabase: disponible" o "Modo Local" según la conexión

### 3.2 Probar funcionalidad

1. Ve a "Dashboard" → Debe mostrar datos si Supabase tiene datos
2. Ve a "Órdenes" → Debe mostrar tabla de órdenes
3. **NOTA:** La página "Importar Excel" NO funcionará en Streamlit Cloud porque necesita acceso a PostgreSQL local

---

## Paso 4: Flujo de Trabajo Post-Despliegue

### Flujo Normal (Día a Día):

```
1. En tu PC local:
   └─> Abres Streamlit local (run_frontend.bat)
   └─> Importas Excel desde "Importar Excel"
   └─> Los datos se guardan en PostgreSQL local

2. Cuando quieras compartir:
   └─> Ejecutas: python etl/sync/sync_manager.py
   └─> Los datos se sincronizan a Supabase

3. Usuarios finales:
   └─> Abren el link público de Streamlit Cloud
   └─> Ven los datos desde Supabase
   └─> Pueden ver Dashboard, Órdenes, Ejecución, etc.
```

---

## 🔧 Troubleshooting

### Error: "No module named 'X'"
- Verifica que todas las dependencias estén en `requirements.txt`
- Streamlit Cloud instala automáticamente desde `requirements.txt`

### Error: "Supabase no disponible"
- Verifica que las variables de entorno estén correctas en Streamlit Cloud Secrets
- Verifica que el Session Pooler esté configurado (`aws-1-us-east-1.pooler.supabase.com`)

### Error: "Table does not exist"
- Ejecuta el schema SQL en Supabase desde `database/supabase/schema.sql`
- Verifica que las tablas existan en Supabase

### La app carga pero no muestra datos
- Verifica que hayas ejecutado el sync desde tu PC local
- Verifica que Supabase tenga datos: ve a Supabase Dashboard → Table Editor

---

## ✅ Checklist Final

- [ ] Código subido a GitHub
- [ ] App creada en Streamlit Cloud
- [ ] Variables de entorno configuradas en Streamlit Cloud Secrets
- [ ] Schema SQL ejecutado en Supabase
- [ ] Prueba de humo ejecutada (`python scripts/smoke_test.py`)
- [ ] Sync ejecutado desde PC local (`python etl/sync/sync_manager.py`)
- [ ] App pública accesible y mostrando datos

---

## 🎉 ¡Listo!

Una vez completado, tendrás:
- ✅ Sistema local funcional (ETL + PostgreSQL)
- ✅ Sistema en la nube (Streamlit Cloud + Supabase)
- ✅ Sincronización automática cuando ejecutes el sync

**Link público:** `https://USERNAME-siciap-cloud-app-XXXXX.streamlit.app`
