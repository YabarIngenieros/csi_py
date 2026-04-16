# Backend Flow

## Flujo de conexion

El flujo base de `Handler` es este:

1. validar `program` y `backend`
2. construir `self.connector`
3. obtener o crear `self.object`
4. derivar `self._raw_model` desde `self.object`
5. construir `self.model` como proxy uniforme

En codigo:

```text
Handler.__init__()
  -> _build_backend(...)
  -> self.connector

connect_open_instance() / open_and_connect() / open_empty_instance()
  -> self.object
  -> self._bind_model()

_bind_model()
  -> self._raw_model = self.connector.get_sap_model(self.object)
  -> self.model = self.api.get_model_proxy()
```

## Donde se absorben diferencias entre backends

La diferencia no se absorbe en un solo lugar. Se reparte en dos capas:

### 1. `handler.py`

Resuelve:

- como obtener el objeto de aplicacion
- como crear una nueva instancia
- como derivar `SapModel`

Esta capa responde la pregunta:

> que objeto concreto tengo que pedirle al backend para empezar a trabajar

### 2. `api_helpers.py`

Resuelve:

- indices y orden de retorno
- enums `.NET`
- arrays `.NET`
- firmas de metodos con parámetros `ref` o `out`

Esta capa responde la pregunta:

> una vez que ya tengo `SapModel`, como hago para que las llamadas se vean iguales en Python

## Como funciona `normalize_api_result`

Uno de los puntos mas importantes del backend `.NET` es:

```python
def normalize_api_result(self, result):
    if self.backend == "dotnet":
        return tuple(result[1:]) + (result[0],)
    return result
```

Esto refleja una diferencia clave:

- en `.NET`, muchos metodos retornan primero el codigo `ret`
- en `comtypes`, la forma esperada en el proyecto suele coincidir mas con la firma COM tradicional

El helper mueve el `ret` al final para estabilizar indices en el resto del codigo.

## Como funciona `wrap_callable`

`wrap_callable(path, func)` decide si un metodo necesita wrapper especial.

Ejemplos:

- `LoadCases.GetNameList`
- `DatabaseTables.GetTableForDisplayArray`
- `PropFrame.SetRectangle`
- `Results.FrameForce`

Si hay wrapper registrado:

- prepara parámetros adicionales en `.NET`
- transforma enums
- normaliza arrays de salida
- reordena el retorno

Si no hay wrapper:

- devuelve la funcion tal cual

## Diferencia estructural entre `.NET` y `comtypes`

### `.NET`

Problemas típicos:

- enums reales, no enteros
- arrays `System.Array`
- clases tipadas de la DLL CSI
- metodos con firmas más estrictas
- posibilidad de que miembros expuestos no se comporten exactamente como callables Python comunes

### `comtypes`

Problemas típicos:

- proxies COM con semantica distinta
- retornos empaquetados por `comtypes`
- interfaces a veces menos tipadas pero más directas para ciertas llamadas

## Donde depurar cada tipo de bug

### Si falla al conectar, crear o cerrar la aplicacion

Revisar primero:

- [handler.py](/d:/programas/paquetes/csi_py/handler.py)
- `_DotNetBackend`
- `_ComtypesBackend`

Preguntas clave:

- el objeto devuelto es realmente el objeto de aplicacion CSI
- se esta usando el wrapper correcto para ese backend
- `SapModel` se deriva del objeto correcto

### Si falla una llamada de `self.model`

Revisar primero:

- [api_helpers.py](/d:/programas/paquetes/csi_py/api_helpers.py)
- `wrap_callable`
- el wrapper especifico `_wrap_*`

Preguntas clave:

- faltan enums o arrays para `.NET`
- el retorno necesita `normalize_api_result`
- la firma usada por el wrapper coincide con la version de CSI instalada

### Si falla una operacion de alto nivel del extractor o builder

Revisar:

- [extractor.py](/d:/programas/paquetes/csi_py/extractor.py)
- [builder.py](/d:/programas/paquetes/csi_py/builder.py)

Pero solo despues de validar que:

- `self.object` es correcto
- `self._raw_model` es correcto
- `self.model` esta llamando un wrapper valido

## Recomendaciones para cambios futuros

1. no mezclar correcciones de rol de objeto con correcciones de firma
2. si un bug toca `ApplicationStart`, `ApplicationExit` o `SapModel`, empezar en `handler.py`
3. si un bug toca `GetTableForDisplayArray`, `SetRectangle`, `JointDispl` o similares, empezar en `api_helpers.py`
4. antes de generalizar un workaround, confirmar si el problema existe en ambos backends
5. documentar explicitamente si un nombre como `csi_object` representa:
   - objeto de aplicacion
   - `SapModel`
   - proxy uniforme
