"""data_cleaner.py
Clean and prepare raw CDC coverage CSVs for the regional-vitals pipeline.

Columns in the raw files:
    year, state, locationdesc, measure, value, ci_lower, ci_upper, sample_size

What this module does:
    1. Loads a CSV from disk
    2. Drops columns not needed downstream (ci_lower, ci_upper, sample_size)
    3. Renames 'value' -> 'prevalence_pct' and 'locationdesc' -> 'location'
    4. Removes rows with nulls in key columns
    5. Deduplicates on (year, state, measure)
    6. Enforces correct dtypes
"""

import pandas as pd

# ---------------------------------------------------------------------------
# Constants — edit here if the raw schema ever changes
# ---------------------------------------------------------------------------
DROP_COLS     = ["ci_lower", "ci_upper", "sample_size"]

RENAME_MAP    = {
    "value":        "prevalence_pct",
    "locationdesc": "location",
}

# Rows must have values in ALL of these columns or they get dropped
REQUIRED_COLS = ["year", "state", "measure", "value"]

# Dedup key: one row per state/year/measure combination
DEDUP_SUBSET  = ["year", "state", "measure"]


def clean_coverage_data(filepath: str) -> pd.DataFrame:
    """Load and clean a single raw coverage CSV.

    Parameters
    ----------
    filepath : str
        Path to the raw CSV (e.g. "data/raw/coverage.csv").

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame ready for analysis / heatmap generation.
        Columns: year (int), state (str), location (str),
                 measure (str), prevalence_pct (float)
    """
    # --- 1. Load ---
    df = pd.read_csv(filepath)
    print(f"[load]    {len(df):,} rows | columns: {list(df.columns)}")

    # --- 2. Drop unneeded columns ---
    existing_drops = [c for c in DROP_COLS if c in df.columns]
    df = df.drop(columns=existing_drops)
    print(f"[drop]    removed columns: {existing_drops}")

    # --- 3. Rename ---
    df = df.rename(columns=RENAME_MAP)
    print(f"[rename]  {RENAME_MAP}")

    # --- 4. Remove nulls in required columns ---
    # Map pre-rename names to post-rename equivalents before checking
    check_cols = [RENAME_MAP.get(c, c) for c in REQUIRED_COLS]
    before = len(df)
    df = df.dropna(subset=check_cols)
    print(f"[nulls]   dropped {before - len(df):,} rows with missing values")

    # --- 5. Deduplicate ---
    before = len(df)
    df = df.drop_duplicates(subset=DEDUP_SUBSET)
    print(f"[dedup]   removed {before - len(df):,} duplicate rows "
          f"(key: {DEDUP_SUBSET})")

    # --- 6. Enforce dtypes ---
    df["year"]           = df["year"].astype(int)
    df["prevalence_pct"] = df["prevalence_pct"].astype(float)
    df["state"]          = df["state"].astype(str).str.strip().str.upper()

    print(f"[done]    {len(df):,} rows remaining | "
          f"columns: {list(df.columns)}\n")
    return df


def load_and_clean_multiple(filepaths: list) -> pd.DataFrame:
    """Load, clean, and concatenate multiple CSV files into one DataFrame.

    Parameters
    ----------
    filepaths : list of str
        List of raw CSV file paths.

    Returns
    -------
    pd.DataFrame
        Combined cleaned DataFrame, deduplicated across all files.
    """
    frames = []
    for fp in filepaths:
        print(f"--- Processing: {fp} ---")
        frames.append(clean_coverage_data(fp))

    combined = pd.concat(frames, ignore_index=True)

    # Final dedup across files in case of overlapping data
    before = len(combined)
    combined = combined.drop_duplicates(subset=DEDUP_SUBSET)
    print(f"[merge]   combined {len(filepaths)} files -> "
          f"{len(combined):,} rows ({before - len(combined):,} cross-file dupes removed)")

    return combined


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Single file
    df = clean_coverage_data("data/raw/coverage.csv")
    print(df.head())

    # Multiple files (e.g. one per region or year)
    # df = load_and_clean_multiple([
    #     "data/raw/coverage_northeast.csv",
    #     "data/raw/coverage_south.csv",
    # ])

    # This cleaned df plugs directly into generate_region_heatmap():
    #   generate_region_heatmap(df, "Northeast", "outputs/northeast_heatmap.png")
