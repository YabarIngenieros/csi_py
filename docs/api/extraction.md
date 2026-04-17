# Extraccion y resultados

Esta seccion documenta la API publica de lectura: listas cacheadas, extraccion de tablas de resultados, consultas geometricas y exportes resumidos.

## Cargas y combinaciones

### Propiedades relacionadas

- `cases`
- `combos`
- `cases_and_combos`
- `design_cases`
- `design_cases_and_combos`
- `seismic_cases`
- `seismic_combos`
- `seismic_cases_and_combos`
- `gravity_cases`
- `gravity_combos`
- `gravity_cases_and_combos`

```python
cases = model.cases
combos = model.combos
seismic = model.seismic_cases_and_combos
```

Notas:

- estas propiedades suelen cachearse
- varias se derivan de tipos de caso o del contenido de combinaciones

### `get_combo_cases(combo_name)`

Retorna los casos base contenidos en una combinacion, resolviendo combinaciones anidadas.

```python
base_cases = model.get_combo_cases("COMB_SERV")
```

### `select_cases_and_combos(cases_and_combos)`

Selecciona casos y combinaciones para la salida tabular activa.

```python
model.select_cases_and_combos(["DEAD", "LIVE", "SX"])
```

Uso:

- afecta tablas de resultados extraidas despues
- es util cuando se quiere controlar el conjunto activo antes de `get_table()`

### `get_response_spectrum(spectrum_names="all")`

Lee funciones de espectro de respuesta desde tablas editables.

```python
all_spectra = model.get_response_spectrum()
sx = model.get_response_spectrum("SPEC_X")
```

### `get_load_cases_info(include_cases=True, include_combos=True, include_patterns=True, include_details=True)`

Retorna un diccionario con `DataFrame` de patrones, casos, combinaciones, detalle interno y resumen.

```python
info = model.get_load_cases_info()
patterns = info["load_patterns"]
combo_details = info["combo_details"]
```

### `get_load_cases_summary()`

Retorna un `dict` resumen con conteos de patrones, casos y combinaciones.

```python
summary = model.get_load_cases_summary()
```

### `export_load_cases_to_dict(simplified=False)`

Exporta la estructura de cargas a un diccionario serializable.

```python
payload = model.export_load_cases_to_dict(simplified=True)
```

### `get_combo_breakdown(combo_name)`

Descompone una combinacion en casos base, acumulando factores.

```python
breakdown = model.get_combo_breakdown("COMB_U1")
```

## Materiales

### Propiedades relacionadas

- `material_list`
- `material_properties`

```python
names = model.material_list
props = model.material_properties
```

### `get_material_properties(material_name)`

Consulta directamente la API de propiedades del material para uno o varios nombres.

```python
df = model.get_material_properties(["CONC25", "A36"])
```

Retorno:

- `DataFrame` con tipo de material, simetria y constantes principales

Es un metodo poco abstraido, cercano a los getters nativos de CSI.

## Puntos

### Propiedades relacionadas

- `point_list`
- `base_points`
- `points_coordinates`
- `points_restraints`
- `points_reactions`

```python
points = model.point_list
coords = model.points_coordinates
```

### `get_point_coordinates(point_names)`

Retorna coordenadas cartesianas de uno o varios puntos.

```python
coords = model.get_point_coordinates(points[:5])
```

### `get_point_restraints(point_names)`

Retorna restricciones nodales.

```python
restraints = model.get_point_restraints(["1", "2", "3"])
```

### `get_point_reactions(point_names=None, cases_and_combos=None)`

Extrae reacciones nodales desde resultados.

```python
reactions = model.get_point_reactions(point_names=model.base_points)
```

Notas:

- si no se filtra, usa puntos y casos de diseño por defecto
- prepara la seleccion de resultados antes de consultar la API

### `get_selected_points()`

Retorna los puntos seleccionados actualmente en la interfaz CSI.

```python
selected = model.get_selected_points()
```

## Grids

### Propiedades relacionadas

- `grid_system_names`
- `grid_lines`

```python
names = model.grid_system_names
lines = model.grid_lines
```

