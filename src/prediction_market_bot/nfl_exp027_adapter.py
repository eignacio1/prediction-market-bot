"""EXP-027/T-531 LR model adapter -- NFLForecastModel protocol (T-534/GG-263).

Wraps scripts/exp027_hyp012_nfl_moneyline_backtest.py's pre-registered LR+Platt
model (HYP-012; verdict UNDERPOWERED pending more 2026 season data, per
05_RESEARCH_EXPERIMENTS/HYP012_nfl_moneyline_lr_preregistration_2026-09-09.md)
so it can be injected into run_t1_nfl_game_market.py's main(model=...) in
place of StubNFLForecastModel.

**Consumed as-is, not retrained/re-tuned/re-fit for this task.** The
pre-registered script fits its Pipeline in-memory and never serializes it to
disk -- there is no saved .pkl/.joblib artifact anywhere in the repo. The only
way to obtain the trained object at all is to re-run the pre-registered
script's own load -> feature-build -> fit procedure once, so this module
imports that script by file path and calls its own functions unmodified:
same TRAIN_SEASONS (2015-2024), same FEATURES, same random_state=42
(LogisticRegression + CalibratedClassifierCV inside _fit_lr). No parameter,
season, feature, or hyperparameter is changed here. This is loading the
pre-registered fit, not producing a new one.

Scope: moneyline (KXNFLGAME) only -- EXP-027 has no spread/total/team_total
head. predict_proba() returns None (a refusal, per NFLForecastModel's
contract -- REFUSED_NO_MODEL fires downstream) for any market this model
cannot score, rather than ever substituting a default/imputed probability:
  - market_type != "moneyline"
  - ticker cannot be parsed into two team codes (parse_event_teams)
  - the parsed teams / game date do not join to a known schedule row
  - either team is missing EPA history or rest-days data as of that game
      (checked BEFORE calling the training-time _impute() helper, which
      would otherwise silently plug in 0.0 for a NaN feature -- correct for
      cross-sectional training-set imputation, wrong for a single live
      inference row, which must refuse instead)

**Import-order requirement (worktree isolation, GG-082/GG-101 class of risk):**
exp027's own top-of-file code runs `sys.path.insert(0, MAIN_TREE / "src")`
(MAIN_TREE = the shared checkout, not this session's isolated worktree) so it
can run standalone as `python scripts/exp027_...py`. Loading that module here
re-executes that insert. Any `prediction_market_bot.*` submodule NOT already
present in `sys.modules` at that moment will therefore import from MAIN_TREE
instead of this worktree -- silently running whatever code happens to be
checked out on MAIN, not this session's branch. The caller MUST import
`run_t1_nfl_game_market` (which pulls in `AuditLogger` and everything else
this run needs) BEFORE constructing `EXP027NFLForecastModel`, so every module
the two scripts share is already cached from this worktree first. `__init__`
below asserts this held, rather than trusting the caller silently.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from prediction_market_bot.c5_execution.kalshi_client import GameMarket

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_EXP027_PATH = _REPO_ROOT / "scripts" / "exp027_hyp012_nfl_moneyline_backtest.py"

# Kalshi ticker alphabet -> nflverse schedule alphabet (identical mapping to
# the one in exp027's own module, duplicated here only because that script is
# loaded dynamically by path, not imported as a package).
_KALSHI_TO_NFLVERSE = {"LAR": "LA", "WSH": "WAS"}

_AUDIT_LOGGER_MODULE = "prediction_market_bot.c6_audit_logger.audit_logger"


def _load_exp027_module():
    # Snapshot sys.modules identity for the one module exp027 shares with
    # run_t1_nfl_game_market, so we can detect (not just hope against)
    # cross-tree contamination -- see module docstring.
    pre_audit_mod = sys.modules.get(_AUDIT_LOGGER_MODULE)
    if pre_audit_mod is None or not str(getattr(pre_audit_mod, "__file__", "")).startswith(
        str(_REPO_ROOT)
    ):
        raise RuntimeError(
            "nfl_exp027_adapter: run_t1_nfl_game_market (or another worktree-"
            "rooted import of prediction_market_bot.c6_audit_logger.audit_logger) "
            "must be imported BEFORE constructing EXP027NFLForecastModel -- "
            "see this module's docstring, import-order requirement."
        )

    path_before = list(sys.path)
    spec = importlib.util.spec_from_file_location(
        "exp027_hyp012_nfl_moneyline_backtest", _EXP027_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    # Restore sys.path so nothing imported *after* this point (in this
    # process) can resolve against MAIN_TREE instead of this worktree.
    sys.path[:] = path_before
    return mod


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


class EXP027NFLForecastModel:
    """NFLForecastModel implementation backed by EXP-027's LR+Platt pipeline.

    Model provenance for dashboard/audit labeling: "EXP-027 LR (T-531,
    verdict UNDERPOWERED)" -- callers should surface this string, never
    "stub", alongside any output produced through this class.
    """

    PROVENANCE = "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"

    def __init__(self) -> None:
        exp027 = _load_exp027_module()
        self._exp027 = exp027

        schedule = exp027.load_schedule()
        team_stats = exp027.load_team_stats()
        store = exp027.NFLTeamStatsStore.build_from_team_stats(team_stats, schedule)
        exp027.verify_store(store)
        feat_df = exp027.build_feature_rows(schedule, store)
        train_df = feat_df[
            feat_df["season"].isin(exp027.TRAIN_SEASONS) & feat_df["label"].notnull()
        ].reset_index(drop=True)

        X_train = exp027._impute(train_df[exp027.FEATURES].to_numpy(dtype=float))
        y_train = train_df["label"].to_numpy(dtype=int)
        self._model = exp027._fit_lr(X_train, y_train)
        self._store = store
        self._sched_lookup = {
            (str(r["gameday"]), frozenset({r["home_team"], r["away_team"]})): r
            for _, r in schedule.iterrows()
        }
        print(
            f"[EXP027NFLForecastModel] LR+Platt reproduced from pre-registration "
            f"on {len(train_df)} TRAIN games (seasons {sorted(exp027.TRAIN_SEASONS)}), "
            f"random_state=42 -- unmodified from HYP-012 pre-registration.",
            file=sys.stderr,
        )

    def predict_proba(self, market: GameMarket, features: dict[str, Any]) -> float | None:
        if market.market_type != "moneyline":
            return None  # EXP-027 has no spread/total/team_total head

        parts = market.ticker.split("-")
        if len(parts) != 3:
            return None
        event_segment = parts[1]

        teams = self._exp027.parse_event_teams(event_segment)
        if teams is None:
            return None
        # market.game_date is already parsed by KalshiMarketClient itself
        # (_game_date_from_event_ticker) from the same date prefix -- use it
        # directly rather than re-deriving, so this adapter never disagrees
        # with what the live client already computed for this market.
        game_date = market.game_date
        if not game_date:
            return None

        team_a = _KALSHI_TO_NFLVERSE.get(teams[0], teams[0])
        team_b = _KALSHI_TO_NFLVERSE.get(teams[1], teams[1])
        yes_team = _KALSHI_TO_NFLVERSE.get(market.team_abbr, market.team_abbr)
        if yes_team not in (team_a, team_b):
            return None

        sched_row = self._sched_lookup.get((str(game_date), frozenset({team_a, team_b})))
        if sched_row is None:
            return None

        home_team, away_team = sched_row["home_team"], sched_row["away_team"]
        if yes_team not in (home_team, away_team):
            return None

        as_of = str(sched_row["gameday"])
        off_h = self._store.get_off_epa(
            home_team, as_of, window=self._exp027.DEFAULT_WINDOW,
            min_periods=self._exp027.MIN_PERIODS, decay=self._exp027.DEFAULT_DECAY,
        )
        def_h = self._store.get_def_epa_allowed(
            home_team, as_of, window=self._exp027.DEFAULT_WINDOW,
            min_periods=self._exp027.MIN_PERIODS, decay=self._exp027.DEFAULT_DECAY,
        )
        off_a = self._store.get_off_epa(
            away_team, as_of, window=self._exp027.DEFAULT_WINDOW,
            min_periods=self._exp027.MIN_PERIODS, decay=self._exp027.DEFAULT_DECAY,
        )
        def_a = self._store.get_def_epa_allowed(
            away_team, as_of, window=self._exp027.DEFAULT_WINDOW,
            min_periods=self._exp027.MIN_PERIODS, decay=self._exp027.DEFAULT_DECAY,
        )
        home_rest = sched_row.get("home_rest")
        away_rest = sched_row.get("away_rest")

        row = [off_h, def_h, off_a, def_a, home_rest, away_rest]
        if any(_is_missing(v) for v in row):
            return None  # insufficient history -- refuse, never impute a live row

        X = self._exp027._impute(np.array([row], dtype=float))
        p_home = float(self._model.predict_proba(X)[0, 1])

        return p_home if yes_team == home_team else (1.0 - p_home)


def _run() -> None:
    """One-shot manual runner -- T-534/GG-263 Deliverable 1.

    NOT wired into cron (scheduling not authorized for this task). Invoke
    manually: `source /opt/prediction-market-bot/.env; BOT_ENV=paper
    PYTHONPATH=src python src/prediction_market_bot/nfl_exp027_adapter.py`.

    Import order matters here (see module docstring): run_t1_nfl_game_market
    is imported, and thus fully module-loaded from this worktree, before
    EXP027NFLForecastModel is constructed.
    """
    from prediction_market_bot import run_t1_nfl_game_market as run_mod

    model = EXP027NFLForecastModel()
    outcome_counts = run_mod.main(model)
    print(f"[nfl_exp027_adapter] run complete via {model.PROVENANCE}: {outcome_counts}")


if __name__ == "__main__":
    _run()
