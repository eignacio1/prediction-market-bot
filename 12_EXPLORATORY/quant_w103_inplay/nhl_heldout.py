"""W103.3 Part B: NHL jump-process held-out test. Run: /usr/bin/python3 nhl_heldout.py <NHL_EVENTS dir> <out_json, relative to 12_EXPLORATORY/>

Train 2021-2024 (season label = STARTING year, 2025 = 2025-26), test 2025 (full 2025-26 regular season).
Pre-game rates are a walk-forward team attack/defence rating (no historical lines exist), a stated proxy.
State multipliers (EV, power play, empty net) are fitted on training seasons only, relative to the overall rate.
"""
import json
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, __file__.rsplit("/12_EXPLORATORY", 1)[0] + "/src")
sys.path.insert(0, __file__.rsplit("/quant_w103_inplay", 1)[0])
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import inplay_nhl as q  # noqa: E402

root, out = sys.argv[1], sys.argv[2]
G, E = [], []
for yr in range(2021, 2026):
    g = pd.read_parquet(f"{root}/games_{yr}.parquet")
    e = pd.read_parquet(f"{root}/events_{yr}.parquet", columns=[
        "game_id", "event_id", "sort_order", "period", "period_type", "time_in_period_s", "type", "owner_is_home",
        "home_skaters", "away_skaters", "home_goalie", "away_goalie"])
    G.append(g[(g.game_type == 2) & g.has_pbp])
    E.append(e)
G = pd.concat(G).sort_values("start_time_utc").reset_index(drop=True)
E = pd.concat(E)
E = E[E.game_id.isin(G.game_id) & (E.period_type == "REG")].sort_values(["game_id", "period", "sort_order"])
E["state"] = [q.classify_state(int(a), int(b), int(c), int(d)) if not np.isnan([a, b, c, d]).any() else "EV"
              for a, b, c, d in zip(E.home_skaters.astype(float), E.away_skaters.astype(float),
                                    E.home_goalie.astype(float), E.away_goalie.astype(float))]
train_ids = set(G[G.season < 2025].game_id)
# ---- state exposure and goals (training only), the state is that of the PRECEDING event ----
exp = defaultdict(float); gh = defaultdict(int); ga = defaultdict(int)
for gid, d in E[E.game_id.isin(train_ids)].groupby("game_id"):
    for per, p in d.groupby("period"):
        t = p.time_in_period_s.values.astype(float); st = p.state.values; ty = p.type.values; oh = p.owner_is_home.values
        for i in range(1, len(p)):
            dt = (t[i] - t[i - 1]) / 60.0
            if dt > 0:
                exp[st[i - 1]] += dt
            if ty[i] == "goal":
                (gh if oh[i] else ga)[st[i - 1]] += 1
tot_t = sum(exp.values()); tot_h = sum(gh.values()); tot_a = sum(ga.values())
base_h = tot_h / tot_t; base_a = tot_a / tot_t
states = {}
for s in ("EV", "H_PP", "A_PP", "H_EN", "A_EN"):
    if exp[s] < 50:
        states[s] = (1.0, 1.0, None if s in ("EV", "H_EN", "A_EN") else 1.0)
        continue
    states[s] = ((gh[s] / exp[s]) / base_h, (ga[s] / exp[s]) / base_a, 1.0 if s in ("H_PP", "A_PP") else None)
# EV is the baseline state: the pre-game rate already averages in the power-play mix, so EV multiplier is 1 (v1 applied the fitted 0.84 and underpriced goals).
states["EV"] = (1.0, 1.0, None)
fit = {s: dict(exposure_min=exp[s], goals_home=gh[s], goals_away=ga[s], mult_home=states[s][0], mult_away=states[s][1])
       for s in states}

# ---- game table: regulation goals, final, ratings proxy ----
REGG = E[E.type == "goal"].groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0)
REGG.columns = ["reg_a" if c is False or c == 0 else "reg_h" for c in REGG.columns]
G = G.join(REGG, on="game_id")
G[["reg_h", "reg_a"]] = G[["reg_h", "reg_a"]].fillna(0).astype(int)
G["home_won"] = (G.home_score > G.away_score).astype(int)
trg = G[G.season < 2025]
mu_h, mu_a = trg.reg_h.mean(), trg.reg_a.mean()
att = defaultdict(float); dfn = defaultdict(float); K = 0.03
lam_h, lam_a = [], []
for r in G.itertuples():
    eh = mu_h + att[r.home] + dfn[r.away]; ea = mu_a + att[r.away] + dfn[r.home]
    lam_h.append(eh * 60 / 60.0); lam_a.append(ea * 60 / 60.0)  # expected regulation goals = rate per 60
    att[r.home] += K * (r.reg_h - eh); dfn[r.away] += K * (r.reg_h - eh)
    att[r.away] += K * (r.reg_a - ea); dfn[r.home] += K * (r.reg_a - ea)
G["lam_h"] = np.clip(lam_h, 1.5, 5.0); G["lam_a"] = np.clip(lam_a, 1.5, 5.0)
# rate is per 60 of *average* state mix; states are multipliers relative to overall rate, so use as-is.

