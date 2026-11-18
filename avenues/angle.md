# Avenue: angle (2026-11-10, evening)

**Result: public score 22.2145729630 → 22.2000677210 with the day's public harvest (2026-11-10 18:35Z, ref 58211343, 144 n, 0.0145). After the outline avenue's two files, four more polish passes took it from 22.1998270133 to 22.1998073897 (2026-11-10 22:52Z, ref 58216356, 24 n, 0.0000196). The patch generator failed its control: 451 squares where we hold 454. It was not run over all n. The rational-tangent idea does not hold for the patches that matter.**

This avenue had three jobs: merge the layouts published since the last harvest, polish what moved until a pass gains nothing, and build the one idea the [rowangle avenue](rowangle.md) left open, a patch generator with the angle as the main variable.

Words used here: the side is `L = m + f` with `m` whole. A "patch" is a connected group of tilted squares. "Exact refill" is Evan Daniel's `fillfast.fill` (MIT): the largest set of upright squares around given tilted squares. `fq` is his all-free quench. "The base" is the best certified packing per n that the lane holds.

## 1. The harvest

`harvest_delta.py` fetched every public notebook and dataset that was new or re-run since 2026-11-09 (26 notebooks, 5 datasets). `harvest_merge.py` compared them per n with our file. Every n the merge took then went through the lane's `floatsafe` (2e-11 clearance), and we kept only the n that still certified below ours.

| | n | gain of score |
|---|---|---|
| kept after `floatsafe` | 144 | 0.014505 |
| credited to `prvsiyan/a-square-deal-research-to-verified-packings` | 103 | 0.011221 |
| credited to `malyshevdanil/squares-in-squares-living-atlas-of-tight-packings` | 41 | 0.003284 |

Both notebooks are unions of other public files. Where several sources hold the same layout, the merge credits the first one it reads. Per n: [`results/angle-harvest-2026-11-10.tsv`](../results/angle-harvest-2026-11-10.tsv).

`engine_assemble.py` put the 144 n on `gather/rowangle-2026-11-10b.csv`, as `gather/angle-2026-11-10c.csv` on boxA (SHA-256 `4acbdd86…`). The gate was GREEN at 22.2000677211 against `gate/cand-rowangle-1110b`, 144 n moved, smallest gap 2.206e-11 ([`results/angle-gate-2026-11-10c.json`](../results/angle-gate-2026-11-10c.json)). Submitted 2026-11-10 18:35Z as ref 58211343. Kaggle's public score is 22.2000677210.

## 2. Polish until a pass gains nothing

`engine_polish.py` quenches each n with `fq` and keeps a result only when `floatsafe` and the official metric certify a smaller side. Each pass runs only on the n that moved in the pass before.

| pass | n tried | n smaller | gain of score |
|---|---|---|---|
| 1, on the 144 harvest n | 144 | 42 | 0.000192 |
| 2, on the winners of pass 1 | 42 (stopped early, then covered by pass 3) | 2 | 0.0000000075 |
| 3, on the 24 n that still beat the base | 24 | 5 | 0.0000000034 |
| 4, on the winners of pass 3 | 2 of 5 (stopped by a time limit; 910, 934 and 997 were not reached) | 2 | 0.0000000015 |

Three n carry pass 1: 543 (0.000148), 497 (0.000024) and 989 (0.000019).

The outline avenue ran the same quench on the same harvest n while pass 1 was running, and it submitted first. Its file `gather/outline-2026-11-10b.csv` already holds 18 of the 42 wins of pass 1, at the same side to ten digits, n = 543 and 497 among them. So we compared per n and took the smaller side: 24 n of ours still beat that file, by 0.0000196 together. n = 989 is 0.0000193 of it.

`engine_assemble.py` put the 24 n on `gather/outline-2026-11-10b.csv`, as `gather/angle-2026-11-10d.csv` on boxA (SHA-256 `1a0cb7fe…`). The gate was GREEN at 22.1998073897 against `gate/cand-outline-1110b`, 24 n moved, smallest gap 2.206e-11 ([`results/angle-gate-2026-11-10d.json`](../results/angle-gate-2026-11-10d.json), gate dir `gate/cand-angle-1110d`: the next gate run uses `--last gate/cand-angle-1110d`). Submitted 2026-11-10 22:52Z as ref 58216356. Kaggle's public score is **22.1998073897**. It was 22.1998270133.

