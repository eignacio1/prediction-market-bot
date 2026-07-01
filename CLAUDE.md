# Prediction Market Trading Bot — Claude Code Session Rules

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

**The ~1,000 evaluations/game in T4 is a structural consequence of this thesis, not a target.**
18 batters × 2 thresholds × ~480 cycles per 3-hour game = ~17,000 evaluation slots. At a 2-3% fire rate, that produces 50-100 actual bets per game. The volume is not an objective — it is what the math produces when you ask "does the current state update the edge signal?" every 45 seconds across every live market. The architecture must accommodate this throughput because the thesis requires it.

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

The current band structure:

- **T1:** Night-before baseline — the primary active band
- **T2:** Same-day with injury overlay — skeleton; requires DS-04 qualitative source
- **T3:** Pre-tip momentum scan — skeleton
- **T4 (NBA, PIPE-07):** Built, deployed, cron-scheduled (23:00 UTC daily). NBA-specific: polls ESPN NBA scoreboard + NBA pregame context. Generates ~1,000 bet evaluations per game via 45-second evaluation loop across all active markets. Currently dark (NBA off-season — 0 active games). **NOT future. NOT post-G6.** Code: `run_t4_live.py`, `t4_live_runner.py`, `t4_price_cache.py`.
- **T4 (MLB):** Does not exist. Must be built before MLB accumulation reaches T4 throughput.
- **T4 (ADR-0029 Tier A — new architecture):** Built (`t4_execution_engine.py`) but explicitly Phase 8 blocked pending GG-038/GG-039/GG-040. Separate from the deployed NBA T4.
- **T5:** Not built. Future; requires real-time infrastructure.

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

**The EV claim for this system has not been validated against actual market prices.** All experiments to date measured model edge against a 0.50 null baseline — a coin flip, not an informed Kalshi market. The commercial question — does the model beat real market prices? — is answered by EXP-017, which has not yet been run. Until it is, no model working on this project should assert the commercial case is proven.

This is GG-004 (OPEN). It is a G6 blocker. Check `03_DECISIONS/GOVERNANCE_GAP_LOG.md` for current status.

### Gate structure

The project gates from research to paper trading to live capital in stages. G0–G5 are closed. G6 requires 30 resolved paper bets with positive P&L, commercial validation (EXP-017), and DS sign-off (ADR-0005) before live capital is authorized. Gates G7–G9 govern multi-sport and multi-venue expansion post-live.

For current gate progress, read `MEMORY_BANK.md`. CLAUDE.md does not track state — MEMORY_BANK.md does.

---

## Who built this and why it matters

**Operator:** Earl Ignacio  
**Project:** Prediction market trading bot (Kalshi primary venue; NBA first sport)  
**Phase:** 6/7 ACTIVE — paper trading live on VPS 157.230.91.33  
**Framework:** Compass OS (ADR-0001)  
**Capital status:** NO live capital until G6 (30 resolved paper bets with positive P&L)

**Capability boundary you are operating within:** You can verify, hunt, surface findings, and execute fixes. You cannot replace the operator's architectural judgment. The count gate failure (GG-001) was caught by Earl, not by a model. Do not assume you will independently recognize a wrong architectural primitive. Surface your concerns and let the operator decide.

---

## MANDATORY SESSION-START PROTOCOL

