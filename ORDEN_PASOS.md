# Orden de pasos – SICIAP Cloud

Listado de anclaje para no saltar pasos. Cada fase depende de la anterior.

---

## Fase 1: Entorno
1. Python 3.9+ instalado  
2. PostgreSQL instalado y servicio activo  
3. Directorio del proyecto con el código  

## Fase 2: Entorno virtual y dependencias
4. Crear venv: `python -m venv venv`  
5. Activar venv: `venv\Scripts\activate` (Windows)  
6. Instalar: `pip install -r requirements.txt`  

## Fase 3: Base de datos local
7. Crear base: `CREATE DATABASE siciap_local;` (en psql)  
8. Aplicar esquema local:  
   `& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d siciap_local -f database/local/schema.sql`  
   (con `$env:PGPASSWORD` definido si hace falta)  

## Fase 4: Supabase
9. Proyecto y credenciales en Supabase  
10. Ejecutar en SQL Editor de Supabase el contenido de `database/supabase/schema.sql`  

## Fase 5: Variables de entorno
11. Archivo `.env` en la raíz con DB local y Supabase (usar pooler: `SUPABASE_DB_HOST=aws-1-us-east-1.pooler.supabase.com`, `SUPABASE_DB_USER=postgres.hbuencwjgfzypgmwinlp`)  

## Fase 6: Verificar conexiones
12. Ejecutar: `python scripts/verificar_conexiones.py`  
    - Local y Supabase deben dar OK (Supabase puede requerir WiFi del celular en redes restrictivas).  

---

## Fase 7: ETL – Cargar datos desde Excel (orden fijo)

Los procesadores deben ejecutarse en este orden:

| Orden | Procesador   | Tabla local      | Archivo sugerido en `data/` |
|------|--------------|-------------------|-----------------------------|
| 1    | Órdenes      | siciap.ordenes    | ordenes.xlsx               |
| 2    | Ejecución    | siciap.ejecucion  | ejecucion.xlsx             |
| 3    | Stock        | siciap.stock_critico | stock.xlsx             |
| 4    | Pedidos      | siciap.pedidos   | pedidos.xlsx               |

Comando único (lee archivos desde la carpeta `data/`):

```powershell
python scripts/cargar_datos_excel.py
```

O con carpeta personalizada:

```powershell
python scripts/cargar_datos_excel.py "C:\ruta\a\mis\excels"
```

Las tablas `datosejecucion`, `cantidad_solicitada`, `vencimientos_parques` se sincronizan a Supabase si existen en local; no tienen procesador Excel propio en este listado (se pueden cargar después por otro medio si aplica).  

---

## Fase 8: Sincronización Local → Supabase

13. Con conexión a Supabase disponible (por ejemplo WiFi del celular):  
    `python -m etl.sync.sync_manager`  
14. Opcional: revisar en Supabase (Table Editor) que las tablas tengan datos.  

---

## Fase 9: Aplicación Streamlit

15. Ejecutar: `streamlit run frontend/app.py`  
16. Abrir en el navegador la URL que indique (ej. http://localhost:8501).  
17. Comprobar: estado Supabase/Local, Dashboard y páginas (Órdenes, Ejecución, Stock, Pedidos).  

---

## Resumen del flujo de datos

1. **Excel** → (ETL con `cargar_datos_excel.py`) → **PostgreSQL local**  
2. **PostgreSQL local** → (sync con `etl.sync.sync_manager`) → **Supabase**  
3. **Streamlit** lee de **Supabase** si hay conexión; si no, de **PostgreSQL local**.  

Uso típico: subir el documento (Excel) cada tanto con el script ETL; cuando puedas, sincronizar a Supabase (WiFi celular); usar la app en cualquier lugar (Streamlit con datos en Supabase o local).
