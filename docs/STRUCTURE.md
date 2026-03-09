# Repository structure (src layout)

- `src/` — main package code (preprocessing, regional mapping, prevalence and trend utilities). Contains `__init__.py` so it can be imported as a package.
- `data/raw/` — optional original downloads; keep immutable.
- `data/processed/` — cleaned/combined BRFSS CSVs used by analysis.
- `regional_analysis/` — region-specific work area. The shared runner `example_region_run.py` lives here; teammates can:
	- reuse the runner with different `--region/--measure` flags (preferred), and
	- keep optional per-region notes or custom scripts under `regional_analysis/{region}/` if they truly need bespoke logic. Most contributions should come from outputs written to `outputs/tables/`, not by duplicating the runner.
- `notebooks/` — exploratory analysis notebooks.
- `outputs/` — generated tables/figures; keep large intermediates out of git when possible.
- `tests/` — lightweight smoke tests to ensure modules import.
- `docs/` — project documentation.
- `README.md` — project overview and instructions.
