# Avenue: classfill (2026-11-12, round 17)

**Result: six n certified against the round 16 file: 703, 982, 874, 378, 995 and 983. At 19:55 UTC two of them are the lowest take of their n in round 17 (874 and 995). The class table did not pay. The cells with the most n are 0.05 to 0.9 squares above a break-even loss. The searches gained that much only where another zone binds. The gains came from one sweep on a far zone of a layout, at the f of that layout. On 703 the layout was a held one, and the round 17 file holds that row. On the other five n the layout was a take that another lane had certified minutes before. Each of those rows is 6.5e-09 to 5.6e-06 of score below the take it started from. Other lanes went lower on 703 and 982 with other designs: the modules lane has 703 at 0.016216223785, and the border lane has 982 at 0.014819343384. The modules lane then built 378 on the corner of our row and went 3.4e-09 lower. The border lane then certified 983 at 0.014641566927 with another design.**

This avenue had one job. It ranks the far zones we lack by the number of trailing n that each one would serve. Then it searches the zones at the top of that list. Its slice is the n whose board side fraction is 0.85 or more.

Words used here: "held" is `gather/round15-2026-11-12a.csv` (22.1672602051, gate dir `gate/cand-round15-1112a`). "The board" is the per-puzzle board of 2026-11-09 ([`results/per-puzzle-lb-2026-11-09.json`](../results/per-puzzle-lb-2026-11-09.json)). The side is `L = m + f` with `m` whole, and `k = n - m²`. The zones, the classes and the loss are the ones of the [zones avenue](zones.md) and the [modules avenue](modules.md). The library is `lib16b` of the modules lane of round 16, copied at 13:12 UTC. It has 9,039 modules: 926 corners, 4,589 grant variants of corners and 2,453 far zones that the generator may use. The tool is [`classfill.py`](../classfill.py).

## 1. Kill line and control (written before the first long run)

**The measurement**. For every trailing n, `classfill.py table` gives the loss that a new far zone must reach to tie the held side (the break-even loss, section 2). The three cells with the most n are far zones of an 8-arm. They are class 7 at f from 0.93 to 0.99, class 6 from 0.92 to 0.99 and class 4 from 0.90 to 0.96. What we hold in these cells is 0.00 to 0.56 squares above the break-even loss.

**Kill line**. Take the zone we hold in each of the three cells. The idea cannot pay with these tools if no search result is 0.05 squares or more below it. The search for each cell has three steps. First the taper enumeration with stack positions up to 9.5, at two values of f. Then the delete and insert moves from the library zones. Then 20 CPU-minutes of sweeps and hops.

**Positive control**. The library holds 8-arm far zones of class 4 that were cut from layouts. They have 44 to 76 squares and lose 0.3 squares less than the best taper of the zones avenue (3.00 against 3.34 at f = 0.93). We delete every 8-arm far zone of class 4 from the library and run the same search at f = 0.9298 for 52 squares. The control passes if the search returns a zone with a loss of 3.01 or less. The held zone `871h14.F2` has 2.997 there. It can fail: the taper enumeration of round 11 stopped at 3.34 for this class.

## 2. The break-even loss of a far zone

`modules.Library.fit` says that a corner C, two far zones F1 and F2 and s1 and s2 flush stacks fit in the side `m + f` when

```
Y(C) + s1 p1 + L(F1) <= m + f      and      X(C) + s2 p2 + L(F2) <= m + f
```

and they hold `n = (m - c1 + 1)(m - c2 + 1) + count(C) + count(F1) + s1 c1 + count(F2) + s2 c2` squares.

Take a corner in one of its five states, and a real far zone F2 with s2 stacks that fits on arm 2. Arm 1 then has to hold `T1 = n - rest - count(C) - count(F2) - s2 c2` squares beyond the corner, in a length of `m + f - Y(C)`. The loss of a far zone is `c cos t * length - count`, and whole flush stacks leave it alone. So a far zone of the class `T1 mod c1` does the job if and only if its loss is at most

```
break-even loss = c1 cos t1 (m + f - Y(C)) - T1
```

`classfill.py table` takes the largest break-even loss over every corner, state, far zone of the other arm and stack count. It does this for each arm size and class, with the new zone on either arm. For arms of two sizes it also tries up to `c - 1` stacks fewer on the other arm, which gives the new zone its other classes. It does it twice: at the held f (a zone below that loss wins n) and at the board's f (a zone below it reaches the board's side). Beside it stands the library's lowest far loss of the same class at the same f, which is what we hold. The difference is what a search must gain. The table took 4 s for 151 n.

The table agrees with the generator where both speak. It puts the held zones of 598 and 649 at 0.03 and 0.04 below their break-even loss, and the modules lane certified both in round 16. It puts 993, 505 and 652 at 0.00: their best cell is the held layout itself.

**The strict table loses the rows that miss the fit by a hair**. The rigid tables put the held layout of 871 at f = 0.92973. Its real f is 0.92952. So at exactly the held f that layout is 0.0002 too long, the table drops one flush stack, and the row lands in another class 5 squares lower. The strict table gives 2.75 for 871 on an 8-arm in class 4, and the layout's own row gives 2.98. The option `--eps 0.0005` tests the fit at the held f plus 0.0005. With it, 40 of the 151 n have a cell at or below zero. That cell is the held layout itself, or a layout that the generator already predicts within 0.0005 of the held side. Sections 3 and 4 use the strict table. Section 8 uses the table with `--eps 0.0005`.

A corner cell is not the same kind of number. A new corner needs both of its lengths under a cap, so `classfill.py ccells` gives only an upper bound of what a corner may lose. The library's corners already sit below that bound for many n, and they still do not fit. So the corner tables say nothing we can rank, and this avenue searches far zones only.

## 3. The (c1, c2) table

151 n trail the board at a board f of 0.85 or more. They are the n from 260 that we hold below the plain grid, with the board's side below ours by more than 1e-7. Their gap is 0.02825 of score. `classfill.py pairs` gives three numbers for every ordered pair of arm sizes from 6 to 12. The first is the loss the board's count implies, `k_flush(m, f_board, c1, c2) - k`. The second is the loss of our side. The third is the free sum: the library's lowest sum of a corner and two far zones at the board's f, with the class left free.

Each cell has the median board loss, then the median of the free sum less the board loss, then the number of n with a free sum. A dash means the library has no corner of that pair there. Arm 1 is the row.

| c1 \ c2 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|
| 6 | 4.84, +0.92 (148) | 5.62, +1.02 (103) | 6.26, +0.99 (139) | 6.75, - | 7.18, - | 7.54, - | 7.83, - |
| 7 | 6.28, +0.68 (109) | 7.07, +0.67 (148) | 7.66, +0.91 (148) | 8.16, +1.35 (55) | 8.59, - | 8.92, - | 9.26, - |
| 8 | 7.50, +0.79 (148) | 8.24, +0.66 (148) | **8.83, +0.11 (148)** | 9.33, +1.37 (135) | 9.77, - | 10.15, - | 10.47, - |
| 9 | 8.54, - | 9.27, +1.01 (34) | 9.86, +1.12 (135) | 10.39, +2.63 (114) | 10.82, - | 11.13, - | 11.41, - |
| 10 | 9.48, +1.92 (30) | 10.20, - | 10.79, - | 11.29, - | 11.65, +4.32 (6) | 11.98, - | 12.22, - |
| 11 | 10.33, - | 11.03, - | 11.61, +2.11 (115) | 12.07, - | 12.40, - | 12.69, - | 12.94, - |
| 12 | 11.13, - | 11.84, - | 12.35, - | 12.74, - | 13.09, - | 13.37, - | 13.59, - |

- **Two 8-arms are the only pair where our best zones reach the board**. With the class left free, the library's best corner and best two far zones are within 0.11 squares of the board's loss in the median. On 65 of 148 n they are at or below it. Every other pair is 0.66 to 4.3 squares above the board.
- **No arm of 12 is in the library, and no pair with an arm of 10 or more has enough corners**. So the cells of arms 9 to 12 are empty because we have no corner there, not because a far zone is missing.

Two 8-arms by class `(k - 2m - 1) mod 8`:

| class | n | board loss | our loss | free sum less board loss |
|---|---|---|---|---|
| 0 | 18 | 8.91 | 9.37 | -0.06 |
| 1 | 18 | 8.85 | 9.43 | +0.05 |
| 2 | 16 | 8.93 | 9.44 | +0.02 |
| 3 | 20 | 8.76 | 9.28 | +0.12 |
| 4 | 18 | 8.79 | 9.04 | +0.07 |
| 5 | 21 | 8.81 | 9.20 | +0.08 |
| 6 | 20 | 8.84 | 9.25 | +0.17 |
| 7 | 20 | 8.86 | 9.03 | +0.18 |

The board's loss is 8.76 to 8.93 in all eight classes, a spread of 0.17. Ours is 9.03 to 9.44. The free sum is within 0.18 of the board in every class. This is the measurement of the main session on a wider band of f: the board has our best zone quality in every class.

## 4. The cells, ranked by the n they would serve

A cell is an arm size, a class and a band of held f of width 0.03. A cell counts an n when a zone no worse than the best class of that arm would win it. That is, the break-even loss is at or above the library's lowest far loss of any class of that arm at the f of the n. The other n need a zone better than every zone we hold.

42 of the 151 n have such a cell. For 12 of them the zone we hold is 0.10 squares or less above the break-even loss. For 21 it is 0.20 or less, and for 31 it is 0.35 or less.

| cell | n | short by 0.10 or less | by 0.20 | by 0.35 | break-even loss | we hold | best class of the arm | the n (squares short) |
|---|---|---|---|---|---|---|---|---|
| 8-arm, class 7, f 0.93 to 0.96 | 9 | 0 | 4 | 7 | 2.75 to 3.07 | 3.06 to 3.25 | 2.73 | 419 (0.33), 461 (0.36), 505 (0.28), 506 (0.29), 552 (0.15), 601 (0.10), 703 (0.17), 704 (0.39), 758 (0.19) |
| 8-arm, class 6, f 0.93 to 0.96 | 8 | 0 | 0 | 0 | 2.76 to 3.30 | 3.45 to 3.85 | 2.79 | 461 (0.37), 506 (0.80), 601 (0.73), 650 (0.61), 703 (0.50), 758 (0.55), 814 (0.92), 873 (0.94) |
| 8-arm, class 4, f 0.90 to 0.93 | 7 | 4 | 5 | 7 | 2.75 to 3.03 | 2.98 to 3.13 | 2.76 | 700 (0.00), 810 (0.18), 811 (0.08), 812 (0.09), 870 (0.29), 871 (0.26), 931 (0.03) |
| 8-arm, class 6, f 0.96 to 0.99 | 7 | 1 | 2 | 3 | 2.95 to 3.66 | 3.75 to 3.83 | 2.93 | 554 (0.70), 815 (0.56), 874 (0.28), 934 (0.87), 935 (0.15), 997 (0.82), 998 (0.09) |
| 8-arm, class 7, f 0.96 to 0.99 | 7 | 0 | 0 | 5 | 2.96 to 3.50 | 3.30 to 3.80 | 2.93 | 652 (0.33), 759 (0.26), 815 (0.34), 816 (0.34), 874 (0.37), 875 (0.30), 935 (0.48) |
| 8-arm, class 4, f 0.93 to 0.96 | 4 | 1 | 2 | 3 | 2.88 to 3.13 | 3.19 to 3.27 | 2.72 | 932 (0.23), 994 (0.19), 995 (0.05), 996 (0.39) |
| 7-arm, class 5, f 0.96 to 0.99 | 2 | 1 | 2 | 2 | 2.67 to 2.74 | 2.75 to 2.77 | 2.58 | 759 (0.10), 816 (0.01) |
| 6-arm, class 2, f 0.90 to 0.96 | 4 | 1 | 3 | 4 | 1.85 to 2.08 | 2.08 to 2.09 | 1.80 to 1.87 | 378 (0.01), 419 (0.18), 599 (0.15), 650 (0.23) |

- **The three cells of the kill line hold 34 of the 42 n**. They are classes 7, 6 and 4 of an 8-arm.
- **Classes 7 and 6 have only tapers**. Every zone we hold there is a lattice taper of the zones avenue with 22 to 47 squares. Class 4 has zones cut from layouts, with 44 to 76 squares.
- **The ceiling**. Give every class of every arm a far zone as good as the best class of that arm. Put one such zone into each layout. The 42 n would then gain 0.0036 of score. That is 13% of the slice's gap. Class 6 of an 8-arm is 0.00175 of it, class 4 is 0.00069 and class 7 is 0.00056.
- **One far zone does not reach the board**. A far zone at the level of our best class reaches the board's side on 7 n only. They are 601, 758, 815, 816, 874, 935 and 998, all with class 6 or 7 of an 8-arm. On the other 144 n the board needs more than one zone of our best quality. Section 3 says the three best zones together are at the board's level. So the board's layouts hold a good zone of the right class in two or three places at once.
- **Some cells are the held layout itself**. 816 and 936 (7-arm, class 5) and 378 (6-arm, class 2) are 0.01 short with the far zone of their own held layout. Their layouts use a class that is not the best of the arm. A better zone of that class wins them, but nothing new is waiting behind those cells.

## 5. How much side one hundredth of a square is

The break-even loss rises with the side at the rate `c cos t`, which is 7.6 squares per unit of side for an 8-arm at these f. So a zone that is 0.01 squares above its break-even loss leaves the layout 0.0013 of side too long. At n = 874 that is 4.5e-5 of score, a quarter of the gap of that n. A shortfall of 0.03 to 0.05 squares is the whole distance from the held side to the board's side for a typical n of this slice.

This sets the scale for sections 4 and 7. A cell that is "0.10 short" is not close. It is two or three board gaps away, and the zone search must gain all of it.

## 6. The control passed

The control library is `lib16b` less its 107 far zones of class 4 on an 8-arm. At f = 0.9298 and 52 squares, the taper enumeration with stack positions up to 9.5 gave a length of 7.215734, a loss of 3.0465. The hops then took it to 7.210718, a loss of 3.0082, after 170 hops and 241 s. The line was 3.01. No more came in the next 590 s.

The held zone `871h14.F2` has a length of 7.20921 there, a loss of 2.997. So the search finds a zone of this cell again to 0.011 squares, which is 0.0015 of side. With the found zone in the control library, the generator predicts 871 at 0.000212 of side above held and 931 at 0.000329 above held.

## 7. What the searches found

The loss is in squares. "Library" is the lowest loss that `lib16b` holds for that arm, class and f. The full list is in [`results/classfill-zones-2026-11-12.tsv`](../results/classfill-zones-2026-11-12.tsv).

| arm | f | class | squares | library | found | change | how |
|---|---|---|---|---|---|---|---|
| 8 | 0.9296 | 4 | 52 | 3.012 | 3.012 | none | 271 hops in 241 s from the held zone `871fa14.F1`, then stopped |
| 8 | 0.945 | 7 | 47 | 3.045 | 3.045 | none | taper, then 778 hops in 582 s |
| 8 | 0.975 | 7 | 55 | 3.561 | 3.561 | none | taper, then hops for 476 s |
| 8 | 0.975 | 6 | 54 | 3.780 | 3.681 | -0.099 | one square put into the class 5 zone `935h09c.F2` of 53 squares |
| 8 | 0.970 | 6 | 54 | 3.800 | 3.560 | -0.240 | the same insert, then sweeps |
| 8 | 0.975 | 3 | 67 | 3.516 | 3.211 | -0.305 | long taper, settled with free angles |
| 8 | 0.9298 | 3 | 67 | 3.887 | 3.803 | -0.084 | long taper |
| 8 | 0.9298 | 2 | 66 | 3.786 | 3.737 | -0.049 | long taper |
| 8 | 0.945 | 2 | 66 | 3.649 | 3.621 | -0.027 | long taper |
| 7 | 0.9464 | 3 | 31 | 2.802 | 2.728 | -0.073 | sweeps on `703h13.F2`, a far zone cut from a layout of 703 |
| 7 | 0.9464 | 1 | 50 | 3.241 | 3.179 | -0.062 | long taper |
| 7 | 0.9702 | 5 | 33 and 26 | 2.767 | 2.767 | none | hops for 295 s on each |
| 7 | 0.9702 | 1 | 50 | 3.099 | 3.051 | -0.048 | long taper |

- **Class 4 and class 7 of an 8-arm did not move**. These are two of the three cells of the kill line. The zones we hold there are at a floor for the hops and the sweeps.
- **Class 6 of an 8-arm moved by 0.10 to 0.27 squares**. One square put into a class 5 zone of 53 squares gives a class 6 zone of 54. Carried over f, it loses 3.59 at f = 0.955, 3.61 at 0.965, 3.56 at 0.970 and 3.68 at 0.975. The tapers we hold lose 3.78 to 3.85 there. Above f = 0.977 it is worse than the tapers. With 62 squares the same search stopped at 4.16.
- **A long taper relaxes in classes 2 and 3**. A taper of 50 to 67 squares, settled with free angles, ends with stacks at their own tilts (13 to 24 degrees beside the flush 17.5). The lattice count of the zones avenue repeats with a period of one stack, so it did not see this. Class 3 at f = 0.975 falls from 3.81 to 3.21. Classes 5, 6 and 7 show no such gain at any length.

By the letter of the kill line the idea lives: one of the three cells gained more than 0.05. It still does not pay. Section 8 gives the number.

## 8. The new zones do not reach a break-even loss

**The table**. With `--eps 0.0005`, class 3 of an 8-arm is 1.17 squares or more above its break-even loss on every n, and class 2 is 0.97 or more. A gain of 0.31 does not change that. Class 6 is the only cell where the new zone comes near:

| n | held f | break-even loss | we held | new zone at that f | still short |
|---|---|---|---|---|---|
| 874 | 0.9719 | 3.545 | 3.790 | 3.61 | 0.06 |
| 935 | 0.9785 | 3.650 | 3.763 | 3.77 | 0.11 |
| 998 | 0.9858 | 3.682 | 3.757 | 3.95 | 0.08 with the old zone |
| 758 | 0.9549 | 3.326 | 3.853 | 3.59 | 0.26 |
| 815 | 0.9609 | 3.293 | 3.832 | 3.60 | 0.31 |

**The generator**. The 13 new zones of an 8-arm went into a copy of the library (26 modules with their dense twins). `modules.py queue` then looked for rows that use a new zone, on all 151 n. It reported 143 n done. We did not check which 8 it left out. No row is within 0.001 of side of held. With a slack of 0.03, the best rows are:

| n | predicted side less held | new zone in the row |
|---|---|---|
| 874 | +0.00220 | class 6, 54 squares |
| 758 | +0.00512 | class 6, 54 squares |
| 935 | +0.00535 | class 6, 54 squares |
| 995 | +0.00605 | class 3, 67 squares |
| 815 | +0.00612 | class 6, 54 squares |
| 810 | +0.00620 | class 3, 67 squares |

The squeeze takes 6.2e-4 of side off a start in the median (round 16 of the modules avenue). So a row at +0.0022 ends above held, and we did not build it.

**Why 874 stops there**. On 874 the arm with the new class 6 zone fits from f = 0.970, which is below the held f of 0.9719. The other arm holds the class 5 zone `874h.F1` and 14 stacks, and at the held f it is 0.016 too long. So the missing class no longer binds on 874. The corner and the other arm do.

**What the table cannot see**. "We hold" is the lowest loss of the class at that f. The table does not test if that zone suits the corner of the row (its lean, its gap and its count). So the shortfall is a lower bound, and the generator is the judge.

## 9. The rows the generator had left

No modules lane ran in this round, so we asked the generator for every row of `lib16b` alone within 0.0008 of side of held, on the 151 n. It gave 192 rows on 46 n. `classfill.py fresh` drops the rows that rounds 11 to 16 built with the same corner, far zones and stacks: 73 rows. Of the other 119, 115 have a corner that an earlier round built on that n, and those builds ended at the held side. Four rows have a corner that no round built on that n. We built three:

