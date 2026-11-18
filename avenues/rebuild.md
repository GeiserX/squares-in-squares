# Avenue: rebuild (rounds 25 to 28, 2026-11-13 to 15)

The rebuild lane makes clean copies of withdrawn layouts and hands them on. A layout is withdrawn when its recorded ancestry reaches a source that is out. These sources are the Samanyu-dev GitHub seed (no licence), the penguin069 union, the CC BY-SA 4.0 best-of-1105 file and the five areebbb counts. We rebuild from licensed inputs only. Then other lanes can use the clean copy as a parent again.

## Tools

| tool | what it does |
|---|---|
| `rebuild_bars.py` | The bar per n: the base details.csv and the live take rows whose text has no seed ancestry. `SQ_ROUND` picks the live round (default 26). It writes the score in column 2. |
| `rebuild_heldpool.py` | A join pool of held layouts. Each layout keeps the source of the newest round table that lists it. That text is walked with `quench_audit.walk` and checked with the `quench_audit` rules and `forensics_policy.classify_text`. A bare per-n file name such as `921-29e12ff3.csv` also refuses it. |
| `rebuild_pool.py` | A pool where each layout is turned to the symmetry whose chain reading finds the most chains. |
| `rebuild_seams.py` | Brute force over every seam of `k123_join.join` (j1, j2, shift, d ladder) for chosen pairs and target counts. It reads the bar side from column 2. |
| `rebuild_run.py` | One worker per box slot. It runs `k123_turn.py --turns=0` and the fq loop on a start, a midm kick, or one fq quench of a certified file. |
| `rebuild_anc.py` | The source and licence cells of a row, with every parent record stored once by hash. |
| `rebuild_take.py` | Certify (floatsafe at 2.2e-11, below the bar by more than 1e-10) and publish against the live takes of the round. |

## Round 25

The agent stopped on a usage limit at about 23:50 UTC. Its workers ran on to the deadline. `take-rebuild-r25/STATE.txt` holds the record.

- 735 and 790 certify from single corner windows of the licensed n = 847 rectangle parts of the k123 lane. Those parts are two opposite windows of the licensed 581 and the CC0 123. Gains: 2.918e-4 and 2.660e-4. Both are held in round 25 b.
- 968 certifies from a join of the rebuilt 735 (mirrored) and 790 (j21-16, shift 3), then the turn and fq loop: gain 1.436e-4. The midm lane then kicked it 2.8e-5 of side lower, and that copy is held.
- 534 from a 735 + 847r join was withdrawn: its 735 parent was the border lane's withdrawn 735.
- Walks from held layouts on the line where k minus 2m is -33 (750, 807, 866, 927, 990) end above the held sides. The best one is 866 from 807, at 1.26e-3 of side above.
- A 489 join of the rebuilt 790 (mirrored) and 968 reached 22.6056231 after the agent stopped. Round 26 certified it.

## Round 26

`take-rebuild-r26/STATE.txt` holds the record. The boxes were boxB (2 processes) and boxE (1 process). The first agent stopped at about 16:25 UTC when its connection dropped. Its workers ran on, and a new agent took them over at 16:34 UTC. The table of every measured job is `results/rebuild-r26-2026-11-14.tsv` (253 jobs).

### Result

- 489 certifies at side 22.6056231 (score 0.022261614103, gain 4.425e-5 on the round 25 b bar). It is the round 25 join of the rebuilt 790 (mirrored) and the rebuilt 968, after the turn and the fq loop. This round certified it and quenched it once from the certified file. A 900 s midm kick then moved it by only 1.1e-9.
- `quench_walk.py` walks 489 clean over 21 files. As a positive control, the same walk refuses the k123 round 25 982.

### CC0 rows that copy best-of-1105 rows

The harvest tool `nearpub_excl.py` compares a layout with the best-of-1105 row of the same n. Each of these CC0 sis-final-packings rows matches a best-of-1105 row in every square, to within 1e-6:

| CC0 rows | where | largest shift |
|---|---|---|
| 123, 365 | `take-k123-r24/work/cc0` | 4.2e-10 |
| 648, 700, 701, 989, 990 | the file of 2026-11-14, `work/cc0r26` | 7.1e-10 |

The best-of-1105 file had a version on 2026-11-06. The oldest CC0 version on disk is from 2026-11-09. So this round cannot tell which file came first.

Every 927 and 648 near miss of this round came from the rows of 2026-11-14. The 927 ends share 0.50 of their squares within 1e-3 with the best-of-1105 927. The harvest lane withdrew rows at 0.42 to 0.76 for the same reason. So we withdrew the nine near files. One more kick of that line then ended 8.9e-6 of side below the 927 bar. It stays out too. It gains only 2.9e-7 of score, and its inputs are copies.

489 shares 0.231 of its squares with the best-of-1105 489. Its CC0 inputs are 123 and 365. The round 25 rebuilds 534, 735, 790 and 968 used the same inputs, and the round 25 skeptic accepted them. So we keep 489 and hand the measurement to the main session.

### Where the withdrawn 866, 927 and 990 come from

A positive control rebuilt the k123 round 23 start of 990 from `869r-928r-j13-10-s1`. So the 23a gains on 866, 927 and 990 (4.7e-4 together) all come from that one join. The 869 there is a readers walk one shell up from an 810. That 810 is a readers walk up from a 753, and the 753 is the k123 join `809r-870`. The 870 is a family step down from a 931. That 931 is a stair-c composition with the far zones `931h.F2d` and `811h.F1`, and both zones were cut from the seed. A clean copy needs a clean stand-in at each of 9 steps, so it did not fit in this round.

### Measured dead ends

| what | measured |
|---|---|
| Brute seams of the f = 0.596 bands (489, 534, 581 and the rest of pool A) | Every turned start ends at f = 0.59604 or at a known side. |
| `forensics_rect.py` windows for 735 and 790 from the 0.596 donors | No window under 0.6008. |
| `rebuild_seams.py` on the f = 0.87 layouts (866, 927, 990, 648) | `kj.join` reports L from the chains, and that is not the real side. Every real start is 0.3 to 2 above the bar. Use `k123_join.py scan` there. It uses `kj.norm` and keeps a seam only when the chain sizes match. |
| Readers walks of the CC0 811 | They end 0.008 to 0.018 above the bars. The walked 870 reads 12 chains and no band. |
| `k123_join.py scan` over the clean held pools B (13 layouts and the CC0 811) and B3 (98 layouts) | Starts that reuse the held layout of their own count come back to it. From other donors the best ends are 866 at 3.6e-3, 927 at 3.4e-3 and 990 at 4.4e-3 above the bars. |
| The CC0 648 of 2026-11-14 | One 900 s kick took it to 9.1e-5 above the bar. Two more chains of 1800 s found nothing in 188 tries. It is a copy of a best-of-1105 row, so it is out anyway. |
| Pool E: B3 plus the 13 live round 26 takes that walk clean | 59 starts. The best ends are 599 at 1.7e-3, 648 at 2.7e-3 and 862 at 1.3e-2 above the bars. |

### The CC0 joins for 927

The k123 scan also ran over the CC0 set itself: 145 tilted counts (k minus 2m from -41 to -21) and 20880 pairs. That gave 4797 starts, and 1437 remain after we drop the starts whose count is one of their own donors. The 812 from 755r + 813r ends 1.25e-3 above its bar. Only the 927 came close:

- The joins X + 989 (the CC0 989 as the second band) turn from rooms of -0.026 to -0.028 down to 3.4e-4 above the bar. The same joins with the held 989 end 3.4e-3 above. So the CC0 989 band made the difference.
- Kicks (lkick and kick, 900 s to 1800 s) took the 700 + 989 end from 1.36e-4 to 7.3e-5 above the bar in four rounds. The fifth crossed it. The whole line is out, as the section above says.

### Audit of held rows

`rebuild_heldpool.py` refuses a held row when the text of its newest table row walks to an out source or to a bare per-n file name. These held rows were refused, and the handoff log lists them:

- seed 811: 698, 752, 753, 809, 810, 811, 868, 869, 870, 929, 930, 931, 992, 993, 994
- seeds 503 and 504: 598, 601, 649, 700, 701, 754, 755, 756, 812, 813, 932, 995, 996
- seed 983: 804, 860, 862, 863, 924
- 987 (seed 861 and a bare name) and 921 (a bare name)
- penguin069: 815, 875, 876, 936, 999
- 800 (a 745r-858r join) and 802 (unknown source)

The same check refused 8 live round 26 takes of other lanes. Seven of them walk to the bare names `972-9fbe11c7828e084f.csv` or `910-5c321becbd66bcdd.csv`, and the classfill 850 names penguin069.

### Tool changes

- `rebuild_run.py`: with `REBUILD_TRIAGE=D`, a start whose turned side is more than D above the bar skips the fq loop. Round 26 used D = 0.002, because the round 25 loops moved an end by 3e-4 at most.
- `rebuild_heldpool.py` (new): a join pool of held layouts whose recorded ancestry walks clean.
- `rebuild_bars.py` and `rebuild_take.py` read the live takes of round `SQ_ROUND` (default 26) and the round 25 b base.
- A near file needs a record that `quench_walk.py` can follow. Our near files had none, so the follow lanes refused them as "no root". Write a `.csv.json` record next to every near file.

### Next

1. Find out row by row whether the CC0 sis-final-packings file or the best-of-1105 file came first. Use the dated copies on disk (`harvest-2026-11-10` and later). The answer decides 489, the round 25 rows built on the CC0 123 and 365, and the 927 line (8.9e-6 of side below the bar).
2. If the CC0 rows are out, rebuild 927 with a second band that is not a copy. The 927 line needed the CC0 989 band (3.4e-4 against 3.4e-3 with the held 989), and kicks then moved it below the bar in five rounds.
3. Replay the 23a 990 tree from clean zones (9 steps). The 23a gains on 866, 927 and 990 were 4.7e-4 together. It needs a clean stand-in for `811h.F1` (the CC0 811, if step 1 clears it) and a new far zone for `931h.F2d`.
4. Do not repeat brute seams of the 0.596 bands, rectangle windows for 735 and 790, or readers walks of the CC0 811. Each one is a measured dead end above.

## Round 27

`take-rebuild-r27/STATE.txt` holds the record. The agent stopped writing at about 20:44 UTC and wrote no report. Its workers ran on to 23:45 UTC. The table of every measured job is `results/rebuild-r27-2026-11-14.tsv` (32 jobs).

### Result

Round 27 lifted the Samanyu-dev rule, so rows refused for that seed came back.

| n | score | gain on bar27 | what |
|---|---|---|---|
| 866 | 0.015148788996 | 1.813e-4 | the invent round 23 866, re-opened |
| 927 | 0.014321929905 | 1.391e-4 | a 900 s midm kick of the invent round 24 927 |
| 935 | 0.013063540710 | 4.144e-5 | the invent round 24 935, re-opened |
| 990 | 0.013529711478 | 1.562e-4 | the invent round 24 990, re-opened |

Round 28 holds 935 and 990 as they are. The backlog lane kicked 866 and 927 a little lower, and round 28 holds those copies.

### Measured

- The lane csv files keep the angle in radians (`methods_lp.load`). The first scan read degrees, so it missed rows with a tilted edge square.
- A `k123_join.py scan` of 363 held layouts gave 796 starts. The 16 best starts each got the turn and the fq loop. The best end is a 932 from 933r + 871r, at 3.7e-7 of side above bar28. The others end 1.2e-3 to 7.9e-3 above.
- One quench of each certified file never went lower (+1.6e-7 to +9.5e-5 of side).

## Round 28

`take-rebuild-r28/STATE.txt` holds the record. The boxes were boxB (2 processes) and boxE (1 process). The table of every measured job is `results/rebuild-r28-2026-11-15.tsv`.

### The rule change of 00:19 UTC

The main session dropped the ancestor share test and the original-seed share test. The share test now applies only to a row whose first source is a fetched public notebook or dataset. The test is 0.4 or more of the squares within 1e-3 of the best-of-1105 row. A row whose recorded ancestry names the best-of-1105 file itself stays out.

So rows that earlier rounds refused only for an ancestor's share came back. Many of their parents had moved or gone. We pinned each one from an immutable snapshot with its sha256. `take-rebuild-r28/work/prov/moved-parents.json` maps every moved parent to its snapshot.

### Result

These rows are in the take at 05:55 UTC (gain on bar28):

| n | score | gain | what |
|---|---|---|---|
| 546 | 0.020249795279 | 2.846e-6 | the midm round 26 certificate, re-opened |
| 694 | 0.018255086255 | 1.389e-5 | the midm round 26 certificate, re-opened |
| 695 | 0.017778579457 | 1.829e-5 | the backlog round 26 near file b063, re-opened |
| 805 | 0.016429737225 | 1.422e-4 | our 900 s kick of the stair-c round 28 805 |
| 923 | 0.014979394406 | 1.9e-10 | our 900 s kick of the held 923 |
| 985 | 0.014318746672 | 3.871e-6 | the classfill round 25 kick, re-opened |

The sum is 1.811e-4 on bar28, and the same beyond the other live round 28 takes.

Each row is certified by floatsafe at 2.2e-11. Each one also got one fq quench of the certified file on a box that is not boxA.

We certified these rows first. Then another lane went a little lower at the same n, so its row is in that lane's take. The backlog lane kicked our files for 180 s. The modules 748 is its own composition, and the border 642 is a contact LP reclose of a pinned copy.

| n | our score | now held by | its score |
|---|---|---|---|
| 684 | 0.018613976364 (gain 9.013e-5) | backlog | 0.018611107863 |
| 748 | 0.017375064950 (gain 8.638e-5) | modules | 0.017342228718 |
| 910 | 0.016262543017 (gain 1.943e-5) | backlog | 0.016262540434 |
| 978 | 0.015369240108 (gain 2.215e-6) | backlog and quench | 0.015365308190 |
| 642 | 0.018923097033 (gain 8.952e-7) | border | 0.018923096217 |

### What gave the gains

- Re-opened rows came first. The backlog round 26 near files of 748, 695, 694 and 805 were refused for an ancestor's share. The midm round 26 certificates of 694 and 546 and the k123 round 26 raw join for 910 were refused the same way. The scan of every frozen work folder found one more: a classfill round 25 kick of 985 that its own lane never published.
- The first 900 s midm kick of a fresh layout moved it far. The 748 went 3.1e-5 lower, and its side became our 694 side plus exactly 1. The two layouts share the same left arm and band. The 910 went 1.6e-5 lower in three kicks.
- A 900 s midm kick of a forensics rectangle at the bar side gave 9.0e-5 on 684. The rectangle joins a window of the held 684 donor and a window of the 737 donor. The twoshort lane's 180 s lkicks of the same file had moved it by 1.3e-9 only.
- Follow kicks of other lanes' fresh rows gave 805 (5.1e-7 below the stair-c row), 978 and 642.

### Rows that stay out

| n | why |
|---|---|
| 998, 457 | The first source is a harvested public row. It shares 0.84 and 0.73 with the best-of-1105 row. |
| 646 | A kick of the harvest round 26 public 646. Share 0.64. |
| 926 | Its tree holds the near-public 988, an exact copy of the best-of-1105 988. |
| 916 | The public source of the harvest row is not resolved. |
| 639, 858 | penguin069 counts. |
| 505 | The classfill chain reaches kmmmvs local_bank (Other terms), and the walk does not end. |
| 971, the k123 546 final | No record traces them. |
| 641, 654, 737, and the forensics round 21 to 24 inputs | These are raw compositions from before the quench. Their squares overlap, so they are not layouts. Their quenched ends are above bar28. |
| 503, 697, 495, 341 | They certify 6.9e-11 to 9.7e-11 below bar28, under the 1e-10 rule. |
| 802 | Our kick of the forensics 802 rectangle certifies 5.4e-8 below bar28. Its tree reaches the forensics round 24 745 rectangle and 918, a rule-a family. |

