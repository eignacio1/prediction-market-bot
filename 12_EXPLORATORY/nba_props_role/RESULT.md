# EXP-047-C1 retrospective result (W125.4)
Rule: PREREG.md (frozen 437975c, committed before any outcome was read). Script: run_retro.py. Numbers: RESULT.json.
Data: sportsdataverse box scores + ESPN tips + the in-repo injury snapshots (Out = status Out at the last slot >=4h before tip).

## Verdict by the PREREG rule: **INDETERMINATE (mixed sign)**
One stat improves (BH-significant), three are worse (BH-significant). The rule gives SUPPORTED only if none is worse, and REFUTED only if none improves. Neither holds.
Hypothesis C1 as written (one shared proportional rule on all four stats) is not supported. It is not closed for points (see below).

## Judge window (games on/after 2024-10-01, teams with V>0)
1,899 games, 357,010 scored rows, 32,028 DNP rows excluded. 166 of 4,920 games had no pre-tip report and were skipped (counted, not scored).
Log-loss difference C1 minus EXP-047 (negative = C1 better), game-clustered bootstrap, 10,000 draws:

| Stat | diff | 95% interval | Brier diff | verdict |
|---|---|---|---|---|
| points | -0.0273 | [-0.0306, -0.0241] | -0.0080 | improves |
| assists | +0.0090 | [+0.0070, +0.0109] | +0.0025 | worse |
| rebounds | +0.0232 | [+0.0206, +0.0259] | +0.0074 | worse |
| threes | +0.0025 | [+0.0007, +0.0043] | +0.0009 | worse |

## By vacated usage V (share of the rotation's points mean that is Out)
| Stat | V<0.10 | 0.10-0.25 | V>=0.25 |
|---|---|---|---|
| points | -0.0105 | -0.0293 | -0.0565 |
| assists | +0.0021 | +0.0056 | +0.0343 |
| rebounds | +0.0088 | +0.0162 | +0.0765 |
| threes | -0.0003 (spans 0) | +0.0002 (spans 0) | +0.0155 |
All points cells improve and the gain grows with V. Rebounds, assists and threes get worse as V grows. The modal outcome in PREREG (points modest, others indeterminate) understated points and was wrong on the other three: they are worse, not indeterminate.

## Read
- The same factor f was applied to every stat. That fits points, which follow usage. Rebounds and assists follow position and role, so scaling every teammate up overshoots. This is an explanation, not a tested result.
- Listed-Out reliability: P(played | listed Out) is 0.05%-0.2% by season, so the Out flag is clean.
- Scored against realised outcomes on a fixed synthetic ladder. This is not a market comparison and not an edge claim (ADR-0075: applied = a tested path to a price).
- Seeds are shared between arms, so the paired difference is the rule, not the draw noise.

## Consequence
- Rebounds, assists, threes: hypothesis closed for the uniform rule (EXP-047-C1, parked for R&D). Reopen only with a stat-specific absorption rule, pre-registered first.
- Points: a per-stat points-only variant (proposed EXP-047-C2) is worth its own pre-registration. It is chosen after seeing this result, so this retro cannot confirm it; it needs a fresh window or the forward log.
- Nothing is activated. PM_PROPS_C1 stays off; activation is the operator's call (queue line).
- Limits: fit window 2022-23..2023-24 is used for diagnostics only. 2026-27 games are not in the judge window.
