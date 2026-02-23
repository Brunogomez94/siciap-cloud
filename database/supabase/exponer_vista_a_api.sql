-- =============================================================================
-- EXPONER vista_tablero_principal A LA API REST DE SUPABASE
-- Ejecutar en Supabase → SQL Editor → New query → Pegar → Run
-- =============================================================================
-- Sin estos GRANT, PostgREST bloquea el acceso y el dashboard no puede leer la vista.

-- 0. Uso del schema public (necesario para que la API vea las tablas/vistas)
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;

-- 1. Permisos para que la API REST pueda leer la vista
GRANT SELECT ON public.vista_tablero_principal TO anon;
GRANT SELECT ON public.vista_tablero_principal TO authenticated;
GRANT SELECT ON public.vista_tablero_principal TO service_role;

-- 2. Opcional: permitir que la tabla cantidad_solicitada acepte UPSERT desde la API
-- (necesario para que el botón "Guardar cambios" del dashboard funcione)
GRANT SELECT, INSERT, UPDATE ON public.cantidad_solicitada TO anon;
GRANT SELECT, INSERT, UPDATE ON public.cantidad_solicitada TO authenticated;
GRANT ALL ON public.cantidad_solicitada TO service_role;

-- 3. Verificación (opcional): al ejecutar, no debe dar error.
-- Si la vista no existe, primero ejecuta migracion_definitiva.sql
SELECT 1 FROM public.vista_tablero_principal LIMIT 1;
