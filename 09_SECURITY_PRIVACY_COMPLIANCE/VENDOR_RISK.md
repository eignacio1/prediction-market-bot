# Vendor Risk — Prediction Market Trading Bot

**Class:** LIVING (registered in `00_ADMIN/DOC_REGISTRY.toml`)
**Last verified:** 2026-10-20 against `src/` (hosts called), `.github/workflows/`, `deploy/`, `requirements*`/`06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/`, and DECISION_LOG 2026-10-11, 2026-10-15.
**Owner (role):** Risk and Compliance Owner (RCO)
**Must match:** the external hosts and services the code and workflows actually touch. A new host in `src/` or a new workflow makes this file stale.
**Replaces:** the 2026-05-26 version (VND-01..04 with "vault TBD" and "private repo only, remote host TBD"). Superseded text is in git history.
**Related:** `ACCESS_CONTROL_MATRIX.md` (who holds which credential), `RESILIENCE_FAILURE_MODES.md`, `RUNBOOKS/`.

Rating = how badly the project is hurt if the vendor disappears for a week. No dollar contracts exist with any vendor below; all data use is free tier or public.

| ID | Vendor / service | Used for | Criticality | Failure mode and what happens |
|---|---|---|---|---|
| VND-01 | **Kalshi** (`api.elections.kalshi.com`, `external-api.kalshi.com`, demo `external-api.demo.kalshi.co`) | Market data, demo orders, settlement | CRITICAL | API down or auth change: no prices, no fills. Orders refuse on connectivity failure (C5). Regulatory or ToS action ends the venue. Only the demo host is used for orders. |
| VND-02 | Polymarket US (`clob.polymarket.com`) | Secondary venue, inactive | LOW | Gated on operator KYC; adapter built, not live. Any activation needs its own ADR. |
| VND-03 | **GitHub** (public repo, Actions, PR/CI) | Source of truth, CI, scheduled data syncs, deploy, box bridge | HIGH | Outage stops deploys and syncs, not the box's own services. **The repo is public since 2026-10-11** because the free private minutes ran out; everything committed is world-readable. Free hosted minutes are the dependency: back to private means self-hosted runners (DECISION_LOG 2026-10-15). |
| VND-04 | **The VPS** (157.230.91.33; provider not recorded in the repo) | The only runtime host: cron pipelines, `t4-mlb`, dashboard | CRITICAL | Single host, no failover, services as root. Loss stops all logging until rebuilt from the repo; ledgers on the box are the only copy of the unsynced portion. |
| VND-05 | ESPN (`site.api.espn.com`) | Live game state, schedules (T4) | HIGH | Unofficial endpoint; it began returning 403 to discovery on 2026-08-04 (GG-163) and the outage ran 43 h unnoticed. Cycle-log recency probe now exists in the session-start protocol. |
| VND-06 | MLB StatsAPI (`statsapi.mlb.com`) | Games, boxscores, outcomes | HIGH | Unofficial but stable. Outage delays features and resolution. |
| VND-07 | NHL web API (`api-web.nhle.com`), NBA CDN (`ak-static.cms.nba.com`) | NHL and NBA shadow arms | MEDIUM | Outage silences those arms; the silent-arms alarm should catch it. |
| VND-08 | nflverse data releases (`github.com/nflverse/nflverse-data/releases`) | NFL schedules, team stats, event store | MEDIUM | Community-maintained; format or schedule change breaks the NFL arm. Free. |
| VND-09 | PyPI ecosystem | Python dependencies | HIGH | Supply-chain risk. Mitigation: pinned versions in `DEPENDENCY_LOCKS/`, bandit at pre-commit. |
| VND-10 | **Muse archive** (private repo `eignacio1/sports-intel-archive`) | Qualitative sports-intel feed, read-only to the bot | LOW | Write is by a single-repo deploy key held by the operator. If it stalls, the qualitative factor class stops growing; nothing trades on it. Bot treats it as untrusted input. |
| VND-11 | Claude / Anthropic (Claude Code, cloud sessions) | Engineering work on the repo | MEDIUM | Not in the runtime path. Cloud sessions cannot ssh and see restricted network egress. |

**No paid data vendor is used or approved** (standing rule: free data only). A factor available only from a paid source is registered as a gap, not bought.

**Concentration risks to know:** one venue (Kalshi), one host (the VPS), one CI provider (GitHub), two unofficial sports endpoints (ESPN, MLB). None is mitigated by a second source today.

**Review:** on any new host in `src/`, new workflow, vendor incident, or repo visibility change; the registry alarm fires past `max_age_days`.
