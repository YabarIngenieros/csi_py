# Indice de API

Referencia agrupada por responsabilidades de implementacion.

```{toctree}
:maxdepth: 2
:caption: API publica

connection
tabular
extraction
building
direct_csi
```

## Vista general

`CSIHandler` concentra la API publica y hereda de tres capas:

- `Handler`: conexion, backend y operaciones base
- `DataExtractor`: lectura, resultados y resumentes
- `ModelBuilder`: escritura, construccion y edicion

## Agrupacion elegida

- [Conexion y utilidades](connection.md)
- [Tablas y edicion](tabular.md)
- [Extraccion y resultados](extraction.md)
- [Construccion y cargas](building.md)
- [Metodos poco abstraidos](direct_csi.md)

## Referencias relacionadas

- [Especificacion](../SPEC.md)
- [Arquitectura](../ARQUITECTURA.md)
- [Guia unificada](../USO_API.md)
