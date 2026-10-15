# /vision — read the operator's vision back to him

When the operator asks for the vision, the scale, the bar, or "what are we building" — or types /vision:

1. Read `CLAUDE.md` § "What winning looks like" (north star, four pillars, distance measures) and § "The scale — one deep engine per sport", then `03_DECISIONS/ADR-0073_sport-engine-doctrine.md` and `03_DECISIONS/ADR-0075_betting-architecture-doctrine.md` (what edge means: aggregation > interpretation > application, the eight components).
2. Read the DISTANCE TO OPTIMUM table at the top of `04_EXECUTION/ACTIVE_QUEUE.md` for where the project stands now (dated values only).
3. Answer in plain words, short, in this order:
   - **What winning looks like** — the bot at optimum: every live sport's whole board, every band, every cell's edge found or ruled out; accumulation ("picking up every damn cent that falls along the way").
   - **The scale** — one deep engine per sport at Syndicate32-level granularity or deeper, pricing the whole board from one simulation; the data layer is the work; free sources first.
   - **What edge means** — the betting architecture at play-level granularity: data aggregation > data interpretation > data application, application ("cool info, so what?") the hardest and never finished; the eight components (ADR-0075 § 2), structural tensions = "where the architecture strains", seat interface = "deep mapping of sports-eyes to cells"; PAM into every engine, NFL and NBA first, deep tier built with the operator.
   - **The operator's own words** — quote him from ADR-0073's and ADR-0075's Context sections. Quote, never compress (window error W16).
   - **Where we are against it** — D1–D5 and the other pillars from the sitrep, each with its date and source.
   - **The next move toward it** — the current wave's DEPTH lane, or say plainly that there isn't one.
4. Do not soften the gap and do not re-explain that the model has not beaten the market unless he asks.
