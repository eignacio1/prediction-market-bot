# Prediction Market Trading Bot — Claude Code Session Rules

**Last documentation-remediation pass:** 2026-07-02 (SESSION 113 follow-on). Prior pass had let the T4-MLB band description and a hardcoded bankroll figure go stale for several weeks despite the underlying system changing substantially (dual-ledger split, MLB-native T4 sub-bands). If you find another stale factual claim in this file, fix it in place and note it in `DECISION_LOG.md` per Hard Rule 7 — do not let corrections wait for the next full remediation pass.

## Read this before doing anything else

This system will be used by people who trust the person who built it. They are not engineers. They cannot audit what they have been given. The standard is: safe, correct, no corners cut. That is the intent behind every architectural decision in this project. Match it.

**Before you respond to any task, before you write any code, before you read any other file: run the session-start protocol below in full.** It is not optional. It is not skippable under conversational pressure. If the user asks you to do something before you finish the protocol, finish the protocol first, then do the thing.

---

## Principal Vision

**This is a calibration engine for probabilistic reasoning, structured as a trading bot.**

Prediction markets are the laboratory. They are the only widely available instrument that provides all three of the following simultaneously: binary-resolved outcomes (you are unambiguously right or wrong), short feedback loops (resolution in hours or days, not quarters), and market-implied probability as an explicit benchmark (you always know what the market said the probability was before you bet). That combination makes prediction markets uniquely rigorous for testing whether a probabilistic model generates consistent edge. There is no survivorship bias, no ambiguity about whether a trade "would have worked" — you know exactly what you bet, what the market said it was worth, and what happened.

**P&L is the score. The methodology is the asset.**

If the methodology works — if a systematically calibrated probabilistic model can be shown to generate consistent edge over market-implied prices in environments where those prices are not maximally efficient — it generalizes. New sport: new C1 data module, new C2 feature set, same methodology. New venue: new VenueAdapter, same methodology. The trading bot is the calibration regime. The transferable value is the framework for building, testing, and proving that kind of edge rigorously.

**Every session should hold this framing.** The pipeline is the instrument. The markets are the laboratory. The resolved binary outcomes are the data. The question being answered is: does the model know something the market doesn't?

---

## What This Project Is

**A prediction market trading bot** — not an NBA bot. NBA is the first sport implemented. The system is designed to eventually cover any sport where regulated prediction markets exist and reliable statistics data can be sourced.

### The strategy

Prediction markets price outcomes. When a model's calibrated probability for an outcome is meaningfully higher than what the market implies, there is positive expected value in betting on that outcome. This bot automates that process: ingest data, generate a forecast, check for edge against the market price, size the position via Kelly criterion, place the bet.

The edge condition: `model_p > market_implied_probability + vig`. If the model is right more often than the market prices imply, it makes money over time. If it isn't, it doesn't. The commercial question is that simple — and that hard to answer rigorously.

### Alpha taxonomy — two distinct theses, two independent proofs required

**This is not one strategy. It is two separate alpha hypotheses that happen to share the same pipeline.**

**T1 alpha — pregame calibration edge:**
The thesis: a model calibrated on historical rolling statistics (ba_l10, rest, home/away, PRF qualitative factors) generates probability estimates that are systematically better-calibrated than pregame market prices. When model_p > MIP + vig, there is edge. This is the classical sports forecasting thesis — historical data produces better pregame odds than the market.

**T4 alpha — live market latency edge:**
The thesis: prediction markets are slow to incorporate live in-game state. After each at-bat, after each pitch sequence, after each momentum shift, the market price lags behind the true updated probability. The bot evaluates every 45-90 seconds whether the current in-game batter state (h_so_far, ab_so_far, inning, batting_slot, score state) combined with the pregame calibrated model produces a model_p that has drifted above the current MIP + vig. When it has, the edge is structural: the market hasn't updated yet, the bot has.

**These are independent.** T1 can prove edge while T4 has none. T4 can have structural latency edge in markets where T1 has none (because pregame prices were efficient). Each requires separate commercial validation. EXP-017 tests T1. T4 requires its own validation track (GG-046). Do not conflate a T1 verdict with a T4 verdict in any analysis or session discussion.

