"""T-588 / GG-317: evidence-class predicate. Fails closed; unwired."""
import pytest

from prediction_market_bot import logic_epoch as le

REAL = "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"
STUB = "STUB (StubNFLForecastModel — NOT a trained model, GG-255)"


def row(identity="<absent>", epoch=le.CURRENT_LOGIC_EPOCH):
    r = {"logic_epoch": epoch}
    if identity != "<absent>":
        r["model_identity"] = identity
    return r


def test_a_stub_with_valid_epoch_is_not_countable():
    r = row(STUB)
    assert le.is_clean_for_band(r["logic_epoch"], "T1")  # the GG-317 mechanism
    assert le.is_countable_evidence(r, "T1") is False


@pytest.mark.parametrize("identity", ["<absent>", None, "", "  ", "UNKNOWN", "unknown", 7])
def test_b_unattributed_is_not_countable(identity):
    assert le.is_countable_evidence(row(identity), "T1") is False
    assert le.evidence_class(row(identity)) == le.EVIDENCE_UNATTRIBUTED


def test_c_model_evidence_with_pre_floor_epoch_is_not_countable():
    floor = le.clean_epoch_floor_for_band("T4M-PROJ")
    assert le.is_countable_evidence(row(REAL, floor - 1), "T4M-PROJ") is False


def test_model_evidence_at_floor_is_countable():
    floor = le.clean_epoch_floor_for_band("T4M-PROJ")
    assert le.is_countable_evidence(row(REAL, floor), "T4M-PROJ") is True


def test_unregistered_non_stub_identity_fails_closed():
    assert le.evidence_class(row("SomeNewModel v1")) == le.EVIDENCE_UNATTRIBUTED
    assert le.is_countable_evidence(row("SomeNewModel v1"), "T1") is False


@pytest.mark.parametrize("bad", [None, [], "x", 3])
def test_non_dict_rows_fail_closed(bad):
    assert le.is_countable_evidence(bad, "T1") is False


@pytest.mark.parametrize("epoch", [None, "12", True, 12.0])
def test_bad_epoch_fails_closed(epoch):
    assert le.is_countable_evidence(row(REAL, epoch), "T1") is False


def test_untagged_requires_current_epoch():
    assert le.is_countable_evidence(row(REAL, le.CURRENT_LOGIC_EPOCH), "UNTAGGED") is True
    assert le.is_countable_evidence(row(REAL, le.CURRENT_LOGIC_EPOCH - 1), "UNTAGGED") is False


def test_existing_predicate_unchanged():
    assert le.is_clean_for_band(None, "T1") is False
    assert le.is_clean_for_band(le.clean_epoch_floor_for_band("T1"), "T1") is True
