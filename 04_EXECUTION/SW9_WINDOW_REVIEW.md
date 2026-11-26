# SW-9 window review — Waves 101 → 130 (2026-11-04 → 11-26)

**Written:** 2026-11-26 at the SW-9 handoff, at the operator's request (11-25 20:04 PT): "Give me a full comprehensive review of your
work from start to finish". **Sources:** WINDOW_ERROR_LOG (W45–W69), the queue's sequencing track and closed-wave rows, DECISION_LOG,
the box reads (`STATE_OF_THE_BOT.md` 11-26 03:15Z, `DISTANCE_TABLE_W129.md`), the earlier PDTP self-assessment
(`SW9_SELF_ASSESSMENT_PDTP.md`, Waves 104–126, scored 6 / 10). Numbers are from those sources; nothing here is from memory alone.

## 1. What the window was for

Thirty waves, three weeks, the longest window yet. The operator's frame for it:
- **"Let's build out the bot."**
- The routing doctrine he stated on 11-10: "a certain betting pattern doesn't beat the "market" ... he fucking routes it to the correct
  path so that loss still WINS".
- **The weekly rhythm:** waves of four to seven Sonnet blocks, Muse on Mondays, and the box reached only through the bridge.

## 2. What moved (start → handoff)

| Measure | Start of SW-9 | Handoff | Read |
|---|---|---|---|
| B1 cells logging / registered | 52 / 108 | **72 / 129** | +20 logging, +21 registered |
| B2 families | 17 / 19 | 20 / 26 | combos and in-play families registered |
| B4 props · parlays logging | 2 · 0 | 5 · 0 → 1 | combo shadow installed 11-26 |
| D4 engines | NFL, NBA, NHL engines; MLB none | MLB engine built and its 2027 board frozen | +1 sport |
| D5(a) / D5(b) applied | MLB 3/8 · NFL 14 applied | MLB 4/8 · NFL 18 / 26 · NBA 11 / 17 · NHL 8 / 12 | splits applied per leaf |
| **D6 wired end to end** | **0** (the measure did not exist; defined 11-11) | **18 / 129** | the window's main structural result |
| PAM | 100 hindsight deep-tier NBA records | + state tables + **469 point-in-time archetypes** | start of PAM proper, "not even 1/4" |
| P1 · P2 | 12 / 49 · 12 verdicts | 25 / 49 · 25+ routed | PROOF moved most |
| E (demo forward test) | MLB-only books, idle | three winter sports placing demo orders; props and combo order paths built | first execution numbers are small and understated |
| Open gaps | 250 | 185 | gap burner |
| Real capital · Kelly | $0 · 0 | $0 · 0 | guardrails held the whole window |

**By pillar:**
- **PROOF and DEPTH moved most.**
- **BREADTH moved steadily.**
- **EXECUTION barely moved** until the last two waves. That is the plainest judgment on the window's steering.

## 3. The arc, wave by wave (condensed)

- **101–104, memory and the restart:**
  - Box memory fought down (T1 / T2 shadow-line lock); the forward test restarted on a clean epoch (GG-1771).
  - Stray branches cut 35 → 3.
  - First PAM-to-engine work.
- **105–110, the doctrine:**
  - The operator's routing doctrine became ADR-0077 and the one-page DOCTRINE.md, with freshness checks (Hard Rule 16). D6 was defined.
  - The window caught itself scoring factors as "model vs market" four times (W48, W50, W52, W53) and rewrote the scoring.
  - Same-game correlation was priced (W110): the parlay machinery the pot-of-gold arm needs.
- **111–122, the tree reached orders:**
  - The router was wired to demo arm orders; ride and longshot cells were built.
  - The "daily breaker" that had silently starved the arm-order test for four days was found and removed (W57 / GG-1935).
  - Also: the weekly evidence look, NBA props splits (14 kept leaves of 143), NFL / NHL depth seats, the NHL event store.
  - The Muse queue scaled into the thousands of chunks.
- **123–126, the edge-location program:**
  - The window's main strategic finding: gross effects keep appearing and dying at one round cost on the most-watched lines (H1–H4,
    H-EDGE-5); closing-line value was licensed in 1 of 50 families (H-MEAS-1).
  - That turned the build toward retail flow (combos, props), depth and MLB.
  - Cost: three measurement-heavy waves before the turn. The operator had to say "align your backlog".
