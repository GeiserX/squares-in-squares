# Avenue: twoshort (2026-11-12 and 13, rounds 17, 19, 20, 21 and 22)

**Result: arms of 10 and more are dead by the kill line, and an arm of 9 is alive. A staircase corner that a new tool makes from nothing gives layouts of two 9-arms, or of an 8-arm with a 9-arm, at m 28 to 31. 15 n certify for a gain of 2.197e-03, and 13 of them are in the slice (1.992e-03). No pair of arm sizes reaches the board. At f = 0.63 hops take the corner of two 9-arms from 3.81 to 3.03 squares, but no row is below held with it yet.**

**Round 19 (section 9): 4 more n certify for 5.235e-05 against the round 17 file: 793, 794, 853 and 910. The corner near 3.0 is one state, and it is lowest at f = 0.64. Carried to the side fraction of a row and hopped again, it gave three of the four.**

**Round 20 (section 10): 2 more n certify for 3.980e-05 against the round 18 file: 852 and 794. Seeds 2 and 3 on the deep class-6 state copied to f = 0.69 reached 3.35 and 3.34 squares, and those states gave both.**

**Round 21 (section 11): 793 certifies for 5.287e-07 against the round 19 file. A chain of local kicks without fq on the family build of a near row took it 6.1e-6 of side under the bar. Seeds and copies of the deep class-6 state gave no row.**

The slice is m 28 to 31 and k 5 to 16, 48 n. There the held file is 1.5 to 2 squares short of the board. The idea is wider and unequal arms: a pair of arm sizes (c1, c2) other than two 8-arms.

Words used here: "held" is the round 16 file `gather/round16-2026-11-12a.csv` (22.1664224426, gate dir `gate/cand-round16-1112a`). Every certified gain is measured against it. The margins of sections 4 and 5 were computed on the round 15 file. In the slice the two files differ by more than 1e-6 of side at 789 and 972 only. "The board" is the per-puzzle board of 2026-11-09. The side is `L = m + f` and `k = n - m²`. A stack is a row of `c` tilted squares set face to face, flush in a strip of width `c - 1 + f`. An arm is a row of stacks along a wall. The model, the zones and the library are those of the [modules](modules.md) and [zones](zones.md) avenues. The tools are [`twoshort.py`](../twoshort.py) and [`twoshort_corner.py`](../twoshort_corner.py).

## 1. Kill line (written 2026-11-12 13:35 UTC, before the first run)

The margin of a pair (c1, c2) at an n is the loss that the held side allows, less the loss of the cheapest zones we can show.

- The loss the held side allows is `k_flush(m, f, c1, c2) - k` at the held f.
- The zones are the best lattice far zone of each arm at that f, of any count class and with no slack, plus a corner.
- For a pair that the library holds below f = 0.82, the corner is the library's lowest loss. For every other pair it is the lower line through the library's corners, `0.55 (c1 + c2) - 6.3`.

**The idea is dead if no pair with an arm of 10 or more has a margin above 0.3 squares on any n of the slice.**

A build ends within 0.25 squares of the model, so 0.3 is the least that can show.

Positive controls, each of which can fail:

1. The far zones. The enumeration of this tool must return the zone table's best zones. For an arm of 8 at f = 0.65 that is 17 squares with a loss of 2.59. For an arm of 10 at f = 0.68 it is 50 squares with a loss of 3.83.
2. The margin. The slice holds four layouts of two 8-arms (911, 912, 974 and 975). The margin of two 8-arms at these n must be zero or above. A negative margin there would say that a layout we hold cannot exist.
3. The pipeline. 911 and 974 are put together from their own modules and squeezed. Each must end at its held count and within 1e-6 of its held side.

Two notes that we added after the first runs, before any margin was computed:

- The model gives a different number to a pair when the two arms change places: `k_flush(c2, c1) - k_flush(c1, c2) = g2 W1 - g1 W2 + (c2 - c1) f`, with `W = c - 1 + f`. This is 0.66 squares for arms of 8 and 9 at f = 0.68. The table puts the narrower arm first. A library corner with the wider arm first is moved to that labelling with this formula.
- The zone table's 3.83 in control 1 is the loss of the zone after the squeeze. The same zone on the lattice loses 4.21.

## 2. Controls

| control | result |
|---|---|
| 1. Far zones | Pass. Arm of 8 at f = 0.65: 17 squares, loss 2.594. Arm of 10 at f = 0.68: 50 squares, lattice length 5.8191 (loss 4.214), built length 5.7781 (loss 3.833). |
| 2. Margin of two 8-arms at 911, 912, 974 and 975 | Pass. +0.53, +0.56, +0.17 and +0.52 squares. |
| 3. Pipeline | Pass at 911, miss at 974. 911 from its own modules ends at 30.689167170, 3e-9 below its held side. 974 from its own modules ends at 31.703438100, 7.4e-6 above its held side. The line was 1e-6. |

Control 3 says that the pipeline gives back a held side to within 1e-5, not 1e-6. Every result of section 7 is more than 1.3e-3 of side below held, and each one has its own certificate.

Two more checks of the pipeline came from the corner tool of section 6. They start from a corner that the tool made from nothing, not from a held layout. 740 ends at 27.706453157 against a held side of 27.706453158. 974 ends at 31.703432933, 2.3e-6 above held.

## 3. What the held layouts of the slice are

`twoshort.py held` reads each held layout and counts the chains of tilted squares.

| group | n | what the layout is |
|---|---|---|
| Two 8-arms that the cut accepts | 911, 912, 974, 975 | Stacks of 8 at 24° or 25° along two walls. |
| 8-arms that the cut refuses | 793 to 795, 797, 851, 852, 854, 908 to 910, 913, 968 to 973 and others | Chains of 8 at 23° to 26°, with one zone that the cut cannot read. |
| An 8-arm and chains of 10 and 11 | 796, 798 to 800, 855 to 857, 914 to 916, 976, 977 | Chains of 8 at 23° and chains of 10 and 11 at 18° or 19°. The side fraction is 0.72 or more. |
| Other designs | 789, 846, 847, 850, 853, 905 to 907, 966, 967 | Tilts of 35°, 41° or 45° in short chains. 905 and 906 equal the board. |

So the held file already holds wide chains at k of 14 to 16. It holds no stack of 9 anywhere in the slice.

## 4. The loss a side allows, by pair

`twoshort.py table` prints `k_flush(m, f, c1, c2) - k` for each pair, at the board's f and at the held f. This is the number of squares that the three end zones of a two-arm layout may cost at that side. The first number of each cell is at the board's side, the second at the held side.

n = 910 (m 30, k 10, board f 0.6465, held f 0.6791):

| c1 \ c2 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|
| 8 | 6.02 / 8.64 | 6.74 / 9.36 | 7.34 / 9.95 | 7.85 / 10.45 | 8.29 / 10.88 | 8.67 / 11.25 |
| 9 | | 8.11 / 10.70 | 8.68 / 11.27 | 9.17 / 11.74 | 9.59 / 12.15 | 9.95 / 12.51 |
| 10 | | | 9.86 / 12.42 | 10.32 / 12.88 | 10.72 / 13.27 | 11.07 / 13.61 |
| 11 | | | | 11.35 / 13.89 | 11.73 / 14.26 | 12.06 / 14.58 |
| 12 | | | | | 12.65 / 15.15 | 12.96 / 15.46 |
| 13 | | | | | | 13.78 / 16.26 |

One more square in the stacks of one arm allows 0.72 more loss from 8 to 9 and 0.60 from 9 to 10. It allows 0.51 from 10 to 11 and 0.44 from 11 to 12. The gain of a flush stack, `g = f - sin t`, is 0.179, 0.210, 0.237, 0.259, 0.278 and 0.295 for c of 8 to 13 at f = 0.62. A wider arm pays only if its far zone and its share of the corner cost less than that.

## 5. Far zones by arm size, and the margins

`twoshort.py far` lists the lattice far zones of an arm of c at a side fraction, for each count class. It runs the taper enumeration of the zones avenue with one change. For each split of the `c - 1` upright columns between the two sides it runs the count once, and the state is the heights of the columns. The enumeration of `zone_search.py` packs its state in 64 bits, which is too few for an arm of 11 or more. `--build` then squeezes the best zone of each class with `zone_search.settle_zone`.

Lowest loss of a far zone over the count classes (squares):

| c | f = 0.62 | f = 0.66 | f = 0.70 | f = 0.74 |
|---|---|---|---|---|
| 8 | 2.50 | 2.63 | 2.77 | 2.85 |
| 9 | 2.91 | 3.08 | 3.08 | 3.26 |
| 10 | 3.94 | 4.12 | 3.92 | 3.85 |
| 11 | 4.47 | 4.47 | 4.39 | 4.23 |
| 12 | | 4.9 | 4.6 (0.72) | |
| 13 | | 5.4 | 5.6 (0.72) | |
| 14 | | 6.2 | 6.2 (0.72) | |
| 15 | | 6.5 | 7.0 (0.72) | |

The rows of 8 to 11 are built zones, the lower of this tool and the zone table. The rows of 12 to 15 are lattice zones from a count with a cap on the states, so they can be a little high.

The far zone of an arm of 9 costs 0.3 to 0.45 squares more than that of an arm of 8. The side allows 0.72 more. The far zone of an arm of 10 costs 0.6 to 1.0 more than that of an arm of 9. The side allows 0.60 more. From 10 up, each step costs as much as it allows or more, before the corner.

`twoshort.py pay` puts the three terms together for every n of the slice and every pair. Margin in squares at the held side, 48 n each:

| pair | corner used | median | best (n) | n above 0.3 | median at the board's side | best at the board's side |
|---|---|---|---|---|---|---|
| 8 and 8 | library | +0.16 | +0.79 (910) | 19 | -1.30 | +0.11 |
| 8 and 9 | line | -0.10 | +0.52 (914) | 12 | -1.60 | -0.18 |
| 9 and 9 | library | -0.04 | +0.66 (973) | 16 | -1.50 | -0.09 |
| 8 and 10 | line | -0.79 | -0.10 (915) | 0 | -2.68 | -0.87 |
| 9 and 10 | line | -0.42 | +0.26 (914) | 0 | -2.29 | -0.54 |
| 10 and 10 | library | -0.71 | +0.10 (914) | 0 | -2.76 | -0.70 |
| 8 and 11 | line | -1.33 | -0.53 (915) | 0 | -3.14 | -1.30 |
| 9 and 11 | line | -1.00 | -0.20 (914) | 0 | -2.78 | -0.96 |
| 10 and 11 | line | -1.21 | -0.30 (977) | 0 | -3.22 | -1.09 |
| 11 and 11 | line | -1.29 | -0.23 (977) | 0 | -3.17 | -1.03 |

**By the kill line, arms of 10 and more are dead: 336 rows have an arm of 10 or 11, and none has a margin above 0.3. The best is +0.26 (9 and 10 at 914).** Arms of 12 to 15 are lower still, because their far zones cost 4.6 to 7.0 squares each.

The same table says two more things.

- A 9-arm is alive. The pairs 8 and 9, and 9 and 9, have 12 and 16 n above 0.3. The held file has no stack of 9 in the slice.
- No pair reaches the board. At the board's side the best margin of any pair is +0.11. The zones we can show are 1.3 to 1.6 squares too dear for the board in the median, for every pair. A change of arm sizes does not close that gap.

### The same table with corners that we built

The kill table takes the corner of most pairs from a line. Section 6 gives a tool that builds a corner for any pair, so we measured the line. The held layouts of k 14 to 16 hold an 8-arm and chains of 11, and the kill table gives that pair -0.53 at 915. So the line was too dear for a layout that exists.

| pair | corner by the line | corner that we built | best margin with the line | best margin with the built corner | n above 0.3 with the built corner |
|---|---|---|---|---|---|
| 8 and 9 | 3.05 | 2.72 (f 0.68) | +0.52 | +0.85 (914) | 22 |
| 9 and 9 | library 3.89 | 3.78 (f 0.68) | +0.66 | +0.77 (973) | 19 |
| 8 and 10 | 3.60 | 3.28 (f 0.74) | -0.10 | +0.22 (915) | 0 |
| 9 and 10 | 4.15 | 3.87 (f 0.72) | +0.26 | +0.54 (914) | 8 |
| 8 and 11 | 4.15 | 3.62 (f 0.74) | -0.53 | 0.00 (915) | 0 |
| 11 and 11 | 5.80 | 5.37 (f 0.68) | -0.23 | +0.20 (977) | 0 |

- 8 and 11: with the built corner the margin at 915 is 0.00. The model with our best zones gives back the held side there, and no more.
- 9 and 10 is the one wide pair that passes the line with a built corner: +0.54 at 914, and 8 n above 0.3.

The margin takes the best far zone of any count class. A layout must also match the classes: the counts of the corner and of the two far zones must add up to n. The generator of `modules.py` checks that. We put the built corners in the library and ran it over all 414 n. Its best row with arms of 9 and 10 is 0.0050 of side above held (973). Its best row with arms of 8 and 10 is 0.0052 above held (976). It finds no row within 0.006 for 8 and 11. That is about 0.4 squares short.

A prediction is not a build, and section 7 shows that a build can end 0.007 below its prediction. So we built the best rows of the two wide pairs.

| pair | n | predicted less held | built less held | the same n with two 9-arms, built less held |
|---|---|---|---|---|
| 9 and 10 | 973 | +0.0050 | +0.0019 | -0.0069 |
| 9 and 10 | 973 (two more corners) | +0.0065, +0.0068 | +0.0036, +0.0067 | |
| 8 and 10 | 976 | +0.0052 | +0.0035 | -0.0069 |
| 8 and 10 | 587 | +0.0058 | +0.0039 | no row |

**So no pair with an arm of 10 or 11 gives a layout below held, with the line or with built corners. The best build ends 0.0019 of side above held, and 0.0088 above the build of two 9-arms at the same n.**

## 6. A corner from nothing: the staircase

The library held no corner for an 8-arm with a 9-arm, and no 9-and-9 corner that the generator could use at these sides. A corner zone could only come from a held layout, so a new pair had no start.

The library's best corner of two 8-arms below f = 0.8 (`zc8x8-98f7134`, loss 2.47) has a plain design. A staircase of upright squares fills the corner, with columns of 7, 6, down to 1. The rows of arm 1 lie on the lattice of its flush stacks, and each row is one square shorter than the row above it. The columns of arm 2 are cut the same way, and the two arms meet on the diagonal.

`twoshort_corner.py stair C1 C2 F` builds that design for any pair. For a staircase of H columns and the two stack positions (y0, x0), it places the staircase. It then places a row of arm 1 and a column of arm 2 in turn. Each one is the longest run of its lattice row that is clear, over nine shifts along the row. The tool scans H, y0 and x0 and keeps the layout with the lowest loss for each count. It then settles the best counts with `zone_corner.settle_zone`. The output is a base file for `zone_corner.py adopt` and `search`.

Control: for two 8-arms at f = 0.713437 the tool returns a corner of 82 squares with a loss of 2.4675. The library's best there is 2.4675 (the same design with two more stacks).

Lowest loss of a staircase corner (squares):

| pair (arm 1, arm 2) | f | lowest loss | next classes | corner of the kill table |
|---|---|---|---|---|
| 8 and 8 | 0.7134 | 2.47 | 3.11, 3.29, 3.30, 3.42 | library 2.47 |
| 8 and 9 | 0.68 | 2.72 | 2.72, 2.78, 2.82, 3.21 | 3.05 |
| 9 and 8 | 0.68 | 3.44 (2.78 with the 8-arm first) | 3.44, 3.66, 3.99 | 3.05 |
| 9 and 9 | 0.68 | 3.78 | 3.83, 3.87, 3.92, 4.04, 4.07 | library 3.89 |
| 10 and 10 | 0.68 | 4.94 | | library 4.77 |
| 11 and 11 | 0.68 | 5.37 | | 5.80 |
| 8 and 9 | 0.72 | 2.79 | 3.06, 3.06, 3.25 | 3.05 |
| 8 and 10 | 0.74 | 3.28 | 3.30, 3.30, 3.39, 3.48 | 3.60 |
| 9 and 10 | 0.72 | 3.87 | 3.90, 3.91, 4.02, 4.26 | 4.15 |
| 8 and 11 | 0.74 | 3.62 | 3.87, 4.49, 4.64 | 4.15 |

The settle changes the order of the counts by up to 1.2 squares, so the scan loss is a poor guide. A run that settles 40 counts in place of 8 found a lower corner in every class of 9 and 9. Class 1 went from 5.03 to 3.78, class 3 from 4.17 to 3.83 and class 0 from 4.47 to 4.04.

### The second pass

The second pass changes three things. `--walls` puts the first flush stack of each arm into the scan, so no scan layout crosses it. `--per 4` keeps four layouts for each count. `--keep 40` writes the 40 settled corners with the lowest loss to the base file. Each run has 10 to 16 minutes on one core.

Lowest loss of a staircase corner in the second pass (squares). The class is the count of the corner modulo the size of arm 1.

| pair (arm 1, arm 2) | f | layouts settled | lowest loss | its class and count | lowest loss of the other classes |
|---|---|---|---|---|---|
| 7 and 7 | 0.72 | 196 | 2.10 | class 6, 76 squares | 2.30, 2.44, 2.61, 2.63, 2.90, 2.98 |
| 7 and 8 | 0.72 | 240 | 2.09 | class 2, 93 squares | 2.13, 2.39, 2.39, 2.45, 2.89, 2.99 |
| 8 and 7 | 0.72 | 214 | 2.79 | class 5, 101 squares | 2.81, 2.87, 2.87, 2.90, 3.13, 3.14, 3.36 |
| 8 and 8 | 0.64 | 193 | 2.80 | class 0, 112 squares | 3.15, 3.24, 3.38, 3.54, 3.60, 3.71, 3.71 |
| 8 and 8 | 0.68 | 212 | 2.68 | class 0, 88 squares | 2.74, 3.21, 3.40, 3.48, 3.50, 3.52, 3.55 |
| 8 and 8 | 0.76 | 205 | 2.78 | class 2, 90 squares | 2.99, 3.00, 3.32, 3.34, 3.34, 3.49, 3.66 |
| 8 and 9 | 0.74 | 266 | 2.98 | class 4, 84 squares | 3.08, 3.13, 3.35, 3.35, 3.64, 3.90, 4.04 |
| 9 and 9 | 0.63 | 150 | 3.81 | class 6, 96 squares | 3.86, 3.86, 3.92, 3.97, 4.02, 4.03, 4.13, 4.48 |
| 9 and 9 | 0.64 | 232 | 3.71 | class 6, 78 squares | 3.91, 3.94, 3.95, 4.07, 4.07, 4.15, 4.19, 4.24 |
| 9 and 9 | 0.68 | 279 | 3.49 | class 4, 85 squares | 3.66, 3.83, 3.92, 3.97, 4.04, 4.34, 4.52, 4.70 |
| 9 and 9 | 0.72 | 283 | 3.65 | class 1, 118 squares | 3.77, 3.80, 3.86, 3.93, 4.13, 4.20, 4.35, 4.71 |
| 9 and 9 | 0.76 | 257 | 3.59 | class 0, 117 squares | 3.78, 3.92, 4.07, 4.08, 4.17, 4.41, 4.69, 4.71 |

