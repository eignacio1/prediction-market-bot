# /bro — Plain-English Translation

**Trigger:** User types `/bro` (optionally followed by a specific thing to focus on, e.g. `/bro just the risk part`).

## What this does

Takes whatever you (Claude) just said in your immediately preceding message — or, if the user points `/bro` at something else ("bro that file", "bro what the last agent said"), takes that instead — and re-says it in plain, ordinary English. The goal is a normal person with zero background in the subject matter walks away knowing what actually matters, with nothing lost in translation.

**This is a compression exercise, not just a jargon swap.** Plain English should almost always come out *shorter* than the jargon-laden original, not longer — most technical/corporate phrasing is already padded, and stripping it tends to save words, not cost them. Don't burn tokens re-explaining a dropped term from three different angles or restating the same point twice in different words. The floor is clarity: never cut a distinct fact, number, or piece of bad news to hit a length target. But above that floor, every extra sentence needs to earn its place — if a plain-English pass costs *more* tokens than the original, something went wrong (over-explaining, hedging, or narrating the translation instead of just doing it).

## Rules for the rewrite

1. **Lead with the bottom line.** First sentence: what happened / what's true / what to do. Not throat-clearing, not "so basically what's going on is."
2. **Kill jargon, corporate-speak, and structural scaffolding.** No ticket/ticket-like codes (GG-004, T-235, ADR-0040, APR-0024...), no acronyms without immediately saying what they mean in normal words, no phrases like "leverage," "surface," "align on," "the ask," "actionable," "gate," "governance," "artifact" (in the business-jargon sense), "stakeholder." If a technical term is load-bearing (can't be cut without losing the point), keep the concept but explain it the way you'd explain it to a smart friend who doesn't work in this field — not the way you'd write it in a doc.
3. **Kill headers, tables, and bullet-nesting theater.** A person reads this in one pass, top to bottom, like a text message from a friend, not a report. Short paragraphs or a flat list, not a structured document. No bolded section labels unless there are genuinely multiple distinct things to say.
4. **Say what changed and what it means for the user, not the mechanism.** "The number that decides how much data we need went up" beats "the variance-derived n* threshold was recalculated." Prefer consequences over process: what should the user do, worry about, or expect next — not how the sausage got made, unless the how is the actual point.
5. **Don't hedge for hedging's sake.** If something is uncertain, say so once, plainly ("this isn't confirmed yet, might change"). Don't stack qualifiers.
6. **Keep the honesty.** Plain English is not an excuse to round off a "no" into a maybe, or a real risk into a shrug. If the original message had a warning, a blocker, or bad news in it, that has to survive the translation just as bluntly — plain-spoken bad news is still bad news.
7. **Numbers stay, just contextualized.** Don't drop figures (money, percentages, dates) — just say what they mean in a sentence a non-specialist would parse instantly.
8. **Length matches the source's actual content, not its wordiness.** If the original was ten paragraphs of dense process language that boiled down to one real fact, give one real fact. If the original had five genuinely distinct things going on, give five plain-English things — don't force it down to one bullet just to seem punchy.

## Output

Just the plain-English version. No preamble like "Here's that in plain English:" — start directly with the translation. No closing meta-commentary about the translation itself.
