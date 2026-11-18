# Avenue: inflate (2026-11-11, round 10)

**Result: no pocket reaches side 1, so this path makes no n + 1 smaller. The map is measured on 44 layouts. In the box just below the held side of n + 1 the best pocket of a layout grows to 0.72 to 0.96. Eight layouts pass 0.9, all with `f` above 0.92. The best are 0.9613 at n = 419 and 0.9586 at n = 757. A straight line through the two boxes puts the unit square 0.004 of side above the held 420 and 0.006 above the held 758. Three insertion runs from the grown states (305, 758, 997) found nothing in 9 minutes each. One n is certified from here: 815, by 9.2e-10 of score, a by-product of a control.**

This avenue had one job. Take the held packing of n, set a small square in one of its waste pockets, and grow that square while every other square may move. If the square reaches side 1 in a box below the held side of n + 1, that is a smaller packing of n + 1. If it does not, the largest side per pocket says where one more square almost fits.

Words used here. "Held" is `gather/round9-2026-11-11a.csv` (22.1910935047, gate dir `gate/cand-round9-1111a`). The side is `L = m + f` with `m` whole, and `k = n - m²`. The "step" of n is `L(n + 1) - L(n)` in the held file. `B0` is the box of side `L(n)`. `B1` is the box of side `L(n + 1) - 1e-6`. The "seed" of a pocket is the largest square that fits there while every other square is frozen. `s_max` is the largest side the grow reaches. Stacks, arms, caps and the corner zone are those of [frontier](frontier.md).

## 1. Which pockets can gather waste

This section was derived before the map ran. Section 4 sets it against the measurement.

A two-arm layout at side `m + f` is tight across every row. An arm strip is `W = c - 1 + f` wide, and a flush stack of `c` squares at tilt `t` spans `c cos t + sin t = W`. The upright block beside it has `m - c + 1` columns in a width of exactly `m - c + 1`. So the waste of 7 to 10 squares is in pieces, and each piece has its own rule.

| piece | where | free square it holds | can it gather more |
|---|---|---|---|
| tooth | both ends of every flush stack | a right triangle with legs 1 and `tan t`. The largest square in it is `tan t / (1 + tan t)`, 0.27 at 20° | No. Its neighbours are two rigid stacks and a wall or a tight column |
| slot | a row of `c - 1` upright squares across an arm strip, in a cap or in the corner zone | `f` wide and 1 long. The uprights slide, so the whole `f` comes to one place | Only what the box gives across the strip: `f` in B0, `f` + step in B1 |
| wedge | between pieces of different tilt in a cap or in the corner zone | 0.5 to 0.8 | Yes. It lies at the end of a flush run |

A slot cannot grow past `f` by turning its row into a stack. A row of length `l = c - 1 + s` at tilt `u` spans `l cos u + sin u`. That span is above `l` for every `u` below `2 atan(1 / l)`, which is 14° at `l = 8`. So `s` must first fall by `1 / (2 W)`, about 0.06, before it can rise. A method that only climbs stops at `f`.

A larger box gives every strip the step across. Along the wall an arm gives more. Each flush stack can turn upright by `step / (c sin t - cos t)`, which shortens its pitch `1 / cos t`. An arm of `N` stacks frees

`F = step × (1 + N tan t / (cos t (c sin t - cos t)))`

of wall at one of its ends. For `N` = 13 and `c` = 8 at 17° that is 4.0 steps. The stacks slide along the wall, so the arm can deliver `F` to its cap or to the corner zone.

Three predictions follow.

1. A slot pocket reaches exactly `f` in B0 and exactly `f` + step in B1.
2. A wedge pocket at the end of a flush run reaches its B0 value plus `F` in B1. If the pocket lies on the tilted end of a stack whose only limit is the far wall, the gain is `F / sin t`, about three times more. The ranking of the map used this larger lever for every cap pocket and for corner pockets inside one strip.
3. A tooth stays near 0.27, and a pocket inside the upright block does not exist.

