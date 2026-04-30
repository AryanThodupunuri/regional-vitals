"""Multi-line plot runner: all regions on one chart per measure.

Usage (from repo root):
    python -m scripts.multiline_plot_run
    python -m scripts.multiline_plot_run --measure smoking
    python -m scripts.multiline_plot_run --measure obesity --combined data/processed/brfss_combined_2011_2023.csv

Outputs (figures):
    outputs/figures/all_regions_{measure}_trends.png   (one per measure)

Requirements:
    - data/processed/brfss_combined_2011_2023.csv must exist
    - src/ package must be importable (repo root on PYTHONPATH)
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from src.region_mapping import add_region_column
from src.utils import safe_read_csv
from src.trend_analysis import compute_region_year_prevalence

MEASURES = ["obesity", "coverage", "smoking"]
REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]

REGION_COLORS = {
    "Northeast": "#1f77b4",
    "Southeast": "#d62728",
    "Midwest":   "#2ca02c",
    "Southwest": "#ff7f0e",
    "West":      "#9467bd",
}


def plot_all_regions(df, measure: str, out_path: Path):
    """Plot prevalence trends for all regions on one chart for a given measure."""
    fig, ax = plt.subplots(figsize=(9, 5))

    for region in REGIONS:
        regional_ts = compute_region_year_prevalence(
            df[df["region"] == region], measure=measure
        )
        if regional_ts.empty:
            continue
        regional_ts = regional_ts.sort_values("year")
        ax.plot(
            regional_ts["year"],
            regional_ts["prevalence_pct"],
            marker="o",
            label=region,
            color=REGION_COLORS[region],
        )

    ax.set_title(f"All Regions — {measure.capitalize()} Prevalence (2011–2023)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.legend(title="Region", frameon=True)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Wrote {out_path}")


def run(measures: list, combined_path: Path, figures_dir: Path):
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined file missing: {combined_path}")

    df = safe_read_csv(combined_path)
    required = ["year", "state", "measure", "value", "sample_size"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Combined file missing columns: {missing}")

    df = add_region_column(df)
    figures_dir.mkdir(parents=True, exist_ok=True)

    for measure in measures:
        out_path = figures_dir / f"all_regions_{measure}_trends.png"
        plot_all_regions(df, measure, out_path)


def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-line plots: all regions on one chart per measure."
    )
    parser.add_argument(
        "--measure",
        choices=MEASURES,
        default=None,
        help="Single measure to plot. Omit to plot all three measures.",
    )
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS long-format CSV",
    )
    parser.add_argument(
        "--fig-dir",
        default="outputs/figures",
        help="Directory to write figures",
    )
    args = parser.parse_args()

    measures = [args.measure] if args.measure else MEASURES
    run(measures, Path(args.combined), Path(args.fig_dir))


if __name__ == "__main__":
    main()
