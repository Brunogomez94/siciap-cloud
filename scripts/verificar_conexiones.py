"""
Script para verificar conexiones a bases de datos
"""
import sys
import os
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')  # UTF-8
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Agregar raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config.database import DatabaseConfig
from config.supabase import SupabaseConfig
from sqlalchemy import create_engine, text


def verificar_postgres_local():
    """Verifica conexión a PostgreSQL local"""
    print("\n" + "="*50)
    print("VERIFICANDO CONEXIÓN A POSTGRESQL LOCAL")
    print("="*50)
    
    try:
        db_config = DatabaseConfig()
        db_config.validate()
        
        print(f"[OK] Host: {db_config.HOST}")
        print(f"[OK] Puerto: {db_config.PORT}")
        print(f"[OK] Base de datos: {db_config.DATABASE}")
        print(f"[OK] Usuario: {db_config.USER}")
        print(f"[OK] Password: {'*' * len(db_config.PASSWORD)}")
        
        # Intentar conectar
        conn_str = db_config.get_connection_string()
        engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n[OK] Conexion exitosa!")
            print(f"  Version PostgreSQL: {version[:50]}...")
            
            # Verificar esquema
            result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'siciap';"))
            if result.fetchone():
                print(f"[OK] Esquema 'siciap' existe")
            else:
                print(f"[ERROR] Esquema 'siciap' NO existe - Ejecuta database/local/schema.sql")
            
            # Contar tablas
            result = conn.execute(text("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'siciap'
            """))
            table_count = result.fetchone()[0]
            print(f"[OK] Tablas en esquema 'siciap': {table_count}")
            
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nVerifica:")
        print("  1. PostgreSQL esta corriendo")
        print("  2. La base de datos 'siciap_local' existe")
        print("  3. Las credenciales en .env son correctas")
        return False


def verificar_supabase():
    """Verifica conexión a Supabase"""
    print("\n" + "="*50)
    print("VERIFICANDO CONEXIÓN A SUPABASE")
    print("="*50)
    
    try:
        supabase_config = SupabaseConfig()
        
        if not supabase_config.is_configured():
            print("[INFO] Supabase NO esta configurado")
            print("  Configura las variables SUPABASE_URL y SUPABASE_KEY en .env")
            return False
        
        print(f"[OK] URL: {supabase_config.URL}")
        print(f"[OK] API Key: {supabase_config.API_KEY[:20]}...")
        print(f"[OK] DB Host: {supabase_config.DB_HOST}")
        print(f"[OK] DB Port: {supabase_config.DB_PORT}")
        print(f"[OK] DB Name: {supabase_config.DB_NAME}")
        print(f"[OK] DB User: {supabase_config.DB_USER}")
        print(f"[OK] DB Password: {'*' * len(supabase_config.DB_PASSWORD)}")
        
        # Intentar conectar
        conn_str = supabase_config.get_connection_string()
        engine = create_engine(conn_str, connect_args={"client_encoding": "utf8"})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"\n[OK] Conexion exitosa!")
            print(f"  Version PostgreSQL: {version[:50]}...")
            
            # Verificar tablas principales
            tables_to_check = ['ordenes', 'ejecucion', 'datosejecucion', 'stock_critico', 'pedidos']
            print(f"\nVerificando tablas:")
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT count(*) FROM {table};"))
                    count = result.fetchone()[0]
                    print(f"  [OK] {table}: {count} registros")
                except Exception as e:
                    print(f"  [ERROR] {table}: NO existe o error - {e}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nVerifica:")
        print("  1. Las credenciales en .env son correctas")
        print("  2. El proyecto de Supabase esta activo")
        print("  3. Ejecutaste database/supabase/schema.sql")
        return False


def main():
    """Función principal"""
    print("\n" + "="*50)
    print("VERIFICADOR DE CONEXIONES - SICIAP CLOUD")
    print("="*50)
    
    # Verificar PostgreSQL local
    local_ok = verificar_postgres_local()
    
    # Verificar Supabase
    supabase_ok = verificar_supabase()
    
    # Resumen
    print("\n" + "="*50)
    print("RESUMEN")
    print("="*50)
    print(f"PostgreSQL Local: {'[OK]' if local_ok else '[ERROR]'}")
    print(f"Supabase:         {'[OK]' if supabase_ok else '[NO CONFIGURADO]'}")
    
    if local_ok:
        print("\n[OK] Conexion a PostgreSQL Local funcionando correctamente!")
        if supabase_ok:
            print("[OK] Conexion a Supabase funcionando correctamente!")
        else:
            print("[INFO] Supabase no configurado - puedes continuar solo con PostgreSQL local")
        return 0
    else:
        print("\n[ERROR] Hay problemas con las conexiones. Revisa los errores arriba.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
