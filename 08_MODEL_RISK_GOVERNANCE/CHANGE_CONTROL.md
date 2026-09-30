# Change Control — Prediction Market Trading Bot

**Purpose:** Define what changes require formal approval (ADR) versus lightweight documentation. Prevents silent changes to model, risk limits, or strategy from undermining governance.  
**Owner (role):** Director/Sponsor (DS) + Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified current, no drift found. This is a process/policy document (change classification, band-assignment governance, conditional-language rules, decisions-logged requirement) rather than a system-state snapshot, so it doesn't decay the way status documents do. Cross-checked its Session-Start Enforcement grep command (lines 161-167) against CLAUDE.md's own Step 1 protocol — verbatim match, still wired in and enforced.  
**Next review:** G2; update when new component or major change type identified  
**Staleness triggers:** New change type encountered; ADR process revised  
**Upstream links:** ADR-0001, RISK_APPETITE_CONSTRAINTS.md  
**Downstream links:** 03_DECISIONS/, 00_ADMIN/CHANGELOG.md  
**Decision references:** ADR-0001  
**Confidence:** 8/10 — Change types are well-defined; application to edge cases requires judgment  
**Decisions logged:** true — T-154 (SESSION 65 2026-06-22): four framework decisions extracted to DECISION_LOG.md Notable Judgment Calls (three-tier classification; SKELETON→ACTIVE Class A; no emergency override; conditional-language escalation rule)

---

## Change Classification

### Class A — ADR Required (Immutable Record)

These changes require a formal ADR. No exception. ADRs are immutable once accepted.

| Change Type | Rationale |
|------------|-----------|
| New strategy class or strategy expansion (e.g., incorporating arb/) | Fundamental scope change; invalidates prior validation |
| Paper trading promotion (Phase 5 → 6) | Capital risk introduced |
| Live capital authorization (Phase 7 → 8) | Real capital at risk |
| Venue selection | Determines execution design, compliance, and data APIs |
| Risk limit changes (any hard limit in RISK_APPETITE_CONSTRAINTS.md) | Direct capital safety impact |
| Model version promotion to paper/live | Model risk change |
| Retraining in production | Prohibited; requires ADR to even design |
| Removing or changing a component interface (breaking change) | Downstream coupling change |
| Technology stack changes (language, data store) | Reproducibility impact |
| Band assignment change for a strategy currently executing live capital | Changing band of a live strategy changes execution risk and SLA; requires full ADR |

---

## Band Assignment Changes

Band assignment is a structural requirement for all strategies (ADR reference: DECISION_LOG 2026-05-29 Band Framework decisions). `BAND_REGISTRY` in `execution_bands.py` is the machine-readable enforcement layer. The following governance rules apply:

