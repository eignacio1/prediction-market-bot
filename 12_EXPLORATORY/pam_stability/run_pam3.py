"""H-DEPTH-PAM-3 (PREREG.md @ 16fcd204 + PREREG_ADDENDUM_1.md): stability-weighted shrinkage vs EXP-047's raw means, NBA props.

Read-only research code. Nothing here touches a live path, model, runner, leaf map or cron. The judged seasons (2023-2025) are loaded
only with --final. Pure functions take a box-score DataFrame so the known-answer test (tests/test_pam3_known_answer.py) can run the
entire pipeline on a simulated league with planted rates and reliability.

Box schema (one row per player-game with minutes > 0): season, game_id, date (YYYY-MM-DD), person_id, team_id, min, points, rebounds,
assists, threes, blocks, steals, ftm, fta.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
from scipy import stats as sps
from scipy.optimize import minimize_scalar

from prediction_market_bot.quant.inference import mde_paired

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402

STATS = ["points", "rebounds", "assists", "threes"]
LADDER = {"points": [10, 15, 20, 25, 30], "rebounds": [4, 6, 8, 10, 12], "assists": [2, 4, 6, 8, 10], "threes": [1, 2, 3, 4, 5]}
MIN_PRIOR_GAMES, MIN_MPG, ROTATION = 4, 10.0, 10      # EXP-047 as frozen
PSEUDO_LEAGUE_MIN = 500.0
BAND_CUTS = (15.0, 22.0, 29.0)                         # A1
MU_FLOOR, P_CLIP = 0.02, 1e-6                          # A5
QUAL_MIN = 1000.0                                      # split-half qualifying minutes
STRATA = [("4-10", 4, 10), ("11-30", 11, 30), ("31+", 31, 10 ** 9)]
SRC_COLS = {"points": "points", "rebounds": "rebounds_total", "assists": "assists", "threes": "three_pointers_made",
            "blocks": "blocks", "steals": "steals", "ftm": "free_throws_made", "fta": "free_throws_attempted"}
JUDGED = (2023, 2024, 2025)
_N = NormalDist()


# ----------------------------------------------------------------------------------------------------------- data
def _minutes(x) -> float:
    if x is None or (isinstance(x, float) and math.isnan(x)) or x == "":
        return 0.0
    s = str(x)
    if ":" in s:
        a, b = s.split(":")[:2]
        return float(a) + float(b) / 60.0
    return float(s)


def load_box(root: Path, seasons) -> pd.DataFrame:
    """Regular-season player box rows with minutes > 0 for the given seasons, dated from the schedule table."""
    out = []
    for s in seasons:
        if s in JUDGED and not load_box.allow_judged:
            raise PermissionError(f"season {s} is judged; pass --final (PREREG addendum A9)")
        b = pd.read_parquet(Path(root) / "raw" / "player_box" / f"player_box_{s}.parquet")
        sc = pd.read_parquet(Path(root) / "raw" / "schedule" / f"schedule_{s}.parquet")
        b = b[b["season_type_id"].astype(str) == "2"].copy()
        b["game_id"] = b["game_id"].astype(str)
        dates = sc.drop_duplicates("game_id").set_index(sc.drop_duplicates("game_id")["game_id"].astype(str))["game_date"]
        b["date"] = b["game_id"].map(dates).astype(str)
        b["min"] = b["minutes"].map(_minutes)
        b = b[(b["min"] > 0) & (b["date"] != "nan")]
        r = pd.DataFrame({"season": s, "game_id": b["game_id"], "date": b["date"], "person_id": b["person_id"].astype("int64"),
                          "team_id": b["team_id"].astype("int64"), "min": b["min"].astype(float)})
        for k, c in SRC_COLS.items():
            r[k if k not in ("ftm", "fta") else k] = b[c].astype(float).fillna(0.0)
        out.append(r)
    return pd.concat(out, ignore_index=True)


load_box.allow_judged = False


def data_report(root: Path, seasons) -> list[dict]:
    rep = []
    for s in seasons:
        b = pd.read_parquet(Path(root) / "raw" / "player_box" / f"player_box_{s}.parquet")
        reg = b[b["season_type_id"].astype(str) == "2"]
        played = reg[reg["minutes"].map(_minutes) > 0]
        rep.append(dict(season=s, rows_all=len(b), rows_regular=len(reg), rows_played=len(played), games_regular=reg["game_id"].nunique()))
    return rep


# ------------------------------------------------------------------------------------------------- reliability (A3)
def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 10 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def fisher_pool(rs, ns) -> float:
    rs, ns = np.asarray(rs, float), np.asarray(ns, float)
    ok = ~np.isnan(rs) & (ns > 3)
    if not ok.any():
        return float("nan")
    z = np.arctanh(np.clip(rs[ok], -0.999, 0.999))
    w = ns[ok] - 3
    return float(np.tanh((w * z).sum() / w.sum()))


def spearman_brown(r_half: float) -> float:
    return 2 * r_half / (1 + r_half) if r_half > -0.99 else float("nan")


def k_from_r(r_half: float, size: float) -> float:
    rf = min(max(spearman_brown(r_half), 0.05), 0.999)
    return float(size * (1 - rf) / rf)


def _halves(box: pd.DataFrame) -> pd.DataFrame:
    """Per player-season (all teams): sums for odd / even games (date order) and totals."""
    b = box.sort_values(["person_id", "season", "date", "game_id"]).copy()
    b["par"] = b.groupby(["person_id", "season"]).cumcount() % 2
    cols = ["min", "points", "rebounds", "assists", "threes", "blocks", "steals", "ftm", "fta"]
    b["g"] = 1.0
    agg = b.groupby(["person_id", "season", "par"])[cols + ["g"]].sum().unstack("par")
    agg.columns = [f"{c}_{p}" for c, p in agg.columns]
    return agg.dropna().reset_index()


def reliability(box: pd.DataFrame, seasons, stat: str, boot: int = 500, seed: int = 20261121) -> dict:
    """Split-half (A3) for per-minute stats ('points'..'steals'), 'mpg' (minutes per game) and 'ft_pct' (per attempt, A8)."""
    h = _halves(box[box["season"].isin(seasons)])
    if stat == "mpg":
        h = h[(h["min_0"] + h["min_1"]) >= QUAL_MIN]
        x0, x1 = h["min_0"] / h["g_0"], h["min_1"] / h["g_1"]
        size = float(((h["g_0"] + h["g_1"])).mean())
    elif stat == "ft_pct":
        h = h[(h["fta_0"] + h["fta_1"]) >= 200]
        h = h[(h["fta_0"] > 0) & (h["fta_1"] > 0)]
        x0, x1 = h["ftm_0"] / h["fta_0"], h["ftm_1"] / h["fta_1"]
        size = float((h["fta_0"] + h["fta_1"]).mean())
    else:
        h = h[(h["min_0"] + h["min_1"]) >= QUAL_MIN]
        x0, x1 = h[f"{stat}_0"] / h["min_0"], h[f"{stat}_1"] / h["min_1"]
        size = float((h["min_0"] + h["min_1"]).mean())
    se = h["season"].to_numpy()
    a, b = x0.to_numpy(), x1.to_numpy()

    def pooled(idx):
        rs, ns = [], []
        for s in np.unique(se[idx]):
            m = idx[se[idx] == s]
            rs.append(_pearson(a[m], b[m])); ns.append(len(m))
        return fisher_pool(rs, ns)

    allidx = np.arange(len(a))
    r_half = pooled(allidx)
    rng = np.random.default_rng(seed)
    ks, rs_b = [], []
    for _ in range(boot):
        rb = pooled(rng.integers(0, len(a), len(a)))
        if not math.isnan(rb):
            rs_b.append(rb); ks.append(k_from_r(rb, size))
    out = dict(stat=stat, n_player_seasons=int(len(a)), r_split_half=r_half, r_full=spearman_brown(r_half), size=size,
               k=k_from_r(r_half, size))
    if ks:
        out.update(r_lo=float(np.percentile(rs_b, 5)), r_hi=float(np.percentile(rs_b, 95)),
                   k_lo=float(np.percentile(ks, 5)), k_hi=float(np.percentile(ks, 95)))
    return out


def year_to_year(box: pd.DataFrame, seasons, stat: str) -> float:
    """Descriptive: Pearson of full-season rates, player-seasons >= QUAL_MIN in t and t+1, Fisher-pooled over t."""
    g = box[box["season"].isin(seasons)].groupby(["person_id", "season"])[["min", "points", "rebounds", "assists", "threes", "blocks",
                                                                          "steals", "ftm", "fta"]].sum().reset_index()
    if stat == "ft_pct":
        g = g[g["fta"] >= 200]; g["x"] = g["ftm"] / g["fta"]
    else:
        g = g[g["min"] >= QUAL_MIN]; g["x"] = g[stat] / g["min"]
    nxt = g[["person_id", "season", "x"]].copy(); nxt["season"] -= 1
    m = g.merge(nxt, on=["person_id", "season"], suffixes=("", "_n"))
    rs, ns = [], []
    for _, d in m.groupby("season"):
        rs.append(_pearson(d["x"].to_numpy(), d["x_n"].to_numpy())); ns.append(len(d))
    return fisher_pool(rs, ns)


# ------------------------------------------------------------------------------------------ player-season tables
def player_seasons(box: pd.DataFrame) -> pd.DataFrame:
    g = box.groupby(["person_id", "season"]).agg(min=("min", "sum"), games=("min", "size"), **{s: (s, "sum") for s in STATS}).reset_index()
    g["mpg"] = g["min"] / g["games"]
    g["band"] = np.digitize(g["mpg"].to_numpy(), BAND_CUTS)
    return g


def league_rates(ps: pd.DataFrame) -> dict:
    """(season, band) -> {stat: total stat / total minutes} over that season's player-seasons (A1)."""
    out = {}
    for (s, bnd), d in ps.groupby(["season", "band"]):
        m = d["min"].sum()
        out[(int(s), int(bnd))] = {st: float(d[st].sum() / m) for st in STATS}
    return out


