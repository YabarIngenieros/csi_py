import pandas as pd
import numpy as np

class EtabsError(Exception):
    """Error general de ETABS."""
    pass

class DataExtractor:
    """Clase para métodos de extracción de información del modelo"""
    
    def __init__(self, csi_handler):
        self.handler = csi_handler
        self.model = csi_handler.model
    
    def get_table(self, table_name, set_envelopes=True):
        """
        Método de extracción de tablas, usa envolventes por defecto
        Corre el modelo en caso de no encontrar datos
        """
        self.handler.set_envelopes_for_dysplay(set_envelopes=set_envelopes)
        data = self.model.DatabaseTables.GetTableForDisplayArray(
            table_name, FieldKeyList='', GroupName=''
        )
        flag = data[5]
        if flag == 1:
            self.model.Analyze.RunAnalysis()
            return self.get_table(table_name,set_envelopes)
        
        elif flag == -96:
            raise ValueError(f"La tabla '{table_name}' no existe en el modelo ETABS.")
        
        elif flag != 0:
            raise EtabsError(f"Error al extraer la tabla, flag devuelto de {flag}")
        
        columns = data[2]
        num_records = data[3]
        data = [i if i else '' for i in data[4]]
        data = pd.DataFrame(data)
        data = data.values.reshape(num_records, len(columns))
        table = pd.DataFrame(data, columns=columns)
        return table
    
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
        frames = [frame_name] if frame_name else self.handler.get_frame_list()
        cases_and_combos = (
            [cases_and_combos] if isinstance(cases_and_combos, str)
            else list(cases_and_combos) if cases_and_combos
            else self.handler.get_cases_and_combos()
        )

        data = {
            'Frame': [], 'Station': [], 'OutputCase': [], 
            'StepType': [], 'StepNumber': [],
            'P': [], 'V2': [], 'V3': [], 'T': [], 'M2': [], 'M3': []
        }
        
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        for case in cases_and_combos:
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
    
    def get_frame_section_dimensions(self, get_properties=False):
        """Dimensiones de las secciones"""
        from .csi_py import eFramePropType
        
        columns = ['SectionName', 'PropType', 't3', 't2', 'tf', 'tw', 't2b', 'tfb', 'Area']
        data = self.model.PropFrame.GetAllFrameProperties_2()[1:-1]
        data = pd.DataFrame(np.array(data).T, columns=columns)
        data['SectionType'] = data['PropType'].astype(int).map(eFramePropType)
        data = data[['SectionName', 'SectionType', 't3', 't2', 'tf', 'tw', 't2b', 'tfb', 'Area']]
        
        if get_properties:
            df_props = pd.DataFrame(
                data['SectionName'].apply(self.get_frame_section_properties).tolist()
            )
            data = data.merge(df_props, on='SectionName', how='left')
        
        return data
    
    def extract_frame_info(self, frame_names=None, include_forces=False, 
                        cases_and_combos=None, output_file=None, format='json'):
        """
        Extrae información completa de frames y opcionalmente la guarda
        
        Parameters:
        -----------
        frame_names : list or str, optional
            Nombre(s) de frame(s). Si None, extrae todos.
        include_forces : bool, default False
            Si True, incluye fuerzas internas
        cases_and_combos : list, optional
            Casos/combos para fuerzas. Si None, usa todos.
        output_file : str, optional
            Ruta para guardar. Si None, genera nombre automático.
        format : str, default 'json'
            Formato de salida: 'json' o 'excel'
        
        Returns:
        --------
        dict con DataFrames: 'geometry', 'sections', 'forces' (opcional)
        """
        
        # Normalizar entrada
        if frame_names is None:
            frames = self.get_frame_list()
        elif isinstance(frame_names, str):
            frames = [frame_names]
        else:
            frames = list(frame_names)
        
        # 1. Geometría
        geo_data = []
        for frame in frames:
            coords = self.get_frame_coordinates(frame)
            points = self.get_frame_points(frame)
            length = self.get_frame_length(frame)
            section = self.get_frame_section(frame)
            
            geo_data.append({
                'Frame': frame,
                'Section': section,
                'PointI': points['point_i'],
                'PointJ': points['point_j'],
                'XI': coords['coord_i'][0],
                'YI': coords['coord_i'][1],
                'ZI': coords['coord_i'][2],
                'XJ': coords['coord_j'][0],
                'YJ': coords['coord_j'][1],
                'ZJ': coords['coord_j'][2],
                'Length': length
            })
        
        df_geometry = pd.DataFrame(geo_data)
        
        # 2. Propiedades de secciones únicas
        df_sections = self.get_frame_section_dimensions(get_properties=True)
        
        result = {
            'geometry': df_geometry,
            'sections': df_sections
        }
        
        # 3. Fuerzas (opcional)
        if include_forces:
            df_forces = self.extract_frame_forces(
                frame_name=None if frame_names is None else frames,
                cases_and_combos=cases_and_combos
            )
            result['forces'] = df_forces
        
        # 4. Guardar archivo
        if output_file is None:
            # Nombre automático basado en el modelo
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            base_name = self.file_name.replace('.EDB', '').replace('.sdb', '')
            ext = 'json' if format == 'json' else 'xlsx'
            output_file = f'{base_name}_frames_{timestamp}.{ext}'
        
        format = format.lower()
        
        if format == 'json':
            # Convertir DataFrames a formato serializable
            data_json = {
                'model_info': {
                    'file_name': self.file_name,
                    'file_path': self.file_path,
                    'units': self.units,
                    'export_date': pd.Timestamp.now().isoformat()
                },
                'geometry': result['geometry'].to_dict(orient='records'),
                'sections': result['sections'].to_dict(orient='records')
            }
            
            if include_forces:
                data_json['forces'] = result['forces'].to_dict(orient='records')
            
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_json, f, indent=2, ensure_ascii=False)
            
            print(f'Información guardada en: {output_file}')
        
        elif format == 'excel':
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                result['geometry'].to_excel(writer, sheet_name='Geometry', index=False)
                result['sections'].to_excel(writer, sheet_name='Sections', index=False)
                if include_forces:
                    result['forces'].to_excel(writer, sheet_name='Forces', index=False)
            
            print(f'Información guardada en: {output_file}')
        
        else:
            raise ValueError(f"Formato no válido: {format}. Use 'json' o 'excel'")
        
        return result