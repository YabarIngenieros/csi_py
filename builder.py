from .constants import eMatType,u
import numpy as np

import pandas as pd

# funciones auxiliares
def is_ccw(points):
    """
    Verifica si los puntos 3D están en sentido antihorario (CCW)
    usando solo las dos primeras coordenadas (x, y).
    points: lista de [(x,y,z), ...] o [(x,y), ...]
    """
    area = 0.0
    n = len(points)

    for i in range(n):
        x1, y1 = points[i][0], points[i][1]
        x2, y2 = points[(i + 1) % n][0], points[(i + 1) % n][1]
        area += (x2 - x1) * (y2 + y1)

    return area < 0
class ModelBuilder:
    '''Mixin de modelamiento con API de ETABS'''  
    def __init__(self):
        super().__init__()
        self._section_definitions_table = None
        self._tee_section_table = None
        
    # Tables
    def apply_edited_table(self):
        apply_result = self.model.DatabaseTables.ApplyEditedTables(True)
        num_fatal, num_errors, num_warnings, num_info = apply_result[1:5]

        if num_fatal > 0 or num_errors > 0:
            msg = (
                f"Errores al aplicar cambios:\n"
                f"   Fatal: {num_fatal}, Errores: {num_errors}\n"
                f"   Advertencias: {num_warnings}, Info: {num_info}"
            )
            if apply_result[0]:
                msg += f"\n   Log: {apply_result[5]}"
            raise RuntimeError(msg)
        else:
            import warnings
            if num_warnings > 0:
                warnings.warn(f"Advertencias: {num_warnings}", RuntimeWarning)
                
        return 0
    
    def get_editable_table(self,name,columns):
        if name in self.available_tables['Table'].values:
            version,table = self.get_table(name,to_edit=True)
        else:
            version = 1
            table = pd.DataFrame(columns=columns)
        return version,table
    
    def set_table(self, table_name, table:'pd.DataFrame', table_version=1, apply=True):
        """
        Modifica una tabla en ETABS

        Parameters:
        -----------
        table_name : str
            Nombre de la tabla a modificar
        table : pd.DataFrame
            DataFrame con los datos modificados
        table_version : int
            Versión de la tabla (obtenida de get_table con to_edit=True)

        Returns:
        --------
        tuple: (flag, TableVersion, FieldsKeysIncluded, NumberRecords)
        """
        columns = list(table.columns)
        data = table.values
        n_records = data.shape[0]
        # Aplanar los datos a una lista 1D
        data = list(data.flatten())

        # Enviar la tabla modificada
        self.model.DatabaseTables.SetTableForEditingArray(
            table_name, table_version, columns, n_records, data
        )
        if apply:
            return self.apply_edited_table()
        else:
            return 0
        
    # ================== GRIDS ================================
    def set_grid_sitem(self,X:list,Y:list,spacing=True):
        table_name_1 = 'Grid Definitions - General'
        table_1:pd.DataFrame # hint
        version, table_1 = self.get_table(table_name_1,to_edit=True)
        
        if table_1.empty:
            row = ['T1','G1','Cartesian','0','0','0','Default','','',
                    '','','']
            table_1.loc[0] = row
            self.set_table(table_name_1,table_1,version,apply=True)
            
        table_name_2 = 'Grid Definitions - Grid Lines'
        # reiniciar tabla
        version,table_2 = self.get_table(table_name_2,to_edit=True)
        table_2.drop(table_2.index, inplace=True)
        if spacing:
            X = np.array([0]+X).cumsum()
            Y = np.array([0]+Y).cumsum()
        for x,ID in zip(X,['A','B','C','D','E','F','G','H','I','J','K','L','M']):
            row = ['G1','X (Cartesian)',ID,f'{x}','','','','','','End','Yes']
            table_2.loc[len(table_2)] = row
            
        for i,y in enumerate(Y):
            row = ['G1','Y (Cartesian)',f'{i+1}',f'{y}','','','','','','End','Yes']
            table_2.loc[len(table_2)] = row
            
        self.set_table(table_name_2,table_2,version,apply=True)
            
        
    # ===================== POINTS =============================
    def add_point(self,x,y,z):
        point = self.model.PointObj.AddCartesian(x,y,z)
        if point[-1]!=0:
            raise RuntimeError(f"Error ETABS al crear punto en ({x}, {y}, {z})")
        return point[0]
        
    # ==================== LOAD COMBINATIONS ====================
    
    def add_load_combo(self, combo_name, combo_type=0):
        """
        Añade una combinación de carga
        
        Parameters:
        -----------
        combo_name : str
            Nombre de la combinación
        combo_type : int
            Tipo (0=Linear Add, 1=Envelope, 2=Absolute Add, etc.)
        """
        self.model.RespCombo.Add(combo_name, combo_type)
        print(f"Combinación de carga '{combo_name}' añadida")
    
    def set_combo_case(self, combo_name, case_name, scale_factor):
        """
        Añade un caso a una combinación con su factor
        
        Parameters:
        -----------
        combo_name : str
            Nombre de la combinación
        case_name : str
            Nombre del caso
        scale_factor : float
            Factor de escala
        """
        self.model.RespCombo.SetCaseList(combo_name, 0, case_name, scale_factor)
        print(f"Caso '{case_name}' añadido a combo '{combo_name}' con factor {scale_factor}")
     
    # ==================== MATERIALS ====================
    
    def add_material(self, 
                     material_name:str, 
                     material_type:eMatType, 
                     E:float, U:float, A:float, 
                     mass_per_volume:float):
        """
        Añade un material al modelo
        
        Parameters:
        -----------
        material_name : str
            Nombre del material
        material_type : int
            Tipo de material (1=Steel, 2=Concrete, 3=NoDesign, etc.)
        E : float
            Módulo de elasticidad
        U : float
            Relación de Poisson
        A : float
            Coeficiente de expansión térmica
        weight_per_volume : float
            Peso por unidad de volumen
        """
        self.model.PropMaterial.SetMaterial(material_name, material_type)
        self.model.PropMaterial.SetMPIsotropic(material_name, E, U, A)
        self.model.PropMaterial.SetWeightAndMass(material_name, 2, mass_per_volume)
        print(f"Material '{material_name}' añadido")
        
    def add_uniaxial_material(self, 
                          material_name: str, 
                          material_type: eMatType, 
                          E: float, 
                          A: float,
                          mass_per_volume: float):
        """
        Añade un material uniaxial al modelo (para elementos tipo cable, tendón, etc.)
        
        Parameters:
        -----------
        material_name : str
            Nombre del material
        material_type : eMatType
            Tipo de material (1=Steel, 2=Concrete, 3=NoDesign, etc.)
        E : float
            Módulo de elasticidad
        A : float
            Coeficiente de expansión térmica
        mass_per_volume : float
            Peso por unidad de volumen
        """
        self.model.PropMaterial.SetMaterial(material_name, material_type)
        self.model.PropMaterial.SetMPUniaxial(material_name, E, A)
        self.model.PropMaterial.SetWeightAndMass(material_name, 2, mass_per_volume)
        print(f"Material uniaxial '{material_name}' añadido")
        
    def add_concrete_material(self,name,fc=21*u.MPa,
                              E=None,U=0.15,A=0.0000099,
                              mass_per_volume=2400*u.kg/u.m**3):
        if (u.system == 'SI') and (E is None):
            E = 4700*(fc*u.MPa)**0.5
            print(E/(u.kgf/u.m**3))
        elif (u.system == 'MKS') and (E is None):
            E = 15000*(fc*u.kgf)**0.5
            print(E/(u.kgf/u.m**3))
        elif E is None:
            raise NotImplementedError('Cálculo del módulo de Elasticidad no Implementado')
            
        return self.add_material(name,eMatType.Concrete,
                                E,U,A,mass_per_volume)
        
    def add_steel_material(self,name,E=2e5*u.MPa,
                           U=0.30,A=0.0000117,
                           mass_per_volume=7850*u.kg/u.m**3):
        return self.add_material(name,eMatType.Steel,
                                E,U,A,mass_per_volume)
        
    def add_rebar_material(self,name,E=2e5*u.MPa,
                           A=0.0000117,
                           mass_per_volume=7850*u.kg/u.m**3):
        return self.add_uniaxial_material(name,eMatType.Rebar,
                                E,A,mass_per_volume)
        
    def set_point_restraint(self, point_name, UX=True, UY=True,
                        UZ=True, RX=True, RY=True, RZ=True):
        """
        Define restricciones en un punto
        
        Parameters:
        -----------
        point_name : str
            Nombre del punto
        UX, UY, UZ : bool
            Restricciones de traslación
        RX, RY, RZ : bool
            Restricciones de rotación
        """
        restraints = [UX, UY, UZ, RX, RY, RZ]
        self.model.PointObj.SetRestraint(point_name, restraints)
        print(f"Restricciones aplicadas a punto '{point_name}'")
        
    # ==================== FRAMES ====================
    
    def add_rectangle_section(self,section_name, material_name, t3, t2):
        """
        Crea una sección rectangular sólida
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la sección (profundidad)
        t2 : float
            Ancho de la sección
        """
        self.model.PropFrame.SetRectangle(section_name, material_name, t3, t2)
        # SetRebarBeam / SetRebarColumn
        print(f"Sección rectangular '{section_name}' añadida: {t2} x {t3}")
        
    def add_circle_section(self, section_name, material_name, diameter):
        """
        Crea una sección circular sólida
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        diameter : float
            Diámetro de la sección
        """
        self.model.PropFrame.SetCircle(section_name, material_name, diameter)
        print(f"Sección circular '{section_name}' añadida: ø{diameter}")
        
    def add_pipe_section(self, section_name, material_name, diameter, thickness):
        """
        Crea una sección tipo tubo (pipe)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        diameter : float
            Diámetro exterior
        thickness : float
            Espesor de pared
        """
        self.model.PropFrame.SetPipe(section_name, material_name, diameter, thickness)
        print(f"Sección pipe '{section_name}' añadida: ø{diameter}, t={thickness}")
        
    def add_tube_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección tipo tubo rectangular (HSS)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura exterior
        t2 : float
            Ancho exterior
        tf : float
            Espesor de ala
        tw : float
            Espesor de alma
        """
        self.model.PropFrame.SetTube(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección tube '{section_name}' añadida: {t2} x {t3}, tf={tf}, tw={tw}")
        
    def add_i_section(self, section_name, material_name, t3, t2, tf, tw, t2b=None, tfb=None):
        """
        Crea una sección tipo I
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura total de la sección
        t2 : float
            Ancho del ala superior
        tf : float
            Espesor del ala superior
        tw : float
            Espesor del alma
        t2b : float, optional
            Ancho del ala inferior (si None, usa t2)
        tfb : float, optional
            Espesor del ala inferior (si None, usa tf)
        """
        if t2b is None:
            t2b = t2
        if tfb is None:
            tfb = tf
        
        self.model.PropFrame.SetISection(section_name, material_name, t3, t2, tf, tw, t2b, tfb)
        print(f"Sección I '{section_name}' añadida: h={t3}, bf={t2}/{t2b}, tf={tf}/{tfb}, tw={tw}")
        
    def add_channel_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección tipo canal (C)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la sección
        t2 : float
            Ancho del ala
        tf : float
            Espesor del ala
        tw : float
            Espesor del alma
        """
        self.model.PropFrame.SetChannel(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección canal '{section_name}' añadida: h={t3}, bf={t2}, tf={tf}, tw={tw}")
        
    def add_tee_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección tipo T
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la sección
        t2 : float
            Ancho del ala
        tf : float
            Espesor del ala
        tw : float
            Espesor del alma
        """
        self.model.PropFrame.SetTee(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección T '{section_name}' añadida: h={t3}, bf={t2}, tf={tf}, tw={tw}")
        
    def add_angle_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección tipo ángulo (L)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura del ángulo
        t2 : float
            Ancho del ángulo
        tf : float
            Espesor de la pierna vertical
        tw : float
            Espesor de la pierna horizontal
        """
        self.model.PropFrame.SetAngle(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección ángulo '{section_name}' añadida: {t3} x {t2}, tf={tf}, tw={tw}")
        
    def add_double_angle_section(self, section_name, material_name, t3, t2, tf, tw, dis):
        """
        Crea una sección de doble ángulo
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura del ángulo
        t2 : float
            Ancho del ángulo
        tf : float
            Espesor de la pierna vertical
        tw : float
            Espesor de la pierna horizontal
        dis : float
            Separación entre ángulos
        """
        self.model.PropFrame.SetDblAngle(section_name, material_name, t3, t2, tf, tw, dis)
        print(f"Sección doble ángulo '{section_name}' añadida: 2L {t3}x{t2}, sep={dis}")
        
    def add_double_channel_section(self, section_name, material_name, t3, t2, tf, tw, dis):
        """
        Crea una sección de doble canal
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la canal
        t2 : float
            Ancho del ala
        tf : float
            Espesor del ala
        tw : float
            Espesor del alma
        dis : float
            Separación entre canales
        """
        self.model.PropFrame.SetDblChannel(section_name, material_name, t3, t2, tf, tw, dis)
        print(f"Sección doble canal '{section_name}' añadida: 2C h={t3}, sep={dis}")
        
    def add_concrete_box_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección cajón de concreto
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura exterior
        t2 : float
            Ancho exterior
        tf : float
            Espesor de losa superior/inferior
        tw : float
            Espesor de almas
        """
        self.model.PropFrame.SetConcreteBox(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección cajón concreto '{section_name}' añadida: {t2}x{t3}, tf={tf}, tw={tw}")
        
    def add_concrete_tee_section(self, section_name, material_name, t3, t2, tf, tw, twt=None, mirror=False):
        """
        Crea una sección T de concreto

        Parameters:
        -----------
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura total
        t2 : float
            Ancho del ala
        tf : float
            Espesor del ala
        tw : float
            Espesor del alma (inferior)
        twt : float, optional
            Espesor del alma superior (si None, usa tw)
        mirror : bool, optional
            Si True, refleja la sección sobre el eje 3 (default: False)
        """
        if twt is None:
            twt = tw
        self.model.PropFrame.SetConcreteTee(section_name, material_name, t3, t2, tf, tw, twt, mirror)
        print(f"Sección T concreto '{section_name}' añadida: h={t3}, bf={t2}")
        
    def add_concrete_L_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección L de concreto
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura
        t2 : float
            Ancho
        tf : float
            Espesor vertical
        tw : float
            Espesor horizontal
        """
        self.model.PropFrame.SetConcreteL(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección L concreto '{section_name}' añadida: {t3}x{t2}")
        
    def add_concrete_pipe_section(self, section_name, material_name, diameter, thickness):
        """
        Crea una sección tubo de concreto
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        diameter : float
            Diámetro exterior
        thickness : float
            Espesor de pared
        """
        self.model.PropFrame.SetConcretePipe(section_name, material_name, diameter, thickness)
        print(f"Sección tubo concreto '{section_name}' añadida: ø{diameter}, t={thickness}")
        
    def add_concrete_cross_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección tipo cruz de concreto
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura total
        t2 : float
            Ancho total
        tf : float
            Espesor del ala
        tw : float
            Espesor del alma
        """
        self.model.PropFrame.SetConcreteCross(section_name, material_name, t3, t2, tf, tw)
        print(f"Sección cruz concreto '{section_name}' añadida: {t2}x{t3}")
        
    def add_plate_section(self, section_name, material_name, thickness):
        """
        Crea una sección tipo placa sólida
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        thickness : float
            Espesor de la placa
        """
        self.model.PropFrame.SetPlate(section_name, material_name, thickness)
        print(f"Sección placa '{section_name}' añadida: t={thickness}")
        
    def add_rod_section(self, section_name, material_name, diameter):
        """
        Crea una sección tipo varilla sólida
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        diameter : float
            Diámetro de la varilla
        """
        self.model.PropFrame.SetRod(section_name, material_name, diameter)
        print(f"Sección varilla '{section_name}' añadida: ø{diameter}")
        
    def add_cold_formed_c_section(self, section_name, material_name, t3, t2, thickness, lip):
        """
        Crea una sección C de acero conformado en frío
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la sección
        t2 : float
            Ancho del ala
        thickness : float
            Espesor
        lip : float
            Longitud del labio
        """
        self.model.PropFrame.SetColdC(section_name, material_name, t3, t2, thickness, lip)
        print(f"Sección C conformada '{section_name}' añadida: h={t3}, bf={t2}, t={thickness}")
        
    def add_cold_formed_z_section(self, section_name, material_name, t3, t2, thickness, lip):
        """
        Crea una sección Z de acero conformado en frío
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la sección
        t2 : float
            Ancho del ala
        thickness : float
            Espesor
        lip : float
            Longitud del labio
        """
        self.model.PropFrame.SetColdZ(section_name, material_name, t3, t2, thickness, lip)
        print(f"Sección Z conformada '{section_name}' añadida: h={t3}, bf={t2}, t={thickness}")
        
    def add_cold_formed_hat_section(self, section_name, material_name, t3, t2, thickness):
        """
        Crea una sección Hat de acero conformado en frío
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        t3 : float
            Altura de la sección
        t2 : float
            Ancho total
        thickness : float
            Espesor
        """
        self.model.PropFrame.SetColdHat(section_name, material_name, t3, t2, thickness)
        print(f"Sección Hat conformada '{section_name}' añadida: h={t3}, b={t2}, t={thickness}")
        
    def add_frame_section(self, section_name, material_name, section_type, **kwargs):
        """
        Función unificada para añadir cualquier tipo de sección
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        section_type : str
            Tipo de sección (ver SECTION_FUNCTIONS keys)
        **kwargs : dict
            Parámetros específicos del tipo de sección
        
        Examples:
        ---------
        # Sección rectangular
        add_frame_section('SEC1', 'CONC25', 'Rectangle', t3=0.5, t2=0.3)
        
        # Sección I
        add_frame_section('SEC2', 'A36', 'I', t3=0.6, t2=0.2, tf=0.02, tw=0.01)
        
        # Sección circular
        add_frame_section('SEC3', 'A36', 'Circle', diameter=0.3)
        """
        # Diccionario de mapeo de funciones
        SECTION_FUNCTIONS = {
            'Rectangle': self.add_rectangle_section,
            'Circle': self.add_circle_section,
            'Pipe': self.add_pipe_section,
            'Tube': self.add_tube_section,
            'I': self.add_i_section,
            'Channel': self.add_channel_section,
            'Tee': self.add_tee_section,
            'Angle': self.add_angle_section,
            'DoubleAngle': self.add_double_angle_section,
            'DoubleChannel': self.add_double_channel_section,
            'ConcreteBox': self.add_concrete_box_section,
            'ConcreteTee': self.add_concrete_tee_section,
            'ConcreteL': self.add_concrete_L_section,
            'ConcretePipe': self.add_concrete_pipe_section,
            'ConcreteCross': self.add_concrete_cross_section,
            'Plate': self.add_plate_section,
            'Rod': self.add_rod_section,
            'ColdC': self.add_cold_formed_c_section,
            'ColdZ': self.add_cold_formed_z_section,
            'ColdHat': self.add_cold_formed_hat_section,
        }

        
        if section_type not in SECTION_FUNCTIONS:
            available = ', '.join(SECTION_FUNCTIONS.keys())
            raise ValueError(f"Tipo de sección '{section_type}' no válido. Disponibles: {available}")
        
        func = SECTION_FUNCTIONS[section_type]
        func(section_name, material_name, **kwargs)
        
    def apply_tee_sections(self,version_1=1,version_2=1):
        table_1 = 'Frame Section Property Definitions - Section Designer'
        table_2 = 'Section Designer Shapes - Concrete Tee'
        if self._section_definitions_table is None:
            version_1,self._section_definitions_table = self.get_table(table_1,to_edit=True)
        if self._tee_section_table is None: # No hay cambios a aplicar
            return
        self.set_table(table_1,self._section_definitions_table,version_1,apply=False)
        self.set_table(table_2,self._tee_section_table,version_2,apply=False)
        self.apply_edited_table()
        self._section_definitions_table = None
        self._tee_section_table = None
        
    def add_tee_SD_sections(self,name,material,height,width,thick,apply=False):
        # Comprobar compatibilidad de los datos
        vals = [name, height, width, thick]   # obligatorios
        if isinstance(material, (list,tuple)): 
            vals += [material] # si material es definido como lista o tupla

        # Si alguno es lista/tupla → todos los obligatorios deben serlo
        is_seq = [isinstance(v, (list, tuple)) for v in vals]

        if any(is_seq) and not all(is_seq):
            raise TypeError("No se colocaron datos compatibles")

        # Si son listas/tuplas → misma longitud
        if all(is_seq):
            lengths = {len(v) for v in vals} # set
            if len(lengths) != 1:
                raise ValueError("Los datos ingresados deben tener la misma longitud")
            
        if not isinstance(name,(list,tuple)):
            name = [name]; height = [height]; width = [width]
            thick = [thick]; material = [material]
        if not isinstance(material,(list,tuple)):
            material = [material]*len(name)

        # Tabla 1
        table_1 = 'Frame Section Property Definitions - Section Designer'
        '''
        columns_1 = ['Name', 'Material', 'DesignType', 'IsDesigned', 'NotSizeType',
                'NotAutoFact', 'NotUserSize', 'AMod', 'A2Mod', 'A3Mod', 'JMod', 'I2Mod',
                'I3Mod', 'MMod', 'WMod', 'Color', 'GUID', 'Notes']
        '''
            
        if self._section_definitions_table is None:
            version_1,table = self.get_table(table_1,to_edit=True)
        else:
            version_1=1
            table = self._section_definitions_table
        
        for n, mat in zip(name,material):
            row_add = [n,mat,'Concrete Column','Yes','Auto','1','']\
                +['1']*8 + ['','','']
            if n in table['Name'].values:
                table[table['Name']==n] = row_add
            else:
                table.loc[len(table)] = row_add
        
        self._section_definitions_table = table
    
        # Tabla 2
        table_2 = 'Section Designer Shapes - Concrete Tee'
        '''
        columns_2 = ['SectionType', 'SectionName', 'ShapeName', 'Material', 'XCenter',
                'YCenter', 'Rotation', 'MirrorAbt3', 'Height', 'Width', 'FlangeThick',
                'WebThick', 'Reinforcing', 'RebarMat', 'Color', 'ZOrder']
        '''
        
        if self._tee_section_table is None:
            version_2,table = self.get_table(table_2,to_edit=True)
        else:
            version_2 = 1
            table = self._tee_section_table
        
        for n,mat,h,w,t in zip(name,material,height,width,thick):
            data_2 = ['Frame',n,'ConcTee1',mat]+['0']*3+\
                ['No',f'{h}',f'{w}',f'{t}',f'{t}',
                 'No','','','1']
            if n in table['SectionName'].values:
                table[table['SectionName']==n] = data_2
            else:
                table.loc[len(table)] = data_2
            
        self._tee_section_table = table
            
        if apply:
            self.apply_tee_sections(version_1,version_2)
    
    def add_line_bar_to_section(self,section_name,material,p1,p2,size,max_spacing,end_bars='Yes'):
        table_name = 'Section Designer Shapes - Reinforcing - Line Bar'
        columns = ['SectionType', 'SectionName', 'ShapeName', 'Material', 'X1', 'Y1', 'X2',
       'Y2', 'RebarSize', 'Area', 'HasEndBars', 'LayoutType', 'MaxSpacing',
       'NumberBars', 'ZOrder']
        
        version,table = self.get_editable_table(table_name,columns)
        
        if not table.empty:
            shape_name = max(table['ShapeName'].values)
            shape_name = shape_name[:-1] + str(int(shape_name[-1])+1)
        else:
            shape_name = 'LineBar1'
        
        data = ['Frame',section_name,shape_name,material,f'{p1[0]}',f'{p1[1]}',
                f'{p2[0]}',f'{p2[1]}',f'{size}','',end_bars.capitalize(),'Spacing',
                f"{max_spacing}",'','2']
        table.loc[len(table)] = data
        
        self.set_table(table_name,table,version,apply=True)
                
    def add_frame(self,  point_i, point_j, section_name):
        """
        Añade un frame entre dos puntos
        
        Parameters:
        -----------
        frame_name : str
            Nombre del frame
        point_i : str
            Punto inicial
        point_j : str
            Punto final   
        section_name : str
            Sección asignada
        """
        frame_name = self.model.FrameObj.AddByPoint(point_i, point_j)[0]
        self.model.FrameObj.SetSection(frame_name, section_name)
        print(f"Frame '{frame_name}' añadido entre '{point_i}' y '{point_j}'")
        
    # ==================== SLABS (LOSAS) ====================

    def add_slab_section(self, section_name, material_name, thickness, 
                        slab_type=0, shell_type=1):
        """
        Crea una sección de losa básica
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la losa
        thickness : float
            Espesor de la losa
        slab_type : int, default 0
            Tipo de losa:
            - 0 = Slab 
            - 1 = Drop 
            - 2 = Mat 
            - 3 = Footing 
        shell_type : int, default 1
            Tipo de shell:
            - 1 = Shell-thin
            - 2 = Shell-thick
        """
        self.model.PropArea.SetSlab(section_name, slab_type, shell_type, 
                            material_name, thickness)
        slab_types = {0: 'Slab', 1: 'Drop', 2: 'Mat', 3: 'Footing'}
        print(f"Sección de losa '{section_name}' añadida: t={thickness} ({slab_types.get(slab_type, 'Unknown')})")


    def add_ribbed_slab_section(self, section_name, material_name,
                                overall_depth, slab_thickness, stem_width,
                                rib_spacing, rib_direction=1):
        """
        Crea una sección de losa nervada (ribbed slab)
        NOTA: Esta función requiere DOS llamadas a la API

        Parameters:
        -----------
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la losa
        overall_depth : float
            Altura total de la losa (incluyendo nervios)
        slab_thickness : float
            Espesor de la losa superior
        stem_width : float
            Ancho de los nervios
        rib_spacing : float
            Espaciamiento entre nervios (centro a centro)
        rib_direction : int, default 1
            Dirección de los nervios:
            - 1 = Parallel to local 1 axis
            - 2 = Parallel to local 2 axis
        """
        # Inicializar como slab básico
        self.model.PropArea.SetSlab(section_name, 0, 1, material_name, overall_depth)

        # Configurar como ribbed
        self.model.PropArea.SetSlabRibbed(
            section_name,
            overall_depth,
            slab_thickness,
            stem_width,  # StemWidthTop (ancho superior del nervio)
            stem_width,  # StemWidthBot (ancho inferior del nervio)
            rib_spacing,
            rib_direction  # RibsParallelTo: 1 = local 1, 2 = local 2
        )

        direction_str = "Local 1" if rib_direction == 1 else "Local 2"
        print(f"Sección de losa nervada '{section_name}' añadida:")
        print(f"  - Altura total: {overall_depth}")
        print(f"  - Espesor losa: {slab_thickness}")
        print(f"  - Ancho nervio: {stem_width}")
        print(f"  - Espaciamiento: {rib_spacing}")
        print(f"  - Nervios paralelos a: {direction_str}")


    def add_waffle_slab_section(self, section_name, material_name,
                                overall_depth, slab_thickness, stem_width_dir1, 
                                stem_width_dir2, rib_spacing_dir1, rib_spacing_dir2):
        """
        Crea una sección de losa reticular/waffle (losa nervada en dos direcciones)
        NOTA: Esta función requiere DOS llamadas a la API
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la losa
        overall_depth : float
            Altura total de la losa
        slab_thickness : float
            Espesor de la losa superior
        stem_width_dir1 : float
            Ancho de nervios en dirección 1
        stem_width_dir2 : float
            Ancho de nervios en dirección 2
        rib_spacing_dir1 : float
            Espaciamiento de nervios en dirección 1 (c/c)
        rib_spacing_dir2 : float
            Espaciamiento de nervios en dirección 2 (c/c)
        """
        # Inicializar como slab básico
        self.model.PropArea.SetSlab(section_name, 0, 1, material_name, overall_depth)
        
        # Configurar como waffle
        self.model.PropArea.SetSlabWaffle(
            section_name,
            overall_depth,
            slab_thickness,
            stem_width_dir1,
            stem_width_dir2,
            rib_spacing_dir1,
            rib_spacing_dir2
        )
        
        print(f"Sección de losa reticular '{section_name}' añadida:")
        print(f"  - Altura total: {overall_depth}")
        print(f"  - Espesor losa: {slab_thickness}")
        print(f"  - Nervios Dir1: ancho={stem_width_dir1}, espaciamiento={rib_spacing_dir1}")
        print(f"  - Nervios Dir2: ancho={stem_width_dir2}, espaciamiento={rib_spacing_dir2}")

    # ==================== WALLS (MUROS) ====================
    def add_wall_section(self, section_name, material_name, thickness,
                        wall_prop_type=1, shell_type=1):
        """
        Crea una sección de muro

        Parameters:
        -----------
        section_name : str
            Nombre de la sección
        material_name : str
            Material del muro
        thickness : float
            Espesor del muro
        wall_prop_type : int, default 1
            Tipo de propiedad de muro:
            - 1 = Specified (especificado)
            - 2 = AutoSelectList (lista de auto-selección)
        shell_type : int, default 1
            Tipo de shell:
            - 1 = Shell-thin (cáscara delgada)
            - 2 = Shell-thick (cáscara gruesa)
        """
        self.model.PropArea.SetWall(section_name, wall_prop_type, shell_type,
                            material_name, thickness)
        print(f"Sección de muro '{section_name}' añadida: t={thickness}")
        
    # ==================== DECKS (LOSAS COLABORANTES) ====================

    def add_deck_filled_section(self, section_name, deck_type, shell_type, 
                                fill_material, concrete_material, 
                                slab_depth, rib_depth, rib_width_top, rib_width_bot,
                                rib_spacing, shear_studs_per_rib):
        """
        Crea una sección de deck relleno (losa colaborante rellena)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        deck_type : str
            Tipo de deck (referencia del fabricante)
        shell_type : int
            Tipo de shell (1=thin, 2=thick)
        fill_material : str
            Nombre del material de relleno del deck
        concrete_material : str
            Nombre del material de concreto sobre el deck
        slab_depth : float
            Profundidad total de la losa
        rib_depth : float
            Profundidad de las nervaduras del deck
        rib_width_top : float
            Ancho superior de la nervadura
        rib_width_bot : float
            Ancho inferior de la nervadura
        rib_spacing : float
            Espaciamiento de nervaduras
        shear_studs_per_rib : int
            Número de conectores de corte por nervadura
        """
        self.model.PropArea.SetDeckFilled(
            section_name, deck_type, shell_type, fill_material, 
            concrete_material, slab_depth, rib_depth, rib_width_top, 
            rib_width_bot, rib_spacing, shear_studs_per_rib
        )
        print(f"Sección de deck relleno '{section_name}' añadida: h_total={slab_depth}")


    def add_deck_unfilled_section(self, section_name, deck_type, shell_type, 
                                material, rib_depth, rib_width_top, rib_width_bot,
                                rib_spacing, shear_thickness, unit_weight):
        """
        Crea una sección de deck sin relleno (losa colaborante sin relleno)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        deck_type : str
            Tipo de deck
        shell_type : int
            Tipo de shell (1=thin, 2=thick)
        material : str
            Material del deck
        rib_depth : float
            Profundidad de las nervaduras
        rib_width_top : float
            Ancho superior de la nervadura
        rib_width_bot : float
            Ancho inferior de la nervadura
        rib_spacing : float
            Espaciamiento de nervaduras
        shear_thickness : float
            Espesor para corte
        unit_weight : float
            Peso unitario
        """
        self.model.PropArea.SetDeckUnfilled(
            section_name, deck_type, shell_type, material,
            rib_depth, rib_width_top, rib_width_bot, rib_spacing,
            shear_thickness, unit_weight
        )
        print(f"Sección de deck sin relleno '{section_name}' añadida")


    def add_deck_solid_slab_section(self, section_name, shell_type, material, 
                                    depth, shear_studs_per_rib):
        """
        Crea una sección de deck tipo losa sólida
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección
        shell_type : int
            Tipo de shell (1=thin, 2=thick)
        material : str
            Material de la losa
        depth : float
            Profundidad/espesor de la losa
        shear_studs_per_rib : int
            Número de conectores de corte por nervadura
        """
        self.model.PropArea.SetDeckSolidSlab(
            section_name, shell_type, material, depth, shear_studs_per_rib
        )
        print(f"Sección de deck losa sólida '{section_name}' añadida: t={depth}")


    # ==================== SHELL LAYERS (CAPAS DE SHELL) ====================

    def add_shell_layer(self, section_name, layer_name, distance_from_ref, 
                    thickness, shell_type, material, angle=0.0):
        """
        Añade una capa a una sección tipo shell (para losas multicapa)
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
        section_name : str
            Nombre de la sección shell
        layer_name : str
            Nombre de la capa
        distance_from_ref : float
            Distancia desde la superficie de referencia
        thickness : float
            Espesor de la capa
        shell_type : int
            Tipo de shell (1=membrane, 2=plate, 3=shell)
        material : str
            Material de la capa
        angle : float, default 0.0
            Ángulo de orientación del material (grados)
        """
        self.model.PropArea.SetShellLayer(
            section_name, layer_name, distance_from_ref,
            thickness, shell_type, 0, material, angle
        )
        print(f"Capa '{layer_name}' añadida a sección '{section_name}': t={thickness}")

    def add_area_section(self, section_name, material_name, section_type, **kwargs):
        """
        Función unificada para añadir cualquier tipo de sección de área
        
        Parameters:
        -----------
        section_name : str
            Nombre de la sección
        material_name : str
            Material de la sección
        section_type : str
            Tipo de sección (ver AREA_SECTION_FUNCTIONS keys)
        **kwargs : dict
            Parámetros específicos del tipo de sección
        
        Examples:
        ---------
        # Losa básica
        add_area_section('LOSA20', 'CONC25', 'Slab', thickness=0.20)
        
        # Losa nervada
        add_area_section('LOSA_NERV', 'CONC25', 'RibbedSlab',
                        overall_depth=0.30, slab_thickness=0.05, 
                        stem_width=0.10, rib_spacing=0.60, rib_direction=1)
        
        # Muro
        add_area_section('MURO20', 'CONC25', 'Wall', thickness=0.20)
        """
        
        AREA_SECTION_FUNCTIONS = {
            'Slab': self.add_slab_section,
            'RibbedSlab': self.add_ribbed_slab_section,
            'WaffleSlab': self.add_waffle_slab_section,
            'Wall': self.add_wall_section,
            'DeckFilled': self.add_deck_filled_section,
            'DeckUnfilled': self.add_deck_unfilled_section,
            'DeckSolidSlab': self.add_deck_solid_slab_section,
        }
        
        if section_type not in AREA_SECTION_FUNCTIONS:
            available = ', '.join(AREA_SECTION_FUNCTIONS.keys())
            raise ValueError(f"Tipo de sección '{section_type}' no válido. Disponibles: {available}")
        
        func = AREA_SECTION_FUNCTIONS[section_type]
        
        # Inyectar material_name si la función lo requiere
        if section_type in ['Slab', 'RibbedSlab', 'WaffleSlab', 'Wall']:
            func(section_name, material_name, **kwargs)
        else:
            # Para decks y otros que tienen parámetros diferentes
            func(section_name, **kwargs)
            
    def add_area_obj(self,points,section_name):
        num_points = len(points)
        if not is_ccw(points):
            points = list(reversed(points))
        
        coords_x = list(np.array(points)[:,0])
        coords_y = list(np.array(points)[:,1])
        coords_z = list(np.array(points)[:,2])
        slab_name = self.model.AreaObj.AddByCoord(num_points, coords_x, coords_y, coords_z)[3]
        self.model.AreaObj.SetProperty(slab_name, section_name)
        return slab_name
            
     # ==================== LOAD PATTERNS ====================
    
    def add_load_pattern(self, pattern_name, pattern_type=1):
        """
        Añade un patrón de carga
        
        Parameters:
        -----------
        pattern_name : str
            Nombre del patrón
        pattern_type : int
            Tipo (1=Dead, 2=SuperDead, 3=Live, 4=ReduceLive, etc.)
        """
        self.model.LoadPatterns.Add(pattern_name, pattern_type)
        print(f"Patrón de carga '{pattern_name}' añadido")
    
    def add_point_load(self, point_name, load_pattern, Fx=0, Fy=0, Fz=0, 
                      Mx=0, My=0, Mz=0):
        """
        Añade carga puntual a un punto
        
        Parameters:
        -----------
        point_name : str
            Nombre del punto
        load_pattern : str
            Patrón de carga
        Fx, Fy, Fz : float
            Fuerzas en direcciones globales
        Mx, My, Mz : float
            Momentos en direcciones globales
        """
        forces = [Fx, Fy, Fz, Mx, My, Mz]
        self.model.PointObj.SetLoadForce(point_name, load_pattern, forces)
        print(f"Carga puntual añadida a '{point_name}'")
    
    def add_frame_distributed_load(self, frame_name, load_pattern, direction, 
                                   value, dist_type=1):
        """
        Añade carga distribuida a un frame
        
        Parameters:
        -----------
        frame_name : str
            Nombre del frame
        load_pattern : str
            Patrón de carga
        direction : int
            Dirección (1=Local1, 2=Local2, 3=Local3, 4-6=Global X,Y,Z)
        value : float
            Valor de la carga
        dist_type : int
            Tipo de distribución (1=Force, 2=Moment)
        """
        self.model.FrameObj.SetLoadDistributed(frame_name, load_pattern, 
                                              dist_type, direction, 0, 1, 
                                              value, value)
        print(f"Carga distribuida añadida a frame '{frame_name}'")
    
    def add_area_uniform_load(self, area_name, load_pattern, value, direction=6):
        """
        Añade carga uniforme a un área
        
        Parameters:
        -----------
        area_name : str
            Nombre del área
        load_pattern : str
            Patrón de carga
        value : float
            Valor de la carga
        direction : int
            Dirección (4-6 = Global X,Y,Z)
        """
        self.model.AreaObj.SetLoadUniform(area_name, load_pattern, value, direction)
        print(f"Carga uniforme añadida a área '{area_name}'")
    
    