# --------------------------------------------------------------------------------------- units (EXP-047 eligibility)
def build_units(box: pd.DataFrame, seasons) -> pd.DataFrame:
    """One row per eligible player-game (PREREG §3): prior sums on this team this season, and the actual stats."""
    rows = []
    for (season, team), g in box[box["season"].isin(seasons)].groupby(["season", "team_id"]):
        tg = g[["date", "game_id"]].drop_duplicates().sort_values(["date", "game_id"]).reset_index(drop=True)
        gi = {gid: j for j, gid in enumerate(tg["game_id"])}
        pl = sorted(g["person_id"].unique())
        pi = {p: i for i, p in enumerate(pl)}
        P, G = len(pl), len(tg)
        played = np.zeros((P, G)); val = {c: np.zeros((P, G)) for c in ["min"] + STATS}
        ii = g["person_id"].map(pi).to_numpy(); jj = g["game_id"].map(gi).to_numpy()
        played[ii, jj] = 1.0
        for c in val:
            val[c][ii, jj] = g[c].to_numpy()
        csum = {c: np.cumsum(v, axis=1) - v for c, v in val.items()}      # strictly before game j (one game per team-day)
        cn = np.cumsum(played, axis=1) - played
        pids = np.array(pl)
        for j in range(G):
            n = cn[:, j]
            with np.errstate(invalid="ignore", divide="ignore"):
                mm = np.where(n > 0, csum["min"][:, j] / np.maximum(n, 1), 0.0)
            el = np.where((n >= MIN_PRIOR_GAMES) & (mm >= MIN_MPG))[0]
            if not len(el):
                continue
            order = el[np.lexsort((pids[el], -mm[el]))][:ROTATION]
            for i in order:
                if played[i, j] == 1.0:
                    r = dict(season=int(season), game_id=tg["game_id"][j], team_id=int(team), person_id=int(pids[i]), n=int(n[i]),
                             M=float(csum["min"][i, j]))
                    for s in STATS:
                        r[f"prior_{s}"] = float(csum[s][i, j]); r[f"y_{s}"] = float(val[s][i, j])
                    rows.append(r)
    u = pd.DataFrame(rows)
    u["mbar"] = u["M"] / u["n"]
    return u


