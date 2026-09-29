"""T-583 tests. SYNTHETIC cohorts (year 2027 tickers, seeded RNG, known ground truth) exercise
the machinery only — they say nothing about ADR-0065's candidate or any real enhancer."""
import copy
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ab_harness_t4 as H  # noqa: E402

MON = ["APR", "MAY"]


def synth(n_games=160, rows_per_game=8, seed=5, late_bias=0.12):
    """Truth p_true per row. Incumbent is biased by +late_bias on 'late' rows (state.late=True);
    a candidate that removes the bias is truly better; outcome ~ Bernoulli(p_true)."""
    rng = random.Random(seed)
    rows = []
    for g in range(n_games):
        m, day = MON[g // 80], g % 28 + 1
        gid = f"G{g}"
        for k in range(rows_per_game):
            p_true = rng.uniform(0.2, 0.7)
            late = k >= rows_per_game // 2
            rows.append(dict(
                ticker=f"KXMLBHIT-27{m}{day:02d}1840AAABBB-BBBPLAYER{g}-{k}", game_id=gid,
                game_date=f"2027-{4 if m == 'APR' else 5:02d}-{day:02d}",
                p_incumbent=min(0.99, p_true + (late_bias if late else 0.0)),
                outcome=int(rng.random() < p_true), resolution_source="synthetic_ground_truth",
                cohort_band="SYNTH", logic_epoch=0, late=late, p_true=p_true))
    return rows


def fixing(train):
    return lambda r: r["p_true"]              # oracle candidate: removes the bias


def noop(train):
    return lambda r: r["p_incumbent"]


def worse(train):
    return lambda r: min(0.99, r["p_incumbent"] + (0.15 if r["late"] else 0.0))


KW = dict(cutoff="2027-05-01", hypothesis="synthetic: removing late bias improves Brier",
          synthetic=True, n_boot=800)


def test_e2e_synthetic_improvement_detected():
    out = H.run_gate(synth(), fixing, **KW)
    assert out["verdict"] == "DEFENSIBLE_IMPROVEMENT"
    assert out["synthetic"] and not out["gate_eligible"]
    assert out["brier_gain"]["ci_low"] > 0 and out["n_differing_test_games"] >= 30


def test_e2e_synthetic_harm_detected():
    assert H.run_gate(synth(), worse, **KW)["verdict"] == "HARMFUL"


def test_refuses_no_difference_cohort():           # refusal 1: candidate == incumbent everywhere
    with pytest.raises(H.InadequateCohortError, match="differs from incumbent"):
        H.run_gate(synth(), noop, **KW)


def test_refuses_too_few_games():                  # refusal 2
    with pytest.raises(H.InadequateCohortError, match="games"):
        H.run_gate(synth(n_games=40), fixing, **KW)


def test_refuses_missing_state_field():            # refusal 3: ADR-0065 fields absent
    with pytest.raises(H.MissingFieldError, match="inning_half"):
        H.run_gate(synth(), fixing, required_state_fields=H.WALKOFF_STATE_FIELDS, **KW)


def test_refuses_ledger_outcomes():                # refusal 4
    rows = synth(); rows[3]["resolution_source"] = "paper_ledger"
    with pytest.raises(H.UnresolvedOutcomeError):
        H.run_gate(rows, fixing, **KW)


def test_refuses_unresolved_outcome():
    rows = synth(); rows[0]["outcome"] = 0.5          # not a resolved binary
    with pytest.raises(H.UnresolvedOutcomeError):
        H.run_gate(rows, fixing, **KW)
    rows[0]["outcome"] = None                          # unresolved/absent
    with pytest.raises(H.MissingFieldError):
        H.run_gate(rows, fixing, **KW)


def test_refuses_stored_date_disagreeing_with_ticker():   # GG-164
    rows = synth(); rows[7]["game_date"] = "2027-05-09" if rows[7]["game_date"] != "2027-05-09" else "2027-05-10"
    with pytest.raises(H.DateIntegrityError):
        H.run_gate(rows, fixing, **KW)


def test_refuses_empty_hypothesis():
    with pytest.raises(H.PreRegistrationError):
        H.run_gate(synth(), fixing, **{**KW, "hypothesis": "  "})


def test_refuses_t4mproj_epoch12_by_label():
    rows = synth()
    for r in rows: r["cohort_band"], r["logic_epoch"] = "T4M-PROJ", 12
    with pytest.raises(H.ForbiddenCohortError, match="T-577"):
        H.run_gate(rows, fixing, **KW)


def test_refuses_t4mproj_cohort_by_manifest_even_if_relabelled():
    rows = synth()
    t = sorted(H._forbidden_tickers())[0]                 # real 765/905-cohort ticker, band label scrubbed
    rows[0]["ticker"] = t
    with pytest.raises(H.ForbiddenCohortError, match="manifest"):
        H.run_gate(rows, fixing, **KW)


def test_manifest_covers_full_forbidden_ledger():
    import json
    d = json.load(open(Path(__file__).resolve().parent.parent /
                       "exp_output/T577_cohort_salvage/paper_portfolio_mlb_t4.LIVE.20260922.json"))
    ledger = {r["kalshi_ticker"] for k in ("open_positions", "closed_positions", "rejected_positions")
              for r in d[k] if r.get("band") == "T4M-PROJ" and r.get("logic_epoch") == 12}
    assert ledger == set(H._forbidden_tickers()) and len(ledger) == 879


def test_bootstrap_primitive_is_game_clustered_not_iid():
    # clustering must widen the CI vs treating every row as its own cluster
    vals = [(-1) ** g * 0.1 for g in range(60) for _ in range(10)]
    keys = [f"G{g}" for g in range(60) for _ in range(10)]
    c = H._block_bootstrap_mean_ci(vals, keys, n_boot=800, seed=1)
    i = H._block_bootstrap_mean_ci(vals, [str(x) for x in range(600)], n_boot=800, seed=1)
    assert (c["ci_high"] - c["ci_low"]) > 3 * (i["ci_high"] - i["ci_low"])
