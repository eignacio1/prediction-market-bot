# ADR-0072 Addendum — applying the NFL ADOPT word (2026-11-05)

**Status: PROPOSED.** Written by terminal W102.2. A terminal may not accept this; only the operator can.
Premise note: the block that asked for this calls ADR-0072 a DRAFT; its header reads ACCEPTED (2026-10-10), with the 10-14, 10-15, 10-20, 10-21 and 10-22 addenda. This addendum treats it as ACCEPTED.

## Verdict and numbers (source: `12_EXPLORATORY/forward_test_nfl_final/results_W101_2.md`, report of 2026-11-04T11:25Z)
shadow/NFL, post-top-up, 41 games: **ADOPT** — (a), (b), (c) all hold at judged n (>= 550 per arm).
- (a) settle-minus-price, treatment minus control: **+0.190**, one-sided 95% game-clustered lower bound **+0.088** (> 0); upper 95% +0.291, so REJECT (< +0.05) does not fire.
- (b) fill rate 18.9% vs 50.3%, ratio **0.376** (>= 0.25).
- (c) 30-minute markout, treatment minus control: **-0.0117**, 95% interval [-0.0334, +0.0101]; upper bound >= 0, so "not credibly worse".
- First ADOPT line 2026-11-02T11:25Z; unchanged 11-03 and 11-04. NBA and NHL: (a) holds, (b) fails (0.203, 0.222): not adopted.
- This is an **execution-rule** verdict about shadow demo orders. It is not a cell verdict and moves no PROOF count (P2).

## What would change if accepted (nothing changes until the operator also flips the switch)
- Code (built, **OFF**, PR #424): `DEMO_FILL_ADOPT_BOOK_SPORT`, unset by default. Listing `shadow:NFL` makes every NFL shadow order place treatment-style (post at the book, cancel at the configured 60 s). Orders the forward-test hash already assigns to treatment keep `arm=treatment`; the rest are labelled `arm=adopt`, so no pre-registered arm label is rewritten and the report ignores `adopt` rows.
- Flip = one line in `deploy/demo_fill.override.env` (read last), reversible by deleting it.

## What would not change
MLB paper book, NBA and NHL shadow arms, `deploy/demo_fill.env`, the seed and share, every pre-registered parameter, every verdict word, `kelly_fraction` (0), real capital (none). No order placement changes while the switch is OFF (tested byte-for-byte).

## W98.2's caution, in one line
The gain comes from *which orders fill after waiting 60 s*, not from a measured edge in the posting rule, and (c) is a "not credibly worse" test whose interval allows a markout up to 3.3 cents worse.

## Open questions (the documents are silent; not answered here)
1. **NFL control arm after adoption.** With adoption ON, NFL has no model-mid control. Does the forward test stop for NFL (word is final), or keep a held-out control share so ADOPT can be re-checked?
2. **Which day was the look (GG-1750).** The 10-21 addendum says the look is taken once; the report recomputes daily. The word was ADOPT on 11-02, 11-03, 11-04. Options: pin 2026-11-02T11:25Z (first daily report after the 550th treatment markout fill), or pin 2026-11-04 (latest). The terminal has not pinned either.
3. **Scope.** Shadow book only, or also any future NFL paper cell? (As written: shadow only.)
4. **NBA/NHL.** Their (b) fails; does any later change to (b) reopen them, or are they final under the 10-20 addendum?
5. **Season end.** NFL games end in January; is adoption a standing rule or a one-season experiment with a stated review date?

## Blockquote-ready sentence for the operator
> I accept the NFL ADOPT word as an execution rule for NFL shadow demo orders only: place them treatment-style (post at the book, cancel at 60 s), as an experiment and not as proof of edge, with NBA and NHL unchanged.

Accepting the sentence authorises flipping the switch; it does not by itself flip it.