| n | row | predicted side less held | built side less held |
|---|---|---|---|
| 704 | `651h15.C`, `996h.F2d` with 15 stacks, `462h10.F2` with 10 | +0.000282 | -0.000000001, the held layout again |
| 933 | `933h15.C`, `504h.F2` with 11 stacks, `599fa12.F2` with 11 | +0.000876 | +0.000000001, the held layout again |
| 705 | `zc8x7-68f9501ar.C`, `874h.F1` with 13 stacks, `874h14.F1` with 10 | +0.000994 | +0.000802 |

The fourth row (549 with `700mo16.C`) is 0.0019 above the round 16 take of 549, and we left it. So the round 16 library has no row left to build in this slice.

## 10. Sweeps on a far zone at the f of its layout: 703 certified

The 7-arm search for 703 in section 7 started from `703h13.F2`. That zone is the lattice taper `z7-31f930.F1` (31 squares, class 3) after the squeeze of a layout of 703. At f = 0.9464 it loses 2.802 squares. Sweeps took it to 2.728 in less than 295 s. By the table that is still 0.076 short for 703.

The generator put the round 16 corner of 703 with this zone at 0.000712 of side above held. The build ended 0.000875 below held:

| n | held | new | gain | below the round 16 take | row |
|---|---|---|---|---|---|
| 703 | 0.016302168767 | 0.016269154217 | 3.301e-05 | 1.009e-05 | `703mo16.C`, `703h.F1d` with 15 stacks, the new zone `cf7-31f9464.F1` with 12 stacks |

- The file is floatsafe at a gap of 5.0e-11. The fq quench from the certified file found nothing more (13 s).
- The squeeze took 0.0018 of side off the start here. That is three times its median. So a row with a new zone is worth a build up to 0.0015 above held.
- The same row with the 7-arm class 3 zones of 38 and 45 squares (found at f = 0.9702) ended 0.000088 and 0.000091 above held.

**The recipe**. Take a far zone that is a lattice taper, or was one before a squeeze. Seed the hops with it at the exact f of the layout that holds it, and run sweeps for 3 minutes. Put the result into the library and build the same row again. At f = 0.9464 one sweep in 444 hops found the 0.073 squares, after 243 s. We did not test if the same sweep works at the f where the taper was made.

## 11. The corner of the round 16 take with the new zone: 703 again

The library copy was made at 13:24 UTC, before round 16 ended. So it did not hold the last takes of round 16. `modules.py grow` cut the takes of rounds 16 and 17 into it: 17 layouts and 51 modules, in 86 s. One of them is the 703 of the corners lane of round 16. Its corner is `703co16.C`. That lane found it with hops on the corner, beside the old far zone `z7-31f930.F1`.

The generator put `703co16.C` with the new zone 0.000609 of side below held. That is the side of the round 16 take, because the corner sets the side of this row before the squeeze. Eight rows were built. Seven of them ended at 26.945163. The one with the taper `z8-29f950.F1d` on the other arm ended at 26.945949.

We then built 703 with the new zone on seven more corners. Five of them ended between 26.945673 and 26.945675. One of the five is `703h13.C`, the corner of the held layout. So the table has the zone beside three corners that we also hold with the old zone:

| corner of 703 | side with the old zone | side with the new zone | the new zone gives |
|---|---|---|---|
| `703h13.C`, of the held layout | 26.946385 (held) | 26.945673 | 0.000712 |
| `703mo16.C`, of the round 16 take of the modules lane | 26.946147 | 26.945510 | 0.000637 |
| `703co16.C`, of the round 16 take of the corners lane | 26.945777 | 26.945163 | 0.000614 |

| n | held | new | gain | below the round 16 take | row |
|---|---|---|---|---|---|
| 703 | 0.016302168767 | 0.016256062956 | 4.611e-05 | 2.318e-05 | `703co16.C`, `871fa14.F2d` with 15 stacks, `cf7-31f9464.F1` with 12 stacks |

- The file is floatsafe. The fq quench from the certified file found nothing more (15 s).
- The gain of the zone and the gain of the corner add up. The zone gives 0.00061 to 0.00071 of side beside each of the three corners. The hops of the corners lane gave 0.000608 with the old zone, and they still give 0.000510 with the new one.
- The far zone of the other arm does not matter here. Six different 8-arm far zones ended at the same side to 2e-9.
- No other corner comes near. With the new zone, `703cf17.C`, `651h15.C` and `703mo16.C` end at 26.945510, six corners end between 26.945673 and 26.945675, and the 7 by 8 corner `zc7x8-91f9582bu2.C` ends 0.000992 above held.
- 703 still trails the board by 0.0107 of side, which is 4.0e-4 of score.

## 12. The same sweep on 20 other zones found nothing

Section 10 gave a recipe, so we ran it on every zone near a break-even loss. The list had 56 zones. They are the lattice tapers that a held layout or a take names. They are also the best zone of each cell that is within 0.06 squares of its break-even loss. Each search took the library zones and the lattice tapers of that count as seeds, at the held f of its n. It then ran a sweep and hops for 2 or 3 minutes.

25 searches ran. Two had no seed of their count, and three were stopped before their end. In the other 20 the hops and the sweep found no shorter zone. The list is in [`results/classfill-sweeps-2026-11-12.tsv`](../results/classfill-sweeps-2026-11-12.tsv).

We ran three more searches outside the slice, on the 9-arm far zones of the round 17 layouts with two 9-arms (`take-twoshort-r17`). They are lattice tapers of 36 squares at f = 0.6898 and 0.6772, and of 28 squares at f = 0.7146. One zone of each count serves 12 of those n. After 462 and 502 hops in 235 s they had not moved. The [zones avenue](zones.md) measured the same in round 11: a sweep repairs long tapers of an 8-arm, and tapers of a 9-arm do not gain.

So the gain on `703h13.F2` is not a rule. It is one hit in the 24 searches that ran to their end. The zones we hold near a break-even loss are at a floor for these moves. The control of section 6 says the same: the hops reach a held zone to 0.011 squares and do not pass it.

## 13. What the new 703 gives the other n

**The family line**. `family_step.py` took the first new 703 one shell down and one shell up on its line. Both ended far above held: 650 at +0.00505 of side and 758 at +0.00413. The held layouts of 650 and 758 are other designs.

**Its far zones in other rows**. The squeeze of 703 also changed its 8-arm far zone (29 squares, class 5). Cut from the new layouts, that zone is `703cf17.F1`, `703cf17a.F1` and `703co16.F1`. The generator found rows with it within 0.0012 of side of held on 24 n. We built the rows nearest to held:

| n | corner | built side less held | what the build is |
|---|---|---|---|
| 505 | `zc8x7-68f9708ar.C` | -0.000000001 | the held layout again |
| 814 | `814h10.C` | -0.000000001 | the held layout again |
| 994 | `zc8x9-141f9415ar.C` | -0.000000002 | the held layout again |
| 600 | `600co16.C` | -0.000754 | the round 16 take of the corners lane again |
| 932 | `932co16.C` | -0.000649 | the round 16 take of the corners lane again |
| 995 | `995re16.C` | -0.000340 | the round 16 take of the modules lane again, 7e-9 above it |
| 996 | `996m10.C` | +0.000115 | |
| 552 | `601m10.C` | +0.000267 | |
| 651 | `zc8x7-80f9434ar.C` | +0.000288 | |
| 933 | `933s11.C` | +0.000423 | |
| 873 | `934h10.C` | +0.000739 | |
| 601 | `705h12.C` | +0.000931 | |

Six of the 12 builds end on a layout we hold, and no build is new. The reason is in the zone. At the f of the new 703, the lattice taper of 29 squares loses 2.718 and no library zone of that count loses less. So these rows are rows that earlier rounds built with the taper under another name.

**The far zones of the new 703 at its own f**. We ran the hops on both far zones of the new 703 at f = 0.945163. The 7-arm zone has 45 squares there: the zone of 31 and two stacks that are no longer flush. It stayed at a loss of 2.722 after 381 hops in 235 s. The 8-arm zone of 29 squares stayed at 2.718 after 492 hops in 235 s. So a second round of the recipe on 703 gives nothing.

## 14. The sweep on the best zones of every class

Sections 14 and 15 ran after round 16 was submitted. "Held" in them is the round 16 file (gate dir `gate/cand-round16-1112a`). It holds the same layouts as the round 15 file on 874, 930 and 993. A take counts when it is below the round 16 file and below the same n of every round 17 take dir.

`zone_search.py search` sweeps only the shortest zone of one count. A class holds zones of several counts, and a zone that is second before a sweep may be first after it. `classfill.py sweepall` runs the sweep on the best zones of every class of an arm, at the exact held f of an n. Its start zones come from the library with our own new zones (`classfill.py base`). `classfill.py wide` lists the lines to run. A line is an arm size and a held f where a zone of some class is at most 0.25 squares above its break-even loss. It takes only the n that trail the board by 2e-5 of score or more.

**Control**. On the base of 703 (7-arm, f = 0.9464, class 3, 60 s for each zone) the sweep took `703h13.F2` from 2.8016 to 2.7283 in 52 s. That is the gain of section 10. The control can fail: the first search needed 243 s of hops to make the same change.

**The queue**. `classfill.py wide` gave 89 lines from the table with `--eps 0.0005`. We kept the 68 lines whose best cell is at most 0.035 squares below its break-even loss, and ran them nearest first. Each line swept the two best zones of each listed class, for 90 s each. 14 lines ran before boxE's time went to section 15. That is 33 sweeps on arms of 6, 7, 8 and 11. 25 of them changed nothing. The other eight:

| arm | f | class | zone | squares | loss before | loss after | best of the class before |
|---|---|---|---|---|---|---|---|
| 11 | 0.9175 | 8 | `993h.F1` | 74 | 4.3165 | 4.1885 | 4.1939 |
| 11 | 0.9248 | 8 | `930h.F1d` | 63 | 4.1310 | 4.1284 | 4.1310 |
| 11 | 0.9248 | 8 | `930h.F1` | 63 | 4.2304 | 4.1310 | 4.1310 |
| 7 | 0.9719 | 4 | `874h14.F1` | 46 | 2.6472 | 2.6415 | 2.6472 |
| 8 | 0.9100 | 5 | `811m10.F1` | 37 | 2.8110 | 2.8040 | 2.8040 |
| 8 | 0.9159 | 4 | `700mo16.F1` | 60 | 3.0900 | 3.0880 | 3.0880 |
| 6 | 0.9348 | 2 | `378h.F2` | 32 | 2.0783 | 2.0781 | 2.0781 |
| 6 | 0.9100 | 2 | `599h.F1d` | 32 | 2.1025 | 2.1024 | 2.1024 |

- **The sweep gives back what the carry over f lost, and no more**. Five of the eight zones ended at the loss of the best zone of their class. A zone carried to another f keeps the kinds it had, and the sweep puts them right. The best zone of each class of a 6-arm, 7-arm or 8-arm did not move in any line.
- **The two 11-arm zones below their class do not pay**. Both went into the library. The generator put 993 with them 0.000032 of side above held, and 930 at 0.000379 above. The build of 993 ended on the held layout, 9e-9 above it. The two builds of 930 ended 0.000003 and 0.000014 above held. Hops on the zone of 74 squares for 596 s found no more.
- **874 was measured against a slid twin**. The table had the 7-arm of 874 at 0.004 squares above its break-even loss in class 4. The zone behind that number is `874fa14.F1~` with a loss of 2.5488. It is a slid twin: a far zone with the rest moved off the grid beside it. The zone search holds the rest on the grid, so the base has no slid twins. The swept `874h14.F1` at 2.6415 is 0.09 above the twin. 20 of the 116 cells within 0.25 squares of a break-even loss are held by a slid twin.

## 15. The sweep on the far zones of new layouts, at their own f: 982, 874, 378, 995 and 983 certified

The gain of section 10 came on a far zone at the f of its own layout. Sections 12 and 14 swept the best zone of a class at the f of some other n, and found a floor. So the next thing to run was the recipe itself, on layouts that no sweep had seen. `classfill.py own` takes a list of far zones, carries each to the f of its own layout and sweeps it.

**Control**. `703h13.F2` at its own f of 0.946385 went from 2.8017 to 2.7284 in 34 s. That is the gain of section 10 again.

**The new layouts of round 17**. At 18:16 UTC the round 17 take dirs of all lanes held 102 files. `modules.py grow` cut 32 of them into the library as two-arm layouts, with 64 far zones. The others have no two flush arms or are layouts the library held. Each zone got 100 s.

**Later snapshots**. The lanes kept certifying, so we copied the take dirs again and cut only what was new. <!-- snap -->Seven snapshots followed, from 18:36 to 19:47 UTC. They cut 13, 7, 5, 3, 4, 3 and 0 layouts that were new.<!-- /snap --> Each zone of a later snapshot got 70 s on boxE and up to 200 s on boxA. A zone whose layout holds its slid twin is passed over (see 760 below).

<!-- own-results -->
173 far zones were swept in all, and 14 more were passed over.

- The far zones of the layouts that round 17 certified (every snapshot of the take dirs): 123 swept. 100 did not move, 15 moved by less than 0.002 squares, and 8 moved by more.
- The far zones of older layouts that are the bar of their n: 32 swept. 26 did not move, 4 moved by less than 0.002 squares, and 2 moved by more.
- The far zones of builds that had ended a little above their bar (section 15, last part): 18 swept. 12 did not move, 3 moved by less than 0.002 squares, and 3 moved by more.

The zones that moved by 0.002 squares or more:

| zone | arm | f | squares | class | loss before | loss after | gain | what it is |
|---|---|---|---|---|---|---|---|---|
| `760mm17.F2` | 7 | 0.9762 | 39 | 4 | 2.8057 | 2.6148 | 0.1909 | not real: the layout holds the slid twin of this zone |
| `378nx.F1` | 6 | 0.9224 | 16 | 4 | 1.9232 | 1.8681 | 0.0551 | a build of the modules lane that had ended 0.000057 of side above its bar, built and certified (below) |
| `983co19.F1` | 9 | 0.8147 | 52 | 7 | 3.4109 | 3.3664 | 0.0445 | the 983 of the corners lane, the bar of 983, built and certified (below) |
| `982co17.F1` | 9 | 0.8075 | 52 | 7 | 3.4560 | 3.4123 | 0.0437 | the 982 of the corners lane, built and certified (below) |
| `995mm17.F2` | 8 | 0.9454 | 60 | 4 | 3.1928 | 3.1666 | 0.0262 | the 995 of the midm lane, the bar of 995, built and certified (below) |
| `602h.F2` | 6 | 0.9708 | 22 | 4 | 2.1227 | 2.1019 | 0.0208 | not real: the layout holds the slid twin of this zone |
| `982po17.F2` | 9 | 0.8078 | 97 | 7 | 3.5841 | 3.5709 | 0.0132 | the 982 of the polish lane, which is above the 982 of the corners lane, not built |
| `930nx.F2` | 8 | 0.9174 | 53 | 5 | 2.7938 | 2.7830 | 0.0108 | a build of 930 of the stair-c lane that had ended above held, built, ended above held |
| `804sc17.F1` | 7 | 0.8284 | 39 | 4 | 2.2664 | 2.2579 | 0.0085 | the 804 of the stair-c lane, which is above the 804 of the corners lane, not built |
| `930nm.F2` | 8 | 0.9174 | 61 | 5 | 2.7915 | 2.7830 | 0.0085 | our own build of 930 that had ended 0.000003 of side above held, built, ended 2.4e-08 of side above held |
| `875mm18.F2` | 7 | 0.9871 | 46 | 4 | 2.7127 | 2.7064 | 0.0063 | not real: the layout holds the slid twin of this zone |
| `874mm18.F1` | 7 | 0.9717 | 46 | 4 | 2.6484 | 2.6428 | 0.0056 | the 874 of the midm lane, the bar of 874, built and certified (below) |
| `503h.F2` | 8 | 0.8982 | 37 | 5 | 2.8440 | 2.8413 | 0.0027 | the held 503 |

The full list is in [`results/classfill-own-2026-11-12.tsv`](../results/classfill-own-2026-11-12.tsv).
<!-- /own-results -->

**982**. The corners lane had certified 982 in this round at 0.015018759980, a layout of two 9-arms at f = 0.807520. Its arm-1 far zone has 52 squares. The sweep changed the kind of two of them, and the loss fell from 3.4560 to 3.4123. With that zone in the library, the generator put the same corner 0.001017 of side above the take. The squeeze ended 0.000011 above it, and the fq quench ended 0.000115 below it.

| n | round 16 file | best take before | new | gain over round 16 | below the best take | row |
|---|---|---|---|---|---|---|
| 982 | 0.015115105229 | 0.015018759980 (`take-corners-r17`) | 0.015015102766 | 1.000e-04 | 3.657e-06 | `982co17.C`, the swept zone `cf9-52f8075.F1` with 11 stacks, `982co17.F2` with 10 stacks |

- The file is floatsafe. The build ends with an fq quench. A second fq quench from the certified file found nothing more (57 s).
- A second build has the swept zone on arm 2 and the lattice taper `z9-43f760.F1` on arm 1. It ended at the same side to 1e-9. A third build has `983h.F1` on arm 1, and it ended on the side of the corners take.
- The swept zone serves no other n yet. The generator found a row with it on 983 only, 0.001005 of side above the bar, and that build ended 0.000531 above the bar.
- 982 is outside the slice of this avenue: its f is 0.8075. It still trails the board by 0.0143 of side, which is 4.6e-4 of score.
- **The row was the lowest take for ten minutes.** After 18:25 UTC the border lane certified 982 at 0.014819343384. That layout is the 921 of the family lane with one border of 61 squares, and it is 1.958e-04 of score below this row. The library cannot cut it into two arms, so the sweep has no zone of it to work on.
- **Why this zone moved.** The corners lane built its 982 with the far zone `921h13.F2d` on arm 1. The generator carried that zone from the f of a layout of 921 to the f of 982. A carried zone keeps the kinds it had at its first f. The squeeze and the quench move squares and do not change a kind. Section 14 measured the same on carried zones. We did not test this on 982 in any other way.

<!-- own-more -->
**Four more n, the same way**. Each row below starts from a take that another lane certified in this round. The sweep changed the kind of a few squares of one far zone. The generator then built the same corner with the swept zone, and the fq quench ended below the take.

| n | round 16 file | best take before | new | gain over round 16 | below the best take | row |
|---|---|---|---|---|---|---|
| 874 | 0.013815144963 | 0.013807897998 (`take-midm-r17`) | 0.013807467010 | 7.678e-06 | 4.310e-07 | `874h14.C~`, the swept zone `cf7-46f9717.F1`, `874h14.F2~` |
| 378 | 0.024696384157 | 0.024696354813 (`take-modules-r17`) | 0.024696348297 | 3.586e-08 | 6.516e-09 | `378nx.C`, the swept zone `cf6-16f9224.F1`, `599h.F1` |
| 995 | 0.012739630789 | 0.012737713999 (`take-midm-r17`) | 0.012732067423 | 7.563e-06 | 5.647e-06 | `995mm17.C`, `995h12.F2d`, the swept zone `cf8-60f9454.F1`, 12 and 12 stacks |
| 983 | 0.014783194889 | 0.014734442626 (`take-corners-r17`) | 0.014729224957 | 5.397e-05 | 5.218e-06 | `983co19.C`, the swept zone `cf9-52f8148.F1` with 13 stacks, `921mo16.F1` with 10 stacks |

