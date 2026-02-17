# ✅ Checklist de Instalación - SICIAP Cloud

## 📋 Proceso Paso a Paso Estricto

**INSTRUCCIONES**: Marca cada paso cuando lo completes. No pases al siguiente hasta que el paso actual esté 100% completo y verificado.

**Orden resumido (ETL y flujo):** Ver también **`ORDEN_PASOS.md`** — ahí está el listado de anclaje con el orden exacto de los procesadores ETL (Órdenes → Ejecución → Stock → Pedidos) y los comandos.

---

## FASE 1: PREPARACIÓN DEL ENTORNO

### ✅ Paso 1.1: Verificar Python instalado
- [ ] Verificar versión de Python (debe ser 3.9 o superior)
- [ ] Comando: `python --version` o `python3 --version`
- [ ] **Resultado esperado**: Python 3.9.x o superior
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 1.2: Verificar PostgreSQL instalado
- [ ] Verificar que PostgreSQL esté instalado
- [ ] Comando: `psql --version`
- [ ] Verificar que el servicio esté corriendo
- [ ] **Resultado esperado**: Versión de PostgreSQL y servicio activo
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 1.3: Crear directorio del proyecto
- [ ] Navegar a la carpeta del proyecto
- [ ] Verificar que todos los archivos estén presentes
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 2: CONFIGURACIÓN DEL ENTORNO VIRTUAL

### ✅ Paso 2.1: Crear entorno virtual
- [ ] Ejecutar: `python -m venv venv`
- [ ] Verificar que se creó la carpeta `venv/`
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 2.2: Activar entorno virtual
- [ ] Windows: `venv\Scripts\activate`
- [ ] Linux/Mac: `source venv/bin/activate`
- [ ] Verificar que aparece `(venv)` en el prompt
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 2.3: Actualizar pip
- [ ] Ejecutar: `python -m pip install --upgrade pip`
- [ ] Verificar versión actualizada
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 3: INSTALACIÓN DE DEPENDENCIAS

### ✅ Paso 3.1: Instalar dependencias base
- [ ] Ejecutar: `pip install -r requirements.txt`
- [ ] Verificar que no haya errores
- [ ] Verificar instalación de Streamlit: `streamlit --version`
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 3.2: Verificar instalaciones críticas
- [ ] Verificar pandas: `python -c "import pandas; print(pandas.__version__)"`
- [ ] Verificar sqlalchemy: `python -c "import sqlalchemy; print(sqlalchemy.__version__)"`
- [ ] Verificar psycopg2: `python -c "import psycopg2; print('OK')"`
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 4: CONFIGURACIÓN DE BASE DE DATOS LOCAL

### ✅ Paso 4.1: Crear base de datos PostgreSQL
- [ ] Conectarse a PostgreSQL: `psql -U postgres`
- [ ] Crear base de datos: `CREATE DATABASE siciap_local;`
- [ ] Verificar creación: `\l` (debe aparecer siciap_local)
- [ ] Salir: `\q`
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 4.2: Ejecutar esquema inicial
- [ ] Ejecutar: `psql -U postgres -d siciap_local -f database/local/schema.sql`
- [ ] Verificar que no haya errores
- [ ] Verificar tablas creadas: `psql -U postgres -d siciap_local -c "\dt siciap.*"`
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 4.3: Verificar estructura de tablas
- [ ] Conectarse: `psql -U postgres -d siciap_local`
- [ ] Verificar esquema: `\dn`
- [ ] Verificar tablas: `\dt siciap.*`
- [ ] Verificar estructura de una tabla: `\d siciap.ordenes`
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 5: CONFIGURACIÓN DE SUPABASE

### ✅ Paso 5.1: Crear cuenta y proyecto en Supabase
- [ ] Ir a https://supabase.com
- [ ] Crear cuenta (si no tienes)
- [ ] Crear nuevo proyecto
- [ ] Anotar nombre del proyecto
- [ ] Esperar a que termine la configuración (2-3 minutos)
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 5.2: Obtener credenciales de Supabase
- [ ] Ir a Settings → Database
- [ ] Copiar Host (ej: db.xxxxx.supabase.co)
- [ ] Copiar Database name (postgres)
- [ ] Copiar Port (5432)
- [ ] Copiar User (postgres)
- [ ] Copiar Password (la que configuraste)
- [ ] Ir a Settings → API
- [ ] Copiar URL del proyecto
- [ ] Copiar anon/public key
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 5.3: Ejecutar esquema en Supabase
- [ ] En Supabase, ir a SQL Editor
- [ ] Abrir archivo: `database/supabase/schema.sql`
- [ ] Copiar todo el contenido
- [ ] Pegar en SQL Editor de Supabase
- [ ] Ejecutar (Run)
- [ ] Verificar que no haya errores
- [ ] Verificar tablas creadas en Table Editor
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 6: CONFIGURACIÓN DE VARIABLES DE ENTORNO

