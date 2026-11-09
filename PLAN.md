# CI/CD Learning Plan

Each stage = one or two PRs. Work on a branch, open a PR, watch the run, then merge.
**Rule: every stage ends with you deliberately breaking something and reading the failure.**
Keep a `NOTES.md` journal: what broke, how you diagnosed it, what you changed.

Status legend: [x] done · [ ] todo

## Stage 0: Bootstrap (scaffolded)
- [x] App, tests, lint, `make check`, Dockerfile, `ci.yml` with lint + test jobs
- [x] Create the GitHub repo: `gh repo create ci-cd-practice --public --source=. --push`
- [x] Watch the first run: Actions tab, and `gh run watch`
- **Break it:** push a lint error, then a failing test. Find the log line that tells you why.

## Stage 1: Fundamentals of CI
Goal: read workflow logs fluently; fast, reliable feedback.
- [x] Test matrix across Python 3.10/3.11/3.12 (`strategy.matrix`)
- [x] Upload coverage report as an artifact (`actions/upload-artifact`)
- [x] Add `concurrency:` to cancel superseded runs
- [x] Add a status badge to the README
- [x] Add `needs:` so `test` only runs after `lint` passes; compare total time
- **Break it:** make one matrix cell fail; observe `fail-fast` behavior.

## Stage 2: Protect main
Goal: CI as a gate, not a suggestion.
- [ ] Branch protection / ruleset: require PR, require `lint` and `test` checks
- [ ] Add `CODEOWNERS` and a PR template
- [ ] Add a coverage threshold (`--cov-fail-under=90`)
- **Break it:** try pushing directly to main; try merging a red PR.

## Stage 3: Build and package (CI → artifact)
Goal: produce something deployable.
- [ ] Workflow job: build Docker image with `docker/build-push-action`
- [ ] Push to GHCR (`ghcr.io`) using `GITHUB_TOKEN` and `permissions: packages: write`
- [ ] Tag images with commit SHA and `latest`; understand why SHA is the real identity
- [ ] Docker layer caching (`cache-from/to: type=gha`)
- [ ] Smoke test: run the built container in CI and `curl /health`
- **Break it:** break the Dockerfile; make the container crash on start.

## Stage 4: Security and quality gates
- [ ] Dependabot (`.github/dependabot.yml`) for pip + github-actions
- [ ] CodeQL analysis workflow
- [ ] Dependency audit (`pip-audit`) and container scan (Trivy)
- [ ] Pin actions to commit SHAs; learn why
- [ ] Secret scanning / push protection; practice with a fake secret
- **Break it:** pin a dependency with a known CVE and watch the gate fail.

## Stage 5: Continuous delivery
Goal: automatic deploys with safety.
- [ ] Pick a target: Fly.io / Render / Cloud Run (free tiers) or a local k3d/kind cluster
- [ ] GitHub **Environments** (`staging`, `production`) with secrets per environment
- [ ] Auto-deploy to staging on merge to main
- [ ] Manual approval gate (required reviewers) for production
- [ ] Post-deploy health check; automatic rollback on failure
- **Break it:** deploy a bad version, practice rolling back to the previous SHA.

## Stage 6: Releases and versioning
- [ ] Tag-triggered release workflow (`on: push: tags: v*`)
- [ ] Conventional commits + changelog generation (release-please)
- [ ] GitHub Release with attached artifacts
- [ ] `workflow_dispatch` with inputs for manual redeploys

## Stage 7: Pipeline engineering
- [ ] Reusable workflows (`workflow_call`) and composite actions
- [ ] Path filters so docs-only changes skip heavy jobs
- [ ] OIDC auth to a cloud provider instead of long-lived secrets
- [ ] Scheduled runs (`cron`) for nightly tests/scans
- [ ] Self-hosted runner (your WSL box) and when you would not use one
- [ ] Measure: pipeline duration, flake rate, failure causes. Reduce one.

## Stage 8: Observability and operations
- [ ] Structured logging + `/metrics` (prometheus_client)
- [ ] Track DORA metrics by hand from the Actions history: deploy frequency, lead time, change failure rate, time to restore
- [ ] Write a short postmortem for an incident you caused in Stage 5
- [ ] Optional: Terraform for the infra, plan on PR / apply on merge

## Stage 9: Stretch
- Monorepo with a second service; matrix by changed path
- Preview environments per PR
- Canary / blue-green deploy
- Compare with GitLab CI or Jenkins for the same pipeline

## Monitoring habits (do these every push)
- `gh run list --limit 5` · `gh run watch` · `gh run view --log-failed`
- `gh pr checks` for a PR snapshot (no `--watch` flag in older `gh`; use `gh run watch` or `watch -n 5 gh pr checks`)
- Re-run a failed job; decide if it was flaky or real
- Check the run's duration trend weekly
