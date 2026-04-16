# csi_py

Documentacion del proyecto organizada para consulta local y publicacion con Sphinx + MyST.

```{toctree}
:maxdepth: 2
:caption: Contenido

SPEC
ARQUITECTURA
api/index
USO_API
```

## Inicio rapido

La clase principal es `CSIHandler`:

```python
from csi_py import CSIHandler

model = CSIHandler(program="ETABS", backend="auto")
```

## Mapa de consulta

- [Especificacion](SPEC.md): contratos y alcance
- [Arquitectura](ARQUITECTURA.md): organizacion interna por capas
- [Indice de API](api/index.md): referencia agrupada por responsabilidades
- [Guia unificada](USO_API.md): puerta de entrada resumida

## Criterio editorial

La documentacion esta separada en:

- documentos normativos
- documentos arquitectonicos
- documentos de referencia de API

La navegacion principal recomendada para publicacion es esta pagina.
