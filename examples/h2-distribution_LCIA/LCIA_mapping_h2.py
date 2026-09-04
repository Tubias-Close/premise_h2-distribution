"""Canonical semantic mappings for the hydrogen-distribution LCIA examples.

All notebooks and analysis modules import activity names, LCIA methods, scenario
labels, contribution groups, and visual identities from this file. Operational
settings such as output paths and reconciliation tolerances remain in
``config.py``.

Keep display names stable: they are written to audit tables and are also used as
exact keys by the contribution-analysis plotting helpers.
"""

# Brightway databases included in the multi-IAM comparison. Keeping the IAM
# metadata beside each database makes the exported scenario audit reproducible.
DATABASES = [
    {
        "database": "ecoinvent-3.12-cutoff_remind-SSP1-PkBudg650_2030_08_full",
        "iam_model": "remind",
        "scenario": "SSP1-PkBudg650",
        "year": 2030,
    },
    {
        "database": "ecoinvent-3.12-cutoff_remind-SSP1-PkBudg650_2040_08_full",
        "iam_model": "remind",
        "scenario": "SSP1-PkBudg650",
        "year": 2040,
    },
    {
        "database": "ecoinvent-3.12-cutoff_remind-SSP1-PkBudg650_2050_08_full",
        "iam_model": "remind",
        "scenario": "SSP1-PkBudg650",
        "year": 2050,
    },
    {
        "database": "ecoinvent-3.12-cutoff_remind-SSP2-PkBudg1000_2030_08_full",
        "iam_model": "remind",
        "scenario": "SSP2-PkBudg1000",
        "year": 2030,
    },
    {
        "database": "ecoinvent-3.12-cutoff_remind-SSP2-PkBudg1000_2040_08_full",
        "iam_model": "remind",
        "scenario": "SSP2-PkBudg1000",
        "year": 2040,
    },
    {
        "database": "ecoinvent-3.12-cutoff_remind-SSP2-PkBudg1000_2050_08_full",
        "iam_model": "remind",
        "scenario": "SSP2-PkBudg1000",
        "year": 2050,
    },
    {
        "database": "ecoinvent-3.12-cutoff_image-SSP2-VLHO_2030_08_full",
        "iam_model": "image",
        "scenario": "SSP2-VLHO",
        "year": 2030,
    },
    {
        "database": "ecoinvent-3.12-cutoff_image-SSP2-VLHO_2040_08_full",
        "iam_model": "image",
        "scenario": "SSP2-VLHO",
        "year": 2040,
    },
    {
        "database": "ecoinvent-3.12-cutoff_image-SSP2-VLHO_2050_08_full",
        "iam_model": "image",
        "scenario": "SSP2-VLHO",
        "year": 2050,
    },
    {
        "database": "ecoinvent-3.12-cutoff_message-SSP2-L_2030_08_full",
        "iam_model": "message",
        "scenario": "SSP2-L",
        "year": 2030,
    },
    {
        "database": "ecoinvent-3.12-cutoff_message-SSP2-L_2040_08_full",
        "iam_model": "message",
        "scenario": "SSP2-L",
        "year": 2040,
    },
    {
        "database": "ecoinvent-3.12-cutoff_message-SSP2-L_2050_08_full",
        "iam_model": "message",
        "scenario": "SSP2-L",
        "year": 2050,
    },
]

MODEL_LABELS = {
    "image": "IMAGE",
    "message": "MESSAGE",
    "remind": "REMIND",
}
SCENARIO_LABELS = {
    ("remind", "SSP1-PkBudg650"): "REMIND - SSP1-PkBudg650",
    ("remind", "SSP2-PkBudg1000"): "REMIND - SSP2-PkBudg1000",
    ("image", "SSP2-VLHO"): "IMAGE - SSP2-VLHO",
    ("message", "SSP2-L"): "MESSAGE - SSP2-L",
}
WARMING_MAP = {
    ("remind", "SSP1-PkBudg650"): "<1.5 °C",
    ("remind", "SSP2-PkBudg1000"): "<2.0 °C",
    ("image", "SSP2-VLHO"): "<2.0 °C",
    ("message", "SSP2-L"): "<2.0 °C",
}

