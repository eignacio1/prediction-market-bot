#!/usr/bin/env python3
"""W124.1 power ledger: for every open hypothesis, when does it become judgeable, and which variance tool shortens it most.

Usage: power_ledger.py --out power_ledger.json [--md POWER_LEDGER.md] [--meas variance_measurements.json] [--asof 2026-11-23]
Re-runnable by the weekly evidence look. READ-ONLY on its inputs; no box change; no settlement read of any held-out third.

Convention: sd_game = sd of per-game means (already carries the design effect). From a published 90% interval:
sd_game = ((hi-lo)/(2*1.645)) * sqrt(games). n needed = games_needed(sd_game, 1, 0, effect=one round cost) at 80% power, one-sided 5%.
The binding n is the larger of that and the pre-registered minimum n. Rows with a fit/judged split (H1 style, 2/3 fit by date) need
fit_mult x the judged n in total games. A proxy input is labelled proxy. A row whose input is not on disk is measured:false, never guessed.
"""
import argparse, json, math, os, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prediction_market_bot.quant import variance as V  # noqa: E402

Z90 = 1.6448536269514722
SEASON = {  # (end, next start): calendar facts used only to flag that a date falls out of season
    "NFL": (date(2027, 2, 14), date(2027, 9, 9)), "NBA": (date(2027, 6, 20), date(2027, 10, 19)),
    "NHL": (date(2027, 6, 20), date(2027, 10, 7)), "MLB": (None, None)}


def sdg(lo, hi, games):
    return (hi - lo) / (2 * Z90) * math.sqrt(games)


def project(asof, n_now, need, yield_wk, sport):
    """Date n reaches `need`. Returns (iso|None, note)."""
    if need <= n_now:
        return asof.isoformat(), "reached"
    if not yield_wk or yield_wk <= 0:
        return None, "yield 0 per week"
    wk = (need - n_now) / yield_wk
    if wk > 104:
        return None, f"{wk:.0f} weeks at the current yield (> 2 years): not judgeable on this outcome"
    d = asof + timedelta(days=round(wk * 7))
    end, nxt = SEASON.get(sport, (None, None))
    if end and d > end:
        weeks_left = max(0.0, (end - asof).days / 7)
        rem = need - (n_now + yield_wk * weeks_left)
        d2 = nxt + timedelta(days=round(rem / yield_wk * 7))
        return d2.isoformat(), f"in-season rate reaches it after the {sport} season ends {end}; resumes {nxt} (opening day + {rem / yield_wk:.1f} wk)"
    return d.isoformat(), "in season"