At 01:43 UTC the forensics lane withdrew its 743 and 29 near rectangles. Their root names a rule-a donor (the round 23 forensics donor858). `rebuild_rulea28.py` walks each of our published rows and every moved-parent snapshot. No text reached names penguin069, the joegun-boxed union or a rule-a donor. The only "joegun" hits are the jonathan1506/joegun-squares-packings credits of the held 684, 750, 923 and 986.

### Measured dead ends

| what | measured |
|---|---|
| Scans of every per-n csv in the frozen take dirs: top and near of rounds 20 to 28, and every work folder of rounds 1 to 28 (about 870000 files), against bar28 | One new row that traces, the classfill round 25 985. The rest are raw compositions that overlap, inflate or soft states that fail floatsafe, beaten rows, or rows under 1e-10. |
| Second and later 900 s kicks of the re-opened rows (546, 694, 695, 985, and 748 after its first kick) | No lower layout, or under 2e-9 of side. Only 910 kept moving: 1.2e-5 at the second kick, 7.4e-6 at the third, then 1.6e-7 and less. |
| `family_step.py read` and `family_readers.py read` on our 546, 694, 695, 748 and 910 | family_step refuses all five. family_readers reads them. The up step builds 0.10 to 0.30 above the target bars, and the down step builds 0.013 to 0.030 above. |
| One upright square put into the largest empty upright square (0.64 to 0.70 wide, `rebuild_holes28.py`) of our 910, 546 and 694, then the turn and the fq loop | The turn quench ends 0.072 to 0.197 above the target bars. The area estimate was 0.016 to 0.021. |
| 900 s kicks of forensics round 28 rectangles at the bar side (x- jobs) | 684 dropped 9.0e-5. 682, 685, 686 and 972 found no lower layout. Of the 13 more, 12 found no lower layout. The 802 went 5.4e-8 below bar28, but its tree reaches the forensics round 24 745 rectangle and 918, so it stays out. |
| Follow kicks of the lowest live row of other lanes | Most found no lower layout. Gains came only on fresh rows (805, 978, 684, 642). The backlog lane then kicked our new rows for 180 s and took 910, 748, 684, 978 and 642 a little lower. |

### Tool changes

The tools ran from `take-rebuild-r28/work/tools` under short names (`q28.py` and so on). The repo copies carry the prefix `rebuild_`.

- `rebuild_q28.py`: pin a start (byte copy and sha256) and queue one `rebuild_run.py` job on a box. The queue order is quench jobs, then kicks of our own rows, then insert, rectangle and held-row kicks, then the rest.
- `rebuild_collect28.py`: one pass of the collector. It fetches each job that ends below the bar side and certifies it against bar28. A row that beats the live takes gets a quench of the certified file on the same box. A kick of one of our rows must also beat our published side.
- `rebuild_follow28.py`: a 900 s kick of the lowest live row of each n of the other lanes. It can also take the near files of the handoff log.
- `rebuild_reopen28.py`: pin a near file, certify it against bar28 and queue its quench.
- `rebuild_rows28.py` and `rebuild_pub28.py`: the source and licence cells of each row, then the per-n csv and take.tsv by rename. A row that a live take beats leaves the take.
- `rebuild_walk28.py`: the round 27 walk plus the ancestor shares. `rebuild_rulea28.py`: search every text a walk reaches for a rule-a reference.
- `rebuild_scan28.py`, `rebuild_scanwork28.py`, `rebuild_scangather28.py`: light scans of take, near, work and gather files against bar28.
- `rebuild_holes28.py`: the largest empty upright square of a layout. `rebuild_heldshare28.py`: the best-of-1105 share of each held row. `rebuild_order28.py`: reorder a box queue. `rebuild_table28.py`: the job table from done.jsonl. `rebuild_driver28.sh`: the collector and follow loop.
- `rebuild_reopen27.py` and `rebuild_walk27.py` are the round 27 tools, committed now.

### Next

1. Kick every forensics rectangle that sits at the bar side, 900 s each, first. The 684 rectangle gave 9.0e-5 in one kick. In this round only 18 of the 88 rectangles with mixed donors had a slot.
2. Kick each fresh row once, within minutes of its certificate. The first kick moved 748 by 3.1e-5 and 910 by 8.4e-6. The second and later kicks of the same rows gave almost nothing.
3. Kick the held rows with a high best-of-1105 share (0.4 or more). The share gates kept every lane away from them until 00:19 UTC of this round, so most were never kicked. `rebuild_heldshare28.py` lists them. The scan reached n = 480 only.
4. Do not repeat the family steps of our rows, the single-square inserts, or the scans of the frozen folders. Each one is a measured dead end above.

## Round 29

`take-rebuild-r29/STATE.txt` holds the record. The boxes were boxB (2 processes) and boxE (1 process). The table of every measured job is `results/rebuild-r29-2026-11-15.tsv`.

### Result

These rows are in the take at 11:55 UTC (gain on bar29):

| n | score | gain | what |
|---|---|---|---|
| 593 | 0.019439190066 | 5.077e-5 | our 900 s kick of the quench round 29 593 |
| 594 | 0.019246869762 | 2.052e-5 | our 900 s kick of the backlog round 29 594 |
| 689 | 0.018864047395 | 8.808e-6 | our 900 s kick of the backlog round 29 689 |
| 802 | 0.016715892829 | 5.358e-8 | our round 28 kick of the forensics round 28 802 rectangle, re-opened |
| 910 | 0.016262508071 | 3.236e-8 | our round 28 kick k5-910, never published in round 28, re-opened |
| 988 | 0.013956275195 | 6.140e-5 | our 900 s kick of the forensics round 29 988 rectangle |

The sum is 1.416e-4 on bar29 and 1.382e-4 beyond the other live round 29 takes at 11:54 UTC.

Each row is certified by floatsafe at 2.2e-11, with the bisected dilation of the border lane (`tools/border/r28/finesafe.py`). Each one also got one fq quench of the certified file on boxB or boxE.

We certified these rows below bar29 first. Then another lane published the same layout or a lower one at the same n, so its row is in that lane's take. Most of them are 180 s kicks of our files.

| n | our score | now held by | its score |
|---|---|---|---|
| 907 | 0.016251715183 (gain 9.390e-5) | quench | 0.016251715181 |
| 752 | 0.016507285394 (gain 3.508e-5) | midm | 0.016506678667 |
| 504 | 0.020486673686 (gain 2.259e-5) | twoshort | 0.020480793977 |
| 412 | 0.024529996750 (gain 2.040e-5) | harvest | 0.024529996750 |
| 747 | 0.017380950108 (gain 1.150e-5) | midm | 0.017380950091 |
| 737 | 0.018089339729 (gain 2.324e-6) | twoshort | 0.018089335633 |
| 551 | 0.019069481133 (gain 1.803e-6) | backlog | 0.019069419749 |
| 916 | 0.016016060114 (gain 5.339e-7) | border | 0.016015885514 |
| 991 | 0.013358908131 (gain 6.312e-8) | midm | 0.013358906865 |

### What gave the gains

- The first 900 s midm kick of a fresh row from another lane gave the large moves. 907 went 9.4e-5 lower, 988 6.1e-5, 593 5.1e-5, 752 3.5e-5, 594 2.1e-5, 504 1.9e-5, 747 1.2e-5 and 689 8.8e-6. The other lanes' 180 s kicks of the same rows had moved them less. Then those lanes kicked our files and went 1e-11 to 6e-6 lower.
- A near file paid only when it was well below the bar side already: 747 (3.1e-4 of side), 907 (2.8e-3) and 412 (4.1e-4). None of the 9 near files at the bar side (within 2e-9) moved.
- Re-opened files came first in the round. We scanned the 92327 per-n files that round 28 wrote after 00:00 UTC. Three certified layouts were below bar29 and in no take: a classfill final of 737, a k123 certificate of 551, and our own kick of 910.
- The round 28 kick of the forensics 802 rectangle came back. Round 28 kept it out on a rule-a match through the forensics round 24 745 rectangle. That match was the false directory-name rule that main corrected at 07:34 UTC.