# ------------------------------------------------------------------------------------------------------ the two inputs
def attach_prev(units: pd.DataFrame, ps: pd.DataFrame, lr: dict) -> pd.DataFrame:
    """Previous-season (any team) totals per unit + league band rates from the previous season only."""
    prev = ps.copy(); prev["season"] += 1
    prev = prev.rename(columns={"min": "pm", "games": "pg", "mpg": "pmpg", **{s: f"p_{s}" for s in STATS}})
    u = units.merge(prev[["person_id", "season", "pm", "pg", "pmpg", "band"] + [f"p_{s}" for s in STATS]], on=["person_id", "season"], how="left")
    u["has_prev"] = u["pm"].notna()
    cur_band = np.digitize(u["mbar"].to_numpy(), BAND_CUTS)
    u["band_u"] = np.where(u["has_prev"], u["band"].fillna(0).astype(int), cur_band)
    for s in STATS:
        league = np.array([lr.get((int(se) - 1, int(b)), {}).get(s, np.nan) for se, b in zip(u["season"], u["band_u"])])
        u[f"lg_{s}"] = league
    return u.dropna(subset=[f"lg_{s}" for s in STATS]).reset_index(drop=True)


def mus(u: pd.DataFrame, kvec: dict, kmin: float) -> dict:
    """Per stat: control, challenger, decomposition identity, rate-only, minutes-only (A4)."""
    m_prev = u["pm"].fillna(0.0).to_numpy()
    n, mbar, hp = u["n"].to_numpy(), u["mbar"].to_numpy(), u["has_prev"].to_numpy()
    shrunk_min = np.where(hp, (n * mbar + kmin * u["pmpg"].fillna(0.0).to_numpy()) / (n + kmin), mbar)
    out = {}
    for s in STATS:
        k = kvec[s]
        r_obs = u[f"prior_{s}"].to_numpy() / u["M"].to_numpy()
        r_prev = np.where(hp, u[f"p_{s}"].fillna(0.0).to_numpy() / np.where(m_prev > 0, m_prev, 1.0), 0.0)
        lg = u[f"lg_{s}"].to_numpy()
        prior = np.where(hp, (m_prev * r_prev + PSEUDO_LEAGUE_MIN * lg) / (m_prev + PSEUDO_LEAGUE_MIN), lg)
        sr = (u["M"].to_numpy() * r_obs + k * prior) / (u["M"].to_numpy() + k)
        out[s] = dict(control=u[f"prior_{s}"].to_numpy() / n, challenger=sr * shrunk_min, raw_identity=r_obs * mbar,
                      rate_only=sr * mbar, minutes_only=r_obs * shrunk_min)
    return {s: {a: np.maximum(v, MU_FLOOR) for a, v in d.items()} for s, d in out.items()}


