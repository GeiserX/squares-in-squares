# Avenue: farend (2026-11-12, round 19)

**Result: no n certified. By its letter the kill line did not fire, and for the score the lane is dry all the same.**

For an arm of 8, the best far end that is not a taper is 0.21 to 0.27 squares under the taper of its class. That holds at f = 0.66, 0.70 and 0.74. For an arm of 9 it is 0.02 to 0.17 under at f = 0.68, 0.72 and 0.76. The library already holds those far ends, except one. Four far ends are new. One is class 7 of an arm of 8, 0.16 to 0.22 squares under the library. Three are classes 4, 0 and 2 of an arm of 7, 0.33 to 0.59 under. The class 4 far end of an arm of 7 loses 2.165 squares at f = 0.70. That is 0.26 under the far end of the arm of 7 in held 634, so it meets the go line. None of the four gives a layout under held. The nearest build is 977, 0.000434 of side above held.

An arm of a two-arm layout ends at a wall. The tilted stacks cannot run into the wall, so the last part of the arm is a different packing. We call it the far end. Every far end we hold is a taper: shorter and shorter pieces of the tilted stacks, with columns of upright squares on the wall. The lane asks one question. Is there a far end that is not a taper and loses less?

Words used here. "Held" is `gather/round17-2026-11-12a.csv` with the gate dir `gate/cand-round17-1112a`. The side is `L = m + f` and `k = n - m²`. An arm of `c` is a strip of width `W = c - 1 + f` that holds stacks of `c` squares, all at the flush tilt `t` with `c cos t + sin t = W`. A stack takes `1 / cos t` of the length of the arm. A far zone is the far end as a module: `N` squares in the strip, from the end wall to the last flush stack, with the length `lam`. Its loss is `c cos t × lam - N`, in squares: the squares that flush stacks of the same length would hold, less the squares it holds. Its count class is `N mod c`. A layout needs a far zone of one class on each arm, and which class comes from `n`. "The taper" of a class is the lattice taper with the lowest loss in that class: `zone_search.py taper` counts every one of them. "The library" is the module library of round 17, `take-modules-r17/work/lib17`, with 2,857 far zones. "The generator" is `modules.py queue`. It gives the predicted side of every choice of a corner, two far zones and two stack counts, and a "row" is one such choice. "The bar" of an `n` is the lowest side that held or any take dir of round 17 or 19 has for it. "The arm bar" is a different number, a far-end loss, and section 1 gives it.

The tools are [`farend_read.py`](../farend_read.py), [`farend_search.py`](../farend_search.py), [`farend_rows.py`](../farend_rows.py) and [`farend_ceiling.py`](../farend_ceiling.py). They import `zone_search.py`, `modules.py` and `frontier_stacks.py` and change none of them. The table of every measured far end is [`results/farend-r19-2026-11-12.tsv`](../results/farend-r19-2026-11-12.tsv).

## 1. Kill line and control (written 2026-11-12 20:21 UTC, before the first search)

**The lane is dry when the best new far end is within 0.1 squares of the taper of the same count class. That must hold at three f, for an arm of 8 and for an arm of 9.**

The f are 0.66, 0.70 and 0.74 for the arm of 8, and 0.68, 0.72 and 0.76 for the arm of 9.

**Go line: a far end gets generator rows and builds when it is 0.2 squares or more under the arm bar.**

The arm bar is the lowest far-end loss of the held layouts with that arm. It is 2.85 squares for an arm of 8, 3.27 for an arm of 9 and 4.27 for an arm of 11.

Positive control, which can fail: our own reading of the far ends of three held layouts must match the numbers of the invent lane to 0.05 squares. `farend_read.py` cuts a held layout into modules with `modules.cut` and measures each far zone with `zone_search.length`. The invent lane measured the same far ends with its own code, and its numbers are in `results/round17-invent-parts.tsv`.

**The control passed.** Six far ends, largest difference 0.033 squares:

| n | arm | our reading | invent lane | difference |
|---|---|---|---|---|
| 634 | 7 | 2.429 | 2.435 | 0.006 |
| 634 | 8 | 2.795 | 2.820 | 0.025 |
| 740 | 8 | 2.793 | 2.794 | 0.001 |
| 740 | 8 | 2.793 | 2.794 | 0.001 |
| 747 | 10 | 3.996 | 4.029 | 0.033 |
| 747 | 6 | 1.614 | 1.617 | 0.003 |

Held 639, 687 and 979 were asked for too. The cut refuses them, because they do not have two flush arms.

A second control ran before the search. The taper table of `farend_search.py` for an arm of 8 at f = 0.70 is 3.06, 2.77, 3.33, 3.36, 3.07, 3.47, 3.08, 3.33 for the classes 0 to 7. It equals the table of the [zones](zones.md) avenue.

## 2. Where a far end loses its squares

The tilted stacks meet the end wall at the angle `t`. The wall cuts `W sin t` stacks, and a taper loses about one square for each of them.

