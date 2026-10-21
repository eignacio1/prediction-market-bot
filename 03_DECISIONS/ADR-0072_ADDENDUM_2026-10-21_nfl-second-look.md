# ADR-0072 Addendum — 2026-10-21 — NFL: one more pre-registered look after an INCONCLUSIVE read

**Status:** ACCEPTED (operator decision, before any further NFL data was read). Amends nothing in the accepted ADR-0072 text or
the 2026-10-20 addendum (Hard Rule 3); it fills a gap: the pre-registration does not say what happens after a cell reads
INCONCLUSIVE at judged n.
**Decisions logged:** true

## Authorization
> **AUTHORIZATION - ADR-0072 NFL SECOND LOOK (operator, 2026-10-20 ~23:05 PT, asked by the strategic window: "Keep running, one
> more look (Recommended)").** The forward test keeps running for NFL; one more pre-registered NFL read is taken when criterion
> (c) has markout-bearing fills at judged n (~550 per arm) on both arms. Nothing else changes.

## What was read (W82.2, 2026-10-21T04:59Z, post-top-up, per book and sport)
NFL: 3,085 control / 878 treatment fills over 13 games; treatment minus control mean settle-minus-price +0.153 (se 0.123),
one-sided 95% game-clustered lower bound −0.050; (b) fill-rate ratio 0.288 (holds); (c) NOT_EVALUABLE (0 markouts; collection
began 2026-10-21T04:30Z). Read: INCONCLUSIVE at judged n (not adopted, not rejected).

## The rule from here
1. The test keeps running unchanged (seed, share, judged n, placement rule, switches, the 2026-10-20 decisions).
2. **One more NFL look**, taken once each arm has ≥ 550 post-top-up fills that carry a 30-minute markout (the (c) epoch). At that
   look, (a), (b) and (c) are all judged on the fills available then, under the 2026-10-20 addendum's methods, and the verdict
   word is final for NFL: ADOPT / "removed fills, not adverse selection" / REJECT / INCONCLUSIVE.
3. Between now and that look, NFL numbers are descriptive only. Nobody reads (a) for NFL early.
4. NHL, NBA and MLB are unchanged: each gets its first verdict at its own judged n.