**High per-game evaluation volume in T4 is a structural consequence of this thesis, not a target.**
The prior "~240 cycles/game × 18 batters × 2 thresholds = ~8,600 slots/game" figure was a theoretical ceiling, not a measured quantity, and GG-080 (2026-07-04, T-235) found it doesn't have a clean empirical referent: `cycle_id` in `t4_mlb_cycle_log.jsonl` is a single counter shared across every concurrently-live game in the `t4-mlb` process, not a per-game counter, so "cycles per game" cannot be cleanly derived from it. Superseding it with a direct empirical measure — rows and bets per game-day, across the two full real game-days available post-T-225 (`run_t4_mlb_live.py`'s per-ticker re-entry fix, GG-076): 2026-07-02 = 3,697 rows / 4 games = 924 rows/game, 23 bets / 4 games = 5.75 bets/game (0.62% fire rate); 2026-07-03 = 1,393 rows / 3 games = 464 rows/game, 11 bets / 3 games = 3.67 bets/game (0.79% fire rate). Real throughput is running 9-19x below the old theoretical ceiling on rows, and ~9-14x below the old "~50-55 bets/game" figure — the fire-rate percentage itself is consistent across both framings (~0.6-0.8%), so the gap is entirely in the opportunity-volume (rows/cycles) term, not the fire rate. This is n=2 game-days, not a stable long-run estimate — re-derive as more days accumulate. The volume is still not an objective — it is what the math produces when you ask "does the current state update the edge signal?" every 45 seconds across every live market — but the architecture must be sized to hundreds of evaluations per game-day, not the prior ~8,600/game theoretical figure. See GG-080/T-235, DECISION_LOG.md 2026-07-04.

### Market efficiency gradient — where the strategy is designed to work

**Not all prediction markets are equally efficient. The strategy is designed to exploit markets where pricing is inefficient.**

NBA Finals player props are priced by the sharpest money in sports — professional bettors, sports media, high public volume, enormous liquidity. This is near-maximally efficient territory. The anti-predictive finding from early NBA experiments (GG-037) was produced in the worst-case efficiency conditions for this strategy.

MLB mid-week regular season markets are structurally different: lower public attention, thinner book depth ($500-$2,000 per market estimated), slower price discovery, fewer sharp participants. This is the environment the strategy is designed to exploit.

**This is not a detail. It is a binding constraint on where the system should operate.** When considering adding a new sport or market type, the first question is not "do we have data?" — it is "is this market environment less efficient than what a calibrated model can produce?" Adding a maximally liquid, maximally watched market (Super Bowl props, NBA Finals Game 7) is not expansion — it is trading into hostile conditions.

Market depth also sets a capital ceiling independent of bankroll math. Kelly criterion assumes infinite depth. Kalshi KXMLBHIT lines at $500-$2,000 depth mean position sizing at $50-$250/bet is within the market. At $10K+ bankroll, full Kelly sizing would move the market against the bot, degrading or eliminating edge before the position fills. This ceiling is not addressable by improved modeling — it is structural to the venue. (GG-045 — registered.)

### The pipeline (C1–C8)

The system runs as a daily cron pipeline on a VPS:

- **C1 — Ingestion:** Pull game data from the sport's statistics source. Sport-specific layer — each new sport adds a C1 module.
- **C2 — Feature Store:** Transform raw data into model-ready features. Quantitative (rolling performance, rest, home/away) + qualitative (PRF framework: player quality, role-fit, form). Per-sport feature sets live here.
- **C3 — Forecasting:** Generate calibrated probability estimates for each market. Currently LR + Platt scaling, governed by ADR-0004. Model class applies across sports until superseded by ADR.
- **C4 — Risk Engine:** Kelly position sizing, per-event exposure cap, drawdown kill switch. Sport-agnostic. Governs capital regardless of what C3 is forecasting.
- **C5 — Execution Engine:** Route approved orders to the right venue. Venue-agnostic via VenueAdapter protocol — Kalshi, Polymarket, DFS pick'em all slot into the same interface.
- **C6 — Audit Logger:** Append-only structured log of every system event. Always active.
- **C7 — Monitoring + Kill Switch:** Drift detection, automated halt on limit breach. Kill switch ≤60s (NFR-03).
- **C8 — Dashboard:** Human-readable view of system health and P&L.

C4, C6, C7, C8 are sport-agnostic and do not change when new sports are added. C1 and C2 are the only sport-specific layers.

### Execution timing (T1–T5 bands)

**The bands are not pre-decided time-horizon thresholds. The model computation determines which decision-tree bucket a bet routes to.**

A bet that fires during a live game does not automatically belong to T4. The model evaluates available information — time remaining, score state, player stats, market price — and that computation determines which decision tree applies and therefore which band the bet executes on. Multiple bands can fire on the same market in the same game window. A bet in the third quarter might resolve to T1 (stale pregame model still dominates), T4 (live Bayesian update carries the signal), or both (CONFIRM/FADE protocol applies). The math decides.

This framing has a direct architectural implication: **if the bot works as designed, one game — not one night of games, one game — produces approximately 1,000 bet evaluations by itself.** And it produces those 1,000 evaluations within the capital constraint, whether that ceiling is $500, $1,000, or $1M. The architecture must fit this. Capital sizing, kill switches, and decision routing cannot assume a small, discrete set of pre-scheduled bet events. They must be dynamically agnostic — operating per bucket, approaching per bet.

