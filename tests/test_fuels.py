from types import SimpleNamespace

import pytest
import xarray as xr

import premise.fuels.base as fuels_base
from premise.fuels.base import Fuels


def test_petrol_variants_reclassify_consumer_carbon_only_once():
    """A high biofuel share must not append the same combustion CO2 twice."""
    fuel = {
        "name": "market for petrol, low-sulfur",
        "product": "petrol, low-sulfur",
        "location": "RER",
        "unit": "kilogram",
        "type": "technosphere",
        "amount": 0.1,
    }
    fossil = {
        "name": "Carbon dioxide, fossil",
        "unit": "kilogram",
        "categories": ("air",),
        "type": "biosphere",
        "amount": 0.315,
    }
    consumer = {
        "name": "petrol consumer",
        "location": "R1",
        "exchanges": [fuel, fossil],
    }
    blend = xr.DataArray(
        [[[0.4]], [[0.6]]],
        dims=("variables", "region", "year"),
        coords={
            "variables": ["gasoline", "bioethanol"],
            "region": ["R1"],
            "year": [2050],
        },
    )
    fuels = object.__new__(Fuels)
    fuels.database = [consumer]
    fuels.fuel_map = {"gasoline": [], "bioethanol": []}
    fuels.model, fuels.system_model, fuels.year = "image", "cutoff", 2050
    fuels.regions = ["R1"]
    fuels.ecoinvent_to_iam_loc = {}
    fuels.iam_data = SimpleNamespace(production_volumes=blend, petrol_blend=blend)
    fuels.mapping = SimpleNamespace(
        generate_sets_from_filters=lambda _: {},
        generate_fuel_map=lambda **_: fuels.fuel_map,
    )
    fuels.generate_biofuel_activities = lambda: None
    fuels._filter_biodiesel_feedstocks = lambda: None
    fuels._filter_bioethanol_feedstocks = lambda: None
    created = []
    fuels.process_and_add_markets = lambda **kwargs: created.append(kwargs["name"])
    fuels.is_in_index = lambda exchange, location: exchange["name"] in created
    fuels.biosphere_flows = {
        ("Carbon dioxide, non-fossil", "air", "unspecified", "kilogram"): "bio-co2"
    }

    fuels.generate_synthetic_fuel_activities()

    assert len(created) == 3
    assert fuel["location"] == "R1"
    assert fossil["amount"] == pytest.approx(0.126)
    biogenic = [
        e for e in consumer["exchanges"] if e["name"] == "Carbon dioxide, non-fossil"
    ]
    assert len(biogenic) == 1
    assert biogenic[0]["amount"] == pytest.approx(0.189)
    assert fossil["amount"] + biogenic[0]["amount"] == pytest.approx(0.315)


def test_gcam_coal_methane_inventory_is_regionalized():
    coal_methane = {
        "name": (
            "methane, synthetic, gaseous, 5 bar, from coal-based hydrogen, "
            "at fuelling station"
        ),
        "reference product": "methane, high pressure",
        "location": "RER",
    }
    fuels = object.__new__(Fuels)
    fuels.database = [coal_methane]
    fuels.fuel_map = {"methane, from coal": [coal_methane]}
    fuels.iam_data = SimpleNamespace(
        production_volumes=None,
        natural_gas_blend=None,
    )
    fuels.mapping = SimpleNamespace(generate_fuel_map=lambda: {})

    captured = {}

    def capture_regionalization(mapping, production_volumes):
        captured.update(mapping)

    fuels.process_and_add_activities = capture_regionalization

    fuels.generate_biogas_activities()

    assert captured == {"methane, from coal": [coal_methane]}


@pytest.mark.parametrize(
    ("failure_stage", "expected_calls"),
    [
        ("logistics", ["logistics"]),
        ("logging", ["logistics", "logging"]),
        ("market creation", ["logistics", "logging", "market creation"]),
    ],
)
def test_fuel_update_fails_before_partial_hydrogen_processing(
    monkeypatch, failure_stage, expected_calls
):
    """Mandatory hydrogen steps must not produce a partial fuel update."""
    calls = []
    original_database = [{"name": "original dataset"}]

    class FailingFuels:
        def __init__(self, database, **_kwargs):
            self.database = database
            self.hydrogen_demand_nodes = "calculated demand nodes"

        @staticmethod
        def _fail_if_selected(stage):
            calls.append(stage)
            if failure_stage == stage:
                raise RuntimeError(f"failed during {stage}")

        def set_hydrogen_logistics(self):
            self._fail_if_selected("logistics")

        def write_hydrogen_demand_node_logs(self):
            self._fail_if_selected("logging")

        def generate_hydrogen_activities(self):
            self._fail_if_selected("market creation")

        def relink_hydrogen_consumers_to_sector_markets(self):
            calls.append("consumer relinking")

    iam_data = SimpleNamespace(
        petrol_blend=None,
        diesel_blend=None,
        natural_gas_blend=None,
        hydrogen_blend=object(),
    )
    scenario = {
        "database": original_database,
        "iam data": iam_data,
        "model": "test-model",
        "pathway": "test-pathway",
        "year": 2030,
    }

    monkeypatch.setattr(fuels_base, "Fuels", FailingFuels)

    with pytest.raises(RuntimeError, match=f"failed during {failure_stage}"):
        fuels_base._update_fuels(
            scenario=scenario,
            version="3.10",
            system_model="cutoff",
        )

    assert calls == expected_calls
    assert "consumer relinking" not in calls
    assert scenario["database"] is original_database


