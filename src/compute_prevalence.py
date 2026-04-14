"""compute_prevalence.py

Simple helper to compute prevalence summaries from the combined BRFSS dataset.
"""

from pathlib import Path
import pandas as pd


def compute_state_prevalence(df: pd.DataFrame) -> pd.DataFrame:
    """Return a state-year-indicator prevalence table.

    Expects df with columns: year, state, measure, value, sample_size
    and computes a sample-size-weighted prevalence_pct.
    """
    required = ["year", "state", "measure", "value", "sample_size"]
    for r in required:
        if r not in df.columns:
            raise ValueError(f"DataFrame missing required column: {r}")
            
    out = df.copy()
    out["weighted"] = out["value"] * out["sample_size"]

    out = out.groupby(["year", "state", "measure"], as_index=False).agg(
        weighted_sum=("weighted", "sum"),
        sample_size=("sample_size", "sum"),
    )

    out["prevalence_pct"] = out["weighted_sum"] / out["sample_size"]

    out = out[["year", "state", "measure", "prevalence_pct", "sample_size"]]

    return out
    

def load_combined(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)
