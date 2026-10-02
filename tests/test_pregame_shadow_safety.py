"""EXP-037 D2(e): the pregame shadow package must have no import path to any order,
position, sizing or paper-trader function, and may write only to its own ledger dir."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
PKG = "prediction_market_bot.pregame_shadow"
FORBIDDEN_MODULES = {
    "prediction_market_bot.c5_execution.paper_trader",
    "prediction_market_bot.c5_execution.kalshi_client",
    "prediction_market_bot.c5_execution.venue_router",
    "prediction_market_bot.c5_execution.venue_adapter",
}
# execution_bands is reachable ONLY transitively, through market_type_registry's read-only
# `from execution_bands import ExecutionBand` (an Enum). It holds config dataclasses (incl.
# kelly_fraction VALUES) but no order/position/sizing function. The package itself must never
# import it directly -- see test_package_does_not_import_execution_bands_directly.
TRANSITIVE_ONLY_OK = {"prediction_market_bot.execution_bands"}
FORBIDDEN_PREFIXES = ("prediction_market_bot.c4_risk_engine",)
FORBIDDEN_NAMES = {"get_band_config", "BandConfig", "submit_order", "open_position", "exit_position", "settle_position",
                   "evaluate_forecast", "kelly_fraction", "place_order", "PaperTrader"}


def _module_path(mod: str) -> Path | None:
    p = SRC.joinpath(*mod.split("."))
    if p.with_suffix(".py").exists():
        return p.with_suffix(".py")
    if (p / "__init__.py").exists():
        return p / "__init__.py"
    return None


def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    tree = ast.parse(path.read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            out.add(n.module)
            out.update(f"{n.module}.{a.name}" for a in n.names)
    return {m for m in out if m.startswith("prediction_market_bot")}


def _reachable() -> set[str]:
    seen: set[str] = set()
    stack = [str(p.relative_to(SRC).with_suffix("")).replace("/", ".").removesuffix(".__init__")
             for p in (SRC / "prediction_market_bot" / "pregame_shadow").glob("*.py")]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        path = _module_path(m)
        if path is None:
            continue
        stack.extend(_imports(path))
        # importing a submodule imports its parent packages' __init__ too
        parts = m.split(".")
        stack.extend(".".join(parts[:i]) for i in range(2, len(parts)))
    return seen


def test_no_import_path_to_order_position_sizing_modules():
    reach = _reachable()
    bad = {m for m in reach if m in FORBIDDEN_MODULES or m.startswith(FORBIDDEN_PREFIXES)}
    assert not bad, f"pregame_shadow reaches forbidden modules: {sorted(bad)}"


def test_package_does_not_import_execution_bands_directly():
    for p in (SRC / "prediction_market_bot" / "pregame_shadow").glob("*.py"):
        assert not (_imports(p) & TRANSITIVE_ONLY_OK), p.name


def test_package_source_never_names_order_or_sizing_functions():
    hits = []
    for p in (SRC / "prediction_market_bot" / "pregame_shadow").glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text())):
            name = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None
            if name in FORBIDDEN_NAMES:
                hits.append((p.name, name))
    assert not hits, hits


def test_safety_walk_detects_a_planted_violation(tmp_path, monkeypatch):
    """The walk itself must be able to fail: a package module importing paper_trader is caught."""
    import tests.test_pregame_shadow_safety as me  # noqa: F401  (self-import keeps helper shared)
    fake = tmp_path / "prediction_market_bot" / "pregame_shadow"
    fake.mkdir(parents=True)
    (fake / "__init__.py").write_text("")
    (fake / "bad.py").write_text("from prediction_market_bot.c5_execution import paper_trader\n")
    monkeypatch.setattr(me, "SRC", tmp_path)
    # reachability only follows files under the fake SRC, so the planted import name is the signal
    assert "prediction_market_bot.c5_execution.paper_trader" in me._reachable()


def test_runner_writes_only_inside_its_ledger_dir(tmp_path):
    from prediction_market_bot.pregame_shadow.runner import run_once
    from prediction_market_bot.pregame_shadow.contract import PregameForecast

    class F:
        sport = "NFL"

        def forecast(self, tkr, as_of):
            return PregameForecast("NFL", "NFL_MONEYLINE", "KXNFLGAME-26OCT04ARINYG", tkr, 0.55,
                                   as_of, "m", "s", "f")

    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
    ko = datetime(2026, 10, 4, 17, 0, tzinfo=timezone.utc)  # 29h -> T1
    raw = [{"ticker": "KXNFLGAME-26OCT04ARINYG-NYG", "event_ticker": "KXNFLGAME-26OCT04ARINYG",
            "yes_bid_dollars": "0.50", "yes_ask_dollars": "0.54"}]
    work = tmp_path / "work"
    work.mkdir()
    before = {p for p in tmp_path.rglob("*")}
    res = run_once(forecaster=F(), cells=[("NFL_MONEYLINE", "KXNFLGAME")],
                   list_markets=lambda s: (True, raw), kickoff_for=lambda e: (ko, "test"),
                   ledger_dir=work / "ledgers", run_id="r1", now_utc=now, code_sha="x")
    after = {p for p in tmp_path.rglob("*")} - before
    assert res["written"] == {"NFL_MONEYLINE:T1": 1}
    assert all(str(p).startswith(str(work / "ledgers")) or p == work / "ledgers" for p in after)
