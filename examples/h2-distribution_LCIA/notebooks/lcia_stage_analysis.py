"""Life-cycle-stage contribution helpers for the European hydrogen-market notebook."""

import sys
import textwrap
from collections import defaultdict
from pathlib import Path

import bw2calc as bc
import bw2data as bd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# The notebook helper contains calculations only. All semantic names and plot
# families come from the single canonical mapping module in the parent folder.
ANALYSIS_DIR = Path(__file__).resolve().parent.parent
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

from LCIA_mapping_h2 import (
    CONVERSION_NAMES,
    DIRECT_EMISSION_TYPES,
    FAMILY_STYLES,
    method_plot_label,
    LEAKAGE_COLORS,
    LEAKAGE_CONTRIBUTION_TYPES,
    PIPELINE_TRANSPORT_ACTIVITY_NAME,
    PROCESS_HATCH,
    PRODUCTION_TECHNOLOGY_COLORS,
    SHARED_DISTRIBUTION_FAMILY,
)
from LCIA_mapping_h2 import (
    classify_market_branch as _classify_market_branch,
)  # noqa: E402
from LCIA_mapping_h2 import (
    classify_production_input as _classify_production_input,
)
from LCIA_mapping_h2 import distribution_family
from LCIA_mapping_h2 import is_hydrogen_market as _is_hydrogen_market
from LCIA_mapping_h2 import normalized as _normalized


def _reference_output_amount(activity):
    production = [
        exc for exc in activity.production() if exc.input.key == activity.key
    ]
    if len(production) != 1:
        raise ValueError(
            f"Expected one reference production exchange for {activity.key}; found {len(production)}."
        )
    amount = float(production[0].get("amount", 0.0))
    if amount == 0:
        raise ZeroDivisionError(
            f"Reference production amount is zero for {activity.key}."
        )
    return amount


def _collect_market_branches(activity, demand_amount, path=(), visited=()):
    """Unwrap pass-through hydrogen markets and return direct production/distribution branches."""
    if activity.key in visited:
        raise RuntimeError(
            f"Hydrogen-market pass-through cycle detected at {activity.key}."
        )

    scale = demand_amount / _reference_output_amount(activity)
    current_path = (*path, activity.key)
    branches = []
    market_biosphere = []

    for exc in activity.technosphere():
        provider = exc.input
        provider_demand = scale * float(exc.get("amount", 0.0))
        if _is_hydrogen_market(provider):
            nested_branches, nested_biosphere = _collect_market_branches(
                provider,
                provider_demand,
                current_path,
                (*visited, activity.key),
            )
            branches.extend(nested_branches)
            market_biosphere.extend(nested_biosphere)
        else:
            branches.append(
                {
                    "provider": provider,
                    "demand amount": provider_demand,
                    "market path": current_path,
                }
            )

    for exc in activity.biosphere():
        market_biosphere.append(
            {
                "exchange": exc,
                "scaled amount": scale * float(exc.get("amount", 0.0)),
                "market path": current_path,
            }
        )

    return branches, market_biosphere


def _pipeline_conversion_inputs(activity, demand_amount):
    """Return inputs that provide compression within pipeline distribution."""
    if _normalized(activity.get("name")) != PIPELINE_TRANSPORT_ACTIVITY_NAME:
        return []

    scale = demand_amount / _reference_output_amount(activity)
    inputs = []
    for exc in activity.technosphere():
        provider = exc.input
        exchange_name = _normalized(exc.get("name") or provider.get("name"))
        if exchange_name in CONVERSION_NAMES:
            inputs.append(
                {
                    "provider": provider,
                    "demand amount": scale * float(exc.get("amount", 0.0)),
                    "component": CONVERSION_NAMES[exchange_name],
                }
            )
    return inputs


def _method_cf_lookup(method):
    return {
        int(flow_id): float(cf) for flow_id, cf in bd.Method(method).load()
    }


def _direct_biosphere_rows(
    activity, demand_amount, cf_lookup, classify_transport_leakage=False
):
    scale = demand_amount / _reference_output_amount(activity)
    rows = []
    for exc in activity.biosphere():
        flow = exc.input
        flow_name = str(flow.get("name", ""))
        scaled_amount = scale * float(exc.get("amount", 0.0))
        if (
            classify_transport_leakage
            and flow_name.lower() in DIRECT_EMISSION_TYPES
        ):
            contribution_type = DIRECT_EMISSION_TYPES[flow_name.lower()]
        else:
            contribution_type = "Other direct emissions"
        rows.append(
            {
                "flow": flow_name,
                "flow key": flow.key,
                "flow unit": flow.get("unit", ""),
                "physical amount": scaled_amount,
                "contribution type": contribution_type,
                "score": scaled_amount * cf_lookup.get(int(flow.id), 0.0),
            }
        )
    return rows


