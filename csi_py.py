from extractors import DataExtractor

import comtypes.client
import pandas as pd
import numpy as np
import psutil
import os

eFramePropType = {
    1: 'I',
    2: 'Channel',
    3: 'T',
    4: 'Angle',
    5: 'DblAngle',
    6: 'Box',
    7: 'Pipe',
    8: 'Rectangular',
    9: 'Circle',
    10: 'General',
    11: 'DbChannel',
    12: 'Auto',
    13: 'SD',
    14: 'Variable',
    15: 'Joist',
    16: 'Bridge',
    17: 'Cold_C',
    18: 'Cold_2C',
    19: 'Cold_Z',
    20: 'Cold_L',
    21: 'Cold_2L',
    22: 'Cold_Hat',
    23: 'BuiltupICoverplate',
    24: 'PCCGirderI',
    25: 'PCCGirderU',
    26: 'BuiltupIHybrid',
    27: 'BuiltupUHybrid',
    28: 'Concrete_L',
    29: 'FilledTube',
    30: 'FilledPipe',
    31: 'EncasedRectangle',
    32: 'EncasedCircle',
    33: 'BucklingRestrainedBrace',
    34: 'CoreBrace_BRB',
    35: 'ConcreteTee',
    36: 'ConcreteBox',
    37: 'ConcretePipe',
    38: 'ConcreteCross',
    39: 'SteelPlate',
    40: 'SteelRod',
    41: 'PCCGirderSuperT',
    42: 'Cold_Box',
    43: 'Cold_I',
    44: 'Cold_Pipe',
    45: 'Cold_T',
    46: 'Trapezoidal',
    47: 'PCCGirderBox'
}

eMatSymType = {
    0: 'Isotropic',
    1: 'Orthotropic',
    2: 'Anisotropic',
    3: 'Uniaxial'
}

def validate_programs(program):
    # Validar y estandarizar el programa
    program = program.upper().strip()
    
    # Mapeo de variaciones comunes
    program_map = {
        'ETABS': 'ETABS',
        'SAP': 'SAP2000',
        'SAP2000': 'SAP2000',
        'SAFE': 'SAFE'
    }
    
    if program not in program_map:
        raise ValueError(f"Programa no válido: {program}. Use: ETABS, SAP2000 o SAFE")
    
    return program_map[program]

def get__pids(program='ETABS'):
    """Obtiene todos los PIDs de procesos activos"""
    pids_etabs = []
    
    program = validate_programs(program)
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if f'{program}.exe' == proc.info['name']:
                pids_etabs.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return pids_etabs

def get_paths(program='ETABS'):
    '''Obtiene los paths de los procesos ETABS activos'''
    
    program = validate_programs(program)
    pids = get__pids(program=program)
    paths = []
    helper = comtypes.client.CreateObject(f'{program}v1.Helper')
    module = getattr(comtypes.gen, f'{program}v1')
    helper = helper.QueryInterface(module.cHelper)
    for pid in pids:
        etabs_object = helper.GetObjectProcess(
            f"CSI.ETABS.{program}.ETABSObject" 
            if program in ['ETABS','SAFE'] 
            else "CSI.SAP2000.API.SapObject", pid)
        paths.append(etabs_object.SapModel.GetModelFilename())
        
    return {pid:path for pid,path in 
            zip(pids,paths)}