# --------------------------------------------------------------------------------------------- distribution layer
def nb_sf(mu: np.ndarray, r: float, thresholds) -> np.ndarray:
    """P(Y >= t) for t in thresholds; NB with var = mu + mu^2 / r."""
    p = r / (r + mu)
    return np.column_stack([sps.nbinom.sf(t - 1, r, p) for t in thresholds])


def fit_dispersion(mu: np.ndarray, y: np.ndarray) -> float:
    def nll(lr):
        r = math.exp(lr)
        return -float(sps.nbinom.logpmf(y, r, r / (r + mu)).sum())
    return float(math.exp(minimize_scalar(nll, bounds=(math.log(0.05), math.log(1e5)), method="bounded").x))


def score_rows(p: np.ndarray, y: np.ndarray, thresholds) -> tuple[np.ndarray, np.ndarray]:
    o = (y[:, None] >= np.asarray(thresholds)[None, :]).astype(float)
    p = np.clip(p, P_CLIP, 1 - P_CLIP)
    return -(o * np.log(p) + (1 - o) * np.log(1 - p)), (p - o) ** 2


# ------------------------------------------------------------------------------------------------------ bootstrap (A7)
def game_bootstrap(sums: np.ndarray, counts: np.ndarray, b: int = 2000, seed: int = 20261121, alpha: float = 0.10) -> dict:
    """sums, counts: (games, columns). Resample whole games; returns mean, interval, one-sided p (mean<=0) per column set.
    The same resampled games serve every column, so linear combinations (pooled = sum of columns) stay consistent."""
    rng = np.random.default_rng(seed)
    G = sums.shape[0]
    W = np.empty((b, G), dtype=np.float32)
    for i in range(b):
        W[i] = np.bincount(rng.integers(0, G, G), minlength=G)
    return dict(S=W @ sums.astype(np.float64), C=W @ counts.astype(np.float64), alpha=alpha, b=b)


