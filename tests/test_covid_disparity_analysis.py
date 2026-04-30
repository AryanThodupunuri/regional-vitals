"""Unit tests for src/covid_disparity_analysis.py."""

import pandas as pd
import pytest

from src.covid_disparity_analysis import (
    _classify_change,
    _higher_is_better,
    compare_pre_post_disparity,
    compare_pre_post_gap_to_best,
    compute_regional_gap_to_best,
    compute_state_disparity_by_region,
    rank_regions_by_disparity_change,
)


@pytest.fixture
def sample_brfss_df():
    """Small BRFSS-style dataset with two regions, two states each, and two measures."""
    return pd.DataFrame([
        # Coverage: higher is better
        {"year": 2017, "state": "VA", "region": "Southeast", "measure": "coverage", "value": 80.0, "sample_size": 100},
        {"year": 2017, "state": "NC", "region": "Southeast", "measure": "coverage", "value": 90.0, "sample_size": 100},
        {"year": 2021, "state": "VA", "region": "Southeast", "measure": "coverage", "value": 82.0, "sample_size": 100},
        {"year": 2021, "state": "NC", "region": "Southeast", "measure": "coverage", "value": 96.0, "sample_size": 100},

        {"year": 2017, "state": "CA", "region": "West", "measure": "coverage", "value": 95.0, "sample_size": 100},
        {"year": 2017, "state": "OR", "region": "West", "measure": "coverage", "value": 85.0, "sample_size": 100},
        {"year": 2021, "state": "CA", "region": "West", "measure": "coverage", "value": 94.0, "sample_size": 100},
        {"year": 2021, "state": "OR", "region": "West", "measure": "coverage", "value": 86.0, "sample_size": 100},

        # Obesity: lower is better
        {"year": 2017, "state": "VA", "region": "Southeast", "measure": "obesity", "value": 30.0, "sample_size": 100},
        {"year": 2017, "state": "NC", "region": "Southeast", "measure": "obesity", "value": 35.0, "sample_size": 100},
        {"year": 2021, "state": "VA", "region": "Southeast", "measure": "obesity", "value": 32.0, "sample_size": 100},
        {"year": 2021, "state": "NC", "region": "Southeast", "measure": "obesity", "value": 42.0, "sample_size": 100},

        {"year": 2017, "state": "CA", "region": "West", "measure": "obesity", "value": 25.0, "sample_size": 100},
        {"year": 2017, "state": "OR", "region": "West", "measure": "obesity", "value": 30.0, "sample_size": 100},
        {"year": 2021, "state": "CA", "region": "West", "measure": "obesity", "value": 26.0, "sample_size": 100},
        {"year": 2021, "state": "OR", "region": "West", "measure": "obesity", "value": 32.0, "sample_size": 100},
    ])


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def test_higher_is_better():
    assert _higher_is_better("coverage") is True
    assert _higher_is_better("obesity") is False
    assert _higher_is_better("smoking") is False


def test_classify_change():
    assert _classify_change(1.0) == "widened"
    assert _classify_change(-1.0) == "narrowed"
    assert _classify_change(0.0) == "unchanged"
    assert _classify_change(float("nan")) == "insufficient data"


# ---------------------------------------------------------------------------
# compute_state_disparity_by_region
# ---------------------------------------------------------------------------

def test_compute_state_disparity_by_region_basic(sample_brfss_df):
    result = compute_state_disparity_by_region(sample_brfss_df, measures=["coverage"])

    row = result[
        (result["region"] == "Southeast")
        & (result["measure"] == "coverage")
        & (result["year"] == 2017)
    ].iloc[0]

    assert row["min_state"] == "VA"
    assert row["max_state"] == "NC"
    assert row["min_value"] == pytest.approx(80.0)
    assert row["max_value"] == pytest.approx(90.0)
    assert row["state_gap"] == pytest.approx(10.0)


def test_compute_state_disparity_by_region_weighted_average():
    df = pd.DataFrame([
        {"year": 2021, "state": "VA", "region": "Southeast", "measure": "coverage", "value": 80.0, "sample_size": 100},
        {"year": 2021, "state": "VA", "region": "Southeast", "measure": "coverage", "value": 100.0, "sample_size": 300},
        {"year": 2021, "state": "NC", "region": "Southeast", "measure": "coverage", "value": 90.0, "sample_size": 100},
    ])

    result = compute_state_disparity_by_region(df, measures=["coverage"])
    row = result.iloc[0]

    # VA weighted average = (80*100 + 100*300) / 400 = 95
    # NC = 90, so gap = 95 - 90 = 5
    assert row["state_gap"] == pytest.approx(5.0)
    assert set([row["min_state"], row["max_state"]]) == {"VA", "NC"}


def test_compute_state_disparity_by_region_empty_result(sample_brfss_df):
    result = compute_state_disparity_by_region(sample_brfss_df, measures=["smoking"])
    assert result.empty


def test_compute_state_disparity_by_region_missing_columns_raises(sample_brfss_df):
    bad_df = sample_brfss_df.drop(columns=["sample_size"])

    with pytest.raises(ValueError):
        compute_state_disparity_by_region(bad_df)


# ---------------------------------------------------------------------------
# compare_pre_post_disparity
# ---------------------------------------------------------------------------

def test_compare_pre_post_disparity(sample_brfss_df):
    disparity = compute_state_disparity_by_region(sample_brfss_df, measures=["coverage"])
    result = compare_pre_post_disparity(disparity, pre=(2017, 2017), post=(2021, 2021))

    row = result[
        (result["region"] == "Southeast")
        & (result["measure"] == "coverage")
    ].iloc[0]

    assert row["pre_gap_avg"] == pytest.approx(10.0)
    assert row["post_gap_avg"] == pytest.approx(14.0)
    assert row["gap_change"] == pytest.approx(4.0)
    assert row["gap_direction"] == "widened"


