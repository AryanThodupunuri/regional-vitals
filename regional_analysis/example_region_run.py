"""Example runner for a single region + measure.

Usage (from repo root):
    python -m regional_analysis.example_region_run --region West --measure obesity

Outputs (tables):
    outputs/tables/{region_lower}_{measure_lower}_state_prevalence.csv
    outputs/tables/{region_lower}_{measure_lower}_regional_trends.csv

Outputs (figures):
    outputs/figures/{region_lower}_{measure_lower}_regional_trend.png
    outputs/figures/{region_lower}_{measure_lower}_state_trends.png

Requirements:
    - data/processed/brfss_combined_2011_2023.csv must exist
    - src/ package must be importable (repo root on PYTHONPATH)
"""

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

from src.region_mapping import STATE_TO_REGION
from src.utils import safe_read_csv, safe_write_csv
from src.compute_prevalence import compute_state_prevalence
from src.trend_analysis import (
    compute_region_year_prevalence,
    compute_rolling_avg,
    compute_trend_slope,
    pivot_measures_by_region,
    pivot_regional_trends,
)


def plot_regional_trend(regional_ts, region: str, measure: str, out_path: Path):
    if regional_ts.empty:
        raise ValueError("Regional timeseries is empty; cannot plot.")
    regional_ts = regional_ts.sort_values("year")
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(regional_ts["year"], regional_ts["prevalence_pct"], marker="o", color="#1f77b4")
    ax.set_title(f"{region} — {measure} (regional weighted prevalence)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_state_trends(state_prev, region: str, measure: str, out_path: Path):
    if state_prev.empty:
        raise ValueError("State-level table is empty; cannot plot.")
    fig, ax = plt.subplots(figsize=(9, 5))
    for state, group in state_prev.groupby("state"):
        g = group.sort_values("year")
        ax.plot(g["year"], g["prevalence_pct"], label=state, alpha=0.45)
    ax.set_title(f"{region} — {measure} by state")
    ax.set_xlabel("Year")
    ax.set_ylabel("Prevalence (%)")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=4, fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run(region: str, measure: str, combined_path: Path, tables_dir: Path, figures_dir: Path):
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined file missing: {combined_path}")

    df = safe_read_csv(combined_path)
    required = ["year", "state", "measure", "value", "sample_size"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Combined file missing columns: {missing}")

    # Add region column
    df = df.assign(region=df["state"].map(STATE_TO_REGION).fillna("Other"))

    region_filter = df["region"] == region
    measure_filter = df["measure"] == measure
    subset = df[region_filter & measure_filter]
    if subset.empty:
        raise ValueError(f"No rows found for region={region} measure={measure}")

    # State-level prevalence summary
    state_prev = compute_state_prevalence(subset)
    state_out = tables_dir / f"{region.lower()}_{measure.lower()}_state_prevalence.csv"
    safe_write_csv(state_prev, state_out)

    # Regional per-year weighted prevalence
    regional_ts = compute_region_year_prevalence(df[df["region"] == region], measure=measure)
    regional_out = tables_dir / f"{region.lower()}_{measure.lower()}_regional_trends.csv"
    safe_write_csv(regional_ts, regional_out)

    # Trend slope (linear fit per region)
    slope_df = compute_trend_slope(regional_ts)
    slope_out = tables_dir / f"{region.lower()}_{measure.lower()}_trend_slope.csv"
    safe_write_csv(slope_df, slope_out)

    # Pivot table (wide format: regions as rows, years as columns)
    pivot_df = pivot_regional_trends(regional_ts)
    pivot_out = tables_dir / f"{region.lower()}_{measure.lower()}_pivot.csv"
    pivot_df.to_csv(pivot_out)  # keep region index as a column

    # Rolling 3-year average
    rolling_df = compute_rolling_avg(regional_ts, window=3)
    rolling_out = tables_dir / f"{region.lower()}_{measure.lower()}_rolling_avg.csv"
    safe_write_csv(rolling_df, rolling_out)

    # Cross-measure pivot for the most recent year
    # Build all-measure trends for this region, then pivot
    all_measure_frames = []
    for m in ["obesity", "coverage", "smoking"]:
        m_ts = compute_region_year_prevalence(df[df["region"] == region], measure=m)
        if not m_ts.empty:
            all_measure_frames.append(m_ts)
    if all_measure_frames:
        all_trends = pd.concat(all_measure_frames, ignore_index=True)
        latest_year = int(all_trends["year"].max())
        cross_pivot = pivot_measures_by_region(all_trends, latest_year)
        cross_out = tables_dir / f"{region.lower()}_cross_measure_{latest_year}.csv"
        cross_pivot.to_csv(cross_out)
        print(f"Wrote {cross_out}")

    # Figures
    regional_fig = figures_dir / f"{region.lower()}_{measure.lower()}_regional_trend.png"
    state_fig = figures_dir / f"{region.lower()}_{measure.lower()}_state_trends.png"
    plot_regional_trend(regional_ts, region, measure, regional_fig)
    plot_state_trends(state_prev, region, measure, state_fig)

    print(f"Wrote {state_out} (rows={len(state_prev)})")
    print(f"Wrote {regional_out} (rows={len(regional_ts)})")
    print(f"Wrote {slope_out}")
    print(f"Wrote {pivot_out}")
    print(f"Wrote {rolling_out}")
    print(f"Wrote {regional_fig}")
    print(f"Wrote {state_fig}")


def main():
    parser = argparse.ArgumentParser(description="Generate outputs for a single region + measure.")
    parser.add_argument("--region", required=True, help="Region name, e.g., West, Midwest, Northeast")
    parser.add_argument("--measure", required=True, help="Measure name, e.g., obesity, coverage, smoking")
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS long-format CSV",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/tables",
        help="Directory to write outputs",
    )
    parser.add_argument(
        "--fig-dir",
        default="outputs/figures",
        help="Directory to write figures",
    )
    args = parser.parse_args()

    combined_path = Path(args.combined)
    tables_dir = Path(args.out_dir)
    figures_dir = Path(args.fig_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    run(args.region, args.measure, combined_path, tables_dir, figures_dir)


if __name__ == "__main__":
    main()
