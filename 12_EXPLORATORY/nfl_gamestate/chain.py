"""EXPLORATORY -- NFL game-state Markov chain: play-level absorbing chain -> drive banks -> full-game simulation (W89.4).

Not a verdict. Plan frozen in PLAN.md before any held-out score was read. numpy/pandas only; no I/O except load_plays().

Layers (each a pure function of its inputs; estimation sees earlier seasons only):
  1. estimate_chain(plays)  play states (down x distance bucket x field-position bucket) -> next state | drive outcome.
  2. TiltedChain            one scalar theta per (offense, opponent) pairing tilts every row toward / away from valuable
                            destinations (quant.absorbing.exp_tilt, value = expected drive points from the chain itself).
  3. build_banks            simulate drives from each start bucket at each theta -> (outcome, last bucket, seconds).
  4. simulate_games         resample drives from the banks, alternate possessions, run the clock through two halves and OT.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from prediction_market_bot.quant import absorbing as A  # noqa: E402

DIST_EDGES = [2, 5, 9, 10]             # ydstogo buckets: <=2, 3-5, 6-9, 10, 11+
YL_EDGES = [5, 10, 20, 35, 50, 65, 80]  # yardline_100 buckets: <=5, 6-10, 11-20, 21-35, 36-50, 51-65, 66-80, 81+
ND, NY = len(DIST_EDGES) + 1, len(YL_EDGES) + 1
S = 4 * ND * NY
CLASSES = ["TD", "FG", "SAF", "OPP_TD", "MISS", "PUNT", "TURN", "TOD"]
CI = {c: i for i, c in enumerate(CLASSES)}
NA = len(CLASSES)
RESULT_MAP = {"Touchdown": "TD", "Field goal": "FG", "Safety": "SAF", "Opp touchdown": "OPP_TD", "Missed field goal": "MISS",
              "Punt": "PUNT", "Turnover": "TURN", "Turnover on downs": "TOD"}
# nominal points to the OFFENSE of the drive (TD counted at its mean value elsewhere); used only for values and ratings
NOMINAL = {"TD": 6.95, "FG": 3.0, "SAF": -2.0, "OPP_TD": -6.95}
ABS_REWARD = np.array([NOMINAL.get(c, 0.0) for c in CLASSES])
FLIP = np.array([c != "OPP_TD" for c in CLASSES])   # possession alternates except after a defensive touchdown
SCORE_START = {"TD", "FG", "SAF", "OPP_TD"}            # next drive starts from a kickoff / free kick


def dist_b(d):
    return np.searchsorted(DIST_EDGES, np.minimum(d, 99), side="left")


def yl_b(y):
    return np.searchsorted(YL_EDGES, y, side="left")


def sid(down, dist, yl):
    return (((np.asarray(down) - 1) * ND + dist_b(dist)) * NY + yl_b(yl)).astype(int)


YL_REP = [3, 8, 15, 28, 43, 58, 73, 90]   # representative yardline_100 inside each bucket


def start_state(yl_bucket):
    """First-and-ten at a representative yardline of the bucket."""
    return int(sid(1, 10, YL_REP[yl_bucket]))


def load_plays(pbp_paths: dict) -> pd.DataFrame:
    cols = ["game_id", "season", "season_type", "fixed_drive", "fixed_drive_result", "posteam", "defteam", "home_team", "away_team",
            "down", "ydstogo", "yardline_100", "play_type", "game_seconds_remaining", "extra_point_result",
            "two_point_conv_result", "game_date", "play_deleted"]
    out = []
    for s, p in sorted(pbp_paths.items()):
        d = pd.read_parquet(p)
        d = d[[c for c in cols if c in d.columns]].copy()
        d["season"] = s
        out.append(d)
    return pd.concat(out, ignore_index=True)


@dataclass
class Chain:
    Q: np.ndarray            # S x S
    R: np.ndarray            # S x NA
    T: np.ndarray            # S x (S+NA) mean seconds consumed by the play (incl. time to next snap / next drive's first snap)
    counts: np.ndarray       # visits per state (before back-off)
    next_start: dict         # (class, last yl bucket) -> np.ndarray of next-drive yardline_100 (offense's own perspective)
    ko_start: np.ndarray     # start yardlines after a score / opening kickoff
    td_pts: np.ndarray       # P(6), P(7), P(8) given a touchdown
    start_freq: np.ndarray   # empirical distribution of drive-start yardline bucket
    drive_len: float
    n_plays: int
    n_drives: int


def _prep(plays: pd.DataFrame) -> pd.DataFrame:
    p = plays[plays.play_type.isin(["pass", "run", "punt", "field_goal", "no_play"]) & plays.down.notna()
              & plays.posteam.notna() & plays.yardline_100.notna() & plays.fixed_drive.notna()].copy()
    if "play_deleted" in p.columns:
        p = p[p.play_deleted.fillna(0) == 0]
    p = p.sort_values(["game_id", "game_seconds_remaining"], ascending=[True, False], kind="stable").reset_index(drop=True)
    p["state"] = sid(p.down.astype(int), p.ydstogo.fillna(10).astype(int), p.yardline_100.astype(int))
    p["ylb"] = yl_b(p.yardline_100.astype(int))
    g = p.groupby(["game_id", "fixed_drive"], sort=False)
    p["last"] = g.cumcount(ascending=False) == 0
    p["next_state"] = g.state.shift(-1)
    p["gsr_next"] = p.groupby("game_id", sort=False).game_seconds_remaining.shift(-1)
    gsr = p.game_seconds_remaining
    floor = np.where(gsr > 1800, 1800.0, 0.0)           # a clock gap never crosses the half boundary
    p["dt"] = (gsr - np.maximum(p.gsr_next.fillna(0.0), floor)).clip(0, 150)
    return p


def estimate_chain(plays: pd.DataFrame, min_visits: int = 15) -> Chain:
    p = _prep(plays)
    cls = p.fixed_drive_result.map(RESULT_MAP)
    inner = ~p["last"]
    term = p["last"] & cls.notna()
    cnt = np.zeros((S, S + NA))
    tsum = np.zeros((S, S + NA))
    a = p[inner & p.next_state.notna()]
    np.add.at(cnt, (a.state.to_numpy(), a.next_state.astype(int).to_numpy()), 1)
    np.add.at(tsum, (a.state.to_numpy(), a.next_state.astype(int).to_numpy()), a.dt.to_numpy())
    b = p[term]
    cc = cls[term].map(CI).astype(int).to_numpy()
    np.add.at(cnt, (b.state.to_numpy(), S + cc), 1)
    np.add.at(tsum, (b.state.to_numpy(), S + cc), b.dt.to_numpy())
    visits = cnt.sum(1)
    # back-off: a sparse row borrows the row of the nearest field-position bucket with enough visits (same down, distance)
    P = cnt.copy()
    Tm = np.divide(tsum, cnt, out=np.zeros_like(tsum), where=cnt > 0)
    for s in range(S):
        if visits[s] >= min_visits:
            continue
        dn, rem = divmod(s, ND * NY)
        db, yb = divmod(rem, NY)
        cand = sorted(range(NY), key=lambda y: abs(y - yb))
        donor = next((dn * ND * NY + db * NY + y for y in cand if visits[dn * ND * NY + db * NY + y] >= min_visits), None)
        if donor is None:
            donor = next((dn * ND * NY + d2 * NY + yb for d2 in sorted(range(ND), key=lambda d: abs(d - db))
                          if visits[dn * ND * NY + d2 * NY + yb] >= min_visits), None)
        if donor is not None:
            P[s], Tm[s] = cnt[donor], Tm[donor]
    rowsum = P.sum(1)
    dead = rowsum == 0
    P[dead, S + CI["PUNT"]] = 1.0                       # a never-visited state ends the drive (punt) -- keeps rows stochastic
    rowsum = P.sum(1)
    P = P / rowsum[:, None]
    rowmean = np.where(cnt.sum(1) > 0, tsum.sum(1) / np.maximum(cnt.sum(1), 1), 6.0)
    Tm = np.where(Tm > 0, Tm, rowmean[:, None])
    # drive starts: first scrimmage play of each drive; next-drive start by terminal class of the previous drive
    first = p.groupby(["game_id", "fixed_drive"], sort=False).agg(yl=("yardline_100", "first"), res=("fixed_drive_result", "first"),
                                                                  lastyl=("ylb", "last"), gid=("game_id", "first")).reset_index()
    first["cls"] = first.res.map(RESULT_MAP)
    first["next_yl"] = first.groupby("game_id", sort=False).yl.shift(-1)
    nxt = first[first.cls.notna() & first.next_yl.notna()]
    ns = {}
    ko = []
    for (c, lb), g in nxt.groupby(["cls", "lastyl"]):
        if c in SCORE_START:
            continue
        ns[(CI[c], int(lb))] = g.next_yl.to_numpy(float)
    for c in CLASSES:
        pool = nxt[nxt.cls == c].next_yl.to_numpy(float)
        ns[(CI[c], -1)] = pool
    ko = nxt[nxt.cls.isin(SCORE_START)].next_yl.to_numpy(float)
    # touchdown conversion mix from the PAT / two-point plays of touchdown drives
    td_drives = first[first.cls == "TD"][["game_id", "fixed_drive"]]
    allp = plays[plays.fixed_drive.notna()].merge(td_drives, on=["game_id", "fixed_drive"])
    xp_good = int((allp.extra_point_result == "good").sum())
    xp_bad = int(allp.extra_point_result.isin(["failed", "blocked"]).sum())
    tp_ok = int((allp.two_point_conv_result == "success").sum())
    tp_no = int((allp.two_point_conv_result == "failure").sum())
    tot = xp_good + xp_bad + tp_ok + tp_no
    td_pts = (np.array([(xp_bad + tp_no) / tot, xp_good / tot, tp_ok / tot]) if tot >= 50
              else np.array([0.04, 0.93, 0.03]))                                # P(6), P(7), P(8); frozen-engine mix if no data
    sf = np.bincount(yl_b(first.yl.astype(int).to_numpy()), minlength=NY).astype(float)
    return Chain(Q=P[:, :S], R=P[:, S:], T=Tm, counts=visits, next_start=ns, ko_start=ko, td_pts=td_pts,
                 start_freq=sf / sf.sum(), drive_len=float(len(p)) / max(len(first), 1), n_plays=len(p), n_drives=len(first))


def values(ch: Chain) -> np.ndarray:
    """Expected drive points to the offense from each play state (absorption algebra)."""
    return A.expected_reward(ch.Q, ch.R, ABS_REWARD)


class TiltedChain:
    def __init__(self, ch: Chain, theta: float):
        self.ch, self.theta = ch, theta
        v = values(ch)
        self.Q, self.R = A.exp_tilt(ch.Q, ch.R, v, ABS_REWARD, theta)

    def cum(self):
        return np.cumsum(np.hstack([self.Q, self.R]), axis=1)

    def drive_points(self) -> np.ndarray:
        return A.expected_reward(self.Q, self.R, ABS_REWARD)


def simulate_drives(tc: TiltedChain, s0: int, n: int, rng) -> tuple:
    """n drives from state index s0 -> (class idx, last-play yl bucket, seconds)."""
    cum = tc.cum()
    T = tc.ch.T
    st = np.full(n, s0)
    cls = np.full(n, -1)
    last_yb = np.zeros(n, int)
    secs = np.zeros(n)
    act = np.ones(n, bool)
    for _ in range(80):
        if not act.any():
            break
        idx = np.nonzero(act)[0]
        u = rng.random(len(idx))
        rows = cum[st[idx]]
        dest = np.minimum((rows < u[:, None]).sum(1), S + NA - 1)
        secs[idx] += T[st[idx], dest]
        term = dest >= S
        last_yb[idx[term]] = st[idx[term]] % NY
        cls[idx[term]] = dest[term] - S
        act[idx[term]] = False
        st[idx[~term]] = dest[~term]
    cls[cls < 0] = CI["PUNT"]
    return cls, last_yb, secs


def build_banks(ch: Chain, thetas: np.ndarray, per: int, seed: int):
    """banks[i] = dict(cls, lastyb, secs) arrays of shape (NY, per) for theta i; plus expected drive points at the empirical start mix."""
    rng = np.random.default_rng(seed)
    out, epd = [], []
    for th in thetas:
        tc = TiltedChain(ch, float(th))
        c = np.zeros((NY, per), int)
        l = np.zeros((NY, per), int)
        t = np.zeros((NY, per))
        for yb in range(NY):
            c[yb], l[yb], t[yb] = simulate_drives(tc, start_state(yb), per, rng)
        out.append(dict(cls=c, lastyb=l, secs=t))
        V = tc.drive_points()
        epd.append(float(sum(ch.start_freq[yb] * V[start_state(yb)] for yb in range(NY))))
    return out, np.array(epd)


def _sample_start(ch: Chain, cls, lastyb, rng):
    """Next drive's start yardline bucket given the previous class / last-play bucket."""
    n = len(cls)
    yl = np.zeros(n)
    for c in range(NA):
        m = cls == c
        if not m.any():
            continue
        if CLASSES[c] in SCORE_START:
            yl[m] = rng.choice(ch.ko_start, m.sum())
            continue
        for lb in np.unique(lastyb[m]):
            mm = m & (lastyb == lb)
            pool = ch.next_start.get((c, int(lb)))
            if pool is None or len(pool) < 15:
                pool = ch.next_start[(c, -1)]
            yl[mm] = rng.choice(pool, mm.sum())
    return yl_b(np.clip(yl, 1, 99).astype(int))


