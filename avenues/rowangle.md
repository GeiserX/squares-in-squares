# Row-angle avenue (2026-11-10, afternoon)

**Result: public score 22.2145729630, ref 58208771, submitted 2026-11-10 17:06Z. It was 22.2145943790. The gain is 0.0000214. It comes from two more `fq` polish passes on 20 of the n that moved this morning, and from one row move on n=549. No experiment added a square.**

This avenue took the three ideas the engine avenue left open. All three are measured now. None adds a square. One of them finds very small gains in the side, of the order of 1e-6.

Words used here: the side is `L = m + f` with `m` whole. A "shell" is one value of `m`. A "patch" is a block of tilted squares. "Held" means the packing in `gather/engine-2026-11-10a.csv`. "The board" is the per-puzzle best of all teams, read on 2026-11-09.

## Results

| experiment | file | what it measures | result |
|---|---|---|---|
| Rows of the held patches | `rowangle_rows.py report` | Tilt of each row, and the spread inside a row | The middle rows of a patch share one tilt to 0.001 degrees. The four or five rows at each end of a large patch differ, by 0.5 to 2.6 degrees |
| One-row moves, relaxed by `fq` | `rowangle_rows.py search` | 17 trailing n, 885 moves, each one relaxed by `fq` | 0 squares gained. 3 moves ended below the held side, all on n=549, by up to 2.0e-6. Rows: [`results/rowangle-rows-2026-11-10.tsv`](../results/rowangle-rows-2026-11-10.tsv) |
| `fq` with other flags | `rowangle_fq.py --pilot` | 12 trailing n, 12 flag sets, 204 runs | 2 runs smaller, both on n=791, by 3.5e-9 and 1.7e-8 of side. Rows: [`results/rowangle-fqflags-2026-11-10.tsv`](../results/rowangle-fqflags-2026-11-10.tsv) |
| n = 544 at side 23.8037 | `rowangle_shell.py`, scratch scans | Five ways to build it from 498 and 591 | Best count 543 of 544 |
| Family step across shells | `rowangle_shell.py` | 543 targets, donors one shell up or down, 19,794 exact refills | 0 hits. 295 targets end 1 square short. Rows: [`results/rowangle-shell-2026-11-10.tsv`](../results/rowangle-shell-2026-11-10.tsv) |
| Overcount starts | `rowangle_over.py` | n = 30 to 797: a tolerant refill that places n+1 or n+2 squares, then `fq` | 227 real starts on 133 n, 0 below our side. The best ends 0.0053 above it, the median 0.104. Rows: [`results/rowangle-over-2026-11-10.tsv`](../results/rowangle-over-2026-11-10.tsv) |
| Third polish pass | `engine_polish.py` on the 68 n that moved this morning | Default and deep `fq`, then `floatsafe` | Pass 3: 20 of 68 n smaller, 0.0000213 of score. Pass 4 on those 20 and on 549: 5 smaller, 3.5e-8. Rows: [`results/rowangle-polish-2026-11-10.tsv`](../results/rowangle-polish-2026-11-10.tsv) |

## 1. The patch model with one angle per row

### What the rows look like

`rowangle_rows.py report N` splits each patch into rows and prints, per row, the count, the tilt, the direction of the line through the centres, and the spread of the tilt inside the row.

- n=454, both patches (52 squares, 10 rows each): every row is at 26.565 degrees. The spread is 0.03 degrees between rows and 0.04 inside rows.
- n=498, small patch (52 squares, 10 rows): the same patch as in 454. Its two end rows are at 26.12 and 26.70 degrees.
- n=498, large patch (87 squares, 15 rows): the six middle rows are at 22.700 to 22.702 degrees, with a spread of 0.000 inside each row. The next rows outward are at 23.2, 24.5 to 25.0 and 25.3 degrees. The spread between rows is 1.7 degrees.
- The direction of a row is not its tilt. In the large patch of 498 the centres of a row at 22.70 degrees run along 23.3 to 23.8 degrees. Each square is shifted against the one before it by 0.01 to 0.02.

So the model is right as a description. A row is a rigid line of squares with one tilt. The 1.5 degree spread that the engine avenue measured is a difference between rows, and it sits at the two ends of a patch. A few squares at the row ends are loose and stand at other angles.

### What the model can and cannot do

A model with fewer variables cannot find a smaller side by smooth optimisation. `fq` already moves all 3n numbers, and the held packings are its local optima. The row variables are a part of those 3n numbers. What the model adds is a short list of changes that keep the relaxed state: change one row and leave every other square where it is.

