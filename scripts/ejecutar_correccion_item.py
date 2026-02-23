"""
Script para ejecutar la corrección crítica de ejecucion.item
Ejecuta ALTER TABLE en PostgreSQL local y Supabase
"""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import psycopg2
from config.database import DatabaseConfig
from config.supabase import SupabaseConfig
from dotenv import load_dotenv

load_dotenv(root_dir / '.env')


def ejecutar_sql_local():
    """Ejecuta la corrección en PostgreSQL local"""
    print("=" * 60)
    print("EJECUTANDO CORRECCIÓN EN POSTGRESQL LOCAL")
    print("=" * 60)
    
    try:
        config = DatabaseConfig()
        conn_dict = config.get_connection_dict()
        
        print(f"Conectando a: {conn_dict['host']}:{conn_dict['port']}/{conn_dict['database']}")
        
        conn = psycopg2.connect(**conn_dict)
        cursor = conn.cursor()
        
        # Verificar tipo actual
        print("\n1. Verificando tipo actual de ejecucion.item...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'siciap'
              AND table_name = 'ejecucion'
              AND column_name = 'item'
        """)
        resultado = cursor.fetchone()
        if resultado:
            print(f"   Tipo actual: {resultado[1]}, Nullable: {resultado[2]}")
        else:
            print("   ⚠️ Columna 'item' no encontrada en siciap.ejecucion")
            cursor.close()
            conn.close()
            return False
        
        # Verificar si ya está corregido
        if resultado[1] == 'text' and resultado[2] == 'YES':
            print("   [OK] Ya está corregido (TEXT, nullable)")
            cursor.close()
            conn.close()
            return True
        
        # Ejecutar corrección
        print("\n2. Ejecutando ALTER TABLE...")
        cursor.execute("ALTER TABLE siciap.ejecucion ALTER COLUMN item TYPE TEXT")
        cursor.execute("ALTER TABLE siciap.ejecucion ALTER COLUMN item DROP NOT NULL")
        conn.commit()
        print("   [OK] Cambios aplicados correctamente")
        
        # Verificar tipo nuevo
        print("\n3. Verificando tipo nuevo...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'siciap'
              AND table_name = 'ejecucion'
              AND column_name = 'item'
        """)
        resultado = cursor.fetchone()
        if resultado:
            print(f"   Tipo nuevo: {resultado[1]}, Nullable: {resultado[2]}")
            if resultado[1] == 'text' and resultado[2] == 'YES':
                print("   [OK] Correccion exitosa!")
            else:
                print("   [ADVERTENCIA] El tipo no es el esperado")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error ejecutando correccion en PostgreSQL local: {e}")
        return False


def ejecutar_sql_supabase():
    """Ejecuta la corrección en Supabase"""
    print("\n" + "=" * 60)
    print("EJECUTANDO CORRECCIÓN EN SUPABASE")
    print("=" * 60)
    
    try:
        config = SupabaseConfig()
        
        # Verificar si está configurado
        if not config.DB_HOST or not config.DB_PASSWORD:
            print("[INFO] Supabase no esta configurado en .env")
            print("   Saltando correccion en Supabase...")
            return False
        
        conn_dict = config.get_connection_dict()
        
        print(f"Conectando a: {conn_dict['host']}:{conn_dict['port']}/{conn_dict['database']}")
        
        conn = psycopg2.connect(**conn_dict)
        cursor = conn.cursor()
        
        # Verificar tipo actual
        print("\n1. Verificando tipo actual de ejecucion.item...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'ejecucion'
              AND column_name = 'item'
        """)
        resultado = cursor.fetchone()
        if resultado:
            print(f"   Tipo actual: {resultado[1]}, Nullable: {resultado[2]}")
        else:
            print("   [INFO] Columna 'item' no encontrada en public.ejecucion")
            print("   [INFO] La tabla puede no existir aun en Supabase")
            cursor.close()
            conn.close()
            return False
        
        # Verificar si ya está corregido
        if resultado[1] == 'text' and resultado[2] == 'YES':
            print("   [OK] Ya esta corregido (TEXT, nullable)")
            cursor.close()
            conn.close()
            return True
        
        # Ejecutar corrección
        print("\n2. Ejecutando ALTER TABLE...")
        cursor.execute("ALTER TABLE public.ejecucion ALTER COLUMN item TYPE TEXT")
        cursor.execute("ALTER TABLE public.ejecucion ALTER COLUMN item DROP NOT NULL")
        conn.commit()
        print("   [OK] Cambios aplicados correctamente")
        
        # Verificar tipo nuevo
        print("\n3. Verificando tipo nuevo...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'ejecucion'
              AND column_name = 'item'
        """)
        resultado = cursor.fetchone()
        if resultado:
            print(f"   Tipo nuevo: {resultado[1]}, Nullable: {resultado[2]}")
            if resultado[1] == 'text' and resultado[2] == 'YES':
                print("   [OK] Correccion exitosa!")
            else:
                print("   [ADVERTENCIA] El tipo no es el esperado")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error ejecutando correccion en Supabase: {e}")
        print("   Esto puede ser normal si Supabase no esta configurado o la tabla no existe")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CORRECCIÓN CRÍTICA: ejecucion.item")
    print("Cambiando de INTEGER NOT NULL a TEXT")
    print("=" * 60 + "\n")
    
    # Ejecutar en PostgreSQL local
    resultado_local = ejecutar_sql_local()
    
    # Ejecutar en Supabase (opcional)
    resultado_supabase = ejecutar_sql_supabase()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"PostgreSQL Local: {'[OK] Exitoso' if resultado_local else '[ERROR] Fallo'}")
    print(f"Supabase:         {'[OK] Exitoso' if resultado_supabase else '[INFO] Saltado o Fallo'}")
    print("\n" + "=" * 60)
    
    if resultado_local:
        print("\n[OK] Correccion aplicada en PostgreSQL local")
        print("   Ahora puedes cargar archivos Excel con item='2-2.2' sin errores")
    else:
        print("\n[ERROR] Error en PostgreSQL local. Verifica la conexion y configuracion.")
    
    if resultado_supabase:
        print("[OK] Correccion aplicada en Supabase")
    else:
        print("[INFO] Supabase: No se aplico (puede ser normal si no esta configurado)")
