"""Runner script for COVID trend-shift analysis across all U.S. regions.

This script loads the real CDC BRFSS data and runs all five analyses
from src/covid_analysis.py, printing results to the console and saving
CSV outputs to outputs/tables/.

Usage (from repo root):
    python -m scripts.covid_analysis_run
    python -m scripts.covid_analysis_run --measure obesity
    python -m scripts.covid_analysis_run --measure smoking
    python -m scripts.covid_analysis_run --measure coverage

Outputs (tables):
    outputs/tables/covid_trend_slopes_{measure}.csv
    outputs/tables/covid_disruption_score_{measure}.csv
    outputs/tables/covid_rank_measures.csv
    outputs/tables/covid_recovery_trajectory_{measure}.csv
    outputs/tables/covid_summary_table.csv
"""

import argparse
from pathlib import Path
import pandas as pd

from src.region_mapping import STATE_TO_REGION
from src.utils import safe_read_csv, safe_write_csv
from src.trend_analysis import compute_region_year_prevalence
from src.covid_analysis import (
    compare_trend_slopes,
    compute_disruption_score,
    rank_measures_by_disruption,
    compute_recovery_trajectory,
    build_covid_summary_table,
)

VALID_MEASURES = ["obesity", "coverage", "smoking"]
MEASURE_LABELS = {
    "obesity": "Obesity Prevalence (%)",
    "coverage": "Healthcare Coverage (%)",
    "smoking": "Smoking Prevalence (%)",
}

def print_section(title: str):
    width = 70
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)

def run(measures: list, combined_path: Path, tables_dir: Path):
    if not combined_path.exists():
        raise FileNotFoundError(f"Combined data file missing: {combined_path}\n"
                                "Run: python -m src.download_data --all")
    df = safe_read_csv(combined_path)
    df = df.assign(region=df["state"].map(STATE_TO_REGION).fillna("Other"))

    # Build per-measure timeseries for all regions
    ts_by_measure = {}
    for m in measures:
        ts_by_measure[m] = compute_region_year_prevalence(df, measure=m)

    pd.set_option("display.float_format", "{:.2f}".format)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 100)

    # ------------------------------------------------------------------
    # 1. Trend slopes — how did the rate of change shift post-COVID?
    # ------------------------------------------------------------------
    for measure in measures:
        print_section(
            f"TREND SLOPES — {measure.upper()} "
            f"(pp/year before vs after COVID-19)"
        )
        print(
            "  pre_slope  = average annual change 2017-2019 (percentage points/year)\n"
            "  post_slope = average annual change 2021-2023\n"
            "  slope_shift = post minus pre (negative = slowdown or reversal)\n"
        )
        result = compare_trend_slopes(ts_by_measure[measure])
        print(result.to_string(index=False))

        out = tables_dir / f"covid_trend_slopes_{measure}.csv"
        safe_write_csv(result, out)
        print(f"\n  Saved -> {out}")

    # ------------------------------------------------------------------
    # 2. Disruption score — which regions were hit hardest?
    # ------------------------------------------------------------------
    for measure in measures:
        print_section(
            f"COVID DISRUPTION SCORE — {measure.upper()}"
        )
        print(
            "  pre_avg  = mean prevalence 2017-2019\n"
            "  post_avg = mean prevalence 2021-2023\n"
            "  delta    = post minus pre (absolute change in percentage points)\n"
            "  disruption_score = combined measure of how much COVID shifted\n"
            "                     both the level AND the trend (higher = more disrupted)\n"
        )
        result = compute_disruption_score(ts_by_measure[measure])
        print(result.to_string(index=False))

        out = tables_dir / f"covid_disruption_score_{measure}.csv"
        safe_write_csv(result, out)
        print(f"\n  Saved -> {out}")

    # ------------------------------------------------------------------
    # 3. Rank measures — which health metric was most affected by COVID?
    # ------------------------------------------------------------------
    print_section("WHICH HEALTH MEASURE WAS MOST DISRUPTED BY COVID?")
    print(
        "  avg_disruption_score  = average disruption score across all 5 regions\n"
        "  max_disruption_region = region with the single highest disruption score\n"
    )
    ranking = rank_measures_by_disruption(ts_by_measure)
    print(ranking.to_string(index=False))

    out = tables_dir / "covid_rank_measures.csv"
    safe_write_csv(ranking, out)
    print(f"\n  Saved -> {out}")

    # ------------------------------------------------------------------
    # 4. Recovery trajectory — are regions back on track?
    # ------------------------------------------------------------------
    for measure in measures:
        print_section(
            f"RECOVERY TRAJECTORY — {measure.upper()}"
        )
        print(
            "  projected = where the pre-COVID trend line predicted prevalence would be\n"
            "  actual    = what was actually observed in the CDC data\n"
            "  gap       = actual minus projected\n"
            "              negative gap = below pre-COVID trajectory (recovering faster)\n"
            "              positive gap = above pre-COVID trajectory (lagging recovery)\n"
        )
        result = compute_recovery_trajectory(ts_by_measure[measure])
        print(result.to_string(index=False))

        out = tables_dir / f"covid_recovery_trajectory_{measure}.csv"
        safe_write_csv(result, out)
        print(f"\n  Saved -> {out}")

    # ------------------------------------------------------------------
    # 5. Full summary table — everything in one place
    # ------------------------------------------------------------------
    print_section("FULL COVID IMPACT SUMMARY (all measures x all regions)")
    print(
        "  All metrics combined: pre/post averages, delta, pct_change,\n"
        "  pre/post slopes, slope_shift, and disruption_score.\n"
        "  Sorted by measure then disruption_score descending.\n"
    )
    summary = build_covid_summary_table(ts_by_measure)
    print(summary.to_string(index=False))

    out = tables_dir / "covid_summary_table.csv"
    summary.to_csv(out, index=False)
    print(f"\n  Saved -> {out}")

    print()
    print("=" * 70)
    print("  All outputs written to:", tables_dir)
    print("=" * 70)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Run COVID trend-shift analysis across all U.S. regions."
    )
    parser.add_argument(
        "--measure",
        choices=VALID_MEASURES,
        help="Single measure to analyze. Omit to run all three.",
    )
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS CSV.",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/tables",
        help="Directory to write output CSVs.",
    )
    args = parser.parse_args()

    combined_path = Path(args.combined)
    tables_dir = Path(args.out_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    measures = [args.measure] if args.measure else VALID_MEASURES
    run(measures, combined_path, tables_dir)

if __name__ == "__main__":
    main()