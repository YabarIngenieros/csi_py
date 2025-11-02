"""
Ejemplo 4: Construcción de una Losa Simple

Este ejemplo muestra cómo:
- Crear una losa con columnas de soporte
- Definir secciones de área (losas)
- Aplicar cargas en áreas
- Crear una estructura 3D completa
"""

from handler import CSIHandler

def build_slab_structure():
    """
    Construye una estructura simple con losa de 6m x 6m
    soportada por 4 columnas en las esquinas
    """
    
    handler = CSIHandler(program='ETABS', units='kN_m_C')
    
    try:
        print("Asegúrate de tener ETABS abierto con un modelo nuevo")
        handler.connect_open_instance()
        
        # ===== MATERIALES =====
        print("\n=== Creando Materiales ===")
        handler.add_material(
            material_name='CONC25',
            material_type=2,
            E=25000000,
            U=0.2,
            A=0.0000099,
            weight_per_volume=24
        )
        
        # ===== SECCIONES =====
        print("\n=== Creando Secciones ===")
        
        # Columnas 40x40
        handler.add_rectangle_section(
            section_name='COL40X40',
            material_name='CONC25',
            t3=0.40,
            t2=0.40
        )
        
        # Losa de 20 cm
        handler.add_slab_section(
            section_name='LOSA20',
            material_name='CONC25',
            thickness=0.20,
            slab_type=0,  # Losa normal
            shell_type=1  # Shell-thin
        )
        
        # ===== GEOMETRÍA - NIVEL BASE =====
        print("\n=== Creando Geometría - Base ===")
        
        # Puntos base (4 esquinas)
        p1 = handler.model.PointObj.AddCartesian(0, 0, 0)[0]
        p2 = handler.model.PointObj.AddCartesian(6, 0, 0)[0]
        p3 = handler.model.PointObj.AddCartesian(6, 6, 0)[0]
        p4 = handler.model.PointObj.AddCartesian(0, 6, 0)[0]
        
        base_points = [p1, p2, p3, p4]
        print(f"Puntos base: {base_points}")
        
        # Empotrar columnas
        print("\n=== Aplicando Restricciones ===")
        for point in base_points:
            handler.set_point_restraint(
                point_name=point,
                UX=True, UY=True, UZ=True,
                RX=True, RY=True, RZ=True
            )
        
        # ===== GEOMETRÍA - NIVEL LOSA =====
        print("\n=== Creando Geometría - Nivel Losa (h=3m) ===")
        
        # Puntos superiores
        p5 = handler.model.PointObj.AddCartesian(0, 0, 3)[0]
        p6 = handler.model.PointObj.AddCartesian(6, 0, 3)[0]
        p7 = handler.model.PointObj.AddCartesian(6, 6, 3)[0]
        p8 = handler.model.PointObj.AddCartesian(0, 6, 3)[0]
        
        top_points = [p5, p6, p7, p8]
        print(f"Puntos superiores: {top_points}")
        
        # ===== COLUMNAS =====
        print("\n=== Creando Columnas ===")
        
        columns = []
        for i, (pb, pt) in enumerate(zip(base_points, top_points), 1):
            col = handler.model.FrameObj.AddByPoint(pb, pt)[0]
            handler.model.FrameObj.SetSection(col, 'COL40X40')
            columns.append(col)
        
        print(f"Columnas creadas: {columns}")
        
        # ===== LOSA =====
        print("\n=== Creando Losa ===")
        
        # Crear área (losa) definida por los 4 puntos superiores
        # Orden: anti-horario visto desde arriba
        area_points = [p5, p6, p7, p8]
        
        # Crear el objeto de área
        area_name = handler.model.AreaObj.AddByPoint(len(area_points), area_points)[0]
        
        # Asignar sección de losa
        handler.model.AreaObj.SetProperty(area_name, 'LOSA20')
        
        print(f"Losa creada: {area_name}")
        
        # ===== CARGAS =====
        print("\n=== Creando Patrones de Carga ===")
        
        handler.add_load_pattern('DEAD', 1)    # Muerta
        handler.add_load_pattern('LIVE', 3)    # Viva
        handler.add_load_pattern('SUPER', 2)   # Super muerta
        
        # Aplicar cargas en la losa
        print("\n=== Aplicando Cargas en Losa ===")
        
        # Carga muerta adicional (acabados)
        handler.add_area_uniform_load(
            area_name=area_name,
            load_pattern='SUPER',
            value=-2.0,  # kN/m²
            direction=6  # Global Z
        )
        
        # Carga viva
        handler.add_area_uniform_load(
            area_name=area_name,
            load_pattern='LIVE',
            value=-5.0,  # kN/m²
            direction=6
        )
        
        # ===== COMBINACIONES =====
        print("\n=== Creando Combinaciones de Carga ===")
        
        # Combo de servicio
        handler.add_load_combo('SERVICIO', 0)
        handler.set_combo_case('SERVICIO', 'DEAD', 1.0)
        handler.set_combo_case('SERVICIO', 'SUPER', 1.0)
        handler.set_combo_case('SERVICIO', 'LIVE', 1.0)
        
        # Combo de resistencia (simplificado)
        handler.add_load_combo('RESISTENCIA', 0)
        handler.set_combo_case('RESISTENCIA', 'DEAD', 1.4)
        handler.set_combo_case('RESISTENCIA', 'SUPER', 1.4)
        handler.set_combo_case('RESISTENCIA', 'LIVE', 1.7)
        
        print("\n=== Estructura con Losa Creada Exitosamente ===")
        print("\nResumen:")
        print(f"  - 4 columnas de 3m de altura")
        print(f"  - Losa de 6m x 6m, espesor 20cm")
        print(f"  - Carga muerta adicional: 2 kN/m²")
        print(f"  - Carga viva: 5 kN/m²")
        print("\nAhora puedes:")
        print("  1. Revisar el modelo en ETABS")
        print("  2. Ejecutar análisis")
        print("  3. Verificar diseño")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nModelo listo. ETABS no se cerró para inspección.")

if __name__ == "__main__":
    build_slab_structure()
