# CI/CD Practice

A tiny Flask service used as a vehicle for learning CI/CD with GitHub Actions.
The app is deliberately boring; the pipeline is the point. See [PLAN.md](PLAN.md).

```bash
make install   # venv + deps (uses uv)
make check     # lint + tests: same commands CI runs
make run       # http://localhost:8000/health
```

Layout: `app/` code · `tests/` · `Dockerfile` · `.github/workflows/` pipelines · `PLAN.md` roadmap.
