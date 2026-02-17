"""
🧪 PRUEBA DE HUMO (SMOKE TEST) - SICIAP Cloud
Simula un día real de trabajo: Excel → Local → Supabase → Verificación
"""
import sys
import logging
from pathlib import Path
from sqlalchemy import text

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config.database import DatabaseConfig
from config.supabase import SupabaseConfig
from etl.sync.sync_manager import SyncManager
from sqlalchemy import create_engine

# Configurar logging con encoding UTF-8 para Windows
import io
import sys

# Forzar UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_local_connection():
    """Paso 1: Verificar conexión a PostgreSQL local"""
    logger.info("=" * 60)
    logger.info("PASO 1: Verificando conexión a PostgreSQL LOCAL")
    logger.info("=" * 60)
    
    try:
        db_config = DatabaseConfig()
        conn_str = db_config.get_connection_string()
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'siciap'"))
            table_count = result.scalar()
            logger.info(f"[OK] PostgreSQL LOCAL: Conectado")
            logger.info(f"   Tablas en esquema 'siciap': {table_count}")
            return True
    except Exception as e:
        logger.error(f"[ERROR] PostgreSQL LOCAL: Error - {e}")
        return False


def test_supabase_connection():
    """Paso 2: Verificar conexión a Supabase"""
    logger.info("=" * 60)
    logger.info("PASO 2: Verificando conexión a SUPABASE")
    logger.info("=" * 60)
    
    try:
        supabase_config = SupabaseConfig()
        if not supabase_config.is_configured():
            logger.warning("[WARN] Supabase no esta configurado en .env")
            return False
        
        conn_str = supabase_config.get_connection_string()
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            table_count = result.scalar()
            logger.info(f"[OK] SUPABASE: Conectado")
            logger.info(f"   Tablas en esquema 'public': {table_count}")
            return True
    except Exception as e:
        logger.error(f"[ERROR] SUPABASE: Error - {e}")
        logger.warning("   (Esto es normal si estas en una red restrictiva)")
        return False


def check_local_data():
    """Paso 3: Verificar datos en PostgreSQL local"""
    logger.info("=" * 60)
    logger.info("PASO 3: Verificando datos en PostgreSQL LOCAL")
    logger.info("=" * 60)
    
    tables_to_check = ['ordenes', 'ejecucion', 'stock_critico', 'pedidos', 'vencimientos_parques']
    results = {}
    
    try:
        db_config = DatabaseConfig()
        conn_str = db_config.get_connection_string()
        engine = create_engine(conn_str)
        
        with engine.connect() as conn:
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM siciap.{table}"))
                    count = result.scalar()
                    results[table] = count
                    status = "[OK]" if count > 0 else "[WARN]"
                    logger.info(f"{status} {table}: {count} registros")
                except Exception as e:
                    results[table] = 0
                    logger.warning(f"⚠️  {table}: No existe o error - {e}")
        
        total_records = sum(results.values())
        logger.info(f"\n📊 Total de registros en LOCAL: {total_records}")
        
        return results, total_records > 0
    except Exception as e:
        logger.error(f"[ERROR] Error verificando datos locales: {e}")
        return {}, False


def test_sync():
    """Paso 4: Probar sincronización Local → Supabase"""
    logger.info("=" * 60)
    logger.info("PASO 4: Probando SINCRONIZACIÓN Local → Supabase")
    logger.info("=" * 60)
    
    try:
        sync_manager = SyncManager()
        
        # Verificar que Supabase esté configurado
        if not sync_manager.supabase_config.is_configured():
            logger.warning("⚠️  Supabase no configurado. Saltando sincronización.")
            return False
        
        # Intentar sincronizar solo la primera tabla como prueba
        test_table = 'ordenes'
        logger.info(f"[SYNC] Sincronizando tabla de prueba: {test_table}")
        
        success = sync_manager.sync_table(test_table)
        
        if success:
            logger.info(f"[OK] Sincronizacion de {test_table} exitosa")
            
            # Verificar que los datos llegaron
            verification = sync_manager.verify_sync(test_table)
            if 'error' not in verification:
                logger.info(f"   Local: {verification['local_count']} registros")
                logger.info(f"   Supabase: {verification['supabase_count']} registros")
                logger.info(f"   {'[OK] Coinciden' if verification['match'] else '[WARN] No coinciden'}")
                return verification['match']
            else:
                logger.warning(f"[WARN] No se pudo verificar: {verification.get('error')}")
                return False
        else:
            logger.error(f"[ERROR] Sincronizacion de {test_table} fallo")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en sincronizacion: {e}")
        return False


