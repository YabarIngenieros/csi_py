# Guia de uso derivada de la spec

Esta guia sigue existiendo como puerta de entrada humana, pero la referencia ya no vive en una sola pagina grande.

La documentacion de API fue agrupada por responsabilidades para hacerla mas consultable y mas facil de publicar con Sphinx + MyST.

El detalle de las funciones no abstraidas ya no esta en esta pagina: fue movido a las paginas tematicas, donde ahora queda documentado por grupos de responsabilidad.

## Ruta recomendada de lectura

1. [Indice principal](index.md)
2. [Especificacion](SPEC.md)
3. [Arquitectura](ARQUITECTURA.md)
4. [Indice de API](api/index.md)

## Referencia agrupada

- [Conexion y utilidades](api/connection.md)
- [Tablas y edicion](api/tabular.md)
- [Extraccion y resultados](api/extraction.md)
- [Construccion y cargas](api/building.md)

Cada una de esas paginas incluye:

- metodos y propiedades agrupados por tema
- parametros y comportamiento practico cuando aplica
- ejemplos minimos de uso
- notas sobre los puntos mas cercanos a la semantica de CSI

Si necesita una lista concentrada de los helpers mas tecnicos y menos abstraidos, use:

- [Metodos poco abstraidos](api/direct_csi.md)

## Flujo minimo

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
model.open_and_connect(r"C:\Modelos\edificio.edb")

story_forces = model.get_table("Story Forces")

model.save(r"C:\Modelos\edificio_editado.edb")
model.close()
```

Si no quiere pasar la ruta manualmente:

```python
model = CSIHandler(program="ETABS", backend="auto")
model.open_and_connect()
```

## Cuando usar esta pagina

Use esta pagina como mapa.

Use las paginas agrupadas cuando necesite:

- ver metodos relacionados entre si
- navegar como referencia publicada
- ubicar rapido que capa expone cada capacidad

## Referencias relacionadas

- [Especificacion](SPEC.md)
- [Arquitectura](ARQUITECTURA.md)
- [Indice de API](api/index.md)
- [Ejemplo de builder](../examples/ejemplo_builder.py)
- [Chequeo por lotes del extractor](../examples/ejemplo_error_cargas.py)
