# Backend Objects

## Objetos principales

En la capa de conexion aparecen tres niveles de objeto:

1. objeto de aplicacion CSI
2. objeto `SapModel`
3. proxy Python uniforme usado por el resto del proyecto

En el codigo actual esos niveles viven asi:

- `self.object`: objeto de aplicacion CSI, el equivalente conceptual de `myETABSObject` en los ejemplos oficiales
- `self._raw_model`: objeto `SapModel` real del backend
- `self.model`: proxy uniforme creado por `CSIAPIHelpers.get_model_proxy()`

## Que es `csi_object`

En `handler.py`, el nombre `csi_object` se usa como nombre generico para el objeto de aplicacion CSI que devuelve el helper del backend.

Conceptualmente:

- en ETABS corresponde al objeto OAPI de la aplicacion
- en los ejemplos oficiales de CSI suele llamarse `myETABSObject`
- desde ese objeto se accede a `.SapModel`
- desde ese objeto tambien se invocan operaciones de ciclo de vida como `ApplicationStart()` y `ApplicationExit(...)`

Por eso:

- `csi_object` no es `SapModel`
- `csi_object` no es el proxy `self.model`
- `csi_object` es el objeto de aplicacion del backend

## Que es `SapModel`

`SapModel` es la interfaz central del modelo CSI.

En `csi_py` aparece en dos formas:

- `self._raw_model`: el objeto real devuelto por el backend
- `self.model`: un proxy `_CSIProxy` que intercepta llamadas para normalizar diferencias entre backends

## Que hace `_CSIProxy`

`_CSIProxy` en [api_helpers.py](/d:/programas/paquetes/csi_py/api_helpers.py) envuelve el `SapModel` real y sus subobjetos.

Su comportamiento es:

- si el atributo es callable, lo reenvia por `wrap_callable(...)`
- si no es callable, devuelve otro `_CSIProxy`

Eso permite escribir:

```python
self.model.File.OpenFile(path)
self.model.DatabaseTables.GetTableForDisplayArray(...)
```

sin ramificar el codigo de alto nivel por backend.

## Donde vive cada cosa

### En `.NET`

El backend `_DotNetBackend`:

- carga `ETABSv1.dll`, `SAP2000v1.dll` o `SAFEv1.dll`
- importa el modulo generado por CSI, por ejemplo `ETABSv1`
- crea `self.helper = self.module.cHelper(self.module.Helper())`
- usa ese helper para obtener o crear el objeto de aplicacion

En el codigo actual, `get_object`, `get_object_process`, `create_object` y `create_object_progid` devuelven objetos tipados con `self.module.cOAPI(...)`.

Luego `get_sap_model(csi_object)` devuelve `self.module.cSapModel(csi_object.SapModel)`.

### En `comtypes`

El backend `_ComtypesBackend`:

- crea el helper COM con `comtypes.client.CreateObject(...)`
- obtiene el modulo de tipos desde `comtypes.gen`
- consulta objetos de aplicacion por `GetObject`, `GetObjectProcess`, `CreateObject` o `CreateObjectProgID`

En este backend:

- `csi_object` es un proxy COM
- `get_sap_model(csi_object)` devuelve `csi_object.SapModel`

## Consecuencia practica

La misma variable `self.object` representa el mismo rol conceptual, pero no necesariamente el mismo tipo Python:

- en `.NET`: wrapper tipado de la DLL CSI
- en `comtypes`: proxy COM generado por `comtypes`

Eso explica por que un metodo puede comportarse distinto aun teniendo el mismo nombre.

## Regla de oro

Cuando un bug afecta:

- `ApplicationStart`
- `ApplicationExit`
- `SapModel`
- `GetObject` / `CreateObject`

primero hay que verificar si el problema es de:

- rol del objeto equivocado
- wrapper del backend equivocado
- semantica distinta entre `.NET` y `comtypes`

antes de agregar logica generica en `Handler`.
