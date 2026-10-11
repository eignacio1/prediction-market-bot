"""NFL QB-shrunk challenger features (W65.3 live port of the W64.1 study, pre-registration ACCEPTED 2026-10-10).

Point-in-time: every source row used for a game dated d has gameday < d. The QB term uses the PROJECTED starter
(the team's most recent completed prior game's starter), never the starter of the game itself. Logic is a verbatim
port of ``12_EXPLORATORY/20261009_nfl_qb_challenger/qb_features.py`` (constants, shrinkage, QB history).
"""
from __future__ import annotations

from bisect import bisect_left
from datetime import date, timezone
from typing import Optional

import numpy as np
import pandas as pd

WINDOW, DECAY, MIN_PERIODS = 8, 0.85, 3  # mirror nfl_pregame_features
QB_N, QB_K, EB_K = 16, 6.0, 2.0
TEAM_RATES = ["off_epa", "def_epa", "pf", "pa"]


def _d(x) -> date:
    return pd.to_datetime(x).date()


def shrunk_mean(vals, decay: float, K: float, mu: float) -> float:
    """(sum w_i x_i + K*mu)/(sum w_i + K), w_i = decay**(n-1-i), oldest first. K=0 is the frozen recency mean."""
    n = len(vals)
    w = np.array([decay ** (n - 1 - i) for i in range(n)])
    return float((w * np.asarray(vals, float)).sum() + K * mu) / float(w.sum() + K)


class _LeagueMean:
    """Mean of a quantity over all team-games with date strictly before d."""

    def __init__(self, dates, vals):
        o = np.argsort(np.array(dates, dtype="datetime64[D]"), kind="stable")
        self._d = [dates[i] for i in o]
        v = np.asarray(vals, float)[o]
        ok = ~np.isnan(v)
        self._cs = np.concatenate([[0.0], np.cumsum(np.where(ok, v, 0.0))])
        self._cn = np.concatenate([[0], np.cumsum(ok)])

    def before(self, d: date) -> float:
        i = bisect_left(self._d, d)
        return float(self._cs[i] / self._cn[i]) if self._cn[i] else 0.0


class ChallengerFeatures:
    def __init__(self, team_stats: pd.DataFrame, schedule: pd.DataFrame, schedule_ext: pd.DataFrame):
        sch = schedule.assign()
        sch["d"] = sch.gameday.map(_d)
        dmap = dict(zip(sch.game_id, sch.d))
        ts = team_stats.assign()
        opp = ts.set_index(["game_id", "team"]).off_epa
        ts["def_epa"] = [opp.get((g, o), np.nan) for g, o in zip(ts.game_id, ts.opponent_team)]
        ts["d"] = ts.game_id.map(dmap)
        ts = ts.dropna(subset=["d"]).sort_values(["team", "d"], kind="stable")
        self._epa = {t: g.reset_index(drop=True) for t, g in ts.groupby("team")}
        self._lm_epa = _LeagueMean(list(ts.d), ts.off_epa.to_numpy(float))
        done = sch.dropna(subset=["home_score", "away_score"])
        pr = []
        for r in done.itertuples():
            pr.append((r.home_team, r.d, r.home_score, r.away_score))
            pr.append((r.away_team, r.d, r.away_score, r.home_score))
        pdf = pd.DataFrame(pr, columns=["team", "d", "pf", "pa"]).sort_values(["team", "d"], kind="stable")
        self._pts = {t: g.reset_index(drop=True) for t, g in pdf.groupby("team")}
        self._lm_pts = _LeagueMean(list(pdf.d), pdf.pf.to_numpy(float))
        # QB: per team-game starter (completed games only) and per-QB start history (date, own-team off_epa)
        ext = schedule_ext.assign()
        ext["d"] = ext.gameday.map(_d)
        ext = ext.dropna(subset=["home_score", "away_score"])
        epa_by = {(g, t): e for g, t, e in zip(ts.game_id, ts.team, ts.off_epa)}
        tg, hist = [], {}
        for r in ext.itertuples():
            for team, qid in ((r.home_team, r.home_qb_id), (r.away_team, r.away_qb_id)):
                if pd.isna(qid):
                    qid = None
                tg.append((team, r.d, qid))
                e = epa_by.get((r.game_id, team))
                if qid is not None and e is not None and not pd.isna(e):
                    hist.setdefault(qid, []).append((r.d, float(e)))
        self._team_starters = {t: g for t, g in pd.DataFrame(tg, columns=["team", "d", "qb"]).sort_values(
            ["team", "d"], kind="stable").groupby("team")}
        self._qb_hist = {q: sorted(v) for q, v in hist.items()}

    # --- team rates -------------------------------------------------------------------------------------------
    def team_rates(self, team: str, d: date, K: float) -> Optional[dict]:
        """Shrunk (K>0) or frozen-equivalent (K=0) off_epa/def_epa/pf/pa; None where the frozen builder is None."""
        g = self._epa.get(team)
        p = self._pts.get(team)
        if g is None or p is None:
            return None
        out = {}
        mu_e, mu_p = self._lm_epa.before(d), self._lm_pts.before(d)
        prior = g[g.d < d]
        if len(prior) < MIN_PERIODS:
            return None
        rec = prior.tail(WINDOW)
        for col in ("off_epa", "def_epa"):
            v = rec[col].dropna()
            if len(v) < MIN_PERIODS:
                return None
            out[col] = shrunk_mean(v.to_numpy(), DECAY, K, mu_e)
        pp = p[p.d < d]
        if len(pp) < MIN_PERIODS:
            return None
        rp = pp.tail(WINDOW)
        out["pf"] = shrunk_mean(rp.pf.to_numpy(), DECAY, K, mu_p)
        out["pa"] = shrunk_mean(rp.pa.to_numpy(), DECAY, K, mu_p)
        return out

    # --- quarterbacks -----------------------------------------------------------------------------------------
    def projected_starter(self, team: str, d: date):
        """Starter of the team's most recent completed game strictly before d (point-in-time legal)."""
        g = self._team_starters.get(team)
        if g is None:
            return None
        prior = g[g.d < d]
        return None if prior.empty else prior.qb.iloc[-1]

    def qb_epa(self, qb_id, d: date) -> float:
        """(sum of QB's last N starts' team off_epa + k*mu)/(n+k); starts strictly before d. Unknown QB -> mu."""
        mu = self._lm_epa.before(d)
        h = self._qb_hist.get(qb_id) if qb_id is not None else None
        if not h:
            return mu
        i = bisect_left([x[0] for x in h], d)
        xs = [e for _, e in h[max(0, i - QB_N):i]]
        return (sum(xs) + QB_K * mu) / (len(xs) + QB_K)


