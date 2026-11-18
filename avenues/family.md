# Avenue: family (2026-11-11, rounds 10 and 11)

**Result: 30 n certified below the held file, for 0.001258 of score. The layouts are in the take dir. Nothing was submitted from here. The shell step is exact and the control passed: 814 stepped down to 757 gives side 27.931788181 against a held 27.931788239. The gain the board differences predicted is not there. The gains we found come from the upward step, at n where the held layout is a different design from its line neighbour.**

**Round 11:** 29 n certified below the held file of round 10, for 0.0021816 of score. 0.0017416 of that is new against the round 10 takes, on 29 n. The far-zone swap passes the upward jam, and the reader takes 55 more layouts. The section [Round 11](#round-11-2026-11-11-night) has the measurements.

This avenue had one job: build the exact step that carries a layout to the next n of its family line. Then measure the step and sweep it over every n from 300 up.

Words used here: "held" is `gather/round9-2026-11-11a.csv` (gate dir `gate/cand-round9-1111a`). "The board" is the per-puzzle board, the best side per n over all teams (`results/per-puzzle-lb-2026-11-09.json`). The side is `L = m + f` with `m` whole, and `k = n - m²`. A "stack" is a row of `c` tilted squares set face to face. An "arm" is a row of stacks along a wall. A "flush" stack touches the wall and the grid, so it spans the arm. The "run" is the part of an arm where neighbouring stacks are flush, parallel and one pitch apart. A "family line" is the set of n with the same `k - 2m`. The "donor" is the layout a step starts from, and the "target" is the n it ends at. The score of one n is `L / sqrt(n) - 1`, so a side that falls by `x` gains `x / sqrt(n)`.

## 1. The step, as measured

**A flush stack fixes its tilt.** A stack of `c` squares tilted by `t` spans `c cos t + sin t`. The arm is `c - 1 + f` wide. So `c cos t + sin t = c - 1 + f`. Neighbouring stacks touch along their long sides, so the pitch along the wall is `p = 1 / cos t`. The reader checks both on every stack before it accepts a layout. At n = 814 (`c = 8`, `f = 0.944430`) the equation gives a tilt of 16.9326° and a pitch of 1.045317. The layout reads 16.933°.

**The step down removes 2m + 1 squares and keeps f.** Cut each arm between two stacks of its run and take one stack out. Take out one grid row and one grid column. Move everything beyond each cut in by exactly 1. The count is `c₁ + c₂` squares of the two stacks plus a row and a column that share one square. At n = 814 that is `8 + 8 + 21 + 21 - 1 = 57 = 2·28 + 1`. The result has `m - 1` and `k - 2`, so it is on the same family line. Its side is `L - 1` to 1e-7 and each arm has a gap of `p - 1`. It is legal as built in 110 of the 118 downward starts of the sweep. The other 8 overlap by up to 1.2e-4, and the first exact LP repairs them. The targets are `n - 2m - 1` for one shell down and `n + 2m + 3` for one shell up.

**Line neighbours differ by a median of 0.018 in f.** We measured the difference of `f` between an n and its neighbour one shell up. Only pairs of tilted layouts count.

| f of the lower n | held: median difference (pairs) | board: median difference (pairs) |
|---|---|---|
| 0.5 to 0.6 | 0.0366 (56) | 0.0376 (64) |
| 0.6 to 0.7 | 0.0339 (53) | 0.0305 (55) |
| 0.7 to 0.8 | 0.0208 (87) | 0.0177 (83) |
| 0.8 to 0.9 | 0.0146 (79) | 0.0147 (81) |
| 0.9 to 1.0 | 0.0092 (91) | 0.0088 (89) |
| all | 0.0178 (366) | 0.0176 (372) |

**The squeeze turns the gap into tilt.** After the step each arm has `p - 1` of free wall. Let the side fall by `d`. Each of the `s` stacks left in the run tilts more and its pitch grows by `|dp/df| d`, with

`dp/df = (sin t / cos² t) / (cos t - c sin t)`.

The wall itself is `d` shorter. If the two end zones of the arm kept their length, the balance would be `p - 1 = d (1 + s |dp/df|)`. They do not keep it. With `Z` for the wall the two end zones take per unit of `f`, the balance is

`d = (p - 1) / (1 + s |dp/df| + Z)`.

At n = 814 the reader counts 13 flush stacks per arm, so `s = 12` after the step. The plain formula (`Z = 0`, `dp/df = -0.2317`) gives `d = 0.011986` and we measured 0.012642, which is 105%. (The first version of this page said `s = 11`, `d = 0.012769` and 99%: that came from an older state of the reader.) That pair is the exception. Over the 117 one-shell steps down whose donor reads, the squeeze recovered a median of 58% of the plain formula. The table and the `pred_formula` column of the results table were computed again in round 11 with the committed reader:

| squares in the shorter stack | pairs | recovered / plain formula, median (range) | zone term Z, median |
|---|---|---|---|
| 5 | 1 | 0.32 (0.32 to 0.32) | 7.60 |
| 6 | 32 | 0.48 (0.33 to 0.88) | 3.19 |
| 7 | 44 | 0.66 (0.32 to 1.13) | 2.35 |
| 8 | 37 | 0.57 (0.05 to 1.06) | 2.73 |
| 9 | 1 | 0.35 (0.35 to 0.35) | 3.20 |
| 10 | 1 | 0.53 (0.53 to 0.53) | 2.48 |
| 11 | 1 | 0.15 (0.15 to 0.15) | 8.14 |
| all | 117 | 0.58 (0.05 to 1.13) | 2.63 |

"Recovered" is the side after the step less the side after the squeeze. The zone term is `Z` solved from the measured side, for the arm that binds. The plain formula is not an upper limit: 6 of the 117 pairs recover more than `d`, the most 113%. `Z` is solved from each pair's own result, so it is one free number per pair. It restates what the formula misses and predicts nothing until it is derived from a layout. On 814 down to 757 the end zones gave wall back (`Z` about -0.17).

**Stacks also shear.** The exact LP with every angle fixed lowers the gapped 757 from 27.944430 to 27.940615. No square turns in that move. The squares of a stack slide along their faces, so a stack is rigid in tilt but not in shape. The formula does not hold this term, so a pair can recover more than the formula. The largest we measured is 113%.

## 2. The tool

[`family_step.py`](../family_step.py) is the tool.

- **read** finds the two arms, their runs and the stack boundaries. It also finds the full grid rows and columns and the three end zones: the corner between the arms and the far end of each arm. It refuses a layout it cannot read and gives the reason.
- **down** is the step of section 1, then the squeeze.
- **up** is the reverse. A new stack needs `p` of wall and the step gives 1. So the tool opens the layout by the pitch, which gives a layout in a box `L + p`. It adds one stack per arm, one grid row and one grid column. That start is not legal as built. Of the 178 one-shell upward starts of the sweep none has a positive gap: 94 are at exact contact and 84 overlap, 74 of them by more than 1e-4 and the worst by 1.6e-2 (797 from the held 740). The first exact LP of the squeeze makes the start legal, and every later stage is legal. The squeeze takes the room back. The new squares are copies of their own neighbours, because a grid line beside an arm can sit 0.09 off the lattice. The copies can still end up to 1.6e-2 inside a neighbour. The exact LP repairs that in one solve. The tool refuses the step beyond 3e-2.
- **squeeze** is a sequential LP over every square. One step solves an LP over all centres and angles with the gaps linearised, then the exact LP at the new angles. A step counts only when the exact LP returns a legal layout with a smaller side. So every stage is a legal layout, and the stacks of an arm turn together. An upward step then alternates Evan Daniel's `fq quench` (MIT) with the LP, up to three rounds.
- **take** certifies with the lane's rule (`floatsafe` at 2.2e-11, and below the held score by more than 1e-10) and writes the take dir.

**The reader covers 74 of the 701 n from 300 up.** 288 are the plain grid. 290 have no arm of flush stacks. 46 have one arm. 3 have a second arm that does not reach from the wall to the grid. 74 read as two arms.

**`methods_lp.py` asks for a smaller gap than its solver delivers.** It asks its LP for a gap of 4e-11, and it runs HiGHS at a feasibility of 1e-10. The exact step can come back 1e-10 to 3e-10 inside a neighbour, and the 2.5e-11 check then rejects the move. On the gapped 757 every step was rejected. `family_step.py` asks for 2e-10 in its own process and moves the centres apart by the rest, at a cost under 1e-8 of side. `methods_lp.py` is not changed.

**An older HiGHS gives up on some starts that overlap.** The HiGHS of scipy 1.13 ends with status 15 (unknown) on some exact LPs that start from an overlap. Another solver or another trust radius solves the same LP. The tool tries three radii and three solvers. Before the repair of overlaps and this retry, the upward step refused one pair in three for overlap. 35 of the 37 upward one-shell pairs it refused that way build now.

## 3. The controls

**814 down to 757: passed.** The donor reads as `m = 28`, `k = 30`, `f = 0.944430`, two arms of 8-square stacks at 16.933°, runs of 13 and 13.

| stage | side | note |
|---|---|---|
| after the step | 27.944429709 | 757 squares, smallest gap 5.02e-11, equal to 28.944429709 - 1 |
| exact LP, angles fixed | 27.940615318 | the shear |
| sequential LP, 16 steps, 84 s | 27.931788185 | below the go line 27.9362 after two steps |
| fq polish | 27.931788180 | |
| certified | 27.931788181 | |
| held 757 | 27.931788239 | ours is 5.8e-8 lower |

The squeeze recovered 0.012642 against a formula value of 0.011986 (`s = 12`), which is 105%. The result reads as the held design: 8-square stacks at 17.447°, runs of 12 and 11. The path of the sequential LP does not repeat to these digits: a second run ended at 27.931788367 in 18 steps, and the fq polish brought both to 27.931788180.

**757 up to 814: lands on the held layout.** The layout opens at 28.980010457 (`p = 1.048222`). The sequential LP ends at 28.944429713 in 163 s. Held is 28.944429709.

**924 down to 863 (c = 7, f = 0.855): 59% of the formula.** After the step the side is 29.855381659. The squeeze ends at 29.844358062. Held is 29.844287857, so we are 7.0e-5 above it. 924 reads runs of 14 and 14, so `s = 13`. The formula gives `d = 0.018708` and we measured 0.011024.

**Two pairs with f near 0.7, from the sweep.**

| pair | stacks | f | after the step | after the squeeze | held | recovered of formula d |
|---|---|---|---|---|---|---|
| 857 down to 798 | 9 and 9 | 0.766537 | 28.766536608 | 28.752284901 | 28.745602739 | 0.014252 of 0.040778, 35% |
| 852 down to 793 | 7 and 8 | 0.699596 | 28.699596305 | 28.680311328 | 28.678779877 | 0.019285 of 0.032048, 60% |

Both end above the held side. In both the held target is a different design from the donor.

## 4. The sweep

The held file gives 74 donors. The merged harvests give 38 public layouts that read and sit within 0.005 above the held side. The raw harvests give 127 more designs that we did not already hold as a donor, and 84 of them were built in the time. Every public donor has an accepted licence (Apache 2.0, CC BY 4.0 or CC0), and `take.tsv` keeps the source and the licence of each one it uses. We ranked the pairs by the gain the board predicts. The predicted side is the side of the board at the target plus the gap of the donor to the board. The predicted gain is the held side of the target less that. We built the best first. A "walk" carries one design shell after shell while it stays within 4e-3 of the held side.

432 pairs are in the table, on 139 targets, from 196 donors.

| step | pairs | built | refused | below held | certified | within 1e-6 of held | within 1e-4 | within 1e-3 | median of side less held |
|---|---|---|---|---|---|---|---|---|---|
| down, 1 shell | 123 | 118 | 5 | 15 | 7 | 15 | 25 | 50 | +1.32e-03 |
| down, 2 shells | 45 | 34 | 11 | 1 | 1 | 0 | 1 | 8 | +4.39e-03 |
| down, 3 shells or more | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 1 | +7.45e-03 |
| up, 1 shell | 181 | 172 | 9 | 37 | 26 | 24 | 38 | 80 | +8.75e-04 |
| up, 2 shells | 53 | 43 | 10 | 8 | 8 | 0 | 3 | 14 | +1.88e-03 |
| up, 3 shells or more | 20 | 19 | 1 | 2 | 2 | 1 | 1 | 4 | +3.04e-03 |
| all | 432 | 396 | 36 | 63 | 44 | 40 | 68 | 157 | +1.40e-03 |

"Below held" counts the rows the tool marked below the held side by more than 1e-9 (63 rows; the first version of this page counted 56 with a cut of 1.5e-9). "Certified" also needs the lane's rule, so a result a few 1e-9 lower does not count. A row that ended above held is not a final answer. One pair built twice differs by 5.8e-4 (924 from the held 863: 30.855875802 on one box, 30.855298160 in a walk). So the certified rates per direction are lower limits.

The full table is [`results/family-r10-2026-11-11.tsv`](../results/family-r10-2026-11-11.tsv). Its columns are the target, the donor, the direction and the shells, then the two predicted sides. Next come the side after the step, after the sequential LP and after the squeeze, and the held side. The last columns say whether the result certified, and give the load chain of a result that ended above held.

**Certified results.**

| n | step | donor n | donor source | held side | new side | score gain |
|---|---|---|---|---|---|---|
| 341 | up 1 | 304 | held | 18.942682818 | 18.941857360 | 4.470e-05 |
| 550 | up 1 | 503 | held | 23.911181037 | 23.910016066 | 4.967e-05 |
| 598 | up 1 | 549 | `grennwolf/squares-in-squares-top-1-santa-2025`, Apache 2.0 | 24.906541039 | 24.904006615 | 1.036e-04 |
| 599 | up 2 | 503 | held | 24.923742503 | 24.922343417 | 5.717e-05 |
| 601 | up 2 | 505 | held | 24.955538627 | 24.955535844 | 1.134e-07 |
| 602 | up 1 | 553 | held | 24.970896931 | 24.970896867 | 2.554e-09 |
| 638 | up 1 | 587 | `lucifer19/think-select-reclose`, Apache 2.0 | 25.763561933 | 25.762901981 | 2.613e-05 |
| 701 | down 1 | 756 | held | 26.912944726 | 26.912870096 | 2.819e-06 |
| 704 | up 1 | 651 | held | 26.963163195 | 26.958200040 | 1.871e-04 |
| 740 | up 1 | 685 | `lucifer19/think-select-reclose`, Apache 2.0 | 27.706993808 | 27.706459855 | 1.963e-05 |
| 745 | up 1 | 690 | held | 27.788343934 | 27.788306345 | 1.377e-06 |
| 757 | down 1 | 814 | `jazivxt/boxed-in-sub`, Apache 2.0 | 27.931788239 | 27.931788180 | 2.105e-09 |
| 797 | up 1 | 740 | held | 28.733979870 | 28.730580280 | 1.204e-04 |
| 813 | up 1 | 756 | held | 28.931300391 | 28.928915984 | 8.362e-05 |
| 817 | up 2 | 705 | held | 28.993201312 | 28.991970613 | 4.306e-05 |
| 861 | down 2 | 985 | held | 29.823848743 | 29.823846237 | 8.534e-08 |
| 862 | up 1 | 803 | `alexchilton/fault-line-dp-basin-hopping-lb-22-2620`, Apache 2.0 | 29.836563650 | 29.833382719 | 1.083e-04 |
| 863 | up 1 | 804 | held | 29.844287857 | 29.843714231 | 1.953e-05 |
| 872 | up 2 | 756 | held | 29.940885411 | 29.936667342 | 1.428e-04 |
| 873 | down 1 | 934 | held | 29.957161236 | 29.957160932 | 1.023e-08 |
| 875 | up 1 | 816 | held | 29.988865693 | 29.988197284 | 2.260e-05 |
| 921 | down 1 | 984 | `malyshevdanil/squares-in-squares-living-atlas-of-tight-packings`, Apache 2.0 | 30.821403941 | 30.821263278 | 4.635e-06 |
| 922 | down 1 | 985 | held | 30.834719600 | 30.834718163 | 4.729e-08 |
| 924 | up 1 | 863 | held | 30.855381659 | 30.855298160 | 2.747e-06 |
| 933 | up 3 | 756 | `jazivxt/boxed-in-sub`, Apache 2.0 | 30.949834163 | 30.945191596 | 1.520e-04 |
| 934 | up 1 | 873 | `prvsiyan/a-square-deal-research-to-verified-packings`, Apache 2.0 | 30.964143237 | 30.964143057 | 5.816e-09 |
| 936 | up 1 | 875 | `jazivxt/boxed-in-sub`, Apache 2.0 | 30.997511207 | 30.995923263 | 5.190e-05 |
| 987 | up 2 | 863 | held | 31.865850947 | 31.865776790 | 2.360e-06 |
| 996 | up 1 | 933 | `jazivxt/boxed-in`, Apache 2.0 | 31.955474332 | 31.955104163 | 1.173e-05 |
| 997 | up 3 | 814 | `jazivxt/boxed-in-sub`, Apache 2.0 | 31.973616782 | 31.973616723 | 1.825e-09 |
| total | | | | | | 1.2582e-03 |

"Step" is the direction and the number of shells. 11 of the 30 come from a public donor. The sides are the tool's own. The gain is the certified score against the held score.

**The prediction from board differences does not hold where we tested it.** It said that a target gains the difference when its gap to the board is larger than its donor's. The total was about 0.057 of score over 284 targets. We could test it on the pairs whose donor reads. 111 built one-shell pairs had a predicted gain, on 55 targets, for 0.0064 of score with the best pair of each target. That is 11% of the total: the other 89% had no donor that reads or was not built, so it is untested, not refuted. 25 of the 111 ended below held. The measured gain on those targets is 0.000483 of score, 8% of the prediction, and the rank correlation of predicted and measured gain is -0.26. Of the 30 pairs with the largest predicted gain, 5 ended below held. The median result is 1.3e-03 from the held side and 2.5e-03 from the predicted side, so the held side is the better predictor. The other targets of the 241 have no donor that reads, or were not built in the time. The reason is in the first control. Where the held target is the same design as the donor, the step lands on the held layout to between 1e-9 and 1e-6 (39 one-shell pairs). So where our layouts along a line are one design, each is already at the side that design allows. Our reading is that the gap to the board changes along a line because the board changes design there, not because ours is loose. We do not have the board's layouts to check that.

**The gains come from a change of design.** 24 of the 30 certified n are upward steps. By the reader's signature (stack sizes, run lengths, zone sizes), in 11 of the 30 the held layout and the new one both read and differ. In 8 the held layout does not read as two flush arms and the new one does. Those 19 carry 93% of the gain. In the other 11 the signature is the same, and their gains sum to 8.8e-05. So the step wins where the target held a design other than its line neighbour's, and the neighbour's design is better there. The re-tilt by the LP is not the whole of it. At the last step the LP alone was below held for 21 of the 30 n. For the other 9 (704, 817, 863, 740 and 638 among them) the LP ended above held and the fq quench made the win.

## 5. Blockers

**Down: the target already holds a better design.** A downward step keeps the donor's design. Its median result is 1.3e-03 above the held side. The load chain of those results runs through an end zone, the corner and the grid. The side is held up by zones the step does not change.

**Up: the end zones do not follow.** 814 up to 873 is the clear case. The sequential LP stalls at 29.977812743 against a held 29.957161236. The LP multipliers name the contacts that carry the side: 29 inside the corner, 13 in each run, 6 in each far end, and 7 against the walls. No grid contact carries load. The chain runs wall, far end, run, corner, wall along both arms. `fq quench` with its default flags moves the layout to 29.968493, and the LP confirms a local optimum there, 0.0113 above held. So fq passes some jams that stop the LP, which is why the upward step alternates them. The far ends of the 814 design still do not fit `f = 0.957`.

**Refusals.** 20 upward and 16 downward pairs are refused in the table. 21: the layout before the step does not read as two arms (mostly after a first shell). 9: the exact LP cannot make the start legal. 4: the opened layout overlaps (beyond 3e-2, or refused by the older limit of 2e-3 and not built again in the time). 2: no clean cut through the grid. A refused pair has the reason in its row.

**The corner cannot be grafted between designs as it is.** We tried to put the corner zone of one design into another at the same n. Most grafts overlapped by 1e-3 to 1e-2 at the inner corner, where the grid block is irregular. The legal ones started a whole pitch short, about 0.21 above held. The wall of an arm is `corner + s·p + far end = m + f`, and two designs split it differently, so a graft leaves up to one pitch of room. The code was removed.

## 6. Next runs

1. **Finish the upward sweep.** 160 one-shell pairs of the plans are not built yet, 39 of them upward, most from the raw public donors. 87 of the 127 walks started before the deadline. The plans and the walk lists are in the work dir of the take. The command is `family_step.py run PLAN donors details.csv OUT --only up`, and `family_step.py walk` for the walks. Of the built upward pairs, 15% certified at one shell (26 of 172) and 19% at two shells (8 of 43). Of the built downward pairs at one shell, 6% certified (7 of 118).
2. **Widen the reader.** 336 tilted layouts from 300 up do not read: 290 have no flush arm and 46 have one. The step needs only two neighbouring stacks with the same tilt on each side of a cut. A reader for one arm and for arms that are not flush opens up to 336 more donors.
3. **Rank by design, not by board difference.** The predicted gain did not find the winners. A better rank puts first the targets whose held layout reads as a different design from the donor, or does not read as two arms at all.
4. **Fix the gap of `methods_lp.py` in its own lane.** Its `slp` can reject legal steps for the reason in section 2. The change is to ask 2e-10 and to move the centres apart by the rest.
5. **Swap a far end.** A far end sits at the free end of an arm, so it does not have the pitch problem of the corner. This is the untested way past the upward jam.

## Round 11 (2026-11-11, night)

**Result: 29 n certified below the held file of round 10, for 0.0021816 of score. 0.0017416 of that is new against the round 10 takes of this lane and of the modules lane, on 29 n. The large gains are steps from layouts that only the wider reader takes, and most of them land on an n whose held layout has no flush arm. The wider reader takes 31 of the 337 tilted layouts that the strict reader refuses, and 24 more with one flush stack per wall. The far-zone swap passes the upward jam. 814 up to 873 ended 0.0113 above held in round 10, and with the target's own far zones it ends 9.4e-5 below. Nothing was submitted from here.**

Words for this section: "held" is `gather/round10-2026-11-11a.csv` (gate dir `gate/cand-round10-1111a`). The held file does not hold every result of the round 10 takes yet. So "the bar" of an n is the lowest of three sides. They are its held side and its sides in the round 10 takes of the family lane and of the modules lane. A result counts only when it certifies below the bar. The take keeps the gain against held, and the tables here give both.

### Corrections to round 10

The skeptic of round 10 checked the take. All 30 n pass and the control repeats. It named the statements below as wrong, and sections 1 to 4 above now hold the corrected text.

- At 814 the reader counts 13 flush stacks per arm, and the first text said 12. So `s = 12` and `d = 0.011986`, and the control recovers 105% of the formula. At 924 it is `s = 13`, `d = 0.018708` and 59%.
- The plain formula is not an upper limit. 6 of 117 one-shell steps down recover more than `d`.
- The `pred_formula` column of the round 10 table mixed two states of the reader. We computed it again, and 126 of its 304 one-shell values changed.
- The zone term `Z` is fitted per pair, so it predicts nothing yet.
- The upward start is not legal as built. It is at contact or overlaps by up to 1.6e-2, and the first exact LP repairs it.
- The prediction from board differences was refuted on 55 targets, which hold 11% of it. The rest is untested.
- A row above held is not final. The LP path does not repeat beyond 1.8e-7, and one pair built twice differed by 5.8e-4.
- The round 10 take measured against round 9. Against round 10 it adds 15 n for 0.000498.
- The take named only "the held packing of n = X" where that held packing is a public layout. From this round, the source of every held donor carries its upstream source and licence. We match them by side against the results tables of the lane.

### Changes to the tool

- **walk** has `--misses N`. The walk goes on from every result, and a direction ends after N steps in a row that do not end below the bar.
- `--beat TAKE.tsv ...` lowers the bar of an n to its side in another take. `run`, `walk` and `take` have it.
- **The wide reader.** Where the strict reader refuses a layout, `read` tries a wider one. On each of two neighbouring walls it asks for two or more neighbouring stacks of one size and one tilt, one pitch apart. They must span a strip of width `c - 1 + f`, to 2e-2. The strip can start at the wall, or behind one or two border lines of upright squares. Other stacks on the wall belong to the end zones. The step cuts a border line at the square beside the cut stack, so the count stays `2m + 1`.
- The wide reader does not guess. The step that follows must remove or add exactly the right count and give the side `L - 1` to 1e-7. Its overlap must stay within what the exact LP repairs.
- **build** tries the cut at the middle of the runs. Where that cut is refused, it tries four other places.
- **A small overlap no longer refuses a step.** Sometimes the exact LP cannot make a start legal. If the overlap is under 5e-3, the tool moves every centre apart until the layout is legal, and the exact LP takes the room back. The limit for a downward cut is now 1.5e-2 (it was 2e-3).
- With `SQ_APART=3e-2` the same repair takes an overlap of up to 3e-2. It then runs more rounds of the exact LP, at a larger trust radius. It is off by default.
- **swap_far** is the far-zone swap, described below. `run --swap DIR` and `walk --swap DIR` use it.
- **run** has `--where` and `--tra`, for a second build of a pair at another cut and another first trust radius.

**Controls of the changed tool.** We built 814 down to 757 on boxD. After the step the side is 27.944429709, with 757 squares and a smallest gap of 5.02e-11. After the squeeze it is 27.931788180, and certified 27.931788181. Both sides equal the round 10 values to 1e-9. We ran it again on boxA with the last state of the tool, and it gives the same three numbers. The plain grids 399, 400, 900 and 961 are refused as "plain grid" before the wide reader runs, with `SQ_LOOSE=1` too.

### Walks from the new designs

Round 10 moved 51 n from 300 up in four lanes: family 30, modules 28, border 5 and soft 5. Some n are in two lanes. For each n we took the lowest layout we hold.

- 30 read as two arms and hold a design other than the round 9 layout. 19 of them read with another signature, and 11 did not read in round 9.
- 7 hold the same design as in round 9. We did not walk them.
- 14 do not read with the strict reader. 4 of those (507, 542, 638, 756) read with the wide reader, and their walks are in the part on the wider reader.
- The other 10 do not read at all: 341, 378, 640, 701, 705 (the modules layout), 799, 800, 811, 971 and 986. So of the border and soft wins named as two-arm layouts, only 600 and 651 read.

A walk steps one shell at a time, and each step starts from the result of the step before. A direction ends after two steps in a row that do not end below the bar. It ends at once when a step ends more than 2e-2 above the bar. 6 walks were refused in the first pass at a start with a small overlap. They ran again after the repair above, and the table holds the second run.

| start n | lanes of round 10 | up: shells built | up: n reached | up: certified | down: shells built | down: n reached | down: certified |
|---|---|---|---|---|---|---|---|
| 504 | modules | 2 | 551 600 | - | 1 | 459 | - |
| 550 | family | 3 | 599 650 703 | 599 | 2 | 503 458 | - |
| 598 | family+modules | 1 | 649 | - | 1 | 549 | 549 |
| 599 | family+modules | 2 | 650 703 | - | 1 | 550 | - |
| 600 | soft | 1 | 651 | - | 2 | 551 504 | 551 |
| 601 | family+modules | 2 | 652 705 | 705 | 2 | 552 505 | - |
| 651 | modules+soft | 2 | 704 759 | - | 3 | 600 551 504 | 600 551 |
| 652 | modules | 1 | 705 | 705 | 3 | 601 552 505 | - |
| 704 | family | 1 | 759 | - | 2 | 651 600 | - |
| 740 | family+modules | 2 | 797 856 | - | 2 | 685 632 | - |
| 745 | family | 1 | 802 | - | 2 | 690 637 | - |
| 797 | family+modules | 1 | 856 | - | 3 | 740 685 632 | 740 |
| 813 | family+modules | 3 | 872 933 996 | 933 | 1 | 756 | 756 |
| 816 | modules | 3 | 875 936 999 | - | 2 | 759 704 | - |
| 817 | family | 2 | 876 937 | - | 2 | 760 705 | - |
| 862 | family+modules | 2 | 923 986 | - | 2 | 803 746 | - |
| 863 | family | 2 | 924 987 | - | 2 | 804 747 | - |
| 872 | family | 2 | 933 996 | 933 | 3 | 813 756 701 | 813 |
| 873 | family | 2 | 934 997 | - | 2 | 814 757 | - |
| 875 | family+modules | 2 | 936 999 | - | 3 | 816 759 704 | 816 |
| 911 | modules | 1 | 974 | - | 2 | 850 791 | - |
| 921 | family+modules | 1 | 984 | - | 2 | 860 801 | - |
| 933 | family+modules | 1 | 996 | - | 2 | 872 813 | - |
| 934 | family | 1 | 997 | - | 3 | 873 814 757 | - |
| 936 | family | 1 | 999 | - | 2 | 875 816 | - |
| 974 | modules | not run | - | - | 2 | 911 850 | - |
| 975 | modules | not run | - | - | 3 | 912 851 792 | 912 |
| 987 | family+modules | not run | - | - | 2 | 924 863 | - |
| 995 | modules | not run | - | - | 2 | 932 871 | - |
| 997 | family+modules | not run | - | - | 2 | 934 873 | - |

The 30 walks made 105 steps, and every step built. 21 steps ended below the bar. 14 of them certified, on 11 n: 599, 705 and 933 upward, and 549, 551, 600, 740, 756, 813, 816 and 912 downward. In the table, "not run" marks a step that leaves the range of n.

- The largest gains come down from 651. 600 ends 1.4e-3 of side below the bar. 551 ends 8.7e-4 below, two shells down. 933 ends 9.5e-4 below, with the same side from 872 and from 813. 549 from 598 ends 4.8e-4 below.
- A chain works. 651 down to 600 certified. The next step started from that 600, went down to 551 and certified too.
- 7 steps land on the layout that the target already holds, to 2e-9 of side. They are 652 from 601, 601 from 652, 704 from 651, 797 from 740, 872 from 813, 875 from 816 and 873 from 934. So both n of each pair already hold one design.
- The median step ends 2.9e-3 above the bar. 10 steps end between 2e-8 and 2e-4 above it. They are 934 (2e-8), 911 (1.4e-5), 759 (5.2e-5, from two starts), 923 (7.5e-5), 701 (9.4e-5), 924 (1.1e-4 and 1.3e-4), 974 (1.1e-4) and 851 (1.7e-4).
- No direction went past three shells.

**A walk also ends where its result does not read.** The tool writes no row then. By the stop rule, 15 of the 55 walks of this part could have gone on. The same holds for 27 of the 49 walks from the layouts of the wide reader. It also holds for 17 of the 37 walks from the layouts of the loose option. A few of those ended at the deadline of the round, and the others at a result that does not read. The walks of this part ran with the tool as it was at the start of the round, before the wide reader.

We ran 3 upward steps from the new designs again with the last tool and `SQ_APART=3e-2`. The results are: 705 from 652 ends 4.2e-5 below the bar, 760 from 652 ends 6.7e-3 below the bar and 817 from 652 ends 1.5e-3 below the bar. 705 from 652 ends on the side it had before. The walk then goes on to 760 and 817, which the first run did not reach.

### The pairs and walks round 10 left

Round 10 left 30 upward one-shell pairs unbuilt. Its report said 39, and 9 of those were built before it ended. It also left 40 walks, and 37 of them have a donor that reads. We ranked both lists by design.

1. The targets whose held layout does not read: 11 pairs and 13 walks.
2. The targets that read with a signature other than the donor's one shell on: 19 pairs and 20 walks.
3. The targets with the same design: 4 walks.

The walks ran with the rule of round 10: go on while the result stays within 4e-3 of the bar.

**The pairs.** 29 of the 30 pairs built. One certified: 638 from a public layout of 587 ends 7.8e-5 below the bar. 3 more end less than 3e-6 from the bar: 507 (1e-9 below, not certified), 812 (9e-9 above) and 755 (2.7e-6 above). The median pair ends 3.8e-3 above the bar, which is the upward jam again. The build of 981 from a public layout of 918 did not end in 21 minutes of the LP. We stopped it, and the tool needs a time limit for one build.

Round 10 refused 6 one-shell pairs at a start that overlapped by less than 5e-3. 6 of them ran with the repair, and 6 built. None of them ended below the bar. The nearest is 924 from 863, which ends 1.3e-4 above.

**The walks.** 14 of the 37 walks ran, for 16 steps. All of them built. None certified. 3 steps landed on the bar, to 2e-9: 745 from 690, 870 from 811 and 976 from 913. The nearest are 993 from 930 (1.7e-7 above) and 987 from 924 (8.0e-4 above). We gave the workers of this part to the loose walks, which were winning. The other 23 walks did not run.

### Pairs from new public donors

We read the public files of the harvest again with the wide reader on. A donor is a public layout no more than 0.005 above the held side of its n, from which the step builds. Round 10 did the same with the strict reader only.

The scan read 439 public files. 2085 layouts were inside the 0.005 and were not donors already. 300 of them read and build a step: 113 with the strict reader and 187 with the wide reader only. The first 122 donors make 223 one-shell pairs, 103 of them upward. They are ranked with the upward pairs first, and first the targets whose held layout does not read.

65 pairs ran, and 61 built. 2 rows certified, all on n = 374. They start from public layouts of 335 and end on the side of the 374 that the loose walk gives. The nearest misses are 993 from 930 (9.0e-8 above), 934 from 873 (5.0e-7 above), 930 from 869 (1.4e-5 above) and 917 from 856 (3.8e-5 above). The other 158 pairs and the 178 donors outside this list did not run.

### The reach of the wider reader

The held file of round 10 has 701 n from 300 up. 288 are the plain grid, and 76 read with the strict reader. The strict reader refuses 337: 288 have no flush arm, 46 have one, and 3 have a second arm that does not span.

**The wide reader adds 31 of the 337.** That is 13 of the 288, 16 of the 46 and 2 of the 3. The step builds from 25 of them upward and from 23 downward. The others are refused at the cut: no full grid line near the cut, a cut that is not clean, or no border square beside it. `work/reach.tsv` in the take dir has every n.

**The other 306.** We counted the stacks of each refused layout without any wall test. A "pair" in this table is two neighbouring stacks with one tilt, one pitch apart.

| what the layout holds | n |
|---|---|
| no pair of stacks of 3 or more squares | 180 |
| pairs of stacks of 5 or more, along one wall direction only | 61 |
| pairs along both directions, but the stacks do not span `c - 1 + f` to 2e-2 | 49 |
| pairs only of stacks shorter than 5 | 12 |
| flush pairs along both directions, away from the walls | 4 |

So the step has nothing to cut in 180 of them. The 61 need a step for one arm. The 49 hold strips with more than one stack across them, and a cut along one stack is not clean there. In 971 and 811 the ends of the stacks reach 0.01 to 0.04 into the grid line beside them. 799 holds two tiers of 7-square stacks.

**Walks from the layouts the wide reader adds.** There are 49 walks: 8 from the four starts above and 41 from held layouts that the wide reader adds. The upward walks ran first.

| start n | donor | up: shells built | up: n reached | up: certified | down: shells built | down: n reached | down: certified |
|---|---|---|---|---|---|---|---|
| 460 | `460-w11` | 1 | 505 | - | 1 | 417 | - |
| 507 | `507-s11` | 1 | 554 | - | 2 | 462 419 | - |
| 507 | `507-w11` | 1 | 554 | - | 2 | 462 419 | - |
| 542 | `542-s11` | 1 | 591 | - | 1 | 495 | - |
| 591 | `591-w11` | 1 | 642 | - | not run | - | - |
| 592 | `592-w11` | 1 | 643 | - | not run | - | - |
| 601 | `601-w11` | 5 | 652 705 760 817 876 | 705 760 817 | 2 | 552 505 | - |
| 637 | `637-w11` | 1 | 690 | - | 1 | 586 | - |
| 638 | `638-s11` | 1 | 691 | - | 2 | 587 538 | - |
| 638 | `638-w11` | 1 | 691 | - | 2 | 587 538 | - |
| 645 | `645-w11` | 1 | 698 | - | 1 | 594 | - |
| 689 | `689-w11` | 2 | 744 801 | - | 2 | 636 585 | - |
| 696 | `696-w11` | 1 | 751 | - | 1 | 643 | - |
| 703 | `703-w11` | 2 | 758 815 | - | 2 | 650 599 | - |
| 742 | `742-w11` | 2 | 799 858 | - | 2 | 687 634 | 687 |
| 744 | `744-w11` | 1 | 801 | - | 2 | 689 636 | - |
| 745 | `745-w11` | 2 | 802 861 | - | 1 | 690 | - |
| 750 | `750-w11` | 1 | 807 | 807 | 1 | 695 | - |
| 756 | `756-s11` | 2 | 813 872 | - | 1 | 701 | 701 |
| 798 | `798-w11` | 1 | 857 | - | 2 | 741 686 | - |
| 806 | `806-w11` | 1 | 865 | - | 1 | 749 | 749 |
| 856 | `856-w11` | 1 | 917 | - | 0 (then refused) | - | - |
| 915 | `915-w11` | 1 | 978 | - | 1 | 854 | - |
| 972 | `972-w11` | not run | - | - | 2 | 909 848 | - |
| 979 | `979-w11` | not run | - | - | 1 | 916 | - |
| 981 | `981-w11` | not run | - | - | 1 | 918 | - |
| 994 | `994-w11` | not run | - | - | 2 | 931 870 | - |
| 997 | `997-w11` | not run | - | - | 2 | 934 873 | - |

The 49 walks made 71 steps. 70 built and 1 was refused. 9 steps ended below the bar, and 7 certified, on 7 n.

| n | step | side less bar | the held layout of n |
|---|---|---|---|
| 687 | down from 742 | -3.875e-03 | no flush arm |
| 701 | down from 756 | -2.804e-05 | no flush arm |
| 705 | two shells up from 601 | -2.077e-03 | two arms |
| 749 | down from 806 | -3.409e-05 | no flush arm |
| 760 | three shells up from 601 | -8.366e-03 | two arms |
| 807 | up from 750 | -3.288e-03 | no flush arm |
| 817 | 4 shells up from 601 | -8.559e-04 | two arms |

- The strict reader refuses the layouts of 601, 742, 750 and 806. Most of the targets hold no flush arm in the held file. So these gains bring a two-arm design to an n that holds another kind of layout.
- The walk up from 601 was refused at its first step, at an overlap of 8.7e-3. With `SQ_APART=3e-2` it built. It passes 652 on the bar and then ends below the bar at 705, 760 and 817. Its 705 is 2.0e-3 lower than the 705 that the round 10 layout of 652 gives. Its fifth step, 876, ends 4.3e-3 above the bar.
- 801 from 744 ended 2e-9 below the bar and did not pass floatsafe.
- The nearest misses are 916 from 979 (3.4e-6 above), 801 from 689 (8.5e-5) and 505 from 460 (1.2e-4).

**One flush stack is enough for a cut.** A cut needs one flush stack with clean faces on each wall, and the checks of the step decide whether the stack has them. With `SQ_LOOSE=1` the wide reader also takes a wall that has flush stacks but no two neighbours. Its run is then every flush stack of the most common size on that wall, and `build` tries the cut at five of them. That adds 24 of the 306, and the step builds from 21 of them: from 21 upward and from 20 downward. `work/reach-loose.tsv` in the take dir has them. The option is off by default. The walk list holds 37 walks from the 21 layouts, the upward walks first.

| start n | donor | up: shells built | up: n reached | up: certified | down: shells built | down: n reached | down: certified |
|---|---|---|---|---|---|---|---|
| 335 | `335-l11` | 2 (then refused) | 374 415 | 374 415 | not run | - | - |
| 410 | `410-l11` | 1 | 453 | - | 1 | 369 | - |
| 413 | `413-l11` | 1 | 456 | - | 1 | 372 | - |
| 453 | `453-l11` | 1 | 498 | - | 2 | 410 369 | - |
| 459 | `459-l11` | 1 | 504 | 504 | 1 | 416 | - |
| 497 | `497-l11` | 3 | 544 593 644 | 593 | 1 | 452 | - |
| 498 | `498-l11` | 1 | 545 | - | 1 | 453 | - |
| 544 | `544-l11` | 2 | 593 644 | - | not run | - | - |
| 587 | `587-l11` | 2 | 638 691 | - | 1 | 538 | - |
| 649 | `649-l11` | 2 | 702 757 | - | 1 | 598 | - |
| 738 | `738-l11` | 2 | 795 854 | 795 854 | 1 | 683 | - |
| 748 | `748-l11` | 2 | 805 864 | - | 1 | 693 | - |
| 756 | `756-l11` | 4 | 813 872 933 996 | 813 933 | 1 | 701 | - |
| 799 | `799-l11` | 1 | 858 | - | 1 | 742 | - |
| 811 | `811-l11` | 2 (then refused) | 870 931 | 870 | 1 | 754 | 754 |
| 812 | `812-l11` | 2 | 871 932 | - | 2 | 755 700 | - |
| 868 | `868-l11` | 1 (then refused) | 929 | 929 | 1 | 809 | - |
| 917 | `917-l11` | 1 | 980 | - | 1 | 856 | - |
| 977 | `977-l11` | not run | - | - | 1 | 914 | - |
| 980 | `980-l11` | not run | - | - | 2 | 917 856 | - |
| 990 | `990-l11` | not run | - | - | 2 | 927 866 | 866 |

All 37 walks ran.

- Upward, 18 walks made 34 steps, and 31 built. 12 ended below the bar and 10 certified. The median upward step ends 9.0e-4 above the bar.
- Downward, 19 walks made 23 steps, and all built. 2 certified, on 754 and 866. The median downward step ends 8.4e-3 above the bar.
- 5 upward walks were refused at their first step, at an overlap of 1.1e-2 to 2.0e-2. They ran again with `SQ_APART=3e-2`, and all 5 built. 2 of them then certified: 811 gives 870, and 335 gives 374 and 415.

| n | step | side less bar | the held layout of n |
|---|---|---|---|
| 374 | up from 335 | -4.807e-03 | no flush arm |
| 415 | two shells up from 335 | -1.555e-03 | no flush arm |
| 504 | up from 459 | -3.660e-03 | two arms |
| 593 | two shells up from 497 | -4.729e-04 | no flush arm |
| 754 | down from 811 | -1.028e-03 | no flush arm |
| 795 | up from 738 | -5.162e-03 | no flush arm |
| 813 | up from 756 | -1.000e-08 | two arms |
| 854 | two shells up from 738 | -3.107e-03 | no flush arm |
| 866 | two shells down from 990 | -5.213e-05 | no flush arm |
| 870 | up from 811 | -1.313e-03 | two arms |
| 929 | up from 868 | -1.645e-04 | no flush arm |
| 933 | three shells up from 756 | -9.524e-04 | two arms |

- 8 of the 12 n hold no flush arm in the held file.
- A miss does not end the use of a walk. 544 from 497 ended 1.2e-2 above the bar, and the next step, 593, certified. 927 from 990 ended 9.4e-5 above, and the next step, 866, certified.
- 3 steps were refused later in a walk. Two had no border square beside the cut (992 and 994), and one overlapped by 5.3e-2 (458).
- The nearest misses are 755 from 812 (6e-7 above the bar), 701 from 756 (1.9e-6), 702 from 649 (2.4e-6), 809 from 868 (8.5e-5) and 927 from 990 (9.4e-5).

### The far-zone swap

**The swap moves the jam of 814 up to 873, and one way round ends below held.** In round 10 that step stalled at 29.977812743 after the sequential LP. After fq and the LP it stalled at 29.968493, which is 0.0113 above held. The load sat in the corner, the runs and the far ends.

`swap_far` replaces the far zone of each arm of the opened layout by the held target's own far zone. The zone keeps its own distance from the far wall. The two zones must hold the same squares to within whole stacks of the run, and the stacks that make up the difference go with the zone. At 873 the target reads runs of 14 and 13, with far zones of 37 and 29 squares. The opened donor has runs of 14 and 14, with far zones of 29 and 29. So one arm gives up its 29 squares and one stack for the 37 squares of the target.

The swapped layout overlaps by 3.4e-2. The tool moves every centre apart, which gives a side of 31.96. Then 17 rounds of the exact LP bring it back to a legal 30.046.

| start of the squeeze | after the sequential LP | after fq and the LP | against held 29.957160933 |
|---|---|---|---|
| no swap (round 10) | 29.977812743 | 29.968493 | +1.13e-2 |
| swap, the target's arms the same way round | 29.958149194 | 29.957808534 | +6.5e-4 |
| swap, the target's arms the other way round | 29.957067172 | 29.957067166 | -9.4e-5 |

The reader puts the arm with more flush stacks first. So we do not know which arm of the target belongs to which arm of the donor. The tool builds both ways round where the stack sizes allow it.

**The sweep.** 134 upward one-shell pairs of rounds 10 and 11 ended more than 2e-4 above the bar. 82 of them have a target that reads and stack sizes that agree in one way round or in both. That gives 142 builds, ranked nearest to the bar first.

36 of the 142 builds ran, on 26 pairs. 30 built, and 6 were refused because the two far zones did not differ by whole stacks or overlapped too far. The numbers are the side less the bar.

| target | donor | no swap | swap, same way round | swap, other way round |
|---|---|---|---|---|
| 987 | `924-held` | +7.53e-04 | -1.41e-09 | -1.41e-09 |
| 987 | `924-h09` | +7.69e-04 |  | -1.41e-09 |
| 745 | `690-rd28e3c` | +6.05e-04 | +2.22e-06 |  |
| 862 | `803-held` | +2.16e-04 | +3.04e-05 | +1.30e-03 |
| 506 | `461-rc22e4c` | +8.28e-04 |  | +5.68e-05 |
| 984 | `921-held` | +1.13e-03 | +5.98e-05 |  |
| 924 | `863-r0b9d45` | +1.15e-03 |  | +1.65e-04 |
| 757 | `702-r25ad72` | +3.93e-04 | +2.34e-04 | +3.93e-04 |
| 506 | `461-raebaa9` | +8.28e-04 |  | +3.01e-04 |
| 757 | `702-held` | +3.93e-04 | +3.93e-04 | +3.93e-04 |
| 816 | `759-h07` | +4.55e-04 | +7.32e-04 | +4.55e-04 |
| 816 | `759-held` | +4.55e-04 | +4.55e-04 | +2.18e-02 |
| 816 | `759-rccf017` | +4.55e-04 | +4.55e-04 | +4.55e-04 |
| 816 | `759-re76cc2` | +4.55e-04 | +4.55e-04 | +4.22e-02 |
| 863 | `804-r19c592` | +6.52e-04 | +6.71e-04 | +6.49e-04 |
| 759 | `704-rf8c890` | +6.78e-04 | +6.95e-04 | +6.78e-04 |
| 602 | `553-r24c710` | +8.07e-04 |  | +8.65e-04 |
| 996 | `933-s11` | +8.75e-04 | +8.75e-04 |  |
| 870 | `811-rdeb3a5` | +9.68e-04 | +9.68e-04 |  |
| 814 | `757-rbe986e` | +1.13e-03 | +1.13e-03 |  |
| 602 | `553-rdc1177` | +8.07e-04 |  | refused |
| 506 | `461-held` | +8.26e-04 |  | refused |
| 506 | `461-rfc0c5a` | +8.28e-04 |  | refused |
| 506 | `461-r8ba0a2` | +8.28e-04 |  | refused |
| 932 | `871-r8df885` | +9.30e-04 | refused |  |
| 973 | `910-rc441b6` | +1.10e-03 | refused |  |

The swap ends lower than the plain build on 11 of the 20 pairs that have both. At 987 it lands on the bar itself, to 1.4e-9, where the plain build ended 7.5e-4 above. 745 from 690 goes from 6.1e-4 above the bar to 2.2e-6 above, and 862 from 803 from 2.2e-4 to 3.0e-5. Nothing in the sweep certified. At 816 the swap lands on the side of the plain build, so the far zones do not hold that step.

**Downward the swap does not help.** We tested 933 down to 872. With the far zones of the held 872, the step ends 3.34e-3 above held one way round and 3.33e-3 the other. Without the swap it ends 3.40e-3 above.

### Parts not run

- The builds of two or three shells with no polish between did not run (`work/deploy/plan-2shell.tsv`, 65 builds).
- The second builds of the near misses did not run (`work/deploy/plan-near.tsv`, 36 pairs, each at another cut and another first trust radius).
- The far-zone swap sweep ran 36 of its 142 builds.
- 23 of the 37 walks that round 10 left did not run.
- 158 of the 223 pairs from the public donors did not run, and 178 donors are in no list yet.

### Steps by part

| part | steps | built | refused | below the bar | certified | median of side less bar |
|---|---|---|---|---|---|---|
| walk from a new design, up | 42 | 42 | 0 | 10 | 5 | +1.94e-03 |
| walk from a new design, down | 63 | 63 | 0 | 11 | 9 | +2.91e-03 |
| walk from a layout the wide reader adds, up | 32 | 32 | 0 | 6 | 4 | +2.83e-03 |
| walk from a layout the wide reader adds, down | 39 | 38 | 1 | 3 | 3 | +5.55e-03 |
| pair left from round 10, up | 34 | 34 | 0 | 1 | 1 | +4.18e-03 |
| pair left from round 10, down | 1 | 1 | 0 | 0 | 0 | +2.70e-03 |
| walk left from round 10, up | 16 | 16 | 0 | 3 | 0 | +3.25e-03 |
| far-zone swap, up | 38 | 32 | 6 | 4 | 1 | +4.55e-04 |
| walk from a layout the loose option adds, up | 34 | 31 | 3 | 12 | 10 | +8.96e-04 |
| walk from a layout the loose option adds, down | 23 | 23 | 0 | 2 | 2 | +8.43e-03 |
| pair from a new public donor, up | 65 | 61 | 4 | 7 | 2 | +2.62e-03 |
| walk from a new design, with the larger repair, up | 3 | 3 | 0 | 3 | 3 | -1.51e-03 |

"Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule: floatsafe at 2.2e-11 and a score more than 1e-10 below the bar. Every step is in [`results/family-r11-2026-11-11.tsv`](../results/family-r11-2026-11-11.tsv).

### Certified results

| n | step | start | bar side | new side | gain on held | gain on the round 10 takes |
|---|---|---|---|---|---|---|
| 374 | 1 up | the held packing of n = 335 | 19.832356218 | 19.827549544 | 2.485e-04 | 2.485e-04 |
| 415 | 2 up | the held packing of n = 335 | 20.860873027 | 20.859318178 | 7.632e-05 | 7.632e-05 |
| 504 | 1 up | the held packing of n = 459 | 22.915093562 | 22.911433559 | 1.649e-04 | 1.630e-04 |
| 549 | 1 down | the held packing of n = 598 | 23.895110569 | 23.894632678 | 2.040e-05 | 2.040e-05 |
| 551 | 2 down | the held packing of n = 651 | 23.926436941 | 23.925563222 | 3.722e-05 | 3.722e-05 |
| 593 | 2 up | the held packing of n = 497 | 24.827146485 | 24.826673602 | 1.942e-05 | 1.942e-05 |
| 599 | 1 up | the round 10 layout of n = 550 | 24.922343419 | 24.922343395 | 9.529e-10 | 9.529e-10 |
| 600 | 1 down | the held packing of n = 651 | 24.934824613 | 24.933421981 | 5.726e-05 | 5.726e-05 |
| 638 | 1 up | grennwolf/squares-in-squares-top-1-santa-2025 :: submission_improved.csv | 25.762901982 | 25.762824427 | 2.920e-05 | 3.070e-06 |
| 687 | 1 down | the held packing of n = 742 | 26.727922063 | 26.724046662 | 1.479e-04 | 1.479e-04 |
| 701 | 1 down | the round 10 layout of n = 756 | 26.912870097 | 26.912842057 | 3.878e-06 | 1.059e-06 |
| 705 | 2 up | the held packing of n = 601 | 26.972905707 | 26.970828618 | 2.285e-04 | 7.823e-05 |
| 740 | 1 down | the round 10 layout of n = 797 | 27.706459856 | 27.706455207 | 1.980e-05 | 1.709e-07 |
| 749 | 1 down | the held packing of n = 806 | 27.843351544 | 27.843317452 | 1.246e-06 | 1.246e-06 |
| 754 | 1 down | the held packing of n = 811 | 27.905568524 | 27.904540904 | 3.742e-05 | 3.742e-05 |
| 756 | 1 down | the round 10 layout of n = 813 | 27.921545069 | 27.921468853 | 3.938e-06 | 2.772e-06 |
| 760 | 3 up | the held packing of n = 601 | 27.984676451 | 27.976310656 | 3.035e-04 | 3.035e-04 |
| 795 | 1 up | the held packing of n = 738 | 28.703852896 | 28.698690781 | 1.831e-04 | 1.831e-04 |
| 807 | 1 up | the held packing of n = 750 | 28.870124903 | 28.866837212 | 1.157e-04 | 1.157e-04 |
| 813 | 1 down | the held packing of n = 872 | 28.928915985 | 28.928910904 | 8.380e-05 | 1.782e-07 |
| 816 | 1 down | the round 10 layout of n = 875 | 28.978163044 | 28.978162964 | 1.304e-08 | 2.817e-09 |
| 817 | 3 up | the round 10 layout of n = 652 | 28.991970614 | 28.990462295 | 5.277e-05 | 5.277e-05 |
| 854 | 2 up | the held packing of n = 738 | 29.727922063 | 29.724815077 | 1.063e-04 | 1.063e-04 |
| 866 | 2 down | the held packing of n = 990 | 29.879061281 | 29.879009156 | 1.771e-06 | 1.771e-06 |
| 870 | 1 up | the held packing of n = 811 | 29.924791453 | 29.923478757 | 4.450e-05 | 4.450e-05 |
| 873 | 1 up | the held packing of n = 814, far zones of the held 873 | 29.957160933 | 29.957067167 | 3.173e-06 | 3.173e-06 |
| 912 | 1 down | the round 10 layout of n = 975 | 30.703185851 | 30.703185815 | 2.453e-06 | 1.193e-09 |
| 929 | 1 up | the held packing of n = 868 | 30.908528618 | 30.908364096 | 5.398e-06 | 5.398e-06 |
| 933 | 2 up | the round 10 layout of n = 813 | 30.945191598 | 30.944239201 | 1.832e-04 | 3.118e-05 |
| total | | | | | 2.1816e-03 | 1.7416e-03 |

"Gain on held" is against `gate/cand-round10-1111a/details.csv`, and `take.tsv` holds it. "Gain on the round 10 takes" is against the bar. Where the second number is small, a round 10 take of this lane or of the modules lane already lowers that n by nearly as much.

### Next runs

1. **The larger repair on every start.** `SQ_APART=3e-2` came late in this round. It turned refused first steps into 870, 374 and 415 from the loose layouts, and into 705, 760 and 817 from 601. Make it the default of every upward walk, and build again the starts that rounds 10 and 11 refused.
2. **Walk on from the results that ended a walk.** A walk ends where its result does not read, and that ended about half of the walks of this round. Read those results with `SQ_LOOSE=1` and walk on. The one test went from 705 on to 760 and 817, and both certified.
3. **Steps into the n with no flush arm.** Most of the large gains land on one: 374, 415, 687, 795, 807 and 854. 288 n from 300 up hold no flush arm. List each one that is one shell from a layout that any reader takes, and build it.
4. **The public donors that only the wide reader takes.** 300 donors wait, and 65 pairs ran. Build the upward pairs first. Read the public files with `SQ_LOOSE=1` too, which this scan did not do.
5. **The rest of the swap sweep**, and `walk --swap` as the standing rule. Then every upward step that ends above the bar tries the target's far zones, both ways round.
6. **Second builds of the near misses.** 755, 993, 701, 702, 745, 916 and 862 ended less than 5e-5 above the bar. The LP path does not repeat, so a second build at another cut can end lower.
7. **Two more readers.** A step for a layout with one arm reaches 61 more n. A cut through a strip with more than one stack across reaches 49 more.
8. **A time limit for one build.** 981 from 918 held one worker for 21 minutes.
9. **Sources.** 4 held donors have no source in the results tables yet (587, 915, 934 and 997). None of them is the start of a certified result.

## Round 12 (2026-11-12, night)

**Result: 24 n certified below the held file of round 11, for 0.0009333 of score. Against the round 11 takes of every lane the gain is 0.0006365, on 24 n. Nearly all of it comes from walks of new designs. 11 of the 24 n start from layouts that other lanes wrote late in round 11 or in this round: 9 from the corner-zone sweep, one from the soft lane and one from the polish lane. Nothing was submitted from here.**

Words for this section: "held" is `gather/round11-2026-11-11b.csv` (gate dir `gate/cand-round11-1111b`). "The bar" of an n is the lowest of its held side and its sides in the round 11 takes of the family, modules, zones, soft and polish lanes, and of the two zone sweeps. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it. `take.tsv` gives the gain against held.

### Changes to the tool

- **A walk reads every layout with `read_any`.** That is the strict reader, then the wide reader, then the wide reader with the loose option. A walk no longer needs `SQ_LOOSE=1` to go on from a result that only the loose option takes.
- **An upward step repairs an overlap of up to 3e-2.** This was `SQ_APART=3e-2` in round 11. It is now the default of every upward walk. `SQ_APART` still sets the limit when it is given.
- **Every step's layout goes to `OUTDIR/steps`.** A later run can start from any step, also from one that did not end below the bar.
- **A walk that ends because a layout does not read leaves a line in `OUTDIR/ends-R.tsv`.** The line gives the donor, the direction, the step and the reason.
- **One build has a time limit, `--buildsec` (900 s by default, 600 s in this round).** The LPs and fq get what is left of it. HiGHS gets the rest as its own time limit. When the time runs out, the row keeps the last legal layout and has the state `time limit`.
- The names and arguments of the functions did not change, so `family_readers.py` of the readers lane can import the file.

The boxes ran the repo file of commit `dbf91b6`, sha256 `baca0ff68e51bca5d5a7627d9b73eabe150592abbd2d3677a6e7827adbee6a4e`. The work log of the take dir has the hashes of the other files.

**Controls.** 814 down to 757 with the new tool on boxA gives 27.944429709 after the step and 27.931788181 certified. Both equal round 10 and round 11 to 1e-9. One step up from `652-s11` with `--buildsec 20` ends at 20 s with the state `time limit`. Its layout is legal (smallest gap 1.3e-10), at side 26.975454643.

### What ran

The round ran from 01:00 to 02:36 UTC on boxC (3 workers, 5 from 02:16), boxD (2) and boxA (2). The first builder of the round stopped at 01:09 on a usage limit. Its workers ran on, and a second run of the same builder took over at 01:16 from the same lists. Each job is one walk or one pair. The workers take the jobs in the order of their names, so the order below is the order of the work.

| order | list | what it holds | jobs | ran | certified n |
|---|---|---|---|---|---|
| 1 | near and near2 | second builds of the near misses of round 11, then of this round | 36 + 49 | 36 + 49 | 996; 549 740 854 933 |
| 2 | new, up | upward walks from the new designs | 88 | most | 16 n |
| 3 | reach, up | one-shell walks from held layouts that read and were never built | 8 | all | 922 985 |
| 4 | new, down | downward walks from the new designs | 88 | most | 6 n |
| 5 | on | the walks of round 11 that ended with no row, again from their start | 46 | 31 | - |
| 6 | apart | starts refused at an overlap in rounds 10 and 11, downward | 2 | 1 | - |
| 7 | reach, down | as 3, downward | 16 | 9 | - |
| 8 | raw, raw2 | pairs from public donors: 158 left from round 11, 332 from donors in no list | 490 | 6 | - |

Of the 176 walks from new designs, 152 ran. Some jobs of each list were cut at the deadline of 02:36.

The walks continued from round 11 restart from their first donor, because round 11 did not save the layouts of its steps. Their first 10 steps ended a median 1.07e-2 above the bar, and none certified. At 01:30 we moved them behind the downward walks of the new designs. The walks from the new designs were winning. In the end the continued walks made 42 steps, and none certified. We also moved 15 upward walks and 28 near-miss builds from boxA and boxC to boxD. A step there takes 10 s to 3 minutes. On boxA it takes 2.5 to 6 minutes, at a load of 20 to 28.

### Walks from the new designs

A new design is a held layout of an n that round 11 moved, or a layout that another lane wrote in this round or in the late zone sweeps of round 11. That is the 60 n from 300 up of `gate/cand-round11-1111b/gate.json`, 634 and 995 of the zones lane, the n of `take-zones-lowf-r11` and `take-zones-corner-r11`, and the n of `take-border-r12`, `take-polish-r12` and `take-soft-r12`. Each walk steps one shell at a time from the result of the step before. A direction ends after two steps in a row that do not end below the bar, or at once more than 2e-2 above it.

| start n | donor | up: shells built | up: n reached | up: certified | down: shells built | down: n reached | down: certified |
|---|---|---|---|---|---|---|---|
| 374 | `374-h12` | 1 (then refused) | 415 | - | 1 | 335 | - |
| 378 | `378-h12` | 2 | 419 462 | - | 2 | 339 302 | - |
| 415 | `415-h12` | 0 (then refused) | - | - | 2 | 374 335 | - |
| 507 | `507-h12` | 1 | 554 | - | 2 | 462 419 | - |
| 549 | `549-h12` | 5 | 598 649 702 757 814 | 598 649 702 | 1 | 502 | - |
| 550 | `550-h12` | 3 | 599 650 703 | 599 | 2 | 503 458 | - |
| 551 | `551-h12` | 5 | 600 651 704 759 816 | - | not run | - | - |
| 593 | `593-h12` | 1 | 644 | - | 1 | 544 | - |
| 598 | `598-o12` | 4 | 649 702 757 814 | 649 702 | not run | - | - |
| 598 | `598-zc11` | 4 | 649 702 757 814 | 702 | 2 | 549 502 | - |
| 599 | `599-h12` | 2 | 650 703 | - | not run | - | - |
| 600 | `600-h12` | 3 | 651 704 759 | - | 2 | 551 504 | - |
| 601 | `601-h12` | 5 | 652 705 760 817 876 | 817 | 2 | 552 505 | - |
| 634 | `634-z11` | 2 | 687 742 | - | not run | - | - |
| 634 | `634-zc11` | 2 | 687 742 | - | 1 | 583 | - |
| 638 | `638-h12` | 1 | 691 | - | 2 | 587 538 | - |
| 649 | `649-zc11` | 3 | 702 757 814 | - | 3 | 598 549 502 | 598 549 |
| 651 | `651-h12` | 2 | 704 759 | - | 3 | 600 551 504 | - |
| 652 | `652-h12` | 2 | 705 760 | - | 3 | 601 552 505 | - |
| 687 | `687-h12` | 3 | 742 799 858 | 742 | 1 | 634 | - |
| 702 | `702-zc11` | 2 | 757 814 | - | 1 | 649 | 649 |
| 703 | `703-zc11` | 2 | 758 815 | - | 2 | 650 599 | - |
| 705 | `705-h12` | 3 | 760 817 876 | - | not run | - | - |
| 738 | `738-h12` | 2 | 795 854 | 795 854 | not run | - | - |
| 740 | `740-h12` | 3 | 797 856 917 | - | not run | - | - |
| 742 | `742-h12` | 2 | 799 858 | - | 2 | 687 634 | 687 |
| 745 | `745-h12` | 2 | 802 861 | - | 1 | 690 | - |
| 756 | `756-h12` | 4 | 813 872 933 996 | 933 | 1 | 701 | - |
| 758 | `758-zc11` | 3 | 815 874 935 | 815 | not run | - | - |
| 760 | `760-h12` | 2 | 817 876 | - | not run | - | - |
| 795 | `795-h12` | 1 | 854 | - | 2 | 738 683 | 738 |
| 797 | `797-h12` | 2 | 856 917 | - | 2 | 740 685 | - |
| 803 | `803-zc11` | 3 | 862 923 986 | 862 | 2 | 746 691 | - |
| 806 | `806-h12` | 1 | 865 | - | 1 | 749 | - |
| 813 | `813-h12` | 3 | 872 933 996 | - | 2 | 756 701 | - |
| 815 | `815-h12` | 2 | 874 935 | - | 2 | 758 703 | - |
| 815 | `815-p12` | 2 | 874 935 | - | not run | - | - |
| 816 | `816-h12` | 2 | 875 936 | - | 2 | 759 704 | - |
| 817 | `817-h12` | 2 | 876 937 | - | 2 | 760 705 | - |
| 817 | `817-p12` | 1 | 876 | - | not run | - | - |
| 852 | `852-b12` | 1 (then refused) | 913 | - | 2 | 793 736 | - |
| 852 | `852-p12` | 1 | 913 | 913 | not run | - | - |
| 856 | `856-h12` | 2 | 917 980 | - | 1 | 797 | - |
| 862 | `862-h12` | 2 | 923 986 | - | 2 | 803 746 | - |
| 862 | `862-zc11` | 2 | 923 986 | 986 | 3 | 803 746 691 | - |
| 863 | `863-h12` | 2 | 924 987 | - | 2 | 804 747 | - |
| 863 | `863-zl11` | 2 | 924 987 | - | 2 | 804 747 | - |
| 870 | `870-h12` | 1 (then refused) | 931 | - | 1 (then refused) | 811 | - |
| 871 | `871-zc11` | 2 | 932 995 | 932 995 | 3 | 812 755 700 | 812 |
| 873 | `873-h12` | 2 | 934 997 | - | 2 | 814 757 | - |
| 875 | `875-h12` | 2 | 936 999 | - | 3 | 816 759 704 | - |
| 911 | `911-h12` | 1 | 974 | - | 2 | 850 791 | - |
| 912 | `912-h12` | 1 | 975 | - | not run | - | - |
| 921 | `921-h12` | 1 | 984 | - | not run | - | - |
| 921 | `921-zl11` | 1 | 984 | - | 2 | 860 801 | - |
| 923 | `923-zc11` | 1 | 986 | - | 4 | 862 803 746 691 | - |
| 924 | `924-h12` | 1 | 987 | - | 2 | 863 804 | - |
| 924 | `924-zc11` | 1 | 987 | 987 | not run | - | - |
| 929 | `929-h12` | 0 (then refused) | - | - | 0 (then refused) | - | - |
| 932 | `932-zc11` | 1 | 995 | 995 | 4 | 871 812 755 700 | 812 |
| 933 | `933-h12` | 1 | 996 | - | 2 | 872 813 | - |
| 972 | `972-h12` | not run | - | - | 2 | 909 848 | - |
| 974 | `974-h12` | not run | - | - | 2 | 911 850 | - |
| 975 | `975-h12` | not run | - | - | 3 | 912 851 792 | - |
| 983 | `983-zl11` | not run | - | - | 2 | 920 859 | - |
| 986 | `986-zc11` | not run | - | - | 3 | 923 862 803 | - |
| 994 | `994-h12` | not run | - | - | 2 | 931 870 | - |
| 995 | `995-h12` | not run | - | - | 2 | 932 871 | - |
| 995 | `995-z11` | not run | - | - | 2 | 932 871 | - |
| 996 | `996-h12` | not run | - | - | 2 | 933 872 | - |
| 997 | `997-h12` | not run | - | - | 2 | 934 873 | - |

- Upward, 128 steps ran and 123 built. 41 ended below the bar, and 20 rows certified, on 16 n. The median upward step ends 3.9e-4 above the bar.
- Downward, 113 steps ran and 111 built. 20 ended below the bar, and 7 rows certified, on 6 n. The median downward step ends 3.4e-3 above the bar.
- The layouts of the corner-zone sweep walk best. 871 gives 932 and then 995, 862 gives 986, 924 gives 987, 758 gives 815, 803 gives 862, and 932 gives 812 two shells down.
- The held 549 (from round 11, one shell down from 598) gives 598, 649 and 702 in one walk up. 601 gives 817 at its fourth shell.
- The start of 11 upward and 8 downward walks does not read with any reader, for example 807, 701, 754 and 504.

### Steps into the n with no flush arm

The held file of round 11 has 283 n from 300 up with no flush arm. 80 of them are one shell from a held layout that one of the readers takes. 66 of those 80 targets were built in round 10 or 11. The jobs of this part are the 24 one-shell walks from held layouts that read and were never built, with the targets that have no flush arm first. 17 of the 24 walks ran, for 21 steps. 11 steps were refused at the cut: no full grid line near the cut, or no border square beside it. 4 ended below the bar, and 2 certified: 922 and 985, one and two shells up from the held 861. Both targets hold two arms.

Unlike round 11, the gains of this round land mostly on n that hold two arms: 19 of the 24. 3 hold a layout that only the loose option reads (649, 738, 812), 854 holds one arm, and only 986 holds no flush arm. So the steps into the n with no flush arm did not repeat the yield of round 11 on the held layouts that are one shell away. Most of those were built in rounds 10 and 11.

### Second builds of the near misses

The 36 pairs of round 11's `plan-near.tsv` ran again at the cut 0.3 of the runs (it is 0.5 by default) and with a first trust radius of 1e-3 (it is 2e-3). Each bar was taken again from the held file of round 11. All 36 ran and 35 built. 2 ended below the bar and 1 certified: 996, by 1.8e-10 of score. A second build of 924 from `863-s11` certified 7.7e-6 below held. The corner-zone sweep then wrote a lower 924, so it is not in the take. The median second build ends 8e-5 above the bar upward and 1.7e-4 downward.

The same idea ran on this round's own misses. `mknear12.py` takes every built step that ends between 1e-9 and 2e-4 above its bar, and builds it once more from the layout it stepped from. A walk step gets the cut 0.3, and a near build gets the cut 0.7 and the radius 5e-4. A walk step k > 1 starts from the layout of step k - 1, which the tool now writes to `steps/`. 49 builds ran, and 44 built. 4 ended below the bar, and all 4 certified: 854 and 933 upward, 549 and 740 downward. The first build of 854 from the held 795 ended 9.2e-5 above the bar, and the second ends 4.1e-3 below it. A walk from 738 through 795 then found an 854 3.9e-6 lower still, which the take holds. 740 certifies only from its second build.

### Steps by part

| part | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|
| walk from a new design, up | 128 | 123 | 5 | 41 | 20 | 598 599 649 702 742 795 815 817 854 862 913 932 933 986 987 995 | +3.93e-04 |
| walk from a new design, down | 113 | 111 | 2 | 20 | 7 | 549 598 649 687 738 812 | +3.41e-03 |
| walk continued from round 11, up | 30 | 27 | 3 | 0 | 0 | - | +8.55e-03 |
| walk continued from round 11, down | 12 | 12 | 0 | 0 | 0 | - | +7.48e-03 |
| start refused at an overlap, built again, down | 1 | 1 | 0 | 0 | 0 | - | +1.05e-02 |
| walk from a held layout that a reader takes, up | 10 | 6 | 4 | 4 | 2 | 922 985 | -2.00e-09 |
| walk from a held layout that a reader takes, down | 11 | 4 | 7 | 0 | 0 | - | +1.09e-02 |
| second build of a near miss, up | 22 | 22 | 0 | 2 | 1 | 996 | +7.98e-05 |
| second build of a near miss, down | 14 | 13 | 1 | 0 | 0 | - | +1.67e-04 |
| pair from a public donor in no list, up | 6 | 6 | 0 | 0 | 0 | - | +6.41e-03 |
| second build of a near miss of this round, up | 30 | 27 | 3 | 2 | 2 | 854 933 | +7.40e-05 |
| second build of a near miss of this round, down | 19 | 17 | 2 | 2 | 2 | 549 740 | +5.22e-05 |

"Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule. Every step is in [`results/family-r12-2026-11-12.tsv`](../results/family-r12-2026-11-12.tsv). Its column `target_flush_arm` says whether the held layout of the target has a flush arm.

### Certified results

| n | step | start | the held layout of n | bar side | new side | gain on held | gain on the round 11 takes |
|---|---|---|---|---|---|---|---|
| 549 | 2 down | the zones-corner-r11 result of n = 649 | two arms (wide reader) | 23.894632678 | 23.893837106 | 3.395e-05 | 3.395e-05 |
| 598 | 1 down | the zones-corner-r11 result of n = 649 | two arms | 24.903994006 | 24.903875860 | 5.347e-06 | 4.831e-06 |
| 599 | 1 up | the held packing of n = 550 | two arms | 24.922343395 | 24.921888409 | 1.859e-05 | 1.859e-05 |
| 649 | 2 up | the held packing of n = 549 | loose reader | 25.914167947 | 25.911684960 | 1.241e-04 | 9.747e-05 |
| 687 | 1 down | the held packing of n = 742 | two arms (wide reader) | 26.724046662 | 26.724034289 | 4.721e-07 | 4.721e-07 |
| 702 | 2 up | the soft-r12 result of n = 598 | two arms | 26.921330474 | 26.920367208 | 9.227e-05 | 3.636e-05 |
| 738 | 1 down | the held packing of n = 795 | loose reader | 27.679294515 | 27.679226932 | 2.488e-06 | 2.488e-06 |
| 740 | 1 down | the held packing of n = 797 | two arms | 27.706455022 | 27.706453158 | 6.853e-08 | 6.853e-08 |
| 742 | 1 up | the held packing of n = 687 | two arms (wide reader) | 27.741947240 | 27.741943525 | 1.364e-07 | 1.364e-07 |
| 795 | 1 up | the held packing of n = 738 | two arms (wide reader) | 28.698690781 | 28.698690397 | 1.362e-08 | 1.362e-08 |
| 812 | 2 down | the zones-corner-r11 result of n = 932 | loose reader | 28.924791453 | 28.924167957 | 2.188e-05 | 2.188e-05 |
| 815 | 1 up | the zones-corner-r11 result of n = 758 | two arms | 28.965965694 | 28.965123570 | 2.950e-05 | 2.950e-05 |
| 817 | 4 up | the held packing of n = 601 | two arms (wide reader) | 28.990462295 | 28.987620664 | 9.942e-05 | 9.942e-05 |
| 854 | 2 up | the held packing of n = 738 | does not read | 29.724815077 | 29.720685782 | 1.413e-04 | 1.413e-04 |
| 862 | 1 up | the zones-corner-r11 result of n = 803 | two arms | 29.829920510 | 29.829899959 | 1.135e-04 | 7.000e-07 |
| 913 | 1 up | the polish-r12 result of n = 852 | two arms | 30.721540004 | 30.720685813 | 2.827e-05 | 2.827e-05 |
| 922 | 1 up | the held packing of n = 861 | two arms | 30.834718165 | 30.834591317 | 4.178e-06 | 4.178e-06 |
| 932 | 1 up | the zones-corner-r11 result of n = 871 | two arms | 30.939377900 | 30.939377655 | 4.939e-05 | 8.029e-09 |
| 933 | 3 up | the held packing of n = 756 | two arms | 30.944195823 | 30.944154495 | 1.353e-06 | 1.353e-06 |
| 985 | 2 up | the held packing of n = 861 | two arms | 31.844831970 | 31.844767232 | 2.063e-06 | 2.063e-06 |
| 986 | 2 up | the zones-corner-r11 result of n = 862 | no flush arm | 31.854405074 | 31.854396953 | 5.176e-05 | 2.586e-07 |
| 987 | 1 up | the zones-corner-r11 result of n = 924 | two arms | 31.865719579 | 31.865489514 | 7.323e-06 | 7.323e-06 |
| 995 | 1 up | the zones-corner-r11 result of n = 932 | two arms | 31.949761487 | 31.946420671 | 1.059e-04 | 1.059e-04 |
| 996 | 1 up | the held packing of n = 933 | two arms | 31.955104165 | 31.955104159 | 1.805e-10 | 1.805e-10 |
| total | | | | | | 9.3332e-04 | 6.3654e-04 |

"Gain on held" is against `gate/cand-round11-1111b/details.csv`, and `take.tsv` holds it. "Gain on the round 11 takes" is against the bar. The bar includes the late zone sweeps, which also wrote 598, 649 and 702. Every new side is above the best side of the public per-puzzle board of 2026-11-09. 922 and 985 start from the held 861, which is two shells down from the held 985. That 985 is from kmmmvs/squares-in-squares-private-packings, `local_bank.csv`, under "Other" terms, and `take.tsv` names it. The other rows build on Apache 2.0 or CC BY 4.0 layouts or on our own.

### How the walks ended

| list | direction | start does not read | a result does not read | refused at the step | two misses in a row | more than 2e-2 above | out of range or deadline |
|---|---|---|---|---|---|---|---|
| new | up | 11 | 10 | 5 | 23 | 6 | 17 |
| new | down | 8 | 9 | 2 | 35 | 7 | 3 |
| on | up | 0 | 9 | 3 | 4 | 3 | 1 |
| on | down | 0 | 10 | 0 | 1 | 0 | 0 |
| reach | up and down | 0 | 0 | 11 | 2 | 1 | 3 |

A walk now reads each result with the loose option too. Still, 39 walks ended at a result that no reader takes: 24 hold no flush arm and 15 hold one arm. The readers lane covers the one-arm layouts. In 5 of 5 walks that we tested, the opened layout before the squeeze does not read either, so a step without the squeeze between does not help.

### Parts not run

- 24 walks from new designs, 15 continued walks, 7 reach walks and one rebuilt start.
- 484 of the 490 pairs from public donors. The rescan of the public files with `SQ_LOOSE=1` did not run.
- The rest of the far-zone swap sweep (106 builds), the two- and three-shell builds without polish (65) and the 23 walks of round 10 (`walks-left.tsv`).

### Next runs

1. **Walk every new layout of every lane as it certifies.** 11 of the 24 n start from layouts that other lanes wrote hours before. A loop that reads every take dir and walks each new n up and down would catch them in the same round. `mk12d.py` in the work dir does one pass.
2. **Second builds of every near miss, at once.** 5 certified rows came from second builds, and 2 of them (740 and 996) are the result the take holds. A build takes 15 s to 3 minutes. `mknear12.py` does one pass.
3. **The rest of the walks of this round:** 24 from new designs, 15 continued walks and 7 reach walks.
4. **Public donors** last: 484 pairs and the rescan with the loose option. 6 pairs ran this round, and the median ended 6.4e-3 above the bar.
5. **Readers.** 39 walks ended at a result that no reader takes. The one-arm reader of the readers lane can carry 15 of them on.

## Round 13 (2026-11-12, early morning)

**Result: 16 n certified below the held file of round 12, for 0.0003479 of score. Against the round 13 takes of the other lanes the gain is 0.0003230. 12 of the 16 come from the follow loop, which walks every new layout of every lane as soon as it certifies. 7 of those 12 start from layouts that the soft, polish and modules lanes wrote during this round. The 795 that the skeptic of round 12 built on boxA certifies, and so does a 738 one shell down from it. The difference of 795 between the boxes comes from the scipy version, not the box. Nothing was submitted from here.**

Words for this section: "held" is `gather/round12-2026-11-12a.csv` (gate dir `gate/cand-round12-1112a`). "The bar" of an n is the lowest of its held side and its side in the take dir of every other lane of round 13 (`take-*-r13`). The loop reads it again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it. `take.tsv` gives the gain against held.

### The 795 that differs by box: the cause is the scipy version

The skeptic of round 12 built the step 738 -> 795 on boxA and got a side of 28.697749707. The family build of round 12 on boxD got 28.698690396 from the same start. We ran the same step, from the same file and the same tool, on every box and with five Python environments:

| box | Python | numpy | scipy (its HiGHS) | after the step | after the SLP | after the squeeze | seconds |
|---|---|---|---|---|---|---|---|
| boxA (skeptic of round 12) | 3.14.7 | 2.5.4 | 1.18.1 (1.12.0) | 28.781380413 | 28.697749715 | 28.697749707 | 35 |
| boxC | 3.12.16 | 2.5.4 | 1.18.1 (1.12.0) | 28.781380413 | 28.697749715 | 28.697749707 | 31 |
| boxD | 3.12.16 | 2.5.4 | 1.18.1 (1.12.0) | 28.781380413 | 28.697749715 | 28.697749707 | 38 |
| boxC | 3.12.16 | 2.2.6 | 1.18.1 (1.12.0) | 28.781380413 | 28.697749715 | 28.697749707 | 36 |
| boxC | 3.12.16 | 2.2.6 | 1.13.1 (1.2.0) | 28.781380413 | 28.698690578 | 28.698690396 | 106 |
| boxC | 3.12.16 | 2.0.2 | 1.13.1 (1.2.0) | 28.781380413 | 28.698690578 | 28.698690396 | 106 |
| boxC | 3.9.6 | 2.0.2 | 1.13.1 (1.2.0) | 28.781380413 | 28.698690578 | 28.698690396 | 94 |
| boxD (as in round 12) | 3.9.6 | 2.0.2 | 1.13.1 (1.2.0) | 28.781380413 | 28.698690578 | 28.698690396 | 110 |

- **The cause is the scipy version, through the HiGHS solver it bundles.** scipy 1.13.1 ships HiGHS 1.2.0 (July 2021), and scipy 1.18.1 ships HiGHS 1.12.0. The box, the Python version and the numpy version change nothing: each scipy gives the same side to 1e-9 on every box. The difference starts in the sequential LP, before fq. The step itself is the same to 1e-9.
- **Round 12 ran the old one on the remote boxes.** Their venv was built from the system Python 3.9, where pip stops at scipy 1.13.1. boxA ran scipy 1.18.1. So the same pair could give a different side on boxA than on boxC or boxD.
- **Both are right, and neither is better in general.** Both solvers return exact LP optima, and every layout is checked legal after each LP. With angles and contacts as they are, the LP often has many optimal vertices. The two HiGHS versions pick different ones, and the path of the sequential LP then forks. We measured it on 63 round 12 builds (near misses, and 4 wins). Each was built again on scipy 1.18.1 from the same start, with the same cut and trust radius (`mkrestack13.py`, list "round 12 near miss built again on scipy 1.18.1" below). The new solver is lower on 22, higher on 22 and equal on 19 (to 1e-9). The median difference is 0 and the mean is +1.3e-4, so the new solver is a little worse on average. The 795 is the largest gain of scipy 1.18.1. The largest loss is 917, 6.0e-3 higher.
- **What we changed.** Every box now runs scipy 1.18.1, so a pair gives the same side on every box. On boxC and boxD it is a venv of the uv Python 3.12.16 with numpy 2.5.4. scipy 1.18.1 is also 3 times faster on this step (31 to 38 s against 94 to 110 s). The old numpy (2.0.2, OpenBLAS) ran one build at 350 % CPU, so the workers now export `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `VECLIB_MAXIMUM_THREADS=1`. With 1.18.1 this changes nothing: one thread gives 28.697749707 too. Neither solver is better on average, so a near miss built on one is worth building on the other. Of the 71 builds of round 12 steps on scipy 1.18.1, 3 certified (652, 795 and 809). That is about as many as the second builds at another cut.

**The new 795 and the steps from it.** The skeptic's 795 certifies 3.336e-05 below held. It went into the take dir at 04:10 UTC, for the border lane. One shell down from it, a 738 certifies 7.216e-06 below held. The 854 did not come back. The up step from the new 795 needs `SQ_WALLTOL=4e-2` and `SQ_APART=6e-2` (below). Of 9 builds at five cuts and trust radii, the best ends 3.9e-6 above the bar (29.720689690 against 29.720685782). The old 795 gave the held 854 only at its second build, at the cut 0.3. One build of 854 from the old 795 on scipy 1.18.1 ends 4.2e-3 above the bar.

### Changes to the tool

- **`SQ_WALLTOL=4e-2` widens the wide reader.** It takes a stack whose span or distance from the wall is off by up to that much (the default stays 2e-2). The 795 of scipy 1.18.1 has one arm of 7 stacks of 8 squares. Their span is 0.022 to 0.025 short of flush and 0.034 off the border line, so no reader took it. At 4e-2 it reads as two arms of stacks of 8.
- **When `SQ_APART` is more than 3e-2, the up step refuses only an overlap beyond `SQ_APART`.** The up step from that 795 opens with an overlap of 3.6e-2. `SQ_APART=6e-2` now lets the squeeze repair it.
- Without the two options, the tool behaves as in round 12, and the function names and arguments did not change.
- **`family_loop.py` is the follow loop.** Every 5 minutes it does what `mk12d.py` and `mknear12.py` did by hand in round 12:
  1. It collects the rows of every box.
  2. It certifies them against the held file and every other lane's take dir.
  3. It copies those take dirs to the boxes as bars.
  4. It makes second builds of the near misses, and walks from every new layout.
  5. It deals the jobs to the box with the shortest queue for its slots and speed.
- `family_loop.py left` moves the unrun jobs of the round before into the queues.

The boxes ran the repo file of commit `490320f`, sha256 `f3111619f531cf8f8d9a3e69cd9530f4971f21d3ee1165e0bd6feaab74446452`. The work log of the take dir has the hashes of the other files.

### What ran

The round ran from 04:10 to 05:28 UTC on boxC (3 workers), boxD (2) and boxA (1, at about one core). The loop ran a cycle every 5 minutes from 04:10, with a stop from 04:47 to 04:56 (a name clash in its near pass, fixed). Each job is one walk or one build, and the workers take the jobs in the order of their names.

| order | list | what it holds | jobs made | jobs run |
|---|---|---|---|---|
| 1 | fault | the skeptic's 795: a walk down, and 854 from it at five cuts and trust radii | 6 | 6 |
| 2 | restack | round 12 near misses built on scipy 1.13.1, built again on 1.18.1 (`mkrestack13.py`) | 65 | 65, and 2 again after a refusal |
| 3 | follow | walks up and down from every new layout, ranked by gain (`family_loop.py`) | 216 | 148 |
| 4 | near2 | second builds of this round's near misses (moved behind the strongest walks at 04:44) | 54 | 52 |
| 5 | restack, wins | round 12 wins built on scipy 1.13.1, built again on 1.18.1 (moved behind the follow walks at 04:34) | 39 | 4 |
| 6 | left | the unrun jobs of round 12: 47 walks, then 484 public donor pairs | 531 | 1 |

At 04:44 the near builds had certified 0 of 30, and the follow walks 3 of 26 steps. So we moved the near builds behind the follow walks of gain above 1e-5.

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| the 795 of the skeptic, walked and built again | down | 2 | 2 | 0 | 1 | 1 | 738 | +1.08e-02 |
| the 795 of the skeptic, walked and built again | up | 9 | 7 | 2 | 1 | 1 | 795 | +3.63e-03 |
| second build of a near miss of this round | down | 24 | 24 | 0 | 1 | 1 | 812 | +6.68e-05 |
| second build of a near miss of this round | up | 28 | 28 | 0 | 3 | 1 | 795 | +6.42e-05 |
| round 12 near miss built again on scipy 1.18.1 | down | 33 | 29 | 4 | 4 | 1 | 809 | +5.22e-05 |
| round 12 near miss built again on scipy 1.18.1 | up | 38 | 34 | 4 | 7 | 2 | 652 795 | +9.87e-05 |
| follow loop: walk from a new design | down | 131 | 120 | 11 | 16 | 12 | 549 696 738 758 795 812 861 867 924 | +3.58e-03 |
| follow loop: walk from a new design | up | 96 | 87 | 9 | 11 | 6 | 649 702 755 874 932 | +1.36e-03 |
| left from round 12: continued walk | up | 1 | 1 | 0 | 0 | 0 | - | +1.18e-04 |

"Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule. Every step is in [`results/family-r13-2026-11-12.tsv`](../results/family-r13-2026-11-12.tsv), with the box and the lane whose layout the walk started from.

### The follow loop by source lane

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| polish-r13 | 35 | 52 | 47 | 4 | 696 867 | +5.02e-03 |
| round 12 held, by family | 17 | 42 | 42 | 10 | 549 702 758 795 861 924 | +5.50e-04 |
| round 12 held, by zones-corner | 18 | 35 | 35 | 1 | - | +2.83e-03 |
| family-r13 (own results) | 10 | 17 | 16 | 2 | 738 | +2.84e-03 |
| border-r13 | 8 | 12 | 7 | 0 | - | +4.81e-03 |
| modules-r13 | 8 | 12 | 12 | 1 | 755 | +1.52e-03 |
| soft-r13 | 6 | 11 | 10 | 4 | 758 812 874 932 | +9.11e-04 |
| the skeptic's 795 (round 12) | 2 | 10 | 8 | 1 | 738 | +3.88e-03 |
| round 12 held, by modules | 6 | 9 | 9 | 0 | - | +1.91e-03 |
| round 12 held, by border | 5 | 9 | 9 | 0 | - | +8.90e-03 |
| round 12 held, by readers | 7 | 7 | 3 | 0 | - | +1.84e-03 |
| round 12 held, by soft | 2 | 6 | 6 | 3 | 549 649 702 | +1.94e-04 |
| readers-r13 | 5 | 5 | 1 | 0 | - | +8.92e-04 |
| corners-r13 | 3 | 5 | 5 | 2 | - | +2.69e-03 |
| round 12 held, by polish | 3 | 5 | 5 | 0 | - | +1.61e-03 |
| the held 738 of round 11 (the 738 -> 795 pair) | 1 | 1 | 1 | 1 | 795 | -9.41e-04 |

"Round 12 held, by X" is a layout of the round 12 file that lane X wrote. The other rows are the take dirs of round 13. Before a walk, the loop read every layout that it saw. 14 of the 57 n that moved in round 12, and most of the polish results, do not read with any reader and get no walk. The gain by source:

- Layouts that the soft lane wrote in this round walk best. 4 of their 11 steps end below the bar, and all 4 certify (758, 812, 874, 932). The held layouts that the soft lane wrote in round 12 (598, 702) give 549, 649 and 702.
- The family results of round 12 walk on. 10 of their 42 steps end below the bar, for 6 certified n. The walk that made each one went on in its own direction in round 12, so these are mostly the other direction.
- The polish lane's results of 751 and 928 give 696 and 867. The modules lane's 700 gives 755 one shell up, for 1.2e-4, the largest gain of the round.
- The corner-zone layouts held since round 12 give nothing this time. Of 35 steps, 1 ends below the bar and 0 certify. Their walks ran in round 12.
- Layouts of the border, readers and corners lanes give 22 steps, and none certifies.

### Near misses

`family_loop.py` builds every step that ends 1e-9 to 2e-4 above its bar once more, from the layout it started from. A walk step gets the cut 0.3 and trust radius 1e-3, and a single build gets 0.7 and 5e-4. 52 of 54 ran. 4 ended below the bar and 2 certified (795 and 812). Neither is the take's result, because other builds of those n are lower. The median second build ends 6.4e-5 above the bar upward and 6.7e-5 downward. The 71 builds of round 12 steps on scipy 1.18.1 certified 3 rows, all in the take (652, 795, 809). A run job now reads as a walk does (`SQ_LOOSE=1`). Without it, 3 of the first restack builds were refused at a start that only the loose reader takes.

### Certified results

| n | step | start | gain on held | gain on the bar |
|---|---|---|---|---|
| 549 | 1 down | the held packing of n = 598 | 1.097e-05 | 1.097e-05 |
| 649 | 1 up | the held packing of n = 598 | 2.093e-07 | 2.093e-07 |
| 652 | 1 up | the held packing of n = 601 | 3.791e-07 | 3.791e-07 |
| 696 | 1 down | the polish result of n = 751 | 8.772e-06 | 8.772e-06 |
| 702 | 1 up | the held packing of n = 649 | 5.027e-07 | 5.027e-07 |
| 738 | 1 down | the 795 of the round 12 skeptic (scipy 1.18.1) | 7.216e-06 | 7.216e-06 |
| 755 | 1 up | the modules result of n = 700 | 1.192e-04 | 9.982e-05 |
| 758 | 1 down | the soft result of n = 815 | 9.553e-05 | 9.375e-05 |
| 795 | 1 up | the held 738 of round 11 (the skeptic's build, scipy 1.18.1) | 3.336e-05 | 3.336e-05 |
| 809 | 1 down | the held packing of n = 868 | 6.143e-09 | 6.143e-09 |
| 812 | 1 down | the soft result of n = 871 | 2.698e-05 | 2.698e-05 |
| 861 | 2 down | the held packing of n = 985 | 6.280e-07 | 6.280e-07 |
| 867 | 1 down | the polish result of n = 928 | 4.212e-06 | 4.824e-07 |
| 874 | 1 up | the soft result of n = 815 | 1.485e-05 | 1.485e-05 |
| 924 | 1 down | the held packing of n = 987 | 1.216e-07 | 1.216e-07 |
| 932 | 1 up | the soft result of n = 871 | 2.498e-05 | 2.498e-05 |
| total | | | 3.4793e-04 | 3.2303e-04 |

"Gain on held" is against `gate/cand-round12-1112a/details.csv`, and `take.tsv` holds it. "Gain on the bar" is against the lowest of held and every other lane's `take-*-r13` at the end of the round. 755, 758 and 867 have lower sides there than held. 652 and 809 come from the builds of round 12 near misses on scipy 1.18.1. 795 comes from the skeptic's build, 738 from the walk down from it, and the other 12 from the follow loop. 861 is built two shells down from the held 985. That 985 is from kmmmvs/squares-in-squares-private-packings (`local_bank.csv`, "Other" terms). `take.tsv` names it. The other rows build on Apache 2.0 or CC BY 4.0 layouts or on our own.

### Parts not run

- 68 follow walks (the low-gain end of the list), 35 builds of round 12 wins on scipy 1.18.1 and 2 near builds.
- 46 of the 47 walks left from round 12 (24 from new designs, 15 continued, 7 reach) and all 484 public donor pairs. The rescan of the public files with `SQ_LOOSE=1` did not run.

### Next runs

1. **Run the follow loop from the first minute of the round,** with the soft, polish and modules lanes' layouts first. They gave 7 of the 12 follow results. `family_loop.py cycle` does it. The work dir needs `deploy/`, `boxes.tsv` and `sources.tsv`.
2. **The 854 from the new 795** at more cuts. Also use `SQ_WALLTOL=4e-2` on every walk that ends at a layout one arm short of flush (15 such ends in round 12).
3. **Keep one scipy on every box,** and use the other one only as a second draw for near misses. The two HiGHS versions differ on about two thirds of the builds, about a third in each direction.
4. The rest of the follow list, the 35 builds of round 12 wins on scipy 1.18.1, then the 46 walks left from round 12, then the public donors.

## Round 14 (2026-11-12, morning)

**Result: 9 n certified below the held file of round 13, for 0.0001473 of score. Against the round 14 takes of the other lanes the gain is 0.0001373. Five of the 9 come from follow walks (651, 874, 932, 935 and 999), and they hold 0.0001466 of the gain. The walks start from layouts that other lanes wrote in this round or that round 13 moved. Second draws of near misses on the same scipy certified 815 (6.9e-7) and 816, 854 and 936 (about 1e-9 each). None of the 97 jonathan1506 layouts gave a result. 67 do not read with this lane's readers. One shell away from the 30 that do, the median step ends 6.6e-3 above the bar. Nothing was submitted from here.**

Words for this section: "held" is `gather/round13-2026-11-12a.csv` (gate dir `gate/cand-round13-1112a`). "The bar" of an n is the lowest of its held side and its side in the take dir of every other lane of round 14 (`take-*-r14`). The loop reads it again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it. `take.tsv` gives the gain against held.

### The jonathan1506 layouts

Round 13 took 97 n from the fault-line notebook of jonathan1506 (`results/round13-best-2026-11-12.tsv` names it as the source of these rows). We tried to walk each of them one shell up and one shell down.

- **30 of the 97 read with `read_any`.** They are the arm layout, with arms that the notebook moved. The follow loop walked them first, in the order of their round 13 gain.
- **67 do not read.** 12 of them are one band of tilted squares from corner to corner (0.0031 of the round 13 gain). They are 403, 444, 487, 629, 680, 733, 788, 845, 904, 905, 965 and 966. In 905, for example, 119 squares at 36 degrees run in chains of 3 along the diagonal, and the grid on each side is upright. 55 are two blocks of stacks on two walls. The stacks of a block are staggered and sit a fraction of a unit off the wall. So no stack spans the strip that the readers ask for (0.0057 of the gain).
- **The readers lane takes most of the 67.** We gave the list to the readers lane at 06:38. Its `read_layers` reads 62 of the 67: the 55 two-block layouts and 7 of the bands. It refuses 629, 680, 733, 905 and 966. It walks the 62 up in its own take dir, so this lane left those walks to it. Its results come back into this loop as new layouts.
- **The walks of the 30 that read: 29 walks from the 30 ran (50 steps, 42 built). Four steps ended 1e-9 to 2e-9 of side under the bar (696, 704, 802 and 861). That is under the 1e-10 rule of score. The median step ends 6.6e-3 above the bar. The notebook tunes each layout to its own n, and one shell away the layout loses.**

A family step for the diagonal band does not exist yet. The band runs at 45 degrees from corner to corner, but its own lattice does not: the chains of 905 step by (0.78, 0.67), at 41 degrees. The notebook keeps the band on the diagonal with slips (the "fault lines"). A shell step must add √2 of band and one row and one column of grid on each side, so it needs a slip of its own. That is the next design for this lane (next runs, item 2).

### The grid strip cut, measured dry

A full row of grid squares and a full column can come out of a layout at once. Then the side falls by exactly 1, and the count by the squares of the row and the column. So (m, k) goes to (m-1, k) at the same f. On 444 n, the held f at (m, k) is smaller than at (m-1, k). The cut would win wherever a layout has such a row and column. `strip_scan.py` (work dir) finds every row and column whose squares can go, with the squares on each side kept apart by at least 1. We ran it over the held file and every layout of the take dirs of rounds 13 and 14. It finds one cut that beats the bar: 845 from the held 904, by 2.0e-9 of side. That is 7e-11 of score, under the 1e-10 rule. Arm layouts never have a full row, because an arm crosses every row. The layouts that do have one already sit on the line. The cut is dry.

### Second draws on the same scipy

Round 13 found that scipy 1.13.1 and 1.18.1 take different paths through the sequential LP on a third of the builds, in both directions. The cause is that an LP here often has several optimal vertices, and the two HiGHS versions pick different ones. Every box runs scipy 1.18.1 now, so that second draw was gone. `SQ_DRAW` brings it back on the same scipy. It changes the order of the HiGHS solvers:

| `SQ_DRAW` | angle LP | exact LP |
|---|---|---|
| unset (as before) | interior point, then dual simplex | HiGHS choice, interior point, dual simplex |
| 1 | dual simplex, then interior point | as unset |
| 2 | as unset | interior point, HiGHS choice, dual simplex |
| 3 | dual simplex, then interior point | interior point, HiGHS choice, dual simplex |

Each solver returns an exact optimum, and every layout is checked legal after each LP, as before. In this round the draws ran on the near misses of rounds 13 and 14: 135 builds. 18 ended below the bar and 9 rows certified, on 815, 816 and 936. The median draw ends 2.0e-5 to 3.7e-5 above the bar. The draws of 816 and 936 certify by about 1e-9 of score each: a near miss that sits 1e-8 above the bar moves by about that much. The draw of 815 from the modules layout of 758 ends 2.0e-5 of side under the bar, and it is the take's 815 (6.9e-7 of score). The large gains of the round came from walks, not draws.

### 854 from the held 795

Round 13 built 854 from the new 795 nine times, and the best ended 3.9e-6 above the bar. This round built it 49 times from the held 795, which is that same layout. The builds cover the 11 distinct cuts of its two arms at three trust radii, then 100 and 150 LP rounds, and the three draws. The median build ends 2.2e-3 above the bar. Four ended within 5e-8 of it, and two went under:

| cut | trust radius | option | side | side less bar |
|---|---|---|---|---|
| 0.65 | 1e-3 | - | 29.720685830 | +4.8e-8 |
| 0.1 | 2e-3 | - | 29.720685798 | +1.6e-8 |
| 0.1 | 2e-3 | `SQ_DRAW=1` | 29.720685751 | -3.1e-8 |
| 0.1 | 3e-3 | - | below the bar | certified, not the best |

The bar is the held 854, 29.720685782. `near_polish.py` (fq with its default and polish flags, then the exact LP, in turn) moved none of the four near layouts: fq finds nothing at these optima. The draw at cut 0.1 certifies by 1.09e-9 of score. It went to the border lane at 07:01 for its 854 -> 913. The border lane had built its 913 already (1.5e-4 below held, at 06:54), on the near 854 layouts that `SQ_KEEPNEAR` kept. The held 854 is the same design, one shell up from the old 795 at cut 0.3. So the new 854 is a hair under it, not a new design.

### Changes to the tool

- **`SQ_DRAW=1`, `2` or `3`** (`family_step.py`, commit `5e89596`): the solver order above.
- **`SQ_KEEPNEAR=1e-4`** (`family_step.py`, commit `757f11a`): `run` keeps the layout of a build that ends less than that above the bar, in `OUTDIR/near`. Before, a run kept only the layouts below the bar. The border lane built its 913 (1.50e-4 to 1.52e-4 below held) on the near 854 layouts that this kept.
- **`family_loop.py cycle --draws`** (commits `807d1dd` and `a365547`): every near miss of the round gets the same step with `SQ_DRAW=1`, `2` and `3`. The jobs are numbered 1150 (at the bar) to 1750 (2e-4 above), so they mix with the follow walks. The near pass and the draw pass skip the n that the lane has already certified.
- Without the options the tool behaves as in round 13. The names and arguments of the functions did not change, so `family_readers.py` still imports the file.

The boxes ran the repo file of commit `5e89596` from 06:53 UTC (sha256 `7d504b34c0e8b37dd39c62a6613b571186c2c3b0bd7d3dfe9ca7e0f355193efc`), and of `757f11a` from 06:32 before it. The work log of the take dir has the hashes of the other files.

### What ran

The round ran from 06:26 to 08:00 UTC on boxC (3 workers), boxD (2) and boxA (1, at about one core, in `work/boxA` on <data>). The loop ran a cycle every 5 minutes from 06:27, with `--draws` from 07:07. Each job is one walk or one build, and the workers take the jobs in the order of their names.

| order | list | jobs made | jobs started |
|---|---|---|---|
| 1 | 854: builds from the held 795 (cuts, trust radii, iterations, draws) | 49 | 49 |
| 1 | 854: fq polish of the near layouts | 4 | 4 |
| 2 | follow walks from new layouts | 246 | 105 |
| 3 | second builds of near misses at another cut | 125 | 39 |
| 3 | second draws of near misses (SQ_DRAW 1 to 3) | 324 | 153 |
| 4 | walk ends one arm short of flush, walked on with SQ_WALLTOL | 17 | 0 |
| 5 | left from round 13: follow walks | 68 | 2 |
| 5 | left from round 13: near builds | 7 | 0 |
| 5 | left from round 13: round 12 wins built on scipy 1.18.1 | 35 | 0 |
| 6 | left from round 12: walks | 46 | 0 |
| 7 | left from round 12: public donor pairs | 484 | 0 |

The near pass and the draw pass built 854 again after it certified, because the bars do not hold the lane's own take. We dropped 21 draws and 16 near builds of 854 from the queues at 07:14. Since 07:16 the loop skips the n of its own take. The leftovers of rounds 12 and 13 did not run: the new work of the round filled the queues.

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| 854 from the held 795 | up | 49 | 49 | 0 | 2 | 2 | 854 | +2.21e-03 |
| follow loop: walk from a new design | down | 64 | 47 | 17 | 2 | 0 | - | +3.52e-03 |
| follow loop: walk from a new design | up | 90 | 74 | 16 | 15 | 8 | 651 815 874 932 935 999 | +2.31e-03 |
| second draw of a near miss (SQ_DRAW=1) | down | 21 | 21 | 0 | 3 | 2 | 816 | +2.25e-05 |
| second draw of a near miss (SQ_DRAW=1) | up | 25 | 25 | 0 | 1 | 0 | - | +2.25e-05 |
| second draw of a near miss (SQ_DRAW=2) | down | 23 | 23 | 0 | 3 | 2 | 816 | +2.03e-05 |
| second draw of a near miss (SQ_DRAW=2) | up | 22 | 22 | 0 | 3 | 2 | 815 936 | +3.70e-05 |
| second draw of a near miss (SQ_DRAW=3) | down | 23 | 23 | 0 | 6 | 1 | 816 | +2.54e-05 |
| second draw of a near miss (SQ_DRAW=3) | up | 21 | 21 | 0 | 2 | 2 | 815 | +2.40e-05 |
| second build of a near miss of this round | down | 15 | 15 | 0 | 0 | 0 | - | +5.83e-06 |
| second build of a near miss of this round | up | 15 | 15 | 0 | 1 | 0 | - | +8.22e-06 |
| left from round 13: follow walk | up | 3 | 2 | 1 | 0 | 0 | - | +1.49e-03 |

"Below the bar" is the tool's own side more than 1e-9 under the bar at the time of the build. "Certified" is the lane's rule. Every step is in [`results/family-r14-2026-11-12.tsv`](../results/family-r14-2026-11-12.tsv), with the box and the lane whose layout the walk started from.

### The follow loop by source lane

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| round 13 held, by jonathan1506 | 29 | 50 | 42 | 4 | - | +6.60e-03 |
| polish-r14 | 12 | 16 | 11 | 2 | 651 935 | +1.75e-03 |
| round 13 held, by family | 7 | 15 | 14 | 4 | 815 932 | +4.22e-04 |
| border-r14 | 11 | 13 | 3 | 1 | - | +2.25e-05 |
| modules-r14 | 6 | 13 | 13 | 2 | 815 874 | +2.43e-03 |
| round 13 held, by zones-corner | 5 | 8 | 8 | 0 | - | +1.63e-03 |
| round 13 held, by soft | 5 | 7 | 6 | 1 | - | +1.31e-03 |
| family-r14 (own results) | 4 | 7 | 6 | 0 | - | +8.08e-04 |
| round 13 held, by border | 4 | 6 | 4 | 0 | - | +1.03e-02 |
| corners-r14 | 3 | 5 | 5 | 1 | 935 | +1.75e-03 |
| round 13 held, by modules | 3 | 4 | 4 | 2 | 999 | -3.79e-05 |
| round 13 held, by readers | 3 | 3 | 0 | 0 | - | - |
| readers-r14 | 2 | 3 | 3 | 0 | - | +1.52e-02 |
| soft-r14 | 2 | 2 | 0 | 0 | - | - |
| round 13 held, by polish | 1 | 2 | 2 | 0 | - | +3.90e-03 |

The polish, modules and corners layouts of this round gave 651, 874 and 935, and the 815 that its draw then took lower. The held layouts of round 13 from the modules and family lanes gave 932 and 999. The 30 readable jonathan1506 layouts gave nothing.

### Certified results

| n | gain on held | gain on the round 14 takes | source |
|---|---|---|---|
| 651 | 1.127e-05 | 1.127e-05 | family_step.py 1 shell(s) up from the polish result of n = 600 (fq quench of modules.py: corner zc8x7-80f9334d … |
| 815 | 6.896e-07 | 6.896e-07 | family_step.py 1 shell(s) up from the modules result of n = 758 (modules.py: corner 758h14.C <held: family_ste … |
| 816 | 1.061e-09 | 1.061e-09 | family_step.py 1 shell(s) down from the round 11 held packing of n = 875 (family_step.py 1 shell(s) up from th … |
| 854 | 1.091e-09 | 1.091e-09 | family_step.py 1 shell(s) up from the held packing of n = 795 (family_step.py 1 shell(s) up from the held pack … |
| 874 | 1.876e-05 | 8.699e-06 | family_step.py 2 shell(s) up from the modules result of n = 758 (modules.py: corner 758h14.C <held: family_ste … |
| 932 | 8.050e-07 | 8.050e-07 | family_step.py 2 shell(s) up from the held packing of n = 812 (family_step.py 1 shell(s) down from the soft re … |
| 935 | 4.551e-05 | 4.551e-05 | family_step.py 1 shell(s) up from the corners result of n = 874 (modules.py: corner zc8x7-123f9729as.C <zone_c … |
| 936 | 9.355e-09 | 1.386e-09 | family_step.py 1 shell(s) up from the held packing of n = 875 (modules.py: corner 875t13.C <t13 n=875: modules … |
| 999 | 7.027e-05 | 7.027e-05 | family_step.py 2 shell(s) up from the held packing of n = 875 (modules.py: corner 875t13.C <t13 n=875: modules … |
| total | 1.4733e-04 | 1.3726e-04 | |

"Gain on held" is against `gate/cand-round13-1112a/details.csv`. `take.tsv` holds it with the full source and licence of each row. "Gain on the round 14 takes" is against the bar at 08:01. 936 and 999 build on the held 875, whose source chain starts at kmmmvs/squares-public-merge-daily. The licence column of `take.tsv` names it.

### Next runs

1. **Run the follow loop with `--draws` from the first minute again.** The walks of other lanes' new layouts gave most of the gain again (table above). Most of the queue did not run: 141 of 246 follow walks, 86 of 125 near builds, 171 of 324 draws, and every leftover list.
2. **A shell step for the diagonal band.** The held file shows where it pays. On the line k = 4 the band holds every n from 629 (m = 25) to 965 (m = 31), at f = 0.5660 down to 0.5621. On the line k = 5 it holds only 905 and 966, at f = 0.5682. The n below them on that line are held by other designs at a larger f: 846 at 0.5838, and 681, 734 and 789 at 0.5914. If the band carries down to 846 at about the f of 905, that is about 5e-4 of score for 846 alone. The step must add (or remove) one grid row and one grid column on each side of the band. It must also add √2 of band, with a slip of the band's own lattice. Five of the band layouts read with no reader of any lane (629, 680, 733, 905 and 966).
3. **The down walks of the 62 layouts** that the readers lane reads, if that lane does not run them.
4. **Draws only where they can pay.** 816, 854 and 936 show it: a near miss within 1e-7 of its bar gives 1e-9 of score at most. Rank the draws by the distance to the bar and the weight of the n. Start them from 1e-7 above.
5. **The leftovers**, in this order. First the walk ends with `SQ_WALLTOL` (17) and the round 13 follow walks (68). Then the round 12 wins on scipy 1.18.1 (35) and the round 12 walks (46). Last the 484 public donor pairs and the `SQ_LOOSE=1` rescan.

## Round 15 (2026-11-12, mid-morning)

**Result: 4 n certified below the held file of round 14, for 1.39e-7 of score. Against the round 15 takes of the other lanes at 10:30 the gain is 9.8e-8. Each of the 4 is one shell from a layout that moved in this round, and each gains less than 5e-8. 812 and 871 come from second draws, 912 and 984 from walks. The modules, corners and border lanes wrote their takes after 10:08, so the walks of their layouts had about 15 minutes and found nothing. Nothing was submitted from here.**

Words for this section: "held" is `gather/round14-2026-11-12a.csv` (gate dir `gate/cand-round14-1112a`). "The bar" of an n is the lowest of its held side and its side in the take dir of every other lane of round 15 (`take-*-r15`). The loop reads it again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it. `take.tsv` gives the gain against held.

### What ran

The round ran from 08:56 to 10:30 UTC. The workers ran on boxC (3) and boxD (2). boxA ran one worker in `work/boxA` on <data> until 09:55. From then on the loop's certify pass took about 290 s of each 300 s cycle there, so boxA ran the loop only. The loop started with `--draws` at 08:57 and ran a cycle every 5 minutes.

| order | list | jobs made | dropped | jobs started |
|---|---|---|---|---|
| 1 | follow walks from new layouts | 116 | 0 | 98 |
| 2 | second builds of near misses at another cut | 76 | 0 | 76 |
| 2 | second draws of near misses (`SQ_DRAW` 1 to 3) | 96 | 0 | 91 |
| 0 | fq quench of the certified files | 8 | 0 | 8 |
| 3 | down walks of jonathan1506 layouts with `family_readers.py` | 45 | 37 | 8 |
| 4 | left from round 14: walk ends with `SQ_WALLTOL` | 17 | 0 | 13 |
| 5 | left from round 14: round 13 follow walks | 66 | 0 | 9 |
| 6 | left from round 14: round 12 wins on scipy 1.18.1 | 35 | 0 | 1 |
| 7 | left from round 14: round 12 walks | 46 | 0 | 2 |

The jobs are dealt in the order of their names. The follow walks and the draws ran first. The leftovers of rounds 12 to 14 ran in the slots that the new work left free.

### The jonathan1506 down walks

The readers lane wrote at 08:56 that it runs 71 down walks from the round 14 held file. We agreed to run the down walks of the other 45 of the 62 layouts that `read_layers` reads. At 09:00 the readers lane pointed out that its round 14 had already walked all 45 down, from the round 13 held file (`results/readers-r14-2026-11-12.tsv` has the rows). Only 644, 694, 867 and 914 of the 45 changed in round 14. So we dropped 41 of the 45 jobs. Four of the 41 had already run on boxA (543, 545, 695 and 978). The 8 walks that ran built 15 steps. None came near the bar: the median step ends 1.07e-2 of side above it.

### The follow loop

The 48 n that moved in round 14 gave 37 layouts that read and 74 walks. The other 11 do not read with `read_any` (594, 694, 981, 597, 986, 707, 595, 701, 502, 927 and 604). Most of them are layer layouts of the readers lane, and that lane walks them.

The takes of the other lanes came late. By 10:00 only the polish, readers and soft lanes had a `take.tsv`. Of their 22 layouts, 6 read: polish 507, 812, 865 and 975, and readers 811 and 868. The others are corner, border or layer layouts. The corners lane wrote its take at about 10:10, and the border and modules lanes at about 10:15. That left 15 minutes for their walks. We moved the walks of modules 921 and 587 and corners 983 to the head of the queue on boxC. The border 923 does not read.

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| round 14 held, by polish | 21 | 36 | 32 | 3 | - | +2.83e-03 |
| round 14 held, by family | 16 | 30 | 30 | 1 | - | +2.39e-03 |
| round 14 held, by modules | 12 | 26 | 26 | 3 | - | +2.43e-03 |
| round 14 held, by readers | 12 | 22 | 22 | 4 | - | +4.00e-04 |
| family-r15 (own results) | 9 | 18 | 18 | 4 | 912 984 | +1.39e-03 |
| polish-r15 | 11 | 16 | 16 | 3 | 912 | +2.17e-03 |
| round 14 held, by jonathan1506 | 8 | 16 | 15 | 0 | - | +1.07e-02 |
| readers-r15 | 4 | 5 | 2 | 0 | - | +6.66e-04 |
| round 14 held, by border | 3 | 4 | 2 | 0 | - | +1.60e-02 |
| modules-r15 | 3 | 4 | 4 | 0 | - | +1.65e-03 |
| round 14 held, by zones-corner | 1 | 2 | 2 | 0 | - | +4.52e-03 |
| corners-r15 | 1 | 2 | 2 | 0 | - | +2.01e-03 |

The up steps end at a median of 1.1e-3 of side above the bar and the down steps at 2.2e-3. The two wins of the walks are 912 and 984. Both start from a layout that this round had moved already. 912 is one shell down from our own 975, and 984 is one shell up from our own 921. Each gains less than 5e-8 of score.

### Second draws from 1e-7 above the bar

`family_loop.py` now makes a draw only for a near miss at 1e-7 to 2e-4 above its bar (commit `31154c2`). It ranks the draws by the distance to the bar over the weight of n in the score. The weight of n is the derivative of the score by the side, 1/√n. So `draw_rank` uses dv · √(n/300) and maps 1e-7 to job 1150 and 2e-4 to job 1750. In round 14 a draw closer than 1e-7 gave about 1e-9 of score at most. This round made 96 draw jobs and 91 of them ran. 16 draws ended below the bar at the time of the build, and 4 rows certified on 812 and 871. The draws of 871 one shell up from the polish 812 and of 812 one shell down from our own 871 hold 4.7e-8 and 2.6e-8 of score. The median draw ends 2e-6 to 6e-5 of side above the bar.

### Fq quench of the certified files

The corners lane found at 09:20 that a quench of the certified file can find gains that a quench of the raw build misses. So every certified file of this take got one quench from its certified csv (`near_polish.py`: fq with its default and polish flags, then the exact LP). The jobs ran at the head of boxD's queue. 8 files got the quench. It moved two of them: 912 by 1.3e-7 of side and 975 by 1.9e-7. It did not move 812, 871, 921 or 984, nor the final 812, 871 and 912.

The polish lane quenches the takes of the other lanes too. It took our 812 (2.491e-8 of score) and certified it 1.3e-10 lower in its own take. It did the same with our 912 and 975 later in the round. Its versions win at those n, so the assembler takes them from the polish take.

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| follow loop: walk from a new design | down | 100 | 96 | 4 | 10 | 3 | 912 | +2.23e-03 |
| follow loop: walk from a new design | up | 65 | 60 | 5 | 8 | 1 | 984 | +1.10e-03 |
| second draw of a near miss (SQ_DRAW=1) | down | 22 | 22 | 0 | 3 | 1 | 812 | +5.65e-05 |
| second draw of a near miss (SQ_DRAW=1) | up | 12 | 12 | 0 | 1 | 0 | - | +2.25e-05 |
| second draw of a near miss (SQ_DRAW=2) | down | 23 | 23 | 0 | 3 | 0 | - | +2.33e-05 |
| second draw of a near miss (SQ_DRAW=2) | up | 13 | 13 | 0 | 3 | 1 | 871 | +2.07e-06 |
| second draw of a near miss (SQ_DRAW=3) | down | 21 | 21 | 0 | 3 | 0 | - | +2.04e-05 |
| second draw of a near miss (SQ_DRAW=3) | up | 12 | 12 | 0 | 3 | 2 | 871 | +4.09e-06 |
| second build of a near miss of this round | down | 18 | 18 | 0 | 1 | 0 | - | +7.80e-05 |
| second build of a near miss of this round | up | 14 | 14 | 0 | 0 | 0 | - | +1.09e-05 |
| down walk of a jonathan1506 layout changed in round 14 (family_readers.py) | down | 16 | 15 | 1 | 0 | 0 | - | +1.07e-02 |
| left from round 14: round 13 follow walk | down | 9 | 9 | 0 | 0 | 0 | - | +3.59e-03 |
| left from round 14: round 13 follow walk | up | 2 | 1 | 1 | 0 | 0 | - | +2.09e-04 |
| left from round 14: walk end walked on with SQ_WALLTOL | down | 6 | 4 | 2 | 0 | 0 | - | +1.71e-02 |
| left from round 14: walk end walked on with SQ_WALLTOL | up | 7 | 4 | 3 | 0 | 0 | - | +2.41e-02 |
| left from round 14: round 12 win built on scipy 1.18.1 | down | 1 | 1 | 0 | 0 | 0 | - | +2.57e-04 |
| left from round 14: round 12 walk | down | 3 | 2 | 1 | 0 | 0 | - | +3.81e-03 |

"Below the bar" is the tool's own side more than 1e-9 under the bar at the time of the build. "Certified" is the lane's rule, against the bars at the end of the round. Every step is in [`results/family-r15-2026-11-12.tsv`](../results/family-r15-2026-11-12.tsv), with the box and the lane whose layout the walk started from.

### Certified results

| n | gain on held | gain on the round 15 takes | source |
|---|---|---|---|
| 812 | 2.564e-08 | 6.072e-10 | family_step.py 1 shell(s) down from family_step.py 1 shell(s) up from family_step.py 1 shell(s) down from the  |
| 871 | 4.736e-08 | 4.736e-08 | family_step.py 1 shell(s) up from the polish result of n = 812 (fq quench of family_step.py 1 shell(s) down fr |
| 912 | 4.670e-08 | 3.117e-08 | family_step.py 1 shell(s) down from family_step.py 1 shell(s) up from family_step.py 1 shell(s) down from the  |
| 984 | 1.913e-08 | -4.870e-06 | family_step.py 1 shell(s) up from family_step.py 1 shell(s) down from the held packing of n = 984 (modules.py: |
| total | 1.3884e-07 | 9.8270e-08 | |

"Gain on held" is against `gate/cand-round14-1112a/details.csv`. `take.tsv` holds it with the full source and licence of each row. "Gain on the round 15 takes" is against the bar at 10:30. The take held 921 (5.1e-7) and 975 (2.1e-7) for a time. The modules 921 and the polish 975 then went lower, so both left the take.

### Changes to the tool

- **Draws from 1e-7 above the bar** (`family_loop.py`, commit `31154c2`): `draw_pass` takes a floor (1e-7) and ranks the draws with `draw_rank`.
- **Out dirs of `family_readers.py` walks** (commit `a53868c`): the loop leaves the out dirs named `out-j*` to the take of `family_readers.py`. Their rows have other columns, and the near pass of the loop stopped on them at 09:03.
- **No second build of a draw** (commit `49b25e6`): the near pass skips the out dirs of draws. Before, it built the same near miss once from each draw dir, so the same build ran three times (809 from the readers 868 at 10:10).
- `family_step.py` did not change. Its function names and arguments are as before, so `family_readers.py` still imports it. The boxes ran it from origin/main at `31154c2` (the file is from `5e89596`, sha256 `7d504b34c0e8b37dd39c62a6613b571186c2c3b0bd7d3dfe9ca7e0f355193efc`). The work log of the take dir has the hashes of the other files.

### Next runs

1. **Run the follow loop after the other lanes write their takes.** The walks of new layouts gave nearly all of the gain in rounds 13 and 14. In this round the takes of modules, corners and border came after 10:08, and the loop stopped at 10:25. Either those lanes write an interim `take.tsv` early, as the polish and readers lanes did, or the family round starts 30 to 45 minutes after them.
2. **Cache the certification.** The certify pass runs floatsafe again on every raw file at every cycle. On boxA, at a load of about 35, a cycle took 200 to 290 s, so new layouts waited up to 5 minutes for their walks. A cache of the verdict by the hash of the file and the bar removes most of that time.
3. **Retire the leftover lists.** The 28 leftover steps that ran this round all ended above the bar, at a median of 2.1e-4 to 2.4e-2 of side. They are walk ends, round 13 follow walks, and round 12 wins and walks. The jonathan1506 down walks are all done (round 14 of the readers lane, and 644, 694, 867 and 914 here).
4. **Keep the draws from 1e-7 up.** They gave half of this small take (812 and 871). A step that ends within 1e-8 of its bar is still not worth a draw.

## Round 16 (2026-11-12, midday)

**Result: 10 n certified below the held file of round 15, for 1.785e-4 of score. Against the round 16 takes of the other lanes at 13:50 the gain is 1.211e-4. Nearly all of it comes from walks and draws of layouts that the soft, modules, corners and polish lanes wrote in this round, often within minutes. The cached certification takes 1 to 57 s of a cycle, against 200 to 290 s in round 15. Nothing was submitted from here.**

Words for this section: "held" is `gather/round15-2026-11-12a.csv` (gate dir `gate/cand-round15-1112a`). "The bar" of an n is the lowest of its held side and its side in every other take dir of the round. These are the `take-*-r16` dirs and the harvest take dirs that a line of the handoff log names (`take-harvest-2026-11-12m`, `n` and `o`). The loop reads the bars again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it.

### What ran

The round ran from 12:05 to 13:50 UTC. The workers ran on boxC (3) and boxD (2). boxA ran the loop only. The loop ran with `--draws` from 12:09 to 13:49, a cycle every 5 minutes. Steps stopped at 13:42. The leftover lists of rounds 12 to 14 are retired: no `family_loop.py left` ran.

| order | list | jobs made | jobs started |
|---|---|---|---|
| 0 | fq quench of the certified files | 21 | 21 |
| 1 | follow walks from new layouts | 146 | 115 |
| 2 | second builds of near misses at another cut | 18 | 18 |
| 2 | second draws of near misses (`SQ_DRAW` 1 to 3) | 99 | 96 |

### The certification cache

The floatsafe verdict of a file depends on its rows only. `floatsafe.work` gives the score and the dilation e, and the rows as written are `as_float_rows(rows, e)`. The bar only decides whether that score is a win. So `family_loop.py` keeps the score and e in `work/certcache.tsv`, keyed by the hash of the rows, and compares the score with the bar of each cycle.

- `family_loop.py ctake` runs `family_step.py take` unchanged, with `floatsafe.work` answered from the cache.
- Before each take, `prefill` sends the files that the cache does not hold to the box with the lowest load per core. There `family_loop.py fill` scores them in one process. In the 15 cycles that had new files, it chose boxD 12 times and boxA 3 times. boxC ran at a load of 22 to 52 from the other lanes.
- A score from another box that beats its bar is scored again on boxA before it is kept.

The control: on the 43 raw files of round 15, the cached take wrote the same take files, byte for byte, as `family_step.py take`. A warm pass took 0.9 s, a cold pass 75 s, and the plain take 83 s. With all entries marked as from another box, it scored the 12 winning files again and still wrote the same files. The remote fill on boxD gave the same hashes and scores as boxA. In this round the certify step of a cycle took a median of 29 s (1 to 57 s), most of it the fill. A whole cycle took a median of 115 s.

### The follow loop

22 of the 48 n that moved in round 15 read with `read_any`, and each got a walk up and a walk down. The other 26 do not read. They are layer layouts of jonathan1506 and the readers lane, the border 923, and the harvest layouts. The handoff log at 12:16 left them and every layer-reader walk to the readers lane.

The loop also reads the `near/` folder of each take dir and the handoff log. No lane wrote a `near/` folder this round. From the handoff log it took the harvest take dirs (as bars and starts) and the csv files named in lines to "family" or "all". One layout gets one walk, by the hash of its rows, whichever lane names it.

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| family-r16 (own results) | 18 | 37 | 36 | 9 | 549 598 | +2.21e-03 |
| modules-r16 | 14 | 28 | 28 | 5 | 549 598 860 | +2.36e-03 |
| round 15 held, by jonathan1506 | 14 | 20 | 18 | 1 | - | +9.33e-03 |
| round 15 held, by polish | 11 | 16 | 16 | 3 | - | +1.12e-03 |
| corners-r16 | 6 | 14 | 14 | 1 | 704 | +4.37e-03 |
| soft-r16 | 8 | 12 | 12 | 7 | 598 647 755 | -5.47e-04 |
| round 15 held, by other | 5 | 8 | 8 | 0 | - | +7.25e-03 |
| harvest-m-r16 | 4 | 8 | 8 | 1 | - | +6.02e-03 |
| polish-r16 | 5 | 8 | 8 | 2 | 647 755 | +3.36e-03 |
| round 15 held, by family | 4 | 7 | 7 | 1 | - | +5.40e-04 |
| readers (handoff log) | 3 | 6 | 4 | 0 | - | +2.38e-03 |
| border-r16 | 2 | 4 | 4 | 0 | - | +1.53e-02 |
| round 15 held, by zones-corner | 1 | 2 | 2 | 0 | - | +2.01e-03 |
| round 15 held, by readers | 2 | 2 | 0 | 0 | - | - |
| corners (handoff log) | 1 | 2 | 2 | 0 | - | +8.58e-03 |
| readers-r16 | 1 | 2 | 2 | 0 | - | +1.32e-03 |
| border (handoff log) | 1 | 2 | 2 | 0 | - | +1.54e-02 |

The walks of this round's soft layouts end at a median of 5.5e-4 of side below the bar. 7 of 12 steps end below it. The walks of the round 15 held layouts gave nothing that holds.

The gains come from a chain of lanes on one family of layouts:

- The modules lane built a corner 549, and the soft lane took it 5.7e-5 below held.
- Our walk took it up to 598 and 649, and a walk back down gave a 549 7.0e-5 below held.
- The modules lane took our 649 lower, and the soft lane built a 700 from a modules corner on our 598.
- Walks and draws from that 700 gave 755 (up) and 647 and 596 (down). The soft lane then took our 596 lower again.

Each lane wrote its take and a line in the handoff log as soon as a layout certified. So the loop made the walks of a new layout at its next cycle, at most 5 minutes later.

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| follow loop: walk from a new design | down | 105 | 102 | 3 | 14 | 9 | 549 598 647 860 | +4.03e-03 |
| follow loop: walk from a new design | up | 73 | 69 | 4 | 16 | 7 | 598 704 755 | +1.92e-03 |
| second draw of a near miss (SQ_DRAW=1) | down | 24 | 24 | 0 | 7 | 5 | 549 598 687 912 | +1.57e-04 |
| second draw of a near miss (SQ_DRAW=1) | up | 10 | 10 | 0 | 3 | 3 | 598 755 | +2.98e-07 |
| second draw of a near miss (SQ_DRAW=2) | down | 22 | 22 | 0 | 5 | 3 | 549 598 | +1.57e-04 |
| second draw of a near miss (SQ_DRAW=2) | up | 10 | 10 | 0 | 3 | 3 | 598 755 | +5.53e-06 |
| second draw of a near miss (SQ_DRAW=3) | down | 21 | 21 | 0 | 6 | 3 | 549 598 | +1.81e-05 |
| second draw of a near miss (SQ_DRAW=3) | up | 10 | 10 | 0 | 4 | 4 | 598 751 755 | +3.50e-09 |
| second build of a near miss of this round | down | 14 | 14 | 0 | 0 | 0 | - | +9.22e-05 |
| second build of a near miss of this round | up | 4 | 4 | 0 | 0 | 0 | - | +5.53e-06 |

"Below the bar" is the tool's own side more than 1e-9 under the bar at the time of the build. "Certified" counts the rows that certify against the bars at 13:50. Several rows can certify the same n. Every step is in [`results/family-r16-2026-11-12.tsv`](../results/family-r16-2026-11-12.tsv), with the box and the lane whose layout the walk started from.

### Certified results

| n | gain on held | gain on the round 16 takes | made by | start |
|---|---|---|---|---|
| 549 | 7.004e-05 | 1.272e-05 | walk | 1 down from our 598 (1 up from the soft 549) |
| 598 | 4.145e-05 | 4.145e-05 | draw 1 | 1 up from our 549 |
| 755 | 3.285e-05 | 3.285e-05 | draw 2 | 1 up from the polish 700 (fq quench of the soft 700) |
| 860 | 1.818e-05 | 1.818e-05 | walk | 1 down from the modules 921 |
| 647 | 1.480e-05 | 1.480e-05 | walk | 1 down from the soft 700 |
| 704 | 7.714e-07 | 7.714e-07 | walk | 2 up from the corners 600 |
| 751 | 3.447e-07 | 3.447e-07 | draw 3 | 1 up from the harvest 696 (jazivxt/boxed-in) |
| 812 | 2.119e-08 | 2.119e-08 | draw, then fq quench | 1 down from the held 871 |
| 687 | 7.784e-09 | 7.784e-09 | draw 1, then fq quench | 1 down from the held 742 (prvsiyan) |
| 912 | 1.055e-10 | 1.055e-10 | draw 1 | 1 down from the readers 975 |
| total | 1.7847e-04 | 1.2114e-04 | | |

"Gain on held" is against `gate/cand-round15-1112a/details.csv`. `take.tsv` holds it with the full source and licence of each row. "Gain on the round 16 takes" is against the bar at 13:50. Each take file was checked again with `kaggle_metric`, as written and after the pandas parse. All are ok, with a clearance of 5.0e-11 or more.

The 912 row starts from the readers 975, which builds on the held 912 of round 9 (kmmmvs local_bank, "Other" terms). It is worth 1.1e-10 of score, so the assembler can leave it out. For a time the take also held 921, 984, 649, 975 and 596. Other lanes then went lower at each of them, so they left the take (the files are in `work/dropped/`).

The fq quench of each certified file (21 jobs, all ran) moved 687 and 812 below the draws that made them. It did not move the others.

### Changes to the tool

All in `family_loop.py`. `family_step.py` did not change, so `family_readers.py` still imports it with the same names and arguments.

- **Certification cache** (commit `b9688d0`): `ctake`, `fill`, `prefill`, `certcache.tsv`, as above.
- **Bars and starts from the handoff log** (`b9688d0`): `handoff_takes` adds every take dir that a line of the log names by its `take.tsv` (the harvest passes). `extra_cands` adds the `near/` folders of the take dirs and the csv files named in lines to "family" or "all".
- **One walk per layout** (`b9688d0`): the follow pass keys a layout by the hash of its rows. Two lanes that name the same layout get one walk.
- **Handoff line and quench per certified layout** (`b9688d0`): each new certified layout gets one line in the handoff log and one fq quench from its certified csv (jobs 01xx).
- **Time stamps with a date** (commit `1adef67`): a handoff line that starts with a date and a time now parses.
- The boxes ran `family_step.py` from origin/main at `88b34a8` (the file is from `5e89596`, sha256 `7d504b34c0e8b37dd39c62a6613b571186c2c3b0bd7d3dfe9ca7e0f355193efc`). The work log of the take dir has the hashes of the other files.

### Next runs

1. **Keep the lanes on one family together.** The chain of soft, modules and family on the 549, 598, 649 and 700 line gave most of this round. Each lane took the others' new layouts within one or two cycles. Start the follow loop in the first minutes again, and keep the interim takes and the handoff lines.
2. **Hand over the layouts that do not read.** Our 596 and 755 do not read with `read_any`, nor does the soft 596. So the walks of the line 547, 596, 647, 700, 755, 812 stop there. On the line 502, 549, 598, 649, 702, 757 the walks ran to 502, 702 and 757 and ended 3.9e-4 to 3.9e-3 of side above the bar. The layer reader of the readers lane may take 596 and 755. The loop can write a handoff line for each own result that does not read.
3. **More slots near the end.** 31 follow walks and 3 draws never started: at 13:42 the queues held 19 jobs on boxC and 13 on boxD. The workers ran at a full CPU share, so the 5 slots were the limit in the last 20 minutes.
4. **The 26 moved n that `read_any` refuses** stay with the readers lane and its layer reader.

## Round 17 (2026-11-12, afternoon)

**Result: 15 n certified below the held file of round 16, for 1.907e-03 of score. Against the other round 17 take dirs at 20:03 the gain is 7.361e-04. Against the round 17 file (`gather/round17-2026-11-12a.csv`, assembled from the take dirs at 17:42) the take adds 9.248e-04 on 11 n. Nearly all of it is one shell up or down from the new two-arm designs at m 28 to 31. These are the twoshort layouts, the stair-c corner and the corners lane's hops of it. The round 17 file is the held file since its submission at 18:54 (22.1635211736 on Kaggle). Nothing was submitted from here.**

Words for this section: "held" is `gather/round16-2026-11-12a.csv` (gate dir `gate/cand-round16-1112a`). "The bar" of an n is the lowest of its held side and its side in every other `take-*-r17` dir and every take dir a handoff line names. The loop reads the bars again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it.

### What ran

The round ran in four parts, because boxA went down once and this lane's agent stopped three times.

| UTC | what happened |
|---|---|
| 15:15 to 16:08 | Workers on boxC (3) and boxD (2), the loop on boxA, a cycle every 5 minutes. From 15:51 the walks of the stair-b and stair-c layouts ran first too. |
| 16:15 | boxA panicked with its memory full (another project's git processes) and the loop died after its 16:08 cycle. The workers ran on to the step deadline of 16:46. Their rows stayed on the boxes. |
| 17:45 | Restart. The step deadline moved to 19:30 and boxE got 1 worker. The first cycle collected the rows of 16:08 to 16:46 and kept 419 and 871 from them. |
| 17:52 to 18:03 | The agent stopped. The workers and the loop ran on, and the restart adopted them. |
| 18:21 | The loop restarted with `--misses 1`, and the walk jobs in the queues changed the same way. |
| 19:05 to 19:09 | The agent stopped again, and the workers and the loop ran on. The restart adopted them. It moved the loop's end to 20:05 and the step deadline to 20:00, because the round got 30 more minutes. |
| 20:03 | The loop's last cycle. `work/final.sh` stopped every worker, collected and certified once more, and checked the copies. |

| order | list | jobs made | dropped | jobs started |
|---|---|---|---|---|
| 0 | fq quench of the certified files | 39 | 0 | 39 |
| 1 | follow walks from new layouts | 452 | 0 | 419 |
| 2 | second builds of near misses at another cut | 50 | 0 | 50 |
| 2 | second draws of near misses (SQ_DRAW 1 to 3) | 261 | 0 | 174 |

### The new designs: one shell at a time

The twoshort lane built two-arm layouts at m 28 to 31, with a staircase corner (`twoshort_corner.py`). The stair-c lane carried that corner to other n, and the corners lane hopped it. The loop walked each of these layouts first, both ways (`--first twoshort stair-b stair-c`, jobs 1000 to 1099).

| targets | direction | shells | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|
| n 300 to 789 | down | 1 | 79 | 77 | 6 | 335 705 | +3.43e-03 |
| n 300 to 789 | down | 2 | 46 | 46 | 0 | - | +8.61e-03 |
| n 300 to 789 | down | 3+ | 8 | 8 | 0 | - | +1.24e-02 |
| n 300 to 789 | up | 1 | 55 | 54 | 4 | - | +5.95e-04 |
| n 300 to 789 | up | 2 | 18 | 17 | 1 | - | +1.93e-03 |
| n 300 to 789 | up | 3+ | 4 | 4 | 0 | - | +5.29e-03 |
| n 790 to 1000 | down | 1 | 138 | 132 | 31 | 812 852 858 859 861 910 920 | +2.16e-03 |
| n 790 to 1000 | down | 2 | 61 | 60 | 6 | 800 812 858 859 | +7.51e-03 |
| n 790 to 1000 | down | 3+ | 5 | 5 | 1 | 800 | +7.52e-03 |
| n 790 to 1000 | up | 1 | 93 | 90 | 23 | 811 852 871 912 920 973 | +9.23e-04 |
| n 790 to 1000 | up | 2 | 40 | 37 | 4 | - | +4.92e-03 |
| n 790 to 1000 | up | 3+ | 7 | 7 | 0 | - | +3.08e-03 |

At n 790 and above, a step of one shell is the one that works, up or down. One shell down put 31 of 138 steps below the bar and certified 812 852 858 859 861 910 920. One shell up put 23 of 93 below the bar and certified 811 852 871 912 920 973. A step of two or more shells rarely ends below the bar: 10 of 101 steps of two shells and 1 of 12 steps of three or more.

The certified layouts form chains across lanes, as in round 16:

- Twoshort 793 one shell up gave 852, 4.2e-3 of side below the bar. Twoshort 851 one shell up gave 912.
- The corners lane built 910 and 860 from a hopped corner. Our walks took 910 up to 973 and 860 up to 921 and 984. Walks down from 984 then gave 921 and 860 lower again.
- The border lane put one border on our 860 and our 921 (its 919 and 982). Our walks down from those gave 858 and 919.
- The border lane's 983 gave 920, 859 and 800, one, two and three shells down. The modules 754 one shell up gave 811.
- The layer reader of the readers lane took the corners 984 one shell down, to a 921 below ours for a time. Walks from the readers 921 and 984 also certified 860.

A walk used to go on after a step that did not end below the bar (`--misses 2`). After a miss, 132 steps put 2 below the bar and took 8534 s of slot time. After a step below the bar, 57 steps put 10 below the bar for 5140 s. From 18:21 the walks stop at their first miss (`--misses 1`), and the walk jobs already queued were changed the same way.

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| twoshort-r17 | 41 | 64 | 64 | 11 | 852 912 | +8.26e-03 |
| family-r17 (own results) | 39 | 62 | 58 | 18 | 800 812 858 859 861 871 910 973 | +6.04e-04 |
| modules-r17 near/ | 34 | 57 | 57 | 2 | - | +1.99e-03 |
| corners-r17 | 30 | 46 | 46 | 5 | 973 | +3.07e-03 |
| stair-c-r17 near/ | 36 | 46 | 46 | 3 | - | +6.39e-03 |
| stair-c-r17 | 22 | 34 | 34 | 4 | 861 920 | +3.81e-03 |
| round 16 held, by family | 18 | 31 | 28 | 3 | - | +4.03e-03 |
| midm (handoff log) | 21 | 29 | 25 | 4 | - | +1.69e-03 |
| midm-r17 | 19 | 24 | 23 | 2 | 335 705 | +3.53e-03 |
| readers-r17 | 16 | 23 | 23 | 7 | 858 861 | +4.82e-04 |
| modules-r17 | 15 | 19 | 18 | 3 | 811 | +4.08e-04 |
| polish-r17 | 12 | 16 | 16 | 2 | - | +6.26e-03 |
| round 16 held, by modules | 8 | 15 | 15 | 1 | - | +1.08e-03 |
| round 16 held, by zones-corner | 6 | 15 | 15 | 2 | 812 | +4.33e-03 |
| classfill-r17 | 10 | 14 | 14 | 0 | - | +4.89e-03 |
| border-r17 | 8 | 11 | 7 | 6 | 800 858 859 920 | -2.07e-03 |
| stair-c (handoff log) | 5 | 9 | 9 | 0 | - | +3.69e-03 |
| round 16 held, by other | 4 | 8 | 8 | 1 | - | +6.24e-03 |
| soft-r17 | 4 | 7 | 7 | 1 | - | +7.03e-03 |
| round 16 held, by polish | 4 | 6 | 6 | 1 | - | +3.01e-03 |
| modules (handoff log) | 4 | 6 | 6 | 0 | - | +2.88e-03 |
| stair-b-r17 | 2 | 2 | 2 | 0 | - | +1.06e-02 |
| round 16 held, by border | 1 | 2 | 2 | 0 | - | +1.53e-02 |
| round 16 held, by readers | 1 | 2 | 2 | 0 | - | +4.81e-03 |
| classfill (handoff log) | 2 | 2 | 2 | 0 | - | +1.14e-03 |
| readers (handoff log) | 2 | 2 | 2 | 0 | - | +4.66e-03 |
| corners (handoff log) | 1 | 2 | 2 | 0 | - | +1.38e-02 |

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| follow loop: walk from a new design | down | 337 | 328 | 9 | 44 | 20 | 335 705 800 812 852 858 859 861 910 920 | +4.50e-03 |
| follow loop: walk from a new design | up | 217 | 209 | 8 | 32 | 9 | 811 852 871 912 920 973 | +1.01e-03 |
| second draw of a near miss (SQ_DRAW=1) | down | 18 | 18 | 0 | 6 | 4 | 812 852 858 | +2.89e-07 |
| second draw of a near miss (SQ_DRAW=1) | up | 39 | 39 | 0 | 6 | 3 | 871 920 973 | +3.36e-06 |
| second draw of a near miss (SQ_DRAW=2) | down | 18 | 18 | 0 | 8 | 5 | 812 851 852 858 | +2.20e-07 |
| second draw of a near miss (SQ_DRAW=2) | up | 42 | 42 | 0 | 4 | 3 | 871 920 973 | +5.85e-06 |
| second draw of a near miss (SQ_DRAW=3) | down | 20 | 20 | 0 | 7 | 5 | 812 851 852 858 | +1.86e-06 |
| second draw of a near miss (SQ_DRAW=3) | up | 42 | 42 | 0 | 7 | 2 | 871 973 | +2.38e-06 |
| second build of a near miss of this round | down | 18 | 18 | 0 | 3 | 1 | 851 | +9.97e-05 |
| second build of a near miss of this round | up | 32 | 32 | 0 | 4 | 1 | 973 | +2.38e-05 |

"Below the bar" is the tool's own side more than 1e-9 under the bar at the time of the build. "Certified" counts the rows that certify against the bars at 20:03. Several rows can certify the same n. Every step is in [`results/family-r17-2026-11-12.tsv`](../results/family-r17-2026-11-12.tsv), with the box and the lane whose layout the walk started from.

### Certified results

| n | gain on held | gain on the other takes | gain on the round 17 file | start |
|---|---|---|---|---|
| 861 | 2.891e-04 | 5.856e-06 | 1.924e-04 | 1 down from the readers 922 |
| 912 | 2.767e-04 | 4.303e-05 | 4.303e-05 | 1 up from the twoshort 851 |
| 973 | 2.393e-04 | 1.949e-05 | - | 1 up from our layout that began at the corners 910 |
| 852 | 2.341e-04 | 1.423e-04 | - | 1 up from the twoshort 793 |
| 920 | 2.016e-04 | 1.543e-04 | 2.016e-04 | 1 down from the border 983 |
| 851 | 1.767e-04 | 4.443e-07 | 9.457e-05 | 1 down from our layout that began at the twoshort 851 |
| 811 | 1.461e-04 | 1.461e-04 | 1.461e-04 | 1 up from the modules 754 |
| 859 | 1.306e-04 | 9.811e-05 | 1.306e-04 | 2 down from the border 983 |
| 910 | 8.685e-05 | 8.849e-07 | - | 1 down from our layout that began at the corners 910 |
| 800 | 7.791e-05 | 7.791e-05 | 7.791e-05 | 3 down from the border 983 |
| 858 | 2.705e-05 | 2.705e-05 | 2.705e-05 | 1 down from our layout that began at the border 982 |
| 871 | 6.111e-06 | 6.111e-06 | 6.111e-06 | 1 up from our layout that began at the held 932 |
| 705 | 5.407e-06 | 5.407e-06 | 5.407e-06 | 1 down from the midm 760 |
| 335 | 4.641e-06 | 4.641e-06 | - | 1 down from the midm 374 |
| 812 | 4.453e-06 | 4.453e-06 | 2.718e-08 | 1 down from our layout that began at the held 932 |
| total | 1.9066e-03 | 7.3608e-04 | 9.2482e-04 | |

"Gain on held" is against `gate/cand-round16-1112a/details.csv`. `take.tsv` holds it with the full source and licence of each row. "Gain on the round 17 file" is against `gate/cand-round17-1112a/details.csv`, so it is what the next assembly can add from this take dir.

### Changes to the tool

All in `family_loop.py`. `family_step.py` did not change (sha256 `7d504b34c0e8b37dd39c62a6613b571186c2c3b0bd7d3dfe9ca7e0f355193efc`, from `5e89596`), so `family_readers.py` still imports it with the same names and arguments.

- **Walk the new designs first** (commit `5beb224`): with `--first LANE ...`, the take dir layouts of those lanes walk up and down at jobs 1000 to 1099. They run before every other walk. `--logs NAME ...` reads more handoff logs (round 17: `handoff-d5.log` of boxE lanes).
- **No fill on a lent box** (`69982f5`): a box with 1 slot (boxE) gets no fill, so the lane runs one process there.
- **Stop a walk at its first miss** (`3a7feb7`): `cycle --misses N` sets the `--misses` of every walk job. The default stays 2. This round ran 1 from 18:21.
- **Prune the take dir** (`d842180`): a per-n csv at the top of the take dir with no `take.tsv` row moves to `work/dropped/`. The top level then holds only `take.tsv` and the files it names.

### Next runs

1. **Walk the new designs first, one shell each way.** One shell at n 790 and above gave 54 of 231 steps below the bar and 11 certified n. Keep `--first` for the twoshort and stair lanes and add the corners and border lanes: their layouts gave 800, 859, 920 and 973 here. Run `--misses 1` from the start.
2. **More slots, or fewer draws.** At the end the queues still held 156 jobs for 6 slots, and boxC ran at a load of 40 to 50. The second draws gave 38 of 179 steps below the bar and 22 certified rows, on 812 851 852 858 871 920 973. They can wait until the walks of the new designs have run.
3. **Hand over the layouts that do not read.** In the new zone, the stair-c near 919 and the held 862, 908 and 922 do not read with `read_any`. The layer reader of the readers lane took the corners 984 down to 921, so it can also take these.
4. **The main session can merge `take-family-r17`.** The round 17 file is the held file now (22.1635211736 on Kaggle). The next assembly copies the take dirs at 20:11. Against the round 17 file this take dir adds 9.248e-04 on 11 n.

## Round 19 (2026-11-12, evening)

**Result: 8 n certify below the round 17 file, for 6.777e-4 of score. Against the frozen round 17 take dirs and the other round 19 take dirs at 22:27 the gain is 2.576e-4. Nearly all of it is one or two shells from the new two-arm layouts of this round. The stair-c, corners, readers and twoshort lanes wrote them, most of them after 22:00. Nothing was submitted from here.**

Words for this section: "held" is `gather/round17-2026-11-12a.csv` (gate dir `gate/cand-round17-1112a`, 22.1635211736 on Kaggle). "The bar" of an n is the lowest of its held side, its side in every frozen `take-*-r17` dir and its side in every other live `take-*-r19` dir. A row that beats only the held file is already in round 18, so it does not count. The loop reads the bars again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it.

### What ran

The round ran from 20:15 to 22:35 UTC. The workers ran on boxC (3) and boxD (2). boxA ran the loop only, and the loop scored new raw files itself (`--fillhere`), so no box ran a fill beside its workers. The loop started at 20:21 with `--misses 1`, a cycle every 3 minutes. At 22:25 `work/final.sh` stopped the loop and every worker, collected and certified once more, and checked the copies.

| order | list | jobs made | dropped | jobs started |
|---|---|---|---|---|
| 0 | fq quench of the certified files | 17 | 0 | 17 |
| 1 | follow walks from new layouts | 297 | 0 | 240 |
| 2 | second builds of near misses at another cut | 27 | 0 | 20 |
| 2 | second draws of near misses (SQ_DRAW 1 to 3) | 138 | 0 | 64 |

The order of the queues:

| job numbers | what |
|---|---|
| 1000 to 1049 | the take rows of the twoshort, stair-b, stair-c, corners and border lanes of round 19, one walk up and one down |
| 1050 to 1099 | every other take row of round 19 and every csv a line of `handoff-r19.log` names, both ways |
| 1100 to 1110 | the 11 walks of round 17 that were queued but never started (`817-mm17` up, `804-scn17`, `971-mmx17`, `982-stx17`, `986-scn17` and `936-rd17` both ways) |
| 1100 to 1899 | the layouts of the frozen round 17 take dirs that no walk of round 17 started from |
| 1900 and up | second builds and second draws of near misses, for slots that the walks leave idle |

One shell at a time, by target zone:

| targets | direction | shells | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|
| n 300 to 789 | down | 1 | 48 | 42 | 1 | - | +5.51e-03 |
| n 300 to 789 | down | 2 | 4 | 3 | 0 | - | +8.45e-03 |
| n 300 to 789 | down | 3+ | 2 | 0 | 0 | - | - |
| n 300 to 789 | up | 1 | 20 | 20 | 1 | - | +9.63e-04 |
| n 300 to 789 | up | 2 | 1 | 1 | 1 | 649 | -3.97e-05 |
| n 790 to 1000 | down | 1 | 67 | 66 | 14 | 803 811 859 | +1.93e-03 |
| n 790 to 1000 | down | 2 | 6 | 6 | 4 | 811 859 863 | -6.17e-04 |
| n 790 to 1000 | down | 3+ | 1 | 1 | 0 | - | +3.19e-03 |
| n 790 to 1000 | up | 1 | 70 | 64 | 16 | 853 862 987 | +8.76e-04 |
| n 790 to 1000 | up | 2 | 11 | 10 | 2 | 987 | +3.31e-03 |

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| follow loop: walk from a new design | down | 128 | 118 | 10 | 19 | 8 | 803 811 859 863 | +3.40e-03 |
| follow loop: walk from a new design | up | 102 | 95 | 7 | 20 | 8 | 649 853 862 987 | +9.01e-04 |
| second draw of a near miss (SQ_DRAW=1) | down | 9 | 9 | 0 | 2 | 0 | - | +2.12e-05 |
| second draw of a near miss (SQ_DRAW=1) | up | 15 | 15 | 0 | 0 | 0 | - | +9.36e-05 |
| second draw of a near miss (SQ_DRAW=2) | down | 7 | 7 | 0 | 3 | 1 | 863 | +7.22e-07 |
| second draw of a near miss (SQ_DRAW=2) | up | 14 | 14 | 0 | 2 | 0 | - | +5.81e-05 |
| second draw of a near miss (SQ_DRAW=3) | down | 6 | 6 | 0 | 2 | 0 | - | +1.60e-06 |
| second draw of a near miss (SQ_DRAW=3) | up | 13 | 13 | 0 | 0 | 0 | - | +9.37e-05 |
| second build of a near miss of this round | down | 7 | 7 | 0 | 1 | 0 | - | +2.29e-05 |
| second build of a near miss of this round | up | 13 | 13 | 0 | 1 | 0 | - | +6.99e-05 |

### The follow loop by source lane

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| stair-c-r19 near/ | 41 | 44 | 39 | 5 | 811 987 | +3.00e-03 |
| stair-c-r19 | 25 | 31 | 27 | 8 | 811 987 | +1.12e-03 |
| modules (handoff log) | 14 | 15 | 14 | 1 | - | +1.38e-03 |
| readers-r19 | 12 | 13 | 13 | 8 | 859 987 | -1.00e-09 |
| midm-r19 | 11 | 12 | 10 | 1 | - | +7.98e-03 |
| family-r19 (own results) | 9 | 11 | 8 | 2 | 862 | +2.29e-05 |
| twoshort-r19 | 8 | 11 | 11 | 3 | 853 | +8.49e-03 |
| classfill-r19 | 10 | 10 | 10 | 1 | - | +1.98e-03 |
| modules-r19 | 9 | 9 | 9 | 0 | - | +5.32e-03 |
| midm (handoff log) | 6 | 8 | 7 | 3 | 649 | +4.37e-04 |
| corners-r19 | 6 | 7 | 7 | 1 | 803 | +4.57e-03 |
| twoshort (handoff log) | 4 | 5 | 5 | 2 | - | +3.52e-03 |
| polish-r19 | 5 | 5 | 5 | 0 | - | +1.66e-03 |
| farend-r19 near/ | 5 | 5 | 4 | 0 | - | +9.85e-03 |
| invent-r19 | 4 | 4 | 4 | 0 | - | +1.37e-02 |
| invent-r19 near/ | 4 | 4 | 4 | 0 | - | +1.34e-02 |
| stair-c-r17 near/ (round 17 walk that never started) | 3 | 3 | 3 | 0 | - | +5.39e-03 |
| round 17 file, by family | 2 | 3 | 3 | 0 | - | +1.31e-06 |
| border-r19 | 3 | 3 | 3 | 0 | - | +9.32e-03 |
| readers-r19 near/ | 1 | 3 | 3 | 2 | 863 | -2.00e-09 |
| corners-r19 near/ | 2 | 3 | 3 | 1 | 862 | +3.11e-03 |
| twoshort-r19 near/ | 3 | 3 | 3 | 0 | - | +1.73e-02 |
| round 17 file, by zones-corner | 2 | 2 | 2 | 0 | - | +1.06e-02 |
| round 17 walk that never started (readers-r17) | 2 | 2 | 2 | 1 | - | +2.97e-04 |
| family-r17 | 2 | 2 | 2 | 0 | - | +2.67e-03 |
| harvest-r17 | 2 | 2 | 2 | 0 | - | +3.78e-03 |
| corners (handoff log) | 2 | 2 | 2 | 0 | - | +1.53e-03 |
| readers (handoff log) | 2 | 2 | 2 | 0 | - | +8.57e-04 |
| classfill (handoff log) | 2 | 2 | 2 | 0 | - | +4.25e-03 |
| round 17 walk that never started (midm-r17) | 1 | 1 | 1 | 0 | - | +1.78e-03 |
| stair-c (handoff log) | 1 | 1 | 1 | 0 | - | +2.52e-03 |
| classfill-r19 near/ | 1 | 1 | 1 | 0 | - | +8.33e-04 |
| harvest-r19 | 1 | 1 | 1 | 0 | - | +6.63e-04 |

### Certified results

| n | gain on the round 17 file | gain on the bar | start |
|---|---|---|---|
| 649 | 1.558e-06 | 1.558e-06 | 2 up from the midm 549 |
| 803 | 1.116e-04 | 1.114e-04 | 1 down from the corners 862 |
| 811 | 2.148e-04 | 4.764e-05 | 2 down from the stair-c 931 |
| 853 | 1.305e-05 | 8.833e-06 | 1 up from the twoshort 794 |
| 859 | 1.332e-04 | 2.563e-06 | 2 down from the readers 983 |
| 862 | 1.465e-05 | 1.465e-05 | 1 up from our 803 (1 down from the corners 862) |
| 863 | 1.180e-04 | 7.294e-09 | 1 down from the readers 924 |
| 987 | 7.096e-05 | 7.096e-05 | 1 up from the stair-c 924 |
| total | 6.7765e-04 | 2.5762e-04 | |

"Gain on the round 17 file" is against `gate/cand-round17-1112a/details.csv`, as `take.tsv` holds it with the full source and licence of each row. "Gain on the bar" is against the lowest of that file, the frozen `take-*-r17` dirs and the other `take-*-r19` dirs at 22:27. Every take file except 862 had its fq quench on boxC or boxD. The 862 row came in the cycle of 22:21, so its quench never ran.

Other lanes took some of our layouts lower in the same round, so they left this take dir:

- The midm lane kicked our 811 (1 up from the modules 754) down by fq, to 1.671e-4 below the round 17 file.
- The polish lane quenched our 858 (1 down from the readers 919) 3.5e-10 lower.
- Our 870 (1 down from the stair-c 931) held from 22:12 to 22:15, until another lane went lower.

### Layouts the readers lane can take

The loop cannot walk a layout that `read_any` refuses. At 20:24 we tested the layout of every n from 790 to 1000 that sets the bar, and the 13 layouts that the round 17 report named. 129 of the 214 distinct layouts do not read (`work/unread13.py`, `work/unread13.out` in the take dir). 120 of them are layouts of the round 17 file.

- Each of the 13 named layouts got one line to the readers lane in `handoff-r19.log`, with its rows in `work/unread/`. Two of them changed. Our 858 now reads with `SQ_WALLTOL=4e-2`, so the loop walks it. The border lane withdrew its 904 at 15:42 in round 17, so that file is gone.
- Each layout of a round 17 take dir at n 790 and above that does not read also got its own line.
- The 114 other layouts of the round 17 file got one line together, with the list of n.
- With `--newall`, every new layout at n 790 and above that does not read gets its line when the loop meets it. In all, `handoff-r19.log` holds 25 lines from this lane to the readers lane. Among them are our own 858 and 859 and the invent 969.

Below n 790 most new designs of this round do not read either. These are the k123 joins (329, 330, 366, 407, 447, 448, 583, 584), the rigidsoft layouts (328, 332, 365, 409, 494) and the border layouts on them. So no walk started from them, and no line went to the readers lane for them.

### Changes to the tool

All in `family_loop.py` (commit `a9be6b1`). `family_step.py` did not change (sha256 `7d504b34c0e8b37dd39c62a6613b571186c2c3b0bd7d3dfe9ca7e0f355193efc`), so `family_readers.py` still imports it with the same names and arguments.

- `--also r17`: the take dirs of round 17 are bars and starts too. Their layouts carry their own round in the tag (`ts17`, `mm17`).
- `--newall`: every layout of round 19 walks both ways at 1050 to 1099, after the `--first` lanes at 1000 to 1049. A layout of an earlier round starts at 1100. A layout at n 790 and above that `read_any` refuses gets one line to the readers lane in `handoff-r19.log`, with its rows in `work/unread/`.
- `--drawshift 800`: the second draws start at 1950, after every walk.
- `--fillhere`: the loop scores new raw files itself.
- A csv named in an older handoff log keeps that log's round in its tag (`mmx17`, not `mmx19`).

### Next runs

1. **Fewer near copies to walk.** From 22:00 the stair-c lane wrote many near layouts of one n. Three of 863 lie within 2e-7 of side. The loop walks each one both ways, and 57 walks were still queued at 22:25. The loop can skip a near layout within 1e-6 of side of one it already walks.
2. **Keep the new corner lanes first.** Seven of the 8 n that hold at the end start from a layout of the stair-c, corners, readers or twoshort lanes. Most of it came after 22:00, when their new two-arm corners reached n 862 to 931.
3. **Leave the new mid-n designs to their lanes.** Below n 790 the k123 joins and the rigidsoft layouts do not read. So the family walk cannot reach their neighbours, where those lanes certify gains of 2e-4 to 6e-4.
4. **Draws only when the walk queue is empty.** Draws started on idle slots early in the round, when the walk queue ran dry. Each one held a slot for 1.5 to 4 minutes after new walks arrived.

## Round 20 (2026-11-12 to 2026-11-13, night)

**Result: 3 n certify below the round 18 file, for 1.669e-04 of score. Against the frozen round 19 take dirs and the other round 20 take dirs at the end of the round, the gain is 4.248e-05. As in round 19, the gain comes from one shell next to the new corner designs of other lanes. The starts are a corners near layout of 648, the modules 862, and our own chain from the twoshort 794. Nothing was submitted from here.**

Words for this section: "held" is `gather/round18-2026-11-12a.csv` (gate dir `gate/cand-round18-1112a`, 22.1604820601 on Kaggle). "The bar" of an n is the lowest of its held side, its side in every frozen `take-*-r19` dir and its side in every other live `take-*-r20` dir. The loop reads the bars again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it. The round 19 file (`gather/round19-2026-11-12a.csv`) came out during the round. It equals the lowest round 19 take on every n, so it does not change a bar, and the loop kept the round 18 file as its base.

### What ran

The workers ran on boxC (3) and boxD (2), with fresh uv venvs (scipy 1.18.1). boxA ran the loop only. The loop scored new raw files itself (`--fillhere`), so no box ran more than its budget.

- The loop started at 22:47 with `--misses 1` and a cycle every 3 minutes. boxA rebooted at about 22:48, after the first cycle. The workers on the two boxes kept running. The loop was started again at 22:51 with the same command and picked up its state from the work dir.
- The 39 round 19 jobs that were dealt but never started went first (`work/left20.py`). Those are 32 walks and 7 near builds. 17 near copies and 8 walks of our own results in the direction their walk already went were dropped.
- The layouts of the corners, stair-c, readers, twoshort and border lanes walked first (jobs 1000 to 1049). They came from the round 20 take dirs of these lanes and their frozen round 19 dirs. Every other new layout of round 20, and every csv that a line of `handoff-r20.log` names, walked both ways at 1050 to 1099.
- The `near/` folders of the frozen round 19 dirs counted as starts too (`--fresh r19`).
- At 00:56 `work/final.sh` stopped the loop and every worker, collected and certified once more, and checked the copies.

| order | list | jobs made | dropped | jobs started |
|---|---|---|---|---|
| 0 | fq quench of the certified files | 8 | 0 | 8 |
| 1 | follow walks from new layouts | 266 | 0 | 266 |
| 2 | second builds of near misses at another cut | 23 | 0 | 23 |
| 2 | second draws of near misses (SQ_DRAW 1 to 3) | 102 | 0 | 37 |

### Changes to the loop

All four are in `family_loop.py`. Without the new options the loop behaves as in round 19.

- **Near copies** (`--nearcopy 1e-6`, commit `5ad6cae`): a `near/` or handoff layout within 1e-6 of side of a layout that a walk already started from is skipped. In round 19, stair-c wrote three near layouts of 863 within 2e-7 of each other, and each one walked both ways. This round the loop skipped 24 such copies.
- **Walks before draws** (`--drawidle`, commit `5ad6cae`): draws wait in `work/pending-draw.txt`. A box that has walks queued stops as many running draws, and the stopped draws go back to the pending list. We tested it at 22:44 with two dummy draws on boxD. A queued walk stopped one draw and started in the same second. The other draw kept running.
- **Draws fill every free slot** (commits `c8dcf25`, `38ddc18` and `7ca028d`): the first version dealt a draw only in a cycle that dealt no walk at all. New layouts came in almost every cycle, so at 23:13 one slot on each box sat idle with 36 draws pending. Now each box gets its free slots plus 3 draws per slot, queued behind its walks. Walks still run first, because the workers take jobs in name order. `deal()` counts only the queued walks of a box. Control: the 23:38:56 cycle dealt 13 draws (pending 76 to 63), 8 of them on boxC behind 3 running jobs.

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| follow loop: walk from a new design | down | 137 | 84 | 53 | 8 | 1 | 803 | +2.59e-03 |
| follow loop: walk from a new design | up | 108 | 62 | 46 | 9 | 1 | 701 | +2.71e-03 |
| second draw of a near miss (SQ_DRAW=1) | down | 4 | 4 | 0 | 2 | 0 | - | +8.63e-07 |
| second draw of a near miss (SQ_DRAW=1) | up | 5 | 5 | 0 | 0 | 0 | - | +2.94e-05 |
| second draw of a near miss (SQ_DRAW=2) | down | 6 | 6 | 0 | 2 | 0 | - | +4.41e-06 |
| second draw of a near miss (SQ_DRAW=2) | up | 5 | 5 | 0 | 1 | 1 | 853 | +4.60e-08 |
| second draw of a near miss (SQ_DRAW=3) | down | 4 | 4 | 0 | 1 | 0 | - | +1.06e-06 |
| second draw of a near miss (SQ_DRAW=3) | up | 4 | 4 | 0 | 0 | 0 | - | +3.13e-05 |
| second build of a near miss of this round | down | 11 | 11 | 0 | 0 | 0 | - | +9.70e-05 |
| second build of a near miss of this round | up | 12 | 12 | 0 | 1 | 1 | 853 | +2.32e-05 |

One shell at a time, by target zone:

| targets | direction | shells | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|
| n 300 to 789 | down | 1 | 52 | 30 | 1 | - | +4.25e-03 |
| n 300 to 789 | down | 2 | 4 | 3 | 0 | - | +1.73e-02 |
| n 300 to 789 | up | 1 | 20 | 16 | 3 | 701 | +1.46e-03 |
| n 790 to 1000 | down | 1 | 81 | 51 | 7 | 803 | +1.67e-03 |
| n 790 to 1000 | up | 1 | 80 | 39 | 6 | - | +2.33e-03 |
| n 790 to 1000 | up | 2 | 8 | 7 | 0 | - | +1.78e-02 |

### The follow loop by source lane

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| stair-c-r20 near/ | 37 | 37 | 10 | 0 | - | +2.75e-03 |
| polish-r20 | 25 | 26 | 12 | 1 | - | +3.48e-03 |
| family-r20 (own results) | 16 | 18 | 10 | 2 | - | +8.18e-03 |
| corners-r20 | 18 | 18 | 14 | 2 | - | +1.34e-03 |
| stair-c-r20 | 14 | 15 | 3 | 1 | - | +1.39e-03 |
| modules-r20 | 14 | 15 | 11 | 1 | 803 | +3.33e-03 |
| classfill-r20 | 14 | 14 | 11 | 1 | - | +1.67e-03 |
| twoshort-r20 near/ | 12 | 13 | 13 | 1 | - | +8.46e-03 |
| midm-r20 | 10 | 10 | 8 | 0 | - | +2.71e-03 |
| readers-r20 | 10 | 10 | 1 | 1 | - | -8.85e-04 |
| twoshort-r19 near/ | 8 | 9 | 9 | 1 | - | +5.06e-03 |
| forensics-r20 near/ | 8 | 9 | 6 | 1 | - | +5.17e-03 |
| round 18 file, by family | 6 | 8 | 8 | 2 | - | +4.08e-03 |
| stair-c-r19 near/ | 6 | 6 | 4 | 0 | - | +1.99e-03 |
| classfill-r19 near/ | 6 | 6 | 4 | 0 | - | +1.57e-03 |
| family-r19 (own results of round 19) | 4 | 5 | 4 | 1 | - | +1.78e-04 |
| readers-r20 near/ | 5 | 5 | 0 | 0 | - | - |
| invent-r20 | 4 | 4 | 4 | 0 | - | +6.35e-03 |
| corners-r20 near/ | 4 | 4 | 4 | 1 | 701 | +1.13e-04 |
| twoshort-r20 | 4 | 4 | 4 | 0 | - | +4.88e-03 |
| readers-r19 near/ | 2 | 3 | 2 | 1 | - | +1.53e-03 |
| border-r20 | 3 | 3 | 1 | 0 | - | +2.31e-02 |
| family-r19 | 2 | 2 | 2 | 0 | - | +2.30e-03 |
| modules-r19 | 1 | 1 | 1 | 0 | - | +4.30e-03 |

Most refused steps come from the staircase corners of stair-c (`scn20`, `sc20`). The shell step needs a full grid line near the cut, and these layouts have none within 3 to 6 units. The loop wrote one `family -> readers` line for each new layout at n 790 and above that `read_any` refuses. The non-reading layouts of round 20 include the k123 joins (738, 910), the rigidsoft 907, the invent 969, the border 929, and the readers 809 and 868.

### Certified results

| n | step | start | gain on held | gain on the bar |
|---|---|---|---|---|
| 701 | 1 up | the corners near miss of n = 648 | 5.590e-06 | 5.590e-06 |
| 803 | 1 down | the modules result of n = 862 | 1.483e-04 | 3.688e-05 |
| 853 | 1 up | our 1 down from our 1 up from the twoshort result of n = 794 | 1.305e-05 | 6.100e-09 |
| total | | | 1.6693e-04 | 4.2475e-05 |

"Gain on held" is against `gate/cand-round18-1112a/details.csv`, and `take.tsv` holds it. "Gain on the bar" is against the lowest of held, every frozen `take-*-r19` and every other `take-*-r20` at the end of the round. Each file had one fq quench on boxC or boxD before it went into the take. Five more n certified here during the round and then left the take. The polish and harvest lanes ran fq on our 793 and 811 files and hold them a little lower. The modules lane built a lower 549 on the same corners 598. The stair-c lane holds a lower 930 and the twoshort lane a lower 794.

### Next runs

1. **Walk the new corner designs first again.** This round, as in round 19, the results start from layouts that other lanes wrote in the same round. The corners lane gave 549 and 930, modules gave 803, and the corners near 648 gave 701. Other lanes then took 549, 793, 794, 811 and 930 lower, so the chain of lanes gains more than this take shows.
2. **A shell step for the staircase corners.** The stair-c staircase layouts gave most of the refused steps. A step that cuts beside the staircase, not at a full grid line, would open them.
3. **Draws stay last.** They ran in free slots only. The stopped draws restart from the beginning, so a draw of more than 3 minutes can lose its slot again and again.

## Round 21 (2026-11-13)

**Result: 5 n certify below the round 19 file, for 3.178e-04 of score. Against the frozen round 20 take dirs and the other round 21 take dirs at the end of the round, the gain is 1.063e-04. 14 n certified here during the round. Other lanes then took 9 of them lower. For 6 of those the lower layout starts from our file or our near miss. As in rounds 19 and 20, the gain comes from one shell next to the new layouts of other lanes and from our own chain. The new staircase cut opens the stair-c corners, but no walk from it came below the bar. Nothing was submitted from here.**

Words for this section: "held" is `gather/round19-2026-11-12a.csv` (gate dir `gate/cand-round19-1112a`, 22.1514697138 on Kaggle). "The bar" of an n is the lowest of its held side, its side in every frozen `take-*-r20` dir and its side in every other live `take-*-r21` dir. The loop reads the bars again at every cycle. A result counts only when it certifies below the bar: floatsafe at 2.2e-11 and a score more than 1e-10 under it.

### What ran

The workers ran on boxC (3) and boxD (2), with fresh uv venvs (scipy 1.18.1). boxA ran the loop only, and the loop scored new raw files itself (`--fillhere`).

- The lane ran in three parts. The first agent worked from 01:03 to 01:20 and stopped on a usage limit. Its loop ran on until 03:20 and its workers until 03:25. boxA rebooted at 05:36.
- The second agent started the loop and the workers again at 09:50, with a deadline of 12:10. It built the staircase cut and dealt 52 walks with it. It stopped at 09:55 when its session lost its login.
- The third agent took over the running loop and workers at 09:59 and started nothing twice. It restarted the loop three times between cycles, for the three loop changes below.
- The loop walked the layouts of the stair-c, corners, readers, twoshort, border and modules lanes first. Then came every other new layout of round 21, every csv that `handoff-r21.log` names, and the `near/` folders of the frozen round 20 dirs (`--fresh r20`).
- At 12:05 the loop stopped. `work/final.sh` stopped every worker, collected and certified once more, and checked the copies.

| order | list | jobs made | dropped | jobs started |
|---|---|---|---|---|
| 0 | fq quench of the certified files | 18 | 0 | 18 |
| 1 | follow walks from new layouts | 291 | 0 | 291 |
| 1 | stair walks from refused starts (SQ_STAIRCUT) | 52 | 0 | 38 |
| 2 | second builds of near misses at another cut | 61 | 0 | 61 |
| 2 | second draws of near misses (SQ_DRAW 1 to 3) | 345 | 0 | 210 |

### Changes to the tools

All five act only when their option or variable is set. Without them the tools behave as in round 20.

- **Near misses for the kick lanes** (`family_loop.py --nearout 1e-4`, commit `c8ebccb`). The best near miss of each n within 1e-4 of its bar goes to `take-family-r21/near/` with a `near.tsv`, and one handoff line names it. Control on copied round 20 rows: with the option off, 0 files. At 1e-4, 10 files. At 1e-6, 4 files, and the other 6 were removed.
- **The staircase cut** (`family_step.py`, commit `744b06c`). A shell step cuts each arm at a full grid line. Until now that line had to lie within 3 units of the cut, and a border square had to sit beside it. The stair-c layouts have neither. `SQ_CUTREACH` sets the reach of the grid line. With `SQ_STAIRCUT=1` the cut may take the tilted square of a staircase run as its border square. Control on 18 refused cuts of 9 layouts: `SQ_CUTREACH=9` alone leaves every cut without a border square refused. With `SQ_STAIRCUT=1` as well, most open (752, 809 up, 868, 869 down, 930, 931, 993 down, 810 down). 70 layouts of rounds 20 and 21 had refused walks. A scan of the three lowest of them per n opened 52 cuts, and each one got a walk.
- **Every job gets the staircase cut** (`family_loop.py --staircut`, commits `7fd57a7` and `f676aa2`). Both variables act only where the plain cut refuses. Control: 14 builds that open without them give the same side and the same layout hash with them. 10 refused builds change, and 9 of them open. Near builds and draws carry the variables too, so a near miss of a stair walk builds again at the same cut.
- **Draws are not stopped** (`family_loop.py --drawkeep`, commit `346271c`). With `--drawidle` a box with queued walks stopped as many running draws. A stopped draw starts again from the beginning. The first part of the round stopped 59 draws in 26 cycles. Now a queued walk waits for the next free slot, and walks sort before draws. Control: the 11:03:34 cycle dealt 7 walks to boxC while 1 to 3 draws ran there. The old code stops a draw in that case. No draw was stopped, and the walks took the slots as the draws ended (`work/report/drawkeep-ctl.txt`).

### Steps by part

| part | direction | steps | built | refused | below the bar | certified | certified n | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| follow loop: walk from a new design | down | 150 | 131 | 19 | 11 | 0 | - | +1.49e-03 |
| follow loop: walk from a new design | up | 147 | 129 | 18 | 17 | 3 | 693 855 | +1.82e-03 |
| stair walk: a refused start, cut beside the staircase | down | 33 | 33 | 0 | 0 | 0 | - | +2.35e-03 |
| stair walk: a refused start, cut beside the staircase | up | 25 | 25 | 0 | 0 | 0 | - | +3.20e-03 |
| second draw of a near miss (SQ_DRAW=1) | down | 30 | 30 | 0 | 4 | 0 | - | +6.07e-07 |
| second draw of a near miss (SQ_DRAW=1) | up | 33 | 33 | 0 | 5 | 0 | - | +1.56e-05 |
| second draw of a near miss (SQ_DRAW=2) | down | 28 | 28 | 0 | 3 | 1 | 794 | +6.94e-07 |
| second draw of a near miss (SQ_DRAW=2) | up | 32 | 32 | 0 | 5 | 0 | - | +1.32e-05 |
| second draw of a near miss (SQ_DRAW=3) | down | 31 | 31 | 0 | 7 | 4 | 756 794 796 | +6.53e-07 |
| second draw of a near miss (SQ_DRAW=3) | up | 30 | 30 | 0 | 7 | 0 | - | +1.32e-05 |
| second build of a near miss of this round | down | 33 | 33 | 0 | 4 | 0 | - | +5.26e-05 |
| second build of a near miss of this round | up | 28 | 28 | 0 | 0 | 0 | - | +3.35e-05 |

### The follow loop by source lane

| source of the start layout | walks | steps | built | below the bar | certified n | median of side less bar |
|---|---|---|---|---|---|---|
| family-r21 (own results) | 40 | 50 | 49 | 9 | 855 | +7.85e-04 |
| polish-r21 | 26 | 39 | 31 | 3 | - | +2.55e-03 |
| midm-r21 | 27 | 37 | 24 | 2 | 693 | +2.15e-03 |
| modules-r21 near/ | 31 | 33 | 33 | 1 | - | +1.94e-03 |
| readers-r21 | 16 | 23 | 15 | 0 | - | +3.71e-04 |
| stair-c-r21 near/ | 19 | 19 | 19 | 2 | - | +2.77e-04 |
| modules-r20 near/ | 14 | 17 | 17 | 3 | - | +5.84e-04 |
| forensics-r21 | 15 | 15 | 13 | 0 | - | +5.93e-03 |
| classfill-r21 | 13 | 15 | 15 | 2 | - | +6.53e-04 |
| invent-r21 | 9 | 11 | 8 | 0 | - | +3.44e-04 |
| twoshort-r21 near/ | 10 | 10 | 10 | 0 | - | +6.26e-03 |
| corners-r21 | 8 | 9 | 9 | 1 | - | +1.45e-03 |
| stair-c-r20 near/ | 7 | 9 | 9 | 0 | - | +3.97e-03 |
| readers-r20 | 6 | 9 | 9 | 0 | - | +2.06e-03 |
| modules-r21 | 7 | 7 | 7 | 1 | - | +1.15e-04 |
| corners-r20 | 3 | 6 | 6 | 0 | - | +3.99e-03 |
| stair-c-r21 | 4 | 5 | 5 | 2 | - | +6.52e-05 |
| corners-r21 near/ | 5 | 5 | 5 | 0 | - | +4.04e-03 |
| k123-r21 | 4 | 5 | 5 | 1 | 855 | +4.73e-03 |
| border-r21 | 4 | 4 | 4 | 0 | - | +6.47e-03 |
| modules-r20 | 2 | 3 | 3 | 1 | - | +5.22e-05 |
| polish-r20 | 2 | 3 | 3 | 0 | - | +2.82e-03 |
| readers-r20 near/ | 2 | 2 | 2 | 0 | - | +7.89e-06 |
| readers (handoff log) | 2 | 2 | 2 | 0 | - | +1.35e-03 |
| harvest-r20 | 2 | 2 | 0 | 0 | - | - |
| invent (handoff log) | 2 | 2 | 2 | 0 | - | +7.94e-03 |
| twoshort (handoff log) | 2 | 2 | 2 | 0 | - | +8.33e-03 |
| classfill-r21 near/ | 2 | 2 | 2 | 0 | - | +2.22e-05 |
| twoshort-r21 | 2 | 2 | 2 | 0 | - | +9.00e-03 |
| forensics (handoff log) | 2 | 2 | 2 | 0 | - | +9.30e-03 |
| forensics-r20 near/ | 1 | 2 | 2 | 0 | - | +2.53e-02 |
| border-r20 | 1 | 1 | 1 | 0 | - | +4.22e-05 |
| modules (handoff log) | 1 | 1 | 1 | 0 | - | +4.43e-03 |
| stair-c-r20 | 1 | 1 | 1 | 0 | - | +2.35e-03 |

### The staircase cut: measured

The 52 stair walks of the second agent started from the lowest refused layout per n and direction (job 1010), the second (1150) and the third (1250). 58 steps built, 0 of them below the bar and 1 within 1e-4 of side. The median is +2.68e-03 of side above the bar. The closest steps: 868 up from 809-mm21b (+4.7e-05), 752 down from 809-mm21b (+2.1e-04), 809 up from 752-p21a (+3.2e-04). At 10:20 the 14 queued third-donor walks were parked. Their donors lie within 2.4e-4 of side of a donor already walked, and no step had come below the bar yet. The cut opens these layouts, but one shell of a staircase design costs more side than the step saves. The stair-c, midm and readers lanes took the same n lower with their own corners and kicks.

### Certified results

| n | step | start | gain on held | gain on the bar |
|---|---|---|---|---|
| 693 | 1 up | the midm result of n = 640 | 3.851e-05 | 3.851e-05 |
| 756 | 1 down | the modules result of n = 813 | 1.373e-05 | 3.664e-07 |
| 794 | 1 down | the invent result of n = 853 | 3.536e-07 | 4.816e-09 |
| 796 | 1 down | the readers result of n = 855 | 1.978e-04 | 2.083e-09 |
| 855 | 1 up | the k123 result of n = 796 | 6.740e-05 | 6.740e-05 |
| total | | | 3.1780e-04 | 1.0629e-04 |

"Gain on held" is against `gate/cand-round19-1112a/details.csv`, and `take.tsv` holds it. "Gain on the bar" is against the lowest of held, every frozen `take-*-r20` and every other `take-*-r21` at the end of the round. Each file had one fq quench on boxC or boxD before it went into the take. 9 more n certified here during the round and then left the take, because another lane holds them lower: 811, 813, 851, 853, 870, 875, 912, 929, 931. For 813, 853, 875, 912, 929 and 931 the lower layout starts from our file or our near miss. The corners lane took 811 and 870 with its own corners, and k123 took 851 with a join.

### Next runs

1. **Walk new layouts first and hand out near misses.** Each n of this take is one shell from a new layout of another lane. The starts were midm 640, modules 813, invent 853, readers 855 and k123 796. Other lanes then built on our files. Forensics took corner windows of our 693 for 591 and 641. Classfill and modules built 936 and 875 from our near miss of 936. Midm and polish quenched our 912 lower. So the chain of lanes gains more than this take shows.
2. **Run the draws with `--drawkeep` from the start.** Draws of near misses gave 756 and 813 in this round. In the first part of the round, walks stopped 59 running draws, and each one started again from the beginning.
3. **Do not deal extra walks from refused staircase layouts.** The staircase cut opens them, but 58 steps gave 0 below the bar. Keep `--staircut` on, because it changes no build that the plain cut accepts. Leave the staircase designs to stair-c, the layer reader of readers and the kick lanes. In this round those lanes took 810, 811, 868, 930 and 993 lower.
4. **Leave the non-reading designs to readers.** The loop wrote one `family -> readers` line for each new layout that `read_any` refuses. In this round that was 930, 811, 790, 807, 993, 992, 698 and more.

## Files

| file | what it is |
|---|---|
| [`family_step.py`](../family_step.py) | the tool: `read`, `ctl`, `plan`, `run`, `walk`, `take` |
| [`results/family-r10-2026-11-11.tsv`](../results/family-r10-2026-11-11.tsv) | every pair of the sweep |
| `<scratch>/bounties-squares/take-family-r10/` on boxA | the take dir: one csv per certified n and `take.tsv` |
| `<scratch>/bounties-squares/take-family-r10/work/` | plans, reads tables, control logs, raw rows per box |
| [`results/family-r11-2026-11-11.tsv`](../results/family-r11-2026-11-11.tsv) | every step of round 11 |
| `<scratch>/bounties-squares/take-family-r11/` on boxA | the take dir of round 11 |
| `<scratch>/bounties-squares/take-family-r11/work/` | walk lists, plans, `reach.tsv`, `reach-loose.tsv`, swap logs, raw rows per box |
| [`results/family-r12-2026-11-12.tsv`](../results/family-r12-2026-11-12.tsv) | every step of round 12 |
| `<scratch>/bounties-squares/take-family-r12/` on boxA | the take dir of round 12; `work/` has the job lists, `worklog.md` (the deployed commit and hashes), `reach12.tsv` and the rows and steps per box |
| [`family_loop.py`](../family_loop.py) | the follow loop: collect, certify, near builds, walks from every new layout, deal to the boxes. `left` carries the unrun jobs of a round |
| [`results/family-r13-2026-11-12.tsv`](../results/family-r13-2026-11-12.tsv) | every step of round 13, with the box and the source lane of the start |
| `<scratch>/bounties-squares/take-family-r13/` on boxA | the take dir of round 13. `work/` has `worklog.md`, `loop.log`, the rows and steps per box, the comparison runs (`*-out-cmp-*`), `mkrestack13.py`, `restackcmp.py` and `r13doc.py` |
| [`results/family-r14-2026-11-12.tsv`](../results/family-r14-2026-11-12.tsv) | every step of round 14, with the box and the source lane of the start |
| `<scratch>/bounties-squares/take-family-r14/` on boxA | the take dir of round 14. `work/` has `worklog.md`, `loop.log`, the rows and steps per box, `mk854.py`, `mkdraw14.py`, `mkleft14.py`, `mkends14.py`, `near_polish.py` (in `deploy/`), `strip/strip_scan.py`, `whatran.py` and `r14doc.py` |
| [`results/family-r15-2026-11-12.tsv`](../results/family-r15-2026-11-12.tsv) | every step of round 15, with the box and the source lane of the start |
| [`results/family-r16-2026-11-12.tsv`](../results/family-r16-2026-11-12.tsv) | every step of round 16, with the box and the source lane of the start |
| `<scratch>/bounties-squares/take-family-r16/` on boxA | the take dir of round 16. `work/` has `worklog.md` (the deployed commit and hashes), `loop.log`, `certcache.tsv`, the rows and steps per box, `final.sh`, `r16doc.py` and `dropped/` |
| [`results/family-r17-2026-11-12.tsv`](../results/family-r17-2026-11-12.tsv) | every step of round 17, with the box and the source lane of the start |
| `<scratch>/bounties-squares/take-family-r17/` on boxA | the take dir of round 17. `STATE.txt` is the lane's log across the cuts. `work/` has `loop.log`, the rows and steps per box, `final.sh`, `r17doc.py`, `fill17.py` and `dropped/` |
| [`results/family-r19-2026-11-12.tsv`](../results/family-r19-2026-11-12.tsv) | every step of round 19, with the box and the source lane of the start |
| `<scratch>/bounties-squares/take-family-r19/` on boxA | the take dir of round 19. `STATE.txt` is the lane's log. `work/` has `loop.log`, the rows and steps per box, `final.sh`, `r19doc.py`, `fill19.py`, `unread13.py`, `unread/` and `dropped/` |
| [`results/family-r21-2026-11-13.tsv`](../results/family-r21-2026-11-13.tsv) | every step of round 21, with the box, the list and the source lane of the start |
| `<scratch>/bounties-squares/take-family-r21/` on boxA | the take dir of round 21. `STATE.txt` is the lane's log across the three parts. `work/` has `loop.log`, the rows and steps per box, `final.sh`, `r21doc.py`, `r21section.py`, `cutreach/` (the staircase cut controls) and `report/` |

## Summary

- The shell step is exact. It removes `2m + 1` squares, keeps `f`, and leaves a gap of `p - 1` per arm. 814 down to 757 lands 5.8e-8 below the held side, and 757 up to 814 lands on it.
- The squeeze recovers a median of 58% of the plain formula `d = (p - 1) / (1 + s |dp/df|)`, and between 5% and 113%. The end-zone term `Z` (median 2.6) is fitted per pair, so it does not predict yet.
- The predicted gain is not there on the 55 targets we could test (8% of 0.0064 measured). The other 89% of the predicted 0.057 is untested. Where a line holds one design, each n is already at that design's side. 30 n certified for 0.001258, and nearly all of that gain is at n where the step brings a different design.
- The reader covers 74 of 413 tilted n. That is the limit on this avenue today.
- **Round 11:** 29 n certified for 0.0021816 of score on the held file of round 10 (0.0017416 on 29 n against the round 10 takes). The large gains are steps into n whose held layout has no flush arm. They start from layouts that only the wider reader takes.
- **Round 12:** 24 n certified for 0.0009333 of score on the held file of round 11 (0.0006365 against the round 11 takes of every lane). 11 of them start from layouts that other lanes wrote hours before, 9 from the corner-zone sweep.
- **Round 13:** 16 n certified for 0.0003479 of score on the held file of round 12 (0.0003230 against the round 13 takes of the other lanes). 12 come from the follow loop, 7 of them from layouts that the soft, polish and modules lanes wrote in the same round. The step 738 -> 795 differs by box because of the scipy version. Round 12 ran scipy 1.13.1 (HiGHS 1.2.0) on boxC and boxD, and scipy 1.18.1 (HiGHS 1.12.0) on boxA. Neither is better on average, and every box now runs 1.18.1.
- **Round 14:** 9 n certified for 0.0001473 of score on the held file of round 13 (0.0001373 against the round 14 takes of the other lanes). Five come from follow walks of other lanes' layouts and hold nearly all of it. A second draw on the same scipy (`SQ_DRAW`) certified 854, 815, 816 and 936. The 97 jonathan1506 layouts gave nothing here: 67 do not read with this lane's readers.
- **Round 16:** 10 n certified for 0.0001785 of score on the held file of round 15 (0.0001211 against the round 16 takes of the other lanes). Nearly all of it comes from walks and draws of layouts that the soft, modules, corners and polish lanes wrote in the same round. The certification cache cut the certify step of a cycle from 200 to 290 s to a median of 29 s.
- **Round 17:** 15 n certified for 0.0019066 of score on the held file of round 16. Against the other round 17 takes that is 0.0007361, and 0.0009248 on 11 n against the round 17 file. Nearly all of it is one shell up or down from the new two-arm designs at m 28 to 31. The twoshort, stair-c, corners and border lanes built them in the same round.
- **Round 19:** 8 n certified for 0.0006777 of score below the round 17 file, and 0.0002576 below the frozen round 17 takes and the other round 19 takes. Nearly all of it is one or two shells from the new two-arm layouts of the stair-c, corners, readers and twoshort lanes, most of it after 22:00.
- **Round 21:** 5 n certified for 3.178e-04 of score below the round 19 file, and 1.063e-04 below the frozen round 20 takes and the other round 21 takes. 14 n certified during the round. Other lanes took 9 of them lower, 6 of those from our file or our near miss. The new staircase cut opens the stair-c corners, but its 58 steps gave nothing below the bar.
- **Next:** the main session can merge the take dir. Walk the new corner designs first, and skip near copies of a layout the loop already walks.

## Round 22 (2026-11-13)

The final take certifies 9 n below the round 20 file. Its gain is 6.8616611333e-04 of score.
The gain over the frozen round 21 takes and every other round 22 take is 6.2864677389e-04.

The workers ran on boxC (3 slots) and boxD (2 slots). boxA ran the collector only.
The search deadline was 15:20 UTC. The take was checked again against all live takes before the 15:30 cutoff.
Each published file passed floatsafe at 2.2e-11. It also received a remote fq quench from its certified file before publication.
No submission ran from this lane.

The held baseline is `gate/cand-round20-1113a/details.csv`. The bar also includes every frozen round 21 take and every other live round 22 take.
A score must beat that bar by more than 1e-10.
The [results table](../results/family-r22-2026-11-13.tsv) records each step and its source lane. Full provenance stays in the take ledger.

### Measurements

| Part | Direction | Steps | Built | Below bar at build | Median side minus bar |
|---|---|---:|---:|---:|---:|
| draw1 | down | 3 | 3 | 0 | +6.433e-05 |
| draw1 | up | 2 | 2 | 0 | +5.654e-05 |
| draw2 | down | 4 | 4 | 0 | +5.214e-05 |
| draw2 | up | 3 | 3 | 0 | +4.619e-05 |
| draw3 | down | 5 | 5 | 0 | +7.126e-05 |
| draw3 | up | 1 | 1 | 0 | +4.697e-05 |
| fol | down | 140 | 130 | 13 | +4.184e-03 |
| fol | up | 296 | 285 | 34 | +2.654e-03 |

| Queue | Made or carried | Started | Ended |
|---|---:|---:|---:|
| draw1 | 94 | 5 | 5 |
| draw2 | 96 | 7 | 7 |
| draw3 | 95 | 6 | 6 |
| fol | 698 | 446 | 442 |
| near2 | 39 | 0 | 0 |
| quench | 24 | 22 | 22 |

The queue carried 135 unstarted draws from round 21. It carried the seen sets, so layouts already walked stayed out.
The staircase cut stayed enabled. The dry queue of extra refused staircase walks stayed parked.
Jobs that only reached staging did not enter the take. Another lane can also take a published n lower before the final check.

### Tool changes and controls

- `--quenchfirst` certifies into `work/certified/` and queues the remote quench. Only its output can enter the published take.
  Control: 0 published before the quench, 1 afterward, and 0 duplicate quench jobs. The frozen round 21 bar rejected that control.
- File versions now enter follow keys. Control with unchanged rounded gain: 2 initial jobs, 2 after changed coordinates, 0 after an identical rewrite.
- Changed near files replace stale exports and receive a handoff line. Control: exported bytes matched the new input. An unchanged repeat emitted no duplicate.
- Certified starts run ahead of near variants. Control: a near start moved from priority 1022 to 1450 or 1600. The certified start stayed at 1057.
  The lane moved 27 queued near walks to that order. Active jobs continued.
- Near donors retain JSON provenance. Control: the n750 rectangle manifest supplied both windows and their source ledgers.
  The stair-c n816 manifest retained all three module sources and their Apache 2.0 notices. Wrong n and missing manifests were refused.
- Donor names continue beyond ten versions. Control: version 11 raised IndexError before the fix and queued both walks afterward.
  The first ten names stay unchanged. Version 26 is z, version 27 is aa, and version 703 is aaa.

### Final take

| n | Gain on round 20 | Gain on other takes |
|---|---:|---:|
| 420 | 1.4225236480e-04 | 1.4225236480e-04 |
| 550 | 5.6052326326e-05 | 5.6052326326e-05 |
| 595 | 9.8380257072e-05 | 9.8380257072e-05 |
| 689 | 5.3980741088e-05 | 5.3980741088e-05 |
| 758 | 5.3047640405e-05 | 5.3047640405e-05 |
| 815 | 8.8415203876e-06 | 8.8415203876e-06 |
| 847 | 6.8417150711e-05 | 6.8417150711e-05 |
| 908 | 1.4761477894e-04 | 1.4761477894e-04 |
| 936 | 5.7579333592e-05 | 5.9994151647e-08 |

17 distinct layouts were published during the round. The final count uses the last comparison against all takes.

### Next runs

N875 came from the fresh stair-c near layout of n816. Midm then kicked our file lower by 1.5483357152e-07 of score.

N807 came from the fresh forensics near layout of n750. Midm then kicked our file lower by 1.0828093178e-07 of score.

1. Walk fresh readable designs from other lanes, including near layouts. N908 first beat its bar by 1.476e-04 of score from the harvest result of n971. N595 first beat its bar by 9.838e-05 of score from the harvest result of n646. N420 first beat its bar by 9.742e-05 of score from the harvest result of n379. The follow walks put 47 of 436 steps below the bar. Every final gain in round 21 also came from a fresh layout.
2. Keep drawkeep and use spare slots for pending draws. This round measured 0 draws below the bar in 18 draws, after carrying 135 unstarted jobs.
3. Keep the version, provenance and near-refresh controls. They reproduced missed versions, stale exports and a near queue ahead of certified starts.
4. Leave non-reading layouts to readers. Keep staircut enabled, but do not restore the extra refused staircase queue: round 21 measured 58 steps with no gain.
5. Recheck and quench unpublished staging rows 650. They passed staging but did not produce a qualifying published quench before cutoff. Their csv files remain in work/certified/.

## Round 23 (2026-11-13)

The final take holds 4 n. Its gain against round 21 is 8.6484121568e-04 of score.
The gain over frozen round 22 takes and other round 23 takes is 1.2499548795e-04.

The baseline is `gate/cand-round21-1113a/details.csv`. Each row beats its full comparison bar by more than 1e-10 of score.
Each published layout passed floatsafe at 2.2e-11 and a remote fq quench from its certified file.
The workers used three slots on boxC and two on boxD. boxA ran the collector.
Search and quenches stopped at 18:30 UTC. The final comparison ran before 18:40 UTC.
No submission ran from this lane.

The [results table](../results/family-r23-2026-11-13.tsv) records each step and its source lane. The take ledger keeps source notices.

### Measurements

| Part | Direction | Steps | Built | Below bar at build | Median side minus bar |
|---|---|---:|---:|---:|---:|
| cmp-range-after | down | 1 | 1 | 0 | +1.869e-02 |
| draw1 | up | 1 | 1 | 0 | +1.483e-03 |
| draw2 | up | 1 | 1 | 0 | +1.461e-03 |
| draw3 | up | 2 | 2 | 0 | +8.239e-04 |
| fol | down | 153 | 145 | 19 | +3.711e-03 |
| fol | up | 290 | 279 | 59 | +1.662e-03 |

| Queue | Made or carried | Started | Ended |
|---|---:|---:|---:|
| draw1 | 152 | 1 | 1 |
| draw2 | 152 | 1 | 1 |
| draw3 | 152 | 2 | 2 |
| fol | 857 | 416 | 411 |
| near2 | 54 | 0 | 0 |
| other | 2 | 2 | 2 |
| quench | 20 | 20 | 20 |

The queue carried 267 unstarted draws and 239 unstarted follow walks from round 22. Saved hashes prevented repeats.
The staged n650 still beat frozen round 22 by 9.423e-10 of score at startup. It received a remote certified-file quench.
The restored classfill n599 follow lowered n503 by 1.3498303242e-06 of score beyond its first published layout.
The two shells down used a certified start that the previous round never ran.
### Provenance control

The existing rectangle control resolved both window sources before the reader change.
Before the change, 245 saved reader ends lacked metadata in the family metadata reader.
The reader now resolves its exact donor through the immutable `work/sources-all.tsv` ledger.
The control resolved the parent source and licence. It rejected wrong n, a missing donor and a missing ledger.
Handoff sources now use sidecars or their own take ledger. Late ledger updates require an exact match to the stored donor.
The control enriched the exact n990 donor. It rejected a changed geometry and wrong n, and an unchanged repeat enriched zero rows.
The first live pass expanded 26 generic sources, including the full k123 join source and notices for n927.
The walk and follow pass now accept readable starts throughout n1 to n1000. The old walk cutoff suppressed the304 to269 step.
Control: the old walk wrote zero rows. The new walk wrote one legal269 row and passed floatsafe.
That269 layout ended 0.0186862661 of side above held and counts for zero gain.
The fresh public and polish layouts of n127,204,232,264,270 all failed the family reader. Their designs stay with readers.

The collector now fetches all output directories in one transfer per box.
Its control collected both boxes in 20.49 seconds. Both completed n650 quench files matched the original collection byte for byte.
Worker logs were copied too. The transfer excluded the remote venv.
### Final take

| n | Gain on round 21 | Gain on other takes |
|---|---:|---:|
| 379 | 6.8679827912e-04 | 1.9180479427e-10 |
| 597 | 1.0470713582e-04 | 1.0470713582e-04 |
| 758 | 5.3047816084e-05 | 1.7567969302e-10 |
| 876 | 2.0287984651e-05 | 2.0287984651e-05 |

### Next runs

1. Walk fresh readable designs first, including near layouts. Follow steps put 78 of 443 below their build bars. N927 first beat its live bar by 1.342e-04 of score from k123 n990. N597 first beat its live bar by 5.613e-05 of score from harvest n648. N876 first beat its live bar by 2.029e-05 of score from stair-c n817.
2. Resume fresh follow jobs from work/final-unfinished-follow.tsv before older near variants. It records 444 queued or interrupted jobs with their sources. The recovered classfill599 walk improved n503 by1.34983032418e-6 beyond its first result.
3. Keep drawkeep and fill spare slots with saved draws. Draws put 0 of 4 below their build bars. 267 unstarted draws entered this round.
4. Keep exact reader-end provenance from sources-all.tsv. The positive rectangle control passed. The new reader control resolved its parent and rejected wrong n, missing donor and missing ledger.
5. Leave the ten fresh public and polish files below n = 300 to readers. The tested n127,204,232,264,270 all failed the family reader.
6. Keep staircut enabled, and leave the extra refused-staircase backlog parked. Round 21 measured 58 steps with zero below the bar.
7. Keep the scalar side filter for the tested layouts. The only below-bar stage, n758, reproduced the existing family score within1e-15. Require a fresh corner or far zone before repeating these inputs.
8. Keep fresh follows open below n = 300, but skip broad held low-n rescans. The n225..299 audit read0 designs, and the269 boundary control missed held by0.0186863 side.

### Side filter audit

The [angle audit tool](../family_side_audit.py) compares sorted angles folded to the first octant.
A sample of 60 recent near files found 22 side matches within 1e-6.
Twelve readable layouts differed from every nearby stored angle profile by more than 0.01 radians.
Control: the scalar filter emitted zero jobs. A bounded bypass emitted two, and an unchanged repeat emitted zero.
The workers received 18 first-shell jobs for 10 donor counts. Each build had a 180-second cap and the common 18:30 UTC deadline.
The replay wrote 18 step rows. 1 ended below their build bars.
The global side filter stayed unchanged. Full inputs and notices remain in `work/side-audit-queued.json`.
Current take rows with audit ancestry: 758.

## Round 24 (2026-11-13)

The final take holds 0 n. Its gain against the original round 23 candidate is 0.0000000000e+00 of score.
The gain against the revised public baseline is 0.0000000000e+00.
The gain beyond the matching live source group is 0.0000000000e+00.

Publication requires floatsafe at 2.2e-11 and a gain above1e-10 against the matching source group.
Each published file received an fq quench from its certified csv on boxC or boxD.
The workers used three slots on boxC and two on boxD. boxA ran the collector.
Fresh layouts preceded the inherited queue. Saved draws and broad scans below n300 stayed closed.
A queue check found 82 fresh jobs waiting. Equal-rank jobs sorted by count, so newer batches now precede older batches.
The priority control preserved quenches and first-lane starts ahead of those batches.
Fresh follows stopped at 22:10 UTC. Search and quenches shared the 22:15 UTC deadline.
No submission ran from this lane.

The [results table](../results/family-r24-2026-11-13.tsv) records each step and its source lane.
The build-bar count uses more than1e-9 of side on the recorded nine-decimal values. Decimal subtraction avoids boundary errors.

At20:05UTC the main session revised the bar for20 held counts. Source-clean rows there can beat round22 instead of candidate-a.
Rows with Samanyu ancestry still need to beat candidate-a. Every licence cell names the source group and its seed n.
Rows against the wider clean bar can have a negative gain against candidate-a. The revised-public-baseline gain measures their accepted improvement.

### Measurements

| Part | Direction | Steps | Built | Below bar at build | Median side minus bar |
|---|---|---:|---:|---:|---:|
| fol | down | 411 | 384 | 5 | 7.264e-03 |
| fol | up | 206 | 188 | 9 | 1.973e-03 |

### Source admission

The initial source pass admitted 380 of 444 saved jobs. A deeper pass checked 330 distinct donors and refused 40 more.
The public703 input was later verified in its archive. Three donor records were restored after that check. Source-clean503 then passed the revised baseline.
Both worker CSV controls parsed 200000 characters and all1000 bars. Exactly397 jobs failed on the old field limit and were requeued.
The peer-label parser first missed the harvest503 label. Fixing that comparison withdrew the family503 row.
The publication control kept clean599 visible while the strict comparison ran.
Those 40 lacked complete parent records or upstream terms. Their queued jobs were removed and their outputs were quarantined.
The source audit resolves near and take parents. It retains upstream records from the areeb per-n table.
An exact candidate geometry keeps its inherited source table. The brief names that candidate as the clean donor pool.
Control: clean candidate814 generated two walks. An unchanged repeat generated zero, and changed geometry with an excluded source generated zero.
The original927 control failed because its layout did not read. Repeating814 required a fresh control state.
Both remote fq controls reduced the n2 side from2.5 to2.000000000000406. Both boxes used scipy1.18.1.
The rectangle metadata control passed before the reader change. Afterward582 retained its recorded source, and the soft921 sidecar resolved its donor.
The source control accepted fresh forensics918 and refused old forensics-r23/918.
Relative near-parent paths now resolve through their metadata. A pinned manual source notice applies only when its csv hash matches.
Control: reader699 resolves public646 with Apache notices. A wrong-hash notice is refused.
The public donor parser resolves reader699 from646 to public646. The first parser trial missed the filename boundary and failed its control.
The corrected control passed for both direct646 and reader699. Four saved parent files support the staged595 ancestry in `work/source595-proof.json`.
Every remote output and worker log was copied and checked by SHA256 before either scratch directory was removed.

### Final take

| n | Gain on original candidate-a | Gain on revised public baseline | Gain on source-group peers |
|---|---:|---:|---:|
| None | 0 | 0 | 0 |

### Chained results

Later lanes record these family inputs. Their gains belong to the later lanes.

| Family input n | Later lane | Gain beyond best family file |
|---|---|---:|
| 595 | take-invent-r24 | 5.3680719825e-07 |
| 599 | take-invent-r24 | 6.3671934392e-10 |
| 802 | take-forensics-r24 | 3.9742339923e-05 |
| 871 | take-invent-r24 | 8.1364972093e-08 |

The n871 family input has Samanyu seed504 ancestry. The n599 family input has no Samanyu ancestry.
The n802 family input has no Samanyu ancestry. Consumer rows can add other parents.

### Next runs

1. Walk fresh readable designs first, including near layouts. This round put 14 of 617 follow steps below their build bars. Clean599 lowered the revised public bar by8.71022808495e-5 before invent beat it.
2. Resume source-admitted never-started follows from work/final-unfinished-follow.tsv. It records 165 queued or interrupted specifications. Saved draws gave0/4 in round23 and stayed closed here.
3. Preserve rectangle source_record and soft source_override metadata. Controls kept both rectangle parents and resolved the exact soft donor. Missing ancestry remains a refusal.
4. Keep the tested scalar side filter. Round23 replay18 built, only1 below its bar, and that row tied an existing result within1e-15. Revisit only a fresh corner or far zone.
5. Keep broad scans below n300 and unchanged staircase retries closed. Round23 low-n control missed by0.0186863 side, and round21 staircase retries gave0/58 below bar.
