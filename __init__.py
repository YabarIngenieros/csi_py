"""
CSI Python Library
==================

Una biblioteca Python para automatizar y controlar software de análisis 
estructural CSI (ETABS, SAP2000, SAFE) mediante su API COM.

Uso básico:
----------
    from csi_py import CSIHandler
    
    # Crear handler
    model = CSIHandler(program='ETABS', units='kN_m_C')
    
    # Conectar a instancia abierta
    model.connect_open_instance()
    
    # Trabajar con el modelo
    # ...
    
    # Cerrar
    model.close()

Componentes principales:
-----------------------
- CSIHandler: Clase principal para interactuar con CSI software
- DataExtractor: Mixin para extracción de datos
- ModelBuilder: Mixin para construcción de modelos
- eUnits: Enumeración de unidades disponibles
- eFramePropType: Enumeración de tipos de sección de frames

Funciones utilitarias:
---------------------
- get__pids(program): Obtener PIDs de procesos activos
- get_paths(program): Obtener paths de archivos abiertos
- validate_programs(program): Validar y estandarizar nombre del programa
"""

__version__ = "0.1.0"
__author__ = "YabarIngenieros"
__license__ = "MIT"

# Importar componentes principales
from .handler import (
    CSIHandler,
    get__pids,
    get_paths,
    validate_programs
)

from .constants import (
    eUnits,
    eFramePropType,
    EtabsError
)

from .extractor import DataExtractor
from .builder import ModelBuilder

# Definir qué se exporta con "from csi_py import *"
__all__ = [
    # Clase principal
    'CSIHandler',
    
    # Funciones utilitarias
    'get__pids',
    'get_paths',
    'validate_programs',
    
    # Mixins (para uso avanzado)
    'DataExtractor',
    'ModelBuilder',
    
    # Constantes y enumeraciones
    'eUnits',
    'eFramePropType',
    'EtabsError',
    
    # Metadata
    '__version__',
    '__author__',
    '__license__',
]

# Alias para compatibilidad
Handler = CSIHandler

# Información de versión y paquete
def get_version():
    """Retorna la versión actual de la biblioteca"""
    return __version__

def get_supported_programs():
    """Retorna lista de programas soportados"""
    return ['ETABS', 'SAP2000', 'SAFE']

def get_available_units():
    """Retorna diccionario de unidades disponibles"""
    return {
        'Imperial': ['lb_in_F', 'lb_ft_F', 'kip_in_F', 'kip_ft_F'],
        'Metric_kN': ['kN_mm_C', 'kN_m_C', 'kN_cm_C'],
        'Metric_kgf': ['kgf_mm_C', 'kgf_m_C', 'kgf_cm_C'],
        'Metric_N': ['N_mm_C', 'N_m_C', 'N_cm_C'],
        'Metric_Ton': ['Ton_mm_C', 'Ton_m_C', 'Ton_cm_C']
    }