What the second pass says:

- Two 9-arms lose 3.49 to 3.81 squares at every side fraction from 0.63 to 0.76. At f = 0.68 the first pass had 3.78. The corners of this pass carry eight of the certified rows of section 7 (587, 793, 796, 851, 910, 911, 913 and 978).
- Two 8-arms lose 2.68 to 2.80 at f = 0.64, 0.68 and 0.76. The library's 2.47 at f = 0.7134 stays the lowest.
- The best corner of two 8-arms has its stacks at 24.04°, and two 9-arms have that tilt at f = 0.627. The run at f = 0.63 settled 150 layouts, and its lowest loss is 3.81. That is no lower than at the other side fractions. Its two builds of 910 end 0.0020 of side above the lowest row, and its build of 793 ends 0.0028 above. The hops below change this corner a lot.
- An arm of 7 does not pay. Its corner with an 8-arm is the cheapest of all, 2.09 squares, and two 7-arms lose 2.10. But at 796 the side allows 7.34 squares for 7 and 8, against 8.83 for two 8-arms. The generator gives this pair one row. Its build ends at 28.720328, 2e-5 above the build of two 8-arms.
- The order of the arms changes only the labels. 8 and 7 loses 2.79, and 7 and 8 loses 2.09. The side allows 8.04 and 7.34. Both differences are 0.70, as the first note of section 1 says.

### Hops on a settled corner

`zone_corner.py search --moves self,hop` takes one settled corner and moves single squares for 4 to 11 minutes. A hop keeps the count of the corner, so it keeps its class.

| pair | f | corner squares | class | loss before | loss after | change | hops |
|---|---|---|---|---|---|---|---|
| 7 and 8 | 0.72 | 93 | 2 | 2.09 | 2.09 | +0.00 | 72 |
| 8 and 8 | 0.76 | 74 | 2 | 2.78 | 2.78 | +0.00 | 81 |
| 8 and 8 | 0.76 | 82 | 2 | 2.78 | 2.78 | +0.00 | 74 |
| 8 and 9 | 0.68 | 94 | 6 | 2.72 | 2.72 | +0.00 | 54 |
| 8 and 9 | 0.72 | 84 | 4 | 2.79 | 2.79 | +0.00 | 57 |
| 9 and 9 | 0.63 | 77 | 5 | 3.97 | 3.87 | -0.10 | 128 |
| 9 and 9 | 0.63 | 78 | 6 | 3.81 | 3.70 | -0.11 | 64 |
| 9 and 9 | 0.63 | 96 | 6 | 3.81 | 3.03 (cut) | -0.78 |  |
| 9 and 9 | 0.63 | 96 | 6 | 3.81 | 3.03 | -0.78 | 55 |
| 9 and 9 | 0.63 | 98 | 8 | 3.96 | 3.52 | -0.45 | 112 |
| 9 and 9 | 0.63 | 111 | 3 | 3.86 | 3.60 | -0.27 | 82 |
| 9 and 9 | 0.63 | 121 | 4 | 3.86 | 3.26 | -0.60 | 83 |
| 9 and 9 | 0.64 | 78 | 6 | 3.71 | 3.48 | -0.23 | 43 |
| 9 and 9 | 0.64 | 87 | 6 | 3.84 | 3.46 | -0.38 | 63 |
| 9 and 9 | 0.64 | 87 | 6 | 3.84 | 3.50 | -0.33 | 77 |
| 9 and 9 | 0.64 | 93 | 3 | 4.27 | 4.24 | -0.03 | 36 |
| 9 and 9 | 0.68 | 77 | 5 | 3.97 | 3.52 | -0.45 | 71 |
| 9 and 9 | 0.68 | 78 | 6 | 3.92 | 3.40 | -0.52 | 99 |
| 9 and 9 | 0.68 | 78 | 6 | 3.92 | 3.40 | -0.52 | 52 |
| 9 and 9 | 0.68 | 78 | 6 | 3.92 | 3.44 (cut) | -0.48 |  |
| 9 and 9 | 0.68 | 78 | 6 | 3.92 | 3.44 | -0.48 | 61 |
| 9 and 9 | 0.68 | 78 | 6 | 3.92 | 3.89 | -0.03 | 35 |
| 9 and 9 | 0.68 | 84 | 3 | 4.36 | 4.27 (cut) | -0.09 | 105 |
| 9 and 9 | 0.68 | 84 | 3 | 4.36 | 4.29 | -0.06 | 31 |
| 9 and 9 | 0.68 | 85 | 4 | 3.49 | 3.49 | +0.00 | 36 |
| 9 and 9 | 0.68 | 85 | 4 | 3.87 | 3.59 | -0.27 | 107 |
| 9 and 9 | 0.68 | 96 | 6 | 3.92 | 3.89 | -0.03 | 95 |
| 9 and 9 | 0.68 | 102 | 3 | 4.17 | 4.12 | -0.05 | 44 |
| 9 and 9 | 0.68 | 102 | 3 | 4.17 | 4.12 | -0.05 | 46 |
| 9 and 9 | 0.68 | 118 | 1 | 3.66 | 3.63 | -0.03 | 25 |
| 9 and 9 | 0.72 | 77 | 5 | 4.57 | 4.06 | -0.51 | 95 |
| 9 and 9 | 0.72 | 78 | 6 | 4.21 | 3.78 | -0.43 | 33 |
| 9 and 9 | 0.72 | 78 | 6 | 4.21 | 3.78 | -0.43 | 36 |
| 9 and 9 | 0.72 | 85 | 4 | 3.80 | 3.76 | -0.03 | 34 |
| 9 and 9 | 0.72 | 87 | 6 | 4.21 | 3.90 | -0.32 | 33 |
| 9 and 9 | 0.72 | 87 | 6 | 4.21 | 3.90 | -0.32 | 35 |
| 9 and 9 | 0.72 | 94 | 4 | 3.84 | 3.64 | -0.20 | 35 |
| 9 and 9 | 0.72 | 96 | 6 | 4.21 | 3.78 | -0.43 | 38 |
| 9 and 9 | 0.72 | 102 | 3 | 3.95 | 3.56 | -0.39 | 40 |
| 9 and 9 | 0.72 | 105 | 6 | 4.13 | 4.13 | -0.00 | 31 |
| 9 and 9 | 0.72 | 112 | 4 | 3.90 | 3.80 | -0.10 | 63 |
| 9 and 9 | 0.72 | 121 | 4 | 3.80 | 3.77 | -0.02 | 29 |
| 9 and 9 | 0.72 | 121 | 4 | 3.80 | 3.80 | +0.00 | 67 |
| 9 and 9 | 0.76 | 68 | 5 | 4.17 | 4.17 | +0.00 | 40 |
| 9 and 9 | 0.76 | 78 | 6 | 4.70 | 4.36 | -0.34 | 38 |
| 9 and 9 | 0.76 | 96 | 6 | 4.69 | 4.36 | -0.33 | 37 |
| 9 and 9 | 0.76 | 103 | 4 | 3.78 | 3.59 | -0.19 | 78 |
| 9 and 9 | 0.76 | 112 | 4 | 4.07 | 4.07 | +0.00 | 69 |
| 9 and 9 | 0.76 | 116 | 8 | 4.50 | 4.33 | -0.17 | 28 |

What the hops say:

- At f = 0.64 to 0.76, two 9-arms have a floor of 3.4 to 3.5 squares with this design. A corner that the settle left at 3.8 to 4.2 drops by 0.2 to 0.5 squares. The lowest is the corner of 78 squares at f = 0.68, which went from 3.92 to 3.40. The corner of 85 squares at 3.49 does not move.
- At f = 0.63 the hops go further. The corner of 96 squares (class 6) went from 3.81 to 3.03, and the corner of 121 squares (class 4) went from 3.86 to 3.26. The corner of 111 squares (class 3) went from 3.86 to 3.60, and the corner of 77 squares (class 5) from 3.97 to 3.87. A loss of 3.03 is on the trend of the other pairs (2.47 for two 8-arms, 2.72 for an 8-arm with a 9-arm). At f = 0.63 two 9-arms have the tilt of the best corner of two 8-arms.
- The corners of f = 0.63 give no row yet. The generator carries a corner to the side fraction of the row, 0.64 to 0.69 here, and the corner loses most of its gain on the way. The row of 851 with the 3.03 corner is 0.0040 of side above our row, where 0.78 squares at the same f would be 0.009 of side. The builds say the same. 851 with the 3.03 corner ends 0.0010 of side above our row. 910 with the 3.26 corner ends 0.0011 above the lowest row, 791 ends 0.0020 above, 794 ends 0.0032 above and 736 ends 0.0041 above.
- The 3.03 comes back, and it belongs to one corner. A second hop run on the corner of 96 squares with another seed reaches 3.03 again, after 22 s. The corner of 78 squares of the same class, with two stacks fewer, goes from 3.81 to 3.70 only. The corner of 98 squares (class 8) goes from 3.96 to 3.52. At f = 0.64 a second run with another seed on the corner of 87 squares ends at 3.46, and the first run had 3.50.
- An 8-arm with a 9-arm does not move.
- A hop finds what the squeeze of a build cannot find: a square that changes its place. A hop run that takes less than 0.05 squares off a corner gives no new side. The builds of 910 and 974 with such corners end at the side of the old build to 1e-9.
- A run of 5 minutes is short on a loaded box. The corner of 87 squares at f = 0.72 still fell in its last minute.
- The end of a run changes from run to run. The corner of 78 squares at f = 0.68 ran three times from the same start with the same seed. With the box at a load of 85, the run of 5 minutes ended at 3.89. With the box at a load of 60, the run of 5 minutes reached 3.40 after 217 s. A run of 11 minutes ended at 3.44, in another state. A second run from the kept states of the 3.40 run gave 3.3957.
- More time does not move every corner. The corner of 102 squares at f = 0.68 ended at 4.1174 after 5 minutes and again after 11 minutes.
- A second run from the kept states (`--moves resume,hop`, another seed) gave nothing more on the corners of 78 and 87 squares at f = 0.72.
- The other pairs do not move. Two 8-arms at f = 0.76 end where they start (the corners of 74 and 82 squares, 2.78). So does a 7-arm with an 8-arm (93 squares, 2.09), as the 8-arm with a 9-arm did.
- 854 is the nearest n that we do not hold. Its builds with the hopped corners of 78 and of 96 squares at f = 0.72 both end at 29.721977, 0.0013 of side above held.
- The corner at 3.40 gives no new row. Its build of 852 ends at 29.690656, and the build with the 3.44 corner of the long run ends at 29.690337. That is 0.0039 of side below our own row of 852, and 0.0002 above the lowest live row, which another lane walked from our 793. Its builds of 851 end 0.0010 and 0.0014 above our row. Its build of 793 ends at the side of our row to 2e-9.
- The corner of 102 squares at f = 0.72 went from 3.95 to 3.56, and its build of 975 ends 0.0011 above the lowest row. The corner of 77 squares at f = 0.72 went from 4.57 to 4.06, and its best row is 0.0064 above (851).

## 7. Builds

The chain for a new corner is `twoshort_corner.py stair`, `zone_corner.py adopt`, `table` and `merge`, then `modules.py queue` over all 414 n, `modules.py job` with the family squeeze, and `modules.py take`. Each build ran once, on boxE. The take certifies each layout on boxA with floatsafe at 2.2e-11.

The table gives the build with the smallest side for each n. "Builds" is the number of layouts built for that n.

| n | m, k | arms | corner squares | far zones | stacks | predicted | built | held | built less held | builds | certified gain |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 450 | 21, 9 | 8 and 8 | 90 | z8-54f700, 495h11 | 4, 4 | 21.736569 | 21.735266399 | 21.733166009 | +0.002100 | 1 | none |
| 587 | 24, 11 | 8 and 8 | 95 | 495h11, z8-61f720 | 6, 6 | 24.751375 | 24.744919886 | 24.749151179 | -0.004231 | 2 | 1.930e-04 |
| 634 | 25, 9 | 8 and 8 | 74 | z8-26f700, z8-42f700 | 12, 9 | 25.709169 | 25.709097000 | 25.703583890 | +0.005513 | 1 | none |
| 685 | 26, 9 | 8 and 8 | 74 | 740h, 740h | 10, 10 | 26.688281 | 26.686983076 | 26.684143608 | +0.002839 | 2 | none |
| 687 | 26, 11 | 9 and 9 | 103 | z9-22f760, z9-22f760 | 12, 12 | 26.729746 | 26.729541999 | 26.724034085 | +0.005508 | 1 | none |
| 736 | 27, 7 | 9 and 9 | 96 | z9-54f640, z9-54f640 | 10, 9 | 27.643276 | 27.641130604 | 27.637029403 | +0.004101 | 1 | none |
| 740 | 27, 11 | 8 and 8 | 90 | 740h, 912m10d | 11, 10 | 27.710318 | 27.706453157 | 27.706453158 | -0.000000 | 6 | none |
| 791 | 28, 7 | 9 and 9 | 121 | z9-54f640, z9-54f640 | 9, 9 | 28.639870 | 28.636074069 | 28.634070754 | +0.002003 | 1 | none |
| 793 | 28, 9 | 9 and 9 | 87 | z9-36f680, z9-36f680 | 12, 14 | 28.679179 | 28.673443925 | 28.677242857 | -0.003799 | 19 | 1.349e-04 |
| 794 | 28, 10 | 9 and 9 | 96 | z9-19f680, z9-27f720 | 15, 13 | 28.689276 | 28.687335732 | 28.684143608 | +0.003192 | 1 | none |
| 796 | 28, 12 | 8 and 8 | 73 | 740h, 911hd | 12, 13 | 28.723573 | 28.720309002 | 28.721540004 | -0.001231 | 7 | 4.363e-05 |
| 797 | 28, 13 | 8 and 8 | 82 | 911h, 912m10d | 11, 13 | 28.730147 | 28.728120903 | 28.728120904 | -0.000000 | 4 | none |
| 851 | 29, 10 | 9 and 9 | 77 | z9-27f720, z9-36f680 | 15, 15 | 29.680665 | 29.679002510 | 29.684143608 | -0.005141 | 16 | 1.762e-04 |
| 852 | 29, 11 | 9 and 9 | 78 | z9-36f680, z9-36f680 | 15, 14 | 29.690724 | 29.690337223 | 29.696962920 | -0.006626 | 13 | 9.179e-05 |
| 854 | 29, 13 | 9 and 9 | 78 | z9-46f740, z9-19f720 | 14, 16 | 29.722110 | 29.721976715 | 29.720685750 | +0.001291 | 2 | none |
| 855 | 29, 14 | 8 and 8 | 82 | z8-33f750, z8-32f730 | 13, 15 | 29.739227 | 29.739013068 | 29.733979870 | +0.005033 | 1 | none |
| 856 | 29, 15 | 8 and 8 | 82 | z8-25f750, z8-33f750d | 14, 15 | 29.750799 | 29.748695663 | 29.745619382 | +0.003076 | 1 | none |
| 859 | 29, 18 | 9 and 9 | 116 | z9-43f760, 983h13d | 11, 11 | 29.799982 | 29.797374223 | 29.792137063 | +0.005237 | 1 | none |
| 860 | 29, 19 | 9 and 9 | 126 | 921h13, 983h13d | 10, 9 | 29.807771 | 29.804216459 | 29.801895560 | +0.002321 | 2 | none |
| 910 | 30, 10 | 9 and 9 | 118 | z9-19f720, z9-19f680 | 15, 15 | 30.676877 | 30.676556260 | 30.679149392 | -0.002593 | 13 | 8.596e-05 |
| 911 | 30, 11 | 9 and 9 | 85 | z9-36f680, z9-36f680 | 15, 15 | 30.683683 | 30.682866305 | 30.689167173 | -0.006301 | 17 | 2.088e-04 |
| 912 | 30, 12 | 8 and 9 | 94 | 495h11, z9-36f680 | 13, 14 | 30.696438 | 30.696126946 | 30.703184402 | -0.007057 | 11 | 2.337e-04 |
| 913 | 30, 13 | 9 and 9 | 78 | z9-36f680, z9-36f680 | 16, 15 | 30.712492 | 30.710251301 | 30.714694919 | -0.004444 | 15 | 1.471e-04 |
| 914 | 30, 14 | 8 and 9 | 84 | z8-31f730, z9-19f720 | 14, 18 | 30.733307 | 30.730792427 | 30.732158674 | -0.001366 | 10 | 4.519e-05 |
| 915 | 30, 15 | 9 and 9 | 96 | z9-28f760, z9-46f740 | 16, 13 | 30.744682 | 30.744348031 | 30.743639561 | +0.000708 | 8 | none |
| 920 | 30, 20 | 9 and 9 | 135 | 921fa15, z9-51f820 | 10, 11 | 30.813170 | 30.812034056 | 30.805316663 | +0.006717 | 1 | none |
| 971 | 31, 10 | 9 and 9 | 118 | z9-54f640, z9-54f640 | 12, 12 | 31.666478 | 31.665136806 | 31.661205090 | +0.003932 | 2 | none |
| 972 | 31, 11 | 9 and 9 | 93 | z9-36f680, z9-44f680 | 15, 15 | 31.683715 | 31.680502888 | 31.676523629 | +0.003979 | 7 | none |
| 973 | 31, 12 | 9 and 9 | 102 | z9-36f680, z9-36f680 | 16, 14 | 31.692665 | 31.689752756 | 31.696609270 | -0.006857 | 17 | 2.198e-04 |
| 974 | 31, 13 | 9 and 9 | 112 | z9-36f680, z9-36f680 | 14, 15 | 31.698599 | 31.697896726 | 31.703430110 | -0.005533 | 15 | 1.773e-04 |
| 975 | 31, 14 | 9 and 9 | 102 | z9-46f740, z9-19f720 | 15, 16 | 31.718526 | 31.714583981 | 31.720991746 | -0.006408 | 6 | 2.052e-04 |
| 976 | 31, 15 | 9 and 9 | 94 | z9-19f720, z9-46f740 | 17, 15 | 31.727446 | 31.727038266 | 31.733979870 | -0.006942 | 10 | 2.222e-04 |
| 977 | 31, 16 | 8 and 9 | 84 | z8-39f700, z9-28f760 | 14, 18 | 31.746470 | 31.745817967 | 31.745619381 | +0.000199 | 7 | none |
| 978 | 31, 17 | 9 and 9 | 96 | z9-28f760, z9-46f840 | 17, 14 | 31.759941 | 31.759462695 | 31.759851005 | -0.000388 | 4 | 1.242e-05 |
| 982 | 31, 21 | 9 and 9 | 116 | z9-42f840, 983co15 | 13, 13 | 31.817703 | 31.816048947 | 31.810539459 | +0.005509 | 2 | none |

What the builds say:

