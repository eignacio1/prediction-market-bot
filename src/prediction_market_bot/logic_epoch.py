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

  Global counter, not per-band (per T-320 spec): GG-087 only ever affected
  T4M-PROJ's write path and GG-077 only ever affected T1/T2/T3's, but a
  single global epoch counter increments on either fix regardless of which
  band it touched. This is deliberately conservative — it can undercount
  clean_n for a band a given fix never actually touched, but it will never
  overcount. A per-band register was judged unnecessary added complexity
  for what T-320 asked for; revisit only if per-band precision becomes load-
  bearing for a gate decision.

Deploy note:
  This module is a static, hand-maintained register, not something derived
  automatically each run. When a new commit changes the approval/sizing/
  execution write path, append a new LogicEpochBoundary here (epoch = prior
  epoch + 1) and log the change in DECISION_LOG.md per Hard Rule 7.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple


class LogicEpochBoundary(NamedTuple):
    epoch: int
    resolving_gap: str
    commit_sha: str
    commit_utc: datetime
    description: str


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
