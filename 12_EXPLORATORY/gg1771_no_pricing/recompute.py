"""W103.4 Part B (read-only): ADR-0072 forward-test numbers under three views of the NO-side defects.
Usage: python3 recompute.py <log.jsonl> <cache.json> <markout_dir> <out.json>
as_logged  = cache as-is (GG-1770: NO outcomes inverted).  yes_only = NO orders (and their cancel events) removed.
no_outcome_corrected = NO won/nf_won flipped (side set to 'no'); price stays the actual per-contract cost.
NO re-priced is NOT computable from existing fills (see RESULT.md)."""
import copy, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts")); sys.path.insert(0, str(REPO / "src"))
import demo_fill_forward_report as R  # noqa: E402
sys.path.insert(0, str(REPO / "12_EXPLORATORY"))
from _fence import safe_out  # noqa: E402

log, cache_p, mdir, out = sys.argv[1:5]
events = R.load_events(Path(log)); cache = json.load(open(cache_p))
no_ids = {e["order_id"] for e in events if e.get("event") == "shadow_order" and e.get("ok") and e.get("side") == "no"}
yes_events = [e for e in events if e.get("order_id") not in no_ids and not (e.get("event") == "shadow_order" and e.get("side") == "no")]
fixed = copy.deepcopy(cache)
for oid in no_ids:
    r = fixed.get(oid)
    if not r: continue
    r["side"] = "no"
    for k in ("won", "nf_won"):
        if k in r: r[k] = not r[k]
now = datetime.now(timezone.utc)
def run(evs, c):
    return R.build_report(evs, now, lambda oid, tk: c.get(oid, {"status": "unretrievable"}), "", None, None, Path(mdir))
res = {"as_logged": run(events, cache), "yes_only": run(yes_events, cache), "no_outcome_corrected": run(events, fixed)}
counts = Counter()
for e in events:
    if e.get("event") == "shadow_order" and e.get("ok"):
        sp = R.sport_of(R.ticker_of(e)); s = e.get("side") or "unknown"; r = cache.get(e["order_id"], {})
        counts[(sp, s, "orders")] += 1; counts[(sp, s, "fills")] += 1 if (r.get("fills") or 0) > 0 else 0
res["no_side_counts"] = {f"{a}|{b}|{c}": n for (a, b, c), n in sorted(counts.items())}
json.dump(res, open(safe_out(out), "w"), indent=1, default=str)
for v in ("as_logged", "yes_only", "no_outcome_corrected"):
    print("==", v)
    for k, x in res[v]["verdicts"].items():
        a = x.get("a_diff") or {}
        print(f"{k:12} n={x.get('control_n')}/{x.get('treatment_n')} fr={x.get('fill_rate_control')}/{x.get('fill_rate_treatment')} "
              f"a={a.get('diff')} [{a.get('lower95')},{a.get('upper95')}] b={x.get('b_ratio')} c={(x.get('c_markout') or {}).get('diff',{}) and x['c_markout']['diff'].get('diff')} | {x.get('state')}")
print(json.dumps(res["no_side_counts"]))
