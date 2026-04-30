"""
West Region Smoking Prevalence (2011-2023)
All states in the West showed a decline in smoking prevalence over the study period.
This script identifies which states drove the trend and ranks them by total reduction.
"""
import sys
from pathlib import Path
from src.region_mapping import REGIONS

# paths to find src
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# team tools
from src.utils import safe_read_csv, safe_write_csv
from src.compute_prevalence import compute_state_prevalence, compute_state_prevalence_change


def main():
    """Run the West smoking analysis and write output CSVs."""
    # loading data
    data_path = project_root / "data" / "processed" / "brfss_smoking_2011_2023.csv"
    df = safe_read_csv(data_path)

    # west states
    west_states = REGIONS["West"]
    west_df = df[df["state"].isin(west_states)]

    # prevalence stats
    west_results = compute_state_prevalence(west_df)

    # placing in outputs folder
    output_path = project_root / "outputs" / "west_smoking_trends.csv"
    safe_write_csv(west_results, output_path)

    west_change_summary = compute_state_prevalence_change(
        west_results.sort_values(["state", "year"]),
        REGIONS["West"],
        use_each_states_year_range=True,
    ).sort_values("total_change")

    # saving to outputs
    output_path = project_root / "outputs" / "west_smoking_change_summary.csv"
    safe_write_csv(west_change_summary, output_path)

    print(west_change_summary.to_string(index=False))


if __name__ == "__main__":
    main()
