# Operator Digest — 2026-09-25

**T-573 (cohort verification):** ran the check on whether the bot has scorable evidence its model beats the market. Answer: no, not right now. Of the 765 "clean" bets in the ledger, 731 (95.6%) can't be confirmed as real fills at Kalshi — and more than half of those (395) turned out to carry duplicated/fabricated order IDs, a genuine bug in how bets get written to the ledger (GG-303, logged as HIGH priority, not yet fixed). The 34 bets that ARE confirmed real aren't a fair sample either — they cluster on one date and skew toward different prices/sizes than the unconfirmed ones, so they can't be used to answer the question either.

**Bottom line:** neither the old "it's working" number nor the newer "it's losing" number can be trusted as the real answer. Fixing this requires repairing the ledger-write bug first, then re-running the analysis on a clean, representative sample. Nothing was changed in the trading system itself this session — this was read-only diagnosis.

**Also fixed:** a git merge conflict blocked PR #150 (this session's work) from landing on main — resolved and merged (commit `1da5865`).
- T-577 (auto): T-577 cohort salvage pre-registered analysis complete -- UNRECOVERABLE verdict, only n=35 CONFIRMED-REAL is usable.
