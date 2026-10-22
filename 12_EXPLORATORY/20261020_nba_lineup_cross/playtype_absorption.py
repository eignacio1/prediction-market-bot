"""W83.2 Part B: grade Muse's play-type class and run the absorber-profile cross.

Reads the NBA event store (raw parquet, gitignored) and the pinned archive claims file.
Writes playtype_absorption_result.json next to this file. Interpreted-only: no price test.

    python3 playtype_absorption.py --store <NBA_EVENTS/raw> --claims <tracking-play-types.claims.jsonl>
"""
import argparse
import json
import math
import random
import unicodedata
from pathlib import Path

import pandas as pd
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402

SEASON = 2026  # label = ending year, i.e. 2025-26
CREATOR_TOP_K = 2
MIN_CREATOR_GP = 15
MIN_WITH, MIN_WITHOUT = 10, 3
MIN_MPG = 10.0  # the site's qualifier

# Pre-registered proxy map: Muse play type -> event-store feature (fixed before looking).
PROXY = {
    "Isolation": "selfcreate_share",
    "Pick and Roll Ball Handler": "ast_per_min",
    "Spot-Up": "assisted3_share",
    "Transition": "fast_share",
    "Cut": "cut_share",
    "Post-Up": "hook_share",
    "Pick and Roll Roll Man": "dunk_share",
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())


def mins(x):
    try:
        m, s = str(x).split(":")
        return int(m) + int(s) / 60.0
    except Exception:
        return 0.0


def spearman(a, b):
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    n = len(ra)
    if n < 3:
        return float("nan")
    ma, mb = ra.mean(), rb.mean()
    num = ((ra - ma) * (rb - mb)).sum()
    den = math.sqrt(((ra - ma) ** 2).sum() * ((rb - mb) ** 2).sum())
    return float(num / den) if den else float("nan")


def load(store):
    r = Path(store)
    box = pd.read_parquet(r / "player_box" / "player_box_2026.parquet")
    box = box[box.season_type_id.astype(int) == 2].copy()
    box["min"] = box.minutes.map(mins)
    box["name"] = box.first_name.fillna("") + " " + box.family_name.fillna("")
    pbp = pd.read_parquet(r / "pbp" / "pbp_2026.parquet")
    pos = pd.read_parquet(r / "possessions" / "possessions_2026.parquet")
    return box, pbp, pos


def shot_features(box, pbp, pos):
    games = set(box.game_id)
    p = pbp[pbp.game_id.isin(games)]
    s = p[p.is_field_goal == True].copy()  # noqa: E712
    s["made"] = s.is_made_shot == True  # noqa: E712
    s["ast"] = s.description.fillna("").str.contains("AST")
    st = s.sub_type.fillna("")
    s["selfc"] = st.str.contains("Pullup|Step Back|Pull-Up|Driving|Fadeaway|Turnaround")
    s["cut"] = st.str.contains("Cutting")
    s["hook"] = st.str.contains("Hook")
    s["dunk"] = st.str.contains("Dunk")
    s["three"] = s.shot_value == 3
    # fast = shot within 8s of possession start
    pk = pos[["game_id", "possession_number", "period", "start_seconds_remaining"]].drop_duplicates(
        ["game_id", "possession_number", "period"])
    s = s.merge(pk, on=["game_id", "possession_number", "period"], how="left")
    s["fast"] = (s.start_seconds_remaining - s.seconds_remaining) <= 8
    g = s.groupby("person_id")
    f = pd.DataFrame({
        "fga": g.size(),
        "selfcreate_share": g.selfc.mean(),
        "cut_share": g.cut.mean(),
        "hook_share": g.hook.mean(),
        "dunk_share": g.dunk.mean(),
        "fast_share": g.fast.mean(),
    })
    m3 = s[s.made & s.three]
    f["assisted3_share"] = m3.groupby("person_id").ast.mean()
    f["m3"] = m3.groupby("person_id").size()
    return f


def player_table(box, feats):
    gp = box[box["min"] > 0].groupby("person_id").agg(
        gp=("game_id", "nunique"), mpg=("min", "mean"), ast=("assists", "sum"), mins=("min", "sum"),
        name=("name", "first"), team=("team_tricode", "last"))
    t = gp.join(feats, how="left")
    t["ast_per_min"] = t.ast / t.mins
    t["norm"] = t.name.map(norm)
    return t


def grade_playtypes(t, claims_path):
    rows = [json.loads(x) for x in open(claims_path)]
    out = {}
    for ptype, feat in PROXY.items():
        key = "play type: " + ptype
        freq = {norm(r["player"]): r["value"] for r in rows
                if r["split"] == key and r["metric"].startswith("play-type frequency")}
        q = t[(t.mpg >= MIN_MPG) & (t.fga >= 50)].copy()
        q["muse"] = q.norm.map(freq)
        q = q.dropna(subset=["muse", feat])
        if feat == "assisted3_share":
            q = q[q.m3 >= 20]
        rho = spearman(q.muse, q[feat])
        top = set(q.nlargest(15, "muse").norm)
        topf = set(q.nlargest(15, feat).norm)
        out[ptype] = {"proxy": feat, "n": int(len(q)), "spearman": round(rho, 3),
                      "top15_overlap": len(top & topf)}
    return out