def simulate_games(ch: Chain, banks, thetas: np.ndarray, th_home: float, th_away: float, n: int, seed: int,
                   keep_drives: bool = False) -> dict:
    """n full games for one matchup. th_* = tilt of that side's OFFENSE. Returns home/away points and counts."""
    rng = np.random.default_rng(seed)
    ti = [int(np.argmin(np.abs(thetas - th_home))), int(np.argmin(np.abs(thetas - th_away)))]   # side 0 = home, 1 = away
    per = banks[0]["cls"].shape[1]
    pts = np.zeros((n, 2))
    nd = np.zeros(n, int)
    first_recv = rng.integers(0, 2, n)
    off = first_recv.copy()
    half = np.zeros(n, int)
    clock = np.full(n, 1800.0)
    ot = np.zeros(n, bool)
    ot_poss = np.zeros(n, int)
    done = np.zeros(n, bool)
    sb = yl_b(np.clip(rng.choice(ch.ko_start, n), 1, 99).astype(int))
    tdp = ch.td_pts
    for _ in range(90):
        act = ~done
        if not act.any():
            break
        j = rng.integers(0, per, n)
        cls = np.zeros(n, int)
        lyb = np.zeros(n, int)
        sec = np.zeros(n)
        for side in (0, 1):
            m = act & (off == side)
            if m.any():
                b = banks[ti[side]]
                cls[m], lyb[m], sec[m] = b["cls"][sb[m], j[m]], b["lastyb"][sb[m], j[m]], b["secs"][sb[m], j[m]]
        fits = sec <= clock
        gain = np.zeros(n)
        for c in (CI["TD"],):
            m = act & fits & (cls == c)
            gain[m] = rng.choice([6.0, 7.0, 8.0], m.sum(), p=tdp)
        gain[act & fits & (cls == CI["FG"])] = 3.0
        sc_def = act & fits & (cls == CI["OPP_TD"])
        sf = act & fits & (cls == CI["SAF"])
        pts[np.arange(n)[act & fits & (gain > 0)], off[act & fits & (gain > 0)]] += gain[act & fits & (gain > 0)]
        if sc_def.any():
            pts[np.nonzero(sc_def)[0], 1 - off[sc_def]] += rng.choice([6.0, 7.0, 8.0], sc_def.sum(), p=tdp)
        if sf.any():
            pts[np.nonzero(sf)[0], 1 - off[sf]] += 2.0
        nd[act] += 1
        # clock
        clock = np.where(act, np.where(fits, clock - sec, 0.0), clock)
        # OT: a team's first possession ends the game on a TD; sudden death after both have had the ball
        otm = act & ot
        ot_poss[otm] += 1
        td_scored = otm & fits & (cls == CI["TD"])
        any_score = otm & fits & np.isin(cls, [CI["TD"], CI["FG"], CI["SAF"], CI["OPP_TD"]])
        decided = td_scored | (otm & (ot_poss >= 2) & any_score) | (otm & fits & (cls == CI["OPP_TD"]))
        decided |= otm & (ot_poss >= 2) & (np.abs(pts[:, 0] - pts[:, 1]) > 0) & (ot_poss % 2 == 0)
        done |= decided
        # next drive
        nsb = _sample_start(ch, cls, lyb, rng)
        flip = FLIP[cls]
        off = np.where(act, np.where(flip, 1 - off, off), off)
        sb = np.where(act, nsb, sb)
        # half / regulation end
        ended = act & ~done & ~fits & ~ot
        # clock exhausted this half
        h1 = ended & (half == 0)
        half = np.where(h1, 1, half)
        clock = np.where(h1, 1800.0, clock)
        off = np.where(h1, 1 - first_recv, off)
        sb = np.where(h1, yl_b(np.clip(rng.choice(ch.ko_start, n), 1, 99).astype(int)), sb)
        h2 = ended & (half == 1) & ~h1
        tied = h2 & (pts[:, 0] == pts[:, 1])
        done |= h2 & ~tied
        ot |= tied
        clock = np.where(tied, 600.0, clock)
        ot_poss = np.where(tied, 0, ot_poss)
        off = np.where(tied, rng.integers(0, 2, n), off)
        sb = np.where(tied, yl_b(np.clip(rng.choice(ch.ko_start, n), 1, 99).astype(int)), sb)
        done |= ot & ~tied & act & ~fits & ~done        # OT clock expired: tie stands
        # a drive that exactly exhausts the half
        zero = act & ~done & (clock <= 0) & fits & ~ot
        half_roll = zero & (half == 0)
        half = np.where(half_roll, 1, half)
        clock = np.where(half_roll, 1800.0, clock)
        off = np.where(half_roll, 1 - first_recv, off)
        end2 = zero & (half == 1) & ~half_roll
        t2 = end2 & (pts[:, 0] == pts[:, 1])
        done |= end2 & ~t2
        ot |= t2
        clock = np.where(t2, 600.0, clock)
        ot_poss = np.where(t2, 0, ot_poss)
    return dict(home=pts[:, 0], away=pts[:, 1], n_drives=nd, ot=ot, unfinished=int((~done).sum()))
