# Environments — Prediction Market Trading Bot

> **STATUS BANNER (2026-10-20, W80.4): NOT VERIFIED against the running system.** Written May 2026; environment names (ENV-01/02/03) and setup text predate the VPS deployment; see `deploy/DEPLOYMENT_GUIDE.md`, `deploy/*.service`, `RUNTIME_MAP.md`. Where this file disagrees with those sources, they win. Registered LIVING in `00_ADMIN/DOC_REGISTRY.toml` with no verification date.

**Purpose:** Define all execution environments, their configurations, and what is permitted in each. A system that runs differently across environments is not reproducible.  
**Owner (role):** Execution Lead (EL) + Architecture Owner (AO)  
**Status:** **CANONICAL — G3 Execution Gate 2026-05-22** — Changes require version bump and CHANGELOG entry  
**Last reviewed:** 2026-05-22 (G3 review; Python 3.11 confirmed; TBD-at-G2 placeholders resolved; promoted DRAFT → CANONICAL)  
**Next review:** On staleness trigger only  
**Staleness triggers:** New environment provisioned; dependency version change; environment drift detected; live environment activated  
**Upstream links:** RUN_INSTRUCTIONS.md, SECRETS_HANDLING.md  
**Downstream links:** DEPENDENCY_LOCKS/, PIPELINES_JOBS.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — ENV-01 confirmed and buildable; ENV-02/ENV-03 activation gates and credential mechanics remain TBD (G5/G6)

---

## Environment Definitions

### ENV-01 — Local Research (Phases 0–5)

| Attribute | Detail |
|-----------|--------|
| Purpose | All research, backtesting, and model development |
| Who can access | Operator only (Earl Ignacio) |
| Python version | **3.11** (pinned; pyproject.toml enforces ≥3.11) |
| Package manager | pip + pyproject.toml; lock files in DEPENDENCY_LOCKS/ |
| Data | Historical snapshots only (DS-01; DS-02/DS-03 historical when available) |
| Live API access | PROHIBITED — no venue API credentials present (NFR-07) |
| Capital at risk | None |
| Dependency pinning | REQUIRED — all runs use requirements-dev.txt or requirements-locked.txt from DEPENDENCY_LOCKS/ |
| Code quality tools | black 24.4.2; flake8 7.0.0; bandit 1.7.8; pre-commit hooks (enforced on every commit) |
| Logging | JSON Lines (jsonlines 4.0.0) — C6 always active |
| Audit logging | REQUIRED — C6 active for all experiment runs |
| Secrets | .env file (never committed); no VENUE_API_KEY present |

**NFR-07 enforcement:** The research environment must contain no live API credentials. Any credential required for data access during Phase 3+ is sandboxed per SECRETS_HANDLING.md.

---

### ENV-02 — Paper Trading VPS (Phase 6)

| Attribute | Detail |
|-----------|--------|
| Purpose | Scheduled pre-game live inference (PIPE-02); paper trading pipeline (PIPE-03 pending T-060) |
| Who can access | Operator only (Earl Ignacio via SSH) |
| Infrastructure | VPS — DigitalOcean Droplet or Hetzner CX11; datacenter IP (passes Kalshi CloudFront WAF) |
| Python version | **3.11** (Homebrew-equivalent; OpenSSL 3.6+ required for Kalshi TLS) |
| sklearn version | **1.4.2** (must match training environment to load prod_model.joblib cleanly) |
| Model | `models/prod_model.joblib` — serialized LR+Platt, 78 features, v1-28483b21 |
| Data | Live DS-02 (Kalshi KXNBAPTS market data) — read-only, no order submission |
| Live API access | Market data feed only (VENUE_API_KEY read-only); no order submission |
| Capital at risk | None (paper trading uses simulated fills) |
| Secrets | `VENUE_API_KEY` in `/opt/prediction-market-bot/.env` (chmod 600; never committed) |
| Cron schedule | PIPE-02 at 21:30 UTC + 01:30 UTC daily; health check 21:00 UTC |
| Audit logging | REQUIRED — C6 at `logs/audit.jsonl`; append-only |
| Deployment | `deploy/DEPLOYMENT_GUIDE.md` — setup.sh + env.template + cron.conf |
| Gate required | ADR-0004 accepted ✅ (Phase 6 active) |
| Kill switch | Pre-game runner exits on C6 write failure (NFR-03 compatible); C7 not wired in PIPE-02 |

---

### ENV-03 — Live Capital (Phase 8)

