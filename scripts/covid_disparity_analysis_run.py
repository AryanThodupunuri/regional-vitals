"""COVID disparity analysis runner.

Generate descriptive COVID-era disparity tables for all regions and all
project measures: obesity, healthcare coverage, and smoking.

This script is the command-line runner for src/covid_disparity_analysis.py.
It reads the combined BRFSS long-format dataset, adds a region column using
the project state-to-region mapping, runs the COVID disparity analysis
functions, and writes the resulting CSV tables to outputs/tables/.

The analyses produced by this runner focus on disparity rather than simple
average changes. Specifically, the script generates:

1. Within-region state disparity by year:
   Measures the gap between the lowest-prevalence and highest-prevalence
   state inside each region for each measure and year.

2. Pre/post COVID disparity change:
   Compares average within-region state gaps in the pre-COVID window
   (default 2017-2019) versus the post-COVID window (default 2021-2023).

3. Regional gap to best-performing region:
   Calculates how far each region is from the best-performing region in
   each year. For coverage, higher values are better; for obesity and
   smoking, lower values are better.

4. Pre/post change in gap to best:
   Compares whether each region moved closer to or farther from the
   best-performing region after COVID.

5. Disparity rankings:
   Ranks regions by the largest post-COVID widening in within-region
   state disparity.

Usage (from repo root):
    python -m scripts.covid_disparity_analysis_run

Outputs (tables):
    outputs/tables/covid_state_disparity_by_region.csv
    outputs/tables/covid_pre_post_disparity_change.csv
    outputs/tables/covid_gap_to_best_region.csv
    outputs/tables/covid_pre_post_gap_to_best.csv
    outputs/tables/covid_disparity_rankings.csv

These analyses are descriptive only and should not be interpreted as causal
evidence of COVID-related effects.
"""

import argparse
from pathlib import Path

from src.covid_disparity_analysis import (
    compare_pre_post_disparity,
    compare_pre_post_gap_to_best,
    compute_regional_gap_to_best,
    compute_state_disparity_by_region,
    rank_regions_by_disparity_change,
)
from src.region_mapping import STATE_TO_REGION
from src.utils import safe_read_csv, safe_write_csv


def run(
    combined_path: Path,
    tables_dir: Path,
    top_n: int | None = None,
):
    """Run all COVID disparity analyses and write output tables."""
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined file missing: {combined_path}")

    df = safe_read_csv(combined_path)

    required = ["year", "state", "measure", "value", "sample_size"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Combined file missing columns: {missing}")

    # Add region column
    df = df.assign(region=df["state"].map(STATE_TO_REGION).fillna("Other"))

    # Within-region state disparity by year
    state_disparity = compute_state_disparity_by_region(df)
    state_disparity_out = tables_dir / "covid_state_disparity_by_region.csv"
    safe_write_csv(state_disparity, state_disparity_out)

    # Pre/post change in within-region state disparity
    disparity_change = compare_pre_post_disparity(state_disparity)
    disparity_change_out = tables_dir / "covid_pre_post_disparity_change.csv"
    safe_write_csv(disparity_change, disparity_change_out)

    # Regional gap to best-performing region by year
    gap_to_best = compute_regional_gap_to_best(df)
    gap_to_best_out = tables_dir / "covid_gap_to_best_region.csv"
    safe_write_csv(gap_to_best, gap_to_best_out)

    # Pre/post change in gap to best-performing region
    pre_post_gap = compare_pre_post_gap_to_best(gap_to_best)
    pre_post_gap_out = tables_dir / "covid_pre_post_gap_to_best.csv"
    safe_write_csv(pre_post_gap, pre_post_gap_out)

    # Rankings of regions by disparity widening
    rankings = rank_regions_by_disparity_change(disparity_change, top_n=top_n)
    rankings_out = tables_dir / "covid_disparity_rankings.csv"
    safe_write_csv(rankings, rankings_out)

    print(f"Wrote {state_disparity_out} (rows={len(state_disparity)})")
    print(f"Wrote {disparity_change_out} (rows={len(disparity_change)})")
    print(f"Wrote {gap_to_best_out} (rows={len(gap_to_best)})")
    print(f"Wrote {pre_post_gap_out} (rows={len(pre_post_gap)})")
    print(f"Wrote {rankings_out} (rows={len(rankings)})")


def main():
    parser = argparse.ArgumentParser(
        description="Generate COVID-era disparity analyses for all regions and measures."
    )
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS long-format CSV",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/tables",
        help="Directory for output tables",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Optional number of top regions per measure to include in rankings",
    )
    args = parser.parse_args()

    combined_path = Path(args.combined)
    tables_dir = Path(args.out_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    run(
        combined_path=combined_path,
        tables_dir=tables_dir,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