def rows_spec(m):
    fam = m["by_family"]
    prop_sd = 0.0151 * math.sqrt(57)  # MLB|prop_hit se 0.0151, 57 judged games (h1 results.json)
    exec_sd = sdg(-0.016, 0.348, 20)                                  # H-EXEC-2 published interval, 20 games
    return [
        dict(id="H-EDGE-1 NBA props", status="UNDERPOWERED", unit="games (per family)", n_now=14, sd=prop_sd, sd_src="PROXY: MLB|prop_hit se 0.0151 x sqrt(57 judged games), h1_attention/results.json; no prop family has a judged row",
             cost=0.0322, cost_src="PROXY: MLB|prop_hit round_cost, same file", floor=30, fit_mult=3, yield_wk=23.5, yield_src="archive KXNBAPTS events/week, last 28 d (upper bound; pre-start capture of props not verified)", sport="NBA", clv=None, pooled=True),
        dict(id="H-EDGE-1 NFL props", status="UNDERPOWERED", unit="games (per family)", n_now=15, sd=prop_sd, sd_src="PROXY: as above", cost=0.0322, cost_src="PROXY: as above", floor=30, fit_mult=3,
             yield_wk=6.5, yield_src="archive KXNFLPASSYDS events/week, last 28 d", sport="NFL", clv=None, pooled=True),
        dict(id="H-EDGE-3 NBA lineup confirmations", status="UNDERPOWERED", unit="events", n_now=6, sd=sdg(-0.0042, 0.0100, 6), sd_src="h3_news/RESULT.md: +0.25c [-0.42, 1.00], n 6",
             cost=0.0210, cost_src="h3_news/RESULT.md round cost 2.10c", floor=30, fit_mult=1, yield_wk=4.2, yield_src="h3_news/RESULT.md: 6 events per 10 days", sport="NBA", clv=None, pooled=False),
        dict(id="H-EDGE-3 NFL inactives", status="UNDERPOWERED", unit="games", n_now=14, sd=sdg(0.0, 0.0029, 14), sd_src="h3_news/RESULT.md: +0.14c [0.00, 0.29], n 14",
             cost=0.0200, cost_src="h3_news/RESULT.md round cost 2.00c", floor=30, fit_mult=1, yield_wk=14.0, yield_src="one Sunday slate per week IF every game's inactives are captured (12 of 14 on 11-15, 1 on other days)", sport="NFL", clv=None, pooled=False),
        dict(id="H-EDGE-4 frozen 15-min quoting rule", status="UNDERPOWERED", unit="games", n_now=0, sd=exec_sd, sd_src="PROXY: H-EXEC-2 arm-order interval",
             cost=0.022, cost_src="archive NBA/NHL spread round cost at R", floor=20, fit_mult=1, yield_wk=0.0, yield_src="0 simulated fills at the frozen rule (h4_execution/RESULT.md)", sport="NBA", clv="GAME", pooled=False),
        dict(id="H-EXEC-2 FADE crossing the spread", status="UNDERPOWERED", unit="games", n_now=20, sd=exec_sd, sd_src="doctrine Part II: +0.166 [-0.016, +0.348], 20 games",
             cost=0.022, cost_src="archive NBA/NHL spread/game round cost at R", floor=30, fit_mult=1, yield_wk=20 / (17 / 7), yield_src="20 games since the 2026-11-06 epoch (17 days)", sport="NBA", clv="GAME", pooled=False),
        dict(id="EXP-W119.3 FADE one tick inside", status="COLLECTING", unit="resolved orders", n_now=17, sd=None, sd_src="n/a: outcome is a fill rate; the pre-registration judges at n only",
             cost=None, cost_src="n/a", floor=100, fit_mult=1, yield_wk=17 / (17 / 7), yield_src="17 inside orders since the 2026-11-06 epoch (doctrine: inside 2 / 17)", sport="NBA", clv=None, pooled=False),
        dict(id="H-DEPTH-NBA-S1/S2/S4 (best leaf)", status="COLLECTING", unit="games (per leaf)", n_now=16, sd=sdg(0.048, 0.155, 16), sd_src="PROXY: spread of best leaf (+0.155, lower +0.048, 16 games) read as a 90% interval",
             cost=0.021, cost_src="archive NBASPREAD round cost at R", floor=30, fit_mult=1, yield_wk=16 / (13 / 7), yield_src="16 games since snapshots began 11-10 (13 days) for that leaf", sport="NBA", clv="SPREAD", pooled=True),
    ]