CHALLENGER_FEATURE_NAMES = [
    "off_epa_h", "def_epa_h", "off_epa_a", "def_epa_a",
    "pf_h", "pa_h", "pf_a", "pa_a",
    "rest_diff", "rest_short_h", "rest_short_a",
    "qb_epa_h", "qb_epa_a",
]
QB_SOURCE = "projected_prior_game_starter"


class NFLQBFeatureBuilder:
    """13-feature row. Availability gate and rest features come from the frozen builder, so a game the frozen
    model can score is a game the challenger can score (same games, same T1 timing)."""

    def __init__(self, team_stats: pd.DataFrame, schedule: pd.DataFrame) -> None:
        from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder
        self.frozen = NFLPregameFeatureBuilder(team_stats, schedule)
        self.cf = ChallengerFeatures(team_stats, schedule, schedule)

    def row(self, home: str, away: str, as_of_utc, home_rest=None, away_rest=None) -> Optional[dict]:
        import hashlib
        import json
        base = self.frozen.row(home, away, as_of_utc, home_rest, away_rest)
        if base is None:
            return None
        d = as_of_utc.astimezone(timezone.utc).date()
        eh, ea = self.cf.team_rates(home, d, EB_K), self.cf.team_rates(away, d, EB_K)
        if eh is None or ea is None:
            return None
        f = base["features"]
        vals = dict(f)
        for sfx, e in (("h", eh), ("a", ea)):
            vals[f"off_epa_{sfx}"], vals[f"def_epa_{sfx}"] = e["off_epa"], e["def_epa"]
            vals[f"pf_{sfx}"], vals[f"pa_{sfx}"] = e["pf"], e["pa"]
        ph, pa = self.cf.projected_starter(home, d), self.cf.projected_starter(away, d)
        vals["qb_epa_h"], vals["qb_epa_a"] = self.cf.qb_epa(ph, d), self.cf.qb_epa(pa, d)
        payload = json.dumps({k: round(float(vals[k]), 9) for k in CHALLENGER_FEATURE_NAMES}
                             | {"as_of": as_of_utc.isoformat(), "qb_source": QB_SOURCE}, sort_keys=True)
        return {"features": vals, "sha256": hashlib.sha256(payload.encode()).hexdigest(),
                "audit": {"qb_source": QB_SOURCE, "home_qb": ph, "away_qb": pa}}
