# Active queue

**Updated:** 2026-08-19 by T-469. **Verified against `origin/main` at write time — re-fetch before trusting.**
**Free IDs — verify before taking:** T-470+ · GG-190+ · ADR-0055+ · APR-0032+ · EXP-023+
**State:** Phase 0 complete. Phase 1 CLOSED 8/8. Phase 2 1/8 (T-463 landed; gate 2.3 unrun). Phase 3 0/8 (ADR-0054 PROPOSED). Phase 4 0/3. Cell registry: 1 ACTIVE, 2 BLOCKED, 1 DARK, 29 NOT_IMPLEMENTED, 0 SHADOW.

**GG numbers are pre-allocated per block.** GG-162 (no atomic GG-NNN reservation) produced a live GG-187 collision on 2026-08-18. Until Block I ships the uniqueness assertion, take the number your block names and no other.

---

# ⛔ SESSION-END BUDGET — READ BEFORE STARTING, NOT AT THE END

**≤10% context, ≤10 minutes.** Never `Edit` a multi-KB block or `DECISION_LOG.md` — append via `cat >> … <<'EOF'`. A failed exact-match `Edit` is a STOP, not a retry. Word caps: DECISION_LOG ≤150 · TODO_NEXT ≤120 · SESSION_HANDOFF ≤300 · digest ≤150. No re-derivation at close-out. On budget: commit, three-line stub, "truncated at budget," STOP. Run `scripts/session_end_timer.sh` and report measured wall-clock. **Assert your branch reached `origin/main` before writing CLOSED (GG-186).**

---

## Open blocks

| Block | Task | Start when | Tier | GG reserved |
|---|---|---|---|---|
| **C** | Extend `t4_mlb_outcome_store.jsonl` coverage to 2026-08-07→08-15; report how many of GG-185's 532 rows become re-derivable | now | STANDARD | GG-193 |
| ~~**D**~~ | ~~Root-cause the 2026-08-08 post-outage restart: what bound `game_date` differently?~~ DONE (T-471, 2026-08-20) — root cause NOT found; bounded negative result, GG-190 (OPEN). | — | STANDARD | GG-190 |
| **E** | Date derivation series-agnostic and refusal-only; `UNREGISTERED_SERIES` counter; register `KXMLBF5`/`KXMLBF7` | now | STANDARD | GG-191 |
| **F** | APR-0032 decision request: `sport` as a first-class attribute, NFL band naming, NFL epoch inheritance | now | MICRO | — |
| **H** | Amend ADR-0054 §5.2 (per-sport ticker grammar, refuse-don't-fallback); register the exposure-granularity gap | now | MICRO | GG-192 |
| **I** | Claim-without-CLOSED-row assertion + GG-NNN ID-uniqueness assertion | now | MICRO | — |
| **G** | NFL skeleton spike — cells + ticker grammar + one C1 stub, `kelly_fraction=0.0`, no C3 | after E and F | STANDARD | GG-194 |

**Do not run E and G at the same time** — both touch `src/`.

## Standing findings the next windows must not re-derive from scratch

- **GG-185's root cause is incomplete, and Block D (T-471) did NOT resolve it.** Mismatch rate is 0/77 correct under `cbd09ae` vs. 0/532 correct under `687bf9e` (deploy-timestamp-boxed, not calendar-boxed), byte-identical write-path code in both. Ruled out: VPS timezone, systemd restart at onset, `paper_trader.py`/`run_resolve_mlb.py` source diffs. Untested: diff `paper_portfolio_mlb_t4.pre_gg166_correction_20260807T052850Z.json` against live state at that timestamp; live-instrument `game_date` at the `open_position()` call site. See GG-190 (OPEN) for full record — do not re-derive the ruled-out list from scratch.
- **The date-derivation regex is `^KXMLBHIT-` only** (`run_t4_mlb_live.py:731`, `run_resolve_mlb.py:130`) and on no-match the live engine returns the session wall-clock date at three ledger-write call sites (1100, 1166, 1396). It does not match `KXMLBTOTAL`. Phase 2 activating a second cell before Block E lands reproduces GG-166 on that cell from row one.
- **`n*` is not gate-grade for epoch 12.** Recomputed 2026-08-19: all 719 rows → mean +0.2325/bet, n*≈608; the 187 date-consistent rows → mean +0.0163/bet, n*≈75,734. μ is not distinguishable from zero (SE≈0.099) and n* is quadratic in 1/μ. Do not report progress against n* for this epoch until Block C settles which rows are trustworthy.
- **Do not quote any epoch-12 P&L or edge figure**, contaminated or clean, until Block C lands.

## Do not

Don't reopen T1 (dead — four model classes exhausted). Don't unpark `SCALING_MANDATE_PARKED.md`. Don't promote `assert_ledger_invariants.py` to `--strict` (alarm-only, operator decision). Don't touch sizing or any `kelly_fraction` without an ADR. Don't mark ADR-0054 ACCEPTED — only item (c) is signed. Don't build the periodic intent-vs-implementation reconciliation unasked.
