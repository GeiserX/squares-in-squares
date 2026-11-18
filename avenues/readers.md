# Avenue: readers (2026-11-12, rounds 12 to 14)

Round 13 and round 14 are at the end of this file. Round 13: 8 n certified for 3.6556e-4, and a cut at the closest pair of layers for layouts without twins. Round 14: 13 n certified for 3.5505e-4, most from walks on the jonathan1506 layouts.

**Result: 15 n certified below the bar, for 5.2646e-4 of score against `gate/cand-round11-1111b`. 8 start from the two target classes and 7 from other refused layouts that the new reader takes. One layer reader serves both kinds: it reads 49 of the 51 one-direction layouts, all 36 not-flush layouts and 117 of the 188 other refused layouts. Where both arms have twin layers, the step is exact: down then up gives back 339, 417 and 462 within 1e-7 of their held sides. A true one-arm layout would step by 2m squares on the line k - m, and none of the held layouts from 300 up is one. Nothing was submitted from here.**

This avenue had one job: give the family step two new readers, so that it can start from layouts that the readers of [`family_step.py`](../family_step.py) refuse. The first is for layouts with pairs of stacks along one wall direction only. The second is for layouts whose arm strips hold more than one stack across. Both are one reader in the code, the layer reader of [`family_readers.py`](../family_readers.py), because both kinds read as two arms once the reader asks for layers instead of stacks.

Words used here: "held" is `gather/round11-2026-11-11b.csv` (gate dir `gate/cand-round11-1111b`). The side is `L = m + f` with `m` whole, and `k = n - m²`. A "stack" is a row of tilted squares set face to face. A "strip" is the band of an arm, from its wall to the grid. A "layer" is every square of a strip whose centre lies in one band of width 1 across the strip. "g" is the number of upright grid squares beside a layer, so the strip is `s - g` wide. Two layers are "twins" when every square of one is the square of the other moved along the wall by one spacing `d`, to `TWIN` in place and in angle. "The bar" of an n is the lowest of its held side and its sides in the take dirs `take-family-r11`, `take-family-r12`, `take-modules-r11` and `take-zones-r11`.

## 1. What the family readers refuse today

We counted the held file again. It has 701 n from 300 up.

| class | n |
|---|---|
| plain grid | 288 |
| read by the strict reader | 75 |
| read by the wide reader | 35 |
| read by the wide reader with `SQ_LOOSE=1` | 28 |
| no pair of stacks of 3 or more | 174 |
| pairs of stacks of 5 or more, along one wall direction only | 51 |
| pairs along both directions, stacks not flush (strips more than one stack across) | 36 |
| pairs only of stacks shorter than 5 | 11 |
| flush pairs along both directions, away from the walls | 3 |

The round 11 count was 61 and 49 for the two target classes, on the round 10 file. The held file moved, and the wide and loose readers now take 4 and 4 more. `work/classes.tsv` in the take dir has the class of every n.

## 2. One-arm layouts

### The step for a true one-arm layout

Take a layout with one arm on the left wall and the upright grid everywhere else. The strip is `E = s - g` wide, and the grid has `g` columns of `m` squares. One shell is:

- one layer of the arm, `w` squares. A flush layer holds `w = m + 1 - g`: one stack of `c = m + 1 - g` squares spans `c - 1 + f`.
- one full grid column, `m` squares.
- one grid row of the grid part, `g` squares.
- The row and the column share one square.

So one shell is `w + m + g - 1 = 2m` squares, and not `2m + 1`. The step takes n to `n - 2m`, and `m` to `m - 1`. Then `k` goes to `k - 1`, so a one-arm layout walks on the line `k - m` constant, not on `k - 2m`. One shell up adds `2m + 2`.

The cut goes across the strip along the layer, through the grid along the row, and down the grid along the column. Everything beyond the layer and the row moves in by 1 along the wall. Everything beyond the column moves in by 1 across. The side across the arm is `E + g - 1 = s - 1`. Along the wall, the strip loses a layer of thickness `p = 1 / cos t` and closes by 1, so a slit of `p - 1` stays. The grid part has `m - 1` rows in `s - 1`, so it keeps a slack of `f`. The side is `s - 1` as built, and `f` stays. The squeeze then turns the slit into tilt, as in the family step. Both ends of the single arm are free ends at a wall.

### None of the held layouts is one

A one-arm layout leaves the slack `f` of the grid unused along the wall. A second arm on the other wall uses it. So we looked for true one-arm layouts and found none from 300 up:

- 49 of the 51 layouts of the class read as two arms with the layer reader. The second wall holds tilted squares too, but its stacks are shorter than 5 or are broken by shear, so the stack finder of `frontier_stacks.py` sees pairs in one direction only.
- The 2 others, 332 and 739, are a block and a band at about 45 degrees, away from the walls.
- In the other classes, 26 layouts have a layer of the right count on one wall only. All of them are bands, blocks or diamonds at about 45 degrees, away from the walls: [`readers-img/onewall-1.png`](readers-img/onewall-1.png) and [`readers-img/onewall-2.png`](readers-img/onewall-2.png) show all 28.

So there is no donor for the step on the line `k - m`, and we did not write it as code. The class is a two-arm class, and the layer reader below is its reader.

## 3. The layer reader and its cut

### The cut

The reader does not ask for stacks. It asks for a cut window: a band of width 1 across a strip, along the row axis of one tilted square. The layer of the window is every square of the strip whose centre is in the band.

- The strip of arm 1 is `x < E1 = s - g1`, where `g1` upright squares of the grid stand beside the layer. A layer must hold `m + 1 - g1` squares: one more than the `m - g1` upright columns it replaces.
- Every tilted square is the seed of a window, at seven offsets across the band. The reader keeps a window only when its layer has the right count. It takes the arms of the turn with the most layers on both walls.
- **down** takes out one layer per arm, one grid row and one grid column, and moves everything beyond each cut in by 1. The count is `(m + 1 - g1) + (m + 1 - g2) + g1 + g2 - 1 = 2m + 1`, as for the family step, so the result is on the same line `k - 2m`.
- **up** puts in a copy of one layer per arm, moved along the wall by a spacing, one more grid row and one more grid column.
- It does not guess. `family_step.py`'s own `down()` and `up()` check the count, the side (`L - 1` to 1e-7) and the smallest gap of each cut.

**One stack of each tier, not one tier.** In a strip more than one stack across, a straight window takes one stack (or a part of one) from each tier, plus any upright square at the wall. At 701 the cut layer of arm 2 is a stack of 6 at 18.5 degrees and a single square at each end, at 18.1 and 17.8 degrees: 8 squares with `g2 = 19`. At 502 the cut layer of arm 1 holds 10 squares with `g1 = 13`: 8 at 18.4 degrees, an odd square at the wall (4.6 degrees) and one at the grid (14.3 degrees). Its stacks are offset along the wall, so the band takes 2 squares of one stack and 6 of the next. Taking out one whole tier along the wall would change the width of the strip by a whole stack, which is not one shell. So the geometry allows only the cut across the strip. The down step builds from 29 of the 36 layouts of this class, and from 37 of the 51 of the one-direction class. As built, the side is `L - 1` to 1e-7 in every one (the check of `down()`). 23 of the 29 and 30 of the 37 are legal as built. The others overlap by at most 1.3e-3 and 3.1e-3, which the first exact LP repairs. The up step opens the box by the spacing of the copy: a median of 0.095 and 0.099 more than one unit, against about 0.05 for the clean stacks of the family step.

### Which layer: two derivations

**First derivation: any layer, the copy at its clearance.** The up step copies a layer near the middle and moves it by the smallest move that clears the layer of its own copy (1 / cos t for a clean stack). The control fails:

| held n | class | round trip after the LP | after fq and the LP | held side |
|---|---|---|---|---|
| 500 | one direction | +2.07e-3 | +1.77e-3 | 22.848451004 |
| 502 | not flush | +1.10e-2 | +2.64e-3 | 22.877637088 |

The round trip is the down step as built, then the up step from that layout as built, then the squeeze. The reason is in the layers. In these arms, no two neighbouring layers are twins. The best twin defect of a layer is 6e-2 in arm 1 of 500 and 5e-2 in arm 1 of 502. So the copy differs from the layer the down step took out, and the arm gets a contact it did not have. The arm is jammed: after the round trip at 500 the load-carrying contacts are 117 in the strip beyond the cut, 53 before it, 15 at the new layer and 75 in the grid. A misfit of the copy goes straight into the side.

**Second derivation: twin layers.** A cut at a layer that has a twin keeps every contact type of the arm. Down, the twin takes the place of the layer that goes. Up, the copy goes in at the twin spacing `d`, which is the contact the layer already has with its twin. So the round trip gives back the same layout. The reader takes twins first where both arms have them, the closest twins first, and falls back to the first derivation where they do not. `SQ_TWIN` sets the tolerance. The default is 1e-2, and every run here used it.

| held n | class | twin defect, arm 1 / arm 2 | after the LP | after fq and the LP | held side |
|---|---|---|---|---|---|
| 814 | strict (a check of the code) | under 1e-8 / under 1e-8 | +4.2e-9 | not needed | 28.944429709 |
| 339 | not flush | 2.4e-3 / 6.3e-3 | +1.78e-7 | -9.0e-10 | 18.906198209 |
| 417 | one direction | 8.9e-3 / 2.4e-3 | +1.29e-8 | not needed | 20.897143045 |
| 462 | one direction | 9.0e-3 / 4e-15 | +5.00e-5 | -9.2e-10 | 21.948832406 |

All four come back to a legal layout of the same n within 1e-7 of the held side, and floatsafe passes on each. The sequential LP alone does it at 814 and 417. At 339 and 462 it ends 1.8e-7 and 5.0e-5 above, and the fq quench of `finish()` with the LP after it closes the rest. One control was refused: at 341 the up step from the layout as built found no full grid line within 3 of the cut (5.7).

**The plain grid is refused.** 324, 399, 400, 900 and 961 read as `plain grid` before the layer search starts.

**What has twins.** At `TWIN = 1e-2`, 11 of the 36 not-flush layouts and 3 of the 51 one-direction layouts have twins in both arms. The others take the first derivation, whose control fails. Their steps still run, and the certification decides.

## 4. The steps

Every layout of the two classes that the reader takes, one shell up and one shell down, upward first and the layouts with twins first. Then the same for the other refused layouts that the reader takes. Each step uses `SQ_APART=3e-2`, then the fq quench and the LP of `finish()`. A walk goes on from each result and ends a direction after two steps in a row that do not end below the bar. A step has a time limit of 600 s. The runs used 2 processes on boxA and 2 on boxD.

| start class | twins in both arms | direction | steps | built | refused | below the bar | certified | median of side less bar |
|---|---|---|---|---|---|---|---|---|
| one direction | no | down | 30 | 28 | 2 | 0 | 0 | +9.67e-03 |
| one direction | no | up | 17 | 17 | 0 | 2 | 1 | +4.99e-03 |
| one direction | yes | down | 5 | 5 | 0 | 0 | 0 | +2.42e-03 |
| one direction | yes | up | 7 | 7 | 0 | 1 | 1 | +4.54e-03 |
| not flush | no | down | 12 | 12 | 0 | 1 | 1 | +1.29e-02 |
| not flush | no | up | 7 | 7 | 0 | 0 | 0 | +6.32e-03 |
| not flush | yes | down | 24 | 24 | 0 | 3 | 3 | +4.41e-03 |
| not flush | yes | up | 18 | 17 | 1 | 3 | 2 | +2.06e-03 |
| other refused | no | up | 102 | 88 | 14 | 9 | 7 | +3.56e-03 |
| all | | | 222 | 205 | 17 | 19 | 15 | |

"Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule: floatsafe at 2.2e-11 and a score more than 1e-10 below the held score and below the same n in the four live take dirs. 4 steps hit the 600 s limit and kept the last legal layout. Refused steps, by reason: 13 a layer does not clear its own copy within one more unit; 1 no grid line with full neighbours at the cut; 1 the nearest full grid line is 6.2 from the cut; 1 the nearest full grid line is 11.4 from the cut; 1 the nearest full grid line is 11.6 from the cut.

**Certified results.**

| n | step | start | held side | new side | score gain |
|---|---|---|---|---|---|
| 421 | 1 shell up | the held packing of n = 380 (no stack pairs) | 20.974562481 | 20.973809486 | 3.670e-05 |
| 497 | 1 shell up | the held packing of n = 452 (no stack pairs) | 22.785719200 | 22.781963852 | 1.685e-04 |
| 502 | 1 shell up | the held packing of n = 457 (one direction) | 22.877637088 | 22.877574428 | 2.797e-06 |
| 507 | 1 shell up | the held packing of n = 462 (one direction) | 22.964856206 | 22.964157198 | 3.104e-05 |
| 509 | 1 shell up | the held packing of n = 464 (no stack pairs) | 22.989777094 | 22.989525419 | 1.116e-05 |
| 546 | 1 shell down | the held packing of n = 595 (not flush) | 23.850548604 | 23.848812668 | 7.429e-05 |
| 594 | 1 shell up | the held packing of n = 545 (no stack pairs) | 24.848784543 | 24.848748092 | 1.496e-06 |
| 597 | 2 shell down | the held packing of n = 701 (not flush) | 24.896925855 | 24.895083137 | 7.542e-05 |
| 648 | 1 shell down | the held packing of n = 701 (not flush) | 25.904480193 | 25.903930146 | 2.161e-05 |
| 706 | 1 shell up | the held packing of n = 653 (no stack pairs) | 26.987838098 | 26.987368527 | 1.767e-05 |
| 756 | 1 shell up | the held packing of n = 701 (not flush) | 27.921468853 | 27.921468610 | 8.840e-09 |
| 818 | 1 shell up | the held packing of n = 761 (no stack pairs) | 28.998573871 | 28.997919803 | 2.287e-05 |
| 870 | 1 shell down | the held packing of n = 931 (not flush) | 29.923478757 | 29.923030157 | 1.521e-05 |
| 926 | 1 shell up | the held packing of n = 865 (no stack pairs) | 30.874142317 | 30.873274688 | 2.851e-05 |
| 994 | 1 shell up | the held packing of n = 931 (not flush) | 31.940848799 | 31.940242417 | 1.923e-05 |
| total | | | | | 5.2646e-04 |

## 5. The reach of the layer reader

The layer reader on every n from 300 up of the held file, with `SQ_TWIN=1e-2` (`work/reach.tsv` in the take dir). "Read" means the reader finds layers of the right count on two neighbouring walls and full grid lines beside them. "Built" means the step passes the checks of `down()` or `up()` as built, before any LP. The step itself may still be refused later, at the repair of the start.

| class | n | read | twins in both arms | down built | down legal as built | up built | up start overlaps by more than 5e-3 |
|---|---|---|---|---|---|---|---|
| one direction | 51 | 49 | 3 | 37 | 30 | 38 | 2 |
| not flush | 36 | 36 | 11 | 29 | 23 | 29 | 4 |
| other refused | 188 | 117 | 2 | 55 | 48 | 53 | 5 |

