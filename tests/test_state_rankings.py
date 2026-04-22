"""tests/test_state_rankings.py

Tests for src/state_rankings.py
"""

import pandas as pd
import pytest
from src.state_rankings import compute_state_change, rank_states, rank_all_measures


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Small BRFSS-style DataFrame with two states and two years."""
    return pd.DataFrame({
        "year":        [2011, 2011, 2023, 2023, 2011, 2011, 2023, 2023],
        "state":       ["NY", "CA", "NY", "CA", "NY", "CA", "NY", "CA"],
        "measure":     ["coverage"] * 4 + ["obesity"] * 4,
        "value":       [70.0, 75.0, 80.0, 72.0, 30.0, 28.0, 35.0, 32.0],
        "sample_size": [1000] * 8,
    })


# ---------------------------------------------------------------------------
# compute_state_change
# ---------------------------------------------------------------------------

def test_compute_state_change_returns_dataframe(sample_df):
    result = compute_state_change(sample_df, "coverage")
    assert isinstance(result, pd.DataFrame)

def test_compute_state_change_correct_columns(sample_df):
    result = compute_state_change(sample_df, "coverage")
    expected_cols = {"state", "measure", "start_year", "end_year",
                     "start_value", "end_value", "abs_change", "pct_change"}
    assert expected_cols.issubset(set(result.columns))

def test_compute_state_change_correct_values(sample_df):
    result = compute_state_change(sample_df, "coverage", 2011, 2023)
    ny_row = result[result["state"] == "NY"].iloc[0]
    assert ny_row["start_value"] == 70.0
    assert ny_row["end_value"] == 80.0
    assert ny_row["abs_change"] == 10.0

def test_compute_state_change_pct_change(sample_df):
    result = compute_state_change(sample_df, "coverage", 2011, 2023)
    ny_row = result[result["state"] == "NY"].iloc[0]
    expected_pct = round((10.0 / 70.0) * 100, 2)
    assert ny_row["pct_change"] == expected_pct

def test_compute_state_change_sorted_descending(sample_df):
    result = compute_state_change(sample_df, "coverage", 2011, 2023)
    assert result["abs_change"].iloc[0] >= result["abs_change"].iloc[1]

def test_compute_state_change_defaults_to_data_range(sample_df):
    result = compute_state_change(sample_df, "coverage")
    assert result["start_year"].iloc[0] == 2011
    assert result["end_year"].iloc[0] == 2023

def test_compute_state_change_empty_for_unknown_measure(sample_df):
    result = compute_state_change(sample_df, "nonexistent")
    assert result.empty

def test_compute_state_change_measure_column_correct(sample_df):
    result = compute_state_change(sample_df, "coverage", 2011, 2023)
    assert (result["measure"] == "coverage").all()


# ---------------------------------------------------------------------------
# rank_states
# ---------------------------------------------------------------------------

def test_rank_states_returns_tuple(sample_df):
    inc, dec = rank_states(sample_df, "coverage")
    assert isinstance(inc, pd.DataFrame)
    assert isinstance(dec, pd.DataFrame)

def test_rank_states_has_rank_column(sample_df):
    inc, dec = rank_states(sample_df, "coverage")
    assert "rank" in inc.columns
    assert "rank" in dec.columns

def test_rank_states_increasers_sorted_correctly(sample_df):
    inc, _ = rank_states(sample_df, "coverage", 2011, 2023)
    assert inc["abs_change"].iloc[0] >= inc["abs_change"].iloc[1]

def test_rank_states_decreasers_sorted_correctly(sample_df):
    _, dec = rank_states(sample_df, "coverage", 2011, 2023)
    assert dec["abs_change"].iloc[0] <= dec["abs_change"].iloc[1]

def test_rank_states_top_n(sample_df):
    inc, dec = rank_states(sample_df, "coverage", top_n=1)
    assert len(inc) == 1
    assert len(dec) == 1

def test_rank_states_empty_for_unknown_measure(sample_df):
    inc, dec = rank_states(sample_df, "nonexistent")
    assert inc.empty
    assert dec.empty

def test_rank_states_rank_starts_at_one(sample_df):
    inc, dec = rank_states(sample_df, "coverage")
    assert inc["rank"].iloc[0] == 1
    assert dec["rank"].iloc[0] == 1


# ---------------------------------------------------------------------------
# rank_all_measures
# ---------------------------------------------------------------------------

def test_rank_all_measures_returns_dataframe(sample_df):
    result = rank_all_measures(sample_df, measures=["coverage", "obesity"])
    assert isinstance(result, pd.DataFrame)

def test_rank_all_measures_has_direction_column(sample_df):
    result = rank_all_measures(sample_df, measures=["coverage"])
    assert "direction" in result.columns

def test_rank_all_measures_direction_values(sample_df):
    result = rank_all_measures(sample_df, measures=["coverage"])
    assert set(result["direction"].unique()) == {"increase", "decrease"}

def test_rank_all_measures_contains_all_measures(sample_df):
    result = rank_all_measures(sample_df, measures=["coverage", "obesity"])
    assert set(result["measure"].unique()) == {"coverage", "obesity"}

def test_rank_all_measures_top_n(sample_df):
    result = rank_all_measures(sample_df, measures=["coverage"], top_n=1)
    assert len(result) == 2  # 1 increaser + 1 decreaser

def test_rank_all_measures_empty_for_no_data():
    empty_df = pd.DataFrame(columns=["year", "state", "measure", "value", "sample_size"])
    result = rank_all_measures(empty_df, measures=["coverage"])
    assert result.empty