### Source rules we applied

- Rule a is `quench_audit.RULES`, as main narrowed it at 07:34 UTC. Only 745r-858r, 858r-745r, 858-ec97a452 and 745-64c4b4f8 are the 745/858 join. The forensics round 23 rectangle cut from the midm 639 also stays out. The readers donors 858-c82b5be2 and 858-bc8896e9 and the 800-7a2b family are clean.
- The held 801 is ours. Its round 20 table row names the best-of-1105 file, and the walk skips that text, as `quench_walk.py` does.
- The 0.4 share line and the licence list apply to a public-first row that we fetched, and to everything built from it. A held packing is not such a row. When other terms reach a row only through a held packing, the row's source cell names them. The 689 and 802 rows name the held 916 of round 20 (kmmmvs/squares-in-squares-private-packings, licence "Other"). The 802 row also names the held 375 of round 23 (alexchilton/squares-in-squares-starter-kit, licence "Other").
- At 08:32 UTC the forensics lane began to withdraw rows whose held ancestors read share 0.4 or more. We did not apply that stricter gate to our rows, but we did not contest it either: our 376 rows (1.3e-8) stay out. `rebuild_pubroots29.py` lists each held row that a tree reaches, with its licence and share, so the assembler can decide.
- A public-first start whose share reads 0.4 or more is never kicked. The follow skips it. We pruned the harvest 416 (0.748) and 454 (0.414) follows.
- A trap: the share at 1e-3 passes a moved copy. The harvest round 22 799 (kmmmvs public merge) reads 0.376 at 1e-3 but 1.000 at 1e-2, with a largest shift of 5.7e-3. It sits in many round 28 and 29 trees as a forensics part. We told main at 08:40 UTC.

### Measured dead ends

| what | measured |
|---|---|
| Second kicks of our own finds (k2-) | 551 moved 4.2e-5 of room and 504 4.1e-6, but 907, 689, 737 and 752 gave no lower layout or less than the other lanes. |
| Near files at the bar side (stair-c 871 862 873 814, forensics 913 902 908 801, modules 976) | 0 of 9 moved. |
| Follow kicks of 995 993 965 985 971 641 503 587 90 and the held 451 and 785, and the backlog 988 of 06:24 UTC | No lower layout, or 1e-9 only. |
| The forensics rectangles and the held seed rows (x- and h- jobs) | They sat behind the follow kicks, and only a few had a slot before 11:45 UTC. |

### Tool changes

- `rebuild_rt29.py`: the certificate is `rebuild_take.cert` with the border `finesafe.work` (bisected dilation). It certifies 3e-10 to 9e-10 of side lower than the floatsafe ladder.
- `rebuild_autopub29.py` (new): after each collect pass, it walks each final, applies the round 29 rule and publishes the clean rows. A reviewed note in `work/notes.json` replaces the walk for a start whose record moved.
- `rebuild_follow29.py`: it reads near files from any handoff wording. It skips bar copies (0.9 or more of the centres within 1e-3 of the bar row) and near files that are not 1e-8 below the bar side. It skips public-first starts with share 0.4 or more. It keeps one pending take follow per n: a lower live row replaces the pending follow of a higher one.
- `rebuild_prune29.py` (new): it removes unclaimed jobs from a box queue.
- `rebuild_pubroots29.py` and `rebuild_pubanc29.py` (new): they list the held rows and the fetched public-first files that a tree reaches, with licence and share.
- `rebuild_q29.py` and `rebuild_collect29.py` order a box queue: quench jobs, then our second kicks, then follows, then rectangles and held rows.

### Next

1. Kick each fresh row of another lane once, with a 900 s midm kick, within minutes of its certificate. In this round that gave 907 (9.4e-5), 988 (6.1e-5), 593 (5.1e-5), 752 (3.5e-5), 594 (2.1e-5), 504 (1.9e-5), 747 (1.2e-5) and 689 (8.8e-6). The 593 and 594 kicks were certified at 11:45 UTC, so a slot open to the deadline still pays. Our 900 s kicks went deeper than the 180 s kicks of the other lanes.
2. Kick a near file only when it is 1e-7 or more below the bar side. Those paid: 747, 907 and 412. None of the 9 near files at the bar side moved.
3. Settle the held-ancestor share question for all lanes before round 30. The forensics lane withdraws rows whose held ancestors read share 0.4 or more, and we keep them and name the terms. `rebuild_pubroots29.py` gives the list per tree.
4. Give the forensics rectangles a reserved slot, or drop them. In round 28 one rectangle gave 9.0e-5. In this round they never got a slot behind the follows.
## Round 30

`take-rebuild-r30/STATE.txt` holds the record. The boxes were boxB (2 processes) and boxE (1 process). The table of every measured job (79 jobs) is `results/rebuild-r30-2026-11-15.tsv`.

The bar changed once. At 13:31 UTC main submitted round 29 b and named `gate/cand-round29-1115b/details.csv` the round 30 bar. It differs from `bar30.tsv` at 3 n only (376, 503 and 582), so no row of ours moved.

### Result

These rows are in the take at 17:46 UTC (gain on the round 30 bar):

| n | score | gain | what |
|---|---|---|---|
| 495 | 0.023079708562 | 1.149e-10 | our 900 s kick of the held round 28 b 495 |
| 593 | 0.019359666299 | 7.952e-05 | our chain kick (two legs) of our round 29 593 |
| 642 | 0.018925301501 | 6.694e-06 | our 900 s kick of the held round 28 b 642 |
| 655 | 0.015794574388 | 5.555e-06 | our 900 s kick of the quench round 30 655 (an fq quench of the held 655) |
| 968 | 0.015797076272 | 9.353e-07 | our 900 s kick of the quench round 30 968 |

The sum is 9.271e-05 on the bar and 9.157e-5 beyond the other live round 30 takes at 17:46 UTC.

### What gave the gains

- Kicks of held rows in the room the round 28 skeptic opened. The round 29 bar held 9 rows that the round 28 assembler had dropped (`take-assemble-r28/drops.json`), so no round 29 lane worked those n. The held row of each n was still there, with room below it. One 900 s kick of the held 642 (round 18, an fq quench of jazivxt/boxed-in) went 6.69e-6 lower. One kick of the held 695 (round 22, the areebbb union row) went 8.85e-6 lower, and two chain kicks took it to 1.91e-5 below the bar. At 15:43 UTC harvest held a 695 row 2.1e-10 lower, so 695 left our take. The held 546 kick certified 3.3e-5 of side below the bar, but backlog's 546 was lower by then. The held 646 kick moved 1.2e-9 of side only.
- The chain kick of a row that just moved. Our round 29 593 certified at 11:45 UTC, at the job deadline, so nobody kicked it in round 29. Its first 900 s kick of round 30 moved 1.94e-3 of side (7.95e-5 of score). The next kick of the same basin moved 3e-9 only.
- A 900 s kick of a fresh row of another lane. Quench's fq quench of the held 655 went 5.56e-6 lower. Quench's 968 went 9.35e-7 lower.

### Kicks that gave no row

