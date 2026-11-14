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

### Step names
- `name:` on a `uses:` step replaces the raw `Run actions/checkout@v4` label in the run's step list with something readable (`Check out code`, `Lint (ruff)`).
- Step names only show up inside a run. The check names in the PR checks list come from the job key (`lint`, `test (3.10)`), so they didn't change. Renaming those needs a job-level `name:`, which matters for branch protection in Stage 2.
- Expressions work in names: `Test (pytest, Python ${{ matrix.python }})`.

### Concurrency
- `concurrency:` with `group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress: true` cancels an older run when a newer one starts on the same branch or PR.
- The group is just a key. Including `github.ref` means each branch has its own group, so branches don't cancel each other. Without it, every branch would share one group.
- Seen in practice on PR #7: two quick pushes gave a `cancelled` run (4s) and then a `success` run for the second push.
- Caveat for later: cancelling on `main` can interrupt a deploy. Use `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}` once I have deploys (Stage 5).

### Badges and Codecov
- The CI badge is `.../actions/workflows/ci.yml/badge.svg`. Adding `?branch=main` pins it to `main`. Without it, it shows the default branch's latest run anyway, but being explicit makes the intent clear and lets me point it at another branch.
- Codecov needs a `CODECOV_TOKEN` repo secret (set with `gh secret set CODECOV_TOKEN`, never pasted into a file). The workflow reads it as `${{ secrets.CODECOV_TOKEN }}`.
- Upload once per run with `if: matrix.python == '3.12'`, since all matrix cells measure the same code. `if:` on a step skips it for the other cells.
- `fail_ci_if_error: true` makes a failed upload fail the build instead of hiding it.
- The Codecov badge only shows a number once `main` has had an upload.
- Secrets aren't available to PRs from forks. Mine are same-repo, so it works.

### `needs:` (job ordering)
- `needs: lint` on the `test` job makes the test jobs wait for lint.
- Time on PR #10: 46s total with `needs`, against about 30s with lint and test in parallel. Lint is about 10s, so that's the cost of waiting.
- Trade-off: parallel is faster when everything is green. Sequential saves runner minutes when lint fails, because the `test` jobs are skipped instead of run.
- A skipped job is not a failed one. Check how branch protection treats a skipped required check in Stage 2.
- Mistake to avoid: `needs:` is a key of the job (next to `runs-on:`), not of a step. I once pasted it at the bottom of the file under the steps, which made invalid YAML.

## Stage 2: Protect main

### Ruleset (`protect-main`)
- Settings > Rules > Rulesets. Rules used: `deletion`, `non_fast_forward` (no force pushes), `pull_request` (changes must come through a PR, 0 approvals since I'm solo), `required_status_checks` (`lint`, `test (3.10)`, `test (3.11)`, `test (3.12)`).
- "Require branches to be up to date" is `strict_required_status_checks_policy: true`. A PR must be re-tested if `main` has moved.
- No bypass actors, so the rules apply to me as the owner.
- `CODEOWNERS` only requests reviews. It blocks nothing unless "Require review from Code Owners" is on, and on a solo repo that would block me since I can't approve my own PR.

### Mistake: an "Active" ruleset that protected nothing
- My first ruleset was saved as Active, but the target list (`conditions.ref_name.include`) was empty, so it matched no branch. My direct push to `main` went through, twice. Two empty "direct push" commits are still in the history, and `non_fast_forward` now stops me from removing them.
- Found it by reading the ruleset with `gh api repos/<owner>/<repo>/rulesets/<id>`. Fix: Target branches > Add target > Include default branch (`~DEFAULT_BRANCH`).
- Lesson: always run the negative test. "Active" in the UI proves nothing about what is covered.

### Break-it results
- **Direct push:** rejected. `GH013: Repository rule violations found` with two reasons: "Changes must be made through a pull request" and "4 of 4 required status checks are expected". Every broken rule is listed at once.
- **Red PR (lint error):** `lint` failed, so with `needs: lint` the tests were skipped. `mergeStateStatus: BLOCKED`.
- A skipped matrix job is reported as one check named `test`, not `test (3.10)` etc. The required names never report, so they stay "expected" and block the merge. It works because I required the expanded matrix names. Requiring a job named just `test` would behave differently, so check that before relying on it.
- **Coverage gate:** `--cov-fail-under=90` in `addopts`. At 69% pytest printed `FAIL Required test coverage of 90% not reached. Total coverage: 68.97%` even though all tests passed. The `Missing` column lists the uncovered lines. All three matrix cells failed, and the merge was blocked.
- **Green PR:** after adding a parametrized test for every branch, coverage went to 96.55%, all checks passed, and the PR merged as CLEAN. A gate has to be tested in both directions.
- A failed `test` step skips the later steps in that job, so no coverage artifact or Codecov upload exists for a failing run (unless I add `if: always()`).
- Chain: low coverage > pytest exits non-zero > `test (3.xx)` fails > required by ruleset > merge blocked.

### Tooling quirks
- `gh pr edit` fails with a Projects (classic) deprecation error on my `gh` version. Use `gh api -X PATCH repos/<owner>/<repo>/pulls/<n> -f title=...` instead.
- A required check is matched by name, so renaming a job would leave the old name "expected" forever. Name jobs before requiring them.

## Git habits I picked up
- Create the branch first: `git switch -c <name>`. I committed on `main` once by accident and had to move the commit.
- `git branch -f main origin/main` can't run while I'm on `main`. Switch away first.
- Squash merge keeps `main` clean even when a PR has "intentional break" commits.
- `gh pr merge <n> --squash --delete-branch` also removes the local branch and returns me to `main`.
- Paste into the right place: a block copied into the wrong indentation is the most common YAML mistake. Read `git diff` before committing.

- A stray local branch named `=D` showed up from a mistyped `git branch` command. `git branch -vv` is a quick way to spot stray branches. Remove them with `git branch -D -- '=D'`.

## Next
- Stage 3: build the Docker image in CI, smoke test it, push to GHCR. Add the `build` job to the ruleset's required checks once it exists.
