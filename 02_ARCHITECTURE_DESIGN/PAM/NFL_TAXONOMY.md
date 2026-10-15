# NFL PAM Taxonomy (draft v1)

**Status:** W75.1 Part B, 2026-10-14. Stage: **aggregated** (design plus one built group, WR). Free data only (ADR-0073 point 4): an archetype that needs a non-free source is a GAP (GG), never bought. Sources are the free nflverse event store (`02_ARCHITECTURE_DESIGN/NFL_ENGINE/DATA_LAYER.md`): **pbp**, **part** (participation: route on the targeted play, coverage type, pressure, personnel), **FTN** (2022+ charting), **snaps**, **PFR** (`pfr_pass/rush/rec/def`), **ros** (rosters, ids). Status: **FREE** = computable now; **PART** = approximate from free data, named limit; **GAP** = needs a non-free source.

Archetype ids are `<GROUP>-<CODE>`. Archetypes are weighted hybrids (CORE_SCHEMA). Thresholds for built groups live in `qualitative_data/pam/nfl/taxonomy.json`; unbuilt groups are definitions only.

## QB
| Archetype | Signals | Source | Status |
|---|---|---|---|
| QB-PKT Pocket Distributor | dropback depth/time to throw, low out-of-pocket rate, short-mid air yards | part `time_to_throw`, FTN `is_qb_out_of_pocket`, pbp `air_yards` | FREE |
| QB-MOB Mobile Creator | scramble/designed-run rate, rush EPA, out-of-pocket rate | pbp rush by QB, FTN `is_qb_out_of_pocket` | FREE |
| QB-DEEP Downfield Gunslinger | aDOT, deep-attempt rate, interception-worthy rate | pbp, FTN `is_interception_worthy` | FREE |
| QB-PA System/Play-Action Manager | play-action share, screen/RPO share, EPA gap vs no-PA | FTN `is_play_action/is_screen_pass/is_rpo` | FREE |
| QB-PRS Pressure Resister | EPA and sack rate under pressure | part `was_pressure`, pbp | PART (2026 participation absent, GG-730) |

## RB
| Archetype | Signals | Source | Status |
|---|---|---|---|
| RB-WK Workhorse | carry share, snap share, goal-line share | pbp, snaps | FREE |
| RB-EXP Explosive Runner | rush explosive-rate (10+), broken tackles per carry | pbp, PFR rush | FREE |
| RB-REC Receiving Back | target share, routes (swing/screen) share, snap share on pass downs | pbp, part route, snaps | PART (routes only on targets, GG-775) |
| RB-CHG Change-of-Pace/Committee | low snap share, split carries with a primary back | snaps, pbp | FREE |

## WR  (built: mass tier, see Part B result)
| Archetype | Signals | Source | Status |
|---|---|---|---|
| WR-VERT Vertical Stretcher | aDOT, deep-target rate (air yards 20+), deep-route share of targets | pbp, part route | FREE |
| WR-YAC YAC / Short-Game Weapon | YAC per reception, short-target rate (air yards <= 3), screen/swing share | pbp, FTN | FREE |
| WR-VOL Volume Target Earner | team target share | pbp | FREE |
| WR-MID Intermediate Chain-Mover | aDOT near 10, in/dig/out/cross route share | pbp, part route | FREE |
| WR-SLOT Slot Specialist | slot alignment share, slot vs outside targets | tracking alignment (NGS/PFF) | **GAP GG-775** |
| WR-CC Contested/Red-Zone Winner | contested-ball rate and win rate, red-zone target share | FTN `is_contested_ball`, pbp | PART (win rate needs charting; built as modifier candidate only) |
| (cross-cutting) Separation/route quality | separation, yards per route run | tracking / routes-run | **GAP GG-779** |

