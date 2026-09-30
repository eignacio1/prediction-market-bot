"""T-592: allowlist loader validation and overlay semantics (compute-only)."""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import provenance_allowlist_recompute as pa  # noqa: E402

from prediction_market_bot.logic_epoch import is_countable_evidence  # noqa: E402

ALLOWLIST = Path(__file__).resolve().parents[1] / "05_RESEARCH_EXPERIMENTS/provenance/t4m_proj_provenance_allowlist.json"


def _w(**kw):
    w = {"window_id": "W1", "band": "T4M-PROJ", "market_type": "mlb_player_prop_hits",
         "session_id": "S", "window_start_utc": "2026-08-01T00:00:00Z",
         "window_end_utc": "2026-08-02T00:00:00Z", "commit_sha": "a" * 40,
         "model_identity_asserted": "X",
         "citation": {k: "c" for k in pa.CITATION_KEYS}}
    w.update(kw)
    return w


def _dump(tmp_path, wins):
    p = tmp_path / "a.json"
    p.write_text(json.dumps({"windows": wins}))
    return p


def _row(**kw):
    r = {"band": "T4M-PROJ", "logic_epoch": 12, "entered_at": "2026-08-01T12:00:00.000Z",
         "model_identity": "UNKNOWN"}
    r.update(kw)
    return r


def test_shipped_allowlist_valid():
    wins = pa.load_allowlist(ALLOWLIST)
    assert len(wins) == 13 and all(w["citation"] for w in wins)


def test_uncited_entry_refused(tmp_path):
    w = _w()
    w["citation"]["commit"] = " "
    with pytest.raises(ValueError):
        pa.load_allowlist(_dump(tmp_path, [w]))
    w2 = _w()
    del w2["citation"]
    with pytest.raises(ValueError):
        pa.load_allowlist(_dump(tmp_path, [w2]))


def test_short_sha_and_overlap_refused(tmp_path):
    with pytest.raises(ValueError):
        pa.load_allowlist(_dump(tmp_path, [_w(commit_sha="abc1234")]))
    with pytest.raises(ValueError):
        pa.load_allowlist(_dump(tmp_path, [_w(), _w(window_id="W2")]))


def test_overlay_admits_only_unattributed_inside_window():
    wins = [_w()]
    assert pa.countable_with_allowlist(_row(), "T4M-PROJ", wins)
    assert not pa.countable_with_allowlist(_row(entered_at="2026-08-03T00:00:00Z"), "T4M-PROJ", wins)
    assert not pa.countable_with_allowlist(_row(model_identity="STUB v1"), "T4M-PROJ", wins)
    assert not pa.countable_with_allowlist(_row(model_identity="Other model"), "T4M-PROJ", wins)
    assert not pa.countable_with_allowlist(_row(), "T4M-ARITH", wins)
    assert pa.countable_with_allowlist(_row(model_identity=None), "T4M-PROJ", wins)


def test_overlay_never_admits_unclean_epoch():
    assert not pa.countable_with_allowlist(_row(logic_epoch=3), "T4M-PROJ", [_w()])


def test_predicate_unchanged_and_row_not_mutated():
    row = _row()
    before = copy.deepcopy(row)
    pa.countable_with_allowlist(row, "T4M-PROJ", [_w()])
    assert row == before
    assert is_countable_evidence(row, "T4M-PROJ") is False
