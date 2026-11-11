import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dmi", ROOT / "scripts/dashboard_memmax_install.py")
dmi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmi)


def test_dropin_targets_only_the_dashboard_and_raises_the_cap():
    assert dmi.UNIT == "pmbot-web-dashboard.service" and "t4" not in str(dmi.DROPIN)
    assert "MemoryMax=384M" in dmi.CONTENT and dmi.CONTENT.count("[Service]") == 1


def test_unknown_command_is_refused():
    assert dmi.main(["x", "bogus"]) == 2
