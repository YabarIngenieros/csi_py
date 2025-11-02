"""
Ejemplo 2: Construcción de un Pórtico Simple

Este ejemplo muestra cómo:
- Crear un nuevo modelo desde cero
- Definir materiales y secciones
- Crear geometría (puntos y frames)
- Aplicar cargas
- Guardar el modelo
"""

from handler import CSIHandler

def build_simple_frame():
    """
    Construye un pórtico simple de 2 vanos x 1 nivel
    Dimensiones: 6m x 3m de altura
    """
    
    # Crear handler
    handler = CSIHandler(program='ETABS', units='kN_m_C')
    
    try:
        # Nota: Para crear un modelo nuevo, necesitas abrir ETABS primero
        # y luego conectar, o usar el método open_and_connect con una plantilla
        print("Asegúrate de tener ETABS abierto con un modelo nuevo")
        handler.connect_open_instance()
        
        print("=== Creando Material ===")
        # Crear material de concreto
        handler.add_material(
            material_name='CONC25',
            material_type=2,  # Concrete
            E=25000000,       # kN/m²
            U=0.2,            # Relación de Poisson
            A=0.0000099,      # Coef. expansión térmica
            weight_per_volume=24  # kN/m³
        )
        
        print("\n=== Creando Secciones ===")
        # Sección para columnas: 40x40 cm
        handler.add_rectangle_section(
            section_name='COL40X40',
            material_name='CONC25',
            t3=0.40,  # Altura
            t2=0.40   # Ancho
        )
        
        # Sección para vigas: 30x50 cm
        handler.add_rectangle_section(
            section_name='VIG30X50',
            material_name='CONC25',
            t3=0.50,  # Altura
            t2=0.30   # Ancho
        )
        
        print("\n=== Creando Geometría ===")
        # Crear puntos (3 columnas x 2 niveles = 6 puntos)
        # Nivel base
        p1 = handler.model.PointObj.AddCartesian(0, 0, 0)[0]
        p2 = handler.model.PointObj.AddCartesian(3, 0, 0)[0]
        p3 = handler.model.PointObj.AddCartesian(6, 0, 0)[0]
        
        # Nivel superior
        p4 = handler.model.PointObj.AddCartesian(0, 0, 3)[0]
        p5 = handler.model.PointObj.AddCartesian(3, 0, 3)[0]
        p6 = handler.model.PointObj.AddCartesian(6, 0, 3)[0]
        
        print(f"Puntos creados: {p1}, {p2}, {p3}, {p4}, {p5}, {p6}")
        
        # Aplicar restricciones en la base
        print("\n=== Aplicando Restricciones ===")
        for point in [p1, p2, p3]:
            handler.set_point_restraint(
                point_name=point,
                UX=True, UY=True, UZ=True,  # Traslaciones restringidas
                RX=True, RY=True, RZ=True   # Rotaciones restringidas
            )
        
        # Crear columnas
        print("\n=== Creando Columnas ===")
        c1 = handler.model.FrameObj.AddByPoint(p1, p4)[0]
        c2 = handler.model.FrameObj.AddByPoint(p2, p5)[0]
        c3 = handler.model.FrameObj.AddByPoint(p3, p6)[0]
        
        for col in [c1, c2, c3]:
            handler.model.FrameObj.SetSection(col, 'COL40X40')
        
        print(f"Columnas creadas: {c1}, {c2}, {c3}")
        
        # Crear vigas
        print("\n=== Creando Vigas ===")
        v1 = handler.model.FrameObj.AddByPoint(p4, p5)[0]
        v2 = handler.model.FrameObj.AddByPoint(p5, p6)[0]
        
        for viga in [v1, v2]:
            handler.model.FrameObj.SetSection(viga, 'VIG30X50')
        
        print(f"Vigas creadas: {v1}, {v2}")
        
        # Crear patrones de carga
        print("\n=== Creando Patrones de Carga ===")
        handler.add_load_pattern('DEAD', 1)  # Muerta
        handler.add_load_pattern('LIVE', 3)  # Viva
        
        # Aplicar carga distribuida en vigas (carga viva)
        print("\n=== Aplicando Cargas ===")
        for viga in [v1, v2]:
            handler.add_frame_distributed_load(
                frame_name=viga,
                load_pattern='LIVE',
                direction=6,  # Global Z (gravedad)
                value=-10.0   # kN/m
            )
        
        print("\n=== Modelo Creado Exitosamente ===")
        print("Ahora puedes:")
        print("1. Revisar el modelo en ETABS")
        print("2. Ejecutar análisis")
        print("3. Guardar el archivo")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # No cerrar para que el usuario pueda ver el modelo
        print("\nModelo listo para inspección. No se cerró ETABS.")
        # model.close()

if __name__ == "__main__":
    build_simple_frame()
