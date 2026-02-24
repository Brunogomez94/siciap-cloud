# Auditoría de Arquitectura y Código — SICIAP Cloud

**Fecha:** 18/02/2025  
**Contexto:** Migración de conexión directa (SQLAlchemy/psycopg2, puerto 5432) a **solo API REST de Supabase** (supabase-py, HTTPS 443).  
**Alcance:** Proyecto completo, con foco en `frontend/`, `utils/`, `config/`, `etl/` y raíz.

---

## 1. Limpieza de Dependencias y Código Legado

### 1.1 Rojo (Crítico)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 1 | **Páginas que usan `get_supabase_connection()` como si fuera una conexión SQL.** En `frontend/utils/db_connection.py`, `get_supabase_connection` es un **alias de `get_supabase_client()`** y devuelve el **cliente Supabase (API REST)**. Varias páginas hacen `conn = get_supabase_connection()` y luego usan `pd.read_sql(query, conn)`, `conn.commit()`, `conn.rollback()`, `conn.close()`. El cliente de Supabase **no** expone esos métodos. | `frontend/pages/ejecucion.py`, `pedidos.py`, `ordenes.py`, `stock.py`, `dashboard_principal.py`, `dashboard_editable.py` |
| 2 | **Uso explícito de SQLAlchemy (`text`, `read_sql`) en el frontend.** Debe eliminarse y reemplazarse por llamadas a la API: `.table("nombre").select(...)` y `.upsert(...)`. | Mismos archivos que arriba |
| 3 | **`SyncManager` (etl/sync/sync_manager.py) usa solo SQLAlchemy.** Crea `create_engine()` para Supabase con cadena de conexión PostgreSQL (puerto 5432). En entorno solo HTTPS (Streamlit Cloud / firewall), la sincronización **no funcionará** desde la nube. | `etl/sync/sync_manager.py` |
| 4 | **ETL processors usan SQLAlchemy y conexión por puerto.** Cada processor usa `base_processor` o conexión con `create_engine`, `text`, `conn.execute()`, `conn.begin()`, `DELETE FROM siciap.xxx`. Todo pensado para PostgreSQL directo, no para API REST. | `etl/processors/base_processor.py`, `ordenes.py`, `ejecucion.py`, `stock.py`, `pedidos.py`, `vencimientos_parques.py` |

### 1.2 Amarillo (Advertencia)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 5 | **Scripts de mantenimiento siguen con psycopg2 / SQLAlchemy.** Para uso local o one-off. Si el objetivo es "cero 5432", habría que reemplazarlos por API o dejarlos documentados como "solo ejecución local con .env". | `scripts/eliminar_unique_ejecucion.py`, `scripts/ejecutar_correccion_item.py`, `scripts/verificar_conexiones.py`, `scripts/smoke_test.py` |
| 6 | **`requirements.txt` incluye `sqlalchemy` y `psycopg2-binary`.** Necesarios para ETL local e importación desde Excel. Decisión de producto. | `requirements.txt` |
| 7 | **Dos "fuentes de verdad" para Supabase.** Frontend usa `st.secrets`; Importar/Sync usa `config.supabase.SupabaseConfig` que lee solo `os.getenv()`. En Streamlit Cloud no hay `.env`; solo Secrets. | `config/supabase.py` vs `frontend/utils/db_connection.py` |

### 1.3 Verde (Correcto)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 8 | **Un único módulo del frontend usa bien la API REST.** Solo `frontend/pages/dashboard.py` usa `get_supabase_client()`, `supabase.table(...).select("*")` y `supabase.table("cantidad_solicitada").upsert(...)`. | `frontend/pages/dashboard.py` |
| 9 | **Alias sin conflicto de nombres.** `get_supabase_connection = get_supabase_client` está definido y exportado. El problema no es el nombre sino el **uso** de ese valor como "conexión SQL" en otras páginas. | `frontend/utils/db_connection.py`, `frontend/utils/__init__.py` |

---

## 2. Arquitectura de Conexión (API REST)