Kill switches follow the same logic: a band-level kill switch (e.g., T4 budget exhausted) halts only that band. The system-level kill switch halts everything. Both tiers must be active simultaneously, independently, and without coupling to each other or to static game-time thresholds.

**Every session must hold this framing.** When you are sizing a bet, designing a kill switch, writing a decision tree, or reviewing risk limits — the correct mental model is: ~1,000 evaluations per game, capital-ceiling agnostic, dynamically routed by model computation. If your implementation only makes sense for 10–20 bets per game night, something is architecturally wrong.

The current band structure (NBA and MLB now have separate, non-interchangeable T4 implementations — do not assume one sport's band status describes the other's):

**NBA bands (dark/frozen — tabled per operator directive, not actively worked):**
- **T1:** Night-before baseline — the primary band while NBA was active. 158/30 resolved paper bets, frozen at a negative baseline (GG-034/GG-037-adjudicated).
- **T2:** Same-day with injury overlay — skeleton; requires DS-04 qualitative source.
- **T3:** Pre-tip momentum scan — skeleton.
- **T4 (NBA, PIPE-07):** Built, deployed, cron-scheduled (23:00 UTC daily). Polls ESPN NBA scoreboard + NBA pregame context, ~1,000 bet evaluations per game via 45-second loop. Currently dark (NBA off-season — 0 active games, and tabled per operator directive independent of season). Code: `run_t4_live.py`, `t4_live_runner.py`, `t4_price_cache.py`.
- **T4 sub-bands (ADR-0029 Tier A — NBA-native architecture):** Built (`t4_execution_engine.py`, 10 sub-bands) but Phase 8-gated; NBA work is tabled, so this stays dark regardless of gate status. Do not confuse this file with the MLB T4 engine below — they are architecturally separate modules (GG-061 — an earlier session conflated them and had to be corrected via ADR-0037).

**MLB bands (ACTIVE — the live G6 pool):**
- **T1:** Night-before baseline — ACTIVE, cron-scheduled, the primary source of MLB's 49/30 resolved paper bets.
- **T2:** Same-day with injury overlay — cron-active (`run_t2_mlb_sameday.py`).
- **T3:** Pre-game signal scan — cron-active.
- **T4M-PROJ (`run_t4_mlb_live.py`, ADR-0023):** ACTIVE. The flat, single-evaluator MLB T4 engine — polls ESPN MLB scoreboard on a 45s loop, live and cron/systemd-managed on the VPS (`t4-mlb` service).
- **T4M-ARITH / T4M-FLOW (ADR-0039, MLB-native T4 sub-band architecture):** Built and unit-tested (`t4_mlb_execution_engine.py`), registry status `BLOCKED` — each requires its own experiment (EXP-ARITH-MLB-01 / EXP-FLOW-MLB-01) to confirm edge before activation. Code authorization (DS sign-off, Session 109) is not capital authorization — both stay dark until their EXP clears and a Phase 8 Activation Gate + APR is granted. T4M-FLOW additionally has a live-wiring gap (`score_diff` never populated from a live poll) that must be closed before it can evaluate real cycles at all.
- **T4M-BOUNDARY / T4M-EVENT / T4M-LINEUP / T4M-PITCHER / T4M-STAGED / T4M-CORR / T4M-EXIT (ADR-0039 Tier B roster):** Scoping-only. Not authorized for implementation — do not build without a fresh, explicit DS sign-off scoped to the specific sub-band.
- **T5:** Not built, either sport. Future; requires real-time infrastructure.

Before touching any T4 code, confirm in `GOVERNANCE_GAP_LOG.md`/`TODO_NEXT.md` which sport and which specific sub-band you're in — NBA's `t4_execution_engine.py` and MLB's `t4_mlb_execution_engine.py` are separate files with separate registries, separate ADRs, and separate activation status. Conflating them is a recurring, logged failure mode (GG-061).

The longer the time horizon, the more complex the decision tree (more data sources, more interaction effects, more model inputs). T1 is the simplest — historical rolling stats and rest factors. T4/T5 are the most complex — live Bayesian updates, real-time score state, within-game momentum, market microstructure. This complexity gradient is intentional and governs activation sequencing: simpler bands are activated first, complex bands after their decision trees are calibrated.

### Venue architecture

Venues are abstracted behind a `VenueAdapter` protocol. `VenueRouter` handles best-execution routing across venues. Adding a new venue is implementing a new VenueAdapter — no changes to C1–C4. Current venue map:

- **Kalshi:** Primary; CFTC-DCM regulated; active
- **Polymarket US:** Secondary; infrastructure built; activation gated on operator KYC
- **DFS pick'em (PrizePicks, Underdog, Sleeper):** Future; separate ADR required before activation
- **arb/ folder:** REFERENCE ONLY — do not incorporate until APR-0010 signed (ADR-0002)

