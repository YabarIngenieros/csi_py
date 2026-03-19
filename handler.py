from .constants import eUnits, u
from .extractor import DataExtractor
from .builder import ModelBuilder

import importlib
import os
from pathlib import Path
from typing import Optional

import psutil


PROGRAM_INFO = {
    "ETABS": {
        "exe": "ETABS.exe",
        "progid": "CSI.ETABS.API.ETABSObject",
        "module_name": "ETABSv1",
        "dll_name": "ETABSv1.dll",
    },
    "SAP2000": {
        "exe": "SAP2000.exe",
        "progid": "CSI.SAP2000.API.SapObject",
        "module_name": "SAP2000v1",
        "dll_name": "SAP2000v1.dll",
    },
    "SAFE": {
        "exe": "SAFE.exe",
        "progid": "CSI.SAFE.API.ETABSObject",
        "module_name": "SAFEv1",
        "dll_name": "SAFEv1.dll",
    },
}


def validate_programs(program: str):
    """
    Valida y normaliza el nombre del programa CSI.

    Acepta variantes como ``SAP`` y retorna ``ETABS``, ``SAP2000`` o ``SAFE``.
    """
    program = program.upper().strip()
    program_map = {
        "ETABS": "ETABS",
        "SAP": "SAP2000",
        "SAP2000": "SAP2000",
        "SAFE": "SAFE",
    }
    if program not in program_map:
        raise ValueError(f"Programa no válido: {program}. Use: ETABS, SAP2000 o SAFE")
    return program_map[program]


def validate_backend(backend: str):
    """
    Valida y normaliza el backend de conexión.

    Los valores admitidos son ``auto``, ``dotnet`` y ``comtypes``.
    """
    backend = (backend or "auto").lower().strip()
    valid_backends = {"auto", "dotnet", "comtypes"}
    if backend not in valid_backends:
        raise ValueError(f"Backend no válido: {backend}. Use: auto, dotnet o comtypes")
    return backend


def _get_program_info(program: str):
    return PROGRAM_INFO[validate_programs(program)]


def _iter_program_processes(program: str):
    """Itera los procesos activos asociados al programa CSI indicado."""
    exe_name = _get_program_info(program)["exe"]
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            if proc.info["name"] == exe_name:
                yield proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def get__pids(program="ETABS"):
    """
    Retorna los PIDs de las instancias activas del programa indicado.

    El filtro se realiza por nombre de ejecutable del programa CSI.
    """
    program = validate_programs(program)
    return [proc.info["pid"] for proc in _iter_program_processes(program)]


def _find_running_exe_paths(program: str):
    paths = []
    for proc in _iter_program_processes(program):
        exe_path = proc.info.get("exe")
        if exe_path:
            paths.append(exe_path)
    return paths


def _find_installation_exe(program: str):
    info = _get_program_info(program)
    candidate_paths = []
    for env_var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
        base = os.environ.get(env_var)
        if not base:
            continue
        csi_root = Path(base) / "Computers and Structures"
        if not csi_root.exists():
            continue
        for child in csi_root.iterdir():
            if not child.is_dir():
                continue
            if program not in child.name.upper():
                continue
            exe_path = child / info["exe"]
            if exe_path.exists():
                candidate_paths.append(str(exe_path))
    if not candidate_paths:
        return None
    return sorted(candidate_paths)[-1]


def _resolve_exe_path(program: str):
    running_paths = _find_running_exe_paths(program)
    if running_paths:
        return running_paths[0]
    return _find_installation_exe(program)


def _resolve_dll_path(program: str):
    exe_path = _resolve_exe_path(program)
    if not exe_path:
        return None
    dll_path = os.path.join(os.path.dirname(exe_path), _get_program_info(program)["dll_name"])
    return dll_path if os.path.exists(dll_path) else None


def _ensure_pythonnet_loaded():
    from pythonnet import load

    try:
        load("coreclr")
    except RuntimeError:
        pass
    except Exception:
        # Algunos entornos ya tienen un runtime cargado o usan otra configuración.
        pass

    import clr

    return clr