def absorption(box, t, seed=7):
    box = box.copy()
    box["ev"] = box.field_goals_attempted + 0.44 * box.free_throws_attempted + box.turnovers
    played = box["min"] > 0
    absent_row = (~played) & (~box.comment.fillna("").str.contains("Coach"))
    box["played"] = played
    box["absent"] = absent_row
    ev = box[played].groupby("person_id").ev.mean()
    gp = box[played].groupby("person_id").game_id.nunique()
    results = []
    for team, tb in box.groupby("team_id"):
        tb = tb.copy()
        tm = tb[tb.played].groupby("person_id").agg(ev=("ev", "mean"), gp=("game_id", "nunique"))
        creators = tm[tm.gp >= MIN_CREATOR_GP].nlargest(CREATOR_TOP_K, "ev")
        for cid, crow in creators.iterrows():
            ab_games = sorted(tb[(tb.person_id == cid) & tb.absent].game_id)
            wi_games = set(tb[(tb.person_id == cid) & tb.played].game_id)
            if len(ab_games) < MIN_WITHOUT or len(wi_games) < MIN_WITH:
                continue
            for pid in tm.index:
                if pid == cid:
                    continue
                pr = tb[(tb.person_id == pid) & tb.played]
                w = pr[pr.game_id.isin(wi_games)]
                a = pr[pr.game_id.isin(ab_games)]
                if len(w) < MIN_WITH or len(a) < MIN_WITHOUT:
                    continue
                half = {}
                for k, (lo, hi) in {"h1": (0, 2), "h2": (1, 2)}.items():
                    gs = set(ab_games[lo::hi])
                    aa = a[a.game_id.isin(gs)]
                    half[k] = (aa.ev.mean() - w.ev.mean()) / crow.ev if len(aa) else float("nan")
                results.append({
                    "team": int(team), "creator": int(cid), "absorber": int(pid),
                    "n_with": int(len(w)), "n_without": int(len(a)),
                    "absorb": float((a.ev.mean() - w.ev.mean()) / crow.ev), "h1": half["h1"], "h2": half["h2"]})
    d = pd.DataFrame(results).merge(
        t[["selfcreate_share", "ast_per_min", "assisted3_share", "norm", "mpg"]],
        left_on="absorber", right_index=True, how="left")
    d["creator_ev"] = d.creator.map(ev)
    return d.dropna(subset=["absorb", "ast_per_min", "selfcreate_share"])


def cluster_boot(d, feat, reps=2000, seed=7):
    rnd = random.Random(seed)
    cl = {c: g for c, g in d.groupby("creator")}
    keys = list(cl)

    def stat(frames):
        x = pd.concat(frames)
        return spearman(x[feat], x.absorb)

    est = stat([cl[k] for k in keys])
    bs = []
    for _ in range(reps):
        s = stat([cl[rnd.choice(keys)] for _ in keys])
        if not math.isnan(s):
            bs.append(s)
    bs.sort()
    return est, bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--claims", required=True)
    ap.add_argument("--out", default=str(Path(__file__).with_name("playtype_absorption_result.json")))
    a = ap.parse_args()
    box, pbp, pos = load(a.store)
    t = player_table(box, shot_features(box, pbp, pos))
    grade = grade_playtypes(t, a.claims)
    d = absorption(box, t)
    cross = {"pairs": int(len(d)), "creators": int(d.creator.nunique()), "teams": int(d.team.nunique()),
             "mean_absorb": round(float(d.absorb.mean()), 4)}
    reliab = d.dropna(subset=["h1", "h2"])
    cross["split_half_pair_corr"] = round(float(reliab.h1.corr(reliab.h2)), 3)
    # profile score: creation proxies minus spot-up proxy, z-scored in the pair table
    z = lambda s: (s - s.mean()) / s.std()
    d["profile"] = z(d.selfcreate_share) + z(d.ast_per_min) - z(d.assisted3_share.fillna(d.assisted3_share.mean()))
    for feat in ["profile", "selfcreate_share", "ast_per_min", "assisted3_share"]:
        x = d.copy()
        if feat == "assisted3_share":
            x[feat] = x[feat].fillna(x[feat].mean())
        est, lo, hi = cluster_boot(x, feat)
        cross[feat] = {"spearman": round(est, 3), "ci95": [round(lo, 3), round(hi, 3)]}
    # stability: profile effect on each absorption half
    for h in ("h1", "h2"):
        x = d.dropna(subset=[h])
        cross["profile_vs_" + h] = round(spearman(x.profile, x[h]), 3)
    safe_out(a.out).write_text(json.dumps({"season": "2025-26", "grade": grade, "cross": cross}, indent=1))
    print(json.dumps({"grade": grade, "cross": cross}, indent=1))


if __name__ == "__main__":
    main()
