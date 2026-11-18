# Avenue: polish r7 (2026-11-11)

**Result: 23 n certify smaller, total gain 0.0003982645. On the submitted file (22.1947113952) the assembled candidate scores 22.1943131307 through the pandas path. Not submitted from here. The gain is the first `fq` pass on the 54 n of today's harvest. The tie layouts and the older held packings are dry.**

Words used here: `fq` is Evan Daniel's all-free quench (MIT, run from its clone). "Held" is the submitted file `gather/harvest-2026-11-11a.csv`. A result counts only when `floatsafe` certifies it at 2.2e-11 and its score is more than 1e-10 below the held score.

The per-n files and `take.tsv` are in `<scratch>/bounties-squares/take-polish-r7` on boxA, in the layout that `engine_assemble.py` reads.

## 1. The 54 n of today's harvest

`engine_polish.py` with `--sub gather/harvest-2026-11-11a.csv` on the 54 n, 3 workers, about 35 minutes on a loaded box.

| | n | gain of score |
|---|---|---|
| tried | 54 | |
| `fq` found a smaller side that `floatsafe` certifies | 23 | |
| kept, more than 1e-10 below the held score | 22 | 0.0003982641 |
| dropped, under 1e-10 (n = 928, 8.7e-11) | 1 | |

Five n carry 90% of it:

| n | held score | new score | gain |
|---|---|---|---|
| 750 | 0.017118124740 | 0.016916792263 | 0.000201332 |
| 696 | 0.017933382032 | 0.017852950784 | 0.000080431 |
| 459 | 0.022319165573 | 0.022288618287 | 0.000030547 |
| 646 | 0.018383148349 | 0.018359023594 | 0.000024125 |
| 452 | 0.023678793493 | 0.023656869211 | 0.000021924 |

The other 17: n = 644 (2.05e-5), 500 (5.8e-6), 378 (3.1e-6), 918 (3.0e-6), 756 (2.7e-6), 593 (2.0e-6), 751 (9.2e-7), 590 (7.5e-7), 453 (3.9e-7), 921 (3.3e-7), 814 (2.2e-7), 505 (9.5e-8), 654 (2.8e-8), 873 (2.8e-8), 747 (1.8e-8), 856 (4.0e-10), 419 (1.2e-10).

`engine_polish.py` already repeats the quench up to three times per n, so a second pass over the winners was not run. On 2026-11-10 that second pass was worth 7.5e-9.

## 2. The 902 ties the take step dropped

The merge took 956 n and the take step kept 54. For the other 902 we compared the merged layout with the held one, by the count of tilted squares and by the sorted tilt angles.

| | n |
|---|---|
| ties | 902 |
| same layout as held (same tilted count, angles within 1e-3 degree) | 763 |
| different tilted count | 115 |
| same count, an angle more than 1e-3 degree apart | 24 |

All 902 raw sides are 1e-10 to 4e-9 below the held side. That is the dilation `floatsafe` added to our file, not a better layout.

The 139 different layouts were quenched and compared with the held score:

| run | n done | certified below held by more than 1e-10 |
|---|---|---|
| `fq` default flags | 139 of 139 | 0. No quench went more than 3e-9 below its start |
| `fq` default, then the POLISH_DEEP flags | 77 of 139 (stopped by the time limit) | 1: n = 973, gain 4.3e-10 |

**Dry.** A tie with another layout is jammed at the same side as ours. These layouts are other arrangements of the same rigid family (many sit at `m + 0.5355339`). The 62 n the second run did not reach are the ones with the smallest layout difference.

## 3. Slack in the older held packings

Measure: one `fq` default quench of each held packing that is not one of today's 54, and how far the side drops.

| | n |
|---|---|
| scanned (n = 5 to 815; stopped by the time limit, 816 to 1000 not scanned) | 766 |
| side drops more than 3e-9 | 0 |
| largest drop | 2.6e-9 (n = 704) |

**Dry.** Every drop is the `floatsafe` dilation coming back, about 4.6e-11 times the side. The older packings were all quenched on 2026-11-10 and hold no slack that `fq` can see. The `min_gap` column of the gate's `details.csv` is no slack measure: 988 n sit between 2.2e-11 and 5.2e-11, because the dilation moves in fixed steps.

## 4. What this says

- The whole gain is in the n that arrived today. That matches 2026-11-10: the first pass on fresh n pays (0.0002 then, 0.0004 now), and nothing else does.
- A tie in score is not a new start. 139 different layouts gave 4.3e-10.
- The polish belongs inside the daily harvest step: quench every n the take step keeps before the file goes to the gate. Today the harvest was submitted without it, and 0.0004 waited for a second submission.

## Summary

- **Gain:** 23 n, 0.0003982645, all certified. Candidate total 22.1943131307 (`pdscore.py`, 0 not ok). The main session assembles, gates and submits.
- **Ties:** 139 of the 902 are different layouts. Default quench: 0 of 139. Deep flags: 1 of 77, worth 4.3e-10.
- **Older held packings:** 0 of 766 move under a default quench.
- **Next:** make the `fq` pass a fixed step of the harvest, after the take step and before the gate. It costs about 35 minutes for 54 n on 3 workers.
