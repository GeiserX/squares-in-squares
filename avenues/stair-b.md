# Avenue: stair-b (2026-11-12, round 17)

**Result: one n certified, 587, 2.220e-04 of score under held. Two 8-arms with a staircase corner replace the held chains of 6 and 11. No pair with a 9-arm has a row within 0.006 of held on the 68 n, so the kill line ends that part. Hops lower half of the corners of two 8-arms by up to 0.30 squares, and no generator row or build moved with them. A scan of every corner of the shared library over m 20 to 27 found no new row, and hops under the caps of the bar closed none.**

The slice is m 24 to 27 with k 4 to 20, 68 n. The held file is behind the board on 60 of them, by 0.0195 of score. The idea is the design of the [twoshort](twoshort.md) avenue, carried to this slice. A pair of arm sizes is chosen from the loss that the side allows. A staircase corner is then built for that pair at the side fraction of the n.

Words used here: "held" is `gather/round16-2026-11-12a.csv` (22.1664224426, gate dir `gate/cand-round16-1112a`). "The board" is the per-puzzle board of 2026-11-09. The side is `L = m + f` and `k = n - m²`. Stacks, arms, zones and the library are those of the [modules](modules.md), [zones](zones.md) and twoshort avenues. The count class of a corner is its count modulo the stack size of arm 1. The tools of this avenue are [`stair-b_plan.py`](../stair-b_plan.py) and [`stair-b_chain.py`](../stair-b_chain.py). They import `twoshort.py`, `twoshort_corner.py`, `zone_corner.py` and `modules.py` and change none of them.

## 1. Kill line (written 2026-11-12 15:16 UTC, before the first run)

The margin of a pair (c1, c2) at an n starts from the loss that the held side allows. From it we take the two cheapest far zones that we hold at that f, and a corner. The corner is the lowest of three numbers: the library's corner for the pair, the staircase corner that the twoshort avenue built, and the lower line `0.55 (c1 + c2) - 6.3`.

- A pair gets a staircase corner only if its margin is above 0.3 squares on at least one n of the slice.
- **The idea is dead in this slice if the generator has no row within 0.003 of side of held on any n of the slice**. The generator is the one of `modules.py`, with the new corners in the library. The twoshort builds ended up to 0.0056 of side below their prediction. That avenue gives 0.003 as the line for a row worth a build.
- If rows exist, the idea is dead if the builds of the 20 best rows certify nothing below held.

Positive control, which can fail: 911 of the twoshort avenue is rebuilt from its recipe with this lane's copy of the pipeline on boxA. The steps are `twoshort_corner.py stair 9 9 0.72`, `zone_corner.py adopt`, `table` and `merge` into the library of round 16, then `modules.py job` with the far zone `z9-36f680` on both arms and 13 stacks on each arm, with the family squeeze. The twoshort build ended at 30.682866595 against a held side of 30.689167173. The control passes if this build ends within 5e-4 of that side. If it fails, no result of this avenue counts until the cause is found.

## 2. Controls

| control | result |
|---|---|
| 1. The pipeline: 911 from its recipe | Pass. The staircase scan gives a corner of 121 squares with a loss of 3.90. The generator predicts 30.683683 with 13 and 13 stacks. The build ends at 30.682866383, which is 2e-7 below the twoshort build and 0.0063 below held. |
| 2. The generator, added after the first rows: this lane's corners on the n that the twoshort avenue won (rows only, no build) | Pass. The corners of two 9-arms at f = 0.72 give rows below held at 852, 911, 973, 974 and 976 (down to -0.0055). The corners of an 8-arm with a 9-arm at f = 0.70 give rows below held at 912 (-0.0067) and 914 (-0.0012). |

One fault showed in control 1 and is fixed in the chain tool. `modules.py queue` takes a corner of a zone search only if the module carries the mark `ours`. `zone_corner.py merge` does not set it, so the first generator run returned no row at all for 911. `stair-b_chain.py lib` now sets the mark on every staircase corner that it merges.

## 3. What the held layouts of the slice are

`twoshort.py held` reads each held layout. Its cut accepts 4 of the 68 layouts as two flush arms. They are 634 (a 7-arm and an 8-arm), 639 and 747 (a 10-arm and a 6-arm) and 740 (two 8-arms).

| band of k | f | what the held layouts are |
|---|---|---|
| 4 and 5 | 0.57 to 0.61 | Short chains at 35° to 42°. 629, 680 and 733 equal the board. |
| 6 to 10 | 0.61 to 0.71 | Chains of 7 and 8 at 24° to 26° (631, 632, 682 to 685, 735, 739, 740), and designs at 45° (583 to 586, 633, 635, 686). |
| 11 to 14 | 0.72 to 0.78 | Chains of 6 and 11 at 18° and 28° (587, 637, 689, 742 to 744), chains of 5 and 6 at 27° (589, 638, 690), and blocks at 45° (636, 688, 741). |
| 15 to 20 | 0.78 to 0.88 | Chains of 5, 6 and 7 at 22° to 28°. 639 and 747 hold a 10-arm with a 6-arm. |

So the slice has no layout with a stack of 9. It has one layout of two 8-arms.

## 4. The loss a side allows, by pair

`twoshort.py table` prints `k_flush(m, f, c1, c2) - k` for each pair. The first number of each cell is at the board's side, the second at the held side.

n = 587 (m 24, k 11, board f 0.7330, held f 0.7492):

