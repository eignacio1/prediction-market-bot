# W103.4 — GG-1771 / GG-1770 effect on the ADR-0072 forward test (read-only, existing data)

Inputs: box `demo_fill_policy.jsonl`, `demo_fill_forward_cache.json`, `markouts/` (copied 2026-11-06). Script: `recompute.py`; full output: `three_views.json`. No ledger rewritten. **No verdict word is relabelled here** — the logged NFL ADOPT stands as logged; the table shows what it becomes on corrected data and the operator decides.

## Epoch
Fix merged (#431, `da7849d`) **2026-11-06T00:58:09Z**; box deployed and t4-mlb/dashboard restarted **2026-11-06T01:03:42Z**. Cut for readers = the deploy time (code actually running). Nothing before the cut mixes with rows after it.

## NO-side volume (shadow book, all pre-epoch = bugged by code)
| Sport | NO orders | NO fills | YES orders | YES fills |
|---|---|---|---|---|
| NBA | 33,263 | 8,659 | 61,037 | 15,800 |
| NFL | 13,094 | 4,889 | 15,548 | 4,894 |
| NHL | 15,108 | 3,742 | 1,994 | 570 |
| MLB | 43 | 22 | 451 | 38 |
About 46% of all shadow orders and 49% of fills were NO-side. (Paper book NO split is not in this log.)

## Views
- **As logged** — cache as-is (NO outcomes inverted, GG-1770; NO limit mispriced, GG-1771).
- **YES-only** — NO orders removed. Unaffected by either defect.
- **NO outcome-corrected** — NO `won`/`nf_won` flipped; price is the actual per-contract fill cost.
- **NO re-priced** — **NOT COMPUTABLE** from existing fills. The limit was wrong on every NO order, and fills can price-improve to the market ask, so fill cost does not reveal which fills the correct limit would have produced. Bound only: limit error = |2p−1| of the YES mid (p>0.5 over-bid → extra, adversely selected fills; p<0.5 under-bid → fewer fills).

## ADR-0072 (a)(b)(c), shadow book
| Sport | View | fill rate ctl/trt | (a) diff [95%] | (b) b_ratio | (c) 30m | State |
|---|---|---|---|---|---|---|
| NFL | as logged | .502/.189 | +.190 [.088,.291] | .376 | −.012 | **ADOPT** |
| NFL | YES-only | .536/.100 | +.006 [−.100,.112] | .186 | −.012 | INCONCLUSIVE |
| NFL | NO outcome-corrected | .502/.189 | +.049 [−.075,.174] | .376 | −.012 | INCONCLUSIVE |
| NBA | as logged | .428/.086 | +.199 [.134,.264] | .202 | −.030 | (a) holds, (b) fails |
| NBA | YES-only | .449/.064 | +.102 [.016,.188] | .142 | −.030 | (a) holds, (b) fails |
| NBA | NO outcome-corrected | .428/.086 | +.118 [.043,.193] | .202 | −.030 | (a) holds, (b) fails |
| NHL | as logged | .419/.094 | +.303 [.227,.379] | .224 | +.036 | (a) holds, (b) fails |
| NHL | YES-only | .541/.023 | +.390 [.208,.572] | .043 | +.036 | NO VERDICT (trt n=22) |
| NHL | NO outcome-corrected | .419/.094 | +.217 [.145,.288] | .224 | +.036 | (a) holds, (b) fails |
MLB shadow: no judged cell (n=0/0 for arms).

(c) markouts are **not** affected: the collector reads the fills endpoint whose side equals the intended order side on all 30,927 markout rows (13,109 NO, 17,818 YES), so held-side markouts are right for NO. (b) uses fill counts only, so it does not move.

## E1/E2/E3 (NFL, per arm)
| View | Arm | win rate on fills | settle−price on fills | win rate on non-fills |
|---|---|---|---|---|
| as logged | ctl / trt | .412 / .549 | +.056 / +.246 | .335 / .336 |
| YES-only | ctl / trt | .261 / .245 | −.059 / −.052 | .391 / .316 |
| NO outcome-corrected | ctl / trt | .309 / .305 | −.047 / +.003 | .555 / .447 |
Every sport's fills-vs-non-fills win rate moves materially: logged fills look good (NFL .41–.55); on corrected data fills win less than non-fills (.26–.31 vs .32–.55), i.e. adverse selection is present, in the direction GG-037 found. The T4 MLB 25.4% vs 48.3% E3 figure is from the paper book, which is not in this log; it is not recomputable from these inputs.

## Operator line
GG-1771/GG-1770 fixed and live since 01:03Z 2026-11-06; about half of all shadow orders were NO-side and were mispriced and scored backwards, and **the NFL ADOPT does not survive on YES-side fills alone or with NO outcomes corrected — both give INCONCLUSIVE ((a) CI spans 0)**; the logged ADOPT is left as logged pending your call on whether to restart the NFL test clock from the new epoch.
