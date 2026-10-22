# W83.1 — the bot captures what Muse scouted (results)

**Purpose (HR12):** DEPTH. Measure D5(b) NFL (2026 coverage/pressure/personnel splits aggregated weekly, point-in-time) and charter v3 §7 source-card accuracy.
Written 2026-10-22 UTC. Sources: box `exp_output/SOURCE_CAPTURE/` (read back 2026-10-22T00:05Z), the bot's own fetch of each page 2026-10-21.

## 1. Capture read-back (PR #311, merged; box deploy `deployed`, t4_mlb_verdict `not_needed`)
Cron `41 21 * * 2,3` (own marked block, flock, 2 MB/page and 5 MB/day caps), registered, installed after the budget gate went GREEN. Backfill run 2026-10-22T00:03:42Z wrote one snapshot per page, 32 team rows each:

| card | as_of (page's own dateModified) | rows |
|---|---|---|
| sharp-coverage-schemes | 2026-10-20T12:18:53-04:00 | 32 |
| sharp-defensive-tendencies | 2026-10-20T12:18:53-04:00 | 32 |
| sharp-defensive-line-stats | 2026-10-20T12:18:52-04:00 | 32 |
| sharp-offensive-line-stats | 2026-10-20T12:18:57-04:00 | 32 |
| sharp-offensive-personnel | 2026-10-20T14:45:33-04:00 | 32 |

Snapshots are written only when table content changes; `checks.jsonl` records every run (the staleness alarm is `max_age_h=200` on `logs/source_capture_cron.log`).
Not captured: **PFR advanced passing** — a plain GET returns a Cloudflare 403 from both the Mac and the box (GG-1000); and NGS (browser-only). Both stay browser one-offs.

## 2. Card accuracy (charter v3 §7)
Compared each card's sample rows against the bot's fetch of the same page (same as_of, 2026-10-20).

| card | matched | mismatched | not comparable |
|---|---|---|---|
| sharp-coverage-schemes | 5/5 | 0 | – |
| sharp-defensive-tendencies | 5/5 | 0 | – |
| sharp-defensive-line-stats | 4/4 | 0 | – |
| sharp-offensive-line-stats | 4/4 | 0 | – |
| sharp-offensive-personnel | 4/4 | 0 | – |
| pfr-advanced-passing | – | – | all (bot GET 403) |
| ngs-passing | – | – | all (browser-only) |

**Accuracy: 22/22 comparable rows = 100%** (5 of the 7 examined cards comparable; the other 6 of the 13 `sources/nfl/` cards were not examined). Caveat: a match shows the card transcribed the page, not that Sharp's numbers are right. The PFR card's CAPTURABLE verdict is wrong for the bot's fetch route — it should read browser-only.
**NGS definitional flag:** the primary excludes sacks from time to throw; the republisher's text omits that. This sits next to 82.3's FAILED-on-level grade (QB time to throw r=0.962, mean diff −0.161 s, bot lower, constant offset): a constant offset is what a definitional difference would produce, so the level failure is plausibly definitional, not noise. Not re-tested here.

## 3. Descriptive cross on captured 2026 values (no new verdict)
The 82.3 pre-registered test (frozen passyds_strike_v1 sha 1053c843…) needs 2026 QB-games with per-play coverage/pressure; nflverse has no 2026 participation file (GG-730) and the capture is team-level, one snapshot through Week 6. So the test **cannot run on 2026; no verdict**. Descriptive only:
- Sharp man rate, 2026 (32 teams): mean 18.5%, sd 7.7, range 5.0–41.7; top CLE 41.7, CHI 31.9, NE 31.2, CIN 28.0. Sharp blitz rate: mean 30.0%, sd 9.4; top MIN 66.5, TB 42.6, WAS 42.5.
- The 2025 nflverse man-share top three were DEN 44.6, PHI 43.6, CHI 41.7 (part_b_verdict). Sharp 2026 values for them: DEN 22.0, PHI 15.5, CHI 31.9. **Levels are not comparable across sources** (Sharp's man-rate mean is 18.5% against nflverse shares in the 40s at the top); only within-source ranks carry over, and with 3 teams and a changed season that says nothing.
- CLE sits in the far upper tail of Sharp man rate (41.7, ~3 sd above the mean). Man share was a TRAIT in 2018–2025 (split-half r 0.79; year-to-year 0.53), so a tail reading is persistent in principle — but the 2023–25 cross found no yardage slope (d_man −2.6 [−7.2, +1.5]), so the tail carries no price implication. Early-season sample (6 games) widens every figure.

## 4. Stage and granularity index (ADR-0075)
Coverage/pressure/blitz/box/personnel/line rates (Sharp, team level, 2026): **aggregated** (live weekly, point-in-time). Interpreted: not yet for 2026. Applied: no. Granularity index: team-level; no QB, route or personnel-grouping split; no per-play join; weekly; single source. D5(b) NFL moves 0 → live weekly capture of 5 cards.
