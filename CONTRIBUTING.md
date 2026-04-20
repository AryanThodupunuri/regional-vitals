# Contributing — RegionalVitals

## General Rules

1. **Do not commit generated outputs.** CSV tables, PNG/HTML charts, and other artifacts belong in `outputs/` (gitignored). Run a script locally to reproduce them.
2. **Add reusable logic to `src/`.** If your analysis involves a new computation, write a function in the appropriate module and add tests.
3. **Add runner scripts to `scripts/`.** CLI entry-points that orchestrate `src/` functions go here.
4. **Write tests.** Add or update tests under `tests/` for any new or changed behavior. Run `pytest tests/ -v` before opening a PR.
5. **Do not modify core modules** (`src/preprocessing.py`, `src/region_mapping.py`) without team agreement. Open a PR and tag relevant reviewers.
6. **Keep commits small and focused.** Use descriptive commit messages.
7. **Do not upload raw CSV files** without prior discussion. Use processed data in `data/processed/` for analyses.

## Workflow

```
1. Create a feature branch from main.
2. Write code in src/ and/or scripts/.
3. Add tests in tests/.
4. Run pytest locally — all tests must pass.
5. Open a pull request with a short description of the change.
```

## What Goes Where?

| Type of work | Location |
|---|---|
| Reusable functions (prevalence, trends, …) | `src/` |
| CLI runners / analysis scripts | `scripts/` |
| Tests | `tests/` |
| Documentation | `docs/` or `README.md` |
| Generated tables / figures | `outputs/` (local, **not committed**) |

If you're unsure whether a file should be committed, ask in the issue or PR.