@pytest.mark.parametrize("storage", ["legacy", "working", "compact"])
@pytest.mark.parametrize("integrity_error", [False, True])
def test_hydrogen_finalizer_preserves_storage_and_checks_integrity(
    monkeypatch, storage, integrity_error
):
    from premise.inventory_store import CompactInventoryStore, get_scenario_inventory

    captured = {}

    class SynchronizingFuels:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.database = kwargs["database"]
            self.cache = {}
            self.index = {"rebuilt": True}

        def synchronize_hydrogen_distribution(self):
            self.unmatched_hydrogen_consumers = []
            self.matched_hydrogen_consumers = []
            self.skipped_hydrogen_consumers = []
            self.generated_hydrogen_sector_markets = []
            self.eligible_hydrogen_sector_market_regions = {}
            self.consumer_backed_hydrogen_sector_market_regions = {}
            self.excluded_eligible_hydrogen_sector_market_regions_without_consumers = {}
            self.generated_hydrogen_sector_market_regions = {}
            self.uncreated_eligible_hydrogen_sector_market_regions = {}
            self.skipped_hydrogen_sector_markets = []

        def write_hydrogen_sector_market_relink_logs(self):
            pass

    validator = SimpleNamespace(
        major_issues_log=[],
        check_hydrogen_distribution_integrity=lambda: (
            validator.major_issues_log.append({"reason": "orphan hydrogen market"})
            if integrity_error
            else None
        ),
    )
    monkeypatch.setattr(fuels_base, "Fuels", SynchronizingFuels)
    monkeypatch.setattr(
        fuels_base, "_hydrogen_distribution_validator", lambda scenario: validator
    )
    scenario = {
        "database": [
            {
                "name": "database",
                "reference product": "hydrogen",
                "location": "EUR",
                "unit": "kilogram",
                "exchanges": [],
            }
        ],
        "iam data": SimpleNamespace(regions=["EUR"]),
        "model": "image",
        "pathway": "SSP2-M",
        "year": 2050,
        "hydrogen demand nodes": "stored demand nodes",
    }

    if storage == "working":
        scenario["_inventory_working_copy"] = scenario.pop("database")
    elif storage == "compact":
        scenario["_inventory_store"] = CompactInventoryStore(scenario.pop("database"))

    if integrity_error:
        with pytest.raises(ValueError, match="orphan hydrogen market"):
            fuels_base._finalize_hydrogen_distribution(
                scenario, version="3.12", system_model="cutoff"
            )
    else:
        fuels_base._finalize_hydrogen_distribution(
            scenario, version="3.12", system_model="cutoff"
        )

    assert ("database" in scenario) == (storage == "legacy")
    assert get_scenario_inventory(scenario)[0]["name"] == "database"
    assert scenario["index"] == {"rebuilt": True}
    assert scenario["unmatched hydrogen consumers"] == []
    assert captured["cache"] == {}
    assert captured["index"] is None


def test_hydrogen_finalizer_is_noop_before_fuels_are_applied():
    scenario = {"database": []}

    assert (
        fuels_base._finalize_hydrogen_distribution(
            scenario, version="3.12", system_model="cutoff"
        )
        is scenario
    )