| arm | f | tilt | stacks cut, `W sin t` | cost of one row of uprights |
|---|---|---|---|---|
| 8 | 0.66 | 25.3° | 3.27 | 0.233 |
| 8 | 0.70 | 24.4° | 3.18 | 0.287 |
| 8 | 0.74 | 23.4° | 3.07 | 0.343 |
| 9 | 0.68 | 22.9° | 3.38 | 0.291 |
| 9 | 0.72 | 22.0° | 3.26 | 0.346 |
| 9 | 0.76 | 21.0° | 3.14 | 0.401 |
| 11 | 0.70 | 19.6° | 3.58 | 0.365 |

The last column is the price of a class. A row of `c - 1` uprights on the end wall under a far zone adds `c - 1` squares and one unit of length. The zone then serves the class below, and its loss rises by `c cos t - (c - 1)`.

The loss of the taper depends on the class, and the spread is the reason for the lane. For an arm of 8 at f = 0.70 the cheapest class loses 2.77 squares and the dearest 3.47. For an arm of 9 at f = 0.72 they lose 3.30 and 4.12.

## 3. The designs

Measured designs, all in `farend_search.py`:

| design | what it is |
|---|---|
| `less` | One square deleted from the taper of the class above, then hops. This is the one-less step of the [stair-c](stair-c.md) corners, on a far end. |
| `more`, `morex` | One square put into the largest pocket of the taper of the class below, then hops. `morex` tries every distinct taper and four pockets. |
| `share1`, `share2` | The far end takes one or two cells of the first grid column on the end wall. Their squares become squares of the zone, so the grid across the wall is no longer rigid there. |
| `retilt` | One stack of the taper at a time turns about its centre by 3, 6, 10 or -3 degrees. The turn stays when the zone gets shorter. Then hops. Starts: every distinct taper of the class, and each with one more flush stack. |
| `less+`, `more+` | `less` and `more` again, from the best zone that any design found, with the turns before the hops. |
| `hop` | Hops alone on the taper. It is the control of the other designs: it shows how much of a gain is the hops. |
| `cut` | One square less or one more on the lowest far zones that the library holds for the class above and below. The start is a far zone of a built layout where the library has one, and not a taper. |
| `turn` | The turns of `retilt` on a far end that another design saved. |

Designs that we did not run, each with the arithmetic that rules it out:

- **A staircase far end.** The staircase corner of the [twoshort](twoshort.md) avenue is columns of uprights of falling height against the tilted stacks. At a far end that is a lattice taper: the taper count has the column heights as its state and counts every staircase. The best staircase of each class is the taper itself.
- **A fan.** Bars of `c - 1` squares turn from the tilt `t` down to upright. The gaps between the bars sum to `(c - 1)² t / 2`, which is 10.4 squares for an arm of 8 at f = 0.70. A taper loses 3.
- **Stacks that lean the other way.** A second lattice with the opposite lean leaves a wedge of about 34 squares where the two meet.
- **A third arm on the end wall.** It would cost `c (1 - cos t)` squares for each unit of its length, and the grid would have to give up a column.
- **Shared rows with the grid in general.** The grid across the wall has no slack in either direction. So a far end can share with it in two ways only. It takes whole cells, as the `share` designs do. Or the first grid column slides, and the library holds those zones as slid twins. A tilted square that pokes over the wall of the strip rises by `sin t`, about 0.41. The grants of the corners stop at 0.16.

The taper count of `zone_search.py` works for arms up to 10, so an arm of 11 had no search.

## 4. What the designs measured

Each table has one arm at one f. "Taper" is the lowest lattice taper of the class. "Library lowest" is the lowest loss that the library holds for the class at that f. A design that ends on the taper or above it is "none below the taper". The numbers are squares.

**Arm of 8 at f = 0.66**

| class | taper | best far end that is not a taper | its loss | against the taper | library lowest | against the library | designs tried |
|---|---|---|---|---|---|---|---|
| 0 | 2.860 | not run | | | 2.860 | | |
| 1 | 2.628 | not run | | | 2.628 | | |
| 2 | 3.451 | none below the taper | 3.451 | +0.000 | 3.451 | +0.000 | retilt |
| 3 | 3.279 | none below the taper | 3.279 | +0.000 | 3.279 | +0.000 | retilt |
| 4 | 3.046 | not run | | | 3.046 | | |
| 5 | 3.209 | none below the taper | 3.209 | +0.000 | 3.209 | +0.000 | retilt |
| 6 | 3.285 | retilt | 3.014 | -0.272 | 3.014 | +0.000 | retilt |
| 7 | 3.093 | none below the taper | 3.093 | +0.000 | 3.093 | +0.000 | retilt |

**Arm of 8 at f = 0.70**

