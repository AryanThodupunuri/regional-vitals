"""
RegionalVitals Demo
===================
A quick look at the package's core capabilities using
pre-processed CDC BRFSS data (2011-2023).

Requirements:
    pip install -r requirements.txt
    python -m src.download_data --all   # only needed once

Run:
    python demo.py
"""

from src.state_rankings import rank_states
from src.covid_analysis import compute_disruption_score
from src.trend_analysis import compute_region_year_prevalence, compute_trend_slope
from src.region_mapping import STATE_TO_REGION
import pandas as pd
import os
import sys

# ── 0. Verify the data exists ─────────────────────────────────────────────────
DATA_PATH = os.path.join("data", "processed", "brfss_combined_2011_2023.csv")
if not os.path.exists(DATA_PATH):
    print("Data not found. Run: python -m src.download_data --all")
    sys.exit(1)


DIVIDER = "\n" + "─" * 60 + "\n"

print(DIVIDER)
print("REGIONALVITALS DEMO")
print(DIVIDER)

# ── 1. Load data and add region column ───────────────────────────────────────
df = pd.read_csv(DATA_PATH)
df["region"] = df["state"].map(STATE_TO_REGION)
df = df.dropna(subset=["region"])

print(
    f"Loaded {len(df):,} rows  |  {df['year'].min()}–{df['year'].max()}  |  {df['state'].nunique()} states")
print(f"Measures: {sorted(df['measure'].unique())}")

# ── 2. Trend slopes — obesity across all regions ──────────────────────────────
print(DIVIDER + "1. Trend slopes — obesity (percentage points / year)\n")

regional_ts = compute_region_year_prevalence(df, measure="obesity")
slopes = compute_trend_slope(regional_ts)
print(slopes.to_string(index=False))

# ── 3. COVID disruption scores ────────────────────────────────────────────────
print(DIVIDER + "2. COVID disruption scores — obesity\n")
print("   How much did COVID alter each region's health trajectory?\n")

disruption = compute_disruption_score(regional_ts)
print(disruption.sort_values("disruption_score",
      ascending=False).to_string(index=False))

# ── 4. State rankings — top 5 obesity increasers ─────────────────────────────
print(DIVIDER + "3. Top 5 states by obesity increase (2011–2023)\n")

increasers, decreasers = rank_states(
    df, measure="obesity", top_n=5)  # returns two ranked dataframes
print(increasers.to_string(index=False))

print(DIVIDER)
print("For interactive charts, run:")
print("  python -m scripts.explore")
print(DIVIDER)
