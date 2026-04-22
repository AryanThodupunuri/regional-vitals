"""covid_analysis.py

Dedicated module for COVID-era trend-shift analysis across U.S. regions.

This module goes beyond the basic pre/post comparison in trend_analysis.py
and provides a fuller picture of how the COVID-19 pandemic (2020) disrupted
health trends in obesity, healthcare coverage, and smoking prevalence.

Questions answered:
- Which regions saw the sharpest acceleration or reversal post-COVID?
- Did 2020 act as a structural break in the trend for any measure?
- How quickly did each region recover toward its pre-COVID trajectory?
- Which measure was most disrupted by COVID across all regions?

"""

import numpy as np
import pandas as pd

COVID_YEAR = 2020
PRE_COVID_WINDOW = (2017, 2019)
POST_COVID_WINDOW = (2021, 2023)

VALID_MEASURES = ["obesity", "coverage", "smoking"]
VALID_REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]


def _filter_valid_regions(df: pd.DataFrame, region_col: str = "region") -> pd.DataFrame:
    """Drop non-state rows (territories like GU, PR, VI map to 'Other')."""
    return df[df[region_col].isin(VALID_REGIONS)].copy()


def compute_slope(years: np.ndarray, values: np.ndarray) -> float:
    """Fit a degree-1 polynomial and return the slope (change per year).

    Returns NaN if fewer than 2 data points are provided.
    """
    if len(years) < 2:
        return float("nan")
    coeffs = np.polyfit(years, values, 1)
    return round(float(coeffs[0]), 4)