| class | taper | best far end that is not a taper | its loss | against the taper | library lowest | against the library | designs tried |
|---|---|---|---|---|---|---|---|
| 0 | 3.057 | none below the taper | 3.057 | +0.000 | 3.057 | +0.000 | more, more+, retilt |
| 1 | 2.769 | none below the taper | 2.769 | +0.000 | 2.769 | +0.000 | more, retilt |
| 2 | 3.332 | none below the taper | 3.332 | +0.000 | 3.332 | +0.000 | less, more, morex, retilt, share1 |
| 3 | 3.357 | none below the taper | 3.357 | +0.000 | 3.357 | +0.000 | less, more, morex, retilt, share1 |
| 4 | 3.070 | none below the taper | 3.070 | +0.000 | 3.070 | +0.000 | more, retilt |
| 5 | 3.469 | none below the taper | 3.469 | +0.000 | 3.165 | +0.304 | hop, less, less+, more, morex, retilt, share1, share2 |
| 6 | 3.080 | less | 2.876 | -0.205 | 2.852 | +0.024 | less, less+, more, retilt |
| 7 | 3.326 | more | 3.170 | -0.156 | 3.326 | -0.156 | less, more, more+, morex, retilt, share1 |

**Arm of 8 at f = 0.74**

| class | taper | best far end that is not a taper | its loss | against the taper | library lowest | against the library | designs tried |
|---|---|---|---|---|---|---|---|
| 0 | 3.268 | none below the taper | 3.268 | +0.000 | 3.268 | +0.000 | more, retilt |
| 1 | 2.925 | none below the taper | 2.925 | +0.000 | 2.925 | +0.000 | more, retilt |
| 2 | 3.459 | none below the taper | 3.459 | +0.000 | 3.459 | +0.000 | more, retilt |
| 3 | 3.713 | none below the taper | 3.713 | +0.000 | 3.713 | +0.000 | more, retilt |
| 4 | 3.436 | none below the taper | 3.436 | +0.000 | 3.436 | +0.000 | more, retilt |
| 5 | 3.328 | more | 3.118 | -0.210 | 3.118 | +0.000 | more, retilt |
| 6 | 2.957 | retilt | 2.775 | -0.182 | 2.775 | +0.000 | more, retilt |
| 7 | 3.284 | more | 3.062 | -0.221 | 3.284 | -0.221 | more, retilt |

**Arm of 9 at f = 0.68**

| class | taper | best far end that is not a taper | its loss | against the taper | library lowest | against the library | designs tried |
|---|---|---|---|---|---|---|---|
| 0 | 3.243 | none below the taper | 3.243 | +0.000 | 3.243 | +0.000 | retilt |
| 1 | 3.433 | none below the taper | 3.433 | +0.000 | 3.433 | +0.000 | retilt |
| 2 | 3.997 | more | 3.951 | -0.046 | 3.997 | -0.046 | more, retilt |
| 3 | 3.744 | none below the taper | 3.744 | +0.000 | 3.744 | +0.000 | retilt |
| 4 | 3.935 | none below the taper | 3.935 | +0.000 | 3.935 | +0.000 | more, retilt |
| 5 | 4.190 | none below the taper | 4.190 | +0.000 | 4.190 | +0.000 | more, retilt |
| 6 | 3.932 | none below the taper | 3.932 | +0.000 | 3.932 | +0.000 | retilt |
| 7 | 3.825 | none below the taper | 3.825 | +0.000 | 3.825 | +0.000 | retilt |
| 8 | 3.534 | none below the taper | 3.534 | +0.000 | 3.534 | +0.000 | retilt |

**Arm of 9 at f = 0.72**

| class | taper | best far end that is not a taper | its loss | against the taper | library lowest | against the library | designs tried |
|---|---|---|---|---|---|---|---|
| 0 | 3.409 | none below the taper | 3.409 | +0.000 | 3.409 | +0.000 | more, retilt |
| 1 | 3.300 | none below the taper | 3.300 | +0.000 | 3.300 | +0.000 | retilt |
| 2 | 4.123 | none below the taper | 4.123 | +0.000 | 4.123 | +0.000 | less, more, retilt, share1 |
| 3 | 3.778 | none below the taper | 3.778 | +0.000 | 3.778 | +0.000 | less, more, retilt |
| 4 | 3.669 | none below the taper | 3.669 | +0.000 | 3.669 | +0.000 | more, retilt |
| 5 | 3.995 | retilt | 3.984 | -0.011 | 3.995 | -0.011 | less, more, retilt, share1 |
| 6 | 3.932 | none below the taper | 3.932 | +0.000 | 3.932 | +0.000 | less, more, retilt, share1 |
| 7 | 4.100 | more | 3.932 | -0.169 | 3.932 | +0.000 | less, more, retilt, share1 |
| 8 | 3.754 | none below the taper | 4.110 | +0.355 | 3.754 | +0.355 | more, retilt |

**Arm of 9 at f = 0.76**

