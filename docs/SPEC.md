# Especificacion

## Objetivo

`csi_py` debe ofrecer una API Python unica para automatizar ETABS, SAP2000 y SAFE en Windows, abstraer la diferencia entre backend `.NET` y `comtypes`, y permitir tanto lectura como escritura de modelos CSI desde una misma superficie publica.

## Alcance

La especificacion cubre:

- conexion a instancias abiertas o nuevas de software CSI
- seleccion automatica o explicita de backend
- operaciones base sobre el modelo activo
- extraccion de tablas, geometria, cargas, combinaciones y resultados
- construccion y edicion programatica de materiales, secciones, objetos y cargas
- exporte e importacion tabular por medio de `pandas`

La especificacion no cubre:

- interfaz grafica propia
- ejecucion en sistemas no Windows
- equivalencia total de cada helper entre ETABS, SAP2000 y SAFE
- garantia de backward compatibility entre versiones mayores futuras

## API publica normativa

La API publica del paquete debe incluir al menos:

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

`CSIHandler` es la API principal para usuarios finales.

## Modelo de estados

Una instancia de `CSIHandler` debe seguir este modelo:

### Estado `initialized`

Condiciones:

- el objeto fue creado
- el backend solicitado fue validado
- aun no hay modelo CSI enlazado

### Estado `connected`

Condiciones:

- existe `self.object`
- existe `self.model`
- `self.is_connected` es `True`

Transiciones validas:

- `connect_open_instance()`: `initialized -> connected`
- `open_and_connect()`: `initialized -> connected`
- `open_empty_instance()`: `initialized -> connected`
- `close()`: `connected -> initialized`

## Contratos de conexion

### Programa soportado

El parametro `program` debe aceptar:

- `ETABS`
- `SAP2000`
- `SAFE`
- alias `SAP` como equivalente a `SAP2000`

Si el programa no es valido, se debe lanzar `ValueError`.

### Backend soportado

El parametro `backend` debe aceptar:

- `auto`
- `dotnet`
- `comtypes`

Si el backend no es valido, se debe lanzar `ValueError`.

### Resolucion de backend

Contrato:

- `auto` debe intentar `.NET` primero
- si `.NET` falla, `auto` debe intentar `comtypes`
- si ambos fallan, la inicializacion debe fallar con `RuntimeError`

### Conexion a instancia abierta

`connect_open_instance(instance_position=None)` debe:

- conectarse a la instancia activa cuando `instance_position` sea `None`
- conectarse a una instancia por posicion cuando `instance_position` sea entero
- fallar con `TypeError` si `instance_position` tiene un tipo no soportado
- fallar con `ConnectionError` si no hay instancia disponible

### Apertura de archivo

`open_and_connect(file_path)` debe:

- fallar con `FileNotFoundError` si `file_path` no existe
- abrir el archivo en una instancia nueva del programa CSI
- dejar al handler en estado `connected`

### Modelo vacio

`open_empty_instance(units=None)` debe:

- crear una instancia nueva del programa
- inicializar un modelo en blanco
- aplicar unidades si se solicitaron
- dejar al handler en estado `connected`

## Contratos de compatibilidad entre backends

La capa de helpers debe garantizar, en la medida de lo posible, que:

- las llamadas de alto nivel puedan usar las mismas firmas Python
- las diferencias de retorno entre `.NET` y `comtypes` queden normalizadas
- los enums necesarios para `.NET` se conviertan internamente

La compatibilidad buscada es funcional, no binaria.

## Contratos de lectura

## Tablas

`get_table(table_name, set_envelopes=True, runned=False)` debe:

- retornar un `pandas.DataFrame` cuando la tabla exista y la llamada sea exitosa
- lanzar `ValueError` cuando la tabla no exista
- lanzar `EtabsError` ante codigos de error CSI no manejados
- poder intentar correr analisis si la tabla requiere resultados y aun no existen

`available_tables` debe retornar un `DataFrame` con las tablas disponibles.

`editable_tables` debe retornar el subconjunto editable de `available_tables`.

`tabular_data` debe retornar un diccionario `{nombre_tabla: DataFrame}` cacheado.

