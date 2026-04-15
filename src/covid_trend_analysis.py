"""covid_trend_analysis.py

Utilities for descriptive pre- vs post-COVID trend analysis.

This module extends the repo's existing pre/post average comparisons by adding:
- pre/post slope comparisons
- disruption and recovery metrics
- pre/post volatility comparisons

Methods are descriptive only and do not make causal claims.

Author: Aparna Gana
"""

import numpy as np
import pandas as pd

from src.region_mapping import REGIONS
from src.trend_analysis import compute_region_year_prevalence

# Default regions and measures used by the project
DEFAULT_REGIONS = list(REGIONS.keys())
DEFAULT_MEASURES = ["obesity", "coverage", "smoking"]


def _fit_slope(ts: pd.DataFrame) -> tuple[float, float, int]:
    """Fit a simple linear trend to a time series.

    Parameters
    ----------
    ts : DataFrame
        Must contain columns: year, prevalence_pct.

    Returns
    -------
    tuple
        (slope, intercept, n_points)

        slope and intercept are np.nan if fewer than 2 valid points exist.
    """
    required = {"year", "prevalence_pct"}
    missing = required - set(ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    clean = (
        ts.dropna(subset=["year", "prevalence_pct"])
        .sort_values("year")
        .copy()
    )

    years = clean["year"].to_numpy(dtype=float)
    values = clean["prevalence_pct"].to_numpy(dtype=float)

    if len(years) < 2:
        return np.nan, np.nan, len(years)

    slope, intercept = np.polyfit(years, values, deg=1)
    return float(slope), float(intercept), len(years)


def classify_covid_trend_shift(
    pre_slope: float,
    post_slope: float,
    tol: float = 0.05,
) -> str:
    """Classify how a trend changed from pre-COVID to post-COVID.

    Parameters
    ----------
    pre_slope : float
        Estimated annual slope before COVID.
    post_slope : float
        Estimated annual slope after COVID.
    tol : float
        Tolerance used to treat slopes as approximately flat.

    Returns
    -------
    str
        One of:
        - 'accelerating increase'
        - 'slowing increase'
        - 'stable increase'
        - 'accelerating decline'
        - 'slowing decline'
        - 'stable decline'
        - 'reversal to increase'
        - 'reversal to decline'
        - 'increase emerged'
        - 'decline emerged'
        - 'increase flattened'
        - 'decline flattened'
        - 'stable'
        - 'insufficient data'
        - 'unclear'
    """
    if pd.isna(pre_slope) or pd.isna(post_slope):
        return "insufficient data"

    # both approximately flat
    if abs(pre_slope) <= tol and abs(post_slope) <= tol:
        return "stable"

    # sign reversals
    if pre_slope > tol and post_slope < -tol:
        return "reversal to decline"
    if pre_slope < -tol and post_slope > tol:
        return "reversal to increase"

    # positive / increasing cases
    if pre_slope > tol and post_slope > tol:
        if post_slope > pre_slope + tol:
            return "accelerating increase"
        if post_slope < pre_slope - tol:
            return "slowing increase"
        return "stable increase"

    # negative / declining cases
    if pre_slope < -tol and post_slope < -tol:
        if post_slope < pre_slope - tol:
            return "accelerating decline"
        if post_slope > pre_slope + tol:
            return "slowing decline"
        return "stable decline"

    # transitions involving roughly flat slopes
    if abs(pre_slope) <= tol and post_slope > tol:
        return "increase emerged"
    if abs(pre_slope) <= tol and post_slope < -tol:
        return "decline emerged"
    if pre_slope > tol and abs(post_slope) <= tol:
        return "increase flattened"
    if pre_slope < -tol and abs(post_slope) <= tol:
        return "decline flattened"

    return "unclear"


def compare_pre_post_trend_slopes(
    regional_ts: pd.DataFrame,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
) -> pd.DataFrame:
    """Compare pre-COVID vs post-COVID slopes for each region.

    This complements average-level comparisons by asking whether the
    *rate of change* accelerated, slowed, or reversed after COVID.

    Parameters
    ----------
    regional_ts : DataFrame
        Must contain columns: region, year, prevalence_pct.
    pre : tuple[int, int]
        Inclusive pre-COVID year window.
    post : tuple[int, int]
        Inclusive post-COVID year window.

    Returns
    -------
    DataFrame with columns:
        region, pre_slope, post_slope, slope_change, trend_shift,
        pre_years_n, post_years_n
    """
    required = {"region", "year", "prevalence_pct"}
    missing = required - set(regional_ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows = []
    for region, group in regional_ts.groupby("region"):
        pre_df = group[group["year"].between(pre[0], pre[1])]
        post_df = group[group["year"].between(post[0], post[1])]

        pre_slope, _, pre_n = _fit_slope(pre_df)
        post_slope, _, post_n = _fit_slope(post_df)

        slope_change = (
            round(post_slope - pre_slope, 4)
            if not (pd.isna(pre_slope) or pd.isna(post_slope))
            else np.nan
        )

        rows.append(
            {
                "region": region,
                "pre_slope": round(pre_slope, 4) if not pd.isna(pre_slope) else np.nan,
                "post_slope": round(post_slope, 4) if not pd.isna(post_slope) else np.nan,
                "slope_change": slope_change,
                "trend_shift": classify_covid_trend_shift(pre_slope, post_slope),
                "pre_years_n": pre_n,
                "post_years_n": post_n,
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["trend_shift", "slope_change", "region"], ascending=[True, False, True])
        .reset_index(drop=True)
    )


def compare_pre_post_trend_slopes_by_measure(
    df: pd.DataFrame,
    measures: list[str] | None = None,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
    region_col: str = "region",
    year_col: str = "year",
    measure_col: str = "measure",
    value_col: str = "value",
    sample_size_col: str = "sample_size",
) -> pd.DataFrame:
    """Compare pre/post slope changes for each region and measure.

    Parameters
    ----------
    df : DataFrame
        Long-format DataFrame containing region, year, measure, value,
        and sample size columns.
    measures : list[str] or None
        Measures to include. Defaults to ['obesity', 'coverage', 'smoking'].
    pre : tuple[int, int]
        Inclusive pre-COVID year window.
    post : tuple[int, int]
        Inclusive post-COVID year window.
    region_col : str
        Name of the region column.
    year_col : str
        Name of the year column.
    measure_col : str
        Name of the measure column.
    value_col : str
        Name of the prevalence/value column.
    sample_size_col : str
        Name of the sample size column.

    Returns
    -------
    DataFrame with columns:
        measure, region, pre_slope, post_slope, slope_change, trend_shift,
        pre_years_n, post_years_n
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    required = {region_col, year_col, measure_col, value_col, sample_size_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = (
        df.rename(
            columns={
                region_col: "region",
                year_col: "year",
                measure_col: "measure",
                value_col: "value",
                sample_size_col: "sample_size",
            }
        )
        .copy()
    )

    data = data[
        data["region"].isin(DEFAULT_REGIONS)
        & data["measure"].isin(measures)
    ].copy()

    results = []
    for measure in measures:
        regional_ts = compute_region_year_prevalence(data, measure=measure)
        if regional_ts.empty:
            continue

        comparison = compare_pre_post_trend_slopes(
            regional_ts=regional_ts,
            pre=pre,
            post=post,
        )
        comparison.insert(0, "measure", measure)
        results.append(comparison)

    if not results:
        return pd.DataFrame(
            columns=[
                "measure", "region", "pre_slope", "post_slope",
                "slope_change", "trend_shift", "pre_years_n", "post_years_n",
            ]
        )

    final = pd.concat(results, ignore_index=True)
    final["region"] = pd.Categorical(
        final["region"],
        categories=DEFAULT_REGIONS,
        ordered=True,
    )
    final["measure"] = pd.Categorical(
        final["measure"],
        categories=measures,
        ordered=True,
    )

    return final.sort_values(["measure", "region"]).reset_index(drop=True)


def compute_covid_disruption_metrics(
    regional_ts: pd.DataFrame,
    baseline_year: int = 2019,
    shock_year: int = 2021,
    recovery_year: int = 2023,
) -> pd.DataFrame:
    """Measure COVID disruption and recovery relative to a baseline year.

    Parameters
    ----------
    regional_ts : DataFrame
        Must contain columns: region, year, prevalence_pct.
    baseline_year : int
        Baseline year used as the pre-COVID reference.
    shock_year : int
        Year used to capture the COVID-period disruption.
    recovery_year : int
        Year used to assess whether the region recovered.

    Returns
    -------
    DataFrame with columns:
        region, baseline_year, shock_year, recovery_year,
        baseline_value, shock_value, recovery_value,
        shock_change, recovery_change, recovery_gap, recovered_by_2023
    """
    required = {"region", "year", "prevalence_pct"}
    missing = required - set(regional_ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows = []
    for region, group in regional_ts.groupby("region"):
        baseline = group.loc[group["year"] == baseline_year, "prevalence_pct"]
        shock = group.loc[group["year"] == shock_year, "prevalence_pct"]
        recovery = group.loc[group["year"] == recovery_year, "prevalence_pct"]

        baseline_val = float(baseline.iloc[0]) if not baseline.empty else np.nan
        shock_val = float(shock.iloc[0]) if not shock.empty else np.nan
        recovery_val = float(recovery.iloc[0]) if not recovery.empty else np.nan

        shock_change = (
            round(shock_val - baseline_val, 4)
            if not (pd.isna(baseline_val) or pd.isna(shock_val))
            else np.nan
        )
        recovery_change = (
            round(recovery_val - shock_val, 4)
            if not (pd.isna(recovery_val) or pd.isna(shock_val))
            else np.nan
        )
        recovery_gap = (
            round(recovery_val - baseline_val, 4)
            if not (pd.isna(recovery_val) or pd.isna(baseline_val))
            else np.nan
        )

        recovered_by_2023 = (
            abs(recovery_gap) < 1e-9
            if not pd.isna(recovery_gap)
            else False
        )

        rows.append(
            {
                "region": region,
                "baseline_year": baseline_year,
                "shock_year": shock_year,
                "recovery_year": recovery_year,
                "baseline_value": baseline_val,
                "shock_value": shock_val,
                "recovery_value": recovery_val,
                "shock_change": shock_change,
                "recovery_change": recovery_change,
                "recovery_gap": recovery_gap,
                "recovered_by_2023": recovered_by_2023,
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["shock_change", "region"], ascending=[False, True])
        .reset_index(drop=True)
    )


def compute_covid_disruption_metrics_by_measure(
    df: pd.DataFrame,
    measures: list[str] | None = None,
    baseline_year: int = 2019,
    shock_year: int = 2021,
    recovery_year: int = 2023,
    region_col: str = "region",
    year_col: str = "year",
    measure_col: str = "measure",
    value_col: str = "value",
    sample_size_col: str = "sample_size",
) -> pd.DataFrame:
    """Measure COVID disruption and recovery for each region and measure.

    Parameters
    ----------
    df : DataFrame
        Long-format DataFrame containing region, year, measure, value,
        and sample size columns.
    measures : list[str] or None
        Measures to include. Defaults to ['obesity', 'coverage', 'smoking'].
    baseline_year : int
        Baseline pre-COVID year.
    shock_year : int
        Year used to capture COVID disruption.
    recovery_year : int
        Year used to assess recovery.
    region_col, year_col, measure_col, value_col, sample_size_col : str
        Column names in the input DataFrame.

    Returns
    -------
    DataFrame with columns:
        measure, region, baseline_year, shock_year, recovery_year,
        baseline_value, shock_value, recovery_value,
        shock_change, recovery_change, recovery_gap, recovered_by_2023
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    required = {region_col, year_col, measure_col, value_col, sample_size_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = (
        df.rename(
            columns={
                region_col: "region",
                year_col: "year",
                measure_col: "measure",
                value_col: "value",
                sample_size_col: "sample_size",
            }
        )
        .copy()
    )

    data = data[
        data["region"].isin(DEFAULT_REGIONS)
        & data["measure"].isin(measures)
    ].copy()

    results = []
    for measure in measures:
        regional_ts = compute_region_year_prevalence(data, measure=measure)
        if regional_ts.empty:
            continue

        comparison = compute_covid_disruption_metrics(
            regional_ts=regional_ts,
            baseline_year=baseline_year,
            shock_year=shock_year,
            recovery_year=recovery_year,
        )
        comparison.insert(0, "measure", measure)
        results.append(comparison)

    if not results:
        return pd.DataFrame(
            columns=[
                "measure", "region", "baseline_year", "shock_year", "recovery_year",
                "baseline_value", "shock_value", "recovery_value",
                "shock_change", "recovery_change", "recovery_gap", "recovered_by_2023",
            ]
        )

    final = pd.concat(results, ignore_index=True)
    final["region"] = pd.Categorical(
        final["region"],
        categories=DEFAULT_REGIONS,
        ordered=True,
    )
    final["measure"] = pd.Categorical(
        final["measure"],
        categories=measures,
        ordered=True,
    )

    return final.sort_values(["measure", "region"]).reset_index(drop=True)


def compare_pre_post_volatility(
    regional_ts: pd.DataFrame,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
) -> pd.DataFrame:
    """Compare within-region volatility before and after COVID.

    Volatility is measured here as the standard deviation of annual
    prevalence values within each period.

    Parameters
    ----------
    regional_ts : DataFrame
        Must contain columns: region, year, prevalence_pct.
    pre : tuple[int, int]
        Inclusive pre-COVID year window.
    post : tuple[int, int]
        Inclusive post-COVID year window.

    Returns
    -------
    DataFrame with columns:
        region, pre_std, post_std, volatility_change
    """
    required = {"region", "year", "prevalence_pct"}
    missing = required - set(regional_ts.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows = []
    for region, group in regional_ts.groupby("region"):
        pre_vals = group.loc[
            group["year"].between(pre[0], pre[1]), "prevalence_pct"
        ].dropna()
        post_vals = group.loc[
            group["year"].between(post[0], post[1]), "prevalence_pct"
        ].dropna()

        pre_std = float(np.std(pre_vals.to_numpy(), ddof=0)) if len(pre_vals) > 0 else np.nan
        post_std = float(np.std(post_vals.to_numpy(), ddof=0)) if len(post_vals) > 0 else np.nan
        volatility_change = (
            round(post_std - pre_std, 4)
            if not (pd.isna(pre_std) or pd.isna(post_std))
            else np.nan
        )

        rows.append(
            {
                "region": region,
                "pre_std": round(pre_std, 4) if not pd.isna(pre_std) else np.nan,
                "post_std": round(post_std, 4) if not pd.isna(post_std) else np.nan,
                "volatility_change": volatility_change,
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["volatility_change", "region"], ascending=[False, True])
        .reset_index(drop=True)
    )


def compare_pre_post_volatility_by_measure(
    df: pd.DataFrame,
    measures: list[str] | None = None,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
    region_col: str = "region",
    year_col: str = "year",
    measure_col: str = "measure",
    value_col: str = "value",
    sample_size_col: str = "sample_size",
) -> pd.DataFrame:
    """Compare pre/post volatility for each region and measure.

    Parameters
    ----------
    df : DataFrame
        Long-format DataFrame containing region, year, measure, value,
        and sample size columns.
    measures : list[str] or None
        Measures to include. Defaults to ['obesity', 'coverage', 'smoking'].
    pre : tuple[int, int]
        Inclusive pre-COVID year window.
    post : tuple[int, int]
        Inclusive post-COVID year window.
    region_col, year_col, measure_col, value_col, sample_size_col : str
        Column names in the input DataFrame.

    Returns
    -------
    DataFrame with columns:
        measure, region, pre_std, post_std, volatility_change
    """
    if measures is None:
        measures = DEFAULT_MEASURES

    required = {region_col, year_col, measure_col, value_col, sample_size_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data = (
        df.rename(
            columns={
                region_col: "region",
                year_col: "year",
                measure_col: "measure",
                value_col: "value",
                sample_size_col: "sample_size",
            }
        )
        .copy()
    )

    data = data[
        data["region"].isin(DEFAULT_REGIONS)
        & data["measure"].isin(measures)
    ].copy()

    results = []
    for measure in measures:
        regional_ts = compute_region_year_prevalence(data, measure=measure)
        if regional_ts.empty:
            continue

        comparison = compare_pre_post_volatility(
            regional_ts=regional_ts,
            pre=pre,
            post=post,
        )
        comparison.insert(0, "measure", measure)
        results.append(comparison)

    if not results:
        return pd.DataFrame(
            columns=["measure", "region", "pre_std", "post_std", "volatility_change"]
        )

    final = pd.concat(results, ignore_index=True)
    final["region"] = pd.Categorical(
        final["region"],
        categories=DEFAULT_REGIONS,
        ordered=True,
    )
    final["measure"] = pd.Categorical(
        final["measure"],
        categories=measures,
        ordered=True,
    )

    return final.sort_values(["measure", "region"]).reset_index(drop=True)