So a pocket reaches 1 only where a wedge pocket already holds a free square of `1 - F` or more in B0. With `F` between 0.03 and 0.10 that is a free square of 0.90 to 0.97 in a layout that is one square short.

## 2. The tool

[`inflate.py`](../inflate.py) has two parts.

**Pockets.** The clearance of a point is its distance to the nearest square or wall. The tool computes it on a grid of 0.02 and keeps the 8 highest local maxima that are at least 0.45 apart. For each one it grows a square with every other square frozen, from four start angles, and keeps the largest. That square is the seed.

**Grow.** The variables are the move of every square (`dx`, `dy`, `dangle` inside a trust region of 0.05 and 0.02 rad) and the side `s` of the new square. The objective is the largest `s`. The constraints are the separation of every near pair on its best axis, with the new square at side `s`, and the four walls of the fixed box. The axis choice and the rule for the kink of `|cos| + |sin|` are those of `methods_lp.py` (`best_axes`, `_signs`). The tool adds the rows of a square of side `s` and the rows of the fixed walls. A grow stops when `s` gains less than 1e-6 over 10 steps, when `s` reaches `1 - 1e-7`, or at its time cap. The table marks a grow that the time cap cut.

Four details of the LP decide whether it works. Each one cost a failed control before it was right.

- **Every move has a small cost.** Each `dx`, `dy` and `dangle` is split in two non-negative parts with a cost of 1e-6 against 1 for `s`. Without it the solver moves every free square to the edge of its trust region at each step.
- **The side is cut to what fits after each LP.** The LP drops the product of the change of `s` and the change of angle. In the first step that product left an overlap of 2e-6 that no later step removed. The gap of a pair is linear in `s` on each axis, so the largest `s` that fits at the new place is exact (`s_fit`).
- **A repair LP follows a step that leaves an overlap.** In a jammed box the usual repair with frozen angles is infeasible. A stack that turned by 0.02 rad is 1e-5 too long, and only a turn takes that back. The repair is the same LP from the new point with an angle trust radius of 20 times the overlap. A step counts when the true geometry overlaps by less than 1e-6 and `s` grew.
- **Only the tilted squares and the squares within 5 of the new one may turn.** With every square free to turn the LP takes 6.8 s of CPU at n = 814. With this rule it takes 2.5 s on the dual simplex and 0.8 s on the interior point method.

Three traps of the solver, for whoever runs this next:

- The interior point method of the HiGHS in scipy 1.13.1 crashes with a segmentation fault on some of these LPs. That scipy is the newest for the Python 3.9 of boxC. `INFLATE_FORK=1` runs each LP in a forked child, and the dual simplex solves the LP again when the child dies.
- At tolerances of 1e-10 the same HiGHS answers "model status unknown" on the repair LPs. The tool asks 1e-8.
- `methods_lp.py` asks a gap of 4e-11 of every pair and keeps a result only at 2.5e-11. On boxA (scipy 1.18.1) its LP returned a smallest gap of -1.6e-11 on a grown state, so the squeeze did not move. `inflate.py` runs `methods_lp.slp` down a ladder of asked gaps (1e-8, 1e-9, 2e-10, 4e-11) and keeps the smallest legal side.

When `s` reaches 1 the tool scales the centres apart by 4e-6, squeezes the n + 1 squares with `methods_lp.slp` and writes raw rows. `methods_take.py` certifies them.

## 3. Controls

**Positive.** The control deletes one square of the held n + 1. It starts a square of side 0.3 at the centre of the hole, upright, in the box of the held side. The side must come back to 1. All four did.

