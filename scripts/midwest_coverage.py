"""
Midwest Healthcare Coverage (2011-2023)

All 12 Midwest states showed a positive increase in healthcare coverage.
Indiana (IN) led the region with a 14.5% increase in coverage from 2011 to 2023.
South Dakota (SD) had the lowest growth at 5.2%.
"""

import sys
from pathlib import Path

# paths to find src
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# team tools
from src.region_mapping import REGIONS
from src.utils import safe_read_csv, safe_write_csv
from src.compute_prevalence import compute_state_prevalence, compute_state_prevalence_change


def main():
    """Run the Midwest coverage analysis and write output CSVs."""
    # loading data
    data_path = project_root / "data" / "processed" / "brfss_coverage_2011_2023.csv"
    df = safe_read_csv(data_path)

    # midwest states
    midwest_states = REGIONS["Midwest"]
    midwest_df = df[df["state"].isin(midwest_states)]

    # prevalence stats
    midwest_results = compute_state_prevalence(midwest_df)

    # placing in outputs folder
    output_path = project_root / "outputs" / "midwest_coverage_trends.csv"
    safe_write_csv(midwest_results, output_path)

    full_summary = compute_state_prevalence_change(
        midwest_results.sort_values(["state", "year"]),
        REGIONS["Midwest"],
        start_year=2011,
        end_year=2023,
    )
    present = set(full_summary["state"])
    for state in REGIONS["Midwest"]:
        if state not in present:
            print(f"Warning: missing 2011 or 2023 data for {state}, skipping")

    midwest_growth_summary = (
        full_summary[["state", "total_change"]]
        .rename(columns={"total_change": "total_increase"})
        .sort_values("total_increase", ascending=False)
    )

    # saving to outputs
    output_path = project_root / "outputs" / "midwest_growth_summary.csv"
    safe_write_csv(midwest_growth_summary, output_path)

    print(midwest_growth_summary)


if __name__ == "__main__":
    main()