The four moves of `rowangle_rows.py`, all of which keep n:

- **ext**: the upright next to a row end becomes one more square of that row.
- **del**: the square at a row end becomes an upright at the same centre.
- **turn**: the row turns about its centre by 0.4 or 1.0 degrees.
- **slide**: the row slides along itself by 0.2 or 0.5.

After a move, `fq quench` (default flags, then the deep polish flags) relaxes the whole packing. A smaller side counts after `floatsafe` certifies it.

### Controls

- **Null move, with a refill of the uprights: red.** The first version discarded the uprights and refilled them with `fillfast` at a tolerance. For n=498 the refill gives 498 squares, but the quench ends 0.003029 above the held side. The held uprights are not on the wall grids: `fq` has shifted them by small amounts, and a refill loses that. The engine avenue's hops used the same refill, which explains why its quenches ended high.
- **Null move, all squares kept: green.** The quench returns to the held side of 498 to 1e-9.
- **Damage and return, n=498.** One row-end square is made upright (three different rows). The quench returns to the held side each time, so the damage heals by itself. From each damaged state, all ext moves (67, 68 and 63) end at the held side or above it.

### The search

35 trailing n were chosen, every 12th of the 417. Each got 60 moves drawn at random from its list. The run was stopped after 34 minutes on 3 workers, with 14 n complete and 3 more partly done: 885 moves in total.

| move | runs | back at the held side (within 3e-9) | smaller | larger |
|---|---|---|---|---|
| turn | 293 | 230 | 0 | 63 |
| slide | 305 | 164 | 1 | 140 |
| del | 161 | 83 | 2 | 76 |
| ext | 126 | 40 | 0 | 86 |

The three smaller results are all on n=549, on the same row, and are 1.4e-6 to 2.0e-6 of side. A full run of the moves on rows 12 to 14 of that patch found a fourth (slide +0.2). It is certified: 23.898119029 to 23.898116928, which is 9.0e-8 of score.

**Verdict: no-go for squares.** A one-row change does not leave the basin of the held packing. 58% of the moves return to the same side, and the others end higher. The small gains are the same kind the morning's re-quench found: a held packing that was not fully relaxed. At the measured rate (1 n in 17, about 1e-7 of score each) a sweep of all 417 trailing n would cost about 45 CPU-hours for about 2e-6 of score.

## 2. `fq` with other flags

`rowangle_fq.py --pilot` ran 12 flag sets on 12 trailing n (335, 377, 454, 498, 544, 593, 640, 702, 791, 848, 908, 971), each from the held packing, 204 runs.

| flag set | runs | smaller | same (within 3e-9) | seconds per run |
|---|---|---|---|---|
| default | 12 | 0 | 5 | 16 |
| deep polish (`--no-alm --flip-top 64 --pit 600`) | 12 | 0 | 12 | 3 |
| `--loosen 1.005` | 12 | 0 | 4 | 5 |
| `--loosen 1.05` | 12 | 0 | 2 | 11 |
| `--sqp` | 12 | 0 | 12 | 9 |
| `--finish` | 12 | 0 | 12 | 3 |
| `--flip-top 256 --pit 1500 --stag-w 60` | 12 | 0 | 12 | 11 |
| `--kick 1e-4`, 2 seeds | 24 | 1 | 21 | 3 |
| `--kick 1e-3`, 2 seeds | 24 | 1 | 15 | 4 |
| `--kick 1e-2`, 2 seeds | 24 | 0 | 11 | 7 |
| `--kick 3e-2 --loosen 1.005`, 2 seeds | 24 | 0 | 8 | 9 |
| `--shrink --hops 20`, 2 seeds | 24 | 0 | 24 | 162 |

The two smaller runs are both n=791, by 3.5e-9 and 1.7e-8 of side. That is 6e-10 of score. Every polish-only set returns the held side. Every set that loosens or kicks returns the held side or a larger one.

**Verdict: no-go.** The held packings are local optima for every flag set `fq` has. A sweep was not run: at the pilot's rate (6e-10 of score on 12 n) all 417 trailing n would give about 2e-8.

## 3. n = 544 at 23.8037, and the family step

### 544

The 0.8037 family is n=454 (m=21) and n=498 (m=22), both at `m + 0.803695436`. We also hold n=591 at 24.803695. The board holds 544 at 23.794130, so 23.8037 is not a board value. It is what our own family would give, and it would beat our 23.823801 by 0.0201.