| held n + 1 | square deleted | its tilt | s reached | steps | seconds | side after the squeeze, minus the held side |
|---|---|---|---|---|---|---|
| 815 | cap, at (21.120, 7.348) | -15.93° | 1.000000000000 | 49 | 78 | -2.63e-08 |
| 924 | corner zone, tilted, at (5.540, 4.541) | -4.78° | 0.999999999766 | 9 | 10 | +4.41e-09 |
| 924 | corner zone, upright, at (4.500, 3.882) | 0° | 0.999999999022 | 1 | 1 | +4.42e-09 |
| 704 | grid edge, at (14.500, 7.463) | 0° | 1.000000000000 | 7 | 13 | +3.82e-09 |

The cap square is the hard case. The new square starts upright in a hole tilted by 16°, fills it to 0.81 in one step and then turns into it over 48 steps.

The squeeze of the 815 control ended 2.63e-08 below the held side of 815. `methods_take.py` certifies it: 0.014633524222 against the held 0.014633525143, a gain of 9.2e-10 of score. It is a by-product of the control and it is in the take dir.

**Negative: the plain grid has no pocket.** The grids of n = 25, 289 and 961 were set in boxes of side 5, 17 and 31. The largest clearance is 0 and the tool finds 0 pockets.

**Negative: a held layout in the box of its own side must not reach 1.** The B0 column of the map is this control on every layout. 64 grows ran in the box of the held side and none reached 1. The largest is 0.9269 at n = 340, a slot of width `f` = 0.9269. The largest that is not a slot is 0.7994, at n = 975.

## 4. The map

The sample is 40 values of n, two to four per shell from m = 17 to 31, with `f` from 0.70 to 0.98. All 40 ran. Four more layouts were added after the first results. 341, 380 and 421 are on the family line of 304. 419 has the third largest step of the layouts with `f` above 0.9.

Per layout the 8 pockets were ranked by the predicted side of section 1. The first 3 to 8 grew in B1 and the first 1 to 3 in B0. A grow had a cap of 45 to 110 s. The 15 best capped grows were continued for up to 400 s. In all, 167 grows ran in B1 and 64 in B0. A grow that ended at its cap is marked `time`, and its `s_max` is a lower bound. That is 77 of the 167 grows in B1 and 5 of the 64 in B0. Of the ten best pockets in B1, all ten ended at a stall. Everything ran on boxC with 5 processes, from 20:44 to 21:30 UTC.

The table has one row per layout, for its best pocket in B1. The pocket kinds `wall`, `inner` and `grid` are on layouts where the tool found no pair of flush arms, or outside the arm strips. "Gain per step" is `(s_max in B1 - s_max in B0) / step`.