| class | taper | best far end that is not a taper | its loss | against the taper | library lowest | against the library | designs tried |
|---|---|---|---|---|---|---|---|
| 0 | 3.499 | none below the taper | 3.499 | +0.000 | 3.439 | +0.060 | more, retilt |
| 1 | 3.155 | none below the taper | 3.155 | +0.000 | 3.155 | +0.000 | more, retilt |
| 2 | 4.316 | more | 4.300 | -0.016 | 4.316 | -0.016 | more, retilt |
| 3 | 3.953 | none below the taper | 3.953 | +0.000 | 3.953 | +0.000 | more, retilt |
| 4 | 3.924 | none below the taper | 3.924 | +0.000 | 3.924 | +0.000 | more, retilt |
| 5 | 4.121 | none below the taper | 4.121 | +0.000 | 4.121 | +0.000 | more, retilt |
| 6 | 3.928 | none below the taper | 3.928 | +0.000 | 3.928 | +0.000 | more, retilt |
| 7 | 3.707 | more | 3.704 | -0.003 | 3.704 | +0.000 | more, retilt |
| 8 | 3.901 | none below the taper | 3.901 | +0.000 | 3.901 | +0.000 | more, retilt |

The cells that ended under the taper are of two kinds. The first kind is a turned stack: `retilt`, and `less` where it ends in the same zone. It gives 0.15 to 0.27 squares in classes 5 and 6 of the arm of 8. The library holds each of those zones already. The second kind is one square more, `more`. It gives 0.16 to 0.22 squares in class 7 of the arm of 8, and that zone is new. It gives 0.17 in class 7 of the arm of 9, and the library holds that one. Taking cells of the grid (`share1`, `share2`) gave nothing in any class, after 188 to 267 hops each. `hop` alone gave nothing. The rows of `morex` are weak evidence: at f = 0.745 it took a worse start than `more` and ended at 4.175 where `more` gives 3.045.

Four more runs, outside the tables:

- **A start from the library's far zones and not from a taper** (`farend_search.py cut`, arm of 8, f = 0.68 to 0.76, 20 starts). One square less or more on the lowest far zones of the class above and below, the cut zones among them. Class 2: +0.000 and +0.723 against the library. Class 3: +0.249 and +0.539. Class 7: +0.074 and +0.410. Nothing under the library. The control of this step did not pass. On class 7 it had to give 3.17 squares or less, the number of `more` on the taper, and its best was 3.358. So `cut` is a weaker step than `more`, and its zeros on classes 2 and 3 are weak evidence.
- **The lattice tapers of an arm of 9 above the f that the library covers.** At f = 0.80 and 0.84 the tapers equal the library. At f = 0.88, 0.92 and 0.96, 13 tapers are 0.07 to 2.06 squares under it, because the library has only cut zones there. With them in the library, 2 of 138 n get a row within 0.006 of held: 995 at +0.0048 and 984 at +0.0063. No build.
- **An arm of 6 at f = 0.70** with `more`: +0.039 and +1.244 in the two classes that ran.
- **Classes 8 and 0 of an arm of 9 at f = 0.82** with `more`. The ceiling of section 7 puts 6 n on class 8 at f = 0.81 to 0.84, where its taper loses 4.74 squares against 3.44 for class 7. The step gives 4.691 and 4.248. That is 0.047 and 0.001 under the taper, and not under the library. The class 7 taper has no pocket for the square there.

The best new far end of each table:

| arm | f | classes searched | best new far end against the taper | against the library |
|---|---|---|---|---|
| 8 | 0.66 | 5 of 8 | -0.272 | +0.000 |
| 8 | 0.70 | 8 of 8 | -0.205 | -0.156 |
| 8 | 0.74 | 8 of 8 | -0.221 | -0.221 |
| 9 | 0.68 | 9 of 9 | -0.046 | -0.046 |
| 9 | 0.72 | 9 of 9 | -0.169 | -0.011 |
| 9 | 0.76 | 9 of 9 | -0.016 | -0.016 |

## 5. Rows of uprights under the held far zones

A row of `c - 1` uprights under a far zone gives a zone of the class below, at the cost of section 2. The taper count has such rows for the lattice tapers. The library does not have them for the far zones that were cut from built layouts. Those often lose 0.2 to 0.35 squares less than the taper of their class.

`farend_rows.py make` adds a copy of a held far zone with one or two rows under it. A copy is kept when it is 0.01 squares or more under the library at some f between 0.60 and 0.99. The library number is its lowest loss for that arm and class. The length of the copy is the length of the old zone plus the rows at every f, so its table is copied and no LP runs.

79 copies came out for the arms of 8 and 9: 44 with one row and 35 with two. 12 of them serve an arm, a class and an f where the library holds no far zone at all. The other 67, by the f of their largest gain:

| f | copies | gain against the library, squares | largest |
|---|---|---|---|
| 0.60 to 0.65 | 27 | 0.012 to 0.728 | arm of 9, class 6, f = 0.60: 3.595 against 4.323 |
| 0.66 to 0.76 | 10 | 0.012 to 0.060 | arm of 9, class 8, f = 0.76: 3.841 against 3.901 |
| 0.77 to 0.84 | 10 | 0.023 to 0.468 | arm of 8, class 0, f = 0.81: 3.678 against 4.146 |
| 0.85 to 0.99 | 20 | 0.017 to 0.882 | arm of 9, class 4, f = 0.92: 3.938 against 4.820 |

