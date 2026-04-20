# Policy: Do not commit generated outputs (tables/figures)

Project policy: the repository contains the code, tests, and documentation required to reproduce analysis outputs. Generated files (CSV tables, PNG/JPEG figures, other binary artifacts) must not be committed into the repository. This keeps the history small, reduces merge conflicts, and ensures teammates reproduce outputs locally when needed.

Why:
- Binary diffs (images, large CSVs) quickly bloat the repo and cause merge conflicts.
- Outputs are deterministic given the code and input data; teammates should run the pipeline locally to reproduce them.

Where to put outputs locally:
- The shared runner writes outputs to `outputs/` by default. Keep that folder locally and do not add it to commits.

How to stop tracking outputs if they were already committed:

1. From the repository root, run:

```bash
# stop tracking the outputs folder but keep files locally
git rm -r --cached outputs/
echo "outputs/" >> .gitignore
git add .gitignore
git commit -m "Stop tracking generated outputs (tables/figures); add outputs/ to .gitignore"
git push
```

2. If there are many old large files in history and you want to purge them from the repo history, coordinate with the maintainers — rewriting history is disruptive and requires every collaborator to re-sync their clones.

Recommended contributor workflow:

- Make code or documentation changes in a feature branch.
- Add or update tests under `tests/` when changing behavior.
- Run the runner locally to generate CSV/figures for your review, but do not add them to the PR.
- Include small sample CSV snippets (if absolutely necessary for examples) in a `data/examples/` folder with clearly documented provenance and size limits, agreed by maintainers.

If you're unsure whether a file should be committed, ask in the issue/PR or open a quick discussion with the maintainers.