class _DemandScorer:
    """Reuse one Brightway matrix factorization for many branch demands."""

    def __init__(self, seed_activity, method):
        self.lca = bc.LCA({seed_activity: 1.0}, method)
        self.lca.lci()
        self.lca.lcia()
        self.cache = {}

    def unit_score(self, activity):
        if activity.key not in self.cache:
            self.lca.redo_lcia({int(activity.id): 1.0})
            self.cache[activity.key] = float(self.lca.score)
        return self.cache[activity.key]

    def score(self, activity, amount):
        return float(amount) * self.unit_score(activity)


def _append_score_fields(row, total_score):
    row["share of market (%)"] = (
        100.0 * row["score"] / total_score if total_score != 0 else np.nan
    )
    return row


def _distribution_color_family(process):
    """Return the route palette for a distribution process or its leakage."""
    base_process = str(process).split(" — ", maxsplit=1)[-1]
    # Aggregated distribution rows have no underlying route. Keep them in the
    # explicitly configured shared-distribution family.
    if base_process in {"Hydrogen distribution", "distribution", "market"}:
        return SHARED_DISTRIBUTION_FAMILY
    return distribution_family(process)


def _color_map_by_family(items, family_by_item):
    """Assign a distinct shade to each item within its semantic color family."""
    ordered_items = list(dict.fromkeys(items))
    colors = {}
    for family, style in FAMILY_STYLES.items():
        family_items = [
            item for item in ordered_items if family_by_item(item) == family
        ]
        if not family_items:
            continue
        # Avoid the almost-white ends of sequential maps so every bar remains
        # readable.
        low, high = (0.38, 0.82)
        positions = np.linspace(low, high, len(family_items))
        cmap = plt.get_cmap(style["cmap"])
        colors.update(
            {
                item: cmap(position)
                for item, position in zip(family_items, positions)
            }
        )
    return colors


def stage_layer1_color_map(layer1_df):
    """Use fixed technology colors and route colors for distribution."""
    component_groups = (
        layer1_df[["component", "layer 1 group"]]
        .drop_duplicates()
        .set_index("component")["layer 1 group"]
        .to_dict()
    )

    production = [
        component for component, group in component_groups.items()
        if group == "Production technology"
    ]
    missing = sorted(set(production) - PRODUCTION_TECHNOLOGY_COLORS.keys())
    if missing:
        raise ValueError(
            "Add production technology colors to "
            f"LCIA_mapping_h2.PRODUCTION_TECHNOLOGY_COLORS: {missing}"
        )
    distribution = [item for item in component_groups if item not in production]
    colors = _color_map_by_family(distribution, _distribution_color_family)
    colors.update({item: PRODUCTION_TECHNOLOGY_COLORS[item] for item in production})
    return colors


def distribution_process_color_map(processes):
    """Color transport, conversion, reconversion, and leakage by route."""
    return _color_map_by_family(processes, _distribution_color_family)


def stage_layer1_hatch_map(layer1_df):
    """Map Layer-1 components to PROCESS_HATCH, including H2 leakage."""
    styles = (
        layer1_df[["component", "layer 1 group", "contribution type"]]
        .drop_duplicates()
        .set_index("component")
        .to_dict("index")
    )
    return {
        component: PROCESS_HATCH[
            (
                "Hydrogen leakage"
                if row["contribution type"] == "Hydrogen leakage"
                else (
                    "Production"
                    if row["layer 1 group"] == "Production technology"
                    else "Distribution"
                )
            )
        ]
        for component, row in styles.items()
    }


def distribution_process_hatch_map(distribution_df):
    """Map first-tier processes to PROCESS_HATCH, including H2 leakage."""
    styles = (
        distribution_df[["process", "substage", "contribution type"]]
        .drop_duplicates()
        .set_index("process")
        .to_dict("index")
    )
    return {
        process: PROCESS_HATCH[
            (
                "Hydrogen leakage"
                if row["contribution type"] == "Hydrogen leakage"
                else (
                    row["substage"]
                    if row["substage"] in PROCESS_HATCH
                    else "Distribution"
                )
            )
        ]
        for process, row in styles.items()
    }


