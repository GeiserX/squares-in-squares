# Avenue: stair-c (2026-11-12 and 13, rounds 17, 19 and 20)

**Result: 12 n certified below held. The take holds 9 of them at the end, 0.000726 of score below held, and round 17 took 861 and 982 from this lane (0.000161). The follow lanes hold six of the nine lower still, from this lane's corner. The find is a corner of two 9-arms with one square less than a staircase corner. Every row of the lane is at k of 17 to 26, and the half of the slice above k = 26 stays dry.**

**Round 19 (section 6): the take holds 4 n, 804, 870, 931 and 993. It is 0.000544 of score below the round 17 file and 0.000481 below every other take. Plain hops on class 2 and class 3 staircase corners at f = 0.82 gave 803, 804 and 863. A staircase corner built at f = 0.92 gave 811, 870, 931, 993 and 994, the first layouts of this lane above k = 26.**

**Round 20 (section 7): the lane certified 810, 811, 869, 930 and 993. At the end the take holds none of them: the follow lanes went just below each one, mostly with layouts built from this lane's corners. The new corner is a class 4 staircase corner of 148 squares at f = 0.93, cheap at that f only. After one hop run it took 869, 930 and 993 0.0013 to 0.0034 of side under every take.**

The slice is m 28 to 31 and k 17 to 45, 110 n. On 81 of them the held file is behind the board, by 0.0218 of score in all. The side fraction f is 0.76 to 1.0 there. The idea is the design of the [twoshort](twoshort.md) avenue, carried to this slice. A staircase corner is built for each pair of arm sizes and each f. A 9-arm goes where the held layout has arms of 7 or 8.

Words used here: "held" is `gather/round16-2026-11-12a.csv` (22.1664224426, gate dir `gate/cand-round16-1112a`). "The board" is the per-puzzle board of 2026-11-09. The side is `L = m + f` and `k = n - m²`. A stack, an arm, a far zone, a corner, a count class and the loss of a zone are those of the [modules](modules.md) and [twoshort](twoshort.md) avenues. "The generator" is `modules.py queue`: it gives the predicted side of every choice of a corner, two far zones and two stack counts. A "row" is one such choice, and its number is the predicted side less the held side. A "hop run" is `zone_corner.py search` on one corner at a fixed f: it moves squares and keeps a state when the loss falls. A "near layout" is a build that ends less than 0.003 of side above held. The tools are [`stair-c_table.py`](../stair-c_table.py) and [`stair-c_run.py`](../stair-c_run.py). They import `modules.py`, `zone_corner.py`, `twoshort.py` and `twoshort_corner.py` and change none of them.

## 1. Kill line (written 2026-11-12 15:21 UTC, before the first build of the slice)

The twoshort builds ended 0.0001 to 0.0056 of side below their prediction, so a row up to 0.003 above held is worth a build.

**The idea is dead in this slice if, with the staircase corners of an 8-arm with a 9-arm and of two 9-arms at f = 0.80, 0.84 and 0.88 in the library, the generator gives no row within 0.003 of side of held on at least 5 n. It is also dead if the 10 lowest rows are built and none certifies below held.**

Positive control, which can fail: 975 of the twoshort lane, built again from its recipe with this lane's copy of the pipeline. The recipe is the corner `zc9x9-102f6800ah3`, the far zones `z9-46f740` and `z9-19f720`, and 15 and 16 stacks. It must end within 1e-5 of the side the twoshort lane built, 31.714583981.

**The control passed.** The twoshort corner went into the round 16 library with `zone_corner.py merge`. `modules.py job` with the family squeeze then built 975 to 31.714583981, the same side to 1e-9, in 312 s on boxA.

**Outcome: the first clause fired by its letter, and the builds showed that the clause was too tight.** The library then held the 8x9 and 9x9 staircase corners. Three n had a row within 0.003 of held: 863, 982 and 986. The clause asked for five. The second clause did not fire. The first builds certified 861, 863 and 982 below held, and the 861 row was 0.0036 above held. The builds of this slice end 0.0002 to 0.0064 of side below their prediction, so a row up to 0.005 above held is worth a build here. We kept the lane running on that evidence. By the written line the idea was dead, and we say so.

## 2. The loss a side allows, and the corner that would tie

`stair-c_table.py need` gives three numbers for every n of the slice and every pair of arm sizes from 6 to 15. The first is the loss the held side allows, `k_flush - k`. The second is the loss of the cheapest far zone of each arm that the library holds within 0.05 of the held f. The third is their difference: the corner loss that would tie the held side. `stair-c_table.py pairs` compares that number with the library's cheapest corner of the pair, and with a line through the staircase corners of the twoshort lane, `0.55 (c1 + c2) - 6.3 + 1.2 (f - 0.70)`.

A margin is the corner loss that ties less the corner loss on offer, in squares. The table counts the n with a margin above 0.3.

| pair | n with a library corner | best margin, library (n) | n above 0.3, library | best margin, line (n) | n above 0.3, line | of those, n with no library corner |
|---|---|---|---|---|---|---|
| 6x6 | 89 | +0.68 (875) | 4 | +1.93 (875) | 46 | 6 |
| 6x7 | 66 | +1.12 (875) | 12 | +1.85 (875) | 42 | 13 |
| 6x8 | 110 | +1.31 (875) | 25 | +1.76 (875) | 28 | 0 |
| 6x9 | 0 | none | 0 | +1.15 (875) | 12 | 12 |
| 7x7 | 107 | +1.45 (876) | 22 | +2.42 (876) | 80 | 1 |
| 7x8 | 103 | +1.77 (936) | 29 | +2.27 (876) | 71 | 4 |
| 7x9 | 44 | +0.88 (805) | 32 | +1.57 (875) | 46 | 24 |
| 8x8 | 110 | +2.18 (936) | 67 | +2.62 (999) | 82 | 0 |
| 8x9 | 76 | +1.73 (875) | 29 | +1.91 (875) | 64 | 20 |
| 9x9 | 51 | +1.33 (875) | 32 | +1.69 (875) | 76 | 29 |
| 9x10 | 0 | none | 0 | +0.55 (918) | 5 | 5 |
| 10x10 | 26 | +0.43 (918) | 3 | +0.38 (918) | 2 | 0 |
| 11x11 | 0 | none | 0 | +0.46 (982) | 1 | 1 |

Every pair with an arm of 10 or more has at most 5 n above 0.3. The pairs with arms of 12 to 15 have no far zone in the library at these f. So the table sends the work to arms of 7, 8 and 9.

**The table is about 1 square too kind, and we knew why before the builds.** It takes the cheapest far zone and the cheapest corner of any count class. A layout must also match the classes: the counts of the corner and of the two far zones must add up to n. It must fill both walls with no slack too. The generator checks both. It has run on these pairs since round 11, and it has found none of the +1 to +2 margins that the library column shows. So the table says where a corner is missing. Only the generator says whether a layout exists.

The class is the real gap. The library's corners between f = 0.78 and 0.86, lowest loss by count class of arm 1:

| pair | library, by class | classes the library does not hold |
|---|---|---|
| 7x7 | 3.68, 3.25, 3.41, 2.52, 2.57, 3.85, 3.82 | none |
| 7x8 | 2.88, 4.38, 3.96, 3.43, 3.80, 3.78, 3.08 | none |
| 8x8 | 4.56 (1), 3.93 (2), 3.28 (3), 3.91 (4), 4.32 (6) | 0, 5, 7 |
| 8x9 | none | all |
| 9x9 | none between 0.78 and 0.94 | all |

## 3. The staircase corners at the f of this slice

`twoshort_corner.py stair` built each corner. The runs of 7x7, 7x8, 8x8 and of the later 9-arm corners used its `--walls` option. Lowest loss of each count class, in squares. Each entry is the loss, then the class and the count of the corner:

