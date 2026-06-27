"""
PIPE-08 MLB: Daily Schedule Validator + Cron Adjuster
======================================================
Pipeline:     PIPE-08 MLB (schedule governance)
Schedule:     30 8 * * * (08:30 UTC / 4:30am ET) — runs before every MLB pipe
Environment:  ENV-02 (VPS)

Pulls today's MLB schedule from statsapi.mlb.com (official, no auth required).
Computes optimal fire times for all dynamic-timing pipes in the MLB arm:
  - PIPE-06pre (pregame): 45 min before T4, floor 14:00 UTC
  - PIPE-07 MLB (T4):     30 min before earliest first pitch, floor 15:00 UTC
  - T4 timeout:           (latest game start + 4h30m buffer) − T4 start, min 3h

Modifies LIVE CRONTAB only (not cron.conf). cron.conf defaults are preserved
as fallback; each git deploy resets to defaults; PIPE-08 re-applies dynamic
timing the next morning. Do not commit crontab diffs — they are ephemeral.

Static-timing pipes are NOT adjusted (T1=11:00, T2=19:30, PIPE-05R=06:30)
but are validated for assumption violations and generate warnings if at risk.

Handles:
  - Postponements / cancellations (all-postponed: T4 set to idle window)
  - Doubleheaders (latest game extends T4 timeout)
  - Extra innings (4h30m per-game buffer in timeout calc)
  - Rain/suspension status (logged as warnings; game kept active)
  - Parse failures (aborts crontab update; cron.conf defaults remain active)

Outputs:
  logs/schedule_validation_YYYYMMDD.json — full slate + timing decisions
  logs/schedule_validator_mlb.log       — append-only run log
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
PROJ_ROOT = Path(os.environ.get("PROJ", Path(__file__).resolve().parents[3]))
LOG_DIR = PROJ_ROOT / "logs"

MLB_SCHEDULE_API = "https://statsapi.mlb.com/api/v1/schedule"
SPORT_ID_MLB = 1

log = logging.getLogger(__name__)

# States that definitively mean the game will NOT be played today.
# "Delayed*" and "Suspended" are kept active — they may still be played.
NO_PLAY_STATES = frozenset({"Postponed", "Cancelled", "Postponed - Rain"})

# States that indicate uncertainty — log warning, keep as active
RISK_STATES = frozenset({"Suspended", "Delayed", "Delayed: Rain", "Rain Delay"})

# ---------------------------------------------------------------------------
# T4 (PIPE-07 MLB)
T4_BUFFER_BEFORE_PITCH_MIN: int = 30   # fire T4 this many min before first pitch
T4_FLOOR_H: int = 15                   # never before 15:00 UTC (11am ET)
T4_FLOOR_M: int = 0
T4_ALL_POSTPONED_H: int = 23           # if all off: idle window
T4_ALL_POSTPONED_M: int = 0
T4_ALL_POSTPONED_TIMEOUT_S: int = 1800 # 30 min — detects 0 games and exits
GAME_EXTRA_INNINGS_BUFFER_S: int = int(4.5 * 3600)  # 4h30m per game
T4_MIN_TIMEOUT_S: int = 3 * 3600       # never less than 3h

# Pregame (PIPE-06pre)
PREGAME_LEAD_BEFORE_T4_MIN: int = 45   # pregame fires this many min before T4
PREGAME_FLOOR_H: int = 14              # never before 14:00 UTC (10am ET)
PREGAME_FLOOR_M: int = 0

# T1 guard (PIPE-05 fires at 11:00 UTC — warn if game < 90 min after T1)
T1_FIRE_H: int = 11
T1_FIRE_M: int = 0
T1_DANGER_LEAD_MIN: int = 90

# T2 guard (PIPE-05.5 fires at 19:30 UTC — warn if game already final)
T2_FIRE_H: int = 19
T2_FIRE_M: int = 30

# Resolution guard (PIPE-05R fires at 06:30 UTC next day)
RESOLUTION_FIRE_H: int = 6
RESOLUTION_FIRE_M: int = 30

# ---------------------------------------------------------------------------
# Schedule fetch
# ---------------------------------------------------------------------------

def fetch_schedule(game_date: date) -> list[dict]:
    """Pull today's MLB schedule from official statsapi.mlb.com."""
    params = {
        "sportId": SPORT_ID_MLB,
        "date": game_date.strftime("%m/%d/%Y"),
        "hydrate": "team",
    }
    resp = requests.get(MLB_SCHEDULE_API, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    games: list[dict] = []
    for date_block in data.get("dates", []):
        games.extend(date_block.get("games", []))
    return games


# ---------------------------------------------------------------------------
# Game classification helpers
# ---------------------------------------------------------------------------

def _team_name(game: dict, side: str) -> str:
    return game.get("teams", {}).get(side, {}).get("team", {}).get("name", "?")


def _matchup(game: dict) -> str:
    return f"{_team_name(game, 'away')} @ {_team_name(game, 'home')}"


def _detailed_state(game: dict) -> str:
    return game.get("status", {}).get("detailedState", "Unknown")


def _parse_start_utc(game: dict) -> datetime | None:
    raw = game.get("gameDate")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def classify_games(games: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split games into (active, postponed).
    Active = games that may still be played today.
    Postponed = definitively off (Postponed / Cancelled).
    """
    active, postponed = [], []
    for g in games:
        state = _detailed_state(g)
        if state in NO_PLAY_STATES:
            postponed.append(g)
        else:
            active.append(g)
    return active, postponed


def _game_summary(g: dict) -> dict:
    start = _parse_start_utc(g)
    return {
        "game_pk": g.get("gamePk"),
        "matchup": _matchup(g),
        "start_utc": start.isoformat() if start else None,
        "status": _detailed_state(g),
    }


# ---------------------------------------------------------------------------
# Timing computation
# ---------------------------------------------------------------------------

def compute_t4_window(
    active_games: list[dict],
    now_utc: datetime,
) -> tuple[int, int, int, list[str]]:
    """
    Return (t4_hour, t4_min, timeout_s, warnings).

    t4_hour / t4_min: when PIPE-07 MLB should fire today (UTC)
    timeout_s:        how many seconds T4 should run before forced exit
    warnings:         list of human-readable issue strings
    """
    warnings: list[str] = []

    if not active_games:
        msg = "ALL_GAMES_OFF: No active games today. T4 set to idle window at 23:00 UTC."
        log.warning(msg)
        warnings.append(msg)
        return T4_ALL_POSTPONED_H, T4_ALL_POSTPONED_M, T4_ALL_POSTPONED_TIMEOUT_S, warnings

    starts = [s for g in active_games if (s := _parse_start_utc(g)) is not None]
    if not starts:
        msg = "PARSE_FAILURE: Could not parse start time for any active game. Crontab NOT updated."
        log.error(msg)
        warnings.append(msg)
        return T4_ALL_POSTPONED_H, T4_ALL_POSTPONED_M, T4_ALL_POSTPONED_TIMEOUT_S, warnings

    earliest = min(starts)
    latest = max(starts)

    # T4 start: buffer before earliest first pitch
    raw_t4 = earliest - timedelta(minutes=T4_BUFFER_BEFORE_PITCH_MIN)
    floor_dt = raw_t4.replace(hour=T4_FLOOR_H, minute=T4_FLOOR_M, second=0, microsecond=0)
    if raw_t4 < floor_dt:
        warnings.append(
            f"T4_FLOOR_APPLIED: Computed T4 start {raw_t4.strftime('%H:%M')} UTC "
            f"< floor {T4_FLOOR_H:02d}:{T4_FLOOR_M:02d} UTC. "
            f"First pitch {earliest.strftime('%H:%M')} UTC — T4 will miss pre-pitch window."
        )
        t4_dt = floor_dt
    else:
        t4_dt = raw_t4

    # Round minute to nearest 5 for cron cleanliness
    t4_hour = t4_dt.hour
    t4_min = (t4_dt.minute // 5) * 5

    # Timeout: T4 start → latest game expected end
    t4_ref = now_utc.replace(
        hour=t4_hour, minute=t4_min, second=0, microsecond=0
    )
    latest_expected_end = latest + timedelta(seconds=GAME_EXTRA_INNINGS_BUFFER_S)
    timeout_s = int((latest_expected_end - t4_ref).total_seconds())
    timeout_s = max(timeout_s, T4_MIN_TIMEOUT_S)

    log.info(
        "First pitch: %s UTC | Last game: %s UTC | Expected end (w/buffer): %s UTC",
        earliest.strftime("%H:%M"), latest.strftime("%H:%M"),
        latest_expected_end.strftime("%H:%M"),
    )
    log.info(
        "T4: %02d:%02d UTC → ~%s UTC | timeout %.1fh (%ds)",
        t4_hour, t4_min, latest_expected_end.strftime("%H:%M"),
        timeout_s / 3600, timeout_s,
    )
    return t4_hour, t4_min, timeout_s, warnings


def compute_pregame_time(t4_hour: int, t4_min: int) -> tuple[int, int]:
    """
    Pregame fires PREGAME_LEAD_BEFORE_T4_MIN before T4, with a hard floor.
    Returns (hour, minute) UTC.
    """
    t4_total = t4_hour * 60 + t4_min
    pre_total = t4_total - PREGAME_LEAD_BEFORE_T4_MIN
    floor_total = PREGAME_FLOOR_H * 60 + PREGAME_FLOOR_M
    pre_total = max(pre_total, floor_total)
    return divmod(pre_total, 60)


# ---------------------------------------------------------------------------
# Pipe assumption guards (T1, T2, resolution)
# ---------------------------------------------------------------------------

def check_t1_guard(active_games: list[dict]) -> list[str]:
    """
    T1 (PIPE-05) fires at 11:00 UTC and places bets on Preview-state markets.
    Warn if any game starts within T1_DANGER_LEAD_MIN minutes of T1 fire time —
    contamination guard may fail if markets flip to Live before T1 finishes.
    MLB has never scheduled a game before 13:00 UTC (9am ET), so this guard
    fires only on truly extraordinary scheduling.
    """
    warnings: list[str] = []
    t1_total = T1_FIRE_H * 60 + T1_FIRE_M
    for g in active_games:
        start = _parse_start_utc(g)
        if not start:
            continue
        game_total = start.hour * 60 + start.minute
        lead_min = game_total - t1_total
        if lead_min < T1_DANGER_LEAD_MIN:
            warnings.append(
                f"T1_RISK: {_matchup(g)} starts at {start.strftime('%H:%M')} UTC — "
                f"only {lead_min}min after T1 at {T1_FIRE_H:02d}:{T1_FIRE_M:02d} UTC. "
                f"Contamination guard may be stressed. Verify T1 run completes before first pitch."
            )
    return warnings


def check_t2_guard(active_games: list[dict]) -> list[str]:
    """
    T2 (PIPE-05.5) fires at 19:30 UTC and requires lineups not yet posted.
    Warn if any game starts before T2 fires (T2 contamination guard will skip those,
    but this reduces coverage). Informational only — T2 handles this gracefully.
    """
    warnings: list[str] = []
    t2_total = T2_FIRE_H * 60 + T2_FIRE_M
    early = [g for g in active_games
             if (s := _parse_start_utc(g)) and s.hour * 60 + s.minute < t2_total]
    if early:
        warnings.append(
            f"T2_COVERAGE: {len(early)}/{len(active_games)} games start before T2 at "
            f"{T2_FIRE_H:02d}:{T2_FIRE_M:02d} UTC — these will be skipped by T2 contamination guard. "
            f"T1 and T4 provide coverage for those games."
        )
    return warnings


def check_resolution_guard(active_games: list[dict]) -> list[str]:
    """
    PIPE-05R fires at 06:30 UTC daily and resolves the previous night's games.
    Risk exists for late-night games (start 00:00–08:00 UTC = 8pm–4am ET) whose
    extra-inning expected end overruns the 06:30 UTC resolution window on the same
    calendar day. Evening games (start 17:00+ UTC) always finish before 06:30 UTC
    next day and are safe.
    """
    warnings: list[str] = []
    for g in active_games:
        start = _parse_start_utc(g)
        if not start:
            continue
        # Only late-night UTC games (00:00–08:00 UTC) are at risk of bleeding past
        # the 06:30 UTC resolution window on the SAME calendar day.
        if start.hour >= 8:
            continue
        expected_end = start + timedelta(seconds=GAME_EXTRA_INNINGS_BUFFER_S)
        resolution_same_day = start.replace(
            hour=RESOLUTION_FIRE_H, minute=RESOLUTION_FIRE_M, second=0, microsecond=0
        )
        if expected_end > resolution_same_day:
            warnings.append(
                f"RESOLUTION_RISK: {_matchup(g)} (start {start.strftime('%H:%M')} UTC) "
                f"expected end {expected_end.strftime('%H:%M')} UTC — "
                f"after PIPE-05R at {RESOLUTION_FIRE_H:02d}:{RESOLUTION_FIRE_M:02d} UTC. "
                f"Extra-inning or delayed game may not be fully resolved. "
                f"Check resolve_mlb_cron.log next morning."
            )
    return warnings


def check_risk_state_games(active_games: list[dict]) -> list[str]:
    """Warn about games in weather/suspension risk states kept as active."""
    warnings: list[str] = []
    for g in active_games:
        state = _detailed_state(g)
        if state in RISK_STATES:
            warnings.append(
                f"GAME_RISK_STATE: {_matchup(g)} — status '{state}'. "
                f"Kept active; may be postponed intraday. Monitor manually."
            )
    return warnings


# ---------------------------------------------------------------------------
# Crontab update
# ---------------------------------------------------------------------------

def update_live_crontab(
    pregame_hour: int,
    pregame_min: int,
    t4_hour: int,
    t4_min: int,
    t4_timeout_s: int,
) -> dict[str, bool]:
    """
    Modify the LIVE crontab (kernel-level via `crontab -l` / `crontab -`).
    Does NOT touch cron.conf on disk — git-managed defaults are preserved.

    Targets:
      run_mlb_pregame.py  → update minute/hour
      run_t4_mlb_live.py  → update minute/hour and timeout value

    Returns {"pregame_changed": bool, "t4_changed": bool}.
    """
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"crontab -l failed: {result.stderr.strip()}")

    lines = result.stdout.splitlines(keepends=True)
    changes = {"pregame_changed": False, "t4_changed": False}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue

        # PIPE-06pre — pregame context
        if "run_mlb_pregame.py" in stripped:
            m = re.match(r'^(\d+)\s+(\d+)\s+(.*)', stripped)
            if not m:
                log.warning("Could not parse PIPE-06pre cron line: %s", stripped)
                continue
            old_m, old_h, rest = int(m.group(1)), int(m.group(2)), m.group(3)
            new_line = f"{pregame_min} {pregame_hour} {rest}\n"
            if new_line != line:
                log.info("PIPE-06pre: %02d:%02d → %02d:%02d UTC",
                         old_h, old_m, pregame_hour, pregame_min)
                lines[i] = new_line
                changes["pregame_changed"] = True
            else:
                log.info("PIPE-06pre: unchanged at %02d:%02d UTC", old_h, old_m)

        # PIPE-07 MLB — T4 live
        elif "run_t4_mlb_live.py" in stripped:
            m = re.match(r'^(\d+)\s+(\d+)\s+(.*)', stripped)
            if not m:
                log.warning("Could not parse PIPE-07 MLB T4 cron line: %s", stripped)
                continue
            old_m, old_h, rest = int(m.group(1)), int(m.group(2)), m.group(3)
            rest_updated = re.sub(r'timeout\s+\d+', f'timeout {t4_timeout_s}', rest)
            new_line = f"{t4_min} {t4_hour} {rest_updated}\n"
            if new_line != line:
                log.info(
                    "PIPE-07 T4: %02d:%02d → %02d:%02d UTC, timeout → %ds (%.1fh)",
                    old_h, old_m, t4_hour, t4_min, t4_timeout_s, t4_timeout_s / 3600,
                )
                lines[i] = new_line
                changes["t4_changed"] = True
            else:
                log.info("PIPE-07 T4: unchanged at %02d:%02d UTC, timeout %ds",
                         old_h, old_m, t4_timeout_s)

    if any(changes.values()):
        new_crontab = "".join(lines)
        proc = subprocess.run(
            ["crontab", "-"], input=new_crontab, capture_output=True, text=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"crontab reinstall failed: {proc.stderr.strip()}")
        log.info("Live crontab reinstalled (pregame=%s, t4=%s)",
                 changes["pregame_changed"], changes["t4_changed"])
    else:
        log.info("Live crontab: no changes needed")

    return changes


# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------

def write_report(
    game_date: date,
    active: list[dict],
    postponed: list[dict],
    pregame_hour: int,
    pregame_min: int,
    t4_hour: int,
    t4_min: int,
    t4_timeout_s: int,
    warnings: list[str],
    changes: dict[str, bool],
) -> None:
    report = {
        "date": game_date.isoformat(),
        "generated_utc": datetime.now(tz=timezone.utc).isoformat(),
        "slate": {
            "active_count": len(active),
            "postponed_count": len(postponed),
            "active_games": [_game_summary(g) for g in active],
            "postponed_games": [_game_summary(g) for g in postponed],
        },
        "computed_schedule": {
            "pregame_utc": f"{pregame_hour:02d}:{pregame_min:02d}",
            "t4_start_utc": f"{t4_hour:02d}:{t4_min:02d}",
            "t4_cron_expression": f"{t4_min} {t4_hour} * * *",
            "t4_timeout_s": t4_timeout_s,
            "t4_timeout_h": round(t4_timeout_s / 3600, 2),
        },
        "static_pipes": {
            "T1_PIPE05": f"{T1_FIRE_H:02d}:{T1_FIRE_M:02d} UTC (fixed)",
            "T2_PIPE055": f"{T2_FIRE_H:02d}:{T2_FIRE_M:02d} UTC (fixed)",
            "PIPE05R_resolution": f"{RESOLUTION_FIRE_H:02d}:{RESOLUTION_FIRE_M:02d} UTC (fixed)",
        },
        "warnings": warnings,
        "crontab_changes": changes,
    }
    path = LOG_DIR / f"schedule_validation_{game_date.strftime('%Y%m%d')}.json"
    path.write_text(json.dumps(report, indent=2))
    log.info("Report written: %s", path.name)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    now_utc = datetime.now(tz=timezone.utc)
    today = now_utc.date()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(LOG_DIR / "schedule_validator_mlb.log")),
        ],
    )

    log.info("=" * 60)
    log.info("PIPE-08 MLB Schedule Validator — %s", today.isoformat())
    log.info("=" * 60)

    # 1. Fetch schedule
    try:
        games = fetch_schedule(today)
    except Exception as exc:
        log.error("Schedule fetch FAILED: %s — crontab NOT modified", exc)
        sys.exit(1)

    log.info("Fetched %d games for %s", len(games), today.isoformat())

    # 2. Classify
    active, postponed = classify_games(games)
    log.info("%d active | %d postponed/cancelled", len(active), len(postponed))

    for g in postponed:
        log.warning("POSTPONED: %s — %s", _matchup(g), _detailed_state(g))

    for g in active:
        start = _parse_start_utc(g)
        log.info("  GAME: %s | %s UTC | %s",
                 _matchup(g),
                 start.strftime("%H:%M") if start else "?",
                 _detailed_state(g))

    # 3. Compute T4 window
    t4_hour, t4_min, t4_timeout_s, compute_warnings = compute_t4_window(active, now_utc)
    pregame_hour, pregame_min = compute_pregame_time(t4_hour, t4_min)

    log.info("Computed: pregame=%02d:%02d UTC | T4=%02d:%02d UTC | T4 timeout=%ds (%.1fh)",
             pregame_hour, pregame_min, t4_hour, t4_min, t4_timeout_s, t4_timeout_s / 3600)

    # 4. Run assumption guards for static-timing pipes
    all_warnings = (
        compute_warnings
        + check_risk_state_games(active)
        + check_t1_guard(active)
        + check_t2_guard(active)
        + check_resolution_guard(active)
    )

    for w in all_warnings:
        log.warning("WARN: %s", w)

    # 5. Update live crontab
    if "PARSE_FAILURE" in " ".join(all_warnings):
        log.error("Aborting crontab update due to parse failure — defaults remain active")
        changes: dict[str, bool] = {"pregame_changed": False, "t4_changed": False}
    else:
        try:
            changes = update_live_crontab(pregame_hour, pregame_min,
                                          t4_hour, t4_min, t4_timeout_s)
        except Exception as exc:
            log.error("Crontab update FAILED: %s — defaults remain active", exc)
            changes = {"pregame_changed": False, "t4_changed": False}

    # 6. Write report
    write_report(
        today, active, postponed,
        pregame_hour, pregame_min,
        t4_hour, t4_min, t4_timeout_s,
        all_warnings, changes,
    )

    log.info("PIPE-08 complete — %d active games, %d warnings, pregame=%02d:%02d, T4=%02d:%02d",
             len(active), len(all_warnings), pregame_hour, pregame_min, t4_hour, t4_min)


if __name__ == "__main__":
    main()
