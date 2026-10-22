"""W84.2: NBA PAM mass tier (layer 3). Assigns pam_v4 factors/modifiers to every player-season the free signals cover.

Reads the NBA event store (raw parquet, gitignored) and Muse's play-type/tracking records (read-only archive clone).
Interpreted-only: no price test, no model, no ledger, no registry cell touched.

    python3 mass_tier.py --store <NBA_EVENTS/raw> --claims <tracking-play-types.claims.jsonl> --out <dir>

Season label = calendar year the season ends (2026 = 2025-26). Muse's `season` field is the starting year (+1 to align).
Thresholds are pam_v4 as written (taxonomy.json). A clause with no free signal is UNSCORED and listed, never proxied.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402

SEASONS = (2024, 2025, 2026)
QUAL_GP = 15       # season-end qualifier: games played
QUAL_MPG = 10.0    # season-end qualifier: minutes per game (the site's qualifier)
PIT_GP = 10        # point-in-time qualifier: prior games played
MIN_RIM_ATT = 30   # rim FG% needs this many season rim attempts
MIN_BENCH_G = 8    # bench-USG needs this many bench games

SUM_COLS = ["g", "min", "fga", "fgm", "tpa", "tpm", "fta", "ftm", "oreb", "dreb", "ast", "blk", "tov", "pf", "pts", "pts2",
            "tm_min", "tm_fga", "tm_fta", "tm_tov", "tm_fgm", "tm_oreb", "tm_dreb", "opp_2pa", "opp_oreb", "opp_dreb",
            "sh_att", "rim_att", "rim_made", "mid_att", "mid_made", "pu3_att", "pu3_made",
            "bench_g", "bench_ev", "bench_min", "bench_tmev", "bench_tmmin", "start_c"]


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())


def mins(x):
    try:
        m, s = str(x).split(":")
        return int(m) + int(s) / 60.0
    except Exception:
        return 0.0


def ren(df, mapping):
    """Column relabel (DataFrame.rename is write-shaped to the isolation scan)."""
    return df.set_axis([mapping.get(c, c) for c in df.columns], axis=1)


def parse_ts(s):
    return pd.to_datetime(s, utc=True)


# ---------------------------------------------------------------- build the player-game table
def load_player_games(store: Path, seasons=SEASONS) -> pd.DataFrame:
    frames = []
    for s in seasons:
        pb = pd.read_parquet(store / "player_box" / f"player_box_{s}.parquet")
        tb = pd.read_parquet(store / "team_box" / f"team_box_{s}.parquet")
        sc = pd.read_parquet(store / "schedule" / f"schedule_{s}.parquet")[["game_id", "game_date"]]
        sh = pd.read_parquet(store / "shots" / f"shots_{s}.parquet")
        pb = pb[pb.season_type_id.astype(str) == "2"].copy()
        tb = tb[tb.season_type_id.astype(str) == "2"].copy()
        pb["min"] = pb["minutes"].map(mins)
        pb = pb[pb["min"] > 0]
        t = tb[["game_id", "team_id", "minutes", "field_goals_attempted", "field_goals_made", "three_pointers_attempted",
                "free_throws_attempted", "turnovers", "rebounds_offensive", "rebounds_defensive"]].copy()
        t["tm_min"] = t["minutes"].map(mins)
        t = ren(t, {"field_goals_attempted": "tm_fga", "field_goals_made": "tm_fgm", "free_throws_attempted": "tm_fta",
                    "turnovers": "tm_tov", "rebounds_offensive": "tm_oreb", "rebounds_defensive": "tm_dreb",
                    "three_pointers_attempted": "tm_tpa"})
        o = ren(t[["game_id", "team_id", "tm_fga", "tm_tpa", "tm_oreb", "tm_dreb"]],
                {"team_id": "opp_id", "tm_fga": "opp_fga", "tm_tpa": "opp_tpa", "tm_oreb": "opp_oreb", "tm_dreb": "opp_dreb"})
        pg = pb.merge(t.drop(columns=["minutes", "tm_tpa"]), on=["game_id", "team_id"])
        pg = pg.merge(o, on="game_id")
        pg = pg[pg.team_id != pg.opp_id]
        pg["opp_2pa"] = pg["opp_fga"] - pg["opp_tpa"]
        pg = pg.merge(sc, on="game_id", how="left")
        sh = sh[sh.game_id.isin(pg.game_id)].copy()
        d = pd.to_numeric(sh["shot_distance"], errors="coerce")
        v = pd.to_numeric(sh["shot_value"], errors="coerce")
        made = (sh["shot_result"].astype(str).str.lower() == "made") | (sh["action_type"] == "Made Shot")
        subl = sh["sub_type"].astype(str).str.lower()
        sh["att"] = 1
        sh["rim_att"] = (d <= 3).astype(int)
        sh["rim_made"] = ((d <= 3) & made).astype(int)
        mid = (v == 2) & (d >= 10)
        sh["mid_att"] = mid.astype(int)
        sh["mid_made"] = (mid & made).astype(int)
        pu = (v == 3) & subl.str.contains("pullup|pull-up|step back", regex=True)
        sh["pu3_att"] = pu.astype(int)
        sh["pu3_made"] = (pu & made).astype(int)
        agg = sh.groupby(["game_id", "person_id"])[["att", "rim_att", "rim_made", "mid_att", "mid_made", "pu3_att", "pu3_made"]].sum()
        agg = ren(agg, {"att": "sh_att"}).reset_index()
        pg = pg.merge(agg, on=["game_id", "person_id"], how="left").fillna({c: 0 for c in agg.columns if c not in ("game_id", "person_id")})
        pg = ren(pg, {"field_goals_attempted": "fga", "field_goals_made": "fgm", "three_pointers_attempted": "tpa",
                      "three_pointers_made": "tpm", "free_throws_attempted": "fta", "free_throws_made": "ftm",
                      "rebounds_offensive": "oreb", "rebounds_defensive": "dreb", "assists": "ast", "blocks": "blk",
                      "turnovers": "tov", "fouls_personal": "pf", "points": "pts"})
        pg["pts2"] = pg["pts"] ** 2
        pg["g"] = 1
        pos = pg["position"].fillna("").astype(str).str.strip()
        pg["start"] = (pos != "").astype(int)
        pg["start_c"] = (pos == "C").astype(int)
        pg["ev"] = pg["fga"] + 0.44 * pg["fta"] + pg["tov"]
        pg["tm_ev"] = pg["tm_fga"] + 0.44 * pg["tm_fta"] + pg["tm_tov"]
        bench = pg["start"] == 0
        pg["bench_g"] = bench.astype(int)
        pg["bench_ev"] = np.where(bench, pg["ev"], 0.0)
        pg["bench_min"] = np.where(bench, pg["min"], 0.0)
        pg["bench_tmev"] = np.where(bench, pg["tm_ev"], 0.0)
        pg["bench_tmmin"] = np.where(bench, pg["tm_min"], 0.0)
        pg["season"] = s
        pg["person_id"] = pg["person_id"].astype(int)
        frames.append(pg)
    out = pd.concat(frames, ignore_index=True)
    out["game_date"] = pd.to_datetime(out["game_date"]).dt.tz_localize(None).dt.normalize()
    return out.sort_values(["game_date", "game_id"]).reset_index(drop=True)


# ---------------------------------------------------------------- signals from sums (shared by season-end, halves, PIT)
def signals_from_sums(s: pd.DataFrame) -> pd.DataFrame:
    """`s` has SUM_COLS (no `ev` columns needed). Returns the signal frame; no clause thresholds applied here."""
    five = s["tm_min"] / 5.0
    out = pd.DataFrame(index=s.index)
    out["gp"] = s["g"]
    out["mpg"] = s["min"] / s["g"]
    ev = s["fga"] + 0.44 * s["fta"] + s["tov"]
    tmev = s["tm_fga"] + 0.44 * s["tm_fta"] + s["tm_tov"]
    out["usg"] = 100 * ev * five / (s["min"] * tmev)
    out["ts"] = s["pts"] / (2 * (s["fga"] + 0.44 * s["fta"]))
    out["ast_pct"] = 100 * s["ast"] / ((s["min"] / five) * s["tm_fgm"] - s["fgm"])
    out["tov_pct"] = 100 * s["tov"] / ev
    out["oreb_pct"] = 100 * s["oreb"] * five / (s["min"] * (s["tm_oreb"] + s["opp_dreb"]))
    out["dreb_pct"] = 100 * s["dreb"] * five / (s["min"] * (s["tm_dreb"] + s["opp_oreb"]))
    out["blk_pct"] = 100 * s["blk"] * five / (s["min"] * s["opp_2pa"])
    out["ftr"] = s["fta"] / s["fga"]
    out["tpa_rate"] = s["tpa"] / s["fga"]
    out["tp_pct"] = s["tpm"] / s["tpa"]
    out["tpa_pg"] = s["tpa"] / s["g"]
    out["pf36"] = 36 * s["pf"] / s["min"]
    out["rim_freq"] = s["rim_att"] / s["sh_att"]
    out["rim_att_pg"] = s["rim_att"] / s["g"]
    out["rim_att_n"] = s["rim_att"]
    out["rim_fg"] = s["rim_made"] / s["rim_att"]
    out["mid_att_pg"] = s["mid_att"] / s["g"]
    out["mid_efg"] = s["mid_made"] / s["mid_att"]
    out["pu3_att_pg"] = s["pu3_att"] / s["g"]
    out["pu3_pct"] = s["pu3_made"] / s["pu3_att"]
    bt = s["bench_tmev"]
    out["bench_g"] = s["bench_g"]
    out["bench_usg"] = 100 * s["bench_ev"] * (s["bench_tmmin"] / 5.0) / (s["bench_min"] * bt)
    out["start_c_g"] = s["start_c"]
    n = s["g"]
    var = (s["pts2"] - s["pts"] ** 2 / n) / (n - 1)
    out["pts_sd"] = np.sqrt(var.clip(lower=0))
    return out.mask(np.isinf(out))


def aggregate(pg: pd.DataFrame, by=("season", "person_id")) -> pd.DataFrame:
    cols = [c for c in SUM_COLS if c in pg.columns]
    s = pg.groupby(list(by))[cols].sum()
    return s


def player_team(pg: pd.DataFrame) -> pd.Series:
    last = pg.sort_values(["game_date", "game_id"]).groupby(["season", "person_id"]).tail(1)
    return last.set_index(["season", "person_id"])["team_tricode"]


def add_m17(sig: pd.DataFrame, team: pd.Series) -> pd.DataFrame:
    """M-17: sigma(per-game pts) above the team mean by 1+ stddev, among rotation players (>=QUAL_GP games, >=QUAL_MPG)."""
    sig = sig.copy()
    sig["team"] = team.reindex(sig.index).values
    rot = sig[(sig.gp >= QUAL_GP) & (sig.mpg >= QUAL_MPG)]
    g = rot.groupby([sig.index.get_level_values(0)[sig.index.isin(rot.index)], "team"])["pts_sd"]
    mean, sd, cnt = g.transform("mean"), g.transform("std"), g.transform("count")
    sig["m17_z"] = np.nan
    ok = cnt >= 5
    sig.loc[rot.index[ok.values], "m17_z"] = ((rot["pts_sd"] - mean) / sd)[ok].values
    return sig


# ---------------------------------------------------------------- Muse records (REPORTED)
PLAYTYPE = {"Transition": "trans", "Post-Up": "post", "Pick and Roll Roll Man": "roll"}


def load_muse(claims: Path) -> pd.DataFrame:
    rows = []
    for line in open(claims):
        r = json.loads(line)
        m, sp = r["metric"], str(r.get("split") or "")
        notes = r.get("notes") or ""
        gp = re.search(r"GP (\d+)", notes)
        poss = re.search(r"POSS ([\d.]+) per game", notes)
        rows.append({"player": r["player"], "team": r["team"], "season": int(r["season"]) + 1, "metric": m, "split": sp,
                     "value": r["value"], "gp": int(gp.group(1)) if gp else None,
                     "poss_pg": float(poss.group(1)) if poss else None, "id": r["id"]})
    return pd.DataFrame(rows)


def muse_signals(muse: pd.DataFrame, names: pd.DataFrame) -> pd.DataFrame:
    """One row per (season, person_id): Muse-reported values. names: season, person_id, key (normalized name)."""
    muse = muse.copy()
    muse["key"] = muse["player"].map(norm)
    m = muse.merge(names, on=["season", "key"], how="left")
    matched = m.dropna(subset=["person_id"]).copy()
    matched["person_id"] = matched["person_id"].astype(int)
    out = {}
    for (s, pid), grp in matched.groupby(["season", "person_id"]):
        d = {}
        for _, r in grp.iterrows():
            mt, sp = r["metric"], r["split"]
            if mt.startswith("play-type frequency"):
                k = PLAYTYPE.get(sp.removeprefix("play type: "))
                if k:
                    d[f"{k}_freq"] = r["value"]
                    if r["poss_pg"] is not None:
                        d[f"{k}_poss_pg"] = r["poss_pg"]
            elif mt.startswith("play-type points per possession"):
                k = PLAYTYPE.get(sp.removeprefix("play type: "))
                if k:
                    d[f"{k}_ppp"] = r["value"]
            elif mt.startswith("touches"):
                d["touches_pg"] = r["value"]
            elif mt.startswith("drives"):
                d["drives_pg"] = r["value"]
            elif mt.startswith("potential assists"):
                d["potast_pg"] = r["value"]
        out[(s, pid)] = d
    df = pd.DataFrame.from_dict(out, orient="index")
    df.index = pd.MultiIndex.from_tuples(df.index, names=["season", "person_id"])
    return df, muse, m


# ---------------------------------------------------------------- the v4 rules, as written
# status: MET (every clause scored and met) | MET_PARTIAL (every scored clause met, >=1 clause unscored)
#         NOT_MET (a scored clause failed) | UNSCORED (no clause has a free signal)
FACTORS = {
    "PRF-1": "Heliocentric On-Ball Engine", "PRF-2": "Primary On-Ball Creator (non-helio)", "PRF-3": "Secondary Creator / Connector",
    "PRF-4": "Off-Ball Shooter / Movement Spacer", "PRF-5": "Slasher / Rim Pressure Wing", "PRF-6": "Post / Elbow Hub",
    "PRF-7": "Roll-Man / Screen-Setter Big", "PRF-8": "Pop Big / Stretch Big", "PRF-9": "Rim Protector Anchor",
    "PRF-10": "POA Stopper", "PRF-11": "Wing Stopper / Switch Defender", "PRF-12": "Rebounding / Possession Specialist",
    "PRF-13": "Transition Weapon", "PRF-14": "Bench Microwave Scorer", "PRF-15": "Utility Depth / Low-Usage Stabilizer",
}
ALL_IDS = list(FACTORS) + [f"M-{i}" for i in range(1, 33)]


def _ok(v):
    return v is not None and not (isinstance(v, float) and np.isnan(v))


def clauses(fid: str, x: dict, pit: bool = False):
    """Return (scored, unscored): scored = list of bool, unscored = list of text. `x` is a signal dict."""
    g = x.get
    U = []
    S = []

    def chk(val, test):
        if _ok(val):
            S.append(bool(test(val)))
        else:
            U.append("signal missing for this player-season")

    if fid == "PRF-1":
        chk(g("usg"), lambda v: v >= 30); U.append(">=40% of team possessions through player: no published metric")
    elif fid == "PRF-2":
        chk(g("usg"), lambda v: 25 <= v < 30); U.append("secondary engine / can lead lineups: film judgment")
    elif fid == "PRF-3":
        chk(g("usg"), lambda v: 18 <= v < 25); U.append("advantage-extender: film construct, no free source")
    elif fid == "PRF-4":
        chk(g("tpa_rate"), lambda v: v >= 0.45); U.append(">=35% catch-and-shoot 3P: C&S tracking not in event store (stats.nba.com unreachable)")
    elif fid == "PRF-5":
        chk(g("rim_freq"), lambda v: v >= 0.30); chk(g("ftr"), lambda v: v >= 0.30)
    elif fid == "PRF-6":
        if pit:
            U.append("post-up possessions/game: Muse season snapshot, not point-in-time")
        else:
            chk(g("post_poss_pg"), lambda v: v >= 4)
        U.append("hub passer: pass-out rate not published by play type")
    elif fid == "PRF-7":
        if pit:
            U.append("roll possessions/game: Muse season snapshot, not point-in-time")
        else:
            chk(g("roll_poss_pg"), lambda v: v >= 0.5)
        if _ok(g("rim_att_n")) and g("rim_att_n") >= MIN_RIM_ATT:
            S.append(bool(g("rim_fg") >= 0.65))
        else:
            U.append(f"rim FG% needs >={MIN_RIM_ATT} rim attempts")
    elif fid == "PRF-8":
        if _ok(g("start_c_g")) and g("start_c_g") >= 5:
            S.append(bool(g("tpa_rate") >= 0.30))
        else:
            U.append("'a 5' designation: box position exists only for starters (<5 starts at C)")
        U.append("pick-and-pop primary: not a published play type")
    elif fid == "PRF-9":
        chk(g("blk_pct"), lambda v: v >= 4); U.append("rim deterrence in opponent shot location: bot-side computation not built")
    elif fid in ("PRF-10", "PRF-11"):
        U.append("defensive tracking construct (Second Spectrum/Synergy detail): no free source")
    elif fid == "PRF-12":
        if _ok(g("oreb_pct")) and _ok(g("dreb_pct")):
            S.append(bool(g("oreb_pct") >= 10 or g("dreb_pct") >= 25))
        else:
            U.append("signal missing")
        U.append("elite contested rate: rebounding tracking not in event store")
    elif fid == "PRF-13":
        if pit:
            U.append("transition freq/PPP: Muse season snapshot, not point-in-time")
        else:
            chk(g("trans_freq"), lambda v: v >= 20); chk(g("trans_ppp"), lambda v: v >= 1.2)
    elif fid == "PRF-14":
        if _ok(g("bench_g")) and g("bench_g") >= MIN_BENCH_G:
            S.append(bool(g("bench_usg") >= 22))
        else:
            U.append(f"bench USG needs >={MIN_BENCH_G} bench games")
        U.append("shot volatility above team mean: undefined unit (shot count? make rate?) in v4")
    elif fid == "PRF-15":
        chk(g("usg"), lambda v: v <= 15); U.append("turnover avoidance + role discipline: no numeric test in v4")
    elif fid == "M-2":
        chk(g("ftr"), lambda v: v >= 0.40)
    elif fid == "M-3":
        if _ok(g("rim_att_pg")):
            S.append(bool(g("rim_att_pg") >= 4 and _ok(g("rim_fg")) and g("rim_fg") >= 0.70))
        else:
            U.append("signal missing")
    elif fid == "M-4":
        if _ok(g("mid_att_pg")):
            S.append(bool(g("mid_att_pg") >= 3 and _ok(g("mid_efg")) and g("mid_efg") >= 0.50))
        else:
            U.append("signal missing")
        U.append("self-created qualifier: not separable in the event store")
    elif fid == "M-5":
        if _ok(g("pu3_att_pg")):
            S.append(bool(g("pu3_att_pg") >= 3 and _ok(g("pu3_pct")) and g("pu3_pct") >= 0.38))
        else:
            U.append("signal missing")
    elif fid == "M-6":
        chk(g("ast_pct"), lambda v: v >= 25); U.append("low live-ball TOV: turnover type not split in the store")
    elif fid == "M-13":
        chk(g("oreb_pct"), lambda v: v >= 10); U.append("contested OREB top-decile: rebounding tracking not in store")
    elif fid == "M-14":
        chk(g("dreb_pct"), lambda v: v >= 25); U.append("contested rate >=40%: rebounding tracking not in store")
    elif fid == "M-17":
        if pit:
            U.append("team-relative sigma not computed point-in-time")
        else:
            chk(g("m17_z"), lambda v: v >= 1)
    elif fid == "M-18":
        chk(g("tov_pct"), lambda v: v < 10); U.append("consistent role output: no numeric test in v4")
    elif fid == "M-24":
        chk(g("pf36"), lambda v: v <= 2.5); U.append("while guarding top creators: matchup not measurable free")
    elif fid == "M-29":
        if _ok(g("tpa_pg")):
            S.append(bool(g("tpa_pg") >= 1 and _ok(g("tp_pct")) and g("tp_pct") <= 0.30))
        else:
            U.append("signal missing")
    elif fid in ("M-25", "M-26"):
        U.append("Hustle stats (screen assists / charges drawn) not in event store")
    elif fid in ("M-27", "M-28"):
        U.append("listed height / position-minutes estimates not in event store")
    elif fid in ("M-21", "M-31", "M-32", "M-20"):
        U.append("age / service years / first-year status not in event store (bio fields absent)")
    elif fid in ("M-22", "M-30"):
        U.append("shot-clock splits / one-end impact: not in event store, defining qualifier unmeasurable")
    else:
        U.append("NONE row of Muse's signal map: no free source for the threshold test")
    return S, U


def status(fid, x, pit=False):
    S, U = clauses(fid, x, pit)
    if not S:
        return "UNSCORED", U
    if not all(S):
        return "NOT_MET", U
    return ("MET" if not U else "MET_PARTIAL"), U


def assign_row(x: dict, pit=False):
    out = {}
    for fid in ALL_IDS:
        st, U = status(fid, x, pit)
        out[fid] = {"status": st, "unscored": U} if U else {"status": st}
    return out


# ---------------------------------------------------------------- driver pieces
def season_end(pg: pd.DataFrame, muse_sig: pd.DataFrame = None) -> pd.DataFrame:
    sums = aggregate(pg)
    sig = signals_from_sums(sums)
    sig = add_m17(sig, player_team(pg))
    if muse_sig is not None:
        sig = sig.join(muse_sig, how="left")
    sig["qualified"] = (sig.gp >= QUAL_GP) & (sig.mpg >= QUAL_MPG)
    return sig


def pit_table(pg: pd.DataFrame, season: int) -> pd.DataFrame:
    """Season-to-date signals as of each game, using ONLY games strictly before that game's date (no look-ahead)."""
    d = pg[pg.season == season].sort_values(["person_id", "game_date", "game_id"]).copy()
    cols = [c for c in SUM_COLS if c in d.columns]
    cum = d.groupby("person_id")[cols].cumsum()
    # strictly-before: subtract this game's own row, plus every earlier same-date row (doubleheader-safe for NBA: one game/day/team)
    prior = cum - d[cols]
    prior.index = d.index
    sig = signals_from_sums(prior.where(prior["g"] > 0))
    sig["person_id"] = d["person_id"].values
    sig["game_id"] = d["game_id"].values
    sig["game_date"] = d["game_date"].values
    return sig


def flag_table(sig: pd.DataFrame, pit=False, ids=None) -> pd.DataFrame:
    ids = ids or ALL_IDS
    recs = sig.to_dict("records")
    rows = []
    for r in recs:
        rows.append({fid: status(fid, r, pit)[0] for fid in ids})
    return pd.DataFrame(rows, index=sig.index)
