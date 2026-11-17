"""W115.1 long-history prior. usage: python3 -I prior_nflverse.py <games.csv> -> prior_nflverse.json beside this file.
Free nflverse closing lines (moneyline, main spread, main total; odds start in 2006). Seasons before 2026 only: the 2026
season overlaps our own rows. Output per market and favourite-price bin (retro_route FAV_BINS): the calibration gap
E[favourite side wins] - devigged closing probability, with its standard error (games independent)."""
import csv, json, math, os, sys
from collections import defaultdict

EDGES = (0.35, 0.5, 0.65, 0.8)
HERE = os.path.dirname(os.path.abspath(__file__))


def imp(o):
    o = float(o)
    return -o / (-o + 100.0) if o < 0 else 100.0 / (o + 100.0)


def main(path):
    acc = defaultdict(list)
    seasons = set()
    with open(path, newline="") as fh:
        for g in csv.DictReader(fh):
            try:
                season = int(g["season"]); res = float(g["result"]); tot = float(g["total"])
            except (ValueError, KeyError):
                continue
            if season >= 2026:
                continue
            legs = []
            try:
                legs.append(("NFL_MONEYLINE", imp(g["home_moneyline"]), imp(g["away_moneyline"]), None if res == 0 else res > 0))
            except ValueError:
                pass
            try:
                sl = float(g["spread_line"])
                legs.append(("NFL_SPREAD", imp(g["home_spread_odds"]), imp(g["away_spread_odds"]), None if res == sl else res > sl))
            except ValueError:
                pass
            try:
                tl = float(g["total_line"])
                legs.append(("NFL_GAME_TOTAL", imp(g["over_odds"]), imp(g["under_odds"]), None if tot == tl else tot > tl))
            except ValueError:
                pass
            for mt, a, b, won in legs:
                if won is None or a + b <= 0:
                    continue
                p = a / (a + b)
                pf, y = (p, 1.0 if won else 0.0) if p >= 0.5 else (1 - p, 0.0 if won else 1.0)
                acc[(mt, sum(pf >= e for e in EDGES))].append(y - pf)
                seasons.add(season)
    out = {"source": "nflverse games.csv (free)", "seasons": [min(seasons), max(seasons)], "bins": {}}
    for (mt, b), xs in sorted(acc.items()):
        n = len(xs); m = sum(xs) / n
        se = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1) / n) if n > 1 else None
        out["bins"][f"{mt}|{b}"] = {"n": n, "gap": round(m, 5), "se": round(se, 5) if se else None}
    with open(os.path.join(HERE, "prior_nflverse.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
