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
| **D** | Root-cause the 2026-08-08 post-outage restart: what bound `game_date` differently? | now | STANDARD | GG-190 |
| **E** | Date derivation series-agnostic and refusal-only; `UNREGISTERED_SERIES` counter; register `KXMLBF5`/`KXMLBF7` | now | STANDARD | GG-191 |
| **F** | APR-0032 decision request: `sport` as a first-class attribute, NFL band naming, NFL epoch inheritance | now | MICRO | — |
| **H** | Amend ADR-0054 §5.2 (per-sport ticker grammar, refuse-don't-fallback); register the exposure-granularity gap | now | MICRO | GG-192 |
| **I** | Claim-without-CLOSED-row assertion + GG-NNN ID-uniqueness assertion | now | MICRO | — |
| **G** | NFL skeleton spike — cells + ticker grammar + one C1 stub, `kelly_fraction=0.0`, no C3 | after E and F | STANDARD | GG-194 |

**Do not run E and G at the same time** — both touch `src/`.

## Standing findings the next windows must not re-derive from scratch

- **GG-185's root cause is incomplete.** Mismatch rate is 0/187 before the GG-163 outage and 532/532 after it, with the deploy gap constant across both. See GG-185's 2026-08-19 evidence block. Block D owns this.
- **The date-derivation regex is `^KXMLBHIT-` only** (`run_t4_mlb_live.py:731`, `run_resolve_mlb.py:130`) and on no-match the live engine returns the session wall-clock date at three ledger-write call sites (1100, 1166, 1396). It does not match `KXMLBTOTAL`. Phase 2 activating a second cell before Block E lands reproduces GG-166 on that cell from row one.
- **Outcome-store coverage gap CLOSED (T-470, 2026-08-20).** `t4_mlb_outcome_store.jsonl` extended to 2026-07-02..08-19; all 532/532 corrupted epoch-12 closed positions are now re-derivable (verified independently, T-477).
- **Repair method pre-registered and dry-run simulated, NOT applied (T-477/ADR-0055, 2026-08-20).** All 5 pre-registered assertions passed (532 changed/2416 unchanged, dates match ticker, zero cross-epoch bleed, zero remaining mismatches, `size_usd` invariant). Repaired pooled epoch-12 figures: n=719, mean +0.0652/bet (SE 0.0552), n*=5,580 — **clean_n=719 does NOT clear n\* post-repair**, contradicting the governance hook's current `MET` status (that figure is computed off the *uncorrected* ledger, mean +0.2325/n*=608). GG-196 (OPEN): the 2026-08-04..08-07 outage-window sub-bucket (n=144) shows mean +0.3037/bet, crossing ADR-0055's own pre-registered suspicion threshold and nearly matching the pre-repair artifact — unresolved, not investigated this session.
- **Do not quote any epoch-12 P&L or edge figure as production-authoritative until D1 (ADR-0055 §7) is decided by the operator and the repair is actually applied** — the ADR-0055 dry-run numbers above are evidence for that decision, not a cleared gate. The governance hook's `MET`/GG-046 alert should be read with this caveat until then.

## Do not

Don't reopen T1 (dead — four model classes exhausted). Don't unpark `SCALING_MANDATE_PARKED.md`. Don't promote `assert_ledger_invariants.py` to `--strict` (alarm-only, operator decision). Don't touch sizing or any `kelly_fraction` without an ADR. Don't mark ADR-0054 ACCEPTED — only item (c) is signed. Don't build the periodic intent-vs-implementation reconciliation unasked.
