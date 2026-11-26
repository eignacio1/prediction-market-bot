"""Build NBA point-in-time PAM mass-tier archetype records (W130.4). Fit on TRAIN seasons only; write monthly
snapshots of the EVAL season to qualitative_data/pam_pit/nba/records.jsonl (append-only; a deep-tier file is untouched).
Usage: PYTHONPATH=src python3 scripts/pam_pit_archetype_build.py [--write]"""
from __future__ import annotations
import datetime as dt, json, sys
from pathlib import Path
import pandas as pd
from prediction_market_bot.pam import nba_pit_archetype as A, nba_pit_profile as P
from prediction_market_bot.pam.schema import ArchetypeWeight, Basis, Classifier, PamRecord
from prediction_market_bot.pam.store import PamStore

RAW = Path("/Users/earlignacio/PredictionMarketEvidence/data/exp_output/NBA_EVENTS/raw")
OUT_ROOT = Path(__file__).resolve().parents[1] / "qualitative_data" / "pam_pit"
TRAIN, EVAL = [2022, 2023, 2024, 2025], 2026
SNAPS = ["2025-11-01", "2025-12-01", "2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01"]
MIN_POSS_PIT = 800.0
PROFILE_KEYS = ["gp", "poss", "usage_per100", "ast_per100", "oreb_per100", "dreb_per100", "oreb_share", "dreb_share",
                "oreb_mix", "rim_share", "three_share", "blk_per100", "stl_per100", "opp_rim_rate_on", "opp_rim_fg_on"]

def load(s):
    r = lambda t: pd.read_parquet(RAW / t / f"{t}_{s}.parquet")
    return P.game_table(r("pbp"), r("possessions"), r("player_box"), r("schedule"))

def build(games):
    tr = pd.concat([P.profile_as_of(games, s, f"{s}-07-01", min_poss=1500) for s in TRAIN])
    params = A.fit(tr)
    recs = []
    names = {}
    for i, d in enumerate(SNAPS):
        pr = P.profile_as_of(games, EVAL, d, min_poss=MIN_POSS_PIT)
        asg = A.assign(pr, params)
        until = dt.date.fromisoformat(SNAPS[i + 1]) if i + 1 < len(SNAPS) else None
        day = dt.date.fromisoformat(d)
        for pid, a in asg.iterrows():
            prof = {k: (None if pd.isna(pr.loc[pid, k]) else round(float(pr.loc[pid, k]), 4)) for k in PROFILE_KEYS}
            recs.append(PamRecord(
                record_id=f"nbapit:{A.VERSION}:{d}:{pid}", sport="nba", player_id=str(pid),
                archetypes=tuple(ArchetypeWeight(id=k, weight=v) for k, v in a["weights"].items()),
                tier="mass", classified_by=Classifier(kind="model", name="mass", version=A.VERSION),
                effective_from=day, effective_until=until, recorded_at=day, confidence=a["confidence"],
                basis=Basis(seasons=(f"{EVAL-1}-{str(EVAL)[2:]}",), sources=("nba_event_store:pbp+possessions+player_box",),
                            text=f"games strictly before {d}; fit on seasons {TRAIN[0]}-{TRAIN[-1]} only"),
                taxonomy_version="pam_v4", id_map={"nba_person_id": str(pid)},
                extra={"profile": prof, "profile_version": P.VERSION, "unbuilt_archetypes": list(A.UNBUILT), "fit_n": params["n_train"]}))
    return recs, params

if __name__ == "__main__":
    games = pd.concat([load(s) for s in TRAIN + [EVAL]], ignore_index=True)
    recs, params = build(games)
    print(len(recs), "records;", len({r.player_id for r in recs}), "players")
    if "--write" in sys.argv:
        print("written", PamStore(OUT_ROOT).append(recs))
        from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
        pb = pd.read_parquet(RAW / "player_box" / f"player_box_{EVAL}.parquet")
        nm = {norm_name(f"{r.first_name} {r.family_name}"): str(int(r.person_id)) for r in pb.drop_duplicates("person_id").itertuples()}
        (OUT_ROOT / "nba" / "name_map.json").write_text(json.dumps(nm, sort_keys=True))
