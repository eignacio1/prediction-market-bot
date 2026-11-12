# Operator Digest — 2026-11-12

- B-076 (auto): W111.1 B-076: a losing look closes only the FADE arm; NFL game total T1/T2 reopened as SHADOW (PR #482, c592dda).
- B-077 (auto): W111.2 B-077 doctrine-conformance audit: 41 code decision points, label fixes + banned-word test merged (#481), #480 merged

## W111.4 — NBA granularity index (DEPTH)
Built the NBA "situation" index: 24 entries, each with the split, how the team ranks against history, the matchup cross and the market map. 18 were scored per leaf, by arm, on games the fit never saw. None survived the multiple-comparison correction, so those leaves are routed to NO_BET for now, which is a routing result and not a verdict on any cell. NBA depth moved 10 to 11 of 17. Still zero real money at risk. NFL, NHL and MLB entries are not built yet.