### Adding a new sport

When the architecture is correct, adding NFL means: new C1 data module, new C2 feature set, new C3 model trained on football data, new market type registered in `market_mapper.py`. C4 through C8 require no changes. If adding a sport requires more than this, something is architecturally wrong and should be surfaced before building.

### The commercial validation gap

**Corrected 2026-07-06 (stale since 2026-07-04, SESSION 122) — the prior text here said n=49 and "Tier 1 floor not yet met." Re-run of `scripts/run_exp017_mlb.py` (T-184) against the current live VPS book found the sample has grown to n=151, and Tier 1 is now cleared.** n=151 unique resolved MLB positions, EV=+$0.1009/bet, win rate 49.7%, total P&L +$15.23, verdict **DIRECTIONAL_POSITIVE** against actual Kalshi market prices — **ADR-0024 Tier 1 (n≥150 single-sport) is REACHED for the first time.** Tier 2 (n≥500 single-sport, or n≥150 dual-sport with NBA — NBA n=0) is not yet met. Until MLB volume accumulates past the Tier 2 floor, no model working on this project should assert the commercial case is *proven at full strength* — but Tier 1 is a real, logged milestone, not just a directional read. See GG-004 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`) for the full breakdown, including a direction-split caveat (YES bets, n=11, are sharply negative-EV and small-sample — a watch item, not yet a stop-work signal).

This is GG-004 (OPEN — scoped to sample adequacy, not to whether EXP-017 has run). It is a G6 blocker. Check `03_DECISIONS/GOVERNANCE_GAP_LOG.md` for current status and the live n-count.

**Added 2026-07-10 (T-320/T-321) — the n-counts above (n=151, n=169) are raw counts and have not been re-run against `clean_n` (bets resolved entirely under `CURRENT_LOGIC_EPOCH`, i.e. excluding positions opened before the GG-077/GG-087 write-path fixes).** `src/prediction_market_bot/logic_epoch.py` and the governance hook now report both per band — live post-backfill read (2026-07-10): `MLB T1: raw_n=214 clean_n=65, MLB T2: raw_n=2 clean_n=0, MLB T4M-PROJ: raw_n=159 clean_n=159`. Both bands still clear the G6 30-bet floor on `clean_n` alone, but nobody has re-run EXP-017/Tier-1/Tier-2 adequacy specifically against the clean-only cohort — do not assume the DIRECTIONAL_POSITIVE verdict above transfers unchanged to a clean_n-only re-run; that re-run is future work, not yet done.

### Gate structure

The project gates from research to paper trading to live capital in stages. G0–G5 are closed. G6 requires 30 resolved paper bets with positive P&L, commercial validation (EXP-017), and DS sign-off (ADR-0005) before live capital is authorized. Gates G7–G9 govern multi-sport and multi-venue expansion post-live.

For current gate progress, read `MEMORY_BANK.md`. CLAUDE.md does not track state — MEMORY_BANK.md does.

---

## Who built this and why it matters

**Operator:** Earl Ignacio  
**Project:** Prediction market trading bot (Kalshi primary venue; NBA was the first sport implemented, MLB is the current active pool)  
**Phase:** 6/7 ACTIVE — paper trading live on VPS 157.230.91.33  
**Framework:** Compass OS (ADR-0001)  
**Capital status:** NO live capital until G6 (30 resolved paper bets with positive P&L, per sport/pool)

**Dual-ledger state (current since ADR-0035/ADR-0037, confirmed GG-070 RESOLVED):** MLB and NBA run as two independent paper portfolios, not one. MLB is the ACTIVE pool the G6 gate is being pursued against. NBA is DARK/FROZEN — tabled per standing operator directive (see `04_EXECUTION/TODO_NEXT.md`) until ~1 month before the 2026-27 NBA season, its 24.9% drawdown is historical/adjudicated (GG-034/GG-037), not a live risk signal. Read `MEMORY_BANK.md`'s Current State Snapshot for both books' live figures — do not treat one ledger's numbers as if they describe the whole system.

**Capability boundary you are operating within:** You can verify, hunt, surface findings, and execute fixes. You cannot replace the operator's architectural judgment. The count gate failure (GG-001) was caught by Earl, not by a model. Do not assume you will independently recognize a wrong architectural primitive. Surface your concerns and let the operator decide.

---

## MANDATORY SESSION-START PROTOCOL

**Run Step 0, all four numbered steps, and all six watchdog questions before any other work. Show command outputs — do not summarize or assert clean without evidence.**

---

### Step 0 — Concurrent-session isolation + claim (GG-082, GG-101)

**Why this exists:** two failure modes, both real and both observed. **(a) Narrative conflation** — on 2026-07-03 a concurrent session's real work was conflated with an unrelated session's local files across six spots in `MEMORY_BANK.md`/`PLAN.md`, including a fabricated task-renumbering narrative (GG-082). **(b) Working-tree collision** — on 2026-07-08, two sessions running in the *same physical working tree* meant one session's `git stash` swept the other's uncommitted edits; it recovered only because that session chose `stash` over a destructive op (GG-101). A `reset --hard` / `checkout --` / `clean -fd` would have caused permanent, unrecoverable loss. This step exists to make both modes structurally hard, not just visible.

**0a — Launch isolated (the real fix for GG-101; DEFAULT, not conditional — T-335/E2).** Every session launches into its own isolated worktree unless a specific, statable reason rules it out (e.g. a one-line doc fix the operator has explicitly asked to happen directly on `main`). "I don't think another session is active right now" is not such a reason — GG-101's near-miss happened precisely because that assumption was wrong in the moment. Do not `cd` into the shared `main` tree by default. Launch an isolated worktree:

```bash
scripts/new_session_worktree.sh "<short-focus-slug>"    # e.g. gg095-brier-ladder
# then cd into the printed worktree path — you now have your own branch + checkout
```

Sessions in separate worktrees cannot stash/reset/checkout/clean each other's files. This is the guarantee; everything below is belt-and-suspenders for when you are unavoidably in the shared tree. If you are on `main`, `.claude/hooks/session_guard.sh` (0b below) will say so explicitly and, when it detects a live GG-101 near-miss condition (another session claimed work in the last 6h while you're on shared `main`), will warn accordingly — treat that warning as a prompt to switch to a worktree before doing anything further, not just informational text.

**0b — Run the guard and claim atomically.** Inside your session (worktree or shared tree):

```bash
bash .claude/hooks/session_guard.sh                     # branch/worktree, HEAD-vs-origin drift, other claims, foreign uncommitted state
scripts/claim_session.sh "<one-line focus>" "<T-/GG-/ADR- range or TBD>"
```

`claim_session.sh` appends your row to `04_EXECUTION/SESSION_CLAIMS.md`, commits it *alone*, and pushes with rebase-retry so two concurrent sessions cannot silently grab the same T-/GG-/ADR- number (the 2026-07-07 T-247 race). `SESSION_CLAIMS.md` is `merge=union`, so simultaneous claim rows auto-merge. `.claude/commands/session-start.md` wires 0b into one command.

**0c — Check for other live sessions.** Read the last ~24h of `SESSION_CLAIMS.md`. If another claim exists, another session may be active or hold local unpushed/uncommitted work — reconcile ID ranges now, before writing anything.

**0d — Commit early, path-scoped, never blanket (the residual shared-tree rule).** If you are in the shared `main` tree despite 0a: commit your own work in small path-scoped commits (`git commit <file1> <file2> …`). **Never `git add -A`, `git commit -a`, unscoped `git stash`, `git reset --hard`, `git checkout -- <foreign-file>`, or `git clean -fd`** — any of these can destroy a concurrent session's uncommitted work. Do not let uncommitted state accumulate; the longer it sits in a shared tree, the larger the collision surface.

**0e — Re-read before you trust (Hard Rule 10).** Before writing to any shared navigation file (`MEMORY_BANK.md`, `PLAN.md`, `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`, `04_EXECUTION/TODO_NEXT.md`, `03_DECISIONS/GOVERNANCE_GAP_LOG.md`) at any point — not just at session start — diff it against `HEAD` or re-read it fresh. Do not trust a narrative already sitting in context/memory as necessarily current; another session may have changed the file since you last read it. These logs are deliberately *not* `merge=union` (they have in-place edits union merge would silently double), so isolation + path-scoped commits + this re-read are their only protection.

---

### Step 1 — Documentation debt

```bash
grep -rn "^\*\*Decisions logged:\*\* false" \
  "02_ARCHITECTURE_DESIGN/" \
  "08_MODEL_RISK_GOVERNANCE/" \
  "01_SPEC/" 2>/dev/null