def analyze_hydrogen_life_cycle_stages(
    selected,
    market_order,
    method,
    functional_unit,
    scores_df,
    impact_category,
    unit,
    reconciliation_rtol=1e-5,
):
    """Build Layer 1 and Layer 2 contribution tables for one LCIA method."""
    if reconciliation_rtol <= 0:
        raise ValueError("reconciliation_rtol must be positive.")
    scorer = _DemandScorer(selected[market_order[0]], method)
    cf_lookup = _method_cf_lookup(method)
    score_lookup = (
        scores_df[scores_df["method"].isin([method])]
        .set_index("market")["score per kg H2"]
        .to_dict()
    )

    layer1_rows = []
    production_input_rows = []
    distribution_rows = []
    audit_rows = []

    for market_label in market_order:
        market = selected[market_label]
        market_total = float(score_lookup[market_label])
        branches, market_biosphere = _collect_market_branches(
            market, functional_unit
        )

        distribution_nonleakage = 0.0
        distribution_leakage = defaultdict(float)
        distribution_leakage_amount = defaultdict(float)
        distribution_transport_components = []

        for branch in branches:
            provider = branch["provider"]
            demand_amount = branch["demand amount"]
            stage, substage, short_name, rule = _classify_market_branch(
                provider
            )
            total_branch_score = scorer.score(provider, demand_amount)
            direct_rows = _direct_biosphere_rows(
                provider,
                demand_amount,
                cf_lookup,
                classify_transport_leakage=stage == "Distribution",
            )
            leakage_score = sum(
                row["score"]
                for row in direct_rows
                if row["contribution type"] in LEAKAGE_CONTRIBUTION_TYPES
            )

            audit_rows.append(
                {
                    "market": market_label,
                    "market location": market.get("location"),
                    "provider": provider.get("name"),
                    "provider product": provider.get("reference product"),
                    "provider unit": provider.get("unit"),
                    "provider location": provider.get("location"),
                    "provider key": provider.key,
                    "demand amount": demand_amount,
                    "stage": stage,
                    "substage": substage,
                    "component": short_name,
                    "classification rule": rule,
                }
            )

            if stage == "Production":
                layer1_rows.append(
                    _append_score_fields(
                        {
                            "market": market_label,
                            "layer 1 group": "Production technology",
                            "component": short_name,
                            "contribution type": "Technology excluding leakage",
                            "score": total_branch_score - leakage_score,
                        },
                        market_total,
                    )
                )

                scale = demand_amount / _reference_output_amount(provider)
                for exc in provider.technosphere():
                    input_provider = exc.input
                    input_demand = scale * float(exc.get("amount", 0.0))
                    production_input_rows.append(
                        _append_score_fields(
                            {
                                "market": market_label,
                                "technology": short_name,
                                "input group": _classify_production_input(
                                    input_provider
                                ),
                                "input process": input_provider.get("name"),
                                "input location": input_provider.get(
                                    "location"
                                ),
                                "input key": input_provider.key,
                                "contribution type": "Upstream input",
                                "score": scorer.score(
                                    input_provider, input_demand
                                ),
                            },
                            market_total,
                        )
                    )

                for row in direct_rows:
                    production_input_rows.append(
                        _append_score_fields(
                            {
                                "market": market_label,
                                "technology": short_name,
                                "input group": row["contribution type"],
                                "input process": row["flow"],
                                "input location": "biosphere",
                                "input key": row["flow key"],
                                "contribution type": row["contribution type"],
                                "physical amount": row["physical amount"],
                                "physical unit": row["flow unit"],
                                "score": row["score"],
                            },
                            market_total,
                        )
                    )

            else:
                if substage == "Transport":
                    distribution_transport_components.append(short_name)
                conversion_inputs = _pipeline_conversion_inputs(
                    provider, demand_amount
                )
                conversion_score = sum(
                    scorer.score(item["provider"], item["demand amount"])
                    for item in conversion_inputs
                )
                process_nonleakage = (
                    total_branch_score - leakage_score - conversion_score
                )
                distribution_nonleakage += process_nonleakage
                distribution_nonleakage += conversion_score
                distribution_rows.append(
                    _append_score_fields(
                        {
                            "market": market_label,
                            "substage": substage,
                            "process": short_name,
                            "process key": provider.key,
                            "contribution type": "Process excluding leakage",
                            "score": process_nonleakage,
                        },
                        market_total,
                    )
                )
                for item in conversion_inputs:
                    input_provider = item["provider"]
                    input_score = scorer.score(
                        input_provider, item["demand amount"]
                    )
                    distribution_rows.append(
                        _append_score_fields(
                            {
                                "market": market_label,
                                "substage": "Conversion",
                                "process": item["component"],
                                "process key": input_provider.key,
                                "contribution type": "Process excluding leakage",
                                "score": input_score,
                            },
                            market_total,
                        )
                    )
                    audit_rows.append(
                        {
                            "market": market_label,
                            "market location": market.get("location"),
                            "provider": input_provider.get("name"),
                            "provider product": input_provider.get(
                                "reference product"
                            ),
                            "provider unit": input_provider.get("unit"),
                            "provider location": input_provider.get(
                                "location"
                            ),
                            "provider key": input_provider.key,
                            "demand amount": item["demand amount"],
                            "stage": "Distribution",
                            "substage": "Conversion",
                            "component": item["component"],
                            "classification rule": "pipeline compression input",
                        }
                    )
                for leakage_type in LEAKAGE_CONTRIBUTION_TYPES:
                    leakage = [
                        r
                        for r in direct_rows
                        if r["contribution type"] == leakage_type
                    ]
                    if leakage:
                        leakage_value = sum(r["score"] for r in leakage)
                        physical_amount = sum(
                            r["physical amount"] for r in leakage
                        )
                        distribution_leakage[leakage_type] += leakage_value
                        distribution_leakage_amount[
                            leakage_type
                        ] += physical_amount
                        distribution_rows.append(
                            _append_score_fields(
                                {
                                    "market": market_label,
                                    "substage": substage,
                                    "process": f"{leakage_type} — {short_name}",
                                    "process key": provider.key,
                                    "contribution type": leakage_type,
                                    "physical amount": physical_amount,
                                    "physical unit": leakage[0]["flow unit"],
                                    "score": leakage_value,
                                },
                                market_total,
                            )
                        )

        # Any biosphere exchange on an unwrapped market is distribution leakage when it is H2/NH3.
        for item in market_biosphere:
            flow = item["exchange"].input
            flow_name = str(flow.get("name", ""))
            if flow_name.lower() not in DIRECT_EMISSION_TYPES:
                raise ValueError(
                    f"Unclassified direct market emission {flow_name!r} in {market_label}."
                )
            leakage_type = DIRECT_EMISSION_TYPES[flow_name.lower()]
            leakage_score = item["scaled amount"] * cf_lookup.get(
                int(flow.id), 0.0
            )
            distribution_leakage[leakage_type] += leakage_score
            distribution_leakage_amount[leakage_type] += item["scaled amount"]
            route_components = list(
                dict.fromkeys(distribution_transport_components)
            )
            route_component = (
                route_components[0] if len(route_components) == 1 else "market"
            )
            distribution_rows.append(
                _append_score_fields(
                    {
                        "market": market_label,
                        "substage": "Transport",
                        "process": f"{leakage_type} — {route_component}",
                        "process key": market.key,
                        "contribution type": leakage_type,
                        "physical amount": item["scaled amount"],
                        "physical unit": flow.get("unit", ""),
                        "score": leakage_score,
                    },
                    market_total,
                )
            )

        layer1_rows.append(
            _append_score_fields(
                {
                    "market": market_label,
                    "layer 1 group": "Hydrogen distribution",
                    "component": "Hydrogen distribution",
                    "contribution type": "Distribution excluding leakage",
                    "score": distribution_nonleakage,
                },
                market_total,
            )
        )
        for leakage_type, leakage_score in distribution_leakage.items():
            layer1_rows.append(
                _append_score_fields(
                    {
                        "market": market_label,
                        "layer 1 group": "Hydrogen distribution",
                        "component": f"{leakage_type} — distribution",
                        "contribution type": leakage_type,
                        "physical amount": distribution_leakage_amount[
                            leakage_type
                        ],
                        "physical unit": "kilogram",
                        "score": leakage_score,
                    },
                    market_total,
                )
            )

    layer1_df = pd.DataFrame(layer1_rows)
    production_inputs_df = pd.DataFrame(production_input_rows)
    distribution_processes_df = pd.DataFrame(distribution_rows)
    classification_audit_df = pd.DataFrame(audit_rows)

    # Aggregate direct inputs into the requested main input groups.
    production_input_groups_df = production_inputs_df.groupby(
        ["market", "technology", "input group", "contribution type"],
        as_index=False,
        dropna=False,
    )["score"].sum()
    production_input_groups_df = production_input_groups_df.merge(
        scores_df[scores_df["method"].isin([method])][
            ["market", "score per kg H2"]
        ],
        on="market",
        validate="many_to_one",
    )
    production_input_groups_df["share of market (%)"] = np.where(
        production_input_groups_df["score per kg H2"] != 0,
        100.0
        * production_input_groups_df["score"]
        / production_input_groups_df["score per kg H2"],
        np.nan,
    )

    reconciliation_rows = []
    for market_label in market_order:
        total = float(score_lookup[market_label])
        layer1_sum = float(
            layer1_df.loc[layer1_df["market"] == market_label, "score"].sum()
        )
        production_sum = float(
            production_input_groups_df.loc[
                production_input_groups_df["market"] == market_label, "score"
            ].sum()
        )
        distribution_sum = float(
            distribution_processes_df.loc[
                distribution_processes_df["market"] == market_label, "score"
            ].sum()
        )
        layer2_sum = production_sum + distribution_sum
        reconciliation_rows.append(
            {
                "market": market_label,
                "method": method,
                "impact category": impact_category,
                "unit": unit,
                "total score": total,
                "Layer 1 reconstructed score": layer1_sum,
                "Layer 1 difference": layer1_sum - total,
                "Layer 2 reconstructed score": layer2_sum,
                "Layer 2 difference": layer2_sum - total,
            }
        )

    reconciliation_df = pd.DataFrame(reconciliation_rows)
    tolerance = reconciliation_rtol * np.maximum(
        1.0, reconciliation_df["total score"].abs()
    )
    if not (reconciliation_df["Layer 1 difference"].abs() <= tolerance).all():
        raise AssertionError(
            "Layer 1 stage contributions do not reconstruct one or more LCIA totals."
        )
    if not (reconciliation_df["Layer 2 difference"].abs() <= tolerance).all():
        raise AssertionError(
            "Layer 2 stage contributions do not reconstruct one or more LCIA totals."
        )

    for frame in (
        layer1_df,
        production_inputs_df,
        production_input_groups_df,
        distribution_processes_df,
    ):
        frame["method"] = [method] * len(frame)
        frame["impact category"] = impact_category
        frame["unit"] = unit

    return {
        "layer1": layer1_df,
        "production inputs detailed": production_inputs_df,
        "production input groups": production_input_groups_df,
        "distribution processes": distribution_processes_df,
        "classification audit": classification_audit_df,
        "reconciliation": reconciliation_df,
    }


