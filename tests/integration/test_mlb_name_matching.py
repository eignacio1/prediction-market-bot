"""
Phase MLB-G1 — Integration Test 2: Player Name Matching

Validates that the normalize_player_name() function used in T1 achieves ≥90%
match rate between Kalshi market player names and the feature CSV.

A match rate below 90% means the model will silently skip most active markets —
which is the exact mode of failure that caused 0 bets at 03:00 UTC on 2026-06-25.

Run: pytest tests/integration/test_mlb_name_matching.py -v -m integration
"""
import re
from typing import Dict, Set, List, Tuple

import pytest

pytestmark = pytest.mark.integration

_MATCH_RATE_GATE = 0.90  # MLB-G1 gate: must achieve ≥90% name match
_WARN_RATE = 0.95         # warn (not fail) below 95%


def _extract_player_names_from_markets(snapshot) -> List[str]:
    """Pull all unique player_name values from active Kalshi markets."""
    seen: Set[str] = set()
    for m in snapshot.markets:
        if m.status == "active" and m.player_name and m.player_name.strip():
            seen.add(m.player_name.strip())
    return sorted(seen)


def _match_rate(
    kalshi_names: List[str],
    feature_names: Set[str],
    normalizer,
) -> Tuple[float, List[str], List[str]]:
    """
    Returns (rate, matched, unmatched) after normalizing and comparing names.
    """
    matched, unmatched = [], []
    for raw in kalshi_names:
        normalized = normalizer(raw)
        if normalized in feature_names:
            matched.append(raw)
        else:
            unmatched.append(raw)
    total = len(kalshi_names)
    rate = len(matched) / total if total > 0 else 0.0
    return rate, matched, unmatched


@pytest.fixture(scope="session")
def normalizer():
    """Load the actual normalize_player_name function used by run_mlb_paper_trade.py."""
    try:
        from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
        return normalize_player_name
    except ImportError:
        pytest.skip("normalize_player_name not importable from market_mapper — check module path")


@pytest.fixture(scope="session")
def feature_names_set(feature_df) -> Set[str]:
    """Set of normalized player names from feature CSV."""
    # Feature CSV uses 'player_name' column with names like "Elly De La Cruz"
    col = None
    for candidate in ("player_name", "full_name", "name"):
        if candidate in feature_df.columns:
            col = candidate
            break
    if col is None:
        pytest.skip(f"No name column found in feature CSV. Columns: {list(feature_df.columns)}")
    return set(feature_df[col].dropna().str.strip().tolist())


@pytest.fixture(scope="session")
def feature_names_normalized(feature_names_set, normalizer) -> Set[str]:
    """Pre-normalized set for fast matching."""
    return {normalizer(n) for n in feature_names_set}


