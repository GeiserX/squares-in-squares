# seamcell (T4)

Periodic seam-cell solver for the two-grid band regime, from `../../TOOLS-PLAN-2026-11-09.md` T4.

## The model

Two upright grids, one anchored at the bottom-right corner and one at the top-left, with a tilted seam on the diagonal between them. Only their relative position matters for an infinite seam, so the cell frame is:

- G1: cells `[ox+i, ox+i+1] x [j, j+1]`, kept when `i - j >= D`
- G2: cells `[a, a+1] x [oy+b, oy+b+1]`, kept when `b - a >= 0`
- k tilted squares, repeated under the translation `(p, p)`

Moving the picture by (1, 0) turns `(d1, d2)` into `(d1 - 1, d2 + 1)`, so only `D = d1 + d2` matters. In a box of side `m + f` the grids fit when `ox, oy <= f`. That box holds `m^2 + (1 - D) m + O(1)` uprights, so the net gain per diagonal step is

    g = k/p - (D - 1)

The leader's m + 0.794 family fits `n - m^2 = 0.82 m - 3.9`. Our 498 is `D = 3`, 8 squares per 3 steps, `g = 0.667`.

## Files

| file | what it does |
|---|---|
| `kernel.py` | numba penalty energy and gradient (squared SAT penetration), periodic images, lattice obstacles |
| `cert.py` | independent numpy SAT clearance of a cell. It shares no code with `kernel.py`. |
| `brute.py` | third check: an explicit patch (21 periods plus the grid cells), pairwise intersection area by convex clipping |
| `nlp.py` | fixed-line NLP after Evan Daniel's `nlpdesc.py` (MIT), with SLSQP in place of IPOPT. It minimises `f = max(ox, oy)` and restores feasibility when the penalty stalls. |
| `seamcell.py` | CLI: `mine`, `fold`, `cell`, `perturb` |

A cell only counts when all of these hold: the energy is 0 at side 1 + 1e-7, `cert.py` reports a gap > 0, and `brute.py` reports an overlap area of about 1e-13 or less.

## Usage (boxF scratch `<scratch>/seamcell`, venv from uv)

    seamcell.py mine --in 498.csv --p 1..6 > mined.jsonl
    seamcell.py fold --in 498.csv --p 3 --f 0.83 --grow --minf
    seamcell.py perturb --cell cell.json --f F --starts 48
    seamcell.py cell --f 0.7941 --p 1..6 --D 1..4 --gain 0.80 --gmax 1.0 --starts 200 --workers 20 --minf
    brute.py cells.jsonl

Set `OPENBLAS_NUM_THREADS=1`. Without it, each pool worker spawns BLAS threads, and the boxF went to load 230.

## Traps found while building

- **Images must be centred on the real offset.** Squares drift many periods apart along the seam. With images only at `|t| <= 2`, the first search reported six "cells" with gain 1.0 that overlapped by area 0.33 to 1.0. `brute.py` caught them, and all three image loops now centre on `round(du / 2p)`.
- **The penalty relaxer stalls within about 1e-3 of a jam** (E about 3e-8, overlap 5e-5) even from the exact solution, so every near-feasible start goes to `nlp.polish`.

## Results

See `../../results/seamcell-runs.tsv` and `../../docs/LANE-LOG.md`.
