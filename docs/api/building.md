# Construccion y cargas

Esta seccion documenta la API publica de escritura y construccion: materiales, secciones, objetos, cargas y operaciones basadas en tablas editables.

## Materiales

### `add_material(material_name, material_type, E, U, A, mass_per_volume)`

Wrapper directo para material isotropico.

```python
from csi_py import eMatType, u

model.add_material(
    "STEEL1",
    eMatType.Steel,
    2e5 * u.MPa,
    0.3,
    0.0000117,
    7850 * u.kg / u.m**3,
)
```

Es un metodo poco abstraido y cercano a la semantica nativa de CSI.

### `add_uniaxial_material(material_name, material_type, E, A, mass_per_volume)`

Wrapper directo para material uniaxial.

```python
model.add_uniaxial_material(
    "RB420",
    eMatType.Rebar,
    2e5 * u.MPa,
    0.0000117,
    7850 * u.kg / u.m**3,
)
```

### `add_concrete_material(name, fc=21*u.MPa, E=None, U=0.15, A=0.0000099, mass_per_volume=...)`

Helper para concreto.

```python
from csi_py import u

model.add_concrete_material("CONC25", fc=25 * u.MPa)
```

Notas:

- si `E` no se entrega, intenta estimarlo segun el sistema de unidades activo
- en sistemas no contemplados puede lanzar `NotImplementedError`

### `add_steel_material(name, E=..., U=0.30, A=..., mass_per_volume=...)`

```python
model.add_steel_material("A36")
```

### `add_rebar_material(name, E=..., A=..., mass_per_volume=...)`

```python
model.add_rebar_material("FY420")
```

## Puntos y restricciones

### `add_point(x, y, z)`

Crea un punto y retorna su nombre.

```python
p1 = model.add_point(0, 0, 0)
p2 = model.add_point(0, 0, 3)
```

Errores esperables:

- `RuntimeError` si CSI devuelve error al crear el punto

### `set_point_restraint(point_name, UX=True, UY=True, UZ=True, RX=True, RY=True, RZ=True)`

Asigna restricciones al punto.

```python
model.set_point_restraint(p1, True, True, True, True, True, True)
```

## Secciones frame

### Metodos directos por tipo

Todos estos son wrappers casi directos de CSI:

- `add_rectangle_section(section_name, material_name, t3, t2)`
- `add_circle_section(section_name, material_name, diameter)`
- `add_pipe_section(section_name, material_name, diameter, thickness)`
- `add_tube_section(section_name, material_name, t3, t2, tf, tw)`
- `add_i_section(section_name, material_name, t3, t2, tf, tw, t2b=None, tfb=None)`
- `add_channel_section(section_name, material_name, t3, t2, tf, tw)`
- `add_tee_section(section_name, material_name, t3, t2, tf, tw)`
- `add_angle_section(section_name, material_name, t3, t2, tf, tw)`
- `add_double_angle_section(section_name, material_name, t3, t2, tf, tw, dis)`
- `add_double_channel_section(section_name, material_name, t3, t2, tf, tw, dis)`
- `add_concrete_box_section(section_name, material_name, t3, t2, tf, tw)`
- `add_concrete_tee_section(section_name, material_name, t3, t2, tf, tw, twt=None, mirror=False)`
- `add_concrete_L_section(section_name, material_name, t3, t2, tf, tw)`
- `add_concrete_pipe_section(section_name, material_name, diameter, thickness)`
- `add_concrete_cross_section(section_name, material_name, t3, t2, tf, tw)`
- `add_plate_section(section_name, material_name, thickness)`
- `add_rod_section(section_name, material_name, diameter)`
- `add_cold_formed_c_section(section_name, material_name, t3, t2, thickness, lip)`
- `add_cold_formed_z_section(section_name, material_name, t3, t2, thickness, lip)`
- `add_cold_formed_hat_section(section_name, material_name, t3, t2, thickness)`

Ejemplos:

```python
model.add_rectangle_section("COL40x40", "CONC25", t3=0.40, t2=0.40)
model.add_i_section("W18x35", "A36", t3=0.457, t2=0.152, tf=0.011, tw=0.007)
model.add_pipe_section("PIPE8", "A36", diameter=0.203, thickness=0.008)
```

### `add_frame_section(section_name, material_name, section_type, **kwargs)`

Dispatcher unificado para secciones frame.

```python
model.add_frame_section(
    "COL50x30",
    "CONC25",
    "Rectangle",
    t3=0.50,
    t2=0.30,
)
```

Uso:

- `section_type` debe coincidir con una clave soportada por el dispatcher
- los `kwargs` dependen del tipo de seccion elegido

Errores esperables:

- `ValueError` si `section_type` no es valido

## Section Designer

### `add_tee_SD_sections(name, material, height, width, thick, apply=False)`

Crea una o varias secciones tee mediante tablas de Section Designer.

```python
model.add_tee_SD_sections(
    name=["T1", "T2"],
    material="CONC25",
    height=[0.60, 0.70],
    width=[0.50, 0.60],
    thick=[0.12, 0.12],
    apply=True,
)
```

Comportamiento:

- acepta escalares o listas compatibles
- acumula cambios en tablas internas antes de aplicar

Errores esperables:

- `TypeError` si se mezclan escalares y listas incompatibles
- `ValueError` si las listas no tienen la misma longitud