### `get_grid_system(grid_system_name=None)`

Retorna líneas de grid como `DataFrame`.

```python
all_grids = model.get_grid_system()
g1 = model.get_grid_system("G1")
```

Retorno:

- cuando `grid_system_name` es `None`, devuelve todas las líneas de todos los sistemas
- cuando se indica un nombre, filtra por ese sistema

Columnas esperadas:

- `GridSystem`
- `Axis`
- `GridLineID`
- `Ordinate`
- `Visible`
- `BubbleLoc`
- `Xo`
- `Yo`
- `RZ`
- `GridSysType`

Notas:

- usa como fuente principal la tabla `Grid Definitions - Grid Lines`
- mantiene una ruta de respaldo con la API nativa cuando la tabla no está disponible
- es la base prevista para resolver pertenencia de vigas a grids

## Frames

### Propiedades relacionadas

- `frame_sections_list`
- `frame_sections_data`
- `frame_list`
- `frame_label_names`
- `frames_properties`
- `frames_connectivity`
- `frames_forces`
- `beams_connectivity`
- `columns_connectivity`
- `label_beams`
- `label_columns`

```python
frames = model.frame_list
sections = model.frame_sections_data
```

### `get_frame_section_properties(section_name)`

Lee propiedades seccionales calculadas para una seccion.

```python
props = model.get_frame_section_properties("COL40x40")
```

Retorno:

- `dict` con area, inercia, torsion y modulos resistentes

### `get_frame_section_dimensions(get_properties=False)`

Retorna dimensiones de todas las secciones frame.

```python
df = model.get_frame_section_dimensions(get_properties=True)
```

Uso:

- `False`: solo geometria y tipo de seccion
- `True`: agrega propiedades calculadas

### `get_frame_section(frame_name)`

Retorna la seccion asignada a un frame.

```python
section = model.get_frame_section("45")
```

### `get_frame_points(frame_name)`

Retorna puntos inicial y final.

```python
ij = model.get_frame_points("45")
```

### `get_frame_coordinates(frame_name)`

Retorna coordenadas de los extremos.

```python
coords = model.get_frame_coordinates("45")
```

### `get_frame_length(frame_name)`

Calcula longitud geometrica.

```python
L = model.get_frame_length("45")
```

### `get_frame_forces(frame_name=None, cases_and_combos=None)`

Extrae fuerzas internas de frames usando la API de resultados.

```python
forces = model.get_frame_forces(frame_name=["45", "46"])
```

Es un metodo poco abstraido porque opera con la semantica directa de resultados CSI.

### `get_beam_forces(beams_label=None, cases_and_combos=None)`

Extrae la tabla `Element Forces - Beams`, filtrando por etiqueta de viga.

```python
beam_forces = model.get_beam_forces(beams_label=["B1", "B2"])
```

### `get_frames_connectivity(frame_type=None, labels=None, tol=1e-6)`

Retorna una vista conjunta de conectividad para vigas y columnas.

```python
all_frames = model.get_frames_connectivity()
beams = model.get_frames_connectivity(frame_type="beam", labels=["B1", "B2"])
columns = model.get_frames_connectivity(frame_type="column", labels=["C1"])
```

Columnas:

- `Frame`
- `FrameType`
- `Label`
- `Story`
- `Section`
- `point_i`
- `point_j`
- `Grid`
- `GridX`
- `GridY`
- `General`

Notas:

- `frame_type` acepta `beam`, `column` o `None`
- para vigas, la pertenencia principal se reporta en `Grid`
- para columnas, la pertenencia se separa en `GridX`, `GridY` y `General`

### `frames_connectivity`

Propiedad cacheada equivalente a `get_frames_connectivity()`.

```python
df = model.frames_connectivity
```

Aliases compatibles:

- `get_frame_connectivity(...)`
- `frame_connectivity`

### `get_beams_connectivity(beams_label=None, tol=1e-6)`

Retorna conectividad de vigas y su pertenencia a grid como `DataFrame`.

```python
all_beams = model.get_beams_connectivity()
subset = model.get_beams_connectivity(["B1", "B2"])
```

Columnas:

