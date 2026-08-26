"""
GG-038 / T-489 — MLB T4 band-level kill-switch halt-latency measurement.

Scope: MEASUREMENT ONLY. Does not touch risk.py, execution_bands.py, or any
threshold/kelly_fraction. See GOVERNANCE_GAP_LOG.md GG-038 (2026-08-26
measurement sub-section) for the write-up this file supports.

Real, verified check topology in src/prediction_market_bot/run_t4_mlb_live.py
(source line refs as of this session; re-verify if the file has since moved):

  - `kill_switch_armed(path) -> path.exists()`                       (~line 296)
  - `KILL_SWITCH_PATH = _LOGS_DIR / "t4_mlb_kill_switch.flag"`        (line 242)
  - `POLL_INTERVAL_S = 45`                                            (line 151)
  - top-of-outer-loop check, `while True:`                            (~line 1719)
  - per-game check inside the ESPN-poll `for gid in game_ids:` loop   (~line 1815)
  - NO check anywhere inside `_run_cycle()` (lines 997-1457; grepped, zero hits)
  - `time.sleep(POLL_INTERVAL_S)` after `_run_cycle()` returns runs
    UNCONDITIONALLY, with no re-check before/during it                (~line 1894)

The very next check after that sleep is the top-of-loop check. So the
worst-case detection window for "flag touched right after a check just
passed" is: (remaining per-game polls) + `_run_cycle()` duration + the full
45s sleep + negligible top-of-loop overhead.

Empirical cross-check (real production data, not simulated): pulled live from
the VPS on 2026-08-26 via
    ssh prediction-market-vps
    tail -400 /opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl
grouped by cycle_id (48 real cycles, MLB in-season):
    within-cycle span (s):        min 0.007478  p50 0.032449  p90 3.683535  max 7.132238
    cycle-start-to-cycle-start (s): min 51.471619 p50 66.955196 p90 74.670213 max 81.187241
This harness's simulated structural distribution is cross-checked against
those real numbers below (test_worst_case_matches_empirical_vps_data).
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_ENV", "paper")  # run_t4_mlb_live.py requires this at import time

import random
import time
from pathlib import Path

import pytest

from prediction_market_bot.run_t4_mlb_live import (
    KILL_SWITCH_PATH as _REAL_KILL_SWITCH_PATH,  # noqa: F401  (imported to prove it exists)
    POLL_INTERVAL_S,
    kill_switch_armed,
)

# Empirical _run_cycle() duration samples pulled from the real VPS
# t4_mlb_cycle_log.jsonl on 2026-08-26 (48 cycles). Used to parameterize the
# mocked cycle duration realistically rather than a fabricated constant.
EMPIRICAL_CYCLE_DURATIONS_S = [0.007478, 0.032449, 3.683535, 7.132238]

N_TRIALS = 200


def _simulate_one_trial(flag_path: Path, touch_at_fraction: float) -> float:
    """
    Simulate one pass of the real outer-loop shape and return detection
    latency in *simulated* seconds. `touch_at_fraction` in [0, 1) picks where
    within one full loop period (per-game polls -> _run_cycle -> 45s sleep ->
    top-of-loop check) the flag gets touched, modeling "trip happens at an
    arbitrary point in the cycle."

    Uses a fake monotonic clock so the test does not actually sleep.
    """
    clock = {"t": 0.0}

    def advance(dt: float) -> None:
        clock["t"] += dt

    n_games = random.randint(1, 6)  # plausible concurrent live-game count
    per_game_check_cost_s = 0.0005  # kill_switch_armed() is a stat() call
    cycle_duration = random.choice(EMPIRICAL_CYCLE_DURATIONS_S)

    # Total duration of one full real loop period, used to convert
    # touch_at_fraction into an absolute touch time.
    period = n_games * per_game_check_cost_s + cycle_duration + POLL_INTERVAL_S
    touch_at = touch_at_fraction * period

    detected_at = None

    # top-of-loop check
    if clock["t"] >= touch_at and flag_path.exists():
        detected_at = clock["t"]

    if detected_at is None:
        # per-game checks
        for _ in range(n_games):
            advance(per_game_check_cost_s)
            if clock["t"] >= touch_at and flag_path.exists():
                detected_at = clock["t"]
                break

    if detected_at is None:
        # _run_cycle() — no check inside, so the flag cannot be observed
        # mid-cycle even if touched during it
        advance(cycle_duration)

        # unconditional post-cycle sleep — again, no check inside it
        advance(POLL_INTERVAL_S)

        # next top-of-loop check, immediately after the sleep
        if clock["t"] >= touch_at:
            detected_at = clock["t"]

    assert detected_at is not None
    return detected_at - touch_at


@pytest.fixture()
def flag_path(tmp_path: Path) -> Path:
    p = tmp_path / "t4_mlb_kill_switch.flag"
    p.touch()  # existence is all kill_switch_armed() checks
    return p


def test_kill_switch_armed_is_real_function_behavior(flag_path: Path, tmp_path: Path) -> None:
    """Sanity: we are driving the real `kill_switch_armed`, not a reimplementation."""
    assert kill_switch_armed(flag_path) is True
    assert kill_switch_armed(tmp_path / "does_not_exist.flag") is False


def test_band_level_detection_latency_distribution(flag_path: Path) -> None:
    random.seed(20260826)
    latencies = [
        _simulate_one_trial(flag_path, touch_at_fraction=random.random())
        for _ in range(N_TRIALS)
    ]
    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p90 = latencies[int(n * 0.90)]
    p99 = latencies[int(n * 0.99)]
    lo, hi = latencies[0], latencies[-1]

    print(
        f"\n[GG-038 T4-MLB band-level detection latency, n={n} trials]\n"
        f"  min={lo:.3f}s  p50={p50:.3f}s  p90={p90:.3f}s  p99={p99:.3f}s  max={hi:.3f}s\n"
        f"  NFR-03 bar: 60.0s\n"
        f"  fraction of trials exceeding 60s: {sum(1 for x in latencies if x > 60.0) / n:.1%}"
    )

    # Structural floor: touching the flag right before a check is observed
    # almost immediately (near-zero latency is possible).
    assert lo < 0.1
    # Structural ceiling: worst case is bounded by
    # (n_games * check_cost) + max(cycle_duration) + POLL_INTERVAL_S, i.e.
    # comfortably under ~2 minutes for this system's real parameters.
    assert hi < 6 * per_game_upper_bound() + max(EMPIRICAL_CYCLE_DURATIONS_S) + POLL_INTERVAL_S + 1.0


def per_game_upper_bound() -> float:
    return 0.0005


def test_worst_case_matches_empirical_vps_data() -> None:
    """
    Cross-check: the "touch right after a check just passed" worst case is
    structurally ~= POLL_INTERVAL_S + cycle_duration, which is exactly what
    the real VPS cycle-start-to-cycle-start gap measures (48 real cycles,
    2026-08-26 pull): min 51.47s / p50 66.96s / p90 74.67s / max 81.19s.
    POLL_INTERVAL_S (45s) + the empirical cycle-duration range (0.007-7.13s)
    covers 45.0-52.1s, which undershoots the real p50/p90/max — meaning real
    production latency is WORSE than the pure-sleep structural floor, almost
    certainly due to real network I/O (ESPN/Kalshi fetch) inside the loop
    that this harness does not model. Document this gap rather than papering
    over it: the harness's number is a structural lower bound, not a ceiling.
    """
    structural_min = POLL_INTERVAL_S + min(EMPIRICAL_CYCLE_DURATIONS_S)
    structural_max = POLL_INTERVAL_S + max(EMPIRICAL_CYCLE_DURATIONS_S)

    real_p50 = 66.955196
    real_max = 81.187241

    assert structural_min < real_p50, (
        "structural floor should undershoot real p50 (real loop has more "
        "overhead than sleep+cycle alone, e.g. network I/O)"
    )
    assert structural_max < real_max
    print(
        f"\n[Cross-check] structural (sleep+cycle only): {structural_min:.2f}s-{structural_max:.2f}s "
        f"vs real VPS cycle-gap: 51.47s-81.19s (p50=66.96s, p90=74.67s)\n"
        "  Gap is real, unmodeled loop overhead (network I/O) -- the real "
        "system is measurably slower than the pure sleep+cycle structural bound."
    )


def test_check_primitive_microbenchmark(flag_path: Path) -> None:
    """
    Isolate the cost of the check *primitive* itself (a filesystem stat via
    Path.exists()) from the check *interval* structure measured above. This
    answers "how fast is one kill_switch_armed() call", not "how often is it
    called" -- two very different numbers.
    """
    N = 1000
    samples = []
    for _ in range(N):
        t0 = time.perf_counter()
        kill_switch_armed(flag_path)
        samples.append(time.perf_counter() - t0)
    samples.sort()
    p50 = samples[int(N * 0.50)]
    p99 = samples[int(N * 0.99)]
    print(
        f"\n[GG-038 kill_switch_armed() primitive cost, n={N}]\n"
        f"  min={samples[0]*1e6:.1f}us  p50={p50*1e6:.1f}us  "
        f"p99={p99*1e6:.1f}us  max={samples[-1]*1e6:.1f}us"
    )
    # The primitive itself is not the bottleneck -- it must be microseconds,
    # not a meaningful fraction of the 45-81s interval measured above.
    assert p99 < 0.05
