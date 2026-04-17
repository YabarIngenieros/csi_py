# csi_py

Biblioteca Python para automatizar software CSI en Windows: ETABS, SAP2000 y SAFE.

La libreria expone una sola API de trabajo (`CSIHandler`) que combina:

- conexion a instancias abiertas o nuevas,
- compatibilidad con backend `.NET` (`pythonnet`) y respaldo `comtypes`,
- extraccion de tablas, geometria, cargas y resultados,
- construccion programatica de materiales, secciones, objetos y cargas.

## Enfoque de documentacion

La documentacion del proyecto ahora sigue un enfoque spec driven:

- la fuente de verdad es la [especificacion](docs/SPEC.md)
- la [arquitectura](docs/ARQUITECTURA.md) explica como la implementacion cumple la spec
- el [indice principal](docs/index.md) organiza la documentacion para consulta y publicacion
- el [indice de API](docs/api/index.md) agrupa la referencia por responsabilidades

## Estado del proyecto

El paquete esta en una etapa temprana pero ya tiene una superficie de API amplia. La capa principal esta organizada asi:

- `handler.py`: conexion, seleccion de backend y operaciones base sobre el modelo.
- `extractor.py`: lectura de tablas, geometria, cargas, modos y resultados.
- `builder.py`: creacion y edicion de materiales, secciones, objetos y cargas.
- `api_helpers.py`: adaptacion entre salidas `.NET` y `comtypes`.
- `constants.py`: enums, unidades y errores comunes.

La clase publica para uso diario es `CSIHandler`, que hereda de `ModelBuilder`, `DataExtractor` y `Handler`.

## Requisitos

- Windows
- Python 3.7+
- ETABS, SAP2000 o SAFE instalado
- Acceso a la API del producto CSI correspondiente

## Instalacion

Instalacion editable durante desarrollo:

```bash
pip install -e .
```

Instalacion directa de dependencias:

```bash
pip install pythonnet comtypes pandas numpy psutil
```

## Inicio rapido

Conectar a una instancia abierta de ETABS:

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS")
model.connect_open_instance()
```

Abrir un archivo en una instancia nueva:

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS")
model.open_and_connect(r"C:\Proyectos\MiModelo.EDB")
```

Abrirlo con selector de archivos:

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS")
model.open_and_connect()
```

Crear un modelo vacio:

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS")
model.open_empty_instance(units="kN_m_C")
```

Forzar backend:

```python
CSIHandler(program="ETABS", backend="dotnet")
CSIHandler(program="ETABS", backend="comtypes")
CSIHandler(program="ETABS", backend="auto")
```

## API publica

### Conexion y utilidades

Funciones y clases publicas exportadas desde `__init__.py`:

- `CSIHandler`
- `DataExtractor`
- `ModelBuilder`
- `get__pids(program)`
- `get_paths(program, backend="auto")`
- `validate_programs(program)`
- `get_available_backends()`
- `get_supported_programs()`
- `get_default_backend()`
- `get_available_units()`

### Operaciones base

`CSIHandler` incluye estos metodos base:

- `connect_open_instance(instance_position=None)`
- `open_and_connect(file_path=None)`
- `open_empty_instance(units=None)`
- `save(model_path)`
- `close()`
- `refresh_view()`
- `set_units()`

### Extraccion de datos

Grupos principales disponibles en `extractor.py`:

- tablas: `available_tables`, `editable_tables`, `get_table()`, `tabular_data`
- cargas: `cases`, `combos`, `get_combo_cases()`, `get_load_cases_info()`, `get_combo_breakdown()`
- materiales: `material_list`, `get_material_properties()`
- puntos: `point_list`, `get_point_coordinates()`, `get_point_restraints()`, `get_point_reactions()`
- grids: `grid_system_names`, `grid_lines`, `get_grid_system()`
- frames: `frame_list`, `frame_sections_data`, `get_frame_forces()`, `get_beams_connectivity()`
- areas: `area_list`, `area_geometry`, `get_area_forces()`
- muros y pisos: `wall_list`, `floor_list`, `pier_forces`, `story_forces`, `story_drifts`
- analisis modal: `get_modal_data()`, `get_modal_periods()`, `get_modal_summary()`, `get_modal_displacements()`, `get_modal_shape()`
- exportes resumidos: `get_model_geometry()`, `get_geometry_summary()`, `export_geometry_to_dict()`, `get_load_cases_summary()`, `export_load_cases_to_dict()`