def test_compare_pre_post_disparity_narrowed(sample_brfss_df):
    disparity = compute_state_disparity_by_region(sample_brfss_df, measures=["coverage"])
    result = compare_pre_post_disparity(disparity, pre=(2017, 2017), post=(2021, 2021))

    row = result[
        (result["region"] == "West")
        & (result["measure"] == "coverage")
    ].iloc[0]

    assert row["pre_gap_avg"] == pytest.approx(10.0)
    assert row["post_gap_avg"] == pytest.approx(8.0)
    assert row["gap_change"] == pytest.approx(-2.0)
    assert row["gap_direction"] == "narrowed"


def test_compare_pre_post_disparity_missing_columns_raises():
    bad_df = pd.DataFrame({"region": ["A"], "year": [2021]})

    with pytest.raises(ValueError):
        compare_pre_post_disparity(bad_df)


# ---------------------------------------------------------------------------
# compute_regional_gap_to_best
# ---------------------------------------------------------------------------

def test_compute_regional_gap_to_best_coverage_higher_is_better(sample_brfss_df):
    result = compute_regional_gap_to_best(sample_brfss_df, measures=["coverage"])

    southeast = result[
        (result["measure"] == "coverage")
        & (result["year"] == 2017)
        & (result["region"] == "Southeast")
    ].iloc[0]

    west = result[
        (result["measure"] == "coverage")
        & (result["year"] == 2017)
        & (result["region"] == "West")
    ].iloc[0]

    assert west["gap_to_best"] == pytest.approx(0.0)
    assert southeast["best_region"] == "West"
    assert southeast["gap_to_best"] == pytest.approx(5.0)


def test_compute_regional_gap_to_best_obesity_lower_is_better(sample_brfss_df):
    result = compute_regional_gap_to_best(sample_brfss_df, measures=["obesity"])

    southeast = result[
        (result["measure"] == "obesity")
        & (result["year"] == 2017)
        & (result["region"] == "Southeast")
    ].iloc[0]

    west = result[
        (result["measure"] == "obesity")
        & (result["year"] == 2017)
        & (result["region"] == "West")
    ].iloc[0]

    assert west["gap_to_best"] == pytest.approx(0.0)
    assert southeast["best_region"] == "West"
    assert southeast["gap_to_best"] == pytest.approx(5.0)


def test_compute_regional_gap_to_best_missing_columns_raises(sample_brfss_df):
    bad_df = sample_brfss_df.drop(columns=["region"])

    with pytest.raises(ValueError):
        compute_regional_gap_to_best(bad_df)


# ---------------------------------------------------------------------------
# compare_pre_post_gap_to_best
# ---------------------------------------------------------------------------

def test_compare_pre_post_gap_to_best_closer_to_best(sample_brfss_df):
    gap_df = compute_regional_gap_to_best(sample_brfss_df, measures=["coverage"])
    result = compare_pre_post_gap_to_best(gap_df, pre=(2017, 2017), post=(2021, 2021))

    row = result[
        (result["measure"] == "coverage")
        & (result["region"] == "Southeast")
    ].iloc[0]

    assert row["pre_gap_to_best"] == pytest.approx(5.0)
    assert row["post_gap_to_best"] == pytest.approx(1.0)
    assert row["gap_change"] == pytest.approx(-4.0)
    assert row["relative_position"] == "closer to best"


def test_compare_pre_post_gap_to_best_unchanged_for_best_region(sample_brfss_df):
    gap_df = compute_regional_gap_to_best(sample_brfss_df, measures=["coverage"])
    result = compare_pre_post_gap_to_best(gap_df, pre=(2017, 2017), post=(2021, 2021))

    row = result[
        (result["measure"] == "coverage")
        & (result["region"] == "West")
    ].iloc[0]

    assert row["pre_gap_to_best"] == pytest.approx(0.0)
    assert row["post_gap_to_best"] == pytest.approx(0.0)
    assert row["gap_change"] == pytest.approx(0.0)
    assert row["relative_position"] == "unchanged"


def test_compare_pre_post_gap_to_best_missing_columns_raises():
    bad_df = pd.DataFrame({"measure": ["coverage"], "region": ["West"]})

    with pytest.raises(ValueError):
        compare_pre_post_gap_to_best(bad_df)


# ---------------------------------------------------------------------------
# rank_regions_by_disparity_change
# ---------------------------------------------------------------------------

def test_rank_regions_by_disparity_change(sample_brfss_df):
    disparity = compute_state_disparity_by_region(sample_brfss_df, measures=["coverage"])
    change = compare_pre_post_disparity(disparity, pre=(2017, 2017), post=(2021, 2021))

    result = rank_regions_by_disparity_change(change)

    first = result[result["measure"] == "coverage"].iloc[0]

    assert first["rank"] == 1
    assert first["region"] == "Southeast"
    assert first["gap_change"] == pytest.approx(4.0)


def test_rank_regions_by_disparity_change_top_n(sample_brfss_df):
    disparity = compute_state_disparity_by_region(sample_brfss_df, measures=["coverage"])
    change = compare_pre_post_disparity(disparity, pre=(2017, 2017), post=(2021, 2021))

    result = rank_regions_by_disparity_change(change, top_n=1)

    assert len(result[result["measure"] == "coverage"]) == 1


def test_rank_regions_by_disparity_change_missing_columns_raises():
    bad_df = pd.DataFrame({"region": ["West"], "measure": ["coverage"]})

    with pytest.raises(ValueError):
        rank_regions_by_disparity_change(bad_df)
