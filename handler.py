from constants import eUnits,u
from extractor import DataExtractor
from builder import ModelBuilder

import comtypes.client
import pandas as pd
import numpy as np
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


class CSIHandler(DataExtractor,
                 ModelBuilder):
    def __init__(self,program='ETABS',units=u.csi_units):
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
        super().__init__()
        
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
        self.model= None
        print(f'{self.file_name} cerrado')
        
    def set_units(self):
        '''
        Definir unidades de trabajo solo para el output del codigo
        imput:
        unit: unidad definida en el diccionario: units_dict
        '''
        self.model.SetPresentUnits(eUnits[self.units])
        
        
        
if __name__ == '__main__':
    import time
    etabs_model = CSIHandler('Etabs')
    etabs_model.connect_open_instance()
    to = time.time()
    print(etabs_model.add_rectangle_section('S1','C f\'c = 21 MPa',0.5,0.3))
    print(time.time()-to)
    # to = time.time()
    # print(etabs_model.area_properties)
    # print(time.time()-to)