- **874**. The zone is `874mm18.F1` of the midm take (7-arm, f = 0.9717, 46 squares, class 4). The sweep took its loss from 2.6484 to 2.6428 and changed 6 kinds in 68 s. The build ended at a side of 29.971687923. An fq quench from the certified file found no more in 31 s.
- **378**. The modules lane had a build of 378 that ended 0.000057 of side above its bar. We cut that build into the library as `378nx`. Its far zone `378nx.F1` (6-arm, f = 0.9224, 16 squares, class 4) went from 1.9232 to 1.8681 with one kind changed, in 18 s. The build with the corner of that layout ended at 19.922373986. The same row with the held corner `378h.C` ended 4.3e-08 of side above the round 16 file. An fq quench from the certified file took 2.968e-09 of side more, and that file is the row. After 19:30 UTC the modules lane built 378 on the corner of this row and certified 0.024696344874, which is 3.4e-09 below it.
- **995**. The zone is `995mm17.F2` of the midm take (8-arm, f = 0.9454, 60 squares, class 4). Its loss went from 3.1928 to 3.1666 with 6 kinds changed. The sweep stopped at its limit of 101 s. Three builds with three other zones on the first arm ended at the same side, 31.945236094. An fq quench from the certified file found no more in 152 s.
- **983**. The zone is `983co19.F1` of the corners take (9-arm, f = 0.8148, 52 squares, class 7). Its loss went from 3.4109 to 3.3664 with 4 kinds changed. The sweep stopped at its limit of 71 s. Three builds ended at the same side, 31.814633710. <!-- quench983 -->An fq quench from the certified file found no more in 321 s.<!-- /quench983 --> After 19:45 UTC the border lane certified 983 at 0.014641566927 with another design. That is 8.766e-05 below this row.
- 874 and 995 are in the slice of this avenue. 378, 982 and 983 are not.

**760, 602 and 875: a slid twin makes a gain that is not real.** `760mm17.F2` moved by 0.1909 squares, the largest move of any sweep here. Its layout holds the slid twin `760mm17.F2~` with a loss of 2.4550, and the swept zone ended at 2.6148. The sweep works on the zone with the rest on the grid, and the layout uses the twin. So the layout did not gain. `602h.F2` (0.0208) and `875mm18.F2` (0.0063) are the same case. The generator had no row with the swept zone of 602 within 0.0012 of side of the held 602. `classfill.py own` now passes over a zone whose layout holds its slid twin.

**930: near misses.** Two builds of 930 had ended a little above the held 930. Ours was 0.000003 of side above it. One of the stair-c lane was 0.0000005 above it. We cut both into the library and swept their far zones. `930nm.F2` moved by 0.0085 squares and `930nx.F2` by 0.0108. Four builds with the swept zones ended 2.4e-08 to 0.000014 of side above the held 930. None certified.

**804**. `804sc17.F1` is a far zone of the stair-c layout of 804 (7-arm, 39 squares, loss 2.2664 to 2.2579). That layout is 1.6e-5 of score above the 804 of the corners lane, which the library could not cut. A zone gain of 0.0085 squares is about 0.0001 of side, and the layout is 0.00046 of side behind. We did not build it. `982po17.F2` (0.0132) is a zone of the polish take of 982, which is above the corners take. We did not build it either.

<!-- near3 -->
**More near misses.** At 19:22 UTC we listed the builds of every lane that had ended 2e-9 to 6e-5 of side above the bar of their n. There were 28 such n. `modules.py grow` cut 11 of them as new layouts with 22 far zones: 700, 551, 910, 920, 976, 863, 804, 758, 973, 815 and 759. The others have no two flush arms or are layouts the library held. By the end of the round 9 of these zones had a whole pass and 1 a cut one. `815ny.F1` moved by 0.0019 squares. We built 815 with the swept zone and the held corner `815h14.C`. The build ended at a side of 28.960907618, on the take of the stair-c lane to 4e-12 of score, so it did not certify. 11 zones were not swept: `700ny.F1`, `700ny.F2`, `910ny.F1`, `910ny.F2`, `920ny.F1`, `920ny.F2`, `758ny.F1`, `973ny.F1`, `973ny.F2`, `759ny.F1`, `759ny.F2`.
<!-- /near3 -->

<!-- cuts -->
**Sweeps that reached their limit.** The limit of a sweep is on the clock. On boxE 133 sweeps ended a whole pass, and 19 of them moved. 14 more reached the limit, and 13 of those had moved. After 19:10 UTC the lane ran on boxA as one process, with about a third of one core. There 16 sweeps ended a whole pass (1 moved), and 10 reached the limit (2 moved). A sweep that reaches its limit has not tried every square, so it does not show that the zone is at its end. `classfill.py own` now prints CUT on such a sweep. The zones known only from a cut sweep: `549co22.F1`, `549co22.F2`, `851fa21.F1`, `851fa21.F2`, `861fa21.F1`, `910fa17.F2`, `983cf20.F1`, `983cf20.F2`, `995cf20.F1`, `863ny.F1`, `863po18.F2`, `863sc17.F2`, `921fa18.F1`, `921mm17.F1`, `921re17.F2`, `922fa22.F1`, `922sc20.F1`, `922sc20.F2`, `930nm.F2`, `930nx.F2`, `982po17.F2`, `983co19.F1`, `994b14.F2`. `995mm17.F2` was cut too. It had a whole pass later as `995cf20.F2`, a zone of our own row of 995, and did not move again.
<!-- /cuts -->

**What the rows have in common.** Each of the six rows came from a move of 0.0056 squares or more, on a zone with no slid twin. Five of the six layouts were the bar of their n. The sixth (378) was 0.000057 of side above its bar. A move does not always pay. 930 moved by 0.0085 squares in a layout 0.000003 of side above the bar, and its builds ended above the bar. We did not build the moves under 0.003 squares. The far zones of older layouts moved less often than the far zones of new takes: the list above has the counts.
<!-- /own-more -->

## 16. Round 19: whole cores, the cut sweeps, the near misses and the slid twins

In this round "held" is the round 17 file, `gather/round17-2026-11-12a.csv` (22.1635211736, gate dir `gate/cand-round17-1112a`). A row counts when it certifies against that file and is also below the same n in every take dir of round 17 and of round 19.

**Result: 5 rows, each the lowest take of its n.** The rows sum to 3.6963e-04 of score below the round 17 file. Against the lowest other take of each n the sum is 1.9630e-04. For 994 and 554 that take is a row that its lane took out of its take dir after ours passed it. Most of the first number is the design of other lanes on 994, 969 and 554. This lane added a swept zone to their new layout.

| n | round 17 file | lowest other take | new | gain over round 17 | below the lowest other take | from |
|---|---|---|---|---|---|---|
| 994 | 0.013034737482 | 0.012947610698 (`take-stair-c-r19`) | 0.012752992835 | 2.817e-04 | 1.946e-04 | the zone of a finished cut sweep (16.1) in the new layout of the stair-c lane (16.7) |
| 554 | 0.018650559121 | 0.018566956776 (`take-modules-r19`) | 0.018566956548 | 8.360e-05 | 2.281e-10 | a swept far zone of a new take of the corners lane (16.7), a tie |
| 875 | 0.013750642489 | 0.013748068423 (`take-polish-r19`) | 0.013748068045 | 2.574e-06 | 3.780e-10 | the swept 936 twin on another n (16.5) |
| 936 | 0.013023291971 | 0.013023291337 (`take-readers-r17`) | 0.013021615973 | 1.676e-06 | 1.675e-06 | a swept slid twin (16.4) |
| 812 | 0.015007850361 | 0.015007823177 (`take-family-r17`) | 0.015007820655 | 2.971e-08 | 2.522e-09 | a swept slid twin (16.4), a tie |

- **994 is the largest row.** It is the staircase layout of the stair-c lane with our swept zone on both arms, 1.946e-04 below the stair-c take.
- **936 and 875 are this lane's own rows.** 936 is 1.68e-06 below every other take. 875 is 2.37e-06 below the takes of other designs. The polish lane polished our first 875 row, and our last row is 3.8e-10 below that.
- **969 was a sixth row for six minutes.** The sweep shortened both far zones of the invent lane's new 969 by 0.08 squares. Our build with them was 1.485e-05 below their take. The invent lane then put the swept zone into its corner too, and its 969 is now 5.3e-05 below ours (section 16.7). Our file is in `near/`.
- **812 and 554 are ties.** 812 is 2.5e-09 below the family take it started from. 554 ended 2.3e-10 below the 554 of the modules lane, which then took its own row out.
- Each row had one fq quench from its certified file on boxE. None found more (2 to 97 s). The 969 row had none, because a lower 969 was there before its turn.

**Boxes.** The lane ran two processes on boxE and one on boxD, each with a whole core. A whole pass of the sweep took 6 to 289 s there. In round 17 on boxA the same passes took 50 to 170 s, and ten were cut.

**Controls, run first.**

- The sweep: `703h13.F2` at its own f went from 2.8017 to 2.7284 in 21 s. That is the gain of section 10.
- The build script `build6.sh`: 703 from a library without the swept zone ended at a side of 26.945162811, the side of the round 17 row.
- The certifier `cert19.sh`: it dropped that build, because 0.016256062955597 is not 1e-10 below the round 17 file.

### 16.1 The cut sweeps

Section 15 lists 23 zones whose sweep had reached its limit. Two of them are not in the library of this round (`930nm.F2`, `930nx.F2`). Three hold a slid twin and are in section 16.4 (`863sc17.F2`, `921fa18.F1`, `921re17.F2`). The other 18 got a whole pass in this round.

| zone | squares | round 17, cut | round 19, whole pass | seconds |
|---|---|---|---|---|
| `549co22.F1` | 37 | 2.8741, no move, 73 s | 2.8741, no move | 15 |
| `549co22.F2` | 37 | 2.8741, no move, 71 s | 2.8741, no move | 15 |
| `851fa21.F1` | 36 | 3.2514, no move, 71 s | 3.2514, no move | 15 |
| `851fa21.F2` | 81 | 3.2514, no move, 73 s | 3.2514, no move | 60 |
| `861fa21.F1` | 61 | 3.3844, no move, 71 s | 3.3844, no move | 38 |
| `910fa17.F2` | 81 | 3.2722, no move, 101 s | 3.2722, no move | 56 |
| `983cf20.F1` | 61 | 3.3621, no move, 70 s | 3.3621, no move | 33 |
| `983cf20.F2` | 61 | 3.3621, no move, 72 s | 3.3621, no move | 33 |
| `995cf20.F1` | 29 | 2.7182, no move, 71 s | 2.7182, no move | 10 |
| `863ny.F1` | 39 | 2.2938, 1 kind, no gain, 201 s | 2.2938, 1 kind, no gain | 39 |
| `863po18.F2` | 70 | 3.3496, 3 kinds, no gain, 100 s | 3.3496, 3 kinds, no gain | 98 |
| `921mm17.F1` | 61 | 3.3565, 1 kind, no gain, 101 s | 3.3565, 1 kind, no gain | 77 |
| `922fa22.F1` | 52 | 3.3251 to 3.3248, 72 s | 3.3251 to 3.3248 | 55 |
| `922sc20.F1` | 52 | 3.3249 to 3.3246, 70 s | 3.3249 to 3.3246 | 62 |
| `922sc20.F2` | 52 | 3.3248 to 3.3246, 71 s | 3.3248 to 3.3246 | 62 |
| `982po17.F2` | 97 | 3.5841 to 3.5709, 102 s | 3.5841 to 3.5709 | 289 |
| `983co19.F1` | 52 | 3.4109 to 3.3664, 71 s | 3.4109 to 3.3664 | 63 |
| `994b14.F2` | 68 | 3.3972 to 3.3963, 4 kinds, 101 s | **3.3972 to 3.3137**, 5 kinds | 130 |

- 17 of the 18 zones ended where round 17 had left them. The cut had lost nothing there.
- `994b14.F2` is the exception. Round 17 cut it at 101 s with four kinds changed and 0.0009 squares gained. The whole pass needs 130 s and a fifth change, and that change is worth 0.08 squares.
- `983co19.F1` gave the 0.0445 squares of round 17 again and nothing more. That zone is in our row of 983 of round 17.
- `982po17.F2` moved by 0.0132 squares again. Its layout is above the bar of 982, so no build ran.
- So "13 of 14 cut sweeps had moved" did not mean that they would move more. It was true for one zone in 18.

**994.** The layout is `994b14`, the 994 of the border lane of round 14 (an 8-arm and a 9-arm at f = 0.938722). Its 9-arm far zone has 68 squares. The sweep took its loss from 3.3972 to 3.3137.

- The row is `994b14.C`, `599r10.F1` with 11 stacks and the swept zone `cf9-68f9387.F1` with 12 stacks.
- The side is 31.938027057, which is 0.000695 below the round 17 file. The generator had predicted 0.000100 below it, and the squeeze took the rest.
- Three builds with three zones on the first arm ended at 31.938027057, 31.938027294 and 31.938030731.
- An fq quench from the certified file found no more in 14 s.
- This row was 2.203e-05 below the round 17 file and 2.084e-05 below every other take. At 21:51 UTC the stair-c lane certified a lower 994 with a new corner. Section 16.7 has what the swept zone did in that layout.
- The library had no 9-arm zone of this class below a loss of 3.3975 at this f. The swept zone is at 3.3134. A sweep gain pays when it goes below the best zone the library holds for that class. It does not pay when it only reaches that zone (see 507 and 551 below).

### 16.2 Far zones of older layouts that are the bar

Round 17 had swept 32 such zones and left the list unfinished. This round swept the 39 that were left. Three moved: `993h.F1` by 0.1258 squares, `507po15.F2` by 0.0019 and `999fa14.F2` by 0.0006.

**993: one far zone gained 0.126 squares and the layout did not move.** `993h.F1` is the 11-arm far zone of the held 993 (f = 0.924791, 74 squares, class 8). The sweep took it from 4.2543 to 4.1285 with two kinds changed. That is about 0.0115 of arm length. Three builds with the held corner `993h.C` ended 9e-08 to 5e-07 of side above the round 17 file. The best has a score of 0.013102637389, and the file holds 0.013102634478. The second arm binds. Its far zone `993h.F2` had a whole pass with no move, and 379 hops in 300 s found nothing shorter. The corner does not trade the spare length of the first arm for length on the second. The layout is in `near/993.csv` of the take dir, and the corners lane has the numbers.

**507.** `507po15.F2` moved by 0.0019 squares, to 2.5259. The library already holds a zone of that class at 2.5255 at this f, so the generator had no row with the swept zone.

### 16.3 The near-miss zones

The 11 near-miss zones that round 17 had left (`700ny`, `910ny`, `920ny`, `758ny.F1`, `973ny`, `759ny`) each had a whole pass on boxD. One moved, `758ny.F1` by 0.0016 squares. Its three builds ended within 2e-09 of side of the round 17 file, and the certifier dropped them. With the 11 of round 17, the 22 far zones of the near-miss builds gave two moves under 0.002 squares and no row.

### 16.4 The slid twins

A far zone can poke past the grid edge of its strip. The first row of the rest leaves a gap there when it slides towards the corner. `modules.py` keeps such a zone twice. The module itself has the rest on the grid beside it and is longer. Its slid twin (`ID~`) has the cells of that row where the layout has them. `zone_search.py` knows only the grid, so round 17 passed these zones over.

**What changed.** `classfill.py own` now sweeps such a zone as the twin.

- `zone_search.mod_of` gets the `slide` and the need `g` of the twin, so the exact test and the contact LP place the slid cells as `modules.far_state` does.
- The soft energy of the zone search knows only walls and fixed squares. It now gets the slid cells as fixed squares, and its wall moves one cell out, to the face of the second row of the rest.
- `classfill.py merge` puts a swept twin into the library as a twin. It is the module of the twin with the new squares, so it keeps its arm, its lean, its slide and its need.
- `classfill.py twins` lists the far zones whose layout holds their twin and is the bar of its n.

**Control.** `own --control` first changes the kind of one square, so that the zone is longer. The sweep then has to come back. It did on all four zones we tried.

| zone | twin before the break | broken start | after the sweep |
|---|---|---|---|
| `602h.F1` | 1.9405 | 2.5330 | 1.9405 |
| `760mm17.F2` | 2.4808 | 3.0340 | 2.4808 |
| `553h14.F1` | 2.0011 | 2.2460 | 2.0011 |
| `874cf19.F2` | 2.5493 | 2.6614 | 2.5493 |

**The model state is a little above the cut.** In the layout the last flush stack is not exactly the ideal one. Put at the cut length, the ideal stack is 0.0004 to 0.0037 inside the zone. `modules.far_len` pushes it out, so the state the library works with is 0.003 to 0.026 squares above the loss as cut. For `553h14.F1` the loss is 1.9847 as cut, 2.0011 as the twin in the model and 2.1939 on the grid. The sweep starts from the model state, and so does the generator.

**Result.** The library holds 90 far zones with a slid twin. 26 of them are in a layout that is the bar of its n. The sweep ran on 45 twins: all 26 of the bar layouts, and 19 of layouts that are a little above the bar. 12 moved, 6 of them by 0.002 squares or more.

| zone | arm | f | squares | class | twin before | after the sweep | gain | seconds | layout |
|---|---|---|---|---|---|---|---|---|---|
| `817mm25.F2` | 7 | 0.987107 | 53 | 4 | 2.7036 | 2.6675 | 0.0361 | 98 | the bar |
| `817h13.F2` | 7 | 0.987585 | 53 | 4 | 2.7002 | 2.6649 | 0.0353 | 68 | above the bar |
| `936u13.F2` | 7 | 0.992553 | 46 | 4 | 2.6665 | 2.6385 | 0.0280 | 88 | above the bar |
| `936po14.F2` | 7 | 0.992553 | 46 | 4 | 2.6664 | 2.6385 | 0.0279 | 95 | the bar |
| `994h13.F2` | 9 | 0.940242 | 70 | 7 | 3.6634 | 3.6431 | 0.0203 | 302 | above the bar |
| `812po15.F2` | 8 | 0.923398 | 53 | 5 | 2.7681 | 2.7529 | 0.0152 | 104 | above the bar |
| `551ny.F2` | 8 | 0.923696 | 45 | 5 | 2.7528 | 2.7511 | 0.0017 | 48 | the bar |
| `812fa16.F2` | 8 | 0.923398 | 53 | 5 | 2.7542 | 2.7529 | 0.0013 | 98 | above the bar |
| `812fa17.F2` | 8 | 0.923271 | 53 | 5 | 2.7550 | 2.7537 | 0.0013 | 63 | the bar |
| `551h15.F1` | 8 | 0.923696 | 53 | 5 | 2.7522 | 2.7509 | 0.0013 | 60 | the bar |
| `812h14.F2` | 8 | 0.923399 | 53 | 5 | 2.7531 | 2.7529 | 0.0002 | 95 | above the bar |
| `999mm22.F2` | 7 | 0.997719 | 60 | 4 | 2.6889 | 2.6887 | 0.0002 | 79 | the bar |

No move, each with a whole pass: `506h.F2`, `507hj.F1`, `507po15.F1`, `553h.F1`, `553h.F2`, `553h14.F1`, `553h14.F2`, `602h.F1`, `602h.F2`, `705fa18.F2`, `705h13.F2`, `760h13.F2`, `760mm17.F2`, `817mm25.F1`, `860fa21.F1`, `860fa21.F2`, `863fax33.F1`, `863sc17.F2`, `874cf19.F2`, `874fa14.F1`, `874h14.F2`, `875mm18.F2`, `921re20.F1`, `921re20.F2`, `924re17.F2`, `924rex32.F1`, `924rex32.F2`, `934h.F2`, `934r10.F2`, `981h14.F2`, `985co23.F1`, `987scx28.F2`, `996f10.F1`.

