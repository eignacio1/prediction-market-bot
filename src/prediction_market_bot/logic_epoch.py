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
  that *actually changed that band's write path*, per the ALL_BANDS
  sentinel for boundaries proven to touch every band (e.g. GG-077, which
  patched the shared paper_trader.py::open_position() unconditionally
  before any band-gate existed). A band whose write path a given fix never
  touched keeps accruing clean_n straight through that fix's global
  counter bump. This remains deliberately conservative in the same
  direction as before — a boundary's `bands_affected` must be positively
  verified from the diff, not assumed — it can still undercount but must
  never overcount. See GOVERNANCE_GAP_LOG.md GG-124 and
  ITERATION_PLAN_MC_REMEDIATION_2026-07-22.md Window C (C2).

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


# Sentinel for LogicEpochBoundary.bands_affected: this boundary's resolving
# commit touched shared write-path code unconditionally (no band-gate existed
# yet), so it must be treated as having touched every band — known ones and
# any added later. Verified per-boundary from the actual commit diff, not
# assumed from the resolving gap's prose description (GG-124).
ALL_BANDS = "*"


class LogicEpochBoundary(NamedTuple):
    epoch: int
    resolving_gap: str
    commit_sha: str
    commit_utc: datetime
    description: str
    # Bands whose write path this boundary's resolving commit actually
    # changed, per direct git-diff verification — {ALL_BANDS} for a
    # commit proven to touch shared/unconditional code (GG-124, Window C).
    bands_affected: frozenset[str] = frozenset({ALL_BANDS})


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
        # git show --stat 47ada94a: run_t4_mlb_live.py only.
        bands_affected=frozenset({"T4M-PROJ"}),
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
        # T4M-PROJ via the shared open_position() change).
        bands_affected=frozenset({ALL_BANDS}),
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
        # git show 91111b7d: explicit `band == "T4M-PROJ"` gate.
        bands_affected=frozenset({"T4M-PROJ"}),
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
        # pre-existing `elif band == "T4M-PROJ":` branch unchanged.
        bands_affected=frozenset({"T1"}),
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
        bands_affected=frozenset({"T2"}),
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
        # (explicit in this boundary's own description above).
        bands_affected=frozenset({"T4M-PROJ"}),
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
        # Same resolving commit/gap as epoch 7 — T4M-PROJ only.
        bands_affected=frozenset({"T4M-PROJ"}),
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
        # (KELLY_T4 constant) — all four named bands' write paths changed.
        bands_affected=frozenset({"T1", "T2", "T3", "T4M-PROJ"}),
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
            "band-gate around CHECK 3/4b), matching the ALL_BANDS "
            "precedent set by GG-077's boundary. Correctness fix only — "
            "ADR-0048's kelly_fraction=0 for T1/T2/T3/T4M-PROJ is "
            "unchanged; no sizing goes live at this boundary. DS sign-off: "
            "operator, 2026-07-29 (Strategic Analysis §A/§E/§H). See "
            "ADR-0049, GG-142, DECISION_LOG.md 2026-07-29."
        ),
        # git show 1b0a8f83: risk.py::evaluate_forecast() CHECK 3/CHECK 4b —
        # shared, unconditional across every band; no band-gate exists.
        bands_affected=frozenset({ALL_BANDS}),
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


def clean_epoch_floor_for_band(band: str) -> int:
    """Most recent tracked boundary whose resolving commit actually touched
    `band`'s write path (GG-124, Window C, 2026-07-23) — the per-band
    replacement for comparing a stamped `logic_epoch` against the single
    global `CURRENT_LOGIC_EPOCH`. A boundary counts if `band` is in its
    `bands_affected`, or if that set contains `ALL_BANDS` (a commit proven
    to touch shared/unconditional write-path code). Falls back to 1
    (pre-history floor) if no tracked boundary ever touched this band.
    """
    floor = 1
    for boundary in _BOUNDARIES:
        if ALL_BANDS in boundary.bands_affected or band in boundary.bands_affected:
            floor = boundary.epoch
    return floor


def is_clean_for_band(stamped_epoch: int | None, band: str) -> bool:
    """True iff a position's stamped `logic_epoch` reflects fully-correct,
    currently-deployed write-path logic for `band` specifically — i.e. it
    is at or past `band`'s own clean-epoch floor, not necessarily
    `CURRENT_LOGIC_EPOCH` globally (GG-124 remediation).
    """
    if stamped_epoch is None:
        return False
    return stamped_epoch >= clean_epoch_floor_for_band(band)
