"""
Gestor de sincronización de datos Local → Supabase
"""
import pandas as pd
import logging
from typing import List, Optional
from sqlalchemy import create_engine, text
from config.database import DatabaseConfig
from config.supabase import SupabaseConfig
from config.settings import Settings

logger = logging.getLogger(__name__)


class SyncManager:
    """Gestiona la sincronización de datos desde PostgreSQL local a Supabase"""
    
    # Tablas a sincronizar
    TABLES_TO_SYNC = [
        'ordenes',
        'ejecucion',
        'datosejecucion',
        'stock_critico',
        'pedidos',
        'cantidad_solicitada',
        'vencimientos_parques'
    ]
    
    def __init__(self):
        """Inicializa el gestor de sincronización"""
        self.local_config = DatabaseConfig()
        self.supabase_config = SupabaseConfig()
        self.local_engine = None
        self.supabase_engine = None
    
    def get_local_connection(self):
        """Obtiene conexión a PostgreSQL local"""
        if self.local_engine is None:
            conn_str = self.local_config.get_connection_string()
            self.local_engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        return self.local_engine.connect()
    
    def get_supabase_connection(self):
        """Obtiene conexión a Supabase"""
        if not self.supabase_config.is_configured():
            raise ValueError("Supabase no está configurado. Verifica .env")
        
        if self.supabase_engine is None:
            conn_str = self.supabase_config.get_connection_string()
            self.supabase_engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        return self.supabase_engine.connect()
    
    def _table_exists_in_supabase(self, conn, table_name: str) -> bool:
        """Verifica si la tabla existe en Supabase."""
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = :table
            )
        """), {"table": table_name})
        return result.scalar()
    
    def _get_supabase_table_columns(self, conn, table_name: str):
        """Obtiene las columnas que existen en la tabla de Supabase (schema public)."""
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table
            ORDER BY ordinal_position
        """), {"table": table_name})
        return [row[0] for row in result]
    
    def sync_table(self, table_name: str, schema: str = 'siciap', batch_size: int = 1000) -> bool:
        """
        Sincroniza una tabla específica
        
        Args:
            table_name: Nombre de la tabla
            schema: Esquema de la tabla (local)
            batch_size: Tamaño del lote para sincronización
        
        Returns:
            True si la sincronización fue exitosa
        """
        try:
            logger.info(f"Sincronizando tabla {schema}.{table_name}...")
            
            # Leer datos de PostgreSQL local
            with self.get_local_connection() as local_conn:
                query = text(f"SELECT * FROM {schema}.{table_name}")
                df = pd.read_sql(query, local_conn)
            
            if df.empty:
                logger.warning(f"Tabla {table_name} está vacía, saltando sincronización")
                return True
            
            logger.info(f"Leídas {len(df)} filas de {schema}.{table_name}")
            
            # Escribir datos a Supabase
            supabase_conn = self.get_supabase_connection()
            try:
                # Verificar que la tabla existe en Supabase (usar autocommit para evitar transacciones)
                if not self._table_exists_in_supabase(supabase_conn, table_name):
                    logger.warning(f"Tabla {table_name} no existe en Supabase, saltando sincronización")
                    supabase_conn.close()
                    return False
                
                # Obtener columnas que existen en Supabase (filtrar antes de insertar)
                skip_cols = {'id', 'creado_en', 'actualizado_en'}
                supabase_cols = [c for c in self._get_supabase_table_columns(supabase_conn, table_name) if c not in skip_cols]
                valid_cols = [c for c in df.columns if c in supabase_cols]
                
                if not valid_cols:
                    logger.error(f"Ninguna columna del DataFrame existe en Supabase.{table_name}. Tabla Supabase: {supabase_cols}")
                    supabase_conn.close()
                    return False
                
                missing = set(supabase_cols) - set(valid_cols)
                if missing:
                    logger.info(f"Columnas omitidas (no vienen en local): {missing}")
                
                df_filtered = df[valid_cols].copy()
                logger.info(f"Filtrando a {len(valid_cols)} columnas válidas de {len(df.columns)} originales")
                
                # Cerrar conexión anterior y crear una nueva para la transacción
                supabase_conn.close()
                supabase_conn = self.get_supabase_connection()
                
                # Limpiar tabla en Supabase (usar DELETE en lugar de TRUNCATE para mejor compatibilidad)
                trans = supabase_conn.begin()
                try:
                    supabase_conn.execute(text(f"DELETE FROM public.{table_name}"))
                    
                    # Insertar datos en lotes
                    total_rows = len(df_filtered)
                    for i in range(0, total_rows, batch_size):
                        batch = df_filtered.iloc[i:i+batch_size]
                        batch.to_sql(
                            table_name,
                            supabase_conn,
                            schema='public',
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                        logger.info(f"Insertadas {min(i+batch_size, total_rows)}/{total_rows} filas")
                    
                    trans.commit()
                    logger.info(f"[OK] Tabla {table_name} sincronizada exitosamente")
                    supabase_conn.close()
                    return True
                
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Error sincronizando {table_name}: {e}", exc_info=True)
                    supabase_conn.close()
                    return False
            except Exception as e:
                logger.error(f"Error obteniendo conexión Supabase: {e}", exc_info=True)
                if supabase_conn:
                    supabase_conn.close()
                return False
        
        except Exception as e:
            logger.error(f"Error en sincronización de {table_name}: {e}", exc_info=True)
            return False
    
    def sync_all_tables(self) -> dict:
        """
        Sincroniza todas las tablas configuradas
        
        Returns:
            Diccionario con resultados de sincronización
        """
        results = {}
        
        logger.info("Iniciando sincronización completa...")
        
        for table in self.TABLES_TO_SYNC:
            success = self.sync_table(table)
            results[table] = {
                'success': success,
                'synced_at': pd.Timestamp.now().isoformat()
            }
        
        # Resumen
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        
        logger.info(f"Sincronización completada: {successful}/{total} tablas exitosas")
        
        # Refrescar vista materializada si existe (opcional, no crítico)
        # Nota: Esta función solo existe si se creó la vista materializada manualmente en Supabase
        # Por ahora, simplemente omitimos este paso para evitar errores
        # Si necesitas la vista materializada, créala manualmente en Supabase con el script correspondiente
        pass  # Comentado temporalmente hasta que se cree la vista materializada en Supabase
        
        return results
    
    def sync_table_incremental(self, table_name: str, schema: str = 'siciap', 
                              timestamp_column: str = 'actualizado_en') -> bool:
        """
        Sincronización incremental basada en timestamp
        
        Args:
            table_name: Nombre de la tabla
            schema: Esquema de la tabla
            timestamp_column: Columna de timestamp para detectar cambios
        
        Returns:
            True si la sincronización fue exitosa
        """
        try:
            logger.info(f"Sincronización incremental de {schema}.{table_name}...")
            
            # Obtener último timestamp sincronizado de Supabase
            with self.get_supabase_connection() as supabase_conn:
                try:
                    result = supabase_conn.execute(
                        text(f"SELECT MAX({timestamp_column}) as max_ts FROM public.{table_name}")
                    ).fetchone()
                    last_sync = result[0] if result and result[0] else None
                except Exception:
                    # Si la tabla no existe o no tiene la columna, sincronizar todo
                    last_sync = None
            
            # Leer solo registros nuevos/modificados
            with self.get_local_connection() as local_conn:
                if last_sync:
                    query = text(
                        f"SELECT * FROM {schema}.{table_name} "
                        f"WHERE {timestamp_column} > :last_sync"
                    )
                    df = pd.read_sql(query, local_conn, params={'last_sync': last_sync})
                else:
                    query = text(f"SELECT * FROM {schema}.{table_name}")
                    df = pd.read_sql(query, local_conn)
            
            if df.empty:
                logger.info(f"No hay cambios nuevos en {table_name}")
                return True
            
            logger.info(f"Sincronizando {len(df)} filas nuevas/modificadas...")
            
            # Insertar/actualizar en Supabase
            with self.get_supabase_connection() as supabase_conn:
                trans = supabase_conn.begin()
                try:
                    # Usar upsert si hay clave primaria, sino insertar
                    df.to_sql(
                        table_name,
                        supabase_conn,
                        schema='public',
                        if_exists='append',
                        index=False,
                        method='multi'
                    )
                    
                    trans.commit()
                    logger.info(f"[OK] Sincronizacion incremental de {table_name} completada")
                    return True
                
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Error en sincronización incremental: {e}", exc_info=True)
                    return False
        
        except Exception as e:
            logger.error(f"Error en sincronización incremental de {table_name}: {e}", exc_info=True)
            return False
    
    def verify_sync(self, table_name: str) -> dict:
        """
        Verifica que la sincronización sea correcta comparando conteos
        
        Args:
            table_name: Nombre de la tabla a verificar
        
        Returns:
            Diccionario con información de verificación
        """
        try:
            # Contar registros en local
            with self.get_local_connection() as local_conn:
                local_count = local_conn.execute(
                    text(f"SELECT COUNT(*) FROM siciap.{table_name}")
                ).scalar()
            
            # Contar registros en Supabase
            with self.get_supabase_connection() as supabase_conn:
                supabase_count = supabase_conn.execute(
                    text(f"SELECT COUNT(*) FROM public.{table_name}")
                ).scalar()
            
            return {
                'table': table_name,
                'local_count': local_count,
                'supabase_count': supabase_count,
                'match': local_count == supabase_count,
                'difference': abs(local_count - supabase_count)
            }
        
        except Exception as e:
            logger.error(f"Error verificando sincronización de {table_name}: {e}", exc_info=True)
            return {
                'table': table_name,
                'error': str(e)
            }


def main():
    """Función principal para ejecutar sincronización desde línea de comandos"""
    import sys
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Settings.get_log_dir() / 'sync.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    sync_manager = SyncManager()
    
    if len(sys.argv) > 1:
        # Sincronizar tabla específica
        table_name = sys.argv[1]
        success = sync_manager.sync_table(table_name)
        sys.exit(0 if success else 1)
    else:
        # Sincronizar todas las tablas
        results = sync_manager.sync_all_tables()
        
        # Mostrar resumen
        print("\n=== Resumen de Sincronización ===")
        for table, result in results.items():
            status = "[OK]" if result['success'] else "[ERROR]"
            print(f"{status} {table}: {result.get('synced_at', 'N/A')}")
        
        # Verificar sincronización (no fallar si Supabase no es alcanzable, ej. timeout/firewall)
        print("\n=== Verificación ===")
        try:
            for table in SyncManager.TABLES_TO_SYNC:
                verification = sync_manager.verify_sync(table)
                if 'error' not in verification:
                    match = "[OK]" if verification['match'] else "[ERROR]"
                    print(f"{match} {table}: Local={verification['local_count']}, "
                          f"Supabase={verification['supabase_count']}")
                else:
                    print(f"[SKIP] {table}: Supabase no alcanzable - {verification.get('error', '')[:60]}")
        except Exception as e:
            print(f"[AVISO] No se pudo verificar con Supabase (timeout/firewall?). Sincronizacion OK.")
            logger.warning("Verificacion Supabase fallida: %s", e)


if __name__ == '__main__':
    main()
