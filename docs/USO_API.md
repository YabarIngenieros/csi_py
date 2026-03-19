# Uso API

Este proyecto ahora usa una estrategia de documentación compacta:

- Los docstrings en el código son breves y describen solo el propósito del método.
- Las notas de uso, ejemplos y convenciones se concentran aquí para no recargar `builder.py`, `extractor.py` y `handler.py`.

## Conexión

`CSIHandler` admite:

- `backend="auto"`: intenta `.NET` primero y luego `comtypes`.
- `backend="dotnet"`: fuerza `pythonnet`.
- `backend="comtypes"`: fuerza COM clásico.

Ejemplo:

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.connect_open_instance()
```

## Builder

Métodos clave:

- `set_table(...)`: envía un `DataFrame` a una tabla editable del modelo.
- `export_tabular_data(...)`: exporta un diccionario `{tabla: DataFrame}`.
- `export_tables_batch(...)`: exporta tablas por grupos.
- `add_frame_section(...)`: despacha la creación según `section_type`.
- `add_area_section(...)`: despacha la creación según `section_type`.

## Extractor

Métodos clave:

- `get_table(...)`: obtiene tablas de display o edición.
- `get_modal_periods(...)`: retorna períodos modales.
- `get_modal_summary(...)`: resume participación modal por modo.
- `get_modal_displacements(...)`: extrae eigenvectores en nodos.
- `get_modal_shape(...)`: construye una forma modal lista para visualizar.
- `get_model_geometry(...)`: arma un paquete de geometría del modelo.
- `get_load_cases_info(...)`: resume patrones, casos y combinaciones.
- `get_combo_breakdown(...)`: expande combinaciones de carga recursivamente.

## Criterio

Si un método necesita más explicación que una sola línea, la idea es documentarlo aquí o en `README.md`, no dentro del archivo fuente.