def test_fuel_carbon_update_preserves_ordered_exchange_semantics():
    fuel_input = {
        "name": "market for test fuel",
        "product": "test fuel",
        "location": "GLO",
        "unit": "kilogram",
        "type": "technosphere",
        "amount": 2.0,
    }
    fossil = {
        "name": "Carbon dioxide, fossil",
        "unit": "kilogram",
        "type": "biosphere",
        "amount": 10.0,
    }
    consumer = {
        "name": "fuel consumer",
        "location": "R1",
        "exchanges": [fuel_input, fossil],
    }
    market = {
        "name": "market for test fuel",
        "location": "R1",
        "exchanges": [fuel_input.copy(), fossil.copy()],
    }
    fuels = object.__new__(Fuels)
    fuels.database = [consumer, market]
    fuels.fuel_map = {"biofuel": [], "fossil": []}
    fuels.iam_data = SimpleNamespace(production_volumes=None)
    fuels.regions = ["R1"]
    fuels.ecoinvent_to_iam_loc = {}
    fuels.biosphere_flows = {
        ("Carbon dioxide, non-fossil", "air", "unspecified", "kilogram"): "flow"
    }
    fuels.is_in_index = lambda exchange, location: location == "R1"
    fuels.get_technology_and_regional_production_shares = lambda **kwargs: (
        None,
        {("biofuel", "R1"): 0.5, ("fossil", "R1"): 0.5},
        {"R1": 1.0},
    )

    fuels.update_fuel_carbon_dioxide_emissions(
        variables=["biofuel", "fossil"],
        market_names=["market for test fuel"],
        co2_intensity=1.0,
        fossil_variables=["fossil"],
    )

    assert fuel_input["location"] == "R1"
    assert fossil["amount"] == 9.0
    assert consumer["exchanges"][-1]["name"] == "Carbon dioxide, non-fossil"
    assert consumer["exchanges"][-1]["amount"] == 1.0
    assert len(market["exchanges"]) == 2
    assert market["exchanges"][0]["location"] == "GLO"
    assert market["exchanges"][1]["amount"] == 10.0


def test_diesel_markets_receive_the_marginal_blend():
    diesel_supplier = {
        "name": "diesel production",
        "reference product": "diesel",
        "location": "WEU",
        "unit": "kilogram",
        "exchanges": [],
    }
    diesel_blend = xr.DataArray(
        [[[1.0]]],
        dims=("variables", "region", "year"),
        coords={"variables": ["diesel"], "region": ["WEU"], "year": [2050]},
    )
    production_volumes = xr.DataArray(
        [[[10.0]]],
        dims=("variables", "region", "year"),
        coords={"variables": ["diesel"], "region": ["WEU"], "year": [2050]},
    )
    fuel_map = {"diesel": [diesel_supplier]}
    fuels = object.__new__(Fuels)
    fuels.fuel_map = fuel_map
    fuels.model = "image"
    fuels.system_model = "consequential"
    fuels.iam_data = SimpleNamespace(
        diesel_blend=diesel_blend,
        production_volumes=production_volumes,
    )
    fuels.mapping = SimpleNamespace(
        generate_sets_from_filters=lambda filters: {},
        generate_fuel_map=lambda model: fuel_map,
    )
    fuels.process_and_add_activities = lambda **kwargs: None
    fuels.generate_biofuel_activities = lambda: None
    fuels._filter_biodiesel_feedstocks = lambda: None
    fuels._filter_bioethanol_feedstocks = lambda: None
    market_calls = []
    carbon_calls = []
    fuels.process_and_add_markets = lambda **kwargs: market_calls.append(kwargs)
    fuels.update_fuel_carbon_dioxide_emissions = lambda **kwargs: carbon_calls.append(
        kwargs
    )

    fuels.generate_synthetic_fuel_activities()

    assert len(market_calls) == 4
    assert all(call["technology_shares"] is diesel_blend for call in market_calls)
    assert all(call["retain_validation_technology"] for call in market_calls)
    assert len(carbon_calls) == 1
    assert carbon_calls[0]["technology_shares"] is diesel_blend


def test_fuel_carbon_update_can_use_marginal_technology_shares():
    fuel_input = {
        "name": "market for diesel",
        "product": "diesel",
        "location": "R1",
        "unit": "kilogram",
        "type": "technosphere",
        "amount": 2.0,
    }
    fossil = {
        "name": "Carbon dioxide, fossil",
        "unit": "kilogram",
        "type": "biosphere",
        "amount": 10.0,
    }
    consumer = {
        "name": "diesel consumer",
        "location": "R1",
        "exchanges": [fuel_input, fossil],
    }
    production_volumes = xr.DataArray(
        [[[0.5]], [[0.5]]],
        dims=("variables", "region", "year"),
        coords={
            "variables": ["biodiesel", "diesel"],
            "region": ["R1"],
            "year": [2050],
        },
    )
    marginal_mix = xr.DataArray(
        [[[0.0]], [[1.0]]],
        dims=("variables", "region", "year"),
        coords={
            "variables": ["biodiesel", "diesel"],
            "region": ["R1"],
            "year": [2050],
        },
    )
    fuels = object.__new__(Fuels)
    fuels.database = [consumer]
    fuels.fuel_map = {"biodiesel": [], "diesel": []}
    fuels.iam_data = SimpleNamespace(production_volumes=production_volumes)
    fuels.regions = ["R1"]
    fuels.year = 2050
    fuels.ecoinvent_to_iam_loc = {}
    fuels.is_in_index = lambda exchange, location: True

    fuels.update_fuel_carbon_dioxide_emissions(
        variables=["biodiesel", "diesel"],
        market_names=["market for diesel"],
        co2_intensity=3.15,
        fossil_variables=["diesel"],
        technology_shares=marginal_mix,
    )

    assert fossil["amount"] == 10.0
    assert len(consumer["exchanges"]) == 2
