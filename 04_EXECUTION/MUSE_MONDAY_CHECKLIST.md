# Muse Monday checklist — run in full BEFORE writing Earl's message (one message, not a drip)

**Why (W65, 2026-11-23):** Earl had to ask four times ("IS THERE ANYTHING ELSE WE CAN DO WHILE WE STILL HAVE USAGE ON MUSE??") before
the window found the claim-order, late-tip, Thanksgiving-slate, source-failure and repo-size issues. Earl can talk to Muse only on
Mondays; anything not in that message waits a week. The window answered "is the reported problem fixed?" instead of "what can break
or be worth more before next Monday?". This list is the second question, asked once, up front.

Read live (scripts/muse_check.py first; then STATUS.md tail, "For Earl's Monday message", QUEUE.md, CLAIMS.md, L3-snapshots):

1. **Supply:** unclaimed vs the 500 floor; days of work at the current pace; which families are queued; does any rule let it run dry.
2. **Open rulings:** every item under "For Earl's Monday message" gets a ruling in the message. None carried over.
3. **Value order:** which queued families unblock a bot test or a parked hypothesis THIS week (check the backlog NOW lane and
   HYPOTHESIS_DOCTRINE COLLECTING / UNDERPOWERED rows); put them first in the claim order.
4. **The calendar:** the coming week's slates per league (holidays, Thursday / Friday NFL, dark days, international games, season
   starts / ends). Every snapshot type knows its game days and writes NO SLATE on dark days.
5. **Snapshot timing vs data:** read one day's snapshot files; does the last snapshot land after the last game's lineup / goalie can be
   confirmed? Coverage of confirmed rows per game.
6. **Source risk:** any source that failed or changed since last Monday (Cloudflare, parked, layout); the fallback rule (two tries,
   BLOCKED, skip, file) is in force.
7. **Capacity:** archive repo size and growth per week vs 4 GB; largest file vs 50 MB.
8. **Usage pressure:** perishable snapshots first if usage runs short.
9. **Monitoring:** the nightly check ran clean last night (list_triggers last_run); HEARTBEAT lines present.
10. **Bot side:** does the bot have an intake path for every new family Muse is writing? If not, register the task.

Write ONE message covering every item that needs Muse to act. Then tell Earl what was checked and what was not.
