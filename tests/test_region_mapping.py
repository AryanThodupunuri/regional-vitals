"""tests/test_region_mapping.py

Tests for src/region_mapping.py
"""

import pandas as pd
import pytest
from src.region_mapping import (
    REGIONS,
    STATE_TO_REGION,
    TERRITORIES,
    VALID_STATES,
    filter_states_only,
)


# ---------------------------------------------------------------------------
# REGIONS
# ---------------------------------------------------------------------------

def test_regions_has_five_regions():
    assert len(REGIONS) == 5

def test_all_expected_regions_present():
    assert set(REGIONS.keys()) == {"Northeast", "Midwest", "Southeast", "Southwest", "West"}

def test_no_duplicate_states_across_regions():
    all_states = [s for states in REGIONS.values() for s in states]
    assert len(all_states) == len(set(all_states)), "Duplicate state found across regions"

def test_known_states_in_correct_region():
    assert "NY" in REGIONS["Northeast"]
    assert "IL" in REGIONS["Midwest"]
    assert "FL" in REGIONS["Southeast"]
    assert "TX" in REGIONS["Southwest"]
    assert "CA" in REGIONS["West"]


# ---------------------------------------------------------------------------
# STATE_TO_REGION
# ---------------------------------------------------------------------------

def test_state_to_region_covers_all_states():
    all_states = [s for states in REGIONS.values() for s in states]
    for state in all_states:
        assert state in STATE_TO_REGION

def test_state_to_region_correct_mapping():
    assert STATE_TO_REGION["NY"] == "Northeast"
    assert STATE_TO_REGION["IL"] == "Midwest"
    assert STATE_TO_REGION["FL"] == "Southeast"
    assert STATE_TO_REGION["TX"] == "Southwest"
    assert STATE_TO_REGION["CA"] == "West"

def test_territories_not_in_state_to_region():
    for territory in TERRITORIES:
        assert territory not in STATE_TO_REGION


# ---------------------------------------------------------------------------
# VALID_STATES
# ---------------------------------------------------------------------------

def test_valid_states_matches_state_to_region():
    assert VALID_STATES == set(STATE_TO_REGION.keys())

def test_territories_not_in_valid_states():
    for territory in TERRITORIES:
        assert territory not in VALID_STATES


# ---------------------------------------------------------------------------
# filter_states_only
# ---------------------------------------------------------------------------

def test_filter_removes_territories():
    df = pd.DataFrame({"state": ["NY", "CA", "PR", "GU", "TX"]})
    result = filter_states_only(df)
    assert "PR" not in result["state"].values
    assert "GU" not in result["state"].values

def test_filter_keeps_valid_states():
    df = pd.DataFrame({"state": ["NY", "CA", "TX"]})
    result = filter_states_only(df)
    assert set(result["state"].values) == {"NY", "CA", "TX"}

def test_filter_removes_unknown_codes():
    df = pd.DataFrame({"state": ["NY", "XX", "ZZ"]})
    result = filter_states_only(df)
    assert set(result["state"].values) == {"NY"}

def test_filter_returns_copy():
    df = pd.DataFrame({"state": ["NY", "PR"]})
    result = filter_states_only(df)
    result["state"] = "MODIFIED"
    assert df["state"].iloc[0] == "NY"  # original unchanged

def test_filter_empty_dataframe():
    df = pd.DataFrame({"state": []})
    result = filter_states_only(df)
    assert result.empty

def test_filter_custom_column_name():
    df = pd.DataFrame({"abbrev": ["NY", "PR", "CA"]})
    result = filter_states_only(df, state_col="abbrev")
    assert set(result["abbrev"].values) == {"NY", "CA"}
