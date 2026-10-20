# Access Control Matrix — Prediction Market Trading Bot

**Class:** LIVING (registered in `00_ADMIN/DOC_REGISTRY.toml`)
**Last verified:** 2026-10-20 against `.github/workflows/*.yml`, `deploy/*.service`, `deploy/env.template`, `scripts/pmbot-web-dashboard.service`, `scripts/box_tasks.py`, `src/` (credential reads), `06_CODE_EXECUTION_REPRODUCIBILITY/SECRETS_HANDLING.md`, and DECISION_LOG 2026-10-11 / 2026-10-15.
**Owner (role):** Risk and Compliance Owner (RCO) + Director/Sponsor (DS)
**Must match:** the credential list the code and workflows actually read. A new secret name in `src/`, `deploy/`, or `.github/workflows/` makes this file stale.
**Rule for this file:** names, scopes and holders only. **No secret value, key material, or token ever goes in this repo or this file.**
**Replaces:** the 2026-05-22 version (roles R-01..R-06, "vault TBD at G5"). No vault exists; the real store is described below. Superseded text is in git history.

---

## Roles

Single-operator system. Every role is held by Earl Ignacio; the separation is conceptual accountability. Abbreviations: DS (Director/Sponsor), RL (Research Lead), MO (Model Owner), RCO (Risk and Compliance Owner), MV (Model Validator), IO (Infrastructure Operator). Full table: `00_ADMIN/STAKEHOLDERS_RACI.md`.

Non-human actors that now act on the system, and are the real access question:

| Actor | What it can do |
|---|---|
| Claude Code sessions (local worktrees) | Read/write the repo. `ssh` to the box as root when the operator's ssh config is present. No venue key. |
| Claude cloud sessions | Read/write the repo. **No ssh client**; reach the box only through the box bridge. Outbound network is restricted; Kalshi returned `CONNECT 403` from the cloud container. |
| Box bridge (`box_tasks.yml`) | Runs only allowlisted tasks from `scripts/box_tasks.py` on the box, from a request file in `04_EXECUTION/BOX_TASKS/requests/`. Allowlist: `budget_read`, `silent_arms_read`, `deploy_truth_read`, `capture_install`, `capture_readback`, `capture_uninstall`, `thin_depth_stats`, `nba_opening_preflight`. **No kill-switch task, no order task.** |
| GitHub Actions | Eight workflows (below). One secret. |
| Muse (sports-intel archive writer) | Pushes to a separate private repo. The bot reads that archive only. |

## Credential inventory (names only)

| Credential | What it unlocks | Where it lives | Who / what can use it |
|---|---|---|---|
| `VPS_SSH_KEY` (GitHub Actions secret) | root ssh to the box (157.230.91.33) | GitHub repo secret | Workflows: `deploy`, `box_tasks`, `mlb_features_sync`, `mlb_games_cache_sync`, `post_game_resolve`. Anyone who can edit a workflow on a branch the secret reaches can run commands as root on the box. Public repo: PRs from forks do not receive secrets; own-branch pushes do. |
| `VENUE_API_KEY` + `VENUE_PRIVATE_KEY_PATH` | Kalshi API (demo host `external-api.demo.kalshi.co`; production hosts exist in code, gated off) | Box `.env` (untracked) loaded by systemd `EnvironmentFile=`; key file on the box | The `t4-mlb` service, cron pipelines, and Kalshi client on the box (all run as root). `deploy/demo_fill.env` selects the demo-fill mode. Not present in GitHub or cloud sessions. |
| `POLYMARKET_API_KEY`, `VENUE_ID` | Polymarket US (inactive; gated on operator KYC) | Box `.env` if ever set | Nothing active. |
| `KALSHI_LIVE_CAPITAL_ADR` | A guard value, not a credential: live orders refuse unless it names an accepted ADR | Box environment | C5. No ADR accepts live capital (G6 not cleared). |
| `BOT_ENV`, `BOT_AUDIT_LOG_PATH`, `LOG_DIR` | Configuration, not secrets | `.env` / unit files | The bot processes. |
| Muse archive deploy key (id 166624777, "Muse archive push (write, this repo only)") | Write to `eignacio1/sports-intel-archive` only | Private half in the operator's `~/.config/sports-intel-archive/`; public half on that repo | The operator's machine / Muse. The bot has no write path to the archive. |
| Operator ssh key for `prediction-market-vps` | Interactive root on the box | Operator's machine ssh config | Operator and Claude Code sessions on that machine. |

Templates: `deploy/env.template`, `deploy/demo_fill.env`. Storage policy: `06_CODE_EXECUTION_REPRODUCIBILITY/SECRETS_HANDLING.md` (ADR-0008). No formal vault (OQ-009 open).

## Resources

| ID | Resource | Read | Write | Notes |
|---|---|---|---|---|
| RES-01 | Source repo `eignacio1/prediction-market-bot` | **Public since 2026-10-11** (to make Actions free). Anyone on the internet. | Operator, Claude sessions, CI (`contents: write` on `box_tasks`) | Stays public for now (DECISION_LOG 2026-10-15 22:28 PT). Returning to private moves every workflow to a self-hosted runner. Never commit a secret, an `.env`, or account-identifying data. |
| RES-02 | Box `/opt/prediction-market-bot` | Operator, `VPS_SSH_KEY` workflows | same, as root | Single host, services run as root. |
| RES-03 | Ledgers and audit logs (`logs/`) | Box; copies synced to the repo by workflows | Bot processes append | Append-only by convention (C6). |
| RES-04 | Venue order API | Bot on the box | Bot on the box (demo only) | Orders pass C4 risk gate and the kill switch first. |
| RES-05 | Kill switch flags (`logs/*kill_switch*.flag`) | Any order path | Operator by ssh; C7 | `RUNBOOKS/RUNBOOK_kill-switch.md`. Not reachable via the bridge. |
| RES-06 | Web dashboard `pmbot-web-dashboard.service` | Binds `127.0.0.1:8050` only; reached over an ssh tunnel | read-only view | No public listener. |
| RES-07 | Muse archive repo (private) | Bot (read-only), operator | Operator's deploy key | Intake contract: DECISION_LOG 2026-10-15 22:09 PT. |
| RES-08 | Public data hosts (ESPN, MLB StatsAPI, NHL web API, NBA CDN, nflverse releases, Kalshi public market data) | Bot, workflows | none | No credential; outbound HTTPS only. |

## Environments

| Environment | Market data | Order API | Live funds | Kill switch |
|---|---|---|---|---|
| Research (local / cloud sessions) | Snapshots, public APIs | not connected | not connected | n/a |
| Paper / demo (the box) | Live read | **Kalshi demo** and simulated | **none** | Active |
| Live capital | — | — | **Not authorized.** Hard Rule 2: no real capital until G6 and DS sign-off | Active |

## Access review

Review on: a new credential name appearing in code or workflows; a new workflow; a change to repo visibility; live-capital authorization; a suspected leak (log to `04_EXECUTION/RID_LOG.md`, rotate, trip the kill switch if an order key is involved). The doc registry alarms when this file passes its `max_age_days`.

**Known gaps (not fixed here):** all box services run as root; no formal vault (OQ-009); `VPS_SSH_KEY` is a root key shared by five workflows. Register or cite a GG before changing any of them.
