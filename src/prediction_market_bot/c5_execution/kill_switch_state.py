"""GG-667/GG-745: the ONE kill-switch check for every order path (NFR-03).

Flag files in ``logs/`` (touch to halt, rm to resume):
  * ``kill_switch.flag``              GLOBAL - halts every order path (written by C7 on a trip)
  * ``kill_switch_<band>.flag``       BAND   - halts only that band (CLAUDE.md "Execution timing")
  * legacy aliases, read as band flags until every reader is moved:
      ``t4_mlb_kill_switch.flag`` -> band ``t4_mlb``;  ``t4_kill_switch.flag`` -> band ``t4``
Any other ``*kill_switch*.flag`` is unrecognised and fails closed as GLOBAL.
A caller that passes no band is treated as "any flag halts me" (conservative: a new runner
that forgets to name its band can be over-halted, never under-halted).
``KalshiMarketClient.submit_order`` calls ``halt_reason`` itself, so no runner can skip it.
Read-only; fails closed (an unreadable logs dir counts as halted).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_DEFAULT_LOGS_DIR = Path(__file__).resolve().parents[3] / "logs"

GLOBAL_FLAG = "kill_switch.flag"
_LEGACY_ALIASES = {"t4_mlb_kill_switch.flag": "t4_mlb", "t4_kill_switch.flag": "t4"}


def _logs_dir(logs_dir: Optional[Path]) -> Path:
    if logs_dir is not None:
        return Path(logs_dir)
    env = os.environ.get("PMBOT_KILL_SWITCH_DIR")  # tests / drills only
    return Path(env) if env else _DEFAULT_LOGS_DIR


def global_flag_path(logs_dir: Optional[Path] = None) -> Path:
    return _logs_dir(logs_dir) / GLOBAL_FLAG


def band_flag_path(band: str, logs_dir: Optional[Path] = None) -> Path:
    return _logs_dir(logs_dir) / f"kill_switch_{band}.flag"


def flag_band(name: str) -> Optional[str]:
    """Band a flag file name applies to; None = global (including unrecognised names)."""
    if name == GLOBAL_FLAG:
        return None
    if name in _LEGACY_ALIASES:
        return _LEGACY_ALIASES[name]
    if name.startswith("kill_switch_") and name.endswith(".flag"):
        return name[len("kill_switch_"):-len(".flag")] or None
    return None


def halt_reason(market_type=None, band=None, logs_dir: Optional[Path] = None,
                band_name: Optional[str] = None) -> Optional[str]:
    """Return why order placement must halt, or None when nothing is halted.

    ``band_name`` is the flag-file band label (e.g. ``t4_mlb``); ``band`` is the registry
    ExecutionBand used with ``market_type`` for the cell-tier check."""
    d = _logs_dir(logs_dir)
    try:
        flags = sorted(p.name for p in d.glob("*kill_switch*.flag")) if d.exists() else []
    except OSError as e:
        return f"kill_switch_state_unreadable:{type(e).__name__}"
    for name in flags:
        fb = flag_band(name)
        if fb is None or band_name is None or fb == band_name:
            return f"kill_switch_flag:{name}"
    if market_type is not None and band is not None:
        from prediction_market_bot.c5_execution.market_type_registry import (
            CellKillSwitchStatus, resolve_kill_switch_state,
        )
        st = resolve_kill_switch_state(market_type, band)
        if st.status is CellKillSwitchStatus.HALTED:
            return f"cell_halted:{st.reason}"
    return None