- A 9-arm pays where the held layout is an 8-arm design. Before this round the held file had no stack of 9 in the slice. Every certified layout here has one.
- The squeeze ends below the prediction. The difference is 0.0001 to 0.0025 of side for an 8-arm with a 9-arm, and up to 0.0056 for two 9-arms (973: predicted 31.695982, built 31.690352). The corner tool settles a corner with both stacks at the flush tilt. The squeeze of the whole layout then turns the stacks and finds more. So a row up to 0.003 above held is worth a build.
- The far zone of the 8-arm does not matter. Three choices end at the same side to 1e-8 (851, 914).
- Hops pay when they take 0.2 squares or more off a corner. The corner of 78 squares at f = 0.72 went from 4.21 to 3.78, and 913 went from 30.713517 to 30.710251. The corner of 77 squares at f = 0.68 went from 3.97 to 3.52, and 851 went from 29.679908 to 29.679003. The corner of 94 squares at f = 0.72 went from 3.84 to 3.64, and 976 went from 31.727108 to 31.727038. In the first pass, hops gave the corners of 973 and 975 (4.17 to 4.12), of 974 and of 976. A build with a hopped corner ends 0.0004 to 0.0019 of side below its prediction.
- Near misses. 740 and 797 end at their held side to 1e-9, so a corner made from nothing gives the held layout again. 977 ends 0.0002 above held with an 8-arm and a 9-arm. 915 ends 0.0007 above held, 860 0.0023 and 856 0.0031. For 972 and 971 the best build is 0.0040 and 0.0049 above held.
- Outside m 28 to 31 the generator finds no row with a 9-arm within 0.004 of held, over all 414 n.
- The fq quench of the 15 certified files moved 587 by 4.5e-4 of side. It moved 973, 911 and 976 by less than 3e-7, and the other eleven not at all. The family squeeze ends with fq, so a built file is at an fq optimum already.
- Other lanes took these layouts further in the same round. At 19:57 UTC they hold lower rows on 8 of these n: 587 (stair-b), 851, 852, 910, 912 and 973 (family), 914 (soft), 975 (midm). Each of these rows names a corner of this tool in its source. The round 17 assembly of 17:42 UTC took 8 n from this take: 793, 796, 851, 912, 913, 974, 976 and 978.

Known limits of the corner tool, as it ran here:

- In the first pass the scan places the rows and columns without the first flush stack of each arm in the way. For a staircase two columns narrower than the arm, some scan layouts cross that stack. They show as a negative scan loss, `zone_corner.exact` refuses them, and none reaches a base file. But they take the place of the valid layout of the same count, so those counts are lost. `--walls` removes this limit in the second pass.
- The tool settles the layouts with the lowest scan loss first, and a run of 10 minutes settles 150 to 280 of them. The settle moves a loss by up to 1.2 squares, so a layout that it did not settle can hold a lower corner.

## 8. What the next round should run

