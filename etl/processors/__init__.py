"""
Procesadores modulares para diferentes tipos de datos
"""
from .ordenes import OrdenesProcessor
from .ejecucion import EjecucionProcessor
from .stock import StockProcessor
from .pedidos import PedidosProcessor
from .vencimientos_parques import VencimientosParquesProcessor

__all__ = [
    'OrdenesProcessor', 'EjecucionProcessor', 'StockProcessor', 'PedidosProcessor',
    'VencimientosParquesProcessor'
]
