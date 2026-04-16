"""Generate formatted regional summary / comparison tables.

Usage (from repo root):
    python -m regional_analysis.regional_summary_run
    python -m regional_analysis.regional_summary_run --combined data/processed/brfss_combined_2011_2023.csv

Outputs (tables):
    outputs/tables/regional_snapshot_{year}.csv
    outputs/tables/regional_period_change.csv
    outputs/tables/regional_trend_slopes.csv
    outputs/tables/regional_rankings_{year}.csv
    outputs/tables/regional_matrix_obesity.csv
    outputs/tables/regional_matrix_coverage.csv
    outputs/tables/regional_matrix_smoking.csv
    outputs/tables/regional_grand_summary.csv
"""

import argparse
from pathlib import Path

from src.utils import safe_read_csv, safe_write_csv
from src.regional_summary import (
    MEASURE_ORDER,
    grand_summary,
    latest_year_snapshot,
    period_change_table,
    rank_regions_by_year,
    trend_slopes_summary,
    year_by_region_matrix,
)

SEPARATOR = "-" * 72


def _print_table(title: str, df, path: Path):
    """Write a DataFrame to CSV and print a formatted preview."""
    if hasattr(df, "attrs") and "title" in df.attrs:
        title = df.attrs["title"]
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)
    print(df.to_string())
    print()

    if df.index.name == "region":
        df.to_csv(path)
    else:
        safe_write_csv(df, path)
    print(f"  -> {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate cross-region comparison tables for all 5 regions."
    )
    parser.add_argument(
        "--combined",
        default="data/processed/brfss_combined_2011_2023.csv",
        help="Path to combined BRFSS long-format CSV",
    )
    parser.add_argument("--out-dir", default="outputs/tables")
    args = parser.parse_args()

    combined_path = Path(args.combined)
    tables_dir = Path(args.out_dir)
    tables_dir.mkdir(parents=True, exist_ok=True)

    if not combined_path.exists():
        raise FileNotFoundError(f"Combined file missing: {combined_path}")

    df = safe_read_csv(combined_path)

    # 1 — Latest-year snapshot
    snap = latest_year_snapshot(df)
    latest_year = int(df["year"].max())
    _print_table(
        f"Regional Prevalence Snapshot ({latest_year})",
        snap,
        tables_dir / f"regional_snapshot_{latest_year}.csv",
    )

    # 2 — Period change (full study window)
    change = period_change_table(df)
    _print_table(
        "Period Change (Start → End Year)",
        change,
        tables_dir / "regional_period_change.csv",
    )

    # 3 — Trend slopes
    slopes = trend_slopes_summary(df)
    _print_table(
        "Linear Trend Slopes (pp/year) & R² by Region",
        slopes,
        tables_dir / "regional_trend_slopes.csv",
    )

    # 4 — Regional rankings
    ranks = rank_regions_by_year(df)
    _print_table(
        f"Regional Rankings ({latest_year})",
        ranks,
        tables_dir / f"regional_rankings_{latest_year}.csv",
    )

    # 5 — Year-by-region matrices (one per measure)
    for measure in MEASURE_ORDER:
        matrix = year_by_region_matrix(df, measure)
        _print_table(
            f"Year × Region Matrix — {measure.title()}",
            matrix,
            tables_dir / f"regional_matrix_{measure}.csv",
        )

    # 6 — Grand summary statistics
    gs = grand_summary(df)
    _print_table(
        "Grand Summary Statistics (Full Study Period)",
        gs,
        tables_dir / "regional_grand_summary.csv",
    )

    print(f"\n{'=' * 72}")
    print("  All regional summary tables written to", tables_dir)
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
