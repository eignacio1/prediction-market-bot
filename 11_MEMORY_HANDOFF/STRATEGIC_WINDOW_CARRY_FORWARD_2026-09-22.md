# Strategic window carry-forward — Waves 25–30, 2026-09-22

**Outgoing window:** Cowork strategic window, Waves 25–30. Operator: Earl, sole operator and reviewer.
**Verified against:** `origin/main = e9a335d`, derived 2026-09-22. This window could not `git fetch` (no credentials in its environment) — its ref was frozen wherever a terminal last left it.

**Do not trust any figure below without re-deriving it.** Every number here was derived by execution at `e9a335d`. This window asserted un-derived facts three separate times and was corrected by a terminal every time (see §8). Assume that applies to this document the moment another commit lands.

---

## §0 — RUN THIS FIRST. Literal commands. Do not design your own.

```
cd <repo> && git fetch origin && git log --oneline -1 origin/main

PYTHONPATH=src python3 - <<'EOF'
from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY as R
from prediction_market_bot.execution_bands import ExecutionBand
from collections import Counter
print("BANDS:", len(list(ExecutionBand)))
print("CELLS:", len(R))
print("STATUS:", dict(Counter(v.status.value for v in R.values())))
EOF

G=03_DECISIONS/GOVERNANCE_GAP_LOG.md
grep -cE '^### GG-[0-9]' $G
grep -c '^\*\*Status:\*\* OPEN' $G
grep -oE '^### GG-[0-9]+' $G | grep -oE '[0-9]+' | sort -n | tail -1

scripts/sweep_stray_branches.sh 30          # landed this session; 17 strays outstanding
cat 00_ADMIN/APPROVALS_REGISTER.md          # read directly, never paraphrased
```

Then run the Princeton Protocol (`00_ADMIN/Princeton Protocol.txt`) in full and re-derive the state block yourself.

---

## §1 — Landmarks, derived 2026-09-22 at `e9a335d`

| Indicator | Value |
|---|---|
| Execution bands / registry cells | 22 / 92 |
| **Cells ACTIVE** | **1** (MLB player-prop hits × T4M-PROJ) — 88 NOT_IMPLEMENTED, 2 BLOCKED, 1 DARK |
| Gap-log entries / OPEN / next free | 134 / 94 / **GG-296** |
| Unlanded remote branches | **17** (GG-292) |
| NFL T1 paper positions open | **42** — ~20 games final since 09-20, **none settled** |
| MLB positions entered since 2026-08-14 | **0 — 39 days dark** |
| Shard 3 collateral | **$200.00** (funded 2026-09-22, `transfer_id 13b801e1-d31f-40e7-b6ea-b760c5dba8be`) |

---

## §2 — ⚠️ FIRST BLOCK OF YOUR FIRST WAVE

**Two things, both live, neither optional.**

**(a) GG-295 (HIGH, OPEN) — someone wrote to the live ledger and there is no record of it.** All 42 NFL positions' `kalshi_threshold` values were already backfilled when T-563 went to do it. There is **no commit anywhere in repo history** for that write, and it is **misattributed to T-562**, an unrelated session. A live ledger that feeds G6 evidence was modified by an unidentified actor. Establish provenance before anything else touches that file. This is GG-228's rule violated by persons unknown.

**(b) GG-291 (HIGH, OPEN) — the settlement still has not run.** ~20 positions have had their games played since 09-20. T-563 fixed the write path (`derive_kalshi_threshold()` / `KalshiThresholdUndefined` in `kalshi_client.py`, called by both T1 game-market run scripts) and proved the not-yet-final guard refuses correctly against a copy with real network calls. **Deliverable 5, the live settlement, never executed.** The runbook is `04_EXECUTION/NFL_T1_FIRST_SETTLEMENT_RUNBOOK.md`. Resolve (a) first — do not settle on a ledger whose provenance is unestablished.

---

## §3 — ALREADY ANSWERED. Do not re-investigate.

