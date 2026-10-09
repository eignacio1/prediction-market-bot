# Prediction Market Trading Bot — Project Directory

**Purpose:** Navigation hub and canonical entry point for the Prediction Market Trading Bot project. Start here.
**Owner (role):** Directory Steward (DS)
**Last reviewed:** 2026-10-09 (strategic window "forest" pass — test: if somebody picked this up, would they know where we're at? Found this hub 82 days stale despite the 14-day staleness alert it describes below)
**Last reviewed (prior):** 2026-07-19 (revival pass, Cowork session — see Compass Health section below for why this was needed)
**Last reviewed (prior):** 2026-05-21 (baseline instantiation) — this file went **~7 weeks (2026-05-21 to 2026-07-19) without a single update**, despite the project moving from Phase 0 (all gates Not Started) to Phase 6/7 ACTIVE with MLB paper trading live and G6 in progress. See Compass Health below.
**Next review:** Weekly (Directory Integrity Review cadence, per Update Cadence table below) — this cadence is aspirational until it is actually enforced; a staleness check was added to `.claude/hooks/governance_scan.sh` on 2026-07-19 (GG-127) so this file cannot silently drift unnoticed again.
**Staleness triggers:** New module added; major scope change; phase gate passed; ownership transfer
**Upstream links:** None (root artifact)
**Downstream links:** All modules below
**Decision references:** ADR-0001
**Confidence:** 7/10 — the tables below were re-pointed at the files that actually carry live state on 2026-10-09; the per-module documents they link to are of mixed age (several unchanged since May–July) and say so where it matters

---

## What This Project Is

An automated prediction market trading bot, built from scratch with institutional governance, designed to progress from a research-only forecasting engine to a live-capital trading system. The bot ingests signals, generates calibrated probabilistic forecasts, and — once promoted through formal gates — executes positions on prediction market venues. Full framing (vision, alpha taxonomy, market efficiency thesis) lives in `CLAUDE.md` — read that for *why*, this document for *where*.

**Current phase:** Phase 6 paper trading (G0–G5 closed, G6 not cleared). Four sports log pre-registered shadow forecasts (MLB, NFL, NHL, NBA); one cell trades flat demo measurement stakes (MLB player hits, T4M-PROJ); $0 real capital. **For where the project is right now, read the RUNNING SITREP at the top of [04_EXECUTION/ACTIVE_QUEUE.md](../04_EXECUTION/ACTIVE_QUEUE.md) — never this line.** The operator's north star is [CLAUDE.md](../CLAUDE.md) § "What winning looks like".
**Capital status:** Research/paper-only. No real capital authorized. Live capital requires G6 Release Gate passage (30 resolved paper bets with positive P&L, per-band `clean_n ≥ n*` sample adequacy per APR-0024, and DS sign-off per ADR-0005).

---

## Where to Find Things

| Need | Go to |
|------|-------|
| **Where we are right now** (bottom line, pillar scoreboard, calendar, operator's open calls) | [04_EXECUTION/ACTIVE_QUEUE.md](../04_EXECUTION/ACTIVE_QUEUE.md) — RUNNING SITREP at the top |
| **How far we are from optimum** (the numbers, per pillar) | [04_EXECUTION/ACTIVE_QUEUE.md](../04_EXECUTION/ACTIVE_QUEUE.md) — DISTANCE TO OPTIMUM table, top of the sitrep; measures defined in CLAUDE.md |
| **What winning looks like** (the operator's north star — BREADTH / DEPTH / EXECUTION / PROOF) | [CLAUDE.md](../CLAUDE.md) § "What winning looks like" |
| What the system does and why (vision, alpha taxonomy, hard rules, session protocol) | [CLAUDE.md](../CLAUDE.md) |
| What the system does and why (spec form) | [01_SPEC/VISION_OUTCOMES.md](../01_SPEC/VISION_OUTCOMES.md) |
| What is in and out of scope | [01_SPEC/SCOPE_IN_OUT.md](../01_SPEC/SCOPE_IN_OUT.md) |
| Hard risk limits and kill-switch conditions | [01_SPEC/RISK_APPETITE_CONSTRAINTS.md](../01_SPEC/RISK_APPETITE_CONSTRAINTS.md) |
| Full requirements + acceptance criteria | [01_SPEC/REQUIREMENTS.md](../01_SPEC/REQUIREMENTS.md) |
| System architecture and component map | [02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md](../02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md) |
| **Current band status (which sub-bands are ACTIVE/BLOCKED/dark, per sport)** | [02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md § Live Registry](../02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md) |
| Data flow and lineage | [02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md](../02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md) |
| Interface contracts (schemas/APIs) | [02_ARCHITECTURE_DESIGN/INTERFACES_CONTRACTS.md](../02_ARCHITECTURE_DESIGN/INTERFACES_CONTRACTS.md) |
| Why decisions were made (chronological) | [03_DECISIONS/DECISION_LOG/](../03_DECISIONS/DECISION_LOG/) |
| Why decisions were made (formal ADRs) | [03_DECISIONS/](../03_DECISIONS/) (files named `ADR-NNNN_*.md`) |
| **Mathematical / model overview** (model class, calibration methodology, feature classes) | [08_MODEL_RISK_GOVERNANCE/METHODOLOGY.md](../08_MODEL_RISK_GOVERNANCE/METHODOLOGY.md) |
| Model card, limitations, monitoring/drift plan | [08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md](../08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md), [08_MODEL_RISK_GOVERNANCE/MONITORING_DRIFT_PLAN.md](../08_MODEL_RISK_GOVERNANCE/MONITORING_DRIFT_PLAN.md) |
| G6 gate checklist and current status | [08_MODEL_RISK_GOVERNANCE/G6_GATE_CHECKLIST.md](../08_MODEL_RISK_GOVERNANCE/G6_GATE_CHECKLIST.md) Checklist last edited 2026-07-06; since 2026-10-08 T4M-PROJ's G6 evidence counts real demo fills only (GG-527). |
| **Commercial validation status (live n-counts, EV, tier progress)** | [03_DECISIONS/GOVERNANCE_GAP_LOG.md](../03_DECISIONS/GOVERNANCE_GAP_LOG.md) GG-004 + [05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG004_ev_validation_benchmark_history.md](../05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/GG004_ev_validation_benchmark_history.md) |
| Open governance process gaps | [03_DECISIONS/GOVERNANCE_GAP_LOG.md](../03_DECISIONS/GOVERNANCE_GAP_LOG.md) |
| What's being worked on right now | [04_EXECUTION/ACTIVE_QUEUE.md](../04_EXECUTION/ACTIVE_QUEUE.md) — the wave under NOW (three blocks run by terminals). `TODO_NEXT.md` is the per-task ledger through T-580 (2026-09-28), not the live list. |
| Operator decisions waiting, and every standing authorization | [04_EXECUTION/ACTIVE_QUEUE.md](../04_EXECUTION/ACTIVE_QUEUE.md) § "Needs your decision" |
| How the strategic window runs (protocols, traps, state at last handoff) | [04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md](../04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md) |
| Market-type × band cells and their status (the live inventory) | `src/prediction_market_bot/c5_execution/market_type_registry.py` (`MARKET_TYPE_REGISTRY`); summarized in [EXECUTION_BANDS.md § Live Registry](../02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md) |
| Pre-registrations for the shadow arms (what each first look computes and its verdict rule) | `05_RESEARCH_EXPERIMENTS/EXP036_*`, `EXP037_*` (NFL, MLB), `EXP038_*` |
| Exploratory research (challengers, never verdicts) | [12_EXPLORATORY/CHARTER.md](../12_EXPLORATORY/CHARTER.md) |
| Active risks, issues, dependencies | [03_DECISIONS/GOVERNANCE_GAP_LOG.md](../03_DECISIONS/GOVERNANCE_GAP_LOG.md) (live). `04_EXECUTION/RID_LOG.md` has not been updated since 2026-05-28. |
| **Latest strategic update / what happened most recently** | [04_EXECUTION/ACTIVE_QUEUE.md](../04_EXECUTION/ACTIVE_QUEUE.md) (sitrep + Sequencing track, newest wave first) and the newest entries at the bottom of [03_DECISIONS/DECISION_LOG/DECISION_LOG.md](../03_DECISIONS/DECISION_LOG/DECISION_LOG.md) |
| Research questions and experiments | [05_RESEARCH_EXPERIMENTS/RESEARCH_QUESTIONS.md](../05_RESEARCH_EXPERIMENTS/RESEARCH_QUESTIONS.md) Not updated since 2026-05-28 — the experiment record is `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/` and the EXP-0NN pre-registrations. |
| How to run the system | [06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md](../06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md) Not updated since 2026-05-28 — the live job schedule is `deploy/` (mirrors the VPS crontab) and `.github/workflows/`. |
| **Continuous testing / validation results** | [07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md](../07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md) (strategy) + [07_TEST_VALIDATION_EVIDENCE/VALIDATION_REPORTS/](../07_TEST_VALIDATION_EVIDENCE/VALIDATION_REPORTS/) (results) + [07_TEST_VALIDATION_EVIDENCE/EVIDENCE/](../07_TEST_VALIDATION_EVIDENCE/EVIDENCE/) (raw evidence) |
| Security, compliance, access controls | [09_SECURITY_PRIVACY_COMPLIANCE/POLICY_REQUIREMENTS.md](../09_SECURITY_PRIVACY_COMPLIANCE/POLICY_REQUIREMENTS.md) |
| Runbooks, on-call, known issues | [10_INFRA_OPERATIONS/RUNBOOKS/](../10_INFRA_OPERATIONS/RUNBOOKS/), [10_INFRA_OPERATIONS/KNOWN_ISSUES.md](../10_INFRA_OPERATIONS/KNOWN_ISSUES.md) |
| Navigation index (module map) + dated state snapshot | [11_MEMORY_HANDOFF/MEMORY_BANK.md](../11_MEMORY_HANDOFF/MEMORY_BANK.md) — its "Where we are" box points back to ACTIVE_QUEUE for live state |
| Latest session handoff pack | Newest `11_MEMORY_HANDOFF/SESSION_HANDOFF_*.md` or `11_MEMORY_HANDOFF/CONTEXT_PACKS/` |
| Glossary of project-specific terms | [00_ADMIN/GLOSSARY.md](GLOSSARY.md) |
| Approvals register (ADR/APR sign-off status) | [00_ADMIN/APPROVALS_REGISTER.md](APPROVALS_REGISTER.md) |

---

## Compass Health (Directory Integrity Status)

This project adopted the Compass OS workflow (`00_ADMIN/Project Directory Compass OS Workflow.txt`, ADR-0001), which prescribes a **weekly Directory Integrity Review (DIR)** run by the Directory Steward specifically to catch documents that have silently drifted from reality. That review is not currently running on cadence — this file itself is the proof: it went unedited from 2026-05-21 to 2026-07-19 (~7 weeks) while the project moved through multiple phase transitions, and nobody's session-start protocol caught it because no automated check existed for *this specific file's* freshness (CLAUDE.md's own session-start protocol checks code stubs, governance gaps, and VPS pipeline health — not the nav hub's own staleness).

**Fixed 2026-07-19 (GG-127):** `.claude/hooks/governance_scan.sh` now parses this file's `Last reviewed` date on every session start and prints an ALERT if it exceeds 14 days (double the nominal weekly DIR cadence). This makes the failure mode visible again; it does not by itself restore the weekly cadence — that requires someone actually running a DIR pass on schedule. See `GOVERNANCE_GAP_LOG.md` GG-127 for the full write-up and remediation options.

**Known related gap:** `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` (Last reviewed 2026-05-31, revived 2026-07-19 alongside this file) had the same failure pattern — its own stale-content caveat told readers to check `CLAUDE.md` for live band status instead, which is how CLAUDE.md ended up carrying state it was never meant to hold. Both documents are current as of 2026-07-19; watch for recurrence.

---

## Phase Gates

| Gate | Name | Status |
|------|------|--------|
| G0 | Intent | 🟢 CLOSED |
| G1 | Spec | 🟢 CLOSED |
| G2 | Architecture | 🟢 CLOSED |
| G3 | Execution | 🟢 CLOSED |
| G4 | Evidence | 🟢 CLOSED |
| G5 | Operational | 🟢 CLOSED |
| G6 | Release / Live Capital | 🟡 IN PROGRESS — see `08_MODEL_RISK_GOVERNANCE/G6_GATE_CHECKLIST.md` and `GOVERNANCE_GAP_LOG.md` GG-004 for live sample-adequacy status per band |

For the live per-band `clean_n`/`n*` numbers behind G6's current status, do not rely on this table — run the governance scan or read GG-004 directly. Gate *status* (closed/open) is stable enough to track here; gate *evidence* (n-counts) is not.

---

## Canonical Artifacts

**This section previously maintained a manually-curated table of canonical artifacts (last touched 2026-05-21, 6 entries).** It was dropped in the 2026-07-19 revival rather than refreshed, because a second hand-maintained index is exactly the kind of artifact that silently rots (see Compass Health above — this file's own staleness is the proof). `11_MEMORY_HANDOFF/MEMORY_BANK.md` already serves this function and is updated every session by convention (Hard Rule 7) — treat it as the single canonical-status index rather than duplicating it here.

---

## Update Cadence + Owners

| Cadence | Activity | Owner |
|---------|----------|-------|
| Daily | TODO_NEXT + RID_LOG review | Execution Lead |
| Weekly | Directory Integrity Review (DIR) | Directory Steward |
| Weekly | Cross-Cutting Concerns Council (C4) | Architecture / Risk Owner |
| Biweekly | Integration Review | Architecture Owner |
| Monthly | Gate Readiness Review | Execution Lead + DS |
| Monthly | Grounding-docs staleness review (GG-074, adopted 2026-07-06) | Directory Steward |
| Quarterly | Retrieval Drill + Workflow Retrospective | Directory Steward |

**As of 2026-07-19, only the Daily and Monthly (grounding-docs) items above have evidence of actually running on cadence** (via CLAUDE.md's session-start protocol and TODO_NEXT.md's Standing Items). The Weekly DIR, Weekly C4, Biweekly Integration Review, and Quarterly Retrieval Drill are documented intent, not confirmed practice — see Compass Health above.

---

## Non-Negotiable Invariants

1. If it isn't in the directory (or linked from it), it does not exist for governance/handoff purposes.
2. Every artifact must have the Universal Header (Purpose, Owner, Last Reviewed, Next Review, Staleness Triggers, Links, ADR refs, Confidence).
3. Major changes require an ADR. Accepted ADRs are immutable; changes are made via superseding ADRs.
4. No real capital deployment until G6 Release Gate is formally cleared with evidence artifacts.
5. The `arb/` folder is a reference-only artifact. Nothing from it enters the canonical directory without a formal ADR.
