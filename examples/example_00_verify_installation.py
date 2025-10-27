"""
Ejemplo 0: Verificación de Instalación y Entry Points

Este ejemplo muestra:
- Cómo importar desde csi_py
- Verificar la instalación
- Usar las funciones utilitarias
- Información del paquete
"""

def main():
    print("=" * 60)
    print("CSI Python Library - Verificación de Instalación")
    print("=" * 60)
    
    # 1. Importar el paquete
    print("\n1. Importando csi_py...")
    try:
        import csi_py
        print("   ✓ Paquete importado correctamente")
    except ImportError as e:
        print(f"   ✗ Error al importar: {e}")
        return
    
    # 2. Información del paquete
    print("\n2. Información del paquete:")
    print(f"   - Versión: {csi_py.__version__}")
    print(f"   - Autor: {csi_py.__author__}")
    print(f"   - Licencia: {csi_py.__license__}")
    
    # 3. Programas soportados
    print("\n3. Programas soportados:")
    programs = csi_py.get_supported_programs()
    for prog in programs:
        print(f"   - {prog}")
    
    # 4. Unidades disponibles
    print("\n4. Unidades disponibles:")
    units = csi_py.get_available_units()
    for category, unit_list in units.items():
        print(f"   {category}:")
        for unit in unit_list:
            print(f"      - {unit}")
    
    # 5. Verificar imports principales
    print("\n5. Verificando imports principales:")
    components = [
        'CSIHandler',
        'get_paths',
        'get__pids',
        'validate_programs',
        'eUnits',
        'eFramePropType',
        'DataExtractor',
        'ModelBuilder',
        'EtabsError'
    ]
    
    for component in components:
        if hasattr(csi_py, component):
            print(f"   ✓ {component}")
        else:
            print(f"   ✗ {component} (no encontrado)")
    
    # 6. Verificar instancias activas
    print("\n6. Verificando instancias activas:")
    from csi_py import get__pids, get_paths
    
    for program in ['ETABS', 'SAP2000', 'SAFE']:
        try:
            pids = get__pids(program)
            if pids:
                print(f"   {program}:")
                paths = get_paths(program)
                for pid, path in paths.items():
                    print(f"      PID {pid}: {path}")
            else:
                print(f"   {program}: No hay instancias activas")
        except Exception as e:
            print(f"   {program}: Error al verificar ({e})")
    
    # 7. Ejemplo de uso básico
    print("\n7. Ejemplo de uso básico:")
    print("""
    from csi_py import CSIHandler
    
    # Crear handler
    model = CSIHandler(program='ETABS', units='kN_m_C')
    
    # Conectar a instancia abierta
    model.connect_open_instance()
    
    # Trabajar con el modelo
    print(f"Conectado a: {model.file_name}")
    
    # Cerrar
    model.close()
    """)
    
    print("\n" + "=" * 60)
    print("Verificación completada")
    print("=" * 60)
    print("\nPara más ejemplos, ver la carpeta 'examples/'")
    print("Para guía rápida, ver QUICKSTART.md")

if __name__ == "__main__":
    main()
