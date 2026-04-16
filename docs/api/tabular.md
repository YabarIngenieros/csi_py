# Tablas y edicion

Esta seccion agrupa los metodos que trabajan directamente con tablas CSI, tanto de visualizacion como editables.

## Tablas de visualizacion

### `available_tables`

Propiedad que retorna un `DataFrame` con las tablas disponibles y su `ImportType`.

```python
tables = model.available_tables
```

Uso tipico:

- inspeccionar tablas disponibles en el modelo activo
- detectar cuales pueden editarse despues

### `editable_tables`

Subconjunto de `available_tables` que CSI reporta como editable.

```python
editable = model.editable_tables
```

### `tabular_data`

Propiedad cacheada que retorna un diccionario `{tabla: DataFrame}` con todas las tablas editables.

```python
all_editable = model.tabular_data
```

Notas:

- se construye iterando `editable_tables`
- no invalida cache automaticamente cuando el modelo cambia

### `set_envelopes_for_dysplay(set_envelopes=True)`

Configura el modo de salida tabular para combinaciones, casos multistep y analisis no lineales.

```python
model.set_envelopes_for_dysplay(True)
```

Uso:

- `True`: prioriza envolventes
- `False`: permite salidas paso a paso donde la tabla lo soporte

Es un metodo poco abstraido y esta muy cercano a las opciones internas de CSI.

### `get_table(table_name, set_envelopes=True, runned=False)`

Extrae una tabla CSI de visualizacion como `DataFrame`.

```python
story_forces = model.get_table("Story Forces")
joint_disp = model.get_table("Joint Displacements", set_envelopes=False)
```

Parametros:

- `table_name`: nombre exacto de la tabla CSI
- `set_envelopes`: aplica primero `set_envelopes_for_dysplay`
- `runned`: control interno para reintento despues de correr analisis

Comportamiento:

- si la tabla requiere analisis y no hay resultados, intenta correrlo
- si la tabla no existe, lanza `ValueError`
- si CSI devuelve otro codigo de error, lanza `EtabsError`

## Tablas editables

### `get_editing_table(table_name)`

Extrae una tabla editable y retorna una tupla `(version, dataframe)`.

```python
version, table = model.get_editing_table("Material Properties 01 - General")
```

Uso:

- `version`: version de tabla que CSI espera al reimportar
- `table`: `DataFrame` listo para edicion

Errores esperables:

- `ValueError` si la tabla no existe
- `EtabsError` si CSI devuelve un error no manejado

### `apply_edited_table()`

Aplica al modelo los cambios pendientes en tablas editables.

```python
model.apply_edited_table()
```

Comportamiento:

- si CSI reporta errores fatales o de edicion, lanza `RuntimeError`
- si solo hay advertencias, puede emitir `RuntimeWarning`

### `get_editable_table(name, columns)`

Retorna una tabla editable existente o un `DataFrame` vacio con columnas dadas.

```python
version, table = model.get_editable_table(
    "Section Designer Shapes - Reinforcing - Line Bar",
    ["SectionType", "SectionName", "ShapeName"],
)
```

Uso:

- facilita trabajar con tablas opcionales o aun no creadas
- si la tabla existe, devuelve su version real
- si no existe, devuelve `version = 1` y tabla vacia

### `set_table(table_name, table, table_version=1, apply=True)`

Escribe un `DataFrame` en una tabla editable CSI.

```python
version, table = model.get_editing_table("Material Properties 01 - General")
table.loc[len(table)] = [...]
model.set_table("Material Properties 01 - General", table, table_version=version)
```

Parametros:

- `table_name`: nombre exacto de tabla editable
- `table`: `DataFrame` a importar
- `table_version`: version esperada por CSI
- `apply`: si `True`, aplica los cambios de inmediato

Notas:

- aplana el `DataFrame` a una lista 1D antes de enviarlo a CSI
- cuando `apply=False`, los cambios quedan pendientes hasta `apply_edited_table()`

### `export_tabular_data(tabular_data, table_names=None, apply=True)`

Exporta varias tablas editables a partir de un diccionario `{tabla: DataFrame}`.

```python
status = model.export_tabular_data(model.tabular_data)
```

Uso:

- `table_names=None`: exporta todas las tablas del diccionario
- `table_names=[...]`: exporta solo el subconjunto indicado

Retorno:

- diccionario de estado por tabla

Errores esperables:

- `TypeError` si `tabular_data` no es diccionario
- `ValueError` si `table_names` pide tablas ausentes en el diccionario

### `export_tables_batch(tabular_data, table_groups=None)`

Exporta tablas por grupos.

```python
batch = model.export_tables_batch(model.tabular_data)
```

Uso:

- si `table_groups` es `None`, usa grupos predefinidos
- cada grupo se exporta y aplica por separado

Retorno:

- diccionario con estado por grupo y por tabla

## Grillas del modelo

### `set_grid_system(X, Y, spacing=True)`

Define la grilla cartesiana del modelo mediante tablas CSI.

```python
model.set_grid_system([5, 5, 5], [4, 4], spacing=True)
```

Parametros:

- `X`: lista de coordenadas o espaciamientos en direccion X
- `Y`: lista de coordenadas o espaciamientos en direccion Y
- `spacing`: si `True`, interpreta `X` e `Y` como espaciamientos acumulables

Comportamiento:

- asegura existencia de la tabla general de grillas
- reescribe la tabla de lineas de grilla
- asigna letras para ejes X y numeros para ejes Y

### `set_grid_sitem(X, Y, spacing=True)`

Alias retrocompatible de `set_grid_system`.

```python
model.set_grid_sitem([5, 5, 5], [4, 4], spacing=True)
```

## Flujo tipico de edicion tabular

```python
version, table = model.get_editing_table("Material Properties 01 - General")
table.loc[len(table)] = [...]
model.set_table("Material Properties 01 - General", table, table_version=version, apply=True)
```

## Metodos menos abstraidos

Los puntos mas cercanos a CSI en esta seccion son:

- `get_table`
- `set_envelopes_for_dysplay`
- `get_editing_table`
- `set_table`
- `set_grid_system`

En ellos conviene validar:

- nombres exactos de tabla
- version de tabla
- efectos de cache y de analisis automatico
