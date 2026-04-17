# Metodos Poco Abstraidos

Esta pagina agrupa los metodos publicos mas cercanos a la semantica nativa de CSI.

No son necesariamente dificiles de usar, pero exponen nombres de tabla, codigos, enums, filtros de salida o estructuras que siguen muy de cerca a ETABS, SAP2000 o SAFE.

Conviene usarlos cuando:

- ya conoce la tabla o el getter CSI que quiere consultar
- necesita control fino de filtros, codigos o nombres exactos
- quiere construir utilidades propias por encima de la API de `csi_py`

Conviene revisar antes:

- nombres exactos de tablas y casos
- tipos numericos o enums CSI
- si el modelo ya fue analizado
- si la propiedad consultada queda cacheada

## Tablas y configuracion de salida

### `set_envelopes_for_dysplay(set_envelopes=True)`

Configura opciones internas de visualizacion tabular para combinaciones, casos multistep y analisis no lineales.

Es un wrapper casi directo de opciones de `DatabaseTables`.

### `get_table(table_name, set_envelopes=True, runned=False)`

Lee una tabla CSI por nombre exacto y la retorna como `DataFrame`.

Aspectos a cuidar:

- `table_name` debe coincidir con el nombre CSI
- puede correr el analisis si la tabla necesita resultados
- el contenido depende del estado de seleccion de casos y combinaciones

### `get_editing_table(table_name)`

Lee una tabla editable y devuelve `(version, dataframe)`.

La `version` es parte del contrato tabular CSI y debe conservarse al reimportar.

### `apply_edited_table()`

Aplica cambios tabulares pendientes en CSI.

Debe usarse cuando se trabaja con tablas editables sin `apply=True`.

### `get_editable_table(name, columns)`

Retorna una tabla editable existente o una tabla vacia compatible para empezar a llenarla.

Es util para tablas opcionales o generadas sobre la marcha.

### `set_table(table_name, table, table_version=1, apply=True)`

Escribe un `DataFrame` en una tabla editable CSI.

Es poco abstraido porque conserva:

- el nombre exacto de la tabla
- la version de tabla
- el momento en que se aplican o no los cambios

### `export_tabular_data(tabular_data, table_names=None, apply=True)`

Exporta varias tablas editables desde un diccionario `{tabla: DataFrame}`.

Es un helper de lote, pero sigue trabajando con la estructura tabular nativa CSI.

### `export_tables_batch(tabular_data, table_groups=None)`

Exporta conjuntos de tablas por grupos.

Es util para cambios grandes donde conviene aislar grupos de importacion.

## Grids del modelo

### `set_grid_system(X, Y, spacing=True)`

Define la grilla cartesiana reescribiendo tablas CSI de grids.

Es poco abstraido porque opera directamente con:

- `Grid Definitions - General`
- `Grid Definitions - Grid Lines`

### `set_grid_sitem(X, Y, spacing=True)`

Alias retrocompatible de `set_grid_system`.

### `grid_system_names`

Lista los nombres de sistemas de grids detectados, principalmente desde tablas CSI.

### `grid_lines`

Retorna todas las lineas de grid normalizadas en un `DataFrame`.

### `get_grid_system(grid_system_name=None)`

Retorna lineas de grid como `DataFrame`.

Si no se indica nombre, devuelve todos los sistemas; si se indica, filtra por uno.

## Seleccion de cargas y espectros

### `select_cases_and_combos(cases_and_combos)`

Controla la seleccion activa de casos y combinaciones para consultas de resultados.

Es cercano a CSI porque modifica el estado de visualizacion del modelo.

### `get_response_spectrum(spectrum_names="all")`

Lee espectros desde tablas editables.

Es util cuando necesita el contenido tabular real, no solo una vista resumida.

### `get_combo_cases(combo_name)`

Descompone una combinacion en sus casos base.

Es semidirecto porque conserva la logica de `RespCombo.GetCaseList`.

### `get_combo_breakdown(combo_name)`

Desglosa recursivamente una combinacion acumulando factores.

Aunque agrega valor, sigue reflejando la estructura interna de combinaciones CSI.

## Materiales

### `get_material_properties(material_name)`

Consulta propiedades de material desde getters nativos CSI.

El retorno conserva tipos, simetria y constantes principales cercanas a la API.

### `add_material(material_name, material_type, E, U, A, mass_per_volume)`

Wrapper directo para material isotropico.

### `add_uniaxial_material(material_name, material_type, E, A, mass_per_volume)`

Wrapper directo para material uniaxial.

Ambos requieren conocer:

