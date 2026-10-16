"""W62.1 Part B: silent-arm alarm (GG-532 follow-on).

One question per arm: was at least one game scheduled to START inside this arm's window (last N hours, per the
arm's OWN schedule source) while the arm wrote ZERO rows in that window? Off-days and off-season have no games,
so they are never alarms. Computed on read; reads files only, writes nothing, touches no order/stake/cron.

Why this exists: the MLB postseason shadow wrote nothing for ~29h (GG-532) and was found by hand. Every other
freshness chip is mtime-based and goes quiet-green on an off-day; none asks "was there anything to write?".

N per arm is stated on its ``ArmSpec.why``. Rows count if written up to ``lead_h`` BEFORE the window opens: the
pregame arms write T3 rows up to 60 minutes before a start, so a game at the window's left edge was
legitimately served by a row just before it.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

_NOT_STARTED = ("postponed", "cancel", "suspend")


@dataclass(frozen=True)
class ArmSpec:
    key: str
    name: str
    window_h: float      # N: games started in the last N hours must have been served by a row in that window
    lead_h: float        # rows written this long before the window opens still count (T3 writes <=1h pre-start)
    why: str             # reason N was chosen (shown in docs/tests, not the UI)


@dataclass
class ArmInput:
    spec: ArmSpec
    game_starts: Optional[list[datetime]]   # tz-aware UTC starts from the arm's own schedule; None = unreadable
    last_row_ts: Optional[datetime]         # newest row the arm wrote (tz-aware UTC); None = none found
    note: str = ""                          # why a source was unreadable


SPECS = {
    "mlb_shadow": ArmSpec("mlb_shadow", "MLB game-market shadow", 12, 1,
                          "T1 cron every 6h + T3 every 10 min in the 15-60 min pre-start window: any game that "
                          "started in 12h had >=2 T1 runs and a T3 pass, so zero rows in 12h is a dead arm"),
    "nfl_shadow": ArmSpec("nfl_shadow", "NFL shadow", 12, 1,
                          "same T1 6h / T2 hourly / T3 10-min cron shape as the MLB shadow"),
    "nfl_qb_challenger": ArmSpec("nfl_qb_challenger", "NFL QB challenger shadow", 12, 1,
                                 "W65.3: T1 6h cron (staggered minute) on the same hours as the frozen NFL T1; "
                                 "same KXNFLGAME games, so it must write whenever the frozen NFL arm does"),
    "nhl_shadow": ArmSpec("nhl_shadow", "NHL shadow", 12, 1,
                          "T1 daily 14:00Z, T2 every 30 min 15-01Z, T3 every 10 min 17-02Z: evening starts get "
                          "rows within the hour; 12h keeps a matinee start from false-alarming before T1 at 14Z"),
    "nba_preseason_shadow": ArmSpec("nba_preseason_shadow", "NBA preseason shadow", 12, 1,
                                    "hourly smoke-test cron (:57) writes whenever a preseason game is in window"),
    "nba_shadow": ArmSpec("nba_shadow", "NBA regular-season shadow", 12, 1,
                          "T1 6h / T2 hourly / T3 10-min crons, same shape as MLB/NFL"),
    "nba_player_points_shadow": ArmSpec("nba_player_points_shadow", "NBA player points shadow", 12, 1,
                                        "W67.1: EXP-039 points arm (T1 6h / T2 hourly / T3 10-min crons). The game-market "
                                        "arm excludes PLAYER_POINTS files (W78.3/GG-892) so neither arm masks the other"),
    "nba_player_points_minutes_shadow": ArmSpec(
        "nba_player_points_minutes_shadow", "NBA player points minutes+injury challenger (EXP-040)", 12, 1,
        "W70.2: EXP-040 rides the EXP-039 runner (same T1/T2/T3 crons), strike 15 only, own NBAMIN_*.jsonl ledgers; "
        "silent while EXP-039 writes means the challenger arm itself is dead (runner exits rc 3 and prints EXP-040 ARM FAILED)"),
    "t1_mlb": ArmSpec("t1_mlb", "T1 MLB paper pipeline", 30, 0,
                      "the T1 pipeline runs once a day (11:00Z PIPE-05, 18:45Z PIPE-06pre); 30h = one missed "
                      "daily run plus slack"),
    "t4_mlb": ArmSpec("t4_mlb", "T4 MLB live", 3, 0,
                      "T4 writes a cycle-log row every 45-90s while a game is live; a game lasts ~3h, so a game "
                      "that started 3h ago with no row is a dead process (GG-163 ran 43h unnoticed)"),
}


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def evaluate_arm(inp: ArmInput, now: datetime) -> dict:
    """Pure. status: silent | ok | idle | unknown."""
    now = _aware(now)
    s = inp.spec
    base = {"key": s.key, "name": s.name, "window_h": s.window_h}
    if inp.game_starts is None:
        return {**base, "status": "unknown", "games_in_window": None, "hours_silent": None,
                "text": f"{s.name}: cannot check ({inp.note or 'schedule source unreadable'})"}
    win_start = now - timedelta(hours=s.window_h)
    games = [g for g in (_aware(x) for x in inp.game_starts) if win_start <= g <= now]
    last = _aware(inp.last_row_ts) if inp.last_row_ts else None
    wrote = last is not None and last >= win_start - timedelta(hours=s.lead_h)
    last_txt = last.strftime("%Y-%m-%d %H:%MZ") if last else "none found"
    if not games:
        return {**base, "status": "idle", "games_in_window": 0, "hours_silent": None,
                "last_row": last.isoformat() if last else None,
                "text": f"{s.name}: no games in the last {s.window_h:g}h, nothing expected"}
    if wrote:
        return {**base, "status": "ok", "games_in_window": len(games), "hours_silent": None,
                "last_row": last.isoformat(),
                "text": f"{s.name}: {len(games)} game(s) started in the last {s.window_h:g}h, rows written"}
    hrs = round((now - last).total_seconds() / 3600, 1) if last else None
    since = f"no rows for {hrs:g}h" if hrs is not None else f"no rows found (looked back {s.window_h:g}h)"
    return {**base, "status": "silent", "games_in_window": len(games), "hours_silent": hrs,
            "last_row": last.isoformat() if last else None,
            "text": f"{s.name} is SILENT: {len(games)} game(s) started in the last {s.window_h:g}h but {since} "
                    f"(last row {last_txt})"}


def silent_arms(inputs: list[ArmInput], now: datetime) -> dict:
    arms = [evaluate_arm(i, now) for i in inputs]
    return {"as_of": _aware(now).strftime("%Y-%m-%dT%H:%M:%SZ"), "arms": arms,
            "silent": [a for a in arms if a["status"] == "silent"],
            "unknown": [a for a in arms if a["status"] == "unknown"]}


# ── loaders (read-only; every failure becomes "unknown", never a crash and never a false alarm) ──────────────

def _parse(ts) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        return _aware(datetime.fromisoformat(ts.replace("Z", "+00:00")))
    except ValueError:
        return None


def _tail_lines(p: Path, nbytes: int) -> list[str]:
    with p.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - nbytes))
        data = f.read().decode("utf-8", "replace")
    lines = data.splitlines()
    return lines[1:] if size > nbytes and lines else lines   # first line may be cut mid-row


def last_ts_in_files(files: list[Path], keys=("ts_utc", "ts", "timestamp"), nbytes: int = 1_048_576,
                     accept: Optional[Callable[[dict], bool]] = None,
                     until: Optional[datetime] = None) -> Optional[datetime]:
    """Newest row timestamp at or before ``until`` (default: no bound; the bound makes as-of replays honest)."""
    best = None
    for p in files:
        if not p.exists():
            continue
        for ln in reversed(_tail_lines(p, nbytes)):
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if accept and not accept(r):
                continue
            t = next((x for x in (_parse(r.get(k)) for k in keys) if x), None)
            if t and (until is None or t <= until):
                best = t if best is None or t > best else best
                break
    return best


def _mlb_starts(repo: Path) -> list[datetime]:
    import pandas as pd
    from prediction_market_bot.pregame_shadow.mlb_forecaster import is_placeholder_start
    cache = repo / "exp_output" / "MLB_GAME" / "cache_w47"
    g = pd.read_parquet(cache / "games.parquet")
    cur = cache / "games_current.parquet"
    if cur.exists():
        c = pd.read_parquet(cur)
        g = pd.concat([g[~g.season.isin(c.season.unique())], c], ignore_index=True)
    g = g[g.game_type.isin(["R", "F", "D", "L", "W"])]
    g = g[~g.status.astype(str).str.lower().str.contains("|".join(_NOT_STARTED))]
    out = []
    for t in pd.to_datetime(g.start_utc, utc=True, errors="coerce").dropna():
        if not is_placeholder_start(t):      # a 07:33Z placeholder is not a real start (GG-532)
            out.append(t.to_pydatetime())
    return out


def _nfl_starts(repo: Path) -> list[datetime]:
    import pandas as pd
    s = pd.read_parquet(repo / "exp_output" / "NFL" / "cache_w47" / "schedule_extended.parquet")
    et = ZoneInfo("America/New_York")
    out = []
    for r in s.itertuples():
        gt = getattr(r, "gametime", None)
        if isinstance(gt, str) and ":" in gt:
            hh, mm = gt.split(":")[:2]
            out.append(datetime.fromisoformat(str(r.gameday)).replace(hour=int(hh), minute=int(mm), tzinfo=et)
                       .astimezone(timezone.utc))
    return out


def _nhl_starts(repo: Path, now: datetime) -> list[datetime]:
    base = repo / "data" / "raw" / "nhl" / "schedule"
    season = now.year - (1 if now.month < 8 else 0)
    out = []
    for s in (season, season - 1):
        p = base / f"{s}.json"
        if p.exists():
            for g in json.loads(p.read_text()).get("games", []):
                t = _parse(g.get("start_time_utc"))
                if t:
                    out.append(t)
    return out


def _nba_starts(repo: Path, season_type: int) -> list[datetime]:
    import sys
    sys.path.insert(0, str(repo / "scripts"))
    import run_nba_pregame_shadow as nba     # reuse the arm's own game loader
    games = nba.load_games(repo / "data" / "raw" / "nba")
    return [t for t in (_parse(g.get("start_time_utc")) for g in games if g.get("season_type") == season_type) if t]


def _t1_last(logs: Path, until: datetime) -> Optional[datetime]:
    p = logs / "audit_mlb.jsonl"
    if not p.exists():
        return None
    best = None
    for ln in _tail_lines(p, 12_000_000):        # ~2-3 days of audit rows; PT-/PG- sessions are the T1 pipeline
        if '"session_id": "PT-' not in ln and '"session_id": "PG-' not in ln:
            continue
        try:
            t = _parse(json.loads(ln).get("timestamp"))
        except ValueError:
            continue
        if t and t <= until and (best is None or t > best):
            best = t
    return best


def load_inputs(repo: Path, logs: Optional[Path] = None, now: Optional[datetime] = None) -> list[ArmInput]:
    repo = Path(repo)
    logs = Path(logs) if logs else repo / "logs"
    now = _aware(now or datetime.now(timezone.utc))
    led = repo / "exp_output" / "PREGAME_SHADOW"
    pre = repo / "exp_output" / "PREGAME_SHADOW_PRESEASON"
    mlb_starts: list = []
    mlb_err = ""
    try:
        mlb_starts = _mlb_starts(repo)
    except Exception as e:
        mlb_err = f"MLB games cache: {type(e).__name__}"

    def arm(key, starts_fn, last_fn):
        spec = SPECS[key]
        try:
            starts, err = starts_fn(), ""
        except Exception as e:
            starts, err = None, f"schedule: {type(e).__name__}"
        try:
            last = last_fn()
        except Exception:
            last = None
        return ArmInput(spec, starts, last, err)

    def mlb_starts_fn():
        if mlb_err:
            raise RuntimeError(mlb_err)
        return mlb_starts

    return [
        arm("mlb_shadow", mlb_starts_fn, lambda: last_ts_in_files(sorted(led.glob("MLB_*.jsonl")), until=now)),
        arm("nfl_shadow", lambda: _nfl_starts(repo), lambda: last_ts_in_files(sorted(led.glob("NFL_*.jsonl")), until=now)),
        arm("nfl_qb_challenger", lambda: _nfl_starts(repo),
            lambda: last_ts_in_files(sorted((repo / "exp_output" / "PREGAME_SHADOW_NFLQB").glob("NFLQB_*.jsonl")), until=now)),
        arm("nhl_shadow", lambda: _nhl_starts(repo, now),
            lambda: last_ts_in_files(sorted(p for p in (repo / "data" / "shadow" / "nhl").glob("NHL_*.jsonl")), until=now)),
        arm("nba_preseason_shadow", lambda: _nba_starts(repo, 1), lambda: last_ts_in_files(sorted(pre.glob("NBA_*.jsonl")), until=now)),
        arm("nba_shadow", lambda: _nba_starts(repo, 2), lambda: last_ts_in_files(sorted(p for p in led.glob("NBA_*.jsonl") if "PLAYER_POINTS" not in p.name), until=now)),
        arm("nba_player_points_shadow", lambda: _nba_starts(repo, 2),
            lambda: last_ts_in_files(sorted(led.glob("NBA_NBA_PLAYER_POINTS_*.jsonl")), until=now)),
        arm("nba_player_points_minutes_shadow", lambda: _nba_starts(repo, 2),
            lambda: last_ts_in_files(sorted((repo / "exp_output" / "PREGAME_SHADOW_EXP040").glob("NBAMIN_*.jsonl")), until=now)),
        arm("t1_mlb", mlb_starts_fn, lambda: _t1_last(logs, now)),
        arm("t4_mlb", mlb_starts_fn, lambda: last_ts_in_files([logs / "t4_mlb_cycle_log.jsonl"], nbytes=262144, until=now)),
    ]


# GG-621 / W71.2: static inputs an arm silently starves without. A missing file writes no error anywhere - the arm
# just logs nothing - so the file's existence and size are checked here, independent of any game being in window.
DATA_PREREQS = (
    ("nba_player_box_2026", "data/raw/nba/players_2026.json", "games", 1000,
     "EXP-039/EXP-040 early-season rows (restore: scripts/nba_player_box_backfill.py --seasons 2026)"),
)


def data_prereqs(repo: Path) -> list[dict]:
    out = []
    for key, rel, field, min_rows, why in DATA_PREREQS:
        p = Path(repo) / rel
        rows, status = 0, "missing"
        if p.exists():
            try:
                d = json.loads(p.read_text())
                rows = len(d.get(field, {})) if isinstance(d, dict) else 0
                status = "ok" if rows > min_rows else "thin"
            except (OSError, ValueError):
                status = "unreadable"
        text = (f"{key}: {rel} {status} ({rows} {field}, need >{min_rows}) - {why}"
                if status != "ok" else f"{key}: {rel} ok ({rows} {field})")
        out.append({"key": key, "path": rel, "status": status, "rows": rows, "min_rows": min_rows, "text": text})
    return out


def compute(repo: Path, logs: Optional[Path] = None, now: Optional[datetime] = None) -> dict:
    now = _aware(now or datetime.now(timezone.utc))
    res = silent_arms(load_inputs(repo, logs, now), now)
    res["data_prereqs"] = data_prereqs(repo)
    return res


def compute_isolated(repo: Path, logs: Optional[Path] = None, timeout: int = 40) -> dict:
    """compute() in the repo's own venv python. The dashboard service runs on system python3 (no pandas), and
    the MLB/NFL schedule caches are parquet -- run in-process there, every arm reads 'cannot check'. Stdlib only."""
    import json
    import os
    import subprocess
    import sys
    repo = Path(repo)
    py = repo / "venv" / "bin" / "python"
    cmd = [str(py) if py.exists() else sys.executable, "-m", "prediction_market_bot.pregame_shadow.silent_arms", "--json"]
    if logs:
        cmd += ["--logs", str(logs)]
    r = subprocess.run(cmd, cwd=str(repo), env={**os.environ, "PYTHONPATH": str(repo / "src")},
                       capture_output=True, text=True, timeout=timeout)
    return json.loads(r.stdout[r.stdout.index("{"):])


if __name__ == "__main__":   # `python -m prediction_market_bot.pregame_shadow.silent_arms [YYYY-MM-DDTHH:MMZ] [--json] [--logs DIR]`
    import sys
    args = sys.argv[1:]
    as_json = "--json" in args
    logs = Path(args[args.index("--logs") + 1]) if "--logs" in args else None
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--logs")]
    root = Path(__file__).resolve().parents[3]
    at = _parse(pos[0].replace("Z", "+00:00")) if pos else None
    res = compute(root, logs=logs, now=at)
    if as_json:
        import json
        print(json.dumps(res, default=str))
    else:
        for a in res["arms"]:
            print(f"[{a['status'].upper():7}] {a['text']}")
        for d in res.get("data_prereqs", []):
            print(f"[{('OK' if d['status'] == 'ok' else 'MISSING' if d['status'] == 'missing' else 'THIN'):7}] {d['text']}")
