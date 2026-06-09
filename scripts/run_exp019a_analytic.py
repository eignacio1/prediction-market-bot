"""
EXP-019A Analytic Derivation — NOISE_BUFFER_BAND per execution band
ADR-0018 Section 2 methodology

Exit signal: mip_current > p_current + NOISE_BUFFER_BAND
NOISE_BUFFER_BAND = max(2 * sigma_p, EXIT_NET_COST)

sigma_p = |dP/dlambda| * sigma_lambda
        = P(X = k-1 | Poisson(lambda)) * sigma_lambda    [Poisson CDF derivative identity]

Evaluated at the decision boundary: k = floor(lambda) + 1
This is where the PMF is maximized (steepest gradient in P vs lambda),
i.e., the highest-noise scenario for any exit signal evaluation.

No external dependencies. Run with: python3 scripts/run_exp019a_analytic.py
"""

import math
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Poisson PMF and CDF (pure Python, same implementation as game_state_model.py)
# ---------------------------------------------------------------------------

def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k | Poisson(lambda))"""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    if k < 0:
        return 0.0
    # Use log-space to avoid overflow
    log_p = -lam + k * math.log(lam) - math.lgamma(k + 1)
    return math.exp(log_p)


def poisson_cdf_ge(k: int, lam: float) -> float:
    """P(X >= k | Poisson(lambda))"""
    if lam <= 0:
        return 0.0 if k > 0 else 1.0
    # Sum P(X = i) for i = 0..k-1, subtract from 1
    cumulative = 0.0
    for i in range(k):
        cumulative += poisson_pmf(i, lam)
    return max(0.0, 1.0 - cumulative)


# ---------------------------------------------------------------------------
# Band input parameters
# ---------------------------------------------------------------------------

class BandParams(NamedTuple):
    name: str
    kelly_fraction: float       # from ADR-0010
    sigma_lambda: float         # uncertainty in lambda_remaining (pts expected remaining)
    lambda_rep: float           # representative lambda_remaining at exit window
    k_rep: int                  # k_needed at decision boundary = floor(lambda_rep) + 1
    time_remaining_min: float   # representative time remaining in minutes
    sigma_lambda_derivation: str  # how sigma_lambda was derived


# ---------------------------------------------------------------------------
# sigma_lambda derivation
# ---------------------------------------------------------------------------
# T4 baseline: sigma_lambda = 0.5 at Q3/Q4 ~18 min remaining (ADR-0010 established)
# T5: sigma_lambda_T5 = sigma_lambda_T4 * sqrt(t_remaining_T5 / t_remaining_T4)
#     = 0.5 * sqrt(2 / 18) = 0.5 * 0.333 = 0.167
# T1/T2/T3 in-game: these positions are evaluated by T4 cycle during the game.
#   At Q2 mid (~30 min remaining), fewer game-state observations → higher sigma_lambda.
#   Upper bound: proportional to T4 estimate by time ratio
#     = 0.5 * sqrt(30 / 18) = 0.5 * 1.291 = 0.645
#   Lower bound: pure temporal scaling from pre-game prior
#     sigma_lambda_pregame = 2.055 (ADR-0010), scaled by sqrt(t_remaining/48):
#     = 2.055 * sqrt(30/48) = 2.055 * 0.791 = 1.625
#   The in-game Bayesian update reduces this. At Q2 mid with 18 min of game data,
#   the posterior is between the two bounds. Use geometric mean as a conservative estimate:
#     sigma_lambda_T1_ingame = sqrt(0.645 * 1.625) = sqrt(1.048) = 1.024
#   Round to 1.0 for clean presentation; flag as requiring EXP-019A empirical validation.
#
# Representative player: pts_l10_mean = 22 pts/game, adj_pace = 22/48 = 0.458 pts/min
# At each window, lambda_rep = adj_pace * time_remaining_min

ADJ_PACE = 22.0 / 48.0  # pts/min for representative player (22 pts/game)
SIGMA_LAMBDA_T4 = 0.5   # established ADR-0010
T_REMAINING_T4 = 18.0   # Q3/Q4 midpoint
T_REMAINING_T5 = 2.0    # final 2 min (T5 window representative)
T_REMAINING_T123 = 30.0 # Q2 mid (T1/T2/T3 evaluated by T4 cycle)

SIGMA_LAMBDA_T5 = SIGMA_LAMBDA_T4 * math.sqrt(T_REMAINING_T5 / T_REMAINING_T4)
SIGMA_LAMBDA_T123 = math.sqrt(
    (SIGMA_LAMBDA_T4 * math.sqrt(T_REMAINING_T123 / T_REMAINING_T4)) *
    (2.055 * math.sqrt(T_REMAINING_T123 / 48.0))
)  # geometric mean of lower and upper bounds

def lambda_rep(t_remaining: float) -> float:
    return ADJ_PACE * t_remaining

def k_rep(lam: float) -> int:
    return math.floor(lam) + 1


BANDS = [
    BandParams(
        name="T1",
        kelly_fraction=0.10,
        sigma_lambda=SIGMA_LAMBDA_T123,
        lambda_rep=lambda_rep(T_REMAINING_T123),
        k_rep=k_rep(lambda_rep(T_REMAINING_T123)),
        time_remaining_min=T_REMAINING_T123,
        sigma_lambda_derivation=(
            f"Geometric mean of T4-extrapolated upper bound "
            f"({SIGMA_LAMBDA_T4 * math.sqrt(T_REMAINING_T123 / T_REMAINING_T4):.3f}) "
            f"and pre-game-prior lower bound "
            f"({2.055 * math.sqrt(T_REMAINING_T123 / 48.0):.3f}); "
            f"requires EXP-019A empirical validation"
        ),
    ),
    BandParams(
        name="T2",
        kelly_fraction=0.13,
        sigma_lambda=SIGMA_LAMBDA_T123,
        lambda_rep=lambda_rep(T_REMAINING_T123),
        k_rep=k_rep(lambda_rep(T_REMAINING_T123)),
        time_remaining_min=T_REMAINING_T123,
        sigma_lambda_derivation="Same as T1 (injury overlay does not change pace uncertainty structure; EXP-019A validation required)",
    ),
    BandParams(
        name="T3",
        kelly_fraction=0.07,
        sigma_lambda=SIGMA_LAMBDA_T123,
        lambda_rep=lambda_rep(T_REMAINING_T123),
        k_rep=k_rep(lambda_rep(T_REMAINING_T123)),
        time_remaining_min=T_REMAINING_T123,
        sigma_lambda_derivation="Same as T1 (T3 pre-tip signal is historical at exit time; EXP-019A validation required)",
    ),
    BandParams(
        name="T4",
        kelly_fraction=0.20,
        sigma_lambda=SIGMA_LAMBDA_T4,
        lambda_rep=lambda_rep(T_REMAINING_T4),
        k_rep=k_rep(lambda_rep(T_REMAINING_T4)),
        time_remaining_min=T_REMAINING_T4,
        sigma_lambda_derivation="0.500 — established ADR-0010; in-game Bayesian posterior with 24-30 min observation",
    ),
    BandParams(
        name="T5",
        kelly_fraction=0.25,
        sigma_lambda=SIGMA_LAMBDA_T5,
        lambda_rep=lambda_rep(T_REMAINING_T5),
        k_rep=k_rep(lambda_rep(T_REMAINING_T5)),
        time_remaining_min=T_REMAINING_T5,
        sigma_lambda_derivation=(
            f"T4 σ_λ × √(t_T5/t_T4) = 0.500 × √({T_REMAINING_T5}/{T_REMAINING_T4}) "
            f"= 0.500 × {math.sqrt(T_REMAINING_T5 / T_REMAINING_T4):.4f} = {SIGMA_LAMBDA_T5:.4f}"
        ),
    ),
]


# ---------------------------------------------------------------------------
# Cost floor (taker fee only, at mip=0.50 worst case)
# Spread component requires EXP-019C — excluded from this analytic phase.
# NOISE_BUFFER must be >= EXIT_NET_COST = taker_fee + spread_cost.
# We compute the taker-fee floor only here; spread_cost pushes buffer higher.
# ---------------------------------------------------------------------------

def taker_fee(mip: float) -> float:
    return 0.07 * mip * (1.0 - mip)

EXIT_NET_COST_FLOOR = taker_fee(0.50)  # worst-case mip for fee (mip=0.50 maximizes fee)


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------

class BandResult(NamedTuple):
    band: str
    kelly_fraction: float
    sigma_lambda: float
    lambda_rep: float
    k_rep: int
    pmf_at_boundary: float   # P(X = k-1 | Poisson(lambda)) = dP/dlambda
    sigma_p: float           # sigma_p = pmf * sigma_lambda
    two_sigma_p: float       # statistical noise floor
    exit_net_cost_floor: float  # taker fee floor (spread excluded)
    noise_buffer: float      # max(2*sigma_p, exit_net_cost_floor)
    binding_constraint: str  # which term drove the buffer
    p_current_at_boundary: float  # P(X >= k | Poisson(lambda)) for context


results = []
for band in BANDS:
    lam = band.lambda_rep
    k = band.k_rep
    pmf = poisson_pmf(k - 1, lam)       # dP/dlambda at (lambda, k)
    sigma_p = pmf * band.sigma_lambda
    two_sigma_p = 2.0 * sigma_p
    p_at_boundary = poisson_cdf_ge(k, lam)  # p_current at boundary
    noise_buffer = max(two_sigma_p, EXIT_NET_COST_FLOOR)
    binding = "statistical (2σ_p)" if two_sigma_p >= EXIT_NET_COST_FLOOR else "economic (taker fee)"
    results.append(BandResult(
        band=band.name,
        kelly_fraction=band.kelly_fraction,
        sigma_lambda=band.sigma_lambda,
        lambda_rep=lam,
        k_rep=k,
        pmf_at_boundary=pmf,
        sigma_p=sigma_p,
        two_sigma_p=two_sigma_p,
        exit_net_cost_floor=EXIT_NET_COST_FLOOR,
        noise_buffer=noise_buffer,
        binding_constraint=binding,
        p_current_at_boundary=p_at_boundary,
    ))


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

print("=" * 80)
print("EXP-019A — NOISE_BUFFER_BAND Analytic Derivation")
print("ADR-0018 Section 2 Methodology")
print(f"Representative player: pts_l10_mean=22, adj_pace={ADJ_PACE:.4f} pts/min")
print(f"Decision boundary: k = floor(λ) + 1  (maximum PMF / maximum signal sensitivity)")
print(f"EXIT_NET_COST_FLOOR = taker_fee(mip=0.50) = {EXIT_NET_COST_FLOOR:.4f}  (spread excluded — EXP-019C required)")
print("=" * 80)

print()
print(f"{'σ_λ derivation chain':}")
print("-" * 80)
for i, band in enumerate(BANDS):
    print(f"  {band.name}: σ_λ = {band.sigma_lambda:.4f}")
    for line in band.sigma_lambda_derivation.split("; "):
        print(f"       {line}")
print()

print("PRIMARY RESULTS TABLE")
print("-" * 80)
header = (
    f"{'Band':<5} {'Kelly':>7} {'σ_λ':>7} {'λ_rep':>7} {'k':>4} "
    f"{'PMF(k-1)':>10} {'σ_p':>8} {'2σ_p':>8} {'fee_floor':>10} "
    f"{'BUFFER':>8} {'p@boundary':>12} {'Binding':>20}"
)
print(header)
print("-" * 80)
for r in results:
    print(
        f"{r.band:<5} {r.kelly_fraction:>7.2f} {r.sigma_lambda:>7.4f} "
        f"{r.lambda_rep:>7.3f} {r.k_rep:>4d} "
        f"{r.pmf_at_boundary:>10.5f} {r.sigma_p:>8.5f} {r.two_sigma_p:>8.5f} "
        f"{r.exit_net_cost_floor:>10.5f} {r.noise_buffer:>8.5f} "
        f"{r.p_current_at_boundary:>12.5f} {r.binding_constraint:>20}"
    )
print("-" * 80)
print()

print("DERIVATION CHAIN PER BAND")
print("-" * 80)
for i, (band, r) in enumerate(zip(BANDS, results)):
    print(f"\n[{band.name}]  Kelly={band.kelly_fraction}  Window={band.time_remaining_min:.0f} min remaining")
    print(f"  σ_λ = {band.sigma_lambda:.4f}")
    print(f"  λ_rep = adj_pace × t_remaining = {ADJ_PACE:.4f} × {band.time_remaining_min:.0f} = {r.lambda_rep:.3f} pts")
    print(f"  k_rep = floor(λ_rep) + 1 = floor({r.lambda_rep:.3f}) + 1 = {r.k_rep}")
    print(f"  p_current at boundary = P(X ≥ {r.k_rep} | Poisson({r.lambda_rep:.3f})) = {r.p_current_at_boundary:.5f}")
    print(f"  dP/dλ = P(X = {r.k_rep-1} | Poisson({r.lambda_rep:.3f})) = {r.pmf_at_boundary:.5f}")
    print(f"  σ_p = dP/dλ × σ_λ = {r.pmf_at_boundary:.5f} × {r.sigma_lambda:.4f} = {r.sigma_p:.5f}")
    print(f"  2σ_p = {r.two_sigma_p:.5f}  ← statistical noise floor")
    print(f"  EXIT_NET_COST_FLOOR (taker fee only) = {r.exit_net_cost_floor:.5f}")
    print(f"  NOISE_BUFFER_{band.name} = max({r.two_sigma_p:.5f}, {r.exit_net_cost_floor:.5f}) = {r.noise_buffer:.5f}")
    print(f"  Binding constraint: {r.binding_constraint}")

print()
print("=" * 80)
print("CANDIDATE NOISE_BUFFER_BAND VALUES (pending EXP-019A empirical validation)")
print("-" * 80)
for r in results:
    print(f"  NOISE_BUFFER_{r.band} = {r.noise_buffer:.5f}  ({r.binding_constraint})")
print()

print("IMPORTANT CAVEATS")
print("-" * 80)
print("  1. T1/T2/T3 σ_λ values use geometric mean of two bounds; EXP-019A empirical")
print("     validation against observed p_current variance is REQUIRED before activation.")
print()
print("  2. EXIT_NET_COST_FLOOR = taker fee only. Actual EXIT_NET_COST includes")
print("     spread_cost_band(t_remaining). EXP-019C will add this component.")
print("     Final NOISE_BUFFER >= these values (spread cost only raises the floor).")
print()
print("  3. Representative player: 22 pts/game, adj_pace=0.458 pts/min.")
print("     Buffer is HIGHER for lower-scoring players (smaller λ → higher PMF at boundary).")
print("     Buffer is LOWER for higher-scoring players (larger λ → lower PMF at boundary).")
print("     Per-player adjustment: use actual adj_λ in production evaluate_exit(), not the")
print("     band-level constant. The band constant is the empirically-validated typical-case")
print("     noise floor — not a per-evaluation oracle.")
print()
print("  4. Decision boundary (k = floor(λ)+1) is the WORST CASE for noise (max PMF).")
print("     At strongly out-of-pace scenarios (k >> λ), PMF is much smaller → σ_p smaller")
print("     → less noise → buffer is conservative (safely over-specified). This is correct")
print("     design: if the player is badly behind pace, the exit signal is CLEANER, not noisier.")
print()
print("  5. T5 band: T5 positions typically exit via near-certain arithmetic gate, not")
print("     Poisson CDF reversal. The buffer computed here governs the unusual case where")
print("     a T5 YES position needs to be exited after a score-state reversal in final 2 min.")
print()
print("  6. Acceptance criteria for EXP-019A empirical validation (per ADR-0018):")
print("     Exit-at-signal outperforms hold-to-expiry in ≥60% of signal-fire events;")
print("     false exit rate (exit fires but hold was correct) ≤ 40%.")
print("=" * 80)