- `eMatType`
- unidades activas
- significado de `E`, `U`, `A` y densidad/masa segun CSI

## Puntos y reacciones

### `get_point_reactions(point_names=None, cases_and_combos=None)`

Lee reacciones nodales desde resultados CSI.

Es poco abstraido porque depende del estado de resultados y de la seleccion de casos.

### `add_point_load(point_name, load_pattern, Fx=0, Fy=0, Fz=0, Mx=0, My=0, Mz=0)`

Aplica una carga puntual usando el vector de seis componentes CSI.

## Frames y secciones frame

### `get_frame_section_properties(section_name)`

Retorna propiedades seccionales calculadas desde la API nativa.

### `get_frame_section_dimensions(get_properties=False)`

Resume dimensiones de secciones frame.

Cuando `get_properties=True`, agrega propiedades calculadas desde getters CSI.

### `get_frame_forces(frame_name=None, cases_and_combos=None)`

Lee fuerzas internas de frames mediante resultados nativos.

Es uno de los metodos mas cercanos a CSI en todo el paquete.

### `get_frames_connectivity(frame_type=None, labels=None, tol=1e-6)`

Construye una vista conjunta de conectividad de vigas y columnas.

Es un helper integrador, pero sigue muy cerca de CSI porque se apoya en:

- labels de frames
- puntos extremos
- coordenadas nodales
- definicion tabular de grids

### `frames_connectivity`

Version cacheada de `get_frames_connectivity()`.

Aliases:

- `get_frame_connectivity(...)`
- `frame_connectivity`

### `filter_frames_by_grid(grid=None, grid_x=None, grid_y=None, story=None, frame_type=None, labels=None, tol=1e-6)`

Filtra frames por eje, intersección de ejes y piso.

Es un helper de consulta construido sobre la conectividad ya resuelta, pero sigue cerca de la semantica CSI porque depende de:

- labels
- story
- grids tabulares
- conectividad de vigas y columnas

Aliases expresivos:

- `get_frames_on_grid(...)`
- `get_frames_at_intersection(...)`

### `get_beam_forces(beams_label=None, cases_and_combos=None)`

Lee la tabla `Element Forces - Beams`.

Es tabular y depende de nombres de label y casos activos.

### `get_beams_connectivity(beams_label=None, tol=1e-6)`

Resuelve la conectividad de vigas contra grids.

Aunque devuelve un `DataFrame` conveniente, sigue muy cerca de la semantica CSI porque depende de:

- labels de vigas derivados de `FrameObj.GetLabelNameList`
- puntos extremos del frame
- coordenadas nodales
- definicion de grids desde tablas CSI

El filtro principal se hace por `Label` de viga.

### `beams_connectivity`

Version cacheada de `get_beams_connectivity()`.

Aliases:

- `get_beam_connectivity(...)`
- `beam_connectivity`

### `get_columns_connectivity(columns_label=None, tol=1e-6)`

Resuelve la conectividad de columnas contra grids y separa la salida en:

- `GridX`
- `GridY`
- `General`

Sigue muy cerca de la semantica CSI porque depende de:

- labels de columnas derivados de `FrameObj.GetLabelNameList`
- puntos extremos del frame
- coordenadas nodales
- definicion tabular de grids

### `columns_connectivity`

Version cacheada de `get_columns_connectivity()`.

Aliases:

- `get_column_connectivity(...)`
- `column_connectivity`

### `add_frame_distributed_load(frame_name, load_pattern, direction, value, dist_type=1)`

Aplica carga distribuida conservando la semantica CSI de `direction` y `dist_type`.

### Metodos directos de seccion frame

Estos wrappers son casi directos y conservan la forma de CSI:

- `add_rectangle_section`
- `add_circle_section`
- `add_pipe_section`
- `add_tube_section`
- `add_i_section`
- `add_channel_section`
- `add_tee_section`
- `add_angle_section`
- `add_double_angle_section`
- `add_double_channel_section`
- `add_concrete_box_section`
- `add_concrete_tee_section`
- `add_concrete_L_section`
- `add_concrete_pipe_section`
- `add_concrete_cross_section`
- `add_plate_section`
- `add_rod_section`
- `add_cold_formed_c_section`
- `add_cold_formed_z_section`
- `add_cold_formed_hat_section`

### `add_frame_section(section_name, material_name, section_type, **kwargs)`

Unifica la creacion de secciones frame, pero sigue dependiendo de tipos y argumentos CSI por familia.

## Areas, shells, muros y decks

### `map_wall_properties(section, wall_dict)`

