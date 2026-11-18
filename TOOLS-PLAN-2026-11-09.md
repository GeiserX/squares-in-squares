# Squares in Squares: our own tool build plan (10 days, design only)

Nothing here gets started on a box. The lane owns boxB, boxA, boxF and boxD, and it decides when each tool runs. Everything written goes under `tools/`, and runs happen from scratch copies on the boxes. Nothing is ever copied into Evan's clone.

## 0. What I checked before planning (two critiques were out of date)

- **`floatsafe.py` already enforces a 2e-11 minimum clearance.** One critique said it did not. The setting is `MIN_CLEARANCE = 2e-11` at `floatsafe.py:32`, and the dilation loop only accepts a puzzle when `clearance(fr) >= MIN_CLEARANCE` and the pandas re-read passes (`floatsafe.py:94`). It landed in commit `6f0f635` (2026-11-09 00:40Z). The boxA copy has the same SHA-256 (`68a15ca1…`). Caveat: the submitted file `gather/floatsafe-2026-11-08.csv` scored at 00:31Z, before that commit. So the Kaggle score 22.2223 does not yet prove the 2e-11 path.
- **Evan's `packer` is now built on boxA.** `ext/evand/search/packer/target/release` holds `anneal`, `fq` and `harden`. The "release dir is empty" premise is gone. The FTMC positive control is the lane's next step, not something blocked.
- **The real family leverage is small.** Several designs assumed a solved island carries to many n. Two critiques broke that assumption.
  - Families whose fractional parts match to 1e-6 or 1e-9 hold only 0.011–0.012 of the 0.17 gap. That covers 791/908, 842/901/962, 530/577 and 902/963.
  - The figure "254 families, top 30 hold 34%" only appears when fractional parts are rounded to about 1e-3.
  - A permutation null shows no family excess over chance at 2e-4 to 1e-3.
  - The "m + 0.794 family" members differ in the 4th digit. They are different packings, not one structure rolled out.
- **What does survive:** in that 0.794 group, the leader's count fits n − m² ≈ 0.82·m − 3.9, with residuals under 0.3 over 6 members. A count that grows linearly with m is what a periodic seam produces, with each n relaxed on its own. That is the only evidence behind a new constructor.

## 1. The dependency everything rests on (the lane's job, not ours)

**FTMC / compose2 positive control.** Remove one square from 498 or 593, then ask FTMC to fit n again at the same side. After that, run 2 CPU-hours each on 498 and 593 at the side halfway between ours and the leader's. The research expects 0.04–0.08 from this. Every tool below either feeds FTMC, competes with it at equal CPU, or does both. If FTMC fails its control, only tools T1, T2 and T4 keep their value.

## 2. Kept tools, in build order

Common packing format, the same for every tool:
- One packing is `cand/<tool>/<n>/<utc>-<seed>.txt` in Evan's `n s / x y deg` text format.
- Beside it sits `<same>.json`: `{n, side, side_dec, tool, method, parent, source, licence, cpu_s, box}`.
- Results append to `results/<tool>-runs.tsv`. Each row: `tool, n, target_side, start, seed, wall_s, cpu_s, count_reached, side_out, metric_reason, kaggle_safe`.
- To move packings into Evan's `pk` store, run `kaggle_import.py` / `pk.py import` with a separate `PK_STORE` path. We never write into his own store.
- Nothing counts until T2 passes it.

### T1. `targets.py`: fresh board, exact families, work list (0.5 day, agent A, day 1)

