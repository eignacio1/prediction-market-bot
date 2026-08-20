"""
Tests for market_type_registry.py (T-439, Market Expansion Phase 1 box 1.1/1.3).
"""

from __future__ import annotations

import pytest

from prediction_market_bot.execution_bands import ExecutionBand
from prediction_market_bot.c5_execution.market_type_registry import (
    MARKET_TYPE_REGISTRY,
    CellKillSwitchStatus,
    CellMeasurement,
    CellStatus,
    MarketType,
    MarketTypeCell,
    TickerDateParseError,
    cells_by_status,
    cells_for_market_type,
    derive_game_date,
    get_cell,
    get_measurement,
    halt_cell,
    market_type_for_series_ticker,
    market_type_for_ticker,
    parse_ticker_date,
    promote_cell_status,
    resolve_kill_switch_state,
    series_ticker_for,
    set_measurement,
)


# ---------------------------------------------------------------------------
# Legacy-constant regression guard (box 1.3's explicit requirement)
# ---------------------------------------------------------------------------


class TestLegacyAliasRegression:
    """The two pre-existing kalshi_client.py constants must keep resolving to
    their historical literal values through the registry — a value drift here
    would silently misroute every NBA/MLB market-data fetch."""

    def test_series_player_points_alias_unchanged(self):
        from prediction_market_bot.c5_execution.kalshi_client import SERIES_PLAYER_POINTS
        assert SERIES_PLAYER_POINTS == "KXNBAPTS"

    def test_series_mlb_player_hits_alias_unchanged(self):
        from prediction_market_bot.c5_execution.kalshi_client import SERIES_MLB_PLAYER_HITS
        assert SERIES_MLB_PLAYER_HITS == "KXMLBHIT"

    def test_aliases_match_registry_lookup(self):
        from prediction_market_bot.c5_execution.kalshi_client import (
            SERIES_MLB_PLAYER_HITS,
            SERIES_PLAYER_POINTS,
        )
        assert SERIES_PLAYER_POINTS == series_ticker_for(MarketType.NBA_PLAYER_POINTS)
        assert SERIES_MLB_PLAYER_HITS == series_ticker_for(MarketType.MLB_PLAYER_PROP_HITS)


# ---------------------------------------------------------------------------
# Registry shape / starting-state honesty
# ---------------------------------------------------------------------------


class TestRegistryStartingState:
    def test_exactly_one_active_cell(self):
        active = cells_by_status(CellStatus.ACTIVE)
        assert len(active) == 1
        cell = active[0]
        assert cell.market_type is MarketType.MLB_PLAYER_PROP_HITS
        assert cell.band is ExecutionBand.T4M_PROJ

    def test_no_cells_ruled_out_yet(self):
        """Phase 0-I's depth signal exists but the operator has not promoted
        either family to a kill decision ('neither declared dead') — the
        registry must not invent a verdict that isn't the operator's."""
        assert cells_by_status(CellStatus.RULED_OUT) == []

    def test_blocked_cells_are_the_mlb_native_t4_subbands(self):
        blocked = {cell.band for cell in cells_by_status(CellStatus.BLOCKED)}
        assert blocked == {ExecutionBand.T4M_ARITH, ExecutionBand.T4M_FLOW}

    def test_every_other_cell_is_not_implemented_or_dark(self):
        allowed = {CellStatus.NOT_IMPLEMENTED, CellStatus.DARK}
        for cell in MARKET_TYPE_REGISTRY.values():
            if cell.status in (CellStatus.ACTIVE, CellStatus.BLOCKED):
                continue
            assert cell.status in allowed, cell

    def test_mlb_families_other_than_player_prop_have_no_active_or_blocked_cells(self):
        other_families = [
            MarketType.MLB_MONEYLINE,
            MarketType.MLB_RUN_LINE,
            MarketType.MLB_GAME_TOTAL,
            MarketType.MLB_TEAM_TOTAL,
            MarketType.MLB_PARTIAL_GAME,
        ]
        for market_type in other_families:
            for cell in cells_for_market_type(market_type):
                assert cell.status is CellStatus.NOT_IMPLEMENTED, cell


# ---------------------------------------------------------------------------
# Key shape — pair, not market_type alone
# ---------------------------------------------------------------------------


