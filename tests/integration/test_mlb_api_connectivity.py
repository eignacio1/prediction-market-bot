"""
Phase MLB-G1 — Integration Test 1: API Connectivity

Validates that all external data sources used by the MLB arm are reachable,
return well-formed responses, and meet latency SLAs from the current machine.

These are the checks that MUST pass before the MLB crons re-enable.
No mocks. Real HTTP calls.

Run: pytest tests/integration/test_mlb_api_connectivity.py -v -m integration
"""
import re
import time
from datetime import datetime, timedelta, timezone

import pytest
import requests

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MLB_BASE = "https://statsapi.mlb.com"
_ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
_ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/summary"
_ESPN_HEADERS = {"User-Agent": "Mozilla/5.0"}

_LATENCY_SLA_S = 5.0   # any API must respond within 5 seconds
_ESPN_T4_SLA_S = 10.0  # T4 polling — must complete in 10s (45s loop, 10s budget per call)

_KNOWN_GAME_DATE = "2026-06-24"  # recent date with confirmed games
_KNOWN_PLAYER_ID = 592450        # Aaron Judge — always has 2026 data if season active


# ---------------------------------------------------------------------------
# MLB Stats API
# ---------------------------------------------------------------------------

class TestMLBStatsAPIConnectivity:
    """Core MLB Stats API endpoints used by T1, T2, and resolution pipeline."""

    def test_schedule_endpoint_reachable(self):
        """GET /api/v1/schedule returns 200 within SLA."""
        today = datetime.now(tz=timezone.utc).date().isoformat()
        t0 = time.monotonic()
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/schedule",
            params={"sportId": 1, "date": today},
            timeout=_LATENCY_SLA_S,
        )
        elapsed = time.monotonic() - t0
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        assert elapsed < _LATENCY_SLA_S, f"Latency {elapsed:.2f}s exceeds SLA {_LATENCY_SLA_S}s"

    def test_schedule_response_structure(self):
        """Schedule response has expected top-level keys."""
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/schedule",
            params={"sportId": 1, "date": _KNOWN_GAME_DATE},
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dates" in data, f"'dates' key missing. Got: {list(data.keys())}"
        assert "totalGames" in data, f"'totalGames' key missing"

    def test_schedule_known_date_has_games(self):
        """Known game date returns at least one game."""
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/schedule",
            params={"sportId": 1, "date": _KNOWN_GAME_DATE},
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code == 200
        data = resp.json()
        games = [g for d in data.get("dates", []) for g in d.get("games", [])]
        assert len(games) > 0, f"Expected games on {_KNOWN_GAME_DATE}, got 0"

    def test_probable_pitcher_hydration(self):
        """Schedule with hydrate=probablePitcher returns pitcher data."""
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/schedule",
            params={
                "sportId": 1,
                "date": _KNOWN_GAME_DATE,
                "hydrate": "probablePitcher",
            },
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code == 200
        data = resp.json()
        games = [g for d in data.get("dates", []) for g in d.get("games", [])]
        assert len(games) > 0
        # At least some games should have probablePitcher field
        has_pitcher = any("probablePitcher" in t for g in games for t in g.get("teams", {}).values())
        assert has_pitcher, "No probablePitcher data returned in any game on known date"

    def test_lineup_hydration(self):
        """Schedule with hydrate=lineups,team returns team lineup data."""
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/schedule",
            params={
                "sportId": 1,
                "date": _KNOWN_GAME_DATE,
                "hydrate": "lineups,team",
            },
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code == 200
        data = resp.json()
        games = [g for d in data.get("dates", []) for g in d.get("games", [])]
        assert len(games) > 0
        # Team data should be hydrated
        has_team = any("team" in t for g in games for t in g.get("teams", {}).values())
        assert has_team, "No team data returned with hydrate=lineups,team on known date"

    def test_player_game_log_accessible(self):
        """Player game log endpoint returns stats for known player."""
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/people/{_KNOWN_PLAYER_ID}/stats",
            params={"stats": "gameLog", "group": "hitting", "season": 2026},
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code == 200, f"HTTP {resp.status_code} for player {_KNOWN_PLAYER_ID}"
        data = resp.json()
        assert "stats" in data, f"'stats' key missing from game log response"
        stat_groups = data["stats"]
        assert len(stat_groups) > 0, "Empty stats list for known player in 2026"

    def test_player_game_log_has_hits_field(self):
        """Player game log rows include hits field (used by resolution pipeline)."""
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/people/{_KNOWN_PLAYER_ID}/stats",
            params={"stats": "gameLog", "group": "hitting", "season": 2026},
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code == 200
        data = resp.json()
        games = []
        for sg in data.get("stats", []):
            games.extend(sg.get("splits", []))
        assert len(games) > 0, "No game splits found for known player"
        sample = games[0].get("stat", {})
        assert "hits" in sample, f"'hits' field missing from game log stat. Got: {list(sample.keys())}"
        assert "atBats" in sample, f"'atBats' field missing from game log stat"

    def test_2025_season_blocked_from_vps(self):
        """
        Historical seasons (≤2025) are blocked from DigitalOcean IPs (Fastly/Akamai CDN).
        This test documents the constraint — it PASSES if 2025 returns a non-200 OR if
        it returns 200 (policy may have changed). It FAILS only if behaviour is unknown.

        If this test starts returning 200 for 2025, the IP-blocking constraint in
        cron.conf PIPE-05FX comment should be updated.
        """
        resp = requests.get(
            f"{_MLB_BASE}/api/v1/people/{_KNOWN_PLAYER_ID}/stats",
            params={"stats": "gameLog", "group": "hitting", "season": 2025},
            timeout=_LATENCY_SLA_S,
        )
        # Document actual status — do not assert a specific code since policy can change
        print(f"\n[INFO] 2025 season game log HTTP status from this machine: {resp.status_code}")
        # This always passes — it's a documentation/alerting test, not a gate


