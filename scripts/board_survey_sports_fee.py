#!/usr/bin/env python3
"""EXP-035 D2(e): fee re-score of EXP-031/032's published E (policy a / first-seen). READ-ONLY. Adds one-way taker fee
k*p*(1-p) per contract at the first-seen mid; nothing else is re-cut. Verdict labels are NOT changed."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from market_efficiency_survey import decision_snapshots

K = {"ADR0016_0.07": 0.07, "series_multiplier_0.5_x_0.07_INFERRED_UNVERIFIED": 0.035}
archive, exp031, exp032, out = sys.argv[1:5]
snaps = decision_snapshots(archive)
ref = json.load(open(os.path.join(exp032, "results.json")))["families"]
res = {}
for fam in ("KXMLBHIT", "KXMLBTEAMTOTAL"):
    st = json.load(open(os.path.join(exp031, "settlements", f"{fam}.json")))
    p = np.array([s["p"] for t, s in snaps.items() if s["series"] == fam and st.get(t, {}).get("result") in ("yes", "no")])
    r = ref[fam]; E0 = r["policy_a"]["E"]; ci = r["policy_a"]["E_ci_game"]
    res[fam] = {"n": int(len(p)), "E_published_policy_a": E0, "E_ci_game_published": ci, "label_published": r["policy_a"]["label"],
                "fee": {}}
    for name, k in K.items():
        f = k * p * (1 - p)
        fm = float(np.median(f)); fmean = float(f.mean())
        res[fam]["fee"][name] = {"k": k, "fee_median": fm, "fee_mean": fmean, "E_net_median_fee": E0 - fm,
                                 "E_net_mean_fee": E0 - fmean, "E_net_ci_game_shifted_by_median": [c - fm for c in ci]}
json.dump(res, open(out, "w"), indent=1); print(json.dumps(res, indent=1))
