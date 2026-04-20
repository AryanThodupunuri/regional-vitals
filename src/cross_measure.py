"""cross_measure.py

Compare obesity, coverage, and smoking trends within a single region.

This module answers questions like:
- How do different health measures trend together over time in one region?
- Are obesity and coverage correlated at the state level?
- Which measure changed the most in a given region?
- What does a region's health profile look like in a snapshot year?

Author: Aryan Thodupunuri
"""

import numpy as np
import pandas as pd

from src.region_mapping import STATE_TO_REGION

# Default measures the project tracks
DEFAULT_MEASURES = ["obesity", "coverage", "smoking"]


def _add_region(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'region' column if missing, using STATE_TO_REGION mapping."""
    if "region" not in df.columns:
        if "state" not in df.columns:
            raise ValueError("DataFrame must have a 'state' or 'region' column.")
        df = df.copy()
        df["region"] = df["state"].map(STATE_TO_REGION).fillna("Other")
    return df


def compare_measures_over_time(
    df: pd.DataFrame,
    region: str,
    measures: list[str] | None = None,
) -> pd.DataFrame:
    """Compute year-by-year weighted prevalence for multiple measures in one region.

    Returns a long-format table with columns:
        year, measure, prevalence_pct, sample_size_total

    This lets you plot all measures on one chart for a single region.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data with columns: year, state, measure, value, sample_size.
    region : str
        Region to filter on (e.g. 'West').
    measures : list[str] or None
        Measures to include. Defaults to ['obesity', 'coverage', 'smoking'].

    Returns
    -------
    DataFrame with columns: year, measure, prevalence_pct, sample_size_total
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    df = _add_region(df)
    region_df = df[df["region"] == region]

    required = ["year", "measure", "value", "sample_size"]
    missing = [c for c in required if c not in region_df.columns]
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    frames = []
    for m in measures:
        sub = region_df[region_df["measure"] == m].copy()
        if sub.empty:
            continue
        sub["weighted"] = sub["value"] * sub["sample_size"]
        agg = sub.groupby("year", as_index=False).agg(
            weighted_sum=("weighted", "sum"),
            sample_size_total=("sample_size", "sum"),
        )
        agg["prevalence_pct"] = agg["weighted_sum"] / agg["sample_size_total"]
        agg["measure"] = m
        frames.append(agg[["year", "measure", "prevalence_pct", "sample_size_total"]])

    if not frames:
        return pd.DataFrame(columns=["year", "measure", "prevalence_pct", "sample_size_total"])

    return pd.concat(frames, ignore_index=True).sort_values(["measure", "year"])


def compute_measure_correlations(
    df: pd.DataFrame,
    region: str,
    measures: list[str] | None = None,
    level: str = "state",
) -> pd.DataFrame:
    """Compute pairwise Pearson correlations between measures.

    At the *state* level (default), this answers: "In the West, do states with
    high obesity also tend to have low coverage?"

    At the *year* level, this answers: "Over time, do obesity and coverage move
    together in this region?"

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data.
    region : str
        Region to filter on.
    measures : list[str] or None
        Measures to compare. Defaults to ['obesity', 'coverage', 'smoking'].
    level : {'state', 'year'}
        Aggregation level for the correlation.
        - 'state': average each measure per state across all years, then correlate.
        - 'year': average each measure per year across states, then correlate.

    Returns
    -------
    DataFrame — a correlation matrix (measures × measures).
    """
    if measures is None:
        measures = DEFAULT_MEASURES
    if level not in ("state", "year"):
        raise ValueError(f"level must be 'state' or 'year', got {level!r}")

    df = _add_region(df)
    region_df = df[df["region"] == region]

    # Build a pivot: rows = grouping unit (state or year), columns = measures
    sub = region_df[region_df["measure"].isin(measures)].copy()
    if sub.empty:
        return pd.DataFrame(index=measures, columns=measures, dtype=float)

    sub["weighted"] = sub["value"] * sub["sample_size"]

    group_cols = [level, "measure"]
    agg = sub.groupby(group_cols, as_index=False).agg(
        weighted_sum=("weighted", "sum"),
        sample_size_total=("sample_size", "sum"),
    )
    agg["prevalence_pct"] = agg["weighted_sum"] / agg["sample_size_total"]

    pivot = agg.pivot_table(
        index=level,
        columns="measure",
        values="prevalence_pct",
        aggfunc="mean",
    )

    # Only correlate measures that actually appear
    present = [m for m in measures if m in pivot.columns]
    if len(present) < 2:
        return pd.DataFrame(index=measures, columns=measures, dtype=float)

    return pivot[present].corr().round(4)


def rank_measure_changes(
    df: pd.DataFrame,
    region: str,
    measures: list[str] | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Rank measures by largest absolute change in a region over a time window.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data.
    region : str
        Region to filter on.
    measures : list[str] or None
        Measures to compare. Defaults to ['obesity', 'coverage', 'smoking'].
    start_year, end_year : int or None
        Year bounds. Defaults to earliest/latest in data.

    Returns
    -------
    DataFrame with columns:
        measure, start_year, end_year, start_value, end_value,
        abs_change, pct_change, direction
    Sorted by abs(abs_change) descending.
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    trends = compare_measures_over_time(df, region, measures)
    if trends.empty:
        return pd.DataFrame(columns=[
            "measure", "start_year", "end_year", "start_value",
            "end_value", "abs_change", "pct_change", "direction",
        ])

    records = []
    for m in measures:
        m_data = trends[trends["measure"] == m].sort_values("year")
        if m_data.empty:
            continue

        sy = start_year if start_year is not None else int(m_data["year"].min())
        ey = end_year if end_year is not None else int(m_data["year"].max())

        start_row = m_data[m_data["year"] == sy]
        end_row = m_data[m_data["year"] == ey]

        if start_row.empty or end_row.empty:
            # Fall back to closest available years
            start_row = m_data.iloc[[0]]
            end_row = m_data.iloc[[-1]]
            sy = int(start_row["year"].iloc[0])
            ey = int(end_row["year"].iloc[0])

        sv = float(start_row["prevalence_pct"].iloc[0])
        ev = float(end_row["prevalence_pct"].iloc[0])
        abs_chg = round(ev - sv, 4)
        pct_chg = round((abs_chg / sv) * 100, 2) if sv != 0 else float("nan")

        records.append({
            "measure": m,
            "start_year": sy,
            "end_year": ey,
            "start_value": round(sv, 4),
            "end_value": round(ev, 4),
            "abs_change": abs_chg,
            "pct_change": pct_chg,
            "direction": "increase" if abs_chg > 0 else ("decrease" if abs_chg < 0 else "no change"),
        })

    result = pd.DataFrame(records)
    return result.sort_values("abs_change", key=abs, ascending=False).reset_index(drop=True)


def generate_cross_measure_summary(
    df: pd.DataFrame,
    region: str,
    measures: list[str] | None = None,
    year: int | None = None,
) -> dict:
    """Generate a comprehensive cross-measure summary for a region.

    Returns a dictionary with:
    - 'snapshot': prevalence for each measure in the given year
    - 'trends': year-by-year prevalence for all measures
    - 'correlations': pairwise correlations between measures
    - 'changes': measures ranked by largest change over the full period
    - 'region': the region name
    - 'year': the snapshot year

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data.
    region : str
        Region to filter on.
    measures : list[str] or None
        Measures to include. Defaults to ['obesity', 'coverage', 'smoking'].
    year : int or None
        Snapshot year. Defaults to the latest available year.

    Returns
    -------
    dict with keys: region, year, snapshot, trends, correlations, changes.
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    trends = compare_measures_over_time(df, region, measures)
    correlations = compute_measure_correlations(df, region, measures, level="state")
    changes = rank_measure_changes(df, region, measures)

    if year is None and not trends.empty:
        year = int(trends["year"].max())

    # Snapshot: prevalence for each measure in the target year
    if year is not None and not trends.empty:
        snap = trends[trends["year"] == year][["measure", "prevalence_pct"]].copy()
        snap = snap.rename(columns={"prevalence_pct": "value"})
    else:
        snap = pd.DataFrame(columns=["measure", "value"])

    return {
        "region": region,
        "year": year,
        "snapshot": snap,
        "trends": trends,
        "correlations": correlations,
        "changes": changes,
    }


def compare_all_regions_cross_measure(
    df: pd.DataFrame,
    measures: list[str] | None = None,
    year: int | None = None,
) -> pd.DataFrame:
    """Build a table of measure values for ALL regions in a given year.

    Rows = regions, columns = measures.  Useful for a quick "which region
    is highest/lowest on each measure" comparison.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data.
    measures : list[str] or None
        Measures to include. Defaults to ['obesity', 'coverage', 'smoking'].
    year : int or None
        Snapshot year. Defaults to the latest year in data.

    Returns
    -------
    DataFrame with one row per region and one column per measure.
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    df = _add_region(df)
    regions = sorted(df["region"].dropna().unique())

    frames = []
    for region in regions:
        if region == "Other":
            continue
        trends = compare_measures_over_time(df, region, measures)
        if trends.empty:
            continue
        frames.append(trends.assign(region=region))

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    if year is None:
        year = int(combined["year"].max())

    snapshot = combined[combined["year"] == year]
    return snapshot.pivot_table(
        index="region",
        columns="measure",
        values="prevalence_pct",
        aggfunc="mean",
    ).round(4).sort_index()