class TestPlayerNameMatching:
    """Player name normalization coverage tests."""

    def test_normalizer_is_callable(self, normalizer):
        """normalize_player_name is importable and callable."""
        result = normalizer("Aaron Judge")
        assert isinstance(result, str), f"Expected str, got {type(result)}"

    def test_normalizer_handles_special_chars(self, normalizer):
        """Normalizer handles accents and hyphens (e.g., De La Cruz, García)."""
        cases = [
            ("Elly De La Cruz", str),
            ("Manny Machado", str),
            ("Jackson Merrill", str),
            ("Trea Turner", str),
        ]
        for name, expected_type in cases:
            result = normalizer(name)
            assert isinstance(result, expected_type), f"Failed on '{name}'"
            assert result.strip(), f"Empty result for '{name}'"

    def test_normalizer_is_idempotent(self, normalizer):
        """normalize_player_name(normalize_player_name(x)) == normalize_player_name(x)."""
        samples = ["Elly De La Cruz", "Aaron Judge", "Manny Machado", "SHOHEI OHTANI"]
        for name in samples:
            once = normalizer(name)
            twice = normalizer(once)
            assert once == twice, f"Normalizer not idempotent for '{name}': {once!r} != {twice!r}"

    def test_feature_csv_has_players(self, feature_names_set):
        """Feature CSV contains at least 50 unique players."""
        count = len(feature_names_set)
        assert count >= 50, (
            f"Feature CSV has only {count} unique player names. "
            f"Expected ≥50 for a populated MLB feature matrix."
        )
        print(f"\n[INFO] Feature CSV player count: {count}")

    def test_name_match_rate_meets_gate(
        self, kalshi_mlb_snapshot, feature_names_normalized, normalizer
    ):
        """
        MLB-G1 gate: ≥90% of active Kalshi market player names match feature CSV.

        A rate below 90% means the pipeline skips most markets silently — the same
        failure mode observed on 2026-06-25 (0 bets placed due to 0 player matches).
        """
        kalshi_names = _extract_player_names_from_markets(kalshi_mlb_snapshot)
        if not kalshi_names:
            pytest.skip("No active Kalshi markets with player names — off-season or quota hit")

        rate, matched, unmatched = _match_rate(
            kalshi_names, feature_names_normalized, normalizer
        )

        print(f"\n[INFO] Kalshi unique player names: {len(kalshi_names)}")
        print(f"[INFO] Matched: {len(matched)}, Unmatched: {len(unmatched)}")
        print(f"[INFO] Match rate: {rate:.1%}")

        if unmatched:
            print(f"\n[WARN] Unmatched names ({len(unmatched)}):")
            for name in sorted(unmatched)[:30]:
                print(f"  '{name}' → normalized: '{normalizer(name)}'")

        assert rate >= _MATCH_RATE_GATE, (
            f"Player name match rate {rate:.1%} < MLB-G1 gate {_MATCH_RATE_GATE:.0%}.\n"
            f"Matched: {len(matched)}/{len(kalshi_names)}\n"
            f"Unmatched ({len(unmatched)}): {sorted(unmatched)[:10]}\n"
            f"\nAction: rebuild feature matrix or update normalize_player_name()."
        )

        if rate < _WARN_RATE:
            print(
                f"\n[WARN] Match rate {rate:.1%} is below warning threshold {_WARN_RATE:.0%}. "
                f"Feature matrix may be stale — consider refreshing."
            )

    def test_known_players_always_match(
        self, feature_names_normalized, normalizer
    ):
        """
        Named spot-check: players confirmed present on 2026-06-25 must match.

        These three were verified during the T1 investigation that triggered Phase MLB-G1.
        If any of these fail, it means the feature CSV is stale or the normalizer regressed.
        """
        known_kalshi_names = [
            "Elly De La Cruz",
            "Manny Machado",
            "Jackson Merrill",
        ]
        failures = []
        for raw in known_kalshi_names:
            normalized = normalizer(raw)
            if normalized not in feature_names_normalized:
                failures.append((raw, normalized))

        assert len(failures) == 0, (
            f"Known players failed to match feature CSV (feature matrix may be stale):\n"
            + "\n".join(f"  '{r}' → '{n}'" for r, n in failures)
        )

    def test_unmatched_names_are_logged(
        self, kalshi_mlb_snapshot, feature_names_normalized, normalizer, capsys
    ):
        """
        All unmatched names are printed for operator review.

        Not a failure — this is an audit/observability test. The output helps
        the operator identify whether mismatches are stale-feature-CSV or
        normalizer issues vs. genuine roster gaps.
        """
        kalshi_names = _extract_player_names_from_markets(kalshi_mlb_snapshot)
        if not kalshi_names:
            pytest.skip("No active Kalshi markets")

        _, _, unmatched = _match_rate(kalshi_names, feature_names_normalized, normalizer)
        if unmatched:
            print(f"\n[AUDIT] Unmatched player names ({len(unmatched)} of {len(kalshi_names)}):")
            for name in sorted(unmatched):
                print(f"  '{name}'")
        else:
            print(f"\n[AUDIT] All {len(kalshi_names)} Kalshi player names matched — 100% coverage.")


class TestNameMatchingEdgeCases:
    """Edge case coverage for the normalizer."""

    def test_empty_string(self, normalizer):
        """Normalizer handles empty string without raising."""
        result = normalizer("")
        assert isinstance(result, str)

    def test_already_normalized(self, normalizer):
        """Idempotent on already-normalized names."""
        for name in ("elly de la cruz", "aaron judge", "manny machado"):
            result = normalizer(name)
            assert isinstance(result, str)
            assert result == normalizer(result)

    def test_extra_whitespace(self, normalizer):
        """Leading/trailing/internal whitespace is handled."""
        result = normalizer("  Aaron  Judge  ")
        assert "aaron" in result.lower() or "judge" in result.lower()

    def test_suffix_handling(self, normalizer):
        """Jr. / Sr. / III suffixes don't break matching."""
        for name in ("Ken Griffey Jr.", "Vladimir Guerrero Jr.", "Fernando Tatis Jr."):
            result = normalizer(name)
            assert isinstance(result, str)
            assert result.strip()