- Held kicks without a known room. After 642 and 695 paid, we queued 900 s kicks of 19 more held rows. Each one has a results-table source that names no kick or construction, only a public file or an fq quench of one. We took them in board-gap order. Only 495 gave a row, at 1.1e-10. 491, 545, 864, 643, 925, 370, 553 and 411 found no lower layout. 851, 500, 506, 644, 857, 638, 552, 742, 913 and 707 moved 1.1e-9 to 1.7e-9 of side only. That is fq rounding, below the 1e-10 score rule.
- Races with other lanes. We certified 10 layouts of 7 n below the bar that another lane had beaten by the time they landed. These are 546 (backlog 3.3e-8 lower), 584 (equal to 1e-15), 378 (1.5e-6), 687 (twice), 791 (1.9e-10) and 695 (harvest 2.1e-10 lower). 594 landed twice: backlog was 1.9e-9 lower, then ours was 2.1e-11 lower, under the 1e-10 rule. Backlog claims nearly every fresh row within minutes with a short kick. Then it kicks our certified files.
- Chain kicks after the first leg. k2-593-7c44e5fe moved 3e-9 of side. k2-642, k2-655, k2-968 and the fourth 695 leg found nothing lower. Only 695 paid on its second and third legs (1.82e-5 and 1.91e-5 below the bar).
- The re-open scan of round 29 files read 75698 files. 17 n certified below the bar, and we re-opened none of them. The round 28 assembler had dropped each one for a reason the round 30 rules keep, or classfill had refused it after a full walk.
- Fresh near files close to the bar side. At 17:15 UTC we swapped the last three held kicks for 900 s kicks of three fresh designs nobody had claimed. These were the stair-c 812 (4.9e-6 of side above the bar), the modules 975 (2.0e-7 above) and the modules 871 (2.4e-6 above). 812 and 975 found nothing lower. 871 reached 1.44e-9 of side below the bar, which is the basin of the held row and below the score rule.
- Three late follows (queued 17:27 UTC, cut at 17:45 UTC). Our kick of k123's 693 moved 8.0e-7 of side and certified, but harvest held a row 1.1e-12 lower. Harvest's 401 and midm's 875 found nothing lower.

### Source rules we applied

- Main 12:40:55Z and 13:32:00Z. A held row is our own layout, and the share of a held ancestor never refuses a row. A tree that takes a withdrawn public-first file directly stays out, even when it also reaches held rows. The files named are `take-harvest-r26/695.csv`, the harvest round 26 814 collector file 5a4c0cdb and the forensics round 22 donor 799-986b3b6d. So our round 28 695, 694 and 546 stay out. We asked main, and main confirmed it at 13:32 UTC.
- `autopub30.py` holds a row for review when a walk text outside a held label names one of those three files. Our round 29 689 and 802 reach the 799 donor, but through the record of `take-forensics-r22/799.csv`. That file is the held round 22 799. The assembler decides on 802, because border and backlog read it as a direct parent.
- A kick of our byte extract of a held row gets no share gate. The extract has no record beside it, so `quench_walk.py` reads it as a public-first start. The held 695 reads 0.511 against the best-of-1105 row.
- Our kick of backlog's 687 certified 2.08e-6 below the bar at 17:01 UTC, and we kept it out. `quench_walk.py` reached the forensics round 22 donor 685-6b47294817b9f93dad47, which harvest's 14:04 and 14:06 UTC lines name as a direct public parent at share 1.000. Backlog then showed that the donor sits only inside the record of the held round 28 b 687, which is held ancestry. By then backlog's own 687 was lower, so the question did not change our take.
- Our kick of the midm 412 certified 4.56e-5 below the bar, and we keep it out. Its tree takes the malyshevdanil atlas 412 directly, and that file reads 1.000 against the best-of-1105 row.

### Tool changes

The tools are copies of the round 29 tools in `take-rebuild-r30/work/tools/`, with these changes:

- `follow30.py`:
  - It skips start bytes that one of our round 29 or round 30 kicks already ran on.
  - It kicks a near file only when the file is 1e-7 or more of side below the bar.
  - It respects a claim of another lane only when the claim is a 900 s kick. Backlog claims almost every row with a short kick, and respecting those claims starved our follows.
  - It writes a claim line for each job that it queues.
  - It skips each lane:n pair that is listed in `work/skip.txt`.
  - It skips files under `gather/` and files bigger than 2 MB. A midm claim line named the whole submission `gather/round28-2026-11-15b.csv` as a start. The near step read all of it, and the follow reached 3.3 GB and blocked the collector for 16 min.
- `autopub30.py`:
  - It queues a chain kick (`k2-`) of every certified row whose kick moved the side by more than 1e-6.
  - It adds the share hits of `quench_walk.check`. These are skipped on our byte extracts of held rows.
  - It holds a row when a walk text outside a held label names one of the three files that main named.
  - A chain key takes the reviewed note of the key that has the same start.
- `rows30.py`:
  - It takes the source from the note when the start has no record (a held extract).
  - It names the pinned side when the start is a near file.
- New tools:
  - `review30.py` writes a reviewed note and sends the key back to autopub.
  - `recheck30.sh` runs `pub30.py` every 5 min until 17:54 UTC, so `take.tsv` drops a row when a live take beats it.
  - `scancert30.py` and `dupes30.py` support the re-open scan of round 29 files.

### Measured dead ends

- Held kicks of rows whose source is a plain public file or an fq quench of one: 19 kicks of 900 s, one row of 1.1e-10. The room below such a row is gone after the first fq quench. Change before a repeat: kick a held row only when a lower layout of the same n was seen (a skeptic drop, a near file below the bar).
- Chain kicks of a row whose first kick moved less than 1e-4 of side: 968 (8e-6) gave nothing. Of the chains after larger moves, only 695 paid (593 1.9e-3, 642 1.7e-4 and 655 1.4e-4 gave nothing).
- Follows of rows that backlog claims: 8 certified layouts landed behind backlog's own kick of our file or of the same basin. Change before a repeat: follow only rows nobody claimed in the last 10 minutes, or kick for 900 s the rows that only short kicks touched.

### Next

1. Kick the held row of every n that the round 30 skeptic drops, at once, for 900 s. Chain while a leg moves more than 1e-4 of side. The held 642 and 695 gave 6.69e-6 and 1.91e-5 this round in the room that the round 28 skeptic opened.
2. Kick our own rows of the previous round that certified at its deadline. Our round 29 593 moved 1.94e-3 of side in one 900 s kick (7.95e-5).
3. Give a 900 s kick to fresh certified rows of other lanes, but only to rows that no lane claimed in the last 10 minutes. 655 and 968 paid, while 10 layouts of 7 n landed behind short kicks of the same basins.
4. Stop held kicks of rows whose source is a plain public file or an fq quench of one. 19 kicks gave one row of 1.1e-10.

## Round 31

`take-rebuild-r31/STATE.txt` holds the record. The boxes were boxB (2 processes), boxE (1 process) and boxD (1 process, the slot of the retired modules lane). The table of every measured job (142 jobs) is `results/rebuild-r31-2026-11-16.tsv`. The bar is `round31-briefs/bar31.tsv`, the held round 30 c file.

The first agent stopped at 22:52 UTC on a usage limit. The background drivers ran on to the 00:15 UTC job deadline and published 405 and 928 in that time. A revived agent closed the round at 00:07 UTC.

### Result

These rows are in the take at 00:21 UTC (gain on bar31):

| n | score | gain | what |
|---|---|---|---|
| 405 | 0.025309025284 | 1.809e-06 | our 900 s kick of the quench round 31 405 |
| 926 | 0.014469174188 | 1.826e-06 | our 900 s kick, no probe, of the held 926 (a room) |
| 928 | 0.014078373639 | 9.154e-09 | our 900 s kick of the k123 round 31 928 |

The sum is 3.644e-6 on the bar and 3.636e-6 beyond the other live round 31 takes.

Four more of our certified rows started rows that backlog holds now. Backlog's short kicks of our rows went a little lower each time:

| n | our gain | backlog's gain | our start |
|---|---|---|---|
| 910 | 1.470e-05 | 1.471e-05 (7e-10 lower) | 900 s room kick of the held 910 |
| 548 | 8.464e-06 | 8.967e-06 | 900 s kick of backlog's 548, then a chain leg |
| 654 | 4.247e-06 | 4.305e-06 | 900 s room kick of the held 654, then a follow |
| 761 | 3.699e-07 | 1.943e-06 | 900 s kick of the held 761 |

### What gave the gains