### Construccion y edicion

Grupos principales disponibles en `builder.py`:

- tablas editables: `get_editing_table()`, `set_table()`, `export_tabular_data()`, `export_tables_batch()`
- materiales: `add_material()`, `add_concrete_material()`, `add_steel_material()`, `add_rebar_material()`
- secciones frame: `add_rectangle_section()`, `add_i_section()`, `add_tube_section()`, `add_frame_section()`
- secciones area: `add_slab_section()`, `add_ribbed_slab_section()`, `add_waffle_slab_section()`, `add_wall_section()`, `add_area_section()`
- objetos: `add_point()`, `set_point_restraint()`, `add_frame()`, `add_area_obj()`
- cargas: `add_load_pattern()`, `add_point_load()`, `add_frame_distributed_load()`, `add_area_uniform_load()`
- combinaciones: `add_load_combo()`, `set_combo_case()`

## Ejemplo de modelado

```python
from csi_py import CSIHandler, u

etabs = CSIHandler(program="ETABS")
etabs.open_empty_instance(units="kN_m_C")

etabs.add_concrete_material("CONC25", fc=25 * u.MPa)
etabs.add_rectangle_section("COL40x40", "CONC25", t3=0.40, t2=0.40)

p1 = etabs.add_point(0, 0, 0)
p2 = etabs.add_point(0, 0, 3)
etabs.set_point_restraint(p1, True, True, True, True, True, True)
etabs.add_frame(p1, p2, "COL40x40")

etabs.add_load_pattern("DEAD", pattern_type=1)
etabs.save(r"C:\Temp\modelo.edb")
```

## Ejemplo de extraccion

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS")
model.connect_open_instance()

periods = model.get_modal_periods()
grids = model.get_grid_system()
geometry = model.get_model_geometry()
loads = model.get_load_cases_info()
```

## Contratos principales

La spec actual fija estos contratos de alto nivel:

- `program` acepta `ETABS`, `SAP2000`, `SAFE` y alias `SAP`
- `backend` acepta `auto`, `dotnet` y `comtypes`
- `CSIHandler` tiene un estado no conectado al inicializar y pasa a conectado al adjuntarse o abrir un modelo
- las lecturas tabulares retornan `pandas.DataFrame`
- las operaciones de edicion tabular fallan si CSI reporta errores fatales o de edicion
- la capa de compatibilidad intenta mantener una firma Python uniforme entre `.NET` y `comtypes`

## Backends

`csi_py` usa una capa de compatibilidad para que la API de alto nivel sea practicamente la misma con ambos backends:

- `dotnet`: opcion preferida. Carga `ETABSv1.dll`, `SAP2000v1.dll` o `SAFEv1.dll` mediante `pythonnet`.
- `comtypes`: opcion de compatibilidad para entornos donde `.NET` no esta disponible o falla.
- `auto`: intenta `.NET` primero y cae a `comtypes` si no puede inicializarlo.

La logica de adaptacion esta en [`api_helpers.py`](api_helpers.py).

## Documentacion incluida

- [Indice principal](docs/index.md)
- [Indice de API](docs/api/index.md)
- [Especificacion](docs/SPEC.md)
- [Guia de uso derivada](docs/USO_API.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Ejemplo de builder](examples/ejemplo_builder.py)
- [Ejemplo de chequeo de extractor](examples/ejemplo_error_cargas.py)

## Limitaciones actuales

- El proyecto esta orientado a Windows.
- La mayor parte de la funcionalidad requiere una instalacion real de ETABS, SAP2000 o SAFE.
- No hay aun una suite automatizada de pruebas para la API completa.
- Varias rutas del proyecto siguen asumiendo ETABS como caso principal, aunque la capa de conexion soporta tambien SAP2000 y SAFE.

## Desarrollo

Archivos que conviene leer primero:

- [`handler.py`](handler.py)
- [`extractor.py`](extractor.py)
- [`builder.py`](builder.py)
- [`api_helpers.py`](api_helpers.py)

Para cambios de API, la regla recomendada es:

1. cambiar primero [`docs/SPEC.md`](docs/SPEC.md)
2. ajustar despues el codigo
3. actualizar la documentacion derivada
