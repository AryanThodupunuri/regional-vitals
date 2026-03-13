"""run_all.py

Batch driver: generate outputs for all region × measure combinations.

Usage (from repo root):
    python -m regional_analysis.run_all

Outputs land in outputs/tables/ and outputs/figures/ (same as example_region_run.py).
"""

from pathlib import Path

from regional_analysis.example_region_run import run

REGIONS = ["West", "Midwest", "Northeast", "Southwest", "SouthEast"]
MEASURES = ["obesity", "coverage", "smoking"]

COMBINED = Path("data/processed/brfss_combined_2011_2023.csv")
TABLES_DIR = Path("outputs/tables")
FIGURES_DIR = Path("outputs/figures")


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    total = len(REGIONS) * len(MEASURES)
    done = 0
    failed = []

    for region in REGIONS:
        for measure in MEASURES:
            done += 1
            print(f"\n[{done}/{total}] {region} — {measure}")
            try:
                run(region, measure, COMBINED, TABLES_DIR, FIGURES_DIR)
            except Exception as exc:
                print(f"  ERROR: {exc}")
                failed.append((region, measure, exc))

    print(f"\nDone. {total - len(failed)}/{total} succeeded.")
    if failed:
        print("Failed:")
        for region, measure, exc in failed:
            print(f"  {region}/{measure}: {exc}")


if __name__ == "__main__":
    main()
