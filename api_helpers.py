import importlib

from .constants import eAreaDesignOrientation, eCNameType, eFramePropType, eItemType, eItemTypeElm, eLoadCaseType, eLoadPatternType, eMatType

class _CSIProxy:
    """Proxy genérico para centralizar acceso al modelo CSI."""

    def __init__(self, helpers, target, path=""):
        self._helpers = helpers
        self._target = target
        self._path = path

    def __getattr__(self, name):
        attr = getattr(self._target, name)
        path = f"{self._path}.{name}" if self._path else name

        if callable(attr):
            return self._helpers.wrap_callable(path, attr)
        return _CSIProxy(self._helpers, attr, path)


class CSIAPIHelpers:
    """Encapsula helpers y proxys de compatibilidad entre backends CSI."""

    def __init__(self, owner):
        self.owner = owner

    @property
    def raw_model(self):
        return getattr(self.owner, "_raw_model", None)

    @property
    def backend(self):
        return self.owner.backend

    @property
    def api_module(self):
        return self.owner.api_module

    def get_model_proxy(self):
        """Retorna el proxy del modelo activo."""
        if self.raw_model is None:
            return None
        return _CSIProxy(self, self.raw_model)

    def get_system_types(self):
        """Obtiene tipos base de ``System`` cuando el runtime .NET ya está cargado."""
        system = importlib.import_module("System")
        return system.Array, system.Double, system.Int32, system.String

    def get_api_enum_placeholder(self, enum_name):
        """Retorna el primer valor disponible de un enum expuesto por la API .NET."""
        system = importlib.import_module("System")
        api_enum = getattr(self.api_module, enum_name)
        return system.Enum.GetValues(api_enum)[0]

    def coerce_api_enum(self, enum_name, value):
        """Convierte un entero Python al enum real de la API .NET."""
        if self.backend != "dotnet" or self.api_module is None:
            return value
        system = importlib.import_module("System")
        api_enum = getattr(self.api_module, enum_name)
        return system.Enum.ToObject(api_enum, int(value))

    def _as_int(self, value, default=0):
        if value in ("", None):
            return default
        if hasattr(value, "__int__"):
            return int(value)
        return int(value)

    def _as_float(self, value, default=0.0):
        if value in ("", None):
            return default
        return float(value)

    def _item(self, values, index, default=None):
        if index >= len(values):
            return default
        return values[index]

    def normalize_api_result(self, result):
        """Normaliza salidas CSI para mantener índices estables entre backends."""
        if self.backend == "dotnet":
            return tuple(result[1:]) + (result[0],)
        return result

    def wrap_callable(self, path, func):
        """Envuelve métodos especiales y deja el resto como pass-through."""
        special = {
            "LoadCases.GetNameList": self._wrap_get_name_list,
            "RespCombo.GetNameList": self._wrap_get_name_list,
            "PropMaterial.GetNameList": self._wrap_get_name_list,
            "PointObj.GetNameList": self._wrap_get_name_list,
            "PointObj.GetNameListOnStory": self._wrap_get_name_list_on_story,
            "PropFrame.GetNameList": self._wrap_get_name_list,
            "FrameObj.GetNameList": self._wrap_get_name_list,
            "PropArea.GetNameList": self._wrap_get_name_list,
            "PierLabel.GetNameList": self._wrap_get_name_list,
            "LoadPatterns.GetNameList": self._wrap_get_name_list,
            "LoadPatterns.GetLoadType": self._wrap_load_pattern_get_load_type,
            "LoadPatterns.GetSelfWTMultiplier": self._wrap_load_pattern_get_self_wt_multiplier,
            "LoadCases.GetTypeOAPI_1": self._wrap_get_type_oapi_1,
            "PropMaterial.GetTypeOAPI": self._wrap_get_prop_material_type_oapi,
            "PropMaterial.SetMaterial": self._wrap_set_material,
            "PropMaterial.SetMPIsotropic": self._wrap_set_mp_isotropic,
            "PropMaterial.SetWeightAndMass": self._wrap_set_weight_and_mass,
            "PropMaterial.SetMPUniaxial": self._wrap_set_mp_uniaxial,
            "RespCombo.GetTypeOAPI": self._wrap_get_resp_combo_type_oapi,
            "RespCombo.GetTypeCombo": self._wrap_resp_combo_get_type_combo,
            "RespCombo.Add": self._wrap_resp_combo_add,
            "RespCombo.GetCaseList": self._wrap_get_case_list,
            "RespCombo.SetCaseList": self._wrap_resp_combo_set_case_list,
            "LoadPatterns.Add": self._wrap_load_patterns_add,
            "Results.JointReact": self._wrap_joint_react,
            "Results.FrameForce": self._wrap_frame_force,
            "Results.AreaForceShell": self._wrap_area_force_shell,
            "Results.PierForce": self._wrap_pier_force,
            "Results.ModalParticipatingMassRatios": self._wrap_modal_participating_mass_ratios,
            "Results.JointDispl": self._wrap_joint_displ,
            "DatabaseTables.GetTableForEditingArray": self._wrap_get_table_for_editing_array,
            "DatabaseTables.ApplyEditedTables": self._wrap_apply_edited_tables,
            "DatabaseTables.GetAvailableTables": self._wrap_get_available_tables,
            "DatabaseTables.GetTableForDisplayArray": self._wrap_get_table_for_display_array,
            "DatabaseTables.SetTableForEditingArray": self._wrap_set_table_for_editing_array,
            "PropFrame.GetAllFrameProperties_2": self._wrap_get_all_frame_properties_2,
            "PropFrame.GetSectProps": self._wrap_get_sect_props,
            "PropFrame.GetRectangle": self._wrap_get_rectangle,
            "PropFrame.SetRectangle": self._wrap_set_rectangle,
            "PropFrame.SetCircle": self._wrap_set_circle,
            "PropFrame.SetPipe": self._wrap_set_pipe,
            "PropFrame.SetTube": self._wrap_set_tube,
            "PropFrame.SetISection": self._wrap_set_i_section,
            "PropFrame.SetTee": self._wrap_set_tee,
            "PropFrame.SetAngle": self._wrap_set_angle,
            "PropFrame.SetChannel": self._wrap_set_channel,
            "PropFrame.SetSDSection": self._wrap_set_sd_section,
            "PropFrame.SetDblAngle": self._wrap_set_dbl_angle,
            "PropFrame.SetDblChannel": self._wrap_set_dbl_channel,
            "PropFrame.SetConcreteBox": self._wrap_set_concrete_box,
            "PropFrame.SetConcreteTee": self._wrap_set_concrete_tee,
            "PropFrame.SetConcreteL": self._wrap_set_concrete_l,
            "PropFrame.SetConcreteCross": self._wrap_set_concrete_cross,
            "PropFrame.SetConcretePipe": self._wrap_set_concrete_pipe,
            "PropFrame.SetPlate": self._wrap_set_plate,
            "PropFrame.SetRod": self._wrap_set_rod,
            "PropFrame.SetColdC": self._wrap_set_cold_c,
            "PropFrame.SetColdZ": self._wrap_set_cold_z,
            "PropFrame.SetColdHat": self._wrap_set_cold_hat,
            "PointObj.AddCartesian": self._wrap_add_cartesian,
            "PointObj.SetRestraint": self._wrap_set_restraint,
            "FrameObj.GetSection": self._wrap_get_section,
            "FrameObj.GetPoints": self._wrap_get_points,
            "FrameObj.GetLabelNameList": self._wrap_get_label_name_list,
            "FrameObj.GetNameFromLabel": self._wrap_get_name_from_label,
            "AreaObj.GetProperty": self._wrap_area_get_property,
            "AreaObj.GetPoints": self._wrap_area_get_points,
            "PointObj.GetCoordCartesian": self._wrap_get_coord_cartesian,
            "PointObj.GetRestraint": self._wrap_get_restraint,
            "PointObj.GetSelected": self._wrap_get_selected,
            "SelectObj.GetSelected": self._wrap_select_obj_get_selected,
            "AreaObj.GetAllAreas": self._wrap_get_all_areas,
            "PropArea.GetWall": self._wrap_get_wall,
            "PropArea.GetSlab": self._wrap_get_slab,
            "PropArea.GetSlabRibbed": self._wrap_get_slab_ribbed,
            "PropArea.GetSlabWaffle": self._wrap_get_slab_waffle,
            "PropArea.GetDeck_1": self._wrap_get_deck_1,
            "PropArea.SetWall": self._wrap_set_wall,
            "PropArea.SetSlab": self._wrap_set_slab,
            "PropArea.SetSlabRibbed": self._wrap_set_slab_ribbed,
            "PropArea.SetSlabWaffle": self._wrap_set_slab_waffle,
            "PropArea.SetDeck_1": self._wrap_set_deck_1,
            "PropArea.SetDeckFilled": self._wrap_set_deck_filled,
            "PropArea.SetDeckUnfilled": self._wrap_set_deck_unfilled,
            "PropArea.SetDeckSolidSlab": self._wrap_set_deck_solid_slab,
            "PropArea.SetShellLayer": self._wrap_set_shell_layer,
            "AreaObj.SetProperty": self._wrap_area_set_property,
            "AreaObj.SetLoadUniform": self._wrap_area_set_load_uniform,
            "AreaObj.SetLoadUniformToFrame": self._wrap_area_set_load_uniform_to_frame,
            "AreaObj.AddByCoord": self._wrap_area_add_by_coord,
            "FrameObj.AddByPoint": self._wrap_add_by_point,
            "FrameObj.SetSection": self._wrap_frame_set_section,
            "PointObj.SetLoadForce": self._wrap_point_set_load_force,
            "FrameObj.SetLoadDistributed": self._wrap_frame_set_load_distributed,
            "FrameObj.SetLoadPoint": self._wrap_frame_set_load_point,
            "LoadCases.StaticLinear.SetCase": self._wrap_static_linear_set_case,
            "LoadCases.StaticLinear.SetInitialCase": self._wrap_static_linear_set_initial_case,
            "LoadCases.StaticLinear.SetLoads": self._wrap_static_linear_set_loads,
            "LoadCases.ResponseSpectrum.SetCase": self._wrap_response_spectrum_set_case,
            "LoadCases.ResponseSpectrum.SetLoads": self._wrap_response_spectrum_set_loads,
            "View.RefreshView": self._wrap_refresh_view,
            "File.OpenFile": self._wrap_open_file,
            "File.NewBlank": self._wrap_new_blank,
            "Analyze.RunAnalysis": self._wrap_run_analysis,
            "Story.GetStories": self._wrap_get_stories,
            "Story.GetHeight": self._wrap_get_story_height,
            "GridSys.GetNameList": self._wrap_get_name_list,
            "GridSys.GetGridSys_2": self._wrap_get_grid_sys_2,
            "PropMaterial.GetMPIsotropic": self._wrap_get_mpi_isotropic,
            "PropMaterial.GetMPOrthotropic": self._wrap_get_mp_orthotropic,
            "PropMaterial.GetMPAnisotropic": self._wrap_get_mp_anisotropic,
            "PropMaterial.GetMPUniaxial": self._wrap_get_mp_uniaxial,
        }
        if path in special:
            return lambda *args, **kwargs: special[path](func, *args, **kwargs)
        return func

    def _wrap_get_name_list(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(0, [])
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_get_name_list_on_story(self, func, story_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(story_name, 0, [])
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(story_name, *args, **kwargs)
        return func(story_name)

    def _wrap_get_type_oapi_1(self, func, case_name, *args, **kwargs):
        if self.backend == "dotnet":
            case_type_ref = eLoadCaseType.resolve(eLoadCaseType.LinearStatic, api_module=self.api_module)
            design_type_ref = eLoadPatternType.resolve(eLoadPatternType.Dead, api_module=self.api_module)
            result = func(case_name, case_type_ref, 0, design_type_ref, 0, 0)
            normalized = self.normalize_api_result(result)
            return tuple(int(item) if hasattr(item, "__int__") else item for item in normalized)

        if args or kwargs:
            return func(case_name, *args, **kwargs)
        return func(case_name)

    def _wrap_load_pattern_get_load_type(self, func, pattern_name, *args, **kwargs):
        if self.backend == "dotnet":
            load_type_ref = eLoadPatternType.resolve(eLoadPatternType.Dead, api_module=self.api_module)
            normalized = self.normalize_api_result(func(pattern_name, load_type_ref))
            return (
                self._as_int(self._item(normalized, 0)),
                self._as_int(self._item(normalized, 1)),
            )
        if args or kwargs:
            return func(pattern_name, *args, **kwargs)
        return func(pattern_name)

    def _wrap_load_pattern_get_self_wt_multiplier(self, func, pattern_name, *args, **kwargs):
        if self.backend == "dotnet":
            normalized = self.normalize_api_result(func(pattern_name, 0.0))
            return (
                self._as_float(self._item(normalized, 0)),
                self._as_int(self._item(normalized, 1)),
            )
        if args or kwargs:
            return func(pattern_name, *args, **kwargs)
        return func(pattern_name)

    def _wrap_get_case_list(self, func, combo_name, *args, **kwargs):
        if self.backend == "dotnet":
            cname_type_ref = eCNameType.resolve(eCNameType.LoadCase, api_module=self.api_module)
            result = func(combo_name, 0, [cname_type_ref], [], [])
            data = self.normalize_api_result(result)
            return (
                int(data[0]),
                [int(item) if hasattr(item, "__int__") else item for item in data[1]],
                list(data[2]),
                [float(item) for item in data[3]],
                int(data[4]),
            )
        if args or kwargs:
            return self.normalize_api_result(func(combo_name, *args, **kwargs))
        return self.normalize_api_result(func(combo_name))

    def _wrap_get_table_for_editing_array(self, func, table_name, *args, **kwargs):
        if self.backend == "dotnet":
            return self.normalize_api_result(func(table_name, "", 0, [], 0, []))
        if args or kwargs:
            return func(table_name, *args, **kwargs)
        return func(table_name, GroupName="")

    def _wrap_apply_edited_tables(self, func, fill_import_log, *args, **kwargs):
        if self.backend == "dotnet":
            normalized = self.normalize_api_result(func(fill_import_log, 0, 0, 0, 0, ""))
            return (
                bool(fill_import_log),
                self._as_int(self._item(normalized, 0)),
                self._as_int(self._item(normalized, 1)),
                self._as_int(self._item(normalized, 2)),
                self._as_int(self._item(normalized, 3)),
                self._item(normalized, 4, ""),
                self._as_int(self._item(normalized, 5)),
            )
        if args or kwargs:
            return func(fill_import_log, *args, **kwargs)
        return func(fill_import_log)

    def _wrap_set_table_for_editing_array(self, func, table_key, table_version, fields, number_records, table_data, *args, **kwargs):
        return func(table_key, table_version, fields, number_records, table_data)

    def _wrap_add_cartesian(self, func, x, y, z, *args, **kwargs):
        if self.backend == "dotnet":
            user_name = kwargs.get("UserName", "")
            csys = kwargs.get("CSys", "Global")
            merge_off = kwargs.get("MergeOff", False)
            merge_number = kwargs.get("MergeNumber", 0)
            return self.normalize_api_result(func(x, y, z, "", user_name, csys, merge_off, merge_number))
        return func(x, y, z, *args, **kwargs)

    def _wrap_resp_combo_add(self, func, combo_name, combo_type, *args, **kwargs):
        return func(combo_name, combo_type, *args, **kwargs)

    def _wrap_resp_combo_set_case_list(self, func, combo_name, cname_type, case_name, scale_factor, *args, **kwargs):
        if self.backend == "dotnet":
            cname_type = eCNameType.resolve(cname_type, api_module=self.api_module)
        return func(combo_name, cname_type, case_name, scale_factor, *args, **kwargs)

    def _wrap_load_patterns_add(self, func, name, my_type, self_wt_multiplier=0, add_analysis_case=True, *args, **kwargs):
        if self.backend == "dotnet":
            my_type = self.coerce_api_enum("eLoadPatternType", my_type)
        return func(name, my_type, self_wt_multiplier, add_analysis_case, *args, **kwargs)

    def _wrap_set_material(self, func, material_name, material_type, *args, **kwargs):
        if self.backend == "dotnet":
            material_type = eMatType.resolve(material_type, api_module=self.api_module)
        return func(material_name, material_type, *args, **kwargs)

    def _wrap_set_mp_isotropic(self, func, material_name, E, U, A, *args, **kwargs):
        return func(material_name, E, U, A, *args, **kwargs)

    def _wrap_set_weight_and_mass(self, func, material_name, option_value, value, *args, **kwargs):
        return func(material_name, option_value, value, *args, **kwargs)

    def _wrap_set_mp_uniaxial(self, func, material_name, E, A, *args, **kwargs):
        return func(material_name, E, A, *args, **kwargs)

    def _wrap_set_restraint(self, func, point_name, values, item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            Array = self.get_system_types()[0]
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module)
            values = Array[bool]([bool(value) for value in values])
            return func(point_name, values, item_type, *args, **kwargs)
        return func(point_name, values, item_type, *args, **kwargs)

    def _wrap_set_rectangle(self, func, name, mat_prop, t3, t2, *args, **kwargs):
        return func(name, mat_prop, t3, t2, *args, **kwargs)

    def _wrap_set_circle(self, func, name, mat_prop, t3, *args, **kwargs):
        return func(name, mat_prop, t3, *args, **kwargs)

    def _wrap_set_pipe(self, func, name, mat_prop, t3, tw, *args, **kwargs):
        return func(name, mat_prop, t3, tw, *args, **kwargs)

    def _wrap_set_tube(self, func, name, mat_prop, t3, t2, tf, tw, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, *args, **kwargs)

    def _wrap_set_i_section(self, func, name, mat_prop, t3, t2, tf, tw, t2b, tfb, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, t2b, tfb, *args, **kwargs)

    def _wrap_set_tee(self, func, name, mat_prop, t3, t2, tf, tw, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, *args, **kwargs)

    def _wrap_set_angle(self, func, name, mat_prop, t3, t2, tf, tw, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, *args, **kwargs)

    def _wrap_set_channel(self, func, name, mat_prop, t3, t2, tf, tw, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, *args, **kwargs)

    def _wrap_set_sd_section(self, func, name, mat_prop, design_type=0, *args, **kwargs):
        return func(name, mat_prop, design_type, *args, **kwargs)

    def _wrap_set_dbl_angle(self, func, name, mat_prop, t3, t2, tf, tw, dis, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, dis, *args, **kwargs)

    def _wrap_set_dbl_channel(self, func, name, mat_prop, t3, t2, tf, tw, dis, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, dis, *args, **kwargs)

    def _wrap_set_concrete_box(self, func, name, mat_prop, t3, t2, tf, tw, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, *args, **kwargs)

    def _wrap_set_concrete_tee(self, func, name, mat_prop, t3, t2, tf, twf, twt, mirror_about_3, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, twf, twt, mirror_about_3, *args, **kwargs)

    def _wrap_set_concrete_l(
        self, func, name, mat_prop, t3, t2, tf, twc, twt, mirror_about_2, mirror_about_3, *args, **kwargs
    ):
        return func(name, mat_prop, t3, t2, tf, twc, twt, mirror_about_2, mirror_about_3, *args, **kwargs)

    def _wrap_set_concrete_cross(self, func, name, mat_prop, t3, t2, tf, tw, *args, **kwargs):
        return func(name, mat_prop, t3, t2, tf, tw, *args, **kwargs)

    def _wrap_set_concrete_pipe(self, func, name, mat_prop, diameter, tw, *args, **kwargs):
        return func(name, mat_prop, diameter, tw, *args, **kwargs)

    def _wrap_set_plate(self, func, name, mat_prop, t3, t2, *args, **kwargs):
        return func(name, mat_prop, t3, t2, *args, **kwargs)

    def _wrap_set_rod(self, func, name, mat_prop, t3, *args, **kwargs):
        return func(name, mat_prop, t3, *args, **kwargs)

    def _wrap_set_cold_c(self, func, name, mat_prop, t3, t2, thickness, radius, lip_depth, *args, **kwargs):
        return func(name, mat_prop, t3, t2, thickness, radius, lip_depth, *args, **kwargs)

    def _wrap_set_cold_z(self, func, name, mat_prop, t3, t2, thickness, radius, lip_depth, lip_angle, *args, **kwargs):
        return func(name, mat_prop, t3, t2, thickness, radius, lip_depth, lip_angle, *args, **kwargs)

    def _wrap_set_cold_hat(self, func, name, mat_prop, t3, t2, thickness, radius, lip_depth, *args, **kwargs):
        return func(name, mat_prop, t3, t2, thickness, radius, lip_depth, *args, **kwargs)

    def _wrap_set_wall(self, func, name, wall_prop_type, shell_type, mat_prop, thickness, *args, **kwargs):
        if self.backend == "dotnet":
            wall_prop_type = self.coerce_api_enum("eWallPropType", wall_prop_type)
            shell_type = self.coerce_api_enum("eShellType", shell_type)
        return func(name, wall_prop_type, shell_type, mat_prop, thickness, *args, **kwargs)

    def _wrap_set_slab(self, func, name, slab_type, shell_type, mat_prop, thickness, *args, **kwargs):
        if self.backend == "dotnet":
            slab_type = self.coerce_api_enum("eSlabType", slab_type)
            shell_type = self.coerce_api_enum("eShellType", shell_type)
        return func(name, slab_type, shell_type, mat_prop, thickness, *args, **kwargs)

    def _wrap_set_slab_ribbed(
        self, func, name, overall_depth, slab_thickness, stem_width_top, stem_width_bot, rib_spacing, ribs_parallel_to, *args, **kwargs
    ):
        return func(
            name, overall_depth, slab_thickness, stem_width_top, stem_width_bot, rib_spacing, ribs_parallel_to, *args, **kwargs
        )

    def _wrap_set_slab_waffle(
        self, func, name, overall_depth, slab_thickness, stem_width_top, stem_width_bot, rib_spacing_dir1, rib_spacing_dir2, *args, **kwargs
    ):
        return func(
            name, overall_depth, slab_thickness, stem_width_top, stem_width_bot, rib_spacing_dir1, rib_spacing_dir2, *args, **kwargs
        )

    def _wrap_set_deck_1(
        self,
        func,
        name,
        deck_type,
        slab_fill_mat_prop,
        deck_mat_prop,
        slab_depth,
        rib_depth,
        rib_width_top,
        rib_width_bot,
        rib_spacing,
        deck_shear_thickness,
        deck_unit_weight,
        shear_stud_dia,
        shear_stud_hs,
        shear_stud_fu,
        *args,
        **kwargs,
    ):
        if self.backend == "dotnet":
            deck_type = self.coerce_api_enum("eDeckType", deck_type)
        return func(
            name,
            deck_type,
            slab_fill_mat_prop,
            deck_mat_prop,
            slab_depth,
            rib_depth,
            rib_width_top,
            rib_width_bot,
            rib_spacing,
            deck_shear_thickness,
            deck_unit_weight,
            shear_stud_dia,
            shear_stud_hs,
            shear_stud_fu,
            *args,
            **kwargs,
        )

    def _wrap_set_deck_filled(
        self, func, name, slab_depth, rib_depth, rib_width_top, rib_width_bot, rib_spacing, shear_thickness, unit_weight, shear_stud_dia, shear_stud_ht, shear_stud_fu, *args, **kwargs
    ):
        return func(
            name, slab_depth, rib_depth, rib_width_top, rib_width_bot, rib_spacing, shear_thickness, unit_weight, shear_stud_dia, shear_stud_ht, shear_stud_fu, *args, **kwargs
        )

    def _wrap_set_deck_unfilled(
        self, func, name, rib_depth, rib_width_top, rib_width_bot, rib_spacing, shear_thickness, unit_weight, *args, **kwargs
    ):
        return func(name, rib_depth, rib_width_top, rib_width_bot, rib_spacing, shear_thickness, unit_weight, *args, **kwargs)

    def _wrap_set_deck_solid_slab(self, func, name, slab_depth, shear_stud_dia, shear_stud_ht, shear_stud_fu, *args, **kwargs):
        return func(name, slab_depth, shear_stud_dia, shear_stud_ht, shear_stud_fu, *args, **kwargs)

    def _wrap_set_shell_layer(
        self, func, name, number_layers, layer_name, dist, thickness, mat_prop, nonlinear, mat_ang, num_integration_pts, *args, **kwargs
    ):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            layer_name = Array[String]([str(value) for value in layer_name])
            dist = Array[Double]([float(value) for value in dist])
            thickness = Array[Double]([float(value) for value in thickness])
            mat_prop = Array[String]([str(value) for value in mat_prop])
            nonlinear = Array[bool]([bool(value) for value in nonlinear])
            mat_ang = Array[Double]([float(value) for value in mat_ang])
            num_integration_pts = Array[Int32]([int(value) for value in num_integration_pts])
            number_layers = Int32(number_layers)
        return func(
            name, number_layers, layer_name, dist, thickness, mat_prop, nonlinear, mat_ang, num_integration_pts, *args, **kwargs
        )

    def _wrap_area_set_property(self, func, name, prop_name, item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, prop_name, item_type, *args, **kwargs)

    def _wrap_area_set_load_uniform(self, func, name, load_pat, value, direction, replace=True, c_sys="Global", item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, load_pat, value, direction, replace, c_sys, item_type, *args, **kwargs)

    def _wrap_area_set_load_uniform_to_frame(
        self, func, name, load_pat, value, direction, dist_type, replace=True, c_sys="Global", item_type=0, *args, **kwargs
    ):
        if self.backend == "dotnet":
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, load_pat, value, direction, dist_type, replace, c_sys, item_type, *args, **kwargs)

    def _wrap_area_add_by_coord(self, func, number_points, x, y, z, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, _String = self.get_system_types()
            result = func(
                Int32(number_points),
                Array[Double]([float(value) for value in x]),
                Array[Double]([float(value) for value in y]),
                Array[Double]([float(value) for value in z]),
                "",
                *args,
                **kwargs,
            )
            return self.normalize_api_result(result)
        return self.normalize_api_result(func(number_points, x, y, z, *args, **kwargs))

    def _wrap_add_by_point(self, func, point1, point2, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(point1, point2, "", *args, **kwargs)
            return self.normalize_api_result(result)
        return self.normalize_api_result(func(point1, point2, *args, **kwargs))

    def _wrap_frame_set_section(
        self, func, name, prop_name, item_type=0, s_var_rel_start_loc=0, s_var_total_length=0, *args, **kwargs
    ):
        if self.backend == "dotnet":
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, prop_name, item_type, s_var_rel_start_loc, s_var_total_length, *args, **kwargs)

    def _wrap_point_set_load_force(self, func, name, load_pat, values, replace=False, c_sys="Global", item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            Array = self.get_system_types()[0]
            values = Array[float]([float(value) for value in values])
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, load_pat, values, replace, c_sys, item_type, *args, **kwargs)

    def _wrap_frame_set_load_distributed(
        self, func, name, load_pat, my_type, direction, dist1, dist2, val1, val2, c_sys="Global", rel_dist=True, replace=True, item_type=0, *args, **kwargs
    ):
        if self.backend == "dotnet":
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, load_pat, my_type, direction, dist1, dist2, val1, val2, c_sys, rel_dist, replace, item_type, *args, **kwargs)

    def _wrap_frame_set_load_point(
        self, func, name, load_pat, my_type, direction, dist, val, c_sys="Global", rel_dist=True, replace=True, item_type=0, *args, **kwargs
    ):
        if self.backend == "dotnet":
            item_type = eItemType.resolve(eItemType.Objects, api_module=self.api_module) if item_type == 0 else self.coerce_api_enum("eItemType", item_type)
        return func(name, load_pat, my_type, direction, dist, val, c_sys, rel_dist, replace, item_type, *args, **kwargs)

    def _wrap_static_linear_set_case(self, func, name, *args, **kwargs):
        return func(name, *args, **kwargs)

    def _wrap_static_linear_set_initial_case(self, func, name, initial_case, *args, **kwargs):
        return func(name, initial_case, *args, **kwargs)

    def _wrap_static_linear_set_loads(self, func, name, number_loads, load_type, load_name, sf, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            load_type = Array[String]([str(value) for value in load_type])
            load_name = Array[String]([str(value) for value in load_name])
            sf = Array[Double]([float(value) for value in sf])
            number_loads = Int32(number_loads)
        return func(name, number_loads, load_type, load_name, sf, *args, **kwargs)

    def _wrap_response_spectrum_set_case(self, func, name, *args, **kwargs):
        return func(name, *args, **kwargs)

    def _wrap_response_spectrum_set_loads(self, func, name, number_loads, load_name, func_name, sf, c_sys, ang, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            number_loads = Int32(number_loads)
            load_name = Array[String]([str(value) for value in load_name])
            func_name = Array[String]([str(value) for value in func_name])
            sf = Array[Double]([float(value) for value in sf])
            c_sys = Array[String]([str(value) for value in c_sys])
            ang = Array[Double]([float(value) for value in ang])
        return func(name, number_loads, load_name, func_name, sf, c_sys, ang, *args, **kwargs)

    def _wrap_refresh_view(self, func, window=0, zoom=True, *args, **kwargs):
        return func(window, zoom, *args, **kwargs)

    def _wrap_open_file(self, func, file_name, *args, **kwargs):
        return func(file_name, *args, **kwargs)

    def _wrap_new_blank(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def _wrap_run_analysis(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def _wrap_get_prop_material_type_oapi(self, func, material_name, *args, **kwargs):
        if self.backend == "dotnet":
            mat_type_ref = eMatType.resolve(eMatType.Steel, api_module=self.api_module)
            result = func(material_name, mat_type_ref, 0)
            normalized = self.normalize_api_result(result)
            return tuple(int(item) if hasattr(item, "__int__") else item for item in normalized)
        if args or kwargs:
            return func(material_name, *args, **kwargs)
        return func(material_name)

    def _wrap_get_resp_combo_type_oapi(self, func, combo_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(combo_name, 0)
            normalized = self.normalize_api_result(result)
            return tuple(int(item) if hasattr(item, "__int__") else item for item in normalized)
        if args or kwargs:
            return func(combo_name, *args, **kwargs)
        return func(combo_name)

    def _wrap_resp_combo_get_type_combo(self, func, combo_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(combo_name, 0)
            normalized = self.normalize_api_result(result)
            return tuple(self._as_int(item) if hasattr(item, "__int__") or item in ("", None) else item for item in normalized)
        if args or kwargs:
            return func(combo_name, *args, **kwargs)
        return func(combo_name)

    def _wrap_joint_react(self, func, point_name, item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            item_type = eItemTypeElm.resolve(eItemTypeElm.ObjectElm, api_module=self.api_module)
            result = func(
                point_name,item_type,0,[],[],[],[],[],[],[],[],[],[],[]
            )
            return self.normalize_api_result(result)
        return self.normalize_api_result(func(point_name, item_type))

    def _wrap_frame_force(self, func, frame_name, item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            item_type = eItemTypeElm.resolve(eItemTypeElm.ObjectElm, api_module=self.api_module)
            result = func(
                frame_name,
                item_type,
                0,
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
            )
            return self.normalize_api_result(result)
        return self.normalize_api_result(func(frame_name, item_type))

    def _wrap_area_force_shell(self, func, area_name, item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            item_type = eItemTypeElm.resolve(eItemTypeElm.ObjectElm, api_module=self.api_module)
            result = func(
                area_name,
                item_type,
                0,
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
            )
            return self.normalize_api_result(result)
        return self.normalize_api_result(func(area_name, item_type))

    def _wrap_pier_force(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            result = func(
                Int32(0),
                Array[String]([]),
                Array[String]([]),
                Array[String]([]),
                Array[String]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
            )
            normalized = self.normalize_api_result(result)
            return (
                self._as_int(self._item(normalized, 0)),
                tuple(self._item(normalized, 1, ())),
                tuple(self._item(normalized, 2, ())),
                tuple(self._item(normalized, 3, ())),
                tuple(self._item(normalized, 4, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 5, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 6, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 7, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 8, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 9, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 10, ())),
                self._as_int(self._item(normalized, 11)),
            )
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_modal_participating_mass_ratios(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            result = func(
                Int32(0),
                Array[String]([]),
                Array[String]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
            )
            normalized = self.normalize_api_result(result)
            return (
                self._as_int(self._item(normalized, 0)),
                tuple(self._item(normalized, 1, ())),
                tuple(self._item(normalized, 2, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 3, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 4, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 5, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 6, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 7, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 8, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 9, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 10, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 11, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 12, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 13, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 14, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 15, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 16, ())),
                self._as_int(self._item(normalized, 17)),
            )
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_joint_displ(self, func, point_name, item_type=0, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            item_type = eItemTypeElm.resolve(eItemTypeElm.ObjectElm, api_module=self.api_module)
            result = func(
                point_name,
                item_type,
                Int32(0),
                Array[String]([]),
                Array[String]([]),
                Array[String]([]),
                Array[String]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
            )
            normalized = self.normalize_api_result(result)
            return (
                self._as_int(self._item(normalized, 0)),
                tuple(self._item(normalized, 1, ())),
                tuple(self._item(normalized, 2, ())),
                tuple(self._item(normalized, 3, ())),
                tuple(self._item(normalized, 4, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 5, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 6, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 7, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 8, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 9, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 10, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 11, ())),
                self._as_int(self._item(normalized, 12)),
            )
        return self.normalize_api_result(func(point_name, item_type))

    def _wrap_get_available_tables(self, func, *args, **kwargs):
        result = func(0, [], [], [])
        return self.normalize_api_result(result)

    def _wrap_get_table_for_display_array(self, func, table_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(table_name, [], "", 0, [], 0, [])
            data = self.normalize_api_result(result)
            return (data[0], data[1], list(data[2]), int(data[3]), list(data[4]), int(data[5]))
        return func(table_name, FieldKeyList="", GroupName="")

    def _wrap_get_all_frame_properties_2(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            prop_type_ref = eFramePropType.resolve(eFramePropType.Rectangular, api_module=self.api_module)
            result = func(0, [], [prop_type_ref], [], [], [], [], [], [], [])
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_get_sect_props(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(section_name, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_rectangle(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(section_name, "", "", 0.0, 0.0, 0, "", "")
            normalized = self.normalize_api_result(result)
            return (
                self._item(normalized, 0, ""),
                self._item(normalized, 1, ""),
                self._as_float(self._item(normalized, 2)),
                self._as_float(self._item(normalized, 3)),
                self._as_int(self._item(normalized, 4)),
                self._item(normalized, 5, ""),
                self._item(normalized, 6, ""),
                self._as_int(self._item(normalized, 7)),
            )
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_section(self, func, frame_name, *args, **kwargs):
        result = func(frame_name, "", "")
        return self.normalize_api_result(result)

    def _wrap_get_points(self, func, frame_name, *args, **kwargs):
        result = func(frame_name, "", "")
        return self.normalize_api_result(result)

    def _wrap_area_get_property(self, func, area_name, *args, **kwargs):
        if self.backend == "dotnet":
            return self.normalize_api_result(func(area_name, ""))
        if args or kwargs:
            return func(area_name, *args, **kwargs)
        return func(area_name)

    def _wrap_area_get_points(self, func, area_name, *args, **kwargs):
        if self.backend == "dotnet":
            return self.normalize_api_result(func(area_name, 0, []))
        if args or kwargs:
            return func(area_name, *args, **kwargs)
        return func(area_name)

    def _wrap_get_wall(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            wall_prop_type = self.get_api_enum_placeholder("eWallPropType")
            shell_type = self.get_api_enum_placeholder("eShellType")
            normalized = self.normalize_api_result(
                func(section_name, wall_prop_type, shell_type, "", 0.0, 0, "", "")
            )
            return (
                self._as_int(self._item(normalized, 0)),
                self._as_int(self._item(normalized, 1)),
                self._item(normalized, 2, ""),
                self._as_float(self._item(normalized, 3)),
                self._as_int(self._item(normalized, 4)),
                self._item(normalized, 5, ""),
                self._item(normalized, 6, ""),
                self._as_int(self._item(normalized, 7)),
            )
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_slab(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            slab_type = self.get_api_enum_placeholder("eSlabType")
            shell_type = self.get_api_enum_placeholder("eShellType")
            normalized = self.normalize_api_result(
                func(section_name, slab_type, shell_type, "", 0.0, 0, "", "")
            )
            return (
                self._as_int(self._item(normalized, 0)),
                self._as_int(self._item(normalized, 1)),
                self._item(normalized, 2, ""),
                self._as_float(self._item(normalized, 3)),
                self._as_int(self._item(normalized, 4)),
                self._item(normalized, 5, ""),
                self._item(normalized, 6, ""),
                self._as_int(self._item(normalized, 7)),
            )
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_slab_ribbed(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            normalized = self.normalize_api_result(
                func(section_name, 0.0, 0.0, 0.0, 0.0, 0.0, 0)
            )
            return (
                self._as_float(self._item(normalized, 0)),
                self._as_float(self._item(normalized, 1)),
                self._as_float(self._item(normalized, 2)),
                self._as_float(self._item(normalized, 3)),
                self._as_float(self._item(normalized, 4)),
                self._as_int(self._item(normalized, 5)),
                self._as_int(self._item(normalized, 6)),
            )
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_slab_waffle(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            normalized = self.normalize_api_result(
                func(section_name, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            )
            return (
                self._as_float(self._item(normalized, 0)),
                self._as_float(self._item(normalized, 1)),
                self._as_float(self._item(normalized, 2)),
                self._as_float(self._item(normalized, 3)),
                self._as_float(self._item(normalized, 4)),
                self._as_float(self._item(normalized, 5)),
                self._as_int(self._item(normalized, 6)),
            )
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_deck_1(self, func, section_name, *args, **kwargs):
        if self.backend == "dotnet":
            deck_type = self.get_api_enum_placeholder("eDeckType")
            normalized = self.normalize_api_result(
                func(
                    section_name,
                    deck_type,
                    "",
                    "",
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0,
                    "",
                    "",
                )
            )
            return (
                self._as_int(self._item(normalized, 0)),
                self._item(normalized, 1, ""),
                self._item(normalized, 2, ""),
                self._as_float(self._item(normalized, 3)),
                self._as_float(self._item(normalized, 4)),
                self._as_float(self._item(normalized, 5)),
                self._as_float(self._item(normalized, 6)),
                self._as_float(self._item(normalized, 7)),
                self._as_float(self._item(normalized, 8)),
                self._as_float(self._item(normalized, 9)),
                self._as_float(self._item(normalized, 10)),
                self._as_float(self._item(normalized, 11)),
                self._as_float(self._item(normalized, 12)),
                self._as_float(self._item(normalized, 13)),
                self._as_int(self._item(normalized, 14)),
                self._item(normalized, 15, ""),
                self._item(normalized, 16, ""),
                self._as_int(self._item(normalized, 17)),
            )
        if args or kwargs:
            return func(section_name, *args, **kwargs)
        return func(section_name)

    def _wrap_get_label_name_list(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(0, [], [], [])
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_get_name_from_label(self, func, label, story, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(label, story, "")
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(label, story, *args, **kwargs)
        return func(label, story)

    def _wrap_get_coord_cartesian(self, func, point_name, *args, **kwargs):
        if self.backend == "dotnet":
            csys = kwargs.get("CSys", "Global")
            if len(args) >= 4:
                csys = args[3]
            result = func(point_name, 0.0, 0.0, 0.0, csys)
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(point_name, *args, **kwargs)
        return func(point_name)

    def _wrap_get_restraint(self, func, point_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(point_name, [])
            return self.normalize_api_result(result)
        if args or kwargs:
            return func(point_name, *args, **kwargs)
        return func(point_name, [])

    def _wrap_get_selected(self, func, *args, **kwargs):
        if args:
            point_name, *rest = args
            if self.backend == "dotnet":
                result = func(point_name, False, *rest, **kwargs)
                normalized = self.normalize_api_result(result)
                return (bool(self._item(normalized, 0, False)), self._as_int(self._item(normalized, 1)))
            return func(point_name, *rest, **kwargs)

        result = func(**kwargs)
        return self.normalize_api_result(result)

    def _wrap_select_obj_get_selected(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            Array, _Double, Int32, String = self.get_system_types()
            result = func(Int32(0), Array[Int32]([]), Array[String]([]))
            normalized = self.normalize_api_result(result)
            return (
                self._as_int(self._item(normalized, 0)),
                tuple(self._as_int(item) for item in self._item(normalized, 1, ())),
                tuple(self._item(normalized, 2, ())),
                self._as_int(self._item(normalized, 3)),
            )
        result = func(*args, **kwargs)
        return self.normalize_api_result(result)

    def _wrap_get_all_areas(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            Array, Double, Int32, String = self.get_system_types()
            orientation_ref = eAreaDesignOrientation.resolve(eAreaDesignOrientation.Wall, api_module=self.api_module)
            orientation_type = type(orientation_ref)
            result = func(
                Int32(0),
                Array[String]([]),
                Array[orientation_type]([]),
                Int32(0),
                Array[Int32]([]),
                Array[String]([]),
                Array[Double]([]),
                Array[Double]([]),
                Array[Double]([]),
            )
            normalized = self.normalize_api_result(result)
            return (
                int(normalized[0]),
                tuple(normalized[1]),
                tuple(int(item) if hasattr(item, "__int__") else item for item in normalized[2]),
                int(normalized[3]),
                tuple(normalized[4]),
                tuple(normalized[5]),
                tuple(float(item) for item in normalized[6]),
                tuple(float(item) for item in normalized[7]),
                tuple(float(item) for item in normalized[8]),
                int(normalized[9]),
            )
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_get_stories(self, func, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(0, [], [], [], [], [], [], [])
            normalized = self.normalize_api_result(result)
            return (
                self._as_int(self._item(normalized, 0)),
                tuple(self._item(normalized, 1, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 2, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 3, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 4, ())),
                tuple(bool(item) for item in self._item(normalized, 5, ())),
                tuple(self._item(normalized, 6, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 7, ())),
                self._as_int(self._item(normalized, 8)),
            )
        if args or kwargs:
            return func(*args, **kwargs)
        return func()

    def _wrap_get_story_height(self, func, story_name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(story_name, 0.0)
            normalized = self.normalize_api_result(result)
            return (
                self._as_float(self._item(normalized, 0)),
                self._as_int(self._item(normalized, 1)),
            )
        if args or kwargs:
            return func(story_name, *args, **kwargs)
        return func(story_name)

    def _wrap_get_grid_sys_2(self, func, name, *args, **kwargs):
        if self.backend == "dotnet":
            result = func(
                name,
                0.0,
                0.0,
                0.0,
                "",
                0,
                0,
                [],
                [],
                [],
                [],
                [],
                [],
                [],
                [],
            )
            normalized = self.normalize_api_result(result)
            return (
                self._as_float(self._item(normalized, 0)),
                self._as_float(self._item(normalized, 1)),
                self._as_float(self._item(normalized, 2)),
                self._item(normalized, 3, ""),
                self._as_int(self._item(normalized, 4)),
                self._as_int(self._item(normalized, 5)),
                tuple(self._item(normalized, 6, ())),
                tuple(self._item(normalized, 7, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 8, ())),
                tuple(self._as_float(item) for item in self._item(normalized, 9, ())),
                tuple(bool(item) for item in self._item(normalized, 10, ())),
                tuple(bool(item) for item in self._item(normalized, 11, ())),
                tuple(self._item(normalized, 12, ())),
                tuple(self._item(normalized, 13, ())),
                self._as_int(self._item(normalized, 14)),
            )
        if args or kwargs:
            return func(name, *args, **kwargs)
        return func(name)

    def _wrap_get_mpi_isotropic(self, func, material_name, *args, **kwargs):
        if self.backend == "dotnet":
            temp = kwargs.get("Temp", 0)
            if len(args) >= 5:
                temp = args[4]
            result = func(material_name, 0.0, 0.0, 0.0, 0.0, temp)
            normalized = self.normalize_api_result(result)
            return tuple(float(item) if isinstance(item, (int, float)) else item for item in normalized)
        if args or kwargs:
            return func(material_name, *args, **kwargs)
        return func(material_name)

    def _wrap_get_mp_orthotropic(self, func, material_name, *args, **kwargs):
        if self.backend == "dotnet":
            return self.normalize_api_result(func(material_name, [], [], [], []))
        if args or kwargs:
            return func(material_name, *args, **kwargs)
        return func(material_name)

    def _wrap_get_mp_anisotropic(self, func, material_name, *args, **kwargs):
        if self.backend == "dotnet":
            return self.normalize_api_result(func(material_name, [], [], [], []))
        if args or kwargs:
            return func(material_name, *args, **kwargs)
        return func(material_name)

    def _wrap_get_mp_uniaxial(self, func, material_name, *args, **kwargs):
        if self.backend == "dotnet":
            return self.normalize_api_result(func(material_name, 0.0, 0.0))
        if args or kwargs:
            return func(material_name, *args, **kwargs)
        return func(material_name)