What the three members are:

- 454: two patches of 52.
- 498: one patch of 87 and one of 52. One patch grew by 35 squares between 454 and 498.
- 591: the patches of 498 (85 and 52) with two more shells of uprights around them, and one more square at 45 degrees in a hole between the upright blocks. 498 + 45 + 47 = 590, plus that one square.

So 591 is not a larger member built the same way. It is 498 with two shells of room, and the room of two shells opens one hole. 544 needs the same extra square with one shell of room.

Five attempts at side 23.803695, each counted by the exact refill:

| attempt | best count |
|---|---|
| 498's patches, each kept at its corner, one shell added | 543 |
| 591's patches, one shell removed, every choice of which wall each patch follows | 542 |
| 498's patches, each moved rigidly on a 0.1 grid over ±1.5 in x and y (961 places per patch, two rounds) | 543, only at whole-number shifts. The best other place gives 536 for the large patch and 538 for the small one |
| the large patch of 498 at both corners (two copies, both symmetries) | 540 and 536 |
| tolerant refill around 543's tilted squares (544 placed at tolerance 0.15), then `fq` | ends 0.176 above our side |

The control for the patch moves, 498 from 454, gives 497 of 498 the same way. **544 was not built.** The count is 1 short, as for every one-shell step in this lane.

### Families shared with the board

`fam.py` (scratch) grouped the sides by fractional part to 1e-5, for n = 50 to 1000, over our file and the board together. A family counts here when we hold one member and the board holds another member that we lack.

| f | members we hold | members only the board holds | our deficit there |
|---|---|---|---|
| 0.76001 | 744 (m=27) | 333 (m=18) | 0.0137 |
| 0.81088 | 127 (m=11) | 748 (m=27) | 0.0172 |
| 0.68414 | 794, 851 (m=28, 29) | 537 (m=23), 739 (m=27) | 0.0082, 0.0068 |
| 0.92110 | 154 (m=12) | 931 (m=30) | 0.0117 |
| 0.88096 | 70, 207 (m=8, 14) | 179 (m=13) | 0.0028 |
| 0.75748 | 588, 743 (m=24, 27) | 744 (m=27) | 0.0025 |

That is 6 families and 7 members we lack. All 7 together are worth 0.0027 of score. The board has no large family that we hold a member of. Its 0.794 group (454, 498, 544, 747, 803) and its 0.606 group are families we hold nothing of.

One of these is a pure shell step: 794 and 851 are the same patches (two of 110 squares) with one shell between them, and the board's 739 has the same f one shell below. Removing a shell from 794 gives 737 of 739 with the patches at the walls. The best start over all donors gives 738, from 685.

### The step across shells, for every n

`rowangle_shell.py` runs the step for every target. A donor in the shell above or below gives its tilted squares. Each of the three largest patches either keeps its place or moves with the wall, in x and in y (4 choices per patch). The uprights are refilled exactly at the donor's side plus or minus 1. A count of n or more at a side below ours is a hit.

Two bounds that were checked first, over all n, with no search:

- Our sides never decrease with n.
- `L(n + 2m + 1) <= L(n) + 1`, the plain step of adding one row and one column: no n violates it. Our file already holds every packing that this step gives.

Controls: 851 from 794 (one shell added) gives 851 of 851. 794 from 851 (one shell removed) gives 794 of 794, but only when the patches keep their places. With the patches moved to the new walls it gives 792. The first version of the scan had only that choice, and its control was red.

Result: 543 targets, 19,794 refills, **0 hits**. The best count is 1 short on 295 targets, 2 short on 170, 3 short on 41 and 4 short on 3.

### Overcount starts

The exact refill with a tolerance sometimes places more squares than we hold. Around the tilted squares of our 791, at our side, a tolerance of 0.02 gives 792. `rowangle_over.py` takes each such start with n+1 or n+2 squares, runs `fq`, and compares with our side for the larger n.

It covered n = 30 to 797 before it was stopped at 56 minutes. 866 starts were quenched. 639 of them are the plain grid with spare cells just under m², which returns our own side. Of the 227 real starts on 133 n, none ends below our side. One (368 from 367) returns our own 368. The best of the others ends 0.0053 above our side (655 from 654), and the median 0.104 above.

## The polish, and the submission

The pilot above says that one `fq` run from a held packing gains nothing on 12 n. The morning's sweep had gained on 68 n, so those 68 got a third pass (`engine_polish.py --ns ... --jobs 2`, 51 minutes).

