# /new-exp — Scaffold a New Experiment

Before starting, ask me: **What is the experiment hypothesis and ID?** (e.g., EXP-006, HYP-004)

Then follow this protocol exactly.

---

## Step 0 — Pilot-Before-Infrastructure Check (LL-009)

Before scaffolding anything, answer these two questions:

1. **Does this experiment require infrastructure that doesn't exist yet?** (new component, new feature class, new data pipeline)
2. **Has the hypothesis been validated at pilot scale first?**

If the answer to (1) is YES and (2) is NO — **do not build the infrastructure yet.** Run the minimal experiment using existing components. If the hypothesis is confirmed, then build the infrastructure. If falsified, you have saved the build cost entirely.

Only proceed to Steps 1–6 if: the hypothesis is confirmed at pilot scale, OR the experiment requires no new infrastructure, OR DS has explicitly approved building ahead of confirmation.

---

## Step 1 — Pre-Flight

Read and confirm:
- `11_MEMORY_HANDOFF/MEMORY_BANK.md` — current phase and gate state
- `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/RESULTS_INDEX.md` — next available EXP ID
- `06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md` — next available SNAP ID
- `05_RESEARCH_EXPERIMENTS/HYPOTHESES.md` — hypothesis being tested

## Step 2 — Snapshot Registration

Register a new snapshot BEFORE the experiment runs:

```
Format: SNAP-YYYY-MM-DD-NNN (next sequence for today)
Add to: 06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md
Required fields: Snapshot ID | Dataset | Source | Version | Ingestion Date | File Path | Row Count (TBD) | Schema Version | Lineage Note | Used In
```

## Step 3 — Experiment Record

Create `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-NNN_[short-title].md` from template at `05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/EXP-TEMPLATE.md`.

Fill in before running:
- Status: RUNNING
- Hypothesis tested: HYP-XXX
- Snapshot IDs Used: [SNAP just registered]
- Experimental Design: train/val/test windows, features, model class, null model
- Temporal Integrity Check: all 4 boxes checked with reasoning

Leave Results section as TBD.

## Step 4 — Runner Script

Check if an existing runner (`run_exp001.py`, `run_backtest.py`) can be parameterized for this experiment. Prefer reuse over new scripts.

If a new runner is needed (`run_expNNN.py`), it must:
- Import from C1, C2, C3, C4, C6 using the standard pipeline
- Use `market_implied_prob = 0.50` unless live Kalshi price is available
- Validate C4 returns `REJECTED("phase_gate_not_reached")` if BOT_C4_ACTIVE not set
- Write all outputs to `exp_output/EXP-NNN/`
- Log to C6 with session_id and snapshot_id throughout
- Never access TEST-labeled rows during fitting or validation metric computation

## Step 5 — Post-Run Updates

After the experiment completes:
1. Populate Results table in EXP-NNN record (Brier/LogLoss/ECE/AUC for Train + Validation + Null)
2. Update `RESULTS_INDEX.md` — status → COMPLETE, fill metrics
3. Update snapshot row count in `DATA_SNAPSHOTS_INDEX.md`
4. Evaluate hypothesis: confirmed / falsified / inconclusive
5. Update `HYPOTHESES.md` if hypothesis status changes
6. Update `MEMORY_BANK.md` and `TODO_NEXT.md`

## Step 6 — Gate Evidence Check

G4 is CLOSED (✅ 2026-05-28). After any Phase 6 experiment:
- Compare new Brier/ECE/EV to production baseline: v1-28483b21, Brier 0.2461, ECE 0.0342, EV +$0.0958/bet
- If Brier improvement ≥ 0.001 OR ECE improvement ≥ 0.005 → candidate for model promotion via /retrain
- If experiment tests a new model class → ADR-0004 amendment required before promotion
- If experiment materially improves EV → flag for G6 gate readiness (T-070 / ADR-0005)

## Temporal Integrity Checklist (mandatory for every experiment)

- [ ] All feature `temporal_cutoff` values precede `game_date` — verified via `shift(1)` in C2
- [ ] No outcome data in feature set — `pts` excluded from X matrix
- [ ] Train/val/test splits strictly chronological — no shuffling
- [ ] Snapshot registered and immutable before run
