import pandas as pd
import numpy as np

from .constants import EtabsError, eFramePropType

# funciones de normalización
def format_list_args(names,defect_values=None,check_values=True):
    if names is None:
        return defect_values
    if isinstance(names, (str, int)):
        names = [str(names).strip()]
    if isinstance(names,(list,tuple)):
        names = [str(name).strip() for name in names if name]
    if (defect_values is not None) and check_values:
        return [name for name in names if name in defect_values]
    return names
        

class DataExtractor:
    """Clase para métodos de extracción de información del modelo"""
    
    def __init__(self):
        super().__init__()
        self._stories = None
        
        self._tabular_data = None
        
        self._cases = None
        self._combos = None
        self._cases_and_combos = None
        self._design_cases = None
        self._design_cases_and_combos = None
        self._seismic_cases = None
        self._seismic_combos = None
        self._seismic_cases_and_combos = None
        
        self._material_list = None
        self._material_properties = None
        
        self._point_list = None
        self._points_coordinates = None
        self._points_restraints = None
        self._points_reactions = None
        
        self._frame_sections_data = None
        self._frame_list = None
        self._frame_label_names = None
        self._frames_properties = None
        self._frames_forces = None
        
        self._wall_sections_data = None
        self._slab_sections_data = None
        self._deck_sections_data = None
        self._area_geometry = None
        self._area_forces = None
        
    def set_envelopes_for_dysplay(self,set_envelopes=True):
        '''
        metodo de formateo de tablas (por defecto elige envolventes en casos de carga compuesto)
        '''
        MultistepStatic=1 if set_envelopes else 2
        NonlinearStatic=1 if set_envelopes else 2
        self.model.DataBaseTables.SetOutputOptionsForDisplay(False,False,0,0,True,0,0,True,0,0,MultistepStatic,NonlinearStatic,1,1,2)
        
    @property
    def available_tables(self):
        data = self.model.DatabaseTables.GetAvailableTables()
        return pd.DataFrame(zip(data[1],data[3]),columns=['Table','ImportType'])
    
    @property
    def editable_tables(self):
        df = self.available_tables
        df = df[df['ImportType'].isin([2,3])].reset_index(drop=True)
        return df
    
    def get_table(self, table_name, set_envelopes=True):
        """
        Método de extracción de tablas, usa envolventes por defecto
        Corre el modelo en caso de no encontrar datos
        """
        self.set_envelopes_for_dysplay(set_envelopes=set_envelopes)
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
    
    @property
    def tabular_data(self):
        if self._tabular_data is None:
            table_data = {}
            for table in self.editable_tables['Table']:
                data = self.get_table(table,set_envelopes=False)
                table_data[table] = data
            self._tabular_data = table_data
        return self._tabular_data
        
    
    # ==================== LOADS ====================
        
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
    
    def select_cases_and_combos(self,cases_and_combos):
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)
        
    def get_response_spectrum(self,spectrum_names='all'):
        tables = self.editable_tables['Table']
        tables = tables[tables.str.contains('Functions - Response Spectrum')]
        cols = ['Name','Period','Value','DampRatio']
        data = pd.DataFrame(columns=cols)
        for table in tables:
            df = self.get_table(table)
            data = pd.concat([data,df[cols]],ignore_index=True)
            
        if spectrum_names=='all':
            return data
        elif spectrum_names not in data['Name'].values:
            raise ValueError(f"Nombre de espectro no definido: {spectrum_names}")
        else:
            spectrum_names = [spectrum_names] if isinstance(spectrum_names,(str))\
                else spectrum_names
            return data[data['Name'].isin(spectrum_names)]
    
    # ==================== MATERIALS ====================
    @property
    def material_list(self):
        """Obtiene lista de todos los materiales"""
        if self._material_list is None:
            self._material_list = list(self.model.PropMaterial.
                                       GetNameList()[1])
        return self._material_list
    
    def get_material_properties(self, material_name):
        """Obtiene propiedades de un material"""
        material_name = format_list_args(material_name)
        data = {'Material':[],'Type':[],'SymmetricType':[],
                    'E':[],'U':[],'A':[],'G':[]}
        for m_name in material_name:
            mat_type,sym_type = self.model.PropMaterial.\
                GetTypeOAPI(m_name)[:2]
            if sym_type == 0:
                props = self.model.PropMaterial.GetMPIsotropic(m_name)
            elif sym_type == 1:
                props = self.model.PropMaterial.GetMPOrthotropic(m_name)
            elif sym_type == 2:
                props = self.model.PropMaterial.GetMPAnisotropic(m_name)
            elif sym_type == 3:
                props = self.model.PropMaterial.GetMPUniaxial(m_name)
            
            data['Material'].append(m_name)
            data['Type'].append(mat_type)
            data['SymmetricType'].append(sym_type)
            data['E'].append(props[0])
            data['U'].append(props[1] if sym_type!=3 else 0)
            data['A'].append(props[2])
            data['G'].append(props[3] if sym_type!=3 else 0)
            
        return pd.DataFrame(data)
    
    @property
    def material_properties(self):
        if self._material_properties is None:
            self._material_properties = \
                self.get_material_properties(self.material_list)
        return self._material_properties
    
    
    # ==================== POINTS ====================
    @property
    def point_list(self):
        """Obtiene lista de todos los puntos"""
        if self._point_list is None:
            self._point_list = list(self.model.PointObj.GetNameList()[1])
        return self._point_list
    
    def get_point_coordinates(self, point_names):
        """Obtiene coordenadas de un punto"""
        point_names = format_list_args(point_names,self.point_list)
        data = {'Point':[],'X':[],'Y':[],'Z':[]}
        for point in point_names:
            if point not in self.point_list:
                continue
            data['Point'].append(point)
            coords = self.model.PointObj.GetCoordCartesian(point)
            data['X'].append(coords[0])
            data['Y'].append(coords[1])
            data['Z'].append(coords[2])
        return pd.DataFrame(data)
    
    @property
    def points_coordinates(self):
        """Dataframe de coordenadas"""
        if self._points_coordinates is None:
            self._points_coordinates = \
                self.get_point_coordinates(self.point_list)
                
        return self._points_coordinates

    def get_point_restraints(self,point_names):
        """Obtiene restricciones de un punto"""
        point_names = format_list_args(point_names,self.point_list)
        data = {'Point':[],'UX':[],'UY':[],'UZ':[],
                'RX':[],'RY':[],'RZ':[]}
        for point in point_names:
            if point not in self.point_list:
                raise ValueError(f'El punto {point} no existe en el modelo')
            restraints = self.model.PointObj.GetRestraint(point)[0]
            data['Point'].append(point)
            data['UX'].append(restraints[0])
            data['UY'].append(restraints[1])
            data['UZ'].append(restraints[2])
            data['RX'].append(restraints[3])
            data['RY'].append(restraints[4])
            data['RZ'].append(restraints[5])
            
        return pd.DataFrame(data)
    
    @property
    def points_restraints(self):
        if self._points_restraints is None:
            data = self.get_point_restraints(self.point_list)
            mask = data['UX'] & data['UY'] & data['UZ'] & \
                data['RX'] & data['RY'] & data['RZ']
            self._points_restraints = data[mask].reset_index(drop=True)
        
        return self._points_restraints
    

    def extract_point_reactions(self,point_names=None,cases_and_combos=None):
        """
        Extrae reacciones en puntos
        
        Parameters:
        -----------
        point_name : str, optional
            Nombre del punto. Si None, extrae todos.
        cases_and_combos : list, optional
            Lista de casos/combos. Si None, usa todos.
        
        Returns:
        --------
        DataFrame con F1, F2, F3, M1, M2, M3 para cada punto
        """
        point_names = format_list_args(point_names,self.point_list)
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
        data = {
            'Point': [], 'OutputCase': [], 'StepType': [], 'StepNumber': [],
            'F1': [], 'F2': [], 'F3': [], 'M1': [], 'M2': [], 'M3': []
        }
        
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        for case in cases_and_combos:
            self.model.Results.Setup.SetCaseSelectedForOutput(case)
            self.model.Results.Setup.SetComboSelectedForOutput(case)
            
        for point in point_names:
            res = self.model.Results.JointReact(point, 0)
            if res[0] == 0:
                continue

            data['Point'].extend(res[1])
            data['OutputCase'].extend(res[3])
            data['StepType'].extend(res[4])
            data['StepNumber'].extend(res[5])
            data['F1'].extend(res[6])
            data['F2'].extend(res[7])
            data['F3'].extend(res[8])
            data['M1'].extend(res[9])
            data['M2'].extend(res[10])
            data['M3'].extend(res[11])
                
        return pd.DataFrame(data)
    
    @property
    def points_reactions(self):
        if self._points_reactions is None:
            data = self.extract_point_reactions()
            cols = ['F1','F2','F3','M1','M2','M3']
            mask = (data[cols].fillna(0) != 0).any(axis=1) 
            self._points_reactions = data[mask].reset_index(drop=True)

        return self._points_reactions
    
    
    # ==================== FRAMES ====================
    
    @property
    def frame_sections_list(self):
        return list(self.model.PropFrame.GetNameList()[1])
    
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
        
        columns = ['SectionName', 'PropType', 't3', 't2', 'tf', 'tw', 't2b', 'tfb', 'Area']
        data = self.model.PropFrame.GetAllFrameProperties_2()[1:-1]
        data = pd.DataFrame(np.array(data).T, columns=columns)
        data['SectionType'] = data['PropType'].astype(int).map(lambda x: eFramePropType(x).name)
        data = data[['SectionName', 'SectionType', 't3', 't2', 'tf', 'tw', 't2b', 'tfb', 'Area']]
        
        if get_properties:
            df_props = pd.DataFrame(
                data['SectionName'].apply(self.get_frame_section_properties).tolist()
            )
            data = data.merge(df_props, on='SectionName', how='left')
        return data
    
    @property
    def frame_sections_data(self):
        if self._frame_sections_data is None:
            self._frame_sections_data = \
                self.get_frame_section_dimensions(get_properties=True)
        return self._frame_sections_data
    
    @property
    def frame_list(self):
        """Obtiene lista de todos los frames"""
        if self._frame_list is None:
            self._frame_list =  list(self.model.FrameObj.GetNameList()[1])
        return self._frame_list
    
    def get_frame_section(self, frame_name):
        """Obtiene sección asignada a un frame"""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        return self.model.FrameObj.GetSection(frame_name)[0]
    
    def get_frame_points(self, frame_name):
        """Obtiene puntos inicial y final de un frame"""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        result = self.model.FrameObj.GetPoints(frame_name)
        return {'point_i': result[0], 'point_j': result[1]}
    
    def get_frame_coordinates(self,frame_name):
        """Obtiene coordenadas de los puntos inicial y final"""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        points = self.get_frame_points(frame_name)
        coord_i = self.model.PointObj.GetCoordCartesian(points['point_i'])[:-1]
        coord_j = self.model.PointObj.GetCoordCartesian(points['point_j'])[:-1]
        
        return {'coord_i': coord_i, 'coord_j': coord_j}
    
    def get_frame_length(self, frame_name):
        """Obtiene longitud del frame"""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        coords = self.get_frame_coordinates(frame_name)
        coord_i = coords['coord_i']
        coord_j = coords['coord_j']
        
        import numpy as np
        length = np.sqrt(sum((coord_j[i] - coord_i[i])**2 for i in range(3)))
        return length

    @property
    def frame_label_names(self):
        if self._frame_label_names is None:
            data = self.model.FrameObj.GetLabelNameList()
            df = {'Frame':data[1],'Label':data[2],'Story':data[3]}
            self._frame_label_names = pd.DataFrame(df)
        return self._frame_label_names
    
    @property
    def frames_properties(self):
        if self._frames_properties is None:
            data = pd.DataFrame({'Frame':self.frame_list})
            label_data = self.frame_label_names
            data = data.merge(label_data, on='Frame')
            data['Section'] = data['Frame'].map(self.get_frame_section)
            data[['point_i', 'point_j']] = data['Frame'].map(
                self.get_frame_points).apply(pd.Series)
            data[['coord_i', 'coord_j']] = data['Frame'].map(
                self.get_frame_coordinates).apply(pd.Series)
            data['length'] = data['Frame'].map(self.get_frame_length)
            self._frames_properties = data
        
        return self._frames_properties
        
    
    def extract_frame_forces(self,frame_name=None,cases_and_combos=None):
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
        frames = format_list_args(frame_name,self.frame_list)
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
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
            if res[-1] == 1:
                self.model.Analyze.RunAnalysis()

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
    
    @property
    def frames_forces(self):
        if self._frames_forces is None:
            self._frames_forces = self.extract_frame_forces()
        return self._frames_forces
        
    
    # ==================== AREAS  ====================
    @property
    def area_section_list(self):
        return list(self.model.PropArea.GetNameList()[1])
    
    def map_wall_properties(self,section,wall_dict):
        *wall_props, flag = self.model.PropArea.GetWall(section)
        
        if flag != 0:
            return wall_dict
        
        wall_dict['wall'].append(section)
        wall_dict['wallPropType'].append(wall_props[0])
        wall_dict['ShellType'].append(wall_props[1])
        wall_dict['MatProp'].append(wall_props[2])
        wall_dict['Thickness'].append(wall_props[3])
        
        if wall_props[0] == 2:
            props = self.model.PropArea.GetWallAutoSelectList(section)
            wall_dict['AutoSelectList'].append(props[0])
            wall_dict['StartingProperty'].append(props[1])
            return wall_dict
            
        wall_dict['AutoSelectList'].append(None)
        wall_dict['StartingProperty'].append(None)
        return wall_dict
    
    def map_slab_properties(self,section,slab_dict):
        *slab_props, flag = self.model.PropArea.GetSlab(section)
        if flag != 0:
            return slab_dict
        
        slab_dict['slab'].append(section)
        slab_dict['SlabType'].append(slab_props[0])
        slab_dict['ShellType'].append(slab_props[1])
        slab_dict['MatProp'].append(slab_props[2])
        slab_dict['Thickness'].append(slab_props[3])
        
        if slab_props[0] == 3: #ribbed
            rib_props = self.model.PropArea.GetSlabRibbed(section)
            slab_dict['OverallDepth'].append(rib_props[0])
            slab_dict['SlabThickness'].append(rib_props[1])
            slab_dict['StemWidthTop'].append(rib_props[2])
            slab_dict['StemWidthBot'].append(rib_props[3])
            slab_dict['RibSpacing1'].append(rib_props[4])
            slab_dict['RibSpacingDir2'].append(None)
            slab_dict['RibsParallelTo'].append(rib_props[5])
            return slab_dict
            
        if slab_props[0] == 4: #waffle
            waf_props = self.model.PropArea.GetSlabWaffle(section)
            slab_dict['OverallDepth'].append(waf_props[0])
            slab_dict['SlabThickness'].append(waf_props[1])
            slab_dict['StemWidthTop'].append(waf_props[2])
            slab_dict['StemWidthBot'].append(waf_props[3])
            slab_dict['RibSpacing1'].append(waf_props[4])
            slab_dict['RibSpacingDir2'].append(waf_props[5])
            slab_dict['RibsParallelTo'].append(None)
            return slab_dict
        
        slab_dict['OverallDepth'].append(None)
        slab_dict['SlabThickness'].append(None)
        slab_dict['StemWidthTop'].append(None)
        slab_dict['StemWidthBot'].append(None)
        slab_dict['RibSpacing1'].append(None)
        slab_dict['RibSpacingDir2'].append(None)
        slab_dict['RibsParallelTo'].append(None)
        
        return slab_dict
    
    def map_deck_properties(self,section,deck_dict):
        *deck_props, flag = self.model.PropArea.GetDeck_1(section)

        if flag != 0:
            return deck_dict
        
        deck_dict['deck'].append(section)
        deck_dict['DeckType'].append(deck_props[0])
        deck_dict['SlabFillMatProp'].append(deck_props[1])
        deck_dict['DeckMatProp'].append(deck_props[2])
        deck_dict['SlabDepth'].append(deck_props[3])
        deck_dict['RibDepth'].append(deck_props[4])
        deck_dict['RibWidthTop'].append(deck_props[5])
        deck_dict['RibWidthBot'].append(deck_props[6])
        deck_dict['RibSpacing'].append(deck_props[7])
        deck_dict['DeckShearThickness'].append(deck_props[8])
        deck_dict['DeckUnitWeight'].append(deck_props[9])
        deck_dict['ShearStudDia'].append(deck_props[10])
        deck_dict['ShearStudHs'].append(deck_props[11])
        deck_dict['ShearStudFu'].append(deck_props[12])
        
        return deck_dict
        
    
    def map_area_properties(self):
        sections = self.area_section_list
        walls = {'wall':[],'wallPropType':[],'ShellType':[],
                 'MatProp':[],'Thickness':[],'AutoSelectList':[],'StartingProperty':[]}
        slabs = {'slab':[],'SlabType':[],'ShellType':[],'MatProp':[],
                 'Thickness':[],'OverallDepth':[],'SlabThickness':[],
                 'StemWidthTop':[],'StemWidthBot':[],'RibSpacing1':[],
                 'RibSpacingDir2':[],'RibsParallelTo':[]}
        decks = {'deck':[],'DeckType':[],'SlabFillMatProp':[],
                 'DeckMatProp':[],'SlabDepth':[],'RibDepth':[],
                 'RibWidthTop':[],'RibWidthBot':[],'RibSpacing':[],
                 'DeckShearThickness':[],'DeckUnitWeight':[],
                 'ShearStudDia':[],'ShearStudHs':[],'ShearStudFu':[]}
        
        for section in sections:
            walls = self.map_wall_properties(section,walls)
            slabs = self.map_slab_properties(section,slabs)
            decks = self.map_deck_properties(section,decks)
            
        for name in ['walls', 'slabs', 'decks']:
            df = pd.DataFrame(locals()[name]) 
            num_cols = df.select_dtypes(include='number').columns
            df[num_cols] = df[num_cols].fillna(0)
            locals()[name] = df
            
        self._wall_sections_data = walls
        self._slab_sections_data = slabs
        self._deck_sections_data = decks

    
    @property
    def area_list(self):
        return list(self.model.PropArea.GetNameList()[1])
    
    def get_area_section(self, area_name):
        """Obtiene sección asignada a un área"""
        return self.model.AreaObj.GetProperty(area_name)[0]
    
    def get_area_points(self, area_name):
        """Obtiene puntos que definen un área"""
        result = self.model.AreaObj.GetPoints(area_name)
        return list(result[1])
    
    @property
    def area_geometry(self): 
        """Propiedades de los objetos area """ 
        if self._area_geometry is None:
            data = self.model.AreaObj.GetAllAreas() 
            area_name = data[1] 
            orientation = data[2] 
            points = [data[5][i+1:j+1] for i,j in 
                      zip((-1,)+data[4],data[4])] 
            p_x = [data[6][i+1:j+1] for i,j in 
                   zip((-1,)+data[4],data[4])] 
            p_y = [data[7][i+1:j+1] for i,j in 
                   zip((-1,)+data[4],data[4])] 
            p_z = [data[8][i+1:j+1] for i,j in 
                   zip((-1,)+data[4],data[4])] 
            type_map = {1:'wall',2:'floor',3:'ramp',4:'null',5:'other'} 
            area_type = [type_map[o] for o in orientation] 
            data =  pd.DataFrame({ 
                'name' : area_name, 
                'area_type' : area_type, 
                'points_name': points, 
                'points_x': p_x, 
                'points_y': p_y, 
                'points_z': p_z })
            data['section'] = data['name'].map(self.get_area_section)
            data = data[['name','area_type','section','points_x',
                         'points_y','points_z']]
            self._area_geometry = data
        return self._area_geometry              
    
    def extract_area_forces(self, area_name=None, cases_and_combos=None):
        """
        Extrae fuerzas en áreas (losas)
        
        Parameters:
        -----------
        area_name : str, optional
            Nombre del área. Si None, extrae todas.
        cases_and_combos : list, optional
            Lista de casos/combos. Si None, usa todos.
        
        Returns:
        --------
        DataFrame con F11, F22, F12, M11, M22, M12, V13, V23 para cada área
        """
        areas = format_list_args(area_name,self.area_list)
        cases_and_combos = format_list_args(cases_and_combos,
                            self.handler.design_cases_and_combos)
    
        data = {
            'AreaName': [], 'PointName': [], 'OutputCase': [], 
            'StepType': [], 'StepNumber': [],
            'F11': [], 'F22': [], 'F12': [],
            'M11': [], 'M22': [], 'M12': [],
            'V13': [], 'V23': []
        }
        
        self.model.View.RefreshView(0, False)
        
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        self.handler.set_envelopes_for_dysplay(set_envelopes=False)
        for case in cases_and_combos:
            self.model.Results.Setup.SetCaseSelectedForOutput(case)
            self.model.Results.Setup.SetComboSelectedForOutput(case)
            
        area_force = self.model.Results.AreaForceShell
        for area in areas:
            res = area_force(area, 0)
            if res[-1] == 0:
                self.model.Analyze.RunAnalysis()
                res = area_force(area, 0)

            data['AreaName'].extend(res[1])
            data['PointName'].extend(res[3])
            data['OutputCase'].extend(res[4])
            data['StepType'].extend(res[5])
            data['StepNumber'].extend(res[6])
            data['F11'].extend(res[7])
            data['F22'].extend(res[8])
            data['F12'].extend(res[9])
            data['M11'].extend(res[14])
            data['M22'].extend(res[15])
            data['M12'].extend(res[16])
            data['V13'].extend(res[20])
            data['V23'].extend(res[21])
                
        return pd.DataFrame(data)
    
    @property
    def area_forces(self):
        if self._area_forces is None:
            self._area_forces = self.extract_area_forces(cases_and_combos=self.design_cases)
        return self._area_forces
    
    # ==================== SLABS/FLOORS ====================
    @property
    def slab_sections_data(self):
        if self._slab_sections_data is None:
            self.map_area_properties()
        return self._slab_sections_data
    
    @property
    def deck_sections_data(self):
        if self._deck_sections_data is None:
            self.map_area_properties()
        return self._deck_sections_data
    
    @property
    def floor_sections_list(self):
        df = self.area_geometry
        slab_list = df[df['area_type']=='floor']['section']
        return list(slab_list.unique())
    
        
    @property
    def floor_list(self):
        """Obtiene la lista de elementos piso"""
        properties = self.area_geometry
        return list(properties[properties['type']=='floor']['name'])
    
    
    
    # ==================== WALLS ====================
    @property
    def wall_sections_data(self):
        if self._wall_sections_data is None:
            self.map_area_properties()
        return self._wall_sections_data
    
    @property
    def wall_list(self):
        """Obtiene la lista de elementos piso"""
        properties = self.area_geometry
        return list(properties[properties['type']=='wall']['name'])
    
    @property
    def pier_list(self):
        return list(self.model.PierLabel.GetNameList()[1])
    
    def extract_pier_forces(self,piers=None,cases_and_combos=None):
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        for case in cases_and_combos:
            self.model.Results.Setup.SetCaseSelectedForOutput(case)
            self.model.Results.Setup.SetComboSelectedForOutput(case)
        
        df = {'Pier':[],'Story':[],'OutputCase':[],
                'Location':[],'P':[],'V2':[],'V3':[],
                'T':[],'M2':[],'M3':[]}
            
        data = self.model.Results.PierForce()

        if data[-1] == 1:
            self.model.Analyze.RunAnalysis()

        df['Pier'].extend(data[2])
        df['Story'].extend(data[1])
        df['OutputCase'].extend(data[3])
        df['Location'].extend(data[4])
        df['P'].extend(data[5])
        df['V2'].extend(data[6])
        df['V3'].extend(data[7])
        df['T'].extend(data[8])
        df['M2'].extend(data[9])
        df['M3'].extend(data[10])
        df = pd.DataFrame(df)
        
        if piers is None:
            return df
        piers = format_list_args(piers,self.pier_list)
        
        return df[df['Pier'].isin(piers)]
        
    @property
    def pier_forces(self):
        self.model.DesignForces.PierDesignForces()
   

    # ==================== STORIES ====================   
    @property
    def stories(self):
        return self.model.Story.GeStories()[1]
    
    def get_story_height(self,story):
        return self.model.Story.GetHeight(story)[0]
    
    def get_story_forces(self,cases_and_combos=None):
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
        
        self.model.DatabaseTables.\
            SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.\
            SetLoadCombinationsSelectedForDisplay(cases_and_combos)
            
        self.set_envelopes_for_dysplay()
        df = self.get_table('Story Forces')
        df[['P','VX','VY','T','MX','MY']] =\
            df[['P','VX','VY','T','MX','MY']].astype(float)
        df['Height'] = df['Story'].map(self.get_story_height)
        df = df.drop(['CaseType','StepNumber','StepLabel'],axis=1)
        
        return df
    
    @property
    def story_forces(self):
        return self.get_story_forces()
    
    def get_story_displacements(self,cases_and_combos=None):
        cases_and_combos = format_list_args(cases_and_combos,
                            self.seismic_cases_and_combos)
        self.model.DatabaseTables.\
            SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.\
            SetLoadCombinationsSelectedForDisplay(cases_and_combos)
            
        df = self.get_table('Story Max Over Avg Displacements')
        df[['Maximum','Average','Ratio']] =\
            df[['Maximum','Average','Ratio']].astype(float)
        df['Height'] = df['Story'].map(self.get_story_height)
        df = df.drop(['CaseType','StepNumber','StepLabel'],axis=1)
        
        return df
    
    @property
    def story_displacements(self):
        return self.get_story_displacements()
    
    def get_story_drifts(self,cases_and_combos=None):
        cases_and_combos = format_list_args(cases_and_combos,
                            self.seismic_cases_and_combos)
        self.model.DatabaseTables.\
            SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.\
            SetLoadCombinationsSelectedForDisplay(cases_and_combos)
            
        df = self.get_table('Diaphragm Max Over Avg Drifts')
        df[['Max Drift','Avg Drift','Ratio']] =\
            df[['Max Drift','Avg Drift','Ratio']].astype(float)
        df['Height'] = df['Story'].map(self.get_story_height)
        df = df.drop(['CaseType','StepNumber','StepLabel',
                      'Max Loc X','Max Loc Y','Max Loc Z','Label'],axis=1)
        return df
    
    @property
    def story_drifts(self):
        return self.get_story_drifts()
  
