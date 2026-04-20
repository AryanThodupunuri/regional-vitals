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
