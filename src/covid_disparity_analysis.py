"""covid_disparity_analysis.py

Utilities for descriptive COVID-era disparity analysis.

This module examines whether gaps in BRFSS prevalence estimates widened or
narrowed before vs. after the COVID era. While other project modules focus on
overall trends, cross-measure comparisons, or pre/post average changes, this
module focuses specifically on disparity: differences between states within
the same region and differences between each region and the best-performing
region.

The module supports three related questions:

1. Within-region state disparity:
   For each region, measure, and year, how large is the gap between the
   lowest-prevalence and highest-prevalence state?

2. Pre/post COVID disparity change:
   Did the average within-region state gap widen, narrow, or remain roughly
   unchanged after COVID?

3. Regional gap to best performer:
   For each measure and year, how far is each region from the best-performing
   region? For coverage, higher prevalence is treated as better. For obesity
   and smoking, lower prevalence is treated as better.

The functions in this module are descriptive only. They are intended to help
identify patterns in public health disparities, not to make causal claims
about COVID or policy effects.
"""

import numpy as np
import pandas as pd

from src.compute_prevalence import compute_state_prevalence
from src.region_mapping import REGIONS
from src.trend_analysis import compute_region_year_prevalence

DEFAULT_MEASURES = ["obesity", "coverage", "smoking"]
DEFAULT_REGIONS = list(REGIONS.keys())


def _higher_is_better(measure: str) -> bool:
    """Return whether higher prevalence is preferable for a measure."""
    return measure == "coverage"


def _classify_change(change: float, tol: float = 0.05) -> str:
    """Classify whether a gap widened, narrowed, or stayed roughly unchanged."""
    if pd.isna(change):
        return "insufficient data"
    if change > tol:
        return "widened"
    if change < -tol:
        return "narrowed"
    return "unchanged"


