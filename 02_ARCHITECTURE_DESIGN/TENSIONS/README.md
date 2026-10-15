# Structural tension registers (ADR-0075)

One register per engine (`nfl.toml`, `nba.toml`), rendered to `NFL_TENSIONS.md` / `NBA_TENSIONS.md` by `scripts/render_tensions.py`. A tension is a place where the architecture strains against the evidence; it is a standing question, not a defect ticket.

## Schema (`[[tension]]`)
- `id` — `NFL-T1`, `NBA-T1`, ... stable, never reused.
- `title` — one line.
- `where` — the component / file / cell the strain sits in.
- `evidence` — repo path(s) that exist on main (tests enforce this); gap ids (GG-NNN) may be cited in the text.
- `pillar` — the pillar it hurts (BREADTH / DEPTH / EXECUTION / PROOF).
- `relief` — what would relieve it. Not a commitment to do it.
- `status` — `open` or `relieved` (a relieved tension keeps its row, with the relieving evidence).

## Review rule
At every wave close, the strategic window reviews each engine's register (step in `.claude/commands/strategic-handoff.md`): add tensions the wave exposed, mark relieved ones with evidence, and flag any tension whose relief has been deferred across two waves. Tensions that need an ADR-0075 definition changed are brought to the operator, not decided in-session.

## Regenerate
`python3.11 scripts/render_tensions.py` — `tests/test_tensions.py` fails if a render is stale.