| Attribute | Detail |
|-----------|--------|
| Purpose | Real order submission to venue |
| Who can access | Operator only; credentials in vault (not local machine) |
| Data | Live venue data feed + order submission API |
| Live API access | FULL — venue order submission API active |
| Capital at risk | REAL — limits per RISK_APPETITE_CONSTRAINTS.md enforced |
| Dependency pinning | REQUIRED — model and library versions frozen at paper→live promotion |
| Audit logging | REQUIRED — C6 active; every order and decision logged |
| Gate required | ADR-0005 + G6 Release Gate + APR-0009 + ACC-0002 |
| Kill switch | ACTIVE — C7 monitoring wired; kill switch tested (G5 drill required) |

---

## Environment Separation Rules

| Rule | Rationale |
|------|-----------|
| Research environment (ENV-01) may NEVER contain live venue credentials | NFR-07; prevents accidental live order submission |
| Paper trading (ENV-02) may NOT have order submission credentials | Paper trading uses simulated fills only |
| Model version must be identical between ENV-02 and ENV-03 | Paper trading validates the exact model used in live |
| Dependency lock file must be identical between ENV-02 and ENV-03 | Reproducibility; prevents environment-specific behavior |
| No model retraining permitted in ENV-02 or ENV-03 | Frozen model policy; retraining requires ADR + new model version |

---

## Environment Variables

Confirmed at G3. See `.env.example` in project root for template.

| Variable | Environment | Purpose | Storage |
|----------|------------|---------|---------|
| `BOT_ENV` | All | Identifies current environment (`research` / `paper` / `live`) | Plain (not secret); set before every run |
| `LOG_DIR` | All | Path for C6 audit log output (e.g., `./logs/`) | Plain |
| `SNAPSHOT_DIR` | All | Path to data snapshots directory | Plain |
| `VENUE_ID` | ENV-02, ENV-03 only | Identifies target venue (parameter — never hardcoded; per ADR-0003) | Plain |
| `VENUE_API_KEY` | ENV-02, ENV-03 only | Kalshi venue authentication | Vault (G5+) / .env file — NEVER committed to VCS |
| `VENUE_API_SECRET` | ENV-03 only | Order signing credential | Vault (G5+) — NEVER in .env or plaintext |
| `VENUE_ROUTER_MODE` | ENV-02, ENV-03 | VenueRouter routing mode: `kalshi_only` (default) or `best_price` | Plain |
| `POLYMARKET_API_KEY` | ENV-02, ENV-03 | Polymarket US authentication (Phase 7 — T-077) | Vault / .env — NEVER committed |
| `PRIZEPICKS_API_KEY` | ENV-02, ENV-03 | PrizePicks authentication (Phase 7+ — new ADR required) | Vault / .env — NEVER committed |
| `UNDERDOG_API_KEY` | ENV-02, ENV-03 | Underdog Fantasy authentication (Phase 7+ — new ADR required) | Vault / .env — NEVER committed |

---

## Dependency Lock Files

All dependency lock files are stored in `DEPENDENCY_LOCKS/` (confirmed at G3):

```
DEPENDENCY_LOCKS/
  requirements-base.txt      # Production dependencies (pinned exact versions)
  requirements-dev.txt       # Dev + research dependencies (includes base)
  requirements-locked.txt    # Full pip freeze output after install (generated per run)
  README.md                  # Policy and naming conventions
```

**Policy:**
- `requirements-dev.txt` is the install source for ENV-01 research runs
- After each install, `pip freeze > requirements-locked.txt` is run and the output committed alongside the experiment record
- The ENV-03 deployment lock file is frozen at paper→live promotion and may not be changed without a new ADR

---

## Environment Health Checks

Before any run (ENV-01 research):

```bash
# 1. Verify Python version
python3.11 --version  # must be 3.11.x

# 2. Verify correct environment tag
echo $BOT_ENV  # must output: research

# 3. Verify no live credentials in ENV-01
printenv | grep -i venue  # must return nothing

# 4. Verify virtual environment is active
which python | grep .venv

# 5. Verify dependencies are consistent
pip check  # must return: No broken requirements

# 6. Verify C6 audit log directory is writable
test -w $LOG_DIR && echo "LOG_DIR writable" || echo "ERROR: LOG_DIR not writable"

# 7. Verify pre-commit hooks installed
pre-commit --version
```

Kill switch health check (ENV-02, ENV-03 only): per RUNBOOK_kill-switch.md drill procedure — mandatory before G5.