| n | m | k | f | step to n + 1 | pockets grown | best pocket | seed | s_max at B0 | s_max at B1 | stop | gain per step |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 297 | 17 | 8 | 0.7404 | 0.0378 | 3 | wall | 0.6306 | 0.6790 | 0.7782 | stall | 2.63 |
| 304 | 17 | 15 | 0.9209 | 0.0295 | 3 | cap | 0.6764 | 0.6764 | 0.9122 | stall | 7.99 |
| 338 | 18 | 14 | 0.8776 | 0.0286 | 3 | corner | 0.6407 |  | 0.8700 | stall |  |
| 340 | 18 | 16 | 0.9269 | 0.0158 | 3 | grid | 0.8937 | 0.9269 | 0.9427 | stall | 1.00 |
| 341 | 18 | 17 | 0.9427 | 0.0218 | 3 | wall | 0.7065 | 0.7791 | 0.8694 | stall | 4.15 |
| 370 | 19 | 9 | 0.7575 | 0.0188 | 3 | inner | 0.6819 | 0.6820 | 0.7763 | stall | 5.02 |
| 378 | 19 | 17 | 0.9225 | 0.0202 | 3 | cap | 0.5938 |  | 0.9162 | stall |  |
| 380 | 19 | 19 | 0.9614 | 0.0134 | 3 | wall | 0.7231 | 0.7231 | 0.9034 | stall | 13.46 |
| 410 | 20 | 10 | 0.7721 | 0.0148 | 3 | wall | 0.7126 | 0.7165 | 0.7775 | stall | 4.12 |
| 418 | 20 | 18 | 0.9201 | 0.0147 | 3 | corner | 0.6383 |  | 0.8129 | time |  |
| 419 | 20 | 19 | 0.9348 | 0.0265 | 3 | cap | 0.6914 | 0.6914 | 0.9613 | stall | 10.20 |
| 421 | 20 | 21 | 0.9746 | 0.0090 | 3 | wall | 0.7558 | 0.7558 | 0.8917 | stall | 15.09 |
| 452 | 21 | 11 | 0.7632 | 0.0203 | 3 | wall | 0.6854 | 0.6854 | 0.7835 | stall | 4.83 |
| 461 | 21 | 20 | 0.9320 | 0.0168 | 3 | cap | 0.6879 | 0.6879 | 0.8274 | stall | 8.29 |
| 496 | 22 | 12 | 0.7811 | 0.0046 | 3 | grid | 0.7264 | 0.7811 | 0.7857 | stall | 1.00 |
| 503 | 22 | 19 | 0.8982 | 0.0169 | 3 | cap | 0.5822 |  | 0.8820 | time |  |
| 542 | 23 | 13 | 0.7849 | 0.0068 | 3 | wall | 0.5845 |  | 0.7918 | stall |  |
| 552 | 23 | 23 | 0.9401 | 0.0214 | 3 | cap | 0.7307 |  | 0.9197 | stall |  |
| 599 | 24 | 23 | 0.9237 | 0.0121 | 3 | cap | 0.7590 | 0.7590 | 0.8247 | time | 5.45 |
| 602 | 24 | 26 | 0.9709 | 0.0128 | 3 | corner | 0.6894 |  | 0.8911 | stall |  |
| 639 | 25 | 14 | 0.7811 | 0.0088 | 4 | cap | 0.6647 |  | 0.8151 | time |  |
| 645 | 25 | 20 | 0.8634 | 0.0197 | 3 | wall | 0.6992 | 0.7107 | 0.7913 | time | 4.09 |
| 652 | 25 | 27 | 0.9654 | 0.0152 | 4 | cap | 0.6712 |  | 0.8945 | stall |  |
| 702 | 26 | 26 | 0.9228 | 0.0242 | 4 | cap | 0.7579 | 0.7579 | 0.8827 | stall | 5.16 |
| 705 | 26 | 29 | 0.9769 | 0.0109 | 4 | corner | 0.7058 |  | 0.8718 | stall |  |
| 740 | 27 | 11 | 0.7070 | 0.0209 | 8 | cap | 0.6734 | 0.6874 | 0.7911 | time | 4.95 |
| 747 | 27 | 18 | 0.8112 | 0.0168 | 3 | cap | 0.7529 | 0.7544 | 0.8280 | stall | 4.37 |
| 757 | 27 | 28 | 0.9318 | 0.0269 | 3 | cap | 0.7609 | 0.7609 | 0.9586 | stall | 7.36 |
| 760 | 27 | 31 | 0.9847 | 0.0084 | 4 | cap | 0.7648 | 0.7648 | 0.8037 | time | 4.62 |
| 796 | 28 | 12 | 0.7215 | 0.0124 | 8 | corner | 0.7127 | 0.7815 | 0.8349 | stall | 4.29 |
| 803 | 28 | 19 | 0.8204 | 0.0093 | 3 | cap | 0.6143 | 0.6154 | 0.8297 | time | 22.95 |
| 814 | 28 | 30 | 0.9444 | 0.0215 | 4 | cap | 0.7666 | 0.7666 | 0.8897 | time | 5.71 |
| 852 | 29 | 11 | 0.6996 | 0.0075 | 8 | corner | 0.5670 |  | 0.7246 | stall |  |
| 857 | 29 | 16 | 0.7665 | 0.0129 | 3 | cap | 0.6639 |  | 0.7795 | stall |  |
| 863 | 29 | 22 | 0.8443 | 0.0076 | 3 | cap | 0.7012 | 0.7012 | 0.7649 | time | 8.34 |
| 873 | 29 | 32 | 0.9572 | 0.0157 | 4 | corner | 0.7450 |  | 0.8823 | stall |  |
| 911 | 30 | 11 | 0.6956 | 0.0076 | 8 | cap | 0.6813 | 0.6872 | 0.7196 | stall | 4.24 |
| 923 | 30 | 23 | 0.8472 | 0.0081 | 3 | cap | 0.7879 | 0.7900 | 0.8331 | stall | 5.30 |
| 932 | 30 | 32 | 0.9409 | 0.0089 | 4 | corner | 0.7650 | 0.7650 | 0.8028 | stall | 4.23 |
| 935 | 30 | 35 | 0.9799 | 0.0176 | 4 | cap | 0.7620 | 0.7620 | 0.8850 | stall | 6.98 |
| 975 | 31 | 14 | 0.7215 | 0.0124 | 8 | cap | 0.7126 | 0.7994 | 0.8350 | stall | 2.87 |
| 983 | 31 | 22 | 0.8169 | 0.0176 | 3 | corner | 0.7442 |  | 0.8340 | time |  |
| 986 | 31 | 25 | 0.8593 | 0.0066 | 3 | cap | 0.7453 | 0.7750 | 0.8051 | time | 4.58 |
| 996 | 31 | 35 | 0.9555 | 0.0181 | 4 | cap | 0.7660 | 0.7660 | 0.9308 | stall | 9.08 |