class CSIHandler:
    units_dict = {
        'kN_mm':5,
        'kN_m':6,
        'kgf_mm':7,
        'kgf_m':8,
        'N_mm':9,
        'N_m':10,
        'tonf_mm':11,
        'tonf_m':12,
        'kN_cm':13,
        'kgf_cm':14,
        'N_cm':15,
        'tonf_cm':16
    }
    
    def __init__(self,program='ETABS',units='kN_m'):
        program = validate_programs(program)
        self.program = program
        self.model = None
        self.object = None
        self.file_path = None
        self.file_name = None
        self.units = units
    
        helper = comtypes.client.CreateObject(f'{program}v1.Helper')
        module = getattr(comtypes.gen, f'{program}v1')
        self.helper = helper.QueryInterface(module.cHelper)
        
        self.initialize_properties()
        
        # Inicializar extractor
        self._extractor = None
        
    def initialize_properties(self):
        self._cases = None
        self._combos = None
        self._cases_and_combos = None
        self._design_cases = None
        self._design_cases_and_combos = None
        self._seismic_cases = None
        self._seismic_combos = None
        self._seismic_cases_and_combos = None
        self._stories = None
        
    @property
    def extractor(self):
        """Propiedad lazy para el extractor de datos"""
        if self._extractor is None:
            self._extractor = DataExtractor(self)
        return self._extractor
        
    def connect_open_instance(self,instance_position=None):
        program = self.program
        if instance_position is None:
            self.object = self.helper.GetObject(
                f"CSI.{program}.API.ETABSObject" 
                if program in ['ETABS','SAFE'] 
                else "CSI.SAP2000.API.SapObject")
        elif isinstance(instance_position, int):
            pids = get__pids()
            self.object = self.helper.GetObjectProcess(
                f"CSI.{program}.API.ETABSObject" 
                if program in ['ETABS','SAFE'] 
                else "CSI.SAP2000.API.SapObject", pids[instance_position])
        else:
            raise TypeError(f"instance_position no puede ser{type(instance_position).__name__}")
        
        if self.object is None:
            raise ConnectionError(f'No hay instancia de {program} abierta')
        
        self.model = self.object.SapModel
        self.file_path = self.model.GetModelFilename()
        self.file_name = os.path.basename(self.file_path)
        self.set_units()
        print(f'Conectado a {self.file_name}')
            
    def open_and_connect(self,file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        
        program = self.program
        self.object = self.helper.CreateObjectProgID(
                f"CSI.{program}.API.ETABSObject" 
                if program in ['ETABS','SAFE'] 
                else "CSI.SAP2000.API.SapObject")
        self.object.ApplicationStart()
        self.model = self.object.SapModel
        self.model.File.OpenFile(file_path)
        self.file_path = file_path
        self.file_name = os.path.basename(self.file_path)
        self.set_units()
        print(f'Conectado a {self.file_name}')
        
        
    def close(self):
        '''
        cerrar
        '''
        #SapModel.SetModelIsLocked(False)
        self.object.ApplicationExit(True)
        self.object = None
        self.model = None
        print(f'{self.file_name} cerrado')
        
    def set_units(self):
        '''
        Definir unidades de trabajo solo para el output del codigo
        imput:
        unit: unidad definida en el diccionario: units_dict
        '''
        self.model.SetPresentUnits(self.units_dict[self.units])
        
    def set_envelopes_for_dysplay(self,set_envelopes=True):
        '''
        metodo de formateo de tablas (por defecto elige envolventes en casos de carga compuesto)
        '''

        SapModel = self.model
        IsUserBaseReactionLocation=False
        UserBaseReactionX=0.
        UserBaseReactionY=0.
        UserBaseReactionZ=0.
        IsAllModes=True
        StartMode=0
        EndMode=0
        IsAllBucklingModes=True
        StartBucklingMode=0
        EndBucklingMode=0
        MultistepStatic=1 if set_envelopes else 2
        NonlinearStatic=1 if set_envelopes else 2
        ModalHistory=1
        DirectHistory=1
        Combo=2
        SapModel.DataBaseTables.SetOutputOptionsForDisplay(IsUserBaseReactionLocation,UserBaseReactionX,UserBaseReactionY,UserBaseReactionZ,IsAllModes,StartMode,EndMode,IsAllBucklingModes,StartBucklingMode,EndBucklingMode,MultistepStatic,NonlinearStatic,ModalHistory,DirectHistory,Combo)
        
    @property
    def available_tables(self):
        data = self.model.DatabaseTables.GetAvailableTables()
        return dict(zip(data[1],data[3]))
        
    @property
    def cases(self):
        if self._cases is None:
            load_cases = self.model.LoadCases.GetNameList()[1]
            load_cases = [i for i in load_cases if i[0] != '~']
            self._cases =  list(load_cases)
        return self._cases
    
    @property
    def combos(self):
        if self._combos is None:
            load_combos = self.model.RespCombo.GetNameList()[1]
            load_combos = [i for i in load_combos if i[0] != '~']
            self._combos = list(load_combos)
        return self._combos
    
    @property
    def cases_and_combos(self):
        if self._cases_and_combos is None:
            self._cases_and_combos = self.cases+self.combos
        return self._cases_and_combos
        
    def get_combo_cases(self, combo_name):
        # Obtener la información inicial de la combinación
        combo_info = self.model.RespCombo.GetCaseList(combo_name)
        combo_types = combo_info[1]
        combo_cases = combo_info[2]
        
        unique_cases = []
        
        for c_type,combo_case in zip(combo_types,combo_cases):
            if c_type == 0:
                unique_cases += [combo_case,]
            elif c_type == 1:
                unique_cases += self.get_combo_cases(combo_case)
                
        return list(set(unique_cases))
    
    @property
    def design_cases(self):
        if self._design_cases is None:
            self._design_cases = [case for case in self.cases if
                self.model.LoadCases.GetTypeOAPI_1(case)[2] != 8]
        return self._design_cases
    
    @property
    def design_cases_and_combos(self):
        if self._design_cases_and_combos is None:
            self._design_cases_and_combos = self.design_cases+self.combos
            
        return self._design_cases_and_combos
    
    @property
    def seismic_cases(self):
        load_cases = self.cases
        seismic_cases = [case for case in load_cases if
         self.model.LoadCases.GetTypeOAPI_1(case)[2]==5]
        return seismic_cases
    
    @property
    def seismic_combos(self):
        load_combos = self.combos
        seismic_cases = self.seismic_cases
        seismic_combos = [cb for cb in load_combos if
         set(self.get_combo_cases(cb)).\
             intersection(seismic_cases)]
        return seismic_combos
    
    @property
    def seismic_cases_and_combos(self):
        return self.seismic_cases + self.seismic_combos

    @property
    def stories(self):
        return self.model.Story.GeStories()[1]
    
    def select_cases_and_combos(self,cases_and_combos):
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)

    # Métodos delegados al extractor
    
    def get_table(self, table_name, set_envelopes=True):
        """Extrae una tabla del modelo, la devuelve en dataFrame"""
        return self.extractor.get_table(table_name, set_envelopes)
    
    # ==================== MÉTODOS DELEGADOS - MATERIALS ====================
    @property
    def material_list(self):
        """Obtiene lista de todos los materiales"""
        return self.extractor.material_list
    
    def get_material_properties(self, material_name):
        """
        Obtiene propiedades de un material.
        
        Parameters:
            material_name (str): Nombre del material
            
        Returns:
            dict: Propiedades del material
        """
        return self.extractor.get_material_properties(material_name)
    
    @property
    def material_properties(self):
        return self.extractor.material_properties
    

    # ==================== MÉTODOS DELEGADOS - POINTS ====================
    @property
    def point_list(self):
        """Obtiene lista de todos los puntos"""
        return self.extractor.point_list
    
    def get_point_coordinates(self, point_name):
        """
        Obtiene coordenadas de un punto.
        
        Parameters:
            point_name (str): Nombre del punto
            
        Returns:
            dict: Coordenadas {'X', 'Y', 'Z'}
        """
        return self.extractor.get_point_coordinates(point_name)
    
    @property
    def point_coordinates(self):
        """Dataframe de coordenadas"""
        return self.extractor.points_coordinates
    
    def get_point_restraints(self, point_name):
        """
        Obtiene restricciones de un punto.
        
        Parameters:
            point_name (str): Nombre del punto
            
        Returns:
            dict: Restricciones {'UX', 'UY', 'UZ', 'RX', 'RY', 'RZ'}
        """
        return self.extractor.get_point_restraints(point_name)
    
    @property
    def points_restraints(self):
        return self.extractor.points_restraints
    
    def extract_point_reactions(self, point_name=None, cases_and_combos=None):
        """
        Extrae reacciones en puntos.
        
        Parameters:
            point_name (str, optional): Nombre del punto. Si None, extrae todos.
            cases_and_combos (list, optional): Casos/combos. Si None, usa todos.
            
        Returns:
            DataFrame: Reacciones F1, F2, F3, M1, M2, M3
        """
        return self.extractor.extract_point_reactions(point_name, cases_and_combos)
    
    @property
    def points_reactions(self):
        return self.extractor.points_reactions
        
    # ==================== MÉTODOS DELEGADOS - FRAMES ====================
    
    @property
    def frame_sections_list(self):
        return self.extractor.frame_sections_list
    
    def get_frame_section_properties(self, section_name):
        """
        Obtiene propiedades de una sección.
        
        Parameters:
            section_name (str): Nombre de la sección
            
        Returns:
            dict: Propiedades de la sección
        """
        return self.extractor.get_frame_section_properties(section_name)
    
    def get_frame_section_dimensions(self, get_properties=False):
        """
        Obtiene dimensiones de las secciones.
        
        Parameters:
            get_properties (bool): Si True, incluye propiedades geométricas
            
        Returns:
            DataFrame: Dimensiones de secciones
        """
        return self.extractor.get_frame_section_dimensions(get_properties)
    
    @property
    def frame_sections_data(self):
        return self.extractor.frame_sections_data
    
    @property
    def frame_list(self):
        """Obtiene lista de todos los frames"""
        return self.extractor.frame_list

    def get_frame_section(self, frame_name):
        """
        Obtiene sección asignada a un frame.
        
        Parameters:
            frame_name (str): Nombre del frame
            
        Returns:
            str: Nombre de la sección
        """
        return self.extractor.get_frame_section(frame_name)
    
    def get_frame_points(self, frame_name):
        """
        Obtiene puntos inicial y final de un frame.
        
        Parameters:
            frame_name (str): Nombre del frame
            
        Returns:
            dict: {'point_i', 'point_j'}
        """
        return self.extractor.get_frame_points(frame_name)
    
    def get_frame_coordinates(self, frame_name):
        """
        Obtiene coordenadas de puntos inicial y final.
        
        Parameters:
            frame_name (str): Nombre del frame
            
        Returns:
            dict: {'coord_i', 'coord_j'}
        """
        return self.extractor.get_frame_coordinates(frame_name)
    
    def get_frame_length(self, frame_name):
        """
        Obtiene longitud del frame.
        
        Parameters:
            frame_name (str): Nombre del frame
            
        Returns:
            float: Longitud del frame
        """
        return self.extractor.get_frame_length(frame_name)
    
    @property
    def frames_properties(self):
        return self.extractor.frames_properties
    
    def extract_frame_forces(self, frame_name=None, cases_and_combos=None):
        """
        Extrae fuerzas en frames.
        
        Parameters:
            frame_name (str, optional): Nombre del frame. Si None, extrae todos.
            cases_and_combos (list, optional): Casos/combos. Si None, usa todos.
            
        Returns:
            DataFrame: Fuerzas P, V2, V3, T, M2, M3
        """
        return self.extractor.extract_frame_forces(frame_name, cases_and_combos)
    
    @property
    def frames_forces(self):
        return self.extractor.frames_forces
    
        
    # ==================== MÉTODOS DELEGADOS - AREAS ====================
    @property
    def area_sections_list(self):
        return self.extractor.area_sections_list
    
    def get_area_section(self, area_name):
        """
        Obtiene sección asignada a un área.
        
        Parameters:
            area_name (str): Nombre del área
            
        Returns:
            str: Nombre de la sección
        """
        return self.extractor.get_area_section(area_name)
    
    def get_area_points(self, area_name):
        """
        Obtiene puntos que definen un área.
        
        Parameters:
            area_name (str): Nombre del área
            
        Returns:
            list: Lista de nombres de puntos
        """
        return self.extractor.get_area_points(area_name)
    
    @property
    def area_geometry(self):
        """Obtiene lista de todos los objetos de área"""
        return self.extractor.area_geometry
    
    def map_area_properties(self):
        self.extractor.map_area_properties()
    
    @property
    def area_list(self):
        return self.extractor.area_list
    
    def extract_area_forces(self,area_name,cases_and_combos):
        return self.extractor.extract_area_forces(area_name,cases_and_combos)
    
    @property
    def area_forces(self):
        return self.extractor.area_forces   
    
    
    # ==================== MÉTODOS DELEGADOS - SLABS ====================
    @property
    def slab_sections_data(self):
        return self.extractor.slab_sections_data
    
    @property
    def deck_sections_data(self):
        return self.extractor.deck_sections_data
    
    @property
    def floor_list(self):
        return self.extractor.floor_list
    
    
    @property
    def slab_properties(self):
        return self.extractor.slab_properties
    
    def extract_area_forces(self, area_name=None, cases_and_combos=None):
        """
        Extrae fuerzas en áreas.
        
        Parameters:
            area_name (str, optional): Nombre del área. Si None, extrae todas.
            cases_and_combos (list, optional): Casos/combos. Si None, usa todos.
            
        Returns:
            DataFrame: Fuerzas F11, F22, F12, M11, M22, M12, V13, V23
        """
        return self.extractor.extract_area_forces(area_name, cases_and_combos)

    # ==================== MÉTODOS DELEGADOS - WALLS ====================
    @property
    def wall_sections_data(self):
        return self.extractor.wall_sections_data
    
    @property
    def wall_list(self):
        return self.extractor.wall_list
        

    

if __name__ == '__main__':
    import time
    etabs_model = CSIHandler('Etabs')
    etabs_model.connect_open_instance()
    print(etabs_model.slab_sections_data)
    # to = time.time()
    # print(etabs_model.area_properties)
    # print(time.time()-to)
    # to = time.time()
    # print(etabs_model.area_properties)
    # print(time.time()-to)
