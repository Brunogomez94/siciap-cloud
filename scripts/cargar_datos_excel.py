"""
Carga datos desde archivos Excel a PostgreSQL local, en el orden correcto.

Orden de ejecución: 1) Órdenes, 2) Ejecución, 3) Stock, 4) Pedidos.

Uso:
  python scripts/cargar_datos_excel.py
  python scripts/cargar_datos_excel.py "C:\ruta\a\carpeta\con\excels"
"""
import sys
import logging
from pathlib import Path

# Raíz del proyecto
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from config.settings import Settings
from etl.processors import OrdenesProcessor, EjecucionProcessor, StockProcessor, PedidosProcessor

# Orden de anclaje: no cambiar el orden de esta lista
PROCESADORES = [
    ("ordenes", OrdenesProcessor, "ordenes.xlsx"),
    ("ejecucion", EjecucionProcessor, "ejecucion.xlsx"),
    ("stock", StockProcessor, "stock.xlsx"),
    ("pedidos", PedidosProcessor, "pedidos.xlsx"),
]


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger(__name__)

    # Carpeta de datos: primer argumento o data/ por defecto
    data_dir = Path(Settings.get_data_dir())
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
    if not data_dir.is_dir():
        logger.error("No existe el directorio: %s", data_dir)
        sys.exit(1)

    logger.info("Directorio de datos: %s", data_dir)
    logger.info("Orden de carga: Ordenes -> Ejecucion -> Stock -> Pedidos")

    ok = 0
    for nombre, clase_procesador, nombre_archivo in PROCESADORES:
        ruta = data_dir / nombre_archivo
        if not ruta.exists():
            # Buscar archivo con nombre similar (ej. Ordenes_2024.xlsx)
            candidatos = list(data_dir.glob(f"*{nombre}*.xlsx")) + list(data_dir.glob(f"*{nombre}*.xls"))
            ruta = candidatos[0] if candidatos else None
        if ruta is None or not ruta.exists():
            logger.warning("[OMITIDO] No encontrado: %s (o *%s*.xlsx)", nombre_archivo, nombre)
            continue
        try:
            contenido = ruta.read_bytes()
            proc = clase_procesador()
            if proc.process_file(contenido, ruta.name):
                logger.info("[OK] %s cargado desde %s", nombre, ruta.name)
                ok += 1
            else:
                logger.error("[ERROR] Fallo al procesar %s", nombre_archivo)
        except Exception as e:
            logger.exception("[ERROR] %s: %s", nombre_archivo, e)

    logger.info("--- Fin: %d de %d archivos cargados", ok, len(PROCESADORES))
    sys.exit(0 if ok > 0 else 1)


if __name__ == "__main__":
    main()
