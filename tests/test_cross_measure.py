"""Tests for src/cross_measure.py — cross-measure comparison functions."""

import numpy as np
import pandas as pd
import pytest

from src.cross_measure import (
    compare_measures_over_time,
    compute_measure_correlations,
    rank_measure_changes,
    generate_cross_measure_summary,
    compare_all_regions_cross_measure,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Minimal multi-measure, multi-region BRFSS-like DataFrame."""
    rows = []
    for year in [2015, 2016, 2017]:
        for state, region in [("CA", "West"), ("OR", "West"), ("IL", "Midwest"), ("OH", "Midwest")]:
            rows.append({
                "year": year,
                "state": state,
                "region": region,
                "measure": "obesity",
                "value": 30.0 + (year - 2015) * 0.5 + (0 if state in ("CA", "IL") else 2),
                "sample_size": 1000,
            })
            rows.append({
                "year": year,
                "state": state,
                "region": region,
                "measure": "coverage",
                "value": 85.0 - (year - 2015) * 0.3 + (0 if state in ("CA", "IL") else -1),
                "sample_size": 1000,
            })
            rows.append({
                "year": year,
                "state": state,
                "region": region,
                "measure": "smoking",
                "value": 18.0 - (year - 2015) * 0.4 + (0 if state in ("CA", "IL") else 1),
                "sample_size": 1000,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def sample_df_no_region(sample_df):
    """Same data but without the region column (should be inferred)."""
    return sample_df.drop(columns=["region"])


# ---------------------------------------------------------------------------
# compare_measures_over_time
# ---------------------------------------------------------------------------

class TestCompareMeasuresOverTime:
    def test_returns_all_measures(self, sample_df):
        result = compare_measures_over_time(sample_df, "West")
        assert set(result["measure"].unique()) == {"obesity", "coverage", "smoking"}

    def test_returns_correct_years(self, sample_df):
        result = compare_measures_over_time(sample_df, "West")
        assert sorted(result["year"].unique()) == [2015, 2016, 2017]

    def test_correct_columns(self, sample_df):
        result = compare_measures_over_time(sample_df, "West")
        assert list(result.columns) == ["year", "measure", "prevalence_pct", "sample_size_total"]

    def test_weighted_average_is_correct(self, sample_df):
        """CA=30, OR=32 both with sample_size=1000 → avg should be 31 for 2015 obesity."""
        result = compare_measures_over_time(sample_df, "West", ["obesity"])
        row_2015 = result[(result["year"] == 2015) & (result["measure"] == "obesity")]
        assert row_2015["prevalence_pct"].iloc[0] == pytest.approx(31.0)

    def test_custom_measures(self, sample_df):
        result = compare_measures_over_time(sample_df, "West", ["obesity"])
        assert list(result["measure"].unique()) == ["obesity"]

    def test_region_not_found_returns_empty(self, sample_df):
        result = compare_measures_over_time(sample_df, "Northeast")
        assert result.empty

    def test_infers_region_from_state(self, sample_df_no_region):
        result = compare_measures_over_time(sample_df_no_region, "West")
        assert not result.empty
        assert set(result["measure"].unique()) == {"obesity", "coverage", "smoking"}

    def test_missing_columns_raises(self):
        bad_df = pd.DataFrame({"year": [2020], "state": ["CA"]})
        with pytest.raises(ValueError, match="missing required columns"):
            compare_measures_over_time(bad_df, "West")


# ---------------------------------------------------------------------------
# compute_measure_correlations
# ---------------------------------------------------------------------------

class TestComputeMeasureCorrelations:
    def test_returns_square_matrix(self, sample_df):
        corr = compute_measure_correlations(sample_df, "West")
        assert corr.shape[0] == corr.shape[1]
        assert set(corr.index) == set(corr.columns)

    def test_diagonal_is_one(self, sample_df):
        corr = compute_measure_correlations(sample_df, "West")
        for m in corr.index:
            assert corr.loc[m, m] == pytest.approx(1.0)

    def test_year_level(self, sample_df):
        corr = compute_measure_correlations(sample_df, "West", level="year")
        assert corr.shape[0] == corr.shape[1]

    def test_invalid_level_raises(self, sample_df):
        with pytest.raises(ValueError, match="level must be"):
            compute_measure_correlations(sample_df, "West", level="county")

    def test_single_measure_returns_nan_matrix(self, sample_df):
        corr = compute_measure_correlations(sample_df, "West", measures=["obesity"])
        # Only one measure means no pairwise comparison possible
        assert corr.isna().all().all() or corr.shape == (1, 1)

    def test_empty_region_returns_nan_matrix(self, sample_df):
        corr = compute_measure_correlations(sample_df, "Northeast")
        assert corr.isna().all().all()


# ---------------------------------------------------------------------------
# rank_measure_changes
# ---------------------------------------------------------------------------

class TestRankMeasureChanges:
    def test_returns_all_measures(self, sample_df):
        result = rank_measure_changes(sample_df, "West")
        assert set(result["measure"]) == {"obesity", "coverage", "smoking"}

    def test_direction_column(self, sample_df):
        result = rank_measure_changes(sample_df, "West")
        assert set(result["direction"].unique()).issubset({"increase", "decrease", "no change"})

    def test_sorted_by_abs_change(self, sample_df):
        result = rank_measure_changes(sample_df, "West")
        abs_vals = result["abs_change"].abs().tolist()
        assert abs_vals == sorted(abs_vals, reverse=True)

    def test_custom_year_range(self, sample_df):
        result = rank_measure_changes(sample_df, "West", start_year=2015, end_year=2016)
        assert all(result["start_year"] == 2015)
        assert all(result["end_year"] == 2016)

    def test_obesity_increases(self, sample_df):
        """In our fixture, obesity increases by 0.5 pp/year for each state."""
        result = rank_measure_changes(sample_df, "West")
        obesity_row = result[result["measure"] == "obesity"].iloc[0]
        assert obesity_row["abs_change"] > 0
        assert obesity_row["direction"] == "increase"

    def test_empty_region(self, sample_df):
        result = rank_measure_changes(sample_df, "Northeast")
        assert result.empty


# ---------------------------------------------------------------------------
# generate_cross_measure_summary
# ---------------------------------------------------------------------------

class TestGenerateCrossMeasureSummary:
    def test_returns_dict_with_expected_keys(self, sample_df):
        summary = generate_cross_measure_summary(sample_df, "West")
        assert set(summary.keys()) == {"region", "year", "snapshot", "trends", "correlations", "changes"}

    def test_region_is_correct(self, sample_df):
        summary = generate_cross_measure_summary(sample_df, "West")
        assert summary["region"] == "West"

    def test_year_defaults_to_latest(self, sample_df):
        summary = generate_cross_measure_summary(sample_df, "West")
        assert summary["year"] == 2017

    def test_snapshot_has_all_measures(self, sample_df):
        summary = generate_cross_measure_summary(sample_df, "West")
        assert set(summary["snapshot"]["measure"]) == {"obesity", "coverage", "smoking"}

    def test_custom_year(self, sample_df):
        summary = generate_cross_measure_summary(sample_df, "West", year=2015)
        assert summary["year"] == 2015

    def test_trends_is_dataframe(self, sample_df):
        summary = generate_cross_measure_summary(sample_df, "West")
        assert isinstance(summary["trends"], pd.DataFrame)
        assert not summary["trends"].empty


# ---------------------------------------------------------------------------
# compare_all_regions_cross_measure
# ---------------------------------------------------------------------------

class TestCompareAllRegionsCrossMeasure:
    def test_returns_all_regions(self, sample_df):
        result = compare_all_regions_cross_measure(sample_df)
        assert "West" in result.index
        assert "Midwest" in result.index

    def test_columns_are_measures(self, sample_df):
        result = compare_all_regions_cross_measure(sample_df)
        assert set(result.columns) == {"obesity", "coverage", "smoking"}

    def test_custom_year(self, sample_df):
        result = compare_all_regions_cross_measure(sample_df, year=2015)
        assert not result.empty

    def test_values_are_reasonable(self, sample_df):
        result = compare_all_regions_cross_measure(sample_df)
        # All prevalence values should be between 0 and 100
        assert (result >= 0).all().all()
        assert (result <= 100).all().all()

    def test_empty_df(self):
        empty = pd.DataFrame(columns=["year", "state", "measure", "value", "sample_size"])
        result = compare_all_regions_cross_measure(empty)
        assert result.empty