def _plot_signed_stacks(
    ax,
    data,
    markets,
    component_column,
    color_map,
    value_column,
    xlabel,
    hatch_map=None,
    label_threshold=None,
    value_format="{:.2e}",
    show_values=True,
    value_fontsize=8,
):
    y = np.arange(len(markets))
    positive_left = np.zeros(len(markets))
    negative_left = np.zeros(len(markets))
    maximum = float(data[value_column].abs().max()) if not data.empty else 0.0
    threshold = (
        (0.03 * maximum if maximum > 0 else np.inf)
        if label_threshold is None
        else label_threshold
    )
    for component in data[component_column].drop_duplicates():
        values = (
            data[data[component_column] == component]
            .groupby("market")[value_column]
            .sum()
            .reindex(markets, fill_value=0.0)
            .to_numpy(dtype=float)
        )
        left = np.where(values >= 0, positive_left, negative_left)
        bars = ax.barh(
            y,
            values,
            left=left,
            color=color_map[component],
            hatch=(hatch_map or {}).get(component, ""),
            edgecolor="white",
            linewidth=0.6,
            label=component,
        )
        for bar, value, start in zip(bars, values, left):
            if show_values and abs(value) >= threshold:
                ax.text(
                    start + value / 2,
                    bar.get_y() + bar.get_height() / 2,
                    value_format.format(value),
                    ha="center",
                    va="center",
                    fontsize=value_fontsize,
                )
        positive_left += np.where(values >= 0, values, 0.0)
        negative_left += np.where(values < 0, values, 0.0)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y, markets)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)


