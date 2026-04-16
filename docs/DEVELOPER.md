# Developer Guide

Esta guia esta orientada a quien modifica la implementacion interna de `csi_py`.

No describe la API de usuario final. Describe:

- que objetos CSI existen internamente
- como se conectan `handler.py` y `api_helpers.py`
- que diferencias reales hay entre `.NET` y `comtypes`
- donde conviene tocar el codigo cuando aparece un problema de compatibilidad

```{toctree}
:maxdepth: 2
:caption: Developer

dev/backend_objects
dev/backend_flow
```

## Lectura recomendada

1. [Backend Objects](dev/backend_objects.md)
2. [Backend Flow](dev/backend_flow.md)
3. [Arquitectura](ARQUITECTURA.md)
4. [handler.py](/d:/programas/paquetes/csi_py/handler.py)
5. [api_helpers.py](/d:/programas/paquetes/csi_py/api_helpers.py)