The full table, one row per pocket, is [`results/inflate-r10-2026-11-11.tsv`](../results/inflate-r10-2026-11-11.tsv).

What the map says:

- **The slot rule is exact.** 10 pockets on 8 layouts are slots. Each one reached `f` in B0 with a difference of 0.000000. In B1 each one reached `f` plus the step, less the 1e-6 of the box. Their gain per step is 1.00. A slot is the best pocket of two layouts, 496 and 340. At 340 it is 0.9427 wide because `f` is 0.9269. That is one of the eight values above 0.9, and it says nothing about a fit: the row holds one more square only at side `m + 1`.
- **From n = 552 up, every layout with `f` above 0.92 holds a pocket of nearly the same size.** The sample has 12 such layouts: 552, 599, 652, 702, 705, 757, 760, 814, 873, 932, 935 and 996. The seed is 0.754 to 0.767 on all of them. It is in a cap on 11 of them and in the corner zone of 932, and it does not grow at all in B0. This is the end cap that the public files share ([frontier](frontier.md), section 3), measured as a pocket. In shells 17 to 21 (304, 378, 418, 419, 461) and at 602 the first pocket is 0.676 to 0.695.
- **In B1 a wedge pocket gains 3 to 10 times the step.** On the 26 wedge pockets where both grows stalled the gain per step is 2.6 to 15.1, median 5.2. The two values above 10.2 are at 380 (13.5) and 421 (15.1), layouts without a pair of flush arms. The freed wall `F` alone is 3 to 4 steps, so part of the lever `1 / sin t` is real. On 304, 419, 418 and 461 the stacks hold 6 squares, and the prediction with the full lever holds within 0.04. It gave 0.9022, 0.9236, 0.8015 and 0.8491. They reached 0.9122, 0.9613, 0.8084 and 0.8274. 338 also has stacks of 6 squares, and there the prediction is 0.05 too high (0.8674 against 0.8162). On the layouts with stacks of 7 or 8 squares the prediction is too high. It gave 1.0 for 757, 996, 935 and 873, and they stalled at 0.9586, 0.9308, 0.8850 and 0.8757. On 503, 602, 652, 702, 747 and 932 the gain is 28% to 56% of the predicted gain. The derivation assumes that the far wall is the only limit of the pocket. Either that is false on those layouts or the grow stops before the arm has given all of `F`. This round did not separate the two.
- **The step decides.** `s_max` in B1 is the cap pocket plus a multiple of the step, and the cap pocket is nearly the same everywhere. The layouts above 0.9 are those with `f` above 0.92 and a large step: 419 (step 0.0265), 757 (0.0269), 304 (0.0295), 552 (0.0214) and 378 (0.0202). 996 and 380 have smaller steps (0.0181 and 0.0134) and a gain per step of 9.1 and 13.5.
- **No pocket reaches 1, and the best is 0.004 of side short.** A straight line through the two boxes of a pocket gives the box where it would reach 1. That box is above the held side of n + 1 on every pocket where both grows stalled. The distance is 0.0038 at 419, 0.0056 at 757, 0.0072 at 380 and at 421, 0.0076 at 996 and 0.0110 at 304. On the other 20 it is 0.017 to 0.099. The line is an estimate from two points.
- **Below `f` = 0.85 the best pocket is 0.72 to 0.84** on all 18 such layouts. The best are 975 (0.8350) and 796 (0.8349), both at `f` = 0.7215.

