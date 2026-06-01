# Mid-Session Checkpoint — YYYY-MM-DDTHH:MMZ

**Trigger:** [Block completed: PDTP review / governance sprint / implementation sprint / experiment / gate close / category switch / 30-tool-call failsafe]
**Approximate context state:** [early ~20% / mid ~40% / late ~60% / critical ~80%+]

---

## Block Completed

[1-2 sentences on what was finished. Be specific — file names, task IDs, test count before → after, decision names.]

---

## Decisions Made This Block

| Decision | Rationale | DECISION_LOG entry | Owner |
|----------|-----------|-------------------|-------|
| [what was decided] | [why — constraint, deadline, or evidence] | [row ID or "none needed"] | DS |

*If none: "None — implementation-only block."*

---

## Governance State

```bash
grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/ 2>/dev/null
```

Result: [clean — no matches / N files with debt: list them and their T-NNN tasks]

---

## Next Block

**Block type:** [e.g., arb strategy review / implementation sprint / research experiment / governance]
**First action:** [exact task ID or: "Read [filename] to..."]
**Operator dependency:** [none / waiting on: describe]