# Exact LCIA method tuples. These are the only methods calculated by the
# notebooks; adding or removing a method here changes every LCIA workflow.
PREMISE_GWP_METHOD = ("IPCC 2021", "climate change", "GWP 100a, incl. H")
METHOD_LABELS = {
    (
        "EF v3.1",
        "acidification",
        "accumulated exceedance (AE)",
    ): "Acidification",
    PREMISE_GWP_METHOD: "Climate change — GWP100 incl. H₂",
    (
        "EF v3.1",
        "ecotoxicity: freshwater",
        "comparative toxic unit for ecosystems (CTUe)",
    ): "Ecotoxicity — freshwater",
    (
        "EF v3.1",
        "energy resources: non-renewable",
        "abiotic depletion potential (ADP): fossil fuels",
    ): "Resource use — energy carriers",
    (
        "EF v3.1",
        "eutrophication: freshwater",
        "fraction of nutrients reaching freshwater end compartment (P)",
    ): "Eutrophication — freshwater",
    (
        "EF v3.1",
        "eutrophication: marine",
        "fraction of nutrients reaching marine end compartment (N)",
    ): "Eutrophication — marine",
    (
        "EF v3.1",
        "human toxicity: carcinogenic",
        "comparative toxic unit for human (CTUh)",
    ): "Human toxicity — cancer",
    (
        "EF v3.1",
        "human toxicity: non-carcinogenic",
        "comparative toxic unit for human (CTUh)",
    ): "Human toxicity — non-cancer",
    (
        "EF v3.1",
        "material resources: metals/minerals",
        "abiotic depletion potential (ADP): elements (ultimate reserves)",
    ): "Resource use — minerals and metals",
    (
        "EF v3.1",
        "particulate matter formation",
        "impact on human health",
    ): "Particulate matter",
}
SELECTED_METHODS = tuple(METHOD_LABELS)
CONTRIBUTION_METHODS = (PREMISE_GWP_METHOD,)

HYDROGEN_PRODUCT = "hydrogen, gaseous, low pressure"
PIPELINE_TRANSPORT_ACTIVITY_NAME = "hydrogen supply, distributed by pipeline"
DIRECT_EMISSION_TYPES = {
    "hydrogen": "Hydrogen leakage",
    "ammonia": "Ammonia leakage",
}
LEAKAGE_CONTRIBUTION_TYPES = tuple(DIRECT_EMISSION_TYPES.values())
LEAKAGE_COLORS = {
    "Hydrogen leakage": "#d62728",
    "Ammonia leakage": "#9467bd",
}

# Exact Brightway activity names and their canonical reporting names. The LH2
# tanker is intentionally not mapped because it is outside this LCIA scope.
TRANSPORT_NAMES = {
    "transport, hydrogen, gaseous, lorry, unspecified": "Gaseous H2 truck",
    "transport, hydrogen, liquid, lorry, unspecified": "Liquid H2 truck",
    PIPELINE_TRANSPORT_ACTIVITY_NAME: "Pipeline distribution",
    "transport, freight, sea, tanker for liquefied ammonia, ammonia and mdo": (
        "Ammonia tanker, powered by NH3 and MDO"
    ),
}
CONVERSION_NAMES = {
    "gaseous hydrogen production": "Compression (truck)",
    "liquid hydrogen production": "Liquefaction",
    "liquid ammonia production": "Ammonia production (HB)",
    "market group for electricity, low voltage": "Compression (pipeline)",
    "compressor assembly for transmission hydrogen pipeline": (
        "Compression (pipeline)"
    ),
}
RECONVERSION_NAMES = {
    "ammonia cracking": "Ammonia cracking",
    "liquid hydrogen regasification": "Liquid hydrogen regasification",
}