### `apply_tee_sections(version_1=1, version_2=1)`

Aplica los cambios acumulados por `add_tee_SD_sections`.

```python
model.add_tee_SD_sections("T1", "CONC25", 0.60, 0.50, 0.12, apply=False)
model.apply_tee_sections()
```

### `add_line_bar_to_section(section_name, material, p1, p2, size, max_spacing, end_bars="Yes")`

Agrega una linea de refuerzo a una seccion de Section Designer.

```python
model.add_line_bar_to_section(
    "T1",
    "FY420",
    p1=(-0.20, -0.25),
    p2=(0.20, -0.25),
    size="#5",
    max_spacing=0.15,
)
```

## Objetos frame y area

### `add_frame(point_i, point_j, section_name)`

Crea un frame entre dos puntos y asigna seccion.

```python
model.add_frame(p1, p2, "COL40x40")
```

### Secciones de area directas

Metodos directos:

- `add_slab_section(section_name, material_name, thickness, slab_type=0, shell_type=1)`
- `add_ribbed_slab_section(section_name, material_name, overall_depth, slab_thickness, stem_width, rib_spacing, rib_direction=1)`
- `add_waffle_slab_section(section_name, material_name, overall_depth, slab_thickness, stem_width_dir1, stem_width_dir2, rib_spacing_dir1, rib_spacing_dir2)`
- `add_wall_section(section_name, material_name, thickness, wall_prop_type=1, shell_type=1)`
- `add_deck_filled_section(section_name, deck_type, shell_type, fill_material, concrete_material, slab_depth, rib_depth, rib_width_top, rib_width_bot, rib_spacing, shear_studs_per_rib)`
- `add_deck_unfilled_section(section_name, deck_type, shell_type, material, rib_depth, rib_width_top, rib_width_bot, rib_spacing, shear_thickness, unit_weight)`
- `add_deck_solid_slab_section(section_name, shell_type, material, depth, shear_studs_per_rib)`
- `add_shell_layer(section_name, layer_name, distance_from_ref, thickness, shell_type, material, angle=0.0)`

Ejemplos:

```python
model.add_slab_section("LOSA20", "CONC25", thickness=0.20)
model.add_wall_section("MURO25", "CONC25", thickness=0.25)
model.add_shell_layer("LOSA_COMP", "TOP", 0.10, 0.05, 1, "CONC25")
```

### `add_area_section(section_name, material_name, section_type, **kwargs)`

Dispatcher unificado para secciones de area.

```python
model.add_area_section(
    "LOSA25",
    "CONC25",
    "Slab",
    thickness=0.25,
)
```

Errores esperables:

- `ValueError` si `section_type` no es valido

### `add_area_obj(points, section_name)`

Crea un area a partir de coordenadas y asigna una seccion.

```python
area_name = model.add_area_obj(
    [[0, 0, 3], [5, 0, 3], [5, 4, 3], [0, 4, 3]],
    "LOSA20",
)
```

Notas:

- si hace falta, invierte el orden de puntos para mantener orientacion antihoraria

## Patrones, combinaciones y cargas

### `add_load_pattern(pattern_name, pattern_type=1)`

Wrapper directo para patron de carga.

```python
model.add_load_pattern("DEAD", pattern_type=1)
model.add_load_pattern("LIVE", pattern_type=3)
```

### `add_load_combo(combo_name, combo_type=0)`

```python
model.add_load_combo("SERVICIO")
```

### `set_combo_case(combo_name, case_name, scale_factor)`

```python
model.set_combo_case("SERVICIO", "DEAD", 1.0)
model.set_combo_case("SERVICIO", "LIVE", 1.0)
```

### `add_point_load(point_name, load_pattern, Fx=0, Fy=0, Fz=0, Mx=0, My=0, Mz=0)`

```python
model.add_point_load("1", "DEAD", Fz=-100)
```

### `add_frame_distributed_load(frame_name, load_pattern, direction, value, dist_type=1)`

Metodo casi directo de CSI. `direction` y `dist_type` conservan la semantica de la API.

```python
model.add_frame_distributed_load("B1", "LIVE", direction=6, value=-12.5)
```

### `add_area_uniform_load(area_name, load_pattern, value, direction=6)`

```python
model.add_area_uniform_load("A1", "LIVE", value=-2.0, direction=6)
```

## Flujo minimo de modelado

```python
from csi_py import CSIHandler, u

model = CSIHandler(program="ETABS")
model.open_empty_instance(units="kN_m_C")

model.add_concrete_material("CONC25", fc=25 * u.MPa)
model.add_rectangle_section("COL40x40", "CONC25", t3=0.40, t2=0.40)

p1 = model.add_point(0, 0, 0)
p2 = model.add_point(0, 0, 3)
model.set_point_restraint(p1, True, True, True, True, True, True)
model.add_frame(p1, p2, "COL40x40")
```

## Metodos menos abstraidos

Los puntos mas cercanos a CSI en esta seccion son:

- `add_material`
- `add_uniaxial_material`
- `add_frame_section`
- `add_area_section`
- `add_frame_distributed_load`

En ellos conviene revisar:

- enums o codigos numericos de CSI
- compatibilidad de argumentos por tipo de seccion
- comportamiento de dispatchers frente a tipos no validos
