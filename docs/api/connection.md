# Conexion y utilidades

Esta seccion agrupa la entrada al modelo, la resolucion de backend y las funciones publicas expuestas desde el paquete.

## Funciones del paquete

### `get__pids(program="ETABS")`

Retorna los PID de las instancias activas del programa indicado.

```python
from csi_py import get__pids

pids = get__pids("ETABS")
```

Uso:

- `program` acepta `ETABS`, `SAP2000`, `SAFE` y alias `SAP`
- el filtro se hace por nombre de ejecutable CSI

### `get_paths(program="ETABS", backend="auto")`

Retorna un diccionario `{pid: ruta_modelo}` para las instancias activas del programa.

```python
from csi_py import get_paths

paths = get_paths("ETABS")
```

Notas:

- usa el backend solicitado para adjuntarse a cada proceso
- si una instancia no expone modelo activo, puede quedar fuera del resultado

### `validate_programs(program)`

Normaliza el nombre del programa CSI.

```python
from csi_py import validate_programs

program = validate_programs("sap")
```

Retorna:

- `ETABS`
- `SAP2000`
- `SAFE`

### `get_available_backends()`

Retorna los backends soportados por la libreria.

```python
from csi_py import get_available_backends

backends = get_available_backends()
```

### `get_supported_programs()`, `get_default_backend()`, `get_available_units()`, `get_version()`

Helpers informativos del paquete.

```python
from csi_py import (
    get_supported_programs,
    get_default_backend,
    get_available_units,
)

programs = get_supported_programs()
backend = get_default_backend()
units = get_available_units()
```

## Punto de entrada

La clase de trabajo es `CSIHandler`.

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
```

`CSIHandler` hereda de:

- `Handler`: conexion y operaciones base
- `DataExtractor`: lectura y resultados
- `ModelBuilder`: construccion y edicion

## Conexion al modelo

### `connect_open_instance(instance_position=None)`

Se adjunta a una instancia ya abierta.

```python
model.connect_open_instance()
model.connect_open_instance(instance_position=0)
```

Uso:

- `None`: usa la instancia activa
- `int`: usa la posicion dentro de los procesos detectados

Errores esperables:

- `TypeError` si `instance_position` no es `None` ni entero
- `ConnectionError` si no hay instancia disponible

### `open_and_connect(file_path)`

Abre un archivo de modelo en una instancia nueva y conecta el handler.

```python
model.open_and_connect(r"C:\Modelos\edificio.edb")
```

Errores esperables:

- `FileNotFoundError` si la ruta no existe

Notas:

- intenta usar el backend configurado para crear la instancia
- deja la instancia en estado conectado

### `open_empty_instance(units=None)`

Crea una instancia nueva con un modelo en blanco.

```python
model.open_empty_instance(units="kN_m_C")
```

Uso:

- si `units` se entrega, se aplica despues de inicializar el modelo
- si no se entrega, usa `self.units`

## Operaciones base

### `save(model_path)`

Guarda el modelo actual en la ruta indicada.

```python
model.save(r"C:\Modelos\salida.edb")
```

### `close()`

Cierra la aplicacion CSI conectada y limpia el estado del handler.

```python
model.close()
```

### `refresh_view()`

Fuerza el refresco de la vista del modelo en la aplicacion CSI.

```python
model.refresh_view()
```

### `set_units()`

Aplica `self.units` como unidades activas del modelo.

```python
model.units = "kN_m_C"
model.set_units()
```

Notas:

- normalmente se llama implicito al abrir o conectar un modelo
- existe como operacion manual cuando se cambia `self.units`

## Flujo minimo recomendado

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.open_and_connect(r"C:\Modelos\edificio.edb")

model.refresh_view()
model.save(r"C:\Modelos\edificio_editado.edb")
model.close()
```

## Notas operativas

- `backend` acepta `auto`, `dotnet` y `comtypes`
- `auto` intenta `.NET` primero y luego `comtypes`
- la clase publica de uso diario es `CSIHandler`