| c1 \ c2 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|
| 6 | 3.53 / 4.63 | 4.43 / 5.53 | 5.14 / 6.23 | 5.72 / 6.80 | 6.20 / 7.28 | 6.60 / 7.67 |
| 7 | | 6.04 / 7.13 | 6.72 / 7.80 | 7.26 / 8.34 | 7.71 / 8.79 | 8.10 / 9.16 |
| 8 | | | 8.04 / 9.11 | 8.56 / 9.62 | 8.99 / 10.04 | 9.34 / 10.40 |
| 9 | | | | 9.68 / 10.73 | 10.08 / 11.13 | 10.42 / 11.46 |
| 10 | | | | | 11.04 / 12.08 | 11.36 / 12.39 |
| 11 | | | | | | 12.21 / 13.23 |

The table for all 68 n and pairs of 6 to 15 is in the take dir (`work/table-24-27.txt`).

What one more square in the stacks of one arm allows depends on m. At f = 0.70:

| m | 7 to 8 | 8 to 9 | 9 to 10 |
|---|---|---|---|
| 20 | 0.53 | 0.40 | 0.31 |
| 24 | 0.68 | 0.52 | 0.41 |
| 27 | 0.80 | 0.62 | 0.48 |
| 28 | 0.83 | 0.65 | 0.51 |
| 31 | 0.95 | 0.74 | 0.59 |

A 9-arm in place of an 8-arm earns 0.52 to 0.62 squares in this slice. In the twoshort slice it earns 0.65 to 0.74.

## 5. The margins

`stair-b_plan.py margins` puts the three terms together for every n and every pair of 6 to 15. It differs from `twoshort.py pay` in one point: a corner counts for an n only within 0.06 of the f it was found at, as `modules.py` uses it. Where no corner is in reach, the corner is the line, and the row is marked.

| pair | median margin on held | best (n) | n above 0.3 | best on the board | rows with a corner from the line |
|---|---|---|---|---|---|
| 6 and 7 | -0.35 | +0.79 (596) | 7 | +0.19 | 68 of 68 |
| 6 and 10 | -1.17 | +0.50 (748) | 4 | -0.19 | 33 |
| 7 and 9 | -0.55 | +0.43 (645) | 5 | -0.16 | 38 |
| 8 and 8 | -0.21 | +0.99 (587) | 13 | +0.21 | 11 |
| 8 and 9 | -0.20 | +0.79 (587) | 15 | +0.15 | 33 |
| 9 and 9 | -0.25 | +0.67 (749) | 11 | -0.09 | 18 |
| 8 and 10, 9 and 10, 10 and 10 | -0.6 to -1.3 | +0.20 (587) | 0 | -0.33 | |
| any pair with an arm of 11 to 15 | -1.4 to -8.2 | -0.24 (587) | 0 | -0.80 | |

The first rule of the kill line gives five pairs to build: 8 and 9, 9 and 9, 8 and 8, 6 and 7, and 7 and 9. Arms of 10 and more have no margin above 0.3 and got no corner.

The table of margins is `work/margins-24-27.tsv`, and the cells to build are `work/plan-24-27.tsv`.

## 6. The corners that we built

Each cell is one run of `twoshort_corner.py stair`. The first runs settle the 30 or 40 counts of lowest scan loss. The later runs use the options that the twoshort lane added during the round: `--walls`, `--per 2` and `--top 0`, which settle every count, with a time limit.

