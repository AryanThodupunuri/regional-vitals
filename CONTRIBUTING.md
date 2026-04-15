# Contributing — RegionalVitalsContributing guidelines — RegionalVitals



## General rulesPlease follow these lightweight rules when contributing data or code:



1. **Do not commit generated outputs.**  CSV tables, PNG/HTML charts, and- Do not upload new raw CSV files to the repository without prior discussion with the team.

   other artifacts belong in `outputs/` (gitignored).  Run a script locally- Use processed data in `data/processed/` for analyses. If you need a raw file stored, place it in `data/raw/` and open an issue to request its addition.

   to reproduce them.- Place regional scripts inside your region’s folder under `regional_analysis/<region>/`.

2. **Add reusable logic to `src/`.**  If your analysis involves a new- Do not modify `src/preprocessing.py` or core pipeline code unless the team agrees. Propose changes via a pull request and include tests.

   computation, write a function in the appropriate module and add tests.- Keep notebooks under `notebooks/` and avoid committing large output images; instead commit figures to `outputs/figures/`.

3. **Add runner scripts to `scripts/`.**  CLI entry-points that orchestrate- Add short descriptive commit messages and make small, focused PRs.

   `src/` functions go here.- Run tests (if any) and linting locally before creating a PR.

4. **Write tests.**  Add or update tests under `tests/` for any new or

   changed behavior.  Run `pytest tests/ -v` before opening a PR.If unsure, open an issue and tag the team members responsible for data management.

5. **Do not modify core modules** (`src/preprocessing.py`,
   `src/region_mapping.py`) without team agreement.  Open a PR and tag
   relevant reviewers.
6. **Keep commits small and focused.**  Use descriptive commit messages.

## Workflow

```
1. Create a feature branch from main.
2. Write code in src/ and/or scripts/.
3. Add tests in tests/.
4. Run pytest locally — all tests must pass.
5. Open a pull request with a short description of the change.
```

## What goes where?

| Type of work | Location |
|---|---|
| Reusable functions (prevalence, trends, …) | `src/` |
| CLI runners / analysis scripts | `scripts/` |
| Tests | `tests/` |
| Documentation | `docs/` or `README.md` |
| Generated tables / figures | `outputs/` (local, **not committed**) |

If you're unsure whether a file should be committed, ask in the issue or PR.
