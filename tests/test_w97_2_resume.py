"""W97.2 known-answer test: the resumable per-series reproduction equals the hand-computed cell figures and is resumable."""
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY", "frozen_evidence_check"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "12_EXPLORATORY"))
import repro as R  # noqa: E402
import resume as M  # noqa: E402
import calib as C  # noqa: E402

from prediction_market_bot.quant.money import fee_k007  # noqa: E402


def _setup(tmp_path, monkeypatch, n=40):
    """n KXMLBHIT games 1h before first pitch (bid .20 / ask .22), every 4th YES; plus 5 KXMLBTOTAL noise rows."""
    arch, settle = tmp_path / "arch", tmp_path / "settle"
    arch.mkdir()
    settle.mkdir()
    rows, res = [], {}
    for i in range(n):
        ev = f"KXMLBHIT-26OCT201905T{i:02d}"
        tk = ev + "-P1"
        ts = C.game_start(ev)[0] - 3600
        iso = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat()
        rows.append({"series_ticker": "KXMLBHIT", "event_ticker": ev, "ticker": tk, "run_ts": iso,
                     "yes_bid": 0.20, "yes_ask": 0.22, "yes_mid": 0.21})
        res[tk] = {"result": "yes" if i % 4 == 0 else "no"}
    noise = [{"series_ticker": "KXMLBTOTAL", "event_ticker": "KXMLBTOTAL-26OCT201905T00", "ticker": f"KXMLBTOTAL-26OCT201905T00-{k}",
              "run_ts": rows[0]["run_ts"], "yes_bid": 0.5, "yes_ask": 0.52, "yes_mid": 0.51} for k in range(5)]
    (arch / "prices_2026-10-20.jsonl").write_text("\n".join(json.dumps(r) for r in rows + noise))
    json.dump(res, open(settle / "s.json", "w"))

    def under(p):
        d = tmp_path / "fence" / p
        d.mkdir(parents=True, exist_ok=True)
        return str(d)
    monkeypatch.setattr(R, "under_fence", under)
    monkeypatch.setattr(M, "safe_out", lambda p: pathlib.Path(p))
    return str(arch), str(settle)


def test_prefilter_splits_by_series_and_resumes(tmp_path, monkeypatch):
    arch, _ = _setup(tmp_path, monkeypatch)
    a = M.prefilter(arch)
    assert a["prefiltered_this_call"] == 1 and a["left"] == 0
    hit = (pathlib.Path(M._dir("pre", "KXMLBHIT")) / "prices_2026-10-20.jsonl").read_text().splitlines()
    tot = (pathlib.Path(M._dir("pre", "KXMLBTOTAL")) / "prices_2026-10-20.jsonl").read_text().splitlines()
    assert len(hit) == 40 and len(tot) == 5
    assert all(json.loads(l)["series_ticker"] == "KXMLBHIT" for l in hit)
    assert M.prefilter(arch)["prefiltered_this_call"] == 0  # unchanged source: skipped


def test_prefilter_redoes_a_source_that_grew(tmp_path, monkeypatch):
    arch, _ = _setup(tmp_path, monkeypatch)
    M.prefilter(arch)
    with open(os.path.join(arch, "prices_2026-10-20.jsonl"), "a") as fh:
        fh.write("\n" + json.dumps({"series_ticker": "KXMLBHIT", "event_ticker": "x", "ticker": "x-1"}))
    assert M.prefilter(arch)["prefiltered_this_call"] == 1


def test_resumed_cell_equals_hand_computation_and_budget_resumes(tmp_path, monkeypatch):
    arch, settle = _setup(tmp_path, monkeypatch)
    s1 = M.step(arch, settle, budget_s=0.0)  # zero budget: prefilter only (its own cap is min(budget, 400))
    s2 = M.step(arch, settle, budget_s=10_000)
    assert s2["remaining_units"] == 0
    res = M.combine_window(None)
    assert res["missing_units"] == []
    c = next(x for x in res["cells"] if x["id"].startswith("89.2 KXMLBHIT T0-2h 20-25c all"))
    # f = 10/40 = 0.25 > pbar 0.21 -> YES at the ask 0.22: net = 0.25 - 0.22 - fee
    assert c["n"] == 40 and abs(c["k007"]["net"] - (0.25 - 0.22 - fee_k007(0.22))) < 1e-12
    assert c["status"] == "DIFFERS"  # reported n is 1892; the synthetic archive has 40
    assert M.pending_units() == []


def test_wave_window_excludes_files_on_or_after_the_bound(tmp_path, monkeypatch):
    arch, settle = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(M, "WINDOWS", (None, "2026-10-20"))
    M.step(arch, settle, budget_s=10_000)
    res = M.combine_window("2026-10-20")  # exclusive bound: the only file is dated 10-20
    c = [x for x in res["cells"] if x["id"].startswith("89.2 KXMLBHIT T0-2h 20-25c all")][0]
    assert c["n"] == 0 and c["status"] == "NOT REPRODUCED"


def test_box_tasks_registered_and_read_only_on_the_archive():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    import box_tasks as B
    for t in ("frozen_resume_step", "frozen_resume_combine"):
        assert "resume.py" in B.TASKS[t] and "rm " not in B.TASKS[t]
