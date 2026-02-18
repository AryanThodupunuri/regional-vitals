"""preprocessing.py

Small utility to help place existing BRFSS CSVs into `data/processed/` and to combine them.

Usage examples:
  # Copy from Downloads (macOS default path) to data/processed
  python src/preprocessing.py --copy-from ~/Downloads

  # Combine processed CSVs into a single combined CSV
  python src/preprocessing.py --combine

This file is intentionally conservative: it will not overwrite existing processed files unless --overwrite is passed.
"""

from pathlib import Path
import argparse
import shutil
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"

EXPECTED_FILES = {
    "brfss_obesity_2011_2023.csv": DATA_PROCESSED / "brfss_obesity_2011_2023.csv",
    "brfss_coverage_2011_2023.csv": DATA_PROCESSED / "brfss_coverage_2011_2023.csv",
    "brfss_smoking_2011_2023.csv": DATA_PROCESSED / "brfss_smoking_2011_2023.csv",
}


def copy_from_path(src_dir: Path, overwrite: bool = False):
    """Copy expected CSVs from src_dir into data/processed/.

    src_dir may be a path like `~/Downloads` where you placed the original CSVs.
    """
    src_dir = Path(src_dir).expanduser()
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src_dir}")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, dest in EXPECTED_FILES.items():
        src = src_dir / name
        if not src.exists():
            print(f"Warning: expected file not found in {src_dir}: {name}")
            continue
        if dest.exists() and not overwrite:
            print(f"Skipping {name} because it already exists at {dest}. Use --overwrite to replace.")
            continue
        shutil.copy2(src, dest)
        print(f"Copied {src} -> {dest}")


def combine_processed(outpath: Path = DATA_PROCESSED / "brfss_combined_2011_2023.csv", overwrite: bool = False):
    """Combine the three processed CSVs into a single file with columns:
       year,state,measure,value,ci_lower,ci_upper,sample_size,locationdesc
    """
    files = []
    for p in EXPECTED_FILES.values():
        if p.exists():
            files.append(p)
        else:
            print(f"Missing processed file: {p}")
    if not files:
        raise FileNotFoundError("No processed files found to combine. Place them in data/processed/ or use --copy-from.")

    dfs = []
    for f in files:
        print(f"Reading {f}")
        df = pd.read_csv(f, comment='#')
        # normalize expected columns
        expected_cols = ["year","state","locationdesc","measure","value","ci_lower","ci_upper","sample_size"]
        missing = [c for c in expected_cols if c not in df.columns]
        if missing:
            raise ValueError(f"File {f} is missing columns: {missing}")
        dfs.append(df[expected_cols])

    combined = pd.concat(dfs, ignore_index=True)
    if outpath.exists() and not overwrite:
        print(f"Combined file {outpath} already exists. Use --overwrite to replace.")
        return
    combined.to_csv(outpath, index=False)
    print(f"Wrote combined dataset to {outpath}")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--copy-from", help="Directory containing the three CSVs to copy into data/processed/")
    parser.add_argument("--combine", action="store_true", help="Combine processed CSVs into brfss_combined_2011_2023.csv")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing processed/combined files")
    args = parser.parse_args(argv)

    if args.copy_from:
        copy_from_path(Path(args.copy_from), overwrite=args.overwrite)
    if args.combine:
        combine_processed(overwrite=args.overwrite)
    if not args.copy_from and not args.combine:
        parser.print_help()


if __name__ == "__main__":
    main()
