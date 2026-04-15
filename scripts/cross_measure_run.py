"""Cross-measure comparison runner.

Compare obesity, coverage, and smoking trends within a single region.

Usage (from repo root):
    python -m scripts.cross_measure_run --region West
    python -m scripts.cross_measure_run --region Midwest --year 2020
    python -m scripts.cross_measure_run --all-regions

Outputs (tables — written locally, do NOT commit):
    outputs/tables/{region}_cross_measure_trends.csv
    outputs/tables/{region}_cross_measure_correlations.csv
    outputs/tables/{region}_cross_measure_changes.csv
    outputs/tables/{region}_cross_measure_snapshot_{year}.csv

Outputs (figures — written locally, do NOT commit):
    outputs/figures/{region}_cross_measure_trends.png
    outputs/figures/{region}_cross_measure_correlations.png

Author: Aryan Thodupunuri
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.cross_measure import (
    compare_measures_over_time,
    compute_measure_correlations,
    rank_measure_changes,
    generate_cross_measure_summary,
    compare_all_regions_cross_measure,
)
from src.region_mapping import REGIONS, STATE_TO_REGION
from src.utils import safe_read_csv, safe_write_csv


# ── Plotting helpers ────────────────────────────────────────────────────────

def plot_cross_measure_trends(trends: pd.DataFrame, region: str, out_path: Path):
    """Line chart: all measures over time for one region."""
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"obesity": "#e74c3c", "coverage": "#2ecc71", "smoking": "#3498db"}

    for measure, grp in trends.groupby("measure"):
        grp = grp.sort_values("year")
        ax.plot(
            grp["year"], grp["prevalence_pct"],
            marker="o", linewidth=2, label=measure.capitalize(),
            color=colors.get(measure, None),
        )

    ax.set_title(f"{region} — Cross-Measure Comparison", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.legend(frameon=False, fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_correlation_heatmap(corr: pd.DataFrame, region: str, out_path: Path):
    """Heatmap of pairwise measure correlations."""
    fig, ax = plt.subplots(figsize=(6, 5))
    mask = np.zeros_like(corr, dtype=bool)

    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
        vmin=-1, vmax=1, square=True, linewidths=0.5,
        mask=mask, ax=ax,
    )
    ax.set_title(f"{region} — Measure Correlations (state-level)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ── Single-region runner ────────────────────────────────────────────────────

def run_region(region: str, combined_path: Path, tables_dir: Path, figures_dir: Path, year: int | None):
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined file missing: {combined_path}")

    df = safe_read_csv(combined_path)

    # Add region column
    df = df.assign(region=df["state"].map(STATE_TO_REGION).fillna("Other"))

    summary = generate_cross_measure_summary(df, region, year=year)
    trends = summary["trends"]
    corr = summary["correlations"]
    changes = summary["changes"]
    snapshot = summary["snapshot"]
    snap_year = summary["year"]

    tag = region.lower()

    # Write tables
    safe_write_csv(trends, tables_dir / f"{tag}_cross_measure_trends.csv")
    print(f"  Wrote {tag}_cross_measure_trends.csv ({len(trends)} rows)")

    if not corr.empty:
        corr.to_csv(tables_dir / f"{tag}_cross_measure_correlations.csv")
        print(f"  Wrote {tag}_cross_measure_correlations.csv")

    safe_write_csv(changes, tables_dir / f"{tag}_cross_measure_changes.csv")
    print(f"  Wrote {tag}_cross_measure_changes.csv ({len(changes)} rows)")

    if not snapshot.empty:
        safe_write_csv(snapshot, tables_dir / f"{tag}_cross_measure_snapshot_{snap_year}.csv")
        print(f"  Wrote {tag}_cross_measure_snapshot_{snap_year}.csv")

    # Write figures
    if not trends.empty:
        plot_cross_measure_trends(trends, region, figures_dir / f"{tag}_cross_measure_trends.png")
        print(f"  Wrote {tag}_cross_measure_trends.png")

    if not corr.empty and corr.notna().any().any():
        plot_correlation_heatmap(corr, region, figures_dir / f"{tag}_cross_measure_correlations.png")
        print(f"  Wrote {tag}_cross_measure_correlations.png")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Cross-measure comparison: obesity vs coverage vs smoking within a region."
    )
    parser.add_argument("--region", help="Region name, e.g., West, Midwest, Northeast")
    parser.add_argument("--all-regions", action="store_true", help="Run for all five regions")
    parser.add_argument("--year", type=int, default=None, help="Snapshot year (default: latest)")
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS CSV",
    )
    parser.add_argument("--out-dir", default="outputs/tables", help="Tables output directory")
    parser.add_argument("--fig-dir", default="outputs/figures", help="Figures output directory")
    args = parser.parse_args()

    if not args.region and not args.all_regions:
        parser.error("Provide --region <name> or --all-regions")

    combined_path = Path(args.combined)
    tables_dir = Path(args.out_dir)
    figures_dir = Path(args.fig_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    if args.all_regions:
        regions = list(REGIONS.keys())
    else:
        regions = [args.region]

    for region in regions:
        print(f"\n{'='*50}")
        print(f"Cross-measure comparison: {region}")
        print(f"{'='*50}")
        run_region(region, combined_path, tables_dir, figures_dir, args.year)

    print("\nDone. Remember: do NOT commit outputs to the repo.")


if __name__ == "__main__":
    main()
