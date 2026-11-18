# Engine avenue (2026-11-10)

We looked for a search engine that none of the lane's tools resembles. Six experiments ran on boxA. One gave a certified gain of 0.00033 on 68 n. The other five found nothing, and each one says why.

## Results

| experiment | file | what it measures | result |
|---|---|---|---|
| fq re-quench of every held packing | `engine_polish.py` | Evan Daniel's `fq quench` (all squares free) on each of our 1,000 packings, then the lane's `floatsafe.work` | 68 n smaller, total gain **0.000330**, 25 of them above 1e-6 each. Rows: [`results/engine-polish-2026-11-10.tsv`](../results/engine-polish-2026-11-10.tsv) |
| E1 rigid patch moves, fixed side | `engine_patch.py` | n=498 at side 22.80331 (0.0005 below ours), 1,238 moves in 60 s | starts at 485 of 498, reaches 487 |
| E1b rigid patch moves, smallest side as objective | `engine_sstar.py` | n=454, 498, 544, 240 s each, about 650 moves each | 0 improving moves in all three |
| E2 rigid patch generator | `engine_lens.py` | n=498 (2 seeds) and n=454, 240 s each, about 10,000 states each | 484 and 485 of 498, 442 of 454. The plain grid holds 484 and 441 |
| E3 lattice hops, tolerant refill, fq | `engine_hop.py` | n=498, 300 s, 268 hops, 89 quenches | best side 22.803695, the same value that fq alone gives. The median quench ends at 23.0 |
| E4 graft a donor's patches and grow them | `engine_graft.py` | 544 from 498 (300 s, 4,653 hops) and 498 from 454 (control) | 541 of 544 and 497 of 498. No quench ran. The control failed |
| graft scan, exact refill | `engine_scan.py` | 417 trailing n, donors n-8 to n+3, side 2e-5 below ours, 3,906 fills | 0 hits. 333 targets end 1 square short. Rows: [`results/engine-scan-2026-11-10.tsv`](../results/engine-scan-2026-11-10.tsv) |

## The fq re-quench

Submitted 2026-11-10 11:15Z as ref 58198537: `gather/engine-2026-11-10a.csv` on boxA (SHA-256 `28482ebd…`). The gate was GREEN at 22.2145943790 against the last submitted file, with 68 n moved and a smallest gap of 2.206e-11 ([`results/engine-gate-2026-11-10a.json`](../results/engine-gate-2026-11-10a.json), gate dir `gate/cand-engine-1110a`). Kaggle's public score is **22.2145943790**. The score before was 22.2149239905. The next gate run must use `--last gate/cand-engine-1110a`.

`fq quench` took our n=498 from 22.803808951 to 22.803695436 in 1.6 s. The new side has the same fractional part as our n=454 (21.803695436), so the held 498 was an unfinished copy of that family. The sweep over all n found 67 more cases. The largest are n=979 (31.773511 to 31.771997), 553, 695, 865 and 464. All of them stay above the board's side.

Controls: n=10 at its known optimum gave no win, and five other n gave none. Every win passed `floatsafe.work`, which runs the official metric as written and after a pandas read, with 2.2e-11 clearance. A second pass over the winners added 3.5e-6.

The sweep took about 2.5 hours of wall time on 2 to 3 workers. `drive.py` gained 0.0002 in two days on three boxes.

To repeat it after a harvest: `engine_polish.py OUT --all --jobs 3 --sub NEW.csv`, then `engine_assemble.py NEW.csv CAND.csv OUT`, then the gate.

## The structure of the held packings

The large packings are not a diagonal seam. Each one holds two tilted patches, one near the top-left corner and one near the bottom-right corner, between two large upright blocks. n=498 has patches of 84 and 52 squares. n=454 has two of 52.

Three measured facts shaped the experiments:

- The waste `L^2 - n` is close to `0.95 L` for every fractional part. For m=22 it runs from 22.3 to 19.4 on the board, and ours is 0.2 to 1.0 higher. So the board leads by 2% to 5% of the waste on almost every n, with no single family behind it.
- A patch is a stack of rows that slide along each other. A fit to one square lattice leaves a residual of 0.25 to 0.29. A fit to rows with a free slip per row leaves 0.016 on the rigid patch of 498 and 0.072 on the relaxed one.
- In n=454 all 104 tilted squares sit at atan(1/2) = 26.565 degrees. At that angle the lattice vector (1, 2) of the patch is vertical. The patch then has straight vertical and horizontal faces, and upright rows end flush on them.

## Why the five searches found nothing

- The packings are jammed against whole patches too. A side 0.0005 smaller costs 13 squares at once in n=498, because many wall-to-wall chains of squares are tight at the same time. Turning, shifting or slipping a patch as one body does not shorten all of them.
- The count of the exact refill is flat almost everywhere. A search that only sees the count shrinks the patches away and ends at the plain grid (E2).
- A tolerant refill reaches n only very near the held packing. With an overlap tolerance of 0.15 a hop of 0.2 degrees already ends 1 or 2 squares short. The few starts that reach n quench to the integer side 23.0.
- Growing a family by one step needs more than a new line of squares. From 454 to 498 one patch grew from 52 to 84 squares and its angle changed to 23.1 degrees with a spread of 1.5 degrees.

## What is still open

- A patch model with one angle per row. The relaxed patches have a 1.5 degree spread that the row model with one angle does not hold.
- `fq` with other flags on the 349 n that still trail the board by one square. The sweep used the default flags and Evan's POLISH_DEEP flags only.
- The 0.8037 family (n=454 and 498 at m+0.803695436) predicts n=544 at 23.8037 against our 23.8238. Neither E4 nor the scan built it.

## Code

All files are in the lane root with the prefix `engine_`. They import Evan Daniel's MIT packer (`fillfast`, the `fq` binary) from its clone under `ext/evand` in the box dir, and copy none of it. `SQ_BOX` sets the box dir and `SQ_BEST` sets the submission that they read.

## Summary

- The only gain is a re-quench of our own packings with `fq`: 68 n, 0.000330 in total, all certified by `floatsafe`.
- Whole-patch moves, a rigid patch generator, lattice hops with a quench, grafts with growth, and a graft scan over 417 n found no square.
- The held packings are two tilted patches of sliding rows between two upright blocks. The diagonal seam that seamcell and bandseed assume is not there.
- Next: run `engine_polish.py` after each harvest. It costs about 2.5 hours on 3 workers.
