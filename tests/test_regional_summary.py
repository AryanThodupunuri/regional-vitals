"""Tests for regional_summary table builders (small synthetic BRFSS-like frames)."""

import pandas as pd
import pytest

from src.regional_summary import (
    grand_summary,
    latest_year_snapshot,
    period_change_table,
    rank_regions_by_year,
    trend_slopes_summary,
    year_by_region_matrix,
)


@pytest.fixture
def tiny_regional_df() -> pd.DataFrame:
    """Two regions, two years, all three measures — enough for slopes and pivots."""
    rows = []
    for year, ob, cov, smk in [
        (2021, 30.0, 90.0, 18.0),
        (2022, 31.0, 89.0, 17.0),
    ]:
        for state in ("NY", "CA"):
            rows.extend(
                [
                    {
                        "year": year,
                        "state": state,
                        "measure": "obesity",
                        "value": ob + (0.5 if state == "CA" else 0),
                        "sample_size": 1000,
                    },
                    {
                        "year": year,
                        "state": state,
                        "measure": "coverage",
                        "value": cov - (0.5 if state == "CA" else 0),
                        "sample_size": 1000,
                    },
                    {
                        "year": year,
                        "state": state,
                        "measure": "smoking",
                        "value": smk + (0.5 if state == "CA" else 0),
                        "sample_size": 1000,
                    },
                ]
            )
    return pd.DataFrame(rows)


def test_latest_year_snapshot_shape_and_title(tiny_regional_df):
    out = latest_year_snapshot(tiny_regional_df)
    assert not out.empty
    assert list(out.index) == ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    assert list(out.columns) == ["obesity", "coverage", "smoking"]
    assert "2022" in out.attrs.get("title", "")


def test_period_change_table_columns(tiny_regional_df):
    out = period_change_table(tiny_regional_df, start_year=2021, end_year=2022)
    assert not out.empty
    assert set(out.columns) >= {
        "region",
        "measure",
        "start_year",
        "end_year",
        "start_prev",
        "end_prev",
        "change_pp",
        "pct_change",
    }


def test_trend_slopes_summary_has_measure_columns(tiny_regional_df):
    out = trend_slopes_summary(tiny_regional_df)
    assert not out.empty
    for m in ("obesity", "coverage", "smoking"):
        assert f"{m}_slope" in out.columns
        assert f"{m}_r2" in out.columns


def test_rank_regions_by_year_orders_coverage_high_best(tiny_regional_df):
    out = rank_regions_by_year(tiny_regional_df, year=2022)
    cov = out[out["measure"] == "coverage"].sort_values("rank")
    # Higher coverage is rank 1
    assert cov.iloc[0]["prevalence_pct"] >= cov.iloc[1]["prevalence_pct"]


def test_year_by_region_matrix_obesity(tiny_regional_df):
    out = year_by_region_matrix(tiny_regional_df, "obesity")
    assert not out.empty
    assert 2021 in out.columns and 2022 in out.columns


def test_grand_summary_one_row_per_region_measure(tiny_regional_df):
    out = grand_summary(tiny_regional_df)
    assert len(out) == 2 * 3  # two regions in data × three measures
    assert {"mean_prev", "min_prev", "max_prev", "total_samples"}.issubset(out.columns)


@pytest.mark.parametrize(
    "fn",
    [
        latest_year_snapshot,
        period_change_table,
        trend_slopes_summary,
        rank_regions_by_year,
        grand_summary,
    ],
)
def test_empty_input_returns_empty_frame(fn):
    empty = pd.DataFrame(columns=["year", "state", "measure", "value", "sample_size"])
    out = fn(empty)
    assert isinstance(out, pd.DataFrame)
    assert out.empty
