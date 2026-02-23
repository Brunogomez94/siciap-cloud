-- Verificar que las 7 tablas se crearon correctamente
SELECT 
    tablename,
    schemaname
FROM pg_catalog.pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
      'ordenes', 
      'ejecucion', 
      'datosejecucion', 
      'stock_critico', 
      'pedidos', 
      'cantidad_solicitada', 
      'vencimientos_parques'
  )
ORDER BY tablename;