Between f = 0.66 and 0.76 the library already has the rows, to 0.06 squares. That is the band where the zones avenue counted its tapers. Outside it the copies are worth much more, because the library is thin there.

The first run covered the 163 n above 400 with a held f of 0.60 to 0.84. With the copies in the library, the generator gives 42 rows within 0.006 of side of held. `stair-c_bar.py` puts each next to the bar. The nearest:

| n | row less held | bar less held, and who sets it | row less bar | corner, far zones |
|---|---|---|---|---|
| 587 | +0.0010 | 0, held | +0.0010 | `587tw17a.C`, `495h11.F1`, `587st17a.F2+r1` |
| 796 | +0.0021 | -0.0011, twoshort of round 17 | +0.0033 | `zc8x8-98f7134ar.C`, `911h.F2d`, `685h09.F2+r1` |
| 910 | +0.0029 | -0.0006, twoshort of round 19 | +0.0034 | `851tw17a.C`, `z9-44f680.F1`, `910co17.F2+r1` |
| 973 | +0.0037 | 0, family of round 17 | +0.0037 | `913tw17.C`, `910co17.F2+r1`, `851fa17.F2` |
| 984 | +0.0004 | -0.0034, corners of round 17 | +0.0038 | `984st17.C`, `984h.F2+r1`, `z9-43f840.F1d` |
| 854 | +0.0045 | 0, held | +0.0045 | `914tw17.C`, `740h13.F2+r1`, `z9-19f720.F1` |

Two of them were built with `modules.py job` and the family squeeze:

| n | row | built | held | built less held | built less row |
|---|---|---|---|---|---|
| 587 | 24.744788 | 24.744474499 | 24.743771960 | +0.000703 | -0.0003 |
| 796 | 28.723573 | 28.723406290 | 28.721423798 | +0.001982 | -0.0002 |

The 587 row came in three forms that differ in the far zone of the other arm. All three build to the same side. A build with a row copy ends 0.0002 to 0.0003 under its row, so such a row must be within 0.0003 of the bar to certify. None is, and we stopped the builds of 910, 984 and 973. The two built layouts are in `near/` of the take dir.

The second run covered the 137 n above 400 with a held f above 0.84, where the copies gain the most against the library. It gives 9 rows within 0.006 of held, on three n: 810 at +0.0043, 870 at +0.0048 and 754 at +0.0056. No take holds 810 or 870 lower, so their rows are that far above the bar too. No build.

The copies fill real holes of the library, and they are not enough alone. The layouts of those f need more than a cheaper far zone.

## 6. The new zone of class 7, and its build

One design gave a zone that the library does not hold. It comes from `more` on the class 6 taper of 46 squares of an arm of 8. The step puts a tilted single square on top of the upright column at the arm wall, under the first stack. The zone has 47 squares and serves class 7.

| f | the zone | taper of class 7 | library lowest | difference |
|---|---|---|---|---|
| 0.70 | 3.170 | 3.326 | 3.326 | -0.156 |
| 0.74 | 3.063 | 3.284 | 3.284 | -0.222 |

The go line asks for 2.65 squares, 0.2 under the arm bar of an arm of 8. The zone is 0.4 to 0.5 above that, so by the go line it gets no builds. We ran the generator once all the same, to test the line.

`farend_search.py lib` made the module `fe8-47f700mo.F1` from the zone at f = 0.70, with a table of lengths from f = 0.65 to 0.75 by `modules.tabulate`. The run covered the 65 n above 400 with a held f of 0.645 to 0.755. With the module in the library, the generator gives no row within 0.006 of side of held. With a slack of 0.03 the nearest rows are 914 at +0.0065, 913 at +0.0092, 852 at +0.0115 and 853 at +0.0121.

The zero could have been a fault of the step, so it had a control. The same run with the held far zone `495h11.F1` as the needed module gives 587 at +0.0004 and 450 at +0.0027. The step can give rows.

One build, to see how far a build ends from its row: 914 from the corner `914tw17.C`, the new zone and `z9-19f720.F1`, with 14 and 18 stacks. Predicted side 30.735627, built 30.733221, held 30.729164. The build is 0.0024 under its row and 0.0041 above held.

One fault of that first module: its table is good up to f = 0.705 only. Above that the carried zone locks, and its loss rises to 3.69 at f = 0.74, where a search at 0.74 gives 3.06. So the zone found at f = 0.74 became a second module, `fe8-47f740mo.F1`, with a table from 0.69 to 0.79. The generator ran again on the 163 n with a held f of 0.60 to 0.84.

| n | row less held | bar less held, and who sets it | row less bar |
|---|---|---|---|
| 977 | +0.0015 | 0, held | +0.0015 |
| 914 | +0.0034 | -0.0006, soft of round 17 | +0.0040 |
| 913 | +0.0039 | -0.0033, twoshort of round 17 | +0.0072 |

