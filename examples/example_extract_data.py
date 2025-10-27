"""
Ejemplo 3: Extracción de Datos de un Modelo Existente

Este ejemplo muestra cómo:
- Conectar a un modelo existente
- Extraer información de geometría
- Extraer propiedades de materiales y secciones
- Exportar datos a archivos CSV
"""

from handler import CSIHandler
import pandas as pd
import os

def extract_model_data():
    """
    Extrae datos completos de un modelo ETABS abierto
    """
    
    handler = CSIHandler(program='ETABS', units='kN_m_C')
    
    try:
        # Conectar a instancia abierta
        print("=== Conectando al Modelo ===")
        handler.connect_open_instance()
        print(f"Conectado a: {handler.file_name}\n")
        
        # Crear directorio para exportar datos
        output_dir = "extracted_data"
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. EXTRAER PUNTOS
        print("=== Extrayendo Puntos ===")
        try:
            num_points = handler.model.PointObj.Count()
            
            points_data = []
            for i in range(num_points):
                name = handler.model.PointObj.GetNameList()[1][i]
                coords = handler.model.PointObj.GetCoordCartesian(name)
                
                # Obtener restricciones
                restraints = handler.model.PointObj.GetRestraint(name)
                
                points_data.append({
                    'Point': name,
                    'X': coords[1],
                    'Y': coords[2],
                    'Z': coords[3],
                    'UX': restraints[1][0],
                    'UY': restraints[1][1],
                    'UZ': restraints[1][2],
                    'RX': restraints[1][3],
                    'RY': restraints[1][4],
                    'RZ': restraints[1][5]
                })
            
            df_points = pd.DataFrame(points_data)
            csv_file = os.path.join(output_dir, 'points.csv')
            df_points.to_csv(csv_file, index=False)
            print(f"✓ {len(points_data)} puntos extraídos → {csv_file}")
            print(df_points.head())
            print()
        except Exception as e:
            print(f"✗ Error extrayendo puntos: {e}\n")
        
        # 2. EXTRAER FRAMES
        print("=== Extrayendo Frames ===")
        try:
            num_frames = handler.model.FrameObj.Count()
            
            frames_data = []
            for i in range(num_frames):
                name = handler.model.FrameObj.GetNameList()[1][i]
                
                # Puntos de conexión
                points = handler.model.FrameObj.GetPoints(name)
                
                # Sección asignada
                section = handler.model.FrameObj.GetSection(name)[1]
                
                # Material de la sección
                try:
                    mat_prop = handler.model.PropFrame.GetMaterial(section)
                    material = mat_prop[1]
                except:
                    material = "N/A"
                
                frames_data.append({
                    'Frame': name,
                    'PointI': points[1],
                    'PointJ': points[2],
                    'Section': section,
                    'Material': material
                })
            
            df_frames = pd.DataFrame(frames_data)
            csv_file = os.path.join(output_dir, 'frames.csv')
            df_frames.to_csv(csv_file, index=False)
            print(f"✓ {len(frames_data)} frames extraídos → {csv_file}")
            print(df_frames.head())
            print()
        except Exception as e:
            print(f"✗ Error extrayendo frames: {e}\n")
        
        # 3. EXTRAER MATERIALES
        print("=== Extrayendo Materiales ===")
        try:
            num_materials = handler.model.PropMaterial.Count()
            
            materials_data = []
            for i in range(num_materials):
                name = handler.model.PropMaterial.GetNameList()[1][i]
                
                # Propiedades del material
                mat_type = handler.model.PropMaterial.GetMaterial(name)[1]
                
                try:
                    iso_props = handler.model.PropMaterial.GetMPIsotropic(name)
                    E = iso_props[1]
                    U = iso_props[2]
                    A = iso_props[3]
                except:
                    E = U = A = None
                
                try:
                    weight = handler.model.PropMaterial.GetWeightAndMass(name)[2]
                except:
                    weight = None
                
                materials_data.append({
                    'Material': name,
                    'Type': mat_type,
                    'E': E,
                    'Poisson': U,
                    'ThermalCoeff': A,
                    'Weight': weight
                })
            
            df_materials = pd.DataFrame(materials_data)
            csv_file = os.path.join(output_dir, 'materials.csv')
            df_materials.to_csv(csv_file, index=False)
            print(f"✓ {len(materials_data)} materiales extraídos → {csv_file}")
            print(df_materials)
            print()
        except Exception as e:
            print(f"✗ Error extrayendo materiales: {e}\n")
        
        # 4. EXTRAER SECCIONES DE FRAMES
        print("=== Extrayendo Secciones de Frames ===")
        try:
            num_sections = handler.model.PropFrame.Count()
            
            sections_data = []
            for i in range(num_sections):
                name = handler.model.PropFrame.GetNameList()[1][i]
                
                # Tipo de sección
                prop_type = handler.model.PropFrame.GetType(name)[1]
                
                # Material
                try:
                    material = handler.model.PropFrame.GetMaterial(name)[1]
                except:
                    material = "N/A"
                
                sections_data.append({
                    'Section': name,
                    'Type': prop_type,
                    'Material': material
                })
            
            df_sections = pd.DataFrame(sections_data)
            csv_file = os.path.join(output_dir, 'frame_sections.csv')
            df_sections.to_csv(csv_file, index=False)
            print(f"✓ {len(sections_data)} secciones extraídas → {csv_file}")
            print(df_sections.head())
            print()
        except Exception as e:
            print(f"✗ Error extrayendo secciones: {e}\n")
        
        # 5. EXTRAER PATRONES DE CARGA
        print("=== Extrayendo Patrones de Carga ===")
        try:
            num_patterns = handler.model.LoadPatterns.Count()
            
            patterns_data = []
            for i in range(num_patterns):
                name = handler.model.LoadPatterns.GetNameList()[1][i]
                load_type = handler.model.LoadPatterns.GetLoadType(name)[1]
                
                patterns_data.append({
                    'Pattern': name,
                    'Type': load_type
                })
            
            df_patterns = pd.DataFrame(patterns_data)
            csv_file = os.path.join(output_dir, 'load_patterns.csv')
            df_patterns.to_csv(csv_file, index=False)
            print(f"✓ {len(patterns_data)} patrones de carga extraídos → {csv_file}")
            print(df_patterns)
            print()
        except Exception as e:
            print(f"✗ Error extrayendo patrones: {e}\n")
        
        print("=== Extracción Completada ===")
        print(f"Datos guardados en: {os.path.abspath(output_dir)}")
        
    except ConnectionError as e:
        print(f"Error de conexión: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if handler.object is not None:
            handler.close()

if __name__ == "__main__":
    extract_model_data()