# Exact process families used for route-level contribution reporting.
GH2_PIPE_PROCESSES = {
    "Pipeline distribution",
    "Compression (pipeline)",
}
GH2_TRUCK_PROCESSES = {
    "Gaseous H2 truck",
    "Compression (truck)",
}
LH2_TRUCK_PROCESSES = {
    "Liquid H2 truck",
    "Liquefaction",
    "Liquid hydrogen regasification",
}
NH3_TANKER_PROCESSES = {
    "Ammonia tanker, powered by NH3 and MDO",
    "Ammonia production (HB)",
    "Ammonia cracking",
}

# Plot-oriented matching also handles leakage labels, which prefix the
# canonical process name with ``Hydrogen leakage —`` or ``Ammonia leakage —``.
DISTRIBUTION_FAMILY_RULES = {
    "Compressed gas truck": tuple(GH2_TRUCK_PROCESSES),
    "Pipeline": tuple(GH2_PIPE_PROCESSES),
    "Liquid hydrogen": tuple(LH2_TRUCK_PROCESSES),
    "Ammonia shipping": (*NH3_TANKER_PROCESSES, "Ammonia leakage"),
    "Shared distribution": (
        "Hydrogen leakage — distribution",
        "Hydrogen leakage - distribution",
    ),
}

# Production technologies deliberately use grey tones so distribution routes
# remain visually prominent. Each route receives a distinct color family/hatch.
PRODUCTION_FAMILY = "Hydrogen production"
SHARED_DISTRIBUTION_FAMILY = "Shared distribution"
FAMILY_STYLES = {
    PRODUCTION_FAMILY: {"cmap": "Greys", "hatch": ""},
    "Compressed gas truck": {"cmap": "Blues", "hatch": "///"},
    "Pipeline": {"cmap": "Greens", "hatch": "\\\\"},
    "Liquid hydrogen": {"cmap": "Oranges", "hatch": "xx"},
    "Ammonia shipping": {"cmap": "Purples", "hatch": "oo"},
    SHARED_DISTRIBUTION_FAMILY: {"cmap": "Reds", "hatch": ".."},
}
FAMILY_ORDER = tuple(FAMILY_STYLES)

PROCESS_COLORS = {
    "GH2 truck": "#39e0c4",
    "LH2 truck": "#1832f5",
    "GH2 pipeline": "#0091ff",
    "NH3 ship": "#7ab648",
}
# Route-level plots use the same colors under the family names returned by
# ``distribution_family``.
ROUTE_COLORS = {
    "Compressed gas truck": PROCESS_COLORS["GH2 truck"],
    "Pipeline": PROCESS_COLORS["GH2 pipeline"],
    "Liquid hydrogen": PROCESS_COLORS["LH2 truck"],
    "Ammonia shipping": PROCESS_COLORS["NH3 ship"],
    SHARED_DISTRIBUTION_FAMILY: "#D62728",
}
AMMONIA_CRACKING_COMPONENT = RECONVERSION_NAMES["ammonia cracking"]
PROCESS_HATCH = {
    "Production": "",
    "Hydrogen leakage": "ooo",
    "Conversion": "//",
    "Reconversion": "\\\\",
    "Distribution": "xxx",
}
YEAR_COLORS = {
    2030: "#c8d9ef",
    2040: "#6baed6",
    2050: "#ec006d",
}
WARMING_COLORS = {
    "<1.5 °C": "#0B3D0B",
    "<2.0 °C": "#1B5E20",
    "2.0-2.5 °C": "#FF9800",
    ">2.5 °C": "#8B0000",
}


def normalized(value):
    """Return a whitespace-normalized, lowercase representation."""
    return " ".join(str(value or "").replace(" ,", ",").split()).lower()


def is_hydrogen_market(activity):
    """Return whether an activity is a low-pressure gaseous H2 market."""
    return (
        normalized(activity.get("name")).startswith(
            "market for hydrogen, gaseous, low pressure"
        )
        and normalized(activity.get("reference product")) == HYDROGEN_PRODUCT
    )