- 20 of the 68 came out smaller, 0.0000213 of score in total.
- Two n hold almost all of it. n=933 went from 30.953068 to 30.952629 (0.0000144). n=990 went from 31.895234 to 31.895031 (0.0000064). Both had descended this morning as well, so their descent was not finished.
- A fourth pass with up to 6 rounds, on those 20 and on 549, gained 3.5e-8 on 5 n. The descent has ended.

`engine_assemble.py` put the 21 n into `gather/rowangle-2026-11-10b.csv` on boxA (SHA-256 `e352d491…`), on top of `gather/engine-2026-11-10a.csv`. The gate was GREEN at 22.2145729630 against `gate/cand-engine-1110a`, with 21 n moved and a smallest gap of 2.206e-11 ([`results/rowangle-gate-2026-11-10b.json`](../results/rowangle-gate-2026-11-10b.json), gate dir `gate/cand-rowangle-1110b`). Kaggle's public score is **22.2145729630**, ref 58208771. Two of the day's ten submissions are used. The next gate run must use `--last gate/cand-rowangle-1110b`.

So the rule for the polish is: after a sweep, run it again on the n that moved, until a pass gains nothing. A pass over the n that did not move is not worth its 2.5 hours.

## Why nothing adds a square

- Every step across shells ends exactly 1 short on more than half the targets. The exact refill is the best possible for the given tilted squares, so the tilted squares themselves must change, and by more than a rigid move.
- A change of one row is undone by `fq`. A refill of the uprights costs 0.003 of side before any search starts. Our 498 is 0.0098 of side behind the board, so that loss is a third of the distance before the first move.
- The one known case of a gained square inside a family is 498 against 454: one patch grew from 52 to 87 squares and changed its angle from 26.57 to 22.70 degrees. That is a change of a whole patch at once, with a new angle, and no move in this lane makes it.

## What is still open

- A patch generator with the angle as the main variable: build the patch from rows at a given middle tilt with the end rows relaxed, for patch sizes around the held ones, and score each by refill plus `fq`. The pair 454 and 498 is its control: from the 52-square patch at 26.57 degrees it must reach the 87-square patch at 22.70.
- The 0.68414 step from 794 to 739, which is 1 square short and worth 0.00025.

## Code

All files are in the lane root with the prefix `rowangle_`. They import the engine avenue's helpers (`engine_lib`, `engine_patch`, `engine_fq`, `engine_polish.certify`) and Evan Daniel's MIT packer (`fillfast`, the `fq` binary) from its clone under `ext/evand` in the box dir. They copy none of it. `SQ_BOX` sets the box dir, `SQ_BEST` the submission to read, and `SQ_TMP` the directory for `fq`'s temporary files.

| file | what it does |
|---|---|
| `rowangle_rows.py` | The row model: `report` prints the rows of each patch, `search` runs the one-row moves with `fq`, `control` runs the null move and the damage test |
| `rowangle_fq.py` | `fq` with 12 flag sets; `--pilot` runs each from the held packing and certifies nothing |
| `rowangle_shell.py` | The step across shells with the exact refill |
| `rowangle_over.py` | Overcount starts from the tolerant refill |

## Summary

- Public score 22.2145729630 (was 22.2145943790), ref 58208771. The gain of 0.0000214 is 20 n from two more polish passes and n=549 from a row move. It does not change our rank band.
- The row model describes the held patches well: a row is a rigid line with one tilt, the middle rows share it to 0.001 degrees, and the spread sits in the end rows. As a search it is a no-go: 885 one-row moves on 17 n gained no square, and 58% returned to the held side.
- `fq` with 12 flag sets, 204 runs on 12 n: nothing above 1.7e-8 of side. No sweep was run.
- n=544 at 23.8037 was not built: 543 of 544 at best. The board's 544 is at 23.7941, in a family we hold nothing of.
- The step across shells, with exact refill, over 543 targets and 19,794 refills: 0 hits, 295 targets 1 square short. Six families are shared with the board; the 7 members we lack are worth 0.0027 in total.
- A refill of the uprights costs 0.003 of side on 498 before any search starts. Every engine that refills, in this avenue or the engine avenue, starts with that loss.
- **Next:** run the polish on the n that moved after each harvest or sweep, until a pass gains nothing. The one build idea left here is a patch generator with the angle as the main variable, with 454 to 498 as its control.
