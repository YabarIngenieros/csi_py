# CSI Python Library

Biblioteca Python para automatizar ETABS, SAP2000 y SAFE. Ahora usa `.NET` por defecto mediante `pythonnet`, y mantiene `comtypes` como respaldo.

## Caracteristicas

- Conexion a instancias abiertas de ETABS, SAP2000 y SAFE
- Backend `.NET` por defecto con carga dinamica de `ETABSv1.dll`, `SAP2000v1.dll` o `SAFEv1.dll`
- Respaldo automatico o explicito con `comtypes`
- Extraccion de datos del modelo
- Construccion programatica de modelos
- Gestion de multiples instancias y unidades

## Requisitos

- Windows
- Python 3.7+
- ETABS, SAP2000 o SAFE instalado

## Instalacion

```bash
pip install -e .
```

O manualmente:

```bash
pip install pythonnet comtypes pandas numpy psutil
```

## Uso rapido

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS")
model.connect_open_instance()
```

Forzar backend:

```python
model = CSIHandler(program="ETABS", backend="dotnet")
model = CSIHandler(program="ETABS", backend="comtypes")
```

Abrir un archivo:

```python
model = CSIHandler(program="ETABS")
model.open_and_connect(r"C:\Proyectos\MiModelo.EDB")
```

Crear un modelo vacio:

```python
model = CSIHandler(program="ETABS")
model.open_empty_instance(units="kN_m_C")
```

## Backends

- `dotnet`: backend preferido. Carga la DLL del programa CSI instalado y usa `pythonnet`.
- `comtypes`: backend de compatibilidad.
- `auto`: intenta `.NET` primero y si falla usa `comtypes`.

## Utilidades

```python
from csi_py import get__pids, get_paths, get_available_backends

pids = get__pids("ETABS")
paths = get_paths("ETABS")
backends = get_available_backends()
```

## Programas soportados

- ETABS
- SAP2000
- SAFE