## 5. Verdict against the kill line

The kill line was a best `s_max` in B1 below 0.85. The best is 0.9613 and 19 of the 44 layouts are above 0.85, so the map did not stop there. With pockets above 0.9 it went on to the two next steps.

**The family line.** 304 has `k - 2m = -19`. Its neighbours on that line are 341 (m = 18), 380 (m = 19) and 421 (m = 20). The tool finds no pair of flush arms on any of the three. Their best pockets reach 0.8694, 0.9034 and 0.8917. So the line does not carry the 0.91 of 304 upward. 419 (`k - 2m = -21`, stacks of 6 squares as in 304) was added for its step and reached 0.9613, the best of the round. It came in the last minutes, and no insertion run started from it.

**Insertion runs.** `methods_soft.py` started from the grown states of 304, 757 and 996. The new square was set to side 1 and its centre was pulled inside the box, so it overlaps its neighbours by 0.04 to 0.09. The island box was 1e-4 below B1.

| n + 1 | pocket side before | seconds | children | restarts | overlap energy at the start and at the end | finds |
|---|---|---|---|---|---|---|
| 305 | 0.9122 | 560 | 253,127 | 84 | 3.6e-04, 2.4e-04 | 0 |
| 758 | 0.9586 | 540 | 119,080 | 39 | 1.7e-04, 1.0e-04 | 0 |
| 997 | 0.9308 | 560 | 87,169 | 29 | 2.0e-04, 1.4e-04 | 0 |

A member is soft-free below an energy of `1e-10 n`, which is 3e-8 to 1e-7 here. No island came within a factor of 1,000 of it. No box dropped, and no run wrote a packing for the certifier.

So the map answers the question of this avenue. A unit square is nearest in the cap pocket of a layout with `f` above 0.92 and a large step. Nearest there means 0.004 to 0.011 of side short. The soft search does not close that: its finds on this file are steps of 1e-4 to 4e-3 of side ([methods](methods.md), section 3c).

## 6. What to run next

