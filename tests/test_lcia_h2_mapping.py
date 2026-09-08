"""Consistency checks for the canonical H2-distribution LCIA mapping."""

import importlib.util
from pathlib import Path


MAPPING_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "h2-distribution_LCIA"
    / "LCIA_mapping_h2.py"
)
SPEC = importlib.util.spec_from_file_location("LCIA_mapping_h2", MAPPING_PATH)
MAPPING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MAPPING)


def test_database_records_are_unique_and_match_their_year():
    names = [record["database"] for record in MAPPING.DATABASES]
    assert len(names) == len(set(names))
    assert all(f"_{record['year']}_" in record["database"] for record in MAPPING.DATABASES)


def test_every_emitted_distribution_process_has_one_route_group():
    emitted = (
        set(MAPPING.TRANSPORT_NAMES.values())
        | set(MAPPING.CONVERSION_NAMES.values())
        | set(MAPPING.RECONVERSION_NAMES.values())
    )
    grouped = (
        MAPPING.GH2_PIPE_PROCESSES
        | MAPPING.GH2_TRUCK_PROCESSES
        | MAPPING.LH2_TRUCK_PROCESSES
        | MAPPING.NH3_TANKER_PROCESSES
    )
    assert emitted == grouped
    assert all(MAPPING.distribution_family(process) for process in emitted)
    assert (
        MAPPING.distribution_family("Hydrogen leakage — distribution")
        == MAPPING.SHARED_DISTRIBUTION_FAMILY
    )
    assert (
        MAPPING.distribution_family(
            "Hydrogen leakage — Liquid hydrogen regasification"
        )
        == "Liquid hydrogen"
    )


def test_scope_and_canonical_display_names_are_preserved():
    assert not any("liquefied hydrogen" in name for name in MAPPING.TRANSPORT_NAMES)
    assert (
        MAPPING.RECONVERSION_NAMES["liquid hydrogen regasification"]
        == "Liquid hydrogen regasification"
    )
    assert MAPPING.FAMILY_STYLES["Hydrogen production"]["cmap"] == "Greys"


def test_only_hydrogen_leakage_has_a_canonical_leakage_hatch():
    assert MAPPING.PROCESS_HATCH["Hydrogen leakage"] == "ooo"
    assert "Ammonia leakage" not in MAPPING.PROCESS_HATCH


def test_all_method_selection_comes_from_method_labels_without_ced():
    assert MAPPING.SELECTED_METHODS == tuple(MAPPING.METHOD_LABELS)
    assert MAPPING.CONTRIBUTION_METHODS == (MAPPING.PREMISE_GWP_METHOD,)
    assert all(
        method[0] != "Cumulative Energy Demand (CED)"
        for method in MAPPING.SELECTED_METHODS
    )
