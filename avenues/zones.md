# Avenue: zones (2026-11-11, round 11)

**Result: 2 n certified (634 and 995), a gain of 1.85e-04 on the total. Nothing was submitted from here. The search of one zone at a time works: it finds the library's best far zone again from a shaken start and from the next zone of its class. A closed-form enumeration of tapers reproduces the library's best far zone at four values of f and gives a far zone for every count class of arms of 8, 7 and 6. At f = 0.93 the best new 8-arm class is 7 mod 8, with a loss of 3.12 against the library's 2.71. That is 0.41 above, so the go line of 0.3 is not met as it was written. On arms of 7 at f = 0.70 the new class 2 mod 7 has a loss of 2.45 against the library's best of 2.30 there, and that zone wins n = 634 by 0.0035 of side.**

This avenue had one job: design the end zones the library of the [modules avenue](modules.md) lacks, by search on one zone at a time. Every search before this one moved a whole layout of 300 to 1,000 squares. A zone has 16 to 61 squares and cannot rearrange inside such a search.

Words used here: "held" is `gather/round10-2026-11-11a.csv` (22.1892638148). "The board" is the per-puzzle board, the best side per n over all teams ([`results/per-puzzle-lb-2026-11-09.json`](../results/per-puzzle-lb-2026-11-09.json)). The side is `L = m + f` with `m` whole, and `k = n - m²`. A "stack" is a row of `c` tilted squares set face to face. The "library" is the 366 modules of `modules.py`. The tool is [`zone_search.py`](../zone_search.py).

## 1. The zone problem

A far zone lives in a strip of width `W = c - 1 + f` along a wall. We use the frame of a far module in `modules.py`: `x` is the distance from the wall the arm runs along, and `y` is the distance from the end wall. The upright grid of the layout starts at `x = W`. We keep it rigid first (section 8).

The other end of the zone is the face of a flush stack. A flush stack has the tilt `t` with `c cos t + sin t = W`, and it slides along `y`. Its position `lam` is where its near face crosses the middle line `x = W / 2`. For a count N, the length of the zone is the smallest `lam` at which N unit squares fit between the end wall and the stack.

```
loss = c cos t * length - N
```

This is the far loss of `modules.py`, so the numbers here compare with its library. One more flush stack adds `c` squares and one pitch `1 / cos t`, and the loss stays the same. So a zone serves every count of its class `N mod c`.

At f = 0.93 and c = 8: t = 17.517 degrees, the pitch is 1.04863, `8 cos t` = 7.629 and W = 7.93. One square of loss is 0.131 of length.

## 2. Does the board's loss depend on the class?

It does not, so the zones exist. We took every n from 620 to 1000 with a board side below the plain grid, and computed the loss as if the layout had two arms of 8, at the board's side and at ours. The class is `(k - 2m - 1) mod 8`. Each cell has the number of n, the median board loss and our median loss (`zone_search.py classes`).

| class | board f 0.90 to 0.94 | board f 0.94 to 0.97 | board f 0.97 to 1.00 |
|---|---|---|---|
| 0 | 2 n, 8.64, 9.34 | 2 n, 9.70, 10.28 | 5 n, 10.00, 10.71 |
| 1 | 3 n, 8.77, 9.23 | none | 5 n, 9.95, 10.49 |
| 2 | 4 n, 8.65, 9.68 | none | 3 n, 9.84, 10.25 |
| 3 | 4 n, 8.80, 9.47 | 1 n, 8.97, 9.87 | 1 n, 9.72, 10.13 |
| 4 | 4 n, 8.79, 8.96 | 2 n, 8.93, 9.32 | none |
| 5 | 3 n, 8.60, 8.81 | 4 n, 9.19, 9.81 | none |
| 6 | 2 n, 8.81, 9.61 | 3 n, 9.57, 10.26 | 2 n, 9.98, 10.54 |
| 7 | none | 3 n, 9.55, 9.81 | 4 n, 9.97, 11.11 |

- For board f from 0.90 to 0.94 the board's loss is 8.60 to 8.81 in all seven classes that have an n there. The spread is 0.22 squares. Ours is 8.81 to 9.68, a spread of 0.86: we are at the board's level in classes 4 and 5 and 0.5 to 1.0 above it in the others.
- For f from 0.94 to 0.97 the board's spread is 0.78, but this band mixes values of f. The board's loss rises with f in every class: 8.6 near 0.91, 9.2 near 0.945, 9.6 near 0.96 and 10.0 above 0.98. At equal f the classes agree to about 0.3. Example at f near 0.96: class 0 has 9.61, class 5 has 9.28, class 6 has 9.57 and class 7 has 9.55.
- The medians by class in the table of the modules avenue differ because a class meets other values of f along its family lines, not because the board lacks a class.

This check assumes two arms of 8 for every n. The board's packings are not public, so we cannot tell whether it reaches a class with a far zone, with a corner, or with arms of two sizes.

## 3. The tool

`zone_search.py` treats the zone as its own problem.

- **Exact evaluator** (`exact`, `length`): the smallest gap of a zone at a stack position by the lane's separating-axis test, and the length by bisection on the stack position. A zone is legal when no gap inside is below -2e-9 (the tolerance of `modules.legal`) and no square is within 2.2e-11 of the stack. A built layout gets its 2.2e-11 everywhere from the squeeze and floatsafe.
- **Compactor** (`compact`): the contact LP of `modules.py` on the zone's squares with the stack sliding and the angles free in a trust region. One call takes 0.2 to 0.3 s of CPU for 29 squares.
- **Soft search** (`soft`, `squeeze`): an overlap energy over the zone's squares with the stack held, minimised by L-BFGS with an exact gradient. The squeeze lowers the stack in steps while the energy still reaches zero, and the LP closes the rest. It takes 0.6 to 1.4 s of CPU.
- **Moves that change the count**: delete (a beam over which square leaves, ranked by the fixed-angle LP), insert (a square in the largest pocket, the stack pushed out as little as the soft search needs), rows (a row of `c - 1` uprights on the end wall under a known zone) and the taper enumeration of section 5.
- **Moves that keep the count**: hop (shake a neighbourhood, move one square to a pocket, snap angles to upright or to the flush tilt, change the kind of one square) and sweep (change the kind of every square in turn and keep what shortens the zone).

We did not run `fq` on a zone. Its objective is the side of the box, and a zone inside a frozen layout cannot change the side. It would need a moving wall in `fq` itself.

The public notebook `alexchilton/fault-line-dp-basin-hopping-lb-22-2620` is in the harvest dirs with its output files only, not its source. The write-up of `jonathan1506/joegun-22-2004-stretch-fault-line-dp-fq-quench`, which was written from the same starter kit, says what the fault-line DP enumerates: an upright block, the same block shifted along a staircase fault, and small gadgets cropped from good packings placed on the fault. It is a dynamic programme over donor gadgets along a fault line. It does not enumerate stack sizes of a taper, and it cannot make a zone that no donor holds.

## 4. Control

The library's best far zone of an 8-arm at f = 0.93 has 29 squares, length 4.156936 and loss 2.7133. 25 library zones of 29 squares reach this same length when carried to f = 0.93.

| control | start | result | difference to the library | verdict |
|---|---|---|---|---|
| A, seed 1 | every square moved by up to 0.2 and turned by up to 10 degrees, stack pushed out to 4.4569; squeeze and LP give 4.400040 | 4.156936 after 83 hops, 296 s | +4.2e-12 | pass |
| A, seed 5 | the same shake, stack pushed out to 4.7805; squeeze and LP give 4.161408; with every angle snapped to upright or the flush tilt first | 4.156936 with no hop | +6.9e-11 | pass |
| B, seed 3 | the library zone of 37 squares (5.205566), 8 squares deleted by the beam: 4.210038 | 4.156936 after two sweep changes and 16 hops | +2.6e-10 | pass |
| B, seed 5 | the same as seed 3 | 4.156936 after two sweep changes and 6 hops | +1.9e-11 | pass |
| B, seeds 1 and 2 | the same, with earlier versions of the moves | 4.161408 after 81 and 38 hops in 5 minutes | +4.5e-3 | fail |

The two failures of B ran before two repairs: the pocket finder placed the new square beyond the stack, so "move one square to a pocket" never worked, and the squeeze was three times slower. Both ended in the same zone at 4.161408, which is a real local optimum 0.0045 above the best.

The enumeration of section 5 has its own control: it returns the library's best zone at f = 0.70, 0.83, 0.93 and 0.95.

## 5. The taper enumeration, and why 5 mod 8 is special

The library's far zones are tapers. Under the flush stack lie sub-stacks of fewer squares on the same lattice (the flush stack moved by whole pitches towards the end wall), and uprights fill the room below them in columns that stand on the end wall.

`zone_search.py taper` enumerates this family in closed form. For a stack position `lam`:

- slab j is the flush stack moved j pitches towards the end wall. It holds a run of slots `a..b`. A run with `a > 0` moves along the stack until its corner is at `x = a`, so that it clears `a` columns of uprights on the wall side;
- there are `c - 1` columns of uprights, some against the wall (`x` from i to i + 1) and the others against the grid (`x` from W - 1 - i to W - i). The height of a column is the whole number of squares under the lowest tilted square above it, in closed form;
- a dynamic programme over the slabs keeps, for every vector of column heights, the partial taper with the most squares.

The count is a step function of `lam`. The length of a count is the first `lam` at which a taper holds it. A scan of `lam` from 3.3 to 5.3 in steps of 0.001 takes 17 s. Each best taper is then built as squares, squeezed and compacted with free angles, and its length is measured by the exact evaluator.

**Control.** The enumeration finds the library's best zone at four values of f:

| f | library's best far zone | enumeration |
|---|---|---|
| 0.70 | 41 squares (1 mod 8), loss 2.72 to 2.79 | 1 mod 8, loss 2.77 |
| 0.83 | 23 squares (7 mod 8), loss 3.13 to 3.17 | 7 mod 8, loss 3.16 |
| 0.93 | 29 squares (5 mod 8), length 4.156936, loss 2.7133 | 29 squares, length 4.156936, loss 2.7133 |
| 0.95 | 29 squares (5 mod 8), loss 2.813 | 5 mod 8, loss 2.8126 |

At f = 0.90 the enumeration gives 2.92 for class 5, and the library has 2.84 to 2.86 at f = 0.896 with a zone whose sub-stacks lean at their own tilts. So the lattice family is not everything.

**Loss of the best taper by class and f, for an arm of 8** (built and measured; bold is the lowest of the row). The library has 8-arm far zones of class 1 near f = 0.70, class 6 from 0.70 to 0.79, class 7 from 0.82 to 0.85, class 5 from 0.84 to 0.98, and one zone of class 4 at 0.92.

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 |
|---|---|---|---|---|---|---|---|---|
| 0.60 | 2.61 | **2.45** | 3.34 | 3.19 | 3.04 | 2.96 | 2.93 | 2.76 |
| 0.65 | 2.81 | **2.59** | 3.48 | 3.26 | 3.04 | 3.15 | 3.36 | 3.03 |
| 0.70 | 3.06 | **2.77** | 3.33 | 3.36 | 3.07 | 3.47 | 3.08 | 3.33 |
| 0.73 | 3.21 | **2.88** | 3.47 | 3.67 | 3.34 | 3.43 | 3.10 | 3.30 |
| 0.75 | 3.32 | 2.97 | 3.41 | 3.74 | 3.41 | 3.37 | **2.94** | 3.27 |
| 0.78 | 3.62 | 3.22 | 3.27 | 3.66 | 3.42 | 3.46 | **3.06** | 3.23 |
| 0.80 | 3.97 | 3.33 | **3.17** | 3.58 | 3.45 | 3.65 | 3.22 | 3.21 |
| 0.83 | 4.30 | 3.83 | 3.57 | 3.61 | 3.49 | 3.16 | 3.47 | **3.16** |
| 0.86 | 4.01 | 3.96 | 4.06 | 3.54 | 3.53 | **3.02** | 3.28 | 3.24 |
| 0.88 | 4.11 | 4.00 | 4.16 | 3.76 | 3.61 | **3.15** | 3.51 | 3.36 |
| 0.90 | 3.95 | 3.82 | 4.02 | 3.78 | 3.31 | **2.92** | 3.40 | 3.27 |
| 0.91 | 3.97 | 3.73 | 3.95 | 3.73 | 3.38 | **2.87** | 3.48 | 3.22 |
| 0.92 | 3.92 | 3.63 | 3.87 | 3.78 | 3.43 | **2.81** | 3.63 | 3.17 |
| 0.93 | 3.86 | 3.57 | 3.78 | 4.01 | 3.34 | **2.71** | 3.41 | 3.12 |
| 0.94 | 3.80 | 3.65 | 3.70 | 3.88 | 3.24 | **2.72** | 3.59 | 3.07 |
| 0.95 | 3.74 | 3.75 | 3.60 | 3.79 | 3.48 | **2.81** | 3.77 | 3.11 |
| 0.96 | 3.67 | 3.84 | 3.50 | 4.01 | 3.69 | **2.87** | 3.84 | 3.28 |
| 0.97 | 3.59 | 3.95 | 3.55 | 3.88 | 3.68 | **2.99** | 3.80 | 3.47 |
| 0.985 | 3.58 | 3.93 | 3.66 | 3.66 | 3.73 | **3.40** | 3.74 | 3.76 |

The scans of the stack position do not all have the same range (from 2.2 to 5.6 at most, from 3.3 to 5.3 at least). A row compares the classes at one f. Two rows can differ because one scan reached longer zones.

**Why 5 mod 8 is special at f = 0.93.** The library's zone is the taper with sub-stacks of 7, 5 and 4 squares and 13 uprights: a column of 4 against the wall, three single squares on the end wall, and columns of 1, 2 and 3 against the grid. Three contacts hold the stack, and each gives a smallest stack position in closed form:

```
grid column of 3 under the lowest corner of the flush stack     lam >= 3 + (8 cos t - W/2) tan t
end-wall square at x = 3..4 under the face of the third slab     lam >= 1 + 3 p + (4 - W/2) tan t
wall column of 4 under the face of the first slab at x = 1       lam >= 4 + p - (W/2 - 1) tan t
```

| f | grid column | end-wall square | wall column | spread |
|---|---|---|---|---|
| 0.900 | 4.22454 | 4.18293 | 4.06031 | 0.1642 |
| 0.920 | 4.18005 | 4.16560 | 4.09460 | 0.0855 |
| 0.930 | 4.15648 | 4.15694 | 4.11278 | 0.0442 |
| 0.940 | 4.13190 | 4.14826 | 4.13175 | 0.0165 |
| 0.947 | 4.11402 | 4.14217 | 4.14556 | 0.0315 |
| 0.960 | 4.07917 | 4.13083 | 4.17250 | 0.0933 |

The largest of the three is the length. At f = 0.93 the derivation gives 4.15694 and the library zone measures 4.156936. The three contacts close at the same stack position to 0.044 at f = 0.93 and to 0.017 at f = 0.94. No room is left unused under any of the three sub-stacks, and that is the band (0.92 to 0.947) where the library's loss is 2.71.

Another count changes one column height or one run by a whole square. That moves one contact by a whole step, 1 for a column and 0.748 for a run (`p - sin t`), and the other contacts stay. The stack then waits on the highest contact and room is lost under the others. Example: the best taper of 23 squares at f = 0.93 has its three contacts at 3.424, 3.380 and 3.157, a spread of 0.27, and loses 0.41 more.

So in this family one class has matching contacts at a given f, and which class it is changes with f: 1 from 0.60 to 0.73, 6 at 0.75 and 0.78, 2 at 0.80, 7 at 0.83, 5 from 0.86 to 0.985.

**Arms of 7 and 6.** The same enumeration runs for any arm size (`zone_search.py taper 7 F`, `taper 6 F`). The library's far zones cover three classes of a 7-arm (4, 5 and 6) and four classes of a 6-arm (1, 2, 3 and 4). Where both have a zone the enumeration agrees with the library in two cases: 6 mod 7 at f = 0.70 (2.30 against the library's 2.29) and 4 mod 6 at f = 0.80 (1.62 against 1.60). For 4 mod 7 the library's best is 2.21 at f = 0.86 with 32 squares, and the best taper there is 2.35 to 2.51. That is the second case where the lattice family is not everything.

Loss of the best taper for an arm of 7:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 |
|---|---|---|---|---|---|---|---|
| 0.60 | 2.61 | 2.95 | 2.84 | 2.73 | 2.93 | 2.61 | **2.50** |
| 0.65 | 2.49 | 2.87 | 2.69 | 2.66 | 2.93 | 2.58 | **2.40** |
| 0.70 | 2.84 | 2.70 | 2.45 | 2.58 | 2.82 | 2.55 | **2.30** |
| 0.73 | 3.05 | 2.75 | 2.46 | 2.51 | 2.77 | 2.69 | **2.40** |
| 0.75 | 3.15 | 2.83 | 2.51 | **2.49** | 2.76 | 2.71 | 2.50 |
| 0.78 | 3.32 | 2.95 | **2.59** | 2.76 | 2.76 | 2.72 | 2.67 |
| 0.80 | 3.33 | 3.12 | 2.72 | 2.94 | **2.71** | 2.72 | 2.79 |
| 0.83 | 3.25 | 3.54 | 3.11 | 2.99 | **2.62** | 2.72 | 2.98 |
| 0.86 | 3.17 | 3.38 | 3.28 | 3.03 | **2.51** | 2.72 | 2.74 |
| 0.88 | 3.11 | 3.41 | 3.34 | 2.93 | **2.35** | 2.72 | 2.85 |
| 0.90 | 3.04 | 3.45 | 3.40 | 3.10 | **2.50** | 2.72 | 2.98 |
| 0.92 | 3.08 | 3.37 | 3.47 | 3.00 | **2.42** | 2.72 | 2.82 |
| 0.93 | 3.16 | 3.32 | 3.50 | 2.85 | **2.59** | 2.81 | 2.94 |
| 0.95 | 3.06 | 3.22 | 3.26 | 2.79 | **2.57** | 2.81 | 3.20 |
| 0.96 | 2.99 | 3.16 | 3.24 | **2.77** | 2.78 | 2.79 | 3.33 |
| 0.97 | 2.91 | 3.10 | 3.29 | **2.75** | 2.99 | 2.77 | 3.40 |

Loss of the best taper for an arm of 6:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 |
|---|---|---|---|---|---|---|
| 0.60 | 1.55 | **1.49** | 1.78 | 1.67 | 1.66 | 1.62 |
| 0.65 | 1.99 | 1.85 | 1.86 | 1.64 | **1.59** | 2.12 |
| 0.70 | 2.26 | 2.27 | 2.64 | 1.85 | **1.65** | 2.68 |
| 0.73 | 2.55 | 2.54 | 2.13 | 1.88 | **1.64** | 2.80 |
| 0.75 | 2.49 | 2.62 | 2.18 | 1.90 | **1.63** | 2.77 |
| 0.78 | 2.40 | 2.60 | 2.23 | 1.91 | **1.62** | 2.69 |
| 0.80 | 2.34 | 2.58 | 2.31 | 1.86 | **1.62** | 2.59 |
| 0.83 | 2.37 | 2.55 | 2.52 | 2.13 | **1.74** | 2.76 |
| 0.86 | 2.33 | 2.50 | 2.67 | 2.23 | **1.79** | 2.76 |
| 0.88 | 2.13 | 2.46 | 2.60 | 2.13 | **1.66** | 2.60 |
| 0.90 | 2.22 | 2.42 | 2.61 | 2.33 | **1.83** | 2.72 |
| 0.92 | 2.37 | 2.36 | 2.19 | 2.55 | **1.94** | 2.69 |
| 0.93 | 2.45 | 2.35 | 2.17 | 2.28 | **1.88** | 2.68 |
| 0.95 | 2.61 | 2.44 | 2.14 | 2.59 | **2.00** | 2.64 |
| 0.96 | 2.70 | 2.50 | **2.12** | 2.62 | 2.15 | 2.62 |
| 0.97 | 2.79 | 2.55 | **2.10** | 2.63 | 2.31 | 2.60 |

The classes are closer together here than on an 8-arm. On a 7-arm at f = 0.70 to 0.78 the class 2 is the best class or at most 0.15 above it, and the library has no zone of that class. The zone of 16 squares at f = 0.70 (2 mod 7, length 2.952625, loss 2.4525, one slab of 7 with the runs below it empty, columns of 3, 2, 2, 1 and 1 uprights against the wall) is the one that wins n = 634 in section 7.

## 6. The zones found at f = 0.93

The first target was the 8-arm far zone at f = 0.93 for the seven classes other than 5.