class TestRegistryKeyedOnPair:
    def test_get_cell_requires_both_market_type_and_band(self):
        active_cell = get_cell(MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T4M_PROJ)
        assert active_cell.status is CellStatus.ACTIVE

        # Same market type, different band -> different status. Proves the
        # band is part of the key, not an incidental attribute.
        pregame_cell = get_cell(MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T1_MULTI_DAY)
        assert pregame_cell.status is CellStatus.NOT_IMPLEMENTED

    def test_unseeded_pair_raises_keyerror(self):
        with pytest.raises(KeyError):
            get_cell(MarketType.MLB_MONEYLINE, ExecutionBand.T4M_PROJ)

    def test_series_ticker_constant_across_bands_for_same_family(self):
        tickers = {
            cell.series_ticker
            for cell in cells_for_market_type(MarketType.MLB_PLAYER_PROP_HITS)
        }
        assert tickers == {"KXMLBHIT"}


# ---------------------------------------------------------------------------
# RULED_OUT is a first-class state — schema enforces its evidence fields
# ---------------------------------------------------------------------------


class TestRuledOutRequiresEvidence:
    def test_ruled_out_without_reason_raises(self):
        import datetime
        with pytest.raises(ValueError):
            MarketTypeCell(
                MarketType.MLB_GAME_TOTAL,
                ExecutionBand.T1_MULTI_DAY,
                CellStatus.RULED_OUT,
                measured_date=datetime.date(2026, 8, 11),
            )

    def test_ruled_out_without_measured_date_raises(self):
        with pytest.raises(ValueError):
            MarketTypeCell(
                MarketType.MLB_GAME_TOTAL,
                ExecutionBand.T1_MULTI_DAY,
                CellStatus.RULED_OUT,
                reason="depth gate failed 3/3 pre-slate",
            )

    def test_ruled_out_with_both_fields_succeeds(self):
        import datetime
        cell = MarketTypeCell(
            MarketType.MLB_GAME_TOTAL,
            ExecutionBand.T1_MULTI_DAY,
            CellStatus.RULED_OUT,
            reason="depth gate failed 3/3 pre-slate",
            measured_date=datetime.date(2026, 8, 11),
        )
        assert cell.status is CellStatus.RULED_OUT

    def test_active_cell_does_not_require_reason_or_date(self):
        cell = MarketTypeCell(
            MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T4M_PROJ, CellStatus.ACTIVE,
        )
        assert cell.reason is None
        assert cell.measured_date is None


# ---------------------------------------------------------------------------
# T-466 — ACTIVE cells require formula-assertion coverage
# ---------------------------------------------------------------------------


class TestActiveRequiresFormulaCoverage:
    def test_active_cell_without_formula_coverage_raises(self):
        with pytest.raises(ValueError):
            MarketTypeCell(
                MarketType.MLB_MONEYLINE, ExecutionBand.T2_SAME_DAY, CellStatus.ACTIVE,
            )

    def test_active_cell_with_formula_coverage_succeeds(self):
        cell = MarketTypeCell(
            MarketType.MLB_PLAYER_PROP_HITS, ExecutionBand.T1_MULTI_DAY, CellStatus.ACTIVE,
        )
        assert cell.status is CellStatus.ACTIVE

    def test_shadow_cell_without_formula_coverage_still_succeeds(self):
        cell = MarketTypeCell(
            MarketType.MLB_GAME_TOTAL, ExecutionBand.T5_LATE_GAME, CellStatus.SHADOW,
        )
        assert cell.status is CellStatus.SHADOW

    def test_promote_to_active_on_uncovered_band_raises(self):
        with pytest.raises(ValueError):
            promote_cell_status(
                MarketType.MLB_TEAM_TOTAL, ExecutionBand.T3_PRE_TIP, CellStatus.ACTIVE,
            )


# ---------------------------------------------------------------------------
# ADR-0053 §6.3 item 1 — reverse ticker -> market_type lookup
# ---------------------------------------------------------------------------


class TestReverseTickerLookup:
    def test_round_trips_for_every_market_type(self):
        for market_type in MarketType:
            ticker = series_ticker_for(market_type)
            assert market_type_for_series_ticker(ticker) is market_type

    def test_unknown_ticker_raises_keyerror(self):
        with pytest.raises(KeyError):
            market_type_for_series_ticker("KXNOTAREALSERIES")