class _DotNetBackend:
    name = "dotnet"

    def __init__(self, program: str, dll_path: Optional[str] = None):
        self.program = validate_programs(program)
        self.program_info = _get_program_info(self.program)
        self.dll_path = dll_path or _resolve_dll_path(self.program)
        if not self.dll_path:
            raise RuntimeError(
                f"No se encontró {self.program_info['dll_name']} para {self.program}. "
                "Verifique que el programa CSI esté instalado."
            )

        clr = _ensure_pythonnet_loaded()
        clr.AddReference(self.dll_path)
        self.module = importlib.import_module(self.program_info["module_name"])
        self.helper = self.module.cHelper(self.module.Helper())

    def get_object(self):
        return self.module.cOAPI(self.helper.GetObject(self.program_info["progid"]))

    def get_object_process(self, pid: int):
        return self.module.cOAPI(self.helper.GetObjectProcess(self.program_info["progid"], pid))

    def create_object(self, exe_path: str):
        return self.module.cOAPI(self.helper.CreateObject(exe_path))

    def create_object_progid(self):
        return self.module.cOAPI(self.helper.CreateObjectProgID(self.program_info["progid"]))

    def get_sap_model(self, csi_object):
        return self.module.cSapModel(csi_object.SapModel)


class _ComtypesBackend:
    name = "comtypes"

    def __init__(self, program: str):
        self.program = validate_programs(program)
        self.program_info = _get_program_info(self.program)

        import comtypes.client

        self.comtypes_client = comtypes.client
        helper = self.comtypes_client.CreateObject(f"{self.program_info['module_name']}.Helper")
        module = getattr(importlib.import_module("comtypes.gen"), self.program_info["module_name"])
        self.module = module
        self.helper = helper.QueryInterface(module.cHelper)

    def get_object(self):
        return self.helper.GetObject(self.program_info["progid"])

    def get_object_process(self, pid: int):
        return self.helper.GetObjectProcess(self.program_info["progid"], pid)

    def create_object(self, exe_path: str):
        return self.helper.CreateObject(exe_path)

    def create_object_progid(self):
        return self.helper.CreateObjectProgID(self.program_info["progid"])

    def get_sap_model(self, csi_object):
        return csi_object.SapModel


def _build_backend(program: str, backend: str, dll_path: Optional[str] = None):
    backend = validate_backend(backend)
    if backend == "dotnet":
        return _DotNetBackend(program, dll_path=dll_path)
    if backend == "comtypes":
        return _ComtypesBackend(program)

    errors = []
    try:
        return _DotNetBackend(program, dll_path=dll_path)
    except Exception as exc:
        errors.append(f".NET: {exc}")

    try:
        return _ComtypesBackend(program)
    except Exception as exc:
        errors.append(f"comtypes: {exc}")

    raise RuntimeError(
        "No se pudo inicializar ningún backend CSI. "
        + " | ".join(errors)
    )


def get_paths(program="ETABS", backend="auto"):
    """
    Retorna los archivos abiertos por las instancias activas del programa.

    Usa el backend indicado para adjuntarse a cada proceso y leer su modelo activo.
    """
    program = validate_programs(program)
    connector = _build_backend(program, backend)
    pids = get__pids(program=program)
    paths = {}
    for pid in pids:
        try:
            csi_object = connector.get_object_process(pid)
            if csi_object is None:
                continue
            sap_model = connector.get_sap_model(csi_object)
            paths[pid] = sap_model.GetModelFilename()
        except Exception:
            continue
    return paths


def get_available_backends():
    """Retorna los backends de conexión soportados por la librería."""
    return ["dotnet", "comtypes"]