| pair | f | corners settled | lowest loss | lowest loss by count class of arm 1 |
|---|---|---|---|---|
| 6 and 7 | 0.86 | 30 | 1.93 | 0: 1.98, 1: 1.98, 2: 2.48, 3: 2.33, 4: 1.93, 5: 2.23 |
| 7 and 6 | 0.86 | 30 | 2.62 | 0: 2.62, 1: 2.92, 2: 2.89, 3: 2.67, 4: 2.95, 5: 3.08, 6: 3.08 |
| 7 and 8 | 0.74 | 65 | 1.93 | 0: 2.85, 1: 1.93, 2: 1.93, 3: 2.33, 4: 2.36, 5: 2.46, 6: 3.16 |
| 7 and 9 | 0.86 | 9 | 2.93 | 0: 3.07, 2: 3.56, 3: 2.99, 4: 3.34, 5: 2.93 |
| 8 and 7 | 0.74 | 76 | 2.61 | 0: 3.32, 1: 3.04, 2: 3.04, 3: 3.15, 4: 3.59, 5: 2.61, 6: 2.62, 7: 2.65 |
| 8 and 8 | 0.66 | 65 | 2.65 | 0: 2.65, 1: 3.34, 2: 2.98, 3: 2.68, 4: 3.02, 5: 3.52, 7: 3.56 |
| 8 and 8 | 0.68 | 43 | 2.58 | 0: 2.58, 1: 3.59, 2: 2.78, 3: 2.81, 4: 3.21, 5: 3.50, 6: 5.18, 7: 3.45 |
| 8 and 8 | 0.70 | 42 | 2.57 | 0: 2.83, 1: 3.44, 2: 2.57, 3: 3.68, 4: 3.58, 5: 3.45, 6: 4.65, 7: 3.96 |
| 8 and 8 | 0.72 | 38 | 2.48 | 0: 2.93, 1: 3.11, 2: 2.48, 3: 4.01, 4: 4.32, 5: 3.41, 6: 4.06, 7: 3.14 |
| 8 and 8 | 0.74 | 40 | 2.53 | 0: 3.18, 1: 3.20, 2: 2.53, 3: 3.62, 4: 3.63, 5: 3.36, 6: 3.91, 7: 3.13 |
| 8 and 8 | 0.75 | 78 | 2.62 | 0: 3.22, 1: 3.41, 2: 2.62, 3: 3.24, 4: 3.52, 5: 3.41, 6: 3.89, 7: 3.00 |
| 8 and 8 | 0.76 | 58 | 2.78 | 0: 3.00, 1: 3.34, 2: 2.78, 3: 3.82, 4: 3.66, 5: 3.49, 6: 3.32, 7: 2.99 |
| 8 and 8 | 0.77 | 59 | 2.89 | 0: 3.02, 1: 3.42, 2: 2.89, 3: 3.51, 4: 3.81, 5: 3.57, 6: 3.34, 7: 3.13 |
| 8 and 8 | 0.78 | 40 | 3.02 | 0: 3.02, 1: 3.64, 2: 3.08, 3: 3.63, 4: 3.96, 5: 3.66, 6: 3.06, 7: 3.14 |
| 8 and 8 | 0.80 | 58 | 2.97 | 0: 2.97, 1: 3.92, 2: 3.28, 3: 3.46, 4: 3.96, 5: 3.82, 6: 3.59, 7: 3.18 |
| 8 and 8 | 0.82 | 39 | 3.01 | 0: 3.01, 1: 3.96, 2: 3.71, 3: 3.49, 4: 4.10, 5: 3.53, 6: 4.45, 7: 3.43 |
| 8 and 8 | 0.84 | 41 | 3.52 | 0: 3.52, 1: 3.93, 2: 4.20, 3: 3.87, 4: 4.26, 5: 3.56, 6: 4.09, 7: 3.88 |
| 8 and 8 | 0.86 | 9 | 3.78 | 0: 4.04, 1: 3.88, 2: 4.40, 3: 4.36, 4: 4.09, 5: 3.78, 6: 3.80, 7: 3.97 |
| 8 and 9 | 0.70 | 193 | 2.76 | 0: 3.75, 1: 3.75, 2: 3.35, 3: 2.89, 4: 2.76, 5: 2.77, 6: 2.77, 7: 3.44 |
| 8 and 9 | 0.78 | 30 | 3.08 | 0: 3.96, 1: 3.39, 2: 3.08, 3: 3.16, 4: 3.14, 5: 3.26, 6: 3.83, 7: 4.34 |
| 8 and 9 | 0.82 | 40 | 3.36 | 0: 3.36, 1: 3.48, 2: 3.60, 3: 3.75, 4: 3.75, 5: 3.76, 6: 4.02, 7: 4.54 |
| 9 and 7 | 0.86 | 30 | 4.09 | 0: 4.24, 1: 4.41, 2: 4.09, 3: 4.53, 4: 4.20, 5: 4.28, 6: 4.81, 7: 4.65, 8: 4.28 |
| 9 and 8 | 0.70 | 29 | 3.41 | 0: 3.44, 1: 3.74, 2: 3.74, 3: 3.41, 4: 3.41, 5: 3.76, 6: 4.65, 7: 4.09, 8: 4.12 |
| 9 and 9 | 0.72 | 40 | 3.83 | 0: 4.54, 1: 3.91, 2: 4.27, 3: 3.83, 4: 3.90, 5: 4.57, 6: 4.21, 7: 6.06, 8: 4.20 |
| 9 and 9 | 0.84 | 30 | 4.18 | 0: 4.25, 1: 5.01, 2: 4.87, 3: 4.48, 4: 5.29, 5: 4.28, 6: 5.18, 7: 5.23, 8: 4.18 |

What the corners say:

- **The line is too low outside the pairs it was drawn through.** It gives 0.85 for a 6-arm with a 7-arm, and the staircase costs 1.93. It gives 3.05 for an 8-arm with a 9-arm, and the staircase costs 2.76 at f = 0.70, 3.08 at 0.78 and 3.36 at 0.82. It gives 3.60 for two 9-arms, and the staircase costs 3.83 at 0.72 and 4.18 at 0.84. So every margin of section 5 that stands on the line is 0.3 to 1.1 squares too high.
- **The staircase is a design for f below 0.75.** For each pair its loss grows with f.
- **Two 8-arms have one cheap class.** Class 2 costs 2.48 to 2.78 from f = 0.68 to 0.76. The library's best corner of two 8-arms loses 2.47. Classes 0 and 7 cost 2.6 to 3.2. Classes 3 to 6 cost 3.2 to 4.6 at most f. So the staircase adds count classes to the library more than it lowers the loss.
- **An 8-arm with a 9-arm is cheap in four classes.** At f = 0.70 it costs 2.76 to 2.89 in classes 3 to 6. It costs 3.35 to 3.75 in classes 0, 1, 2 and 7. The run that settles every count with walls moved class 3 from 3.11 to 2.89 and no other class.

## 7. The generator

`stair-b_chain.py lib` puts the corners of a cell into a copy of the library of round 16 (`lib16b` of the modules lane). `stair-b_chain.py queue` then runs `modules.py queue` over the n, with only the choices that hold a new corner. A run over the 68 n takes under a minute. So each cell was judged by the generator, and a build ran only for a row within 0.003 of the bar. The bar of an n is the smaller of its held side and its side in every live take dir.

The best row of each cell, as predicted side less held side:

