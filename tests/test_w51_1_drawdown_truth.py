"""W51.1: dashboard drawdown must be the REALIZED quantity the kill switch reads."""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import web_dashboard as wd

NOW = datetime(2026, 10, 3, 20, 0, tzinfo=timezone.utc)


def test_frozen_label_over_72h():
    assert wd._frozen_label("2026-08-06T00:05:01.517Z", NOW) == "FROZEN (last write 2026-08-06)"


def test_not_frozen_within_72h():
    assert wd._frozen_label("2026-10-02T12:00:00Z", NOW) is None


def test_frozen_label_unparseable_is_none():
    assert wd._frozen_label(None, NOW) is None


def test_js_rail_uses_realized_not_bankroll_gap():
    src = Path(wd.__file__).read_text()
    assert "Math.max(0,-D.P.total_realized_pnl)" in src
    assert "(D.P.initial_bankroll_usd-D.P.bankroll_usd)" not in src
    assert "max(0.0, -rpnl) / init" in src
