import comtypes.client
import pandas as pd
import psutil
import os

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
        
        # self.conc_dict = {}
        # self.reb_dict = {}
        # self.section_dict = {}
        
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
        
        
    def get_table(self,table_name,set_envelopes=True):
        '''
        método de extraccion de tablas, usa evolventes por defecto
        Corre el modelo en caso de no encontrar datos
        '''

        SapModel = self.model
        self.set_envelopes_for_dysplay(set_envelopes=set_envelopes)
        data = SapModel.DatabaseTables.GetTableForDisplayArray(table_name,FieldKeyList='',GroupName='')
        
        if not data[2][0]:
            SapModel.Analyze.RunAnalysis()
            data = SapModel.DatabaseTables.GetTableForDisplayArray(table_name,FieldKeyList='',GroupName='')
            
        columns = data[2]
        data = [i if i else '' for i in data[4]] #reemplazando valores None por ''
        #reshape data
        data = pd.DataFrame(data)
        data = data.values.reshape(int(len(data)/len(columns)),len(columns))
        table = pd.DataFrame(data, columns=columns)
        return table
    
    def get_cases(self):
        load_cases = self.model.LoadCases.GetNameList()[1]
        load_cases = [i for i in load_cases if i[0] != '~']
        return list(load_cases)
    
    def get_combos(self):
        load_combos = self.SapModel.RespCombo.GetNameList()[1]
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
        
    def extract_beam_loads(self,cases_and_combos=None):
        if cases_and_combos == None:
            cases_and_combos = self.get_cases_and_combos()
        
        data_forces = self.get_table('Element Forces - Beams')
        data_forces = data_forces.sort_values(
                by=['OutputCase', '_index'],
                key=lambda col: col.map({nombre: i for i, nombre in enumerate(cases_and_combos)}) if col.name == 'OutputCase' else col
            ).reset_index(drop=True)
        data_forces = data_forces.drop(columns='_index')
        
        return data_forces


        
    
    

if __name__ == '__main__':
    etabs_model = CSIHandler('Etabs')
    etabs_model.connect_open_instance(0)
    