1. **GG-203's cause was per-shard collateral, not code.** Kalshi shards its matching engines; shard 3 is Sports; balances are per-shard; the account had $397.44 on shard 0 and $0.00 on shard 3 for 38 days. Fixed 2026-09-22 by an intra-account transfer. **`exchange_index` propagation was tested head-to-head and DISPROVED** — identical order with and without the field failed byte-for-byte identically (T-558). Do not revive it, including if you find the outside `degeneracy_v3` fix that suggests it.
2. **No order has yet been confirmed to fill.** Shard 3 is funded; that is necessary, not sufficient. GG-203 stays PARTIALLY RESOLVED until the live `t4-mlb` service is observed converting approvals into fills — not a hand-built order succeeding.
3. **`_get()` defaults to `authenticated=False`, which resolves to PRODUCTION regardless of `BOT_ENV`.** Market discovery uses that default, so production market data feeds demo order writes. Real architectural defect, surfaced by T-556, still unfixed. Pass `authenticated=True` on every portfolio read or you will read the wrong account.
4. **The P&L gate is not reachable.** T-554: T4M-PROJ `n*=8,587` at ~198 clean bets/wk ≈ 1.6 MLB seasons; NFL moneyline `n*=2,610` ≈ 11 NFL seasons. T1/T2/T3 have `clean_n<2` — no variance estimate exists at all. APR-0035 drafted, unsigned.
5. **EXP-027 is UNDERPOWERED and re-running it changes nothing** — `clean_n=14` against `n*=2,610`. 2026: acc 0.5625 / Brier 0.2290 / ECE 0.1739, n=16. 2025 baseline: 0.6056 / 0.2210 / 0.0661, n=284.
6. **A fresh open-attempt can never be settled in the same session (GG-287).** Kalshi only quotes live markets for unfinished games, so anything you open is for a future game. Open and settle are two sessions, always.
7. **The close-out fix is installed** — `scripts/close_session_claim.sh` pushes closure rows straight to `main`; `scripts/sweep_stray_branches.sh` is Step 9 of `/session-end`. GG-289 records that the auto-mode classifier blocks edits to those paths as Self-Modification.

---

## §4 — Genuinely open, with the directive attached

| Gap | State | Directive |
|---|---|---|
| **GG-295** | Live ledger backfilled by nobody, misattributed | §2(a). Provenance before any further write. |
| **GG-291** | Write path fixed; settlement never ran | §2(b). After GG-295. |
| **GG-274 / GG-287** | Settlement path still never exercised against a real position | Closes when GG-291's Deliverable 5 runs. |
| **GG-203** | Shard funded; no fill observed | Watch the live service across a real MLB window. No restart is authorized. |
| **GG-292** | 17 stray branches, oldest ~2 weeks | Operator routing pass — land, abandon or archive, named branch by branch. Never absorb another session's branch (Hard Rule 11). |
| **GG-279** | Deploy-vs-activation has no structural check | Compare each service's `ActiveEnterTimestamp` to its source's last relevant commit. One SHORT block. |
| **GG-262** | VPS crontab diverges from repo, cause unknown | Same class as GG-295 — the repo is not a reliable picture of the server. |

---

## §5 — Operator-only. Neither you nor a terminal can move these.

| Item | Plain English |
|---|---|
| **APR-0035** | The P&L gate is ~1.6 MLB seasons / ~11 NFL seasons from clearing. Options drafted, **none selected.** This is the biggest open question in the project. |
| **ADR-0063** | Five-tier kill-switch / Kelly alignment. Drafted 2026-09-05, approved in chat 2026-09-18, **still needs a signature row in `APPROVALS_REGISTER.md`** to be citable. |
| **APR-0034** | Whether T4 MLB should stop sending demo orders. **Likely moot** now shard 3 is funded — withdraw it once a fill is confirmed. |

---

## §6 — Your first waves. THE DIRECTION HAS CHANGED — READ THIS.

**Operator directive, 2026-09-22, verbatim in substance:** *"Let's get this damn thing fixed so we can move on to more pressing matters (aka edge calibration — we have not focused nearly enough on it bc we've been busy piping the architecture to get the NFL into the build)."*

He is right, and the record supports him. Waves 25–30 were ring buffers, sharding, capture gaps, thresholds, close-out plumbing and stray branches. **Six consecutive waves of infrastructure.** The only edge work was one backtest that came back UNDERPOWERED and one analysis nobody acted on — and that analysis says the gate we are building toward cannot close in any horizon he cares about.