def build(asof, meas):
    fam = meas["by_family"]; cv_vr = meas["control_variate"]["variance_reduction"]; pr_vr = meas["paired_game_vs_spread"]["variance_reduction"]
    pr = [c["post_se"] / c["raw_se"] for c in meas["partial_pool_by_series"]["cells"] if c["raw_se"] > 0]
    pr.sort(); pool_ratio = pr[len(pr) // 2]
    out = []
    for r in rows_spec(meas):
        o = dict(id=r["id"], status=r["status"], unit=r["unit"], n_now=r["n_now"], yield_per_week=round(r["yield_wk"], 2), yield_src=r["yield_src"], inputs_src=[r["sd_src"], r["cost_src"]])
        if r["sd"] is None or r["cost"] is None:
            need = r["floor"] * r["fit_mult"]
            o.update(measured=True, sd_settle=None, cost=None, mde_now=None, n_needed_mde=None, binding="minimum n (pre-registered); no outcome sd applies", n_needed=need)
        else:
            nm = V.games_needed(r["sd"], 1, 0.0, r["cost"])
            need = max(math.ceil(nm), r["floor"]) * r["fit_mult"]
            o.update(measured=True, sd_settle=round(r["sd"], 4), cost=r["cost"], mde_now=(round(V.mde_clustered(r["sd"], r["n_now"], 1, 0.0), 4) if r["n_now"] > 0 else None),
                     n_needed_mde=math.ceil(nm), binding=("effect size" if nm > r["floor"] else "minimum n"), n_needed=need)
        o["icc_clv"] = round(fam[r["clv"]]["icc"], 3) if r["clv"] else None
        o["sd_clv"] = round(fam[r["clv"]]["clv_sd"], 4) if r["clv"] else None
        d, note = project(asof, r["n_now"], need, r["yield_wk"], r["sport"]); o["judgeable"] = d; o["judgeable_note"] = note
        # tools: measured saving in games needed (judged), each reported separately; the largest is named
        tools = {}
        if r["sd"] is not None and r["cost"] is not None:
            base = o["n_needed"]
            if r["clv"]:
                nc = max(math.ceil(V.games_needed(fam[r["clv"]]["clv_sd"], 1, fam[r["clv"]]["icc"], r["cost"])), r["floor"]) * r["fit_mult"]
                tools["clv_outcome"] = dict(n_needed=nc, saves=base - nc, date=project(asof, r["n_now"], nc, r["yield_wk"], r["sport"])[0],
                                            caveat="only where H-MEAS-1 (W124.2) licenses CLV; R here is the game-morning line, not the close")
            tools["control_variate"] = dict(n_needed=math.ceil(base * (1 - cv_vr)), saves=base - math.ceil(base * (1 - cv_vr)),
                                            date=project(asof, r["n_now"], math.ceil(base * (1 - cv_vr)), r["yield_wk"], r["sport"])[0], caveat=f"variance reduction {cv_vr:.3f} measured on archive CLV; not transferred to settlement")
            tools["paired_within_cluster"] = dict(n_needed=math.ceil(base * (1 - pr_vr)), saves=base - math.ceil(base * (1 - pr_vr)),
                                                  date=project(asof, r["n_now"], math.ceil(base * (1 - pr_vr)), r["yield_wk"], r["sport"])[0], caveat=f"variance reduction {pr_vr:.4f} measured on GAME-vs-SPREAD CLV; applies only to arm-vs-rule pairs on one game")
            if r["pooled"]:
                nq = math.ceil(base * pool_ratio ** 2)
                tools["partial_pool"] = dict(n_needed=nq, saves=base - nq, date=project(asof, r["n_now"], nq, r["yield_wk"], r["sport"])[0], caveat=f"median post_se/raw_se {pool_ratio:.3f} over 8 archive series cells (tau {meas['partial_pool_by_series']['tau']:.4f}); shrinks the per-cell interval, not the pooled estimate")
        o["tools"] = tools
        best = max(tools.items(), key=lambda kv: kv[1]["saves"]) if tools else None
        o["best_tool"] = None if not best or best[1]["saves"] <= 0 else dict(tool=best[0], **best[1])
        o["dated_by"] = "computation"
        o["judgeable_with_best_tool"] = o["best_tool"]["date"] if o["best_tool"] else None
        out.append(o)
    cited = [  # already dated in a source file; ISO dates are quoted, not computed
        dict(id="EXP-045 NFL engine forward", judgeable="2027-01-12", dated_by="cited: doctrine Part II (reads 01-12)", status="COLLECTING"),
        dict(id="EXP-044/044b/044c NBA engine blend test", judgeable="2027-02-15", dated_by="cited: doctrine Part II (blend test 12-29 .. 02-15)", status="COLLECTING"),
        dict(id="H-DEPTH-PAM-3 trait stability", judgeable=asof.isoformat(), dated_by="cited: PREREG.md retrospective on stored 2023-25 seasons; a build, not a wait", status="PRE-REGISTERED"),
        dict(id="MLB-2027 (42 cells)", judgeable=None, dated_by="cited: PREREG_2027 power calendar, weeks after opening day (+0.04: totals 2-3, run line 6, moneyline ~34); opening-day date not in the repo", status="PRE-REGISTERED"),
    ]
    undated = [
        dict(id="H-ROUTER-2", reason="next look 2026-11-24 is a look, not a judgeable date; per-leaf n and sd are not on disk offline"),
        dict(id="EXP-W117.1", reason="table has 0 cells, so yield per cell is not observable yet"),
        dict(id="H-DEPTH-NBA-S3 / S5", reason="waits on lineup / ref history backfill; no n to project"),
        dict(id="H-DEPTH-NHL-1", reason="unit of the 42 held-out items not stated in the doctrine row; no sd on disk"),
        dict(id="EXP-NBAPROPS-001", reason="unit is leaves (143), settled props per leaf not observable offline"),
        dict(id="H-DEPTH-NFL-1", reason="recount after 11-22/23 is a recount date, not a judgeable date"),
    ]
    dated = [x for x in out if x["judgeable"]] + [x for x in cited if x["judgeable"]]
    with_tool = [x for x in out if not x["judgeable"] and x["judgeable_with_best_tool"]]
    return dict(asof=asof.isoformat(), rule="n needed = games_needed(sd_game,1,0,one round cost), 80% power, one-sided 5%; binding = max(that, minimum n) x fit_mult",
                caveats=["R is the game-morning 15:00Z line, not the close: every CLV figure is descriptive until H-MEAS-1",
                         "settlement sd values are proxies where marked; they come from published intervals, not from re-reading the W123 held-out third",
                         "a tighter interval is not an edge: the ledger dates when a test can judge, not what it will find"],
                rows=out, cited=cited, undated=undated,
                p3=dict(covered=len(out) + len(cited) + len(undated), dated_before=2, dated_after=len(dated), dated_only_with_licensed_tool=[x["id"] for x in with_tool], source="power_ledger.json; before = rows already carrying an ISO judgeable date in doctrine Part II (EXP-044, EXP-045)"))


def md(led, meas):
    L = [f"# Power ledger ({led['asof']})", "", "Generated by `power_ledger.py`; re-run weekly. " + led["rule"], ""]
    L += ["| Hypothesis | Unit | n now | sd (settle) | cost | n needed (binding) | /wk | Judgeable | Best tool (saves) |", "|---|---|---|---|---|---|---|---|---|"]
    for r in led["rows"]:
        bt = r["best_tool"]; bts = f"{bt['tool']} ({bt['saves']})" if bt else "none"
        L.append(f"| {r['id']} | {r['unit']} | {r['n_now']} | {r['sd_settle']} | {r['cost']} | {r['n_needed']} ({r['binding']}) | {r['yield_per_week']} | {r['judgeable'] or 'none: ' + r['judgeable_note']}{' (with ' + bt['tool'] + ': ' + str(r['judgeable_with_best_tool']) + ')' if bt and not r['judgeable'] and r['judgeable_with_best_tool'] else ''} | {bts} |")
    L += ["", "## Already dated elsewhere", ""] + [f"- {c['id']}: {c['judgeable'] or 'relative to opening day'} ({c['dated_by']})" for c in led["cited"]]
    L += ["", "## Not datable offline (stated, not guessed)", ""] + [f"- {u['id']}: {u['reason']}" for u in led["undated"]]
    L += ["", "## Notes", ""] + [f"- {c}" for c in led["caveats"]]
    g, c, cv, pp, pd_, de = meas["clv"]["gross"], meas["clv"]["net"], meas["control_variate"], meas["partial_pool_by_series"], meas["paired_game_vs_spread"], meas["design_effect"]
    L += ["", "## RESULT (W124.1)", "",
          f"Archive proxy, {meas['rows']} favourite-side rows, {meas['games']} games, entry gd-1 15:00Z, reference = game-morning 15:00Z line (not the close). Descriptive; pre-H-MEAS-1.",
          f"- **CLV, gross / cost / net side by side:** gross {g['mean']:+.4f} [{g['lo']:+.4f}, {g['hi']:+.4f}] per contract; round cost {meas['clv']['cost_mean']:.4f}; net {c['mean']:+.4f} [{c['lo']:+.4f}, {c['hi']:+.4f}]. A tighter interval is not an edge: net is negative.",
          f"- **design_effect:** icc {de['icc']:.3f}, deff {de['deff']:.2f}, {de['n_games']} games x {de['rows_per_game']:.1f} rows -> {de['n_eff_rows']:.0f} effective rows; CLV sd {de['clv_sd']:.4f}. Applies where several lines share a game; does not apply to one-row-per-game outcomes.",
          f"- **control_variate (pre-entry move):** theta {cv['theta']:+.3f} fit through {cv['fit_through']} only; judged {cv['n_judged']} rows / {cv['adjusted']['n_clusters']} games; variance reduction {cv['variance_reduction']:.3f}; interval width {cv['raw']['hi']-cv['raw']['lo']:.4f} -> {cv['adjusted']['hi']-cv['adjusted']['lo']:.4f}. Small: the pre-entry move explains little of the later move.",
          f"- **paired_within_cluster (GAME vs SPREAD CLV, same game):** diff {pd_['mean_diff']:+.4f} [{pd_['lo']:+.4f}, {pd_['hi']:+.4f}], {pd_['n_games']} games; variance reduction {pd_['variance_reduction']:.4f}. Pairing helps only when two arms share a game effect; these two do not.",
          f"- **partial_pool (8 series cells):** mu {pp['mu']:+.4f}, tau {pp['tau']:.4f}, I2 {pp['i2']:.2f}: cells are heterogeneous, so shrinkage is light (median B small). Applies to many small leaves; does not rescue one underpowered cell.",
          "- **clv (own side):** known-answer tests cover both sides; measured above.",
          "- **Largest measured shortening:** swapping settlement for CLV where a price path exists (H-EXEC-2: 3,128 games -> 30 by the minimum-n rule; NBA depth best leaf: 238 -> 208 games, floor 30). It is conditional on H-MEAS-1 licensing CLV; until then those dates are conditional, not earned.",
          "- **Not measured here (stated):** props and NFL have no 15:00Z game-day snapshot in this window, so no CLV path or ICC was measured for them; EXP-W117.1, H-ROUTER-2, NBA S3/S5, NHL-1, EXP-NBAPROPS-001 and NFL-1 are listed undated with the reason."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--md")
    ap.add_argument("--meas", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "variance_measurements.json")); ap.add_argument("--asof", default="2026-11-23")
    a = ap.parse_args(); meas = json.load(open(a.meas)); led = build(date.fromisoformat(a.asof), meas)
    json.dump(led, open(a.out, "w"), indent=1)
    if a.md:
        open(a.md, "w").write(md(led, meas))
    print(json.dumps(led["p3"]))


if __name__ == "__main__":
    main()