def compare_trend_slopes(
    regional_ts: pd.DataFrame,
    pre: tuple = PRE_COVID_WINDOW,
    post: tuple = POST_COVID_WINDOW,
) -> pd.DataFrame:
    """Compare the trend slope (pp/year) before vs after COVID per region.
    A positive slope_shift means the measure is rising faster post-COVID.
    A negative slope_shift means it slowed down or reversed post-COVID.

    Parameters
    ----------
    regional_ts : DataFrame with columns: region, year, prevalence_pct.
    pre : (start_year, end_year) for the pre-COVID window.
    post : (start_year, end_year) for the post-COVID window.

    Returns
    -------
    DataFrame with columns: region, pre_slope, post_slope, slope_shift
    """
    required = {"region", "year", "prevalence_pct"}
    missing = required - set(regional_ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    ts = _filter_valid_regions(regional_ts)
    records = []
    for region, group in ts.groupby("region"):
        pre_data = group[group["year"].between(pre[0], pre[1])].sort_values("year")
        post_data = group[group["year"].between(post[0], post[1])].sort_values("year")
        pre_slope = compute_slope(pre_data["year"].values, pre_data["prevalence_pct"].values)
        post_slope = compute_slope(post_data["year"].values, post_data["prevalence_pct"].values)
        slope_shift = (
            round(post_slope - pre_slope, 4)
            if not (np.isnan(pre_slope) or np.isnan(post_slope))
            else float("nan")
        )
        records.append({"region": region, "pre_slope": pre_slope,
                        "post_slope": post_slope, "slope_shift": slope_shift})

    if not records:
        return pd.DataFrame(columns=["region", "pre_slope", "post_slope", "slope_shift"])
    return (pd.DataFrame(records)
            .sort_values("slope_shift", ascending=False)
            .reset_index(drop=True))


def compute_disruption_score(
    regional_ts: pd.DataFrame,
    pre: tuple = PRE_COVID_WINDOW,
    post: tuple = POST_COVID_WINDOW,
) -> pd.DataFrame:
    """Compute a disruption score for each region based on COVID impact.
    Score = abs(delta) + abs(slope_shift) * 10
    Higher score means COVID had a larger measurable effect.

    Parameters
    ----------
    regional_ts : DataFrame with columns: region, year, prevalence_pct.
    pre : pre-COVID window tuple.
    post : post-COVID window tuple.

    Returns
    -------
    DataFrame with columns:
        region, pre_avg, post_avg, delta, slope_shift, disruption_score
    """
    required = {"region", "year", "prevalence_pct"}
    missing = required - set(regional_ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    ts = _filter_valid_regions(regional_ts)
    pre_avg = (ts[ts["year"].between(pre[0], pre[1])]
               .groupby("region")["prevalence_pct"].mean().rename("pre_avg"))
    post_avg = (ts[ts["year"].between(post[0], post[1])]
                .groupby("region")["prevalence_pct"].mean().rename("post_avg"))
    slopes = compare_trend_slopes(ts, pre=pre, post=post).set_index("region")

    result = pd.concat([pre_avg, post_avg], axis=1).reset_index()
    result.columns = ["region", "pre_avg", "post_avg"]
    result["delta"] = (result["post_avg"] - result["pre_avg"]).round(2)
    result["slope_shift"] = result["region"].map(slopes["slope_shift"])
    result["disruption_score"] = (
        result["delta"].abs() + result["slope_shift"].abs() * 10
    ).round(3)
    return result.sort_values("disruption_score", ascending=False).reset_index(drop=True)


def rank_measures_by_disruption(
    all_region_ts_by_measure: dict,
    pre: tuple = PRE_COVID_WINDOW,
    post: tuple = POST_COVID_WINDOW,
) -> pd.DataFrame:
    """Rank measures by average disruption score across all regions.

    Parameters
    ----------
    all_region_ts_by_measure : dict
        Keys are measure names, values are DataFrames with
        region, year, prevalence_pct columns.

    Returns
    -------
    DataFrame with columns:
        measure, avg_disruption_score, max_disruption_region, max_disruption_score
    """
    records = []
    for measure, ts in all_region_ts_by_measure.items():
        if ts.empty:
            continue
        scores = compute_disruption_score(ts, pre=pre, post=post)
        if scores.empty:
            continue
        top_row = scores.iloc[0]
        records.append({
            "measure": measure,
            "avg_disruption_score": round(scores["disruption_score"].mean(), 3),
            "max_disruption_region": top_row["region"],
            "max_disruption_score": top_row["disruption_score"],
        })
    if not records:
        return pd.DataFrame(columns=["measure", "avg_disruption_score", "max_disruption_region", "max_disruption_score"])
    return (pd.DataFrame(records)
            .sort_values("avg_disruption_score", ascending=False)
            .reset_index(drop=True))

def compute_recovery_trajectory(
    regional_ts: pd.DataFrame,
    pre: tuple = PRE_COVID_WINDOW,
) -> pd.DataFrame:
    """Estimate deviation of post-COVID values from the pre-COVID trend line.

    For each year after COVID_YEAR, projects what the pre-COVID trend would
    have predicted and computes gap = actual - projected.

    Gap near zero = recovered to pre-COVID trajectory.
    Positive gap = higher than trend predicted.
    Negative gap = lower than trend predicted.

    Parameters
    ----------
    regional_ts : DataFrame with columns: region, year, prevalence_pct.
    pre : (start_year, end_year) used to fit the pre-COVID trend line.

    Returns
    -------
    DataFrame with columns: region, year, actual, projected, gap
    """
    required = {"region", "year", "prevalence_pct"}
    missing = required - set(regional_ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    ts = _filter_valid_regions(regional_ts)
    records = []
    for region, group in ts.groupby("region"):
        pre_data = group[group["year"].between(pre[0], pre[1])].sort_values("year")
        if len(pre_data) < 2:
            continue
        slope, intercept = np.polyfit(
            pre_data["year"].values, pre_data["prevalence_pct"].values, 1
        )
        for _, row in group[group["year"] > COVID_YEAR].sort_values("year").iterrows():
            projected = round(slope * row["year"] + intercept, 3)
            actual = round(row["prevalence_pct"], 3)
            records.append({
                "region": region,
                "year": int(row["year"]),
                "actual": actual,
                "projected": projected,
                "gap": round(actual - projected, 3),
            })
    if not records:
        return pd.DataFrame(columns=["region", "year", "actual", "projected", "gap"])
    return pd.DataFrame(records).sort_values(["region", "year"]).reset_index(drop=True)

def build_covid_summary_table(
    all_region_ts_by_measure: dict,
    pre: tuple = PRE_COVID_WINDOW,
    post: tuple = POST_COVID_WINDOW,
) -> pd.DataFrame:
    """Build a full summary table of COVID impact across all measures and regions.

    Parameters
    ----------
    all_region_ts_by_measure : dict
        Keys are measure names, values are DataFrames with
        region, year, prevalence_pct columns.

    Returns
    -------
    DataFrame with columns:
        measure, region, pre_avg, post_avg, delta, pct_change,
        pre_slope, post_slope, slope_shift, disruption_score
    """
    all_frames = []
    for measure, ts in all_region_ts_by_measure.items():
        if ts.empty:
            continue
        disruption = compute_disruption_score(ts, pre=pre, post=post)
        if disruption.empty:
            continue
        slopes = compare_trend_slopes(ts, pre=pre, post=post).set_index("region")
        disruption["pct_change"] = (
            (disruption["delta"] / disruption["pre_avg"]) * 100
        ).round(2)
        disruption["pre_slope"] = disruption["region"].map(slopes["pre_slope"])
        disruption["post_slope"] = disruption["region"].map(slopes["post_slope"])
        disruption["slope_shift"] = disruption["region"].map(slopes["slope_shift"])
        disruption.insert(0, "measure", measure)
        all_frames.append(disruption)

    if not all_frames:
        return pd.DataFrame()

    return (
        pd.concat(all_frames, ignore_index=True)
        .sort_values(["measure", "disruption_score"], ascending=[True, False])
        .reset_index(drop=True)
    )