### 2.1 Rojo (Crítico)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 10 | **Páginas de dashboard/pestañas no usan cliente Supabase para lectura.** Deberían usar `client = get_supabase_client()` y luego `client.table("ejecucion").select("*").execute()`. Hoy usan `get_supabase_connection()` y SQL con `text()`, incompatible con el cliente. | `ejecucion.py`, `pedidos.py`, `ordenes.py`, `stock.py`, `dashboard_principal.py`, `dashboard_editable.py` |
| 11 | **Escritura en dashboard_editable con SQL crudo.** Usa `conn.execute(upsert, {...})`, `conn.commit()`, `conn.rollback()`. Debe pasarse a API: `supabase.table("cantidad_solicitada").upsert(...)` sin `commit`/`rollback`. | `frontend/pages/dashboard_editable.py` |

### 2.2 Amarillo (Advertencia)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 12 | **SyncManager asume siempre PostgreSQL directo.** Para que "sincronizar con Supabase" funcione en entorno solo-API, habría que reescribir el sync para usar el cliente Supabase. Mientras tanto, dejarlo como "solo local". | `etl/sync/sync_manager.py` |

### 2.3 Verde (Correcto)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 13 | **Cliente Supabase inicializado desde `st.secrets`.** `get_supabase_client()` lee `st.secrets["SUPABASE_URL"]` y `st.secrets["SUPABASE_KEY"]`. | `frontend/utils/db_connection.py` |
| 14 | **Lectura y escritura vía API en el único dashboard migrado.** En `dashboard.py`, lectura con `.select("*").limit(...)` y escritura con `.upsert(registros_a_guardar)`. | `frontend/pages/dashboard.py` |

---

## 3. Lógica de Negocio y UI (Streamlit)

### 3.1 Rojo (Crítico)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 15 | **Dashboard principal (gerencial) nunca limpia caché.** Tiene `@st.cache_data(ttl=300)` en `load_vista_tablero()` pero no hay botón "Refrescar" ni llamada a `st.cache_data.clear()`. | `frontend/pages/dashboard_principal.py` |

### 3.2 Amarillo (Advertencia)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 16 | **dashboard_editable depende de "conn" para cargar datos.** Mientras no se migre a API, la lógica está atada a un `conn` que ya no es válido como conexión SQL. Al migrar, revisar que los `st.cache_data.clear()` sigan en los mismos puntos. | `frontend/pages/dashboard_editable.py` |

### 3.3 Verde (Correcto)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 17 | **Uso de `st.cache_data` y limpieza en el resto.** En dashboard, ejecucion, pedidos, ordenes, stock, dashboard_editable e importar se llama `st.cache_data.clear()` en "Refrescar" o tras guardar/cargar. | Varios `frontend/pages/*.py` |
| 18 | **AgGrid: columnas editables acotadas.** En dashboard solo `cantidad_solicitada` y `ver_en_fecha` editables; en dashboard_editable solo "CANTIDAD SOLICITADA" y "VER EN FECHA". Configuración segura. | `dashboard.py`, `dashboard_editable.py` |
| 19 | **Coherencia de flujo de inventario/parques.** Vista tablero, nivel_stock, distribución, parque_regentes, estado_parque, etc. aparecen en el diseño; lógica consistente entre dashboard y dashboard_editable. | Diseño general |

---

## 4. Seguridad y Estructura de Archivos

### 4.1 Rojo (Crítico)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 20 | **Ninguno.** No se encontraron credenciales, contraseñas ni URLs de base de datos hardcodeadas en `.py`. | — |

### 4.2 Amarillo (Advertencia)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 21 | **Configuración Supabase/DB dual.** En Cloud solo existen Secrets; `SupabaseConfig` y `DatabaseConfig` leen de `.env`. Conviene documentar: "En local: .env; en Streamlit Cloud: Secrets". | `config/supabase.py`, `config/database.py`, `frontend/pages/importar.py` |
| 22 | **`.streamlit/secrets.toml` en .gitignore.** Correcto que no se suba. Asegurarse de que `STREAMLIT_CLOUD_SECRETS.toml` (plantilla) no contenga valores reales si se sube al repo. | `.gitignore` |

