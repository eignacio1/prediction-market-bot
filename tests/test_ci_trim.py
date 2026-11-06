"""CI-trim guard: the workflow skip-list may ignore exploratory RESULTS files but never a .py file, and the
pre-PR selector picks the isolation fence for exploratory code."""
import fnmatch
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = yaml.safe_load((ROOT / ".github/workflows/tests.yml").read_text())
ON = WF.get("on", WF.get(True))


def _glob(pat, path):  # GitHub '**/' also matches zero directories
    return fnmatch.fnmatch(path, pat.replace("**/", "*")) or fnmatch.fnmatch(path, pat.replace("**/", ""))


def _ignored(path, trigger):
    return any(_glob(p, path) for p in ON[trigger]["paths-ignore"])


def test_exploratory_results_skip_ci_on_push_and_pr():
    for trig in ("push", "pull_request"):
        for f in ("12_EXPLORATORY/q/RESULT.md", "12_EXPLORATORY/q/results.json", "12_EXPLORATORY/q/deep/t.csv"):
            assert _ignored(f, trig), (trig, f)


def test_no_python_or_code_path_is_ever_skipped():
    for trig in ("push", "pull_request"):
        for f in ("12_EXPLORATORY/q/analyze.py", "src/prediction_market_bot/x.py", "tests/test_x.py", "scripts/a.py",
                  ".github/workflows/tests.yml", "pyproject.toml", "configs/a.json", "src/x/data.csv"):
            assert not _ignored(f, trig), (trig, f)


def test_selector_picks_fence_and_matching_tests():
    import importlib.util
    spec = importlib.util.spec_from_file_location("pc", ROOT / "scripts/precheck_changed.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    allt = ["tests/test_exploratory_isolation.py", "tests/test_quant_price_dynamics.py", "tests/test_other.py"]
    got = m.select(["12_EXPLORATORY/q/analyze.py", "src/prediction_market_bot/quant/price_dynamics.py", "docs.md"], allt)
    assert "tests/test_exploratory_isolation.py" in got and "tests/test_quant_price_dynamics.py" in got
    assert "tests/test_other.py" not in got
