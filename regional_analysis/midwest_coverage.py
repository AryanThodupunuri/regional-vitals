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