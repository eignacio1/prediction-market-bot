# PAM Deep Tier: PROPOSED working method

**Status:** PROPOSAL, not adopted. Written W75.1 2026-10-14. Nothing here is built.

**OPERATOR ANSWER, 2026-10-15 16:46 PT (window recorded):** "No - deep PAM tier needs to be substantially deeper than that, even
foundationally. I want RB's, TEs, OL, and core defenders in that tier. We don't need to get to that anytime soon anyway."
→ The ~100-player QB + top-2 WR start below is **rejected**. The deep tier, even at its foundation, covers QBs, WRs, **RBs, TEs,
OL and core defenders**. Not scheduled soon; the mass tier and the core come first. The layers and supersession rules below are
unchanged; the "who qualifies" paragraph is superseded by this scope.

> Operator, 2026-10-14: "the deep PAM tier will be a multi layer effort between me and you (Claude). right now - we just need to get the ball rolling on at least building it out foundationally."

**Who qualifies.** A player is deep-tier when a model's price depends materially on the label *and* the mass label is weak or contested: starters whose mass weights are near-ties (top weight < 0.6), role changes (trade, injury return, scheme change), and the few players a market is built on (QBs, the top WR/RB/EDGE per team). Target set is small and named, not "everyone"; start with one sport (NBA already has 50 deep records) and the team-prop-relevant NFL players.

**Layers.** (1) *Mass baseline*: the rule/model record, always present as the floor. (2) *Claude evidence pass*: for each qualifying player, assemble the data the mass rule cannot see (film notes already published, usage changes, coach statements, injury context) as dated, cited evidence per archetype and modifier, with a proposed hybrid and confidence. (3) *Operator judgment pass*: the operator accepts, edits or rejects each proposed record; the operator's call is the record. (4) *Review on trigger*: re-open on role change or a stability break (mass label flips between seasons), not on a calendar.

**How a deep record supersedes a mass one.** Deep records are written through the same store with `tier = "deep"`, `classified_by.kind = "human"`, `supersedes = [mass record id]`, their own `effective_from`, and evidence on every modifier. `pam_as_of` already prefers a deep record on a tie and drops the superseded mass record from the deep record's effective date, so earlier dates keep reading the mass label. The mass record is never edited. If the deep record ends, the mass record is not resurrected automatically (a new mass record or a deep record must cover the period).

**Guardrails.** Evidence and judgment are separated in the record (`basis.text` vs `notes`); no deep label may use data after its `effective_from` unless `backdated` with a rationale; a deep label is *aggregated* until an engine uses it with a pre-registered measure.

**Open question for the operator (one line):** do you want the deep tier to start with the NFL starting QBs and top-2 WRs per team (about 100 players), reviewed by you in batches of 10 per sitting?