- **127–128, retail flow and the archive:**
  - Combos through Kalshi RFQ in demo (2 fills); H-EXEC-4 frozen; MLB engine counted.
  - H-DEPTH-PAM-3 SUPPORTED; NFL play-level 0 of 74 leaves earned (routed to ride / no bet).
  - Muse deleted its own archive with one push. The window restored it the same night (two-parent commit, 29,196 entries verified).
  - Muse's mechanical families moved to four free server scrapers.
- **129–130, depth into the live path, then execution:**
  - EXP-047-S SUPPORTED (4 of 4 stats on an unread season).
  - MLB 2027 frozen before its first row; PAM state tables, then 469 point-in-time archetypes.
  - NFL and NHL in-play feeds (the NFL one installed for Thanksgiving).
  - Props and combo demo-order paths, each under its own PREREG.
  - Every live writer probed; D6 one number; STATE_OF_THE_BOT.md generated from the box for the next window.

## 4. What went well

1. **The doctrine is written down and enforced.** DOCTRINE.md, ADR-0077 / 0078, HYPOTHESIS_DOCTRINE.md with a 73-row registry, the
   freshness check, and the words ("hypothesis closed, parked for R&D"). A new window cannot drift back to "beat the market" without
   tripping something.
2. **Pre-registration discipline held** through 30 waves: every test committed before its first row, judged at its n, nulls routed,
   not hidden. PROOF doubled.
3. **The edge-location program asked the question nobody had stated** (where does gross edge go?) and answered it with tests. It set
   the direction for the rest of the window.
4. **Recovery under pressure.** Muse's archive wipe was repaired the same night, with a method that worked around the proxy's 403 on
   API writes. Muse's emergency channel was found and used; the queue-floor fix landed while Muse was still reachable.
5. **Guardrails never moved.** $0 real, Kelly 0, installs only on named approval, no paid data, no Polymarket work.
6. **The handoff leaves instruments, not prose:** STATE_OF_THE_BOT.md, every live writer probed, D6 from the box.

## 5. What went wrong

The error log has **25 SW-9 entries** (W45–W69), the most of any window:
- UNVERIFIED 9
- PROCESS 7
- DOCTRINE 4
- REPEAT 2
- one each of PRESET, SCOPE and a misread

The ones that cost most:
1. **"All set" on Muse, repeatedly, before it was (W59–W62, W65, W66).**
   - The operator asked "are we set?" several times and got "yes" before the checks existed.
   - The cost was a near-lost Muse week, a jammed browser and late snapshots.
   - His words: "Bro this kinda shit pisses me the fuck off - how many times did I come back at you asking 'ARE WE SET?'"
   - The checklist, the alarms and verified / not-verified reporting came after, not before.
2. **The doctrine drift before the doctrine (W48–W53).** Scoring and framing kept sliding to "the model must beat the market" until
   the operator restated it twice. The fix (DOCTRINE.md) is good; it should not have needed his second statement.
3. **The operator making catches on things he had already said (W54, W55).** He said it plainly: the window exists so he is not the
   one making the strategic catches.
4. **Steering order.** Measurement waves ran before the build turn (123–125). The retail-parlay lane, his stated first step since
   10-16, reached orders only in W130. EXECUTION stayed the weakest pillar for the whole window.
5. **Late-window accuracy fell as context compressed.** W67 (a fixed router bug reported as live), W68 (his PAM-value point read as
   "drop PAM"), W69 (the sitrep's distance table not recomputed from Wave 110 to 130, and the closed prompts for 123–129 not archived;
   both repaired at the handoff). He said it: "You've been misreading a lot this window."

## 6. Verdict

- **Score: 6 / 10, same as the PDTP self-assessment at Wave 126.** The last four waves were the most productive of the window, and
  the late errors offset them.
- **Strategically,** the window left the project with:
  - the right doctrine, enforced;
  - an honest finding about where edge is not (the most-watched lines, gross of costs);
  - 18 cells wired end to end from zero;
  - the first order paths into the markets the doctrine names first: retail props and parlays.
- **What it did not do:** produce a single arm that clears zero after real costs. That is still the open question, and the answer
  starts arriving in SW-10, from fills rather than calibration.
- **Operationally,** it was too slow to verify before saying "done". That is the habit SW-10 should not inherit.

## 7. For SW-10, in one paragraph

Execution first. Get a complete fill join so E1 / E2 / E3 are real per book (B-136); read the props and combo demo orders as soon as
they run. Read H-EXEC-4 on 12-01. Build PAM archetypes into the props tree as splits, scored per leaf on net. Fix GG-2013 so the
state page tells the truth about installs. Before every Monday, run the whole Muse checklist and say what was and was not verified.
Recompute the distance table at every close. And when a message could mean two things, ask in one line before acting.
