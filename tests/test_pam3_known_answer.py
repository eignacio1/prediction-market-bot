"""Known-answer test for H-DEPTH-PAM-3 (run_pam3.py): planted rates and reliability are recovered; the shrinkage challenger beats the
raw mean on a simulated league with noisy rates; a zero-noise league shows no gain. Runs on simulated box rows only."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

_P = Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "pam_stability" / "run_pam3.py"
_spec = importlib.util.spec_from_file_location("run_pam3", _P)
r3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r3)

PLANT = {"points": (0.45, 150.0), "rebounds": (0.18, 200.0), "assists": (0.12, 250.0), "threes": (0.08, 300.0)}  # (mean rate, k min)


def simulate(seasons, seed=7, teams=10, per=12, noisy=True):
    rng = np.random.default_rng(seed)
    n = teams * per
    pid = np.arange(n) + 1000
    team = np.repeat(np.arange(teams), per) + 1
    mpg = rng.integers(16, 35, n).astype(float)
    rate = {}
    for s, (mu, k) in PLANT.items():
        a = k * mu
        rate[s] = rng.gamma(a, mu / a, n) if noisy else rng.integers(1, 6, n) * mu
    for s, mu in (("blocks", 0.03), ("steals", 0.04)):
        rate[s] = rng.gamma(20, mu / 20, n) if noisy else rng.integers(1, 5, n) * mu
    ftp = rng.beta(40, 14, n) if noisy else rng.integers(6, 10, n) / 10.0
    rows = []
    for season in seasons:
        for d in range(82):
            order = rng.permutation(teams) + 1
            for gnum in range(teams // 2):
                gid = f"{season}{d:03d}{gnum}"
                date = f"{season}-{1 + d // 28:02d}-{1 + d % 28:02d}"
                for t in order[2 * gnum:2 * gnum + 2]:
                    for i in np.where(team == t)[0]:
                        m = float(np.clip(rng.normal(mpg[i], 3), 5, 44)) if noisy else mpg[i]
                        r = dict(season=season, game_id=gid, date=date, person_id=int(pid[i]), team_id=int(t), min=m)
                        for s in list(PLANT) + ["blocks", "steals"]:
                            r[s] = float(rng.poisson(rate[s][i] * m)) if noisy else float(round(rate[s][i] * m))
                        fta = float(rng.poisson(4)) if noisy else 4.0
                        r["fta"] = fta
                        r["ftm"] = float(rng.binomial(int(fta), ftp[i])) if noisy else float(round(fta * ftp[i]))
                        rows.append(r)
    return pd.DataFrame(rows)


def test_planted_reliability_recovered():
    box = simulate([2016, 2017, 2018, 2019])
    for s, (mu, k) in PLANT.items():
        got = r3.reliability(box, [2016, 2017, 2018, 2019], s, boot=20)
        assert abs(got["k"] - k) / k < 0.40, (s, got["k"], k)


def test_challenger_beats_raw_mean_and_identity():
    box = simulate([2016, 2017, 2018, 2019, 2020, 2021])
    res = r3.run_pipeline(box, [2016, 2017, 2018, 2019], [2020, 2021], b=200, reliab_boot=20)
    assert res["identity_max_abs_diff"] < 1e-9
    assert res["pooled"]["challenger"]["D"] > 0
    assert res["n_stats_positive"] >= 3
    assert res["verdict"] == "SUPPORTED"
    assert res["by_stratum"]["challenger"]["4-10"]["D"] > res["by_stratum"]["challenger"]["31+"]["D"]


def test_zero_noise_shows_no_gain():
    box = simulate([2016, 2017, 2018, 2019, 2020], noisy=False)
    res = r3.run_pipeline(box, [2016, 2017, 2018], [2019, 2020], b=100, reliab_boot=10)
    assert abs(res["pooled"]["challenger"]["D"]) < 0.01
    assert res["verdict"] != "SUPPORTED"


def test_judged_seasons_refused_without_final(tmp_path):
    import pytest
    r3.load_box.allow_judged = False
    with pytest.raises(PermissionError):
        r3.load_box(tmp_path, [2023])