### 4.3 Verde (Correcto)

| # | Hallazgo | Ubicación |
| --- | --- | --- |
| 23 | **Credenciales solo desde configuración.** Frontend usa `st.secrets`; config y scripts usan `os.getenv` / `.env`. No hay URLs ni passwords en claro. | Todo el proyecto |
| 24 | **Estructura de carpetas escalable.** `config/`, `frontend/` (app, pages, utils), `etl/` (processors, sync, utils), `database/` (local, supabase), `scripts/`. Adecuada para proyecto institucional. | Raíz del proyecto |

---

## Resumen por color

| Color | Cantidad | Significado |
| --- | --- | --- |
| Rojo | 6 | Crítico: fallos de concepto o código que no puede funcionar con "solo API REST". |
| Amarillo | 6 | Advertencia: deuda técnica, scripts legados o configuración dual. |
| Verde | 9 | Correcto: lo que ya está alineado con API REST, caché y seguridad. |

---

## Plan de acción (paso a paso)

**No se ha modificado código.** Orden sugerido para limpiar y alinear todo con "solo API REST" en el frontend:

1. **Migrar páginas de solo lectura a API REST**
   - Reemplazar en `ejecucion.py`, `pedidos.py`, `ordenes.py`, `stock.py`: quitar `from sqlalchemy import text` y uso de `conn`. Usar `get_supabase_client()` y `client.table("nombre_tabla").select("*").limit(...).execute()`. Construir `pd.DataFrame(response.data)` desde `response.data`. Eliminar llamadas a `conn.rollback()`, `conn.close()`, `pd.read_sql(..., conn)`.

2. **Migrar dashboard_principal.py**
   - Cargar la vista con `supabase.table("vista_tablero_principal").select("*").order(...).limit(...).execute()`. Añadir un botón "Refrescar" que llame a `st.cache_data.clear()` y `st.rerun()`.

3. **Migrar dashboard_editable.py**
   - Carga de datos: mismo patrón que dashboard_principal (API). Guardado: reemplazar `conn.execute(upsert, ...)`, `commit`/`rollback` por `supabase.table("cantidad_solicitada").upsert(...)`. Mantener los `st.cache_data.clear()` en los mismos puntos.

4. **Unificar fuente de configuración (opcional)**
   - Crear helper que devuelva URL y KEY: en contexto Streamlit `st.secrets.get("SUPABASE_URL")`; si no hay Streamlit, `os.getenv("SUPABASE_URL")`. Usar ese helper en `db_connection.get_supabase_client()`.

5. **ETL y Sync (decisiones de producto)**
   - **Opción A (recomendada):** Dejar ETL y SyncManager como están; solo para uso **local**. Documentar en README y DESPLIEGUE_WEB.md que en Cloud no hay importación ni sync.
   - **Opción B:** Reescribir SyncManager para que escriba en Supabase vía API.

6. **Scripts de mantenimiento**
   - Dejar scripts como "solo ejecución local con .env y conexión directa". Añadir al inicio de cada script un comentario: "Solo para entorno local con PostgreSQL/Supabase por puerto 5432".

7. **Requirements**
   - Mantener `sqlalchemy` y `psycopg2-binary` mientras existan ETL local y scripts. Si en el futuro el frontend en Cloud no usa nada de eso, valorar un `requirements-cloud.txt` mínimo.

8. **Revisión final**
   - Buscar de nuevo en el repo: `sqlalchemy`, `psycopg2`, `create_engine`, `text(`, `read_sql`, `conn.commit`, `conn.rollback`. Comprobar que en `frontend/pages/` no quede ningún uso de `conn` como conexión SQL; solo cliente Supabase.

Con esto se deja una base firme: frontend 100 % API REST, sin código "sucio" de la versión anterior en las páginas, y con un plan claro para ETL/sync y scripts.