def summarise(boot: dict, cols, full_sum: float, full_cnt: float) -> dict:
    S = boot["S"][:, cols].sum(axis=1); C = boot["C"][:, cols].sum(axis=1)
    m = S / C
    a = boot["alpha"]
    return dict(D=full_sum / full_cnt, lo=float(np.percentile(m, 100 * a / 2)), hi=float(np.percentile(m, 100 * (1 - a / 2))),
                p=float((np.sum(m <= 0) + 1) / (boot["b"] + 1)), n_rows=int(full_cnt))


# ------------------------------------------------------------------------------------------------------------ pipeline
def _bh(ps, q=0.10):
    m = len(ps); order = sorted(range(m), key=lambda i: ps[i]); kmax = 0
    for rank, i in enumerate(order, 1):
        if ps[i] <= q * rank / m:
            kmax = rank
    keep = set(order[:kmax])
    return [i in keep for i in range(m)]


def run_pipeline(box: pd.DataFrame, train, judged, b: int = 2000, seed: int = 20261121, reliab_boot: int = 200) -> dict:
    train, judged = sorted(train), sorted(judged)
    have = set(box["season"].unique())
    train_fit = [s for s in train if s - 1 in have]                     # A2
    ps = player_seasons(box); lr = league_rates(ps)
    # --- reliability, fitted on training seasons only
    rel = {s: reliability(box, train, s, boot=reliab_boot) for s in STATS + ["blocks", "steals", "mpg", "ft_pct"]}
    for s in STATS + ["blocks", "steals", "ft_pct"]:
        rel[s]["r_year_to_year"] = year_to_year(box, train, s)
    kvec = {s: rel[s]["k"] for s in STATS}; kmin = rel["mpg"]["k"]
    # --- units
    tu = attach_prev(build_units(box, train_fit), ps, lr)
    ju = attach_prev(build_units(box, judged), ps, lr)
    arms = ["control", "challenger", "rate_only", "minutes_only"]
    tm, jm = mus(tu, kvec, kmin), mus(ju, kvec, kmin)
    disp = {s: {a: fit_dispersion(tm[s][a], tu[f"y_{s}"].to_numpy()) for a in arms} for s in STATS}
    # --- score judged units
    games = {g: i for i, g in enumerate(ju["game_id"].unique())}
    gi = ju["game_id"].map(games).to_numpy()
    strat = np.select([(ju["n"] >= lo) & (ju["n"] <= hi) for _, lo, hi in STRATA], list(range(len(STRATA))), -1)
    nG, nS = len(games), len(STRATA)
    ncols = len(STATS) * (1 + nS)                       # per stat: [all, stratum0..2]
    D = {a: np.zeros((nG, ncols)) for a in arms[1:]}; Cn = np.zeros((nG, ncols))
    brier = {s: {a: 0.0 for a in arms} for s in STATS}; ll_tot = {s: {a: 0.0 for a in arms} for s in STATS}; rows_stat = {s: 0 for s in STATS}
    for si, s in enumerate(STATS):
        y = ju[f"y_{s}"].to_numpy(); th = LADDER[s]; T = len(th)
        res = {}
        for a in arms:
            p = nb_sf(jm[s][a], disp[s][a], th)
            res[a] = score_rows(p, y, th)
        for a in arms:
            brier[s][a] = float(res[a][1].sum()); ll_tot[s][a] = float(res[a][0].sum())
        rows_stat[s] = len(y) * T
        for a in arms[1:]:
            d = (res["control"][0] - res[a][0]).sum(axis=1)       # per unit, summed over thresholds
            np.add.at(D[a][:, si * (1 + nS)], gi, d)
            for k in range(nS):
                np.add.at(D[a][:, si * (1 + nS) + 1 + k], gi, np.where(strat == k, d, 0.0))
        np.add.at(Cn[:, si * (1 + nS)], gi, T)
        for k in range(nS):
            np.add.at(Cn[:, si * (1 + nS) + 1 + k], gi, np.where(strat == k, T, 0))
    boot = {a: game_bootstrap(D[a], Cn, b, seed) for a in arms[1:]}
    col_all = [si * (1 + nS) for si in range(len(STATS))]
    col_stat = {s: [si * (1 + nS)] for si, s in enumerate(STATS)}
    col_strat = {STRATA[k][0]: [si * (1 + nS) + 1 + k for si in range(len(STATS))] for k in range(nS)}

    def block(a, cols):
        return summarise(boot[a], cols, float(D[a][:, cols].sum()), float(Cn[:, cols].sum()))

    out = dict(train=train, train_fit=train_fit, judged=judged, n_units_train=int(len(tu)), n_units_judged=int(len(ju)),
               n_games_judged=int(nG), k=kvec, k_min=kmin, reliability=rel, dispersion=disp, bootstrap=dict(b=b, seed=seed, level=0.90))
    out["pooled"] = {a: block(a, col_all) for a in arms[1:]}
    out["per_stat"] = {a: {s: block(a, col_stat[s]) for s in STATS} for a in arms[1:]}
    ch = out["per_stat"]["challenger"]
    bh = _bh([ch[s]["p"] for s in STATS], 0.10)
    for s, flag in zip(STATS, bh):
        ch[s]["bh_q10"] = bool(flag)
    out["by_stratum"] = {a: {k: block(a, c) for k, c in col_strat.items()} for a in arms[1:]}
    out["stratum_by_stat"] = {s: {STRATA[k][0]: summarise(boot["challenger"], [si * (1 + nS) + 1 + k], float(D["challenger"][:, si * (1 + nS) + 1 + k].sum()),
                                                          float(Cn[:, si * (1 + nS) + 1 + k].sum())) for k in range(nS)} for si, s in enumerate(STATS)}
    out["score"] = {s: {a: dict(logloss=ll_tot[s][a] / rows_stat[s], brier=brier[s][a] / rows_stat[s]) for a in arms} for s in STATS}
    out["identity_max_abs_diff"] = float(max(np.abs(jm[s]["control"] - jm[s]["raw_identity"]).max() for s in STATS))
    out["prior_games_stratum_units"] = {STRATA[k][0]: int((strat == k).sum()) for k in range(nS)}
    # verdict (PREREG §5)
    pooled = out["pooled"]["challenger"]
    npos = sum(1 for s in STATS if ch[s]["D"] > 0)
    gsum = D["challenger"][:, col_all].sum(axis=1); gcnt = Cn[:, col_all].sum(axis=1)
    sd_game = float(np.std(gsum / gcnt, ddof=1))
    z = _N.inv_cdf(0.95) + _N.inv_cdf(0.80)
    out["power"] = dict(sd_game_mean_diff=sd_game, n_games=int(nG), mde=mde_paired(sd_game, nG, alpha=0.05, power=0.80),
                        n_games_needed_for_observed_D=(float((z * sd_game / pooled["D"]) ** 2) if pooled["D"] > 0 else None))
    out["n_stats_positive"] = npos
    if pooled["D"] <= 0 or npos < 3:
        out["verdict"] = "NOT SUPPORTED"
    elif pooled["lo"] > 0:
        out["verdict"] = "SUPPORTED"
    else:
        out["verdict"] = "UNDERPOWERED"
    return out