Per n and pass: [`results/angle-polish-2026-11-10.tsv`](../results/angle-polish-2026-11-10.tsv).

No pass reached zero: pass 4 still moved 2 n by 1.5e-9. We stopped there, because from pass 2 on a pass is worth less than 1e-8, which is below anything that changes a rank. Pass 1 pays because the layouts are fresh.

## 3. The rational-tangent idea

The idea: the tilt of a patch sits at `atan(p/q)` for small whole `p` and `q`. If so, a generator would be a small discrete search over `(p, q, patch shape)`.

`angle_scan.py` lists every patch of a file with its angle and the nearest fraction. On the base after the harvest: 812 patches of 4 squares or more, on 547 n.

| fractions | tolerance | patches that hit | a uniform angle would give |
|---|---|---|---|
| q ≤ 6 | 0.005° | 195 of 812 (24.0%) | 0.3% |
| q ≤ 6 | 0.1° | 234 (28.8%) | 5.2% |
| q ≤ 8 | 0.005° | 196 (24.1%) | 0.5% |

The rate is 80 times what chance gives, but the hits are four angles:

| tan | angle | patches within 0.005° | where |
|---|---|---|---|
| 1 | 45° | 151 | all sizes; a 45° block is a known structure and no generator is needed to find it |
| 3/4 | 36.87° | 30 | all in patches of 10 to 19 squares |
| 1/2 | 26.57° | 7 | patches of 40 squares or more |
| 1/3 | 18.43° | 7 | patches of 40 squares or more |

Without the 45° patches, 44 of 654 patches hit (6.7%), on 26 n. Of the 578 patches of 40 squares or more, 14 sit at a rational tangent other than 1. The file JoeGun published on 2026-11-10 reads the same: 202 of 824 patches, 159 of them at 45°. Rows: [`results/angle-scan-2026-11-10.tsv`](../results/angle-scan-2026-11-10.tsv).

The control pair shows both cases. In 498 the patch of 52 squares is at 26.5651° (tan 1/2) and the patch of 87 is at 22.70°, which is no small fraction. In 454 the patches are 54 squares at 26.5651° and 68 at 27.10°.

**So the idea does not hold as a rule.** A rational tangent is one angle a patch can lock to. Most large patches sit at an angle that follows from the side.

## 4. The flush tilt

The next candidate: a row of `c` tilted squares that spans a slot of width `c − 1 + f` has one tilt, the root of `c·cos θ + sin θ = c − 1 + f`. With this the tilt is not a variable. It follows from `f` and the row length.

Measured on the held patches, by the patch class of the structure avenue:

| class | patches | within 0.1° of a flush tilt | a uniform angle would give | within 0.3° | uniform |
|---|---|---|---|---|---|
| none | 214 | 18% | 9% | 36% | 25% |
| mixed | 244 | 25% | 6% | 44% | 19% |

It is a real signal, two to four times chance, and it is weak: three patches in four are more than 0.1° from every flush tilt.

## 5. The generator and its control

`angle_gen.py` builds a layout from two slot patches: a vertical one near the top-left corner and a horizontal one near the bottom-right corner. A patch is a stack of flush rows along a wall. Its shape is discrete: the row length `c`, the wall offset, the number of rows, where the stack starts, the jog pattern (a row slides one whole column) and a taper at both ends. One real number, `dth`, takes the tilt below the flush value. The exact refill places the uprights and counts the squares. `opt` is a hill climb over the shape from random starts.

**The control.** We hold 454 squares at side 21.796670 and 498 at 22.803695. The generator must reach 454 at `m = 21`.