1. **Measure the box where the cap pocket reaches 1, on a ladder of boxes.** Call it `B*`. `B* - L(n + 1)` is what the pocket path costs over the held n + 1, as a measured number in place of the straight line of section 4. A hit is `B* < L(n + 1)`. It needs four grows per n, about 15 CPU-minutes. Run it on the layouts with `f` above 0.9, largest step first, because the step decides. The 15 largest steps there are at 304, 757, 419, 702, 417, 341, 505, 377, 814, 552, 339, 378, 651, 600 and 462.
2. **Give the grows of the map their time.** A grow needs 100 to 400 s at n above 500, and the caps of this round were 45 to 110 s. Let the 77 capped grows run to their stall. With `--seconds 400` and 3 pockets per layout that is about 35 CPU-minutes per n.
3. **Use the cap pocket as the measure of an end cap.** At `f` above 0.92 the cap holds a free square of 0.76, and no move of the layout uses it in its own box. A cap solver ([frontier](frontier.md), section 6) can test a new cap for a free square above 0.5 before it counts squares. The test costs seconds.
4. **Do not run insertion searches from these states.** The three runs of section 5 lowered the overlap energy by a third in 9 minutes each. The gap to close is 0.004 to 0.011 of side, and the soft search closes steps of 1e-4 to 4e-3. One run from the state of 419 is the only one still worth its 10 minutes, because 0.0038 is at the edge of that range.
5. **Do not map teeth, slots or layouts with `f` below 0.85.** The rules of section 1 give their value without a run.

## Files

| file | what it does |
|---|---|
| [`inflate.py`](../inflate.py) | `pockets`, `map` (pockets, then the grow in B1 and B0), `cont` (grow on from a state that the time cap cut), `ctlpos`, `ctlgrid`, `squeeze` |
| [`results/inflate-r10-2026-11-11.tsv`](../results/inflate-r10-2026-11-11.tsv) | the map, one row per pocket: seed, predicted side, `s_max` and stop reason in B0 and B1, the gain per step |
| [`results/inflate-r10-controls-2026-11-11.tsv`](../results/inflate-r10-controls-2026-11-11.tsv) | the controls |

`inflate.py` is our own code. It imports `methods_lp.py` and, for the names of the zones, `frontier_profile.py`.

On boxA, under `<scratch>/bounties-squares/take-inflate-r10`: `take.tsv` and `815.csv` (the by-product of the control), and `work/` with the per-n map tables, the grown states and the logs.

To repeat: `inflate.py ctlgrid OUT`, `inflate.py ctlpos HELD.csv DETAILS.csv OUT --ns 815 --kinds cap`, `inflate.py map HELD.csv DETAILS.csv OUT --ns 814,996 --top 3 --top0 1 --seconds 45`, `inflate.py cont DETAILS.csv OUT OUT/state/996-p0-B1.csv --seconds 400`.

## Summary

- **No n + 1 is smaller by this path.** No pocket reached side 1 in the box below the held side of n + 1. That holds on the 40 layouts of the sample and on 4 more.
- **The tool passes its controls.** A deleted square comes back to side 1 from 0.3 in all four cases: cap, corner zone twice, grid edge. The squeeze then returns to the held side within 5e-9 on three of them and ends 2.6e-8 below it on 815. The plain grid has no pocket. No held layout reached 1 in the box of its own side.
- **A slot pocket holds exactly `f`** and gains exactly the step. It is the best pocket only below `f` = 0.8.
- **Layouts with `f` above 0.92 hold one cap pocket of 0.75 to 0.77** (0.68 to 0.70 in shells 17 to 21). It does not grow in the layout's own box. In the box of n + 1 it gains 5 to 10 times the step.
- **The best is 0.9613 at n = 419, then 0.9586 at n = 757.** Eight layouts pass 0.9: 419, 757, 340, 996, 552, 378, 304 and 380. The one at 340 is a slot. The straight line through the two boxes puts the unit square 0.0038 of side above the held 420, 0.0056 above 758, 0.0076 above 997 and 0.0110 above 305.
- **Three insertion runs of 9 minutes found nothing** (305, 758, 997). The overlap energy fell by a third and stayed 1,000 times above soft-free.
- **815 is certified 9.2e-10 of score below the held file,** from the squeeze of a control. It is in the take dir.
- **Next:** measure the box where the cap pocket reaches 1 on the 15 layouts with `f` above 0.9 and the largest steps, and finish the capped grows of the map. One insertion run from the state of 419, and no others.