# ---- OT multiplier and shootout share from training ----
ot_games = trg[trg.last_period_type.isin(["OT", "SO"])]
so_share = float((ot_games[ot_games.last_period_type == "SO"].home_won).mean())
CK = {"P1_end": (1, 1200, 40.0), "P2_end": (2, 1200, 20.0), "P3_10m_left": (3, 600, 10.0), "P3_5m_left": (3, 900, 5.0)}
te = G[G.season == 2025]
ed = {gid: d for gid, d in E.groupby("game_id")}
rows = []
for r in te.itertuples():
    d = ed.get(r.game_id)
    if d is None:
        continue
    for name, (per, sec, tl) in CK.items():
        past = d[(d.period < per) | ((d.period == per) & (d.time_in_period_s <= sec))]
        if past.empty:
            continue
        gl = past[past.type == "goal"]
        sh = int(gl.owner_is_home.sum()); sa = int((~gl.owner_is_home.astype(bool)).sum())
        # state at the instant: last non-stoppage event state is fine; at a period end use even strength (clock stopped)
        st = past.state.iat[-1] if sec < 1200 else "EV"
        rows.append(dict(game_id=r.game_id, ck=name, tl=tl, sh=sh, sa=sa, state=st, lam_h=r.lam_h, lam_a=r.lam_a,
                         reg_h=r.reg_h, reg_a=r.reg_a, home_won=r.home_won))
R = pd.DataFrame(rows)

def run(col_f):
    return None

res = {"fit_states": fit, "base_rate_home_per_min": base_h, "base_rate_away_per_min": base_a, "so_home_share_train": so_share,
       "n_train_games": int(len(trg)), "n_test_games": int(len(te)), "checkpoints": {}}
bs = lambda p, y: np.asarray(p, float) - np.asarray(y, float)
for name in CK:
    s = R[R.ck == name]
    po = [q.outcome_probs(a.sh, a.sa, a.tl, a.lam_h, a.lam_a, a.state, states, ot_mult=1.0, p_so_home=so_share)
          for a in s.itertuples()]
    p_game = np.array([o["game_home"] for o in po]); y_game = s.home_won.values
    p_reg = np.array([o["reg_home"] for o in po]); y_reg = (s.reg_h > s.reg_a).astype(int).values
    p_tie = np.array([o["reg_tie"] for o in po]); y_tie = (s.reg_h == s.reg_a).astype(int).values
    p_ov = np.array([q.p_total_over(a.sh, a.sa, a.tl, a.lam_h, a.lam_a, 5.5, a.state, states) for a in s.itertuples()])
    y_ov = ((s.reg_h + s.reg_a) > 5.5).astype(int).values
    # pre-game-only reference at the same rows (no score information)
    p_pre = np.array([q.outcome_probs(0, 0, 60.0, a.lam_h, a.lam_a, "EV", states, p_so_home=so_share)["game_home"]
                      for a in s.itertuples()])
    def ci(sq):
        r = np.random.default_rng(20261105).integers(0, len(sq), size=(2000, len(sq)))
        m = sq[r].mean(1); return [float(sq.mean()), float(np.quantile(m, .025)), float(np.quantile(m, .975))]
    ent = {"n": int(len(s)),
           "game_home_win": dict(brier_ci95=ci(bs(p_game, y_game) ** 2), pregame_only_brier=float(np.mean(bs(p_pre, y_game) ** 2)),
                                 mean_p=float(p_game.mean()), rate=float(y_game.mean())),
           "reg_home_win": dict(brier_ci95=ci(bs(p_reg, y_reg) ** 2), mean_p=float(p_reg.mean()), rate=float(y_reg.mean())),
           "reg_tie": dict(brier_ci95=ci(bs(p_tie, y_tie) ** 2), mean_p=float(p_tie.mean()), rate=float(y_tie.mean())),
           "total_over_5.5": dict(brier_ci95=ci(bs(p_ov, y_ov) ** 2), mean_p=float(p_ov.mean()), rate=float(y_ov.mean())),
           "state_counts": s.state.value_counts().to_dict()}
    bins = []
    for lo in np.arange(0, 1, .2):
        m = (p_game >= lo) & (p_game < lo + .2 + (1e-9 if lo > .75 else 0))
        if m.any():
            bins.append([float(lo), float(p_game[m].mean()), float(y_game[m].mean()), int(m.sum())])
    ent["game_home_win"]["bins"] = bins
    res["checkpoints"][name] = ent

# score-effect diagnostic (training): EV home/away goal rate by home lead state
sc = defaultdict(lambda: [0.0, 0, 0])
for gid, d in E[E.game_id.isin(train_ids)].groupby("game_id"):
    sh = sa = 0
    for per, p in d.groupby("period"):
        t = p.time_in_period_s.values.astype(float); st = p.state.values; ty = p.type.values; oh = p.owner_is_home.values
        for i in range(1, len(p)):
            dt = (t[i] - t[i - 1]) / 60.0
            lead = "home_ahead" if sh > sa else ("away_ahead" if sa > sh else "tied")
            if st[i - 1] == "EV":
                if dt > 0:
                    sc[lead][0] += dt
                if ty[i] == "goal":
                    sc[lead][1 if oh[i] else 2] += 1
            if ty[i] == "goal":
                sh += int(bool(oh[i])); sa += int(not bool(oh[i]))
res["score_effects_ev_train"] = {k: dict(min=v[0], home_goals=v[1], away_goals=v[2], home_rate60=60 * v[1] / v[0], away_rate60=60 * v[2] / v[0])
                                 for k, v in sc.items()}
json.dump(res, open(safe_out(out), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