def compute_state_disparity_by_region(
    df: pd.DataFrame,
    measures: list[str] | None = None,
) -> pd.DataFrame:
    """Compute within-region state disparity for each year and measure.

    For each region, measure, and year, this function identifies the states
    with the lowest and highest prevalence and computes the gap between them.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data with columns:
        year, state, region, measure, value, sample_size.
    measures : list[str] or None
        Measures to include. Defaults to obesity, coverage, and smoking.

    Returns
    -------
    DataFrame with columns:
        region, measure, year, min_state, max_state,
        min_value, max_value, state_gap
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    required = {"year", "state", "region", "measure", "value", "sample_size"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = df[
        df["region"].isin(DEFAULT_REGIONS)
        & df["measure"].isin(measures)
    ].copy()

    if data.empty:
        return pd.DataFrame(
            columns=[
                "region", "measure", "year", "min_state", "max_state",
                "min_value", "max_value", "state_gap",
            ]
        )

    state_prev = compute_state_prevalence(data)
    state_prev = state_prev.merge(
        data[["state", "region"]].drop_duplicates(),
        on="state",
        how="left",
    )

    rows = []
    for (region, measure, year), group in state_prev.groupby(["region", "measure", "year"]):
        group = group.dropna(subset=["prevalence_pct"])
        if group.empty:
            continue

        min_idx = group["prevalence_pct"].idxmin()
        max_idx = group["prevalence_pct"].idxmax()

        min_row = group.loc[min_idx]
        max_row = group.loc[max_idx]

        min_value = float(min_row["prevalence_pct"])
        max_value = float(max_row["prevalence_pct"])

        rows.append(
            {
                "region": region,
                "measure": measure,
                "year": int(year),
                "min_state": min_row["state"],
                "max_state": max_row["state"],
                "min_value": round(min_value, 4),
                "max_value": round(max_value, 4),
                "state_gap": round(max_value - min_value, 4),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["measure", "region", "year"])
        .reset_index(drop=True)
    )


def compare_pre_post_disparity(
    disparity_df: pd.DataFrame,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
) -> pd.DataFrame:
    """Compare average within-region state disparity before vs. after COVID.

    Parameters
    ----------
    disparity_df : DataFrame
        Output of compute_state_disparity_by_region.
    pre : tuple[int, int]
        Inclusive pre-COVID year window.
    post : tuple[int, int]
        Inclusive post-COVID year window.

    Returns
    -------
    DataFrame with columns:
        region, measure, pre_gap_avg, post_gap_avg,
        gap_change, gap_direction
    """
    required = {"region", "measure", "year", "state_gap"}
    missing = required - set(disparity_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    pre_df = (
        disparity_df[disparity_df["year"].between(pre[0], pre[1])]
        .groupby(["region", "measure"], as_index=False)["state_gap"]
        .mean()
        .rename(columns={"state_gap": "pre_gap_avg"})
    )

    post_df = (
        disparity_df[disparity_df["year"].between(post[0], post[1])]
        .groupby(["region", "measure"], as_index=False)["state_gap"]
        .mean()
        .rename(columns={"state_gap": "post_gap_avg"})
    )

    merged = pd.merge(pre_df, post_df, on=["region", "measure"], how="outer")
    merged["gap_change"] = (merged["post_gap_avg"] - merged["pre_gap_avg"]).round(4)
    merged["gap_direction"] = merged["gap_change"].apply(_classify_change)

    return (
        merged.sort_values(["measure", "gap_change"], ascending=[True, False])
        .reset_index(drop=True)
    )


def compute_regional_gap_to_best(
    df: pd.DataFrame,
    measures: list[str] | None = None,
) -> pd.DataFrame:
    """Compute each region's gap to the best-performing region by year.

    For coverage, the best region is the one with the highest prevalence.
    For obesity and smoking, the best region is the one with the lowest
    prevalence.

    Parameters
    ----------
    df : DataFrame
        Combined BRFSS data with columns:
        year, region, measure, value, sample_size.
    measures : list[str] or None
        Measures to include. Defaults to obesity, coverage, and smoking.

    Returns
    -------
    DataFrame with columns:
        measure, year, region, best_region,
        region_value, best_value, gap_to_best
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    required = {"year", "region", "measure", "value", "sample_size"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = df[
        df["region"].isin(DEFAULT_REGIONS)
        & df["measure"].isin(measures)
    ].copy()

    results = []
    for measure in measures:
        regional_ts = compute_region_year_prevalence(data, measure=measure)
        if regional_ts.empty:
            continue

        for year, group in regional_ts.groupby("year"):
            group = group.dropna(subset=["prevalence_pct"])
            if group.empty:
                continue

            if _higher_is_better(measure):
                best_idx = group["prevalence_pct"].idxmax()
            else:
                best_idx = group["prevalence_pct"].idxmin()

            best_row = group.loc[best_idx]
            best_region = best_row["region"]
            best_value = float(best_row["prevalence_pct"])

            for _, row in group.iterrows():
                region_value = float(row["prevalence_pct"])

                if _higher_is_better(measure):
                    gap = best_value - region_value
                else:
                    gap = region_value - best_value

                results.append(
                    {
                        "measure": measure,
                        "year": int(year),
                        "region": row["region"],
                        "best_region": best_region,
                        "region_value": round(region_value, 4),
                        "best_value": round(best_value, 4),
                        "gap_to_best": round(gap, 4),
                    }
                )

    return (
        pd.DataFrame(results)
        .sort_values(["measure", "year", "region"])
        .reset_index(drop=True)
    )


def compare_pre_post_gap_to_best(
    gap_df: pd.DataFrame,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
) -> pd.DataFrame:
    """Compare each region's gap to the best region before vs. after COVID.

    Parameters
    ----------
    gap_df : DataFrame
        Output of compute_regional_gap_to_best.
    pre : tuple[int, int]
        Inclusive pre-COVID year window.
    post : tuple[int, int]
        Inclusive post-COVID year window.

    Returns
    -------
    DataFrame with columns:
        measure, region, pre_gap_to_best, post_gap_to_best,
        gap_change, relative_position
    """
    required = {"measure", "region", "year", "gap_to_best"}
    missing = required - set(gap_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    pre_df = (
        gap_df[gap_df["year"].between(pre[0], pre[1])]
        .groupby(["measure", "region"], as_index=False)["gap_to_best"]
        .mean()
        .rename(columns={"gap_to_best": "pre_gap_to_best"})
    )

    post_df = (
        gap_df[gap_df["year"].between(post[0], post[1])]
        .groupby(["measure", "region"], as_index=False)["gap_to_best"]
        .mean()
        .rename(columns={"gap_to_best": "post_gap_to_best"})
    )

    merged = pd.merge(pre_df, post_df, on=["measure", "region"], how="outer")
    merged["gap_change"] = (
        merged["post_gap_to_best"] - merged["pre_gap_to_best"]
    ).round(4)

    merged["relative_position"] = merged["gap_change"].apply(
        lambda x: (
            "farther from best"
            if x > 0.05
            else "closer to best"
            if x < -0.05
            else "unchanged"
            if not pd.isna(x)
            else "insufficient data"
        )
    )

    return (
        merged.sort_values(["measure", "gap_change"], ascending=[True, False])
        .reset_index(drop=True)
    )


def rank_regions_by_disparity_change(
    disparity_change_df: pd.DataFrame,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Rank regions by how much within-region disparity changed after COVID.

    Parameters
    ----------
    disparity_change_df : DataFrame
        Output of compare_pre_post_disparity.
    top_n : int or None
        If provided, return only the top N regions per measure.

    Returns
    -------
    DataFrame with columns:
        measure, rank, region, pre_gap_avg, post_gap_avg,
        gap_change, gap_direction
    """
    required = {
        "region", "measure", "pre_gap_avg", "post_gap_avg",
        "gap_change", "gap_direction",
    }
    missing = required - set(disparity_change_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows = []
    for measure, group in disparity_change_df.groupby("measure"):
        ranked = group.sort_values("gap_change", ascending=False).copy()
        ranked.insert(0, "rank", range(1, len(ranked) + 1))

        if top_n is not None:
            ranked = ranked.head(top_n)

        rows.append(ranked)

    if not rows:
        return pd.DataFrame(
            columns=[
                "measure", "rank", "region", "pre_gap_avg", "post_gap_avg",
                "gap_change", "gap_direction",
            ]
        )

    combined = pd.concat(rows, ignore_index=True)

    col_order = [
        "measure", "rank", "region", "pre_gap_avg", "post_gap_avg",
        "gap_change", "gap_direction",
    ]

    return combined[[c for c in col_order if c in combined.columns]]
