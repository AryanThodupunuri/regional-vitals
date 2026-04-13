"""Example runner for analyses that span ALL regions at once.

Some analyses (convergence across regions, COVID-period comparison across
regions) only make sense when you have every region in the dataset, not just
one. Previously these were tucked inside example_region_run.py, which meant
they got recomputed every time someone ran a single-region job and they wrote
files that didn't depend on --region at all. This script pulls them out into
their own runner.

Usage (from repo root):
    python -m regional_analysis.example_all_regions_run --measure obesity
    python -m regional_analysis.example_all_regions_run --measure coverage
    python -m regional_analysis.example_all_regions_run --measure smoking

    # Or run all three measures in one go:
    python -m regional_analysis.example_all_regions_run --all

Outputs (tables):
    outputs/tables/{measure}_convergence.csv
    outputs/tables/{measure}_covid_comparison.csv

Outputs (figures):
    outputs/figures/{measure}_all_regions_trend.png
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from src.region_mapping import STATE_TO_REGION
from src.utils import safe_read_csv, safe_write_csv
from src.trend_analysis import (
    compare_covid_periods,
    compute_convergence,
    compute_region_year_prevalence,
)

VALID_MEASURES = ["obesity", "coverage", "smoking"]


def plot_all_regions(all_region_ts, measure: str, out_path: Path):
    """Plot one line per region on a single chart."""
    if all_region_ts.empty:
        raise ValueError("All-region timeseries is empty; cannot plot.")
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for region, group in all_region_ts.groupby("region"):
        g = group.sort_values("year")
        ax.plot(g["year"], g["prevalence_pct"], marker="o", label=region)
    ax.set_title(f"All regions — {measure} (weighted prevalence)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run_measure(measure: str, combined_path: Path, tables_dir: Path, figures_dir: Path):
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined file missing: {combined_path}")

    df = safe_read_csv(combined_path)
    required = ["year", "state", "measure", "value", "sample_size"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Combined file missing columns: {missing}")

    df = df.assign(region=df["state"].map(STATE_TO_REGION).fillna("Other"))

    if not (df["measure"] == measure).any():
        raise ValueError(f"No rows found for measure={measure}")

    # All-region weighted timeseries (one row per region per year)
    all_region_ts = compute_region_year_prevalence(df, measure=measure)

    # Convergence analysis: are regions converging or diverging over time?
    conv_df = compute_convergence(all_region_ts)
    conv_out = tables_dir / f"{measure.lower()}_convergence.csv"
    safe_write_csv(conv_df, conv_out)

    # COVID period comparison (pre vs post 2019-2023)
    covid_df = compare_covid_periods(all_region_ts)
    covid_out = tables_dir / f"{measure.lower()}_covid_comparison.csv"
    safe_write_csv(covid_df, covid_out)

    # Figure: all regions on one chart
    fig_out = figures_dir / f"{measure.lower()}_all_regions_trend.png"
    plot_all_regions(all_region_ts, measure, fig_out)

    print(f"[{measure}] wrote {conv_out}")
    print(f"[{measure}] wrote {covid_out}")
    print(f"[{measure}] wrote {fig_out}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate all-region outputs (convergence + COVID comparison)."
    )
    parser.add_argument("--measure", choices=VALID_MEASURES,
                        help="Single measure to run")
    parser.add_argument("--all", action="store_true",
                        help="Run for all measures (obesity, coverage, smoking)")
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS long-format CSV",
    )
    parser.add_argument("--out-dir", default="outputs/tables")
    parser.add_argument("--fig-dir", default="outputs/figures")
    args = parser.parse_args()

    if not args.measure and not args.all:
        parser.error("Specify --measure <name> or --all")

    combined_path = Path(args.combined)
    tables_dir = Path(args.out_dir)
    figures_dir = Path(args.fig_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    measures = VALID_MEASURES if args.all else [args.measure]
    for m in measures:
        run_measure(m, combined_path, tables_dir, figures_dir)


if __name__ == "__main__":
    main()
