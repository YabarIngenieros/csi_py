import pandas as pd
import numpy as np

from .constants import EtabsError, eFramePropType
from .handler import Handler

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
        

class DataExtractor(Handler):
    """
    Capa de extracción de datos sobre la conexión base CSI.

    Reúne propiedades cacheadas y métodos para extraer geometría, cargas y resultados.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stories = None
        self._grid_system_names = None
        self._grid_lines = None
        
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
        self._frames_connectivity = None
        self._beams_connectivity = None
        self._columns_connectivity = None
        
        self._wall_sections_data = None
        self._slab_sections_data = None
        self._deck_sections_data = None
        self._area_geometry = None
        self._area_forces = None
        
        self._strips = None

        self._modal_cases = None
        self._modal_data = None
        
    def set_envelopes_for_dysplay(self,set_envelopes=True):
        """
        Configura el formato de resultados mostrado en tablas.

        Por defecto selecciona envolventes para casos compuestos y análisis no lineales.
        """
        MultistepStatic=1 if set_envelopes else 2
        NonlinearStatic=1 if set_envelopes else 2
        self.model.DatabaseTables.SetOutputOptionsForDisplay(False,False,0,0,True,0,0,True,0,0,MultistepStatic,NonlinearStatic,1,1,2)
        
    @property
    def available_tables(self):
        data = self.model.DatabaseTables.GetAvailableTables()
        return pd.DataFrame(zip(data[1],data[3]),columns=['Table','ImportType'])
    
    @property
    def editable_tables(self):
        df = self.available_tables
        df = df[df['ImportType'].isin([2,3])].reset_index(drop=True)
        return df
    
    def get_table(self, table_name, set_envelopes=True, runned=False):
        """
        Extrae una tabla de visualización del modelo.

        Puede ejecutar el análisis automáticamente si la tabla no tiene resultados.
        """
        self.set_envelopes_for_dysplay(set_envelopes=set_envelopes)
        data = self.model.DatabaseTables.GetTableForDisplayArray(
            table_name, FieldKeyList='', GroupName=''
        )

        flag = data[-1]
        if flag == 1:
            if runned == True:
                return pd.DataFrame()
            self.model.Analyze.RunAnalysis()
            return self.get_table(table_name,set_envelopes,runned=True)

        elif flag == -96:
            raise ValueError(f"La tabla '{table_name}' no existe en el modelo ETABS.")

        elif flag != 0:
            raise EtabsError(f"Error al extraer la tabla, flag devuelto de {flag}")

        columns = data[2]
        num_records = data[3]
        table_data = [i if i else '' for i in data[4]]

        # Convertir a DataFrame
        df = pd.DataFrame(table_data)
        df = df.values.reshape(num_records, len(columns))
        table = pd.DataFrame(df, columns=columns)
        return table

    
    @property
    def tabular_data(self):
        """
        Retorna todas las tablas editables como un diccionario de DataFrames.

        El resultado se cachea tras la primera carga.
        """
        if self._tabular_data is None:
            table_data = {}
            for table in self.editable_tables['Table']:
                data = self.get_table(table,set_envelopes=False)
                table_data[table] = data
            self._tabular_data = table_data
        return self._tabular_data

    # ==================== GRIDS ====================

    @property
    def grid_system_names(self):
        if self._grid_system_names is None:
            names = []
            try:
                table = self.get_table('Grid Definitions - Grid Lines', set_envelopes=False)
                for column in ('GridSystem', 'Grid System', 'GridSys', 'Name', 'Grid System Name'):
                    if column in table.columns:
                        names = table[column].tolist()
                        break
            except Exception:
                try:
                    names = list(self.model.GridSys.GetNameList()[1])
                except Exception:
                    table = self.get_table('Grid Definitions - General', set_envelopes=False)
                    for column in ('Name', 'Grid System', 'GridSys', 'Grid System Name'):
                        if column in table.columns:
                            names = table[column].tolist()
                            break
            self._grid_system_names = list(set(str(name).strip() for name in names if str(name).strip()))
        return self._grid_system_names

    def get_grid_system(self, grid_system_name=None):
        """
        Extrae líneas de grid del modelo como ``DataFrame``.

        Si ``grid_system_name`` es ``None``, retorna todas las líneas.
        Si se indica un nombre, filtra por ese sistema.
        """
        lines = self.grid_lines.copy()
        if grid_system_name is None:
            return lines.reset_index(drop=True)

        if not isinstance(grid_system_name, str) or not grid_system_name.strip():
            raise ValueError("Debe indicar un nombre de grid válido.")

        grid_system_name = grid_system_name.strip()
        lines = lines[lines['GridSystem'] == grid_system_name].reset_index(drop=True)
        if lines.empty:
            raise ValueError(f"El grid system '{grid_system_name}' no existe en el modelo.")
        return lines

    @property
    def grid_lines(self):
        """
        Retorna todas las líneas de grid de todos los sistemas del modelo.
        """
        if self._grid_lines is None:
            try:
                raw = self.get_table('Grid Definitions - Grid Lines', set_envelopes=False).copy()
                self._grid_lines = self._normalize_grid_lines_table(raw)
            except Exception:
                frames = [
                    self._grid_system_to_lines(self._get_grid_system_api(grid_name))
                    for grid_name in self.grid_system_names
                ]
                frames = [frame for frame in frames if not frame.empty]
                if frames:
                    self._grid_lines = pd.concat(frames, ignore_index=True)
                else:
                    self._grid_lines = pd.DataFrame(columns=[
                        'GridSystem', 'Axis', 'LineType', 'GridLineID', 'Ordinate',
                        'Visible', 'BubbleLoc', 'X1', 'Y1', 'X2', 'Y2',
                        'Xo', 'Yo', 'RZ', 'GridSysType'
                    ])
        return self._grid_lines

    def _normalize_grid_lines_table(self, table):
        columns = {column.lower().strip(): column for column in table.columns}

        def pick_column(*names):
            for name in names:
                key = name.lower().strip()
                if key in columns:
                    return columns[key]
            return None

        grid_system_col = pick_column('GridSystem', 'Grid System', 'GridSys', 'Name')
        line_type_col = pick_column('LineType', 'GridLineType', 'Grid Line Type')
        grid_line_id_col = pick_column('GridLineID', 'Grid Line ID', 'ID')
        ordinate_col = pick_column('Ordinate')
        visible_col = pick_column('Visible')
        bubble_col = pick_column('BubbleLoc', 'Bubble Location', 'Bubble')
        x1_col = pick_column('X1', 'X Start', 'Start X')
        y1_col = pick_column('Y1', 'Y Start', 'Start Y')
        x2_col = pick_column('X2', 'X End', 'End X')
        y2_col = pick_column('Y2', 'Y End', 'End Y')

        if grid_system_col is None or line_type_col is None or grid_line_id_col is None or ordinate_col is None:
            raise ValueError("La tabla 'Grid Definitions - Grid Lines' no tiene las columnas esperadas.")

        data = pd.DataFrame({
            'GridSystem': table[grid_system_col].astype(str).str.strip(),
            'Axis': table[line_type_col].map(self._parse_grid_axis),
            'LineType': table[line_type_col].astype(str).str.strip(),
            'GridLineID': table[grid_line_id_col].astype(str).str.strip(),
            'Ordinate': pd.to_numeric(table[ordinate_col], errors='coerce'),
            'Visible': table[visible_col].map(self._parse_grid_visible) if visible_col else True,
            'BubbleLoc': table[bubble_col].astype(str).str.strip() if bubble_col else '',
            'X1': pd.to_numeric(table[x1_col], errors='coerce') if x1_col else np.nan,
            'Y1': pd.to_numeric(table[y1_col], errors='coerce') if y1_col else np.nan,
            'X2': pd.to_numeric(table[x2_col], errors='coerce') if x2_col else np.nan,
            'Y2': pd.to_numeric(table[y2_col], errors='coerce') if y2_col else np.nan,
        })

        data = data[data['GridSystem'] != ''].reset_index(drop=True)
        data['Axis'] = data['Axis'].fillna('')
        data['GridSysType'] = data['Axis'].map(lambda axis: 'Cartesian' if axis in ('X', 'Y') else '')
        data['Xo'] = 0.0
        data['Yo'] = 0.0
        data['RZ'] = 0.0
        return data[[
            'GridSystem', 'Axis', 'LineType', 'GridLineID', 'Ordinate',
            'Visible', 'BubbleLoc', 'X1', 'Y1', 'X2', 'Y2',
            'Xo', 'Yo', 'RZ', 'GridSysType'
        ]]

    def _parse_grid_axis(self, value):
        text = str(value).strip().upper()
        if text.startswith('X'):
            return 'X'
        if text.startswith('Y'):
            return 'Y'
        if 'X' in text and 'CARTESIAN' in text:
            return 'X'
        if 'Y' in text and 'CARTESIAN' in text:
            return 'Y'
        return text

    def _parse_grid_visible(self, value):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in ('yes', 'true', '1', 'si', 'sí'):
            return True
        if text in ('no', 'false', '0'):
            return False
        return bool(value)

    def _get_grid_system_api(self, grid_system_name):
        data = self.model.GridSys.GetGridSys_2(grid_system_name)
        if data[-1] != 0:
            raise EtabsError(
                f"Error al extraer el grid system '{grid_system_name}', flag devuelto {data[-1]}"
            )
        return {
            'Name': grid_system_name,
            'Xo': float(data[0]),
            'Yo': float(data[1]),
            'RZ': float(data[2]),
            'GridSysType': data[3],
            'NumXLines': int(data[4]),
            'NumYLines': int(data[5]),
            'GridLineIDX': tuple(data[6]),
            'GridLineIDY': tuple(data[7]),
            'OrdinateX': tuple(data[8]),
            'OrdinateY': tuple(data[9]),
            'VisibleX': tuple(data[10]),
            'VisibleY': tuple(data[11]),
            'BubbleLocX': tuple(data[12]),
            'BubbleLocY': tuple(data[13]),
        }

    def _grid_system_to_lines(self, grid_data):
        x_lines = pd.DataFrame({
            'GridSystem': grid_data['Name'],
            'Axis': 'X',
            'LineType': 'X (Cartesian)',
            'GridLineID': list(grid_data['GridLineIDX'])[:grid_data['NumXLines']],
            'Ordinate': list(grid_data['OrdinateX'])[:grid_data['NumXLines']],
            'Visible': list(grid_data['VisibleX'])[:grid_data['NumXLines']],
            'BubbleLoc': list(grid_data['BubbleLocX'])[:grid_data['NumXLines']],
            'X1': np.nan,
            'Y1': np.nan,
            'X2': np.nan,
            'Y2': np.nan,
        })
        y_lines = pd.DataFrame({
            'GridSystem': grid_data['Name'],
            'Axis': 'Y',
            'LineType': 'Y (Cartesian)',
            'GridLineID': list(grid_data['GridLineIDY'])[:grid_data['NumYLines']],
            'Ordinate': list(grid_data['OrdinateY'])[:grid_data['NumYLines']],
            'Visible': list(grid_data['VisibleY'])[:grid_data['NumYLines']],
            'BubbleLoc': list(grid_data['BubbleLocY'])[:grid_data['NumYLines']],
            'X1': np.nan,
            'Y1': np.nan,
            'X2': np.nan,
            'Y2': np.nan,
        })
        lines = pd.concat([x_lines, y_lines], ignore_index=True)
        if lines.empty:
            return pd.DataFrame(columns=[
                'GridSystem', 'Axis', 'LineType', 'GridLineID', 'Ordinate',
                'Visible', 'BubbleLoc', 'X1', 'Y1', 'X2', 'Y2',
                'Xo', 'Yo', 'RZ', 'GridSysType'
            ])
        lines['Ordinate'] = lines['Ordinate'].astype(float)
        lines['Visible'] = lines['Visible'].astype(bool)
        lines['Xo'] = grid_data['Xo']
        lines['Yo'] = grid_data['Yo']
        lines['RZ'] = grid_data['RZ']
        lines['GridSysType'] = grid_data['GridSysType']
        return lines.reset_index(drop=True)
        
    
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
        """
        Retorna los casos base contenidos en una combinación de carga.

        Si la combinación incluye otras combinaciones, el desglose es recursivo.
        """
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
    def gravity_cases(self):
        return list(set(self.cases).difference(self.seismic_cases))
    
    @property
    def gravity_combos(self):
        return list(set(self.combos).difference(self.seismic_combos))
    
    @property
    def gravity_cases_and_combos(self):
        return self.gravity_cases + self.gravity_combos
    
    def select_cases_and_combos(self,cases_and_combos):
        """
        Selecciona casos y combinaciones para la salida tabular activa.

        Esta selección afecta las tablas de resultados extraídas después.
        """
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)
        
    def get_response_spectrum(self,spectrum_names='all'):
        """
        Extrae funciones de espectro de respuesta desde tablas del modelo.

        Puede devolver todos los espectros o filtrar por nombre.
        """
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
        """
        Obtiene propiedades mecánicas básicas de uno o varios materiales.

        Retorna un DataFrame con tipo de material, simetría y constantes principales.
        """
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
    
    @property
    def base_points(self):
        base = self.stories[0]
        return self.model.PointObj.GetNameListOnStory(base)[1]
    
    def get_point_coordinates(self, point_names):
        """
        Obtiene coordenadas cartesianas de uno o varios puntos.

        Retorna un DataFrame con columnas ``Point``, ``X``, ``Y`` y ``Z``.
        """
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
        """
        Obtiene las restricciones asignadas a uno o varios puntos.

        El resultado indica grados de libertad traslacionales y rotacionales restringidos.
        """
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
    

    def get_point_reactions(self,point_names=None,cases_and_combos=None):
        """Extrae reacciones nodales para los puntos solicitados."""
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
            data = self.get_point_reactions()
            cols = ['F1','F2','F3','M1','M2','M3']
            mask = (data[cols].fillna(0) != 0).any(axis=1) 
            self._points_reactions = data[mask].reset_index(drop=True)

        return self._points_reactions
    
    def get_selected_points(self):
        selection = self.model.SelectObj.GetSelected()
        selected = [selection[2][i] for i in range(len(selection[2])) if selection[1][i] == 1]
        return selected
    
    # ==================== FRAMES ====================
    
    @property
    def frame_sections_list(self):
        return list(self.model.PropFrame.GetNameList()[1])
    
    def get_frame_section_properties(self, section_name):
        """
        Obtiene propiedades seccionales de un frame.

        Retorna un diccionario con área, inercia, torsión y módulos resistentes.
        """
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
        """
        Extrae dimensiones geométricas de las secciones de frame.

        Si ``get_properties`` es verdadero, agrega propiedades seccionales calculadas.
        """
        
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
        """Obtiene la sección asignada a un frame."""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        return self.model.FrameObj.GetSection(frame_name)[0]
    
    def get_frame_points(self, frame_name):
        """Obtiene los puntos inicial y final de un frame."""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        result = self.model.FrameObj.GetPoints(frame_name)
        return {'point_i': result[0], 'point_j': result[1]}
    
    def get_frame_coordinates(self,frame_name):
        """Obtiene las coordenadas de los extremos de un frame."""
        if isinstance(frame_name,int):
            frame_name = str(frame_name)
        points = self.get_frame_points(frame_name)
        coord_i = self.model.PointObj.GetCoordCartesian(points['point_i'])[:-1]
        coord_j = self.model.PointObj.GetCoordCartesian(points['point_j'])[:-1]
        
        return {'coord_i': coord_i, 'coord_j': coord_j}
    
    def get_frame_length(self, frame_name):
        """Calcula la longitud geométrica de un frame."""
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
        
    
    def get_frame_forces(self,frame_name=None,cases_and_combos=None):
        """Extrae fuerzas internas de frames usando la API nativa."""
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
            self._frames_forces = self.get_frame_forces()
        return self._frames_forces
    
    @property
    def label_beams(self):
        label_names = self.frame_label_names
        return (label_names[label_names['Label'].str.startswith('B')]
                 ['Label'].unique())
        
    @property
    def label_columns(self):
        label_names = self.frame_label_names
        return (label_names[label_names['Label'].str.startswith('C')]
                 ['Label'].unique())

    def _point_on_grid_line(self, point_xy, grid_line, tol=1e-6):
        x, y = point_xy
        axis = str(grid_line.get('Axis', '')).strip().upper()
        ordinate = grid_line.get('Ordinate', np.nan)

        if axis == 'X' and pd.notna(ordinate):
            return abs(float(x) - float(ordinate)) <= tol
        if axis == 'Y' and pd.notna(ordinate):
            return abs(float(y) - float(ordinate)) <= tol

        x1 = grid_line.get('X1', np.nan)
        y1 = grid_line.get('Y1', np.nan)
        x2 = grid_line.get('X2', np.nan)
        y2 = grid_line.get('Y2', np.nan)
        if pd.notna(x1) and pd.notna(y1) and pd.notna(x2) and pd.notna(y2):
            dx = float(x2) - float(x1)
            dy = float(y2) - float(y1)
            seg_len_sq = dx * dx + dy * dy
            if seg_len_sq <= tol ** 2:
                return np.hypot(float(x) - float(x1), float(y) - float(y1)) <= tol

            px = float(x) - float(x1)
            py = float(y) - float(y1)
            cross = abs(px * dy - py * dx)
            if cross / np.sqrt(seg_len_sq) > tol:
                return False

            dot = px * dx + py * dy
            if dot < -tol or dot > seg_len_sq + tol:
                return False
            return True

        return False

    def _resolve_beam_grid(self, point_i_xy, point_j_xy, tol=1e-6):
        for _, grid_line in self.grid_lines.iterrows():
            if self._point_on_grid_line(point_i_xy, grid_line, tol=tol) and \
               self._point_on_grid_line(point_j_xy, grid_line, tol=tol):
                return str(grid_line['GridLineID']).strip()
        return ''

    def _append_grid_id(self, current_value, grid_id):
        grid_id = str(grid_id).strip()
        if not grid_id:
            return current_value
        if not current_value:
            return grid_id
        existing = [item for item in current_value.split('|') if item]
        if grid_id in existing:
            return current_value
        return f"{current_value}|{grid_id}"

    def _split_grid_ids(self, value):
        if value in (None, ''):
            return []
        return [item.strip() for item in str(value).split('|') if item.strip()]

    def _grid_value_matches(self, value, targets):
        if not targets:
            return False
        values = set(self._split_grid_ids(value))
        return bool(values.intersection(targets))

    def _resolve_column_grids(self, point_i_xy, point_j_xy, tol=1e-6):
        grid_x = ''
        grid_y = ''
        general = ''

        for _, grid_line in self.grid_lines.iterrows():
            if not (
                self._point_on_grid_line(point_i_xy, grid_line, tol=tol)
                and self._point_on_grid_line(point_j_xy, grid_line, tol=tol)
            ):
                continue

            grid_id = grid_line.get('GridLineID', '')
            axis = str(grid_line.get('Axis', '')).strip().upper()
            if axis == 'X':
                grid_x = self._append_grid_id(grid_x, grid_id)
            elif axis == 'Y':
                grid_y = self._append_grid_id(grid_y, grid_id)
            else:
                general = self._append_grid_id(general, grid_id)

        return {
            'GridX': grid_x,
            'GridY': grid_y,
            'General': general,
        }

    def get_beams_connectivity(self, beams_label=None, tol=1e-6):
        """
        Retorna conectividad de vigas y su pertenencia a grid como ``DataFrame``.

        Una viga pertenece a un grid solo si ambos puntos extremos caen sobre la misma línea.
        """
        beams = self.frames_properties.copy()
        beams = beams[beams['Label'].astype(str).str.startswith('B')].reset_index(drop=True)

        if beams_label is not None:
            beams_label = format_list_args(beams_label, check_values=False)
            beams = beams[beams['Label'].isin(beams_label)].reset_index(drop=True)

        if beams.empty:
            return pd.DataFrame(columns=[
                'Beam', 'Label', 'Story', 'Section', 'point_i', 'point_j', 'Grid'
            ])

        points_i = self.points_coordinates.rename(columns={
            'Point': 'point_i',
            'X': 'Xi',
            'Y': 'Yi',
            'Z': 'Zi',
        })
        beams = beams.merge(points_i, on='point_i', how='left')

        points_j = self.points_coordinates.rename(columns={
            'Point': 'point_j',
            'X': 'Xj',
            'Y': 'Yj',
            'Z': 'Zj',
        })
        beams = beams.merge(points_j, on='point_j', how='left')

        beams['Grid'] = beams.apply(
            lambda row: self._resolve_beam_grid(
                (row['Xi'], row['Yi']),
                (row['Xj'], row['Yj']),
                tol=tol,
            ),
            axis=1,
        )

        beams = beams.rename(columns={'Frame': 'Beam'})
        return beams[['Beam', 'Label', 'Story', 'Section', 'point_i', 'point_j', 'Grid']].reset_index(drop=True)

    @property
    def beams_connectivity(self):
        if self._beams_connectivity is None:
            self._beams_connectivity = self.get_beams_connectivity()
        return self._beams_connectivity

    def get_beam_connectivity(self, beams_label=None, tol=1e-6):
        """Alias de :meth:`get_beams_connectivity`."""
        return self.get_beams_connectivity(beams_label=beams_label, tol=tol)

    @property
    def beam_connectivity(self):
        """Alias de :attr:`beams_connectivity`."""
        return self.beams_connectivity

    def get_frames_connectivity(self, frame_type=None, labels=None, tol=1e-6):
        """
        Retorna una vista conjunta de conectividad para vigas y columnas.

        ``frame_type`` acepta ``beam``, ``column`` o ``None``.
        ``labels`` filtra por labels del tipo solicitado.
        """
        frames = []
        frame_type_norm = None if frame_type is None else str(frame_type).strip().lower()
        if frame_type_norm not in (None, '', 'beam', 'beams', 'column', 'columns'):
            raise ValueError("frame_type debe ser None, 'beam' o 'column'.")

        if frame_type_norm in (None, '', 'beam', 'beams'):
            beams = self.get_beams_connectivity(beams_label=labels, tol=tol).copy()
            if not beams.empty:
                beams['FrameType'] = 'Beam'
                beams['Frame'] = beams['Beam']
                beams['GridX'] = ''
                beams['GridY'] = ''
                beams['General'] = beams['Grid']
                frames.append(beams[[
                    'Frame', 'FrameType', 'Label', 'Story', 'Section',
                    'point_i', 'point_j', 'Grid', 'GridX', 'GridY', 'General'
                ]])

        if frame_type_norm in (None, '', 'column', 'columns'):
            columns = self.get_columns_connectivity(columns_label=labels, tol=tol).copy()
            if not columns.empty:
                columns['FrameType'] = 'Column'
                columns['Frame'] = columns['Column']
                columns['Grid'] = ''
                frames.append(columns[[
                    'Frame', 'FrameType', 'Label', 'Story', 'Section',
                    'point_i', 'point_j', 'Grid', 'GridX', 'GridY', 'General'
                ]])

        if not frames:
            return pd.DataFrame(columns=[
                'Frame', 'FrameType', 'Label', 'Story', 'Section',
                'point_i', 'point_j', 'Grid', 'GridX', 'GridY', 'General'
            ])

        return pd.concat(frames, ignore_index=True)

    @property
    def frames_connectivity(self):
        if self._frames_connectivity is None:
            self._frames_connectivity = self.get_frames_connectivity()
        return self._frames_connectivity

    def filter_frames_by_grid(self, grid=None, grid_x=None, grid_y=None,
                              story=None, frame_type=None, labels=None, tol=1e-6):
        """
        Filtra frames por eje, intersección de ejes y/o piso.

        - ``grid`` busca frames asociados a un solo eje.
        - ``grid_x`` + ``grid_y`` busca intersección de dos ejes.
        - ``story`` filtra por piso.
        """
        frames = self.get_frames_connectivity(frame_type=frame_type, labels=labels, tol=tol).copy()
        if frames.empty:
            return frames

        grid_targets = set(format_list_args(grid, check_values=False) or [])
        grid_x_targets = set(format_list_args(grid_x, check_values=False) or [])
        grid_y_targets = set(format_list_args(grid_y, check_values=False) or [])
        story_targets = set(format_list_args(story, check_values=False) or [])

        if story_targets:
            frames = frames[frames['Story'].isin(story_targets)]

        if grid_targets:
            mask_grid = frames.apply(
                lambda row: (
                    self._grid_value_matches(row.get('Grid', ''), grid_targets)
                    or self._grid_value_matches(row.get('GridX', ''), grid_targets)
                    or self._grid_value_matches(row.get('GridY', ''), grid_targets)
                    or self._grid_value_matches(row.get('General', ''), grid_targets)
                ),
                axis=1,
            )
            frames = frames[mask_grid]

        if grid_x_targets:
            mask_grid_x = frames['GridX'].apply(lambda value: self._grid_value_matches(value, grid_x_targets))
            frames = frames[mask_grid_x]

        if grid_y_targets:
            mask_grid_y = frames['GridY'].apply(lambda value: self._grid_value_matches(value, grid_y_targets))
            frames = frames[mask_grid_y]

        return frames.reset_index(drop=True)

    def get_frames_on_grid(self, grid, story=None, frame_type=None, labels=None, tol=1e-6):
        """Alias expresivo para filtrar frames en un solo eje."""
        return self.filter_frames_by_grid(
            grid=grid,
            story=story,
            frame_type=frame_type,
            labels=labels,
            tol=tol,
        )

    def get_frames_at_intersection(self, grid_x, grid_y, story=None,
                                   frame_type=None, labels=None, tol=1e-6):
        """Alias expresivo para filtrar frames en la intersección de dos ejes."""
        return self.filter_frames_by_grid(
            grid_x=grid_x,
            grid_y=grid_y,
            story=story,
            frame_type=frame_type,
            labels=labels,
            tol=tol,
        )

    def get_frame_connectivity(self, frame_type=None, labels=None, tol=1e-6):
        """Alias de :meth:`get_frames_connectivity`."""
        return self.get_frames_connectivity(frame_type=frame_type, labels=labels, tol=tol)

    @property
    def frame_connectivity(self):
        """Alias de :attr:`frames_connectivity`."""
        return self.frames_connectivity

    def get_columns_connectivity(self, columns_label=None, tol=1e-6):
        """
        Retorna conectividad de columnas y su pertenencia a grids como ``DataFrame``.

        La salida separa la pertenencia en ``GridX``, ``GridY`` y ``General``.
        """
        columns = self.frames_properties.copy()
        columns = columns[columns['Label'].astype(str).str.startswith('C')].reset_index(drop=True)

        if columns_label is not None:
            columns_label = format_list_args(columns_label, check_values=False)
            columns = columns[columns['Label'].isin(columns_label)].reset_index(drop=True)

        if columns.empty:
            return pd.DataFrame(columns=[
                'Column', 'Label', 'Story', 'Section', 'point_i', 'point_j',
                'GridX', 'GridY', 'General'
            ])

        points_i = self.points_coordinates.rename(columns={
            'Point': 'point_i',
            'X': 'Xi',
            'Y': 'Yi',
            'Z': 'Zi',
        })
        columns = columns.merge(points_i, on='point_i', how='left')

        points_j = self.points_coordinates.rename(columns={
            'Point': 'point_j',
            'X': 'Xj',
            'Y': 'Yj',
            'Z': 'Zj',
        })
        columns = columns.merge(points_j, on='point_j', how='left')

        grid_data = columns.apply(
            lambda row: self._resolve_column_grids(
                (row['Xi'], row['Yi']),
                (row['Xj'], row['Yj']),
                tol=tol,
            ),
            axis=1,
        ).apply(pd.Series)
        columns = pd.concat([columns, grid_data], axis=1)

        columns = columns.rename(columns={'Frame': 'Column'})
        return columns[[
            'Column', 'Label', 'Story', 'Section', 'point_i', 'point_j',
            'GridX', 'GridY', 'General'
        ]].reset_index(drop=True)

    @property
    def columns_connectivity(self):
        if self._columns_connectivity is None:
            self._columns_connectivity = self.get_columns_connectivity()
        return self._columns_connectivity

    def get_column_connectivity(self, columns_label=None, tol=1e-6):
        """Alias de :meth:`get_columns_connectivity`."""
        return self.get_columns_connectivity(columns_label=columns_label, tol=tol)

    @property
    def column_connectivity(self):
        """Alias de :attr:`columns_connectivity`."""
        return self.columns_connectivity
    
    def get_beam_forces(self,beams_label=None,cases_and_combos=None):
        beams_label = format_list_args(beams_label,self.label_beams)
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)
        data_forces = self.get_table('Element Forces - Beams')
        data_forces = data_forces[data_forces['Beam'].isin(beams_label)]
        data_forces['_index'] = data_forces.index
        data_forces = data_forces.sort_values(
                by=['OutputCase', '_index'],
                key=lambda col: col.map({nombre: i for i, nombre in enumerate(cases_and_combos)}) if col.name == 'OutputCase' else col
            ).reset_index(drop=True)
        data_forces = data_forces.drop(columns='_index')
        
        return data_forces
    
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
        """
        Clasifica y cachea las propiedades de áreas en muros, losas y decks.

        Usa la API de propiedades de área para poblar los DataFrames auxiliares.
        """
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
        """Obtiene la sección asignada a un área."""
        return self.model.AreaObj.GetProperty(area_name)[0]
    
    def get_area_points(self, area_name):
        """Obtiene los puntos que definen un área."""
        result = self.model.AreaObj.GetPoints(area_name)
        return list(result[1])
    
    @property
    def area_geometry(self): 
        """
        Retorna la geometría básica de los objetos de área.

        Incluye tipo, sección y coordenadas de sus puntos de contorno.
        """
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
    
    def get_area_forces(self, area_name=None, cases_and_combos=None):
        """Extrae fuerzas internas en áreas."""
        areas = format_list_args(area_name,self.area_list)
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
    
        data = {
            'AreaName': [], 'PointName': [], 'OutputCase': [], 
            'StepType': [], 'StepNumber': [],
            'F11': [], 'F22': [], 'F12': [],
            'M11': [], 'M22': [], 'M12': [],
            'V13': [], 'V23': []
        }
        
        self.model.View.RefreshView(0, False)
        
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        self.set_envelopes_for_dysplay(set_envelopes=False)
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
            self._area_forces = self.get_area_forces(cases_and_combos=self.design_cases)
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
        return list(properties[properties['area_type']=='floor']['name'])
    
    # =================== STRIPS ====================
    
    @property
    def strip_list(self):
        if self._strips is not None:
            return self._strips
        d_case = self.design_cases[0]
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay([d_case])
        strip_forces = self.get_table('Strip Forces')
        if strip_forces.empty:
            return []
        if 'StripObject' in strip_forces.columns:
            strips = strip_forces['StripObject'].unique()
        else:
            strips = strip_forces['Strip'].unique()
        self._strips = list(strips)
        return self._strips
    
    def extract_strip_loads(self,strips=None,cases_and_combos=None):
        """
        Extrae fuerzas de strips desde la tabla ``Strip Forces``.

        Puede filtrar por nombre de strip y por casos o combinaciones.
        """
        if cases_and_combos ==None:
            cases_and_combos = self.design_cases_and_combos
            
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)
        
        df = self.get_table('Strip Forces')
        
        if 'Strip' in df.columns:
            df = df.rename(columns={'Strip':'StripObject'})
            
        required_columns = {'V2', 'M3', 'Station'}
        if df.empty or not required_columns.issubset(df.columns):
            return pd.DataFrame()
            
        if strips is not None:
            strips = format_list_args(strips,self.strip_list)
            if 'StripObject' not in df.columns:
                return pd.DataFrame()
            df = df[df['StripObject'].isin(strips)]
            if df.empty:
                return pd.DataFrame()
            
        df[['V2','M3','Station']] =\
            df[['V2','M3','Station']].astype('float')
        
        return df.reset_index(drop=True)
    
    
    @property
    def strip_loads(self):
        return self.extract_strip_loads()
    
    
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
        return list(properties[properties['area_type']=='wall']['name'])
    
    @property
    def pier_list(self):
        return list(self.model.PierLabel.GetNameList()[1])
    
    def get_pier_forces(self,piers=None,stories=None,cases_and_combos=None):
        """
        Extrae fuerzas globales reportadas para piers.

        Permite filtrar por pier, nivel y casos o combinaciones de salida.
        """
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

        # Etiquetar max/min en casos sísmicos (2 filas por grupo)
        group_cols = ['Pier', 'Story', 'OutputCase', 'Location']
        suffixes = df.groupby(group_cols).cumcount()
        mask_dup = df.duplicated(subset=group_cols, keep=False)
        suffix_map = {0: ' max', 1: ' min'}
        df.loc[mask_dup, 'OutputCase'] = (
            df.loc[mask_dup, 'OutputCase'] + suffixes[mask_dup].map(suffix_map)
        )

        if piers is not None:
            piers = format_list_args(piers,self.pier_list)
            df = df[df['Pier'].isin(piers)]
        if stories is not None:
            stories = format_list_args(stories,self.stories)
            df = df[df['Story'].isin(stories)]
        
        return df.reset_index(drop=True)
        
    @property
    def pier_forces(self):
        return self.get_pier_forces()
    
    def get_pier_displacements(self,piers=None,cases_and_combos=None):
        """
        Estima desplazamientos de piers usando etiquetas, bays y desplazamientos nodales.

        La dirección principal del pier se deduce de sus propiedades de sección.
        """
        cases_and_combos = format_list_args(cases_and_combos,
                            self.design_cases_and_combos)
        # Trabajo con tablas
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)
        data = self.get_table('Area Assignments - Pier Labels')
        
        # Filtro con el máximo piso del Pier
        idx_story = list(data.groupby('PierName')['Story'].idxmax()) 
        data = data.loc[idx_story]
        data = data[['Story','PierName','Label']]
        # Puntos de los muros
        wall_points = self.get_table('Wall Bays')
        wall_points = wall_points[['Label','PointBay']]
        data = data.merge(wall_points)
        
        # Desplazamiento de los puntos
        p_disp = self.get_table('Joint Displacements')
        p_disp = p_disp[['Story','OutputCase','Label','Ux','Uy']]
        data = data.merge(p_disp, left_on=['Story','PointBay'], right_on=['Story','Label'])
        data = data.drop(columns = ['Label_x','PointBay','Label_y'])
        data = data.rename(columns={'PierName':'Pier'})
        
        # Dirección de los piers
        direc = self.get_table('Pier Section Properties')
        idx_ = list(direc.groupby('Pier')['Story'].idxmin())
        direc = direc.loc[idx_]
        direc = direc[['Pier','AxisAngle']]
        direc['Dir'] = np.where(direc['AxisAngle']=='0','X','Y')
        direc = direc.drop(columns='AxisAngle')
        data = data.merge(direc, on ='Pier')
        
        data[['Ux','Uy']] = data[['Ux','Uy']].astype(float)
        data['delta'] = np.where(data['Dir']=='X',data['Ux'],data['Uy'])
        
        data = data.groupby(['Story','Pier','Dir','OutputCase']).max().reset_index()
        if piers is not None:
            piers = format_list_args(piers,self.pier_list)
            data = data[data['Pier'].isin(piers)]
        
        return data.reset_index(drop=True)
        
    # ==================== STORIES ====================   
    @property
    def stories(self):
        return self.model.Story.GetStories()[1]
    
    def get_story_height(self,story):
        return self.model.Story.GetHeight(story)[0]
    
    def get_story_forces(self,cases_and_combos=None):
        """
        Extrae fuerzas globales por nivel desde la tabla ``Story Forces``.

        El resultado agrega la altura de cada nivel y limpia columnas auxiliares.
        """
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
        drop_columns = {'Casetype','StepNumber','StepLabel'}.intersection(df.columns)
        df = df.drop(drop_columns,axis=1)
        
        return df
    
    @property
    def story_forces(self):
        return self.get_story_forces()
    
    def get_story_displacements(self,cases_and_combos=None):
        """
        Extrae desplazamientos globales por nivel desde tablas de resultados.

        Puede limitarse al conjunto de casos y combinaciones indicado.
        """
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
        drop_columns = {'Casetype','StepNumber','StepLabel'}.intersection(df.columns)
        df = df.drop(drop_columns,axis=1)
        
        return df
    
    @property
    def story_displacements(self):
        return self.get_story_displacements()
    
    def get_story_drifts(self,cases_and_combos=None):
        """
        Extrae derivas máximas por diafragma y nivel.

        Incluye la altura de piso y elimina columnas auxiliares no esenciales.
        """
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
        drop_columns = {'Casetype','StepNumber','StepLabel',
                        'Max Loc X','Max Loc Y','Max Loc Z','Label'}.\
                            intersection(df.columns)
        df = df.drop(drop_columns,axis=1)
        return df
    
    @property
    def story_drifts(self):
        return self.get_story_drifts()
    
    # ================ Presiones del Suelo ======================
    
    def extract_soil_pressures(self,cases_and_combos=None):
        """
        Extrae presiones de suelo ordenadas por los casos o combinaciones dados.

        Normaliza columnas clave y consolida el tipo de paso cuando existe.
        """
        if cases_and_combos == None:
            cases_and_combos = self.cases_and_combos
            
        self.model.DatabaseTables.SetLoadCasesSelectedForDisplay(cases_and_combos)
        self.model.DatabaseTables.SetLoadCombinationsSelectedForDisplay(cases_and_combos)
        
        soil_pressures = self.get_table('Soil Pressures')
        required_columns = {'UniqueName', 'OutputCase', 'SoilPressure', 'GlobalX', 'GlobalY'}
        if soil_pressures.empty or 'OutputCase' not in soil_pressures.columns:
            return pd.DataFrame()

        soil_pressures['_index'] = soil_pressures.index
        soil_pressures = soil_pressures.sort_values(
                by=['OutputCase', '_index'],
                key=lambda col: col.map({nombre: i for i, nombre in enumerate(cases_and_combos)}) if col.name == 'OutputCase' else col
            ).reset_index(drop=True)
        soil_pressures = soil_pressures.drop(columns='_index')
        if 'StepType' in soil_pressures.columns:
            soil_pressures['OutputCase'] = soil_pressures['OutputCase'].astype(str)+' '+soil_pressures['StepType']
        if not required_columns.issubset(soil_pressures.columns):
            return pd.DataFrame()
        soil_pressures = soil_pressures[['UniqueName','OutputCase','SoilPressure','GlobalX','GlobalY']]
        soil_pressures[['SoilPressure','GlobalX','GlobalY']] =\
            soil_pressures[['SoilPressure','GlobalX','GlobalY']].astype(float)
        
        return soil_pressures
    
    @property
    def soil_pressures(self):
        return self.extract_soil_pressures()
    
    

    # ================= Analisis modal =========================
    def get_modal_data(self,cases=None):
        """
        Extrae períodos y razones de masa participante de casos modales.

        Los datos se cachean tras la primera lectura y pueden filtrarse por caso.
        """
        if self._modal_data is None:
            cases_and_combos = self.cases_and_combos
            self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
            for case in cases_and_combos:
                self.model.Results.Setup.SetCaseSelectedForOutput(case)
                self.model.Results.Setup.SetComboSelectedForOutput(case)
                
            res = self.model.Results.ModalParticipatingMassRatios()
            columns = ['LoadCase','StepType','StepNum','Period','UX','UY',
                    'UZ','SumUX','SumUY','SumUZ','RX','RY','RZ','SumRX',
                    'SumRY','SumRZ']
            df = pd.DataFrame(np.array(res[1:-1]).T
                            .reshape((res[0],len(columns))),
                            columns=columns)
            df = df[['LoadCase','Period','UX','UY','UZ','SumUX','SumUY',
                     'RZ','SumRZ']]
            self._modal_data = df
            
        if cases is None:
            return self._modal_data
        
        if isinstance(cases,str):
            cases = [cases]
        
        df = df[df['LoadCase'].isin(cases)]
        
        return df
    
    @property
    def modal_data(self):
        return self.get_modal_data()
    
    @property
    def modal_cases(self):
        if self._modal_cases is None:
            df = self.modal_data
            self._modal_cases = list(df['LoadCase'].unique())
        return self._modal_cases

    def get_modal_periods(self, case_name=None, num_modes=None, as_dict=False):
        """
        Obtiene los períodos modales de un caso modal.

        Puede limitar el número de modos y devolver lista o diccionario.
        """
        # Obtener datos modales completos
        modal_data = self.get_modal_data(cases=case_name)

        if modal_data.empty:
            raise ValueError("No hay datos modales disponibles en el modelo")

        # Si no se especifica caso, usar el primero disponible
        if case_name is None:
            case_name = modal_data['LoadCase'].iloc[0]
            print(f"Usando caso modal: {case_name}")

        # Filtrar por caso específico
        case_data = modal_data[modal_data['LoadCase'] == case_name].copy()

        if case_data.empty:
            available_cases = list(modal_data['LoadCase'].unique())
            raise ValueError(
                f"El caso '{case_name}' no tiene datos modales. "
                f"Casos disponibles: {available_cases}"
            )

        # Convertir períodos a float
        case_data['Period'] = case_data['Period'].astype(float)

        # Ordenar por período (mayor a menor = modo 1, 2, 3...)
        case_data = case_data.sort_values('Period', ascending=False).reset_index(drop=True)

        # Limitar número de modos si se especifica
        if num_modes is not None:
            case_data = case_data.head(num_modes)

        # Retornar según formato solicitado
        if as_dict:
            # Diccionario {modo: periodo}
            return {i+1: period for i, period in enumerate(case_data['Period'])}
        else:
            # Lista de períodos
            return list(case_data['Period'])

    def get_modal_summary(self, case_name=None, num_modes=None):
        """
        Resume períodos y participaciones modales de un caso.

        Retorna un DataFrame ordenado por período con numeración de modo.
        """
        # Obtener datos modales completos
        modal_data = self.get_modal_data(cases=case_name)

        if modal_data.empty:
            raise ValueError("No hay datos modales disponibles en el modelo")

        # Si no se especifica caso, usar el primero disponible
        if case_name is None:
            case_name = modal_data['LoadCase'].iloc[0]
            print(f"Usando caso modal: {case_name}")

        # Filtrar por caso específico
        case_data = modal_data[modal_data['LoadCase'] == case_name].copy()

        if case_data.empty:
            available_cases = list(modal_data['LoadCase'].unique())
            raise ValueError(
                f"El caso '{case_name}' no tiene datos modales. "
                f"Casos disponibles: {available_cases}"
            )

        # Convertir columnas numéricas
        numeric_cols = ['Period', 'UX', 'UY', 'UZ', 'SumUX', 'SumUY', 'RZ', 'SumRZ']
        for col in numeric_cols:
            case_data[col] = case_data[col].astype(float)

        # Ordenar por período (mayor a menor)
        case_data = case_data.sort_values('Period', ascending=False).reset_index(drop=True)

        # Añadir columna de número de modo
        case_data.insert(0, 'Mode', range(1, len(case_data) + 1))

        # Limitar número de modos si se especifica
        if num_modes is not None:
            case_data = case_data.head(num_modes)

        # Seleccionar columnas relevantes
        summary = case_data[['Mode', 'Period', 'UX', 'UY', 'UZ',
                            'SumUX', 'SumUY', 'RZ', 'SumRZ']]

        return summary

    def get_modal_displacements(self, case_name=None, point_names=None,
                               mode_number=None, item_type=0):
        """
        Obtiene desplazamientos modales para puntos y modos seleccionados.

        El resultado incluye traslaciones y rotaciones por punto y modo.
        """
        # Obtener casos modales disponibles
        modal_cases_list = self.modal_cases

        if not modal_cases_list:
            raise ValueError("No hay casos modales disponibles en el modelo")

        # Si no se especifica caso, usar el primero disponible
        if case_name is None:
            case_name = modal_cases_list[0]
            print(f"Usando caso modal: {case_name}")
        elif case_name not in modal_cases_list:
            raise ValueError(
                f"El caso '{case_name}' no es un caso modal. "
                f"Casos modales disponibles: {modal_cases_list}"
            )

        # Determinar puntos a extraer
        if point_names is None:
            point_names = self.point_list
        else:
            point_names = format_list_args(point_names, self.point_list)

        # Estructura de datos para almacenar resultados
        data = {
            'Point': [],
            'LoadCase': [],
            'StepType': [],
            'StepNum': [],
            'U1': [],
            'U2': [],
            'U3': [],
            'R1': [],
            'R2': [],
            'R3': []
        }

        # Configurar salida para el caso específico
        self.model.Results.Setup.DeselectAllCasesAndCombosForOutput()
        self.model.Results.Setup.SetCaseSelectedForOutput(case_name)

        # Extraer desplazamientos para cada punto
        for point in point_names:
            res = self.model.Results.JointDispl(point, item_type)

            # Verificar si hay resultados
            if res[-1] != 0:
                # Intentar correr análisis si no hay resultados
                self.model.Analyze.RunAnalysis()
                res = self.model.Results.JointDispl(point, item_type)

                if res[-1] != 0:
                    continue

            # Extraer datos
            num_results = res[0]
            if num_results == 0:
                continue

            # res[1] = Point names
            # res[3] = Load case names
            # res[4] = Step types
            # res[5] = Step numbers
            # res[6-11] = U1, U2, U3, R1, R2, R3

            data['Point'].extend(res[1])
            data['LoadCase'].extend(res[3])
            data['StepType'].extend(res[4])
            data['StepNum'].extend(res[5])
            data['U1'].extend(res[6])
            data['U2'].extend(res[7])
            data['U3'].extend(res[8])
            data['R1'].extend(res[9])
            data['R2'].extend(res[10])
            data['R3'].extend(res[11])

        # Crear DataFrame
        df = pd.DataFrame(data)

        if df.empty:
            raise ValueError(
                f"No se encontraron desplazamientos modales para el caso '{case_name}'"
            )

        # Filtrar por caso específico (por si acaso hay otros casos en los resultados)
        df = df[df['LoadCase'] == case_name].copy()

        # Convertir columnas numéricas
        numeric_cols = ['StepNum', 'U1', 'U2', 'U3', 'R1', 'R2', 'R3']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Filtrar por modos específicos si se solicita
        if mode_number is not None:
            if isinstance(mode_number, int):
                mode_number = [mode_number]
            df = df[df['StepNum'].isin(mode_number)]

            if df.empty:
                raise ValueError(
                    f"No se encontraron datos para el/los modo(s) {mode_number}"
                )

        # Ordenar por punto y modo
        df = df.sort_values(['Point', 'StepNum']).reset_index(drop=True)

        return df

    def get_modal_shape(self, case_name=None, mode_number=1,
                       direction='3D', normalize=True):
        """
        Obtiene la forma modal de un modo para visualización.

        Puede calcular magnitud 3D, horizontal o una componente específica.
        """
        # Obtener desplazamientos del modo específico
        modal_displ = self.get_modal_displacements(case_name=case_name,
                                                   mode_number=mode_number)

        # Obtener coordenadas de los puntos
        coords = self.points_coordinates

        # Merge con coordenadas
        shape = modal_displ.merge(coords, on='Point', how='left')

        # Calcular desplazamiento según dirección solicitada
        if direction == '3D':
            shape['Displacement'] = np.sqrt(
                shape['U1']**2 + shape['U2']**2 + shape['U3']**2
            )
        elif direction == 'horizontal':
            shape['Displacement'] = np.sqrt(
                shape['U1']**2 + shape['U2']**2
            )
        elif direction in ['U1', 'U2', 'U3']:
            shape['Displacement'] = shape[direction]
        else:
            raise ValueError(
                f"Dirección '{direction}' no válida. "
                f"Opciones: '3D', 'horizontal', 'U1', 'U2', 'U3'"
            )

        # Normalizar si se solicita
        if normalize:
            max_disp = shape['Displacement'].abs().max()
            if max_disp > 0:
                shape['Displacement'] = shape['Displacement'] / max_disp

        # Seleccionar columnas relevantes
        result = shape[['Point', 'X', 'Y', 'Z', 'Displacement',
                       'U1', 'U2', 'U3', 'R1', 'R2', 'R3']]

        return result

    # ==================== GEOMETRY EXTRACTION ====================

    def get_model_geometry(self, include_frames=True, include_areas=True,
                          include_points=True, include_sections=True,
                          include_connectivity=False):
        """
        Extrae la geometría principal del modelo.

        Puede incluir puntos, frames, áreas, secciones, límites globales
        y conectividad de frames.
        """
        geometry = {}

        # 1. Extraer puntos
        if include_points:
            print("Extrayendo puntos...")
            geometry['points'] = self.points_coordinates.copy()

            # Calcular límites del modelo
            coords = geometry['points']
            geometry['bounds'] = {
                'xmin': coords['X'].min(),
                'xmax': coords['X'].max(),
                'ymin': coords['Y'].min(),
                'ymax': coords['Y'].max(),
                'zmin': coords['Z'].min(),
                'zmax': coords['Z'].max()
            }
            print(f"  Total puntos: {len(geometry['points'])}")
        else:
            geometry['points'] = None
            geometry['bounds'] = None

        # 2. Extraer frames
        if include_frames:
            print("Extrayendo frames...")
            geometry['frames'] = self.frames_properties.copy()
            print(f"  Total frames: {len(geometry['frames'])}")

            # Añadir información de conectividad
            if include_points and geometry['points'] is not None:
                # Coordenadas de puntos inicial y final
                frames_df = geometry['frames']
                points_df = geometry['points']

                # Merge para punto inicial
                frames_df = frames_df.merge(
                    points_df.rename(columns={'X': 'Xi', 'Y': 'Yi', 'Z': 'Zi'}),
                    left_on='point_i', right_on='Point', how='left'
                ).drop('Point', axis=1)

                # Merge para punto final
                frames_df = frames_df.merge(
                    points_df.rename(columns={'X': 'Xj', 'Y': 'Yj', 'Z': 'Zj'}),
                    left_on='point_j', right_on='Point', how='left'
                ).drop('Point', axis=1)

                geometry['frames'] = frames_df

            if include_connectivity:
                connectivity = self.get_frames_connectivity()
                geometry['frames'] = geometry['frames'].merge(
                    connectivity[[
                        'Frame', 'FrameType', 'Grid', 'GridX', 'GridY', 'General'
                    ]],
                    on='Frame',
                    how='left',
                )
        else:
            geometry['frames'] = None

        # 3. Extraer áreas
        if include_areas:
            print("Extrayendo áreas...")
            geometry['areas'] = self.area_geometry.copy()
            print(f"  Total áreas: {len(geometry['areas'])}")
        else:
            geometry['areas'] = None

        # 4. Extraer secciones
        if include_sections:
            print("Extrayendo secciones...")

            if include_frames:
                geometry['frame_sections'] = self.frame_sections_data.copy()
                print(f"  Total secciones de frame: {len(geometry['frame_sections'])}")
            else:
                geometry['frame_sections'] = None

            if include_areas:
                # Asegurar que las propiedades de área estén mapeadas
                if self._wall_sections_data is None:
                    self.map_area_properties()

                geometry['area_sections'] = {
                    'walls': self._wall_sections_data.copy() if self._wall_sections_data is not None else pd.DataFrame(),
                    'slabs': self._slab_sections_data.copy() if self._slab_sections_data is not None else pd.DataFrame(),
                    'decks': self._deck_sections_data.copy() if self._deck_sections_data is not None else pd.DataFrame()
                }
                total_area_sections = (
                    len(geometry['area_sections']['walls']) +
                    len(geometry['area_sections']['slabs']) +
                    len(geometry['area_sections']['decks'])
                )
                print(f"  Total secciones de área: {total_area_sections}")
            else:
                geometry['area_sections'] = None
        else:
            geometry['frame_sections'] = None
            geometry['area_sections'] = None

        # Resumen
        print("\nResumen de geometría extraída:")
        print(f"  Puntos: {len(geometry['points']) if geometry['points'] is not None else 'No incluidos'}")
        print(f"  Frames: {len(geometry['frames']) if geometry['frames'] is not None else 'No incluidos'}")
        print(f"  Áreas: {len(geometry['areas']) if geometry['areas'] is not None else 'No incluidos'}")

        return geometry

    def get_geometry_summary(self):
        """
        Resume la geometría del modelo en métricas básicas.

        Incluye conteos, dimensiones globales, secciones y materiales.
        """
        summary = {}

        # Estadísticas de puntos
        points = self.points_coordinates
        summary['num_points'] = len(points)
        summary['height'] = points['Z'].max() - points['Z'].min()
        summary['x_dimension'] = points['X'].max() - points['X'].min()
        summary['y_dimension'] = points['Y'].max() - points['Y'].min()

        # Estadísticas de frames
        frames = self.frames_properties
        summary['num_frames'] = len(frames)
        summary['total_frame_length'] = frames['length'].sum()

        # Contar por tipo de frame (basado en Label)
        if 'Label' in frames.columns:
            label_counts = frames['Label'].value_counts().to_dict()
            summary['frames_by_label'] = label_counts

        # Estadísticas de áreas
        areas = self.area_geometry
        summary['num_areas'] = len(areas)

        # Contar por tipo de área
        area_type_counts = areas['area_type'].value_counts().to_dict()
        summary['areas_by_type'] = area_type_counts

        # Estadísticas de secciones
        frame_sections = self.frame_sections_data
        summary['num_frame_sections'] = len(frame_sections)

        # Contar por tipo de sección
        if 'SectionType' in frame_sections.columns:
            section_counts = frame_sections['SectionType'].value_counts().to_dict()
            summary['frame_sections_by_type'] = section_counts

        # Pisos/Niveles
        if 'Story' in frames.columns:
            stories = frames['Story'].unique()
            summary['num_stories'] = len(stories)
            summary['stories'] = list(stories)

        # Materiales
        materials = self.material_list
        summary['num_materials'] = len(materials)
        summary['materials'] = materials

        return summary

    def export_geometry_to_dict(self, simplified=False):
        """
        Exporta la geometría del modelo a un diccionario serializable.

        Puede generar una versión resumida o una exportación más completa.
        """
        if simplified:
            # Versión simplificada: solo puntos y conectividad básica
            points = self.points_coordinates
            frames = self.frames_properties[['Frame', 'point_i', 'point_j', 'Section', 'Label']]
            areas = self.area_geometry[['name', 'area_type', 'section']]

            geometry = {
                'points': points.to_dict(orient='records'),
                'frames': frames.to_dict(orient='records'),
                'areas': areas.to_dict(orient='records'),
                'summary': self.get_geometry_summary()
            }
        else:
            # Versión completa
            full_geometry = self.get_model_geometry()

            geometry = {
                'points': full_geometry['points'].to_dict(orient='records') if full_geometry['points'] is not None else [],
                'frames': full_geometry['frames'].to_dict(orient='records') if full_geometry['frames'] is not None else [],
                'areas': [],
                'frame_sections': full_geometry['frame_sections'].to_dict(orient='records') if full_geometry['frame_sections'] is not None else [],
                'bounds': full_geometry['bounds'],
                'summary': self.get_geometry_summary()
            }

            # Convertir áreas (manejo especial de listas en columnas)
            if full_geometry['areas'] is not None:
                areas_df = full_geometry['areas'].copy()
                # Convertir listas a strings para serialización
                for col in ['points_x', 'points_y', 'points_z']:
                    if col in areas_df.columns:
                        areas_df[col] = areas_df[col].apply(lambda x: list(x) if isinstance(x, (list, tuple)) else x)
                geometry['areas'] = areas_df.to_dict(orient='records')

            # Secciones de área
            if full_geometry['area_sections'] is not None:
                geometry['area_sections'] = {
                    'walls': full_geometry['area_sections']['walls'].to_dict(orient='records'),
                    'slabs': full_geometry['area_sections']['slabs'].to_dict(orient='records'),
                    'decks': full_geometry['area_sections']['decks'].to_dict(orient='records')
                }

        return geometry

    # ==================== LOAD CASES EXTRACTION ====================

    def get_load_cases_info(self, include_cases=True, include_combos=True,
                           include_patterns=True, include_details=True):
        """
        Extrae información de patrones, casos y combinaciones de carga.

        Opcionalmente agrega detalles internos y un resumen estadístico.
        """
        load_info = {}

        # 1. Patrones de carga
        if include_patterns:
            print("Extrayendo patrones de carga...")
            patterns_data = {
                'Pattern': [],
                'Type': [],
                'TypeName': [],
                'SelfWtMultiplier': []
            }

            # Obtener lista de patrones
            num_patterns = self.model.LoadPatterns.GetNameList()[0]
            pattern_names = self.model.LoadPatterns.GetNameList()[1]

            # Mapeo de tipos de patrones
            pattern_type_map = {
                1: 'Dead',
                2: 'Super Dead',
                3: 'Live',
                4: 'Reducible Live',
                5: 'Quake',
                6: 'Wind',
                7: 'Snow',
                8: 'Other',
                9: 'Move',
                10: 'Temperature',
                11: 'Roof Live',
                12: 'Notional',
                13: 'Pattern Live',
                14: 'Wave',
                15: 'Bridge',
                16: 'Vehicle'
            }

            for pattern in pattern_names:
                pattern_type = self.model.LoadPatterns.GetLoadType(pattern)[0]
                self_wt = self.model.LoadPatterns.GetSelfWTMultiplier(pattern)[0]

                patterns_data['Pattern'].append(pattern)
                patterns_data['Type'].append(pattern_type)
                patterns_data['TypeName'].append(pattern_type_map.get(pattern_type, 'Unknown'))
                patterns_data['SelfWtMultiplier'].append(self_wt)

            load_info['load_patterns'] = pd.DataFrame(patterns_data)
            print(f"  Total patrones: {len(load_info['load_patterns'])}")
        else:
            load_info['load_patterns'] = None

        # 2. Casos de carga
        if include_cases:
            print("Extrayendo casos de carga...")
            cases_data = {
                'Case': [],
                'Type': [],
                'TypeName': []
            }

            # Mapeo de tipos de casos
            case_type_map = {
                1: 'Linear Static',
                2: 'Nonlinear Static',
                3: 'Modal',
                4: 'Response Spectrum',
                5: 'Linear History',
                6: 'Nonlinear History',
                7: 'Moving Load',
                8: 'Buckling',
                9: 'Steady State',
                10: 'Power Spectral Density',
                11: 'Linear Static Multistep',
                12: 'Hyperstatic',
                13: 'Direct Integration Time History',
                14: 'Staged Construction'
            }

            for case in self.cases:
                case_type = self.model.LoadCases.GetTypeOAPI_1(case)[2]

                cases_data['Case'].append(case)
                cases_data['Type'].append(case_type)
                cases_data['TypeName'].append(case_type_map.get(case_type, 'Unknown'))

            load_info['load_cases'] = pd.DataFrame(cases_data)

            # Agregar información de casos modales
            if include_details:
                modal_cases = self.modal_cases if hasattr(self, 'modal_cases') else []
                load_info['load_cases']['IsModal'] = load_info['load_cases']['Case'].isin(modal_cases)

                seismic_cases = self.seismic_cases if hasattr(self, 'seismic_cases') else []
                load_info['load_cases']['IsSeismic'] = load_info['load_cases']['Case'].isin(seismic_cases)

            print(f"  Total casos: {len(load_info['load_cases'])}")
        else:
            load_info['load_cases'] = None

        # 3. Combinaciones de carga
        if include_combos:
            print("Extrayendo combinaciones de carga...")
            combos_data = {
                'Combo': [],
                'Type': [],
                'TypeName': [],
                'NumCases': []
            }

            # Mapeo de tipos de combinaciones
            combo_type_map = {
                0: 'Linear Add',
                1: 'Envelope',
                2: 'Absolute Add',
                3: 'SRSS',
                4: 'Range Add'
            }

            combo_details_list = []

            for combo in self.combos:
                combo_type = self.model.RespCombo.GetTypeOAPI(combo)[0]

                # Obtener casos de la combinación
                combo_info = self.model.RespCombo.GetCaseList(combo)
                num_cases = combo_info[0]
                case_types = combo_info[1]
                case_names = combo_info[2]
                scale_factors = combo_info[3]

                combos_data['Combo'].append(combo)
                combos_data['Type'].append(combo_type)
                combos_data['TypeName'].append(combo_type_map.get(combo_type, 'Unknown'))
                combos_data['NumCases'].append(num_cases)

                # Detalles de cada caso en la combinación
                if include_details:
                    for i in range(num_cases):
                        combo_details_list.append({
                            'Combo': combo,
                            'CaseType': 'LoadCase' if case_types[i] == 0 else 'LoadCombo',
                            'CaseName': case_names[i],
                            'ScaleFactor': scale_factors[i]
                        })

            load_info['load_combos'] = pd.DataFrame(combos_data)
            print(f"  Total combinaciones: {len(load_info['load_combos'])}")

            if include_details and combo_details_list:
                load_info['combo_details'] = pd.DataFrame(combo_details_list)
            else:
                load_info['combo_details'] = None
        else:
            load_info['load_combos'] = None
            load_info['combo_details'] = None

        # 4. Resumen
        summary = {}
        if load_info['load_patterns'] is not None:
            summary['num_patterns'] = len(load_info['load_patterns'])
            summary['patterns_by_type'] = load_info['load_patterns']['TypeName'].value_counts().to_dict()

        if load_info['load_cases'] is not None:
            summary['num_cases'] = len(load_info['load_cases'])
            summary['cases_by_type'] = load_info['load_cases']['TypeName'].value_counts().to_dict()

        if load_info['load_combos'] is not None:
            summary['num_combos'] = len(load_info['load_combos'])
            summary['combos_by_type'] = load_info['load_combos']['TypeName'].value_counts().to_dict()

        load_info['summary'] = summary

        # Resumen en consola
        print("\nResumen de casos de carga:")
        if 'num_patterns' in summary:
            print(f"  Patrones: {summary['num_patterns']}")
        if 'num_cases' in summary:
            print(f"  Casos: {summary['num_cases']}")
        if 'num_combos' in summary:
            print(f"  Combinaciones: {summary['num_combos']}")

        return load_info

    def get_load_cases_summary(self):
        """
        Resume los casos y combinaciones de carga del modelo.

        Incluye conteos de patrones, casos, combinaciones y subconjuntos de diseño.
        """
        summary = {}

        # Patrones
        try:
            num_patterns = self.model.LoadPatterns.GetNameList()[0]
            summary['num_patterns'] = num_patterns
        except:
            summary['num_patterns'] = 0

        # Casos
        summary['num_cases'] = len(self.cases)
        summary['num_design_cases'] = len(self.design_cases)
        summary['num_seismic_cases'] = len(self.seismic_cases)
        summary['num_modal_cases'] = len(self.modal_cases) if hasattr(self, 'modal_cases') else 0

        # Combinaciones
        summary['num_combos'] = len(self.combos)
        summary['num_design_combos'] = len(self.design_cases_and_combos) - len(self.design_cases)
        summary['num_seismic_combos'] = len(self.seismic_combos)

        # Total casos y combos
        summary['total_cases_and_combos'] = len(self.cases_and_combos)
        summary['total_design_cases_and_combos'] = len(self.design_cases_and_combos)
        summary['total_seismic_cases_and_combos'] = len(self.seismic_cases_and_combos)

        return summary

    def export_load_cases_to_dict(self, simplified=False):
        """
        Exporta la información de cargas a un diccionario serializable.

        Puede generar una versión simplificada o una exportación detallada.
        """
        if simplified:
            # Versión simplificada
            load_dict = {
                'cases': self.cases,
                'combos': self.combos,
                'design_cases': self.design_cases,
                'seismic_cases': self.seismic_cases,
                'modal_cases': self.modal_cases if hasattr(self, 'modal_cases') else [],
                'summary': self.get_load_cases_summary()
            }
        else:
            # Versión completa
            full_info = self.get_load_cases_info()

            load_dict = {
                'load_patterns': full_info['load_patterns'].to_dict(orient='records') if full_info['load_patterns'] is not None else [],
                'load_cases': full_info['load_cases'].to_dict(orient='records') if full_info['load_cases'] is not None else [],
                'load_combos': full_info['load_combos'].to_dict(orient='records') if full_info['load_combos'] is not None else [],
                'combo_details': full_info['combo_details'].to_dict(orient='records') if full_info['combo_details'] is not None else [],
                'summary': full_info['summary']
            }

        return load_dict

    def get_combo_breakdown(self, combo_name):
        """
        Desglosa recursivamente una combinación de carga.

        El resultado acumula factores y consolida los casos base repetidos.
        """
        def get_combo_cases_recursive(combo, factor=1.0, level=0):
            """Función recursiva para obtener todos los casos base"""
            combo_info = self.model.RespCombo.GetCaseList(combo)
            num_items = combo_info[0]
            item_types = combo_info[1]  # 0 = LoadCase, 1 = LoadCombo
            item_names = combo_info[2]
            scale_factors = combo_info[3]

            results = []

            for i in range(num_items):
                current_factor = factor * scale_factors[i]
                item_type = 'Case' if item_types[i] == 0 else 'Combo'

                if item_types[i] == 0:  # Es un caso de carga
                    results.append({
                        'Case': item_names[i],
                        'Factor': current_factor,
                        'Level': level,
                        'Path': combo if level == 0 else f"{combo} > {item_names[i]}"
                    })
                else:  # Es otra combinación (recursivo)
                    sub_results = get_combo_cases_recursive(
                        item_names[i],
                        current_factor,
                        level + 1
                    )
                    results.extend(sub_results)

            return results

        # Verificar que la combinación existe
        if combo_name not in self.combos:
            raise ValueError(f"La combinación '{combo_name}' no existe")

        # Obtener el desglose
        breakdown_list = get_combo_cases_recursive(combo_name)

        if not breakdown_list:
            return pd.DataFrame(columns=['Case', 'Factor', 'Level', 'Path'])

        df = pd.DataFrame(breakdown_list)

        # Agrupar casos repetidos y sumar factores
        df_grouped = df.groupby('Case').agg({
            'Factor': 'sum',
            'Level': 'min',
            'Path': lambda x: ', '.join(set(x))
        }).reset_index()

        df_grouped = df_grouped.sort_values('Factor', ascending=False)

        return df_grouped

