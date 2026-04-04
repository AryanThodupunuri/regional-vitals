"""state_rankings.py

Rank states by largest increase or decrease in prevalence for each measure.
Computes the change from the earliest to the latest available year per state,
then ranks states accordingly.

Author: Andrew Kohl
"""

import numpy as np
import pandas as pd


def compute_state_change(
    df: pd.DataFrame,
    measure: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Compute the change in prevalence for each state over a time window.

    For each state, computes the difference between the end-year and
    start-year prevalence values, plus the percentage change.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data with columns: year, state, measure, value, sample_size.
    measure : str
        The measure to filter on (e.g. 'obesity', 'coverage', 'smoking').
    start_year : int or None
        First year of the comparison window.  Defaults to the earliest year in data.
    end_year : int or None
        Last year of the comparison window.  Defaults to the latest year in data.

    Returns
    -------
    DataFrame with columns:
        state, measure, start_year, end_year,
        start_value, end_value, abs_change, pct_change
    Sorted by abs_change descending (largest increase first).
    """
    sub = df[df["measure"] == measure].copy()
    if sub.empty:
        return pd.DataFrame(
            columns=[
                "state", "measure", "start_year", "end_year",
                "start_value", "end_value", "abs_change", "pct_change",
            ]
        )

    if start_year is None:
        start_year = int(sub["year"].min())
    if end_year is None:
        end_year = int(sub["year"].max())

    start_df = (
        sub[sub["year"] == start_year]
        .groupby("state", as_index=False)["value"]
        .mean()
        .rename(columns={"value": "start_value"})
    )
    end_df = (
        sub[sub["year"] == end_year]
        .groupby("state", as_index=False)["value"]
        .mean()
        .rename(columns={"value": "end_value"})
    )

    merged = pd.merge(start_df, end_df, on="state", how="inner")
    merged["measure"] = measure
    merged["start_year"] = start_year
    merged["end_year"] = end_year
    merged["abs_change"] = (merged["end_value"] - merged["start_value"]).round(2)
    merged["pct_change"] = (
        (merged["abs_change"] / merged["start_value"]) * 100
    ).round(2)

    return merged[
        ["state", "measure", "start_year", "end_year",
         "start_value", "end_value", "abs_change", "pct_change"]
    ].sort_values("abs_change", ascending=False).reset_index(drop=True)


def rank_states(
    df: pd.DataFrame,
    measure: str,
    start_year: int | None = None,
    end_year: int | None = None,
    top_n: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ranked tables of states with the largest increase and decrease.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data.
    measure : str
        Measure name (obesity, coverage, smoking).
    start_year, end_year : int or None
        Year window; defaults to data range.
    top_n : int or None
        If provided, return only the top N states in each direction.

    Returns
    -------
    (top_increasers, top_decreasers) : tuple of DataFrames
        Each with a 'rank' column prepended.
    """
    changes = compute_state_change(df, measure, start_year, end_year)
    if changes.empty:
        empty = pd.DataFrame(
            columns=["rank"] + list(changes.columns)
        )
        return empty, empty.copy()

    # Top increasers (largest positive abs_change)
    increasers = changes.sort_values("abs_change", ascending=False).copy()
    increasers.insert(0, "rank", range(1, len(increasers) + 1))

    # Top decreasers (largest negative abs_change, i.e. most improvement)
    decreasers = changes.sort_values("abs_change", ascending=True).copy()
    decreasers.insert(0, "rank", range(1, len(decreasers) + 1))

    if top_n is not None:
        increasers = increasers.head(top_n)
        decreasers = decreasers.head(top_n)

    return increasers.reset_index(drop=True), decreasers.reset_index(drop=True)


def rank_all_measures(
    df: pd.DataFrame,
    measures: list[str] | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    top_n: int = 10,
) -> pd.DataFrame:
    """Rank states across all measures in a single combined table.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data.
    measures : list of str or None
        Measures to rank; defaults to ['obesity', 'coverage', 'smoking'].
    start_year, end_year : int or None
        Year window; defaults to data range.
    top_n : int
        Number of top states per direction per measure.

    Returns
    -------
    DataFrame with columns:
        measure, direction, rank, state, start_value, end_value,
        abs_change, pct_change
    """
    if measures is None:
        measures = ["obesity", "coverage", "smoking"]

    rows = []
    for measure in measures:
        inc, dec = rank_states(df, measure, start_year, end_year, top_n)
        if not inc.empty:
            inc_out = inc.copy()
            inc_out["direction"] = "increase"
            rows.append(inc_out)
        if not dec.empty:
            dec_out = dec.copy()
            dec_out["direction"] = "decrease"
            rows.append(dec_out)

    if not rows:
        return pd.DataFrame()

    combined = pd.concat(rows, ignore_index=True)
    col_order = [
        "measure", "direction", "rank", "state",
        "start_year", "end_year", "start_value", "end_value",
        "abs_change", "pct_change",
    ]
    return combined[[c for c in col_order if c in combined.columns]]
