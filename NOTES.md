# CI/CD Notes

A journal of what broke, how I diagnosed it, and what I changed.

## Stage 0: Bootstrap

- Config in `pyproject.toml` (ruff + pytest) means my laptop and CI behave the same. `make check` runs what CI runs.
- First local failure: `ModuleNotFoundError: No module named 'app'`. Fixed with `pythonpath = ["."]` in the pytest config, not by changing the tests.
- `gh run watch` follows a run live. `gh pr checks` has no `--watch` in my version of `gh`.

## Stage 1: Fundamentals of CI

### Reading failures
- Which job failed tells you what kind of problem it is. The `lint` job failing means style or unused code. The `test` job failing means behaviour.
- Lint error (`import os` unused): `F401 imported but unused`. Found it with `gh run view --log-failed`.
- One bad line can trip two jobs. `import tomllib` failed lint (`F401`) and failed `test (3.10)` (`ModuleNotFoundError`, since `tomllib` is 3.11+).
- Log noise to ignore: the `DEP0169 url.parse()` warning comes from Node inside GitHub's own actions, not my code.

### Reusable composite actions (`.github/actions/`)
- Split into `setup-python-env`, `python-lint` and `python-test`. `ci.yml` is now mostly `uses:` lines.
- `actions/checkout` must run first, or the runner can't find local actions.
- Every `run:` step in a composite action needs `shell: bash`.
- Inputs (`python-version`, etc.) with defaults make an action reusable.

### Test matrix
- `strategy.matrix.python: ["3.10", "3.11", "3.12"]` expands one job into three parallel jobs, named `test (3.10)` and so on.
- Quote the versions. Unquoted `3.10` is read as the number 3.1.
- `fail-fast: false` lets every cell finish. Without it, one failure cancels the others still running, and I can't see which versions are broken.
- When I require checks in Stage 2, the names will be `test (3.10)` and so on, not `test`.

### Artifacts
- Pytest writes `coverage.xml` via `--cov-report=xml` in `addopts`. The upload step in the `test` job saves it.
- Artifact names must be unique per matrix cell (`coverage-${{ matrix.python }}`), or the upload fails on a name conflict.
- Where to find them: the run's summary page, **Artifacts** section. From the terminal: `gh run download <run-id> -n coverage-3.12`.
- Artifacts expire after 90 days by default (`retention-days:` changes that).
- Open question: steps after a failed step are skipped by default, so a failing test run won't upload coverage. `if: always()` changes that.

## Git habits I picked up
- Create the branch first: `git switch -c <name>`. I committed on `main` once by accident and had to move the commit.
- `git branch -f main origin/main` can't run while I'm on `main`. Switch away first.
- Squash merge keeps `main` clean even when a PR has "intentional break" commits.

## Next
- `concurrency:` to cancel superseded runs
- Status badge in the README
- `needs: lint` on the test job, then compare total time
