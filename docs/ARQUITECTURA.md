# Arquitectura

Este documento describe como la implementacion satisface la especificacion en [`docs/SPEC.md`](/d:/programas/paquetes/csi_py/docs/SPEC.md).

## Vision general

`csi_py` esta armado en capas para esconder diferencias entre la API `.NET` de CSI y la via COM clasica.

```text
CSIHandler
  -> ModelBuilder
    -> DataExtractor
      -> Handler
        -> backend real (.NET o comtypes)
        -> CSIAPIHelpers
```

## Capas de implementacion

### `handler.py`

Responsabilidades:

- validar programa (`ETABS`, `SAP2000`, `SAFE`)
- resolver backend (`auto`, `dotnet`, `comtypes`)
- localizar ejecutables y DLLs instaladas
- adjuntarse a una instancia abierta o crear una nueva
- exponer operaciones base del modelo (`save`, `close`, `refresh_view`, `set_units`)

Piezas principales:

- `PROGRAM_INFO`: metadatos por producto CSI
- `_DotNetBackend`: wrapper para `pythonnet`
- `_ComtypesBackend`: wrapper para `comtypes`
- `Handler`: clase base de conexion
- `CSIHandler`: API final publica

### `api_helpers.py`

Responsabilidades:

- envolver el modelo CSI con un proxy uniforme
- normalizar firmas y valores de retorno entre `.NET` y `comtypes`
- convertir enums y arreglos donde la API `.NET` lo requiere

Esta capa es la razon por la que metodos como `GetNameList`, `GetTableForDisplayArray` o `SetRectangle` pueden ser usados desde el resto del proyecto casi sin ramas por backend.

### `extractor.py`

Responsabilidades:

- leer tablas de display y tablas editables
- consultar geometria, materiales, puntos, frames, areas y pisos
- extraer cargas, combinaciones, resultados de elementos y resultados globales
- resumir informacion modal y de casos de carga

Patron interno:

- muchas propiedades usan cache (`self._...`) para evitar repetir llamadas a la API CSI
- los metodos `get_*` suelen construir `DataFrame` o `dict`
- varias propiedades publicas se apoyan en esos metodos y almacenan el resultado

### `builder.py`

Responsabilidades:

- modificar tablas editables del modelo
- crear materiales y secciones
- crear puntos, frames y areas
- asignar restricciones, patrones, cargas y combinaciones
- exportar conjuntos de tablas por lotes

`ModelBuilder` hereda de `DataExtractor`, de modo que puede usar informacion del modelo actual mientras construye o modifica objetos.

## Flujo de implementacion

1. `CSIHandler(...)` valida programa y backend.
2. `Handler` crea un conector real.
3. Al conectar o abrir una instancia, `Handler._bind_model()` obtiene el `SapModel`.
4. `CSIAPIHelpers.get_model_proxy()` envuelve el modelo con `_CSIProxy`.
5. Las capas superiores usan `self.model` sin preocuparse por diferencias de backend.

## Decisiones de implementacion

- La libreria prioriza una API de trabajo practica sobre una API estrictamente minimalista.
- El proyecto usa `pandas` como formato principal de intercambio para tablas y resultados.
- La mayor parte del codigo esta centrada en ETABS, pero la capa de conexion fue generalizada para SAP2000 y SAFE.
- El codigo prefiere mantener los docstrings cortos y mover el detalle normativo a la spec y el detalle operativo a las guias.

## Riesgos y deuda tecnica observables

- La jerarquia es amplia y concentra mucha responsabilidad en una sola clase publica.
- Hay caches sin invalidacion automatica cuando el modelo cambia.
- La cobertura de pruebas no esta integrada como suite reproducible del repo.
- Persisten algunos nombres heredados y pequenas inconsistencias tipograficas, por ejemplo `get__pids`; `set_grid_sitem` se mantiene solo como alias retrocompatible de `set_grid_system`.

## Donde extender la implementacion

Si se agregan nuevas capacidades, la separacion recomendada es:

- conexion o compatibilidad de backend: `handler.py` o `api_helpers.py`
- lectura o resumen de datos: `extractor.py`
- escritura, construccion o edicion del modelo: `builder.py`
- enums, errores o unidades: `constants.py`
