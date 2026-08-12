# Operator Digest — 2026-08-11

**What changed today, in one paragraph:**
Today's session added a rule that has been missing: from now on, an internal issue tracker entry can only be marked "fixed" if there's an actual automated check that would catch it happening again — or an explicit note saying why no such check is possible. This was prompted by comparing two past issues: one that stayed fixed because the fix was code, and one that came back within a day because the fix was only a written note. The written note turned out to be wrong, and nothing caught that until real trading data got corrupted by it.

**What this means for your money:**
No change today — still zero real money at risk. But this closes a real gap in how the safety net around the money-tracking ledger gets verified: the rule now also says the system can't go live until its data-integrity checks have run clean for a while, not just once. That's a stricter bar than existed before.

**Does anything need your decision right now?**
The new rule (a formal governance document) is written but not yet formally signed off — that sign-off is a "when convenient" item, not urgent. No trading logic or money-handling code was touched today.

**Anything that worried the session, even if not urgent:**
One thing: the automated check that would let the two issues above graduate from "flagged" to "fully resolved" is being built by a separate, parallel work session and isn't finished yet — so today's fix sets up the rule correctly but the actual safety check it depends on is still pending.

---

## T-436 — Phase 1 depth verdict, "Good to unblock"

**What changed today, in one paragraph:**
You asked for a fresh check of how deep the order books actually are on the six market types the bot trades — deep enough that a bet could actually get filled at a fair price, not just theoretically available. Four of six passed comfortably (game totals, game winner, run line, team total). Two (partial-game winner, player props) came in thin — well under the floor — but per your standing instruction, thin isn't the same as dead, so neither gets shut off. Along the way I found a contradiction in the internal planning notes: one document said the next phase of work stays blocked on an unrelated cleanup task regardless of what the depth check found. I flagged it rather than deciding it myself, and you said "Good to unblock" — so that phase of work (fixing some structural rough edges, not adding new markets) can now start.

**What this means for your money:**
No change today — still zero real money at risk. No bets were placed or resized. This was a measurement-and-paperwork session.

**Does anything need your decision right now?**
No — the one decision that needed you (whether the next phase should wait on that unrelated cleanup task) was already made in-session when you said "Good to unblock." Nothing else pending.

**Anything that worried the session, even if not urgent:**
The two thin-depth market types (partial-game winner, player props) are worth revisiting once there's fresh depth data — a FAIL today doesn't mean permanently unusable, but it also isn't something to forget about.

---

## T-432 — Ledger invariant suite (data "smoke alarm")

**What changed today, in one paragraph:**
This is the direct fix for the incident where a bad date field silently corrupted about 44% of a batch of resolved bets, and nobody caught it for four separate work sessions because nothing actually checked whether the numbers in the ledger were *correct* — only that the process that writes them had run. Today's session built that missing check: a script that reads the ledger and independently verifies about a dozen things that should always be true (prices between 0 and 1, profit/loss sign matching win/loss, no position open in both directions on the same bet, etc.), and cross-checks resolved bets against a second, independently-built record of what actually happened in each game. Two of the checks you originally specified turned out to be slightly wrong as written — they would have falsely flagged good data as bad — so those two were corrected before being built, with the reasoning written down.

**What this means for your money:**
No change today — still zero real money at risk. This is a smoke alarm, not a fix: it's explicitly built to only warn, never to stop or block anything, per your instruction. It ran once and confirmed the earlier corruption issue is still only partially resolved (a related, already-known data problem is still live and being worked separately) — that's not a new problem, just confirmation the old one isn't fully closed yet.

**Does anything need your decision right now?**
No — nothing needs you today. The smoke alarm runs quietly in the background from now on. There's a written proposal for a future stricter mode, where it could actually block something instead of just warning — but that's not built, and it's explicitly your call whenever you want to consider it, not urgent.

**Anything that worried the session, even if not urgent:**
One small, isolated oddity turned up: one bet's ticker ID appears to be missing a letter, so it doesn't cleanly match the player's name. It's a single occurrence, doesn't look like it caused any actual harm, and has been noted for whoever next works on how those IDs get generated.

---
