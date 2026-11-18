# Avenue: gap (round 25, 2026-11-13)

This lane builds fresh designs for the counts where we trail the best known side the most. A kick of a held layout is not its job. It moves whole tilted patches between layouts, or adds squares to them, and counts with the exact upright refill.

Words used here. The *base bar* of n is the lower of the held file `gather/round23-2026-11-13b.csv` (gate dir `gate/cand-round23-1113b`) and the frozen round 24 takes. A *patch* is a connected group of tilted squares (more than 5 degrees off upright). The *refill* is `fillfast.fill(L, T, mode='exact')` of Evan Daniel's packer: the largest set of upright squares that fits in the box of side L around the tilted squares T. A *count* is the number of squares of T and its refill. A count of n or more at a side below the base side of n is a layout of n below the bar.

## Round 25

### 1. The gap

`main-r17/gap-by-n.tsv` holds the per-puzzle board of 2026-11-09. Set against the base bar, 366 n trail the board, by 0.0802 of score in all. The largest gaps are 791 (0.00100), 367 (0.00088), 972, 793, 908, 741, 686, 911, 973 and 328 (0.00072 to 0.00081). The counts just above a square (k = 1 and 2) trail by 0.0085 over 20 n. 144 n with a gap had no take row in rounds 22 to 24 and at most 10 mentions in their STATE files. They trail by 0.0275.

The board side of a count often equals a side we hold at another count. The board's 854 sits at 29 + 12/17, the side of our 853, 796, 740 and 686. Those four are two blocks at 22.62 degrees (the 5-12-13 angle). So the board holds one square more than we do at m = 29 with that side. The same check finds 456, 585 and 534.

### 2. Three tools and their controls

| tool | what it does | positive control | result |
|---|---|---|---|
| `gap_grow.py` | the tilted squares of the held n - j, placed in the box of the base side of n (as they are, dilated, or moved to the walls they touch), refill, count | `ctl`: the held 853 counts 853 at its side and 845 at 0.002 below | 2091 refills on 366 n with j = 1, 2: no count reached n; 228 n were one short |
| `gap_walk.py` | a walk on the tilted patches at a fixed side: a full sweep of lattice adds, then moves that keep the count (slide, turn, delete, a whole line); `--scan` first moves each patch over a grid of 0.1 | 367 less one edge square counts 366; the walk restores 367 in 5 refills. 367 with its band moved by (0.3, 0.2) counts 349; the scan restores 367 in 26 refills | 12 starts on 854, 791, 972, 367 and 741: no start gained a square |
| `gap_shift.py` | the patches of the held d at m + 1 moved by whole cells into the box one size smaller, squares outside or on another square dropped, refill, counted at the base side of every n of a window of 11 | the held 980 gives 918 at the base side of 918 | see section 3 |

The walk was red twice before its control passed. The lattice site beside a square of a relaxed band is up to 0.04 off the hole, so the first version refused every add. The second version moved the new square at random and missed holes narrower than its step. The third pushes the new square out of each overlap by the smallest move, and the control passes.

### 3. Results

RESULTS-PLACEHOLDER

### 4. What did not work, measured

- Growth at the larger side alone gives nothing. The refill around the fixed tilted squares of n - 1 never reached n at the base side of n (2091 refills, 366 n).
- The count walk gives nothing at m = 19 to 31. Each add of a tilted square displaces at least one upright, and the moves that keep the count drift.
- A third copy of a 22.62-degree block on 853 loses 13 to 20 squares. A block pays only where the four upright grids around it meet in the right phase.
- The 918 built from 980 jams at 30.776257 under fq and under the polish flags. The smallest side at which its refill holds 918 is 30.779288, and fq from there ends at the same side.

## Files

| file | what it does |
|---|---|
| [`gap_grow.py`](../gap_grow.py) | `ctl`, `run` (growth at a larger side), `finish` (floatsafe, one fq quench from the certified file, floatsafe) |
| [`gap_walk.py`](../gap_walk.py) | the count walk and the patch scan; `n:j` starts from the held n - j, `n@d` from the patches of the held d |
| [`gap_shift.py`](../gap_shift.py) | the patches of each donor moved into the box one size smaller, counted over a window of n |
| [`gap_take.py`](../gap_take.py) | the take dir: the bar check against the held file and every round 24 and live round 25 take, and the source of each donor row |
| [`results/gap-r25-2026-11-14.tsv`](../results/gap-r25-2026-11-14.tsv) | every certified or near layout of this round |

On boxB, `<scratch>/squares-gap` held the job logs during the round. The take dir is `<scratch>/bounties-squares/take-gap-r25` on boxA.