- `Beam`
- `Label`
- `Story`
- `Section`
- `point_i`
- `point_j`
- `Grid`

Notas:

- una viga pertenece a un grid solo si ambos puntos extremos caen sobre la misma línea
- si no existe un grid común, `Grid` se devuelve como cadena vacía
- `beams_label` filtra por label de viga, no por nombre interno del frame
- la pertenencia usa `grid_lines` y soporta líneas cartesianas y líneas generales cuando la tabla trae geometría

### `beams_connectivity`

Propiedad cacheada equivalente a `get_beams_connectivity()`.

```python
df = model.beams_connectivity
```

Aliases compatibles:

- `get_beam_connectivity(...)`
- `beam_connectivity`

### `get_columns_connectivity(columns_label=None, tol=1e-6)`

Retorna conectividad de columnas y su pertenencia a grids como `DataFrame`.

```python
all_columns = model.get_columns_connectivity()
subset = model.get_columns_connectivity(["C1", "C2"])
```

Columnas:

- `Column`
- `Label`
- `Story`
- `Section`
- `point_i`
- `point_j`
- `GridX`
- `GridY`
- `General`

Notas:

- `columns_label` filtra por label de columna
- `GridX` y `GridY` corresponden a líneas cartesianas
- `General` agrupa líneas no cartesianas o generales
- si una columna coincide con más de una línea de una misma categoría, los IDs se concatenan con `|`

### `columns_connectivity`

Propiedad cacheada equivalente a `get_columns_connectivity()`.

```python
df = model.columns_connectivity
```

Aliases compatibles:

- `get_column_connectivity(...)`
- `column_connectivity`

## Areas, losas, muros y decks

### Propiedades relacionadas

- `area_section_list`
- `area_list`
- `area_geometry`
- `area_forces`
- `slab_sections_data`
- `deck_sections_data`
- `wall_sections_data`
- `floor_sections_list`
- `floor_list`
- `wall_list`
- `pier_list`

```python
area_names = model.area_list
areas = model.area_geometry
walls = model.wall_sections_data
```

### `map_area_properties()`

Clasifica las secciones de area y llena caches de muros, losas y decks.

```python
model.map_area_properties()
walls = model.wall_sections_data
```

Notas:

- internamente usa utilidades como `map_wall_properties`, `map_slab_properties` y `map_deck_properties`
- esas utilidades existen como metodos publicos pero su uso normal es indirecto

### `get_area_section(area_name)`

Retorna la seccion asignada a un area.

```python
section = model.get_area_section("A12")
```

### `get_area_points(area_name)`

Retorna los puntos del contorno.

```python
pts = model.get_area_points("A12")
```

### `get_area_forces(area_name=None, cases_and_combos=None)`

Extrae fuerzas internas de shell en areas.

```python
forces = model.get_area_forces(area_name=["A12", "A13"])
```

Es un metodo poco abstraido porque trabaja directamente con la API de resultados de shell.

## Tiras, piers, stories y suelo

### Strips

#### `strip_list`

Propiedad que deduce strips desde la tabla `Strip Forces`.

```python
strips = model.strip_list
```

#### `strip_loads`

Alias cacheado de `extract_strip_loads()`.

```python
strip_forces = model.strip_loads
```

#### `extract_strip_loads(strips=None, cases_and_combos=None)`

Extrae la tabla `Strip Forces`, limpia columnas y permite filtrar.

```python
strip_forces = model.extract_strip_loads()
```

### Piers

#### `get_pier_forces(piers=None, stories=None, cases_and_combos=None)`

Extrae fuerzas globales reportadas para piers.

```python
pier_forces = model.get_pier_forces(piers=["P1", "P2"])
```

#### `pier_forces`

Alias directo de `get_pier_forces()`.

```python
pier_forces = model.pier_forces
```

#### `get_pier_displacements(piers=None, cases_and_combos=None)`

Metodo semiestructurado: arma desplazamientos de piers cruzando varias tablas CSI.

```python
pier_disp = model.get_pier_displacements()
```

Es uno de los metodos menos abstraidos del extractor.

### Stories

#### `stories`

Lista de niveles del modelo.