- Rooms. A room is a held row of an n where we know a lower layout that is out for its source, or where the round 30 skeptic dropped a row. We gave each one a 900 s kick of the held row with no probe. 3 of 11 rooms paid: 910 moved 4.44e-4 of side (1.47e-5 of score), 926 moved 5.56e-5 (1.83e-6) and 654 moved 3.06e-5 (1.20e-6). 972 (two seeds), 814, 646, 851, 807, 694, 642 and 546 found nothing.
- The late find. In the three room kicks that paid, the first find above 1e-8 of side came at 183 s (910), 281 s (654) and 299 s (926). A 120 s probe would have stopped all three.
- Follows of fresh rows of other lanes. 4 of 51 certified a row. Backlog's 548 moved 1.70e-4 of side (8.44e-6). The others were backlog's 654 (4.25e-6), quench's 405 (1.81e-6) and k123's 928 (9.2e-9). From 21:37 UTC on, follows and chain legs ran 900 s with no probe.

### Kicks that gave no row

- Held first kicks without a room. 53 held first kicks ran. Only the four room kicks (910, 926, 654, 761) moved more than 1e-8 of side. 19 more found only fq rounding of about 1e-9 of side.
- No-probe reruns of plain held rows. We reran 15 held rows that the 120 s probe had stopped, this time 900 s with no probe. The first 10 that finished were dry. Of all 15, only 859 moved more than rounding (2.3e-8 of side), and twoshort's live 859 is lower.
- Board-gap rooms. We tried n where the board of 2026-11-09 sits 1e-7 to 3e-5 below bar31. 549, 755 and 684 found nothing, and 536 and 487 found fq rounding only. We dropped five more unrun.
- Chain legs. 1 of 8 moved (k2-548, 4.7e-7 of side, 2e-8 of score).
- The 20 follows that ran after 22:52 UTC found nothing lower. These were 911, 548, 761 (twice), 800, 936, 405, 695, 811, 805, 909, 646, 342, 818, 971, 635, 601, 509, 743 and 692.
- Races. Backlog's 180 s lkicks of our fresh rows beat us on 910 (by 7e-10), 548 and 654 within minutes. Our 909 follow certified only 2.8e-11 under twoshort's 909, so we left it out.

### Tool changes

- `rebuild_run.py`: `kick:SECONDS:PROBE` stops a kick at PROBE seconds when no find has gained more than 1e-8 of side. `scan:SECONDS:MODES:DONOR` runs drop1 or grow1 from a layout of n+1 or n-1. A control showed that the probe can go both ways (a child with a find ran on, a child with none stopped at the probe).
- `rebuild_probe_watch31.py`: a watcher beside the workers on each box. It applies the probe to the `# FIND` gain, because the worker's own probe passed on any raw file, and the first try of a held row is often an fq polish of 1e-9 of side.
- `rebuild_autopub31.py`, `rebuild_follow31.py`, `rebuild_feedheld31.py`, `rebuild_hq31.py`: they post a claim line with the start's sha256 before each kick, and skip bytes or an n another lane claimed in the last 60 minutes (rule 6b). Chain legs and follows run 900 s with no probe.
- `rebuild_scanwork31.py` and `rebuild_scancert31.py`: a light scan of the per-n files in old take dirs against the bar, by bounding side, then a certification of each hit.
- Every published cert now has a `cert/<job>.csv.source.json` sidecar with its take.tsv source and licence. Without it, a cert whose row has left the take walks as "no root" with a public-first share hit (548: 0.485 at 1e-3; 654: 0.800). With it, `quench_walk.check` of backlog's 654 walks clean to the held 654 of round 30. Backlog's 548 reaches the held 548 of rounds 30 and 23. Its one hit sits inside the held 548 record of stair-c, where a pinned near file was rebuilt at its own path.

### Measured dead ends

- drop1 and grow1 from fresh n±1 rows. drop1 squeezes the donor side by only 5e-4 to 1.1e-3 (740 needed 1.88e-3 and ended 2.1e-4 above). grow1 grew the side by 6.9e-2 against a room of 2.17e-2.
- Re-open scans of old take dirs. `take-*-r30` (94397 files) and `take-*-r20..r28` (450849 files) gave 99 and 592 layouts below bar31 by bounding side. Every one that certified was out for its source, overlapped or sat at the bar. Their only use was to point at the 926 and 654 rooms.
- No-probe reruns of plain held rows, and board-gap rooms (above).

### Next

1. Kick the held row of every room at once, 900 s with no probe. A room is an n that the round 31 skeptic drops, or an n where a lower layout is known but is out for its source. 3 of 11 paid this round, and every find came after 180 s.
2. Follow fresh certified rows of other lanes that moved more than 1e-4 of side with a 900 s kick, no probe, within 10 minutes of the handoff line. 548 and 654 paid, and the short follows after ours went lower again, so those basins were still moving.
3. Chain a 900 s leg from every cert that moved more than 1e-6 of side, and claim the cert bytes before publishing. Backlog took 910, 548 and 654 from us by 7e-10 to 5e-7 with short lkicks we did not run ourselves.
4. Write the `.source.json` sidecar beside each cert when it is published, not at the end of the round.
5. Stop no-probe reruns of plain held rows, board-gap rooms, drop1 and grow1, and re-open scans of old take dirs.

## Round 32

`take-rebuild-r32/STATE.txt` holds the record. The boxes were boxB (2 processes) and boxE (1 process). The bar is `round32-briefs/bar32.tsv`, the held round 31 b file. The table of every measured job (206 jobs) is `results/rebuild-r32-2026-11-16.tsv`. The box queues ran dry at 16:20 UTC. From then to the 17:15 UTC deadline the workers had no job.

### Result

These rows are in the take at 17:23 UTC (gain on bar32):

| n | score | gain | what |
|---|---|---|---|
| 911 | 0.016163560628 | 3.419e-05 | our 900 s room kick of the held 911, then two chain legs |
| 464 | 0.020388567170 | 7.741e-08 | our 150 s lkick of the held 464 |
| 811 | 0.015079392734 | 3.197e-08 | our second-seed 300 s lkick of the held 811 |
| 551 | 0.019069415353 | 4.395e-09 | our second-seed 300 s lkick of the held 551 |

The sum is 3.4307e-5 on the bar. No other live round 32 take holds a lower row for these four n, except the k123 911 that rule 3 puts out (see below).

Three more of our certified rows are now held by quench. Quench ran one fq quench of each of our files, and each went a little lower:

| n | our gain | quench's row is lower by | our start |
|---|---|---|---|
| 378 | 2.074e-07 | 2.0e-10 | 150 s lkick of the held 378 |
| 854 | 1.315e-08 | 1.8e-10 | 150 s lkick of the held 854 |
| 934 | 1.313e-08 | 6.3e-09 | 150 s lkick of the held 934, then an lkick leg |

### What gave the gains

- The 911 room. A room is a held row of an n where we know a lower layout that is out for its source. The held 911 is the public jazivxt root 116f72f56b. Backlog's bd788481 sat 3.4e-5 of score lower, and the round 31 skeptic dropped it because its start was a withdrawn file. One 900 s kick of the held row moved it 1.03e-3 of side. The chain legs then moved it 2.0e-6 (k2), 6.6e-8 (k3) and 1.9e-7 (k4) of side. A leg from the k2 certificate (k5) moved it 5.0e-7 more, and the leg after that (k6) found nothing.
- The 911 share measure. k123's 911 sits 7.2e-9 of score below ours, and k123's final take still holds it. We measured it with `share31.py`: 0.056 at 1e-3 and 0.407 at 1e-2 against the non-own 1105 versions. Its 911 band is quench's fq of harvest's public root decbd4b1, which was never held. So it is a public-first tree at 0.4 or more at 1e-2, and rule 3 puts it out. `rebuild_pub32.py` skips the live rows listed in `work/outlive.json`, so our 911 stays in the take. Two takes now hold 911, and the assembler picks one. Our own 911 reads 0.247 at 1e-3 and 0.415 at 1e-2. It is built on a held row, so rule 2 makes it our own layout, and the measure is for the record only. Harvest's audit at 16:09 UTC also left our 911 ungated as a held rebuild.
- Short lkicks. We ran 150 s of `invent_rest.py --modes lkick` on held rows whose bytes no lkick claim of rounds 29 to 32 names. This is the kind that moved 12 of 121 held rows for twoshort in round 31. 4 of 94 first lkicks moved: 854, 378, 934 and 464, by 3.8e-7 to 4.0e-6 of side. All four came from list 1, the held rows above the board side of 2026-11-09. A second 300 s seed of the dry list 1 rows moved 2 of 51 more: 811 (9.1e-7 of side) and 551 (1.0e-7 of side).