def _stage_plot_title(title_context, title):
    """Include scenario metadata when supplied by the calling notebook."""
    return f"{title}\n{title_context}" if title_context else title


def _presentation_stage_layout(fig, ax, title, title_context, legend_title):
    """Keep the chart, wrapped legend, and headings inside a 16:9 slide."""
    ax.tick_params(axis="both", labelsize=16)
    ax.xaxis.label.set_size(16)
    ax.xaxis.labelpad = 14
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    labels = [textwrap.fill(label, width=36, break_long_words=False,
                           break_on_hyphens=False) for label in labels]
    fig.legend(handles, labels, title=legend_title,
               bbox_to_anchor=(0.67, 0.51), loc="center left",
               frameon=False, fontsize=14, title_fontsize=16,
               labelspacing=0.65, handlelength=2.0)
    fig.suptitle(_stage_plot_title(title_context, title),
                 fontsize=22, y=0.97, linespacing=1.35)
    fig.subplots_adjust(left=0.075, right=0.65, bottom=0.16, top=0.83)
    # Set the family on all text, including ticks, bar values, and legend entries.
    from matplotlib.text import Text
    for text in fig.findobj(match=Text):
        text.set_fontfamily("DejaVu Sans")



def plot_stage_layer1(layer1_df, market_order, label_threshold=3.0, *, title_context=""):
    method_label = method_plot_label(tuple(layer1_df["method"].iloc[0]))
    colors = stage_layer1_color_map(layer1_df)
    hatches = stage_layer1_hatch_map(layer1_df)

    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    _plot_signed_stacks(
        ax,
        layer1_df,
        market_order,
        "component",
        colors,
        value_column="share of market (%)",
        xlabel=f"Contribution to total {method_label} score (%)",
        hatch_map=hatches,
        label_threshold=label_threshold,
        value_format="{:.1f}%",
        value_fontsize=12,
    )
    _presentation_stage_layout(
        fig, ax, "Hydrogen production technologies and distribution",
        title_context, "Layer 1 component",
    )
    plt.show()