# ---------------------------------------------------------------------------
# ESPN APIs (used by T3 and T4)
# ---------------------------------------------------------------------------

class TestESPNAPIConnectivity:
    """ESPN baseball endpoints used by T4 in-play polling."""

    def test_scoreboard_reachable(self):
        """ESPN MLB scoreboard returns 200 within SLA."""
        t0 = time.monotonic()
        resp = requests.get(_ESPN_SCOREBOARD, headers=_ESPN_HEADERS, timeout=_LATENCY_SLA_S)
        elapsed = time.monotonic() - t0
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        assert elapsed < _LATENCY_SLA_S, f"Latency {elapsed:.2f}s exceeds SLA {_LATENCY_SLA_S}s"

    def test_scoreboard_structure(self):
        """ESPN scoreboard response has required top-level keys."""
        resp = requests.get(_ESPN_SCOREBOARD, headers=_ESPN_HEADERS, timeout=_LATENCY_SLA_S)
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data, f"'events' key missing. Got: {list(data.keys())}"

    def test_scoreboard_event_structure(self):
        """Each scoreboard event has the fields T4 polling reads."""
        resp = requests.get(_ESPN_SCOREBOARD, headers=_ESPN_HEADERS, timeout=_LATENCY_SLA_S)
        assert resp.status_code == 200
        data = resp.json()
        events = data.get("events", [])
        if not events:
            pytest.skip("No events on scoreboard right now — run during MLB season")
        event = events[0]
        assert "id" in event, "'id' missing from scoreboard event"
        assert "status" in event, "'status' missing from scoreboard event"
        status = event["status"]
        assert "type" in status, "'type' missing from event status"
        assert "name" in status["type"], "'name' missing from status type"

    def test_scoreboard_latency_meets_t4_sla(self):
        """ESPN scoreboard responds within T4 SLA (10s per poll cycle)."""
        t0 = time.monotonic()
        resp = requests.get(_ESPN_SCOREBOARD, headers=_ESPN_HEADERS, timeout=_ESPN_T4_SLA_S)
        elapsed = time.monotonic() - t0
        assert resp.status_code == 200
        assert elapsed < _ESPN_T4_SLA_S, (
            f"ESPN scoreboard latency {elapsed:.2f}s exceeds T4 SLA {_ESPN_T4_SLA_S}s. "
            f"T4 budget per poll: {_ESPN_T4_SLA_S}s within 45s evaluation loop."
        )

    def test_summary_endpoint_reachable(self):
        """ESPN MLB summary (boxscore) endpoint is reachable."""
        # Use a real recent game_id from the scoreboard if available
        scoreboard = requests.get(_ESPN_SCOREBOARD, headers=_ESPN_HEADERS, timeout=_LATENCY_SLA_S)
        assert scoreboard.status_code == 200
        events = scoreboard.json().get("events", [])
        if not events:
            pytest.skip("No scoreboard events — test during season")
        game_id = events[0]["id"]
        resp = requests.get(
            _ESPN_SUMMARY,
            params={"event": game_id},
            headers=_ESPN_HEADERS,
            timeout=_LATENCY_SLA_S,
        )
        assert resp.status_code in (200, 404), (
            f"Unexpected HTTP {resp.status_code} from ESPN summary for event={game_id}"
        )

    def test_summary_boxscore_has_player_stats(self):
        """ESPN boxscore for an in-progress or completed game has player batting stats."""
        scoreboard = requests.get(_ESPN_SCOREBOARD, headers=_ESPN_HEADERS, timeout=_LATENCY_SLA_S)
        assert scoreboard.status_code == 200
        events = scoreboard.json().get("events", [])
        if not events:
            pytest.skip("No scoreboard events — test during season")

        # Try each event until we find one with a valid boxscore
        for event in events[:5]:
            resp = requests.get(
                _ESPN_SUMMARY,
                params={"event": event["id"]},
                headers=_ESPN_HEADERS,
                timeout=_LATENCY_SLA_S,
            )
            if resp.status_code != 200:
                continue
            data = resp.json()
            boxscore = data.get("boxscore", {})
            players = boxscore.get("players", [])
            if players:
                # Verify structure T4 expects
                team_players = players[0] if players else {}
                stats_list = team_players.get("statistics", [])
                if stats_list:
                    stat_block = stats_list[0]
                    assert "athletes" in stat_block, "'athletes' missing from boxscore statistics"
                    return  # found valid boxscore — test passes
        pytest.skip("No in-progress/completed games with boxscore data — test during active games")


