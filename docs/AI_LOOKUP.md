# AI Lookup

Esta pagina esta optimizada para recuperacion semantica y busqueda por intencion.

Use este documento cuando necesite responder rapido preguntas del tipo:

- "como conecto a ETABS"
- "como sacar vigas y columnas"
- "como leer grids"
- "como exportar geometria"
- "como aplicar cargas"

## Punto de entrada principal

- clase principal: `CSIHandler`
- herencia publica: `CSIHandler -> ModelBuilder + DataExtractor + Handler`

## Intenciones frecuentes -> metodos

### Conectar a una instancia o abrir un modelo

- conectar a instancia abierta: `connect_open_instance(instance_position=None)`
- abrir archivo y conectar: `open_and_connect(file_path=None)`
- crear modelo vacio: `open_empty_instance(units=None)`
- guardar modelo: `save(model_path)`
- cerrar aplicacion: `close()`
- refrescar vista: `refresh_view()`
- cambiar unidades activas: `set_units()`

Sinonimos utiles:

- conectar ETABS
- abrir SAP2000
- adjuntarse a instancia
- crear modelo nuevo

## Tablas CSI

- listar tablas disponibles: `available_tables`
- listar tablas editables: `editable_tables`
- leer tabla por nombre exacto: `get_table(table_name, set_envelopes=True, runned=False)`
- leer todas las tablas editables cacheadas: `tabular_data`
- leer tabla editable: `get_editing_table(table_name)`
- escribir tabla editable: `set_table(table_name, table, table_version=1, apply=True)`
- aplicar tablas pendientes: `apply_edited_table()`
- exportar varias tablas: `export_tabular_data(tabular_data, table_names=None, apply=True)`
- exportar tablas por grupos: `export_tables_batch(tabular_data, table_groups=None)`

Sinonimos utiles:

- tabla CSI
- database tables
- editable tables
- importar tabla
- exportar tabla

## Grids y ejes

- nombres de sistemas de grids: `grid_system_names`
- lineas de grid normalizadas: `grid_lines`
- leer grids como DataFrame: `get_grid_system(grid_system_name=None)`
- definir grilla cartesiana por tablas: `set_grid_system(X, Y, spacing=True)`
- alias retrocompatible: `set_grid_sitem(X, Y, spacing=True)`

Sinonimos utiles:

- ejes
- grillas
- grid definitions
- grid lines
- grid system
- eje general
- grid oblicuo

## Puntos

- lista de puntos: `point_list`
- puntos base: `base_points`
- coordenadas de puntos: `get_point_coordinates(point_names)`
- restricciones nodales: `get_point_restraints(point_names)`
- reacciones nodales: `get_point_reactions(point_names=None, cases_and_combos=None)`
- puntos seleccionados: `get_selected_points()`
- crear punto: `add_point(x, y, z)`
- restringir punto: `set_point_restraint(point_name, UX=True, UY=True, UZ=True, RX=True, RY=True, RZ=True)`
- carga puntual: `add_point_load(point_name, load_pattern, Fx=0, Fy=0, Fz=0, Mx=0, My=0, Mz=0)`

Sinonimos utiles:

- joints
- nodos
- joints coordinates
- restraints

## Frames, vigas y columnas

- lista de frames: `frame_list`
- labels y story de frames: `frame_label_names`
- propiedades resumidas de frames: `frames_properties`
- seccion de un frame: `get_frame_section(frame_name)`
- puntos extremos de un frame: `get_frame_points(frame_name)`
- coordenadas extremas de un frame: `get_frame_coordinates(frame_name)`
- longitud de frame: `get_frame_length(frame_name)`
- fuerzas internas de frame: `get_frame_forces(frame_name=None, cases_and_combos=None)`
- labels de vigas: `label_beams`
- labels de columnas: `label_columns`
- fuerzas de vigas por tabla: `get_beam_forces(beams_label=None, cases_and_combos=None)`

### Conectividad de frames

- conectividad conjunta de vigas y columnas: `get_frames_connectivity(frame_type=None, labels=None, tol=1e-6)`
- propiedad cacheada: `frames_connectivity`
- aliases: `get_frame_connectivity(...)`, `frame_connectivity`
- filtrar frames por eje, interseccion y piso: `filter_frames_by_grid(grid=None, grid_x=None, grid_y=None, story=None, frame_type=None, labels=None, tol=1e-6)`
- alias por eje simple: `get_frames_on_grid(grid, story=None, frame_type=None, labels=None, tol=1e-6)`
- alias por interseccion: `get_frames_at_intersection(grid_x, grid_y, story=None, frame_type=None, labels=None, tol=1e-6)`
- conectividad de vigas: `get_beams_connectivity(beams_label=None, tol=1e-6)`
- propiedad cacheada: `beams_connectivity`
- aliases: `get_beam_connectivity(...)`, `beam_connectivity`
- conectividad de columnas: `get_columns_connectivity(columns_label=None, tol=1e-6)`
- propiedad cacheada: `columns_connectivity`
- aliases: `get_column_connectivity(...)`, `column_connectivity`

Columnas clave de conectividad:

- vigas: `Grid`
- columnas: `GridX`, `GridY`, `General`
- vista conjunta: `FrameType`, `Grid`, `GridX`, `GridY`, `General`

Sinonimos utiles:

- beam connectivity
- column connectivity
- frame connectivity
- vigas por eje
- columnas por grid
- frames en un eje
- frames en interseccion de ejes
- frames por piso
- beam label
- frame section

## Secciones frame

- lista de secciones frame: `frame_sections_list`
- propiedades de seccion: `get_frame_section_properties(section_name)`
- dimensiones de secciones: `get_frame_section_dimensions(get_properties=False)`
- cache resumida: `frame_sections_data`

### Crear secciones frame

