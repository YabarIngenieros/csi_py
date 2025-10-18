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

    def get_frame_list(self):
        """Obtiene lista de todos los frames"""
        return list(self.model.FrameObj.GetNameList()[1])
    
    def get_frame_section(self, frame_name):
        """Obtiene sección asignada a un frame"""
        frame_name = f'{frame_name}'
        return self.model.FrameObj.GetSection(frame_name)[0]
    
    def get_frame_points(self, frame_name):
        """Obtiene puntos inicial y final de un frame"""
        frame_name = f'{frame_name}'
        result = self.model.FrameObj.GetPoints(frame_name)
        return {'point_i': result[0], 'point_j': result[1]}
    
    def get_frame_coordinates(self,frame_name):
        """Obtiene coordenadas de los puntos inicial y final"""
        points = self.get_frame_points(frame_name)
        coord_i = self.model.PointObj.GetCoordCartesian(points['point_i'])[:-1]
        coord_j = self.model.PointObj.GetCoordCartesian(points['point_j'])[:-1]
        
        return {'coord_i': coord_i, 'coord_j': coord_j}
    
    def get_frame_length(self, frame_name):
        """Obtiene longitud del frame"""
        coords = self.get_frame_coordinates(frame_name)
        coord_i = coords['coord_i']
        coord_j = coords['coord_j']
        
        import numpy as np
        length = np.sqrt(sum((coord_j[i] - coord_i[i])**2 for i in range(3)))
        return length
    
    def extract_frame_forces(self, frame_name=None, cases_and_combos=None):
        """
        Extrae fuerzas en frames usando API nativa
        
        Parameters:
        -----------
        frame_name : str, optional
            Nombre del frame. Si None, extrae todos.
        cases_and_combos : list, optional
            Lista de casos/combos. Si None, usa todos.
        
        Returns:
        --------
        DataFrame con P, V2, V3, T, M2, M3 para cada frame
        """
        
        frames = [frame_name] if frame_name else self.get_frame_list()
        cases_and_combos = (
        [cases_and_combos] if isinstance(cases_and_combos, str)
        else list(cases_and_combos) if cases_and_combos
        else self.get_cases_and_combos()
        )

        data = {
        'Frame': [], 'Station': [], 'OutputCase': [], 
        'StepType': [], 'StepNumber': [],
        'P': [], 'V2': [], 'V3': [], 'T': [], 'M2': [], 'M3': []
        }
        
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        for case in cases_and_combos :
            self.model.Results.Setup.SetCaseSelectedForOutput(case)
            self.model.Results.Setup.SetComboSelectedForOutput(case)
            
        frame_force = self.model.Results.FrameForce
        for frame in frames:
            res = frame_force(frame, 0)
            if res[0] == 0:
                continue

            data['Frame'].extend(res[1])
            data['Station'].extend(res[2])
            data['OutputCase'].extend(res[5])
            data['StepType'].extend(res[6])
            data['StepNumber'].extend(res[7])
            data['P'].extend(res[8])
            data['V2'].extend(res[9])
            data['V3'].extend(res[10])
            data['T'].extend(res[11])
            data['M2'].extend(res[12])
            data['M3'].extend(res[13])
                
        return pd.DataFrame(data)

    def get_frame_section_properties(self, section_name):
        """Obtiene propiedades de una sección"""
        result = self.model.PropFrame.GetSectProps(section_name)
        return {
            'SectionName': section_name,
            'Area': result[0],
            'As2': result[1],
            'As3': result[2],
            'Torsion': result[3],
            'I22': result[4],
            'I33': result[5],
            'S22': result[6],
            'S33': result[7],
            'Z22': result[8],
            'Z33': result[9],
            'R22': result[10],
            'R33': result[11]
        }
        
    def get_frame_section_dimensions(self,get_properties=False):
        '''Dimensiones de las secciones'''
        columns = ['SectionName','PropType','t3','t2','tf','tw','t2b','tfb','Area']
        data = self.model.PropFrame.GetAllFrameProperties_2()[1:-1]
        data = pd.DataFrame(np.array(data).T,columns=columns)
        data['SectionType'] = data['PropType'].astype(int).map(eFramePropType)
        data = data[['SectionName', 'SectionType', 't3', 't2', 'tf', 'tw', 't2b', 'tfb', 'Area']]
        if get_properties:
            df_props = pd.DataFrame(data['SectionName'].apply(self.get_frame_section_properties).tolist())
            data = data.merge(df_props,on='SectionName',how='left')
        return data

        

if __name__ == '__main__':
    import time
    etabs_model = CSIHandler('Etabs')
    etabs_model.connect_open_instance()
    to = time.time()
    #print(etabs_model.get_frame_section_properties('VIGA 30X60'))
    print(etabs_model.get_frame_section_dimensions())
    print(time.time()-to)
    