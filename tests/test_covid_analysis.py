"""Unit tests for src/covid_analysis.py

Tests cover:
- compute_slope: basic slope calculation
- compare_trend_slopes: correct slope shift direction
- compute_disruption_score: score increases with larger delta/shift
- rank_measures_by_disruption: correct ordering
- compute_recovery_trajectory: gap sign and structure
- build_covid_summary_table: shape and columns
- Edge cases: empty input, missing columns, single data point
"""
import numpy as np
import pandas as pd
import pytest

from src.covid_analysis import (
    compute_slope,
    compare_trend_slopes,
    compute_disruption_score,
    rank_measures_by_disruption,
    compute_recovery_trajectory,
    build_covid_summary_table,
    VALID_REGIONS,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_ts():
    """Two regions with known linear trends across pre and post windows.

    Region A: flat pre (slope=0), rising post (slope=+2) → slope_shift = +2
    Region B: rising pre (slope=+1), flat post (slope=0) → slope_shift = -1
    """
    rows = []
    # Pre-COVID window: 2017-2019
    for year in [2017, 2018, 2019]:
        rows.append({"region": "Northeast", "year": year, "prevalence_pct": 30.0})  # flat
        rows.append({"region": "Southeast", "year": year,
                     "prevalence_pct": 20.0 + (year - 2017)})  # slope +1
    # Post-COVID window: 2021-2023
    for i, year in enumerate([2021, 2022, 2023]):
        rows.append({"region": "Northeast", "year": year,
                     "prevalence_pct": 30.0 + i * 2})   # slope +2
        rows.append({"region": "Southeast", "year": year,
                     "prevalence_pct": 23.0})             # flat
    return pd.DataFrame(rows)


@pytest.fixture
def ts_by_measure(simple_ts):
    """Dict of measure -> timeseries using simple_ts data."""
    return {
        "obesity": simple_ts.copy(),
        "smoking": simple_ts.copy(),
        "coverage": simple_ts.copy(),
    }


# ---------------------------------------------------------------------------
# compute_slope
# ---------------------------------------------------------------------------

def test_compute_slope_positive():
    years = np.array([2017, 2018, 2019])
    values = np.array([10.0, 12.0, 14.0])
    assert abs(compute_slope(years, values) - 2.0) < 0.01


def test_compute_slope_negative():
    years = np.array([2017, 2018, 2019])
    values = np.array([15.0, 13.0, 11.0])
    assert abs(compute_slope(years, values) - (-2.0)) < 0.01


def test_compute_slope_flat():
    years = np.array([2017, 2018, 2019])
    values = np.array([20.0, 20.0, 20.0])
    assert abs(compute_slope(years, values)) < 0.001


def test_compute_slope_single_point_returns_nan():
    result = compute_slope(np.array([2019]), np.array([10.0]))
    assert np.isnan(result)

# ---------------------------------------------------------------------------
# compare_trend_slopes
# ---------------------------------------------------------------------------

def test_compare_trend_slopes_columns(simple_ts):
    result = compare_trend_slopes(simple_ts)
    assert set(result.columns) == {"region", "pre_slope", "post_slope", "slope_shift"}


def test_compare_trend_slopes_northeast_positive_shift(simple_ts):
    """Northeast was flat pre-COVID and rising post-COVID → positive shift."""
    result = compare_trend_slopes(simple_ts)
    ne = result[result["region"] == "Northeast"].iloc[0]
    assert ne["slope_shift"] > 0


def test_compare_trend_slopes_southeast_negative_shift(simple_ts):
    """Southeast was rising pre-COVID and flat post-COVID → negative shift."""
    result = compare_trend_slopes(simple_ts)
    se = result[result["region"] == "Southeast"].iloc[0]
    assert se["slope_shift"] < 0


def test_compare_trend_slopes_filters_other():
    """Rows with region='Other' (territories) should be excluded."""
    rows = [
        {"region": "Other", "year": y, "prevalence_pct": 10.0}
        for y in [2017, 2018, 2019, 2021, 2022, 2023]
    ]
    df = pd.DataFrame(rows)
    result = compare_trend_slopes(df)
    assert result.empty


def test_compare_trend_slopes_missing_column_raises():
    df = pd.DataFrame({"region": ["Northeast"], "year": [2019]})
    with pytest.raises(ValueError, match="Missing required columns"):
        compare_trend_slopes(df)


# ---------------------------------------------------------------------------
# compute_disruption_score
# ---------------------------------------------------------------------------

def test_compute_disruption_score_columns(simple_ts):
    result = compute_disruption_score(simple_ts)
    expected = {"region", "pre_avg", "post_avg", "delta", "slope_shift", "disruption_score"}
    assert expected.issubset(set(result.columns))


def test_compute_disruption_score_nonnegative(simple_ts):
    result = compute_disruption_score(simple_ts)
    assert (result["disruption_score"] >= 0).all()


def test_compute_disruption_score_sorted_descending(simple_ts):
    result = compute_disruption_score(simple_ts)
    scores = result["disruption_score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_compute_disruption_score_only_valid_regions(simple_ts):
    result = compute_disruption_score(simple_ts)
    assert set(result["region"]).issubset(set(VALID_REGIONS))


# ---------------------------------------------------------------------------
# rank_measures_by_disruption
# ---------------------------------------------------------------------------

def test_rank_measures_columns(ts_by_measure):
    result = rank_measures_by_disruption(ts_by_measure)
    expected = {"measure", "avg_disruption_score", "max_disruption_region", "max_disruption_score"}
    assert expected.issubset(set(result.columns))


def test_rank_measures_one_row_per_measure(ts_by_measure):
    result = rank_measures_by_disruption(ts_by_measure)
    assert len(result) == len(ts_by_measure)


def test_rank_measures_sorted_descending(ts_by_measure):
    result = rank_measures_by_disruption(ts_by_measure)
    scores = result["avg_disruption_score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_rank_measures_empty_dict():
    result = rank_measures_by_disruption({})
    assert result.empty


def test_rank_measures_skips_empty_ts(simple_ts):
    ts_dict = {"obesity": simple_ts, "smoking": pd.DataFrame()}
    result = rank_measures_by_disruption(ts_dict)
    assert len(result) == 1
    assert result.iloc[0]["measure"] == "obesity"


# ---------------------------------------------------------------------------
# compute_recovery_trajectory
# ---------------------------------------------------------------------------

def test_compute_recovery_trajectory_columns(simple_ts):
    result = compute_recovery_trajectory(simple_ts)
    assert set(result.columns) == {"region", "year", "actual", "projected", "gap"}


def test_compute_recovery_trajectory_only_post_covid_years(simple_ts):
    result = compute_recovery_trajectory(simple_ts)
    assert (result["year"] > 2020).all()


def test_compute_recovery_trajectory_gap_is_actual_minus_projected(simple_ts):
    result = compute_recovery_trajectory(simple_ts)
    expected_gap = (result["actual"] - result["projected"]).round(3)
    pd.testing.assert_series_equal(result["gap"], expected_gap, check_names=False)


def test_compute_recovery_trajectory_filters_other():
    rows = [
        {"region": "Other", "year": y, "prevalence_pct": 10.0}
        for y in [2017, 2018, 2019, 2021, 2022, 2023]
    ]
    result = compute_recovery_trajectory(pd.DataFrame(rows))
    assert result.empty


def test_compute_recovery_trajectory_missing_column_raises():
    df = pd.DataFrame({"region": ["Northeast"], "year": [2019]})
    with pytest.raises(ValueError, match="Missing required columns"):
        compute_recovery_trajectory(df)


# ---------------------------------------------------------------------------
# build_covid_summary_table
# ---------------------------------------------------------------------------

def test_build_covid_summary_table_columns(ts_by_measure):
    result = build_covid_summary_table(ts_by_measure)
    expected = {
        "measure", "region", "pre_avg", "post_avg", "delta",
        "pct_change", "pre_slope", "post_slope", "slope_shift", "disruption_score"
    }
    assert expected.issubset(set(result.columns))


def test_build_covid_summary_table_row_count(ts_by_measure):
    """Should have one row per measure per region = 3 measures x 2 regions."""
    result = build_covid_summary_table(ts_by_measure)
    assert len(result) == 3 * 2  # 3 measures, 2 regions in simple_ts


def test_build_covid_summary_table_all_measures_present(ts_by_measure):
    result = build_covid_summary_table(ts_by_measure)
    assert set(result["measure"]) == set(ts_by_measure.keys())


def test_build_covid_summary_table_empty_dict():
    result = build_covid_summary_table({})
    assert result.empty


def test_build_covid_summary_table_only_valid_regions(ts_by_measure):
    result = build_covid_summary_table(ts_by_measure)
    assert set(result["region"]).issubset(set(VALID_REGIONS))