def plot_production_layer2(
    production_groups_df, market_order, label_threshold=None, *, title_context=""
):
    method_label = method_plot_label(tuple(production_groups_df["method"].iloc[0]))
    technologies = (
        production_groups_df["technology"].drop_duplicates().tolist()
    )
    input_groups = (
        production_groups_df["input group"].drop_duplicates().tolist()
    )
    palette = plt.get_cmap("tab20")
    colors = {
        group: palette(i % palette.N) for i, group in enumerate(input_groups)
    }
    colors.update(LEAKAGE_COLORS)
    # Link only direct H2 leakage to its existing canonical hatch.
    hatches = {
        group: PROCESS_HATCH[
            "Hydrogen leakage" if group == "Hydrogen leakage" else "Production"
        ]
        for group in input_groups
    }

    fig, axes = plt.subplots(
        len(technologies),
        1,
        figsize=(
            16,
            max(5, len(technologies) * (0.6 * len(market_order) + 1.8)),
        ),
        squeeze=False,
    )
    unit = production_groups_df["unit"].iloc[0]
    for ax, technology in zip(axes.ravel(), technologies):
        subset = production_groups_df[
            production_groups_df["technology"] == technology
        ]
        _plot_signed_stacks(
            ax,
            subset,
            market_order,
            "input group",
            colors,
            value_column="score",
            xlabel=f"{method_label} contribution ({unit} / kg H2)",
            hatch_map=hatches,
            label_threshold=label_threshold,
        )
        ax.set_title(_stage_plot_title(title_context, technology), loc="left")
    handles = {}
    for ax in axes.ravel():
        for handle, label in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(label, handle)
    fig.legend(
        handles.values(),
        handles.keys(),
        title="Main production input",
        bbox_to_anchor=(1.01, 0.5),
        loc="center left",
        frameon=False,
    )
    fig.suptitle(
        _stage_plot_title(title_context, "Layer 2 — main inputs to each hydrogen production technology"), y=1.002
    )
    fig.tight_layout(rect=(0, 0, 0.84, 1))
    plt.show()


def plot_distribution_layer2(
    distribution_df, market_order, label_threshold=None, *, title_context=""
):
    method_label = method_plot_label(tuple(distribution_df["method"].iloc[0]))
    processes = distribution_df["process"].drop_duplicates().tolist()
    colors = distribution_process_color_map(processes)
    hatches = distribution_process_hatch_map(distribution_df)

    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    unit = distribution_df["unit"].iloc[0]
    _plot_signed_stacks(
        ax,
        distribution_df,
        market_order,
        "process",
        colors,
        value_column="score",
        xlabel=f"{method_label} contribution ({unit} / kg H2)",
        hatch_map=hatches,
        label_threshold=label_threshold,
        show_values=False,
    )
    _presentation_stage_layout(
        fig, ax, "Transport, conversion, and reconversion by market",
        title_context, "Distribution process",
    )
    plt.show()