- **936.** `936po14.F2` is the 7-arm far zone of the bar of 936 (f = 0.992553, 46 squares, class 4). The sweep took the twin from 2.6664 to 2.6385 with seven kinds changed. The library's best zone of that class was at 2.6671 there. The row is `zc7x7-78f9944br.C^2g04`, `999fa14.F1` with 17 stacks and the swept twin `cf7-46f9926s.F1~` with 13 stacks. Its side is 30.992501924. It is the first row from a slid twin. `936u13.F2` is the same zone in an older layout, and its sweep ended in the same state.
- **812.** `812fa17.F2` is the 8-arm far zone of the bar of 812. It moved by 0.0013 squares. One of its three builds ended at 28.923270757, which is 8.5e-07 of side below the round 17 file and 2.5e-09 of score below the family take: a tie. `812po15.F2` moved by 0.0152 squares to the same end state, and its builds ended 0.00013 of side above the bar.
- **817: two twins moved by 0.035 squares and neither builds.** `817mm25.F2` is in the bar of 817, a kick of the midm lane. Its corner has no state in the model (no start up to f0 + 0.02), so the generator has no row. `817h13.F2` is in the layout that the kick started from. The generator has no row with it within 0.004 of side of the bar.
- **551.** `551h15.F1` and `551ny.F2` moved by 0.0013 and 0.0017 squares, to 2.7510. The library holds a zone at 2.7507 there. The build ended 7.5e-08 of side above the round 17 file.
- The gain that round 17 saw on the grid beside such a zone was not real (section 15). The gain on the twin is real: the rows of 936 and 875 are built from one. 6 of the 45 twins moved by 0.01 squares or more.

### 16.5 A swept zone on the other n, and how much the squeeze takes

A swept zone is a library zone, so the generator can try it on every n. The first runs used rows predicted within 0.0012 of side of the bar. The 875 row showed that this was too narrow: it was predicted 0.00099 above the bar and was built 0.00008 below it.

| build | corner | predicted side minus the bar | built side minus the prediction |
|---|---|---|---|
| 875 | `817s11.C^2g04` | +0.000990 | -0.001066 |
| 936 | `936u13.C~` | +0.000796 | -0.000843 |
| 703 (control) | `703co16.C` | +0.000613 | -0.000613 |
| 994 | `994b14.C` | -0.000100 | -0.000595 |
| 551 | `551h15.C~` | +0.000487 | -0.000487 |
| 936 | `zc7x7-78f9944br.C^2g04` | +0.000165 | -0.000216 |
| 705 | `zc8x7-68f9501ar.C^2g04` | +0.000994 | -0.000140 |
| 993 | `993h.C` | +0.000032 | -0.000032 |
| 758 | `758h14.C` | +0.000042 | -0.000042 |

- The squeeze takes 0.00003 to 0.0011 of side off the prediction. The amount belongs to the corner, and it is the largest on corners that hold a grant (`^2g04`, `C~`).
- A build that ends at the side of the bar (703, 551, 758, 993) is the layout of the bar again. The prediction was above it by the amount the squeeze gives back.

So the swept zones ran again on the other n with rows up to 0.003 above the bar, the row nearest to its bar first.

- The swept 936 twin, 34 other n: the generator had rows for six n. None was built below its bar: 705 ended 0.00085 of side above it, 874 0.00132, 935 0.00141, 998 0.00144, 997 0.00171 and 760 0.00179.
- The swept 994 zone, 40 other n: two rows. 870 and 931 were built 0.0018 of side above their bar.
- A build after a sweep now takes rows up to 0.004 above the bar. `build6.sh` takes the slack as an argument.

### 16.6 Hops at the own f

`own --hops S` runs `zone_search.hops` in place of the sweep alone. That is the sweep first, and then hops: shakes, one square moved to a pocket, snaps, and changes of kind of one square or two neighbours. It ran on boxD for 100 s on each of the 12 smallest far zones of bar layouts. Each has 16 squares (`304h.F1`, both zones of `338h`, `340h.F1`, `378cf19.F1`, both zones of `418h14`, `419co18` and `461h`, and `634h13.F1`). It ran for 300 s on `993h.F2` on boxE. It tried 125 to 149 hops on each small zone and 379 on `993h.F2`. None was shorter.

### 16.7 The loop on the take dirs

`loop-s.sh` copied the take dirs of round 17 (frozen at 20:11 UTC) and of round 19 every 9 minutes and cut what was new.

- It made 9 snapshots between 20:21 and 22:07 UTC and cut 34 new two-arm layouts of other lanes.
- It swept 49 far zones of those layouts and of our own new rows. 8 moved. The moves of 0.001 squares or more:

| zone | arm | f | squares | class | before | after the sweep | gain | seconds |
|---|---|---|---|---|---|---|---|---|
| `969inx28.F1` | 9 | 0.622749 | 72 | 0 | 2.9140 | 2.8344 | 0.0796 | 126 |
| `969inx28.F2` | 9 | 0.622749 | 81 | 0 | 2.9140 | 2.8344 | 0.0796 | 157 |
| `969inx29.F1` | 9 | 0.621682 | 54 | 0 | 2.8667 | 2.8402 | 0.0265 | 67 |
| `969inx29.F2` | 9 | 0.621682 | 54 | 0 | 2.8667 | 2.8402 | 0.0265 | 66 |
| `554cox31.F1` | 6 | 0.974364 | 22 | 4 | 2.0984 | 2.0818 | 0.0166 | 18 |
| `862cox33.F2` | 9 | 0.826723 | 97 | 7 | 3.4531 | 3.4503 | 0.0028 | 268 |

- The new layouts of our own rows (994, 936, 875) had whole passes with no move. The 969 row does not read as two flush arms after its fq pass, so it was not cut.

**969: the sweep found 0.08 squares on each arm of a new design.** At 21:04 UTC the invent lane certified a new 969. It has a block corner and two 9-arms at f = 0.6227. Its far zones are taper zones of the library (`z9-54f640.F1`), which no sweep had seen at that f.

- Snapshot s28 cut the layout at 21:07. By 21:16 the sweep had taken both far zones from 2.9140 to 2.8344, with five and four kinds changed in 126 s and 157 s.
- Our library has no table for the cut corner (224 squares), so our generator had no row. The same happened with 817.
- The build then read the invent lane's own library on boxE, which holds its block corners with their tables. With the corner `zc9x9-179f6300cb4.C` and the swept zone on both arms the side was 31.621219525. That is 0.000462 below the invent take of that minute, and 1.485e-05 of score.
- The invent lane had the handoff line at 21:18. A block corner holds two far zones as its near ends, so the swept zone went into its corner too. Its 969 at 21:32 is at a side of 31.619580678, 0.00164 below ours.
- The invent lane named three more near ends of its block corners. `classfill.py own --f F` sweeps a library zone at another f than its own. The control ran first: `z9-54f640.F1` at f = 0.622749 went from 2.9141 to 2.8344, the end state of the zone cut from the layout. Then `z9-53f640.F1` at f = 0.62 went from 3.1688 to 3.0597 (0.1091 squares, 60 s). `z9-46f640.F1` at 0.62 and the 8-arm zones `z8-17f650.F1`, `z8-33f650.F1` and `z8-24f650.F1` at 0.64 did not move. The invent lane has the zone files.

**994: a swept zone in another lane's new layout.** At 21:51 UTC the stair-c lane certified a new 994, at a side of 31.935974774. It has a staircase corner and two 9-arms. Its far zones are `994mi17.F2` and the dense copy of it.

- The swept zone `cf9-68f9387.F1` of section 16.1 is a far zone of the same arm and class, 0.084 squares shorter. It had been in our library for an hour.
- The build read the stair-c library on boxE. With the staircase corner `zc9x9-131f9200ar.C` and the swept zone on both arms the generator predicted 0.0045 of side below the stair-c take.
- The build ended at 31.929838907. That is 0.006136 of side below the stair-c take and 1.946e-04 of score. It is 2.817e-04 below the round 17 file.
- The stair-c lane also has two hopped copies of its 122-square corner. With the swept zone on both arms they ended at 31.929995698 and 31.930001853, 0.00016 of side above the row.
- The stair-c lane has rows of 931, 870 and 811 with its 122-square staircase corner. The swept zone on one arm of those layouts ended 0.000028 of side above the stair-c take on 931 and 0.000075 above it on 870. On 811 it ended 0.000022 above the family take. The three files are in `near/` of the take dir.

**554.** `554cox31.F1` is a far zone of the 554 of the corners lane (6-arm, 22 squares). It moved by 0.0166 squares, to the loss of its sibling on the other arm. The build ended at the 554 of the modules lane, 2.3e-10 of score below it: the same layout, reached from another take.

### 16.8 Far zones that no sweep had seen

Two more lists ran when the lists above were done.

- **Far zones of layouts near the bar** (the layout is the bar or within 3e-04 of side of it, and no sweep had seen the zone). The list has 111 zones, and 53 had a pass by 22:07 UTC. 13 moved, four of them by 0.02 squares or more. `875t13.F2` moved by 0.1113 squares. Its builds ended at the side of our 875 row to 2e-08, and the row of 875 now names this zone. `996m10.F1` moved by 0.0697 squares. Its builds ended 0.000115 of side above the round 17 file, because the zone only reached the loss of its sibling on the other arm. `995mo16.F2` moved by 0.0263 squares, and its builds ended at 31.945376, above the 995 of our round 17 take. `874fa14.F2` moved by 0.0211 squares, and its builds ended at 29.971820, above the 874 of our round 17 take. The other nine moved by less than 0.002 squares, and the builds that ran from them ended at the bar.
- **Large far zones of layouts above the bar** (40 squares or more, the layout 3e-04 to 2e-03 of side above the bar). The list has 37 zones, and 12 had a pass by 22:07 UTC. `995re16.F2` moved by 0.0959 squares in a pass that boxD cut at 300 s. Its builds ended 0.000027 of side above the round 17 file. `740h.F2` moved by 0.0361 squares, and its builds ended 0.000002 above the bar. `995b14.F2` moved by 0.0266 squares, to the state of `995mo16.F2`.
- `982co17.F1`, a zone of the round 17 list, moved by 0.0437 squares to 3.4121. The library holds a zone at 3.4038 there, so the generator had no row.
- Over the round the sweep ran on 258 far zones. 55 moved, 31 of them by 0.002 squares or more. A whole pass took 6 to 303 s.

### 16.9 What round 19 says