| cell | n of the slice with a row within 0.004 | best rows |
|---|---|---|
| 8 and 9 at 0.70 | none | 686 +0.0072, 587 +0.0075, 687 +0.0093, 738 +0.0096, 634 +0.0117 |
| 8 and 9 at 0.78 and 0.82 | none | 639 +0.0060, 691 +0.0093, 587 +0.0095, 745 +0.0113, 747 +0.0127 |
| 9 and 8 at 0.70 | none | |
| 9 and 9 at 0.72 and 0.84 | none | 687 +0.0138, 738 +0.0140, 634 +0.0141, 587 +0.0154 |
| 6 and 7, 7 and 6 at 0.86 (m 20 to 27) | none | |
| 7 and 9, 9 and 7 at 0.86 (m 20 to 27) | none | |
| 8 and 8 at 0.74 and 0.78 (m 20 to 27) | 587, 740 | 587 -0.0028, 740 +0.0002 |
| 8 and 8 at 0.76 and 0.80 | 587, 740 | 587 -0.0010 (from 0.76) and +0.0021 (from 0.80), 740 +0.0002 |
| 8 and 8 at 0.70 and 0.72, every count | 740, 685 | 740 +0.0002, 450 +0.0032 (m 21), 685 +0.0040 |
| 8 and 8 at 0.66 and 0.68, every count | 685, 740 | 685 +0.0036, 740 +0.0035 |
| 8 and 8 at 0.75 and 0.77, every count | 587, 740 | 587 -0.0017, 740 +0.0002, 450 +0.0034 (m 21) |
| 8 and 8 at 0.82, 0.84 and 0.86, every count | none | |
| 7 and 8, 8 and 7 at 0.74, every count (m 20 to 27) | none | 540 +0.0054 (m 23) |

**A 9-arm is dead in this slice by the kill line.** No pair with a 9-arm has a row within 0.003 of held on the 68 n. The nearest row is 0.0060 above held. A second library with all 58 settled corners of the two cells of an 8-arm with a 9-arm, four states of each, gave the same three best rows.

The same corners give rows below held at m 28 to 31 (control 2). The best row of a pair with a 9-arm, by m: +0.0075 at m 24, +0.0060 at m 25, +0.0072 at m 26 and +0.0096 at m 27. It is -0.0067 at m 30 and -0.0055 at m 31. Section 4 gives the cause. In this slice a 9-arm earns 0.52 to 0.62 squares over an 8-arm. Its far zone costs 0.5 to 0.8 squares more in the library, by count class, and its corner costs 0.25 more. The sum turns positive near m 28.

**Two 8-arms give rows on four n.** 587 has rows below held from the cells at 0.74 to 0.78. 740 is two 8-arms in the held file, and every cell gives its held layout again. 685 and 450 have rows 0.003 above held.

After the cells, one library held all 528 staircase corners of this avenue with the library of the modules lane of this round (`stair-b_chain.py union`). One generator run over the 136 n of m 20 to 27 with a slack of 0.009 gives the nearest row of every n. 12 n have a row within 0.009 of held, and the other 124 n have none. Below held: 587 -0.0028. Within 0.004: 740 +0.0002, 450 +0.0032 and 685 +0.0036. Within 0.006: 638 +0.0048, 540 +0.0054 and 634 +0.0056. Within 0.009: 639 +0.0060, 686 +0.0072, 691 +0.0078, 588 +0.0088 and 687 +0.0093.

The library alone, with no new corner, has a row within 0.006 of held on 5 of the 14 n of largest score gap. Four of those rows are the held layout itself. For 686, 687, 741, 748, 694, 585, 738, 742 and 635 no choice of our modules comes within 0.006 of held. So our two-arm zones are the limit there. The row of an 8-arm with a 9-arm at 686 (+0.0072) is the best two-arm layout that we can predict for it.

## 8. The builds

