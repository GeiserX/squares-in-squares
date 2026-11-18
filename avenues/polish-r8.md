# Avenue: polish r8 (2026-11-11)

**Result: 27 n certify smaller, polish gain 0.0003667578 on top of the round-8 harvest take. The held file with the harvest take scores 22.1923448318; with this take on top it scores 22.1919780740 (`pdscore.py`, 0 not ok). Not submitted from here. The polish is now one command, [`daily_polish.sh`](../daily_polish.sh).**

Words used here: `fq` is Evan Daniel's all-free quench (MIT, run from its clone). "Held" is the submitted file `gather/round7-2026-11-11a.csv` (22.1934052297, gate dir `gate/cand-round7-1111a`). "Start" is the packing a polish started from: the harvest take's packing where that take has the n, the held packing otherwise. A result counts only when `floatsafe` certifies it at 2.2e-11 and its score is more than 1e-10 below both the held score and the start score.

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-polish-r8` on boxA, in the layout that `engine_assemble.py` reads. `take.tsv` has two more columns than a harvest take: `start` and `polish_gain`. Its `gain` column is against the held file, so for the 10 n the harvest take also has, that number includes the harvest's part.

## 1. What was polished

70 n: every n that moved on 2026-11-11 and had no polish yet.

| group | n |
|---|---|
| the round-8 harvest take (`take-harvest-r8`) | 13 |
| the n round 7 moved (harvest, outside register, soft-box search) | 63 |
| both | 6 |
| total, distinct | 70 |

## 2. The `fq` quench

`engine_polish.py` with the default flags, then the deep flags, up to three rounds per n. 4 workers, 1,655 s.

| | n | gain of score |
|---|---|---|
| tried | 70 | |
| `fq` found a smaller side | 27 | 0.0003378 |
| kept by the take | 25 | |
| dropped, under 1e-10 (n = 921, 7.8e-11) | 1 | |
| replaced by a better soft-box result (n = 806) | 1 | |

Five n carry 94% of it:

| n | start | start score | new score | polish gain |
|---|---|---|---|---|
| 497 | harvest take | 0.022254792346 | 0.022079191729 | 0.000175601 |
| 643 | harvest take | 0.018778046844 | 0.018708881017 | 0.000069166 |
| 690 | harvest take | 0.018990454786 | 0.018964016248 | 0.000026439 |
| 462 | harvest take | 0.021178109045 | 0.021152099535 | 0.000026010 |
| 701 | held | 0.016507446311 | 0.016487893405 | 0.000019553 |

The other 20: n = 335 (8.7e-6), 696 (4.5e-6), 593 (3.7e-6), 646 (2.1e-6), 694 (8.9e-7), 552 (6.6e-7), 805 (2.8e-7), 865 (6.4e-8), 502 (6.0e-8), 933 (5.1e-8), 869 (5.1e-8), 453 (4.2e-8), 873 (1.6e-8), 689 (6.8e-9), 601 (8.2e-10), 864 (6.8e-10), 981 (3.4e-10), 508 (3.0e-10), 815 (1.5e-10), 555 (1.1e-10).

By start: the 13 harvest n gave 0.000312 on 10 n. The 57 held n gave 0.000025 by `fq` on 15 kept n, and most of that is 701, the n our soft-box search moved in round 7.

## 3. The soft-box search, 60 s per n

`methods_soft.py` for 60 s on each of 57 n (the 13 of the harvest take and the 47 in `results/round7-best-2026-11-11.tsv`, 3 in both), from the quenched packing. 4 workers, about 17 minutes.

| | n | gain of score |
|---|---|---|
| tried | 57 | |
| a find that certifies | 2 | 0.0000290 |

| n | start score | new score | polish gain |
|---|---|---|---|
| 806 | 0.016251062332 | 0.016226300236 | 0.000024762 |
| 590 | 0.020615717655 | 0.020611522134 | 0.000004196 |

The other 55 n: 0 finds in 60 s. The run used the working copy of `methods_soft.py` of that hour, which had changes not yet committed. n = 873 started from the packing before its quench, because its quench ended after the search list was built; it had no find.

## 4. What this says

- The first polish of a fresh n pays again: 0.00031 on the 13 harvest n, as on 2026-11-10 (0.0002) and in round 7 (0.0004).
- An n polished once holds little: 0.000025 on 57 n, and 0.00002 of it is one n.
- 60 s of the soft-box search finds a move on 2 of 57 n. It costs as much time as the quench and gives a tenth of it. A longer run per n is the soft-box avenue's question, not this one's.

## 5. `daily_polish.sh`

```
daily_polish.sh TAKE_DIR BASE_DETAILS.csv OUT_TAKE_DIR
```

It takes a take dir and the `details.csv` of the held file's gate dir. It assembles the start file, runs the quench and the 60 s search on every n of the take dir (and on the n in `NS`), certifies, and writes a polished take dir. It never builds a submission and never submits. Give `engine_assemble.py` the take dir first and the polished dir after it.

Checked on 2026-11-11 with a take dir of one n (335) plus `NS=590` and `SOFT_SECONDS=20`: it kept both n with the scores of this avenue's take, 0.026875310128 and 0.020611522134. A take dir with no rows writes an empty `take.tsv` and exits 0. A second run into the same output dir refuses.

One trap, now in the script: macOS `xargs -I` refuses a command longer than 255 bytes, so the n goes to the search as `$1`.

## Summary

- **Gain:** 27 n, 0.0003667578 on top of the harvest take, all certified. Candidate total 22.1919780740 with the harvest take and this take. The main session assembles, gates and submits.
- **Where it came from:** `fq` on the 13 fresh harvest n gave 0.00031. `fq` on the 57 older n gave 0.000025. The 60 s soft-box search gave 0.000029 on 2 n.
- **Next:** run `daily_polish.sh` on every take dir before the gate. For 13 n it costs about 10 minutes on 4 workers.
