# Avenue: methods (2026-11-11)

**Result: 5 n certified below the held file, 0.0000990 of score, from `methods_soft.py`, our CPU version of the public island GA. n = 701 carries three quarters of it. The contact LP (`methods_lp.py`) passes its control and is dry as a sweep. Nothing was submitted from here; the take dir is ready for the gate.**

This avenue had one job: read how the public notebooks that lead the scene find their packings, find the methods the lane does not have, build the one or two with the best measured yield as our own code, and prove each on a control before it runs on our file.

Words used here: "the held file" is `gather/harvest-2026-11-11a.csv` (public 22.1947113952). A "child" is one packing made by one move and then relaxed. "Soft-free" means the overlap energy of a packing is below `1e-10 · n` in a box smaller than its legal side: the squares overlap by a few millionths. "Legal" means certified by `floatsafe` at 2.2e-11.

## 1. What the public notebooks run

We pulled the source of each notebook with the Kaggle API and read it as data. Nothing fetched was run. The sources are in `take-methods-r7/src` on boxA.

| notebook | what it is | optimiser and moves | measured yield | do we have it |
|---|---|---|---|---|
| jazivxt/boxed-in-sub | 3 cells. It copies `submission.csv` from the author's dataset `jazivxt/boxed-in` | none published. The text names no method | 37 n in our harvest of today | the data, through the harvest |
| lucifer19/think-select-reclose | a merger with an audit per stage. 21 stages, each a set of whole-puzzle replacements from public outputs | none. The stage of 2026-11-10 takes 162 n from public files | 0.0006 per stage, all from other notebooks | yes: `harvest_merge.py` and the gate |
| kmmmvs/squares-public-merge-daily | a daily merge of 30 notebooks and datasets | none in this notebook | 7 n in our harvest of today | yes |
| busyaprime, "sacred geometry of 1000 squares" | a merge of 1,600 public files, plus the author's dataset of `fq`-quenched packings (11 n) | Evan Daniel's `fq quench` on public layouts | 5 n in our harvest of today | yes: `engine_polish.py` |
| malyshevdanil, living atlas | a merge. Its own CUDA L-BFGS search and contact LP (from lightningv08's public notebook) are in the source, but the text says public packings have since beaten all 60 of its own gains | soft energy on a GPU, then a contact LP | 0 own n left in version 128 | merge: yes. LP: now `methods_lp.py` |
| penguin069, public certified union | a replay of a certified file. Its text names the experiments | `fq` on module geometry; an exact DP over a bank of 4,793 donors (the fault-line DP class); two "pressure" experiments with softened solves | 8 n, 0.000173 from `fq` and the DP. The pressure experiments kept no gain | `fq`: yes. DP: yes, through alex chilton's kit (`outline_gadget.py`), and it is dry on the pool |
| jonathan1506 (JoeGun), stretch, fault-line DP, fq quench | the one full pipeline write-up | merge, fault-line DP, stretch, `fq`, then a fixed-angle LP in HiGHS | 113 n ahead of the public best, 0.0035: 92 by polish, 16 by flipped arms, 5 new layouts | all but the LP. LP: now `methods_lp.py` |
| nilanjansaha123, GPU seam DP + soft-rigid + HiGHS | the best public notebook score on 2026-11-11 (22.19487) | closures (cut a slab, expand, drop a square), a global rotation of the box, fault-line DP, a kink-aware free-angle sequential LP, CUDA L-BFGS with a soft-to-rigid continuation, regional basin hopping | not stated per stage | closures: our file is closed (0 of 999 n break `L(n) ≤ L(n+1)`). Global rotation: 0 of 1,000 n gain. Sequential LP: now `methods_lp.py` |
| grennwolf, "top-1 santa 2025" | an island genetic algorithm on two T4 GPUs, after Jeroen Cottaar's Santa 2025 solution. The full source is in the notebook | 8 islands of 64 packings, each island in its own box below the best side; 960 children per generation, one move each; CUDA L-BFGS on the overlap energy; a float64 ladder to legalise; a fixed-angle LP at the end | its own log: 61 improvements on 5 n, **0.00096 of score in 41 minutes** on 2 × T4 with 10 processes. The author reports 37 of 342 visits with a find on an RTX 5090 | **no. Now `methods_soft.py`** |

`cshara/squares-in-squares-current-best` does not exist under that name: the API answers "Not found" for the notebook and for the user.

Two things follow from the table.

- **Most of the leading notebooks are mergers.** The methods that make new packings in public are four: `fq` on fresh layouts, the fault-line DP, the stretch, and the island GA. The lane had the first three. Each of them is dry on our file ([engine](engine.md), [outline](outline.md), [rowangle](rowangle.md)).
- **The island GA is the one method we did not have, and it has the best measured yield in public**: 0.0014 of score per hour of two T4 GPUs on fresh layouts. The fixed-angle LP is the second gap: every pipeline ends with it.

## 2. `methods_lp.py`: the contact LP, with free angles

The public LP freezes the angles. Every near pair keeps the separating axis it has now, and a linear programme moves all centres at once to the smallest box. With frozen angles the constraints are exactly linear, so the result is a valid packing.

Ours adds the angles as a sequential LP:

1. Step A: an LP over `(dx, dy, dθ)` of every square, with each gap linearised in the angles, inside a trust region. Where a square is within the trust radius of parallel to a wall or to its neighbour, the half-width `|cos| + |sin|` has a kink. Both branches are written as rows there, so the model never predicts a gain from crossing the kink.
2. Step B: the fixed-angle LP at the new angles. It is exact and restores every gap.
3. Accept if the true side fell. If not, the angle trust radius shrinks by 4.

It needs only numpy and scipy (HiGHS through `linprog`). An n of 500 takes 5 to 70 s.

**Control, green.** Three held packings, each with its centres scaled by `1 + 1e-3` (a side 0.013 to 0.019 longer). The LP brings all three back to the held side within 2e-10: n = 150 to 12.778174593511 (held 12.778174593653), n = 261 to 16.678779875958 (held 16.678779876143), n = 333 to 18.772634114164 (held 18.772634114356).

**On our file it is dry.**

| run | n | result |
|---|---|---|
| fixed-angle LP on 5 held n (37, 150, 261, 452, 498) | 5 | 1 n moves, by 9e-10 of score |
| sequential LP on the same 5 | 5 | n = 452 gains 9.4e-8; the other four gain 1e-11 |
| sequential LP on the layouts as they were on 2026-11-10 (452, 459, 644) | 3 | 0 |
| sequential LP on 22 of the 54 n that today's harvest brought in | 22 | 3 n above 1e-9, total 1.3e-7 of score |

So the held packings are local optima of the exact problem, not only of `fq`. The LP is worth keeping as the last step of a search, which is how `methods_soft.py` uses it. A sweep of the file with it is not worth the CPU.

## 3. `methods_soft.py`: the soft-box search

Our CPU version of the island GA, written from the notebook's description:

- The box is `DELTA` (2e-4) below the best side, so every member overlaps a little.
- A child is a copy of a member with one move: slide a row, turn every square of one tilt about the group's centre, jiggle a square, jiggle or twist a cluster, turn a block of one angle rigidly, or turn an upright square into the tilted row beside it. The moves are drawn with the weights the notebook measured. 80% of the moves aim at a square that overlaps.
- The child is relaxed with L-BFGS on `E = Σ penetration² + 4 Σ wall excess²`. The penetration of a pair is the smallest push on one of its four edge directions.
- The lowest energies survive (12 members).
- When the best member is soft-free, the box drops by `DELTA` again. So the island works below the legal side.
- Legalising: a member is relaxed hard in a ladder of boxes a little above its own (+1e-5 to +2e-3). The first one that comes out overlap-free is repaired and squeezed by `methods_lp`. A legal side below the best is a find.

Differences from the public GA: one island and no diversity rule; numpy on one core in place of CUDA, at 4 to 6.5 children a second for n = 450 to 650 on boxC (the notebook makes about 60 a second per process on a shared T4); the legaliser ends in an exact LP.

`--start mdrop1` and `--start mbest` make a mirror island (every child is made symmetric about the diagonal), which is where the notebook found its n = 452. Our mirror seed is crude: the half of the squares below the diagonal plus their mirror images. It does not relax to soft-free even in a box 0.32 above the seed, so the three mirror islands never moved. Round 8 rebuilt the seed (section 3b).

**Control on n = 644, green in part.** The public GA started its n = 644 from the atlas packing at side 25.854927027 and took it to 25.848586871 within its 41-minute run. We gave `methods_soft.py` the same start (read from the atlas notebook's output). One seed made 5 finds in 317 s, by the twist and re-angle moves, and reached **25.853388644** (0.0000606 of score). That is 24% of the public descent. Then it stalled: two seeds made no more finds in 32,000 further children. So our version walks the same lineage down from a looser start, and it stops earlier than the GPU version does. The sequential LP alone gains nothing from that start.

**Control on n = 452 (the mirror island), red.** The public GA found its n = 452 on a mirror island seeded from n + 1 minus a square. Our three mirror islands (two `mdrop1`, one `mbest`, from the file of 2026-11-10) never became soft-free: the seed relaxes to E = 0.04 to 0.14 even in a box 0.32 above it. They made 2,900 children and no find.

**Runs on our file.** All on boxC (10 cores) and 2 processes on boxA, between 13:08Z and 14:10Z.

| run | what | children | finds |
|---|---|---|---|
| round 1 | 8 n with the largest gap to the board below n = 760 (367, 634, 687, 328, 530, 686, 741, 577), one plain island each, 410 s, whole-packing relaxation, the LP as the only legaliser | 17,200 | 0 |
| rounds 2 and 3 | the 5 n that today's harvest took from the public GA (452, 459, 593, 644, 646), 1 to 3 seeds each, with the ladder | about 128,000 | 4 n: 644 (two steps), 452, 459, 646. None on 593 (4 seeds) |
| sweep A | the other 49 n of today's harvest, 60 s each | 12,100 | 1 n: 701 |
| sweep B | every odd n from 331 to 999, 25 s each (335 n) | 59,000 | 1 n: 459 again, nothing new |
| 701 | the find of sweep A, continued: 1 process for 16 minutes, then 4 seeds for 11 minutes | about 31,000 | 15 finds. Every start from the legal best found again within 1 to 3 minutes; the last find came 5 minutes after the last start, and the 4 seeds made none in the 6 minutes before the stop |

Certified by `methods_take.py` (`floatsafe.work`, strictly below the held score by more than 1e-10):

| n | held side | new side | gain of score |
|---|---|---|---|
| 452 | 21.763709680 | 21.763608543 | 4.757e-06 |
| 459 | 21.902457456 | 21.902366354 | 4.252e-06 |
| 644 | 25.848586871 | 25.848384296 | 7.983e-06 |
| 646 | 25.883765897 | 25.883610914 | 6.098e-06 |
| 701 | 26.915472716 | 26.913462417 | 7.593e-05 |
| **total** | | | **0.0000990** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-methods-r7` on boxA, in the layout `engine_assemble.py` reads. Nothing was submitted from here.

What the runs show:

- **The method finds only where the layout is loose.** Four of the five n that came from the public GA moved again, and one n of about 380 others did (701). An island stalls once its box is about 8e-4 below its legal side; a new start from the legal best finds again. The code does not make that restart by itself yet.
- **Two finds came in the first seconds.** On 452 the first relaxation in a box 1e-4 smaller, then the ladder and the LP, gave the new side with no move at all. On 459 it took one to three children. The sequential LP alone gains 9e-8 and 3e-8 on those two. So the soft squeeze crosses contact changes that the LP does not.
- **Relaxing only the squares near the move pays.** A child then costs 0.1 s in place of 0.25 to 0.8 s (4 to 6 children a second became 10 to 12), and its total energy follows exactly from the parent's (checked on 40 children: relative error 4e-16).
- **Yield.** 0.0000990 of score in about 13 CPU-hours, three quarters of it from one n. The public GA reports 0.00096 in 41 minutes on two T4s. Ours makes about one sixth of its children per second and has no mirror islands, which is where the notebook says most of its finds start.

## 3b. Round 8: a C kernel, the restart, a legal mirror seed

Run on 2026-11-11 from 14:44Z to 16:25Z: 8 processes on boxC and 2 on boxA, 7.9 million children, about 14 CPU-hours.

**Speed: 9 to 15 times more children a second.** The energy, its gradient and the L-BFGS loop are now C, compiled once with the system `cc` and loaded with ctypes (`--kernel c`, the default; `--kernel numpy` is the old path, and the tool falls back to it when there is no `cc`). Both kernels relax the same start to the same energy (4.2e-9 against 4.2e-9 after 200 iterations).

| measure | numpy | C |
|---|---|---|
| n = 701, two processes side by side on boxA, first 75 s | 400 children, 6 a second | 3,900 children, 54 a second |
| n = 701, long island | 10 to 12 a second (round 7) | 166 a second on boxA, 173 on boxC |
| n = 590 / 601 / 806, long island on boxC | | 217 / 214 / 147 a second |

The public GA makes about 60 children a second per process on a shared T4. One core of ours now makes more.

**Restart.** An island with no find in `--restart` children (3,000) starts again from its legal best. The first version seeded the new population wrongly (the energy jumped from 6e-7 to 4e-4 at each restart); the fix seeds it with the soft relaxation of the legal best.

- Control on n = 644 (same start as the public GA, 317 s): 4 finds, side 25.853266059, 26% of the public descent. Round 7 reached 25.853388644 (24%). Three of the four finds came after a restart. Then 4 restarts found nothing. So the restart adds a little and does not remove the stall.
- On our file, every long island found again after a restart, and then went dry:

| island | time | children | restarts | finds | last find at |
|---|---|---|---|---|---|
| 590 | 3,234 s | 703,000 | 232 | 5 | 347 s |
| 601 | 4,515 s | 964,000 | 320 | 1 | 218 s |
| 701 (boxC) | 4,515 s | 781,000 | 259 | 2 | 887 s |
| 701 (boxA, from the first find) | 1,499 s | 249,000 | 83 | 1 | 530 s |
| 806 | 2,668 s | 392,000 | 128 | 8 | 2,454 s |

Only 806 found late (two finds after 2,200 s). The others made all their finds in the first 6 to 15 minutes. A long island on one n is a poor use of a core after 15 minutes.

**The sweep is where the new n come from.** The 47 n that the harvest of 2026-11-11 moved (other than the five of round 7) got three short passes each, one plain island per n:

| pass | children | n with a find |
|---|---|---|
| numpy, 150 s, 32 n reached | 55,000 | 601 |
| C, 180 s, `--delta 2e-4`, 47 n | 1,666,000 | 590, 806 |
| C, 200 s, `--delta 1e-4`, another seed, 45 n | 1,903,000 | 419, 654, 806 |

Five new n of 47. Three of them (419, 654, 590) needed the C kernel's child count; the numpy pass missed them. Plain islands on 452, 459, 644, 646 (370 s each) and 593 (240 s) found nothing more: round 7 emptied them.

**Certified** by `methods_take.py` against `gate/cand-round7-1111a/details.csv`:

| n | held side | new side | gain of score |
|---|---|---|---|
| 419 | 20.936398827 | 20.935511038 | 4.337e-05 |
| 590 | 24.790669645 | 24.789470132 | 4.938e-05 |
| 601 | 24.956843415 | 24.956032450 | 3.308e-05 |
| 654 | 25.990586798 | 25.990486096 | 3.938e-06 |
| 701 | 26.913462417 | 26.913201719 | 9.846e-06 |
| 806 | 28.851509054 | 28.849386623 | 7.476e-05 |
| **total** | | | **0.0002144** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r8` on boxA. Nothing was submitted from here.

**The mirror island now has a legal seed. Its control on n = 452 is still red.** The seed takes the squares on one side of the diagonal of the held n, n + 1 or n + 2 (with a strip of 0.20 to 0.50 along the diagonal kept as diagonal squares), adds their mirror images, and relaxes the result inside the symmetric subspace in a growing box until it is soft-free. The lowest box of the 18 variants is the seed. Every relaxation of a child stays in that subspace, so the island is exactly symmetric at every step. In round 7 no seed became soft-free at all.

| control | start | children | result |
|---|---|---|---|
| 452 from the file of 2026-11-10 (legal side 21.776303384; the public GA reached 21.763709680 from there), island starts where its seed settles | seed soft-free at 21.805170193, 0.0289 above the legal side | 108,550 in 1,853 s, 4 restarts | box came down 0.0060 to 21.799170193. Still 0.0229 above its own legal start and 0.0355 above the public result. **Red** |
| the same, island starts just below the legal side with the overlap that takes (`--mirror-box below`) | E = 6.3e-4 | 23,750 in 487 s | E fell to 4.6e-4 and no member became soft-free. **Red** |
| held 452 (side 21.763243564, already mirror-symmetric: its seed is the packing itself) | +0.0000 | 115,500 in 1,500 s, 38 restarts | 0 finds |
| held 459 (side 21.901803002) | seed 0.0040 above | 279,900 in 2,644 s on boxC | 0 finds. **Open:** the island reported soft-free members in boxes down to 21.888403, 0.0134 below the legal side, and neither the ladder nor the LP made a legal packing from any of them |
| held 701 | seed 0.0148 above | not run | settling the seed takes 20 s per variant |

The 459 line is either a hole in the soft energy on a symmetric packing (an overlap it does not count, for example a square against its own mirror image, or a pair missing from the neighbour list after a long walk) or a legaliser that fails on a real gain of about 1.3e-3 of score. The run wrote no file of those members, so this round cannot say which. It is the first thing to check next.

The seed costs the island its start: a symmetrised packing settles 0.004 to 0.03 above the legal side it came from, and the island descends about 0.003 per 1,000 s from there. The public notebook's mirror islands start from a seed that is already near the legal side, and we do not know how it makes that seed.

## 3c. Round 9: the mirror 459 question, the wide pass, 806

Run on 2026-11-11 from 17:10Z to 18:22Z: 8 processes on boxC and 3 on boxA, about 7.5 million children, about 13 CPU-hours.

**Mirror 459: it was a hole in the island's energy bookkeeping, not a legaliser failure. No real packing was lost.** A child relaxes only the squares near its move (the active set), and the island keeps its total energy as the parent's total plus the change inside that set. On a mirror island two things broke that sum:

- the symmetrisation after each relaxation rounds every square in the last bit, so "the squares the move changed" was almost all of them, or, when it was not,
- the active set was not mirror-symmetric, and the symmetrisation then moved squares outside it (75 to 113 squares per child, by up to 4.2e-3). Their new overlaps were never counted.

Measured on the held 459 (seed soft-free at box 21.905603002, 2,866 children, 2,344 of them local): the kept energy was below a fresh total energy on 60% of the local children, by up to 4.9e-3, and never above it by more than 1.3e-9. So a member could read as soft-free in a box where it overlapped, the box dropped, and the walk went on to 0.0134 below the legal side on overlaps the island did not see. The soft energy itself is right: C and numpy agree to 13 digits on a shrunk 459, and its sign follows `methods_lp.min_gap`.

The fix (`methods_soft.py`): on a mirror island a square counts as changed only above 1e-12, the active set is closed under the mirror, and a member is counted afresh before the box may drop. After it, kept and fresh energy agree to 4e-17 on 2,848 local children. The island also writes any member that is soft-free below the legal best and that the ladder cannot make legal to `OUTDIR/softfree/`, with a `SOFTFREE-ILLEGAL` log line (fresh energy, true smallest gap, wall overshoot); `--keep-softfree 1` does the same on a plain island. On plain 419 that line shows what a soft-free member below the legal side is: box 0.0001 to 0.0003 below, smallest gap -1.0e-05 to -3.2e-05, the overlap the soft tolerance allows.

The 459 mirror island, rerun for 480 s (61,600 children, 4 restarts), stopped at box 21.902403002, 0.0006 above the legal side 21.901803002, and wrote no member below it.

**The 452 mirror control is still red with the fix**, so no mirror island ran on our file after it:

| control (file of 2026-11-10, legal side 21.776303384) | children | result |
|---|---|---|
| island starts where its seed settles (21.805170193) | 213,100 in 1,000 s, 14 restarts | box came down 0.0044 to 21.800770193, still 0.0245 above the legal side. 0 finds. **Red** |
| `--mirror-box below` (starts at 21.776103384, E = 6.3e-4) | 97,600 in 459 s | E fell to 4.5e-4, never soft-free. **Red** |

The fix made the island twice as fast per child as in round 8 and did not change the picture: the symmetric seed starts too high.

**The wide pass: all n from 300 to 1,000, one plain island each, 18 s, `--delta 1e-4`.** 700 islands in 31 minutes on boxC, 2,235,342 children (3,193 per island on average). 2 finds: 645 and 648. The log of each island also gives its count of box drops in 18 s, which sorts the n by how loose they are: 400 islands made 2 drops, 62 made 5 or more.

A second pass then gave the 63 loosest n (the three with a find, then the most box drops) 140 s each at `--delta 1e-4` and at `2e-4`, from the newest find of that n: 126 islands, 3,904,985 children, finds on 419, 640, 645, 648, 651, 756 and 800. 7 of 63 n, against 2 of 700 in the 18 s pass. The full `--delta 2e-4` pass over all n was dropped for this second pass after 4 islands.

Three longer islands on boxA (`--delta 2e-4`, from the finds): 648 for 1,644 s (288,289 children, 3 finds, the last at 144 s), 645 for 1,232 s (224,283 children, 1 find at 46 s), 756 for 1,232 s (160,403 children, 4 finds, the last at 364 s). The same shape as round 8: all finds in the first 6 minutes.

651 was still finding when the time ran out: 7 finds in its first 140 s island, and 7 more in the 10 children of the next one before the deadline cut it.

**n = 806, two seeds, 44 minutes each from the held packing:** 507,988 and 443,461 children, 0 finds. Round 8 took what was there.

**Certified** by `methods_take.py` against `gate/cand-round8-1111a/details.csv`:

| n | held side | new side | gain of score |
|---|---|---|---|
| 419 | 20.935511038 | 20.935104705 | 1.985e-05 |
| 640 | 25.790687771 | 25.789971366 | 2.832e-05 |
| 645 | 25.864599444 | 25.863361859 | 4.873e-05 |
| 648 | 25.906616169 | 25.904484055 | 8.376e-05 |
| 651 | 25.948909417 | 25.945321730 | 1.406e-04 |
| 756 | 27.923898205 | 27.922108033 | 6.511e-05 |
| 800 | 28.777991355 | 28.777508083 | 1.709e-05 |
| **total** | | | **0.0004035** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r9` on boxA. Nothing was submitted from here.

## 3d. Round 10: 651 again, the next 165 n, `--dry`

Run on 2026-11-11 from 19:07Z to 20:42Z. 8 processes ran on boxC, 3 on boxA from 20:00Z to 20:20Z, and up to 6 on boxD from 20:02Z. In all: 388 islands, 11.36 million children, about 16.5 CPU-hours.

**651 gave as much again as in round 9, then went dry.** Two islands of 900 s on boxA, from the held packing (side 25.945321730):

| island | children | finds | last find at | side at the end | gain of score |
|---|---|---|---|---|---|
| `--delta 1e-4` | 74,701 | 14 | 615 s | 25.941684354 | 1.426e-04 |
| `--delta 2e-4` | 102,293 | 11 | 294 s | 25.943154908 | 8.492e-05 |

- Both went down at the same rate for the first 300 s (8.8e-05 at 315 s and 8.5e-05 at 294 s). Then the `2e-4` island made no find in its last 606 s. A third island (`2e-4`, 140 s, boxD) made 5 finds, 6.363e-05.
- The finds come in runs (six between 201 s and 315 s on the `1e-4` island, then none for 108 s). Inside a run, a find takes about 20 s of ladder and LP and about 1 s of children. So the legaliser sets the rate there.
- A larger box step is not faster. One 140 s leg at `--delta 1e-3`, from side 25.942265494, made 1 find (2.059e-05, through the ladder, at 135 s). The `1e-4` island, which had made that packing, gained 1.85e-05 in the same 140 s.
- Six legs of 140 s after the last find (20:10:30Z) found nothing in 138,000 children. One started from side 25.941740207 and five from the best packing. Their box steps were `5e-4` twice, `2e-4` twice, `1e-3` and `1e-4`. So 651 is dry by the 6-minute rule.

Rounds 9 and 10 together took 651 from side 25.948909417 to 25.941684354, 2.832e-04 of score. It is still 0.0089 above the held side of 650.

**The 140 s pass on the next n by box drops**, both deltas, the `1e-4` island from the newest find of that n. The count of box drops is from the 18 s pass of round 9.

| group | n | islands | children | n with a find |
|---|---|---|---|---|
| 4 box drops (boxC) | 83 | 166 | 5,070,321 | 1: 600 (3 finds, 3.960e-05) |
| 3 box drops (boxC) | 67 | 134 | 3,908,090 | 0 |
| 3 box drops, the last 15 (970 to 997, boxD) | 15 | 30 (the deadline cut 3 of them to about 80 s) | 411,216 | 0 |
| the n of round 9 again, from their new packings (640, 756, 800, 645, 648) | 5 | 10 | 195,892 | 3: 640 (8.135e-06), 756 (6.528e-06), 800 (9.432e-06). None on 645 and 648 |

Round 9 found on 7 of the 63 loosest n. This round found on 1 of the next 165. Every n from 300 to 1,000 with 3 or more box drops has now had the 140 s pass at both deltas. The 400 n with 2 drops and the 73 with 1 have had only the 18 s.

**Relays from the finds** (boxD): legs of 140 s, `2e-4` and `1e-4` in turn, each from the best packing of that n, until 3 legs in a row find nothing.

| n | start | legs | children | finds |
|---|---|---|---|---|
| 640 | the find of this round | 5 | 104,657 | 1 in each of the first two legs (6.855e-06 more), then 3 dry legs |
| 600 | the find of this round | 3 | 71,617 | 0 |
| 756 | the find of this round | 3 | 58,964 | 0 |
| 800 | the find of this round | 3 | 51,855 | 0 |
| 419 | the held packing | 3 | 109,240 | 0 |

**The three n that the harvest of 19:22Z moved** (644, 694, 696) got 3 legs each from the harvest packings (`2e-4`, `1e-4`, `2e-4`). They made 83,130, 74,870 and 76,195 children and 0 finds.

**Longer islands, 600 s each, from the held packings:**

| n | `--delta 2e-4` | `--delta 1e-4` |
|---|---|---|
| 549 | 143,854 children, 0 finds | 116,595 children, 0 finds |
| 542 | 121,365 children, 0 finds | 97,766 children, 0 finds |
| 690 | 90,933 children, 0 finds | 74,936 children, 0 finds |
| 602 | 47,269 children, 0 finds | 87,321 children, 0 finds |

The 602 island at `2e-4` ran on boxA while another lane loaded that box. It got about a third of a core in its second half. Its 600 s made 47,269 children, against 87,321 for the same n on boxD. The rest of this queue moved to boxD at 20:17Z. An island's work is its count of children. On a loaded box, give the island more seconds or move it.

**`--dry S` (new).** The island ends S seconds after its last find, or after its start when it finds nothing. `--seconds 1800 --dry 360` is the 6-minute rule in one line of a queue, so a round needs no relay script. On a dry n (549, `--dry 15 --seconds 120`) the island ended at 15 s with 0 finds. On 651 (`--dry 200 --seconds 600`, on a loaded box) the island found at 118 s, 191 s, 250 s, 341 s and 560 s. It stayed alive to the end of its 600 s.

**Certified** by `methods_take.py` against `gate/cand-round9-1111a/details.csv`. A find on 644, 694 or 696 also had to beat the harvest take, and none came.

| n | held side | new side | gain of score |
|---|---|---|---|
| 600 | 24.935794655 | 24.934824613 | 3.960e-05 |
| 640 | 25.789971366 | 25.789592128 | 1.499e-05 |
| 651 | 25.945321730 | 25.941684354 | 1.426e-04 |
| 756 | 27.922108033 | 27.921928550 | 6.528e-06 |
| 800 | 28.777508083 | 28.777241303 | 9.432e-06 |
| **total** | | | **0.0002131** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r10` on boxA. The logs of every island are under `work/logs/` and `work/boxA/run/` there. Nothing was submitted from here.

What the round shows:

- **The gain is on a few n, and it comes early.** 651 alone is two thirds of the round. The latest find of the round came 615 s into its island. In rounds 8 and 9 the long islands also made their finds in the first 6 to 15 minutes.
- **The wide pass is nearly used up.** 1 n of 165 found, against 7 of 63 in round 9. The n that are left have 1 or 2 box drops in 18 s.
- **A find does not mean more finds.** Of the four n that found in the pass, only 640 found again in a relay.

## 3e. Round 11: the layouts of the family, modules and border lanes

Run on 2026-11-11 from 22:29Z to 23:27Z. One more island ran on boxA until 23:35Z. The CPU was 3 processes on boxC, 3 on boxD and 1 on boxA. In all: 137 islands, 2.93 million children, about 6.4 CPU-hours. boxC ran 69 islands (1,516,761 children), boxD 55 (1,144,018) and boxA 13 (268,125).

**One chain per start.** A chain is the 140 s island at `--delta 2e-4`, then 140 s at `1e-4` from the newest find. A chain with no find ends there. A chain with a find goes on with one island (`--seconds 1800 --dry 360`, at `2e-4` unless only the `1e-4` island found). Then it gives its result the fq quench on the same box: default flags, then the deep flags, up to three rounds, the loop of `engine_polish.py`. When the quench gains, the n goes to the end of the queue for one more island from the quenched packing.

**The starts**, 78 in all:

- 28 of the 34 n that round 10 moved, from the held file (`gather/round10-2026-11-11a.csv`).
- 29 n of the family, modules, border and inflate take dirs of round 10 whose file there is below the held score, from that file. Where two dirs hold an n, the lower file is the start. 6 of the 29 are n that round 10 moved, and 23 are n the held file does not have yet.
- 21 starts that the family lane (16, `take-family-r11`) and the modules lane (5, `take-modules-r11`) wrote during the round. A look every 10 minutes found them and put each at the head of a queue. The border lane wrote nothing new.

The layouts of the family, modules and border lanes ran first, largest gain first. The n that the polish, the harvest and this search moved in round 10 came last.

A find counts when it is more than 1e-10 below the held score and below the file it started from. It is left out when another lane holds a file for that n more than 1e-10 below it at the end of the round. That left out nothing.

| kind of start | starts | full pass | cut short | not run | replaced | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| family, in the held file since round 10 | 14 | 10 | 0 | 2 | 2 | 21 | 474,189 | 1: 817 | 4 |
| family, `take-family-r10` | 11 | 9 | 0 | 0 | 2 | 21 | 442,406 | 2: 933, 745 | 9 |
| family, written during the round (`take-family-r11`) | 16 | 16 | 0 | 0 | 0 | 34 | 791,112 | 1: 807 | 21 |
| modules | 22 | 19 | 0 | 0 | 3 | 38 | 771,040 | 0 | 0 |
| border | 5 | 5 | 0 | 0 | 0 | 10 | 204,013 | 0 | 0 |
| polish (fq, soft, harvest) | 9 | 6 | 0 | 3 | 0 | 12 | 227,323 | 0 | 0 |
| inflate | 1 | 0 | 1 | 0 | 0 | 1 | 18,821 | 0 | 0 |
| **all** | 78 | 65 | 1 | 5 | 7 | 137 | 2,928,904 | 4 | 34 |

- "Replaced" is a start that a lower file of the same n replaced before its chain began: 599, 813, 740, 873 (family), 756, 816, 912 (modules).
- "Not run" is the end of the queue when the time ran out. It holds 602 and 757 (family layouts that round 10 took for 2.6e-09 and 2.1e-09) and 645, 696 and 648 (polish). 815 (inflate) had one island of 140 s.
- All six polish n ran on boxA. 651 and 600 ran while that box was starved (10,330 and 7,738 children in their two islands). 640, 800, 644 and 694 had longer islands for that reason (420 s, later 200 s) and made 41,769 to 63,176 children each.

**Every find is on a layout of the family step.** 4 of the 35 family starts that had the full pass found. None of the 19 modules starts, the 5 border starts and the 6 polish starts found.

| n | start | island at `2e-4`, 140 s | island at `1e-4`, 140 s | island after the find | fq quench | own gain, certified |
|---|---|---|---|---|---|---|
| 933 | `take-family-r10` (3 shells up) | 4,600 children, 2 finds, 1.742e-05 | 6,500 children, 1 find, 4.812e-06 | 44,230 children, 1 find at 112 s, ended dry at 472 s, 3.847e-06 | 6.524e-06 | 3.260e-05 |
| 817 | held file (round 10, 2 shells up) | 19,996 children, 0 finds | 9,131 children, 1 find, 1.229e-05 | 49,391 children, 3 finds, the last at 202 s, ended dry at 562 s, 8.292e-06 | 1.520e-05 | 3.578e-05 |
| 745 | `take-family-r10` (1 shell up) | 16,600 children, 1 find, 2.144e-05 | 5,002 children, 3 finds, 2.505e-05 | 45,003 children, 1 find at 46 s, ended dry at 407 s, 7.010e-06 | 1.458e-05 | 6.808e-05 |
| 807 | `take-family-r11` (1 shell up from the held 750), found by the look of 22:50Z | 2,828 children, 2 finds, 1.723e-05 | 81 children, 4 finds, 1.283e-05 | 67,478 children, 15 finds, the last at 1,209 s, cut by the deadline at 1,269 s, 1.341e-04 | 5.452e-05 | 2.186e-04 |

- **The island on 807 was still finding when the deadline cut it.** It found every 48 to 165 s for 21 minutes. The finds came at 58, 141, 207, 278, 339, 419, 467, 536, 603, 674, 724, 805, 970, 1,108 and 1,209 s. After the quench, one more island on boxA (360 s, 40,802 children) found nothing.
- **The fq quench after the island gained on all four**: 9.08e-05 together, a quarter of the round's own gain. On 807 it gained 5.452e-05 in two steps.
- One more island after the quench ran on 933 (34,100 children in 280 s, cut by the deadline) and on 807. Neither found. 817 and 745 did not get theirs.
- The 34 finds by move: twist 11, first relaxation with no move 7, jiggle 5, row 4, re-angle 3, cluster 2, block 2. 6 of the 34 came through the ladder.

**Certified** against `gate/cand-round10-1111a/details.csv` (floatsafe at 2.2e-11). "Own gain" is the gain on top of the file the search started from. The rest of the gain against the held file belongs to the family lane's start.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 745 | `take-family-r10` | 27.788343934 | 27.788306347 | 27.786448158 | 6.946e-05 | 6.808e-05 |
| 807 | `take-family-r11` | 28.870124903 | 28.866837212 | 28.860626075 | 3.344e-04 | 2.186e-04 |
| 817 | held file | 28.991970614 | 28.991970614 | 28.990947877 | 3.578e-05 | 3.578e-05 |
| 933 | `take-family-r10` | 30.949834163 | 30.945191598 | 30.944195823 | 1.846e-04 | 3.260e-05 |
| **total** | | | | | **0.0006242** | **0.0003551** |

The per-n files and `take.tsv` (with the start score and the own gain of each n) are in `<scratch>/bounties-squares/take-soft-r11` on boxA. The logs of every island are under `work/boxC/run/`, `work/boxD/run/` and `work/boxA/run/` there. Nothing was submitted from here.

**boxA was starved at the start.** At 22:30Z its load was 33, and one island made 350 children in 37 s. An island on boxC made 6,700 in 46 s. Its queue of 8 starts went to the other two boxes at 22:31Z, and its slot ran the polish n. From 23:00Z its share was 65% to 97% of a core. The other two boxes reached loads of 54 and 46 from other lanes, and our islands there still had 61% to 100% of a core each.

**The driver** is `tools/softround/`. `ctl.py plan` writes the starts and one queue per box. `chain.sh` is the chain, and `worker.sh` takes the next line of a queue. `ctl.py watch` adds the new wins of the other lanes, and `ctl.py collect` fetches and certifies. The paths of the round are constants at the top of `ctl.py`. In zsh, write `"${b}:path"` in an rsync or scp line: `$b:scratch/...` is read as a substitution on `$b` and the copy lands in a local dir.

What the round shows:

- **The search pays on a layout the family step has just made, and on nothing else this round.** Family: 4 of 35. Modules, border and polish: 0 of 30. The modules and border lanes squeeze their layouts with the LP and fq before they write them.
- **A family layout can be as loose as 651 was.** 807 gave 2.186e-04 of own gain in one chain. 651 gave 1.426e-04 in round 10.
- **The quench belongs in the chain.** It gained on every n the island had moved, and it cost 23 to 162 s per n.
- **A look every 10 minutes is enough to follow the other lanes.** Four looks found 8, 4, 0 and 9 new files. The first island of each began 12 s to 10 minutes after its look.

## 3f. Round 12: the new layouts of the family, readers, border and zone lanes

Run on 2026-11-12 from 01:04Z to 02:24Z, and the fq quench of the last finds until 02:28Z. The CPU was 2 processes on boxC and 1 on boxA. boxD got none: the rule was to start it when its load fell under 9, and other lanes kept it at 9.3 to 18 all round. In all: 84 islands, 1,847,161 children, about 3.8 CPU-hours. boxC ran 54 islands (1,493,881 children) and boxA 30 (353,280).

**The chain** is the chain of round 11 (section 3e). It has three modes now. `full` runs the island even when the two 140 s islands found nothing. `short` has no island. `again` is the island alone. `ctl.py plan` reads the plan and logs of round 11 and starts no n whose packing already had both 140 s islands there.

**The starts**, 90 in all:

- 34 of the 61 n that round 11 moved, from the held file (`gather/round11-2026-11-11b.csv`). The other 27 had both 140 s islands on the same packing in round 11, or rest (807 and 933: the island after their quench found nothing). 745 ran `again`, 817 `full` and 806 `short`.
- Five of the six n that did not get their pass in round 11 (602, 757, 645, 696, 648), last in the queue. The sixth, 815, is among the 34.
- 1 zones file below the held score at the plan (634).
- 50 files that the other lanes wrote during the round: family 18, readers 10, zone corner 9, border 8, zone low-f 5. A look every 10 minutes found them and put each at the head of a queue, family and readers files first.

| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| family, in the held file | 16 | 7 | 0 | 7 | 2 | 17 | 367,762 | 1: 854 | 7 |
| family, written during the round | 18 | 13 | 2 | 3 | 0 | 30 | 674,232 | 1: 598 | 7 |
| family (readers), written during the round | 10 | 10 | 0 | 0 | 0 | 20 | 519,172 | 0 | 0 |
| own soft result on a family layout (745, `again`) | 1 | 1 | 0 | 0 | 0 | 1 | 57,986 | 0 | 0 |
| modules, in the held file | 7 | 0 | 0 | 5 | 2 | 0 | 0 | 0 | 0 |
| border, in the held file | 4 | 0 | 0 | 1 | 3 | 0 | 0 | 0 | 0 |
| border, written during the round | 8 | 3 | 0 | 4 | 1 | 6 | 86,106 | 0 | 0 |
| zones, in a take dir at the plan | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| zones, written during the round | 14 | 5 | 0 | 8 | 1 | 10 | 141,903 | 0 | 0 |
| polish (fq), in the held file | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 0 |
| harvest, in the held file | 6 | 0 | 0 | 5 | 1 | 0 | 0 | 0 | 0 |
| inflate, in the held file | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **all** | 90 | 39 | 2 | 38 | 11 | 84 | 1,847,161 | 2 | 14 |

- "Dropped" is a start that a lower file of the same n replaced before its chain began. From the held file: 870, 972, 986, 863, 994, 924, 742, 648. From the other lanes: 972 (border) and 921 (zone low-f, 2e-09 below the 921 file that had its pass). 817 is the eleventh (below).
- "Not run" is the end of the queues at the deadline. 932 and 995 (family) were cut short by the deadline. The starts that did not run:
  - the held family layouts 754, 638, 593, 929, 866, 602 and 757
  - the other n that round 11 moved: 237, 459, 931, 551, 995, 997, 806, 378, 987, 738, 457, 856 and 815
  - two more of the six from round 11: 645 and 696 (602 and 757 are in the first item)
  - 634 (zones, at the plan)
  - the zone files 703, 932, 986, 871, 803, 923, 924 and 758, the border files 972, 913 and 994, and the family files 795, 985 and 922
- 745 had its island from the held packing: 57,986 children, dry at 360 s, nothing found.

**Finds on 2 n, both layouts of the family step.** 2 of the 20 family starts with a full pass found. None of the 10 readers, 3 border and 5 zone starts found.

| n | start | island at `2e-4`, 140 s | island at `1e-4`, 140 s | island after the find | fq quench | own gain, certified |
|---|---|---|---|---|---|---|
| 598 | `take-family-r12`, found by the look of 01:16Z | 9,783 children, 0 finds | 6,284 children, 1 find, 4.100e-06 | 26,450 children in 577 s on boxA, 3 finds, 1.621e-05, then 195,140 children in 956 s on boxC, 3 finds, the last at 596 s, 1.871e-05 | 2.112e-05 | 6.014e-05 |
| 854 | held file (round 11 family layout) | 4,503 children, 2 finds, 4.433e-05 | 9,900 children, 1 find, 1.407e-05 | 74,165 children, 4 finds, the last at 410 s, ended dry at 770 s, 3.962e-05 | 4.274e-05 | left out (below) |

- The 14 finds by move: twist 5, first relaxation with no move 3, re-angle 2, arm 2, cluster 1, jiggle 1. 5 of the 14 came through the ladder.
- **The family lane moved faster than the search on 854 and 817.** The 854 chain took the held packing to 0.017021469755. During the round the family lane wrote 854 at 0.017021064230 and then at 0.017020930452, so the result is left out. Both new files had their pass, with no find. On 817 the family lane wrote a file 9.9e-05 below the held packing at 01:53Z. The chain on the held packing was stopped in its second 140 s island (the first found nothing), and the new file had its pass, with no find. So 817 did not get the island from the held packing that the round owed it.

**Certified** against `gate/cand-round11-1111b/details.csv` (floatsafe at 2.2e-11). `methods_take.py` on the raw file keeps the same score and a byte-identical file, and drops the held 598 against itself.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 598 | `take-family-r12` | 24.904006616 | 24.903986318 | 24.902515634 | 6.097e-05 | 6.014e-05 |
| **total** | | | | | **0.0000610** | **0.0000601** |

The per-n file and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r12` on boxA, and the logs of every island under `work/boxC/run/` and `work/boxA/run/` there. Nothing was submitted from here.

**boxA was starved, so the starts moved by box.** Its slot had 27% to 75% of a core at loads of 15 to 58. Our islands on boxC had 98% to 100% at loads of 7 to 12. The island of the 598 find made 26,450 children in 577 s on boxA. It went on from its best packing on boxC, which made 195,140 children in 956 s, 7 times as fast, and found 3 more times. From 01:47Z the family and readers starts ran on boxC and the zone and border starts on boxA.

**Two driver bugs, fixed.** `ctl.py watch` held `plan.json` in memory through a scan of minutes and wrote it back over the edits made meanwhile. It now reloads the plan and adds only its new jobs. `status.sh` failed in boxA's `/bin/sh` on a nested `awk` quote. It uses `cut` now.

What the round shows:

- **The search still pays only on family layouts.** Rounds 11 and 12 together: 6 of 55 family starts with a full pass found. 0 of 10 readers, 0 of 8 border, 0 of 5 zone, 0 of 19 modules and 0 of 6 polish starts found.
- **The family lane can take an n past the search while the chain runs.** So a chain on a family file pays most when the family lane has finished with that n.
- **The slots were the limit, not the starts.** 90 starts met 2 full-speed slots and one at a quarter to three quarters of a core. 39 passed and 38 did not run, the held family layouts among them.
- **An island moves between boxes from its best packing** and goes on finding. Moving it is cheaper than leaving it on a starved slot.

## 3g. Round 13: the family layouts that waited, and the new ones

The round ran on 2026-11-12 from 04:03Z to 05:28Z, with the fq quench inside that time. The CPU was 2 processes on boxC, 1 on boxD and 1 on boxA. All four were full-speed slots: each of our islands had 91% to 100% of a core. The loads were 6.8 to 12.6 on boxC, 7.5 to 11 on boxD (4.9 at the start, under the limit of 9) and 5.7 to 14.8 on boxA. In all, the round ran 121 islands, 3,184,640 children and about 5.3 CPU-hours. boxC ran 55 islands (1,410,250 children), boxD 36 (917,710) and boxA 30 (856,680).

**The chain** is the chain of rounds 11 and 12 (section 3e).

**The starts** were 59 in all. Every one had its full pass or was dropped, so nothing waited at the end:

- 12 family files of round 12 that are now held: 995, 702, 932, 549, 815, 812, 987, 922, 738, 985, 687 and 740. Seven more had their pass on the same packing in round 12 (649, 742, 854, 933, 986, 996, and 817 before its quench), so they got no start. 795 waited for the skeptic's rebuild (below).
- The 7 held family layouts that round 12 did not run: 754, 638, 593, 929, 866, 602 and 757. The table counts 754 under polish and 757 under modules, the kinds of their newest step.
- The other n that round 12 moved, last in the queue: 5 readers layouts, 11 modules, 2 border, 4 polish, 1 harvest and our own 598.
- 16 files that the family lane (11) and the readers lane (5) wrote during the round. The look every 10 minutes found 1, 2, 2, 1, 1 and 9 files, and put each at the head of a queue. One of them is 795, the skeptic's rebuild of round 12 (3.336e-05 below the held 795). It had its pass with no find.

| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| family, in the held file | 17 | 17 | 0 | 0 | 0 | 36 | 973,557 | 1: 815 | 12 |
| family, written during the round | 11 | 11 | 0 | 0 | 0 | 23 | 581,350 | 1: 871 | 3 |
| family (readers), in the held file | 5 | 5 | 0 | 0 | 0 | 12 | 391,864 | 1: 497 | 8 |
| family (readers), written during the round | 5 | 5 | 0 | 0 | 0 | 10 | 237,473 | 0 | 0 |
| own soft result on a family layout (598) | 1 | 1 | 0 | 0 | 0 | 2 | 55,292 | 0 | 0 |
| modules, in the held file | 12 | 11 | 0 | 0 | 1 | 22 | 503,280 | 0 | 0 |
| border, in the held file | 2 | 2 | 0 | 0 | 0 | 4 | 73,011 | 0 | 0 |
| polish (fq), in the held file | 5 | 5 | 0 | 0 | 0 | 10 | 249,463 | 0 | 0 |
| harvest, in the held file | 1 | 1 | 0 | 0 | 0 | 2 | 119,350 | 0 | 0 |
| **all** | 59 | 58 | 0 | 0 | 1 | 121 | 3,184,640 | 3 | 23 |

- The one start dropped is 758 (modules). The family lane wrote a lower 758 while it waited, and the watch took it out of its queue.
- The 9 files of the look at 05:06Z came 22 minutes before the deadline. To give them their pass, the deadline moved from 05:22Z to 05:28Z.

**Finds on 3 n, all family layouts.** 815 and 871 are layouts of the family step, and 497 is a layout of the layer reader. 3 of 38 family and readers starts found. None of the 20 other starts found.

| n | start | island at `2e-4`, 140 s | island at `1e-4`, 140 s | island after the find | fq quench | own gain, certified |
|---|---|---|---|---|---|---|
| 815 | held file (round 12 family file, 1 shell up from the corner zones' 758) | 18,222 children, 1 find, 5.621e-05 | 600 children, 3 finds, 1.298e-05 | 135,082 children, 8 finds, the last at 998 s, ended dry at 1,358 s, 5.893e-05 | 1.823e-05 | 1.463e-04 |
| 497 | held file (round 12 readers file, 1 shell up from 452) | 7,448 children, 7 finds, 5.912e-05 | 26,121 children, 1 find, 4.047e-06 | 79,974 children, 0 finds, dry at 360 s | 5.133e-06 | 6.830e-05 |
| 871 | `take-family-r13` (1 shell up from the held 812), found by the look of 05:06Z | 17,200 children, 1 find, 6.711e-06 | 4,900 children, 2 finds, 1.166e-05 | 50,426 children, 0 finds, dry at 360 s | 1.346e-05 | 3.182e-05 |

- The 23 finds by move: twist 12, first relaxation with no move 5, jiggle 2, cluster 2, row 1, block 1. 5 of the 23 came through the ladder.
- 815 and 497 had one more island from the quenched packing (`again`): 61,007 and 86,565 children, 0 finds. Rounds 11 to 13 together give 0 finds in 5 such islands (933, 807, 745, 815, 497).
- 497 and 815 had waited a round in the held file. Their round 12 files landed at 02:47Z and 02:42Z, after the last look of round 12 (02:19Z), so the search had not seen them. A family or readers file that lands after a round's last look pays as well as one the look catches.

**Certified** against `gate/cand-round12-1112a/details.csv` (floatsafe at 2.2e-11). `methods_take.py` on the three raw files keeps the same scores and writes byte-identical files. The held 815 against itself drops.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 497 | held file | 22.781963852 | 22.781963852 | 22.780441187 | 6.830e-05 | 6.830e-05 |
| 815 | held file | 28.965123570 | 28.965123570 | 28.960945738 | 1.463e-04 | 1.463e-04 |
| 871 | `take-family-r13` | 29.930903374 | 29.930774668 | 29.929835499 | 3.618e-05 | 3.182e-05 |
| **total** | | | | | **0.0002508** | **0.0002465** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r13` on boxA, and the logs of every island under `work/boxC/run/`, `work/boxD/run/` and `work/boxA/run/` there. Nothing was submitted from here.

**Three driver changes.**

- `ctl.py plan` ranks the starts in four groups: the family files of the round before, then the held family layouts that waited, then readers layouts, then the other moved n. It reads the passes of the round before from the logs of every box, so a chain that changed box still counts as passed.
- `ctl.py watch` takes a start out of its queue when a lower file of the same n lands before the start begins (`WATCH drop`). Round 12 did this by hand.
- `chain.sh` puts the island that a quench owes (`N TAG again`) at the head of its queue, where the plan ranks it. Before, it went to the end, behind the modules and border starts.

What the round shows:

- **The search pays on family and readers layouts, and on nothing else.** In rounds 11 to 13, 9 of 103 family and readers starts with a full pass found. 0 of 57 other starts found (modules, border, zones, polish, harvest).
- **Four full-speed slots emptied the queue.** All 59 starts ran in 85 minutes. Round 12 had 2 full-speed slots and left 38 starts.
- **The island after the quench does not pay.** It gave 0 finds in 5 islands over three rounds.

## 3h. Round 14: family and readers layouts only

The round ran on 2026-11-12 from 06:29Z to 07:59Z, with the fq quench inside that time. The CPU was 2 processes on boxC, 1 on boxD and 1 on boxA. Each island had 97% to 100% of a core. The loads were 5.9 to 15.7 on boxC, 5.3 to 9.3 on boxD and 6.3 to 16.1 on boxA. In all, the round ran 92 islands, 2,165,622 children and about 4.0 CPU-hours. boxC ran 41 islands (970,102 children), boxD 23 (563,243) and boxA 28 (632,277).

**The chain** is the chain of round 13 (section 3g), with no island after the quench. Rounds 11 to 13 ran 5 such islands, and none found. `ctl.py plan` now makes a start from the held file only when the newest step of that n is a family step or a layer reader (`KINDS`). In rounds 11 to 13, starts of other kinds found 0 times in 57.

**The starts** were 44 in all. Every one had its full pass:

- 9 held family and readers layouts of round 13 had no pass on that packing. They are 755, 812, 932, 867 and 924 (family), and 739, 655, 604 and 868 (readers).
- 13 more held family and readers layouts of round 13 had their pass on the same packing in round 13. They are 548, 549, 649, 652, 696, 702, 758, 795, 809, 874, 928, 991 and 994. Each had a second pass with new seeds (21 to 23) at the end of the queue (`seed2`). This measures whether a new seed finds on a layout where the first seed found nothing.
- 497, 815 and 871 got no start from the held file. Their held packings are our round 13 results, and they had their pass. The family lane wrote lower 815 (twice) and 871 files during the round, and those files had their pass.
- 21 files that the family lane (11) and the readers lane (10) wrote during the round. The look every 10 minutes found 0, 2, 0, 0, 3, 8, 0, 7 and 1 files. One more look by hand at 07:58Z found none.
- 1 file from the family lane's handoff: an 854 one shell up from the held 795, 4.8e-8 above the held side. `ctl.py add` put it at the head of a queue. Its start counts from the held score.

| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| family, in the held file | 5 | 5 | 0 | 0 | 0 | 11 | 245,748 | 1: 755 | 11 |
| family, in the held file, second seed | 9 | 9 | 0 | 0 | 0 | 18 | 445,245 | 0 | 0 |
| family, written during the round | 12 | 12 | 0 | 0 | 0 | 26 | 573,041 | 1: 755 | 11 |
| family (readers), in the held file | 4 | 4 | 0 | 0 | 0 | 8 | 211,414 | 0 | 0 |
| family (readers), in the held file, second seed | 4 | 4 | 0 | 0 | 0 | 8 | 176,628 | 0 | 0 |
| family (readers), written during the round | 10 | 10 | 0 | 0 | 0 | 21 | 513,546 | 0 | 0 |
| **all** | 44 | 44 | 0 | 0 | 0 | 92 | 2,165,622 | 1 | 22 |

- The chain on the family lane's 755 file was stopped by hand in its island at 06:59Z. The chain from the held 755 had certified a packing 1.3e-4 below that file by then.
- At 07:32Z two slots had no work. Each ran one island (seed 14, `--dry 360`) on a start whose pass was dry: 999 (family) and 981 (readers). They made 45,100 and 46,372 children and found nothing.

**Finds on 1 n: 755.** It is a layout of the family step, 1 shell up from the modules result of n = 700. Both the held 755 and the family lane's 755 file found, 11 times each. None of the other 29 first passes found, and none of the 13 second-seed passes.

| n | start | island at `2e-4`, 140 s | island at `1e-4`, 140 s | island after the find | fq quench | own gain, certified |
|---|---|---|---|---|---|---|
| 755 | held file (round 13 family file) | 784 children, 3 finds, 4.032e-05 | 5 children, 3 finds, 1.828e-05 | 76,548 children, 5 finds, the last at 344 s, ended dry at 704 s, 4.796e-05 | 2.865e-05 | 1.352e-04 |
| 755 | `take-family-r14`, found by the look of 06:40Z | 1,834 children, 4 finds, 4.959e-05 | 700 children, 3 finds, 2.712e-05 | 82,650 children, 4 finds, stopped at 591 s, 2.643e-05 | not run | stopped, not kept |

- The 22 finds by move: twist 10, jiggle 3, arm 3, first relaxation with no move 3, block 2, re-angle 1. 3 of the 22 came through the ladder.

**Certified** against `gate/cand-round13-1112a/details.csv` (floatsafe at 2.2e-11). `methods_take.py` on the raw file keeps the same score and writes a byte-identical file. The held 755 against itself drops.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 755 | held file | 27.913047732 | 27.913047732 | 27.909332331 | 1.352e-04 | 1.352e-04 |
| **total** | | | | | **0.0001352** | **0.0001352** |

The per-n file and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r14` on boxA, and the logs of every island under `work/boxC/run/`, `work/boxD/run/` and `work/boxA/run/` there. Nothing was submitted from here. At the collect, `take-polish-r14` held a 755 at 0.0157246004316, 5.9e-10 below ours. It is the polish lane's fq quench of this result, so the gain counts once.

**Driver changes.**

- `ctl.py plan` skips a held n whose newest step is not of `KINDS` (family and readers). With `RESEED`, a held family or readers packing that had its pass in the round before goes to the end of the queue. It runs with the seeds 21 to 23 (`seed2`).
- `chain.sh` has no island after the quench. Mode `island` runs one island on a start whose pass was dry, for an idle slot.
- `ctl.py add N FILE KIND BOX` puts a file that a lane hands over at the head of a box queue.
- `setup.sh BOX DEADLINE FQDEADLINE` makes the scratch of a box. It builds a venv on the box's Python 3.12 with numpy 2.5.4 and scipy 1.18.1.
- `stats.py` and `mdtables.py` read the seeds of a `seed2` start.

What the round shows:

- **New family and readers layouts still pay, and only a few of them.** 1 of 31 first passes found, on 1 n. Over rounds 11 to 14, 11 of 134 family and readers starts with a full pass found.
- **A second seed does not pay.** 13 layouts that were dry with the seeds 11 and 12 stayed dry with the seeds 21 and 22 (621,873 children).
- **An island does not pay after a dry pass.** The 2 islands on 999 and 981 found nothing.
- **The supply of new layouts was the limit, not the slots.** The four slots ran islands or quenches for about 70% of the round. The rest of the time they waited for new files.
- **When a layout finds, it finds from more than one start.** The held 755 and the family lane's 755 file both found 11 times.

## 3i. Round 15: family and readers files, no second seed

The round ran on 2026-11-12 from 08:56Z to 10:24Z, with the fq quench inside that time. The CPU was 2 processes on boxC and 1 on boxD for the whole round, and 1 on boxA until 10:04Z. In all, the round ran 47 islands, 1,069,605 children and about 2.1 CPU-hours. boxC ran 25 islands (598,086 children), boxD 14 (345,743) and boxA 8 (125,776).

**The chain** is the chain of round 14 (section 3h). `RESEED` is off, so no held packing got a second seed. No idle slot ran an island. The watch also reads `take-band-r15` and puts its files at the head of a queue, as it does for family and readers files. The band lane wrote no file during the round.

**The starts** were 23 in all:

- 9 held family and readers layouts that had no pass on that packing. The assembly of round 14 took them in after the last look of that round. They are 935 and 651 (family), and 597, 933, 872, 707, 701, 813 and 756 (readers). Round 14 ran 701 and 935 from earlier files of the same n, 1.6e-6 and 1.2e-5 above the held packing.
- 6 held n of round 14 got no start: 502, 604, 868, 914, 928 and 981. The newest step of each is an fq quench of a family or readers file that had its pass in round 13 or 14. Each held packing is at most 3.5e-8 of score below that file.
- 14 files that the family lane (9) and the readers lane (5) wrote during the round. The looks every 10 minutes found 0, 1, 2, 1, 0, 0, 3 and 2 files. Looks by hand at 09:59Z, 10:16Z and 10:21Z found 2, 1 and 1. One of the 14 is the family 912 again on boxD (below).

| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| family, in the held file | 2 | 2 | 0 | 0 | 0 | 4 | 113,706 | 0 | 0 |
| family, written during the round | 9 | 8 | 1 | 0 | 0 | 17 | 290,369 | 0 | 0 |
| family (readers), in the held file | 7 | 7 | 0 | 0 | 0 | 14 | 340,383 | 0 | 0 |
| family (readers), written during the round | 5 | 5 | 0 | 0 | 0 | 12 | 325,147 | 2: 746, 802 | 11 |
| **all** | 23 | 22 | 1 | 0 | 0 | 47 | 1,069,605 | 2 | 11 |

- The start cut short is the family 975 of 10:21Z. It is 6e-9 below the family 975 that had a dry pass at 10:14Z. Its first island ran 112 s to the deadline and found nothing.

**Finds on 2 n, both readers files of the round.** 746 and 802 are 1 shell up from the held 691 and 745, two jonathan1506 layouts. The readers lane wrote them at 09:16Z, 1.459e-04 and 9.460e-05 below the held file.

| n | start | island at `2e-4`, 140 s | island at `1e-4`, 140 s | island after the find | fq quench | own gain, certified |
|---|---|---|---|---|---|---|
| 802 | `take-readers-r15`, found by the look of 09:17Z | 23,300 children, 0 finds | 1,300 children, 2 finds, 2.139e-05 | 66,043 children, 5 finds, the last at 369 s, ended dry at 729 s, 2.427e-05 | 1.045e-05 | 5.611e-05 |
| 746 | `take-readers-r15`, found by the look of 09:17Z | 16,202 children, 2 finds, 8.395e-06 | 11,823 children, 1 find, 2.583e-06 | 95,706 children, 1 find, the last at 293 s, ended dry at 653 s, 4.917e-06 | 7.182e-06 | 2.308e-05 |

- The 11 finds by move: twist 4, jiggle 3, first relaxation with no move 3, row 1. 3 of the 11 came through the ladder.
- **A second fq quench from the float-safe rows finds nothing.** The corners lane saw this on a raw build. There the fq quench stopped on the raw rows and went on from the float-safe rows. `ctl.py cq N TAG` quenches the take file of an n in a fresh dir, and `collect` reads its steps. On 746 and 802 it ended 1.4e-9 of side below the take file, under the 3e-9 step of `fqjob.py`. That is the float-safe scaling and no more. Our chain quenches the raw best packing after the island, and that quench gained 7.2e-6 and 1.0e-5 of score.

**Certified** against `gate/cand-round14-1112a/details.csv` (floatsafe at 2.2e-11). `methods_take.py` on the two raw files keeps the same scores and writes byte-identical files.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 746 | `take-readers-r15` | 27.799033591 | 27.795047565 | 27.794417275 | 1.690e-04 | 2.308e-05 |
| 802 | `take-readers-r15` | 28.799148763 | 28.796469760 | 28.794880646 | 1.507e-04 | 5.611e-05 |
| **total** | | | | | **0.0003197** | **0.0000792** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r15` on boxA, and the logs of every island under `work/boxC/run/`, `work/boxD/run/` and `work/boxA/run/` there. Nothing was submitted from here. The two results went to the readers, family and polish lanes at 09:41Z (`handoff-r15.log`).

**boxA was starved, so its slot stopped at 10:04Z.** Our island there had 99.7% of a core at 08:57Z (load 3.5). At 10:04Z it had 27% (load 28 to 31). The pass on the family 912 made 5,548 and 4,835 children there. The same file then ran on boxD and made 21,001 and 19,140. Both passes were dry. From 10:04Z the watch sent new files to boxC and boxD only (`active.txt`). Our islands there had 98% to 99% of a core in each sample, at loads of 0.9 to 16.5.

**Driver changes.**

- `ctl.py` reads the take dirs of round 15, with `take-band-r15` as a third kind of `FIRST`. `RESEED` is off.
- `ctl.py cq N TAG` is the quench of the take file above. `collect` reads `W/cq/run` like a box.

What the round shows:

- **Finds come from files that move their n far.** 9 of the 23 starts are more than 1e-5 below the score they replaced. 2 of them found. None of the 14 other starts found, and 11 of those 14 are under 1e-6 below that score.
- **Both finds came from readers files.** None of the 10 family starts with a full pass found. Over rounds 11 to 15, 13 of 156 family and readers starts with a full pass found.
- **The supply of new files was the limit again.** The slots ran islands or quenches for about 40% of the round. The rest of the time they waited for new files.

## 3j. Round 16: modules files, and a loop through three lanes

The round ran on 2026-11-12 from 12:09Z to 13:45Z, with the fq quench inside that time. The CPU was 2 processes on boxC, 1 on boxD and 1 on boxA for the whole round. In all, the round ran 92 islands, 2,033,569 children and about 3.8 CPU-hours. boxC ran 44 islands (1,031,533 children), boxD 26 (558,699) and boxA 22 (443,337).

**The chain** is the chain of round 15 (section 3i). `RESEED` is off. No idle slot ran an island on a start whose pass was dry.

**The starts** were 45 in all. 44 had their full pass, and 1 was stopped by hand.

- 5 held family and readers layouts of round 15 that had no pass on that packing: 655, 761 and 910 (readers), and 912 and 812 (family). The held 912 and 812 are 3.6e-8 and 7.3e-10 below files that had a dry pass in round 15. 868, 871 and 985 had their pass in round 15. The other 40 n that round 15 moved are not family or readers steps.
- 29 files that the watch found: 17 family, 7 readers, 1 band and 4 modules. The watch looked 33 times, every 2 to 3 minutes, and found 0 to 5 files each time.
- 6 files of the modules and corners lanes that `handoff-r16.log` named. `ctl.py add` put them at the head of a queue by hand. They are the modules 921, 984 and 549, and the corners 863, 702 and 600. The corners 702 is 2.4e-5 of side above the bar, so its start counts from the held score.
- 5 starts on idle slots from held packings of another kind: 642, 922, 862 (twice) and 507. Each is an fq quench of a new public layout of round 15 (jonathan1506, jazivxt), 7.0e-5 to 3.4e-4 below the score it replaced. `addheld.py` makes these starts.

After the modules 549 found at 12:40Z, the watch also read `take-modules-r16`. It took a modules file only when the file was more than 1e-6 below held.

| kind of start | starts | passed | stopped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|
| family, in the held file | 2 | 2 | 0 | 4 | 97,161 | 0 | 0 |
| family, written during the round | 17 | 17 | 0 | 35 | 780,461 | 1: 596 | 10 |
| readers, in the held file | 3 | 3 | 0 | 6 | 161,184 | 0 | 0 |
| readers, written during the round | 7 | 7 | 0 | 14 | 341,359 | 0 | 0 |
| band, written during the round | 1 | 1 | 0 | 2 | 46,705 | 0 | 0 |
| modules, written during the round | 7 | 7 | 0 | 16 | 332,701 | 2: 549, 700 | 11 |
| corners, written during the round | 3 | 3 | 0 | 6 | 107,018 | 0 | 0 |
| held, an fq quench of a public layout | 5 | 4 | 1 | 9 | 166,980 | 0 | 0 |
| **all** | 45 | 44 | 1 | 92 | 2,033,569 | 3 | 21 |

- The start stopped by hand is 862 on boxC. The same start also ran on boxD, so the copy on boxC stopped after 4,950 children.

**Finds on 3 n.** All three are steps of a loop through three lanes:

1. Our chain found on the modules 549 (12:40Z). The modules lane had built it on the held 549.
2. The family lane went 1 shell up from our 549 to a 598 file. The modules lane put a corner of that 598 file into a 700 file, 3.64e-5 below held.
3. Our chain found on that modules 700 (13:11Z).
4. The family lane went 2 shells down from our 700 to a 596 file, 1.73e-4 below held.
5. Our chain found on that family 596 (13:32Z).

The family lane also took our 549 1 shell down and 1 up again. That file is 1.27e-5 below ours, so it holds 549.

| n | start | island at `2e-4`, 140 s | island at `1e-4`, 140 s | island after the find | fq quench | own gain, certified |
|---|---|---|---|---|---|---|
| 549 | `take-modules-r16`, added by hand at 12:36Z | 13,632 children, 4 finds, 3.581e-05 | 25,538 children, 0 finds | 71,136 children, 0 finds, ended dry at 360 s | 1.702e-05 | 5.283e-05, then the family lane's file held 549 |
| 700 | `take-modules-r16`, found by the look of 13:07Z | 2,900 children, 3 finds, 5.956e-05 | 377 children, 4 finds, 2.461e-05 | 57,031 children, 0 finds, ended dry at 360 s | 7.360e-06 | 9.153e-05 |
| 596 | `take-family-r16`, found by the look of 13:23Z | 8,600 children, 4 finds, 4.739e-05 | 12,751 children, 3 finds, 1.650e-05 | 104,539 children, 3 finds, the last at 173 s, stopped by the deadline at 533 s, 1.859e-05 | 3.048e-05 | 1.130e-04 |

- The 21 finds by move: twist 7, first relaxation with no move 5, jiggle 3, row 2, arm 2, cluster 1, re-angle 1. 6 of the 21 came through the ladder.
- The fq quench of each take file from its float-safe rows (`ctl.py cq`) gained 4.1e-10 of score on 700 and nothing on 549 and 596.

**Certified** against `gate/cand-round15-1112a/details.csv` (floatsafe at 2.2e-11). `methods_take.py` on the two raw files keeps the same scores and writes byte-identical files.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 596 | `take-family-r16` | 24.877799458 | 24.873586395 | 24.870828695 | 2.855e-04 | 1.130e-04 |
| 700 | `take-modules-r16` | 26.901756846 | 26.900793222 | 26.898371523 | 1.280e-04 | 9.153e-05 |
| **total** | | | | | **0.0004135** | **0.0002045** |

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r16` on boxA, and the logs of every island under `work/boxC/run/`, `work/boxD/run/` and `work/boxA/run/` there. Nothing was submitted from here. `take.tsv` was current from 12:40Z on. `collect` wrote 13 lines to `handoff-r16.log`, one for each new or lower certified n. The polish lane quenched our 549 within 10 minutes of its line.

**CPU.** Our islands had 92% to 99% of a core on boxC and boxD, at loads of up to 58 on boxC. On boxA they had 61% to 98% of a core at loads of 8 to 20, so its slot ran to the end. The slots ran islands for about 59% of the round (13,590 of 23,040 slot-seconds).

**Driver changes.**

- `ctl.py` reads the take dirs of round 16. `take-modules-r16` is a fourth kind of `FIRST`, with `MIN_STEP` 1e-6.
- `plan` and `watch` put the largest step first, whatever the kind. Round 15 found only on starts more than 1e-5 below the score they replaced. An idle worker takes a line within 10 s of its push, so `watch` now pushes the largest step first. In this round a 1e-10 step ran first and a 4.2e-5 step waited 4 minutes.
- `watch` skips a file less than 1e-8 below a start of its n (`SAME`). Such a file is the same packing.
- `collect` writes a line to the handoff log for each new or lower certified n. `watchloop.sh` collects after each look and looks every 2 minutes, so `take.tsv` stays current. It stops on `W/STOPWATCH`. A `STOP` in `boxA/` now stops only the boxA slot.
- `add` keeps the source of the file from the lane's take table. A lane can drop an n from its table later, and the modules lane dropped 549.
- `addheld.py N BOX` makes a start from the held packing of N, of any kind, with its held source.

What the round shows:

- **Modules files find.** 2 of 7 modules starts found. In round 11, 0 of 19 found. Both modules files of this round are built on family layouts of our own soft results.
- **The lanes pass layouts on to each other.** Soft 549 went to family 598 and then to modules 700. From there it went to soft 700, family 596 and soft 596. Our three finds came out of this loop, and each one gave the next lane a new start.
- **Step size still matters, but a big step is not enough.** 2 of the 20 starts more than 1e-5 below held found. 1 of the 25 others found: the modules 549, 4.5e-6 below held. None of the 12 starts under 1e-6 found.
- **Held fq quenches of public layouts do not find.** The 4 full passes on 642, 922, 862 and 507 found nothing, with steps of 7.0e-5 to 3.4e-4.
- **The supply of new files was the limit again.** The slots ran islands for about 59% of the round.

## 3k. Round 17: the files of seven new lanes, and three cuts

The round ran on 2026-11-12 from 15:27Z to 20:03Z. It stopped three times. boxA panicked at 16:15Z and every process on it died. The lane came back at 17:43Z. Two usage limits cut the agent at about 18:00Z and at 19:05Z, but the jobs on the other boxes kept running. The CPU was 1 process on boxC, 1 on boxD and 1 on boxA. After 17:43Z the boxA slot moved to boxE. At 19:10Z boxE slot stopped, because boxE load was 67 on 18 cores. Its queue went to the other two boxes.

**The chain** is the chain of round 16 (section 3j). `RESEED` is off. No idle slot ran an island.

**The starts.** The watch read 15 take dirs of round 17. They are the 4 lanes of round 16 (family, readers, band and modules) and 11 more (twoshort, stair-b, stair-c, classfill, midm, rigidsoft, k123, invent, border, corners and polish). Twoshort, stair-b and stair-c files go before every other kind, largest step first. A file of a new lane starts only if it is more than 1e-6 below held (1e-5 for polish).

| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| family, in the held file | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| family, written during the round | 24 | 20 | 0 | 3 | 1 | 40 | 873,232 | 0 | 0 |
| family (readers), written during the round | 14 | 9 | 0 | 2 | 3 | 18 | 455,023 | 0 | 0 |
| modules, written during the round | 5 | 3 | 0 | 1 | 1 | 6 | 155,919 | 0 | 0 |
| border, written during the round | 7 | 3 | 0 | 3 | 1 | 6 | 111,524 | 0 | 0 |
| twoshort, in a take dir at the plan | 13 | 11 | 0 | 0 | 2 | 24 | 412,502 | 1: 852 | 3 |
| classfill, in a take dir at the plan | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| midm, in a take dir at the plan | 5 | 4 | 0 | 1 | 0 | 8 | 406,843 | 0 | 0 |
| twoshort, written during the round | 6 | 4 | 0 | 1 | 1 | 8 | 148,576 | 0 | 0 |
| midm, written during the round | 28 | 21 | 0 | 5 | 2 | 43 | 980,350 | 1: 986 | 2 |
| classfill, written during the round | 4 | 3 | 0 | 1 | 0 | 6 | 110,042 | 0 | 0 |
| corners, written during the round | 19 | 13 | 0 | 3 | 3 | 27 | 574,838 | 1: 914 | 2 |
| stair-b, written during the round | 1 | 0 | 0 | 0 | 1 | 2 | 54,164 | 0 | 0 |
| stair-c, written during the round | 13 | 11 | 0 | 1 | 1 | 22 | 483,860 | 0 | 0 |
| invent, written during the round | 2 | 2 | 0 | 0 | 0 | 4 | 139,463 | 0 | 0 |
| k123, written during the round | 4 | 2 | 0 | 2 | 0 | 4 | 121,894 | 0 | 0 |
| **all** | 148 | 106 | 0 | 24 | 18 | 218 | 5,028,230 | 3 | 7 |

- In all, the round ran 218 islands, 5,028,230 children and about 8.8 CPU-hours. boxC ran 90 islands, boxD 87, boxE 36 and boxA 5.
- 24 starts did not run before the deadline. 18 starts were dropped, because a lower file of the same n came in before they began.

**Finds on 3 n**, 7 finds in all: twist 4, jiggle 2 and the first relaxation 1. 2 came through the ladder.

| n | start | pass at `2e-4` | pass at `1e-4` | island | fq quench | own gain certified |
|---|---|---|---|---|---|---|
| 852 | twoshort, in a take dir at the plan (two) | 18,151 children, 0 finds | 14,100 children, 1 finds, 2.966e-05 | 36,667 children, 2 finds, last at 142 s of 502 s, 5.073e-05 | 6.188e-05 | not kept |
| 914 | corners, written during the round (cor) | 11,400 children, 1 finds, 7.928e-06 | 14,257 children, 0 finds | 48,800 children, 1 finds, last at 60 s of 420 s, 6.872e-06 | 4.942e-06 | 1.974e-05 |
| 986 | midm, written during the round (mid) | 13,277 children, 0 finds | 3,568 children, 1 finds, 1.913e-05 | 19,370 children, 1 finds, last at 73 s of 279 s, 3.117e-06 | 1.828e-05 | 4.052e-05 |

**Certified** against `gate/cand-round16-1112a/details.csv` (floatsafe at 2.2e-11). A result counts only if it is also below every live take dir of round 17 by more than 1e-10.

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 914 | corners, written during the round | 30.732158674 | 30.729163923 | 30.728567066 | 1.188e-04 | 1.974e-05 |
| 986 | midm, written during the round | 31.851902845 | 31.848946389 | 31.847674022 | 1.347e-04 | 4.052e-05 |
| **total** | | | | | **0.0002535** | **0.0000603** |

- The 852 find tied the family lane. The family lane quenched the same twoshort 852 file, and its file is 3.7e-14 from ours. So the 852 result went back out of `take.tsv` at 16:01Z.
- The 914 find is in the round 17 file that scored 22.1635211736.
- The 986 find came at about 19:51Z on boxC, after the round 17 file was built. It is for round 18.

The per-n file and `take.tsv` are in `<scratch>/bounties-squares/take-soft-r17` on boxA. The logs of every island are under `work/boxC/run/`, `work/boxD/run/`, `work/boxE/run/` and `work/boxA/run/` there. Nothing was submitted from here.

**Driver changes.**

- `ctl.py` reads the round number from `RN`. It watches the 15 take dirs above. `LEAD` puts twoshort, stair-b and stair-c files first.
- `collect` drops a result that does not beat every live take dir by more than 1e-10. In round 16 a tie counted.
- `SAME` is 1e-7 now. The family lane's quench of a twoshort file sits 1e-8 to 3e-8 below that file. It is the same packing.
- `plan` uses `MIN_STEP` too, as `watch` did.
- `status.sh`, `stats.py` and `mdtables.py` read boxE slot too.

What the round shows:

- **Finds come from new designs with a big step.** The 3 finds are on a twoshort, a corners and a midm file. Each start was more than 9e-5 below held. The 53 passed family, readers, modules, border, classfill, stair, invent and k123 starts found nothing.
- **Midm files find now, but rarely.** 1 of 25 passed midm starts found (986), for 980,350 plus 406,843 children.
- **A find on a file another lane also quenches can tie.** The 852 find and the family lane's quench of the same file are the same packing. The tie rule in `collect` now drops such a result.
- **Stair-c files did not find.** 11 passed, 0 finds, 483,860 children.
- **The cuts cost time, not results.** The jobs on the other boxes ran on through the two usage limits.

## 3l. Round 19: new designs only, and two finds that other lanes beat

The round ran on 2026-11-12 from 20:26Z to 22:11Z. The CPU was 1 process on boxC and 1 on boxD. No process ran on boxA or boxE. The held file was the round 17 file (`gate/cand-round17-1112a`). A result had to beat it and every frozen `take-*-r17` dir and every live `take-*-r19` dir.

**The rule of the round.** The chain is the chain of section 3j. `RESEED` is off, and no idle slot ran an island. The controller picks a start in this way:

- An n qualifies when a file of the twoshort, corners or midm lanes is more than 9e-5 below held. Rigidsoft, invent, modules and forensics files use the same bar.
- Family, readers, border, classfill, stair-c and k123 files qualify only above 1e-4.
- The start is the lowest file of that n in any watched dir. So a twoshort file starts from the family lane's quench of it when there is one.
- A twoshort file with no family file waits 30 minutes for the quench.
- Twoshort and corners files go first, then midm. The other kinds go to the tail of the queue.
- Three of the midm lane's kicked finds ran first (509, 817 and 510). The rest (454 and 981) waited for a find among them.
- A packing that had its pass in round 17 does not start again.

The control of `pick()` printed the expected answers. A family file 9.5e-5 below held gave no start, and one 1.1e-4 below gave a start. A corners file 9.5e-5 below started from a lower family file of the same n. A corners file 8e-5 below gave no start.

**The plan found few starts.** The round 17 file already holds most new-design rows. Only 1 corners file (984) was more than 9e-5 below held. Only 1 twoshort file (913) was, and it had no family quench and waited. No midm file was, except 986, which had its pass in round 17. 5 n had their pass in round 17 (595, 754, 802, 851 and 986). Most later starts came from the watch.

| kind of start | starts | passed | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|
| family | 6 | 3 | 0 | 3 | 6 | 120,710 | 0 | 0 |
| family (readers) | 8 | 6 | 1 | 1 | 12 | 215,796 | 0 | 0 |
| modules | 1 | 1 | 0 | 0 | 2 | 40,091 | 0 | 0 |
| border | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| corners | 1 | 1 | 0 | 0 | 2 | 32,509 | 0 | 0 |
| midm, kicked finds (509, 817, 510) | 3 | 3 | 0 | 0 | 6 | 164,919 | 0 | 0 |
| midm, written during the round | 13 | 10 | 2 | 1 | 20 | 688,172 | 0 | 0 |
| twoshort | 1 | 1 | 0 | 0 | 2 | 37,996 | 0 | 0 |
| stair-c (2 of them near layouts from the handoff log) | 7 | 3 | 3 | 1 | 6 | 116,664 | 0 | 0 |
| k123 | 13 | 8 | 3 | 2 | 17 | 718,245 | 1: 295 | 5 |
| rigidsoft | 4 | 3 | 0 | 1 | 7 | 321,435 | 1: 365 | 7 |
| invent | 4 | 2 | 0 | 2 | 4 | 67,933 | 0 | 0 |
| classfill | 2 | 1 | 1 | 0 | 2 | 34,984 | 0 | 0 |
| forensics | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **all** | 65 | 42 | 11 | 12 | 86 | 2,559,454 | 2 | 12 |

- In all, the round ran 86 islands, 2,559,454 children and about 3.5 CPU-hours. Each box ran 43 islands.
- The 12 finds were twist 5, angle 3, jiggle 1, row 1, cluster 1 and the first relaxation 1. 2 came through the ladder.
- The kicked midm sample found nothing in 3 of 3 starts. So 454 and 981 did not run.

**Two finds, both beaten by another lane.**

| n | start | pass at `2e-4` | pass at `1e-4` | island | fq quench | best certified | own gain | lowest live file at the end |
|---|---|---|---|---|---|---|---|---|
| 295 | k123 join file | 37,228 children, 5 finds, 7.903e-05 | 43,304 children, 0 finds | 121,007 children, 0 finds | 5.433e-06 | 0.030424094434 | 8.446e-05 | midm 0.030421258578 |
| 365 | rigidsoft band file | 27,700 children, 6 finds, 5.779e-05 | 38,285 children, 1 find, 3.674e-06 | 104,691 children, 0 finds | 2.484e-05 | 0.026371022536 | 8.630e-05 | rigidsoft 0.026344166769 |

- Both certified below held: 295 by 3.562e-4 and 365 by 2.128e-4. The collect kept 295 from 21:24Z and wrote its handoff line. A later collect dropped it.
- The midm lane kicked and quenched the same k123 file of 295 and reached 0.03042409443350702. Our quench reached 0.030424094433562088, which is 5.5e-14 higher. It is the same packing. Then the midm lane kicked our 295 file and reached 0.030421258578.
- On 365 the midm kick of the same rigidsoft file reached 0.026349054472. Then the rigidsoft lane reached 0.026344166769.
- So `take.tsv` is empty at the end. Our 295 file is the start of the lowest live 295.

The table is `results/soft-r19-2026-11-12.tsv`. The logs of every island are under `work/boxC/run/` and `work/boxD/run/` in `<scratch>/bounties-squares/take-soft-r19` on boxA. Nothing was submitted from here.

**Driver changes.** `ctl.py` is set for round 19:

- It watches the take dirs of 18 lanes in round 17 and round 19.
- `pick()` holds the rule above.
- The collect checks a result against the frozen r17 dirs and the live r19 dirs.
- `push` can add a line at the tail of a queue.
- boxE is out of `REMOTE`.
- `prev_passes` reads boxE logs of round 17 by name.

What the round shows:

- **The soft box finds on fresh block designs at small n.** Both finds came from files a few minutes old. In each, a lane had just built a new block layout (a k123 join, a rigidsoft band). Such files are far from a local optimum. 2 of 11 passed k123 and rigidsoft starts found.
- **The midm kick gets there first on the same files.** The midm lane kicks and quenches every new file of another lane within minutes. On both n it reached the same or a lower packing. A soft find on a fresh file counts only if it beats that kick.
- **The round 17 pattern did not repeat.** The corners 984, twoshort 913, midm and kicked midm starts found nothing (0 of 15 passed).
- **Family, readers, modules, stair-c, invent and classfill starts found nothing**, as in round 17 (0 of 16 passed).

## 3m. Round 20: one find on a fresh corners file

The round ran on 2026-11-12 and 2026-11-13 from 22:39Z to 00:40Z. The CPU was 1 process on boxC and 1 on boxD. No process ran on boxE. On boxA only the watch loop ran. The held file was the round 18 file (`gate/cand-round18-1112a`). A result had to beat it and every frozen `take-*-r19` dir and every live `take-*-r20` dir.

**The rule of the round.** The rule is the rule of section 3l, with four changes in `ctl.py`:

- k123 and rigidsoft files go first. Round 19 found on 2 of 11 such starts and on 0 of 31 others.
- k123 files now use the 9e-5 bar, not the 1e-4 bar.
- Midm, invent, twoshort and corners files come next. The other kinds go to the tail of the queue.
- No kicked midm sample ran.

The control of `pick()` printed the expected answers. A k123 file 9.5e-5 below held gave a start, and one 8e-5 below gave none. A family file 9.5e-5 below gave none. A rigidsoft file 9.5e-5 below started from a lower midm file of the same n.

By hand, I added the rigidsoft file of 907 at the head of the boxD queue. It sat 7.1e-5 below held, under the bar.

boxA rebooted at about 22:48Z. The watch loop died and came back at 22:51Z. The two box workers ran on without a break.

| kind of start | starts | islands | children | n with a find | finds |
|---|---|---|---|---|---|
| k123 (3 of them midm kicks of k123 files) | 10 | 20 | 672,832 | 0 | 0 |
| corners | 4 | 9 | 276,891 | 1: 646 | 4 |
| midm | 4 | 8 | 217,467 | 0 | 0 |
| forensics | 2 | 4 | 160,630 | 0 | 0 |
| stair-c | 4 | 8 | 149,806 | 0 | 0 |
| invent (1 of them a readers file) | 3 | 6 | 112,800 | 0 | 0 |
| classfill | 3 | 6 | 110,850 | 0 | 0 |
| polish (the polish lane's quench of our 646) | 2 | 4 | 103,626 | 0 | 0 |
| family | 2 | 4 | 85,804 | 0 | 0 |
| modules | 1 | 2 | 36,214 | 0 | 0 |
| rigidsoft | 1 | 2 | 34,726 | 0 | 0 |
| **all** | 36 | 73 | 1,961,646 | 1 | 4 |

- Every start passed. The queues ran dry at about 23:45Z, and after that the watch fed the slots.
- The 4 finds were angle 2, twist 1 and arm 1.

**One find, on 646.**

| n | start | pass at `2e-4` | pass at `1e-4` | island | best certified | own gain | gain on held |
|---|---|---|---|---|---|---|---|
| 646 | corners file, 1.760e-4 below held | 24,316 children, 0 finds | 12,595 children, 2 finds, 9.268e-06 | 108,170 children, 2 finds, 9.147e-06 | 0.018042203488 | 3.229e-05 | 2.083e-04 |

- The fq quench of each find on boxD added the rest of the own gain.
- The polish lane quenched our file and reached 0.018042208617, which is 5.1e-12 above ours. So our 646 stays in `take.tsv`.
- The midm lane did not kick this corners file before us.

The table is `results/soft-r20-2026-11-13.tsv`. The logs of every island are under `work/boxC/run/` and `work/boxD/run/` in `<scratch>/bounties-squares/take-soft-r20` on boxA. Nothing was submitted from here.

What the round shows:

- **The k123 and rigidsoft lead did not repeat.** 0 of 11 such starts found this round. With round 19, the count is 2 of 22.
- **A fresh corners file found.** The corners file of 646 was minutes old and 1.76e-4 below held. In round 19, corners files found on 0 of 1 starts.
- **Old kinds stay dry.** Family, stair-c, classfill, invent, modules, forensics and midm files found nothing in 23 starts.
- **The soft step pays only on a file that no other lane has kicked yet.** The one find came from a file that no other lane had touched.

## 3n. Round 21: 43 starts on new files, no find

The round ran on 2026-11-13 from 01:04Z to 03:25Z and again from 09:50Z to 12:12Z. The CPU was 1 process on boxC and 1 on boxD. On boxA only the watch loop ran. The held file was the round 19 file (`gate/cand-round19-1112a`). A result had to beat it and every frozen `take-*-r20` dir and every live `take-*-r21` dir.

**The rule of the round.** The rule is the rule of section 3m, with four changes in `ctl.py`:

- Corners files go first. Round 20 found on 1 of 4 such starts.
- k123, rigidsoft, midm and twoshort files come next. k123 and rigidsoft found on 2 of 22 starts over rounds 19 and 20.
- Invent, modules, forensics and polish files join the 1e-4 tail. Such files found on 0 of 39 starts over rounds 19 and 20.
- The watch skips the polish lane's quench of a file we hold. It also stops a running start when a lower file of the same n arrives. `stop_run()` writes a STOP file in the run dir and kills the soft process.

The control of `stop_run()` printed the expected answers. A dummy soft process in a test run dir gave True and was killed. A second call gave False.

The limit of an account ended the first run at about 01:30Z. The box workers ran on until their deadline at 03:25Z. boxA rebooted at 05:36Z. At 09:50Z the queues started again with new deadlines.

| kind of start | starts | islands | children | n with a find | finds |
|---|---|---|---|---|---|
| midm | 18 | 36 | 829,248 | 0 | 0 |
| readers | 12 | 22 | 471,285 | 0 | 0 |
| polish | 4 | 8 | 187,706 | 0 | 0 |
| harvest | 3 | 6 | 122,859 | 0 | 0 |
| invent | 3 | 6 | 112,700 | 0 | 0 |
| k123 | 1 | 2 | 35,987 | 0 | 0 |
| border | 1 | 2 | 33,209 | 0 | 0 |
| family | 1 | 2 | 35,783 | 0 | 0 |
| **all** | 43 | 84 | 1,828,777 | 0 | 0 |

- 17 starts ran before the cut and 26 after it. 42 starts passed. One start did not begin before the deadline.
- No corners file came under the bar while the queues ran. So the lead of the round never had a start.
- Other lanes moved most of these n again within 10 to 30 minutes. 752 and 929 had 8 starts each, 868 had 7 and 809 had 5.
- The watch dropped one start before it began. The stop of a running start never fired: each dry start ended in about 5 minutes, before a lower file of its n came.

The take is empty, and `results/soft-r21-2026-11-13.tsv` holds only its header. The logs of every island are under `work/boxC/run/` and `work/boxD/run/` in `<scratch>/bounties-squares/take-soft-r21` on boxA. Nothing was submitted from here.

What the round shows:

- **The soft step found nothing on files that other lanes keep moving.** In round 21, the follow lanes went below most new files within minutes. The soft pass then searched packings that were already old.
- **The pass is dry on most kinds now.** Over rounds 19 to 21, 3 n had a find in 121 starts. In round 19, 2 came from k123 or rigidsoft files. In round 20, 1 came from a corners file. No other lane had kicked these files yet.
- **A slot gives more when it waits for a fresh corners or k123 file.** The next round can keep the slot for these kinds and skip the rest.

## Round 22

The final take holds 1 n. It gains 9.42221251756e-05 against round 20 and 1.53357639083e-05 over all other takes.
The comparison includes every frozen round 21 take and every live round 22 take.
Sources and licences are in [the results table](../results/soft-r22-2026-11-13.tsv).

One search process ran on boxC and one on boxD. No search ran on boxA or boxE.
The worker deadline was 15:20 UTC. Intake ended at 15:15 UTC.
The search used the round 20 gate throughout.

### Search

Fresh corners, k123 joins and rigidsoft faults went first.
Complete designs got two 140-second islands, then a continuation and quench on a find.
Other fresh near layouts got two 20-second probes, with the same continuation on a find.
The queue took fresh round 22 files instead of the old broad backlog.

| kind | queued | started | passed | finds |
|---|---|---|---|---|
| corners | 30 | 20 | 19 | 0 |
| k123 | 24 | 21 | 21 | 2 |
| forensics | 125 | 36 | 36 | 0 |
| classfill | 19 | 0 | 0 | 0 |
| twoshort | 98 | 3 | 3 | 0 |
| modules | 37 | 1 | 1 | 0 |
| stair-c | 60 | 6 | 6 | 0 |
| rigidsoft | 57 | 8 | 7 | 12 |
| border | 17 | 3 | 3 | 2 |

The round ran 201 islands and 3,675,367 children in 19,386 island-seconds.
There were 16 finds on 4 n: 297, 328, 494, 539.
Of the 467 queued starts, 90 were dropped before starting and 279 did not start before the deadline.
Controls and certificate-only quenches are excluded from these counts.

| n | held score | new score | gain against round 20 |
|---|---|---|---|
| 494 | 0.022825412554 | 0.022731190429 | 9.422e-05 |

The fresh k123 n=494 join found once, at 151 seconds in its first island.
That find gained 9.001e-6 of score. The raw quench added 6.335e-6.
Its continuation found nothing in 360 seconds.
A quench from the certified soft file reached the same floor before publication at 14:07 UTC.
The source joins held n=450 with the frozen round 21 n=494 at chain 10.

The k123 n=539 start found 8.618e-6, then quenched to the same side fraction as n=494.
A border n=539 start also reached that floor. At 14:29 UTC, another lane held n=539 there. Neither layout counted at that handoff.
The rigidsoft starts produced legal near layouts of n=297 and n=328.
Their handoff sides were 17.739478138800 and 18.613038868949.
They remained above the bar and went to the other lanes through the handoff log.

### Controls and collection

The atlas n=644 control made five finds in its first 147 seconds.
Its side fell from 25.854927027286 to 25.853210265678.
The expanded n=3 probe recovered side 2.000000000040 from 2.010000000050 in 20 seconds.
The certified n=3 quench reported two successful calls with no retained change.

The final controller checks accepted held n=3 and refused an overlapping n=2.
They checked queue order, 30 donor versions, geometric copies and the rule for stopping old starts.
The publication check refused missing and unsuccessful quenches, then accepted a completed quench.
Its log is `take-soft-r22/work/logs/controls-final.log` on boxA.
Python compilation, shell syntax and the diff check passed.

Every published result passes floatsafe at 2.2e-11 clearance.
It also passes an fq quench from its certified file on a remote worker before publication.
The collector can keep a completed certificate while a lower candidate waits for its quench.

Queues sort inside each push. Certificates go first, followed by complete priority designs and their near layouts.
Other complete designs precede probes. Fresh raw k123 starts join the first design group. Old complete designs within a group go before newer ones.
A source lane publishing its own row no longer stops the search on that row.
Three starts stopped by that mistake were restored from their saved inputs.
A watcher typo also cost one cycle before its positive control passed.

The take and legal near files are under `<scratch>/bounties-squares/take-soft-r22`.
The log of each island is under its `work/boxC/run` or `work/boxD/run` folder.
Nothing was submitted from this lane.

## Round 23

The final take holds 1 n. It gains 0.000362797829614 against round 21.
Its gain over every frozen round 22 take and every other round 23 take is 0.000100658096129.
Sources and licences are in [the results table](../results/soft-r23-2026-11-13.tsv).

One search process ran on boxC and one on boxD. Both used scipy 1.18.1.
Intake ended at 18:25 UTC. Search and quenches shared the 18:30 UTC deadline.
The round used the round 21 gate throughout.

### Search

Fresh k123 joins and rigidsoft faults received two 140-second islands.
Fresh corners received two 60-second islands. Other fresh designs received two 20-second probes.
Early corners starts used 140 seconds. The n=503 find began after 26 seconds and reached the log at 37 seconds.
Each useful result went straight to fq. No 360-second continuation ran.
Both intake and near exports accepted fresh layouts within 0.015 of side above the competing bar.
The broad frozen near backlog stayed closed.

| kind | queued | started | passed | finds |
|---|---|---|---|---|
| k123 | 26 | 25 | 24 | 4 |
| border | 117 | 39 | 38 | 0 |
| family | 85 | 33 | 32 | 0 |
| stair-c | 73 | 25 | 24 | 0 |
| forensics | 48 | 17 | 17 | 0 |
| readers | 29 | 11 | 11 | 1 |
| corners | 21 | 20 | 19 | 6 |
| modules | 50 | 18 | 17 | 0 |
| invent | 20 | 8 | 8 | 0 |
| classfill | 29 | 14 | 14 | 0 |
| twoshort | 106 | 54 | 54 | 0 |

The logs cover 527 islands, 2,876,583 children and 18,591 island-seconds.
There were 11 finds. Controls and certificate-only quenches are excluded.
Of 604 queued starts, 35 were dropped before starting and 305 remained unstarted.
A pass means both initial islands ended. Killed or cut islands remain in the logged counts.

| n | kind | start tag | finds | start score | best certified score |
|---|---|---|---|---|---|
| 503 | corners | xcor1 | 6 | 0.020900233138 | 0.020798601042 |
| 503 | readers | xrea | 1 | 0.020900242384 | 0.020799265140 |
| 847 | k123 | k1223 | 4 | 0.017032734485 | 0.016932076389 |

The corners n=503 start came from a fresh family build, through a raw corners kick.
Its six finds gained 4.444e-5 of score. The raw quench added 5.720e-5.
The reader n=503 start gained 9.734e-6 before fq, then 9.124e-5 in fq.
Both remained above the competing harvest and polish result, whose score was 0.020774616365762943 at the audit.
The legal soft near file went to the handoff log at 16:06:58 UTC.
Its source follows family and reader steps from the areebbb public file. Its notice is Apache 2.0.

| n | held score | new score | gain against round 21 |
|---|---|---|---|
| 847 | 0.017294874219 | 0.016932076389 | 0.0003628 |

The late k123 n=847 join used held n=630 and a reader near file at n=734.
It joined the first band through chain 19 with the second band from chain 14, shifted two rows.
Four soft finds and the raw fq step reached side 29.596043118068 after certification.
The exact certified-file quench completed at 18:10:54 UTC with two successful calls and no retained change.
The first audit gained 0.000100658096 beyond its donor and every competing take.
Its source table records the held ancestry and the reader near file.

### Controls and fixes

The atlas n=644 control made four finds in 154 seconds.
It moved side 25.854927027286 to 25.853266058739.
The expanded n=3 probe recovered side 2.000000000040 from 2.010000000050 in 20 seconds.
Its certified-file quench completed two successful calls and retained no further change.

A 20-second n=507 probe spent over seven minutes inside its legaliser and was stopped.
[The wall limiter](../tools/softround/softjob.py) now allows the requested duration plus 45 seconds, capped by the common deadline.
Its positive child finished. Its sleeping child was killed after 0.2 seconds.
The final logs contain 2 wall-limit events.

The comparison briefly accepted n=503 while lower competing files were being replaced.
That row was withdrawn and the handoff log records the correction.
The collector now preserves ledger bars and certifies fresh competing files immediately.
An unverified recent replacement delays publication.
Controls covered missing CSVs, recent replacements, and the difference between intake and comparison scans.

The geometry controls covered translation, square order, rounding and all eight box symmetries.
Frozen round 22 geometry was indexed to refuse repeated starts under fresh filenames.
Changed priority layouts also entered geometry intake when their score barely moved.
Near metadata kept the full donor chain and licence.
An early watcher restart and a disappearing near file were recorded in STATE.txt.

Every retained row passes floatsafe at 2.2e-11 clearance.
Publication also requires a completed remote fq quench from its certified file.
Python compilation, shell syntax, controller controls and the diff check passed.

The take, near files and logs are under `<scratch>/bounties-squares/take-soft-r23`.
Both remote scratch directories were copied, verified and removed after the workers stopped.
Nothing was submitted from this lane.

## Round 24

The final take holds 1 n. Its gain against the round 23 candidate is -2.15383266777e-14.
Its gain beyond every other eligible live round 24 take is 0.000100658096104.
The gain against the submitted round 23b file is 0.000294380678882.

The 20:05 UTC source rule allows a clean replacement at twenty counts to beat round 22.
Those rows can match the smaller candidate-a packing that the source review held back.
Each licence cell names the GitHub seed counts or states that the row has none.
Sources and licences are in [the results table](../results/soft-r24-2026-11-13.tsv).

One search process ran on boxC and one on boxD. Both used scipy 1.18.1.
The base was `gather/round23-2026-11-13a.csv` and its candidate gate.
Automated intake last added a start at 21:49 UTC. Manual handoff checks continued through 22:12 UTC.
Search and quenches shared the 22:15 UTC deadline.

### Search

Priority k123 inputs received two 140-second islands. Fresh corners received two 60-second islands.
Other fresh layouts received two 20-second probes.
A find went straight to fq. Corners also received fq when both islands were dry.
The intake kept the 0.015 side margin for near layouts.
It refused geometry already searched in round 23.
A new licensed input could replay an old successful start at a source-held count.
Targeted unstarted reader and 847-related layouts preceded the older backlog.

| kind | queued | started | passed | finds |
|---|---|---|---|---|
| forensics | 83 | 16 | 15 | 2 |
| modules | 5 | 2 | 2 | 0 |
| twoshort | 9 | 3 | 3 | 0 |
| readers | 203 | 189 | 181 | 8 |
| invent | 12 | 1 | 1 | 0 |
| border | 10 | 3 | 3 | 0 |
| corners | 50 | 12 | 11 | 0 |
| k123 | 22 | 22 | 21 | 11 |
| harvest | 7 | 0 | 0 | 0 |
| midm | 7 | 0 | 0 | 0 |
| stair-c | 12 | 0 | 0 | 0 |
| family | 5 | 0 | 0 | 0 |
| licensed-rectangle | 1 | 1 | 0 | 1 |
| classfill | 1 | 0 | 0 | 0 |

The logs cover 498 islands, 2,306,984 children and 16,423 island-seconds.
There were 22 soft finds across 8 n.
Of 427 queued starts, 249 started and 237 completed both islands.
Another 56 dropped before starting and 122 remained unstarted.
Controls and certificate-only quenches are excluded.
The logs contain 14 wall-limit events.

| n | kind | tag | finds | input score | candidate score |
|---|---|---|---|---|---|
| 756 | forensics | xfor | 2 | 0.015837449376 | 0.015478289641 |
| 802 | readers | xrea | 1 | 0.017018435691 | 0.016761933447 |
| 701 | readers | xrea1 | 1 | 0.016816683269 | 0.016466498436 |
| 814 | readers | xrea1 | 2 | 0.014969642107 | 0.014501736286 |
| 757 | readers | xrea | 2 | 0.015459650908 | 0.015198108918 |
| 365 | k123 | xk121 | 5 | 0.026457325439 | 0.026344166769 |
| 692 | readers | xrea2 | 2 | 0.018695149858 | 0.018467059451 |
| 847 | licensed-rectangle | licensedrect24 | 1 | 0.017226457068 | 0.016932076389 |
| 847 | k123 | xk121 | 2 | 0.017032734485 | 0.016932076389 |
| 847 | k123 | xk122 | 4 | 0.017032734485 | 0.016932076389 |

Legal descents above the candidate went to `near/` with a source sidecar.
The rectangle n=756 start produced two soft finds, followed by further descent in fq.
Its first near export remained 0.00589 of side above the candidate.
The reader n=802 start also found, but its first quench remained above the candidate.

### Licensed 847

The rectangle control first exposed a 0.006165 overlap where its windows meet.
An inflated start and fq repair recovered certified side 29.600801736245.
The target used an immutable copy of the actual CC0-derived n=581.
Its two rectangle windows had symmetry tags 4 and 0, with three extra squares each.
The new raw overlap was 0.006870. Its repair reached certified side 29.600801736342.
That packing briefly qualified under the clean-source exception, then a lower licensed join superseded it.

The new join used the actual Apache n=630 and a new unpolished n=734 from the licensed rectangle.
It joined chains 19 and 14 with a shift of two rows.
Both soft starts reached the old numerical 847 floor after fq.
The certified-input quench completed at 22:12:11 UTC with two successful calls and no further change.
The source uses the new CC0 public input and original transformations.
It reaches no Samanyu-dev GitHub seed layout.

A family-reader check found no flush arms in the licensed rectangle.
The immutable unread copy and the measured banddown2 recipe went to the layer reader.
The recipe uses diagonal cut 12.900 for the 734 return.

### Controls and source records

The atlas n=644 control made six finds in 162 seconds.
Its side fell from 25.854927027286 to 25.853099825284.
The expanded n=3 control recovered side 2.000000000040 from 2.010000000050.
Its raw quench reported two successful calls and no further retained change.
A separate quench of the certified n=3 file also completed two successful calls.
A dry n=3 corner control completed both 60-second islands and two successful fq calls.

Ancestry checks accept the candidate and the allowed round 23 changed rows.
They refuse excluded public donors, unknown origins and missing metadata.
A current reader end passed only after the checker loaded its saved parent state.
Exact family near records needed their own table reader.
The controls accepted the real n=814 reader end and the n=595 family near file.
They also accepted the full n=646 producer record after its temporary donor file rotated away.
Unknown origins and a nested prohibited origin remained refused.
Affected fresh records were retried after these fixes.

The soft lane imports the producer checks in `readers_sources.py`, `forensics_sources.py` and `tools/harvest_follow.py`.
It records each admitted input's ancestry in `work/plan.json`.
Near sidecars retain the full source and licence for the next lane.
The original candidate-a source table is pinned in `work/candidate-a-sources.tsv`.
This preserves its seed notices after the submitted table drops the twenty held rows.
The source controls distinguish samanyu1808 CC0 data from the unlicensed Samanyu-dev GitHub seed.
They also retain every count in a multiple-seed notice.
Unlisted peer CSVs remain competing unknowns while their source ledger changes.
No other lane's tool or doc changed here.

Late intake delayed collection of 847 results that finished at 21:51 and 21:52 UTC.
The priority collector wrapper then hit a macOS multiprocessing entry-point error.
Serial collection fixed that error at 22:08 UTC. The remote workers continued through both delays.

The collector requires floatsafe at 2.2e-11 clearance for each retained row.
Publication also requires a completed remote fq quench from the certified input.
Python compilation, shell syntax, controller controls and the diff check passed.
The comparison preserves peer ledger bars while their CSVs change.

The take, near files and logs are under `<scratch>/bounties-squares/take-soft-r24`.
Both remote scratch directories were copied, verified and removed after the workers stopped.
Nothing was submitted from this lane.

## Round 26

The final take holds 2 n: 791, 814.
Its gain against the round 25 b base bar is 3.4625e-04.
Its gain beyond every other live round 26 take is 3.4625e-04.
Sources and licences are in [the results table](../results/soft-r26-2026-11-14.tsv).

Round 25 has no section here because its agent died at about 23:50 UTC on 2026-11-13.
Its driver ran on to the deadline and certified 534 and 597 for 0.00056.
Both rows went into the round 25 b file.

Two search processes ran on boxC and one on boxD, all on scipy 1.18.1.
The base bar was `gate/cand-round25-1114b/details.csv`.
Search stopped at 17:05 UTC and the quenches at 17:15 UTC.
The lane agent died between 16:20 and 16:33 UTC when its connection dropped.
The driver and the three box workers kept running, and a new agent adopted them at 16:35 UTC.

### What changed against round 25

- The idle fill now runs every minute.
  In round 25 it ran only at the end of a follow cycle that took 2 h 24 min, after its own cutoff.
  So boxC sat idle from 01:35 UTC and boxD from 02:13 UTC.
- The intake refuses every input whose source policy is not "none".
  Round 25 kept seed rows with a label.
- The provenance check resolves each row of the round 25 b file to its recorded take file.
  It reads the recorded text of every held root it reaches and refuses the round 26 markers, such as `921-29e12ff3.csv`.
- A border donor copy counts as its original when a traced take or near file of the same n has the same bytes.
- One island runs per n, and no island starts above the all-lane bar.
  Fresh midm kick files go first.
- A source-policy refusal is final, and other refusals wait 900 s.
  Before this change the follow loop traced every refused file every 120 s.
  Both boxes sat idle from 15:21 to 15:40 UTC at load 48 while it did.
- The driver runs at nice 5.
  A zsh background job adds 5 to nice, so it first ran at 10 and got a tenth of a core.

### Controls

Nine source controls were green (`work/logs/controls26.log`).
The new marker check refused the round 25 b 921.
The held 801 and the k123 round 25 982 were refused.
The rows 500, 534 and 597 were accepted.
The n=3 probe on boxD recovered side 2.000000000040 from 2.010000000050, with two successful fq calls.

### Search

Each fresh layout of another lane got a start within minutes of its handoff line.
k123 joins got two 140 s islands, other fresh files two 20 s islands, and an idle slot one 1800 s island.

| kind | mode | queued | dropped | started | passed | starts with a find |
|---|---|---|---|---|---|---|
| backlog | island | 3 | 1 | 2 | 2 | 0 |
| backlog | probe | 3 | 1 | 2 | 2 | 0 |
| border | probe | 2 | 0 | 2 | 2 | 0 |
| border | short | 2 | 0 | 2 | 2 | 0 |
| classfill | probe | 3 | 0 | 3 | 3 | 0 |
| forensics | island | 3 | 0 | 3 | 3 | 0 |
| forensics | probe | 48 | 0 | 48 | 48 | 5 |
| harvest | island | 5 | 1 | 4 | 4 | 1 |
| harvest | probe | 8 | 0 | 8 | 8 | 0 |
| invent | probe | 14 | 0 | 14 | 14 | 0 |
| k123 | island | 3 | 1 | 2 | 2 | 0 |
| k123 | short | 24 | 1 | 23 | 23 | 7 |
| midm | island | 8 | 0 | 8 | 8 | 2 |
| midm | probe | 9 | 1 | 8 | 8 | 0 |
| modules | probe | 24 | 0 | 24 | 24 | 0 |
| quench | probe | 3 | 0 | 3 | 3 | 0 |
| rebuild | probe | 1 | 0 | 1 | 1 | 0 |
| stair-c | probe | 88 | 0 | 88 | 88 | 1 |
| twoshort | island | 1 | 0 | 1 | 1 | 1 |
| twoshort | probe | 4 | 0 | 4 | 4 | 0 |

The soft logs hold 477 ended islands with 89 finds in all, and 0 wall-limit events.

### Results

- **791.** A 1800 s island on the midm fq kick file `take-midm-r26/791.csv` made 8 finds in 15 minutes.
  The side fell from 28.626622634561 to 28.625354262546, and fq took it to 28.624454951676.
  The score is 0.017768450415, 3.419e-4 below the base bar and 7.7e-5 below the midm start.
  The midm lane then took its own 791 row out, so its rows and full trace are kept in `work/donors/791-midm-r26.json`.
  The roots are the round 23 rows 631 and 736, the same in the a and b files, and a public Apache 2.0 notebook layout of 791.
- **814.** A 20 s probe on the stair-c composition `814-r26-6a74aa50a757-m.csv`, which sat at the base score, made 2 finds.
  After fq the gain is 4.353e-6.
- **365.** An island on the twoshort 365 file certified 1.228e-4 below the base bar at 16:27 UTC.
  The backlog lane then ran fq on our file and went 4.5e-10 lower, so the row is now theirs.
  The invent lane used the same file as a donor for its 328.
  The file stays in `near/365-take-1632Z.csv` (sha256 `76ea21f3ebee6237…`) with its source record.

### Measured dead ends

- Islands on certified files of other lanes found nothing in 16 of 20 runs.
  Each ran 55,000 to 215,000 children.
  The finds came on the midm kick files of 791 and 972, the twoshort 365 file and the again leg on the harvest 791 file.
  That last one stayed above our 791.
  The midm lane moved its own 972 lower than our find.
- k123 short starts: queued 24, started 23, passed 23, 7 with a find.
  Every find ended at or above the fq floor that the k123 lane already held, 328 and 365 within 1e-9.
- Forensics probes: queued 48, started 48, passed 48, 5 with a find.
  Each find ended above another lane's row after fq.
- stair-c probes: queued 88, started 88, passed 88, 1 with a find.
  Round 25 had 0 finds in 24.
- A second island from the legal best of 791 repeated the first.
  The again mode of `chain.sh` uses the fixed seed 14, so it walked the same path (81,165 children, no find).

### Next

1. Give every fresh midm kick file and every fresh certified twoshort or k123 file an 1800 s island within minutes of its write, up to the search deadline.
   Measured: of all the island inputs this round, only those three kinds found, and they gave 791 (3.4e-4, kept) and 365 (1.2e-4, now held by backlog).
   The idle fill stopped at 16:30 UTC, 35 minutes before the search deadline, and an island waited behind every probe.
   So the midm 971 kick file of 16:12 UTC never got an island.
   Let a fresh kick file go ahead of the probes, and move the cutoff to 10 minutes before the deadline.
2. Give the again leg a fresh seed.
   Measured: the again island on 791 restarted with seed 14 and repeated the first island (81,165 children, no find).
3. Run a second fq quench on every kept row before it goes into the take.
   Measured: the backlog fq step on our certified 365 went 4.5e-10 lower and took the row.
4. Cut the stair-c probes to one per composition family.
   Measured: 1 find in 88 passed probes this round and 0 in 24 in round 25, and the probes held the slots from 16:00 UTC on.
5. Keep the k123 short starts but only hand their finds on as near files.
   Measured: 7 of 23 starts found, and each find ended at or above the fq floor that the k123 lane already held.

The take, near files and logs are under `<scratch>/bounties-squares/take-soft-r26`.
Both box scratch directories were copied, checked by md5 and removed after the workers stopped.
Nothing was submitted from this lane.

## Round 29

Round 29 ran from 06:02 to 11:55 UTC on 2026-11-15. It had 2 processes on boxC and 1 on boxD. The bar was bar29.tsv: the held round 27 b file, or the best certified round 28 take row where that was lower. The agents of rounds 27 and 28 died early, and their drivers ran on. Round 28 kept one row, 421 (2.3e-5 under bar28). It came from an island on a loose forensics rectangle file.

### What changed against round 28

- `configure29.py` sets the round 29 names, the held round 27 b file and the bar. A held row resolves through `results/round27-best-2026-11-15.tsv`.
- Collect certifies with border's `finesafe.py`. On fq outputs it measured 5.6e-10 of side under the floatsafe ladder (417 and 421 controls).
- A new chain mode, `lpq`, runs border's LP follow and then the fq loop. It is for a legal file just above the bar.
- `adopt29.py` starts from a round 28 near file. It uses the ancestry that the round 28 job stored for its own start.
- Collect runs a walk gate before it keeps a row. `walkcheck.py` runs backlog's `quench_walk.check` on the job input, with the 745/858 rule narrowed as the main session asked at 07:34Z.
- `qorder.py` puts every k123 start behind the near-file islands.

### Controls

- finesafe on the raw 417 and 421 fq outputs: 5.61e-10 and 5.63e-10 of side under the ladder. Files that were already float-safe at e = 0 did not change.
- Walk gate: the real 745/858 join (take-forensics-r23/980.csv) is refused on 858-ec97a452. The round 28 421 take passes, and so does our 747 input once the rule is narrowed.

### Search

The follow driver queued 490 starts from the fresh round 29 files of other lanes. 124 of them ran before the 11:38 UTC deadline on the 3 slots. The queue put the files closest above 1.5e-4 of score over the bar first.

| kind | started | with a find |
|---|---|---|
| forensics islands (near rectangle files) | 97 | 17 |
| midm take islands | 4 | 1 |
| k123 starts (short and island) | 17 | 0 |
| twoshort islands | 4 | 0 |
| again legs (seed 31, from the fq result of a find) | 16 | 0 |

Almost every forensics island started 1.5e-4 to 3e-4 of score over the bar. Four finds reached the held packing: 498 twice, 417 and 547. One find crossed: 747.

### Results

Our take ends with 0 rows. Two team rows came from our islands, and other lanes hold them:

- **747**: an island on the forensics r29 rectangle file, then fq. It certified at 0.017380959152, 1.150e-5 under bar29. Midm then kicked the rewritten forensics 747 file, which sat in our basin by then. Midm holds 747 at 0.017380950091, 9.1e-12 lower. Our LP and fq self follow gained nothing.
- **907**: an island on the midm r29 take file found 5.1e-5 more, to 9.39e-5 under bar29. Our trace refused midm's 907 parent, so the result stayed near-only. The quench lane ran fq on our near file and holds 907 at 0.016251715181.

At 07:10 UTC backlog refused our 747 on a walk hit. We withdrew it at 07:22. The main session then showed the hit was a false match of the 745/858 rule, so we reinstated the same bytes at 07:48.

### Measured dead ends

- `lpq` on legal files at the held floor. 417 ended at the held side, 1.3e-9 of side short of the rule. The 747 self follow gained 0.
- k123 and twoshort starts: 17 k123 and 4 twoshort runs, no find. Round 28 had 1 find in 5 k123 islands.
- Again legs from the fq result of a find: 0 of 16 found.
- finesafe does not move a file that is already float-safe at e = 0, because the ladder stops there.

### Next

1. Islands on loose forensics rectangle files, 1.5e-4 to 3e-4 of score over the bar. Measured: 17 of 97 found, and 1 crossed (747, 1.15e-5). Hand each find to the kick lanes at once: the midm kick took 747 another 2.5e-7 of side lower.
2. Let a near-only find that passes the assembler walk (quench_walk.check) publish. Measured: 907 gained 9.39e-5 on bar29, and the quench lane published it, not us.
3. Islands on fresh midm take files: 1 of 4 found (907).
4. Drop k123 and twoshort starts. Measured: 0 finds in 21 runs this round.

## Round 30

Round 30 ran from 12:05 to 17:55 UTC on 2026-11-15. It had 2 processes on boxC and 1 on boxD. The bar was bar30.tsv: the held round 28 b file, or the best certified round 29 take row where that was lower. The first agent of the lane stopped at 16:03 UTC on a usage limit. Its drivers ran on, and a second agent adopted them at 16:05 UTC from STATE.txt. That agent stopped on a rate limit, and a third agent adopted the drivers at 17:38 UTC for the final collect.

### What changed against round 29

- `configure30.py` sets the round 30 names, the held round 28 b file and the bar. A held row resolves through `results/round28-best-2026-11-15.tsv`. The held 801 is open, because the 801 row is our own layout.
- `kickleg.py` is new. After the island and its fq quench, a chain runs a 900 s kick scan with the midm lane's `midm_scan.py` (modes kick and lkick, sigma 0.04, `--stop6`). It runs only when the best packing is at most 2.5e-4 of score above the all-lane bar. From 13:20 UTC it chains up to 3 legs while the last leg removed more than 1e-6 of side. From 15:38 UTC it chains up to 8 legs while the result is within 2e-5 of score of the bar.
- `barsync.py` writes the all-lane bar of every n to `bars.txt` on each box every 300 s, and it checks the md5 there.
- A new chain mode, `kick`, runs the kick legs straight from the start and then fq. An `again` leg now runs kick legs first, and the island again only when kickleg skips.
- `r28check.py` skips the withdrawal lines of the public-first held-ancestor gate, which the main session voided at 12:40 UTC. It refuses a trace that takes one of the three withdrawn public-first files directly, as the main session asked at 13:32 UTC.
- From 16:09 UTC the second agent fed starts by hand through `inbox.json`. The follow never reads the modules lane's near files: `follow.log` had no modules line. So we queued the closest traced near files of every lane, ranked by their margin over the all-lane bar, as kick or `lpq` chains. No tool changed for this.

### Controls

- `kickleg.py`: a start 3.9e-4 over the bar printed KICKSKIP. A start 2.2e-7 over the bar ran a 90 s scan with 23 tries and 1 find. A chain whose first leg gained nothing stopped after one leg.
- `r28check.py`: the forensics r29 458 file, which a voided line had withdrawn, is open again. A still-valid round 29 withdrawal still counts. The direct 799 donor and the harvest r26 695 file are refused, and the held 799 passes.
- 910 walk gate: the walk refused the input on a path-level reading of the backlog r26 972 build. A hand trace showed that both parts are other bytes than the two withdrawn backlog rows, and that the share with the prvsiyan 1105 row of 910 is 0.000. We allowed that input in `walk-allow.json`.

### Search

| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |
|---|---|---|---|---|---|---|---|---|---|
| modules, written during the round | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| forensics, written during the round | 298 | 0 | 42 | 116 | 140 | 46 | 3,488,054 | 8: 299, 930, 701, 865, 749, 972, 458, 910 | 55 |
| k123, written during the round | 36 | 0 | 0 | 20 | 16 | 0 | 0 | 0 | 0 |
| twoshort, written during the round | 35 | 0 | 1 | 11 | 23 | 1 | 79,964 | 0 | 0 |
| midm, written during the round | 9 | 0 | 4 | 3 | 2 | 4 | 365,253 | 0 | 0 |
| stair-c, written during the round | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **all** | 385 | 0 | 47 | 157 | 181 | 51 | 3,933,271 | 8 | 55 |
cpu-hours 6.4

| n | start | pass at `2e-4` | pass at `1e-4` | island | fq quench | own gain certified |
|---|---|---|---|---|---|---|
| 299 | forensics, written during the round (xfor) | not run | not run | 281,059 children, 6 finds, last at 419 s of 779 s, 1.311e-04 | 1.063e-05; 0.000e+00 | not kept |
| 930 | forensics, written during the round (xfor) | not run | not run | 44,131 children, 3 finds, last at 273 s of 633 s, 2.790e-05 | 6.548e-06; 0.000e+00 | not kept |
| 701 | forensics, written during the round (xfor) | not run | not run | 89,636 children, 3 finds, last at 227 s of 587 s, 1.767e-05 | 2.371e-05; 0.000e+00 | not kept |
| 865 | forensics, written during the round (xfor) | not run | not run | 70,645 children, 4 finds, last at 377 s of 737 s, 1.916e-05 | 9.890e-06; 0.000e+00 | not kept |
| 749 | forensics, written during the round (xfor) | not run | not run | 79,195 children, 5 finds, last at 475 s of 835 s, 5.904e-05 | 4.263e-05; 0.000e+00 | not kept |
| 972 | forensics, written during the round (xfor) | not run | not run | 46,659 children, 13 finds, last at 1740 s of 1800 s, 1.811e-04 | 1.512e-05; 0.000e+00; 0.000e+00 | not kept |
| 458 | forensics, written during the round (xfor) | not run | not run | 114,165 children, 7 finds, last at 154 s of 514 s, 9.417e-05 | 1.212e-05; 0.000e+00 | not kept |
| 910 | forensics, written during the round (xfor3) | not run | not run | 72,887 children, 14 finds, last at 1597 s of 1800 s, 1.827e-04 | 1.882e-05; 0.000e+00; 0.000e+00; 0.000e+00 | 2.572e-06 |

| n | start | held side | start side | new side | gain against held | own gain |
|---|---|---|---|---|---|---|
| 910 | forensics, written during the round | 30.656784431 | 30.656784431 | 30.656706829 | 2.572e-06 | 2.572e-06 |
| **total** | | | | | **0.0000026** | **0.0000026** |

The lists of starts cut short, not run and dropped are in `take-soft-r30/work/plan.json`.

### Results

- **910 crossed and holds.** The island on the forensics r30 file `near/910-rect.csv` found 1.83e-4 of score in 1800 s. Its fq quench gave 1.88e-5 more. Then 900 s kick legs gave 1.49e-5, 5.3e-6 and 3.05e-6. Leg 3 crossed at 15:40 UTC. The certified row is 0.016259935600120734, 2.572e-6 under bar30 (0.016262508071318793, `take-rebuild-r29/910.csv`). The official metric scores `take-soft-r30/910.csv` (sha256 3a33be77) at the same value with no fault. No other live round 30 take holds 910.
- **972 crossed and went to backlog.** The island and fq on `near/972-rect.csv` crossed at 13:50 UTC. Our row was 1.714e-5 under bar30 from 14:01 UTC. At 14:22 UTC the backlog lane's kick follow of our take certified 4.41e-7 lower. The team keeps 1.758e-5 on bar30 at 972 through that row.
- **Close misses.** 994: the kick chain ended 4.9e-11 of score under the bar raw and 2.8e-11 after the finesafe certify, and a row needs 1e-10. 689: 1.7e-8 over. 756: 2.35e-7 over. 873: 3.4e-6 over after three legs.
- From 17:32 UTC we started no new chain: a crossing needs its certified-file fq quench before collect keeps it, and fq stopped at 17:45 UTC.

### Measured dead ends

- k123 starts: 36 queued, 16 ran short and dropped, 0 finds. twoshort: 1 island, 0 finds. midm: 4 islands, 0 finds.
- Kick legs from the 910 best after the crossing: legs 4 and 5 (seeds 303 and 304) gained 0. A repeated kick from a chain's best is dry after one dry leg.
- Modules near files: `lpq` on 757 and 931 gave 0 (LP 9 iterations, fq 0). Kick leg 1 on 931 and 649 gave 0. 873 legs gained 2.2e-6, 6.1e-7, 5.3e-8 and stayed 3.4e-6 over.
- `kickleg.py` ended a chain when a leg removed under 1e-6 of side. 689 leg 1 removed 9.6e-7 of side and ended 1.9e-8 over the bar. From 17:16 UTC a chain within 2e-6 of score of the bar goes on while a leg removes more than 1e-9 of side (control with stub legs: a close start ran 8 legs, a start 1e-5 over ran 1 leg).

### Next

1. Run islands on the forensics rectangle files from the round start, then 900 s kick legs while they gain. This gave both crossings of round 30 (972 and 910) and all 8 n with a find. The other kinds of start gave 0 finds in 87 starts (5 islands ran).
2. Make `follow.py` read the modules lane's near files: `follow.log` had no modules line in round 30, and they were fed by hand from 16:09 UTC.
3. Start kick chains with new seeds from the close misses at the round start: 994 (needs 7e-11 of score more), 689 (1.7e-8 over) and 756 (2.35e-7 over).
4. End new chains 15 minutes before the fq deadline, so each crossing gets its certified-file quench.

## Round 31

Round 31 ran from 18:48 UTC on 2026-11-15 to 00:25 UTC on 2026-11-16. It had 2 processes on boxC and 1 on boxD. The bar was bar31.tsv, the held round 30 c file. Every valid round 30 take is already in it.

### What we learned from round 30 before we started

The round 30 assembler dropped our 910 row. Its tree started from two forensics warm partners whose roots are public files (`take-harvest-r26/850.csv` and `take-harvest-r26/972.csv`). The tree reaches no held row. Its ICP share with the prvsiyan 1105 row of 910 is 0.456 at 1e-2, and the rule is 0.4 at 1e-3 or at 1e-2. Our own share gate used `prvsim26.py` at 1e-3 only, which read 0.07. The 972 that backlog took from our round 30 file was dropped for the same reason. So both round 30 crossings of this lane came from public-first trees, and neither counted.

We measured the round 30 assembler's `share30.py` on our 17 round 30 near files. All 17 read 0.47 to 0.93 at 1e-2. A public-first tree with no held row therefore cannot give a row. A tree that reaches a held row is our own layout, and it gets no share test.

### What changed against round 30

- `configure31.py` sets the round 31 names and the held round 30 c file. A row of the held round 29 b or round 30 c file is our own layout and a clean root. The trace still reads the recorded source of that row for the excluded markers.
- Claims: `ctl.add` posts a claim line with the sha256 of the start bytes for a `kick` or `lpq` chain. It skips a kick start whose bytes another lane claimed in the last 60 minutes. Other lanes write the full sha256 or a prefix of 12 to 16 hex digits, and the check reads both. An island is not a kick, so it gets no claim and no check. Its kick leg runs only from its own find.
- `configure31b.py`: a start whose tree is public-first and reaches no held row is refused at admission. The output share test of such a row is the assembler's `share30.py` (ICP, 1e-3 and 1e-2).
- `kickleg.py` uses seeds from 500 up (round 30 used 300 up). A kick scan now stops when no try is below the start side at the first check after 120 s and 4 tries. It also stops at 300 s with no such try. The old `--stop6` rule fires only when the tries come back within 5e-9 of the start. On 689 they came back 4.6e-8 above it, so the scan ran its full 900 s with no find.
- `follow.py` follows forensics rectangle files only. Round 30 measured every find on them, and 0 finds in 87 starts of the other kinds. A fresh take row of any lane that kicks held rows gets an island 10 minutes after it is written, after backlog's follow. The inbox adds at most 6 starts per call, because each add certifies the start on boxA.
- `qorder.py` puts the pool of round 30 forensics files behind fresh round 31 files of the same margin.

### Controls

- Claim check on a test log: a fresh border claim of the sha256 refused the start. Our own claim and a claim 67 minutes old did not. A 16-digit prefix of a rebuild claim in the live log refused the start, and a random sha256 did not.
- Public-first refusal: our round 30 910 take traces as public-first with no held row, so it is refused. The round 30 689, 807 and 873 near files reach held rows and pass.
- Kick probe with a stub scan (probe 6 s, 3 tries, 15 s): tries above the start printed a stop after 10 s and 8 tries. One try 1e-9 below the start printed "improved, running on".
- `held_scores()` equals bar31.tsv on all 1000 n.

### What we measured

- The lane certified no row that stands at the end of the round. take.tsv is empty, and the gain is 0.
- One row crossed the bar. A fresh island on the forensics take row of 686 (`take-forensics-r31/686.csv`) found 4.47e-6 of score in 156 s. The fq quench from the certified file added 1.98e-5. The row was 2.43e-5 under the forensics take at 20:01 UTC. At 20:19 UTC a backlog kick of a midm 686 went 1.08e-4 below it, so our row is now a near file. Its tree reaches held rows. `near/686-soft-r31.trace.json` names the start bytes and both parts, so the assembler can walk it again.
- Starts by kind, with the n that found anything:

| Kind | Starts | n with finds | Crossed |
| --- | --- | --- | --- |
| Island on a fresh round 31 forensics rectangle file | 127 | 6 (382 421 457 634 751 865) | 0 |
| Island on the round 30 forensics rectangle pool | 117 | 0 | 0 |
| Fresh island on a fresh take row of another lane | 61 | 1 (686) | 1, superseded |
| Island again from our own legal best | 22 | gains on 421 634 686 751 | 0 |
| Kick chain on our own round 30 close misses | 7 | 807 and 873, under 1e-9 of score | 0 |

- The fresh take rows came from backlog (28), twoshort (12), classfill (7), border (6), forensics (3), k123 (2), invent (2) and rebuild (1). Only the forensics composition row found anything. The 58 kicked rows of the other lanes gave 0 finds.
- The closest island was 421. The island and its fq gave 9.9e-5 of side, and three kick legs gave 3.9e-5, 2.7e-5 and less. It stopped 8.6e-6 of score over the all-lane bar. Five more legs from its best gave 0.
- Close misses: 994 converged at 2.8e-11 of score under the bar, and a row needs 1e-10. 807 and 873 gained 1.6e-10 and 8.5e-10 of score in fq, and they stay 5.5e-7 and 3.4e-6 over.
- The first agent died at 22:45 UTC on a usage limit. The background drivers ran on to the deadline. After that, 28 follow cycles of 300 to 312 jobs found nothing, and 47 more starts were dry.

### Tool changes during the round

- `provenance.py`: a file whose rows equal the held round 30 c row of n is that held row, when the lane reader cannot read its record. Control: `held-inputs/509.csv` True, the forensics 686 take False, and the 509 copy read as n 510 False.
- `ctl.collect`: our trace refused 17 of 22 round 31 take rows of other lanes, because their starts are byte copies without a record. A near-only job on such a row now counts when `walkcheck.py` (the quench lane's `quench_walk.check`) passes its input.
- `kickleg.py`: a kick try counts as improved only 1e-9 of side under the start, the same rule as `midm_scan.py`.

### Next

1. Run islands on fresh forensics rectangle files only in the hour they appear, then kick legs while they gain. This kind found on 6 of 127 starts this round. It gave both round 30 crossings.
2. Stop the islands on the round 30 forensics pool (117 starts, 0 finds) and on the kick rows of other lanes (58 starts, 0 finds). backlog's 180 s kicks of those rows gave about 21 rows this round.
3. Stop the kick chains on 807, 873 and 994. Seven chains moved them by less than 1e-9 of score.
4. The lane gave one row in two rounds, and the assembler dropped it or another lane beat it. Give its slots (boxC 2, boxD 1) to the lane with the best yield per slot in round 31, unless forensics posts fresh rectangle files.

## Round 32

Round 32 ran from 11:17 UTC to about 17:25 UTC on 2026-11-16. It had 2 processes on boxC and 1 on boxD. The bar was bar32.tsv, the held round 31 b file. Every valid round 31 take is already in it.

### What changed against round 31

- `configure32.py` sets the round 32 names and the held round 31 b file. A row of that file is our own layout and a clean root. A byte copy of a held row traces as that row (`provenance.held_copy`).
- The share test of a public-first row that reaches no held row is now the round 31 assembler's `share31.py`. It reads the share against the 1105 versions that are not our own seed (`max_nonown`).
- `follow.py` starts islands on forensics rectangle files only, and only in the hour after the file was written. A start that still waits in a queue after that hour leaves the queue. Round 31 measured finds on 6 of 127 fresh rectangle files and on 0 of 117 old ones.
- No islands on the take rows of other lanes. Round 31 measured 58 such starts with 0 finds.
- `lkleg.py` and the `lk` mode of `chain.sh` run the twoshort lkick: 150 s legs of the invent lane's `invent_rest.py` (mode `lkick`). A leg that moves the side more than 1e-8 gets the next leg, up to 8. Then the chain runs the fq quench. Round 31 twoshort measured this kick moving 12 of 121 held rows, against 2 of 70 for a 900 s midm probe.
- `sel32.py` builds the pool for these kicks. A held row is out when a kick or claim line of rounds 29 to 32 names it as held, or names a file with the same geometry. Rows changed in rounds 29 to 31 are out too. 96 rows were left, led by 792, 498, 683, 685 and 871.
- `follow.lk_fill` gives a slot one of these kicks only when the slot has nothing waiting. A fresh rectangle island waits at most one 150 s leg. The kick skips an n that another lane named in a kick or claim line this round, and it posts our claim first.

### Controls

- The `lk` chain on boxC replayed twoshort's round 31 lkick of the 465 start `465-held30c.csv` (sha256 0fd2ce53, seed 3201). It found the same tries in the same order: try 5 at 21.990557314036, try 30 at 21.990554879573, try 31 at 21.990553365423. It ran 35 tries in 150 s, against 41 on boxE, so it missed try 37. It moved the side 3.97e-6. Then `fqjob.py` ran, and the chain ended.

### What we measured

- The lane certified 1 row: n = 465, 1.458e-6 of score below the bar. No live round 32 take of another lane holds a lower 465.
- 465 came from a held-row lkick. The start was the held round 31 b row of 465 (sha256 of the take file 26cd3167). Its first 150 s leg (seed 3301, 34 tries) moved the side from 21.990552955912 to 21.990521512026, which is 3.14e-5. The second leg moved it 0. The fq quench added 1.9e-10 of score. Two more fq passes from the certified file added 0. The row is our own layout, so it got no share test.
- Held-row lkicks: 169 chains of 150 s legs on held rows that no lane kicked or claimed. The first pass ran 109 chains at seed 3301. It moved 2 rows: 465, and 755 by 7.2e-11 of score, which is under the 1e-10 rule. The second pass ran 60 chains on first-pass rows at seed 3401, and it moved 0. Every start got a claim line first.
- Islands on fresh forensics rectangle files: 33 first islands on 33 n, and 10 island-again legs from our own legal best. Two more left the queue because forensics wrote a newer version of the file. Finds came on 3 n:

| n | Islands | Best margin over the bar |
| --- | --- | --- |
| 491 | 3 | 4.7e-12 under, short of the 1e-10 rule |
| 684 | 2 | 2.5e-3 of side over |
| 908 | 4 | 9.2e-3 of side over |

- The other 30 n gave 0 finds. The near files are in `near/` of the take dir (491, 684, 908).
- The round 31 near file of 421 went to quench and backlog. It is 2.0e-5 of score over bar32, and five island legs from it gave 0.
- The first agent died at about 12:12 UTC on a usage limit. A revived agent adopted the drivers, and nothing restarted. The drivers ran on to the deadline, and the final collect ended at 17:23 UTC. The report was written after the round in a separate pass.

### Tool changes during the round

- `follow.py` (`stop_old`): an island on a forensics rectangle file that still waits an hour after the file was written leaves the queue.
- `follow.py` (`lk_fill`): one lk line can wait in each box queue beyond the workers. Without it a slot sat idle about 2.5 minutes after each chain. When the first pool is spent, a second pass reads `lk-pool2.json`.
- `lkleg.py`: a second lk job of an n (tag `hhel1`) starts at seed 3401. With the same seed it replays the first job try for try, as the control showed.

### Next

1. Keep held-row lkicks of 150 s on rows nobody claimed, one seed per row. The first pass moved 2 of 109 rows and gave the one row of the round.
2. Stop second seeds of the held-row lkick. 60 chains at a new seed moved 0 rows.
3. Keep islands on fresh forensics rectangle files only in the hour they appear. 33 n gave finds on 3 and no row this round. In round 31 it was 6 of 127 with no row.
4. Hand 491 to a kick lane. Three islands converged 4.7e-12 under the bar, and a row needs 1e-10.

## 4. Three smaller checks, all dry

- **Global rotation of the box** (nilanjansaha123's `rotate_square_box`): for each held n, the smallest bounding square of the convex hull over all rotations. 0 of 1,000 n gain more than 1e-9.
- **Drop closure**: `L(n) ≤ L(n+1)` holds for all 999 pairs of the held file.
- **The fixed-angle LP alone**: section 2.

## 5. Files

| file | what it does |
|---|---|
| `methods_lp.py` | The contact LP with free angles (`slp`), the fixed-angle LP (`reclose`, `--fixed`), and `--inflate` for the control. Writes raw float rows and `lp.tsv`. |
| `methods_soft.py` | The soft-box search for one n. `--start best` works from the held packing, `drop1` from the held n+1 minus a square, `mbest` / `mdrop1` are the mirror islands. `--restart` sets the children with no find before a new start from the legal best, `--kernel` picks the C or the numpy kernel, `--mirror-box` picks where a mirror island starts, `--keep-softfree 1` keeps the soft-free members that did not become legal in `softfree/`, `--dry S` ends the island S seconds after its last find. Writes `raw/<n>-<start>-<seed>.csv` on every find, and a log with every find, every box drop and the count of children per move. |
| `methods_take.py` | Certifies raw results the lane's way (`floatsafe.work`, then strictly below the held score by more than 1e-10) into a take dir that `engine_assemble.py` reads. |
| `tools/softround/` | The driver of a round over several boxes, as rounds 11 to 16 ran it (sections 3e to 3j). `ctl.py plan`, `watch`, `add`, `cq` and `collect` run on boxA, and `addheld.py` makes a start from a held packing. `setup.sh` makes the scratch of a box. `chain.sh`, `worker.sh`, `drive.sh`, `bestof.py` and `fqjob.py` go to each box with `methods_soft.py`, `methods_lp.py` and the fq binary. `status.sh`, `qrm.sh` and `verify.sh` show the boxes, take a line out of a queue and compare a box with its copy before the box scratch is removed. `mdtables.py` and `stats.py` print the tables and counts of the section. The paths of the round are constants at the top of `ctl.py`. |

All of these are our own code. They import nothing fetched; `methods_take.py` and `ctl.py` import the lane's `floatsafe.py`, and `fqjob.py` runs Evan Daniel's fq binary (MIT), built on boxA.

To repeat: `methods_soft.py SUB.csv OUT --n N --seconds 1800 --dry 360 [--delta 1e-4]`, one process per n and seed, then `methods_take.py gate/<held>/details.csv TAKE methods_soft OUT/raw`, then `engine_assemble.py` and the gate.

A whole round: set the constants in `tools/softround/ctl.py`, run `ctl.py plan`, and run `setup.sh BOX DEADLINE FQDEADLINE` for each box (epoch seconds). It copies the box scripts, `starts/` and `queue-<box>.txt` (as `queue.txt`), and writes the two deadline files and a `py` wrapper for the box's Python. Then start `drive.sh K` under nohup on each box, run `watchloop.sh`, and end with `ctl.py collect` and `verify.sh BOX`.

## Summary

- The leading public notebooks are mostly mergers. Four methods make new packings in public: `fq` on fresh layouts, the fault-line DP, the stretch and the island GA. The lane lacked the GA and the contact LP.
- `methods_lp.py` (contact LP with free angles) passes its control and gains 1.3e-7 on 22 fresh n. The held packings are exact local optima. It is now the last step of the search, not a sweep.
- `methods_soft.py` (soft-box search) walks the public GA's n = 644 down from the same looser start, 24% of the way in round 7, 26% in round 8.
- On our file it certified 5 n, 0.0000990 of score: 452, 459, 644, 646, 701. It finds only on loose layouts.
- Round 8 made it 9 to 15 times faster with a C kernel (166 children a second at n = 701 against 10 to 12) and added the restart. It certified 6 n, 0.0002144 of score: 419, 590, 601, 654, 701, 806. Five came from a 200 s pass over the 47 n the harvest had moved; long islands went dry after 6 to 15 minutes on all but 806.
- The mirror island has a legal symmetric seed now, and its control on n = 452 is still red: the seed settles 0.029 above the legal side and the island recovers 0.006 of that in 31 minutes.
- Round 9 answered the mirror 459 question: the island's kept energy missed overlaps that its own symmetrisation made outside the active set (below the true energy on 60% of local children, by up to 4.9e-3). No real packing was lost. With the fix the 452 control is still red (0.0245 above the legal side after 213,100 children).
- Round 9 certified 7 n, 0.0004035 of score: 419, 640, 645, 648, 651, 756, 800. An 18 s island on each of the 701 n from 300 to 1,000 found on 2 n; 140 s islands on the 63 n with the most box drops in those 18 s found on 7. Two seeds of 44 minutes on 806 found nothing.
- Round 10 certified 5 n, 0.0002131 of score: 600, 640, 651, 756, 800. 651 gave 1.426e-04 of it in two 15-minute islands and then went dry (six legs of 140 s at four box steps found nothing). The 140 s pass on the next 165 n by box drops found on 1 n (600), against 7 of 63 in round 9. Relays from the finds found again only on 640. The three n that the 19:22Z harvest moved, and 600 s islands on 542, 549, 602 and 690, found nothing. `--dry S` ends an island S seconds after its last find.
- Round 11 certified 4 n: 745, 807, 817, 933. They are 0.0003551 of score on top of the files the search started from, and 0.0006242 against the held file with the family lane's starts. It ran one chain per start on 78 starts: the 140 s pass at both deltas, one island with `--dry 360` from a find, then the fq quench. All four n are layouts of the family step: 4 of 35 family starts found, and none of 19 modules, 5 border and 6 polish starts. 807 gave 2.186e-04 by itself. The quench after the island gained on all four, 9.08e-05 together. A look every 10 minutes put 21 new files of the family and modules lanes under the search during the round.
- Round 12 certified 1 n: 598, 0.0000610 of score against the held file, 0.0000601 of it on top of the family lane's file. It ran the same chain on 90 starts: the n round 11 moved and the files the other lanes wrote during the round. Finds came on 2 family layouts (598, 854) and on none of 10 readers, 3 border and 5 zone starts. The family lane wrote lower 854 files during the round, so the 854 result is left out. 38 starts did not run: the round had 2 full-speed slots, and boxA's slot ran at 27% to 75% of a core.
- Round 13 certified 3 n: 497, 815 and 871. They are 0.0002508 of score against the held file, 0.0002465 of it on top of the files the search started from. It ran the same chain on 59 starts with 4 full-speed slots, and every start ran. The finds came on a readers layout (497), a held family layout of round 12 (815) and a family file of the round (871). None of 20 other starts found, and the island after the quench found nothing on 815 and 497.
- Round 14 certified 1 n: 755, 0.0001352 of score, all of it on top of the held packing. It ran the chain on family and readers layouts only, 44 starts with 4 full-speed slots, and every start ran. 1 of 31 first passes found. A second seed on 13 layouts that were dry in round 13 found nothing, and neither did an island after a dry pass on 999 and 981. The slots waited for new files for about 30% of the round.
- Round 15 certified 2 n: 746 and 802, 0.0003197 of score against the held file, 0.0000792 of it on top of the readers files the search started from. It ran the chain on 23 family and readers starts with no second seed. Both finds came on readers files 1 shell up from jonathan1506 layouts, 9.5e-5 and 1.5e-4 below the held file. None of the 14 starts that moved their n by less than 1e-5 found. A second fq quench from the float-safe rows found nothing. boxA's slot stopped at 10:04Z at 27% of a core.
- Round 16 certified 2 n: 596 and 700, 0.0004135 of score against the held file, 0.0002045 of it on top of the files the search started from. It ran the chain on 45 starts, and from 12:45Z the watch also read the modules lane's files. 3 starts found: the modules 549 and 700 and the family 596. They are steps of one loop. Our 549 went to the family lane (598), then to the modules lane (700) and back to us. Our 700 went to the family lane (596) and back to us. The family lane's walk of our 549 holds 549. 4 passes on held fq quenches of public layouts, 7e-5 to 3.4e-4 below the scores they replaced, found nothing.
- **Next:** (1) Each round, run `tools/softround/` on every new family, readers, band and modules file as it lands, the largest step first. Take a modules file only when it is more than 1e-6 below held. Also run it on the held family and readers files that had no pass. These layouts gave every find of rounds 11 to 16. (2) Keep the loop going: the family and modules lanes can step from the new 596 and 700, and our watch takes their files back. Their lines are in `handoff-r16.log`. (3) Keep `RESEED = False`, no island on an idle slot, and no passes on held fq quenches of public layouts (0 of 4 found). (4) Keep 2 slots on boxC and 1 on boxD. Give boxA a slot only while `ps` shows it more than half a core. (5) No second quench from the float-safe rows (4.1e-10 on 1 of 3 n). No more wide passes, no islands on 806, mirror islands off until the 452 control is green (unchanged).

## Round 33

Round 33 ran from 18:23 UTC on 2026-11-16 to 00:22 UTC on 2026-11-17. It had 2 processes on boxC and 1 on boxD. The bar was bar33.tsv, the held round 32 a file. Every valid round 32 take is already in it. The lane certified no row.

### What changed against round 32

- `configure33.py` sets the round 33 names and the held round 32 a file. A row of that file is our own layout and a clean root.
- `sel33.py` builds the pool of held rows for first 150 s lkicks. It reads only n 400 to 699, the soft share of the split by n. A row is out when a kick or claim line of rounds 29 to 33 names a csv with the geometry of the held row. A row is also out when such a line says held and came after the row last changed.
- `follow.fresh_lk` runs 150 s lkick legs, then the fq loop, on a fresh take row of another lane. It takes a row only when the row is the lowest live row of its n. The row must also have no claim for 10 minutes after it was written. It leaves the rows of backlog, border, harvest, classfill and soft to those lanes.
- `follow.rect_lk_fill` gives a free slot one 150 s lkick chain of a fresh forensics rectangle file within its hour. The tight files come first: 1.5e-4 of score or less over the bar, too close for an island. From 21:29 UTC it also takes fresh invent and classfill near files within 2e-4 of the bar.
- `follow.deep_fill` serves the shared deep-kick queue of the main session. It runs one unprobed 900 s `midm_scan` kick seed of a held row, then the fq loop. The row comes from border's deep order, past the rows border can still reach. Last start 23:15 UTC.
- `follow.lost_race`: after our claim line, the deep fill waits 5 s and reads the log again. When another lane's claim of the same n came at or before ours, it stops the start and posts a release.

### Controls

- `fresh_lk` on a fake k123 take dir took the 465 row written 15 minutes before. It skipped the 466 row, which was 5 minutes old. It skipped 465 again after a backlog claim line named it after the file was written.
- The deep mode ran unprobed. At 6 minutes the 930 scan had 7 tries and the 757 scan had 9, and both still ran. The probed kick stops after 120 s once it has 4 tries and none is below the start.
- `lost_race` ran on a copy of the 757 lines. It released 757, which twoshort claimed at 21:50:19 UTC, 2 s before us. It kept 930.

### What we measured

- The held-row pool of n 400 to 699 was empty. 180 rows had a kick or claim line on their current geometry. With only the lines of rounds 31 to 33 counted, every row with a board gap still had an lkick line. The other 120 rows are closed-form, shared or lattice sides: 116 sit at m + 1.000000001, as the board does.
- Fresh-row follows: 0 started. Backlog claimed k123's 292, 488 and 734 within minutes. Forensics and rebuild claimed 789 and 812 for their own chains. The trace refused invent's 292 and quench's 907 ("refused parent").
- Islands on fresh forensics rectangle files: 37 islands on 29 n. Islands found legal layouts on 6 n, and 10 near files went to the other lanes. The closest was 805, 7.3e-4 of side over the bar, and the walk refused its input.
- First 150 s lkicks of fresh rectangle and near files: 33 chains on 27 n, and 6 moved. 911 moved most usefully: it started 1.8e-9 of score over the bar. Leg 1 moved the side 5.1e-8, and fq added 2.5e-10 of score. The raw result was 2.7e-9 under the bar, but it certified 3.8e-9 over. The assembler-style walk also refused its input: two files in its ancestry are gone, and a 911 line in the log reads as a withdrawal. 681 and 701 moved 2.1e-5 and 7.1e-5 of score from starts about 6.5e-3 of side over the bar.
- Deep kicks: 3 started. 930 was dry. 423 moved 8.4e-11 of score, under the 1e-10 rule. We stopped 757 at once because twoshort claimed it first. Twoshort and quench claimed the rest of the queue before our next cycle. Border's 455 and 932 stayed inside its reach.

### Next

1. Do not give soft a held-row lkick share again. n 400 to 699 has no row whose current geometry no lane lkicked, and the closed-form rows cannot move.
2. Keep the first lkick of fresh forensics rectangle files near the bar only with a walk check at the start. 911 moved under the bar raw but its input could never count. 6 of 33 chains moved and none crossed.
3. Give soft's slots to a lane with a queue of its own. Soft's fresh follows started nothing: backlog and the owning lanes claimed every fresh row within minutes.