```python
stories = model.stories
```

#### `get_story_height(story)`

Retorna altura de un nivel.

```python
h = model.get_story_height("Story2")
```

#### `get_story_forces(cases_and_combos=None)`

Extrae la tabla `Story Forces`.

```python
story_forces = model.get_story_forces()
```

#### `story_forces`

Alias directo de `get_story_forces()`.

```python
story_forces = model.story_forces
```

#### `get_story_displacements(cases_and_combos=None)`

Extrae `Story Max Over Avg Displacements`.

```python
story_disp = model.get_story_displacements()
```

#### `story_displacements`

Alias directo de `get_story_displacements()`.

```python
story_disp = model.story_displacements
```

#### `get_story_drifts(cases_and_combos=None)`

Extrae `Diaphragm Max Over Avg Drifts`.

```python
story_drifts = model.get_story_drifts()
```

#### `story_drifts`

Alias directo de `get_story_drifts()`.

```python
story_drifts = model.story_drifts
```

### Suelo

#### `extract_soil_pressures(cases_and_combos=None)`

Extrae la tabla `Soil Pressures`.

```python
soil = model.extract_soil_pressures()
```

#### `soil_pressures`

Alias cacheado de `extract_soil_pressures()`.

```python
soil = model.soil_pressures
```

## Resultados modales

### Propiedades relacionadas

- `modal_data`
- `modal_cases`

```python
modal_cases = model.modal_cases
modal = model.modal_data
```

### `get_modal_data(cases=None)`

Extrae informacion modal tabular consolidada.

```python
modal = model.get_modal_data()
```

### `get_modal_periods(case_name=None, num_modes=None, as_dict=False)`

Retorna periodos modales.

```python
periods = model.get_modal_periods()
first5 = model.get_modal_periods(num_modes=5)
```

### `get_modal_summary(case_name=None, num_modes=None)`

Devuelve un resumen de participacion modal y periodos.

```python
summary = model.get_modal_summary()
```

### `get_modal_displacements(case_name=None, point_names=None, mode_number=None, item_type=0)`

Consulta desplazamientos modales puntuales con semantica cercana a CSI.

```python
disp = model.get_modal_displacements(mode_number=1, point_names=model.base_points)
```

Parametros relevantes:

- `case_name`: caso modal; si no se da, usa el primero
- `point_names`: puntos a consultar; si no se da, usa todos
- `mode_number`: filtra por modo
- `item_type`: pasa directo al tipo de item de la API CSI

### `get_modal_shape(case_name=None, mode_number=1, direction="3D", normalize=True)`

Construye una forma modal para visualizacion a partir de desplazamientos y coordenadas.

```python
shape = model.get_modal_shape(mode_number=1, direction="horizontal")
```

## Geometria global y exportes

### `get_model_geometry(include_frames=True, include_areas=True, include_points=True, include_sections=True, include_connectivity=False)`

Extrae la geometria principal del modelo en un diccionario.

```python
geom = model.get_model_geometry()
points = geom["points"]
frames = geom["frames"]

geom_conn = model.get_model_geometry(include_connectivity=True)
frames_conn = geom_conn["frames"]
```

Notas:

- si `include_connectivity=True`, `geom["frames"]` agrega columnas de conectividad:
  `FrameType`, `Grid`, `GridX`, `GridY`, `General`
- la conectividad se toma de `get_frames_connectivity()`

### `get_geometry_summary()`

Retorna un resumen escalar del modelo: conteos, dimensiones y materiales.

```python
summary = model.get_geometry_summary()
```

### `export_geometry_to_dict(simplified=False)`

Exporta la geometria a un diccionario serializable.

```python
payload = model.export_geometry_to_dict(simplified=True)
```

## Metodos menos abstraidos

Los puntos mas cercanos a la semantica de CSI en esta seccion son:

- `get_material_properties`
- `get_frame_forces`
- `get_area_forces`
- `get_modal_displacements`
- `get_pier_displacements`

En ellos conviene revisar:

- nombres de tablas y casos activos
- filtros por puntos, frames o areas
- dependencias con resultados ya corridos