The 977 row is the corner `914tw17.C`, the new zone and `978tw17a.F1d`, with 15 and 18 stacks, at f = 0.7451. It was built three times, once for each far zone of the arm of 9 that the generator names. All three end at 31.744007822. The other squeeze of `modules.py job`, `slp`, ends at the same side to 1e-9. So does the row with the corner `796tw17.C`. Held is 31.743573465, so the build is 0.000434 above held and 0.0011 under its row. It is the nearest layout of the lane, and it is in `near/` of the take dir.

At this n, 0.000434 of side is 0.028 squares of far-end loss. So we looked for a class 7 far end that is 0.03 squares cheaper at the f of the row:

| start, at f = 0.745 | class 7 far end | against 3.045 |
|---|---|---|
| `more` on the class 6 taper of 46, 60 s | 3.045 | the same zone |
| `more+` on the class 6 taper with a turned stack (2.787) | 3.123 | +0.078 |
| one square more on the cut zone `587st17.F1` (2.749) | 3.358 | +0.313 |
| one square more on the cut zone `637h12.F1` (2.776) | 3.375 | +0.330 |
| bar turns on the class 7 far end itself, 90 s | 3.045 | no bar turned |

A class 6 far end with a turned stack is 0.15 to 0.19 squares cheaper than the class 6 taper. The single square does not fit it at the same price. The far end of the built 977 measures 3.048 with `farend_read.py`, so the squeeze of the build found nothing more in it.

## 7. What a better far end would be worth

`farend_ceiling.py` answers this without a design. It gives every count class of the arms of 8 and 9 a made-up far zone. At each f its loss is the lowest loss that the library holds for that arm in any class, less a number `delta`. The made-up zones have a length and a count and no squares, so they can stand in a generator row and never in a build. The run covered the 163 n above 400 with a held f of 0.60 to 0.84.

| delta | what it asks | n with a row under the bar | sum of score |
|---|---|---|---|
| 0.0 | every class costs what the cheapest class costs | 36 | 0.004228 |
| 0.2 | a far end 0.2 squares under everything we hold | 78 | 0.016736 |
| -0.5 | the control: zones 0.5 squares dearer | 0 | 0 |

The control can fail and did not. With zones 0.5 squares dearer than the cheapest class, three n have a row under held (861, 922 and 984). None has a row under the bar.

The numbers are upper bounds of the gain, because a row is a prediction for one choice of modules and the made-up zone has no squares. They say where a cheaper class would pay. With delta 0.0, by arm and class:

| arm | class | n | sum of score | f of the rows | which n |
|---|---|---|---|---|---|
| 8 | 2 | 4 | 0.000964 | 0.70 to 0.74 | 634 687 742 798 |
| 9 | 2 | 5 | 0.000517 | 0.70 to 0.75 | 795 853 914 916 978 |
| 9 | 8 | 6 | 0.000496 | 0.81 to 0.84 | 747 748 803 804 862 923 |
| 8 | 4 | 1 | 0.000340 | 0.74 | 587 |
| 8 | 0 | 4 | 0.000315 | 0.72 to 0.75 | 854 915 916 977 |
| 8 | 5 | 1 | 0.000286 | 0.75 | 540 |
| 9 | 0 | 3 | 0.000285 | 0.82 to 0.84 | 694 748 749 |
| 8 | 3 | 2 | 0.000254 | 0.70 to 0.73 | 585 636 |
| 9 | 4 | 3 | 0.000248 | 0.70 to 0.76 | 686 741 799 |
| 9 | 3 | 1 | 0.000188 | 0.72 | 796 |
| 8 | 1 | 3 | 0.000140 | 0.73 to 0.74 | 797 798 856 |
| 9 | 1 | 1 | 0.000115 | 0.67 | 910 |
| 8 | 7 | 3 | 0.000050 | 0.71 to 0.74 | 913 976 977 |
| 9 | 5 | 3 | 0.000032 | 0.76 to 0.79 | 857 918 981 |

Class 2 of an arm of 8 is the dearest gap. Its taper loses 3.33 squares at f = 0.70 and 3.46 at f = 0.74. The cheapest class loses 2.77 at f = 0.70. No design of section 3 moved it. Class 7 of an arm of 8, where we found the one new zone, is worth 0.00005.

## 8. The kill line, with the numbers

The best far end that is not a taper, at each f of the line:

| arm | f | best new far end | taper of its class | against the taper | against the library |
|---|---|---|---|---|---|
| 8 | 0.66 | 3.014, class 6, a turned stack | 3.285 | -0.272 | 0.000 |
| 8 | 0.70 | 2.876, class 6, a turned stack | 3.080 | -0.205 | +0.024 |
| 8 | 0.74 | 3.062, class 7, one square more | 3.284 | -0.221 | -0.221 |
| 9 | 0.68 | 3.951, class 2, one square more | 3.997 | -0.046 | -0.046 |
| 9 | 0.72 | 3.932, class 7, one square more | 4.100 | -0.169 | 0.000 |
| 9 | 0.76 | 4.300, class 2, one square more | 4.316 | -0.016 | -0.016 |

**By its letter the line did not fire.**