| n | m, k | corner | far zones | stacks | builds | predicted less held | built less held |
|---|---|---|---|---|---|---|---|
| 418 | 20, 18 | 6 and 6, 77 squares, from f = 0.92 (`zc6x6-77f9200acapk`) | `304h.F1`, `703h.F2` | 7, 5 | 2 | +0.0001 | +0.000018 |
| 418 | 20, 18 | 6 and 6, 77 squares, from f = 0.93 (`zc6x6-77f9301dr`) | `304h.F1`, `304h.F1` | 7, 7 | 3 | +0.0010 | +0.000018 |
| 450 | 21, 9 | 8 and 8, 74 squares, from f = 0.70 (`zc8x8-74f7000ar`) | `z8-54f700.F1`, `974h13.F2` | 5, 6 | 7 | +0.0032 | +0.002068 |
| 450 | 21, 9 | 8 and 8, 82 squares, from f = 0.75 (`zc8x8-82f7500av`) | `495h11.F1`, `z8-54f700.F1` | 4, 5 | 2 | +0.0034 | +0.002100 |
| 450 | 21, 9 | 8 and 8, 98 squares, from f = 0.71 (`zc8x8-98f7134ar`) | `z8-54f700.F1`, `495h11.F1` | 3, 4 | 3 | +0.0027 | +0.002100 |
| 540 | 23, 11 | 8 and 7, 71 squares, from f = 0.74 (`zc8x7-71f7400au`) | `z8-37f730.F1`, `921fa17.F2` | 9, 8 | 1 | +0.0054 | +0.004291 |
| 587 | 24, 11 | 8 and 8, 94 squares, from f = 0.78 (`zc8x8-94f7800aq`) | `495h11.F1`, `637h12.F1` | 7, 8 | 7 | -0.0028 | -0.005379 |
| 587 | 24, 11 | 8 and 8, 95 squares, from f = 0.76 (`zc8x8-95f7600ah`) | `z8-61f720.F1`, `495h11.F1` | 5, 7 | 4 | -0.0012 | -0.005008 |
| 587 | 24, 11 | 8 and 8, 95 squares, from f = 0.76 (`zc8x8-95f7600ag`) | `z8-61f720.F1`, `495h11.F1` | 5, 7 | 1 | -0.0010 | -0.005008 |
| 587 | 24, 11 | 8 and 8, 95 squares, from f = 0.75 (`zc8x8-95f7500av`) | `z8-61f720.F1`, `495h11.F1` | 5, 7 | 2 | -0.0017 | -0.004677 |
| 587 | 24, 11 | 8 and 9, 90 squares, from f = 0.70 (`zc8x9-90f7000ae`) | `495h11.F1`, `z9-24f720.F1` | 7, 11 | 1 | +0.0075 | +0.002063 |
| 634 | 25, 9 | 7 and 8, 86 squares, from f = 0.70 (`zc7x8-86f7096ar`) | `z7-16f700.F1`, `912h.F1` | 11, 9 | 6 | +0.0000 | -0.000000 |
| 634 | 25, 9 | 8 and 8, 74 squares, from f = 0.76 (`zc8x8-74f7600ag`) | `z8-42f700.F1`, `z8-26f700.F1` | 10, 11 | 1 | +0.0056 | +0.005516 |
| 638 | 25, 13 | 8 and 8, 94 squares, from f = 0.78 (`zc8x8-94f7800aq`) | `495h11.F1`, `495h11.F1` | 8, 8 | 5 | +0.0048 | +0.003312 |
| 685 | 26, 9 | 8 and 8, 90 squares, from f = 0.68 (`zc8x8-90f6800at`) | `740h.F1`, `740h.F2d` | 10, 8 | 7 | +0.0036 | +0.002838 |
| 685 | 26, 9 | 8 and 8, 90 squares, from f = 0.70 (`zc8x8-90f7000ar`) | `740h.F1`, `912m10.F1d` | 10, 9 | 1 | +0.0040 | +0.002841 |
| 685 | 26, 9 | 8 and 8, 90 squares, from f = 0.68 (`zc8x8-90f6800ax8`) | `740h.F2`, `740h.F2` | 9, 8 | 2 | +0.0041 | +0.002846 |
| 686 | 26, 10 | 8 and 9, 79 squares, from f = 0.70 (`zc8x9-79f7000ae`) | `740h13.F1d`, `z9-27f720.F1` | 10, 13 | 1 | +0.0072 | +0.005093 |
| 740 | 27, 11 | 8 and 8, 74 squares, from f = 0.74 (`zc8x8-74f7400aq`) | `740h.F1`, `740f11.F2d` | 12, 11 | 2 | +0.0002 | -0.000000 |
| 740 | 27, 11 | 8 and 8, 90 squares, from f = 0.68 (`zc8x8-90f6800at`) | `685h09.F1`, `975m10.F2d` | 13, 10 | 2 | +0.0035 | -0.000000 |
| 740 | 27, 11 | 8 and 8, 74 squares, from f = 0.76 (`zc8x8-74f7600ag`) | `740h.F1`, `740f11.F2d` | 12, 11 | 2 | +0.0002 | -0.000000 |
| 740 | 27, 11 | 8 and 8, 90 squares, from f = 0.75 (`zc8x8-90f7500av`) | `740h.F1`, `740f11.F2d` | 11, 10 | 2 | +0.0002 | -0.000000 |
| 740 | 27, 11 | 8 and 8, 74 squares, from f = 0.72 (`zc8x8-74f7200ar`) | `740h.F1`, `740h.F1` | 12, 11 | 2 | +0.0002 | +0.000000 |
| 740 | 27, 11 | 8 and 8, 74 squares, from f = 0.76 (`zc8x8-74f7600bx6`) | `740h.F1`, `740h.F1` | 12, 11 | 2 | +0.0002 | +0.000000 |
| 747 | 27, 18 | 10 and 6, 102 squares, from f = 0.81 (`zc10x6-102f8112ar`) | `746h.F1`, `746h.F2d` | 14, 9 | 3 | +0.0016 | +0.000000 |
| 747 | 27, 18 | 10 and 6, 102 squares, from f = 0.81 (`zc10x6-102f8111ccapk`) | `639h.F1`, `747h11.F2d` | 12, 9 | 1 | +0.0009 | +0.000531 |

The table has one row for each n and corner. It shows the build of smallest side. "Builds" counts the builds of that n with that corner. The builds of 418 and 747, of 634 from the corner of 86 squares and of 450 from the corner of 98 squares belong to section 10.

