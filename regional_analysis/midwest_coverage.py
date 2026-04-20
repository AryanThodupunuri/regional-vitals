"""
Midwest Healthcare Coverage (2011-2023)

All 12 Midwest states showed a positive increase in healthcare coverage. 
Indiana (IN) led the region with a 14.5% increase in coverage from 2011 to 2023.
South Dakota (SD) had the lowest growth at 5.2%.
"""

import pandas as pd
import sys
from pathlib import Path

# paths to find src
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# team tools
from src.region_mapping import REGIONS
from src.utils import safe_read_csv, safe_write_csv
from src.compute_prevalence import compute_state_prevalence


def main():
    # loading data
    data_path = project_root / 'data' / 'processed' / 'brfss_coverage_2011_2023.csv'
    df = safe_read_csv(data_path)

    # midwest states
    midwest_states = REGIONS["Midwest"]
    midwest_df = df[df['state'].isin(midwest_states)]

    # prevalence stats
    midwest_results = compute_state_prevalence(midwest_df)

    # placing in outputs folder
    output_path = project_root / 'outputs' / 'midwest_coverage_trends.csv'
    safe_write_csv(midwest_results, output_path)

    # sort to ensure years are in order
    summary_midwest_df = midwest_results.sort_values(['state', 'year'])

    # total change per state (2023 minus 2011)
    trends = []

    for state in REGIONS["Midwest"]:
        midwest_state_data = summary_midwest_df[summary_midwest_df['state'] == state]

        if midwest_state_data.empty:
            print(f"WARNING: No data found for {state}, skipping.")
            continue

        start_rows = midwest_state_data[midwest_state_data['year'] == 2011]['prevalence_pct']
        end_rows   = midwest_state_data[midwest_state_data['year'] == 2023]['prevalence_pct']

        if start_rows.empty:
            print(f"WARNING: No 2011 data for {state}, skipping.")
            continue
        if end_rows.empty:
            print(f"WARNING: No 2023 data for {state}, skipping.")
            continue

        growth = end_rows.values[0] - start_rows.values[0]
        trends.append({'state': state, 'total_increase': round(growth, 2)})

    # making dataframe
    midwest_growth_summary = pd.DataFrame(trends).sort_values('total_increase', ascending=False)

    # saving to outputs
    output_path = project_root / 'outputs' / 'midwest_growth_summary.csv'
    safe_write_csv(midwest_growth_summary, output_path)

    print(midwest_growth_summary)


if __name__ == "__main__":
    main()
