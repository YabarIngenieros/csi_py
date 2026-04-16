"""Prueba propiedades y métodos de extractor por lotes de 5."""

import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csi_py import Handler


def _summarize(value):
    if hasattr(value, "shape"):
        return f"{type(value).__name__} shape={value.shape}"
    if isinstance(value, dict):
        return f"dict keys={list(value.keys())[:5]}"
    if isinstance(value, (list, tuple, set)):
        return f"{type(value).__name__} len={len(value)}"
    if value is None:
        return "None"
    return repr(value)[:120]


def _run_checks(handler, checks, batch_size=5):
    batches = [checks[i:i + batch_size] for i in range(0, len(checks), batch_size)]
    return batches


def _run_batch(batch_number, batch):
    print("-" * 70)
    print(f"Lote {batch_number}")
    print("-" * 70)
    for name, func in batch:
        try:
            value = func()
            print(f"[OK] {name}: {_summarize(value)}")
        except Exception as exc:
            print(f"[ERR] {name}: {type(exc).__name__}: {exc}")
    print()


def run_backend(backend, batch_to_run=1):
    print("=" * 70)
    print(f"Probando backend: {backend}")
    print("=" * 70)

    handler = Handler(backend=backend)
    handler.connect_open_instance()

    print(f"Programa: {handler.program}")
    print(f"Backend real: {handler.backend}")
    print(f"Modelo conectado: {handler.file_name}")
    print(f"Archivo: {handler.file_path}")
    print()

    sample_frame = handler.frame_list[0] if handler.frame_list else None
    sample_area = handler.area_list[0] if handler.area_list else None
    sample_pier = handler.pier_list[0] if handler.pier_list else None
    stories = list(handler.stories) if hasattr(handler, "stories") and handler.stories else []
    sample_story = stories[1] if stories else None
    sample_combo = handler.combos[0] if handler.combos else None
    sample_case = handler.cases[0] if handler.cases else None

    checks = [
        ("available_tables", lambda: handler.available_tables),
        ("editable_tables", lambda: handler.editable_tables),
        ("cases", lambda: handler.cases),
        ("combos", lambda: handler.combos),
        ("cases_and_combos", lambda: handler.cases_and_combos),
        ("design_cases", lambda: handler.design_cases),
        ("seismic_cases", lambda: handler.seismic_cases),
        ("seismic_cases_and_combos", lambda: handler.seismic_cases_and_combos),
        ("material_list", lambda: handler.material_list),
        ("point_list", lambda: handler.point_list),
        ("points_coordinates", lambda: handler.points_coordinates),
        ("points_restraints", lambda: handler.points_restraints),
        ("frame_sections_list", lambda: handler.frame_sections_list),
        ("frame_sections_data", lambda: handler.frame_sections_data),
        ("frame_list", lambda: handler.frame_list),
        ("frame_label_names", lambda: handler.frame_label_names),
        ("frames_properties", lambda: handler.frames_properties),
        ("area_section_list", lambda: handler.area_section_list),
        ("area_list", lambda: handler.area_list),
        ("pier_list", lambda: handler.pier_list),
        #("tabular_data", lambda: handler.tabular_data),
        ("design_cases_and_combos", lambda: handler.design_cases_and_combos),
        ("seismic_combos", lambda: handler.seismic_combos),
        ("gravity_cases", lambda: handler.gravity_cases),
        ("gravity_combos", lambda: handler.gravity_combos),
        ("gravity_cases_and_combos", lambda: handler.gravity_cases_and_combos),
        ("get_response_spectrum", lambda: handler.get_response_spectrum()),
        ("material_properties", lambda: handler.material_properties),
        #("get_point_reactions", lambda: handler.get_point_reactions()),
        ("points_reactions", lambda: handler.points_reactions),
        #("get_frame_forces", lambda: handler.get_frame_forces()),
        #("frames_forces", lambda: handler.frames_forces),
        ("area_geometry", lambda: handler.area_geometry),
        ("get_area_forces", lambda: handler.get_area_forces()),
        ("area_forces", lambda: handler.area_forces),
        ("slab_sections_data", lambda: handler.slab_sections_data),
        ("deck_sections_data", lambda: handler.deck_sections_data),
        ("floor_sections_list", lambda: handler.floor_sections_list),
        ("floor_list", lambda: handler.floor_list),
        ("strip_list", lambda: handler.strip_list),
        ("extract_strip_loads", lambda: handler.extract_strip_loads()),
        ("strip_loads", lambda: handler.strip_loads),
        ("wall_sections_data", lambda: handler.wall_sections_data),
        ("wall_list", lambda: handler.wall_list),
        ("get_pier_forces", lambda: handler.get_pier_forces()),
        ("pier_forces", lambda: handler.pier_forces),
        ("get_pier_displacements", lambda: handler.get_pier_displacements()),
        ("stories", lambda: stories),
        ("get_story_height", lambda: handler.get_story_height(sample_story) if sample_story else []),
        ("get_story_forces", lambda: handler.get_story_forces()),
        ("story_forces", lambda: handler.story_forces),
        ("get_story_displacements", lambda: handler.get_story_displacements()),
        ("story_displacements", lambda: handler.story_displacements),
        ("get_story_drifts", lambda: handler.get_story_drifts()),
        ("story_drifts", lambda: handler.story_drifts),
        ("extract_soil_pressures", lambda: handler.extract_soil_pressures()),
        ("soil_pressures", lambda: handler.soil_pressures),
        ("get_modal_data", lambda: handler.get_modal_data()),
        ("modal_data", lambda: handler.modal_data),
        ("modal_cases", lambda: handler.modal_cases),
        ("get_modal_periods", lambda: handler.get_modal_periods()),
        ("get_modal_summary", lambda: handler.get_modal_summary()),
        ("get_modal_displacements", lambda: handler.get_modal_displacements()),
        ("get_modal_shape", lambda: handler.get_modal_shape()),
        ("get_model_geometry", lambda: handler.get_model_geometry()),
        ("get_geometry_summary", lambda: handler.get_geometry_summary()),
        ("export_geometry_to_dict", lambda: handler.export_geometry_to_dict(simplified=True)),
        ("get_load_cases_info", lambda: handler.get_load_cases_info()),
        ("get_load_cases_summary", lambda: handler.get_load_cases_summary()),
        ("export_load_cases_to_dict", lambda: handler.export_load_cases_to_dict(simplified=True)),
        ("get_combo_breakdown", lambda: handler.get_combo_breakdown(sample_combo) if sample_combo else []),
        ("get_frame_section_properties", lambda: handler.get_frame_section_properties(handler.frame_sections_list[0]) if handler.frame_sections_list else []),
        ("get_frame_section", lambda: handler.get_frame_section(sample_frame) if sample_frame else []),
        ("get_frame_points", lambda: handler.get_frame_points(sample_frame) if sample_frame else []),
        ("get_frame_coordinates", lambda: handler.get_frame_coordinates(sample_frame) if sample_frame else []),
        ("get_frame_length", lambda: handler.get_frame_length(sample_frame) if sample_frame else []),
        ("get_area_section", lambda: handler.get_area_section(sample_area) if sample_area else []),
        ("get_area_points", lambda: handler.get_area_points(sample_area) if sample_area else []),
        ("select_cases_and_combos", lambda: handler.select_cases_and_combos(handler.design_cases[:1]) or "ok"),
        ("get_combo_cases", lambda: handler.get_combo_cases(sample_combo) if sample_combo else []),
        ("get_material_properties", lambda: handler.get_material_properties(handler.material_list[:1]) if handler.material_list else []),
        ("get_point_coordinates", lambda: handler.get_point_coordinates(handler.point_list[:3])),
        ("get_point_restraints", lambda: handler.get_point_restraints(handler.point_list[:3])),
    ]

    try:
        batches = _run_checks(handler, checks, batch_size=5)
        if batch_to_run < 1 or batch_to_run > len(batches):
            raise ValueError(f"Lote inválido: {batch_to_run}. Debe estar entre 1 y {len(batches)}")
        _run_batch(batch_to_run, batches[batch_to_run - 1])
    except Exception:
        print("Se produjo un error general durante las pruebas.")
        traceback.print_exc()
        print()


def main():
    batch_to_run = 16
    if len(sys.argv) > 1:
        batch_to_run = int(sys.argv[1])
    for backend in ("comtypes", "dotnet"):
        run_backend(backend, batch_to_run=batch_to_run)


if __name__ == "__main__":
    main()