class CSIHandler(DataExtractor, ModelBuilder):
    """
    Punto de entrada principal para conectar y operar sobre modelos CSI.

    Combina la capa de conexión con las utilidades de extracción y modelamiento.
    """
    def __init__(self, program="ETABS", units=u.csi_units, backend="auto", dll_path=None):
        self.program = validate_programs(program)
        self.model = None
        self.object = None
        self.file_path = None
        self.file_name = None
        self.units = units
        self.is_connected = False
        self.requested_backend = validate_backend(backend)
        self.backend = None
        self.dll_path = dll_path
        self.connector = _build_backend(self.program, self.requested_backend, dll_path=self.dll_path)
        self.backend = self.connector.name
        self.helper = self.connector.helper
        self.api_module = getattr(self.connector, "module", None)
        super().__init__()

    def _bind_model(self):
        self.model = self.connector.get_sap_model(self.object)
        self.file_path = self.model.GetModelFilename()
        self.file_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        self.set_units()
        self.is_connected = True

    def connect_open_instance(self, instance_position=None):
        """
        Conecta con una instancia abierta del programa.

        Si ``instance_position`` es ``None``, usa la instancia activa; si es entero,
        usa la posición correspondiente dentro de los procesos detectados.
        """
        if instance_position is None:
            self.object = self.connector.get_object()
        elif isinstance(instance_position, int):
            pids = get__pids(self.program)
            self.object = self.connector.get_object_process(pids[instance_position])
        else:
            raise TypeError(f"instance_position no puede ser {type(instance_position).__name__}")

        if self.object is None:
            raise ConnectionError(f"No hay instancia de {self.program} abierta")

        self._bind_model()
        print(f"Conectado a {self.file_name} usando backend {self.backend}")
        return True

    def open_and_connect(self, file_path):
        """
        Abre un archivo de modelo en una nueva instancia y se conecta a él.

        Intenta usar el backend configurado para crear la instancia del programa.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no existe: {file_path}")

        exe_path = _resolve_exe_path(self.program)
        if self.backend == "dotnet" and exe_path:
            self.object = self.connector.create_object(exe_path)
        else:
            self.object = self.connector.create_object_progid()

        self.object.ApplicationStart()
        self.model = self.connector.get_sap_model(self.object)
        self.model.File.OpenFile(file_path)
        self.file_path = file_path
        self.file_name = os.path.basename(self.file_path)
        self.set_units()
        self.is_connected = True
        print(f"Conectado a {self.file_name} usando backend {self.backend}")
        return True

    def open_empty_instance(self, units=None):
        """
        Abre una instancia nueva del programa con un modelo en blanco.

        Si se indican unidades, las aplica después de inicializar el modelo.
        """
        exe_path = _resolve_exe_path(self.program)
        if self.backend == "dotnet" and exe_path:
            self.object = self.connector.create_object(exe_path)
        else:
            self.object = self.connector.create_object_progid()

        self.object.ApplicationStart()
        self.model = self.connector.get_sap_model(self.object)
        self.model.InitializeNewModel()
        self.model.File.NewBlank()
        self.file_path = ""
        self.file_name = "Untitled"

        if units:
            self.units = units
        self.set_units()

        self.is_connected = True
        print(f"Nueva instancia de {self.program} abierta usando backend {self.backend}")
        return True

    def save(self, model_path):
        """Guarda el modelo actual en la ruta indicada."""
        self.model.File.Save(model_path)
        return model_path

    def close(self):
        """
        Cierra la aplicación CSI conectada y limpia el estado del handler.

        Si no hay una instancia conectada, no hace nada.
        """
        if self.object is None:
            return True
        self.object.ApplicationExit(True)
        self.object = None
        self.model = None
        self.is_connected = False
        print(f"{self.file_name} cerrado")
        return True

    def refresh_view(self):
        """Actualiza la vista del modelo en la aplicación CSI."""
        self.model.View.RefreshView()

    def set_units(self):
        """Establece las unidades activas del modelo según ``self.units``."""
        self.model.SetPresentUnits(eUnits[self.units])


if __name__ == "__main__":
    import time

    etabs_model = CSIHandler("Etabs")
    etabs_model.connect_open_instance()
    to = time.time()
    print(etabs_model.get_modal_data())
    print(time.time() - to)
