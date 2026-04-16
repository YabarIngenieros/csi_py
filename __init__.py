"""
CSI Python Library
==================

Una biblioteca Python para automatizar y controlar software de análisis
estructural CSI (ETABS, SAP2000, SAFE) mediante API .NET o COM.
"""

__version__ = "0.1.0"
__author__ = "YabarIngenieros"
__license__ = "MIT"

from .handler import (
    CSIHandler,
    get__pids,
    get_paths,
    validate_programs,
    get_available_backends,
)
from .constants import (
    eUnits,
    eFramePropType,
    EtabsError,
    eMatType,
    u,
)
from .extractor import DataExtractor
from .builder import ModelBuilder

__all__ = [
    "CSIHandler",
    "Handler",
    "get__pids",
    "get_paths",
    "validate_programs",
    "get_available_backends",
    "DataExtractor",
    "ModelBuilder",
    "eUnits",
    "eFramePropType",
    "eMatType",
    "EtabsError",
    "u",
    "__version__",
    "__author__",
    "__license__",
]

CSI = CSIHandler
Handler = CSIHandler

def get_version():
    return __version__


def get_supported_programs():
    return ["ETABS", "SAP2000", "SAFE"]


def get_default_backend():
    return "dotnet"


def get_available_units():
    return {
        "Imperial": ["lb_in_F", "lb_ft_F", "kip_in_F", "kip_ft_F"],
        "Metric_kN": ["kN_mm_C", "kN_m_C", "kN_cm_C"],
        "Metric_kgf": ["kgf_mm_C", "kgf_m_C", "kgf_cm_C"],
        "Metric_N": ["N_mm_C", "N_m_C", "N_cm_C"],
        "Metric_Ton": ["Ton_mm_C", "Ton_m_C", "Ton_cm_C"],
    }
