"""regional_summary.py

Build formatted comparison tables that span all five regions and all three
health indicators.  Every public function returns a plain DataFrame that the
caller can write to CSV, render in a notebook, or format further.
"""

import numpy as np
import pandas as pd

from src.region_mapping import REGIONS, STATE_TO_REGION
from src.trend_analysis import compute_region_year_prevalence, compute_trend_slope

REGION_ORDER = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
MEASURE_ORDER = ["obesity", "coverage", "smoking"]


def _attach_region(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``region`` column derived from the ``state`` column."""
    out = df.copy()
    out["region"] = out["state"].map(STATE_TO_REGION)
    return out[out["region"].notna()]


def _region_trends_all_measures(df: pd.DataFrame) -> pd.DataFrame:
    """Weighted regional prevalence for every region × measure × year."""
    frames = []
    for measure in MEASURE_ORDER:
        ts = compute_region_year_prevalence(df, measure)
        if not ts.empty:
            frames.append(ts)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------------------------
# Table 1 – Latest-year snapshot: regions × measures
# ------------------------------------------------------------------

def latest_year_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot the most recent year of data into a regions × measures matrix.

    Returns a DataFrame with regions as rows, measures as columns,
    and weighted prevalence (%) as values rounded to 1 decimal place.
    """
    rdf = _attach_region(df)
    all_ts = _region_trends_all_measures(rdf)
    if all_ts.empty:
        return pd.DataFrame()

    latest = int(all_ts["year"].max())
    snap = all_ts[all_ts["year"] == latest].copy()

    pivot = snap.pivot_table(
        index="region", columns="measure", values="prevalence_pct", aggfunc="mean"
    )
    pivot = pivot.reindex(index=REGION_ORDER, columns=MEASURE_ORDER)
    pivot = pivot.round(1)
    pivot.index.name = "region"
    pivot.columns.name = None

    pivot.attrs["title"] = f"Regional Prevalence Snapshot ({latest})"
    return pivot


# ------------------------------------------------------------------
# Table 2 – Period change: start-year vs end-year per region/measure
# ------------------------------------------------------------------

def period_change_table(
    df: pd.DataFrame,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Change in weighted prevalence from *start_year* to *end_year*.

    Returns one row per region × measure with columns:
        region, measure, start_prev, end_prev, change_pp, pct_change
    """
    rdf = _attach_region(df)
    all_ts = _region_trends_all_measures(rdf)
    if all_ts.empty:
        return pd.DataFrame()

    if start_year is None:
        start_year = int(all_ts["year"].min())
    if end_year is None:
        end_year = int(all_ts["year"].max())

    start = (
        all_ts[all_ts["year"] == start_year]
        .rename(columns={"prevalence_pct": "start_prev"})
        [["region", "measure", "start_prev"]]
    )
    end = (
        all_ts[all_ts["year"] == end_year]
        .rename(columns={"prevalence_pct": "end_prev"})
        [["region", "measure", "end_prev"]]
    )

    merged = pd.merge(start, end, on=["region", "measure"], how="inner")
    merged["change_pp"] = (merged["end_prev"] - merged["start_prev"]).round(2)
    merged["pct_change"] = (
        (merged["change_pp"] / merged["start_prev"]) * 100
    ).round(2)
    merged["start_year"] = start_year
    merged["end_year"] = end_year

    merged["region"] = pd.Categorical(merged["region"], REGION_ORDER, ordered=True)
    merged["measure"] = pd.Categorical(merged["measure"], MEASURE_ORDER, ordered=True)
    merged = merged.sort_values(["measure", "region"]).reset_index(drop=True)

    col_order = [
        "region", "measure", "start_year", "end_year",
        "start_prev", "end_prev", "change_pp", "pct_change",
    ]
    return merged[col_order]


# ------------------------------------------------------------------
# Table 3 – Trend slopes across all regions × measures
# ------------------------------------------------------------------

def trend_slopes_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Linear-trend slope (pp / year) and R² for every region × measure.

    Returns a wide-format table:
        region | obesity_slope | obesity_r2 | coverage_slope | ...
    """
    rdf = _attach_region(df)
    all_ts = _region_trends_all_measures(rdf)
    if all_ts.empty:
        return pd.DataFrame()

    pieces = []
    for measure in MEASURE_ORDER:
        mts = all_ts[all_ts["measure"] == measure]
        slopes = compute_trend_slope(mts)
        slopes = slopes.rename(columns={
            "slope_pp_yr": f"{measure}_slope",
            "r_squared": f"{measure}_r2",
        })[["region", f"{measure}_slope", f"{measure}_r2"]]
        pieces.append(slopes)

    result = pieces[0]
    for p in pieces[1:]:
        result = pd.merge(result, p, on="region", how="outer")

    result["region"] = pd.Categorical(result["region"], REGION_ORDER, ordered=True)
    result = result.sort_values("region").reset_index(drop=True)
    return result


# ------------------------------------------------------------------
# Table 4 – Regional rankings for a single year
# ------------------------------------------------------------------

def rank_regions_by_year(
    df: pd.DataFrame, year: int | None = None
) -> pd.DataFrame:
    """Rank regions 1-5 for each measure in a given year.

    Lower prevalence is "better" for obesity and smoking (rank 1 = lowest).
    Higher coverage is "better" (rank 1 = highest).

    Returns columns: region, measure, prevalence_pct, rank.
    """
    rdf = _attach_region(df)
    all_ts = _region_trends_all_measures(rdf)
    if all_ts.empty:
        return pd.DataFrame()

    if year is None:
        year = int(all_ts["year"].max())

    snap = all_ts[all_ts["year"] == year].copy()
    rows = []
    for measure in MEASURE_ORDER:
        msub = snap[snap["measure"] == measure].copy()
        ascending = measure != "coverage"
        msub = msub.sort_values("prevalence_pct", ascending=ascending)
        msub["rank"] = range(1, len(msub) + 1)
        rows.append(msub[["region", "measure", "prevalence_pct", "rank"]])

    result = pd.concat(rows, ignore_index=True)
    result["prevalence_pct"] = result["prevalence_pct"].round(1)
    return result


# ------------------------------------------------------------------
# Table 5 – Year-over-year wide matrix per measure
# ------------------------------------------------------------------

def year_by_region_matrix(df: pd.DataFrame, measure: str) -> pd.DataFrame:
    """Wide matrix: rows = regions, columns = years, values = prevalence.

    Useful for quick visual scanning of a single indicator across time.
    """
    rdf = _attach_region(df)
    ts = compute_region_year_prevalence(rdf, measure)
    if ts.empty:
        return pd.DataFrame()

    pivot = ts.pivot_table(
        index="region", columns="year", values="prevalence_pct", aggfunc="mean"
    ).round(1)
    pivot = pivot.reindex(REGION_ORDER)
    pivot.index.name = "region"
    pivot.columns.name = None
    return pivot


# ------------------------------------------------------------------
# Table 6 – Grand summary statistics
# ------------------------------------------------------------------

def grand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """High-level summary per region: mean, min, max prevalence and sample size
    across the full study period, broken out by measure.

    Returns one row per region × measure.
    """
    rdf = _attach_region(df)
    all_ts = _region_trends_all_measures(rdf)
    if all_ts.empty:
        return pd.DataFrame()

    stats = (
        all_ts.groupby(["region", "measure"])
        .agg(
            mean_prev=("prevalence_pct", "mean"),
            min_prev=("prevalence_pct", "min"),
            max_prev=("prevalence_pct", "max"),
            total_samples=("sample_size_total", "sum"),
            years_covered=("year", "nunique"),
        )
        .reset_index()
    )

    for col in ["mean_prev", "min_prev", "max_prev"]:
        stats[col] = stats[col].round(2)

    stats["region"] = pd.Categorical(stats["region"], REGION_ORDER, ordered=True)
    stats["measure"] = pd.Categorical(stats["measure"], MEASURE_ORDER, ordered=True)
    return stats.sort_values(["measure", "region"]).reset_index(drop=True)