# ---------------------------------------------------------------------------
# Kalshi MLB Markets
# ---------------------------------------------------------------------------

class TestKalshiMLBMarketConnectivity:
    """Kalshi KXMLBHIT market fetch and structural validation."""

    def test_kxmlbhit_fetch_succeeds(self, kalshi_mlb_snapshot):
        """Kalshi KXMLBHIT market fetch returns a snapshot."""
        assert kalshi_mlb_snapshot is not None
        assert hasattr(kalshi_mlb_snapshot, "markets")

    def test_kxmlbhit_markets_exist_during_season(self, kalshi_mlb_snapshot):
        """At least some KXMLBHIT markets exist during MLB season."""
        markets = kalshi_mlb_snapshot.markets
        print(f"\n[INFO] Total KXMLBHIT markets: {len(markets)}")
        active = [m for m in markets if m.status == "active"]
        quoted = [m for m in markets if m.status == "active" and m.has_live_quotes]
        print(f"[INFO] Active: {len(active)}, Quoted: {len(quoted)}")
        # Not a hard failure — off-season = 0 markets is valid
        # But log so operator knows
        if len(active) == 0:
            pytest.skip("No active KXMLBHIT markets — MLB off-season or pre-season")

    def test_ticker_format_parseable(self, kalshi_mlb_snapshot):
        """All active/quoted market tickers parse to valid dates via T1 regex."""
        active_quoted = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.has_live_quotes
        ]
        if not active_quoted:
            pytest.skip("No active/quoted markets")

        pattern = re.compile(r"-([0-9]{2})([A-Z]{3})([0-9]{2})[0-9]{4}")
        unparseable = []
        for m in active_quoted:
            if not pattern.search(m.ticker):
                unparseable.append(m.ticker)

        assert len(unparseable) == 0, (
            f"{len(unparseable)} tickers failed T1 date-parse regex:\n"
            + "\n".join(f"  {t}" for t in unparseable[:10])
        )

    def test_ticker_dates_are_current_or_future(self, kalshi_mlb_snapshot):
        """Active/quoted market ticker dates are today or in the future (not stale)."""
        from datetime import datetime, timezone
        active_quoted = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.has_live_quotes
        ]
        if not active_quoted:
            pytest.skip("No active/quoted markets")

        pattern = re.compile(r"-([0-9]{2})([A-Z]{3})([0-9]{2})[0-9]{4}")
        today = datetime.now(tz=timezone.utc).date()
        stale = []
        for m in active_quoted:
            match = pattern.search(m.ticker)
            if match:
                try:
                    game_date = datetime.strptime(
                        match.group(1) + match.group(2) + match.group(3), "%d%b%y"
                    ).date()
                    days_past = (today - game_date).days
                    if days_past > 1:  # allow 1 day lag for late-resolving games
                        stale.append((m.ticker, game_date.isoformat(), days_past))
                except ValueError:
                    pass

        if stale:
            stale_detail = "\n".join(f"  {t} (game {d}, {n} days past)" for t, d, n in stale[:10])
            pytest.fail(
                f"{len(stale)} active/quoted markets have stale ticker dates (>1 day past):\n"
                f"{stale_detail}\n"
                f"This suggests Kalshi has not resolved/expired old markets. "
                f"T1 date filter will exclude these correctly but total market count is inflated."
            )

    def test_player_names_are_strings(self, kalshi_mlb_snapshot):
        """All active market player_name attributes are non-empty strings."""
        active = [m for m in kalshi_mlb_snapshot.markets if m.status == "active"]
        if not active:
            pytest.skip("No active markets")
        empty_names = [m.ticker for m in active if not m.player_name or not m.player_name.strip()]
        assert len(empty_names) == 0, (
            f"{len(empty_names)} active markets have empty player_name:\n"
            + "\n".join(f"  {t}" for t in empty_names[:10])
        )

    def test_thresholds_match_model_scope(self, kalshi_mlb_snapshot):
        """Active market thresholds are within model scope (1 and 2; 3 excluded)."""
        active_quoted = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.has_live_quotes
        ]
        if not active_quoted:
            pytest.skip("No active/quoted markets")

        _MODEL_THRESHOLDS = frozenset({1, 2})
        out_of_scope = {}
        for m in active_quoted:
            t = int(m.threshold) if m.threshold else -1
            if t not in _MODEL_THRESHOLDS:
                out_of_scope[t] = out_of_scope.get(t, 0) + 1

        if out_of_scope:
            print(
                f"\n[INFO] Out-of-scope thresholds found (will be silently skipped by T1):\n"
                + "\n".join(f"  threshold={k}: {v} markets" for k, v in sorted(out_of_scope.items()))
            )
        # Not a hard failure — T1 skips these with a log line — but log them

    def test_mid_price_is_valid_probability(self, kalshi_mlb_snapshot):
        """All quoted market mid-prices are valid probabilities (0 < p < 1)."""
        quoted = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.has_live_quotes
        ]
        if not quoted:
            pytest.skip("No quoted markets")

        invalid = []
        for m in quoted:
            mid = (m.yes_bid + m.yes_ask) / 2 if m.yes_bid is not None and m.yes_ask is not None else None
            if mid is None or not (0.0 < mid < 1.0):
                invalid.append((m.ticker, mid))

        assert len(invalid) == 0, (
            f"{len(invalid)} markets have invalid mid-price:\n"
            + "\n".join(f"  {t}: mid={p}" for t, p in invalid[:10])
        )