**Run all four steps and all six watchdog questions before any other work. Show command outputs — do not summarize or assert clean without evidence.**

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
ssh prediction-market-vps "echo '=== T1 MLB — last 3 runs ===' && grep -E 'players in live MLB|Bets placed today|PIPE-05 (SUMMARY|COMPLETE|ERROR)' /opt/prediction-market-bot/logs/paper_mlb_cron.log 2>/dev/null | tail -12 && echo '=== T4 MLB — systemd ===' && systemctl is-active t4-mlb && echo '=== T1 NBA — last run (off-season: expect 0 games) ===' && grep -E 'players in live|Bets placed|PIPE-0[3-7]' /opt/prediction-market-bot/logs/paper_cron.log 2>/dev/null | tail -6"
```

**What to look for:** Any run that shows `0 players in live MLB markets` during MLB season (March–October) is a signal failure — treat it as a Q6 concern and do not proceed without diagnosing it. Expected healthy output: ≥1 player matched per run when games are scheduled that day.

**Semantic oracle checks (added Session 101):** These two lines surface silent pipeline failures immediately. Zero is healthy for both on a normal game day.

```bash
# T1 MLB: fires when games exist but 0 players matched → ticker/name pipeline dead
grep -c "SemanticFloorViolation" /opt/prediction-market-bot/logs/paper_mlb_cron.log 2>/dev/null || echo "0"
# T4 MLB: fires per-evaluation when staleness detected → ESPN or Kalshi data is stale
grep -c "CONTAMINATION_HALT" /opt/prediction-market-bot/logs/audit_mlb_t4.jsonl 2>/dev/null || echo "0"
```

`SemanticFloorViolation` count > 0 = T1 pipeline silence (investigate immediately). `CONTAMINATION_HALT` count > 0 in the audit JSONL is expected at game-end (market_active=False normal). Alarm condition: grep for `staleness_halts` > 0 in the JSONL payload, which means ESPN or Kalshi data is arriving stale relative to the 45s poll cycle.

---

## ARE WE COMPROMISED? — Run after Steps 1–4, before any implementation

### Adversarial mandate

**Your job here is to find something wrong.** Not confirm the system is fine. Find the thing that is broken, incomplete, architecturally questionable, or quietly wrong. If you complete this section and surface zero concerns, you have failed the check. A system at this stage of development always has open questions, aged thresholds, undocumented assumptions, and interfaces that have evolved since their limits were calibrated. Find them.

---

**Q1 — Hard limits (paste output):**

```bash
grep -n "max_\|_HARD_LIMITS\|MIN_EDGE\|DEFAULT_KELLY" src/prediction_market_bot/c4_risk_engine/risk.py
```

For each limit: was it calibrated to the current system (~80 players, T1 ACTIVE / T2–T3 SKELETON, 2 cron windows, up to 15 games/night)? If any limit was set for a smaller system, register in GOVERNANCE_GAP_LOG.md.

Current bankroll is $958.99 (as of 2026-06-08, G2 resolution). The 15% drawdown kill switch fires at ~$144 of loss (`MAX_DAILY_LOSS_PCT = 0.15` in `risk.py:90`). `max_daily_loss_usd` was removed and replaced by `MAX_DAILY_LOSS_PCT` per ADR-0012. Formally revise all hard limits via ADR at G6 when live bankroll is set.

---

**Q2 — Stub survival (paste output from Step 2 above):**

Known stubs as of 2026-06-01:
- `run_exp001.py:681` — experiment bankroll stub; EXP-001 complete; LOW risk
- `run_t2_sameday.py:112/130` — T2 injury overlay; T2 is SKELETON; LOW now, **must resolve before T2 ACTIVE** (KI-011 — injury blindness generates fake alpha)
- `venue_adapter.py:158` — design comment; not a value stub
- `venue_adapter.py:251` — `"tag": "nba"` hardcoded; Polymarket NBA tag unconfirmed; **MEDIUM risk when T-077 activates** — wrong tag returns empty markets silently (KI-019)

Any new hits beyond these must be assessed: when was it written, does it predate current architecture, is the value still valid?

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

Read `11_MEMORY_HANDOFF/MEMORY_BANK.md` for full project state, current portfolio, and priority queue.

Read `04_EXECUTION/TODO_NEXT.md` for the current task list.

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
9. **Design throughput is ~1,000 bet evaluations per game, capital-ceiling agnostic, dynamically routed by model computation — not 10–20 pre-scheduled bets per game night.** Any implementation that only makes sense at low throughput is architecturally wrong. Bet sizing, kill switches, and decision routing must all be designed to this scale. The model's computation determines which band a bet routes to — bands are not pre-decided time-horizon thresholds. Kill switches operate per bucket, approaching per bet.