| run | side | hill climbs | best count | we hold |
|---|---|---|---|---|
| first run | 21.803695 | 6 | 449 | 454 |
| longer run, 2,500 evaluations per climb | 21.803695 | 12 | 451 | 454 |
| with a drift mode (the patch moves one column every few rows), 1,500 evaluations per climb | 21.796670 | 8 | 450 | 454 |
| `prune` (drop single tilted squares while the count rises) on the best layout of that run | 21.796670 | 1 | 450, no square dropped | 454 |

**The control failed.** The best of 26 climbs is 3 squares short.

The loss is in the patch shape, not in the refill. The exact refill around the tilted squares we hold returns 453 of 454, and 498 of 498. Around the generator's best tilted set it returns 450. The held 454 has 122 tilted squares and the generator's best has 136. A read of the held rows shows what the model lacks: the rows of one patch do not share a tilt (24.0°, 25.6°, 27.9° and 28.9° in neighbouring rows of the 68-square patch), and rows are one square short where the patch moves a column. A stack of equal flush rows cannot make that.

Six more points, to see whether 454 is a bad case. It is not:

| side | best count over `m²` | we hold |
|---|---|---|
| 12.80 | 2 | 6 |
| 16.80 | 5 | 9 |
| 26.80 | 10 | 16 |
| 30.80 | 10 | 19 |
| 16.65 | 0 | 4 |
| 26.65 | 1 | 8 |

The generator is 4 to 9 squares below the base at every point, and the gap grows with the side. A run over all n would return no layout that beats ours, so we did not run it. Rows: [`results/angle-gen-2026-11-10.tsv`](../results/angle-gen-2026-11-10.tsv).

## 6. What this says

- The angle is not the main variable of a good patch. Within one held patch the rows differ by up to 5°, and the count depends on that spread and on single missing squares.
- Two results now agree. The rowangle avenue moved one row of a held patch 885 times and gained no square. This avenue built patches from equal rows and came out 3 to 9 squares short. A held patch is an irregular object. A regular model of it loses squares, and local moves on it do not gain any.
- What pays is the same as in the outline avenue: a fresh public layout, quenched on the day it arrives. The harvest gave 0.0145 and its first polish pass 0.0002. Every pass after that gave less than 1e-8.

## Files

| file | what it does |
|---|---|
| `angle_scan.py` | Lists every tilted patch of a submission with its angle, the nearest `p/q` and the distance. Prints the hit rates beside the rate of a uniform angle. |
| `angle_gen.py` | The slot-patch generator: `theta` (flush tilt), `count`, `opt` (hill climbs), `prune`, `build` (refill, keep N, quench) and `held` (the squares over `m²` that a file holds at each fractional side). |
| `angle_take.py` | Passes every n a harvest merge took through `floatsafe` and keeps those that still certify below the held score. `angle_take.py MERGED_DIR BASE.tsv OUT_DIR`. |
| `angle_pick.py` | Per n, compares the base with per-n files from several dirs and copies the smallest side that beats the base. `angle_pick.py BASE.csv OUT_DIR DIR [DIR...]`. Use it before `engine_assemble.py` when two agents changed the same n. |

`angle_gen.py` imports Evan Daniel's MIT packer from the lane's clone and copies none of it. `SQ_BEST` is the base submission, as in the other avenues.

## Summary

- **Score:** 22.2145729630 → 22.2000677210 with the harvest (ref 58211343), and 22.1998073897 now (ref 58216356). The gate dir is `gate/cand-angle-1110d`.
- **Polish:** four passes. The last three gave less than 1e-8 each, and pass 4 did not finish 3 of its 5 n. 24 n beat the outline avenue's file by 0.0000196 in total, almost all of it n = 989.
- **Rational tangents:** 24% of patches hit one, but 151 of the 195 are at 45° and only 14 of the 578 large patches sit at another fraction. Not a basis for a generator.
- **The generator failed its control:** 451 against 454, and 4 to 9 squares short at six other sides. It was not run over all n. The held patches are irregular in tilt and in row length, and a model of equal rows loses squares before any search starts.
- **Next:** the daily harvest, with one `fq` pass on every n it brings in, on the same day. No build idea is left open in this avenue.
