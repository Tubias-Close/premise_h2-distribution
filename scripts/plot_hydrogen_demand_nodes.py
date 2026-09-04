"""Plot hydrogen demand per node and demand node counts from a change report.

By default, the script reads the newest workbook in
``dev/export/change reports`` and creates one line chart per scenario and demand
node type. Each chart includes all non-WORLD regions from 2025 onward:

* top panel: hydrogen used per demand node per year
* bottom panel: rounded-up number of demand nodes
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANGE_REPORT_DIR = PROJECT_ROOT / "dev" / "export" / "change reports"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dev" / "hydrogen_demand_node_charts"
START_YEAR = 2025
CHANGE_REPORT_SHEET = "Fuel"
HYDROGEN_REPORT_TYPE_COLUMN = (
    "Type of hydrogen sector-market implementation log entry"
)
CHANGE_REPORT_COLUMNS = {
    "IAM model name": "model",
    "Pathway name": "pathway",
    "Year": "year",
    "Region name": "region",
    (
        "End-use sector used for hydrogen demand nodes or sector-specific "
        "market relinking"
    ): "sector",
    "Hydrogen demand subsector represented by the demand node row": "subsector",
    "Type of demand node used for hydrogen logistics": "demand_node_type",
    (
        "Number of hydrogen demand nodes rounded up to the next integer"
    ): "demand_nodes_rounded_up",
    "Annual hydrogen demand per demand node": (
        "hydrogen_demand_t_per_node_per_year"
    ),
}

plt.rcParams.update(
    {
        "font.size": 14,
        "axes.titlesize": 19,
        "axes.labelsize": 16,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "legend.fontsize": 13,
        "lines.linewidth": 2.5,
    }
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create scenario-specific hydrogen demand-node charts from the Fuel "
            "sheet of a premise change report, excluding the WORLD region."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Input change-report workbook. By default, use the most recently "
            f"modified change_report *.xlsx in {CHANGE_REPORT_DIR}."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for PNG charts. Default: {DEFAULT_OUTPUT_DIR}",
    )
    return parser.parse_args()


def find_latest_change_report() -> Path:
    reports = list(CHANGE_REPORT_DIR.glob("change_report *.xlsx"))
    if not reports:
        raise FileNotFoundError(
            f"No change_report *.xlsx workbooks found in {CHANGE_REPORT_DIR}"
        )
    return max(reports, key=lambda path: path.stat().st_mtime)


def load_data(report_path: Path) -> pd.DataFrame:
    raw = pd.read_excel(report_path, sheet_name=CHANGE_REPORT_SHEET)

    required_columns = {
        HYDROGEN_REPORT_TYPE_COLUMN,
        *CHANGE_REPORT_COLUMNS,
    }
    missing_columns = required_columns.difference(raw.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns in {report_path}: {missing}")

    df = raw.loc[
        raw[HYDROGEN_REPORT_TYPE_COLUMN].eq("demand node"),
        list(CHANGE_REPORT_COLUMNS),
    ].rename(columns=CHANGE_REPORT_COLUMNS)

    if df.empty:
        raise ValueError(
            f"No hydrogen demand-node rows found in the {CHANGE_REPORT_SHEET!r} "
            f"sheet of {report_path}"
        )

    df = df[df["region"].astype(str).str.upper() != "WORLD"].copy()
    df = df.dropna(subset=["demand_node_type"])

    numeric_columns = [
        "year",
        "hydrogen_demand_t_per_node_per_year",
        "demand_nodes_rounded_up",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["model", "pathway", "year", "region", "demand_node_type"]
    )
    df["year"] = df["year"].astype(int)
    df = df[df["year"] >= START_YEAR]
    return df


def prepare_plot_data(df: pd.DataFrame) -> pd.DataFrame:
    """Sort values reported in the change report without recalculating them."""
    return df.sort_values(["demand_node_type", "region", "year"])


def safe_filename(value: str) -> str:
    clean = "".join(
        character.lower() if character.isalnum() else "_"
        for character in str(value).strip()
    )
    return "_".join(part for part in clean.split("_") if part)


DEMAND_NODE_LABELS = {
    "cement_plants": ("cement plant", "cement plants"),
    "chemical_plants": ("chemical plant", "chemical plants"),
    "fueling_stations": ("fueling station", "fueling stations"),
    "other_demand_nodes": ("other demand node", "other demand nodes"),
    "steel_plants": ("steel plant", "steel plants"),
}


def plot_demand_node_type(
    df: pd.DataFrame,
    demand_node_type: str,
    output_dir: Path,
    available_years: list[int],
    scenario_label: str,
) -> Path:
    subset = df[df["demand_node_type"] == demand_node_type]
    regions = sorted(subset["region"].unique())
    singular_label, plural_label = DEMAND_NODE_LABELS.get(
        demand_node_type,
        (
            str(demand_node_type).replace("_", " "),
            f"{str(demand_node_type).replace('_', ' ')}s",
        ),
    )

    fig, (ax_hydrogen, ax_nodes) = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(12, 9),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1.4]},
    )

    color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for index, region in enumerate(regions):
        region_data = subset[subset["region"] == region].sort_values("year")
        color = color_cycle[index % len(color_cycle)]

        ax_hydrogen.plot(
            region_data["year"],
            region_data["hydrogen_demand_t_per_node_per_year"],
            color=color,
            linewidth=2,
            marker="o",
            label=region,
        )
        ax_nodes.plot(
            region_data["year"],
            region_data["demand_nodes_rounded_up"],
            color=color,
            linewidth=2,
            marker="o",
            label=f"{region} demand nodes",
        )

    ax_hydrogen.set_title(
        f"Hydrogen demand per {singular_label} and number of "
        f"{plural_label} per region\n"
        f"Scenario: {scenario_label}",
        pad=16,
    )
    ax_hydrogen.set_ylabel(f"Hydrogen demand per {singular_label} (t H2/year)")
    ax_nodes.set_ylabel(f"Number of {plural_label}")
    ax_hydrogen.grid(True, axis="both", linestyle=":", linewidth=0.8, alpha=0.6)
    ax_nodes.grid(True, axis="both", linestyle=":", linewidth=0.8, alpha=0.6)
    ax_hydrogen.set_ylim(bottom=0)
    ax_nodes.set_ylim(bottom=0)
    ax_nodes.set_xlabel("Year")

    ax_nodes.set_xticks(available_years)
    ax_nodes.set_xlim(left=START_YEAR)
    ax_nodes.tick_params(axis="x", rotation=45)

    hydrogen_lines, hydrogen_labels = ax_hydrogen.get_legend_handles_labels()
    ax_hydrogen.legend(
        hydrogen_lines,
        hydrogen_labels,
        loc="upper left",
        bbox_to_anchor=(1.08, 1.0),
    )

    fig.tight_layout()

    output_path = output_dir / f"{safe_filename(demand_node_type)}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    report_path = args.input or find_latest_change_report()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(report_path)
    output_paths = []

    for (model, pathway), scenario_df in df.groupby(
        ["model", "pathway"], sort=True
    ):
        scenario_label = f"{str(model).upper()} — {pathway}"
        scenario_output_dir = output_dir / safe_filename(f"{model}_{pathway}")
        scenario_output_dir.mkdir(parents=True, exist_ok=True)

        plot_data = prepare_plot_data(scenario_df)
        available_years = sorted(plot_data["year"].unique())
        output_paths.extend(
            plot_demand_node_type(
                plot_data,
                demand_node_type,
                scenario_output_dir,
                available_years,
                scenario_label,
            )
            for demand_node_type in sorted(
                plot_data["demand_node_type"].unique()
            )
        )

    print(f"Source change report: {report_path.resolve()}")
    print(f"Created {len(output_paths)} chart(s):")
    for output_path in output_paths:
        print(f"- {output_path}")


if __name__ == "__main__":
    main()
