"""W126.4 Part C (B-024): NBA same-game COMBO shadow writer. EVALUATE-AND-LOG ONLY. Off unless PM_COMBO_SHADOW=on.

Read-only Kalshi list (open multivariate combos) + the NBA props store (box.json / tips.json) -> one simulation per game
(engine_v2 team draws + joint.py player stats, same draw index) -> every combo whose legs are all one game's NBA markets is priced
(``nba_engine.combo_price``) and a row appended to exp_output/COMBO_SHADOW/NBA_SAME_GAME_COMBO.jsonl with the engine P, the
product-of-legs P, legs priced / unpriced, the Kalshi quote showing (or none), the default-fee cost and minutes to tip.
No order, position, fill, stake or kelly. Pre-registration: 12_EXPLORATORY/pot_of_gold/COMBO_PREREG.md.

  PM_COMBO_SHADOW=on PYTHONPATH=src:. python3 scripts/nba_combo_shadow.py [--now ISO] [--no-refresh] [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.nba_engine import combo_price as CP  # noqa: E402
from prediction_market_bot.nba_engine import joint as J  # noqa: E402
from prediction_market_bot.nba_engine.sgp_price import GameDraws  # noqa: E402

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
MODEL_ID = "nba_combo_shadow_w126_4"
WINDOW_MIN = (0.0, 180.0)            # log combos whose game tips within 0-3 h (T-2h and T-30m both inside)
UNQUOTED_SAMPLE = 0.05               # share of no-quote, no-volume combos logged anyway (coverage of how often a price exists)
DEFAULT_FEE_MULT = 0.07              # taker; combo multiplier unverified (MECHANICS.md)


def enabled() -> bool:
    return os.environ.get("PM_COMBO_SHADOW", "off").strip().lower() in ("on", "1", "true")


def fee_default(p: float) -> float:
    """Taker fee per contract at the default multiplier, rounded up to the centi-cent."""
    import math
    return math.ceil(DEFAULT_FEE_MULT * p * (1 - p) * 1e4 - 1e-9) / 1e4


def fetch_open_combos(limit_pages: int = 80) -> list:
    out, cur = [], ""
    for _ in range(limit_pages):
        q = {"status": "open", "mve_filter": "only", "limit": 1000, **({"cursor": cur} if cur else {})}
        d = None
        for i in range(4):
            try:
                req = urllib.request.Request(KALSHI + "/markets?" + urllib.parse.urlencode(q), headers={"User-Agent": "research-client"})
                d = json.load(urllib.request.urlopen(req, timeout=60))
                break
            except Exception:
                time.sleep(2 + i)
        if d is None:
            break
        out += [m for m in d.get("markets", []) if m.get("mve_selected_legs")]
        cur = d.get("cursor") or ""
        if not cur:
            break
    return out


def same_game(m: dict):
    """(date+teams suffix) when every leg is an NBA market of ONE game, else None."""
    suf = set()
    for l in m["mve_selected_legs"]:
        ev = l["event_ticker"]
        if not ev.startswith("KXNBA"):
            return None
        suf.add(ev.split("-", 1)[1])
    return suf.pop() if len(suf) == 1 else None


def game_draws(fc, suffix: str, n_draws: int):
    """GameDraws for one game from the props engine (team draws) + joint.py (player stats), or None if the roster data is missing."""
    from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import _initial, _norm_surname
    mon = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
    date = f"20{suffix[:2]}-{mon[suffix[2:5]]:02d}-{suffix[5:7]}"
    away, home = suffix[7:10], suffix[10:13]
    p = {"game_date": date, "home": home, "away": away}
    try:
        h, a = fc._game_draws(p)
    except Exception:  # noqa: BLE001  (no history for a team -> unpriced, logged as such)
        return None, None
    seed = int(hashlib.sha256(("combo|" + suffix).encode()).hexdigest()[:8], 16) % 99991
    rng = np.random.default_rng(seed)
    marg = np.abs(np.asarray(h, float) - np.asarray(a, float))
    players = {}
    for side, team, pts, opp, opp_t in (("home", home, h, a, away), ("away", away, a, h, home)):
        ros = fc.roster(team, date)
        if not ros:
            continue
        jr = J.JointRoster(tuple(n for _, n, _ in ros), [m for m, _, _ in ros], {s: [r[2][s] for r in ros] for s in J.STATS}, float(np.mean(pts)))
        d = J.simulate_team(pts, marg, jr, rng, opp_pts=opp, opp_mean_pts=float(np.mean(opp)))
        for i, (_, name, _) in enumerate(ros):
            for stat in J.STATS:
                players[(side, _initial(name) + _norm_surname(name), stat)] = d.stat[stat][:, i]
    return GameDraws(np.asarray(h), np.asarray(a), players), (date, home, away)


def _f(m: dict, k: str) -> float:
    try:
        return float(m.get(k) or 0)
    except (TypeError, ValueError):
        return 0.0


def build_rows(combos: list, draws_for, tip_for, now: datetime, run_id: str) -> list:
    """Pure core (tested). draws_for(suffix) -> GameDraws|None; tip_for(suffix) -> tip datetime|None."""
    rows = []
    for m in combos:
        suf = same_game(m)
        if suf is None:
            continue
        tip = tip_for(suf)
        if tip is None:
            continue
        mins = (tip - now).total_seconds() / 60.0
        if not WINDOW_MIN[0] <= mins <= WINDOW_MIN[1]:
            continue
        bid, ask = _f(m, "yes_bid_dollars"), _f(m, "yes_ask_dollars")
        has_ask = 0 < ask < 1 and _f(m, "yes_ask_size_fp") > 0
        has_bid = bid > 0 and _f(m, "yes_bid_size_fp") > 0
        traded = _f(m, "volume_fp") > 0
        if not (has_ask or has_bid or traded):
            if int(hashlib.sha256(m["ticker"].encode()).hexdigest()[:6], 16) / 0xFFFFFF >= UNQUOTED_SAMPLE:
                continue
        g = draws_for(suf)
        legs = [(l["market_ticker"], l["side"]) for l in m["mve_selected_legs"]]
        r = CP.price_kalshi_combo(g, legs) if g is not None else dict(
            n_legs=len(legs), legs_priced=[], legs_unpriced=[{"ticker": t, "side": s, "reason": "no_game_draws"} for t, s in legs],
            flags=[], n_draws=0, p_all=None, p_priced_subset=None, p_naive=None, lift=None, mc_se=None, resolved=False)
        rows.append(dict(
            run_id=run_id, ts_utc=now.isoformat(), model_id=MODEL_ID, market_ticker=m["ticker"], game=suf, minutes_to_tip=round(mins, 1),
            yes_bid=bid if has_bid else None, yes_ask=ask if has_ask else None, yes_ask_size=_f(m, "yes_ask_size_fp") if has_ask else None,
            last_price=_f(m, "last_price_dollars") or None, volume=_f(m, "volume_fp"), quote_state=("bid" if has_bid else "-") + ("ask" if has_ask else "-"),
            fee_at_ask_default=(fee_default(ask) if has_ask else None), fee_multiplier_verified=False,
            engine_p=r["p_all"], p_priced_subset=r["p_priced_subset"], p_product_of_legs=r["p_naive"], lift=r["lift"], mc_se=r["mc_se"],
            resolved=r["resolved"], n_legs=r["n_legs"], legs_priced=r["legs_priced"], legs_unpriced=r["legs_unpriced"], flags=r["flags"],
            n_draws=r["n_draws"], legs=[{"ticker": t, "side": s} for t, s in legs]))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba_props"))
    ap.add_argument("--out", default=str(ROOT / "exp_output" / "COMBO_SHADOW"))
    ap.add_argument("--no-refresh", action="store_true")
    ap.add_argument("--now")
    ap.add_argument("--draws", type=int, default=4000)
    a = ap.parse_args(argv)
    if not enabled():
        print(json.dumps({"event": "COMBO_SHADOW_OFF", "reason": "PM_COMBO_SHADOW is not on"}))
        return 0
    from run_nba_engine_props_shadow import load_tips, refresh
    from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    raw = Path(a.raw)
    if not a.no_refresh:
        refresh(raw / "box.json", raw / "tips.json", now)
    games, pl = F.parse_box(json.loads((raw / "box.json").read_text()))
    fc = F.NBAEngineProps(games, pl, load_tips(raw / "tips.json"))
    cache: dict = {}

    def draws_for(suf):
        if suf not in cache:
            cache[suf] = game_draws(fc, suf, a.draws)[0]
        return cache[suf]

    def tip_for(suf):
        return fc.kickoff_for_event("KXNBAGAME-" + suf) and fc.kickoff_for_event("KXNBAGAME-" + suf)[0]

    rows = build_rows(fetch_open_combos(), draws_for, tip_for, now, now.strftime("%Y%m%dT%H%M%SZ"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "NBA_SAME_GAME_COMBO.jsonl", "a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"event": "COMBO_SHADOW_RUN", "rows": len(rows), "games": len(cache), "ts": now.isoformat()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
