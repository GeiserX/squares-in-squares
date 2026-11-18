# Avenue: midm (2026-11-12, round 17)

**Result: 52 n certified below the held score, for 1.047e-03 of score. 5 of them are in the slice, for 9.649e-05. Against round 16 and the files of the other lanes of round 17, the take stands on 41 n, for 3.804e-04 of score. The idea of the round is dead: no search here reaches another arrangement at n under 440. Every gain comes from a small kick before the fq quench, on a layout that no kick had touched.**

<!-- r19:head -->
**Round 19 (2026-11-12, 20:15Z to 22:35Z), in [section 10](#10-round-19-2026-11-12): 16 n certified below the round 17 file, for 3.460e-03 of score. Below every frozen take of round 17 and every other take of round 19 the take stands on 14 n, for 1.279e-03 of score. Each is a kick of another lane's new file. Most of the gain is in the slice n 257 to 440. There the k123 and rigidsoft lanes wrote new layouts with a seam join and a band move. One kick scan took 1e-5 to 5e-4 of score more on each. The slice also got four construction lists of our own, each with its kill line and control. None gave a layout below its bar.**

<!-- /r19:head -->

The slice is n = 257 to 440 (m = 16 to 20). The held file (`gather/round15-2026-11-12a.csv`, public 22.1672602051) trails the per-puzzle board there on 67 n, by 0.0169 of score in all. The engines of the lane (sqpack, FTMC, winlns, the fq quench, the soft-box search) were measured mostly at n of 498 and above. This avenue measured a wide search with those engines at the small end. All CPU was boxE, at most 4 processes, between 13:26Z and 19:50Z.

Words used here: a "try" is one start squeezed once by one engine. A "kick" moves every square by a random step (sigma 0.003 to 0.04, and 20 times that in degrees) before the fq quench. "Soft-free" means the overlap energy of a layout is below `1e-10 · n` in a box under its legal side, as in [methods](methods.md).

## 1. Kill line (written 2026-11-12 13:26Z, before the first long run)

**The idea.** For each trailing n the search starts from a layout that is not the held one. The starts are of four kinds:

- the held n+1 with one square removed
- the held n+2 with two squares removed
- the held n-1 with one square inserted
- the held n with a kick

An engine then squeezes the start. A result counts when it certifies below the held score.

**The tool control.** It must be green before any count is read. The driver rebuilds a side we hold. The held 370 with a kick must come back to its own side within 1e-6. A driver that reads or writes a layout wrongly fails this.

**The idea's control.** On 2026-11-12 public files took five sides of the slice down: 403, 410, 411 and 412 (jonathan1506, round 13) and 370 (jazivxt, round 15). The control gives the search the file we held before those rounds: `round12-2026-11-12a.csv`, and `round14-2026-11-12a.csv` for 370. It counts two things per engine and kind of start: the tries that end below the side we held then, and the tries that reach the public side.

**The kill line.** The idea cannot pay when both of these hold:

1. On the control, no engine gets below the old held side on any control n in at least 1,000 tries per n.
2. On the 20 n of the slice with the largest gap, at least 400 tries per n give no result that certifies below the held score.

If line 1 holds alone, the search cannot find a better layout that we know exists. The slice run is then cut to the 20 n of line 2.

## 2. The controls

**Tool control, green.** `midm_scan.py` gave the held 370 six kicks. Four came back to 19.7567472, and the held side is 19.756747264. One ended 1e-8 above it and one ended below it (section 5).

**The idea's control, red for every engine.** The starts are the layouts we held before the public finds. No try got below the old held side.

| n | old held side | public side | fq, removed and inserted squares (`midm_scan.py`) | fq kick | seeded soft island, 150 s (`midm_soft.py`) | sqpack, 3 × 100 s | FTMC, 150 s |
|---|---|---|---|---|---|---|---|
| 410 | 20.772126646 | 20.764282967 | 0 of 119 | 0 of 39 | 920 seeds, 76,440 children, 0 finds | 0 of 3 | 0 (49 steps) |
| 403 | 20.571428572 | 20.564935731 | 0 of 128 | 0 of 42 | 920 seeds, 74,086 children, 0 finds | not run | not run |
| 411 | 20.786944253 | 20.776303384 | 0 of 60 | 0 of 20 | 920 seeds, 75,353 children, 0 finds | not run | not run |
| 370 | 19.757499204 | 19.756747264 | 0 of 134 | 0 of 44 | 863 seeds, 80,909 children, 0 finds | 0 of 3 | 0 (46 steps) |

What the counts hide:

- **A layout with a square removed stays jammed at its own side.** The old 411 minus one square had 40 fq quenches. All ended within 4e-5 of the side of 411 (20.786944). That is 0.0148 above the old 410. The same holds for 403, 411 and 370: the lowest result of each is the side of the donor. A hole frees one chain of squares, and many chains carry the side.
- **An inserted square costs a whole column.** The best result of n-1 plus one square is 0.07 to 0.14 above the held side. Many tries end at the plain grid.
- **The soft island never comes near soft-free.** The seeds start at an energy of 5e-5 to 7e-4 in a box 2e-4 under the old held side. The island brings that down by half in 150 s and stalls. Soft-free is 4e-8 there.
- **The kick lands in two basins on the old 410.** 14 of 39 kicks came back to the old side and 24 ended 5.6e-5 above it.
- sqpack with `--local` wrote no result (no new record). Its drop and grow starts ended 0.017 and 0.23 above the held side. FTMC made 46 and 49 steps in 150 s and kept its start.
- fq with `--shrink --hops 30` takes 17 to 36 s a try. Its 6 tries (old 410, 403 and 370) all ended at the held side, and the mode was left out of the scan.

The fq counts are 60 to 178 tries per n, not 1,000. Each fq try takes 0.7 to 3 s, and every result fell on the donor's own side, so more tries of the same kind add nothing. The soft island gives each n about 900 seeds and 75,000 children. Line 1 of the kill line holds in that sense: no engine finds a better layout that we know exists.

## 3. The slice: the 20 n with the largest gap

`midm_soft.py`, kinds `drop1,drop2,grow1`, 75 s of island per n after the seeds, box 2e-4 under the held side. The seeds are every square of n+1 in turn (400 at most), 400 pairs of n+2 and 120 holes of n-1.

| n | children | lowest seed energy | energy at the end | finds |
|---|---|---|---|---|
| 262 | 41,087 | 4.2e-4 | 3.5e-4 | 0 |
| 263 | 46,819 | 1.7e-3 | 1.1e-3 | 0 |
| 295 | 38,664 | 2.0e-5 | 1.7e-5 | 0 |
| 299 | 41,247 | 9.6e-4 | 6.8e-4 | 0 |
| 303 | 35,321 | 2.4e-4 | 1.8e-4 | 0 |
| 328 | 33,358 | 2.3e-3 | 1.7e-3 | 0 |
| 329 | 27,449 | 2.0e-3 | 1.7e-3 | 0 |
| 330 | 38,872 | 4.8e-4 | 3.7e-4 | 0 |
| 333 | 42,832 | 1.9e-4 | 8.6e-5 | 0 |
| 339 | 37,141 | 3.8e-4 | 2.9e-4 | 0 |
| 340 | 34,109 | 5.2e-5 | 9.4e-6 | 0 |
| 365 | 34,341 | 2.4e-3 | 1.8e-3 | 0 |
| 366 | 24,750 | 2.3e-3 | 1.5e-3 | 0 |
| 367 | 24,201 | 1.2e-11 | 5.3e-8 | 0 |
| 371 | 36,591 | 2.3e-4 | 1.4e-4 | 0 |
| 377 | 29,448 | 4.5e-4 | 1.4e-4 | 0 |
| 379 | 36,611 | 5.5e-4 | 1.6e-4 | 0 |
| 401 | 31,277 | 8.0e-8 | 5.4e-8 | 0 |
| 413 | 28,223 | 2.7e-4 | 1.8e-5 | 0 |
| 416 | 33,494 | 9.1e-5 | 6.6e-5 | 0 |

**0 finds on 20 n.** On 18 n the energy at the end is 200 to 50,000 times above soft-free (3e-8 to 4e-8). 367 and 401 are the two n where n+1 has the same side. Their seed is the held layout itself with the overlap the tolerance allows: its energy is at soft-free, and it does not become legal below the held side.

The plain soft-box island with its own drop start ran on three n (`methods_soft.py --start drop1`, 120 s each). 367 made 38,046 children and 12 restarts. 328 made 51,772 and 17. 365 made about 48,000. None found.

Line 2 of the kill line holds. **The idea is dead at this size.** Take a layout of a neighbour n and remove or insert squares. From that start fq, the soft island, sqpack and FTMC do not reach a layout below the held side.

One fault of the first runs: the energy of a first relaxation counts only the pairs that were near at its start. A seed that moved far (an inserted square) read too low, and the island's own count then went wrong for that member. 262 and 339 had such a seed in front. `midm_soft.py` now settles the lowest seeds and counts them afresh. The two n ran again, and the table holds the second run: no find on either.

## 4. Three more starts, all measured dry

**A shell removed from the same k one shell up** (`midm_soft.py --kinds peel,jog`). We trail at some (m, k). There the board's side fraction lies between ours at (m+1, k) and ours at (m, k). So the layout of n + 2m + 1 with one row and one column cut out looked like the board's layout. The cut removes a strip of width 1 across the box and a strip at right angles to it. The second strip may stand at two places, one on each side of the first strip. It then passes beside two tilted patches. Only cuts that remove the right count and at most two tilted squares are kept.

- Tool control, green: 330 from 367 (the same side fraction, 0.69239). The best cuts settle at an energy of 6.9e-8, the energy of the held 330 itself in that box (6.6e-8). Every other cut is 4 orders higher.
- The five largest gaps with a donor: the cut layout becomes soft-free only far above the held side.

| n | donor | held side | energy at the held side | soft-free at |
|---|---|---|---|---|
| 365 | 404 | 19.612856 | 3.3e-4 | +0.04 to +0.08 |
| 367 | 406 | 19.692388 | 1.5e-3 | +0.04 to +0.08 |
| 328 | 365 | 18.614369 | 1.0e-2 | +0.16 to +0.32 |
| 366 | 405 | 19.656854 | 6.1e-3 | +0.04 to +0.08 |
| 333 | 370 | 18.772634 | 6.3e-3 | +0.04 to +0.08 |

So a shell cut out of the layout one shell up is 0.04 or more of side short. The layouts of this size are not two arms on two walls. 404 holds two tilted patches at 40.8 degrees. 406 and 367 hold one block at 45 degrees. 365 holds 174 tilted squares in one band. The border lane's corner window is the rigid form of the same step.

**Two layouts joined at a cut** (`--kinds splice`). A seed is the left part of one layout and the right part of another. The tool takes every ordered pair of the layouts of n-3 to n+3. It takes the 8 turns and mirror images of the second layout, and every cut where the parts hold n squares. On the old 410 it made 1,146 seeds and on the old 403 it made 876. The only seeds near soft-free are the held layout cut and put together again. The best new one settles at 1.5e-4 on 410 and 6.4e-4 on 403. Dry.

**Exact slab recombination** (`midm_slab.py`). A fault line is a straight line across the whole box that no square crosses. A slab of one layout stacked on a slab of another is a legal packing with no search. Its side is the larger of two numbers: the wider of the two slabs, and the sum of the two heights. The public fault DP composes along a staircase between two lattices. This is the straight case over every layout, in four directions.

- Control, green after one fix: with the bar of 370 made 0.001 worse, the scan rebuilds 370 at its true side. The first run reported nothing, because the empty slab was never paired.
- The pool was the held file and four older files: 1,845 layouts, 42,439 slabs and 186,059 middle slabs between two lines. **0 n came out below the held side.** 498 n have a composition within 0.004 of the held side. 478 of them are ties: the layout cut and put together again. The other 20 are an older layout of the same n with one row from the held file. The held file is closed under straight cuts.

## 5. What paid: the kick on a layout that was never kicked

The tool control found it. A kick of the held 370 (a public file as published, round 15) ended 6.3e-5 of side below it on the second try.

**What the kick finds.** It finds a better layout when that layout is the same arrangement as the start, a little more relaxed. The table compares each layout we held before a public find with the public layout that replaced it. The old layout is scaled to the new side. The public one is tried in its 8 turns and mirror images. A square counts as moved when no square of the other layout has its centre within 0.1 of it.

| n | old side | public side | squares moved | kick from the old layout |
|---|---|---|---|---|
| 412 | 20.796615 | 20.796102 | 0 of 412 | the public side on try 3, after 6 s. 36 of 64 tries reach it |
| 410 | 20.772127 | 20.764283 | 161 of 410 | 0 of 39, and 0 of 165 with the walk |
| 403 | 20.571429 | 20.564936 | 117 of 403 | 0 of 42, and 0 of 381 with the walk |
| 411 | 20.786944 | 20.776303 | 153 of 411 | 0 of 20 |
| 370 | 19.757499 | 19.756747 | 136 of 370 | 0 of 44, and 0 of 171 with the walk |

The old 412 was itself a public file as published (round 7). The public 412 of round 13 is that layout one kick later: our kick ends at 20.796101824, and the public side is 20.796101824.

So the kick tests one thing: does the held layout stay where it is under a move of 0.04? A layout that fq quenched with no kick may not.

**The scans.** `midm_scan.py --modes kick,lkick` ran 20 to 260 s per n from the start layout. `kick` moves every square. `lkick` moves the squares within 1.2 to 2.5 of one square by sigma 0.03 to 0.12. The gain of a row is counted from the start layout.

| start | n scanned | tries | core seconds | n certified | gain of score |
|---|---|---|---|---|---|
| slice, a public file as published | 20 | 1,190 | 1,713 | 344, 370, 374 | 9.020e-05 |
| slice, every other held layout | 163 | 6,815 | 5,535 | 378 | 2.809e-08 |
| outside the slice, a public file as published | 99 | 2,622 | 11,948 | 454, 462, 546, 604, 644, 654, 800, 845, 876 | 3.034e-05 |
| outside the slice, other held layouts | 111 | 1,657 | 16,666 | 497, 509, 593, 595, 642, 655, 694, 702, 706, 707, 746, 756, 760, 761, 799, 802, 807, 813, 817, 874, 875, 929, 971, 981, 986, 990, 994, 999 | 2.365e-04 |
| round 16 files | 30 | 273 | 3,845 | 421, 696, 701, 921, 995 | 3.169e-06 |
| round 17 files of other lanes | 44 | 848 | 9,623 | 510, 647, 755, 904, 975, 976 | 1.921e-05 |

- A public file as published opens on 12 of 119 n. The held file has 4 more that had no kick from the held layout: `647, 851, 914, 973`.
- Our own layouts in the slice do not open: 1 of 163 n, for 2.8e-8. The polish rounds of the lane quenched them many times.
- The row "outside the slice, other held layouts" holds the layouts of the held file above the slice that are not a public file as published. 111 n ran, and 28 certified, for 2.365e-04. The second table below splits the row by the kind of source.
- The round 16 files are the takes of the round 16 lanes, and 696 and 744, which the round 16 harvest took from a public file as published. 30 n ran, and 5 certified below their file, for 3.169e-06. They are 421, 696, 701, 921 and 995.
- The round 17 files are the certified files in the take dirs of the other round 17 lanes. The scan read those dirs 6 times, at 15:38Z, 17:47Z, 18:12Z, 18:32Z, 18:48Z and 19:16Z. Each time it kicked the files that were new or had changed. 44 n ran, and 6 certified below their file, for 1.921e-05. They are 510, 647, 755, 904, 975 and 976.
- Every n of the slice had a kick scan. The table of every n with its tries and sides is [`results/midm-kick-2026-11-12.tsv`](../results/midm-kick-2026-11-12.tsv).

**Whose files open.** The public files as published, by the file the results tables name:

| public file | n kicked | n certified | gain of score |
|---|---|---|---|
| `jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch` | 37 | 454, 462, 654, 845 | 2.500e-05 |
| `jonathan1506/50-top-2-6-22-1783-fault-dp-fq-stretch` | 9 | 374, 546, 644, 800 | 7.254e-05 |
| `busyaprime/squares-in-squares-fq-quenched-packings` | 6 | 344, 876 | 1.478e-05 |
| `jazivxt/boxed-in` | 3 | 370, 604 | 8.229e-06 |
| `jazivxt/boxed-in-sub` | 24 | none | 0 |
| `alexchilton/squares-in-squares-starter-kit` | 15 | none | 0 |
| `prvsiyan/a-square-deal-research-to-verified-packings` | 9 | none | 0 |
| results from GitHub (n = 156 to 269) | 5 | none | 0 |
| `kmmmvs/squares-public-merge-daily` | 3 | none | 0 |
| 6 other files with 1 or 2 n each | 8 | none | 0 |

The files that open are the outputs of a fault-line DP with an fq pass, and two sets of fq quenches. The `boxed-in-sub` and starter-kit files do not open.

**Our own layouts above the slice.** The results tables name a source for each n of the held file. The table splits the row "outside the slice, other held layouts" by that source.

| kind of held layout | n kicked | n certified | gain of score |
|---|---|---|---|
| one of our constructions (the family, readers, modules, soft-box, corner and border tools) | 59 | 497, 509, 593, 595, 655, 702, 706, 707, 746, 756, 760, 761, 802, 813, 874, 875, 929, 986, 994, 999 | 1.987e-04 |
| our fq quench of one of our constructions | 10 | 817, 971, 981 | 2.895e-05 |
| our fq quench of a public file | 31 | 642, 694, 799, 807, 990 | 8.805e-06 |
| the first merged file of the lane (2026-11-07), polished in every round since | 11 | none | 0 |

- Our constructions open: 23 of 69 n certified, for 2.277e-04 of score. The public files as published gave 12 of 119. A construction is built and quenched once, and no kick had touched it.
- Our fq quenches of public files: 5 of 31 n certified, for 8.805e-06.
- The first merged file of the lane: 0 of 11 n certified. 304 more n from 441 to 1000 hold such a layout and had no kick.

**Certified results.** All are floatsafe at 2.2e-11 and more than 1e-10 below the held score (`midm_take.py`, on boxA). Each is also more than 1e-10 below the score of round 16 for its n. A result that starts from another lane's file is also more than 1e-10 below that file. The same margin holds against every other take dir of round 17. The check reads the file of the same n in each dir at that moment. Each got one more fq quench from its certified file before it was written. The quench lowered 421, 604 and 701 by 2.3e-09, 1.2e-10 and 7.1e-11 and left the others as they were.

| n | held score | new score | gain | start | gap left to the board |
|---|---|---|---|---|---|
| 344 | 0.023926151655 | 0.023911758123 | 1.439e-05 | busyaprime/squares-in-squares-fq-quenched-packings | 7.4e-11 |
| 370 | 0.027104382269 | 0.027101084457 | 3.298e-06 | jazivxt/boxed-in | 2.9e-04 |
| 374 | 0.025258178867 | 0.025185665264 | 7.251e-05 | jonathan1506/50-top-2-6-22-1783-fault-dp-fq-stretch | 3.5e-05 |
| 378 | 0.024696384157 | 0.024696356063 | 2.809e-08 | our own layout | 1.6e-04 |
| 421 | 0.022200928010 | 0.022194671097 | 6.257e-06 | the round 16 file in `take-readers-r16`, itself 5.201e-06 below the held score | 1.5e-04 |
| 454 | 0.022965800787 | 0.022941795475 | 2.401e-05 | jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch | 1.2e-04 |
| 462 | 0.021148422969 | 0.021148421980 | 9.890e-10 | jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch | 1.7e-04 |
| 497 | 0.021842440478 | 0.021839399172 | 3.041e-06 | our own layout | 3.9e-06 |
| 509 | 0.018992798859 | 0.018973901017 | 1.890e-05 | our own layout | 1.3e-04 |
| 510 | 0.018350918635 | 0.018337654410 | 1.326e-05 | the round 17 file in `take-readers-r17`, itself 1.663e-07 below the held score | 4.2e-05 |
| 546 | 0.020615205889 | 0.020615205061 | 8.273e-10 | jonathan1506/50-top-2-6-22-1783-fault-dp-fq-stretch | 3.8e-04 |
| 593 | 0.019509290863 | 0.019489965599 | 1.933e-05 | our own layout | 4.4e-04 |
| 595 | 0.019241555492 | 0.019226906957 | 1.465e-05 | our own layout | 2.6e-04 |
| 604 | 0.016898067525 | 0.016893136168 | 4.931e-06 | jazivxt/boxed-in | 6.2e-05 |
| 642 | 0.018937525196 | 0.018931995540 | 5.530e-06 | our own layout | 3.2e-04 |
| 644 | 0.018484861595 | 0.018484833936 | 2.766e-08 | jonathan1506/50-top-2-6-22-1783-fault-dp-fq-stretch | 2.5e-04 |
| 647 | 0.017839679215 | 0.017696346353 | 1.433e-04 | the round 17 file in `take-readers-r17`, itself 1.381e-04 below the held score | 1.7e-06 |
| 654 | 0.016297595814 | 0.016297592303 | 3.511e-09 | jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch | 1.6e-04 |
| 655 | 0.015830048094 | 0.015830042738 | 5.356e-09 | our own layout | 1.1e-04 |
| 694 | 0.018271932790 | 0.018268976553 | 2.956e-06 | our own layout | 5.4e-04 |
| 696 | 0.017656803153 | 0.017656802078 | 1.075e-09 | the round 16 file in `take-harvest-2026-11-12m`, itself 3.329e-10 below the held score | 2.3e-04 |
| 701 | 0.016479534467 | 0.016472087983 | 7.446e-06 | the round 16 file in `take-readers-r16`, itself 7.369e-06 below the held score | 8.0e-05 |
| 702 | 0.016043282003 | 0.016042822207 | 4.598e-07 | our own layout | 1.0e-06 |
| 706 | 0.015683013049 | 0.015675001644 | 8.011e-06 | our own layout | 1.4e-04 |
| 707 | 0.015262128323 | 0.015259365084 | 2.763e-06 | our own layout | 1.5e-04 |
| 746 | 0.017625917978 | 0.017625912354 | 5.624e-09 | our own layout | 4.6e-04 |
| 755 | 0.015724600432 | 0.015673848407 | 5.075e-05 | the round 17 file in `take-readers-r17`, itself 5.075e-05 below the held score | 2.3e-05 |
| 756 | 0.015492030704 | 0.015492016671 | 1.403e-08 | our own layout | 1.4e-05 |
| 760 | 0.014807447344 | 0.014803789084 | 3.658e-06 | our own layout | 4.6e-11 |
| 761 | 0.014747298767 | 0.014744960485 | 2.338e-06 | our own layout | 1.7e-04 |
| 799 | 0.017344864319 | 0.017344862945 | 1.374e-09 | our own layout | 1.3e-04 |
| 800 | 0.017398668405 | 0.017398666621 | 1.783e-09 | jonathan1506/50-top-2-6-22-1783-fault-dp-fq-stretch | 4.0e-04 |
| 802 | 0.016782583560 | 0.016761933447 | 2.065e-05 | our own layout | 2.3e-04 |
| 807 | 0.015934554242 | 0.015934339966 | 2.143e-07 | our own layout | 1.7e-04 |
| 813 | 0.014580048806 | 0.014580042046 | 6.760e-09 | our own layout | 4.7e-06 |
| 817 | 0.014147221063 | 0.014130510403 | 1.671e-05 | our own layout | 1.2e-04 |
| 845 | 0.017002796692 | 0.017001814147 | 9.825e-07 | jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch | 7.2e-07 |
| 874 | 0.013815144963 | 0.013807897998 | 7.247e-06 | our own layout | 1.7e-04 |
| 875 | 0.013750642489 | 0.013750433849 | 2.086e-07 | our own layout | 3.2e-04 |
| 876 | 0.013523609625 | 0.013523222986 | 3.866e-07 | busyaprime/squares-in-squares-fq-quenched-packings | 2.3e-04 |
| 904 | 0.016514783453 | 0.016513141193 | 1.642e-06 | the round 17 file in `take-border-r17`, itself 9.499e-07 below the held score | 4.8e-04 |
| 921 | 0.015436991106 | 0.015407699331 | 2.929e-05 | the round 16 file in `take-modules-r16`, itself 2.917e-05 below the held score | 3.2e-04 |
| 929 | 0.014070531638 | 0.014070357950 | 1.737e-07 | our own layout | 2.7e-04 |
| 971 | 0.016056424025 | 0.016056376100 | 4.793e-08 | our own layout | 7.8e-04 |
| 975 | 0.015884774465 | 0.015679063770 | 2.057e-04 | the round 17 file in `take-corners-r17`, itself 2.056e-04 below the held score | 4.1e-04 |
| 976 | 0.015779942601 | 0.015559993024 | 2.199e-04 | the round 17 file in `take-twoshort-r17`, itself 2.199e-04 below the held score | 1.7e-04 |
| 981 | 0.015137741985 | 0.015125552087 | 1.219e-05 | our own layout | 4.4e-04 |
| 986 | 0.014371234234 | 0.014277081512 | 9.415e-05 | our own layout | 2.5e-04 |
| 990 | 0.013686041329 | 0.013685937515 | 1.038e-07 | our own layout | 2.0e-04 |
| 994 | 0.013034737482 | 0.013033542836 | 1.195e-06 | our own layout | 3.3e-04 |
| 995 | 0.012750400654 | 0.012737713999 | 1.269e-05 | the round 16 file in `take-modules-r16`, itself 1.077e-05 below the held score | 8.8e-05 |
| 999 | 0.012364921778 | 0.012363015101 | 1.907e-06 | our own layout | 1.9e-04 |

The 52 n sum to 1.047e-03 of score against the held file. 3.794e-04 of it is the kick. The rest is the gain the files of other lanes already had (421, 510, 647, 696, 701, 755, 904, 921, 975, 976 and 995). The slice holds 5 of the n (344, 370, 374, 378 and 421) and 9.649e-05 of the gain. Both kicks are needed: the kick of every square gave 24 of the results and the local kick 28. The best result of a scan came 6 to 312 s after its start, and after 65 s at the median.

Against round 16 and the files of the other lanes of round 17, the take stands on 41 n, for 3.804e-04 of score. 11 rows were certified before another lane wrote a lower file for the same n (378, 593, 746, 755, 800, 845, 874, 921, 976, 986 and 995). They stay in the take, and the assembler takes the lower file. For 378, 593, 746, 755, 845, 874, 986 and 995 the lower file starts from a kicked file of this take. The other lane went on from it. The round 17 file was assembled from the take dirs at 17:42Z. 28 n of this take are below it and below the other lanes, for 1.469e-04 of score.

**In the slice the step after a find is dry.** `relay.py` kicks again from the find. 344 took one more step of 1.3e-8 and now stands at the board's side, 7e-11 of score above it. The leg after that found nothing: 344 (51 tries), 374 (48), 370 (130), 378 (22). The soft-box island also ran from the find (`softrelay.sh`): 240 s in a box 2e-4 under the find and 240 s at 1e-4. It made 102,403 children on 374, 111,654 on 370 and 110,842 on 344. It found nothing.

**At larger n a second leg pays on some layouts.** `mkrelay.sh` reads each scan that ends. After a find of 3e-8 of score or more it queues one more kick leg, and the leg starts from the find. 49 legs ran on 32 n, 628 tries in all. 13 n took a step of 3e-8 or more. The legs sum to 4.641e-05 of score before the certifier. 19 n took no such step. 421 of the slice is among the n with no step.

**A second kick of a layout with no find adds little.** The box was busy: its load was 60 to 216 on 18 cores. So the first kick of some held constructions got 6 tries or fewer. 11 of them had a second kick with another seed, 117 tries in all. 2 found a lower side that the certifier keeps, for 2.772e-07 of score. They are 929 and 990. So the few tries of the first kick hid little.

## 6. A walk of kicks (kill line written 2026-11-12 14:24Z, before its first run)

**The idea.** The plain kick starts every try from the best layout. A walk also takes a worse result as the next start (`midm_scan.py --walk T`, T = 2e-4 of side). A kick result becomes the start when its side is below the walker's side plus T times an exponential draw. After 60 tries with no new best the walker goes back to the best. On the old 410 the plain kick fell into two basins only, so a walk can reach layouts the plain kick cannot.

**The control.** The same three files as in section 2: the old 410 (20.772126646), the old 403 (20.571428572) and the old 370 (19.757499204), 300 s each. A better layout exists for each. The walk itself is checked first: it must accept moves, or it is the plain kick under another name.

**The kill line.** No control n ends below its old held side in 300 s: the walk is dead and no n of the slice runs it.

**Result: red. The walk is dead and no n of the slice ran it.**

| n | tries | moves of the walker | results below the old held side |
|---|---|---|---|
| 410 | 165 | 82 | 0 |
| 403 | 381 | 4 | 0 |
| 370 | 171 | 83 | 0 |

The walker moves on 410 and 370: one try in two is taken as the next start, among layouts up to 1.4e-4 of side above the old one. None is below it. On 403 a kick comes back to the old side 99 times in 100. Its side is 144/7 to 9 digits, and the layout is rigid.

**The plain kick passes on the old 412.** That n was the fifth of the kill line and was not in the first control. The plain kick found the public side of 412 (20.796102) on try 3, after 6 s. 16 of its 32 kicks and 20 of its 32 local kicks ended there. The walk on the old 412 reached the same side on try 33. Section 5 says why 412 opens and the other four n do not.

## 7. A large local kick (kill line written 2026-11-12 14:38Z, before its first run)

**The idea.** The kick of section 5 moves a square by 0.003 to 0.04 and finds a better layout only when it is the same arrangement. The public layouts of 410, 403, 411 and 370 place a third of the squares elsewhere. A large local kick (`midm_scan.py --modes bkick`) takes every square within 3 to 6 of one square. It moves each by sigma 0.15 to 0.5 and gives it a new angle, so that fq packs a whole patch again.

**The control.** The old 410, 411, 403 and 370, 150 s each. The mode itself is checked first: more than half of its tries must come back as a packing, or fq cannot settle such a start.

**The kill line.** No control n ends below its old held side: the large kick is dead and no n of the slice runs it.

**Result: red. The large kick is dead and no n of the slice ran it.** Every try came back as a packing, so the mode works.

| n | tries | results below the old held side | lowest result |
|---|---|---|---|
| 410 | 24 | 0 | the old side |
| 411 | 51 | 0 | the old side |
| 403 | 47 | 0 | the old side |
| 370 | 31 | 0 | 1.3e-5 above the old side |

A patch packed again ends at the old side or above it, up to the plain grid (side 20 on 370).

**A melt.** The kill line was written at 14:53Z on 2026-11-12, before the first run. One scale between the two kicks was not measured. The melt puts the whole layout in a box 4 to 10 per cent larger and kicks it with sigma 0.03 to 0.1 (`--modes melt`). Every square gets room to move before fq squeezes the box again. The control is the same four n, 100 s each. The kill line is the same: no control n below its old held side.

**Result: red. The melt is dead and no n of the slice ran it.** Every try came back as a packing, so the mode works.

| n | tries | results below the old held side | lowest result |
|---|---|---|---|
| 410 | 12 | 0 | 5.6e-5 above the old side |
| 411 | 23 | 0 | the old side |
| 403 | 116 | 0 | the old side |
| 370 | 52 | 0 | the old side |

After a melt fq ends at the old side or above it, by up to 0.17 of side on 410. The larger box does not lead the squares to the other arrangement.

## 8. Files

| file | what it does |
|---|---|
| `midm_scan.py` | One n, many fq tries: squares removed from n+1 and n+2, a square inserted into n-1, kicks of all squares (`kick`) or of one neighbourhood (`lkick`). After a find the kicks start from the find. |
| `midm_soft.py` | A soft-box island in a box just under the held side, seeded from layouts of other n pressed into it (`drop1`, `drop2`, `grow1`, `peel`, `jog`, `splice`). It imports the kernel and the moves of `methods_soft.py`. |
| `midm_slab.py` | Exact slab recombination over a pool of layouts, with `--inflate` as its control and `--near` for the near misses. |
| `midm_sqpack.py`, `midm_ftmc.py` | One sqpack job and one FTMC job on one n, for the controls. Both engines are used by path and copied nowhere in this repo. |
| `midm_take.py` | `methods_take.py` with a source and a licence per n: floatsafe at 2.2e-11, kept only when more than 1e-10 below the held score, each csv written before `take.tsv` is replaced by a rename. A result must also be below the round 16 score of its n, and below its start when that is another lane's file. With `MIDM_LIVE` it must also be below the file of the same n in every other take dir of the round. |
| `midm_fqonce.py` | The one fq quench of each certified file. |
| `tools/midm/` | `worker.sh` runs a queue, `pw.sh` is a worker that takes lines from several queues in a set order, `pwp.sh` is that worker with a pause for the collect, `stopall.sh` ends every process of the lane on a box, `mkqueue.py` writes the queues of the slice run, `rest.py` queues every held layout above the slice that had no kick, `snapshot.py` queues the files that the other lanes certified since the last snapshot, `relay.py` kicks again from a find until a leg finds nothing, `mkrelay.sh` and `relayloop.sh` queue one more leg after each find of a queue run, `collect.sh` fetches, certifies, quenches and writes the take dir, `gate.sh` starts a queue only when the box has room, `tables.py` writes the kick tables of section 5 and `results/midm-kick-2026-11-12.tsv`. |
<!-- r19:files -->

Round 19 adds:

| file | what it does |
|---|---|
| `midm_scan.py --stop6`, `--bank FILE` | The stop rule and the bank for full kicks at sigma 0.04 (section 10.1). |
| `midm_shell.py` | The shell step and the band step of the family and readers tools where their sweeps stop, at donors and targets under n = 300 (`list`, `run`, `bandlist`, `bandrun`). It imports `family_step.py` and `family_readers.py`. |
| `tools/midm/` | `snap19.py` queues the take files of the other lanes by class, `kw.py` is the kick worker with the legs, `loop19.sh` runs snapshot, collect and handoff every 7 minutes, `collect19.sh` certifies against the round 17 file and every take dir, `handoff19.py` writes the handoff lines, `rule19.py` counts what the stop rule and the bank did, `table19.py` writes the results table, `slice19-mod.sh` runs `modules.py build` over a list, `fetch19.sh` and `stopall19.sh` are boxE side. |
<!-- /r19:files -->
<!-- r20:files -->
Round 20 adds:

| file | what it does |
|---|---|
| `midm_scan.py --kicks LIST` | A full kick draws its sigma from LIST (round 20: 0.02 and 0.04). |
| `midm_take.py` | `MIDM_LIVE` takes several globs, split by spaces. The round 18 table names the held sources first. |
| `tools/midm/` | `snap20.py` queues the take files of the other lanes by class and skips a start not below our own round 20 row. `loop20s.sh` runs it every 3 minutes, and `loop20c.sh` runs `collect20.sh final` and `handoff20.py` every 6 minutes. `near20.py` scores the near files of every take dir (`list`), queues them as kick starts with a start table each (`queue`) and counts what their scans did (`stats`). `table20.py` writes the results table. |
<!-- /r20:files -->
<!-- r21:files -->
Round 21 adds:

| file | what it does |
|---|---|
| `tools/midm/kw.py` | A leg follows every find of 1e-6 or more with no cap. Legs under n = 640 go to `legs.q` and the others to `legsB.q`. `KW_ORDER` names them `S` and `B`. |
| `tools/midm/` | `snap21.py` queues the take files of the other lanes by class, with the frozen round 20 backlog as class 3 (`MIDM_W` moves its work dir for a control). `loop21s.sh` runs it every 3 minutes and `loop21c.sh` runs `collect21.sh final` and `handoff21.py` every 6 minutes, both until `MIDM_END`. `final21.sh` stops the loops, waits for our two workers by pid and copies the run dirs. `table21.py` writes the results table. |
<!-- /r21:files -->

## 9. Next round

1. **Kick every public layout when it comes in.** The harvest step takes a public layout as published. A kick pass (`midm_scan.py --modes kick,lkick`, 60 to 130 s per n) costs about 2 minutes of one core per n. Here 12 of 119 public layouts as published gave a certified gain, 1.205e-04 of score in all. Section 5 names the 4 that had no kick from the held layout.
2. **Kick each lane's take before the merge.** A new construction is quenched and not kicked. Here 39 of 185 layouts gave a certified gain, 2.588e-04 of score in all. They are the round 16 and round 17 files of the lanes and our own layouts in the held file above the slice. Run our constructions first. Per layout, their first kick gave 3.299e-06 of score (69 n). A file of another lane gave 3.024e-07 (74 n). The assembler can run this as one step: `snapshot.py` reads the take dirs, and one core kicks a file in 2 to 4 minutes. `mkrelay.sh` then adds a second leg after each find. Here 13 of 32 n took one more step of 3e-8 of score or more.
3. **Kick the rest of the held file above the slice.** 304 n from 441 to 1000 hold a layout of the first merged file of the lane. They had no kick here, and `rest.py` lists them. 11 of that kind ran here, and none certified.
4. **Kick the public layouts we did not take.** Take a public layout of an accepted licence that ends within 1e-4 of score above the held one. The kick may take it below the held one: the finds here are 1e-9 to 7e-5. The harvest step reads every file and keeps the best layout per n. It would have to write the side of every layout it reads. No such index exists today, and the harvest dirs hold several GB.
5. **Do not run these again at n under 440.** Each has a red control here. They are the starts with squares removed or inserted (with any engine), the shell cut, the splice and straight slab recombination. The walk, the large local kick and the melt are red too.
6. **Use both controls for any local search in this slice.** The old 412 must open in seconds. The old 410, 403, 411 and 370 are another arrangement, with 117 to 161 squares moved. A search that opens one of them changes arrangements, and none here does. The files are `gather/round12-2026-11-12a.csv` and `gather/round14-2026-11-12a.csv`.
7. **The 20 largest gaps of the slice need another arrangement.** They hold 0.0106 of the 0.0169. No local search here reaches them. What is left is construction by family, as the readers, family and twoshort lanes do at larger n, and the fault-line DP on today's pool. The DP kit is fetched code and did not run in this lane.

<!-- r19:body -->
## 10. Round 19 (2026-11-12)

The bar of this round is the round 17 file (`gate/cand-round17-1112a`, public 22.1635211736). A result counts only when it is also lower than the same n in every `take-*-r17` dir, which are frozen, and in every other `take-*-r19` dir. All CPU was boxE, 2 processes. The numbers of this section are of 22:25Z, when the workers ended.

### 10.1 The standing kick, with a stop rule and a bank for sigma 0.04

**What ran.** `tools/midm/snap19.py` reads the take dirs every 7 minutes. For each n it takes the lowest certified file as a kick start. It leaves out a file that had a kick scan of 6 tries or more in round 17. The queue runs in four classes. A construction of round 19 comes first. Next is a construction that entered a frozen round 17 dir after 19:16Z. Then comes the one leg owed on 875, and last every other file. `tools/midm/kw.py` is the worker on boxE. It queues one leg after a find of 3e-8 of score or more, and one more after a find of that leg, never a third. When a later snapshot holds a lower file of an n, the older line of that n is dropped.

**The two rules, from the pool of the invent lane (its section 11).**

- `midm_scan.py --stop6` ends a scan after 6 tries when 3 or more of them came back to the start side (within 5e-9) and none found. In the pool such scans took 21% of the seconds for 3.6% of the gain.
- `midm_scan.py --bank FILE`: a stopped scan puts half of its unused seconds into the bank. A scan that runs to its end takes up to half of its own length from the bank and spends it on full kicks at sigma 0.04. In the pool sigma 0.04 gave 2.2 times the gain per second, on 8 finds.

**Tool controls, both run before the queue.**

- The held 817 of round 15 with seed 1 is a scan of round 17 with two finds in three tries. With `--stop6` the first two tries gave the same sides to 1e-12 (28.991780483613 and 28.987568629204), the same find (28.987568626606), and no stop.
- The file `r22/444.csv` with seed 32 had 4 of its first 6 tries come back in round 17. With `--stop6` the scan ended at try 6 after 8 s and put 71 of its 142 unused seconds into the bank.
- The bank part did not fire in these two. It fired first in the run, on 549: 53 s from the bank gave 6 full kicks at sigma 0.04 after try 18.

**What the two rules did, against the old schedule.** The old schedule runs every scan to its full length. That is 150 s under n = 700 and 225 s from 700 up.

| part of the run | scans | seconds | tries | finds | gain of score before the certifier | finds per 1,000 s | gain per 1,000 s |
|---|---|---|---|---|---|---|---|
| standard tries of the scans the rule stopped | 18 | 268 | 108 | 6 | 3.625e-10 | 22.39 | 1.35e-09 |
| standard tries of the open scans | 53 | 9,767 | 2189 | 66 | 1.227e-03 | 6.76 | 1.26e-04 |
| bank tries (full kick at sigma 0.04) | 18 | 1,122 | 237 | 6 | 3.538e-04 | 5.35 | 3.15e-04 |

- Scans: 71 (first scans 51, legs 20). They took 11,807 s. The old schedule would have taken 13,189 s for the same lines. A find in the table is any step of 1e-9 of side or more.
- Scans that the rule stopped: 18 (n = 147, 202, 262, 295, 295, 328, 329, 330, 365, 365, 366, 367, 419, 447, 448, 537, 579, 983). They saved 2,504 s, 19% of the old schedule. Scans that never reached 6 tries: 7. The rule cannot act on those. At n of 800 and more one try takes 35 to 110 s on a busy box, and a scan of 225 s holds 2 to 5 tries.
- The bank paid 1,122 s of full kicks at sigma 0.04. Open scans that drew from it: 18 (n = 263, 263, 263, 330, 332, 367, 407, 492, 549, 583, 584, 598, 703, 754, 794, 796, 796, 803).
- The first scans with a find of 3e-8 of score or more are in the table of finds below. Legs with such a find: 3 of 20, for 1.704e-04 of score. The rule stopped 6 legs.
- Read the rates with care, because one find moves a rate by a factor. The rule acts only where 6 tries fit in the scan.

The same tries by kind. Sigma 0.04 is the lead of the invent lane, and the bank tries are in its row.

| kind of try | tries | seconds | finds | gain of score before the certifier | gain per 1,000 s |
|---|---|---|---|---|---|
| full kick, sigma 0.003 | 299 | 1,068 | 9 | 1.184e-04 | 1.11e-04 |
| full kick, sigma 0.01 | 302 | 1,239 | 9 | 1.178e-05 | 9.51e-06 |
| full kick, sigma 0.02 | 271 | 1,479 | 9 | 3.475e-04 | 2.35e-04 |
| full kick, sigma 0.04 | 528 | 2,997 | 18 | 8.935e-04 | 2.98e-04 |
| local kick | 1134 | 4,377 | 33 | 2.091e-04 | 4.78e-05 |

**Where the finds are.** The table holds every first scan with a find of 3e-8 of score or more.

| n | start: the file of | tries | finds | gain of score on the start | of it by bank tries |
|---|---|---|---|---|---|
| 263 | `take-rigidsoft-r19` | 129 | 11 | 5.317e-04 | 2.573e-04 |
| 330 | `take-k123-r19` | 110 | 6 | 2.177e-04 | 0.000e+00 |
| 367 | `take-border-r19` | 90 | 7 | 2.064e-04 | 0.000e+00 |
| 365 | `take-rigidsoft-r19` | 62 | 2 | 1.083e-04 | 0.000e+00 |
| 262 | `take-k123-r19` | 91 | 3 | 8.996e-05 | 0.000e+00 |
| 263 | `take-rigidsoft-r19` | 177 | 4 | 8.923e-05 | 7.590e-05 |
| 295 | `take-k123-r19` | 215 | 2 | 8.446e-05 | 0.000e+00 |
| 492 | `take-k123-r19` | 27 | 5 | 2.739e-05 | 2.836e-06 |
| 407 | `take-k123-r19` | 62 | 2 | 1.701e-05 | 1.694e-05 |
| 800 | `take-family-r17` | 6 | 2 | 8.717e-06 | 0.000e+00 |
| 295 | `take-soft-r19` | 221 | 2 | 8.269e-06 | 0.000e+00 |
| 549 | `take-corners-r17` | 24 | 1 | 7.646e-06 | 0.000e+00 |
| 754 | `take-modules-r19` | 2 | 1 | 7.016e-06 | 0.000e+00 |
| 811 | `take-family-r19` | 7 | 1 | 3.264e-06 | 0.000e+00 |
| 584 | `take-k123-r19` | 22 | 3 | 2.741e-06 | 0.000e+00 |
| 796 | `take-twoshort-r17` | 8 | 2 | 1.325e-07 | 0.000e+00 |
| 703 | `take-modules-r17` | 17 | 3 | 4.137e-08 | 0.000e+00 |

- Under n = 440: 23 first scans, 9 with such a find, for 1.353e-03 of score in 2,949 s. From 440 up: 28 first scans, 8 with such a find, for 5.694e-05 in 5,503 s.
- The large finds are on files that the k123, rigidsoft, border and soft lanes wrote in the slice this round. Those lanes make a layout with a seam join or a band move, and then quench it once. A kick scan of 150 s then takes 1e-5 to 5e-4 of score more. The finds do not all come early: in the first scans of 295, 367 and 330 the last find came at try 17, 33 and 68.
- The lanes then build on the kicked file. The rigidsoft lane took our 365 and certified a layout 4.9e-6 below it. The next snapshot gave that file a kick again.
- One waste to cut. The snapshot takes the lowest file of the other lanes, also when our own row of that n is lower. The second 263 of the rigidsoft lane was above our 263. Its scan and its two legs took 613 s and ended on the side we had, 16.724372709.

**Four stopped legs, run again on the old schedule.** The rule ended the leg of 365, 295, 330 and 367 at try 6. That was after 3 to 18 s of 150 s. At n under 440 one try takes about 2 s, so 6 tries are a short look. Each of the 4 legs ran again with the same seed, with no stop and no bank.

| n | seed | the rule stopped at | old schedule: tries | seconds | finds | gain of score | first 6 tries the same |
|---|---|---|---|---|---|---|---|
| 365 | 136 | try 6, 18 s | 79 | 150 | 1 | 4.888e-06 | yes |
| 295 | 137 | try 6, 3 s | 253 | 151 | 0 | 0.000e+00 | yes |
| 330 | 137 | try 6, 15 s | 83 | 152 | 0 | 0.000e+00 | yes |
| 367 | 137 | try 6, 10 s | 81 | 152 | 0 | 0.000e+00 | yes |

- The control: the first 6 tries of each rerun give the sides of the stopped leg.
- 1 of the 4 reruns found. The leg of 365 took 4.9e-6 of score at try 21. That side is the one the rigidsoft lane had certified 8 minutes before, so it is not a row here. The other three legs found nothing in 81 to 253 tries.
- So on these 4 legs the rule saved 554 s and lost one find of 4.9e-6. The same seconds on first scans in the slice gave much more (the bullet above), and the queue was never empty.

**Certified results.** `midm_take.py` certified each on boxA. A row is floatsafe at 2.2e-11 and more than 1e-10 below the round 17 file. It is also below the start of its kick, and below every take dir of round 17 and round 19 at that moment. Each then got one fq quench from its certified file on boxE. `tools/midm/table19.py` wrote the table [`results/midm-r19-2026-11-12.tsv`](../results/midm-r19-2026-11-12.tsv).

| n | held score | new score | gain on the round 17 file | lowest file of the other lanes | gain on every file | the kick started from |
|---|---|---|---|---|---|---|
| 262 | 0.032168504026 | 0.031612991084 | 5.555e-04 | 0.031702950613 (`take-k123-r19`) | 8.996e-05 | `take-k123-r19` |
| 263 | 0.031811218390 | 0.031269000359 | 5.422e-04 | 0.031811218390 (`round 17 file`) | 5.422e-04 | `take-rigidsoft-r19` |
| 295 | 0.030780284892 | 0.030421258578 | 3.590e-04 | 0.030508461444 (`take-polish-r19`) | 8.720e-05 | `take-soft-r19` |
| 330 | 0.028982102189 | 0.028721434312 | 2.607e-04 | 0.028939118769 (`take-k123-r19`) | 2.177e-04 | `take-k123-r19` |
| 365 | 0.026583822412 | 0.026349054472 | 2.348e-04 | 0.026344166769 (`take-rigidsoft-r19`) | none: the other file is lower | `take-rigidsoft-r19` |
| 367 | 0.027934294411 | 0.027687115509 | 2.472e-04 | 0.027934294411 (`round 17 file`) | 2.472e-04 | `take-border-r19` |
| 407 | 0.025683600911 | 0.025637420832 | 4.618e-05 | 0.025654432644 (`take-k123-r19`) | 1.701e-05 | `take-k123-r19` |
| 492 | 0.023715433836 | 0.023059894779 | 6.555e-04 | 0.023087283320 (`take-k123-r19`) | 2.739e-05 | `take-k123-r19` |
| 549 | 0.019683106657 | 0.019640606991 | 4.250e-05 | 0.019648253181 (`take-corners-r17`) | 7.646e-06 | `take-corners-r17` |
| 703 | 0.016256062956 | 0.016216182384 | 3.988e-05 | 0.016216223785 (`take-modules-r17`) | 4.140e-08 | `take-modules-r17` |
| 754 | 0.016223440869 | 0.016066576108 | 1.569e-04 | 0.016099707640 (`take-modules-r17`) | 3.313e-05 | `take-modules-r19` |
| 755 | 0.015673849702 | 0.015672051495 | 1.798e-06 | 0.015672052858 (`take-readers-r17`) | 1.362e-09 | `take-readers-r17` |
| 793 | 0.018223848950 | 0.018199739181 | 2.411e-05 | 0.018199739350 (`take-twoshort-r19`) | 1.692e-10 | `take-twoshort-r19` |
| 796 | 0.018003875582 | 0.017963388777 | 4.049e-05 | 0.017964362744 (`take-twoshort-r17`) | 9.740e-07 | `take-twoshort-r17` |
| 800 | 0.017398666621 | 0.017312041169 | 8.663e-05 | 0.017320759942 (`take-family-r17`) | 8.719e-06 | `take-family-r17` |
| 811 | 0.015374627704 | 0.015207501467 | 1.671e-04 | 0.015159866390 (`take-family-r19`) | none: the other file is lower | `take-family-r19` |

The 16 rows sum to 3.460e-03 of score against the round 17 file. Most of that is the gain the other lane's file already had. Against every other take dir the take stands on 14 n, for 1.279e-03 of score.

### 10.2 The slice by construction: the tools of the other lanes stop at n = 300

The slice trails the board on 65 n, by 0.0168 of score. The 20 largest gaps hold 0.0106. The sweeps of the family, readers and modules lanes skip every n under 300: `family_readers.py` (`walk`, `reach`, `read`) and `modules.py` (`grow`, `queue`, `predict`) test `n < 300`. So 43 n of the slice never had a shell step or a build, and they trail the board by 0.0026. This round ran the steps that the bound left out. Each list had its kill line in `STATE.txt` before its first run.

**List 1: the shell step under 300 (`midm_shell.py list`, `run`). Dead.**

- The step takes a layout one shell up or down its line `k - 2m`. The driver imports the reader, the build, the squeeze and the finish of `family_readers.py` and `family_step.py`.
- Of the 119 held layouts of n 222 to 340 the layer reader reads 40. 21 build one way or both. 27 steps have a donor or a target under 300.
- **0 of 27 ended below the bar.** The closest is 303 down to 268, at 2.8e-3 of side above the bar. Next are 240 up to 273 (3.2e-3) and 239 up to 272 (4.1e-3). 293 up to 330 is the only step into one of the 20 largest gaps, and it ended 1.04e-2 above. The 18 down steps end 2.8e-3 to 5.9e-2 above their bars. All 27 took 171 s.
- The control. The one written first did not run: `family_readers.py ctl` on 293 was refused, because 293 has no twin layers and the copy of a layer does not clear. The driver is shown by a step of the list instead. 273 up one shell ended at 17.997149121, and the held 308 is 17.997149122. So the driver rebuilds a side we hold from a donor under 300.

**List 2: a two-arm build under 300 (`modules.py build` with the frozen library `lib17`). Dead.**

- `modules.cut` reads none of the 78 held layouts of n 222 to 299: all 78 say "no two flush arms". So the library cannot grow from them.
- The build ran on the 10 n under 300 that trail the board by 5e-5 or more: 262, 263, 264, 270, 259, 292, 295, 297, 298 and 299. **No choice of modules is predicted within 2e-3 of side above the bar on any of them.**
- The same build with the limit at 0.06 of side shows how far the library is. It has no choice for 262. Its best choice builds 0.054 of side above the bar at 263, 0.042 at 264, 0.045 at 295 and 0.033 at 299.
- From 300 up the generator of the modules lane runs, and it builds only choices predicted below the bar. Here the best choice builds 0.038 above the bar at 330, 0.070 at 365 and 0.013 at 367. The library has no choice within 0.06 for 328.
- A second kill line then built the 8 best choices for 367, with the limit at 0.03 of side. All 8 share one corner and one far end, and they differ in the second far end. The prediction is 0.0204 above the bar for all 8. The squeeze took 0.0091 of side on two of them and 0.0075 on six. So two ended 0.0114 above the bar and six 0.0129. Dead.
- The control: the build of 378 from the same library ended at 19.922374785, and the bar is 19.922373917.

**List 3: the band step (`midm_shell.py bandlist`, `bandrun`). Dead.**

- `family_readers.band_step` carries a band at 45 degrees 1 to 3 shells along its own period. 35 of the 223 held layouts of n 222 to 444 step as bands, in 89 steps as built.
- 19 steps start within 0.03 of side above the bar of a target that trails the board by 2e-5 or more. **None ended below its bar by more than 1.2e-9 of side.** Three steps rebuilt the held layout of their target to 1e-9. They are 235 to 336, 336 to 455 and 337 to 456. Those held layouts are these bands already.
- 300 up 3 shells to 413 ended 1.05e-3 above the bar. The file is in `near/` of the take dir. The other 15 ended 6e-3 to 2.1e-2 above. All 19 took 85 s.
- The control is in the list. As built, 226 up one shell is the held 257, at 16.535533907 both. In the same way 257 up one is the held 290, and 325 up two is the held 401.

**List 4: the pay table of the twoshort lane at m = 16 to 20 (`twoshort.py pay`, a model with no search). Dead.**

- The table gives a margin in squares for every n and every pair of arms. The margin is the loss that a side allows, less the best far zone of each arm, less a corner. The twoshort lane ran it at m = 28 to 31 only.
- Its far zones are for arms of 8, 9 and 10 at f from 0.62 to 0.74. In the slice 25 n hold a side fraction of 0.60 to 0.76. 15 of them trail the board by 2e-5 or more, and 9 of those are among the 20 largest gaps.
- **On the 15 n no pair has a margin above 0.** The best is 370 with two arms of 8, 0.27 squares short of our side. Next are 367 (0.33 short) and 409 (0.39). At the board's side the best pair is 0.48 squares short.
- On the 9 n of the 20 largest gaps two arms of 8 are 0.33 to 2.09 squares short of our side. They are 1.22 to 2.70 short of the board's side. Wider arms are further away.
- The control: at m = 28 to 31 the same command gives the table of the twoshort lane. 192 rows with the same kind of corner agree to 0.001 of a square, and 0 differ.

**A closure check with no CPU.** Two rules make a layout from another with no search. Add one row and one column of upright squares to a layout of n in a side L. That gives a layout of `n + 2 floor(L) + 1` in `L + 1`. A layout of n + 1 gives a layout of n. Over the round 17 file and every take dir both rules give 0 n. The control: with the side of 330 lowered by 0.02 the check names 367.

**What the board's sides say.** In the model of `modules.py` two flush arms of c1 and c2 squares hold `k_flush` squares more than the grid. The three end zones may then cost `k_flush - k` squares, the loss. The table gives that loss for arms of 8, 9 and 10 squares.

| n | m | k | our f | board f | gap of score | loss at our side: arms 8,8 / 9,9 / 10,10 | loss at the board side: 8,8 / 9,9 / 10,10 |
|---|---|---|---|---|---|---|---|
| 367 | 19 | 6 | 0.6924 | 0.6709 | 1.12e-03 | 7.6 / 9.0 / 10.1 | 6.5 / 7.9 / 9.1 |
| 328 | 18 | 4 | 0.6144 | 0.5995 | 8.19e-04 | 5.4 / 6.7 / 7.9 | 4.7 / 6.0 / 7.2 |
| 365 | 19 | 4 | 0.6129 | 0.5988 | 7.34e-04 | 5.6 / 7.1 / 8.3 | 4.9 / 6.4 / 7.6 |
| 333 | 18 | 9 | 0.7726 | 0.7600 | 6.92e-04 | 8.0 / 9.2 / 10.3 | 7.4 / 8.6 / 9.7 |
| 379 | 19 | 18 | 0.9427 | 0.9293 | 6.87e-04 | 9.4 / 10.5 / 11.4 | 8.6 / 9.7 / 10.6 |
| 366 | 19 | 5 | 0.6569 | 0.6458 | 5.78e-04 | 6.8 / 8.2 / 9.4 | 6.3 / 7.7 / 8.8 |
| 340 | 18 | 16 | 0.9269 | 0.9165 | 5.64e-04 | 9.2 / 10.3 / 11.1 | 8.6 / 9.7 / 10.6 |
| 262 | 16 | 6 | 0.7071 | 0.6981 | 5.56e-04 | 6.6 / 7.8 / 8.7 | 6.2 / 7.4 / 8.4 |
| 263 | 16 | 7 | 0.7332 | 0.7244 | 5.42e-04 | 6.7 / 7.9 / 8.8 | 6.3 / 7.5 / 8.5 |
| 339 | 18 | 15 | 0.9062 | 0.8974 | 4.79e-04 | 9.0 / 10.1 / 11.0 | 8.5 / 9.6 / 10.6 |
| 330 | 18 | 6 | 0.6924 | 0.6838 | 4.73e-04 | 7.1 / 8.4 / 9.5 | 6.7 / 8.0 / 9.1 |
| 401 | 20 | 1 | 0.5355 | 0.5261 | 4.69e-04 | 5.0 / 6.5 / 7.8 | 4.5 / 6.1 / 7.4 |
| 299 | 17 | 10 | 0.8010 | 0.7936 | 4.26e-04 | 7.6 / 8.7 / 9.7 | 7.2 / 8.4 / 9.4 |
| 329 | 18 | 5 | 0.6569 | 0.6492 | 4.22e-04 | 6.4 / 7.7 / 8.8 | 6.0 / 7.3 / 8.5 |
| 413 | 20 | 13 | 0.8229 | 0.8152 | 3.77e-04 | 8.4 / 9.7 / 10.8 | 8.0 / 9.3 / 10.4 |
| 295 | 17 | 6 | 0.7042 | 0.6980 | 3.60e-04 | 7.1 / 8.3 / 9.3 | 6.8 / 8.0 / 9.0 |
| 377 | 19 | 16 | 0.9009 | 0.8941 | 3.51e-04 | 8.9 / 10.0 / 11.0 | 8.5 / 9.7 / 10.6 |
| 416 | 20 | 16 | 0.8778 | 0.8708 | 3.42e-04 | 8.6 / 9.9 / 10.9 | 8.2 / 9.5 / 10.5 |
| 303 | 17 | 14 | 0.9018 | 0.8959 | 3.37e-04 | 8.6 / 9.7 / 10.5 | 8.3 / 9.4 / 10.2 |
| 371 | 19 | 10 | 0.7763 | 0.7705 | 3.02e-04 | 8.0 / 9.3 / 10.4 | 7.7 / 9.0 / 10.1 |

- At k = 6 the board's side fraction falls with m: 0.6981, 0.6980, 0.6838, 0.6709, 0.6569 and 0.6484 for m = 16 to 21. For arms of 10 and 10 the loss at those sides is 8.4, 9.1, 9.1, 9.1, 9.0 and 9.1. A loss that stays the same while m grows is what one design with fixed end zones gives. The same holds at k = 5: 8.6, 8.2, 8.5, 8.9, 8.6 and 8.7.
- Our held layouts at 10 of these 20 n are blocks or bands at 44 to 45 degrees. They are 262, 263, 295, 328, 329, 330, 365, 366, 367 and 401. The board's sides there are not the sides of such a block.
- A loss that stays the same would fit a two-arm design with end zones of about 9 squares for arms of 10. No build stands behind that reading. The zones we hold cost 1.2 to 2.7 squares more than the board's sides allow for arms of 8, and more for wider arms (list 4). The best choice of the frozen library for 263 ends 0.054 above the bar (list 2).
- Two other lanes reached the board's side in the slice this round, and both started from a band. The k123 lane joined the held band of 229 with its own copy at a seam (`k123_join.py`). It certified 366 at the board's side. The rigidsoft lane moved a band of rows of a held block by one diagonal track (`rigidsoft_band.py fault`). It certified 297 at the board's side, and 328, 332 and 409 lower.
- So the board's layouts at these n are bands with a seam or a fault. They are not two-arm designs. We hold no file of the board, so this is read from the two sides that now match.

### 10.3 Next round, best first

1. **Kick every new slice file in the minute it lands.** Under n = 440, 9 of 23 first scans found. They gave 1.353e-03 of score in 2,949 s of one core. From 440 up it was 8 of 28, for 5.694e-05 in 5,503 s. Run two workers from the first minute, with the newest file first.
2. **Put the kick scan inside the seam join and the band move.** The k123 and rigidsoft lanes quench a new layout once. One scan of `midm_scan.py --modes kick,lkick` of 150 s after that quench took 1e-5 to 5e-4 more on 263, 295, 330, 365 and 367. With the kick in their loop the next join or move starts from the lower file, with no wait for a snapshot.
3. **Use the large sigmas for the full kick.** Per 1,000 s, sigma 0.04 gave 3.0e-04 of score and sigma 0.02 gave 2.3e-04. Sigma 0.01 gave 9.5e-06, sigma 0.003 gave 1.1e-04, and the local kick 4.8e-05. A schedule of 0.04, 0.02 and the local kick loses little.
4. **Skip a start above our own row of that n.** Such a 263 took 613 s in a scan and two legs. It ended on the side we had.
5. **Keep the stop rule.** It ended 18 of 71 scans and saved 19% of the old schedule. On 4 stopped legs the old schedule found once, 4.9e-6 for 554 s. Give a scan at n of 800 and more 450 s. A scan of 225 s holds 2 to 5 tries there, so the rule cannot act and a find has little room.
6. **The rest of the 20 largest gaps go to the seam join and the band move.** Both reached the board's side this round, at 366 and 297. This lane then kicks each result.
7. **Do not run these again in the slice.** The shell step from donors under 300 gave 0 of 27, and the band step 0 of 19. The pay table has no pair above 0 on 15 n. The build from the frozen library under 300 gave 0 of 10 n, and its 8 best choices for 367 gave 0 of 8. The cut of layouts under 300 into modules gave 0 of 78.
8. **Do not lower the bound of 300 in `modules.py`.** The bound is not the limit. Two arms of 8 from the zones we hold are 0.3 to 2.1 squares short of our own sides. That holds at f from 0.60 to 0.76.

<!-- /r19:body -->
<!-- r20:body -->
## 11. Round 20 (2026-11-12 to 13)

The bar of this round is the round 18 file (`gate/cand-round18-1112a`, public 22.1604820601). A result counts only when it is also lower than the same n in every `take-*-r19` dir, which are frozen, and in every other `take-*-r20` dir. All CPU was boxE, 2 processes. A harness restart at 22:48Z killed the first agent of the round. The two kick workers on boxE lived on and were adopted. The snapshot and collect loops on boxA died with it and ran again from 22:51Z in their own session. The numbers of this section are of 00:57Z, after the final collect.

### 11.1 The standing kick, round 20

**What ran.** It is the kick of section 10.1 with three changes from the round 19 list (section 10.3).

- `tools/midm/snap20.py` reads every `take-*-r19` and `take-*-r20` dir every 3 minutes (`loop20s.sh`). A collect runs every 6 minutes in its own loop (`loop20c.sh`), so a wait for the fq quench never holds a new start back.
- A full kick draws its sigma from 0.02 and 0.04 only (`midm_scan.py --kicks 0.02,0.04`, item 3). The control: with `--kicks 0.04` the scan of 297 with seed 7 drew sigma 0.04 on all 6 tries. Without it, the same seed drew 0.04, 0.02, 0.02, 0.01, 0.003 and 0.04.
- A scan is 150 s under n = 700, 225 s to 799 and 450 s from 800 up (item 5).

**What it gave.** The take at 00:57Z, after the final collect holds 7 rows, 1.149e-03 of score below the round 18 file. 4 of them are below every other take dir too, by 3.303e-04.

| n | start: the file of | gain on the round 18 file | gain below every other take dir | tag |
|---|---|---|---|---|
| 448 | `take-k123-r20` | 3.029e-04 | 1.531e-05 | `kick-63-3@run_s63` |
| 549 | `take-modules-r20` | 4.555e-05 | 3.790e-05 | `kick-80-1@run_s80` |
| 554 | `take-classfill-r19` | 2.113e-04 | 1.277e-04 | `fq+lkick-350-1@run_s50` |
| 584 | `take-k123-r19` | 4.098e-05 | 0.000e+00 | `kick-139-1@run_s39` |
| 601 | `take-corners-r20` | 1.184e-04 | 0.000e+00 | `fq+lkick-168-1@run_s68` |
| 809 | `take-readers-r20` | 1.494e-04 | 1.494e-04 | `lkick-269-2@run_s69` |
| 910 | `take-k123-r20` | 2.801e-04 | 0.000e+00 | `lkick-155-1@run_s55` |

**The scans of the snapshots.** The counts are from `tools/midm/rule19.py` with `MIDM_RUNGLOB=s[5-9][0-9]`, before the certifier.

- Scans: 50 (36 first scans and 14 legs). The stop rule ended 6 of them.
- Seconds: 12,585 in all, 1,102 of them on bank tries at sigma 0.04. The stops saved 1,269 s.

| kind of try | tries | seconds | finds | gain of score before the certifier | gain per 1,000 s |
|---|---|---|---|---|---|
| full kick, sigma 0.04 | 261 | 4,830 | 8 | 2.562e-04 | 5.304e-05 |
| full kick, sigma 0.02 | 189 | 3,027 | 12 | 3.577e-05 | 1.182e-05 |
| local kick | 354 | 4,262 | 27 | 9.019e-05 | 2.116e-05 |

### 11.2 Kicks of near misses (new this round)

**The idea.** No snapshot reads a `near/` folder. A layout that another lane built and did not certify never gets a kick. In round 19 a kick of a new layout under n = 440 took 1e-5 to 5e-4 of score. That is the size of the gaps of these files. `tools/midm/near20.py list` scores every near file against the bar of its n. `near20.py queue` copies the chosen files into a start table of their own (`r49`, `r48`, ...), one file per n per table, so the certifier names each start.

**The control.** The certifier with these start tables must drop each near file as it is, because it is above the bar. It must keep a file below the bar and name the start row as its source. Both held. The 6 files of the first queue were dropped. A 554 file 1.8e-4 below the round 18 file was kept, with the source of its row.

**What was queued.**

- 6 files of the round 19 near folders under n = 640, more than 1e-7 above the bar. They are 330 (a k123 join), 365 (a rigidsoft band move and a forensics file) and 409 (a rigidsoft band move). The others are 413 (our own band step) and 587 (a farend row build).
- 18 corner windows of the forensics lane (handoff of 23:01Z), 1e-6 to 9e-5 above the bar. The lane had kicked 3 more (697, 582, 177) with no find, and those were left out.
- 3 near layouts of the twoshort lane at 793 and 794 (handoff of 23:12Z) and one of the corners lane at 870 went to class 4. They are 4.7e-7 to 1.8e-6 above the bar, and class 4 did not run before the end of the round. The 648 of the corners lane (4.1e-6 above) went to class 1.
- Left out: 263 of the rigidsoft lane (round 19 kicked it, and it ended on our side), and 332 and 409 within 2.5e-9 of the bar. Those two are the arrangement of the bar file, which had a kick in round 19 with no find.
- At 23:15Z the files under n = 640 moved ahead of the new files at 700 and more. Both workers take those first, and each takes 450 s there. Round 19 measured 1.0e-5 of score per 1,000 s from n = 440 up, against 4.6e-4 under 440.

**Result: dry.** 17 near files under n = 640 and at 648 had 26 kick scans and legs, 3,170 s in all. None ended below the bar. 3 came back to the bar side to 1e-10 (26, 330, 497). 5 stopped between the start and the bar (234, 266, 365, 587, 648). 9 found nothing (53, 106, 183, 260, 341, 409, 413, 452, 581). A near file there holds the arrangement of the bar file, less relaxed: the kick finds the bar again and does not pass it.

| scan | n | tries | finds | seconds | gap of the start | gap after the kick |
|---|---|---|---|---|---|---|
| s44/scan-648-144.tsv | 648 | 12 | 0 | 152 | 3.603e-06 | 3.603e-06 |
| s44/scan-648-44.tsv | 648 | 7 | 1 | 165 | 4.083e-06 | 3.603e-06 |
| s47/scan-106-47.tsv | 106 | 554 | 0 | 150 | 6.963e-06 | 6.963e-06 |
| s47/scan-183-47.tsv | 183 | 6 | 0 | 2 | 3.103e-05 | 3.103e-05 |
| s47/scan-234-147.tsv | 234 | 102 | 0 | 152 | 1.280e-06 | 1.280e-06 |
| s47/scan-234-47.tsv | 234 | 113 | 2 | 153 | 8.157e-05 | 1.280e-06 |
| s47/scan-26-147.tsv | 26 | 6 | 0 | 0 | -4.505e-11 | -4.505e-11 |
| s47/scan-26-47.tsv | 26 | 9785 | 1 | 150 | 2.360e-05 | -4.505e-11 |
| s47/scan-260-47.tsv | 260 | 93 | 0 | 150 | 2.862e-05 | 2.862e-05 |
| s47/scan-266-147.tsv | 266 | 6 | 0 | 10 | 1.335e-06 | 1.335e-06 |
| s47/scan-266-47.tsv | 266 | 71 | 5 | 158 | 6.712e-05 | 1.335e-06 |
| s47/scan-341-47.tsv | 341 | 6 | 0 | 13 | 4.470e-05 | 4.470e-05 |
| s47/scan-452-47.tsv | 452 | 123 | 1 | 214 | 7.125e-05 | 7.125e-05 |
| s47/scan-497-147.tsv | 497 | 61 | 0 | 150 | -4.884e-11 | -4.884e-11 |
| s47/scan-497-47.tsv | 497 | 68 | 1 | 217 | 8.025e-06 | -4.884e-11 |
| s47/scan-53-47.tsv | 53 | 1072 | 0 | 150 | 4.449e-06 | 4.449e-06 |
| s47/scan-581-47.tsv | 581 | 6 | 1 | 16 | 8.757e-05 | 8.757e-05 |
| s48/scan-365-48.tsv | 365 | 50 | 0 | 150 | 2.249e-04 | 2.249e-04 |
| s49/scan-330-149.tsv | 330 | 83 | 0 | 154 | -4.866e-11 | -4.866e-11 |
| s49/scan-330-49.tsv | 330 | 84 | 4 | 151 | 9.437e-05 | -4.866e-11 |
| s49/scan-365-149.tsv | 365 | 40 | 3 | 158 | 1.977e-05 | 4.888e-06 |
| s49/scan-365-249.tsv | 365 | 6 | 0 | 21 | 4.888e-06 | 4.888e-06 |
| s49/scan-365-49.tsv | 365 | 52 | 4 | 155 | 1.132e-04 | 1.977e-05 |
| s49/scan-409-49.tsv | 409 | 47 | 0 | 209 | 1.113e-05 | 1.113e-05 |
| s49/scan-413-49.tsv | 413 | 6 | 0 | 12 | 5.180e-05 | 5.180e-05 |
| s49/scan-587-49.tsv | 587 | 20 | 2 | 158 | 2.900e-05 | 2.899e-05 |

The gaps are of score, against the lowest file of the other lanes (our own round 20 rows left out).

### 11.3 Longer leg chains under n = 640

`kw.py` runs one leg after a find and one more after a find of that leg, never a third. On 554 every leg found, so the next legs were queued by hand.

**What it gave.** On 554 every leg found. The chain ran five legs past the first scan, and the fq quench of each certified file came on top.

| scan of 554 | seed | finds | gain of score on its start, before the certifier |
|---|---|---|---|
| first scan, on the file of `take-classfill-r19` | 50 | 4 | 1.454e-05 |
| leg 1 | 150 | 2 | 7.640e-05 |
| leg 2 | 250 | 2 | 2.035e-06 |
| leg 3, by hand | 350 | 1 | 8.609e-06 |
| leg 4, by hand | 450 | 2 | 2.609e-05 |
| leg 5, by hand | 550 | 1 | 3.380e-08 |

- The 554 of `take-classfill-r19` was 8.36e-5 below the round 18 file. After the chain and one fq quench ours is 2.113e-4 below it, 1.277e-4 below every other take dir.
- The fq quench of the find of leg 3 already held the gain of leg 4. The chain stopped after leg 5. From then on a leg was queued by hand only after a find of 1e-6 or more.
- 601 had two legs after each of its two first scans. They found 3.5e-7, 5.1e-7 and 2.3e-10, so the chain did not go on there.

### 11.4 Tool changes during the round

- `snap20.py` skips a start at or above our own round 20 row of its n (item 4 of section 10.3). The control: a snapshot with a scratch K counted 2 such n (554 and 584), which the old code queued as earlier files.
- `snap20.py` skips a new file of the same lane within 1e-6 of score of the file an earlier snapshot holds for that n. The bound was 2e-9. The family walk posted 549 four times, 6e-9 to 3e-8 apart, and each became a scan of 150 s. The first found nothing. The control: the scratch snapshot counted 3 such files after the change and 2 before.
- The four lines of class 2 under n = 800 moved ahead of the lines at 800 and more at 23:57Z (`q99-c1.q`, same seeds). A scan there takes 450 s, and 18 lines waited for one hour of two workers.
- `stopall.sh` of round 19 ends every process whose command holds `midm_scan.py`. The forensics and invent lanes run their own copies of that file on boxE now. So it did not run this round: the workers end at the deadline file, and only the pids of our own dir were checked.

### 11.5 Next round, best first

1. **Kick every new file under n = 640 in the minute it lands. Run legs while a leg finds 1e-6 or more.** It paid most per second this round. Under 640, 5 of 18 first scans found. The finds on 554, 549 and 448 stand below every other take dir. The polish lane took our 601 5.8e-10 lower. On 554 the third, fourth and fifth legs, queued by hand, gave 3.5e-5 more before the quench. Put that rule in `kw.py`: under n = 640 a leg follows every find of 1e-6 or more, with no cap on the number of legs.
2. **Use sigma 0.04 and the local kick. Drop sigma 0.02.** Per 1,000 s this round, sigma 0.04 gave 5.304e-05 of score. The local kick gave 2.116e-05 and sigma 0.02 gave 1.182e-05. In round 19 sigma 0.04 also led (3.0e-4 against 2.35e-4 for 0.02).
3. **Run the new files at 800 and more after those under 640.** A scan there takes 450 s. In this round those first scans gave 9.538e-05 of score before the certifier in 5,142 s (3 of 11 found). Most of it came from one file, the 809 of the readers lane (9.3e-5 in one scan). Skip a re-post of the same lane: the family walk posted 549 four times, 6e-9 to 3e-8 apart.
4. **Do not queue near files under n = 640 again.** 17 files had 26 scans, and none ended below the bar. All came back to the bar side or stopped above it. A near file there holds the arrangement of the bar file, less relaxed.
5. **The construction lanes now build on our kicked files.** The k123 lane joined our 910 and 584 into its own files of 23:44Z and 23:56Z. Those are 2.9e-10 and 2.4e-9 below ours. A short kick of 150 s in their loop found nothing on 910 and 738 at n of 700 and more. Our scan of 450 s on the same 910 found 2.3e-6. Their loop needs the longer scan at that size, as item 5 of section 10.3 says.
<!-- /r20:body -->
<!-- r21:body -->
## 12. Round 21 (2026-11-13)

The bar of this round is the round 19 file (`gate/cand-round19-1112a`, public 22.1514697138). A result counts only when it is also lower than the same n in every `take-*-r20` dir, which are frozen, and in every other `take-*-r21` dir. All CPU was boxE, 2 processes. The round ran in two parts. The first agent died at 01:24Z on a usage limit. Its two workers and its two loops ran on until 03:25Z. boxA rebooted at 05:36Z. From 09:53Z the workers and the loops ran again, until 12:10Z. The numbers of this section are of 12:11Z, after the final collect.

### 12.1 What ran

- `tools/midm/kw.py` runs a leg after every find of 1e-6 of score or more, with no cap on the chain (item 1 of section 11.5). A find of 3e-8 or more still gets the first two legs. Legs under n = 640 go to `legs.q` and the others to `legsB.q`. The workers take `legs.q`, then class 1, then `legsB.q`, then classes 2, 3 and 4 (`KW_ORDER=S,1,B,2,3,4`).
- A full kick draws sigma 0.04 only (`KW_KICKS=0.04`, item 2).
- `tools/midm/snap21.py` reads every frozen `take-*-r20` dir and every other `take-*-r21` dir every 3 minutes. Class 3 is the frozen backlog: the constructions of round 20 at n of 640 and more that never had a kick scan. A polish or harvest file goes to class 4 only when its n had a kick scan of 6 tries in round 20. A requench within 1e-6 of a file that an earlier snapshot holds is skipped, and so is our own file posted again within 1e-8.
- From 10:04Z the class 2 lines of fresh builds went to the front by hand (`q100-c2.q`, the same lines and seeds). A fresh build is one that no other kick lane had touched yet.

### 12.2 What it gave

**What it gave.** The take after the final collect holds 16 rows, 1.488e-03 of score below the round 19 file. 10 of them are below every other take dir too, by 1.972e-04. The follow lanes took 5 of our files and quenched them 4e-10 to 6.7e-6 lower (415, 809, 868, 869, 992). The merge counts the lowest file, so that gain stays in the round.

| n | start: the file of | gain on the round 19 file | gain below every other take dir | tag |
|---|---|---|---|---|
| 415 | `take-forensics-r21` | 1.816e-05 | 0.000e+00 | `fq+kick-148-1@run_s48` |
| 501 | `take-polish-r21` | 1.074e-04 | 5.779e-06 | `lkick-161-2@run_s61` |
| 591 | `take-forensics-r21` | 1.534e-04 | 5.981e-05 | `kick-62-3@run_s62` |
| 640 | `take-polish-r21` | 6.387e-05 | 9.170e-06 | `kick-49-1@run_s49` |
| 641 | `take-forensics-r21` | 1.224e-04 | 3.258e-05 | `lkick-162-1@run_s62` |
| 693 | `take-family-r21` | 8.643e-05 | 4.792e-05 | `fq+lkick-57-2@run_s57` |
| 749 | `take-forensics-r21` | 8.505e-05 | 4.014e-05 | `lkick-141-2@run_s41` |
| 752 | `take-harvest-r21` | 1.456e-04 | 8.885e-07 | `kick-141-1@run_s41` |
| 809 | `take-midm-r20` | 1.674e-04 | 0.000e+00 | `lkick-398-4@run_s98` |
| 859 | `take-polish-r21` | 4.224e-05 | 8.862e-07 | `lkick-21-1@run_s21` |
| 868 | `take-readers-r21` | 2.491e-04 | 0.000e+00 | `lkick-53-4@run_s53` |
| 869 | `take-harvest-r20` | 1.813e-04 | 0.000e+00 | `kick-21-2@run_s21` |
| 912 | `take-polish-r21` | 2.505e-05 | 1.873e-08 | `lkick-28-1@run_s28` |
| 976 | `take-modules-r21` | 7.664e-09 | 7.664e-09 | `lkick-31-1@run_s31` |
| 992 | `take-readers-r21` | 3.757e-05 | 0.000e+00 | `kick-56-2@run_s56` |
| 994 | `take-readers-r21` | 3.245e-06 | 0.000e+00 | `lkick-140-1@run_s40` |

### 12.3 Where the gain came from

A first scan found 8e-6 of score or more on 8 files. Each was a build that no kick had touched. Its first kick took 2.3e-4 to 2.7e-3 of side.

| n | start | first scan | legs, in order | fq quench of the last certified find |
|---|---|---|---|---|
| 869 | `take-harvest-r20`, the quench of a readers build (frozen backlog) | 6.744e-05 | 0 (a leg of 143 s at the deadline), then 4.9e-11 from the quenched file | none left |
| 749 | `take-forensics-r21`, a rectangle corner window | 2.892e-05 | 1.122e-05, 0 | none left |
| 868 | `take-readers-r21` of 10:39Z, 2 shells down from the border 992 | 2.310e-05 | 0 | none left |
| 640 | `take-polish-r21`, the quench of the forensics 640 | 9.170e-06 | 0 | none left |
| 591 | `take-forensics-r21`, a rectangle corner window (class 1) | 5.981e-05 | 0 | none left |
| 641 | `take-forensics-r21`, a rectangle corner window | 3.256e-05 | 2.326e-08 | none left |
| 992 | `take-readers-r21` of 10:57Z | 8.035e-06 | 0 | none left |
| 693 | `take-family-r21` of 11:03Z | 4.790e-05 | none (the deadline) | 2e-10 |
| 868 | `take-readers-r21` of 01:59Z | 3.758e-07 | 2.654e-06, 4.025e-06, 2.600e-07, then 7.5e-09 from the quenched file | 1.2e-05 |
| 809 | our frozen `take-midm-r20` 809 (the legs owed from round 20) | 3.422e-06 | 3.370e-06, 2.276e-06, 8.940e-06, 0 | none left |

- The files that the invent lane had kicked first gave little. Its loop runs `invent_rest.py --modes lkick` on each new file. Our scans of the readers 810, 930 and 993 came after that and found 0 to 2.2e-9.
- Most other first scans of class 2 found 0 to 6e-7. 415, 752, 859, 813, 549 and 994 gave 2e-7 to 9e-7 each. 750, 790, 807, 855, 929, 976 and 978 gave 0 to 1.3e-9.
- After an fq quench a leg finds little. On 868 the quench of the find took 1.2e-5, and the leg from the quenched file took 7.5e-9. On 869 the leg from the quenched file took 4.9e-11.

**By kind of try.** The counts are from `tools/midm/rule19.py` with `MIDM_RUNGLOB='s[2-9][0-9]'` and an empty `MIDM_OWED`, before the certifier.

| kind of try | tries | seconds | finds | gain of score before the certifier | gain per 1,000 s |
|---|---|---|---|---|---|
| full kick, sigma 0.04 | 762 | 17,772 | 30 | 2.442e-04 | 1.374e-05 |
| local kick | 714 | 12,429 | 54 | 8.148e-05 | 6.556e-06 |

Scans: 87 (60 first scans and 27 legs), 31,182 s in all. The stop rule ended 2 of them.

### 12.4 Traps of this round

- **A start table for every hand queue.** At 09:53Z the legs of 868, 869 and 809 went into `r97/` with no `work/r97.tsv`. `midm_take.py` then stops with "no start table", so the collects of 09:54Z and 10:00Z certified nothing. Write the table before the line enters a queue.
- **The classes run in file order, oldest first.** A class 2 file posted at 10:39Z sat behind 12 lines of 09:54Z. Fresh builds went to the front by hand, and they gave most of the gain of the second part.
- **A kick lane that runs first takes the gain.** The invent, twoshort and classfill lanes now run their own kicks on new files. The first kick on a fresh build takes the large step. A second kick on the same file finds 1e-9.

### 12.5 Next round, best first

1. **Kick each fresh build first, newest first.** A fresh build is a file that no kick lane has touched. Its first full kick at sigma 0.04 took the large step this round: 869, 591, 693, 749, 641, 868, 992 and 640 gave 8.0e-6 to 6.7e-5 each. The files that the invent lane had lkicked first gave 0 to 2.2e-9. Today `kw.py` takes the class 2 files oldest first, and the fresh builds went to the front by hand. Sort class 2 newest first, as class 1 already is.
2. **Kick every new forensics rectangle corner file at once.** Of 10 first scans on its files, 3 gave 2.9e-5 or more. They are 591 (6.0e-5), 641 (3.3e-5) and 749 (2.9e-5, then a leg of 1.1e-5). The polish quenches of two more gave 9.2e-6 (640) and 5.8e-6 (501). 415 gave 7.3e-7 in a scan and a leg. 750, 790, 807, 923, 969 and the forensics 501 gave 1e-10 or less. The design is new, and the forensics lane quenches it once with fq and does not kick it.
3. **Never start a leg from a quenched file.** After the fq quench of a find, the leg from it found 7.5e-9 (868) and 4.9e-11 (869). Run the legs from the raw finds, as `kw.py` does, and quench once at the end of the chain.
4. **Measure sigma 0.02 against 0.04 on the same fresh files.** On its fresh 994 build the classfill lane found 1.13e-4 of side with sigma 0.02. Sigma 0.04 found nothing there in 11 tries. Our fresh-build finds of this round all came at sigma 0.04. One worker on each sigma over the same 6 fresh files settles it.
5. **The near files stay dry.** A stair-c near 921 (5.6e-6 above the bar) and a rigidsoft near 328 (3.1e-6 above) had one scan each. They found 9e-10 and 0. Round 20 had 0 of 17.
6. **The frozen backlog of round 20 still waits.** 646, 649, 754, 852, 933, 982 and 995 never had a kick scan. Class 3 never ran after 03:25Z, because the fresh builds of round 21 came first. In round 21 the backlog gave 6.7e-5 on 869 (1 of 4 scans).
<!-- /r21:body -->

## 13. Round 22 (2026-11-13)

The bar is the round 20 file (`gate/cand-round20-1113a`, public score 22.1486392356).
Every result must beat the frozen round 21 takes and the live round 22 takes by more than 1e-10.
All search runs on boxE, with two slots.

### 13.1 Queue and controls

The queue reads certified takes every minute.
It puts new forensics rectangle corners first.
Small raw-find legs precede ordinary fresh builds.
The late public batch gets its own slot.
The other slot serves forensics and final quenches.
Large raw-find legs follow fresh builds.
The frozen backlog runs last.
Every class uses the source file's timestamp to put the newest file first.
The first six fresh files get paired scans at sigma 0.02 and 0.04.
Each pair uses the same file, seed and time allowance, with no bank time.
Ordinary scans use sigma 0.04 and the local kick.
Explicit handoffs of new strip and rounded-band designs also get scans.
These layouts change the geometry of the old near starts that failed.
Legs start from raw finds.
A result enters the take only after its certified file gets an fq quench on boxE.

The controls passed:

- The old 370 gave one find in six kicks. Its side fell from 19.756747264363 to 19.756683828751.
- The queue put q100 before q99 in every class. A second control checked source timestamps and claims.
- The certifier rejected the frozen 693 and kept the improved 693 from the same start table.
- Rechecking the published 693 gave score 0.017883913731623347 with no error.

The initial snapshot queued stale polish copies because its history matched only the original lane.
Those waiting jobs were canceled.
The corrected snapshot follows polish and harvest copies across lanes and checks the lowest live take.
The paired scan of the old 693 stayed as a separate control.

### 13.2 Results

Comparisons: 2026-11-13T15:29:00Z.

The final take has 13 rows, 0.000935185 below the round 20 file.
9 rows remain below every other take, by 0.00039514 in total.
The [results table](../results/midm-r22-2026-11-13.tsv) gives both comparisons.

| n | gain on round 20 | gain on every take | start |
|---|---|---|---|
| 342 | 7.83117e-06 | 7.83117e-06 | `take-harvest-r22` |
| 372 | 1.1246e-05 | 1.1246e-05 | `take-harvest-r22` |
| 413 | 0.000289959 | 0.000289959 | `take-harvest-r22` |
| 502 | 3.49289e-06 | 3.49289e-06 | `take-polish-r22` |
| 585 | 5.06239e-05 | 7.51036e-07 | `take-forensics-r22` |
| 640 | 9.09645e-05 | 2.7094e-05 | `take-readers-r22` |
| 693 | 0.000140597 | 5.41667e-05 | `take-polish-r22` |
| 793 | 2.10249e-06 | 0 | `take-twoshort-r21` |
| 798 | 0.000183895 | 2.76904e-08 | `take-forensics-r22` |
| 807 | 6.89576e-07 | 5.7136e-07 | `take-family-r22` |
| 875 | 7.28447e-05 | 0 | `take-family-r22` |
| 936 | 5.75193e-05 | 0 | `take-family-r22` |
| 981 | 2.34182e-05 | 0 | `take-forensics-r22` |

### 13.3 Measurements and next round

Completed jobs: 75.
Initial round 22 source scans gave 6.32888e-05 before certification. Raw legs gave 3.21405e-05.
Fresh paired scans gave 9.64514e-09 at sigma 0.02 and 9.65152e-09 at sigma 0.04.
The old 693 control gave 4.076e-5 at sigma 0.04.
At sigma 0.02 it gave 9.077e-6, then 3.168e-5 on its first raw leg.
All jobs ended before cleanup. The copy from boxE passed a checksum comparison.

Next round:

1. Kick fresh builds first. Initial round 22 source scans gained 6.32888e-05 before certification.
2. Give late finds their owed raw legs. The 693 control and its leg gave about 4.076e-5 at either sigma.
3. Keep comparing sigmas on fresh files. The paired gains were 9.64514e-09 at 0.02 and 9.65152e-09 at 0.04.
4. Keep the raw-leg rule. The 10 legs found 3.21405e-05 before certification.
5. Keep near files out. Round 20 had no certified result from 17 near starts.

## 14. Round 23 (2026-11-13)

Two boxE slots ran until 18:25Z. Search and final quenches shared the 18:30Z deadline.
One slot served the 39 public layouts left by round 22 from the start.
New forensics layouts led the other slot. Useful raw legs and other fresh starts followed.

Reserved windows served old raw legs and the frozen backlog.
A later reorder put short public scans first. Each duration tier kept the newest file first.

The queue read takes and handoffs each minute. It inventoried near folders every ten minutes.
Snapshots kept the exact bytes they hashed. Certified source files could not be newer than their take table.
Source scores had to match the captured packing within 5e-11.

The old 370 control made six tries and found once. Its side fell from 19.756747264363 to 19.756683828751.
Completion records name each certified input by its hash. The controls accepted the exact input and rejected stale records.
The deadline guard stopped a simulated blocked child in 0.103 seconds.
The collector drained each finished quench separately, including files from an unfinished batch.

Every published file passed floatsafe at 2.2e-11, then received an fq quench on boxE and passed certification again.

At 2026-11-13T18:39:00Z, 6 rows were 0.000809473729 below round 21.
5 rows beat every frozen round 22 and other live round 23 take, by 4.11298963e-05 in total.
The [results table](../results/midm-r23-2026-11-13.tsv) records both comparisons.

| n | gain on round 21 | gain on every take | start |
|---|---|---|---|
| 264 | 5.70858e-05 | 5.13556e-06 | `take-harvest-r22` |
| 401 | 0.000125552 | 2.01213e-05 | `take-polish-r23` |
| 462 | 2.75836e-05 | 5.9583e-07 | `take-harvest-r22` |
| 543 | 9.69898e-05 | 1.08096e-09 | `take-k123-r23` |
| 587 | 9.48246e-05 | 1.52762e-05 | `take-harvest-r22` |
| 639 | 0.000407438 | 0 | `take-forensics-r23` |

| queue | scans | seconds | gain before certification |
|---|---|---|---|
| public | 39 | 9851.7 | 0.000248207 |
| r23 | 25 | 4820.1 | 2.22146e-06 |
| raw legs | 14 | 2282.6 | 1.95693e-05 |
| new-design raw | 2 | 303.7 | 0 |
| r20 | 6 | 2190.1 | 1.60527e-10 |

The exact source rows account for the inherited gains.
The final take added 2.41385205e-05 beyond those rows. The certified-file quenches added 0.
boxE copy passed a checksum check. All lane processes stopped, and its scratch was removed.

Next round:

1. Kick fresh public layouts first. 39 scans gained 0.000248207 before certification in 9851.7 seconds.
2. Continue raw legs while they gain 1e-6 or more. 14 scans gained 1.95693e-05 before certification in 2282.6 seconds.
3. Give fresh builds priority over older source versions. 25 scans gained 2.22146e-06 before certification in 4820.1 seconds.
4. Test remaining frozen layouts [646] from work/pending-final.json. 6 scans gained 1.60527e-10 before certification in 2190.1 seconds. The round 21 backlog 869 scan gained 6.7e-5.
5. Test a new geometry before repeating the raw near starts. 2 scans gained 0 before certification in 303.7 seconds.
6. Recheck old owed legs [342, 372, 413, 981] against the latest bar. The 2 tested owed legs gained 0 in 310.4 seconds.
7. Require a geometry change before repeating old near layouts. Round 20 had zero certified wins from 17 starts.

## 15. Round 24 (2026-11-13)

Two boxE slots served fresh public and construction layouts before clean unstarted round23 layouts.
The new 639 uses candidate layouts 496 and 590. The new 918 uses candidate layouts 590 and 917.
Raw-find legs started from saved raw layouts. The round20 backlog stayed closed.
Source fields reached 536378 characters. The certifier and results reader now accept fields up to 16 MiB.
The queues read handoffs each minute and inventoried near folders every ten minutes.
Source admission imported `forensics_sources.trace` and saved evidence by input hash.
The old 370 control found once in six kicks. Its side fell from 19.756747264363 to 19.756683828751.
Source controls accepted the candidate and a clean round23 row. They rejected forbidden roots and missing provenance.
Search and certified-file quenches shared the 22:15Z deadline. Every published row passed floatsafe at 2.2e-11 before and after its boxE quench.

At 2026-11-13T22:24:00Z, the take held 13 rows. Their score gains sum to 0.00172106339 against the original round23 candidate.
9 rows beat every other live round24 take, by 0.000120383098 in total.
The [results table](../results/midm-r24-2026-11-13.tsv) records both comparisons.

| queue | scans | seconds | gain before certification |
|---|---|---|---|
| raw legs | 26 | 6561.0 | 3.15153e-05 |
| fresh r24 | 33 | 11590.8 | 0.000465172 |
| new-design raw | 20 | 2517.8 | 9.3682e-05 |
| accepted r23 unstarted | 3 | 823.6 | 2.38062e-05 |
| public | 2 | 342.5 | 6.81928e-05 |

All own workers stopped. boxE archive passed a checksum comparison before scratch removal.

Next round:

1. Finish withheld certified-input quenches in work/fq-send before publication. Their required quenches did not complete by the common deadline.
2. Kick fresh public layouts first. 2 scans gained 6.81928e-05 before certification in 342.5 seconds.
3. Kick fresh builds at handoff. 33 scans gained 0.000465172 before certification in 11590.8 seconds.
4. Test fresh near geometry once. 20 scans gained 9.3682e-05 before certification in 2517.8 seconds.
5. Use clean unstarted builds only when fresh queues are empty. 3 scans gained 2.38062e-05 before certification in 823.6 seconds.
6. Continue raw legs while they gain 1e-6 or more. 26 scans gained 3.15153e-05 before certification in 6561.0 seconds.
7. Audit the 38 starts in work/source-proof-deferrals.json before reuse. Their input-proof links remained unresolved, and they were withheld.
8. Keep old near repeats and round20 backlog closed. Round20 had no certified wins from 17 near starts.

## Summary

- 52 n certified below the held score, for 1.047e-03 of score in all. 5 are in the slice (344, 370, 374, 378 and 421), for 9.649e-05. The others are public files, round 16 and round 17 files and our own constructions at larger n. Against round 16 and the files of the other lanes of round 17, the take stands on 41 n, for 3.804e-04 of score.
- The idea of the round is dead at n under 440. Take a layout of a neighbour n and remove or insert squares. From that start fq, the soft island, sqpack and FTMC do not get below the held side. The control was red on four n, and the 20 largest gaps gave 0 finds.
- Six more starts are dry, each with its own control. They are the shell cut, the splice, straight slab recombination, the walk of kicks, the large local kick and the melt.
- What pays is a small kick before the fq quench, on a layout that no kick has touched. It finds the same arrangement a little more relaxed, in seconds. It does not find another arrangement.
- Above the slice our own constructions open too: 23 of 69 n certified, for 2.277e-04 of score. They are built, quenched once and never kicked.
- Above the slice a second kick leg from a find goes further on some n. Here 13 of 32 n took one more step of 3e-8 of score or more. In the slice the second leg is dry.
- The 20 largest gaps of the slice hold 0.0106 of its 0.0169, and they need another arrangement.
- Next: make the kick pass a step of every harvest and of every lane's take (section 9).
<!-- r19:summary -->

**Round 19**

- 16 n certified below the round 17 file, for 3.460e-03 of score. 14 of them are below every other take dir too, for 1.279e-03. All are kicks of new files of other lanes.
- Most of the gain is in the slice. The k123 and rigidsoft lanes wrote new layouts there with a seam join and a band move, and one kick scan took 1e-5 to 5e-4 more on each. Under n = 440, 9 of 23 first scans found.
- The stop rule ended 18 of 71 scans and saved 19% of the seconds of the old schedule. Four stopped legs ran again on the old schedule, and one found, 4.9e-6. The bank paid 1,122 s of full kicks at sigma 0.04.
- Our own construction lists in the slice are dead. They are 27 shell steps, a two-arm build on 10 n, 19 band steps and the pay table on 15 n. None ended below its bar.
- The board's layouts at the 20 largest gaps are bands with a seam or a fault, and not two-arm designs. **Next:** the kick scan goes inside the seam join and the band move, and this lane kicks every new slice file in the minute it lands.
<!-- /r19:summary -->
<!-- r20:summary -->
**Round 20**

- 7 n certified below the round 18 file, for 1.149e-03 of score. 4 of them are below every other take dir too, for 3.303e-04. All are kicks of new files of other lanes.
- Under n = 640, 5 of 18 first scans found. On 554 the legs went on by hand and took the file 1.277e-4 below every other take dir.
- The kick of near files is dry. 17 files of the near folders had 26 scans, and none ended below the bar.
- Sigma 0.04 led again (5.304e-05 of score per 1,000 s against 1.182e-05 for sigma 0.02). **Next:** kick each new file under 640 at once, run legs while they find 1e-6 or more, and drop sigma 0.02.
<!-- /r20:summary -->
<!-- r21:summary -->
**Round 21**

- 16 n certified below the round 19 file, for 1.488e-03 of score. 10 of them are below every other take dir too, for 1.972e-04. All are kicks of files of other lanes, and the owed legs of our round 20 809.
- The gain came from fresh builds, files that no kick lane had touched. 869, 591, 693, 749, 641, 868, 992 and 640 gave 8.0e-6 to 6.7e-5 each. Files that the invent lane had kicked first gave 0 to 2.2e-9.
- The forensics rectangle corner design paid most per scan: 3 of 10 first scans gave 2.9e-5 or more.
- A leg from an fq-quenched file found 7.5e-9 and 4.9e-11. Two near files found 9e-10 and 0. **Next:** sort class 2 newest first, kick each fresh build before any other kick lane, and compare sigma 0.02 with 0.04 on the same fresh files.
<!-- /r21:summary -->

## 16. Round 25 (2026-11-13 to 14)

Two boxE slots served fresh public layouts and builds. New search starts stopped at 02:15Z. Search and certified-file quenches shared the 02:45Z deadline.
The unfinished round 24 quenches and 38 source-proof deferrals went to the quench lane. Two claimed, never-started public layouts ran while fresh queues were empty.
Source admission walked recorded parents and retained proof files. It saved each proof by its coordinate and metadata hashes. No retained row uses a forbidden or unresolved root.
The old 370 control made 31 tries and found once. Its side fell from 19.756747264363 to 19.756683828751. Source controls rejected the hidden GitHub 735 root and accepted the licensed held 370.
Withdrawals quarantined rebuilt 534 and held 975 descendants. Relative-parent controls retained public 542 and refused the missing old reader 974 link.
Owned-PID cancellation stopped its test tree in 0.735 seconds on boxE. Group signalling failed with EPERM and was removed.
The old 921 far-zone alias reaches the unlicensed 983 seed. Its inputs and four old near handoffs were quarantined. New near filenames bind the input key and coordinate hash.
Every retained take row passed floatsafe at 2.2e-11 before and after a certified-file quench on boxE. The final comparison dropped rows that no longer beat every live take.

The take holds 2 rows. Gains sum to 0.000133594307324 against the base and 0.000133594307324 beyond other live takes. The [results table](../results/midm-r25-2026-11-14.tsv) records both comparisons.

These base gains include the input designs from other lanes. Our kicks and quenches gained 9.58169226628e-07 against those exact inputs. The table records each input score.

| queue | scans | seconds | gain before certification |
|---|---|---|---|
| withdrawn source | 16 | 5340.7 | 0 |
| fresh near | 49 | 12538.0 | 0.000192742817 |
| fresh r25 | 10 | 2287.5 | 1.34363605e-07 |
| clean unstarted r24 | 2 | 350.5 | 5.39034784e-05 |
| raw legs | 14 | 3455.8 | 0.000158195619 |

Next round:

1. Kick fresh public and rebuilt designs before saved starts. Round24 fresh builds gained 0.000465172 in 33 scans. Its two public scans gained 6.81928e-5 in 342.5 seconds.
2. Continue the raw leg for n934 from <scratch>/bounties-squares/take-midm-r25/near/934-raw-kick-r25626-bf1cebc80203.csv. Its last scan gained 2.63461429e-06 before certification in 459.8 seconds. It still missed the live bar, and no further leg finished.
3. Continue the raw leg for n934 from <scratch>/bounties-squares/take-midm-r25/near/934-raw-kick-r25627-7d10b52df496.csv. Its last scan gained 2.7522168e-06 before certification in 572.1 seconds. It still missed the live bar, and no further leg finished.
4. clean unstarted r24: 2 scans gained 5.39034784e-05 before certification in 350.5 seconds. Prioritize changed, traced designs and continue raw legs only while they gain at least 1e-6.
5. raw legs: 14 scans gained 0.000158195619 before certification in 3455.8 seconds. Prioritize changed, traced designs and continue raw legs only while they gain at least 1e-6.
6. fresh near: 49 scans gained 0.000192742817 before certification in 12538.0 seconds. Prioritize changed, traced designs and continue raw legs only while they gain at least 1e-6.
7. fresh r25: 10 scans gained 1.34363605e-07 before certification in 2287.5 seconds. Prioritize changed, traced designs and continue raw legs only while they gain at least 1e-6.
8. Rerank 215 unstarted clean inputs in work/pending-final.json against the next base. Fresh designs took the available slots, so these inputs have no completed scan.
9. Keep old near repeats and round 20 backlog closed. Round20 had 0 certified wins from 17 starts.

## 17. Round 26 (2026-11-14)

Five agents ran the lane in turn. The first lost its login at 12:52Z. The second stopped on a usage limit at 13:24Z. The third ended at 13:56Z. The fourth stopped when its connection dropped between 16:27Z and 16:33Z. The fifth adopted the running driver and closed the round. The driver and the box workers ran on through every change of agent.

One driver on boxA queued, assigned, certified, quenched and published (tools/midm/round26.py). Box workers ran midm_scan.py kick and local kick scans (tools/midm/worker26.py). boxE ran two slots and boxD ran one. New scans started until 16:50Z. Search and quench shared the 17:15Z deadline.

The old 370 control found once on each box. Its side fell from 19.756747264363 to 19.756683828751 on boxE and on boxD.

Changes of round 26, each with its measured reason:

- Forensics rectangle compositions (near/n-rect.csv) run first, up to 2e-4 above the lowest of the base and every live take. Before, a near file more than 1e-4 above the base was skipped. First scans on rect files paid 18 of 51 and gained 0.000865 before certification. Scans on near files of other lanes paid 1 of 16.
- Harvest's fresh public layouts ran before the other fresh takes, as the harvest handoff of 14:22Z asked. Kicks took 761, 818, 971 and 453 below the harvest rows. Those scans paid 4 of 9.
- A certified find gets its quench only after its scan ends. Before, quenches held about a third of boxE slots and half of the boxD slot, mostly on finds that a later find replaced.
- Each start is traced before it takes a slot. Our kicks on starts that the tracer refused beat nothing, and such a start can never publish.
- The source record of a start is saved when the driver queues it. Other lanes rewrite their near files and records within minutes. So publish traces the saved record when the file changed.
- The source cell of a composition names each part and the ledger that gives its source.
- Our certified finds and their quenched copies count when the driver ranks a start. The driver does not run a copy of our own find again.
- The filter for out source (a) matches the upstream name squares-joegun-boxed. The bare word joegun also matched the Apache 2.0 dataset jonathan1506/joegun-squares-packings and refused clean starts.
- The source checks refuse the rows that other lanes withdrew this round. These are harvest 416 499 646 654 695 814, k123 546 695 932, backlog 706, and the forensics rect files on 415 and 501. The trace cache was cleared once, so every queued and published start was traced again. That walk took out our 546, 642 and 694 rows, whose parts reach the harvest 695. Our 684 left too, because its start had changed and had no saved record, so nobody could walk it again.

Other lanes followed our rows within minutes. Backlog, forensics and soft used our finds on 910, 972 and 791 as starts and published lower rows. Those rows count for the team in their takes.

The take holds 4 rows: 453 (0.00026), 736 (2.54e-09), 761 (9.38e-05), 909 (0.000186). Gains sum to 0.000539621 against the base and 0.000539621 beyond other live takes. The [results table](../results/midm-r26-2026-11-14.tsv) records both comparisons and the score of each input.

These base gains include the input designs from other lanes. Our kicks and quenches gained 0.000129 against those exact inputs.

Three rows left near the end. 971 left at 16:44Z. Its part B is a classfill kick of a forensics composition built on our old 684, which forensics now lists as withdrawn. So the walk stops there. Backlog holds a clean 971 only 3.5e-6 above ours, and our file waits in near/ with its chain. 926 left at 17:06Z. Its start tree reaches a harvest near file that harvest withdrew under rule (b). 632 left at 17:05Z because backlog published a lower 632.

Source note for the skeptic. Our 453 and 761 start from harvest public rows (lucifer19/think-select-reclose, Apache 2.0). Quench and twoshort measure those harvest rows at a max centre distance of 0.338 and 0.499 from the prvsiyan 1105 row, below their 0.55 line. Harvest and classfill measure the share of squares within 1e-3 of the prvsiyan row at 0.004 and 0.001, which is an unrelated design. We keep both rows on the share measure. Harvest dropped its own 453, 761, 850 and 971 rows at 16:05Z because live takes were lower, and not for their sources. Their public files now sit in take-harvest-r26/work/cand. Our start copies sit in take-midm-r26/work/starts.

| queue | scans | seconds | gain before certification | scans that gained 1e-6 or more |
|---|---|---|---|---|
| forensics rect files | 51 | 15640 | 0.0008647 | 18 |
| fresh takes of other lanes | 12 | 3703 | 0.0002733 | 2 |
| raw legs | 34 | 10055 | 0.0001483 | 9 |
| harvest public takes | 9 | 2801 | 6.586e-05 | 4 |
| near files of other lanes | 16 | 2995 | 3.468e-06 | 1 |

Next round:

1. Kick forensics rect compositions first, within minutes of their handoff. Walk every part to the end before the slot. Rect files gave 51 scans, 18 gained 1e-6 or more, 0.000865 before certification in 15640 s. 736 and 909 of the take come from rect files. Five rect rows were lost to parts that left later (546 642 684 694 971).
2. Save every walked record and part file at queue time, and the start record as well. Our 684 left because its start changed with no saved record. Two hours later that gap took our 971 with it.
3. Kick the fresh takes of other lanes and harvest public layouts next. Fresh takes gave 12 scans, 2 gained 1e-6 or more, 0.000273 before certification in 3703 s. Harvest layouts gave 9 scans, 4 gained 1e-6 or more, 6.59e-05 before certification in 2801 s. 453 and 761 hold 3.5e-4 of the take.
4. Continue raw legs only of scans that gained 1e-5 or more. Raw legs gave 34 scans, 9 gained 1e-6 or more, 0.000148 before certification in 10055 s.
5. Settle the prvsiyan descent test before the round. Quench, twoshort and backlog refuse 453 761 818 706 on max centre distance 0.338 to 0.542. Harvest and classfill measure a share of 0.001 to 0.016 within 1e-3, which is an unrelated design. Our 453 and 761 depend on it.
6. Re-enter near/971-midm-r26-k26955-untraced.csv (0.01548181336413279) if the skeptic accepts the walk through the classfill audit of forensics 684-rect sha256 52a68b1649543384 (take-classfill-r26/work/audited/x52a68b164954.json).
7. Run near files of other lanes last. They gave 16 scans, 1 gained 1e-6 or more, 3.47e-06 before certification in 2995 s.
8. Stair-c and invent near files that walk to take-stair-c-r22/near/863-0f92c19d-n stay out (47 skips). They need a rebuild from a clean root before midm can kick them.


## 18. Rounds 27 and 28 (2026-11-14 to 15)

Both agents died early: round 27 at about 23:10Z, round 28 at about 02:25Z on a usage limit. Their drivers ran on, so STATE.txt is the record of both rounds. Neither round wrote this doc or a results table.

Round 27 (tools/midm/round27.py, worker27.py) re-opened the starts that were refused only for the Samanyu-dev seed and certified on the boxes. Its take held 743, 798, 921, 922, 978 and 985. Of 1072 queued jobs, 79 ran. Rect files gave 7 certified n, and re-opened starts gave 20.

Round 28 (tools/midm/round28.py) ran on bar28 until boxA rebooted at 05:38Z. Its take held 540 (9.15e-5, forensics 540-rect) and 743 (1.21e-5, forensics 743-rect). Both are bar29 rows. 978, 971, 993 and 551 were taken and then dropped when other lanes went lower. Of 1919 queued jobs, 210 ran. Every scan that gained 1e-5 or more started from a rect file. 401 rect jobs and 104 fresh takes never ran.

## 19. Round 29 (2026-11-15)

One driver on boxA (tools/midm/round29.py) queued, traced, certified, quenched and published. Box workers (tools/midm/worker29.py) ran midm_scan.py kick and local kick scans: two slots on boxE and one on boxD. New scans started until 11:25Z, and every scan ended by 11:35Z.

Changes of round 29, each with its measured reason:

- Certification is border's finesafe.work on the boxes and on boxA. The control on a round 28 raw find of 381 certified 5.35e-10 of side lower than the floatsafe ladder.
- Rect files and fresh takes get 900 s scans. In round 28, 300 s rect scans gained about their margin and were often still finding at the cap.
- Fresh takes of the lanes that build new geometry run first. A fresh take is the live row, so any gain counts. Fresh takes of the polishing lanes come after the rect files below the bar. Quench 503, backlog 421, rebuild 910 and forensics 991 gave 0 finds in 900 s each.
- From 09:15Z boxD took rect files only. Before that, fresh takes and legs held all three slots, and the 1e-5 to 3e-5 rect band got one scan.
- A leg whose start is already below the bar and every live row runs at once. Our 504 and 907 rows grew this way.
- A certified find up to 3e-6 above another lane's live row still gets its quench. The first 504 quench gained 1.3e-6 of score.
- A start whose exact bytes a handoff WITHDRAW line names is refused, unless a later REINSTATE line names the same bytes. The reader found 182 such withdrawals. It took out our 376, a kick of the forensics 376 take that forensics withdrew at 08:32Z.
- A bar29 row that is a round 28 take counts as a held row, with the source of its round 28 take.tsv row. A live round 29 take row whose walk stops only at a missing record or a cycle is accepted with its own take.tsv source. Banned tokens in the walked evidence still refuse. Before this change our tracer refused backlog 421 and quench 503.
- Carry jobs were new: each started from the lowest round 28 find of a scan that ended within 1e-4 of bar29. They crossed 0 of 11, gaining 0 to 6.5e-6, below each margin. 11 more started on the bar row itself (at -4.9e-11) and were cancelled. All carry jobs stopped at 07:25Z.

What the take shows. Our kicks crossed the live row of n eight times: 907, 747, 991, 376, 752, 965, 788 and 504. Only 747 held to the close.

- 907: a kick of the invent take went 5.4e-6 below it. Then soft and quench went 5.1e-5 lower.
- 752: a kick of the k123 take went 1.8e-6 below border's row. Twoshort ran midm_scan.py on backlog's 752 and ended 4.3e-10 lower.
- 504: two legs from our kick of the k123 take reached 0.02048079395. Twoshort reached 0.02048079398 by the same tool, only 2.8e-11 above us, which is short of the 1e-10 rule.
- 965 and 788: k123 takes appeared with our score to 1e-15. They share 75% and 80% of centres within 1e-9 with our certified finds. A handoff note asks main and k123 to check the recorded ancestry.
- 991: a k123 join went 1.4e-9 below our row at 11:30Z.
- 376: we withdrew it, because forensics withdrew the exact start bytes.

So most of our crossings landed in rows that other lanes then matched or beat within minutes. The team keeps the lower row in every case.

The take holds 1 row: 747, 1.1505e-05 below bar29, with no other live row of 747. Its start is the forensics 747 rect file, sha256 5243af1c. Part B of that rect is the soft 747 row. Soft withdrew that row at 07:22Z and reinstated it at 07:48Z. The start tree also reaches the forensics r24 donor 498-b7ee1a15e91c9b9e23db (prvsiyan share 1.0 at n = 498) and take-k123-r23/917.csv (0.737). The final row has share 0.000, and its start is not public-first. The [results table](../results/midm-r29-2026-11-15.tsv) gives both gains and the score of the input.

| queue | scans | seconds | gain before certification | scans that gained 1e-6 or more |
|---|---|---|---|---|
| fresh takes of other lanes | 29 | 25331 | 3.896e-05 | 6 |
| forensics rect files of round 29 | 10 | 7816 | 3.268e-05 | 4 |
| carry from round 28 finds | 26 | 11654 | 1.595e-05 | 3 |
| legs of fresh takes | 6 | 6014 | 9.03e-06 | 1 |
| legs of rect files | 3 | 2362 | 1.84e-06 | 1 |
| carry legs | 2 | 1563 | 1.7e-07 | 0 |

Next round:

1. Kick the fresh takes of the building lanes (k123, invent, forensics) within minutes, and claim each start in the handoff log first. Measured: 8 of our certified finds crossed a live row. 6 of them were matched or beaten within 10 to 90 minutes, and twoshort and backlog ran the same kick tool on the same takes. One lane per fresh take would free those slots.
2. Keep one box on rect files in the 1e-5 to 3e-5 band. Measured: 10 scans, 4 gained 1e-6 or more, and 747 came from this queue. The band was starved until 09:15Z.
3. Run a contact LP polish of each certified find before the quench. Measured: our 504 lost by 2.8e-11, and border measured 1.5e-10 to 5e-10 of score from the LP on raw layouts.
4. Do not kick the takes of the polishing lanes. Measured: quench 503, backlog 421, rebuild 910, forensics 991, harvest 454 and 582 gave 0 finds in 900 s each.
5. Do not carry round 28 finds. Measured: 0 of 11 crossed, gaining 0 to 6.5e-6, each below its margin.

## 20. Round 30 (2026-11-15)

One driver on boxA (tools/midm/round30.py) queued, traced, certified, quenched and published, as in round 29. Box workers (tools/midm/worker30.py) ran midm_scan.py kick and local kick scans: two slots on boxE and one on boxD. The agent stopped on a usage limit from 13:57Z to 15:42Z. The driver ran on alone, and the revived agent adopted it with no restart. New scans started until 17:25Z, and every scan ended by 17:36Z. The driver queued 2459 jobs and ran 72 of them, plus 16 legs.

The bar. Until 13:31Z the bar was round30-briefs/bar30.tsv. Then main made the round 29 b gate (Kaggle ref 58386105) the bar. The two differ at 3 n only: 376 and 503 are lower in round 29 b, and 582 is higher. The driver kept bar30.tsv, and tools/midm/final30.py checks the take on the round 29 b gate.

Changes of round 30, each with its measured reason:

- Seed-take jobs kicked the bar30 rows that came from round 29 takes of other lanes, 900 s each. The harvest 412 row gained 3.86e-5 in the first scan.
- A box with a kind list takes another kind only when none of its kinds waits. boxD ran rect files first.
- At 15:47Z the held kicks moved ahead of the rect files, through work/pin-k.txt with no restart. Held rows go by their score gap to the per-puzzle board. At that time 2 of 3 finished held kicks had crossed, and about 20 rect scans had crossed 0.
- At 15:49Z the rect files more than 3e-5 above the bar were parked. No rect scan of this round gained more than 2.3e-5.
- Legs written by hand on boxE, in the worker30 leg format. worker30.py writes a leg only when the previous scan gained 1e-6 or more. On 412, leg 1 gained 1.6e-7, so no leg 2 was written. But rebuild kicked the same row with another seed and found 6.9e-6 more. Our leg 2 (seed 777) gained 7.0e-6. Legs 3 and 4 (seeds 877 and 1999) gained 7e-11 and 0.

What the take shows. 3 rows, 4.665e-05 below the round 29 b bar: 412 (4.579e-5), 854 (8.33e-7) and 875 (3.10e-8). At 17:37Z no other live take had a lower row of these n. The [results table](../results/midm-r30-2026-11-15.tsv) gives both gains and the score of each input.

- 412: the start is take-harvest-r29/412.csv, the round 29 b row of 412. Rebuild noted that its tree reaches a public notebook file at a prvsiyan share of 1.000 through that row. By the main 13:32Z ruling, a public file that reaches us only through a held row is held ancestry. The final row has a share of 0.117 within 1e-3.
- 854 and 875: 300 s kicks of the held round 28 b rows. Border, rebuild and backlog claimed kicks of our 854 within 5 minutes.
- 687 was taken at 1.2e-10 below the bar. Backlog then went 7.9e-8 lower with a kick of our row, so we dropped ours.
- 556 was taken at 1.8e-7 and dropped when backlog and twoshort went lower.

Rect files near the bar give back the held row. 333 ended 7.1e-9 above the bar, 737 4e-9 above, 701 5e-8 above and 693 2.9e-11 below. Each of them first gained most of its margin.

| queue | scans | seconds | gain before certification | scans that gained 1e-6 or more |
|---|---|---|---|---|
| forensics rect files | 31 | 24297 | 0.000181 | 13 |
| seed-take | 10 | 8615 | 3.878e-05 | 1 |
| raw legs | 16 | 14824 | 1.411e-05 | 3 |
| held, never kicked | 30 | 8445 | 8.64e-07 | 0 |

Next round:

1. Give every row whose first scan gained 1e-5 or more at least two more seeds, whatever its first leg gained. Measured: on 412, seeds 103, 777, 877 and 1999 gained 1.6e-7, 7.0e-6, 7e-11 and 0. The worker30 rule (a leg only after a gain of 1e-6) stopped after seed 103.
2. Kick the held rows that nobody kicked, by score gap to the board, 300 s each. Measured: 30 scans, 3 crossed (854 8.3e-7, 875 3.1e-8, 687 1.2e-10), and 27 gave 0 or the held row again at 4.9e-11. Each crossing then gets kicked by the follow lanes within minutes.
3. Kick a rect file only when its layout differs from the held row. Measured: 31 rect scans gained 1.8e-4 in total and crossed 0. Four rect files that started 2e-6 to 1.7e-5 above the bar ended within 5e-8 of the held score.
4. Leave the fresh takes of other lanes to the follow lanes. Measured: backlog, rebuild, border and twoshort claimed each fresh take within minutes, and about 30 of our fresh-take jobs waited behind their claims all round.

## 21. Round 31 (2026-11-15 to 16)

One driver on boxA (tools/midm/round31.py) queued, traced, certified, quenched and published, as in round 30. Box workers (tools/midm/worker31.py) ran midm_scan.py kick and local kick scans: two slots on boxE and one on boxD. New scans started until 23:50Z, and every job ended by the 00:15Z deadline. The agent died at 23:14Z on a usage limit. The driver and the box workers ran on to the deadline, and a revived agent closed the round at about 00:07Z. The bar is round31-briefs/bar31.tsv, the held round 30 c file. The [results table](../results/midm-r31-2026-11-16.tsv) holds no row. The driver queued 2134 jobs and assigned 257 of them, plus legs.

Changes of round 31, each with its measured reason:

- Every scan stops at 120 s when no try has moved the side 1e-8 below its start. We measured it on 615 of our scans of rounds 22 to 30. The probe keeps 88% of the side gain in 44% of the slot time. So the gain per slot second doubles (x2.01). The 1e-8 floor is there because a certified held row comes back about 1.2e-9 of side lower, and that counted as a find in the first control.
- A leg follows every find that moves the side more than 1e-6. A scan that gains 1e-5 of score or more also gets a sibling seed. Round 30 measured why: on 412, the second and third seeds gained 1.6e-7 and 7.0e-6.
- Every kick of a start we did not make gets a claim line with the full sha256. A start that another lane claimed in the last 60 minutes waits. Fresh rows of other lanes wait 10 minutes for backlog.
- Pub-near starts are new. A pub-near start is a row of a public file that sits 1e-6 to 1e-4 above bar31. Each one passes the harvest round 31 share audit (tools/harvest31/policy.py) at under 0.4. Each one has a licence of Apache 2.0, CC BY 4.0 or CC0, and shares under 0.9 with our held row. The first 12 came from the jazivxt file of round 31 (tools/midm/pubnear31.py). Then tools/midm/pubnear31m.py read every public file that harvest fetched in rounds 28 to 31: 244 files of distinct size, 4892 distinct rows in the window, over 212 n. It kept 38 new starts below 1e-4 and 43 from 1e-4 to 2.5e-4.
- A scan of a start above the bar stops at 300 s when its lowest find has not crossed the bar (tools/midm/crossstop31.py). Measured first: 812 crossed at 34 s. 503 and 871 made most of their gain by 134 s and 214 s and never crossed. They held a slot for 993 s and 1352 s, plus their legs.
- The 211 held rows that a lane last kicked in rounds 28 to 30 went to the back of the queue. None of them changed between the round 28 b, 29 b and 30 c gathers, so a kick of one is an unchanged seed search. Override 6e measured those at zero. The 115 held rows at the board and the 16 k123 three-way near files went back for the same reason.
- Drop-one starts from a changed public row of n+1 ran on boxD. The 790 start gave 0 finds in 914 s.

What the take shows: no row. The driver certified 7 n below bar31 and quenched each one once from its certified file. Then each one went out, because another lane held a lower live row or because of a share refusal:

- 686: 4.963e-4 below the bar, from a kick of forensics' fresh 686 take. Backlog kicked our row and went 5.4e-8 lower. Its live 686 descends from our file. STATE.txt holds the full ancestry: the roots are the held round 30 c row of 687 and the round 23 a row of 739.
- 812: 3.606e-5 below the bar, the first pub-near start (the jazivxt file). Quench and backlog kicked our row and went 3.2e-7 lower.
- 421: 1.822e-5 below the bar, a new seed on invent's 421 take. Backlog kicked our row and went 9.4e-7 lower.
- 454: 9.978e-5 below the bar, from a rect file. Classfill had certified a row 2.2e-13 lower 58 minutes before.
- 464: 7.30e-5 below the bar, from a rect file. Backlog's 464 is 2.07e-5 lower.
- 909: 1.885e-6 below the bar, from a rect file. Twoshort's 909 is only 2.8e-11 above ours. That is less than 1e-10, so our row does not count.
- 972: 2.776e-5 below the bar, from a pub-near start. It was refused at publish, because the final row shares 0.460 with the prvsiyan 1105 row (harvest31 policy.audit, override 3).

The live rows of 686, 812 and 421 that backlog and quench built on our files are 5.519e-4 below bar31. Our own rows of those n were 5.506e-4 below it.

The tracer refused 40 starts before assign. 7 of those refusals (6 n: k123 three-way near files and forensics' 800) came from a TypeError in sources27.trace on a source cell that holds a list. They did not come from a banned source.

The queues below come from the final31.py dry run at 00:10Z. Every scan had ended by 00:05Z.

| queue | scans | probe stops | seconds | gain before certification | scans that gained 1e-6 or more |
|---|---|---|---|---|---|
| public rows 1e-6 to 1e-4 above the bar | 77 | 33 | 20220 | 0.0003493 | 6 |
| fresh takes of other lanes | 48 | 44 | 8079 | 0.0001428 | 2 |
| forensics rect files | 46 | 23 | 13549 | 6.602e-05 | 4 |
| raw legs | 23 | 20 | 3810 | 7.091e-06 | 1 |
| held, never kicked | 7 | 4 | 519 | 4.891e-11 | 0 |
| round 30 c rows from takes (held) | 28 | 26 | 3141 | 0 | 0 |
| our round 30 rows (held) | 4 | 4 | 481 | 0 | 0 |
| drop1 from a public n+1 | 3 | 0 | 1562 | 0 | 0 |
| control | 1 | 1 | 120 | 0 | 0 |

Next round:

1. Kick the fresh certified takes of other lanes within minutes: 900 s, with the 120 s probe. Measured: 48 scans, 2 paid, and both crossed the bar (686 at 4.96e-4, the biggest row of the lane, and 421 at 1.8e-5). At 1.8e-8 of score per slot second, this is the best of our queues. The follow lanes then polish our row by 5e-8 to 9.4e-7.
2. Run pub-near starts from changed public files only, with the 300 s cross-stop. Measured: 77 scans, 6 paid, and 3.49e-4 gained on their starts in 20,220 s. Two crossed: 812 certified at 3.6e-5, and 972 was refused at a share of 0.460. Run the share audit on a start's best find before its legs. Drop a start whose share is already 0.4 or more at 1e-2.
3. Kick rect files only when they sit below the bar. Measured: 46 scans, 4 paid, and 6.6e-5 gained on their starts. They crossed at 454, 464 and 909, but other lanes held the same layout or a lower one.
4. Fix sources27.trace for source cells that hold a list. Run a control first: a banned token inside a list must still refuse. Measured: 7 refusals over 6 n came from that TypeError.
5. Stop the queues that measured zero. Seed-take kicks: 28 scans, 0. Our own held rows: 4 scans, 0. Drop1 from a public n+1: 3 scans in 1562 s, 0. Held rows never kicked: 7 scans, 4.9e-11.
6. Log a publish refusal once per n. The 972 refusal went into STATE.txt 127 times.

## 22. Round 32 (2026-11-16)

One driver on boxA (tools/midm/round32.py) queued, traced, certified, quenched and published, as in round 31. Box workers (tools/midm/worker32.py) ran midm_scan.py kick and local kick scans: two slots on boxE and one on boxD. New scans started until 16:50Z, and every job ended by the 17:15Z deadline. The driver stopped at 17:23Z. The bar is round32-briefs/bar32.tsv, the held round 31 b file. The [results table](../results/midm-r32-2026-11-16.tsv) holds no row. The driver queued 361 jobs and assigned 141 of them. 116 scans wrote a done record (76 on boxE, 40 on boxD), and every record was on boxA before the box scratch was removed.

Changes of round 32, each with its measured reason:

- sources27.trace reads a source cell that holds a list as its JSON text (commit 0928d20). In round 31 that cell raised a TypeError and refused 7 starts over 6 n. Control: the 7 starts now walk to the held round 30 c row. A list cell that names prvsiyan/squares-verified-best-of-1105 still refuses.
- A public-first job gets the frozen share measure of the assembler (take-assemble-r31/scripts/share31.py) on its best find before its legs. A find at 0.4 or more at 1e-3 or 1e-2 writes no leg. Control on 686: the 1105 row, swapped and shifted, reads 1.0. A plain grid reads 0.0.
- Pub-near starts come only from public files that changed in round 32 (tools/midm/pubnear32.py, every 20 minutes until 16:30Z).
- A fresh take waits 10 minutes for the follow lane. Bytes that another lane claimed in the last 60 minutes wait as well. At 11:33Z the first step skipped the claim check and kicked forensics' own 909 and 971 takes 24 s after forensics claimed them. That was fixed at 11:37Z.
- A take of a polishing lane (border, backlog, harvest, classfill, soft) is parked (commits d2b0676 and eb2b2de). First only the lowest live row was parked. Then k=50263 kicked backlog's 866 when it was 2.2e-5 above k123's live 866. It certified 6.18e-5 below bar32 but stayed above the live row, so since 13:53Z every polishing-lane take is parked.
- A trace leaf that equals the held round 31 b row value for value is that held row (commit 9405f4c). Border's held copies name the held file only in prose, and the tracer refused its 910 and 864 chain legs. Controls: border's held 910 and 864 match. A copy with one x moved by 1e-9 does not match, and neither does the 864 file read as 910.
- Filler held-gap2: border's paying kind of round 31 (900 s, no probe, two seeds) on the held rows with the largest board gap that no lane claimed. A held-gap2 job first ran with the stop6 rule, and the first 18 ended in 8 to 53 s. Since 12:01Z they run the full 900 s. Since 12:29Z they also wait on other lanes' held claims (commit 5ef78b3).

The 45-degree lattice rows. Part of the board-gap list is made of rows whose side is a + b*sqrt(2)/2. Every tilted square in them sits at 45 degrees: 785 786 842 843 901 902 962 963 678 677 626 730 731 964. The full 900 s kicks of 785 and 786 came back to the start side on 568 of 586 tries and on 644 of 675 tries. A kick cannot move such a row, so their 24 queued seeds were cancelled at 12:47Z.

What the take shows: no row. The driver certified 4 n below bar32 (finesafe 2.2e-11). Each one then had a lower live row in another lane:

- 909: 7.73e-5 below the bar after one fq quench (5.84e-5 before it), from a kick of forensics' fresh 909. Backlog's live 909 is 6.28e-5 lower.
- 866: 6.18e-5 below the bar, from backlog's 866. It was not quenched, because k123's live 866 was already lower. Backlog's live 866 is now 1.61e-5 lower.
- 973: 2.32e-5 below the bar, from a forensics re-opened endpoint. The fq quench found no lower side. Forensics' live 973 is 1.44e-9 lower.
- 971: 6.84e-6 below the bar, from a kick of forensics' fresh 971. The fq quench found no lower side. Backlog's live 971 is 1.87e-5 lower.

The tracer refused 29 starts over 16 n before assign. 5 of them were classfill near files of 849 whose walked evidence names the bytes ae81705f that harvest withdrew. 14 public-first starts were skipped at a prvsiyan 1105 share of 0.420 to 0.738. 7 starts were skipped because they share 0.9 or more with a live row (the same layout). 142 queue waits came from claims of other lanes, over 57 n.

The queues below come from final32.py verify at 17:32Z. The 909 and 971 scans were cancelled at 11:35Z after their finds, so their done records carry no gain. The table therefore does not count those two finds.

| queue | scans | probe stops | seconds | gain before certification | scans that gained 1e-6 or more |
|---|---|---|---|---|---|
| fresh takes of other lanes | 25 | 22 | 4341 | 7.388e-06 | 1 |
| near files of other lanes | 12 | 3 | 1282 | 1.116e-08 | 0 |
| held rows by board gap, two unprobed seeds (filler) | 55 | 0 | 43056 | 1.811e-09 | 0 |
| public rows from changed files | 22 | 7 | 2668 | 0 | 0 |
| raw legs | 1 | 1 | 120 | 0 | 0 |
| forensics rect files | 1 | 1 | 120 | 0 | 0 |

Next round:

1. Keep the fresh takes of other lanes that nobody claimed after 10 minutes. Measured: this is the only queue that crossed the bar (909, 971 and 866). But the follow lanes polished each crossing below ours within the round, so the lane step gave no live row.
2. Stop the held-gap2 filler. Measured: 55 scans in 43,056 s over 23 n gave 1.8e-9 and no find.
3. Never kick a 45-degree lattice row. Measured: 568 of 586 and 644 of 675 tries came back to the start side. Such a row needs a different construction, not a kick.
4. Run pub-near only when a harvest run brings changed files. Measured: 22 starts from 5 runs, 0 finds, 5 cross-stops at 300 s.
5. Write the find into the done record of a cancelled scan, so that the queue table counts it. Measured: the 909 and 971 records carry no gain.