### Kicks that gave no row

| What | Jobs | Moved | Note |
|---|---|---|---|
| First kicks of fresh round 31 movers, 900 s, probe 330 s | 12 | 0 | held rows whose final round 31 bytes had no long kick |
| Room kicks of rigid held rows, probe 330 s | 5 | 0 | 442, 485, 530, 577 and 585. 585 found 1.2e-9 of side, which is fq rounding |
| Room kicks of 851 and 972 | 2 | 0 | 851 found 1.4e-9 of side (rounding). Both were dry in round 31 too |
| Follows of fresh rows of other lanes, 900 s, probe 330 s | 21 | 0 | 15 of backlog's rows, 2 of quench's and one each of twoshort, forensics, soft and k123 |
| lkick list 1, held rows above the board side | 61 | 4 | the rows above |
| lkick list 2, held rows at or below the board side, n 300 and up | 19 | 0 | |
| lkick list 3, held rows of n 100 to 299 | 14 | 0 | twoshort ran the same n at the same time, and the claim lines kept us apart |
| Second seed, 300 s, of dry list 1 rows | 51 | 2 | 811 and 551. 6 rows of the 57 were skipped for other lanes' claims |
| lkick legs of our certified lkick rows | 6 | 1 | l2-934 moved 9.1e-8 of side, but quench's 934 was lower |

There were no new rooms. Stair-c's withdrawn 812 rows sit above bar32. Quench's and k123's withdrawn fq of them were only 3.9e-9 of score under the bar. Stair-c's withdrawn 997 sits above the held 997.

### Tool changes

- `rebuild_run.py`: `lk:SECONDS` runs `invent_rest.py --modes lkick` with no fq inside, and writes the lowest legal raw file to `best.csv`. The collector certifies it and queues one fq quench of the certified file, as before. In a control, a held 199 scaled by 1.002 came back to the held side plus 2e-9 in 40 s.
- `rebuild_lq32.py` queues one lkick of a held row. It skips bytes that any other lane has lkicked in rounds 29 to 32, at any time. `SEEDTAG` gives a second seed its own key.
- `rebuild_feedlk32.py` keeps every box slot fed from `work/lkorder.txt`. When that list is done, it runs `work/lkorder2.txt`, a second 300 s seed of the dry list 1 rows.
- `rebuild_autopub32.py` chains 150 s lkick legs (l2 to l8) while a published lkick step moves more than 1e-8 of side. It runs no 900 s kick legs on lkick rows. It writes the `.source.json` sidecar beside each certificate when it publishes the row. It also measures `share31.py` on each certificate built on a held public-first row, for the record only.
- `rebuild_pub32.py` skips the live rows of other lanes listed in `work/outlive.json` (n and sha256), each with its reason. It keeps a per-n csv in place when its row leaves the take, and copies it to `near/`.
- `rebuild_follow32.py` reads the WITHDRAW lines of `handoff-r31.log` and `handoff-r32.log`, by path and by sha256. A control caught the withdrawn quench 911 file c171f6d83c60 and let the held 911 root 116f72f56b through.
- `rebuild_table32.py` reads the done files of two boxes and names the lkick kind.
- `rebuild_restart_idle32.sh` replaces each box worker with one on the new code when the worker is between jobs. `rebuild_holdlk32.sh` keeps lk jobs out of the queue until every old worker is gone.

### Next

1. Kick the held row of every room where that row is a non-rigid public root, 900 s. The 911 room paid 3.4e-5. The five rigid held rows (four share the side fraction .525789210, and 585 sits at 420/17) were dry.
2. When a live row of another lane beats ours, measure `share31.py` on it at once. k123's 911 read 0.407 at 1e-2 and is a public-first tree, so rule 3 put it out and our row stayed.
3. Run lkicks only on held rows above the board side, and give each dry one a second 300 s seed. First seeds moved 4 of 61 there, against 0 of 19 at or below the board side and 0 of 14 for n 100 to 299. Second seeds moved 2 of 51.
4. Keep a third list ready so the box queues do not run dry. Ours ran dry at 16:20 UTC, 55 minutes before the deadline.
5. Claim our fresh lkick rows for an fq quench before we publish them. Quench's single fq of our files took 378, 854 and 934 by 2e-10 to 6e-9.
6. Stop first kicks of fresh movers (0 of 12), room kicks of rigid held rows (0 of 5) and probe-gated follows (0 of 21).

## Round 33

`take-rebuild-r33/STATE.txt` holds the record. The boxes were boxB (2 processes) and boxE (1 process). The bar is `round33-briefs/bar33.tsv`, the held round 32 a file. The table of every measured job (219 jobs) is `results/rebuild-r33-2026-11-17.tsv`. Our share of the held rows this round was n 700 to 1000.

### Result

Our take is empty at the end of the round. We certified two rows, and backlog then went lower on both:

| n | our score | gain on bar33 | backlog's row is lower by | our start |
|---|---|---|---|---|
| 812 | 0.014964584717 | 2.746e-07 | 3.65e-06 | 900 s kick of the held 812, no probe |
| 911 | 0.016163560342 | 2.865e-10 | 2.27e-09 | 900 s kick of the held 911, no probe, then quench loops |

Backlog follows fresh certified rows with a 180 s lkick. It took both of our rows within the hour. So both n move in the round, and the gain is counted under backlog.

### What we measured

- The two held kicks of override 8 both moved. The 812 kick found its only step at try 54 of 55, 872 s into the 900 s run. A 330 s probe would have stopped it. The 911 kick moved 7e-9 of side, and quench loops added 2e-9 more.
- First lkicks of held rows were dry. We ran 150 s of `invent_rest.py --modes lkick` on every held row of n 700 to 1000 whose bytes no lkick claim names: 136 jobs and 0 moves. List 1 had 12 rows above the board side, and list 2 had 1 row at the board side. List 3 had 150 rigid-looking rows, with a p/q side, a shared side fraction or a side of a + b*sqrt(2)/2. Many rigid rows ended in seconds. 127 more rows were skipped because some lane had already lkicked their bytes.
- Room kicks were dry. We ran 900 s with a 330 s probe on held public roots: 742, 744, 925, 743, 974, 979 and 814. None moved more than 1.5e-9 of side, which is rounding. Border had already claimed 998.
- Follows were dry. Only two rows of other lanes in our slice were free to take: backlog's 753 and 812. Both 180 s lkicks found nothing. The fresh rows of k123 (734, 752) and forensics (789) were claimed by other lanes first.

### The 740 drop1 pipeline

Round 31 measured a rule for drop1 scans: one scan runs only when the donor side minus the bar side of n-1 is under 3e-3. Over all n against the lowest live rows, one pair qualified in our slice: 741 to 740. The held 741 sits 1.33e-3 of side above the bar side of 740. The bar side of 740 is 471/17, a rigid row.

- Six 900 s drop1 seeds of the held 741 squeezed 1.29e-3 to 1.31e-3 of side. The best came to 2.7e-5 above the bar side.
- `midm_scan` writes only results below its incumbent. So we gave it the held 740 scaled by 1.00005 as the incumbent. Then every new best try is saved as a raw file.
- The first 600 s lkick of a near miss moved it about 1.5e-5 of side. The best reached 27.705894934, 1.26e-5 above the bar side 27.705882354.
- Nine more lkick seeds of that best moved nothing. A 900 s walker (`--modes seg,lkick --walk 3e-6`) also moved nothing in 92 tries. Two 900 s `midm_scan` kicks of the first near miss moved nothing.
- `work/tools/chain740.py` then ran a pool. Each fresh drop near miss got one first lkick, and each lower result joined the pool. The first lkicks stopped between 27.7058948 and 27.7059100. The lowest of the 52 pipeline jobs is 27.705894782, 1.243e-5 above the bar side.

