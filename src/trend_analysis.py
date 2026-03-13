"""trend_analysis.py

Utilities for simple descriptive trend calculations.
This module intentionally keeps methods simple and descriptive (no causal modeling).
"""

import numpy as np
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


def compute_trend_slope(regional_ts: pd.DataFrame) -> pd.DataFrame:
    """Fit a linear trend to each region's prevalence time series.

    Uses ``np.polyfit(years, values, deg=1)`` — ordinary least-squares
    polynomial fit of degree 1 — to estimate the average annual change
    (percentage points per year) for each region.

    Parameters
    ----------
    regional_ts : DataFrame
        Output of ``compute_region_year_prevalence``.
        Must contain columns: region, year, prevalence_pct.

    Returns
    -------
    DataFrame with columns:
        region          — region name
        slope_pp_yr     — estimated change in prevalence (pp) per year
        intercept       — fitted value at year 0 (use for prediction only)
        r_squared       — coefficient of determination (fit quality, 0–1)
        years_n         — number of data points used in the fit
    """
    records = []
    for region, group in regional_ts.groupby("region"):
        group = group.sort_values("year")
        years = group["year"].to_numpy(dtype=float)
        values = group["prevalence_pct"].to_numpy(dtype=float)

        # Need at least 2 points for a meaningful slope
        if len(years) < 2:
            records.append(
                {
                    "region": region,
                    "slope_pp_yr": np.nan,
                    "intercept": np.nan,
                    "r_squared": np.nan,
                    "years_n": len(years),
                }
            )
            continue

        # np.polyfit returns [slope, intercept] for deg=1
        slope, intercept = np.polyfit(years, values, deg=1)

        # R² = 1 - SS_res / SS_tot
        fitted = slope * years + intercept
        ss_res = np.sum((values - fitted) ** 2)
        ss_tot = np.sum((values - np.mean(values)) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

        records.append(
            {
                "region": region,
                "slope_pp_yr": round(float(slope), 4),
                "intercept": round(float(intercept), 4),
                "r_squared": round(float(r_squared), 4),
                "years_n": len(years),
            }
        )

    return pd.DataFrame(records).sort_values("slope_pp_yr", ascending=False)
