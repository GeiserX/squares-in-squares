# Avenue: literature and structure (2026-11-11, round 7)

**Result: five n certified below the held file, gain 0.0004096343 of score. Four come from packings published outside Kaggle on 2026-11-10 and 2026-11-11 (n = 156, 180, 268, 269, Doğa Özden), one from the border step on a packing of today's harvest (n = 495 from 452). Not submitted: the per-n files wait in `take-literature-r7` for the main session. Every other outside record is equal to ours or worse. Three scans for more free wins by structure found none.**

This avenue had three jobs: compare every n we hold with the best side published outside Kaggle, close our file under the rules that give one packing from another, and say where the 0.14 gap to the leader sits.

Words used here: "held" is the submitted file `gather/harvest-2026-11-11a.csv` (22.1947113952, gate dir `gate/cand-harvest-1111a`). "The board" is the per-puzzle board, the best side per n over all teams. "The register" is the public record list of the Squares Project, https://github.com/jlevy/squares. A "shell" is the range of n between two squares, `m² < n <= (m+1)²`.

## 1. Outside records

The lane's README said on 2026-11-07 that GitHub held nothing beyond Couzo and Samanyu-dev. That is no longer true. Since October the record work for n ≤ 324 has moved to a public register with exact certificates, and several people publish packings above 324 there too. We read these, as data only:

| source | what it holds | licence |
|---|---|---|
| https://github.com/jlevy/squares at `591644a9` (2026-11-11 11:02Z) | the register: a witness per n ≤ 324, and the intake ledgers of every reported side up to n = 1568 | MIT, third-party packings under their own terms |
| https://github.com/JoostdeWinter/square-packing at `c4e65d0` | 5 records for n ≤ 260, 15 sub-window packings for n = 413 to 910, 22 refined Kaggle packings for n = 597 to 991 | MIT |
| https://github.com/dostashev/square-packing at `b909e1b` | 11 records for n = 129 to 304 | MIT |
| https://github.com/griffcass/square-packing at `82661bc` | 39 packings for n = 103 to 307 | MIT |
| https://github.com/TheSnakeFang/squarepack-certs at `be93eb1` | Kevin Fang's certificates for `n² − n + 1` squares in a side below n, and 17 direct packings for n = 308 to 814 | MIT |
| https://github.com/franciscouzo/square-packing at `712c6a6`, https://github.com/evand/square-packing at `c801ab4` | the catalogues the register is built on | MIT |
| five public repos of Kaggle competitors (Samanyu-dev at `53551d7`, DigitalEuan, Minuii, Belloblaze-web3, cubres) | submission files | mixed, two have no licence |

Erich Friedman's "Squares in Squares" page now points to David Ellsworth's page, https://kingbird.myphotos.cc/packing/squares_in_squares.html, and the register tracks that page. So the register covers the classical tables.

`literature_targets.py` found a side published outside Kaggle for 721 of the 1,000 n. `literature_scan.py` read 695 certificates, 56 layout files and 15 submission files in the clones.

**Four n beat ours, all by Doğa Özden** (register issues 943, 944, 945 and 947, his repos `kenaznia-doga/s156-upper-bound`, `s180-upper-bound`, `s268-upper-bound-16872029849` and `s269-upper-bound`, CC BY 4.0):

| n | held side | his side | board side | gain of score | date published |
|---|---|---|---|---|---|
| 156 | 12.979165854 | 12.977053087 | 12.977053088 | 0.0001692 | 2026-11-10 |
| 180 | 13.916993523 | 13.915618503 | 13.916993522 | 0.0001025 | 2026-11-10 |
| 268 | 16.872469899 | 16.872029849 | 16.871868135 | 0.0000269 | 2026-11-10 |
| 269 | 16.901513583 | 16.900994580 | 16.889730079 | 0.0000316 | 2026-11-11 |

At n = 180 his side is below the board's side of 2026-11-09. At 156 it equals the board, and at 268 and 269 the board is still smaller.

**Everything else is equal or worse.** On 717 n the outside side is ours or larger. Where it reads smaller by about 1e-9, it is the same packing: our copy carries the 5e-11 centre dilation of `floatsafe`. Three facts worth keeping:

- Our file beats the register at n = 109, 179 and 204. The Kaggle public record is ahead of the register there.
- All 37 of de Winter's packings above 324 are larger than ours, by 4e-9 to 0.024. He measured against the register and against a merge of 2026-11-07, and the public files have moved since.
- Fang's theorem gives `n² − n + F(n)` squares in a side below n, with `F(n) = 1 + max(p + 2q)` over `16p + 21q <= n − 15`. For n = 32 that is 994 squares. We hold 998 below side 32. His composite certificates reach j = 2 at n = 28 and 29, where we hold j = 5 and 6. The theorem is never ahead of our file for n ≤ 1000.

## 2. Structure: three rules, checked on every n

| rule | check | result |
|---|---|---|
| Deletion: `L(n) <= L(n+1)` | all 999 pairs | no violation |
| Border step: `L(n + 2·floor(L) + 1) <= L(n) + 1` (one row above, one column beside) | all n, repeated until nothing moves | **one violation: 452 → 495** |
| Sub-window: any square window of a held packing that holds c whole squares is a packing of c | `literature_window.py`, every anchor on a square's left and bottom extent, all 991 donors with n ≥ 10 | no hit |
| Rectangle window plus p columns and q rows of uprights, p, q ≤ 3 | `literature_rect.py`, anchors within 3.05 of each of the donor's four corners, windows that cut up to 4.05 off the far sides | no hit beyond 452 → 495 |

**The 495 win.** The harvest of this morning brought a new 452 at side 21.763709680. One row of 22 and one column of 21 around it give 495 squares at side 22.763709681, against our 22.765477673. The gain is 0.0000795. The rowangle avenue checked this rule on 2026-11-10 and found no violation; the rule has to be run after every harvest, because a new packing can open it. `literature_border.py` does that in seconds.

**Why the scans are dry.** The near-miss list says it. For 140 values of c where we hold a tilted packing, some window of a larger held packing gives exactly our side. Our file is already closed under windows: the public merges did this work (several public notebooks are named "subset transfer"). Only 37 values of c have a window between 1e-6 and 0.004 above our side. Section 4 has the quench of those.

