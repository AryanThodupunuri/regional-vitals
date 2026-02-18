Contributing guidelines — RegionalVitals

Please follow these lightweight rules when contributing data or code:

- Do not upload new raw CSV files to the repository without prior discussion with the team.
- Use processed data in `data/processed/` for analyses. If you need a raw file stored, place it in `data/raw/` and open an issue to request its addition.
- Place regional scripts inside your region’s folder under `regional_analysis/<region>/`.
- Do not modify `src/preprocessing.py` or core pipeline code unless the team agrees. Propose changes via a pull request and include tests.
- Keep notebooks under `notebooks/` and avoid committing large output images; instead commit figures to `outputs/figures/`.
- Add short descriptive commit messages and make small, focused PRs.
- Run tests (if any) and linting locally before creating a PR.

If unsure, open an issue and tag the team members responsible for data management.