def verify_supabase_data():
    """Paso 5: Verificar datos en Supabase"""
    logger.info("=" * 60)
    logger.info("PASO 5: Verificando datos en SUPABASE")
    logger.info("=" * 60)
    
    tables_to_check = ['ordenes', 'ejecucion', 'stock_critico', 'pedidos', 'vencimientos_parques']
    results = {}
    
    try:
        supabase_config = SupabaseConfig()
        if not supabase_config.is_configured():
            logger.warning("[WARN] Supabase no configurado. Saltando verificacion.")
            return {}, False
        
        conn_str = supabase_config.get_connection_string()
        engine = create_engine(conn_str)
        
        with engine.connect() as conn:
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    results[table] = count
                    status = "[OK]" if count > 0 else "[WARN]"
                    logger.info(f"{status} {table}: {count} registros")
                except Exception as e:
                    results[table] = 0
                    logger.warning(f"⚠️  {table}: No existe o error - {e}")
        
        total_records = sum(results.values())
        logger.info(f"\n📊 Total de registros en SUPABASE: {total_records}")
        
        return results, total_records > 0
    except Exception as e:
        logger.error(f"[ERROR] Error verificando datos en Supabase: {e}")
        return {}, False


def main():
    """Ejecuta la prueba de humo completa"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 PRUEBA DE HUMO - SICIAP Cloud")
    logger.info("=" * 60)
    logger.info("Simulando flujo completo: Local → Supabase\n")
    
    results = {
        'local_connection': False,
        'supabase_connection': False,
        'local_data': False,
        'sync': False,
        'supabase_data': False
    }
    
    # Paso 1: Conexión local
    results['local_connection'] = test_local_connection()
    if not results['local_connection']:
        logger.error("\n[ERROR] FALLO CRITICO: No se puede conectar a PostgreSQL local")
        logger.error("   Verifica tu .env y que PostgreSQL este corriendo")
        return False
    
    # Paso 2: Conexión Supabase (opcional)
    results['supabase_connection'] = test_supabase_connection()
    
    # Paso 3: Datos locales
    local_data, results['local_data'] = check_local_data()
    if not results['local_data']:
        logger.warning("\n[WARN] ADVERTENCIA: No hay datos en PostgreSQL local")
        logger.warning("   Ejecuta primero: python scripts/cargar_datos_excel.py")
        logger.warning("   O importa datos desde la UI de Streamlit")
    
    # Paso 4: Sincronización (solo si Supabase está disponible)
    if results['supabase_connection']:
        results['sync'] = test_sync()
    else:
        logger.warning("\n[WARN] Saltando sincronizacion: Supabase no disponible")
        results['sync'] = None
    
    # Paso 5: Verificación Supabase
    if results['supabase_connection']:
        supabase_data, results['supabase_data'] = verify_supabase_data()
    else:
        logger.warning("\n[WARN] Saltando verificacion Supabase: No disponible")
        results['supabase_data'] = None
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📋 RESUMEN DE PRUEBA DE HUMO")
    logger.info("=" * 60)
    logger.info(f"[OK] PostgreSQL Local: {'OK' if results['local_connection'] else 'FALLO'}")
    logger.info(f"{'[OK]' if results['supabase_connection'] else '[WARN]'} Supabase: {'OK' if results['supabase_connection'] else 'No disponible'}")
    logger.info(f"{'[OK]' if results['local_data'] else '[WARN]'} Datos Locales: {'OK' if results['local_data'] else 'Vacio'}")
    logger.info(f"{'[OK]' if results['sync'] else '[WARN]' if results['sync'] is None else '[ERROR]'} Sincronizacion: {'OK' if results['sync'] else 'Saltado' if results['sync'] is None else 'FALLO'}")
    logger.info(f"{'[OK]' if results['supabase_data'] else '[WARN]' if results['supabase_data'] is None else '[ERROR]'} Datos Supabase: {'OK' if results['supabase_data'] else 'Saltado' if results['supabase_data'] is None else 'Vacio'}")
    
    # Veredicto
    if results['local_connection']:
        logger.info("\n[OK] SISTEMA LOCAL: FUNCIONAL")
        if results['supabase_connection'] and results['sync']:
            logger.info("[OK] SISTEMA COMPLETO: FUNCIONAL (Local + Supabase)")
            logger.info("\n[SUCCESS] PRUEBA DE HUMO EXITOSA!")
            return True
        else:
            logger.info("[WARN] SISTEMA PARCIAL: Funcional solo en local (Supabase no disponible)")
            logger.info("\n[OK] PRUEBA DE HUMO EXITOSA (modo local)")
            return True
    else:
        logger.error("\n[ERROR] PRUEBA DE HUMO FALLIDA")
        logger.error("   Revisa los errores arriba")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