| pair, f | lowest loss by class | the library's lowest loss in that band |
|---|---|---|
| 9x9, 0.76 (7 and 8 stacks only, 12 corners) | 3.78 (4, 103), 3.92 (2, 110), 4.12 (3, 84), 4.19 (1, 91), 4.45 (5, 86), 4.69 (6, 96), 5.08 (7, 97), 5.47 (8, 71), 5.76 (0, 81) | none |
| 9x9, 0.78 (a run of 300 s, 11 corners) | 4.13 (4, 94), 4.15 (2, 110), 4.16 (0, 108), 4.17 (8, 125), 4.34 (1, 91), 4.60 (5, 95), 4.76 (3, 111), 4.99 (6, 96), 5.59 (7, 97) | none |
| 9x9, 0.80 | 4.07 (2, 92), 4.12 (8, 125), 4.12 (1, 109), 4.28 (3, 84), 4.42 (5, 104), 4.47 (4, 121), 4.56 (0, 135), 4.60 (7, 115), 5.61 (6, 96) | none |
| 8x9, 0.78 (the stair-b lane's run) | 3.08 (2, 74), 3.14 (4, 108), 3.16 (3, 107), 3.26 (5, 117), 3.39 (1, 97), 3.83 (6, 78), 3.96 (0, 88), 4.34 (7, 87) | none |
| 8x9, 0.80 | 3.12 (4, 100), 3.12 (3, 83), 3.14 (2, 66), 3.44 (1, 97), 3.64 (0, 88), 3.66 (5, 117), 4.06 (6, 102), 4.49 (7, 87) | none |
| 8x9, 0.84 | 3.41 (2, 106), 3.48 (1, 97), 3.90 (3, 75), 3.90 (5, 109), 3.90 (4, 92), 3.92 (0, 96), 4.05 (7, 79), 4.27 (6, 78) | none |
| 9x9, 0.88 | 4.33 (6, 114), 4.77 (0, 108), 4.82 (8, 89), 5.06 (4, 94), 5.07 (3, 102), 5.09 (5, 104), 5.12 (7, 142), 5.30 (1, 91), 5.35 (2, 83) | none |
| 7x7, 0.78 | 2.33 (6, 69), 2.55 (1, 78), 2.57 (0, 70), 2.82 (2, 58), 2.84 (4, 74), 3.08 (5, 68), 3.57 (3, 87) | 2.52 (class 3) |
| 7x7, 0.82 | 2.55 (0, 84), 2.66 (1, 57), 2.68 (4, 102), 2.93 (5, 68), 2.94 (3, 94), 2.96 (6, 83), 3.15 (2, 58) | 2.52 (class 3) |
| 7x7, 0.86 | 2.72 (4, 102), 2.89 (3, 87), 3.06 (6, 62), 3.17 (5, 47), 3.17 (1, 78), 3.46 (0, 63), 3.53 (2, 51) | not looked up |
| 7x7, 0.88 | 2.67 (4, 81), 3.09 (2, 100), 3.14 (3, 59), 3.22 (5, 75), 3.32 (6, 69), 3.42 (1, 57), 4.27 (0, 56) | none |
| 7x8, 0.82 | 2.42 (1, 78), 2.42 (2, 93), 2.86 (0, 84), 2.89 (3, 59), 2.89 (4, 74), 2.89 (5, 89), 3.36 (6, 55) | 2.88 (class 0) |
| 8x8, 0.78 | 3.02 (0, 88), 3.08 (6, 94), 3.08 (2, 90), 3.14 (7, 87), 3.63 (3, 75), 3.66 (5, 77), 3.93 (1, 105), 3.96 (4, 84) | 3.28 (class 3) |
| 8x8, 0.82 | 3.06 (0, 80), 3.43 (7, 87), 3.49 (3, 67), 3.55 (5, 125), 3.88 (2, 90), 3.96 (1, 97), 4.10 (4, 76), 4.21 (6, 110) | 3.28 (class 3) |
| 8x8, 0.88 | 3.31 (4, 108), 3.73 (5, 101), 3.79 (1, 73), 3.99 (6, 94), 4.06 (7, 103), 4.13 (3, 107), 4.16 (2, 66), 4.52 (0, 96) | none |

Each run settles 40 counts. On boxC a run takes 3 to 6 minutes, and on boxA about twice that.

What the corners say:

- **The staircase loss rises with f.** Two 9-arms lose 3.78 at f = 0.68 and 0.76 (twoshort), 4.07 at 0.80, 4.18 at 0.84 (the stair-b lane's run) and 4.33 at 0.88. An 8-arm with a 9-arm loses 2.72 at 0.68, 3.00 at 0.76, 3.12 at 0.80 and 3.41 at 0.84. Two 8-arms lose 3.02 at 0.78, 3.06 at 0.82 and 3.31 at 0.88. Two 7-arms lose 2.33 at 0.78, 2.55 at 0.82, 2.72 at 0.86 and 2.67 at 0.88. The line of section 2 has a slope of 1.2 per unit of f. The measured slope is about 3.
- **The staircase does not beat the library's best class. It fills the other classes.** For two 7-arms the library's best class loses 2.52 and the staircase's best 2.55 at f = 0.82. But in classes 0, 1, 5 and 6 the staircase loses 2.55 to 2.96 where the library loses 3.25 to 3.85. For a 7-arm with an 8-arm the staircase loses 2.42 in classes 1 and 2, where the library loses 4.38 and 3.96.
- For two 8-arms the staircase brings the three classes that the library does not hold (0, 5 and 7, at 3.06 to 3.55).

## 4. Builds

The chain is that of the twoshort lane. `stair-c_run.py add` runs `zone_corner.py adopt`, `table` and `merge` on the staircase base files. `modules.py queue` then runs on the n of the slice with the new corners as `--need`, and `modules.py job` builds a row with the family squeeze. `modules.py take` certifies each layout with floatsafe at 2.2e-11, below held and below every live take dir.

### 4.1 What the generator gave

The lowest row of each n, before and after the hop runs. The pair of arm sizes is in brackets. A row is listed when it is within 0.006 to 0.012 of held, the slack of the run that made it.

| n | k | held f | lowest row, base corners | lowest row, hopped corners | builds | lowest build less held | result |
|---|---|---|---|---|---|---|---|
| 801 | 17 | 0.7811 | +0.0188 (8x9) | none | 0 |  |  |
| 802 | 18 | 0.7949 | +0.0099 (9x9) | +0.0051 (9x9) | 0 |  |  |
| 803 | 19 | 0.8177 | +0.0019 (8x8) | +0.0013 (8x8) | 3 | -0.000004 (8x8) | certified, 1.524e-07 of score |
| 804 | 20 | 0.8297 | +0.0011 (7x7) | +0.0001 (7x7) | 5 | -0.001305 (7x7) | below held, the corners take is lower |
| 805 | 21 | 0.8434 | +0.0052 (7x7) | +0.0052 (7x7) | 1 | -0.000187 (7x7) | certified, 6.589e-06 of score |
| 858 | 17 | 0.7795 | +0.0117 (9x9) | none | 0 |  |  |
| 859 | 18 | 0.7921 | +0.0075 (8x9) | -0.0005 (9x9) | 1 | -0.000952 (9x9) | certified, 3.248e-05 of score |
| 860 | 19 | 0.8019 | +0.0049 (8x8) | -0.0012 (9x9) | 4 | -0.001516 (9x9) | below held, the family take is lower |
| 861 | 20 | 0.8192 | +0.0036 (9x9) | -0.0067 (9x9) | 9 | -0.008311 (9x9) | certified, 2.833e-04 of score |
| 862 | 21 | 0.8271 | +0.0088 (7x7) | +0.0065 (8x8) | 0 |  |  |
| 863 | 22 | 0.8435 | -0.0009 (8x9) | -0.0009 (8x9) | 6 | -0.001983 (8x9) | below held, the corners take is lower |
| 864 | 23 | 0.8519 | +0.0126 (7x7) | none | 0 |  |  |
| 917 | 17 | 0.7615 | +0.0170 (8x9) | none | 0 |  |  |
| 918 | 18 | 0.7841 | +0.0071 (8x8) | +0.0063 (9x9) | 0 |  |  |
| 919 | 19 | 0.7965 | +0.0035 (9x9) | +0.0035 (9x9) | 5 | +0.001571 (9x9) | above held |
| 920 | 20 | 0.8053 | +0.0038 (8x9) | +0.0002 (9x9) | 3 | -0.001434 (9x9) | certified, 4.728e-05 of score |
| 921 | 21 | 0.8156 | +0.0070 (9x9) | -0.0019 (9x9) | 9 | -0.002538 (9x9) | below held, the readers take is lower |
| 922 | 22 | 0.8272 | +0.0126 (9x9) | -0.0028 (9x9) | 1 | -0.005616 (9x9) | certified, 1.850e-04 of score |
| 923 | 23 | 0.8371 | +0.0086 (8x9) | none | 0 |  |  |
| 924 | 24 | 0.8549 | +0.0034 (7x7) | +0.0006 (7x7) | 3 | +0.000009 (7x7) | above held |
| 925 | 25 | 0.8610 | +0.0153 (7x7) | none | 0 |  |  |
| 978 | 17 | 0.7599 | +0.0001 (9x9) | +0.0051 (9x9) | 4 | -0.000388 (9x9) | below held, the twoshort take is lower |
| 979 | 18 | 0.7665 | +0.0158 (8x9) | none | 0 |  |  |
| 980 | 19 | 0.7841 | +0.0057 (8x8) | +0.0057 (8x8) | 1 | +0.004859 (8x8) | above held |
| 981 | 20 | 0.7950 | +0.0087 (8x8) | +0.0050 (9x9) | 0 |  |  |
| 982 | 21 | 0.8105 | -0.0005 (9x9) | -0.0015 (9x9) | 5 | -0.002022 (9x9) | below held, the readers take is lower |
| 983 | 22 | 0.8163 | +0.0101 (9x9) | +0.0013 (9x9) | 3 | +0.000170 (9x9) | above held |
| 984 | 23 | 0.8275 | +0.0084 (8x9) | -0.0011 (9x9) | 4 | -0.002717 (9x9) | certified, 8.663e-05 of score |
| 985 | 24 | 0.8371 | +0.0116 (8x9) | -0.0011 (9x9) | 1 | -0.002623 (9x9) | certified, 8.358e-05 of score |
| 986 | 25 | 0.8519 | +0.0019 (8x9) | +0.0047 (8x9) | 3 | +0.001393 (8x9) | above held |
| 987 | 26 | 0.8644 | +0.0046 (7x7) | +0.0019 (7x7) | 3 | +0.001018 (7x7) | above held |
| 988 | 27 | 0.8738 | +0.0088 (8x8) | none | 0 |  |  |

What the rows say:

- **The rows stop at k = 26.** The generator ran with a slack of 0.02 on the 9x9 and 8x9 corners of f = 0.80. It gives a row on 26 n: 801 to 804, 858 to 863, 917 to 923 and 978 to 986. No n with k of 27 or more has one. The corners built at f = 0.88 do not change that. Two 8-arms give their best row at +0.0088 (988), two 9-arms none within 0.007, and two 7-arms serve 804, 863, 924 and 987, all of f below 0.87.
- **The class decides, not the loss.** Two 7-arms at f = 0.78 lose 2.33 in class 6, the lowest loss of the lane, and the generator gives no row with them. The 7x7 rows of this slice all come from class 4 (804, 863, 924, 987) and class 5 (805). The 7x8 pair gave no row at all with a slack of 0.006.
- A row moves by 0.002 to 0.003 of side when hops take 0.1 to 0.2 squares off its corner.

### 4.2 Hop runs

A hop run takes 3 to 6 minutes on one core. The loss is in squares at the f of the corner.

The command is `zone_corner.py search BASE.pkl OUT --id ID --moves resume,self,delete,hop --down 1 --minutes 5 --slot 120`. The `delete` move takes one square out of the corner and the hops run on that count too. A corner with one square less is in the class below.

| corner (squares) | f | loss at the start | after the hops | with one square less (squares, class) | n it gave |
|---|---|---|---|---|---|
| 9x9 (109, class 1) | 0.80 | 4.119 | 4.013 | 3.513 (108, class 0) | 861, then 859 and 920 with 108 squares |
| 9x9 (92, class 2) | 0.80 | 4.071 | 4.067 | 3.840 (91, class 1) | 861 again (0.0083 of side below held), 922, 984 and 985, all with 91 squares |
| 9x9 (125, class 8) | 0.80 | 4.117 | 4.117 | 4.152 (124, class 7) | none (919 ends 0.0016 above held, and the 982 row at -0.0015 was not built: the border lane holds 982 lower) |
| 9x9 (104, class 5) | 0.80 | 4.415 | 4.083 | 4.495 (103, class 4) | none (one row, more than 0.005 above held) |
| 9x9 (115, class 7) | 0.80 | 4.602 | 4.602 | 4.596 (114, class 6) | none (the rows of 982 and 919 cannot reach the border and family takes) |
| 9x9 (121, class 4) | 0.80 | 4.467 | 4.467 | 4.214 (120, class 3) | none (one row, more than 0.005 above held) |
| 9x9 (99, class 0) | 0.80 | 4.565 | 4.054 | 4.669 (98, class 8) | none (920, 921 and 983 end 0.0031 to 0.0044 above held) |
| 9x9 (101, class 2) | 0.80 | 4.096 | 4.068 | 4.119 (100, class 1) | none new (861 ends 0.0018 below held, and the take holds it lower) |
| 9x9 (110, class 2) | 0.80 | 4.096 | 4.096 | 4.041 (109, class 1), and 4.944 with two less (108, class 0) | none (one row, more than 0.005 above held) |
| 9x9 (127, class 1) | 0.80 | 4.119 | 4.091 | 3.679 (126, class 0) | none new (921, 984, 861 and 860 end 0.0024, 0.0020, 0.0017 and 0.0015 below held, and the takes hold all four lower) |
| 9x9 (118, class 1) | 0.80 | 4.190 | 4.060 | 3.740 (117, class 0) | none new (921 ends 0.0025 below held, 0.00009 above the readers take, and 860 ends 0.0012 below held) |
| 9x9 (92, class 2), second run, two less | 0.80 | 4.067 | 4.067 | 3.840 again (91), and 4.658 with two less (90, class 0) | none new |
| 9x9 (109, class 1), third run, seed 5 | 0.80 | 4.013 | 4.013 | 3.513 again (108) | none new |
| 9x9 (96, class 6) | 0.78 | 4.994 | 4.391 | not run | none (no row with the hopped corner) |
| 9x9 (96, class 6) | 0.76 | 4.694 | 4.364 | not run | none (978 at +0.0051 with the hopped corner, and at +0.0001 with the corner before the hops) |
| 9x9 (115, class 7), first run with no delete | 0.80 | 4.602 | 4.602 | not run | none |
| 8x9 (114, class 2) | 0.80 | 3.440 | 3.267 | 3.872 (113, class 1) | none (921 and 984 end 0.0016 and 0.0017 above held) |
| 8x9 (113, class 1) | 0.80 | 3.478 | 3.478 | 3.502 (112, class 0) | none (920 ends 0.0008 above held) |
| 8x9 (106, class 2) | 0.84 | 3.412 | 3.408 | 3.570 (105, class 1) | 863 |
| 8x9 (114, class 2) | 0.84 | 3.477 | 3.472 | 4.018 (113, class 1) | none |
| 8x8 (80, class 0) | 0.82 | 3.055 | 2.854 | 3.766 (79, class 7) | 803 |
| 7x7 (102, class 4) | 0.82 | 2.682 | 2.567 | not run | 804 |
| 7x7 (68, class 5) | 0.82 | 2.926 | 2.582 | 3.577 (67, class 4) | none (805 came from the corner before the hops) |
| 7x7 (81, class 4) | 0.88 | 2.671 | 2.568 | 2.758 (80, class 3) | none (924, 863, 804 and 987 end 0.00001 to 0.0010 above held) |

What the hop runs say:

- **One square less is the find of this lane.** It is the rule for one family of corners. The base file of two 9-arms at f = 0.80 holds three class 1 corners of 9 stacks, with 109, 118 and 127 squares. They lose 4.12 to 4.19. Take one square out of each and run hops: the class 0 corners that come out lose 3.51, 3.74 and 3.68. The staircase corner of class 0 loses 4.56. The class 2 corner of 92 squares gives 3.84 in class 1 the same way, against 4.12. The corners lane saw the same on the twoshort corners. The corners of 108 and 91 squares gave every 9x9 row below held except the first 861 and 982.
- **The rule stops there.** The other two class 2 corners (101 and 110 squares) give 4.12 and 4.04 in class 1, which is no gain. Corners of classes 0, 4, 5, 7 and 8 give 4.15 to 4.67 with one square less. Two squares less give 4.66 and 4.94 in class 0, and 4.37 and 4.38 in classes 8 and 7.
- **Three class 0 corners serve the same n.** The corners of 108, 117 and 126 squares give rows on 859, 860, 920, 921, 983 and 984. No corner has the lowest row on all six: the 108 corner has it on 859 and 920, and the 126 corner on 921 and 984. The rows of one n differ by 0.001 to 0.004 of side from corner to corner. So the second and third corner of a class add near layouts, and no new n.
- It does not hold for the other pairs. For 8x9, 8x8 and 7x7 the corner with one square less loses more than the staircase corner of its class, or as much.
- The hops alone take 0.10 to 0.51 squares off half of the corners and nothing off the other half. A second run on the same corner with another seed found nothing more (109, 108 and 91 squares 9x9, 80 squares 8x8).
- **A corner hopped at one f does not serve an n at another f.** The 978 row needs a corner of 96 squares in class 6. The staircase corner built at f = 0.78 gives that row at +0.0014, and the one built at f = 0.76, the f of 978, gives it at +0.0001. Hops at 0.78 take 0.60 squares off the first corner, and the generator then gives no row with it. Hops at 0.76 take 0.33 squares off the second, and the row moves up to +0.0051. The hops trade one length of the corner for the other, and the row needs both. Hops under caps (`--caps 0,0`, then caps 0.01 above the start) made no move at all on that corner. So the staircase corner goes in at the f of the n, and free hops do not help a row that is already near.

### 4.3 Every build

| n | corner | far zones | stacks | predicted less held | built less held | seconds |
|---|---|---|---|---|---|---|
| 803 | `zc8x8-80f8200ah3` | `z8-37f820b.F1`, `862h.F1` | 13, 13 | +0.001320 | -0.000004 | 168 |
| 803 | `zc8x8-80f8200aa` | `z8-37f820b.F1`, `862h.F1` | 13, 13 | +0.001857 | +0.001223 | 206 |
| 803 | `zc9x9-83f8000aa` | `921h13.F2d`, `921h13.F2` | 11, 11 | +0.003159 | +0.002933 | 217 |
| 804 | `zc7x7-102f8200ch4` | `803h.F1`, `862q1.F2` | 11, 11 | +0.000056 | -0.001305 | 21 |
| 804 | `zc7x7-81f8800aa` | `984h.F1`, `984mo16.F2d` | 12, 13 | +0.001385 | +0.000251 | 66 |
| 804 | `zc7x7-81f8800ch14` | `862h13.F1d`, `862h13.F1d` | 12, 13 | +0.001095 | +0.000546 | 53 |
| 804 | `zc7x7-88f8600aa` | `862b14.F2d`, `862h13.F1d` | 12, 12 | +0.001124 | +0.000948 | 90 |
| 804 | `zc7x7-102f8200ab` | `803h.F1`, `862q1.F1d` | 11, 11 | +0.003256 | +0.001051 | 91 |
| 805 | `zc7x7-68f8200ab` | `863h.F1`, `986h13.F1` | 13, 13 | +0.005172 | -0.000187 | 117 |
| 859 | `zc9x9-108f8000ah12` | `z9-51f820.F1`, `921fa15.F1` | 12, 10 | -0.000517 | -0.000952 | 79 |
| 860 | `zc9x9-126f8000bh24` | `860fa16.F2`, `921h13.F2` | 10, 9 | -0.001246 | -0.001516 | 593 |
| 860 | `zc9x9-108f8000ah15` | `860fa16.F2`, `921h13.F2` | 11, 10 | -0.001246 | -0.001466 | 135 |
| 860 | `zc9x9-117f8000dh25` | `983h.F1`, `983h13.F2d` | 11, 11 | -0.000358 | -0.001182 | 329 |
| 860 | `zc9x9-108f8000bh12` | `921mo16.F1d`, `983h.F1` | 11, 12 | +0.000590 | -0.001182 | 102 |
| 861 | `zc9x9-91f8000ah17` | `z9-43f800.F1`, `921mo16.F1` | 14, 11 | -0.006666 | -0.008311 | 75 |
| 861 | `zc9x9-109f8000ah2` | `921h13.F2`, `921h13.F2d` | 11, 10 | +0.001202 | -0.005115 | 79 |
| 861 | `zc9x9-109f8000ah12` | `921h13.F2`, `921h13.F2d` | 11, 10 | +0.001202 | -0.005115 | 70 |
| 861 | `zc9x9-109f8000ba` | `921mo16.F1d`, `921h13.F2` | 11, 10 | +0.003566 | -0.002837 | 233 |
| 861 | `zc9x9-109f8000bk` | `921mo16.F1d`, `921h13.F2` | 11, 10 | +0.003566 | -0.002837 | 70 |
| 861 | `zc9x9-100f8000ch23` | `860fa16.F2`, `921h13.F2` | 10, 12 | -0.001518 | -0.001751 | 53 |
| 861 | `zc9x9-127f8000ah24` | `921h13.F2`, `860fa16.F2` | 10, 9 | -0.000541 | -0.001697 | 36 |
| 861 | `zc8x9-114f8000ch6` | `862h.F1`, `921mo16.F1d` | 11, 11 | +0.003270 | +0.001460 | 141 |
| 861 | `zc8x9-97f7800aa` | `862h.F1`, `860fa16.F2d` | 12, 12 | +0.003956 | +0.001460 | 177 |
| 863 | `zc8x9-106f8400ah5` | `861h.F1`, `921h.F2` | 14, 8 | -0.000885 | -0.001983 | 102 |
| 863 | `zc8x9-106f8400af` | `861h.F1`, `921h.F2` | 14, 8 | -0.000885 | -0.001971 | 121 |
| 863 | `zc7x7-102f8200dh4` | `863h.F1`, `924b14.F1` | 11, 12 | +0.002859 | -0.001653 | 47 |
| 863 | `zc7x7-81f8800ch14` | `863po16.F1`, `863h.F1` | 13, 13 | +0.000204 | +0.000032 | 36 |
| 863 | `zc7x7-88f8600aa` | `863po16.F1`, `863h.F1` | 13, 12 | +0.001485 | +0.000827 | 227 |
| 863 | `zc7x7-81f8800aa` | `924b14.F1`, `863h.F1` | 13, 13 | +0.003263 | +0.001127 | 46 |
| 919 | `zc9x9-124f8000ah16` | `921h.F2`, `983h13.F2d` | 7, 11 | +0.003476 | +0.001571 | 299 |
| 919 | `zc9x9-115f8000aa` | `983h13.F2d`, `983h.F1` | 11, 13 | +0.003476 | +0.002231 | 136 |
| 919 | `zc9x9-115f8000ak` | `983h13.F2d`, `983h.F1` | 11, 13 | +0.003476 | +0.002231 | 90 |
| 919 | `zc9x9-126f8000bh24` | `z9-51f820.F1`, `z9-51f820.F1` | 12, 11 | +0.004290 | +0.003879 | 213 |
| 919 | `zc9x9-108f8000ah15` | `z9-51f820.F1`, `z9-51f820.F1` | 13, 12 | +0.004290 | +0.003932 | 208 |
| 920 | `zc9x9-108f8000ah12` | `z9-51f820.F1`, `921h13.F2` | 13, 11 | +0.000184 | -0.001434 | 210 |
| 920 | `zc8x9-113f8000ah7` | `700so16.F1`, `921mo16.F1d` | 10, 12 | +0.003755 | +0.000817 | 139 |
| 920 | `zc9x9-99f8000ah22` | `921h13.F2d`, `z9-51f820.F1` | 12, 13 | +0.003451 | +0.003212 | 43 |
| 921 | `zc9x9-117f8000dh25` | `z9-43f800.F1`, `921mo16.F1d` | 12, 12 | -0.000610 | -0.002538 | 415 |
| 921 | `zc9x9-108f8000ah15` | `921h13.F2`, `860fa16.F2` | 12, 11 | -0.000308 | -0.002456 | 103 |
| 921 | `zc9x9-117f8000dh25` | `z9-43f820.F1`, `921mo16.F1d` | 12, 12 | -0.000610 | -0.002411 | 353 |
| 921 | `zc9x9-126f8000ah24` | `921mo16.F1`, `z9-43f800.F1` | 11, 12 | -0.001913 | -0.002409 | 268 |
| 921 | `zc9x9-108f8000bh12` | `860fa16.F2`, `983h.F1` | 12, 13 | +0.000040 | -0.002294 | 167 |
| 921 | `zc9x9-126f8000ah24` | `921mo16.F1`, `983h.F1` | 11, 12 | -0.001913 | -0.002158 | 37 |
| 921 | `zc9x9-91f8000ah17` | `860fa16.F2`, `z9-51f820.F1` | 13, 13 | +0.001833 | -0.000267 | 84 |
| 921 | `zc8x9-114f8000ah6` | `700so16.F1`, `860fa16.F2` | 10, 12 | +0.002125 | +0.001613 | 184 |
| 921 | `zc9x9-99f8000ah22` | `921h.F2`, `921mo16.F1d` | 9, 12 | +0.004943 | +0.003054 | 113 |
| 922 | `zc9x9-91f8000ah17` | `z9-43f840.F1`, `z9-43f840.F1d` | 15, 14 | -0.002841 | -0.005616 | 52 |
| 924 | `zc7x7-81f8800ch14` | `924h14.F1`, `924fa12.F2` | 14, 15 | +0.000578 | +0.000009 | 46 |
| 924 | `zc7x7-102f8600aa` | `863h.F1`, `986h13.F1d` | 12, 13 | +0.005083 | +0.001763 | 159 |
| 924 | `zc7x7-81f8800aa` | `924h14.F1`, `924fa12.F2` | 14, 15 | +0.003411 | +0.001792 | 59 |
| 978 | `zc9x9-96f7600aa` | `z9-46f740.F1`, `z9-46f840.F1` | 15, 14 | +0.000090 | -0.000388 | 23 |
| 978 | `zc9x9-96f7600aa` | `z9-28f780.F1`, `z9-46f840.F1` | 17, 14 | +0.000090 | -0.000388 | 27 |
| 978 | `zc9x9-96f7600aa` | `z9-28f760.F1`, `z9-46f840.F1` | 17, 14 | +0.000090 | -0.000388 | 136 |
| 978 | `zc9x9-96f7800aa` | `z9-28f760.F1`, `z9-46f840.F1` | 17, 14 | +0.001351 | -0.000293 | 59 |
| 980 | `zc8x8-80f8200ah3` | `z8-42f800.F1`, `z8-42f800.F1` | 15, 15 | +0.005739 | +0.004859 | 285 |
| 982 | `zc9x9-115f8000aa` | `921mo16.F1`, `983h.F1` | 12, 14 | -0.000454 | -0.002022 | 186 |
| 982 | `zc9x9-115f8000ak` | `921mo16.F1`, `983h.F1` | 12, 14 | -0.000454 | -0.002022 | 56 |
| 982 | `zc9x9-108f8000ch12` | `z9-50f840.F1`, `921mo16.F1` | 14, 12 | +0.000854 | -0.000471 | 165 |
| 982 | `zc8x9-122f7800aa` | `z8-59f800.F1`, `860fa16.F2` | 10, 12 | +0.004695 | +0.000802 | 67 |
| 982 | `zc9x9-126f8000ah24` | `z9-51f820.F1`, `z9-51f820.F1` | 13, 12 | +0.003752 | +0.002763 | 73 |
| 983 | `zc9x9-108f8000ah12` | `z9-42f840.F1`, `z9-43f840.F1` | 15, 14 | +0.001300 | +0.000170 | 410 |
| 983 | `zc9x9-108f8000ah12` | `z9-42f840.F1`, `921h13.F2` | 15, 12 | +0.001300 | +0.000172 | 132 |
| 983 | `zc9x9-99f8000ah22` | `921mo16.F1d`, `z9-42f840.F1` | 13, 15 | +0.004633 | +0.004375 | 89 |
| 984 | `zc9x9-91f8000ah17` | `984mo16.F1d`, `z9-42f840.F1` | 16, 15 | -0.001101 | -0.002717 | 49 |
| 984 | `zc9x9-126f8000dh24` | `984mo16.F1d`, `z9-43f840.F1` | 14, 13 | -0.001084 | -0.001972 | 75 |
| 984 | `zc9x9-108f8000bh12` | `z9-43f840.F1d`, `z9-43f840.F1` | 15, 14 | +0.000699 | -0.001972 | 139 |
| 984 | `zc8x9-114f8000ah6` | `700so16.F1`, `921h13.F2` | 11, 13 | +0.002257 | +0.001721 | 119 |
| 985 | `zc9x9-91f8000ah17` | `921h.F2`, `984h.F2` | 11, 10 | -0.001101 | -0.002623 | 71 |
| 986 | `zc8x9-114f8400af` | `z8-38f860.F1`, `984h16.F2d` | 13, 10 | +0.001889 | +0.001393 | 74 |
| 986 | `zc8x9-114f8000aa` | `z8-38f860.F1`, `984h16.F2d` | 13, 10 | +0.001851 | +0.001424 | 433 |
| 986 | `zc7x7-87f8600ba` | `863h.F1`, `924b14.F1` | 15, 14 | +0.005871 | +0.005375 | 86 |
| 987 | `zc7x7-81f8800ch14` | `924b14.F1d`, `863h.F1` | 15, 15 | +0.001945 | +0.001018 | 85 |
| 987 | `zc7x7-81f8800aa` | `986h13.F1d`, `863h.F1` | 15, 15 | +0.004619 | +0.002732 | 55 |
| 987 | `zc7x7-102f8600aa` | `863h.F1`, `924b14.F1d` | 13, 14 | +0.005304 | +0.002736 | 49 |

What the builds say:

- **A build ends below its row.** Two 9-arms end 0.0002 to 0.0064 of side below the predicted side, 0.0013 in the middle. Two 7-arms end 0.0002 to 0.0054 below, an 8-arm with a 9-arm 0.0004 to 0.0039, and two 8-arms 0.0006 to 0.0013. A row up to 0.003 above the bar is worth a build. A row 0.005 above it is not.
- **38 of the 74 builds end below held, on 14 n.** Two 9-arms give 32 of them.
- **The bar moves while the lane runs.** The follow lanes read this take and its `near/` folder and step from the layouts. At the end the family lane holds 859, 861, 920 and 922 below this take, and the corners lane holds 984 and 985. The source column of their `take.tsv` names the 91-square corner of this lane for all six. Earlier the corners lane took 804 and 863, the border lane 982 and the readers lane 924. Those came from the 804 near layout and from the 861 corner of this lane. The family lane took 860 from the near layout of 921 that this lane handed over at 19:40 UTC. The round keeps the lowest layout each time. [`stair-c_bar.py`](../stair-c_bar.py) prints each row next to the lowest take of its n. That number decides a build, not held.
- **A second far-zone choice ends within 0.0003 of the first.** 921 with the 126 corner ends 0.0022 and 0.0024 below held with two choices, and with the 117 corner 0.0025 and 0.0024. 983 ends 0.00017 above held with both. 978 ends at one side with three.
- **978 ends where the twoshort take stands.** The staircase corner of 96 squares at f = 0.76 gives the row at +0.0001. The build ends at 31.759462876. That is the side of the twoshort layout to 1e-9. 978 is the only n of f below 0.79 that this lane brought below held.

## 5. What the next round should run

1. **The staircase corners at the f of each n, then one square less on the class 1 corners.** At f = 0.80 the step is done for every class. It pays from class 1 to class 0 on all three corners, and from class 2 to class 1 on one. The n of f = 0.76 to 0.79 and 0.82 to 0.84 have no corner built at their f, and 978 shows that the f matters. Run `twoshort_corner.py stair 9 9 F --walls --top 40 --seconds 900` at F = 0.76, 0.78, 0.82 and 0.84 on a quiet box, then `zone_corner.py search --moves self,delete,hop --down 1` for 5 minutes on each class 1 corner with 9 stacks. A run of 300 s settled 11 corners on boxC and none on boxA.
2. **Decide every build by the bar.** `stair-c_bar.py` gives the row less the lowest take. Build a row up to 0.003 above it. This round built 8 layouts with the 117, 126 and 127 corners that ended below held and above the take of their n.
3. **The near layouts need hops that keep both lengths.** 921 with the 117 corner ends 0.00009 above the readers take. 983 ends 0.00017 above held, 924 0.00001 and 863 0.00003. Free hops trade one length for the other and move the row up. The `--caps` option of the search made no move on the 978 corner, with caps at the start lengths and 0.01 above them. Find out why before the next run: the hops return at once with 0 moves.
4. **Above k = 26 the corner is not the missing part.** Staircase corners of 7x7, 8x8, 8x9 and 9x9 at f = 0.88 give no row within 0.008 of held there. Measure the far zones of 7-, 8- and 9-arms at f = 0.86 to 0.95 before any more corner work in that half of the slice.
5. **Drop these.** Two and three squares less (4.37 to 4.94, no gain on four runs). A second seed on a kept corner (no new state on four runs). More class 0 corners at f = 0.80 (they serve the same six n).

## 6. Round 19 (2026-11-12, 20:15 to 22:25 UTC)

Round 19 ran the list of section 5 on the same slice. It used 3 processes: one on boxC and two on boxE. boxA ran no worker.

Every build was decided against the bar. The bar of an n is its lowest side among the round 17 file, the frozen round 17 takes and the live round 19 takes. A result counts when it certifies below the round 17 file and is below every one of those takes.

In this section "held" is `gather/round17-2026-11-12a.csv` (22.1635211736, gate dir `gate/cand-round17-1112a`).

**Result: 9 n certified below the bar during the round, 803, 804, 811, 863, 870, 931, 987, 993 and 994.**

At the end the take holds 4 of them: 804, 870, 931 and 993. It is 0.000544 of score below the round 17 file and 0.000481 below the other takes. The other lanes went below the rest with layouts that start from this lane's. The readers lane took 987 three shells up from the 804. The family lane took 811 one shell down from the 870, by 1.7e-7 of score, and 863 by 5.9e-9. The classfill lane took 994 with the 131-square corner of the 0.92 base file and a far zone of its own sweep, 0.000195 of score lower. The corners lane read the corner out of the 863 of this lane, took one square out of it and certified 862. The family lane stepped one shell down from that 862 and went 0.000031 of score below the 803 of this lane.

The layouts have two sources. 803, 804, 863 and 987 come from plain hops on a class 2 or class 3 staircase corner of two 9-arms at f = 0.82. 811, 870, 931, 993 and 994 come from the staircase corners built at f = 0.92. They are the first layouts of this lane above k = 26.

The step of round 17, one square less on a class 1 corner, pays again in loss. It gives no build below the bar, because its corners serve six n where the follow lanes already stand 0.002 to 0.006 of side below held.

### 6.1 The staircase corners at the f of each n

`twoshort_corner.py stair 9 9 F OUT.pkl --walls --top 40 --step 0.04 --seconds 900` ran at F = 0.76, 0.78, 0.82, 0.84, 0.86 and 0.92. Each run had a whole core. It settled 40 corners in 4 to 5 minutes on boxE and in 6 to 6.5 minutes on boxC.

| f | corners | lowest loss by class (class, squares) |
|---|---|---|
| 0.76 | 40 | 3.78 (4, 103), 3.92 (2, 110), 4.08 (3, 111), 4.13 (1, 127), 4.23 (0, 126), 4.45 (5, 86), 4.50 (8, 116), 4.69 (6, 96), 5.28 (7, 106) |
| 0.78 | 40 | 3.86 (2, 92), 4.00 (4, 103), 4.13 (0, 126), 4.17 (8, 125), 4.27 (5, 86), 4.31 (1, 100), 4.37 (3, 102), 4.99 (6, 96), 5.59 (7, 97) |
| 0.82 | 40 | 3.97 (8, 143), 4.28 (5, 95), 4.31 (7, 115), 4.35 (2, 110), 4.45 (1, 109), 4.57 (0, 126), 4.68 (3, 84), 4.95 (4, 94), 5.58 (6, 96) |
| 0.84 | 40 | 4.18 (8, 125), 4.22 (5, 86), 4.34 (3, 102), 4.37 (0, 117), 4.59 (2, 119), 4.74 (1, 136), 4.89 (6, 114), 5.27 (7, 142), 5.46 (4, 94) |
| 0.86 | 40 | 4.51 (6, 150), 4.53 (0, 99), 4.60 (3, 120), 4.60 (8, 143), 4.69 (5, 86), 5.04 (1, 136), 5.07 (2, 110), 5.10 (7, 115), 5.23 (4, 85) |
| 0.92 | 40 | 4.02 (5, 131), 4.43 (7, 133), 4.44 (4, 121), 4.50 (6, 132), 5.15 (8, 98), 5.28 (2, 83), 5.67 (1, 82), 5.86 (0, 126), 6.04 (3, 93) |

- **The cheapest class changes with f.** It is class 4 at 0.76 and class 2 at 0.78. It is class 8 at 0.82 and 0.84, class 6 at 0.86 and class 5 at 0.92. A base file of one f does not tell which class is cheap at the next f.
- **The loss does not grow evenly with f.** The cheapest corner loses 3.78 squares at 0.76, 4.51 at 0.86 and 4.02 at 0.92.
- **Below f = 0.88 the base files alone give one row under the bar.** It is 803, at 0.0007 under the bar. The row comes from the 110-square corner of 0.82. The generator ran on every class of each base file with slack 0.012. The next rows are 978 at +0.0005 (0.76 base) and +0.0015 (0.78 base), and 982 at +0.0041 (0.82 base). The 0.84 base gives no row within 0.009 of the bar, and the 0.86 base none within 0.010.
- **The 0.92 base gives four rows under the bar.** Section 6.5 has them.

### 6.2 One square less, and plain hops

Each line is one run of `zone_corner.py search` on one corner, 5 to 6 minutes. A run with one square less uses `--moves resume,self,delete,hop --down 1`. A run of plain hops uses `--moves resume,hop --down 0`. The rows are the generator against the bar, with the corner states of that run in the library.

| corner (squares, class, stacks) | f | loss at the start | after the hops | with one square less (squares, class) | rows within 0.012 of the bar, lowest first | builds |
|---|---|---|---|---|---|---|
| 127, class 1, 9 stacks | 0.78 | 4.383 | 3.846 | 3.581 (126, class 0) | 859 +0.0061, 921 +0.0065, 860 +0.0069, 920 +0.0082 | 0 |
| 136, class 1, 9 stacks | 0.78 | 4.387 | 3.921 | 3.676 (135, class 0) | 860 +0.0052, 921 +0.0072 | 0 |
| 118, class 1, 9 stacks | 0.78 | 4.423 | 4.130 | 3.611 (117, class 0) | 859 +0.0042, 921 +0.0046, 860 +0.0049, 984 +0.0058, 983 +0.0060, 920 +0.0063 | 0 |
| 134, class 8, 9 stacks | 0.78 | 4.172 | 4.170 | 4.496 (133, class 7) | none | 0 |
| 125, class 8, 9 stacks | 0.78 | 4.171 | 4.120 | 4.728 (124, class 7) | 858 +0.0083 | 0 |
| 92, class 2, 8 stacks | 0.78 | 3.860 | 3.547 | 4.273 (91, class 1) | none | 0 |
| 127, class 1, 9 stacks | 0.82 | 4.459 | 4.459 | 3.800 (126, class 0) | 860 +0.0032, 921 +0.0038, 984 +0.0051, 983 +0.0054 | 0 |
| 136, class 1, 9 stacks | 0.82 | 4.519 | 4.519 | 4.033 (135, class 0) | none | 0 |
| 118, class 1, 9 stacks | 0.82 | 4.936 | 4.503 | 3.939 (117, class 0) | 860 +0.0004, 921 +0.0012, 984 +0.0069 | 2 |
| 110, class 2, 8 stacks | 0.82 | 4.348 | 4.320 | 4.201 (109, class 1) | 803 +0.0001, 862 +0.0059, 921 +0.0082 | 1 |
| 143, class 8, 9 stacks | 0.82 | 3.966 | 3.965 | 4.870 (142, class 7) | 983 +0.0058 | 0 |
| 110, class 2, 8 stacks | 0.82 | 4.348 | 3.975 | 4.201 (109, class 1) | 803 +0.0010, 923 +0.0056, 862 +0.0059, 921 +0.0082 | 1 |
| 102, class 3, 7 stacks | 0.82 | 4.708 | 4.249 | 4.759 (101, class 2) | 987 +0.0007, 924 +0.0031, 803 +0.0070, 863 +0.0071 | 1 |
| 93, class 3, 7 stacks | 0.82 | 4.708 | 4.127 | 4.125 (92, class 2) | 803 +0.0040, 923 +0.0050, 986 +0.0061, 863 +0.0062, 804 +0.0068, 862 +0.0070 | 0 |
| 102, class 3, 7 stacks | 0.82 | 4.708 | 4.087 | 4.759 (101, class 2) | 804 -0.0005, 863 +0.0037, 924 +0.0048, 803 +0.0054, 923 +0.0064 | 1 |
| 102, class 3, 7 stacks | 0.82 | 4.708 | 4.052 | 4.759 (101, class 2) | 804 +0.0004, 924 +0.0051, 863 +0.0060, 803 +0.0061, 862 +0.0082 | 1 |
| 93, class 3, 7 stacks | 0.82 | 4.708 | 4.087 | 4.125 (92, class 2) | 804 +0.0013, 803 +0.0040, 923 +0.0050, 986 +0.0061, 862 +0.0070 | 1 |
| 102, class 3, 7 stacks | 0.82 | 4.708 | 4.052 | 4.759 (101, class 2) | 804 +0.0021, 803 +0.0061, 924 +0.0072, 863 +0.0073, 862 +0.0082 | 1 |
| 102, class 3, 7 stacks | 0.84 | 4.342 | 4.341 | not run | 863 +0.0060 | 0 |
| 136, class 1, 9 stacks | 0.84 | 4.736 | 4.678 | 4.162 (135, class 0) | none | 0 |
| 120, class 3, 8 stacks | 0.86 | 4.599 | 4.596 | not run | none | 0 |
| 102, class 3, 7 stacks | 0.86 | 4.719 | 4.373 | not run | 863 +0.0071, 804 +0.0080, 862 +0.0082 | 0 |
| 122, class 5, 9 stacks | 0.92 | 4.130 | 3.826 | not run | 931 -0.0042, 994 +0.0006, 870 +0.0009, 993 +0.0012, 930 +0.0014, 811 +0.0018 | 8 |
| 121, class 4, 9 stacks | 0.92 | 4.438 | 4.387 | not run | 930 +0.0037, 992 +0.0046, 869 +0.0047, 929 +0.0069, 993 +0.0071 | 0 |
| 131, class 5, 9 stacks | 0.92 | 4.016 | 3.956 | not run | 931 +0.0020, 870 +0.0036, 993 +0.0038, 869 +0.0041, 930 +0.0051, 811 +0.0060 | 2 |
| 122, class 5, 9 stacks | 0.92 | 4.130 | 3.826 | not run | 870 +0.0009, 993 +0.0012, 930 +0.0014, 931 +0.0014, 869 +0.0022, 811 +0.0033 | 6 |

- **One square less on a class 1 corner with 9 stacks pays at every f.** It gives a class 0 corner. That corner loses 3.58 to 3.68 squares at f = 0.78, 3.80 to 4.03 at 0.82 and 4.16 at 0.84. The staircase corner of class 0 loses 4.13, 4.57 and 4.37 at those f.
- **That step gives no build below the bar.** Its rows are 859, 860, 920, 921, 983 and 984. The lowest are 860 at +0.0004 and 921 at +0.0012, from the 117-square corner of 0.82. Both builds end below held and above the bar: 860 by 0.00020 and 921 by 0.00022.
- **The step does not pay from class 8.** Three runs (143 at 0.82, 134 and 125 at 0.78) give class 7 corners of 4.50 to 4.87. At 0.82 the staircase corner of class 7 loses 4.31.
- **From class 3 and class 2 it pays on one corner of four.** That one is 93 to 92 squares at 0.82. It gives 4.12, and the staircase corner of class 2 loses 4.35. The runs 102 to 101, 110 to 109 and 92 to 91 give no gain.
- **Plain hops pay on class 2 and class 3 corners at f = 0.82.** A second run pays again. The 110-square corner goes from 4.348 to 4.320 and then to 3.975. The 102-square corner goes from 4.708 to 4.249, 4.087 and 4.052 in three runs. The 93-square corner goes to 4.127 and then to 4.087. A fourth run on the 102-square corner gives no gain. Each run starts from the kept states of the run before, with a new seed. Round 17 dropped second seeds on its kept class 0 corners. On these corners the second run is worth its 6 minutes.
- **At f = 0.84 and 0.86 the same hops give no row near the bar.** The 102-square corner at 0.84 stays at 4.34 after 280 s. The 120-square corner at 0.86 goes from 4.599 to 4.596. The 102-square corner at 0.86 goes from 4.719 to 4.373, and its lowest row is 863 at +0.0071.

### 6.3 Builds

Every build of the round. A side is less the round 17 file, and less the lowest of the other takes.

| n | corner | far zones | stacks | predicted less held | built less held | built less the lowest other take |
|---|---|---|---|---|---|---|
| 803 | `zc9x9-110f8151ac21c` | `860fa17.F1d`, `921h13.F2` | 9, 9 | -0.001326 | -0.002285 | +0.000876 |
| 803 | `zc9x9-110f8200bs82c21` | `860fa17.F1d`, `921h13.F2` | 9, 9 | -0.001317 | -0.002285 | +0.000876 |
| 803 | `zc9x9-110f8200ds82c21b` | `860fa17.F1d`, `921h13.F2` | 9, 9 | -0.001317 | -0.002285 | +0.000876 |
| 803 | `zc9x9-110f8148dc803` | `860fa17.F1`, `921h13.F2` | 9, 9 | -0.000681 | -0.001452 | +0.001710 |
| 803 | `zc9x9-110f8158bcws82` | `860fa17.F1`, `921h13.F2` | 9, 9 | -0.000681 | -0.001452 | +0.001710 |
| 803 | `zc9x9-110f8200ar` | `860fa17.F1`, `921h13.F2` | 9, 9 | -0.000681 | -0.001452 | +0.001710 |
| 804 | `zc9x9-93f8200as82c32b` | `921h13.F2`, `983cl17.F2d` | 10, 11 | -0.003028 | -0.004329 | -0.002560 |
| 804 | `zc9x9-102f8200as82c31c` | `982cl17.F2d`, `z9-43f840.F1` | 10, 12 | -0.002254 | -0.004329 | -0.002560 |
| 804 | `zc9x9-102f8200as82c31d` | `982cl17.F2d`, `z9-43f840.F1` | 10, 12 | -0.002254 | -0.004329 | -0.002560 |
| 804 | `zc9x9-102f8267dc31c` | `921h.F2`, `983co17a.F2d` | 7, 10 | -0.001860 | -0.002691 | -0.000922 |
| 804 | `zc9x9-102f8525ac31b` | `921h.F2`, `982cl17.F2d` | 7, 10 | -0.002230 | -0.002685 | -0.000916 |
| 804 | `zc9x9-102f8200as82c31b` | `921h.F2`, `982cl17.F2d` | 7, 10 | -0.002230 | -0.002685 | -0.000916 |
| 804 | `zc7x7-102f8200cold` | `803h.F1`, `862q1.F2` | 11, 11 | +0.000056 | -0.001305 | +0.000464 |
| 811 | `zc9x9-122f9200br` | `931h.F2d`, `811h.F1` | 5, 6 | -0.004913 | -0.006109 | +0.000005 |
| 811 | `zc9x9-122f9200ds92c51` | `931h.F2d`, `811h.F1` | 5, 6 | -0.002922 | -0.005937 | +0.000177 |
| 860 | `zc9x9-126f8000bold` | `860fa16.F2`, `921h13.F2` | 10, 9 | -0.001246 | -0.001516 | +0.000092 |
| 860 | `zc9x9-117f8000ac13` | `z9-43f760.F1`, `860fa16.F2` | 12, 10 | -0.001292 | -0.001466 | +0.000141 |
| 860 | `zc9x9-117f8200as82c13` | `z9-43f760.F1`, `860fa16.F2` | 12, 10 | -0.001164 | -0.001410 | +0.000198 |
| 861 | `zc9x9-91f8000aold` | `z9-43f800.F1`, `860fa17.F1d` | 14, 10 | -0.003841 | -0.005474 | +0.000172 |
| 863 | `zc9x9-102f8411cc31b` | `984h.F2`, `984h.F2` | 8, 8 | -0.002800 | -0.003465 | +0.000000 |
| 863 | `zc9x9-102f8411cc31b` | `984h.F2`, `984h.F2` | 8, 8 | -0.002800 | -0.003465 | +0.000000 |
| 863 | `zc9x9-102f8411ac31c` | `984h.F2`, `921h.F2` | 8, 8 | -0.003109 | -0.003307 | +0.000158 |
| 869 | `zc9x9-122f9200as92c51` | `z9-49f920.F1`, `931h.F2d` | 12, 5 | +0.002182 | +0.000283 | +0.000283 |
| 869 | `zc9x9-122f9200as92c51b` | `z9-49f920.F1`, `931h.F2d` | 12, 5 | +0.002182 | +0.000283 | +0.000283 |
| 870 | `zc9x9-122f9200as92c51` | `931h.F2`, `811h.F1` | 6, 7 | -0.004453 | -0.006059 | -0.006059 |
| 870 | `zc9x9-122f9200br` | `931h.F2`, `931h.F2` | 6, 5 | -0.004657 | -0.005376 | -0.005376 |
| 921 | `zc9x9-117f8127dc13` | `921h13.F2`, `860fa17.F1` | 11, 10 | -0.001693 | -0.002452 | +0.000169 |
| 921 | `zc9x9-117f8200cs82c13` | `z9-43f800.F1`, `860fa17.F1` | 13, 10 | -0.001403 | -0.002405 | +0.000216 |
| 924 | `zc9x9-102f8525bc31b` | `863st17.F2d`, `921h.F2` | 9, 9 | +0.000745 | -0.004202 | -0.000000 |
| 924 | `zc9x9-102f8411ac31c` | `863st17.F2d`, `921h.F2` | 9, 9 | -0.001456 | -0.004138 | +0.000064 |
| 930 | `zc9x9-122f9200as92c51` | `z9-49f920.F1`, `931h.F2` | 13, 6 | +0.001350 | +0.000561 | +0.000561 |
| 931 | `zc9x9-122f9200ds92c51` | `931h.F2d`, `811h.F1` | 7, 8 | -0.004238 | -0.005602 | -0.005602 |
| 931 | `zc9x9-131f9200bs92c52` | `931h.F2d`, `931h.F2d` | 5, 7 | -0.002047 | -0.005431 | -0.005431 |
| 931 | `zc9x9-131f9200ds92c52` | `931h.F2d`, `931h.F2d` | 5, 7 | -0.001595 | -0.005059 | -0.005059 |
| 931 | `zc9x9-122f9200br` | `931h.F2d`, `931h.F2d` | 7, 6 | -0.003328 | -0.004039 | -0.004039 |
| 931 | `zc9x9-131f9200cr` | `931h.F2d`, `931h.F2d` | 5, 7 | -0.002915 | -0.004039 | -0.004039 |
| 978 | `zc9x9-96f7600ar` | `z9-28f760.F1`, `z9-46f840.F1` | 17, 14 | +0.000478 | +0.000000 | +0.000000 |
| 978 | `zc9x9-96f7590bcws78` | `z9-28f760.F1`, `z9-46f840.F1` | 17, 14 | +0.000246 | +0.000095 | +0.000095 |
| 987 | `zc9x9-102f8200ds82c31` | `921h.F2`, `984h10.F2d` | 10, 9 | +0.000686 | -0.000465 | +0.001764 |
| 993 | `zc9x9-122f9200ds92c51b` | `z9-40f950.F1`, `931h.F2d` | 15, 7 | +0.001169 | -0.000066 | -0.000066 |
| 993 | `zc9x9-122f9200as92c51` | `z9-40f950.F1`, `931h.F2d` | 15, 7 | +0.001241 | -0.000066 | -0.000066 |
| 993 | `zc9x9-122f9200ds92c51` | `z9-40f950.F1`, `931h.F2d` | 15, 7 | +0.002370 | -0.000004 | -0.000004 |
| 994 | `zc9x9-122f9200as92c51` | `994mi17.F2`, `811h.F1` | 12, 9 | -0.002171 | -0.004915 | +0.003968 |
| 994 | `zc9x9-122f9200br` | `994mi17.F2d`, `994mi17.F2` | 12, 11 | -0.001455 | -0.002747 | +0.006136 |

- **803** ends at 28.815420113, 0.002285 below held. The first build, with the 110-square corner as the staircase gave it, ended at 28.816253730. The corner after one run of hops gave the lower side. Three more builds with later states of that corner end at the same side to 1e-9.
- **804** ends at 28.825386736, 0.004329 below held. The first build with the 102-square corner ended at 28.827030503. The third hop run on that corner gave a row with other far zones (`982cl17.F2d` and `z9-43f840.F1`, 10 and 12 stacks), and that build ended 0.0016 lower.
- **863** ends at 29.840065197, 0.003465 below held and 0.001353 below the corners take of round 17. The quench took 1.3e-7 more off the side. Its corner is the 102-square corner of the second hop run, carried to the f of 863 by the capped LP of section 6.4. The far zone is `984h.F2` on both arms.
- **987** ended at 31.863976319, 0.000465 below held. Its row was 0.0007 above the bar. It was the first layout of this lane below held at k above 24. It left the take when the readers lane went 0.0017 of side below it.
- **870, 931, 994 and 811** come from one corner, `zc9x9-122f9200br`. It is the 122-square staircase corner of class 5 at f = 0.92, with no hop. 870 ends 0.005376 below held and 931 0.004039. 994 ends 0.002747 below held and 811 0.006109. The far zones are those of held layouts (`931h.F2`, `811h.F1`, `994mi17.F2`).
- **931 and 870 again, and 993,** come from the same corner after 284 s of plain hops. 931 ends at 30.923959290, 0.005602 below held. 870 ends at 29.916971020, 0.006059 below held. 993 ends 0.000066 below held, with the new taper `z9-40f950.F1` on one arm. 994 and 811 with the hopped corner end above the lowest take of their n.
- **924** with the capped 102-square corner ends at 30.850708905. That is the side of the readers layout of 924 to 1e-9, so it is not a result.
- **A build ends below its row, as in round 17.** The builds below held end 0.0002 to 0.0021 below the predicted side.
- **860 and 921 stay just above the bar.** Four builds with the two 117-square corners end 0.00014 to 0.00022 above it. One build of 860 with the kept 126-square corner of round 17 ends 0.00009 above it.
- **978 did not move.** The 96-square corner from the 0.76 base gives the held side again. The corner carried under caps to the f of 978 ends 0.000095 above it. 978 with this corner stays on the dropped list.
- **The fq quench moves a certified layout by 1.3e-7 of side or less.** It found no smaller layout for 803, the last 804, 870, 931, 993 and 994. It took 1.9e-9 off 987, 1.1e-8 off the first 804 and 1.3e-7 off 863. 811 left the take before its quench.

### 6.4 Hops under caps

Round 17 found that `zone_corner.py search --caps` made no move. The cause is in `hops()`: the loop ended as soon as the state fitted under both caps. Caps at the start lengths, or below them, fit at the start, so the run returned with 0 hops. The corners lane changed `search --caps` in this round: the hops now go on under the caps and lower the loss.

This lane used the other path, `zone_corner.py needs` and then `capsearch`. For a choice of an n, `needs` gives the two lengths that the arms leave at the bar's side less 0.0003. `capsearch` carries the corner to that f, runs an LP with the caps as bounds, and then hops on the larger excess.

| n | corner (squares) | f of the n | excess over the caps, before | after | hops | seconds | fits |
|---|---|---|---|---|---|---|---|
| 978 | `zc9x9-96f7800ar` (96) | 0.75896 | +0.00904 | +0.00514 | 23 | 94 | no |
| 860 | `zc9x9-117f8200as82c13` (117) | 0.79999 | +0.01601 | +0.00380 | 79 | 182 | no |
| 921 | `zc9x9-117f8200cs82c13` (117) | 0.81265 | +0.02592 | +0.00421 | 82 | 183 | no |
| 803 | `zc9x9-110f8200ds82c21b` (110) | 0.81512 | +0.00787 | +0.00481 | 89 | 243 | no |
| 862 | `zc9x9-110f8200as82c21b` (110) | 0.82683 | +0.02982 | +0.01522 | 92 | 242 | no |
| 923 | `zc9x9-110f8200as82c21b` (110) | 0.83680 | +0.03619 | +0.03619 | 87 | 244 | no |
| 863 | `zc9x9-102f8200as82c31b` (102) | 0.84112 | +0.01647 | +0.00000 | 87 | 202 | no |
| 924 | `zc9x9-102f8200as82c31b` (102) | 0.85246 | +0.02110 | +0.00000 | 86 | 203 | no |
| 804 | `zc9x9-102f8200as82c31c` (102) | 0.82673 | +0.01360 | +0.00000 | 20 | 47 | no |
| 863 | `zc9x9-102f8200as82c31c` (102) | 0.84112 | +0.01151 | +0.00819 | 17 | 47 | no |
| 924 | `zc9x9-102f8200ds82c31c` (102) | 0.85246 | -0.00089 | -0.00089 | 0 | 1 | yes |
| 803 | `zc9x9-102f8200ds82c31c` (102) | 0.81512 | +0.04882 | +0.04424 | 22 | 48 | no |
| 803 | `zc9x9-110f8200ar` (110) | 0.81475 | +0.01344 | +0.01034 | 60 | 152 | no |
| 803 | `zc9x9-110f8200ar` (110) | 0.81575 | +0.00752 | +0.00349 | 43 | 93 | no |

- **The LP does the step, and the hops after it add nothing.** The corner is the 102-square corner of the second hop run. For 863 the LP brings the excess from 0.0165 to under 0.000005. For 924 it brings it from 0.0211 to under 0.000005. The 200 s of hops after it accept no move. The run does not print FITS, because the test is exact and the LP ends less than 0.000005 over the cap. The state it keeps gives the row all the same.
- **That state gave the 863 of this lane.** Its row went from 0.0037 above the bar to 0.0007 under it. The build ended 0.0014 under the bar.
- **A later state of a corner is not a better start for the LP.** The 102-square corner of the third hop run loses less (4.052 against 4.087). Its capped states give 863 at 29.840223, 0.00016 above the 863 of the take, and 804 0.0016 above the 804 of the take.
- **On the other corners the excess stays above zero.** 860 goes from 0.0160 to 0.0038 and 921 from 0.0259 to 0.0042. 803 goes from 0.0079 to 0.0048 and 862 from 0.0298 to 0.0152. 923 does not move.

### 6.5 The far zones above k = 26

`twoshort.py far C F --hi 6.5 --step 0.02 --refine 9 --build 4` gave the lattice taper far zones of arms of 7, 8 and 9 at f = 0.86, 0.89, 0.92 and 0.95, every class. `TWOSHORT_BEAM=30000` keeps a run under a minute. The table sets them next to the far zones that the library holds within 0.02 of each f.

| arm | f | lowest loss by class: lattice taper / library within 0.02 of f (class) | classes where the taper is 0.15 or more below the library | classes the library does not hold |
|---|---|---|---|---|
| 7 | 0.86 | 3.17 / 3.17 (0), 3.38 / 3.38 (1), 3.28 / 3.28 (2), 3.03 / 2.59 (3), 2.51 / 2.18 (4), 2.72 / 2.72 (5), 2.74 / 2.74 (6) | none | none |
| 7 | 0.89 | 3.08 / 3.04 (0), 3.47 / 3.41 (1), 3.37 / 3.34 (2), 2.95 / 2.93 (3), 2.42 / 2.35 (4), 2.72 / 2.72 (5), 2.94 / 2.85 (6) | none | none |
| 7 | 0.92 | 3.08 / 3.08 (0), 3.37 / 3.32 (1), 3.47 / 3.47 (2), 3.00 / 2.85 (3), 2.42 / 2.42 (4), 2.72 / 2.72 (5), 2.82 / 2.82 (6) | none | none |
| 7 | 0.95 | 3.06 / 2.99 (0), 3.22 / 3.16 (1), 3.31 / 3.24 (2), 2.98 / 2.71 (3), 2.57 / 2.34 (4), 2.81 / 2.74 (5), 3.20 / 2.94 (6) | none | none |
| 8 | 0.86 | 4.01 / 4.01 (0), 3.96 / 3.96 (1), 4.06 / 4.06 (2), 3.54 / 3.54 (3), 3.53 / 3.53 (4), 3.15 / 3.00 (5), 3.28 / 3.28 (6), 3.24 / 3.13 (7) | none | none |
| 8 | 0.89 | 4.06 / 3.95 (0), 3.91 / 3.82 (1), 4.09 / 4.02 (2), 3.67 / 3.76 (3), 3.52 / 2.79 (4), 3.12 / 2.82 (5), 3.54 / 3.40 (6), 3.31 / 3.27 (7) | none | none |
| 8 | 0.92 | 3.92 / 3.80 (0), 3.63 / 3.57 (1), 3.87 / 3.70 (2), 3.78 / 3.73 (3), 3.17 / 2.92 (4), 2.81 / 2.70 (5), 3.63 / 3.41 (6), 3.17 / 3.07 (7) | none | none |
| 8 | 0.95 | 3.74 / 3.67 (0), 3.75 / 3.57 (1), 3.60 / 3.50 (2), 4.13 / 3.79 (3), 3.48 / 3.02 (4), 2.81 / 2.70 (5), 3.77 / 3.41 (6), 3.11 / 3.07 (7) | none | none |
| 9 | 0.86 | 4.06 / 4.06 (0), 4.80 / 4.80 (1), 4.43 / 4.43 (2), 3.88 / 3.88 (3), 4.03 / 4.03 (4), 4.33 / 4.33 (5), 3.79 / 3.79 (6), 3.25 / 3.25 (7), 4.58 / 4.58 (8) | none | none |
| 9 | 0.89 | 3.99 / none (0), 4.58 / none (1), 4.74 / none (2), 4.15 / none (3), 3.73 / none (4), 4.47 / none (5), 3.88 / none (6), 3.31 / none (7), 4.44 / none (8) | none | 0 (3.99), 1 (4.58), 2 (4.74), 3 (4.15), 4 (3.73), 5 (4.47), 6 (3.88), 7 (3.31), 8 (4.44) |
| 9 | 0.92 | 4.14 / none (0), 4.34 / none (1), 5.03 / none (2), 4.44 / none (3), 3.85 / none (4), 4.09 / 3.27 (5), 3.86 / none (6), 3.49 / none (7), 4.28 / none (8) | none | 0 (4.14), 1 (4.34), 2 (5.03), 3 (4.44), 4 (3.85), 6 (3.86), 7 (3.49), 8 (4.28) |
| 9 | 0.95 | 4.30 / none (0), 4.23 / none (1), 4.68 / none (2), 4.56 / none (3), 4.31 / none (4), 3.63 / 3.37 (5), 3.83 / 3.85 (6), 3.65 / 3.52 (7), 4.09 / none (8) | none | 0 (4.30), 1 (4.23), 2 (4.68), 3 (4.56), 4 (4.31), 8 (4.09) |

- **For arms of 7 and 8 the library is at or below the lattice taper in every class at every f.** A new taper gives nothing there. One class of 60 is the exception: the 8-arm of class 3 at f = 0.89, where the taper is 0.09 lower.
- **The library holds few 9-arm far zones above f = 0.88.** It holds none within 0.02 of f = 0.89. It holds one class of nine at 0.92 and three at 0.95. At 0.86 it equals the taper in all nine classes. The round built the 36 tapers of f = 0.89, 0.92, 0.95 and 0.98 into the library (`twoshort.py far 9 F --build 9 --save`). They lose 3.31 to 5.03 squares.

Then `twoshort_corner.py stair 9 9 0.92` gave 40 corners in 6.5 minutes, and the generator ran on the 41 n of k = 27 and more. The library held the 0.86, 0.88 and 0.92 base files and the new far zones.

| n | k | row from the base file | row after hops on the 122-square corner | built, from the base file | built, after the hops |
|---|---|---|---|---|---|
| 870 | 29 | -0.0047 | -0.0045 | -0.005376 | -0.006059 |
| 931 | 31 | -0.0033 | -0.0042 | -0.004039 | -0.005602 |
| 994 | 33 | -0.0008 | -0.0015 | -0.002052 | -0.004220 |
| 811 | 27 | -0.0002 | +0.0018 | -0.001350 | -0.001178 |
| 993 | 32 | +0.0036 | +0.0012 | not built | -0.000066 |
| 930 | 30 | +0.0038 | +0.0014 | not built | +0.000561 |
| 869 | 28 | +0.0041 | +0.0022 | not built | +0.000283 |
| 992 | 31 | +0.0053 | none | not built | not built |
| 929 | 29 | +0.0074 | none | not built | not built |

Every number is a side less the bar at 21:47 UTC, which was the round 17 file for seven of these n. For 811 and 994 another take stood 0.004759 and 0.000695 below that file. The corner of every built row is the 122-square corner of class 5.

- **Above k = 26 the corner was the missing part.** It must be built at the right f. Round 17 built staircase corners at f = 0.88. It found no row within 0.008 of held above k = 26. The corners built at f = 0.92 give four rows under the bar, and all four builds certify. The n of those rows have f = 0.91 to 0.94.
- **The rows under the bar use far zones of held layouts.** The new tapers enter at 993, 869, 992 and 929, 0.0036 to 0.0074 above the bar.

### 6.6 What the next round should run

1. **Staircase corners at every f from 0.88 to 0.98.** Then run the generator on the n of k = 27 and more. One base file at f = 0.92 gave 811, 870, 931 and 994 with no hop. That is 0.000616 of score against the round 17 file. The slice has 41 n of k = 27 and more, and this round had a base file for one f. Run `twoshort_corner.py stair 9 9 F --walls --top 40 --seconds 600` at F = 0.90, 0.94, 0.96 and 0.98, and the same with `stair 8 9` and `stair 8 8`. A run takes 6.5 minutes on one core.
2. **Plain hops on the cheap classes of each of those base files.** 284 s of hops took the 122-square corner at 0.92 from 4.130 to 3.826. That gave 993. It took 931 0.0016 and 870 0.0007 of side lower. 930 and 869 ended 0.0006 and 0.0003 above the bar. A second run of 291 s gave no new state. The 131-square corner went from 4.016 to 3.956, and the 121-square corner from 4.438 to 4.387.
3. **Three hop runs on each class 2 and class 3 corner at f = 0.80 to 0.84.** Then the capped LP at the f of each n. This gave 803, 804 and 863. The follow lanes took 924 and 987 from the 804. The 102-square corner lost 0.66 squares in three runs of 6 minutes. The capped LP took the row of 863 from 0.0037 above the bar to 0.0007 under it.
4. **Build two far-zone choices for a row under the bar.** 804 ended 0.0016 lower with `982cl17.F2d` and `z9-43f840.F1` than with `921h.F2` and `982cl17.F2d`. `stair-c_run.py jobs --per 1` builds one choice for each n.
5. **Make `capsearch` stop when the LP ends within 1e-6 of the caps.** The hops after such an LP took 200 s for each choice and accepted no move.
6. **Drop these.** One square less on class 1 corners in this slice: 7 runs pay in loss, and the 5 builds end 0.00009 to 0.00022 above the bar. One square less from class 8: 3 runs, no gain. Capped hops for 860, 921, 803, 862 and 923: the excess stays 0.004 to 0.015 above zero. Hops at f = 0.84 and 0.86: no row within 0.005 of the bar. 978 with the 96-square corner: two more builds, none below held. The one-less runs at f = 0.76 did not run: their slot went to the corners of f = 0.92.

## 7. Round 20 (2026-11-12 22:36 to 2026-11-13 01:05 UTC)

Round 20 ran the list of section 6.6 on the same slice. It used 3 processes: two on boxE and one on boxC. A harness restart at 22:48 stopped the first agent while it copied the scripts to the boxes. The second agent made the copy again and started the queues at 22:57.

The bar of an n is its lowest side among the round 18 file, the frozen round 19 takes and the live round 20 takes. A result counts when it certifies below the round 18 file and below every one of those takes. In this section "held" is `gather/round18-2026-11-12a.csv` (22.1604820601, gate dir `gate/cand-round18-1112a`).

**Result: 5 n certified below the bar during the round: 810, 811, 869, 930 and 993. At the end the take holds none of them. At 00:55 the polish, readers and classfill lanes held 869, 930 and 993 4e-6 to 3e-5 of side lower, with layouts built from the hopped corner of this lane.**

The best corner of the round is the class 4 staircase corner of 148 squares at f = 0.93 after one hop run. At 00:27 it took 869, 930 and 993 0.0013 to 0.0034 of side under every take. Then the polish and classfill lanes went 7.4e-9 and 1.5e-7 of score below 930 and 993 with that same corner. The base files of f = 0.90 and 0.93 gave 810, 993 and 930 first, with no hop. More hops on the round 19 corner of f = 0.92 gave 869 first.

The control ran first. It used the base file of f = 0.92 of round 19 and the held details of round 18. It gave the rows of round 19 to 1e-4: 870 at -0.004657, 931 at -0.003328 and 811 at -0.000753. So the library, the generator and the copy on the boxes work.

### 7.1 The staircase corners from f = 0.88 to 0.96

`twoshort_corner.py stair 9 9 F --walls --top 40 --step 0.04` ran at seven f. The 0.92 row is the base file of round 19. Each run took 4 to 7 minutes.

| pair, f | corners | lowest loss by class (loss, class, squares) |
|---|---|---|
| 9x9, 0.88 | 40 | 4.26 (8, 134), 4.36 (5, 140), 4.40 (6, 114), 4.85 (7, 106), 5.10 (0, 126), 5.11 (3, 84), 5.14 (1, 109), 5.35 (2, 83), 5.44 (4, 85) |
| 9x9, 0.90 | 40 | 4.17 (5, 131), 4.51 (1, 100), 4.62 (6, 132), 4.79 (4, 85), 4.89 (7, 106), 5.20 (8, 116), 5.22 (2, 101), 5.62 (0, 135), 5.72 (3, 93) |
| 9x9, 0.91 | 40 | 4.11 (5, 149), 4.38 (6, 123), 4.50 (4, 139), 4.53 (7, 106), 4.80 (1, 109), 5.13 (2, 92), 5.18 (8, 125), 5.50 (0, 126), 6.30 (3, 102) |
| 9x9, 0.92 | 40 | 4.02 (5, 131), 4.43 (7, 133), 4.44 (4, 121), 4.50 (6, 132), 5.15 (8, 98), 5.28 (2, 83), 5.67 (1, 82), 5.86 (0, 126), 6.04 (3, 93) |
| 9x9, 0.93 | 40 | 3.78 (5, 131), 4.07 (4, 148), 4.41 (7, 115), 4.42 (6, 141), 5.10 (8, 89), 5.25 (3, 129), 5.36 (0, 81), 5.40 (1, 82), 5.59 (2, 83) |
| 9x9, 0.94 | 40 | 3.77 (5, 131), 4.34 (6, 132), 4.58 (7, 115), 4.70 (8, 98), 4.73 (4, 139), 5.21 (0, 72), 5.49 (3, 120), 5.51 (2, 83), 6.24 (1, 82) |
| 9x9, 0.96 | 40 | 4.12 (3, 147), 4.39 (6, 114), 4.49 (5, 131), 4.73 (7, 97), 4.82 (4, 139), 4.96 (8, 116), 5.53 (1, 82), 5.77 (2, 92), 6.25 (0, 108) |
| 8x9, 0.90 | 40 | 3.89 (2, 130), 3.96 (1, 105), 4.04 (7, 71), 4.06 (6, 78), 4.09 (0, 96), 4.30 (5, 77), 4.47 (3, 91), 4.65 (4, 76) |

- **Class 5 is the cheapest class from f = 0.90 to 0.94.** Its 131-square corner loses 4.17, 4.02, 3.78 and 3.77 at 0.90, 0.92, 0.93 and 0.94.
- **Class 4 has one cheap point, f = 0.93.** There the 148-square corner loses 4.07. Class 4 loses 4.44 at 0.92 and 4.73 at 0.94. That corner gave 930 and 993.
- **Three base files give no row within 0.0065 of the bar.** They are those of f = 0.88 and 0.96 and the 8x9 file. Their lowest rows are 811 at +0.0094, 873 at +0.0067 and 810 at +0.0107.

### 7.2 A build ends 0.0017 to 0.0045 below its row

Round 19 built a row only when it stood at most 0.003 above the bar. The first builds of this round showed that the family squeeze takes much more than that off the predicted side at f = 0.90 to 0.94:

| n | corner | row over the bar | built over the bar | taken off by the build |
|---|---|---|---|---|
| 810 | `zc9x9-131f9000ar` (0.90) | +0.0030 | -0.0015 | 0.0045 |
| 869 | `zc9x9-131f9000ar` (0.90) | +0.0048 | +0.0005 | 0.0043 |
| 993 | `zc9x9-131f9400ar` (0.94) | +0.0037 | +0.0004 | 0.0033 |
| 931 | `zc9x9-131f9400ar` (0.94) | +0.0027 | +0.0002 | 0.0025 |
| 993 | `zc9x9-148f9300ar` (0.93) | +0.0009 | -0.0008 | 0.0017 |
| 930 | `zc9x9-148f9300ar` (0.93) | +0.0024 | -0.0006 | 0.0029 |
| 873 | `zc9x9-141f9600ar` (0.96) | +0.0067 | +0.0030 | 0.0037 |

So the box scripts now build every row up to 0.0065 above the bar, two far-zone choices each (`MAXJ` in `stairf.sh` and `hopx-n.sh`).

### 7.3 Hops

`zone_corner.py search` ran 5 to 7 minutes on one corner at a time. The runs on the 122-square corner of f = 0.92 started from the state that round 19 left (3.826).

| corner (squares, class) | f | loss at the start | after the hops | one square less | rows within 0.008 of the bar, lowest first | result |
|---|---|---|---|---|---|---|
| 122, class 5 | 0.92 | 3.826 | 3.783 (410 s) | 4.384 (121, class 4) | 993 +0.0005, 930 +0.0006, 931 +0.0016, 870 +0.0016, 811 +0.0018, 869 +0.0018 | 869 certified |
| 122, class 5 | 0.92 | 3.783 | 3.783 (two more runs, seeds 2 and 3) | 4.384 | the same rows | no new state |
| 148, class 4 | 0.93 | 4.071 | 3.947 (281 s) | not run | 993 +0.0012, 930 +0.0021, 992 +0.0040, 869 +0.0040 | 869, 930 and 993 certified 0.0013 to 0.0034 of side under every take. 992 at +0.0009 over held, a near file |
| 148, class 4 | 0.93 | 3.947 | 3.947 (a second run, seed 2) | 4.526 (147, class 3) | the same rows | no new state |
| 140, class 5 | 0.93 | 3.899 | 3.728 | not run | 931 +0.0020, 870 +0.0033, 993 +0.0038 | none |
| 131, class 5 | 0.90 | 4.165 | 4.091 | not run | 811 +0.0025, 870 +0.0037, 810 +0.0063 | none |
| 113, class 5 | 0.91 | 4.362 | 4.089 | not run | 811 +0.0004, 870 +0.0041, 930 +0.0045 | 811 at +1.7e-5 of side over the polish 811 |
| 131, class 5 | 0.94 | 3.773 | 3.773 | not run | 931 +0.0027, 994 +0.0027, 993 +0.0038 | no move accepted |
| 122, class 5 | 0.94 | 3.934 | 3.773 | not run | 931 +0.0027, 994 +0.0027, 993 +0.0033 | none |
| 141, class 6 | 0.96 | 4.391 | 4.391 | not run | 873 +0.0067 | none |

The capped LP of round 19 (`caps.sh`) ran once, on the hopped 122-square corner at the f of 869, 930, 929 and 992. The excess stayed at 0.011 to 0.013 after 45 to 49 hops, and its rows (869 +0.0020, 930 +0.0027) are higher than those of the plain hops.

### 7.4 What the follow lanes did with these layouts

The follow lanes went below most rows of this lane within 10 to 50 minutes:

- 810: this lane certified it at 23:05 (5.19e-05). The modules, classfill, invent, polish and readers lanes then went 0.0012 to 0.0022 of side lower with other corners.
- 811: this lane certified it at 23:35, 5.2e-9 of score under the family 811. The polish lane went 1e-6 of side lower.
- 869: this lane certified it at 23:37 (6.03e-06). The modules lane went 0.0012 lower at 23:50 with a corner that the corners lane read out of the round 19 near file `994-1ac70171` of this lane. At 00:27 the hopped 148-square corner of this round took 869 0.0021 of side under the modules 869. At 00:52 the polish lane took it 4e-6 lower with one fq quench of a readers layout two shells down from 993.
- 930 and 993: this lane certified them at 00:13 and 00:19 with the 148-square corner. At 00:27 the hopped corner took them 0.0013 to 0.0014 lower. The polish lane then took 930 7.4e-9 of score lower with one fq quench. The classfill lane took 993 1.5e-7 lower with our corner and a far zone of its own sweep. The readers lane then stepped one shell up from 869 to 930, and from 930 to 993.
- 870: the classfill lane built it at 23:03 with the round 19 corner of this lane and a swept far zone. The build of this round with the corner of 3.783 ended 1.4e-5 of side above it.

The near files and the libraries of this round are in the take dir: `near/` and `work/libs` (`lib-s92d1`, `lib-f93`).

### 7.5 What the next round should run

1. **Hops on the class 4 corners near f = 0.93.** One run of 281 s took the 148-square class 4 corner at 0.93 from 4.071 to 3.947. Its rows gave 869, 930 and 993, 0.0013 to 0.0034 of side under every take, and 992 at +0.0009 over held. A second run from that state found nothing. At f = 0.932 class 4 loses 4.53 (130 squares), so the cheap point is narrow. Build the staircase at f = 0.926 to 0.934 in steps of 0.002, and run hops on each cheap class 4 corner there.
2. **Staircase corners at steps of 0.005 from f = 0.90 to 0.95.** The cheap class 4 point at 0.93 sits between dear ones. Class 4 loses 4.44 at 0.92, 4.35 at 0.925 and 4.73 at 0.94. Steps of 0.01 found it by chance. Each run takes 4 to 7 minutes on one core.
3. **Build every row up to 0.0065 above the bar, with two far-zone choices.** Builds end 0.0017 to 0.0045 below their rows at f = 0.90 to 0.94.
4. **Hand each new corner to the follow lanes as a library at once.** They went below 810, 811, 869, 930 and 993 within 10 to 50 minutes. They used our corner with their own swept zones, kicks or quench.
5. **Drop these.** The staircase at f = 0.88 and 0.96, and two arms of 8 and 9 at 0.90: no row within 0.0065 of the bar. More hops on the 122-square corner at 0.92 from 3.783: two seeds, no new state. Hops on the 131-square corner at 0.94: no move accepted. The capped LP on the 0.92 corner: no fit.

## 8. Round 21 (2026-11-13, 01:03 to 12:20 UTC)

Round 21 ran the list of section 7.5 on the same slice, with 3 processes: two on boxE and one on boxC. The agent died three times. A usage limit stopped it at 01:20, a few minutes after it started the queues. boxA rebooted at 05:36. A lost login stopped the second attempt at 09:55. The queues on the two boxes did not need boxA. They ran to their end at 02:09 and 02:36. Nobody collected their builds until 09:52. The third attempt adopted the two boxE workers that the second one had started, and ran the second leg from 10:03 to 12:10.

The bar of an n is its lowest side among the round 19 file, the frozen round 20 takes and the live round 21 takes. A result counts when it certifies below the round 19 file and below every one of those takes. In this section "held" is `gather/round19-2026-11-12a.csv` (22.1514697138, gate dir `gate/cand-round19-1112a`).

**Result: 3 n certified below the bar: 811, 870 and 931, at 09:52, 2.373e-4 of score below held and 2.366e-4 below every other take at that time. The builds date from 02:13 to 02:18 and sat on boxC until the collect. The follow lanes went just below all three within 4 to 41 minutes, with our files, so the final take is empty.**

The control ran first. On the round 21 box, the base file of f = 0.93 of round 20 gave 14 rows. All 14 are equal to the rows of round 20, to 0.0 of predicted side. So the library, the generator and the copy on the boxes work.

### 8.1 The staircase corners

`twoshort_corner.py stair 9 9 F --walls --top 40 --step 0.04` ran at eleven new f. Each run took 4 to 7 minutes on boxE and 7 to 10 minutes on boxC.

| f | corners | lowest loss by class (class, squares) |
|---|---|---|
| 0.812 | 40 | 3.84 (7, 133), 4.14 (8, 134), 4.31 (5, 95), 4.39 (1, 127), 4.39 (2, 92), 4.54 (0, 126), 4.61 (3, 84), 4.78 (4, 112), 5.85 (6, 123) |
| 0.818 | 40 | 3.96 (8, 143), 4.25 (5, 86), 4.39 (1, 100), 4.50 (7, 142), 4.55 (2, 101), 4.55 (0, 126), 4.70 (3, 84), 4.82 (4, 112), 5.59 (6, 96) |
| 0.822 | 40 | 4.10 (8, 143), 4.20 (5, 104), 4.38 (7, 133), 4.39 (2, 101), 4.45 (3, 102), 4.54 (0, 99), 4.54 (1, 136), 4.70 (4, 94), 5.58 (6, 96) |
| 0.824 | 40 | 4.11 (8, 143), 4.18 (5, 95), 4.45 (1, 91), 4.54 (7, 151), 4.55 (0, 117), 4.56 (2, 119), 4.68 (3, 102), 4.74 (4, 94), 5.57 (6, 87) |
| 0.826 | 40 | 4.16 (5, 95), 4.16 (0, 135), 4.20 (8, 125), 4.44 (3, 102), 4.49 (1, 118), 4.51 (7, 151), 4.66 (2, 101), 4.94 (4, 94), 5.57 (6, 87) |
| 0.830 | 40 | 4.08 (8, 143), 4.16 (5, 86), 4.40 (3, 93), 4.40 (0, 90), 4.59 (1, 127), 4.71 (7, 151), 4.94 (2, 101), 5.00 (4, 94), 5.56 (6, 87) |
| 0.922 | 40 | 4.02 (5, 149), 4.19 (4, 130), 4.43 (7, 124), 4.48 (6, 141), 5.14 (8, 98), 5.15 (2, 83), 5.28 (3, 120), 5.73 (1, 100), 5.86 (0, 126) |
| 0.924 | 40 | 3.82 (5, 122), 4.21 (4, 130), 4.40 (6, 114), 4.42 (7, 106), 5.13 (8, 134), 5.16 (3, 129), 5.33 (2, 101), 5.47 (0, 126), 5.78 (1, 100) |
| 0.926 | 40 | 3.97 (5, 140), 4.38 (4, 130), 4.39 (6, 123), 4.42 (7, 106), 4.92 (1, 100), 5.08 (8, 71), 5.39 (2, 92), 5.62 (0, 126), 6.09 (3, 102) |
| 0.928 | 40 | 3.93 (5, 140), 4.42 (7, 106), 4.43 (4, 139), 4.44 (6, 150), 5.11 (8, 89), 5.19 (3, 129), 5.51 (2, 92), 5.61 (0, 126), 5.87 (1, 91) |
| 0.934 | 40 | 3.66 (5, 131), 4.19 (4, 148), 4.39 (6, 132), 4.41 (7, 106), 4.69 (8, 98), 5.38 (3, 129), 5.70 (2, 83), 5.74 (0, 90), 6.07 (1, 82) |

- **Class 5 is the cheapest class from f = 0.922 to 0.934.** Its lowest corner loses 3.66 to 4.02.
- **Class 4 is not cheap at any of the new f near 0.93.** It loses 4.19 to 4.43 there, against 4.07 at 0.93 in round 20. The cheap class 4 point of round 20 stays alone.
- **At f = 0.826 class 0 has one cheap corner.** The 135-square corner loses 4.16. At 0.812 to 0.83 the lowest class 0 corner loses 4.40 to 4.55.
- **From f = 0.812 to 0.83 class 7 or 8 is the cheapest, except at 0.826.** It loses 3.84 to 4.11. Its rows stand 0.002 to 0.008 above the bar.

### 8.2 Hops

`zone_corner.py search` ran 5 to 10 minutes on one corner at a time, with plain hops. A run from the kept states of an earlier run says so in the table.

| corner (squares, class) | f | loss at the start | after the hops | rows against the bar of the time, lowest first | builds | result |
|---|---|---|---|---|---|---|
| 140, class 5 | 0.926 | 3.966 | 3.785 | 931 +0.0016, 870 +0.0029, 993 +0.0040 | 7 | none |
| 131, class 5 | 0.926 | 3.986 | 3.986, no move | 870 +0.0043, 811 +0.0060 | 2 | none |
| 140, class 5 | 0.928 | 3.933 | 3.760 | 931 +0.0018, 870 +0.0031, 993 +0.0045 | 7 | none |
| 122, class 5 | 0.928 | 3.976 | 3.680 | 931 +0.0002, 994 +0.0016, 870 +0.0016, 811 +0.0054 | 7 | 811, 870 and 931 certified |
| 140, class 5 | 0.934 | 3.833 | 3.656 | 931 +0.0025, 994 +0.0027, 870 +0.0040 | 7 | none |
| 122, class 5 | 0.934 | 3.834 | 3.645 | 931 +0.0025, 994 +0.0027, 870 +0.0040 | 7 | none |
| 122, class 5, seed 3, 593 s | 0.928 | 3.976 | 3.680 | 870 -0.0012, 931 +0.0005, 811 +0.0026 | 5 | the state of seed 1 again |
| 122, class 5, 590 s | 0.930 | 3.930 | 3.676 | 870 -0.0001, 931 +0.0011, 994 +0.0025 | 6 | 0.0020 to 0.0027 under held, not under the bar |
| 122, class 5 | 0.924 | 3.819 | 3.774 | 870 -0.0009, 931 +0.0006, 811 +0.0029 | 5 | 0.0020 to 0.0027 under held, not under the bar |
| 130, class 4 | 0.924 | 4.206 | 4.163 | 992 +0.0046 | 1 | none |
| 122, class 5 | 0.932 | 3.883 | 3.681 | 870 +0.0018, 994 +0.0021, 931 +0.0032 | 4 | 0.0020 to 0.0027 under held, not under the bar |
| 122, class 5 | 0.926 | 4.105 | 3.753 | 931 +0.0043, 870 +0.0054 | 4 | none |
| 110, class 2, from the kept states of round 19 | 0.820 | 3.975 | 3.975 | 803 +0.0029, 986 +0.0056 | 1 | none |
| 93, class 3, from the kept states of round 19 | 0.820 | 4.087 | 4.087 | 804 +0.0013, 924 +0.0021, 987 +0.0022 | 4 | 804 at held |
| 135, class 0 | 0.826 | 4.159 | 3.941 | 921 +0.0007, 984 +0.0034, 860 +0.0035 | 3 | 921 at +0.00017 over held |
| 135, class 0, from its kept states | 0.826 | 3.941 | 3.941 | the same | 2 | none |
| 118, class 1, one square less | 0.826 | 4.492 | 5.266 (117, class 0) | none | 0 | none |
| 133, class 7 | 0.812 | 3.835 | 3.811 | 982 +0.0022, 919 +0.0041 | 3 | none |
| 151, class 7 | 0.812 | 4.207 | 4.032 | 982 +0.0044, 919 +0.0053 | 3 | none |
| 124, class 7 | 0.818 | 4.673 | 4.013 | 982 +0.0078 | 0 | none |
| 101, class 2 | 0.822 | 4.386 | 4.080 | 862 +0.0055, 803 +0.0060 | 2 | none |
| 101, class 2, from its kept states | 0.822 | 4.080 | 4.080 | the same | 0 | none |
| 143, class 8 | 0.822 | 4.104 | 3.786 | 983 +0.0052 | 1 | none |
| 143, class 8 | 0.824 | 4.113 | 3.838 | 983 +0.0058 | 1 | none |
| 143, class 8 | 0.830 | 4.080 | 3.945 | 983 +0.0058 | 1 | none |
| 81, class 0 | 0.830 | 4.405 | 4.125 | 984 +0.0029, 921 +0.0048 | 2 | none |

- **A fresh hop run takes 0.17 to 0.35 off a class 5 corner.** The one exception is the 122-square corner of 0.924, which loses only 0.045. After the hops the 122-square corner loses 3.645 to 3.774 at f = 0.924 to 0.934.
- **The gain comes in the first slot of about 280 s.** The second slot of a 10-minute run found nothing on the 0.93 corner. A second seed from the same start found the same state (3.6800 at 0.928, seeds 1 and 3).
- **Runs from kept states found nothing.** This held on the corners of 0.826 and 0.822, and on the round 19 corners of 0.82.
- **One square less does not pay on the 118 class 1 corner of 0.826.** It gives 117 squares at 5.27.

### 8.3 The builds of 811, 870 and 931 end in one of two places

The hopped 122-square corner of f = 0.928 gave the three results of this round: 811, 870 and 931. The second leg built them again from five more hop runs on the 122-square corner, at f = 0.924 to 0.932. A build ends in one of two places, and the row does not decide which:

- From the hopped corners of f = 0.924, 0.928, 0.93 and 0.932, a build ends 0.0020 to 0.0027 of side below held.
- From the unhopped corners, and from the hopped corners of 0.926 and 0.934, a build ends at held or up to 0.0012 above it.

| n | rows of the hopped corners of 0.924 to 0.932, against held | built less held, 5 builds |
|---|---|---|
| 870 | -0.0012 to +0.0018 | -0.00238 to -0.00257 |
| 931 | -0.0023 to +0.0004 | -0.00224 to -0.00271 |
| 811 | +0.0004 to +0.0054 | -0.00199 to -0.00219 |

So the family squeeze ends at about the same layout from each of these corners. 870 now sits at the board: the board side of 870 and our build both have f = 0.9144. On 811, 931, 993 and 994 the board is 2e-6 to 9e-6 of score below the bar. The 122-square path is spent for these n.

Below f = 0.83 a build takes 0.0006 to 0.0033 off its row, and the rows start too high. The lowest builds there end above held: 921 by 0.00017, 863 and 924 by 0.0008, 803 by 0.0009. 804 ends at held, because it is the round 19 layout of this lane again. The board is 0.004 to 0.02 of side below our bar on 803, 804, 860, 863, 919, 921, 924, 982, 984 and 987. These n need another design.

### 8.4 What the follow lanes did with these layouts

- 811 and 931: this lane certified them at 09:52. The family lane went just below both within 4 to 7 minutes, from our files. Then the invent, polish, classfill and readers lanes went further.
- 870: the family lane reached our side by 10:34.
- The border lane put one border on our 870 and certified 929, 1.9e-4 of score under held. It put one border on our near 931 for 992. The readers lane went down from that 992 to 868 and 929, 2.3e-4 of score each.
- The classfill lane certified 994 with the hopped corner of 0.928, its own far zones and one kick (4.7e-5).

This lane handed 24 near layouts and two libraries to the follow lanes, with one handoff line each.

The libraries of the hopped corners are in the take dir: `work/libs` (`lib-f928h2`, `lib-f93h5`), with the new base files in `work/corners`.

### 8.5 What the next round should run

1. **Drop the 122-square corner for 811, 870 and 931.** Its hopped states at f = 0.924 to 0.932 all build to 0.0020 to 0.0027 below held. On 870 the board side equals ours. On 811, 931, 993 and 994 the board is 2e-6 to 9e-6 of score below the bar. Leave these n to the kick and shell lanes.
2. **The low-f n need a new design.** 803, 804, 860, 863, 919, 921, 924, 982, 984 and 987 trail the board by 0.004 to 0.02 of side. That is 2.4e-4 to 6.9e-4 of score each. Six new base files of f = 0.812 to 0.83 and 14 hop runs gave rows 0.0007 to 0.008 above the bar. A build there takes only 0.0006 to 0.0033 off its row.
3. **Give the near 921 to the border and readers lanes.** It ends 0.00017 above held, no take holds 921, and the board is 2.4e-4 of score below. One lkick of 300 s found 2e-8. The border lane took 929 from our 870 with one border, so a border or a shell step may reach where a kick does not.
4. **Collect on boxA under nohup.** The three results of this round sat on boxC for 7.5 hours, because the collector ran only inside the agent. A collect loop would have taken them at 02:18, before the reboot of 05:36.

## 9. Round 22 (2026-11-13)

The new infill corner reached 978 through the corners lane, gaining 1.245e-5 of score against round 20. Fresh full builds from this lane also led to wins for 507, 815, 875, 936 and 999 in other lanes. This lane holds 985, gaining 4.40949413205e-7. The ten low-f targets still need a better design.

The new tools are [stair-c_design.py](../stair-c_design.py), [stair-c_crop.py](../stair-c_crop.py) and [stair-c_border.py](../stair-c_border.py). They import the geometry and search tools of other lanes. The 161 full build records cover 36 n. They are in [stair-c-r22-2026-11-13.tsv](../results/stair-c-r22-2026-11-13.tsv). These records give raw sides. The take holds the final certified rows.

### 9.1 What the targets hold

None of the ten targets moved in round 21. The board gives sides, not coordinates. The gaps below compare its per-puzzle side with round 20.

| n | held f | board f | side gap |
|---|---|---|---|
| 803 | 0.813499 | 0.793943 | 0.019556 |
| 804 | 0.825387 | 0.810061 | 0.015326 |
| 860 | 0.800288 | 0.788369 | 0.011919 |
| 863 | 0.840065 | 0.830333 | 0.009732 |
| 919 | 0.790019 | 0.780569 | 0.009450 |
| 921 | 0.812954 | 0.805719 | 0.007235 |
| 924 | 0.850709 | 0.841618 | 0.009090 |
| 982 | 0.801262 | 0.793106 | 0.008156 |
| 984 | 0.824096 | 0.820404 | 0.003692 |
| 987 | 0.862212 | 0.854732 | 0.007480 |

Eight held layouts cut into two flush arms of 9. The ordinary reader refuses 919 and 982. A wider cut of 982 finds two arms of 9 and an extra outer column. Its rest starts at x = 9.801262, one unit farther right than its arm width of 8.801262. Twelve tilted squares cross x = 1, reaching x = 0.979345. A simple rectangle and rigid column cannot reproduce that interlock.

Public neighbours use several designs. They have two arms of 7 at 803, 804, 863 and 924, unequal arms at 921 and 984, and two arms of 10 at 981. The old low-f library has 51 corners with two arms of 9, all with opposite lean signs. Its public `981h.C` has equal lean signs. That corner comes from udishiken/square-in-square-strecth-fq, under Apache 2.0. These differences gave the reason to test new seams and cores.

### 9.2 Controls

The placement code rebuilt the imported staircase exactly: 79 squares, largest coordinate difference 0.0. Its smallest exact gap was -1.45e-15, with no centre beyond a flush face. Both boxes printed that result on scipy 1.18.1.

The infill controls gave 114 and 115 squares for the two lean choices. Their smallest gap was -1.11e-15, with no centre beyond a flush face. Adding a square in the reserved grid made the exact test fail at -1.0. Rectangular core controls gave 155 and 169 squares, with smallest gap -1.56e-15.

An earlier seed check caught infill inside the reserved grid. Those scans stopped before publication. Infill now stays in the union of the arm strips. A second check caught centres beyond the other arm's face. The final scan clips against both faces before ranking.

The public elbow needed repair before a cut. Its stored stack gaps were -0.00225 and -0.00393. Settling it kept all 199 squares and passed the exact test at 2.2e-11. Its loss rose from 4.755859 to 4.766590. A separate cut control changed a 3 by 3 upright grid into a 2 by 2 grid exactly.

The border control reproduced the ordinary 975 assembler point for point at source side plus 0.0001. It gave 975 squares, side 31.7146839826 and smallest gap -6.64e-14. Trading one bottom stack for an outer column then gave 974 legal squares. All five tested column placements passed, with smallest gap -6.72e-14.

A tight slid-861 control failed for both the old assembler and the new one at source f plus 0.0001. It passed at plus 0.0003, with 861 squares and smallest gap -9.53e-14. Removing its slide grant made it refuse. The failed control remains in the logs.

### 9.3 New elbow constructions

**Tilted strips, then upright infill.** Place both tilted strips first, growing from the flush faces or from the walls. Fill vacant unit-cell pockets afterward. This removes the protected upright staircase from the seed and permits equal lean signs.

| variant | f | legal settled corners | lowest corner loss |
|---|---|---|---|
| opposite lean signs, before face clipping | 0.800 | 7 | 5.765683 |
| opposite lean signs, before face clipping | 0.825 | 6 | 5.644232 |
| opposite lean signs, with face clipping | 0.800 | 24 | 5.220124 |
| equal lean signs, with face clipping | 0.800 | 19 | 5.156907 |

The 51-square corner `sc22zip-51f8000-20` paid despite its high loss at f = 0.80. The corners lane carried it and used it for its 978 take, 1.245e-5 of score below round 20. A later public layout from the polish lane beat that 978. The corner's count class and its trade between face lengths matter as well as total loss.

One insertion and hop run on that corner produced 52 squares. In 350 s its loss fell from 4.6139 to 4.4714. Only the new count got hops. Its closest ranked row was 0.016029 above held, outside the 0.008 build cut. The unchanged 51-square state was already with the corners lane.

The 100-square corner with equal lean signs got a separate 354 s insertion and hop run. Its loss stayed at 5.1569 after 89 hops. The inserted 101-square state lost 6.3375, then 6.3225 after 16 hops. Equal-lean builds of 863 ended 0.017767 above held. The hopped corner ended 0.013787 above it.

**Rectangular upright core.** Equal-lean strips surround a fixed upright rectangle. Eight short core sizes gave 3,337 cheap candidates and 24 settled corners. The best loses 4.293853, with 125 squares and a core of 8 by 7. Full probes ended 0.023649 above held at 803 and 0.008685 above it at 978. Six longer cores gave 24 settled corners. Their best loses 5.636938, with 198 squares and a core of 8 by 9.

Slide grants of 0.04 and 0.10 did not fix the short core. They made 68 short-core variants and 44 long-core variants. The best target rows remained 0.02795 to 0.03364 above held.

**Shorten the dense public elbow.** Delete a unit row or column from `981h.C`, compress its coordinates, then settle. Of 49 cross cuts, 14 settled. The cheapest loses 7.726062, with 169 squares. Seven column-only cuts gave four legal corners, best loss 5.797262. Seven row-only cuts gave one, loss 7.879708. Repair costs more than the removed strips save.

### 9.4 Outer column construction

The new assembler builds a rectangle of width L minus 1 and height L, then adds m squares in an outer column. Its rest loses m minus c2 plus 1 cells. The column adds m, so the net count rises by c2 minus 1. For arms of 9, rank n minus 8 and add one to the corner's horizontal allowance.

Top, bottom and uniform column gaps gave 21 initial builds across seven target rows. At 921 the uniform seed ended 0.002108 above held. The top and bottom seeds ended 0.005146 and 0.005858 above it. Gap placement changed the final side by 0.00304.

Two more seeds placed gaps around tilted contact vertices, with margins 0.025 and 0.0125. The larger margin protected 12 of 14 contacts at 921. It ended 0.002318 above held, worse than the uniform seed. These tests used symmetric contact margins. They did not test a free asymmetric interlock.

The second pool added 343 modules missing from the old pool. These include designs from rounds 19, 20 and 22. They are not 343 new designs. Ranking three distinct corner families per target gave better builds after full assembly. The best 921 border build ended 0.000774 above held. The best 984 ended 0.001361 above it.

The pool also exposed invalid stored tables. `803fa19.Ct` and `803in20.Ct` predicted gains but failed both start caps. Exact tests at their own f found stack overlaps of 0.002342 and 0.002981. The ranker now imports the closed-corner list and repeated no-start rule from `modules_round22.py`.

A final input repair settled those two plain corner point sets at their own f. It kept their 128 and 119 squares. Fresh rigid groups and length tables went under new `sc22repaired-*` IDs. Losses became 3.875874 and 3.875871, with stack gaps of 2.2001e-11. The old IDs stay closed. Repaired border predictions were 0.0128 to 0.0247 above held. The old negative predictions came from invalid geometry or tables. Ordinary full builds with the repaired corners ended above held too: 803 by 0.001045, 862 by 0.000958, 923 by 0.003115 and 986 by 0.004397.

### 9.5 Follow work and publication

The collector handed every full build and new corner to all follow lanes as it arrived. A feed read handoffs and new layouts every two minutes. It ranked readable new corners across all 110 n in the slice. Exact geometry fingerprints skipped copies of this lane's own designs handed back through another lane.

One untabulated far state, `874ns22.F2~`, blocked eleven cumulative module imports. This was found at 15:11 UTC. The available 882 states then got one combined import. A separate queue ranked the ten primary targets first. All ten primary targets got rows. The broad queue left 44 rows across 22 n before it stopped. A later 39-state patch left 20 rows across ten n. The excluded state and both partial tables are in the work archive. This input fault delayed those module tests.

The primary table gave a fresh 921 build at side 30.813077844774426, 0.000124048 above held. It uses `984nr22.C~`, `860fa17.F1` and `921h13.F2`. The first 860 choice refused a slide grant. Its alternate started but reached the 15:20 deadline before it wrote a full result. It does not count.

The 816 fresh build `816-ed3b461b-s.csv` led through the family lane to 875, 936 and 999. Later kicks and readers improved those files. The 815 near miss `815-748fa00d-s.csv` led through the corners lane to wins at 815 and 507. Their take rows preserve the full ancestry. These gains belong to those lanes.

This lane's 985 uses `863ns22.F2`, read from a fresh 863 near miss. Its other modules are `861fa17.C~` and `984h.F2`. The raw side is 31.83442371775321, against held 31.834437558364247. The certified file got one fq quench on boxE. That quench raised the side, so the final file keeps the better certified input. The final score is 0.014329081623421391. Its smallest gap is 5.02069e-11 under both text and pandas parsing.

Early builds of 875 and 936 beat round 20 but trailed frozen round 21 takes. They count for nothing. The collector checks the full bar before the final quench and again before each atomic take update. A raw change at 998 gained about 4.5e-11 of score, below the required 1e-10, and was not published.

`stair-c_run.py jobs` now accepts `--source-key`. Distinct libraries reused module IDs and could otherwise hide different geometry behind the same job hash. The default hash stays unchanged. The control kept legacy job `863-7af51805` and gave distinct hashes for the fan and opposite-lean libraries.

The process budget stayed at one on boxC and two on boxE. Every heavy job ran under nice, nohup and a 15:20 UTC guard. The final box copies, queue logs, libraries and hop states live in the take's `work/archive`, `work/boxcopy` and `work/libs`. Both box archives passed SHA256 checks: 675 entries on boxC and 3,054 on boxE. Both workers and all local loops stopped. Both own scratch dirs were removed. The shared boxE base remains.

### 9.6 What the next round should run

1. **Build fresh combinations and hand them off at once.** The 816 build led to wins at 875, 936 and 999. The 815 near miss led to 815 and 507. These returns exceed the gain from this lane's final 985. Preserve the exact full build and its module manifest.
2. **Carry the 51-square infill corner at useful f.** It already gave 978 a gain of 1.245e-5 through the corners lane. The inserted 52-square corner loses 4.4714 but its closest row is 0.016029 above held. A new far zone or face-length trade must change that fit before it gets another build.
3. **Give the fresh 921 build to the kick, border and reader lanes.** It ends 0.000124048 above held, closer than the round 21 near miss at 0.00017. Its exact file is `near/921-b97f2a90-s.csv`. It got a full squeeze, but no separate kick.
4. **Make the outer column interlock with the tilted arm.** The held 982 arm crosses x = 1 by 0.020655. A rigid column misses that freedom. The new border builds reach 0.000774 above held at 921, but symmetric contact gaps did not improve the uniform seed. Test asymmetric gaps or moving column cells with exact count checks.
5. **Keep the strict repaired corner tables separate from their closed originals.** The two repaired point sets pass exact stack tests. Their four ordinary builds and their border predictions stay above held. Use only freshly rebuilt tables and require a full assembly before treating a predicted gain as useful.
6. **Drop the tested empty fans, long cores and public-elbow cuts.** Their cheapest losses are 5.156907, 5.636938 and 5.797262. The one useful exception is the 51-square opposite-lean corner, whose later carry gave 978.

## 10. Round 23 (2026-11-13)

The final take holds 0 n. Its gain is 0 against round 21 and 0 beyond frozen round 22 and the other round 23 takes. The run completed 167 full builds across 35 n. It also exported 85 legal SLP stages before the builder quenches.

Every raw record is in [the round 23 table](../results/stair-c-r23-2026-11-13.tsv). A negative raw side difference is not a certified gain. Some early 814 rows stood about 1.4e-9 of side below held, only 4.9e-11 of score. They fail the required 1e-10 score cut.

Other take rows cite this lane at n = 935 (take-classfill-r23), 876 (take-family-r23). Their gains are excluded from this take. Ancestry snapshots remain in `work/contribution-history.jsonl`.

### 10.1 The 51-square corner at useful fractions

[stair-c_infill.py](../stair-c_infill.py) carried the round 22 infill corner, then ran one four-minute hop search at each new fraction. Every carry kept 51 squares. The exact source control passed, and a duplicated square failed at gap -1.0.

| f | lowest corner loss |
|---|---|
| 0.7558 | 4.091540 |
| 0.7700 | 4.258313 |
| 0.7850 | 4.471371 |
| 0.7950 | 4.584001 |
| 0.8100 | 4.694421 |
| 0.8250 | 4.768809 |
| 0.8450 | 4.848779 |

The 0.7558 run started from the hopped 0.77 corner. Its fraction follows the frozen 978 bar, 31.7557396592. It did not repeat the earlier 0.7591 carry.

A wider diagnostic removed the prediction floor. The 0.77 corner first fit 978 at 31.7689126471, 0.013173 above that bar. The 0.7558 corner first fit at 31.7807095115, 0.024970 above it. Lower corner loss did not give a better full fit.

The old 52-square corner got a separate screen against fresh far zones. It got no new insertion or hop search. All four stored corner states passed their exact checks. With 531 far zones of arm size 9, the final screen found no fit within 0.014 of the bar across all 110 n. That screen removed the prediction floor too. It started no full probe.

### 10.2 Asymmetric outer-column interlock

[stair-c_interlock.py](../stair-c_interlock.py) rotates successive wall cells in opposite senses. It assigns their gaps with unequal weights and pushes nearby tilted cells 0.025 into the seam. A local soft repair precedes the full family squeeze.

The source control preserved every coordinate and kept the square count. A duplicated column cell failed with overlap energy 1.0. Small column rotations were 0.002 and 0.006 radians.

One of four seeds passed the first repair. It returned 921 to its starting side, 30.8137274401. Three seeds failed the strict local energy cut. A wider exact repair made all three legal. Their final sides were 30.8157519913 at 921, and 31.8012620300 and 31.8045002550 at 982.

None beat held. The closest 982 ended 6.8e-9 above its source. The 921 source already stood 0.000774 above held. These column seeds need a different contact arrangement before another search.

### 10.3 Fresh combinations and controls

Readable donors now contribute both far zones and their corner. A locked cumulative cache lets one fresh donor combine with earlier fresh donors. Immutable libraries keep each build recipe reproducible. The initial cache control retained 418 patch states and their tables. At source side plus 0.0001, it matched the ordinary 975 assembler with coordinate error 0.0. All five bordered-974 placements passed.

[stair-c_rank.py](../stair-c_rank.py) ranks in bounded chunks, with the ten primary targets first. Its required-module join keeps every eligible pair once. Exact differential checks matched sides, stops, IDs and stack counts at 761, 816 and 873. Two targets had rows. An absent required state returned none. The small control showed no speedup, so it does not prove a faster full search.

[stair-c_job.py](../stair-c_job.py) exports the legal SLP before the two builder quenches. Each builder quench has a 120-second limit. The separate quench from a certified file still has its 240-second limit. The 975 control exported side 31.7145703048 before finishing at 31.7145701761. Both files passed coordinate and count checks against the known 31.7145839826 source.

The feed uses geometry fingerprints, donor snapshots and content versions. A changed table can release an earlier untabulated state. A changed corner library gets a new immutable job identity. An input becomes complete only after its copy and queue append succeed. The runtime sources are in [tools/stair-c](../tools/stair-c).

Search used one process on boxC and two on boxE. Inactive libraries were compressed under a lock and restored before use. SHA256 checks covered each archive member and each moved library. Search and quenches shared the 18:30 UTC deadline. Final box copies passed their receipt checks before both own scratch directories were removed.

The take, controls, donor snapshots and box archives are under `<scratch>/bounties-squares/take-stair-c-r23`. Pending recipes remain there for the next round. No lane process remains. This lane made no Kaggle submission.

### 10.4 Next

1. Build fresh combinations first and export the SLP at once. The 817 and 935 starts reached follow-lane takes at 876 and 935. Keep immutable recipes and carry both far zones.
2. Continue the newest saved queue with the cumulative cache. Bounded ranking left unstarted recipes. Prefer a new corner or far zone over another version of a known floor.
3. Give near layouts to the follow lanes before repeating a quench. The 935 start stood 0.000348 above the bar and still supplied useful modules.
4. Leave the seven tested 51-square carries and the old 52-square corner closed until a new far zone changes their full fit. Their exact corners were legal, but their predicted layouts remained above useful cuts.
5. Change the column contact arrangement before repeating the asymmetric seeds. Wider repair recovered legal packings but no lower side.

## Files

| file | what it is |
|---|---|
| [`stair-c_table.py`](../stair-c_table.py) | `need`: for every n and pair, the loss the side allows, the library's cheapest far zones, and the corner loss that would tie held. `pairs`: the pairs by what a corner on the staircase line would give |
| [`stair-c_run.py`](../stair-c_run.py) | `add`: staircase base files into a new library. `mark`: hopped corners as usable by the generator. `ns`: the n of the slice near an f. `jobs`: the rows of a queue file as job lines, largest score gap first. `best`: every build as one table |
| [`stair-c_design.py`](../stair-c_design.py) | tilted strips with upright infill or a rectangular core, with exact placement controls |
| [`stair-c_crop.py`](../stair-c_crop.py) | unit cuts of a dense public elbow, with source repair and count controls |
| [`stair-c_border.py`](../stair-c_border.py) | two-arm rectangle plus outer column, contact-gap seeds, exact controls and strict corner repair |
| [`stair-c_bar.py`](../stair-c_bar.py) | the lowest row of each n in the queue tables next to the lowest side that any live take dir holds for that n |
| [`results/stair-c-r17-2026-11-12.tsv`](../results/stair-c-r17-2026-11-12.tsv) | every build of this lane: n, corner, far zones, stacks, predicted, built and held side |
| `<scratch>/bounties-squares/take-stair-c-r17` | the take: one csv for each n, `take.tsv`, `near/` with the layouts that ended just above held, and `STATE.txt` with the log of the queues |
| [`results/stair-c-r19-2026-11-12.tsv`](../results/stair-c-r19-2026-11-12.tsv) | every build of round 19: n, corner, far zones, stacks, predicted, built and held side |
| `<scratch>/bounties-squares/take-stair-c-r19` | the take of round 19, with `near/`, `STATE.txt` and `work/`: the queue scripts of the two boxes, the base files in `work/corners` and the far zone tables in `work/far` |
| [`results/stair-c-r20-2026-11-13.tsv`](../results/stair-c-r20-2026-11-13.tsv) | every build of round 20: n, corner, far zones, stacks, predicted, built and held side |
| `<scratch>/bounties-squares/take-stair-c-r20` | the take of round 20, with `near/`, `STATE.txt` and `work/`: the box scripts in `work/box`, the box logs and hop states in `work/boxcopy`, the base files in `work/corners`, the libraries of the hopped corners in `work/libs` |
| [`results/stair-c-r21-2026-11-13.tsv`](../results/stair-c-r21-2026-11-13.tsv) | every build of round 21: n, corner, far zones, stacks, predicted, built and held side |
| `<scratch>/bounties-squares/take-stair-c-r21` | the take of round 21, with `near/`, `STATE.txt` and `work/`: the box copies in `work/boxcopy` (logs, queue tables, hop states, builds), the new base files in `work/corners`, the libraries of the hopped corners in `work/libs` |

| [`results/stair-c-r22-2026-11-13.tsv`](../results/stair-c-r22-2026-11-13.tsv) | every full build of round 22, with the round 20 and live take bars |
| `<scratch>/bounties-squares/take-stair-c-r22` | final take, near misses, box archives, new corners, libraries, controls and queue logs |

## Summary

- The slice is m 28 to 31 with k 17 to 45, 110 n. The lane carried the staircase corner of the twoshort lane to f = 0.76 to 0.88, for arms of 7, 8 and 9.
- Result: 12 n certified below held. The take holds 9 at the end (803, 805, 815, 859, 861, 920, 922, 984 and 985), 0.000726 of score below held. Round 17 took 861 and 982 from this lane, 0.000161. The follow lanes then went below this take on 859, 861, 920, 922, 984 and 985, with the 91-square corner of this lane. At the end 803, 805 and 815 are still the lowest of every take.
- The find is one step: take one square out of a class 1 staircase corner of two 9-arms at f = 0.80, then run hops. The class 0 corner that comes out loses 3.51 to 3.74 squares, and the staircase corner of class 0 loses 4.56. All three class 1 corners of the base file do it. The same step on the 92-square corner gives 3.84 in class 1. These corners gave 859, 861, 920, 922, 984 and 985.
- The kill line fired by its letter after the first generator run: 3 n within 0.003 of held, not 5. The builds then showed that the line was too tight. Section 1 says both.
- Every row is at k of 17 to 26. No corner of this lane gives a row within 0.008 of held above k = 26.
- Next: build the staircase corners at the f of each n and take one square out of their class 1 corners. A corner serves the n near its own f: 978 moved by 0.0013 of side when the corner came from 0.76 and not from 0.78.
- Round 19: the take holds 4 n (804, 870, 931 and 993), 0.000544 of score below the round 17 file and 0.000481 below every other take. The follow lanes took 924 and 987 from the 804 of this round.
- Round 19 has two finds. Plain hops on a class 2 or class 3 staircase corner at f = 0.82 pay for three runs. A capped LP then carries the corner to the f of the next n. A staircase corner built at f = 0.92 serves the n of k = 27 to 33 with no hop.
- The line "no row within 0.008 of held above k = 26" was true for corners built at f = 0.88 and lower. It is not true for corners built at f = 0.92.
- Next after round 19: staircase corners at f = 0.90, 0.94, 0.96 and 0.98, and plain hops on their cheap classes.
- Round 20: the lane certified 810, 811, 869, 930 and 993. The take holds none of them at the end. The follow lanes went just below each one, and 869, 930 and 993 stand on the hopped corner of this lane.
- Round 20 has two finds. A build ends 0.0017 to 0.0045 below its row at f = 0.90 to 0.94, so rows up to 0.0065 above the bar are worth a build. The class 4 staircase corner of 148 squares is cheap at f = 0.93 only: 4.07, against 4.35 to 4.73 at 0.92 to 0.94. One hop run on it gave the best rows of the round.
- Next after round 20: the staircase at steps of 0.005 near f = 0.93, then hops on each class 4 corner there. Hand each new corner to the follow lanes as a library at once.
- Round 21: the lane certified 811, 870 and 931 from the hopped 122-square corner of f = 0.928. The take is empty at the end, because the follow lanes went just below all three with our files.
- Round 21 has two finds. From any hopped 122-square corner of f = 0.924 to 0.932, the builds of 811, 870 and 931 end 0.0020 to 0.0027 below held. 870 now equals the board. The staircase corners of f = 0.812 to 0.83 give no row within 0.0007 of the bar.
- Next after round 21: drop the 122-square corner for these n. The low-f n trail the board by 0.004 to 0.02 of side and need a new design.

- Round 22: new tilted-strip infill gave 978 to the corners lane. Fresh builds led to wins at 507, 815, 875, 936 and 999. This lane also certified 985. The outer-column assembler reached 0.000774 above held at 921. A later module build reached 0.000124 above it. Section 9 records the controls, refused tables and next tests.

## 11. Round 24 (2026-11-13)

The final take holds 0 n. Its gain is 0 against the round 23 candidate and 0 beyond other live takes.

The run completed 192 full builds and exported 193 SLP stages across 28 n. It recorded 11 refused starts. The [round 24 table](../results/stair-c-r24-2026-11-13.tsv) lists every completed stage. Its sides are raw measurements. They do not certify a gain. 18 stages failed the source screen.

### 11.1 Fresh 985 round trip

A fresh composition reached side 31.834424538212, only 8.189e-7 above the candidate. Its corner came from a new readers 921. The modules lane cut that near layout and returned its corner with slide grants. Combining it with two versions of the prvsiyan research 921 far zone reached raw side 31.834226149039.

Floatsafe certified side 31.834226150581. The separate certified-file quench raised the side to 31.834260496315, so the file kept the better certified input. Its score was 0.014322786560749368, a gain of 6.29506267202e-6 against the candidate.

Harvest quenched that fresh file to a score 1.13e-12 lower before this lane's ancestry review finished. Follower takes recorded a gain of at least 6.46393214265e-06 from that 985 chain. That gain is excluded from this take.

The corner matched the near file with coordinate error 0.0. Its copied native module matched its recorded SHA256 exactly. The ancestry review resolved the short round 22 near-921 record through the readers and family ledgers. Its leaves are independent staircase and taper constructions, four named Apache notebooks, and Samanyu seed n = 804 and n = 983. The licence appendix states that Samanyu ancestry explicitly. The recorded roots include no areebbb file. The evidence is in `take-stair-c-r24/work/ancestry-985.json` and the updated near sidecars.

A second certified-file quench, for 995, did not finish before the deadline. Its certified input gains 2.82357136738e-6 score against both the candidate and the current live pool. It is excluded from the take. The input and pending source record remain in boxE archive.

### 11.2 Queues, source checks and controls

The [worker](../tools/stair-c/r24/worker.py) and [collector](../tools/stair-c/r24/coordinator.py) use one serial worker on each assigned box. The first import held 267 named states and saved 253 distinct states after 21 minutes. Later imports used three states per turn. A reader screen checked 148 saved versions in 4.18 seconds and found 52 readable layouts. Their module requests replaced the raw-file backlog. Small corner handoffs use the same priority.

The exact control rebuilt 975 with coordinate error 0.0 and passed all five bordered-974 placements. The fresh join matched two nonempty reference rows. An absent module returned no rows, and a duplicated square failed. The frozen ledger recovered 172 completed recipes as exclusions. Ambiguous versions were left out.

The initial withdrawal quarantined 11 near files from this lane. Later source checks also reject withdrawn ancestors. A live source field of 218752 bytes exposed the CSV reader's default limit. The reader now accepts fields up to 64 MiB. The 804 and 814 raw reductions of about 1.4e-9 side failed the required 1e-10 score gain.

The [independent-source screen](../tools/stair-c/r24/source-free.py) used 1750 staircase and taper modules. Its 975 positive control passed, and its absent-module control returned none. Counts 809, 866, 868, 927, 935 and 990 had no fit within 0.003 side of the round 22 threshold. Those six counts use the later source-policy threshold only for alternatives without Samanyu ancestry.

All search and quenches shared the 22:15 UTC deadline. Both boxes kept scipy 1.18.1. The final copies verified 1046 payload files from boxC and 1247 from boxE by SHA256. Receipt controls rejected changed bytes. The process-scope control found the own worker and excluded the current session. Every own process stopped, and both own box scratch directories were removed. Cleanup left the shared environments untouched. This lane made no Kaggle submission.

### 11.3 Next

1. Audit and quench the archived certified 995 first. Its measured gain is 2.82357136738e-6 score, and the required quench did not complete.
2. Recut fresh near layouts at once. The first 985 was above the bar, and its recut corner supplied the later gain. Preserve the exact input and its source record.
3. Keep small table imports ahead of broad saved pools. The first 267-state import occupied one slot for 21 minutes. The three-state queue preserves room for new layouts.
4. Build new independent zone classes for the held counts. The existing 1750-module pool gave no fit on all six source-policy targets.
5. Resume saved requests against the next bar with their exact module data and recipe ledger. Keep the tested infill and asymmetric-column branches closed.


## 12. Round 25

This round rebuilt the library from licensed sources and recut fresh layouts. Search stopped at 02:15 UTC on November 14. The final period served certified inputs to fq and collected the results.

### 12.1 Sources and certification

The archived 995 went to the quench lane first. Its full parent record then exposed the unlicensed Samanyu GitHub seed 504. The lane withdrew that request and excluded the layout. The older 985 follower also stayed out.

The source reader stores full records once by hash. Queue records point to those immutable proofs. It checks donor labels and every nested parent file. A hidden withdrawn 735 failed the control even when its outer label claimed CC0. Changed proof bytes also failed. The control accepted an independent construction.

Round 23 a matched the clean b coordinates on 980 counts. The remaining 20 counts stayed out. A self locator passed only with its real source record. A parent cycle failed. The areebbb notices now come from its actual per_n.csv rows. Donors 462 and 703 name the malyshevdanil atlas notebook and its ms record.

An early quench wrapper silently skipped fq because its default binary path did not exist on either box. The lane withheld the take and fixed both worker imports and the wrapper. New receipts require the invoked binary, its hash, return code and elapsed time. Old receipts without a completed invocation cannot publish.

The corrected control invoked fq on held 975 on both boxes. Both returned code 0. Its worse output preserved the better certified input. Every retained row needs a completed remote invocation and a fresh floatsafe check at 2.2e-11.

### 12.2 Designs and measured results

Fresh near cuts produced a licensed 985. Its real fq pass reduced side 31.834291741693 to 31.834239160074 in 28.55 seconds. The certified score is 0.014323201126755336. Its gain against the base bar is 0.000005880496666055279. The final take and live comparison are recorded in the report.

The real fq pass on 921 raised its side from 30.812929332922 to 30.816660614183. The wrapper kept the input, and a lower peer result excluded it. A certified 873 reached this lane's take, then the quench lane superseded it. These rows contribute no separate retained gain here.

New independent corner designs tried equal-area transfers and delete-two hops on the six held source-policy targets. No class-only rank fitted those six counts. Plain exact-f designs generated 16 states at 866 and 11 at 935. Their minimum scalar losses were 4.339859814 and 4.61431457. Those scalar bounds did not establish a full layout.

All 27 plain states went to both workers in packets of at most three. The new ranks produced rows at 984 and 921. Neither result closed a held target. Fresh packets now rank before the older build queue. An adversarial file-age control confirmed that explicit priority wins.

The [result table](../results/stair-c-r25-2026-11-14.tsv) records full builds and SLP exports separately. It includes failed source screens as measurements. Such rows cannot enter the take. The infill and column branches stayed closed.

### 12.3 Next

1. Recut fresh licensed layouts first. The new 985 cut supplied the retained improvement, and a real fq pass removed another 0.000052581619 of side.
2. Test coupled corner and far-zone classes at the exact target f. The 27 plain states improved scalar losses but closed none of the six held counts.
3. Preserve the three-state import limit and explicit priority. Large pools delayed fresh work in round 24, and the new priority control passed.
4. Resume saved builds only against the new bar. Keep the exact recipe and immutable source proof. The 921 quench worsened its input, so predictions alone cannot count as gains.


### 12.4 Final measurement and cleanup

The table contains 663 full builds and 664 SLP exports across 17 counts. Source checks excluded 44 stages, and two starts were refused. The saved queues hold 177 pending builds on boxC and 152 on boxE.

The final take retains only 985. Its score gain is 0.000005880496666055279 against both the base and the other live takes. Other lanes retained descendants at 873, 922 and 982. Their gains remain in their own takes.

Receipt checks verified every payload hash: 2249 files from boxC and 2884 from boxE. Changed-byte controls failed as expected. The process-scope control found each own worker and excluded the current session. Both workers stopped before cleanup. The local collectors and relay also stopped.

Both own remote scratch directories were removed after verification. The shared runtimes remain in place. No Kaggle submission ran.

## 13. Round 26

The base bar is `gate/cand-round25-1114b` (round 25 b, local 22.1288984278). The lane ran from 12:48 to 17:15 UTC on November 14, with one serial worker on each of boxC, boxD and boxE. Search stopped at 16:45 UTC. The first agent of the round stopped at about 13:24 UTC on a usage limit, and the second at about 16:29 UTC on a dropped connection. Each time the coordinator and the workers ran on, and the next agent took them over from STATE.txt.

### 13.1 What ran

The workers ran three items of the round 25 list. Item 1 recut fresh licensed layouts. These are the held rows that moved in rounds 24 and 25 and every readable layout of the other round 26 take dirs. Every near layout of our own builds came too. Item 2 built staircase corners at the exact f of a target. Item 4 resumed the saved round 25 builds.

The round 26 source gate drops the held 921 modules and the bare file name `921-29e12ff3`. It also runs the midm text gate as a second check. That gate took 110 states out of the library before the first build. These are the families 860r25d, 921r25c921, 922r25self, 984r25d, 861ns25v and 921ns25v. All of them reach the held 921 Samanyu tree.

Item 4 stopped at 13:04 UTC. 43 of the 44 saved builds repeat an (n, corner) pair whose built floor is already measured above the base. The first rebuilt ones landed on the same floors: 934 at +8.9e-5 side and 873 at +5.2e-4.

The coordinator followed 169 fresh donors and module handoffs of the other lanes. It refused 90 layouts whose full ancestry it could not walk to the end. Most of them were modules and invent layouts at 805 (31), 748 (15) and 650 (11). It could not read 407 layouts as two flush arms and a rest, and it held back 304 donors with a missing or excluded record.

### 13.2 Item 2 with the deletion and hop step

Round 25 built plain exact-f corners for 866 and 935. None of their 27 states closed a target. This round added the round 17 step to each exact-f corner: one square out of each class 1 corner, then hops. The tool is [`tools/stair-c/r26/exactf.py`](../tools/stair-c/r26/exactf.py).

The first batch used two 9-arms at 804, 862, 924, 987, 860 and 863. It used two 7-arms at 805, 816 and 875, and two 8-arms at 997. The worker ranked each package over its 35 to 38 slice counts. None of these packages ranked a row at its own target.

The 860 package was the exception that paid. Its class 0 corner of 117 squares loses 3.52 squares after the deletion and hops. A build of 860 on it ended 1.41e-4 of side above the base. Its row predicted 4.49e-3 above. The recut of that near layout then built 921 to 1.69e-4 above the base.

The second batch went to the low-f neighbours of 860, f = 0.79 to 0.81: 803, 861, 919, 920, 981 and 982. The class 0 corner of 117 squares led again, with losses of 3.52 to 3.79. These packages ranked rows at their own targets 920 and 982, and at 801, 858, 859, 860, 919, 921, 983, 984 and 985. The best 920 build ended 1.56e-4 of score above the base.

A third batch ran the same request with seed 27 and 8-minute hops at 860, 861, 919, 920 and 982. It also ran 921 with seed 26 at its own f of 0.813. The longer hops lowered the 860 loss from 3.5244 to 3.5150. The 921 corner at f 0.813 kept 124 squares at a loss of 4.074.

The recuts closed most of the gap at three counts, but none went below the base:

| n | best build, score above the base | route |
| --- | --- | --- |
| 921 | 1.48e-6 | 860 recut corner, held 921 far zone, 804 recut far zone, stacks 12 and 13 |
| 863 | 1.60e-6 | recut of the 804 / z9 / 985 chain |
| 860 | 4.81e-6 | recut of the exact-f 860 corner |

### 13.3 The import queue and the second CAP level

At 13:45 UTC each box held 35 to 37 fresh packages that it had not imported. The worker imported on 2 turns of 12, and a turn of a build or a request takes 1 to 10 minutes. In the same time it built rows predicted 0.003 to 0.008 above the bar. 29 such builds came no closer than 1.0e-3 of side.

The worker now imports a fresh package first, unless the top build predicts a side within 0.002 of the bar. The first agent's CAP rule had not reached the boxes. It went out now, limited to rows more than 0.002 above the bar, so rows of fresh donors at 805, 934 and 997 keep their builds. [`control_fresh.py`](../tools/stair-c/r26/control_fresh.py) checks both rules. It passed on the new worker. It failed on two changed copies, one with the import test reversed and one that skips every row.

At 15:16 UTC boxC had built 873 42 times with no gain, all on rows 6e-5 to 1e-4 above the bar that only rebuild the held 873. A second CAP level now builds only rows predicted below the bar after 24 builds of one count with no gain. The control passed on it, and a changed copy that ignores the level failed.

### 13.4 Results

No row certified below the base bar, so the take is empty. The workers made 340 full builds and 348 SLP exports over 22 counts. No stage failed its source check, and the worker refused two starts.

Some builds ended a hair under the base: 804, 873 and 997 at -4.9e-11 of score and 924 at -8e-12. They rebuild the held layouts, and the difference is float noise. The rule needs more than 1e-10, so they do not count. The best 805 build ended 3.04e-6 under the base, but the modules lane holds 805 at 9.08e-6 under it, so our 805 is 7.35e-6 behind that take.

The soft lane certified 814 from a composition of this round. It sits 4.35e-6 below the base in the soft take, so the gain stays there. The quench and modules takes of 748 cite our ancestry proofs for their 805 parents. The proof files stay in the take dir.

The [result table](../results/stair-c-r26-2026-11-14.tsv) lists every full build and SLP export, with its source check.

### 13.5 Next

1. Recut the three closest counts again: 921, 863 and 860. Run more seeds and longer hops on the exact-f corner at f 0.80. They ended 1.5e-6 to 4.8e-6 of score above the base. The seed 27 run with 8-minute hops lowered the 860 corner loss from 3.5244 to 3.5150.
2. Run the exact-f deletion and hop step only near f 0.80. It is the one new design of this round that moved targets: 860 from a row predicted 4.49e-3 above to 1.41e-4 of side. The ten first-batch targets at other f ranked no row at their own count.
3. Skip a row whose composition is the held layout itself. 873 took 110 builds and 997 took 64. They only reproduced the held layout within 5e-11.
4. Do not follow 805 again unless a new corner appears. Our best 805 is 7.35e-6 behind the modules take, after 68 builds.

### 13.6 Final measurement and cleanup

The workers stopped at 16:46 UTC. Receipt checks verified every payload hash: 1819 files from boxC, 1604 from boxD and 1827 from boxE. The saved queues hold 96 pending builds on boxC, 57 on boxD and 112 on boxE. The coordinator stopped after one last collect. Each box scratch dir was removed after its receipt matched, with no process left. The shared boxE runtime stays in place. No Kaggle submission ran.


## 14. Round 27

The lane used the round 27 bar and compared every candidate with the live round 27 takes.
One serial worker ran on each of boxC, boxD and boxE.
Search ended at 23:15 UTC and all long jobs ended by 23:45 UTC on November 14.

The source gate reopened the Samanyu seed tree under the round 27 override.
It restored 106 of the 110 states removed in round 26.
The library held 2,567 states after 350 source or share refusals.
The prvsiyan share test and the other excluded sources stayed in force.
The source control accepted the reopened seed and rejected the excluded public roots.
The share control rejected 818, 706 and 971, and accepted the independent 921 and 860 designs.
Every new donor was copied with its SHA256 before dispatch.

The coordinator now reads the current rectangle part records.
Both the producer and assembler walkers must pass.
Each accepted rectangle keeps its full walk snapshot and source notices.
The 863 positive control passed, and a missing-part copy failed.

At adoption, live packets had waited up to 54 minutes behind reopened packets and close builds.
The replacement worker reserved every third turn for a live import.
Every twelfth turn chose the oldest live packet.
The existing import and build-cap controls passed.
Four new cadence cases passed, and always-import and never-import mutants failed.
The workers resumed their saved queues after their current jobs finished.

Each new live corner gets one build after the count cap.
Repeats of that corner keep the cap.
The control built the first new corner and skipped its repeated build.
The 871 and 932 certified-file probes both worsened their inputs.
The wrapper kept each better input, and neither probe entered the take.

Exact-f runs added new seeds and longer hops near f 0.80.
Seed 28 at 860 lowered corner loss to 3.5132, against 3.5150 in round 26.
The 920 seed-28 corner reached 3.5109.
New requests then tried seeds 30 and 31 with 16-minute hops at the live fraction.
These losses describe modules. Only certified full layouts count in the take.

The workers exported 292 full builds and 294 SLP stages across 19 counts.
The final take retained 0 counts, with score gain 0 against the round 27 bar.
The gain beyond the other live takes was 0.
The [result table](../results/stair-c-r27-2026-11-14.tsv) records each exported stage and its source screen.

All three remote receipts passed SHA256 verification before scratch removal.
Changed-byte controls failed, and the sibling scratch control passed.
The local coordinator stopped before the final snapshots.
No lane process remains on the worker boxes.


## 15. Round 28

The lane used bar28 and the live round 28 takes.
One serial worker ran on each of boxC, boxD and boxE.
Search ended at 05:25 UTC on November 15. All long jobs had a 05:45 UTC deadline.

The initial source pass kept 2202 states and deferred or rejected 619.
RULE001903 then reopened own geometry matches and their descendants.
The first pass repriced 25 admitted unrun recipes.
The saved queue keeps all 1,426 unrun recipes separate from 2,923 completed recipes.
Each input kept its byte snapshot and SHA256 before dispatch.
At 00:19 UTC the main handoff relayed the new source rule. Own layouts and their descendants do not fail on geometry share.
The updated controls admitted own construction, held 801, seeds 503/983 and the own n684 tree. Recorded excluded-file ancestry still fails.
The fresh import, count cap, live cadence and new corner controls passed.

A real certified-975 fq control completed with return code 0 in 6.81 seconds.
Its output worsened the input, so the wrapper preserved the better certified input.
Close whole rectangles without two flush arms also received one certified-file fq pass. A dry plain probe then qualified for one bounded kick leg.
The inflated-975 kick control recovered 0.00770 side in 60.07 seconds, then completed certified-file fq in 5.05 seconds.
The first n918 kick shortened side by 0.00000450 and still missed the bar. A new seed supplied one continuation.
The first n871 kick shortened side by 0.0000023945 and still missed the bar.
Its continuation reached bar28 side to within 0.000000000054, with no counted gain.
Own near compositions within 0.00002 side of the live bar also received a follow.
Full CSV source controls admitted n805 and n812. The n871 follow also passed its full walk.
Module records missed unresolved parents in n804, n995 and n997 follows. Those follows remained uncounted.
Publication now requires a full CSV source walk for every score candidate.
Pending jobs now use the latest live bar before each build.
When a bar falls, the cap counts completed recipes against that bar.
The queue control repriced old n805 to +0.000325 side and gave n812 priority.
SLP and full stages count as one recipe. Unfinished recipes do not count toward the cap.
The live-bar cache invalidated a lower replacement. The certificate cache rejected a changed overlapping CSV.
The final archive holds 25 whole-layout receipts.

Of these, 24 completed the final certified-file fq invocation.

Fresh layouts and rectangle handoffs preceded the saved queue.
Each readable fresh layout supplied a corner and far zones to all three workers.
A new corner received one full build after the count cap. Repeated corners kept the cap.
The unchanged exact-f seed and hop campaigns stayed closed because round 27 reached the same loss floors.

An n805 composition reached score 0.0164302490798085, gaining 0.000141661374949642 against bar28.
Rebuild later improved a pinned copy of an earlier stair-c n805 composition.
The final take removed any row beaten by another live take.

The workers exported 586 full builds and 588 SLP stages across 32 counts.
At archive time the take retained 0 counts, gaining 0 against bar28.
The gain beyond the other live takes was 0.
Every retained row required a completed fq invocation from its certified file and a fresh floatsafe check at 2.2e-11.
The [result table](../results/stair-c-r28-2026-11-14.tsv) lists measured builds and their source screens.

All remote copies passed SHA256 verification before scratch removal.
The shared runtimes remain in place. No lane worker remains.


## 16. Round 29

One serial worker ran on each of boxC, boxD and boxE.
Fresh compositions and changed rectangle inputs preceded saved recipes.
The source pass retained 3002 module states and repriced 97 pending recipes against bar29.
The unchanged exact-f hop campaign stayed closed after its round 27 loss floors.

Each queued input kept its byte snapshot and SHA256.
Own layouts and their descendants had no share or ancestor-share test.
Direct public starts retained the licence and share checks.
Recorded excluded-file ancestry stayed out.

The import, count-cap, new-corner, live-bar and saved-recipe controls passed.
The controls now account for the queue sort before checking which build runs.
The certified n975 control passed, and a duplicate-square copy failed.
The larger-corner control moved complete flush stacks into the corner before tabulation.
Four n975 assemblies kept side 31.714095652247682, with worst gap about -2.6e-12.
A partial-stack mutant failed. The experiment used admitted inputs at n805, n812, n871 and n997.
The bar-probe control rejected a false low prediction, then built n975 at side 31.714095650717713.
Failed starts could then probe near the live bar. Four failed probes cap one count and corner.
The cap preserves a first fresh corner, and a changed-cap mutant failed.
One n997 corner failed 23 cross-count bar probes.
Five corner paths still refused two measured n882 recipes.
A table-knot replay at n945 and fraction .995 explained the false prediction.
Its corner escaped beyond the declared cut, producing a full-layout gap of -1.0948843355167908.
That exact corner closed for cross-count builds. Native n997 recipes remained open.
Skipped recipes moved into the deferred queue. A control preserved both deferred and pending recipes.

A new guard checked corner supports against their original cut allowances.
All four n975 assemblies passed, and the observed escaped corner failed the guard.
Three new guarded corner IDs from n997 then ran through the serial workers.
The guarded n945 replay had no table fit and refused the physical corner in 25.103 seconds.
Guarded corners produced 0 full layouts.
A physical replay identified the collision between corner square 65 and later run square 180.
The next model included three following flush stacks in each local arm.
Four n975 source assemblies passed at side 31.714095652247682.
A duplicate of a free square in the following run failed the local legality check.
The changed n945 replay refused the corner in 16.357 seconds.
New corner IDs from n871 and n997 then ran through the workers.
Corners with following stacks produced 18 full layouts.
Three further n975 controls moved two whole stacks into the free corner.
They preserved side 31.714095652247682. An incomplete-stack mutant failed.
Two-stack transfers produced 6 full layouts.
Known native recipes also ran directly from their module geometry, without tables used only for ranking.
The direct n975 control passed at side 31.714095650716718 and positive gap.
A corner-path control found later feasible paths after the original first path refused.
It preserved fixed source geometry before trying rotation.
Direct native recipes produced 9 full layouts.

Expanded corners produced 41 full layouts.
Bar probes produced 0 full layouts and 50 failed starts.
Certification used border's bisected dilation at clearance 2.2e-11.
Each published row required a completed fq invocation from its certified file.

Whole-layout follows included 900-second kicks on the three workers.
One n986 kick shortened its input by 6.81061522e-6 of side, then reached the existing bar.
A proposed source-locator repair failed the full n986 proof control and was reverted.
Withdrawals named pinned bytes. Controls kept replacement bytes at a reused path eligible.

A later byte recovery restored 90 states held by the initial path checks.
It recovered 8 exact input versions from 7 original paths.
Each version passed the full source proof. A wrong expected hash failed.
Copied source records kept content hashes, and the frozen files stayed unchanged.
One original path needed two byte versions, so rebinding selected the recorded hash.
A bounded first build for each changed physical corner preceded the normal live-bar order.
The priority control passed. A mutant with priority disabled failed.
Repeated corners returned to the count caps.
Recovered modules appeared in 8 full builds.

The saved queue contained 1242 exact unrun recipes.
Of these, 194 named recovered module states.
The queue builder derived unrun status before source admission and included deferred jobs.
Recorded full layouts and SLP stages remained completed.
Controls deferred missing modules, admitted recovered geometry once and kept measured recipes closed.

A late audit found failed follow offers from before the certificate directory existed.
The directory writer now creates the parent and resumes an identical certified input.
Controls reject changed input hashes and coordinates.
Failed offers now retry, and an untraced best row can yield to a source-admitted row.
The retry and fallback controls passed.
The real n812 offer passed its full source proof and queued a 900-second kick.
The repair admitted 4 new offers.

Table search ended at 11:25 UTC. Queued kicks could run until 11:38 UTC.
The deadline control reserved 150 seconds for their final certified-file quench.
Collection began at 11:42 UTC. Each worker stopped before its archive.
The archive deadline was 11:45 UTC.

A final variant capped the box side sent to fq at the live bar.
The n975 control requested 31.714095652247682 instead of 31.724095652247684.
Its returned geometry had side 31.716080734071944 and gap 1.09166e-10.
Returned sides stayed unmodified. A duplicate-square mutant failed.
The n812 variant then ran with the remaining kick window through 11:38 UTC.

The workers exported 280 full builds and 280 SLP stages across 22 counts.
At collection, the take retained 0 counts, gaining 0 against bar29.
The gain beyond other live takes was 0.
The [result table](../results/stair-c-r29-2026-11-15.tsv) records measured stages and their source screens.
The detailed follow receipts and saved queues remain in the take work directory.

All three remote archives passed SHA256 verification before own scratch removal.
The shared runtimes remain in place. No lane worker remains.

The late n812 bar-input leg used seed 3912 for 332.992 seconds.
It shortened its input by 4.90988817958e-06 of side.
Its certified side was 28.923083462325636, only 1.46939527212e-09 below the queued live bar.
The score gain was 5.15656650782e-11, below the 1e-10 requirement.
The earlier input-side leg used seed 3612 and shortened 5.69085e-9 in 901 seconds.
These legs used different seeds. A paired test with identical seeds remains open.

The cached following-stack library contains 18 corners and their tables.
It remains in `take-stair-c-r29/work/following-stack-library`.
Install [corner_stacks.py](../tools/stair-c/r29/corner_stacks.py) before using those tables to build.
Try the changed n805 corners at n748, outside this lane's slice.
The round 28 corner transfer to n748 gained 0.000141661 before a peer improved it.


## 17. Round 30

One serial worker ran on each assigned box: boxC, boxD and boxE.
The restored library kept complete source proofs and byte hashes.
Fresh compositions preceded saved recipes. Completed recipes stayed closed.
The physical corner model included following flush stacks.
Own layouts had no share gate. Public starts retained licence and source checks.

The workers exported 386 full builds and 389 SLP stages across 12 counts.
The final take retained 1 counts, gaining 5.74009938936193e-06 against bar30.
Certification used border finesafe at clearance 2.2e-11.
Each retained row required a remote fq pass from its certified file.
The [result table](../results/stair-c-r30-2026-11-15.tsv) records the builds and source screens.
Full experiment receipts and exact saved queues remain in the take work directory.

Matched n812 seed3912: input-side shortening 0, bar-input shortening 4.90988817958e-06 of side.
Matched n812 seed4912: input-side shortening 4.79429262157e-06, bar-input shortening 5.6825797401e-09 of side.
The two matched seeds preferred different input-box variants.
Neither paired comparison supplied a counted row.
Recovered 78 module states from 13 exact input paths after full source proofs. The wrong-hash mutant failed.
CSV source checks could use the module feeder's whole time budget.
The module feeder now has its own budget and reads the newest libraries first.
Its live control admitted 1 fresh module states in 95.951s.
By collection, the repaired feeder admitted 547 more module geometries.
Request-file changes and partial packets each have their own queue identity.
The public-root audit checked 985 source groups and deferred 60. Owned layouts received no share test.
The cached n805 corners reached public-first n457, whose share was 1.0.
Those source versions were removed from the worker libraries after the audit.
The n995 proof passed through public n462, whose share was 0.23809523809523808.
The worker bar omitted the lane's own n995 take.
20 builds returned to its floor while comparing with the older bar.
The corrected worker bar includes the certified own take.
A changed far zone keeps one first build after a count cap. Its repeat remains capped.
The far-zone, corner and count-cap controls passed.
The score baseline stays fixed at bar30.
All 1,000 rows matched the brief, and a synthetic later BASE line could not alter them.
No actual BASE line existed, so this changed no measured gain.
Plain near follows now clear inherited kick fields.
Four real inherited records passed the control.
Explicit self-follows retain the kick, while plain fq checks keep their previous receipts.
Command receipts identified 10 already attempted saved recipes.
The n813 timeout had repeated under r29 and r30 names without an exported layout.
The corrected queue closes those attempts and preserves never-run jobs.
Certificate results persist under exact input and checker hashes.
A real n995 disk replay matched its certificate. A duplicate-square copy failed.
The diagnostic measurement exceeded 200 seconds in a nested source walk.
Bounded diagnostic checks finished in 70.717s and deferred 711 source screens.
Retained rows required completed source proofs and actual fq receipts.
Contact LP shortened the n812 bar result by 2.89222867877e-10 of side.
Its certified side was 28.9230834620364.
The following fq completed and preserved the better LP certificate.
Contact LP on n995 changed its certified side by 0.
Its certified side was 31.9446526771044. The following fq completion flag was True.


All remote archives passed SHA256 verification before scratch removal.
The shared runtimes remain in place.


## 18. Round 31

One serial worker ran on each assigned box: boxC, boxD and boxE.
The workers exported 343 full builds and 346 SLP stages.
After collection, the take retained 2 counts with gain 2.95079619405669e-07 against bar31.
Border finesafe certificates used clearance 2.2e-11.
Each retained row completed remote fq from a certified input.
Fresh matched inputs supplied the n=805 gain. Held probes supplied n=342.
The changed n=805 follow later recovered the existing best.
Own layouts received no share gate. Direct public roots retained both share tolerances and licence checks.
The local SciPy import stalled during finalization. Exact-byte cached certificates preserved the numerical checks.
All remote archives passed SHA256 verification before scratch removal. Shared runtimes remain in place.
The [result table](../results/stair-c-r31-2026-11-16.tsv) records the exported stages.


## 19. Round 32

One serial worker ran on each assigned box: boxC, boxD and boxE.
The restored library kept complete source proofs and byte hashes.
Fresh compositions preceded saved recipes. Completed recipes stayed closed.
The physical corner model included following flush stacks.
Own layouts had no share gate. Public starts retained licence and source checks.

The workers exported 315 full builds and 317 SLP stages across 21 counts.
After collection, the take retained 1 count, gaining 1.53446739759033e-08 against bar32.
A final live peer check removed any late superseded rows before the take froze.
Certification used border finesafe at clearance 2.2e-11.
Each retained row required a remote fq pass from its certified file.
The [result table](../results/stair-c-r32-2026-11-16.tsv) records the builds and source screens.
Full experiment receipts and exact saved queues remain in the take work directory.

New n805 compositions received matched input-box trials.
Each pair used identical certified bytes, a shared seed and both box variants.
Initial plain held probes stayed closed after the dry round31 measurements.
Source checks used both withdrawal logs and the frozen assembler measure.


All remote archives passed SHA256 verification before scratch removal.
The shared runtimes remain in place.

The final live check removed n805 after backlog improved this lane's input.
Backlog retained a total score gain of 1.94329181635e-8 against bar32.
The copied peer scanner still read round31 takes. It now reads round32.
An independent scan removed the duplicate before the take froze.
A positive fixture checked the corrected scanner against a round32 peer.


## 20. Round 33

One serial worker ran on each assigned box: boxC, boxD and boxE.
The restored library kept byte hashes and source records.
Full output walks found additional untraced module versions.
The scheduler gave fresh module packets regular import turns.
Completed recipes stayed closed.
The physical corner model included following flush stacks.
Own layouts had no share gate. Public starts retained licence and source checks.

The workers exported 731 full builds and 733 SLP stages across 21 counts.
After collection, the take retained 0 counts, gaining 0 against bar33.
A final live peer check removed any late superseded rows before the take froze.
Certification used border finesafe at clearance 2.2e-11.
Each retained row required a remote fq pass from its certified file.
The [result table](../results/stair-c-r33-2026-11-17.tsv) records the builds and source screens.
Full experiment receipts and exact saved queues remain in the take work directory.
The sparse975 control compared retained grid points with the complete cached table.
New physical805 corners used sparse tables after that control passed.
Construction805 had one owner, while the other workers ran its paired quenches.
Every candidate required the full default-plus-polish fq loop before publication.
The native805 failures exposed a small overlap between adjacent core cells.
The repair propagated slide offsets along each core edge.
Four repaired805 starts passed finesafe controls before production builds.
A peer take retained the repaired805 output, gaining 1.773492464e-10 against bar33.
This take counts no duplicate.
The [core-slide helper](../tools/stair-c/r33/slide_envelope.py) records the repair.
The [source reader](../tools/stair-c/r33/trace27.py) verifies exact submitted-row module bindings.

Changed n805 compositions were screened for matched input-box trials.
Each pair used identical certified bytes, a shared seed and both box variants.
Whole-row held probes stayed closed. Fresh corner transfers used the current held geometry.
Source checks used round31, round32 and round33 withdrawals and the frozen assembler measure.


All remote archives passed SHA256 verification before scratch removal.
The shared runtimes remain in place.
