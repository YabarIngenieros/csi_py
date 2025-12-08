"""
Ejemplo de uso del módulo builder de csi_py
Este ejemplo demuestra cómo crear un modelo estructural usando:
- Frames (vigas y columnas)
- Slabs (losas)
- Walls (muros)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csi_py import CSI, u
from csi_py.constants import eMatType

def ejemplo_edificio_simple():
    """
    Crea un modelo simple de un edificio de 2 pisos con:
    - Columnas de concreto
    - Vigas de concreto
    - Losas macizas
    - Muros de corte
    """

    # Inicializar modelo ETABS con una instancia vacía
    etabs = CSI()
    etabs.open_empty_instance(units='kN_m_C')

    print("=" * 60)
    print("CREANDO MODELO DE EDIFICIO SIMPLE")
    print("=" * 60)

    # ==================== MATERIALES ====================
    print("\n--- Añadiendo Materiales ---")

    # Concreto f'c = 25 MPa
    etabs.add_concrete_material(
        name="CONC25",
        fc=25*u.MPa
    )

    # Acero A36
    etabs.add_steel_material(
        name="A36"
    )

    # ==================== SECCIONES DE FRAMES ====================
    print("\n--- Creando Secciones de Frames ---")

    # Columnas 40x40 cm
    etabs.add_rectangle_section(
        section_name="COL40x40",
        material_name="CONC25",
        t3=0.40,  # Altura
        t2=0.40   # Ancho
    )

    # Vigas 25x50 cm
    etabs.add_rectangle_section(
        section_name="VIG25x50",
        material_name="CONC25",
        t3=0.50,  # Altura
        t2=0.25   # Ancho
    )

    # Viga metálica I
    etabs.add_i_section(
        section_name="W18x50",
        material_name="A36",
        t3=0.46,   # Altura (18 in ≈ 0.46 m)
        t2=0.19,   # Ancho del ala (7.5 in ≈ 0.19 m)
        tf=0.015,  # Espesor del ala
        tw=0.010   # Espesor del alma
    )

    # ==================== SECCIONES DE AREAS ====================
    print("\n--- Creando Secciones de Áreas ---")

    # Losa maciza de 20 cm
    etabs.add_slab_section(
        section_name="LOSA20",
        material_name="CONC25",
        thickness=0.20,
        slab_type=0,   # 0 = Slab
        shell_type=1   # 1 = Shell-thin
    )

    # Losa nervada
    etabs.add_ribbed_slab_section(
        section_name="LOSA_NERV30",
        material_name="CONC25",
        overall_depth=0.30,      # Altura total
        slab_thickness=0.05,     # Espesor de losa superior
        stem_width=0.10,         # Ancho de nervios
        rib_spacing=0.60,        # Espaciamiento entre nervios
        rib_direction=1          # Dirección local 1
    )

    # Losa reticular (waffle)
    etabs.add_waffle_slab_section(
        section_name="LOSA_RET35",
        material_name="CONC25",
        overall_depth=0.35,
        slab_thickness=0.05,
        stem_width_dir1=0.12,
        stem_width_dir2=0.12,
        rib_spacing_dir1=0.80,
        rib_spacing_dir2=0.80
    )

    # Muro de 25 cm
    etabs.add_wall_section(
        section_name="MURO25",
        material_name="CONC25",
        thickness=0.25,
        wall_prop_type=1,  # 1 = Specified
        shell_type=1       # 1 = Shell-thin
    )

    # ==================== GEOMETRÍA ====================
    print("\n--- Creando Geometría ---")

    # Definir dimensiones
    L = 6.0   # Luz en X (m)
    B = 5.0   # Luz en Y (m)
    H = 3.0   # Altura de piso (m)

    # Crear puntos para columnas (primer nivel)
    print("\nCreando puntos de columnas...")
    points_base = {}
    points_p1 = {}
    points_p2 = {}

    for i in range(2):
        for j in range(2):
            x = i * L
            y = j * B

            # Nivel base (z=0)
            point_name = etabs.add_point(x,y,0)
            points_base[f"P{i}{j}_0"] = point_name

            # Nivel 1 (z=3)
            point_name = etabs.add_point(x,y,H)
            points_p1[f"P{i}{j}_1"] = point_name

            # Nivel 2 (z=6)
            point_name = etabs.add_point(x,y,2*H)
            points_p2[f"P{i}{j}_2"] = point_name

    # Restricciones en la base
    print("\nAplicando restricciones en la base...")
    for point_name in points_base.values():
        etabs.set_point_restraint(point_name,
                                  UX=True, UY=True, UZ=True,
                                  RX=True, RY=True, RZ=True)

    # ==================== FRAMES - COLUMNAS ====================
    print("\n--- Creando Columnas ---")

    # Columnas primer nivel
    for i in range(2):
        for j in range(2):
            point_i = points_base[f"P{i}{j}_0"]
            point_j = points_p1[f"P{i}{j}_1"]
            etabs.add_frame(
                point_i=point_i,
                point_j=point_j,
                section_name="COL40x40"
            )

    # Columnas segundo nivel
    for i in range(2):
        for j in range(2):
            point_i = points_p1[f"P{i}{j}_1"]
            point_j = points_p2[f"P{i}{j}_2"]
            etabs.add_frame(
                point_i=point_i,
                point_j=point_j,
                section_name="COL40x40"
            )

    # ==================== FRAMES - VIGAS ====================
    print("\n--- Creando Vigas ---")

    # Vigas nivel 1 - dirección X
    for j in range(2):
        etabs.add_frame(
            point_i=points_p1[f"P0{j}_1"],
            point_j=points_p1[f"P1{j}_1"],
            section_name="VIG25x50"
        )

    # Vigas nivel 1 - dirección Y
    for i in range(2):
        etabs.add_frame(
            point_i=points_p1[f"P{i}0_1"],
            point_j=points_p1[f"P{i}1_1"],
            section_name="VIG25x50"
        )

    # Vigas nivel 2 - dirección X
    for j in range(2):
        etabs.add_frame(
            point_i=points_p2[f"P0{j}_2"],
            point_j=points_p2[f"P1{j}_2"],
            section_name="VIG25x50"
        )

    # Vigas nivel 2 - dirección Y
    for i in range(2):
        etabs.add_frame(
            point_i=points_p2[f"P{i}0_2"],
            point_j=points_p2[f"P{i}1_2"],
            section_name="VIG25x50"
        )

    # ==================== SLABS - LOSAS ====================
    print("\n--- Creando Losas ---")

    # Losa nivel 1 (usar losa maciza)
    points = [[0,0,H],
              [L,0,H],
              [L,B,H],
              [0,B,H]]

    slab_name = etabs.add_area_obj(points,'LOSA20')

    print(f"Losa nivel 1 '{slab_name}' creada")

    # Losa nivel 2 (usar losa nervada)
    points = [[0,0,2*H],
              [L,0,2*H],
              [L,B,2*H],
              [0,B,2*H]]
    
    slab_name = etabs.add_area_obj(points,'LOSA_NERV30')
    print(f"Losa nivel 2 '{slab_name}' creada (nervada)")

    # ==================== WALLS - MUROS ====================
    print("\n--- Creando Muros de Corte ---")

    # Muro en la dirección X (entre puntos P00 y P10, del nivel 0 al 2)
    points = [[0,0,0],
              [L,0,0],
              [L,0,2*H],
              [0,0,2*H]]
    
    wall_name = etabs.add_area_obj(points,'MURO25')
    print(f"Muro de corte '{wall_name}' creado")

    # ==================== PATRONES DE CARGA ====================
    print("\n--- Creando Patrones de Carga ---")

    # Carga muerta
    etabs.add_load_pattern("DEAD", pattern_type=1)

    # Carga viva
    etabs.add_load_pattern("LIVE", pattern_type=3)

    # Carga de viento
    etabs.add_load_pattern("WIND", pattern_type=5)

    # ==================== APLICAR CARGAS ====================
    print("\n--- Aplicando Cargas ---")

    # Obtener nombres de todas las áreas (losas)
    slab_list = etabs.floor_list

    # Carga muerta en losas (peso propio ya incluido)
    # Sobrecarga permanente: 1.5 kN/m²
    print("\nAplicando sobrecarga muerta en losas...")
    for area_name in slab_list:
        etabs.add_area_uniform_load(
            area_name=area_name,
            load_pattern="DEAD",
            value=-1.5,  # kN/m² (negativo = hacia abajo)
            direction=6  # Global Z
        )

    # Carga viva en losas: 2.0 kN/m²
    print("\nAplicando carga viva en losas...")
    for area_name in slab_list:
        etabs.add_area_uniform_load(
            area_name=area_name,
            load_pattern="LIVE",
            value=-2.0,  # kN/m²
            direction=6  # Global Z
        )

    # ==================== COMBINACIONES DE CARGA ====================
    print("\n--- Creando Combinaciones de Carga ---")

    # Combinación de servicio
    etabs.add_load_combo("SERVICIO", combo_type=0)  # Linear Add
    etabs.set_combo_case("SERVICIO", "DEAD", 1.0)
    etabs.set_combo_case("SERVICIO", "LIVE", 1.0)

    # Combinación de diseño (ACI 318)
    etabs.add_load_combo("DISEÑO_1", combo_type=0)
    etabs.set_combo_case("DISEÑO_1", "DEAD", 1.4)

    etabs.add_load_combo("DISEÑO_2", combo_type=0)
    etabs.set_combo_case("DISEÑO_2", "DEAD", 1.2)
    etabs.set_combo_case("DISEÑO_2", "LIVE", 1.6)

    # ==================== GUARDAR MODELO ====================
    print("\n--- Guardando Modelo ---")

    # Crear carpeta para modelos si no existe
    models_dir = os.path.join(os.path.dirname(__file__), "modelos")
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "edificio_simple.edb")
    etabs.save(model_path)
    print(f"Modelo guardado en: {model_path}")

    print("\n" + "=" * 60)
    print("MODELO COMPLETADO EXITOSAMENTE")
    print("=" * 60)

    # Refrescar la vista para mostrar el modelo actualizado
    etabs.refresh_view()

    # Preguntar si continuar ANTES de cerrar (para que el usuario pueda revisar el modelo)
    respuesta = input("\n¿Desea continuar con el siguiente ejemplo? (s/n): ")

    # Cerrar el modelo
    etabs.close()

    return respuesta.lower() == 's'


def ejemplo_secciones_frames():
    """
    Demuestra la creación de diversos tipos de secciones de frames
    """

    etabs = CSI()
    etabs.open_empty_instance(units='kN_m_C')

    print("\n" + "=" * 60)
    print("EJEMPLO: TIPOS DE SECCIONES DE FRAMES")
    print("=" * 60)

    # Materiales
    etabs.add_concrete_material("CONC30", fc=30*u.MPa)
    etabs.add_steel_material("A572")

    # Secciones de concreto
    print("\n--- Secciones de Concreto ---")
    etabs.add_rectangle_section("C-RECT-30x60", "CONC30", t3=0.60, t2=0.30)
    etabs.add_circle_section("C-CIRC-50", "CONC30", diameter=0.50)
    etabs.add_concrete_tee_section("C-TEE", "CONC30", t3=0.60, t2=0.40, tf=0.15, tw=0.20)

    # Secciones de acero
    print("\n--- Secciones de Acero ---")
    etabs.add_i_section("I-400x200", "A572", t3=0.40, t2=0.20, tf=0.015, tw=0.010)
    etabs.add_channel_section("CH-200x80", "A572", t3=0.20, t2=0.08, tf=0.012, tw=0.008)
    etabs.add_angle_section("ANG-100x100", "A572", t3=0.10, t2=0.10, tf=0.010, tw=0.010)
    etabs.add_pipe_section("PIPE-200x10", "A572", diameter=0.20, thickness=0.010)
    etabs.add_tube_section("TUBE-300x200", "A572", t3=0.30, t2=0.20, tf=0.012, tw=0.012)

    print("\nSecciones creadas exitosamente")

    # Refrescar la vista para mostrar el modelo actualizado
    etabs.refresh_view()

    # Preguntar si continuar ANTES de cerrar (para que el usuario pueda revisar el modelo)
    respuesta = input("\n¿Desea continuar con el siguiente ejemplo? (s/n): ")

    # Cerrar el modelo
    etabs.close()

    return respuesta.lower() == 's'


def ejemplo_secciones_areas():
    """
    Demuestra la creación de diversos tipos de secciones de áreas
    """

    etabs = CSI()
    etabs.open_empty_instance(units='kN_m_C')

    print("\n" + "=" * 60)
    print("EJEMPLO: TIPOS DE SECCIONES DE ÁREAS")
    print("=" * 60)

    # Material
    etabs.add_concrete_material("CONC28", fc=28*u.MPa)

    # Losas
    print("\n--- Losas ---")
    etabs.add_slab_section("LOSA-15", "CONC28", thickness=0.15, slab_type=0)
    etabs.add_slab_section("LOSA-20", "CONC28", thickness=0.20, slab_type=0)
    etabs.add_slab_section("LOSA-25", "CONC28", thickness=0.25, slab_type=0)

    # Losas especiales
    print("\n--- Losas Nervadas ---")
    etabs.add_ribbed_slab_section(
        "LOSA-NERV-25",
        "CONC28",
        overall_depth=0.25,
        slab_thickness=0.05,
        stem_width=0.10,
        rib_spacing=0.50,
        rib_direction=1
    )

    print("\n--- Losas Reticulares ---")
    etabs.add_waffle_slab_section(
        "LOSA-RET-30",
        "CONC28",
        overall_depth=0.30,
        slab_thickness=0.05,
        stem_width_dir1=0.15,
        stem_width_dir2=0.15,
        rib_spacing_dir1=0.70,
        rib_spacing_dir2=0.70
    )

    # Muros
    print("\n--- Muros ---")
    etabs.add_wall_section("MURO-15", "CONC28", thickness=0.15)
    etabs.add_wall_section("MURO-20", "CONC28", thickness=0.20)
    etabs.add_wall_section("MURO-30", "CONC28", thickness=0.30)

    print("\nSecciones creadas exitosamente")

    # Refrescar la vista para mostrar el modelo actualizado
    etabs.refresh_view()

    # Pausa para que el usuario pueda revisar el modelo
    input("\nPresione Enter para cerrar ETABS y finalizar...")

    # Cerrar el modelo
    etabs.close()

    return False


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║       EJEMPLOS DE USO DEL MÓDULO BUILDER - CSI_PY          ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Ejecutar ejemplos
    try:
        print("\n[1/3] Ejecutando: Edificio Simple...")
        continuar = ejemplo_edificio_simple()

        if continuar:
            print("\n[2/3] Ejecutando: Secciones de Frames...")
            continuar = ejemplo_secciones_frames()

        if continuar:
            print("\n[3/3] Ejecutando: Secciones de Áreas...")
            ejemplo_secciones_areas()

        print("\n" + "=" * 60)
        print("EJEMPLOS COMPLETADOS")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
