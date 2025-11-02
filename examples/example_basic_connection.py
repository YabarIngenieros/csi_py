"""
Ejemplo 1: Conexión Básica y Exploración de Modelo

Este ejemplo muestra cómo:
- Conectar a una instancia abierta de ETABS/SAP2000
- Obtener información básica del modelo
- Listar elementos principales
"""

from handler import CSIHandler, get_paths

def main():
    # Ver qué archivos están abiertos actualmente
    print("=== Archivos ETABS Abiertos ===")
    paths = get_paths('ETABS')
    for pid, path in paths.items():
        print(f"PID {pid}: {path}")
    print()
    
    # Crear handler y conectar
    handler = CSIHandler(program='ETABS', units='kN_m_C')
    
    try:
        # Conectar a la instancia activa
        handler.connect_open_instance()
        
        # Información básica
        print(f"Conectado a: {handler.file_name}")
        print(f"Ruta completa: {handler.file_path}")
        print()
        
        # Obtener información del modelo
        print("=== Información del Modelo ===")
        
        # Número de elementos (si el modelo tiene el método disponible)
        try:
            num_points = handler.model.PointObj.Count()
            num_frames = handler.model.FrameObj.Count()
            num_areas = handler.model.AreaObj.Count()
            
            print(f"Puntos: {num_points}")
            print(f"Frames: {num_frames}")
            print(f"Áreas: {num_areas}")
        except:
            print("No se pudo obtener conteo de elementos")
        
        print("\nConexión exitosa!")
        
    except ConnectionError as e:
        print(f"Error de conexión: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        # Cerrar la conexión
        if handler.object is not None:
            handler.close()

if __name__ == "__main__":
    main()