## TE
| Archetype | Signals | Source | Status |
|---|---|---|---|
| TE-IN Inline Blocker | inline snap share, low target share, run-block snaps | snaps, part personnel | PART (alignment not free, GG-775) |
| TE-MOV Move/Flex Receiver | target share, aDOT, route mix | pbp, part route | FREE |
| TE-RZ Red-Zone Specialist | red-zone target and TD share | pbp | FREE |
| TE-HYB Hybrid | both of the above, weighted | derived | PART |

## OL
| Archetype | Signals | Source | Status |
|---|---|---|---|
| OL-PASS Pass-Pro Anchor | pressures allowed per pass-block snap, sacks allowed | block-level win rate | **GAP GG-776** (pbp has team sack/pressure only, no blocker attribution) |
| OL-RUN Road-Grader | run-block win rate, yards before contact by gap | block-level / tracking | **GAP GG-776** |
| OL-POS Position/Versatility tag | positions played from snap counts | snaps | FREE |
| Team-level proxy | line pressure rate, stuffed-run rate by team | pbp, part | FREE (team, not player) |

## EDGE / DL
| Archetype | Signals | Source | Status |
|---|---|---|---|
| DL-RUSH Pure Pass Rusher | sacks + QB hits + hurries per pass-rush snap | pbp sacks/QB hits, PFR def pressures, snaps | PART (rate needs rush-snap denominator; GG-778) |
| DL-RDEF Run Defender | tackles for loss, run stops, missed tackle rate | pbp, PFR def | FREE |
| DL-INT Interior Disruptor | interior pressure and sack share | PFR def, snaps | PART |
| Alignment (wide-9 / 3-tech / 0-tech) | pre-snap alignment | tracking | **GAP GG-778** |

## LB
| Archetype | Signals | Source | Status |
|---|---|---|---|
| LB-RUN Box/Run Stopper | tackles, TFL, run-play snap share | pbp, snaps | FREE |
| LB-COV Coverage Linebacker | targets and completions allowed, pass-down snap share | PFR def | PART (assignment not free, GG-777) |
| LB-BLZ Blitzer | blitz rate, pressures per blitz | PFR def `times_blitzed`, FTN `n_blitzers` | PART |

## CB
| Archetype | Signals | Source | Status |
|---|---|---|---|
| CB-SHD Shadow/Man Corner | man-coverage snap share, target rate vs top receiver | coverage assignment + man/zone per defender | **GAP GG-777** (participation gives play-level coverage type, not who covered whom) |
| CB-ZN Zone Corner | zone snap share, INT/PBU rate | same | **GAP GG-777** (outcome rates FREE from PFR def / pbp) |
| CB-SLOT Nickel/Slot Corner | slot snap share | tracking alignment | **GAP GG-775/777** |
| CB-BALL Ball Hawk | INT + pass breakup per target | pbp, PFR def | FREE |

## S
| Archetype | Signals | Source | Status |
|---|---|---|---|
| S-DEEP Deep Safety | single-high / deep alignment share, deep targets allowed | alignment | **GAP GG-777** |
| S-BOX Box/Strong Safety | tackles near LOS, run-stop rate, blitz rate | pbp, PFR def | PART |
| S-HYB Hybrid | weighted blend | derived | PART |

## Why WR for the first mass-tier group, not CB

WR: every outcome is attributed to the player on every target (receiver id, air yards, YAC, completion, EPA), participation names the route on the targeted play, and snaps/rosters give share and position. Four of six archetypes are computable now. CB: outcomes are attributed only when the ball goes to the covered receiver, assignment (who covered whom, man vs zone per defender) and alignment are not free, so the two defining CB archetypes are GAPs. WR is the group the free data describes best.

## GAP register (all registered in `GOVERNANCE_GAP_LOG.md`)
GG-775 receiver/defender alignment and routes-run denominator (slot vs wide, RB/TE role) · GG-776 OL block-level win rates · GG-777 defender coverage assignment (man/zone per defender, shadow) · GG-778 DL/EDGE pass-rush snaps and alignment · GG-779 tracking-derived separation / speed.
