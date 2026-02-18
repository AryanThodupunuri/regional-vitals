"""compute_prevalence.py

Simple helper to compute prevalence summaries from the combined BRFSS dataset.
"""
from pathlib import Path
import pandas as pd


def compute_state_prevalence(df: pd.DataFrame) -> pd.DataFrame:
    """Return a state-year-indicator prevalence table.

    Expects df with columns: year,state,measure,value,ci_lower,ci_upper,sample_size
    """
    required = ["year","state","measure","value"]
    for r in required:
        if r not in df.columns:
            raise ValueError(f"DataFrame missing required column: {r}")
    out = df.groupby(["year","state","measure"], as_index=False).agg(
        prevalence_pct=("value","mean"),
        sample_size=("sample_size","sum")
    )
    return out


def load_combined(path: Path):
    return pd.read_csv(path)
