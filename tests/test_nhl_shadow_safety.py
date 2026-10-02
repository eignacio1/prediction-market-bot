"""Shadow-package safety: NO import path from the NHL shadow code to any order/position/sizing function."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PKG = "prediction_market_bot"
ENTRY = [ROOT / "scripts" / n for n in ("nhl_shadow_eval.py", "nhl_shadow_settle.py", "nhl_backfill.py")] + \
        sorted((SRC / PKG).glob("*/nhl_*.py"))
FORBIDDEN_MODULES = ("kalshi_client", "paper_trader", "c4_risk_engine", "execution_bands", "venue_adapter",
                     "market_type_registry", "c5_execution", "pregame_shadow.runner")
FORBIDDEN_NAMES = ("submit_order", "open_position", "exit_position", "kelly", "place_order", "PaperTrader")


def _imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            yield base
            yield from (f"{base}.{a.name}" for a in node.names)


def _module_file(mod: str):
    if not mod.startswith(PKG):
        return None
    p = SRC / Path(*mod.split("."))
    for c in (p.with_suffix(".py"), p / "__init__.py"):
        if c.exists():
            return c
    return None


def _closure(entry: Path):
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        for m in _imports(f):
            mf = _module_file(m)
            if mf:
                stack.append(mf)
    return seen


def test_entry_points_exist():
    assert (ROOT / "scripts" / "nhl_shadow_eval.py").exists() and len(ENTRY) >= 4


def test_no_transitive_import_of_order_or_sizing_code():
    for e in ENTRY:
        for f in _closure(e):
            for m in _imports(f):
                assert not any(b in m for b in FORBIDDEN_MODULES), f"{e.name} -> {f.name} imports {m}"


def test_no_order_or_sizing_identifiers_in_shadow_code():
    for e in ENTRY:
        for f in _closure(e):
            names = {n.id for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, ast.Name)} | \
                    {n.attr for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, ast.Attribute)} | \
                    {n.name for n in ast.walk(ast.parse(f.read_text())) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
            bad = [x for x in names if any(b.lower() in x.lower() for b in FORBIDDEN_NAMES)]
            assert not bad, f"{f.name}: {bad}"
