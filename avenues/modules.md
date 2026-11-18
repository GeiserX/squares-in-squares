# Avenue: modules (2026-11-11 and 12, rounds 10 to 16)

**Result: 28 n certify below the held file, for a gain of 0.0013925. Nothing was submitted from here. The take is in `<scratch>/bounties-squares/take-modules-r10`. Control 1 passes on 97 of 122 layouts and control 2 does not pass before the squeeze. The main measured reason is the same for both: the upright grid beside a zone is not rigid. The library closes about 1% of the gap to the board, because the board's end zones are not in it.**

Sections 1 to 8 are round 1, against the held file of round 9. [Round 2](#round-2-2026-11-11-round-11) is the second run, against the held file of round 10: the library grown with the wins, the slide of the grid as a part of the module, and what the library still lacks. [Round 3](#round-3-2026-11-12-round-12) is the third run, against the held file of round 11: corner tables without the points between states, corners with a grant, the zones of the zone lanes, the generator over every n, and low side fractions. [Round 4](#round-4-2026-11-12-round-13) is the fourth run, against the held file of round 12. It covers the head cell of a granted corner, the rebuilt zone corners, the generator over every n with the 5 states, the far zones with no table yet, and the layouts grown from rounds 12 and 13. [Round 5](#round-5-2026-11-12-round-14) is the fifth run, against the held file of round 13. It covers the layouts of round 13 grown, the far zones with no table, grant variants with their grant in place, why the 601 row fails, and far zones walked by smaller steps.

This avenue had one job. It takes the zone-loss model of the [frontier avenue](frontier.md) and cuts the layouts we have into end zones that can be used again. A generator then picks the best end zones for each n.

Words used here: "held" is `gather/round9-2026-11-11a.csv` (22.1910935047, gate dir `gate/cand-round9-1111a`). "The board" is the per-puzzle board, the best side per n over all teams ([`results/per-puzzle-lb-2026-11-09.json`](../results/per-puzzle-lb-2026-11-09.json)). The side is `L = m + f` with `m` whole, and `k = n - m²`. A "stack" is a row of `c` tilted squares set face to face. An "arm" is a row of stacks along a wall. A "module" is one end zone cut from a layout: the corner where the two arms meet, or the far end of one arm. The tool is [`modules.py`](../modules.py).

## 1. The model and our check of it

An arm sits in a strip of width `W = c - 1 + f` along a wall. A stack is flush when it touches both sides of its strip. Its tilt `t` then solves `c cos t + sin t = c - 1 + f`. A flush stack takes `p = 1 / cos t` of wall (the pitch). An arm of flush stacks holds `g = f - sin t` squares more per unit of wall than `c - 1` columns of the plain grid.

Arm 1 runs along the whole left wall and arm 2 along the rest of the bottom wall. If both arms were flush from end to end, the layout would hold `m² + k_flush` squares:

```
k_flush = (m + f) g1 + (c1 - 1) f + (m - c1 + 1) g2
loss    = k_flush - k
```

The loss is the number of squares that the three end zones cost. We checked three things with our own code on the 71 held layouts that cut cleanly.

1. The loss is the sum of three zone losses. The model loss and the sum of the corner loss and the two far losses differ by 0.034 squares in the median (0.247 at most). The stacks between the zones are flush to 1.4e-9 in the median (2.8e-3 at most).
2. The board loses fewer squares than we do, and most of the difference is at low f. For f below 0.87 (22 layouts) our loss is 1.29 squares above the board's in the median (0.59 to 2.80). For f of 0.87 and more (49 layouts) it is 0.54 above (0.00 to 1.19). Examples: n=757 8.81 against 8.81, n=814 9.23 against 9.12, n=756 8.98 against 8.88, n=873 9.77 against 9.26.
3. The gap to the board for n of 300 and more below the plain grid is 0.1338 over 413 n. The 257 n with f below 0.85 hold 0.0972 of it. The 156 n with f of 0.85 and more hold 0.0366.

| arms | band of f | our loss | board loss |
|---|---|---|---|
| 8 and 8 | 0.65 to 0.75 | 8.12 to 8.98 | 6.18 to 7.39 |
| 8 and 8 | 0.75 to 0.87 | 9.57 to 9.81 | 7.44 to 8.52 |
| 8 and 8 | 0.87 to 0.94 | 8.80 to 9.50 | 8.60 to 8.88 |
| 8 and 8 | 0.94 to 1.00 | 9.23 to 9.84 | 8.78 to 9.28 |
| 7 and 7 | 0.75 to 0.87 | 7.18 to 7.40 | 5.25 to 6.10 |
| 7 and 7 | 0.94 to 1.00 | 8.35 to 8.95 | 7.61 to 7.93 |
| 6 and 6 | 0.87 to 0.94 | 5.20 to 6.03 | 5.01 to 5.64 |

## 2. The cut

We turn every layout so that arm 1 is on the left wall and arm 2 on the bottom wall. The far face of the last flush stack of an arm is a straight line across the whole strip. So is the near face of the first one. We cut there, at the middle line of the strip.

- The corner is everything between the two walls and the first flush stack of each arm. It ends at `y0` on arm 1 and at `x0` on arm 2.
- A far zone is everything between the last flush stack and the end wall. Its length is `l`.
- The rest is the upright grid, `(m - c1 + 1)` by `(m - c2 + 1)` cells. A grid cell with no upright square in it belongs to the zone at that corner of the grid.

With `s1` and `s2` flush stacks the cut gives two length sums and one count sum. The length sums hold by the way the cut defines its lengths. They are not a property of the layout: the stacks of a run have small gaps between them (up to 0.011 of wall for one arm, measured on 14 layouts), and no zone counts that room. So the three zone losses miss `k_flush - k` by up to 0.25 squares.

```
y0 + s1 p1 + l1 = m + f
x0 + s2 p2 + l2 = m + f
n = corner + s1 c1 + far1 + s2 c2 + far2 + rest
far loss    = c cos t * l - count
corner loss = c1 cos t1 * y0 + c2 cos t2 * (x0 - W1) - count
```

The squares of the rest are not on the grid exactly. They sit up to 0.035 off their cell and tilt up to 0.5 degrees. The cut accepts a square as rest within 0.3 of a cell and 2 degrees of upright.

## 3. The library

`modules.py library` cut the held file and every public packing with an accepted licence (Apache 2.0, CC BY 4.0, CC0) whose side differs from the held side.

- 71 held layouts and 51 public layouts cut cleanly. They give 366 modules: 122 corners and 244 far zones.
- Not cut in the held file: 624 layouts have no two flush arms, 5 have a broken rest, and 1 has an empty rest. In the public files the counts are 850, 8 and 1.
- 213 modules are from held layouts and 153 from public layouts. Of the public ones, 141 are Apache 2.0, 9 are CC BY 4.0 and 3 are CC0. The largest public sources are `jazivxt/boxed-in-sub` (69 modules), `prvsiyan/a-square-deal-research-to-verified-packings` (30) and `malyshevdanil/squares-in-squares-living-atlas-of-tight-packings` (18).

[`results/modules-library-2026-11-11.tsv`](../results/modules-library-2026-11-11.tsv) has one row per module: kind, c, signature, count, length, f, tilt, loss, the lowest f at which the module still exists, source and licence.

The signature of a far zone names the sub-stacks, the leaning squares and the uprights. For example `c8:7.5.4|l0|u13` is a zone of an 8-arm with sub-stacks of 7, 5 and 4 squares, no other leaning square and 13 uprights.

| kind | c | instances | distinct signatures |
|---|---|---|---|
| far | 5 | 1 | 1 |
| far | 6 | 57 | 31 |
| far | 7 | 73 | 49 |
| far | 8 | 93 | 72 |
| far | 9 | 12 | 12 |
| far | 10 | 6 | 6 |
| far | 11 | 2 | 2 |
| corner | 8 and 8 | 30 | 30 |
| corner | 7 and 7 | 23 | 20 |
| corner | 6 and 6 | 18 | 18 |
| corner | 8 and 7 | 10 | 10 |
| corner | 8 and 6 | 8 | 8 |
| corner | 13 other pairs | 33 | 33 |

### Loss as a function of signature and f

The full signature is too fine: 244 far zones have 172 signatures, and most signatures appear once. A coarser key works. We group far zones by (c, count, number of uprights) and call the group a family. There are 81 families.

- In a family the loss is a straight line in f. Over the 22 families with three or more instances, the median residual is 0.003 squares (0.068 at most). This is the fit of a line to its own points. When one f is left out and predicted from the others (113 points, families with four or more f), the error is 0.009 squares in the median, 0.070 at 90% and 0.24 at most.
- Two zones with the same signature at the same f (to 1e-3) differ in loss by 0.0010 squares in the median (0.0190 at most). One pair is far outside: `652h.F2` and `652h09.F2` are 0.00095 of f apart and differ by 0.12 squares. One of them pokes into the rest (section "Round 2").

So the loss follows the family and f, to about 0.01 squares out of sample. Typical far losses:

| c | family | band of f | loss |
|---|---|---|---|
| 8 | count 29, 13 uprights | 0.92 to 0.947 | about 2.71 |
| 8 | several | 0.957 to 0.973 | 2.80 to 2.93 |
| 8 | count 23, 4 uprights | 0.82 to 0.845 | 3.13 to 3.17 |
| 8 | count 41 | 0.69 to 0.71 | 2.72 to 2.79 |
| 7 | several | 0.82 to 0.86 | 2.2 to 2.3 |
| 7 | several | 0.93 to 0.94 | 2.4 to 2.5 |
| 7 | several | 0.946 and more | 2.69 to 2.79 |
| 6 | several | 0.77 to 0.82 | 1.6 |
| 6 | several | 0.92 to 0.94 | 1.76 to 1.88 |
| 6 | several | 0.94 to 0.97 | 1.9 to 2.1 |

The corners of two 8-arms lose from 2.50 squares (n=740, f 0.707) to 4.13 (n=934, f 0.964). Others: 3.29 (702), 3.32 (756), 3.39 (757), 3.45 (996), 3.56 (933), 3.58 (813), 3.75 to 3.81 (814) and 4.07 (873).

### The count classes

For two equal arms of c, the count of the corner plus the two far zones must equal `(k - 2m - 1) mod c`. We call this number the class of n. The class is the same along a family line `(m, k) -> (m + 1, k + 2)`.

The library serves few classes. All far zones of an 8-arm at f of 0.92 and more hold 29, 37, 45, 53 or 61 squares, which is 5 mod 8. The corners of two 8-arms hold 2 or 3 mod 8, with three exceptions. So two 8-arms at high f reach classes 4 and 5 cheaply, and the other classes cost more or do not exist.

Lowest sum of the three losses, as found in a layout, by class:

| arms | band of f | classes with a layout (loss) | classes with none |
|---|---|---|---|
| 8 and 8 | below 0.78 | 0 (9.15), 1 (8.03), 3 (8.99), 4 (7.87), 6 (8.18), 7 (8.41) | 2, 5 |
| 8 and 8 | 0.78 to 0.90 | 1 (9.56), 5 (8.90), 7 (9.43) | 0, 2, 3, 4, 6 |
| 8 and 8 | 0.90 and more | 1 (10.64), 2 (9.95), 3 (9.34), 4 (8.72), 5 (8.69) | 0, 6, 7 |
| 7 and 7 | below 0.78 | none | all |
| 7 and 7 | 0.78 to 0.90 | 4 (7.34), 5 (7.12) | 0, 1, 2, 3, 6 |
| 7 and 7 | 0.90 and more | 1 (7.74), 2 (7.99), 3 (8.20), 4 (8.48) | 0, 5, 6 |
| 6 and 6 | below 0.78 | none | all |
| 6 and 6 | 0.78 to 0.90 | 1 (5.12) | 0, 2, 3, 4, 5 |
| 6 and 6 | 0.90 and more | 0 (5.89), 1 (5.51), 2 (5.58), 3 (6.12), 4 (5.31), 5 (5.81) | none |

## 4. The generator

For a target n the generator tries every corner and, for each arm, every far zone with the right c. For each pair of stack counts `(s1, s2)` that gives n squares, it finds the smallest f at which both length sums of section 2 hold. It ranks the choices by that f.

The generator needs the length of a module at an f other than the one it was found at. We get it from geometry, because only 22 families have three or more instances. `modules.py lens` does this for each module:

1. Turn the squares that share the arm's tilt to the flush tilt of the new f.
2. Push the next flush stack toward the end wall with a contact LP. The squares of the rest that touch the zone are fixed on the grid.
3. Continue in steps of 0.005 in f, and store the length on a grid of f.

A corner has two lengths, `y0` and `x0`, and it can trade one for the other. The table stores this trade as a line through five LP solutions with different weights on the two lengths.

A layout put together from modules at their LP positions is legal. But a predicted side is not an upper bound by construction, as the first version of this doc said. The state of a module depends on the steps in f it took. In round 1 the tables and the build took different steps, so a table could promise a length that the build did not reach. For `756h11.F2` at the f of n=933 the table was 0.04 shorter than the build's path. In the logs of round 1, 8 of 89 choices needed a start 0.0015 or more above the prediction, or had no start. Since round 2 the build walks the knots of the table (section "Round 2").

We measured the geometry at the f each far zone was found at. The LP length is 0.0013 above the found length in the median (the first version had the sign wrong). It is longer on 198 of 242 far zones and shorter on 9. The rigid grid beside a zone makes the zone longer, and almost no found zone can be pushed further. The table of a far zone starts 0.10 of f below the f it was found at, which is the `SPAN` constant. The `lock` column of the library table is that lower end of the table, not a measured limit.

The tables carry a far zone badly above the f it was found at. 68 of 232 far tables grow there. Found zones of one signature do the opposite: they are never longer at a higher f (0 of 101 pairs), and they shrink by 0.0216 per 0.01 of f in the median. The median table shrinks by 0.0093 per 0.01.

## 5. Controls

### Control 1: a layout from its own modules

Control 1 asks the generator to return each library layout at its own f, to 1e-3, from its own three modules. It does not pass on every layout.

`modules.py rebuild` puts each layout together again exactly, at its own f plus the smallest step that gives a legal layout:

| step above the layout's own f | layouts |
|---|---|
| 0 | 37 |
| 1e-4 | 28 |
| 3e-4 | 20 |
| 1e-3 | 12 |
| 3e-3 | 7 |
| not within 3e-3 | 18 |

So 97 of 122 layouts come back within 1e-3 and 25 do not. From the length tables alone (`modules.py control`), 76 of 115 layouts come back within 1e-3. The median error is 4.6e-4, and the worst errors are -0.0029 and +0.0099.

The 25 failures have two measured causes.

- In 11 of them an arm is not flush: one stack is more than 1e-4 away from the flush tilt, so the cut has no straight line there.
- In the others the rest is not a rigid grid. Rows and columns of the rest slide as a whole into room that a zone leaves, and the zone uses that. In n=998 a square of the corner pokes 0.014 past the grid edge where a column slid. The corner LP against a fixed grid then gives `y0` 12.04444 against 12.00325 found, which is 0.041 of length or about 0.01 of f. In n=814 all 18 cells beside far zone 2 are off the grid.

The right cut keeps one sliding offset for each row and column of the rest beside a zone, and makes the offset part of the module. We tried the simple version, which gives the slid cells to the zone. It repaired 998, 935 and 340 and broke 814 and 757, because a slid row couples the zones at its two ends.

### Control 2: the neighbours of 814 on its line

The line of n=814 = (28, 30) is `(m, k) -> (m + 1, k + 2)`. Its neighbours are 757 = (27, 28) and 873 = (29, 32). All three have class 5. n=871 = (29, 30) has class 3 and is not on the line.

| modules of | target | stacks | f from the tables | f put together exactly | held f | difference |
|---|---|---|---|---|---|---|
| 814 | 757 | 12 and 12 | 0.9352 | 0.9358 | 0.9318 | +0.0040 |
| 814 | 873 | 14 and 14 | no fit | none | 0.9572 | |
| 757 | 814 | 13 and 12 | 0.9575 | 0.9491 | 0.9444 | +0.0047 |
| 757 | 873 | 14 and 13 | no fit | none | 0.9572 | |
| 873 | 814 | 14 and 11 | 0.9508 | 0.9507 | 0.9444 | +0.0063 |
| 873 | 757 | 13 and 10 | 0.9400 | 0.9397 | 0.9318 | +0.0079 |

Control 2 asks for 2e-3 and does not pass. The modules of 814 give 757 at +0.0040, and they do not reach 873 below f = 1. The held 873 has another corner (loss 4.07 against 3.75 to 3.81 for 814), but that is not shown to be the cause. A second cause is measured in the tables: the length of `814h.F1` is smallest at the f it was found at and grows on both sides (4.1444 at f 0.9444, 4.1615 at 0.957, 4.2478 at 0.995). At f = 0.957 the choice for 873 is short by 0.033 of room over the two arms, and the trend of found zones would give back about 0.025 for each arm. So the missing fit can come from the continuation alone.

The miss of 0.004 on 757 was put on the sliding of the rest. That is also not proven. The squeeze recovers it: 757 put together from the modules of 814 at side 27.936000 goes to 27.935022 with the LP and to 27.931847 with the fq quench. The held side is 27.931788, so the squeezed layout ends 5.9e-5 above it.

## 6. Predictions

`modules.py predict` ran the generator for every n of 300 and more whose held side is below the plain grid. [`results/modules-predict-2026-11-11.tsv`](../results/modules-predict-2026-11-11.tsv) has one row per n: n, m, k, held side, board side, predicted side, and the three modules with their sources and licences.

- 413 n are in the regime, and 378 get a prediction. The gap of these 378 to the board is 0.1291.
- 5 predictions are more than 0.002 of side below held, and 11 are more than 1e-4 below. 54 are within 1e-3 of held.
- If every prediction below held were built at its predicted side, the score would fall by 0.00093. That is 0.7% of the gap.

The 12 lowest predictions against held:

| n | held side | predicted side | predicted - held | corner | far 1 | far 2 | stacks |
|---|---|---|---|---|---|---|---|
| 911 | 30.695622 | 30.689620 | -0.006002 | 685h09.C | 852h.F2 | 852h.F2 | 9, 5 |
| 797 | 28.733980 | 28.729226 | -0.004753 | 740h.C | 740h.F1 | 740h.F1 | 13, 11 |
| 974 | 31.707107 | 31.703794 | -0.003313 | 740h.C | 495h11.F1 | 852h.F2 | 15, 10 |
| 652 | 25.965441 | 25.962253 | -0.003188 | 505h.C | 934h.F1 | 462h10.F2 | 12, 9 |
| 934 | 30.964143 | 30.961239 | -0.002904 | 934h.C | 934h.F1 | 814h09.F1 | 15, 14 |
| 705 | 26.976897 | 26.974976 | -0.001921 | 505h.C | 874h.F1 | 462h10.F2 | 13, 10 |
| 873 | 29.957161 | 29.955275 | -0.001886 | 934h.C | 996h.F2 | 504h.F2 | 15, 10 |
| 933 | 30.949834 | 30.948198 | -0.001637 | 933h.C | 504h.F2 | 504h.F2 | 12, 7 |
| 601 | 24.955539 | 24.954903 | -0.000636 | 505h.C | 814h09.F1 | 462h10.F2 | 12, 8 |
| 997 | 31.973617 | 31.973270 | -0.000347 | 873h.C | 874h.F1 | 874h.F1 | 16, 13 |
| 740 | 27.706994 | 27.706774 | -0.000220 | 740h.C | 740h.F1 | 740h.F1 | 12, 10 |
| 987 | 31.865851 | 31.865751 | -0.000100 | 924h.C | 863h.F1 | 863h.F1 | 15, 15 |

A module id is the n of its layout, a tag for the file (`h` is held, `h07` to `h11g` are the public merges) and the zone.

### How much of the gap the library closes

Under 1%. This number is measured. The reason is not proven by the predictions. When every module of a held layout's n is taken away, the generator predicts that layout 0.0030 of f above its held side in the median, and within 1e-3 on 10 of 70 layouts (leave one out, measured by the review of round 1). So a prediction within 0.005 of held does not tell a missing module from a module that the tables carry badly. Only a prediction 0.01 or more above held shows a missing module. Only 71 of the 413 n are cut into modules, and they hold 0.0240 of the 0.1338.

The library holds the end zones of our own layouts and of public layouts at the same level. The board's sides imply zones that lose fewer squares (section 1), if the board uses our stack sizes. Putting known zones together in new ways moves a few n by 0.002 to 0.006 of side. It does not reach the board.

The builds of section 7 agree: 28 n certify for 0.0013925, which is 1.0% of 0.1338.

### Zones the library does not have

Median of predicted side minus held side, by band of the board's f:

| n | arms | board f 0.60 to 0.78 | 0.78 to 0.90 | 0.90 and more |
|---|---|---|---|---|
| 600 to 1000 | mostly 8 | +0.014 to +0.035 in every class | +0.0003 (class 2), +0.0009 (class 3), +0.010 to +0.023 (classes 0, 1, 4, 5, 6), +0.066 (class 7) | -0.0003 to +0.0013 in every class |
| 430 to 599 | mostly 7 | +0.006 to +0.048 | +0.013 to +0.054 | +0.0002 to +0.0035 |
| 300 to 429 | mostly 6 | +0.035 to +0.128 | +0.009 to +0.040 | 0.0000 to +0.0128, and +0.030 for class 3 |

In the cells of this table the held file is 0.0007 to 0.021 of side above the board in the median.

- At board f of 0.90 and more the library gives the held side again and no more. Our high-f zones are complete for what we hold. The board is 0.0025 to 0.010 lower there, so it has far zones or corners with about 0.5 squares less loss. For two 8-arms the board needs a three-zone loss of 8.6 to 8.9 at f 0.87 to 0.94. Our best is 8.69 to 8.72, in classes 4 and 5 only. Classes 0, 6 and 7 have no layout, and classes 1 and 2 cost 9.95 to 10.64.
- At board f of 0.78 to 0.90 the library has good zones for two classes of 8-arms. It also serves walls that leave half to three quarters of a pitch. For the other classes and remainders the prediction is 0.01 to 0.07 above held. The far zones of an 8-arm are at their worst here: the lowest loss is 3.11 at f 0.80, against 2.71 at f 0.92.
- At board f below 0.78 the library has almost nothing. It has four corners of two 8-arms (f 0.687 to 0.707) and one corner each for arms of 7 and 8, 8 and 6, and 9 and 9. It has no corner for two 7-arms or two 6-arms. This band and the one below 0.60 (71 n, outside the tables) hold 0.073 of the gap. Our held layouts there are mostly not two flush arms, so the cut finds no module in them.

A search for new zones should design these first:

1. Far zones and corners of two 8-arms at f 0.65 to 0.87 with a three-zone loss of 6.2 to 8.5, which is the board's level there. Ours is 8.1 to 9.8.
2. Far zones of an 8-arm at f of 0.90 and more with a count other than 5 mod 8. Corners with a count other than 2 or 3 mod 8. They open classes 0, 6 and 7 and make classes 1 and 2 cheaper.
3. Zones for pairs of 7-arms and 6-arms below f 0.78, where the library has none.

## 7. Builds

`modules.py build` puts the modules and the flush stacks together 2e-4 of f above the prediction. If that start is not legal it tries 6e-4, 1.5e-3 and 3e-3 above. `family_step.py` is not on main, so the squeeze is the lane's sequential LP (`methods_lp.slp`) and then the fq quench. `modules.py take` certifies with the lane's rule: floatsafe at 2.2e-11, and a score below held by more than 1e-10. The rule dropped 47 of the 85 raw files, so it can fail.

The 12 best predictions:

| n | held side | predicted | built | built - predicted | built - held | score gain, certified |
|---|---|---|---|---|---|---|
| 911 | 30.695622 | 30.689620 | 30.689167 | -0.000453 | -0.006455 | 2.139e-04 |
| 797 | 28.733980 | 28.729226 | 28.728121 | -0.001106 | -0.005859 | 2.075e-04 |
| 974 | 31.707107 | 31.703794 | 31.703437 | -0.000357 | -0.003669 | 1.176e-04 |
| 652 | 25.965441 | 25.962253 | 25.960803 | -0.001450 | -0.004638 | 1.816e-04 |
| 934 | 30.964143 | 30.961239 | no legal start within 0.003 | | | none |
| 705 | 26.976897 | 26.974976 | 26.972906 | -0.002070 | -0.003991 | 1.503e-04 |
| 873 | 29.957161 | 29.955275 | 29.957806 | +0.002531 | +0.000645 | none |
| 933 | 30.949834 | 30.948198 | 30.946867 | -0.001331 | -0.002967 | 9.714e-05 |
| 601 | 24.955539 | 24.954903 | 24.953958 | -0.000945 | -0.001580 | 6.446e-05 |
| 997 | 31.973617 | 31.973270 | 31.973018 | -0.000252 | -0.000599 | 1.896e-05 |
| 740 | 27.706994 | 27.706774 | 27.706460 | -0.000314 | -0.000534 | 1.963e-05 |
| 987 | 31.865851 | 31.865751 | 31.865746 | -0.000005 | -0.000105 | 3.335e-06 |

Ten of the 12 certify below held. Their gain is 0.0010744.

The squeeze lands below the prediction, so we also built every prediction up to 0.003 of side above held. That is 74 n in all, most with one choice of modules. 28 n certify, for 0.0013925. The 17 n with a gain above 1e-5 hold 0.0013581 of it. The other kept n:

| n | held side | predicted | built | built - held | modules (corner, far 1, far 2) | score gain, certified |
|---|---|---|---|---|---|---|
| 813 | 28.931300 | 28.931799 | 28.928916 | -0.002384 | 756h11.C, 504h.F2, 504h.F2 | 8.362e-05 |
| 598 | 24.906541 | 24.908189 | 24.905021 | -0.001520 | 549h11e.C, 756h09.F2, 503h.F2 | 6.216e-05 |
| 651 | 25.945322 | 25.946477 | 25.944465 | -0.000857 | 651h.C, 703h.F1, 552h.F2 | 3.357e-05 |
| 921 | 30.821404 | 30.821673 | 30.820446 | -0.000958 | 921h.C, 803h.F1, 983h.F1 | 3.156e-05 |
| 875 | 29.988866 | 29.989088 | 29.988197 | -0.000668 | 875h.C, 998h.F1, 998h10.F1 | 2.260e-05 |
| 756 | 27.922108 | 27.922179 | 27.921545 | -0.000563 | 756h.C, 503h.F2, 755h.F2 | 2.047e-05 |
| 975 | 31.721540 | 31.723688 | 31.721000 | -0.000540 | 912h.C, 740h.F1, 740h.F1 | 1.729e-05 |
| 507 | 22.965211 | 22.967701 | 22.964856 | -0.000355 | 462h10.C, 602h10.F1, 462h10.F2 | 1.577e-05 |
| 996 | 31.955474 | 31.955861 | 31.955219 | -0.000256 | 996h.C, 504h.F2, 758h.F1 | 8.097e-06 |
| 811 | 28.916539 | 28.916575 | 28.916323 | -0.000215 | 811h.C, 811h.F1, 503h.F2 | 7.566e-06 |
| 378 | 19.922519 | 19.922807 | 19.922375 | -0.000145 | 378h.C, 304h.F1, 378h.F2 | 7.434e-06 |
| 995 | 31.951393 | 31.952594 | 31.951285 | -0.000108 | 995h.C, 995h.F1, 504h.F2 | 3.425e-06 |
| 912 | 30.703260 | 30.703419 | 30.703186 | -0.000074 | 912h.C, 740h.F1, 740h.F1 | 2.452e-06 |
| 504 | 22.915136 | 22.915279 | 22.915094 | -0.000042 | 504h.C, 504h.F1, 503h.F2 | 1.880e-06 |
| 862 | 29.836564 | 29.836907 | 29.836559 | -0.000005 | 862h09c.C, 862h.F1, 984h.F1 | 1.615e-07 |
| 816 | 28.978163 | 28.978742 | 28.978163 | -0.000000 | 816h.C, 704h.F1, 704h.F1 | 1.023e-08 |
| 757 | 27.931788 | 27.932500 | 27.931788 | -0.000000 | 757h.C, 504h.F2, 504h.F2 | 2.105e-09 |
| 599 | 24.923743 | 24.926730 | 24.923742 | -0.000000 | 599h.C, 378h.F2, 993h.F2 | 1.306e-09 |

### Built against predicted

- 72 of the 74 builds end below their prediction. The median is 0.0006 below, and the largest is 0.0086 below.
- No build ends more than 0.003 above its prediction. The two that end above are 873 (+0.0025) and 814 (+0.0012).
- 25 builds end more than 1e-6 below held, 23 end more than 1e-6 above, and 26 return to the held side.

The builds go below the prediction because the squeeze moves the rest. The tables keep the rest on the grid. The squeeze lets its rows and columns slide, which is the room that control 1 misses.

The largest gains put a known corner at another n. The corner of 740 (loss 2.50, the lowest of two 8-arms) gives 797 and 974. n=797 = (28, 13) is the next n on the line of 740 = (27, 11). The corner of 505 gives 601, 652 and 705.

### The two predictions that failed

n=934 has no legal start within 0.003 of its prediction, and n=873 and n=814 end above theirs. All three use the corner `934h.C`. We measured the cause on 934.

- The far zones are as the tables say. Their exact lengths at the predicted f are 5.18346 and 4.14208, against 5.18472 and 4.14402 in the tables.
- The corner does not reach the pair of lengths that its table promises. The table joins five LP solutions with straight lines. At f = 0.9672 the corner gives up 0.0135 of `y0` for 0.047 of `x0`, and the straight line says 0.020.
- The choice fits between f = 0.9642 and 0.9672. The held f is 0.964143, so n=934 has no gain from this choice.

The repair is a corner table made with caps: for each cap on `y0`, the smallest `x0`. `corner_at` already does this for one f.

### Licences

`take.tsv` names the source and the licence of the three modules of every row. Three kept rows (875, 912 and 975, 4.2e-5 of the gain) use a module of a held layout whose source has the licence "Other (specified in description)". Every other module is from the held seed file, from our own search, or from a source with Apache 2.0 or CC BY 4.0.

## 8. What to run next

1. Build every prediction, with three choices each and a start up to 0.003 above held. We built 74 of the 378 n. One choice takes 1 to 3 minutes on one core. The first ones are the 22 n with a prediction up to 0.0045 above held that we did not build. They are 304, 339, 460, 754, 685, 550, 860, 918, 998, 602, 459, 935, 542, 852, 863, 804, 461, 857, 983, 861, 703 and 747.
2. Cut the 28 new layouts into the library and run the generator again. Each one is a new corner or a new pair of far zones for the n on its line, `(m + 1, k + 2)` and `(m - 1, k - 2)`.
3. Make the sliding of the rest a part of the module: one offset for each row and column of the rest beside a zone. Control 1 must then pass on the 14 layouts that fail with flush arms, and the predictions get closer than 0.003.
4. Tabulate the corner with caps, as in section 7. It removes the error found on 934.
5. Search for the zones of section 6 one zone at a time. A far zone is 16 to 61 squares in a strip of width `c - 1 + f`, with one flush stack as a moving wall. The target is the shortest zone for each count. The count classes say which counts to search first.

## Round 2 (2026-11-11, round 11)

**Result: 11 n certify below the held file of round 10 and below every other take of rounds 10 and 11, for a gain of 0.0006337 against held. The gain over the other takes is 0.0002780, and 7 of the 11 n carry almost all of it. The others are a layout of another take again, lower by less than 1e-7. Nothing was submitted from here. The take is in `<scratch>/bounties-squares/take-modules-r11`. Control 1 passes on 158 of 172 layouts (110 of the 122 of round 1, where it was 97), so it is still red. The largest gain is n=459 (0.0002333). It is a choice of the round 1 library that round 1 did not build. The growth of the library gives small gains, because the new layouts hold the same designs again, one or two steps along their lines.**

Words used here: "held" is now `gather/round10-2026-11-11a.csv` (22.1892638148, gate dir `gate/cand-round10-1111a`). "The bar" of an n is the smallest of its held side and its side in the other takes: `take-modules-r10`, `take-family-r10`, `take-family-r11`, `take-soft-r11`, `take-border-r11` and `take-zones-r11`. A build is kept only when it certifies below the bar by more than 1e-10 of score. Round 10 held the family wins and not the modules wins of round 1, so for 28 n the bar is the modules take of round 1.

### R1. What was wrong in round 1, and what changed

We checked round 1 again. Its take stands (28 n, 0.0013925). Four statements of this doc were wrong or not proven, and sections 2 to 6 above are corrected:

- The LP length of a far zone at its own f is above the found length, not below (198 of 242 zones).
- The length sums are exact by definition only. The stacks of a run have gaps that no zone counts.
- A predicted side is not an upper bound by construction. The tables and the build took different steps in f.
- The cause given for the 814 to 873 miss is not proven. The tables grow above the f a zone was found at.

Two things changed in the tool for it.

1. **One path.** `far_at` and `corner_at` now walk the knots of the table (`path`), then one last step to the f of the build. For `756h11.F2` at f = 0.9489 the table says 4.15220 and the build gets 4.15194. In round 1 the two were 0.04 apart. Between two knots the table is a straight line and the build is one LP step, so they still differ. The difference is 0.005 on `814h.F1` at f = 0.957. It is 0.021 on `756h11.F2` at f = 0.9617, where the build is shorter.
2. **Leave one out** is now a command (`modules.py loo`). It takes every module of a held layout's n away and predicts that layout from the modules of other n. It is the standing control of the generator.

| library | layouts with a prediction | within 1e-3 | within 2e-3 | within 5e-3 | median | quartiles | held f below 0.8 |
|---|---|---|---|---|---|---|---|
| round 1 (366 modules) | 70 of 71 | 10 | 23 | 47 | +0.0030 | +0.0015, +0.0057 | 8 layouts, +0.0107 |
| grown, no twins (516 modules) | 71 of 71 | 18 | 33 | 54 | +0.0020 | +0.0004, +0.0042 | 8 layouts, +0.0076 |
| grown, with the slid twins of R4 (630 modules) | 71 of 71 | 18 | 33 | 55 | +0.0020 | +0.0002, +0.0041 | 8 layouts, +0.0076 |

The grown library moves this number, because a family step puts the design of one n at its neighbours on the line. The slid twins do not move it. So the tables still carry a module about 0.002 of f too high in the median. A prediction within 0.005 of held still reads as equal to held.

Not changed: how a far zone is carried above the f it was found at. The loose squares of a zone keep their angle in the continuation, and the tables grow where found zones shrink.

### R2. The passes

Each pass cuts new layouts into the library, makes the tables of the new modules, lists the choices that hold a new module (`modules.py queue --need`), builds them, and certifies. A choice is built when its prediction is up to 0.003 of side above the bar. The limit is 0.0045 for the 22 n of round 1, 0.005 for a corner from another n, and 0.004 in passes 3 and 4. The lists hold the best three choices of an n in pass 1 and pass 4, and the best two in passes 2 and 3. The builds ran on three processes until the time of the round ended, best prediction first, so a list is not built to its end.

| pass | list | layouts cut | modules added | choices listed | n predicted below held | n predicted below the bar | choices built | no start | n built | n certified below the bar | gain against held | gain over the other takes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | choices with a new module | 50 | 150 | 268 on 90 n | 22 | 7 | 32 | 3 | 29 | 4 | 0.0002489 | 0.0000152 |
| 1 | the 22 n of round 1 not built | 0 | 0 | 64 on 22 n | 1 | 1 | 41 | 0 | 19 | 1 | 0.0002333 | 0.0002333 |
| 2 | corner from another n | 0 | 0 | 206 on 103 n | 16 | 4 | 20 | 0 | 19 | 3 | 0.0000779 | 0.0000217 |
| 2 | slid twins | 0 | 114 | 92 on 46 n | 6 | 2 | 0 | 0 | 0 | 0 | 0.0000000 | 0.0000000 |
| 3 | choices with a module of a pass 1 or 2 win or of a new take layout | 11 | 35 | 168 on 84 n | 23 | 9 | 15 | 0 | 14 | 1 | 0.0000199 | 0.0000004 |
| 4 | choices with a module of the 924 win or of the zones take | 2 | 8 | 193 on 68 n | 4 | 4 | 17 | 0 | 7 | 2 | 0.0000536 | 0.0000074 |
| all | | 63 | 307 | 991 | | | 125 | 3 | 54 | 11 | 0.0006337 | 0.0002780 |

- **Pass 1** cut 50 layouts: 17 of the round 10 file (56 others were in the library already), 21 of `take-modules-r10`, 7 of `take-family-r10` and 5 of `take-family-r11`. The 5 border wins of round 10 (542, 799, 811, 971, 986) are in the round 10 file. Their layouts are not two flush arms after the border, or were held already, so they add no module.
- **Pass 1, the 22 n of round 1.** Their best choices are 0.0000 to 0.0052 above held, and most are the layout's own modules. 41 choices on 19 of the 22 n are built (304, 339, 459, 460, 461, 602, 685, 703, 747, 754, 804, 852, 860, 861, 863, 918, 935, 983, 998). One n ends below held by more than 1e-7 of side, and it certifies below the bar: 459. The list holds no new choice for the other 3 n (542, 550, 857). Built minus held for the best choice of each n: 304 +0.0013936, 339 +0.0015840, 459 -0.0049978, 460 +0.0012887, 461 -0.0000000, 602 +0.0035810, 685 +0.0028382, 703 -0.0000000, 747 +0.0005309, 754 +0.0023033, 804 +0.0000222, 852 -0.0000000, 860 +0.0032074, 861 +0.0000025, 863 +0.0000697, 918 +0.0022842, 935 +0.0004959, 983 +0.0000002, 998 +0.0003950.
- **Pass 2** added the 114 slid twins of R4 and listed, for every n, the choices whose corner comes from another n. In round 1, 0.00114 of the 0.00139 came from such corners.
- **Pass 3** cut the wins of passes 1 and 2 (6 layouts) and what `take-family-r11` and `take-soft-r11` held by 23:17 UTC (3 and 2 layouts).
- **Pass 4** cut one more win of pass 2 (924, certified after pass 3 was listed) and the one layout of `take-zones-r11` (995). By 23:28 UTC the takes held 17 more new layouts (11 of `take-family-r11`, 4 of `take-border-r11`, 2 of `take-soft-r11`). None of them has two flush arms, so the cut refuses them and they add no module.
- A pass ends when its list is built or the time is over. Every pass added certified n, so the loop did not end by itself. The time of the round ended it. Pass 4 built 17 of its 152 listed choices and certified 2 n.

The kept n:

| n | pass | held side | bar | built side | modules (corner, far 1, far 2) | gain against held | gain over the other takes |
|---|---|---|---|---|---|---|---|
| 459 | 1 | 21.901803002 | 21.901803002 | 21.896805201 | `551h.C`, `756h09.F2`, `338h.F1` | 2.333e-04 | 2.333e-04 |
| 551 | 2 | 23.926436941 | 23.925563222 | 23.925055162 | `600f11.C`, `504h.F2`, `600r10.F2` | 5.887e-05 | 2.164e-05 |
| 651 | 1 | 25.941684354 | 25.941684354 | 25.941426494 | `651r10.C`, `504h.F2`, `651r10.F2` | 1.011e-05 | 1.011e-05 |
| 740 | 1 | 27.706993808 | 27.706455207 | 27.706455021 | `740m10.C`, `740m10.F1`, `685h09.F1` | 1.981e-05 | 6.787e-09 |
| 862 | 1 | 29.833382720 | 29.833382720 | 29.833233099 | `862r10.C`, `862r10.F1`, `803h.F1` | 5.096e-06 | 5.096e-06 |
| 863 | 3 | 29.844287857 | 29.843714232 | 29.843702671 | `863f10.C`, `863q1.F2`, `987f10.F1` | 1.992e-05 | 3.935e-07 |
| 911 | 1 | 30.695622172 | 30.689167231 | 30.689167171 | `911m10.C`, `852h.F2`, `495h11.F1` | 2.139e-04 | 1.936e-09 |
| 924 | 2 | 30.855301048 | 30.855298161 | 30.855297803 | `863h.C`, `863h.F1`, `863h.F1` | 1.067e-07 | 1.176e-08 |
| 987 | 4 | 31.865779434 | 31.865746184 | 31.865719577 | `924h.C`, `923h.F1`, `924q1.F1` | 1.905e-06 | 8.469e-07 |
| 995 | 4 | 31.951392555 | 31.949968447 | 31.949761486 | `995z11.C`, `504h.F2`, `995z11.F2` | 5.171e-05 | 6.561e-06 |
| 997 | 2 | 31.973616782 | 31.973018057 | 31.973017756 | `934h.C~`, `874h.F1`, `997m10.F1` | 1.897e-05 | 9.485e-09 |

Licences: the row of n=459 uses the corner `551h.C`. It is cut from a held layout whose source has the licence "Other (specified in description)". That row is 2.333e-04 of the gain. Every other module of the take is from the held seed file, from our own search, or from a source with Apache 2.0 or CC BY 4.0.

n=459 is also the one large gain. Its corner comes from n=551 and its far zones from n=756 and n=338. The prediction was 0.0042 above held and the build ends 0.0050 below held, so the tables were 0.009 too high here.

Why the other gains are small. A layout cut from a family win is the design of its donor, one or two steps along the line `(m + 1, k + 2)`. Its modules are the donor's modules at another f. So the generator returns the bar again. Of the 125 builds, 46 end within 1e-6 of side of the bar, 11 end more than 1e-6 below it and 68 above. The built side is -0.0002 against its prediction in the median. n=873 shows it: 7 choices predicted at 29.9551 all end at 29.957806, which is +0.000645 against held.

[`results/modules-r11-2026-11-11.tsv`](../results/modules-r11-2026-11-11.tsv) has one row for each choice built: the modules, the predicted side, the built side, the held side, the bar and the certified gain.

### R3. The squeeze: `family_step.squeeze` against `methods_lp.slp` and the fq quench

Both squeezes ran from the same start layout on 7 builds (`modules.py job --squeeze both`).

| n | slp, then fq | seconds | family_step.squeeze | seconds | difference |
|---|---|---|---|---|---|
| 601 | 24.953958324 | 15 | 24.953958324 | 18 | -5.7e-14 |
| 760 | 27.984419738 | 35 | 27.984419738 | 36 | +3.2e-13 |
| 814 | 28.945633767 | 63 | 28.945633767 | 44 | +2.7e-13 |
| 852 | 29.699596303 | 79 | 29.699596303 | 10 | -7.2e-12 |
| 863 | 29.843702974 | 43 | 29.843702973 | 71 | -1.1e-09 |
| 873 | 29.957805968 | 105 | 29.957805968 | 81 | -2.8e-14 |
| 987 | 31.865746183 | 98 | 31.865746183 | 23 | +1.0e-12 |

The two end at the same side to 1e-9 on every build. The squeeze of `family_step.py` does not end lower. Its time is 282 s against 439 s in total, on a box whose load changed during the runs. We keep `methods_lp.slp` and then fq as the default, because nothing is gained by the change.

### R4. The slide of the rest beside a zone

Round 1 found that the rest is not a rigid grid and did not find the rule. The rule, measured on the layouts that failed control 1:

- A square of a zone pokes past the grid edge of its strip, by 0.012 to 0.087. It enters a gap between two cells of row 0 or of column 0 of the rest. Row 0 is the cells that stand on the bottom strip, and column 0 is the cells on the left strip.
- The gap is there because every cell of the row between the corner and the poke stands the same distance g towards the corner. The room for g is at the head of the row, where the corner leaves it.
- The gap is wider than the poke is deep. A corner of a square tilted by t that enters by d needs d (tan t + cot t) of gap. For t = 18 degrees that is 3.4 d.

| n | f | which zone pokes | depth | slide g of row 0 | slide g of column 0 |
|---|---|---|---|---|---|
| 506 | 0.9521 | far 2 | 0.044 | 0.151 (cells 1 to 13) | none |
| 553 | 0.9615 | far 2 and far 1 | 0.038 and 0.021 | 0.136 | 0.070 |
| 652 | 0.9654 | far 2 | 0.035 | 0.118 (cells 0 to 15) | none |
| 875 | 0.9889 | far 2 and far 1 | 0.028 and 0.028 | 0.088 (cells 0 to 19) | 0.089 (cells 0 to 19) |
| 935 | 0.9799 | the corner | 0.012 | 0.041 (cells 0 to 2) | none |

So a far zone that pokes needs a slide g, and the corner of the same layout grants it. A row couples the corner and the far zone at its other end, as round 1 saw on 814. Rows other than row 0 and columns other than column 0 slide too, by up to 0.09, but nothing pokes into them: those cells are loose.

What the module holds now (`slide_fields`, `slid`):

- A far zone that pokes has a slid twin (id with `~`). The twin holds the found places of the cells of row 0 beside it and its need g. The module itself stays: its table is made with the rest on the grid, so its poke is pushed back, it is longer, and it fits every corner.
- A corner has a twin when it pokes or when a far zone of its layout pokes. The twin holds the found places of the cells at its end of row 0 and column 0, and what it grants. The two cells at the head of a row also keep their sideways offset. In n=652 cell (0, 0) stands 0.118 to the left and 0.0185 down. Without the second number it hits a square of the corner.
- `assemble` puts row 0 and column 0 of the rest at these places. From the corner outwards they are the corner's found places, then the grant all along the run, then the found places of the far zone. It refuses a choice in which a cell would stand further towards the corner than the cell before it.
- The library has 46 far twins and 68 corner twins from 172 layouts (after pass 4: 47 and 71).

Measured on `652h.F2` at its own f: found length 4.2695, table with the rest on the grid 4.3187, table of the twin 4.2715. The slide gives back 0.047 of length, which is about 0.01 of f.

**Control 1 with the twins** (`modules.py rebuild`, every layout from its own modules at its own f plus the smallest step that is legal):

| step above the layout's own f | 122 layouts of round 1, round 1 | the same 122 now | all 172 layouts now |
|---|---|---|---|
| 0 | 37 | 49 | 74 |
| 1e-4 | 28 | 22 | 32 |
| 3e-4 | 20 | 23 | 32 |
| 1e-3 | 12 | 16 | 20 |
| 3e-3 | 7 | 2 | 4 |
| not within 3e-3 | 18 | 10 | 10 |
| within 1e-3 | 97 | 110 | 158 |

- Of the 14 layouts with flush arms that failed in round 1, 9 pass now. They are the held 506, 652, 875, 935 and 998, the public 651 and 652 of 2026-11-09, and the public 705 and 998 of 2026-11-10. 5 still fail: 340, 553, 591, 936 and 552.
- Of the 11 with an arm that is not flush, 6 pass now.
- Two layouts that passed in round 1 fail with their twins: 702 and 984. Their rows slide by 0.003 to 0.017 with a different amount for every cell, which the model of one g does not hold. From their modules with the rest on the grid they pass (+0.0003 and +0.0001), and the generator has both.
- Control 1 does not pass on every layout. It is red.

The twins repair the model. Their gain so far is small. 8 choices with a twin were built, and 3 of them ended more than 1e-7 below the bar. 1 kept n uses a twin (997, gain over the other takes 9.5e-09). 0 of the 75 choices of the twin list itself were built in the time.

### R5. The corner under two caps

The build asks a corner for a state with `y0` under one cap and `x0` under another. In round 1 `corner_at` went to the state of the smallest sum and asked one LP for both caps. The states of a corner are not a convex set, so that LP can fail where a state exists. The own corner of n=875 did not come back. Its found state is 10.0187 and 11.0674, and its state of the smallest sum is 10.0015 and 11.0815.

`corner_at` now goes to the state with the smallest `y0`. If that `y0` is above its cap, no state fits. From there a chain of LPs lowers `x0` and keeps `y0` under its cap, so every step starts from a legal state. Then it tries the other order, then the old way. n=875 comes back at its own f.

The table of the generator still joins five LP states by straight lines, so the error of n=934 is still in the predictions. 16 built choices have a corner of n=934 and a prediction below the bar. 3 had no start, 9 ended above the bar, 1 ended within 1e-7 of it and 3 ended below. For the choices with no start the exact chain agrees with round 1: the corner of 934 has no state under those caps. A table made with caps (for each cap on `y0` the smallest `x0`, the same chain on a grid of caps) is not built.

### R6. What the grown library still lacks

Lowest sum of the three losses as found, by class `(k - 2m - 1) mod c`, after the growth. A value in bold is new or lower than in section 3.

| arms | band of f | classes with a layout (loss) | classes with none |
|---|---|---|---|
| 8 and 8 | below 0.78 | 0 (**9.13**), 1 (**8.00**), 3 (**8.98**), 4 (**7.85**), 6 (**8.14**), 7 (8.41) | 2, 5 |
| 8 and 8 | 0.78 to 0.90 | 1 (9.56), 5 (8.90), 7 (9.43) | 0, 2, 3, 4, 6 |
| 8 and 8 | 0.90 and more | 1 (10.64), 2 (9.95), 3 (9.34), 4 (8.72), 5 (8.69) | 0, 6, 7 |
| 7 and 7 | below 0.78 | none | all |
| 7 and 7 | 0.78 to 0.90 | 4 (**7.33**), 5 (**7.06**) | 0, 1, 2, 3, 6 |
| 7 and 7 | 0.90 and more | 0 (**7.84**), 1 (**7.66**), 2 (**7.95**), 3 (8.20), 4 (8.48) | 5, 6 |
| 6 and 6 | below 0.78 | none | all |
| 6 and 6 | 0.78 to 0.90 | 1 (5.12) | 0, 2, 3, 4, 5 |
| 6 and 6 | 0.90 and more | 0 (5.89), 1 (5.51), 2 (5.58), 3 (6.12), 4 (5.31), 5 (5.81) | none |

- One class is new: two 7-arms at f of 0.90 and more, class 0, at 7.84. Every other cell moved by 0.08 squares at most. All of it came in pass 1. Passes 2, 3 and 4 changed no cell.
- Two 8-arms at f of 0.90 and more still have no layout for classes 0, 6 and 7. Classes 1 and 2 still cost 10.64 and 9.95 against 8.69 to 8.72. The 8-arm far zones there still hold 5 mod 8 squares.
- Between f 0.78 and 0.90, two 8-arms are still served for three classes as found, and two 7-arms for two.
- Below f 0.78 there is still no corner of two 7-arms or two 6-arms. The four corners of two 8-arms (f 0.687 to 0.707) are now six, all cut from the same design (n=740 and its steps 797, 911, 974).
- A choice whose corner comes from another n exists within 0.005 of the bar for 103 of the 413 n, and below the bar for 4.

So the growth does not open a class or a band. New zones have to come from a search, as section 6 says. R4 gives that search one new fact. A far zone can be 0.05 shorter when it pokes into row 0, if the corner leaves 0.09 to 0.15 of room at the head of that row. A zone search should give the far zone that freedom and charge the corner for the room.

### R7. What to run next

1. Give a corner a grant that it was not found with. Push row 0 by g at the head, let the LP move the corner, and tabulate the cost in `y0` and `x0` for g of 0.03 to 0.15. Then the 46 far zones that poke fit 172 corners. Today they fit 68.
2. Carry a far zone above its found f with the loose squares free to turn, and test it on leave one out. Today 68 of 232 tables grow there.
3. Tabulate the corner with caps (R5), so that the 934 kind of prediction goes away.
4. The 5 flush layouts that still fail control 1 (340, 553, 591, 936, 552), and a slide that differs from cell to cell (702, 984).
5. Build the lists to their end. 128 of the 991 listed choices are built, on 54 of the 114 n that have a listed choice. 9 n have a choice predicted below the bar, and each of them has at least one build. The lists are `work/q*.tsv` and `work/jobs-*.list` in the take dir.

## Round 3 (2026-11-12, round 12)

**Result: 5 n certify below held and below every other take of this round: 599, 755, 757, 862 and 923, for 0.0002864 against held and 0.0000122 over the other takes. Nothing was submitted from here. 208 choices were built on 76 n. The other takes already held most of the large builds of this round, at the same side. The corner tables now hold only the states a corner was found in, so a prediction is an upper bound of its build again. Corners with a grant fit every far zone that pokes, but no granted choice is predicted below held, and none of the 9 built had a start.**

Words used here: "held" is now `gather/round11-2026-11-11b.csv` (22.1846685445, gate dir `gate/cand-round11-1111b`). "The bar" of an n is the smallest of its held side and its side in the other takes of this round: `take-family-r11`, `take-family-r12`, `take-readers-r12`, `take-soft-r11`, `take-soft-r12`, `take-border-r12`, `take-zones-r11`, `take-zones-lowf-r11`, `take-zones-corner-r11` and `take-polish-r11`. A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r12`.

### S1. A corner holds the states it was found in, and nothing between them

The table of a corner holds five LP states for each f, one for each cost of `COST`. Until this round the generator also put two points on the straight line between two neighbouring states, so 13 points in all. The states of a corner are not a convex set (R5), so a point on that line is not a state. We checked the predictions of the 934 kind (predicted below held, then built above held or with no start). Each one fits only at such a point:

| choice | stacks | f with 13 points | f with the 5 states |
|---|---|---|---|
| 934: `934r10.C`, `652m10.F1`, `873f11.F1` | 16, 14 | 0.96103 | 0.97083 |
| 873: `934r10.C`, `996m10.F2`, `873f11.F2` | 15, 13 | 0.95510 | 0.96088 |
| 814: `873r10.C`, `504h.F2`, `551h.F1` | 11, 11 | 0.94397 | 0.95551 |
| 873: `zc8x8-115f9830a.C` (a zone lane corner), `504h.F2`, `814h09.F1` | 12, 12 | 0.95496 | 0.98073 |

So the generator now uses the 5 states only (`CHORD = False`; `--chord` on the command line gives the old table). We compared the two tables on every choice built in rounds 11 and 12 (189 records, `work/chordcheck.tsv`, `tools/chordcheck.py`):

| table | built above the prediction by more than 1e-4 | by more than 1e-3 | predicted below held | of those, built below held | no start, predicted below held |
|---|---|---|---|---|---|
| 13 points (rounds 10 and 11) | 30 of 184 | 22 | 63 | 42 | 5 of 5 |
| 5 states (this round) | 3 of 184 | 0 | 39 | 38 | 0 of 5 |

With the 5 states a prediction is an upper bound of the build again, to 1e-3, and a choice predicted below held ends below held in 38 of 39 cases. No gain is lost: every build that ended below held by more than 1e-6 was predicted within 0.0042 of held by both tables. This is the cheap half of "tabulate the corner with caps". The other half is not built: a table of the true trade curve (for a grid of caps on `y0`, the smallest `x0`, by the chain of `corner_at`). It would add states between the 5 and win back choices that the line found by luck (3 builds of 997 ended below held with a 5-state prediction 0.0014 above held).

### S2. A corner with a grant it was not found with

A far zone that pokes into row 0 (column 0) of the rest needs every cell of that row to stand g towards the corner (R4). Until this round only the slid twin of its own layout's corner granted that. `modules.py grant` now gives every plain corner the grants that the poking far zones of its stack sizes need, at g = 0.04, 0.10 and 0.16. The row (the column) is pushed by g at the head, as `corner_slide` does, and the corner is solved again at its own f for the 5 costs. The variant's table is the corner's table plus that cost in `y0` and `x0`, all along f. The build solves the variant exactly (`corner_at` with the same slide). A variant is named `<corner>^<arm>g<g x 100>`.

| arm | g | variants | no state at the smallest sum | cost in `y0` + `x0` at the smallest sum, median | quartiles | zero (below 1e-4) |
|---|---|---|---|---|---|---|
| 1 (column 0) | 0.04 | 629 | 52 | +0.012 | +0.000, +0.066 | 194 |
| 1 (column 0) | 0.10 | 256 | 48 | +0.073 | +0.027, +0.163 | 29 |
| 1 (column 0) | 0.16 | 601 | 175 | +0.274 | +0.087, +0.366 | 38 |
| 2 (row 0) | 0.04 | 617 | 59 | +0.010 | +0.000, +0.045 | 174 |
| 2 (row 0) | 0.10 | 281 | 57 | +0.058 | +0.012, +0.156 | 32 |
| 2 (row 0) | 0.16 | 588 | 209 | +0.258 | +0.071, +0.355 | 28 |

2,972 variants of 656 corners (`work/grant/all.pkl`, merged into `work/libg`). A grant of 0.04 costs about 0.01 of length in the median and nothing for a quarter of the corners. That is less than the 0.05 a far zone gains when it pokes (R4), and 24 of the 46 poking far zones need 0.04 or less. A grant of 0.16 costs about 0.26, more than it can give back. Before, the 46 poking far zones fitted 295 places (a corner and an arm) of the 669 corners; now they fit 23,298 places of 3,041 corners and variants, and every poking zone fits at least one.

Two faults were found and fixed on the way.

- For a grant on column 0 the head cell (0, 0) stayed in place while the rest of the column slid into it. Fixed bodies are not tested against each other in the LP, so these variants cost nothing and were illegal. The head cell now takes both slides (`corner_slide`). All variants were made again after the fix.
- The LP state of a corner at one cost can move along the trade when the cells move, so the measured cost of a grant was negative in one length for 1,050 of the 2,972 variants (as far as -0.66). Added to the table as it was, it made a variant shorter than its corner. The first generator run with those tables put 13 choices of 7 n below held (305, 342, 378 and 381 with `zc6x6-84f9465b.C^2g04` or `^1g16`, and the corner `zc8x8-138f9552c.C^2g16` 0.01 to 0.025 below held on 421 to 556). The 7 choices with a granted corner that were built all had no start. Now each length of the cost counts only when it is positive, so a variant is never shorter than its corner in either length. The generator ran again on these tables.

9 choices with a granted corner were built, and none had a start:

- The 7 of the first run (305, 342, 378, 381) came from the tables before the clamp. Each failed with "the corner does not fit under both arms": the table promised room that the corner does not have.
- The 2 of the second run (758 and 996, both predicted 3e-4 of side above held) failed the check that no cell of row 0 (column 0) stands nearer the corner than the cell before it. For 996 the cause is that the copies of `modules.py` in the build dirs on both boxes were made before the head-cell fix above. With the fixed code its layout puts together. 758 shows a second fault, not fixed: its corner is a twin slid on row 0 (`758h.C~`), and its grant is on column 0. The head cell (0, 0) takes the found place of the row, not the grant of the column, so the column steps back at its head. 146 of the 2,972 variants are of this kind (93 on column 0 of a corner slid on row 0, 53 the other way). Their costs were measured on the same faulty head cell.

### S3. The zones of the zone lanes

The zone lanes keep their zones in library dirs with tables (`take-zones-r11/work/newlib4`, `newlib4a`; `take-zones-lowf-r11/work/lib1`, `lib2`, `lib2a`, `lib3`; `take-zones-corner-r11/work/lib1`, `lib-r8`, `lib-t3`, `lib-own`, `lib-rall`). `work/tools/union.py` adds every zone with a table to the library, a later dir winning for the same id. At 01:31 UTC the dirs held 922 zones with a table: 503 far zones (stacks of 6 to 11) and 419 corners of 19 pairs of stack sizes. `lib-low` (01:48 UTC) added 50 corners: 972 in all, and the library grew from 673 to 1,645 modules (`work/libz3`). The generator ran on the 922 with the grants, and on all 972 with the 50 counted as new (S4).

The 1,428 zone files in `take-zones-r11/work/zones` have no table outside those dirs, so most of them are not in the library. Tabulating them is CPU work for a later round.

### S4. The generator over every n

Two changes make a run over every n affordable. Both give the same rows as before on the n we compared.

- A search window (`queue --depth D`): only f from D below held up to the slack is searched. Same rows on 5 n (601, 760, 873, 934, 997) with 1,340 modules.
- The fit of all choices of one corner at once (`Library.fit_many`), and the family of a module computed once. Same rows on the same 5 n, and on 873 the run went from 48 s to 16 s. The run over the 413 n with the zones and the grants below took 16 minutes on two processes (boxA at a load of about 25).

The run with every zone and every grant variant counted as new (`--need`, 922 zones and 2,972 variants, the 5 states, window 0.05, slack 0.002) gave 234 rows on 79 n (`work/qz/qz2a.tsv`, `qz2b.tsv`). The other n have no choice with a new module inside the window.

- 11 n have a choice predicted below held: 601, 634, 649, 803, 862, 863, 871, 921, 923, 932 and 995. 60 n have one within 1e-3 of held.
- A granted corner is in 27 rows and is the best choice of 9 n, none below held (924 +6e-5, 986 +9e-5, 873 +1e-4, 758 +3e-4 of side). So the grants open choices, but at their measured cost they do not beat held.
- Below f = 0.80, 13 n have a row and one is below held: 634, with the corner of 852 (7x8), the zone lane's far zone `z7-16f700.F1` and `740h.F1`, predicted 0.0035 of side below held.

The run with the 50 corners of `lib-low` counted as new (`work/libz3`, all 413 n, `work/qz/qz4.tsv`) gave 30 rows on 10 n. One n is below held: 924, by 5.1e-5 of side, with `zc7x7-60f8443a.C`. The zone lane built 924 with that corner already (`take-zones-corner-r11`, 3.8e-4 of side below held), so it is not below the bar. Below f = 0.80 it has rows on 740, 911 and 974, the best 2.7e-4 of side above held.

### S5. The lists

The lists of round 11 (`take-modules-r11/work/q*.tsv`, `jobs-*.list`) had 864 choices not built. 70 were built in the first 20 minutes, chord ranking first. Then the rest was ranked by the 5-state prediction (`tools/rerank.py`), two choices of an n at a time, and only choices predicted within 0.01 of held were kept (694 choices on 109 n). No choice of these lists is predicted below held with the 5 states, and 216 are within 1e-3.

208 choices were built (14 with no start) on 76 n. 34 builds on 17 n certify below held by more than 1e-10 of score, and 7 builds on 5 n are below the bar. The take keeps 5 n.

| list | built | on n | no start | below held | kept |
|---|---|---|---|---|---|
| round 11 lists, chord order (first 20 minutes) | 69 | 25 | 2 | 5 on 4 n | 1 (755) |
| round 11 lists, 5-state order | 71 | 60 | 3 | 7 on 6 n | 1 (757) |
| the generator with the zones and the grants (S4) | 68 | 37 | 9 | 22 on 12 n | 3 (599, 862, 923) |

| n | build | corner, far zones | built - held (side) | gain (score) | over the other takes |
|---|---|---|---|---|---|
| 599 | `599-Qc023` | `zc8x6-79f9323a.C`, `702h.F1`, `378h.F2` | -0.000549 | 2.244e-05 | 3.850e-06 |
| 755 | `755-L018` | `755h.C`, `995z11.F2`, `811m10.F1` | -0.000215 | 7.842e-06 | 7.842e-06 |
| 757 | `757-L261` | `757h.C`, `599r10.F1`, `504h.F2` | -7e-09 | 2.096e-10 | 2.096e-10 |
| 862 | `862-Qd002` | `zc7x7-73f8554a.C`, `862q1.F2`, `862r10.F1` | -0.003339 | 1.137e-04 | 1.945e-07 |
| 923 | `923-Qe000` | `zc7x7-73f8554a.C`, `863h.F1`, `z7-32f860.F1` | -0.004326 | 1.424e-04 | 3.465e-07 |

The other takes held the large builds of this round already. 634 (-0.0035 of side), 803 (-0.0027), 871 (-0.0019) and 863 (-1.8e-5) end at the side of another take to 1e-9. 932 (-0.0015) and 983 (-0.00014) end 1.5e-7 and 1e-9 of side above the bar. 598, 649 and 995 end below held and above the bar of the family and soft takes. Most of the other builds below held rebuild the held layout to 1e-9. The source of 599 names two public notebooks, and one of them has "Other" terms. `take.tsv` names both in its source and licence columns.

### S6. Low side fractions

We counted the held layouts of n 300 and more by side fraction f and by what the cut does with them (`work/tools/lowf.py`, `work/tools/loosecut.py`):

| f | layouts | cut | no two arms of stacks of 5 and more on two walls, even with a flush error of 0.05 | two such arms, refused |
|---|---|---|---|---|
| below 0.80 | 216 | 10 | 192 | 14 |
| 0.80 and more | 197 | 63 | 133 (flush error 3e-3) | 1 |

So the gap at low f is not in layouts that the cut refuses for a detail. 192 of the 216 layouts there have no two arms on walls at all. Two of the main session's examples show why:

- n=855 (f = 0.734): no stack of 5 or more stands against a wall within a flush error of 0.05. Its 8-stacks stand at x = 4.85, one column off the left wall, at 22.7 degrees with a flush error of 0.032. Its 11-stacks on the bottom are broken into chains of 10 and fewer by the stack reader.
- n=845 (f = 0.563): a band of 3-stacks. No stack is long enough to be an arm.

These are other designs. A module for them needs arms that stand off the wall and bands of short stacks, which the model of this lane (two flush arms on two walls, a corner, two far zones and the rest as one grid) does not have.

For the 14 with two arms that are refused, the cut now tries a looser flush tolerance (0.01) when the strict one (3e-3) refuses a layout (`cut(sq, n)`, `LOOSE_TOL`). The control: all 73 held layouts that cut today cut to the same arms, the same cuts and the same modules (`work/tools/cutcontrol.py` against the code of the last commit). It adds 4 layouts: 378 (f = 0.922, 6x6), 507 (0.965, 6x7), 637 (0.745, 8x8) and 638 (0.763, 6x11). The other 12 of the 14 stay refused: 9 because the rest is broken next to an arm that does not reach the corner (687, 689, 690, 742, 796, 798, 856, 913, 973), 2 because a run holds squares of another stack size (740 at 0.01, 797), 1 because an arm leans both ways (639), and 496 because a cell of the rest is empty. A loose tolerance on every layout changes 18 of the 73 cuts, so it is only a fallback. Arms of unequal stack size and a grid block as the corner were already in the model (a corner is all that lies before the first flush stack of both arms). What refuses them at low f is the rest beside an arm that ends short of the corner.

What the library holds below f = 0.80 (modules whose table reaches below 0.80, `work/tools/lowlib.py`, library `work/libz3`: 157 of 719 corners and 525 of 917 far zones reach below 0.80):

| corner (c1 x c2) | corners | from the zone lanes | f reached | lowest loss at the f it was found (corner, f) |
|---|---|---|---|---|
| 6x8 | 8 | 7 | 0.73 to 0.80 | 1.37 (`zc6x8-66f7877a.C`, 0.788) |
| 7x7 | 14 | 3 | 0.77 to 0.80 | 2.63 (`zc7x7-60f8543a.C`, 0.854) |
| 7x8 | 10 | 8 | 0.64 to 0.80 | 1.94 (`852h.C`, 0.700) |
| 7x9 | 24 | 12 | 0.77 to 0.80 | 2.60 (`zc7x9-110f8214a.C`, 0.821) |
| 8x6 | 8 | 5 | 0.71 to 0.80 | 2.80 (`zc8x6-92f7755a.C`, 0.775) |
| 8x7 | 9 | 6 | 0.78 to 0.80 | 3.51 (`zc8x7-84f8366a.C`, 0.837) |
| 8x8 | 59 | 43 | 0.63 to 0.80 | 2.47 (`zc8x8-98f7134a.C`, 0.713) |
| 9x7 | 4 | 2 | 0.76 to 0.80 | 3.78 (`983h.C`, 0.817) |
| 9x9 | 3 | 2 | 0.71 to 0.80 | 3.79 (`857h.C`, 0.767) |
| 10x6 | 14 | 8 | 0.72 to 0.80 | 3.90 (`zc10x6-102f8112b.C`, 0.811) |
| 10x10 | 4 | 2 | 0.74 to 0.80 | 4.76 (`981h.C`, 0.796) |

| far zone (c) | far zones | from the zone lanes | lowest loss at the f it was found (zone, f) |
|---|---|---|---|
| 6 | 53 | 44 | 1.55 (`z6-18f600.F1`, 0.600) |
| 7 | 144 | 87 | 2.18 (`987r10.F1`, 0.866) |
| 8 | 155 | 109 | 2.59 (`z8-17f650.F1`, 0.650) |
| 9 | 70 | 57 | 2.91 (`z9-54f640.F1`, 0.640) |
| 10 | 74 | 67 | 3.83 (`z10-50f680.F1`, 0.680) |
| 11 | 29 | 29 | 4.14 (`z11-45f760.F1`, 0.760) |

No corner of two 6-arms reaches below 0.80. No corner with an 11-arm does either (the library has two of 11x8, both above 0.80), so the design of 855 (an 8-arm and an 11-arm) has no corner in the library. Two 8-arms have 59 corners there, 43 of them from the zone lanes, and the best (2.47 at f = 0.713) is as good as the one of 740 (2.50). The 19 layouts cut below 0.80 are 12 of two 8-arms (685, 740, 911, 912, 974 and 975, several in more than one version), 2 of a 10-arm and a 6-arm, and one each of 8x6, 6x8, 7x8, 9x9 and 10x10.

The generator below f = 0.80:

- With the zones and the grants (S4), 13 of the 216 n there have a choice inside the window. One is below held: 634 (S4). The others are within 0.002 of held or equal to it (639, 740, 746, 852, 911, 912, 913, 974, 975 and 981 within 1e-3).
- With the modules of the two new low-f layouts (637 and 638, tables made for these 8 modules only), on the 216 n below 0.80 (`work/qz/qz5.tsv`): 24 rows on 8 n, none below held. 639 and 852 come back at held, 746 at +0.00023, 911 at +0.00012, 637 itself at +0.0012.

### S7. What to run next

1. Run the generator with the 5 states and no `--need` over every n. The lists of rounds 10 and 11 were chosen with the line between states (S1), so the best honest choices of the old library were never listed. With `fit_many` and the window this is about an hour on two processes.
2. Fix the head cell of a grant on a corner slid on the other arm (S2, 758): in `corner_slide` the head cell must take the grant of the other arm too. Then measure the 146 variants again, copy the current `modules.py` into the build dirs, and build the granted choices again.
3. Finer grants at the small end (0.01 and 0.02). 24 of the 46 poking far zones need 0.04 or less, and the cost grows fast with g. Measure the cost of a grant at more f than the one a corner was found at; today it is carried along f as a constant.
4. The true trade curve of a corner (a grid of caps on `y0`, the smallest `x0` by the chain of `corner_at`). It adds states between the 5 and wins back what the line found by luck.
5. Tabulate the zone files that have no table yet (1,428 in `take-zones-r11/work/zones`), and the 54 modules grown this round (`work/libgrow`: only the 8 of 637 and 638 have tables), then run the generator on them.
6. Low f: a module model for arms that stand off the wall and for bands of short stacks (855, 845). The cut cannot reach 192 of the 216 held layouts below f = 0.80, whatever its tolerance.
7. Rerun the take before a merge with `work/tools/final.sh`. It links the builds below the bar, runs `modules.py take gate/cand-round11-1111b/details.csv take-modules-r12 take-modules-r12/work/cand --beat` with the ten take dirs named at the top of this section, and writes the table of builds. The other takes took most of this round's large builds first.

## Round 4 (2026-11-12, round 13)

**Result: 3 n certify below held and below every other take of round 13: 700, 875 and 936, for 0.0002008. Nothing was submitted from here. All three come from modules grown from layouts of the last two rounds, and each round of growth gave the next its far zone. The generator over every n with the old library, the rebuilt zone corners and the finer grants found no other n below held. With the head cell fixed, every granted choice built this round has a start.**

Words used here: "held" is now `gather/round12-2026-11-12a.csv` (22.1822910977, gate dir `gate/cand-round12-1112a`). "The bar" of an n is the smallest of its held side and its side in the other takes of round 13 (every `take-*-r13` dir). A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r13`.

### T1. The head cell of a granted corner

A grant variant moves row 0 (or column 0) of the rest towards the corner by g. Cell (0, 0) is the head of both runs. Round 12 had a fault on a corner slid on one arm and granted on the other. There the head cell took its found place and ignored the grant, so the granted run stepped back at its head. Now `corner_slide` gives cell (0, 0) its found place and then moves it by the grant of any arm whose cells were not found slid. On the 729 corners that are not variants, the new code gives the same offsets as before for every cell (checked against the code of the last commit). Of the 2,972 variants, only the affected kind changes.

The 146 affected variants (93 granted on column 0 of a corner slid on row 0, 53 the other way) split in two:

- 113 can never be legal. Cell (1, 0) stands where the found slide of the row put it. Cell (0, 1) stands where the grant of the column puts it. The two cells overlap, by 0.018 in the median and up to 0.150. The contact LP does not test two fixed bodies against each other, so the old tables gave these variants a cost of 0. `cells_collide` now finds them, `grant` no longer makes them, and they are out of the library.
- 33 were measured again with the fixed head cell. 13 have no state at the smallest sum any more. The other 20 now cost 0.024 of length in the median (y0 + x0, up to 0.48), where the faulty head cell gave 0 for all but one.

The generator ran on these 33 alone with `tools/qcorners.py`, which loads only the listed corners and keeps every far zone. It gave 12 rows on 4 n (873, 921, 934, 984). The best is 5.8e-4 of side above held. All 8 granted choices built this round have a start. In round 12, none of the 9 had one. The 8 are on 758 and 996 (the two that failed in round 12), 921 and 984. None ends below held: 996 +2e-6, 921 +3.7e-4, 984 +4.7e-4, 758 +1.1e-3 of side above held.

### T2. The corner tables

The zone lanes stored their corners at f rounded to 4 decimals, while the squares and both lengths belong to the exact f of the run. We checked every corner of the round 12 library at its stored f. 446 of the 469 zone corners overlap a first flush stack. The other 23 hit their f exactly. The corners builder rebuilt them at the exact f, and its check finds 0 of 620 illegal (`take-corners-r13/work/zones`). The library of this round (`work/lib4`) drops all 469 old zone corners with their 2,425 grant variants and takes the 471 rebuilt corners that have a table.

The same check flags 175 cut corners of held layouts too, by up to 0.013 (`638h12.C`, cut at the loose tolerance). Their cause is not rounding. The stacks of a held layout are flush only to the cut's tolerance. Their tables start from an LP that pushes the stacks clear, as before.

Of the 1,430 far zone files in `take-zones-r11/work/zones`, 928 had no table in the library. 400 now have one (`work/zfar-tab.pkl`). The order was by how much a zone's loss beats the best zone of the library with the same stack size and class, within 0.03 of f. So all 246 that beat it are in. The other 528 lose to a zone the library has, and the time box left them out. The 46 modules grown in round 12 that had no table have one now (`work/grow-tab.pkl`).

### T3. The generator over every n

Three runs over all 413 n (held below the plain grid, n of 300 and more), each with the 5 states, window 0.05 and slack 0.002:

| run | library | modules counted as new | rows | n | below the bar | within 1e-3 of it |
|---|---|---|---|---|---|---|
| every choice (no `--need`) | round 12 with the grants, 4,479 modules | all | 238 | 80 | 3 rows on 1 n (601) | 165 |
| the rebuilt corners (`qcorners.py`) | `lib4` | 471 corners | 111 | 37 | 3 rows on 1 n (601) | 62 |
| the new tables | `lib3-m13b` (`lib4` with the 400 far zones and the 46 grown modules) | 446 | 216 | 73 | 7 rows on 3 n (601, 875, 936) | 144 |

The run with no `--need` takes about 9 minutes per half on two processes of boxD (more when the load gate pauses it). The run on the 471 corners alone takes 3 minutes.

- The rows below the bar on 601 use the corner `zc8x7-68f9708a` (old and rebuilt). Every build of them rebuilds the held 601 to 1e-9. The start needs 6e-4 of side above the prediction, and the squeeze then finds the held packing. So a prediction is not an upper bound for this corner.
- Most rows within 1e-3 of the bar are the held layout with one far zone swapped for one of the same count. They build back to held to 1e-9.
- The rows below the bar on 875 and 936 come from the run on the new tables, and both use the far zone `760h12.F2`. It was grown in round 12 from the held 760 (a family step 3 shells up from the held 601). Its corners are `817s11.C` and `817r10.C`, from our own soft-box search of round 11 on 817, and `zc7x7-78f9809ar.C`, a rebuilt zone corner.

### T4. The layouts grown this round

`modules.py grow` cut the held file of round 12 and the takes of round 13 into the library. It took 34 layouts of the held file, 1 of `take-polish-r13` and 1 of `take-family-r13`, for 124 modules (`h13`, `p13`, `f13`). 617 held layouts have no two flush arms, and 46 were in the library already. Then it cut the two wins of this round, 875 and 936 (8 modules, `t13`). The generator ran over every n with these modules counted as new:

| run | modules counted as new | rows | n | below the bar | within 1e-3 of it |
|---|---|---|---|---|---|
| `g13` (held round 12, polish and family takes) | 124 | 250 | 84 | 12 rows on 4 n (601, 700, 875, 936) | 179 |
| `t13` (the first builds of 875 and 936) | 8 | 27 | 9 | 6 rows on 2 n (875, 936) | 15 |
| `u13` (the second build of 936, on the 42 n of 600 and more with held f of 0.93 and more) | 5 | 27 | 9 | 6 rows on 2 n (875, 936), at the sides already built | 12 |

The rows below the bar on 700 are new: corner `598h13.C` and far zones `871h13.F1` and `812h13.F1`, all cut from the held file of round 12. On 936, the far zone `817h13.F2` (cut from the held 817 of round 12) sits beside `817r10.F1` and the rebuilt corner `zc7x7-78f9944br.C`. It predicts 0.0032 of side below held. The round's first 936 used `760h12.F2` in its place. So each round of growth gave the next one its far zone.

### T5. The cost of a grant along f

A variant's table is its corner's table plus the cost measured at the f the corner was found at, all along f. We tabulated 36 variants (12 per level, `work/tools/grantf.py`, `work/grantf.tsv`) with the grant in place and compared at the state of the smallest sum:

| grant | f below the found f by 0.03 and more | 0 to 0.03 below | at the found f | 0 to 0.03 above | 0.03 and more above |
|---|---|---|---|---|---|
| 0.04 | +0.000 (−0.046, +0.056) | +0.000 (−0.038, +0.035) | +0.000 | −0.002 (−0.053, 0.000) | −0.006 (−0.086, 0.000) |
| 0.10 | −0.001 (−0.239, +0.036) | −0.002 (−0.060, +0.014) | −0.002 | −0.021 (−0.146, 0.000) | −0.091 (−0.254, +0.026) |
| 0.16 | −0.032 (−0.166, +0.012) | −0.008 (−0.098, +0.014) | −0.003 | −0.071 (−0.187, −0.012) | −0.183 (−0.299, −0.030) |

The cells give the true length minus the table, in y0 + x0, as the median with the 10% and 90% quantiles in brackets. Above the found f, the constant overstates the cost of a grant of 0.10 and 0.16 by 0.02 to 0.18 in the median. So those variants are predicted too long there. Below the found f, the constant is right in the median. But one variant in ten is 0.04 to 0.06 longer than its table, so its prediction is too short. Tabulating each variant with its grant takes about 1.5 s. So the full table of the 3,195 variants of this library is about 80 minutes of one process.

The finer grants (0.01 and 0.02, `--levels`) on the library with the rebuilt corners gave 4,748 new variants. `cells_collide` refused 156, and 668 existed already:

| grant | variants | no state at the smallest sum | cost in y0 + x0 at the smallest sum, median | quartiles | zero (below 1e-4) |
|---|---|---|---|---|---|
| 0.01 | 952 | 40 | +0.000 | +0.000, +0.005 | 428 |
| 0.02 | 1,345 | 88 | +0.002 | +0.000, +0.013 | 497 |
| 0.04 | 976 | 163 | +0.014 | +0.000, +0.058 | 230 |
| 0.10 | 412 | 124 | +0.095 | +0.039, +0.165 | 16 |
| 0.16 | 1,063 | 434 | +0.294 | +0.139, +0.363 | 5 |

A grant of 0.01 is free for nearly half the corners. The generator on these variants alone (`qz/qfine-m13b.tsv`, all 413 n) gave 104 rows on 36 n, none below the bar. The best is 601 at 4.7e-5 of side above held, with `601m10.C^1g01`.

### T6. The sources of held layouts

`held_sources` read only the per-round tables (`*best-20*.tsv`). It missed `angle-harvest-2026-11-10.tsv`, which names the n that the angle step of 2026-11-10 changed outside a round. So it named the alexchilton starter kit as the source of the held 702. But the packing comes from the malyshevdanil atlas (Apache 2.0). It now reads both kinds of table in the order of the date in their name. Without the round 12 table, 702 now comes back as the malyshevdanil atlas.

### T7. Builds

82 choices were built on 26 n, all with a start. 20 builds on 3 n certify below held and below the bar. The take keeps 3 n. The rows of every list are in [`results/modules-r13-2026-11-12.tsv`](../results/modules-r13-2026-11-12.tsv).

| list | built | on n | below held | kept |
|---|---|---|---|---|
| the generator over every n, 5 states | 14 | 8 | 0 | 0 |
| the granted choices with the fixed head cell | 8 | 4 | 0 | 0 |
| the rebuilt zone corners | 13 | 7 | 0 | 0 |
| the new far zone tables (and the 46 grown modules of round 12) | 31 | 15 | 8 on 2 n | 0 |
| the layouts grown from the held file of round 12 (`g13`) | 6 | 2 | 6 | 2 (700, 936) |
| the builds of this round, grown (`t13`, `u13`) | 6 | 2 | 6 | 1 (875) |
| the finer grants, the best row per n at even positions | 4 | 4 | 0 | 0 |

| n | build | corner, far zones | stacks | predicted - held (side) | built - held (side) | gain (score) |
|---|---|---|---|---|---|---|
| 700 | `700-Y2` | `598h13.C`, `871h13.F1`, `812h13.F1` | 6, 5 | -0.000313 | -0.001459 | 5.516e-05 |
| 875 | `875-V9` | `875t13.C`, `875m10.F1`, `817h13.F2` | 14, 11 | -0.000601 | -0.001049 | 3.546e-05 |
| 936 | `936-W1` | `zc7x7-78f9944br.C`, `817r10.F1`, `817h13.F2` | 17, 12 | -0.003159 | -0.003370 | 1.101e-04 |

The squeeze ends below the prediction on every kept build, by 0.0002 to 0.0011 of side. On 936 the steps were: `760h12.F2` gave -0.00242, then `817h13.F2` from the held file gave -0.00337, and the 936 layouts grown from those builds gave the same side to 1e-8. On 875 the first build (`817s11.C` with `760h12.F2`) gave -0.000907, and the corner grown from it (`875t13.C`) with `817h13.F2` gave -0.001049. The other builds below held rebuild the held layout to 1e-9 and do not certify. The 875 row reaches the kmmmvs bundle ("Other" terms) through `875m10.F1`, and `take.tsv` names it in its source and licence columns.

### T8. What to run next

1. Grow every new layout into the library as soon as it certifies, and run the generator on the new modules at once. All three wins of this round use modules grown one round earlier or in this round. The run on new modules takes 3 to 30 minutes on one process.
2. Tabulate each grant variant with its grant (T5), at least those in a row within 1e-3 of the bar, instead of carrying the cost at one f.
3. Tabulate the other 528 far zone files with no table, and the last corner library of the corners builder (`take-corners-r13/work/zones-t`). It adds the hopped 7x9 corner `zc7x9-110f8204at.C`, which certifies 984 and 921 in round 13.
4. The corner of 601 (`zc8x7-68f9708ar`) predicts 2e-4 of side below held and builds back to held. Find which state of the table has no layout under it.
5. Low f: a module model for arms that stand off the wall and for bands of short stacks (855, 845). It was not started this round.

## Round 5 (2026-11-12, round 14)

**Result: 8 n certify below held and below every other take of round 14: 758, 862, 863, 871, 924, 984, 994 and 995, for 6.20e-5. Nothing was submitted from here. Five of the eight use a new kind of module: a far zone walked by steps of 0.001 instead of 0.005 (a dense twin). Each win was cut into the library at once, and the generator near it gave the next win on 758, 862 and 994. The 601 row that predicted below held fails because the table of one far zone is 5.2e-3 too short between two knots. `modules.py check` now tests a row the way the build starts it.****

Words used here: "held" is now `gather/round13-2026-11-12a.csv` (22.1697213494, gate dir `gate/cand-round13-1112a`). "The bar" of an n is the smallest of its held side and its side in the other takes of round 14 (every `take-*-r14` dir). A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r14`. The library of this round starts from `lib4-m13b` of round 13 and adds the grown modules of `libgrow13` without its old zone corners (`work/lib14`, 7,889 modules).

### U1. The layouts of round 13 grown

Round 13 moved 134 n, 133 of them at 300 and more. `modules.py grow` cut the held file of round 13 into the library at once. It took 19 new layouts for 72 modules (`h14`). 51 layouts of the held file were in the library already. 628 have no two flush arms, 2 have a broken rest and 1 a run that is not a whole number of pitches.

The cut misses most of the public fault-line layouts. 97 of the moved n come from the jonathan1506 notebook, directly or through our fq polish. Only 9 of the 97 have two arms of flush stacks on two walls, and the cut takes 6 of them (418, 507, 553, 587, 600, 981). In the other 88:

| what the stacks of 5 and more do | layouts | f |
|---|---|---|
| no stack is flush (more than 0.01 of width off) | 49 | 0.63 to 1.00, median 0.80 |
| no stack of 5 or more | 14 | 0.56 to 0.76 |
| flush stacks, but off the wall | 13 | 0.64 to 0.88 |
| flush stacks on one wall only | 12 | 0.74 to 0.95 |

The family and readers lanes found the same split this round (handoff of 06:38 and 06:40). 55 are two blocks of staggered stacks on two walls, off the wall by a fraction. 12 are one band from corner to corner. Their reader takes 62 of them, and the family walk carries them. The module cut would need a far zone and a corner that stand off the wall.

The tables of the 72 modules took 2 minutes on one process. The 5 hopped corners of the corners builder (`take-corners-r13/work/zones-t`) were not in the library, and have tables now (`lib14b`). Every other corner of `take-corners-r13/work/zones` was in it already. The corners builder sent 11 more corners at 07:47 (`take-corners-r14/work/lib-u2-14b`). The generator on these 11 alone over every n (`tools/qcorners.py`) gives 9 rows, none below the bar. The best is 600 at 6.1e-4 of side above held.

### U2. The 528 far zones

The 528 far zone files of `take-zones-r11/work/zones` that had no table all have one now (`work/lib14c`, 8,494 modules). They took 7 minutes on two processes of boxD. All 528 lose to a zone of the library with the same stack size and class within 0.03 of f, so they were last in line. No generator run counted them as new this round. They are in every library from `lib14c` on, so the runs below use them as old modules.

### U3. The generator over every n

| run | library | modules counted as new | n searched | rows | n | below held | within 1e-3 of held |
|---|---|---|---|---|---|---|---|
| `h14` | `lib14b` | 72 grown (held of round 13) and the 5 hopped corners | all 413 | 221 | 74 | 3 rows on 1 n (601) | 181 |
| `b1`, `g2` | `libg` | 25: the first 3 wins of this round and 4 layouts of other round 14 takes | about 50 of 162 | 43 | 15 | 0 | 39 |
| dense | `libd` | 159 dense twins (U6) | the 72 n of rows within 1.5e-3 | 216 | 72 | 3 rows on 1 n (601) | 192 |
| `g3` | `libd` | 28: 4 family layouts of round 14 and 4 wins grown again | the nearest 25 or more of 99 | 72 | 24 | 5 rows on 2 n (871, 994) | 60 |
| `g4` | `libd` | 3: the 995 win grown | 5 | 10 | 5 | 1 row (994) | 10 |

The `h14` run took 14 minutes on three processes (one on boxA, two on boxD). Every row below held on 601 is the false row of U5. Most rows within 1e-3 of held are the held layout with one far zone swapped, and they build back to held. The runs after `h14` searched only near the grown layouts: the n whose held f is within 0.01 to 0.03 of theirs, the nearest n first. They stopped when the builds needed the process. Four of the eight wins came from those runs (758 and 862 a second time, 871, 994).

### U4. Grant variants with their grant in place

A grant variant's table was its corner's table plus the cost measured at one f (T5 of round 4). Here every variant in a generator row within 1e-3 of the bar, in round 13 or this round, got its true table. The tool is `tools/truegrant.py` (`modules.tabulate` with the grant in place). It made 19 variants on 31 n, about 2 s each.

- At the smallest sum, the true table differs from the carried one by 0.0000 in the median for 12 of the 19. For the other 7 the median is between -0.0016 and +0.0126. The extremes are far from the found f (863q1.C^1g02: -0.128 to +0.335).
- Two variants lose most of their states: zc7x7-78f9869ar.C^2g10 keeps 3 of 14 values of f and zc9x7-146f8169br.C^2g02 keeps 15 of 24.
- The generator on these 19 corners alone over their 31 n gives 51 rows with the carried tables and 48 with the true ones. The 43 rows in both move by -6.7e-5 to +7e-6 of side. No row is below the bar in either run, and the best row is the same: 601 with `601m10.C^1g01` at 4.7e-5 of side above held.

So the cost carried from one f was close enough near the bar, and the true tables change no build.

### U5. The corner of 601

The row `zc8x7-68f9708ar.C` + `814h09.F1` + `507h12.F2` (stacks 12 and 10) predicts 601 at 2.08e-4 of side below held. Its builds start only 4e-4 above the prediction and squeeze back to held. The corner is not the cause (`tools/diag601.py`):

- Arm 1 binds. At the predicted f = 0.95375 the corner's state of the smallest sum fits arm 1 with 0 slack. The corner walked to f the way the build walks it lands on the table to 2e-5.
- The far zone `814h09.F1` does not. Its table has knots at its found f (0.954616) and at 0.950, and puts its length at 4.15409 at f = 0.95375. Walked there, from its found f or up from 0.950, it is 4.15933, so 5.2e-3 longer. Its length jumps by 5.2e-3 between f = 0.9545 (4.15466) and 0.9540 (4.15984), between the two knots.
- With the walked length, the corner has no state under the cap of arm 1 until f is 4e-4 higher (side 24.95415). That is 1.9e-4 above held, and the squeeze from there finds the held packing.

The same check on 144 far zones of this round's rows (`tools/farcheck.py`, a walk by steps of 0.0005 within 0.01 of the found f, against the table):

| the walk against the table | far zones |
|---|---|
| longer by more than 1e-3 somewhere (the table has no state there) | 12 |
| of them by more than 5e-3 | 8 |
| shorter by more than 1e-3 somewhere (a shorter state the table misses) | 73 |
| of them by more than 5e-3 | 17 |

So the length of a far zone is not straight between two knots 0.005 apart, in either direction. `modules.py check` now tests each row of a queue the way the build starts it. It walks the far zones to f, puts the corner under both caps and tests the gaps. It gives the smallest f at which the row starts. On 102 rows of this round, 83 start at the predicted f, 17 start 3e-5 to 9.7e-4 higher, and 2 do not start within 3e-3. The 601 rows start 2.8e-4 higher, 7.3e-5 above held.

### U6. Dense twins of far zones

The walk of U5 also finds shorter states than the table, so a far zone walked by smaller steps can make a shorter arm. A far zone may now carry a step `walk`. `modules.tabulate` then walks it from its found f by that step, up and down `walk_span`, with a knot at every step. `modules.far_at` walks the build by the same steps (`path(f0, f, walk)`). Without `walk` nothing changes.

`tools/densify.py` made a dense twin (id + `d`, step 0.001, span 0.03) of the 159 far zones in the rows of the `h14` and `b1`/`g2` runs (`libd`, about 4 s per zone). Against the table of the zone it was made from:

| the dense twin against the table | far zones |
|---|---|
| shorter by more than 1e-3 somewhere | 118 |
| of them by more than 5e-3 | 48 |
| longer by more than 1e-3 somewhere | 43 |
| of them by more than 5e-3 | 31 |

The library keeps both, so the generator takes whichever is shorter. With the twins counted as new, the best row of an n moved down on 24 of the 72 n. The largest move is 9.3e-4 of side (760: from +1.46e-3 to +5.35e-4 above held). It moved up on 4, where the best row without a twin is not in this run. Five of the eight wins below use a twin (758, 871, 984, 994, 995).

### U7. Builds

136 choices were built on 29 n, all with a start: 2 processes on boxD and 1 on boxA, about 40 s each. 46 builds on 9 n end below held, and the take keeps 8 n. The rows of every list are in [`results/modules-r14-2026-11-12.tsv`](../results/modules-r14-2026-11-12.tsv).

| list | built | on n | below held | kept |
|---|---|---|---|---|
| `h14` (held layouts of round 13, hopped corners) | 58 | 22 | 12 | 0 |
| `b1`, `g2` (the first wins and round 14 takes grown) | 20 | 7 | 9 | 1 |
| dense twins | 41 | 25 | 11 | 2 |
| `g3` (round 14 takes and wins grown again) | 15 | 5 | 12 | 4 |
| `g4` (the 995 win grown) | 2 | 1 | 2 | 1 |

| n | build | corner, far zones | stacks | predicted - held (side) | built - held (side) | gain (score) |
|---|---|---|---|---|---|---|
| 758 | `758-G003` | `758h14.C`, `758b14.F2d`, `815fa14.F1` | 12, 8 | +0.000015 | -0.000026 | 9.41e-07 |
| 862 | `862-G007` | `862h13.C~`, `862q1.F2`, `862b14a.F1` | 12, 11 | +0.000060 | -0.000029 | 9.88e-07 |
| 863 | `863-G002` | `863q1.C`, `863b14.F1`, `863b14.F1` | 14, 14 | +0.000009 | -0.0000006 | 1.97e-08 |
| 871 | `871-G016` | `871fa14.C`, `812h13.F1`, `599fa12.F2d` | 11, 7 | -0.000118 | -0.000315 | 1.069e-05 |
| 924 | `924-B012` | `924b14.C`, `924fa12.F2`, `924h14.F1` | 16, 16 | +0.000077 | -0.000005 | 1.50e-07 |
| 984 | `984-D062` | `984h14.C~`, `862q1.F2`, `921h13.F2d` | 12, 13 | +0.000171 | -0.000076 | 2.437e-06 |
| 994 | `994-K01` | `zc8x9-141f9415ar.C`, `995b14.F1`, `811h.F1d` | 12, 10 | -0.000158 | -0.000868 | 2.754e-05 |
| 995 | `995-D068` | `995h13.C`, `599fa12.F2d`, `995h13.F2d` | 12, 10 | +0.000203 | -0.000606 | 1.922e-05 |

The first builds below held came from the `h14` rows on 758, 862, 924 and 984, predicted 2e-5 to 1.7e-4 above held. The squeeze ends below the prediction on every kept build, by 0.00001 to 0.00081 of side. 995 and 984 come from dense twins. 871 uses the corner of the family lane's new 871 (`871fa14.C`) with a dense twin. 994 uses the zone corner `zc8x9-141f9415ar.C` with the far zone of the 995 win and a dense twin. The same row came out of the `g3` run with a far zone of the family's 871 or 932. Every take row starts from held or take layouts whose sources and licences `take.tsv` names: Apache 2.0, CC BY 4.0 (busyaprime, through 863 and 924) and the seed merged0. No row reaches a source under "Other" terms.

### U8. What to run next

1. Make dense twins for the far zones of every row within 2e-3 of held, and run the generator on them. This round made 159. A twin takes about 4 s.
2. Grow every win at once and search the n within 0.01 of its f, nearest first. This round the chain gave 758 and 862 twice, and 994 from 995.
3. Run `modules.py check` on the rows before the builds, and sort the builds by the checked side.
4. A cut for arms that stand off the wall. 88 of the 97 jonathan1506 layouts have no two flush arms on walls, and the readers lane reads 62 of them as two blocks of staggered stacks.
5. The 528 far zones of U2 as new modules, which no run of this round counted as new.

## Round 6 (2026-11-12, round 15)

**Result: no n in the take. Two n certified below held during the round, and other takes of round 15 beat both by the end. 921 certified 1.181e-6 below held (3.59e-5 of side). The corners lane later took 921 much lower. 587 certified 4.0e-8 below held, and the polish lane took our file and quenched it lower. Both wins came from rows predicted 3.2e-4 and 7.7e-4 above held, and both use a dense twin of this round. The final `take.tsv` holds only its header. Nothing was submitted from here.**

Words used here: "held" is now `gather/round14-2026-11-12a.csv` (22.1686761690, gate dir `gate/cand-round14-1112a`). "The bar" of an n is the smallest of its held side and its side in the other takes of round 15 (every `take-*-r15` dir). Harvest passes j and k (`take-harvest-2026-11-12j`, `-12k`) count as takes too. A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r15`. The library of this round starts from `libd` of round 14 (`work/lib15`).

### V1. New layouts grown into the library

| source | layouts | cut | modules | why the others were not cut |
|---|---|---|---|---|
| held of round 14 (`h15`) | 701 (n of 300 and more) | 7: 551, 600, 651, 813, 872, 933, 935 | 24 | 626 no two flush arms, 65 in the library already, 3 other |
| harvest pass j (`hj`) | 22 | 1: 507 | 5 | 21 no two flush arms |
| round 15 takes until 09:37 UTC | 15 | 3: 507 and 812 (polish), 921 (family) | 13 | 12 no two flush arms |

The generator ran with each set counted as new, over the n whose bar f is within 0.01 of a grown layout, nearest n first. Each n took about 30 s on one process, so the runs were cut short: `h15` searched 32 of 63 n and `t12` 8 of 14. `hj` searched all 18.

### V2. Dense twins of far zones

A dense twin is a far zone walked by steps of 0.001. Round 14 gave one to 157 of the 211 far zones in its rows within 2e-3 of the new held. Two passes made the rest:

| pass | far zones | shorter than the table by more than 1e-3 somewhere | by more than 5e-3 | longer by more than 1e-3 | by more than 5e-3 |
|---|---|---|---|---|---|
| `d15`: the round 14 rows | 54 | 48 | 14 | 21 | 18 |
| `d2`: the rows of this round (`h15`, `hj`, `f528`, `d15`) | 60 | 50 | 15 | 25 | 17 |

Each twin took about 5 s on boxD. The twins are as uneven as in round 14. Nearly every far zone has a state more than 1e-3 shorter than its table within 0.03 of its f.

### V3. The generator runs

| run | modules counted as new | n searched | rows | n | below held | best rows |
|---|---|---|---|---|---|---|
| `h15` | 24 (V1) | 32 | 64 | 22 | 0 | 505 +2.0e-5, 993 +5.4e-5, 814 +1.45e-4 |
| `hj` | 5 (V1) | 18 | 18 | 6 | 3 rows on 601 (false, U5) | 758 +5.6e-5, 652 +9.8e-5 |
| `d15` | 54 twins | 73 | 205 | 69 | 3 rows on 601 | 634 and 639 at held, 863 +8e-6 |
| `f528` | the 528 far zones of U2 | 73 | 161 | 54 | 0 | 634 at held, 505 +2.2e-5, 338 +5.9e-5, 863 +6.3e-5 |
| `d2` | 60 twins | 43 | 121 | 41 | 3 rows on 601 | 634 at held, 863 +8e-6, 505 +2.0e-5 |
| `t12` | 13 (V1) | 8 | 24 | 8 | 0 | 652 +9.8e-5, 803 +3.15e-4 |

The `f528` and dense runs searched the 73 n that had a row within 2e-3 of held in round 14 or this round, not every n. Against the best round 14 row of each n (measured against the new held), the runs lowered the best row on 8 n. The largest moves are on 551 (from +2.07e-3 to +4.9e-4, with the grown 551) and 704 (from +5.2e-4 to +2.8e-4). The 704 row uses the grown 651 corner and 507 far zone. No run found a row below held on an n other than 601.

The generator is close to saturated near held. On most n the best rows of every run are the held layout with one far zone swapped for another of the same length. They predict held to 1e-6.

### V4. The check before the builds

`modules.py check` ran on every row before it was built, and the builds were sorted by the checked side.

| rows | checked | start at the predicted f | start up to 1e-4 higher | up to 5e-4 higher | more | no start |
|---|---|---|---|---|---|---|
| round 14 rows, `h15`, `d15` (within 4e-4) | 286 | 239 | 31 | 14 | 2 | 0 |
| `hj`, `f528`, `d15` (within 4e-4, new) | 57 | 45 | 3 | 6 | 3 | 0 |
| `t12` (within 4e-4) | 12 | 12 | 0 | 0 | 0 | 0 |
| every run (within 1e-3, at most 2 per n and corner) | 179 | 155 | 14 | 7 | 3 | 0 |

The 601 rows on `814h09.F1` start 2.81e-4 higher, at 7.3e-5 above held, as in round 14.

### V5. Builds

142 choices were built on 41 n: 1 process on boxA and 1 or 2 on boxD, about 30 to 80 s each. Every choice had a start. The rows of every list are in [`results/modules-r15-2026-11-12.tsv`](../results/modules-r15-2026-11-12.tsv).

| what the build ends at | builds |
|---|---|
| below held by more than 1e-10 of score | 7 (on 921 and 587) |
| the held side to 1e-8 | 59 |
| above held | 76 |

- 125 of the 142 builds end below their prediction (the median is 8.8e-5 of side below). Most of them still end at or above held.
- The rows predicted within 3e-4 of held gave nothing. Most are the held layout with one far zone swapped, and they build back to held.
- At 09:57 the build lists were remade from every checked row up to 1e-3 above the bar, with the n that had the fewest builds first (`tools/reprio.py`). Both wins came from that list. `921-G019` is `921po14.C` + `983h.F1` + `863b14a.F1d` (stacks 14 and 11), predicted +3.2e-4, built -3.59e-5 of side. `587-G041` is `587h14.C` + `639h.F2` + `z11-45f760.F1d` (stacks 6 and 5), predicted +7.7e-4, built -9.7e-7.
- The fq quench of the polish lane (`zone_corner.py quench`, from the certified file) took 587 a further 2.8e-8 of side and found nothing on 921.
- The 921 win was grown at once (`w15`) and the generator ran over the 6 n nearest its f. The three builds from it on 921 end at the same layout (to 4e-15 of score). The builds on 803 and 983 end above held.
- Two more growth steps cut the round 15 takes that landed later. They took the family lane's 871, 912, 975 and 984, the corners lane's 983 and the polish lane's 912. Their rows build above held.

### V6. Arms that stand off the wall

`tools/offwall.py` looks at the 626 held layouts the cut refuses for "no two flush arms". It groups the flush stacks of 5 and more by direction and size and measures how far each group of 3 or more stands from its nearest wall.

- 55 of the 626 have such a group, and 5 of them have two (60 groups).
- In 39 layouts every group is on its wall (offset below 0.002), and the second arm is not flush.
- 17 groups stand one column off the wall (offset 0.996 to 1.001), and one (593) stands two columns off. One more (916) stands 0.002 off.
- 802, 861 and 972 have two arms, both one column off their walls.

So an arm off the wall stands a whole column off, never a fraction. That column is the outer L of the next shell. A layout of n with both arms one column off holds a layout of a smaller n inside one L of the shell (the L holds 2m-1 squares). `tools/peel.py` tried to peel that L (the left column and the bottom row, in all four orientations) and cut what is left. It peels none of the three: their outer L holds 6 to 10 tilted squares in the best orientation, so it is not a plain column of uprights. A cut for these layouts needs a module for the outer L itself (an L zone). The family lane already walks these layouts one shell up and down.

### V7. What to run next

1. Build rows further from held. Both wins of this round were predicted 3.2e-4 and 7.7e-4 above held. The rows within 3e-4 are nearly all the held layout again. Put the n with the fewest builds first.
2. Make the generator faster. With a far zone list to hold, one n takes about 30 s. So the near searches of this round stopped at 32 of 63 n (`h15`) and 8 of 14 n (`t12`).
3. Grow every new take layout at once, as this round did three times. The family and corners lanes now produce layouts that cut.
4. A module for the outer L of a shell (V6). It would let the cut take the layouts whose two arms stand one column off their walls.
5. Hand every certified win to the polish lane at once. The fq quench of another lane took 587 lower than our file.

## Round 7 (2026-11-12, round 16)

**Result: 6 n certify below held and below every other take of round 16, for 1.130e-4 against held. They are 649 (4.49e-5), 921 (2.92e-5), 984 (2.82e-5), 995 (1.08e-5), 974 (1.7e-8) and 983 (3.7e-10). Each big win takes the corner of a new layout and puts other far zones and other stacks beside it. The squeeze does the rest. Five more of our builds went below held, and other lanes took them lower: soft took 549 and 700, the corners lane 703, and the family lane 860. Nothing was submitted from here.**

Words used here: "held" is now `gather/round15-2026-11-12a.csv` (22.1672602051, gate dir `gate/cand-round15-1112a`). "The bar" of an n is the smallest of its held side and its side in the other takes of round 16. These are every `take-*-r16` dir and harvest passes l and later. A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r16`. The library of this round starts from `lib15` (`work/lib16` on boxA, `work/lib16b` with every growth step of the round).

### W1. A faster generator

`Library.best` spent nearly all its time in `options`, which built the options of an arm one far zone at a time. Three changes, all exact:

- The options of a class of far zones are now computed as arrays, for all far zones of the class at once. The first f at which s stacks fit is one sorted search over the running maximum of each row.
- The two arms are paired by a join on the square count. The pairs are sorted the way the old loops left them.
- With a list to hold (`--need`), a corner is skipped when neither of its arm classes holds a far zone of the list.

On the six searches we compared, the rows are the same as with the old code:

| n | list | old | new |
|---|---|---|---|
| 921 | `new-t4` | 6.4 s | 1.4 s |
| 812 | `new-t4` | 26.9 s | 6.8 s |
| 587 | `new-t4` | 5.4 s | 1.2 s |
| 704 | `new-t4` | 30.1 s | 7.2 s |
| 921 | none | 5.7 s | 1.3 s |
| 652 | none | 30.5 s | 8.1 s |

A near search now covers 40 n in 1 to 4 minutes on one process of boxD. Round 15 stopped these searches at 32 of 63 n. This round ran every list of round 15 again over the 40 n nearest its f (`t4`, `t3`, `t12`, `hj`, `h15`, `t2`, `t1`). They found no row below held other than the rows of the corners in W2 and the false 601 rows.

### W2. New layouts grown at once

| step | source | layouts cut | corners added |
|---|---|---|---|
| `g1` | held of round 15 (48 moved n) | 4 | `912h16`, `921h16`, `974h16`, `984h16` |
| `u2` | takes of round 16 by 12:33 UTC | 7 | corners lane 974, polish 974, readers 975 and 995, our 598, 921 and 984 |
| `u3`, `u4` | family 649, 812 and 860 | 3 | `649fa16`, `812fa16`, `860fa16` |
| `u5` | family 598 and 649, corners lane 863 | 3 | `598fa16`, `649fa16a`, `863co16` |
| `u7`, `u8` | our 649, 700 and 703, polish 863, soft 700 | 5 | `649mo16`, `700mo16`, `703mo16`, `863po16`, `700so16` |

The other 44 moved layouts of the held file have no two arms of flush stacks on two walls. A loop on boxA copied every take of round 16 to boxD every 8 minutes. When a layout changed, a chain there cut it and tabulated the new modules. It made dense twins of the new far zones and ran the generator over the 40 nearest n with them counted as new. Then it checked the rows and built them.

The corners of new layouts gave every big win of the round:

| n | corner | far zones | stacks | predicted minus held | built minus held | list |
|---|---|---|---|---|---|---|
| 921 | `921h16.C` (held 921, a corners lane build after fq) | `983h.F2`, `z9-43f840.F1` | 10, 14 (held: 10, 8) | -4.3e-4 | -8.85e-4 | `g1` |
| 984 | `984h16.C~` (held 984, the same kind) | `804h.F2`, `921h13.F2` | 12, 13 (held: 12, 10) | -3.4e-5 | -8.84e-4 | `g1` |
| 649 | `649fa16a.C` (family 649) | `503h.F2`, `504m10.F1` | 7, 7 | -5.5e-4 | -1.14e-3 | `u5`, `u7`, `W` |
| 995 | `995re16.C` (readers 995) | from the library | | +2.2e-4 | -3.4e-4 | `W` |
| 700 | `598fa16.C` (family 598) | `995z11.F2`, `871b14.F2d` | 6, 5 | +6.2e-5 | -9.64e-4 | `u5` |

On 921 and 984, 16 of the 23 builds end at the side of the win to 1e-8, whatever far zones and stacks they start with. Six end at a second side, 6.4e-4 to 6.6e-4 below held, and one ends above held. So each corner leads to one or two layouts after the squeeze, whatever far zones it starts with.

### W3. Builds

175 choices were built on 55 n: 1 process on boxA (paused while its load was above 15) and 2 on boxD. Every choice had a start. The rows are in [`results/modules-r16-2026-11-12.tsv`](../results/modules-r16-2026-11-12.tsv).

| list | builds | n | below held | more than 1e-5 of side below held | kept |
|---|---|---|---|---|---|
| `A`: checked rows of rounds 13 to 15, 3e-4 to 1e-3 above held, fewest builds first | 47 | 45 | 5 | 2 (549, 703) | 983 |
| `G`: the generator on `g1` | 7 | 3 | 5 | 5 (921, 984) | 921, 984 |
| `V`: the four `g1` corners, 40 choices per n | 24 | 4 | 10 | 10 (921, 984) | none (same sides as `G`) |
| `u`: the growth steps of W2 | 68 | 19 | 37 | 33 (598, 649, 700, 860, 921, 984, 995) | 649 |
| `W`: every new corner of the round, 12 choices per n | 28 | 8 | 24 | 22 (598, 649, 703, 860, 995) | 974, 995 |
| `b`: the round 15 lists again | 1 | 1 | 1 | 1 (921) | none |

- The rows 3e-4 to 1e-3 above held (`A`) gave 549 (predicted +5.8e-4, built -1.05e-4) and 703 (predicted +8.5e-4, built -2.4e-4). The squeeze takes 6.2e-4 off the start in the median, so most of these rows still end above held.
- On the rows with a new corner, the squeeze takes 4.9e-4 (`u`) to 8.3e-4 (`W`) off the start in the median. Most of that is the fq step. On 921 the LP stays at the start and fq takes 6.6e-4 off it.
- The fq quench from the certified file (`zone_corner.py quench`) found nothing more on 549, 598, 649, 700, 703, 921, 984 and 995.
- Each certified win went into the handoff log for the polish and corners lanes within 2 minutes (`tools/takeloop.sh`, a take every 90 s with `--beat` over every live take dir). `take.tsv` was replaced by rename each time.

### W4. The outer L of a shell

Not started. The rows of W2 took the time of this round. The design stays as round 15 left it (V6). We need a zone for the outer L of a shell. Then the cut takes the layouts whose two arms stand one column off their walls (802, 861, 972 and 17 more groups).

### W5. What to run next

1. Grow every new layout of every lane at once and build its corner with other far zones and other stacks. This gave all the big wins of this round. Build at most two choices per corner and pair of stacks: the others end at the same side.
2. Run the growth loop from the start of the round, every 5 minutes, and keep a build slot free for its rows.
3. Build the rows 3e-4 to 1e-3 above held only after the growth rows. They gave 2 wins in 47 builds.
4. A zone for the outer L of a shell (W4).

## Round 8 (2026-11-12, round 17)

**Result: 5 n certify below held and below every other take of round 17, for 2.133e-4 against held and 1.901e-4 over the other takes. They are 754 (1.237e-4), 703 (6.30e-5), 700 (1.49e-5), 598 (1.17e-5) and 378 (3.9e-8). Every win uses the corner of a layout made in this round, and in the median the squeeze takes 8.6e-4 to 4.9e-3 off the rows of these corners. On older corners it takes 5e-4. An earlier 378 went into the round 17 file. 549 certified for 3.40e-5, and then the corners lane took it lower. Nothing was submitted from here.**

Words used here: "held" is now `gather/round16-2026-11-12a.csv` (22.1664224426, gate dir `gate/cand-round16-1112a`). "The bar" of an n is the smallest of its held side and its side in the other takes of round 17 (every `take-*-r17` dir). A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r17`. The library of this round starts from `lib16b` of round 16 (`work/lib17`).

Three other lanes own slices of n this round, and we build nothing there. With `k = n - m²`, the twoshort lane has m 28 to 31 with k 5 to 16. The stair-b lane has m 24 to 27 with k 4 to 20. The stair-c lane has m 28 to 31 with k 17 to 45. `tools/slicefilter.py` drops every build line in these slices.

### X1. The twoshort layouts and the round 16 held file grown

`g1` cut the round 16 held file and every take of round 17 that had a layout at 15:14 UTC.

| source | layouts cut | not cut |
|---|---|---|
| held of round 16 | 7: 600, 700, 703, 704, 932, 974, 995 | 628 no two flush arms, 63 in the library already, 3 other |
| twoshort takes | 9: 796, 852, 910, 913, 914, 973, 975, 976, 978 | 851, 912 and 974: one stack run holds 3 or 4 squares fewer than its stacks. 911: no two flush arms |
| classfill take | 1: 703 | |
| midm takes | 1: 378 | 8 no two flush arms |

The 18 layouts gave 54 modules (18 corners, 36 far zones). Their tables and the dense twins of the 36 far zones took 6 minutes on two processes of boxD.

### X2. Every n predicted again

The generator ran over all 414 n with the 90 new modules and twins counted as new (`--need`, top 3 per n). It found 104 rows within 1e-3 of the bar, on 37 n. Three are predicted below the bar, all on 601, and they hold `814h09.F1`, the far zone whose table is wrong between its knots (round 6). Most of the other rows are in the slices of other lanes:

| slice | rows | n |
|---|---|---|
| twoshort | 18 | 796, 852, 910, 973, 974, 976 |
| stair-b | 6 | 634, 740 |
| stair-c | 60 | 812, 814, 815, 871, 873, 930, 931, 932, 933, 978, 994, 995, 997 |

We wrote these rows to `work/rows-for-<lane>.tsv` and gave each of the three lanes one line in `handoff-r17.log`, with the library that holds the ids. We built the rest.

### X3. Four cuts

The lane stopped four times. At about 16:05 UTC a model limit stopped the agent, and at 16:15 UTC boxA panicked, so every process on it died. At 17:52 UTC and at 19:05 UTC the agent that ran the lane hit a usage limit, but the jobs on the boxes ran on. After each cut we collected the finished builds from `work/` and from boxD, certified them and went on. Builds moved to boxD (two processes) and boxE (one process). From 18:20 UTC boxA ran at load 100 to 160, so it kept only the cut and the tables. From 19:12 UTC boxE ran at load 67 on 18 cores, so it got no new work, and its last list ended at 19:25 UTC. The generator and the check of each growth step ran on boxD, where 219 n take 20 s. `work/STATE.txt` (one line per start, stop and decision) lets the next attempt pick up after a cut.

### X4. Corners that build far below their prediction

| n | build | corner | far zones | stacks | predicted - held | built - held | gain on held | gain over the other takes |
|---|---|---|---|---|---|---|---|---|
| 754 | `754-t9003` | `813mi17.C` | `z8-44f950.F1`, `700h17.F1` | 9, 6 | +0.005296 | -0.003398 | 1.237e-04 | 1.237e-04 |
| 703 | `703-rf071` | `815st17.C` | `651h.F2`, `600h15.F2d` | 5, 10 | +0.004015 | -0.001671 | 6.302e-05 | 3.984e-05 |
| 700 | `700-r1005` | `700re17.C` | `700re17.F1`, `700h17.F1` | 6, 4 | +0.000183 | -0.000393 | 1.485e-05 | 1.485e-05 |
| 598 | `598-v3018` | `598mo17.C` | `756h09.F2`, `649fa16a.F1d` | 7, 5 | +0.000064 | -0.000286 | 1.168e-05 | 1.168e-05 |
| 378 | `378-v4102` | `378cl17.C` | `378h12.F1`, `599h.F1` | 7, 3 | +0.000618 | -0.000001 | 3.928e-08 | 3.423e-09 |

Each of these wins uses the corner of a layout made in this round. `813mi17.C` is the corner of the midm lane's 813. `815st17.C` is the corner of the stair-c lane's 815. `700re17.C` is the corner of the readers lane's 700, one shell up from the held 647. `598mo17.C` is the corner of our own 598, which came from `700re17.C`. `378cl17.C` is the corner of the classfill lane's 378. On the corners of new layouts, the squeeze takes much more off the start than on the older corners:

| corner | builds | median of built - predicted | lowest |
|---|---|---|---|
| `815st17.C` | 37 | -0.000855 | -0.005685 |
| `700re17.C` | 26 | -0.002094 | -0.005142 |
| `378mi17.C` | 19 | -0.001374 | -0.002376 |
| `549mo17.C` | 10 | -0.000855 | -0.004105 |
| `812fa17.C` | 3 | -0.006834 | -0.007250 |
| `813mi17.C` | 33 | -0.004874 | -0.008694 |
| every other corner | 310 | -0.000499 | -0.008362 |

So the prediction ranks these corners too low. The first rows of `700re17.C` were 9e-4 to 1.9e-3 above held, and the rows of `815st17.C` on 703 were 4e-3 above. The lists of rounds 13 to 16 stopped at 1e-3. We widened the search to 1.2e-2 for the corners of round 17 (lists `rf`, `wd`, `we`) and to 8e-3 for every corner of rounds 16 and 17 (`x6`). `tools/offset17.py` now moves each row by the median of `built - predicted` of its corner, once the corner has 3 builds. Ranked that way at 18:45 UTC, the best rows not built yet were the `v2` rows of 505 and 700. At 19:12 UTC the `o9` list took the best 13 rows of that ranking outside the slices of other lanes. None ended below held: on 758 and 418 they ended at the sides of earlier builds.

### X5. One corner on one n ends at one side

`813mi17.C`, the corner of the midm lane's 813, gave the largest win. Its first row on 754 was 3.65e-3 above held, and the build ended 3.29e-3 below held. We then built the same corner on 754 again. Each build took other far zones or a pair of stacks not built yet. The queue lists 25 pairs on 754 (`qz/q-754.tsv`).

| side minus held | builds | spread | stacks | far zones |
|---|---|---|---|---|
| -3.3976e-03 | 2 | 5.5e-10 | 9/6, 9/7 | `700h17.F1`, `700so16.F1`, `z8-44f950.F1` |
| -3.2918e-03 | 4 | 2.3e-08 | 7/6, 7/7, 8/6, 8/7 | `700h17.F2d`, `700mo16.F1`, `700mo16.F2`, `700so16.F2d` |
| -1.1636e-03 | 2 | 7.1e-15 | 7/8, 8/8 | `700mo16.F1`, `700mo16.F2`, `z8-44f950.F1` |
| -1.0569e-03 | 1 | 0.0e+00 | 9/8 | `z8-44f950.F1` |
| +3.2343e-03 | 3 | 3.8e-09 | 6/6, 6/7, 6/8 | `700mo16.F1`, `700mo16.F2`, `995re16.F2`, `z8-44f950.F1` |
| +3.2353e-03 | 1 | 0.0e+00 | 5/7 | `700mo16.F2`, `932h13.F2d` |
| +6.2035e-03 | 1 | 0.0e+00 | 9/5 | `995re16.F2`, `z8-44f950.F1` |
| +6.2052e-03 | 1 | 0.0e+00 | 9/4 | `932h13.F2d`, `z8-44f950.F1` |
| +6.9362e-03 | 1 | 0.0e+00 | 8/5 | `995re16.F2`, `995z11.F2` |

So the builds of one corner on one n end at a few sides, and the stacks pick the side more than the far zones do. Stacks 9 and 6 or 9 and 7 end lowest, 1.06e-4 of side below the first win, and the gain on 754 went from 1.199e-4 to 1.237e-4. A second stack of 8 ends about 2.2e-3 higher. A first stack of 5 or 6, or a second stack of 4 or 5, ends above held. On 756, seven builds of the same corner with other far zones and stacks all ended 1.6e-5 to 9.3e-5 above held. So a second build of a corner on one n pays only with another pair of stacks.

### X6. Builds

| list | choices | n | below held | kept |
|---|---|---|---|---|
| g1 corners alone, top 12 per n (the round 16 held file, the twoshort, classfill and midm takes) | 17 | 4 | 7 | 0 |
| g1: the generator over every n with the 90 new modules and twins, checked | 31 | 14 | 0 | 0 |
| g1: the rest of part 2, unchecked | 3 | 1 | 0 | 0 |
| checked rows of rounds 13 to 16, 3e-4 to 1e-3 above the bar, fewest builds first | 111 | 17 | 2 | 0 |
| every corner of rounds 16 and 17 alone, top 12 per n | 11 | 2 | 0 | 0 |
| growth of the round 17 takes | 12 | 4 | 3 | 0 |
| g1: every row of the g1 searches up to 2e-3 above the bar, not listed before | 18 | 8 | 1 | 0 |
| growth r1 (catch-up after the 16:15 UTC panic) | 16 | 6 | 7 | 1 |
| the corners of round 17 alone over every n, up to 4e-3 above the bar | 29 | 9 | 5 | 0 |
| growth v1 to v5 of the round 17 takes (after 17:50 UTC) | 62 | 15 | 28 | 2 |
| the corners of round 17 over every n, up to 6e-3 above the bar | 27 | 5 | 8 | 1 |
| corners 700re17, 815st17 and 549mo17 over every n, up to 1.2e-2 above the bar | 22 | 7 | 0 | 0 |
| family corners 812fa17, 812fa17a and 419fa17 on 378, 701 and 756, up to 9e-3 above the bar | 6 | 3 | 0 | 0 |
| every corner of rounds 16 and 17 over every n, up to 8e-3 above the bar, 3 per n | 20 | 17 | 4 | 0 |
| corners 813mi17, 812fa17a and 815st17 with other far zones and stacks on 460, 648, 701, 703, 754, 755, 756 and 758 | 27 | 8 | 4 | 0 |
| corner 813mi17 on 754, one row per pair of stacks not built yet | 12 | 1 | 5 | 1 |
| rows of every list ranked by the median built - predicted of their corner (tools/offset17.py), up to 4 per n | 13 | 7 | 0 | 0 |

### X7. What to run next

1. On every n where a new corner builds below held, build one row for each pair of stacks that the queue lists. On 754 the rows with stacks 9 and 6 or 9 and 7 ended 1.06e-4 of side below the first win. Rows with other far zones and the same stacks end at the same side to 2.3e-8, so skip them.
2. Learn the offset of each new corner from its first 3 builds, and rank every row with it (`tools/offset17.py`). In the median the corners of new layouts build 8.6e-4 (`815st17.C`) to 4.9e-3 (`813mi17.C`) below their prediction, and `813mi17.C` built 6.9e-3 below it on 754. Older corners build 5e-4 below.
3. Find why these corners build so far below their prediction. Compare the table of `813mi17.C` at the predicted f with the corner that the squeeze leaves on 754. If the cut leaves slack in the corner, a squeeze of the corner alone before it goes into a table fixes the prediction on every n.
4. Keep the growth loop, but rank its rows with the offsets of item 2. The steps after 18:30 UTC (`v2` to `v5`) gave 42 builds. 27 ended below held, mostly at sides that the corner lists had reached first.
5. A zone for the outer L of a shell (W4) is still not started.

## Round 9 (2026-11-12, round 19)

**Result: 6 n certify below the round 17 file and below every other take of rounds 17 and 19: 378, 503, 550, 587, 975 and 996. They give 3.724e-5 of score against the round 17 file and 3.707e-5 over the other takes. 975 and 996 give 2.84e-5 of it. Our 754 (1.498e-4) and 554 (8.360e-5) certified here first, and then two other lanes took our files lower. So these two n are in the takes of those lanes.**

Words used here: "held" is now `gather/round17-2026-11-12a.csv` (22.1635211736, gate dir `gate/cand-round17-1112a`). "The bar" of an n is the smallest of its held side and its side in every `take-*-r17` dir and every other live `take-*-r19` dir. A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r19`. The library of this round starts from `lib17` of round 17 (`work/lib19`).

### Y1. Why new corners build far below their prediction

A corner table was made with frozen angles. At each step of f, only the squares at the tilt of an arm turned with the arm. The LP moved every other square of the corner without turning it (`corner_len` called `settle`). A far zone table lets its squares turn (`far_len` calls `relax`). So a corner carried away from the f it was found at kept angles that fit only its own f.

We compared the table of `813mi17.C` with the corner that the squeeze left in the 754 build of round 17 (`754-t9003`, stacks 9 and 6). A build keeps the squares in the order of its start: corner, stacks, far zones, rest. So each part of the built layout can be measured (`work/tools/diag2.py`).

| at the built f = 0.901143 | y0 | x0 |
|---|---|---|
| frozen table of `813mi17.C` | 12.2409 | 13.3277 |
| turned table (`813mi17.Ct`, below) | 12.2221 | 13.2796 |
| the corner in the built 754 | 12.1892 | 13.2841 |

The built corner is 0.05 shorter on both lengths than the frozen table. Its squares turned by 0.75 degrees in the mean and by 6.5 degrees at most. The corner had slack at its own f too: there the turned table is 0.018 shorter in y0 than the corner as it was cut.

The fix is a turned twin of a corner. It is the same corner with id + `t` and the field `turn`, and `corner_len` then calls `relax` at every step (`modules.py`, `work/tools/turnify.py`). A turned twin is still an upper bound: each state is checked legal, and a build starts from the same states, because `corner_at` walks the same steps. A table takes 10 to 220 s (median 57 s) on one process of boxD. Over 141 corners, the turned table is shorter than the frozen one by a median of 0.018 in y0 and 0.028 in x0. It is shorter by more than 0.01 on one length or both for 127 of them.

The control: the turned table must predict the built side within 1e-3.

| build | start | turned prediction | built | built - prediction |
|---|---|---|---|---|
| `754-t000` | turned | 27.900472 | 27.900427 | -4.5e-5 |
| `648-t010` | turned | 25.904343 | 25.904066 | -2.8e-4 |
| `701-t014` | turned | 26.913786 | 26.913373 | -4.1e-4 |
| `756-t004` | turned | 27.922254 | 27.921472 | -7.8e-4 |
| `700-r1005` (round 17) | frozen | 26.898408 | 26.897979 | -4.3e-4 |
| `703-rf071` (round 17) | frozen | 26.946163 | 26.944107 | -2.1e-3 |
| `754-t9003` (round 17) | frozen | 27.907929 | 27.901143 | -6.8e-3 |

It passes on every build that starts from the turned table. 99 builds of this round start from a turned table. They end between 7.8e-4 below and 1.8e-4 above their prediction, and 2.1e-4 below in the median. Three of them end above it: there the squeeze stopped above the predicted side. It misses on two of the three frozen builds of round 17. There the fq of the squeeze found a lower layout than the start, with arms off the flush line. In `754-t9003` the stacks of arm 1 stand 0.3 degrees steeper than flush and 9e-3 off their wall. So the frozen offsets of round 17 (`tools/offset17.py`) measured the gap between the frozen table and the corner, plus such jumps of the fq.

The turned table also finds new layouts. On 754, `813mi17.Ct` predicts 27.900472, and that is below the 754 of round 17 (27.901143). The frozen rows of the same corner on 754 all start near 27.9098. The build of the turned row ended at 27.900427.

### Y2. Builds

The lane had 2 processes on boxD and 1 on boxA. On boxD one slot made the turned tables and one built rows. Each batch of turned twins went over every n at once (`modules.py queue --need`, top 3 per n, about 2 minutes). Its rows went to the head of the build list. A turned row is ranked by its own prediction (offset 0). A frozen row keeps the offset of its corner (`work/tools/rank19.py`).

| list | what | builds | n | below held | below the bar | kept |
|---|---|---|---|---|---|---|
| `a` | every n, the 132 corners of round 17, frozen, ranked by the corner offset | 2 | 1 | 0 | 0 | none |
| `p` | one row per stacks pair on the 14 n where a corner of round 17 built within 1e-3 of the bar, frozen | 8 | 1 | 0 | 0 | none |
| `t` | turned `813mi17.Ct`, `815st17.Ct`, `700re17.Ct` on 8 n | 9 | 7 | 4 | 0 | none |
| `c` | turned twins, batch c (7 corners) | 2 | 2 | 1 | 0 | none |
| `d` | turned twins, batch d (7 corners) | 23 | 12 | 8 | 0 | none |
| `e` | turned twins, batch e (20 corners) | 26 | 11 | 18 | 3 | 503, 550 |
| `f` | turned twins, batch f (24 corners) | 9 | 6 | 7 | 1 | 587 (quenched) |
| `tg` | turned twins, batch g (22 corners) | 11 | 6 | 3 | 2 | 975 |
| `th` | turned twins of 16 held corners of rounds 14 to 17 | 4 | 2 | 2 | 2 | 996 |
| `w` | deeper rows of the turned corners that won on 503 and 550 | 8 | 2 | 4 | 2 | 503, 550 |
| `g` | the growth loop on boxA (steps g1 to g6) | 24 (5 no start) | 11 | 19 | 3 | 378, 550 |

The certified layouts:

| n | build | corner | far zones | stacks | prediction - bar | built - bar | gain on held | gain over the other takes |
|---|---|---|---|---|---|---|---|---|
| 378 | `378-g1000` | `378mo17.C` | `378h12.F1`, `419fa17.F2` | 7, 2 | +3.97e-04 | -1.53e-08 | 1.115e-08 | 7.375e-10 |
| 503 | `503-w004` | `550f10.Ct` | `599h.F1`, `598h13.F2` | 6, 6 | +2.63e-04 | -1.46e-05 | 6.504e-07 | 6.504e-07 |
| 550 | `550-g4003` | `550mo19.C` | `549mo17.F1d`, `419fa17.F2` | 9, 6 | -1.18e-04 | -1.91e-04 | 8.135e-06 | 8.135e-06 |
| 587 | `587-f004` | `587st17.Ct` | `495h11.F1`, `587st17a.F2d` | 5, 5 | +1.97e-04 | -6.62e-08 | 5.559e-09 | 5.559e-09 |
| 975 | `975-tg000` | `910co17.Ct` | `z9-19f720.F1`, `z9-46f740.F1` | 17, 8 | -1.59e-04 | -4.73e-04 | 1.530e-05 | 1.515e-05 |
| 996 | `996-th000` | `932h14.Ct` | `758h.F1`, `996m10.F2` | 12, 16 | -1.87e-05 | -4.15e-04 | 1.314e-05 | 1.314e-05 |

- 754 and 975 come from rows that the frozen tables put far above the bar. On 754 the frozen rows of `813mi17.C` start near 27.9098 and the turned rows at 27.9005. On 975 the turned twin of the twoshort lane's 910 corner predicted 1.6e-4 below the bar.
- Our 754 (`754-t000`) certified 1.498e-4 of score below held. The midm lane then took our file through its fq kick and quench, 7.0e-6 of score lower again. So 754 is in the take of the midm lane, not in ours.
- 996 came from the turned twin of a held corner of round 14 (`932h14.Ct`), predicted 1.9e-5 below the bar. The last batch of turned twins (`th`) covered 16 corners of the held file from rounds 14 to 17.
- 554 came from the turned twin of the corners lane's 419 corner, predicted 1.46e-3 below the bar. The growth loop then cut our own 554 and rebuilt it with that layout's turned corner, 2.7e-4 of side lower again (`554-g3001`). The classfill lane certified the same layout 2.3e-10 of score lower at 21:42 UTC, so 554 is not in our take.
- Rows of the frozen lists ranked by the offset of round 17 gave nothing: 756 ended 1.6e-5 above the bar, and 931 8.0e-5 above it.
- Every certified n went through the fq quench of the polish lane (`zone_corner.py quench`) on boxD. It found 7e-8 of side on 587 and nothing on the others. On 996 it found nothing (79 s).

### Y3. Growth loop

`work/tools/growloop19b.sh` ran on boxA in its one slot. Each step cut every new layout of the `take-*-r17` and `take-*-r19` dirs into `lib19` and made the frozen and the turned tables of the new modules. Then it ran the generator over every n with the new corners as the list to hold, and built the best 4 rows. Rows near the bar are rows ranked within 2e-4 of it. Below the bar means more than 1e-10 of score below it.

| step | UTC | new modules | rows | rows near the bar | built | no start | below held | below the bar |
|---|---|---|---|---|---|---|---|---|
| `g1` | 20:51 | 20 | 126 | 8 | 4 | 0 | 4 | 378 |
| `g2` | 21:05 | 12 | 246 | 90 | 4 | 4 | 0 | none |
| `g3` | 21:27 | 25 | 193 | 12 | 4 | 0 | 4 | none |
| `g4` | 21:41 | 24 | 217 | 12 | 4 | 0 | 4 | 550 |
| `g5` | 21:55 | 24 | 111 | 14 | 4 | 1 | 3 | none |
| `g6` | 22:12 | 29 | 158 | 27 | 4 | 0 | 4 | none |

A turned table can hold a state that no build reaches. `549mi19.Ct` predicted rows 0.038 below the bar on 464, 508 and 935, and none of them had a start: the corner did not fit under both arms. The build checks every start, so such a row costs a few seconds.

### Y4. Outer L of a shell

Not started. The slots of this round went to the turned twins and their builds.

### Y5. What to run next

1. Make the turned twin of every corner in the library, the old corners too. This round tabulated 141 corners. 6 rows on 3 n were predicted below the bar of the end of the round (550, 975, 996), and every one of them built below it. Rows of 554 and 754 were below the bar when they were built. Then two other lanes polished our own layouts of these n, and that moved the bar. One table takes about a minute on one process.
2. Rank turned rows by their own prediction. A turned row ends between 7.8e-4 below and 1.8e-4 above it. Drop the offsets of round 17 for turned rows. They held the jumps of the fq from frozen starts.
3. Run the growth loop on our own new layouts at once. A new layout that we cut and rebuild with its turned corner can go lower again: 554 went 2.7e-4 of side lower in one step. A layout that has the same side as a layout in the library is not cut again, so a layout another lane polished by 1e-13 blocks the step.
4. The outer L of a shell (round 16 W4) is still not started.

## Round 10 (2026-11-13, round 20)

**Result: 4 n certify below the round 18 file and below every other take of rounds 19 and 20: 649, 756, 862 and 996. They give 1.262e-4 of score against the round 18 file and 9.68e-5 over the other takes. Three more n certified here first and then went lower in other lanes: 810 (1.094e-4), 869 (4.706e-5) and 549 (4.529e-5). Every n of the take came from the growth loop. It cut the new layouts of other lanes and of our own into modules and made their turned twins.****

Words used here: "held" is now `gather/round18-2026-11-12a.csv` (22.1604820601, gate dir `gate/cand-round18-1112a`). "The bar" of an n is the smallest of its held side and its side in every frozen `take-*-r19` dir and every other live `take-*-r20` dir. A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r20`. The library of this round is `lib19` of round 19 with the turned twins of boxD added (`work/lib20`, 141 turned corners at the start).

The lane had 2 processes on boxD and 1 on boxA. A reboot of boxA at about 22:48 UTC killed the first run of this round after 12 minutes. The run that followed read `STATE.txt`. It kept the scan that still ran on boxD and started the growth loop again from its cut.

### Z1. Which corners to turn first

Round 19 made turned tables for 141 corners. The library holds 968 more corners (base corners and slid twins, without the grant variants). A turned table takes about a minute, so the lane cannot turn them all in one round. We ranked them first.

`work/tools/shiftq.py` lowers both lengths of every corner that has no turned twin by a fixed shift, at every state. Then it runs the generator over every n, as `modules.py queue` does, with these corners as the list to hold. The shift is dy = 0.03 and dx = 0.04. That is about the 25th percentile of what a turned table took off a frozen one in round 19 (the median was 0.018 and 0.028). A shifted row is a rank, not a prediction.

The control: four corners whose turned twins won in round 19, against the bar of round 19.

| n | corner | frozen row - bar | shifted row - bar |
|---|---|---|---|
| 754 | `813mi17.C` | +7.1e-3 | +3.7e-4 |
| 996 | `932h14.C` | +1.6e-2 | +1.2e-3 |
| 503 | `550f10.C` | +5.1e-3 | +1.5e-3 |
| 975 | `910co17.C` | none within 2e-2 | +1.3e-2 |

The shift moves each row toward the bar, but it takes none of the four below it. A turned table can be 0.05 shorter than the frozen one, and the shift is only 0.03 and 0.04. So the turn list keeps every corner with a shifted row up to 0.015 above the bar. The scan ran over 414 n on 3 processes in 17 minutes. 160 corners have a shifted row within 0.015 of the bar, and 104 of them have one below it. `work/tools/turnrank.py` orders them by their lowest shifted row.

### Z2. Workers on boxD

`work/tools/worker20b.py` runs in 2 slots. Each turn of a slot does the first of these that has work:

1. The fq quench of a certified layout (`quench.todo`, `zone_corner.py quench`).
2. The rest of a batch whose driver died (its table file is there, its queue is not).
3. A search over every n for the corners of `wide.todo`.
4. The build of the best turned row whose prediction is less than 3e-4 of side above the bar.
5. The build of the next growth row of `glist.txt` (Z3), from a copy of `lib20`.
6. The turned twins of the next 4 corners of the turn list. The generator then runs with them as the list to hold, on the n where the scan put their frozen rows (top 3, slack 4e-3).

A slot starts a process only while fewer than 2 processes of the lane run. So a driver can be replaced while its child runs, and the lane stays at its budget. We added three rules during the round, each from a measure:

- A row on the n its corner was cut from gets 3e-4 added. The first rows of 340, 418 and 652 rebuilt the held layout of their own n to 1e-9.
- A corner with 2 builds above the bar on one n gets no more builds there. Three stacks pairs of `418h.Ct` on 418 ended at the same side.
- A corner with 2 builds that had no start, and none that had one, gets no more builds.

This round made 159 turned tables, 120 of them by the workers from the turn list (ranks 1 to 120). The turned table is shorter than the frozen one by a median of 0.009 in y0 and 0.023 in x0. It is shorter by more than 0.01 on one length or both for 128 of them. A table took 40 s in the median. Of the 104 corners with a shifted row below the bar, 67 had a turned row within 4e-3 of the bar. Only 2 had one below it. Of the 16 corners with a shifted row above the bar, 1 had a turned row within 4e-3 and none below.

The turned twins of the scan gave one certified n. On 810 the turned twin of `zc8x8-153f9165ar.C` (stacks 6 and 8) was predicted 1.5e-3 of side below the bar and built 1.6e-3 below it. It certified at 1.094e-4 of score against held and 5.76e-5 over the other takes. Then the polish lane quenched our file 6.7e-10 lower, and the classfill lane swept its far zone `F2` (0.159 squares less loss) and took 810 lower again. The search of this corner over every n found rows only on 810. Of the other 103 turned corners, the rows near the bar rebuilt held layouts or ended above the bar.

Builds by list at the end of the round. Below the bar means below every other take at 00:56 UTC by more than 3e-10 of score, because floatsafe moves a file by about 1e-10. So 810, 869 and 549 no longer count.

| list | builds | no start | below held | below the bar now | n below the bar now |
|---|---|---|---|---|---|
| turned twins ranked by the scan (boxD) | 56 | 6 | 13 | 0 | none |
| growth rows built on boxD | 43 | 0 | 34 | 5 | 649, 862 |
| growth loop (boxA) | 59 | 18 | 39 | 13 | 649, 756, 862, 996 |

### Z3. Growth loop

The growth loop ran on boxA in its one slot (`work/tools/growloop20b.sh` to `growloop20e.sh`). Each step cuts every new layout of the frozen `take-*-r19` dirs and of the live `take-*-r20` dirs into `lib20`, ours too. It makes the frozen and the turned tables of the new modules and runs the generator over every n with the new modules as the list to hold. Then it ranks the rows of every step so far (`work/tools/rank20.py`) and builds the best 4 rows that have a start. A step with nothing new to cut builds the next 2 rows instead (`growloop20e.sh`).

Rows near the bar are rows ranked within 2e-4 of it. Steps `h9`, `h10` and `h12` to `h18` had nothing new to cut and built rows up to 1e-3 above the bar.

| step | UTC | new modules | rows | rows near the bar | built | no start | below held | below the bar now |
|---|---|---|---|---|---|---|---|---|
| `h1` | 23:04 | 29 | 340 | 117 | 2 | 2 | 0 | none |
| `h2` | 23:12 | 11 | 106 | 15 | 4 | 0 | 4 | 862 |
| `h3` | 23:29 | 21 | 294 | 107 | 16 | 16 | 0 | none |
| `h4` | 23:44 | 17 | 123 | 25 | 4 | 0 | 4 | 996 |
| `h5` | 23:52 | 6 | 120 | 24 | 4 | 0 | 4 | 996 |
| `h6` | 00:02 | 9 | 135 | 26 | 4 | 0 | 4 | none |
| `h7` | 00:09 | 3 | 24 | 15 | 4 | 0 | 4 | 996 |
| `h8` | 00:15 | 6 | 123 | 8 | 4 | 0 | 4 | 996 |
| `h11` | 00:29 | 6 | 78 | 5 | 4 | 0 | 4 | none |

The loop builds 4 rows per step, and from step `h4` on most of its rows were near the bar. So from 00:01 UTC the workers of boxD also built growth rows from a copy of `lib20` (`glist.txt`). First they built the rows ranked 5 to 23 within 2e-4 of the bar. Then they built the rows up to 6e-4 above it. 649 and 549 came from that second list. The 649 row was predicted 3.9e-4 of side above the bar of the end and built 1.9e-4 below it.

Two turned twins predicted rows 0.038 below the bar on many n, and none of these rows had a start. They are `803fa19.Ct` (57 n in step `h1`) and `803in20.Ct` (47 n in step `h3`, 16 builds without a start). The build says that the corner does not fit under both arms. Since `rank20.py`, a corner with 2 builds that had no start and none that had one is dropped from the list and from the build loop. The slid twin of the same 803 corner (`803fa19.C~`, frozen) gave the 862 of this round.

### Z4. Certified layouts

The bar is the one at the end of the round.

| n | build | corner | far zones | stacks | prediction - bar | built - bar | gain on held | gain over the other takes |
|---|---|---|---|---|---|---|---|---|
| 649 | `649-H011` | `598co20.Ct` | `503h.F2`, `550mo19.F1` | 8, 8 | +3.94e-04 | -1.92e-04 | 9.107e-06 | 7.549e-06 |
| 756 | `756-h18000` | `996cl20.Ct` | `755h.F2`, `755h.F2d` | 7, 6 | +6.32e-04 | -3.67e-04 | 1.336e-05 | 1.336e-05 |
| 862 | `862-H009` | `862mo20.C` | `982cl17.F2d`, `921h13.F2` | 11, 9 | -2.07e-04 | -9.57e-04 | 4.725e-05 | 3.261e-05 |
| 996 | `996-h8000` | `996mo20a.Ct` | `814h09.F1`, `814h09.F1` | 16, 14 | -1.63e-03 | -1.37e-03 | 5.644e-05 | 4.330e-05 |

- Every n of the take uses a corner cut in this round from a layout of another lane or of our own. 649 uses `598co20.Ct` of the corners lane's 598, and 756 uses `996cl20.Ct` of the classfill lane's 996. 862 uses `862mo20.C` of our own 862, which came from `803fa19.C~` of the family lane's 803. 996 uses `996mo20a.Ct` of our own 996.
- 996 went lower twice. `601mi20.Ct` built it 1.4e-3 of side below the bar (step `h5`). The loop then cut our own 996 into `996mo20.C`, and its turned twin rebuilt it 7.5e-6 of side lower (step `h7`). Step `h8` cut that layout again (`996mo20a.C`) and its turned twin ended at the same side.
- 869 certified twice (steps `h4` and `h5`, the turned twin of the corners lane's 993 corner with the far zone of the classfill lane's 870). The stair-c lane then took 869 lower.
- Every certified layout went once through the fq quench of the polish lane (`zone_corner.py quench`) on boxD. It took 1.9e-8 of side off 810 and 3.9e-6 off the first 869 (step `h4`). It found nothing on 862 (two builds), the second 869, 996 (three builds), 549 (two builds), 649 and 756.

### Z5. What to run next

1. Give the growth rows more build slots, at once. Every n of the take came from growth rows. 13 of 59 builds of the loop and 5 of 43 growth rows built on boxD ended below the bar of the end. None of the 56 builds from the turn list did. The loop built only 4 rows per step. Rows ranked up to 6e-4 above the bar still won (649, 756).
2. Keep the cut and the turned twins of the new layouts of other lanes in their own slot. The modules of the wins were cut in this round from layouts of the corners, classfill, midm and family lanes and of our own takes (`598co20.Ct`, `996cl20.Ct`, `993co20.Ct`, `601mi20.Ct`, `803fa19.C~`). Our own 996 went lower twice when the loop cut it again.
3. Find why some turned tables hold states that no build reaches. `803fa19.Ct` and `803in20.Ct` predicted rows 0.038 below the bar on about 50 n each, and every build had no start. A check of each table state with `assemble` would drop such a corner before it fills a list.
4. The rest of the turn list is low. 120 corners turned by the rank of the scan gave one n (810), and other lanes then took it lower.
5. The outer L of a shell (round 16 W4) is still not started.

## Round 11 (2026-11-13, round 21)

**Result: 1 n certifies below the round 19 file and below every other take at 12:11 UTC: 978, for 1.008e-7 of score. Five more n certified here first: 931 (9.309e-5 on held), 875 (4.986e-5), 994 (4.369e-5), 813 (4.66e-6) and 976 (6.5e-9). Other lanes then took them lower, four of them within 40 minutes by a kick or a quench of our own file. Each of the five came from a corner that the growth loop cut in this round from a new layout of another lane. The merge counts those n in the takes of the classfill, polish, family and midm lanes.**

Words used here: "held" is now `gather/round19-2026-11-12a.csv` (22.1514697138, gate dir `gate/cand-round19-1112a`). "The bar" of an n is the smallest of its held side and its side in every frozen `take-*-r20` dir and every other live `take-*-r21` dir. A build is kept only when it certifies below the bar by more than 1e-10 of score. The take is in `<scratch>/bounties-squares/take-modules-r21`. The library is `work/lib21`. It starts as `lib20` with every growth step of round 20 and the turned twins of boxD: 467 layouts, 10,110 modules and 300 turned corners.

The lane had 2 processes on boxD and 1 on boxA. The round ran in three parts. The first run started at 01:03 UTC and stopped at about 01:20 UTC on a usage limit. Its jobs went on under nohup to their deadline of 03:25 UTC. boxA rebooted at 05:36 UTC. A second run started the same jobs again at 09:52 UTC and stopped at 09:55 UTC on a lost login. A third run adopted these jobs at 09:59 UTC and ran them to 12:10 UTC.

### AA1. Two faults of the loop left build slots idle

`work/tools/rank21.py` ranks the rows of every growth step and writes `glist.txt`. The build slots take their rows from that list. The growth loop also passes it the queues of boxD as `boxD-tq/q-*.tsv`. That folder held no queue. In `sh` a glob that matches nothing stays as it is. So the ranker got the literal name, could not open it and stopped. Every rank of the loop failed from 01:20 UTC on, and `glist.txt` kept its first list of 101 rows. The two slots of boxD built those rows by 02:20 UTC. Then they had nothing to build until their deadline at 03:24 UTC. The rows of the 8 growth steps of the first run never reached a list. The second run found the crash at 09:54 UTC. The ranker now skips a queue file that is not there, and the rank that followed gave 69 build lines on 57 n.

The second fault keeps the slot of boxA from building. The loop reads `glist.txt` line by line and claims a row over `ssh`. Without `-n`, `ssh` reads the rest of the list from standard input. So when the first free row is already claimed on boxD, the loop sees the end of the list and builds nothing. The slot of boxA built no row in the first run, and one row from 09:52 to 11:52 UTC. In the last 16 minutes there was no cut to make and no slot of boxD claimed rows, and it built 9. The fix is `ssh -n`. We did not make it during the round: a restart of the loop in the middle of a step loses the tables of that step.

### AA2. Growth steps

Each step cuts the new layouts of every take dir and of the near folders of other lanes. It makes the tables and the turned twins of the new modules. Then it runs the generator over every n with them as the list to hold. Rows are the rows of the generator. The cut tags name the lane and the round (`nf21` is the near folder of the family lane in round 21).

| step | UTC | layouts cut | new modules | turned twins | rows |
|---|---|---|---|---|---|
| `i1` | 01:40 | cl20, re20, 3 nc20, 2 ns20 | 23 | 8 | 558 |
| `i2` | 01:58 | fa21, 4 nf21 | 16 | 6 | 288 |
| `i3` | 02:02 | mo21 | 3 | 1 | 352 |
| `i11` | 02:10 | mo21 | 3 | 1 | 348 |
| `i28` | 02:37 | fa21 | 3 | 1 | 252 |
| `i43` | 02:51 | mi21 | 3 | 1 | 352 |
| `i46` | 02:55 | re21 | 5 | 2 | 71 |
| `i51` | 03:02 | nf21 | 5 | 2 | 68 |
| `i52` | 09:57 | st21 | 5 | 2 | 65 |
| `i53` | 10:30 | fa21, fo21, 4 nc21 | 19 | 7 | 331 |
| `i54` | 11:08 | 2 cl21, co21, 2 fa21, po21, nc21, 3 nf21, ns21 | 46 | 18 | 446 |
| `i55` | 11:24 | cl21, co21, nf21, nr21, ns21 | 23 | 9 | 258 |
| `i56` | 11:52 | 2 cl21, fa21, mo21, po21 | 22 | 10 | 395 |

The generator is slow on boxA when the box is loaded. At a load of 20 it took 33 minutes over 414 n for the 26 new modules of step `i53`. The slot builds nothing in that time, and the layouts of other lanes wait for the next step.

### AA3. Certified here, then lower in other lanes

Five n certified here during the round and then went lower in another lane. Four of them went lower within 40 minutes, by a kick or a quench of our own file.

| n | certified here (UTC) | corner of our build | gain on held | taken lower by | how |
|---|---|---|---|---|---|
| 813 | 01:59 | `754co20.Ct` | 4.66e-6 | family, 02:23 | a shell walk |
| 976 | 01:59 | `976tw17a.Ct` | 6.5e-9 | midm, 02:48 | a kick of our file |
| 994 | 10:00 | `931st21.C` | 4.369e-5 | classfill, 10:25 | a kick of its own build on the same stair-c corner |
| 931 | 11:21 | `931po21.C~` | 9.309e-5 | polish, by 11:27 | the fq quench of our file, 1.8e-10 of score |
| 875 | 11:21 | `936nf21.Ct` | 4.986e-5 | classfill, 11:39 | a kick of our file, 2.43e-4 of side |

The 994 came from step `i52`, which cut the 931 of the stair-c lane at 09:57 UTC. That layout has two 9-arms and the hopped 122-square class 5 corner of the stair-c lane at f 0.928 (`zc9x9-122f9280af928h2.C`). Its corner `931st21.C` had 3 rows on 994, predicted 9.8e-4 of side below the bar. The first of them ended 1.275e-3 below the bar at 10:00 UTC, 3 minutes after the cut. Its far zones come from a near layout of 931 of the family lane (`931nf21a.F2`) and from the 994 of the readers lane (`994re21.F2`). The fq quench on boxD found nothing on it. All 8 of our builds of 994 on `931st21.C`, on `931fa21.C` (the 931 of the family lane, step `i53`) and on the hopped corners of AA4 ended between 31.928461 and 31.928644. Other far zones and stacks reach the same layout, and a kick is what goes lower.

The 875 came from step `i54`. The family lane walked the 875 of the corners lane up to 936 and wrote that layout to its near folder. The loop cut it (`936nf21.C`) and made its turned twin. Its row on 875 ranked 2.3e-4 of side below the bar and was built 2 minutes after the rank. With the far zones `875m10.F1` and `874h14.F1` it ended 1.06e-4 of side below the bar of 11:11 UTC. The other two stacks of the same row rebuilt the 875 of the corners lane to 2e-9.

The 931 came from the slid twin of the corner of the polish lane's 931 (`931po21.C~`) with its own far zone. It ended 3.3e-5 of side below the 931 of the readers lane. Our quench found 5.4e-9 of side on it, the same as the polish lane.

At 11:53 UTC we stopped the two build slots of boxD. Two kick scans of our own builds took their place to 12:10 UTC (`work/kick21.sh`, `midm_scan.py` with kick and lkick at sigma 0.02). The classfill lane had measured 1.5e-5 to 2.4e-4 of side with this scan on 4 of 4 fresh builds of ours. The scan of our 931 build `931-gf65b0e2` made 17 tries. That build was 1.7e-5 of side above the polish 931. The scan of `994-g4b66363` (1.1e-4 above the classfill 994) made 13. Neither found a layout below its start. A try took 50 to 90 s on these n, so 15 minutes is too short for this scan.

### AA4. The hopped corners of stair-c

At 10:23 UTC the stair-c lane handed over a library with 4 hopped states of its class 5 corner at f 0.93 (`zc9x9-122f9300af93h5.C` to `df93h5.C`). They are not cut from any layout, so the loop cannot reach them. `work/f93h5.sh` added them to the library of boxD, made their turned twins and ran the generator over every n with the 8 corners as the list to hold. The generator took 5 s, because two 9-arms at f 0.93 fit few n. It gave 66 rows. The best are on 931 (5.7e-4 of side above the bar), 703 (5.8e-4) and 994 (8.0e-4). We built 5 of these rows. The 2 on 931 ended 1.6e-4 of side above the bar of the end. The 3 on 994 ended at 31.928462 and 31.928644, the layout of the cut corners (AA3).

### AA5. Rows on n whose builds end at the bar

The list of 10:31 UTC began with rows on 754 that the ranker put 1.4e-4 above the bar. Six builds of four corners on 754 all ended at the bar to 1e-8. 975 (5 builds), 703 (3) and 505 (3) did the same: each build rebuilt the layout of the bar. `rank21.py` now drops the rows of an n with 3 or more builds at the bar, unless the row ranks 1e-4 or more below it. On the list of 10:52 UTC this dropped 366 rows, and the list went from 47 to 40 lines.

### AA6. Builds

| part | list | builds | no start | below held | below the bar now | n below the bar now |
|---|---|---|---|---|---|---|
| first run (01:16 to 03:24) | rows of the round 20 queues (boxD) | 94 | 0 | 18 | 2 | 978 |
| third run (09:52 to 12:10) | growth loop (boxA) | 10 | 1 | 9 | 0 | none |
| third run (09:52 to 12:10) | growth rows (boxD) | 151 | 1 | 67 | 0 | none |
| third run (09:52 to 12:10) | stair-c hopped corners (boxD) | 5 | 0 | 5 | 0 | none |

"Below the bar now" means below every other take at 12:11 UTC by more than 3e-10 of score. The first run built only rows of the queues of round 20, because the ranker crashed (AA1).

### AA7. Certified layouts

| n | build | corner | far zones | stacks | prediction - bar | built - bar | gain on held | gain over the other takes |
|---|---|---|---|---|---|---|---|---|
| 978 | `978-g2532571` | `978tw17.Ct` | `z9-46f840.F1`, `z9-28f760.F1` | 15, 17 | +4.69e-04 | -3.15e-06 | 1.008e-07 | 1.008e-07 |

The bar is the one of 12:11 UTC. The fq quench of the polish lane (`zone_corner.py quench`) on boxD found nothing on 978 in 133 s.

### AA8. What to run next

1. Keep the growth loop and its 3 slots, and keep cutting the near folders of other lanes. Every n that certified here in this round came from a corner that the loop cut from a layout of another lane. They are `931st21.C` (stair-c 931) for 994, `936nf21.Ct` (a near layout of the family lane) for 875, `931po21.C~` (polish 931) for 931, and `978tw17.Ct` of an older cut for 978. The 875 row was built 2 minutes after the rank of its step, and the 994 row 3 minutes after its cut.
2. Run the generator of each step with more cores, or split it by n over two boxes. It decides when a new corner gets its first row. On boxA it took 33 minutes for step `i53` at a load of 20, and 15 to 18 minutes for `i54` and `i55`. The slot of boxA builds nothing in that time.
3. Give the lane a kick of its own builds that end near the bar. On 994 all 6 builds of three corners ended at 31.92846. The classfill lane went 1.1e-4 of side lower with an lkick of its own build on the same corner, 25 minutes after our certification. The midm lane took our 976 of the first run lower in the same way. A `midm_scan.py` kick (kick and lkick, sigma 0.02) of each build within 2e-4 of the bar, at once and on its own slot, would keep such n here. Our two scans at the end of the round made only 13 and 17 tries and found nothing.
4. Fix the claim of the loop with `ssh -n`, and check after each step that `glist.txt` is newer than the step. The crash of the ranker idled the two slots of boxD for an hour in the first run, and no check saw it.
5. The hopped class 5 corners of the stair-c lane at f 0.93 fit few n. Their best rows were 5.7e-4 of side above the bar, and their 994 builds ended at the same layout as the cut corners. They need no more slot time.

## Files

| file | what it is |
|---|---|
| [`modules.py`](../modules.py) | the cut, the library, the length tables, the generator, the controls, the builds and the take |
| [`results/modules-library-2026-11-11.tsv`](../results/modules-library-2026-11-11.tsv) | 366 modules with loss, f, source and licence |
| [`results/modules-predict-2026-11-11.tsv`](../results/modules-predict-2026-11-11.tsv) | 378 predictions with the modules chosen |
| `<scratch>/bounties-squares/take-modules-r10` | the take of round 1: one csv per n and `take.tsv` (boxA, not in git) |
| [`results/modules-r11-2026-11-11.tsv`](../results/modules-r11-2026-11-11.tsv) | every choice built in round 2: modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r11` | the take of round 2, and under `work/` the grown library, its tables, the lists and the raw builds (boxA, not in git) |
| [`results/modules-r12-2026-11-12.tsv`](../results/modules-r12-2026-11-12.tsv) | every choice built in round 3: list, modules, predicted side (as listed and from the 5 states), built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r12` | the take of round 3, and under `work/` the libraries (`libz2` with the zones, `libg` with the grants, `libgrow` with the grown layouts), the queues `qz/`, the lists and the raw builds, and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r13-2026-11-12.tsv`](../results/modules-r13-2026-11-12.tsv) | every choice built in round 4: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r13` | the take of round 4, and under `work/` the libraries (`lib4` with the rebuilt zone corners, `lib3-m13b` with the new far zone tables, `lib4-m13b` with the finer grants, `libgrow13` with the layouts grown from rounds 12 and 13), the generator rows `qz/`, the raw builds and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r14-2026-11-12.tsv`](../results/modules-r14-2026-11-12.tsv) | every choice built in round 5: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r14` | the take of round 5, and under `work/` the libraries (`lib14` to `lib14c`, `libg` with the round 14 layouts grown, `libd` with the dense twins), the generator rows `qz/`, the checks `farcheck-h14.tsv` and `qz/check-h14-part.tsv`, the raw builds and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r15-2026-11-12.tsv`](../results/modules-r15-2026-11-12.tsv) | every choice built in round 6: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r15` | the take of round 6 (empty at the end), and under `work/` the library `lib15`, the generator rows `qz/` and `boxD-qz/`, the checks, the raw builds, the off-wall measure `diag/offwall.tsv` and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r16-2026-11-12.tsv`](../results/modules-r16-2026-11-12.tsv) | every choice built in round 7: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r16` | the take of round 7, and under `work/` the libraries (`lib16`, and `lib16b` with every growth step), the generator rows `qz/` and `boxD-qz/`, the raw builds, the quenched copies `qd/` and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r17-2026-11-12.tsv`](../results/modules-r17-2026-11-12.tsv) | every choice built in round 8: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r17` | the take of round 8, `STATE.txt` (one line per start, stop and decision), and under `work/` the library `lib17` with every growth step, the queues `qz/` and `boxE-qz/`, the raw builds, the quenched copies `qd/` and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r19-2026-11-12.tsv`](../results/modules-r19-2026-11-12.tsv) | every choice built in round 9: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r19` | the take of round 9, `STATE.txt` (one line per start, stop and decision), and under `work/` the library `lib19` with the growth steps and the turned twins of the growth loop, the queues `qz/`, the raw builds `raw/` and `boxD-raw/`, the quenched copies `qd/`, the turned tables, logs and queues of boxD (`boxD-misc/`) and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r20-2026-11-13.tsv`](../results/modules-r20-2026-11-13.tsv) | every choice built in round 10: list, modules, predicted side, built side, held side, the bar and the certified gain |
| `<scratch>/bounties-squares/take-modules-r20` | the take of round 10, `STATE.txt` (one line per start, stop and decision), the near layouts `near/`, and under `work/` the library `lib20` with every growth step, the scan rows `qz/shift-*.tsv`, the queues `qz/`, the raw builds `raw/` and `boxD-raw/`, the quenched copies `qd/`, the turned tables, logs and queues of boxD (`boxD-misc/`) and the tools of this round under `work/tools` (boxA, not in git) |
| [`results/modules-r21-2026-11-13.tsv`](../results/modules-r21-2026-11-13.tsv) | every choice built in round 11: list, modules, predicted side, built side, held side, the bar, the certified gain and the UTC time of the build |
| `<scratch>/bounties-squares/take-modules-r21` | the take of round 11, `STATE.txt` (one line per start, stop and decision), the near layouts `near/`, and under `work/` the library `lib21` with every growth step, the queues `qz/`, the raw builds `raw/` and `boxD-raw/`, the quenched copies `qd/`, the tables, logs, kick scans and queues of boxD (`boxD-misc/`) and the tools of this round under `work/tools` (boxA, not in git) |

## Summary

- The cut by stack faces splits a two-arm layout into a corner, two far zones, flush stacks and the rest. The count sum is exact. The length sums hold by definition, and the stacks of a run have gaps of up to 0.011 of wall that no zone counts. The loss of a zone follows its family (c, count, uprights) and f, to 0.003 squares in sample and 0.009 out of sample.
- The library has 366 modules from 71 held and 51 public layouts. The generator returns a layout from its own modules within 1e-3 of f on 97 of 122 layouts. Of the 25 it misses, 11 have an arm that is not flush. In the others the rest slides beside a zone and the tables hold it rigid. Control 2 misses by 0.004 for the same reason, and the squeeze recovers the miss.
- 28 n certify below held for 0.0013925. Ten of them are among the 12 best predictions. 72 of 74 builds end below their prediction.
- The library closes about 1% of the 0.134. The board's zones lose less than ours, by a median of 0.5 squares at f of 0.87 and more and by 1.3 squares below. They are not in any file we have. Section 6 lists the zones to design.
- Next: build the other 304 predictions, cut the new layouts into the library, and make the sliding rest a part of the module.

Round 2:

- The library grew from 366 to 673 modules (63 layouts cut and 114 slid twins). 11 n certify below held and below every other take, for 0.0006337 against held and 0.0002780 over the other takes. 125 choices were built of the 991 listed, so the lists are not built to their end.
- The slide of the grid beside a zone is now a part of the module, as slid twins. Control 1 passes on 158 of 172 layouts (110 of the first 122, where it was 97). It fails on 14, so it is still red. Leave one out misses by +0.0020 in the median (round 1: +0.0030), and the twins do not move it.
- `family_step.squeeze` and `methods_lp.slp` with fq end at the same side to 1e-9 on 7 builds. The default stays.
- The growth opens one count class (two 7-arms, class 0, f of 0.90 and more) and no band of f. New zones have to come from a search, and the far zone in that search should be free to poke into row 0.

Round 3:

- 5 n certify below held and below every other take: 599, 755, 757, 862 and 923, for 0.0002864 against held and 0.0000122 over the other takes. 208 choices were built on 76 n. The other takes already held most of the large builds (634, 803, 871 at the same side).
- A corner table now holds only the 5 LP states a corner was found in. The points on the line between two states were not states, and every prediction of the 934 kind fitted only at one. With the 5 states, 3 of 184 builds end more than 1e-4 above their prediction (30 before), and 38 of 39 choices predicted below held build below held.
- 2,972 corners with a grant they were not found with: a grant of 0.04 costs about 0.01 of length in the median, and every far zone that pokes now fits a corner. No granted choice is predicted below held, and the 9 built had no start: 7 from tables before the clamp of negative costs, 1 from stale build copies of `modules.py`, and 1 from a fault that is not fixed (the head cell of a grant on a corner slid on the other arm, 146 variants).
- The library holds 972 zones of the zone lanes (1,645 modules). The generator runs over all 413 n in 16 minutes on two processes, with a search window and a fit of all choices of a corner at once.
- Below f = 0.80, 192 of the 216 held layouts have no two arms on walls at all, so the cut cannot reach them at any tolerance. A loose tolerance as a fallback adds 4 layouts and leaves the 73 cuts of today unchanged. The library has 157 corners there, none of two 6-arms and none with an 11-arm. The generator finds one n below held there (634), which another take already holds.

Round 4:

- 3 n certify below held and below every other take of round 13: 700, 875 and 936, for 0.0002008. All three use modules grown from layouts of the last two rounds: the far zones `760h12.F2` and `817h13.F2`, and the corner and far zones of the held 598 and 871. Growing the library at once with every new layout pays.
- The head cell of a granted corner now takes the grant. Of the 146 variants it hit, 113 can never be legal (two cells of the rest overlap) and are no longer made. Every granted choice built this round has a start, and none ends below held.
- The zone corners stored at a rounded f are out of the library, and the 471 rebuilt corners are in. The generator over every n, with the old library, with the rebuilt corners and with the finer grants (0.01, 0.02), found no other n below held. Its rows within 1e-3 of held rebuild the held layout.
- Carrying the cost of a grant at one f overstates it above that f, by 0.02 to 0.18 for grants of 0.10 and 0.16. Below that f, it understates the cost in one case in ten. A full table per variant costs about 1.5 s.

Round 5:

- 8 n certify below held and below every other take of round 14: 758, 862, 863, 871, 924, 984, 994 and 995, for 6.20e-5. 994 and 995 give 4.7e-5 of it.
- The length of a far zone is not straight between the knots of its table, 0.005 apart. Walked by steps of 0.0005, 73 of 144 far zones have a state shorter than the table by more than 1e-3. 12 have a stretch where no state is as short as the table. The 601 row fails on one of these: `814h09.F1` is 5.2e-3 longer than its table at the f of the row.
- Far zones may now be walked and tabulated by a smaller step (dense twins, step 0.001). The 159 twins lowered the best row on 24 of 72 n, and five of the eight wins use one. `modules.py check` tests a row the way the build starts it.
- The cut takes only 6 of the 97 public fault-line layouts of round 13: the others have no two arms of flush stacks on two walls. True tables of the near-bar grant variants change no build.

Round 6:

- No n in the final take. 921 (1.181e-6) and 587 (4.0e-8) certified below held during the round, and the corners and polish lanes beat both by the end.
- Both wins came from rows predicted 3.2e-4 and 7.7e-4 above held, with a dense twin of this round. The rows within 3e-4 of held are nearly all the held layout again.
- 114 more dense twins and the 528 far zones as new modules lowered the best row on 8 n. They found no row below held except the false 601 rows.
- An arm off the wall stands one whole column off. Its outer L holds tilted squares, so peeling it does not give a layout the cut takes.

Round 7:

- 6 n certify below held and below every other take of round 16, for 1.130e-4. 921, 984 and 649 give 1.02e-4 of it.
- Every big win takes the corner of a new layout and puts other far zones and other stacks beside it. The new layouts are the round 15 held file and the takes of this round. A loop cut every new take layout within 8 minutes. The squeeze took 5e-4 to 8e-4 off the start of these rows in the median.
- `Library.best` is about 4 times faster and gives the same rows, so a near search covers 40 n in 1 to 4 minutes.
- Other lanes took five more of our builds lower (549, 700, 703, 860). The outer L of a shell is not started.

Round 8:

- 5 n certify below held and below every other take of round 17, for 2.133e-4 against held: 754, 703, 700, 598 and 378. 754 gives 1.237e-4 of it.
- Every win uses the corner of a layout made in this round. In the median the squeeze takes 4.9e-3 off the rows of `813mi17.C`, 2.1e-3 off `700re17.C` and 8.6e-4 off `815st17.C`. On older corners it takes 5e-4. So the lists now reach 1.2e-2 above the bar for new corners, and `tools/offset17.py` ranks each row by the offset of its corner.
- The builds of one corner on one n end at a few sides, and the stacks pick the side more than the far zones do. On 754 a row with other stacks gave 1.06e-4 of side more than the first win.
- The growth steps after 18:30 UTC (`v2` to `v5`) gave 42 builds. 27 ended below held, mostly at sides that the corner lists had reached first. The outer L of a shell is not started.

Round 9:

- 6 n certify below the round 17 file and below every other take of rounds 17 and 19: 378, 503, 550, 587, 975 and 996. They give 3.724e-5 against the round 17 file and 3.707e-5 over the other takes. Our 754 (1.498e-4) and 554 (8.360e-5) certified first here, and then two other lanes took our files lower.
- New corners built far below their prediction because a corner table froze the angles of every square off the arm tilt. The turned twin of a corner lets them turn at every step. On the 754 build of round 17 the frozen table of `813mi17.C` was 0.05 longer on both lengths than the built corner.
- 99 builds from a turned start ended between 7.8e-4 below and 1.8e-4 above their prediction, so the control passes for turned starts. The turned table also finds layouts the frozen one misses: 754, 554, 975 and 996 come from turned rows.
- The growth loop cut every new layout of the round, our own too, and gave 378, 550 and a second 554. The outer L of a shell is not started.

Round 10:

- 4 n certify below the round 18 file and below every other take of rounds 19 and 20: 649, 756, 862 and 996. They give 1.262e-4 against the round 18 file and 9.68e-5 over the other takes. 810, 869 and 549 certified here first, and then other lanes took them lower.
- The growth loop gave every n of the take. It cuts each new layout of every lane, makes the turned twins of its corners and builds the best rows. Rows up to 6e-4 of side above the bar still won (649, 756), so the loop needs more build slots than it had.
- Turned twins of 120 old corners, ranked by a scan with a fixed shift, gave one n (810), and two other lanes then took it lower. Most rows near the bar rebuilt the held layout of their own n.
- Two turned twins predicted rows 0.038 below the bar that had no start. A corner with 2 builds that had no start, and none that had one, is now dropped. The outer L of a shell is not started.

Round 11:

- 978 certifies below the round 19 file and below every other take, for 1.008e-7. Five more n certified here first: 931, 875, 994, 813 and 976. Other lanes took four of them lower within 40 minutes by a kick or a quench of our own file.
- Every one of the six came from a corner that the growth loop cut from a new layout of another lane. The best rows were built 2 to 3 minutes after the cut or the rank.
- A crash of the ranker on a glob that matched nothing idled the build slots of boxD for an hour in the first run. A claim over `ssh` without `-n` kept the slot of boxA from building. The generator of a step took 15 to 33 minutes on boxA under load.
- The lane needs a kick of its own fresh builds. The classfill lane moved our 875 by 2.43e-4 of side with one 450 s scan.
## Round 22

The final take keeps n=507 and n=875, checked at 15:28:52 UTC.
It gains 0.00008062771206 against round 20 and 0.00000778302285 beyond all frozen round 21 and other live round 22 takes.

| n | Certified score | Gain on round 20 | Gain beyond other takes |
|---|---:|---:|---:|
| 507 | 0.019699671054121515 | 0.00000236070791 | 0.00000236070791 |
| 875 | 0.013669801040784968 | 0.00007826700414 | 0.00000542231494 |

The 507 build uses the turned harvest corner and a new far zone cut from the corners lane's 815.
The 875 build uses the corners lane's new 875 corner and a stair-c near layout's far zone.
Its family kick and certified-file quench beat the best other module build without a kick by 1.07e-8 of score.
The exact 931 file also seeded a lower result in the invent lane, so 931 counts there.

The run uses the round 20 held file and must beat every frozen round 21 take and every other live round 22 take.
The take is `<scratch>/bounties-squares/take-modules-r22`.
The [held source register](../results/round20-best-2026-11-13.tsv) and each donor's `take.tsv` name the sources and licences.
The [build table](../results/modules-r22-2026-11-13.tsv) records completed builds and failed attempts.

The [round 22 controller](../modules_round22.py) gives boxD one generator/build slot and one fresh kick/quench slot.
boxA has one slot for cuts, tables, certification and builds.
Each candidate gets floatsafe certification, then a box quench from that certified file, before it enters the take.
The quench slot uses `zone_corner.py`.
The kick slot first used `midm_scan.py`, then the lkick engine of `invent_rest.py`.
Both imports are unchanged.

The claim uses `ssh -n` from the first queue.
Its control preserved both input lines.
A deliberately loose n=2 layout gave side 2.5 before the kick and 2.0 after it.
The certified-file quench reproduced that result.
The standalone readers preserved coordinates, counts and f on the 7 zip80, 6 zip825 and 2 c758b corners.

The first full generator searched 414 n in 558 seconds on boxD.
The next version searches batches of 40, with the newest design first and one build between batches.
The batch control retained all 414 n in order, with no duplicate or omission.
The local builder can use completed rows from a generator that is still running.
Growth passes turn two corners at a time and keep the rest in `work/turn-pending.txt`.
This lets new frozen tables reach the build queue before every turned twin is ready.
The f93h5 corners measured dry in round 21 are excluded from builds.

The generator now rejects predictions more than 0.005 below the bar before choosing its top three rows.
Previously, such rows occupied every slot and the ranker discarded them afterward, hiding the remaining choices.
At n=816 the control changed three rejected predictions at -0.037963 into three alternatives at -0.004578.
One exposed choice built n=816 at side 28.978617565, 0.000455 above the bar at that check.
It gave no gain.
At n=304 all three accepted rows stayed identical.
The queue wrapper also applies the historical corner and nearby-f refusal rules before that selection.

The [table helper](../modules_tabulate22.py) resumes missing tables from earlier growth steps.
Its control recovered one missing old module and added its id to the next generator input.
It preserved the requested module whose table already existed.

At 13:30 UTC the exact 931 result prompted a switch to the lkick engine of `invent_rest.py`.
The worker restarted at 13:35:49 UTC with family squeeze and fq.
That engine took our exact 931 build lower in the invent lane while two of our fq-only scans found nothing.
Its positive control shrank a tilted n=2 layout from 2.509949833751 to 2.000000000000.
The imported tool is unchanged, and each result records the engine that produced it.
The table helper now collects results between module solves, within the same local CPU slot.
It reads complete rows from live kick scans and still requires a box quench before publication.
Its transport control copied a new heartbeat through the family-results channel in 33 seconds.
The collector has its own process group and stops by the lane deadline.
Completed quenches now publish before new raw results are processed.
Unchanged certificates are cached by all row values, scorer code and numeric-library versions.
The cache control checked a valid layout once and reused its identical input.
A changed layout with overlapping squares forced another full check and was rejected.
Raw certification progress is saved per candidate, and interrupted quench sends resume without replacing a completed queue item.
The worker refuses new commands after 15:20 UTC and new builds after 15:19 UTC.
The deadline control ran its on-time marker and refused the expired command before launch.
New-design imports stop at 15:15 UTC.

The final table has 53 attempts, including 43 completed builds and 24 builds below the held side.
Seven raw builds are below the final comparison side.
Four of those margins are at most 1.54e-9 of side and do not become certified wins.
There were 19 completed kick scans: six with midm and thirteen with family.
The last family scan improved the fresh 863 build by 2.94e-5 of side in two tries.
Its result remains 4.47e-5 above the bar and is saved in `near/`.
The last 40-n generator batch took 362 seconds.
Batch j0015 started before the cutoff and timed out at 15:20 UTC.
The box archive retains its partial rows and task, along with 1,099 pending turned corners.

Fresh certification of both retained CSV files passed with zero dilation.
Their minimum separations exceed 5.0e-11, above the 2.2e-11 requirement.
Every retained result completed its quench on boxD from its certified file.
The archive contains 1,337 files and 103,637,006 bytes, all checked with SHA-256 before the box scratch was removed.
The older box controller logged a one-second build after its timeout and ended at 15:20:01 UTC.
It predated the refusal guard now in the controller.
The remaining idle local controller stopped at 15:20:08 UTC.
No lane worker remains.

Next round should cut fresh layouts and use both new corners and far zones first.
Those parts produced both retained n and the 931 seed that invent improved.
Keep the fresh kick slot, but distinguish its small extra gain on 875 from the larger gain of the module build.
Use smaller generator batches or a time limit per batch as the library grows.
The measured time grew from 558 seconds for 414 n to 362 seconds for the last 40 n.
Resume j0015 before older queued work, then select pending turns by their predicted fit rather than list order.
The pending list holds 1,099 corners, while only two turns ran per growth pass.

## Round 23

The final take is empty, checked at 18:28:32 UTC.
It has no qualifying gain against round 21 or the other takes.
Its n=503 near layout fed n=550 and n=599 in the harvest and polish lanes.

The modules lane resumes the unfinished j0015 batch from round 22.
It cuts fresh takes and near layouts, then builds combinations with their corners and far zones.
The [build table](../results/modules-r23-2026-11-13.tsv) records each returned build and failed attempt.
The take is `<scratch>/bounties-squares/take-modules-r23`.
A result must beat round 21, every frozen round 22 take and every other live round 23 take.
The [round 21 source register](../results/round21-best-2026-11-13.tsv) and each named donor table preserve the upstream sources.

The [round 23 controller](../modules_round23.py) keeps one generator/build slot and one family kick/quench slot on boxD.
boxA has one slot for cuts, tables, certification and builds.
Both search and quenches have the same deadline, 18:30 UTC on 2026-11-13.
The generator uses batches of 12 targets with a three-minute limit per batch.
Partial rows remain available to the ranker after a timeout.
The partition control preserved all 414 target numbers in order.
The deadline control ran an on-time marker and refused an expired command.

The [near reader](../modules_near23.py) fixes an angle conversion in the previous scratch helper.
Packing CSV angles are radians.
The previous helper converted them as degrees, which gave incorrect bounding sides.
The new reader matches `modules.normal` on certified n=507 at side 22.960231303451124.
It keeps every distinct round 23 side, including a larger fresh design beside an older smaller one.
The control exported both n=507 layouts at sides 22.960231303451124 and 22.96025326368242.
It also preserves sidecar sources and licences and links the donor tables used by readers.
Archived round 22 near inputs still use their best layout per n.

The [ranker](../modules_rank23.py) now admits untested corners where three older builds ended at the bar.
The previous filter applied the old failures to every new corner at that n.
A control showed the old ranker drop a novel corner at n=862 and the new ranker admit it.
On the archived queues, this exposed three extra build lines on n=871 and n=973.
Historical refusals for a corner and its unreachable states remain in place.

The [table helper](../modules_tabulate23.py) recovers tables that a bounded growth pass leaves unfinished.
Completed tables reach the next generator, and unfinished turns stay in the pending list.
The local controller collects completed certificates between table solves.
It sends the strongest precertificate per n to the remote quench queue.
Four n=503 versions differed by only 1.48e-8 of score, so their weaker pending quenches were redundant.

Two setup faults were corrected during the run.
The recreated remote snapshot lacked the current `Library.best` argument used by the queue wrapper.
Copying the current repository imports repaired it, and the resumed batch completed in 149 seconds.
The imported quench tool also expected `fq` below `ext/evand/search/packer/target/release/`.
The controller now creates a link there to its own binary.
After that fix, the loose n=2 control shrank from side 2.5 to 2.0.
The n=503 certified-file quench then completed, but its file no longer beat the other takes.
No failed quench entered the take.

The table records 54 attempts and 50 completed builds.
Of those builds, 28 end below the held side by more than 1e-10 of score.
None clears that margin over the final bar.
The raw n=503 build initially passed certification, but its completed quench could no longer beat the live takes.
Its near file remains in the source chains of the harvest and polish rows at n=550 and n=599.
Those rows count in their producers' takes.

The growth loop cut 217 new layouts and added 1,912 modules across 18 passes.
There are 1,555 new available tables and 33 completed turned corners.
The pending turn list holds 2,447 corners.
The generator ended 36 batches: 25 succeeded, 10 timed out, and one failed during setup.
Timed-out batches retain partial rows, but the next offset advances by 12 targets.
Targets not reached within a timed-out batch remain unmeasured.

Nineteen bounded family scans ended, including one timeout, and returned 42 raw finds.
A twentieth scan was interrupted during closing.
The final collector checked its complete files before the last comparison.
The take contains 92 near CSV files.
The final uncached certificate check also kept no n.

A handoff audit found that `874ns22.F2~` still had no knots after its recovery attempt.
The library correctly excluded its unusable table.
Handoff lists now contain only available tables.
The positive control retained `304h.F1` and excluded the missing table.
The table helper caches failures by module content and solver code.
Its real-module control recorded one failed solve on the first run and zero solves on the second.
This keeps an unchanged failure from consuming every growth pass.

Search stopped after the 18:25 intake cutoff.
Collection completed with an empty quench queue, and both closing workers then stopped.
The closing control dispatched a fresh canary in normal mode and none in drain mode.
A separate control stopped its owned process tree and preserved an unrelated canary.
No lane worker remains on boxA or boxD.

Next round should cut fresh designs first.
The n=503 near file supplied the measured n=550 and n=599 follow work.
Resume the newest pending generator tasks with their saved tables, then rank the 2,447 pending turns by fit.
Fix per-target checkpointing before repeating the batch scheduler.
Ten batches timed out, and advancing by 12 can skip targets that never ran.
Keep kicks on fresh builds, with geometry deduplication for copies that return to a known side.
The 19 ended scans produced raw improvements but no retained n here.

The final archive contains 1,639 files and one link, totaling 1,735,290,183 bytes.
Every file passed SHA-256 verification before the remote scratch was removed.
The shared Python environment was preserved.
## Round 24

The lane retained clean n=550 under the main session's revised source rule.
Its score matches candidate A to 4.0e-15.
It gains 0.000191725590407 over the source policy base and 0.000023109030044 beyond the other eligible takes.
The uncached certificate measured clearance 5.019984428145108e-11 with no dilation.
The [results table](../results/modules-r24-2026-11-13.tsv) records every build attempt and its source group.

There were 68 build attempts and 60 completed builds, including 11 clean builds.
One clean raw build beat the eligible comparison bar.
The library gained 250 layouts, 1,146 module IDs and 456 valid tables.
Remote workers produced 63 table files, including 45 turned corners.
The queue saved 2,678 completed targets across 226 generator batches.
Sixteen completed kick runs produced 28 raw files, and the lane exported 74 near files.
Its take is `<scratch>/bounties-squares/take-modules-r24`.
The [controller](../modules_round24.py) uses one local slot and two slots on boxD.
Search and quenches share the deadline of 22:15 UTC.

The [queue](../modules_queue24.py) saves every completed target, including targets that return no choice.
A failed solve leaves its target pending.
The control saved empty n=338, retried interrupted n=503 and repeated no completed target.
The resumed j0033 task completed all 414 targets with checkpoints and returned zero choices after source filtering.

The [source filter](../modules_sources24.py) conservatively removes old excluded count families and their named descendants.
The initial filter also removed permitted areebbb modules.
It now accepts complete per-n upstream chains and still refuses the excluded ancestors.
The initial filter removed 2,341 modules and retained 11,473.
The candidate supplied 21 new cuts and 85 modules before the count filter.
The [near reader](../modules_near24.py) imports the soft lane's ancestry reader and preserves each accepted source record.
Its first corrected run accepted all 42 fresh twoshort near files.

The [geometry key](../modules_geometry24.py) stops repeated kicks of the same geometry.
Its control matched a translated quarter turn and admitted a changed separation.
The remote quench control reduced a loose n=2 layout from side 2.5 to 2.0.
The first attempt preceded the completed binary transfer and failed.
The repeated control passed after the transfer and binary link were ready.

The [spare-slot helper](../modules_tablejob24.py) makes missing tables while the box has no build, kick or quench pending.
The [transfer helper](../modules_tables24.py) imports each complete table once.
Its positive control printed `304h.F1 table valid True`.
Local table passes now put fresh corners first and stop after 90 seconds.
Five local turn passes hit their limits without a completed table.
Pending turns now run on the box.
Every second generator batch reserves a table job.
Atomic claims keep the two box slots from solving the same table.
The local slot stays on cuts, tables and certificates while `LOCAL_TABLES_FIRST` exists.
Its control preserved a build for the box with that flag and attempted its claim without the flag.
A local n=973 build timed out during fq after 180 seconds.
The completed remote build took 351 seconds.

The old `911k122.F2` label names a deleted polish n=538 file.
The round 22 register resolves it to areebbb n=538 and the malyshevdanil atlas upstream chain.
The source normalizer now preserves that chain in the source and licence fields of each matching result.
Its control accepted the expanded chain and rejected a copy with an added excluded n=639 ancestor.

The public-chain control accepted the candidate sources of n=503, n=550 and n=599.
It rejected an added excluded n=639 ancestor and an unexpanded public source.
A candidate recut restored 7 layouts and 23 modules.
Four archived n=503 raw layouts entered the cut queue.
Round 23 skipped its own near folder, so those raw layouts supplied no cut there.
The source audit traced their corner parts through areebbb n=703 and the malyshevdanil atlas.
Their full layouts also carry Samanyu far zones, so only separately traced clean parts enter the final clean search.

One shared side limit now admits near designs up to 0.015 above the comparison side.
The earlier raw filter still cut at 0.0002 and hid the wider export limit.
An integration control exported legal packings at +0.000256 and +0.01477 of side.
It excluded the packing at +0.01501.
The own-kick limit stays at 0.0002, while the wider designs reach the module cut and other lanes.

Full ancestry fields broke the cut at Python's default CSV field limit.
The largest live take field measured 218,752 characters at n=802 in the forensics take.
The bar reader now raises the limit before it imports any solver.
The cut, source reader and closing checks accept the same full records.
A control read a source with 200,000 padding characters and selected the expected comparison side.

Each accepted cut now saves its geometry and pending module IDs in one atomic pickle.
The text ID journal is derived from that checkpoint.
The table helper reads the saved IDs when an interrupted pass left that text file incomplete.
The integration control interrupted a two-layout cut after n=507.
It removed the text journal, then recovered n=507's IDs and retried only n=875.
The full padded source survived the cut.
Command failures now appear in STATE.txt with their log paths.

The main session changed the source comparison rule in its 20:05 UTC handoff.
Its submitted round 23 file holds 20 candidate counts at round 22 while the owner reviews Samanyu seed ancestry.
For those counts, a result with no recorded Samanyu ancestry only needs to beat round 22 and the clean competitors.
The [source policy](../modules_policy24.py) applies that comparison and writes the ancestry group in each retained licence cell.
It replays the original seed merge's score order to distinguish Couzo and Samanyu seed rows.
Its control identifies Couzo n=304 and Samanyu n=503 and refuses an unresolved old held donor.
The publisher control retained a certified clean control packing with an explicit notice and refused a fresh Samanyu-only input.

The remaining generation, tables and kicks prioritize parts with no recorded Samanyu ancestry.
The earlier Samanyu and unresolved work stays in the archive.
The clean bootstrap has 7,556 available module tables and searches the 20 held counts first.
Four direct public n=703 parts were restored with the complete malyshevdanil upstream chain.
These include the corner that supplied the archived n=503 design.

The builder now checks the source group again before it claims an old ranked choice.
Generation filters alone left older Samanyu choices in the ranked backlog.
The control skipped the first Samanyu choice and built the next clean choice.
Both remote workers restarted with this guard.

A clean n=550 build reached the round 23 candidate's score.
Its certified-file quench finished on boxD at 22:07:20 UTC.
It entered the take at 22:09:23 UTC under the main session's source comparison rule.
The row records the full areebbb n=703 chain and an explicit no-Samanyu notice.

The final fresh licensed k123 n=847 layout failed the cutter with `no two flush arms`.
Its side is 29.598972597255308.
Retrying the same cutter would repeat that measured failure.

Search stopped at 22:08:40 UTC to finish the certified-file drain.
All owned workers stopped before 22:15 UTC.
The final archive holds 3,471 files and one symlink, totalling 2,011,052,223 bytes.
Every file passed its SHA-256 check.
The process audit found no owned worker on either box.
The lane's remote scratch was removed after verification, and the shared venv remains.

Next, best first:

1. Recombine the certified clean n=550 and its n=703 corner family toward n=503 and n=599.
   The clean corner recovered n=550, and the round 23 n=503 family fed both n=550 and n=599.
2. Filter the 1,739 pending turns by clean ancestry, then finish the freshest jobs remotely.
   The box completed 45 turned corners after five local turn passes produced none.
   The archive also preserves 497 pending table jobs and 22 generator tasks.
3. Process changed take rows before scanning the full near archive.
   The last two near scans hit their 120-second limits, while per-cut checkpoints preserved completed work.
4. Change the extraction geometry before using the new licensed n=847 layout.
   Its current cut fails because it lacks two flush arms.

## Round 26

Round 25 lost its agent on a usage limit at about 23:50 UTC on 2026-11-13.
Its drivers ran on to the deadline, and its STATE.txt is the record of that round.
Round 26 ran from 12:50 to 17:25 UTC on 2026-11-14 against the round 25 b bar (`gate/cand-round25-1114b`).
Its agent died twice, on a usage limit at 13:24 UTC and on a dropped connection at about 16:29 UTC.
The background drivers ran on both times, and the next agent adopted them.
The [results table](../results/modules-r26-2026-11-14.tsv) lists the four take rows, every build of the round and every kick with its start and best score.

| n | round 25 b | round 26 | gain | lowest live r26 row |
|---|---|---|---|---|
| 748 | 0.017461443370112573 | 0.017423530514737218 | 3.791e-05 | no: quench 0.017419158288839443 |
| 805 | 0.016571910454758143 | 0.016562831636665054 | 9.079e-06 | no: invent 0.016561519770223132 |
| 911 | 0.016568050854429694 | 0.01655899393469218 | 9.057e-06 | yes |
| 975 | 0.015663917278472717 | 0.015663910835057582 | 6.443e-09 | yes |

The four rows gain 5.605e-05 against the base bar.
They gain 9.063e-06 beyond the other live takes.
The lower 748 and 805 rows of quench and invent start from our builds.
Every row had one certified-file fq quench on boxD before it entered the take.
The publisher walked each row's full recorded ancestry with `take-assemble-r25/deep25.walk`.
It also searched the bare names `921-29e12ff3`, `747r` and the seeds 365, 804 and 983.

### What gave rows

The first item quenched two round 25 kick results from their certified files.
Round 25 kicked 911 to 9.057e-06 and 805 to 3.825e-06 below the round 25 b bar.
Neither result reached a round 25 take.
In round 25 the one local loop sat in growth steps from 00:50 to 02:18 UTC.
It certified the 805 finds of 01:17 UTC only at 04:19 UTC, after the deadline.
Both quenches gave no further gain, and both rows entered the take at 12:59 UTC.
The 975 near result of round 25 followed at 13:12 UTC with 6.443e-09.

The [controller](../modules_round26.py) is the round 25 controller with round 26 paths and a 17:15 UTC deadline.
`tools/fastloop.sh` now runs collect, bar, certify, quench staging and publish every 60 seconds.
It runs apart from the growth loop, so a growth step no longer delays a certified row.

The 748 row came from a corner that growth cut from an invent near file of n=805.
The build `748-g8b1f3b4` certified at 3.791e-05 below the bar at 13:39 UTC.
Invent followed it within a minute and went 4.37e-06 lower.
Quench then took that row as its own 748.

The [dispatcher](../modules_dispatch26.py) gives the boxB kick slot the best fresh build that the boxD slot has not reached.
Its first claim of this kind became the 805 row.
The build `805-geb9d74b` used the corner of the invent 805 take and far zones `924q1.F1` and `987r10.F1~`.
A 450-second midm kick found 9.079e-06 below the bar, which was 2.92e-06 below the invent 805 of that time.
Invent then built on our row and went 1.31e-06 lower at 14:40 UTC.

### Measured dead ends

A kick start within 1e-5 of side of the base layout gives no row.
The round 25 table has fourteen such starts and one row of 6.4e-09.
Round 26 kicks of near layouts within 1e-8 of the bar went back to the held optimum.
The 758 re-kick went from +1.159e-07 to -4.895e-11, and the 650 re-kick went from +5.781e-09 to +8.449e-10.
The rows of size came from builds 1.6e-04 to 1.0e-03 of side away from the base layout.
The kick worker and the dispatcher now skip a build within 1e-5 of side of the base layout.
They also skip a build within 1e-5 of side of another lane's live row.
That second rule stopped two 932 builds that sat 1.5e-09 of side from the forensics 932 row.

These kicks of fresh builds stayed above the bar:

| n | kicks | best result |
|---|---|---|
| 873 | 8 | one find, +3.424e-06 on the base |
| 813 | 3 | +6.008e-06 on the base |
| 911 | 6 fresh builds | +6.57e-07 to +6.93e-07 on the base |
| 934 | 4 | +6.15e-08 on the base |
| 805 | 6 from builds at +8e-06 | -5.0e-06 on the base, 5.4e-06 above the invent 805 |
| 748 | 6 | 9.3e-09 to 3.1e-08 above the quench 748 |

The 748 kicks of four different builds all ended at 0.01741916 to 0.01741919.
That is one basin, and the quench 748 holds its floor.

### Traps

A corner cut from a path of the form `take-<lane>-r26/<n>.csv` can lose its source when that lane replaces the file.
Invent removed its 805 at 14:29 UTC and wrote a new one at 14:40 UTC.
The publish walk then refused a second 805 kick result for the missing parent.
The old layout still exists under `take-invent-r26/work/boxE-raw`.
Cut corners only from near files or from immutable copies.

The box scratch reached 2.5 GB of its 3 GB budget at 14:57 UTC.
Each of 22 pending generator tasks held its own 110 MB library copy.
`tools/libtrim26.sh` keeps the running task and the newest three copies.
A resumed task copies its library again from its checkpoint.

The 975 source cell named a withheld twoshort file only to say that the row does not use it.
The walk read that mention as a missing ancestor.
The cell now names no path for the file it does not use.

The [table writer](../modules_table26.py) read boxD kicks from a `kickfetch/` folder that round 26 never wrote.
It now reads them from the STATE.txt finish lines and their finds in `kickraw/`.
Its control listed 18 boxD kicks, and the kicks with no find have an empty best.

### Work done

The round ran 45 growth steps, which added 1,530 modules.
The results table lists 142 builds, and 138 of them completed, all on boxD.
It lists 51 kicks, 29 on boxB and 22 on boxD.
The lane wrote 195 near layouts to `near/`.
Two queued 873 boxB kicks went to a hold folder before they started, because 873 had six kicks with no find.
All workers stopped at 17:13 UTC.
A build started after 17:12 UTC could not reach the 17:25 UTC take.
The box scratch was copied to `take-modules-r26/work/box-final` and checked by checksum, then removed.

Next, best first:

1. Cut corners from the fresh near designs of other lanes as soon as they appear, then build and kick them within minutes.
   Both rows of size this round came from corners cut from invent's 805.
   The 748 build certified 3.79e-05 below the bar, and the 805 kick 9.08e-06 below it.
   Cut only from near files or immutable copies, because a replaced take file refused one 805 result.
2. Give both kick slots only to fresh geometry, more than 1e-5 of side from the base layout and from every live row.
   The rows came from builds 1.6e-04 to 1.0e-03 of side away.
   Fourteen round 25 starts within 1e-5 of side gave one row of 6.4e-09.
3. Hand our lowest live rows, 911 and 975, to the quench lane early.
   Our own 911 re-kick moved only 4.9e-11, so a quench by another lane is the next step there.
4. Do not kick 873, 813 or the 911 fresh builds again unless the corner changes.
   The measured results are in the dead-end table above.

## Round 27

Round 27 ran from 19:24 to 23:45 UTC on 2026-11-14 against `round27-briefs/bar27.tsv`.
For each n, that bar is the lower of the held round 25 b row and the best certified round 26 take row.
The round 27 brief lifted the Samanyu-dev rule.
So the lane re-opened the inputs that it had refused only for that ancestry, and ran them first.
The [results table](../results/modules-r27-2026-11-14.tsv) lists the take rows, every build of the round and every kick with its start and best score.

| n | bar27 | round 27 | gain | lowest live r27 row |
|---|---|---|---|---|
| 597 | 0.018733014906038736 | 0.01873292249102132 | 9.242e-08 | yes |
| 871 | 0.014116942813953148 | 0.014111171821493462 | 5.771e-06 | no: backlog 0.014111171584058946 |
| 976 | 0.015557739655214453 | 0.01555773950943462 | 1.458e-10 | yes |

The three rows gain 5.864e-06 against bar27.
They gain 9.256e-08 beyond the other live round 27 takes, because the backlog 871 row is 2.4e-10 lower than ours.

Every row had one certified-file fq quench on boxD before it entered the take.
The publisher walked each row's full recorded ancestry with `take-assemble-r25/deep25.walk` and ran the prvsiyan share test.

### The Samanyu-dev rule is gone from the tools

[`modules_policy27.py`](../modules_policy27.py) removes the check and keeps the other rules.
It replaces `modules_policy24._origin`, so `piece` and `ancestry` give status `none` for the Samanyu roots.
They still give status `unknown` for penguin069, `verified-best-of-1105` and CC BY-SA text.
The soft lane's provenance trace loses its Samanyu markers when this lane stages another lane's file.
The publish walk drops the Samanyu signals and the withdrawals that were made only for that ancestry.
Other withdrawals still refuse a row.
The share test refuses a layout when 0.4 or more of its squares lie within 1e-3 of the excluded 1105 row of that n.

Controls, all measured:

- The held module `811h.F1` gives `samanyu` under the old rule and `none` under the new one.
- The prvsiyan 911 row is refused with share 1.000, and our round 26 911 passes with share 0.000.
- A CC BY-SA text added to a passing 932 record makes the walk refuse it again.

Under the old rule, 5,253 of the 14,366 modules in the library were blocked for Samanyu ancestry.
4,306 of them had tables, and no earlier round combined them with the new cuts.
The first generator task of round 27, `u0001`, used only those 4,306 modules.
The near trace cache `near27-cache.json` started with the 3,586 files that round 26 traced clean.
So only the 1,464 refused near files were traced again.

### What gave rows

The 871 row is the round 24 build `871-g32f9d6f`, squeezed in its family run `sl24-1`.
Round 24 refused it only for the Samanyu seed 504.
Its certified-file quench gave no further gain, and it entered the take at 20:39 UTC with 5.771e-06.

The 597 row came from the round 24 build `597-g175c71e`, 2.45e-06 above bar27, which round 24 never kicked.
A 450-second boxB midm kick found the old family 597 basin.
The row entered the take at 21:17 UTC with 9.242e-08.

The 976 row is a fresh build of this round.
Its far zone `796tw17.F1` was one of the modules that the Samanyu rule had blocked.
The build `976-g5270303` (corner `976tw17.C`, far zones `796tw17.F1` and `z9-19f720.F1`) built 2.25e-06 above the bar.
The boxD kick took it down one step at a time: +1.42e-08, +6.4e-10, -1.5e-11, -7.8e-11 and -1.95e-10 on bar27.
The row entered the take at 22:16 UTC with 1.458e-10.
Other builds of the same corner reached the same basin.

### Measured dead ends

The re-opened Samanyu inputs that gave no row:

| input | result |
|---|---|
| 648, round 24 build `648-gd1c0f1b` | its quench ended 1.5e-09 above the backlog 648 row |
| 503, round 25 family file | it certifies only 7e-11 below bar27, and a row needs 1e-10 |
| 932, round 26 build `932-g1388dc1` | it certifies 9.5e-07 below bar27 but 7.7e-09 above the quench r27 932 row |
| 922, 985, 921 and 814 near-bar builds of round 24 and 25 | kicks found nothing below their start |
| 813, round 24 build `813-gfde61d4` | the kick ended at +1.68e-08, the held 813 basin |

The kicks of fresh builds of this round stayed above the bar or above a live row:

| n | kicks | best result |
|---|---|---|
| 922 | 4 of corner `985ns25v319f1449.C~` | 2.27e-10 below bar27, but only 6.8e-11 below the live midm 922 row, so it was not staged |
| 987 | 3 | -4.91e-11 on bar27, the held basin |
| 812 | 2 | +1.69e-07 on the live backlog 812 row |
| 994 | 3 | +7.66e-07 on bar27 |
| 976 | 2 other builds | +2.25e-06 on bar27 |
| 985 | 3 | +5.9e-06 to +6.3e-06 on bar27 |
| 418, 704, 705, 931 | 8 | no find |

The forensics 986 rectangle near, 1.75e-04 of side above the bar, kicked to +5.56e-06 with no gain.
The round 24 build `973-g91a15f8`, which no round had kicked, gave no find.

### Traps

The k123 lane's text scan refused our 597 row.
The licence cell named the excluded 1105 file and its licence in the share-test record, and the scan read that as ancestry.
The measured share was 0.0017, far under the 0.4 limit.
The share record now gives only the number and the limit, and `tools/fixlic27.py` reworded the 597 and 871 cells.
The quench lane changed `quench_walk.py` the same hour to read such a text as a measure.
Never write the name of an excluded file in a source or licence cell, even to say that the row is clean of it.

The re-opened 932 stopped at files that round 26 had moved away for Samanyu reach only.
k123 dropped its 932 into `work/withdrawn`, forensics moved its copies into `work/quarantine-withdrawals`, and twoshort renamed its near files to `work/withdrawn/near-*`.
The walk reported them as missing parents.
`walk_refusal` now reads the moved copies for n = 932 only.
The 695 files of the same purge stay out, because they left for an unresolved prvsiyan source.

boxA ran at a load of 76 to 112 for the first two hours, and a local python process got under 1% of a core.
`modules.py grow` reads every one of the 3,200 near dirs before its seen check, and two growth steps did not finish in 900 seconds.
Growth now passes only the dirs whose `take.tsv` changed since the last completed cut, 120 at a time (`grow-seen27.json`).
After that change, a step cut 13 to 120 dirs and finished in minutes.

A generator batch repeated target 997 seven times, because no target completed within its 180-second limit.
The batch now skips such a target.

A boxD kick of `812-ge232c68` ended after 3 seconds with a SIGTERM from outside the lane, and no timeout.
Its `.started` and geometry markers went to `kicks/requeued`, and the kick worker ran it again.

### Work done

The round ran 30 growth steps, which added 529 modules.
After the incremental change, growth cut 41 times.
The results table lists 110 builds, all on boxD.
It lists 35 kicks, 17 on boxB and 18 on boxD.
The lane wrote 266 near layouts to `near/`.
All workers stopped by 23:45 UTC, and the last collect at 23:47 UTC published nothing new.
The box scratch was copied to `take-modules-r27/work/box-final` and checked by checksum, then removed.

Next, best first:

1. Run the generator again over the modules that the Samanyu rule had blocked, with each new cut.
   One pass over all 413 target n gave the 976 row and the closest 922 near.
   Both came from a module that the old rule blocked.
2. Before a kick, compare a build with the live rows of every lane as well as with the base bar.
   The 922 find was 2.27e-10 below bar27, but the midm row already sat 1.6e-10 below bar27.
3. Keep growth incremental while boxA runs above a load of 30.
   A full cut over 3,200 near dirs did not finish in 900 seconds at a load of 76 to 112.
4. Do not kick the 985, 812, 994, 987 and 418 builds of this round again unless the corner changes.
   The measured results are in the dead-end tables above.

## Round 28

Round 28 ran from 00:02 to 05:45 UTC on 2026-11-15 against `round28-briefs/bar28.tsv`.
The Samanyu-dev rule stayed lifted.
A rule change at 00:19 UTC made our own layouts and their descendants ours: a share match with a public file is no reason to refuse them.
The share test now applies only to rows whose first source is a public file that a lane fetched.
The [results table](../results/modules-r28-2026-11-15.tsv) lists the take row, every build of the round and every kick with its start and best score.

| n | bar28 | round 28 | gain | lowest live r28 row |
|---|---|---|---|---|
| 748 | 0.017461443370112573 | 0.01734222871800939 | 1.192e-04 | yes, the only live 748 at the end |

The row gains 1.192e-04 against bar28.
Rebuild had certified 748 at 0.017375064950233776 at 02:23 UTC, and its row left its take after ours entered.
So the row gains 3.284e-05 beyond the best other round 28 748 that was certified, and 1.192e-04 beyond the live takes at the end.
It had one certified-file fq quench on boxD before it entered the take at 03:04 UTC.

### What gave the row

The 748 row is the boxD build `748-g5941611`.
Its corner `805ns28v666c8e68.C~` was cut from a stair-c round 28 near of n = 805.
That near holds a far zone that stair-c cut from one of our own 805 kick nears.
The two far zones are the held modules `804h.F2` and `803h.F1`, with stacks 13 and 13 and the slp squeeze.
The build came out 3.26e-03 of side under the held 748, and its quench gave no further gain.
So a corner of a fresh deep layout of one n can move to an n 57 lower and keep most of its gain.

Four later builds of 748 on three other stair-c 805 corners reached the same basin, 1.2e-11 or less above the row.
A boxB midm kick and a boxD family kick of the row found nothing below it.
The two kicks returned the raw build itself, whose bounding score is 4.9e-11 under the certified score.

### Measured dead ends

| n | what ran | best result |
|---|---|---|
| 805 | boxB kick of build `805-g4b88601` on the forensics 805 rectangle corner | 0.016432367, then stair-c certified 0.0164305624 at 01:58 UTC with our near as its far zone |
| 805 | seven kicks of fresh builds on the stair-c 805 corners, and three chained kicks of their best finds | 0.0164300116 at best, 2.7e-07 above the rebuild 805 row 0.0164297372, and the chains found nothing |
| 812 | 15 kicks of 812 builds | `812-g5e13b26` reached 2.84e-09 under bar28, but harvest's fq follow of our near entered first at the same score, and the other 14 ended 1.0e-09 to 3.3e-06 above bar28 |
| 995 | two builds on a corner cut from the live 995 row | 1.3e-13 under that row, so a copy and not a gain |
| 871 | five kicks of builds on the new 871 corners | 4.9e-11 under bar28 at best, the bar basin |
| 932 | six kicks of fresh 932 builds | +7.609e-09 on bar28 each time, the bar basin |
| 748 | kicks of the builds `gd8d27b7` and `g98bdb17` on the forensics 805 corner | 0.0174192, 4.4e-05 above the rebuild 748 row |

`modules_publish28.py` now refuses a row that is not more than 1e-10 under every live take, the 995 copies included.

### Traps

`modules_tablejob24.py` runs as its own process on the boxes.
It imported `modules_policy24` without the round 27 lift, so it deferred every fresh cut whose source text reaches a Samanyu seed.
In round 27, 43 of 55 table jobs came back deferred.
In round 28 before the fix, 111 of 137 jobs on boxD and 36 of 38 on boxB came back deferred.
So most fresh cuts of round 27 never got a table, and the generator never saw them.
The box copies now run a wrapper that imports `modules_policy27` first.

The publish walk refused the 748 for one missing file, `take-forensics-r26/501.csv`.
A stair-c proof lists that file as a held-chain name of the held 986.
The assembler-style walk `rebuild_walk27.py` lets a held-chain name stay missing.
`walk_refusal` now does the same, and a file that a source names directly still blocks.

The forensics lane rewrote its 805 rectangle near after we cut a corner from it.
Our records pin the old sha256, so `rebuild_walk27.py` reports ten "changed since pinned" hits on the 748.
`modules_near27.py` names a snapshot by a hash of the path, not of the bytes.
So the rewrite also replaced our snapshot copy.
The old bytes survived only in a stair-c donor copy.
We kept them at `take-modules-r28/pins/805-rect-3905b3f6064dcafa.csv` and wrote a pin note in the 748 source cell and in the handoff log.
Snapshot names must carry the sha256 of the bytes, or a rewrite upstream breaks every record cut from them.

The publish walk refused the first 805 find for two missing `take.tsv` names in forensics feed records.
A missing `.tsv` no longer blocks, because the walk reads tables through the files they describe.

A local loop started with `/opt/homebrew/bin/python3` died on a missing `mpmath`.
Start the lane loops with the venv python.

Our certification line of 03:04 UTC named the WITHDRAW-line check of the walk.
`quench_walk.load_withdrawn` reads any line with the letters `withdr` as a withdrawal of the paths it names.
So it listed our own 748 as withdrawn.
A REINSTATE line at 05:02 UTC cancels that, and the publisher's handoff text no longer uses the word.
Never write that word in a handoff line about a row that stands.

The boxD kick worker takes the newest build first.
A kick queued by hand waited behind each fresh build until its files were touched.

### Work done

Pending table jobs of the round 28 cuts grew from 118 to 140 between 03:22 and 03:53 UTC.
In the same time, boxB kicks of fresh 932 builds kept returning to the bar basin.
A table job takes 2 to 40 seconds.
So from 03:53 UTC boxB ran only priority kicks and table jobs, and the table list was split between the two boxes.
The round ran 63 growth steps, which added 946 modules.
boxB solved 335 table jobs and boxD 245.
The results table lists 171 builds, all on boxD.
It lists 58 kicks, 22 on boxB and 36 on boxD.
The lane wrote 246 near layouts to `near/`.
All workers stopped at 05:45 UTC, and the box scratch came back to `work/box-final` before the boxes were cleaned.

## Round 29

Round 29 ran from 06:02 to 11:45 UTC on 2026-11-15 against `round29-briefs/bar29.tsv`.
For each n, that bar is the lower of the held round 27 b row and the best certified round 28 take row.
The Samanyu-dev rule stayed lifted, and our own layouts stayed ours, so no share gate ran on them.
The [results table](../results/modules-r29-2026-11-15.tsv) lists the take rows, every build of the round and every kick with its start and best score.

Round 29 gave no row.
No build and no kick came more than 1e-10 under bar29, so `take.tsv` holds only its header.
The closest builds are copies of the bar basins.
The best one, `976-g1f93da5`, is 1.9e-9 of side under the bar, which is 6.1e-11 of score.

### What changed in the tools

`take-modules-r29/work/setup29.py` made four lane files from the round 28 files.
Each change answers a measured round 28 lesson.

- [`modules_round29.py`](../modules_round29.py) certifies box results with the bisected dilation of `tools/border/r28/finesafe.py`.
  It posts no near for a build that it stages for its own quench.
  On the box, the kick worker runs injected records before fresh builds.
- [`modules_publish29.py`](../modules_publish29.py) certifies with `finesafe` too, against `bar29.tsv` and every live `take-*-r29` dir.
- [`modules_policy29.py`](../modules_policy29.py) reads the round 29 bar, takes and handoff log.
  Its checks are the round 28 checks.
- [`modules_near29.py`](../modules_near29.py) keeps every version of a near snapshot.
  When an upstream near file changes after we took a snapshot, the new bytes get a new dir named by their sha256, and the old dir stays.

The table lists are split between the two boxes from the start (`tools/tabfirst29.py`, every 5 minutes).
The round 29 cuts come first, then the round 28 cuts that never got a table.
On boxD the kick worker runs a table job before each kick (`MODULES_KICK_TABLES_FIRST=1`).
It kicks only builds within `MODULES_KICK_WINDOW` of side of the bar (3e-5 from 08:33 UTC).
From 08:07 UTC boxB builds generator targets that `tools/mmbuildfeed29.py` claims on boxD.

Controls, all measured:

- `finesafe` certified the round 28 kick file `748-799fcd49f-p28-748-lkick-28-1` at e = 2.18e-11, against e = 5e-11 for the ladder.
  That is 7.6e-10 of side lower.
  `modules_publish29.py --dry` then refused the file, because its margin on bar29 was 2.77e-11 and a row needs 1e-10.
- A boxB midm kick took a loose n = 3 from side 2.1 to 2.000000000001 in 20 seconds.
- `modules_near29.py` gave six rewritten forensics round 29 near files new snapshot dirs, for example `nforensics-r29v29f92177s2ff9eae9`, and kept the old dirs.

### Measured dead ends

| n | what ran | best result |
|---|---|---|
| 976, 996, 804, 748 | builds on round 27 to 29 corners with held far zones | 1.3e-9 to 1.9e-9 of side under bar29, the bar basins, and 6.1e-11 of score at most (a row needs 1e-10) |
| 994 | build `994-gff08b4c`: corner `931ns29v3ff45b8a.C` with two `994cl19.F2` far zones, the best generator prediction of the round (5.1e-5 of side over the held 994) | 1.16e-4 of side over the held 994 |
| 994 | two kicks of 994 builds | +7.66e-07 of score on bar29, the round 27 basin |
| 871 | three kicks of fresh 871 builds | -4.89e-11 on bar29 at best, the round 28 bar basin |
| 932 | two boxB kicks | +8.40e-09 on bar29 at best, the round 28 basin |
| 418, 805, 813, 931, 996 | 14 kicks | +5.0e-07 to +5.8e-06 on bar29, or no find |
| 90, 454, 582, 848, 907 | the growth step `j0323` on the round 29 take rows of harvest and invent | no corner: the cutter answered "no two flush arms" for each |

All kicks were midm_scan `lkick,kick` at sigma 0.02 for 450 s.
Every kick of the round ended in a round 27 or round 28 basin or found nothing.
So from 08:07 UTC boxB ran builds, and from 08:33 UTC the boxD kick slot kicked only builds within 3e-5 of side of the bar.

### Traps

The soft provenance trace refused every round 29 take row of another lane.
`modules_near29.py` reached the trace through `modules_policy27`, which cannot read the records of the round 28 and 29 lanes.
It refused harvest 848 (Apache 2.0, a gain of 4.9e-4), harvest 90, invent 907 and our own round 28 748.
So until 07:54 UTC no take row of another lane reached the cutter.
`modules_policy29.trace29` now reads the `take.tsv` row of such a file.
It refuses the row when its text names an excluded source.
It also refuses a public-first row whose licence is not Apache 2.0, CC BY 4.0 or CC0, or whose share with the prvsiyan row is 0.4 or more.
Any other row passes as an own chain.

A build follows each generator batch, and a build takes 1 to 8 minutes against about 5 seconds for a batch.
At 08:45 UTC 110 generator tasks were waiting, and only one had finished in the round.
`MODULES_GEN_BATCHES_PER_BUILD=8` now runs eight batches for each build.

The box worker takes the newest generator task first, by its name.
The task of the first round 29 cut, `j0275`, holds 95 modules from the round 28 take and near dirs.
At 09:08 UTC it stood at target 24 of 414, behind 110 newer tasks.
We renamed it `z0275`, so it ran first, and it finished at 09:21 UTC.
The next round should order the tasks by their number of modules.

Both box workers run in the same dir.
`tools/restartkick29.sh` picks the children to kill by their working dir, so it also killed the `fq` of a running build.
That build was lost.
Kill a worker by its process group, not by its dir.

BSD `sed` has no `\?` in a basic regex.
A rename by `sed 's/28d\?/29/'` kept the old name, and the redirect `> $g` then emptied the source file.
We made the round 29 tools again from the frozen round 28 copies.
Check that a new name differs from the old one before you redirect into it.

A table split by list position moved jobs between the boxes as the list got shorter.
`tools/tabfirst29.py` now splits by the job hash: one job in four goes to boxB and three to boxD.
There a table takes 2 to 40 seconds, against about 90 seconds on boxB.
When boxB holds fewer than 8 jobs, it also takes the oldest quarter of the boxD list.

### Work done

The table backlog was 182 jobs at 06:43 UTC and 0 from about 08:25 UTC.
The round ran 138 growth steps (`j0275` to `j0412`), which added 1388 modules.
boxB solved 194 table jobs and boxD 383.
The results table lists 249 builds, 173 on boxD and 76 on boxB.
It lists 21 kicks, 13 on boxD and 8 on boxB.
The lane wrote 269 near layouts to `near/`.
All workers stopped at 11:45 UTC, and the box scratch came back to `work/box-final` before the boxes were cleaned.

## Round 30

Round 30 ran from 12:02 to 17:45 UTC on 2026-11-15 against `round30-briefs/bar30.tsv`.
For each n, that bar is the lower of the held round 28 b row and the best certified round 29 take row.
The Samanyu-dev rule stayed lifted, and our own layouts stayed ours, so no share gate ran on them.
The [results table](../results/modules-r30-2026-11-15.tsv) lists the take rows and every build of the round with its start and its result.

Round 30 gave no row.
No build came more than 1e-10 of score under bar30 and under every live round 30 take, so `take.tsv` holds only its header.
The closest builds are copies of the bar basins.
The best one, `996-gd83cfb6`, is 1.55e-9 of side under the live bar, which is 4.9e-11 of score.
The round ran 280 builds, 165 on boxD and 115 on boxB.

### What changed in the tools

`take-modules-r30/work/setup30.py` made four lane files from the round 29 files:
[`modules_round30.py`](../modules_round30.py), [`modules_policy30.py`](../modules_policy30.py), [`modules_publish30.py`](../modules_publish30.py) and [`modules_near30.py`](../modules_near30.py).
They read the round 30 bar, takes and handoff log.
Three changes answer round 29 lessons:

- The box generator alternates its picks.
  One batch goes to the task with the most modules, and the next batch goes to the newest task.
  Round 29 measured the deep cut `j0275` (95 modules) at target 24 of 414, behind 110 newer tasks.
- No slot kicks a build (`MODULES_KICK_WINDOW=-1`).
  The second boxD worker runs certified-file quenches, then tables, then builds.
  All 21 round 29 kicks ended in a round 27 or round 28 basin or found nothing.
- The table lists stay split by job hash (`tools/tabfirst30.py`), with the round 30 cuts first.

Two more changes come from round 30 measurements:

- `certify` checks a cached result again when its cached score is under the current bar.
  bar30 rose above bar29 at 995, so eleven of our round 29 builds sat 1.81e-4 of side under bar30.
  The stair-c round 30 row holds 995 2.8e-11 under our best certified copy, so none of them gives a row.
- From 14:56 UTC the boxD generator runs 32 batches for each build, up from 8.
  By 14:55 UTC 116 builds had given no row, and the best ranked build stood 2.1e-4 of side over the bar.
  Every prediction under the bar came from new generator output.
  A batch takes 5 to 10 seconds, so with 8 batches for each build the generator had about 30% of the worker.

Controls, all measured:

- Task order: the build worker ran `j0404` (85 modules) first, then alternated the first round 30 cut `j0435` with `j0404`.
- No kicks: the second boxD worker went to builds and tables.
- Certify again: the cached file `995-g66aa9c9` gives "certify again" against bar30 and "skip" against the live stair-c 995 row, so the check goes both ways.
- With 32 batches for each build, the generator wrote 65 batch files in 9 minutes, against about 24 at 8 for each build.

### Measured dead ends

| n | what ran | best result |
|---|---|---|
| 996, 873, 871, 748 | builds on round 28 to 30 corners with held far zones | 1.1e-9 to 1.55e-9 of side under the live bar, the bar basins, and 4.9e-11 of score at most (a row needs 1e-10) |
| 602, 705, 759 | 9 generator rows on the turned corner `704nf29v76da6d4d.C~t`, predicted 4.8e-3 to 5.0e-3 of side under the held layout | no start: the corner does not fit under both arms, so `rank21.py` drops the corner |
| 306, 342, 380, 507, 553, 652, 704, 705, 815, 873, 934 | generator rows on a second turned corner, `931ns30v253cf871.Ct`, predicted near 5.0e-3 of side under the held layout | no start in 3 builds (342, 652): the corner does not fit under both arms, so `rank21.py` drops it |
| 748 | 26 builds, among them the corner `805nm29v264a900b.Ct` predicted 5.0e-7 of side under the held 748 | 1.1e-9 of side under the held 748 at best, 3.9e-11 of score |
| 995 | eleven round 29 builds certified again on bar30 | 2.8e-11 of score over the stair-c round 30 row |
| 695, 694, 642, 546, 646, 640, 416 | bar30 rose here after the round 28 skeptic drops | no corner: no two flush arms (at 646 the rest grid breaks), so the generator has no task |

### Where the cutter works

The cutter needs a corner with two flush arms and a rest grid beside them.
`tools/domain30.py` ran it on the held round 28 b file from n = 30 to 1000.
It cuts 71 of 971 rows, and 890 have no two flush arms.
It cuts no row under 300.
Per band of 100, it cuts 4 rows in the 300s, 4 in the 400s, 7 in the 500s and 7 in the 600s.
It cuts 10 rows in the 700s, 19 in the 800s and 20 in the 900s.
Of the 33 round 29 take rows, 3 cut and 4 have one flush arm.
Of the 40 newest forensics round 30 rectangle nears, 2 cut and 3 have one flush arm.

Two round 29 items stayed out:

- A cutter for one flush arm would open at most 4 of the 33 take rows and 3 of the 40 nears.
  It also needs a new module kind in `cut()`, the tables and the generator.
- A new calibration for corners moved to another n is not needed.
  Over 730 builds of rounds 26 to 29, moved corners and same-n corners finish under the held layout at similar rates (57 of 317 and 81 of 382).
  Every build more than 1e-3 under the held layout was also predicted more than 1e-3 under it.

### Traps

The local loop and the 60-second fast collect both run `certify`, and both wrote `certcache.json.tmp`.
At about 13:29 UTC one process renamed the file away from the other, and the local loop stopped with `FileNotFoundError`.
`atomic()` now names the temporary file by the process id, and `tools/keeplocal30.sh` restarts the local loop when it stops.

`setup30.py` did not copy `state.offset`.
So the first collect appended the 3555 round 29 box log lines to the round 30 `STATE.txt`.
STATE is append only, so the lines stay, with a note after them.

### Work done

The round ran 103 growth steps (`j0435` to `j0537`), which added 1289 modules.
boxD solved 306 table jobs and boxB solved 132.
The lane wrote 552 near layouts to `near/`.
The first agent hit a usage limit at 17:16 UTC.
A revived agent adopted the drivers, and all workers stopped at 17:45 UTC.
The box scratch came back to `work/box-final` with no checksum difference before the boxes were cleaned.

### Next

- Stop the lane, or give it a new design, and move its three slots to the lanes that gave rows in round 30.
  Rounds 29 and 30 ran 529 builds and gave no row, and every build near the bar ended in the bar basin.
- If the lane goes on, the generator must drop a turned corner that does not fit under both arms before it ranks.
  All 42 round 30 generator rows more than 1e-3 under the held layout came from two such corners, at 14 n.
  None of their builds started.
