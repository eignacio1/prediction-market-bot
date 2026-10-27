"""Known-answer tests for the W89.4 game-state chain (estimator recovers a known chain; simulator conserves basics)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain as C  # noqa: E402

# three play states and their absorbing outcomes; probabilities are the planted truth
PLANT = {
    (1, 10, 75): dict(next={(2, 5, 60): 0.55}, term={"PUNT": 0.30, "TURN": 0.15}),
    (2, 5, 60): dict(next={(3, 5, 55): 0.5}, term={"FG": 0.2, "PUNT": 0.3}),
    (3, 5, 55): dict(next={}, term={"TD": 0.4, "FG": 0.35, "TOD": 0.25}),
}
RES = {v: k for k, v in C.RESULT_MAP.items()}


def synth(n_drives=30000, seed=3):
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(n_drives):
        s = (1, 10, 75)
        t = 3500.0
        seq = []
        while True:
            seq.append(s)
            spec = PLANT[s]
            u = rng.random()
            acc = 0.0
            moved = False
            for nx, p in spec["next"].items():
                acc += p
                if u < acc:
                    s, moved = nx, True
                    break
            if moved:
                continue
            cs = list(spec["term"].items())
            tot = sum(p for _, p in cs)
            u2 = rng.random() * tot
            acc = 0.0
            for c, p in cs:
                acc += p
                if u2 < acc:
                    res = RES[c]
                    break
            break
        for i, (dn, yd, yl) in enumerate(seq):
            rows.append(dict(game_id=f"g{d // 20}", season=2020, season_type="REG", fixed_drive=d % 20 + 1,
                             fixed_drive_result=res, posteam="AAA", defteam="BBB", down=dn, ydstogo=yd, yardline_100=yl,
                             play_type="pass", game_seconds_remaining=3500.0 - d % 20 * 100 - i * 8.0, extra_point_result=None,
                             two_point_conv_result=None, game_date="2020-09-10"))
    return pd.DataFrame(rows)


def test_estimator_recovers_planted_absorption():
    ch = C.estimate_chain(synth())
    N = np.linalg.inv(np.eye(C.S) - ch.Q)
    B = N @ ch.R
    a = int(C.sid(1, 10, 75))
    # truth by hand: P(reach B)=.55; from B P(reach C)=.5
    pc, pb = 0.55 * 0.5, 0.55
    truth = {"PUNT": 0.30 + pb * 0.3, "TURN": 0.15, "FG": pb * 0.2 + pc * 0.35, "TD": pc * 0.4, "TOD": pc * 0.25}
    # planted terminal probs are unnormalised weights of the non-move mass; renormalise per state
    def norm(s):
        t = PLANT[s]["term"]
        z = sum(t.values())
        return {k: v / z * (1 - sum(PLANT[s]["next"].values())) for k, v in t.items()}
    A, Bs, Cs = [norm(s) for s in PLANT]
    pb = sum(PLANT[(1, 10, 75)]["next"].values())
    pc = pb * sum(PLANT[(2, 5, 60)]["next"].values())
    truth = {}
    for k in C.CLASSES:
        truth[k] = A.get(k, 0) + pb * Bs.get(k, 0) + pc * Cs.get(k, 0)
    got = {k: float(B[a, C.CI[k]]) for k in C.CLASSES}
    for k in C.CLASSES:
        assert abs(got[k] - truth[k]) < 0.015, (k, got[k], truth[k])


def test_rows_stochastic_and_simulation_runs():
    ch = C.estimate_chain(synth(4000))
    assert np.allclose(ch.Q.sum(1) + ch.R.sum(1), 1.0)
    th = np.array([-0.1, 0.0, 0.1])
    banks, epd = C.build_banks(ch, th, 100, 1)
    assert epd[0] < epd[1] < epd[2]                       # tilt is monotone in expected drive points
    r = C.simulate_games(ch, banks, th, 0.0, 0.0, 200, 5)
    assert r["unfinished"] == 0 and (r["home"] >= 0).all() and (r["away"] >= 0).all()