# ---------------------------------------------------------------------------
# ADR-0053 §6.3 item 5 — SHADOW status + citing_decision + promotion guard
# ---------------------------------------------------------------------------


class TestShadowStatus:
    def test_shadow_cell_constructs_without_reason_or_date(self):
        cell = MarketTypeCell(
            MarketType.MLB_GAME_TOTAL, ExecutionBand.T1_MULTI_DAY, CellStatus.SHADOW,
        )
        assert cell.status is CellStatus.SHADOW


class TestCitingDecisionField:
    def test_citing_decision_optional_and_settable(self):
        import datetime
        cell = MarketTypeCell(
            MarketType.MLB_GAME_TOTAL,
            ExecutionBand.T1_MULTI_DAY,
            CellStatus.RULED_OUT,
            reason="depth gate failed 3/3 pre-slate",
            measured_date=datetime.date(2026, 8, 11),
        )
        assert cell.citing_decision is None

        cited = MarketTypeCell(
            MarketType.MLB_GAME_TOTAL,
            ExecutionBand.T1_MULTI_DAY,
            CellStatus.RULED_OUT,
            reason="depth gate failed 3/3 pre-slate",
            measured_date=datetime.date(2026, 8, 11),
            citing_decision="GG-999",
        )
        assert cited.citing_decision == "GG-999"


class TestPromoteCellStatus:
    def _seed_ruled_out(self):
        import datetime
        key = (MarketType.MLB_TEAM_TOTAL, ExecutionBand.T3_PRE_TIP)
        MARKET_TYPE_REGISTRY[key] = MarketTypeCell(
            MarketType.MLB_TEAM_TOTAL,
            ExecutionBand.T3_PRE_TIP,
            CellStatus.RULED_OUT,
            reason="test fixture",
            measured_date=datetime.date(2026, 8, 11),
        )
        return key

    def test_promotion_without_guard_condition_succeeds(self):
        key = (MarketType.MLB_PARTIAL_GAME, ExecutionBand.T5_LATE_GAME)
        original = MARKET_TYPE_REGISTRY[key]
        try:
            promoted = promote_cell_status(
                MarketType.MLB_PARTIAL_GAME, ExecutionBand.T5_LATE_GAME, CellStatus.SHADOW,
            )
            assert promoted.status is CellStatus.SHADOW
            assert MARKET_TYPE_REGISTRY[key].status is CellStatus.SHADOW
        finally:
            MARKET_TYPE_REGISTRY[key] = original

    def test_ruled_out_to_active_without_superseding_reference_raises(self):
        key = self._seed_ruled_out()
        try:
            with pytest.raises(ValueError):
                promote_cell_status(
                    MarketType.MLB_TEAM_TOTAL, ExecutionBand.T3_PRE_TIP, CellStatus.ACTIVE,
                )
        finally:
            del MARKET_TYPE_REGISTRY[key]

    def test_ruled_out_to_shadow_with_superseding_reference_succeeds(self):
        key = self._seed_ruled_out()
        try:
            promoted = promote_cell_status(
                MarketType.MLB_TEAM_TOTAL,
                ExecutionBand.T3_PRE_TIP,
                CellStatus.SHADOW,
                superseding_reference="GG-999",
            )
            assert promoted.status is CellStatus.SHADOW
            assert promoted.citing_decision == "GG-999"
        finally:
            del MARKET_TYPE_REGISTRY[key]

    def test_unseeded_pair_raises_keyerror(self):
        with pytest.raises(KeyError):
            promote_cell_status(
                MarketType.MLB_MONEYLINE, ExecutionBand.T4M_PROJ, CellStatus.SHADOW,
            )


# ---------------------------------------------------------------------------
# ADR-0053 §6.3 item 3 — per-cell measurement state
# ---------------------------------------------------------------------------


