"""
Script para eliminar la restricción UNIQUE de ejecucion
"""
import psycopg2
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    cur = conn.cursor()
    
    # Verificar restricciones existentes
    print("Verificando restricciones UNIQUE existentes...")
    cur.execute("""
        SELECT constraint_name, constraint_type 
        FROM information_schema.table_constraints
        WHERE table_schema = 'siciap' 
          AND table_name = 'ejecucion' 
          AND constraint_type = 'UNIQUE'
    """)
    
    constraints = cur.fetchall()
    if constraints:
        print(f"\nRestricciones UNIQUE encontradas: {len(constraints)}")
        for row in constraints:
            print(f"   - {row[0]} ({row[1]})")
    else:
        print("\nNo se encontraron restricciones UNIQUE")
    
    # Eliminar la restricción
    print("\nEliminando restriccion UNIQUE...")
    cur.execute("""
        ALTER TABLE siciap.ejecucion 
        DROP CONSTRAINT IF EXISTS ejecucion_id_llamado_licitacion_codigo_item_key
    """)
    conn.commit()
    print("Restriccion eliminada exitosamente")
    
    # Verificar que se eliminó
    print("\nVerificando que se elimino...")
    cur.execute("""
        SELECT constraint_name, constraint_type 
        FROM information_schema.table_constraints
        WHERE table_schema = 'siciap' 
          AND table_name = 'ejecucion' 
          AND constraint_type = 'UNIQUE'
    """)
    
    remaining = cur.fetchall()
    if remaining:
        print(f"\nATENCION: Aun quedan {len(remaining)} restricciones UNIQUE:")
        for row in remaining:
            print(f"   - {row[0]}")
    else:
        print("\nVerificacion exitosa: No quedan restricciones UNIQUE en siciap.ejecucion")
    
    cur.close()
    conn.close()
    
    print("\nScript completado exitosamente!")
    
except Exception as e:
    print(f"\nError ejecutando script: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
