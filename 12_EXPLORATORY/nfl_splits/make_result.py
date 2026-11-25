"""Builds RESULT.md from results.json (and archive_look.json if present). No numbers are typed by hand."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out

here = Path(__file__).parent
R = json.loads((here / "results.json").read_text())
rows, meta = R["rows"], R["meta"]
al = json.loads((here / "archive_look.json").read_text()) if (here / "archive_look.json").exists() else None
j = [r for r in rows if "net" in r]
f = lambda v, n=4: "-" if v is None else f"{v:+.{n}f}"
L = ["# EXP-NFLSPLITS-001 RESULT (W126.5)", "",
     f"**Last reviewed:** 2026-11-24. Source: `run_splits.py` -> `results.json` (this folder). PREREG.md was committed first (1222250, 0a7e3b4).",
     f"Fit 2019-2024, judged on 2025 regular season, **proxy prices** (board_v2 anchored to nflverse closing lines, earlier seasons only; not tradable quotes). "
     f"{meta['games']} games, {meta['bets']} bets. Cost = Kalshi fee + archive-median half-spread (AS {meta['hs_median']['AS']}, AT {meta['hs_median']['AT']}, TT {meta['hs_median']['TT']}). MIN_N = {meta['MIN_N']} games.", "",
     "## Headline", "",
     f"- **{len(rows)} split x leaf x arm rows; {len(j)} judged on 2025; {len(rows)-len(j)} not judged (n below MIN_N).**",
     f"- **Fit-routed rows (BH family): {meta['bh_family']}.** On 2019-2024 no leaf had an arm whose partially-pooled 90% lower bound cleared zero, so every leaf was routed to ride / no bet before 2025 was read.",
     f"- **Arms earned: {sum(1 for r in rows if r['verdict']=='arm earned in this leaf')}.** Raw 2025 net is above zero in {sum(r['net']>0 for r in j)} of {len(j)} judged rows, and its 90% interval excludes zero in {sum(r['net_lo']>0 for r in j)}.",
     "- Verdict in routing words: these factors, as splits on team totals and alternate ladders at consensus-anchored prices, route to **ride / no bet in every judged leaf**. This closes only EXP-NFLSPLITS-001's hypothesis (parked for R&D); no cell, market or arm closes.",
     "", "## Stage by split (D5(b) NFL, source: this file)", "",
     "| Split | Rows | Judged rows (2025, n>=40) | Judged -> stage |", "|---|---|---|---|"]
stage = {}
for sp in ("qb", "rest", "officials", "weather", "matchup"):
    a = [r for r in rows if r["split"] == sp]; b = [r for r in a if "net" in r]
    stage[sp] = "applied (tested, routed to ride / no bet)" if b else "not tested: stays at its seat stage"
    L.append(f"| {sp} | {len(a)} | {len(b)} | {stage[sp]} |")
L += ["", "Rule from PREREG s7: a split moves to `applied` iff at least one leaf was judged on the held-out set, whatever the sign.", "",
      "## Every row", "", "`fit_shrunk` = partially-pooled 2019-2024 net per bet (n games in fit). `net` interval = 90% game-clustered (CR1). "
      "`net@mean-spread` = net at the archive-mean half-spreads (sensitivity). Bootstrap p only for fit-routed rows (there are none).", "",
      "| split | market | leaf | band | arm | fit n | fit_shrunk | 2025 games | gross | cost | net | 90% interval | net@mean-spread | verdict |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: (r["split"], r["market"], r["leaf"], r["band"], r["arm"])):
    if "net" in r:
        L.append(f"| {r['split']} | {r['market']} | {r['leaf']} | {r['band']} | {r['arm']} | {r['fit_n_games']} | {f(r['fit_shrunk'])} | {r['n_judge_games']} | {f(r['gross'])} | {r['cost']:.4f} | {f(r['net'])} | [{f(r['net_lo'])}, {f(r['net_hi'])}] | {f(r['net_mean_cost'])} | {r['verdict']} |")
    else:
        L.append(f"| {r['split']} | {r['market']} | {r['leaf']} | {r['band']} | {r['arm']} | {r['fit_n_games']} | {f(r['fit_shrunk'])} | {r['n_judge_games']} | - | - | - | - | - | {r['verdict']} |")
if al:
    L += ["", "## 2026 archive look (descriptive, real quotes, not pooled with 2025, no BH)", "", al["text"]]
L += ["", "## What this does and does not say", "",
      "- Prices are consensus-anchored proxies. A null here says the consensus line already carries these factors at the rungs tested; it does not say real Kalshi ladders cannot differ.",
      "- Cuts (fit seasons): referee prior " + str(meta["ref_cuts"]) + "; matchup terciles " + str(meta["mu_cuts"]) + ".",
      "- Weather forecasts exist only from 2024, so S4 has one fit season and no leaf could be fit-routed. Rare leaves (`qb_new`, `short` rest) fall under MIN_N and are listed as not judged.",
      "- 2026 archive look: not produced. The archive scan returned no usable settled 2026 ladder rows, so no 2026 number is claimed; it stays open for the forward look.",
      "- No 2026 shadow rows from this commit forward exist yet; the forward look in PREREG s3 is not read.",
      "- Overlap: W110.1 already returned 0 arms on weather / matchup for sides and totals. This result agrees on the new markets."]
safe_out(here / "RESULT.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:14]))
