"""
Phase MLB-G1 — Integration Test 3: Pipeline Smoke Test

End-to-end dry run of the MLB T1 pipeline path WITHOUT placing any bets.

Exercises: feature CSV load → player cohort build → Kalshi market fetch →
player name matching → market date filtering → feature vector assembly →
model score generation → C4 risk check (sizing only, no execute).

This is the smoke test that confirms every stage of the pipeline is wired up
correctly under real data conditions. Any failure here must be resolved before
MLB crons re-enable.

Run: pytest tests/integration/test_mlb_pipeline_smoke.py -v -m integration
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.integration

_PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

# ---------------------------------------------------------------------------
# Feature CSV smoke checks
# ---------------------------------------------------------------------------

class TestFeatureCSVIntegrity:
    """Feature matrix structure and freshness checks."""

    def test_feature_csv_loads(self, feature_df):
        """Feature CSV loads without error and has rows."""
        assert len(feature_df) > 0, "Feature CSV is empty"
        print(f"\n[INFO] Feature CSV: {len(feature_df)} player rows")

    def test_required_columns_present(self, feature_df):
        """Feature CSV contains the minimum columns required by T1."""
        required = [
            "player_id",
            "player_name",
            "game_date",
        ]
        missing = [c for c in required if c not in feature_df.columns]
        assert len(missing) == 0, (
            f"Feature CSV missing required columns: {missing}\n"
            f"Present columns: {sorted(feature_df.columns.tolist())}"
        )

    def test_player_id_is_populated(self, feature_df):
        """player_id is non-null for all rows."""
        null_count = feature_df["player_id"].isna().sum()
        assert null_count == 0, f"{null_count} rows have null player_id"

    def test_game_date_is_parseable(self, feature_df):
        """game_date parses as a date without NaTs."""
        import pandas as pd
        dates = pd.to_datetime(feature_df["game_date"], errors="coerce")
        nat_count = dates.isna().sum()
        assert nat_count == 0, f"{nat_count} game_date values failed to parse as dates"

    def test_feature_csv_freshness(self, feature_df):
        """
        MLB-G1 gate: feature CSV must not be stale.

        Freshness rules (ADR-TBD, MLB-G1 pending):
        - WARNING if max game_date > 3 days old
        - FAIL (gate) if max game_date > 7 days old

        A stale feature CSV produces silent model errors: the model runs but
        uses historical stats that no longer reflect current player form.

        Environment-aware (GG-179, T-449): the feature_df fixture already
        skips this test wherever the CSV artifact is absent (every CI run
        today — CI never generates/restores it). That leaves a second case
        unhandled: a CSV that IS present but is just whatever a contributor
        happens to have lying around locally, not the live/VPS-synced
        artifact this gate is meant to police. Hard-failing on that copy's
        age conflates "my laptop's scratch CSV is old" with "the pipeline's
        real feature matrix is stale" — the latter is the actual MLB-G1
        concern. The hard FAIL therefore only fires when
        MLB_G1_STRICT_FRESHNESS=1 is set — set it in whichever environment is
        expected to hold the live-synced artifact. Everywhere else, staleness
        is reported via an explicit skip (not a silent pass) so it stays
        visible without blocking unrelated local work.
        """
        today = datetime.now(tz=timezone.utc).date()
        max_date = feature_df["game_date_dt"].max().date()
        days_stale = (today - max_date).days
        print(f"\n[INFO] Feature CSV latest game_date: {max_date} ({days_stale} days ago)")

        if days_stale > 7:
            msg = (
                f"Feature CSV is {days_stale} days stale (max game_date: {max_date}). "
                f"MLB-G1 gate: must be ≤7 days. Run scripts/generate_mlb_features.py."
            )
            if os.environ.get("MLB_G1_STRICT_FRESHNESS") == "1":
                pytest.fail(msg)
            pytest.skip(
                f"{msg} Not enforced in this environment — set "
                f"MLB_G1_STRICT_FRESHNESS=1 to enforce against the "
                f"live/VPS-synced artifact (GG-179)."
            )
        if days_stale > 3:
            print(
                f"\n[WARN] Feature CSV is {days_stale} days stale. "
                f"WARNING threshold: >3 days. Refresh recommended."
            )

    def test_no_all_null_feature_rows(self, feature_df):
        """No player row is entirely null across numeric columns."""
        numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            pytest.skip("No numeric columns found in feature CSV")
        all_null = feature_df[numeric_cols].isna().all(axis=1).sum()
        assert all_null == 0, (
            f"{all_null} player rows have all-null numeric feature values. "
            f"These produce NaN model scores and will be skipped silently."
        )


# ---------------------------------------------------------------------------
# Model artifact smoke checks
# ---------------------------------------------------------------------------

class TestModelArtifact:
    """Model artifact structure checks."""

    @pytest.fixture(scope="class")
    def model_artifact(self, project_root):
        import joblib
        model_path = project_root / "models" / "mlb_model.pkl"
        if not model_path.exists():
            # Try alternate path
            alt = project_root / "exp_output" / "MLB" / "mlb_model.pkl"
            if alt.exists():
                model_path = alt
            else:
                pytest.skip(f"MLB model artifact not found at {model_path} or {alt}")
        return joblib.load(model_path)

    def test_artifact_has_required_keys(self, model_artifact):
        """Model artifact has all keys required by run_mlb_paper_trade.py."""
        required = ["pipelines", "feature_names", "col_medians", "model_version"]
        missing = [k for k in required if k not in model_artifact]
        assert len(missing) == 0, f"Model artifact missing keys: {missing}"

    def test_sport_label_is_mlb(self, model_artifact):
        """Model artifact sport label is 'mlb'."""
        sport = model_artifact.get("sport", "unknown")
        assert sport.lower() == "mlb", (
            f"Model artifact sport='{sport}'. Expected 'mlb'. "
            f"Wrong model file loaded?"
        )

    def test_feature_names_match_csv(self, model_artifact, feature_df):
        """Model feature names are present as columns in the feature CSV (≥80%)."""
        model_features = model_artifact["feature_names"]
        csv_cols = set(feature_df.columns.tolist())
        missing = [f for f in model_features if f not in csv_cols]
        coverage = 1.0 - len(missing) / len(model_features) if model_features else 0.0
        print(f"\n[INFO] Model features: {len(model_features)} | CSV match: {coverage:.1%}")
        if missing:
            print(f"[WARN] Model features not in CSV: {missing[:10]}")
        assert coverage >= 0.80, (
            f"Only {coverage:.1%} of model features are present in feature CSV. "
            f"Missing: {missing[:10]}"
        )

    def test_thresholds_exist(self, model_artifact):
        """Model artifact has thresholds list (used to scope market fetch)."""
        thresholds = model_artifact.get("thresholds", [])
        assert isinstance(thresholds, list), "'thresholds' is not a list"
        assert len(thresholds) > 0, "Model artifact has empty 'thresholds' list"
        assert 1 in thresholds, "Threshold 1 (≥1 hit) missing from model artifact"


# ---------------------------------------------------------------------------
# Full pipeline dry-run
# ---------------------------------------------------------------------------

class TestPipelineDryRun:
    """
    Full pipeline dry-run: feature load → market fetch → name match → scoring.
    No bets placed. No money touched.
    """

    def test_cohort_builds_from_feature_csv(self, feature_df):
        """Player cohort (norm_name → latest row) builds without error."""
        from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
        cohort_lookup = {}
        for _, row in feature_df.iterrows():
            norm = normalize_player_name(str(row.get("player_name", "")))
            if norm:
                cohort_lookup[norm] = row
        assert len(cohort_lookup) > 0, "Cohort lookup is empty — feature CSV has no player names"
        print(f"\n[INFO] Cohort lookup built: {len(cohort_lookup)} players")

    def test_market_date_filter_runs(self, kalshi_mlb_snapshot):
        """Date filter (ticker → game_date) runs without regex errors."""
        import re
        pattern = re.compile(r"-([0-9]{2})([A-Z]{3})([0-9]{2})[0-9]{4}")
        today = datetime.now(tz=timezone.utc).date().isoformat()
        active_quoted = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.has_live_quotes
        ]
        today_markets = []
        bad_tickers = []
        for m in active_quoted:
            match = pattern.search(m.ticker)
            if not match:
                bad_tickers.append(m.ticker)
                continue
            try:
                game_date = datetime.strptime(
                    match.group(1) + match.group(2) + match.group(3), "%d%b%y"
                ).date().isoformat()
                if game_date == today:
                    today_markets.append(m)
            except ValueError:
                bad_tickers.append(m.ticker)

        assert len(bad_tickers) == 0, (
            f"{len(bad_tickers)} market tickers failed date parse: {bad_tickers[:5]}"
        )
        print(
            f"\n[INFO] Active/quoted markets: {len(active_quoted)} | "
            f"Today ({today}): {len(today_markets)} | Filtered out: {len(active_quoted) - len(today_markets)}"
        )
        if len(today_markets) == 0:
            print(
                f"[INFO] Zero today-dated markets — correct behavior if MLB games haven't "
                f"been published yet or it's MLB off-season."
            )

    def test_player_cohort_market_overlap(self, kalshi_mlb_snapshot, feature_df):
        """At least one active market player is in the feature cohort."""
        from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
        cohort = {
            normalize_player_name(str(row.get("player_name", "")))
            for _, row in feature_df.iterrows()
        }
        active = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.player_name
        ]
        if not active:
            pytest.skip("No active markets — off-season")

        matched = [m for m in active if normalize_player_name(m.player_name) in cohort]
        match_count = len(matched)
        total = len(active)
        rate = match_count / total if total > 0 else 0.0
        print(
            f"\n[INFO] Active market/cohort overlap: {match_count}/{total} ({rate:.1%})"
        )
        assert match_count > 0, (
            f"Zero overlap between {total} active market players and {len(cohort)} cohort players. "
            f"Feature CSV is likely stale or player name normalization is broken."
        )

    def test_feature_vector_assembles_for_matched_player(self, kalshi_mlb_snapshot, feature_df):
        """
        For the first matched (market, player) pair, _build_mlb_feature_vector()
        assembles without crashing and returns a non-empty array.

        If this fails, the model cannot score any player regardless of market availability.
        """
        from prediction_market_bot.c5_execution.market_mapper import normalize_player_name

        cohort_lookup = {}
        for _, row in feature_df.iterrows():
            norm = normalize_player_name(str(row.get("player_name", "")))
            if norm:
                cohort_lookup[norm] = row

        active = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.player_name
        ]
        if not active:
            pytest.skip("No active markets")

        matched_pair = None
        for m in active:
            norm = normalize_player_name(m.player_name)
            if norm in cohort_lookup:
                matched_pair = (m, cohort_lookup[norm])
                break

        if matched_pair is None:
            pytest.skip("No matched market/player pair — feature CSV may be stale")

        market, row = matched_pair

        # Load model for feature names
        import joblib
        model_path = _PROJECT_ROOT / "models" / "mlb_model.pkl"
        if not model_path.exists():
            alt = _PROJECT_ROOT / "exp_output" / "MLB" / "mlb_model.pkl"
            if alt.exists():
                model_path = alt
            else:
                pytest.skip("Model artifact not found — cannot test feature vector assembly")

        artifact = joblib.load(model_path)
        feature_names = artifact["feature_names"]
        col_medians = artifact["col_medians"]

        from prediction_market_bot.run_mlb_paper_trade import _build_mlb_feature_vector, _impute

        threshold = getattr(market, "threshold", 1)
        try:
            threshold = int(threshold)
        except (TypeError, ValueError):
            threshold = 1

        fv = _build_mlb_feature_vector(row, feature_names, threshold)
        assert fv is not None, "Feature vector assembly returned None"
        assert len(fv) == len(feature_names), (
            f"Feature vector length mismatch: got {len(fv)}, expected {len(feature_names)}"
        )
        fv_imputed = _impute(fv.reshape(1, -1), col_medians)
        assert not np.all(np.isnan(fv_imputed)), (
            "Feature vector is all-NaN after imputation — model will produce garbage scores"
        )
        nan_frac = np.isnan(fv_imputed).mean()
        print(
            f"\n[INFO] Feature vector for '{market.player_name}' (threshold={threshold}): "
            f"{len(feature_names)} features, {nan_frac:.1%} NaN after imputation"
        )
        if nan_frac > 0.30:
            print(
                f"[WARN] {nan_frac:.1%} of features are NaN after imputation. "
                f"Feature CSV may be stale or feature engineering incomplete."
            )

    def test_model_scores_without_crashing(self, kalshi_mlb_snapshot, feature_df):
        """
        Model.predict_proba() runs on a real feature vector without exception.

        A crash here means the model artifact is corrupted, the feature pipeline
        is broken, or the model/CSV mismatch is severe enough to error.
        """
        import joblib
        model_path = _PROJECT_ROOT / "models" / "mlb_model.pkl"
        if not model_path.exists():
            alt = _PROJECT_ROOT / "exp_output" / "MLB" / "mlb_model.pkl"
            if alt.exists():
                model_path = alt
            else:
                pytest.skip("Model artifact not found")

        artifact = joblib.load(model_path)
        feature_names = artifact["feature_names"]
        col_medians = artifact["col_medians"]
        pipelines = artifact["pipelines"]

        from prediction_market_bot.c5_execution.market_mapper import normalize_player_name
        from prediction_market_bot.run_mlb_paper_trade import _build_mlb_feature_vector, _impute

        cohort_lookup = {}
        for _, row in feature_df.iterrows():
            norm = normalize_player_name(str(row.get("player_name", "")))
            if norm:
                cohort_lookup[norm] = row

        active = [
            m for m in kalshi_mlb_snapshot.markets
            if m.status == "active" and m.player_name
        ]
        if not active:
            pytest.skip("No active markets")

        matched = [(m, cohort_lookup[normalize_player_name(m.player_name)])
                   for m in active
                   if normalize_player_name(m.player_name) in cohort_lookup]
        if not matched:
            pytest.skip("No matched market/player pairs")

        market, row = matched[0]
        threshold = int(market.threshold) if market.threshold else 1

        fv = _build_mlb_feature_vector(row, feature_names, threshold)
        fv_imputed = _impute(fv.reshape(1, -1), col_medians)

        scored_count = 0
        errors = []
        for t, pipeline in pipelines.items():
            try:
                proba = pipeline.predict_proba(fv_imputed)[0][1]
                assert 0.0 <= proba <= 1.0, f"Pipeline {t} returned out-of-range probability {proba}"
                scored_count += 1
                print(f"\n[INFO] Pipeline t={t}: p={proba:.4f} for '{market.player_name}' (threshold={threshold})")
            except Exception as e:
                errors.append(f"t={t}: {type(e).__name__}: {e}")

        if errors:
            pytest.fail(
                f"Model pipeline(s) crashed during scoring:\n"
                + "\n".join(f"  {e}" for e in errors)
            )
        assert scored_count > 0, "No pipelines produced a score"

    def test_c4_risk_engine_approves_or_rejects_cleanly(self, feature_df):
        """
        C4 RiskEngine.evaluate_forecast() runs on a synthetic forecast without
        raising exceptions. Tests that C4 is wired up correctly for MLB bets.

        Uses a dummy market value — no real money involved.
        """
        from prediction_market_bot.c4_risk_engine.risk import RiskEngine
        from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
        import io

        # Null logger to /dev/null
        logger = AuditLogger(
            Path("/dev/null"),
            min_severity="CRITICAL",  # suppress output
        )

        engine = RiskEngine(
            logger=logger,
            snapshot_id="TEST",
            bankroll=1000.0,
            kelly_fraction=0.10,
            initial_bankroll=1000.0,
            min_bet_usd=1.0,
        )

        # Synthetic forecast_record matching the IF-C3-C4 interface
        forecast_record = {
            "p_estimate": 0.70,
            "market_implied_prob": 0.55,
            "edge": 0.70 - 0.55,
            "recommended_direction": "YES",
            "ticker": "KXMLBHIT-26JUN261840CINPIT-CINEDELACRUZ44-1",
            "player_name": "Elly De La Cruz",
            "threshold": 1,
            "sport": "mlb",
            "forecast_id": "smoke-test-001",
        }

        ok_c4, approval = engine.evaluate_forecast(
            forecast_record=forecast_record,
            current_daily_loss=0.0,
            current_drawdown_pct=0.0,
            session_id="TEST",
            current_open_exposure_usd=0.0,
            portfolio_equity_usd=1000.0,
        )

        # Either APPROVED or REJECTED is correct. Crash is not.
        assert isinstance(ok_c4, bool), f"evaluate_forecast returned non-bool ok: {ok_c4}"
        assert isinstance(approval, dict), f"evaluate_forecast returned non-dict approval: {approval}"
        assert "approval_status" in approval, f"'approval_status' missing from C4 result: {approval}"
        print(f"\n[INFO] C4 result for synthetic MLB bet: ok={ok_c4}, status={approval.get('approval_status')}")