| Change | Class | Documentation required |
|--------|-------|----------------------|
| New strategy registered at any status | B | DECISION_LOG entry + CHANGELOG |
| SKELETON → ACTIVE promotion | **A** | DECISION_LOG entry + DS sign-off + ADR if strategy will execute live capital |
| SKELETON → BLOCKED demotion | B | DECISION_LOG entry + DS sign-off |
| Band reassignment (e.g., T1 detection → T2 detection) | **A** | DECISION_LOG entry + DS sign-off + ADR (band change changes strategy's risk profile) |
| Evidence invalidation demoting ACTIVE → SKELETON | **A** | DECISION_LOG entry + DS sign-off + ADR if strategy was executing live capital |
| `band_status` field correction (typo fix, no semantic change) | C | Artifact update + CHANGELOG |

**Rationale:** Band status is machine-readable enforcement — SKELETON and BLOCKED strategies are blocked from executing bets in `BandRegistry.validate()`. A silent promotion from SKELETON→ACTIVE would allow a strategy with no validated evidence to drive real capital bets. This makes band assignment changes as load-bearing as model version promotions.

**SKELETON → ACTIVE promotion checklist:**
1. A registered EXP (EXP-NNN) has confirmed the signal at the target band
2. DECISION_LOG entry written with EXP reference and evidence summary
3. DS sign-off obtained (APR-XXXX)
4. `band_status` updated in `execution_bands.py` BAND_REGISTRY
5. `BAND_REGISTRY.validate()` passes with zero violations
6. STRATEGY_OVERVIEW.md Band Assignment Registry table updated

---

### Class B — CHANGELOG Entry Required

| Change Type | Documentation |
|------------|---------------|
| New dependency added (pinned version) | CHANGELOG + DEPENDENCY_LOCKS/ |
| Minor interface field addition (backward-compatible) | INTERFACES_CONTRACTS.md version bump + CHANGELOG |
| New experiment type or new feature added | EXPERIMENT_LOG entry + DATA_FLOWS_LINEAGE.md |
| Runbook updated | CHANGELOG |
| Schedule or timeline change | ROADMAP_MILESTONES.md + CHANGELOG |

### Class C — Artifact Update Only (No Separate Process)

| Change Type | Documentation |
|------------|---------------|
| New snapshot registered | DATA_SNAPSHOTS_INDEX.md |
| Open question resolved | OPEN_QUESTIONS.md + linked artifact |
| Assumption validated or falsified | ASSUMPTIONS_REGISTER.md |
| Status report update | STATUS_REPORTS/ |

---

## Change Governance for Risk Limits

Risk limits (RISK_APPETITE_CONSTRAINTS.md) deserve special mention:

- **Increasing a limit** (loosening): requires ADR + RCO sign-off
- **Decreasing a limit** (tightening): requires ADR (conservative direction; still must be documented)
- **Temporary override**: PROHIBITED without ADR
- **Emergency override**: No emergency override path exists. Kill switch is the emergency response.

---

## Conditional Language Governance

**Conditional language in canonical registers is a governance failure, not documentation.**

The following phrases in APPROVALS_REGISTER, ROADMAP_MILESTONES, KNOWN_ISSUES, or ASSUMPTIONS_REGISTER are red flags that a decision has NOT been made:

- "may be revised"
- "could be adjusted"
- "threshold may change"
- "possibly extended"
- "if needed"
- "subject to DS decision"

**What to do instead:**

| Situation | Correct form |
|-----------|-------------|
| Decision has been made | Record it with DS sign-off, APR-XXXX, and date |
| Decision is pending | "TBD — requires APR-XXXX, owner DS, by [date or gate]" |
| Decision is actively deferred | Record it as an open question in OPEN_QUESTIONS.md with a resolution deadline |

**Any conditional language found during an artifact review must be escalated to DS and resolved before the session ends.** Do not leave it for the next session — conditional language that survives a context window transition looks like a decision to the next context window.

---

## CANONICAL Status and `decisions_logged:` Requirement

A document may **not** be marked CANONICAL if it contains strategic decisions, methodology choices, or judgment calls that do not have corresponding entries in `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`.

### The Field

All strategic and architectural documents must carry a `**Decisions logged:**` metadata field in their header (alongside Owner, Confidence, etc.):

- `**Decisions logged:** true` — all substantive decisions in this document have corresponding DECISION_LOG entries
- `**Decisions logged:** false` — unlogged decisions remain; document is **DRAFT** regardless of any other status label until resolved

### CANONICAL Promotion Checklist (Strategic Documents)

Before marking any strategic or architectural document CANONICAL:
1. Enumerate every judgment call, threshold choice, methodology decision, and sequencing rationale in the document
2. Write each to `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (Notable Judgment Calls table)
3. Set `**Decisions logged:** true`
4. For PDTP documents: **Pass 5 — Decision Extraction** (see below) must complete before step 3

### PDTP Pass 5 — Decision Extraction (Mandatory)

Every document produced via the Princeton Deep Thinking Protocol must conclude with an explicit Pass 5 before being marked CANONICAL:

> **PDTP Pass 5 — Decision Extraction**
> List every judgment call made in this document. For each: write a row to `DECISION_LOG.md` Notable Judgment Calls table (Date | Decision | Rationale | Owner). Then set `**Decisions logged:** true`. This pass is not optional and does not happen at session end — it happens before the document is closed.

Pass 5 is not complete until:
- Every judgment call has a named DECISION_LOG row
- `decisions_logged:` is set to `true`
- The document is committed

### Scope

The `**Decisions logged:**` field is **required** on:
- All `02_ARCHITECTURE_DESIGN/` documents
- All `08_MODEL_RISK_GOVERNANCE/` documents containing methodology or threshold choices
- `01_SPEC/RISK_APPETITE_CONSTRAINTS.md`, `01_SPEC/ROADMAP_MILESTONES.md`

The field is **not required** on: operational runbooks, experiment logs, data snapshots, security checklists, templates, ADR files (which are decision records themselves), or handoff files.

### Session-Start Enforcement

At the start of every session, before any implementation work, run:
```bash
grep -rn "^\*\*Decisions logged:\*\* false" \
  "02_ARCHITECTURE_DESIGN/" \
  "08_MODEL_RISK_GOVERNANCE/" \
  "01_SPEC/"
```
Any match is a governance debt. Either resolve it (extract → DECISION_LOG, flip to `true`) or register a T-NNN task before proceeding.

---

## Change Review Checklist

Before implementing any Class A or B change:

- [ ] Change classified correctly (A vs B vs C)
- [ ] If Class A: ADR drafted, reviewed, and accepted before implementation
- [ ] If Class B: CHANGELOG entry created before or immediately after implementation
- [ ] Downstream links updated (interfaces, runbooks, linked artifacts)
- [ ] No shadow changes (implementation must match documented change)
- [ ] No conditional language left in any canonical register updated this session

---

## Drafted Change Entries — T-597 (Wave 42.x reality reconciliation)

**STATUS: DRAFT. Not approved, not applied.** Evidence: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T597_reality_reconciliation.md`. Exception noted honestly: CC-597-D is already in the code (it records reality) and is listed here for ratification or reversal.

### CC-597-A — Schedule the NFL widened N1-N6 capture (Class B; operator-approved cron addition)
- **Change:** add a scheduled caller for `NFLIngestionClient.capture_extended(season, out_dir)` (currently no production caller, no cron) within the existing capture window, with parquet durably stored off the laptop worktree.
- **Evidence:** D1 — capture works and matches nflverse when run by hand; nothing schedules it; the only parquet lives in an ended worktree. nflverse is a rolling snapshot, so point-in-time pre-kickoff values exist only if captured before kickoff.
- **Effect:** append-only rows accrue per week; no feature is wired into any model; no sizing, order or model path changes.
- **Reversal:** remove the cron entry; captured files are append-only and harmless to retain.

### CC-597-B — T3 band assessment: MISFILED (Class A per "Band reassignment"; DS sign-off + ADR)
- **Change (options, operator picks one):** (1) rebuild T3 to earn its band (sub-minute poll, an order path, its own latency measurement); (2) reassign the drift scan to a slower band consistent with its 15-min cadence and no-order design; (3) leave as SHADOW research.
- **Evidence:** D2 — 3,058 runs, median 30s / p95 96s / max 220s, 0 breaches of the 300s SLA; one-scalar tree; read-only; 900s cadence; no latency thesis measured.
- **Effect:** none until approved; T3 is at kelly 0.0 (ADR-0048), no capital involved.
- **Reversal:** reinstate the current `BAND_REGISTRY` entry and `SHADOW` cell.

### CC-597-C — T4M-PROJ status under GG-320 (Class A if demoted from ACTIVE; DS sign-off)
- **Change (options):** keep ACTIVE and record that "ACTIVE" means "evaluating, sizing zero" ; or demote to SHADOW consistent with D3's treatment of T1/T2/T3; or reactivate sizing via the ADR-0048 edge-conditional table.
- **Evidence:** registry note calls it "the only cell placing live bets today" while `kelly_fraction=0.0` (ADR-0048). T-569 returned NOT SUPPORTED on its latency thesis (a slow-cadence shallow tree, i.e. the same misfiling test T3 fails).
- **Effect:** status/label only under the first two options; the third touches sizing and is out of this wave.
- **Reversal:** restore `CellStatus.ACTIVE` (needs `T4M_PROJ` in `BANDS_WITH_FORMULA_ASSERTIONS`, which it is).

### CC-597-D — Registry T1/T2/T3 prop-hits NOT_IMPLEMENTED -> SHADOW (Class B; ALREADY APPLIED, commit c31a005)
- **Change:** three cells corrected to what cron runs. Records reality; not a promotion.
- **Evidence:** D3 table (cron lines, daily reports, `bets_placed=0`, kelly 0.0).
- **Effect:** status label only; `SHADOW` is not gated by formula assertions and changes no behavior.
- **Reversal:** revert c31a005 (or set the three cells back to `NOT_IMPLEMENTED` and revert the two test lines).

### CC-597-E — Any T1 SHADOW -> ACTIVE (Class A; NOT PROPOSED, precondition only)
- **Change:** none drafted for execution. Preconditions: an ADR-0048 edge-conditional reactivation, `T1_MULTI_DAY` in `BANDS_WITH_FORMULA_ASSERTIONS`, and the undiagnosed "0 players matched" T1 run explained.
- **Reversal:** n/a.
