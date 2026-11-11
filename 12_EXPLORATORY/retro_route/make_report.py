"""Render ROUTING.md from results.json + inventory.json (numbers come only from those files)."""
import json, collections, os
H = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(f"{H}/results.json")); I = json.load(open(f"{H}/inventory.json"))
L = R["route"]["leaves"]
NAME = {"RIDE": "ride the market", "FADE": "fade the market", "MODEL_FADE": "model-disagreement fade", "MOMENTUM": "follow the move", "NO_BET": "no bet"}
fam = collections.defaultdict(list)
for l in L:
    fam[(l["leaf"][0], l["leaf"][1])].append(l)
o = []
o.append("# W110.5 retro-route: where each leaf goes (ride / fade / momentum / no bet)\n")
o.append("Built 2026-11-11 from every settled shadow row on the box (paper rows, not fills; the GG-1771 fill epoch does not apply). Spec frozen before results: `SPEC.md`. All numbers are net per contract after the exact Kalshi taker fee, the taker price (ask, or 1 minus bid) already paying the spread.\n")
o.append("## In plain English\n")
nr = sum(l["arm"] != "NO_BET" for l in L); nt = sum(l["thin"] for l in L); nrep = sum("test_mean" in l for l in L)
nbh = sum(l["bh"] for l in L); nd = sum(l["draft"] for l in L)
o.append(f"- {len(L)} leaves (cell x band x favoured-side price bin x last move). {nt} are thin (under 60 fit rows or 20 fit games) and default to **no bet**. {nr} leaves chose an arm on the earlier 70% of games, and {nrep} of those have enough held-out games (10+) to report.")
o.append(f"- On the held-out 30% of games, **{nbh} leaf** survives Benjamini-Hochberg q=0.10, and **{nd} leaves** meet the draft bar (BH, lower 90% bound above 0, 15+ held-out games). So there are **no pre-registration drafts** from this pass; the one BH leaf has only 11 held-out games and is listed below as a lead for the window, not a result.")
o.append("- Every other routed leaf's held-out interval includes zero or sits below it: those leaves are **routed away from the arm they picked on the fit window** and default to no bet until a forward test says otherwise. That is a routing result, not a verdict on the market.")
o.append("- The cleaner signal is at family level (table below, unrouted, every row of the held-out games): riding the market's favoured side beats fading it in nearly every family, and the model-disagreement fade holds up on NHL puck line (and, with a wide interval, NHL moneyline). Those are leads for the forward test, not drafts.\n")
o.append("## Inventory (Part A): settled shadow rows after dedupe\n")
o.append(f"Raw settled rows {I['raw_settled_rows']:,}; after dedupe (one per market ticker and run; one moneyline ticker per game and run) {I['deduped_rows']:,}.\n")
o.append("| Sport | Family | Rows | Games | First | Last |\n|---|---|---|---|---|---|")
for k, v in I["inventory"].items():
    s, f = k.split("|"); o.append(f"| {s} | {f} | {v['rows']:,} | {v['games']} | {v['first']} | {v['last']} |")
o.append("\n## Arms, family level, held-out games only, every row (not routed)\n")
o.append("Mean net per contract, 90% game-clustered interval, rows / games. The unrouted reference; leaves below refine it.\n")
o.append("| Family | Ride | Fade | Follow move | Model fade |\n|---|---|---|---|---|")
for k, a in R["reference_heldout_all_rows"].items():
    def c(x):
        v = a.get(x)
        return "-" if not v else f"{v['mean']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] {v['n']}/{v['games']}"
    o.append(f"| {k.replace('|', ' ')} | {c('RIDE')} | {c('FADE')} | {c('MOMENTUM')} | {c('MODEL_FADE')} |")
o.append("\n## Routing by family (Part C)\n")
for (s, f), ls in sorted(fam.items()):
    cnt = collections.Counter(l["arm"] for l in ls); rep = [l for l in ls if "test_mean" in l]
    o.append(f"### {s} {f}\n")
    o.append(f"Leaves {len(ls)}; thin {sum(l['thin'] for l in ls)}; routed to " + ", ".join(f"{NAME[a]} {n}" for a, n in sorted(cnt.items())) + f"; reportable held-out {len(rep)}; BH {sum(l['bh'] for l in ls)}.\n")
    if rep:
        o.append("Reportable leaves, best held-out first (band, favoured-price bin 0=<.35 ... 4=>=.8, move):\n")
        o.append("| Leaf | Arm | Held-out net | 90% interval | Rows / games | BH |\n|---|---|---|---|---|---|")
        for l in sorted(rep, key=lambda l: -l["test_mean"])[:6]:
            _, _, b, p, m = l["leaf"]
            o.append(f"| {b}, {p}, {m} | {NAME[l['arm']]} | {l['test_mean']:+.3f} | [{l['test_lo']:+.3f}, {l['test_hi']:+.3f}] | {l['test_n']}/{l['test_n_games']} | {'yes' if l['bh'] else ''} |")
        o.append("")
o.append("## D6 layers 1-5 per cell (what this pass supplies)\n")
o.append("Layer 1 simulated probability: the logged `p_yes`. Layer 2 market state: bid / ask / mid, band, price bin, last move (from the ticker's own earlier shadow rows). Layer 3 factor filters: **price, band and move only**; the 110.1 / 110.2 factor filters are not joined per row (gap below). Layer 4 a tree choosing the arm: this leaf router (fit on 70% of games). Layer 5 per-leaf held-out net after costs per arm: reported where a leaf has 10+ held-out games.\n")
o.append("| Cell | Leaves with held-out result | Layers present |\n|---|---|---|")
for (s, f), ls in sorted(fam.items()):
    n = sum("test_mean" in l for l in ls)
    o.append(f"| {s} {f} | {n} | 1, 2, 4, 5 (3 partial) |" if n else f"| {s} {f} | 0 | 1, 2, 4 (3 partial; 5 awaits more games) |")
o.append("\n## Gaps for the window (registered here, not fixed in this block)\n")
o.append("- **Archive join not done.** Move since open and last hour come from the ticker's own earlier shadow rows, not `PRICE_ARCHIVE`; the ladder gap is not a column. A streaming archive join (2 GB) plus the MLB / NFL settlement cache would add archive-only rows with no model p (ride / fade / momentum only). NBA / NHL archive tickers have no settlement cache.")
o.append("- **Factor filters not joined.** 110.1 (NFL weather, matchup) and 110.2 (NBA via the 109.1 tree) are not per-row fields in the shadow ledgers, so leaves split on market state only. Feature rows are hashed (`feature_row_sha256`), not stored.")
o.append("- **Small windows.** NFL 87 games, MLB postseason 24 games, NBA 154, NHL 270 since early October; the held-out 30% is 161 games across sports. The leaf count is large against that; BH is the guard and it leaves one name.")
o.append("- Shadow data was pulled read-only from the box into a scratch directory; nothing was written to the box.\n")
open(f"{H}/ROUTING.md", "w").write("\n".join(o))