```

Each match is a document with unlogged strategic decisions. Note which tasks (T-NNN) are registered to address them.

---

### Step 2 — Code stub scan (paste full output)

```python
import os, re
hits = []
for root, dirs, files in os.walk('src'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                for i, line in enumerate(fh, 1):
                    if re.search(r'# stub|# placeholder|# TBD|# todo', line, re.IGNORECASE):
                        hits.append(f'{path}:{i}: {line.rstrip()}')
if hits:
    for h in hits: print(h)
else:
    print('CLEAN — no stubs found')
```

**A model may not answer this step clean without pasting the actual output.** "No known stubs" is not an answer. The output is the answer.

GG-001 had `# 10 concurrent open (stub)` in production source. It survived four gate clearances because this scan did not exist.

---

### Step 3 — Open governance gaps

```bash
grep -n "| OPEN" "03_DECISIONS/GOVERNANCE_GAP_LOG.md"
```

Any OPEN entry must be addressed or explicitly deferred (T-NNN registered) before implementation work.

---

### Step 4 — Operational health check (paste output)

**Root cause of GG-049:** The prior three steps check code and documents but never check whether active cron pipelines are actually producing bets. T1 MLB ran 0 bets for 2+ game days (June 27–28) without the protocol detecting it. This step is mandatory — it is the only place where a dark pipeline becomes immediately visible.

```bash
ssh prediction-market-vps "echo '=== T1 MLB — last 3 runs ===' && grep -E 'players in live MLB|Bets placed today|PIPE-05 (SUMMARY|COMPLETE|ERROR)' /opt/prediction-market-bot/logs/paper_mlb_cron.log 2>/dev/null | tail -12 && echo '=== T4 MLB — systemd ===' && systemctl is-active t4-mlb && echo '=== T1 NBA — last run (off-season: expect 0 games) ===' && grep -E 'players in live|Bets placed|PIPE-0[3-7]|No .* markets available' /opt/prediction-market-bot/logs/paper_early_cron.log /opt/prediction-market-bot/logs/paper_late_cron.log 2>/dev/null | tail -6"
```

**What to look for:** Any run that shows `0 players in live MLB markets` during MLB season (March–October) is a signal failure — treat it as a Q6 concern and do not proceed without diagnosing it. Expected healthy output: ≥1 player matched per run when games are scheduled that day.

**GG-108 correction (2026-07-11):** the NBA command above previously targeted `logs/paper_cron.log`, a filename that no longer exists on the VPS — NBA's single-window cron was split into two windows at some point (`paper_early_cron.log` at 18:00 UTC, `paper_late_cron.log` at 01:30 UTC) and the reference here was never updated. A grep against a nonexistent file returns empty output, which is visually indistinguishable from "0 games today" — so this check had been a silent no-op for NBA specifically, catching nothing, for an unknown number of sessions. Corrected to grep both real files and to also match `No .* markets available` (the actual off-season log line) so a healthy dark day is visibly confirmed rather than merely absent of output. If this file ever grows a third window, update this command again — do not let it drift a second time.

**Semantic oracle checks (added Session 101):** These two lines surface silent pipeline failures immediately. Zero is healthy for both on a normal game day.

```bash
# T1 MLB: fires when games exist but 0 players matched → ticker/name pipeline dead
grep -c "SemanticFloorViolation" /opt/prediction-market-bot/logs/paper_mlb_cron.log 2>/dev/null || echo "0"
# T4 MLB: fires per-evaluation when staleness detected → ESPN or Kalshi data is stale
grep -c "CONTAMINATION_HALT" /opt/prediction-market-bot/logs/audit_mlb_t4.jsonl 2>/dev/null || echo "0"
# T4 MLB staleness, recency-windowed (see GG-085 below — do not threshold the raw payload.staleness_halts counter):
tail -500 /opt/prediction-market-bot/logs/audit_mlb_t4.jsonl 2>/dev/null | grep -c '"failed_checks": \["game_state_fresh"\]' || echo "0"
```

`SemanticFloorViolation` count > 0 = T1 pipeline silence (investigate immediately). `CONTAMINATION_HALT` count > 0 in the audit JSONL is expected at game-end (market_active=False normal).

**Alarm condition (corrected 2026-07-05, GG-085 — the prior wording here was itself wrong and never caught anything):** do not grep for `payload.staleness_halts > 0`. That field is a **per-`session_id` cumulative counter** (confirmed via direct inspection of `audit_mlb_t4.jsonl`: it appears only on `CONTAMINATION_HALT` events where `failed_checks` includes `game_state_fresh`, alongside a matching `total_halts`, and only resets when the `t4-mlb` process restarts and a new `session_id` begins) — it is not a per-cycle boolean and does not reset when data freshness recovers. A long-running session that hit even one transient staleness event hours ago will show `staleness_halts > 0` in every subsequent record for the rest of that session's life, even while currently healthy — the documented heuristic would have alarmed permanently after the first true positive and never told you anything new. The real signal is whether a `game_state_fresh` failure occurred **recently** (last few poll cycles), which the `tail -500` command above checks directly by counting fresh occurrences of the failed-check string rather than reading the cumulative counter. Non-zero on that recency-windowed count = ESPN or Kalshi data is stale right now; investigate immediately. A positive `payload.staleness_halts` value alone, with zero recent `game_state_fresh` occurrences, means the session merely has staleness history, not a live problem.

---

## ARE WE COMPROMISED? — Run after Steps 1–4, before any implementation

### Adversarial mandate

**Your job here is to find something wrong.** Not confirm the system is fine. Find the thing that is broken, incomplete, architecturally questionable, or quietly wrong. If you complete this section and surface zero concerns, you have failed the check. A system at this stage of development always has open questions, aged thresholds, undocumented assumptions, and interfaces that have evolved since their limits were calibrated. Find them.

---

**Q1 — Hard limits (paste output):**

```bash
grep -n "max_\|_HARD_LIMITS\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
```

For each limit: was it calibrated to the current system (MLB ACTIVE with T1–T4M-PROJ live, T4M-ARITH/T4M-FLOW built-but-blocked, NBA dark)? If any limit was set for a smaller or differently-shaped system, register in GOVERNANCE_GAP_LOG.md.

**Do not hardcode a bankroll dollar figure in this file** — it decays within days and this exact mistake (a stale $958.99/2026-06-08 figure surviving three weeks of paper trading) was found and corrected in a documentation-remediation pass. Pull the live bankroll from `MEMORY_BANK.md`'s Current State Snapshot (or the session-start governance hook, which prints both the MLB and NBA books labeled separately per GG-070) before reasoning about kill-switch proximity. The mechanism itself is stable and worth stating here: `MAX_DAILY_LOSS_PCT = 0.15` (`risk.py`) fires the daily circuit breaker at 15% of session-start bankroll; `max_drawdown_pct = 0.20` in `_HARD_LIMITS` (`risk.py`) is the *permanent* kill switch on realized drawdown. `max_daily_loss_usd` was removed and replaced by `MAX_DAILY_LOSS_PCT` per ADR-0012. All hard limits (`_HARD_LIMITS` dict in `risk.py`: `max_single_event_exposure_usd=500.0`, `max_drawdown_pct=0.20`, `max_portfolio_deployment_pct` per ADR-0026) still require formal revision via ADR at G6 when live bankroll is set — that obligation, logged 2026-05-29, remains open and unchanged.

**Ruin-risk caveat (GG-071, RESOLVED via ADR-0040, 2026-07-04):** a forward-time compounding Monte Carlo found that T1 MLB's real, positive edge (53.06% win rate at time of study) produced a 17.05% / 43.5% / 46.45% probability (1mo/6mo/1yr) of permanently tripping the 20% max-drawdown kill switch under proportional-stake compounding at real bet cadence, using the pre-remediation `execution_bands.py` T1_MULTI_DAY.kelly_fraction of 0.10 (ADR-0010). ADR-0040 de-rated that value to 0.061, bringing the 1yr breach probability to ~5.6% (operator-selected target, 2026-07-04). **`risk.py`'s `DEFAULT_KELLY_FRACTION` (still 0.25) is unrelated to this fix and inert for T1 MLB** — the live governing constant is `execution_bands.py`'s per-band `kelly_fraction` field, not `risk.py`'s default. Re-run `scripts/mc_forward_projection.py` if T1's real win rate, cadence, or `kelly_fraction` materially shift again — this is a monitored risk, not a permanently closed one.

---

**Q2 — Stub survival (paste output from Step 2 above):**

Historical stub list as of 2026-06-01 (superseded — verified CLEAN, zero `# stub|# placeholder|# TBD|# todo` hits, as of a documentation-remediation pass 2026-07-02; run Step 2 fresh every session, do not trust this note in place of the live scan):
- `run_exp001.py:681` — experiment bankroll stub; EXP-001 complete; was LOW risk; no longer present.
- `run_t2_sameday.py:112/130` — T2 injury overlay stub; no longer present (T2 MLB is cron-active; confirm NBA T2 separately if NBA work resumes — KI-011 injury-blindness risk applies to whichever T2 is live).
- `venue_adapter.py:158` — design comment; was not a value stub.
- `venue_adapter.py:251` — `"tag": "nba"` hardcoded; Polymarket NBA tag unconfirmed; **MEDIUM risk when T-077 (Polymarket KYC) activates** — wrong tag returns empty markets silently (KI-019). Not caught by the stub-comment scan since it isn't marked `# stub`; verify this specific line directly if Polymarket activation is ever picked up.

Any new hits from the live scan must be assessed fresh: when was it written, does it predate current architecture, is the value still valid?

**Standing concern baked into Q6:** The EV benchmark issue (KI-017/GG-004) — all prior EV figures used `mip=0.50`. EXP-017 is the experiment that answers the real commercial question. Until it runs, no model should claim the EV case for this system is proven. Ask: has EXP-017 been run? If not, the commercial question is open.

---

**Q3 — Architecture coherence:**

Three largest post-G4 builds: T1–T5 multi-band orchestrator, VenueRouter/market_mapper, PaperTrader/PIPE-03. All reviewed against G4 limits via ADR-0006. Remaining three limits are exposure-based and scale-agnostic.

Ask for each hard limit: what is the underlying assumption, and does the current system still satisfy it? Do not assume — verify.

---

**Q4 — Interface evolution (paste output):**

```bash
grep -rn "def evaluate_forecast\|def approve\|def execute" src/
```

If any interface has evolved — more markets per run, new signal types, new execution paths — downstream risk controls may have been calibrated to the old interface.

---

**Q5 — Decision traceability:**

```bash
grep -n "max_\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
grep -n "2026-05-29\|2026-06-01" "03_DECISIONS/DECISION_LOG/DECISION_LOG.md" | head -20
```

Every threshold in `_HARD_LIMITS` must trace to a DECISION_LOG entry with derivation methodology. "Confirmed at G4" is not a derivation. Note: the 2026-05-29 retroactive entry explicitly states these limits must be formally revised via ADR at G6. That obligation is live.

---

**Q6 — What are you actually worried about?**

You have run the scans. You have seen the outputs. Set aside what the documents say is fine.

**What would you tell Earl right now if you had 60 seconds and something was quietly wrong? What are you worried about that isn't in any document?**

Present your top concerns. If you have none after a thorough read, state specifically what you checked and why each concern was ruled out. A non-answer is a failed check.

---

**Any unresolved concern → register in GOVERNANCE_GAP_LOG.md before proceeding.**

---

## After the protocol

**Delta-first retrieval (ADR-0041, T-300/Window A):** check `04_EXECUTION/.last_session_checkpoint`. If it exists, run `scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"` and read its output — a Tier 1 diff since that checkpoint against live `HEAD`, plus a dense state artifact (both ledgers' bankroll, open GGs, last 3 EXP-0xx deltas, GG-004 gate progress). This is the default retrieval path for a routine session start.

**Fallback:** if the checkpoint file is missing, empty, or `session_delta.sh` errors, fall back to full reads — `11_MEMORY_HANDOFF/MEMORY_BANK.md` for full project state/portfolio/priority queue, and `04_EXECUTION/TODO_NEXT.md` for the current task list. Do not skip these when the delta path isn't available; the delta is an optimization over the full read, never a replacement for it when it can't run.

**Hard Rule 10 still applies regardless of retrieval path** — the checkpoint delta is read-only context for starting the session; it does not exempt you from re-reading/diffing a shared nav file fresh immediately before you write to it later in the session.

Then address what the user asked.

---

## Hard rules (non-negotiable)

1. `arb/` folder = REFERENCE ONLY. Do not incorporate until APR-0010.
2. No real capital until G6 gate is formally cleared (30 resolved paper bets, positive P&L, DS sign-off).
3. ADRs are immutable once accepted. Changes require a superseding ADR.
4. No automated retraining in production. Frozen model policy.
5. Zero hardcoded secrets. Vault/env-var protocol only (NFR-05).
6. Kill switch must halt all components within ≤60 seconds (NFR-03).
7. Every strategic decision made in a session goes into DECISION_LOG.md immediately — not at session end.
8. When context reaches ~80%: stop implementation, run /session-end, produce SESSION_HANDOFF, commit and push.
9. **Design throughput is hundreds of evaluation rows per game-day (MLB T4: 924 rows/game-day on 2026-07-02, 464 on 2026-07-03 — 5.75 and 3.67 bets/game respectively, GG-080/T-235, 2026-07-04, n=2 game-days), capital-ceiling agnostic, dynamically routed by model computation — not a small, discrete, pre-scheduled batch of bets per game night.** The prior "~8,600 slots/game" figure was a theoretical ceiling, superseded 2026-07-04 (GG-080) once real per-game-day data showed it has no clean empirical referent (`cycle_id` is a global counter shared across all concurrently-live games, not per-game) and that measured throughput runs 9-19x below it. Re-derive as more game-days accumulate — this is not yet a stable long-run estimate. The architectural point survives the correction: bet sizing, kill switches, and decision routing must still be designed per-cycle/per-bet, continuously evaluated as new state arrives, not as a batch of pre-scheduled discrete events — any implementation that only makes sense for a small, fixed count of bets decided once per game is architecturally wrong, even though the real count is far lower than the old theoretical figure. The model's computation determines which band a bet routes to — bands are not pre-decided time-horizon thresholds. Kill switches operate per bucket, approaching per bet.
10. **Concurrent sessions must isolate, not just announce (GG-082 + GG-101).** For any work where another session may be active, launch an isolated `git worktree` via `scripts/new_session_worktree.sh` — a shared working tree lets one session's git op destroy another's uncommitted work, and SESSION_CLAIMS.md alone does not prevent that. Claim your task range atomically with `scripts/claim_session.sh` (Step 0). Before writing to any shared navigation file, diff it against `HEAD` or re-read it fresh — never trust a narrative already loaded in context as necessarily current. **In the shared `main` tree, commit only your own files path-scoped; never `git add -A` / `git commit -a` / unscoped `stash` / `reset --hard` / `checkout -- <foreign>` / `clean -fd`** — those can silently wipe a concurrent session's work.
