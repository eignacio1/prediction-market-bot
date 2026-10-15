# SESSION HANDOFF — W75.1 PAM core

```
vision_pillar: DEPTH
gap_measure: D5(a) cluster designs (NFL, NBA)
gap_delta: NFL 0 -> 1, NBA 0 -> 1 (source: 02_ARCHITECTURE_DESIGN/PAM/README.md D5 line, 2026-10-14; before = ACTIVE_QUEUE 75.1 row, 0/0)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
```

**Status:** DONE (Parts A and B) | branch `session/20261015T050519Z-w75-1-pam-core` | PR #259 | 19 tests green locally.

**Result:** PAM core (schema, append-only store, `pam_as_of`), lossless NBA v4 port (100 deep records, CSV round-trip tested), NFL 9-group taxonomy, NFL WR mass classifier 2023-2025 (247 records, tier = mass), `DEEP_TIER.md` proposal, README, GG-775..779 registered.

**NFL WR mass tier (primary archetype counts, WR with 50+ targets):** 2023 n=80 MID 36 / VOL 21 / VERT 15 / YAC 8; 2024 n=89 MID 43 / VOL 18 / VERT 18 / YAC 10; 2025 n=78 MID 35 / VERT 19 / VOL 16 / YAC 8. Hybrids (2+ archetypes) 63-76 of each season, so the primary label is a rough summary of a mix.
**Stability:** primary label retained 54% (2023->24, n=57) and 60% (2024->25, n=60) vs ~30-33% by chance, so partly trait, partly noise. Split-half reliability (odd/even weeks, Spearman-Brown): aDOT 0.82-0.86, target share 0.89-0.93, short-target rate 0.81-0.89, deep rate 0.63-0.79, YAC per rec 0.58-0.70. Year-over-year r: aDOT 0.75-0.77, target share 0.45-0.60, YAC per rec ~0.50. Volume and depth are traits; YAC is the noisiest.
**Five examples a football eye can check (2025):** Jaxon Smith-Njigba SEA (volume 0.57 / intermediate 0.43), Brian Thomas JAX (pure vertical, aDOT 14.5), Khalil Shakir BUF (YAC 0.67, aDOT 3.7), Tyreek-type deep threat Tee Higgins CIN (vertical 0.70, aDOT 13.4), Deebo Samuel WAS (YAC 0.52 / volume 0.48, aDOT 5.3). Full list in `02_ARCHITECTURE_DESIGN/PAM/NFL_WR_MASS_REPORT.txt`.
Known weakness: WR-MID is the catch-all (45% of primaries); the rules were fixed a priori and not tuned.

**Stage reached per factor (ADR-0075):** NBA PRF/modifiers: aggregated. NFL WR archetypes: aggregated. NFL QB/RB/TE/OL/DL/LB/CB/S: designed only. Nothing interpreted or applied.

**Out of scope, not touched:** experiment scripts, runtime registry, dashboards, deploy, settings. No running component added.

**MEASURE MOVED:** D5(a) NFL 0 -> 1, NBA 0 -> 1 (README D5 line).

**Operator decision (one line):** Should the deep tier start with the NFL starting QBs and top-2 WRs per team (about 100 players), reviewed by you in batches of 10 per sitting?