The pipeline is a dead end at this gap. The drop1 squeeze plus one lkick gets within 1.3e-5 of a rigid bar row. Nothing we tried crossed that last part.

### Tool changes

- `rebuild_run.py` quench mode now runs the full fq loop (default flags, then the deep flags, up to three rounds), as lesson 6e asks. The positive control was the held 199 scaled by 1.0005: the loop came back to 6.8e-10 below the held side in four fq runs.
- `rebuild_run.py` has a new mode, `lk:SECONDS:w`. It runs the `invent_rest.py` walker over `seg,lkick`.
- Do not take a quench result lower than the certificate by 1e-10 of side. The finesafe dilation puts each certificate about 6e-10 of side above its raw side, so every quench looked lower and the collector queued them without end. The 911 chain ran ten quenches that way. The collector now asks for 3e-9 of side below both the certificate and the last raw side.
- `follow33.py` runs 180 s lkick follows, only on n 700 to 1000. It takes rows of non-self-chaining lanes at once, and never takes bytes that any lane has lkicked.

### Traps

- Restarting the box workers through `restart_idle.sh` over ssh lost boxE worker. The worker was killed, and its replacement did not start. The slot was idle for 16 minutes. The killed worker also left a claim (`claims/c740-d15`) with no `done.json`. The new worker skipped that job, and the chain driver counted it as pending, so boxE sat idle another 48 minutes. After a worker restart, check that every claimed key has a running process or a `done.json`.

### Next

1. Give the unprobed 900 s kick to more held rows that are public roots. The 812 find came at 872 s and the round 32 911 find at about 280 s. A 330 s probe stops the late ones. Room kicks with the probe gave 0 of 8 this round.
2. Stop first lkicks of held rows in n 700 to 1000 until the held file changes. This round 136 gave 0, and only 13 non-rigid rows were left that no lane had lkicked.
3. Stop the 740 drop1 pipeline. Its 52 jobs stalled 1.24e-5 of side above a rigid bar row. Run drop1 again only when a new n+1 row comes within about 1.3e-3 of the bar side of n.
4. Hand our certified rows to backlog at once, and do not race it. It took both of ours within the hour.

## Round 35

Round 35 ran from about 10:35Z to 16:25Z on 2026-11-17, against bar35 (the submitted round 34 a file). The lane owned the deep kicks of n mod 4 = 2: unprobed 900 s `midm_scan` lkick,kick seeds, rows with one earlier deep kick first, two seeds per geometry at most. Slots: boxB 2, boxE 1.

### What paid

Four rows count, 2.0519e-5 of score together. Each one is a byte copy of the held round 34 a row, kicked once, then certified with finesafe at 2.2e-11 and quenched with the full fq loop.

| n | seed | gain on bar35 |
|---|---|---|
| 546 | first | 8.703e-6 |
| 594 | second | 6.701e-6 |
| 554 | first | 5.115e-6 |
| 702 | first | 3.5e-10 |

- 33 held-row kicks ran on 22 n. Four moved below the bar. 914 and 762 moved about 1.4e-9 of side, which is under 1e-10 of score, so they do not count.
- The second kicks of our own certified 546, 554 and 594 (two seeds each) gave 0 of 6. A kick on a geometry that just paid comes back at its own certificate.
- The rigid-row test gave 0 of 6: two seeds each on 530, 918 and 762, the three closed-form class 2 rows with a board gap of 1e-5 or more. 762 sits at side 28 and stayed there. It agrees with quench's 0 of 10 on rigid rows.
- The final full fq loop (default flags, then polish) of the four rows moved each one 1.5e-14 to 1.0e-11 of score. That is below the 2e-10 legging floor, so the certified files stay as they are.

### Measured gaps

- `quench_walk.walk` stops at 3000 files and still reports clean. 10 of 18 held-row walks hit exactly 3000. `tools/qwalkcap.py` raises the cap to 40000 and blocks a walk that reaches the cap. The held 593 walks clean at 6566 files, so classfill's round 34 refusal came from its kick's own record.
- The boxes idled from about 14:10Z to the end. The class 2 list and the rigid test were done by then, and no lane handed a row. We posted the idle slots at 13:35Z.

### Next

1. Keep the deep kicks of n mod 4 = 2 on held rows that changed geometry since their last two seeds. The first seed paid three times out of four this round.
2. Do not kick our own certified rows again in the same round (0 of 6). Hand them to backlog at once, as now.
3. Stop deep kicks of rigid rows (0 of 6 here, 0 of 10 for quench).
4. Fill idle slots from other lanes' fresh near files (k123 threeway28, invent fresh) after 14:00Z instead of waiting for handed rows.

## Round 36

Round 36 ran from about 19:20Z to 23:45Z on 2026-11-17, against bar36 (the submitted round 35 a file). The lane started late. Slots: boxB 2, boxC 2. boxE had a budget of 0.

### What we ran

- The held-row list: one unprobed 900 s `midm_scan` lkick,kick seed per held row with no seed since its current geometry. `deep36.py` found 10 such rows. Nine of them were fresh rows of round 35 that took 900 s seeds then, as follows of other lanes. Only 683 was left. Its one seed was dry.
- The k123 near donors, ranked by board room, `(bar36 - board) - (donor - bar36)`. Skip a donor with no room, a donor 1e-4 or more above the bar, and an n whose live row is more than 1e-6 below the bar. Two seeds per geometry across all lanes. `rebuild_donorfeed36.py` does this. It posts the claim, waits 5 s, and reads the log again.
- From 21:05Z, forensics' fresh rectangle near files also joined the pool, the lowest file per n. `rebuild_nearwalk36.py` walks each file first at a cap of 100000 files.

### What we measured

- 59 jobs on 19 n: 965 18, 910 10, 367 3, 491 3, 807 3, 911 3, 972 3, and one or two on each of the rest. 11 found nothing below their start. No row certified below bar36 by more than 1e-10.
- Most donor kicks fell back into the held geometry. 448 moved 1.06e-3 of side and 367 moved 1.91e-3, and both ended 5e-11 to 8e-11 of score below the bar. Nearly all 965 kicks ended at side 31.5620085801, which is 6.7e-10 of side below the bar side.
- 972 certified 1.1e-8 below the bar twice. Backlog and then k123 held lower live rows, so neither counts. 911 certified at k123's own take row.
- 910: seed b of donor c2de5ca6 ended 1.29e-8 of side above the bar. Two rounds of the full fq loop took it 4.0e-10 of side below the bar. That is 1.3e-11 of score, under the 1e-10 rule.
- 750: a donor kick moved 1.98e-4 of side and stopped 9.7e-7 of side above the bar. Forensics' 750 rectangle near file stopped at the same place. We posted ours to near/.
- One quench_walk of a large tree takes 9 to 18 minutes on boxA at load 20 to 30. Our first donor walk held the slots idle for 12 minutes. k123's certified lines already carry an uncapped walk of the same bytes, so the feeder takes that record. Our own walk still runs on any find before it is published.
- `quench_walk.check` now takes `cap=` and passes it to `walk` itself. Setting the default of `walk`, as `qwalkcap.py` did in round 35, no longer reaches the walk. `rebuild_qwalkcap36.py` passes `cap=` to `check`.

### Next

1. Stop seeding k123 donors on n where the held row is a strong local minimum (965, 448, 367, 807). Here 14 of 59 seeds ended within 3e-9 of side of the bar, which is the held geometry.
2. Group donor byte variants by score within 1e-9, not 1e-12. k123 posts many files of one join 1e-10 apart, and each one looked like a new geometry.
3. Give the walkers their own slots early. A forensics near file waits 10 to 15 minutes for its walk, and the boxes idled while it ran.
4. Our held-row list is spent: every held row without closed-form sides already has a seed on its current geometry. A new round needs fresh geometry from k123, forensics or a fresh public file before this lane has work.