### ✅ Paso 6.1: Crear archivo .env
- [ ] Copiar archivo ejemplo: `cp .env.example .env` o crear manualmente
- [ ] Verificar que existe `.env` en la raíz del proyecto
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 6.2: Configurar variables de PostgreSQL local
- [ ] Abrir `.env` en editor
- [ ] Configurar DB_HOST=localhost
- [ ] Configurar DB_PORT=5432
- [ ] Configurar DB_NAME=siciap_local
- [ ] Configurar DB_USER=postgres
- [ ] Configurar DB_PASSWORD=(tu password de PostgreSQL local)
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 6.3: Configurar variables de Supabase
- [ ] En `.env`, configurar SUPABASE_URL=(URL de tu proyecto)
- [ ] Configurar SUPABASE_KEY=(anon/public key)
- [ ] Configurar SUPABASE_DB_HOST=(Host de Database)
- [ ] Configurar SUPABASE_DB_PORT=5432
- [ ] Configurar SUPABASE_DB_NAME=postgres
- [ ] Configurar SUPABASE_DB_USER=postgres
- [ ] Configurar SUPABASE_DB_PASSWORD=(Password de Supabase)
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 6.4: Verificar archivo .env
- [ ] Verificar que todas las variables estén configuradas
- [ ] Verificar que no haya espacios extra
- [ ] Verificar que las contraseñas estén correctas
- [ ] **NO COMMITEAR .env** (debe estar en .gitignore)
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 7: VERIFICACIÓN DE CONEXIONES

### ✅ Paso 7.1: Verificar conexión PostgreSQL local
- [ ] Ejecutar script de prueba (se creará)
- [ ] O probar manualmente: `psql -U postgres -d siciap_local -c "SELECT 1;"`
- [ ] Verificar que funciona
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 7.2: Verificar conexión Supabase
- [ ] Ejecutar script de prueba (se creará)
- [ ] O probar desde Supabase Dashboard → Database → Connection string
- [ ] Verificar que funciona
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 8: PRUEBA DE SINCRONIZACIÓN

### ✅ Paso 8.1: Crear datos de prueba (opcional)
- [ ] Insertar algunos datos de prueba en PostgreSQL local
- [ ] O usar datos existentes si los tienes
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 8.2: Ejecutar sincronización
- [ ] Ejecutar: `python -m etl.sync.sync_manager`
- [ ] Verificar que no haya errores
- [ ] Verificar logs en `logs/sync.log`
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 8.3: Verificar datos en Supabase
- [ ] Ir a Supabase Dashboard → Table Editor
- [ ] Verificar que las tablas tengan datos
- [ ] Comparar conteos con PostgreSQL local
- [ ] **Estado**: ⏳ PENDIENTE

---

## FASE 9: EJECUTAR APLICACIÓN

### ✅ Paso 9.1: Verificar estructura del proyecto
- [ ] Verificar que `frontend/app.py` existe
- [ ] Verificar que todas las páginas existen en `frontend/pages/`
- [ ] Verificar que `config/` tiene todos los archivos
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 9.2: Ejecutar Streamlit
- [ ] Asegurarse de estar en el directorio raíz
- [ ] Asegurarse de que el entorno virtual esté activado
- [ ] Ejecutar: `streamlit run frontend/app.py`
- [ ] Verificar que se abre en http://localhost:8501
- [ ] **Estado**: ⏳ PENDIENTE

### ✅ Paso 9.3: Verificar aplicación funcionando
- [ ] Verificar que la página carga sin errores
- [ ] Verificar que muestra "Supabase Conectado" o "Modo Local"
- [ ] Navegar por las diferentes páginas
- [ ] Verificar que los datos se cargan correctamente
- [ ] **Estado**: ⏳ PENDIENTE

---

## ✅ COMPLETADO

- [ ] Todos los pasos anteriores completados
- [ ] Aplicación funcionando correctamente
- [ ] Datos sincronizados entre local y Supabase
- [ ] Sin errores en logs

---

## 📝 NOTAS IMPORTANTES

1. **NO saltes pasos**: Cada paso depende del anterior
2. **Verifica cada paso**: Asegúrate de que funciona antes de continuar
3. **Guarda tus credenciales**: En un lugar seguro (no en el código)
4. **Revisa los logs**: Si algo falla, revisa `logs/` para más información

---

**Última actualización**: Al completar cada paso, marca la casilla y actualiza el estado.
