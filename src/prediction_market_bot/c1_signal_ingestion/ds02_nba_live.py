"""
DS-02: NBA Stats API Live Game State Polling Adapter (Paper Prototype)
======================================================================
Component:    C1 (Signal Ingestion) — live game state sub-module
Phase active: PAPER PROTOTYPE — polling adapter only (30-60s lag)
              Production-grade real-time stream deferred to Phase 8 DS-02 ADR.
Upstream:     nba_api.live (NBA Stats API public CDN, ~30s update cadence)
Downstream:   run_t4_inplay.py → T4EventLoop.on_game_state_event()

What this module does:
    Polls the NBA Stats API live boxscore endpoint at a configurable interval
    (default 45s) and emits GameStateEvent objects for each active player in
    the operator's cohort. These events feed the T4 event loop decision tree.

Scope constraints (paper prototype):
    - NOT real-time: NBA CDN updates every ~30s; polling adds another 0-15s
    - NOT a WebSocket stream: single-threaded polling loop only
    - NOT SLA-guaranteed: no retry backoff, no dead-letter queue
    - Kill switch: file flag at KILL_SWITCH_PATH (default logs/t4_kill_switch.flag)
      To arm: touch logs/t4_kill_switch.flag
      To disarm: rm logs/t4_kill_switch.flag
    Phase 8 ADR will replace this with a real-time feed and C7-integrated kill switch.

Usage:
    python -m prediction_market_bot.c1_signal_ingestion.ds02_nba_live \\
        --game-id 0042500102 --cohort-ids 1629029 203507 1628978 --poll-sec 45

    Or import and use programmatically:
        feed = NBALiveFeed(game_id="0042500102", cohort_ids=[1629029, 203507])
        for event in feed.poll_once():
            loop.on_game_state_event(event)
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence

logger = logging.getLogger(__name__)

# Default kill switch flag file. Arm with: touch logs/t4_kill_switch.flag
KILL_SWITCH_PATH = Path("logs/t4_kill_switch.flag")

# NBA CDN updates every ~30s. Polling faster gains nothing; slower adds lag.
DEFAULT_POLL_INTERVAL_SEC = 45

# Game status codes from NBA Stats API
_STATUS_NOT_STARTED = 1
_STATUS_IN_PROGRESS = 2
_STATUS_FINISHED = 3


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LivePlayerState:
    """
    Single-player game state snapshot from the NBA live boxscore.
    Suitable for building a GameStateEvent for the T4 event loop.
    """
    player_id: int
    player_name: str
    team_id: int
    pts_so_far: int
    rebounds: int
    assists: int
    minutes_played: float    # decimal minutes of in-game time played
    quarter: int             # 1-4 (5+ = OT)
    time_remaining_min: float  # minutes remaining in game (full game view)
    game_id: str
    game_status: int         # 1=not started, 2=in progress, 3=finished


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------

def kill_switch_armed(flag_path: Path = KILL_SWITCH_PATH) -> bool:
    """
    File-based kill switch. Completes in <1ms (stat call only).

    Arm:   touch logs/t4_kill_switch.flag
    Disarm: rm logs/t4_kill_switch.flag

    Phase 8 ADR replaces this with C7 MonitorAgent in-memory state.
    """
    return flag_path.exists()


# ---------------------------------------------------------------------------
# Time parsing
# ---------------------------------------------------------------------------

def _parse_game_clock(game_clock: str) -> float:
    """
    Convert ISO 8601 duration string 'PT05M30.00S' to decimal minutes.

    Returns 0.0 on parse failure (conservative — treats game as over).
    """
    if not game_clock:
        return 0.0
    try:
        # Strip 'PT' prefix, split on 'M' and 'S'
        s = game_clock.upper().lstrip("PT")
        if "M" in s:
            minutes_part, rest = s.split("M", 1)
            seconds_part = rest.rstrip("S") or "0"
        else:
            minutes_part = "0"
            seconds_part = s.rstrip("S") or "0"
        return float(minutes_part) + float(seconds_part) / 60.0
    except (ValueError, AttributeError):
        logger.warning("Could not parse gameClock: %r", game_clock)
        return 0.0


def _total_time_remaining(quarter: int, clock_min: float) -> float:
    """
    Convert quarter + clock_min-remaining to full-game minutes remaining.

    Regulation: 4 quarters × 12 min = 48 min total.
    OT (quarter ≥ 5): each OT period = 5 min.
    """
    if quarter <= 0:
        return 48.0
    if quarter <= 4:
        quarters_remaining = max(0, 4 - quarter)
        return quarters_remaining * 12.0 + clock_min
    else:
        # OT: just the clock in this period
        return clock_min


# ---------------------------------------------------------------------------
# Live feed adapter
# ---------------------------------------------------------------------------

class NBALiveFeed:
    """
    Polls the NBA Stats API live boxscore for a single game.

    Parameters
    ----------
    game_id:
        10-digit NBA game ID string (e.g. "0042500102").
    cohort_ids:
        Player IDs to filter for. If empty, returns all players.
    p_t1_by_market:
        Optional dict mapping (player_id, threshold) → p_t1 for use as the
        T4 materiality benchmark. Pass empty dict if not available — the T4
        event loop handles missing p_t1 gracefully.
    kill_switch_path:
        Path to the kill switch flag file.
    """

    def __init__(
        self,
        game_id: str,
        cohort_ids: Sequence[int] = (),
        p_t1_by_market: Optional[dict[str, Any]] = None,
        kill_switch_path: Path = KILL_SWITCH_PATH,
    ) -> None:
        self._game_id = game_id
        self._cohort_ids = set(cohort_ids)
        self._p_t1 = p_t1_by_market or {}
        self._kill_path = kill_switch_path

    def poll_once(self) -> list[LivePlayerState]:
        """
        Fetch the current boxscore and return player states.
        Returns empty list if game not in progress or kill switch armed.
        """
        if kill_switch_armed(self._kill_path):
            logger.warning("DS-02: kill switch armed — polling suppressed")
            return []

        try:
            from nba_api.live.nba.endpoints import boxscore as bs_module
            bs = bs_module.BoxScore(game_id=self._game_id, timeout=10)
            data = bs.get_dict()
        except Exception as exc:
            logger.error("DS-02: boxscore fetch failed for %s: %s", self._game_id, exc)
            return []

        game = data.get("game", {})
        status = game.get("gameStatus", 0)
        if status != _STATUS_IN_PROGRESS:
            logger.info("DS-02: game %s status=%d (not in progress)", self._game_id, status)
            return []

        quarter = game.get("period", 1)
        game_clock_str = game.get("gameClock", "")
        clock_min = _parse_game_clock(game_clock_str)
        time_remaining = _total_time_remaining(quarter, clock_min)

        states: list[LivePlayerState] = []
        for team_key in ("homeTeam", "awayTeam"):
            team = game.get(team_key, {})
            team_id = int(team.get("teamId", 0))
            for player in team.get("players", []):
                pid = int(player.get("personId", 0))
                if self._cohort_ids and pid not in self._cohort_ids:
                    continue
                stats = player.get("statistics", {})
                mins_str = stats.get("minutesCalculated", "PT00M00.00S")
                mins_played = _parse_game_clock(mins_str.lstrip("P"))
                states.append(LivePlayerState(
                    player_id=pid,
                    player_name=player.get("name", ""),
                    team_id=team_id,
                    pts_so_far=int(stats.get("points", 0)),
                    rebounds=int(stats.get("reboundsTotal", 0)),
                    assists=int(stats.get("assists", 0)),
                    minutes_played=mins_played,
                    quarter=quarter,
                    time_remaining_min=time_remaining,
                    game_id=self._game_id,
                    game_status=status,
                ))

        logger.info(
            "DS-02: %d player states fetched (game=%s, Q%d, %.1f min remain)",
            len(states), self._game_id, quarter, time_remaining,
        )
        return states

    def run_loop(
        self,
        on_states: object,
        poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC,
    ) -> None:
        """
        Blocking polling loop. Calls on_states(list[LivePlayerState]) each tick.
        Stops when kill switch is armed or game finishes.

        Parameters
        ----------
        on_states:
            Callable(list[LivePlayerState]) invoked after each poll.
        poll_interval_sec:
            Seconds between polls. Default 45s (NBA CDN ~30s cadence).
        """
        logger.info(
            "DS-02: starting polling loop (game=%s, interval=%.0fs)",
            self._game_id, poll_interval_sec,
        )
        while True:
            if kill_switch_armed(self._kill_path):
                logger.warning("DS-02: kill switch armed — polling loop halted")
                break

            states = self.poll_once()
            if states:
                on_states(states)
            elif not kill_switch_armed(self._kill_path):
                # Game may have ended — check status
                try:
                    from nba_api.live.nba.endpoints import boxscore as bs_module
                    bs = bs_module.BoxScore(game_id=self._game_id, timeout=10)
                    st = bs.get_dict().get("game", {}).get("gameStatus", 0)
                    if st == _STATUS_FINISHED:
                        logger.info("DS-02: game %s finished — polling loop complete", self._game_id)
                        break
                except Exception:
                    pass

            time.sleep(poll_interval_sec)


# ---------------------------------------------------------------------------
# CLI entry point (smoke test / manual run)
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="DS-02 NBA live polling adapter — paper prototype"
    )
    parser.add_argument("--game-id", required=True, help="10-digit NBA game ID")
    parser.add_argument("--cohort-ids", nargs="*", type=int, default=[],
                        help="Player IDs to filter (empty = all players)")
    parser.add_argument("--poll-sec", type=float, default=DEFAULT_POLL_INTERVAL_SEC,
                        help=f"Poll interval in seconds (default {DEFAULT_POLL_INTERVAL_SEC})")
    parser.add_argument("--once", action="store_true",
                        help="Poll once and print output; do not loop")
    parser.add_argument("--kill-switch-path", default=str(KILL_SWITCH_PATH),
                        help="Path to kill switch flag file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")

    kill_path = Path(args.kill_switch_path)
    feed = NBALiveFeed(
        game_id=args.game_id,
        cohort_ids=args.cohort_ids,
        kill_switch_path=kill_path,
    )

    if args.once:
        states = feed.poll_once()
        if not states:
            print("No player states returned (game not in progress or kill switch armed).")
            return
        print(f"{'Player':<26} {'PID':>8} {'Pts':>4} {'Q':>2} {'Rem':>6}")
        print("-" * 52)
        for s in states:
            print(f"{s.player_name:<26} {s.player_id:>8} {s.pts_so_far:>4} "
                  f"{s.quarter:>2} {s.time_remaining_min:>6.1f}m")
    else:
        def _print_states(states: list[LivePlayerState]) -> None:
            print(f"\n[{time.strftime('%H:%M:%S')}] {len(states)} players — "
                  f"Q{states[0].quarter} {states[0].time_remaining_min:.1f}m remain")
            for s in states:
                print(f"  {s.player_name:<24} {s.pts_so_far:>3} pts")

        feed.run_loop(on_states=_print_states, poll_interval_sec=args.poll_sec)


if __name__ == "__main__":
    _cli()
