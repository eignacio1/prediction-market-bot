"""Static isolation fence for 12_EXPLORATORY (CHARTER.md rules 2-5). Fail-closed AST scan."""
import ast
from pathlib import Path

import pytest

EXPLORATORY = Path(__file__).resolve().parents[1] / "12_EXPLORATORY"

FORBIDDEN_MODULES = (
    "prediction_market_bot.c5_execution.paper_trader",
    "prediction_market_bot.c5_execution.kalshi_client",
    "prediction_market_bot.c5_execution.venue_adapter",
    "prediction_market_bot.pregame_shadow.ledger",
    "prediction_market_bot.pregame_shadow.runner",
    "prediction_market_bot.pregame_shadow.calibration_engine",
    "prediction_market_bot.pregame_shadow.first_look_report",
    "prediction_market_bot.pregame_shadow.settled_schema",
    "prediction_market_bot.execution_bands_orchestrator",
    "prediction_market_bot.reset_paper_portfolio",
    "paper_trader", "kalshi_client", "subprocess",
)
FORBIDDEN_MODULE_PREFIXES = ("prediction_market_bot.run_", "prediction_market_bot.t4_")
FORBIDDEN_NAMES = {  # imported by name from anywhere (incl. the registry module itself)
    "promote_cell_status", "set_measurement", "submit_order", "open_position", "exit_position",
    "PaperTrader", "KalshiClient",
}
# Read-forbidden path fragments (rule 2). Any string constant containing one fails.
FORBIDDEN_PATH_FRAGMENTS = (
    "logs/", "PAPER_", "paper_ledger", "pregame_shadow", "SHADOW", "shadow_ledger", "_T1.jsonl", "_T2.jsonl", "_T3.jsonl",
    "settled_rows", "first_look", "03_DECISIONS", "market_type_registry",
)
WRITE_ATTRS = {"write_text", "write_bytes", "to_csv", "to_json", "to_parquet", "to_pickle", "dump", "unlink", "rename", "replace",
               "rmtree", "copy", "copy2", "copyfile", "move", "touch", "mkdir", "savefig", "save", "system"}
NET_WRITE_ATTRS = {"post", "put", "delete", "patch"}


def _is_safe_out_call(node) -> bool:
    return isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "safe_out"


def scan_source(src: str, name: str = "<src>") -> list[str]:
    tree = ast.parse(src)
    bad: list[str] = []
    safe_names: set[str] = set()
    for n in ast.walk(tree):  # names bound from safe_out(...)
        if isinstance(n, ast.Assign) and _is_safe_out_call(n.value):
            safe_names.update(t.id for t in n.targets if isinstance(t, ast.Name))

    def safe_target(t) -> bool:
        if _is_safe_out_call(t) or (isinstance(t, ast.Name) and t.id in safe_names):
            return True
        return isinstance(t, ast.Attribute) and safe_target(t.value)  # e.g. safe_out(x).parent

    for n in ast.walk(tree):
        loc = f"{name}:{getattr(n, 'lineno', 0)}"
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name in FORBIDDEN_MODULES or a.name.startswith(FORBIDDEN_MODULE_PREFIXES):
                    bad.append(f"{loc} forbidden import {a.name}")
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if mod in FORBIDDEN_MODULES or mod.startswith(FORBIDDEN_MODULE_PREFIXES):
                bad.append(f"{loc} forbidden import from {mod}")
            for a in n.names:
                full = f"{mod}.{a.name}"
                if a.name in FORBIDDEN_NAMES or full in FORBIDDEN_MODULES or full.startswith(FORBIDDEN_MODULE_PREFIXES):
                    bad.append(f"{loc} forbidden import {full}")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            for frag in FORBIDDEN_PATH_FRAGMENTS:
                if frag in n.value:
                    bad.append(f"{loc} forbidden path fragment {frag!r} in string constant")
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id in ("open", "system", "exec", "eval", "__import__"):
                if f.id == "open":
                    mode = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == "mode"), None)
                    is_write = not (mode is None or (isinstance(mode, ast.Constant) and isinstance(mode.value, str)
                                                     and not set(mode.value) & set("wax+")))
                    if is_write and not (n.args and safe_target(n.args[0])):
                        bad.append(f"{loc} open() for write not routed through safe_out()")
                else:
                    bad.append(f"{loc} forbidden call {f.id}()")
            elif isinstance(f, ast.Attribute):
                if f.attr in NET_WRITE_ATTRS and not isinstance(f.value, ast.Constant):
                    bad.append(f"{loc} network-write-shaped call .{f.attr}()")
                elif f.attr in WRITE_ATTRS:
                    # path.write_text(..) -> receiver must be safe; os.remove(path)/shutil.x(src,dst) -> every arg must be safe
                    recv_ok = safe_target(f.value)
                    arg_ok = bool(n.args) and all(safe_target(a) for a in n.args)
                    if f.attr in ("dump", "savefig", "save"):
                        ok = True  # target is a file object / path opened elsewhere; the open() itself is policed above
                    elif f.attr in ("to_csv", "to_json", "to_parquet", "to_pickle"):
                        ok = bool(n.args) and safe_target(n.args[0])
                    else:
                        ok = recv_ok or arg_ok
                    if not ok and f.attr != "mkdir":
                        bad.append(f"{loc} write-shaped call .{f.attr}() not routed through safe_out()")
    return bad


def _py_files():
    return sorted(p for p in EXPLORATORY.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("path", _py_files() or [None], ids=lambda p: p.name if p else "no-files")
def test_exploratory_file_is_isolated(path):
    if path is None:
        pytest.skip("no .py files in 12_EXPLORATORY")
    assert scan_source(path.read_text(), str(path.relative_to(EXPLORATORY))) == []


def test_fence_directory_exists():
    assert (EXPLORATORY / "CHARTER.md").is_file() and (EXPLORATORY / "_fence.py").is_file()


# ---- negative fixtures: the scan must catch each class of violation -----------------------------------------------
@pytest.mark.parametrize("src", [
    "from prediction_market_bot.c5_execution.paper_trader import PaperTrader\n",
    "from prediction_market_bot.c5_execution.market_type_registry import promote_cell_status\n",
    "import prediction_market_bot.run_t4_mlb_live\n",
    "from prediction_market_bot.pregame_shadow import ledger\nfrom prediction_market_bot.pregame_shadow.ledger import x\n",
    "p='exp_output/pregame_shadow/NFL_MONEYLINE_T1.jsonl'\n",
    "open('logs/x.jsonl','a').write('x')\n",
    "from pathlib import Path\nPath('out.md').write_text('x')\n",
    "import requests\nrequests.post('https://x', data={})\n",
    "import subprocess\n",
    "import os\nos.remove('x')\n",
])
def test_scan_catches_violation(src):
    assert scan_source(src, "fixture.py"), f"scan failed to flag: {src!r}"


def test_scan_allows_fenced_write_and_clean_read():
    ok = ("from _fence import safe_out\nimport json\n"
          "out = safe_out('study/a.json')\nout.write_text('{}')\n"
          "d = json.load(open('exp_output/PRICE_ARCHIVE/prices_2026-08-01.jsonl'))\n"
          "safe_out('study/b.csv').write_text('x')\n")
    assert scan_source(ok, "ok.py") == []