## Geometria y propiedades

El extractor debe proveer consultas para:

- materiales
- puntos
- frames
- areas
- muros, pisos y piers
- historias

Las operaciones de lectura deben retornar `DataFrame`, `dict`, `list` o escalares segun el helper.

## Resultados

El extractor debe proveer consultas para:

- fuerzas de nodos
- fuerzas de frames
- fuerzas de areas
- resultados de piers
- resultados de historias
- resultados modales

Cuando falte la informacion necesaria en el modelo, el helper debe fallar con una excepcion clara, tipicamente `ValueError`.

## Contratos de escritura

## Tablas editables

`get_editing_table(table_name)` debe retornar:

- version de tabla
- `DataFrame` editable

Si la tabla no existe, debe lanzar `ValueError`.

`set_table(table_name, table, table_version=1, apply=True)` debe:

- aceptar un `pandas.DataFrame`
- cargarlo a la tabla editable CSI
- aplicar cambios inmediatamente si `apply=True`

`apply_edited_table()` debe:

- aplicar cambios pendientes al modelo
- fallar con `RuntimeError` si CSI reporta errores fatales o de edicion
- poder emitir advertencias si solo hubo warnings

## Construccion de entidades

La capa builder debe soportar al menos:

- creacion de materiales
- creacion de secciones frame
- creacion de secciones area
- creacion de puntos
- creacion de frames
- creacion de areas
- asignacion de restricciones
- definicion de patrones y combinaciones de carga
- aplicacion de cargas puntuales, distribuidas y uniformes

Si un tipo de seccion solicitado no es valido, se debe lanzar `ValueError`.

Si los datos de entrada para una operacion tabular son incompatibles, se debe lanzar `TypeError` o `ValueError` segun corresponda.

## Contratos de datos

La libreria usa `pandas` como formato principal para:

- tablas CSI
- resultados tabulares
- exportes resumidos

La libreria usa `dict` o `list` para estructuras pequenas o semiestructuradas cuando un `DataFrame` no aporta claridad.

## Caching

La libreria puede cachear lecturas de alto costo en propiedades internas.

La especificacion actual no exige invalidacion automatica de cache cuando el modelo cambia.

Consecuencia:

- despues de mutaciones del modelo, el consumidor puede necesitar reinstanciar el handler o evitar reutilizar caches previas

## Errores

Las categorias de error esperadas en la API incluyen:

- `ValueError`: entrada invalida o recurso inexistente
- `TypeError`: tipo de argumento no soportado
- `FileNotFoundError`: archivo de modelo inexistente
- `ConnectionError`: no se pudo conectar a una instancia abierta
- `RuntimeError`: error de backend o aplicacion de tablas
- `EtabsError`: error CSI reportado por la API
- `NotImplementedError`: comportamiento aun no implementado para cierto caso

## Garantias minimas

La libreria debe garantizar:

- una API publica unica centrada en `CSIHandler`
- compatibilidad operativa con `.NET` y `comtypes`
- soporte para ETABS, SAP2000 y SAFE en la capa de conexion
- soporte para lectura y escritura desde la misma instancia de trabajo

La libreria no garantiza:

- cobertura completa de toda la API CSI
- ausencia de diferencias de comportamiento entre programas CSI
- ausencia de caches obsoletas tras modificar el modelo
- pruebas automatizadas completas sin dependencias externas

## Trazabilidad hacia implementacion

La implementacion actual se reparte asi:

- conexion y estado: [`handler.py`](/d:/programas/paquetes/csi_py/handler.py)
- compatibilidad entre backends: [`api_helpers.py`](/d:/programas/paquetes/csi_py/api_helpers.py)
- lectura: [`extractor.py`](/d:/programas/paquetes/csi_py/extractor.py)
- escritura: [`builder.py`](/d:/programas/paquetes/csi_py/builder.py)

## Regla de evolucion

Los cambios futuros deberian seguir esta prioridad:

1. actualizar primero esta especificacion
2. ajustar despues la implementacion
3. regenerar o reescribir la guia de uso derivada