| class | count | length | loss | above 2.7133 | sub-stacks by slab (slots), uprights against the wall, against the grid | how found |
|---|---|---|---|---|---|---|
| 0 | 24 | 3.651748 | 3.8592 | +1.146 | 0-7.0-5.0-2.0-1; []; [1, 1, 1, 1, 1, 0, 0] | taper enumeration |
| 1 | 25 | 3.744290 | 3.5652 | +0.852 | 0-7.3-6.3-5.0; [3, 3, 3]; [1, 0, 0, 0] | taper enumeration |
| 2 | 26 | 3.904114 | 3.7845 | +1.071 | 0-6.0-4.0-3.0-2; []; [2, 2, 2, 1, 0, 0, 0] | taper enumeration |
| 3 | 27 | 4.064149 | 4.0054 | +1.292 | 1-6.1-4.1-3.1-2; [5]; [2, 2, 2, 1, 0, 0] | taper enumeration |
| 4 | 36 | 5.156480 | 3.3388 | +0.626 | 0-6.1-5.1-4.1-3.1-2; [5]; [4, 3, 2, 1, 0, 0] | taper enumeration |
| 5 | 29 | 4.156936 | 2.7133 | +0.000 | 0-6.1-5.1-4.0; [4, 1, 1, 1]; [3, 2, 1] | taper enumeration (the library's zone) |
| 6 | 30 | 4.379782 | 3.4134 | +0.700 | 2-6.2-5.2-4.2-3.0; [5, 5]; [3, 2, 1, 0, 0] | taper enumeration |
| 7 | 23 | 3.423939 | 3.1212 | +0.408 | 2-6.2-5.0.0; [4, 4, 1, 1, 1]; [2, 1] | taper enumeration |

No class is within 0.3 of 2.71 at f = 0.93. The nearest is class 7 at +0.41. At other f the classes are closer to the best taper of their row: at f = 0.75 class 1 is 0.03 above it; at f = 0.80 classes 7 and 6 are 0.04 and 0.05 above, and class 1 is 0.16 above; at f = 0.60 class 0 is 0.16 above; at f = 0.70 classes 0, 4 and 6 are 0.29 to 0.31 above; at f = 0.95 class 7 is 0.30 above.

What the other moves gave at f = 0.93:

- **Delete.** One square deleted from the zone of 37 and compacted gives 36 squares at 5.176583, loss 3.49. A sweep takes it to 5.161408, loss 3.38.
- **Rows.** One row of 7 uprights under the zone of 29 gives 36 squares at 5.156936, loss 3.34. The enumeration finds 5.156480, loss 3.3388.
- **Insert.** One square in the largest pocket of the zone of 29 gives 30 squares at 4.428411, loss 3.78, and 4.470108 from another pocket. The enumeration finds 4.379782, loss 3.41.
- **Hops.** 669 hops from the class-7 zone of 23 squares (688 s of CPU) found nothing shorter than 3.423939. Shorter runs from the zones of 31, 36 and 30 squares found nothing either. Hops had about 26 CPU-minutes on new classes in all: 15 on class 7, 6 on class 4 and 4 on class 6. The kill line asked for 40 CPU-minutes on each of three classes with two kinds of move. We did not spend them: when the enumeration gave a zone for every class in 17 s, the two processes went to the enumeration at other f, to the generator and to the builds.

Row listings of the new designs (each square as `x,y:angle`, by row of `y`; pictures and module files are in the take's `work/zones`):

Class 7, 23 squares, length 3.423939, loss 3.1212:

```
y~1  0.50,0.50:-0  1.50,0.50:-0  2.50,0.50:-0  3.50,0.50:+0  4.50,0.50:+0  5.52,1.36:-18  6.43,0.50:-0  7.43,0.50:+0
y~2  0.50,1.50:+0  1.50,1.50:-0  2.63,2.17:-18  3.51,1.63:-18  4.55,1.63:-18  5.49,2.42:-18  6.44,2.12:-18  7.43,1.50:-0
y~3  0.50,2.50:-0  1.50,2.50:-0  2.63,3.32:-18  3.55,2.93:-18  4.52,2.69:-18
y~4  0.50,3.50:-0  1.50,3.50:-0
```

Class 4, 36 squares, length 5.156480, loss 3.3388:

```
y~1  0.50,0.50:+0  1.63,0.63:-18  2.68,0.63:-18  3.50,1.41:-18  4.40,0.50:-0  5.40,0.50:-0  6.40,0.50:-0  7.43,0.50:+0
y~2  0.50,1.50:-0  1.63,2.12:-18  2.55,1.72:-18  3.48,2.48:-18  4.43,2.17:-18  5.40,1.50:-0  6.40,1.50:-0  7.43,1.50:+0
y~3  0.50,2.50:+0  1.63,3.26:-18  2.55,2.87:-18  4.43,3.22:-18  5.38,2.92:-18  6.43,2.50:-0  7.43,2.50:+0
y~4  0.50,3.50:-0  1.63,4.32:-18  2.58,4.01:-18  3.50,3.62:-18  4.43,4.38:-18  5.35,3.98:-18  6.30,3.67:-18  7.43,3.50:+0
y~5  0.50,4.50:-0  1.60,5.38:-18  2.55,5.08:-18  3.50,4.77:-18
y~6  0.63,5.63:-18
```

Class 6, 30 squares, length 4.379782, loss 3.4134:

```
y~0  1.50,0.50:+0  6.43,0.50:+0  7.43,0.50:-0
y~1  0.50,0.50:-0  2.63,1.01:-18  3.83,0.63:-18  4.55,1.45:-18  5.43,0.50:-0
y~2  0.50,1.50:-0  1.50,2.50:-0  1.50,1.50:+0  2.63,2.06:-18  3.59,1.75:-18  5.47,2.23:-14  6.43,1.50:+0  7.43,1.50:+0  7.43,2.50:+0
y~3  0.50,2.50:-0  2.61,3.14:-14  3.56,2.84:-14  4.52,2.53:-14  5.47,3.34:-13  6.43,3.04:-13
y~4  0.50,3.50:-0  1.50,3.50:+0  2.60,4.24:-13  3.55,3.94:-13  4.51,3.64:-13
y~5  0.50,4.82:-0  1.50,4.50:-0
```

Class 1, 25 squares, length 3.744290, loss 3.5652:

```
y~0  7.43,0.50:+0
y~1  0.50,0.50:-0  1.50,0.50:-0  1.50,1.50:-0  2.50,0.50:-0  3.63,1.23:-18  4.49,0.63:-18  5.53,0.63:-18  6.49,1.37:-18
y~2  0.50,1.50:+0  2.50,1.50:-0  3.63,2.28:-18  4.58,1.98:-18  5.53,1.68:-18  6.35,2.47:-18  7.30,2.17:-18
y~3  0.50,2.50:-0  1.50,2.50:-0  2.50,2.50:-0  3.49,3.37:-18  4.44,3.07:-18  5.40,2.77:-18
y~4  0.63,4.27:-18  1.47,3.63:-18  2.52,3.63:-18
```

Class 2, 26 squares, length 3.904114, loss 3.7845:

```
y~0  6.43,0.50:+0
y~1  0.63,0.93:-18  1.58,0.63:-18  2.63,0.63:-18  3.53,1.39:-18  4.43,0.50:-0  5.43,0.50:-0  7.43,0.50:-0
y~2  0.63,2.16:-18  1.53,1.69:-18  2.58,1.69:-18  3.50,2.45:-18  4.45,2.15:-18  5.43,1.50:+0  6.43,1.50:+0  7.43,1.50:-0
y~3  0.63,3.33:-18  1.55,2.92:-18  2.54,2.75:-18  4.43,3.20:-18  5.39,2.90:-18  6.35,2.63:-18
y~4  0.63,4.43:-18  1.57,4.08:-18  2.53,3.81:-18  3.48,3.50:-18
```

Class 0, 24 squares, length 3.651748, loss 3.8592:

```
y~0  3.43,0.50:+0  4.43,0.50:+0  7.43,0.50:+0
y~1  0.63,0.93:-18  1.58,0.63:-18  2.52,1.38:-18  5.43,0.50:+0  6.43,0.50:-0
y~2  0.63,2.02:-18  1.57,1.68:-18  2.50,2.43:-18  3.46,2.13:-18  4.35,1.63:-18  5.40,1.63:-18  6.35,2.37:-18  7.30,1.63:-18
y~3  0.63,3.13:-18  1.56,2.78:-18  3.46,3.18:-18  4.41,2.88:-18  5.40,2.68:-18
y~4  0.63,4.18:-18  1.58,3.88:-18  2.52,3.52:-18
```

Class 3, 27 squares, length 4.064149, loss 4.0054:

```
y~0  0.50,0.50:+0
y~1  1.63,0.93:-18  2.58,0.63:-18  3.52,1.38:-18  4.43,0.50:+0  5.43,0.50:+0  6.43,0.50:+0  7.43,0.50:+0
y~2  0.50,1.50:+0  1.63,2.01:-18  2.57,1.68:-18  3.49,2.44:-18  4.45,2.14:-18  5.43,1.50:+0  6.43,1.50:+0  7.43,1.50:+0
y~3  0.50,2.50:-0  1.63,3.16:-18  2.55,2.77:-18  4.45,3.18:-18  5.40,2.88:-18  6.37,2.63:-18
y~4  0.50,3.50:-0  1.63,4.21:-18  2.58,3.91:-18  3.50,3.52:-18
y~5  0.50,4.50:-0
```

## 7. The generator with the new zones

The go line was not met, so the build step was not due. We ran the generator anyway, because the new zones serve classes the library lacks.

`zone_search.py merge` adds new zones to the library: for each f, every class within a set distance of the best one, with lengths tabulated within 0.05 of the f the zone was made at. `zone_search.py predict` runs the generator of `modules.py` on every n below the plain grid. We ran it four times as the zones arrived.

| library | new zones | n with a prediction | n whose best choice uses a new zone | of these predicted below held |
|---|---|---|---|---|
| 8-arm zones at six f | 29 | 319 (n from 430) | 96 | 0 |
| plus 8-arm zones at eight more f | 57 | 319 | 99 | 0 |
| plus 7-arm and 6-arm zones at eight f | 109 | 385 (n from 300) | 158 | 1 (n = 634) |
| plus all three arm sizes at f from 0.60 to 0.78, and 7 and 6 at 0.88, 0.92 and 0.96 | 200 | 385 | 185 | 1 (n = 634) |

We built every n whose prediction was near held and whose best choice holds a new zone. `zone_search.py build` starts a little above the prediction, runs the lane's LP and then the `fq` quench. `modules.py take` certified the builds: floatsafe at 2.2e-11, and below the held score by more than 1e-10. The table has the best build of each n. The second row of 634 is the best build with 8-arm zones only.

| n | corner + far zones | predicted side | built side | held side | built minus held | verdict |
|---|---|---|---|---|---|---|
| 634 | 852h.C + z7-16f700 + 740h.F1 | 25.703584 | 25.703583888 | 25.707106782 | -0.003523 | certified, gain 1.399e-04 |
| 995 | 933h.C + 814h09.F1 + z8-36f930 | 31.951899 | 31.949968445 | 31.951392555 | -0.001424 | certified, gain 4.515e-05 |
| 340 | 340h.C + 304h.F1 + z6-21f930 | 18.927115 | 18.926898900 | 18.926898901 | -0.000000 | not kept: the score agrees with held to 3e-14 |
| 552 | 552h.C + 504h.F2 + z7-25f960 | 23.940563 | 23.940282808 | 23.940134515 | +0.000148 | above held |
| 854 | 740h.C + z8-32f750 + z8-32f730 | 29.729227 | 29.728120903 | 29.727922063 | +0.000199 | above held |
| 796 | 740h.C + 740h.F1 + z8-32f730 | 28.723637 | 28.722766136 | 28.721540004 | +0.001226 | above held |
| 634 | 740h.C + z8-26f700 + z8-26f700 | 25.709473 | 25.709099791 | 25.707106782 | +0.001993 | above held |
| 795 | 740h.C + z8-32f750 + z8-32f750 | 28.706775 | 28.706459834 | 28.703852896 | +0.002607 | above held |
| 420 | 759h.C + z7-14f970 + z7-14f970 | 20.966633 | 20.963969503 | 20.961293021 | +0.002676 | above held |
| 862 | 862h.C + z8-37f830 + 984h.F1 | 29.836828 | 29.836557933 | 29.833382720 | +0.003175 | above held |
| 982 | 983h.C + 983h.F1 + z7-17f800 | 31.817068 | 31.815607755 | 31.810539459 | +0.005068 | above held |
| 994 | 933h.C + z8-36f930 + z8-36f930 | 31.948070 | 31.946454764 | 31.940885411 | +0.005569 | above held |

- **634** has an arm of 7 and an arm of 8 at f = 0.70. The corner and the 8-arm far zone come from the held layouts of 852 and 740. The 7-arm far zone is the new zone of 16 squares (2 mod 7) of section 5. The build ends at the predicted side to 1e-7.
- **995** has two arms of 8 at f = 0.95. One far zone is the new zone of 36 squares (4 mod 8) of section 6, with a loss of 3.34. The prediction was 0.0005 above held and the build ended 0.0019 below the prediction. The take of the modules avenue has this n with a gain of 3.4e-06 of score, and this build is 4.17e-05 of score below it.
- **340** ends at the side of held. The scores agree to 3e-14, so the quench reached the optimum that held already has.
- **552 and 854** are near misses. Since n is the side squared less the losses, 0.000148 and 0.000199 of side are 0.007 and 0.012 of a square of loss. Six choices of far zones for 854 end at the same side.

The take has 2 n with a gain of 1.8506e-04 on held, and 1.8163e-04 over the other takes.

## 8. What the slide is worth

Every number above keeps the grid side of the strip rigid. The modules avenue measured what the slide is worth on whole layouts: its builds end a median 0.0006 of side below their prediction and at most 0.0086 below, and one layout (998) has a corner 0.041 of length shorter than the rigid cut allows. We did not measure the slide on a zone alone. The 12 builds of section 7 end 0.0000 to 0.0027 of side below their prediction, with a median of 0.0006. So the slide and the quench together are worth about as much here as in the modules avenue, and the loss of a rigid zone is a fair guide to what a build gives.

## 9. What to search next

1. **The near misses.** 552 and 854 are 0.007 and 0.012 of a square of loss from held. Their new zones were made at f = 0.96 and at 0.75 and 0.73, and the layouts sit at f = 0.940 and 0.728. Make the taper at the f of the n, then give that zone the hops and the sub-stacks of item 3.
2. **The corner by the same enumeration.** The board has every class at one loss, and our far zones have one cheap class per f. The corner has two lengths that trade, so it has more ways to bring its contacts together. A corner is two tapers that share the squares at the meeting of the arms. The library's corners of two 8-arms hold 2 or 3 mod 8.
3. **Sub-stacks at their own tilt.** Beside k columns of uprights a sub-stack of `c - k` squares is flush at a steeper tilt. Three library zones of this kind are better than the lattice: the 8-arm zone at f = 0.896 (loss 2.84 against 2.92), the second 8-arm zone of 29 squares at f = 0.93 (length 4.1728), and the 7-arm zone of 32 squares at f = 0.86 (loss 2.21 against 2.35 to 2.51). Add a second lattice to the dynamic programme.
4. **More f, longer zones, more arm sizes.** We scanned 16 to 19 values of f, stack positions up to 5.6 and arms of 8, 7 and 6. The two wins and the two near misses came from f = 0.70, 0.73, 0.75, 0.93 and 0.96. Scan f from 0.60 to 0.99 in steps of 0.01, stack positions up to 10 (the library's best 8-arm zone of class 6 at f = 0.70 has 70 squares), and arms of 5 and 9.
5. **Hops with a longer run.** The hops had 26 CPU-minutes on the new classes and found nothing. Give each of classes 7, 4 and 6 at f = 0.93 its 40 CPU-minutes, from the tapers of section 6.
6. **The slide on a zone alone.** Let the grid side of the strip slide in the zone problem, and measure what it gives for each class.

## 10. Low side fractions (2026-11-12, round 11)

**Result.** Every count class of arms of 6 to 11 at f from 0.64 to 0.86 now has a far zone: 378 new rows in the zone table, and their module files in the zones dir. Where the library already had a class, the lattice gives the library's loss to 0.05 squares, and neither hops nor a slot in the grid go clearly below it. At low f the classes sit close together, because one row of uprights costs 0.29 squares at f = 0.70 against 0.63 at 0.93. With the library's corners, two flush arms still lose 0.2 to about 3 squares more than held and 0.7 to about 3.5 more than the board (section 10.3). So at low f the far zone is not what we lack: the corner is. The generator with these zones certifies 4 n against round 11 for 6.045e-05, and 921 is most of it (0.00168 of side, with a short 9-arm zone of class 7).

This section searches the far zone at f from 0.64 to 0.86. That band holds 0.097 of our 0.134 to the board. The tool is `zone_search.py` as it is. The steps around it are in [`zone_lowf.py`](../zone_lowf.py): pick one zone per class, tabulate, join into the library, the three-zone sum, the slide and the tapers that poke.

### 10.1 Loss by class

Loss of the best far zone by class, built and measured. The count is in parentheses and bold is the lowest of the row. The scan of the stack position runs to 9.0 for arms of 6, 7 and 8 (section 5 stopped at 5.6 or 6.6), to 7.0 for arms of 9 and 10, and to 6.6 for an arm of 11. The run kept 2,219 zones, the shortest for every count at 53 pairs of arm size and f. The table of zones gets one row per class of every pair, the one with the lowest loss: 376 new rows, because 64 were in it already.

Arm of 6:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 |
|---|---|---|---|---|---|---|
| 0.68 | 2.20 (24) | 2.10 (13) | 1.93 (26) | 1.76 (21) | **1.58** (16) | 2.45 (23) |
| 0.71 | 2.29 (24) | 2.29 (31) | 2.08 (26) | 1.86 (21) | **1.65** (16) | 2.79 (23) |
| 0.75 | 2.49 (12) | 2.45 (31) | 2.18 (26) | 1.90 (21) | **1.63** (16) | 2.77 (11) |
| 0.78 | 2.40 (12) | 2.54 (31) | 2.23 (26) | 1.91 (21) | **1.62** (16) | 2.69 (11) |
| 0.80 | 2.34 (12) | 2.55 (31) | 2.21 (26) | 1.86 (21) | **1.62** (16) | 2.59 (11) |
| 0.82 | 2.33 (12) | 2.56 (13) | 2.41 (14) | 2.04 (15) | **1.66** (16) | 2.70 (11) |
| 0.84 | 2.42 (12) | 2.53 (13) | 2.43 (20) | 2.22 (15) | **1.82** (16) | 2.78 (11) |

Arm of 7:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 |
|---|---|---|---|---|---|---|---|
| 0.66 | 2.45 (21) | 2.83 (15) | 2.64 (16) | 2.65 (17) | 2.77 (32) | 2.57 (26) | **2.38** (20) |
| 0.68 | 2.60 (21) | 2.77 (15) | 2.55 (16) | 2.61 (17) | 2.78 (32) | 2.56 (26) | **2.34** (20) |
| 0.70 | 2.50 (42) | 2.72 (15) | 2.47 (16) | 2.58 (17) | 2.82 (25) | 2.57 (19) | **2.32** (20) |
| 0.71 | 2.94 (35) | 2.68 (22) | 2.42 (16) | 2.56 (17) | 2.82 (18) | 2.56 (12) | **2.29** (20) |
| 0.73 | 3.05 (28) | 2.76 (22) | 2.46 (16) | 2.51 (17) | 2.74 (39) | 2.69 (12) | **2.39** (13) |
| 0.75 | 3.15 (28) | 2.83 (22) | 2.51 (16) | **2.49** (17) | 2.75 (39) | 2.71 (19) | 2.50 (13) |
| 0.78 | 3.32 (28) | 2.95 (22) | 2.59 (16) | 2.76 (17) | **2.56** (39) | 2.72 (19) | 2.67 (13) |
| 0.82 | 3.28 (14) | 3.40 (22) | 2.98 (16) | 3.03 (31) | **2.30** (32) | 2.72 (19) | 2.92 (13) |
| 0.84 | 3.23 (14) | 3.62 (43) | 3.22 (16) | 2.92 (31) | **2.44** (39) | 2.72 (12) | 2.96 (13) |
| 0.86 | 3.17 (14) | 3.38 (15) | 3.28 (16) | 2.59 (38) | **2.22** (32) | 2.72 (12) | 2.74 (13) |

Arm of 8:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 |
|---|---|---|---|---|---|---|---|---|
| 0.65 | 2.81 (24) | **2.59** (17) | 3.48 (34) | 3.26 (27) | 3.04 (20) | 3.15 (21) | 3.25 (38) | 3.03 (31) |
| 0.66 | 2.86 (24) | **2.63** (17) | 3.45 (18) | 3.28 (27) | 3.05 (20) | 3.21 (21) | 3.26 (54) | 3.09 (31) |
| 0.68 | 2.96 (24) | **2.70** (17) | 3.39 (18) | 3.32 (27) | 3.06 (20) | 3.34 (21) | 3.10 (54) | 3.22 (31) |
| 0.70 | 3.06 (24) | **2.77** (17) | 3.33 (18) | 3.36 (27) | 3.07 (20) | 3.47 (13) | 2.85 (46) | 3.33 (23) |
| 0.72 | 3.16 (32) | **2.85** (25) | 3.37 (18) | 3.55 (27) | 3.24 (20) | 3.28 (61) | 3.00 (46) | 3.31 (23) |
| 0.75 | 3.32 (32) | 2.97 (25) | 3.41 (18) | 3.74 (11) | 3.41 (60) | 3.29 (53) | **2.82** (46) | 3.27 (23) |
| 0.77 | 3.44 (32) | 3.06 (25) | 3.32 (18) | 3.69 (59) | 3.41 (20) | 3.36 (37) | **2.98** (30) | 3.25 (15) |
| 0.80 | 3.97 (32) | 3.19 (41) | **3.17** (18) | 3.48 (59) | 3.45 (20) | 3.65 (13) | 3.22 (30) | 3.21 (15) |
| 0.82 | 4.24 (16) | 3.87 (17) | 3.41 (18) | 3.50 (27) | 3.48 (20) | 3.22 (37) | 3.39 (22) | **3.17** (15) |
| 0.84 | 4.17 (16) | 3.87 (17) | 3.73 (18) | 3.54 (27) | 3.50 (12) | **3.14** (37) | 3.35 (22) | 3.14 (15) |
| 0.86 | 4.01 (16) | 3.96 (17) | 4.06 (18) | 3.54 (27) | 3.53 (12) | **3.06** (37) | 3.28 (22) | 3.24 (15) |

Arm of 9:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 | class 8 |
|---|---|---|---|---|---|---|---|---|---|
| 0.64 | **2.91** (54) | 3.43 (46) | 3.77 (29) | 3.54 (21) | 4.06 (22) | 4.17 (23) | 4.12 (24) | 3.39 (52) | 3.15 (53) |
| 0.68 | **3.24** (36) | 3.43 (19) | 4.00 (29) | 3.74 (30) | 3.93 (22) | 4.19 (32) | 3.93 (24) | 3.82 (52) | 3.53 (44) |
| 0.72 | 3.41 (27) | **3.30** (19) | 4.12 (38) | 3.78 (30) | 3.67 (22) | 3.99 (32) | 3.93 (24) | 4.10 (43) | 3.75 (35) |
| 0.74 | 3.57 (36) | **3.26** (46) | 4.23 (38) | 4.05 (48) | 3.67 (22) | 3.93 (32) | 3.93 (24) | 3.84 (43) | 3.94 (44) |
| 0.76 | 3.50 (36) | **3.16** (28) | 4.32 (29) | 3.95 (21) | 3.92 (22) | 4.12 (32) | 3.93 (24) | 3.70 (43) | 3.90 (44) |
| 0.78 | 3.89 (36) | **3.46** (28) | 4.26 (20) | 3.97 (21) | 4.18 (22) | 4.32 (23) | 3.92 (24) | 3.58 (43) | 4.32 (44) |
| 0.80 | 4.14 (18) | 3.84 (28) | 4.46 (20) | 4.03 (21) | 4.45 (22) | 4.54 (23) | 4.08 (24) | **3.46** (43) | 4.60 (17) |
| 0.82 | 4.25 (45) | 4.06 (37) | 4.73 (20) | 4.24 (39) | 4.36 (31) | 4.58 (41) | 3.93 (51) | **3.44** (43) | 4.74 (17) |
| 0.84 | 4.11 (45) | 4.48 (46) | 4.54 (20) | 4.02 (21) | 4.20 (31) | 4.24 (50) | 3.72 (42) | **3.40** (43) | 4.62 (17) |
| 0.86 | 4.06 (18) | 4.80 (19) | 4.43 (29) | 3.88 (21) | 4.03 (31) | 4.33 (23) | 3.79 (24) | **3.25** (52) | 4.58 (17) |

Arm of 10:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 | class 8 | class 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.64 | 5.01 (20) | 4.53 (21) | - | - | - | - | - | 5.04 (17) | 4.66 (18) | **4.40** (19) |
| 0.68 | **3.83** (50) | 4.27 (31) | 4.11 (22) | 4.16 (23) | 4.66 (24) | 4.49 (25) | 4.79 (26) | 4.89 (37) | 4.63 (28) | 4.32 (19) |
| 0.72 | **4.01** (40) | 4.49 (21) | 4.12 (22) | 4.50 (23) | 4.76 (24) | 4.39 (35) | 4.99 (26) | 5.12 (47) | 4.75 (38) | 4.38 (29) |
| 0.74 | **3.85** (40) | 4.60 (21) | 4.21 (22) | 4.26 (33) | 4.99 (24) | 4.59 (25) | 5.06 (36) | 5.39 (17) | 4.66 (58) | 4.27 (49) |
| 0.76 | 4.18 (30) | 4.90 (21) | 4.47 (22) | 4.51 (33) | 5.24 (24) | 4.81 (25) | 4.88 (36) | 5.31 (57) | 4.57 (58) | **4.15** (49) |
| 0.78 | **4.07** (40) | 4.78 (41) | 4.33 (22) | 4.85 (33) | 5.04 (24) | 4.59 (25) | 4.70 (36) | 5.14 (57) | 4.66 (58) | 4.18 (59) |
| 0.80 | 4.51 (40) | 4.63 (21) | 4.15 (22) | 5.01 (23) | 4.81 (34) | 4.33 (25) | 4.50 (36) | 4.94 (47) | 4.46 (38) | **4.00** (39) |
| 0.82 | 4.84 (60) | 4.55 (31) | 4.21 (22) | 4.85 (23) | 4.81 (34) | 4.30 (45) | 4.29 (36) | 4.97 (17) | 4.63 (28) | **4.12** (39) |
| 0.84 | 5.27 (20) | 4.86 (41) | **4.32** (32) | 4.67 (23) | 4.95 (34) | 4.41 (25) | 4.33 (36) | 4.95 (17) | 4.45 (58) | 4.33 (29) |
| 0.86 | 5.13 (20) | 5.02 (51) | 4.45 (32) | 4.74 (23) | 5.15 (24) | 4.78 (25) | 4.64 (26) | **4.31** (57) | 4.36 (38) | 4.54 (19) |

Arm of 11:

| f | class 0 | class 1 | class 2 | class 3 | class 4 | class 5 | class 6 | class 7 | class 8 | class 9 | class 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.68 | 5.06 (22) | **4.47** (56) | 4.81 (35) | 5.13 (25) | 4.79 (26) | 5.57 (27) | 5.87 (28) | 5.53 (29) | 5.39 (30) | 5.06 (42) | 5.40 (21) |
| 0.72 | 4.71 (55) | **4.32** (56) | 5.32 (35) | 5.30 (58) | 4.91 (26) | 5.72 (27) | 5.91 (39) | 5.52 (29) | 5.52 (41) | 5.33 (31) | 5.48 (54) |
| 0.76 | 4.59 (55) | **4.14** (45) | 5.48 (46) | 5.03 (47) | 4.58 (26) | 5.36 (27) | 5.48 (50) | 5.03 (29) | 5.07 (41) | 5.60 (42) | 5.15 (32) |
| 0.80 | 4.93 (44) | **4.43** (34) | 5.32 (24) | 5.20 (58) | 4.70 (37) | 4.94 (27) | 5.58 (28) | 5.16 (29) | 5.16 (30) | 5.70 (53) | 5.20 (43) |
| 0.84 | 5.31 (55) | 4.75 (45) | 5.08 (24) | 5.65 (25) | 5.27 (37) | 5.16 (27) | 5.55 (50) | 5.05 (40) | 5.24 (63) | **4.67** (64) | 5.00 (32) |

How these compare with the library where it has a zone:

| arm | f | best class here | the library there |
|---|---|---|---|
| 6 | 0.68 to 0.82 | class 4, 1.58 to 1.66 | class 4, 1.60 to 1.63 (at f 0.77 to 0.82) |
| 7 | 0.68 to 0.71 | class 6, 2.29 to 2.34 | class 6, 2.29 at f = 0.70 |
| 7 | 0.82 and 0.86 | class 4, 2.30 and 2.22 | class 4, 2.29 and 2.21 |
| 8 | 0.70 | class 1, 2.77 | class 1, 2.69 to 2.78 |
| 8 | 0.70 | class 6, 2.85 after the sweep (3.07 before) | class 6, 2.84 to 2.90 |
| 8 | 0.80 | class 2, 3.17 (new), then classes 1, 7 and 6 at 3.19, 3.21 and 3.22 | classes 7 and 6 at 3.21 and 3.22, class 5 at 3.29 |
| 8 | 0.84 | classes 5 and 7 at 3.14 | class 5 at 3.11, class 7 at 3.14 |
| 9 | 0.76 | class 1, 3.16 (new), class 0 at 3.50 | class 0 at 3.44, class 7 at 3.73, class 8 at 3.90 |
| 9 | 0.84 | class 7, 3.40 with 43 squares | class 7, 3.36 with 88 squares |
| 10 | 0.80 | class 9, 4.00 | class 9, 3.98 to 4.02 |
| 11 | 0.68 to 0.84 | class 1, 4.14 to 4.47 | no zone of an 11-arm |

- **New classes.** The library has one to four classes per arm below f = 0.86. Every class now has a zone. Two of the new classes are the cheapest of their row: class 2 of an 8-arm at f = 0.80 (3.17) and class 1 of a 9-arm at f = 0.72 to 0.78 (3.16 to 3.46).
- **The level does not move.** In every row where the library has the cheapest class, the lattice gives the same loss to 0.05 squares. The library was cut from the best public and held layouts, so this is the level of those layouts.
- **A better zone of a count the library already has.** The 9-arm zone of class 7 at f = 0.84 has 43 squares here. The library also holds a 43-square zone of that class (983h.F1, loss 3.41, usable from f 0.72 to 0.915), next to an 88-square one. The new zone loses 3.342 at the f of 921 against 3.431 for 983h.F1, 0.09 squares less. This is the zone behind the one win of this section (section 10.6). (Corrected after the zones skeptic of 2026-11-12: the first text said the library had this class only as an 88-square zone.)
- **Arm of 11.** `taper_best` packs the column heights into one 64-bit key, and an arm of 11 has 20 columns, one digit more than the key holds. Two states can then share a key. The zones are measured by the exact evaluator, so every number in the row is a real zone. A better taper of an 11-arm can be missing.

### 10.2 Why the classes are close at low f

One row of `c - 1` uprights on the end wall under a zone adds `c - 1` squares and 1 of length. The loss grows by `c cos t - (c - 1) = f - sin t`, and the class goes down by one. For an arm of 8 this step costs 0.29 at f = 0.70, 0.43 at f = 0.80 and 0.63 at f = 0.93. This is a derivation, and the table agrees with it.

At f = 0.70 class 1 has 2.77, class 0 has 3.06 (one row more) and class 7 has 3.33 (two rows). Class 3 is class 4 plus one row (3.07 and 3.36). So at low f a class is never far from a good one. The spread of the eight classes is 0.70 at f = 0.70 and 0.80 at f = 0.80, against 1.30 at f = 0.93.

This is why the low band is not a problem of classes. Section 2 found that the board has every class at one loss for f of 0.90 and more. Below 0.86 our own zones have that too, within 0.7.

### 10.3 The three-zone loss with the library's best corner

`zone_lowf.py three` adds the corner and two far zones for every class `(k - 2m - 1) mod c` of n, with the lowest sum. The corner is the library's, carried to f by its table. "Board" and "held" are the loss of the board's side and of our side as if the layout had two c-arms, for the n whose board f is within 0.03 (median by class, range over the classes).

The plain sum is a lower bound, because the two far zones must also end their arms together. In squares, the corner's `y0 - x0`, plus class and loss of far zone 1, less class and loss of far zone 2, must be a multiple of c. What is left over is wall on the looser arm that holds nothing. The column "with the slack" adds it. The corner can take up a part of it by trading `y0` for `x0`, which this column does not count, so the real loss lies between the two columns. We checked the rule on the generator's own choices for 40 n: the loss at the fitted f less the plain sum equals this slack in every row (0.00 to 0.04 for balanced choices, 0.15 to 0.64 for the others).

| arms | f | corner in the library | library far zones | with the new far zones | with the slack | held | board |
|---|---|---|---|---|---|---|---|
| 8 and 8 | 0.70 | 2.57 (class 2), 3.07 (class 5), 3.54 (class 4) | 8.11 to 9.24, classes 2 and 5 have none | 8.11 to 8.67, every class | 8.11 to 9.22 | 7.84 to 8.55 | 7.11 to 7.39 |
| 8 and 8 | 0.80 | 3.35 (class 3, found at f = 0.835) | 9.76 to 10.47, class 4 has none | 9.70 to 9.78, every class | 9.74 to 11.21 | 8.43 to 9.15 | 7.66 to 8.04 |
| 9 and 9 | 0.72 | 4.49 (class 3, found at f = 0.767) | 12.19 to 12.63, four classes have none | 11.09 to 11.78, every class | 11.43 to 13.04 | 9.41 to 10.91 | 8.98 to 9.85 |
| 9 and 9 | 0.76 | 3.89 (class 3) | 10.77 to 11.52, four classes have none | 10.20 to 11.28, every class | 10.60 to 12.35 | 9.89 to 10.73 | 9.61 to 9.85 |
| 9 and 9 | 0.80 | 4.40 (class 3, found at f = 0.767) | 11.37 to 12.37, four classes have none | 11.33 to 12.19, every class | 11.87 to 13.37 | 9.96 to 10.87 | 9.38 to 9.74 |
| 10 and 10 | 0.76 | 5.57 (class 9, found at f = 0.796) | 14.24, one class | 13.87 to 14.60, every class | 14.05 to 16.15 | 11.41 to 12.10 | 10.99 to 11.57 |
| 10 and 10 | 0.80 | 4.75 (class 9) | 12.73, one class | 12.73 to 13.66, every class | 12.73 to 15.72 | 11.22 to 12.38 | 10.43 to 11.29 |
| 7 and 7 | 0.82 | 2.83 (class 3), 2.72 (class 4, found at f = 0.844) | 7.30 and 7.40, two classes | 7.30 to 8.36, every class | 7.30 to 8.67 | 6.71 to 7.17 | 5.75 to 6.04 |
| 7 and 7 | 0.86 | 2.68 (class 4), 3.29 (class 3, found at f = 0.833) | 7.10 to 8.65, four classes | 7.10 to 8.16, every class | 7.19 to 9.06 | 6.87 to 7.19 | 6.25 to 6.52 |
| 7 and 7 | 0.68 | none | none | two far zones alone: 4.68 | | 5.78 to 6.12 | 4.77 to 5.21 |
| 7 and 7 | 0.75 | none | none | two far zones alone: 4.98 | | 6.28 to 6.65 | 5.80 to 6.00 |
| 6 and 6 | 0.68 | none | none | two far zones alone: 3.16 | | 2.86 to 3.41 | 1.94 to 2.77 |
| 6 and 6 | 0.75 | none | none | two far zones alone: 3.26 | | 3.60 to 4.02 | 3.20 to 3.53 |
| 11 and 11 | 0.72 to 0.80 | none, the library has no 11-arm | none | two far zones alone: 8.28 to 8.86 | | not measured | not measured |

What the table says:

- **Two 8-arms at f = 0.70.** The new zones give every class a layout at 8.11 to 8.67, or 8.11 to 9.22 with the slack. Held is at 7.84 to 8.55 and the board at 7.11 to 7.39. Our best class (8.11) is 0.2 above held in its own class and 0.7 above the board. Two far zones are 5.54 of the 8.11.
- **Two 8-arms at f = 0.80.** Only one corner reaches this f, and it was found at 0.835. With it the sum is 9.7 to 9.8, which is 0.6 to 1.3 above held. The far zones are 6.3 to 6.4 of it.
- **Two 9-arms.** The new class 1 lowers the sum by up to 0.9 at f = 0.72 and up to 0.5 at f = 0.76, and it opens the four classes that had no layout. The sum is still 0.2 to 1.0 above held at f = 0.76, and 0.5 to 2.1 above it at f = 0.72 and 0.80.
- **Two 10-arms.** Every class now has a layout, 1.1 to 2.8 above held.
- **Two 7-arms.** At f = 0.82 and 0.86 the library has two corners, and the new zones open the missing classes at 7.6 to 8.4. Held is at 6.7 to 7.2. Below f = 0.82 the library has no corner for two 7-arms. The far zones alone say what a corner may lose: at f = 0.75 it must lose 1.3 to 1.7 squares or less to tie held, and 0.8 to 1.0 to reach the board. The corners at f = 0.82 to 0.86 lose 2.68 to 3.29.
- **Two 6-arms.** No corner in the library below f = 0.82. At f = 0.68 the two far zones alone (3.16) lose more than the board's whole layout (1.94 to 2.77). So at that f the board's layouts are not two 6-arms with far zones of this kind.

### 10.4 Hops and sweeps

Eighteen runs of `search --moves resume,hop` finished, each from the taper zone of its count, with 145 to 236 CPU-seconds. The last two went to the zones that the near misses of section 10.6 use.

| arm | f | count | class | taper | after the search | move that gained |
|---|---|---|---|---|---|---|
| 8 | 0.70 | 17, 18, 20, 24, 27 | 1, 2, 4, 0, 3 | 2.77 to 3.36 | the same | none |
| 8 | 0.70 | 46 | 6 | 3.20 | 2.85 | flip and sweep |
| 8 | 0.70 | 54 | 6 | 3.07 | 2.85 | sweep |
| 8 | 0.75 | 46 | 6 | 2.93 | 2.82 | sweep |
| 8 | 0.80 | 30 | 6 | 3.22 | the same | none |
| 8 | 0.80 | 41 | 1 | 3.33 | 3.19 | sweep |
| 8 | 0.80 | 59 | 3 | 3.56 | 3.48 | flip and sweep |
| 9 | 0.76 | 36, 43 | 0, 7 | 3.50, 3.70 | the same | none |
| 9 | 0.80 | 43 | 7 | 3.46 | the same | none |
| 10 | 0.76 | 49 | 9 | 4.15 | the same | none |
| 10 | 0.80 | 39 | 9 | 4.00 | 0.002 less | sweep |
| 8 | 0.82 | 37 | 5 | 3.224 | 3.206 | sweep |
| 7 | 0.82 | 32 | 4 | 2.299 | 2.288 | sweep |

- **Short zones do not move.** No zone of 30 squares or fewer gained anything.
- **Long zones of an 8-arm gain 0.08 to 0.35.** All five zones of 41 squares or more did. The zones of 46 and 54 squares at f = 0.70 end at the same loss, 2.8516: the second is the first with one more period of the stack. That loss is the library's level for class 6 (2.84 to 2.90), not below it.
- **Zones of 32 and 37 squares gain a little.** The 8-arm zone of 37 squares and the 7-arm zone of 32 squares at f = 0.82 gain 0.018 and 0.011 squares, about 0.0002 and 0.0001 of side in a layout near n = 900. They are in the table and the zones dir as `z8-37f820b` and `z7-32f820b`.
- **Long zones of a 9-arm or a 10-arm do not gain.** Five zones of 36 to 49 squares moved by 0.002 or less.

So the taper enumeration is weak only on long zones of an 8-arm, and a 3-minute sweep repairs that. We do not know why the 9-arm and 10-arm zones do not gain.

### 10.5 What the slide is worth

Section 8 left this open. We measured it on the zone alone, in three ways.

- **The contact LP with a slot open.** The first column of the grid stands off by g above a slot, and the LP runs from the rigid zone with free angles (`zone_lowf.py slide`). We tried every height of the slot and g = 0.05, 0.10, 0.15 and 0.25 on 39 zones of arms of 6 to 10. 37 zones do not move at all. The two long ones gain 0.014 and 0.016 squares (the 8-arm zone of 54 squares at f = 0.70 and the 7-arm zone of 39 at f = 0.75).
- **A positive control.** The library has 30 far zones that were found with a slide, all at f of 0.915 and more, with g from 0.022 to 0.151. We ran the same LP on eight of them with their slide and with a rigid grid. Rigid, they lose 0.003 to 0.49 squares more (0.21 to 0.49 for five of the eight). So the measure can show a gain.
- **A taper designed for the slot.** A run that stands beside one column of uprights on the wall side is one square short on the grid side: with the column it needs `1 - cos t` more width than the strip has. With a slot between two cells of the grid's first column its last square can poke that far. The poke is 0.089 deep at f = 0.70 for an arm of 8, and the slot must be `(1 - cos t) / (sin t cos t)` = 0.237 tall or more. The slot starts on top of a whole cell, so most stack positions need a taller one. `zone_lowf.py poke` enumerates the tapers with one such run.

| arm | f | classes that gain with one poke, slot of any height | loss without and with the poke | slot |
|---|---|---|---|---|
| 8 | 0.70 | class 0 only | 3.057 and 3.031 | 0.97 |
| 8 | 0.80 | none | | |
| 9 | 0.76 | none | | |
| 7 | 0.75 | class 1 only | 2.83 and 2.72 | 0.31 |
| 6 | 0.75 | class 1 only | 2.45 and 2.00 | 0.42 |
| 7 | 0.99 (control) | class 5 | 2.760 and 2.723 | 0.23 |
| 6 | 0.96 (control) | class 4 | 2.155 and 1.758 | 1.10 |

The two controls are at f where library zones gain from their slide. The 7-arm zone of 26 squares at f = 0.99 comes out at a loss of 2.723, and the library's zone of 26 squares that pokes has 2.722 to 2.727 at f = 0.996 to 0.998. So the enumeration holds the library's design.

The derivation said a poke buys a whole square. The measurement says it buys nothing in most classes. The derivation was wrong: it compared the run that pokes with a run one square short. The enumeration is free to put the upright column on the grid side instead, where the run stays whole without a slot, and it already does.

The largest grant of any corner in the library is 0.151, and only 4 corners found below f = 0.86 grant more than 0.02. Every gain above needs a slot of 0.31 or more below f = 0.86. So with the corners we hold, the slide gives a far zone nothing at low f. With the slot capped at 0.30, no class of an 8-arm at f = 0.70 gains.

### 10.6 The generator with the new zones

After each batch the generator ran on every n from 300 with the new zones (`modules.py queue --need`, three choices per n). We built the choices near held with `modules.py job` (the contact LP, then the fq quench). `modules.py take` certified the builds against held and against every other take dir.

- **Batch 1: 107 zones at 16 pairs of arm and f, 85 of them new to the library.** The queue gave 103 choices on 40 n. Of 20 builds, 911, 921 and 974 came out below the round 10 file, and other takes held all three at the same side or lower.
- **Batch 2: 339 zones at 53 pairs, 300 of them new to the library.** 62 n have a choice within 0.004 of side above held. A second queue with six choices per n used only the zones of arms of 9, 10 and 11. We built every choice that the queue put within 0.0013 of side of the best take: 78 builds on 27 n in batches 1 and 2.
- **Batch 3: the two swept zones of section 10.4** (the 8-arm zone of 37 squares and the 7-arm zone of 32 squares at f = 0.82), joined into the library under their own ids. The queue on every n gave 64 choices on 16 n, 28 of them on 7 n within 0.0013 of side of held. We built 18. 803 and 862 end at the side of round 11 (2e-9 of side lower, a tie), 804 comes up from +5.6e-5 to +3.7e-7 of side and 984 from +2.5e-4 to +1.2e-4, and 923 stays at +3.9e-6. One build of 921 with the swept 7-arm zone in its other arm ends 6e-8 of side below the build of batch 2 and takes its place. Four more builds of choices nobody had built, predicted 0.0001 to 0.0006 of side above round 11 (922, 984, 912 and 981), end 5e-7 to 1.2e-4 above it.

Held is now the round 11 file. We certified every build again against it and against every take dir of rounds 7 to 12 as they stood at 01:20 UTC. Kept, floatsafe at 2.2e-11 and below held by more than 1e-10. The gains are in score, `side / sqrt(n) - 1`:

| n | built side | round 11 side | gain on round 11 | gain on round 10 | the new zone in the layout |
|---|---|---|---|---|---|
| 921 | 30.818761963 | 30.820446173 | 5.550e-05 | 8.242e-05 | 9-arm, 43 squares, class 7, made at f = 0.84, and the swept 7-arm zone of batch 3 |
| 983 | 31.816720806 | 31.816856499 | 4.328e-06 | 4.328e-06 | the same zone |
| 863 | 29.843684485 | 29.843702672 | 6.191e-07 | 2.054e-05 | 7-arm, 32 squares, class 4, made at f = 0.86, in both arms |
| 974 | 31.703437374 | 31.703437430 | 1.824e-09 | 1.176e-04 | 8-arm, 54 squares, class 6, made at f = 0.70, then swept |

The take has 4 n with a gain of 6.045e-05 on round 11. No other take holds these n lower, so the gain over the other takes is the same number. On round 10 the same four n had 2.247e-04; round 11 took the rest of it with the builds of the modules and family takes.

- **921 and 983 are the real result.** Both use the 9-arm zone of 43 squares of class 7, made at f = 0.84 with a loss of 3.40. The library already has a 43-square zone of that class (983h.F1, 3.41); the new one is 0.09 squares lower at the f of 921 (3.342 against 3.431). 921 ends 0.00168 of side below round 11.
- **863 is small.** Its far zones are the 7-arm zone of 32 squares made at f = 0.86. The library has the same design (2.21 against 2.22), cut at another f. The build ends 0.000018 of side lower.
- **974 is a tie in practice.** It ends 6e-8 of side below round 11, with the swept 8-arm zone of 54 squares in place of the library's zone of the same class.
- **Ties that are not kept.** 639, 740, 746, 797, 803, 862, 911, 912, 975, 985 and 987 end 1e-9 to 3e-9 of side below round 11 or the best take, which is under the line of 1e-10 of score.
- **Near misses above held:** 804 (+3.7e-7 of side, after batch 3), 922 (+5.3e-7), 861 (+2.5e-6), 923 (+3.9e-6), 691 (+2.1e-5), 981 (+2.7e-5), 924 (+9.5e-5), 984 (+1.2e-4), then 851, 920 and 913 at +0.0002 to +0.0006.
- **Nothing new below f = 0.80.** 911, 974, 740, 797, 975 and 912 end at the side that other takes reached with library zones. In that band the far zones here are at the library's level, so the corner decides.

### 10.7 What this means for the low band

- The far zone is searched out for this family. The lattice gives the library's level in the cheap class, every other class within a few rows of it, and neither hops nor a slot go below that level.
- Two flush arms with these zones lose 8.1 to 9.2 squares at f = 0.70. Held is at 7.8 to 8.6 and the board at 7.1 to 7.4, as two 8-arms. Many held layouts in this band are not two flush arms: 850 and 909 have a side of m + 4√2 − 5, which is a 45-degree design, and the generator's best layout for them is 0.04 to 0.09 of side above held.
- One square of loss is 0.0127 of side at n near 900 and f = 0.70 (the derivative of the flush count is 78.7 squares per unit of f). A far zone 0.1 squares better moves a layout by 0.0013 of side.

What to search next, in this order:

1. **The corner at low f.** It is the zone we know least: one design at f = 0.69 to 0.72 for two 8-arms (2.47 to 2.57), one corner for 7 and 8 (1.95), none for two 7-arms or two 6-arms below f = 0.82, none for an 11-arm. The far zones here say what a corner may lose (section 10.3), and a corner with a free trade of `y0` for `x0` removes the slack term, which is up to 1.4 squares in the classes that have it.
2. **Short zones of the classes the library has only long.** This gave the one win here. `zone_lowf.py three` lists the library's zone per class with its count, so the long ones are easy to find.
3. **Sweeps on every long 8-arm zone the generator picks.** A sweep took 0.08 to 0.35 off five zones in 3 CPU-minutes each.
4. **Layouts that are not two flush arms.** Below f = 0.72 the held file is mostly of another kind. The zone-loss model does not describe them, and a zone search cannot improve them.

Three traps met here:

- `zone_search.py merge` leaves out the cheapest class of every f, because at high f the library has it. Below f = 0.86 that class is often new. `zone_lowf.py pick` keeps it.
- A run script with `trap 'kill 0' EXIT` ends every script started from the same ssh command, because they share one process group. Start each run in its own ssh call.
- A zone of `zone_lowf.py poke` needs its slot and is not a rigid zone. `pick` skips it.

## 11. Corner zones (2026-11-12, round 11)

Result: the corner of two 7-arms has a new class at a loss below the library's. A corner of 73 squares (3 mod 7) at f = 0.8554 loses 2.60, and the library's corner of 74 squares (4 mod 7) loses 2.63. With it the generator builds 803, 862, 923 and 986 below round 11 and below every other take. Library corners settled again at the f of the n, or improved by hops, win 703, 758, 871, 924 and 932. The 9 n gain 5.836e-04 over round 11 and every other take. The take dir holds 13 n below round 11 (8.143e-04 on held); other takes hold the other four at the same side or lower. For two 8-arms at f = 0.93 the go line of 0.3 is not met: the nearest new class (4 mod 8) is 0.51 above the library's best.

### 11.1 The corner problem

The corner zone is where the two arms meet. Arm 1 runs up the left wall and arm 2 runs along the bottom. Each arm ends at a flush stack that slides along its strip. So the zone has two lengths: `y0`, where the first flush stack of arm 1 starts, and `x0` for arm 2. The grid side of each strip stays rigid.

The loss of a corner is `c1 cos(t1) y0 + c2 cos(t2) (x0 - W1) - count`. One more flush stack on an arm adds c squares and one pitch, and the loss stays the same. So a corner of two c-arms serves its count mod c, and each length mod the pitch.

The two lengths trade. A layout fixes the remainder of each wall, and a corner fits only if each length is at most that remainder. Slack costs `c cos(t)` squares per unit of length: 0.076 squares per 0.01 for an 8-arm at f = 0.93. One square is worth `1 / (8 cos t)` = 0.131 of summed length there. So the result for a count is a trade curve: for each cap on one length, the smallest other length.

### 11.2 The tool

[`zone_corner.py`](../zone_corner.py) imports the evaluator, the soft energy and the constants of `zone_search.py`, and the contact LP of `modules.py`. It does not change either file.

| command | what it does |
|---|---|
| `base` | cuts the corners of the library and carries each to one f, or keeps each at its own f (`--own`, with `--shift` to move f) |
| `control` | shakes a library corner and searches for its two lengths |
| `search` | from one corner: delete squares (beam), insert squares (pockets), then hops. It keeps for each count the states that no other state beats in both lengths |
| `sweep` | `search` over every corner of a base file |
| `adopt` | settles every corner of a base file with the free-angle LP and hops |
| `table` | writes the kept states as module files of kind `corner`, a picture each, and rows for the table |
| `merge`, `predict`, `build` | add the corners to a library of `modules.py`, run its generator on every n, and build a choice with the lane's LP and the `fq` quench |

Three pieces are new. The exact lengths come from a bisection on each stack. The LP moves both stacks at once with a cost on each, and a cap on one length gives one point of the trade curve. The hops are a shake, a flip of a tilt, a move of one square to a pocket, and a snap of angles to the flush tilt or to upright.

### 11.3 Control

The control takes the library corner of n = 757 at f = 0.93: 115 squares, `y0` 11.187658, `x0` 12.253739, loss 3.337. It moves every square by a random step, turns it by a random angle, and searches. It passes if both lengths return within 1e-4, or if the sum is smaller.

| shake (move, turn) | seed | end state (y0, x0) | sum minus library | verdict |
|---|---|---|---|---|
| 0.05, 3° | 3 | 11.187658, 12.253739 by squeeze and LP (+3.7e-11, -1.8e-11) | 0 | pass |
| 0.05, 3° | 3 | 11.163706, 12.264593 with every angle snapped first | -0.0131 | pass, shorter than the library |
| 0.1, 5° | 4 | 11.163706, 12.264593 | -0.0131 | pass, shorter than the library |
| 0.2, 10° | 1 | 11.238483, 12.205110 after 177 hops, 373 s | +0.0022 | fail |
| 0.2, 10° | 2 | 11.236627, 12.205110 at hop 233, stopped for the load on the box | +0.0003 | not passed |
| 0.2, 10° | 5 | no legal start after the shake | | fail |

The control passes for shakes up to 0.1 and 5°, and fails at 0.2 and 10°. The two strong runs end on the next state of the trade curve: `x0` is 0.0486 shorter, which is the pitch less 1, and `y0` is 0.05 longer. So the search finds the curve and misses the library's point on it by 0.0003 to 0.0022 of summed length, or 0.003 to 0.017 of a square.

The shorter state is a real gain on the library's corner. Three squares turn from 23.85° to the flush 17.52°, and five others turn by 2° to 8°. The loss falls from 3.337 to 3.237.

### 11.4 What the library holds

We cut the corner of every held and harvested layout and took whole stacks off each arm.

- Two 8-arms at f from 0.90 to 0.97 have three corners: 91 squares (3 mod 8) at lengths (10.15, 10.15), 98 squares (2 mod 8) at (10.12, 11.12), and 106 squares (2 mod 8) at (11.13, 11.13). The third is the first with one more stack on each arm and one square less. No other class exists in the library.
- Two 8-arms at f from 0.82 to 0.845 have one corner: 123 squares (3 mod 8).
- Two 7-arms at f from 0.83 to 0.87 have 60, 67 or 74 squares. All three are 4 mod 7.

### 11.5 Two 8-arms at f = 0.93

The library's best corners at this f lose 3.30 (138 squares) and 3.32 (122 squares) in class 2, and 3.34 (115 squares) in class 3. The go line is a new class at 3.60 or less. We searched from four library corners: 757 (115 squares), 872 (122), 702 (131) and 756 (138). Each run deleted up to 7 squares, inserted up to 3, and gave hops to every count.

| count | class | best loss | states on the trade curve (y0, x0) | found by |
|---|---|---|---|---|
| 115 | 3 | 3.237 | (11.1637, 12.2646) (11.1877, 12.2537) (11.2352, 12.2355) (11.3128, 12.1598) | hops on the library corner |
| 116 | 4 | 3.982 | (11.4012, 12.2938) (11.4033, 12.2537) (11.5253, 12.2439) (11.7125, 12.1565) | insert 1, hops |
| 117 | 5 | 4.609 | (11.4223, 12.4858) (11.4282, 12.4588) (11.7139, 12.1565) | delete 5 from 122, hops |
| 118 | 6 | 4.432 | (11.1796, 12.8413) (11.1856, 12.7927) (11.9276, 12.1705) | insert 3, hops |
| 119 | 7 | 5.161 | (12.0484, 12.1565) | delete 3 from 122, hops |
| 120 | 0 | 4.606 | (12.0500, 12.2695) (12.0555, 12.2474) (12.1067, 12.1565) | delete 2 from 122, hops |
| 121 | 1 | 3.893 | (12.1020, 12.1995) to (12.1033, 12.1981) | delete 1 from 122, hops |
| 122 | 2 | 3.316 | (12.1665, 12.2178) (12.1697, 12.1865) | the library corner |

The best loss of each class over all 34 counts from 108 to 141:

| class | 2 | 3 | 4 | 1 | 5 | 6 | 7 | 0 |
|---|---|---|---|---|---|---|---|---|
| best loss | 3.316 | 3.237 | 3.813 | 3.893 | 4.240 | 4.432 | 4.503 | 4.606 |
| count | 122 | 115 | 124 | 121 | 133 | 118 | 111 | 120 |
| above 3.30 | +0.01 | -0.07 | +0.51 | +0.59 | +0.94 | +1.13 | +1.20 | +1.30 |

- The go line is not met. Class 4 is 0.51 above the library's best, and class 1 is 0.59 above.
- Class 3 has a new best of 3.237, from the hops on the library corner (section 11.3).
- A new corner of 114 squares (2 mod 8) sits at (11.15648, 12.15648) with a loss of 3.357. Both stacks stand at the contact position 4.15648 of the far-zone taper of section 5, plus 7 and 8 rows.
- The summed length of counts 116 to 121 is 0.09 to 0.25 above the straight line between 115 and 122. That excess times `8 cos t` = 7.63 is the extra loss.
- The hops had 1,099 tries in 22 rounds over 18 counts, about 45 CPU-minutes in all. The kill line's 40 CPU-minutes per class were not spent.

The LP trade curve of the library corner of 115 squares runs from (11.1565, 12.2750) to (11.6482, 12.1565) in steps of 0.082 in `y0`: (11.2384, 12.2361), (11.3204, 12.2276), (11.4023, 12.2184), (11.4843, 12.2102), (11.5662, 12.2007). The hops found a state at (11.3128, 12.1598), which is 0.068 shorter in `x0` than the LP curve at that `y0`. So the LP curve of one contact structure is an upper bound, and the states are the curve.

### 11.6 Two 8-arms at f = 0.82 to 0.845

No library corner settles at f = 0.82: each one locks below its own f. We searched at f = 0.835 from the corner of n = 922.

The library's corners here lose 3.42 (n = 861 at f = 0.8238), 3.36 (n = 922 at f = 0.8347) and 3.29 (n = 985 at f = 0.8448) by the loss of section 11.1. We found no corner of two 8-arms at 2.36 in the library at any f. The lowest is 2.47, at f = 0.7065.

| count | class | best loss at f = 0.835 | states (y0, x0) |
|---|---|---|---|
| 123 | 3 | 3.344 | (12.3651, 12.3597) (12.3654, 12.3593) (12.3747, 12.3581) |
| 122 | 2 | 3.931 | (12.3027, 12.3668) (12.3141, 12.3640) (12.3209, 12.3636) (12.3507, 12.3604) |
| 121 | 1 | 4.561 | (12.3653, 12.3507) (12.3713, 12.2487) (12.3927, 12.2435) |
| 120 | 0 | 5.238 | (12.3654, 12.2115) |
| 119 | 7 | 5.015 | (12.3697, 12.1352) (12.4769, 11.9568) (12.4878, 11.9256) |
| 118 | 6 | 4.323 | (12.3654, 11.8219) (12.3735, 11.8186) |
| 117 | 5 | 4.931 | (12.3541, 11.7806) |
| 116 | 4 | 3.914 | (12.3636, 11.5016) |

The library's level exists for class 3 only, and at one pair of lengths: its states lie within 0.01 of each other. Every other class is 0.57 or more above it. Every other remainder of the wall pays the slack, 0.075 squares per 0.01 of length. The hops had 337 tries in 8 rounds. Insertion found no state.

### 11.7 Arms of 7, and of 7 and 8, at f = 0.85

| arms, f | count | loss | lengths (y0, x0) | found by |
|---|---|---|---|---|
| 7 and 7, 0.8554 | 74 (4 mod 7) | 2.633 | (9.3549, 9.3345) | the library corner of n = 924 |
| 7 and 7, 0.8554 | **73 (3 mod 7)** | **2.604** | (9.2512, 9.2794) and (9.3525, 9.2512) | delete 1, hops |
| 7 and 7, 0.8554 | 72 (2 mod 7) | 3.415 | (9.2502, 9.2512) | delete 2, hops |
| 7 and 7, 0.8554 | 71 (1 mod 7) | 3.249 | (9.2512, 9.0701) and (9.0701, 9.2512) | delete 3, hops |
| 7 and 7, 0.8554 | 70 (0 mod 7) | 3.678 | (9.0935, 9.1396) | delete 4 |
| 7 and 7, 0.8554 | 69 and 76 (6 mod 7) | 3.821, 3.838 | (9.0186, 9.0821), (9.8877, 9.2967) | delete 5, insert 2 |
| 7 and 7, 0.8554 | 75 and 68 (5 mod 7) | 3.846, 4.167 | (9.7800, 9.2512), (8.9002, 9.0995) | insert 1, delete 6 |
| 7 and 8, 0.8472 | 84 | 2.933 | (10.3651, 9.5066) | the library corner of n = 923 |
| 7 and 8, 0.8472 | 83 | 3.086 | (10.2643, 9.4805) | delete 1, hops |
| 7 and 8, 0.8472 | 80, 82, 81, 79, 78 | 3.432, 3.783, 3.796, 3.959, 4.376 | | delete 4, 2, 3, 5, 6 |

The go line is met for two 7-arms. The corner of 73 squares is a new class, and its loss is 0.03 below the library's corner at this f. One square less shortens the two lengths by 0.159 together, and the ideal exchange for a 7-arm at this f is 0.154. The corner of 83 squares for arms of 7 and 8 is 0.15 above its library corner.

### 11.8 One square less at each library corner

We ran the same step, delete 1 and hops, on 56 states of library corners at their own f (two thirds of the 88 distinct corners, 22 s each).

| corner of n | f | library count, loss | one square less | difference |
|---|---|---|---|---|
| 997 | 0.9730 | 115 (3 mod 8), 3.561 | 114 (2 mod 8), 3.394 | -0.17 |
| 934 | 0.9641 | 107 (3 mod 8), 3.470 | 106 (2 mod 8), 3.446 | -0.02 |
| 814 | 0.9444 | 107 (3 mod 8), 3.619 | 106 (2 mod 8), 3.743 | +0.12 |
| 996 | 0.9555 | 130 (2 mod 8), 3.365 | 129 (1 mod 8), 3.580 | +0.22 |
| 933 | 0.9498 | 146 (2 mod 8), 3.451 | 145 (1 mod 8), 3.682 | +0.23 |
| 936 | 0.9959 | 91 (0 mod 7), 3.170 | 90 (6 mod 7), 3.431 | +0.26 |
| 702 | 0.9228 | 131 (3 mod 8), 3.178 | 130 (2 mod 8), 3.477 | +0.30 |
| 995 | 0.9500 | 138 (2 mod 8), 3.383 | 137 (1 mod 8), 3.816 | +0.43 |
| 912 | 0.7033 | 133 (5 mod 8), 2.881 | 132 (4 mod 8), 3.397 | +0.52 |
| 755 | 0.9165 | 154 (2 mod 8), 3.390 | 153 (1 mod 8), 3.965 | +0.58 |

Class 1 mod 8 comes within 0.3 of the library's corner at f = 0.95 and 0.9555 (rows 996 and 933). At f = 0.93 it is 0.59 above (section 11.5). So the cost of a new class depends on f, as it does for the far zones.

### 11.9 The generator with the new corners

The generator ran on every n from 300 to 1,000 after each batch of corners. The bar of each n is the best of held and of every other take of the round. We built each choice near the bar that holds a new corner.

There were 53 builds on 36 n. Each build is the rigid cut of the prediction, assembled 0.0002 of side above it, then the contact LP of `modules.py` and the `fq` quench. `modules.py take` certified every build against round 11 (floatsafe at 2.2e-11, below held by more than 1e-10), and then against every take dir of rounds 7 to 12 as they stood at 01:25 UTC.

| n | corner in the layout | far zones | predicted side | built side | round 11 side | gain on round 11 |
|---|---|---|---|---|---|---|
| 923 | `zc7x7-73f8554a`: 73 squares, 3 mod 7, f = 0.8554 | 863h.F1, 924q1.F1 | 30.844437 | 30.842931513 | 30.847246896 | 1.420e-04 |
| 862 | the same | 984h.F1, 984h.F1 | 29.830978 | 29.829920509 | 29.833233101 | 1.128e-04 |
| 803 | the same | 803h.F1, 803h.F2 | 28.819328 | 28.817705482 | 28.820376052 | 9.424e-05 |
| 871 | `zc8x8-130f9389a`: the corner of 813, settled at f = 0.9389 with free angles | 504h.F2, 995z11.F2 | 29.932148 | 29.930903373 | 29.932818098 | 6.488e-05 |
| 986 | `zc7x7-73f8554a` | 863h.F1, 923h.F1 | 31.856138 | 31.854405072 | 31.856022191 | 5.150e-05 |
| 932 | `zc8x8-130f9389a` | 504h.F2, 995z11.F2 | 30.939950 | 30.939377899 | 30.940885411 | 4.938e-05 |
| 703 | `zc8x7-94f9356b`: the corner of 551, settled at f = 0.9356 with free angles | 933m10.F1, z7-31f930.F1 | 26.946654 | 26.946385268 | 26.947015852 | 2.378e-05 |

The 7 n gain 5.387e-04 on round 11, and the same over the other takes.

A third batch gave delete 1 and hops to 22 library corners at f from 0.687 to 0.896 that the first batches had not reached (20 s per count, 3 processes, 51 new states). One square less gives a new class below its library corner for arms of 7 and 9 (109 squares, 4 mod 7: 2.82 against 3.20 at f = 0.8345, and 2.81 against 2.95 at f = 0.8214) and for arms of 7 and 8 at f = 0.8593 (83 squares, 3.08 against 3.16). Every other class is 0.10 to 0.88 above its library corner. Hops at the library count lower the corner of 863 from 2.725 to 2.670. The generator with these corners, against round 11 and every take, put 6 new choices within 0.0006 of side of the bar. Two certify:

| n | corner in the layout | far zones | predicted side | built side | bar side | gain on round 11 | over the other takes |
|---|---|---|---|---|---|---|---|
| 758 | `zc7x7-78f9944b`: the corner of 760 settled at f = 0.9944, one length first | 462h10.F2, 704r10.F1 | 27.958964 | 27.957535634 | 27.958641418 | 4.016e-05 | 4.016e-05 |
| 924 | `zc7x7-60f8443a`: the corner of 863 after hops, loss 2.670 | 923h.F1, 863h.F1 | 30.855247 | 30.854918732 | 30.855251925 | 1.247e-05 | 4.768e-06 |

704, 746 and 987 end at the bar (2e-9 of side lower, a tie), and 811 ends 0.00034 above it. With these two, 9 n gain 5.836e-04 over round 11 and every other take.

- **The new class is the real result.** 803, 862, 923 and 986 hold the corner of 73 squares, which the library does not have. Together they gain 4.0e-04.
- **A corner settled at the f of the n gains too.** `modules.tabulate` carries a corner in f with fixed angles. 703, 871 and 932 use a library corner that the LP settled again at the f of the n, with free angles. Together they gain 1.4e-04.
- **Below held, but another take is lower.** 598, 649 and 702 are below round 11, and take-family-r12 holds them 3e-7 to 1e-4 of score lower. 634 ties take-zones-r11 to 7.5e-15 of score. These four are in the take dir too; the assembler keeps the lowest.
- **Won on round 10, not on round 11.** 601, 652, 740, 813, 870, 911, 931, 974 and 987 certified against round 10. Round 11 took them from the modules, family and border takes at the same side or lower.
- **Near misses above round 11:** 812 and 922 end 1e-6 of side above it, 974 1.1e-5 and 987 2.7e-5. Then 757 (+0.00006), 873 (+0.00009), 996 (+0.00012), 461 (+0.00023), 813 (+0.00044), 816 (+0.00046), 870 (+0.00064), 935 (+0.00066) and 931 (+0.00067).
- **Builds that ended far above their prediction:** 873, 875 and 936 end 0.0021 to 0.0023 of side above it. Their corners have one length pushed to its end, and the table promises pairs of lengths that the corner cannot reach (section 11.10).

### 11.10 Derivation and measurement

- **The exchange.** The derivation says one square is 0.131 of summed length for two 8-arms at f = 0.93. The measured states between 115 and 122 squares lie 0.09 to 0.25 above that line. Only the two ends, which the library has, lie on it. For two 7-arms at f = 0.8554 the derivation says 0.154 and the corner of 73 squares measures 0.159. There the contacts close again one square down, and the new class is free.
- **Arms of 9 and 8.** The flush capacity of a layout at m = 28 and f = 0.93 is 37.92 squares over the grid for two 8-arms, and 39.01 for arms of 9 and 8. The held layouts of 811, 870, 931 and 995 have arms of 9 and 8, and their corner counts are 7, 5, 5 and 0 mod 8. So a second arm size gives other classes at the same f. We did not search corners of 9 and 8.
- **The level of 2.36.** We expected a corner of two 8-arms at 2.36 near f = 0.82. The measured loss of that corner is 3.36. The two numbers differ by 1.00, so the 2.36 counts one square differently. The search uses 3.36.
- **The tables of the generator.** `modules.tabulate` carries a corner in f with fixed angles. A corner carried by 0.01 with free angles is up to 0.003 of side better for some n. But a state with one length pushed to its end has a table that promises pairs of lengths that it cannot reach: three choices with such a state had no start, and two builds ended 0.0007 and 0.0012 above the bar. Since 9c3d649, `modules.py` tabulates a corner only at the states it was found in, which removes these promises.

### 11.11 What the slide is worth

The corner search keeps the grid side of each strip rigid. We did not measure the slide on a corner alone. We measured it on whole layouts instead, in the builds of section 11.9. Each build starts from the rigid cut, 0.0002 of side above the prediction. The contact LP lets the rows and columns of the grid slide while every contact stays. Then the `fq` quench moves every square and may change contacts.

| step | side it takes off, over 53 builds | on the 4 builds with the corner of 73 squares |
|---|---|---|
| the contact LP | median 0.00018, up to 0.0013 | 0 to 0.00093 |
| the `fq` quench after the LP | median 0.00020, up to 0.0018 | 0.0011 to 0.0018 |
| both, from the start | median 0.00065, 0.00015 to 0.0025 | 0.0013 to 0.0019 |

One unit of side is 2L squares of loss. So both steps together are a median of 0.035 squares, and 0.135 at most (702). In the four layouts with the corner of 73 squares they are 0.075 to 0.123 squares, two to four times the 0.029 by which the rigid loss of that corner beats the library's corner. 986 is predicted 0.0001 of side above round 11 and wins only by these two steps. Most of it is the quench, which changes contacts, not the LP slide. This is the slide of the whole layout, not of the corner alone.

### 11.12 What to search next

1. **One square less, at every f.** Run delete 1 and hops on the last third of the library corners, and on each corner carried to the f of every n that could use it. It took 22 s to 5 minutes for each corner and gave the four wins.
2. **The corner by enumeration.** A corner is two lattices that share a staircase of uprights at the meeting of the arms. Enumerate the pairs of tapers of section 5 with the staircase as a third part, for every count. The states at 4.15648 plus whole rows (section 11.5) show that the far-zone contacts carry over.
3. **Arms of 9 and 8 at f = 0.93.** Search their corners and their 9-arm far zones. They hold the classes that two 8-arms lack.
4. **Hops under a cap.** Give the hops the remainder of the wall of one n as a cap on each length, and the count that this n needs. The search then works on the layouts that are near the bar.
5. **The strong control.** Make the hops return the library corner from a shake of 0.2 and 10°. The runs end 0.0003 to 0.0022 above it.
6. **Tables with caps.** Tabulate a corner with the capped LP, so that a state with one length at its end promises the pairs that it can reach. Since 9c3d649 the table holds only the found states, which is safe but gives up the points between them.

### 11.13 Summary of the corner search

- `zone_corner.py` searches the corner alone, with two sliding stacks and a trade curve per count. Its control passes for shakes up to 0.1 and 5 degrees. At 0.2 and 10 degrees it ends on the library's trade curve, 0.0003 to 0.0022 of summed length beside the library's point.
- Two 8-arms at f = 0.93: every class now has a corner, but the go line is not met. The nearest new class (4 mod 8) is 0.51 above the library's 3.30. Classes 5, 6, 7 and 0 are 0.94 to 1.30 above it.
- Two 8-arms at f = 0.835: only class 3 is at the library's level (3.34), at one pair of lengths. Every other class is 0.57 or more above it, and every other remainder of the wall pays 0.075 squares per 0.01 of length. The level of 2.36 that we expected there is 3.36 by the loss of section 11.1.
- Two 7-arms at f = 0.8554: a corner of 73 squares (3 mod 7) loses 2.60, 0.03 below the library's corner of 74 squares. It wins 803, 862, 923 and 986.
- 9 n certify below round 11 and below every other take, for a gain of 5.836e-04. The LP slide and the quench of the build add 0.075 to 0.123 squares in the layouts with the new corner.
- Next: one square less at every library corner and every f, corners of arms of 9 and 8 at f = 0.93, and tables that respect the caps.

## 12. Round 13 corners (2026-11-12)

Result: 3 n certify against round 12 and every other take dir: 984, 921 and 975, for 2.360e-04 on held. Over every other take the gain is 5.65e-05. It is smaller because the first 984 build reached the take dir at 05:05 UTC, and the polish lane took it from there. Both wins hold one 7 x 9 library corner (921m10.C) after hops at its own count, which lowered its loss from 2.902 to 2.477. The rebuilt corner table checks clean: 0 of 620 corners are illegal at their stored f, against 452 of 583 stored the old way. At low f the go line is not met: two 7-arms reach 3.40 against 2.2, and two 6-arms reach 1.35 against 1.26. The strong control still fails, and so does a new control B for corners on a 9-arm. The far-zone delete route on a 9-arm passes its control B with a new block move.

Held is now `gather/round12-2026-11-12a.csv` (22.1822910977, gate dir `gate/cand-round12-1112a`). "The bar" of an n is the smallest of its held side and its sides in the take dirs of rounds 7 to 13. `work/mkbar.py` computes it (24 n lowered by a take at 04:07 UTC). Work dir: `<scratch>/bounties-squares/take-corners-r13/work` on boxA, and `<scratch>/squares-corners` on boxC (removed at the end).

### 12.1 The corner table, rebuilt at each run's exact f

Commit f97bc88 fixed `cmd_table`. A corner module now keeps the exact f of its search run. Before, it kept that f rounded to four decimals. The corners already in the library and in `take-zones-r11/work/zones` were still stored the old way.

- We collected every search run file of the round 11 corner lane: `work/out`, `out-f2`, `out-final` and `out-boxD` of `take-zones-corner-r11`. 895 files hold 419 distinct runs (same bytes counted once).
- `zone_corner.py table runs-old zones table-r13.tsv --tag r` wrote 620 corner modules into `work/zones`. Their ids end in `r`, so no id of the old table is used again.
- `zone_corner.py check` is new. It tests every stored corner at its stored f, y0 and x0 with the exact evaluator. A corner is legal when no gap inside is below -2e-9 (the tolerance of `modules.legal`), both stacks clear it, and no square lies beyond a stack.

| zones dir | corners | illegal at the stored f | smallest gap |
|---|---|---|---|
| `take-corners-r13/work/zones` (rebuilt) | 620 | 0 | -1.26e-9 (contact) |
| `take-zones-r11/work/zones` (stored the old way) | 583 | 452 | -1.55e-4 |
| `zc7x7-73f8554a`, the corner of the four wins of round 11, old way | 1 | 1 | -3.83e-5 to both stacks |

The check fails on the old corners and passes on the rebuilt ones, so it can tell the two apart.

`zone_corner.py tables` and `merge --tables --drop-old` then built a library in the same dir. It starts from the round 12 library `take-modules-r12/work/libz3`, removes its 469 old zone-search corners and adds 471 rebuilt corners. Those are the 472 with a loss of 4.6 or less, without the one that has no table. The library has 1,647 modules, each with a table. The modules builder of this round loads it.

### 12.2 One square less on the rest of the library

The library of round 12 has 167 corners that the generator can use. The round 11 batches had given 47 of them a delete run, so 120 had none. `zone_corner.py base --own` settled 113 of the 120 at the f where they were found. The other 7 were not legal there or did not reach it. `sweep --down 1 --slot 12` (delete one square, then 12 s of hops on each count) ran on 104 of them before its deadline, on boxC (2 processes, 35 minutes).

- One square less is below its library corner for 11 of 104 corners. It is within 0.3 for 31. The median is 0.58 above.
- Hops at the library's own count lower 11 corners by more than 0.05 squares.

| corner | f | count | library loss | result | change |
|---|---|---|---|---|---|
| 984h10.C | 0.8361 | 110 (5 mod 7, arms 7 and 9) | 3.037 | 2.709 by hops | -0.328 |
| 921m10.C | 0.8204 | 110 (5 mod 7, arms 7 and 9) | 2.902 | 2.575 by hops | -0.328 |
| 462h10.C | 0.9532 | 71 | 2.165 | 1.931 by hops | -0.234 |
| 549f11.C | 0.8946 | 139 | 3.356 | 3.145 by hops | -0.211 |
| 814h10.C | 0.9448 | 107, then 106 (2 mod 8) | 3.700 | 3.457 one square less | -0.243 |
| 814h11.C | 0.9444 | 107, then 106 | 3.691 | 3.462 one square less | -0.228 |
| 984h10.C | 0.8361 | 110, then 109 (4 mod 7) | 3.037 | 2.856 one square less | -0.181 |
| 552h.C | 0.9401 | 68, then 67 | 3.648 | 3.470 one square less | -0.178 |
| 875h09.C | 0.9889 | 105, then 104 | 3.353 | 3.221 one square less | -0.132 |
| 934r10.C | 0.9641 | 107, then 106 | 3.555 | 3.430 one square less | -0.125 |
| 921h11.C | 0.8214 | 110, then 109 | 2.917 | 2.806 one square less | -0.111 |

The 921m10.C corner after hops keeps y0 (11.3056) and shortens x0 from 11.5671 to 11.5285. It is the corner of the 984 win (section 12.6).

`table --tag s` wrote 286 corners into `work/zones-s`. `check` finds 0 of 286 illegal at the stored f (smallest gap -3.7e-10). 273 of them (loss 4.6 or less) have a table and are in the library `zones-s/library.pkl`.

### 12.3 Hops under a cap

`zone_corner.py needs` runs the generator on every n from 300 with the rebuilt corners. For each choice within 0.0015 of side of the bar, it writes the two caps that the corner must meet at the bar's f less 1e-4. The caps are what arm 1 and arm 2 leave for the corner at that f. "Excess" is how far the corner's best state is over the caps. 285 choices on 72 n came back. Four (all on 601) fit already (excess -0.0004). The other choices are over their caps by 0.0006 or more.

Most of that excess is the margin of 1e-4 of f. A drop of 1e-4 in f shortens what an arm leaves for the corner by 0.0002 to 0.0007 of length. It shortens because every flush stack takes a little more wall at a lower f, and the far zones lengthen. At the bar's own f the excess of the 14 smallest choices is 0.0001 to 0.0006. These are the held layouts of those n, built from these same corners.

`capsearch` gives each (n, corner) pair the corner carried to the target f, three LPs under one or both caps, and then hops on the larger excess (`hops(caps=...)`). Over 24 pairs, at 30 to 45 s each on boxA (10 to 18 hops per pair), no corner fits its caps. The capped LPs take large excesses down to the level of the table (936r10.C at 875 from 0.034 to 0.0071, and 814h10.C from 0.031 to 0.0006). They do not go below it. A build gets 0.0002 to 0.0019 of side from the slide and the quench (section 11.11), which is more than these excesses. So builds of the choices near the bar are worth more than hops on one corner.

### 12.4 Low side fractions

Section 10.3 gives the budget: at f = 0.75, two 7-arms need a corner that loses 1.3 to 1.7 squares or less to tie held. Two 6-arms at f = 0.75 have two far zones of 3.26 against held at 3.60 to 4.02, so their corner must lose 0.76 or less. The go line is a loss within 0.5 of that budget.

With the LP, no library corner of two 7-arms or two 6-arms settles below f = 0.82. The corner locks. `base --soft` adds a soft step. Where the LP finds no state, the step turns the squares at an arm's tilt to the new tilt. Then the soft search pushes both stacks out and squeezes them back. Then `search --down 2 --up 1` ran with 3 to 4 minutes of hops from the best carried corner at each f.

| arms | f | carried corners (loss) | best found | count, class | go line |
|---|---|---|---|---|---|
| 7 and 7 | 0.78 | 804h.C 6.70 (803h, 862r10, 863h, 924h, 924q1 and 987r10 do not reach) | 3.607 | 72, 2 mod 7 | 2.2: not met |
| 7 and 7 | 0.74 | 804h.C 5.87 | 3.399 | 72, 2 mod 7 | 2.2: not met |
| 7 and 7 | 0.70 | 804h.C 5.19 | 3.577 | 72, 2 mod 7 | 2.2: not met |
| 6 and 6 | 0.80 | 340h.C 1.49, 418h.C 1.60, 338h.C 1.72 | 1.702 (61 squares), against 1.49 at the library count of 62 | 61, 1 mod 6 | |
| 6 and 6 | 0.75 | 418h.C 1.61, 340h.C 1.61, 338h.C 1.73 | 1.350 | 78, 0 mod 6 | 1.26: not met, 0.09 above |
| 6 and 6 | 0.70 | 418h.C 1.66, 340h.C 1.70, 338h.C 1.74 | 1.311 | 78, 0 mod 6 | |

- **Two 7-arms.** Only 804h.C reaches below f = 0.82, and its carried loss is 5.2 to 6.7. A free trade between its lengths and two squares less bring it to 3.4 to 3.6. That is about twice the budget. So a carried corner does not work for two 7-arms at low f, and the corner needs another design.
- **Two 6-arms.** The carried corners lose 1.5 to 1.7. One square more (78 squares, 0 mod 6) and hops give 1.35 at f = 0.75 and 1.31 at f = 0.70. That is 0.09 over the go line at f = 0.75.
- **The generator.** We ran it with these 13 low-f corners counted as new (`zones-l`), on the 142 n whose bar f is 0.66 to 0.84. No choice comes within 0.004 of side of the bar.
- **A trap.** `search` named its run files by corner, count and seed only. Runs of one corner at two f wrote the same file, so the states at f = 0.74, 0.75 and 0.78 were lost and only their logs remain. Since this round the file name holds the f.

**Arms of 9 and 8 at f = 0.93.** The held layouts of 811, 870, 931 and 995 use this pair. Carried to f = 0.93, their corners lose 4.14 (931h.C, 141 squares), 4.21 (870h.C and 811m10.C, 125 squares), 4.49 (995m10.C), 4.50 (995h.C) and 4.72 (811h.C). One square less at their own f (section 12.2) is 0.44 to 0.82 above each. A search from 931h.C at f = 0.93 (delete up to 3, insert 1, 4 minutes on boxA) gives 142 squares (6 mod 8) at 4.160. That is 0.02 above the library corner of 141 squares (5 mod 8). One, two and three squares less lose 4.64, 5.35 and 5.87. So arms of 9 and 8 have a second class at almost no cost, as the far-capacity argument of section 11.10 expected. This round changed the run file names to hold the f. A fault in that change wrote these four run files without their states. The f went into the name, and a comment swallowed the rest of the line. So only the log holds the numbers, and the generator did not see them. The fault is fixed in `zone_corner.py`. The searches on boxC ran the code before that change and are not affected.

**The 7 x 9 corner of 109 squares.** Round 11 found it at 2.82 (f = 0.8345). Here, one square less on four more 7 x 9 library corners gives 109 squares at 2.806 to 2.856. Hops at the library count of 110 give 2.575 on 921m10.C and 2.709 on 984h10.C, which is lower than any 109. The 110 is what the generator picks. It wins 984 (section 12.6).

### 12.5 Controls

**The strong control of the corner search.** Round 11 shook the library corner of 757 (115 squares, f = 0.93) by 0.2 and 10 degrees. The hops ended 0.0003 to 0.0022 of summed length beside the library's point, on what looked like the next state of its trade curve. This round adds a second phase to `control`: the library's two lengths become caps, three capped LPs run, and the hops then work on the larger excess (`hops(caps=...)`).

| run | end state (y0, x0) | against the library (11.187658, 12.253739) | loss | verdict |
|---|---|---|---|---|
| phase 1, hops on the sum, 65 hops | 11.238483, 12.205110 | +0.0508, -0.0486 | +0.017 | as in round 11 |
| phase 2, capped LP with x0 at most 12.253789 | 11.226773, 12.253789 | +0.0391, +0.00005 | +0.30 | |
| phase 2, 49 capped hops | no state closer | | | FAIL |

The repair does not pass. The capped LP shows the reason. With x0 held at the library's value, the shaken corner needs y0 0.039 longer. So the shaken corner is off the library's trade curve. It sits in another arrangement, whose best point is 0.017 squares above the library's. 114 hops do not cross to the library's arrangement. The control holds for shakes of up to 0.1 and 5 degrees (section 11.3) and not at 0.2 and 10 degrees.

**A control B for corners, and the delete route on a 9-arm.** `control --mode B` adds one flush stack to an arm of the library corner. Then the delete beam must take c squares out again. Like the far-zone beam of `zone_search.py`, the beam now breaks ties between equal LP sums by the deleted square's distance to a stack face, nearest first. The test is 995h.C (arms of 9 and 8, f = 0.93, 117 squares) with one stack more on the 9-arm (126 squares) and a beam of 4. The beam took the squares out of the 8-arm side. The corner ends with y0 1.11 longer and x0 1.12 shorter. The sum of the two lengths is 0.015 shorter, so the old pass rule (a smaller sum) called it a pass. The loss is 1.02 squares higher. With arms of two sizes, the sum is not the loss. The reason is that a unit of y0 holds c1 cos t1 squares and a unit of x0 holds c2 cos t2. The pass rule now compares the loss. Under it this control fails. So the delete route on a 9-arm corner has no working control yet. The one-square deletions of section 12.2 on 9-arm corners are measured states, but nothing shows that the route finds the best one.

**The far-zone delete route on a 9-arm.** Round 12's skeptic ran control B of `zone_search.py` on 983h.F1 (9-arm, 43 squares, f = 0.817) and it failed by 0.18. The round 12 library holds no 52-square zone of that class at this f. So B starts from the library zone with one more flush stack (52 squares, 6.532294, `--plus-stack`, beam 4).

| route | after 9 deletions | after hops | library | verdict |
|---|---|---|---|---|
| one square at a time, beam 4, with the peel line | 5.885973 | 5.712173 after 85 hops (2 minutes) | 5.471321 | FAIL, +0.24 |
| plus a block move: the 9 squares nearest the stack out at once, one compaction | 5.471321 | no hop needed | 5.471321 | PASS, -2.3e-11 |

One square at a time fails here even with the peel line. After each deletion the compaction moves the rest of the stack, so the next square nearest the stack is no longer one of the stack's own squares. `delete_beam` of `zone_search.py` now also tries the block move when it deletes c or more squares. With it the route passes this control. That is a control of one move. No control yet starts from a zone of another design, which is what the round 12 run did.

The corner hops have the fault of the old pass rule. They and their LP minimise y0 + x0. For a 7 x 9 or 9 x 8 corner, they should weigh the two lengths by c cos t, as the loss does.

### 12.6 The generator with the new corners, and the builds

`zone_corner.py predict --new zones-s` ran the generator of `modules.py` on every n from 300 with only the 273 corners of section 12.2 counted as new (three parts, boxA and boxC, about 12 minutes). 44 n have a choice within 0.002 of side of the bar. Three are predicted below it: 984 (-0.00354), 875 (-0.00042) and 601 (-0.00021). The 29 choices predicted below the bar plus 0.0009 went to `zone_corner.py build` (the rigid cut, the contact LP of `modules.py` and the `fq` quench). 25 of them were built before the deadline. Then the hops on the corner of 984 ran 5 more minutes (`zones-t`, 2.575 to 2.477), and 984 and 921 were built again with it.

`modules.py take` certified every build against `gate/cand-round12-1112a/details.csv`, floatsafe at 2.2e-11 and below held by more than 1e-10. It also certified them against every take dir of rounds 7 to 13 as they stood at 05:35 UTC.

| n | corner | far zones | predicted side | built side | held side | gain on held | over every other take |
|---|---|---|---|---|---|---|---|
| 984 | `zc7x9-110f8204at`: 921m10.C after hops, 110 squares, loss 2.477 | 862q1.F1, 921h.F2 | 31.830938 | 31.828580315 | 31.834478663 | 1.880e-04 | 8.550e-06 |
| 921 | the same | 862q1.F1, 983h.F1 | 30.819328 | 30.817308033 | 30.818761963 | 4.791e-05 | 4.791e-05 |
| 975 | `zc8x8-133f7209as`: 975m10.C after capped hops | 740h.F1, 975m10.F2 | 31.721134 | 31.720998669 | 31.721000186 | 4.853e-08 | 4.853e-08 |

- 984 is the main result. It holds the 7 x 9 corner of 921m10.C after hops: the same 110 squares with x0 0.050 shorter, and a loss of 2.477 in place of 2.902. The first build, with the corner at 2.575, ended 0.00563 of side below held (1.795e-04 of score). That file went into this take dir at 05:05 UTC. The polish lane of this round took it from there and holds it 9e-10 of score lower. The second build, with the corner at 2.477, is another 0.00027 of side lower and beats every other take by 8.6e-06.
- 921 uses the same corner, with 983h.F1 as the second far zone. It ends 0.00145 of side below held. The 921 of round 11 (the 9-arm far zone of section 10.6) was the held one.
- 505, 601, 652, 759, 911 and 997 tie: they end within 3e-9 of side of the bar. 601 was predicted 0.0002 below it.
- These end above the bar: 418 (+6e-6), 974 (+7e-6), 985 (+6.5e-5), 922 (+1.3e-4), 461 (+2.2e-4), 987 (+2.3e-4), 813 (+1.3e-4), 816 (+4.6e-4), 863 (+6.7e-4) and 875 (+1.0e-3, 0.0015 above its prediction).
- The second far zone matters little. 921 with 921h.F2 ends 1.2e-08 of side above the build with 983h.F1. 984 with 983h.F1 ends 9.1e-05 above the build with 921h.F2.
- 4 of the 29 choices got no build before the deadline: 804, 873, 338 and 551, each predicted within 0.0009 of the bar. The next round builds them first.

### 12.7 What to search next

1. **Hops on every corner of arms of two sizes, weighted by the loss.** The 984 and 921 wins come from 17 s and then 5 minutes of hops on one 7 x 9 corner. The hops and their LP minimise y0 + x0, which is not the loss when c1 and c2 differ. Weigh the two lengths by c1 cos t1 and c2 cos t2. Then give every 7 x 9, 9 x 7, 8 x 9, 9 x 8 and 7 x 8 corner several minutes of hops.
2. **Arms of 9 and 8 at f = 0.93, again.** The 142-square corner (6 mod 8) at 4.160 is 0.02 above the library's 141. Its states were lost (section 12.4). Run the search again and put it through the generator.
3. **The block move in the corner delete beam.** The far-zone beam passes control B on a 9-arm with it. The corner beam failed its control B on 995h.C, so add the same move there first.
4. **A control B from a zone of another design.** Neither delete route has one.
5. **Low f needs another corner design.** Carried library corners of two 7-arms lose 3.4 to 3.6 at f = 0.70 to 0.78, about twice the budget. The corner as two tapers that share a staircase (section 11.12, item 2) is the open route.
6. **Build more of the choices near the bar.** Four choices of section 12.6 (804, 873, 338 and 551) were not built before the deadline.

## 13. Round 14 corners (2026-11-12)

Result: Result: the corner of 600 after hops weighted by the loss wins 551, by 3.677e-05 over every other take (4.867e-05 on held), and wins 600 by 1.9e-06. Builds of round 13 choices that round 13 did not build win 551, 874 and 419. The polish lane read each build from our take dir within minutes, and it holds all four n lower with an fq polish of our build. Together they are 7.50e-05 below held: 551 at 5.790e-05, 874 at 1.006e-05, 600 at 3.760e-06 and 419 at 3.268e-06. So this take dir ends empty. Control B of the corner delete beam passes with the block move. A lower corner loss is often not a smaller layout: on 874 and 984 the weighted hops shortened the length that the layout does not need.

Held is now `gather/round13-2026-11-12a.csv` (22.1697213494, gate dir `gate/cand-round13-1112a`). The bar of an n is the smallest of its held side and its sides in every take dir. `work/mkbar.py` computes it (24 n lowered by a take at 06:27 UTC). Work dir: `<scratch>/bounties-squares/take-corners-r14/work` on boxA, and `<scratch>/squares-corners` on boxC (removed at the end).

### 13.1 The hops weigh the two lengths as the loss does

The loss of a corner is `c1 cos t1 y0 + c2 cos t2 (x0 - W1) - count`. Until this round the hops, their LP, the delete ranking and the order of the kept states all used `y0 + x0`. For arms of two sizes that sum is not the loss. Now all four use `w1 y0 + w2 x0`. The weights are proportional to `c1 cos t1` and `c2 cos t2`, and they sum to 2 (`zone_corner.weights`). For arms of one size both weights are 1, so nothing changes there.

| arms | f | w1 | w2 |
|---|---|---|---|
| 7 and 9 | 0.8204 | 0.861 | 1.139 |
| 8 and 9 | 0.93 | 0.937 | 1.063 |
| 8 and 6 | 0.93 | 1.158 | 0.842 |
| 5 and 8 | 0.915 | 0.740 | 1.260 |

Four smaller changes came with it:

- `table` puts the state of lowest loss first.
- `table --over DIRS` keeps only the states at least 1e-3 below every stored corner of the same arms, f and count.
- `zbase` turns stored zone-search corners into start states, and `sweep --mixed --resume` runs only the corners of arms of two sizes, from the kept states of earlier runs.
- `search --caps DY,DX` runs the hops under the caps `y0 - DY` and `x0 - DX` of the start corner.

### 13.2 Hops weighted by the loss on every corner of arms of two sizes

The library has 47 corners of arms of two sizes that settle at their own f (`baseown-r13.pkl` of round 13). With the 2.477 corner of the 984 win, that makes 48. The 5 corners of the near-bar choices of round 13 ran first. The 7 x 9 and the 9 x 8 corners came next, then the rest by loss. Each corner got 150 s of weighted hops from its best kept state of round 13, on boxC (2 processes, 06:31 to 07:15 UTC).

29 of the 48 corners ran before the deadline. 6 of them fell by more than 0.005 squares:

| corner | arms | f | count | loss before | loss after | change in (y0, x0) |
|---|---|---|---|---|---|---|
| 921m10.C (state of round 13) | 7 and 9 | 0.8204 | 110 | 2.5749 | 2.4863 | (0, -0.0104) |
| 600f11.C | 8 and 7 | 0.9334 | 80 | 3.3448 | 3.2841 | (-0.0118, +0.0044) |
| 874h.C | 8 and 7 | 0.9729 | 123 | 3.8311 | 3.7973 | (-0.0289, +0.0283) |
| 995m10.C | 9 and 8 | 0.9513 | 125 | 4.0904 | 4.0610 | (+0.0009, -0.0048) |
| 995h.C | 9 and 8 | 0.9514 | 117 | 4.0721 | 4.0526 | (+0.0005, -0.0030) |
| 705h10.C | 7 and 6 | 0.9773 | 100 | 2.9478 | 2.9426 | (+0.0126, -0.0158) |

The other 23 moved by less than 0.005, and 17 of those did not move at all in 40 to 80 hops. The 19 corners that did not run are the 8 x 7, 8 x 6 and 11 x 8 corners of highest loss.

Then the corner of the 984 and 921 wins (`zc7x9-110f8204at`, 110 squares, loss 2.477) got 14 minutes of weighted hops with seed 15, and 10 minutes with seed 16. Seed 15 found a state with the same y0 and x0 0.0064 shorter, at loss 2.4227 (`zc7x9-110f8204au2`). Seed 16 found nothing.

**A lower loss is not a smaller layout.** The generator puts a corner into a layout only if each length fits the remainder of its own wall. The new states mostly trade one length for the other:

- 984 and 921 with `zc7x9-110f8204au2` predict the same side as with the 2.477 corner (31.830938 and 30.819328). In both layouts the wall of arm 1 binds, and y0 did not change. The builds end 7.2e-5 and 4.2e-5 of side above held. Held holds the builds of round 13 with the 2.477 corner, after the polish lane.
- 874 with the new 874h.C state (3.797) has no choice within 0.002 of the bar. The state is 0.028 longer in x0, and the wall of arm 2 cannot take it. The round 13 state (3.831, the shorter x0) still gives the choice that wins 874 (section 13.5).

So the hops should run under the caps of the layout that would use the corner. `search --caps 0.01,-0.0064` ran from `zc7x9-110f8204au2` for 16 minutes: the hops try to shorten y0 by 0.01, with x0 allowed back up to the value of the 2.477 corner. In 340 capped hops, y0 came down by 0.0004 to 11.305150, with x0 at 11.512261 (loss 2.4348). The run file keeps the 10 states of lowest loss, so the table holds the states next to it. With the state at y0 11.305228 and x0 11.511844 (`zc7x9-110f8204bu3`), 984 predicts 7.5e-5 of side lower than before. The builds end 4.6e-5 (984) and 2.5e-4 (921) of side above held.

### 13.3 The block move in the corner delete beam, and control B

`delete_beam` of `zone_corner.py` now has the block move of `zone_search.py`. When the beam deletes c or more squares, it also takes the c squares nearest the face of that arm's stack out at once. One compaction follows, and the state joins level c of the beam.

Control B is the test of round 13 again. It takes 995h.C at f = 0.93 (arms of 9 and 8, 117 squares, loss 4.503) and adds one flush stack to the 9-arm (126 squares). Then a beam of 4 deletes 9 squares.

| route | end state (y0, x0) | against the library (11.192804, 12.156480) | verdict |
|---|---|---|---|
| round 13, one square at a time | y0 1.11 longer, x0 1.12 shorter | loss +1.02 | FAIL |
| round 14, with the block move | 11.192804, 12.156480 | -2.3e-11 and -2.3e-11 | PASS (100 s, no hop) |

The block of 9 at stack 1 returns the two lengths of the library in one step. The beam keeps it, because its loss is the lowest at level 9. This is a control of one move, as for the far zones. No control B starts from a corner of another design yet.

### 13.4 Arms of 9 and 8 at f = 0.93, again

Round 13 lost these states (section 12.4). The run files now hold the f in their names. Two searches ran on boxC with the weighted hops and seed 14.

| start | count | class | loss | found by | against the library corner at this f |
|---|---|---|---|---|---|
| 995h.C, 117 squares, loss 4.503 | 118 | 1 mod 9 | 4.457 | insert 1, then 11 hops | -0.046 |
| | 116 | 8 mod 9 | 4.680 | delete 1, then 68 hops | +0.18 |
| | 115 | 7 mod 9 | 5.854 | delete 2 | +1.35 |
| 931h.C, 141 squares, loss 4.137 | 142 | 6 mod 8 | 4.474 | insert 1 (44 hops found nothing) | +0.34 |
| | 140 | 4 mod 8 | 4.599 | delete 1, then hops | +0.46 |
| | 139, 138 | 3, 2 mod 8 | 4.740, 5.713 | delete 2, 3 | +0.60, +1.58 |

- **995h.C: 118 squares is a new class below the library.** One square more than the library's corner loses 0.046 less at f = 0.93. It is in `zones-u1`. The generator with it gives no choice within 0.002 of the bar on any n.
- **931h.C: the 142 of round 13 did not come back.** Round 13 reached 4.160 with seed 13 after 43 hops. This run, with seed 14, ended at the insertion's 4.474. So that result depends on the seed. The 142 at 4.160 is still lost.

### 13.5 The builds

Every build is the rigid cut of the prediction, the contact LP of `modules.py` and the `fq` quench (`zone_corner.py build`, one process on boxA). `modules.py take` certified every build against `gate/cand-round13-1112a/details.csv` (floatsafe at 2.2e-11, below held by more than 1e-10) and against every other take dir.

**The four choices that round 13 did not build.** They come from the library `zones-s` of round 13.

| n | corner | built side | held side | result |
|---|---|---|---|---|
| 551 | `zc8x7-94f9256as`: 551f11.C after hops | 23.924775862 | 23.925055163 | -0.000279 of side, below held |
| 338 | `zc6x6-77f9200as` | 18.877694491 | 18.877615341 | +0.000079 |
| 873 | `zc8x8-99f9570as` | 29.957330298 | 29.957067167 | +0.000263 |
| 804 | `zc7x7-74f8436cs` | 28.830382109 | 28.829715540 | +0.000667 |

**The other choices of round 13 near the new bar.** Round 13 predicted 11 more n within 0.0015 of side of today's bar and did not build them. 551 and these were built with up to two choices each.

| n | corner | built side | held side | result |
|---|---|---|---|---|
| 874 | `zc8x7-123f9729as`: 874h.C after hops | 29.972225418 | 29.972469570 | -0.000244 of side, below held |
| 419 | `zc6x6-90f9347as`: 419h.C after capped hops | 20.934768209 | 20.934834819 | -0.000067 of side, below held |
| 912 | `zc8x8-133f7031as` | 30.703186688 | 30.703185815 | +1.1e-6 |
| 924 | `zc7x7-60f8443as` | 30.854919003 | 30.854915038 | +4.0e-6 |
| 757 | `zc8x8-107f9319bs` | 27.931926012 | 27.931788175 | +0.000138 |
| 552 | `zc8x7-68f9607as` | 23.940134514 | 23.939867893 | +0.000267 |
| 998 | `zc7x7-118f9858bs` | 31.986207144 | 31.985812147 | +0.000395 |
| 600 | `zc8x7-59f9348as` | 24.934071255 | 24.933016935 | +0.001054 |
| 814 | `zc8x8-107f9443as` | 28.945557857 | 28.944429709 | +0.001128 |
| 549, 933 | | no start within 0.0015 of the bar | | |

551, 874 and 419 certified against round 13 and every take dir: 1.050e-05, 8.259e-06 and 3.254e-06 of score. Each went into the take dir at once. The polish lane reads that dir. Within minutes it held each one lower with an fq polish of our build: 551 at 1.190e-05, 874 at 1.006e-05 and 419 at 3.268e-06 below held. So these three n are in `take-polish-r14`, which names our corner build as the source. Our later builds of 551 then end 1.6e-11 of score below the polish lane's, which is not below it by 1e-10.

**The new corners.** The generator of `modules.py` ran with the corners of section 13.2 counted as new. It ran on the round 13 corner library (`lib-t`). It ran only on the n whose bar f lies within 0.06 of a new corner's f (241 n, `ns-u2.txt`). On the modules lane's newest library (`lib14b`, 7,966 modules) the same run takes more than 11 minutes. The generator works out the far-zone options of every corner before it tests whether the corner is new. So we stopped it there and built the choices of the smaller library in both.

| n | corner | far zones | predicted side | built side | held side | gain on held | over every other take |
|---|---|---|---|---|---|---|---|
| 551 | `zc8x7-80f9334au2`: 600f11.C after weighted hops, 80 squares, loss 3.284 | 993h.F2, 924h.F2 | 23.925779 | 23.923912824 | 23.925055163 | 4.867e-05 | 3.677e-05 |
| 600 | `zc8x7-80f9334du2`: the same run, state 4 of its curve | 504h.F2, 600f11.F2 | 24.933629 | 24.932970595 | 24.933016935 | 1.892e-06 | 1.892e-06 |

- **551 is the main result.** Its corner comes from the layout of 600, after 150 s of weighted hops. There y0 is 0.0118 shorter and x0 0.0044 longer, and the loss falls from 3.345 to 3.284. The prediction is the same as for the round 13 corner of 551 (23.925779): the far zone of arm 1 sets it in both. The build ends 0.00086 of side below the best build with the round 13 corner, and the same below the polish lane's 551.
- 703 has a choice 0.0012 above the bar, with a start too far above it to build.
- The polish lane took 551 and 600 from the take dir within minutes. It holds them at 5.790e-05 and 3.760e-06 below held, with our builds as start and source.
- The same choices built on `lib-u2-14b` end at the same sides. The far zones of the round 13 donors give 551 and 600 nothing new.

### 13.6 What to search next

1. **Hops under the caps of each near-bar choice.** Run `search --caps` on the length that binds in the layout, for every corner of a choice within 0.0015 of the bar. The weighted loss alone moved the wrong length for 874 and for 984.
2. **Build every near-bar choice, with more than one choice each.** The 551 win was predicted 0.0007 above the bar, like the round 13 choice. Its build took 0.0019 off. The 874 and 419 wins were choices of round 13 that it did not build.
3. **The rest of the sweep.** 19 corners of arms of two sizes got no weighted hops. The 142 of 931h.C at f = 0.93 (4.160 in round 13) needs more seeds.
4. **The generator on the newest library.** Make it test whether a corner is new before it works out the corner's options. Then a run on `lib14b` takes minutes, and the far zones of the round 13 donors meet the new corners.
5. **Low f needs another corner design.** The corner as two tapers that share a staircase (section 11.12, item 2) was not started this round.
6. **A control B from a corner of another design.** The block move passes the control of one move only.

## 14. Round 15 corners (2026-11-12)

Result: 983 certifies against round 14 and every other take dir, by 1.260e-05 of score (3.95e-4 of side). Its corner comes from hops under the caps of 983. They took a 9 x 7 corner of 146 squares 0.0021 under both caps in 4 hops. It is the only one of 28 capped pairs that fits its caps. The fq quench of the polish lane needs the certified file as its start. On the raw build of 551 of round 14 it found nothing. On the certified file it found the polish lane's 2.169e-4 of side. Builds of the other near-bar choices tie held or end above it. The same quench on earlier corner builds certifies 921, 984 and 974. It took the round 14 build of 921 with the capped 7 x 9 corner from 2.65e-4 above the bar to 8.2e-4 under it. In all 4 n certify, for 4.500e-05 on held and 4.499e-05 over every other take at 10:42 UTC: 921 (2.745e-05), 983 (1.260e-05), 984 (4.889e-06) and 974 (6.8e-08).

Held is now `gather/round14-2026-11-12a.csv` (22.1686761690, gate dir `gate/cand-round14-1112a`). The bar of an n is the smallest of its held side and its sides in every take dir. `work/mkbar.py` computes it (58 n lowered by a take at 10:08 UTC). Work dir: `<scratch>/bounties-squares/take-corners-r15/work` on boxA, and `<scratch>/squares-corners` on boxC (removed at the end).

### 14.1 The generator keeps only the corners a choice must hold

`predict`, `needs` and `build` pass a set of module ids to `Library.best` of `modules.py`. A choice counts only if it holds one of them. Until this round the generator worked out the far-zone options of every corner first and tested the set after. When the set holds corners only, `_need` now keeps only those corners in the library. A `predict` with the 3 corners of one zones dir on every n from 300 to 1000 takes 7 s on the library of round 15. A `predict` with 54 new corners takes 2.6 minutes. A `needs` run with all 4,274 zone-search corners on 62 n takes 15 minutes.

The library of this round is `lib15`: the modules lane's `libd` of round 14 (it already holds `zones-u2`) plus `zones-u1` and `zones-u3`.

### 14.2 The quench starts from the certified file

`build --quench D` runs the quench of `engine_polish.py` on a build that ends less than D above the bar. That is fq with its default flags, then the polish flags, up to 3 passes, each win certified by floatsafe. `zone_corner.py quench RAWDIR` does the same on builds already made.

The control is the build of 551 of round 14 (`raw-u2-f/551-1.csv`). The polish lane took it from 23.923912825 to 23.923695940.

| start of the quench | default fq | polish fq | result |
|---|---|---|---|
| the raw build | 23.923912934 (1.1e-7 higher) | 23.923912824 | no certified gain |
| the same file after `floatsafe.work` | 23.923736948 | 23.923732679, then 23.923695939 in pass 2 | 23.923695940, as the polish lane (61 s) |

So the quench starts from the certified file now. The raw build has its contacts at a gap of 0, and fq does not move from there. The certified file has its gaps opened by floatsafe, and fq moves. The builds of rounds 11 to 14 ran fq on the raw state (`modules._squeeze`). The build of 551 kept 2.2e-4 of side that way, and section 14.6 finds more.

### 14.3 The near-bar choices

`needs` ran on the 62 n that any corner prediction of rounds 11 to 14 put within 0.003 of today's bar. 40 n have a choice within 0.0015 of the bar (240 choices). The builds took the n in order of score-weighted excess, two choices each (`build --top 2`).

| n | corner | predicted minus bar | built minus bar |
|---|---|---|---|
| 601 | `zc8x7-68f9708ar` | -0.000208 | -1e-9 (the held packing) |
| 634 | `zc7x8-86f7096ar` | +0.000003 | -2e-9 (the held packing) |
| 505 | `zc8x7-68f9708ar` | +0.000020 | -1e-9 (the held packing) |
| 652 | `zc8x7-68f9708ar` | +0.000098 | +9.7e-6, the quench finds nothing |
| 816 | `zc7x7-112f9809ar` | +0.000152 | +0.000455 |
| 338 | `zc6x6-77f8876ar` | +0.000124 | -1e-9 (the held packing) |
| 912 | `zc8x8-133f7033cr` | +0.000208 | +4.1e-7 after a quench of 8.8e-7 |

The corners of this round (section 14.4) gave five more builds, one choice each:

| n | corner | predicted minus bar | built minus bar |
|---|---|---|---|
| 975 | `zc8x8-133f7210bv` | +0.000142 | +9.6e-7 |
| 797 | `zc8x8-98f7281bv` | +0.000218 | -1e-9 (the held packing) |
| 740 | `zc8x8-98f7064av` | +0.000226 | +2.6e-8 |
| 996 | `zc8x8-130f9551bv` | +0.000212 | +0.000109 |
| 974 | `zc8x8-98f7034av` | +0.000280 | +0.000039 |

One n takes 3 to 16 minutes for two choices on one process, most of it in fq. So 7 of the 40 n got builds before the capped corners took the slot. Most builds end on the held packing to 2e-9. The held layouts of these n came from these same corners.

### 14.4 Hops under the caps of each near-bar choice

`capsearch` ran on the choices of section 14.3 with an excess over their caps of up to 0.02. It carries the corner to the bar's f less 2e-5, runs three capped LPs and then 90 s of hops on the larger excess. 28 pairs ran before the deadline (boxC, one process, 45 minutes).

- **983 fits.** `zc9x7-146f8169br.C` (arms of 9 and 7, 146 squares) starts 0.00124 over its caps at f = 0.8167. One `snapall` hop and three more take it to 0.00207 under both caps. Its loss is 3.775. `build` with this corner gives 31.816325832, against a bar of 31.816720789. The fq quench of `build` ran into the 600 s timeout of `engine_fq.py`. `modules.py take` certifies the build: 1.260e-05 of score below held and below every other take dir.
- **The carried corner is often far from its table.** On 704, 757, 797, 816 and 975 the carried state starts 0.005 to 0.042 over its caps. The hops bring it back to 0.0001 to 0.0032, the level the table already promised.
- **The other 22 pairs move by less than 1e-5.** Their excess stays at 0.0001 to 0.0041, as in round 13.

`predict` with the 54 corners of this round (`zones-v`: the capped hops, the sweep of section 14.5 and the 931h.C states) puts no n other than 983 below the bar. The nearest are 601 (-0.0002, which builds the held packing), 505 (+2e-5), 652 (+1e-4), 975 (+1.4e-4) and 912, 996, 797 and 740 (+2.1e-4 to +2.3e-4).

### 14.5 The rest of the sweep, and 931h.C at 142

The 19 corners of arms of two sizes that round 14 did not reach got 150 s of weighted hops each (boxC, one process). Six fell by more than 0.005 squares:

| corner | count | loss before | loss after | change in (y0, x0) |
|---|---|---|---|---|
| 935h09c.C | 102 | 3.4502 | 3.3590 | (+0.0377, -0.0445) |
| 862m10.C | 84 | 3.5230 | 3.4373 | (-0.0161, +0.0054) |
| 651h.C | 66 | 3.4201 | 3.3454 | (-0.0098, 0) |
| 758h.C | 109 | 3.7770 | 3.7447 | (-0.0095, +0.0061) |
| 747h11.C | 102 | 3.9164 | 3.9030 | (-0.0042, +0.0050) |
| 862h09c.C | 84 | 3.5230 | 3.5100 | (0, -0.0020) |

The other 13 moved by less than 0.004, and 10 of them did not move.

931h.C at f = 0.93 with one square inserted (142 squares, 6 mod 8) got four more seeds of 3.3 minutes each, each one resuming from the states before. The loss went from 4.474 to 4.457 (seed 23) and then to 4.426 (seed 24). The 4.160 of round 13 did not come back. The library corner of 141 squares is at 4.137.

### 14.6 The quench of earlier near misses

The corner builds of rounds 11 to 14 that ended above the bar never reached a take dir, so no lane quenched them. We ran the quench of section 14.2 on them in three groups. boxA took the 20 builds that ended 1e-8 to 1e-5 above the bar, and quenched 2 of them before the slot went to 983. boxC took the 39 builds 1e-5 to 3e-4 above the bar, then the 39 builds 3e-4 to 1.5e-3 above it (two processes). `qmap.tsv` in the work dir names the build behind each copy.

| n | earlier build | above the bar before | quench | result |
|---|---|---|---|---|
| 921 | `take-corners-r14/work/raw-u3/921-1.csv` (the capped 7 x 9 corner `zc7x9-110f8204bu3`) | +2.65e-4 | -1.098e-3 in 66 s | 2.745e-05 of score below held |
| 984 | `take-corners-r14/work/raw-u3/984-1.csv` (the same corner) | +1.23e-4 | -2.763e-4 in 343 s | 4.889e-06 below held |
| 974 | `take-zones-lowf-r11/work/raw2/974-2a.csv` (a low-f build of round 11) | +2.4e-5 | -2.6e-5 in 138 s | 6.8e-08 below held |
| 551 | several builds of rounds 13 and 14 | +5.1e-4 and more | up to -3.5e-4 | still above the bar |
| 461 | two builds of rounds 11 and 13 | +2.2e-4 | -1.5e-4 | still above the bar |
| 600 | `take-corners-r14/work/raw-u2-f/600-3.csv` | +4.6e-5 | -4.6e-5 | ties the bar, which is the polish lane's 600 |
| 419 | `take-corners-r14/work/raw-r13c/419-2.csv` | +2.9e-7 | -2.9e-7 | ties the bar to 1e-9 |

Most of the other builds gain nothing in 3 to 130 s. The third group ran for 5 minutes before the deadline and reached 6 builds, none below the bar. The two large drops (921 and 984) are builds with the capped corner of round 14. So a build that ends up to 1.5e-3 above the bar is worth the quench before it is dropped.

### 14.7 What to search next

1. **Capped hops on every near-bar choice, with more time.** One of 28 pairs fit, and it was the one with a `snapall` hop. It found that state in 4 hops. Give each pair several minutes, and start from the corner's own states as well as from the carried one.
2. **Quench every build from its certified file.** The builds of the modules lane ran fq on the raw state too.
3. **The rest of the near-bar builds.** 33 of the 40 n of section 14.3 got no build. Large n take up to 16 minutes each, so run them on more processes.
4. **The new public layouts of 09:02 UTC as corner donors.** Their corners have not been cut or hopped.
5. **Low f needs another corner design.** The corner as two tapers that share a staircase (section 11.12, item 2) was not started this round.
6. **A control B from a corner of another design.** Not run this round.

## 15. Round 16 corners (2026-11-12)

Result: 3 n certify against round 15 and every live take dir, for 7.495e-05 of score: 600 (3.077e-05), 703 (2.292e-05) and 932 (2.125e-05). All three are builds with corners of the new layouts of round 15, after 50 s of hops at their own f. 600h15.C wins 600, 651h15.C wins 703 and 872h15.C wins 932. Each build ends 6e-4 to 7.5e-4 of side under the bar and 8e-4 to 1.2e-3 under its own prediction. The near-bar builds of round 15's list certify 863 (5.219e-06) and 974 (5.1e-09), and the polish lane took both further, so those rows are theirs. The quench of 104 older builds and 10 more capped pairs find nothing below the bar.

Held is now `gather/round15-2026-11-12a.csv` (22.1672602051, gate dir `gate/cand-round15-1112a`). The bar of an n is the smallest of its held side and its sides in every take dir (`work/mkbar.py`). Work dir: `<scratch>/bounties-squares/take-corners-r16/work` on boxA, and `<scratch>/squares-corners` on boxC and boxD (removed at the end). `work/certloop.sh` copied the remote results back every 8 minutes and certified every file under the bar, so `take.tsv` stayed current through the round.

### 15.1 Two changes to `zone_corner.py`

- **The quench gives fq more time near n = 1000.** fq had a fixed timeout of 600 s, and the quench of 983 in round 15 ran into it. `quench` now passes 600 s below n = 700, 1000 s from 700 and 1800 s from 900 (`ZC_FQ_TIMEOUT` sets one value for all). Quenches of n near 1000 took 500 to 1,130 s this round, so the old limit cut them short.
- **Capped hops start from more than one state.** `capsearch --starts K` also carries K less 1 library corners with the same arms, leans and count whose f0 is nearest the target. Each start gets the three capped LPs, and the hop time is shared among the starts, best start first. `--first N:C,...` runs the named pairs first.

### 15.2 The quench of every build up to 1.5e-3 above the bar

`work/qlist.py` measured the raw side of every corner and modules build of rounds 13 to 15 against the bar of round 15. 104 builds end 0 to 1.5e-3 above it, after the ones quenched in round 15 are left out. boxA and boxC each took half of the list, smallest score-weighted excess first. At 12:45 UTC boxA switched to one build per n at 1e-5 or more above the bar, largest excess first. So both ends of the list ran.

85 quenches ran (a few builds twice, where the two ends met). 35 found a certified gain, and none ended below the bar:

| n | build | above the bar before | quench | above the bar after |
|---|---|---|---|---|
| 702 | `take-corners-r15/work/nbq3-back/q2/702-r22.csv` | +9.77e-4 | -9.52e-4 in 33 s | +2.4e-5 |
| 813 | `take-corners-r15/work/nbq3-back/q3/813-r7.csv` | +4.71e-4 | -3.25e-4 in 45 s | +1.5e-4 |
| 419 | `take-modules-r15/work/raw/419-G002.csv` | +6.7e-5 | -6.7e-5 | ties the bar |
| 874 | `take-corners-r15/work/nbq3-back/q2/874-r0.csv` | +3.1e-4 | -5.3e-5 | +2.6e-4 |
| 600 | `take-corners-r14/work/raw-u2-f/600-1.csv` | +4.6e-5 | -4.6e-5 | ties the bar |
| 936 | `take-modules-r15/work/boxD-raw/936-G071.csv` | +1.06e-5 | -8.9e-6 | +1.7e-6 |

The other 29 gains are below 5e-6 of side, most of them builds that rebuild the held packing to 1e-7 and come back to it exactly. The 702 file went to the polish and soft lanes through the handoff log. So the quench of round 15 took the large drops: what is left of the old builds is 2e-5 or more above the bar after it.

### 15.3 The near-bar builds

boxC built the 32 n of round 15's `q1.txt` that round 15 did not build (746 dropped: its bar fell by 4.6e-3), two choices each, with `lib15v`. Every build within 1.5e-3 of the bar got the quench from its certified file.

27 of the 32 n got builds before 13:43 UTC (873 had no start within the gate). One n certifies:

- **863: 1.53e-4 of side under the bar, 5.219e-06 of score.** The corner is `zc7x7-74f8297av.C` from the capped hops of round 15 (made under the caps of 804, in `zones-v`). The far zones are `863b14a.F1` and `984h.F1`. fq ends 6e-5 under held and the quench takes 9.3e-5 more. Round 15 built `zones-v` corners only on 5 n, so this choice had no build before. The polish lane took our file 1.7e-8 further, so the row is theirs at the end.
- **12 n rebuild the held packing** to 1e-9: 340, 599, 600, 650, 703, 704, 740, 797, 911, 974, 983 and 997. On 974 the quench ends 1.6e-7 of side under held (5.1e-9 of score). The polish lane took that one further too.
- **The rest end above the bar.** Within 1e-4: 875 +1e-6, 924 and 975 +8e-6, 705 +7.1e-5. Further: 996 +1.1e-4, 813 +1.5e-4, 931 +2.0e-4, 461 +2.3e-4, 552 +2.7e-4, 804 +2.8e-4, 651 +2.9e-4, 757 +3.9e-4 and 811 +4.2e-4.

### 15.4 Capped hops on the pairs round 15 did not reach

`capsearch` ran on boxD with 240 s per pair and 3 starts. It took the 11 pairs of `needs-near.pkl` that round 15 did not reach (the tool skips the two with a `^` id). 10 ran before 12:59 UTC. None fits its caps.

| n | corner | excess of the carried corner | after the capped LPs and hops | best start |
|---|---|---|---|---|
| 600 | `zc8x7-80f9334du2.C` | +0.0083 | +0.00020 | the corner itself |
| 997 | `zc8x8-107f9672ar.C` | +0.0395 | +0.00018 | all three tie (`997h12.C`) |
| 703 | `zc8x7-59f9417bu2.C` | +0.0131 | +0.00025 | ties `703h13.C` |
| 932 | `zc8x8-130f9389ar.C` | +0.0046 | +0.00458 | the corner itself |
| 705 | `zc8x7-68f9501ar.C` | +0.0074 | +0.00743 | all three tie |
| 873 | `zc8x8-107f9419ar.C` | +0.0374 | +0.00435 | all three tie |
| 418 | `zc6x6-77f9301dr.C` | +0.0005 | +0.00027 | `418h14.C` |
| 875 | `zc7x7-92f9820ar.C` | +0.0089 | +0.00892 | all three tie |
| 650 | `zc8x6-93f9428ar.C` | +0.0017 | +0.00017 | `650h.C` |
| 998 | `zc7x7-118f9858br.C` | +0.0077 | +0.00375 | the corner itself |

The capped LPs do most of the work. They take the carried corner from 0.0005 to 0.04 over its caps down to the level of the held layout's own corner. On 997, 703, 418 and 650 that corner is one of the starts (`997h12.C`, `703h13.C`, `418h14.C`, `650h.C`) and it reaches the same excess. So these near-bar choices are the held layout's own corner, about 2e-4 over caps set 1e-4 under the bar. The hops find nothing below it in 240 s.

### 15.5 Hops on the corners of the new layouts and of our wins

The modules lane cut 23 corners into `lib16`. They come from the new layouts of round 15 (harvest pass j and the held file) and from our wins of 921, 983 and 984. Each got 50 s of hops at its own f and count (`sweep`, boxD). 12 of them came out with a lower loss and went into the table with the tag `x` (`zones-x`, merged into `lib16` as `lib16x`):

| corner | count | loss before | loss after |
|---|---|---|---|
| 600h15.C | 73 | 3.2812 | 3.2140 |
| 872h15.C | 130 | 3.1654 | 3.1529 |
| 921fa15.C | 115 | 3.6914 | 3.6834 |
| 507hj.C | 64 | 2.0783 | 2.0717 |
| 983co15.C | 164 | 2.5014 | 2.4948 |
| 651h15.C | 59 | 3.2842 | 3.2778 |
| 812po15.C | 154 | 3.4418 | 3.4383 |

The other 5 fell by less than 0.001. `predict` with the 12 new corners puts no n below the bar. The nearest are 703 (+1.9e-4), 600 (+2.2e-4), 912 (+2.6e-4) and 974 (+3.2e-4). The builds of these four n came out far lower than the prediction:

| n | corner | predicted minus bar | built minus bar | score |
|---|---|---|---|---|
| 600 | `zc8x7-73f9329ax.C` (600h15.C after hops) | +2.2e-4 | -7.54e-4 | 3.077e-05 below held and every take |
| 703 | `zc8x7-59f9411ax.C` (651h15.C after hops) | +1.9e-4 | -6.08e-4 | 2.292e-05 below held and every take |
| 912 | `zc8x8-133f7032ax.C` | +2.6e-4 | +1.1e-6 | |
| 974 | `zc8x8-98f7034ax.C` | +3.2e-4 | +4.1e-5 | |

The quench found nothing more on any of the four. The build of 600 is 9.8e-4 under its prediction and the one of 703 is 8.0e-4 under it. So the generator's prediction is not a good cut for these corners. From 13:39 UTC the other n of the list got builds too, nearest first, on boxD and from the far end on boxC: 

| n | corner | predicted minus bar | built minus bar |
|---|---|---|---|
| 932 | `zc8x8-130f9363ax.C` (872h15.C after hops) | +5.4e-4 | -6.49e-4, 2.125e-05 of score below held and every take |
| 740 | `zc8x8-98f7034ax.C` | +6.2e-4 | +1.9e-8 (the held packing) |
| 812 | `zc8x8-154f9234ax.C` | +7.9e-4 | +1.3e-5 |
| 931 | `zc8x8-130f9289ax.C` | +1.1e-3 | +1.7e-4 |
| 872 | `zc8x8-130f9363ax.C` | +1.1e-3 | +4.9e-4 |
| 813 | `zc8x8-130f9289ax.C` | +8.1e-4 | +1.25e-4 |
| 983 | `zc7x9-164f8163ax.C` (983co15.C after hops) | +8.9e-4 | +1.57e-4 |
| 984 | `zc9x7-115f8285ax.C` | +1.1e-3 | +4.9e-4 |
| 921 | `zc9x7-115f8173ax.C` | +1.2e-3 | +8.6e-4 |
| 911 | `zc8x8-98f7034ax.C` | +1.2e-3 | -2e-9 (the held packing) |

The bars of 921 and 984 are held here. Other lanes hold both lower now.

### 15.6 What to search next

1. **Hop the corners of every new layout as it lands.** Then build every n they predict within 1.5e-3. This round, 50 s of hops on 23 such corners gave 3 wins out of 11 builds. Builds with these corners ended 2.6e-4 to 1.2e-3 under their prediction, so a cut at 5e-4 leaves wins unbuilt. The corners of the layouts that landed this round have not been cut or hopped. These are the 549, 598, 649 and 984 of other lanes, and our 600, 703 and 932.
2. **Give the 23 corners more than 50 s.** 600h15.C fell 0.067 squares in 50 s. Its curve may not be flat yet.
3. **Skip capped hops that end on the held corner.** On 4 of 10 pairs the capped LPs reach the excess of the held layout's own corner, about 2e-4. The hops do not move it.
4. **Quench only new builds.** The old builds left after the quench of rounds 15 and 16 are 2e-5 or more above the bar.
5. **Low f needs another corner design** (two tapers that share a staircase), and **a control B from a corner of another design**. Neither was started this round.

## 16. Round 17 corners (2026-11-12)

Result at 20:05 UTC: 8 n certify against round 16 and every live take dir: 915, 984, 985, 863, 977, 804, 549 and 419. They give 5.798e-04 of score on held, and 3.425e-04 over the other takes. The round 17 file holds our 915 and 977. The other six certified after 17:42 UTC and go to the next assembly. Seven more n certified here first. Other lanes then took our files further: 914 (soft), 860, 910 and 921 (family), 982 (polish, then classfill), 975 (midm) and 983 (classfill). The main find: a corner of another lane's new layout, cut and hopped within the hour with one square less, wins n outside its own layout. The stair-c 861 corner at 108 squares wins 860, 921 and 984. The readers 863 corner wins 804 and 863. The family 861 corner at 91 squares wins 984 and 985.

Held is now `gather/round16-2026-11-12a.csv` (22.1664224426, gate dir `gate/cand-round16-1112a`). The bar of an n is the smallest of its held side and its sides in every live take dir of round 17 (`work/mkbar.py`). Work dir: `<scratch>/bounties-squares/take-corners-r17/work` on boxA, and `<scratch>/squares-corners` on boxC, boxD and boxE (removed at the end). `work/certloop2.sh` and `work/certloop3.sh` copied the remote results back every 5 to 7 minutes. They certified every file under the bar and wrote a handoff line for each new row.

This lane ran four times. boxA rebooted at 16:15 UTC, and usage limits stopped the second run at 17:52 UTC and the third at 19:05 UTC. Each run went on from the files the run before left. The jobs on the boxes kept running through the two usage limits.

### 16.1 The library of this round

`lib17` is the modules lane's `lib16b` of round 16 with three additions:

- the 12 hopped corners of round 16 (`zones-x`), which `lib16b` did not hold.
- the layouts of the round 16 held file that `lib16b` did not hold: 600, 700, 703, 704, 932, 974 and 995 (tag `h17`).
- the layouts of the live takes of round 17: 9 of the 13 twoshort layouts (tag `ts17`), the classfill 703 (`cf17`) and the midm 378 (`md17`).

`modules.py grow` cuts a layout into its modules. It does not cut the twoshort 851, 911 and 912 (their second arm does not cut) or 974 (no two flush arms). The tables of the 54 new modules took 4 minutes on one process.

Later in the round the same `grow` took the newest take layouts three more times. These are `lib17g` at 15:52 UTC (tag `*17`), `lib17h` at 17:47 UTC (tag `*3`) and `lib17i` at 18:10 UTC (tag `*4`).

### 16.2 Hops on the corners of the new layouts

The corners of the new layouts of rounds 16 and 17 got 50 s of hops each at their own f and count (`sweep`, 21 corners, boxC and boxD). Six near copies of the same corner were left out. Only one corner fell by more than 0.005 squares: 975re16.C, from 2.8446 to 2.7617. The others are the corners of layouts that the polish and family lanes had already squeezed, and the hops find nothing there.

`predict` with the 36 new corners before the hops gives 39 n with a choice, and none below the bar. The nearest are 973 (+6.9e-5), 975 (+1.3e-4), 976 (+1.4e-4), 921 and 796 (+2.4e-4). With the hopped corners (`zones-y`) only 7 n have a choice, from 700 (+5.8e-4) up.

The builds of the nearest rows give the twoshort layouts back, or a hair below them:

| n | corner | built minus bar | result |
|---|---|---|---|
| 973 | 973ts17.C, far zone 910ts17.F2 on both arms | -2.9e-7 | certifies, 9.2e-10 under the twoshort take |
| 975 | 975ts17.C, far zones z9-19f720.F1 and z9-46f740.F1 | -1.06e-5 | certifies, 3.4e-7 under the twoshort take |
| 976 | 976ts17.C | -3.6e-9 | ties |
| 978 | 978ts17.C | -1.5e-9 | ties |
| 796 | 796ts17.C | -1e-12 | ties |

### 16.3 The twoshort corners: hops and one square less

The twoshort lane built its corners from nothing with the staircase tool (`st8x9` and `st9x9`), and settled them in its own layouts. We cut those corners from the 9 layouts. Each got 45 s of hops on its own count, then 45 s on each count with one square deleted (`sweep --down 1`, boxC). The table `zones-k` holds 16 of them (tag `k17`).

| corner | arms | f | count | loss at the start | loss after |
|---|---|---|---|---|---|
| 852ts17.C | 9 and 9 | 0.6943 | 96 | 4.0266 | 3.5335 |
| 910ts17.C | 9 and 9 | 0.6772 | 129 | 4.0042 | 3.8121 |
| 914ts17.C | 8 and 9 | 0.7308 | 68 | 2.8903 | 2.7211 |
| 975ts17.C | 9 and 9 | 0.7146 | 129 | 3.5696 | 3.5587 |
| 978ts17.C | 9 and 9 | 0.7595 | 87 | 4.6845 | 4.3559 |
| 978ts17.C less one | 9 and 9 | 0.7595 | 86 | | 4.1409 |
| 913ts17.C less one | 9 and 9 | 0.7135 | 102 | | 3.7367 |
| 914ts17.C less one | 8 and 9 | 0.7308 | 67 | | 3.1369 |

The 86 squares of 978ts17.C less one lose 0.21 less than its own 87. The hops on its own count started from the cut, which the twoshort squeeze had left at 4.68.

`predict` with `zones-k` puts two n below the bar: 915 (-2.58e-3) and 914 (-1.21e-3). Its other rows are 910 (+4.4e-4), 976 (+4.6e-4), 977 (+5.5e-4), 975 (+8.5e-4) and 973 (+1.0e-3). With a slack of 4e-3 the generator adds 916 (+1.55e-3), 912 and 796 (+2.1e-3), 913 (+2.6e-3), 854 and 851 (+2.9e-3).

The builds:

| n | corner | predicted minus bar | built minus bar | result |
|---|---|---|---|---|
| 914 | `zc9x9-86f7595ak17.C` (978ts17.C less one) | -1.21e-3 | -1.63e-3 | certified, 9.906e-05 of score. The soft lane took our file 2e-5 of score further, so the row is theirs |
| 915 | `zc8x9-68f7308ak17.C` (914ts17.C after hops) | -2.58e-3 | -3.5e-3. A copy of the corner after more hops (`am17`) and other far zones took 1.6e-4 more off | 1.215e-04 of score under held and every take |
| 977 | `zc9x9-86f7595ak17.C` | +5.5e-4 | -2.05e-3 | 6.545e-05 of score under held and every take. fq ended 1.4e-5 above the bar and the quench took 2.06e-3 of side off |
| 910 | `zc9x9-129f6772ak17.C` | +4.4e-4 | -6.6e-4 | certified, 8.684e-05 of score. The family lane holds the same layout 4e-12 lower |
| 976 | `zc9x9-103f7271ak17.C` | +4.6e-4 | +7.8e-6 | |
| 975 | `zc9x9-129f7146ak17.C` | +8.5e-4 | +8.3e-6 | |
| 973 | `zc9x9-129f6898ak17.C` | +1.0e-3 | +6.9e-5 | |
| 916 | `zc8x9-68f7308ak17.C` | +1.55e-3 | +1.1e-3 | |
| 912 | `zc9x9-96f6943ak17.C` | +2.1e-3 | +1.8e-3 | |

On 854 and 851 the start is 3.1e-3 above the bar, so the build stops there. The second and third choices of 910, 914 and 977 (boxD) give the same side to 1e-6.

### 16.4 The twoshort corners carried outside the slice

The nine twoshort corners are seven 9 x 9, the 9 x 8 of 796 and the 8 x 9 of 914. We carried them to f = 0.79 and f = 0.84, with soft steps where the LP locks. Each then got 30 s of hops on its own count and on one square less (`work/boxC/carry.sh`, boxC). They lose 3.52 to 5.14 there. `predict` with them gives one row within 3e-3: 977 at +1.4e-3, with the 8 x 9 corner at f = 0.79. A carried twoshort corner is not a good start outside its own slice. The stair lanes' fresh staircases at f = 0.80 are, as section 16.6 shows.

### 16.5 Hops under the caps of the twoshort pairs

`capsearch` took the near-bar pairs of the twoshort corners (boxC, about 165 s each). The capped LPs and hops bring each corner close to its caps, but not under them:

| n | corner | excess of the carried corner | after |
|---|---|---|---|
| 973 | 973ts17.C | +0.0061 | +0.0012 |
| 975 | 975ts17.C | +0.0057 | +0.00086 |
| 976 | 976ts17.C | +0.0019 | +0.0012 |

We stopped `capsearch` at 16:08 UTC to give its slot to the builds of section 16.6.

### 16.6 The staircase corners of the stair-c lane, one square less

The stair-c lane built new layouts of 861, 982 and 804 (and a near 986) with staircase corners at f = 0.80 to 0.85. We cut their corners (`lib17g`) and gave each 50 s of hops on its own count and on one square less (boxC):

| corner | arms | f | count | loss at the start | loss after |
|---|---|---|---|---|---|
| 861sc17.C less one | 9 and 9 | 0.8164 | 108 | 3.9882 | 3.8165 |
| 861sc17.C | 9 and 9 | 0.8164 | 109 | 4.2557 | 4.2557 |
| 982sc17.C | 9 and 9 | 0.8085 | 133 | 4.3816 | 4.1832 |
| 982sc17.C less one | 9 and 9 | 0.8085 | 132 | 5.0124 | 4.4607 |
| 804sn17.C | 7 and 7 | 0.8308 | 81 | 2.6008 | 2.5961 |

`predict` with these corners (`zones-g`, `lib17gg`) gives 8 rows within 1.5e-3: 860 (-1.1e-3), 921 (-1.7e-4), 984 (+7e-5), 982 (+8.4e-4), 973, 804, 863 and 983. The builds:

| n | corner | far zones | predicted minus bar | built minus bar | result |
|---|---|---|---|---|---|
| 860 | `zc9x9-108f8164ag17.C` (861sc17.C less one) | 921h13.F2, 860fa16.F2 | -1.10e-3 | -1.41e-3 | 4.811e-05 of score under held and every take |
| 921 | `zc9x9-108f8164ag17.C` | 921h13.F2, 860fa16.F2 | -1.7e-4 | -2.45e-3 | certified, 8.091e-05 of score. The family lane holds the same file 5e-13 lower |
| 984 | `zc9x9-108f8164ag17.C` | 921h13.F2, 921mo16.F1d (the second choice) | +7e-5 | -1.97e-3 | 6.288e-05 of score under held and every take |
| 982 | `zc9x9-133f8085ag17.C` (982sc17.C after hops) | 921h13.F2d, 983h.F1 (the second choice) | +8.4e-4 | -1.00e-3 | 9.635e-05 of score under held, 9.9e-6 under the polish lane's copy of our first 982 |
| 983 | `zc9x9-108f8164ag17.C` | 860fa16.F2, z9-42f840.F1 | +1.38e-3 | +4.0e-4 | |
| 804 | `zc7x7-81f8308ag17.C` | 862b14.F2d, 803h.F1 | +9.9e-4 | +6.7e-4 | |
| 973 | `zc9x9-129f6898ag17.C` | z9-36f680.F1, 910ts17.F2 | +1.53e-3 | +6.1e-4 | |
| 863 | `zc7x7-81f8308ag17.C` | 863h.F1 on both arms | +1.03e-3 | +8.3e-4 | |

The corner of the stair-c 861 with one square less wins three n: 860, 921 and 984. These builds end 3e-4 to 2.3e-3 under their prediction. The second and third choices change only the far zones, and they move the side by 1e-6 to 3e-4.

### 16.7 The corners of the layouts that landed after 17:00 UTC

At 17:47 UTC `grow` took every layout of the live take dirs into `lib17h`: 23 new corners (tag `*3`). Each got 40 s of hops on its own count and 40 s on one square less (`sweep --down 1`, half on boxE and half on boxA). The table `zones-q` holds 35 of the kept states (tag `q17`). The largest drops:

| corner | arms | f | count | loss at the start | loss after |
|---|---|---|---|---|---|
| 982cr3.C less one | 9 and 9 | 0.8078 | 150 | 4.7639 | 4.2296 |
| 812fy3.C less one | 8 and 8 | 0.9233 | 153 | 4.1200 | 3.7528 |
| 551mn3.C less one | 7 and 8 | 0.9237 | 89 | 3.1573 | 3.0444 |
| 812fy3.C | 8 and 8 | 0.9233 | 154 | 3.4230 | 3.3353 |
| 863rd3.C | 7 and 7 | 0.8421 | 95 | 2.5250 | 2.4415 |
| 910po3.C less one | 9 and 9 | 0.6772 | 155 | 4.0801 | 3.9975 |
| 587sb3.C | 8 and 8 | 0.7438 | 126 | 3.1976 | 3.1311 |
| 871fy3.C | 8 and 8 | 0.9293 | 146 | 3.3641 | 3.2987 |

On 910po3.C the count with one square less ends below its own count (3.9975 against 4.0039).

`predict` with `zones-q` (`lib17hq`) gives 11 rows within 3e-3, and one of them below the bar (419). We built all 11, and the second choice of the 6 nearest:

| n | corner | far zones | predicted minus bar | built minus bar | result |
|---|---|---|---|---|---|
| 804 | `zc7x7-95f8421aq17.C` (863rd3.C after hops) | 803h.F1, 984mo16.F2d | +1.19e-3 | -1.77e-3 | 6.238e-05 of score under held, 1.64e-05 under the stair-c take |
| 863 | `zc7x7-95f8421aq17.C` | 803h.F1, 863po16.F1 | +9.3e-4 | -1.41e-4 | 7.189e-05 of score under held, 4.4e-06 under the stair-c take |
| 419 | `zc6x6-78f9350aq17.C` (419mn3.C after hops) | 304h.F1, 419h.F2d | -3.4e-5 | -5.94e-4 | 3.123e-05 of score under held, 2.90e-05 under the family take |
| 983 | `zc9x9-98f8255aq17.C` (984cr3.C less one, after hops) | 921mo16.F1 on both arms | +1.38e-3 | -4.17e-4 | 1.330e-05 of score under held and every take |
| 973 | `zc9x9-156f6765aq17.C` (910fy3.C after hops) | z9-36f680.F1, 910ts17.F2 | +1.02e-3 | +4e-6 | |
| 815 | `zc7x7-113f9549aq17.C` | 462h10.F2, 815fa14.F1d | +1.20e-3 | +2.0e-5 | |
| 871 | `zc8x8-146f9293aq17.C` | 812h14.F1, 503h.F2 | +9.0e-4 | +6.2e-5 | |
| 758 | `zc7x7-113f9549aq17.C` | 505h.F2, 758b14.F2d | +5.1e-4 | +1.77e-4 | |
| 996 | `zc8x8-122f9454aq17.C` | 704r10.F2d, 758h.F1 | +1.04e-3 | +8.75e-4 | |
| 910 | `zc9x9-156f6765aq17.C` | z9-36f680.F1, 973fy17.F2 | +7.3e-4 | ties | |
| 982 | `zc9x9-151f8078aq17.C` (982cr3.C after hops) | 983h13.F2, 921h.F2 | +1.26e-3 | ties the polish take | |

One corner of the readers lane's 863 wins two n, 804 and 863. Its 95 squares at f = 0.8421 lose 0.083 less after 40 s of hops. The second choices of 804, 863, 419, 983, 815 and 973 change only a far zone. They end within 1e-5 of the first, and none lower.

At 18:10 UTC a second `grow` took the layouts that had landed since 17:47 into `lib17i`: 15 new corners (tag `*4`). Each got 60 s of hops on its own count and on one square less (boxE and boxA). The table `zones-v` holds them (tag `v17`), merged with `zones-q` into `lib17iqv`. The largest drops:

| corner | arms | f | count | loss at the start | loss after |
|---|---|---|---|---|---|
| 982cr4.C less one | 9 and 9 | 0.8075 | 150 | 4.7711 | 4.3034 |
| 921fy4.C less one | 9 and 9 | 0.8131 | 125 | 4.2759 | 3.9785 |
| 984cr4.C less one | 9 and 9 | 0.8255 | 107 | 4.2026 | 4.0074 |
| 921fy4.C | 9 and 9 | 0.8131 | 126 | 3.7642 | 3.5906 |
| 976md4.C | 9 and 9 | 0.7271 | 121 | 3.7077 | 3.6213 |
| 851ts4.C | 9 and 9 | 0.6799 | 104 | 3.5818 | 3.5187 |

921fy4.C comes from the family lane's 921, which is our 984 of section 16.6 one shell down. `predict` with `zones-v` gives 9 rows within 3e-3, two of them below the bar of 18:08 UTC: 804 (-9.9e-4) and 920 (-6.6e-4). The builds:

| n | corner | far zones | predicted minus bar | built minus bar | result |
|---|---|---|---|---|---|
| 983 | `zc9x9-125f8131av17.C` (921fy4.C less one, after hops) | 860fa16.F2, 983h.F1 | +2.9e-5 | -1.11e-3 | 4.875e-05 of score under held, taken 5.2e-06 further by the classfill lane at 19:10 UTC |
| 920 | `zc9x9-126f8131av17.C` (921fy4.C after hops) | z9-51f820.F1, z9-43f760.F1 | -6.6e-4 | -1.43e-3 | ties the stair-c take, which certified the same side to 2e-9 at 18:50 UTC |
| 976 | `zc9x9-121f7271av17.C` (976md4.C after hops) | z9-19f720.F1, z9-46f740.F1 | +3.4e-4 | -7.0e-5 | 1.7e-7 of side above the twoshort take, which fell in the meantime |
| 975 | `zc9x9-129f7146av17.C` (975md4.C after hops) | z9-46f740.F1, z9-19f720.F1 | +8.7e-4 | +4e-6 | |
| 851 | `zc9x9-104f6799av17.C` (851ts4.C after hops) | z9-27f720.F1, 910ts17.F2 | +7.6e-4 | +6.7e-5 | |
| 813 | `zc8x8-130f9289av17.C` (813md4.C after hops) | 503h.F2, 995h12.F2d | +8.1e-4 | +1.25e-4 | |
| 931 | `zc8x8-130f9289av17.C` | 995z11.F2, 871fa14.F1d | +1.1e-3 | +1.69e-4 | |
| 804 | `zc7x7-88f8284av17.C` (804sc4.C after hops) | 803h.F1, 862q1.F2 | -9.9e-4 | +3.97e-4 | above our 804 of the table before |
| 982 | `zc9x9-151f8075av17.C` (982cr4.C after hops) | 921h.F2, 982sc17.F2 | +1.18e-3 | no build | the border lane's 982 had moved the bar 6.6e-3 lower |

The predictions use the bar of 18:08 UTC, and the builds the bar of 18:37 UTC. Our 804 and 983 of the table before had moved the bar in between. The second choices of 920 and 983 give the same side to 1e-9.

Deeper hops on the three corners that won in this section (`zc7x7-95f8421aq17.C`, `zc9x9-98f8255aq17.C` and `zc6x6-78f9350aq17.C`, 100 s per count, boxD):

The 9 x 9 corner at 98 squares fell from 4.2025 to 4.1024. The 7 x 7 corner at 95 and the 6 x 6 corner at 78 did not move, and their counts with one square less stay above them. So the first 40 s had taken the drop on those two. The 983 build with the deeper 98-square corner ends 5.5e-5 under the bar of 18:37 UTC. That is still 1.06e-3 of side above our 983 with the corner of 921fy4.C.

At 18:45 UTC a third `grow` took the layouts that had landed since 18:10 into `lib17j`: 11 new corners (tag `*5`). Each got 40 s of hops on its own count and on one square less (boxA and boxD). The table `zones-x` (tag `x17`) holds 16 of the kept states, merged into `lib17jx`. The largest drop is on the twoshort 851 corner with one square less, from 4.2458 to 4.0190. `predict` gives 6 rows within 3e-3 and none below the bar of 19:02 UTC. The builds:

| n | corner | far zones | predicted minus bar | built minus bar | result |
|---|---|---|---|---|---|
| 549 | `zc8x8-139f8980ax17.C` (700mo5.C, the modules lane's 700) | 598h13.F2, 598fa16.F1d | +1.10e-3 | -2.1e-5 | 3.485e-05 of score under held and every take |
| 700 | `zc8x8-139f8980ax17.C` | 700h17.F2, 700so16.F1 | +4.8e-4 | +7e-7 | |
| 975 | `zc9x9-129f7146ax17.C` (975md5.C) | z9-46f740.F1, z9-19f720.F1 | +8.7e-4 | +2e-6 | |
| 598 | `zc8x8-139f9012ax17.C` (598mo5.C) | 756h09.F2, 503h.F2 | +9.7e-4 | +1.74e-4 | |
| 875 | `zc7x7-99f9871ax17.C` (875md5.C) | 704h.F1d, 462h10.F2 | +1.36e-3 | +5.45e-4 | |
| 936 | `zc7x7-99f9871ax17.C` | 936t13.F1, 760h12.F2 | +2.19e-3 | +9.5e-4 | |

A corner built back into its own n ends within 2e-6 of the layout it came from (700 and 975). The gain comes when the corner moves to another n: the 700 corner wins 549.

The two corners of 921fy4.C that won 983 and tied 920 got 90 s more hops (tag `y17`, boxE). With one square less, the 126-square corner fell from 3.9785 to 3.8345. Even so, `predict` puts no n within 3e-3 of the bar. Our 983 and the classfill lane's 983 had moved that bar by 1.3e-3 of side.

At 19:10 UTC a fourth `grow` took the layouts that had landed since 18:50 into `lib17m`: 12 new corners (tag `*6`). Each got 40 s of hops on its own count and on one square less (boxA and boxC). The table `zones-z` (tag `z17`) holds 17 of the kept states, merged into `lib17mz`. The largest drops:

| corner | arms | f | count | loss at the start | loss after |
|---|---|---|---|---|---|
| 861fy6.C | 9 and 9 | 0.8108 | 91 | 3.7362 | 3.3984 |
| 921rd6.C less one | 9 and 9 | 0.8130 | 134 | 4.3319 | 3.9777 |
| 978ts6.C | 9 and 9 | 0.7595 | 105 | 4.6845 | 4.3559 |
| 995cf6.C less one | 8 and 8 | 0.9452 | 121 | 4.1928 | 4.0927 |

`predict` gives 7 rows within 3e-3, and one of them below the bar of 19:14 UTC: 984 (-2.7e-4). The builds:

| n | corner | far zones | predicted minus bar | built minus bar | result |
|---|---|---|---|---|---|
| 984 | `zc9x9-91f8108az17.C` (861fy6.C after hops) | z9-42f840.F1, z9-43f840.F1 | -2.7e-4 | -6.54e-4 | 1.075e-04 of score under held, 2.08e-05 under the stair-c take |
| 985 | `zc9x9-91f8108az17.C` | 984h.F2, 921h.F2 | +1.41e-3 | -4.5e-5 | 8.50e-05 of score under held, 1.45e-06 under the stair-c take |
| 983 | `zc9x9-134f8146az17.C` (983cf6.C) | 921h13.F2, 860fa16.F2 | +6.8e-4 | +8e-8 | ties the classfill take |
| 977 | `zc9x9-104f7595az17.C` (978ts6.C less one, after hops) | z9-46f740.F1, z9-19f720.F1 | +2.60e-3 | 0 | the quench ends on our own 977 |
| 914 | `zc9x9-104f7595az17.C` | z9-19f720.F1, z9-46f740.F1 | +1.02e-3 | +5.97e-4 | |
| 920 | `zc9x9-135f8130az17.C` (921rd6.C after hops) | z9-51f820.F1, 860fa16.F2d | +2.22e-3 | +1.54e-3 | |
| 921 | `zc9x9-100f8215az17.C` (922sc6.C after hops) | z9-42f840.F1, 860fa16.F2 | +2.51e-3 | +2.19e-3 | |

The family lane's 861 corner wins 984 and 985 after 40 s of hops. Its 91 squares at f = 0.8108 lose 0.338 less, the largest drop of this grow. The second choices of 984 and 985 change a far zone and give the same side or a larger one.

At 19:35 UTC a fifth `grow` took the layouts that had landed since 19:10 into `lib17p`: 5 new corners (tag `*7`), 4 of them with a corner `base` can use. Each got 40 s of hops on its own count and on one square less (boxC and boxD). `predict` (tag `p17`) gives 4 rows within 3e-3 and none below the bar. 378 built 1.21e-4 over the bar, 339 1.58e-3 over and 860 4.25e-4 over. The build of 921 stopped at its start, 3.1e-3 over the bar.

60 s more hops on `zc9x9-91f8108az17.C` (tag `h17`, boxC) left its 91 squares at 3.3984. With one square less it gives 90 squares at 4.1529. `predict` puts that corner in 984 at +1.82e-3 over the bar of 19:14 UTC. The build ends 1.10e-3 over that bar, and our 984 is 6.5e-4 under it.

### 16.8 Traps

The venv on boxC and boxD needs numpy 2.5.4, scipy 1.18.1, mpmath 1.4.1 and pandas 2.2.3. The first builds ran without mpmath and pandas, which only the quench imports. A build then writes its fq layout, stops at the quench, and writes no json. `modules.py take` needs the json, so the layout cannot certify. We wrote the json of 915 by hand from its log, and built 975 again.

`chain.sh` ran `predict` with `--slack 0.0015`, but the builds take every row within 3e-3. Rows between the two were never listed. `chain3.sh` predicts with `--slack 0.003`. On the x17 corners that adds one n (936), which built 9.5e-4 over the bar.

### 16.9 What to search next

1. **Cut and hop the corners of every new layout as it lands.** This round `grow` ran at the start and six more times. Each of the six won n within the hour, except the last. The grow of 15:52 UTC gave 860, 921, 982 and 984 from the stair-c layouts. The grow of 17:47 UTC gave 804, 863, 419 and 983, and the grow of 18:10 UTC a lower 983. The grow of 18:45 UTC gave 549, and the grow of 19:10 UTC gave 984 and 985. Builds end 3e-4 to 3e-3 under their prediction, so every row within 3e-3 is worth a build.
2. **Predict at slack 3e-3.** `chain.sh` listed only rows within 1.5e-3, and the 804 that won was predicted at +1.19e-3. Use `chain3.sh`.
3. **Always hop one square less.** With one square less, the stair-c 861 corner wins 860, 921 and 984. The twoshort 978 corner wins 914 and 977 the same way.
4. **Build a corner into other n, not into its own.** In its own n, a corner ends within 2e-6 of its source layout (700, 975 and 977). The gains came from other n: 549 from the 700 corner, 984 and 985 from the 861 corner.
5. **Second choices only near the bar.** They change a far zone and move the side by 1e-8 to 3e-4. After 18:00 UTC no second choice gained (549, 976, 975, 984, 985).
6. **The first 40 to 60 s of hops take the drop.** More hops on the winning corners found no new n (section 16.7).
7. **Drop two searches.** The twoshort corners carried outside their slice do not pay (section 16.4). The capped hops on the twoshort pairs stay 8.6e-4 or more over the caps (section 16.5).
8. **Low f needs another corner design** (two tapers that share a staircase), and **a control B from a corner of another design**. Neither was started this round.

## 17. Round 19 corners (2026-11-12)

Result at 22:26 UTC: 2 n certify against round 17 and every live take dir: 598 and 700. They give 1.299e-05 of score on held, and 1.297e-06 over the other takes. Two more n certified here first, and other lanes then took them further from our files. 554 certified at 21:33 UTC for 7.742e-05, and the classfill lane took our file further. 862 certified at 22:04 UTC for 1.397e-05, and the family lane went one shell up from our near 803 layout to a 862 6.7e-7 lower. The main find came last. The grow of 21:54 UTC cut the stair-c 863 corner of round 19, and with one square less it wins 862 by 4.10e-4 of side. The `--caps` fault is fixed (section 17.2), the low-f corner of two tapers is measured (section 17.3), and control B ran from a corner of another design (section 17.4).

Held is now `gather/round17-2026-11-12a.csv` (22.1635211736, gate dir `gate/cand-round17-1112a`). The bar of an n is the smallest of its held score and its scores in every `take-*-r17` dir and every live `take-*-r19` dir (`work/mkbar.py`). Work dir: `<scratch>/bounties-squares/take-corners-r19/work` on boxA, and `<scratch>/squares-corners` on boxC and boxD (removed at the end). The budget was 2 processes on boxC, 1 on boxD and 1 on boxA.

### 17.1 The grow loop

`work/grow.sh` copies every take dir of rounds 17 and 19 (not ours), cuts the new layouts into the library with `modules.py grow`, and writes the start states of the new corners (`zone_corner.py base --own`). Each corner then gets hops on its own count and on one square less (`sweep --down 1`). `work/gchain.sh` makes the table, merges it into the library and predicts at slack 3e-3 (`chain3.sh`). `work/rows.py` drops the rows whose corner was cut from a layout of the same n. Then one or two build loops run on boxC.

| grow (UTC) | layouts cut | corners with a start | rows within 3e-3 | builds, minus the bar |
|---|---|---|---|---|
| g8 (20:21) | 7: our six round 17 layouts, midm 817 | 6 | 3 (419 and 984 own n) | 863 +9.1e-4. Later the own-n 419: 0 (a tie) |
| g9 (20:36) | 2: midm 549, stair-c 803 (round 19) | 2 | 2 (549 own n) | **700 -1.6e-5, certified**. Later the own-n 549: +3.5e-5, its second choice the same |
| g10 (20:56) | 2: family 598, modules 754 | 2 | 3 (598 own n) | 700 the same side as g9, 549 +1.4e-4. Later the own-n 598: -6.8e-8 |
| g11 (21:08) | 24 near layouts of other lanes (stair-c 19, modules 1) and 4 take layouts | 24 | 10 (758 and 863 own n) | 977 0, 815 +2.0e-5, 921 +1.7e-4, 860 +2.0e-4, 924 +5.3e-4, 987 +5.5e-4, 914 +6.0e-4, 984 +1.4e-3. The second choice of 815: the same side. Later the own-n 758 +1.8e-4, 863 +1.1e-3 |
| g12 (21:25) | 5: classfill 875, invent 969, modules 554, readers 932, twoshort 910 | 4 | 3 (554 and 875 own n) | **554 -1.27e-4 under the modules take, certified**, 936 +6.2e-5 |
| g13 (21:40) | 11 | 9 | 1 (550, own n) | 550 -2e-9 of side (a tie) |
| g14 (21:54) | 7: classfill 554, family 987, modules 587 and 975, stair-c 863, 870 and 994 | 7 | 3 | **862 -4.10e-4, certified**, 975 -1e-9 (a tie), 803 +1.15e-4 over a take that landed during the build (to `near/803-g14.csv`) |

The round 19 take dirs filled slowly, and most of their new layouts do not cut. `grow` needs two flush arms. Most new layouts of the k123, midm, rigidsoft, family and readers lanes have none: 36 of the 49 round 19 layouts that g13 did not cut. So the grows found 2 to 9 new corners each. The near layouts of other lanes are a second source: `work/nears11` holds each `near/` file as a take dir of its own, and g11 cut 24 corners from them.

The certified rows came from corners of round 19 layouts of other lanes:

- **862** (1.397e-05 on held and over the other takes): the stair-c 863 corner of round 19 with one square less after hops (`zc9x9-110f8401ag14x.C`, 110 squares, f = 0.8401, loss 4.2774). Its far zones are `921h.F2` and `z9-43f840.F1d`. The build ends 4.10e-4 of side under the bar, 2.6e-4 under its prediction, and the quench found no gain.
- **700** (6.292e-07 on held, 6.115e-07 over the other takes): the midm 549 corner of round 19 after 40 s of hops (`zc8x8-147f8909ag9x.C`), with the far zones `700so16.F1` and `700h17.F2`. The quench found no gain. The g10 corner of the family 598 builds 700 to the same side, 1e-9 higher.
- **554** (7.742e-05 on held, 5.396e-06 over the other takes): the modules 554 corner of round 19 after 40 s of hops, built into its own n. The corner is `zc6x6-78f9745ag12x.C` (loss 2.0316 to 2.0304). The classfill lane then took our 554 file further (8.360e-05 on held), so 554 left our take at 22:02 UTC. The generator took other far zones (`506h.F2` and `507h12.F1`) than the modules layout, and the build ends 1.27e-4 of side under the modules take.
- **598** (1.236e-05 on held, 6.854e-07 over the other takes at 22:04 UTC): the family 598 corner of round 19 after hops, built into its own n. It ends 6.8e-8 of side under the family take, which certifies by the rule.

So the rule of round 17 (a corner built into its own n ends on its source) does not always hold. It held for 419 and 549 (a tie and +3.5e-5) and for 758 and 863 (+1.8e-4 and +1.1e-3). 598 ended 6.8e-8 of side lower, and 554 1.27e-4 lower. The 554 layout was new in the modules take, and the generator found other far zones for its corner. The bar files on the boxes were refreshed at 21:08 and 21:31. A row predicted against an old bar can be above the bar of the moment. 554 was predicted 1.6e-3 under the bar of 21:08 and 5.6e-5 above the bar of 21:31, and it still won.

### 17.2 Why `search --caps` made no move

The stair-c lane reported that `zone_corner.py search --caps` returned at once with 0 moves on its 978 corner. The cause has two parts:

- `hops` stopped as soon as both lengths fit their caps. `--caps DY,DX` sets the caps to the start lengths less DY and DX. With `0,0` or negative values the start fits already, so `hops` returned before its first hop.
- The `search` loop then called `hops` again and again with no exit. In 59 s it ran 2.0 to 2.7 million passes of 0 hops and wrote 270 to 377 MB of log.

The control is the family 861 corner (`861fy6.C`, 91 squares, f = 0.8108), which free hops take from 3.7362 to 3.3984:

| run | code | caps | hops | result |
|---|---|---|---|---|
| R1 | before the fix | `-0.03,0.05` (the start is over the x0 cap) | 1, then the loop spins | 3.4060, fits both caps |
| R2 | before the fix | `0,0` | 0, the loop spins | 3.7362, no move |
| R3 | after the fix | `0,0` | 9 | 3.7362: no state below the start fits both caps |
| R1n | after the fix | `-0.03,0.05` | 10 | 3.3984 under both caps |
| R4 | after the fix | `0,0` on the stair-c 978 corner `st9x9-96f7600a` | 10 in 115 s | 4.6941: no state below the start fits both caps |

The fix (`e844c88`): with `--caps`, the hops go on after both lengths fit. The objective is then the weighted sum plus 1000 times the excess over the caps. A pass of the `search` loop with no hop ends the loop. A run with hops as its only move starts from the corner. `capsearch` keeps the old rule and stops when both fit. One hop costs 5 to 7 s on these corners, so a capped run needs minutes, not seconds.

**n = 993 under the caps of the classfill lane.** The classfill lane shortened the 11-arm far zone of 993 by 0.0115 of arm length. So a corner of 993 wins if arm 1 is at most 0.0115 longer than the held corner and arm 2 is shorter. The held corner `993h.C` (arms 11 and 8, f = 0.924791, 169 squares) got 6 minutes of capped hops with the fixed code. The first run took its caps from the carried start, whose x0 is 4.5e-4 longer than the held corner. So we ran it again with caps from the held lengths. In 72 hops no state fits both caps, and `predict` gives no row with the kept state.

### 17.3 The low-f corner of two tapers

`zone_lowf.py corner C1 C2 F` builds a corner from two lattice tapers of section 5 (`zone_search.py taper_best`). The taper of arm 1 stands on the floor in its own strip, as in the far-zone frame (lean -1). The taper of arm 2 is mirrored in y = x (lean +1) and stands on the left wall. Arm 1 keeps the meeting square with the staircase of its upright columns. Arm 2 keeps only the squares that lie wholly at x >= W1. For every pair of taper positions at which a taper gains a square, the corner is settled (squeeze, then the two-stack LP of `zone_corner.py`), and its loss is measured. The best corner of each count class then got 1.6 minutes of `search` (one square less, one more, hops).

The positive test came first: on two 7-arms at f = 0.74 all 9 pairs of a 60 s run settled legal, at a loss of 4.80 to 7.45. A pair takes about 6.5 s.

| arms, f | pairs | best raw loss | best after search, by class | reference |
|---|---|---|---|---|
| 7 x 7, 0.74 | 204 of 256 in 12 min | 3.77 (63, class 0) | 3.61 (63, class 0), 3.84 (75, class 5), 3.86 (71, class 1), 3.87 (79, class 2), 3.94 (76, class 6), 4.15 (80, class 3), 4.30 (74, class 4) | round 13: 3.399 after hops (72, class 2). The carried library corner 804h.C: 5.87 |
| 6 x 6, 0.75 | 169 | 2.38 (48, class 0) | 2.25 (49, class 1), 2.29 (47, class 5), 2.38 (48, class 0) | round 13: 1.350 (78, class 0). Carried: 1.61 |
| 6 x 6, 0.70 | 169 | not kept | 1.67 (56, class 2), 1.89 (55, class 1), 2.29 (61, class 1) | round 13: 1.311 (78, class 0). Carried: 1.66 to 1.74 |
| 9 x 9, 0.76 | none | killed after 18 CPU-minutes and 2.6 GB in the taper scan | | |

- On two 7-arms the design gives every class a corner at 3.61 to 4.30. That is 2.3 below the carried library corner, but 0.21 above the corner that round 13 found by hops. The go line of 2.2 is not met.
- On two 6-arms it is 0.36 to 0.9 above round 13. A taper of 6 squares is short, so the two tapers leave a large empty part of the meeting square.
- With these corners merged (`lib19lf`), `predict` gives 0 rows within 3e-3 of the bar.
- The taper scan of `zone_search.py` keeps one partial taper per vector of 16 column heights for a 9-arm. At step 0.01 over 240 positions it did not end in 18 minutes. A 9-arm needs a coarser step or a cap on the heights.

### 17.4 Control B from a corner of another design

`control --mode B` adds one flush stack to an arm, and the delete beam must take c squares out again. Round 14 passed it on a library corner. Here it starts from the stair-c staircase corner `st9x9-96f7600a` (two 9-arms, f = 0.76, 96 squares, loss 4.6941):

| arm | block move | beam alone at level 9 | final | verdict |
|---|---|---|---|---|
| 1 | 9.83412 + 10.91130 (the start lengths) | 9.97695 + 10.79389 (+0.025 of summed length) | -1.1e-5 and +1.7e-5 | PASS by the block move |
| 2 | 9.67267 + 11.18107 (+0.108) | 9.54486 + 11.30959 (+0.109) | 9.372496 + 11.544858 after 12 hops (+0.172, loss +1.44) | FAIL |

Arm 1 passes only by the block move, which takes out the stack that the control added. The beam alone ends 0.025 of summed length longer. On arm 2 the block move does not give the corner back: the 9 squares nearest the new face are not all squares of the added stack. Our reading, not measured: the staircase corner has squares beside the arm 2 stack that are nearer to it. So the delete route of a corner fails control B on arm 2 of a corner of another design.

Control B on the best two-taper corner (`tt7x7-63f7400a`, arm 1) passes. The block move gives the start lengths back (9.29809 + 8.03062). The beam found a state of the same count at a loss 0.0082 lower, with y0 0.95 longer and x0 0.95 shorter, and the control kept that one.

### 17.5 What to search next

1. **Keep the grow loop, with one square less, into other n.** 862 won 1.397e-05 in the last grow of the round. It came from the stair-c 863 corner with one square less.
2. **Also build the own-n row of a layout that is new in another lane's take.** 554 won 7.742e-05 that way, and the classfill lane took it further. The own-n rows of layouts that the polish quench had already squeezed end near their source: 598 -6.8e-8 of side, 419 a tie, 549 +3.5e-5.
3. **Refresh the bar on the boxes before each chain.** The 554 row moved from 1.6e-3 under the bar to 5.6e-5 over it in 23 minutes. The modules take had landed.
4. **Copy a library by delta.** Copy the last library on the box first, then `rsync` the new one over it. A plain copy of 56 MB took 4 to 6 minutes under load, and one sweep skipped every corner because its deadline passed during the copy. Set a sweep deadline after the copy ends.
5. **Give capped hops minutes.** They run now (section 17.2), but one hop costs 5 to 7 s. 72 hops on 993 and 10 on the 978 corner found nothing under the caps.
6. **Near layouts are a second source of corners.** g11 cut 24 corners from them and gave 10 rows. The best builds tie (977) or end 2.0e-5 over the bar (815). No win yet.
7. **Make the block move take the added stack by its lattice.** Today it takes the squares nearest the face. Control B fails on arm 2 of the stair-c staircase corner, where those 9 squares are not the added stack.
8. **Drop the two-taper corner for 6-arms. Give it longer hops for 7-arms.** On two 7-arms, 1.6 minutes of search took the class 0 corner from 3.77 to 3.61. That is still 0.21 over round 13. On two 6-arms it is 0.36 to 0.9 over round 13. The next design to try is a staircase that both tapers use, since this one keeps arm 2 out of the meeting square. A 9-arm needs a coarser taper scan.

## 18. Round 20 corners (2026-11-13)

Result at 00:59 UTC: 3 n certify against round 18, every frozen `take-*-r19` dir and every live `take-*-r20` dir: 598, 703 and 914. They give 2.614e-04 of score on held, and 2.607e-04 over the other takes. The corners of 703 and 914 come from near layouts that their lanes had written off. Seven more n certified here first, and other lanes then took them further from our files:

- Midm kicked our 601, and modules then built 996 from that 601.
- Polish quenched our 700, and invent kicked our 754.
- Classfill swept a far zone of our 993, and then readers and stair-c went lower. Readers also went 3 shells down from our 993 to 810.
- Soft ran its soft-box search on our 646 corner.
- Classfill took our 995 (certified here at 00:36 UTC) further by 00:50 UTC. Its corner came from the classfill near 996 of round 20, cut by the grow of 00:18 UTC (g18).

The three rows come from the grow of 22:39 UTC (g15). It cut the round 19 takes and the `near/` files of round 19, and 40 s of hops per count followed. The corners after hops build far under their frozen prediction (section 18.2).

Held is now `gather/round18-2026-11-12a.csv` (22.1604820601, gate dir `gate/cand-round18-1112a`). The bar of an n is the smallest of its held score and its scores in every `take-*-r19` dir and every live `take-*-r20` dir (`work/mkbar.py`). Work dir: `<scratch>/bounties-squares/take-corners-r20/work` on boxA, and `<scratch>/squares-corners` on boxC and boxD (removed at the end). The budget was 2 processes on boxC, 1 on boxD and 1 on boxA. boxA rebooted at 22:48 UTC and cut one hop part and the chain. The revived agent ran that part again (`994scq15.C`), and that corner gave 703.

### 18.1 Where the rows come from

`work/grow.sh` cuts every frozen and live take dir. It also cuts each `near/` file, made a take dir of its own by `work/mknears.py`. The g15 grow cut 26 layouts: 11 from round 19 takes and 15 from near layouts. 25 corners came out, and 24 have a start. Each got 40 s of hops on its own count and on one square less. The chain predicted 23 rows within 3e-3 of the bar.

| n | gain on held | corner after hops | first cut from |
|---|---|---|---|
| 598 | 3.134e-05 | `zc8x8-131f9012ag15x.C` (arms 8 and 8, 131 squares, f = 0.9012) | our round 19 598 (corners-r19) |
| 703 | 9.068e-05 | `zc9x9-140f9338ag15x.C` (arms 9 and 9, 140 squares, f = 0.9338) | the stair-c near 994 of round 19 |
| 914 | 1.394e-04 | `zc9x8-92f7440ag15x.C` (arms 9 and 8, 92 squares, f = 0.7440) | the farend near 977 of round 19 |

The farend lane wrote off its 977 near layout of round 19. But the corner of that layout (arms 9 and 8, f = 0.744, 92 squares) builds 914 4.21e-3 of side under the bar, the largest margin of the round. The stair-c near 994 corner gives 703 and, with one square less (139 squares), 993 and 810. The classfill near 996 corner, with one square less after hops, builds 995 1.78e-4 of side under the bar. So a near layout of another lane can hold a corner that is worth more than the layout.

### 18.2 The frozen tables predict new corners too high

A corner table is made at fixed angles (`zone_corner.py tables`). The build then squeezes the whole layout with the LP and fq. `work/stats.py` reads every build of the round:

- Round 20 corners (ours after hops, and the stair-c corners of section 18.5): 100 builds. Built minus predicted side has a median of -1.57e-03. The lowest is -8.46e-03 and the highest +1.41e-07. 16 builds ended under the bar.
- Turned twins (section 18.6): 2 builds. They ended -2.15e-04 and -7.52e-05 of side against their prediction, and none under the bar.

So a row of a hopped corner 3e-3 over the bar is not a lost row. `work/wide.sh` predicts at a wider slack and lists the rows that no build has tried. The box builds take the same slack (`work/bldq2.sh`, item `B LIB ZDIR N SKIP SLACK QUENCH`).

| predicted minus the bar | builds | under the bar |
|---|---|---|
| under 3e-3 | 49 | 14 builds, 9 n: 598 (-7.49e-04), 601 (-2.36e-03), 700 (-7.28e-04), 703 (-2.40e-03), 754 (-1.20e-04), 914 (-4.21e-03), 993 (-1.26e-03), 995 (-1.78e-04), 996 (-1.22e-03) |
| 3e-3 to 6e-3 | 31 | 1 build, 1 n: 646 (-4.47e-03) |
| 6e-3 to 1e-2 | 21 | 1 build, 1 n: 810 (-5.05e-04) |

Wide rows pay rarely, but they pay big. 646 was predicted 3.99e-3 over the bar and certified 1.760e-04 of score. The soft lane then took our corner further. 810 was predicted 7.94e-3 over the bar and built 5.05e-4 of side under it, but the polish lane held 810 lower before our file certified.

### 18.3 More hops on the winners

The corners that built under the bar got 90 s more hops per count (g15w). Then they got 120 s more with another seed (g15x and g15y), and the 646 corner got its own 120 s run (g15v). The hops pay once:

- g15w took 601 from -1.09e-3 to -2.36e-3 of side under the bar, and 996 from -4.5e-4 to -1.22e-3. The 914 and 703 corners kept their states.
- g15x (seed 21) found no better state for the 914 and 703 corners. g15y gave 996 the same side as g15w.
- g15v (seed 22) left the 646 corner at its start loss (3.4350).

So a second hop round can pay, and a third did not. The g18 grow (00:18 UTC) cut the corners of our own built layouts of 598, 703 and 754. It also cut every take layout new since g17. 30 s of hops followed. The corners of our own layouts build their source again: 598 to the side of our take, and 700 to a tie with the polish take. Of its 8 rows within 3e-3, one went under the bar. The classfill near 996 corner with one square less built 995 1.78e-4 of side under the bar. It certified, and classfill took it further. 931 +5.3e-5, 549 +8.2e-5 and 996 +1.7e-4 of side were the nearest misses. The last grow (g19, 00:34 UTC, 20 s of hops) cut 7 corners and gave 5 rows. 912 built 2.2e-5 of side over the bar.

### 18.4 Builds on boxA, the quench on the boxes

A build without the quench takes 20 s to 1.5 min on boxA. The fq quench of a certified file takes 8 s to 530 s, and it must run on a box. So boxA built the rows (`work/bldm.sh`, with `work/mmq.sh` as the queue of its one slot). `work/autoq.sh` sent each build under the bar, or less than 3e-4 over it, to a box. A box loop (`work/bldq.sh`, then `work/bldq2.sh`) reads its queue file before each item: a build, a quench, a hop part or a table part. `work/certloop.sh` copies the box dirs back every 4 minutes and certifies only quenched files.

38 quenches ran on the boxes, and 7 found a certified gain. The largest was on 646. Its fresh wide build was already 1.38e-3 of side under the bar, and the quench took it 3.09e-3 further in 80 s. The other gains are small: 996 1.71e-4, 601 1.27e-4, 811 3.1e-5 and 2.2e-5, 810 1.1e-5 and 700 4e-7 of side. So the quench pays most on a fresh build of a hopped corner.

The first library copy to the boxes ran at about 70 KB/s. 60 MB took more than 9 minutes. With `rsync -z` it took 2 minutes, because a pickled library packs to a fifth. Later libraries went by delta in 20 to 30 s (`work/pushlib.sh`).

### 18.5 Handoffs

- Stair-c hopped its 122-square class 5 corner at f = 0.92 (`zc9x9-122f9200as92d1.C` and states b to d, loss 3.7834). `work/hs92.sh` merged that library into ours with `merge --also` and predicted at 6e-3. It gave 9 rows within 6e-3 and none under the bar. Its builds also end under their prediction, by 6.6e-4 to 3.7e-3 of side. The nearest are 870 (+4.7e-5) and 931 (+5.3e-5 of side over the bar). Our hopped 149-square corner (`zc9x9-149f9170ag15x.C`) builds both n to the same side to 10 digits. Five corners in all built these two n: two of ours from g15, two stair-c corners, and the g19 corner cut from a stair-c near 870. With first and second choices (other far zones and stacks), 870 ends at +4.7e-5 to +4.8e-5 and 931 at +5.2e-5 to +5.7e-5 of side. Every one of these builds holds the far zone `931h.F2` or `931h.F2d`. So that far zone sets the side of 870 and 931, and a better corner cannot move it.
- Classfill swept the far zone F2 of our 996 corner and built 996 with it on boxE. We did not build it twice.

### 18.6 Turned twins of the old near-bar corners

In round 19 the modules lane found that a corner table with free angles (`turn`) predicts lower than the frozen table. We made the turned twins of the 60 hopped corners of every round 17 and round 19 build that ended within 2e-3 of the bar (`work/mkturn.py`). The tables ran in 20 parts of 3 on the boxes, 2 to 4 minutes a part. The control failed. On the 862 row the turned table predicts 29.827028 and the frozen table 29.826979, and the build gives 29.826723. Two twins (`zc9x9-90f8108ah17t.C` and `973ts17t.C`) have broken tables: they predict about 0.04 under the bar on many n. A turned build takes more than 4 minutes on boxA at load 13 to 16, because the corner relaxes at every step of the assembly. 700 tied the bar (+4e-7 of side) and 815 ended 1.8e-5 over it. We stopped the rest.

### 18.7 What to search next

1. **Cut and hop the corners of each new near layout at once.** Two of our three rows came from near layouts that their lanes had written off. 914 (1.394e-04) came from the farend near 977 and 703 (9.068e-05) from the stair-c near 994, both of round 19. The 995 that certified here at 00:36 UTC came from the classfill near 996 of round 20. The same 994 corner with one square less built 993 1.26e-3 and 810 5.05e-4 of side under the bar. Other lanes took both n further from our files.
2. **Sweep the far zone `931h.F2` for 870 and 931.** Five corners build these n to 4.7e-5 to 5.7e-5 of side over the bar, with first and second choices. Every build holds that far zone. Only a better far zone can move them.
3. **Build wide rows when a slot is free.** 100 builds of round 20 corners ended a median 1.57e-3 of side under the frozen prediction. 646 (predicted +4.0e-3) certified 1.760e-04, and 810 (+7.9e-3) built under the bar. But only 2 of the 52 builds over 3e-3 went under, so these rows come after every row within 3e-3.
4. **Quench each fresh build under the bar on a box.** The quench took 646 a further 3.09e-3 of side in 80 s. The other 6 gains were 4e-7 to 1.7e-4 of side, and 31 of the 38 quenches found nothing.
5. **Give the winners one more hop round, then stop.** The second round took 601 and 996 1.3e-3 and 7.7e-4 of side lower. The third found no better state for 914, 703 and 646.
6. **Do not cut corners from our own built layouts.** g18 built 598 and 700 back to their sources. The rows of that grow came from the layouts of other lanes.
7. **Drop the turned twins of old corners.** The control failed, two twins have broken tables, and a turned build takes more than 4 minutes.
8. **Keep a list of wide rows ready for each box.** The boxes ran dry three times this round. Each time the next rows took minutes to compute.

## 19. Round 21 corners (2026-11-13)

Result at 11:53 UTC: 3 n certify against round 19, every frozen `take-*-r20` dir and every live `take-*-r21` dir: 811, 870 and 587. They give 1.673e-04 of score on held. Over the lowest file any other lane certified for the same n, they give 1.84e-06 (811 1.607e-06 over invent, 870 2.31e-07 over family, 587 2.7e-09). 811 and 870 come from kick scans of our own near-miss builds (section 19.4).

Two more n certified here first, and other lanes took them further from our files. 936 (5.077e-05 on held) and 875 (4.627e-05) came from a new corner of two 7-arms at f = 0.99 (section 19.2). The family lane went one shell down from our 936 to 875, and the classfill and modules lanes cut our corners. Classfill holds 936 now (5.575e-05) and modules holds 875 (4.986e-05). So the round 21 total holds about 1.0e-04 that started in this lane but sits in other takes.

Held is `gather/round19-2026-11-12a.csv` (22.1514697138, gate dir `gate/cand-round19-1112a`). The bar of an n is the smallest of its held score and its scores in every frozen `take-*-r20` dir and every live `take-*-r21` dir (`work/mkbar.py`). Work dir: `<scratch>/bounties-squares/take-corners-r21/work` on boxA, and `<scratch>/squares-corners` on boxC and boxD (removed at the end). The budget was 2 processes on boxC, 1 on boxD and 1 on boxA.

The lane ran three times. The first run (01:03 to 01:20 UTC) stopped on a usage limit, and its queues ran on until 03:33 UTC. boxA rebooted at 05:36 UTC. The second run (09:48 to 09:55 UTC) lost its login. The third run picked up the queues of both from `STATE.txt` at 09:59 UTC.

### 19.1 What the first run left

The first run certified nothing:

- The g20 grow cut 7 corners from the new round 20 layouts. After 40 s of hops, the chain gave 11 rows within 3e-3. Four builds tie their source layout (338, 598, 700, 932). The other builds end 3.3e-6 (419), 2.0e-5 (418), 6.3e-5 (995), 8.0e-5 (461), 1.4e-4 (996) and 2.0e-4 (549) of side over the bar.
- The round 20 hopped corners at n that no build had tried (wide rows at 1e-2): 7 builds, 9e-4 to 9.5e-3 of side over the bar.
- The far zone `931h.F2` swept at f = 0.917 and 0.924 (`work/farz.sh`, `classfill.py own`): the sweep cut the loss by 6e-4 and 2.6e-3, but the merge kept no module. 870 and 931 built +4.7e-5 and +5.3e-5 of side over the bar, as in round 20.
- One square less twice (N-2) on the 8 winner corners of round 20 (`work/dn.py`, collected by the second run): 14 corners, no row within 3e-3.

The second run cut 14 corners from the round 21 layouts that had landed since (the g21 grow) and started their hops on the boxes.

### 19.2 The corner of two 7-arms at f = 0.99

The g21 grow cut the modules near layout of 936 (5.3e-5 of side over the bar). Its corner has two arms of 7, 78 squares (class 1) and f = 0.9926. After 40 s of hops it is `zc7x7-78f9926ag21x.C` (loss 3.2572). It built 936 1.553e-3 of side under the bar, with a prediction of 2.2e-4 over. With other far zones it built 875 6.05e-4 of side under the bar.

| n | gain on held | corner after hops | first cut from |
|---|---|---|---|
| 936 | 5.077e-05 | `zc7x7-78f9926ag21x.C` (arms 7 and 7, 78 squares, f = 0.9926) | the modules near 936 of round 21 |
| 875 | 4.627e-05 | `zc7x7-127f9861ag23x.C` (arms 7 and 7, 127 squares, f = 0.9861) | the family 875 of round 21, one shell down from our 936 |

875 changed hands three times in 50 minutes. Our 875 certified at 10:20 UTC (2.046e-05). The family lane went one shell down from our 936 and took 875 lower at 10:21 UTC (3.411e-05). The g23 grow cut that family layout, and its corner after hops built 875 3.6e-4 of side under the family file at 10:38 UTC (4.627e-05). The classfill lane then cut our 127-square corner and built 875 1.2e-6 of score lower at 11:12 UTC (4.747e-05). The modules lane then went 7.8e-05 of side lower again (4.986e-05). So a corner, a shell and a corner again each took the n further.

These n are where the board leads by the most. On the board of 2026-11-09, the side gap was 6.0e-3 at 816, 9.6e-3 at 875, 7.3e-3 at 936 and 9.8e-3 at 997. Our 936 is still 5.7e-3 of side over that board. The wide rows of the two corners do not reach the bar: 816 +2.16e-3, 758 +3.43e-3, 759 +4.05e-3, 874 +5.5e-3 and 935 +7.1e-3 of side. They build 1.5e-3 to 1.8e-3 under their prediction, as in round 20.

Three more searches on this corner class found nothing:

- A second hop round (90 s, seed 21): the 78-square and the 127-square corner keep their states at their own count.
- One square less twice (class 6, `work/dn.py --down 2`): losses of 3.66 to 4.00, against 3.10 to 3.26 for class 1. The rows are 6.7e-3 to 8.2e-3 over the bar.
- `zone_corner.py base --ids` cannot carry these corners to the f of another n. `cmd_base` skips every library corner of tag `z` (the corners of the zone search). `zbase` keeps them at their own f only.

### 19.3 Far zones set the side of 870, 931, 811 and 418

The stair-c lane handed two libraries with its hopped 122-square corner of two 9-arms (`lib-f928h2` at f = 0.928 and `lib-f93h5` at f = 0.93). `work/hlib.sh` merged each into our library and predicted at 1e-2: 11 and 12 rows, none under the bar. Our grows cut the same class 5 corner again from the new 931 layouts of four lanes (g22, g23 and g26).

Every build of 870, 931 and 811 with one of these corners ends 3.8e-5 to 1.3e-4 of side over the bar. Each holds the far zone `931h.F2d` or `811h.F1(d)`. Three corners (g20, g21 and g23) build 418 to the same side, 20.920101743, 2.0e-5 over the bar. So a better corner cannot move these n. Their far zones set the side.

### 19.4 Kick scans of our near misses

At 10:59 UTC the classfill lane wrote that `midm_scan.py --modes lkick,kick --kicks 0.02` finds 6e-5 to 1.1e-4 of side on a fresh `modules.py` build. That run is the control: 2 finds in 6 tries on its 994 build, and 2 in 8 on its 870 build. A fresh build has been squeezed and quenched, but never kicked.

`work/kq.sh` runs that scan on a box for 300 s, from our quenched build of an n. `work/kcollect.sh` copies the finds back, and every find under the bar goes to `cand/` with the json of its start build, so `cert.sh` certifies it. Each scan made 3 to 8 tries in 300 s (80 on the small n 418 and 461).

| n | start over the bar (side) | tries and finds | best find |
|---|---|---|---|
| 811 | +3.8e-5 (the g22 corner with `931h.F2d` and `811h.F1`) | seed 1: 6 tries, 2 finds. Seed 2: 6 tries, 2 finds. Seeds 5 and 6 from the find: 0 of 6, 0 of 8 | 4.58e-5 under the bar: certified, 8.002e-05 on held |
| 870 | +4.6e-5 (the stair-c f928 corner with `931h.F2` and `811h.F1`) | seed 1: 4 tries, 1 find (4.25e-5). Seed 4 from that find: 4 tries, 1 find (1.0e-5 more). Seeds 2, 3 and 5: 0 finds | 6.8e-6 under the bar: certified, 8.727e-05 on held |
| 872 | +4.7e-5 | seed 1: 8 tries, 2 finds. Seeds 4 and 9 from the find: 0 of 7, 0 of 8 | 3.4e-5, still 1.3e-5 over |
| 875 | our certified build, and the fresh g27s build (+1.02e-4) | 6 tries, 1 find each | 2.4e-5 and 2.5e-5, not enough to pass the classfill and modules files |
| 418, 461 | +2.0e-5, +7.2e-5 | 80 tries each, 2 finds each | to the bar to 1e-9 of side, under the 1e-10 score margin |
| 931 | +1.29e-4 | 3 and 6 tries, 1 find each | 8.4e-6 |
| 756, 996 | +2.3e-6, +1.4e-4 | 8 and 4 tries | 8e-8 and 7e-7 |
| 813, 936, 995, 549, 587 | +4e-7, our certified build, +6.3e-5, +2.4e-4, our certified build | 6 to 18 tries each | none |

After our 870 certified, the family and stair-c lanes dropped their 870 rows. So the bar of 870 in `results/corners-r21-2026-11-13.tsv` is the frozen round 20 value, and the 870 kick rows read 2.6e-3 under it.

So the kick pays on a fresh build of a corner of two 9-arms, where the far zones stop the build 4e-5 over the bar. 418 and 461 come back to the side of the bar layout itself, so their bar is the end of that structure. A second scan from a find paid once in five (870 seed 4, and not 870 seed 5, 872 seeds 4 and 9, 811 seeds 5 and 6).

### 19.5 What to search next

1. **Kick every fresh build within 1e-4 of the bar at once, then once more from the find**. 2 of the 14 n crossed the bar (811 and 870, 1.673e-04 on held with 587). Three more found 2.4e-5 to 4.3e-5 of side (872, 875, 870 seed 1). A scan takes 300 s on a box, and 26 scans ran this round (25 logged their end).
2. **Cut and hop the corners of every new layout as it lands**. The g21 and g23 grows gave 936 and 875, both from near or shell layouts of other lanes, within 20 minutes of landing. The other lanes then took both n further from our corners.
3. **Make a carry for zone corners, then hop the two-7-arm corner at the f of 816, 874, 997, 758 and 759**. The board leads by 6e-3 to 1e-2 of side at these n. Our corners at f = 0.99 build them 2.2e-3 to 7.1e-3 over the bar. `zone_corner.py base` skips corners of tag `z`, so this needs a tool change.
4. **Only a new far zone moves 870, 931, 811 and 418**. Five corners of two 9-arms build them to the same few sides. Do not build these n again with another corner of that class.
5. **Drop more hop rounds and N-2 on the two-7-arm corners**. The second round kept both states at their own count, and N-2 gave class 6 losses of 3.66 to 4.00 with no row under 6.7e-3.

## Round 22 (2026-11-13)

The final take holds 0 n. The gain is 0 against round 20 and 0 over frozen round 21 and competing round 22 takes.

The lane first certified 815, 875, 978. Other takes later passed 815, 875, 978.

The first 978 winner was replaced by a newer public file from `areebbb/sis-certified-union-micro-shrink-lb-22-17479`. Its side was 0.00333 below ours.

The c874b carry fed a stair-c 816 build. A family shell step made the 875 start, and its kick scan removed 7.89e-5 of side.

The g33 corner certified 815. Family later improved 815 from our 758 near layout with that same corner.

The control for `base --zones` passed. At its original fraction, the 78-square corner kept both lengths within 9e-15 and remained legal. The default command exported no zone corner. The new flag exported one.

The five carry targets were 816, 874, 997, 758 and 759. The searches used the two-7-arm corners of round 21 at each target fraction. The next pass deleted one square at each new fraction.

There were 107 completed builds. Fresh builds within 2e-4 of the competing side received a sigma 0.02 kick scan. Each raw find received one leg. A box quenched each file before it entered the take.

The fresh family 870 scan removed 2.4103e-5 of side in four tries. Its first find remained 6.64e-7 above the frozen round 21 side. The scan and its leg used the raw finds before the final quench.

New stair-c and twoshort bases went through the corner evaluator and predictor. Large bases used the best representative of each count class, up to four classes. The grow loop also cut take and near files.

[The results table](../results/corners-r22-2026-11-13.tsv) names each completed build and its modules. Work and logs remain in `<scratch>/bounties-squares/take-corners-r22/work`.

Measured next steps:

1. Kick each fresh family shell build within 1e-4 of the best side. The 875 scan found three times in eight tries and removed 7.89e-5 of side. Give each raw find one leg, then quench once.
2. Build wide rows from new strip designs. The 51-square corner won 978 from a prediction 0.007921 above the bar. The full 24-state longrect80 test was dry at 0.01.
3. Keep the carry and grow chain, including near layouts. The c874b carry fed stair-c 816 and family 875. A g33 corner certified 815, and family improved 815 from our 758 near layout.
4. Resume unstarted corners from `work/final/unstarted-corners.tsv`, newest first. The g33 grow certified 815 and fed a lower family 815. There are 13 unfinished near builds and 180 wide builds. There are also 11 unfinished hop parts. First IDs: `hb-hd30aa60-911@boxC`, `hb-hd3946c1-805@boxC`, `hb-hd3946c1-997@boxC`, `hb-hd790d3f-974@boxC`, `hb-hd790d3f-911@boxC`, `hb-hd12f5f0-759@boxC`, `hb-hd4e41f6-805@boxC`, `hb-hd4e41f6-997@boxC`. Full queues are in `work/final/boxC` and `work/final/boxD`.
5. Skip repeated builds that return to a known kicked side. Three 974 scans found nothing in 86 tries. The first two family scans, on 875 and 870, both moved fresh shell builds.
6. Do not repeat the five direct two-7-arm carry batches unchanged. Their 35 direct builds were dry. The c874b corner paid through another far-zone build and a shell step.
7. Keep collection separate from heavy queue preparation. Per-row ssh transfers stretched one cycle to 20 minutes before batching. A new take needs to reach the follow lanes within minutes.

## Round 23 (2026-11-13)

The final take holds 0 n. The gain is 0 against round 21 and 0 over frozen round 22 and competing round 23 takes.

The new 648 construction also fed harvest and polish, then family 597. These receiving takes hold their rows. Their gains are separate from this take.

The predictor control reproduced side 31.767381 for the known 51-square strip corner at n = 978.

The fresh-kick control produced three raw finds at n = 875. Each received its own leg. The final side was 29.984843749646, a reduction of 7.90133e-05.

[The fresh runner](../zone_fresh.py) certifies the best raw layout before one remote fq call. It saves the certified start, its hash and the remote box. A timeout produces no ready copy.

There were 24 packing builds and 195 design predictions. Of these builds, 6 used the LP only on the local box. Production scans made 821 tries and saved 45 finds. The historical control is separate from these counts.

The 648 build ended about 0.003493 of side below its bar. Its initial kicks added 3.38e-7 and its raw-find legs added 3.17e-8.

Initial scans use 240 seconds. The early control and 648 used 180-second legs. Later legs use 90 seconds so more fresh designs can run.

The LP-only control reproduced side 28.843124435653 at 805 and passed floatsafe. This saves a local layout before the remote quench when polishing runs too long.

New handoff geometry is kept in full. Library imports use the exact IDs named in each handoff. Inputs transfer once per box in each collection cycle.

The grow importer reads takes and near layouts without the old 300-square floor. The local slot tests fresh corners at their own count and at N-1. Spare cycles resume unstarted near builds.

[The results table](../results/corners-r23-2026-11-13.tsv) records builds, scans and predictions. Work, source records and logs remain in `<scratch>/bounties-squares/take-corners-r23/work`.

Measured next steps:

First, replace the grow importer's side-only duplicate key with a geometry key. The 650 audit found distinct layouts at nearly the same side.

1. Resume never-started corners before repeating kicked layouts. The first two backlog corners built 648 and 597 below their bars.
2. Kick each fresh family shell within 1e-4 of the best side. Give each initial raw find one leg, then quench its certified file remotely.
3. Run new strip designs promptly and build their best wide rows. Round 22 won 978 from a prediction 0.007921 above the bar.
4. Keep exact handoff IDs, full geometry states and batched transfers. These avoid repeated historical imports and slow per-row copies.
5. Drain every finished quench before freezing the take. The report separates retained rows from lower downstream files.

## Files

| file | what it is |
|---|---|
| [`zone_search.py`](../zone_search.py) | the zone problem, the evaluator, the compactor, the soft search, the moves, the taper enumeration, the controls, and the generator steps with the new zones |
| [`results/zones-2026-11-11.tsv`](../results/zones-2026-11-11.tsv) | every kept zone and corner (2,354 rows since section 12: the 583 corners stored the old way were replaced by 924 rebuilt and new ones): kind, c, f, count, class, length, loss, how found, file |
| [`zone_lowf.py`](../zone_lowf.py) | section 10: the steps around `zone_search.py` at low f (pick one zone per class, length tables, join into the library, the three-zone sum, the slide, the tapers that poke, rows for the table) |
| `<scratch>/bounties-squares/take-zones-r11/work/zones` | one module file per zone with the fields of a far module of `modules.py`, a picture and a row listing (boxA, not in git) |
| `<scratch>/bounties-squares/take-zones-r11` | the take dir: `634.csv`, `995.csv` and `take.tsv` (2 n, gain 1.8506e-04 on held). `work/newlib4` is the library with the 200 new zones, and `work/raw*` and `work/blog*` are the builds and their logs (boxA, not in git) |
| `<scratch>/bounties-squares/take-zones-lowf-r11` | the take dir of section 10: `863.csv`, `921.csv`, `974.csv`, `983.csv` and `take.tsv` (4 n, gain 6.045e-05 on round 11). `work/out` holds every zone of the low-f sweep by f and arm, `work/lib3` is the library with them, and `work/raw*` and `work/blog*` are the builds and their logs (boxA, not in git) |
| [`zone_corner.py`](../zone_corner.py) | section 11: the corner problem with two sliding stacks, the exact lengths, the two-stack LP and its trade curve, the moves and hops, the control, and the generator steps with the new corners. The corners are rows of kind `corner` in the zone table, and module files `zc*.pkl` with a picture each and `corners.pkl` in the zones dir |
| `<scratch>/bounties-squares/take-zones-corner-r11` | the take dir of section 11: 13 per-n csv and `take.tsv` (13 n below round 11, 9 of them below every other take, gain 5.836e-04 over round 11 and every take). `work/` has the search states, the libraries, the builds and their logs (boxA, not in git) |
| `<scratch>/bounties-squares/take-corners-r13` | the take dir of section 12: `921.csv`, `975.csv`, `984.csv` and `take.tsv` (3 n, gain 2.360e-04 on round 12, 5.65e-05 over every other take) |
| `<scratch>/bounties-squares/take-corners-r13/work/zones` | the 620 corners rebuilt at their run's exact f (ids ending in `r`), their tables, and the library `library.pkl` with 1,647 modules (boxA, not in git) |
| `<scratch>/bounties-squares/take-corners-r13/work/zones-s`, `zones-l`, `zones-t` | the corners of the round 13 search (ids ending in `s`), the low-f corners (`l`), and the hops on the 984 corner (`t`), each a library with them. `raw-*` and `blog-*` hold the builds and their logs (boxA, not in git) |
| `<scratch>/bounties-squares/take-corners-r14` | the take dir of section 13: `take.tsv` with no row. The polish lane holds 551, 600, 874 and 419 lower from our builds (7.50e-05 on round 13) |
| `<scratch>/bounties-squares/take-corners-r14/work/zones-u1`, `zones-u2`, `zones-u3` | the corners of the round 14 search: the 9 x 8 states and the first part of the sweep (`u1`), the rest of the sweep and the deep hops (`u2`), the capped hops (`u3`). Each is a library on the round 13 corner library. `lib-u2-14b` is `zones-u2` merged into the modules lane's `lib14b`. `raw-*` hold the builds, `logs/` the logs, and `from-boxC/` the run files of boxC (boxA, not in git) |
| `<scratch>/bounties-squares/take-corners-r15` | the take dir of section 14: `921.csv`, `974.csv`, `983.csv`, `984.csv` and `take.tsv` (4 n, 4.500e-05 on round 14) |
| `<scratch>/bounties-squares/take-corners-r15/work/zones-v`, `zones-w` | the corners of the round 15 search (ids ending in `v` and `w`): the capped hops, the rest of the sweep and 931h.C at 142 (`v`), and the capped 983 corner (`w`). `lib15` is the modules lane's `libd` with `zones-u1` and `zones-u3`, and `lib15w` and `lib15v` add `zones-w` and then `zones-v`. `raw-*` hold the builds, `nbq-back` and `nbq3-back` the quenched copies of earlier builds, `qmap.tsv` the build behind each copy, `logs/` and `nb/` the logs and run files (boxA, not in git) |
| `<scratch>/bounties-squares/take-corners-r16` | the take dir of section 15: `600.csv`, `703.csv`, `932.csv` and `take.tsv` (3 n, 7.495e-05 on round 15) |
| `<scratch>/bounties-squares/take-corners-r16/work` | `qlist.py` and `qmap.tsv` (the 104 builds of the quench and their sources), `qa` and `qb` the quenched copies, `cert.sh` and `certloop.sh` (the certification every 8 minutes), `boxC` and `boxD` the run files and logs of boxC and boxD (`raw-b` the near-bar builds, `raw-x` the builds with the hopped corners, `out-cap`, `out-x`), `boxDx/zones-x` and `boxDx/lib16x` the 12 hopped corners and the library with them (boxA, not in git) |
| `<scratch>/bounties-squares/take-corners-r17` | the take dir of section 16: per-n csv and `take.tsv`, and `STATE.txt`, the log of every queue the four runs of this lane started |
| `<scratch>/bounties-squares/take-corners-r17/work` | `cert.sh`, `certloop2.sh`, `certloop3.sh` and `handoff_new.py` (the certification every 5 to 7 minutes, with a handoff line per new row), `chain3.sh` (the chain with `predict` at slack 3e-3), `mkres.py` (the results table), `takes3` to `takes7` (the take layouts of 17:47, 18:10, 18:50, 19:10 and 19:35 UTC), the libraries `lib17h` to `lib17p`, the hopped corners `zones-g`, `zones-q`, `zones-v`, `zones-x`, `zones-z` and `zones-p`, the hop runs `out-g3` to `out-g7`, and `boxC`, `boxD` and `boxE` (the run files and logs of boxC, boxD and boxE) (boxA, not in git) |
| [`results/corners-r17-2026-11-12.tsv`](../results/corners-r17-2026-11-12.tsv) | every corner build of round 17: corner, far zones, predicted and built side minus the bar, box, log, and the certified score where our take holds the row |
| `<scratch>/bounties-squares/take-corners-r19` | the take dir of section 17: per-n csv and `take.tsv`, and `STATE.txt`, the log of every queue of this lane |
| `<scratch>/bounties-squares/take-corners-r19/work` | `grow.sh` (snapshot the take dirs, `modules.py grow`, `base`), `gchain.sh` and `rows.py` (chain, rows without or with `--own`, builds), `cert.sh`, `take.sh`, `mkbar.py` and `handoff_new.py` (the bar and the certification against round 17 and every take dir), `capctl` (the caps control, its logs and control B on the stair-c corner), `nears11` (the near layouts as take dirs), the library `lib19g14` with every grow of the round (the earlier ones were removed), `boxA` (the boxA hops and chains of g11 to g14, and `lib19g14z` with the g14 hops), and `boxC`, `boxD` (the run files and logs of boxC and boxD) (boxA, not in git) |
| [`results/corners-r19-2026-11-12.tsv`](../results/corners-r19-2026-11-12.tsv) | every corner build of round 19: corner, far zones, predicted and built side minus the bar, box, log, and the certified score where our take holds the row |
| `<scratch>/bounties-squares/take-corners-r20` | the take dir of section 18: per-n csv and `take.tsv`, `STATE.txt` (the log of every queue of this lane), and `near/` (quenched builds less than 3e-4 over the bar) |
| `<scratch>/bounties-squares/take-corners-r20/work` | `grow.sh` (with the near layouts and `EXTRA` take dirs), `chaing.sh`, `wide.sh` and `hs92.sh` (chain, wide predict, the stair-c handoff), `bldm.sh` and `mmq.sh` (the boxA slot), `bldq2.sh`, `pushq.sh`, `pushlib.sh` and `autoq.sh` (the box queues and the quench), `cert.sh`, `certloop.sh`, `take.sh` and `mkbar.py`, `stats.py`, `mkres.py`, `mkturn.py` and `cmpturn.py`, the libraries `lib20g15` to `lib20g19z` and `lib20s92`, the hopped corners `zones-g15` to `zones-g19`, and `boxC`, `boxD` (the run files and logs of boxC and boxD) (boxA, not in git) |
| [`results/corners-r20-2026-11-13.tsv`](../results/corners-r20-2026-11-13.tsv) | every corner build of round 20: corner, far zones, predicted and built side minus the bar, box, log, and the certified score where our take holds the row |
| `<scratch>/bounties-squares/take-corners-r21` | the take dir of section 19: per-n csv and `take.tsv`, `STATE.txt` (the log of every queue of the three runs), and `near/` (quenched builds less than 3e-4 over the bar) |
| `<scratch>/bounties-squares/take-corners-r21/work` | `grow.sh`, `chaing.sh`, `chainw.sh`, `wide.sh`, `hlib.sh` and `dn.py` (grows, chains, the stair-c libraries, one square less twice), `bldm.sh`, `mmq.sh`, `bldq3.sh`, `pushq.sh`, `pushlib.sh` and `autoq.sh` (the slots and their queues), `kq.sh`, `kqm.sh` and `kcollect.sh` (the kick scans and their finds), `cert.sh`, `certloop2.sh`, `take.sh`, `mkbar.py`, `gains.py` and `mkres21.py`, the libraries `lib21` to `lib21g28`, the hopped corners `zones-g20` to `zones-g27s`, `kickback` (the kick finds), and `boxC`, `boxD` (the run files and logs of boxC and boxD) (boxA, not in git) |
| [`results/corners-r21-2026-11-13.tsv`](../results/corners-r21-2026-11-13.tsv) | every corner build and kick scan of round 21: corner, far zones, predicted and built side minus the bar, box, log, and the certified score where our take holds the row |

## Summary

- The board's loss does not depend on the count class at f from 0.90 to 0.94 (8.60 to 8.81 in seven classes). Ours does (8.81 to 9.68). So the zones or corners exist.
- The zone search passes its control: the library's zone of 29 squares comes back to 4.156936 from a shaken start (+4e-12) and from the zone of 37 squares (+3e-10).
- A closed-form enumeration of tapers returns the library's best far zone at f = 0.70, 0.83, 0.93 and 0.95, and gives a far zone for every class of arms of 8, 7 and 6. The table has 1,052 zones: 444 for an arm of 8 at 19 values of f, 334 for an arm of 7 and 274 for an arm of 6 at 16 values of f.
- 5 mod 8 is special at f = 0.93 because three contacts of that taper close at the same stack position to 0.044 (4.15648, 4.15694 and 4.11278). Every other count moves one contact by a whole step.
- At f = 0.93 the best new 8-arm class is 7 mod 8 at a loss of 3.12, which is 0.41 above 2.71. The go line of 0.3 is not met as it was written. The kill line's 40 CPU-minutes of hops per class were not spent: the hops had 26 CPU-minutes in all and found nothing.
- With 200 new zones in the library the generator predicts one n below held, 634. Of 12 builds, 634 and 995 certify, with a gain of 1.8506e-04 on the total. 340 ends at the side of held. 552 and 854 end 0.00015 and 0.0002 of side above held.
- Next: the two near misses with a taper made at their own f, then the corner by the same enumeration and sub-stacks at their own tilt.
- Round 13 rebuilt the corner table at each run's exact f. 0 of 620 corners are illegal at their stored f, against 452 of 583 stored the old way. The new `check` command tells the two apart.
- Hops on one 7 x 9 library corner at its own count (110 squares) cut its loss from 2.902 to 2.477. It wins 984 and 921. With 975, 3 n certify for a gain of 2.360e-04 on round 12 and 5.65e-05 over every other take.
- At low f the go line is not met (two 7-arms 3.40 against 2.2, two 6-arms 1.35 against 1.26). The strong control and control B on a corner of a 9-arm still fail. The far-zone delete route on a 9-arm passes its control B with a block move.
- Next: hops weighted by the loss on every corner of arms of two sizes, then the 4 unbuilt choices (section 12.7).
- Round 14 weighs the two corner lengths as the loss does, in the hops, their LP and the delete beam. 29 of 48 corners of arms of two sizes got 150 s each, and 6 fell by more than 0.005 squares. A lower loss often shortens the length that the layout does not need, so 874 and 984 did not gain.
- The corner of 600 after weighted hops wins 551, and 600. Builds of round 13 choices win 874 and 419. The polish lane holds all four lower from our builds, 7.50e-05 on round 13.
- Control B of the corner delete beam passes with the block move (-2.3e-11). At f = 0.93 a corner of 995h.C with 118 squares (1 mod 9) is 0.046 below the library.
- Next: hops under the caps of each near-bar choice, and builds of every near-bar choice (section 13.6).
- Round 15: hops under the caps of 983 bring a 9 x 7 corner of 146 squares under both caps, and it wins 983 by 1.260e-05. The polish quench works only from the certified file. From there it takes earlier corner builds of 921, 984 and 974 below the bar. 4 n certify for 4.500e-05 on round 14.
- Next: quench every build up to 1.5e-3 above the bar from its certified file, and give the capped hops more time per pair (section 14.7).
- Round 16: the corners of the new layouts of round 15 got 50 s of hops each. Builds with them win 600, 703 and 932, for 7.495e-05 on round 15. Each build ends 6e-4 to 7.5e-4 of side under the bar, well under its prediction. The near-bar builds win 863 and 974, which the polish lane took further. The quench of 104 old builds and 10 capped pairs find nothing below the bar.
- Next: hop the corners of every new layout as it lands and build every n they predict within 1.5e-3 (section 15.6).
- Round 17: the corners of other lanes' new layouts, cut and hopped within the hour with one square less, win n outside their own layout. The six grows after the first won 10 n between them. At 20:05 UTC the take holds 8 n for 5.798e-04 on round 16, and other lanes took 7 more of our files further.
- Next: cut and hop the corners of every new layout as it lands, always with one square less, and predict at slack 3e-3 (section 16.9).
- Round 19: corners cut from the new layouts of other lanes and hopped within the hour win 862 (one square less, another n), 598 and 700. 554 certified first, and the classfill lane took it further. `search --caps` made no move because the hops stopped when the start fit its caps. It runs now. The low-f corner of two tapers gives every class of two 7-arms a corner at 3.61 to 4.30, 0.21 over the hopped best, and no row. Control B from a staircase corner fails on arm 2.
- Next: keep the grow loop with one square less, build own-n rows of layouts new in another take, and refresh the bar before each chain (section 17.5).
- Round 20: corners cut from the near layouts of other lanes and hopped win 914 and 703, and our round 19 598 corner wins 598. 3 n certify for 2.614e-04 on round 18 and 2.607e-04 over the other takes. Seven more n certified here first, and other lanes took them further from our files. Hopped corners build a median 1.57e-3 of side under the frozen prediction, so a row up to 1e-2 over the bar can still win (646, 810).
- Next: hop each new near layout at once, sweep the far zone `931h.F2` for 870 and 931, and build wide rows in free slots (section 18.7).
- Round 21: kick scans (`midm_scan.py --modes lkick,kick --kicks 0.02`) of our own fresh builds, 4e-5 of side over the bar, win 811 and 870. With 587, 3 n certify for 1.673e-04 on round 19. A new corner of two 7-arms at f = 0.99, cut from a modules near layout and hopped, won 936 and 875 here first. The family, classfill and modules lanes then took both n further from our corners.
- Next: kick every fresh build within 1e-4 of the bar at once, and keep the grow loop. A carry for zone corners would open the rows at f = 0.99 (section 19.5).

## Round 24 (2026-11-13)

The take retains 2 rows. It gains 0.000168715360241 against submitted round 23-b. Against scientific round 23-a, the gain is -2.30102301702e-05. The source rules changed during the round, so both comparisons matter.

At 20:05 UTC, the main lane held 20 counts whose sources reach Samanyu. A row without that seed ancestry can qualify against round 22. A row with that ancestry must beat scientific round 23-a. Each retained source and licence names its seed counts or says none recorded.

The intake now compares positions and angles under all eight symmetries of a square. It ignores row order and translation. Equal side lengths no longer cause a different layout to be skipped. Fresh kick inputs use the same geometry check.

The 650 control rejected the known duplicate and admitted a different layout at almost the same side. It rejected a changed square angle. The tolerance is 2e-9.

The full-library predictor control reproduced side 31.767381 for the 51-square strip corner at n = 978. The independent-taper library passed the same control before production. The remote quench control reduced n = 2 from side 2.5 to 2.0000000000502034.

The source control rejected the excluded 639 public donor, the excluded 801 source and a layout without metadata. It admitted candidate 935 and the traced 799 near layout. The source checks read both JSON sidecar formats and the near ledgers. Frozen take files remain unchanged.

A temporary 735 row exposed a missed bare donor path. That path reaches Samanyu seed 365. Its scientific gain was below 1e-10, so the row was withdrawn and its near sidecars corrected. The new traversal and regression control identify seed 365. Unnamed 802 ancestry remains excluded.

The walk stores completed source closures to avoid repeating them. A walk exceeding 15 seconds remains unproved and is excluded. Current-round donors remain live reads until their complete source closure is saved.

New corners run at their own count and with one square deleted. Builds from new predictions precede pending far-zone tables. The driver checks for completed results during source scans and between local steps. Fresh family shells receive a kick scan and one continuation per raw find.

The workers returned 31 builds and 53 production receipts from certified-file quenches. The 36 prediction files contain 182 rows. The 89 scans and continuations made 1396 tries and saved 57 raw finds. Controls are excluded from those counts. The near folder holds 172 layouts.

Fresh shells first supplied 646 and 699 here. The 646 file gains about 9.88e-8 of score. The 699 start lost about 0.00103 of side. Invent then improved it from this lane's file, so 699 is excluded from our retained count.

The clean 550 build uses the public 650 corner with independently enumerated far zones `z8-37f930.F1` and `z8-45f900.F1d`. Its first certified side is 23.9045563371706. It gains about 0.00016861656 against submitted round 23-b. It is about 0.00002310903 of score above scientific round 23-a.

Clean 503 built side 22.895329151374295, about 0.001742 above the eligible bar. Clean 599's first scan stopped at 24.916958770438313, about 1.27e-6 above its eligible bar. The second 599 seed returned side 24.916958770438, with 0 raw finds and 0 continuations. The wider 648 kick returned side 25.903777124801, with 1 raw finds and 1 continuations. The second 550 seed returned side 23.904556337171, with 0 raw finds and 0 continuations. The clean scan across the other 17 held counts returned only 597 and 648. Their builds stayed about 0.001947 and 0.000944 of side above their eligible bars.

The first two unused 650 corners built 758 within 7e-6 of the scientific side. One kick scan and its continuation reached a tie. A 911 build started about 3.24e-5 above the bar and stopped about 2.03e-5 above it.

Every retained row passes floatsafe at 2.2e-11 and a remote fq call from its certified file. Its score beats its applicable source-group bar by more than 1e-10. It also beats every eligible live take for that count. The final check verifies the certified-start hash and walks the recorded source again.

Next, run these in order:

1. Follow the measured clean corner and taper combinations. The independent taper pool has 1519 zones and recovered 550 under the submitted bar.
2. Kick fresh family shells before polished copies. The 699 scan lost about 0.00103 of side, and 646 crossed the bar by 2.51e-6.
3. Resume source-resolved corners that never started. Their exact jobs are in `work/unfinished-jobs.json`. Keep new geometry ahead of repeated 758 floor scans.
4. Build promising predictions before making more tables. Near-bar rows waited while only three builds had finished. The changed priority moves those builds forward.
5. Keep full source closures and explicit seed counts. The 735 correction shows why a bare donor path needs the same walk as a named take.

[The results table](../results/corners-r24-2026-11-13.tsv) records every returned build and certified-file quench. Work, source records and logs remain in `<scratch>/bounties-squares/take-corners-r24/work`. Both remote scratch directories were copied and checked by SHA-256 before removal. The final process audit found no lane processes.
