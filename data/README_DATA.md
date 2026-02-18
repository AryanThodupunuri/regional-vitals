RegionalVitals — data folder

This file documents how to place and manage BRFSS input files for this project.

Expected structure (root of repository):

data/
  raw/                 # optional: keep original yearly files here
  processed/           # processed/ should contain cleaned combined files used by analysis
    brfss_obesity_2011_2023.csv
    brfss_coverage_2011_2023.csv
    brfss_smoking_2011_2023.csv
    brfss_combined_2011_2023.csv

Guidelines
- Do not edit files in `data/processed/` directly unless you are intentionally updating a processed dataset.
- When acquiring BRFSS files, place original downloads in `data/raw/` and note checksums.
- If you have the three CSVs in your local Downloads folder (or elsewhere), run `python src/preprocessing.py --copy-from PATH` to copy them into `data/processed/`.

Notes about provided placeholders
- The repository currently contains placeholder headers in `data/processed/`. Replace these with the real CSVs or run the preprocessing utility.

License & citation
- Use BRFSS data according to CDC terms. Cite BRFSS in any formal use of the derived outputs.