class TestCellMeasurement:
    def test_unmeasured_cell_returns_safe_default(self):
        m = get_measurement(MarketType.MLB_MONEYLINE, ExecutionBand.T4M_PROJ)
        assert m.clean_n == 0
        assert m.n_star is None

    def test_set_then_get_round_trips(self):
        key_args = (MarketType.MLB_RUN_LINE, ExecutionBand.T1_MULTI_DAY)
        try:
            set_measurement(*key_args, CellMeasurement(clean_n=42, n_star=100))
            m = get_measurement(*key_args)
            assert m.clean_n == 42
            assert m.n_star == 100
        finally:
            from prediction_market_bot.c5_execution import market_type_registry as _m
            _m._CELL_MEASUREMENTS.pop(key_args, None)


# ---------------------------------------------------------------------------
# ADR-0053 §6.3 item 4 — per-cell kill-switch state (seam only, not wired)
# ---------------------------------------------------------------------------


class TestCellKillSwitchState:
    def test_unhalted_cell_defaults_to_active(self):
        state = resolve_kill_switch_state(MarketType.MLB_MONEYLINE, ExecutionBand.T4M_PROJ)
        assert state.status is CellKillSwitchStatus.ACTIVE

    def test_halt_then_resolve_round_trips(self):
        key_args = (MarketType.MLB_GAME_TOTAL, ExecutionBand.T4M_ARITH)
        try:
            halt_cell(*key_args, "test halt")
            state = resolve_kill_switch_state(*key_args)
            assert state.status is CellKillSwitchStatus.HALTED
            assert state.reason == "test halt"
            assert state.halted_at is not None
        finally:
            from prediction_market_bot.c5_execution import market_type_registry as _m
            _m._CELL_KILL_SWITCH_STATE.pop(key_args, None)


# ---------------------------------------------------------------------------
# T-472/GG-191 — series-agnostic ticker date grammar, refusal-only contract
# ---------------------------------------------------------------------------


class TestTickerDateGrammar:
    def test_mlb_ticker_parses_date_and_teams(self):
        parsed = parse_ticker_date("KXMLBHIT-26AUG011610MIANYM-T1.5")
        assert parsed.game_date == "2026-08-01"
        assert parsed.teams_raw == "MIANYM"

    def test_nba_ticker_parses_date_without_hhmm(self):
        parsed = parse_ticker_date("KXNBAPTS-26JUN05NYKSAS-T25.5")
        assert parsed.game_date == "2026-06-05"
        assert parsed.teams_raw == "NYKSAS"

    def test_mlb_doubleheader_suffix_does_not_break_parse(self):
        # 21/2948 real tickers failed here before the team-code class was
        # widened from [A-Z]+ to [A-Z0-9]+ (see module docstring).
        parsed = parse_ticker_date("KXMLBHIT-26JUL041900TBBOSG1-T1.5")
        assert parsed.game_date == "2026-07-04"
        assert parsed.teams_raw == "TBBOSG1"

    def test_derive_game_date_matches_parse_ticker_date(self):
        assert derive_game_date("KXMLBHIT-26AUG011610MIANYM-T1.5") == "2026-08-01"

    def test_f5_and_f7_aliases_resolve_to_mlb_partial_game_grammar(self):
        for series in ("KXMLBF5", "KXMLBF7"):
            ticker = f"{series}-26AUG011610MIANYM-T1.5"
            assert market_type_for_ticker(ticker) is MarketType.MLB_PARTIAL_GAME
            parsed = parse_ticker_date(ticker)
            assert parsed.game_date == "2026-08-01"

    def test_unregistered_series_raises_keyerror_not_fallback(self):
        with pytest.raises(KeyError):
            parse_ticker_date("KXMLBUNKNOWNSERIES-26AUG011610MIANYM-T1.5")

    def test_malformed_tail_raises_ticker_date_parse_error_not_fallback(self):
        with pytest.raises(TickerDateParseError):
            parse_ticker_date("KXMLBHIT-NOT-A-VALID-TAIL")

    def test_unrecognized_month_token_raises(self):
        with pytest.raises(TickerDateParseError):
            parse_ticker_date("KXMLBHIT-26XXX011610MIANYM-T1.5")

    def test_ticker_with_no_series_separator_raises(self):
        # Registered series prefix (so market_type_for_ticker succeeds) but no
        # '-' anywhere in the ticker -- TickerGrammar.parse's own separator
        # check must fire, not a KeyError from the series lookup.
        with pytest.raises(TickerDateParseError):
            parse_ticker_date("KXMLBHIT")
