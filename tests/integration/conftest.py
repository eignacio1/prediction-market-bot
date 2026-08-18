"""
Phase MLB-G1 integration test fixtures.

All tests in this directory make REAL network calls. They are gated behind
pytest.mark.integration and never run in standard CI.

Run manually:
    pytest tests/integration/ -v -m integration

Requirements:
    - .env file loaded (VENUE_API_KEY, VENUE_PRIVATE_KEY_PATH set)
    - Network access to statsapi.mlb.com, site.api.espn.com, kalshi.com
    - exp_output/MLB/mlb_feature_matrix.csv present

GG-179/T-464 (2026-08-18): the feature-CSV-only tests in this directory
(no Kalshi credentials needed) don't need real production data to exercise
real code — they need a CSV that is *shaped* like the real one. When
MLB_CI_SYNTHETIC_FIXTURE=1 is set (CI sets this; local/VPS runs never do),
`feature_csv_path` synthesizes one in a tmp dir instead of skipping. This
intentionally does NOT cover the 6 tests that also require a trained model
.pkl (TestModelArtifact class + the two feature-vector/scoring tests in
test_mlb_pipeline_smoke.py) or the Kalshi-network-gated tests — those stay
skipped in CI with an explicit reason; see GG-179 for the disposition.
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Ensure src/ is on path when running from project root
_PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# Known real players the MLB-G1 name-matching regression gate
# (test_known_players_always_match) requires to be present and
# normalize-matchable. Keep in sync with that test's expected list.
_SYNTHETIC_KNOWN_PLAYERS = ["Elly De La Cruz", "Manny Machado", "Jackson Merrill"]
# test_feature_csv_has_players requires >=50 unique player names.
_SYNTHETIC_FILLER_COUNT = 50


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests making real network calls — run with -m integration",
    )


@pytest.fixture(scope="session")
def project_root() -> Path:
    return _PROJECT_ROOT


def _write_synthetic_feature_csv(out_dir: Path) -> Path:
    """
    Write a small, schema-correct synthetic feature CSV for CI.

    Not real MLB data — it exists to exercise CSV-shape and name-matching
    assertions (structure, non-null columns, date parseability, known-player
    presence) without requiring a generated production artifact. Dates are
    always "today" so the freshness gate (test_feature_csv_freshness)
    evaluates as fresh rather than skipping on staleness.
    """
    import pandas as pd

    today = datetime.now(tz=timezone.utc).date().isoformat()
    names = list(_SYNTHETIC_KNOWN_PLAYERS) + [
        f"Synthetic Fixture Player {i}" for i in range(_SYNTHETIC_FILLER_COUNT)
    ]
    rows = [
        {
            "player_id": idx + 1,
            "player_name": name,
            "game_date": today,
            "ba_l10": round(0.200 + (idx % 10) * 0.01, 3),
            "ab_l10": 30 + (idx % 10),
        }
        for idx, name in enumerate(names)
    ]
    out_path = out_dir / "mlb_feature_matrix_synthetic.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    return out_path


@pytest.fixture(scope="session")
def feature_csv_path(project_root, tmp_path_factory) -> Path:
    p = project_root / "exp_output" / "MLB" / "mlb_feature_matrix.csv"
    if p.exists():
        return p
    if os.environ.get("MLB_CI_SYNTHETIC_FIXTURE") == "1":
        return _write_synthetic_feature_csv(tmp_path_factory.mktemp("mlb_fixture"))
    pytest.skip(f"Feature CSV not found: {p}. Run scripts/generate_mlb_features.py first.")


@pytest.fixture(scope="session")
def kalshi_client():
    """Real KalshiMarketClient from environment credentials."""
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    try:
        return KalshiMarketClient.from_env()
    except Exception as e:
        pytest.skip(f"Kalshi client not available: {e}")


@pytest.fixture(scope="session")
def kalshi_mlb_snapshot(kalshi_client):
    """Live KXMLBHIT snapshot — fetched once per session."""
    from prediction_market_bot.c5_execution.kalshi_client import SERIES_MLB_PLAYER_HITS
    ok, snap = kalshi_client.fetch_player_points_markets(series_ticker=SERIES_MLB_PLAYER_HITS)
    if not ok or snap is None:
        pytest.skip("Kalshi KXMLBHIT fetch failed — check credentials and network.")
    return snap


@pytest.fixture(scope="session")
def feature_df(feature_csv_path):
    """Latest-row-per-player DataFrame from feature CSV."""
    import pandas as pd
    df = pd.read_csv(feature_csv_path, low_memory=False)
    df["game_date_dt"] = pd.to_datetime(df["game_date"], errors="coerce")
    return df.sort_values("game_date_dt").groupby("player_id").last().reset_index()
