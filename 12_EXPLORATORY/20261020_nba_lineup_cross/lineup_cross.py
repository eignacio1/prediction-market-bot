"""EXPLORATORY (W81.2 Part A) -- NBA lineup cross, index parts 1-3. Not a verdict (CHARTER rule 6).

PRE-REGISTERED RULES (written before any result was read):
* Data: NBA event store player_box/team_box/schedule, seasons 2016-2025 (ending year), regular season only
  (season_type_id == 2). Nothing from 2026 is read. Read-only.
* Absence A: a player whose box row is a DNP with an Injury/Illness comment in game G, who in the team's
  games BEFORE G (strictly earlier) was a rotation player: average minutes over his last 10 played games >= 20,
  last played within the team's previous 10 games.
* Role of A, from pre-G data only: 'creator' = highest trailing FGA/game on the team among rotation players;
  'starter' = top-5 trailing minutes excluding creator; 'rotation' = other rotation player.
* Single-absence design: only team-games with exactly one rotation absentee (injury) are "absence" games;
  team-games with zero rotation absentees (any DNP kind) are "clean" controls.
* Absorber B: played in G, rotation player by the same test, B != A. Effect = actual - B's trailing-10 mean
  (pre-G) for points, minutes, FGA. Net uplift = mean effect(absence) - mean effect(clean), by role of A.
* Stability: pair (B, A, team-season) with >= 3 absence games; odd/even split-half Spearman; and year-to-year
  correlation of B's mean uplift under 'creator' absence across consecutive seasons (same B, >=3 games each).
* Matchup cross: opponent trailing-30 points allowed per game, and opponent trailing-30 possessions proxy
  (FGA+0.44*FTA-OREB+TOV) per game; terciles are cut over all team-games of the same season using
  pre-G values only. Reported: net uplift by tercile; frequency of each absence role.
* Bootstrap CI: B=2000, seed 20261020, resampling games.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402

RAW = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path("exp_output/NBA_EVENTS/raw")
SEASONS = range(2016, 2026)
OUT = Path(__file__).resolve().parent


def mins(x):
    if not isinstance(x, str) or ":" not in x:
        return 0.0
    m, s = x.split(":")[:2]
    try:
        return int(m) + int(s) / 60.0
    except ValueError:
        return 0.0


def load():
    pb, tb, sc = [], [], []
    for s in SEASONS:
        pb.append(pd.read_parquet(RAW / f"player_box/player_box_{s}.parquet"))
        tb.append(pd.read_parquet(RAW / f"team_box/team_box_{s}.parquet"))
        sc.append(pd.read_parquet(RAW / f"schedule/schedule_{s}.parquet"))
    pb, tb, sc = pd.concat(pb), pd.concat(tb), pd.concat(sc)
    pb = pb[pb.season_type_id.astype(str) == "2"].copy()
    tb = tb[tb.season_type_id.astype(str) == "2"].copy()
    sc = sc[["game_id", "game_date"]].drop_duplicates("game_id")
    pb = pb.merge(sc, on="game_id", how="left")
    tb = tb.merge(sc, on="game_id", how="left")
    pb["min"] = pb["minutes"].map(mins)
    pb["played"] = pb["min"] > 0
    pb["inj_dnp"] = (~pb["played"]) & pb["comment"].fillna("").str.contains("Injury|Illness", case=False)
    return pb, tb


def team_games(pb, tb):
    """One row per (team, game) in time order with a per-team-season game index and opponent info."""
    tb = tb.sort_values(["team_tricode", "game_date", "game_id"]).copy()
    tb["tg"] = tb.groupby(["team_tricode", "season"]).cumcount()
    opp = tb[["game_id", "team_tricode", "points", "field_goals_attempted", "free_throws_attempted",
              "rebounds_offensive", "turnovers"]].copy()
    opp.columns = [c if c == "game_id" else "o_" + c for c in opp.columns]
    tb = tb.merge(opp, on="game_id")
    tb = tb[tb.team_tricode != tb.o_team_tricode].copy()
    tb = tb.sort_values(["team_tricode", "game_date", "game_id"])
    tb["poss"] = (tb.field_goals_attempted + 0.44 * tb.free_throws_attempted
                  - tb.rebounds_offensive + tb.turnovers)
    return tb


def trailing_defense(tg):
    """Opponent-facing defensive quality: trailing-30 (pre-game) points allowed and pace per team."""
    g = tg.groupby(["team_tricode", "season"])
    tg["def_pa30"] = g["o_points"].transform(lambda s: s.shift(1).rolling(30, min_periods=15).mean())
    tg["pace30"] = g["poss"].transform(lambda s: s.shift(1).rolling(30, min_periods=15).mean())
    return tg


def build_events(pb, tg):
    """Walk each team-season in time order keeping pre-G state only; emit one row per (absorber, game)."""
    rows = []
    for (team, season), g in tg.groupby(["team_tricode", "season"]):
        games = g.sort_values("tg")
        p = pb[(pb.team_tricode == team) & (pb.season == season)]
        by_game = {gid: d for gid, d in p.groupby("game_id")}
        hist = {}  # person_id -> list of (tg, min, pts, fga) for PLAYED games
        for _, gr in games.iterrows():
            d = by_game.get(gr.game_id)
            if d is None:
                continue
            gi = gr.tg
            rot = {}
            for pid, h in hist.items():
                if h[-1][0] >= gi - 10 and len(h) >= 5:
                    last = h[-10:]
                    am = np.mean([x[1] for x in last])
                    if am >= 20:
                        rot[pid] = dict(am=am, fga=np.mean([x[3] for x in last]), pts=np.mean([x[2] for x in last]))
            absent = [pid for pid in rot if pid in set(d.loc[~d.played, "person_id"])]
            inj = [pid for pid in absent if pid in set(d.loc[d.inj_dnp, "person_id"])]
            any_dnp_rot = len(absent)
            kind = None
            if any_dnp_rot == 0:
                kind = "clean"
            elif any_dnp_rot == 1 and len(inj) == 1:
                kind = "single"
            role = None
            if kind == "single":
                a = inj[0]
                top_fga = max(rot, key=lambda k: rot[k]["fga"])
                top5 = sorted(rot, key=lambda k: -rot[k]["am"])[:5]
                role = "creator" if a == top_fga else ("starter" if a in top5 else "rotation")
            if kind:
                for _, r in d[d.played].iterrows():
                    b = r.person_id
                    if b in rot and (kind == "clean" or b != inj[0]):
                        h = hist[b][-10:]
                        rows.append(dict(team=team, season=season, game_id=gr.game_id, tg=gi, kind=kind,
                                         role=role, absent=inj[0] if kind == "single" else None, b=b,
                                         d_pts=r.points - np.mean([x[2] for x in h]),
                                         d_min=r["min"] - np.mean([x[1] for x in h]),
                                         d_fga=r.field_goals_attempted - np.mean([x[3] for x in h]),
                                         opp=gr.o_team_tricode, def_pa30=gr.get("opp_def_pa30"),
                                         opp_pace30=gr.get("opp_pace30"), game_date=gr.game_date))
            for _, r in d[d.played].iterrows():
                hist.setdefault(r.person_id, []).append((gi, r["min"], r.points, r.field_goals_attempted))
    return pd.DataFrame(rows)


def attach_opponent(tg):
    key = tg[["game_id", "team_tricode", "def_pa30", "pace30"]].copy()
    key.columns = ["game_id", "o_team_tricode", "opp_def_pa30", "opp_pace30"]
    return tg.merge(key, on=["game_id", "o_team_tricode"], how="left")


def boot_ci(x, groups=None, B=2000, seed=20261020):
    """Percentile CI of the mean. With `groups` (team-game ids) resamples whole games (absorbers in one game are correlated)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    if groups is not None:  # ratio estimator: resample games, keep the same all-absorber-games mean
        gs = pd.Series(x).groupby(np.asarray(groups)).agg(["sum", "count"]).to_numpy()
        idx = rng.integers(0, len(gs), (B, len(gs)))
        m = gs[idx, 0].sum(1) / gs[idx, 1].sum(1)
        return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
    m = [rng.choice(x, len(x)).mean() for _ in range(B)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    if "--reuse" in sys.argv and (OUT / "events.parquet").exists():
        ev = pd.read_parquet(OUT / "events.parquet")
    else:
        pb, tb = load()
        tg = attach_opponent(trailing_defense(team_games(pb, tb)))
        ev = build_events(pb, tg)
        ev.to_parquet(safe_out(OUT / "events.parquet"))
    lines = ["# W81.2 Part A - lineup cross, parts 1-3 (EXPLORATORY, not a verdict)\n"]
    clean = ev[ev.kind == "clean"]
    base = {m: clean[m].mean() for m in ("d_pts", "d_min", "d_fga")}
    lines.append(f"Absorber-games: clean={len(clean)} single-absence={int((ev.kind=='single').sum())}. "
                 f"Clean-control mean effect (should be ~0): pts {base['d_pts']:+.3f} min {base['d_min']:+.3f} fga {base['d_fga']:+.3f}\n")
    lines.append("## 1. Split: net uplift of the absorber by the absent player's role\n")
    lines.append("| role of absent | absorber-games | team-games | d_pts net [95% CI] | d_min net | d_fga net |\n|---|---|---|---|---|---|")
    sing = ev[ev.kind == "single"]
    for role in ("creator", "starter", "rotation"):
        s = sing[sing.role == role]
        if len(s) < 30:
            continue
        lo, hi = boot_ci(s.d_pts - base["d_pts"], s.team + s.game_id.astype(str))
        lines.append(f"| {role} | {len(s)} | {s.game_id.nunique()} | {s.d_pts.mean()-base['d_pts']:+.2f} [{lo-0:+.2f},{hi:+.2f}] "
                     f"| {s.d_min.mean()-base['d_min']:+.2f} | {s.d_fga.mean()-base['d_fga']:+.2f} |")
    # 2. rank + stability
    lines.append("\n## 2. Rank against history and stability\n")
    c = sing[sing.role == "creator"].copy()
    c = c.sort_values(["b", "season", "game_date"])
    c["half"] = c.groupby(["team", "season", "b"]).cumcount() % 2
    pair = c.groupby(["team", "season", "b"]).size()
    keep = pair[pair >= 6].index
    cc = c.set_index(["team", "season", "b"]).loc[keep].reset_index()
    h = cc.groupby(["team", "season", "b", "half"]).d_pts.mean().unstack()
    h = h.dropna()
    if len(h) >= 10:
        r = h[0].corr(h[1], method="spearman")
        rng = np.random.default_rng(20261020)
        bs = [h.sample(len(h), replace=True, random_state=int(rng.integers(1e9)))
              for _ in range(500)]
        rs = [b[0].corr(b[1], method="spearman") for b in bs]
        lines.append(f"Split-half (odd/even game) Spearman of pair-level uplift, creator absences, absorber-team-seasons with >=6 creator-absence games: "
                     f"r={r:.3f} [{np.percentile(rs,2.5):.3f},{np.percentile(rs,97.5):.3f}] over {len(h)} pairs.\n")
    else:
        lines.append(f"Split-half: only {len(h)} pairs with >=6 games - insufficient.\n")
    # year-to-year: same absorber, creator absences, consecutive seasons
    y = c.groupby(["b", "season"]).d_pts.agg(["mean", "size"]).reset_index()
    y = y[y["size"] >= 3]
    j = y.merge(y.assign(season=y.season - 1), on=["b", "season"], suffixes=("", "_next"))
    if len(j) >= 10:
        r2 = j["mean"].corr(j["mean_next"], method="spearman")
        lines.append(f"Year-to-year Spearman (same absorber, >=3 creator-absence games in each of two consecutive "
                     f"seasons): r={r2:.3f} over {len(j)} absorber-season pairs.\n")
    else:
        lines.append(f"Year-to-year: {len(j)} pairs - insufficient.\n")
    # rank distribution
    pu = cc.groupby(["team", "season", "b"]).d_pts.agg(["mean", "size"])
    lines.append(f"Distribution of absorber-team-season mean uplift (pts) over {len(pu)} comparable cases: "
                 + ", ".join(f"p{q}={pu['mean'].quantile(q/100):+.2f}" for q in (5, 25, 50, 75, 95)) + ".\n")
    # 3. matchup cross
    lines.append("## 3. Matchup cross: creator-absence uplift by opponent defence and pace tercile\n")
    s = sing[sing.role == "creator"].dropna(subset=["def_pa30", "opp_pace30"]).copy()
    # tercile cuts over ALL analysable team-games of the season (pre-registered), not over the absence subset
    allg = ev.drop_duplicates(["team", "game_id"]).dropna(subset=["def_pa30", "opp_pace30"])
    cuts = allg.groupby("season").agg(d1=("def_pa30", lambda x: x.quantile(1 / 3)), d2=("def_pa30", lambda x: x.quantile(2 / 3)),
                                      p1=("opp_pace30", lambda x: x.quantile(1 / 3)), p2=("opp_pace30", lambda x: x.quantile(2 / 3)))
    s = s.join(cuts, on="season")
    s["def_t"] = np.where(s.def_pa30 <= s.d1, "good D", np.where(s.def_pa30 <= s.d2, "mid", "weak D"))
    s["pace_t"] = np.where(s.opp_pace30 <= s.p1, "slow", np.where(s.opp_pace30 <= s.p2, "mid", "fast"))
    lines.append("| opp defence | n | d_pts net [95% CI] |\n|---|---|---|")
    for t, g in s.groupby("def_t", observed=True):
        lo, hi = boot_ci(g.d_pts - base["d_pts"], g.team + g.game_id.astype(str))
        lines.append(f"| {t} | {len(g)} | {g.d_pts.mean()-base['d_pts']:+.2f} [{lo:+.2f},{hi:+.2f}] |")
    lines.append("\n| opp pace | n | d_pts net [95% CI] |\n|---|---|---|")
    for t, g in s.groupby("pace_t", observed=True):
        lo, hi = boot_ci(g.d_pts - base["d_pts"], g.team + g.game_id.astype(str))
        lines.append(f"| {t} | {len(g)} | {g.d_pts.mean()-base['d_pts']:+.2f} [{lo:+.2f},{hi:+.2f}] |")
    # frequency
    tgm = ev.drop_duplicates(["team", "game_id"])
    tot = len(tgm)
    lines.append("\nFrequency (share of team-games in the analysable set): " + ", ".join(
        f"{k}={(tgm.role==k).sum()/tot:.1%}" for k in ("creator", "starter", "rotation")) +
        f"; clean={(tgm.kind=='clean').sum()/tot:.1%} (n team-games={tot}).\n")
    safe_out(OUT / "results_partA.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