1. **The corner of two 9-arms near f = 0.63.** At f = 0.63 the hops reach 3.03 (class 6) and 3.26 (class 4). The floor at f = 0.64 to 0.76 is 3.4 to 3.5. One square of corner loss is about 0.012 of side at these n. So a corner at 3.03 at the side fraction of a row is worth about 0.005 of side on that n. The 3.03 is stable: a second run with another seed reached it after 22 s. Two steps, in this order. First run the staircase and the hops on a grid of f from 0.58 to 0.67 in steps of 0.01, for every class. At f = 0.64 two hop runs on corners of class 6 ended at 3.48 and 3.50 on a loaded box. So the corner changes between 0.63 and 0.64, or those two runs were too short, and nothing is measured below 0.63. Then hop each corner at the side fraction of the row that it serves, with a staircase base made at that f, and build the rows.
2. **Hops on every settled corner of two 9-arms, class by class.** This is the lever that gave new sides. 44 hop runs ran on 32 corners of two 9-arms. Three of them gave a new side: 913 (1.08e-4 of score), 851 (3.1e-5) and 976 (2.2e-6). The runs took the corners behind the rows nearest to the bar first (`hoppot.py` in the take's `work` dir ranks them). Run each corner three or four times, 15 minutes each on a free core, because the end of a run changes from run to run. Start with the corner of 78 squares at f = 0.68: it is at 3.40, and its build of 852 is 0.0002 of side above the lowest row. These classes have no hop run. At f = 0.63 they are 0, 1, 2 and 7. At f = 0.64 they are 0, 1, 2, 4, 5, 7 and 8. At f = 0.68 they are 0, 2, 7 and 8. At f = 0.72 they are 0, 1, 2, 7 and 8. At f = 0.76 they are 0, 1, 2, 3 and 7.
3. **The second pass for an 8-arm with a 9-arm below f = 0.74.** The first pass gave 912 and 914 there. The second pass ran at f = 0.74 only. Its hops did not move at f = 0.68 and 0.72.
4. **Count classes.** The library holds one far zone of a 9-arm in each class at each side fraction. Classes 0 and 1 are cheap (3.24 and 3.43 at f = 0.68), and classes 2 to 7 cost 3.74 to 4.19. The 8-and-9 corner is cheap in classes 3 to 6 (2.72 to 2.82) and dear in classes 0, 1, 2 and 7 (3.2 to 3.9). The margin table gives 22 n above 0.3 for 8 and 9, and we certify 2 of them (912 and 914). The rest need a far zone of a 9-arm that is 0.3 to 0.9 squares cheaper in its class.
5. **The low end is another design.** The generator has no row within 0.012 of held for 15 n of the slice. They are every n with k of 5 or 6, and 792, 799, 800, 848, 907, 968 and 970. The held layouts with k of 5 to 7 have tilts of 35° to 45° in short chains (section 3), and 905 and 906 equal the board. Two flush arms are not the design there.
6. **9 and 10.** It is the one wide pair with a margin (+0.54 at 914), and its best build ends 0.0019 of side above held. It needs a corner and far zones of a 10-arm in the class that 914 asks for. Do this after items 1 and 2, because the same work serves it.
7. **No arm of 7, and no arm of 11 or more.** A far zone of an arm of 11 or more costs 4.2 to 7.0 squares. The best margin with a built corner is +0.20. The arm of 7 is measured in section 6.

## 9. Round 19 (2026-11-12, 20:15 to 22:35 UTC)

**Result: 4 n certify for a gain of 5.235e-05 against the round 17 file, and each is below every other take. They are 793 (2.411e-05), 910 (1.823e-05), 794 (5.795e-06) and 853 (4.214e-06). All four are layouts of two 9-arms. 910 came from a second seed on a class-1 corner. The other three came from the deep class-6 corner of round 17, carried to the side fraction of the row. Two of them use a state that new hops reached at f = 0.68 from that carried corner: 3.19 squares, 0.25 below the floor of round 17. The corner near 3.0 at f = 0.63 is one state that is lowest at f = 0.64 (2.99). The second pass for an 8-arm with a 9-arm gave no new corner.**

The bar of this round is the round 17 file (22.1635211736, gate dir `gate/cand-round17-1112a`), lowered by every row of the other lanes' takes of rounds 17 and 19. A result counts when it certifies against the round 17 file and is below every one of those takes. All runs were on boxE with three processes. The slice is the same: m 28 to 31 and k 5 to 16.

### 9.1 A second seed on a class-1 corner gave 910

The count class of a corner is its count modulo 9. The staircase corner of 127 squares at f = 0.67 is of class 1 and loses 3.5489 squares.

| run | seed | minutes | loss after | first stack of arm 1 (y0) | first stack of arm 2 (x0) | build of 910, side less the bar |
|---|---|---|---|---|---|---|
| no hops | - | - | 3.5489 | 12.7498 | 11.6919 | +0.000027 |
| hc127 | 1 | 6 | 3.5274 | 12.7562 | 11.6829 | +0.000775 |
| hc127s2 | 2 | 8 | 3.4611 | 12.7482 | 11.6829 | **-0.000550** |
| hc127s3 | 3 | 8 | 3.4611 | 12.7482 | 11.6829 | -0.000550 |

- Seeds 2 and 3 end in the same state. Seed 2 was there after 20 s and seed 3 after 170 s. Seed 1 did not reach it in 6 minutes.
- The build of 910 from that state ends at side 30.675979735. The bar is 30.676529569, a row of the family lane. It certifies at 0.016898826246728005, which is 1.823e-05 below the round 17 file and below every take. The fq quench on boxE found nothing more.
- **A lower loss is not a better row.** Seed 1 took 0.009 off x0 and put 0.0065 on y0. Its loss fell by 0.02 squares, and its build of 910 ended 0.0007 of side higher than the build with no hops. The row asks for each of the two lengths. The loss is their weighted sum.
- The build with no hops ends at 30.676556260. That is the side of the 910 of round 17, which came from a class-1 corner of 118 squares at f = 0.68. So that corner and this staircase corner end in one layout, and the new state is another one.
- A staircase base made at f = 0.677, the side fraction of the 910 row, gave the same kind of state. Its class-1 corner of 118 squares went from 3.8044 to 3.5658 with seed 1, and its build of 910 ends at 30.676045558. That is 0.000484 below the bar and 0.000066 above the certified layout. Seed 2 on that base ends at 3.5658 too.

### 9.2 The corner of two 9-arms near 3.0 is one state, and it is lowest at f = 0.64

Round 17 found a corner of 96 squares (class 6) at 3.03 squares at f = 0.63. This round measured where that state lives.

- The same corner at f = 0.64 goes from 3.84 to **2.99** with hops, after 150 s on a free core. Round 17 had hopped the corners of 78 and of 87 squares at f = 0.64, which end at 3.46 to 3.50, and not the corner of 96 squares.
- [`twoshort_carry.py`](../twoshort_carry.py) carries one hopped corner to other side fractions with `zone_corner.carry` and writes each as a start state. The 3.03 corner carried to f = 0.64 is the 2.99 state to six digits. So it is one state.

Loss of that state by side fraction (squares):

| f | 0.60 | 0.61 | 0.62 | 0.63 | 0.64 | 0.65 | 0.66 | 0.67 | 0.68 | 0.69 | 0.70 | 0.71 | 0.72 | 0.74 | 0.76 | 0.78 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| loss | 3.38 | 3.25 | 3.12 | 3.03 | 2.99 | 3.08 | 3.18 | 3.29 | 3.39 | 3.49 | 3.70 | 3.92 | 4.15 | 4.65 | 5.16 | 5.69 |

- The loss rises by 0.13 squares for each 0.01 of side fraction below 0.63. It rises by 0.10 from 0.64 to 0.69, and by 0.22 to 0.27 above 0.69.
- At f = 0.68 the carried state loses 3.39. The hops of round 17 ended at 3.40 and 3.44 there, so the floor of round 17 at f = 0.68 is this state or one next to it. Above f = 0.69 the floor is another state. At f = 0.72 the carried state loses 4.15 and the hops end at 3.78. At f = 0.76 it loses 5.16 against 4.36.
- More runs end where round 17 ended. From the staircase corner of 96 squares, 6 minutes on a free core end at 3.4406 at f = 0.68 and at 3.7835 at f = 0.72. On the corner of 78 squares at f = 0.68, seed 2 ran 10 minutes and ends at 3.4406 too.
- What the state is. The staircase has upright columns of 7, 6, 5, 4, 3, 2 and 1 squares. The 2.99 state has columns of 8, 6, 6, 5, 3, 1 and 1, with one more square 1° from upright. Three squares left the tilt of arm 1. The first stack of arm 1 sits 0.12 nearer the corner, and the first stack of arm 2 sits 0.02 farther from it.
- The other hopped corners carried the same way. The corner of 121 squares (class 4, 3.26 at f = 0.63) loses 3.30 at f = 0.62 and 0.64. From f = 0.65 to 0.68 it loses 3.38, 3.46, 3.56 and 3.77. The corner of 78 squares (class 6, 3.40 at f = 0.68) loses 3.56, 3.46, 3.45 and 3.42 at f = 0.64 to 0.67. It loses 3.49 at f = 0.69 and 3.70 at f = 0.70.

**The 2.99 state gives no row.** The generator carries it to the side fraction of each row. Its nearest rows are 851 at 0.0027 of side above the bar and 910 at 0.0051, both at f = 0.68, where the state loses 3.39. No n of the slice has a row with a class-6 corner near f = 0.64. The state wins its 0.4 squares on one length only, the one of arm 1. A row gains from that only when the length of its arm 1 fits.

### 9.3 The deep state at the side fraction of a row gave 793, 853 and 794

`twoshort_carry.py` wrote the 2.99 state as a start state at f = 0.674, 0.684, 0.69 and 0.70. `zone_corner.py search` on a start state keeps up to four points of its trade between the two lengths, and the library gets each as a corner (variants a to d).

- At f = 0.684 the state loses 3.4302, and 3 minutes of hops with seed 1 did not move it. Its variant c, with two far zones of 36 squares, is a row of 793 that the generator predicts 0.0025 of side above the bar.
- The build ends at 28.672765056, which is 0.000679 below the bar (28.673443927, this lane's row of round 17). After its fq quench it certifies at 0.018199739349723965, 2.411e-05 below the round 17 file and below every take.
- The squeeze of the build took the layout 0.0030 below its prediction (28.672967868). Then fq took 0.0002 more. Until this build the screen step sent a layout to fq only within 0.00003 of the bar. After 793 it sent one within 0.00035, and after 853 within 0.0007.
- The generator had this state in its library from round 17, as the corner at f = 0.63. It carries a corner to the side fraction of each row by itself. Its nearest row of 793 that way was 0.0084 above the bar. The row came from the trade of lengths at f = 0.684, so the base has to be made at the side fraction of the row.

**Hops from the carried state reach 3.19 at f = 0.68.** The carried state loses 3.3894 there.

| seed | minutes | loss after | y0 | x0 |
|---|---|---|---|---|
| 1 | 3 | 3.3018 | 9.6963 | 10.9608 |
| 2 | 5 | **3.1892** | 9.7100 | 10.9336 |
| 3 | 6 | 3.3894 (no move) | 9.7323 | 10.9354 |

- 3.19 is 0.25 squares below the floor of round 17 at f = 0.68 (3.44 on this corner, 3.40 on the corner of 78 squares).
- The 3.19 state carried to f = 0.674, 0.679, 0.684, 0.69, 0.695, 0.705 and 0.712 loses 3.13, 3.17, 3.25, 3.35, 3.43, 3.61 and 3.78. So it rises by 0.16 squares for each 0.01 of side fraction, and by 0.24 above f = 0.70.

**Builds from the 3.19 state.** Each carried copy went into the library with the points of its length trade. Every row within 0.004 to 0.006 of the bar was built. All sides are less the bar:

| n | base at f | variant | far zones (squares) | predicted | after the squeeze | after fq | result |
|---|---|---|---|---|---|---|---|
| 853 | 0.679 | b | 46 and 27 | +0.0028 | +0.000304 | **-0.000123** | certified at 0.01714774887663917, gain 4.214e-06 |
| 794 | 0.712 | a | 19 and 27 | +0.0041 | -0.000162 | **-0.000163** | certified at 0.017956370367327112, gain 5.795e-06 |
| 912 | 0.674 to 0.712 | a | 36 and 44 | +0.0005 | +0.000309 | +0.000309 | above the bar |
| 851 | 0.674 to 0.712 | a, c, d | 36 and 44 | +0.0012 | +0.000524 | +0.000524 | above the bar |
| 852 | 0.679, 0.68 | c, d | 36 and 36 | +0.0010 | +0.000526 | +0.000526 | above the bar |

- The bar of 853 is 29.707106783, which is 29 + 1/√2. The build ends at 29.706983693.
- fq took 0.0004 of side on 853 and 0.0002 on 793. It took nothing on 794, 851, 852 and 912.
- For 912, 851 and 852 the builds from different copies end in one layout, to 1e-8 of side. So another copy does not help them. They need 0.03 to 0.045 squares more off the corner.
- For 794 and 853 the copy decides. The copy at f = 0.712 builds 794 below the bar, and the copies at f = 0.684 and 0.69 build the same row 0.0013 above it. 853 ends 0.000123 below the bar from the copy at f = 0.679, 0.000069 below from f = 0.712 and 0.000057 below from f = 0.674.
- The fq quench on boxE, from each certified file: 793 went 6.3e-08 of side lower, and 794, 853 and 910 did not move.

### 9.4 Which class of corner each n can use

A layout of two 9-arms needs the counts of its corner and its two far zones to add up to n. The far zones of a 9-arm are cheap in two classes only (0 and 1 at f = 0.68, with 3.24 and 3.43 squares). So each n has two or three classes of corner that can reach it, and one class does most of the work.

The nearest row of each n by corner class, over every generator file of rounds 17 and 19, for rows within 0.006 of the bar of round 19:

| class | n it serves (predicted side above the bar, f of the row) |
|---|---|
| 1 | 910 (-0.0002, 0.676), 908 (+0.0039, 0.638), 971 (+0.0053, 0.666) |
| 3 | 975 (+0.0018, 0.716), 973 (+0.0035, 0.693), 910 (+0.0036, 0.680), 972 (+0.0042, 0.681), 974 (+0.0055, 0.703) |
| 4 | 976 (+0.0004, 0.727), 911 (+0.0005, 0.683), 974 (+0.0007, 0.699), 910 (+0.0020, 0.679), 973 (+0.0035, 0.693), 793 (+0.0037, 0.677), 913 (+0.0044, 0.715), 851 (+0.0052, 0.684), 852 (+0.0056, 0.696), 791 (+0.0058, 0.640) |
| 5 | 851 (+0.0017, 0.681), 910 (+0.0041, 0.681), 913 (+0.0055, 0.716), 977 (+0.0056, 0.749) |
| 6 | 853 (+0.0002, 0.707), 852 (+0.0002, 0.690), 912 (+0.0005, 0.695), 793 (+0.0007, 0.674), 851 (+0.0012, 0.680), 854 (+0.0014, 0.722), 794 (+0.0018, 0.686), 913 (+0.0022, 0.712), 914 (+0.0026, 0.731), 915 (+0.0036, 0.744), 910 (+0.0037, 0.680), 911 (+0.0047, 0.688), 977 (+0.0054, 0.749) |

- Class 6 is the class with the deep state, and its rows sit at f = 0.67 and above.
- A row near f = 0.64 needs class 1 (908) or class 4 (791), and those rows are 0.004 to 0.006 of side above the bar. That is 0.3 to 0.5 squares of corner loss.
- Classes 0, 2, 7 and 8 have no row within 0.0099 of the bar on any n of the slice.
- So below f = 0.67 no n of this slice has a row within 0.0039 of the bar with two 9-arms. The work that pays is at f = 0.67 to 0.76, on classes 1, 3, 4 and 6.

### 9.5 Staircases and hops on the grid of side fractions

The second-pass staircase of two 9-arms, 5 minutes for each side fraction (10 minutes in round 17). Each cell is the lowest settled loss of the class, with the count of that corner:

| f | round | settled | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 | class 8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.63 | 17 | 150 | 4.13 (81) | 4.02 (127) | 4.48 (128) | 3.86 (129) | 3.86 (121) | 3.97 (77) | **3.81** (96) | 4.03 (79) | 3.92 (71) |
| 0.64 | 17 | 232 | 4.19 (90) | 3.94 (127) | 4.24 (137) | 3.91 (102) | 3.95 (94) | 4.15 (95) | **3.71** (78) | 4.07 (97) | 4.07 (98) |
| 0.65 | 19 | 63 | 4.26 (99) | **3.54** (136) | 4.36 (119) | 4.12 (129) | 3.69 (112) | 3.70 (86) | 3.60 (96) | 4.74 (106) | 4.13 (89) |
| 0.66 | 19 | 69 | 4.32 (81) | **3.65** (136) | 4.35 (119) | 3.90 (102) | 3.70 (85) | 4.08 (95) | 3.77 (96) | 4.96 (88) | 3.70 (71) |
| 0.67 | 19 | 52 | 4.38 (90) | 3.55 (127) | 4.93 (92) | 3.95 (102) | **3.49** (121) | 4.38 (77) | 3.84 (78) | 5.28 (70) | 4.28 (107) |
| 0.677 | 19 | 49 | 4.42 (90) | 3.80 (118) | 4.76 (110) | 4.07 (93) | **3.48** (121) | 4.30 (95) | 3.90 (96) | 4.35 (97) | 4.49 (89) |
| 0.68 | 17 | 279 | 4.04 (72) | 3.66 (118) | 4.34 (101) | 3.83 (93) | **3.49** (85) | 3.97 (104) | 3.92 (96) | 4.70 (97) | 4.52 (107) |
| 0.72 | 17 | 283 | 3.77 (126) | **3.65** (118) | 3.86 (119) | 3.93 (102) | 3.80 (85) | 4.35 (68) | 4.13 (105) | 4.71 (70) | 4.20 (107) |
| 0.76 | 17 | 257 | **3.59** (117) | 4.07 (100) | 3.92 (110) | 4.08 (111) | 3.78 (103) | 4.17 (68) | 4.69 (96) | 4.71 (106) | 4.41 (125) |

- The rows of f = 0.63, 0.64, 0.68, 0.72 and 0.76 are the runs of round 17. This round ran f = 0.65, 0.66 and 0.67, and f = 0.677, which is the side fraction of the 910 row.
- Class 1 is the lowest class at f = 0.65 and 0.66 (3.54 and 3.65, on 136 squares). Class 4 is the lowest at f = 0.67 to 0.68 (3.48 to 3.49).
- A run of 5 minutes settles 49 to 69 corners. The runs of 10 minutes of round 17 settled 150 to 283.
- The staircases at f = 0.58 to 0.62 did not run. No n of the slice has a row within 0.006 of the bar there (section 9.4). The carried state gives the loss of the deep corner at f = 0.60 to 0.62 (3.38 to 3.12).

Every hop run of this round. "Cut" marks a run that the deadline stopped:

| f | corner squares | class | start | seed | loss before | loss after | change | last gain at (s) | hops | run |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.63 | 127 | 1 | staircase | 1 | 4.02 | 3.82 | -0.21 | 223 | 124 | j127 |
| 0.64 | 127 | 1 | staircase | 1 | 3.94 | 3.70 | -0.24 | 185 | 127 | i127 |
| 0.64 | 96 | 6 | carried | 1 | 2.99 | 2.99 | +0.00 | 0 | 248 | na |
| 0.64 | 96 | 6 | staircase | 1 | 3.84 | 2.99 | -0.84 | 150 | 111 | i96 |
| 0.65 | 136 | 1 | staircase | 1 | 3.54 | 3.49 | -0.06 | 3 | 124 | ha136 |
| 0.65 | 136 | 1 | staircase | 2 | 3.54 | 3.49 | -0.06 | 4 | 136 | ha136s2 |
| 0.65 | 112 | 4 | staircase | 1 | 3.69 | 3.35 | -0.34 | 19 | 80 | ha112 |
| 0.66 | 136 | 1 | staircase | 1 | 3.65 | 3.49 | -0.16 | 32 | 130 | hb136 |
| 0.66 | 96 | 6 | carried | 1 | 3.15 | 3.15 | +0.00 | 0 | 62 | cq6600 |
| 0.67 | 127 | 1 | staircase | 1 | 3.55 | 3.53 | -0.02 | 74 | 138 | hc127 |
| 0.67 | 127 | 1 | staircase | 2 | 3.55 | 3.46 | -0.09 | 199 | 177 | hc127s2 |
| 0.67 | 127 | 1 | staircase | 3 | 3.55 | 3.46 | -0.09 | 170 | 171 | hc127s3 |
| 0.67 | 121 | 4 | staircase | 1 | 3.49 | 3.48 | -0.00 | 10 | 142 | hc121 |
| 0.67 | 96 | 6 | carried | 1 | 3.29 | 3.29 | +0.00 | 0 | 105 | cd6700 |
| 0.674 | 96 | 6 | carried | 1 | 3.13 | 3.13 | +0.00 | 0 | 96 | cm6740 |
| 0.677 | 118 | 1 | staircase | 1 | 3.80 | 3.57 | -0.24 | 15 | 148 | hk118 |
| 0.677 | 118 | 1 | staircase | 2 | 3.80 | 3.57 | -0.24 | 113 | 158 | hk118s2 |
| 0.679 | 96 | 6 | carried | 2 | 3.17 | 3.17 | +0.00 | 0 | 160 | ck6790s2 |
| 0.68 | 93 | 3 | staircase | 1 | 3.83 | 3.63 | -0.20 | 143 | 189 | e93 |
| 0.68 | 102 | 3 | staircase | 1 | 3.83 | 3.64 | -0.19 | 121 | 170 | e102 |
| 0.68 | 85 | 4 | staircase | 2 | 3.49 | 3.49 | +0.00 | 0 | 193 | e85s2 |
| 0.68 | 78 | 6 | staircase | 2 | 3.92 | 3.44 | -0.48 | 389 | 361 | s78b2 |
| 0.68 | 96 | 6 | carried | 1 | 3.39 | 3.30 | -0.09 | 58 | 86 | cd6800 |
| 0.68 | 96 | 6 | staircase | 1 | 3.92 | 3.44 | -0.48 | 219 | 170 | k96 |
| 0.68 | 96 | 6 | carried | 2 | 3.39 | 3.19 | -0.20 | 219 | 159 | cd6800s2 |
| 0.68 | 96 | 6 | carried | 3 | 3.39 | 3.39 | +0.00 | 0 | 190 | cd6800s3 |
| 0.684 | 96 | 6 | carried | 1 | 3.25 | 3.25 | +0.00 | 0 | 55 | ck6840b |
| 0.684 | 96 | 6 | carried | 1 | 3.43 | 3.43 | +0.00 | 0 | 102 | cj6840 |
| 0.69 | 96 | 6 | carried | 1 | 3.49 | 3.49 | +0.00 | 0 | 108 | cj6900 |
| 0.69 | 96 | 6 | carried | 1 | 3.35 | 3.35 | +0.00 | 0 | 57 | ck6900b |
| 0.695 | 96 | 6 | carried | 2 | 3.43 | 3.43 | +0.00 | 0 | 158 | ck6950s2 |
| 0.70 | 96 | 6 | carried | 1 | 3.51 | 3.51 | +0.00 | 0 | 56 | cq7000 |
| 0.705 | 96 | 6 | carried | 1 | 3.61 | 3.61 | +0.00 | 0 | 94 | cm7050 |
| 0.712 | 96 | 6 | carried | 1 | 3.78 | 3.78 | +0.00 | 0 | 92 | cm7120 |
| 0.72 | 94 | 4 | staircase | 2 | 3.84 | 3.64 | -0.20 | 35 | 175 | p94s2 |
| 0.72 | 96 | 6 | carried | 1 | 3.97 | 3.97 | +0.00 | 0 | 58 | cq7200 |
| 0.72 | 96 | 6 | staircase | 1 | 4.21 | 3.78 | -0.43 | 45 | 178 | l96 |

- The runs cd and cj start from the 2.99 state carried to that side fraction. The runs ck, cm and cq start from the 3.19 state carried the same way. The run na starts from the 2.99 state itself.
- **A second seed is worth its time.** Six corners have runs with two seeds or more now. Two ended lower with a later seed: the class-1 corner of 127 squares at f = 0.67 (3.53, then 3.46) and the 2.99 state carried to f = 0.68 (3.30, then 3.19). Four ended in the same state. They are 136 squares at f = 0.65 (3.49), 118 squares at f = 0.677 (3.57), 94 squares at f = 0.72 (3.64) and 85 squares at f = 0.68 (3.49, no move with either seed).
- **Class 4 at f = 0.65.** The corner of 112 squares goes from 3.69 to 3.35 in 19 s. The class-4 corner of round 17 carried to f = 0.65 loses 3.38. It has no row within 0.004 of the bar.
- **Class 1 at f = 0.63 to 0.66** ends at 3.82, 3.70, 3.49 and 3.49. The nearest row of 908 is 0.0039 above the bar, from the corner at f = 0.65, and its build ends 0.0029 above the bar.
- **A carried state seldom moves.** Of 17 hop runs on a carried state, 2 moved. Both ran at f = 0.68, with seeds 1 and 2. Most of these runs had 2 to 4 minutes.

### 9.6 Designs that failed

- **A staircase with other column heights.** `twoshort_corner.py stair` got an option for the heights of the upright columns. The control passed. The heights 7, 6, 5, 4, 3, 2, 1 gave the scan of the plain staircase (47 counts, 108 layouts) and its settled corner (78 squares, 3.7075). Then the run at f = 0.64 took two other sets of heights. They are those of the 2.99 state (8, 6, 6, 5, 3, 1, 1) and of the 3.03 state (8, 6, 5, 5, 3, 2, 1). The lowest of its 52 settled corners is 3.99 (class 5). The corner of 96 squares settles at 5.55, not 2.99. The column heights do not make the state: its tilted rows moved by 0.47 of a square along the row too. The option is not in the tool.
- **Class 3 for 910.** 910 takes a class-3 corner with two far zones of class 0. Hops took the staircase corners of 93 and of 102 squares at f = 0.68 from 3.83 to 3.63 and 3.64. Their builds of 910 end 0.0024 and 0.0023 of side above the bar, and the build with no hops ends 0.0022 above it. The hops won on a length that the row does not ask for.
- **The count neighbours of the 2.99 state.** `zone_corner.py search` deleted up to 3 squares and inserted up to 3 from the 2.99 state at f = 0.64. Then it hopped on each count, for 9 minutes in all. The corner of 95 squares (class 5) ends at 3.63. The others end at 4.35 (94 squares, class 4), 4.77 (93, class 3), 4.53 (97, class 7), 5.56 (98, class 8) and 4.80 (99, class 0). No row is within 0.004 of the bar. The state does not pass to the next counts.

### 9.7 Builds

- 154 builds ran on 17 n: 54 with fq and 100 with the squeeze only. A build with the squeeze only takes 5 to 40 s, and fq with its polish takes 20 s to 5 minutes more.
- 12 builds on 4 n end below the bar (793, 794, 853, 910), and those n are certified.
- 7 builds end on the bar to 1e-7 of side: 852 from 2 corners, 911 from 2 corners, 974 from 3 corners. These are the layouts of round 17 again. The squeeze reaches them from any corner of the same class, so a new side needs a new state of the corner, not another start.
- A build ends below its predicted side by 0.0013 at the median. 15 of 154 end more than 0.003 below it, and the lowest ends 0.0054 below.
- The rows that round 17 never built, within 0.005 of the bar, were built from five libraries of round 17 and from the staircases of this round. None ends below the bar.
- Every build is in [`results/twoshort-r19-2026-11-12.tsv`](../results/twoshort-r19-2026-11-12.tsv).

### 9.8 An 8-arm with a 9-arm, second pass

The second pass of the staircase for an 8-arm with a 9-arm ran at f = 0.68 and 0.72, 5 minutes each. Round 17 ran it at f = 0.74.

| f | round | settled | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.68 | 19 | 78 | 3.34 (88) | 3.90 (73) | 3.21 (98) | 2.82 (75) | 2.78 (84) | **2.72** (77) | **2.72** (94) | 3.34 (71) |
| 0.72 | 19 | 82 | 3.90 (88) | 3.48 (81) | 3.30 (98) | 3.25 (91) | **2.79** (84) | 3.03 (77) | 3.03 (94) | 3.84 (79) |
| 0.74 | 17 | 266 | 4.04 (88) | 3.64 (89) | 3.13 (90) | 3.08 (99) | **2.98** (84) | 3.35 (77) | 3.35 (94) | 3.90 (103) |

- The lowest corner at f = 0.68 loses 2.7204 (77 and 94 squares). The corner of 94 squares of the first pass loses 2.7204 there too. At f = 0.72 the lowest loses 2.7895 (84 squares), which is the corner of the first pass again.
- The builds within 0.004 of the bar, without fq: from f = 0.68, 796 ends 0.0011 above the bar, 912 0.0013 and 914 0.0022. From f = 0.72, 796 ends 0.0011 above it, 912 0.0013, 914 0.0022, 977 0.0022 and 851 0.0029.
- So the second pass gives no new corner for this pair at these two side fractions. The passes at f = 0.64 and 0.76 did not run.

### 9.9 What the next round should run

1. **The deep class-6 state at the side fraction of every row, with more seeds.** This gave 793, 853 and 794 in the last 45 minutes of the round. One seed of three reached 3.19 at f = 0.68, and no run tried a fourth. The builds of 912, 851 and 852 from the 3.19 state end 0.0003 to 0.0005 of side above the bar. That is 0.03 to 0.045 squares of corner loss. Carry the 2.99 state and the 3.19 state to each side fraction from 0.66 to 0.72 in steps of 0.005. Run seeds 2 to 6 for 10 minutes on each copy. Build every row within 0.006 of the bar, with fq.
2. **The same carry for the other hopped corners.** The row of 793 came from a point of the length trade of a copy made at f = 0.684. The generator's own carry from f = 0.63 gave that n nothing within 0.008. The class-1 state of 910 (3.46 at f = 0.67) has no copies at other side fractions yet. The class-4 corners (3.35 at f = 0.65, 3.49 at f = 0.68) have none either. The class-4 rows of 976, 911 and 974 are predicted 0.0004 to 0.0007 above the bar, and their builds end on the bar.
3. **Seeds 2 and 3 on every hop run.** Seed 1 missed in 6 minutes the state of 910 that seed 2 found in 20 s. On the carried corner at f = 0.68, seed 1 ended at 3.30, seed 2 at 3.19, and seed 3 did not move. Four other corners gave the same end with two seeds, so two or three seeds are enough.
4. **fq on every squeezed build within 0.0007 of the bar.** fq took 0.0004 of side on 853 and 0.0002 on 793. The screen step of the first 90 minutes sent a build to fq only within 0.00003 of the bar.
5. **Hops that take the two lengths of a row as the goal.** A lower loss made a worse row twice. Seed 1 on the class-1 corner put 910 up by 0.0007. Class 3 at f = 0.68 lost 0.20 squares of loss, and 910 was not better. `zone_corner.py search --caps` hops against two length caps. The corners lane fixed it this round, and this lane did not use it yet.
6. **908.** Its nearest row is from the class-1 corner of 136 squares at f = 0.65. The build ends 0.0029 above the bar. It needs 0.25 squares, so a base at f = 0.638 with three seeds is the cheap test.
7. **Stop the second pass for an 8-arm with a 9-arm at f = 0.68 and 0.72.** It gives the corners of the first pass again. Its builds end 0.0011 to 0.0029 above the bar. The passes at f = 0.64 and 0.76 did not run.
8. **No staircase below f = 0.63 for this slice.** The lowest side fraction with a row within 0.006 of the bar is 0.638 (908). The staircases at f = 0.58 to 0.62 did not run. The hop runs on classes 0, 2, 7 and 8 did not run either. Those classes have no row within 0.0099 of the bar.

## 10. Round 20 (2026-11-12 22:36 to 2026-11-13 01:05 UTC)

**Result: 2 n certify for 3.980e-05 against the round 18 file, and each is below every other take: 852 (3.368e-05) and 794 (6.128e-06). Over the other takes the gain is 3.401e-05. Both are layouts of two 9-arms from seeds 2 and 3 on the deep class-6 state copied to f = 0.69. Round 19 had hopped that copy with seed 1 only. Capped hops, copies without new seeds and the 908 carry were dry.****

The bar of this round is the round 18 file (22.1604820601, gate dir `gate/cand-round18-1112a`). Every row of the frozen takes of round 19 and of the live takes of round 20 lowers it. Our own round 19 take is part of that bar. All runs were on boxE with three processes. The first agent of the round died in a harness restart at 22:48 UTC. Its three queue workers on boxE ran on, and the second agent took them over.

### 10.1 Seeds 2 and 3 on the 2.99 state at f = 0.69 gave 852 and 794

The 2.99 state is the hopped class-6 corner of 96 squares of round 17. Round 19 copied it to f = 0.69 and ran seed 1 there, and it did not move (3.4914). This round ran seeds 2 to 5 on that copy, 8 minutes each.

- Seed 2 ended at 3.3472 and seed 3 at 3.3384. Seed 4 ended at 3.4814, and seed 5 did not move.
- The state of seed 3 has four points of its length trade (variants a to d). Its variant c builds 852 at side 29.689147722, which is 0.000983 below the bar. The generator predicted that row 0.0039 **above** the bar. The squeeze took 0.0049 off it.
- That 852 certifies at 0.017133441217701106, 3.368e-05 below the round 18 file and below every take.
- The same state copied to f = 0.6948 (`carryq.sh`, variant a) builds 794 at 28.683970925. It certifies at 0.017956037263424873. That is 6.128e-06 below the round 18 file, and 3.3e-07 below the lowest other take (our own 794 of round 19).
- The fq quench on boxE, from each certified file, found nothing more (86 s and 17 s).
- The other builds of these states end above the bar. The nearest are 853 at 29.706727541 and 912 at 30.694849588. The 853 is 2.0e-6 above the 853 of the family lane, and it comes from the copy at f = 0.673. The 912 is 2.2e-5 above the bar. Scans of `midm_scan.py` kicks (kick and lkick) on that 853 (540 s, 10 tries) and on that 912 (600 s, 29 tries) found nothing.

### 10.2 A copy of a state does not make a new layout

Copies of four hopped corners went to the side fraction of each row near them. Each copy went into a library, and every row within 0.006 of the bar was built.

| state | class | copies at f | loss of the copies | what the builds give |
|---|---|---|---|---|
| the 3.19 state (round 19, f = 0.68) | 6 | 0.676 to 0.716, 8 copies | 3.14 to 3.87 | 912 +0.000309, 851 +0.000524, 853 +0.000324, 852 +0.0010 to +0.0013 |
| the class-1 state of 910 (3.46 at f = 0.67) | 1 | 0.634 to 0.69, 6 copies | 3.51 to 3.83 | 910 on our round 19 910, 971 +0.0038 |
| the class-4 state of 112 squares (3.35 at f = 0.65) | 4 | 0.657 to 0.727, 4 copies | 3.38 to 4.60 | 910 +0.00075 |
| the class-1 corner of 136 squares for 908 (3.49 at f = 0.65) | 1 | 0.638, 0.643 | 3.55, 3.52 | 908 +0.00314 from every copy |

- Each control passed. At its own f each copy keeps the loss of its state (3.4611, 3.3528, 3.4869 and 3.3384).
- The builds of one n from every copy of one state end in one layout, to 1e-8 of side. Only a hop that reaches a new state gives a new layout. The copy then picks which rows that state reaches. The 794 of section 10.1 came from a copy at f = 0.6948, not from the state at its own f.
- 908 needs 0.25 squares of corner loss. The copies at f = 0.638 and 0.643 change nothing there. It is dry.

### 10.3 Capped hops do not move the 912 corner

`zone_corner.py search --caps` at e844c88 hops under a cap on one length of the corner. We ran it on the 3.19 state copied to f = 0.695, the corner of the 912 row. The cap was 0.0008 under y0, and then 0.0008 under x0, for 454 s each.

- The hops ran: 157 and 153 tries.
- No try won. The loss stayed at 3.4265, and neither length went under its cap.
- So no state with one length 0.0008 shorter is within reach of this corner.

### 10.4 Staircases at f = 0.695 and 0.705

The grid of second-pass staircases had f = 0.63 to 0.68, 0.72 and 0.76. The rows of 912 (0.695), 852 (0.690), 973 (0.693), 974 (0.699) and 853 (0.707) sit between them. Round 19 started f = 0.70 at 22:20, and the deadline cut it.

| f | settled | lowest | class 1 | class 3 | class 4 | class 6 |
|---|---|---|---|---|---|---|
| 0.695 | 48 | 3.6473 (94, class 4) | 3.90 (118) | 3.89 (93) | **3.65** (94) | 4.03 (78) |
| 0.705 | 53 | 3.6727 (101, class 2) | 3.95 (109) | 3.87 (93) | 3.83 (85) | 4.11 (78) |

- The class-4 corner of 94 squares at f = 0.695 builds 911 with no hops. The build ends 8.2e-5 above the bar after the squeeze, and 7.2e-7 above it after fq. That is the round 18 layout of 911 again.
- The hops on classes 0, 2, 7 and 8 did not run. Those classes have no row within 0.0099 of the bar (section 9.4).

### 10.5 Every hop run of this round

| run | start state | f | squares | class | seed | seconds | loss before | loss after | what its builds gave |
|---|---|---|---|---|---|---|---|---|---|
| cd6800s4 | the 2.99 state copied | 0.68 | 96 | 6 | 4 | 453 | 3.3894 | 3.3894 | 852 on the round 18 layout |
| cd6800s5 | the 2.99 state copied | 0.68 | 96 | 6 | 5 | 454 | 3.3894 | 3.3236 | 852 +0.000526, 851 +0.00088 |
| cj6900s2 | the 2.99 state copied | 0.69 | 96 | 6 | 2 | 455 | 3.4914 | 3.3472 | 912 +0.000022 |
| cj6900s3 | the 2.99 state copied | 0.69 | 96 | 6 | 3 | 455 | 3.4914 | **3.3384** | **852 -0.000983**, 912 +0.000022, 853 +0.000257, 851 +0.000304 |
| cj6900s4 | the 2.99 state copied | 0.69 | 96 | 6 | 4 | 454 | 3.4914 | 3.4814 | nothing within 0.0005 |
| cj6900s5 | the 2.99 state copied | 0.69 | 96 | 6 | 5 | 453 | 3.4914 | 3.4914 | 852 on the round 18 layout |
| d16820s2 | the 3.19 state copied | 0.682 | 96 | 6 | 2 | 455 | 3.2208 | 3.2182 | no builds |
| d16920s2 | the 3.19 state copied | 0.692 | 96 | 6 | 2 | 454 | 3.3789 | 3.3679 | no builds |
| d16920s3 | the 3.19 state copied | 0.692 | 96 | 6 | 3 | 453 | 3.3789 | 3.3679 | no builds |
| d17080s2 | the 3.19 state copied | 0.708 | 96 | 6 | 2 | 454 | 3.6791 | 3.6791 | no builds |
| hp96 | staircase | 0.695 | 96 | 6 | 1 | 274 | 4.0319 | 3.5421 | 852 on the round 18 layout, 793 +0.000045 |
| hp96s2 | staircase | 0.695 | 96 | 6 | 2 | 454 | 4.0319 | 3.4561 | 853 +0.000271 |
| hp96s3 | staircase | 0.695 | 96 | 6 | 3 | 456 | 4.0319 | 3.5421 | 851 +0.0015 |
| hq96 | staircase | 0.705 | 96 | 6 | 1 | 274 | 4.1057 | 3.6062 | 912 +0.000309, 851 +0.000524 |
| hq96s2 | staircase | 0.705 | 96 | 6 | 2 | 456 | 4.1057 | 3.6062 | the same |
| hq96s3 | staircase | 0.705 | 96 | 6 | 3 | 456 | 4.1057 | 3.5817 | 912 +0.000309, 854 +0.0013 |
| hp94 | staircase | 0.695 | 94 | 4 | 1 | 273 | 3.6473 | 3.6285 | no builds |
| hp94s2 | staircase | 0.695 | 94 | 4 | 2 | 452 | 3.6473 | 3.6202 | no builds |
| hq85 | staircase | 0.705 | 85 | 4 | 1 | 272 | 3.8258 | 3.6850 | no row within 0.004 |
| hp118 | staircase | 0.695 | 118 | 1 | 1 | 333 | 3.9006 | 3.7101 | no row within 0.004 |
| hq109 | staircase | 0.705 | 109 | 1 | 1 | 336 | 3.9496 | 3.8321 | no row within 0.004 |
| hp93 | staircase | 0.695 | 93 | 3 | 1 | 272 | 3.8939 | 3.6010 | 973 +0.0030 |

- The runs cd and cj start from the 2.99 state copied to that f. The runs d1 start from the 3.19 state copied the same way.
- **A later seed found a deeper state five times.** At f = 0.69 the 2.99 state reached 3.35 with seed 2 and 3.34 with seed 3. At f = 0.68 seed 5 found a third state (3.32), after seeds 3 and 4 did not move. The class-6 staircase corner at f = 0.695 reached 3.54 with seed 1 and 3.46 with seed 2. At f = 0.705 seed 3 reached 3.58, and seeds 1 and 2 ended at 3.61.
- **The 3.19 state does not move again.** Its copies at f = 0.682, 0.692 and 0.708 moved by 0.011 squares or less with seeds 2 and 3.
- The capped runs, the copies with 1-minute hop lines and two chained runs that we stopped after 47 s are not in the table.

### 10.6 912 and 851 end in one layout from many corners

The builds of 912 end at +0.000309 of side, and those of 851 at +0.000524, from every copy of the 3.19 state and from the capped runs. They end there too from the class-6 staircase corner at f = 0.705, which is another state (3.58 to 3.61 squares). Their far zones are the lattice tapers of 36 and 44 squares at f = 0.68. The classfill lane swept the 9-arm tapers of 36 squares at f = 0.68 and 0.69 in round 17, and they did not move (classfill.md, section 12).

Only the states of seeds 2 and 3 at f = 0.69 gave other layouts of these two n: 912 at +2.2e-5 and 851 at +3.0e-4. A scan of 600 s of `midm_scan.py` kicks (kick and lkick, 29 tries) on that 912 found nothing.

### 10.7 What the next round should run

1. **Seeds 2 to 6 on the 2.99 state, copied to each f from 0.66 to 0.72**. At f = 0.69 seeds 2 and 3 gave the two deepest states of the round. Those states gave 852, 794 and the near rows of 853 and 912. At f = 0.68 seeds 2 and 5 gave new states. The copies at f = 0.674, 0.684, 0.70 and 0.72 had only seed 1, for 2 to 3 minutes.
2. **Copy every new state to the f of every row near it**. Build every row within 0.006 of the bar. 794 came from a copy of the state of seed 3 at f = 0.6948. The near row of 853 came from a copy at f = 0.673. The 852 row was predicted 0.0039 above the bar and ended 0.000983 below it.
3. **The near rows of this round:** 853 at 2.0e-6 of side above the bar and 912 at 2.2e-5, both in `take-twoshort-r20/near`. They need a kick or a family step, not more corners.
4. **Stop these**. Capped hops on the 912 corner won 0 of 310 tries. A copy of a state without new seeds gives its old layouts. The 908 carry gives one layout, 0.0031 above the bar. More seeds on the 3.19 state move it by 0.011 squares or less. Classes 0, 2, 7 and 8 have no row near the bar.

## 11. Round 21 (2026-11-13, 01:03 to 12:20 UTC)

**Result: 1 n certifies, 793, for 5.287e-07 against the round 19 file and 2.150e-07 under every other take. We kicked the family build of a near row locally, without fq, in a chain of runs. That took 793 from 1.1e-4 of side above the bar to 6.1e-6 of side below it. The seeds and the copies of the deep class-6 state gave 176 builds and no row below the bar. Four of the nine seeds on the copies of the 2.99 state landed on a state that we had already. Six seeds on other copies did not move.**

The bar of this round is the round 19 file (22.1514697138, gate dir `gate/cand-round19-1112a`). Every row of the frozen takes of round 20 and of the live takes of round 21 lowers it. Our own round 20 take is part of that bar. All runs were on boxE with three processes. Three agents ran this round. The first one started the queue and died at 01:20 UTC on a usage limit. The queue ran on by itself until 02:29. The second agent started a new queue at 09:54 and died at 09:55. The third agent took over that queue and ran it to 12:10.

### 11.1 Seeds and copies of the 2.99 state: 176 builds, no row below the bar

The first queue ran the next list of round 20. It ran seeds on the 2.99 state copied to f = 0.67 to 0.70. It also copied the new states of round 20 to the rows near them. Each run that took 0.05 squares or more off the corner built every row within 0.006 of the bar.

| run | start state | f | seed | loss before | loss after | nearest builds (side above the bar) |
|---|---|---|---|---|---|---|
| cj6740s2 | the 2.99 state copied | 0.674 | 2 | 3.3278 | 3.1346 | 912 +0.0011 |
| cj6740s3 | the 2.99 state copied | 0.674 | 3 | 3.3278 | 3.2779 | 852 +0.0015 |
| cj6840s3 | the 2.99 state copied | 0.684 | 3 | 3.4302 | 3.2486 | **853 +5.3e-6**, 794 +3.1e-5 |
| cj6840s4 | the 2.99 state copied | 0.684 | 4 | 3.4302 | 3.2523 | 853 +0.00026 |
| cj6840s5 | the 2.99 state copied | 0.684 | 5 | 3.4302 | 3.3537 | none within the screen |
| cj6900s6 | the 2.99 state copied | 0.69 | 6 | 3.4914 | 3.3384 | 853 +0.00026 |
| cj7000s3 | the 2.99 state copied | 0.70 | 3 | 3.7031 | 3.7031 | 793 +3.8e-5 |
| cd6700s2 | the 2.99 state copied | 0.67 | 2 | 3.2867 | 3.1999 | 852 +0.0030 |
| cd6800s6 | the 2.99 state copied | 0.68 | 6 | 3.3894 | 3.3894 | 793 +1.9e-5 |
| f26790s2 | the round 20 state copied | 0.679 | 2 | 3.1724 | 3.1724 | no builds |
| f36730s2 | the round 20 state copied | 0.673 | 2 | 3.1339 | 3.1339 | no builds |
| f36730s3 | the round 20 state copied | 0.673 | 3 | 3.1339 | 3.1339 | no builds |
| f26790s3 | the round 20 state copied | 0.679 | 3 | 3.1724 | 3.1724 | no builds |
| f56730s2 | the cd6800s5 state of round 20 copied | 0.673 | 2 | 3.2702 | 3.2702 | no builds |
| cj6740s4 | the 2.99 state copied | 0.674 | 4 | 3.3278 | 3.3278 | the old rows again |

- Four seeds found a state that we had already. Seed 6 at f = 0.69 ends at 3.3384, the state of seed 3 of round 20. Seed 2 at f = 0.674 ends at 3.1346 and seed 3 at f = 0.684 ends at 3.2486. Those are the losses of the same round 20 state (variant d) copied to f = 0.674 and 0.684. Seed 5 at f = 0.684 ends at 3.3537, the state of seed 2 of round 20.
- The copies of the round 20 states at the f of 793 and 794 (0.673 and 0.679) did not move with seeds 2 and 3. Seed 4 at f = 0.674 did not move either.
- We copied six states of round 20 to the side fractions of the rows near them. Four are the variants a to d of the state of seed 3 at f = 0.69. The other two are the states of seed 5 at f = 0.68 and of seed 2 at f = 0.684. The nearest build is 794 at 1.0e-5 above the bar, from variant d copied to f = 0.679.
- All 176 builds of the round end above the bar, or on it. The first queue made 170 of them. Three builds of 852 give our own 852 of round 20 again.
- The third agent copied the state of seed 3 at f = 0.684 to eight rows. Every copy had the loss of a copy that the first queue had made, so we dropped its hops and builds.

### 11.2 A chain of local kicks without fq certifies 793

In round 20 the invent lane kicked the near builds of stair-c locally, before their first fq pass. That took 6e-5 to 7e-5 of side off them. We ran `invent_rest.py --modes lkick` for 300 s without fq on the family builds of our three nearest rows. Then the fq quench of `zone_corner.py` ran on the best file of each.

| n | family build | fq build | lkick, no fq | lkick, then fq | bar |
|---|---|---|---|---|---|
| 793 | 28.672864931 | 28.672775590 | 28.672760397 | 28.672760176 | 28.672756154 |
| 794 | 28.684154387 | 28.683980587 | 28.683980261 | 28.683980257 | 28.683970359 |
| 853 | 29.707240020 | 29.706725569 | 29.706732785 | 29.706724551 | 29.706720216 |

- One lkick run takes about as much off a family build as fq does: 1.0e-4 on 793, 1.7e-4 on 794 and 5.1e-4 on 853.
- After the kick, fq takes 2.2e-7 off 793, 4e-9 off 794 and 8.2e-6 off 853. On 853 that is 1.0e-6 under its fq build, and 4.3e-6 above the bar.
- **On 793 the next lkick run keeps going.** Each run starts from the best file of the run before it, with a new seed. The chain below took 793 from 4.2e-6 above the bar to 6.1e-6 of side below it. On 794 and 853 the second run found 4.5e-8 and 1.3e-9, so their chains end there.

| run | seed | start | best side after the run | side taken |
|---|---|---|---|---|
| 1 | 21 | the family build, 28.672864931 | 28.672760397 | 1.0e-4 |
| 2 | 22 | the best of run 1 | 28.672758286 | 2.1e-6 |
| 3 | 23 | the best of run 2 | 28.672756204 | 2.1e-6 |
| 4 | 25 | the best of run 3 | **28.672754384** (under the bar) | 1.8e-6 |
| 5 | 27 | the best of run 4 | 28.672753367 | 1.0e-6 |
| 6 | 29 | a file of run 5 (28.672753473) | 28.672750324 | 3.1e-6 |
| 7 to 11 | 40 to 44 | the best so far | 28.672750100 | 2.2e-7 in all |

- Two runs from the same start find different steps. From the best file of seed 25, seed 27 took 1.0e-6 and seed 28 took 3.5e-6. From the best file of seed 23, seed 25 took 1.8e-6 and seed 26 found nothing.
- The chain ends at a floor near 28.6727501. Four more runs from there found 5e-9 or nothing. A walker of 600 s (`--walk 2e-6`, small steps up allowed) found nothing. A chain of lkick runs from the quenched file found nothing in 3 runs.
- The fq quench of the end of the chain took 4.7e-9. It certifies at 0.018199210438143876, 5.287e-07 under the round 19 file and 2.150e-07 under the lowest other take (the k123 793 of round 21).
- `tools/twoshort/chainlk.sh` runs such a chain: one run of 300 s from the best file so far, with the next seed, until three runs in a row find nothing.
- Other near rows did the same, but they end higher. The second 793 layout (the state of seed 3 at f = 0.70, far zones of 36 and 36) ends at 28.672756117 after four runs. The 793 near row of round 20 has the corner cd6800s4 and far zones of 36 and 36. Six runs took its family build from 28.672967868 to 28.672756151, past its fq build at 28.672769876. Both end 6e-6 above our 793. On 794 the chains end at 28.683980217 and 28.684005946, which is 9.9e-6 and 3.6e-5 above the bar.
- The `seg` move of `invent_rest.py` slides row and column segments of the plain rest beside the arms. It found nothing that lkick does not find: on 793 it ends where lkick ends (28.672756204), on 794 it finds nothing and on 853 it finds 7.7e-8.

### 11.3 Kicks with fq on the fq builds are dry

We ran `midm_scan.py` kicks (kick and lkick, sigma 0.04, with fq) on the fq builds. They found nothing in 12 tries on 794, 7 on 853, and 9 on the quenched lkick file of 793. Every try ends at the start side or above. One lkick run with fq on the fq build of 853 found 1.3e-7 in 5 tries. These are the same results as the scans on 853 and 912 in round 20. So we kick the family build without fq, and quench once at the end.

### 11.4 What the next round should run

1. **An lkick chain on each new near row.** Run it on the family build, before any fq. On 793 it went 2.5e-5 under the fq build of the same layout and certified. Stop a chain after three runs with no find. Run two chains from each good start: two seeds from one file find different steps.
2. **New states, not new seeds on old copies.** Four of the nine seeds of this round landed on states that we had. The copies at the f of 793 and 794 do not move. A new state needs a new start: another class, or a staircase at a new f.
3. **Stop these.** fq kicks of fq builds (28 tries, no find). Seeds 5 and up on the copies at f = 0.684 to 0.70. The `seg` move on these layouts. Copies of a state whose loss matches a copy that we have.

## 12. Round 22 (2026-11-13)

Final snapshot at 15:27 UTC: 4 n remain below every frozen round 21 take and every other live round 22 take. Their gain is 5.654988546e-04 against round 20 and 5.616709966e-07 over the other takes.

| n | certified side | gain against round 20 | gain over the other takes |
|---|---|---|---|
| 793 | 28.672696657748 | 2.112948810e-06 | 1.046291054e-08 |
| 796 | 28.705900224601 | 5.097316735e-04 | 1.038438824e-08 |
| 851 | 29.676485106249 | 2.455274475e-05 | 3.268994409e-09 |
| 912 | 30.693948722767 | 2.910148757e-05 | 5.375547034e-07 |

The source and licence of each row are in `take-twoshort-r22/take.tsv` in the scratch directory. Each retained file passed floatsafe at 2.2e-11 after a boxE fq quench from a certified input.

### 12.1 Raw chains on fresh layouts

The retained layouts start from other lanes' full packings. Local kicks run without fq. Each leg starts from the best raw file, and fq runs on a separate copy.

The two 851 branches start at 29.676485140443. Seed 323 reaches 29.676485118132. Seed 324 reaches 29.676485111660 and certifies after fq. On 793, three runs from 28.672696662499 are dry in 85 tries.

The record holds 62 completed kick scans, 1187 tries and 46 builds. The [result table](../results/twoshort-r22-2026-11-13.tsv) records each run. For `stair`, `hop` and `weak`, start and best are corner losses in squares. For builds and kicks they are sides.

### 12.2 New corner starts

New staircases use f = 0.6730, 0.6948 and 0.7067. Each gets class 6, 4, 1 and 3 hops. Separate runs test the 96-square corner. These builds add no row to this lane's take.

Small kicks on the f = 0.7067 staircase give no gain in 106 tries. Standard hops lower its loss from 4.1182 to 3.6127. Small kicks from the settled states also produce no qualifying packing. At f = 0.6730, temperature 0.05 ends at 3.8537 after 84 hops, matching temperature 0.01.

The intake screens 10 imported bases across the 48 target n. It produces 0 generator rows and 0 builds.

### 12.3 Controls and guards

- The certificate control rejects the frozen 793 as a tie. It accepts that file when its winning round 21 lane is omitted.
- The 8 by 8 staircase control recovers loss 2.467489068, matching the documented 2.4675.
- A table overwrite initially hid 34 standard-hop counts. The repaired screen keeps all 35 counts. Each new table checks that no standard count is lost.
- The geometry control matches two 974 files at distance 2.17e-9. Moving one square by 1e-4 gives distance 1e-4 and fails the match.

On 974, 7 dry scans record 118 tries. Numerical handoff copies now share one queue budget. An input already below the live bar bypasses this filter.

The [round 22 tools](../tools/twoshort/) hold the queue, raw branches, corner experiments, source checks and audit. Raw near files carry source metadata and an uncertified flag. The collector publishes them before a chain finishes. Completed libraries are copied back and hash-checked before their boxE copies are removed.

The final rsync completed. The extra full remote manifest failed because its output path was wrong. Cleanup removed boxE scratch before that extra check. Local validation checked 2,843 archived files and rechecked 18 earlier library hash proofs.

### 12.4 Next

1. Kick fresh whole layouts first, then branch from raw finds. The first 912 scan takes off 1.62e-5 of side. The two 851 seeds find different lower points.
2. Test joint row offsets and column heights before another plain-staircase sweep. Section 9 records the deep state's 0.47 row shift. New f and count starts here add no take.
3. Check geometry at the originating lane before sending a new version. The 974 copies consume repeated scans at one state. Keep direct raw legs separate from copied handoffs.

## 13. Round 23 (2026-11-13)

Final snapshot at 2026-11-13T18:33:32Z: 1 n remain below every frozen round 22 take and every other live round 23 take.
The gain is 1.85693448509e-05 against round 21 and 1.85693448509e-05 beyond the other takes.

| n | certified side | gain against round 21 | gain beyond the other takes |
|---|---|---|---|
| 969 | 31.618993680670 | 1.856934485e-05 | 1.856934485e-05 |

Each retained file passed floatsafe at 2.2e-11 after a boxE fq quench from a certified input.
The source records are in `take-twoshort-r23/take.tsv` in the scratch directory.

### 13.1 Raw kicks and handoffs

The lane completed 60 kick scans with 908 tries, 28 design screens and 127 full builds.
The [result table](../results/twoshort-r23-2026-11-13.tsv) records the measurements.
Runs used three boxE processes with one common deadline at 18:30 UTC.

The first raw kick on a fresh forensics 969 removes 0.000578033 of side in 15 tries.
Its first quench certifies a gain of 1.856934485e-5 against round 21 and the other takes at that time.
Both rectangle donors match their original packings exactly.
Their source records name our own designs.
A late fresh forensics 799 removes 0.001586312 of side in 13 tries.
Its completed quench ties the harvest result from our raw file, so it does not count here.
Five exact geometry matches resolve its source through a border, a rectangle composition and a k123 join.
The public source records name the areebbb and kmmmvs public notebooks under Apache 2.0.

A carried round 22 raw 793 certifies before invent supersedes it.
Two raw branches remove another 4.58e-8 and 4.44e-8 of side.
The later 427 branch is dry in 23 tries.
Four byte-equality checks trace the input through a reader step and a family return to our own 793.

The closest direct module builds receive raw kicks before fq.
The 911 kick removes 1.253e-6 of side.
Invent then certifies a lower descendant of that raw file.
The classfill 852 probe removes 0.001859 of side but remains 0.000983 above the bar.
The classfill 912 and 854 probes are dry.

### 13.2 Joint column heights and row offsets

The joint tests try 144 altered starts at f = 0.6730, 0.6948 and 0.7067. 109 settle.
Each changes upright column heights and offsets of whole tilted rows together.
The control reconstructs the known corner and recovers loss 2.9914105035.
An overlapping copy has gap -1.0 and fails.

The lowest losses are 4.55790, 3.77493 and 3.93629.
The f = 0.6948 state builds 852 at 0.002844 of side above the bar.
None of these transfers gives a qualifying row.

### 13.3 Queue and source checks

The design queue now keeps each full module and stack specification.
The old key kept only n and corner.
On j0016, the corrected key keeps ten specifications instead of three.
The extra 915 far-zone builds remain 0.002553 above the bar.

Fresh imported designs use prediction slack 0.012.
The earlier 0.006 screen would reject the measured winning prediction of 0.007921 from the corners lane.
Individual builds stop after 120 seconds.
Later build batches stop after six minutes and save `unstarted.json`.
Two cancelled calls were 1:44 and 0:39 old.
Their pipelines had run for more than eight minutes, which caused the initial timing mistake.

A foreign pickle containing tuples stopped the collector.
The repaired importer keeps readable dictionary entries and skips unsupported entries.
Its control keeps one valid entry and rejects two unsupported entries.
Source lookup reads `.json` and `.csv.json` sidecars and rectangle part records.

Raw module builds initially waited behind polished copies.
The audit promoted the closest original builds for 911, 973 and 976.
Future queues need that priority from the first handoff.
Numerical copies share a geometry check, while direct raw legs keep their own runs.
The geometry control accepts distance 2.17e-9 and rejects a square moved by 1e-4.
The final audit re-certifies 31 completed quenches and finds no unpublished qualifying row.
The certificate control rejects the frozen 793 tie and accepts it when that reference is omitted.

### 13.4 Next

1. Kick fresh whole layouts before polished copies. The 799 and 969 scans remove 0.001586312 and 0.000578033 of side.
2. Put original module builds first when they arrive. The promoted 911 raw file feeds a lower invent result.
3. Resume the saved new design specifications by predicted fit and completed build history.
   Keep the two-minute call limit and the six-minute batch limit.
4. Preserve immutable source records for every raw branch. The 793 chain needed four byte-equality checks.
5. Stop unchanged joint transfers. They settle altered corners but produce no qualifying row.

The final archive holds 28 verified library copies. 286 unstarted jobs remain in `work/pending-final.json`.
All 2217 remote files and one symlink match the final manifest.
The remote and local manifest hashes match.
Cleanup removes the lane scratch after those checks and preserves `squares-base`.

## 14. Round 24 (2026-11-13)

Snapshot at 2026-11-13T22:18:17Z: 2 n beat their allowed reference and the other live takes in their ancestry group.
The gain is 4.36591736763e-07 against the candidate and 4.2825302482e-07 beyond the other takes.

| n | certified side | gain against the reference |
|---|---|---|
| 800 | 28.770036361119 | 1.397929794e-08 |
| 973 | 31.689103700380 | 4.226124388e-07 |

Every retained file passed floatsafe at 2.2e-11 after a boxE fq quench from a certified input.
Per-n source and licence records stay in `take-twoshort-r24/take.tsv` in the scratch directory.

### 14.1 Measurements

The lane records 113 kick scans with 1421 tries, 191 full builds and 41 library screens.
It completes 72 quenches.
The [result table](../results/twoshort-r24-2026-11-13.tsv) lists the measurements.
Three boxE workers share one search and quench deadline at 22:15 UTC.
The main handoff gives seed-free rows on 20 held counts the round 22 reference.
Other rows use the round 23 candidate.
Every retained licence cell states whether a Samanyu seed is in its ancestry.

The first saved module specification for 973 removes 0.000092743936 of side in 13 tries.
Its first raw continuation is dry in 12 tries.
The complete specification control rebuilds side 31.689196449175988 exactly.
Its recorded modules reach our own staircase and taper designs through 18 source records.

Fresh forensics 800 certifies during the round.
Its source reaches new round 24 layouts of 980, 639 and 918.
A recorded ancestry walk accepts those versions and refuses the excluded old 639 interior.
The source and licence cells preserve the public per-n chains.

Late module builds also reach 911 with a candidate gain of 2.709e-9.
The final 911 score ties a newer live take within 2.24e-13, so it stays out.
Its ancestry proof preserves 28 source records.

The licensed 847 start from the k123 CC0 chain gets nine raw tries without a gain.
The remote source copy matches the local mirror by SHA-256.

Joint column and row tests stay closed.
This round adds no joint tests.

### 14.2 Intake and source controls

Each named module handoff now has its own key, including the library, table and module IDs.
The control finds 13 distinct ID sets with 166 modules behind one current library file.
The old digest key keeps one set in that control.
Immutable library snapshots are shared between requests.

Certification now runs once per intake cycle and checks only the new stage files.
The former loop rechecked the accumulated stage folder for every new quench and delayed fresh work.
Files without source proof now stop before the metric.
The control accepts certified 973 and refuses an unproved 974 with invalid coordinate text.

Source lookup follows pointer records and checks immutable reader snapshots against their recorded hashes.
A changed live parent of a 914 reader return fails that check.
Its saved donor copy has the expected hash and supplies the frozen source record.
The parser preserves a 270,000-character source control that the default CSV limit refuses.
Source caches preserve exact lookup results.

The deadline control stops a 30-second child with return code 124 after 1.23 seconds.
The geometry guard keeps full states and compares against 57 completed starts from round 23.
Near files carry their source records before a later quench can qualify.

### 14.3 Next

1. Build new module families before copies of known floors. The saved 973 specification gains 4.226e-7 at its first certification.
2. Kick fresh whole layouts with recorded ancestry. The new 800 chain qualifies after the count-only screen first refuses it.
3. Resume saved full specifications by current fit and completed build history.
   The archive keeps 205 pending jobs and 371 specifications in 11 partial batches.
4. Keep named ID sets, batch certification and immutable source records from the first intake. Their controls expose skipped work and stale parents.
5. Leave unchanged joint transfers closed. Round 23 settled 109 altered starts and found no qualifying row.

The final copy verifies 2629 files, 25 symlinks and 30 earlier library archives.
The lane removes its boxE scratch after verification and keeps `squares-base`.
All lane workers and the collector have exited.

## 15. Round 25 (2026-11-13 and 14)

The final take retains 1 counts.
Its gain is 0.000144488904209 against the source-admitted base and 9.10700796553e-07 beyond the other live takes.
The [measurement table](../results/twoshort-r25-2026-11-14.tsv) records 71 kick scans, 1471 tries and 57 builds.
The lane completed 7 library screens and 49 quenches on two boxE slots.

The first saved 975 build crossed its base by 6.4434e-9 of score.
Its raw kick removed 2.438388e-6 of side in 18 tries.
Invent then held the same floor within 1.6e-14 of score, so this lane withdrew 975.
The 968 kick removed 2.3975e-5 of side in nine tries and completed its quench.
The 918 transplant lost 1.3387e-5 of side and its continuation was dry in 15 tries.
It remained above the proved round 24 reference.
Four 974 family starts were dry in 44 tries.
Unchanged joint row and column transfers stayed closed.

### Source and intake checks

Source evidence is cached by hash and donor version.
The checker selects one provenance-registry row, which avoids unrelated source histories.
Its control accepts the selected own row and rejects the selected unlicensed row.
A classfill input hash and its selected producer row close the frozen 918 tree.
Reader snapshot 6851644d preserves the old 911 parent when its live file changes.
New metadata can admit a refused file and later source changes can revoke that admission.
File-byte pins and selected source-record pins use separate hash checks.
Their control accepts unchanged evidence and rejects changed bytes or metadata.
Overlapping copies fail the numerical control, while the known 973 packing passes.

New library requests keep their named modules and admitted partners.
The pair control preserves all three original 973 module and lens pairs exactly.
Family screens retain the original 48 counts and add fresh hosts, shells and matching side fractions.
Each build batch has a six-minute limit and each build call has a two-minute limit.
A queue control promotes one family alongside raw layouts and blocks replayed aliases.

The collector stalled during module cleanup after its 01:29 checkpoint.
It restarted at 02:10, and collecting commands now flush output and exit directly.
The final archive verifies 3275 files and 19 symlinks.
It preserves 103 pending jobs and 82 saved specifications.
The lane removes its boxE scratch after the verified copy and preserves squares-base.
The [round 25 tools](../tools/twoshort/r25/) hold the worker, source checks and collection code.

## 16. Round 26 (2026-11-14)

The final take holds 2 counts: 415, 459.
Its gain is 5.56157e-05 against the round 25 b base and 3.025e-09 beyond the other live round 26 takes.
The [measurement table](../results/twoshort-r26-2026-11-14.tsv) records 135 kick runs with 4483 tries.
Each run is 180 s of `invent_rest.py` lkick on boxE.
Two boxE slots ran from 13:02 to 17:03 UTC.
A quench followed every kick that ended within 7e-4 of side of the bar.
Two agents of this lane died during the round, at about 12:50 and 13:24 UTC.
Their collector and boxE workers kept running, and the third agent adopted them at 13:31 UTC.

| n | gain against the base | gain beyond the live takes | input |
|---|---|---|---|
| 415 | 2.271e-09 | 2.271e-09 | forensics |
| 459 | 5.561e-05 | 7.545e-10 | harvest |

### 16.1 What moved

The lkick pays on layouts that are new and that no kick lane has touched yet.
By source lane the kicks moved as follows (runs, tries, runs that moved, best side removed):

| source lane | runs | tries | moved | best side removed |
|---|---|---|---|---|
| forensics | 38 | 939 | 27 | 0.00097 |
| k123 | 17 | 1243 | 12 | 0.00067 |
| harvest | 22 | 658 | 13 | 0.00023 |
| modules | 20 | 353 | 13 | 0.00012 |
| midm | 7 | 186 | 3 | 3.3e-05 |
| stair-c | 8 | 114 | 4 | 3.1e-05 |
| classfill | 9 | 226 | 7 | 1.4e-05 |
| quench | 2 | 37 | 1 | 8.9e-08 |
| border | 1 | 97 | 1 | 1.4e-08 |
| invent | 8 | 562 | 0 | 0 |
| rebuild | 1 | 42 | 0 | 0 |
| stair | 2 | 26 | 0 | 0 |

A raw k123 join of 328 lost 6.7e-4 of side over two legs and certified at 6.03e-4 of score.
Another lane then went lower from our near file, so 328 left the take.
A forensics rectangle composition of 926 started 9.45e-4 of side above the bar.
One kick removed 9.7e-4 of side in 11 tries, and it certified at 1.75e-6.
The quench lane then quenched our file 8.3e-8 lower, so 926 also left the take as a parent.
The 459 row is a kick of the certified harvest 459.
Most of its gain is harvest's, and the kick adds 7.5e-10 of score below the backlog kick of the same file.
Invent near files are dry for this tool, because invent makes them with the same lkick.
Eight such kicks with 562 tries moved nothing.
The one module family screen of the round (117 module IDs) built nothing in 6 minutes.

### 16.2 Ancestry

Our own walk refused good inputs in four ways.
Each now has a narrow resolver with controls.

1. An invent start file has its record in the lane's `work/jobs.json` and a content-addressed ancestry file.
   The resolver accepts it only when the id and the input hash match.
   It refuses the same bytes at another path and a file with one changed coordinate.
2. A public notebook output that the harvest lane downloaded is credited by the harvest start record of the same file.
   A harvest row that names the same notebook and member also credits it.
   A member with no record and a fake notebook stay refused.
3. A rectangle composition record has parts but no top-level source cell, and a modules build record has a list of modules.
   The walk now builds that cell from the parts or the modules and walks them.
   Parts or modules without a licence stay refused.
4. A raw or quenched file of our own kick, in the local mirror of boxE, is credited by the job of the same tag, seed and n.
   That job's input proof must be admitted with an unchanged snapshot.
   The same bytes under `/tmp`, under a fake tag or with a wrong n stay refused.

A second walker gates every row: `quench_walk.py` of the quench lane.
It resolves a held reference without a round the way the assembler does, it refuses gone records, and it applies the prvsiyan share rule.
It refused 932 although our walk passed it.
The 933 donor of that join names the held 813 without a round.
That reference resolves to the round 21 813, whose modules reach the Samanyu-dev seed 503.
It also refused 415 and 501 for a gone kmmmvs record in a classfill closure.
Classfill re-traced that closure at 15:13 UTC, and 415 came back.
The gate runs at certification, on the take every cycle and on each input in a background walker.

Two faults of ours cost a row for an hour.
Our stage records named boxE paths of the raw and quenched files.
`quench_walk.py` reads a path that contains `harvest-<n>-<hash>-s725/<n>-best.csv` as a scratch file that is gone.
So it refused every quench of a harvest input, 459 included.
The records now name the local mirror files, and 459 certified at 16:21 UTC.
The same fix showed that 499, 646 and 818 start from harvest files whose prvsiyan best-of-1105 share is below 0.55.
They stay out under rule b.
Our intake had admitted 16 harvest starts without that rule, and ten were below 0.55.
The collector now refuses such a job before it exports a near file.
We withdrew 104 near files of those kicks and of the midm kicks built on them.

### 16.3 Queue

The queue changed by measured yield during the round.
Module family screens no longer jump the queue.
Near copies of one design wait at a lower priority after the first two of each lane and count.
A start at the same side as two dry kicks of its count is skipped.
Forensics and k123 starts keep the head of the queue up to 5e-3 of side above the bar.
A leg that still removes more than 1e-6 of side gets one more leg.
A collector cycle took 16 to 19 minutes at 15:00 UTC.
It re-walked every job and every deferred file, and it ran one `grep` per bare file name over a 57 MB index.
After the fixes a cycle takes about 5 minutes.

### 16.4 Next

1. Kick fresh forensics rectangles and raw k123 joins first.
   Forensics kicks moved in 27 of 38 runs and removed up to 9.7e-4 of side (926).
   k123 kicks moved in 12 of 17 runs and removed up to 6.7e-4 (328).
   Both certified rows this round.
2. Apply the prvsiyan share rule (`quench_walk.py` `PRV_MIN` 0.55) at intake, before a job is queued.
   Ten of 16 harvest starts were below it.
   Their kicks and the midm and quench kicks built on them took 21 of 135 runs, about 15% of the kick time.
3. Name only local, immutable files in every stage record and take row, and snapshot each input with its record at intake.
   boxE paths in our records cost 459 an hour.
   A rewrite of the forensics `near/926-rect.csv` at 15:15 UTC made our own walk refuse the follows of our 926.
4. Hand each certified row to the soft and quench lanes at once, and kick their follows of our rows.
   Within an hour soft took our 365 3.43e-5 lower and quench took our 926 8.3e-8 lower.
   Our intake refused the backlog follow of the soft 365, because `forensics_policy.classify_text` gives "unknown" on its source cell.
5. Keep invent near files and module family screens out of the queue.
   Eight invent kicks with 562 tries moved nothing, and the family screen built nothing.

The [round 26 tools](../tools/twoshort/r26/) hold the collector, the worker, both ancestry gates and the queue rules.

## 17. Rounds 27 and 28 (2026-11-14 and 15)

The agents of both rounds died before they wrote a report.
Their collectors and boxE workers ran on to the deadline, so the `STATE.txt` of each take dir is the record.

Round 27 ran 95 kicks with 2445 tries, and 48 of them moved.
Its take ended empty.
Its best row was 866, which certified 1.82e-4 of score below bar27.
The backlog lane then certified the same layout 7.5e-8 lower, so 866 left the take.

Round 28 holds 4 counts.
Each row is an lkick chain on a fresh forensics rectangle, then one fq quench of the certified raw best.

| n | gain against bar28 | input |
|---|---|---|
| 457 | 4.404e-06 | forensics rectangle |
| 501 | 2.520e-06 | forensics rectangle |
| 697 | 8.783e-05 | forensics rectangle |
| 737 | 1.462e-10 | forensics rectangle |

Round 28 ran 167 kicks with 3208 tries, and 85 of them moved.
The [round 28 table](../results/twoshort-r28-2026-11-15.tsv) lists every kick.
By source lane the kicks moved as follows (runs, tries, runs that moved, best side removed):

| source lane | runs | tries | moved | best side removed |
|---|---|---|---|---|
| forensics | 118 | 2613 | 57 | 2.3e-03 |
| modules | 34 | 383 | 21 | 1.3e-05 |
| stair-c | 12 | 160 | 6 | 4.9e-06 |
| quench | 1 | 24 | 1 | 1.6e-07 |
| harvest | 1 | 13 | 0 | 0 |
| rebuild | 1 | 15 | 0 | 0 |

Round 28 also ran an A/B test of the kick step size.
Three in four first passes used the wide steps `--sigs 0.01,0.02,0.04`, and the rest kept the default steps.
On forensics inputs the wide steps moved 34 of 61 runs, and the default steps moved 23 of 57.
The 697 row came from a wide first leg that removed 2.3e-3 of side.

A clean stage record made the round 28 rows count.
The old record named our intake proof.
Its closure reached `take-readers-r22/work/follow.json` and the gone files that it names.
`quench_walk.py` refused 697 for that reason alone.
The new record names only a byte snapshot of the input, with the input's own record beside it.

## 18. Round 29 (2026-11-15)

Round 29 ran the round 28 collector and boxE workers again.
`tools/twoshort/r29/setup29.py` writes every round 29 tool from its round 28 copy, so each rule change below is one edit there.

Round 29 holds 3 counts for 6.649e-05 of score against bar29.

| n | gain against bar29 | gain beyond the other r29 takes | input | kick |
|---|---|---|---|---|
| 504 | 2.847e-05 | 7.716e-06 | the backlog take row of 08:41 | one 900 s midm kick |
| 737 | 2.328e-06 | 2.328e-06 | a forensics rectangle | a 180 s lkick |
| 752 | 3.569e-05 | 1.018e-06 | the backlog take row of 09:24 | the second 900 s midm leg |

Each row then got one fq quench of its certified raw best.

Two more rows certified and then left the take, because another lane took the same layout lower.
Our first 504 row went 1.9e-9 deeper in the backlog lane's fq quench. A second midm kick of 504 then beat that row.
Our 412 row went 1.7e-10 deeper in the harvest lane's fq quench.
The gain stays in the round 29 takes in both cases, but in another lane's row.

### The midm kick of fresh rows

A fresh row of another lane, or a forensics rectangle at the bar side, now gets one 900 s `midm_scan.py --modes lkick,kick` kick.
The 180 s `invent_rest.py` lkick stays for the inputs above the bar.
In round 28, nine such lkick kicks of rectangles within 1e-8 of the bar moved nothing.
A midm kick that removes more than 1e-6 of side gets more legs of the same kind, up to seed 1028.

Round 29 ran 97 kicks in total.
By tool the kicks moved as follows:

| tool | runs | tries | moved | best side removed |
|---|---|---|---|---|
| invent_rest lkick 180 s | 77 | 1863 | 50 | 1.4e-03 |
| midm_scan lkick,kick 900 s | 19 | 7353 | 7 | 3.9e-04 |
| invent_rest lkick 900 s | 1 | 63 | 0 | 0.0e+00 |

By input lane:

| lane | runs | tries | moved | best side removed |
|---|---|---|---|---|
| forensics | 70 | 2015 | 42 | 1.4e-03 |
| backlog | 13 | 5955 | 6 | 3.9e-04 |
| k123 | 9 | 338 | 7 | 6.5e-06 |
| harvest | 3 | 195 | 1 | 1.5e-05 |
| held27 seed rows | 2 | 776 | 1 | 1.1e-09 |

The midm kicks gave 504 and 752.
The 180 s lkick chains gave 737 and 412.

### Withdrawn and gated inputs

At 08:36 the forensics lane withdrew 185 near files by sha256, because a recorded public-first ancestor fails the source check.
We removed 38 pending jobs built on them and stopped one running kick.
`unqueue29.py` and the collector now drop an input whose sha256 is in a WITHDRAW line.

The quench lane listed 55 held rows that came from the Samanyu-dev seed and that no lane had touched.
We claimed 10 of them.
`quench_walk.py` refused 4 (549, 754, 758, 874), because a public-first ancestor shares 1.000 of the prvsiyan 1105 row.
Two 900 s midm kicks from the raw seed rows did not move: 414 (615 tries) and 556 (161 tries, 4.9e-11 of score).
The quench lane then certified 556 after one fq quench.
So a seed row needs an fq quench before the midm kick.

### Gate fixes

- The quench lane's `held27` start files name their root as the relative path `gather/round27-2026-11-15b.csv`. `admit29.py` now visits that path.
- A live r29 near file that its lane rewrote under a pinned chain now counts the same as a rewritten r29 take csv. The 752 leg needed this, and `quench_walk.py` found the leg clean.
- A chain through the areebbb union must name its upstream notebooks in the source cell (`source29.credited_cells`). `clean_record` now appends the upstream names from the input record.
- The source cell names the tool that ran (midm or lkick).

### Traps

- **A STATE line that names a file can refuse it.** `quench_walk.py` reads each lane's `STATE.txt`. A line that names a file and holds a word such as *refused*, *drop* or *out* counts as a lane refusal. QUEUE, START, FINISH or COPY in the line cancels that. Our own note about the 752 gate blocked the 752 leg and its input. We staged the result again under new names. Name no live file next to those words.
- **A final prune can fail the rows built on it.** At about 11:45 the backlog lane moved `504.csv` and `752.csv` to `near/` at its final prune. Its CERT lines that name those files hold *unwalked* and *out at 0.4*, so `quench_walk.py` reads them as refusals. After that the walk refused our 504 and 752, and k123 snapshots also name those paths. Keep a superseded take csv in place until the assembler copies.
- **`quench_walk.py` needs an absolute path.** A relative path reads as a gone file, and `qgate29.py` caches that refusal for 60 minutes under the path text.
- **`pgrep -f` matches the shell that runs it.** A wait loop on `pgrep -f "manage29.py --once"` in an inline command finds its own command line. Match the interpreter path too.

## 19. Round 30 (2026-11-15)

Round 30 ran the round 29 collector and the two boxE workers again, from 12:09 to 17:45 UTC.
`tools/twoshort/r30/setup30.py` writes every round 30 tool from its round 29 copy, so each rule change below is one edit there.
The agent stopped on a usage limit from 13:59 to 15:42. The collector and the workers ran on alone, and they certified 556 and 653 in that time.

Round 30 holds 1 count for 2.016e-07 of score against the bar.
The bar is the lower of `bar30.tsv` and the round 29 b file. That file was sent at 13:31 and it moved only 376 and 503.

| n | gain against the bar | gain beyond the other r30 takes | input | kick |
|---|---|---|---|---|
| 556 | 2.016e-07 | 1.300e-08 | the backlog take row of 13:22 | one 900 s midm kick, then a 180 s lkick |

The row got one fq quench of its certified raw best, then a contact LP polish.

Three more rows certified and then left the take, because another lane took the same layout lower:

| n | our gain | the lower row | how |
|---|---|---|---|
| 594 | 1.847e-07 | backlog, 2.1e-08 lower | one 180 s lkick of our certified file |
| 378 | 1.287e-09 | backlog, 1.12e-05 | a kick of its own start |
| 653 | 4.692e-07 | border, then backlog, 2.2e-09 and 3.8e-09 lower | a contact LP of our raw near file, then a kick of that row |

The gain of 594 and 653 stays in the round 30 takes, in the other lane's row.

The skeptic asked us to post 641 and 694 from our round 29 near files.
finesafe gives 641 at 1.155e-06 under the bar and 694 at 8.68e-06 under it.
But invent already holds 641 3.8e-09 lower, and quench holds 694 1.9e-10 lower. The quench row of 694 starts from our forensics 694 file.
So nothing was left to post.

### What changed

- **LP polish.** After each fq quench the worker runs `methods_lp.py` (420 s cap) on the quenched file. It keeps the result only when finesafe certifies it lower. The positive control scaled the centres of the round 28 b 60 by 1 + 2e-4, and the score went from 0.032976298 to 0.032795559. In the round the LP ran 11 times. Each run took off about 1e-11 of score, at most 4e-11, which is below the 1e-10 rule. Border's LP of our raw 653 file, with no fq first, went 2.2e-9 lower than our fq and LP. So the LP pays on the raw layout, not after the fq.
- **An lkick after a moving midm kick.** The backlog lane took our 594 row 2.1e-8 lower with one 180 s lkick of the certified file. So a 900 s midm kick that moves now runs one 180 s lkick from its best in the same job. It ran 9 times. Only 556 moved, by 2.4e-7 of side.
- **Claims.** Any `claim` or `claims` line of another lane in the handoff log now puts that input behind unclaimed work. The old reader wanted ` claims `, so we queued the backlog 378 row a minute after the rebuild lane claimed it. 9 pending jobs moved back.
- **Queue order by the measured crossing rate.** Fresh take rows run first, because 4 of 9 crossed in rounds 28 and 29. Forensics and k123 files within 1e-4 above the bar come next (7 of 51), then the files 1e-4 to 2e-3 above (2 of 49). Modules, stair, soft and classfill near files come last (0 of 35).
- **Held rows.** Border kicked 13 held rows that no kick line names, and 2 crossed. 791 went 7.5e-5 of side lower in 300 s, and 494 went 1.6e-4 lower in 900 s. At 16:36 we queued 600 s midm kicks of 8 such rows of the round 28 b file (lane `reopen-held28b`, byte snapshots with records in `work/held30`). We took the rows with the largest gap to the board that border had not claimed. Each of 635, 678, 730, 731, 785 and 786 moved 1.2e-9 to 1.4e-9 of side, in 139 to 527 tries. None crossed. 804 and 964 did not start before the search deadline at 17:33.
- **The bar.** `bar30.py` takes the lower of `bar30.tsv` and `gate/cand-round29-1115b/details.csv`.

### Measured

Round 30 ran 106 kicks in total.
By tool the kicks moved as follows:

| tool | runs | tries | moved | best side removed |
|---|---|---|---|---|
| invent_rest lkick 180 s | 83 | 2017 | 51 | 2.0e-03 |
| midm_scan lkick,kick 900 s | 16 | 3935 | 4 | 2.2e-05 |
| midm_scan lkick,kick 600 s | 7 | 2561 | 7 | 4.8e-09 |

By input lane:

| lane | runs | tries | moved | best side removed |
|---|---|---|---|---|
| k123 | 39 | 2087 | 21 | 5.6e-04 |
| forensics | 29 | 385 | 21 | 2.0e-03 |
| backlog | 9 | 620 | 2 | 4.4e-06 |
| classfill | 8 | 214 | 4 | 8.7e-06 |
| modules | 6 | 498 | 5 | 3.6e-05 |
| quench | 6 | 629 | 2 | 2.2e-05 |
| reopen-held28b | 6 | 2321 | 6 | 1.4e-09 |
| harvest | 1 | 1579 | 0 | 0.0e+00 |
| border | 1 | 135 | 0 | 0.0e+00 |
| midm | 1 | 45 | 1 | 1.7e-08 |

### Traps

- **A kick of a fresh row often ends on it.** Six chains ended 3e-9 to 4e-9 of side above the live row. They are the k123 chains of 492, 543, 738, 758 and 975, and our 556. That is the margin that certification adds, so the kick found the same layout. Of the last 12 kicks of fresh take rows, none crossed. Several lanes run the same 900 s kick on each fresh row within minutes.
- **A large gap to the board does not mean slack.** Six held rows moved only 1.2e-9 to 1.4e-9 of side in 600 s. Their sides sit on an exact structure. The gap to the board does not say that a row can move. Pick held rows by their own slack, not by the board gap.
- **The quench walk refuses rows through `take-readers-r22/work/follow.json`.** That file names gone files: a family r22 near file and the harvest r22 799. Every live row whose tree reaches it stays out of our queue: invent 641, midm 412, forensics 640, harvest 376 and stair-c 995. The walk of invent 641 also found a public-first ancestor at a share of 1.000. A lane should walk such a row before it kicks it.
- **A file in `reopen.txt` reaches the collector late.** The 150 s intake checkpoint broke each cycle before it read `work/reopen.txt`. Then a cycle that had already read it queued the same 8 jobs a second time. Queue a hand list with `handq30.py`, and do not put it in `reopen.txt` too.

## 20. Round 31 (2026-11-15 and 16)

Round 31 kicked held rows of the round 30 c file that no lane had kicked in rounds 28 to 31.
It ran from 18:48 to 00:15 UTC, with two boxE workers and a collector on boxA.
The agent stopped on a usage limit at 23:16. A new agent took over the lane at 00:07.
The drivers ran on alone in that time, and they certified 859, 601 and 699.

Round 31 holds 14 counts for 9.966e-06 of score against bar31.
That is 9.966e-06 below the other r31 takes after their final prunes.
The bar is `round31-briefs/bar31.tsv`, the held round 30 c file.

| n | gain against bar31 | how |
|---|---|---|
| 999 | 7.397e-06 | a 900 s midm probe moved 2.34e-4 of side, then a 180 s lkick of our certified row |
| 909 | 1.885e-06 | a 150 s lkick of the held row moved 5.68e-5 of side |
| 465 | 2.032e-07 | a 150 s lkick after a dry midm probe, then one lkick leg |
| 555 | 1.458e-07 | a 150 s lkick of the held row |
| 935 | 1.195e-07 | a 150 s lkick of the held row |
| 699 | 7.016e-08 | a 150 s lkick after a dry midm probe, then one lkick leg |
| 859 | 6.937e-08 | a 150 s lkick of the held row, then one lkick leg |
| 416 | 5.805e-08 | a 150 s lkick after a dry midm probe |
| 603 | 6.760e-09 | a 150 s lkick of the held row, then one lkick leg |
| 601 | 4.073e-09 | a 150 s lkick after a dry midm probe |
| 912 | 3.040e-09 | a 900 s midm probe |
| 634 | 1.917e-09 | a 150 s lkick of the held row |
| 381 | 1.158e-09 | a 150 s lkick after a dry midm probe |
| 341 | 1.045e-10 | a 900 s midm probe |

Each row got one fq quench of its certified raw best. Then border's `finesafe.py` certified it.
601 was the closest call: the backlog follow of our row ended 1.0e-10 above it, and backlog dropped that row at its final prune.
811 certified 7.7e-09 under the bar. The backlog lane then took the same layout 4.2e-07 lower with one 180 s lkick, so its row holds 811.

### What changed

- **The probe.** A 900 s midm kick stops at its probe when no try moves 1e-8 of side. The probe ends after 12 tries or 300 s, but never before 120 s. At 120 s, 936 had made only 4 tries.
- **lkick first.** From 21:26 a held row got a 150 s `invent_rest.py` lkick first, with no midm probe. Up to then, 68 midm probes had moved 2 rows (3%). 26 lkicks of rows that the probe found dry had moved 3 (12%).
- **lkick legs.** An lkick job chains a new leg while a step moves 1e-8 of side, up to 8 legs. A midm job still needs 1e-6.
- **Claims.** A claim of another lane blocks a held row for 60 minutes. Then it stops blocking the row, except for an `invent_rest.py` lkick claim.
- **Queue order.** Rows whose side fraction another held n shares (within 3e-9) go last. Rows at a fraction p/q with q up to 40 also go last. About 20 probes of such rows found nothing.
- **The prune.** The collector's prune moved `811.csv` to `near/` at 22:45. But the backlog 811 row names `take-twoshort-r31/811.csv`, so the assembler walk would refuse that row. This is the round 29 trap again. At 00:08 we put the same bytes back in place. The prune in `manage31.py` now copies to `near/` and keeps the file. `final31.py` is the last prune before the assembler. Its control injected a lower 601 row and an equal 909 row, and it dropped each one.

### Measured

boxE ran 208 kicks, plus 4 controls.
By kind the kicks moved as follows (moved means more than 1e-8 of side):

| kind | runs | tries | moved | best side removed | n that moved |
|---|---|---|---|---|---|
| midm probe, 900 s | 70 | 5484 | 2 | 2.34e-04 | 912, 999 |
| lkick of a held row, 150 s | 76 | 2446 | 7 | 5.68e-05 | 555, 603, 634, 811, 859, 909, 935 |
| lkick after a dry midm probe, 150 s | 45 | 1823 | 5 | 4.02e-06 | 381, 416, 465, 601, 699 |
| lkick leg | 15 | 353 | 4 | 1.61e-06 | 465, 699, 859 (two legs) |
| midm leg | 1 | 9 | 0 | 0 | none |
| lkick of our certified row | 1 | 14 | 1 | 2.51e-07 | 999 |

The workers stopped at the 23:55 search deadline. 18 lkick jobs did not run: 751, 753, 801, 803, 816, 847, 849, 850, 853, 861, 866, 915, 921, 929, 936, 981, 989 and 992. Their midm probes were dry. Their job files are in `take-twoshort-r31/work/boxE31/jobs`.

### Next

- A 150 s lkick of each held row that no lane kicked in rounds 29 to 31. Start with the 18 jobs above. The 150 s lkick moved 12 of 121 held rows, and the 900 s midm probe moved 2 of 70 for 6 times the time.
- An lkick leg from every row that moves 1e-8 of side. 4 of 15 legs moved.
- Leave the rows whose side fraction another n shares, or a p/q fraction with q up to 40, for last. About 20 probes of them found nothing.
- Prune by copy, never by move. Other lanes' rows name our take csv paths.

## 21. Round 32 (2026-11-16)

Round 32 gave a 150 s `invent_rest.py` lkick to held round 31 b rows that no lane had lkicked in rounds 29 to 32.
It ran from 11:25 to the 16:55 search deadline, with two boxE workers and a collector on boxA.
The first agent left only the take dir. The second agent built the queue and the controls, and it stopped on a usage limit at about 12:10.
A third agent took over the running drivers at 12:14 and started no second copy of them.

Round 32 holds 8 counts for 1.046e-06 of score against bar32.
Each row is below every other live r32 take.
The bar is `round32-briefs/bar32.tsv`, the held round 31 b file.

| n | gain against bar32 | how |
|---|---|---|
| 706 | 9.026e-07 | a 150 s lkick of the held row moved 2.40e-5 of side |
| 540 | 5.528e-08 | a 150 s lkick of the held row |
| 875 | 4.705e-08 | a 150 s lkick of the held row |
| 870 | 2.813e-08 | a 150 s lkick of the held row moved 6.4e-7 of side, and its quench took 1.9e-7 more |
| 750 | 8.236e-09 | a 900 s midm kick with no probe moved 2.26e-7 of side |
| 705 | 2.710e-09 | a 150 s lkick of the held row |
| 508 | 1.667e-09 | a 150 s lkick of the held row |
| 999 | 3.411e-10 | a third lkick seed of our round 31 row |

Each row got one fq quench of its raw best. Then border's `finesafe.py` certified it.
Two more rows certified and were then beaten by other lanes.
The quench lane holds 992 1.88e-6 below the bar with one fq of our file, which was 1.08e-7 below it.
On 866 a k123 join, lkicked by the backlog lane, holds 7.8e-5 below the bar, and ours was 8.0e-10 below it.

### What changed

- **Leg start.** A leg starts from the quenched file when the quench ran clean and went lower. The 992 leg 1 had started from the raw best, 7.6e-7 of side above its own quench, and it ended above that quench.
- **Queue tiers.** Tier 0 held the round 31 jobs that never ran. Tier 1 held rows with no lkick line in rounds 29 to 32. Tier 2 held rows whose side fraction another n shares, or a p/q fraction with q up to 40. The 95 rows of tiers 0 to 2 would have run out near 13:45. So `sel32ext.py` added a second seed for each row whose one lkick found nothing. Tier 3a holds rows whose last lkick was in round 29 or 30, and tier 3b rows whose last lkick was in round 31. It also added rows at the 2026-11-09 board (tier 5).
- **Wide kick steps.** From 14:36 a second seed used `--sigs 0.01,0.02,0.04` in place of the default steps. Round 28 measured the wide steps moving 34 of 61 runs, against 23 of 57 for the default steps. Controls: the scaled 793 moved 2.766e-3 of side, and the rigid 730 did not move.
- **900 s kicks with no probe.** From 15:09 both slots ran `midm_scan.py --modes lkick,kick` for 900 s with no probe. The rows were the held rows with the largest board gap that no other lane had claimed. In round 31 border measured 2 rows in 9 such kicks. Controls: the scaled 793 moved 2.729e-3 of side in 60 s, and the rigid 730 moved 1.3e-9.
- **Claims.** Three lanes swept the same kind of row this round (soft, rebuild and us). By 14:30, 133 of the planned rows were claimed by another lane, and the collector skipped each one.

### Measured

boxE ran 172 jobs, plus 7 controls. One more job (a 900 s kick of 997) ended at the search deadline with 16 tries and no find.
By kind the jobs moved as follows (moved means more than 1e-8 of side):

| kind | runs | tries | moved | best side removed | n that moved |
|---|---|---|---|---|---|
| 150 s lkick, extra seed of our r31 row (999) | 2 | 22 | 0 | 6.13e-09 | none |
| 150 s lkick, tier 0 | 9 | 108 | 1 | 2.60e-06 | 992 |
| 150 s lkick, tier 1 | 57 | 1294 | 6 | 2.40e-05 | 508, 540, 705, 706, 870, 875 |
| 150 s lkick, tier 2 | 21 | 529 | 0 | 0.00e+00 | none |
| 150 s lkick, tier 3a | 11 | 262 | 0 | 0.00e+00 | none |
| 150 s lkick, tier 3b | 23 | 728 | 0 | 0.00e+00 | none |
| 150 s lkick, tier 3b, wide steps | 21 | 521 | 0 | 0.00e+00 | none |
| 150 s lkick, tier 5 | 6 | 1739 | 0 | 0.00e+00 | none |
| 60 s control, lkick | 2 | 7 | 1 | 2.77e-03 | 793 |
| 60 s control, lkick, wide steps | 2 | 9 | 1 | 2.77e-03 | 793 |
| 60 s control, midm kick, no probe | 2 | 34 | 1 | 2.73e-03 | 793 |
| 900 s midm kick, no probe, held row with the largest board gap | 13 | 3329 | 1 | 2.26e-07 | 750 |
| leg, 150 s lkick | 9 | 165 | 2 | 4.61e-07 | 992, 992 |

### Next

- Give the first 150 s lkick of each held row to one lane only, or split the rows by n between lanes. Reason: first lkicks of rows that no lane had lkicked moved 7 of 66 (tiers 0 and 1), and 12 of 121 in round 31. But soft, rebuild and twoshort swept the same rows this round, and by 14:30 another lane had claimed 133 of our planned rows.
- Run that first lkick on the rows that change in the round 32 b file, within minutes, where the backlog lane does not claim them. Reason: every lkick that moved this round was the first lkick of the row's current geometry.
- Stop second 150 s lkick seeds of rows where one lkick found nothing. Reason: 0 of 55 moved (tier 3a 11, tier 3b 44), and the wide kick steps did not change that (0 of 21).
- Stop lkicks of rows with a shared or p/q side fraction, and of rows at the board under n 200. Reason: 0 of 21 shared rows moved, and 0 of about 20 in round 31. Also 0 of 6 rows at the board at n 152 to 182 moved in 1739 tries.
- A 900 s midm kick with no probe on a held row with a large board gap is a weak second choice. Reason: 1 of 13 moved (750, 2.26e-7 of side, 8.2e-9 of score), against 2 of 9 for border in round 31.
- Keep the leg start from the quenched file and the prune by copy. Reason: on 992 a leg from the raw best ended above its own quench. Other lanes' rows name our take csv paths, and the quench lane holds 992 on our file.

## 22. Round 33 (2026-11-16 and 17)

Round 33 holds 1 count for 1.462e-05 of score against bar33. The bar is `round33-briefs/bar33.tsv`, the held round 32 a file.
The row is below every other live r33 take.

| n | gain against bar33 | how |
|---|---|---|
| 540 | 1.462e-05 | a 900 s midm kick with no probe of the held row moved 3.40e-4 of side, then one fq loop |

The fq loop ran on the raw best. Then border's `finesafe.py` certified it.
The share test `share31.py` read 0.422 at 1e-2 against a 1105 row that is not our layout.
The start is a held row, so its descendants are ours, and the round 32 table already logs the held 540 at 0.419 as no reason to refuse.

### What we ran

- **First lkicks, n 1 to 399.** The pool was empty. 253 rows have a closed-form side. Each row above the board side had an lkick or a claim of its current bytes in rounds 31 or 32. 298 is a 45-degree lattice row.
- **Follows.** The collector waited 10 minutes after a fresh row of another lane appeared, then took it only if no lane had claimed it. The backlog lane claims each fresh row within seconds, so we ran one follow (292) and stopped it after 28 s. Its claim came before we first saw the row. Since then the claim window starts 30 minutes before that.
- **First lkicks, n 400 to 1000.** The screen left 4 of 601 rows. Other lanes held 911 and 585, so we ran 811 and 442. Both did not move.
- **Shared deep-kick queue.** From 21:48 boxE budget was 8 processes. Each row got one 900 s `midm_scan.py --modes lkick,kick` seed with no probe. The first list (`sel33c.py`) gave 10 rows under 1e-5 of board gap, because border had kicked every row above that. The second list (`sel33d.py`) gave 22 held rows that changed in round 32 and had only probed 900 s kicks since that change. Other lanes held 7 of the 32 rows.
- **Load.** boxE reached load 17.7 with the three legs of 540. From 22:42 the collector started no new kick while the 5-minute load was 13 or more.

### Measured

Moved means more than 1e-8 of side.

| kind | runs | moved |
|---|---|---|
| deep queue, first list (gap under 1e-5) | 8 | 0 (700 and 917 moved 1.9e-9) |
| deep queue, rows changed in round 32 | 15 | 1 (540) |
| legs of the 540 find (150 s, 120 s probe) | 3 | 0 |
| first 150 s lkick of a held row | 2 | 0 |
| follow lkick | 1 | 0 (stopped after 28 s) |

Controls: the scaled 793 moved 2.766e-3 of side under the lkick and under the 900 s kick with no probe. The rigid 730 did not move. The final prune dropped an injected lower 540 row and kept ours without it.

## Files

| file | what it is |
|---|---|
| [`twoshort.py`](../twoshort.py) | `table` (the loss a side allows, by pair), `held` (what a held layout is), `far` (lattice far zones for any arm size), `pay` (the margin table) |
| [`twoshort_corner.py`](../twoshort_corner.py) | `stair`: the staircase corner for any pair |
| [`results/twoshort-margins-2026-11-12.tsv`](../results/twoshort-margins-2026-11-12.tsv) | the margin of every pair of 8 to 11 at every n of the slice |
| [`results/twoshort-far-2026-11-12.tsv`](../results/twoshort-far-2026-11-12.tsv) | the far zones of arms of 8 to 11 by class, lattice and built |
| `<scratch>/bounties-squares/take-twoshort-r17` | the take of round 17: one csv for each n and `take.tsv` |
| [`twoshort_carry.py`](../twoshort_carry.py) | carries one hopped corner of a library to other side fractions and writes each copy as a start state for `zone_corner.py search` |
| [`results/twoshort-r19-2026-11-12.tsv`](../results/twoshort-r19-2026-11-12.tsv) | every build of round 19: n, corner, far zones, predicted side, built side, the bar |
| `<scratch>/bounties-squares/take-twoshort-r19` | the take of round 19: one csv for each n and `take.tsv` |
| [`results/twoshort-r20-2026-11-13.tsv`](../results/twoshort-r20-2026-11-13.tsv) | every build of round 20, in the columns of the round 19 table |
| `<scratch>/bounties-squares/take-twoshort-r20` | the take of round 20: one csv for each n, `take.tsv`, and the near rows in `near/` |
| [`tools/twoshort/chainlk.sh`](../tools/twoshort/chainlk.sh), [`tools/twoshort/pickbest.py`](../tools/twoshort/pickbest.py) | a chain of `invent_rest.py` lkick runs without fq, each from the best file so far (round 21) |
| [`results/twoshort-r21-2026-11-13.tsv`](../results/twoshort-r21-2026-11-13.tsv) | every build of round 21, in the columns of the round 19 table |
| [`results/twoshort-r21-kicks-2026-11-13.tsv`](../results/twoshort-r21-kicks-2026-11-13.tsv) | every kick and quench run of round 21: n, run, tool, seed, tries, start side, best side, the bar |
| `<scratch>/bounties-squares/take-twoshort-r21` | the take of round 21: one csv for each n, `take.tsv`, and the near rows in `near/` |
| [`results/twoshort-r26-2026-11-14.tsv`](../results/twoshort-r26-2026-11-14.tsv) | every kick of round 26: n, run, seed, tries, start side, best side, the bar, side removed, source and licence |
| [`tools/twoshort/r26/`](../tools/twoshort/r26/) | the round 26 collector, boxE worker, both ancestry gates (`admit26.py`, `qgate26.py`) and queue rules |
| `<scratch>/bounties-squares/take-twoshort-r26` | the take of round 26: one csv for each n, `take.tsv`, `STATE.txt`, `report.json`, the near rows in `near/` and the work in `work/` |
| [`results/twoshort-r28-2026-11-15.tsv`](../results/twoshort-r28-2026-11-15.tsv) | every kick of round 28, in the columns of the round 26 table |
| [`results/twoshort-r29-2026-11-15.tsv`](../results/twoshort-r29-2026-11-15.tsv) | every kick of round 29, in the columns of the round 26 table |
| [`tools/twoshort/r29/`](../tools/twoshort/r29/) | the round 29 collector, boxE worker, both ancestry gates and the queue tools, all written by `setup29.py` from round 28 |
| [`results/twoshort-r30-2026-11-15.tsv`](../results/twoshort-r30-2026-11-15.tsv) | every kick of round 30, in the columns of the round 26 table |
| [`tools/twoshort/r30/`](../tools/twoshort/r30/) | the round 30 collector, boxE worker, both ancestry gates and the queue tools, all written by `setup30.py` from round 29 |
| [`results/twoshort-r31-2026-11-16.tsv`](../results/twoshort-r31-2026-11-16.tsv) | every kick of round 31, in the columns of the round 26 table |
| [`tools/twoshort/r31/`](../tools/twoshort/r31/) | the round 31 collector, boxE worker, held-row selection and the final prune |
| [`results/twoshort-r32-2026-11-16.tsv`](../results/twoshort-r32-2026-11-16.tsv) | every kick of round 32, in the columns of the round 26 table, with the kind and tier of each run |
| [`tools/twoshort/r32/`](../tools/twoshort/r32/) | the round 32 collector, boxE worker, held-row selection and its second-seed tiers, the 900 s kick queue and the final prune |
| [`results/twoshort-r33-2026-11-17.tsv`](../results/twoshort-r33-2026-11-17.tsv) | every kick of round 33, in the columns of the round 26 table, with the kind of each run |
| [`tools/twoshort/r33/`](../tools/twoshort/r33/) | the round 33 collector, boxE worker, held-row screens, deep-queue screens, table and final prune |
| [`results/twoshort-r35-2026-11-17.tsv`](../results/twoshort-r35-2026-11-17.tsv) | every 900 s kick of round 35, with its finesafe score, bar35 and outcome |

## Summary

- Arms of 10 and more are dead by the kill line. No pair with an arm of 10 or 11 has a margin above 0.3 squares, and the best build ends 0.0019 of side above held.
- An arm of 9 is alive. `twoshort_corner.py` makes a staircase corner from nothing for any pair of arm sizes. With it we built two 9-arms, and an 8-arm with a 9-arm, at m 28 to 31. 15 n certify for a gain of 2.197e-03, and 13 of them are in the slice (1.992e-03).
- Hops on a settled corner are the lever that gave new sides. They took corners of two 9-arms down by 0.2 to 0.5 squares, and 913, 851 and 976 went lower by 1.4e-4 together. The end of a hop run changes from run to run.
- Other lanes walked and kicked these layouts in the same round. They hold lower rows on 8 of these n, and each row names a corner of this tool.
- No pair reaches the board. At f = 0.64 to 0.76 the staircase corner of two 9-arms has a floor of 3.4 to 3.5 squares. That is about 0.4 more than the trend of the other pairs. At f = 0.63 the hops take it to 3.03, which is the trend, but no row uses that corner at its own side fraction yet. Round 19 measured that this is one state (section 9).
- **Round 19.** 4 n certify for 5.235e-05 against the round 17 file, each below every other take: 793, 794, 853 and 910. The corner near 3.0 is one state that is lowest at f = 0.64 (2.99 squares). `twoshort_carry.py` carries it to the side fraction of a row. There a second seed of hops reaches 3.19 at f = 0.68, which is 0.25 below the floor of round 17. That gave 793, 853 and 794. A second seed on a class-1 corner gave 910.
- **Round 20.** 852 and 794 certify for 3.980e-05 against the round 18 file, and 3.401e-05 over the other takes. They come from seeds 2 and 3 on the 2.99 state copied to f = 0.69. A copy alone, capped hops on the 912 corner and the 908 carry gave nothing. The builds of 912 and 851 end in one layout from many corners.
- **Round 21.** 793 certifies for 5.287e-07 against the round 19 file, and 2.150e-07 under every other take. A chain of `invent_rest.py` lkick runs without fq on its family build went 2.5e-5 under the fq build of the same layout. Seeds on the copies of the 2.99 state landed on known states four times in nine. Six seeds on other copies did not move, and fq kicks of fq builds found nothing.
- **Round 26.** 415 and 459 certify for 5.562e-05 against the round 25 b base, and 3.0e-09 below every other take. Fresh forensics rectangles and k123 joins moved most under the lkick. The soft and quench lanes took our 365 and 926 lower from our own files. boxE paths in our stage records made the second ancestry gate refuse every harvest quench for an hour. With local paths, 459 certified. The prvsiyan share rule now runs before a job is queued (section 16).
- **Rounds 27 and 28.** Both agents died, and their drivers ran on. Round 27 ended empty: the backlog lane certified 866 7.5e-8 below ours. Round 28 holds 457, 501, 697 and 737 for 9.5e-05 against bar28, all lkick chains on fresh forensics rectangles. Wide kick steps moved 34 of 61 forensics runs, against 23 of 57 for the default steps (section 17).
- **Round 29.** 504, 737 and 752 certify for 6.649e-05 against bar29. A 900 s midm kick of a fresh take row gave 504 and 752. A 180 s lkick of a forensics rectangle gave 737. Two held seed rows did not move without an fq quench first. A STATE line that names a file next to *refused* or *drop* makes `quench_walk.py` refuse that file.
- **Round 31.** 14 n certify for 9.966e-06 against bar31, 9.966e-06 below the other takes. 999 and 909 give 93% of it. A 150 s lkick of a held row moved 12 of 121 rows, and a 900 s midm probe moved 2 of 70.
- **Round 32.** 8 n certify for 1.046e-06 against bar32, each below every other take. 706 gives 86% of it. First 150 s lkicks of held rows moved 7 of 66. Second seeds moved 0 of 55, with the default or the wide kick steps. Three lanes swept the same held rows, so the pool of first lkicks ran out by 13:20.
- **Round 33.** 540 certifies for 1.462e-05 against bar33, below every other take. One unprobed 900 s kick of a held row that changed in round 32 moved it, 1 of 15 such rows. Rows under 1e-5 of board gap moved 0 of 8. First lkicks had no pool left in any n, and the backlog lane claims fresh rows within seconds.
- **Round 35.** 809 and 653 certify for 9.862e-07 against bar35, each below every other take. We ran 49 unprobed 900 s midm kicks on 34 rows. 38 kicks found nothing. 11 finds certify, but only 4 of them are more than 1e-10 below the live row. All 4 came from a first seed. The 15 second seeds paid nothing this time. Other lanes later beat our 925 and 807, by kicking our rows again. Kicks of the fresh rows of other lanes (693, 803, 806, 808, 864, 966) gave nothing or 3e-11.
- **Next:** an lkick chain without fq on the family build of every new near row, two seeds from each good start, and fq once at the end. New states need new starts: seeds on the old copies repeat known states.