**Wave 31 — finish the plumbing, and only this.** GG-295 provenance, then GG-291's live settlement. Those ~20 settled games are not a detour: they are the first real resolved NFL outcomes and therefore calibration input.

**Wave 32 — pivot to calibration. The highest-value untouched analysis in the project:**
**T4M-PROJ has 765 clean resolved bets and nobody has ever reported its Brier or ECE against the MLB baselines ADR-0046 established** (`BRIER_BASELINE_MLB=0.2190`, `ECE_BASELINE_MLB=0.0680`). Calibration converges far faster than P&L because it carries no payoff variance. That is a genuine read on whether the model knows anything — available today, from data already on disk, with zero new accrual. Do this before proposing any new market, sport or cell.

**Wave 33 — force APR-0035 to a decision** with Wave 32's numbers in hand, rather than leaving it open a fourth week.

---

## §7 — How the operator wants you to work

- **He is eyes and ears, not plumbing.** His words: *"I'm eyes and ears on the project not the plumbing — that's for you and the terminals to do."* Route findings, verdicts and decisions to him. Do not hand him commands to run. This window made him hand-run three terminal commands and was rightly called out.
- **Sandbox, paper and demo environments are plumbing.** Moving mock collateral, demo-account configuration, test-environment setup — handle it, do not escalate it. Only actions touching **real capital** are his, and G6 has not cleared so none exist yet.
- **The Cowork window cannot SSH.** Anything on the VPS goes to a terminal block, never to him.
- **Prompt blocks go in `04_EXECUTION/ACTIVE_QUEUE.md`**, fenced and paste-in ready, ASCII-only inside the fence. Structure: session-start line, `new_session_worktree.sh`, claim-at-run-time, `*** WORK FROM origin/main. PUSH AFTER EACH DELIVERABLE. ***`, TIER, numbered deliverables, `DO NOT:`, `SCOPE FENCE:`, self-serialising close-out, `REPORT BACK:`. Prose bullet lists are not usable.
- **Three blocks per wave. Hard ceiling.** A block in the wave fires immediately and concurrently with every other. A sequencing note is not a fence — dependent work goes in "Queued next."
- **Plain English in chat.** No acronym walls.
- Never say "did not land" — say "not visible at my ref `<SHA>`, which may be stale."

---

## §8 — This window's verdict on itself

**Three times this window stated a derived fact it had not derived, and a terminal caught it every time.** The `t4-mlb` restart timestamp (quoted from a close-out; T-548 measured something different and the whole restart premise collapsed). "Weeks 1 and 2 have resolved" (only Week 1 had — GG-281). GG-291's own premise (the backfill was already done — GG-295). It never once caught itself.

The pattern is specific and worth carrying: **this window was reliable when it derived from the repo in the same breath as writing, and unreliable when it recalled something from earlier in its own context.** Mid-session recall does not feel like forgetting. It feels like knowing. Re-derive at cite time, every time, including line numbers — they had shifted under it twice.

**It also over-applied a rule.** It refused to move mock collateral in a demo sandbox on the grounds that transfers are financial transactions, and made the operator do it by hand three times. Sandbox configuration is not a financial transaction. Pattern-matching the shape of an action instead of its substance cost the operator real time and was correctly called out.

**What it got right** was structural, not analytical: blocks written with conditional deliverables ("implement only if D1 proves it") stopped a wrong fix from shipping on the `exchange_index` theory, and a rehearsal-before-live-write block caught a resolver crash three days before it would have hit the real ledger. Keep that pattern.

---

## §9 — DO NOT — standing, carry forward verbatim

- **Never bypass, disable, or work around a permission control.** Record the exact refusal and hand back.
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair a derived file without establishing provenance first (GG-228 — and see GG-295 for what happens when this is ignored).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport or market family on one finding.
- Modify or re-time an existing price-capture window. Adding a missing day or series is different.
- Restart a production service without a scoped, written authorization.
- Add a cron entry for any T1 game-market run script without explicit operator authorization.
- Pre-assign T-/GG- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the running process, not the file on disk, contains it.
- Manufacture a position, a row, a cohort member, or a final score to have something to measure.
- Revive `exchange_index` propagation — tested and disproved (T-558).
- Submit an order against the production Kalshi account or with real funds. Demo only, always.