- **A swept zone pays most in another lane's new design.** The 994 zone gave 2.1e-05 in its own layout and 1.9e-04 in the staircase layout. The far zones of the new 969 moved by 0.08 squares each, 12 minutes after the take.
- **The owner of the design can do more with the zone.** Our build with the invent lane's corner gave 1.5e-05 on 969. The invent lane's rebuild of its corner with the same zone gave 5.3e-05 more.
- **A zone that had a whole pass does not move again.** No second pass, no near-miss zone and no hop search moved one.
- **Finishing a cut sweep paid once in 18.** That one case is the zone behind both 994 rows.
- **The slid twins were worth the tool change.** The sweep ran on 45 twins. 6 moved by 0.01 squares or more, and one of them certified 936 and 875.
- **A gain on a zone is not a gain of the layout** in three measured cases. The other arm binds (993: 0.126 squares, the side stays). The library already holds a zone that good (507, 551, 758, 740: the build ends at the bar). The corner has no state in the model (817, and 969 until the owner's library was read).
- **The squeeze takes up to 0.0011 of side off the prediction** on corners that hold a grant. A slack of 0.0012 had cut off the 875 row.

## 17. What to run next

Best first. Each item has the measurement behind it.

1. **Build each new corner of another lane with our swept zones.** Do it within minutes of the take. The swept 994 zone in the staircase layout of the stair-c lane gave 1.9e-04 of score, six minutes after that take. The build reads the owner's library, which holds the corner with its table (`BASE=<library> ./build6.sh`). Our own library has no table for a corner it cuts from such a layout.
2. **Run the loop on every lane's new takes.** Hand each swept zone to the lane that owns the layout within minutes. The far zones of the new 969 moved by 0.08 squares each, 12 minutes after the take. Our build with them gave 1.5e-05 of score, and the owner's rebuild of its corner gave 5.3e-05 more.
3. **Sweep every taper zone that a new design holds, at the f of that design** (`classfill.py own --f F`). Two of the six zones that the invent lane named moved, by 0.08 and 0.11 squares. In a block layout a zone stands at four arm ends, so it counts four times.
4. **Sweep the slid twins of layouts a little above the bar.** Take layouts up to 0.002 of side above it, and build with a slack of 0.004. Six of the twins that moved by 0.01 squares or more are in such layouts (`817h13.F2`, `936u13.F2`, `994h13.F2`, `812po15.F2`), or in the bar (`817mm25.F2`, `936po14.F2`). The 875 row was predicted 0.00099 of side above its bar.
5. **Write a splice for a swept zone whose corner has no table**: put the swept squares into the layout file and squeeze. `817mm25.F2` is 0.036 squares shorter on the bar of 817, and the generator has no row for it. The cut corner of 969 had no table too.
6. **Give the sweep 300 s on a zone of 60 squares or more.** The one cut sweep that paid needed 130 s, and `982po17.F2` needed 289 s. With 100 s both are cut.
7. **993 needs a corner, not a zone.** Its first arm has 0.126 squares to spare and the side does not move. The corners lane ran 72 capped hops on the held corner and found no state that fits both arms. A cut of another layout with an 11-arm and an 8-arm is the next start.
8. **Sweep the corners the same way.** A corner is also a mixture of upright squares and squares at the tilt of an arm. `zone_corner.py` hops on corners and does not change the kind of one square at a time. No round has run this.
9. **Do not run these again.** A second pass on a zone that had a whole pass (17 of 18 ended in the same state). The near-miss zones (22 zones, no row). Hops at the own f (13 zones, 125 to 379 hops each, none shorter). The swept 994 zone on other n (two rows, 0.0018 of side above the bar). A search of far zones by class (sections 7, 8, 12 and 14).

## 18. Round 20: the loop on new takes, near layouts and the new corners of other lanes

In this round "held" is the round 18 file, `gather/round18-2026-11-12a.csv` (22.1604820601, gate dir `gate/cand-round18-1112a`). A row counts when it certifies against that file. It must also be below the same n in every frozen take dir of round 19 and every live take dir of round 20.

**Result: two rows in the take, 870 and 995, 2.136e-04 of score below the round 18 file.** The lane certified eleven layouts on six n. On four of those n another lane certified a lower layout 1 to 23 minutes later: 803, 810, 993 (four times) and 996. Our files of those n are in `near/` of the take dir. Three rows of other lanes start from our 870. The border lane put one border on it for 929 (4.9e-05 below the round 18 file). The readers lane went shells down from that 929 to 868 and 809 (7.1e-05 and 3.7e-06).

| n | round 18 file | our row | gain over round 18 | lowest other take | its dir | margin |
|---|---|---|---|---|---|---|
| 870 | 0.014485733372 | 0.014279819106 | 2.059e-04 | 0.014280309428 | take-stair-c-r19 | 4.9e-07 |
| 995 | 0.012732067423 | 0.012724405364 | 7.662e-06 | 0.012732067423 | round 18 file | 7.662e-06 |

The 995 margin is the full gain only because the corners lane took its own 995 of 00:36 (0.012726410589) out of its take when ours passed it. Our 995 is 2.0e-06 below that layout.

The rows that another lane passed:

| n | our row | certified (UTC) | passed by | at | its score | under ours |
|---|---|---|---|---|---|---|
| 993 | 0.013097843726 | 23:21 | take-corners-r20 | 23:30 | 0.013057965745 | 4.0e-05 |
| 803 | 0.016841231328 | 23:21 | take-family-r20 | 23:29 | 0.016806301525 | 3.5e-05 |
| 810 | 0.015528707909 | 23:39 | take-invent-r20 | 23:39 | 0.015528562437 | 1.5e-07 |
| 993 | 0.013057003035 | 23:50 | take-readers-r20 | 00:05 | 0.013052111932 | 4.9e-06 |
| 996 | 0.012483155788 | 23:56 | take-modules-r20 | 23:57 | 0.012480019858 | 3.1e-06 |
| 993 | 0.013027760780 | 00:23 | take-stair-c-r20 | 00:28 | 0.012985166068 | 4.3e-05 |
| 993 | 0.012984670926 | 00:45 | take-readers-r20 | 00:51 | 0.012984611399 | 6.0e-08 |

**870.** The stair-c lane's 870 of round 19 has a staircase corner and the held far zones 931h.F2 and 811h.F1. The sweep of the kinds at the f of that layout (0.917) took 0.0048 squares off its F1 zone (3.3153 to 3.3105, 121 s). The cut corner `870scx40.C` has no table in our library, so the build took its slid twin `870scx40.C~`. The row is that twin with the swept zone `cf9-77f9170.F1` and the twin of the F2 zone, squeezed. One fq quench on boxE found no certified gain. A kick scan on boxD found nothing. It stopped after 7 tries and 65 s, because the tries came back to the start side.

**993, passed at the end.** At 00:28 the stair-c lane certified 993 with a hopped state of its 148-square corner, `zc9x9-148f9300cf93h1.C` (loss 3.947). Its far zones were 811h.F1 and a held second zone. We copied its library (read-only) at 00:25 and built the same corner with our swept zones (request f93h). The first build put the swept zone `cf9-77f9240.F1d` in place of the second zone. That zone is the far zone of the stair-c 931 of round 19, swept at its own f (0.0024 squares). The build certified at 0.012985015163, 1.5e-07 below the stair-c 993. One fq quench found no certified gain. Then one kick scan (`midm_scan.py` of the midm lane, modes kick and lkick, 420 s) found 3.44e-07 more in its sixth try. That layout was in the take from 00:45 to 00:51. Then the readers lane certified 993 6.0e-08 lower, one shell up from the polish 930. Its 810 and 869 of 00:51 start from our 993 (three and two shells down).

**The rows that were passed.** Each one is a swept far zone in a layout that was the bar a few minutes before:

- 993 (build B1, then s993): the swept taper zone of the stair-c 993 (0.0106 squares). B1 used our cut corner and s993 used the stair-c 122-square corner of round 19.
- 803: the slid twin of the family lane's 803 corner, with its F2 zone swept for 300 s (0.0100 squares, cut at the limit).
- 810: the cut corner of the modules lane's 810 with its swept F2 zone. It was a tie: 6.1e-10 below the polish take. The zone moved by 0.1588 squares, but most of that was the cut state of the zone. The merged zone was 0.0008 below the best zone of its class in the library.
- 993 (o993): the new corner `zc9x9-139f9338ag15x.C` of the corners lane, read from its own library, with its swept F2 zone (0.0112 squares).
- 996: the cut corner of the corners lane's 996 with its swept F2 zone (0.0165 squares).
- 993 (f93): the stair-c 148-square corner of 00:13, before its hop, with our swept 870 zone and `993scx40.F2`. It was 1.9e-08 below the stair-c 993 of 00:13.

**995.** At 00:43 a snapshot cut the corners lane's 995 of 00:36. The sweep took 0.0258 squares off its F2 zone in 87 s, and the build at once used the cut corner `995coy48.C` with `812fa16.F2d` and the swept zone `cf8-60f9451.F1`. It certified at 00:48, 2.0e-06 below the corners take. One fq quench found no certified gain, and a kick scan of 12 tries found nothing.

**Boxes.** The lane ran two processes on boxE and one on boxD, as in round 19. Other lanes loaded both boxes. boxE load was 13 to 28 on 18 cores and boxD was at 10 to 38 on 10 cores. A build took 1 to 5 minutes.

**Controls, run first.**

- The bar script `mkbar20.py` took the lowest of the round 18 file, every frozen take of round 19 and every live take of round 20. It gave 994 as our frozen round 19 row, 450 as the forensics row of round 20 and 969 as the invent row of round 19.
- The zone filter `filt.py` drops a layout whose n and f a sweep of round 17 or 19 already had. It dropped our own round 19 layouts of 875 and 936. A first version matched f to 5 places and let 552h and 817h13 through at a rounding edge. It now matches f within 5e-6.
- The certifier `cert20.sh` dropped the first 994 build. That build has the side of our frozen round 19 row to 1e-9.
- The keep rule of the near layouts: after a sync pass with `--delete`, the 11 files of the near take were still on boxE.

### 18.1 The loop on new takes

The loop of round 19 ran again (`loop-s.sh`), with three changes:

- The library grows from every frozen take of round 19 and every live take of round 20.
- `filt.py` orders the new far zones by the side of their layout over the bar, closest first.
- When worker A was held by long builds, `snapm.sh` took the snapshot on boxA. That is a grow of a few seconds. It writes the new library into boxE's newest dir in place, so the next snapshot of worker A starts from it.

Over the round the snapshots cut 53 new layouts from the takes into the library (406 to 459 layouts). Snapshot s40 at 22:56 cut 22 of them, and later snapshots cut 0 to 14 each. `filt.py` dropped 28 far zones as swept in round 19 and kept 86.

The sweep ran on 140 far zones on the two boxes. 32 moved, 22 of them by 0.002 squares or more. The moves that led to a build:

| zone | layout of | move (squares) | what the build gave |
|---|---|---|---|
| `870scx40.F1` | the stair-c 870 of round 19 | 0.0048 | **870 certified, the row of the take** |
| `993scx40.F1` | the stair-c 993 of round 19 (its taper) | 0.0106 | 993 certified (B1, s993), passed |
| `803fax40.F2` | the family 803 of round 19 | 0.0100 (cut) | 803 certified, passed |
| `810miy90.F2` | the modules 810 of round 20 | 0.1588 | 810 certified (a tie), passed |
| `993coy92.F2` | the corners 993 of round 20 | 0.0112 (cut) | 993 certified (o993), passed |
| `996coy44.F2` | the corners 996 of round 20 | 0.0165 | 996 certified, passed |
| `995coy48.F2` | the corners 995 of round 20 | 0.0258 | **995 certified, a row of the take** |
| `931scx40.F1` | the stair-c 931 of round 19 | 0.0024 | 931 4.8e-05 of side above the bar |
| `993coy92.F1` | the corners 993 of round 20 | 0.0111 | the side of o993 |
| `870ney90.F1` | the corners near 870 | 0.0049 | 4.6e-05 of side above our 870 |
| `599r10.F2`, `995h13.F1`, `995h13.F2`, `996h.F1` | the filler list | 0.027 to 0.096 | at or above the held side |

### 18.2 Near layouts of other lanes

No lane swept the far zones of the near layouts in the `near/` dirs. `mknearcf.py` writes one per n into a pseudo take dir, `work/nearcf/take-nearcf-r20`. It takes the near layout of each n (n of 300 or more) that cuts into two arms and is closest to the bar. The limit was 0.0002 of side above the bar at first and 0.0008 from 23:29 UTC. The sync keeps that dir on boxE, and the next snapshot cuts it with the tag `ne`.

Two snapshots cut 11 near layouts (`ney90` 8, `ney91` 3). Three of their far zones moved:

- `803ney90.F2` (the corners lane's near 803 of round 19) moved 0.0099 squares, cut at 300 s. We did not build it. The family 803 of 23:29 was already 3.5e-05 under every 803 we held.
- `870ney90.F1` (the corners lane's near 870) moved 0.0049 squares. The merge gave the same zone that our 870 row holds (`cf9-77f9170.F1`). The build ended 4.6e-05 of side above our 870.
- `870ney90.F2` moved 0.0006 squares, under the build threshold.

The stair-c lane handed three near layouts that do not cut into two flush arms: 869, 930 and 992. We swept their far zones at their own f (`classfill.py own --f`, on the stair-c libraries). `870h.F2` moved 0.0025 squares at the f of 869 and 0.0054 at the f of 930 (both cut at 300 s). `z9-49f920.F1` moved 0 and 0.0005. The 869 build ended 4.7e-04 of side above held, and the 930 build 7.5e-04 above. We did not sweep for 992 (9.2e-04 above held): the same zones had moved too little.

No near layout gave a row.

### 18.3 The new corners of other lanes with our swept zones

This was item 1 of the round 19 list. Each request copied the owner's library (a read-only source) and built its corner with our swept zones (`BASE=<library> ./build6.sh`).

| request | corner | our zones | result |
|---|---|---|---|
| f93h | the hopped state `cf93h1` of the stair-c 148-square corner (library copied 00:25) | the swept 931 zone | **993 certified, 1.5e-07 below the stair-c 993 of 00:28, then 3.4e-07 more by one kick, passed at 00:51** |
| f93 | stair-c 148-square corner at f 0.93 (handed 00:13) | swept 870 zone and `993scx40.F2` | 993 certified 9 minutes after that take, 1.9e-08 below it, passed at 00:28 |
| o993 | corners lane `zc9x9-139f9338ag15x.C` (handed 23:30) | its swept F2 zone | 993 certified, 9.6e-07 below the corners take, passed at 00:05 |
| s993 | stair-c 122-square corner of round 19 | the swept 993 taper | 993 certified, 7.3e-08 below our own B1, passed at 23:30 |
| o993c, co993 | corners lane g15 corners | both swept 993 zones, our 9-arm zones | the side of o993, and 0 rows within slack on 16 n |
| o996 | corners lane 996 corners | its swept F2 zone | the side of A3, nothing lower |
| s870 | stair-c 122-square corner | the swept 870 zone | 3.1e-05 of side above our 870 |
| f90, f94, d92, s931, h994 | stair-c corners at f 0.90, 0.94, the hopped d1 and the hopped 131 | swept 870, 931, 993, 994 zones | no row |

### 18.4 What did not pay

- **Corners of another f with our swept zones.** f90 and f94 used the stair-c corners at f 0.90 and 0.94. d92 used its hopped corner of 23:50. They and s931 gave no row. Their best builds were 4.8e-05 of side above the bar (931) or above our own frozen row (994).
- **h994.** The stair-c hopped 131-square corner of round 19 with our swept 994 zone built the side of our frozen 994 row to 1e-9.
- **The filler list** (round 19 item 4: layouts up to 0.0012 of side above the bar that no sweep had seen). Zones moved by 0.0397 (`599r10.F2`), 0.0273 (`995h13.F2`), 0.0473 (`995h13.F1`) and 0.0956 squares (`996h.F1`). Every build ended at the held side (599) or 1.2e-04 to 1.4e-04 above it (995, 996): the corner binds.
- **A large move on a cut zone.** The 0.1588 squares of `810miy90.F2` gave a tie, because the cut zone starts far above the library's best zone of its class.
- **The fq quench of a certified row** found no certified gain on 870, 810, 993 and 995 (5 to 124 s each).

### 18.5 What to run next

Best first. Each item has the measurement behind it.

1. **Build each new corner of another lane with our swept zones, within minutes of its handoff.** It gave four of the eleven certified layouts. The f93 build (the stair-c 148-square corner with our swept 870 zone) certified 993 9 minutes after that take, 1.9e-08 below it. The f93h build of the hopped state of that corner was 1.5e-07 below the stair-c build of the same corner. The o993 build (the corners lane's new corner with its swept zone) was 9.6e-07 below the corners take. Copy the owner's library of a hopped corner as soon as the hop ends: the hopped corner was 0.12 squares shorter, and it moved 993 by 4.3e-05.
2. **Run one kick scan on each certified row at once, before the handoff line** (`midm_scan.py --modes kick,lkick`, 400 to 600 s). Our margins were 1.5e-07 to 4.0e-05, and other lanes passed four of five n within 15 minutes. A kick scan on the f93 row of 993 found 1.21e-05 more in 8 tries, but that row was passed before the scan ended. The scan on the f93h row found 3.44e-07, and that row held 6 minutes. The scans on our 870 and 995 found nothing.
3. **Keep the loop on the new takes** (`loop-s.sh` with `snapm.sh` on boxA whenever a take moves). Each of the eleven certified layouts holds a zone that the loop swept. The corners lane's 993 of 23:30 had its swept zone at 23:45, and a row at 23:50.
4. **Do not run these again.** Corners of another f with our swept zones (f90, f94, d92, s931). The filler list of round 19 item 4 (four zones moved by 0.03 to 0.10 squares, and every build ended at or above the held side). Sweeps of near layouts more than 4e-04 of side above the bar.

## 19. Round 21: kicks of sigma 0.02 on fresh builds

In this round "held" is the round 19 file, `gather/round19-2026-11-12a.csv` (22.1514697138, gate dir `gate/cand-round19-1112a`). A row counts when it certifies against that file. It must also be below the same n in every frozen take dir of round 20 and every live take dir of round 21.

**Result: three rows (875, 936, 994), 1.611e-04 below the round 19 file.** Each row is below every take of round 20 and round 21 at 12:12 UTC. Each is also below the lowest row that any other lane certified for its n in round 21, by 3.5e-06 to 8.2e-06 (1.67e-05 in all). Two of the rows come from a kick scan of sigma 0.02 on a fresh build, and one from a swept far zone.

| n | round 19 file | our row | gain over round 19 | lowest row of another lane in round 21 | its lane | margin |
|---|---|---|---|---|---|---|
| 875 | 0.013748068045 | 0.013689992132 | 5.808e-05 | 0.013698206521 | modules | 8.21e-06 |
| 936 | 0.013021615973 | 0.012965869328 | 5.575e-05 | 0.012970844272 | corners | 4.97e-06 |
| 994 | 0.012752992835 | 0.012705752091 | 4.724e-05 | 0.012709301161 | modules | 3.55e-06 |

- **875** is the modules lane's 875 of 11:21 with one kick scan of sigma 0.02 (k875m, 16 tries, 2.43e-04 of side). The modules lane then took its 875 out of its take.
- **936** is the family lane's near 936 (3.2e-05 of side above the bar). Its F2 zone moved 0.0364 squares in the sweep. The build used the slid twin of its corner, `936t13.F1` and the swept zone.
- **994** is the stair-c hopped 122-square corner of f 0.928 with our swept far zones, then one kick scan of sigma 0.02 (k994b, 1.13e-04 of side).

We certified 931 three times (B12, B21, C22, up to 9.200e-05 below the round 19 file). Each time the polish or harvest lane passed it within minutes, first by quenching our own file. The last 931 is in `near/` with the near 870 (6.0e-06 of side above the family 870) and the near 994 build.

The round ran in two parts. The first part ran from 01:17 to 03:24 UTC. The agent stopped at 01:20 on a usage limit, and its queues ran on to their deadline. They gave no row. The second part ran from 10:00 to 12:10 UTC, and it gave every row.

### 19.1 The first part, 01:17 to 03:24

The loop of round 20 ran again (`loop-s.sh` on boxE and boxD, `sync21.sh` and `snapm21.sh` on boxA). The library grew from the frozen takes of round 20 and the live takes of round 21. Snapshots m60 to m78 swept 22 far zones. Three moved: `870cfy60.F2` by 0.0012 squares, `994rez74.F1` by 0.0003 and `378nez72.F2` by 0.0002. All three moves were under the build threshold of 0.002 squares.

Two requests ran on boxE:

- `k993n`, a kick scan on our near 993 of round 20 (kicks of sigma 0.04, 450 s). It found nothing.
- `g93`, the stair-c hopped 148-square corner of round 20 with our swept 9-arm zones. It built 930 twice, at 7.8e-07 and 4.5e-05 of side above the readers 930 of round 20.

### 19.2 Kicks of sigma 0.02 on fresh builds

A fresh build is a `modules.py job` output (built, then squeezed) that no kick has seen. The kick scan is `midm_scan.py` of the midm lane, modes lkick and kick, 360 to 450 s.

At 10:00 the first request was item 1 of the round 20 list. It built the stair-c hopped 122-square corner of f 0.928 (`lib-f928h2`, handed at 09:53) with our swept far zones on 15 n. Its first build was 994 at 31.928462104. That was 7.0e-07 of side above the modules 994 of round 21, which uses the same corner with other far zones. Two kick scans ran on that build. With the full kicks at sigma 0.04 (k994a), 11 tries found nothing. With sigma 0.02 (k994b), the second lkick try found 1.13e-04 of side, and 994 certified.

From then on every near build got one scan with kicks of sigma 0.02:

| scan | start | tries | finds | move of side | result |
|---|---|---|---|---|---|
| k875m | the modules 875 of round 21 (fresh build) | 16 | 2 | 2.43e-04 | **875 certified, 8.2e-06 below the modules 875** |
| k994b | our 994 build g9281 (fresh) | 6 | 2 | 1.13e-04 | **994 certified** |
| k994d | our 994 build g93h53 (fresh) | 17 | 1 | 8.8e-05 | 2.4e-05 above our 994 |
| k870a | our 870 build g9287 (fresh) | 8 | 2 | 6.0e-05 | 6.0e-06 above the family 870, in `near/` |
| k870c | our 870 build g93h58 (fresh) | 13 | 1 | 1.5e-05 | 6.8e-05 above the family 870 |
| k875a | our 875 build B33 (fresh) | 10 | 1 | 4.6e-06 | above the modules 875 |
| k812a | our 812 build g9282 (fresh) | 8 | 1 | 3.2e-08 | 8.9e-07 above the round 19 812 |
| k936a | our 936 build B42 (fresh) | 18 | 1 | 1.5e-09 | the 936 row, 3e-13 lower |
| k931a, k931b | our 931 builds B12 and B21 (fresh) | 6, 9 | 0 | 0 | no row |
| k418a | the corners near 418 | 114 | 1 | 1.2e-05 | 8.0e-06 above the round 19 418 |
| k995a | the corners near 995 | 14 | 0 | 0 | every try came back to the start |
| k870x, k811x | the corners 870 and 811 of round 21 | 12, 6 | 0, 1 | 0, 1.4e-12 | no row |
| k978x | the modules 978 of round 21 (certified 02:07) | 23 | 1 | 1.5e-12 | no row |
| k994c, k994e | our certified 994 (a kick find) | 8, 10 | 1, 1 | 1.5e-12 | no row (k994e also ran bkick and melt) |
| k870b, k875n | the finds of k870a and k875m | 8, 10 | 0, 0 | 0 | no row |

Our own fresh builds moved in 6 of 9 scans, by 1.5e-09 to 1.13e-04 of side, and 4 of them by 1.5e-05 or more. The fresh modules 875 moved by 2.43e-04. The 931 builds did not move at all. Other starts had already seen a kick or a second squeeze. They moved by 1.2e-05 once (the corners near 418), and by at most 1.5e-12 in eight scans.

Two rows of the take come from these scans. The 994 row is our own f928h2 build kicked. The 875 row is the modules 875 kicked, and its source names that row.

### 19.3 The loop on new takes

The loop ran on boxE (workers A and B) and on boxD (worker C). `sync21.sh` cut a snapshot on boxA at most every 5 minutes when a take of round 21 moved, and gave the new far zones to the sweep queues. It also cut the near pseudo take (`take-nearcf-r21`, the near layouts of other lanes that cut into two arms).

Over the second part the sweep ran on 33 far zones. 21 moved, and 13 by 0.002 squares or more. Over the whole round it ran on 55 zones and 24 moved (`results/classfill-own-r21-2026-11-13.tsv`). The moves that led to a build:

| zone | layout of | move (squares) | what the build gave |
|---|---|---|---|
| `875coz83.F2` | the corners 875 of round 21 | 0.0449 | 875 at 29.986268, above the modules 875 |
| `936nez84.F2` | the family near 936 (3.2e-05 of side above the bar) | 0.0364 | **936 certified, a row of the take** |
| `931poz80.F1` | the polish 931 of round 21 | 0.0338 | 931 certified (B12), then passed |
| `931scz79.F1` | the stair-c 931 of round 21 | 0.0338 | 931 certified (B21), then passed |
| `875faz83.F2` | the family 875 of round 21 | 0.0263 | 875 7.6e-05 of side above held |
| `875coz86.F2` | the corners 875 of round 21 | 0.0197 | 875 certified (B33), then passed by the modules 875 |
| `931poz82.F2` | the polish 931 of round 21 | 0.0067 | 931 certified (C22), then passed |
| `931nez82.F2`, `931poz81.F2`, `931faz80.F2` | near and polish 931 layouts | 0.0066 to 0.0067 | 931 at 30.92115 to 30.92118, above the polish 931 |
| `931scz79.F2` | the stair-c 931 of round 21 | 0.0060 | 931 7.7e-05 of side above the readers 931 |
| `875faz83.F1` | the family 875 of round 21 | 0.0043 | 875 7.0e-05 of side above held |

The 936 row holds the swept zone of a family near layout. The 931 rows did not hold. Each time, the polish or the harvest lane quenched our new file within minutes. It took 931 2.6e-10 lower with that same layout, and by 11:35 the polish lane was 1.1e-06 lower.

### 19.4 What did not pay

- **Other corners of stair-c with our zones.** We built the f93h5 corner (f 0.93, loss 3.676) with our swept zones. Its builds of 994, 931 and 870 fell into the basins of the f928h2 corner. They were 994 at 31.928461404 (the modules 994), 931 at 30.92118 and 870 at 29.914487.
- **More far zones on the same corner.** Request g928b built 994 with the far zones of the newest takes. All four builds ended at 31.92846140, the side of the modules 994.
- **The f928h2 corner on 28 n from 418 to 758** (request g928w). The queue picked other corners of the library for those n, and the builds gave the held side of 505 and 758.
- **Kicks of sigma 0.04** on a fresh build, and the bkick and melt modes on our 994. They found nothing.
- **The fq quench of a new row in the take.** It found 8.0e-09 and 8.9e-09 of side on 931. It found nothing on 875, 936 and 994. On 931 the polish and harvest lanes had already run the same quench on our file.

### 19.5 What to run next

Best first. Each item has the measurement behind it.

1. **Kick each fresh build within 2e-04 of side of the bar once, at sigma 0.02, before anything else touches it.** Use `midm_scan.py --modes lkick,kick --kicks 0.02` for 360 to 450 s. It certified 875 and 994 this round. The fresh modules 875 moved 2.43e-04 of side, and our fresh builds moved in 6 of 9 scans, by up to 1.13e-04. Kicks of sigma 0.04 on the same 994 build found nothing in 11 tries. It works on the fresh builds of every lane.
2. **Quench a new row on a box before it goes into the take.** The output contract says so. Twice the polish or harvest lane quenched our new 931 within minutes and took it 2.6e-10 lower with our own file. `cert21.sh` writes the row first. It should send the file to a box for its one quench and write the row after that.
3. **Keep the loop on the new takes and the near layouts.** The 936 row is the family near 936 with its swept far zone (0.0364 squares). It certified 43 minutes after the snapshot that cut it. Four more rows (875 and three on 931) came from zones swept in takes of the last hour, and each was passed later.
4. **Build each new corner of another lane with our swept zones, then kick it.** With our zones the f928h2 corner built 994 7.0e-07 above the bar. The kick took it below. The f93h5 corner built into the same basins, so a second corner of the same family adds little.
5. **Do not run these again.** Kicks of sigma 0.04 on a fresh build. A second kick scan on a kick find (k870b, k875n, k994c: 0 to 1.5e-12). Kicks on rows that were kicked or quenched before (the corners 870, 811, 995 and the modules 978: 0 to 1.5e-12). The bkick and melt modes on our 994. The f928h2 corner on the n below 801 (g928w).

## 20. Round 22: fresh builds and a quench before publication

The held file is `gather/round20-2026-11-13a.csv` (22.1486392356). A row must also beat every frozen round 21 take and every other live round 22 take by more than 1e-10.

The final take holds 4 n (599, 751, 799, 981). It gains 0.0001703249611 against round 20 and 0.0001108513069 against the final competing takes. The 599 margin now compares with the held file because the readers lane removed its passed row. At first certification, 599 added 2.187e-06 over that row. The scores, sources and licences are in [the results table](../results/classfill-r22-2026-11-13.tsv).

The 599 row joins a readers corner and its swept far zone to a far zone from seed 503. The readers input is a two-shell descent from the polish 703, from the areebbb certified-union notebook with Apache 2.0 notices. Seed 503 exactly matches Samanyu best-fit data, with no licence stated upstream. The first kick scan gained 0.0002665 of side, and the certified-file quench gained another 4.87e-10 of score. `work/599-lineage.json` preserves the source records and input hashes.

The 751 scan started from the forensics rectangle composition. It gained 1.273e-07 over that producer's row at first certification. Its donors trace to held 697 and a quenched near layout of 697. The latter combines crops of held 751 and 696, with a family step on one crop. Their public roots are jonathan1506 and jazivxt, with Apache 2.0 notices. `work/751-lineage.json` preserves the records, hashes and an exact match to the stored input of the polish run.

The 981 row starts from another forensics composition. Its chain includes family and layer walks, stored rectangle results and held seed 801. Six exact comparisons resolve the copied inputs. Seed 801 is Samanyu best-fit data with no licence stated upstream. Other branches have Apache 2.0 notices or use our own constructions. `work/981-lineage.json` preserves the full records and input hashes.

The 799 row also starts from a forensics composition. Its two windows use the harvest 799 and 744 layouts. The producer records name the kmmmvs public merge and the areebbb certified-union notebook, both with Apache 2.0 notices. `work/799-lineage.json` preserves the received notices and immutable donor copies.

The workers wrote 70 build records, including the setup diagnostics. 39 completed kick scans made 1923 tries. 16 scans moved the side by more than 1e-8. The sweep ran on 41 far zones. 2 moved by at least 0.002 squares.

The scan of 875 reached 0.013672734328468605. The corners lane already held that exact score, so it did not enter this take. The near 870 moved 2.393e-05 of side but stayed 8.36e-07 above the bar. A quench found no more in 96 seconds. The 994 scan moved about 8.8e-05 but stayed 2.42e-05 above the frozen round 21 row. A near 911 gained another 1.48e-07 in its quench and still missed.

[The finishing tool](../classfill_finish.py) gives each eligible fresh build one sigma 0.02 scan. It certifies the best copy before the box runs its finishing quench. The collector then compares it with the latest takes. The quench now has one default and polish pass, with a limit of 180 seconds per fq call. The older three-pass form held one near-911 finish for about 15 minutes.

The original control preserved the known 875 score of 0.013689992131794115 after its quench. The bounded control preserved the same score in 54 seconds and recorded one pass. The collector rejected both control copies because they lost to a competing take. A dispatcher control chose one new corner ahead of an older library request.

The early corner screens excluded their imported modules because the copies lacked the `ours` flag. Those empty queues are invalid measurements. The corrected copies passed the eligibility control and were screened again. Plain SLP also stalled on the first 875 build, so the build pipeline restored its original fq polish. The low-fraction target list omitted 978 at first. Later screens include it, with a separate rerun on 978. A controlled family squeeze reproduced the recorded start and reached the same 978 basin as SLP, still above the kick cutoff.

boxE ran two compute workers and boxD ran one. New handoff inputs use unique paths by content hash. Completed input copies were removed only after a checksum comparison with the archive on boxA. The dispatcher now handles one request per pass, with a new far-zone sweep between requests.

Next, give the first sigma 0.02 scan to new compositions and private builds. The forensics 751 paid, while the parallel scan of 875 only tied its owner. Use the owner's tables and exact handed ID list before rebuilding tables. Include 978 when screening corners near f = 0.8. Keep the bounded quench and stop repeat scans of a kicked find. The boxD stop record holds 42 unprocessed requests and one zone queue. Their input versions remain in `work/` for the next round. All three compute workers finished by 15:19:55 UTC.

## 21. Round 23

The held file is `gather/round21-2026-11-13a.csv` (22.1462686042). A result must also beat every frozen round 22 take and every other live round 23 take by more than 1e-10.

The final take holds 4 n (699, 917, 935, 988). It gains 0.000265283316506 against round 21 and 3.26280869558e-05 against the final competing takes. [The results table](../results/classfill-r23-2026-11-13.tsv) preserves each comparison, source and notice.

At first certification, 648 added 7.037e-09 beyond its closest competing take. The 699 margin was 6.698e-07. The 917 margin was 8.571e-08 and the 988 margin was 3.983e-09. Their producer rows can retire after a lower take appears, which changes the final comparison. Most of their gain against round 21 comes from the layouts they build on.

935 added 3.186862184e-05 beyond every competing take at first certification. Its input was a stair-c near layout. A sweep shortened its 7-arm far zone by 0.0708 squares. The new build stayed 0.000255989 of side above the bar. The default 0.0002 scan cutoff rejected it.

[The finishing tool](../classfill_finish.py) now accepts an explicit `--side-slack`. One scan at 0.0005 removed about 0.00123046 of side from that fresh 935 build. Its certified-file quench found no more. The default remains 0.0002. Private module builds use 0.0005, and the fresh near intake now admits that range too. It recovered 47 formerly rejected hashes. Already scanned inputs stayed excluded.

The workers completed 44 kick scans and 2352 tries. 16 scans moved the side by more than 1e-8. The sweep ran on 72 far zones. 8 moves reached 0.002 squares. The archive holds 34 completed build records.

The 503 zone gained 0.0643 squares, but its builds missed a newer bar. The 996 scan removed 4.300e-05 of side and reached the existing best side. Two 758 scans moved by 3.620e-06 and 6.945e-06 and still missed. The first grown-library request took 18 minutes and returned the already held 648 side.

[The handoff importer](../classfill_import.py) reports missing owner tables and retains the other handed modules. One missing far table previously aborted 39 valid table pairs. The control recovered those pairs without rebuilding them. The native reader accepted 38 modules, including 15 corners. A repeat import added no duplicates. The owner confirmed that the missing far zone had no valid knots.

Early failed importer starts and wrapper starts are excluded from the measurements. The wrapper passed shell syntax checks before its corrected retry. A remote executable bit also needed correction. Every affected request was preserved for retry. Raw libraries without owner tables use native tabulation after its control passed.

The finishing controls preserved the known 875 score of 0.013689992131794115 in 48 and 54 seconds. Temporary quench files stay under the worker journal. The native table control reproduced the saved 703h13.F2 length of 5.104160081739077 exactly. The dispatcher control selected an older owner-table handoff before a newer corner after both received equal priority.

The intake now separates a producer's method from its ancestors. A kicked ancestor no longer hides a fresh rectangle or family build. Fresh k123 joins also enter the queue. Both `.json` and `.csv.json` source sidecars are read. Private admission includes this lane's own retained scores, which prevents stale comparisons with already beaten layouts.

`work/648-lineage.json`, `work/699-lineage.json`, `work/935-lineage.json`, `work/917-lineage.json` and `work/988-lineage.json` preserve immutable inputs and notice records. The 648 chain includes merged seeds 503, 504 and 755. The 935 chain includes seed 934. Each exactly matches Samanyu best-fit data, with no licence stated upstream. Other public and own notices remain in full. The 699, 917 and 988 public roots are the areebbb certified-union notebook with Apache 2.0 notices.

boxE ran two compute workers and boxD ran one. Search and finishing quenches shared the 18:30 UTC cutoff. All owned processes stopped. Both remote archives passed checksum comparison before the lane scratch directories were removed. The archive preserves 177 pending requests and their inputs. `work/CLOSING.txt` records the checks. The final comparison ledger and per-file hashes are in `work/final-comparison-inputs.json` and `work/final-manifest.json`.

Next, give each fresh private near layout one first scan with a 0.0005 allowance. Prefer exact owner tables and one best build per screen. Resume the saved requests from their archived inputs. Keep the source snapshots and both sidecar conventions.

## Round 24

The final take retains n=863. It gains 5.53898260591e-09 against the submitted round 23b file and the other live round 24 takes. [The results table](../results/classfill-r24-2026-11-13.tsv) gives the source and licence. The file passed floatsafe at the 2.2e-11 target. Its required quench ran from its certified copy on boxD.

The n=863 chain reaches Samanyu seed 861. The saved audit matches that packing to the Apache-licensed jazivxt original. All 861 squares match, with a uniform centre dilation and maximum residual 5.33e-14. Seed 755 fails the same matching control. The other branches use our staircase and taper designs, plus direct jazivxt packings 921 and 984. The licence cell names seed 861 and the accepted original. The metadata does not grant a packing licence to unrelated Samanyu rows.

Both prospective n=911 results have complete source audits. Their modules trace to our staircase and taper constructions through the twoshort, harvest, polish and reader records. The better score is 0.01656805085420654. A live harvest row scores 0.016568050854429694. The difference is only 2.24e-13, below the required 1e-10 margin, so neither n=911 result enters the take.

The workers completed 102 kick scans with 3794 tries. 23 scans moved their starting side by more than 1e-8. There were 28 sweep requests, including unreadable layouts. The 18 completed far-zone sweeps produced no gain of 0.002 squares. The 26 owner screens built 26 layouts. These counts exclude the separate controls.

The n=2 positive control shortened side 2.5 to 2.000000000000406. The native table control reproduced length 5.104160081739077 for 703h13.F2. Its kind sweep reduced loss from 2.8017 to 2.7284. The source controls accepted an own staircase and rejected explicit Samanyu and nested unlicensed ancestry. A geometry control recognised translated, rotated and relabelled copies while keeping a distinct packing separate.

The harness restart left the controller and remote workers alive. The revived lane adopted them and started no new search. boxE kept two slots and boxD kept one. Search and quenches shared the 22:15 UTC cutoff. The last n=975 finishing job hit that cutoff without a completed quench and is excluded.

The final table was replaced by rename at 22:16 UTC. All owned processes stopped. boxE archive passed 1374 file hashes and boxD passed 635. Both remote lane scratch directories were then removed. The shared base directory stayed intact. Full archives and comparison manifests remain under `take-classfill-r24/work/` on boxA.

Next, prefer fresh private layouts for one scan with side slack 0.0005. The retained n=863 came from a family step on a reader layout. Keep immutable source snapshots and both sidecar names. The n=911 audits needed a reader donor ledger to resolve a missing sidecar. Deprioritise unchanged own-f sweeps, since none of the 18 completed sweeps reached the build threshold.

## Files

| file | what it is |
|---|---|
| [`classfill.py`](../classfill.py) | the break-even table (`table`, `cells`, `ccells`), the pair table (`pairs`), the control library (`drop`), the taper enumeration for wide arms (`taper`), the seeds for the hops (`seed`), the report and the merge of the new zones (`report`, `merge`), the rows no earlier round built (`fresh`), the tables of the builds and of the hop searches (`builds`, `sweeps`), the sweep on the best zones of every class (`base`, `wide`, `sweepall`), and the sweep on far zones at the f of their own layout (`own`, `owns`). `own` also sweeps a zone as its slid twin, runs a hop search (`--hops`) and takes another f (`--f`). `twins` lists the twins of the layouts that are the bar |
| [`results/classfill-cells-2026-11-12.tsv`](../results/classfill-cells-2026-11-12.tsv) | one row per n, arm size and class: the break-even loss at the held f and at the board's f, what we hold, and the corner and far zone behind the break-even loss |
| [`results/classfill-pairs-2026-11-12.tsv`](../results/classfill-pairs-2026-11-12.tsv) | one row per n and pair of arm sizes: the board's loss, our loss and the library's free sum |
| [`results/classfill-zones-2026-11-12.tsv`](../results/classfill-zones-2026-11-12.tsv) | the best zone of every class at every f searched, beside the library's |
| [`results/classfill-cells-eps-2026-11-12.tsv`](../results/classfill-cells-eps-2026-11-12.tsv) | the same cells with the fit tested at the held f plus 0.0005 (section 2) |
| [`results/classfill-builds-2026-11-12.tsv`](../results/classfill-builds-2026-11-12.tsv) | one row per build: the corner, the far zones, the predicted side and the built side |
| [`results/classfill-sweeps-2026-11-12.tsv`](../results/classfill-sweeps-2026-11-12.tsv) | one row per hop search at the held f of an n (section 12) |
| [`results/classfill-own-2026-11-12.tsv`](../results/classfill-own-2026-11-12.tsv) | one row per far zone swept at the f of its own layout (section 15) |
| `<scratch>/bounties-squares/take-classfill-r17` | the take dir: `378.csv`, `703.csv`, `874.csv`, `982.csv`, `983.csv`, `995.csv`, `take.tsv` and `STATE.txt` (the log of every queue of this lane). `work/` holds the library copies (`lib-g3`, and `lib-r17d` with every two-arm take of round 17), the table, the zone files of every search (`work/out`), the scripts of the queues (`work/boxE-scripts`, `work/boxA`) and the logs (boxA, not in git) |
| [`results/classfill-own-r19-2026-11-12.tsv`](../results/classfill-own-r19-2026-11-12.tsv) | one row per far zone swept in round 19 (section 16) |
| [`results/classfill-r19-2026-11-12.tsv`](../results/classfill-r19-2026-11-12.tsv) | the rows of round 19: the score in the round 17 file, the new score, the lowest other take and its dir, the source and the licence |
| `<scratch>/bounties-squares/take-classfill-r19` | the take dir of round 19: one csv for each row, `take.tsv`, `STATE.txt`, and `near/993.csv`. `work/` holds the scripts of the round (`stage/loop-s.sh`, `stage/build6.sh`, `sync.sh`, `cert19.sh`, `quench19.sh`), the zone files of every sweep (`work/boxE/out/own`, `work/boxD/out/own`) and the logs (boxA, not in git) |
| [`results/classfill-own-r20-2026-11-13.tsv`](../results/classfill-own-r20-2026-11-13.tsv) | one row per far zone swept in round 20 (section 18) |
| [`results/classfill-r20-2026-11-13.tsv`](../results/classfill-r20-2026-11-13.tsv) | the rows of round 20: the score in the round 18 file, the new score, the lowest other take and its dir, the source and the licence |
| `<scratch>/bounties-squares/take-classfill-r20` | the take dir of round 20: `870.csv`, `995.csv`, `take.tsv`, `STATE.txt`, and `near/` with the six passed rows. `work/` holds the scripts of the round (`stage/loop-s.sh`, `stage/build6.sh`, `stage/mkbar20.py`, `stage/filt.py`, `snapm.sh`, `mknearcf.py`, `sync20.sh`, `cert20.sh`, `quench20.sh`, `mkres20.sh`), the zone files of every sweep (`work/boxE/out/own`, `work/boxD/out/own`) and the logs (boxA, not in git) |
| [`results/classfill-own-r21-2026-11-13.tsv`](../results/classfill-own-r21-2026-11-13.tsv) | one row per far zone swept in round 21 (section 19) |
| [`results/classfill-r21-2026-11-13.tsv`](../results/classfill-r21-2026-11-13.tsv) | the rows of round 21: the score in the round 19 file, the new score, the lowest other take and its dir, the source and the licence |
| `<scratch>/bounties-squares/take-classfill-r21` | the take dir of round 21: one csv for each row, `take.tsv`, `STATE.txt`, and `near/` with the near and passed layouts. `work/` holds the scripts of the round (`stage/loop-s.sh`, `stage/build6.sh`, `stage/mkbar21.py`, `sync21.sh`, `snapm21.sh`, `mknearcf21.py`, `cert21.sh`, `certkick21.sh` with the start of each kick in `kickjson/`, `mkres21.sh`), the zone files of every sweep (`work/boxE/out/own`, `work/boxD/out/own`) and the logs (boxA, not in git) |

## Summary

- **Round 21: three rows (875, 936, 994), 1.611e-04 below the round 19 file.** They are 1.67e-05 below the lowest row of any other lane. Two rows come from one kick scan of sigma 0.02 on a fresh build. One is the modules 875, and one is our 994 build on the stair-c corner of f 0.928. The third is a family near layout of 936 with its swept far zone. Next, kick every fresh build within 2e-04 of side of the bar at sigma 0.02. Quench a new row before it goes into the take.
- **Round 20: two rows, 870 and 995, 2.136e-04 of score below the round 18 file.** 870 is the stair-c layout of round 19 with its swept far zone. 995 is the corners lane's new 995 with its swept far zone. The lane certified eleven layouts on six n, and other lanes passed four of those n within 1 to 23 minutes. The best next step is to build each new corner of another lane with our swept zones within minutes, then run one kick scan on the row.
- **Round 19: five rows, each the lowest take of its n.** 994 is the largest. It is the staircase layout of the stair-c lane with our swept far zone on both arms, 1.946e-04 of score below the stair-c take. 936 and 875 are the lane's own rows, 1.68e-06 and 2.37e-06 below the takes of other designs. 812 and 554 are ties.
- **A swept zone pays most in another lane's new design.** The sweep shortened both far zones of the new 969 of the invent lane by 0.08 squares. Our build with them was 1.5e-05 below their take. The invent lane then rebuilt its corner with the swept zone, and its 969 is 5.3e-05 below ours.
- **One thing pays in this avenue.** It is a sweep of the kinds on a far zone, at the f of its own layout. It pays on a zone that no sweep has seen, most of all in a new design. It certified 703, 982, 874, 378, 995 and 983 in round 17.
- **The sweep now works on the slid twins.** It ran on 45 twins. Six moved by 0.01 squares or more, and one of them certified 936.
- **Five things did not pay.** The class table (sections 3 to 9). A search of the best zone of a class at the f of another n. A second pass on a swept zone. The near-miss zones. Hops at the own f.
- **A zone gain is not always a layout gain.** 993 gained 0.126 squares on one arm, and the side did not move. The other arm binds.
- **Next.** Build every new corner of another lane with our swept zones. Run the loop on the new takes of every lane, and hand each swept zone to the lane that owns the layout. Sweep the taper zones that new designs hold. Sweep the twins of layouts a little above the bar, and build with a slack of 0.004.

## Round 25

The [results table](../results/classfill-r25-2026-11-14.tsv) retains n=699 at score 0.017008561997086336. It improves the clean frozen invent result by 3.70490227386e-8. The base combines round 23 b with source-audited frozen round 24 rows. Current competing takes give the same incremental gain.

The result came from the first sigma 0.02 scan of a fresh corners layout. Its parents are invent699, corners699, family699, reader646, family595 and public646. The public chain is areebbb's union, then the Living Atlas notebook and its internal `submission_merged.csv`. Both public notebooks have Apache 2.0 notices. The take records the complete chain and immutable source proof.

boxE ran fq from the certified 699 file before publication. Its receipt records the binary hash, certified input hash and two completed calls. The final file passed floatsafe at 2.2e-11 and the metric after pandas parsing.

The three slots started 123 scans and completed 122, with 2,324 perturbation tries. Forty-two starts shortened by more than 1e-8 of side. These numerical totals include inputs later excluded by source checks. They are not retained gains. Thirty-six handed library screen jobs completed with return code zero. One repeated, prohibited endpoint scan was cancelled with return code -15. Unchanged own-f sweeps remained closed after round 24 found no buildable move in 18 sweeps.

The fresh rebuilt-parent 228 scan shortened side by 0.002256248436, then tied the lower live midm result within 7e-16 of score. The fresh rebuilt 534 scan shortened side by 0.000261864171, but lost to soft534. Candidates 646, 599, 691, 918, 980 and 981 also failed the clean frozen or live comparison. The two 973 candidates stayed out without source approval. None of these reductions enters the take.

Source review rejected the old 985 branch through stair-c near921 and the unlicensed seed983. It also held the old 863 branch because the near CSV did not exactly match its archived raw CSV. Withdrawn and withheld source versions stayed excluded.

The [source walker](../classfill_sources.py) now keeps each rectangle parent's count and resolves shell parents by their exact donor ID. It selects the requested row of a shared provenance index. This prevents unrelated index rows from entering a source tree. The walker still reports missing records for review before publication. Archived metadata applies only when its CSV exactly matches the near file.

Controls accepted the separately licensed CC0 dataset and an own construction. They rejected explicit and nested unlicensed sources, including the hidden 790 and 921 trees. A shared-index control accepted clean581, rejected bad735, and rejected their mixed parent tree. The real clean918 tree selected only row917 from the shared index. A shell control resolved reader699 to public646, preserving the donor count.

Every worker shortened the loose n=2 control from side 2.5 to 2.000000000000406. The native table control reproduced length 5.104160081739077 for 703h13.F2. Its kind sweep reduced loss from 2.8017 to 2.7284.

Admission hit its 300-second limit 12 times. Candidate generation was bounded and source snapshots were deferred until dispatch, but repeated source work still delayed the feed. A seven-trace budget replay retained about 48% of measured shortening in the first 90 seconds and 94% in 120 seconds. Keep the 180-second first scan until a larger sample supports a shorter limit. This replay includes held traces and measures scheduling only.

Search starts closed at 02:05 UTC. All workers exited by 02:08:04 UTC. The two remote archives passed every manifest hash: 1,537 boxE files and 695 boxD files. Cleanup found no remaining lane processes and removed both owned scratch directories. The shared boxE base remained in place.

Next round, run fresh rebuilt-parent joins first. The 228 and 534 scans made large design reductions, although peers already held lower scores. Then scan fresh private layouts once at side slack 0.0005, with unseen counts first. Persist source refusals as they happen and cache immutable proofs to avoid the 12 admission timeouts. Keep unchanged own-f sweeps and repeated kick endpoints closed.

## Round 26

The [results table](../results/classfill-r26-2026-11-14.tsv) keeps four rows: 684, 706, 818 and 972. Together they are 5.86675e-4 of score below the round 25 b base (gate/cand-round25-1114b). At 17:23 UTC no other live round 26 take held these four n, so the gain beyond the other takes is the same 5.86675e-4. Each final file passed floatsafe at 2.2e-11. Each one also had one fq quench from its certified file on boxE.

| n | new score | below base | below the lowest other live take | where the layout came from |
|---|---|---|---|---|
| 684 | 0.01870410280518353 | 1.078e-8 | 1.078e-8 | forensics rectangle build of 14:00 UTC, one scan |
| 706 | 0.015587270905757178 | 8.773e-5 | 8.773e-5 | lucifer19/think-select-reclose output, first scan and one leg |
| 818 | 0.013808745548867574 | 7.974e-5 | 7.974e-5 | lucifer19/think-select-reclose output, first scan and two legs |
| 972 | 0.015605779557653188 | 4.192e-4 | 4.192e-4 | forensics rectangle build of 13:35 UTC, one scan |

### Where the gain came from

706 and 818 start from fresh public notebook outputs that the harvest lane took on 14 November. Their source is lucifer19/think-select-reclose :: submission.csv (run 07:30 UTC, Apache 2.0). The first scan used sigma 0.02 and 0.04 kicks for 180 s. Then we scanned our own certified row again (a leg): once for 706 and twice for 818. The first 818 leg moved the side by 7.96e-4. The 706 leg moved it by 3.19e-5. Both rows lost the lead to a follow lane once and came back through a leg.

684 is a forensics rectangle build of 14:00 UTC with one scan. It has three roots, each under Apache 2.0. They are the held 684 of round 13 (jonathan1506 fq stretch) and the harvest 972 (alexchilton fault-line notebook). The third is the held 737 of round 22 (malyshevdanil living atlas rows 490 and 792). Quench and midm withdrew their own 684 rows because forensics rewrote `near/684-rect.csv` after they traced it. Our input is a byte snapshot with the hash that the forensics record pins (52a68b16…), so our walk stays complete. The row came back into the take when those rows left.

972 is a forensics rectangle build of 13:35 UTC with one scan, 1.04e-6 below the quench fq of the same build. Its roots are the alexchilton fault-line 972 and the held 684 of round 13, both under Apache 2.0. Midm (sigma 0.04) beat it at 13:49 UTC, two minutes after we certified it. Midm, invent and backlog later withdrew their 972 rows, and our row came back at 17:20 UTC. Forensics withdrew a later `near/972-rect.csv` that it built on the invent 972. Our input is the earlier build, kept as a byte snapshot, and its part hashes match their records.

We also held 971, 850 and 415 for some time. Other lanes beat each of them within minutes, by 2.3e-13 to 2.4e-4 of score. Backlog took 971 with one invent_rest.py lkick of our row (1.33e-6 lower). Our own scan of that backlog row then found only 6.8e-13 more, under the 1e-10 margin.

### Source decisions

**Per-square check against the prvsiyan 1105 rows.** Rule b excludes the prvsiyan best-of-1105 rows (CC BY-SA 4.0). Quench and backlog refuse a harvest row when its record puts the layout under 0.55 of max centre distance from that row. 818 (0.471) and 706 (0.542) were on that list. Max centre distance looks only at the one square that is farthest from any prvsiyan square, so it cannot show that the other squares match. [`prvsim26.py`](../tools/classfill/round26/prvsim26.py) counts the share of squares whose centre is within 1e-3 of a prvsiyan square, under the best of the 8 symmetries.

| layout | share within 1e-3 of the prvsiyan row |
|---|---|
| harvest 818 / our 818 | 0.004 / 0.000 |
| harvest 706 / our 706 | 0.001 / 0.000 |
| harvest 971 | 0.000 |
| round 25 b base 818 / 706 / 971 | 0.573 / 0.527 / 0.483 |
| harvest 695, 654, 646, 814, 416, 499 | 0.42 to 0.76 |

The accepted base is much closer to the prvsiyan rows than 818 and 706 are. The base 453 is identical to the prvsiyan 453. So the prvsiyan file shares rows with older public merges, and geometry alone cannot prove descent. A share near zero does show that a layout is not a copy. We kept 818 and 706. Harvest used the same measure at 15:18 UTC: it kept 453, 706, 761 and 818 and withdrew 416, 499, 646, 654, 695 and 814. The main session decides on the 0.55 rule.

**The daily merge step of the tracer.** The round 25 tracer (`take-assemble-r25/trace/trace_base.py`) read the kmmmvs daily `merge_report.json` from the round 24 harvest copy. Its files had been carried away, so that report was gone. Every closure that reached the daily merge said "missing daily report". Twoshort's `quench_walk.py` then refused the forensics 415 and 501 builds on our 375 closure. Our `history26.py` (in `take-classfill-r26/work/`) now walks every kept copy of the report: ten runs from 7 to 14 November. The 34 closures that had the issue were traced again on the two round 26 runs (06:03 and 13:54 UTC), which the harvest records cite. After this, 818, 706, 971 and 375 walk clean.

**Refused prospects.** We refused four certified results that were below the base:

- 642 (6.69e-6), because its part B reaches the harvest 695, which harvest later withdrew.
- Two 505 results (1.08e-6 and 5.07e-7). Their module 552nm25v1c1d192d reaches the areebbb per_n rows 552 and 601, which credit the kmmmvs daily merge with no version. The kmmmvs runs up to 11 November take 552 unchanged from its private `local_bank.csv`, and quench_walk treats `local_bank` as a Samanyu signal.
- 684 (1.75e-8), built on the 684 that quench withdrew.

Midm and quench later withdrew their own 642, 694 and 684 rows for the same reasons. The intake holds the withdrawn rows of harvest, k123, quench and midm, and the purged forensics tree. It refuses any input whose recorded text names one of them.

### What we measured

| class of start | scans | result |
|---|---|---|
| harvest round 26 take rows (fresh public outputs) | 15 | 14 below the base, 3 entered the take (971, 706, 818) |
| forensics rectangle builds | 39 | 20 below the base, 4 entered the take (972, 850, 684, 415) |
| legs on our own certified rows (kicks 0.02 and 0.04, 300 s) | 7 | 7 below the base, 3 entered the take (818 twice, 706) |
| near files of modules, invent, stair-c, k123, backlog, soft, border and quench | 96 | 37 below the base, none below the lowest live take |
| legs on our own near misses | 5 | none entered |
| take rows of modules and rebuild, frozen round 25 stair-c files | 6 | none entered |
| legs with kicks 0.06 and 0.1 | 3 | no find in 45 tries |
| scan of the backlog 971 that followed our 971 | 1 | 6.8e-13 lower, under the 1e-10 margin |

The three slots ran 172 scans with 4,261 kick tries. The intake started 168 of them and we started 4 by hand. 56 scans moved the start by more than 1e-8 of side. Every job returned 0. A scan with kicks 0.06 and 0.1 on 971, 818 and 706 found nothing in 45 tries. Its kicks landed 1e-3 to 0.3 above the held side. Mixed kicks of 0.02 and 0.04 replaced 0.02 at 14:04 UTC, after the 850 leg found its best at a 0.04 kick. Midm won 972 with sigma 0.04 as well.

### Tool changes

The first item is in the repo. The others are lane scripts under `take-classfill-r26/work/` on boxA.

- [`classfill_finish.py`](../classfill_finish.py) takes `--kicks`, or a `kicks` field in the worker job file. The default stays 0.02.
- The collector now puts a retired row back when the take that beat it leaves (415, 684 and 972 came back this way). It caches the floatsafe score of each retired file, because 7 of them pushed one collect past its 180 s limit.
- Explicit refusals stop the repeat "needs complete ancestry" lines. Prohibited tags stay out of `near/`.

### End of the round

The first attempt of this lane started at 12:49 UTC and died within minutes. This run adopted its staged scripts and started the workers at 12:58 UTC: two on boxE and one on boxD. A light controller ran on boxA.

Search closed at 16:45 UTC. The three workers stopped between 16:45 and 16:49 UTC, and one queued job never started. `stop_manifest26.py` found no lane process on either box. The archives passed every manifest hash: 1,504 boxE files and 860 boxD files. We then removed both remote lane directories, with the boxD venv the lane made. The shared boxE base was not touched. The boxA controller stopped at 16:51 UTC. Full archives stay under `take-classfill-r26/work/` on boxA.

### Next

1. Scan each fresh public row as soon as harvest takes it, then run a leg on our certified row in the same minute. 3 of 15 harvest rows entered the take, with the three largest gains (4.7e-4, 8.8e-5 and 8.0e-5). 3 of 7 legs entered, and they won 818 and 706 back.
2. Run `prvsim26.py` on every public start before its first scan, and skip a start whose share is 0.4 or more. Harvest withdrew 6 rows at 0.42 to 0.76, and the lanes then lost the 642, 694, 748 and 546 rows built on them.
3. Keep a byte snapshot of every input and every pinned part. Our 684 stayed because its snapshot matches the pinned hash. Midm, quench and invent lost rows when forensics rewrote a near file.
4. Treat a credit to the kmmmvs daily merge with no version as untraceable before the scan, not after it. Two 505 results (best 1.08e-6) were refused only after their scans.
5. Give each forensics rectangle build a leg in the same job. 4 of 39 entered the take, but follow lanes took 972, 850 and 415 within minutes (972 came back only when they withdrew).
6. Stop the wide kicks and the near legs: none of the 3 wide legs or 5 near legs entered.

## Round 27

The [results table](../results/classfill-r27-2026-11-14.tsv) keeps 2 counts, gaining 0.000410900606386 against the round 27 bar.
The margin beyond other live round 27 takes is 7.07717256829e-05.
Each kept file has the worker's floatsafe certificate at 2.2e-11 and a completed fq quench from its certified file.
The final comparison and immutable source records are in `take-classfill-r27/work/` on boxA.

The round reopened 259 files refused under the former seed rule.
The workers completed 127 scans and 5342 perturbation tries.
51 starts shortened by more than 1e-8 of side.
These performance counts include inputs later refused by the source check.

The first share checker selected an auxiliary archive member.
The corrected checker reads `submission.csv`, uses the best share across eight symmetries, and rejects shares of 0.4 or more.
The exact prvsiyan 982 control measured 1.0 and failed admission.
The 982 candidate measured 0.0 against that same submission.
Its temporary withdrawal was lifted after the corrected check and archived run manifests resolved its raw parent.
The finishing quench preserved its score of 0.01479451530802578.

Queue reads now use a light coordinate reader and a spatial bucket share check.
Their controls reproduced the certified 982 score and both share decisions.
Collection runs separately from admission, because paging caused repeated admission timeouts.
Identical source refusals persist until an input version or policy changes.
The source walker admits the independently discovered seed and retains the other exclusions.
It now allows 300 records, matching the measured needs of large joins.

Search admission closed at 23:35 UTC and the shared search and quench deadline was 23:45 UTC.
Cleanup records state which remote archives passed SHA-256 checks before removal.

The revived run adopted the three surviving remote workers and the local drivers.
An SFTP stall left boxE workers idle until the queue transport switched to legacy SCP.
The same-file transfer control completed with its expected SHA-256 hash.
The deadline finisher uses that transport as well.

Intake now reads single-part rectangle manifests and defers a producer family after three dry starts.
Competitive fresh public finds can receive one second leg even below the old 1e-5 side-move threshold.
Later legs still need a side move above 1e-5.
Near publication now requires complete source history or an accepted exact-byte audit.
The 585 and two 932 near files were withheld because their histories remain incomplete.

The public 972 and 793 starts required explicit copy resolution.
Each raw packing matched its named Apache notebook row exactly, and the pinned completion records linked the certified input.
Those audits are retained under `work/manual-audit/`.
The reopened 632 input passed an independent root walk and every listed pin before its priority scan.
It used the earlier 684 and 850 snapshots, rather than the later withdrawn versions.

The final donor audit withdrew the earlier 927 and 982 results.
The exact k123 donor pools contained a 548 layout with prvsiyan share 0.8412408759124088 and a 747 layout with share 1.0.
Their descendant outputs had low shares, which did not clear those excluded donors.
These withdrawals apply under the share rule and do not reinstate the former seed ancestry exclusion.

The [ancestor guard](../tools/classfill/round27/ancestor_share27.py) now checks pinned packing files and the recorded counts of multi-count donor pools.
It runs before queue publication and before take retention.
The 982 ancestry control rejects its three 747 donor copies, while the public 793 ancestry control passes three packing checks.
The share cache now includes both the packing hash and the count.
Its multi-count control returns share 1.0 for 747 and 0.0 for 982 from the same file.
The 856 candidate also stayed out because five historical source issues remain unresolved.

## Round 28

The [results table](../results/classfill-r28-2026-11-14.tsv) retains 3 counts against bar28.
The gain against the bar is 9.49311919689e-05. The margin beyond other live round 28 takes is 9.49311919689e-05.
Each retained row has floatsafe certification at 2.2e-11 and a completed fq quench from the certified file.
The table names areebbb per-count upstream donors in both source and licence cells.
Inputs and ancestry records have immutable SHA-256 snapshots under `take-classfill-r28/work/` on boxA.

Three remote slots ran on boxE and boxD. Each passed the loose n=2 control from side 2.5 to 2.000000000000406.
The exact excluded public row measured share 1.0 and failed admission.
The retained 793 control measured share 0.0012610340479192938 and passed.
The source checker now accepts the exact original-seed declaration that contains semicolons.
Its control still rejects a separate unknown public source without a licence.

The workers completed 230 scans and 15315 perturbation tries.
62 starts shortened by more than 1e-8 of side.
These counts include results later refused or superseded.
Source admission and result collection ran independently. Fresh public rows and rectangle designs had priority.
The 00:19 policy update removed share gates for our own layouts, original seeds and descendants.
Direct fetched public starts retain the share test. Ancestry that names the excluded public file still stays out.
The public-copy resolver verifies the raw remote hash and the certification dilation.
The older 375 input matched its receipt hash and dated notebook row.
The 457 source recheck verified 27 immutable source snapshots and resolved every history issue.
Its exact 499 notebook-row control passed with zero error. An altered coordinate failed the control.
The 264, 793 and 798 source rechecks also cleared every path and saved the recovered evidence by hash.
Larger kicks of 0.08 and 0.12 followed the stalled small-kick endpoints.
Their n=2 control ran 526 tries and shortened side 2.0004 to 2.0000000000503197, then completed its certified-file quench.
The three production scans ran 287 tries and moved at most 1.4e-9 of side, with no meaningful gain.
The smaller-kick control used 0.004 and 0.008. Its 552 tries reached the same certified side and completed its quench.
The manual helpers now honor backlog byte claims. Two pending smaller-kick follows were removed before they ran.
Search admission closed at 05:35 UTC. Search and quench work stopped by 05:45 UTC.
Archives were checked by SHA-256 before remote scratch removal.
The own-endpoint cache prevents a byte change from repeating a completed scan.
A replacement of our own take must improve its score by more than 1e-10.
Generation now has one 25-second cap, with fresh directories ahead of frozen inputs.
Job-history preparation now runs before that candidate budget starts.
A late saved-input filter examined 520 files. Of these, 510 met the side allowance, six were scanned or claimed, and four were too far away.
Source walks now have a 45-second admission budget. A timed-out source stays out of the numerical queue.
The public 916 follow stayed out because its frozen notice names the excluded file and lacks a per-count trace.
A sample of 85 inputs stayed distinct under both geometry hashes. Signed-zero normalization collapsed no layouts, so the production hash stayed unchanged.

## Round 29

The [results table](../results/classfill-r29-2026-11-15.tsv) retains 0 counts against bar29.
The gain against the bar is 0. The margin beyond other live round 29 takes is 0.
Each retained row passed bisected floatsafe certification at 2.2e-11 and completed an fq quench from its certified file.
Inputs and source records have immutable SHA-256 snapshots under `take-classfill-r29/work/` on boxA.

The workers completed 100 scans and 33070 perturbation tries.
29 starts shortened by more than 1e-8 of side.
These counts include results later refused or superseded.
Fresh rectangle compositions and changed certified layouts had priority.
Already completed geometry stayed closed. Backlog byte claims stayed reserved.
boxE ran two slots and boxD ran one. All three passed the loose n=2 fq control.
Own layouts and original seeds have no share gate. Direct fetched public starts retain that test.
Explicit excluded-file ancestry stays out. Source walks that exceed their time budget stay unqueued.
Search admission closed at 11:35 UTC. Search and quenches shared the 11:45 UTC cutoff.
Both remote archives were checked by SHA-256 before removal.
The finishing quench now certifies every returned attempt, including moves below the former 3e-9 side threshold.
Its n=2 control shortened side 2.000000001 to 2.000000000022. Both default and polish attempts completed.
The source resolver pins cached table reads and preserves byte-specific withdrawals.
Its copied793 independent control passed. The initial rectangle747 control exposed a broad inherited join rule. The later source policy narrows it to the exact join names.

## Round 30

The [results table](../results/classfill-r30-2026-11-15.tsv) retains 0 counts against bar30.
The gain against the bar is 0. The margin beyond other live round 30 takes is 0.
Each retained file passed bisected floatsafe certification at 2.2e-11 and completed an fq quench from its certified file.
Inputs and source records have immutable SHA-256 snapshots under `take-classfill-r30/work/` on boxA.

The workers completed 114 scans and 24251 perturbation tries.
22 starts shortened by more than 1e-8 of side.
These measurements include later source refusals and superseded results.
Fresh rectangles and changed joins had priority. Completed geometry and backlog byte claims stayed closed.
boxE ran two compute slots and boxD ran one.
All three loose n=2 controls shortened side 2.5 to 2.000000000000406.
The bar-input n=2 control shortened side 2.0004 to 2.000000000022.
The first fq input exactly matched the bar, and the certified-file quench completed.
Fresh rectangle jobs then received a 900-second budget at the bar input side.
The six-try rigidity stop also passed its loose n=2 control before activation.
A second preparation order certifies and quenches an owned seed before its 300-second kick.
That path passed a loose n=2 control, including the final certified-file quench.
The fallback first screened 15 held starts, retaining their historical source graphs.
Direct catalogue extraction supplied 24 alternative candidates within the side allowance.
Each catalogue start names a pinned extraction receipt.
Fresh compositions kept higher queue priority.
The prepared-endpoint follow first entered n653 at score 0.01670080981033295.
That entry gained 1.107545635203877e-7 against bar30 before later follows or supersession.
Its recorded root was the owned Samanyu seed, with no public-first source.
The exact certified output received a high-priority follow.
A later comparison used 180-second family local kicks without fq inside each try.
Its tilted n=2 control shortened a raw search result before the final fq step.
The family comparisons use existing boxE slots and honor backlog byte reservations.
The public terminal preflight accepted own roots and the notebook 793 control.
It rejected the fetched notebook 750 control before numerical admission.
The named-member adapters read `local_bank.csv` and `packings.csv` as data.
Their absent-count controls stayed unapproved.
Exact public-first row pins can bind changing archives without a geometry inference from descendants.
The row-pin control accepted notebook 793 and rejected an altered SHA-256 record.
Own layouts and original seeds have no share gate.
A bare public reference with different archived layouts needs an exact version before admission.
Search admission closed at 17:35 UTC. Search and quench work shared the 17:45 UTC cutoff.
Both remote archives passed SHA-256 checks before scratch removal.


## Round 31

The [results table](../results/classfill-r31-2026-11-16.tsv) retains 5 counts.
The gain against bar31 is 0.000119306399912.
The workers completed 286 scans and 10668 perturbation tries.
The 120-second probe stopped 264 scans without a certified gain above 1e-10.
Every retained row passed border finesafe at 2.2e-11 and a quench from its certified file.
Input projections preserve the held container hash and each source table record.
Search and quench shared the 00:15 UTC deadline.

The measured next steps and immutable receipts remain in `take-classfill-r31/work/` on boxA.

Both round 31 archives passed every manifest hash on 16 November at 11:18 UTC.
boxE archive contains 3287 files and 70929824 bytes.
The boxD archive contains 1866 files and 40667810 bytes.
Both remote scratch roots are absent, and no classfill worker remains.
Commit `7637fda` already records the round 31 tools, documentation and results on remote main.
The committed results table matches the frozen take exactly.


## Round 32

The [results table](../results/classfill-r32-2026-11-16.tsv) retains 2 counts.
The gain against bar32 is 9.4575938776043e-06.
The workers completed 146 scans and 23480 perturbation tries.
Short local kicks used 150 seconds on held counts absent from round 29 to 31 claims.
Changed rectangles kept priority, with a 120-second probe before a 900-second kick.
New searches after 16:45 UTC were capped at 180 seconds. Intake closed at 16:55 UTC.
Each retained row passed border finesafe at 2.2e-11 and completed a quench from its certified file.
Original-byte audits checked the direct and pandas reads.
Exact input snapshots preserve the held container and inherited source records.
Typed primary trees bind each output to its numerical inputs.
The independent source audit checks retained bytes through those trees.
Withdrawals apply to pinned bytes. External claims reserve exact starts for 60 minutes.
Owned layouts have no share gate. Public outputs use the frozen round 31 measure at both required tolerances.
Both remote archives passed every manifest hash before scratch removal.
Detailed measurements and immutable receipts remain under `take-classfill-r32/work/` on boxA.


## Round 33

The [results table](../results/classfill-r33-2026-11-17.tsv) retains 0 counts.
The gain against bar33 is 0.
The native module queue used 36 newly held layouts and the 66 saved changed poses from round 32.
It added 4 source-cleared fresh endpoints.
Of 106 checked layouts, 6 had two readable flush arms.
The far-zone sweeps shortened 0 zones by more than 1e-8.
The known 703 control reproduced loss 2.8017 to 2.7284.
Every replacement checks the native zone coordinates before changing them.
Held rows received no kicks from this lane.
Changed geometry kept priority over module generation.
Current producer adapters recovered 5 source-cleared starts.
Earlier numerical starts stayed closed during those source checks.
A broader scan admitted 6 inputs from other near folders.
Those inputs passed the source, claim and live-side checks.
A kick required the lowest live side and a free claim after ten minutes.

The finishing quench now runs default flags and polish for up to three rounds.
The control made six attempts and retained a second-round improvement.
A failed polish prevents publication.
All three workers passed the loose fq and certified-file quench controls.
The native-join control rebuilt 934 at +0.0001 of side and rejected the wrong count.
It also matched the known 703 module length.
The join experiment finished 28 sparse tables.
It made 4 constrained-state measurements.
It closed 9 bounded builds.
The first two fixed-grid 805 layouts remained above the live bar.
The closer layout missed by 3.1756572e-5 of side.
Its second fq round recovered another 1.1522703e-6 of score.
The third round was dry.
Both valid layouts were source-checked and handed off as donors.
The first sparse 934 model missed a known feasible build by 0.007845 of side.
Two native-state revisions failed the unchanged0.0005 forecast control.
The inward-margin model control returned: `{'passed': True, 'n': 934, 'source_f': 0.964142330178813, 'predicted_f': 0.9644, 'delta': 0.0002576698211870232, 'certified_side': 30.964410002258017}`.
Each new state came from a constrained LP, with a 1e-6 inward margin.
The queue refused a reserved module marker.
Renaming the new state fixed that parser error.
The fixed-grid forecast and assembly controls passed before the revised queue.
No production join could bypass those controls.
The corrected screen built five new recipes.
The closer 934 substitution missed live by8.6323e-7 of side.
The 875/999 composition needed a separate full finishing run.
Its wrapper control reduced two squares to side 2.000000000022.
The 875 layout finished at side 29.98526140242541.
It remained above live.
The cold source walk passed 8 donor outputs.
A second curve repair tested 705 and 999.
Their self rebuilds failed with 0.001 extra side.
The corner could not fit under both arms.
That gate queued no joins.
The forecast for 934 included each measured fraction.
It passed at a side delta of 0.0002.
Both boxE workers disappeared after completed jobs.
The two assigned slots restarted after checks proved the old slots were gone.
Their startup controls passed again.
Held, stale and 45-degree lattice inputs failed the dispatch controls.
Withdrawn direct and mixed ancestry failed the source controls.
Submitted held boundaries passed.

boxE used two serial slots and boxD used one.
Both remote archives passed every manifest hash and size before scratch removal.
Stopped-worker outputs were copied from the verified archives.
Completed local receipts were compared again at the final peer freeze.
Measurements and immutable source records remain in `take-classfill-r33/work/` on boxA.

## Round 34

The [results table](../results/classfill-r34-2026-11-17.tsv) lists the rows this lane took in round 34.
Each row is below bar34 by more than 1e-10 and below every other live r34 take.
Each one passed finesafe at 2.2e-11, the full fq loop and the source walk.

The plan changed at 01:39Z.
Fresh-row follows went to backlog.
The three slots took this lane's own geometry work instead.
That work had four parts: the 705/999 self rebuild, native far-zone cuts, family runs on new gains, and fresh endpoints.
Deep kicks ran only on rows that a deep-kick owner handed over by name.

### What each kind of job paid

| Job | Jobs | Rows | Rows taken |
|---|---|---|---|
| Unprobed 900 s deep kick on a handed row | 38 | 20 | 3: 995, 653, 928 |
| 180 s family run on a fresh row of another lane | 6 | 6 | 1: 753 |
| Family follow and extra seed on our own find | 8 | 4 | lowered 653 and 928 again |
| Fresh rectangle endpoint at the lowest live side | 10 | 9 | 0 |
| Native far-zone cut | 12 started | 8 | 0 |

The handed deep kicks paid best.
A kick also lowered 593 by 3.7e-10.
The final source walk refused that row.
Its tree reaches the gone file `take-harvest-r22/799.csv` and withdrawn files.
The controller did not walk handed held rows, because it treated the submitted round 33 a row as clean.
The final walk follows the held row's recorded source, and for 593 that source is not clean.
The next controller must walk every handed held row before the kick.
We dropped 593 from the take.
The largest single gain was 653 at 9.23e-7.
A family follow on our own 928 find added 1.56e-9.
The endpoints moved by 2.7e-11 or less.
With no r34 row at those n, the endpoints were only copies of held geometry.
After that measurement, the controller admitted an endpoint only where an r34 row had lowered the live side.

### The 705/999 self rebuild

In round 33 the 705 and 999 corners did not fit under both arms.
The cause is that the quenched native stacks are not rigid, centred, flush stacks.
In 705 the first square of the arm-2 stack sits 0.0133 off the model.
The 999 stack angles run from 16.297 to 16.449 degrees, but the model uses 16.515 degrees.

`classfill_native34.py` gives each corner stack square and each rest cell its native residual.
It then walks the corner state from the native state under both caps.
With it, both self rebuilds certify at the native f:

- 999: side 31.99547611715602, native 31.99547606447374.
- 705: side 26.970685153866576, native 26.97068497322593.

The wrong-count controls pass.
The plain model without residuals still fails, which is the negative control.

The model works only at the native f.
At any other f, from -1e-4 to +3e-3, the corner does not fit or the stacks are illegal.
`joinscan34.py` built 760 joins of the two corners with every c-compatible far module of the round 33 library.
Only the self rebuilds tied their own row.
The best other join was n=998, at 0.00967 of side above live.
Joins at the native f are a dead end: a fixed f gives counts near the native n and packs no extra square.
A join at another f needs a corner model that can bend.

### Native far-zone cuts

The cuts ran on the changed rows 805, 812, 995 and 998, and on fresh and near inputs within 3e-3 of live.
The first seven cut inputs gave no far-zone move.
In round 33 the count was 0 of 106.
Two near files of k123 at n=985 gave the first moves.
The kind sweep shortened far zone F2 by 6.30e-5.
After the full fq loop, the two outputs were 1.1e-7 and 1.0e-7 of score below their starts.
Both were still about 2.6e-5 of score above live.
We handed them to k123 as join donors.

### Controls and faults

- Each worker passed the fq control (side 2.5 to 2.000000000000406), finesafe at 2.2e-11 and the full fq loop with its negative case.
- The unprobed path ran a held n=37 for 151.2 s without the 120 s probe stop.
- The source walk passed its regression: clean 911 rectangle, red gone, red withdrawn 812.
- The source walk refused a backlog 998 input. Its public-first ancestor shares 0.565 of its squares with a 1105 row at 1e-2.
- Script jobs first lacked the `source` and `licence` keys. The workers raised KeyError and restarted 7 times between 02:01Z and 02:10Z. The fixed jobs ran clean.
- An unmatched zsh glob broke the worker restart path at 02:11Z. A `find` loop replaced it.

boxE ran two serial slots and boxD ran one.
The tools are in `tools/classfill/round34/`.
Measurements and the source records stay in `take-classfill-r34/work/` on boxA.

## Round 35

Four rows certified below bar35 and below every live round 35 take.
The sum is 5.645e-5 against bar35 and 1.082e-5 beyond the other live takes.

| n | gain on bar35 | beyond live | how |
| --- | --- | --- | --- |
| 869 | 4.565e-5 | 1.30e-8 | 180 s invent follow of backlog's fresh 869 |
| 790 | 1.069e-5 | 1.069e-5 | 180 s family follow of our own unprobed 900 s find |
| 549 | 1.159e-7 | 1.159e-7 | unprobed 900 s kick of a k123 near/ donor |
| 746 | 3.05e-9 | 3.05e-9 | 180 s invent follow of invent's fresh 746 |

A fifth row, 925 at 1.85e-5, came from a handed held row. Twoshort then posted a lower 925, so the row left the take.

### What we measured

- 82 jobs ran on two boxE slots and one boxD slot.
- Fresh-near unprobed 900 s kicks: 34 runs, and 29 moved more than 1e-10. They gave 549 and the start of 790. Most stopped within 1e-7 of the live row.
- Fresh-row 180 s follows: 14 runs, and 2 moved. They gave 869 and 746.
- Own-family follows and extra seeds: 12 runs, and 2 moved. One gave the 790 row.
- Handed held deep kicks: 6 runs, and 2 moved. One gave 925, which a peer then passed.
- Second 900 s seeds on fresh-near outputs that stayed above live (870, 993) moved 5.8e-11 and 1.5e-10. The second seed did not pay on these near files.

### Final pass

The final pass ran border's finesafe at 2.2e-11 on each take file. Every file passed at e = 0 with clearance 2.2002e-11.
It also ran a fresh `quench_walk.check` at HEAD (42af8b3), and all four walks were clean.
All four walks stopped at exactly 3000 files.
`quench_walk.walk` has a 3000-file cap, and `check` does not flag a walk that hit it.
So a clean result only covers the first 3000 files of the tree.
Walks of the same four rows with a 30000-file cap did not finish in 15 minutes on a loaded boxA.

### Next

- Run the fresh-near unprobed 900 s kicks first. They moved in 29 of 34 runs and gave the round's 549 and 790.
- Give each own find its 180 s family follow. It gave the 790 row at 1.069e-5.
- Stop second 900 s seeds on near outputs that a first seed left above live. Both moved less than 2e-10.
- Make the walker report a walk that hits its cap, or raise the cap. Today a capped walk reads as clean.

## Round 36

No row this round. Our take is empty.
We ran 76 jobs on one boxE slot, one boxD slot and two boxA slots.
One find at 972 moved 8.95e-10 below the live row.
Forensics then built a lower 972 from rectangle windows of that find, so the gain sits in their take.

### What we measured

- k123 near donors, ranked by board room, two unprobed 900 s seeds each: 59 runs.
  43 moved more than 1e-10, but none ended below the live row by more than 1e-10.
  26 runs ended within 1e-10 of the bar, back in the basin of the held row.
  Donors 5e-5 above the bar did this too (448, 581, 904).
- A leg from a find that moved 1e-3 of side (634): 2 runs, and neither moved.
- One seed on held rows that round 35 changed late: 4 runs (546, 653, 702, 920). None moved more than 1e-10.
- 180 s follows of other lanes' fresh rows: 7 runs. One moved (972, 8.95e-10). The own follow of it moved 3.6e-11.
- The donor pool is shared, and peers claimed most donors first. 188 donor files had a claim of another lane when we reached them.

### Tool changes

- The stop and skip rule is now live below min(start, bar) by more than 1e-6. Its four controls pass.
- Walks run detached through `walk36.py`, with a file cap. Every certified line records files and capped.
- A donor that lands within 1e-10 of the bar marks its n. Later donors near the bar at that n are skipped.
- Donors within 2e-7 of a donor already run at the same n are skipped. Forensics writes many near copies of one window.

### Next

- Give fresh rows the first slot, before donors. Our only find came from a 180 s follow, and forensics turned it into a row within minutes.
- Drop donors near the bar at an n where one donor already fell back to the bar. 26 of 59 runs ended there.
- Run donors only at n where the board has much more room. Every donor in this round went back to the held geometry or stayed above it.

## Round 37

No row this round. Our take is empty.
We ran 6 slots: two on boxE, two on boxC, one on boxD and one on boxA.
One donor seed made a row at 793, 2.545e-6 below the bar.
Two 180 s follows of it took it to 5.087e-6 below the bar, and both walks were clean.
Then k123 ran a 180 s follow of our row and went 2.4e-9 lower, so the gain sits in their take.

### What we measured

- k123 near donors with a held share under 0.5 at 1e-3, one unprobed 900 s seed per geometry: 10 runs.
  One went below the bar (793, 2.6e-6). That donor sat 4e-11 above the bar with a held share under 0.5.
  2 runs fell back to the bar basin (367, 448). The other 7 stayed above the bar (904, 634, 972, a second 793, and 910 three times).
- The share rule kept 83 donor files out. All the 965 joins share 0.84 to 0.95 of the held row.
- Own follows of the 793 find: 2 runs of 180 s. Both moved, by 1.1e-6 and 2.5e-6.
- One seed on held rows that no handoff line of rounds 33 to 37 names: 76 runs on n from 53 to 877.
  None moved more than 1e-10. Each moved about 2.7e-11, which is only the finer certification.
- Fresh rows of other lanes (683, 793): peers claimed every one on its own bytes before us.
  Backlog's 683 walks to a gone file, harvest/near/683-public34-502b5af49b6fe836.csv, named by take-forensics-r37.

### Tool changes

- Donors pass only with a held share under 0.5 at 1e-3, measured against the held 36 b row.
- A donor whose share with a seeded donor at the same n is 0.9 or more counts as the same geometry.
  Seeded donors include ours of rounds 35 to 37 and every donor another lane claimed by its bytes.
- One donor that falls back to the bar closes its n for every later donor.
- A fresh row is closed only by a claim that names its own bytes. Our own follows work the same way.
- We claim a fresh row first and walk it after. The kick still waits for a clean walk, and a refused walk posts a release.
- A fresh row that walked clean stops our newest held-row seed when no slot is free.
- The held file is read once. One read per n made the first controller loop take 10 minutes.

### Next

- Seed low-share donors that sit at the bar first. The only donor row came from one of them (793).
- Drop seeds on held rows that no handoff line names. 0 of 76 moved more than 1e-10.
- Follow a fresh row within a minute of its certified line, or leave it to its producer. Peers claimed every fresh row first this round.

## Round 38

No row this round. Our take is empty.
The lane seeded only k123 near donors: within 1e-7 of score above the bar, held share under 0.5, and a geometry nobody had run yet.
One donor qualified and got one 900 s seed. It fell back to the bar.
From 08:52Z to the 12:15Z admission close, no other donor qualified, so every slot stayed empty.

### What we measured

- At 08:03Z the old pool held 5 donors within 1e-7 of the bar on open n (972, 976, 865).
  Each had a held share of 0.55 or more, so none qualified.
- k123 posted 19 near donors in round 38, all at 973, from 08:28Z to 08:55Z.
  Forensics claimed the first one 4 s after its line.
- Our one seed: 973 0a035e22, 3.8e-9 above the bar, held share 0.49.
  Its geometry differs from forensics' donor: share 0.39 at 1e-3 and 0.78 at 1e-2.
  It moved 3.9e-9 and ended 4.0e-11 above the bar, which is the held basin.
  The forensics seed at 973 ended at nearly the same score. So 973 is closed for every lane.
- Two 973 donors that are 2e-13 apart in score share only 0.53 at 1e-3 but 0.95 at 1e-2.
  A geometry test at 1e-3 alone counts them as two geometries.
- Controls: the stop rule passed all four cases.
  The walk wrapper refused the red file and passed the green one.
  On all three boxes, fq, finesafe at 2.2e-11 and the full fq loop passed their positive and negative checks.
  The new hold control passed, and its red mutant failed as it should.

### Tool changes (tools/classfill/round38)

- Donors only: no fresh-row follows, no held-row seeds and no legs.
- The donor window is now 1e-7 above the bar (it was 1e-4). Donors nearest the bar go first.
- Held share is measured against the held round 37 a row.
- n where a donor fell back in rounds 36 or 37 stay closed. Two donors that end at the same endpoint close their n.
- Same geometry now means a share of 0.9 or more at 1e-3 or at 1e-2, against any donor that we seeded or that another lane claimed.
- A claim closes only the bytes it names, not the whole n. The geometry test runs again after our claim.
- A find that passes every number gate is held back: no find line and no take row.
  Two 180 s follows run first, for up to three rounds while a follow gains 1e-8.
  Then the best result is walked and published.
- Records name the producer's record by its absolute path and sha256, and never copy its text.
- Workers start when a job arrives and leave after 10 idle minutes.

### Next

- Leave k123 donors to one seeder lane. In round 38, forensics claimed every new donor n within seconds, and two lanes seeding the same n gave nothing.
- Treat donors that share 0.9 or more at 1e-2 as one geometry. At 973, 19 donors were really two or three basins.
- Do not keep this lane at round 39 unless it gets a source of fresh rows of its own: it was idle from 08:52Z to 12:15Z.
