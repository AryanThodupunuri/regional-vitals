"""utils.py

Small helpers used by the pipeline.
"""
from pathlib import Path
import pandas as pd


def safe_read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame, skipping comment lines starting with '#'.

    Parameters
    ----------
    path : Path
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
    """
    return pd.read_csv(path, comment="#")


def safe_write_csv(df: pd.DataFrame, path: Path):
    """Write a DataFrame to CSV, creating parent directories if needed.

    Parameters
    ----------
    df : pd.DataFrame
        Data to write.
    path : Path
        Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def validate_dataframe(
    df: pd.DataFrame,
    required_cols: list[str],
    name: str = "DataFrame",
) -> None:
    """Validate that a DataFrame contains the required columns.

    This is a lightweight upfront guard intended to be called at the top of
    public functions in the analysis modules. It produces an immediate,
    actionable error rather than letting downstream code fail with a cryptic
    KeyError or, worse, silently produce wrong results.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.
    required_cols : list[str]
        Column names that must be present in df.
    name : str
        Optional human-friendly name for the DataFrame, used in the error
        message (e.g. "regional_ts").

    Raises
    ------
    TypeError
        If df is not a pandas DataFrame.
    ValueError
        If any of the required columns are missing.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"{name} must be a pandas DataFrame, got {type(df).__name__}"
        )
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"{name} missing required columns: {missing} "
            f"(got columns: {list(df.columns)})"
        )
