"""EXPLORATORY -- W75.2 Part A: aggregate + interpret F5/F6 (coverage shell x personnel x motion). Writes via safe_out()."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
import factors as F  # noqa: E402

ROOT = HERE.parent.parent


def corr(a, b):
    m = a.notna() & b.notna()
    return (float(np.corrcoef(a[m], b[m])[0, 1]), int(m.sum())) if m.sum() > 5 else (float("nan"), int(m.sum()))


def main():
    plays = F.build_play_table(ROOT, list(range(2018, 2026)))
    res = {}
    cov = plays.groupby("season").agg(plays=("epa", "size"), shell=("shell", lambda x: x.notna().mean()),
                                      motion=("motion", lambda x: x.notna().mean()))
    res["fill"] = cov.round(3).to_dict("index")

    # --- literal 2025 question: Cover 6 share on 11 personnel with pre-snap motion, season to date at 2026-03-01 ---
    asof = pd.Timestamp("2026-03-01", tz="UTC")
    v = F.factor_values(plays, asof, F.COVERAGE_X_PERSONNEL, prior_seasons_only=2025)
    v25 = F.factor_values(plays[plays.season == 2025], asof, F.COVERAGE_X_PERSONNEL)  # 2025 only, for the illustration
    lit = v25[(v25["shell"] == "COVER_6") & (v25["pers"] == "11") & (v25["motion"] == "M")].sort_values("share_shrunk", ascending=False)
    # share of the defense's 11-personnel+motion snaps that were Cover 6
    base = plays[(plays.season == 2025) & plays.shell.notna() & (plays.pers == "11") & (plays.motion == "M")]
    g = base.groupby("dfn").agg(n=("epa", "size"), c6=("shell", lambda x: (x == "COVER_6").sum()), epa=("epa", "mean"), succ=("success", "mean"))
    c6 = base[base.shell == "COVER_6"].groupby("dfn").agg(c6_epa=("epa", "mean"), c6_succ=("success", "mean"))
    g = g.join(c6)
    lg_rate = g.c6.sum() / g.n.sum()
    k = 40.0
    g["rate"] = g.c6 / g.n
    g["rate_shrunk"] = (g.c6 + k * lg_rate) / (g.n + k)
    res["league_c6_rate_11_motion_2025"] = float(lg_rate)
    res["illustration_2025_top"] = g.sort_values("rate_shrunk", ascending=False).head(8).round(3).reset_index().to_dict("records")

    # --- stability: split-half (odd/even game index) and YoY of shell shares and shell-conditional EPA allowed ---
    def half(df, par):
        return df[df.game_idx % 2 == par]
    rows = []
    for s in range(2019, 2026):
        d = plays[(plays.season == s) & plays.shell.notna() & plays.pers.notna()]
        if len(d) < 5000:
            continue
        for shell in ("COVER_1", "COVER_2", "COVER_3", "COVER_4", "COVER_6", "COVER_0", "2_MAN"):
            a = half(d, 0).groupby("dfn").apply(lambda x: (x.shell == shell).mean())
            b = half(d, 1).groupby("dfn").apply(lambda x: (x.shell == shell).mean())
            r, n = corr(a, b)
            rows.append(dict(season=s, shell=shell, kind="share_splithalf", r=r, n=n))
        # shell-conditional EPA allowed on 11 personnel pass-heavy cell: man vs zone EPA split
        for par in (0, 1):
            pass
    sh = pd.DataFrame(rows)
    res["splithalf_share"] = sh.groupby("shell").r.mean().round(3).to_dict()
    # Spearman-Brown to full-season reliability
    res["splithalf_share_SB"] = {k_: round(2 * r / (1 + r), 3) for k_, r in res["splithalf_share"].items() if r == r}
    yoy = []
    for s in range(2019, 2025):
        d0, d1 = plays[(plays.season == s) & plays.shell.notna()], plays[(plays.season == s + 1) & plays.shell.notna()]
        if len(d0) < 5000 or len(d1) < 5000:
            continue
        for shell in ("COVER_1", "COVER_2", "COVER_3", "COVER_4", "COVER_6"):
            a = d0.groupby("dfn").apply(lambda x: (x.shell == shell).mean())
            b = d1.groupby("dfn").apply(lambda x: (x.shell == shell).mean())
            r, n = corr(a, b)
            yoy.append(dict(season=s, shell=shell, r=r))
    yy = pd.DataFrame(yoy)
    res["yoy_share"] = yy.groupby("shell").r.mean().round(3).to_dict()
    # cell-EPA stability: does a defense's shrunk-cell EPA allowed (shell x pers) predict next season's?
    ep = []
    for s in range(2020, 2025):
        a = F.factor_values(plays[plays.season == s], pd.Timestamp(f"{s+1}-03-01", tz="UTC"), F.COVERAGE_X_PERSONNEL_NOMOTION)
        b = F.factor_values(plays[plays.season == s + 1], pd.Timestamp(f"{s+2}-03-01", tz="UTC"), F.COVERAGE_X_PERSONNEL_NOMOTION)
        m = a.merge(b, on=["dfn", "shell", "pers"], suffixes=("_0", "_1"))
        m = m[(m.n_0 >= 30) & (m.n_1 >= 30)]
        ep.append(dict(season=s, raw=corr(m.adj_0, m.adj_1)[0], shrunk=corr(m.epa_shrunk_0, m.epa_shrunk_1)[0], cells=len(m)))
    res["yoy_cell_epa_allowed"] = ep
    # does the defense's 'shell mix given personnel' persist? corr of share(shell|pers) YoY
    sp = []
    for s in range(2020, 2025):
        a = F.factor_values(plays[plays.season == s], pd.Timestamp(f"{s+1}-03-01", tz="UTC"), F.COVERAGE_X_PERSONNEL_NOMOTION)
        b = F.factor_values(plays[plays.season == s + 1], pd.Timestamp(f"{s+2}-03-01", tz="UTC"), F.COVERAGE_X_PERSONNEL_NOMOTION)
        m = a.merge(b, on=["dfn", "shell", "pers"], suffixes=("_0", "_1"))
        m = m[(m.n_0 >= 30) & (m.n_1 >= 30)]
        sp.append(dict(season=s, share_r=corr(m.share_0, m.share_1)[0]))
    res["yoy_cell_share"] = sp
    # motion: league effect and the who-lives-in-this-look view for the offense side (unit_side='off')
    d = plays[(plays.season >= 2022) & plays.shell.notna() & plays.motion.notna() & (plays.pers == "11")]
    res["motion_effect_11"] = d.groupby(["motion"]).agg(n=("epa", "size"), epa=("epa", "mean"), succ=("success", "mean")).round(4).to_dict("index")
    res["shell_x_motion_11_league"] = d.groupby(["shell", "motion"]).agg(n=("epa", "size"), epa=("epa", "mean"), succ=("success", "mean")).round(3).reset_index().to_dict("records")
    ov = F.factor_values(plays[plays.season == 2025], asof, F.FactorSpec("F5F6_off", ("shell", "pers", "motion"), "off", ("shell", "pers")))
    ov = ov[ov.n >= 40].sort_values("epa_shrunk", ascending=False)
    res["offense_view_2025_top"] = ov.head(5)[["off", "shell", "pers", "motion", "n", "adj", "epa_shrunk", "succ"]].round(3).to_dict("records")
    res["offense_view_2025_bottom"] = ov.tail(5)[["off", "shell", "pers", "motion", "n", "adj", "epa_shrunk", "succ"]].round(3).to_dict("records")
    res["k_cell"] = v.attrs.get("k_cell")
    p = safe_out(HERE / "part_a.json")
    p.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float)[:9000])


if __name__ == "__main__":
    main()
