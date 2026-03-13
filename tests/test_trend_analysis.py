"""Unit tests for src/trend_analysis.py — tests actual computation correctness."""
import numpy as np
import pandas as pd
import pytest

from src.trend_analysis import (
    compare_covid_periods,
    compute_convergence,
    compute_region_year_prevalence,
    compute_rolling_avg,
    compute_trend_slope,
    pivot_measures_by_region,
    pivot_regional_trends,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_ts():
    """Two regions with perfectly linear trends, equal sample sizes."""
    rows = []
    for year in range(2011, 2014):
        rows.append({"region": "A", "year": year, "measure": "obesity",
                     "prevalence_pct": 10.0 + (year - 2011) * 2.0,  # slope = +2
                     "sample_size_total": 100})
        rows.append({"region": "B", "year": year, "measure": "obesity",
                     "prevalence_pct": 30.0 - (year - 2011) * 1.0,  # slope = -1
                     "sample_size_total": 100})
    return pd.DataFrame(rows)


@pytest.fixture
def multi_measure_ts():
    """Single region, two measures, one year — for pivot tests."""
    return pd.DataFrame([
        {"region": "A", "year": 2023, "measure": "obesity",  "prevalence_pct": 30.0},
        {"region": "A", "year": 2023, "measure": "smoking",  "prevalence_pct": 15.0},
        {"region": "B", "year": 2023, "measure": "obesity",  "prevalence_pct": 25.0},
        {"region": "B", "year": 2023, "measure": "smoking",  "prevalence_pct": 12.0},
    ])


# ---------------------------------------------------------------------------
# compute_trend_slope
# ---------------------------------------------------------------------------

def test_slope_perfect_linear(simple_ts):
    result = compute_trend_slope(simple_ts)
    a = result[result["region"] == "A"].iloc[0]
    b = result[result["region"] == "B"].iloc[0]

    assert abs(a["slope_pp_yr"] - 2.0) < 0.01
    assert abs(b["slope_pp_yr"] - (-1.0)) < 0.01


def test_slope_r_squared_perfect(simple_ts):
    result = compute_trend_slope(simple_ts)
    # Perfect linear data → R² = 1.0
    for _, row in result.iterrows():
        assert abs(row["r_squared"] - 1.0) < 1e-6


def test_slope_sorted_descending(simple_ts):
    result = compute_trend_slope(simple_ts)
    slopes = result["slope_pp_yr"].tolist()
    assert slopes == sorted(slopes, reverse=True)


def test_slope_single_point():
    """Only one data point → slope should be NaN."""
    ts = pd.DataFrame([{"region": "X", "year": 2020, "prevalence_pct": 25.0}])
    result = compute_trend_slope(ts)
    assert np.isnan(result.iloc[0]["slope_pp_yr"])


# ---------------------------------------------------------------------------
# compute_convergence
# ---------------------------------------------------------------------------

def test_convergence_diverging(simple_ts):
    """A starts at 10, B starts at 30 (std=10); A ends at 14, B ends at 28 (std=7).
    std decreases → converging."""
    result = compute_convergence(simple_ts)
    assert result["trend"].iloc[0] == "converging"


def test_convergence_diverging_case():
    ts = pd.DataFrame([
        {"region": "A", "year": 2011, "prevalence_pct": 20.0},
        {"region": "B", "year": 2011, "prevalence_pct": 20.0},
        {"region": "A", "year": 2012, "prevalence_pct": 10.0},
        {"region": "B", "year": 2012, "prevalence_pct": 30.0},
    ])
    result = compute_convergence(ts)
    assert result["trend"].iloc[0] == "diverging"


def test_convergence_columns(simple_ts):
    result = compute_convergence(simple_ts)
    assert set(result.columns) >= {"year", "regional_std", "trend"}


def test_convergence_single_year():
    ts = pd.DataFrame([
        {"region": "A", "year": 2020, "prevalence_pct": 25.0},
        {"region": "B", "year": 2020, "prevalence_pct": 30.0},
    ])
    result = compute_convergence(ts)
    assert result["trend"].iloc[0] == "insufficient data"


# ---------------------------------------------------------------------------
# compare_covid_periods
# ---------------------------------------------------------------------------

def test_covid_delta_calculation():
    ts = pd.DataFrame([
        {"region": "A", "year": 2017, "prevalence_pct": 20.0},
        {"region": "A", "year": 2018, "prevalence_pct": 20.0},
        {"region": "A", "year": 2019, "prevalence_pct": 20.0},
        {"region": "A", "year": 2021, "prevalence_pct": 25.0},
        {"region": "A", "year": 2022, "prevalence_pct": 25.0},
        {"region": "A", "year": 2023, "prevalence_pct": 25.0},
    ])
    result = compare_covid_periods(ts)
    row = result[result["region"] == "A"].iloc[0]
    assert row["pre_avg"] == pytest.approx(20.0)
    assert row["post_avg"] == pytest.approx(25.0)
    assert row["delta"] == pytest.approx(5.0)
    assert row["pct_change"] == pytest.approx(25.0)


def test_covid_sorted_by_delta_descending():
    ts = pd.DataFrame([
        {"region": "A", "year": 2018, "prevalence_pct": 10.0},
        {"region": "A", "year": 2022, "prevalence_pct": 20.0},  # delta=10
        {"region": "B", "year": 2018, "prevalence_pct": 30.0},
        {"region": "B", "year": 2022, "prevalence_pct": 31.0},  # delta=1
    ])
    result = compare_covid_periods(ts, pre=(2018, 2018), post=(2022, 2022))
    assert result["region"].iloc[0] == "A"


# ---------------------------------------------------------------------------
# compute_rolling_avg
# ---------------------------------------------------------------------------

def test_rolling_avg_center_window():
    ts = pd.DataFrame([
        {"region": "A", "year": y, "prevalence_pct": float(y), "measure": "obesity"}
        for y in range(2011, 2016)
    ])
    result = compute_rolling_avg(ts, window=3)
    # Middle year (2013) should be average of 2012, 2013, 2014
    mid = result[result["year"] == 2013].iloc[0]
    assert mid["rolling_avg"] == pytest.approx(2013.0)


def test_rolling_avg_edge_nan():
    ts = pd.DataFrame([
        {"region": "A", "year": y, "prevalence_pct": float(y), "measure": "obesity"}
        for y in range(2011, 2016)
    ])
    result = compute_rolling_avg(ts, window=3)
    # First and last years can't fill the centered window → NaN
    assert np.isnan(result[result["year"] == 2011].iloc[0]["rolling_avg"])
    assert np.isnan(result[result["year"] == 2015].iloc[0]["rolling_avg"])


# ---------------------------------------------------------------------------
# pivot_regional_trends
# ---------------------------------------------------------------------------

def test_pivot_regional_trends_shape(simple_ts):
    result = pivot_regional_trends(simple_ts)
    assert set(result.index) == {"A", "B"}
    assert set(result.columns) == {2011, 2012, 2013}


# ---------------------------------------------------------------------------
# pivot_measures_by_region
# ---------------------------------------------------------------------------

def test_pivot_measures_by_region(multi_measure_ts):
    result = pivot_measures_by_region(multi_measure_ts, year=2023)
    assert set(result.index) == {"A", "B"}
    assert "obesity" in result.columns
    assert "smoking" in result.columns
    assert result.loc["A", "obesity"] == pytest.approx(30.0)
    assert result.loc["B", "smoking"] == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# compute_region_year_prevalence
# ---------------------------------------------------------------------------

def test_prevalence_weighted_average():
    """Verify weighted mean: (10*100 + 20*100) / 200 = 15."""
    df = pd.DataFrame([
        {"year": 2020, "region": "A", "measure": "obesity", "value": 10.0, "sample_size": 100},
        {"year": 2020, "region": "A", "measure": "obesity", "value": 20.0, "sample_size": 100},
    ])
    result = compute_region_year_prevalence(df, "obesity")
    assert result.iloc[0]["prevalence_pct"] == pytest.approx(15.0)


def test_prevalence_empty_for_unknown_measure():
    df = pd.DataFrame([
        {"year": 2020, "region": "A", "measure": "obesity", "value": 10.0, "sample_size": 100},
    ])
    result = compute_region_year_prevalence(df, "nonexistent")
    assert result.empty
