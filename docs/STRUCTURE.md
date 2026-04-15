# Repository Structure# Repository structure (src layout)



## `src/` — Core Package- `src/` — main package code (preprocessing, regional mapping, prevalence and trend utilities). Contains `__init__.py` so it can be imported as a package.

- `data/raw/` — optional original downloads; keep immutable.

All analytical functions live here.  Every module is importable via- `data/processed/` — cleaned/combined BRFSS CSVs used by analysis.

`from src.<module> import <function>`.- `regional_analysis/` — region-specific work area. The shared runner `example_region_run.py` lives here; teammates can:

	- reuse the runner with different `--region/--measure` flags (preferred), and

| Module | Purpose |	- keep optional per-region notes or custom scripts under `regional_analysis/{region}/` if they truly need bespoke logic. Most contributions should come from outputs written to `outputs/tables/`, not by duplicating the runner.

|---|---|- `notebooks/` — exploratory analysis notebooks.

| `region_mapping.py` | `REGIONS` dict (5 regions → state lists), `STATE_TO_REGION` reverse lookup |- `outputs/` — generated tables/figures; keep large intermediates out of git when possible.

| `compute_prevalence.py` | `compute_state_prevalence` — weighted prevalence by state / year / measure |- `tests/` — lightweight smoke tests to ensure modules import.

| `trend_analysis.py` | `compute_region_year_prevalence`, `compute_trend_slope`, `compute_rolling_avg`, `compute_convergence`, `compare_covid_periods`, `pivot_regional_trends`, `pivot_measures_by_region` |- `docs/` — project documentation.

| `cross_measure.py` | `compare_measures_over_time`, `compute_measure_correlations`, `rank_measure_changes`, `generate_cross_measure_summary`, `compare_all_regions_cross_measure` |- `README.md` — project overview and instructions.

| `state_rankings.py` | `compute_state_change`, `rank_states`, `rank_all_measures` |
| `coverage_heatmap.py` | `generate_region_heatmap` |
| `download_data.py` | Download BRFSS data from the CDC Socrata API |
| `preprocessing.py` | `copy_from_path`, `combine_processed` — CSV combining helpers |
| `utils.py` | `safe_read_csv`, `safe_write_csv` |

## `scripts/` — CLI Runners

Ready-made scripts that use `src/` functions to produce outputs.
Run any script with `python -m scripts.<name>`.

| Script | Description |
|---|---|
| `example_region_run.py` | Single region + measure → tables + figures |
| `example_all_regions_run.py` | All-region convergence & COVID comparison |
| `cross_measure_run.py` | Cross-measure comparison for one region |
| `state_rankings_run.py` | State-level ranking charts |
| `explore.py` | Interactive data explorer (CLI prompts or flags) |
| `run_all.py` | Batch driver — all regions × all measures |
| `midwest_coverage.py` | Midwest-specific coverage analysis |

## `tests/` — Test Suite

Unit and smoke tests.  Run with `pytest tests/ -v`.

## `data/processed/` — Input Data

The combined BRFSS CSV (`brfss_combined_2011_2023.csv`) used by all scripts.
Raw data files go in `data/raw/` (gitignored).

## `docs/` — Documentation

Supplementary documentation (this file, output policy, etc.).

## `outputs/` — Generated Outputs (local only)

Scripts write CSV tables and charts here.  This folder is **gitignored** —
outputs are reproducible from the code and should not be committed.
