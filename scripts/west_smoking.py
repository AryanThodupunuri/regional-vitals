"""
West Region Smoking Prevalence (2011-2023)
All states in the West showed a decline in smoking prevalence over the study period.
This script identifies which states drove the trend and ranks them by total reduction.
"""
import pandas as pd
import sys
from pathlib import Path
from src.region_mapping import REGIONS

# paths to find src
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# team tools
from src.utils import safe_read_csv, safe_write_csv
from src.compute_prevalence import compute_state_prevalence


def main():
    """Run the West smoking analysis and write output CSVs."""
    # loading data
    data_path = project_root / 'data' / 'processed' / 'brfss_smoking_2011_2023.csv'
    df = safe_read_csv(data_path)

    # west states
    west_states = REGIONS["West"]
    west_df = df[df['state'].isin(west_states)]

    # prevalence stats
    west_results = compute_state_prevalence(west_df)

    # placing in outputs folder
    output_path = project_root / 'outputs' / 'west_smoking_trends.csv'
    safe_write_csv(west_results, output_path)

    # sort to ensure years are in order
    summary_west_df = west_results.sort_values(['state', 'year'])

    # total change per state (2023 minus 2011)
    trends = []
    for state in REGIONS["West"]:
        west_state_data = summary_west_df[summary_west_df['state'] == state]
        if not west_state_data.empty:
            years = west_state_data['year'].values
            start_year = years.min()
            end_year = years.max()
            start_vals = west_state_data[west_state_data['year'] == start_year]['prevalence_pct'].values
            end_vals = west_state_data[west_state_data['year'] == end_year]['prevalence_pct'].values
            if len(start_vals) > 0 and len(end_vals) > 0:
                change = end_vals[0] - start_vals[0]
                trends.append({
                    'state': state,
                    'start_year': start_year,
                    'end_year': end_year,
                    'start_pct': round(float(start_vals[0]), 2),
                    'end_pct': round(float(end_vals[0]), 2),
                    'total_change': round(float(change), 2),
                })

    # making dataframe — sorted by largest reduction (most negative change first)
    west_change_summary = pd.DataFrame(trends).sort_values('total_change')

    # saving to outputs
    output_path = project_root / 'outputs' / 'west_smoking_change_summary.csv'
    safe_write_csv(west_change_summary, output_path)

    print(west_change_summary.to_string(index=False))


if __name__ == "__main__":
    main()