Controls, each watched going red and green:
- Sub-window scan: with `L(452)` raised by 0.01 in the table, the scan of donor 495 reports 452 at 21.763709680. With the real table it reports nothing.
- Rectangle scan: on the held file, donor 452 gives the 495 hit with p = q = 1.
- Repo scan: with `L(600)` and `L(758)` raised by 0.01, it reports both from a public submission file. With the real table it reports nothing.
- `literature_check.py` (pandas read, the unchanged metric, the gate's own separating-axis check at 2e-11): all five per-n files pass, and a copy of 156 with one square moved by 0.3 fails with exit 1.

## 3. Where the 0.14 sits

Our gap to the leader is 22.1947113952 − 22.0544 = 0.1403, and 0.1399 after this round. The sum of our gaps to the board is 0.1438. The board file is the copy of 2026-11-09; the leader's total has not moved since 2026-11-07, so the split below still holds. Cats and boxes hold 0.1187 of the 0.1438.

By n:

| n | gap | share |
|---|---|---|
| 1 to 300 | 0.0059 | 4% |
| 301 to 600 | 0.0457 | 32% |
| 601 to 784 | 0.0315 | 22% |
| 785 to 1000 (shells m = 28 to 31) | 0.0607 | 42% |

The gap per shell grows steadily, from 0.0048 at m = 18 to 0.0167 at m = 31.

By place in the shell, for n ≥ 300, with `k = n − m²`:

| k | n in the class | gap | per n |
|---|---|---|---|
| up to m/4 | 80 | 0.0242 | 0.00030 |
| m/4 to m/2 | 88 | 0.0387 | 0.00044 |
| m/2 to 3m/4 | 86 | 0.0338 | 0.00039 |
| 3m/4 to m | 96 | 0.0285 | 0.00030 |
| m to m + 8 | 120 | 0.0128 | 0.00011 |
| above m + 8 | 231 | 0.0000 | 0 |

So the gap is in the first half of each shell, where the side is between m and m + 1 and the packing needs a tilted band. Above `m² + m + 8` both sides hold the plain grid and nothing can be won. 407 n have a gap above 1e-6. The top 100 hold 47% and the top 200 hold 75%.

Two more exact statements from the table ([`tools/targets-2026-11-11.tsv`](../tools/targets-2026-11-11.tsv)):

- 492 n are one square short at the board's side and 122 are two short. Two short is concentrated at n > 800 (55 of the 122).
- On seven n we hold the plain grid and the board holds a tilted packing just below the whole side: 510, 605, 762, 877, 937, 999 and 1000. Together 0.00094. These are `k² − k + j` with j = 4 to 8, one or two squares past the last n where we beat the grid.

**What the next round should aim at:** shells m = 28 to 31 (n = 785 to 1000) with `m/4 < k <= 3m/4`: 59 n that hold 0.0328. Then the same band in shells 24 to 27: 51 n, 0.0200. One more square at the board's side is enough on four n in five.

## 4. Near-miss windows, quenched

`literature_window.py scan --tol -0.004 --min-drop 8` lists, for every count c, the smallest window of a larger held packing (at least 8 squares larger) and how far its side is above ours. After dropping the c where we hold the plain grid:

| | c |
|---|---|
| a window gives our side to 1e-6 | 140 |
| a window is 1e-6 to 0.004 above our side | 37 |

The 35 of those 37 with c ≥ 50 went through one pass of `engine_polish.py` (Evan Daniel's `fq`, default and polish flags, 241 s on 2 processes). This is de Winter's method, a sub-window re-optimized, on our own file.

| | c |
|---|---|
| tried | 35 |
| the quench lowered the window's side | 12 |
| ended at our side (128 and 69, to 6e-12) | 2 |
| ended below our side | **0** |

The ten others that moved stopped 2.5e-5 to 3.0e-3 above ours. The closest windows (53, 177, 106 and 740, all within 0.00012) did not move at all. So a window of one held packing does not lead below another held packing, with or without a quench.

What would change this: a quench that may also add or move whole rows, which is the search the other avenues ran and found dry. The window list itself is cheap to rerun after each harvest, and a new donor can open a window the same way the new 452 opened the border step.

## 5. The border step as a sweep (2026-11-11, round 10)

**Result: five n certified below the held file, gain 0.0007376373 of score: 542 (3.250e-05), 799 (1.052e-04), 811 (1.934e-05), 971 (5.003e-04), 986 (8.026e-05). Each is one border on a held packing, then the `fq` quench. They wait in `take-border-r10` for the main session. The step pays when the border goes on a wall where the donor's tilted band ends. It pays most where the held target is weak: 971 alone gives 0.0005. Corner windows and borders on plain grids gave nothing. Most pairs beyond a margin of 2e-3 have not run yet.**

Round 9 built one pair by hand: the held 497 plus one border, quenched, beat the held 542 by 1.18e-4. `border_sweep.py` does this for every pair, in both directions.

Words used here. The *donor* is the held packing a step starts from, and the *target* is the n it gives. The *margin* of a pair is the side of the built packing minus the held side of the target, before any quench. A *tie* is a margin within 1e-8 of zero: the held target already is that step. A *grid start* is a start whose side is within 1e-4 of a whole number: a plain grid with holes. The *give-back* is how far the quench lowers the side of a start. The *edge count* of a start is the number of tilted squares of the donor that touch the two walls where the border goes. The *base* is the held file `gather/round9-2026-11-11a.csv` with the harvest take of 19:22 UTC on top (644, 694 and 696).

The three steps:

- **b1**, one border: a row of `floor(s) + 1` upright squares above the donor and a column of `floor(s)` beside it. The side is `s + 1`. Each of the four corners gives a different start.
- **b2**, two borders. The side is `s + 2`.
- **rev**, the reverse: keep the k squares of a donor that lie nearest one corner and drop the rest.

### The pairs

`border_sweep.py enum` lists every pair whose margin is at most 1e-2:

| step | pairs | ties | not ties | of those, not a grid start | their distinct n |
|---|---|---|---|---|---|
| b1 | 4,678 | 4,222 | 456 | 115 | 112 |
| b2 | 4,495 | 4,126 | 369 | 40 | 39 |
| rev | 76,173 | 44,660 | 31,513 | 27,136 | 431 |

No pair has a margin below zero outside the tie band, so no step is a plain win. The new 696 of the harvest does not open 644: the harvest's 644 is the corner window of the harvest's 696, to 9e-14 (sides 26.847861794 and 25.847861794). Two more lists have no plain win either. One has the takes of the other lanes of this round on top (600, 640, 645, 648, 651, 756 and 800, read at 20:33 UTC). The other has this section's own takes on top. Control: with `L(542)` raised by 0.01 in the table, `enum` reports 497 → 542 at a margin of −9.2e-3.

On donors that are not grids, 16 b1 pairs and 4 b2 pairs sit within 2e-3, and 47 and 11 within 5e-3.

### Give-back by kind of start

A chain is `fq` with its default flags (loosen 2 %, compress, polish), then the deep flags, again and again while the side falls. The table has the best chain of each start.

| step | starts | distinct n | margin before | gave back more than 1e-7 | largest give-back | ended on the held side, to 3e-9 | n certified below the bar |
|---|---|---|---|---|---|---|---|
| b1, grid start | 76 | 4 | 4.2e-04 to 1.6e-03 | 0 | - | 0 | 0 |
| b1, not a grid | 86 | 37 | 8.9e-05 to 9.6e-03 | 22 | 1.79e-02 | 1 | 5 |
| b2, grid start | 72 | 4 | 4.2e-04 to 1.6e-03 | 0 | - | 0 | 0 |
| b2, not a grid | 16 | 4 | 7.8e-04 to 1.9e-03 | 0 | - | 0 | 0 |
| rev, grid start | 260 | 240 | 3.5e-09 to 1.0e-04 | 102 | 1.00e-04 | 260 | 0 |
| rev, not a grid | 70 | 70 | 3.2e-05 to 1.1e-04 | 67 | 1.06e-04 | 67 | 0 |

What ran:

- Every border pair within 2e-3. The grid starts ran on one corner and the 20 others on all four.
- 21 border pairs between 2e-3 and 1e-2, each on the corner with the highest edge count.
- The closest corner window of 240 n.
- The closest corner window that is not a grid, for 70 n.

**A grid start never moves.** All 148 border starts on a plain grid ended where they began.

**A corner window comes back to the held packing.** All 260 windows near a grid ended on the grid, which is what we hold for those n. The 70 other windows have n from 16 to 472 and margins from 3.2e-5 to 1.1e-4. 67 of them gave back their whole margin and ended on the held side to 3e-9. 3 did not move. None ended below. The file is closed under corner windows after the quench too, as section 4 found for windows anywhere.

**A border gives back only next to tilted squares.** The border starts on donors that are not grids, by edge count:

| edge count | starts | gave back more than 1e-7 | largest give-back | n certified |
|---|---|---|---|---|
| 0 | 26 | 0 | - | 0 |
| 1 to 5 | 47 | 4 | 3.12e-03 | 2 |
| 6 or more | 29 | 18 | 1.79e-02 | 3 |

On 497 → 542 the donor has one tilted square on its top wall, with its top corner at x = 4.35. The border row has 23 squares in a width of 23.79, so 0.79 of its length is free. After the quench that free length is one gap from x = 4.00 to 4.67, over the tilted square. 17 border squares and 213 donor squares changed angle, and the side fell by 8.2e-4. On 738 → 793 the donor has 13 tilted squares on its bottom wall and none on the three others. The two corners that include the bottom wall gave back 3.5e-4 and 1.9e-4. The two others gave nothing. So the end of the band needs the free length of the border to move into. A border on a wall of upright squares leaves the donor as rigid as it was.

`starts` variants 4 and up place the free length over the band end in the build. That did not help on the one start that ran: 738 → 793 gave back 9.5e-5, less than the even spread on the same corner.

**The margin does not bound the give-back.** 910 → 971 starts 2.4e-3 above the held side, beyond the first cut. Its donor has 27 tilted squares on the two walls of one corner. The first default quench of that start fell by 1.76e-2, and the chain ended 1.56e-2 below the held side. The held 971 was weak: the board's side is 31.6368, ours was 31.6768 and is now 31.6612. 925 → 986 starts 3.0e-3 above and ended 2.5e-3 below: four default quenches in a row each gave more. 756 → 811 starts 5.6e-3 above and ended 5.5e-4 below. What bounds a give-back is how far the held target is from the best packing. So the pairs to run have a high edge count and a target far from the board, at any margin.

**A cut deep quench hides a give-back.** `fq` drops a call that reaches its deadline. On 744 → 799 two deep quenches were cut at 120 s on a loaded box and the chain stopped 1.2e-3 below the held side. Continued with a 900 s deadline, the next deep quench ran 155 s and gave 1.8e-3 more.

**A kick changes where a chain ends, on a border start only.** A chain is deterministic: the same start gave the same side on both boxes. `quench --kick 1e-3 --seeds K` runs K more chains, each after `fq` moves every centre by about 1e-3 first.

| start | chains | where they ended, against the held side |
|---|---|---|
| 497 → 542, border start | 15 | 3 below (by 7.6e-4, 5.1e-4 and 1.0e-5), 7 on it to 2e-9, 1 above by 6.2e-5, 4 did not move |
| held 542 itself (control) | 4 | all 4 on it |
| 744 → 799, border start, corner 2 | 4, and 3 more from the packing of the cut chain | the cut chain 1.2e-3 below, the 6 others between 2.92e-3 and 2.98e-3 below |
| 744 → 799, corner 1 | 4 | none moved |
| 801 → 858, corner 2 | 4, and 1 more from its best packing | 2 on it to 2e-9, 2 above by 5.5e-4, and the one from the best packing did not move |
| 738 → 793, corner 2 | 4, and 1 more from its best packing | all 5 above by 1.6e-4 |
| 855 → 914, corners 1 and 2 | 8 | none moved |
| 910 → 971, corner 2 | 3 | all 3 below by 1.56e-2, on the same side to 2e-9 |
| 925 → 986, corner 2 | 3 | below by 2.0e-3, 2.5e-3 and 2.0e-3 (the third was stopped at the time limit while still falling) |

The control says the border start does the work: the same kicks on the held 542 came back to the held 542 four times. The held 542 and the held 858 are this same step already, which is why chains land on them.

### The takes

| n | donor | corner | edge count | margin before | margin after | held score | new score | gain |
|---|---|---|---|---|---|---|---|---|
| 542 | 497 | 0 | 2 | 8.09e-04 | -7.57e-04 | 0.0216493718 | 0.0216168723 | 3.250e-05 |
| 799 | 744 | 2 | 5 | 1.50e-04 | -2.97e-03 | 0.0174505719 | 0.0173453410 | 1.052e-04 |
| 811 | 756 | 2 | 46 | 5.57e-03 | -5.51e-04 | 0.0153970159 | 0.0153776804 | 1.934e-05 |
| 971 | 910 | 2 | 27 | 2.36e-03 | -1.56e-02 | 0.0165567381 | 0.0160564240 | 5.003e-04 |
| 986 | 925 | 2 | 12 | 3.04e-03 | -2.52e-03 | 0.0146066165 | 0.0145263593 | 8.026e-05 |
| total | | | | | | | | **0.0007376373** |

All pass `literature_check.py` (pandas read, the unchanged metric, the gate's own separating-axis check at 2e-11). A copy of 799 with one square moved by 0.3 fails it with exit 1.

### Conditions for a give-back

- **Tilted squares of the donor on a wall, and the border on that wall.** With none, 26 starts of 26 gave nothing. `starts` writes the edge count of every start in its manifest.
- **A long deadline.** One `fq` call takes 5 to 35 s of CPU for n from 500 to 965. A deep quench that is winning can take 150 s. Other lanes had both boxes at a load of 20 to 60. There a 60 s deadline cut three default quenches, and a 120 s deadline cut one default and two deep ones. The default is now 600 s.
- **Not a small margin.** The takes started 1.5e-4, 8.1e-4, 2.4e-3, 3.0e-3 and 5.6e-3 above the held side. Of the 21 starts beyond 2e-3 that ran, 3 ended below the held side, 11 more gave back part of their margin and 7 did not move. The closest of those are 701 → 754 (2.7e-4 short) and 933 → 994 (1.8e-3 short, stopped at the time limit while still falling).

### Round 11: the sweep on the round 10 file (2026-11-11)

**Result: four n certified below the round 10 file, gain 0.0002487774 of score: 931 (6.462e-05), 972 (1.591e-04), 986 (2.394e-05) and 994 (1.161e-06). They wait in `take-border-r11` for the main session. Three of the four donors are packings that round 10 made, so every new packing of a round is a new donor for the next one. The give-back follows the tilted squares on each of the two walls of the corner, not their sum. A corner with five or more on each wall gave back more than 1e-3 in 31 of 64 starts. A corner with none on one wall did so in 3 of 74.**

The base of this round is the held file `gather/round10-2026-11-11a.csv` (22.1892638148) with the round 10 takes of the family and modules lanes on top. Those are 28 n that are below the held file and not in it yet. `base` now leaves out a take that the held file already holds. The *distance* of an n is its held side minus the board's side (`results/per-puzzle-lb-2026-11-09.json`).

#### The pairs

`enum --max 3e-2` lists 98,960 pairs on this base: 5,731 for b1, 5,317 for b2 and 87,912 for rev. No pair has a margin below zero outside the tie band, so no step is a plain win. The border pairs that are not ties and not grid starts:

| margin | b1 pairs | with a corner of edge 6 or more | and a target 0.01 or more above the board | b2 pairs | with a corner of edge 6 or more | and a target 0.01 or more above the board |
|---|---|---|---|---|---|---|
| up to 2e-3 | 17 | 4 | 3 | 4 | 0 | 0 |
| 2e-3 to 1e-2 | 94 | 43 | 36 | 34 | 2 | 2 |
| 1e-2 to 3e-2 | 493 | 284 | 109 | 280 | 109 | 66 |

`rank` is new. It writes one line per pair and corner. The line has the edge count, the edge count of each of the two walls, and the distance of the target and of the donor.

#### What ran

99 starts on 64 pairs and 58 n, one plain chain each, and kick seeds on the wins. `fq` had 600 s per call. Both boxes were at a load of 20 to 50 from other lanes, so the list did not finish.

- **The three chains that round 10 stopped** went on from their last packing. The third seed of 925 → 986 fell 1.3e-3 more and ended 7.5e-4 below our round 10 side: 986 again. 912 → 973 gave 6e-5 more and ended 4.4e-3 above the held side. 933 → 994 did not move, 1.8e-3 above.
- **Pairs within 1e-2, corners with an edge count of 6 or more.** 49 pairs have such a corner. We took the two corners with the most edge of each pair and left out the 22 starts that round 10 ran on the same donor: 77 starts. 56 ran, on 34 pairs. 29 gave back, 16 of them more than 1e-3, and 3 ended below the held side (931, 972, 994).
- **Pairs up to 3e-2 with an edge count of 6 or more and a target 0.01 or more above the board.** 148 b1 pairs on 88 n. We ranked them by edge count (capped at 30) times distance and took the best corner of the first 60 pairs. 6 of them ran in round 10 and 12 are in the list above. Of the 42 starts beyond a margin of 1e-2, 16 ran. 10 gave back, 8 of them more than 1e-3, and the largest was 1.25e-2. None ended below the held side.
- **Two borders on the donors of the round 10 wins**, and one border on the new 799 and 811: 7 starts. The pairs with two borders are 497 → 589, 744 → 856 and 756 → 868. Two borders on 910 or 925 would pass n = 1000. 6 did not move. 756 → 868 gave back 5.4e-3 of a margin of 2.3e-2 and was still falling when stopped.
- **Small margins with an edge count of 1 to 5.** 16 starts on 8 pairs with a margin of 1.7e-3 to 2.6e-3, which round 10 did not reach. Each has one wall with no tilted square. None moved.
- **Kick seeds** on the starts that ended near the held side. One more chain of 872 → 931 ended 4.2e-5 lower than the plain chain and is the take. One more chain of 933 → 994 was stopped above the plain chain. One more chain of the round 10 start of 701 → 754 was stopped in its first round.

The same pair behaves differently on a new donor. 701 → 754 gave back 7.1e-3 on the round 9 donor and nothing on the family lane's 701, which is 2.8e-6 of score better. 933 → 994 stopped 1.8e-3 above the held side on the round 9 donor. On the family lane's 933 the first default quench fell 4.34e-3 from a margin of 4.31e-3. 813 → 870 gave nothing in round 10, on corner 3 of the round 9 donor. On corner 2 of the new 813 it gave 3.1e-3 of a margin of 4.1e-3.

#### Give-back by edge count and by distance

Rounds 10 and 11 together: the best chain of each border start on a donor that is not a grid, 197 starts. First by the tilted squares on each of the two walls of the corner:

| tilted squares on the wall that has fewer | starts | gave back more than 1e-7 | more than 1e-3 | median of those that moved | largest | ended below the held side |
|---|---|---|---|---|---|---|
| no tilted square on either wall | 26 | 0 | 0 | - | - | 0 |
| 0, and 1 or more on the other wall | 74 | 13 | 3 | 2.2e-04 | 3.1e-03 | 1 |
| 1 to 4 | 33 | 7 | 3 | 2.8e-04 | 1.6e-03 | 1 |
| 5 to 9 | 21 | 11 | 7 | 1.2e-03 | 1.2e-02 | 1 |
| 10 or more | 43 | 31 | 24 | 3.2e-03 | 1.8e-02 | 5 |

Then by the edge count (the sum over the two walls) and by the distance of the target:

| edge count | target above the board | starts | gave back more than 1e-7 | more than 1e-3 | median of those that moved | largest | ended below the held side |
|---|---|---|---|---|---|---|---|
| 0 | under 0.01 | 11 | 0 | 0 | - | - | 0 |
| 0 | 0.01 to 0.02 | 7 | 0 | 0 | - | - | 0 |
| 0 | 0.02 or more | 8 | 0 | 0 | - | - | 0 |
| 1 to 5 | under 0.01 | 29 | 3 | 2 | 1.6e-03 | 3.1e-03 | 2 |
| 1 to 5 | 0.01 to 0.02 | 27 | 1 | 0 | 3.9e-05 | 3.9e-05 | 0 |
| 1 to 5 | 0.02 or more | 12 | 0 | 0 | - | - | 0 |
| 6 to 14 | under 0.01 | 4 | 1 | 0 | 7.6e-05 | 7.6e-05 | 0 |
| 6 to 14 | 0.01 to 0.02 | 26 | 10 | 3 | 2.2e-04 | 5.6e-03 | 1 |
| 6 to 14 | 0.02 or more | 6 | 3 | 0 | 1.9e-04 | 3.5e-04 | 0 |
| 15 to 29 | under 0.01 | 8 | 4 | 4 | 5.4e-03 | 7.1e-03 | 0 |
| 15 to 29 | 0.01 to 0.02 | 28 | 18 | 11 | 1.5e-03 | 7.1e-03 | 2 |
| 15 to 29 | 0.02 or more | 14 | 8 | 7 | 1.7e-03 | 1.8e-02 | 1 |
| 30 or more | under 0.01 | 1 | 1 | 1 | 6.1e-03 | 6.1e-03 | 1 |
| 30 or more | 0.01 to 0.02 | 11 | 8 | 6 | 1.9e-03 | 5.7e-03 | 0 |
| 30 or more | 0.02 or more | 5 | 5 | 3 | 3.2e-03 | 1.2e-02 | 1 |

The starts with an edge count of 6 or more, by the distance of the target, by the distance of the donor and by the margin:

| target above the board | starts with edge 6 or more | gave back more than 1e-7 | more than 1e-3 | median of those that moved | largest | ended below the held side |
|---|---|---|---|---|---|---|
| under 0.01 | 13 | 6 | 5 | 5.4e-03 | 7.1e-03 | 1 |
| 0.01 to 0.02 | 65 | 36 | 20 | 1.2e-03 | 7.1e-03 | 3 |
| 0.02 or more | 25 | 16 | 10 | 1.4e-03 | 1.8e-02 | 2 |

| donor above the board | starts with edge 6 or more | gave back more than 1e-7 | more than 1e-3 | median of those that moved | largest | ended below the held side |
|---|---|---|---|---|---|---|
| under 0.003 | 24 | 11 | 8 | 4.3e-03 | 7.1e-03 | 3 |
| 0.003 to 0.01 | 28 | 14 | 3 | 4.7e-04 | 7.1e-03 | 1 |
| 0.01 to 0.02 | 45 | 28 | 19 | 1.5e-03 | 1.2e-02 | 0 |
| 0.02 or more | 6 | 5 | 5 | 1.0e-02 | 1.8e-02 | 2 |

| margin before | starts with edge 6 or more | gave back more than 1e-7 | more than 1e-3 | median of those that moved | largest | ended below the held side |
|---|---|---|---|---|---|---|
| under 2e-3 | 10 | 4 | 1 | 3.5e-04 | 1.7e-03 | 0 |
| 2e-3 to 5e-3 | 20 | 13 | 5 | 3.4e-04 | 1.8e-02 | 3 |
| 5e-3 to 1e-2 | 55 | 30 | 20 | 1.5e-03 | 1.0e-02 | 3 |
| 1e-2 to 3e-2 | 18 | 11 | 9 | 4.4e-03 | 1.2e-02 | 0 |

How to read them:

- **Count the tilted squares per wall.** With ten or more on each wall, 24 of 43 starts gave back more than 1e-3. Five of them ended below the held side. With five to nine on each, 7 of 21 gave back that much and 1 ended below. With one to four on the weaker wall, 3 of 33. With none on one wall, 3 of 74, whatever the other wall has (up to 18). The edge count hides this: a corner with 18 on one wall and none on the other has an edge count of 18.
- **The distance of the target does not say how often a start gives back.** Under 0.01, 5 of 13 starts gave back more than 1e-3. Between 0.01 and 0.02, 20 of 65 did. At 0.02 or more, 10 of 25 did. The distance says how far a give-back can go. The two largest (1.8e-2 on 971 and 1.0e-2 on 972) have a target 0.040 and 0.033 above the board and a donor 0.033 and 0.028 above it. Six starts have a donor 0.02 or more above the board: five gave back more than 1e-3, with a median of 1.0e-2.
- **A margin beyond 6e-3 has not been closed.** The nine takes of the two rounds started 1.5e-4 to 5.6e-3 above the held side. 18 starts with a margin between 1e-2 and 3e-2 ran: 9 gave back more than 1e-3, the largest 1.2e-2, and none ended below.
- **The list for a round is short.** It is `rank --both-min 5 --max 1e-2`, sorted by margin. On this base that is 40 corners. 28 ran in this round and 8 in round 10 on the same donor. Beyond 1e-2, only a pair whose donor and target are both 0.02 or more above the board is worth a chain.

#### The takes

| n | donor | corner | edge count | margin before | margin after | held score | new score | gain |
|---|---|---|---|---|---|---|---|---|
| 931 | 872 | 2 | 26 | 5.13e-03 | -1.97e-03 | 0.0137400589 | 0.0136754344 | 6.462e-05 |
| 972 | 911 | 2 | 36 | 5.18e-03 | -4.96e-03 | 0.0162644600 | 0.0161054067 | 1.591e-04 |
| 986 | 925 | 2 | 12 | 5.56e-03 | -7.52e-04 | 0.0145263593 | 0.0145024209 | 2.394e-05 |
| 994 | 933 | 2 | 27 | 4.31e-03 | -3.66e-05 | 0.0131033666 | 0.0131022053 | 1.161e-06 |
| total | | | | | | | | **0.0002487774** |

The donors: 872 is the family step's packing in the held file. 911 is the modules take of round 10 and 933 the family take of round 10, neither in the held file yet. 925 is the held packing, and 986 is the round 10 chain gone on. `take.tsv` names each donor's own source and licence. All four pass `literature_check.py`. A copy of 972 with one square moved by 0.3 fails it.

#### Not run yet

- 47 of the 119 starts picked for this round did not run. 21 are within 1e-2: the second corner of a pair, mostly with one wall empty. 26 are beyond 1e-2.
- Eight chains were stopped while still falling, all more than 6e-3 above the held side. They are 756 → 868 with two borders, 911 → 971, 923 → 984, 924 → 984 and 637 → 687. The others are 920 → 981 and 917 → 978 on a second corner, and the kick chain of 701 → 754.
- Kick seeds on 972, 986 and 994, and on 756 → 811 (2.3e-4 above the held side) and 813 → 870 (1.0e-3 above).
- After the next harvest or take: `base`, `enum`, `rank --both-min 5 --max 1e-2` and a chain on every corner whose donor or target moved.

### Round 12: the sweep on the round 11 file (2026-11-12)

**Result: four n certified below the round 11 file, gain 0.0001435761 of score: 852 (3.751e-05), 913 (5.626e-05), 972 (4.669e-05) and 994 (3.116e-06). They wait in `take-border-r12` for the main session. Two of the four are plain wins: a border on a packing that is already below the held side before any quench. One came from the base itself (795 → 852), and one from a new packing of the family lane that a poll found during the round (854 → 913). 972 is the corner that won in round 11, run again because its donor 911 moved: the plain chain fell 1.16e-2 from a margin of 1.01e-2, the largest margin a border has closed. Kick seeds mostly stayed in the basin of their first chain.**

The base is the held file `gather/round11-2026-11-11b.csv` (22.1846685445) with the smallest take of each n over the live take dirs on top. At the start that replaced 1 n. Five polls (01:04 to 02:04 UTC) rebuilt it on the takes of this round; the last one replaced 40 n. The bar of each start is the held side of its own base.

#### The pairs

`enum --max 3e-2` on the first base lists 98,366 pairs: 5,732 for b1, 5,318 for b2 and 87,316 for rev. Not counting ties, 456 b1 pairs on 130 n and 369 b2 pairs on 57 n have a margin up to 1e-2. One pair is below the tie band: 795 → 852, margin -9.06e-4. `rank --both-min 5 --max 1e-2` gives 36 corners. 15 of them have a donor or a target among the 61 n that moved in round 11. 5 of those 15 ran in round 10 or 11 on the same start, so 10 ran.

#### What ran

One process on boxA and two on boxC, from 01:02 to 02:13 UTC. boxA sat at a load of 20 to 32 and gave the process about half a core.

- **The plain win 795 → 852, three corners.** Corner 2 (14 tilted squares on one wall, none on the other) fell 1.9e-4 below the plain border: the take. Corner 1 (none and 14) fell 1.8e-6 and corner 0 (none on either wall) 3.4e-7. The polish lane holds the corner 0 result in `take-polish-r12`.
- **The 10 moved corners within 1e-2, one plain chain each.** 8 gave back more than 1e-7, 5 more than 1e-3, and 1 ended below the held side: 933 → 994, 3.445e-3 from a margin of 3.347e-3. 756 → 811 gave 5.3e-3 of 5.5e-3 and ended 1.65e-4 above. 813 → 870 gave 2.6e-3 of 5.4e-3. 856 → 915 gave 3.9e-5 of 5.0e-4. 912 → 973 and 745 → 800 each gave 1.7e-3. 740 → 795, 807 → 864, 701 → 754 and 863 → 922 gave nothing that counts.
- **Kick seeds** (`--seeds K --sfrom 1`, sigma 1e-3). 911 → 972: the plain chain on the moved 911 ended 1.456e-3 below our round 11 take, and seeds 1 and 2 ended 2.7e-6 and 7.4e-8 lower again. Seed 3 was stopped at the end of the round, 8.1e-4 above seed 1. 933 → 994: seed 1 ended 4.7e-8 below seed 0, seed 2 was stopped above it. 872 → 931: seeds 2 and 3 both ended 8.1e-5 above the held side (the round 11 take came from seed 1). 813 → 870: seed 1 ended 5.6e-4 lower than seed 0, still 2.3e-3 above. 756 → 811 and 856 → 915: seed 1 did not get below seed 0. On the 913 win, three seeds at sigma 1e-3 and three at 5e-3: five ended within 2e-9 of seed 0 and one 3.0e-5 above it. 925 → 986 did not run.
- **Beyond a margin of 1e-2.** On the first base only three corners with five or more tilted squares on each wall have a donor and a target both 0.02 or more above the board: 911 → 972 (above), 911 → 971 and 910 → 971. 910 → 971 is round 10's own win, so its margin is what that chain gave back. The stopped round 11 chain 911 → 971 did not run. One corner below 1e-2 with both n far from the board ran: 851 → 910 (margin 5.0e-3, 4 and 1 tilted squares on the walls). It did not move.
- **Polls for new packings** of the family, readers and modules lanes, and of the other live take dirs. Each new n got one border to n + 2m + 1 on its corner with the most tilted squares on the weaker wall, unless that corner had none on one wall, the margin was beyond 1e-2 with the target under 0.02 above the board, or the target was past 1000. That gave 8 starts:

| poll (UTC) | start | donor from | margin | tilted squares on the walls | result |
|---|---|---|---|---|---|
| 01:18 | 702 → 755 | family | 3.84e-3 | 13, 12 | did not move |
| 01:18 | 649 → 700 | family | 8.47e-3 | 11, 13 | did not move |
| 01:18 | 921 → 982 | zones | 8.22e-3 | 17, 15 | gave 4.8e-3, ended 3.4e-3 above |
| 01:55 | 854 → 913, corner 2 | family | -8.50e-4 | 9, 0 | fell 8.5e-4 more: the take |
| 01:55 | 854 → 913, corner 1 | family | -8.50e-4 | 0, 9 | fell 8.2e-5 more |
| 01:55 | 854 → 913, corner 0 | family | -8.50e-4 | 0, 0 | did not move |
| 01:55 | 933 → 994 | family | 3.31e-3 | 15, 14 | gave 2.9e-3, stopped while falling, 3.8e-4 above |
| 02:04 | 854 → 913, corners 2 and 1 | family, 4e-6 smaller side | -8.54e-4 | 9, 0 and 0, 9 | fell 5.8e-4 and 3.9e-4: 2.6e-4 above the take |

The polls at 01:04 and 01:35 found no start that passed these rules. 923 → 984 on the zones lane's new 923 (8.45e-3, 17 and 17) was built and did not run.

#### Give-back by wall count

The best chain of each start of this round. A start on a new donor counts apart from the start of the same id on the old donor.

| tilted squares on the wall that has fewer | starts | chains | gave back more than 1e-7 | more than 1e-3 | largest | ended below the held side |
|---|---|---|---|---|---|---|
| any, on a plain win (margin below 0) | 8 | 15 | 7 | 0 | 8.5e-04 | 8 |
| 0 | 0 | 0 | 0 | 0 | - | 0 |
| 1 to 4 | 2 | 2 | 1 | 0 | 1.7e-07 | 0 |
| 5 to 9 | 4 | 6 | 4 | 2 | 5.3e-03 | 0 |
| 10 or more | 12 | 19 | 8 | 7 | 1.2e-02 | 2 |

26 starts ran, with 42 chains. The rules of round 11 kept every corner with no tilted square on one wall out of the list, so the 0 line is empty. On a plain win the give-back is what the quench found below the plain border. The 2 starts below the held side with 10 or more on each wall are 911 → 972 and 933 → 994.

#### The takes

| n | donor | corner | tilted squares on the walls | margin before | margin after | held score | new score | gain |
|---|---|---|---|---|---|---|---|---|
| 852 | 795 | 2 | 14, 0 | -9.06e-04 | -1.10e-03 | 0.0174914037 | 0.0174538939 | 3.751e-05 |
| 913 | 854 | 2 | 9, 0 | -8.50e-04 | -1.70e-03 | 0.0167345773 | 0.0166783157 | 5.626e-05 |
| 972 | 911 | 2 | 18, 18 | 1.01e-02 | -1.46e-03 | 0.0161054067 | 0.0160587183 | 4.669e-05 |
| 994 | 933 | 2 | 14, 14 | 3.35e-03 | -9.83e-05 | 0.0131022053 | 0.0130990891 | 3.116e-06 |
| total | | | | | | | | **0.0001435761** |

The donors: 795 and 911 are in the held file. 854 is the family lane's take of this round, not in the held file yet; 933 is the held packing from the round 11 file. The 913 packing stands by itself whether or not 854 is taken. `take.tsv` names each donor's own source and licence. No other live take dir holds a smaller 852, 913, 972 or 994 (checked 02:15 UTC). All four pass `literature_check.py` against `gate/cand-round11-1111b/details.csv`.

#### How to read round 12

- **Plain wins come from new packings.** A new packing of n is a new donor for n + 2m + 1, and a border on it can land below the held side before any quench. 795 → 852 was a plain win on the base, and 854 → 913 on a packing that the family lane made during the round. That 854 appeared between the polls at 01:35 and 01:55. Poll every 10 minutes, and run the corners of a plain win first: they take seconds to minutes.
- **On a plain win, run every corner.** On 852 and 913 the corner with tilted squares on one wall gave 2 to 10 times more than the others. A donor 4e-6 smaller on the side gave a 913 that is 2.6e-4 worse. So a better donor does not always give a better result.
- **A moved donor makes an old pair new.** 911 → 972 won in round 11 and won again on the moved 911, from a margin of 1.01e-2. Round 11 said that no margin beyond 5.6e-3 had been closed. This one had 18 tilted squares on each wall and both n 0.028 above the board.
- **Kick seeds mostly stay in the basin of seed 0.** 17 kick chains ran. 4 ended more than 1e-8 below their seed 0: 870 by 5.6e-4 (still 2.3e-3 above the bar), 972 by 2.7e-6 on two seeds and 994 by 4.7e-8. Larger kicks (sigma 5e-3) did not change that on 913. A kick pays only where seed 0 ended within about 1e-4 of the bar, and then by little.
- **Family donors with tilted walls do not all give back.** 702 → 755 and 649 → 700, with 11 or more tilted squares on each wall, did not move at all, and neither did 701 → 754 on the family 701 in round 11. 933 → 994 and 854 → 913 on family donors did give.

#### Not run yet

- 925 → 986 kick seeds 3 to 5, 911 → 972 seed 3 (stopped while falling, 8.1e-4 above seed 1), the stopped round 11 chain 911 → 971, and 913 → 973 and 793 → 850 beyond 1e-2.
- 923 → 984 on the zones lane's new 923 (margin 8.45e-3, 17 and 17), and 933 → 994 on the family's newest 933 (stopped while falling, 3.8e-4 above the held side).
- A trap in `cert`: it names a donor's source from the take dirs as they are when `cert` runs. When another lane has replaced that donor since `starts` built the corner, the row names the wrong packing. It happened to 913 and 994 in this round, and we wrote their rows of `take.tsv` again by hand. The fix is to write the donor's source into the manifest at `starts`.
- The next round: rebuild the base on the round 12 file, poll the take dirs every 10 minutes and run each plain win on all its corners, then `rank --both-min 5 --max 1e-2` on the corners whose donor or target moved.

### Round 13: the sweep on the round 12 file (2026-11-12)

**Result: three n certified below the round 12 file, gain 0.0002344757 of score: 542 (1.624e-04), 852 (5.271e-05) and 755 (1.940e-05). They wait in `take-border-r13` for the main session. 542 and 852 are plain wins on new packings of other lanes: the soft lane's 497 and the family lane's 795. 755 is a corner whose donor 702 moved in round 12. It closed a margin of 4.04e-3.**

The base is the held file `gather/round12-2026-11-12a.csv` (22.1822910977), with the smallest take of each n over the live take dirs on top. The live take dirs are `take-*-r13` of family, readers, corners, modules, soft, polish and gadget. At the start no take dir had a take, so the base was the held file. Nine polls (04:02 to 05:12 UTC) rebuilt it. The last one replaced 71 n. The bar of each start is the held side of its own base.

#### The fix in `cert`

`base` now writes three more columns into its details table for each n it replaces: the take dir with the time of the base, the source and the licence. `starts` copies the donor's three into the manifest (`donor_take`, `donor_source`, `donor_licence`). `cert` names a take donor from the manifest, so a donor that another lane replaces after `starts` keeps its source. A manifest from before these columns still reads the take dirs at `cert` time, and `cert` prints a line when it does.

The control is `take-border-r13/work/ctl/ctl.sh` on boxA. A fake take dir holds n = 795 with source A when `starts` builds 795 → 852. Then its source changes to B, as when another lane replaces 795. The fixed `cert` names A. The same dir with the donor columns cut from the manifest names B, which is the round 12 trap.

#### The pairs

`enum --max 3e-2` on the first base lists 97,940 pairs: 5,732 for b1, 5,313 for b2 and 86,895 for rev. Not counting ties, 435 b1 pairs on 131 n and 346 b2 pairs on 55 n have a margin up to 1e-2. One pair is below the tie band: 497 → 542, margin -2.19e-3, because 497 moved in round 12. `rank --both-min 5 --max 1e-2` gives 33 corners. 17 of them have a donor or a target among the 57 n that moved in round 12. 8 of those 17 had run before on the same start, so 9 ran, and the round 12 chain 933 → 994 went on from its record.

#### What ran

Two processes ran on boxC and one on boxA, from 03:59 to 05:13 UTC. boxA sat at a load of 2 to 7 and gave its process a full core this time.

- **Plain wins, 16 starts.** All 16 ended below the held side.

| poll (UTC) | donor | start | corners | best result | margin before | margin after |
|---|---|---|---|---|---|---|
| 03:58 | held 497 (moved in round 12) | 497 → 542 | 0 to 3, then 4 kick seeds on each | no corner and no kick moved | -2.19e-3 | -2.19e-3 |
| 04:10 | the family lane's 795 | 795 → 852 | 0 to 3 | corner 2 (11 and 2 tilted squares) fell 7.6e-4 more, and corners 0, 1 and 3 did not move | -7.52e-4 | -1.52e-3 |
| 04:25 | the same 795 | 795 → 852, corner 2 | gap variants 6, 10, 14 and 46 | variant 6 (the free length of the row over the first tilted square on the top wall) 2.2e-5 below the even spread, the others within 3e-6 of it | -7.52e-4 | -1.54e-3 |
| 04:47 | the soft lane's 497 | 497 → 542 | 0 to 3 | corners 1 and 3 fell 6.8e-5 more, corners 0 and 2 did not move | -3.71e-3 | -3.78e-3 |

- **The 9 moved corners within 1e-2, one plain chain each.** 6 gave back more than 1e-7, and 1 ended below the held side. That one is 702 → 755, which gave 4.58e-3 from a margin of 4.04e-3. 921 → 982 gave 4.9e-3 of 8.2e-3, 926 → 987 2.1e-3 of 7.8e-3 and 923 → 984 1.2e-3 of 8.4e-3. 740 → 795 and 818 → 875 gave less than 1e-4. 756 → 811, 757 → 812 and 863 → 922 did not move.
- **The round 12 leftovers.** 933 → 994 went on from its record and stopped 9.9e-4 above the held side. 911 → 972 seed 3 ended 7.4e-8 above the held 972, on the side of seed 1. The round 11 chain 911 → 971 fell about 1e-5 in its last three rounds and was still 1.55e-2 above the held side, so we stopped it. 913 → 973 and 793 → 850 (x3) did not move. 923 → 984 on the zones lane's 923 of round 12 did not run, because the round 12 file holds another 923. The 925 → 986 kick seeds did not run, because seed 0 ended 2.9e-3 above the held side.
- **New donors from the polls.** Each new n got one border to n + 2m + 1 on the corner with the most tilted squares on the weaker wall. It ran when both walls had tilted squares and the margin was under 1e-2. The margin could also be beyond 1e-2 if the target was 0.02 or more above the board. That gave 9 starts besides the plain wins:

| donor from | start | margin | tilted squares on the walls | result |
|---|---|---|---|---|
| polish (923) | 923 → 984 | 3.85e-3 | 9, 6 | did not move |
| polish (750) | 750 → 805 | 3.73e-3 | 4, 5 | did not move |
| family (702) | 702 → 755 | 4.03e-3 | 13, 12 | did not move (the held 702 gave the take) |
| polish (684) | 684 → 737 | 3.68e-3 | 4, 4 | did not move |
| polish (756) | 756 → 811 | 5.47e-3 | 12, 10 | gave 5.04e-3, ended 4.3e-4 above |
| polish (926) | 926 → 987, corner 0 | 7.64e-3 | 7, 11 | did not move |
| family (649) | 649 → 700 | 8.46e-3 | 8, 13 | did not move |
| readers (928) | 928 → 989 | 7.23e-3 | 10, 8 | did not move |
| never run before | 804 → 861 | 5.87e-3 | 15, 15 | gave 3.17e-3, ended 2.7e-3 above |

The family lane's 854 on the new 795 had not appeared by 05:12 UTC, so 854 → 913 did not run.

#### Give-back by wall count

The best chain of each start of this round. A start on a new donor counts apart from the start of the same id on the old donor.

| tilted squares on the wall that has fewer | starts | chains | gave back more than 1e-7 | more than 1e-3 | largest | ended below the held side |
|---|---|---|---|---|---|---|
| any, on a plain win (margin below 0) | 16 | 32 | 7 | 0 | 7.9e-04 | 16 |
| 0 | 0 | 0 | 0 | 0 | - | 0 |
| 1 to 4 | 2 | 2 | 0 | 0 | - | 0 |
| 5 to 9 | 6 | 6 | 2 | 1 | 2.1e-03 | 0 |
| 10 or more | 12 | 12 | 8 | 7 | 1.2e-02 | 1 |

The leftover 911 → 972 is not in the table, because its bar moved to its own round 12 result. The 10 or more line includes the stopped 911 → 971 and 933 → 994. Their give-back counts the chains of earlier rounds too.

#### The takes

| n | donor | corner | tilted squares on the walls | margin before | margin after | held score | new score | gain |
|---|---|---|---|---|---|---|---|---|
| 542 | 497 (soft lane) | 1 | 0, 2 | -3.71e-03 | -3.78e-03 | 0.0216168723 | 0.0214545001 | 1.624e-04 |
| 852 | 795 (family lane) | 2, gap variant 6 | 11, 2 | -7.52e-04 | -1.54e-03 | 0.0174538939 | 0.0174011855 | 5.271e-05 |
| 755 | 702 (held) | 2 | 12, 11 | 4.04e-03 | -5.33e-04 | 0.0159790329 | 0.0159596378 | 1.940e-05 |
| total | | | | | | | | **0.0002344757** |

`take.tsv` names each donor as `starts` saw it: the 497 of `take-soft-r13` and the 795 of `take-family-r13`, with the time of the base. Both 542 and 852 stand by themselves whether or not the donor is taken. The held 542 and 852 were border packings of the old donors, so these two replace earlier border takes.

#### How to read round 13

- **Plain wins come from other lanes' new packings, and they pay most.** 542 and 852 give 92% of the gain. Both donors were new packings of this round or the last. The poll caught the soft lane's 497 about two minutes after it appeared.
- **A plain win on a donor with almost no tilted squares on its walls gives the bare border.** The held 497 has one tilted square on its walls. No corner moved, and 16 kick chains did not move either. The soft lane's 497 is another layout. Two of its corners fell 6.8e-5.
- **Gap placement on a plain win is worth little.** The four gap variants of 852 corner 2 ended within 2.2e-5 of the even spread.
- **A small change to the donor can change the give-back completely.** 756 → 811 did not move on the held 756. It gave 5.04e-3 on the polish lane's 756, whose score is only 3.4e-7 lower. 702 → 755 is the reverse. It gave 4.58e-3 on the held 702 and nothing on the family lane's 702. So a moved donor is worth one chain even when the move is tiny.
- **Corners with fewer than 5 tilted squares on a wall still gave nothing** (2 starts, plus 2 more in round 12).

#### Not run yet

- 854 → 913 on the family lane's 854 from the new 795 (the family lane was still walking it at 05:12 UTC). The round 12 913 is a border on the old 854.
- 756 → 811 on the polish lane's 756 ended 4.3e-4 above the held side. That is the nearest miss of the round, but it is beyond the 1e-4 rule for kick seeds.
- The rule for walls without tilted squares left out the three starts with the smallest margins of the round. 738 → 793 is on the family lane's 738 (margin 2.5e-4, 11 and 0 tilted squares). 535 → 582 and 908 → 969 are on the polish lane's donors (margin 8.8e-5, at most one tilted square on a wall).

### Round 14: the sweep on the round 13 file (2026-11-12)

**Result: three n certified below the round 13 file, gain 0.0001896 of score: 913 (1.703e-04), 972 (1.050e-05) and 644 (8.869e-06). They wait in `take-border-r14` for the main session. 913 and 972 are borders on near layouts of the family lane. A near layout is a packing that ends a little above the held side, so it is not a take, but its layout is new. One border on a near 854 and the quench gave back 5.4e-3 from a margin of 8.5e-4. A gap in the border's column over the first tilted square gave 6e-4 more. 644 is a corner window of the held 696, the only plain win of the enum. The small margins that round 13 left out gave nothing below the held side.**

The base is the held file `gather/round13-2026-11-12a.csv` (22.1697213494), with the smallest take of each n over the live take dirs on top. The live take dirs are `take-*-r14` of family, readers, corners, modules, soft and polish. At 06:25 UTC no take dir had a take, so the first base was the held file. Polls every 10 minutes from 06:39 to 08:02 UTC rebuilt it. The bar of each start is the held side of its own base.

#### The pairs

`enum --max 3e-2` on the first base lists 101,301 pairs: 5,729 for b1, 5,313 for b2 and 90,259 for rev. Not counting ties, 436 b1 pairs on 130 n and 346 b2 pairs on 55 n have a margin up to 1e-2. One pair is below the tie band. It is a corner window: the 644 squares of the held 696 nearest corner 0, margin -2.25e-4. The held 696 came in round 13, one shell down from the public 751.

`rank --both-min 5 --max 1e-2` gives 22 corners. 16 of them have a donor or a target among the 134 n that moved in round 13. 12 of those 16 had run before on a start with the same bytes, so 4 ran. We compare the md5 of each new start file with every start file of rounds 10 to 13. A target that moved while its donor did not gives the same start and a lower bar, so it needs no new chain.

#### Near layouts as donors

The family lane keeps every build that ends within 1e-4 of the held side in a `near/` folder. At 06:44 UTC it wrote that its 854, one shell up from the held 795, ended 4.8e-8 above the held 854. That 854 is not a take. But one border on it is a start that never ran. Its corner 1 has no tilted square on the top wall and 9 on the right wall. So the rule of five on each wall would leave it out. We ran it anyway, on all four corners.

By 07:25 UTC the family lane had written 14 near 854 files with distinct bytes, and a take of 854 1.1e-9 below the held one. Each is the same structure from another cut or trust radius. We ran 9 of them, and the take. The table gives the side after the quench minus the held side of 913 (30.719840010). The margin before is 8.5e-4 to 9.0e-4 on every donor. Gap variant 5 is corner 1 with the column's free length as one gap beside the first tilted square of the right wall.

| donor 854 (cut, trust radius) | above the held 854 | corner 1 (0 and 9 tilted) | corner 2 (9 and 0) | corners 0 and 3 | corner 1, gap variant 5 |
|---|---|---|---|---|---|
| 0.65, 1e-3 | 4.8e-8 | -4.54e-3 | +2.9e-4 | did not move | -5.13e-3 |
| 0.5, 1e-3 | 1.6e-5 | -4.53e-3 | +2.1e-5 | - | -5.14e-3 |
| 0.9, 1e-3 | 1.6e-5 | -4.59e-3 | +2.1e-5 | - | -5.13e-3 |
| 0.3, 1e-3 | 3.9e-6 | +7.9e-4 | 0 | - | -5.14e-3 |
| 0.9, 5e-4 | 1.6e-5 | +7.9e-4 | +5.0e-5 | - | -5.09e-3 |
| 0.1, 2e-3 | 1.6e-8 | -4.56e-3 | 0 | - | -5.14e-3 |
| 0.8, 5e-4 | 3.9e-6 | -4.53e-3 | +3.0e-5 | - | - |
| 0.65, 1.2e-3 | 5.4e-5 | -2.78e-3 | +2.9e-4 | - | - |
| the family take (0.1, 2e-3, second draw) | -3.1e-8 | -4.53e-3 | +3.0e-5 | did not move | -5.11e-3 |
| 0.5, 2e-3, second draw (0 and 15 tilted on corner 1) | 1.7e-8 | -2.25e-3 | 0 | - | **-5.15e-3** |

- **Corner 1 gave back 5.4e-3 on six donors, 3.1e-3 and 3.7e-3 on two, and less than 1e-4 on two.** The donors differ by at most 5e-5 in side. So the layout near the wall decides the give-back.
- **Gap variant 5 gave back 5.9e-3 to 6.0e-3 on all eight donors** where it ran, also where the plain corner 1 gave nothing. Three chains ended on the same side to 1e-9 (30.714700539). The take is the one donor with 15 tilted squares on that wall: 5.6e-6 lower again. Other gap places on corner 1 (variants 9 to 37) gave 0 to 5.8e-4.
- **Corner 2 comes back to the held 913.** Two donors ended on it to 2e-9. The held 913 is round 12's corner 2 on the old 854.
- **Kick seeds stayed in the basin.** Three on the 0.3 donor's variant 5 ended 0 to 2.6e-5 above seed 0. Two on the take's variant 5 ended 1.8e-4 and 2.8e-3 above it. One of two on the 0.9 donor's corner 1 ended 1.5e-5 below its seed 0, still 5.2e-4 above variant 5.

The same idea on the near 911s gave 972. Three distinct 911s sat 6e-6 to 1.4e-5 above the held 911, one shell down from the held 974. Corner 2 has 18 and 17 tilted squares. On one donor it gave back 1.19e-2 from a margin of 1.16e-2 and ended 3.3e-4 below the held side. On the two others it gave 1.15e-2 and ended 8.4e-5 above. Corner 1 (0 and 18) gave 1.6e-3. Gap variant 6 of corner 2 gave 7.5e-4 on two donors.

Other near layouts did not give a take. 862 → 921 (17 and 16) gave 2.3e-3 of 1.26e-2 on corner 2 and 1.3e-3 on corner 1. 803 → 860 (15 and 15) gave 4.3e-3 of 1.53e-2. 740 → 795 gave 3.3e-4 on corner 2. 701 → 754 gave 7.8e-5 on corner 1. 813 → 870 did not move on either corner.

#### What else ran

One process on boxA and two on boxC, from 06:26 to 08:02 UTC.

- **The plain win 696 → 644.** The window itself is the take: the quench gave 3e-8 more, and two kick seeds ended on or above it. The window of the public 751 for 697 (margin 3.2e-5) did not move.
- **The small margins of round 13, all four corners each.** 738 → 793 is now on the round 13 file's 738. Its margin is 5.8e-4, with 8 and 0 tilted squares on corners 1 and 2. Corner 2 gave 1.9e-4, corners 1 and 3 gave 7e-5, corner 0 nothing. 535 → 582 and 908 → 969 (8.8e-5) did not move on any corner. Nor did 788 → 845 and the two borders 788 → 904 (6.1e-5, at most one tilted square on a wall), 629 → 680 (3.8e-4) and 227 → 258 (1.8e-4). That is 24 starts with at most one tilted square on each wall, and none moved. Corner 3 of 738 → 793 has none on either wall and still gave 7.2e-5.
- **Kick seeds on 756 → 811.** Three seeds on round 13's start on the polish lane's 756 did not move. After the kick the first quench ended above the start, so each chain stopped there. The plain corner on the held 756 of this round did not move either.
- **Moved corners within 1e-2.** 755 → 810 on round 13's 755 gave 4.4e-3 of 7.5e-3. 921 → 982 on the held 921 gave 5.3e-3 of 6.8e-3 and ended 1.5e-3 above. On the polish lane's 921 it gave 3.6e-3. 859 → 918 gave 4.5e-4 of 8.0e-3. 928 → 989 and 701 → 754 on new takes did not move. 755 → 810 on the soft lane's new 755 (12 and 12 tilted squares, margin 3.8e-3) gave 6.4e-4 in three rounds and was stopped 3.1e-3 above.
- **New donors with 1 to 4 tilted squares on the weaker wall.** 11 starts, none moved.
- **Gap variants on the corners of earlier wins.** Variant 10 of corner 2 ran on six pairs. They are 933 → 994, 872 → 931, 925 → 986, 702 → 755, 911 → 972 and 910 → 971. Variant 6 ran on the first two. None ended below. 994 gave 2.8e-3 and ended 1.7e-3 above. 972 gave 9.1e-3 and ended 2.5e-3 above.
- **Moved donors beyond 1e-2.** 812 → 869 and 871 → 930 gave 2.3e-3 and 2.4e-3 of 1.2e-2. 548 → 595 gave 1.2e-3 of 1.0e-2. 604 → 653, 751 → 806, 809 → 866, 867 → 926, 868 → 927 and 924 → 985 did not move.

#### How to read round 14

- **A near layout is a donor.** The family lane's near 854s are not below the held side, and they gave 913 its 1.7e-4. A poll that reads only `take.tsv` misses them. Read the `near/` folders at every poll. This round did it with two scripts in `take-border-r14/work` on boxA: `nearscan.py` lists each near layout with its target, margin and walls, and `mknear.py` puts it into a base for `starts`. They are not in `border_sweep.py` yet.
- **The rule of five on each wall is wrong for this pair.** Corner 1 of 854 has no tilted square on the top wall. On six of the ten donors it gave 6 to 10 times more than corner 2, which has them on the top wall. The border puts a row of `floor(s) + 1` squares on top and a column of `floor(s)` beside, so the two walls are not the same.
- **On a winning corner, run the gap variants.** Variant 5 gave 6e-4 more than the even spread, on every donor. In round 13 the gap variants of 852 gave 2.2e-5.
- **Walls with at most one tilted square give nearly nothing.** 24 starts in this round, with margins down to 6.1e-5, did not move. The one exception is corner 3 of 738 → 793, which gave 7.2e-5.

#### Not run yet

- The other near layouts of the family lane: 649, 702, 755, 936 and 598, and the gap variants on 813 → 870 and 803 → 860.
- Gap variants on 911 → 972 corner 2 (variant 6 ran on one donor at the end of the round), and on 862 → 921.
- 913 → 974 on the new 913 has no tilted square on any wall, so it is closed.

### Round 15: the sweep on the round 14 file (2026-11-12)

**Result: one n certified below the round 14 file, 923, gain 4.046e-05 of score. It waits in `take-border-r15` for the main session. It is a corner window: the 923 squares nearest one corner of the readers lane's new 985, which it built one shell up from a jonathan1506 layout. The window alone was 1.22e-3 of side below the held 923, and the quench took 5.4e-6 more. No border start ended below its held side. The gap variants ran on six pairs. On four of them, a gap at the first or the last tilted square of a wall gave back more than the even spread.**

The base is the held file `gather/round14-2026-11-12a.csv` (22.1686761690) with the smallest take of each n on top. The take dirs are `take-*-r15` and the harvest pass `take-harvest-2026-11-12j`. That pass brought 22 public n at 09:08 UTC. Polls every 10 minutes from 09:12 to 10:21 UTC rebuilt the base. At 10:02 it replaced 40 n.

#### What changed in `border_sweep.py`

- **`near` reads the near layouts of every lane at each poll.** It lists every `near/*.csv` under the take dirs and skips the files it read before (md5). For each new file it writes the rows of `rank` for b1 and b2 to the largest n they reach. It writes one row per corner, with the file and what made it. `starts` builds such a row on the near layout, not on the held donor, and keeps a copy of the file beside the starts. `cert` names the lane and the file. From the file name it also names the held packing the layout came from, with that packing's source and licence. A control: round 14's 972, from its near 911, run again through the new path, gave the same score to 1e-17 and the same licence chain.
- **`rank` no longer asks for five tilted squares on each wall.** It keeps a corner with two or more on one wall. It sorts by the larger of the two counts times the distance from the board, then by the other count. `--moved OLD_DETAILS.csv` keeps the pairs whose donor or target moved since that table.
- **`starts --gaps 1,end` builds the gap variants of each corner.** Variant `4g + corner` leaves one gap in the border at the g-th tilted square of each wall. `end` is the last one, at the end of the donor's tilted band. `gaps DIR` lists the plain corners of a dir that gave back more than 1e-3, as rows for it.
- `base` now runs with no take dir.

`nearscan.py` and `mknear.py` of round 14 are no longer needed. In `take-border-r15/work`, two scripts drop a start before it runs. `dedupe.sh` drops a start whose bytes ran in rounds 10 to 15 (md5 of each start file). `samesid.py` drops a start that ran this round on a donor within 1e-6 of side, such as a public layout and the polish lane's fq of it.

#### What ran

One process on boxA and two on boxC, from 09:01 to 10:23 UTC. Other lanes kept boxA at a load of 11 to 30 on 10 cores, so its chains ran 5 to 20 times slower than in round 14. 112 chains ran in all: 99 on boxC and 13 on boxA. The table gives the side after the quench minus the held side of the target.

| pair, donor | margin before | corner (top, right tilted) | plain corner gave back | gap variant gave back | ends above held |
|---|---|---|---|---|---|
| 921 → 982, the family lane's new 921 | 6.74e-3 | 1 (0, 15) | 3.62e-3 | end (v61): 5.11e-3 | 1.63e-3 |
| | | 2 (15, 15) | 3.64e-3 | 1 (v6): 4.96e-3, end (v62): 3.64e-3 | 1.78e-3 |
| 862 → 921, round 14's near 862 | 1.26e-2 | 2 (17, 16) | 2.37e-3 (round 14) | end (v66): 4.47e-3, 1 (v6): 3.9e-4 | 8.1e-3 |
| | | 1 (0, 17) | 1.32e-3 (round 14) | end (v69): 4.9e-4 | |
| 813 → 870, round 14's near 813 | 5.89e-3 | 1 (0, 11) | 0 | end (v45): 2.49e-3 | 3.39e-3 |
| | | 2 (11, 13) | 0 | end (v54): 9.7e-4, 1 (v6): 2.6e-4 | |
| 813 → 870, three more near 813s | 5.85e-3 to 5.89e-3 | 2 | 0 to 3.11e-3 | | 2.78e-3 |
| 748 → 803, the public 748 | 9.59e-3 | 1 | 3.04e-3 | 1 (v5): 2.69e-3 | 6.54e-3 |
| 854 → 913, five more near 854s | 5.99e-3 | 1 (0, 9) | 3.10e-3 to 5.41e-3 | | 5.8e-4 |
| | | 2 (9, 0) | 8.4e-4, back on the old held 913 | | 5.1e-3 |
| 921 → 982, a near 921 of round 14 | 6.78e-3 | 2 (15, 15) | 1.44e-3 | 1 (v6): 2.95e-3 | 3.83e-3 |
| 738 → 793, the public 738 | 1.41e-3 | 2 (12, 0) | 4.8e-4 | end and 1: under 4e-5 | 9.3e-4 |

- **The plain win 985 → 923.** The poll at 10:02 found it, and the chain ran at once. The window gave 30.837106594, and the quench gave 30.837101199. A second fq quench on the certified file (as the corners lane advised) found nothing more.
- **The harvest pass j as donors.** 37 starts on the new public layouts ran (jonathan1506's fault-dp notebook and the jazivxt dataset). Three gave back more than 1e-3: 748 → 803 corner 1 and its first gap, and 694 → 747 (1.4e-3 of 1.4e-2). 22 gave back under 1e-7.
- **Near layouts.** 41 starts ran on near layouts. 20 were on 813 → 870 and 10 on 854 → 913. 6 were on 872 → 931, 3 on 862 → 921 and 2 on 921 → 982. The lanes wrote 16 new near files during the round. The two new near 872s did not move on any corner. The near layouts of 649, 702, 755, 936 and 598, which round 14 did not run, sat behind these in the queue and did not run.
- **Two near-miss windows** of new layouts ran on boxA at the end: 802 → 746 (4.6e-4) and 535 → 260 (5.5e-4). Neither moved.
- **The held donors that moved in round 14** (`w1`, 58 starts) got one chain. 755 → 810 corner 1 gave back 3.8e-5 of 3.8e-3 in 21 minutes and was cut.

#### How to read round 15

- **The band-end gap moves corners that the border does not.** On 813 → 870 corner 1 the plain border gave nothing. The gap at the band's end gave 2.5e-3. On 921 → 982 and 862 → 921 it gave 1.5e-3 and 2.1e-3 more than the plain corner. Round 14 found the same on 854 → 913 with the first gap. So the gap variants belong in the first wave of each strong corner. Do not wait for a plain give-back above 1e-3.
- **The fault-line layouts of jonathan1506 give almost nothing as border donors.** Most of their corners have at most a few tilted squares on the walls. Their corner windows are another matter: the one plain win of the round is a window of a layout built from one of them.
- **A busy box halves the round.** With the load at 30, the one boxA process ran 11 chains from 09:01 to 10:13. Next round, put the long queue on the box with the lowest load, after `uptime` on each.

#### Not run yet

- The rest of the near layouts and held donors in the queues: about 260 starts in `take-border-r15/work` (`nwA`, `nwB`, `w1`, `p-c`, `p-e`, `pn-d` to `pn-g`, `gv2`). `quench` goes on from where each chain stopped.
- Gap variants g = 2 to 10 on 813 → 870 corner 1 (`gv2`), and the gap variants of every corner of 921 → 982 on the next new 921.

### Round 16: the sweep on the round 15 file (2026-11-12)

**Result: one n certified below the round 15 file, 972, gain 2.325e-05 of score. It waits in `take-border-r16` for the main session. It is one border on corner 2 of a near 911 of the family lane, which the family lane built one shell down from the held 974. On four such near 911s, corner 2 gave back 1.23e-2 to 1.26e-2 from a margin of 1.19e-2. The best ended 7.3e-4 of side below the held 972. 921 → 982 on the modules lane's new 921 came within 7.7e-5 of the held 982, with the gap at the first tilted square of corner 2.**

The base is the held file `gather/round15-2026-11-12a.csv` (22.1672602051) with the smallest take of each n over `take-*-r16` on top. Polls every 10 minutes from 12:20 to 13:44 UTC rebuilt it. At 13:41 it replaced 31 n. No poll found a plain win.

#### What changed in `border_sweep.py`

- **`carry DETAILS.csv PREFIX SRC_DIR ...`** takes the starts of earlier dirs that have no record or a cut one. It gives each its margin on the new details table and puts it into a tier dir. Tier 1 is a margin under 7e-3, tier 2 under 1.1e-2, tier 3 the rest. Each tier is dealt over `--split` dirs, one per quench process, smallest margin first. A start keeps its manifest line, its near donor copy, and its record and packing, so its chain goes on from where it stopped. An id that two dirs built on two donors keeps the one with the smaller margin. Control: on the 11 dirs that round 15 left, `carry` gives the same 257 starts as the dirs built by hand at the start of this round. The bytes are the same on 256. The one start that differs is 868 → 927 corner 3. Two polls of round 15 built it on two donors of 868, and `carry` keeps the smaller margin where the hand copy kept the other.
- The poll (`poll.sh` in the work dir) builds the new rows of `rank` and `near` with `--gaps 0,1,end` in the first wave.

#### What ran

Two processes on boxC and one on boxA, from 12:09 to 13:41 UTC. boxA paused from 12:39 to 12:40 and from 13:25 to 13:28, because its load went over 15. boxC ran at a load of 32 to 45, so a chain on 972 or 982 took 4 to 20 minutes. 101 chains ran, and 55 of them gave back more than 1e-7. The table gives the side after the quench minus the held side of the target.

| pair, donor | margin before | corner (top, right tilted) | plain corner gave back | gap variant gave back | ends against held |
|---|---|---|---|---|---|
| 911 → 972, four near 911s of the family lane (7e-8 to 1.6e-5 above the held 911) | 1.19e-2 | 2 (18, 18) | 1.226e-2, 1.241e-2, 1.263e-2, 1.264e-2 | 1 (v6): 1.02e-3, 1.03e-3 | **-3.4e-4, -4.9e-4, -7.0e-4, -7.3e-4** |
| 921 → 982, the modules lane's new 921 | 5.04e-3 | 2 (18, 12) | 3.68e-3 | 1 (v6): 4.96e-3, end (v74): 3.68e-3, v50: 3.58e-3 | +7.7e-5 |
| | | 3 (12, 0) | 1.88e-3 | | |
| 921 → 982, the held 921 of round 15 | 5.92e-3 | 2 (15, 15) | 4.25e-3 | | +1.67e-3 |
| 921 → 982, the family lane's new 921 | 5.82e-3 | 2 (16, 15) | 2.02e-3, cut | | +3.80e-3 |
| 755 → 810, the family lane's new 755 | 3.05e-3 | 2 (10, 12) | 1.31e-3 | 1 (v6): 1.08e-3, cut | +1.74e-3 |
| 860 → 919, the family lane's new 860 | 5.39e-3 | 2 (16, 16) | 1.73e-3 | 1 (v6): 3.4e-4 | +3.66e-3 |
| 750 → 805, a held donor that moved in round 15 | 4.41e-3 | 2 | ran in round 15 | 1 (v6): 1.55e-3 | +2.87e-3 |
| 806 → 863 | 5.24e-3 | 1 | | v29: 1.07e-3 | +4.17e-3 |
| 912 → 973, a near 912 of the family lane | 6.58e-3 | 2 | 5.5e-4 | v38: 2.19e-3 | +4.39e-3 |
| 335 → 372, three near 335s of the family lane | 1.32e-3 | 1 to 3 (2 to 6 tilted) | 0 | v6, v11, v14: 6.5e-4 | +6.6e-4 |

- **The 972 take.** The near 911s certified at 12:48 (gain 1.09e-5), 12:58 (1.57e-5), 13:26 (2.24e-5) and 13:35 (2.325e-5). Each went into `take.tsv` as it certified, with one line in the handoff log. The fq quench of each certified file moved the side by 3.3e-9 at most. The polish lane took the first one and quenched it 3.1e-6 of score lower, still above the last. A fifth near 911 was cut after one round, 2.1e-3 above. `literature_check.py` on the take gives bad 0 (min gap 5.06e-11), and a copy with one square moved by 0.3 makes it exit 1.
- **The 921s.** Two lanes wrote a new 921 during the round, the family lane and the modules lane. Each opened 921 → 982 again. On the modules 921, the gap at the first tilted square of corner 2 gave 1.3e-3 more than the plain corner. Round 15 saw the same on the family 921.
- **The carried starts.** `carry` put 257 starts of round 15 into six dirs. They sat behind the new layouts of this round in the queues, and only 6 of them ran. One near 854 → 913 corner 1 gave back 5.3e-3 and stopped 6.7e-4 above.

#### How to read round 16

- **A near layout of the family lane is still the best donor.** 972 came from near 911s, as in round 14. That time it came from near 911s one shell down from the held 974 of round 13. This time it came from near 911s one shell down from the held 974 of round 15. Each time the corner with 17 or 18 tilted squares on each wall gave back more than its margin.
- **The gap variants do not help every corner.** On two donors of 911 → 972 corner 2, the gap at the first tilted square gave 1.0e-3. The plain corner gave 1.24e-2. On 921 → 982 corner 2 it gave 1.3e-3 more than the plain corner. Run the plain corner first, and the gap variants beside it only on the corners where they helped before.
- **Slow chains cost the round.** The chains on 982 took 5 to 20 minutes each, and the carried starts never reached the front of the queues.

#### Not run yet

- 251 carried starts (`o1a` to `o3b` in `take-border-r16/work`), and the gap variants 2 to 5 of 921 → 982 corner 2 on the modules 921 (`gg982`, one ran in part).
- The fifth near 911 (`pe972m`, cut after one round), and the starts of the polls from 13:06 on (`p-g` to `p-k`, `pn-i`, `pn-j`).
- 755 → 810 corners 1 and 3 and its other gap variants (`pi810`).

### Round 17: the sweep on the round 16 file (2026-11-12)

**Result: three n stay in `take-border-r17` for the next assembly, 0.0001614 of score in all. 983 gives 1.416e-4. It is one border on the family lane's new 922, with a gap at the last tilted square of a corner. 746 (1.81e-5) and 845 (1.7e-6) are corner windows of the midm lane's new 802 and 904. Two more n certified and left the take for lower layouts that other lanes built from them. 982 (2.958e-4) went to the readers lane at 19:57 UTC, and 919 (1.907e-4) to the family lane at 19:00 UTC.**

The base is the held file `gather/round16-2026-11-12a.csv` (22.1664224426) with the smallest take of each n over `take-*-r17` on top. At 18:50 UTC it replaced 85 n. The round ran in four parts. boxA rebooted at 16:15 UTC, and the agent that ran the round stopped at 17:52 and at 19:05 UTC. Each part read the take dir and the queue dirs of the part before it, so no chain ran twice.

#### What ran

Two quench processes on boxC for the whole round, and one on boxE from 17:45 UTC. Polls `g` to `k` rebuilt the base and the starts between 17:43 and 18:50 UTC. A loop (`collect.sh`) brought the queue dirs back and certified them every 10 minutes. boxC ran at a load of 12 to 40, and boxE at 19 to 50. 108 chains wrote a record, and 78 of them gave back more than 1e-7. The table gives the side after the quench minus the side of the target in the base.

| pair, donor | margin before | best corner and gap | gave back | ends against the base |
|---|---|---|---|---|
| 921 → 982, the family lane's new 921 (one shell up from the corners lane's 860) | 5.29e-3 | corner 1, gap at the last tilted square (v77) | 1.185e-2 | **-6.1e-3** |
| | | corner 2, gap at the last tilted square (v54) | 5.20e-3 | +9e-5 |
| | | corner 2, plain (v2) | 4.75e-3 | +5.4e-4 |
| 860 → 919, the corners lane's 860, then the family lane's 860 (two shells down from the corners 984) | 3.84e-3 to 3.98e-3 | corner 3, gap at the last tilted square (v71) | 9.62e-3 | **-5.8e-3** |
| | | corner 3, gap 1 (v7) | 8.64e-3 | |
| | | corner 2, plain (v2) and its last gap (v54) | 7.50e-3, 7.70e-3 | |
| 802 → 746, the midm lane's new 802 | -1.21e-4 (plain win) | the corner window | 3.73e-4 | **-4.9e-4** |
| 904 → 845, the midm lane's new 904 | -2.08e-5 (plain win) | the corner window | 0 | **-2.1e-5** |
| 851 → 910, the twoshort lane's 851 as it moved | 5.22e-3, then 3.38e-3 | corner 2, gaps 4 and 5 (v18, v22) | 3.59e-3 | +3.9e-4 |
| 756 → 811 | 5.58e-3 | corner 2, plain | 5.07e-3 | +5.2e-4 |
| 861 → 920, the stair-c lane's 861 | 8.76e-3 | corner 2, plain | 5.55e-3 | +3.2e-3 |
| 912 → 973, the family lane's 912 | 5.97e-3 to 6.98e-3 | corner 2, plain | 3.97e-3 | +3.0e-3 |
| 922 → 983, the family lane's new 922 (19:36 UTC) | 6.88e-3 | corner 3, gap at the last tilted square (v79) | 9.62e-3 | **-2.7e-3** |
| 921 → 982, the readers lane's new 921 | 5.55e-3 | corner 1, plain and gap 1 | 7.1e-4, 2.74e-3 | +2.8e-3 |
| 921 → 982, a near 921 of another lane | 5.72e-3 | corner 2, gap at the last tilted square | 5.11e-3 | +6e-4 |
| 933 → 994 | 5.09e-3 | corner 1, gap at the last tilted square | 2.29e-3 | +2.8e-3 |

- **The takes.** 919 certified four times, at 1.161e-4, 1.226e-4, 1.583e-4 and 1.907e-4 of score, as better donors and gaps came in. It left the take at 19:00 UTC for the family lane's 919. At 19:03 UTC the certify loop put it back, because `cert` compared a result only with its base and with this lane's own take. It left again at 19:09 UTC. `cert` now also skips an n that a live take dir holds lower. 982 certified once from the first chain of corner 1's last gap. Each went into `take.tsv` as it certified, with one line in the handoff log. 904 certified at 15:29 UTC as one border on the midm lane's 845. It was withdrawn at 15:42 UTC, when the midm lane's own 904 went lower.
- **The twoshort layouts as donors.** One border on the twoshort lane's 851, 852 and 910 to 914 gave back 1.4e-3 to 3.6e-3. The margins were 1.6e-2 to 2.1e-2 (971, 972, 974 and 975), so none came near. Those donors are already tight, so the border has little slack to take back.

#### How to read round 17

- **The gap at the last tilted square is now the best variant.** In round 16 the gap variants helped on two corners only. This round all three large takes (982, 919 and 983) came from the gap at the last tilted square of a wall. On 982 it gave 2.5 times what the plain corner gave. Build the plain corner and its last gap side by side on every corner with 9 or more tilted squares on a wall.
- **The donors come from the corner and family lanes, and go back to them.** 919, 982 and 983 are each one border on a packing of theirs. The two donors, 860 and 921, are one shell apart. When those lanes move 860 or 921 again, run the border on them at once.
- **A plain win comes after every midm or polish take.** 746 and 845 were plain wins on the base, so `starts --max 0` on `enum` should run on every poll.

#### Not run yet

- One border on the near donors of 755 → 810 (2.38e-3) and 851 → 910 (2.49e-3), the smallest margins of the round.
- 859 → 918 (7.04e-3) and 920 → 981 (8.83e-3), both on the family lane's new donors.

### Round 19: the sweep on the round 17 file and the round 19 takes (2026-11-12)

**Result: one n stays in `take-border-r19`: 332, 5.278e-5 of score against the round 17 file. No other take holds 332 at 22:30 UTC. It is a plain border on the rigidsoft lane's new 297, and the quench gave nothing more. Two more n certified and left the take for lower layouts of other lanes. 367 (4.08e-5, a plain border on the k123 lane's new 330) went to the midm lane, which holds it 2.06e-4 lower. 980 (2.09e-5, one border on the readers lane's new 919) went to the polish lane, which polished it 1.3e-9 lower.**

The base is `gather/round17-2026-11-12a.csv` (22.1635211736) with the smallest take of each n over the frozen `take-*-r17` dirs and the live `take-*-r19` dirs on top. A poll rebuilt it every 5 to 10 minutes from 20:16 to 22:12 UTC. One `fq` queue ran on boxC with 2 processes. From 21:47 UTC one of them ran kicks on the two best chain ends. `cert` ran every 10 minutes on boxA.

#### What ran

The table gives the side the quench gave back, against the margin of the start (the built side minus the lowest side of the target).

| pair, donor | margin | corner and gap | gave back |
|---|---|---|---|
| 297 → 332, the rigidsoft lane's 297 | -4.6e-8, then -9.6e-4 | plain | 0, **take** |
| 330 → 367, the k123 lane's 330 | -7.8e-4 | plain | 0, certified, then the midm lane held 367 lower |
| 328 → 365, the rigidsoft lane's 328 | -2.8e-4 | plain | 0. The rigidsoft and forensics lanes held 365 lower 5 minutes later |
| 919 → 980, the readers lane's 919 | 6.01e-3 | corner 1, gap variant 5 | **6.67e-3**, certified, then polished lower by the polish lane |
| | | corner 1 plain (v1), corner 2 plain (v2) | 4.46e-3, 4.38e-3 |
| 860 → 919, the polish lane's 860 | 1.027e-2 | corner 3, gap at the last tilted square (v75) and gaps 16, 17 (v67, v71) | 9.72e-3, all three to the same side 30.7905726, short by 5.5e-4 |
| | | corner 2, gap at the last tilted square (v74) | 7.50e-3 |
| 860 → 919, two near 860 of the stair-c lane | 1.03e-2, 1.04e-2 | corner 1, last gap (v73) | 5.76e-3, 5.59e-3 |
| 921 → 982, two near 921 of the stair-c lane | 1.19e-2 | corner 1, last gap (v73, v77) | 6.93e-3, 6.89e-3 |
| | | corner 2, last gaps (v62, v74, v78) | 3.9e-3 to 4.5e-3 |
| 920 → 981, the readers lane's 920 | 4.42e-3 | corner 3, last gap (v67) and gap 1 (v7) | 2.91e-3, 2.92e-3 |
| 859 → 918, the family lane's r17 859 | 4.16e-3 | corner 2 last gap (v10), corner 3 last gap (v67), plain (v2) | 1.99e-3, 2.74e-3, 1.90e-3 |
| 755 → 810, the midm lane's 755 | 2.32e-3 | corner 2, last gap (v26) | 4.3e-4 |
| 851 → 910, a near 851 of the family lane | 7.61e-3 | corners 1 and 3, last gaps (v16, v19) | 0 |
| 755 → 810, two near 755 of the family lane | 2.37e-3, 2.38e-3 | corner 2, last gap (v50) | 3.5e-5 |

- **Kicks on the best chain ends.** Kicks of 1e-3 on the end of 919 v75 gave 0 in two seeds. On the end of 980 v5 they gave 7e-7 of side. A kicked quench comes back to the same layout. It does not close a gap of 5e-4.
- **The last gap is still the best variant. It gives less on these donors.** In round 17 it gave back 9.6e-3 to 1.19e-2 on 921, 860 and 922. This round it gave 9.7e-3 on the polish lane's 860. That layout is close to the family 860 of round 17. It gave 5.6e-3 to 6.9e-3 on the stair-c near layouts of 860 and 921, which have other corners. The donor's corner sets the give-back more than the variant does.

#### How to read round 19

- **Plain borders pay at once on the small n that other lanes move.** 332 and 367 came within 10 minutes of the rigidsoft 297 and k123 330. The 365 from the rigidsoft 328 was too late by 5 minutes. A plain border needs no quench, so the poll should certify it on the spot rather than queue it behind a chain.
- **The large border pairs are closed on today's donors.** Every pair with a margin over 4e-3 ended short, the closest by 5.5e-4 (919 on the polish 860). The near layouts of 755 and 851 gave back 3.5e-5 and 0. They are tight already, so the border has no slack to take back.
- **A border take goes to the next lane within the hour.** 367 and 980 both left the take for a lower layout of another lane. The gain lands either way.

#### Not run yet

- Certify a plain border in the poll itself, with no queue. The 365 from the rigidsoft 328 lost by 5 minutes.
- Nothing more on 919 from the polish 860: three gap variants of corner 3 ended at the same side. A lower 919 needs a new donor 860.

### Round 20: the sweep on the round 18 file and the round 20 takes (2026-11-12 to 13)

**Result: two n stay in `take-border-r20`, 1.106e-4 of score against the round 18 file. 851 gains 6.130e-5 with one border on the family lane's new 794. 929 gains 4.929e-5 with one border on the classfill lane's new 870. No other take holds either n at 00:56 UTC. They are the first large border pairs to pay since round 17. A second n, 868 (3.07e-5, one border on the family lane's new 811), certified and then left the take, because the readers lane holds 868 4.03e-5 lower.**

The base is `gather/round18-2026-11-12a.csv` (22.1604820601) with the smallest take of each n over the frozen `take-*-r19` dirs and the live `take-*-r20` dirs on top. A poll rebuilt it every 5 minutes from 22:39 to 00:50 UTC. One `fq` queue ran on boxC with 2 processes. `cert` ran every 10 minutes on boxA. A harness restart at about 22:48 UTC stopped the poll and the cert loop on boxA for 4 minutes. The queue on boxC ran on.

#### What ran

The table gives the side the quench gave back, against the margin of the start (the built side minus the lowest side of the target).

| pair, donor | margin | corner and gap | gave back |
|---|---|---|---|
| 870 → 929, the classfill lane's 870 (f 0.917) | 8.60e-3 | corner 2 (14 and 14 tilted), plain (v2) | **1.010e-2, take** |
| | | corner 2, last gap (v58) | 1.003e-2, certified first |
| | | corner 1 last gap (v57), corner 3 last gap (v59), plain (v1, v3) | 3.8e-3, 7.9e-5, 0, 0 |
| 811 → 868, the family lane's 811 (f 0.910) | 1.119e-2 | corner 2, last gap (v50) | **1.209e-2**, certified, then the readers lane held 868 lower |
| 868 → 927, the readers lane's 868 | 9.53e-3 | corner 2, plain (v2) | 3.74e-3 |
| 809 → 866 | 1.06e-2 | corner 2, plain (v2) | 3.66e-3 |
| 929 → 990, our new 929 | 1.20e-2 | corner 0, last gap (v52) | 3.7e-4 |
| 870 → 929, a near 870 of the corners lane | 1.01e-2 | corner 2, plain (v2) | 9.67e-3, 4.7e-4 of side above our 929 |
| 870 → 929, four near 870 of the stair-c lane | 1.06e-2 to 1.19e-2 | corner 2, plain (v2) | 1.062e-2 and 1.033e-2, which is 4.0e-5 and 3.6e-4 of side above our 929, and 0 on a third |
| 931 → 992, a near 931 of the stair-c lane (36 tilted) | 8.15e-3 | plain (v2), last gap (v78) | 5.61e-3, 4.41e-3 |
| 794 → 851, the family lane's 794 (f 0.684) | 4.99e-3 | gap variant 7 | **6.78e-3, take** (certified at 00:55 UTC) |
| | | last gaps (v59, v54), v53 and v58 cut | 4.47e-3, 2.43e-3, under 1e-4 |
| 632 → 683 and 632 → 736 | 1.89e-3 | gap variant 15 | 1.20e-3 |
| 689 → 742 | 3.68e-3 | gap variant 4 | 6.7e-4 |
| 535 → 582, 452 → 495, 739 → 794, 848 → 907, 684 → 792 | 8.8e-5 to 1.6e-3 | plain and gap variants | 0 |

- **The donor's corner sets the give-back.** Two of the three pairs that paid had a donor with f over 0.9 (side = m + f). Each had a corner with 14 or more tilted squares on both walls. The third, 851, has f 0.684 and paid on gap variant 7. All three donors are new layouts of another lane. The classfill 870 is a far-zone sweep on the stair-c staircase corner. The family 811 is a new shell. The plain variant and the last gap gave nearly the same side on the 870 (1.010e-2 and 1.003e-2).
- **The small pairs gave 0.** Every pair with a margin under 2e-3 gave back 0 or about half its margin. No plain win showed up in 27 polls.
- **A killed chain loses little.** `quench` goes on from the last packing of a chain when it runs again on the same DIR. So a requeue with `rq.sh` costs only the step in flight.

#### How to read round 20

- **Border every new high-f corner at once.** 929 came 20 minutes after the classfill 870, and 868 came 30 minutes after the family 811. The other lanes moved 868 lower again within the hour, so the gain lands either way.
- **The near layouts of other lanes give less than their takes.** The corners near 870 ended 4.7e-4 of side above the classfill 870's border. The stair-c near 931 gave back 70% of its margin.

#### Not run yet

- Kicks on the end of the stair-c near 870 border (sn21), which ended 4.0e-5 of side above our 929. In round 19 kicks gave 0 to 7e-7, so this is a long shot.
- Some high-f corners with 9 or more tilted squares on both walls have not run. They are 812 → 869 (f 0.923), 702 → 755 (0.920), 701 → 754 (0.912), 649 → 700 and 648 → 699 (17 starts in `take-border-r20/work/p-hf`).

### Round 21: the sweep on the round 19 file and the round 21 takes (2026-11-13)

**Result: one n stays in `take-border-r21`: 918, 4.842e-5 of score against the round 19 file. It is one border on the harvest lane's 859 of round 20. The polish lane holds 918 8.7e-9 higher, a polish of our file. Two more n certified and then went to the follow lanes. 929 (1.942e-4, one border on the stair-c lane's new 870) went to the readers lane and then the invent lane. The invent lane holds it 5.8e-5 lower at 12:12 UTC. 992 (1.921e-5, one border on a near 931 of the stair-c lane) went to the readers, harvest and polish lanes. The polish lane holds it 2.0e-5 lower. Their files are in `take-border-r21/near`.**

The base is `gather/round19-2026-11-12a.csv` with the smallest take of each n over the frozen `take-*-r20` dirs and the live `take-*-r21` dirs on top. A poll rebuilt it every 5 minutes. One `fq` queue ran on boxC with 2 processes, and `cert` ran every 10 minutes on boxA. The lane ran from 01:03 to 01:23 UTC and from 09:50 to 12:10 UTC. A usage limit stopped it at 01:23 UTC. The queue on boxC ran on to its deadline of 03:25 UTC, and boxA rebooted at 05:36 UTC.

#### What ran

The table gives the side the quench gave back, against the margin of the start (the built side minus the lowest side of the target).

| pair, donor | margin | corner and gap | gave back |
|---|---|---|---|
| 870 → 929, the stair-c lane's 870 (f 0.914) | 7.55e-3 | corner 2 (15 and 15 tilted), plain (v2) | **1.196e-2**, certified, then the readers lane held 929 lower |
| | | the same corner on a family near 870 | 9.62e-3 |
| 931 → 992, the family lane's 931 (f 0.921) | 5.21e-3 | corner 2 (19 and 15 tilted), plain (v2) | **5.81e-3**, certified first |
| 931 → 992, a stair-c near 931 (qa) | 5.73e-3 | corner 2, plain (v2) | **6.34e-3**, certified, then the harvest lane held 992 lower |
| 931 → 992, seven other 931 of the readers, stair-c, family and classfill lanes, and a modules near of round 20 | 5.17e-3 to 6.24e-3 | corner 2, plain (v2) | 4.8e-3 to 6.8e-3, ending between 31.91553 and 31.91725 |
| 859 → 918, the harvest lane's 859 (f 0.787) | 2.87e-3 | gap variant 67 | **4.34e-3, take** (attempt 1) |
| 794 → 851, four near 794 of the family and twoshort lanes (f 0.684) | 6.8e-3 to 7.5e-3 | gap variant 7 | 5.0e-3 to 6.2e-3 |
| 868 → 927, three 868 of the readers and midm lanes | 4.3e-3 to 4.8e-3 | plain (v2), last gap | 5.4e-4 to 6.3e-4 |
| 929 → 990, the readers lane's 929 | 6.5e-3 | plain (v2), last gap | 0 to 1e-5 |
| 921 → 982, a stair-c near 921 | 1.19e-2 | plain (v2) | 4.3e-3 |
| 702 → 755, 649 → 700, 930 → 991, 701 → 754, 933 → 994 (the high-f starts of round 20) | 1.2e-2 to 1.4e-2 | plain and last gap | 22% to 56% of the margin |

- **The same three pairs pay again.** 870 → 929, 931 → 992 and 859 → 918 gave back more than their margin. Each donor is a new layout of another lane, and two of them have f over 0.9 with 15 or more tilted squares on both walls. The high-f pairs with a margin over 1.2e-2 gave back half of it at most.
- **The side of the donor does not predict the end.** Eight of the 931 donors built 992 starts within 5.7e-4 of side of each other. Their chains ended between 31.91538 and 31.91648. The lowest end came from the start with the highest built side (the stair-c near qa).
- **The follow lanes take a border result within 30 minutes.** That was the lesson of round 20, and it held. The readers lane went under our 929 16 minutes after it certified. It went under our 992 in 23 minutes, and the harvest lane went lower again 9 minutes later. The merge counts their rows, so the gain lands either way.

#### Two tool traps, fixed in the lane's work dir

- `rq.sh` merged a new start dir into the queue by id. When an id had run before on another donor, it kept the old manifest row and copied the new start file. So `cert` named the wrong donor. `fixman.py` now matches each manifest row to its start file by the built side. `retag.py` gives a new start of an old id its own tag, so it runs instead of being skipped.
- `mknear.sh` built a near layout's starts on a base with that n replaced. The manifest then named the base n as the donor, not the near file. `fixnear.py` writes the near file into the row, and `cert` names it.

#### Not run yet

- Nothing from this round's list has a measured reason to run again. The three pairs that paid have run on every new donor.
- A new layout of 870, 931 or 859 from another lane gets one border at once, plain (v2) on corner 2 and gap variant 67 on 859.

### To repeat

```
border_sweep.py base   HELD.csv DETAILS.csv BASE.csv BASE_DETAILS.csv TAKE_DIR...
border_sweep.py enum   BASE.csv BASE_DETAILS.csv PAIRS.tsv --max 3e-2
border_sweep.py rank   BASE.csv BASE_DETAILS.csv PAIRS.tsv results/per-puzzle-lb-2026-11-09.json RANKED.tsv --max 1.5e-2 --dist-min -1 --kinds b1,b2 --moved OLD_DETAILS.csv
border_sweep.py near   BASE_DETAILS.csv results/per-puzzle-lb-2026-11-09.json NEAR.tsv TAKE_DIR... --done SEEN.txt --max 1.5e-2
border_sweep.py starts BASE.csv BASE_DETAILS.csv RANKED.tsv DIR --kinds b1,b2 --max 3e-2      (and NEAR.tsv into its own DIR)
border_sweep.py gaps   DIR GAPS.tsv --min 1e-3
border_sweep.py starts BASE.csv BASE_DETAILS.csv GAPS.tsv DIR2 --max 3e-2 --gaps 1,end
border_sweep.py quench DIR --jobs 4 --until EPOCH
border_sweep.py carry  NEW_DETAILS.csv PREFIX OLD_DIR...      (the starts an earlier round left, into tier dirs)
border_sweep.py cert   BASE.csv BASE_DETAILS.csv DIR TAKE_DIR --takes TAKE_DIR... --submitted DETAILS.csv --sources results/*-best-*.tsv
border_sweep.py report TAKE_DIR --board results/per-puzzle-lb-2026-11-09.json
```

`rank` writes one line per pair and corner, with the edge count of each of the two walls (`top`, `right`), and `starts` builds exactly those corners. Since round 15 it ranks each wall on its own, and `--both-min 5` (the rule of rounds 11 to 14) is off by default. `near` gives the same rows for the near layouts of every lane, and `--done` makes each poll read only the new files. `quench` needs only the standard library and the `fq` binary, so a box with nothing else can run it: copy `border_sweep.py`, `fq` and DIR there, and copy DIR back for `cert`. A chain writes its record after every round. A chain that was killed, or cut by `--until`, goes on from its last packing when `quench` runs again on the same DIR. `DIR/order.txt`, when it exists, lists the starts in the order to run them. After each harvest, `starts --max -3e-9 --min-abs 3e-9` on the pairs of `enum` builds the plain wins first.

## Files

| file | what it does |
|---|---|
| `literature_take.py` | Reads a published packing (register pose YAML, de Winter or Evan Daniel certificate, Ostashev `sqpk`, Casson layout, or one n of a submission file), passes it through `floatsafe` and keeps it when it certifies below the held score. `literature_take.py HELD_DETAILS.csv OUT_DIR SPEC.tsv`. |
| `literature_scan.py` | Walks cloned repos and lists every certificate, layout or submission n whose side beats the held side, as a SPEC for `literature_take.py`. |
| `literature_border.py` | Checks deletion and the border step on the held file plus any take dirs, and builds every n the border step improves. |
| `literature_window.py` | `scan`: the sub-window scan (a negative `--tol` lists near misses). `take`: builds and certifies the hits. |
| `literature_rect.py` | `scan` and `take` for a rectangle window plus columns and rows of uprights. |
| `literature_targets.py` | Adds `outside_L`, `outside_src`, `struct_L` and `new_L` to the table `tools/targets.py` writes. |
| `literature_check.py` | A second per-n check of a take dir with the gate's parts. Exit 1 on any failure. |
| `border_sweep.py` | The border step and the corner window as a sweep, with the `fq` quench (section 5): `base`, `enum`, `rank`, `near`, `starts`, `gaps`, `quench`, `cert`, `report`. |
| [`tools/targets-2026-11-11.tsv`](../tools/targets-2026-11-11.tsv) | Per n: our side, the board's side of 2026-11-09, the gap, the squares short, the best outside side and its source, the structural bound, and this round's side. |

On boxA, under `<scratch>/bounties-squares/take-border-r10`: the per-n files and `take.tsv` of section 5, and under `work/` the pair lists, one dir per wave with its starts, chain records and `manifest.tsv`, and `sweep.tsv` with one line per run. `take-border-r11` has the same layout for round 11. Its `work/` also has the ranked lists (`rank-*.tsv`), the picked starts (`pick.tsv`) and the scripts that made the tables of this page (`table.py`, `split.py`, `both.py`, `final.py`).

On boxA, under `<scratch>/bounties-squares/take-literature-r7`: the five per-n files and `take.tsv` (the layout `engine_assemble.py` reads), `spec.tsv`, `src/` (Özden's four pose files) and `work/` (scan outputs, the near-miss lists and a check file `cand-literature-r7.csv`, SHA-256 `1c7fa2ed…`, the held file with the five n replaced). The clones under `ext/` were deleted at the end; the commits are in the table above.

To repeat after a harvest: `literature_border.py HELD.csv DETAILS.csv OUT_DIR`, then `literature_window.py scan`, then clone the register and run `literature_targets.py` for the outside column.

## Summary

- **Five n, 0.0004096343 of score, certified and not yet submitted:** 156, 180, 268 and 269 from Doğa Özden's packings of 2026-11-10 and 2026-11-11 (CC BY 4.0, credit him), and 495 from today's 452 plus one row and one column.
- **The outside record is now read in full.** 721 n have a published side outside Kaggle. Only those four beat us. The register moves every day, and the people who feed it are not all on Kaggle, so it belongs in the daily harvest.
- **Structure gives nothing more today.** Deletion, the border step, every sub-window and the rectangle-plus-strips step are all closed on our file, with controls that went red. A quench of the 35 closest sub-windows ended below our side on none.
- **The gap:** 42% of it is in n = 785 to 1000, and inside every shell it sits at `k = n − m²` up to m. Nothing is left above `m² + m + 8`.
- **Next:** add the register to `harvest_delta.py`'s sources, and run `literature_border.py` after each merge.
- **Round 10, the border sweep (section 5):** five n, 0.0007376373 of score, certified and not yet submitted: 542, 799, 811, 971 and 986. Each is one border on a held packing and the `fq` quench. 971 alone gives 0.0005. The step pays when the border goes on a wall where the donor's tilted band ends. Corner windows and borders on grids gave nothing.
- **Round 11, the border sweep on the round 10 file (section 5):** four n, 0.0002487774 of score, certified and not yet submitted: 931, 972, 986 and 994. Three of the four donors are packings that round 10 made. A corner pays when it has five or more tilted squares on each of its two walls and a margin under 6e-3. The distance of the target from the board says how far a give-back can go, not how often it comes.
- **Next for the sweep:** after every harvest or take, `base`, `enum` and `rank --both-min 5 --max 1e-2`, and one chain on every corner whose donor or target moved: about 40 corners on today's base. Then the 47 picked starts that did not run.

### Round 22: fresh donors and donor records (2026-11-13)

The collector certified 4 distinct n during the round. The final take holds 4 n. Its gain is 0.001240109695 against round 20 and 0.001020603441 over the frozen round 21 and other round 22 takes.

Two quench slots ran on boxC. The collector on boxA read new takes and near files throughout the round. It exported 26 near files. Each published result passed floatsafe at 2.2e-11, then fq on its certified file on boxC, then floatsafe again.

The queue measured 102 starts on 17 donor pairs. Another 228 starts had no record at the deadline. Fresh 870, 931 and 859 donors went first, following the three pairs that paid in round 21. Long chains delayed fresh donors. The scheduler then yielded after each saved round, with unrun starts and final certified-file quenches first.

#### Tool changes and controls

Held donor ids now contain a hash of the donor coordinates. A new version of the same n gets its own start. The manifest stores the start digest and the retained near-donor copy. Certification refuses a manifest whose start changed. Near-donor records name the actual near file. They also preserve source and licence fields from a JSON sidecar when one exists.

The reused-id control printed 1 start before the fix and 2 after it. Each manifest matched its start. The near source and retained copy passed. A changed start was refused by its SHA-256. The round 21 near-931 control rebuilt the 992 start byte for byte. A source-sidecar control failed before the change and passed after it, preserving both ancestry and licence.

The two-default positive control passed at side 30.902488813594. One slot then used two defaults per round. The other kept the full chain.

A job reader stopped on a partial JSON copy. The repaired reader skipped the incomplete copy and accepted the completed object in its control. Both slots resumed from saved records.

The final local drain recovered completed quench proofs for 485 and 530. Those runs finished before the box deadline. Late raw windows without a completed quench stayed out of the take.

#### Measurements

Side columns use raw fq headers before floatsafe. Only certified rows in the results table count as gains.

| donor | target | give-back of best end | raw end minus current bar | starts |
|---|---|---|---|---|
| 485 | 530 | 0.00681467 | -1.62016e-08 | 8 |
| 917 | 978 | 0.000141551 | -1.53755e-09 | 4 |
| 530 | 577 | 0.00701664 | -1.17567e-09 | 4 |
| 442 | 485 | 0.00695908 | -1.07611e-09 | 8 |
| 494 | 539 | -9.99982e-11 | 9.99982e-11 | 13 |
| 538 | 585 | 3.55954e-06 | 1.82253e-05 | 4 |
| 297 | 332 | -9.99982e-11 | 5.93117e-05 | 3 |
| 870 | 929 | 0.0135941 | 0.000167198 | 18 |
| 931 | 992 | 0.00558951 | 0.000780648 | 16 |
| 693 | 746 | -9.99982e-11 | 0.00176256 | 1 |
| 855 | 914 | 0.00185008 | 0.00326943 | 1 |
| 912 | 973 | 0.00147155 | 0.00333521 | 6 |
| 801 | 858 | 0.00165199 | 0.00337355 | 1 |
| 750 | 805 | -9.99982e-11 | 0.0048446 | 5 |
| 796 | 853 | 0.000641679 | 0.00576496 | 5 |
| 911 | 972 | 2.8936e-05 | 0.00631359 | 4 |
| 859 | 918 | 0.00425359 | 0.00663182 | 1 |

Certified rows and their source chains are in [the results table](../results/border-r22-2026-11-13.tsv). The queue measurements are in `take-border-r22/work/measure.tsv`. Retained donor copies sit beside the starts.

The workers stopped at the deadline. Their files were copied back and checked by SHA-256 before the boxC scratch was removed.

### Round 23: fresh corner windows (2026-11-13)

The final take holds 3 n. The gain is 0.001000265252 against round 21 and 0.000579236728 over the frozen round 22 and other live round 23 takes. Sources and licences are in [the results table](../results/border-r23-2026-11-13.tsv).

Two quench slots ran on boxC. The collector measured 177 border starts on 28 donor pairs. It read 128 completed certified-input quench jobs from 172 staged jobs and exported 179 near files. Search stopped before the common quench deadline of 18:30 UTC.

The pending round 22 windows of 401 and 442 completed their required quenches first. Their recipes rebuilt byte for byte. Fresh corner windows then gave new donors to the follow lanes. The collector checked plain one-border and two-border closure at every reachable target. It read new takes, nested near folders and the handoff log throughout the round. Completed round 22 starts were skipped. Unrun starts stayed eligible. Planning bars included the lane's own best rows.

The two-default control reached side 30.902488813593994. One worker used those defaults. The second kept the full chain. The two-border positive control built 577 from 485 at side 24.526261715649774. Its deliberately worsened bar was 24.53626171558978. A duplicate-square control failed the metric and floatsafe. Every final row passed the independent pandas metric and clearance check. Its certified quench input and published result also passed byte comparisons.

Near records can store ancestry inside a manifest. The metadata reader now recovers that donor source and licence when explicit fields are absent. The control lost both fields before the fix and kept them after it. Explicit fields still take precedence. A partial JSON record returns no metadata. The reader also accepts `.csv.json` sidecars and preserves composition ancestry under `parts`. Its control failed before the fix and passed after it. Both donor paths and licences survived. The retained 847 donor matched the live near file byte for byte. Its recorded end side agreed within 2.1e-13. Those checks support the restored source of 735.

[Raw near export](../tools/border/export_raw_near.py) gives the follow lanes float-safe endpoints before optional proof jobs finish. These files name their proof status and stay outside the take. The first run exported seven files. A later run exported two improved endpoints. An unchanged repeat exported none. The raw feed accepts side gaps up to 0.015. The round 22 layer reader won from a donor 0.01477 above its bar. A wider pass exported 23 previously filtered endpoints at gaps from 0.003092831 to 0.013545220. [Progress priority](../tools/border/prioritize_progress.py) advances promising saved chains without changing inputs or quench flags. Two fresh 931-to-992 chains closed 89.25% and 87.00% of their margins on the first round.

Live near files can vanish while a poll sorts them. The collector now captures each available mtime first and skips missing files. Its positive scan returned 2216 donor entries.

#### Border measurements

Side columns use raw fq headers before floatsafe. Only the certified rows in the results table count as gains.

| donor | target | kind | starts | best give-back | raw end minus current bar |
|---|---|---|---|---|---|
| 442 | 485 | b1 | 10 | 2.140527e-08 | -0.0004725064 |
| 485 | 577 | b2 | 24 | 2.87272e-08 | -1.176105e-09 |
| 530 | 577 | b1 | 11 | 2.866633e-07 | -1.175906e-09 |
| 442 | 530 | b2 | 9 | 3.295814e-07 | -1.125915e-09 |
| 485 | 530 | b1 | 21 | 1.173639e-07 | -1.065303e-09 |
| 736 | 791 | b1 | 1 | 0 | 0.0002918398 |
| 931 | 992 | b1 | 9 | 0.005814157 | 0.0006331218 |
| 917 | 978 | b1 | 1 | 0 | 0.001666691 |
| 870 | 929 | b1 | 10 | 0.01208684 | 0.001756864 |
| 794 | 851 | b1 | 2 | 0.005626371 | 0.001859417 |
| 860 | 919 | b1 | 1 | 0.007177087 | 0.003092831 |
| 937 | 1000 | b1 | 1 | 0.0003219247 | 0.004512035 |
| 852 | 911 | b1 | 12 | 0.0008311032 | 0.00547022 |
| 911 | 972 | b1 | 13 | 0.0008620519 | 0.005541474 |
| 921 | 982 | b1 | 6 | 0.005315169 | 0.006545268 |
| 401 | 442 | b1 | 2 | 0 | 0.007250275 |
| 927 | 988 | b1 | 5 | 0.002071239 | 0.0077203 |
| 912 | 973 | b1 | 1 | 0 | 0.007740306 |
| 646 | 697 | b1 | 1 | 3.748681e-09 | 0.008296061 |
| 379 | 418 | b1 | 6 | 3.71292e-05 | 0.009193031 |
| 926 | 987 | b1 | 4 | 5.279623e-05 | 0.009228759 |
| 588 | 637 | b1 | 1 | 0.001445201 | 0.00989997 |
| 908 | 969 | b1 | 1 | 0.0004362302 | 0.01019276 |
| 749 | 804 | b1 | 1 | 0 | 0.01061603 |
| 648 | 699 | b1 | 16 | 2.440486e-07 | 0.01063975 |
| 791 | 848 | b1 | 2 | 5.781533e-09 | 0.01100553 |
| 550 | 597 | b1 | 3 | 0 | 0.01271851 |
| 867 | 926 | b1 | 3 | 0 | 0.01289143 |

The full queue measurements are in `take-border-r23/work/measure.tsv`. All owned workers stopped. The boxC archive passed its SHA-256 comparison before the scratch was removed.

### Round 24: fresh closure and shell returns (2026-11-13)

The final take holds 2 n. Its gain against the round 23 candidate is 0.000000000001. Its gain beyond other live round 24 takes in the same source group is 0.000557781368. Against the round 23b file, it gains 0.000557781368. Sources and licences are in [the results table](../results/border-r24-2026-11-13.tsv).

Two quench slots ran on boxC until 22:15 UTC. The collector measured 201 starts on 84 donor pairs. It read 37 completed certified-file quench jobs and exported 138 near layouts. Another 734 starts have no record. Their exact inputs remain in `take-border-r24/work/unstarted.tsv`.

Fresh round 24 files took priority over the frozen queue. The named near files of 992, 929 and 851 each received a one-shell cut and a restored border. Each set has four cuts and four border orientations. The raw near feed ran after each queue sync from the first saved result. Its side limit stayed at 0.015.

The first two-default control used a different saved input and missed its threshold at side 30.907306623320885. The exact archived input then passed at 30.902488813593994. One slot used those defaults. The other kept the default and deep calls. A two-border control certified 485 to 577 at side 24.525789210324547 against a deliberately raised bar. A duplicate-square control failed. The ancestry control rejected a poisoned parent from the excluded harvest 745.

The main handoff held 20 candidate rows for Samanyu seed ancestry. Recorded public and original roots can replace those rows against round 22. Samanyu descendants keep the candidate-a bar and name their seed n. Unresolved seed ancestry cannot enter the take. The lane imports the soft and forensics source policies. The table's old score follows the row's eligibility reference.

A provisional 228 matched candidate-a numerically. Its full parent tree reached Samanyu seed 365 through 735, so it left the take. The local donor labels had missed that root. The new control binds a retained descriptor to a byte-identical donor CSV. It refuses a descriptor whose recorded end differs by 0.1.

At 21:34 UTC a 735 window of the new CC0-derived 847 passed its numerical and source checks. Its input tree ends in samanyu1808/sis-final-packings at n=123 and n=365. It matches candidate-a and recovers 0.000291795863 against round 23b.

The source check follows versioned reader records and source-override sidecars. A clean new 918 passed. The excluded harvest 745 and old forensics 980 failed. The geometry audit found no equivalent starts at 1e-8 precision and no completed round 23 repeats.

The fresh border cap rose from 0.012 to 0.02 after a reader 921 was skipped at margin 0.012768. It has 17 and 16 tilted wall contacts. Queue priority follows earlier measured yields. Its control puts 931 before 911 and 873. A saved chain within 0.001 of the bar gets priority after closing 75% of its margin.

Three gap variants on the first promising 634-to-685 donor passed floatsafe at side 26.6884042288564. They move the free gap to the first or last tilted wall square. Their measurements are included below.

Every retained result passed floatsafe and the independent metric and clearance checks. Its certified input received an fq quench on boxC. The final archive passed SHA-256 comparisons before the scratch was removed. All owned workers stopped.

| donor | target | kind | starts | best give-back | raw end minus live bar |
|---|---|---|---|---|---|
| 735 | 790 | b1 | 8 | 0 | 7.972289e-11 |
| 534 | 581 | b1 | 4 | 0 | 7.978329e-11 |
| 796 | 853 | b1 | 4 | 0 | 1.786775e-05 |
| 442 | 530 | b2 | 3 | 0 | 0.0004690981 |
| 442 | 485 | b1 | 2 | 0 | 0.0004690981 |
| 485 | 530 | b1 | 2 | 0 | 0.0004690981 |
| 737 | 792 | b1 | 1 | 0 | 0.001862412 |
| 917 | 978 | b1 | 2 | 0 | 0.001875704 |
| 744 | 799 | b1 | 3 | 0.0008845827 | 0.002304377 |
| 634 | 685 | b1 | 10 | 0.001697737 | 0.002562883 |
| 870 | 929 | b1 | 5 | 0.03376517 | 0.002595664 |
| 860 | 919 | b1 | 9 | 0.007498774 | 0.002967892 |
| 590 | 639 | b1 | 1 | 0.001651989 | 0.003373549 |
| 912 | 973 | b1 | 1 | 0.001469023 | 0.003376 |
| 922 | 983 | b1 | 2 | 0.009298852 | 0.00362369 |
| 852 | 911 | b1 | 21 | 0.002379007 | 0.003922398 |
| 735 | 847 | b2 | 4 | 0 | 0.004758618 |
| 911 | 972 | b1 | 15 | 0.0016632 | 0.004761173 |
| 750 | 805 | b1 | 1 | 0 | 0.004844599 |
| 695 | 748 | b1 | 1 | 6.156316e-07 | 0.004876273 |
| 802 | 859 | b1 | 3 | 0.007788293 | 0.004916823 |
| 798 | 855 | b1 | 1 | 0.007915979 | 0.005108378 |
| 921 | 982 | b1 | 1 | 0.006827071 | 0.005940935 |
| 745 | 800 | b1 | 2 | 0 | 0.006094 |
| 550 | 597 | b1 | 2 | 0.01113463 | 0.006332547 |
| 861 | 920 | b1 | 3 | 0.008311118 | 0.007084674 |
| 803 | 860 | b1 | 2 | 0.006198435 | 0.00713148 |
| 849 | 908 | b1 | 1 | 0 | 0.007406743 |
| 794 | 851 | b1 | 2 | 0.04158031 | 0.0076585 |
| 689 | 742 | b1 | 1 | 0.002323812 | 0.007895858 |
| 646 | 697 | b1 | 1 | 0 | 0.008293554 |
| 862 | 921 | b1 | 1 | 0.005292747 | 0.008476131 |
| 872 | 931 | b1 | 2 | 0.00706823 | 0.008495499 |
| 800 | 857 | b1 | 1 | 0 | 0.008504471 |
| 916 | 977 | b1 | 3 | 6.996089e-09 | 0.008616307 |
| 908 | 969 | b1 | 1 | 0.001986188 | 0.008642797 |
| 540 | 587 | b1 | 1 | 0.005488687 | 0.008776628 |
| 690 | 743 | b1 | 1 | 2.580424e-05 | 0.008904896 |
| 934 | 995 | b1 | 1 | 0.0101379 | 0.009015239 |
| 931 | 992 | b1 | 2 | 0.2216602 | 0.009278348 |
| 755 | 810 | b1 | 2 | 0 | 0.009673964 |
| 588 | 637 | b1 | 1 | 0.001445201 | 0.00989997 |
| 806 | 863 | b1 | 1 | 0.001336351 | 0.01006596 |
| 799 | 856 | b1 | 1 | 0 | 0.01010659 |
| 855 | 914 | b1 | 1 | 0 | 0.01022815 |
| 791 | 848 | b1 | 3 | 0 | 0.01100554 |
| 809 | 866 | b1 | 2 | 0 | 0.01109156 |
| 873 | 932 | b1 | 4 | 0.008595394 | 0.01130356 |
| 814 | 871 | b1 | 1 | 0.003884105 | 0.01137757 |
| 863 | 922 | b1 | 1 | 0.007171301 | 0.01153704 |
| 700 | 753 | b1 | 1 | 0 | 0.01159117 |
| 909 | 970 | b1 | 1 | 0.007474128 | 0.01159563 |
| 647 | 698 | b1 | 1 | 0.0006745388 | 0.01160106 |
| 648 | 699 | b1 | 3 | 0 | 0.01165843 |
| 687 | 740 | b1 | 1 | 0.002288759 | 0.01166803 |
| 743 | 798 | b1 | 1 | 0.00348321 | 0.01184855 |
| 920 | 981 | b1 | 1 | 0.0019113 | 0.01186069 |
| 699 | 752 | b1 | 1 | 0 | 0.01202071 |
| 793 | 850 | b1 | 3 | 0.004419419 | 0.01217026 |
| 746 | 801 | b1 | 1 | 0 | 0.01278619 |
| 595 | 644 | b1 | 1 | 0 | 0.01305522 |
| 804 | 861 | b1 | 2 | 0.005605314 | 0.01312227 |
| 932 | 993 | b1 | 2 | 0.005201689 | 0.01325338 |
| 548 | 595 | b1 | 3 | 4.44982e-09 | 0.01351858 |
| 742 | 797 | b1 | 1 | 1.357831e-07 | 0.01377042 |
| 416 | 457 | b1 | 2 | 0 | 0.0141876 |
| 856 | 915 | b1 | 1 | 0 | 0.01432975 |
| 871 | 930 | b1 | 3 | 0.001900858 | 0.01453196 |
| 639 | 690 | b1 | 1 | 0.00302789 | 0.01462125 |
| 859 | 918 | b1 | 1 | 0.0008519041 | 0.01495034 |
| 645 | 696 | b1 | 1 | 0 | 0.01517258 |
| 812 | 869 | b1 | 4 | 0.00210324 | 0.01531023 |
| 542 | 589 | b1 | 2 | 1.316752e-05 | 0.01549706 |
| 915 | 976 | b1 | 1 | 4.170572e-05 | 0.0155092 |
| 644 | 695 | b1 | 1 | 0 | 0.0156015 |
| 851 | 910 | b1 | 1 | 6.601934e-06 | 0.01606346 |
| 696 | 749 | b1 | 1 | 2.411953e-07 | 0.01670502 |
| 599 | 648 | b1 | 1 | 0 | 0.01699729 |
| 910 | 971 | b1 | 4 | 0.001280545 | 0.01714698 |
| 462 | 505 | b1 | 1 | 0 | 0.01771085 |
| 848 | 907 | b1 | 1 | 0 | 0.01774121 |
| 691 | 744 | b1 | 1 | 0 | 0.01862757 |
| 913 | 974 | b1 | 2 | 0.0006651178 | 0.01914588 |
| 547 | 594 | b1 | 1 | 3.728088e-05 | 0.01917087 |

### Round 26: filters, kicks and sub-windows of fresh layouts (2026-11-14)

**Result: no row.** No border result of round 26 is below its base bar and below every live round 26 take by more than 1e-10. Two results were below the base bar, but another lane published the same count first. The 328 cut from the backlog 365 is lower than the invent 328 by only 7.4e-11. The contact LP of a raw twoshort 501 is lower than the forensics 501 by 4.3e-10, but the quench lane published a 501 that is 3.8e-11 lower still.

The round 25 lane stopped without a report. Its STATE.txt and boxC scratch were the only record. We copied its 2,266 boxC files with SHA-256 checks and then removed that scratch. Its one take row, 581 from the soft 534 by b1, is already in the round 25b file at the same score. The base bar is `gate/cand-round25-1114b/details.csv`.

The r26 exclusions removed most of the frozen round 25 queue. Of its 928 starts, 347 name the Samanyu-seeded file `29e12ff3`. Another 84 name a stair-c 985 of rounds 22 to 25, and 48 name a held or gathered 921. Two name the held 801, two name the forensics-r25 540 and 735 rect files, and one names a midm-r25 921 kick. The provenance gate refuses all of them, and the source policy calls that gate. A control refuses a bare `29e12ff3` in parent evidence and a 747r join. It keeps a seed-ancestry-no notice.

Later in the round the gate became stricter, with three changes. First, a recorded max centre distance below 0.5 to prvsiyan 1105 or a Samanyu file now refuses the row, which is the backlog lane's rule. This drops the harvest-r26 rows 695, 814 and 416 and every near layout built on them. Second, a file named `ancestry-refused`, or one whose sidecar has a `refused` key, is refused. Third, the audit now walks a parent that is another lane's take csv through that lane's take.tsv row. Before this change only near parents were walked.

We adopted 10 round 25 starts. One was a saved chain within 1e-3 of the bar: 739 to 794, which ended 1.73e-4 above it. The others had the lowest expected end. The expected end is the margin minus the best give-back measured on the same donor and target pair in rounds 24 to 26. When a pair has no record, the give-back is taken as 0.3 of the margin. We skipped 692 starts on 15 measured dead-end pairs. Some of them also fail the gate. A dead-end pair has 3 or more records, and its best end is more than 1.5e-3 above the bar. We also skipped 221 starts whose expected end was above 4e-3.

Controls ran before any chain. Plain default fq took the archived 870 control from side 30.914404078294062 to 30.913882090742. A kicked chain (k=1, sigma 0.01) reached 30.913824485828, which is lower than both. Both endpoints passed floatsafe. A duplicate-square copy was refused.

Global fq kicks on near-bar endpoints are a measured dead end. We kicked the 794 endpoint 8 times, the 791 endpoint 4 times and a 909 endpoint 4 times, with sigma 0.003 to 0.04. All 16 chains returned to the side they started from, so the driver stopped queueing kicks at 14:50 UTC. We handed 794 and 791 to the soft and midm lanes. Two 140 s soft-box islands on our 794 endpoint found nothing.

The expected-end filter replaced the fixed margin cap for fresh chains. A fresh chain whose expected end is above 4e-3 gets no job. An explore tier gives one chain to each fresh pair below n=800 that has no record and a margin under 0.012. This tier runs only when the slots are idle. Direct windows always run. After 13:35 UTC, no fresh chain passed the filter, so worker1 sat idle.

The idle tier tested that filter. When worker1 sat idle, it ran the best start of 13 skipped clean pairs, one chain per pair. Nine chains gave back less than 4e-5. The largest give-backs were 8.25e-3 on 934 to 995 (0.43 of its margin), 4.94e-3 on 813 to 870 and 1.76e-3 on 850 to 909. Every chain ended above its expected end, between 5.9e-3 and 1.9e-2 above the bar. So the 0.3 guess for a pair with no record is too high, and the 4e-3 filter holds.

The second new step is a soft-box island on a stuck endpoint. fq and its kicks leave a b1 or rev endpoint where it is. So we ran the lane's `methods_soft.py` on boxC: one 140 s island at delta 2e-4, then one at 1e-4 from the best so far. A find then gets the worker's fq chain. We ran 8 endpoints, and the soft lane ran our 794 endpoint. Two of these 9 endpoints moved. The 365 endpoint (b1 of 328) fell from 1.48e-3 above its bar to a certified 1.63e-8 above it. The 328 endpoint (a corner window of 365) fell from 1.63e-3 to a certified 1.63e-8 above its bar. Both are in `near/` with their full recipe. Both landed in the basin of the live 328 and 365 layouts, and the 365 bar is itself a b1 of the 328 bar. So they rebuilt the best known pair and did not beat it. A further 1800 s island on 365 ended dry after 360 s. The other seven endpoints gave no find: 794, 851, 909, 737, 970, 995 and the 365 corner window of 790. The 737, 909 and 970 endpoints are one nested-border family, with sides that all end in .6425697.

The new design of this round is a sub-window scan of fresh layouts. In round 10 every sub-window of the held file was closed. This time the donors are the fresh layouts of the other r26 lanes. `wscan.py` runs `literature_window.scan_one` on boxC. For each count, it finds the smallest square window that holds that many squares, with anchors at square extents. `wfeed.py` on boxA sends each new take and near csv that passes the gate. It then sends the frozen round 25 and 24 take and near layouts. When a window is below the live bar by more than 1e-10*sqrt(c)+1e-9, wfeed cuts it, runs floatsafe, and stages a certified-file fq job. The driver publishes it through the same source policy as a corner window.

By 17:00 UTC wscan had scanned 2,387 distinct layouts (3,580 scans). Three windows were below the live bar when wfeed cut them, and none counts. The 909 window of the harvest-r26 971 lost to the harvest lane's own 909. The 328 window of the soft-r26 365 lost to the invent 328 (see below). The 850 window of a twoshort raw 909 (17:00 UTC) is 1.7e-10 above the quench-r26 850.

The rev, b1 and b2 composition scan over the held and fresh layouts found no real gain. Held and fresh layouts are closed under one or two borders.

The chains of the round, by donor and target (`work/measure.tsv`):

| donor | target | kind | starts | best give-back | raw end minus live bar |
|---|---|---|---|---|---|
| 739 | 794 | b1 | 9 | 2.395393e-06 | 0.0001732589 |
| 850 | 909 | b1 | 13 | 0.00175559 | 0.001289848 |
| 794 | 851 | b1 | 4 | 0.005627586 | 0.00185822 |
| 328 | 365 | b1 | 8 | 1.370867e-07 | 0.002130036 |
| 790 | 365 | rev | 2 | 0 | 0.002346554 |
| 909 | 970 | b1 | 2 | 0 | 0.003587895 |
| 684 | 737 | b1 | 3 | 1.738777e-08 | 0.003677934 |
| 968 | 365 | rev | 1 | 0 | 0.004710008 |
| 695 | 748 | b1 | 1 | 0 | 0.005551922 |
| 550 | 597 | b1 | 2 | 0.005560908 | 0.007451757 |
| 646 | 697 | b1 | 1 | 6.440252e-08 | 0.008271134 |
| 365 | 404 | b1 | 1 | 3.573681e-05 | 0.008812303 |
| 736 | 791 | b1 | 5 | 0 | 0.009907501 |
| 934 | 995 | b1 | 2 | 0.008247579 | 0.01090107 |
| 873 | 932 | b1 | 2 | 0.007832367 | 0.01129116 |
| 818 | 875 | b1 | 1 | 0 | 0.01205454 |
| 595 | 644 | b1 | 1 | 0 | 0.01206139 |
| 761 | 816 | b1 | 1 | 3.994867e-05 | 0.01271542 |
| 813 | 870 | b1 | 1 | 0.004937618 | 0.01338262 |
| 546 | 593 | b1 | 1 | 0 | 0.01364332 |
| 706 | 759 | b1 | 1 | 0 | 0.01463873 |
| 650 | 701 | b1 | 1 | 0.0001187807 | 0.01730709 |
| 459 | 502 | b1 | 1 | 0 | 0.01750223 |
| 501 | 546 | b1 | 1 | 0 | 0.01789534 |
| 375 | 414 | b1 | 1 | 0 | 0.01863399 |

The first agent of this lane stopped at about 16:31 UTC on a dropped connection. A second agent read STATE.txt and adopted its five processes. These were the driver, wfeed and finish on boxA, and worker1 and wscan on boxC. It kept them, because they all ran to the 17:15 UTC deadline.

The second agent found one real gain that the gate had blocked. The backlog lane published a 365 at side 19.5995354658. One border row and one border column less gives a 328 at side 18.599535465789828. That was 3.6e-5 below every live 328 take at that moment and 7.2e-4 below the base bar. The driver could not publish it, for two reasons. First, `provenance.bad` refused the backlog row on the bare text `CC BY-SA`. In that row the text only labels a measured max centre distance of 0.647 to the prvsiyan 1105 file, and that distance is above the 0.5 refusal line. Second, the source policy needs `forensics_sources.trace`, and the trace fails on that row. The same false positive kept the backlog 459, 595, 971 and 986 out of the window scan.

We changed `provenance.bad` in two ways. It drops the label `(CC BY-SA)` after `prvsiyan 1105` before it checks the text, so only a distance below 0.5 refuses. It also refuses a labelled low distance such as `samanyu_22249 (Samanyu-dev s=0.312`, which the old pattern let through. The control printed these results. A far distance of 0.647 passes. A prvsiyan distance of 0.347 is refused, and a labelled Samanyu distance of 0.312 is refused. A `CC BY-SA 4.0` licence and the prvsiyan dataset name are refused. An own CC0 source passes. After the change, the backlog 365 passes the audit, and wfeed sent the five backlog takes to the window scan.

We built the 328 by hand (`work/manual/m328.py`). `check_start` confirmed the rev start against the donor copy, and floatsafe certified it at score 0.02698754288520111. One certified-file fq on boxC gave a larger side, 18.599537718512, so we kept the certified input. We walked the donor ancestry: 63 files, no excluded name and no distance below 0.5. The held 581 and 534 rows and the rebuild 489 row are clean. But the invent lane had already published a 328 at 0.026987542959048927. Our 328 is lower by only 7.4e-11, which is inside the 1e-10 rule, so it does not count. The contact LP of the lane (`methods_lp.py`) took the window to 18.5995354655936 from a start inflated by 1e-6. That is still 2.8e-10 of side short of the rule, and the plain run gave no gain. The 328 and 365 layouts of every lane now sit at sides that end in .5995354656.

The contact LP was measured dry as a sweep on held packings. We ran it on fresh layouts of other lanes instead. These are the take and near csv files whose side is within 2e-6 above the live bar (`work/lpnear/pick.py`, 150 files, smallest gap first). The control ran first. From the 328 start inflated by 1e-6, the LP came back to 1.96e-10 below the start. The LP ran on 55 files before the deadline. Of these, 26 gained nothing and 11 gained at most 2e-11 of score. These were fq-converged takes and near layouts. The other 18 were raw near layouts that fq had not polished, and they gained 1.5e-10 to 5.0e-10. Only one of them, the twoshort raw 501, went below the live bar by more than 1e-10. The quench lane had a lower 501 by then. So the LP is dry on converged layouts. On raw layouts it is worth one run, but only when the raw side is already within about 5e-9 of the bar.

### Round 27: the re-opened inputs and the LP follow of fresh takes (2026-11-14)

**Result: no row.** The lane certified four rows below the bar. Two lost to lower rows of other lanes within 15 minutes, and two were withdrawn because a parent was withdrawn. At 23:55 UTC the take is empty.

| n | certified score | below bar27 | what it was | what happened |
|---|---|---|---|---|
| 866 | 0.01514782426540151 | 1.822e-4 | contact LP of the backlog 866, then one certified-file fq | twoshort went 3.75e-8 lower 7 minutes later |
| 916 | 0.016016510851622368 | 6.44e-5 | LP and fq of the harvest 916 | withdrawn: harvest withdrew that parent 38 s before we published |
| 693 | 0.01787045989688929 | 4.82e-8 | sub-window of the forensics 859 rectangle | classfill went 9.1e-7 lower 13 minutes later |
| 798 | 0.017399397990594423 | 1.31e-8 | LP of the forensics 798 rectangle | withdrawn: part A is the k123 798, which k123 withdrew at 23:07 UTC |

The round 27 brief lifted the Samanyu rule. The layouts that match the Samanyu-dev seed came from our own code, so that ancestry no longer refuses a row. The brief also replaced the prvsiyan distance cut with a share test. A layout is out when 0.4 or more of its squares lie within 1e-3 of the prvsiyan 1105 row of the same n. The bar for each n is `round27-briefs/bar27.tsv`. It is the lower of the held round 25 b file and the best certified round 26 take.

#### Tool changes and controls

The round 27 tools are in `tools/border/r27`. They are the round 26 tools with these changes:

- `provenance.bad` no longer refuses the Samanyu names: `29e12ff3`, `747r`, `Samanyu-dev/squares_in_squares`, the held 921, the stair-c 985 and the 735 and 790 trees of seed 365. It still refuses CC BY-SA, the prvsiyan file name, the penguin069 counts, the held 801 and the withdrawn parents. A recorded distance to prvsiyan or a Samanyu file is no longer a test.
- `provenance.prvsiyan_share` runs the classfill `prvsim26.py` on each row before it is published. A share of 0.4 or more refuses the row. The share goes into the source cell.
- `source_policy.classify` renames every Samanyu text before the imported soft and forensics policies read it. `samanyu1808` stays as it is. When `forensics_sources.trace` fails, a clean `provenance.audit` walk now lets the row through. This was the second item of our round 26 list.
- `base27.py` reads the bar file. `reopen.py` lists the re-opened inputs. `lpfeed.py` and an LP job kind in `worker.py` run the contact LP on boxC. `direct.py` and `below_scan.py` find frozen layouts below the bar.

The controls printed these results:

- The share test measured 0.573 on the base 818, so that layout is refused. It measured 0.000 on the classfill r26 818, so that one passes.
- `bad()` now passes a bare `29e12ff3`, a `747r` join and a labelled Samanyu distance. It still refuses `CC BY-SA 4.0`, the prvsiyan file name and the held 801.
- The source policy passes a Samanyu donor, a bare `29e12ff3` parent and a `747r` join. It still refuses CC BY-SA, the prvsiyan file and `seed merged0`.
- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 75.7 s. Round 26 measured the same endpoint.

#### What ran on the re-opened inputs

We scanned 9,448 frozen take, near and withdrawn files of rounds 22 to 26, and the re-opened seeds (`below_scan.py`). In 44 counts a layout has a raw side below the bar27 side by more than 3e-9. By 20:50 UTC other lanes had re-published 15 of them: rebuild, quench, backlog, classfill, k123, twoshort and invent. The others are out for reasons that still apply, or harvest and backlog hold them in their own re-open queues. The reasons that still apply are penguin069 for 639 and 858 and gone parents for 972 and 632. The others are the prvsiyan share for 926 and the harvest 695 tree, and unwalked starts. Our direct pass (`direct.py`) walked 4 of the 44 counts in 44 minutes at load 120, so we stopped it.

The border tools found no new row in the re-opened inputs:

- One or two borders on the seeds `samanyu_bestfit.csv` and `samanyu_22249.csv` and on the held file: the best margin was -1.5e-9 of side. That is inside the certification slack, since the rule needs about -3e-9 at n = 900.
- A corner window plus one or two borders (`scan_revb1.py`) on 3,255 re-opened and fresh files: 128,243 compositions under 5e-4. The best was -1.24e-9 of side, on 790 from a 735 window of a forensics r23 847 rectangle. The rule needs -2.8e-9 at 790, and the 790 bar is itself a b1 of that 735 family.
- The b1 margins of the re-opened rows (866, 927, 648, 935, 812, 871, 599, 860) were 9.7e-3 to 2.4e-2 above the bar.
- The driver adopted 16 starts of rounds 25 and 26 that the round 26 gate had refused. It then queued 48 chains from re-opened donors on three pairs: (860, 919), (922, 983) and (861, 920). These pairs are measured dead ends: 3 to 131 records each, with best ends 2.97e-3 to 7.08e-3 above the bar. We skipped those chains, and the driver now applies the dead-pair rule to fresh donors too.

The window scanner (`wscan.py`) covered 3,564 distinct layouts: the re-opened pool first, then every fresh take and near file of round 27. Two windows were below the live bar by the rule when they were scanned. The 693 window of the forensics 859 rectangle became a row. The forensics composition holds the held 693 as a block, and its fq improved that block by 1.27e-6 of side. A 793 window of the harvest 851 was 1.3e-3 below bar27, but another lane already held a lower 793 when our driver cut it.

#### The LP follow of fresh takes

This was the first item of our round 26 list. `lpfeed.py` gives each fresh take and near csv of round 27 within 5e-9 of side of the live bar one contact LP (`methods_lp.py --iters 40`, 300 s cap). The result, or the start when the LP gains nothing, then gets one certified-file fq. The driver publishes the lower of the two through the source policy, the share test and the live-take check. From 21:20 UTC the queue also held 184 frozen raw and unconverged near layouts within 1e-11 to 5e-9 of side above the bar.

We queued 459 inputs: 275 fresh and 184 frozen. 244 ran before the deadline. On 195 of them the LP gained nothing. On 35 the LP output certified below the live bar, but mostly by only 1e-10 to 3.3e-10 of side, about a tenth of the rule. One input crossed the rule: the backlog 866 take, at -4.6e-9 of side after the LP. The fq after it went 1.2e-6 of side lower still, so that take had not been converged by its one fq. The 916 and 798 rows also came through this path. On the converged files, the fq after the LP ended higher than its input. For example, 973 went from 31.6891037 to 31.68912, and the driver kept the smaller. The walk refused 83 LP results below the bar. Their starts were on WITHDRAW lines or had unresolved parents.

The race decided the rows again. The 866 lasted 7 minutes and the 693 13 minutes, until the kick lanes followed them. The backlog lane claimed a follow of each of our rows within a minute. The live take csv files now come first in the LP queue. At 22:33 UTC the classfill 793 had waited 11 minutes behind near files.

Two rows were withdrawn. `provenance.audit` now reads the WITHDRAW lines of `handoff-r27.log`. It refuses a file named there when the file is gone or older than the line. It also refuses a row whose record names the sha256 prefix of a withdrawn file, since lanes name pinned snapshots, not paths. The 798 needed the second test, because its record named the forensics snapshot of the k123 798. The control refuses our withdrawn 798 and still passes our 693.

#### Load on boxA

boxA ran at load 94 to 120 all evening. The ancestry walk took most of the wall time of the light processes. From 20:05 to 20:22 UTC, the boxC window scanner and worker sat idle while the feeders walked ancestry. We changed the order. The walk now runs only for a layout whose scan finds a window, a border pick or an LP result below the bar. After this change, the feed queued 279 layouts in a few minutes. Two more costs came from restarts. Each driver restart re-certified 16 finished chain ends that were all above the bar. Each restart also re-read 12 finished quench jobs, one floatsafe each. Chain ends and finished jobs above the bar are now closed without floatsafe, and the closed jobs persist in `work/published.json`. One layout held the window scanner for 37 minutes of CPU. Each scan now stops after 90 s.

#### Not run yet

- Run the LP and certified-file fq follow on every fresh take csv of other lanes within a minute of its row, before anything else. Measured: it gave all four rows of this round, and the crossing on the 866 came from a take that one fq had not converged. On converged takes it gained 0 to 3.3e-10 of side, about a tenth of the rule.
- Read WITHDRAW lines before each publication, and match them by path and by sha256 prefix. Measured: 916 and 798 were published on parents that had been withdrawn 38 s and 7 minutes earlier.
- Keep the walk after the scan on a loaded boxA. Measured: with the walk first, the boxC slots sat idle for 17 minutes, and after the change the feed queued 279 layouts in minutes.
- Window scans of fresh rectangle compositions, with the 90 s cap: the 693 came from a composition that embeds a held block. 3,564 layouts gave 2 windows below the rule.
- Stop the border closure scans and the chains on re-opened and fresh layouts. Measured: 128,243 compositions with best -1.24e-9, b1 margins 9.7e-3 to 2.4e-2, and dead-end pairs only.

### Round 28: the LP follow of fresh takes, kicked follows and a finer floatsafe (2026-11-15)

**Result: 2 rows, 642 and 916, 6.523e-5 of score below bar28, all of it beyond the other round 28 takes.**

The bar for each n is `round28-briefs/bar28.tsv`. It is the lower of the held round 26 b file and the best certified round 27 take. A main rule at 00:19 UTC changed two things. The prvsiyan share test now applies only to rows whose first source is a public notebook or dataset. A withdrawal made only for a share is void. A row whose ancestry names the prvsiyan 1105 file still stays out.

#### Tool changes and controls

The round 28 tools are in `tools/border/r28`. They are the round 27 tools with these changes:

- `base28.py` reads the bar file. Each process writes its own temporary file, because two feeders crashed on one shared name.
- `provenance.withdrawn` reads the handoff logs of rounds 27 and 28 in time order. A REINSTATE or REOPEN line opens a path again, and so does a line that calls a withdrawal void or lifted. A withdrawal line that gives only a share is skipped. A line that also names another reason still counts. The reasons are penguin069, CC BY-SA, a licence, a notice, an unresolved trace, the rule-a family or an excluded family. A retention phrase counts only right before a path.
- `provenance.audit` no longer runs the ancestor share test.
- `source_policy.classify` keeps the status that the soft policy marks as lifted for Samanyu names.
- `driver.py` runs the share test only on public-first inputs. The border scan (`make`) reads only the fresh take csv of other lanes, and the chain-only b1 picks are off.
- `lpfeed.py` gives every LP result a polish fq (`--no-alm --loosen 1.0 --flip-top 64 --pit 600`). The default fq runs only on take inputs and on inputs more than 5e-9 above the bar. The processed outputs persist in `lp/done.json`, so a restart does not certify them again.
- `finesafe.py` certifies with a bisected dilation. See the next section.
- `kfeed.py` queues kicked follows of live takes. We measured it and stopped it.
- `worker.py` takes the fq flags from each job, and two workers share the queue.
- `design/` holds the block models of the design search.

The controls printed these results:

- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 76.5 s. Rounds 26 and 27 measured the same endpoint.
- The polish fq on the r27 LP final of 973 ended 1.4e-9 above its certified input. The default fq on the same input ended 1.9e-5 above.
- The source policy accepts an own root below the bar and a Samanyu seed. It refuses CC BY-SA, the prvsiyan file, `seed merged0` and unresolved sources.
- `withdrawn()` reads 40 withdrawn paths. These include the forensics 743 take and the 29 forensics near rectangles of 01:51 UTC. The share-only k123 798 lines stay void.

#### A finer floatsafe

`floatsafe.work` scales the centres about their mean by 1+e. It takes the first e of a 1-2-5 ladder that passes two tests. Every pair must clear 2.2e-11 on a separating axis, and the metric must accept the rows as written and after the pandas float parse. On every LP and fq output of this round the ladder stopped at e = 5e-11, but about 2.18e-11 is enough. `finesafe.py` bisects e between the failing and the passing ladder step. It then runs the same clearance test and both metric checks.

On the fq outputs of our 19 near files, finesafe certified 3.0e-10 to 8.2e-10 of side lower than the ladder. That is about 28% of the rule. The certify step of the driver, lpfeed and wfeed uses it from 02:30 UTC.

It moved one layout past the rule. The polish fq of the backlog near 503 certified 2.754e-9 below the live bar, and the rule needs 2.243e-9 at 503. The row still stays out. The backlog record of that parent names a public-first ancestor in `take-harvest-r22/work/collector/certified` with a prvsiyan 1105 share of 0.492.

#### What ran

Eight layouts certified past the rule. Five lost to lower rows of other lanes within seconds to 37 minutes. Two are in the final take. At the last refresh (05:51 UTC) no other round 28 take held 642 or 916, so the whole gain is beyond the other takes.

| n | certified score | below bar28 | below other takes | what it was | what happened |
|---|---|---|---|---|---|
| 499 | 0.02187739078442408 | 6.95e-6 | 7.8e-9 | LP and polish fq of the backlog 499 take | a backlog follow went lower 1 minute later |
| 499 | 0.02187731126229364 | 7.03e-6 | 4.5e-10 | the same chain, one step on | a backlog follow went lower 19 minutes later |
| 978 | 0.01536979320912368 | 1.66e-6 | 6.4e-10 | polish fq of the harvest 978 take | quench went lower 80 s later |
| 978 | 0.01536531084055959 | 6.14e-6 | 1.4e-8 | polish fq of a newer harvest 978 take | backlog had certified a lower 978 2 s earlier |
| 993 | 0.01293307850323999 | 2.4e-6 | 1.6e-8 | default-flag fq of the k123 993 take (Samanyu ancestry) | midm went lower |
| 916 | 0.016016593991535544 | 6.43e-5 | 4.9e-9 | LP, polish fq and self follows of the forensics 916 rectangle | in the final take |
| 642 | 0.018923096216731716 | 8.96e-7 | 8.2e-10 | polish fq of the rebuild 642 take | in the final take |

The row from the first 916 certification is not listed, because the self follow replaced it 3 minutes later.

The LP follow (`lpfeed.py`) queued 480 inputs: 100 take csv files and 380 near files of other lanes. 478 ran before the deadline. The LP gained nothing on most of them. 96 certified outputs were below the live bar, the best by 2.17e-9 of side. The walk refused 101 outputs.

The polish fq always ends lower in raw side than its certified input. It did so on 65 of 67 take inputs and 293 of 296 near inputs, by a median of 1.4e-9. That is the dilation that the certify step added, and certifying again adds it back. The default fq ended lower on 2 of 67 take inputs, and the median take ended 5.0e-5 higher. The rows came from polish fq on takes that one fq or one kick follow had made. The polish gained 2.1e-8 of side on the harvest 978 take.

`sfeed.py` gives each new row of ours one more polish fq from its certified file. It repeats while a step gains more than 1e-9 of side. On the 916 the first step gained 4.4e-8 of side and the second step 1.2e-11, so the chain stopped. The self follows of the 978 rows came too late. The 978 self follow waited 12 minutes at the bottom of the worker queue, so follow jobs now carry the top priority. The same feeder gives a near file of ours one more polish when it is below the bar but short of the rule. It ran on 3 near files, and the best moved 6.7e-10 of side.

`kfeed.py` ran 36 kicked follows on 12 live takes, with one fq quench each at kick 0.003, 0.01 or 0.02. Two ended lower in raw side, by 1.3e-9 and 1.4e-9, inside the certification slack. The medians ended 1.6e-4 to 7.4e-4 higher. A kick does not move a converged take, so we stopped it after 18 minutes.

The window scanner ran 6,518 scans on 2,160 distinct fresh layouts. No window was below the rule. The border scan of fresh takes found only b1 picks 1.0e-2 to 1.8e-2 above the bar.

Three reading errors of the withdrawal lines were found and fixed during the round:

- At 01:51 UTC forensics withdrew 29 near rectangles for the rule-a family. The lines mention the lifted share rule, and our reader skipped them as share-only. Rule-a and excluded-family wording now count as a reason.
- With the case-insensitive search, the word "reopen" inside a named file turned 9 withdrawal lines into re-opens. REINSTATE and REOPEN now count only in capitals, and the prose words only outside a path.
- A SOURCE-HOLD line now counts as a withdrawal of every file of the builds it names. Stair-c held three builds at 03:41 UTC, and we had run LP on six of their files.

The walk also refuses the live rebuild and backlog 910 takes. They descend from the forensics r24 684 donor, which has a prvsiyan 1105 share of 1.000.

#### The end of the run

The session stopped at about 05:40 UTC, which killed the driver, `sfeed.py` and `finish.py`. We queued the last 916 self follow by hand. It ran, and fq gave no side. We then ran `finish.py --now` by hand. It copied 10,793 remote files with SHA-256 checks and removed the boxC scratch and its venv. The literature check passed on both rows with a minimum gap of 2.20e-11.

The round 27 `verify_proofs.py` failed on the 642 row, because it had no branch for an LP recipe. The round 28 copy checks the pinned donor hash, the certified score of the staged input and the byte-exact input of the job. It now passes on both rows. The 642 failure was the control that it can go red.

#### The design search

We modelled tilted-block designs to find new layouts for the m²+k counts of the board. The block is a×b squares at an angle, with upright rows along the walls.

- At 45° the rows model reaches 842 = 29²+1 only with the 17×17 block, at f = 0.52089. Our held 842 has f = 0.520815, so the model rebuilds our design, and no other 45° block of 13 to 21 squares a side does better.
- From 5° to 27.5° the rows model reaches no configuration.
- A control on 442 = 21²+1 failed. The held 442 is a block of about 230 squares at 20.7° with f = 0.525789. A mixed model at that angle reaches 428 of 442 at f = 0.53, and none at f = 0.75. The small-angle designs of the board need fills that the model does not hold, so we stopped the search.

#### Not run yet

- Run the LP and polish fq on every fresh take csv of other lanes within a minute, then a self follow of each new row. Measured: all seven certifications of this round came from this path. Takes made by one fq or one kick follow are not converged. The polish gained 2.1e-8 of side on the harvest 978 take, and the self follow gained 4.4e-8 more on our 916.
- Certify with the bisected dilation (`finesafe.py`) everywhere, the assembly included. Measured: 3.0e-10 to 8.2e-10 of side lower than the ladder on 19 fq outputs, about 28% of the rule. It moves every near miss by that much.
- Run the follow jobs of live rows before the LP queue. Measured: the 978 self follow waited 12 minutes, and the 978 row was gone before it ran.
- Match REINSTATE and REOPEN only as words outside file names, and read SOURCE-HOLD lines. Measured: 9 withdrawal lines were read as re-opens, and 29 rule-a near files were read as share-only, until the fix.
- Stop the kicked single fq follows, the window scans, the border scans of fresh takes and the block-model design search. Measured: 36 kicks gave nothing past the slack, and 2,160 layouts gave no window. The b1 picks were 1.0e-2 to 1.8e-2 above the bar. The model rebuilds 842 but misses the 442 control.

### Round 29: the take path, the band edge and two holes in the withdrawal walk (2026-11-15)

**Result: 1 row, 916, 7.085e-7 of score below bar29, all of it beyond the other round 29 takes.**

The bar for each n is `round29-briefs/bar29.tsv`. It is the lower of the held round 27 b file and the best certified round 28 take. Three source rules changed for this round:

- The Samanyu rule is lifted.
- Our own layouts (801, the Samanyu seeds 503 and 983, and their descendants) get no share test.
- A public-first row stays out when its licence is not Apache 2.0, CC BY 4.0 or CC0, or when its prvsiyan 1105 share is 0.4 or more.

A withdrawal applies to the pinned bytes it names.

#### Tool changes and controls

The round 29 tools are in `tools/border/r29`. They are the round 28 tools with these changes:

- `base29.py` reads the round 29 bar file.
- `lpfeed.py` gives each LP job a priority by kind. A fresh take of another lane comes first, then a fresh near file above the bar, then frozen inputs. A fresh near file at the bar side comes last. A race in the seen set marked a fresh take as done against an old bar. The set now takes an input only after its bar check.
- `kfeed29.py` gives one 900 s `midm_scan.py` lkick,kick run to a near file that the rebuild follow chose and skipped because its queues were full. It runs one kick per n, unless a new input is 1e-9 lower. It also collects the band-edge runs of `bfeed29.py`, below.
- `worker.py` (boxC) runs these kick jobs. A job can name its modes, its donor file and its flag sets. Worker 2 takes kick jobs first. Worker 1 takes them only after the take path: the LP of fresh takes, the take finals and the self follows.
- `provenance.withdrawn` reads the logs of rounds 27 to 29. A re-open word counts only in the prose of a line, not inside a file name. Three fixes followed, one in the reader and two in the walk. See "Withdrawals" below.
- `provenance.audit` gives the public-first share test to every ancestor that comes from a harvest or public folder. It tests the n of the descendant. Before this fix it tested n = 1 of whole public files, which always has a share of 1.0, and it refused 907, 582 and 848.
- `driver.refresh` audits our own take rows again on every pass.
- `finish.py` also stops `sfeed.py` and `kfeed29.py`.

The controls printed these results:

- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 73.5 s. Rounds 26 to 28 measured the same endpoint.
- The withdrawal reader still refuses the 849 rule-a rectangle by its sha256, before and after each fix.
- After the last fix our 376 row and its twoshort parent are refused, and our 916 and the backlog 916 take pass.

#### What ran

Ten certifications passed the rule. One of them is in the final take. At the last refresh (11:51 UTC) no other round 29 take held 916, so the whole gain is beyond the other takes.

| n | certified score | below bar29 | below other takes | what it was | what happened |
|---|---|---|---|---|---|
| 916 | 0.01601655675443103 | 3.72e-8 | 6.6e-10 | LP and polish fq of the backlog 916 take | backlog followed it and went lower at 08:20 UTC |
| 916 | 0.01601588551444388 | 7.08e-7 | 2.2e-8 | LP and polish fq of the backlog 916 follow of our row | in the final take |
| 752 | 0.01650845182050631 | 3.39e-5 | 1.1e-7 | LP and polish fq of the k123 752 take | backlog went lower 7 minutes later |
| 376 | 0.02502672744936674 | 1.34e-8 | 1.34e-8 | LP of a twoshort near file | withdrawn by us after 4 minutes (withdrawn ancestor) |
| 988 | 0.01397370560346678 | 4.40e-5 | 3.37e-5 | default fq of the forensics 988 rectangle take | the next row |
| 988 | 0.01397292241317749 | 4.48e-5 | 3.45e-5 | default-flag self follow of our 988 row | backlog went lower 10 minutes later |

The table leaves out three 916 rows and one 376 row, because a self follow replaced each within minutes.

The 988 shows that a fresh rectangle take is not converged. The LP gained nothing on it, but the default fq with ALM gained 1.06e-3 of side. A default-flag self follow gained 7.8e-7 of score more. We then ran the default fq with `--seed 11` and `--seed 12`. Both ended at 31.87169524356431, the same side to 14 digits as the plain default fq. A seed alone does not change a quench without a kick.

The LP follow (`lpfeed.py`) queued 514 inputs: 81 take csv files and 433 near files of other lanes. 507 ran before the deadline. The LP gained nothing on 457 of them. 183 certified outputs were below the live bar, and the walk refused 130 outputs.

The polish fq ended lower in raw side than its certified input on 74 of 74 take inputs and 308 of 310 near inputs. The median was about 6.5e-10. That is the dilation that the certify step adds. The default fq ended lower on 14 of 75 take inputs, and the median take ended 2.9e-6 higher.

The 916 went from us to backlog and back. We certified it first at 08:14 UTC, from an LP of the backlog 916 take. Backlog went lower at 08:20 and 08:30 UTC with follows of our row. The 08:30 row was 6.5e-7 of score below ours. Our LP and polish of that backlog row then certified 2.2e-8 lower again, at 08:36 UTC. The rebuild follow and a backlog follow of those bytes found nothing lower. A 900 s bkick and melt run of ours found nothing lower either.

#### The band edge

At each side m our held file has the plain m×m grid for every n from n_low(m) to m². The board of 2026-11-09 is below m at five of these n_low: 605, 762, 877, 937 and 1000. The n_low−1 layouts we tried sit 0.004 to 0.024 below m. So we tried `midm_scan.py --modes grow1`. Each try puts one square into the widest hole of our n_low−1 layout, then runs one fq quench, rotating the flag sets d, t, k and K.

| n | n - 1 layout | tries | best end |
|---|---|---|---|
| 91 | backlog 90 take, 9.99404 | 1,105 | 10.000000000450 (the grid) |
| 133 | held 132, 11.97605 | 403 | 12.000000000550 (the grid) |
| 158 | held 157, 12.99330 | 332 | 13.000000000600 (the grid) |
| 762 | held 761, 27.9904 | 26 | 28.0000000000055 (the grid) |
| 937 | held 936, 30.99074 | 18 | 31.0108 |
| 1000 | held 999, 31.99571 | 22 | 32.0000000000065 (the grid) |

Every end near m was the plain grid again. The best end that was not the grid was 0.0036 above m (133). The fq quench of an n_low−1 layout plus one square goes back to the grid or ends higher. It does not find the board design.

The grid finds at 762 and 1000 certified 7.6e-10 and 8.7e-10 of side below the held grid rows. The rule needs 2.8e-9 and 3.2e-9 there. So a cleaner grid certification does not reach the rule at any n.

#### Kicks of skipped near files and of converged takes

`kfeed29.py` kicked 5 near files that the rebuild follow had skipped: 814 (20 tries), 748 (142), 790 (185), 997 (9) and 792 (25). None of them went below its start. We stopped a sixth run (454) when forensics withdrew its bytes. The rebuild lane measured 0 of 9 on the same kind of input.

A 900 s bkick and melt run on our 916 row and on the midm 752 take found nothing lower. The best melt ends were 3.3e-3 and 3.9e-4 of side above the start, and the best bkick end at 752 was the 28.0 grid.

#### Withdrawals

We found and fixed three holes:

- The trigger words matched inside file names. The words "reopen" and "withdraw" inside names (for example `r27reopen`, `reopened932v4`) turned several lines into withdrawals. This refused the clean chain 871, 812, 813, 933 and 995. The words now count only in the prose of a line. The count of withdrawn paths went from 550 to 527, and the 849 rule-a control stayed refused.
- The reader skipped every withdrawal that gives only a share, which was the round 28 rule. In round 29 a public-first share of 0.4 or more is a valid reason. So the reader skipped three valid withdrawals: classfill 503 (07:52 UTC), harvest 454 (08:07 UTC) and forensics 376 (08:32 UTC). A share line now counts when it says public-first or public-source.
- The walk checked a withdrawal only on near parents. It never checked a withdrawn take csv that was already gone. Our 376 row came from an LP of a twoshort near file. Twoshort made that file at 08:35 UTC from the forensics 376 bytes, which forensics had withdrawn at 08:32 UTC. The row certified 1.34e-8 below the bar and was in our take from 09:51 to 09:55 UTC. Now every csv ancestor that a withdrawal names refuses the row when the file is gone or older than the line. So does a name that carries the last 8 hex characters of a withdrawn sha256. The twoshort file name carried `299a6d9f`, the tail of the withdrawn sha256. We posted a WITHDRAW line for our 376 bytes.


#### The end of the run

`finish.py` ran at 11:45 UTC. It stopped the driver, the four feeders and boxC worker 1. Worker 2 had already stopped at its own deadline. It copied 5,655 remote files with SHA-256 checks and removed the boxC scratch and its venv. The literature check passed on the 916 row with a minimum gap of 2.20e-11. `verify_proofs.py` passed: the pinned donor, the certified input and the published result are byte exact. `measure.py` failed, because this round ran no chain queue (`q/manifest.tsv`). It measures nothing that this round used.

#### Not run yet

- Run the LP, the polish fq and the default fq on every fresh take of other lanes within a minute. Then give each new row a polish and a default-flag self follow until a step gains under 1e-9 of side. Measured: all ten certifications of this round came from this path. The default fq gained 1.06e-3 of side on the fresh forensics 988 rectangle take, where the LP gained nothing.
- Walk every withdrawn ancestor, a take csv that is gone included, and match withdrawn sha256 tails in file names. Audit our own take rows again on every refresh. Measured: our 376 row was in the take for 4 minutes through a withdrawn take csv that the walk never checked.
- Read a share withdrawal of a public-first row as valid. Measured: the round 28 reader skipped three valid round 29 withdrawals (503, 454 and 376).
- Stop the band-edge grow1. Measured: 1,906 tries on 6 n. Every end near m was the plain grid, and the best other end was 0.0036 above m.
- Stop the lkick and kick runs on near files that the rebuild follow skipped, and the bkick and melt runs on converged takes. Measured: 0 finds in 381 kick tries on 5 near files, and 0 in 38 bkick and melt tries on 2 takes.
- Vary a quench with `--kick`, not with `--seed`. Measured: two seeds gave the same side as no seed, to 14 digits.

### Round 30: kicks of held rows that nobody kicked, and the take path (2026-11-15)

**Result: 1 row, 494, 9.948e-6 of score below bar30, all of it beyond the other round 30 takes.**

The bar for each n is `round30-briefs/bar30.tsv`. It is the lower of the held round 28 b file and the best certified round 29 take. The Samanyu rule stays lifted. Our own layouts (801, the Samanyu seeds 503 and 983, and their descendants) get no share test.

#### Tool changes and controls

The round 30 tools are in `tools/border/r30`. They are the round 29 tools with these changes:

- `base30.py` reads the round 30 bar file.
- `provenance.enrich_source` takes the per_n.csv row of the output count for two more kinds of areebbb chain. The first kind names the areebbb `submission.csv` with no harvest r22 donor path (the rebuild r29 594 bar row). The second kind names areebbb only in the licence cell of a results table (the held 791 of round 26). Before this change both were refused for "areebbb ancestry lacks a per-n public donor". The excluded counts 639, 691, 745, 858 and 918 still refuse.
- `provenance` follows the main session's ruling of 12:40 UTC. A withdrawal for the share of a held ancestor is void. So are the withdrawals that followed only because they descend from the withdrawn forensics r29 376 bytes. The share test now reads only a public-first ancestor of the same n. In round 29 it also read ancestor files of other counts, and it refused the midm r30 412 take through an 805 file.
- `kfeed30.py` runs two kick slots on boxC. Worker 2 always runs one kick (900 s, then 450 s from 15:19 UTC). Worker 1 runs one 300 s kick when its LP and fq follows are empty. A kick can move its start by more than 1e-6 of side and certify within 1e-5 of the bar. Then it gets one more leg of the same length from its certified find.
- `kfeed30.py` kicks four kinds of input. In order, they are fresh takes of other lanes, and near files of k123, forensics and invent from 1e-7 to 3e-5 above the bar. Then come the parked Samanyu-seed held rows of bar30. Last come the other held rows of bar30 that no kick or claim line of rounds 28 to 30 names. The held rows are n 200 and up where our bar is 3e-6 or more of score above the board of 2026-11-09, largest gap first. A row whose side fraction repeats at another n is left out, because a repeated fraction marks a rigid construction.
- At 17:15 UTC the near files moved after the held rows. `lpfeed.py` then gave a fresh near file above the bar priority -138, after the worker 1 kicks (-140). Both moves follow the yields measured below.
- `worker.py` (boxC) runs a kick job on the worker that the job names.
- `finish.py` also stops `kfeed30.py`.

The controls printed these results:

- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 73.3 s. Rounds 26 to 29 measured the same endpoint.
- After the `enrich_source` changes 594 and 791 are enriched, and 745 and a text without the submission name are still refused.
- After the share changes the midm r30 412 take and the harvest r29 412 row pass. The harvest r30 376 take (public-first, share 0.654 at n = 376) is still refused, and so is the 849 rule-a rectangle.
- The chain-leg rule, replayed on finished kicks, queued leg 1 for 378 and nothing for the kicks that moved less than 1e-6.

#### What ran

Five n certified under the rule. One is in the final take.

| n | below bar30 | below other takes | what it was | what happened |
|---|---|---|---|---|
| 802 | 4.5e-10 | 1.7e-10 | LP and polish fq of the backlog 802 take | refused at 13:34 UTC: its tree names the forensics r22 donor 799-986b3b6d, which the main session keeps out as a direct public-first start |
| 695 | 8.908e-6 | 2.0e-10 | LP and polish fq of the backlog 695 take | backlog went lower 6 minutes later |
| 494 | 2.613e-6 | 2.613e-6 | 900 s kick of the parked Samanyu-seed held row (round 28 b bytes) | the next row |
| 494 | 9.948e-6 | 9.948e-6 | 900 s leg 1 from that find, 1.630e-4 of side lower | in the final take |
| 791 | 2.678e-6 | 2.678e-6 | 300 s kick of the held 791 (order 3 class) | backlog followed our find to 7.9e-6 below bar30, 4 minutes later |
| 653 | 4.71e-7 | 2.2e-9 | LP and polish fq of the twoshort 653 take | backlog went lower 7 minutes later |

Leg 2 of the 494 kick found nothing lower in 900 s.

`kfeed30.py` finished 44 kicks by 17:45 UTC, in five kinds:

| kind | kicks | moved more than 1e-6 of side | rows |
|---|---|---|---|
| fresh take of another lane | 4 | 0 | 0 |
| k123 three-way near file | 13 | 10 | 0 |
| chain leg | 10 | 2 | 1 (494) |
| parked Samanyu-seed held row | 6 | 1 | 1 (494) |
| other held row | 11 | 1 | 1 (791) |

Ten k123 near files moved by 1.8e-6 to 5.9e-6 of side. Each one certified at the bar side, from 1.1e-9 below it to 1.2e-7 above it, and never below the rule. Their legs moved nothing more. The near file is the bar layout plus a few micro-units of slack, and the kick removes only that slack. We stopped the 806 leg after 24 s to give its slot to a held row.

Five held rows (842, 901, 902, 962 and 703) moved by 1.3e-9 to 1.5e-9 of side. That is the polish of the certify dilation, and the rule needs 2.6e-9 to 3.1e-9 there. Two of them share a side fraction with another n, which marks a rigid construction. After 15:32 UTC such rows left the list.

The LP follow (`lpfeed.py`) queued 506 inputs: 90 take csv files, 406 near files and 10 frozen files. The LP gained nothing on 355 of them. 303 outputs certified, and 64 of those were below the live bar side. The walk refused 68 outputs. All four LP rows (802, 695 and two of 653) came from take csv files of other lanes. No near-file LP gave a row.

#### Not run yet

- Kick every held row of the bar file that no lane kicked in the last three rounds, before any near file. Measured: kicks of 17 held rows gave 2 rows. The 494 kick found 5.807e-5 of side and its leg found 1.630e-4 more. The 791 kick found 7.531e-5. The 13 k123 near files gave none. 58 of the 71 listed held rows got no kick from us this round. Another lane claimed some of them.
- Chain a leg from every kick find that moves more than 1e-6 of side. Measured: the 494 leg gave 1.630e-4 of side more after a first find of 5.807e-5.
- Stop kicking k123 three-way near files. Measured: 10 of 13 moved by more than 1e-6 of side, and every one certified at the bar side or above it.
- Keep the LP and polish fq of fresh takes of other lanes, but expect each row to be followed within minutes. Measured: 695, 653 and 791 each went to backlog within 4 to 7 minutes, and only the kick row 494 stayed ours.


### Round 31: a probe on held-row kicks, and long seeds on a row with slack (2026-11-15)

**Result: 2 rows, 494 and 864, 1.576e-5 of score below bar31. 1.460e-5 of it is beyond the other round 31 takes.**

The bar for each n is `round31-briefs/bar31.tsv`, the submitted round 30 c file. Every row of a file we submitted is our own layout, so a kick of a held row gets no share test. A public-first row is out when its share against a 1105 row that is not our own layout is 0.4 or more at 1e-3 or at 1e-2.

#### Tool changes and controls

The round 31 tools are in `tools/border/r31`. They are the round 30 tools with these changes:

- `build_held31.py` writes each row of the round 30 c file to `held31/<n>.csv`. Its record points at the row of n in the latest `results/round*-best` table. `build_order_all.py` ranks the held rows in four classes. Class 0 holds the rows that no kick or claim line of rounds 29 to 31 names. Class 1 holds the rows that round 30 c added. Class 2 holds the rows that only round 29 named, and class 3 the rows that round 30 named. Within a class the largest board gap comes first. A side fraction that 3 or more n share marks a closed form, and such a row is left out. A pair is a border step: 539 is 494 plus a strip.
- `kfeed31.py` skips every n that another lane claimed in `handoff-r31.log`. It waits 10 minutes before it kicks a fresh take of another lane, because backlog is the follow lane. It does not kick near files.
- `worker.py` (boxC) runs a kick with a probe. After 120 s, and after at least 2 tries, the kick stops when no try came 3e-9 of side or more below its start. The certify dilation alone moves a held row by 1.3e-9 to 1.5e-9.
- `kfeed31.py` gives a first scan that gains 1e-5 of score or more two more seeds. It takes hand-queued kicks from `kq/manual`.
- `deepfeed.py` (from 21:29 UTC) gives worker 2 one 900 s kick with no probe per held row, largest board gap first.
- `lpfeed.py` reads take csv files only, and an LP result gets the polish fq only.
- `provenance.prvsiyan_share` takes the largest of prvsim26 at 1e-3, prvsim26 at 1e-2 and the assembler's `share30.py`. A share against a 1105 row that equals our own seed in every harvested version reads 0 (228, 405, 588, 635, 741 and 974).
- `verify_proofs.py` checks the kick proof kind.

The controls printed these results:

- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 72.7 s, the same endpoint as rounds 27 to 30.
- Probe, held 902 (60 s probe): it stopped at 60 s after 33 tries. Its best try was 1.5e-9 below the start.
- Probe, held 902 scaled by 1 + 2e-6: the first try found 5.9e-5 of side, and the kick ran to its end (93 tries, 152 s).
- `share30.py` reads the public 851 input at 0.4642. Harvest and backlog measured 0.46416. It reads our own 494 seed row at 0.664, because one version of the 1105 row is our seed.
- `verify_proofs.py` passes on a copy of the round 30 494 row. It fails on the same row with one x moved by 1e-9.

#### The probe, measured

We read the 60 kick logs of border rounds 29 and 30. 14 kicks moved more than 1e-6 of side. 12 of them crossed 3e-9 within 120 s. The 494 kick (470 s) and its leg (800 s) did not. The rows that moved only by the dilation never crossed 3e-9. Six of them crossed 1e-9 within 3 s, so a 1e-9 line would stop nothing.

Then we read the 2943 kick logs of all lanes in rounds 28 to 31. Of the kicks that moved 1e-6 to 1e-4 of side, 40% made their first 3e-9 find after 120 s. For moves of 1e-4 or more the share is 33%. A probe still tests about 6 rows in the time of one full kick, so the probe stays on the held-row list.

#### What ran

Two n certified under the rule. Each certified row and what became of it:

| n | below bar31 | below other takes | what it was | what happened |
|---|---|---|---|---|
| 494 | 7.501e-6 | 7.501e-6 | second 900 s seed (478) of our own round 30 494 row, 1.667e-4 of side lower | the next row |
| 494 | 1.460e-5 | 1.460e-5 | 900 s leg 1 from that find, 1.577e-4 of side lower | in the final take |
| 864 | 6.49e-7 | 6.49e-7 | 900 s depth kick of the held 864 with no probe, 1.908e-5 of side lower | the next row |
| 864 | 1.004e-6 | 1.004e-6 | leg 1 from that find, 1.044e-5 of side lower | backlog followed it to 1.073e-6 below bar31, 6 minutes later |
| 864 | 1.159e-6 | 2.0e-10 | LP and polish fq of the backlog 864 take | in the final take, 2.0e-10 below the backlog 864 |

The first 900 s seed of our own 494 row found nothing. Two seeds of 494 leg 2 (900 s each) found nothing. Leg 2 of 864 moved 1.224e-6 of side, but it ended 3.2e-6 above the backlog row. Leg 3 of 864 stopped at the probe.

`kfeed31.py` and `deepfeed.py` finished 95 kicks by 00:01 UTC, in five kinds:

| kind | kicks | seconds | moved more than 1e-6 of side | rows |
|---|---|---|---|---|
| held row with the 120 s probe | 73 | 9,907 | 0 | 0 |
| held row, 900 s depth kick with no probe | 7 | 6,464 | 1 (864) | 1 (864) |
| our own round 30 494 row, 900 s | 2 | 1,813 | 1 | 1 (494) |
| chain leg | 6 | 4,768 | 3 | 2 (494, 864) |
| fresh take of another lane | 7 | 2,414 | 1 (464) | 0 |

The probe stopped 70 of the 73 held kicks. The best of them moved 971 by 1.2e-8 of side. The probe also stopped the first kick of 864 (seed 138) after 2 tries in 135 s, with no find. The depth kick of the same 864 bytes (seed 3964) made its first find at 117 s, on try 2, and its 1.908e-5 of side by 289 s. So the seed paid there, not the time. The paying 494 seed made its first find at 324 s, where a 120 s probe would have stopped it. Our kick of the backlog 812 take found 1.77e-8 of side. The walk refused it. It is a public-first row, and its share against the 1105 row is 0.543 at 1e-2. The other six depth kicks (333, 367, 803, 854, 965 and 973) moved 1.5e-9 of side or less, which is the polish of the certify dilation. The 464 kick moved 5.470e-4 of side, but another lane had put 464 lower while it ran, so it ended 4.5e-5 above the live bar.

The LP follow (`lpfeed.py`) queued 134 take csv files of other lanes and no near file. The LP gained nothing on 126 of them. Its largest move was 5.4e-9 of side (the backlog 864), the only LP row. The walk refused 40 outputs from 25 files (backlog 421 eight times, 548 of three lanes). None of those outputs had an LP gain, so the refusals cost no row. The log does not record the reason for a refusal.

#### Not run yet

- Kick held rows for the full 900 s with no probe, largest board gap first, and give each row two seeds. Measured: 73 probed held kicks used 9,907 s and gave no row. 9 kicks of held rows with no probe used 8,277 s and gave 2 n. In both n an earlier kick found nothing: a full 900 s seed of 494, and a 135 s probe of 864. Another seed then found 1.667e-4 of side on 494 (first find at 324 s) and 1.908e-5 on 864 (at 117 s).
- Chain a leg from every find that moves more than 1e-5 of side, and stop the chain after a leg that moves less than 2e-6. Measured: the 494 leg found 1.577e-4 of side more, and the 864 legs found 1.044e-5 and then 1.224e-6. After that, 3 more legs (2 of 494, 1 of 864) found nothing.
- Stop the LP follow of fresh takes of other lanes, and give its worker slot to depth kicks. Measured: 134 inputs, 126 with no LP gain, one row 2.0e-10 below the backlog 864.
- Log the reason for each walk refusal. Measured: 40 refusals from 25 files, no reason recorded.

### Round 32: two unprobed seeds per held row (2026-11-16)

**Result: 1 row, 405, 1.858e-9 of score below bar32. Two more finds (864 and 910) went to the follow lanes. Their rows now sit 1.420e-5 and 2.723e-6 below bar32.**

The bar for each n is `round32-briefs/bar32.tsv`, the submitted round 31 b file. A row of a file we submitted is our own layout, so a kick of a held row gets no share test.

#### Tool changes and controls

The round 32 tools are in `tools/border/r32`. They are the round 31 tools with these changes:

- `build_held32.py` writes each row of the round 31 b file to `held32/<n>.csv`. For each n it also counts the 900 s kick lines of round 31 that name it. A row that round 31 b changed counts 0, because those kicks ran on older bytes.
- `deepfeed32.py` feeds both boxC workers. It takes the held rows with a board gap of 1e-5 of score or more. It leaves out a side fraction that 3 or more n share. Rows with no unprobed round 31 kick come first, then the largest board gap. It skips an n that another lane named on a kick or claim line in the last hour. It also skips an n where a live round 32 take is below the held side.
- `kfeed32.py` runs every kick for 900 s with no probe. A first seed that finds nothing, or less than 1e-6 of side, gives the row a second seed. A first find of more than 1e-5 of side gets a leg. A leg gets the next leg only when it moved 2e-6 of side or more.
- Each find gets a default-flag fq beside the polish fq. `sfeed32.py` runs both kinds of fq on our take rows each time a row changes. The reason: the quench fq loop (default flags, then polish) of our 864 find went 1.68e-6 of score below our polish-only fq.
- The fq jobs of a find now go to boxC before its second seed or its leg. The worker that ends the kick then runs the fq first. Before this change, the 405 fq waited 13 minutes behind the second seed.
- A refusal now logs its reason (`provenance.last_reason`).

The controls printed these results:

- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 74.0 s. Rounds 27 to 31 reached the same endpoint.
- Held 902 scaled by 1 + 2e-6, kicked for 150 s with no probe: the kick ran its full 151 s (87 tries). It found 5.907e-5 of side below its start, and the chain rule chose a leg. The control flag stopped the leg.
- The walk passes the held 692 row. It refuses a copy whose record names the 1105 file, and it logs the reason "forbidden ancestry CC BY-SA".

#### What ran

`kfeed32.py` finished 40 kicks on the two boxC workers from 11:30 to 16:56 UTC:

| kind | kicks | seconds | moved more than 1e-6 of side |
|---|---|---|---|
| first seed of a held row | 19 | 17,839 | 0 |
| second seed of a held row | 18 | 16,407 | 2 (864, 910) |
| chain leg | 3 | 2,783 | 1 (864 leg 1) |

The rows kicked, in order: 692 746 864 910 643 341 926 863 695 686 859 989 405 812 416 634 912 588 936. Each got two seeds, except 936, which got one before the 16:40 UTC stop. The first seed of 405 found 3.781e-8 of side. No other first seed found anything below its start.

What each find became:

| n | find | what happened |
|---|---|---|
| 864 | seed 2: 4.090e-5 of side. Leg 1: 3.764e-4 more. Leg 2: nothing | Our polish-fq row (1.391e-6 below bar32) lasted 46 s. The quench fq loop of the same certified find went 1.68e-6 lower. Leg 1 certified 1.43e-5 below bar32. When our fq ended, backlog's 180 s lkick of the same chain file was already 1.5e-9 lower, so the driver closed our fq. Backlog holds 864 at 1.420e-5 below bar32. |
| 910 | seed 2: 1.138e-5 of side. Leg 1: nothing | Backlog's legs of our find hold 910 at 2.723e-6 below bar32. |
| 405 | seed 1: 3.781e-8 of side. Seed 2: nothing | Our row, 1.858e-9 below bar32. The default fq gained 8.6e-14 and the self follow gained nothing. |

The k123 864 row names our pinned 864 start. k123 then joined an 864 band into 808 (recipe `808-864r`) and went on to 866.

In round 31, 9 unprobed kicks of held rows gave 2 n. In round 32, 37 seeds gave 3 finds. All 19 kicked rows were rows that round 31 b changed, because the feeder ranked them first. The unchanged rows with no unprobed round 31 kick got no seed.

#### Not run yet

- Give the two unprobed seeds only to held rows that no lane kicked without a probe in rounds 31 and 32. Measured: 37 seeds gave 3 finds (864, 910, 405). 15 rows with two dry seeds each are now spent: 692 746 643 341 926 863 695 686 859 989 812 416 634 912 588.
- Run the fq loop (default flags, then polish, up to three rounds) on each find before it is published. Measured: a polish-only fq left 1.68e-6 of score on the 864 find, which the quench loop took.
- Keep handing finds to the follow lanes, and keep our legs on the chain file. Measured: quench copied the 864 and 910 finds from our leg claim lines within 2 minutes, and backlog kicked them too. Both rows reached the team file through them. Our 864 leg 1 then gave 3.764e-4 of side more on the same chain.

### Round 33: two unprobed seeds on held rows nobody kicked, with the fq loop before publishing (2026-11-16)

**Result: 1 row, 998, 2.647e-7 of score below bar33. A second find (753, 5.480e-4 of side, 1.997e-5 of score) went to backlog, which holds 753 2.65e-7 lower.**

The bar for each n is `round33-briefs/bar33.tsv`, the submitted round 32 a file. A row of a file we submitted is our own layout, so a kick of a held row gets no share test.

#### Tool changes and controls

The round 33 tools are in `tools/border/r33`. They are the round 32 tools with these changes:

- `build_held33.py` writes each row of the round 32 a file to `held33/<n>.csv`. A row is a candidate only when no 900 s kick or claim line of round 31 or round 32 without a probe names its n. It also leaves out the 15 rows with two dry seeds in round 32. Side fractions that 3 or more n share stay out, and so does every 45-degree lattice row. A lattice row is a row where every tilted square sits at exactly 45 degrees. The largest board gap comes first, and changed and unchanged rows rank together. This left 32 rows with a board gap of 1e-5 of score or more.
- `deepfeed33.py` also skips an n that another lane claimed for 900 s at any time in round 33.
- One boxC job now runs the full fq loop on the certified file of each find (`worker.py`, a final job with `loop`). The loop runs default flags, then the polish flags, for up to three rounds. It goes on while a round gains 3e-9 of side, as `midm_fqonce.py` does. Only the end of the loop is published. The self follow runs the same loop.

The loop control (`boxC/ctl_loop.py`, the same loop code on `control-870`) printed these sides in 507 s:

| step | side |
|---|---|
| round 1, default flags | 30.91388209074235 |
| round 1, polish | 30.91388171220834 |
| round 2, default flags | 30.901495455086522 |
| round 2, polish | 30.901495002529867 |
| round 3, default flags | 30.90150243510765 |
| round 3, polish | 30.901494995827413 |

The first step is the plain fq endpoint of rounds 27 to 32. The loop ended 1.29e-2 of side below it.

#### What ran

The two boxC workers finished 33 kicks of 900 s with no probe from 18:36 to 23:35 UTC:

| kind | kicks | seconds | moved more than 1e-6 of side |
|---|---|---|---|
| first seed of a held row | 15 | 13,796 | 0 |
| second seed of a held row | 15 | 13,674 | 2 (753, 998) |
| leg of the 753 find | 1 | 917 | 0 |
| leg of our 998 row, two seeds | 2 | 1,805 | 0 |

The rows kicked, in order: 371 759 998 537 808 907 457 753 735 801 492 508 927 455 932. Each got two seeds. Seven first seeds and three second seeds only polished about 1e-9 of side, which is under the 1e-10 rule of score.

What each find became:

| n | find | what happened |
|---|---|---|
| 753 | seed 2: 5.480e-4 of side (3 finds in 21 tries). Leg 1: nothing | Our row certified 1.997e-5 below bar33 at 20:45 UTC. In the loop, the default flags went 1.7e-5 of side higher and the polish kept the input. Backlog's follow went 2.65e-7 lower at 21:50 UTC. |
| 998 | seed 2: 8.363e-6 of side. Two legs of the row: nothing | Our row, 2.647e-7 below bar33. In the loop, the default flags went 5.0e-5 of side higher and the polish kept the input. |

Both finds came on a second seed after a dry first seed, as in rounds 31 and 32.

The pool ran out at 22:53 UTC. Another lane claimed each of the other 17 candidates for 900 s in round 33, most of them through the shared deep-kick queue of 21:46 UTC. These are 871 742 979 414 701 869 983 543 985 339 504 589 501 407 463 488 594. Both workers sat idle for 27 and 42 minutes before we saw it. Then they ran the two legs of our 998 row.

#### Not run yet

- Keep two unprobed seeds per held row and give the rows to one lane only. Measured: 30 seeds on 15 rows gave 2 finds, both on the second seed (753 5.480e-4 and 998 8.363e-6 of side). Another lane's 900 s claims took the last 17 rows of our list.
- Keep the fq loop before publishing. Measured: on both finds the default flags went higher and the polish kept the input, so the loop took under a minute on each. On the control it went 1.29e-2 of side below a single fq.
- Give the feeder a second list when the first runs dry. Measured: both workers sat idle for 27 and 42 minutes after the pool ran out at 22:53 UTC.

### Round 34: deep kicks of class n mod 4 = 0, screened since the current geometry (2026-11-17)

**Result: no row in our take. One find: 640, 8.789e-5 of side, certified 3.474e-6 of score below bar34. Backlog's 180 s follow of it went 7.25e-7 lower and holds 640.**

The bar for each n is `round34-briefs/bar34.tsv`, the submitted round 33 a file. Every deep kick list now has one owner per row, by n mod 4. Border owns n mod 4 = 0.

#### Tool changes and controls

The round 34 tools are in `tools/border/r34`. They are the round 33 tools with these changes:

- `build_held34.py` finds the current geometry of each row. That is the first round from which every bar file up to bar34 holds the same score for n. It counts the kick claims of all lanes since that round. A claim counts when it names the n and a 900 s kick, and carries no probe of 1 s or more. Of the 250 rows of our class, 146 are closed-form sides and 12 are lattice rows. List 1 holds 32 rows with a board gap of 1e-5 of score or more and fewer than two such claims, largest gap first. List 2 holds 30 rows for idle slots: two rows of smaller gap, then third seeds.
- `kfeed34.py` posts each claim, waits 5 s and reads the log again. It starts the kick only if no other lane claimed that n in the 1200 s before. It also stops a running kick when another lane holds a row more than 1e-6 of score lower at that n. Every 4 minutes it checks one worker per slot on boxC and restarts a dead one.
- `deepfeed34.py` closes a held row for another lane's 900 s claim only when the claim names that row. It reads `handed.json` for rows given to another lane.

Controls, both able to fail:

- Claim check on a scratch log: a claim of another lane 0 s earlier refused the start and wrote a release line. A claim 3000 s earlier and no claim both let it start.
- Stop file: a 300 s control kick of held 100 got its stop file at about 40 s and ended as `superseded-stop 55 s`.

#### What ran

The two boxC workers ran 40 kicks of 900 s with no probe from 01:33 to 06:58 UTC, 36,695 s in all:

| kind | kicks | moved more than 1e-6 of side |
|---|---|---|
| first seed of a row with no deep kick since its geometry | 11 | 0 |
| second seed of the same rows | 10 | 0 |
| one seed of a row that had one deep kick (its second) | 15 | 1 (640) |
| third seed (list 2: 908 804 748) | 3 | 0 |
| leg of the 640 find | 1 | 0 (7.05e-7) |

Twelve kicks only polished about 1e-9 of side, which is under the 1e-10 rule of score.

The 640 find came on the second deep kick of the row, as 753 and 998 did in round 33. The fq loop took 4 s: the default flags went 1.0e-4 of side higher and the polish kept the input. Backlog claimed the follow 10 minutes after our line and certified 7.25e-7 lower 14 minutes later. Our leg moved 7.05e-7 of side and ended 6.97e-7 of score above backlog's row.

Two mistakes cost slots:

- `deepfeed34.py` first closed a held row for any 900 s claim of its n. Invent's claims of fresh joins at 448 and 492 kept both held rows out of our queue until 04:12 UTC.
- The feeder and the second seed of 904 both sent a job to worker 2 within 17 s, so worker 2 ran two jobs in a row. No slot sat idle.

Classfill offered its idle slots, so we gave it the last 10 rows of list 1. It claimed 380 984 704 928 968, and 928 gave it a take row. We took back 632 604 464 652 548 at 06:30 UTC, and 632 and 604 got a first seed each. Both were dry.

Rows of list 1 that ran: 904 860 864 376 736 640 752 644 372 448 540 920 988 876 856 800 936 992 264 812 556 412 632 604. Rows that got no deep kick: 464 652 548 and the second seeds of 632 and 604.

#### Not run yet

- Run 464 652 548 first, two seeds each, then the second seeds of 632 and 604. Measured: these are the rows of our class left with fewer than two deep kicks since their geometry.
- Rank rows that had one deep kick before rows with none. Measured: the second deep kick of a row paid in 1 of 25 tries here (640). It also gave both rows of round 33, while 11 first seeds gave nothing here.
- Stop third seeds of rows with two dry deep kicks. Measured: 3 of 3 gave nothing here.
- Close a held row only for a claim that names its bytes. Measured: claims of fresh joins at 448 and 492 kept two held rows idle for an hour and a half.

### Round 35: deep kicks of class n mod 4 = 0, then k123 near donors ranked by board room (2026-11-17)

**Result: one row in our take, 803, 3.715e-4 of score below bar35. Its start was a k123 near donor 2.37e-4 above the bar. Our class 0 deep kicks gave one find, 808 (4.934e-6 below bar35). Backlog's follow of it went 1.455e-6 lower and holds 808.**

The bar for each n is `round35-briefs/bar35.tsv`, the submitted round 34 a file. Border owns the deep kicks of n mod 4 = 0.

#### Tool changes and controls

The round 35 tools are in `tools/border/r35`. They are the round 34 tools with these changes:

- `build_held35.py` no longer counts a hand-off line as a kick. In round 34 it counted our own hand lines of 464, 652, 548, 604 and 632, so 464, 652 and 548 looked kicked once. It now counts each seed of a claim line that names two seeds, as classfill writes them.
- `kfeed35.py` stops a running kick only when a live row is 1e-6 of score below the lower of its start and the bar. The old rule compared the start with the live row. A k123 near donor starts above the bar, so the old rule stopped 489 and 199 at once. Control: a near donor with the live row at the bar does not stop. A near donor with a row 2e-6 below the bar stops. A held start with a row 2e-6 below stops, and a held start alone does not.
- The deep feeder gave 604 seed 7628 again, the seed round 34 had run on the same bytes. We stopped it after 30 s and ran seed 5113.

#### What ran

After the count fix, the class 0 list held 7 rows. First came the second seed of 604 and two seeds each of 464, 652 and 548. Then came the rows whose geometry changed in the round 34 a file: 640, 808 and 928. Quench then listed rows that the closed-form screen skips, and we took back 852 and 1000. We added 292.

| kind | kicks | result |
|---|---|---|
| second seed of 604 | 1 | dry |
| two seeds of 464, 652, 548 | 6 | dry |
| first seed of 808 (changed in round 34 a) | 1 | 1.403e-4 of side, 4.934e-6 of score below bar35 |
| two seeds of 640 and 928 (changed in round 34 a) | 4 | dry |
| leg 1 and a second seed on the 808 find | 2 | dry |
| closed-form rows 852 and 292 (two seeds), 1000 (one) | 5 | dry (1000 polished 2.7e-11 of score) |

Backlog's 180 s follow of our 808 went 1.455e-6 of score lower 47 minutes later, so backlog holds 808.

At 14:18 UTC the main session gave our idle slots to the k123 near/ donors, closest to the bar first. The first two runs showed that closeness is the wrong order. 803 started 2.37e-4 of score above the bar, moved 1.723e-2 of side on its first seed and certified 3.713e-4 of score below the bar. The board's 803 is still 2.2e-3 of side lower. 789 moved 4.665e-3 of side from 2.15e-4 above. The donor next in closeness, 489, has no room: the board sits at bar35 there. So we ranked the pool by room: the board gap of bar35 minus the donor's gap above the bar.

| donor (k123 r35 near/) | room, score | above bar35 at start | what ran | result |
|---|---|---|---|---|
| 803 prejoin31 bc086790 | 2.1e-4 | 2.37e-4 | seed 4133, then legs 1 and 2 | seed: 1.723e-2 of side, certified 3.713e-4 below bar35. Leg 1: 5.3e-6 of side more. Leg 2 dry |
| 789 threeway28 a50c0c4a | 2.1e-5 | 2.15e-4 | seed 3979, then a leg from its find | seed: 4.665e-3 of side, still 4.85e-5 above. Leg dry. A second leg seed was cut by the deadline |
| 804 threeway28 b833ca27 | 7.2e-5 | 4.69e-4 | two seeds | first dry. Second 1.6e-5 of side, still above |
| 908 threeway28 da2b4c4a | 2.5e-4 | 5.42e-4 | two seeds | dry |
| 489 threeway28 ece16ed7 | -1.9e-6 | 1.92e-6 | stopped after 15 min | no room: the board sits at bar35 |
| 199 threeway28 fc19aad3 | -1.25e-4 | 2.30e-4 | stopped after 15 min | no room |

862 went to backlog first. We skipped 965 and 491 because other lanes already ran other k123 donors at those n. 630 we dropped: twoshort ran a 630 donor only 2.8e-7 above the bar.

Two faults cost slot time. The old stop rule stopped 489 and 199 at once. Worker 1 then sat idle from 14:58 to 15:30 UTC. The cause: 862 lost its claim, the 789 leg had no ancestry sidecar, and we had put 908 and 804 both on worker 2.

#### Not run yet

- Run the k123 near/ donors by room, largest first, two seeds each, then a leg from any find that moves 1e-3 of side or more. Measured: 803 (room 2.1e-4) gave 3.715e-4 of score, more than every class 0 deep kick of rounds 34 and 35 together. 789 moved 4.665e-3 of side. The donors closest to the bar (489, 199) had no room at all.
- Give a leg to a find that is still above the bar when it moved far, with the board below. The kick chain rule gives no leg to a find 1e-5 or more above the bar, so we queued the 789 leg by hand. It was dry, but 803's legs added 1.9e-7.
- Stop deep kicks of class 0 held rows with two dry seeds since their geometry, and of closed-form rows. Measured: 22 held-row kicks this round gave one find (808). Quench measured 0 of 10 on closed-form rows.
- Write every hand-queued job's sidecar before it goes to the queue, and spread the jobs over both workers. Measured: a refused leg and a lost claim left worker 1 idle for 32 minutes.

### Round 36: k123 near donors ranked by board room, two seeds each, legs on big moves (2026-11-17)

**Result: no row in our take. One find went below the bar: 698, 3.696e-5 of score below bar36. Backlog's 180 s follow of our certified 698 went 7.9e-8 lower, so backlog holds 698.**

The bar for each n is `round36-briefs/bar36.tsv`, the submitted round 35 a file. Held-row deep kicks follow rule 6d (one seed), with no n mod 4 ownership.

#### Tool changes and controls

The round 36 tools are in `tools/border/r36`. They are the round 35 tools with these changes:

- `kfeed36.py` runs one feeder per box: boxC workers 1 and 2, boxE worker 3, boxA workers 4 and 5.
- A first find that moves 1e-3 of side or more now gets a leg, even when it stays above the bar.
- Reseeds vary by round. The round 34 formula gave 604 the same seed twice.
- Remote worker restarts run through `sh -s`. In round 35 zsh stopped the command on a glob that matched nothing.
- `dfeed36.py` feeds every slot from `rank36.py`. The rank is the board gap of bar36 minus the donor's gap above bar36. It gives two unprobed 900 s seeds per donor and one donor per n in flight.
- At 21:02 UTC `rank36.py` began to read every take-*-r35 and r36 near/ dir. By 20:50 UTC the k123 pool held only donors with room near 1e-6. Donors less than 1e-8 of score above bar36 are now skipped. A donor within 1e-10 of score of one already queued at its n counts as the same geometry.
- At 22:13 UTC `dfeed36.py` began to put band donors first: 5e-6 to 3e-4 of score above bar36, with room 1e-4 or more.
- Stop-rule control (lesson 6i), on the four cases. A donor above the bar with the live row at the bar: no stop. A donor with a live row 2e-6 below the bar: stop. A held start with a live row 2e-6 below: stop. A held start alone: no stop. All four passed.

#### What ran

The feeders queued 59 kicks, 4 second seeds and 15 legs on 33 n, from 18:10 to 23:22 UTC. 77 kicks finished, and 50 of them gave a find below their start.

| what | count | result |
|---|---|---|
| finds that moved 1e-3 of side or more | 8 | 698 went 7.495e-4 of side below bar36. Six (372, 644, 687, 537, 448, 330) landed within 3e-9 of side of the bar36 geometry. 790 stayed 3.0e-4 above. |
| legs from those finds | 15 | 698 leg 1 moved 2.262e-4 more, leg 2 moved 8.1e-7 more. The other legs were dry. |
| donors within 1e-6 of score of bar36 | 12 | all fell back to the bar36 geometry (-4e-10 to -9e-10 of side, under the 1e-10 score rule) |
| band donors (5e-6 to 3e-4 above, room 1e-4 or more) after 22:13 UTC | 14 | 789 moved 7.1e-4 and 4.9e-4 of side, 904 moved 7.8e-4. All ended at or above the bar. |

The 698 chain: the k123 donor fdfcf4df (3.38e-5 of score above bar36, room 3.26e-4) moved 1.642e-3 of side on seed 8856. It certified 2.837e-5 below bar36. Two legs and the fq loop took it to 3.696e-5 below. Its uncapped walk was clean (7355 files). Backlog's follow overtook it at 19:39 UTC.

The walker hit its cap of 3000 files on many forensics, invent and classfill near/ donors. We skipped four donors on their walk: 591 4ddf691a, 372 81bbbac9, 372 2fab03c8 and 925 1383e5e9. The 591 and 372 walks reached gone take dirs, but only through walk reports in take-forensics-r35/work/walks/. Lesson 6h says the walker reads such reports as ancestry, so these three may be false refusals. The 925 walk reached a public-first file with a 1105 share of 1.0.

#### Not run yet

- Stop kicking near donors that fall back to the held geometry of their n. Measured: six of eight big movers and all twelve donors within 1e-6 fell back to the bar36 geometry within 3e-9 of side. Only 698 broke out.
- Give the rectangle composer and the follows a share of every fresh certified row at once, and keep our own 180 s follow on it. Measured: backlog's 180 s follow of our 698 went 7.9e-8 lower within 20 minutes and took the row.
- Rank donors by room and by their distance from the bar36 geometry in layout space. Measured: a donor that moves far but lands back on the held geometry gives nothing. 698's donor was 3.38e-5 above with a different layout, and it paid.
- Rewalk the 591 and 372 donors skipped above with the walk reports left out. Measured: each refusal named a gone take dir only through a take-forensics-r35 walk report.

### Round 37: fresh rows first, then low-share donors under rule 6c (2026-11-18)

**Result: no row in our take. No find of ours went below bar37 by more than the 1e-10 rule.**

The bar for each n is `round37-briefs/bar37.tsv`, the held round 36 b file. The work ran from 01:55 to 06:10 UTC on six slots. boxC ran workers 1 and 2, boxE worker 3, and boxB workers 4 and 5. One boxA slot ran the 180 s follows.

#### Tool changes and controls

The round 37 tools are in `tools/border/r37`. They are the round 36 tools with these changes:

- `worker.py` runs `invent_rest.py lkick` for a job with tool `invent_rest`. This is backlog's 180 s follow. Control: a 40 s run on the held 698 made 3 tries and wrote its trace. It found nothing, as expected on a held row.
- `driver.py` queues our own 180 s follow of each certified row. It posts the claim before the certified line.
- `dfeed37.py` was rewritten. Fresh rows of other lanes come first: a 180 s follow, then the first 900 s seed. Donors follow rule 6c. Each needs a held share at 1e-3 under 0.5 (`heldshare37.py`, against the round 36 b row). It also needs room above 0 and no seed on its sha in rounds 34 to 37. It allows one geometry per score band of 2e-8, at most two donors per n, and no donor at an n where one fell back. The rank is room times one minus the share. Idle slots take rule 6d held rows.
- `kfeed37.py` gives no leg from an endpoint at the live bar (brief 6u). A fresh row's claim check counts only claims made after the row appeared.
- `rewalk37.py` walks with no file cap and does not follow `work/walks/*.json`.
- Stop-rule control on six cases, the four of the brief among them: all passed (`stop-control.txt`).

#### What ran

| what | count | result |
|---|---|---|
| fresh rows of other lanes (683, 793) | 2 follows, 2 seeds | The producer or backlog, quench or forensics claimed every follow and first seed within 1 to 8 minutes. Our two 793 seeds lost their claims. Our two 793 follows ran (one was a restart duplicate) and were dry. |
| donors under rule 6c | 34 queued, 3 refused by the walk at the kick | 698 moved 2.4e-4 of side, 862 2.2e-3, 692 1.1e-3, 919 1.1e-3, 746 7.1e-4, 864 7.4e-4, 634 6.8e-4. All stayed 2.4e-4 to 3.6e-3 of side above the bar. 367 moved 1.3e-3 and 591 and 642 moved less. All three fell back to the held geometry. 687 (two donors) ended 2.7e-8 and 3.0e-8 of side above the bar. |
| held rows under rule 6d (29 listed, 11 run) | 11 | 9 dry. 552 and 496 ended at the bar (-6.7e-10 and -6.4e-10 of side). |
| legs | 5 | dry or at the bar. We stopped the 367 leg at the bar by hand. |

We rewalked the three round 36 refusals with walk reports left out. All three were clean and uncapped: 591 4ddf691a (7740 files), 372 81bbbac9 (7753) and 372 2fab03c8 (7750). 372 81bbbac9 has a held share of 0.519, so rule 6c drops it. 372 2fab03c8 (share 0.360) sits 4.4e-7 of score above the bar, and our near-bar rule wants a share under 0.3. 591 4ddf691a (share 0.225) did not run, because a 591 donor of round 36 ran first and fell back.

At 04:15 UTC every slot was idle. The round 36 and 37 donor pool under rule 6c and the 29 held rows were spent. Then the rank read the near/ dirs of rounds 34 to 37: 241 donors had a share under 0.5 and no seed on their sha.

#### Not run yet

- Give each fresh row to one lane only. Measured: the producer and three follow lanes claimed every follow and first seed of 683 and 793 within 1 to 8 minutes. Our two seeds lost their claims.
- Stop donor kicks at n where an earlier donor found the same endpoint. Measured: 634 4ab52542 ended at 25.68843844046 of side, the endpoint of the round 36 634 donor bf28a025.
- Skip k123 threeway28 and invent fresh donors that sit within 1e-6 of the bar. Measured: 687 (two donors) ended 3e-8 of side above the bar, and 642 fell back.
- Treat a relative path in a fresh row's take.tsv cell as a fault of the producer, not a refusal. Measured: every 683 descendant failed our walk on `harvest/near/683-public34-...csv`. Quench named that file by a path relative to its own dir.
