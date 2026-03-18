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


def pivot_regional_trends(regional_ts: pd.DataFrame) -> pd.DataFrame:
    """Reshape long-format regional trends into a wide cross-region matrix.

    Rows = regions, columns = years, values = prevalence_pct.
    This makes it easy to compare all regions side-by-side for any year.

    Parameters
    ----------
    regional_ts : DataFrame
        Output of ``compute_region_year_prevalence``.
        Must contain columns: region, year, prevalence_pct.

    Returns
    -------
    DataFrame with regions as the index and one column per year.
    """
    return regional_ts.pivot_table(
        index="region",
        columns="year",
        values="prevalence_pct",
        aggfunc="mean",
    )


def pivot_measures_by_region(all_trends: pd.DataFrame, year: int) -> pd.DataFrame:
    """Pivot all measures for a single year into a cross-region comparison.

    Produces a table like:
        region     obesity  coverage  smoking
        Midwest      36.0      88.2     17.1
        West         30.2      87.5     12.4
        ...

    Parameters
    ----------
    all_trends : DataFrame
        Combined regional trends for ALL measures.
        Must contain columns: region, year, measure, prevalence_pct.
    year : int
        The year to extract.

    Returns
    -------
    DataFrame with regions as rows and one column per measure,
    sorted by region name.
    """
    subset = all_trends[all_trends["year"] == year]
    return subset.pivot_table(
        index="region",
        columns="measure",
        values="prevalence_pct",
        aggfunc="mean",
    ).sort_index()


def compute_rolling_avg(
    regional_ts: pd.DataFrame, window: int = 3
) -> pd.DataFrame:
    """Compute a rolling-window average of prevalence per region.

    Smooths year-to-year noise to reveal the underlying trend.

    Parameters
    ----------
    regional_ts : DataFrame
        Output of ``compute_region_year_prevalence``.
        Must contain columns: region, year, prevalence_pct.
    window : int
        Number of years in the rolling window (default 3).

    Returns
    -------
    Copy of ``regional_ts`` with an extra column ``rolling_avg``
    containing the centred rolling mean. Rows where the window
    cannot be fully applied have NaN in ``rolling_avg``.
    """
    out = regional_ts.sort_values(["region", "year"]).copy()
    out["rolling_avg"] = (
        out.groupby("region")["prevalence_pct"]
        .transform(lambda s: s.rolling(window, center=True, min_periods=window).mean())
    )
    return out


def compute_convergence(regional_ts: pd.DataFrame) -> pd.DataFrame:
    """Measure whether regions are converging or diverging over time.

    For each year, computes ``np.std`` of prevalence across regions.
    A declining std means regions are converging; rising means diverging.

    Parameters
    ----------
    regional_ts : DataFrame
        Must contain columns: year, prevalence_pct (with multiple regions).

    Returns
    -------
    DataFrame with columns: year, regional_std, trend
        trend is 'converging' if std decreased from first to last year,
        'diverging' otherwise.
    """
    yearly_std = (
        regional_ts.groupby("year")["prevalence_pct"]
        .agg(lambda vals: float(np.std(vals.to_numpy(), ddof=0)))
        .reset_index(name="regional_std")
        .sort_values("year")
    )
    if len(yearly_std) >= 2:
        first = yearly_std["regional_std"].iloc[0]
        last = yearly_std["regional_std"].iloc[-1]
        yearly_std["trend"] = "converging" if last < first else "diverging"
    else:
        yearly_std["trend"] = "insufficient data"
    return yearly_std


def compare_covid_periods(
    regional_ts: pd.DataFrame,
    pre: tuple[int, int] = (2017, 2019),
    post: tuple[int, int] = (2021, 2023),
) -> pd.DataFrame:
    """Compare pre-COVID vs post-COVID prevalence per region.

    Computes the mean prevalence for each period, then merges them
    side-by-side with a delta column.

    Parameters
    ----------
    regional_ts : DataFrame
        Must contain columns: region, year, prevalence_pct.
    pre : tuple
        (start_year, end_year) for the pre-COVID window.
    post : tuple
        (start_year, end_year) for the post-COVID window.

    Returns
    -------
    DataFrame with columns:
        region, pre_avg, post_avg, delta, pct_change
    """
    pre_df = (
        regional_ts[regional_ts["year"].between(pre[0], pre[1])]
        .groupby("region", as_index=False)["prevalence_pct"]
        .mean()
        .rename(columns={"prevalence_pct": "pre_avg"})
    )
    post_df = (
        regional_ts[regional_ts["year"].between(post[0], post[1])]
        .groupby("region", as_index=False)["prevalence_pct"]
        .mean()
        .rename(columns={"prevalence_pct": "post_avg"})
    )
    merged = pd.merge(pre_df, post_df, on="region", how="outer")
    merged["delta"] = (merged["post_avg"] - merged["pre_avg"]).round(2)
    merged["pct_change"] = (
        (merged["delta"] / merged["pre_avg"]) * 100
    ).round(2)
    return merged.sort_values("delta", ascending=False)
