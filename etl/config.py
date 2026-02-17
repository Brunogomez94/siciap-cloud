"""
Configuración para el módulo ETL
"""
from config.settings import Settings
from config.database import DatabaseConfig

# Configuración de procesamiento por lotes
BATCH_SIZE = Settings.ETL_BATCH_SIZE

# Configuración de logging
LOG_LEVEL = Settings.ETL_LOG_LEVEL

# Directorio de datos
DATA_DIR = Settings.get_data_dir()