For the arm of 8, the best new far end is 0.21 to 0.27 squares under the taper of its class at all three f. For the arm of 9 it is 0.17 under at f = 0.72 and within 0.05 at the two other f.

**The lane is dry all the same. The line was written against the wrong reference.** Four numbers say why.

1. The far ends that pass the line are in the library already. The squeeze of a build turns the stacks of a taper by itself. The library holds the far zones cut from built layouts, so it holds those turned stacks. Against the library, the turned-stack far ends of the table are within 0.024 squares.
2. The one far end that is new to the library does not pay. It is the class 7 zone of section 6. Class 7 of an arm of 8 is worth 0.00005 of score at the ceiling of section 7. The generator has no row within 0.006 of held with it. The build of 914 ends 0.0041 above held.
3. No far end reaches the go line. For an arm of 8 at f = 0.70 the lowest loss we measured is the taper of class 1, 2.769, and the best new far end is 2.876. The go line is 2.65. For an arm of 9 at f = 0.72 the lowest is the taper of class 1, 3.300, against a go line of 3.07.
4. The classes where a cheaper far end would pay did not move. Class 2 is worth the most at the ceiling for both arms. Its taper stands at 3.332 (arm of 8, f = 0.70) and 4.123 (arm of 9, f = 0.72) after `less`, `more`, `morex`, `retilt` and `share1`.

Section 9 has the one far end that meets the go line. It is on an arm of 7, which the line did not name.

So the number to carry is this. A far end loses about one square for each stack that the end wall cuts. No design of this lane takes it more than 0.27 squares under the lattice taper in any class. Where it gets under, a build finds the same far end from the taper.

## 9. The same step on an arm of 7

`more` was the one design that gave a zone the library does not hold, so it ran last on the arm of 7. 50 held layouts have an arm of 7 (`results/round17-invent-parts.tsv`), more than have an arm of 9. Most of them sit at f = 0.85 to 0.99.

| f | class | squares | the new far end | taper of the class | library lowest | against the library |
|---|---|---|---|---|---|---|
| 0.70 | 4 | 32 | 2.165 | 2.816 | 2.749 | -0.584 |
| 0.74 | 4 | 32 | 2.170 | 2.745 | 2.504 | -0.334 |
| 0.74 | 0 | 42 | 2.632 | 3.099 | 3.025 | -0.393 |
| 0.92 | 2 | 37 | 3.354 | 3.466 | 3.406 | -0.052 |
| 0.94 | 2 | 44 | 2.893 | 3.377 | 3.303 | -0.410 |
| 0.98 | 2 | 44 | 2.750 | 3.342 | 3.342 | -0.592 |

**The far end of class 4 at f = 0.70 meets the go line.** It loses 2.165 squares. The cheapest taper of an arm of 7 at that f loses 2.316, and the far end of the arm of 7 in held 634 loses 2.429. So it is 0.26 under the only arm bar we have for an arm of 7. We checked it by hand because it looked too good. It has 32 squares. `zone_search.exact` gives a smallest gap inside of -1.3e-14 and a gap to the first stack of 2.2e-11. Its length is 5.4668, against 5.5709 for the lattice taper of 32. Its table by `modules.tabulate` stays between 2.16 and 2.21 from f = 0.65 to 0.75.

Each of these is the taper of the class below with one tilted square more, as in section 6. The square goes into a pocket where an upright square does not fit, and the lattice count cannot see it.

The zones went to the generator, with rows of uprights under them for the classes below. At f = 0.65 the rows give class 3 at 2.387 and class 2 at 2.568. That is 0.28 and 0.12 squares under the library.

| library with | n of the run | rows within 0.006 of held | nearest rows with a wider slack |
|---|---|---|---|
| the zones of f = 0.70 and 0.74 and their rows | 189 n above 119, held f 0.60 to 0.80 | none | 634 at +0.0090, 687 at +0.0183, 537 at +0.0202 |
| the zones of f = 0.92 and 0.94 too | 262 n above 119, held f 0.78 and more | none | 874 at +0.0099, 871 at +0.0193, 646 at +0.0204 |

No row is near enough for a build. The zone of f = 0.98 came after the second run. The table of the 0.94 zone already gives 2.80 at f = 0.98, so the run saw most of it.

A far end that cheap pays nothing today because the held layouts with an arm of 7 need other classes. In held 634 the far end of the arm of 7 has 16 squares, class 2, and loses 2.429 at f = 0.70. The new zone serves class 4. Class 2 from it costs two rows of uprights and comes to 2.69. A layout that uses class 4 needs another corner or other stack counts, and the library has none that fits within 0.009 of side.

## Round 19

The lane is new in round 19, in the slot of the closed stair-b lane. All of this document is round 19. The record of the round:

