class ModelBuilder:
    '''Mixin de modelamiento con API de ETABS'''   
    # ==================== MATERIALS ====================
    
    def add_material(self, material_name, material_type, E, U, A, weight_per_volume):
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
        self.model.PropMaterial.SetWeightAndMass(material_name, 1, weight_per_volume)
        print(f"Material '{material_name}' añadido")
        
    def set_point_restraint(self, point_name, UX=False, UY=False, UZ=False, 
                           RX=False, RY=False, RZ=False):
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
        
    def add_concrete_tee_section(self, section_name, material_name, t3, t2, tf, tw):
        """
        Crea una sección T de concreto
        
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
            Ancho del ala
        tf : float
            Espesor del ala
        tw : float
            Espesor del alma
        """
        self.model.PropFrame.SetConcreteTee(section_name, material_name, t3, t2, tf, tw)
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
        
                
    def add_frame(self, frame_name, point_i, point_j, section_name):
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
                                rib_spacing, rib_direction):
        """
        Crea una sección de losa nervada (ribbed slab)
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
            Altura total de la losa (incluyendo nervios)
        slab_thickness : float
            Espesor de la losa superior
        stem_width : float
            Ancho de los nervios
        rib_spacing : float
            Espaciamiento entre nervios (centro a centro)
        rib_direction : int
            Dirección de los nervios:
            - 1 = Local 1 direction
            - 2 = Local 2 direction
        """
        # Primera llamada: Inicializar como slab básico
        self.model.PropArea.SetSlab(section_name, 0, 1, material_name, overall_depth)
        
        # Segunda llamada: Configurar como ribbed
        self.model.PropArea.SetSlabRibbed(
            section_name, 
            overall_depth, 
            slab_thickness,
            stem_width, 
            rib_spacing, 
            rib_direction
        )
        
        direction_str = "Local 1" if rib_direction == 1 else "Local 2"
        print(f"Sección de losa nervada '{section_name}' añadida:")
        print(f"  - Altura total: {overall_depth}")
        print(f"  - Espesor losa: {slab_thickness}")
        print(f"  - Ancho nervio: {stem_width}")
        print(f"  - Espaciamiento: {rib_spacing}")
        print(f"  - Dirección: {direction_str}")


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
        # Primera llamada: Inicializar como slab básico
        self.model.PropArea.SetSlab(section_name, 0, 1, material_name, overall_depth)
        
        # Segunda llamada: Configurar como waffle
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
    def add_wall_section(model, section_name, material_name, thickness, 
                        wall_prop_type=1, shell_type=1):
        """
        Crea una sección de muro
        
        Parameters:
        -----------
        model : CSI Model object
            Objeto del modelo CSI
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
        model.PropArea.SetWall(section_name, wall_prop_type, shell_type, 
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
        
    # def build_from_extraction(self, extraction_data, element_type='frames'):
    #     """
    #     Construye elementos en el modelo desde datos extraídos
        
    #     Parameters:
    #     -----------
    #     extraction_data : dict
    #         Datos extraídos por DataExtractor
    #     element_type : str
    #         Tipo de elemento ('frames', 'points', 'materials', 'slabs', 'walls')
    #     """
    #     if element_type == 'materials' and 'materials' in extraction_data:
    #         df = extraction_data['materials']
    #         for _, row in df.iterrows():
    #             try:
    #                 self.add_material(
    #                     row['Material'], row['Type'], row['E'], 
    #                     row['U'], row['A'], row['WeightPerVolume']
    #                 )
    #             except Exception as e:
    #                 print(f"Error añadiendo material {row['Material']}: {e}")
        
    #     elif element_type == 'points' and 'geometry' in extraction_data:
    #         df = extraction_data['geometry']
    #         for _, row in df.iterrows():
    #             try:
    #                 self.add_point(row['Point'], row['X'], row['Y'], row['Z'])
    #                 if any([row['UX'], row['UY'], row['UZ'], row['RX'], row['RY'], row['RZ']]):
    #                     self.set_point_restraint(
    #                         row['Point'], row['UX'], row['UY'], row['UZ'],
    #                         row['RX'], row['RY'], row['RZ']
    #                     )
    #             except Exception as e:
    #                 print(f"Error añadiendo punto {row['Point']}: {e}")
        
    #     elif element_type == 'frames':
    #         Primero crear secciones
    #         if 'sections' in extraction_data:
    #             df_sections = extraction_data['sections']
    #             for _, row in df_sections.iterrows():
    #                 try:
    #                     Simplificado - solo secciones rectangulares por ahora
    #                     if row['SectionType'] == 'Rectangular':
    #                         Necesitaríamos el material de alguna forma
    #                         pass
    #                 except Exception as e:
    #                     print(f"Error añadiendo sección {row['SectionName']}: {e}")
            
    #         Luego crear frames
    #         if 'geometry' in extraction_data:
    #             df_geo = extraction_data['geometry']
    #             for _, row in df_geo.iterrows():
    #                 try:
    #                     self.add_frame(
    #                         row['Frame'], row['PointI'], row['PointJ'], row['Section']
    #                     )
    #                 except Exception as e:
    #                     print(f"Error añadiendo frame {row['Frame']}: {e}")
        
    #     else:
    #         raise ValueError(f"Tipo de elemento '{element_type}' no soportado o datos faltantes")