- dispatcher general: `add_frame_section(section_name, material_name, section_type, **kwargs)`
- directos: `add_rectangle_section`, `add_circle_section`, `add_pipe_section`, `add_tube_section`, `add_i_section`, `add_channel_section`, `add_tee_section`, `add_angle_section`, `add_double_angle_section`, `add_double_channel_section`, `add_concrete_box_section`, `add_concrete_tee_section`, `add_concrete_L_section`, `add_concrete_pipe_section`, `add_concrete_cross_section`, `add_plate_section`, `add_rod_section`, `add_cold_formed_c_section`, `add_cold_formed_z_section`, `add_cold_formed_hat_section`

Sinonimos utiles:

- propframe
- frame section
- seccion viga
- seccion columna

## Areas, losas, muros y decks

- lista de areas: `area_list`
- geometria de areas: `area_geometry`
- seccion de area: `get_area_section(area_name)`
- puntos de area: `get_area_points(area_name)`
- fuerzas de shell: `get_area_forces(area_name=None, cases_and_combos=None)`
- clasificar propiedades de area: `map_area_properties()`

Secciones de area y caches:

- `slab_sections_data`
- `deck_sections_data`
- `wall_sections_data`
- `floor_sections_list`
- `floor_list`
- `wall_list`

Creacion:

- dispatcher general: `add_area_section(section_name, material_name, section_type, **kwargs)`
- directos: `add_slab_section`, `add_ribbed_slab_section`, `add_waffle_slab_section`, `add_wall_section`, `add_deck_filled_section`, `add_deck_unfilled_section`, `add_deck_solid_slab_section`, `add_shell_layer`
- crear objeto area: `add_area_obj(points, section_name)`
- carga uniforme de area: `add_area_uniform_load(area_name, load_pattern, value, direction=6)`

Sinonimos utiles:

- shell
- slab
- wall
- deck
- area forces

## Materiales

- lista de materiales: `material_list`
- propiedades de materiales: `get_material_properties(material_name)`
- cache de propiedades: `material_properties`
- crear material isotropico: `add_material(...)`
- crear material uniaxial: `add_uniaxial_material(...)`
- helpers: `add_concrete_material(...)`, `add_steel_material(...)`, `add_rebar_material(...)`

Sinonimos utiles:

- concrete
- steel
- rebar
- propmaterial

## Cargas, casos y combinaciones

- casos: `cases`
- combinaciones: `combos`
- casos y combos: `cases_and_combos`
- casos de diseño: `design_cases`, `design_cases_and_combos`
- casos sísmicos: `seismic_cases`, `seismic_combos`, `seismic_cases_and_combos`
- gravedad: `gravity_cases`, `gravity_combos`, `gravity_cases_and_combos`
- seleccionar casos activos para resultados: `select_cases_and_combos(cases_and_combos)`
- desglose de combinacion: `get_combo_cases(combo_name)`
- breakdown recursivo: `get_combo_breakdown(combo_name)`
- espectros: `get_response_spectrum(spectrum_names="all")`
- patrones y resumen de cargas: `get_load_cases_info(...)`, `get_load_cases_summary()`, `export_load_cases_to_dict(simplified=False)`

Creacion:

- patron de carga: `add_load_pattern(pattern_name, pattern_type=1)`
- combinacion: `add_load_combo(combo_name, combo_type=0)`
- añadir caso a combinacion: `set_combo_case(combo_name, case_name, scale_factor)`
- carga distribuida de frame: `add_frame_distributed_load(frame_name, load_pattern, direction, value, dist_type=1)`

Sinonimos utiles:

- load pattern
- combo
- response spectrum
- distributed load

## Strips, piers, stories y suelo

- strips detectados: `strip_list`
- cargas de strips: `extract_strip_loads(strips=None, cases_and_combos=None)`, `strip_loads`
- piers: `pier_list`, `get_pier_forces(...)`, `pier_forces`, `get_pier_displacements(...)`
- stories: `stories`, `get_story_height(story)`, `get_story_forces(...)`, `story_forces`, `get_story_displacements(...)`, `story_displacements`, `get_story_drifts(...)`, `story_drifts`
- suelo: `extract_soil_pressures(cases_and_combos=None)`, `soil_pressures`

Sinonimos utiles:

- story forces
- drifts
- pier forces
- soil pressures

## Resultados modales

- datos modales: `get_modal_data(cases=None)`, `modal_data`
- casos modales: `modal_cases`
- periodos: `get_modal_periods(case_name=None, num_modes=None, as_dict=False)`
- resumen modal: `get_modal_summary(case_name=None, num_modes=None)`
- desplazamientos modales: `get_modal_displacements(case_name=None, point_names=None, mode_number=None, item_type=0)`
- forma modal: `get_modal_shape(case_name=None, mode_number=1, direction="3D", normalize=True)`

Sinonimos utiles:

- modal periods
- modal displacements
- modal shape
- eigen

## Geometria global y exportes

- geometria global: `get_model_geometry(include_frames=True, include_areas=True, include_points=True, include_sections=True, include_connectivity=False)`
- resumen geometrico: `get_geometry_summary()`
- exporte geometrico: `export_geometry_to_dict(simplified=False)`

Si necesita conectividad embebida dentro de `geom["frames"]`:

- use `get_model_geometry(include_connectivity=True)`

Sinonimos utiles:

- full geometry
- export geometry
- bounds
- connectivity embedded

## Dónde leer detalles

- conexion: [api/connection.md](api/connection.md)
- tablas y edicion: [api/tabular.md](api/tabular.md)
- extraccion y resultados: [api/extraction.md](api/extraction.md)
- construccion y cargas: [api/building.md](api/building.md)
- metodos poco abstraidos: [api/direct_csi.md](api/direct_csi.md)
