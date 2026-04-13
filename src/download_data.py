"""download_data.py

Function to download BRFSS Prevalence & Trends data directly from the CDC's
open data API (Socrata). This lets the project pull fresh data without
requiring users to manually download CSVs from the BRFSS website.

The CDC publishes the BRFSS Prevalence & Trends data on data.cdc.gov.
Dataset: "Behavioral Risk Factor Surveillance System (BRFSS) Prevalence Data
(2011 to present)" with resource id `dttw-5yxu`.

Each row in that dataset has columns including:
    Year, Locationabbr, Locationdesc, Class, Topic, Question,
    Data_value, Confidence_limit_Low, Confidence_limit_High, Sample_Size,
    Break_Out, Break_Out_Category, ...

We filter to overall (non-broken-out) state-level rows for the topic of
interest (obesity / coverage / smoking) and write a CSV that matches the
schema the rest of the project expects:
    year, state, locationdesc, measure, value, ci_lower, ci_upper, sample_size

Usage (from repo root):
    python -m src.download_data --measure obesity
    python -m src.download_data --measure coverage --start-year 2015 --end-year 2023
    python -m src.download_data --all
"""

from pathlib import Path
import argparse
import sys
import urllib.parse
import urllib.request
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"

# CDC Socrata endpoint for BRFSS Prevalence Data (2011 to present)
BRFSS_DATASET_ID = "dttw-5yxu"
BRFSS_API_URL = f"https://data.cdc.gov/resource/{BRFSS_DATASET_ID}.json"

# Map our internal measure names to the BRFSS "Topic" / "Question" filters.
# These topic strings come from the BRFSS Prevalence & Trends dataset.
MEASURE_FILTERS = {
    "obesity": {
        "topic": "Overweight and Obesity (BMI)",
        "question_contains": "obese",
    },
    "coverage": {
        "topic": "Health Care Access/Coverage",
        "question_contains": "health care coverage",
    },
    "smoking": {
        "topic": "Tobacco Use",
        "question_contains": "current smoker",
    },
}


def _fetch_page(params: dict) -> list:
    """Fetch one page of records from the Socrata API."""
    url = BRFSS_API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "regional-vitals/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_brfss_measure(
    measure: str,
    start_year: int = 2011,
    end_year: int = 2023,
    out_dir: Path = DATA_PROCESSED,
    overwrite: bool = False,
) -> Path:
    """Download BRFSS data for a single measure and write it as a CSV.

    Parameters
    ----------
    measure : str
        One of "obesity", "coverage", "smoking".
    start_year, end_year : int
        Inclusive year range to pull.
    out_dir : Path
        Directory to write the CSV into.
    overwrite : bool
        If False and the destination file already exists, skip the download.

    Returns
    -------
    Path to the written CSV.
    """
    measure = measure.lower()
    if measure not in MEASURE_FILTERS:
        raise ValueError(
            f"Unknown measure: {measure!r}. Valid: {list(MEASURE_FILTERS)}"
        )

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"brfss_{measure}_{start_year}_{end_year}.csv"

    if out_path.exists() and not overwrite:
        print(f"Skipping {measure}: {out_path} already exists. Use overwrite=True to replace.")
        return out_path

    filters = MEASURE_FILTERS[measure]
    print(f"Downloading BRFSS {measure} data for {start_year}-{end_year}...")

    # Page through the API in chunks of 5000 (Socrata default max).
    all_rows = []
    limit = 5000
    offset = 0
    while True:
        params = {
            "$limit": limit,
            "$offset": offset,
            "$where": (
                f"year >= '{start_year}' AND year <= '{end_year}' "
                f"AND topic = '{filters['topic']}' "
                f"AND lower(question) like '%{filters['question_contains']}%' "
                f"AND break_out = 'Overall'"
            ),
        }
        try:
            page = _fetch_page(params)
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch from CDC API ({BRFSS_API_URL}): {e}\n"
                f"Check your internet connection or the dataset id."
            ) from e

        if not page:
            break
        all_rows.extend(page)
        print(f"  fetched {len(all_rows)} rows so far...")
        if len(page) < limit:
            break
        offset += limit

    if not all_rows:
        raise RuntimeError(
            f"No rows returned for measure={measure}. "
            f"The BRFSS topic/question filter may need updating."
        )

    raw = pd.DataFrame(all_rows)

    # Normalize columns to the project's expected schema.
    # Socrata returns lowercase column names.
    rename_map = {
        "year": "year",
        "locationabbr": "state",
        "locationdesc": "locationdesc",
        "data_value": "value",
        "confidence_limit_low": "ci_lower",
        "confidence_limit_high": "ci_upper",
        "sample_size": "sample_size",
    }
    missing = [c for c in rename_map if c not in raw.columns]
    if missing:
        raise RuntimeError(
            f"Downloaded data missing expected columns: {missing}. "
            f"Got columns: {list(raw.columns)}"
        )

    out = raw[list(rename_map)].rename(columns=rename_map).copy()
    out["measure"] = measure

    # Convert numeric columns
    for col in ["year", "value", "ci_lower", "ci_upper", "sample_size"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # Drop US-wide / territory rows; keep 50 states + DC.
    out = out[out["state"].str.len() == 2]
    out = out[out["state"] != "US"]

    # Reorder to match project schema
    out = out[
        ["year", "state", "locationdesc", "measure",
         "value", "ci_lower", "ci_upper", "sample_size"]
    ].sort_values(["year", "state"]).reset_index(drop=True)

    out.to_csv(out_path, index=False)
    print(f"Wrote {len(out)} rows -> {out_path}")
    return out_path


def download_all(start_year: int = 2011, end_year: int = 2023, overwrite: bool = False):
    """Download all three measures."""
    paths = []
    for m in MEASURE_FILTERS:
        paths.append(download_brfss_measure(m, start_year, end_year, overwrite=overwrite))
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Download BRFSS data directly from the CDC open data API."
    )
    parser.add_argument("--measure", choices=list(MEASURE_FILTERS),
                        help="Single measure to download")
    parser.add_argument("--all", action="store_true",
                        help="Download all measures (obesity, coverage, smoking)")
    parser.add_argument("--start-year", type=int, default=2011)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing CSVs in data/processed/")
    args = parser.parse_args(argv)

    if not args.measure and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.all:
        download_all(args.start_year, args.end_year, overwrite=args.overwrite)
    else:
        download_brfss_measure(
            args.measure, args.start_year, args.end_year, overwrite=args.overwrite
        )


if __name__ == "__main__":
    main()
