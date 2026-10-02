"""C3 — NHL pregame forecaster (T-607 / EXP-036, deliverable D2).

ONE joint distribution of (home, away) regulation goals per game — a bivariate Poisson
(shared component, ``lam0 = c * min(lam_h, lam_a)``) whose two means come from a frozen
Poisson log-link regression on C2 features. Every market is derived from that single
distribution, so the ladder is coherent by construction:

* Kalshi settles OT *and* shootout with the winner credited ONE goal (the total counts
  regulation + OT goals, a shootout adds one goal to the winner; the puck-line strikes
  1.5/2.5 are unaffected because a tie-break winner's margin is exactly 1). So a regulation
  tie becomes final (k+1, k) for the tie-break winner; no separate OT/SO branch is needed
  for any listed strike. ``pt`` = P(home takes the tie-break | tie).
* moneyline  = P(h>a) + P(tie)*pt
* puck line  "T wins by over 1.5 / 2.5" = P(regulation margin_T >= 2 / >= 3)
* total      "over N.5" = P(h + a + 1[h==a] > N.5)

Calibration (ADR-0004: Platt scaling): Platt on logit(P(home win)); the calibrated
moneyline is propagated into the distribution by a one-parameter tilt of (lam_h, lam_a)
so the puck line and totals stay coherent with it, plus a total-intensity scale. Fit on a
prior-season fold only. The artifact is frozen (``models/nhl_pregame_v1.json``) and hashed;
there is no production retraining (Hard Rule 4).

Information cutoff: all inputs come from ``NhlFeatureStore.game_features`` which raises if
any input is timestamped after ``as_of_utc``.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from prediction_market_bot.c2_feature_store.nhl_features import (
    NhlFeatureStore, feature_row_sha256, parse_ts)

try:  # 47.2's contract; code to the described text until it lands on origin/main
    from prediction_market_bot.pregame_shadow.contract import PregameForecast  # type: ignore
except ImportError:  # pragma: no cover - exercised until the contract lands
    @dataclass(frozen=True)
    class PregameForecast:  # type: ignore[no-redef]
        sport: str
        market_type: str
        event_ticker: str
        market_ticker: str
        p_yes: float
        as_of_utc: datetime
        model_id: str
        model_sha256: str
        feature_row_sha256: str

        def __post_init__(self):
            if not (0.0 < self.p_yes < 1.0):
                raise ValueError("p_yes must be strictly in (0,1)")

GRID = 16
MODEL_PATH = Path("models/nhl_pregame_v1.json")
MODEL_ID = "nhl_pregame_v1"
GLM_FEATURES = [
    "own_gf_ew", "opp_ga_ew", "own_sf_ew", "opp_sa_ew", "own_pp_ew", "opp_pim_ew",
    "own_gf_l10", "opp_ga_l10", "own_b2b", "opp_b2b", "own_rest_days", "opp_rest_days",
    "opp_goalie_svp", "is_home",
]
EPS = 1e-4


# ----------------------------------------------------------------- distribution
def _pois_pmf(lam: float, n: int = GRID) -> np.ndarray:
    k = np.arange(n)
    logp = -lam + k * math.log(max(lam, 1e-12)) - np.array([math.lgamma(i + 1) for i in k])
    return np.exp(logp)


def joint_pmf(lam_h: float, lam_a: float, c: float) -> np.ndarray:
    """Bivariate Poisson over regulation goals, GRID x GRID, renormalised."""
    lam0 = c * min(lam_h, lam_a)
    p1, p2, p0 = _pois_pmf(lam_h - lam0), _pois_pmf(lam_a - lam0), _pois_pmf(lam0)
    J = np.zeros((GRID, GRID))
    for k in range(GRID):
        if p0[k] < 1e-14:
            continue
        J[k:, k:] += p0[k] * np.outer(p1[: GRID - k], p2[: GRID - k])
    return J / J.sum()


class Ladder:
    """All market probabilities derived from one joint pmf + tie-break probability."""

    def __init__(self, joint: np.ndarray, pt: float):
        self.J, self.pt = joint, pt
        x = np.arange(GRID)[:, None]
        y = np.arange(GRID)[None, :]
        self._margin = x - y
        self._tie = (self._margin == 0)
        self._total = x + y + self._tie  # shootout/OT winner adds one goal

    def p_home_win(self) -> float:
        return float(self.J[self._margin > 0].sum() + self.pt * self.J[self._tie].sum())

    def p_win_by_over(self, side: str, strike: float) -> float:
        m = self._margin if side == "home" else -self._margin
        return float(self.J[m > strike].sum())

    def p_total_over(self, strike: float) -> float:
        return float(self.J[self._total > strike].sum())

    def p_team_win(self, side: str) -> float:
        p = self.p_home_win()
        return p if side == "home" else 1.0 - p


# ----------------------------------------------------------------- model
def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def side_vector(row: dict, own: str, opp: str, is_home: int) -> list[float]:
    o, p = f"{own}_", f"{opp}_"
    return [row[o + "gf_ew"], row[p + "ga_ew"], row[o + "sf_ew"], row[p + "sa_ew"], row[o + "pp_ew"],
            row[p + "pim_ew"], row[o + "gf_l10"], row[p + "ga_l10"], row[o + "b2b"], row[p + "b2b"],
            row[o + "rest_days"], row[p + "rest_days"], row[p + "goalie_svp"], float(is_home)]


class NhlGoalsModel:
    """Frozen parameters; ``params`` is the JSON-serialisable artifact body."""

    def __init__(self, params: dict):
        self.p = params
        self.mu = np.array(params["glm"]["mu"])
        self.sd = np.array(params["glm"]["sd"])
        self.coef = np.array(params["glm"]["coef"])
        self.icpt = float(params["glm"]["intercept"])

    def lambdas(self, row: dict) -> tuple[float, float]:
        out = []
        for own, opp, h in (("h", "a", 1), ("a", "h", 0)):
            z = (np.array(side_vector(row, own, opp, h)) - self.mu) / self.sd
            out.append(float(np.exp(self.icpt + z @ self.coef)))
        return out[0], out[1]

    def pt(self, lam_h: float, lam_a: float) -> float:
        t = self.p["tiebreak"]
        return _sigmoid(t["a"] + t["b"] * math.log(lam_h / lam_a))

    def raw_ladder(self, row: dict) -> tuple[Ladder, float, float]:
        lh, la = self.lambdas(row)
        s = self.p["calibration"]["total_scale"]
        lh, la = lh * s, la * s
        return Ladder(joint_pmf(lh, la, self.p["bivariate_c"]), self.pt(lh, la)), lh, la

    def ladder(self, row: dict) -> Ladder:
        """Calibrated ladder: Platt on logit(P(home win)), propagated by a lam tilt."""
        lad, lh, la = self.raw_ladder(row)
        cal = self.p["calibration"]
        p_raw = min(max(lad.p_home_win(), 1e-6), 1 - 1e-6)
        z = cal["platt_a"] + cal["platt_b"] * math.log(p_raw / (1 - p_raw))
        target = min(max(_sigmoid(z), 0.02), 0.98)
        lo, hi = -2.0, 2.0
        for _ in range(60):  # monotone in the tilt -> bisection
            mid = 0.5 * (lo + hi)
            e = math.exp(mid)
            l2 = Ladder(joint_pmf(lh * e, la / e, self.p["bivariate_c"]), self.pt(lh * e, la / e))
            if l2.p_home_win() < target:
                lo = mid
            else:
                hi = mid
        e = math.exp(0.5 * (lo + hi))
        return Ladder(joint_pmf(lh * e, la / e, self.p["bivariate_c"]), self.pt(lh * e, la / e))


def artifact_sha256(params: dict) -> str:
    body = {k: v for k, v in params.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def load_model(path: Path = MODEL_PATH) -> tuple[NhlGoalsModel, str]:
    params = json.loads(Path(path).read_text())
    sha = artifact_sha256(params)
    if params.get("sha256") != sha:
        raise ValueError(f"model artifact hash mismatch: stored {params.get('sha256')} computed {sha}")
    return NhlGoalsModel(params), sha


# ----------------------------------------------------------------- tickers
_TICK = re.compile(r"^KXNHL(GAME|SPREAD|TOTAL)-(\d{2})([A-Z]{3})(\d{2})([A-Z]{3})([A-Z]{3})-(.+)$")
_MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
MARKET_TYPE = {"GAME": "NHL_MONEYLINE", "SPREAD": "NHL_PUCK_LINE", "TOTAL": "NHL_GAME_TOTAL"}
TEAM_ALIASES: dict[str, str] = {}  # Kalshi code -> NHL abbrev if they ever differ (unverified)


def parse_ticker(t: str) -> Optional[dict]:
    m = _TICK.match(t)
    if not m:
        return None
    kind, yy, mon, dd, a, h, suf = m.groups()
    if mon not in _MON:
        return None
    out = {"series": kind, "market_type": MARKET_TYPE[kind],
           "game_date": f"20{yy}-{_MON[mon]:02d}-{dd}",
           "away": TEAM_ALIASES.get(a, a), "home": TEAM_ALIASES.get(h, h),
           "event_ticker": t.rsplit("-", 1)[0]}
    if kind == "GAME":
        out["team"] = TEAM_ALIASES.get(suf, suf)
    elif kind == "SPREAD":
        mm = re.match(r"^([A-Z]{3})(\d)$", suf)
        if not mm:
            return None
        out["team"], out["strike"] = TEAM_ALIASES.get(mm.group(1), mm.group(1)), int(mm.group(2)) - 0.5
    else:
        if not suf.isdigit():
            return None
        out["strike"] = int(suf) - 0.5
    return out


# ----------------------------------------------------------------- forecaster
StarterProvider = Callable[[int, datetime], Optional[tuple]]


class NhlPregameForecaster:
    """PregameForecaster implementation. Evaluate-and-log only: no order/position imports."""
    sport = "NHL"

    def __init__(self, model: NhlGoalsModel, model_sha256: str, store: NhlFeatureStore,
                 schedule: list[dict], starter_provider: Optional[StarterProvider] = None,
                 model_id: str = MODEL_ID):
        self.model, self.sha, self.store = model, model_sha256, store
        self.model_id, self.starter_provider = model_id, starter_provider
        self._sched = {}
        for g in schedule:
            self._sched[(g["game_date"], g["home"], g["away"])] = g

    def _game(self, info: dict) -> Optional[dict]:
        """Resolve the game; ticker order (AWAYHOME) is checked against the schedule and the
        swapped order is accepted so a wrong ordering assumption cannot silently mis-map."""
        g = self._sched.get((info["game_date"], info["home"], info["away"]))
        if g is None:
            g = self._sched.get((info["game_date"], info["away"], info["home"]))
            if g is not None:
                info["home"], info["away"] = g["home"], g["away"]
        return g

    def feature_row(self, game: dict, as_of_utc: datetime) -> dict:
        confirmed, hg, ag = False, None, None
        if self.starter_provider is not None:
            got = self.starter_provider(game["game_id"], as_of_utc)
            if got:
                hg, ag = got
                confirmed = hg is not None or ag is not None
        return self.store.game_features(game["home"], game["away"], parse_ts(game["start_time_utc"]),
                                        as_of_utc, home_goalie=hg, away_goalie=ag, confirmed=confirmed)

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        info = parse_ticker(market_ticker)
        if info is None:
            return None
        game = self._game(info)
        if game is None or game.get("schedule_state") in ("PPD", "CNCL", "SUSP"):
            return None
        if as_of_utc.tzinfo is None:
            as_of_utc = as_of_utc.replace(tzinfo=timezone.utc)
        if as_of_utc >= parse_ts(game["start_time_utc"]):
            return None  # pregame only
        row = self.feature_row(game, as_of_utc)
        lad = self.model.ladder(row)
        if info["series"] == "GAME":
            side = "home" if info["team"] == info["home"] else "away" if info["team"] == info["away"] else None
            if side is None:
                return None
            p = lad.p_team_win(side)
        elif info["series"] == "SPREAD":
            side = "home" if info["team"] == info["home"] else "away" if info["team"] == info["away"] else None
            if side is None:
                return None
            p = lad.p_win_by_over(side, info["strike"])
        else:
            p = lad.p_total_over(info["strike"])
        p = min(max(p, EPS), 1 - EPS)
        return PregameForecast(sport=self.sport, market_type=info["market_type"],
                               event_ticker=info["event_ticker"], market_ticker=market_ticker, p_yes=p,
                               as_of_utc=as_of_utc, model_id=self.model_id, model_sha256=self.sha,
                               feature_row_sha256=feature_row_sha256(row))
