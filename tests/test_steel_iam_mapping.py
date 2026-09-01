from pathlib import Path

import yaml


MAPPING = (
    Path(__file__).parents[1]
    / "premise"
    / "iam_variables_mapping"
    / "steel.yaml"
)
FINAL_ENERGY_MAPPING = (
    Path(__file__).parents[1]
    / "premise"
    / "iam_variables_mapping"
    / "final_energy.yaml"
)


def test_message_dri_routes_use_mutually_exclusive_processed_variables():
    mapping = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))

    assert mapping["steel - primary - DRI"]["iam_aliases"]["message"] == (
        "Production|Industry|Iron and Steel|NG-DRI/EAF"
    )
    assert mapping["steel - primary - DRI CCS"]["iam_aliases"]["message"] == (
        "Production|Industry|Iron and Steel|NG-DRI/EAF + CCS"
    )
    assert mapping["steel - primary - H-DRI"]["iam_aliases"]["message"] == (
        "Production|Industry|Iron and Steel|H-DRI/EAF"
    )


def test_message_dri_routes_do_not_reuse_aggregate_energy_inputs():
    mapping = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))

    for route in (
        "steel - primary - DRI",
        "steel - primary - DRI CCS",
        "steel - primary - H-DRI",
    ):
        assert "message" not in mapping[route].get("energy_use_aliases", {})


def test_tiam_h_dri_hydrogen_uses_preprocessed_final_energy_variable():
    mapping = yaml.safe_load(FINAL_ENERGY_MAPPING.read_text(encoding="utf-8"))

    assert mapping["Industry - Steel - H-DRI/EAF - H2"]["iam_aliases"][
        "tiam-ucl"
    ] == "Final Energy|Production|Steel|Secondary|DRH2 and EAF|Hydrogen"