| refusal | one direction | not flush | other refused |
|---|---|---|---|
| up: a layer does not clear its own copy within one more unit | 9 | 6 | 59 |
| down: the nearest full grid line is N from the cut | 11 | 7 | 48 |
| read: no cut window: a window with the right count on no wall | 0 | 0 | 46 |
| read: no cut window: a window with the right count on one wall only | 2 | 0 | 18 |
| down: the cut is not clean: side N (want N), smallest gap N | 0 | 0 | 9 |
| read: no cut window: layers on two walls but no full grid row or column beside them | 0 | 0 | 7 |
| down: no grid line with full neighbours at the cut | 1 | 0 | 5 |
| up: the nearest full grid line is N from the cut | 2 | 1 | 1 |
| up: the opened layout overlaps: smallest gap N at side N | 0 | 0 | 4 |

- "A layer does not clear its own copy within one more unit": the layer is not one band across the strip. It is a window that happens to hold the right count, at a layout whose tilted squares do not form an arm (blocks at 45 degrees, floating groups).
- "The nearest full grid line is N from the cut": the grid beside the arms is broken by a third tilted group, so no grid row or column runs whole near the cut.
- The 288 plain grids are refused before the search. The strict, wide and loose classes are left to `family_step.py`, which reads them already.

## 6. Pictures

One layout of each kind before and after one shell down. The cut squares are white.

- One direction, 500: [`readers-img/500-down.png`](readers-img/500-down.png)
- Not flush, 502: [`readers-img/502-down.png`](readers-img/502-down.png)
- A certified step, 701 down to 648 at a twin cut: [`readers-img/701-to-648.png`](readers-img/701-to-648.png). The cut layer of arm 1 is one clean stack of 8. The cut layer of arm 2 is a stack of 6 with a single square at each end.

## 7. Next runs

1. **Finish the walks.** At the deadline, list A2: 39 of 57 did not start (39 up); list B: 81 of 157 did not start (1 up, 80 down). The lists are `work/walks-A2.tsv` (boxA) and `work/walks-B.tsv` (boxD) in the take dir, and a walker skips the walks its rows file already holds. The command is `SQ_TWIN=1e-2 SQ_APART=3e-2 family_readers.py walk LIST donors details.csv OUT --mod 2,R --deadline FILE --misses 2 --beat TAKE.tsv ...`. Under a load of 20, boxA needed 4 to 10 minutes for one upward step above n = 800, and two of them hit the 600 s limit. boxD took 5 to 50 s for a step below n = 600. Give the large n to the faster box.
2. **Read the public donors with the layer reader.** Round 11 scanned the harvest with the wide reader and found 300 donors. The layer reader takes most of the layouts that the wide reader refuses, so the same scan with `read_layers` should find more donors near the held side.
3. **Layouts without twins.** 25 of the 36 not-flush layouts and 46 of the 49 one-direction layouts have no twins at 1e-2. For them the cut falls back to the first derivation, whose round trip loses 1.8e-3 to 2.6e-3. Their steps still certify sometimes (546 from 595). Measure a cut at the closest pair of layers (the smallest defect, up to 6e-2) with the same control.
4. **Walk on from the certified results.** `family_step.py walk` reads with `read_any`, which does not take most of these layouts. The walk of `family_readers.py` does, and it goes on from every result.
5. **The 45-degree layouts.** 28 n from 300 up are bands, blocks or diamonds at about 45 degrees. No reader of the family step takes them, and they need a step of their own.

## Files

| file | what it is |
|---|---|
| [`family_readers.py`](../family_readers.py) | the layer reader, the twin cut, `read`, `reach`, `ctl`, `walk`, `take` |
| [`results/readers-r12-2026-11-12.tsv`](../results/readers-r12-2026-11-12.tsv) | every step of this round |
| `<scratch>/bounties-squares/take-readers-r12/` on boxA | the take dir: one csv per certified n and `take.tsv` |
| `<scratch>/bounties-squares/take-readers-r12/work/` | classes, reach table, walk lists, control logs, rows per box |

## Summary

- One layer reader serves both target kinds. It asks for a band across each strip that holds `m + 1 - g` squares, not for stacks. It reads 49 of the 51 one-direction layouts and all 36 not-flush layouts. The down step builds from 37 and 29 of them, at side `L - 1` and on the line `k - 2m`.
- A true one-arm layout steps by `2m` squares on the line `k - m`. No held layout from 300 up is one: the class is two-armed, and the layouts with a window on one wall only are 45-degree bands, blocks and diamonds.
- The cut takes one band across the strip, so one stack (or a part of one) of each tier. Cut at a twin layer, the round trip is exact: 814, 339, 417 and 462 come back within 1e-7. Cut anywhere else, it loses 1.8e-3 to 2.6e-3 (500, 502), because no two neighbouring layers there are alike.
- 222 steps ran, 205 built, 15 certified for 5.2646e-4 of score: 11 upward and 4 downward. The take dir holds them. Steps from layouts with twins certified 6 times in 54, and steps from layouts without twins 9 times in 168.
- **Next:** the main session can merge the take dir. Then finish the walks (39 upward walks on list A2 did not start), and read the public donors with the layer reader.

---

# Round 13 (2026-11-12)

**Result: 8 n certified, for 3.6556e-4 of score against `gate/cand-round12-1112a`. 4 come from held packings walked up (868, 928, 991, 994). 3 come from public donors that only the layer reader reads (604, 655, 739), and 739 alone gives 2.5e-4. 1 comes from a round trip at a closest-pair cut (548). A layout without twins can now be cut at its closest pair of layers. The round trip comes back within 1e-7 of the held side while the worse arm's defect is under about 4e-2. Nothing was submitted from here.**

Words used here: "held" is now `gather/round12-2026-11-12a.csv` (gate dir `gate/cand-round12-1112a`). "The bar" of an n is the lowest of its held score and its score in every take dir of round 13 that existed at the take. These were `take-border-r13`, `take-corners-r13`, `take-family-r13`, `take-gadget-r13`, `take-modules-r13`, `take-polish-r13` and `take-soft-r13`, at 05:27 UTC. The take dir is `take-readers-r13` on boxA.

## 1. The walks

The lists were what round 12 left, plus the walks on from its 14 results:

- 39 upward walks of list A2 and 81 walks of list B (1 up, 80 down) that did not start in round 12.
- The 14 n of round 12 that came from the layer reader (421, 497, 502, 507, 509, 594, 597, 648, 706, 756, 818, 870, 926, 994), one shell up and one down from their held packings. Where round 12 already walked on in the same direction, the walk now starts from the held packing, with the layer reader first. Round 12 did not do that after its first step. 994 up leaves the range.
- That makes 49 upward and 87 downward walks. Every donor is the held packing of round 12.

The walks ran with `SQ_APART=3e-2`, the fq quench and the LP of `finish()`, and the 2-miss stop rule, from 04:01 to 05:25 UTC. Upward walks came first, the largest n first, and the n from 640 up went to boxD (2 processes). boxA (1 process) took the rest after the scan of section 2 and the controls of section 3. The public pairs of section 2 were dealt in between, one public pair after each held walk. From 04:14 UTC the walks cut at the closest pair of layers (`SQ_TWIN=5.5e-2`, section 3). The rows before that used `SQ_TWIN=1e-2`.

132 steps ran, in 73 walks: 33 from held packings and 40 from public donors (section 2). 17 upward held walks, 45 public pairs and all 87 downward walks did not start before the deadline. No step hit the 600 s limit.

| start | direction | steps | built | refused | below the bar | certified steps |
|---|---|---|---|---|---|---|
| held, from a round 12 result | up | 19 | 16 | 3 | 1 | 1 |
| held, from a round 12 result | down | 1 | 0 | 1 | 0 | 0 |
| held, list left from round 12 | up | 38 | 37 | 1 | 6 | 4 |
| public donor | up | 74 | 68 | 6 | 5 | 4 |
| all | | 132 | 121 | 11 | 12 | 9 |

"Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule. It needs floatsafe at 2.2e-11. It also needs a score more than 1e-10 below the held score and below the same n in every take dir of round 13. Three steps below the bar do not certify. 596 from 547 and 685 from 632 sit only 1e-9 under it (5e-11 of score). 927 from 866 certified at 04:55 UTC, but `take-corners-r13` now holds a better 927. The 9 certified steps are on 7 n. The take keeps the best of each.

**Certified results.**

| n | step | start | held side | new side | score gain |
|---|---|---|---|---|---|
| 548 | round trip | the held packing of 548 (one direction), cut at its closest pair (defects 4.4e-3 / 5.0e-2) | 23.872557388 | 23.872518109 | 1.678e-06 |
| 604 | 1 shell up | amirhezekiahespanto/debut :: submission.csv, n = 555 (Apache 2.0) | 24.993251061 | 24.992794293 | 1.859e-05 |
| 655 | 2 shells up | lucifer19/think-select-reclose :: v32_anchor.csv, n = 555 (Apache 2.0) | 25.999572992 | 25.998772935 | 3.126e-05 |
| 739 | 1 shell up | lucifer19/think-select-reclose :: v43_anchor.csv, n = 684 (Apache 2.0) | 27.690960115 | 27.684143608 | 2.507e-04 |
| 868 | 1 shell up | the held packing of 809 (one direction) | 29.898657172 | 29.898592977 | 2.179e-06 |
| 928 | 1 shell up | the held packing of 867 (not flush) | 30.892003751 | 30.891964556 | 1.287e-06 |
| 991 | 2 shells up | the held packing of 867 (not flush) | 31.901926663 | 31.900694929 | 3.913e-05 |
| 994 | 2 shells up | the held packing of 870 (a round 12 result) | 31.940242417 | 31.939590119 | 2.069e-05 |
| total | | | | | 3.6556e-04 |

739 is one of the 45-degree layouts of section 4. Its held packing is a block in a band. The new 739 is a two-arm layout with `f` = 0.684144. The same `f` comes back, to 2e-9, at 685 (from the held 632) and at 910 (from a public 849). So it is one family on several lines, and the public 684 carries it. `take.tsv` names the file and the licence of every public donor, and the source of every held donor.

## 2. Public donors read with the layer reader

