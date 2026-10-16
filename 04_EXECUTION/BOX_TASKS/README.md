# Box tasks (W80R.1) — run a named job on the box from a cloud session

1. Add `requests/<UTC>_<name>.toml` (stem like `20261016T1600Z_budget_read`) containing only
   `task = "<name>"` and optionally `note = "<why, <=200 chars>"`, and push it to `main` (docs-only push).
2. `.github/workflows/box_tasks.yml` runs `scripts/box_tasks.py TASKS[task]` on the box over ssh.
3. Read `results/<same stem>.md` (committed to `main` by the workflow, ~1-3 min later) or the run's job summary.

Allowlist (the only commands that can ever run): see `TASKS` in `scripts/box_tasks.py`. Read-only except
`capture_install`, which refuses unless the SURFACE BUDGET reads GREEN (Hard Rule 14). Adding a task = a PR to that
dict with a test, CI green. Output is redacted (keys/tokens/passwords/private keys) and capped at 60 KB.