- **What it does:** refreshes the per-puzzle board on demand through the `harvest_fetch.py` path. For every n it writes `targets-<date>.tsv` with:
  - our side and the target side L*
  - squares short (largest n' < n whose side still fits under L*)
  - the fractional family keyed at 1e-9, with its member count
  - the team holding the best
  - `mpmath.pslq` on the sides of exact multi-member families only, over the basis {1, √2, √3, √5, √7}, max coefficient 40

  It also writes `worklist.jsonl`, ordered by gap. In each exact family the smallest member comes first (299 for the 0.794 group, 791 for 791/908). The list also carries the k = 1 band, n = 401, 442, 485, 530, 577, 626, 677, 730, 785, 842, 901, 962, because Chris Deotte holds those with FTMC.
- **Language and core:** Python 3.12, pandas, mpmath.
- **Runs on:** anything light. Not the laptop if it needs the 4.7 GB harvest; use boxA, where `harvest/` sits.
- **Acceptance test:**
  - It must reproduce the checked numbers: gap 0.1704 on the 11-07 board, the squares-short table 305 / 115 / 2, 971 at the top with 0.00135, and the exact-family share of about 0.011–0.012 at 1e-9.
  - Red first: feed the 11-07 board with n = 498 deleted. The output must flag 498 as "missing target" and must not show a zero gap. A board in a changed schema must exit non-zero, never hand over an empty map.
- **Go/no-go:** go once the numbers match. No gain metric applies.
- **Expected gain:** 0 direct. It points every engine at today's frontier instead of the stale 11-07 sides.

### T2. `gate.py`: last check before any file leaves us (0.5 day, agent A, day 1)

- **What it does:**
  1. Assembles the best certified packing per n.
  2. Runs `floatsafe.py`, then `pdscore.py`, the pandas path into the unchanged `kaggle_metric.score`.
  3. Runs an independent float64 SAT minimum-gap check per pair, using a grid hash for candidate pairs and Evan's `satcheck_f64.py` logic as the second checker. It must report every n at ≥ 2e-11.
  4. Diffs per n against the last submitted file.

  It refuses the file (exit 1, writes `RED`) on any n not ok, any per-n regression or a higher total. It writes `candidate.json` with the SHA-256, the total, which n moved and through which tool, and a licence summary. It prints the submit command and never submits. It runs on demand, not on a cron.
- **Language:** Python.
- **Runs on:** boxA at nice 19, capped at 4 processes.
- **Acceptance test, watched red first:**
  - `gather/assembled-2026-11-08.csv` (the file that scored 25.974) must go RED and list the ~190 exact-contact n.
  - A copy of the floatsafe file with one n = 498 coordinate nudged 1e-12 toward a neighbour must go RED on clearance only.
  - A copy with n = 10 made 0.01 worse must go RED with that one regression line.
  - Only after those: `floatsafe-2026-11-08.csv`, re-run through today's 2e-11 floatsafe, must go GREEN at 22.2223365 ± 1e-6.
- **Go/no-go:** all four outcomes as stated. The only real proof is one Kaggle submission of a gate-green file. That is Sergio's call, and it is worth making soon, because the 2e-11 path has never been scored on Kaggle.
- **Expected gain:** 0 in packings. It is insurance against a repeat of the 3.75-point loss and of Samanyu's 1e-12 rejection.

### T3. `insbench`: the bench that kills engines in hours (0.75 day, agent A, days 1–2)

- **What it does:** produces fit-n-again controls at n ≥ 300 (498, 593, 791, 908, 544, 971) in three classes:
  - (a) drop one square, then scatter at a fixed side: jitter σ 0.02 and 0.5°, then an `fq` quench
  - (b) drop one, `fq`-squeeze to the side halfway between ours and L*, then ask for n back. This is the class closest to the real one-short state.
  - (c) negative controls: area-infeasible sides (side² < n) and L* − 0.05 on 498

  It runs any engine through the command template `'cmd {in} {side} {out}'` with a CPU budget. It appends to `results/insbench.tsv` and certifies results through T2's check. It reuses `pk/eventbench.py` conventions and `pk/bandit.py` if any weighting is needed. There is no new scheduler, no optimal-transport census and no Thompson sampler.
- **Language:** Python.
- **Runs on:** boxB (10 cores). 100 controls at 120 s each is about 25 minutes of wall time on 10 cores.
- **Acceptance test:**
  - Red first: on class (a), the trivial "put the deleted pose back" engine must score about 100% before scattering and about 0% after. If it still scores 100% after scattering, raise σ until it fails.
  - `fq` squeeze run as an engine must score 0% on class (c).
  - Then the first real engine: Evan's `mcmin` reinsert and `removal_ctl.py` style.
- **Go/no-go:** the bench is trusted once the trivial engine goes from 100% to about 0% and no engine passes class (c). After that, any engine below FTMC's measured rate per CPU-hour on class (b) is not run on real targets.
- **Expected gain:** 0 direct. It decides which of T4, T5 and FTMC gets CPU.

### T4. `seamcell`: periodic seam-cell solver and band constructor (the one real bet; agent B; 2-day go/no-go, then 2–3 days to build all n)

This merges seamc (design 1) and seamcell (design 4). The caps, knapsack DP, compatibility matrix and Rust Benders MILP are dropped from the first build.

- **What it does:** the band regime is two upright corner grids with a tilted seam between them. Both grids repeat under the translation (p, p), so the seam is periodic. seamcell solves one period cell of the seam:
  - a fixed number of tilted squares in a cell of p diagonal steps, p ≤ 6
  - periodic images along u = (x+y)/√2
  - the staircase uprights of both grids as fixed obstacles
  - removed diagonals d1, d2 ∈ 1..4, with the grid phases left free (our 498's uprights sit at x mod 1 = 0.315–0.318)

  Objective: the lowest f for a given net gain per step, or the most squares per p steps at a fixed f.

  The full packing for each n is built outside seamcell:
  1. tile the cell along the diagonal
  2. fill the ends and the uprights with compose2 / `gen.mis_fill2` / `fillfast` exact fill
  3. polish with `fq`
  4. pass T2
- **Language and core:**
  - Python prototype on Evan's fixed-line NLP (`nlpdesc.py` through `ipenv.sh` / cyipopt), with the periodic images added.
  - Separator lines are re-picked at every NLP point, as `nlpdesc` does, plus 200 multistarts from random angles and from the folded seam of our own packings.
  - `seamcell mine` uses the `bandflip` cluster finder and folds our 498 / 593 / 791 seams modulo (p, p).
  - Port to Rust only if a cell beats our seam and the solves turn out to be the bottleneck.
- **Interfaces:**
  - `seamcell mine --in state/best/498.txt --p 1..6 > mined.jsonl`
  - `seamcell cell --f 0.70:0.85 --p 1..6 --d 1..4 > cells.jsonl`. Each cell record: `{p, k, d1, d2, f_star, gain_per_step, rigid, coords}`.
  - `seamcell build --cells cells.jsonl --n 299,454,498,544,747,803 --out cand/seamcell/`. This hands pieces to compose2 and warm starts to FTMC.
- **Runs on:** boxB during development; any box once the lane grants CPU.
- **Acceptance tests:**
  - Day 1, red first: fold our 498 seam with the period deliberately wrong (p = 5 when the motif is period 3). The solver must not report a cell at our f. Then fold at p = 3. It must rebuild 8 squares per 3√2 period, at a gain per step at or above ours and at f ≤ 0.8231.
  - Day 2, the test that can actually fail: perturb the mined cell (angles ±5°, positions ±0.1) and require the multistart to recover it. Then search fresh at f ∈ [0.75, 0.85] for a cell with net gain ≥ 0.82 squares per step, which is the leader's fitted slope.
- **Go/no-go at the end of day 2:**
  - Go: a rigid cell reaches ≥ 0.80 gain per step at f ≤ 0.794 + 1e-4.
  - Stop: no cell reaches 0.75 gain per step after one box-day of compute.
- **If go, days 3–5:** build 299 end to end first (the smallest member, target 17.7936 against our 17.8010), then 498 and 544. Success is a certified side below ours. Then fit the same law on the 0.6059 group, where (n − m²)/m ≈ 0.25, and sweep f over 0.55–0.90.
- **Second kill rule:** if 2 CPU-days over f ∈ [0.6, 0.95] produce no certified n ≥ 300 below our side, compared against FTMC on the same n, stop.
- **Expected gain:** 0–0.05, expected value about 0.01, with a 25% chance a useful cell exists at all. It is the only tool that can close part of the Cats-only gap, because nothing in the lane or in Evan's repo builds a periodic seam cell. `quadrant_lp`, `seam_1d` and `SEAM_W1` are bounds, not constructions.

### T5. `winlns`: window ruin-and-recreate at a fixed side (1.5 days, agent C, days 2–4, starts only after T3 is trusted)

- **What it does:** cuts a window of radius 2–4 out of the seam or island region (8–40 squares) and freezes everything outside it. It then re-creates k + 1 squares inside the window. Window centres come from familymap, `pk/bands.py` and `shove/island.py`. The re-create step:
  - samples an upright count u from k_up − 2 .. k_up + 1, so the staircase can lose a step. This is the one new move.
  - fills the uprights exactly with `fillfast`
  - places the tilted squares with `fill_resolve` keep/kick
  - relaxes with `fq` at the full side, then a one-ring release
- **Language:** Python orchestration over Evan's MIT pieces. No new Rust crate, no CMA-ES unless L-BFGS seeding plateaus, and no SQLite boundary bank: a window win at one n goes to T6.
- **Interface:** `winlns --in n.txt --n N --side L --windows auto --restarts R --cpu-budget S --out cand/winlns/N/`
- **Runs on:** boxF (Intel WSL, 12 threads) or boxB, as the lane allows.
- **Acceptance test:**
  - Red first: the unscattered "delete one island square" control cannot fail, because the hole is still there. Run it only to confirm the plumbing; it must pass 5 of 5.
  - The real control is T3 class (b) on 498 / 593 / 791.
  - Negative: k + 2 at side − 0.05 must fail.
- **Go/no-go:** head to head with FTMC through T3 at equal CPU, 2 CPU-hours each on 498, 593 and 791. Kill it if its fit-n-again rate per CPU-hour is below FTMC's.
- **Expected gain:** 0.002–0.01 on top of FTMC / compose2.

### T6. `donorfeed`: initial packings across n, plus win propagation (0.5 day, agent C, day 2)

- **What it does:** for each target n it writes Evan-format init files for `ftmc.py` and `gen.seed`. The source is the tilted island T from our n − 3 .. n + 3 and from exact (1e-9) family members, transformed by:
  - the 8 symmetries of the square
  - integer and near-integer (d, d) shifts
  - placing the island on the target box's diagonal

  It also holds one propagation rule: when T2 accepts a win at n, queue `stretch.py` (exact-fill variant) and donor-feed jobs for n ± 1 and the exact-family siblings, smallest member first. That is a 20-line cron, or a `pk/react.py` @rule if the lane adopts the store.
- **Language:** Python.
- **Runs on:** anywhere; it is light.
- **Acceptance test:**
  - Red first: a donor from an unrelated family (frac difference > 1e-3) placed into the 791 box must fail certification after `fillfast` + `fq`.
  - Then: our own 791 island placed into the 908 box (same fractional part, .6370295589) must reproduce our 908 side within 1e-7.
  - Then: a simulated win at 791 must emit jobs for 908 and for 790 / 792.
- **Go/no-go:** go if the 908 reconstruction matches. On a real win, count the sibling wins it produces.
- **Expected gain:** 0.001–0.005, capped by the about 0.012 that sits in exact families.

### T7 (conditional, likely not built). `metalquench` profile-then-prototype

- **Trigger:** FTMC has at least one count win, and a 1-hour profile of an FTMC step at n = 498 shows relax plus squeeze above 70% of the step time.
- **Build:** 1 day in MLX (custom Metal kernel for the pair penalty), as a drop-in replacement for `run_packer('relax')`. It runs on the M4 GPUs of boxB, boxA and boxD; that is three boxes, the boxF is Intel.
- **Acceptance test:** red first, with one sign in the SAT kernel flipped, the gradient test against a float64 numpy reference must fail. Then it must agree to 1e-5 relative on 250 configurations.
- **Expected gain:** 0–0.005.

## 3. Schedule (3 agents, files owned per agent)

| Day | Agent A (`tools/targets.py`, `tools/gate.py`, `tools/insbench/`) | Agent B (`tools/seamcell/`) | Agent C (`tools/winlns/`, `tools/donorfeed.py`) |
|---|---|---|---|
| 1 | T1, T2 with their red tests | T4 mine plus fold control | read compose2 / fill_resolve / fillfast interfaces |
| 2 | T3, then FTMC through the bench when the lane runs it | T4 cell search, **go/no-go** | T6 |
| 3–4 | operate T1–T3 for the lane, rank by T3 rates | if go: build 299, then 498 / 544 | T5, then head to head with FTMC |
| 5–7 | refresh board, re-gate | f sweep 0.55–0.90, carry results up | T5 on the rest of the band n if it beat FTMC, else stop |
| 8–10 | gate every candidate, prepare one submission for Sergio's yes | 0.6059 group; second kill rule | T7 profile, only if its trigger holds |

## 4. Can we reach 22.05?

Honestly, not in 10 days, and probably not by 2027-01-17. The realistic landing is about 22.12–22.17:
- FTMC / compose2 bring 0.04–0.08, if their control passes.
- T4, T5 and T6 add perhaps 0.005–0.03 on top, with overlap.

Reaching 22.05 needs all of the following to be true:
1. The leader's band-regime advantage (about 0.12 of the 0.143 band-regime gap) is a periodic seam construction plus per-n caps, not one-off irregular islands.
2. T4 finds cells with the leader's gain per step (about 0.82 at f ≈ 0.794) and finds equivalent cells across the whole f range 0.55–0.90, not just one group.
3. compose2 + `fq` can close the caps and the upright fill to a certified side at every n with no loss.
4. FTMC independently covers the roughly 0.07 that 19 other teams reached privately.

I put the chance of all four under 10%. The day-2 T4 go/no-go is the earliest real signal: a cell at ≥ 0.80 gain per step would move that estimate; nothing else in this plan can.

## 5. Rejected, one line each

- **famfit:** 0.000 direct by its own measurement, and its roll-out is `stretch.py` plus familymap; what remains is folded into T1.
- **vband:** Evan's `rational/` covers the rational-angle class, FTMC (Deotte) already holds k = 1 at m = 23–28, and its ceiling is 0.0275; the k = 1 n go into T1's work list instead.
- **ghostgrow:** Evan measured soft homotopies at 0/1,800, 0/552 and 0/180, and three days of Rust for a method already shown dead.
- **seamgraph:** the analyser duplicates familymap / bands / island, and the constructor is T5's work.
- **refill engine:** every piece exists (`fillfast`, `gen.py`, `ftmc`, `crop` / `ladd`, compose2); only its donor transforms survive, as T6.
- **seamdp:** rests on a fuzzy-family excess that a permutation null shows is chance, and it only spreads tiles we hold.
- **donorix model:** its prior is noise at 2e-4 to 1e-3, and there are too few wins to fit it; the propagation rule lives in T6.
- **windowfill:** about 1 unit of free area in slivers within radius 3, and Evan's `harden.py insert:K` already exists.
- **kkt certifier:** most of it exists (`rigid.py`, `exact/localmin.py`), and the 0.00049 ceiling only matters for tie-breaks near January (a half-day wrapper then, not now).
- **ulpcert:** the ±8 ulp model is wrong (the pandas parse is deterministic), and `floatsafe.py` + `pdscore.py` + T2 cover the risk.
- **sqstore:** duplicates `pk/store.py`, and the stale-seed bug it fixes belongs to the stopped `drive.py`.
- **sqfleet:** CPU does not bind (58k CPU-h available against 1k–8k per pass), and it duplicates `pk/bandit.py`, `tasks.py` and `react.py`.
- **sqmap:** duplicates familymap / `pk/lab.py`; T1's TSV is enough.
- **sidefinger engine:** 1e-9 families hold only 0.011 of the gap, and leader sides vary in the 4th digit within a group; only its PSLQ step survives, inside T1.
- **seamgp:** family-wide fitness has no exact families to work on, and its rigid typed grammar repeats bandseed's failure (492 of 498).
- **moveprior:** no training data at n ≥ 300; hand-reweight FTMC's 7 move kinds from accept logs if they ever exist.

## Summary

- The plan keeps one bet and five cheap enablers. The bet is T4 `seamcell`, a periodic seam-cell solver built on Evan's NLP, with a hard go/no-go at day 2: at least 0.80 squares gained per diagonal step at f ≈ 0.794. The enablers are T1 targets, T2 gate, T3 bench, T5 window search (kept only if it beats FTMC at equal CPU) and T6 donor feeding and propagation. T7 GPU quench is conditional and probably not built.
- Two critique premises were out of date. `floatsafe.py` already enforces 2e-11 (`floatsafe.py:32`, same SHA-256 on boxA), but that path has never been scored on Kaggle. Evan's packer is now built on boxA (`fq`, `harden`, `anneal`).
- Family leverage is small (about 0.012 of the gap in exact families), so every tool is judged per n, against FTMC, at equal CPU.
- 22.05 is under 10% likely. The realistic result is 22.12–22.17, and the T4 day-2 test is the earliest real signal.
- **Needs Sergio:** one Kaggle submission of a T2-green file, to prove the 2e-11 path on Kaggle itself.