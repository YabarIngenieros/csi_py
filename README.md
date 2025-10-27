# CSI Python Library

Una biblioteca Python para automatizar y controlar software de análisis estructural CSI (ETABS, SAP2000, SAFE) mediante su API COM.

## Características

- 🔌 Conexión a instancias abiertas de ETABS, SAP2000 y SAFE
- 📊 Extracción de datos del modelo (geometría, materiales, resultados)
- 🏗️ Construcción programática de modelos
- 🔄 Soporte para múltiples instancias simultáneas
- 📦 Gestión automática de unidades

## Requisitos

- Windows OS
- Python 3.7+
- ETABS, SAP2000 o SAFE instalado
- Dependencias:
  - comtypes
  - pandas
  - numpy
  - psutil

## Instalación

```bash
pip install -e .
```

O instalar dependencias manualmente:

```bash
pip install comtypes pandas numpy psutil
```

## Uso Rápido

### Conectar a una instancia abierta

```python
from handler import CSIHandler

# Crear handler para ETABS
model = CSIHandler(program='ETABS', units='kN_m_C')

# Conectar a la instancia activa
model.connect_open_instance()

# Trabajar con el modelo...

# Cerrar cuando termines
model.close()
```

### Abrir un archivo específico

```python
model = CSIHandler(program='ETABS')
model.open_and_connect(r'C:\Proyectos\MiModelo.EDB')

# Trabajar con el modelo...

model.close()
```

## Ejemplos

Ver la carpeta `examples/` para ejemplos completos:

- `example_basic_connection.py` - Conexión básica y exploración
- `example_build_frame.py` - Construcción de un pórtico simple
- `example_extract_data.py` - Extracción de datos del modelo

## Unidades Disponibles

```python
# Unidades imperiales
'lb_in_F', 'lb_ft_F', 'kip_in_F', 'kip_ft_F'

# Unidades métricas
'kN_mm_C', 'kN_m_C', 'kN_cm_C'
'kgf_mm_C', 'kgf_m_C', 'kgf_cm_C'
'N_mm_C', 'N_m_C', 'N_cm_C'
'Ton_mm_C', 'Ton_m_C', 'Ton_cm_C'
```

## Funcionalidades Principales

### DataExtractor (Extracción de datos)
- Extracción de geometría de frames
- Propiedades de materiales
- Propiedades de secciones
- Resultados de análisis
- Reacciones y fuerzas

### ModelBuilder (Construcción de modelos)
- Creación de materiales
- Secciones de frames (vigas/columnas)
- Secciones de áreas (losas/muros)
- Patrones de carga
- Combinaciones de carga

## Programas Soportados

- **ETABS** - Análisis y diseño de edificios
- **SAP2000** - Análisis estructural de propósito general
- **SAFE** - Diseño de losas y fundaciones

## Utilidades

### Listar instancias activas

```python
from handler import get__pids, get_paths

# Obtener PIDs de procesos ETABS activos
pids = get__pids('ETABS')

# Obtener paths de archivos abiertos
paths = get_paths('ETABS')
```

## Estructura del Proyecto

```
csi_py/
├── constants.py      # Enumeraciones y constantes
├── handler.py        # Clase principal CSIHandler
├── extractor.py      # Mixin para extracción de datos
├── builder.py        # Mixin para construcción de modelos
├── setup.py          # Configuración de instalación
└── examples/         # Ejemplos de uso
```

## Licencia

MIT License - ver archivo [LICENSE](LICENSE)

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## Autor

YabarIngenieros

## Notas

- Esta biblioteca requiere que el software CSI correspondiente esté instalado y licenciado
- La API COM debe estar habilitada en el software CSI
- Algunos métodos pueden variar según la versión del software CSI