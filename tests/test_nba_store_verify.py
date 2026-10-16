import json

from prediction_market_bot.c1_signal_ingestion import nba_store_verify as v


def _mk(tmp_path):
    root = tmp_path / "store"
    (root / "raw" / "pbp").mkdir(parents=True)
    (root / "raw" / "pbp" / "a.parquet").write_bytes(b"alpha")
    man = tmp_path / "m.json"
    man.write_text(json.dumps({"build_as_of": "t", "files": [{"store_file": "raw/pbp/a.parquet"}]}))
    return root, man, tmp_path / "s.json"


def test_roundtrip_ok(tmp_path):
    root, man, side = _mk(tmp_path)
    v.write_sidecar(root, man, side)
    assert v.verify(root, side) == []


def test_detects_corruption_missing_and_size(tmp_path):
    root, man, side = _mk(tmp_path)
    v.write_sidecar(root, man, side)
    f = root / "raw" / "pbp" / "a.parquet"
    f.write_bytes(b"alphX")
    assert v.verify(root, side)[0].startswith("SHA")
    f.write_bytes(b"alpha-longer")
    assert v.verify(root, side)[0].startswith("SIZE")
    f.unlink()
    assert v.verify(root, side)[0].startswith("MISSING")
