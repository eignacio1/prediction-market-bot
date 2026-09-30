"""
Logic-Epoch Register (T-320, Workstream A — Clean-logic provenance)
=====================================================================
Component:    Sport-agnostic; consumed by C5 (paper_trader.py::open_position())
Phase active: Phase 6 (paper trading)
Status:       NEW — 2026-07-10

Responsibility:
  Define a monotonic LOGIC_EPOCH integer that increments whenever a commit
  changes the approval/sizing/execution write path (risk.py, paper_trader.py,
  run_*_paper_trade.py, run_t2_mlb_sameday.py, run_t4_mlb_live.py, etc.) in a
  way that alters what a bet's stored edge/direction/size would have been.
  Every position opened via paper_trader.py::open_position() is stamped with
  the epoch active at write time and the commit SHA that established it, so
  a later analysis can report clean_n — bets resolved entirely under the
  current, correct logic — separately from raw_n.

Boundary selection (why GG-100 is NOT a boundary):
  The seed set proposed for this register was GG-077, GG-087, GG-100 (each
  closed a contaminating bug per TODO_NEXT.md's T-320 spec). Direct commit
  inspection (T-320, this session) found GG-100's fix (016357e) touches only
  scripts/run_t177_edge_monitor.py — an offline analysis/monitoring script —
  and never risk.py, paper_trader.py, run_mlb_paper_trade.py, or
  run_t4_mlb_live.py. No bet's approval/sizing/execution computation changed
  at that commit; GG-100 corrected how an already-written position was later
  *read* and re-cohorted for the Fisher edge-monotonicity test, not how it
  was written. Including it as a boundary would incorrectly demote a batch
  of genuinely-clean bets (opened between the GG-087 and GG-100 commits) out
  of clean_n. Operator decision 2026-07-10: exclude GG-100. See
  GOVERNANCE_GAP_LOG.md GG-100 ("RESOLVED-AS-ARTIFACT... a measurement bug,
  not a real signal-inversion in the model") and DECISION_LOG.md 2026-07-10.

  The two real write-path boundaries used below (GG-087, GG-077) both landed
  2026-07-05, ~12.5 hours apart, on the same day. This module treats their
  git commit author timestamp as the epoch boundary. That is a deliberate,
  documented approximation: the VPS auto-deploy pipeline (deploy.yml) pulls
  on push, typically within minutes, but no per-deploy timestamp log exists
  for these two specific commits to confirm exact VPS-live time. A handful
  of positions opened within that deploy-lag window (commit time to actual
  VPS pull) could be misclassified by up to a few minutes. Acceptable for
  paper-trading provenance; revisit if this register is ever used to gate
  live-capital decisions with tighter tolerance requirements.

  Global counter, per-band interpretation (GG-124, Window C, 2026-07-23):
  the underlying stamp (`logic_epoch` on each position) is still a single
  global monotonic counter — that part of T-320's design is unchanged, and
  paper_trader.py::open_position() still stamps every new bet with
  CURRENT_LOGIC_EPOCH regardless of which band it belongs to. What changed
  is the *measurement-layer interpretation* of that stamp: GG-124 found
  that gating clean_n on exact equality to CURRENT_LOGIC_EPOCH means any
  fix — even one that demonstrably touched only one band's write path —
  zeroes every band's clean_n simultaneously (five such resets landed in
  ~5 days, 2026-07-05 through 2026-07-19, producing a monitoring-coverage
  blackout). Each `LogicEpochBoundary` below now carries `bands_affected`,
  derived by direct `git show`/`git show --stat` inspection of the
  resolving commit's actual diff (not the prose description alone) —
  `clean_epoch_floor_for_band()` and `is_clean_for_band()` use it to give
  each band its own effective clean-epoch floor: the most recent boundary
  that *actually changed that band's write path*, per the ALL_CELLS
  sentinel for boundaries proven to touch every band (e.g. GG-077, which
  patched the shared paper_trader.py::open_position() unconditionally
  before any band-gate existed). A band whose write path a given fix never
  touched keeps accruing clean_n straight through that fix's global
  counter bump. This remains deliberately conservative in the same
  direction as before — a boundary's `bands_affected` must be positively
  verified from the diff, not assumed — it can still undercount but must
  never overcount. See GOVERNANCE_GAP_LOG.md GG-124 and
  ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md Window C (C2).

  Cell re-key (ADR-0054(b), 2026-09-03): `bands_affected` elements are now
  `(MarketType, band)` cell keys (or the `ALL_CELLS` sentinel), not bare
  band strings — T-509/ADR-0054(a) made MAIN's cell-aware measurement live
  in assert_ledger_invariants.py/run_band_monitor.py, and a boundary scoped
  only to a band string cannot express "this fix touched MLB's T1 cell but
  not some other market type's T1 cell" once more than one market type can
  share a band. `clean_epoch_floor_for_cell()`/`is_clean_for_cell()` are
  the new cell-aware entrypoints. `clean_epoch_floor_for_band()`/
  `is_clean_for_band()` are preserved with their original signatures for
  their five existing external callers (band-only, no market-type
  argument) — each now returns the most conservative (latest) floor across
  every cell that matches the given band string, so a caller with no cell
  information gets the safest available answer rather than an arbitrary
  one, consistent with this register's asymmetric-risk posture.

Deploy note:
  This module is a static, hand-maintained register, not something derived
  automatically each run. When a new commit changes the approval/sizing/
  execution write path, append a new LogicEpochBoundary here (epoch = prior
  epoch + 1) and log the change in DECISION_LOG.md per Hard Rule 7.

Bump-time safety check (T-388, GG-124):
  Before appending a new boundary, run `scripts/check_epoch_activation.py`
  (optionally with `--field`/`--artifact-glob` naming the production data
  field the new logic depends on, if any). It warns (does not block) when
  another boundary has landed within the trailing 7 days (GG-124: five
  boundaries landed in ~5 days, blacking out clean_n across all active MLB
  bands simultaneously), and, when a field/artifact is given, alerts if that
  field is not yet present/non-null in production (the exact epoch-7
  activation-failure mode GG-105/T-387 found: deploy != behavioral
  activation when a runner falls back silently on a missing field).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple

from prediction_market_bot.c5_execution.market_type_registry import MarketType

# ADR-0054(b): bands_affected re-keyed from bare band strings to
# (MarketType, band) cell keys. All twelve tracked boundaries below predate
# both NFL (T-474, 2026-08-21) and NHL (T-495, 2026-08-25) having any
# registered cell, and predate ADR-0062 entirely — no boundary here is
# scoped to a cell that did not exist at the time it was set. MLB and NBA
# are the only families in scope for any of these twelve. NBA_PLAYER_POINTS'
# sole-ever-registered cell (T4_IN_PLAY, bare band "T4") never overlaps any
# of the four band strings these boundaries actually gate on ("T1", "T2",
# "T3", "T4M-PROJ") at any point in the registry's history, and no other MLB
# family besides MLB_PLAYER_PROP_HITS was an implemented cell until T-504/
# GG-226 (2026-08-29) — long after every boundary below. So every
# band-specific (non-ALL_CELLS) boundary is narrowly and defensibly scoped
# to MLB_PLAYER_PROP_HITS alone; see each boundary's own comment for the
# per-entry justification. See DECISION_LOG.md for this session's entry.
CellKey = tuple[MarketType, str]

# Sentinel for LogicEpochBoundary.bands_affected: this boundary's resolving
# commit touched shared write-path code unconditionally (no band-gate/no
# cell-gate existed yet), so it must be treated as having touched every
# cell — known ones and any added later, in any market type. Verified
# per-boundary from the actual commit diff, not assumed from the resolving
# gap's prose description (GG-124; generalized band->cell per ADR-0054(b)).
ALL_CELLS = "*"


class LogicEpochBoundary(NamedTuple):
    epoch: int
    resolving_gap: str
    commit_sha: str
    commit_utc: datetime
    description: str
    # Cells whose write path this boundary's resolving commit actually
    # changed, per direct git-diff verification — {ALL_CELLS} for a
    # commit proven to touch shared/unconditional code (GG-124, Window C;
    # ADR-0054(b)). Elements are either (MarketType, band) cell keys or the
    # ALL_CELLS sentinel. A historical boundary is never scoped to a cell
    # that did not exist when it was set (see module-level note above) —
    # scope wider (toward ALL_CELLS) when a narrower cell scope cannot be
    # positively justified from the diff; the failure mode is asymmetric
    # (ADR-0054(b) sign-off): too-wide only costs sample. too-narrow
    # silently leaves dirty rows inside a cohort that reports itself clean.
    bands_affected: frozenset[CellKey | str] = frozenset({ALL_CELLS})


# Ordered chronologically (ascending commit_utc). epoch N is active for any
# timestamp >= this boundary's commit_utc and < the next boundary's
# commit_utc (or indefinitely, for the last entry).
_BOUNDARIES: tuple[LogicEpochBoundary, ...] = (
    LogicEpochBoundary(
        epoch=2,
        resolving_gap="GG-087",
        commit_sha="47ada94a81fee7be497d99952a17ded4c53a1fbb",
        # 2026-07-05 03:18:51 -07:00
        commit_utc=datetime(2026, 7, 5, 10, 18, 51, tzinfo=timezone.utc),
        description=(
            "T4 MLB live engine was structurally YES-only (discarding "
            "NO-side edge signal); fixed to bidirectional direction/sizing "
            "in run_t4_mlb_live.py."
        ),
        # git show --stat 47ada94a: run_t4_mlb_live.py only. run_t4_mlb_live.py
        # is MLB T4's only live engine; no other MLB family was an
        # implemented cell until T-504/GG-226 (2026-08-29), and NBA never
        # traded T4M-PROJ (NBA_PLAYER_POINTS' sole cell is bare-band "T4",
        # T4_IN_PLAY) — ADR-0054(b) scope: narrow to MLB_PLAYER_PROP_HITS.
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ")}),
    ),
    LogicEpochBoundary(
        epoch=3,
        resolving_gap="GG-077",
        commit_sha="0797c320f5158afdfa3e34b890c971970e9a5215",
        # 2026-07-05 15:45:38 -07:00
        commit_utc=datetime(2026, 7, 5, 22, 45, 38, tzinfo=timezone.utc),
        description=(
            "T1/T2/T3 MLB fee_net_edge sign-convention bug (production "
            "side): fee_net_edge was stored YES-frame-only and wrong-"
            "signed for NO bets, permitting false CHECK 3 approvals. "
            "Fixed in paper_trader.py::open_position() and "
            "run_mlb_paper_trade.py."
        ),
        # git show 0797c320: paper_trader.py::open_position() changed
        # unconditionally — no band-gate existed yet, so this touches every
        # band's write path (T1/T2/T3 via run_mlb_paper_trade.py, and
        # T4M-PROJ via the shared open_position() change). ADR-0054(b) named
        # this boundary explicitly as needing the all-cells marking: the
        # commit touched shared, unconditional open_position() code before
        # any cell-gate existed — every cell in every market type, known or
        # future, is in scope. No narrower justification is possible.
        bands_affected=frozenset({ALL_CELLS}),
    ),
    LogicEpochBoundary(
        epoch=4,
        resolving_gap="GG-113",
        commit_sha="91111b7d64ff6f9c26f64ab9152a0e16637b76a2",
        # 2026-07-14 18:56:45 -07:00
        commit_utc=datetime(2026, 7, 15, 1, 56, 45, tzinfo=timezone.utc),
        description=(
            "T4M-PROJ NO-direction vig sign flip (ADR-0043): GG-087's fix "
            "negated the whole gross_edge expression for NO bets, which "
            "already had vig subtracted with a fixed sign, converting vig "
            "from a cost into a credit for 81.8% of the resolved book. "
            "Fixed to a direction-independent symmetric cost in "
            "run_t4_mlb_live.py (fb13166) and paper_trader.py::"
            "open_position(), matching run_exp017.py's established "
            "convention. Boundary points to 91111b7, not the earlier "
            "2569c1f: 2569c1f's paper_trader.py change applied the "
            "corrected formula unconditionally (would have silently "
            "changed T1/T2 ledger values, out of this sign-off's scope) "
            "and was self-corrected pre-deploy, before ever running in "
            "production, to band-gate the fix to band == \"T4M-PROJ\" "
            "only (91111b7) — that band-gated commit is the first one "
            "whose code, if checked out alone, reflects the actual "
            "deployed-correct behavior. DS sign-off 2026-07-14 (operator) "
            "explicitly accepted this epoch reset as a deliberate cost of "
            "correcting a formula that was inflating edge on the majority "
            "of T4M-PROJ's book, over continuing to accumulate on the "
            "biased formula."
        ),
        # git show 91111b7d: explicit `band == "T4M-PROJ"` gate — MLB T4's
        # only live engine (run_t4_mlb_live.py); ADR-0054(b) scope: narrow
        # to MLB_PLAYER_PROP_HITS (see epoch-2 boundary's comment above for
        # the full NBA/other-MLB-family exclusion reasoning, unchanged here).
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ")}),
    ),
    LogicEpochBoundary(
        epoch=5,
        resolving_gap="GG-119",
        commit_sha="53a92089b8d424554e2074d848f6a6a639efe82e",
        # 2026-07-15 16:52:42 -07:00
        commit_utc=datetime(2026, 7, 15, 23, 52, 42, tzinfo=timezone.utc),
        description=(
            "T1 NO-direction vig sign flip (ADR-0045), the identical "
            "GG-113/ADR-0043 pattern found in T1's own gating file: "
            "run_mlb_paper_trade.py::_directional_edge()'s NO branch "
            "negated the whole half_spread-inclusive gross_edge, "
            "converting half_spread from a cost into a credit for all "
            "248 NO-direction resolved bets in the pre-fix book (74 of "
            "which only cleared MIN_EDGE_TO_APPROVE due to the "
            "inflation). Fixed to a direction-independent symmetric cost "
            "in run_mlb_paper_trade.py and paper_trader.py::"
            "open_position() (band gate extended from {\"T4M-PROJ\"} to "
            "include \"T1\", both landing in the same commit — unlike "
            "GG-113, no self-correction needed here since the write path "
            "and gating path were fixed together from the start). "
            "DS sign-off: Earl Ignacio (operator), authorizing the "
            "T1-scoped fix and explicitly accepting the resulting T1 "
            "clean_n reset despite T1's much larger n* (~2,322 vs "
            "T4M-PROJ's ~787) making this a proportionally larger ETA "
            "cost than ADR-0043 accepted. See ADR-0045, GG-119 "
            "(GOVERNANCE_GAP_LOG.md), DECISION_LOG.md 2026-07-15."
        ),
        # git show 53a92089: new `elif band == "T1":` branch added;
        # pre-existing `elif band == "T4M-PROJ":` branch unchanged. T1 was
        # only ever an MLB band at this date (no other family implemented);
        # ADR-0054(b) scope: narrow to MLB_PLAYER_PROP_HITS.
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T1")}),
    ),
    LogicEpochBoundary(
        epoch=6,
        resolving_gap="GG-123",
        commit_sha="cc887e88385ec793d849859da543deee50c1940c",
        # 2026-07-15 17:13:46 -07:00
        commit_utc=datetime(2026, 7, 16, 0, 13, 46, tzinfo=timezone.utc),
        description=(
            "T2 same-day gating cost-term magnitude bug (APR-0028 "
            "Proposed D1): run_t2_mlb_sameday.py subtracted the FULL "
            "vig (bid-ask spread) as its cost term instead of "
            "half_spread (vig / 2.0), the one-sided transaction cost "
            "convention established by run_exp017.py and T1's own "
            "formula. Unlike GG-113/GG-119, this is a magnitude-only "
            "bug, not a sign flip, and is conservative-direction "
            "(under-computes edge, causing missed bets rather than "
            "false approvals) — confirmed via a 39-candidate diagnostic "
            "sample (scripts/run_t368_gg122_t2_vig_magnitude_diag.py, "
            "filename retains original informal numbering) "
            "showing 1 PASS->YES flip at T2's own EDGE_YES gate and 0 "
            "additional bets clearing the binding MIN_EDGE_TO_APPROVE "
            "floor — zero realized bet-outcome changes in the observed "
            "sample. Fixed in run_t2_mlb_sameday.py only; "
            "paper_trader.py::open_position() needs no corresponding "
            "band-gate change since T2 has no NO-direction branch "
            "(PAPER_YES_ONLY defaults true) — the NO-branch sign-flip "
            "bug GG-113/GG-119 fixed does not apply to T2's YES-only "
            "gating path. DS sign-off: Earl Ignacio (operator), "
            "verbatim: 'Okay - yes proceed with the fix now, you have "
            "my authority.' D2 (this epoch bump) was initially deferred "
            "pending confirmation that the concurrent GG-119/ADR-0045 "
            "T1 branch's own epoch bump (epoch 5, above) did not "
            "already cover T2 — confirmed it does not (T1-scoped only), "
            "so this bump proceeds as its own boundary, per APR-0028's "
            "explicit 'coordinate once that branch merges' instruction. "
            "See APR-0028 (00_ADMIN/), GG-123 (GOVERNANCE_GAP_LOG.md), "
            "DECISION_LOG.md 2026-07-15. Renumbered from this task's "
            "original T-372/GG-122 self-assignment after a merge-time "
            "collision with a different, unrelated, already-merged "
            "concurrent session's own T-372/GG-122 claim; see "
            "GOVERNANCE_GAP_LOG.md GG-123's numbering note."
        ),
        # git show cc887e88: run_t2_mlb_sameday.py only; no corresponding
        # paper_trader.py band-gate change (T2 has no NO-direction branch).
        # run_t2_mlb_sameday.py is MLB-only; ADR-0054(b) scope: narrow to
        # MLB_PLAYER_PROP_HITS.
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T2")}),
    ),
    LogicEpochBoundary(
        epoch=7,
        resolving_gap="GG-105",
        commit_sha="f961fba63760f46b5b3878a8f89dac9d0a861afb",
        # NOT this commit's timestamp (2026-07-18 00:33:41 UTC) — see below.
        commit_utc=datetime(2026, 7, 18, 14, 0, 0, tzinfo=timezone.utc),
        description=(
            "T4M-PROJ ba_l10 empirical-Bayes shrinkage (ADR-0047, GG-105 "
            "remediation): p_hits_gte_threshold() now consumes ba_l10_shrunk "
            "= (h_sum + K*PRIOR)/(ab_sum + K), K=40, PRIOR=.2512, replacing "
            "raw ba_l10 whose small-denominator extremes drove the tercile "
            "anti-predictive pattern. Uniquely among tracked boundaries, "
            "commit_utc here is NOT the resolving commit's timestamp: "
            "run_t4_mlb_live.py falls back to raw ba_l10 whenever the "
            "pregame JSON lacks ba_l10_shrunk, and the 2026-07-17 pregame "
            "regeneration (22:15 UTC) predated the merge (00:33 UTC Jul 18) "
            "— so the entire Jul-17 game night ran behaviorally pre-fix "
            "(epoch 6) despite post-fix code being deployed and t4-mlb "
            "restarted (01:17 UTC). Verified directly: zero ba_l10_shrunk "
            "fields in pregame_mlb_20260717.json, and zero T4 evaluation "
            "cycles ran in the fallback window (last audit eval 00:34 UTC, "
            "pre-restart). The fix goes behaviorally live at the FIRST "
            "post-deploy pregame regeneration: 2026-07-18, PIPE-08-set "
            "PIPE-06pre time in [14:00, 22:15] UTC. commit_utc uses the "
            "earliest bound (14:00 UTC) deliberately: T4M-PROJ — the only "
            "band whose write path ADR-0047 changes — cannot open a bet "
            "before that regeneration (PIPE-08 schedules PIPE-06pre at "
            "max(14:00 UTC, T4_start-45min), so the regen always precedes "
            "the day's first T4 cycle), and T1/T2/T3 write paths are "
            "behaviorally unchanged by ADR-0047 (T1 surfacing is "
            "audit-only), so their classification anywhere inside "
            "[14:00, actual-regen] is immaterial. Same "
            "documented-approximation posture as the GG-087/GG-077 "
            "deploy-lag note above, with the ambiguity window analyzed to "
            "zero behavioral misclassification. Contingency: if the "
            "2026-07-18 regeneration verification (pregame_mlb_20260718 "
            ".json contains ba_l10_shrunk; audit_mlb_t4.jsonl logs "
            "distinct raw-vs-shrunk values) FAILS, this boundary is "
            "mis-anchored and must be corrected before any epoch-7 bets "
            "resolve. DS sign-off: Earl Ignacio (operator), 2026-07-18: "
            "'you have my full sign off for the epoch-7 recommendation "
            "ruling' — accepting the global clean_n reset (all four MLB "
            "bands re-zero, T4M-PROJ's n*~787 race restarts) as the cost "
            "of correcting the GG-105 anti-predictive input. See "
            "ADR-0047, GG-105/GG-124 (GOVERNANCE_GAP_LOG.md), "
            "DECISION_LOG.md 2026-07-18. Note (GG-124 Window C, 2026-07-23): "
            "the operator's sign-off above accepted a global 4-band reset "
            "under the then-current global-only clean_n interpretation; "
            "bands_affected below reflects the verified diff scope "
            "(T4M-PROJ only, per ADR-0047's own description) and is used "
            "retroactively by the measurement layer going forward — it "
            "does not retract or reinterpret the sign-off itself."
        ),
        # git show f961fba6: p_hits_gte_threshold() / run_t4_mlb_live.py —
        # T4M-PROJ is the only band whose write path ADR-0047 changes
        # (explicit in this boundary's own description above). MLB T4's
        # only live engine; ADR-0054(b) scope: narrow to MLB_PLAYER_PROP_HITS.
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ")}),
    ),
    LogicEpochBoundary(
        epoch=8,
        resolving_gap="GG-105",
        # Same resolving commit as epoch 7 — no logic changed at this
        # boundary; it corrects epoch 7's activation accounting after its
        # documented contingency FIRED.
        commit_sha="f961fba63760f46b5b3878a8f89dac9d0a861afb",
        # First cycle row with ba_l10 != ba_l10_shrunk in
        # t4_mlb_cycle_log.jsonl (verified directly on the VPS).
        commit_utc=datetime(2026, 7, 18, 18, 7, 19, tzinfo=timezone.utc),
        description=(
            "Epoch-7 activation-failure correction (contingency executed). "
            "The 2026-07-18 15:55 UTC pregame regeneration emitted "
            "ba_l10_shrunk: null for all 62 players — run_mlb_pregame.py "
            "sources the field from exp_output/MLB/mlb_feature_matrix.csv, "
            "and the VPS copy had last been regenerated by PIPE-05FX at "
            "22:35 UTC Jul-17, two hours BEFORE the ADR-0047 merge, so the "
            "column did not exist. run_t4_mlb_live.py's fallback therefore "
            "kept T4M-PROJ on raw ba_l10 (behaviorally epoch 6) through the "
            "Jul-18 afternoon slate while paper_trader stamped every bet "
            "epoch 7 — the exact mis-stamping epoch 7's contingency named. "
            "Remediation (operator-selected Option A, 2026-07-18): manual "
            "PIPE-05FX re-run (CSV regenerated with ba_l10_shrunk, 18:04 "
            "UTC), manual PIPE-06pre re-run (pregame_mlb_20260718.json "
            "repopulated with real values, exit 0), t4-mlb restart 18:06:52 "
            "UTC; first cycle row with DISTINCT raw-vs-shrunk values at "
            "2026-07-18T18:07:19Z — this boundary's commit_utc. All bets "
            "STAMPED epoch 7 are excluded from clean_n regardless of when "
            "they opened: the stamped-7 cohort irreversibly mixes pre-fix "
            "fallback bets (05:31-18:07 UTC Jul-18, ~200 orders, some "
            "resolved before this correction landed) with genuinely "
            "shrunk-behavioral bets (18:07 UTC Jul-18 through this bump's "
            "deploy), and stamps cannot distinguish them. Bets in that "
            "second group are timestamp-classified epoch 8 by "
            "epoch_for_timestamp() under this boundary; recovering them "
            "into clean_n would require a DS-authorized re-stamp backfill "
            "— deliberately NOT done here (operator declined mid-slate "
            "position-file surgery when selecting Option A). Clean accrual "
            "restarts at this bump's VPS deploy. Verification PASSED "
            "post-remediation: pregame_mlb_20260719.json zero nulls; "
            "t4_mlb_cycle_log.jsonl 3,004 shrunk-bearing rows, 2,835 "
            "distinct raw-vs-shrunk. See GG-105/GG-124 addenda and "
            "DECISION_LOG.md 2026-07-19."
        ),
        # Same resolving commit/gap as epoch 7 — T4M-PROJ only; ADR-0054(b)
        # scope: narrow to MLB_PLAYER_PROP_HITS (same reasoning as epoch 7).
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ")}),
    ),
    LogicEpochBoundary(
        epoch=9,
        resolving_gap="GG-135",
        commit_sha="6be807f650c3157d9a0f76ede2aa30943e58ea40",
        # author date 2026-07-29 17:04:04 -07:00 (unchanged across two rebases
        # onto origin/main's concurrent G1/G2/G4 sessions; only the SHA/
        # committer date changed each time — 3cb04ca -> c0156a9 -> 6be807f)
        commit_utc=datetime(2026, 7, 30, 0, 4, 4, tzinfo=timezone.utc),
        description=(
            "ADR-0048 (edge-conditional, variance-aware sizing) applied: "
            "kelly_fraction zeroed for T1_MULTI_DAY, T2_SAME_DAY, "
            "T3_PRE_TIP, and T4M_PROJ. GG-135's MC bootstrap found MAIN's "
            "real variance alone (independent of edge sign) produces "
            "~100%/yr probability of tripping the 20% max-drawdown kill "
            "switch at any positive Kelly; this halts that self-"
            "termination for T1/T2/T3. T4M-PROJ is additionally zeroed "
            "pending GG-105 anti-predictive-edge remediation and GG-142's "
            "abs()-gate defect fix, gated on ADR-0048's reactivation "
            "lookup table. Two write paths required correction in the "
            "same commit: execution_bands.py's BAND_CONFIGS entries "
            "(consumed live by T1/T2/T3 via get_band_config(...)."
            "kelly_fraction) and run_t4_mlb_live.py's separate module-"
            "level KELLY_T4 constant (T4M-PROJ stakes from this directly "
            "— that file never imports execution_bands.py, so editing "
            "only the BAND_CONFIGS entry would have left T4M-PROJ's real "
            "sizing unchanged at 0.10). Evaluations continue to log for "
            "research (risk.py's kelly_size_zero rejection path preserves "
            "full forecast context); only sizing goes to zero. DS "
            "sign-off: operator, 2026-07-29. See ADR-0048, GG-135, T-398, "
            "DECISION_LOG.md 2026-07-29."
        ),
        # git show 6be807f: execution_bands.py (T1_MULTI_DAY, T2_SAME_DAY,
        # T3_PRE_TIP, T4M_PROJ kelly_fraction fields) + run_t4_mlb_live.py
        # (KELLY_T4 constant) — all four named bands' write paths changed,
        # all four MLB-only at this date; ADR-0054(b) scope: narrow each to
        # MLB_PLAYER_PROP_HITS (four cells, not ALL_CELLS — execution_bands.py
        # is keyed per band, not unconditional shared code).
        bands_affected=frozenset({
            (MarketType.MLB_PLAYER_PROP_HITS, "T1"),
            (MarketType.MLB_PLAYER_PROP_HITS, "T2"),
            (MarketType.MLB_PLAYER_PROP_HITS, "T3"),
            (MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ"),
        }),
    ),
    LogicEpochBoundary(
        epoch=10,
        resolving_gap="GG-142",
        commit_sha="1b0a8f83d2d4b6294913b4f0864d04f41209d4bb",
        # author date 2026-07-29 22:43:12 -07:00 (git show -s --format=%aI)
        commit_utc=datetime(2026, 7, 30, 5, 43, 12, tzinfo=timezone.utc),
        description=(
            "C4 CHECK 3 edge-gate sign defect (ADR-0049): risk.py gated on "
            "abs(edge) < MIN_EDGE_TO_APPROVE, but edge is already "
            "direction-resolved by every producer — a negative value means "
            "a confidently-wrong bet (vig/fee cost exceeds signal in the "
            "recommended direction), not a smaller-but-valid one. abs() "
            "rescued 239/239 (46.1%) of T4 epoch-8 evaluations with "
            "vig > |model_p - mid| into approval. Fixed to a signed check "
            "(edge < MIN_EDGE_TO_APPROVE), plus a new CHECK 4b validating "
            "recommended_direction against gross_edge's sign when present "
            "on the record. risk.py::evaluate_forecast() is shared, "
            "unconditional code called identically by every band (no "
            "band-gate around CHECK 3/4b), matching the ALL_CELLS "
            "precedent set by GG-077's boundary. Correctness fix only — "
            "ADR-0048's kelly_fraction=0 for T1/T2/T3/T4M-PROJ is "
            "unchanged; no sizing goes live at this boundary. DS sign-off: "
            "operator, 2026-07-29 (Strategic Analysis §A/§E/§H). See "
            "ADR-0049, GG-142, DECISION_LOG.md 2026-07-29."
        ),
        # git show 1b0a8f83: risk.py::evaluate_forecast() CHECK 3/CHECK 4b —
        # shared, unconditional across every band; no band-gate exists.
        # ADR-0054(b): matches the GG-077/epoch-3 all-cells precedent —
        # shared, unconditional code with no cell-gate is in scope for
        # every cell in every market type, known or future.
        bands_affected=frozenset({ALL_CELLS}),
    ),
    LogicEpochBoundary(
        epoch=11,
        resolving_gap="GG-046",
        commit_sha="cafcf742ad2a5fd41c666a80c9d32b489b514b97",
        commit_utc=datetime(2026, 7, 31, 6, 36, 44, tzinfo=timezone.utc),
        description=(
            "ADR-0050: T4M-PROJ reactivated at a flat $1.00 measurement "
            "stake, replacing the GG-087 '1 contract at market price' "
            "policy. risk.py::evaluate_forecast() gains an optional "
            "fixed_stake_usd param that bypasses Kelly sizing (and its "
            "kelly_size_zero rejection, which previously made "
            "KELLY_T4=0.0 unconditionally reject every T4 bet before "
            "reaching APPROVED) with a flat dollar amount; all other "
            "gate checks (signed edge threshold, direction consistency, "
            "kill switches, single-event cap, min-bet floor, aggregate "
            "deployment) still apply unchanged. run_t4_mlb_live.py passes "
            "T4_MEASUREMENT_STAKE_USD=1.00 as fixed_stake_usd on its "
            "evaluate_forecast() call; KELLY_T4 stays 0.0, so the "
            "Kelly-proportional path is untouched and never engages. "
            "Edge is unvalidated (GG-105 open) — this stake's only job "
            "is to accrue a clean, gate-fixed T4M-PROJ cohort at a size "
            "far inside GG-045 orderbook depth. MAIN (T1/T2/T3) sizing "
            "is unchanged. DS sign-off: operator, 2026-07-30. See "
            "ADR-0050, GG-046, DECISION_LOG.md 2026-07-30. "
            "GG-148 (2026-07-31): commit_sha corrected from the original "
            "R3 commit (b7ff281) to cafcf74 — b7ff281's own "
            "StagedOrderStore.stage_order() unconditionally rejected "
            "every kelly_fraction=0.0 call (GG-147), so zero T4M-PROJ "
            "positions could ever have been recorded under that commit; "
            "cafcf74 is the first commit under which epoch 11 can "
            "actually produce data, and is also where the addendum's "
            "contract cap (§B) first exists, itself a sizing-path change "
            "this epoch's own convention would otherwise require a new "
            "boundary for — folded into epoch 11 in place rather than "
            "bumped to 12 specifically because the prior commit_sha "
            "produced no real rows to protect from contamination."
        ),
        # git show cafcf74: staged_order_store.py (0.0 <= kelly_fraction
        # bound fix, GG-147) + run_t4_mlb_live.py (contract cap via
        # measurement_stake_and_stratum(), entry_price_paid/price_stratum
        # stamping) + paper_trader.py (field passthrough). Supersedes the
        # b7ff281 commit_sha this boundary originally recorded — see the
        # GG-148 note in the description above. MLB T4's only live engine;
        # ADR-0054(b) scope: narrow to MLB_PLAYER_PROP_HITS.
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ")}),
    ),
    LogicEpochBoundary(
        epoch=12,
        resolving_gap="GG-149",
        commit_sha="66bb0d3c6fff57b2dd75ffc2241ece102fac78f5",
        commit_utc=datetime(2026, 7, 31, 8, 0, 0, tzinfo=timezone.utc),
        description=(
            "GG-149: T4 offsetting-position suppression. 161 T4M-PROJ "
            "tickers were found holding simultaneous open YES and NO "
            "positions (a wash trade under Kalshi's CFTC-DCM rulebook, no "
            "manipulative intent — the model re-evaluated and took the "
            "other side without closing the first); 141 closed locked "
            "pairs / 374 legs, combined -$0.13 on $178.76 stake, plus 35 "
            "tickers with opposite directions across the T1/T4 books. "
            "Diagnosed the existing per-ticker re-entry guard "
            "(already_fired_game, T-208/T-225) as NOT applicable: it is "
            "keyed on ticker but blocks on (h_so_far, ab_remaining) "
            "state-equality with no direction field, and merges "
            "open+closed positions — an opposite-direction bet at a "
            "changed live state sails through by design. This is a "
            "genuinely new control, not a repair. Implemented: (1) "
            "intra-book (T4 vs T4) — before staging any order, check for "
            "an OPEN position on the same kalshi_ticker with the opposite "
            "direction; if found, SKIP (never close-and-reverse, which is "
            "a separate ADR-0018-governed decision, out of scope). Logs "
            "t4_offsetting_suppressed with both edges. (2) cross-book (T1 "
            "vs T4) — read-only, best-effort check of T1's portfolio file; "
            "ADR-0023 pool isolation means this is alarm-only "
            "(t4_t1_cross_book_direction_conflict, WARNING), never "
            "blocking — no cross-process coordination mechanism exists or "
            "should be improvised here. ADR-0050 pre-registration amended "
            "(append, Hard Rule 3): locked pairs (same-ticker, "
            "opposite-direction, overlapping open intervals) are EXCLUDED "
            "from the measurement cohort, both legs, retroactive + "
            "prospective; suppression-event count is itself a reported "
            "metric. 161 historical locked-pair tickers (425 legs) tagged "
            "via scripts/tag_locked_pairs_t4_mlb.py — filter-based "
            "exclusion only, no P&L altered. Bands affected: T4M-PROJ "
            "only (MAIN untouched). DS sign-off: operator, 2026-07-31. "
            "See GG-149, GG-150 (cross-book blocking variant, registered "
            "unstaffed), DECISION_LOG.md 2026-07-31. commit_sha corrected "
            "post-rebase from the original 01aaade (a pre-rebase SHA that "
            "no longer resolves to any object after this branch was "
            "rebased onto origin/main to resolve a non-fast-forward push) "
            "to 66bb0d3, the functional implementation commit — same "
            "defect class GG-148 fixed for epoch 11, caught here before "
            "merge rather than after."
        ),
        # git show 66bb0d3: run_t4_mlb_live.py (_find_open_position_
        # opposite_direction, _t1_open_position_opposite_direction, two new
        # checks in _run_cycle) + 8 new unit tests + retroactive tagger.
        # MLB T4's only live engine, and the description above states
        # "Bands affected: T4M-PROJ only (MAIN untouched)" explicitly;
        # ADR-0054(b) scope: narrow to MLB_PLAYER_PROP_HITS.
        bands_affected=frozenset({(MarketType.MLB_PLAYER_PROP_HITS, "T4M-PROJ")}),
    ),
)

# epoch 1 = everything before the earliest tracked boundary (pre-history;
# may contain untracked contaminating bugs from before this register
# existed — not claimed to be "clean", just the floor of what is tracked).
CURRENT_LOGIC_EPOCH: int = _BOUNDARIES[-1].epoch if _BOUNDARIES else 1
CURRENT_APPROVAL_COMMIT: str = _BOUNDARIES[-1].commit_sha if _BOUNDARIES else ""


def epoch_for_timestamp(ts: datetime) -> int:
    """Return the logic_epoch active at the given timestamp (naive == UTC)."""
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    epoch = 1
    for boundary in _BOUNDARIES:
        if ts >= boundary.commit_utc:
            epoch = boundary.epoch
        else:
            break
    return epoch


def approval_commit_for_epoch(epoch: int) -> str:
    """Resolving commit SHA that established `epoch`, or '' for epoch 1 (pre-history, untracked)."""
    for boundary in _BOUNDARIES:
        if boundary.epoch == epoch:
            return boundary.commit_sha
    return ""


def get_boundaries() -> tuple[LogicEpochBoundary, ...]:
    """Public read accessor for `_BOUNDARIES` (T-388, scripts/check_epoch_activation.py)."""
    return _BOUNDARIES


def clean_epoch_floor_for_cell(market_type: MarketType, band: str) -> int:
    """Most recent tracked boundary whose resolving commit actually touched
    the `(market_type, band)` cell's write path (ADR-0054(b), 2026-09-03,
    generalizing GG-124's per-band floor to per-cell). A boundary counts if
    `(market_type, band)` is in its `bands_affected`, or if that set
    contains `ALL_CELLS` (a commit proven to touch shared/unconditional
    write-path code). Falls back to 1 (pre-history floor) if no tracked
    boundary ever touched this cell.
    """
    floor = 1
    for boundary in _BOUNDARIES:
        if ALL_CELLS in boundary.bands_affected or (market_type, band) in boundary.bands_affected:
            floor = boundary.epoch
    return floor


def is_clean_for_cell(stamped_epoch: int | None, market_type: MarketType, band: str) -> bool:
    """True iff a position's stamped `logic_epoch` reflects fully-correct,
    currently-deployed write-path logic for the `(market_type, band)` cell
    specifically — i.e. it is at or past that cell's own clean-epoch floor,
    not necessarily `CURRENT_LOGIC_EPOCH` globally (ADR-0054(b)).
    """
    if stamped_epoch is None:
        return False
    return stamped_epoch >= clean_epoch_floor_for_cell(market_type, band)


def clean_epoch_floor_for_band(band: str) -> int:
    """Most recent tracked boundary whose resolving commit actually touched
    `band`'s write path in ANY market type (GG-124, Window C, 2026-07-23;
    re-scoped conservatively for cell-keyed `bands_affected` by ADR-0054(b),
    2026-09-03). Preserved for this function's five existing external
    callers, all of which have no market-type information to give — a
    boundary counts if `band` matches the band half of any `(MarketType,
    band)` cell key in its `bands_affected`, or if that set contains
    `ALL_CELLS` (a commit proven to touch shared/unconditional write-path
    code). This is deliberately the WIDEST floor across every cell sharing
    `band`, never the narrowest: a caller with no cell context must get the
    conservative answer, per this register's asymmetric-risk posture (a
    too-wide floor only costs sample; a too-narrow one risks passing a
    dirty row as clean). For a cell-aware caller, prefer
    `clean_epoch_floor_for_cell()` instead. Falls back to 1 (pre-history
    floor) if no tracked boundary ever touched this band in any cell.
    """
    floor = 1
    for boundary in _BOUNDARIES:
        touches_band = ALL_CELLS in boundary.bands_affected or any(
            isinstance(key, tuple) and key[1] == band for key in boundary.bands_affected
        )
        if touches_band:
            floor = boundary.epoch
    return floor


def is_clean_for_band(stamped_epoch: int | None, band: str) -> bool:
    """True iff a position's stamped `logic_epoch` reflects fully-correct,
    currently-deployed write-path logic for `band` specifically, in ANY
    market type — i.e. it is at or past `band`'s own (conservative,
    cell-agnostic) clean-epoch floor, not necessarily `CURRENT_LOGIC_EPOCH`
    globally (GG-124 remediation; re-scoped by ADR-0054(b)). For a
    cell-aware caller, prefer `is_clean_for_cell()` instead.
    """
    if stamped_epoch is None:
        return False
    return stamped_epoch >= clean_epoch_floor_for_band(band)


# ---------------------------------------------------------------------------
# Evidence class (T-588 / GG-317). ADDITIVE and UNWIRED: nothing in the repo
# counts with `is_countable_evidence()` yet. Which counters adopt it is an
# operator decision. `is_clean_for_band()` above is unchanged.
# ---------------------------------------------------------------------------

EVIDENCE_MODEL = "MODEL_EVIDENCE"
EVIDENCE_STUB = "STUB"
EVIDENCE_UNATTRIBUTED = "UNATTRIBUTED"

# `model_identity` prefixes registered as real, non-stub forecasters. An
# identity that is not on this list is NOT assumed real: it is classified
# UNATTRIBUTED (fail closed). Add an entry only with a citable source.
REGISTERED_MODEL_IDENTITY_PREFIXES: tuple[str, ...] = (
    "EXP-027 LR",  # nfl_exp027_adapter.PROVENANCE (T-531, HYP-012)
    # T4M-PROJ, FORWARD rows only (T-595 D2, Wave 41). Source: run_t4_mlb_live.T4M_PROJ_MODEL_IDENTITY,
    # stamped only when ba_l10_shrunk actually fed p_hits_gte_threshold (ADR-0047 / APR-0025); the
    # raw-fallback label T4M_PROJ_MODEL_IDENTITY_RAW_FALLBACK is deliberately NOT registered. This
    # entry does NOT attribute any historical row: those carry "UNKNOWN"/no identity and stay
    # UNATTRIBUTED. The inert T-592 provenance allowlist is a separate mechanism and is not applied.
    "T4M-PROJ Binomial (ba_l10_shrunk, ADR-0047)",
)


def evidence_class(row: object) -> str:
    """Classify a pool row by its already-stamped `model_identity` only.

    STUB: identity names a stub. UNATTRIBUTED: identity absent, empty,
    non-string, the literal "UNKNOWN", or not on the registered-model list.
    MODEL_EVIDENCE: identity starts with a registered real-model prefix.
    Reads no other field and repairs nothing (GG-228).
    """
    if not isinstance(row, dict):
        return EVIDENCE_UNATTRIBUTED
    identity = row.get("model_identity")
    if not isinstance(identity, str) or not identity.strip():
        return EVIDENCE_UNATTRIBUTED
    text = identity.strip()
    if text.upper() == "UNKNOWN":
        return EVIDENCE_UNATTRIBUTED
    if "STUB" in text.upper():
        return EVIDENCE_STUB
    if text.startswith(REGISTERED_MODEL_IDENTITY_PREFIXES):
        return EVIDENCE_MODEL
    return EVIDENCE_UNATTRIBUTED


def is_countable_evidence(row: object, band: str) -> bool:
    """True iff `row` is epoch-clean for `band` AND MODEL_EVIDENCE.

    Fails closed: any non-dict row, missing/non-int epoch, pre-floor epoch,
    STUB, or UNATTRIBUTED row returns False. UNTAGGED additionally requires
    `CURRENT_LOGIC_EPOCH`, mirroring `run_band_monitor.filter_clean`.
    """
    if not isinstance(row, dict):
        return False
    epoch = row.get("logic_epoch")
    if isinstance(epoch, bool) or not isinstance(epoch, int):
        return False
    if band == "UNTAGGED":
        if epoch != CURRENT_LOGIC_EPOCH:
            return False
    elif not is_clean_for_band(epoch, band):
        return False
    return evidence_class(row) == EVIDENCE_MODEL
