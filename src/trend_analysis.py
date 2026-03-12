"""trend_analysis.py

Utilities for simple descriptive trend calculations.
This module intentionally keeps methods simple and descriptive (no causal modeling).
"""

import pandas as pd


def compute_region_year_prevalence(df: pd.DataFrame, measure: str) -> pd.DataFrame:
    """Compute weighted-average prevalence per region per year for a given measure.

    Parameters
    ----------
    df : DataFrame
        Must contain columns: year, region, measure, value, sample_size.
    measure : str
        The measure to filter on (e.g. 'obesity', 'coverage', 'smoking').

    Returns
    -------
    DataFrame with columns: region, year, measure, prevalence_pct, sample_size_total.
    """
    sub = df[df["measure"] == measure].copy()
    if sub.empty:
        return pd.DataFrame(columns=["region", "year", "measure", "prevalence_pct", "sample_size_total"])

    sub["weighted"] = sub["value"] * sub["sample_size"]

    agg = sub.groupby(["region", "year"], as_index=False).agg(
        weighted_sum=("weighted", "sum"),
        sample_size_total=("sample_size", "sum"),
    )
    agg["prevalence_pct"] = agg["weighted_sum"] / agg["sample_size_total"]
    agg["measure"] = measure
    return agg[["region", "year", "measure", "prevalence_pct", "sample_size_total"]].sort_values("year")
