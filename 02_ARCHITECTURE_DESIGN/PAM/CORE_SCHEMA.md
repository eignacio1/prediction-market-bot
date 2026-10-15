# PAM Core Schema

**Status:** W75.1 Part A, 2026-10-14. Implements ADR-0075 §3 (PAM core segment). Code: `src/prediction_market_bot/pam/`. Store: `qualitative_data/pam/<sport>/records.jsonl`.

> Operator, 2026-10-14: "we're gonna start piping in the PAM into the NFL, NBA, MLB and NHL (starting with NFL and NBA) - this is going to be a portion of our Syndicate32 bridging - it needs to stay dynamic enough that we can port it easily and do mass application but we'll keep it substantive for when it matters most."

One sport-agnostic record, one append-only store, one read path. Sport specifics live only in a taxonomy file (`qualitative_data/pam/<sport>/taxonomy.json`), never in the record shape.

## Record (`PamRecord`)

| Field | Meaning |
|---|---|
| `record_id` | Unique within the store. NBA: `nba:<snapshot>:<player_id>`. |
| `sport`, `player_id` | Sport key; the project's canonical id for that sport (NBA: person id). |
| `id_map` | `{source: id}` for every source the player appears in (NBA `nba_person_id`; NFL `gsis_id`, `pfr_id`). |
| `archetypes` | Weighted hybrid: one or more `{id, weight, label}`. Weights in (0,1], sum to 1 (tol 1e-6), ids unique. `label` is the classifier's own wording; canonical names are in the taxonomy. |
| `modifiers` | Named flags `{id, name, threshold, evidence}`; threshold copied from the taxonomy at write time. Additive on top of the archetype mix. |
| `effective_from` / `effective_until` | Window the classification describes (QTI-01/02). `until` exclusive; None = open. |
| `recorded_at` | When the classification was made (knowledge time). |
| `tier` | `mass` (rule/model, many players) or `deep` (operator + Claude, few players). |
| `classified_by` | `{kind: human\|rule\|model, name, version}`. |
| `confidence` | Optional [0,1]. |
| `basis` | `{seasons, sources, text}`. |
| `supersedes` | Record ids this record replaces (same sport and player only). |
| `snapshot_id`, `taxonomy_version`, `backdated`, `backdating_rationale`, `notes`, `player_name`, `extra` | Provenance. `backdated=True` requires a rationale (QTI-02). |

## Store rules

- **Append-only.** `PamStore.append` only adds lines; a duplicate `record_id` or a supersede of an unknown / other-player record raises. Nothing is ever rewritten. A new classification supersedes, it never overwrites.
- **Supersession is virtual.** A superseded record stops applying from the date its superseder takes effect, so reads before that date still return the old classification.

## The one read path

`pam_as_of(sport, player_id, as_of, *, known_at=None) -> PamRecord | None`

A record applies iff `effective_from <= as_of < effective_until`. With `known_at`, records with `recorded_at > known_at` are invisible. A classification effective after `as_of` is never returned. Ties: latest `effective_from`, then latest `recorded_at`, then deep over mass, then `record_id`. Engines must call this and nothing else.

## NBA v4 port (lossless)

Both QS CSVs (50 players each) become 100 `deep` records. `QS-…-002` (backdated, earlier `effective_from`) supersedes `-001`. `record_to_csv_row` inverts the port and `tests/test_pam_core.py` asserts every row of both CSVs reproduces exactly. A pure archetype (secondary 0) is one archetype at weight 1.0. Canonical archetype (PRF-1..15) and modifier (M-1..32) names, thresholds and signals are extracted from `Player_Attribute_Matrix_v4.docx` into `qualitative_data/pam/nba/taxonomy.json` (`nba_port.extract_taxonomy_from_docx`). The experiment scripts still read the old CSVs; nothing is rewired. The CSVs carry no per-modifier evidence, so NBA modifier `evidence` is empty and the player-level `notes` hold it.

## Stage (ADR-0075)

Core schema/store: PLUMBING for the D5(a) measure. NBA records: stage **aggregated** (human-classified, not yet applied by any engine).
