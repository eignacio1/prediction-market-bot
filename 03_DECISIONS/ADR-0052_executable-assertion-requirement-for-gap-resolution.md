# ADR-0052 — Executable-Assertion Requirement for Governance-Gap RESOLVED Status + G6 Ledger-Invariant Precondition

**Status:** PROPOSED — drafted this session (T-433) under explicit task instruction; awaiting DS sign-off (Earl Ignacio). Not yet ACCEPTED. Treat as governing intent, not a closed decision, until sign-off is recorded here.
**Date:** 2026-08-11
**Author:** Session `20260811T043030Z-invariant-policy` (T-433)
**Supersedes:** ADR-0007 §"Decision" → "1. GOVERNANCE_GAP_LOG.md" (the RESOLVED-marking criterion — ADR-0007's other mechanisms, the ARE WE COMPROMISED? 5-question check and the 3-step session-start scan, are unaffected and remain fully operative; ADR-0007 itself is not edited in place, per Hard Rule 3)
**Amends:** ADR-0028 §"Updated G6 Closure Condition" (adds a 7th item; does not alter items 1–6)
**Depends on:** T-432 (`scripts/assert_ledger_invariants.py`, in parallel development, task brief only as of this ADR's drafting — see `04_EXECUTION/ACTIVE_QUEUE.md` lines 120-236)
**Scope:** Governance process only. No `src/` change. No code. Governs how `GOVERNANCE_GAP_LOG.md` entries earn RESOLVED status going forward, and adds one precondition to the G6 gate.

---

## 1. Context

Two controls were compared this session, both addressing the same defect family (wrong-day/wrong-game resolution corrupting the T4M-PROJ paper ledger):

- **GG-149** (offsetting/wash-trade suppression) HELD. It is a code-based per-ticker opposite-direction check plus a tagging script (`scripts/tag_locked_pairs_t4_mlb.py`), `logic_epoch` 11→12. When T-432's baseline suite ran against the live ledger, it found 17/151 T4 both-direction-OPEN violations — all pre-epoch-12 legacy residue, correctly distinguishable from a live regression because the check is executable and re-runnable against fresh data.
- **GG-164** (the `game_date` field bug) did not hold in the same way. Its original "Why it survived" field asserted an unverified negative — a claim that the field wasn't used as a join key — that GG-166's own investigation later contradicted directly: `run_resolve_mlb.py` consumed exactly that field as a join key and silently resolved ~44%-to-55% of affected cohorts against the wrong day's box score.

**The difference is not diligence. One was executable and the other was prose.** A prose "why it survived" field can be well-reasoned, reviewed, and still wrong, because nothing re-checks it against reality after it's written. An executable assertion is wrong or right every time it runs, on whatever data currently exists.

Separately, the live count of OPEN governance gaps was cited three different ways in the 48 hours preceding this session — 46, then 49, then 51 — each citation individually defensible at the moment it was made, none of them stable enough to reason from. That instability is itself evidence for the same point: a status that lives only in prose narrative (a paragraph asserting current state) decays faster than a status a machine can recompute. GOVERNANCE_GAP_LOG.md's own OPEN count is machine-countable today (T-420's structured `**Status:** TOKEN · **Severity:** LEVEL` line, `grep -c`) precisely because the same lesson was already applied to *whether a gap is open*. This ADR applies the identical lesson to *whether a gap is resolved*.

**Precedent for the mechanism:** T-420/Window F's restructuring of `GOVERNANCE_GAP_LOG.md` (2026-08-05) replaced an emphasis-dependent OPEN/RESOLVED signal (bold vs. plain markdown, GG-144) with a structured field a machine can read. That restructuring's own governing principle — "the signal that routes attention belongs in a structured field a machine can read, not in how emphatically a paragraph is written" — is the direct precedent this ADR extends from *status* to *resolution basis*.

## 2. Decision

### 2.1 — RESOLVED requires an assertion or a named exemption

**A governance gap in `GOVERNANCE_GAP_LOG.md` may not be marked `RESOLVED` (and therefore may not be moved to `GOVERNANCE_GAP_LOG_ARCHIVE.md`) unless its structured header line carries an `**Assertion:**` field in one of two states:**

1. **An executable assertion exists that would have caught the gap** — a script, test, or check that, had it existed and been run against the corrupted state, would have failed loudly. State it concretely: `LANDED(<path>::<test_or_check_id>)`.
2. **No such assertion is possible, stated explicitly and specifically** — not "N/A", not silence. State what kind of check was considered and why it can't apply (e.g., a one-time documentation-formatting correction has no data invariant to assert against). Format: `EXEMPT: <reason>`.

**PENDING is not a terminal state for RESOLVED.** If the remediation code has landed but the assertion that would continuously re-verify it has not, the gap's Assertion field reads `PENDING(<T-ID>)` and the gap's Status field stays `OPEN` (or a more specific in-progress token per ADR-0007's existing vocabulary), never `RESOLVED`, until the assertion itself lands. A fix without a standing check is remediation, not closure — this is the exact gap GG-164's "unverified negative" fell into: the code path was believed fixed, and nothing re-verified that belief against new data until a separate investigation (GG-166) happened to test it.

### 2.2 — Field grammar

Extends the T-420 structured header line from two fields to three:

```
**Status:** TOKEN · **Severity:** LEVEL · **Assertion:** VALUE
```

Where `VALUE` is exactly one of:
- `LANDED(<path>::<id>)` — an executable assertion exists and is wired into a script, test suite, or governance hook. `<path>` is the file; `<id>` is the test name, check name, or function the assertion lives in.
- `PENDING(<T-ID>)` — an assertion is designed/scoped/in progress under a named task, not yet landed. Gaps carrying this value are not eligible for RESOLVED regardless of what other remediation has occurred.
- `EXEMPT: <reason>` — no executable assertion applies to this gap. The reason must name what kind of check was considered and why it doesn't fit (process/documentation-only defects, one-time historical-data corrections with no recurring invariant, etc.) — a reviewer must be able to look at the reason and agree or disagree with it, not just accept that a reason exists.

**The escape hatch is narrow by construction, not by discipline:** `EXEMPT` is a value in a grep-able field, not the absence of a field. `grep -c "EXEMPT:" GOVERNANCE_GAP_LOG.md` and the same against the archive gives an exact, reviewable exemption count at any time — the same structural property T-420 gave the OPEN/RESOLVED count. A gap with no `**Assertion:**` field at all (an omission, not a stated `EXEMPT`) is a format violation, not a valid exemption, and should be treated the same way GG-165's missing-Severity gaps are treated: registered, not silently tolerated.

### 2.3 — G6 precondition (amends ADR-0028)

**Adds item 7 to ADR-0028 §"Updated G6 Closure Condition"** (items 1–6 unchanged, reproduced for reference: Tier 0, statistical floor, Tier 1, Tier 2, Tier 3, formal gate prerequisites):

> **7. Ledger invariant integrity** — G6 does not clear until (a) the invariant suite (T-432, `scripts/assert_ledger_invariants.py`) runs clean at `--strict` for a stated observation period, and (b) cross-path outcome agreement (the independent-store agreement check GG-166/GG-170 established) is a standing check that runs continuously against the live ledger, not a one-off investigation that happened to run once.

**Why this is a G6 precondition and not merely a hygiene item:** G6 authorizes live capital. Two mechanisms downstream of the paper ledger directly determine how that capital is deployed and protected:

- **Kelly position sizing sizes off the measured win rate.** The win rate is computed from resolved WIN/LOSS outcomes in the same ledger GG-166 found corrupted (55.63% overall game_date mismatch pre-fix; a second, independent 25.1% outcome-disagreement source — GG-170 — persists even after the game_date fix is 100% clean). A win rate computed from resolutions against the wrong game is not a measurement of the model's real edge; it is noise with a sign.
- **The permanent drawdown kill switch (`max_drawdown_pct = 0.20` in `_HARD_LIMITS`, `risk.py`) computes `realized_loss / initial_bankroll` from that same ledger.** The kill switch is the mechanism that is supposed to catch it when the bot is wrong about its own edge. If the ledger it reads is corrupted the same way the sizing input is corrupted, the kill switch is not an independent check on the sizing decision — it is measuring the same fiction the sizing decision was computed from. **The safety mechanism sits downstream of the corruption.** A bot sized up on a fictional edge, whose kill switch also reads the fiction, does not fail safe; it fails silently, exactly as GG-166 demonstrated happened to 223/223 open positions before anyone noticed.

A one-off investigation (GG-166's B1–B5 sub-investigations) proved this happened once and was fixed once. It does not prove it stays fixed. GG-170's discovery — a *second*, structurally distinct disagreement source found only because B5 kept checking after B1–B4's fix looked complete — is the concrete demonstration that "we checked and it was clean" is a point-in-time claim, not a standing guarantee, for exactly this ledger. Item 7 requires the standing check to remain the closure condition, not the one-time proof.

**This precondition does not block current work.** T-432 is unstaffed-relative-to-this-ADR (a parallel, already-claimed task) and is `PENDING`, not required to exist before this ADR is accepted — this ADR states the requirement and its justification; T-432 fulfills it. G6 was already blocked by T0-A (GG-004, EXP-017 not yet CONFIRMED_POSITIVE) at the time of this ADR's drafting, so item 7 adds no new *practical* delay today — it closes a gap that would otherwise surface only once GG-004 clears and G6 evaluation actually reaches the ledger-quality question.

## 3. Retrofit (applies §2.1–2.2 to six specific gaps; not a blanket migration)

**Not applied to all 114 archived RESOLVED entries.** Applying this requirement retroactively to the full archive is out of scope for this ADR and this session — it is exactly the kind of low-value, collision-prone busywork ADR-0044 §"Non-Goals" already warns against for a related migration. Applied only to the six gaps in the defect family that motivated this ADR:

| Gap | Location | Assertion | Basis |
|---|---|---|---|
| GG-164 | `GOVERNANCE_GAP_LOG.md` (live, OPEN) | `PENDING(T-432)` — assertion A (join-key/`game_date` validity) | T-432 task brief, `ACTIVE_QUEUE.md` lines 120-236 |
| GG-166 | `GOVERNANCE_GAP_LOG.md` (live, OPEN) | `PENDING(T-432)` — assertion A (shared with GG-164; same defect, write-site vs. read-site) | same |
| GG-149 | `GOVERNANCE_GAP_LOG_ARCHIVE.md` (RESOLVED) | `PENDING(T-432)` — assertion H (offsetting/both-direction-open check) | see `03_DECISIONS/GG_ASSERTION_RETROFIT_LEDGER.md` (new linked file — archive not hand-patched, per Hard Rule/CLAUDE.md archive-immutability convention) |
| GG-142 | `GOVERNANCE_GAP_LOG_ARCHIVE.md` (RESOLVED) | `LANDED(tests/test_c4_risk.py::test_negative_directional_edge_rejected)` (plus two CHECK-4b tests); secondary `PENDING(T-432)` fee_net_edge cascade assertion | same linked file |
| GG-141 | `GOVERNANCE_GAP_LOG_ARCHIVE.md` (RESOLVED) | `LANDED(scripts/check_feature_column_health.py)` | same linked file |
| GG-145 | `GOVERNANCE_GAP_LOG.md` (live, OPEN — not RESOLVED, no RESOLVED-eligibility question applies yet) | `LANDED(scripts/check_feature_column_health.py)` — detection assertion exists and already caught this exact defect; the underlying `park_factor_hits` bug itself remains unfixed | GG-141's own Resolution field, GG-145's own entry |

**Archive-immutability handling:** GG-149/GG-142/GG-141 are already in `GOVERNANCE_GAP_LOG_ARCHIVE.md`, moved there verbatim per the T-420 restructure, and CLAUDE.md is explicit that the archive is never hand-patched for content. Rather than violate that, their assertion mapping is recorded in a new standalone file, `03_DECISIONS/GG_ASSERTION_RETROFIT_LEDGER.md`, which points at the unmodified archive entries rather than editing them — applying ADR-0044's "current-status line + linked file" pattern in reverse (annotating existing immutable content via a pointer file, rather than relocating dense content out of a live one).

## 4. Non-Goals

- Does not retrofit the other ~108 archived RESOLVED gaps outside the six named above.
- Does not require every OPEN gap to declare an Assertion field retroactively as a blocking condition for continued work — this ADR governs the RESOLVED transition going forward, and the six gaps named in §3 as a bounded, motivated exception.
- Does not build `scripts/assert_ledger_invariants.py` — that is T-432, tracked separately.
- Does not change `GOVERNANCE_GAP_LOG.md`'s Status or Severity vocabulary, only adds the third field.
- Does not re-litigate GG-149/GG-142/GG-141's RESOLVED verdicts — those stand; this ADR only adds the assertion-basis annotation on top of an unchanged verdict.

## 5. Consequences

- Every future RESOLVED marking is a reviewable claim (`LANDED`/`EXEMPT`), not an assertion of confidence. A reviewer can `grep` the live log and the retrofit ledger and get an exact accounting of how many RESOLVED gaps rest on a real check versus a stated exemption, the same way GG-144's fix made the OPEN count exact.
- Some gaps will sit at `PENDING` for longer than they would have sat at `RESOLVED` under the old rule — this is the intended effect, not a cost to be minimized. GG-164/GG-166 are the direct example: marking them RESOLVED on the code fix alone (as the old rule would have permitted) is exactly the failure this ADR exists to prevent.
- G6 gains one more concrete, justified precondition (§2.3) instead of leaving ledger-quality assumed by omission.
- Slightly more governance surface area (a new linked file, a third header field) — an accepted, disclosed tradeoff, consistent with ADR-0044's own acceptance of "slightly more files to navigate" for the same kind of gain.

## 6. Validation

- Confirmed ADR-0007's text directly (re-read in full this session) before drafting the supersession language in §2.1 — the RESOLVED-marking criterion being superseded was, in fact, entirely absent from ADR-0007's original text (it mandated the log's *existence* and structure, not a bar for the RESOLVED transition specifically), so this ADR adds a new criterion rather than literally contradicting stated text; framed as "Supersedes" rather than "Amends" because it changes the operative meaning of marking a gap RESOLVED under the artifact ADR-0007 created.
- Confirmed ADR-0028's exact "Updated G6 Closure Condition" 6-item list (re-read in full this session) before drafting §2.3's item 7, to ensure the new item is additive and does not renumber or restate items 1–6.
- Confirmed GG-149's T-432 baseline finding (17/151 legacy both-direction-OPEN violations, explicitly pre-epoch-12) directly from `ACTIVE_QUEUE.md` before citing it in §3, rather than from memory — the finding supports `PENDING`, not `EXEMPT`, since a standing assertion clearly *can* apply to GG-149's defect class (T-432 already ran one).

## DS Sign-off

Pending. Recorded here (not fabricated) — this ADR is `PROPOSED` until Earl Ignacio signs off in a future session or turn.