We read the public files of the harvest again, this time with the layer reader, as round 11 did with the wide reader. The scan (`work/scripts/scanlayers.py`) read every file of an accepted licence (Apache 2.0, CC BY 4.0, CC0, from each source's `meta.json`) in the harvests from 2026-11-09 to 2026-11-12b.

| what | layouts |
|---|---|
| public files read | 447 |
| layouts from 300 up, within 0.005 above the held side, not seen before in the scan | 2198 |
| read by `family_step.py`'s own readers (left to the family lane) | 453 |
| no tilted square, or the plain grid | 599 |
| refused by the layer reader: no cut window | 257 |
| refused: a layer does not clear its own copy within one more unit | 196 |
| refused: no full grid line near the cut, or the opened layout overlaps | 71 |
| **read by the layer reader, and the step one shell up builds** | **622** |

The 622 donors cover 163 n. All of them come from public notebooks under Apache 2.0. One shell up from each donor, with at most 2 donors per target, gives 255 pairs on 150 targets. We ranked them by the gain that the board predicts, as round 11 did. The predicted side is the board's side at the target plus the donor's gap to the board at its own n. 85 pairs have a predicted side below the held side.

40 of the 85 pairs started before the deadline, for 74 steps. 4 steps certified, on 604, 655 and 739. The board's prediction was poor. The top pair (910 from a public 849, predicted 2.2e-2 below the held side) ended 5.0e-3 above it. The median step ended above the bar. The 3 results came from the pairs ranked 23rd, 38th and 39th. The 23rd gave 739 (predicted 4.2e-3 below, got 6.8e-3 below). The 38th and 39th gave 604, and 655 is the second step of the 39th.

## 3. The cut at the closest pair of layers

**The derivation.** A cut at a twin layer keeps every contact type of the arm. Down, the twin takes the place of the layer that goes. Up, the copy goes in at the twin spacing `d`, which is the contact the layer already has with its twin. A layout without twins has a closest pair: two neighbouring layers of the same count whose squares differ by a defect `D` after the move `d` along the wall. `D` is the largest misfit in place along the wall, across it, or in angle (radians). Cut at that pair, the step keeps every contact type except a misfit of up to `D`. Down, the neighbour takes the place of the cut layer up to `D`. Up, the copy differs from the layer the down step took out by up to `D`. So the round trip comes back if the LP absorbs a misfit of `D`. It cannot when the copy at the spacing `d` overlaps its neighbour by more than the repair takes.

**The code.** `twins()` already marks the closest pair of each layer when `SQ_TWIN` is larger than its defect. `twin_cuts()` now ranks a pair whose defect is 1e-2 or more by its defect alone, after the true twins (under 1e-2), which keep their old order. Nothing else changed.

**Which layouts.** On the held file of round 12, 85 of the 87 target layouts (51 one direction, 36 not flush) read with the layer reader. 69 have no twins in both arms at 1e-2 (round 12 counted 71 on its own held file). Their closest pairs, by the worse arm (`work/defects.tsv`):

| defect of the worse arm | layouts |
|---|---|
| under 4e-2 | 28 |
| 4e-2 to 5.5e-2 | 10 |
| 5.5e-2 and more | 21 |
| no pair of the same count in one arm | 10 |

**The control.** It is the same gapped control as round 12, with `SQ_TWIN=0.15`. It goes down one shell as built, then up from that as built, with no LP between. Then the LP runs. When the LP alone ends more than 1e-7 off, fq runs with the LP after it. The first run ranked the pairs by the power of ten of the defect. The second run ranked them by the defect itself (the code as committed). 417 checks that the larger tolerance leaves a true twin cut alone.

| held n | class | defect of the cut pair, arm 1 / arm 2 | first run | second run | held side |
|---|---|---|---|---|---|
| 417 | one direction (twins) | 1.0e-2 / 2.4e-3 | +2.9e-9 | | 20.897143045 |
| 539 | one direction | 8e-14 / 1.85e-2 | +4.6e-9 | | 23.732037288 |
| 504 | one direction | 3.06e-2 / 4e-15 | +3.9e-9 | +5.0e-8 | 22.911433559 |
| 376 | not flush | 4.69e-2 / 1.81e-2 (first), 3.66e-2 / 1.81e-2 (second) | +1.4e-8 | +9.1e-8 | 19.876005940 |
| 303 | one direction | 2.54e-2 / 3.5e-5 | +4.3e-5 | +2.4e-5 | 17.901789274 |
| 548 | one direction | 4.4e-3 / 5.04e-2 | **-2.5e-6** | **-3.9e-5** | 23.872557388 |
| 595 | not flush | 5.28e-2 / 1.20e-2 (first), 4.56e-2 / 1.20e-2 (second) | +5.1e-4 | +2.8e-5 | 24.862204709 |
| 500 | one direction | 8.09e-2 / 5.5e-3 (first), 5.85e-2 / 5.5e-3 (second) | +9.6e-4 | +4.2e-3 | 22.848451004 |
| 375 | not flush | 8.9e-3 / none | refused | | 19.860175821 |
| 454 | not flush | 1.22e-1 / 1.18e-1 | refused | | 21.796670062 |

Every number is the side after the round trip less the held side. Every legal end passed floatsafe.

**How the end side depends on the defect.** It does not grow in proportion to `D`. It depends on whether the copy at the spacing `d` fits:

- **`D` under about 4e-2: exact.** 539, 504 and 376 come back within 1e-7 of the held side, in both runs, as true twins do. 303 is the exception, at +2.4e-5 to +4.3e-5. There the up step finds a different closest pair in the layout as built (4.7e-2 instead of 2.5e-2). So the copy is not the twin of the layer that the down step took out. In the second run of 504, the up step also read another pair (9.5e-2 in arm 2), and its copy overlapped by 3.3e-2. The fallback still came back within 5e-8.
- **`D` from about 4.5e-2: the copy often does not fit.** At 595 (4.6e-2 and 5.3e-2) and 500 (5.85e-2 and 8.1e-2), the copy overlaps its neighbour by 7.6e-2 to 9.3e-2. That is 1.2 to 1.8 times the defect, and more than `SQ_APART` repairs. The up step then falls back to the first derivation, and the round trip ends 2.8e-5 to 4.2e-3 above. At 548 (5.0e-2) the copy fits. The LP takes the misfit and lands in a neighbouring jammed state, 2.5e-6 and 3.9e-5 below the held side.
- **`D` of 1.2e-1 (454), or one arm with no pair (375): refused.** The up step finds no layer that clears its own copy.

So the closest-pair cut is exact below about 4e-2. Above that, the step falls back to the first derivation by itself when the copy does not fit. The walks of this round use `SQ_TWIN=5.5e-2`. With it, 38 of the 69 layouts cut at a closest pair, 28 of them in the exact range. The 21 layouts above keep the first derivation.

**The round trip as a polish.** The second control of 548 ends 3.928e-5 below the held side and certifies (floatsafe, 1.678e-6 of score). It is a result of this round (section 1). A down-then-up round trip at a pair in the scatter range is a cheap move: 10 to 150 s per layout.

## 4. The 45-degree layouts: their shells

28 n from 300 up have a cut window on one wall only (round 12, section 2). They are of three kinds. We derived the shell of each from the held layouts. Nothing was built for them, so no control ran.

- **Bands from corner to corner: 300, 301, 337, 414, 455, 499, 642.** A band of tilted squares (median tilt 27 to 36 degrees) runs from one corner to the opposite one between two upright staircases. Two held pairs sit one shell apart at consecutive `m` with the same `k - m`: 301 and 337 (`k - m = -5`, `f` 0.8467 and 0.8537), and 455 and 499 (`k - m = -7`, `f` 0.8251 and 0.8293). From 301 to 337 the layout gains 36 squares, 4 tilted and 32 upright. From 455 to 499 it gains 44, 5 tilted and 39 upright. So a band walks on the line `k - m`, and one shell up adds `2m + 2` squares. They are one grid row and one grid column that cross at the band (`2m - 2` or `2m - 3` upright squares), and one period of the band (4 or 5 tilted squares). The cut moves the four quadrants of the cross by (0, 0), (0, -1), (-1, 0) and (-1, -1). Only the far quadrant holds band beyond the cross, and its move (-1, -1) runs along the band. So the band loses one period, and the cut needs a twin under that move, as the layer cut does. A band cell of the leader's family sits on the same kind of line: 454, 498 and 544 have `k - m = -8`.
- **Fixed blocks at small `k`: 626, 730, 785, 842, 962 (`k = 1`, `f` 0.5208) and 787, 844, 903, 964 (`k = 3`, `f` 0.5355).** The block is the same at every `m`, to 4 decimals of `f`, and the grid grows around it. The shell is one grid row and one grid column, `2m + 1` squares, on the line `k` constant. The step can only give back the same `f`, which those n already hold. These n belong to the gadget lane (`n = m² + 1` to `m² + 3`).
- **Blocks inside a band, and the rest: 330, 332, 445, 448, 487, 537, 540, 581, 589, 739, 789, 909.** The same `f` appears at different `m` (0.6924 at 330, 448 and 537, and 0.5914 at 445 and 789). But `k` and `m` do not move together by one shell. We found no common line, so we derived no step.

The band step is the one worth building. Its control is the same as the layer cut: down one shell at a twin period, up again, back within 1e-7.

## 5. Next runs

1. **Merge the take dir** `take-readers-r13` (8 n). `take.tsv` names each source and licence.
2. **Round trips as a polish.** A round trip at the closest pair takes 10 to 150 s per layout and certified 548. Run it on all 85 target layouts and on every layout the layer reader reads, at `SQ_TWIN` from 4e-2 to 6.5e-2, and keep the ends below the bar.
3. **Finish the walks.** 17 upward held walks, 45 public pairs and all 87 downward walks did not start. Their lists are `q-boxD/q1b.tsv`, `q-boxA/q1b.tsv` and `q-*/q3.tsv` in the work dir, and a walker skips the walks that its rows file holds. Down steps from the 38 layouts that now cut at a closest pair have never run.
4. **Walk on from the new results**, down from 739, 868, 928, 991 and 994 (up leaves the range), and up and down from 604 and 655.
5. **Build the band step** of section 4 for 300, 301, 337, 414, 455, 499 and 642. The step is a cross cut at a twin period of the band, on the line `k - m`. Its control is 337 down to 301 and back up.
6. Rank the public pairs by something better than the board's gap, or run them all. The results came from pairs ranked 23rd to 39th of 85.

## Files of round 13

| file | what it is |
|---|---|
| [`family_readers.py`](../family_readers.py) | the closest-pair rank in `twin_cuts()`, and the defects of the cut layers in the control's output |
| [`results/readers-r13-2026-11-12.tsv`](../results/readers-r13-2026-11-12.tsv) | every walk step of this round |
| `<scratch>/bounties-squares/take-readers-r13/` on boxA | the take dir: one csv per certified n and `take.tsv` |
| `take-readers-r13/work/` | the walk lists, the scan (`scripts/scanlayers.py`, `sources-pub.tsv`, `pairs-pub.tsv`, `donors-pub/`), the controls (`box-boxA/ctl/`), `defects.tsv`, the rows per box |

## Summary of round 13

- 8 n certified for 3.6556e-4 of score. They are 4 held packings walked up (868, 928, 991, 994), 3 public donors that only the layer reader reads (604, 655, 739), and 1 round trip (548). The take dir holds them.
- The layer reader read 622 public layouts on 163 n that the family readers refuse (447 files, all Apache 2.0). 40 of their 85 best pairs ran. 739 from a public 684 alone gives 2.5e-4.
- A layout without twins can be cut at its closest pair of layers. The round trip is exact while the worse arm's defect is under about 4e-2 (539, 504, 376). From about 4.5e-2 the copy often overlaps its neighbour by 1.2 to 1.8 times the defect, and the step falls back to the first derivation. 548 fits there and ends below its held side. The walks now use `SQ_TWIN=5.5e-2`: 38 of the 69 layouts without twins cut at a closest pair.
- The 45-degree bands walk on the line `k - m`. One shell is a grid row and column crossed at the band, plus one band period (301 to 337 and 455 to 499 in the held file). The fixed blocks at `k` = 1 and 3 walk on `k` constant and only repeat their `f`. Nothing was built for them.
- **Next:** merge the take dir, then round trips on every readable layout, the walks that did not start (all 87 downward ones), and the band step with its control.

---

# Round 14 (2026-11-12)

**Result: 13 n certified, for 3.5505e-4 of score against `gate/cand-round13-1112a`. 9 come from walks on the jonathan1506 layouts that only the layer reader reads, and 594 alone gives 2.800e-4. 4 come from round trips: 595 gives 9.5e-6, and 698, 867 and 927 together give 3e-7. A 14th n, 981 (3.1e-5, one shell up from the held 918), is in `take-polish-r14` as the fq polish of our step. The band step is built and exact as code, but every band step lands on a held layout or above it. Nothing was submitted from here.**

Words used here: "held" is now `gather/round13-2026-11-12a.csv` (gate dir `gate/cand-round13-1112a`). "The bar" of an n is the lowest of its held score and its score in every take dir of round 14 at the take. These were `take-border-r14`, `take-corners-r14`, `take-family-r14`, `take-modules-r14`, `take-polish-r14` and `take-soft-r14`, at 08:08 UTC. The take dir is `take-readers-r14` on boxA. The runs used 2 processes on boxD and 1 on boxA, from 06:37 to 08:05 UTC.

## 1. Round trips as a polish

`family_readers.py trip` turns the control of round 13 into a polish step. It goes one shell down from a layout as built, with no LP between, and one shell up again from that. Then come the squeeze and the fq polish of `finish()`. The trip runs once for each value of `SQ_TWIN` in 1e-2, 4e-2, 5.5e-2 and 6.5e-2. Two values that give the same two cuts run once. A trip that comes back within 1e-7 of its start is exact and gets no fq. An end below the bar goes to the take.

- A value under the defect of a layout's closest pair cuts it at any layer (the first derivation of round 12).
- A value over that defect cuts it at the closest pair.
- We added 1e-2 to the values of the task because the first test, on 595, ended 2.3e-4 below its held side with the first derivation.

The list held 343 layouts from 300 up. They are the 85 target layouts of round 12, the jonathan1506 layouts, and every other layout that the layer reader read in round 12. The 20 targets whose closest pair has a defect from 3.5e-2 to 6.5e-2 came first. The 62 jonathan1506 layouts that the layer reader reads (section 3) came next, then the rest.

17 layouts ran before the deadline: 38 distinct trips. 28 more values gave the same cuts and were skipped. A layout took 1 to 8 minutes under a load of 8 to 15. We moved two of the three slots to the walks of section 2 at 07:10 and 07:33, because the walks paid more.

| layouts | what the trips gave |
|---|---|
| 595 | the first derivation ends 2.31e-4 below the held side (24.861973821 against 24.862204709): 9.465e-6 of score |
| 698 | the closest pair (defect 3.8e-2) ends 7.8e-6 below: 2.97e-7 of score |
| 867, 927 | 7e-9 and 6e-9 below: 1.7e-10 and 1.6e-10 of score, at the noise level of fq |
| 376, 416, 647, 752, 854, 866, 914, 989 | the closest pair or a twin comes back within 4e-7 of the bar (647, 854 and 914 end a few 1e-9 below, under the 1e-10 of score the rule asks) |
| 501, 548, 808, 818 | the closest pair (defect 4.1e-2 to 6.2e-2) ends 3.9e-5 to 3.3e-4 above |
| all 17 | the first derivation (`SQ_TWIN=1e-2`) ends 2.3e-4 below on 595, within 2e-7 of the bar on 416, 548, 647, 752, 854, 867 and 927, 4.4e-6 above on 698, and 3.5e-5 to 1.8e-3 above on the other 8 |

So a round trip moves a layout by more than the fq noise only twice in 17 layouts (595 and 698). One of the two is the first derivation, which round 12 measured as a loss on average.

## 2. The walks

The lists were what round 13 left and the walks on from its results, all at `SQ_TWIN=5.5e-2`, from the held packings of round 13:

- Down from 739, 868, 928, 991 and 994, and up and down from 604 and 655: 9 walks, run first.
- Up from the 62 jonathan1506 layouts of section 3, and then down from them.
- The 17 upward held walks and all 45 public pairs that round 13 did not start, all of them and not a ranked top.
- The 82 downward walks of round 13 that did not start (the other 5 of its 87 are in the first list or ran).

108 walks started (54 up, 54 down) and took 173 steps. The 17 upward held walks, the 45 public pairs and the 82 held downward walks did not start before the deadline.

| start | direction | steps | built | refused | below the bar | certified steps |
|---|---|---|---|---|---|---|
| a round 13 result | up | 3 | 1 | 2 | 0 | 0 |
| a round 13 result | down | 14 | 13 | 1 | 1 | 1 |
| a jonathan1506 layout | up | 82 | 62 | 20 | 15 | 12 |
| a jonathan1506 layout | down | 74 | 60 | 14 | 1 | 1 |

52 of the 62 upward and 47 of the 62 downward jonathan1506 walks started. "Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule. It needs floatsafe at 2.2e-11, and a score more than 1e-10 below the held score and below the same n in every take dir of round 14. The take keeps the best of each n.

The walks on from the round 13 results were dry. Their only step below the bar is 867 from 928 (6e-9), and a round trip of 867 beats it.

**Certified results of the walks.**

| n | step | start | gain |
|---|---|---|---|
| 594 | 1 shell up | the held 545 (jonathan1506) | 2.800e-04 |
| 597 | 1 shell down | the held 648 (jonathan1506) | 1.395e-05 |
| 701 | 1 shell up | the held 648 | 4.481e-06 |
| 707 | 1 shell up | the held 654 (jonathan1506) | 1.041e-05 |
| 756 | 2 shells up | the held 648 | 4.954e-08 |
| 813 | 4 shells up | the held 597 (jonathan1506) | 1.152e-06 |
| 872 | 5 shells up | the held 597 | 1.222e-05 |
| 933 | 6 shells up | the held 597 | 1.248e-05 |
| 986 | 1 shell up | the held 923 (jonathan1506) | 1.057e-05 |
| total | | | 3.4531e-04 |

The walk up from the held 597 went 6 shells, to 701, 756, 813, 872 and 933, and ended below the bar at 5 of them. The walk up from the held 648 did the same at 701, 756, 813, 872 and 933. The take keeps the better of the two at each n. 981 one shell up from the held 918 (3.142e-5) certified too, but `take-polish-r14` holds its fq polish, 1.3e-9 better. All 13 results and their donors are Apache 2.0 or ours on Apache 2.0, and `take.tsv` names each source.

## 3. The jonathan1506 layouts

The family lane found that 67 of the 97 jonathan1506 layouts do not read with `family_step.py`. 12 of them are one band from corner to corner. 55 are two blocks of staggered stacks on two walls, off the wall by a fraction. The layer reader reads 62 of the 67 (`work/jread.txt`): all 55 two-block layouts and 7 of the 12 bands. It refuses 629, 680, 733, 905 and 966, which have a cut window on one wall only. So the walks of this lane carry these 62, and the family lane leaves them to us.

## 4. The band step

**No band has a twin one shell along.** A band from corner to corner holds pairs of tilted squares along the diagonal, about 1.05 apart. We moved the tilted squares of each band by (k, k) and compared each with the tilted square nearest to its image, in place and in angle (`work/scripts/band_twin.py`). The median defect:

| n | f | k = 1 | k = 2 | k = 3 | k = 4 |
|---|---|---|---|---|---|
| 300 | 0.8241 | 3.5e-1 | 3.2e-1 | 2.7e-2 | 3.9e-1 |
| 455 | 0.8251 | 3.5e-1 | 3.1e-1 | 4.4e-2 | 3.9e-1 |
| 642 | 0.8262 | 3.5e-1 | 2.9e-1 | 6.1e-2 | 4.1e-1 |
| 499 | 0.8293 | 3.6e-1 | 3.0e-1 | 7.0e-2 | 4.3e-1 |
| 414 | 0.8407 | 3.8e-1 | 3.1e-1 | 8.1e-2 | 4.7e-1 |
| 301 | 0.8467 | 3.8e-1 | 3.0e-1 | 1.2e-1 | 4.9e-1 |
| 337 | 0.8537 | 4.0e-1 | 2.9e-1 | 1.4e-1 | 4.7e-1 |

No tilted square of any band is within 1e-2 of a twin at any k. The 12 bands of jonathan1506 (f about 0.56) are worse: their median at k = 3 is 0.14 to 0.19. The band repeats after 3 shells: 4 pairs span about 4.2 along the diagonal, and 3 shells span 3√2 = 4.24. So the step of the task (one shell, with the control 337 down to 301) has no twin to cut at. We built the step for k shells instead.

**The step.** `band_step()` cuts across the band at a point `a0` of the diagonal, with `a = (x + y) / √2`:

- Down keeps every square with `a < a0`, moves every square with `a ≥ a0 + k√2` by (-k, -k), and drops the rest. That drops one band period and k rows and k columns of each grid.
- Up keeps every square with `a < a0 + k√2`, and moves every square with `a ≥ a0` by (k, k). The period from `a0` to `a0 + k√2` is then in twice. The two corners that the moves leave open get the grid moved by (0, k) above the band and by (k, 0) below it.

Both grids are lattices that a move by (k, k) keeps. So the band is the only place where the layout meets itself at a misfit. The step tries every cut along the band in steps of 0.1. It keeps the count that most cuts give, at the cut with the largest smallest gap. In every band that count is 113 squares for k = 3 (8 tilted and 105 upright), and not 114 = 6m + 12 as three shells of `2m + 2` would give. Up then down at the same cut gives back the donor exactly, on 300, 301, 337, 414, 455 and 499. Down as built overlaps where the band meets itself, by 2.7e-2 (300) to 8.7e-2 (337). The period it takes out is 1 % longer than the band's own. Up as built is legal, because there the band opens by the same amount.

**What it gives.** We ran 8 steps with k = 3 and `SQ_APART=1e-1`, then the squeeze and fq.

| step | as built less held | end less held |
|---|---|---|
| 414 down to 301 | -6.0e-3 | -1e-9 (the held 301) |
| 455 down to 336 | -5.1e-4 | -1e-9 (the held 336) |
| 300 down to 205 | -3.3e-4 | -1e-9 (the held 205) |
| 499 up to 642 | +3.0e-3 | -1e-9 (the held 642) |
| 300 up to 413 | +1.2e-3 | +1.05e-3 |
| 642 down to 499 | -3.0e-3 | +6.9e-4 |
| 301 down to 206 | -1.35e-2 | +4.4e-4 |
| 337 down to 236 | -8.2e-3 | +4.6e-2 |
| 414 down to 301, then up again (the control) | | +6.0e-3 against the held 414 |

So the held 205, 301, 336 and 642 are the bands of 300, 414, 455 and 499 moved by one period, to 1e-9. These bands are one design at many n, and the held file already holds every member that the step reaches. The control shows the same from the other side. 414 down gives the held 301, and back up it gives 301's band moved up by one period, which is 6.0e-3 worse than the held 414. The held 414 is a different and better layout. The band step is exact as code, and dry as a search.

## 5. Next runs

1. **Merge the take dir** `take-readers-r14` (13 n, 3.5505e-4). `take.tsv` names each source and licence.
2. **Finish the jonathan1506 walks.** 10 upward and 15 downward walks of section 3 did not start (`work/walk-jup-asc.tsv`, `work/walk-jdown.tsv`). Walk on from the new results too: down from 594, 597, 707 and 986, and up from 933. The jonathan1506 layouts were the best donors of the round: 13 of 156 steps certified.
3. **The other walks.** The 17 upward held walks and the 45 public pairs (`work/walk-up.tsv`), then the 82 held downward walks (`work/walk-down.tsv`).
4. **Round trips** only after those. 326 of the 343 layouts did not start (`work/trip-rest.tsv`), and 2 of 17 moved by more than the fq noise.
5. **No more band steps** on the bands of section 4. The held file holds every member that the step reaches. The family lane called 12 jonathan1506 layouts bands. They sit at `k` = 3 (403, 444, 487), 4 (629, 680, 733, 788, 845, 904, 965) and 5 (905, 966). Their `f` is 0.562 to 0.568 at every `m`. They are blocks that the grid grows around, like the fixed blocks of round 13, and belong to the gadget lane.

## Files of round 14

| file | what it is |
|---|---|
| [`family_readers.py`](../family_readers.py) | `trip` (round trips as a polish) and `band` (the band step, `band_step()`, `band_build()`) |
| [`results/readers-r14-2026-11-12.tsv`](../results/readers-r14-2026-11-12.tsv) | every round trip, walk step and band step of this round |
| `<scratch>/bounties-squares/take-readers-r14/` on boxA | the take dir: one csv per certified n and `take.tsv` |
| `take-readers-r14/work/` | the lists (`trip-list.tsv`, `walk-*.tsv`), `jread.txt`, the scripts (`band_twin.py`, `band_geo.py`), the rows per box |

## Summary of round 14

- 13 n certified for 3.5505e-4 of score. The take dir holds them. A 14th, 981, is in the polish take as the fq polish of our step.
- The jonathan1506 layouts are the best donors so far. The layer reader reads 62 of the 67 that `family_step.py` refuses. Walks from them gave 9 n, with 594 at 2.8e-4 and a chain from 597 up to 933.
- Round trips as a polish gave 595 (9.5e-6) and 698 (3e-7) in 17 layouts. The other ends are within the fq noise or above.
- A band from corner to corner repeats after 3 shells, at 113 squares and not 114. The band step at k = 3 is exact as code: up then down gives back the donor. It reproduces the held 205, 301, 336 and 642 from the held 300, 414, 455 and 499. So it is dry as a search.
- Next: merge the take dir, then finish the jonathan1506 walks and walk on from the new results.

---

# Round 15 (2026-11-12)

**Result: 5 n in the take, for 6.687e-5 of score against `gate/cand-round14-1112a`. 985 (3.900e-5) and 655 (2.607e-5) are one shell up from two of the 22 public layouts that the harvest found at 09:08 UTC. Three more of our steps certified but sit in other takes now. 746 is one shell up from the held 691 (1.459e-4 as built), 802 from the held 745 (9.46e-5) and 811 from the held 754 (3.1e-6). The soft-box search and the fq polish took them further. The border lane built 923 (4.0e-5) from our 985. As built, our steps are worth 3.10e-4. Nothing was submitted from here.**

Words used here: "held" is now `gather/round14-2026-11-12a.csv` (gate dir `gate/cand-round14-1112a`). "The bar" of an n is the lowest of its held score and its score in every take dir that changed after that gate. At the final take (10:32 UTC) these were the round 15 takes of seven lanes and the harvest takes j, k and l of 2026-11-12. The lanes are band, border, corners, family, modules, polish and soft. The take dir is `take-readers-r15` on boxA. The runs used 2 processes on boxD, 1 on boxC and 1 on boxA, from 08:58 to 10:30 UTC.

## 1. The lists

Every walk ran with `SQ_TWIN=5.5e-2`, `SQ_APART=3e-2`, the fq quench of `finish()` and the 2-miss stop rule, as in round 14. The lists ran in this order, and no list was ranked:

- **A, 30 walks.** Down from the round 14 results 594, 597, 707 and 986, and up from 933. Then the 10 upward and 15 downward jonathan1506 walks that did not start in round 14.
- **D, 44 walks.** At 09:08 UTC the harvest lane wrote about two new public files. jonathan1506's notebook ran again at 09:02 UTC, and the jazivxt/boxed-in dataset changed at 08:49 UTC. Together they hold 22 n below the held file (`take-harvest-2026-11-12j`, all Apache 2.0). We walked up and down from all 22 and put this list before B and C, because the jonathan1506 layouts were the best donors of round 14.
- **B, 58 walks.** The 13 upward held walks and the 45 public pairs that round 13 left. 4 of its 17 upward held walks ran in round 14.
- **C, 52 walks.** The downward held walks that round 13 left. Of its 82, 22 ran in round 14 as jonathan1506 walks and 8 are in list A.
- **Round trips** after the walks: the 326 layouts that did not start in round 14, 6 to a queue file.

We wrote the downward walks of lists A and C into the handoff log at 08:56 UTC, and list D at 09:10 UTC. The family lane left them to us. It walks down only from 644, 694, 867 and 914, which changed in round 14.

177 of the 184 walks started. 5 of the other 7 leave the range at their first step (965, 978, 980 and 987 up, and the new 966 up). 927 and 925 down did not start before the deadline. The slots of boxD finished their lists at 10:13 UTC, so 7 round trips ran (500, 547, 596, 749, 910, 965 and 978).

## 2. What ran

| part | direction | steps | built | refused | below the bar | certified |
|---|---|---|---|---|---|---|
| a round 14 result | down | 8 | 8 | 0 | 0 | 0 |
| a round 14 result | up | 3 | 2 | 1 | 0 | 0 |
| a jonathan1506 layout | up | 11 | 7 | 4 | 2 | 2 (746, 802) |
| a jonathan1506 layout | down | 18 | 8 | 10 | 0 | 0 |
| a new public layout (list D) | up | 38 | 33 | 5 | 2 | 2 (655, 985) |
| a new public layout (list D) | down | 37 | 32 | 5 | 0 | 0 |
| a public pair of round 13 | up | 79 | 68 | 11 | 2 | 2 (761, 868) |
| a held layout of round 13's lists | up | 23 | 23 | 0 | 1 | 1 (811) |
| a held layout of round 13's lists | down | 94 | 84 | 10 | 2 | 0 |
| round trip | | 15 | 11 | 4 | 1 | 1 (910) |
| all | | 326 | 276 | 50 | 10 | 8 |

"Below the bar" is the tool's own side more than 1e-9 under the bar. "Certified" is the lane's rule. It needs floatsafe at 2.2e-11, and a score more than 1e-10 below the held score and below the same n in every live take dir. The 2 downward steps below the bar are 795 and 796, 2e-9 under it, which is under the 1e-10 of score the rule asks. 3 steps hit the 600 s limit. The round trips skipped 13 more values of `SQ_TWIN` that gave the same cuts.

The downward walks were dry again: 157 steps and no certified result. Every certified step went up one shell.

## 3. Certified results

| n | step | start | held side | new side | score gain | where it is |
|---|---|---|---|---|---|---|
| 746 | 1 shell up | the held 691 (jonathan1506) | 27.799033591 | 27.795047564 | 1.459e-04 | `take-soft-r15`, 1.690e-4 after the soft-box search |
| 802 | 1 shell up | the held 745 (jonathan1506) | 28.799148763 | 28.796469759 | 9.460e-05 | `take-soft-r15`, 1.507e-4 after the soft-box search |
| 985 | 1 shell up | the new 922 of jonathan1506 (list D) | 31.838330374 | 31.837106278 | 3.900e-05 | this take |
| 655 | 1 shell up | the new 604 of jazivxt/boxed-in (list D) | 25.998772935 | 25.998105694 | 2.607e-05 | this take |
| 811 | 1 shell up | the held 754 | 28.915988263 | 28.915901349 | 3.05e-06 | `take-polish-r15`, 7.6e-10 better after fq |
| 761 | 1 shell up | lucifer19/think-select-reclose :: v45_anchor.csv, n = 706 | 27.993099233 | 27.993050800 | 1.756e-06 | this take |
| 868 | 1 shell up | amirhezekiahespanto/debut :: submission.csv, n = 809 | 29.898592954 | 29.898591942 | 3.43e-08 | this take |
| 910 | round trip, `SQ_TWIN=4e-2` | the held 910 | 30.679149653 | 30.679149391 | 8.6e-09 | this take |

The take holds 5 n for 6.687e-5. The three others are worth 2.436e-4 as built, and the takes that hold them name our step as their source. The border lane also built 923 from the corner window of our 985 (4.0e-5, in `take-border-r15`). All donors are Apache 2.0, or the held file. `take.tsv` names each source and licence.

**The extra fq quench.** Before the take we ran fq once more on every layout that certified. It started from the floatsafe rows, as the corners lane advised at 09:20 UTC. It moved none of the 5 by even 1e-9. `finish()` already ends with the fq quench and the polish flags, so these layouts were jammed when they landed.

## 4. Next runs

1. **Merge the take dir** `take-readers-r15` (5 n, 6.687e-5). 746, 802 and 811 are in the soft and polish takes, and 923 is in the border take.
2. **Walk every new public layout up one shell as soon as the harvest lands.** List D gave 2 certified steps in 22 upward walks. The round 14 jonathan1506 layouts gave 2 more in the 10 upward walks left from round 14. The cheapest yield of this lane is a step up from a layout that another lane or a notebook has just made.
3. **Round trips.** 7 of the 326 layouts ran. 1 certified at 8.6e-9, which is fq noise. Run them only when no new donor is waiting.
4. **The downward walks are dry.** Rounds 14 and 15 ran about 245 downward steps. 2 certified: 597 (1.4e-5) and 867 at the fq noise. 927 and 925 down did not start.

## Files of round 15

| file | what it is |
|---|---|
| [`results/readers-r15-2026-11-12.tsv`](../results/readers-r15-2026-11-12.tsv) | every walk step and round trip of this round |
| `<scratch>/bounties-squares/take-readers-r15/` on boxA | the take dir: one csv per certified n and `take.tsv` |
| `take-readers-r15/work/` | the lists (`walk-a.tsv`, `walk-b.tsv`, `walk-c.tsv`, `qd/`, `trips/`), the runners (`run.sh`, `run-trip.sh`, `final.sh`), the rows per box, the extra quench (`scripts/quench2.py`, `q2-*.log`) |

No code changed in `family_readers.py` this round.

## Summary of round 15

- 5 n in the take for 6.687e-5. 985 and 655 are one shell up from new public layouts of 09:02 UTC. 761, 868 and 910 add 1.8e-6.
- 3 more certified steps are in other takes after their polish: 746 (1.459e-4 as built), 802 (9.46e-5) and 811 (3.1e-6). As built, our steps are worth 3.10e-4.
- 177 of 184 walks ran, all one shell at a time. Every certified step went up. 157 downward steps gave nothing.
- Next: merge the take, and walk every new public layout up one shell as soon as it lands.

---

# Round 16 (2026-11-12)

**Result: 4 n in the take, for 1.258e-5 of score against `gate/cand-round15-1112a`. 701 (7.37e-6) and 421 (5.20e-6) come from a new kind of step. Its first step up is at the second- or third-ranked cut of the layer reader. The donors are layouts whose best cut had ended just above the bar. 975 and 502 add 7e-9. 7 more of our steps beat the held file, but other takes hold those n lower now. The modules lane built its 995 (1.08e-5) from the corner of our 995 (1.00e-6 as built). Nothing was submitted from here.**

Words used here: "held" is now `gather/round15-2026-11-12a.csv` (gate dir `gate/cand-round15-1112a`). "The bar" of an n is the lowest of its held score and its score in every take dir that changed after that gate. At the final take these were the round 16 takes of band, border, corners, family, modules, polish and soft, and the harvest takes m and n of 2026-11-12. The take dir is `take-readers-r16` on boxA. The runs used 2 processes on boxD, 1 on boxC and 1 on boxA, from 12:12 to 13:28 UTC.

## 1. New in the code: a walk at another cut

The layer reader ranks every pair of layers it can cut, and until now a walk always took the best one. In round 15 many upward steps ended just above the bar, some by less than 1e-5 of side. Another cut puts a different layer in twice, so the squeeze starts from another layout and can end lower.

- `build_layers(R, direction, pick)` now refuses a pick past the end of its ranking, where it used to repeat the last cut.
- `read_build(..., pick)` with a pick above 0 uses the layer reader only.
- `walk` reads an optional third column `pick` in its rows. The first step of that walk is at that cut, and the later steps at the best cut. Its rows have shells `KcP` (shell K, cut P), and its layouts go to `raw/N-DIRKcPfromDONOR.csv`.
- `take` names the cut in `take.tsv`.

The default (pick 0) builds the same steps as before.

## 2. The lists

All walks ran with `SQ_TWIN=5.5e-2`, `SQ_APART=3e-2` and the fq quench of `finish()`, as in round 15. A plain walk stops after 2 misses in a row. A walk at another cut stops at its first miss.

- **E, 16 walks.** Up from the 13 new held layouts of round 15 whose next shell is in range. They are 746 and 802 (the soft versions), 923 (border), 921 (corners), and 811, 761, 868, 910, 587, 812, 871, 912 and 865. Down from 746, 802 and 923. The family lane walks 921, 983 and 984 with its own readers, and our 984 up from 921 was the same layout as theirs to 1.7e-13 of score. So we dropped our walks down from 921, 983 and 984.
- **M, 14 walks.** Plain walks from the new layouts of this round as they landed. Up from the five layouts of the harvest pass m (748, 862, 922, 696 and 744, jazivxt/boxed-in of 11:10 UTC). Up from the modules 549, 649, 700 and 703, the family 649, the corners 863, the soft 700 and our own 421. Down from the family 984.
- **F, 128 walks at another cut.** Cut 1, 2 or 3 of the first step up. The donors are in five groups, by how close the step at the best cut came:
  - F0: the near misses of list E (696, 812, 868, 811), our own 421 and 701, and the new layouts of other lanes in this round. These are the family 549, 598 and 649, the corners 863, the soft 700, and the modules 549, 649, 921 and 984.
  - F1: 10 donors whose best cut ended less than 1e-4 of side above the bar in rounds 12 to 15.
  - F2: the new held layouts of list E (746, 802, 761, 923 and 921).
  - F3: 19 donors between 1e-4 and 1e-3.
  - F4: 26 donors between 1e-3 and 2e-3.

The harvest pass n (12:50 UTC) held no new public layout, so no list came from it.

## 3. What ran

| part | walks | steps | built | refused | below the bar | in the take |
|---|---|---|---|---|---|---|
| E: new held layouts of round 15, up | 13 | 21 | 19 | 2 | 3 | 1 (975) |
| E: new held layouts of round 15, down | 3 | 6 | 4 | 2 | 0 | 0 |
| M: new layouts of this round, up | 13 | 20 | 17 | 3 | 3 | 0 |
| M: new layouts of this round, down | 1 | 3 | 3 | 0 | 1 | 0 |
| F0: near misses of list E | 9 | 10 | 8 | 2 | 1 | 0 |
| F0: new layouts of this round | 15 | 21 | 19 | 2 | 6 | 0 |
| F1: misses under 1e-4 | 28 | 34 | 32 | 2 | 4 | 3 (421, 502, 701) |
| F2: new held layouts of round 15 | 10 | 10 | 8 | 2 | 1 | 0 |
| F3: misses 1e-4 to 1e-3 | 30 | 32 | 31 | 1 | 2 | 0 |
| F4: misses 1e-3 to 2e-3 | 5 | 5 | 5 | 0 | 0 | 0 |
| all | 127 | 162 | 146 | 16 | 21 | 4 |

127 of the 158 walks started: all 16 of list E, all 14 of list M and 97 of the 128 of list F. The F walks that did not start are the end of F3 at cut 2 and 21 of the 26 donors of F4. No step hit the 600 s limit.

By cut, over all steps:

| cut | steps | below the bar |
|---|---|---|
| best (0) | 50 | 7 |
| 1 | 64 | 10 |
| 2 | 38 | 4 |
| 3 | 10 | 0 |

"Below the bar" is the tool's own side more than 1e-9 under the held side. "Certified" is the lane's rule: floatsafe at 2.2e-11, and a score more than 1e-10 below the held score and below the same n in every live take dir.

## 4. Certified results

| n | step | start | held side | new side | score gain |
|---|---|---|---|---|---|
| 701 | 2 shells up, the first at cut 2 | the held 597 (our step down from the jonathan1506 648, round 14) | 26.912723412 | 26.912528309 | 7.369e-06 |
| 421 | 1 shell up at cut 1, then fq | emptydaboi/squareforge-master-1-v11-consolidated :: squareforge_22_286_candidate.csv, n = 380 | 20.973809486 | 20.973702779 | 5.201e-06 |
| 975 | 1 shell up | the held 912 | 31.720991916 | 31.720991746 | 5.4e-09 |
| 502 | 1 shell up at cut 2 | lucifer19/think-select-reclose :: v40_anchor.csv, n = 457 | 22.877574352 | 22.877574315 | 1.7e-09 |
| total | | | | | 1.2577e-05 |

The best cut of the 380 had ended 4.9e-6 of side above the held 421 in round 15. Cut 1 ends 9.2e-5 below it. The best cut of the 597 ended 5.6e-7 above the held 648 in round 14. Cut 2 ends 2e-9 below it, and the next shell up ends 1.95e-4 below the held 701. The donors are Apache 2.0, or held layouts that `take.tsv` traces to their sources.

Each certified file then had one fq quench (default flags) from its floatsafe rows. It moved 421 by 1.45e-5 of side and none of the others.

**Beat the held file, but not the other takes.** 7 more n:

- 995, two shells up from the held 871 (1.003e-6). The modules lane put a corner of it into its 995, at 1.077e-5.
- 751, up from the held 696 at cut 1 (2.2e-7). The family lane walks the pass-m 696 and holds 751 at 3.4e-7.
- 755, up from the soft 700 of 13:13 UTC (2.57e-5 at the best cut, 2.62e-5 at cut 1). The family lane walked the soft 700 too, and holds 755 at 3.28e-5.
- 921 down from the modules 984 at cut 1 (2.32e-5). The modules 921 is at 2.92e-5.
- 984 up from the held 921, at the best cut and at cut 1. It is the same layout as the family 984 of 12:17 UTC, to 1.7e-13 of score.
- 598 and 649 up from the family 549 and 598 at cut 1. They are the family layouts again, to 3e-13 of score, and the modules 649 is lower.

## 5. Next runs

1. **Merge the take dir** `take-readers-r16` (4 n, 1.258e-5). `take.tsv` names each source and licence.
2. **Every near miss gets its other cuts.** Cut 1 or 2 certified 3 of 28 donors whose best cut ended under 1e-4 of side above the bar. It certified none of 30 donors from 1e-4 to 1e-3. So run cuts 1 and 2 on every upward step that ends less than 1e-4 above the bar. Run them as soon as the step ends, in the walks of this lane and of the family lane.
3. **Step up from every new layout of another lane as soon as it lands.** The family lane runs the same step with its own readers. Where both readers take a layout, they gave the same layout (984, 598 and 649). So this lane should run only the other cuts on those, and the plain walk only where `read_any` refuses.
4. **Not run:** the rest of F3 at cut 2 and 21 of the 26 F4 donors (1e-3 to 2e-3), `work/walk-f.tsv`. They are the lowest odds: a miss of 1e-3 needs a cut that ends ten times lower than the best.
5. **Downward walks and round trips** stay last. The 6 downward steps of list E gave nothing.

## Files of round 16

| file | what it is |
|---|---|
| [`family_readers.py`](../family_readers.py) | `walk` at another cut (a third column `pick`), and the take names the cut |
| [`results/readers-r16-2026-11-12.tsv`](../results/readers-r16-2026-11-12.tsv) | every walk step of this round |
| `<scratch>/bounties-squares/take-readers-r16/` on boxA | the take dir: one csv per certified n and `take.tsv` |
| `take-readers-r16/work/` | the lists (`walk-e.tsv`, `walk-m.tsv`, `walk-f.tsv`), the runners (`box/run2.sh`, `collect.sh`, `final.sh`), the rows per box, `scripts/near.py` (the near misses of rounds 12 to 15), `scripts/picks.py` (the ranked cuts of a donor) |

## Summary of round 16

- 4 n in the take for 1.258e-5: 701 (7.37e-6) and 421 (5.20e-6) from the new walk at another cut, 975 and 502 at 7e-9.
- The walk at another cut is new in `family_readers.py`. It pays on donors whose best cut ended less than 1e-4 of side above the bar: 3 of 28 certified.
- 7 more of our steps beat the held file, but the family and modules lanes hold those n lower. The modules 995 is built on our 995.
- Next: merge the take, run the other cuts of every near miss at once, and step up from every new layout of the other lanes.

---

# Round 17 (2026-11-12)

**Result: 9 n in the take at 20:06 UTC, for 8.91e-4 of score against `gate/cand-round16-1112a`. Against the round 17 file (submitted at 18:54 UTC), they are worth 7.84e-4. Against the best row of every other live take dir, they are worth 5.08e-4. 982 (2.96e-4), 919 (2.05e-4) and 922 (1.88e-4) carry most of it. All three are one or two shells up from the family lane's new 858 and 861, and all three came in the last hour. Nothing was submitted from here.**

Words used here: "held" is `gather/round16-2026-11-12a.csv` (gate dir `gate/cand-round16-1112a`). "The bar" of an n is the lowest of its held score and its score in every live take dir `take-*-r17`. The take dir is `take-readers-r17` on boxA. The walks ran on 2 processes on boxD and 1 on boxC from 15:18 to 20:05 UTC. A fourth process ran on boxE from 17:51 to 19:35 UTC. boxA rebooted at 15:08 and 16:15 UTC. The lane stopped at about 16:07, 17:52 and 19:05 UTC. Each time, the queues on the other boxes kept running, and the next attempt took them over from `STATE.txt`.

## 1. The twoshort layouts under the layer reader

The twoshort lane builds two 9-arms, or an 8-arm and a 9-arm, around a staircase corner, at m 28 to 31. The layer reader takes all 13 of its layouts (796, 851, 852, 910 to 914, 973 to 976 and 978). Each reads as two arms of tilted layers 8 and 9 or 9 and 9, with twin layers at the best cut.

- **Up, 14 walks (7 donors at cuts 0 and 1).** The best step ends 2e-7 of side below the bar (973 from 910). 852 from 793 and 974 from 911 end 1e-9 to 2e-9 below it. The twoshort and family takes hold these n lower, so none certifies. The other 11 steps end 2.5e-4 to 9.4e-3 above the bar.
- **Down.** The family lane walked all 13 layouts one and two shells down before us. Every step ended 1.2e-2 to 1.9e-2 of side above the bar. So we dropped 11 of our 13 down walks. 973 and 914 down end 6.6e-4 and 7.9e-3 above it.

So the reader works on these layouts, but a shell step does not beat a new staircase corner built for the n itself.

## 2. The lists

All walks ran with `SQ_TWIN=5.5e-2`, `SQ_APART=3e-2` and the fq quench of `finish()`, as in round 16. A plain walk stops after 2 misses in a row. A walk at another cut stops at its first miss.

- fa and fb: the twoshort layouts (section 1).
- fb00, 15 walks: up and down from the held layouts that the round 16 gate moved.
- fb0, e and f0, 11 walks: the new midm 374, 421, 604 and 876, the twoshort 793 and the classfill 703.
- f00 and f000, 13 walks: our own new layouts, and the held 596, 647 and 701 at cuts 1 and 2.
- f02 and f03, 12 walks: the corners 914 and 915, the stair-c 861 and 982, and the stair-c near 804, 919 and 986.
- fy, 5 walks: the modules near 552, 652, 704, 756 and 758 at cut 1.
- fz, 29 walks: the round 16 leftovers at cuts 1 to 3.
- g1 and g2, 26 walks: the new layouts of 17:48 UTC, among them the midm 647, 701, 755 and 904 that `read_any` refuses.
- g0, g05, g06, g065, g07 and g3, 71 walks (18:15 to 19:05 UTC). They walk every new layout of the corners, stair-c, border, family and polish lanes at cuts 0 and 1, and our new 921, 984 and 755. They also walk midm layouts down where the step as built starts 0.005 to 0.015 of side above the bar.
- a0, a00, a05 and a1, 27 walks (19:15 to 20:05 UTC). They walk the new family 851, 858, 860, 861, 920 and 922 up, the stair-c 920 and 984, and our new 919, 921 and 922 up. They also walk the new midm 986, 994, 995 and 999 down, to n where the held file still holds the bar.

## 3. What ran

Counts at 20:10 UTC. `scripts/lists.py` counts a step in a list when the list holds its donor, direction and cut, so a layout that two lists walked shows in both.

| list | walks | steps | built | refused | below the bar | in the take |
|---|---|---|---|---|---|---|
| fa, fb: twoshort | 16 | 16 | 16 | 0 | 1 | 0 |
| fb00: moved held layouts | 15 | 20 | 19 | 1 | 5 | 0 |
| fb0, e, f0: midm, twoshort, classfill | 11 | 16 | 16 | 0 | 2 | 0 |
| f00, f000: our layouts, other cuts | 13 | 26 | 25 | 1 | 13 | 1 (597) |
| f02, f03: corners and stair-c | 12 | 14 | 14 | 0 | 3 | 1 (924) |
| fy: modules near | 5 | 5 | 5 | 0 | 0 | 0 |
| fz: round 16 leftovers | 29 | 30 | 27 | 3 | 1 | 0 |
| g1, g2: layouts of 17:48 UTC | 26 | 55 | 53 | 2 | 10 | 2 (648, 755) |
| g0 to g3: layouts of 18:15 to 19:05 UTC | 71 | 140 | 132 | 8 | 14 | 1 (921) |
| a0 to a1: layouts of 19:15 UTC | 27 | 49 | 47 | 2 | 11 | 4 (919, 922, 936, 982) |
| all | 225 | 371 | 354 | 17 | 60 | 9 |

"Below the bar" is a step more than 1e-9 of side under the bar when its walk started. "In the take" is the lane's rule. The file is floatsafe at 2.2e-11. Its score is more than 1e-10 below the held score and below the same n in every live take dir.

## 4. Certified results

| n | step | start | held side | new side | score gain | over the best other take |
|---|---|---|---|---|---|---|
| 982 | 2 shells up at cut 0 | the family 858 of 19:07 UTC | 31.810539459 | 31.801262053 | 2.961e-04 | 1.96e-04 (classfill) |
| 919 | 1 shell up at cut 1 | the family 858 of 19:07 UTC | 30.796505607 | 30.790280876 | 2.053e-04 | 2.05e-04 (held) |
| 922 | 1 shell up at cut 0 | the family 861 of 19:17 UTC | 30.827151956 | 30.821430315 | 1.884e-04 | 3.5e-06 (stair-c) |
| 921 | 1 shell up at cut 1 | the family 860 | 30.815577970 | 30.812953796 | 8.647e-05 | 5.6e-06 (polish) |
| 924 | 2 shells up at cut 1 | the stair-c near layout 804 | 30.854910472 | 30.852759708 | 7.075e-05 | 7.08e-05 (held) |
| 755 | 2 shells up at cut 0 | the midm 647 | 27.908429775 | 27.907888451 | 1.970e-05 | 1.8e-06 (midm) |
| 597 | 2 shells down at cut 1 | the held 701 (our round 16 step) | 24.894187881 | 24.893854241 | 1.365e-05 | 1.37e-05 (held) |
| 648 | 1 shell down at cut 0 | the midm 701 | 25.903724065 | 25.903443654 | 1.102e-05 | 1.10e-05 (held) |
| 936 | 1 shell down at cut 0 | the midm 999 | 30.992553201 | 30.992553182 | 6.3e-10 | 6.3e-10 (held) |
| total | | | | | 8.914e-04 | 5.08e-04 |

The certified files up to 936 had one fq quench (default flags). It moved only 863, by 2.0e-5 of side. 919, 922 and 982 certified in a fast collect at 19:56 UTC and had no quench. A full collect with the quench took 20 minutes at load 34 on boxA. The round 17 file took 597, 647, 648, 700 and 755 from this take at 17:42 UTC.

**Lost to other takes.** Six n left the take after they certified. The midm lane holds 647 and 510 lower, the modules lane 700, the stair-c lane 863, 920 and 984.

**The family loop.** The family lane steps a layout down with `family_step.py`, and we step it back up at the layer reader's cuts. 919, 921, 922 and 982 all came this way within 20 minutes of the family layout landing. The family lane then often steps our result down again, so the two lanes keep moving the same n from 858 to 984.

## 5. Next runs

1. **Merge the take dir** `take-readers-r17`. `take.tsv` names each source and licence.
2. **Walk each new family, corners and stair-c layout from 850 to 990 up, within minutes of it landing.** Walk one and two shells at cuts 0 and 1. In this round, 5 of the 9 n came from these walks, worth 7.6e-4 against held. A step takes 1 to 8 minutes. Watch the take dirs every 5 minutes, not 10.
3. **Quench 919, 922 and 982 once with fq** at the start of the next round, on boxC or boxD.
4. **Certify only the new raw files.** The full take re-certifies every raw file of the round, and took 8 minutes at load 34. `work/collect-fast.sh` takes the new files and the kept ones in 67 seconds.
5. **Walk down from the midm layouts toward n the held file still holds.** 999 down to 936 certified at 6e-10. 995, 994 and 986 down missed by 4e-4 to 4e-3 of side.
6. **Drop the walks from the twoshort layouts.** No shell step beat the twoshort lane's own corners.

## Files of round 17

| file | what it is |
|---|---|
| [`results/readers-r17-2026-11-12.tsv`](../results/readers-r17-2026-11-12.tsv) | every walk step of this round (362 rows) |
| `<scratch>/bounties-squares/take-readers-r17/` on boxA | the take dir: one csv per certified n, `take.tsv` and `STATE.txt` (the queues started, adopted and killed) |
| `take-readers-r17/work/` | the queues (`box/q0` to `box/q3`), the runner `box/run.sh`, `collect.sh`, `collect-fast.sh`, the rows per box, `scripts/adddonors.py` (the layouts of every live take dir as donors), `scripts/need.py` (the side of each cut as built against the bar), `scripts/lists.py` (the table of section 3), `scripts/queue3.sh` (queues on 3 slots) |

`family_readers.py` did not change in this round.

## Summary of round 17

- 9 n in the take for 8.91e-4 against held, 5.08e-4 over the best other take: 982, 919, 922, 921, 924, 755, 597, 648 and 936.
- The best yield is one or two shells up from the family lane's newest layouts at 858 to 861. That gave 919, 921, 922 and 982 in the last hour of the round.
- The twoshort layouts read, but no shell step from them beats the twoshort and family takes.
- Next: walk each new layout from 850 to 990 up within minutes, quench 919, 922 and 982, and certify only new raw files.

---

# Round 19 (2026-11-12)

**Result: 5 n in the take at 22:27 UTC, for 6.995e-04 of score against the round 17 file (`gate/cand-round17-1112a`). Against the best row of every frozen `take-*-r17` dir (ours included) and every live `take-*-r19` dir, they are worth 8.02e-05. Most of the gain over held is already in the round 17 takes, so round 18 holds it. Nothing was submitted from here.**

Words used here: "held" is `gather/round17-2026-11-12a.csv`. "The bar" of an n is the lowest of its held score and its score in every `take-*-r17` dir and every live `take-*-r19` dir. The take dir is `take-readers-r19` on boxA. The walks ran on 2 processes on boxD and 1 on boxC from 20:22 to 22:26 UTC.

## 1. The fq quench of the round 17 results

919, 922 and 982 certified in round 17 without the quench. One fq quench (default flags, `quench2.py`) from each certified file moved none of them. The change was 0.0 of side for each. So the round 17 files need no change.

## 2. Walks from the newest layouts

A loop on boxA (`work/watch.sh`) ran every 4 minutes. It copied each new or changed layout of every take dir into the donors. It queued walks (`work/scripts/autoq.py`) and certified the new raw files (`work/collect-fast.sh`). Family, corners, stair-c and border layouts at n 790 to 937 got walks up at cuts 0 and 1. Their near layouts got cut 0 only. Layouts of other lanes got cut 0 only. New layouts went to the front of the queue. Walks from twoshort layouts were dropped. Walks down from midm layouts waited at the end of the queue and did not run.

71 walks started and made 103 steps. 28 steps ended below the bar at the start of their walk. Four of the five certified n came from family layouts, one shell up:

- 919 from the family 858 of about 20:45 UTC. The family lane had stepped our round 17 919 down to 858. One shell up gave a 919 that is 2.6e-4 of side lower than the round 17 take.
- 920 from the family 859 of 19:52 UTC. Its walk went on to 983 at the same side as the next row.
- 983 from the family 920 of 19:52 UTC, at cut 1. Cut 0 gives the same layout.
- 932 from the family 871, 5.7e-6 of side under the bar.

The fifth is 924, one shell up from the family 863 of 22:02 UTC. Two shells up from the stair-c 804 and one shell up from the stair-c 863 give the same layout, 4e-11 of score higher. The walk from the 804 went on to 987 and certified it at 6.97e-5 below held. Then the stair-c lane took a lower 987. Our step from its 863 gives that same 987 to the last digit. So 987 left our take.

Near misses at 982: the family 858 two shells up ended 1.7e-6 and 9.6e-6 of side above the bar. Our own 919 one shell up at cuts 1 and 2 ended 8e-6 and 1.7e-6 above it.

## 3. Layouts that `read_any` refuses

The family lane named 13 layouts in its round 17 report. At 20:22 to 20:24 UTC it handed over 138 more: every layout of the round 17 file at n 790 and above that `read_any` refuses. The layer reader reads 48 of the 138 and refuses 84 (`work/unread2/read.log`). Most refusals are plain grids or have layers on one wall only.

`work/scripts/rank.py` gives, for each layout that reads, the side as built of the step up and down minus the bar side of the target. In the steps of round 17, an up step that started 0.04 to 0.08 of side above the bar ended below the bar in 28 of 92 tries. A down step that started 0.005 to 0.010 above it did so in 10 of 30.

That rank did not carry over to the held layouts. Their up steps started 0.050 to 0.066 above the bar as built, like the family steps that won. After the squeeze, the held 810 ended 1.0e-2 above the bar, the held 818 2.1e-3, and the family 800 1.5e-3. The held 927 came closest: one shell up to 990 ended 2.0e-5 of side above the bar. The down walks from held layouts waited behind the new layouts and did not run. So no layout from this list certified.

## 4. Certified results

| n | step | start | held side | new side | gain on held | over the best other take |
| --- | --- | --- | --- | --- | --- | --- |
| 919 | 1 shell up at cut 0 | the family 858 of about 20:45 UTC | 30.796505607 | 30.790018622 | 2.140e-04 | 8.65e-06 (readers r17) |
| 983 | 1 shell up at cut 1 | the family 920 of 19:52 UTC | 31.816325821 | 31.811880510 | 1.418e-04 | 1.6e-07 (border r17) |
| 924 | 1 shell up at cut 0 | the family 863 of 22:02 UTC | 30.854910472 | 30.850708906 | 1.382e-04 | 6.75e-05 (readers r17) |
| 920 | 1 shell up at cut 0 | the family 859 of 19:52 UTC | 30.805316663 | 30.799088348 | 2.053e-04 | 3.7e-06 (family r17) |
| 932 | 1 shell up at cut 0 | the family 871 of round 17 | 30.937941886 | 30.937936226 | 1.854e-07 | 1.9e-07 (held) |
| total | | | | | 6.995e-04 | 8.02e-05 |

Each certified file had one fq quench (default flags) on boxD. It moved none of them.

## 5. Two traps: a donor rewritten under the same name

Other lanes rewrite a layout under the same file name when they certify it again. Two things then go wrong.

- **The result is overwritten.** A walk writes its result as `raw/N-STEPfromDONOR.csv`. The second walk of a rewritten donor writes the same name. At 21:10 UTC the second walk of the family 858 replaced our best 919 (30.790018621) with a worse one (30.790050325). The next collect took the worse one. The better file came back from its quench copy. `collect-fast.sh` now copies each raw file once, by its content, into `work/rawarc/` as `N-STEPfromDONORvHHMMSS.csv`, and certifies from there.
- **The walk does not run.** `family_readers.py walk` skips a donor, direction and cut that its slot walked before, from its rows file. So a re-walk of a rewritten layout on the same slot ends at once with no step. This hit the family 858 of 21:20 UTC on two slots. `autoq.py` now queues a copy of the donor as `DONORvHHMMSS`, so each version has its own name. `work/scripts/srcver.py` names the source of each version.

## 6. Next runs

1. **Merge the take dir** `take-readers-r19`. `take.tsv` names each source and licence.
2. **Keep the loop with the family lane.** The family lane steps our new layout one shell down, and we step its result up. Four of five n came this way. Start `watch.sh` with the versioned donors from the first minute.
3. **Give each walk a versioned donor from the start** (`autoq.py` as it is now). In this round some re-walks did not run until 21:51 UTC.
4. **Down walks from held layouts, in an idle slot.** The held 818, 927, 864, 809 and 923 start 0.005 to 0.010 above the bar as built (`rank.py`). They did not run.
5. **Drop the up walks from held layouts that `read_any` refuses.** Three of four ended 1.5e-3 to 1.0e-2 above the bar.

## Files of round 19

| file | what it is |
| --- | --- |
| [`results/readers-r19-2026-11-12.tsv`](../results/readers-r19-2026-11-12.tsv) | every walk step of this round (103 rows) |
| `<scratch>/bounties-squares/take-readers-r19/` on boxA | the take dir: one csv per certified n, `take.tsv`, `STATE.txt` and `near/` |
| `take-readers-r19/work/` | the runner `box/run2.sh` (walks plus an fq quench queue), `watch.sh`, `collect-fast.sh`, the queues `box/q0` to `box/q2`, `rawarc/` (every raw file by version), `scripts/autoq.py`, `rank.py`, `srcver.py`, `gains.py`, `table.py`, `unread2/read.log` |

`family_readers.py` did not change in this round.

## Summary of round 19

- 5 n in the take: 919, 920, 924, 932 and 983. They are worth 7.00e-4 against the round 17 file and 8.0e-5 over the best other take.
- All five are one shell up from the newest family layouts. The family lane steps our layouts down and we step them up again.
- The quench of the round 17 919, 922 and 982 moved nothing.
- The layer reader reads 48 of the 138 layouts that `read_any` refuses. No up step from them certified.
- Two traps with donors rewritten under the same name are fixed in the lane scripts.

---

# Round 20 (2026-11-12 and 13)

**Result: 5 n in the take at 00:58 UTC, for 4.691e-04 of score against the round 18 file (`gate/cand-round18-1112a`). Over the best row of every frozen `take-*-r19` dir and every live `take-*-r20` dir they are worth 2.447e-04. Nothing was submitted from here.**

Words used here: "held" is `gather/round18-2026-11-12a.csv`. "The bar" of an n is the lowest of its held score and its score in every `take-*-r19` dir and every live `take-*-r20` dir. The walks ran on 2 processes on boxD and 1 on boxC from 22:43 to 00:56 UTC. A harness restart at about 22:48 UTC stopped the first agent and the loop on boxA. The box walks ran on, and the loop was back at 22:51.

## 1. Down walks from the new designs of the round

This is the finding of the round. Two of the five n come from down walks that start at a design another lane made in this round. Two more are one shell up from a new layout at the n below:

- 868: one shell down from the border 929 of about 23:25 UTC (a border on the classfill 870). The family lane handed that 929 over as a layout `read_any` does not read. The layer reader reads it, and its down step started 0.0083 of side above the bar as built. Two shells down from it gave 809, which the midm lane later took lower.
- 810: three shells down from the classfill 993 of about 00:43 UTC (993, 930, 869, 810). The corners 993 gave an 810 at 00:05 UTC, and the polish lane took it lower with a quench. Then the stair-c 993 and the classfill 993 each gave a lower 810.
- 930: one shell up from the stair-c 869. One shell down from the stair-c 993 gave a 930 first.
- 993: one shell up from the polish 930.

`work/scripts/downs.py` reads each new layout of a live take once, by content. It compares the down step as built with the bar, as `rank.py` does. It queues the walk when the step starts under +0.010 of side above the bar. `work/scripts/dloop.sh` ran it every 5 minutes until 00:45 UTC. The down steps from round 20 layouts: 65 steps, 16 below the bar at the start of their walk. The up steps from round 20 layouts: 61 steps, 8 below the bar.

## 2. Up walks from the layouts of round 19

In round 19, the newest family layouts one shell up gave 4 of 5 n. In this round the family 803, 811, 853, 862 and 863 of round 19 and our own 920, 924 and 932 gave none. The other lanes had new designs at most of the targets (862, 870, 923, 924, 931), so the bar was lower. One near miss: 862 from the family 803 ended 1.9e-5 of side above the bar.

From the layouts the family lane handed over at 22:52 UTC (`read_any` does not read them), the layer reader read 9 that round 19 had not read (`work/unread3/read.log`). The midm 800 of round 19, one shell up, certified 859 at 4.39e-5 below held at 00:36 UTC. The polish lane then took it lower by a quench. The held 813 two shells up gave 933, 5.1e-7 below held.

## 3. The queue under load

Load on boxC reached 56 on 10 cores. A walk took about 12 minutes there and 6 to 8 minutes on boxD. 80 walks ran, and 120 were still waiting at 00:55 UTC. Three changes put the best measured walks first:

- `work/scripts/autoq.py` gives the cut 1 walks the prefix `cz` and walks from near layouts the prefix `g`, so they wait behind the cut 0 walks of new layouts. In this round, cut 1 ended within 1e-6 of side of cut 0 in 4 of 5 pairs. In round 19, the stair-c near layouts gave 1 step below the bar in 18.
- `work/scripts/dedupe.py` keeps one donor for each n, direction and cut among the waiting walks: the one with the lowest side. Lanes polish each other's results, so one design comes in several versions. 870 one shell up from four versions of 811 ended within 3e-5 of side of each other.
- `autoq.py` now takes main-lane layouts up to n 1000. It stopped at 990, so the corners 993 and 996 did not get a down walk on their own.

## 4. Certified results

| n | step | start | held side | new side | gain on held | over the best other take |
| --- | --- | --- | --- | --- | --- | --- |
| 810 | 3 shells down | the classfill 993 of about 00:43 UTC | 28.905568520 | 28.900291770 | 1.854e-04 | 5.58e-05 (polish r20) |
| 993 | 1 shell up | the polish 930 of about 00:40 UTC | 31.924791454 | 31.921072322 | 1.180e-04 | 1.159e-04 (stair-c r19) |
| 930 | 1 shell up | the stair-c 869 of about 00:30 UTC | 30.917455329 | 30.914585196 | 9.412e-05 | 1.4e-06 (polish r20) |
| 868 | 1 shell down | the border 929 of about 23:25 UTC | 29.898591944 | 29.896498904 | 7.104e-05 | 7.10e-05 (held) |
| 933 | 2 shells up | the held 813 | 30.943773310 | 30.943757718 | 5.105e-07 | 5.1e-07 (held) |
| total | | | | | 4.691e-04 | 2.447e-04 |

Each certified file had one fq quench (default flags) on boxD. It moved the stair-c 993 chain 810 by 3.0e-6 of side and the corners 993 chain 810 by 4.9e-5. It moved no other file.

## 5. A trap: a loop stopped by another lane

At 00:10 UTC another lane stopped our `watch.sh` by its pid, taking it for its own expired loop. For 10 minutes our loop did not run. It now runs as `readers-watch20.sh`. Give each loop a name with the lane in it, and check the working folder of a loop before you stop it.

## 6. Next runs

1. **Merge the take dir** `take-readers-r20`. `take.tsv` names each source and licence.
2. **Down walks from each new design of the round, at the front of the queue, from the first minute.** Run `downs.py` and `dedupe.py` in the loop. In this round the down steps from new designs gave 16 steps below the bar in 65, and 810 and 868.
3. **Step back up from each down result of another lane's design.** 930 and 993 came this way, one shell up from the stair-c 869 and the polish 930.
4. **Put the up walks from the round 19 layouts last in the queue.** In this round, 29 such steps gave 3 below the bar and no n. Other lanes had new designs at most targets.
5. **Run the never-walked held layouts in an idle slot.** The held 817, 875 and 815 up and the held 999 and 815 down did not run. The held 813 two shells up gave 933.

## Files of round 20

| file | what it is |
| --- | --- |
| [`results/readers-r20-2026-11-13.tsv`](../results/readers-r20-2026-11-13.tsv) | every walk step of this round (164 rows) |
| `<scratch>/bounties-squares/take-readers-r20/` on boxA | the take dir: one csv per certified n, `take.tsv`, `STATE.txt` and `near/` |
| `take-readers-r20/work/` | the loop `readers-watch20.sh`, `collect-fast.sh`, the queues `box/q0` to `box/q2`, `rawarc/`, and `scripts/`: `autoq.py`, `downs.py`, `dloop.sh`, `dedupe.py`, `qbatch.py`, `reorder.sh`, `reorder2.sh`, `rank.py`, `yield.py`, the read logs `unread3/`, `read4/` to `read8.log` |

`family_readers.py` did not change in this round.

## Summary of round 20

- 5 n in the take: 810, 868, 930, 933 and 993. They are worth 4.69e-4 against the round 18 file and 2.45e-4 over the best other take.
- 810 and 868 come from down walks that start at new designs of other lanes. 930 and 993 are one shell up from new layouts at the n below. `downs.py` queues the down walks within 5 minutes of a new layout.
- 859 and 809 also certified, and then the polish and midm lanes took them lower. The gain stays in round 20 through their takes.
- The up walks from the round 19 family layouts gave nothing this time.

# Round 21 (2026-11-13)

**Result: 3 n in the take at 12:13 UTC (753, 868 and 993), for 4.247e-04 of score against the round 19 file (`gate/cand-round19-1112a`). Over the best row of every frozen `take-*-r20` dir and every other live `take-*-r21` dir they are worth 5.96e-05. We certified 14 n in the round. 11 of them went lower in the take of another lane, so their gain stays in round 21 there. Nothing was submitted from here.**

Words used here: "held" is `gather/round19-2026-11-12a.csv`. "The bar" of an n is the lowest of its held score and its score in every frozen `take-*-r20` dir and every live `take-*-r21` dir. The walks ran on 2 processes on boxD and 1 on boxC.

The round ran in three parts. The first agent worked from 01:03 to about 01:25 UTC and stopped on a usage limit. Its loop and its box walks ran on until their 03:25 UTC deadline. boxA rebooted at 05:36 UTC. A second agent restarted the loop and the walks at 09:52 UTC and stopped at 09:55 on a lost login. The third agent adopted the running jobs at 10:00 UTC and kept them to 12:10 UTC.

## 1. Our own new layouts, walked again

The midm lane kicked an 869 at about 03:20 UTC. One shell down from it gave 810, two shells down gave 753, and one shell up gave 930. After the restart the loop made our own 810, 930 and 753 donors (`N-rd21`), and their walks gave more:

- 993: three shells up from our 810, the first step at cut 1 of the layer reader. It ended 1.617e-3 of side under the bar. The same walk at cut 0 ended 1.022e-3 under it, so cut 1 was 5.9e-4 of side better on this chain.
- 698: four shells down from our 930, and two shells down from our 810. Both ended 5.27e-4 of side under the bar.
- 753: three shells down from our 930, a little lower than two shells down from the midm 869.

## 2. New designs of other lanes, walked within minutes

- 929 and 868: one and two shells down from the border 992 of about 10:14 UTC. The border lane rewrote its 992 at 10:37, and the new file gave a lower 929 (cut 0) and a lower 868 (cut 1). The down step of the first 992 started 0.0130 of side above the bar as built, which is over the 0.010 cut of `downs.py`. `autoq.py` queued it anyway, because border is a main lane. It ended 1.0e-3 of side under the bar, so the 0.010 cut is too tight for a new design.
- 992: two shells up from our 868, which is two shells down from the border 992. This down and up round trip ended 3.25e-4 of side under the border 992 it started from. A second round trip from our 992 did not work: its down step ended 7.3e-3 above the bar.
- 931: one shell up from the stair-c 870 of about 09:57 UTC.
- 855: one shell up from the k123 796 of about 10:08 UTC.
- In the first part, the midm 809 gave 752 one shell down and 868 one shell up. The modules 813 gave 756 one shell down. A family near layout of 931 gave 994 one shell up.

## 3. Kicked copies of our results are new layouts

The midm lane kicked our 868 (`midm_scan.py`, lkick) and moved it 5e-4 of side lower. One shell up from that copy gave 929 at 2.526e-4 under held, lower than our 929 from the border 992 and lower than the invent kick of it. A kick moves a layout by 1e-5 to 1e-3 of side. A quench copy moves it by 1e-12 to 1e-7. So walk the kicked copies at once, and put the quench copies last.

Two traps in the loop. First, `autoq.py` does not queue a donor again while an older walk of it waits. That older walk reads the older version of the file. The midm 868 and the invent 929 were skipped this way until we queued them by hand. Second, `dedupe.py` keeps one walk per n, direction and cut, so it can drop a kicked copy in favour of an equal or lower layout. That is right when the files are one design.

## 4. The follow lanes take each result lower within minutes

The polish, invent, midm, harvest and family lanes read our take. Of the 14 n we certified, 11 left our take 5 to 30 minutes later, when another lane quenched or kicked them 1e-12 to 5e-5 of score lower. The gain stays in round 21 through their takes. Our take holds the results they have not reached yet.

## 5. What gave nothing

- Down walks from held round 19 layouts (batch h, 11 walks, 22 steps): no step under the bar. Their down steps started +0.005 to +0.008 above the bar as built.
- Walks from the forensics 749 and 750 (new designs under n 790): +3.4e-4 and +5.5e-3 of side above the bar at the first step.
- Down walks from our 993, and up walks from our 698 and 753: they ended within 4e-5 of side of the bar at cut 0. The 869 chain was used up after 993.
- In all, 195 walks ran with 384 steps: 109 walks from 01:15 to 03:25 UTC and 86 from 09:51 to 12:12 UTC. 50 steps ended under the bar of the time.

## 6. Certified results

Gain is against held. "Lowest now" is the take that holds the lowest row at 12:13 UTC.

| n | step | start | our lowest score | gain on held | lowest now |
| --- | --- | --- | --- | --- | --- |
| 810 | 1 shell down | the midm 869 | 0.015379313231 | 2.588e-04 | harvest r21 |
| 929 | 1 shell up | the midm kick of our 868 | 0.013817741969 | 2.526e-04 | invent r21 |
| 868 | 1 shell down | the invent 929 | 0.014575241010 | 2.491e-04 | **ours** |
| 809 | 1 shell up | the midm 752 | 0.015534434380 | 1.741e-04 | harvest r21 |
| 993 | 3 shells up, cut 1 | our 810 | 0.012933190311 | 1.673e-04 | **ours** |
| 930 | 1 shell up | the midm 869 | 0.013668530041 | 1.548e-04 | harvest r21 |
| 752 | 1 shell down | the midm 809 | 0.016544149535 | 1.447e-04 | midm r21 |
| 931 | 1 shell up | the stair-c 870 | 0.013400250975 | 9.158e-05 | harvest r21 |
| 855 | 1 shell up | the k123 796 | 0.016813253833 | 6.740e-05 | family r21 |
| 992 | 2 shells up | our 868 | 0.013303995493 | 2.953e-05 | harvest r21 |
| 698 | 4 shells down | our 930 | 0.017444581871 | 1.993e-05 | harvest r21 |
| 756 | 1 shell down | the modules 813 | 0.015478571084 | 1.345e-05 | family r21 |
| 753 | 3 shells down | our 930 | 0.016358734532 | 8.209e-06 | **ours** |
| 994 | 1 shell up | a family near 931 | 0.012750341049 | 2.652e-06 | classfill r21 |

The take keeps 753, 868 and 993: 4.247e-04 against held, and 5.96e-05 over the best other take. By n: 993 is 5.14e-05 under our own round 20 993, 753 is 8.2e-06 under held, and 868 is 2.5e-09 under the midm 868. Each kept file had one fq quench (default flags) on boxD. It moved none of the three.

## 7. Next runs

1. **Walk each kicked copy of a certified result at once, up and down, at cuts 0 and 1, at any n.** A kick moves a layout by 1e-5 to 1e-3 of side. This round, the midm kick of our 868 gave 929 (2.53e-4) and the midm kick of 752 gave 809 (1.74e-4). Fix `autoq.py` so a new version of a donor is queued even when an older walk of it waits, and let it take n under 790.
2. **Raise the down cut of `downs.py` to +0.015 of side for new designs.** The border 992 started +0.0130 above the bar as built and ended 1.0e-3 under it, and gave 929 and 868.
3. **Try a down and up round trip on each new design.** Two shells down from the border 992 and two shells up again gave a 992 3.25e-4 of side under it.
4. **Step up at cut 1 at the start of a long up chain.** Our 810 three shells up gave 993 5.9e-4 of side lower at cut 1 than at cut 0.
5. **Put quench copies last, and drop the down walks from held round 19 layouts.** The quench copies moved by 1e-12 to 1e-7 and their walks ended at the bar. The held layouts gave 0 steps under the bar in 22.

## Files of round 21

| file | what it is |
| --- | --- |
| [`results/readers-r21-2026-11-13.tsv`](../results/readers-r21-2026-11-13.tsv) | every walk step of this round |
| `<scratch>/bounties-squares/take-readers-r21/` on boxA | the take dir: one csv per certified n, `take.tsv`, `STATE.txt` and `near/` |
| `take-readers-r21/work/` | the loop `readers-watch21.sh`, `collect-fast.sh`, the queues `box/q0` to `box/q2`, `rawarc/`, and `scripts/`: `adddonors.py`, `autoq.py`, `downs.py`, `dedupe.py`, `qbatch.py`, `beat.sh`, `held21.py`, `frozen20.py`, `table.py`, `gain21.py` |

`family_readers.py` did not change in this round.

## Summary of round 21

- 3 n in the take: 753, 868 and 993. They are worth 4.25e-4 against the round 19 file and 5.96e-5 over the best other take.
- We certified 14 n in the round. 11 went lower in the takes of the polish, invent, midm, harvest, family and classfill lanes, and their gain stays in round 21 there.
- The results came from three sources. New designs of other lanes gave 929, 868, 931 and 855. Our own new layouts as donors gave 993, 753 and 698. Kicked copies of our results gave 929, 809 and 868.
- A round trip, two shells down and two up, took the border 992 3.25e-4 of side lower.


# Round 22 (2026-11-13)

The final take holds 9 n: 305, 379, 458, 503, 504, 650, 699, 855, 999. Their score gain is 0.00145784280387 against round 20 and 0.0013373619379 over the frozen round 21 and other round 22 takes.

The comparator snapshot is from 2026-11-13T15:29:04.163272+00:00. Each row beats round 20 by more than 1e-10 and is strictly below every competing take.

The workers logged 408 shell steps from 233 walks. They used 30,260 step seconds across two processes on boxD and one on boxC. Three steps reached their time limit. The queue held 2,273 specifications from 893 donor versions.

Fifteen distinct n certified during the round. Later kicks in other lanes took several of those n lower. All final rows passed floatsafe at 2.2e-11 and one completed default fq run on boxD.

The two boxes stopped at the compute deadline. We copied and checked 3,851 files from boxD and 3,452 from boxC by SHA-256. Both scratch directories were then removed.

## Results and source credit

Fresh public layouts gave the largest new donor family. Their source was `areebbb/sis-certified-union-micro-shrink-lb-22-17479`, notebook run 369173112, under Apache 2.0. The polish lane handed these files to us. A down step from 379 to 340 gained about 0.010325 of side before another lane kicked it lower. The 703 donor gave 650, 599, 550 and 503. The 270 donor gave 305, which the old 300-square floor would have skipped.

The final 379 returns from a kicked 340 and closely matches its public parent. The 855 return closely matches the invent parent's side. Their margins over remaining takes include gains from those parents when other lanes retract their rows. They do not measure new physical gain from the return itself.

The 458 margin over forensics is only 3.33e-15 of score. It passes the strict competing-score rule but has no practical margin. Forensics used our near 458 as its source.

The 999 result grew a fresh family 936. Its source chain includes the invent 875 and earlier corners and stair layouts. Full source chains and licences remain in `take.tsv` and `work/sources-all.tsv`.

## Queue changes

Each donor has an immutable copy named by its SHA-256. The hash and the copy use the same bytes. A waiting walk cannot hide a later version of that donor.

The queue accepts n from 1 to 1000 and both first cuts. New down steps normally enter when their built side is less than 0.015 above the bar. A local read that exceeds 25 seconds goes to a box for its first run.

Fresh certified layouts and family refusals come first. Explicit near handoffs follow them. Quench copies wait last. Family handoffs tagged as round 21 retain their historical priority. Targets within 0.001 of the stored board wait behind targets with larger gaps. These priorities preserve every queued walk.

New near files get a handoff line. The collector certifies each candidate, sends its guarded file to fq, and publishes after that box run. The final helper leaves a candidate unpublished if fq returns no completed output. It writes each csv before replacing `take.tsv` by rename.

## Controls

- The 814 down-and-up control returned side 28.944429713 against 28.944429709, a difference of 4.134e-9, in 12 seconds.
- Default fq shrank two separated squares from side 3 to 2.000000000050. A simulated fq failure left no publishable file.
- The collector kept the positive 458. It rejected an equal competing score and a held-score gain of only 5e-11.
- An expired deadline stopped before loading a deliberately missing donor.
- Geometry checks preserved translations, mirrors, row order and a 1e-9 perturbation. A changed tilt remained distinct.
- The copy checker accepted an exact copy and rejected altered bytes of the same size.

## Measured limits

The new 855 started 0.01477 above the best 796 as built. Its down step ended 0.00241 below that best side. The old 0.010 cutoff would have skipped this result.

The 997 down steps ended about 0.00768 above 934 and 0.00905 above 873. A two-shell return from 873 lowered the original 997 by 0.000531, but remained 0.003634 above the bar.

The 805 probe started 0.01571 above 748 and ended 0.003287 above it. The 974 probe missed 911 by 1.86e-5 at cut 0. Cut 1 missed by 1.86e-5 too. The automatic cutoff stayed at 0.015.

A return from 698 to 753 missed by 7.9e-6. Its third cut was refused because only two cuts ranked. A return from 796 to 855 matched the kicked parent to about 1e-9 of side.

Forensics rebuilt 458 from windows of our near 458 before our final quench was collected. It used our file for both windows.

For a re-run, use a fresh output folder and pass `--defer-list /dev/null`. The immutable donor files and their source records remain in the work folder.

## Next runs

1. Read fresh public and new-design layouts at every n. The 270 donor gave 305, and the 379 and 703 donors gave several winning walks.
2. Run both cuts up and down on fresh kicks. The 855 donor started 0.01477 above 796 and still beat it after the down step.
3. Preserve donor versions and schedule first passes before copies. Only 233 walks started from 2,273 queued specifications in this budget.
4. Try two-shell returns on new designs. The 997 test improved its donor by 0.000531 of side but missed the bar by 0.003634. Repeating that state has low priority.

## Files

- [The measured steps](../results/readers-r22-2026-11-13.tsv) include every completed or limited step and its donor.
- [The coordinator](../family_readers_follow.py) stores donor versions and provenance, then schedules box walks.
- [The reader](../family_readers.py), [box runner](../tools/readers/run.sh) and [quench helper](../tools/readers/quench.py) run and certify the candidates.
- `take-readers-r22/work/` holds the immutable donors, queue state, box archives, final manifests, controls and comparator snapshots.

# Round 23 (2026-11-13)

The final take holds 2 n. Its score gain against round 21 is 0.000158481375796.
Its gain over frozen round 22 and the other round 23 takes is 2.50910403565e-14.

The comparator snapshot is `2026-11-13T18:40:06.796107+00:00`. Each retained row beats round 21 by more than 1e-10.
Each is strictly below every competing take at that snapshot. Each received a completed default fq run from its guarded file before publication.

The retained numerical returns are 703, 971. Their larger gains against round 21 include their round 22 parents.

| n | side | gain against round 21 | gain over competing takes |
|---|---|---|---|
| 703 | 26.940182559860 | 5.73164786397e-05 | 4.4408920985e-15 |
| 971 | 31.658051210166 | 0.000101164897157 | 2.0650148258e-14 |

The workers logged 302 steps from 177 reader walks and 1 band step.
They logged 29,235 step seconds. 6 steps reached their time limit.
The queue held 2533 specifications from 963 donor versions.
The guard excluded 18 specifications for rectangle parts. Published rows covered 5 distinct n.

Both box archives passed SHA-256 checks on 5432 files.
The finisher removed both box scratch directories after those checks. No reader search process remains.

## Queue and controls

The reader follows fresh public files and new designs at every n from 1 to 1000. It keeps the 0.015 down-step threshold and both first cuts. Fresh handoffs precede frozen donors and quench copies.

The coordinator restores immutable round 22 donor versions whose first cuts never started. It retains each version's source and licence. Completed cuts stay excluded. Cached geometry and rank estimates avoid reading the same frozen donor again on boxA.

The 814 down-and-up control returned within 4.134e-9 of its starting side in 12 seconds. Default fq shrank the separated two-square control from side 3 to 2.000000000050.

The collector kept its positive row. It rejected an equal competing score and a held-score gain of 5e-11. A simulated fq failure produced no publishable file.

The pending-version control restored an unstarted cut and excluded completed cuts. The archive checker accepted an exact copy and rejected altered bytes of the same size. A decimal expired deadline stopped the box runner before it loaded any donor.

Both boxes use scipy 1.18.1. Two serial workers run on boxD and one on boxC. The common deadline for search and final quenches is 18:30 UTC. Worker starts and finishes also enter the append-only state file.

## Source credit

The n=971 return comes from the round 22 family 908. Its parent is the public 971 from `areebbb/sis-certified-union-micro-shrink-lb-22-17479`, under Apache 2.0. At its first publication, its score margin over the frozen harvest 971 was only 2.07e-14. Its larger gain against round 21 belongs to that public parent.

## Intake and scheduling

Harvest JSON sidecars supply source and licence fields for near layouts. A partial JSON copy leaves the existing source record intact.

Rectangle parts under `work/interior/` stay out of whole-layout walks. Nine such files entered before this guard. The control retained complete near and unread layouts.

A fresh high-n design with no target above it gets one down probe when the usual 0.015 threshold refuses it. Other automatic walks keep that threshold.

The first ten comparable first-step pairs favored cut 0. Seven pairs ended within 1e-5 of side. Cut 0 was lower by more in three pairs, and cut 1 in none. Fresh first cuts now run before second cuts. Both cuts remain queued before frozen donors.

Two near-648 kick files differed by only 2.39e-9 in side, but by up to 0.0596 in position and 0.0371 radians in angle. The geometry-equivalence probe failed. Both versions remain queued, and no new geometry deduplication rule runs.

Own two-down ends enter discovery before unrelated handoffs. The 863 end from the new 987 waited 17 minutes under the previous intake order. The positive control found that exact end with its parent source before ordinary handoffs.

## Fresh chains

The new modules 503, after the polish lane's fq run, gave 550 and 599 on upward walks. Their guarded ends gained 0.000191726 and 0.0000875104 over frozen round 22. Other lanes hold the lower copies.

The fresh k123 990 join gave 927 one shell down and 866 two shells down. At their first retained collection, 866 gained 0.000174820 over the frozen best. The 927 margin over the best competing take was 0.000000340443.

## Numerical returns

A side gain under 1e-7 no longer resets the walk's miss counter. Raw files and certification rules stay the same. `walk --min-progress 0` restores the old continuation rule.

Ten of the first 18 below-bar steps were under this threshold. A replay of 93 completed walks preserved all eight meaningful below-bar steps. It would avoid ten later steps totaling 1,887 logged seconds. That figure is a replay estimate, not measured CPU savings.

The positive control keeps a meaningful gain after one numerical return. The negative control stops two consecutive numerical returns. Already running walks finish under their original rule.

## Fresh band screen

The new quartic 534 and 581 fail the band frame. Their tilted squares reach 3.7 and 5.6 from the diagonal. The 847 frame reads.

The 414 control passed: three shells up, then down at the same cut, recovered every square within 1e-8. The 847 cuts at one and three shells overlap by 0.398 and 0.234, beyond the 0.1 repair allowance.

Two shells down build 734. The LP and fq finish at side 27.600801735, still 0.009423589 above the bar. The run took 21 seconds. The as-built layout and its source sidecar are in `near/734-banddown2from847-r23h168ca12ed7dc4df0.csv`.

The screen used boxC's existing slot after its active walk ended. The slot resumed its normal queue afterward. A new period or repair step must change the overlap before these band cuts run again.


## Files

- [Measured steps](../results/readers-r23-2026-11-13.tsv).
- [Reader and continuation rule](../family_readers.py).
- [Coordinator and source records](../family_readers_follow.py).
- [Serial box runner](../tools/readers/run.sh).
- `<scratch>/bounties-squares/take-readers-r23/` holds the take, near layouts and state.
- Its `work/` folder holds immutable donors, source records, controls and verified box archives.

# Round 24 (2026-11-13)

The baseline is the round 23 candidate, `gather/round23-2026-11-13a.csv`.
Only live round 24 takes set the competing bar. Excluded frozen rows cannot suppress a clean result.

## Queue and sources

All 2,338 unstarted specifications were reranked against the candidate and the stored board.
The source check admitted 1,100 specifications from 369 donor versions. It excluded 1,238 specifications outside the clean pool or without traceable ancestry.
Both first cuts remain queued. Fresh designs precede the saved specifications.

The intake follows fresh module and k123 designs first. It imports the ancestry checker from [forensics_sources.py](../forensics_sources.py).
Reader ends retain their immutable parent's source record. Each accepted source has a saved admission record.
The candidate and changed round 23 rows supply the clean roots. Other inputs need recorded ancestry.

## Controls

The reader's 814 down-and-up control returned within 4.134e-9 of its starting side in 13 seconds.
Default fq on both boxes shrank the separated-square control from side 3 to 2.000000000050.
The first fq attempt lacked executable permission. Both controls passed after that permission was restored.

The collector retained its positive row. It rejected an equal competing score and a held gain of 5e-11.
The source control admitted the candidate's 639 and the clean k123 581.
It refused the excluded harvest 639, forensics 980, held-801 descendants and frozen round 23 variants of 639.
The copy checker accepted the exact copy and rejected altered bytes of the same size.

## Intake repairs

Near layouts now carry source sidecars and pinned ancestry beside each csv.
This repaired the module 985 admission. Its parent was a reader near layout whose source had appeared only in the central ledger.

Two module 973 designs and k123 755 needed historical public donor records.
Their removed top-level polish files remain in the frozen `work/candidates/` folder.
The source adapter verifies the archived per-n atlas row before it accepts those copies.
It appends the recovered upstream notice to the source and licence cells.
A recorded raw output can also match its near copy byte for byte. The adapter then verifies the source inputs.
An unrecorded work copy stays excluded.

A source audit found one queued 918 version that reached candidate 907.
That candidate row reaches the prohibited public source. The queue entry was withdrawn before it ran.
No certified reader row used that version. Other clean 918 versions remain eligible.

Second cuts from fresh designs move forward when the first cut ends 1e-7 to 1e-4 of side above the bar.
The control promoted the +5e-5 case. It left numerical returns, larger misses, completed cuts, frozen donors and quench copies unchanged.
Fresh module and k123 first cuts still run before these second cuts.

## Source groups

The main session changed the source rule at 20:05 UTC.
Rows now name their Samanyu seed ancestry in the licence cell. Rows with an unresolved seed cannot enter the take.
The original 58-row source table remains in `work/round23a-sources-58.tsv`.

For the 20 held-back targets, a row without Samanyu ancestry uses the round 22 reference and competes with that source group.
Seed descendants keep the original candidate reference. The collector replays near ends for those 20 targets.
Worker continuation still uses the original candidate bar. The collector applies the source-specific rule before the required guarded-file quench.

The source controls resolve candidate 581 to seed 365, candidate 698 to seed 811 and candidate 590 to public roots.
The guarded 871 control names seed 504. It passes without a competitor and fails against an equal competing score.
A classifier control caught a shared synthetic hash across counts. Its cache key now includes the donor identifier.

The metadata-only seed control caught generic source cells that hid module notices.
Those donors carry seeds 503 and 504. Full retained metadata now enters classification and fills incomplete source cells.
The affected guarded candidates had not been published. They remain subject to the original candidate bar.

## Worker recovery

Expanded source cells exceeded the workers' default CSV field limit of 131,072 bytes.
A 160,000-byte control failed before the repair and passed on both boxes afterward.
The reader now accepts fields up to 16 MiB.

Current jobs with no recorded first step were requeued: 1,421 on boxD and 721 on boxC.
The repair preserved 105 completed current specifications and kept excluded ancestry out.
Alias attempts and pre-step failures do not count as measured search walks.

The paired CC0 control classifies the licensed 581 as free and the original candidate 581 as a descendant of seed 365.
It recognizes the explicit negative seed label used by the k123 lane.
New CC0 module and k123 versions have priority even when their geometry matches an older design.

## Queue delays

Source checks and CSV failures delayed fresh follows. Large provenance files also slowed collection.
Compacting both JSON files reduced their combined size by 77,237,296 bytes. The control confirmed equal parsed contents before replacement.
Admission now saves once per batch before syncing jobs. A smaller monitor reads the recent state lines and result rows.
The final pending file lists each current complete-layout specification that never logged a first step.

## Final measurement

Final take: 932. The 932 is a numerical return to an existing side. Fresh follows fed 871 and the 699-to-595 chain held by other lanes.

The submitted base is `gather/round23-2026-11-13b.csv` (`gate/cand-round23-1113b`). The gain against it is 9.56746020853e-07.
The original candidate remains the strict source-group reference under the main session rule.
The revived lane reused completed work and started no searches. The final queued quench timed out and stayed unpublished.
The workers logged 286 steps from 164 walks and 29935 step seconds. 4 steps reached their time limit.
The final take gains 9.56746020853e-07 against the original candidate and 9.56746020853e-07 over eligible live takes.
Its gain against the applicable source-group references is 9.56746020853e-07. The comparator snapshot is 2026-11-13T22:19:46.073533+00:00.

| n | score | reference gain | source group |
|---|---|---|---|
| 932 | 0.01340483896832767 | 9.56746020853e-07 |  seeds n=504 |

The guarded 871 gained 4.04059979275e-6 before other lanes took it lower.
The recorded reader 699 lineage also supplied the family 595 start that invent later lowered by 4.34868615449e-5 against the candidate.

All 6513 copied box files passed SHA-256 checks. Both scratch directories were removed, and no reader worker remains.

## Next runs

1. Walk fresh module and mixed k123 designs, then changed shell descendants. The 812 follow supplied guarded 871, and the reader 699 lineage fed the improved 595.
2. Rerank the 3025 saved specifications and reserve capacity for unseen counts. Fifteen module 871 first cuts had already run when 14 distinct first passes moved forward.
3. Keep both cuts with cut 0 first. The explicit cut 1 walk returned 932 at the existing live side, so unchanged repeats have little measured value.
4. Keep the source-group and large-field controls before queues. Root-only source classification missed seeds 503/504, and the default CSV limit stopped workers before search.
5. Store shared ancestry once by hash and keep references. Even after compaction, queue and admission files used 175 MB and 217 MB.

## Files

- [Measured steps](../results/readers-r24-2026-11-13.tsv).
- [Reader](../family_readers.py) and [coordinator](../family_readers_follow.py).
- [Source adapter](../readers_sources.py) and [source-group collector](../readers_policy_take.py).
- `take-readers-r24/work/` holds immutable donors, source proofs, controls and verified box archives.
