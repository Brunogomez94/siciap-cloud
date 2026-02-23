-- =============================================================================
-- CORRECCIÓN CRÍTICA: Cambiar ejecucion.item de INTEGER NOT NULL a TEXT
-- Ejecutar esto en PostgreSQL local para permitir valores como "2-2.2"
-- =============================================================================

-- Verificar el tipo actual
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'siciap'
  AND table_name = 'ejecucion'
  AND column_name = 'item';

-- Cambiar tipo de INTEGER NOT NULL a TEXT (permite NULL y valores como "2-2.2")
ALTER TABLE siciap.ejecucion ALTER COLUMN item TYPE TEXT;
ALTER TABLE siciap.ejecucion ALTER COLUMN item DROP NOT NULL;

-- Verificar que se aplicó correctamente
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'siciap'
  AND table_name = 'ejecucion'
  AND column_name = 'item';
-- Debería mostrar: data_type = 'text', is_nullable = 'YES'
