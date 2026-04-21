"""tests/test_utils.py

Tests for src/utils.py — safe_read_csv and safe_write_csv
"""

import pandas as pd
import pytest
from pathlib import Path
from src.utils import safe_read_csv, safe_write_csv


# ---------------------------------------------------------------------------
# safe_read_csv
# ---------------------------------------------------------------------------

def test_read_csv_basic(tmp_path):
    """Reads a normal CSV correctly."""
    csv = tmp_path / "test.csv"
    csv.write_text("state,value\nNY,1\nCA,2\n")
    df = safe_read_csv(csv)
    assert list(df.columns) == ["state", "value"]
    assert len(df) == 2

def test_read_csv_skips_comment_lines(tmp_path):
    """Lines starting with # should be ignored."""
    csv = tmp_path / "test.csv"
    csv.write_text("# this is a comment\nstate,value\nNY,1\n")
    df = safe_read_csv(csv)
    assert list(df.columns) == ["state", "value"]
    assert len(df) == 1

def test_read_csv_returns_dataframe(tmp_path):
    csv = tmp_path / "test.csv"
    csv.write_text("state,value\nNY,1\n")
    df = safe_read_csv(csv)
    assert isinstance(df, pd.DataFrame)

def test_read_csv_empty_file(tmp_path):
    """An empty CSV (headers only) returns an empty DataFrame."""
    csv = tmp_path / "test.csv"
    csv.write_text("state,value\n")
    df = safe_read_csv(csv)
    assert df.empty
    assert list(df.columns) == ["state", "value"]

def test_read_csv_file_not_found(tmp_path):
    """Should raise an error if the file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        safe_read_csv(tmp_path / "nonexistent.csv")


# ---------------------------------------------------------------------------
# safe_write_csv
# ---------------------------------------------------------------------------

def test_write_csv_basic(tmp_path):
    """Writes a DataFrame to CSV correctly."""
    df = pd.DataFrame({"state": ["NY", "CA"], "value": [1, 2]})
    out = tmp_path / "output.csv"
    safe_write_csv(df, out)
    assert out.exists()

def test_write_csv_content_matches(tmp_path):
    """Written file should read back to the same data."""
    df = pd.DataFrame({"state": ["NY", "CA"], "value": [1, 2]})
    out = tmp_path / "output.csv"
    safe_write_csv(df, out)
    result = pd.read_csv(out)
    pd.testing.assert_frame_equal(df, result)

def test_write_csv_no_index(tmp_path):
    """Written CSV should not have a row index column."""
    df = pd.DataFrame({"state": ["NY"], "value": [1]})
    out = tmp_path / "output.csv"
    safe_write_csv(df, out)
    result = pd.read_csv(out)
    assert "Unnamed: 0" not in result.columns

def test_write_csv_creates_parent_dirs(tmp_path):
    """Should create nested directories if they don't exist."""
    df = pd.DataFrame({"state": ["NY"], "value": [1]})
    out = tmp_path / "nested" / "dirs" / "output.csv"
    safe_write_csv(df, out)
    assert out.exists()

def test_write_csv_overwrites_existing(tmp_path):
    """Writing to an existing file should overwrite it."""
    out = tmp_path / "output.csv"
    df1 = pd.DataFrame({"state": ["NY"], "value": [1]})
    safe_write_csv(df1, out)
    df2 = pd.DataFrame({"state": ["CA"], "value": [2]})
    safe_write_csv(df2, out)
    result = pd.read_csv(out)
    assert result["state"].iloc[0] == "CA"

def test_write_csv_empty_dataframe(tmp_path):
    """Should write an empty CSV with headers."""
    df = pd.DataFrame({"state": [], "value": []})
    out = tmp_path / "output.csv"
    safe_write_csv(df, out)
    result = pd.read_csv(out)
    assert result.empty
    assert list(result.columns) == ["state", "value"]
