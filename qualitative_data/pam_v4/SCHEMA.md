# PAM v4 Classification Schema — DS-01

**Purpose:** Defines every column in a DS-01 PAM classification CSV. All QS snapshots for DS-01 must conform to this schema.  
**Version:** 1.0 (2026-05-28)  
**Source:** Player_Attribute_Matrix_v4.docx — fill in archetype names and modifier descriptions from that document when operationalization begins.

---

## Identity Columns

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `player_id` | integer | YES | NBA player ID (nba_api). Must match TARGET_PLAYER_IDS in run_exp001.py |
| `player_name` | string | YES | Full name for human readability (not used in model join; join key is player_id) |
| `classification_date` | YYYY-MM-DD | YES | Date this classification was made |
| `classified_by` | string | YES | Name or role of classifier (e.g., "Earl Ignacio") |
| `classification_basis` | string | YES | Which season(s) and data sources informed this classification (e.g., "2025-26 regular season; NBA.com box score + tracking; film review") |

---

## Temporal Integrity Columns (QTI-01, QTI-02)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `effective_from` | YYYY-MM-DD | YES | Earliest game_date for which this classification is valid. Must not predate the earliest season used as classification basis. |
| `effective_until` | YYYY-MM-DD or NULL | NO | Last game_date (exclusive) for which this classification is valid. NULL = currently active. Set when superseded by a new snapshot. |
| `backdated` | boolean (0/1) | YES | 1 if effective_from is set to a date before the classification_date (historical backdating). Requires backdating_rationale. |
| `backdating_rationale` | string | conditional | Required when backdated=1. Must cite specific evidence that the archetype was observable at the effective_from date. |

---

## PRF Archetype Columns (F-100–F-124)

| Column | Type | Required | Description | Feature ID |
|--------|------|----------|-------------|------------|
| `prf_primary` | integer (1–15) | YES | Primary PRF archetype ID. See DS-01 document for archetype definitions. | F-100 |
| `prf_secondary` | integer (0–15) | YES | Secondary archetype ID for hybrid players. 0 = no secondary. | F-101 |
| `prf_hybrid_weight` | float (0.0–1.0) | conditional | Primary archetype weight in hybrid notation (e.g., 0.7 = 70% primary, 30% secondary). Required when prf_secondary ≠ 0. Null when prf_secondary = 0. | F-102 |
| `prf_primary_name` | string | NO | Human-readable archetype name (informational only; not used as a model feature) | — |
| `prf_secondary_name` | string | NO | Human-readable secondary archetype name (informational only) | — |

---

## Modifier Columns (F-150–F-181)

Binary flags (0 = absent, 1 = present). See DS-01 document for threshold criteria for each modifier.

| Column | Type | Feature ID | Description |
|--------|------|------------|-------------|
| `mod_01` | binary | F-150 | Modifier 1 — name and threshold per DS-01 document |
| `mod_02` | binary | F-151 | Modifier 2 — name and threshold per DS-01 document |
| `mod_03` | binary | F-152 | Modifier 3 |
| `mod_04` | binary | F-153 | Modifier 4 |
| `mod_05` | binary | F-154 | Modifier 5 |
| `mod_06` | binary | F-155 | Modifier 6 |
| `mod_07` | binary | F-156 | Modifier 7 |
| `mod_08` | binary | F-157 | Modifier 8 |
| `mod_09` | binary | F-158 | Modifier 9 |
| `mod_10` | binary | F-159 | Modifier 10 |
| `mod_11` | binary | F-160 | Modifier 11 |
| `mod_12` | binary | F-161 | Modifier 12 |
| `mod_13` | binary | F-162 | Modifier 13 |
| `mod_14` | binary | F-163 | Modifier 14 |
| `mod_15` | binary | F-164 | Modifier 15 |
| `mod_16` | binary | F-165 | Modifier 16 |
| `mod_17` | binary | F-166 | Modifier 17 |
| `mod_18` | binary | F-167 | Modifier 18 |
| `mod_19` | binary | F-168 | Modifier 19 |
| `mod_20` | binary | F-169 | Modifier 20 |
| `mod_21` | binary | F-170 | Modifier 21 |
| `mod_22` | binary | F-171 | Modifier 22 |
| `mod_23` | binary | F-172 | Modifier 23 |
| `mod_24` | binary | F-173 | Modifier 24 |
| `mod_25` | binary | F-174 | Modifier 25 |
| `mod_26` | binary | F-175 | Modifier 26 |
| `mod_27` | binary | F-176 | Modifier 27 |
| `mod_28` | binary | F-177 | Modifier 28 |
| `mod_29` | binary | F-178 | Modifier 29 |
| `mod_30` | binary | F-179 | Modifier 30 |
| `mod_31` | binary | F-180 | Modifier 31 |
| `mod_32` | binary | F-181 | Modifier 32 |

*Populate modifier names from DS-01 document. The column names (mod_01..mod_32) are fixed — add a lookup table in the DS-01 document or a separate MODIFIER_LOOKUP.md.*

---

## Notes Column

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `notes` | string | NO | Free-text notes on this player's classification (edge cases, disagreements, confidence level) |

---

## Validation Rules

Before registering a QS snapshot:
- [ ] All 50 TARGET_PLAYER_IDS are present (or the subset being classified is explicitly documented)
- [ ] No player_id appears more than once per (effective_from, effective_until) range
- [ ] prf_primary is in range 1–15
- [ ] prf_secondary is 0 or in range 1–15
- [ ] prf_hybrid_weight is null iff prf_secondary == 0
- [ ] All mod_XX columns are 0 or 1 (no nulls — default to 0 if modifier is absent)
- [ ] effective_from is populated on all rows
- [ ] backdated column is populated on all rows (0 or 1)
- [ ] backdating_rationale is populated on all rows where backdated == 1