- **587 is the result of this avenue.** It has two 8-arms and a staircase corner of 94 squares that was built at f = 0.78. The held 587 has chains of 6 and 11. The corner is not cheap (its loss is 3.06, and the library's best corner of two 8-arms loses 2.47). It is in count class 6, and with it the two far zones and the 7 and 6 stacks fill the side with no slack. Corners of 95 squares from the cells at 0.75 and 0.76 give 587 too, 0.0004 to 0.0012 of side above the first build.
- 740 is the held layout again. The held 740 is two 8-arms already. Ten builds from five corners end between 2e-9 below its side and 2e-6 above it. None is far enough below it to certify.
- 450, 685, 638, 540 and 634 are the next rows of two 8-arms. Their builds end 0.0021, 0.0028, 0.0033, 0.0043 and 0.0055 of side above held.
- The squeeze takes 0.0025 to 0.0040 of side off the prediction at 587. At the other n of two 8-arms it takes 0.0001 to 0.0015. 740 is apart, because it falls to its held layout. The two builds of an 8-arm with a 9-arm lose 0.0021 and 0.0054 and stay above held. So a row that is more than 0.003 above the bar has not paid here.

## 9. Hops on the staircase corners

`zone_corner.py sweep` and `search` run hops (shake, flip and relocate moves) on a settled corner. A sweep can delete one square first, which gives the count class below. This section measures what hops do to the corners of two 8-arms. A sweep takes the cheapest corner of each count class of a cell. It gives each count 40 s on boxD and 120 s on boxA, which ran at a fifth of its speed. A search gives one corner 5 to 7 minutes.

| cell | start corner | count, class | loss before the hops | loss after | lowest staircase loss of that class in the cell |
|---|---|---|---|---|---|
| 8 and 8 at 0.68 | `st8x8-112f6800t` | 112, 0 | 2.58 | 2.55 | 2.58 |
| 8 and 8 at 0.68 | `st8x8-112f6800t` | 111, 7 | 3.58 | 3.55 | 3.45 |
| 8 and 8 at 0.68 | `st8x8-90f6800t` | 90, 2 | 2.78 | 2.74 | 2.78 |
| 8 and 8 at 0.68 | `st8x8-90f6800t` | 89, 1 | 3.40 | 3.40 | 3.59 |
| 8 and 8 at 0.68 | `st8x8-99f6800t` | 99, 3 | 2.81 | 2.81 | 2.81 |
| 8 and 8 at 0.68 | `st8x8-99f6800t` | 98, 2 | 2.86 | 2.78 | 2.78 |
| 8 and 8 at 0.70 | `st8x8-104f7000r` | 104, 0 | 2.83 | 2.69 | 2.83 |
| 8 and 8 at 0.70 | `st8x8-104f7000r` | 103, 7 | 3.44 | 3.32 | 3.96 |
| 8 and 8 at 0.70 | `st8x8-74f7000r` | 74, 2 | 2.58 | 2.58 | 2.57 |
| 8 and 8 at 0.70 | `st8x8-90f7000r` | 90, 2 | 2.57 | 2.57 | 2.57 |
| 8 and 8 at 0.70 | `st8x8-90f7000r` | 89, 1 | 3.12 | 2.97 | 3.44 |
| 8 and 8 at 0.72 | `st8x8-90f7200r` | 90, 2 | 2.48 | 2.48 | 2.48 |
| 8 and 8 at 0.72 | `st8x8-90f7200r` | 89, 1 | 3.32 | 3.16 | 3.11 |
| 8 and 8 at 0.72 | `st8x8-95f7200r` | 95, 7 | 3.14 | 3.14 | 3.14 |
| 8 and 8 at 0.72 | `st8x8-95f7200r` | 94, 6 | 3.59 | 3.59 | 4.06 |
| 8 and 8 at 0.72 | `st8x8-96f7200r` | 96, 0 | 2.93 | 2.93 | 2.93 |
| 8 and 8 at 0.72 | `st8x8-96f7200r` | 95, 7 | 3.20 | 3.20 | 3.14 |
| 8 and 8 at 0.72 | `st8x8-97f7200r` | 97, 1 | 3.11 | 3.02 | 3.11 |
| 8 and 8 at 0.72 | `st8x8-97f7200r` | 96, 0 | 3.42 | 3.12 | 2.93 |
| 8 and 8 at 0.75 | `st8x8-112f7500v` | 112, 0 | 3.22 | 3.05 | 3.22 |
| 8 and 8 at 0.75 | `st8x8-112f7500v` | 111, 7 | 3.08 | 2.81 | 3.00 |
| 8 and 8 at 0.75 | `st8x8-69f7500v` | 69, 5 | 3.41 | 3.41 | 3.41 |
| 8 and 8 at 0.75 | `st8x8-69f7500v` | 68, 4 | 3.72 | 3.60 | 3.52 |
| 8 and 8 at 0.75 | `st8x8-82f7500v` | 82, 2 | 2.62 | 2.62 | 2.62 |
| 8 and 8 at 0.75 | `st8x8-82f7500v` | 81, 1 | 3.41 | 3.39 | 3.41 |
| 8 and 8 at 0.75 | `st8x8-87f7500v` | 87, 7 | 3.00 | 2.94 | 3.00 |
| 8 and 8 at 0.75 | `st8x8-87f7500v` | 86, 6 | 3.94 | 3.88 | 3.89 |
| 8 and 8 at 0.75 | `st8x8-89f7500v` | 89, 1 | 3.41 | 3.41 | 3.41 |
| 8 and 8 at 0.75 | `st8x8-89f7500v` | 88, 0 | 3.53 | 3.52 | 3.22 |
| 8 and 8 at 0.75 | `st8x8-99f7500v` | 99, 3 | 3.24 | 3.24 | 3.24 |
| 8 and 8 at 0.75 | `st8x8-99f7500v` | 98, 2 | 3.07 | 3.07 | 2.62 |
| 8 and 8 at 0.76 | `st8x8-112f7600g` | 112, 0 | 3.00 | 3.00 | 3.00 |
| 8 and 8 at 0.76 | `st8x8-112f7600g` | 111, 7 | 3.04 | 2.77 | 2.99 |
| 8 and 8 at 0.76 | `st8x8-118f7600g` | 118, 6 | 3.32 | 3.32 | 3.32 |
| 8 and 8 at 0.76 | `st8x8-118f7600g` | 117, 5 | 3.23 | 3.06 | 3.49 |
| 8 and 8 at 0.76 | `st8x8-74f7600g` | 74, 2 | 2.78 | 2.78 | 2.78 |
| 8 and 8 at 0.76 | `st8x8-74f7600g` | 73, 1 | 3.56 | 3.56 | 3.34 |
| 8 and 8 at 0.76 | `st8x8-87f7600g` | 87, 7 | 2.99 | 2.82 | 2.99 |
| 8 and 8 at 0.76 | `st8x8-87f7600g` | 86, 6 | 3.51 | 3.51 | 3.32 |
| 8 and 8 at 0.76 | `st8x8-95f7600g` | 95, 7 | 2.99 | 2.82 | 2.99 |
| 8 and 8 at 0.76 | `st8x8-97f7600g1` | 97, 1 | 3.34 | 3.31 | 3.34 |
| 8 and 8 at 0.76 | `st8x8-97f7600g1` | 96, 0 | 3.50 | 3.44 | 3.00 |
| 8 and 8 at 0.78 | `st8x8-103f7800q` | 103, 7 | 3.14 | 2.95 | 3.14 |
| 8 and 8 at 0.78 | `st8x8-103f7800q` | 102, 6 | 3.25 | 3.25 | 3.06 |
| 8 and 8 at 0.78 | `st8x8-82f7800q` | 82, 2 | 3.08 | 3.08 | 3.08 |
| 8 and 8 at 0.78 | `st8x8-82f7800q` | 81, 1 | 3.64 | 3.64 | 3.64 |
| 8 and 8 at 0.78 | `st8x8-88f7800q` | 88, 0 | 3.02 | 3.02 | 3.02 |
| 8 and 8 at 0.78 | `st8x8-88f7800q` | 87, 7 | 3.24 | 3.04 | 3.14 |
| 8 and 8 at 0.78 | `st8x8-94f7800q` | 94, 6 | 3.06 | 3.06 | 3.06 |
| 8 and 8 at 0.78 | `st8x8-94f7800q` | 94, 6 | 3.06 | 2.97 | 3.06 |
| 8 and 8 at 0.78 | `st8x8-94f7800q` | 93, 5 | 3.97 | 3.91 | 3.66 |

- **Hops lower the corners.** The sweeps and searches ended on 51 counts. 27 are a corner at its own count, and 11 of them fell by more than 0.005 squares. 24 are a corner with one square deleted, and 15 of them fell after the deletion. The largest fall is 0.30 squares. Class 7 fell from 3.00 to 2.81 at f = 0.75, from 2.99 to 2.77 at 0.76 and from 3.14 to 2.95 at 0.78. Class 0 fell from 2.83 to 2.69 at 0.70. Class 1 fell from 3.44 to 2.97 at 0.70, from a corner with one square deleted.
- **The corners of 587 fell too.** A search of 7 minutes took the corner of 94 squares from 3.06 to 2.97. The corner of 95 squares at 0.76 fell from 2.99 to 2.82.
- **No row moved.** With the hopped corners in the library, the generator gives the same best rows: 587 -0.0028, 740 +0.0002, 685 +0.0039 and 638 +0.0048. The hopped corner of 95 squares lost 0.18 squares, and its row of 587 moved by 0.0003 of side.
- **No build moved.** The builds of 587 from the hopped corner of 95 squares end at 24.744143434, the side of the build before the hops. The hopped corners of 685 give +0.0028 again.
- **A hop shortens one length.** A corner has two lengths, one along each arm. The hops took 0.013 to 0.024 off one length of these corners and less than 0.001 off the other. A row gains only when both arms can use the room.
- **Hops under caps on both lengths found nothing on the corner of 587.** `zone_corner.py search --caps` asks for a state that is shorter in both lengths. Two searches of 6 minutes at f = 0.78 asked for 0.004 and then for 0.0015 off both lengths. They ran 123 and 129 hops and kept no state.

Two more checks ran on the nearest builds, and both are dry.

- **Other far zones and stacks.** The generator listed 54 rows of 587, 450, 685 and 638 with other far zones and stack counts. 18 of them were built. The 5 builds of 587 end between 24.743772038 and 24.743773024, and the take is 24.743771960. The 5 builds of 450 end between 21.735234 and 21.735278. The 4 builds of 638 all end at 25.764848073. The 4 builds of 685 end between 26.686982 and 26.686983. So the far zones and the stack counts do not set the side of a build.
- **The fq quench of the polish lane.** It moved the build of 450 by 1e-8 of side. It found nothing on the builds of 685 and 638 and on the second layout of 587 (24.744143).

## 10. Every corner of the library at the f of the bar

Sections 7 to 9 use only the rows that hold a staircase corner of this avenue. `zone_corner.py needs` runs the generator with every corner of a zone search in the shared library. For each row it gives the two lengths that the bar leaves for the corner at the f of the bar. The excess is how far the corner stands above them. `zone_corner.py capsearch` carries the corner to that f and runs hops under both caps.

The scan took the 24 best rows of each of the 136 n of m 20 to 27, up to 0.004 of side above the bar. Ten n have a row.

| n | row less bar | corner | excess | what the row is |
|---|---|---|---|---|
| 634 | +0.000004 | 7 and 8, 86 squares | 0.0006 | The held layout. Six builds end 2e-9 of side below held. That is 4.9e-11 of score, under the line of 1e-10. |
| 740 | +0.0003 | 8 and 8, 98 squares | 0.0022 | The held layout (section 8). |
| 461 | +0.0003 | 6 and 6, 77 squares | 0.0031 | The held layout. The modules lane built it this round, equal to held. |
| 418 | +0.0010 | 6 and 6, 77 squares | 0.0083 | Three builds end 1.8e-5 of side above the bar. The bar is the take of the harvest lane. |
| 747 | +0.0016 | 10 and 6, 102 squares | 0.0107 | The held layout. Three builds end 8e-8 to 9e-7 of side above held. |
| 587 | +0.0026 | 8 and 8, 94 squares, staircase | 0.0120 | The bar is our take. |
| 450 | +0.0027 | 8 and 8, 98 squares | 0.0116 | Three builds end 0.0021 of side above held, on the side of the builds from the staircase corner of 74 squares (section 8). |
| 419 | +0.0031 | 6 and 7, 71 squares | 0.0244 | Not built. The corners and modules lanes hold 419 this round. |
| 460 | +0.0033 | 8 and 7, 68 squares | 0.0169 | Not built. |
| 685 | +0.0036 | 8 and 8, 90 squares, staircase | 0.0183 | Built in section 8, +0.0028. |

- **The scan found no new row.** In m 24 to 27 five n have a row within 0.004 of the bar. 587 and 685 are rows of this avenue. 634, 740 and 747 are their held layouts. In m 20 to 23 a row is a held layout, or it stands 0.003 above the bar.
- **The excess is four to six times the distance of the row.** The row of 587 is 0.0026 of side above the bar. Its corner is 0.0120 too long in both lengths at the f of the bar. A shorter side gives longer stacks, so the room for the corner falls faster than the side. The hops of section 9 took 0.013 to 0.024 off one length and under 0.001 off the other.
- **Hops under the caps of the bar lowered no excess to zero.** `capsearch` ran on the rows of 634, 740, 450, 587, 685, 638, 540, 418 and 747. Each corner got 3 to 6 minutes, which is 32 to 163 hops, from one or two starts. On 634 the excess stays at 0.0006 after 163 hops. On 587 and 638 it stays at 0.0120 and 0.0216, and the hops that won lowered the sum of the two lengths only. On 540 one hop took it from 0.0386 to 0.0347. On the other five corners the run ends on the excess of its better start, and no hop won.
- **The states that the runs kept move two rows and no build.** With them in the library, the row of 418 moves from +0.0010 to +0.00009. The row of 747 moves from +0.0016 to +0.0009. Two builds of 418 end at 20.920100249, which is 1.8e-5 above the bar again. The build of 747 from its kept state ends at 27.811731607, which is 0.0005 above held. The rows of 740, 450, 685 and 540 stay where they were or move up, so they got no build.
- **Two corners lead to one layout of 450.** From the library's corner of 98 squares the build ends at 21.735266411. From the staircase corner of 74 squares it ends at 21.735266387. The corner of 98 squares is three stacks longer on its arms, and the squeeze takes both to the same place.
- **A longer run on 740 found nothing.** 740 is the held layout of two 8-arms, so a state under its caps would certify. A second run of 199 hops in 569 s ends on the excess of its start, 0.0009.

## 11. What the next round should run

1. **Search far zones of an 8-arm in the dear count classes.** At f = 0.70 the far zones of an 8-arm cost 2.77 to 3.48 squares by class. The classes of a corner and its two far zones must sum to the class of n. So the cheapest modules cost 8.07 to 8.82 squares by class of n. The builds of 450, 685 and 638 end 0.2 to 0.3 squares above held. This is the one lever of two 8-arms that this round did not measure.
2. **Write a corner search that shortens both lengths.** Section 10 gives the target for each row at the f of the bar. It is 0.012 for 587 and 450, and 0.017 to 0.035 for 685, 638 and 540. The hops do not reach it. A staircase scan that takes the two caps of `zone_corner.py needs` as its goal is the tool that is missing.
3. **Do not repeat these.** Section 9: hops at the f of the cell, a second choice of far zones or stacks, and the fq quench. Section 10: the scan of the shared library over m 20 to 27, and hops under the caps of the bar.
4. **Leave these out.** A pair with a 9-arm at m 24 to 27. A 6-arm with a 7-arm, where the staircase costs 1.1 squares more than the line. Arms of 10 and more, which have no margin above 0.3.
5. **686, 687, 741 and 634 need another design.** They hold 0.0031 of the score gap of the slice. No two-arm choice of ours comes within 0.005 of held at 686, 687 and 741. At 634 the best row is the held layout.

## Files

| file | what it is |
|---|---|
| [`stair-b_plan.py`](../stair-b_plan.py) | `margins` (the margin of every pair at every n, and the cells to build), `bar` (the bar over the live take dirs), `rows` (generator rows as a build list, rows below the bar first, largest score gap first) |
| [`stair-b_chain.py`](../stair-b_chain.py) | `pick`, `lib` (adopt, table, merge), `union` (one library with the staircase corners of many), `queue`, `run` (the builds of a list, shared between runners), `quench` |
| [`results/stair-b-r17-2026-11-12.tsv`](../results/stair-b-r17-2026-11-12.tsv) | the control, every settled corner with its loss, the best generator row of every n for every cell, every build, the hops, the scan of section 10 and the runs under caps |
| `<scratch>/bounties-squares/take-stair-b-r17` | the take: one csv for each n and `take.tsv`. `work/` holds the tables of sections 4 and 5, the corners, the libraries, the generator rows and the builds |

## Summary

- The slice is m 24 to 27 with k 4 to 20, 68 n, 0.0195 of score behind the board. The design of the twoshort avenue was carried to it. Arm pairs are chosen from the loss that the side allows, and each pair gets a staircase corner at its f.
- One n certified: 587, 2.220e-04 under held. It has two 8-arms and a staircase corner of 94 squares.
- A 9-arm is dead in this slice by the kill line. The nearest row of a pair with a 9-arm is 0.0060 above held. A 9-arm earns 0.52 to 0.62 squares over an 8-arm here, and its far zone and its corner cost more than that.
- Two 8-arms give rows on four n of m 20 to 27. Twelve n have a row within 0.009 of held. 587 certifies, 740 equals its held layout, and the builds of the next five end 0.0021 to 0.0055 above held.
- Hops lower half of the staircase corners of two 8-arms, by up to 0.30 squares. No row and no build moved, because a hop shortens one of the two lengths of a corner. Other far zones, other stacks and the fq quench moved no build either.
- Every corner of the shared library was tried on the 136 n of m 20 to 27. Ten n have a row within 0.004 of the bar. Five are held layouts, and their builds end on the held side. A row that is 0.003 above the bar needs a corner that is 0.012 to 0.035 shorter in both lengths. Hops under those caps closed none on nine corners.
- Next: far zones of an 8-arm in the dear count classes, and a corner search that takes both caps of the bar as its goal.