Interpreta una seccion de muro desde getters CSI y llena un diccionario acumulador.

### `map_slab_properties(section, slab_dict)`

Interpreta una seccion de losa.

### `map_deck_properties(section, deck_dict)`

Interpreta una seccion deck.

### `map_area_properties()`

Clasifica secciones de area y llena caches internas.

Es publico, pero su uso normal es como paso interno del extractor.

### `get_area_forces(area_name=None, cases_and_combos=None)`

Lee esfuerzos de shell desde resultados CSI.

### `add_area_uniform_load(area_name, load_pattern, value, direction=6)`

Aplica una carga uniforme de area conservando el codigo CSI de direccion.

### Metodos directos de seccion de area

Estos wrappers siguen casi sin traduccion la semantica CSI:

- `add_slab_section`
- `add_ribbed_slab_section`
- `add_waffle_slab_section`
- `add_wall_section`
- `add_deck_filled_section`
- `add_deck_unfilled_section`
- `add_deck_solid_slab_section`
- `add_shell_layer`

### `add_area_section(section_name, material_name, section_type, **kwargs)`

Dispatcher unificado para secciones de area.

Aunque mejora la API, los `kwargs` siguen siendo especificos de cada tipo CSI.

## Section Designer

### `add_tee_SD_sections(name, material, height, width, thick, apply=False)`

Construye secciones tipo tee mediante tablas de Section Designer.

### `apply_tee_sections(version_1=1, version_2=1)`

Aplica las tablas acumuladas para Section Designer.

### `add_line_bar_to_section(section_name, material, p1, p2, size, max_spacing, end_bars="Yes")`

Agrega barras a una seccion de Section Designer usando la tabla correspondiente.

Los argumentos geometricos siguen la estructura de la tabla CSI.

## Strips, piers, stories y suelo

### `strip_list`

Deduce strips desde la tabla `Strip Forces`.

### `extract_strip_loads(strips=None, cases_and_combos=None)`

Lee y limpia la tabla `Strip Forces`.

### `get_pier_forces(piers=None, stories=None, cases_and_combos=None)`

Lee resultados de piers con estructura muy cercana al reporte CSI.

### `get_pier_displacements(piers=None, cases_and_combos=None)`

Arma desplazamientos de piers cruzando varias tablas CSI.

Es un metodo semiestructurado y depende de nombres de tablas, stories y bays.

### `get_story_forces(cases_and_combos=None)`

Lee `Story Forces`.

### `get_story_displacements(cases_and_combos=None)`

Lee `Story Max Over Avg Displacements`.

### `get_story_drifts(cases_and_combos=None)`

Lee `Diaphragm Max Over Avg Drifts`.

### `extract_soil_pressures(cases_and_combos=None)`

Lee `Soil Pressures`.

Estos metodos dependen del estado de resultados y del conjunto activo de casos/combinaciones.

## Resultados modales

### `get_modal_data(cases=None)`

Consolida informacion modal desde tablas CSI.

### `get_modal_periods(case_name=None, num_modes=None, as_dict=False)`

Resume periodos modales, pero sigue dependiendo del caso modal activo y de columnas CSI.

### `get_modal_summary(case_name=None, num_modes=None)`

Arma un resumen modal a partir de datos tabulares.

### `get_modal_displacements(case_name=None, point_names=None, mode_number=None, item_type=0)`

Consulta desplazamientos modales puntuales con semantica muy cercana a CSI.

`item_type` se pasa casi directo al contrato de la API.

### `get_modal_shape(case_name=None, mode_number=1, direction="3D", normalize=True)`

Construye una forma modal para visualizacion.

Es mas alto nivel que `get_modal_displacements`, pero sigue dependiendo de la estructura modal nativa.

## Exportes tecnicos

### `get_load_cases_info(include_cases=True, include_combos=True, include_patterns=True, include_details=True)`

Construye una vista amplia de patrones, casos, combinaciones y detalle interno.

Es util como inspeccion tecnica del modelo mas que como helper simplificado.

### `export_load_cases_to_dict(simplified=False)`

Exporta la informacion de cargas con formato serializable.

### `get_model_geometry(include_frames=True, include_areas=True, include_points=True, include_sections=True)`

Construye una vista amplia de geometria del modelo.

### `get_geometry_summary()`

Resume conteos, dimensiones y clasificaciones.

### `export_geometry_to_dict(simplified=False)`

Exporta la geometria en formato serializable.

Estos metodos no son tan directos como los getters CSI, pero son tecnicos y pensados para inspeccion, reporte o integracion.
