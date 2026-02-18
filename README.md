# RegionalVitals — BRFSS Prevalence & Trends (2010–2023)

## Overview

RegionalVitals is a collaborative, reproducible data-analysis project to summarize trends in public-health indicators from the CDC BRFSS Prevalence & Trends data (2010–2023). The team will analyze obesity prevalence, health coverage, and selected smoking indicators across five U.S. regions: Northeast, Southeast, Midwest, Southwest, and West. Analyses are descriptive and comparative only; this project does not perform causal inference or provide medical advice.

## Dataset (summary)

- Source: CDC BRFSS Prevalence & Trends Data (2010–2023). Place raw files in `data/raw/`.
- Key indicators: obesity prevalence, insurance coverage (insured/uninsured), smoking prevalence.
- Use state-year prevalence estimates; apply survey weights if microdata are used.

## Research questions

1. How has obesity prevalence changed in each region (2010–2023)?
2. How does health coverage vary across regions and time?
3. Which region experienced the largest change for each indicator?
4. Are regional trends converging or diverging?
5. How did health behaviors shift during and after the COVID period (2019–2023)?

## Approach (brief)

- Standardize and combine BRFSS files across years.
- Map states to five regions (see `data/regions.yaml`).
- Compute state and regional prevalence (population-weighted where appropriate).
- Produce trend tables and visual summaries; flag unreliable estimates.

## Minimal repository structure

```
README.md
data/
	raw/
	processed/
notebooks/
src/
outputs/
```

## How to run (placeholder — code not yet implemented)

This repository is currently at the planning stage. When code is available, the workflow will include:

- Create and activate a Python virtual environment and install dependencies from `requirements.txt`.
- Place BRFSS files in `data/raw/`.
- Run the pipeline (e.g., `python -m src.cli` or `bash scripts/run_full_pipeline.sh`).
- Explore results in `notebooks/`.

## Key planned outputs

- `outputs/tables/regional_trends.csv` — annual regional prevalence by indicator.
- `outputs/tables/state_changes_2010_2023.csv` — state-level changes from 2010 to 2023.
- `outputs/figures/` — trend plots and maps.

## Limitations

- Descriptive analysis only; avoid causal claims.
- BRFSS methodology changes and self-report bias may affect comparability.
- Some state-year estimates may be unreliable due to small samples and will be flagged.

## Contributors

1. Alhaji Bah
2. Angeline Ngo
3. Andrew Girvin
4. Inmar Chavarria-Ramirez
5. Gabriel Syed
6. Michael Huang
7. Dinah Addisalem
8. Aparna Gana
9. Samuel Fuller
10. Andrew Kohl
11. Aryan Thodupunuri
12. Walif Khan
13. Rhea Sethi
14. Vishal Sai Chindepalli

If you are a contributor, please add your role/affiliation in a `CONTRIBUTORS.md` or update this section.

## Next steps

- Add minimal `src/` module skeletons (cleaning, combining, aggregations).
- Create `requirements.txt` and a basic `scripts/run_full_pipeline.sh` placeholder.
- Begin data acquisition and processing following the documented plan above.

---

For any questions or to assign tasks, open an issue or edit the `CONTRIBUTORS.md` file.
