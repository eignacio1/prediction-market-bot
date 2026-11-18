"""W117.2 (B-099) NHL consensus prior. usage: python3 -I prior_nhl_consensus.py <archive_root>  -> prior_nhl_consensus.json beside this file.
Built like prior_nflverse: per market x favourite-price bin (retro_route FAV_BINS), gap = E[favourite side wins] - devigged
consensus close, with its standard error (games independent). Net of riding the favourite at the consensus close = gap (fair price,
no fee); net of fading it = -gap. Regular season only; playoffs are reported in the file apart and never enter the bins the router reads.
The Kalshi transfer allowance (TRANSFER_SD) is applied by the runner, not here."""
import json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.archive_intake import closing_lines as cl  # noqa: E402

EDGES = (0.35, 0.5, 0.65, 0.8)


def legs(g):
    """-> [(family, p_yes_side, y)] with p the devigged consensus close prob of a side and y whether it won (pushes dropped)."""
    out = []
    if g["close_home_win_prob"] is not None:
        out.append(("NHL_MONEYLINE", g["close_home_win_prob"], 1.0 if g["moneyline_winner"] == "home" else 0.0))
    if g["close_home_cover_prob"] is not None and g["ats_result"] in ("home", "away"):
        out.append(("NHL_PUCK_LINE", g["close_home_cover_prob"], 1.0 if g["ats_result"] == "home" else 0.0))
    if g["close_over_prob"] is not None and g["total_result"] in ("over", "under"):
        out.append(("NHL_GAME_TOTAL", g["close_over_prob"], 1.0 if g["total_result"] == "over" else 0.0))
    return out


def bins(games):
    acc = defaultdict(list)
    for g in games:
        for mt, p, y in legs(g):
            pf, yf = (p, y) if p >= 0.5 else (1 - p, 1 - y)
            acc[(mt, sum(pf >= e for e in EDGES))].append(yf - pf)
    out = {}
    for (mt, b), xs in sorted(acc.items()):
        n = len(xs); m = sum(xs) / n
        se = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1) / n) if n > 1 else None
        out[f"{mt}|{b}"] = {"n": n, "gap": round(m, 5), "se": round(se, 5) if se else None,
                            "ride_net": round(m, 5), "fade_net": round(-m, 5)}
    return out


def main(root):
    d = cl.load_nhl_closing(root)
    doc = {"source": "Muse archive L3-closing-lines/nhl/minmaxxxer-2025-26 @ " + cl.PINNED_SHA, "terms": cl.TERMS,
           "season": "2025-26 regular season", "transfer_sd_note": "0.03 applied by the runner, as for nflverse",
           "bins": bins(d["regular"]), "playoffs_descriptive_only": bins(d["postseason"])}
    safe_out(os.path.join(HERE, "prior_nhl_consensus.json")).write_text(json.dumps(doc, indent=1))
    print(json.dumps(doc["bins"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