def short_production_name(name):
    """Return the canonical reporting label for an H2 production activity."""
    text = normalized(name)
    if "pem electrolysis" in text:
        return "PEM electrolysis"
    if "alkaline electrolysis" in text:
        return "Alkaline electrolysis"
    if "woody biomass" in text and "with ccs" in text:
        return "Biomass gasification with CCS"
    if "woody biomass" in text:
        return "Biomass gasification"
    if "coal gasification" in text and "with ccs" in text:
        return "Coal gasification with CCS"
    if "steam methane reforming" in text and "with ccs" in text:
        return "Steam methane reforming with CCS"
    if "steam methane reforming" in text:
        return "Steam methane reforming"
    return name


def classify_market_branch(provider):
    """Return stage, substage, display name, and classification evidence."""
    name = normalized(provider.get("name"))
    if name in TRANSPORT_NAMES:
        return (
            "Distribution",
            "Transport",
            TRANSPORT_NAMES[name],
            "exact transport activity",
        )
    if name in CONVERSION_NAMES:
        return (
            "Distribution",
            "Conversion",
            CONVERSION_NAMES[name],
            "exact conversion activity",
        )
    if (
        name in RECONVERSION_NAMES
        or "ammonia cracking" in name
        or "regasification" in name
    ):
        return (
            "Distribution",
            "Reconversion",
            RECONVERSION_NAMES.get(name, provider.get("name")),
            "reconversion activity",
        )
    if name.startswith("hydrogen production"):
        return (
            "Production",
            "Production technology",
            short_production_name(provider.get("name")),
            "hydrogen production activity",
        )
    raise ValueError(
        "Unclassified direct hydrogen-market input: "
        f"{provider.get('name')} | {provider.get('reference product')} | "
        f"{provider.get('unit')} | {provider.key}"
    )


def classify_production_input(provider):
    """Group a production-technology input without hiding unknown materials."""
    name = normalized(provider.get("name"))
    product = normalized(provider.get("reference product"))
    unit = normalized(provider.get("unit"))
    text = f"{name} | {product}"
    if "electricity" in text:
        return "Electricity"
    if "heat" in text or "steam" in text:
        return "Heat"
    if "water" in text:
        return "Water"
    if "carbon dioxide, captured" in text or "carbon capture" in text:
        return "CO2 capture and storage"
    if any(term in text for term in ("wood", "biomass", "biomethane")):
        return "Biomass feedstock"
    if any(
        term in text
        for term in ("natural gas", "hard coal", "lignite", "petroleum", "coke")
    ):
        return "Fossil feedstock"
    if name.startswith("transport") or "transport," in product:
        return "Transport services"
    if name.startswith("treatment") or "waste" in product:
        return "Waste treatment"
    if unit in {"unit", "kilometer"} or any(
        term in text
        for term in ("construction", "factory", "plant", "electrolyzer", "pipeline")
    ):
        return "Infrastructure"
    return "Other raw materials"


def impact_category_label(method):
    """Return the stable analytical label used in tables and reconciliation."""
    if method == PREMISE_GWP_METHOD:
        return "climate change — GWP 100a, incl. H (premise_gwp)"
    return method[1]


# The configured hotspot order follows METHOD_LABELS insertion order. This
# keeps method selection and plotting order synchronized in one place.
SPECIFIC_IMPACT_CATEGORY_ORDER = tuple(
    impact_category_label(method) for method in SELECTED_METHODS
)


def distribution_family(process):
    """Return exactly one canonical route family for a distribution process."""
    text = normalized(process)
    matches = [
        family
        for family, patterns in DISTRIBUTION_FAMILY_RULES.items()
        if any(normalized(pattern) in text for pattern in patterns)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one distribution-family mapping for {process!r}; "
            f"matched {matches}. Update LCIA_mapping_h2.py."
        )
    return matches[0]
