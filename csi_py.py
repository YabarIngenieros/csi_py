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
        
        # Inicializar extractor
        self._extractor = None
        
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
        
    def get_available_tables(self):
        data = self.model.DatabaseTables.GetAvailableTables()
        return dict(zip(data[1],data[3]))
        
    
    def get_cases(self):
        load_cases = self.model.LoadCases.GetNameList()[1]
        load_cases = [i for i in load_cases if i[0] != '~']
        return list(load_cases)
    
    def get_combos(self):
        load_combos = self.model.RespCombo.GetNameList()[1]
        load_combos = [i for i in load_combos if i[0] != '~']
        return list(load_combos)
    
    def get_cases_and_combos(self):
        return self.get_cases()+self.get_combos()
        
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
    
    def get_seismic_cases(self):
        load_cases = self.get_cases()
        seismic_cases = [case for case in load_cases if
         self.model.LoadCases.GetTypeOAPI_1(case)[2]==5]
        return seismic_cases
    
    def get_seismic_combos(self):
        load_combos = self.get_combos()
        seismic_cases = self.get_seismic_cases()
        seismic_combos = [cb for cb in load_combos if
         set(self.get_combo_cases(cb)).\
             intersection(seismic_cases)]
        return seismic_combos
    
    def get_seismic_cases_and_combos(self):
        seismic_cases = self.get_seismic_cases()
        seismic_combos = self.get_seismic_combos()
        return seismic_cases + seismic_combos
    
    def get_stories(self):
        return self.model.Story.GeStories()[1]
    
    @property
    def story_order(self):
        return self.get_stories()
    
    def select_cases_and_combos(self,cases_and_combos):
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)

    # Métodos delegados al extractor para mantener compatibilidad
    def get_table(self, table_name, set_envelopes=True):
        """Delegado al extractor"""
        return self.extractor.get_table(table_name, set_envelopes)

        

if __name__ == '__main__':
    import time
    etabs_model = CSIHandler('Etabs')
    etabs_model.connect_open_instance()
    to = time.time()
    print(etabs_model.get_table('Element Forces - Beams'))
    #print(etabs_model.extract_frame_info(format='excel'))
    print(time.time()-to)
    