# ------------------------------------------------------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("exp_output/NBA_EVENTS"))
    ap.add_argument("--final", action="store_true", help="load and score the judged seasons 2023-2025 (run once)")
    ap.add_argument("--smoke", action="store_true", help="development smoke on training seasons only: fit 2016-2020, check 2021-2022")
    ap.add_argument("--out", type=Path, default=Path("12_EXPLORATORY/pam_stability/results.json"))
    ap.add_argument("--b", type=int, default=2000)
    a = ap.parse_args(argv)
    if a.final == a.smoke:
        ap.error("pass exactly one of --final or --smoke")
    if a.final:
        load_box.allow_judged = True
        train, judged = list(range(2016, 2023)), list(JUDGED)
    else:
        train, judged = list(range(2016, 2021)), [2021, 2022]
    seasons = train + judged
    box = load_box(a.root, seasons)
    res = run_pipeline(box, train, judged, b=a.b)
    res["data_report"] = data_report(a.root, seasons)
    res["columns_used"] = SRC_COLS | {"minutes": "minutes", "date": "schedule.game_date", "team": "team_id", "player": "person_id"}
    path = a.out if a.final else a.out.with_name("smoke_results.json")
    with open(safe_out(path.resolve()), "w") as fh:
        fh.write(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({k: res[k] for k in ("verdict", "pooled", "n_stats_positive", "k", "k_min")}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