| step | what ran | outcome |
|---|---|---|
| control | our reading of 6 held far ends against the invent lane | largest difference 0.033 squares, line 0.05 |
| search | 7 designs on the tapers of the arms of 8 and 9 at six f | section 4 |
| new zone | class 7 of an arm of 8, one square more on the class 6 taper | 0.16 to 0.22 squares under the library |
| arm of 7 | one square more on the tapers at f = 0.70 to 0.98 | classes 4, 0 and 2 are 0.33 to 0.59 under the library, section 9 |
| rows | 79 copies of held far zones with rows of uprights | rows 0.0010 of side and more above the bar |
| high f | 13 tapers of an arm of 9 at f = 0.88 to 0.96, under the library by 0.07 to 2.06 squares | 2 of 138 n with a row within 0.006 |
| ceiling | made-up far zones at the loss of the cheapest class | 36 n and 0.0042 of score at most |
| builds | 914, 587, 796 and 977, eleven builds in all | all above held, by 0.0041, 0.0007, 0.0020 and 0.0004 of side |

**The take dir holds no n.** `take.tsv` has the header only. `near/` holds three built layouts: 977 at 0.000434 of side above held, 587 at 0.000703 and 796 at 0.001982. The handoff log names each of them for a kick or a polish.

boxE ran two processes and boxA one, each under `nice` with a deadline file. `STATE.txt` of the take dir has one line for each queue that started or stopped.

## What the next round should run

Best first. Each has the number that puts it there.

1. **Kick or polish the built 977.** It is 0.000434 of side above held, which is 0.028 squares. Both squeezes and both corners end at the same side to 1e-9, so the next move has to come from outside the squeeze. The file is `near/977-farend-class7.csv`.
2. **Run `more` on every arm and every f.** Then look for the layouts that fit the new far ends. `more` is the only design that got under the library. It did so in 8 of the 12 cells of an arm and an f where it ran, by up to 0.59 squares. It costs 25 s a class. Arms of 4, 5, 10 and 11 have had no run. Neither has an arm of 6 outside f = 0.70, nor arms of 7 and 8 at most f. The far ends alone are not enough: the nearest row with a new zone of an arm of 7 is 0.0090 of side above held. They need corners and stack counts that fit their class.
3. **Put the row copies into the shared library.** The command is `farend_rows.py make`. It gives 79 far zones that are 0.01 to 0.88 squares under the library. Most of that is outside f = 0.66 to 0.76. They cost one command and no search. Their rows are 0.0010 of side above the bar at best, and their builds end 0.0002 to 0.0003 under the row.
4. **Count the tapers of the arms of 9 and 10 above f = 0.86, with corners for those f.** The library is thin there. In 13 classes of the arm of 9 it is 0.07 to 2.06 squares above the taper. The far zones alone do not pay: 2 of 138 n get a row within 0.006 of held.
5. **Leave class 2 of an arm of 8 alone.** The ceiling puts the most on it, 4 n and 0.00096 of score. Five designs on its taper left it at 3.33 to 3.46 squares. So did 7 starts of `cut`, a step whose control did not pass.
6. **Do not run again:** `less`, `share`, `retilt` and `hop` on a lattice taper, for arms of 8 and 9 at f = 0.66 to 0.76. Section 4 has every class.
7. **An arm of 11 needs a taper count that does not stop at 10.** Its arm bar is the highest, 4.27 squares. This lane has no number for it.

## Files

- Tools: `farend_read.py` (the control), `farend_search.py` (`run`, `table`, `lib`, `results`, `cut`, `turn`), `farend_rows.py` (`make`, `show`), `farend_ceiling.py` (`make`, `sum`).
- Table: `results/farend-r19-2026-11-12.tsv`, the best far end of every arm, f, class and design, next to the taper and the lowest loss of the library.
- Take dir: `<scratch>/bounties-squares/take-farend-r19`. `STATE.txt` has one line for each queue and each decision. `work/boxE` and `work/boxA` hold the rows and one pickle for each far end. `work/ceil` holds the three ceiling queues. `work/lib-rows.tsv` lists the zones with rows. `work/boxE-box` holds every generator table (`q-*.tsv`), the built layouts (`raw-*`) and the logs. The new modules are not kept as a library: `farend_search.py lib` makes them again from the pickles in seconds.

## Summary

- No n certified. The take dir has three near layouts. The nearest is 977, 0.000434 of side above held.
- The control passed: our reading of 6 held far ends matches the invent lane to 0.033 squares.
- The kill line did not fire by its letter. A far end with a turned stack is 0.21 to 0.27 squares under the taper of its class for an arm of 8. The library already holds those far ends, because the squeeze of a build turns the stacks itself.
- One design finds far ends that the library does not hold: one tilted square more in a pocket of a taper. It gives class 7 of an arm of 8 at 3.06 to 3.17 squares. It gives classes 4, 0 and 2 of an arm of 7 at 0.33 to 0.59 squares under the library.
- The class 4 far end of an arm of 7 loses 2.165 squares at f = 0.70 and meets the go line. No held layout can use it within 0.009 of side.
- A far end that makes every class as cheap as the cheapest would be worth 0.0042 of score at most, on 36 n. Class 2 of an arm of 8 is the largest part, and nothing moved it.
- **Next:** a kick of the built 977, then `more` on every arm and f together with corners that fit the new classes.
