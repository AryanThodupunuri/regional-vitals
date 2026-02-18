"""utils.py

Small helpers used by the pipeline.
"""
from pathlib import Path
import pandas as pd


def safe_read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, comment="#")


def safe_write_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
