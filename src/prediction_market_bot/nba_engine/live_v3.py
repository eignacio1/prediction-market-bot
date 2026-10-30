"""EXP-044c live entry (W97.1): the v3 challenger prices the same board at tip-60 and logs beside v1 (EXP-044) and v2 (EXP-044b).

v3 = v2's as-of team means + two pre-tip availability factors (expected missing rotation share, rotation-weighted player net rating),
fitted once off-box (``12_EXPLORATORY/nba_engine_v3/freeze_v3.py``) and shipped as one hashed JSON. This runner loads that file only:
no player-level store is needed on the box. Rotation + player ratings are an end-of-2025-26 snapshot (not updated in season); the
injury statuses are the latest report published at or before tip - 60 min, taken from this runner's own append-only snapshot log
(the lineup-window capture keeps only its latest state, so no tip-60 snapshot exists anywhere else).

Claims (EXP-044c): spread and team total only. Moneyline and total rows are logged with ``claim=False``.
Places no order, reads no ledger and writes only its own JSONL. Edits nothing in v1/v2/v3.
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nba_availability import ET, UNREPORTED
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
from prediction_market_bot.nba_engine import engine_v2 as V, engine_v3 as V3, live as L, live_v2 as L2
from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / "12_EXPLORATORY/nba_engine_v3/frozen/v3_frozen_2027.json"
OUT_DIR = Path("exp_output/NBA_ENGINE_LIVE_V3")
CAPTURE_STATE = Path("exp_output/NBA/LINEUP_WINDOW/state.json")
CLAIMED = ("NBA_SPREAD", "NBA_TEAM_TOTAL")   # EXP-044c claims these families only
LEAD_MIN = 60.0


class SnapshotLeakError(RuntimeError):
    """A report published after tip - lead reached the pricing step."""


def load_frozen(path: Path = FROZEN) -> dict:
    """Load the frozen artifact and verify its sha256 (computed over the body without the hash key)."""
    art = json.loads(Path(path).read_text())
    want = art.pop("sha256")
    got = hashlib.sha256(json.dumps(art, sort_keys=True, indent=1).encode()).hexdigest()
    if got != want:
        raise ValueError(f"frozen v3 artifact hash mismatch: file {want[:16]} != computed {got[:16]}")
    art["sha256"] = want
    return art


def build_model(art: dict):
    prm = art["params"]
    p = V.V2Params(hca=prm["hca"], tbias=prm["tbias"], sd_margin=prm["sd_margin"], sd_total=prm["sd_total"],
                   shift_margin=dict(prm["shift_margin"]), shift_total=dict(prm["shift_total"]),
                   platt={f: tuple(v) for f, v in prm["platt"].items()})
    return p, V3.Centers(dict(art["centers"]))


# ---------------------------------------------------------------- injury snapshot log

def _slot_utc(slot_et: str) -> datetime:
    """``"YYYY-MM-DD HH:MM"`` ET wall clock -> UTC."""
    return datetime.strptime(slot_et, "%Y-%m-%d %H:%M").replace(tzinfo=ET).astimezone(timezone.utc)


def append_snapshot(state_path: Path, snap_path: Path, now: datetime) -> bool:
    """Append the capture's latest report to our own log (one row per slot). Names are re-normalised from the stored raw name with
    ``nba_injury_reports.norm_name`` (the capture's own key differs). Returns True when a new slot was written."""
    if not Path(state_path).exists():
        return False
    st = json.loads(Path(state_path).read_text())
    slot = st.get("slot_et")
    if not slot or not st.get("rows"):
        return False
    snap_path = Path(snap_path)
    if snap_path.exists():
        for line in snap_path.read_text().splitlines():
            if line.strip() and json.loads(line)["slot_et"] == slot:
                return False
    rows = {norm_name(v["name"]): v["status"] for v in st["rows"].values()}
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    with open(snap_path, "a") as fh:
        fh.write(json.dumps(dict(slot_et=slot, captured_utc=now.isoformat(), rows=rows)) + "\n")
    return True


def read_snapshots(snap_path: Path) -> list:
    p = Path(snap_path)
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def select_snapshot(snaps: list, tip: datetime, lead_min: float = LEAD_MIN):
    """Latest logged slot on the tip's ET date published at or before tip - lead. (slot_et, rows) or (None, {}). Raises on a leak."""
    cutoff = tip.timestamp() - lead_min * 60.0
    day = tip.astimezone(ET).date()
    best = None
    for s in snaps:
        ts = _slot_utc(s["slot_et"])
        if ts.astimezone(ET).date() != day or ts.timestamp() > cutoff:
            continue
        if best is None or ts > best[0]:
            best = (ts, s)
    if best is None:
        return None, {}
    if best[0].timestamp() > cutoff:
        raise SnapshotLeakError(f"slot {best[1]['slot_et']} after cutoff")
    return best[1]["slot_et"], best[1]["rows"]


# ---------------------------------------------------------------- factors

def team_factors(rotation: list, statuses: dict, rates: dict, has_report: bool) -> dict:
    """exp_missing = sum w*(1-p); lineup_net = sum w*rel_net; cover = rotation share the report lists. A player the report does not
    list (or any player when there is no report) gets the Unreported rate, as in the study."""
    miss = net = cover = 0.0
    fallback = rates.get(UNREPORTED, 1.0)
    for pl in rotation:
        st = statuses.get(pl["norm_name"]) if has_report else None
        pr = rates.get(st, fallback) if st is not None else fallback
        miss += pl["w"] * (1.0 - pr)
        net += pl["w"] * pl["rel_net"]
        cover += pl["w"] if st is not None else 0.0
    return dict(exp_missing=miss, lineup_net=net, cover=cover)


def game_factors(art: dict, home_id: str, away_id: str, statuses: dict, has_report: bool) -> tuple:
    rot, rates = art["rotation"], art["rates"]
    if str(home_id) not in rot or str(away_id) not in rot:
        return {}, dict(h_cover=None, a_cover=None)
    h = team_factors(rot[str(home_id)], statuses, rates, has_report)
    a = team_factors(rot[str(away_id)], statuses, rates, has_report)
    x = dict(d_exp_missing=h["exp_missing"] - a["exp_missing"], s_exp_missing=h["exp_missing"] + a["exp_missing"],
             d_lineup_net=h["lineup_net"] - a["lineup_net"], s_lineup_net=h["lineup_net"] + a["lineup_net"])
    return x, dict(h_cover=round(h["cover"], 4), a_cover=round(a["cover"], 4))


def price_event_rows(event_rows: dict, parsed_by_ticker: dict, tg: pd.DataFrame, team_ids: dict, art: dict, p: V.V2Params,
                     centers: V3.Centers, snaps: list, tip: datetime, now: datetime, pid: str) -> list:
    any_p = next(iter(parsed_by_ticker.values()))
    home, away = any_p["home"], any_p["away"]
    if home not in team_ids or away not in team_ids:
        return []
    cut = pd.Timestamp(tip)
    h = L.team_rating(tg, team_ids[home], L.SEASON, cut)
    a = L.team_rating(tg, team_ids[away], L.SEASON, cut)
    gm = L.game_means(h, a)
    slot, statuses = select_snapshot(snaps, tip)
    x, cov = game_factors(art, team_ids[home], team_ids[away], statuses, slot is not None)
    m, t = V3.game_means(p, centers, gm["mu_poss"] * gm["ppp_h"] / 100.0, gm["mu_poss"] * gm["ppp_a"] / 100.0, x)
    rows = []
    for tk, q in event_rows.items():
        pr = parsed_by_ticker[tk]
        pe = L2.engine_p(p, m, t, pr)
        if pe is None or q.get("yes_mid") is None:
            continue
        rows.append(dict(ticker=tk, event_ticker=pr["event_ticker"], family=pr["market_type"], game_date=pr["game_date"],
                         home=home, away=away, subject=pr["subject"],
                         strike_n=None if pr["strike"] is None else int(round(pr["strike"] + 0.5)),
                         p_engine=float(pe), p_market=float(q["yes_mid"]), half_spread=q.get("half_spread"),
                         quote_ts=q["run_ts"], tip_utc=tip.isoformat(), logged_at=now.isoformat(),
                         n_games_home=h["n_prior"], n_games_away=a["n_prior"], engine_version="v3",
                         engine_commit=L.ENGINE_COMMIT, params_hash=pid,
                         claim=pr["market_type"] in CLAIMED, injury_slot_et=slot,
                         injury_report=slot is not None, rotation_known=bool(x),
                         factors={k: round(v, 5) for k, v in x.items()}, **cov))
    return rows


def run(raw: str, espn_schedule: pd.DataFrame, current_tg: pd.DataFrame, now: Optional[datetime] = None,
        out_dir: Path = OUT_DIR, archive_dir: Path = L.ARCHIVE_DIR, state_path: Path = CAPTURE_STATE,
        frozen: Path = FROZEN) -> dict:
    """Log rows for every game whose tip - 60 min has passed and that is not yet logged. Idempotent per event."""
    now = now or datetime.now(timezone.utc)
    art = load_frozen(frozen)
    p, centers = build_model(art)
    pid = art["sha256"][:16]
    hist = L.load_history(raw)
    tg = pd.concat([hist, current_tg[current_tg["season_type"] == "regular-season"]], ignore_index=True)
    sched = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{raw}/schedule/*.parquet"))], ignore_index=True)
    abbr_id = {}
    for side in ("home", "away"):
        for _, r in sched.drop_duplicates(f"{side}_team_id").iterrows():
            abbr_id[r[f"{side}_team_abbreviation"]] = r[f"{side}_team_id"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snap_path = out_dir / "injury_snapshots.jsonl"
    new_snap = append_snapshot(state_path, snap_path, now)
    snaps = read_snapshots(snap_path)
    tips = L.tip_index(espn_schedule)
    f_out = out_dir / "rows.jsonl"
    done = set()
    if f_out.exists():
        done = {json.loads(l)["event_ticker"] for l in f_out.read_text().splitlines() if l.strip()}
    logged, skipped = 0, []
    for day in sorted({(now + timedelta(days=d)).strftime("%Y-%m-%d") for d in (0, 1)}):
        arch = L.read_archive(day, archive_dir) + L.read_archive((now - timedelta(days=1)).strftime("%Y-%m-%d"), archive_dir)
        by_event = {}
        for r in arch:
            pr = parse_market_ticker(r["ticker"])
            if pr:
                by_event.setdefault(pr["event_ticker"], {})[r["ticker"]] = pr
        for ev, parsed in by_event.items():
            if ev in done:
                continue
            p0 = next(iter(parsed.values()))
            tip = tips.get((p0["game_date"], p0["home"], p0["away"]))
            if tip is None or now < tip - L.LEAD or now >= tip:
                continue
            q = L.quote_at([r for r in arch if r["ticker"] in parsed], tip - L.LEAD)
            q = {t: v for t, v in q.items() if t in parsed}
            if not q:
                skipped.append((ev, "no_quote_at_tip_minus_60"))
                continue
            rows = price_event_rows(q, parsed, tg, abbr_id, art, p, centers, snaps, tip, now, pid)
            with open(f_out, "a") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            done.add(ev)
            logged += len(rows)
    status = dict(as_of=now.isoformat(), rows_logged_this_run=logged, events_logged_total=len(done), skipped=skipped,
                  params_hash=pid, snapshots_logged=len(snaps), new_snapshot=new_snap)
    (out_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main(argv: Optional[list] = None) -> int:
    import argparse
    from prediction_market_bot.c1_signal_ingestion import nba_current_season as C
    ap = argparse.ArgumentParser(description="EXP-044c: log v3 challenger prices at tip-60 beside the Kalshi archive quote.")
    ap.add_argument("--raw", required=True, help="NBA event store root holding schedule/espn_schedule/team_box (<= 2026)")
    ap.add_argument("--current-dir", type=Path, default=C.DEFAULT_OUT)
    ap.add_argument("--no-refresh", action="store_true", help="use the current-season table as it is")
    a = ap.parse_args(argv)
    if not a.no_refresh:
        C.refresh(a.current_dir)
    espn, _ = C.fetch("espn_schedule")
    cur = pd.read_parquet(a.current_dir / f"team_game_{C.SEASON}.parquet")
    print(json.dumps(run(a.raw, espn, cur), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
