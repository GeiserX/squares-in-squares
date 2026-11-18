# Backlog lane

The lanes of round 24 left large saved queues unstarted, because each lane runs fresh work first. The backlog lane runs items from those queues with the owner lane's own tool. It claims each item in the handoff log before it starts, so the owner skips it.

## Tools

| File | What it does |
| --- | --- |
| `backlog_base.py` | Writes the per-n base bar. Until a `main -> all: BASE` line, the clean bar is the lower of the held gate details and the frozen r24 take rows that the r24 assembler traced clean (`take-assemble-r24/trace.log`: group A, no issues, no blocks). Rows at the out counts never lower it. The strict bar also takes every other r24 row. |
| `backlog_queue.py` | Builds one ranked queue over the saved queues of the owners. It walks the recorded ancestry of each entry and drops the entries that reach a source that is out. |
| `backlog_worker.py` | One slot on the compute box. It runs an item with the owner's tool, then floatsafe at 2.2e-11, then one fq quench from the certified file (`midm_fqonce.py`). |
| `backlog_ctl.py` | The controller on boxA. It claims items in the handoff log, sends them to the slots, collects the results, certifies them against the clean bar and the live r25 takes, and writes the take by rename. |

### The ancestry walk

The walk reads the entry's own source and licence text first. Then it reads every scratch file path that text names: the `.json` sidecars of the file and, for a per-n file of a take dir, the `take.tsv` row of its count. It goes up to six levels deep. The verdict is stored once per path, so a parent shared by many entries is read once.

An entry is out when its text or a parent's text matches one of these:

- a Samanyu-dev seed. The forensics classifier `forensics_policy.classify_text` reports `seeds` or `unknown`.
- `penguin069`, `joegun` or `squares_in_squares`.
- the prvsiyan best-of-1105 file.
- a path or file of the out counts 639, 691, 745, 858, 918, 980, 981 or 801.
- a 735, 790, 228 or 985 file of a round up to 23. That is the tree with seed 365, which local labels missed in round 24.
- an unresolved ancestry.

The first version joined the text of every parent into one string. That string grew with each level, and the build ran for more than 12 minutes at load 30. The memo of verdicts by path builds the same queue in about one minute.

### The adapters

| Owner | Tool and settings |
| --- | --- |
| invent | `invent_rest.py N START RUN --seconds S --seed K --modes lkick --bar SIDE` with the owner's recorded seconds, seed and fq flag (the settings of `take-invent-r24/work/worker24.py`). |
| harvest | One fq quench with the flags of `take-harvest-r24/work/remote_run.py` (`--no-alm --loosen 1.0 --pit 40 --flip-top 8`), 120 s. The start goes through `midm_scan.to_fq`, because fq reads its own text format. |
| readers | `family_readers.py walk SPEC donors details.csv OUT` with the flags and environment of `take-readers-r25/work/box/run25.sh`, from a copy of the readers box. A walk can end at several counts, so each count gets its own certification and quench. |

A certified find of the invent queue gets one leg: `invent_rest.py` again from the certified file, with a new seed, 300 s and no fq inside. Legs continue while a leg gains 1e-6 or more, three at most.


## Round 26 (2026-11-14, 12:47Z to 17:25Z)

### What ran

The round 25 agent died at 23:50Z, and its controller crashed at 00:55Z on a readers spec file that the readers lane had removed. So round 26 started from the round 25 STATE file. The base bar is `gate/cand-round25-1114b/details.csv`.

The slots were boxB 2 and boxC 1. boxC has no shared base, so the lane made its own venv there (uv, python 3.12, scipy 1.18.1) and copied fq from the boxB base. The worker reads the python and fq paths of a box from `box.json`.

Three kinds of item ran:

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 to 300 s, then one fq quench from the certified file | each certified row of a live `take-*-r26` dir that is below the bar, once per file content |
| held | `invent_rest.py` lkick, 300 s, then the same quench | the held round 25 b layout of the 44 n that rounds 24 and 25 moved (not 873) |
| midm | `midm_scan.py` kick,lkick, sigma 0.04, `--stop6`, then the same quench | the unstarted raw designs of `take-midm-r25/work/pending-final.json` within 3e-5 of the bar, at most 3 per n |

A certified find gets a leg from its own file, with a new seed, while a leg gains 1e-6 of score or more, three legs at most. An item whose start is more than 3e-5 above the bar or a live take is skipped. A newer and lower file of the same take replaces a follow item.

### The ancestry gate

Every row passes the independent walk of the round 25 assembler (`take-assemble-r25/deep25.py`) before it goes into the take. The controller imports the walk and writes no bytecode into that frozen dir. The walk follows every file, sidecar, ledger row, ancestry record and held reference that the source cells name. A row is refused on any Samanyu-dev signal, a withdrawn tree, the CC BY-SA file, penguin069, or a walk that hits its cap. At 13:22Z the rebuild lane found that ten held rows use the far zone 811h.F1 of the Samanyu-dev seed. They are 698, 753, 809, 810, 811, 868, 869, 870, 929 and 931. So a row at one of those n, or a row whose walked text names 811h, is refused too. The take cell records the result of the walk.

### Controls

- midm adapter, new this round: the held 30 scaled by 1.01 (score 0.104574) came back to 0.0954451150562, 2.0e-13 above the bar 0.0954451150560. It moved down and was not published.
- invent adapter, unchanged: on 30 it made no try, because 30 has no tilted square. This is the same as in round 25. The round 25 positive control on 978 stands.

### The gate changed during the round

- The walk of the round 25 assembler reads `samanyu_bestfit` as a seed. The harvest lane writes that name in a negative finding: "not a layout of rules a-d (max centre distance: prvsiyan 1105=X samanyu_22249=Y samanyu_bestfit=Z)". The controller drops that clause only when every distance is 0.55 or more. A closer distance stays a signal.
- A geometry guard runs on every result before publication. It imports `take-harvest-r26/work/tools/audit_ac.py` and measures the smallest symmetric centre distance from the result to each excluded layout of rules a to d for that n. Below 0.55 the row is refused. The control: the prvsiyan 1105 layout of 501 measures 0 and is refused.
- The line is 0.55 because the quench lane drew it there at 15:01Z. The harvest 695 sits at 0.238 from the prvsiyan 1105 row of 695, and nine more harvest rows sit under 0.55. Every row built on them was refused: k123 695, quench 748, forensics 694 and 748. The backlog 706 was withdrawn, because its harvest parent records 0.542.
- The rebuild lane traced the held r25b rows of 42 n to the Samanyu-dev seeds 811, 503, 504, 983 and 861, the bare 921 file or penguin069. A row whose walk reaches a held layout of one of those n is refused. This refused the modules and invent 805, which walk to the held 924 of round 9.
- From 15:10Z a follow or near-pub start is walked before it gets a slot. A start that fails is skipped.
- At 16:36Z the harvest lane measured its 338 near-pub starts. 276 of them are copies of an excluded layout: 0.4 or more of their squares lie within 1e-3 of a layout of rules a to d. Only the 62 starts left in `work/near-pub/queue-fresh.tsv` are clean. Some of my near-pub claims were out starts (204, 547, 551, 814, 916 and 970). None of my near-pub runs certified, so no row of the take grew from one. From 16:58Z the controller refuses a near-pub result whose start is not in that file, and the unstarted near-pub items were dropped.
- At 17:06Z the take was walked again with the walk of the round 26 assembler (`quench_walk.check`, imported). It found two faults of my own:
  - The geometry note in my licence cells named the excluded sources (`CC BY-SA`, `samanyu_bestfit`). The walk reads those names as positive signals. The note now gives only the smallest distance, and the controller writes it that way.
  - The walks of 632, 850, 909 and 972 reach `take-forensics-r26/near/684-rect.csv` or `near/972-rect.csv`. The forensics lane withdrew those files at 16:40Z for a withdrawn packing identity. These four rows left the take for `near/<n>-backlog-withdrawn-gone-parent.csv`. With them went 1.03e-3 of the gain on the bar.

### What was measured

Counts up to 17:19Z, from `STATE.txt` (`work/scripts/tally.py` in the take dir):

| Kind | Runs | Outcomes |
| --- | --- | --- |
| follow, kick-lane file | 18 | dry: 12, certified: 3, not below a live take: 3 |
| follow, other lane file | 61 | dry: 26, certified: 12, not below a live take: 11, refused: 12 |
| held r25b lkick | 3 | dry: 3 |
| leg or own kick | 16 | dry: 11, certified: 1, not below a live take: 1, refused: 1, above the bar: 2 |
| midm r25 pending | 3 | dry: 2, above the bar: 1 |
| nearpub | 30 | dry: 17, refused: 3, above the bar: 10 |

- **The follow of a certified row of a non-kick lane paid.** These are the harvest, forensics, classfill, quench, k123, soft and modules rows. Most of the gain came from the fq quench of the certified file after the lkick, not from the lkick itself. On the harvest 972 (an alexchilton fault-line layout) the lkick moved the side by 2.4e-7 of score and the quench by 8.1e-5. On the quench 910 the lkick took 5e-5 and the quench 7.5e-5 more.
- **The race was close.** The other follow lanes kicked my files again within minutes. By 16:15Z the midm, invent, forensics or twoshort take was lower than mine on 7 of my 10 certified n, often by less than 1e-8. The assembler takes the lowest row, so each of those steps still counts once.
- **The follow of a kick-lane file paid less.** These are the midm, twoshort and invent rows, which their owner had kicked already. Those runs wait behind the others. After three runs on one n they are skipped.
- **The held lkick was dry**, 0 of 3 (228, 534 and 581). In round 25 it certified 3 of 6. Those six starts were saved invent starts at the bar. The held r25b layouts of 228, 534 and 581 are k123 joins and rebuilds that their owners had quenched.
- **The midm r25 pending kick was dry**, 0 of 3 plus one leg. 650 ended 2.1e-10 above the bar, and its leg did not move it.
- **The near-pub kick was dry**, 0 of 30. These are the fresh public near misses of the harvest lane, 2e-10 to 6e-5 above the bar. Many public designs ended within 1e-13 of the bar, because they are public copies of the layout we hold. Most of these starts were later measured as copies of an excluded layout (see above).

### Results

| n | Bar | New | Gain on the bar | Gain beyond the next live take | Next live take |
| --- | --- | --- | --- | --- | --- |
| 365 | 0.0260093977233 | 0.0258865734476 | 1.228e-04 | 3.428e-05 | take-k123-r26 |
| 595 | 0.0190850398380 | 0.0190840762612 | 9.636e-07 | 9.636e-07 | none |
| 910 | 0.0166369572472 | 0.0162819695662 | 3.550e-04 | 3.550e-04 | none |
| 971 | 0.0159552112025 | 0.0154853144677 | 4.699e-04 | 4.699e-04 | none |
| 986 | 0.0142364919283 | 0.0142309293998 | 5.563e-06 | 2.169e-07 | take-k123-r26 |

Sum: 9.542e-04 on the bar, 8.603e-04 beyond the other live round 26 takes, on 5 n.

Five rows stay. The final pass moved 459 and 501 to `near/`, because the twoshort 459 and the quench 501 are lower. The four rows withdrawn at 17:06Z are above.

The results table is `results/backlog-r26-2026-11-14.tsv`.

### Next

1. Follow the certified rows of the non-kick lanes, then one fq quench from the certified file. This paid 12 of 61 runs, and the quench gave most of the gain.
2. Walk every start with the walk of the assembler (`quench_walk.check`) before it gets a slot, and walk the take again before the final pass. The 17:06Z walk found four rows whose parents had left their lane after the certification.
3. Check which version of the forensics `near/972-rect.csv` the withdrawn 972 used (sha256 db36d2772385847c). The quench lane reports that only a later version was built on the withdrawn invent 972. If db36 is the clean version, the 972 at 0.0154213989981 (6.04e-4 below the bar) can come back from `near/972-backlog-withdrawn-gone-parent.csv`.
4. Drop the held lkick (0 of 3) and the midm r25 pending kick (0 of 3). Run near-pub starts only from the clean list of the harvest lane (0 of 30 this round).


## Round 27 (2026-11-14, 19:25Z to 23:55Z)

The round 27 agent died at about 23:10Z on a usage limit. Its controller and workers ran on to the 23:45Z deadline and stopped at 00:00Z. It wrote no report, so this record comes from its `STATE.txt`.

### What ran

The Samanyu-dev rule was lifted in round 27. The bar was `round27-briefs/bar27.tsv`. The slots were boxB 2 and boxC 1, as in round 26.

| Kind | Tool | Start |
| --- | --- | --- |
| re-open | `invent_rest.py` lkick, 180 s, with the start itself among the raw files, then floatsafe and one fq quench | a frozen per-n file below bar27 that `backlog_reopen27.py` gated clean |
| follow | `invent_rest.py` lkick, 180 s, then the same quench | each certified row of a live `take-*-r27` dir below the bar |
| near | `midm_scan.py` kick,lkick, sigma 0.04, 240 s | a new near file of forensics or k123 within 2e-5 of the bar, or of stair-c, modules, border or invent within 1e-8 |

The gate was `backlog_gate27.py`. It ran the share test against the prvsiyan 1105 row, which puts a layout out at 0.4 of the squares within 1e-3. It also ran the walk of `quench_walk.check`, without the hits that name only the Samanyu-dev seed. The box worker ran the share test on each final file.

### What was measured

| Kind | Runs | Outcomes |
| --- | --- | --- |
| re-open | 15 | 5 certified (648, 812, 871, 926, 863), 4 not below a live take, 2 above the bar, 1 refused |
| follow, other lane file | 52 | 37 dry, about 10 certified, 4 not below a live or own take |
| near | 34 | 0 certified: 23 dry, 9 above the bar, 2 not below a live take |
| leg | 4 | 0 certified |

The take held 15 rows, 9.79e-4 on bar27. Most of that gain was the gain of the followed take itself.

### Faults found in round 28

- The 927 row is an lkick of `take-rebuild-r27/927.csv`. Classfill withdrew that chain at 22:13:40Z, because a donor of its k123 pool has a prvsiyan share of 0.84.
- The 932 row is an lkick of `take-k123-r27/932.csv`. K123 withdrew it at 22:54:35Z, because its seed 503 has a prvsiyan share of 1.0. The held 932 is lower, so this row never set the bar.
- The held round 26 b 910 is our round 26 row. Its walk reaches the 684 donor `take-forensics-r24/work/donors/684-6d78315914dc85da2cb4.csv`, which has a prvsiyan share of 1.0. Invent withdrew that tree at 23:50:47Z.

The agent died before it could act on these lines. Round 28 posted them in `handoff-r28.log` at 00:09Z and 00:13Z.


## Round 29 (2026-11-15, 06:01Z to 11:55Z)

The round 28 agent died at about 02:25Z on a usage limit. Its controller ran on to the 05:39Z reboot of boxA. It made 191 runs and held 12 rows, but it wrote no report. Round 29 started the same controller again as round 29 (`BACKLOG_ROUND=29`).

### What ran

The bar was `round29-briefs/bar29.tsv`. The slots were boxB 2 and boxC 1. Each run ended in one fq quench from the certified file on the box, then a floatsafe check at 2.2e-11, with finesafe allowed.

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s | each certified row of a live `take-*-r29` dir below the bar |
| follow midm | `midm_scan.py` kick,lkick, sigma 0.04, 240 s, or 900 s for a row 1e-5 or more below the bar | the same rows, from lanes that do not kick |
| re-open | `invent_rest.py` lkick, 180 s, with the start among the raw files | a frozen `take-*-r28` file below bar29 that the gate passed |
| own | `midm_scan.py` 600 s and `invent_rest.py` lkick 300 s | each row of ours that is the lowest live row of its n |
| seed | `midm_scan.py` kick,lkick, 600 s | the open held seed rows in `take-quench-r29/work/held27/` |
| leg | the tool of the find, 300 s | a find that moved the score by 1e-6 or more |
| near | `midm_scan.py` kick,lkick, 240 s | a near file of another lane close to the bar |

### Changes to the controller

- Certify with `backlog_finesafe.py`, a copy of the border finesafe (the dilation is bisected between the ladder steps). The other lanes certify that way, and a follow must beat their row by 1e-10.
- Rule 3 of round 29: a share match never refuses our own layouts or their descendants. The share test refuses only a start whose first source is public (harvest type).
- The quench_audit rule `r22 745/858 join` matched every forensics r23 donor of 745 or 858 by its folder name. The gate narrows it in memory to the real join (`858-ec97a452`, `745-64c4b4f8`). `quench_audit.py` itself is unchanged.
- A near kick or a follow midm kick is skipped when rebuild or quench already kicks the same bytes at 900 s. The check reads the sha256 prefix in the rebuild `queue-log.tsv` and in the quench claim lines.
- Within a rank, the item with the larger predicted gain goes first.
- Ranks: follow lkicks go first. Follow midm kicks, follows of the kick lanes and legs go next, then own and seed items. Near kicks go last.
- `withdraw_check` runs on every loop. When another lane withdraws the parent of one of our rows, the row moves to `near/` and `take.tsv` is rewritten. A later REINSTATE of the same bytes cancels it. The parent is read from the first byte copy named in the row's source.
- One dispatch walk per start file, so the plain and midm follows of one row share it. Each walk takes about 90 s on boxA.
- Stair-c, modules, border and invent near files get one near kick per n per round.

### What was measured

| Kind | Runs | Outcomes |
| --- | --- | --- |
| follow, other lane file | 35 | 14 certified, 20 dry, 1 not below our own row |
| follow, kick-lane file | 5 | 1 certified, 3 dry, 1 not below a live take |
| follow midm | 10 | 2 certified, 7 dry, 1 not below our own row |
| re-open | 3 | 1 certified (421), 1 not below a live take, 1 refused by the gate |
| own | 10 | 1 certified (587), 8 dry, 1 not below a live take |
| seed | 15 | 1 certified (455, 3.7e-9), 9 dry, 5 above the bar or less than 1e-10 below it |
| leg | 16 | 2 certified, 11 dry, 3 other |
| near | 103 | 0 certified: 69 dry, 34 above the bar |

The ctl made 197 runs. Most certified rows beat the followed row by a small step, then the next lane followed ours. Six certified rows were passed before 11:55Z by a lower row of another lane. They are 504 (twoshort), 594 (rebuild), 689 (rebuild), 752 (twoshort), 916 (border) and 988 (rebuild).

Rebuild and quench already kicked most fresh rows at 900 s with the same midm tool. The sha256 check skipped 40 of our midm kicks for that reason.

Four of the 15 seed kicks stopped after 6 tries (`--stop6`), because 3 of the first 6 tries came back to the start side. Such a row is rigid. Quench measured 5 seed rows of about 27 that moved (420 1.0e-4, 587 3.9e-5, 593 9.2e-6, 594 3.4e-6, 556 6.2e-7). We followed its 420, 587 and 594 rows and took them lower.

### Faults found

- The quench_audit join rule above caught the readers donor `858-c82b5be2`. We told soft that its 747 failed for that reason, and soft withdrew it. Soft reinstated it after our correction.
- Forensics withdrew its 376 at 08:32Z (public-first held ancestors with prvsiyan shares of 0.755 and 1.0). Our 376 was a kick of that row, so it left our take at 08:38Z.
- The 421 re-open was marked as taken by another lane, because our own `STATE.txt` held its id. Items of our own (claim `backlog`) no longer read our own state.

### Results

| n | Bar | New | Gain on the bar | Gain beyond the next live take | Next live take |
| --- | --- | --- | --- | --- | --- |
| 90 | 0.0540925534369 | 0.0534641842349 | 6.284e-04 | 6.284e-04 | none |
| 420 | 0.0226641170482 | 0.0225617874816 | 1.023e-04 | 1.023e-04 | none |
| 421 | 0.0221719225231 | 0.0221519775053 | 1.995e-05 | 1.995e-05 | none |
| 455 | 0.0228519582791 | 0.0228519545974 | 3.682e-09 | 3.682e-09 | none |
| 551 | 0.0190712845523 | 0.0190694197487 | 1.865e-06 | 1.865e-06 | none |
| 587 | 0.0211899334118 | 0.0211507660880 | 3.917e-05 | 3.917e-05 | none |

Sum: 7.917e-04 on the bar and beyond the other live round 29 takes, on 6 n. The 90 row is a 900 s midm kick of the public malyshevdanil row that harvest holds (Apache 2.0, prvsiyan share 0.000). It gives 79% of the gain.

The final pass moved 504, 689, 752, 916, 988 and 594 to `near/`, because another lane holds a lower row of each. Rebuild passed our 594 at 11:53Z by 5.6e-10.

The results table is `results/backlog-r29-2026-11-15.tsv`.

### Next

1. Follow the certified rows of the other lanes first. This paid 17 of 50 follow runs, the best yield of the round.
2. Kick every fresh row 1e-5 or more below the bar at 900 s at once. The 90 row (6.3e-4) came from one such kick, and quench measured 420 and 587 the same way.
3. Drop the near kicks. They certified 0 of 103 in round 29, and 3 of 70 in round 28.
4. Give the open held seed rows a short kick first, and a long kick only to a row that moves. Only 1 of our 15 seed kicks went below the bar by more than 1e-10, and `--stop6` found 4 of 15 rigid in about 90 s each.
5. Give the ctl a smaller start margin near the deadline. Its 400 s margin refused a 300 s leg at 11:35Z, so the leg ran by hand.

## Round 30 (2026-11-15, 12:01Z to 17:55Z)

The same controller ran as round 30 (`BACKLOG_ROUND=30`), with boxB 2 slots and boxC 1 slot. The agent stopped on a usage limit at 14:04Z and came back at 15:42Z. The controller and its watchdog ran on in that time. They made 41 runs and certified 9 results.

### What ran

The bar was `round30-briefs/bar30.tsv` until 15:45Z. After that it was the gate of the submitted round 29 b file, `gate/cand-round29-1115b/details.csv`. The two differ only at 376, 503 and 582, and we hold no row at those n. Each run ended in one fq quench from the certified file on the box, then floatsafe at 2.2e-11 or finesafe.

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s | each certified row of a live `take-*-r30` dir below the bar |
| follow midm | `midm_scan.py` kick,lkick, 240 s, or 900 s for a row 1e-5 or more below the bar | the same rows |
| fresh | `midm_scan.py` 900 s and lkick 300 s | the round 29 rows that set bar30 and got no 900 s kick in round 29 |
| own | `midm_scan.py` 600 s and `invent_rest.py` lkick 300 s | each row of ours that is the lowest live row of its n |
| leg | the tool of the find, 300 s | a find that moved the score by 1e-6 or more, or ended less than 1e-10 below the bar |
| near | `invent_rest.py` lkick, 180 s | a forensics rectangle file within 3e-5 above the bar |
| seed | `midm_scan.py` kick,lkick, 300 s | the held seed row 815 |

### Changes to the controller

- Near kicks run only on files close to the bar. In round 29, 103 near kicks at or above the bar gave nothing.
- A job starts while 450 s are left. The worker cuts it to the deadline.
- No dispatch walk for follow and near items. In round 29 the dispatch walk refused 20 of 70 follow starts, and the assembler held 6 of them. The certify walk of our result stays the gate.
- After 3 lkick follows of one n, a follow runs only when its start is 1e-6 or more below the lowest start we followed. Quench posted 4 fq steps of 694 by 12:44Z, and our 3 lkicks of them were dry.
- A forensics rectangle file within 3e-5 above the bar gets a 180 s lkick, with legs while a leg moves 1e-6. Twoshort measured this as the best near yield of round 29.
- The share test applies only to a row whose own first source is a public file and that reaches no held row (main ruling 12:40:55Z).
- The taint list takes the withdrawn public-first files of the 13:32:00Z clarification: the harvest r26 files of 695 and 814, and the forensics r22 donor `799-986b3b6d`.
- The bar moved to the round 29 b gate at 15:45Z.
- The final pass knows four walk hits that we traced by hand (594, 687, 791, 972). It accepts each only for its n and writes a walk note into the source cell.

### What was measured

| Kind | Runs | Outcomes |
| --- | --- | --- |
| follow, other lane file | 41 | 10 certified, 28 dry, 3 not below a live take or our own row |
| follow, kick-lane file | 12 | 4 certified, 7 dry, 1 not below a live take |
| follow midm | 12 | 1 certified (972), 9 dry, 1 not below our own row, 1 refused by the walk |
| fresh and late | 10 | 2 certified, 8 dry |
| own | 46 | 12 certified, 27 dry, 7 not below our own row |
| leg | 9 | 4 certified, 5 dry |
| near | 18 | 1 certified, 12 dry, 4 above the bar, 1 not below a live take |
| re-open and seed | 2 | 0 certified |

The controller made 150 runs and certified 34 results. Most certified rows beat the followed row by a small step, and then another lane followed ours. Rebuild, harvest and twoshort passed four of our rows before 17:40Z: 556 (twoshort), 655 (rebuild), 695 (harvest) and 653 for a time (twoshort). We followed 653 again and took it back.

The own chains paid more this round than in round 29 (12 of 46, against 1 of 10). The 687 row went from 7.9e-8 to 2.09e-6 under the bar in 9 certified steps. The 791 row went from 2.9e-6 to 7.9e-6 in 5 steps. The steps shrank to about 1e-9 of score at the end.

Two slots were idle from 17:14Z to 17:24Z, because the queue was empty. We added 840 s midm kicks with new seeds on seven low rows. The two that ran (412 and 378) were dry, and the rebuild claim skipped 593.

### Faults found

- We withdrew our 802 at 13:47Z. Its tree took the forensics r22 donor `799-986b3b6d` as a direct part, and the 13:32:00Z ruling keeps such rows out. Border withdrew its 802 for the same reason.
- `quench_walk.check` flags four of our rows for reasons that do not hold:
  - 594: twoshort moved the start file to its `near/` with the same bytes.
  - 687: harvest withdrew two of its own near files. The walker matched the forensics r22 donor of 685 that their reason names. Our tree reaches that donor only through the held round 28 b row 687.
  - 791: the changed pin is the pin of the held round 28 b row itself.
  - 972: our own round 26 withdrawal misread a forensics retention note. The held row 972 is the quench of those bytes.
- Our own 16:51:56Z handoff note named two paths next to the word withdrawal. `quench_walk.load_withdrawn` read it as a new withdrawal, and the final pass dropped 972. A REINSTATE line at 17:40Z cancelled it, and the row went back into the take.
- The re-open gate refused the modules r29 926 near files, because their start has no record.

### Results

| n | Bar | New | Gain on the bar | First step from |
| --- | --- | --- | --- | --- |
| 339 | 0.0264153848370 | 0.0264147683250 | 6.165e-07 | lkick of the quench fq of 339 |
| 378 | 0.0246963441369 | 0.0246836262059 | 1.272e-05 | lkick of the twoshort 378, then 3 legs |
| 401 | 0.0253700735984 | 0.0253696777559 | 3.958e-07 | lkick of the harvest 401 |
| 546 | 0.0202526416519 | 0.0202512007298 | 1.441e-06 | lkick of the quench fq of 546, then an own lkick |
| 584 | 0.0211282536018 | 0.0211264755786 | 1.778e-06 | lkick of the quench fq of 584 |
| 594 | 0.0192468697624 | 0.0192466639719 | 2.058e-07 | lkick of the twoshort 594 |
| 653 | 0.0167009205649 | 0.0167004475469 | 4.730e-07 | lkick of the border 653 |
| 687 | 0.0193519479805 | 0.0193498627468 | 2.085e-06 | lkick of the midm 687, then own kicks |
| 791 | 0.0177684504146 | 0.0177605400512 | 7.910e-06 | lkick of the border 791, then own kicks and a leg |
| 972 | 0.0154213989981 | 0.0154038179269 | 1.758e-05 | 900 s midm kick of the soft 972 |

Sum: 4.520e-05 on the bar and beyond the other live round 30 takes, on 10 n. The bar is the round 29 b gate.

The results table is `results/backlog-r30-2026-11-15.tsv`.

### Next

1. Follow the certified rows of the other lanes within minutes. Lkick follows certified 14 of 53 runs. The one 900 s midm kick of a row 1e-5 or more below the bar gave 972 (1.76e-5, 39% of the gain).
2. Keep the own chains going while a step gains 1e-9 of score or more. Own runs certified 12 of 46, and 687 and 791 came from such chains.
3. Keep legs on every find. They certified 4 of 9.
4. Never name a take path next to the word withdrawal in a handoff note. The walker reads such a line as a new withdrawal: our 16:51:56Z note made it drop our 972 (1.76e-5) until a REINSTATE line followed.
5. Keep a standing fill of 900 s midm kicks with new seeds on the lowest live rows, so no slot waits. Two slots sat idle for 10 minutes this round.
6. Drop the seed, re-open and far near items. They certified 0 of 2, and near items 1 of 18 (a border LP of our own 687).

## Round 31 (2026-11-15 18:48Z to 2026-11-16 00:30Z)

The same controller ran as round 31 (`BACKLOG_ROUND=31`). It had three slots on boxB and one on boxC. The modules lane stopped, and its boxB slot came to backlog.

### What ran

The bar was `round31-briefs/bar31.tsv`, the gate of the submitted round 30 c file. Each run ended in one fq quench from the certified file on the box, then finesafe at 2.2e-11.

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s | each certified row of a live `take-*-r31` dir below the bar |
| follow midm | `midm_scan.py` kick,lkick, 900 s, probe 120 s | the same rows, 1e-7 or more below the bar (1e-5 for a kick lane's row) |
| mine | `midm_scan.py` 900 s, probe 120 s | our own round 30 rows that set bar31 |
| fresh | `midm_scan.py` 900 s, probe 120 s | the other lanes' round 30 rows that set bar31 (228 left out: a plain public file) |
| held | `midm_scan.py` 900 s, probe 120 s | held rows of the round 30 c file by score gap to the per-puzzle board |
| near | `midm_scan.py` 900 s, probe 120 s | a near file of another lane below the bar and every live take |
| leg | the tool of the find (900 s probe-gated midm, or a 300 s lkick) | a find that moved the side by more than 1e-6 |

### Changes to the tools

- The worker has a probe. A midm job with `probe=120` stops when it has no find after 120 s and at least 3 tries. The control: a fake scan with no find stopped at the probe time, and one that found at try 2 ran on to its limit.
- Every claim line names the start's sha256. The controller skips a start that another lane claimed in the last 60 minutes by its sha256. The lanes pin the same held row as different bytes. So for a held row, the controller also skips the start when a claim line of another lane this round names `n=` and the word held.
- A follow is claimed at queue time, so the other lanes see our claim within a minute (brief: they wait 10 minutes for it).
- A leg runs from every find that moves the side by more than 1e-6, up to six deep. A first scan that gained 1e-5 of score gets two seeds.
- Near files of every other lane count (not k123), but only when they sit below the bar and every live take. The rectangle lkicks above the bar are dropped (1 of 18 in round 30).

### What happened

The controller made 263 runs and certified 50 rows on 22 n. The agent died at about 23:29Z on a usage limit. The controller, its watchdog and the four workers ran on to the 00:15Z search end without it. A revived agent took over at about 00:07Z. It started no new job and stopped the controller after the last run.

Runs by kind (`work/scripts/tally.py`):

| Kind | Runs | Certified |
| --- | --- | --- |
| follow lkick, file of a lane that does not kick | 47 | 18 |
| leg | 45 | 13 |
| own | 65 | 11 |
| follow lkick, file of a kick lane (midm, twoshort, invent) | 21 | 4 |
| follow midm kick, 900 s with probe | 35 | 4 |
| refollow (a second lkick with a new seed after a dry follow) | 10 | 0 |
| fresh | 12 | 0 |
| near | 13 | 0 |
| follow midm2 (bkick, melt) | 7 | 0 |
| mine | 5 | 0 |
| held | 3 | 0 (all above the bar) |

The probe stopped 95 midm jobs at 120 s and let 10 run on.

### The share test

The rule 3 share test ran at certify time on the public-first n in `work/share31-n.txt` (910 743 852 791 588 635). It ran by hand on every take row at 22:32Z (`work/share/all1.json`, file sha256 in `work/share/all1.sha`).

- The public-first rows 741 812 910 911 974 read in. Their bytes at the end are the bytes measured at 22:32Z.
- 911 stays at the earlier b157 row (0.01616364218341526, sha256 bd788481a0ae), which reads 0.238 at 1e-3 and 0.350 at 1e-2. Two later 911 rows read 0.4 or more at 1e-2 (our leg row 0.351/0.429, b166 0.256/0.429). They are in `near/` and the n is in `work/out31.txt`, so no later 911 row could enter the take.
- 11 rows read 0.4 or more against a table that is not our seed: 454 464 548 601 654 686 695 761 818 971 990. Each tree starts from held rows, so rule 2 applies and they stay. The trace of each, with its held root, the files its source cell names and its share, is `work/held-traces/<n>.txt`. The index is `work/held-traces/INDEX.tsv`.

### Faults found

- The ctl walk refused the harvest r31 evidence blocks as ancestry. They are share measurements against the 1105 tables. `deep_check` now strips them. The positive control: our b044 851 row passed. The negative control: a cell that names the 1105 file as a parent still refused.
- The claim test took certified lines with the words "fresh build for kicks" as claims, and skipped the follows of forensics 686. Only a line with the word claim counts now.
- Two followed rows sat 5e-10 apart (border LP of the quench 851). The ctl now runs one follow of each kind per basin of an n, the lowest first.
- A fresh row 3.9e-4 below the bar (soft 686) waited 4 to 7 minutes behind 900 s legs. boxB slot 3 now takes follow items only.

### Results

| n | Bar | New | Gain on the bar | First step from |
| --- | --- | --- | --- | --- |
| 421 | 0.0221519775053 | 0.0221328220922 | 1.916e-05 | lkick of the midm 421, then 8 own and leg steps |
| 464 | 0.0204823325342 | 0.0203886445780 | 9.369e-05 | 900 s midm kick of the forensics 464, then an own kick |
| 548 | 0.0197466184589 | 0.0197376515314 | 8.967e-06 | lkick of the rebuild 548, then 2 legs |
| 646 | 0.0177891411437 | 0.0177882591193 | 8.820e-07 | lkick of the k123 646 |
| 654 | 0.0162975923026 | 0.0162932870396 | 4.305e-06 | lkick of the rebuild 654, then own steps |
| 686 | 0.0196353263370 | 0.0191390008357 | 4.963e-04 | lkick of the midm 686, then an own step |
| 695 | 0.0177777990486 | 0.0177776521138 | 1.469e-07 | lkick of the quench 695 |
| 741 | 0.0186106689466 | 0.0178499889418 | 7.607e-04 | lkick of the quench 741 |
| 761 | 0.0146511624003 | 0.0146492197980 | 1.943e-06 | lkick of the quench 761, then own steps |
| 811 | 0.0150798484863 | 0.0150794247000 | 4.238e-07 | lkick of the twoshort 811 |
| 818 | 0.0138086602371 | 0.0138022214461 | 6.439e-06 | lkick of the classfill 818, then 2 legs |
| 863 | 0.0157676150926 | 0.0157618527955 | 5.762e-06 | lkick of the classfill 863, then an own step |
| 910 | 0.0162625080713 | 0.0162477986714 | 1.471e-05 | lkick of the border 910, then an own step |
| 911 | 0.0165589939347 | 0.0161636421834 | 3.954e-04 | lkick of the quench 911 |
| 971 | 0.0154137137680 | 0.0154106073811 | 3.106e-06 | lkick of the border 971, then 2 legs |
| 974 | 0.0156661245367 | 0.0154737083530 | 1.924e-04 | 900 s midm kick of the quench 974 |
| 990 | 0.0135297114775 | 0.0135297099424 | 1.535e-09 | lkick of the quench 990 |

Sum: 2.004e-03 on the bar and 2.004e-03 beyond the other live round 31 takes, on 17 n. Four more certified rows (454 601 812 864) left the take at the end, because classfill, twoshort, quench and border passed them. Their files are in `near/`.

The results table is `results/backlog-r31-2026-11-16.tsv`.

### Next

1. Follow the fresh certified rows of other lanes with a 180 s lkick within minutes. These certified 18 of 47 runs on files of lanes that do not kick, and they gave the biggest rows: 741, 911 and 686.
2. Keep legs from every find that moves the side by more than 1e-6. They certified 13 of 45.
3. Keep own chains while a step gains 1e-9 of score. They certified 11 of 65. Stop a chain after two dry steps.
4. Keep one 900 s probe-gated midm kick for fresh rows 1e-5 or more below the bar. It certified 4 of 35, among them 974 (1.92e-4) and 464 (9.4e-5).
5. Stop refollow, fresh, near, midm2, mine and held kicks. They certified 0 of 50 runs together.
6. Leave 911 on the b157 row. Every lower 911 we made read 0.4 or more at 1e-2.

## Round 32 (2026-11-16, 11:17Z to 17:30Z)

The same controller ran as round 32 (`BACKLOG_ROUND=32`). It had two slots on boxB and one on boxC. The bar was `round32-briefs/bar32.tsv`, the gate of the submitted round 31 b file. Each run ended in one fq quench from the certified file on the box, then finesafe at 2.2e-11.

### What ran

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s | each certified row of a live `take-*-r32` dir below the bar |
| follow midm | `midm_scan.py` kick,lkick, 900 s, probe 120 s | the same rows, 1e-5 or more below the bar (any lane) |
| leg | the tool of the find | a find that moved the side by more than 1e-6 |
| own | 900 s probe-gated midm kick and a 300 s lkick | each new row of ours that is the lowest live row of its n |
| heldfill | `invent_rest.py` lkick, 150 s | held round 31 b rows that no claim line of rounds 29 to 31 names with the word held, only when no other item waits |

Round 31 measured zero for refollow, fresh, near, midm2, mine and the 900 s held kicks. They did not run (`work/NO_REFOLLOW`, `NO_NEAR`, `NO_M2`, no fill of that kind).

### Changes to the tools

- Slots: boxB 2 and boxC 1. The third boxB slot of round 31 is gone.
- No standing out list. The held rows at 851, 911 and 972 are ours now (rule 2). `work/out.txt` still takes an n out without a restart.
- The share test of rule 3 is `work/scripts/share32.py`. It imports the round 31 assembler's frozen measure (`take-assemble-r31/scripts/share31.py`): bounding-box centring on centres and corners, 8 symmetries, median-offset ICP, 1e-3 and 1e-2, against the 10 harvested 1105 tables. A table whose row equals one of our Samanyu seeds is our own layout. The list of the 10 zips is cached once in `work/share/zips.json`, because the glob takes about 18 s.
- The share test runs at certify time on every row of a public-first tree, and refuses at 0.4 or more at either tolerance. A tree is public-first when its cell names a round 32 harvest file, or the start's first source is a public file (`quench_walk.harvest_type`), or the start is under `take-harvest-r*`. The round 31 harvest roots that the round 31 b file took are held now, so their names in old cells do not count.
- Controls of `share32.py`: our round 31 911 leg read 0.351 and 0.429 (out), the 911 b157 row 0.238 and 0.350 (in), the held 911 0.132 and 0.341 (in). These are the round 31 numbers.
- The WITHDRAW lines of `handoff-r31.log` and `handoff-r32.log` are read every 60 s (24 sha256 prefixes and one path at the start). A start with withdrawn bytes is skipped at dispatch. A row whose cell names withdrawn bytes is refused at certify. Control: quench's withdrawn 911 fq `c171f6d83c60` reads as withdrawn, the held 911 `116f72f56b76` does not.
- The 900 s kick of a fresh row runs only at 1e-5 or more below the bar, for every lane (brief 6a).
- A path claim whose line names other bytes no longer blocks a newer file at that path. At 11:35Z the controller skipped the new forensics 973 file because midm had claimed the older bytes of the same path.
- The provenance check reads names only. A cell note such as "replaces bd788481 ... the withdrawn fq c171f6d83c60" names withdrawn bytes as history, not as a source. A hex token counts only after `sha256`, `-`, `/` or `_`, and not when the 120 characters before it say replaced, dropped, withdrawn, instead or rather than. Two rebuild 911 follows were skipped at 13:38Z before this fix. Controls: the rebuild 911 cell reads clean. A byte copy, a quench-style name, a file name and the start sha still read as withdrawn.
- One n runs on one slot at a time for leg, own and heldfill items. At 12:47Z all three slots ran 864 at once.
- A leg is dropped when its start is more than 1e-6 above the lowest live row of its n. The 866 leg of b066 started 2.3e-5 above the k123 866.
- The superseded test of a 900 s follow kick now strips the `-m` suffix. Before, it kept the sha in the lane name and never matched.
- The heldfill list reads angles as radians. A 45 degree lattice row (every tilted angle at pi/4 mod pi/2) and the 12 lattice n that main named at 12:47Z stay out. The first list read degrees: b120 (678) and b121 (731) ran on lattice rows, both dry.

### Results

10 rows, 3.799e-04 of score below bar32. That is also 3.799e-04 below the other live round 32 takes, because forensics and k123 superseded their 808, 864, 866, 909, 970 and 971 rows to ours. Table: `results/backlog-r32-2026-11-16.tsv`.

| n | bar32 | new | gain on bar |
| --- | --- | --- | --- |
| 442 | 0.0238773800721 | 0.0238620725399 | 1.531e-05 |
| 530 | 0.0218949822055 | 0.0218754182888 | 1.956e-05 |
| 805 | 0.0164294625833 | 0.0164294431504 | 1.943e-08 |
| 808 | 0.0157689228580 | 0.0157484978532 | 2.043e-05 |
| 864 | 0.0155817270553 | 0.0155675300804 | 1.420e-05 |
| 866 | 0.0151477121222 | 0.0150698042472 | 7.791e-05 |
| 909 | 0.0163052003839 | 0.0161650707459 | 1.401e-04 |
| 910 | 0.0162477986714 | 0.0162450751722 | 2.723e-06 |
| 970 | 0.0158664715394 | 0.0158024173743 | 6.405e-05 |
| 971 | 0.0154106073811 | 0.0153850594883 | 2.555e-05 |

The final pass moved 485, 577 and 849 to `near/`. Forensics and classfill hold lower rows of those n.

The finalize walk (`quench_walk.check`) flags 909, 970 and 971 now that the parent forensics rows are out of the forensics take. It names the public jazivxt boxed-in-sub file of `take-harvest-r29` (Apache 2.0) and a changed pin in a stair-c round 31 `held31/548` record. Both are reached through held round records (47 held refs). The certify walk of each row found no public-first source. We read this as held ancestry (rule 2). Each source cell carries the note, and the assembler walk decides.

### What was measured

170 runs, 31 certified steps (later steps replace earlier ones at the same n).

| Kind | Runs | Certified | Dry |
| --- | --- | --- | --- |
| follow lkick of another lane's fresh row | 44 | 17 | 22 |
| follow lkick of a kick lane's fresh row | 12 | 1 | 11 |
| follow midm 900 s kick (probe 120 s) | 18 | 2 | 13 (13 probe-stopped) |
| leg | 20 | 5 | 12 |
| own (900 s midm kick and 300 s lkick) | 39 | 6 | 32 |
| heldfill (150 s lkick of an unclaimed held row) | 36 | 0 | 36 |
| control | 1 | 0 | 1 |

- Follows of other lanes' fresh rows paid best again: 909 (1.40e-04), 866 (7.79e-05) and 970 (6.41e-05) started from forensics and k123 rows.
- The 900 s kick of a fresh row paid twice: 971 and 909.
- Own chains gave small steps (530 7e-07, 970 1.2e-09, 805) and went dry from about 14:10Z.
- Heldfill gave nothing: the first list was claimed by soft, twoshort and rebuild, and the second list gave 0 of 36. Border's 900 s unprobed held kicks gave 1 row (405, 1.9e-09) of 71 claims this round, so no third fill ran. From 15:36Z the slots waited for follows.

### Next

1. Keep the 180 s lkick follow of every fresh certified row of another lane. It gave 17 of 31 certified steps and the three largest rows.
2. Keep legs and the one 900 s probe-gated kick of fresh rows 1e-5 or more below the bar (5 and 2 certified).
3. Keep own chains, but stop after two dry steps (6 of 39).
4. Drop the 150 s held fill (0 of 36) and do not add held kicks of any length (border 1 of 71). Leave idle slots free for follows.
5. Let the finalize walk read the hits of a parent row from its superseded record. A parent that leaves its take late then keeps its own held-ancestry hits.

## Round 33 (2026-11-16 18:22Z to 2026-11-17 00:12Z)

The same controller ran as round 33 (`BACKLOG_ROUND=33`). It had two slots on boxB, one on boxC and one on boxE. The bar was `round33-briefs/bar33.tsv`, the gate of the submitted round 32 a file. Each run ended in the fq loop from the certified file on the box (`midm_fqonce.py`), then finesafe at 2.2e-11.

### What ran

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s | each certified row of a live `take-*-r33` dir that is the lowest live row of its n |
| follow midm | `midm_scan.py` kick,lkick, 900 s, probe 120 s | the same rows, 1e-5 or more below the bar |
| leg | the tool of the find | a find that moved the side by more than 1e-6 |
| own | 900 s probe-gated midm kick and a 300 s lkick | each new row of ours that is the lowest live row of its n |

No held fill, refollow, near or midm2 items ran. Round 32 measured them dry.

### Changes to the tools

- A fourth slot on boxE (`<scratch>/squares-backlog`, the `squares-base` venv and fq). Control: a 60 s midm kick of the held 60 row scaled by 1.0005 wrote a raw file. Finesafe and fq certified it 2.5e-11 under the bar, inside the 1e-10 margin, so certify refuses it.
- No follow of a 45 degree lattice row. These are the 14 known n and any row whose squares all sit at 0 or 45 degrees, with at least one at 45. The test reads radians or degrees. Control on the held round 32 a file: it finds all 14 known n and 66 more such rows. It does not flag 909 or 700.
- Only the lowest live row of an n gets a follow. The test runs at queue time and again at dispatch.
- A fresh row of border, harvest, classfill or soft waits 10 minutes. It runs then only when no lane claimed its bytes.
- A later RELEASE line of another lane ends its claim on the same bytes. Forensics released its 789 at 19:19Z, and the old claim had blocked our follow.
- A line that says it is no withdrawal ("no WITHDRAW or kick claim") withdraws nothing. One such line of round 32 put quench's 292 start on the withdrawn list, and the 789 follow was skipped for it at 19:27Z. The list went from 63 to 61 sha256 prefixes.
- A withdrawn public-first file counts only when the tree takes it directly. A hit whose walk chain passes `take-assemble-r*/held-roots.json`, a `gather/round*` file or a `results/round*-best` table is held ancestry. Our 734 follow was refused at 18:51Z for `799-986b3b6d`, six steps under the round 32 held roots. Controls: the 734 cell now passes. A cell that names the 799 donor directly is still refused.
- The WITHDRAW lines of `handoff-r31.log`, `handoff-r32.log` and `handoff-r33.log` are read. PUBFIRST also marks round 33 harvest files, so `share32.py` runs at certify on every public-first output.

### Results

7 rows, 1.0994e-04 of score below bar33. That is also 1.0994e-04 below the other live round 33 takes, because k123, border and rebuild superseded their rows of these n to ours. Table: `results/backlog-r33-2026-11-17.tsv`.

| n | bar33 | new | gain on bar |
| --- | --- | --- | --- |
| 489 | 0.0222616141033 | 0.0222012338481 | 6.038e-05 |
| 594 | 0.0192466639719 | 0.0192400255409 | 6.638e-06 |
| 701 | 0.0164664984356 | 0.0164660704874 | 4.279e-07 |
| 753 | 0.0162505551868 | 0.0162303201898 | 2.023e-05 |
| 812 | 0.0149648592928 | 0.0149609333882 | 3.926e-06 |
| 911 | 0.0161635606283 | 0.0161635580732 | 2.555e-09 |
| 995 | 0.0127135718226 | 0.0126952376434 | 1.833e-05 |

734 and 907 moved to near/ at the end, because k123 and forensics hold lower rows.

### What was measured

- 68 runs and 11 certified steps. A later step replaces an earlier one at the same n.
- 180 s lkick follow of another lane's fresh row: 28 runs, 9 certified, 16 dry. It gave 5 of the 7 kept rows and the first finds of 489 and 812.
- 900 s probe-gated midm follow: 13 runs, 1 certified (489, 7.4e-07 below the lkick find), 7 stopped by the probe.
- Legs of finds over 1e-6 of side: 12 runs, 1 certified (812, 4.1e-09 more).
- Own chains: 13 runs, 0 certified.
- boxE worker died after its second job at 19:10Z with no stop line. The controller reads a slot as busy while `next.json` waits, so the 900 s kick of border 753 never ran. The slot stood dead for 5 hours.
- Few fresh rows came in. From 20:00Z most slots stood idle for long spells.

### Next

1. Keep the 180 s lkick follow of every fresh row within minutes. It gave 9 of 11 certified steps.
2. Add a worker liveness check to the controller. It should check the worker pid on each box every loop, and restart a dead one. The dead boxE slot cost one 900 s kick and 5 hours of a slot.
3. Stop own chains. They gave 0 of 13 this round and 6 of 39 in round 32.
4. Stop a running kick when another lane posts a lower row of its n. The 734, 259 and 907 kicks of superseded rows ran on to the end.

## Round 34 (2026-11-17 01:25Z to 07:40Z)

The same controller ran as round 34 (`BACKLOG_ROUND=34`). It had two slots on boxB, one on boxC and one on boxE. The bar was `round34-briefs/bar34.tsv`, the gate of the submitted round 33 a file. Each run ended in the fq loop from the certified file on the box (`midm_fqonce.py`: default flags, then the deep flags, up to three rounds), then finesafe at 2.2e-11.

### What ran

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s, seed 11 | each certified row of a live `take-*-r34` dir that is the lowest live row of its n |
| follow kick | `midm_scan.py` kick,lkick, 900 s, no probe, seeds 3100+n and 3300+n | the same rows, 1e-5 or more below the bar |
| refollow | `invent_rest.py` lkick, 300 s, seed 12 | a followed row whose follow was dry |
| leg | `invent_rest.py` lkick, 300 s | a find that moved the side by more than 1e-6 |

No own chains ran. Round 33 measured them at 0 of 13.

### Changes to the tools

- The 900 s kick of a fresh row runs with no probe and with two seeds. In round 33 the 120 s probe stopped 7 of our 13 kicks, and border's 753 and 998 came on the second seed.
- Every leg is a 300 s lkick. Legs rank behind the follows and the kicks, so they fill idle slots only.
- A running job gets `RUN/KILL` when another lane posts a row of its n more than 1e-6 of score below the job's start. The worker polls for that file every 5 s and stops the search. The raw files found so far still go through finesafe and the fq loop. The KILL file never stops that last step.
- Each worker writes its pid to `slotK/pid`. Every loop the controller checks the pid of every slot. A dead worker is restarted with `start_worker.sh`, and its unfinished job goes back to `next.json`. A job that already wrote `done.json` is dropped instead. In round 33 a dead boxE worker held its slot for 5 hours.
- A follow is dispatched no sooner than 5 s after our claim line. The log is then read again, and an earlier claim of another lane on the same bytes or the same take file stops it.
- The WITHDRAW lines of `handoff-r33.log` are read too, and PUBFIRST marks round 34 harvest files.

Controls, run before the controller started:

- KILL: with another lane's row faked 5e-7 below the start of a 600 s boxE kick, `r34_guard` wrote nothing. At 2e-6 below it wrote the KILL file. The worker stopped 4 s later (rc 124), and its find certified at 0.03279555900853692, the same value as the round 33 control.
- Liveness: after `kill -9` of the boxC worker and its search, `r34_guard` found the worker dead. It moved the job back, and the new worker ran it to the end (rc 0). A second pass with the worker alive wrote nothing.

### Results

4 rows, 5.1894e-05 of score below bar34. That is also 5.1894e-05 below the other live round 34 takes, because k123, border and rebuild superseded their rows of these n to ours. Table: `results/backlog-r34-2026-11-17.tsv`.

| n | bar34 | new | gain on bar | source |
| --- | --- | --- | --- | --- |
| 640 | 0.0192860473767 | 0.0192818124561 | 4.235e-06 | follow of border's fresh 640, then one leg |
| 735 | 0.0180709092006 | 0.0180502735458 | 2.064e-05 | second 900 s seed on k123's fresh 735 |
| 808 | 0.0157484978532 | 0.0157222496484 | 2.625e-05 | follow of k123's fresh 808, the second 900 s seed, then one leg |
| 998 | 0.0124929271696 | 0.0124921520553 | 7.751e-07 | follow of rebuild's fresh 998 |

### What was measured

- 39 runs and 7 certified steps (a later step replaces an earlier one at the same n).
- 180 s lkick follow: 17 runs, 5 raw finds, 3 certified (640, 808 and 998). The other 2 finds sat less than 1e-10 under the live row or above a newer row of the owner.
- Unprobed 900 s kick, two seeds: 8 runs on 4 rows (790, 735, 683 and 808). 6 wrote a raw find. 2 certified (735 and 808), and both came on the second seed. On 790 and 735 the first seed found 2e-11 to 3e-11 below the start, inside the margin. 683 was dry on both seeds.
- 300 s lkick leg: 5 runs, 4 raw finds, 2 certified (640 by 3.6e-08, 808 by 9.6e-07).
- 300 s refollow after a dry follow: 8 runs, 0 raw finds.
- KILL and liveness: neither fired in the live run. No lane posted a row 1e-6 below a running start, and no worker died.
- Fresh rows were few. From 01:30Z to 07:20Z the other lanes posted 27 certified lines in the log. Several were claimed first by their owners, because classfill and rebuild follow their own rows. The slots stood idle for long spells, as in round 33.

### Next

1. Keep the 180 s lkick follow of every fresh certified row within minutes. It gave 3 of 7 certified steps and the first find of 640, 808 and 998.
2. Keep two unprobed 900 s seeds for fresh rows 1e-5 or more below the bar. Both certified kicks came on the second seed (735 and 808). The first seeds wrote finds inside the margin only.
3. Keep the 300 s lkick leg on finds over 1e-6 of side. It gave 2 of 7 steps, and the 808 leg added 9.6e-07.
4. Drop the 300 s refollow. It gave 0 raw finds in 8 runs.
5. Give the idle slots a second list. Fresh rows came in slowly, and most slots stood idle for hours. A candidate is unprobed 900 s second seeds of the newest held rows of the owner classes, if the owners hand them over in the log.

## Round 35 (2026-11-17 10:30Z to 16:40Z)

The controller ran as round 35 (`BACKLOG_ROUND=35`). It had two slots on boxB, one on boxC and one on boxE. The bar was `round35-briefs/bar35.tsv`, the gate of the submitted round 34 a file. Each run ended in the fq loop on the box, then finesafe at 2.2e-11.

### What ran

| Kind | Tool | Start |
| --- | --- | --- |
| follow | `invent_rest.py` lkick, 180 s, seed 11 | each certified row of a live `take-*-r35` dir that is the lowest live row of its n |
| follow kick | `midm_scan.py` kick,lkick, 900 s, no probe, seeds 3100+n and 3300+n | the same rows, 1e-5 or more below the bar |
| hand | `midm_scan.py` kick,lkick, 900 s, no probe, seeds 3500+n and 3700+n | a held row that an owner lane hands over in the log |
| join | `midm_scan.py` kick,lkick, 900 s, no probe, seed 3900+n | a quenched k123 join donor less than 1e-4 above the bar that no lane claimed in 20 minutes |
| leg | `invent_rest.py` lkick, 300 s | a find that moved the side by more than 1e-6 |

### Changes to the tools

- The refollow is off. It gave 0 raw finds in 8 runs in round 34.
- No leg starts from a find that sits within 1e-10 of the bar. Such a find is the held basin.
- The WITHDRAW lines of `handoff-r34.log` are read too.
- Hand items: the controller reads `hands deep kick n=N` lines. A later `takes back n=N` line of the same lane cancels the row. The start is the n row of the submitted round 34 a file, checked against the bar. One seed runs when the line says one unprobed kick already ran, and two run otherwise. Before the claim, `quench_walk.check` walks the row through a sidecar that names the held row. The claim names the bytes, and the start waits 5 s and a new read of the log. Only one claimed seed waits at a time. A row handed to another lane by name waits 20 minutes for that lane.
- Join items: the same claim and walk steps, on the k123 file. A job stops when any lane certifies its n.

Controls: the parser gave one seed for "exactly one unprobed kick" and two for "none". It did not read a claim line that quotes a hand line, and it read `takes back`. `quench_walk.check` refused a start whose sidecar names the prvsiyan file. The donor claim check found the claims of invent and classfill on 11 donors and none on the other 7.

### Results

10 rows, 2.986e-04 of score below bar35, and 2.465e-04 below the other live round 35 takes. 808 and 869 sit 3.8e-10 and 1.3e-08 above the k123 808 and the classfill 869. Table: `results/backlog-r35-2026-11-17.tsv`.

| n | gain on bar | source |
| --- | --- | --- |
| 693 | 8.000e-05 | unclaimed k123 join donor, 2e-7 above the bar, one 900 s seed (6.48e-05), two legs, then our own deep seed |
| 812 | 6.627e-05 | follow of quench's fresh 812 |
| 869 | 4.564e-05 | follows and the second 900 s seed of k123's fresh 869 |
| 871 | 4.384e-05 | follow of quench's fresh 871, then its second 900 s seed |
| 806 | 2.448e-05 | follow of k123's fresh 806 |
| 925 | 1.978e-05 | second 900 s seed on twoshort's 925, then one leg |
| 864 | 1.141e-05 | follow of k123's fresh 864 |
| 808 | 6.389e-06 | follow of border's fresh 808, then one leg |
| 865 | 3.997e-07 | join donor, then the follow of k123's 865 |
| 807 | 3.438e-07 | follow of quench's 807 |

### What was measured

- 110 runs and 20 certified steps.
- 180 s follow: 23 runs, 14 raw finds, 9 certified steps on 8 rows.
- 900 s follow seeds: 16 runs, 9 raw finds, 3 certified steps (925 and 871 on the second seed, 869).
- Handed held rows: twoshort handed us 7 rows, which ran as 10 seeds. They gave 3 raw finds and 0 certified. The finds sat 3e-11 to 5e-11 under the bar, inside the margin.
- Join donors: 34 runs, 26 raw finds, 2 certified (693 and 865). Donors 1e-4 or more above the bar gave 0 of 11, so the limit went from 3e-4 to 1e-4 at 14:43Z. Four donors fell into the held basin.
- Legs: 19 runs, 10 raw finds, 5 certified steps.
- Near files above the lowest live row: 5 runs, 0 raw finds. They were switched off at 14:47Z.
- Fault: the new take dir had no `work/share/zips.json`. The first certify of 812 and 871 failed at 16:13Z. Both certified at 16:22Z after we copied the file.
- `finalize.py --walk` took more than 15 minutes on the loaded boxA and did not finish by 16:35Z. Its dry run at 15:27Z walked the first 8 rows clean.

### Next

1. Keep the 180 s follow and the two unprobed 900 s seeds of fresh rows 1e-5 or more below the bar. They gave 12 of 20 steps and 9 of 10 rows.
2. Keep the unclaimed k123 join donors within 1e-5 of the bar on idle slots, and give a find its legs and two deep seeds. 693 gave 8.0e-05, our largest row.
3. Copy `work/share/zips.json` into the take dir at setup.
4. Start the final walk by 15:45Z.
5. Put join donors ahead of handed held rows. The held seeds gave 0 of 10.

## Round 36 (2026-11-17 18:00Z to 23:55Z)

The controller ran as round 36 (`BACKLOG_ROUND=36`). It had one slot on boxB, two on boxC and one on boxE. The bar was `round36-briefs/bar36.tsv`, the gate of the submitted round 35 a file. Each run ended in the fq loop on the box (`midm_fqonce.py`: default flags, then polish, up to three rounds), then finesafe at 2.2e-11. The first agent hit its usage limit at about 22:57Z. A revived agent adopted the controller at 23:00Z and closed the round.

### Changes to the tools

- The donor walk runs in its own process, `backlog_prewalk.py`. A donor walk took 4 to 7 minutes on the loaded boxA. While the old controller walked, quench claimed 9 donors.
- The controller claims a donor first and walks it after. No run starts before the walk is clean.
- A clean walk that stopped at the 3000-file cap is walked again with cap 100000.
- The controller reads k123's new donor line (`certified near donor n=N, ...`). It also reads the round 35 donors that no lane claimed in round 35.
- Join donors are ranked by board room, `(bar - board best) - (donor - bar)`. A donor with no room is skipped. Each donor gets two unprobed 900 s seeds (3900+n and 4100+n).

### Results

4 rows, 1.698e-04 of score below bar36. All 4 are the lowest live round 36 rows of their n. Table: `results/backlog-r36-2026-11-17.tsv`.

| n | gain on bar | source |
| --- | --- | --- |
| 793 | 1.326e-04 | follow and 900 s seed of forensics' fresh 793, then the 180 s follow of k123's lower 793 |
| 698 | 3.704e-05 | two 180 s follows of border's fresh 698 |
| 812 | 1.870e-07 | 180 s follow of k123's fresh 812 |
| 692 | 3.093e-09 | 180 s follow of forensics' fresh 692, at 23:04Z |

Our 972 (3.902e-05 below the bar) left the take at 23:47Z. classfill followed it, and forensics composed a 972 from that follow that sits 1.0e-9 lower. The file stays at the top of the take dir because that row descends from it. It came from an unclaimed k123 join donor (6.2e-8 above the bar), one 900 s seed and a leg, then the follows of k123's fresh 972.

The final walk of all 4 rows used `quench_walk.check` at repo HEAD. It finished at 22:44Z, clean and not capped: 698 7363 files, 793 7549, 812 7355, 972 7538. Each walk took 1149 to 1328 s. The walk of 692 at 23:12Z was clean too: 64 files, not capped, 39 s.

### What was measured

- 76 runs and 12 certified steps.
- 180 s follow: 15 runs, 7 raw finds, 7 certified steps.
- 900 s follow seeds: 19 runs, 9 raw finds, 3 certified steps.
- Join donors: 33 runs, 14 raw finds, 1 certified step (972). Most finds stayed above the bar: 864, 634, 808, 549, 750, 811 and 910 were 3.8e-7 to 1.9e-5 above it. 735 and 549 came back to the held basin, within 5e-10 of the bar.
- Legs: 7 runs, 2 raw finds, 1 certified step.
- Our own deep seeds: 2 runs, 0 finds.
- Inside the margin: a 900 s seed on quench's 597 gave a row 4.5e-11 below quench's live row. That is under 1e-10, so it does not count.
- Skips: 13 follows were not the lowest live row of their n. 3 donors had no board room.
- A donor walk of about 7550 files took 1215 s on boxA at 22:18Z.

### Next

1. Keep the 180 s follow of every fresh row. It gave 7 of 12 steps from 15 runs, the best yield per run.
2. Keep the two 900 s seeds of fresh rows 1e-5 or more below the bar. They gave 3 steps, and 793's first seed carried most of its 8.9e-5.
3. Give join donors one seed, not two. They gave 1 step in 33 runs. Their finds mostly stay above the bar or fall back into the held basin.
4. Start the final walk at least 70 minutes before the take deadline. A walk of a held-tree row takes about 20 minutes on the loaded boxA.

## Round 37 (2026-11-18 01:42Z to 06:55Z)

The controller ran as round 37 (`BACKLOG_ROUND=37`). It had two slots on boxB, two on boxC and one on boxE. The bar was `round37-briefs/bar37.tsv`, the gate of the submitted round 36 b file. Each run ended in the fq loop on the box, then finesafe at 2.2e-11.

### Changes to the tools

- Join donors follow rule 6c. A donor gets a seed only when its held share at 1e-3 is under 0.5. The controller imports invent's `heldshare.py` and fills its held cache from the round 36 b file. A donor gets no seed at an n where a donor already fell back to the bar this round.
- Each donor geometry gets one seed (5300+n). A donor whose centres sit 0.9 or more within 1e-3 of a donor we already queued is the same geometry. Control: the two 910 donors share 0.536, so both got a seed.
- Idle slots take held rows by rule 6d, two slots at most (`fill37.py`). The list is quench's `heldpick37.py`, taken from the far end. Rows with a side fraction shared with another n are out (lesson 6k). Each row is walked before it joins the queue.
- When our record quotes another lane's take row, a path that lane wrote relative to its own take dir is written in full (`parent_src`).
- The names that deep25 could not walk stay out of our records. Only their count stays. quench_walk reads every path in a record as ancestry, and it reads a relative name as gone.

### Results

1 row, 4.221e-05 of score below bar37. Table: `results/backlog-r37-2026-11-18.tsv`.

| n | gain on bar | source |
| --- | --- | --- |
| 683 | 4.221e-05 | three 180 s follows of the fresh 683 tree (quench's public jazivxt/boxed-in-sub row, Apache 2.0), each step after a forensics step |

The 683 tree went 5.9e-6, then 1.0e-5, 2.1e-5 and 4.2e-5 below the bar in 75 minutes. Quench's fq loop of the public row came first. Then our 180 s follows and forensics' compositions and 900 s follows took turns. Each of our three follows went 1.2e-8 to 2.8e-8 below the forensics row it started from.

The walk of the 683 row is not clean at repo HEAD. Its one hit is the relative name `harvest/near/683-public34-502b5af49b6fe836.csv`. Our first 683 record carried it inside a deep25 note, and forensics' follow-root sidecar copied that note. The file exists under `take-quench-r37/work/harvest/near/` with the expected sha256. With quench's `walkalias37.py`, which maps that one name to its full path, the walk is clean: 44 files, not capped. We wrote new records for our own rows and edited no other lane's record. The assembler judges the alias.

### What was measured

- 31 runs and 3 certified steps, all on 683.
- 180 s follow: 5 runs, 4 raw finds, 3 certified steps.
- 900 s follow seeds: 4 runs, 2 raw finds, 0 steps. Two seeds on forensics' 72dbb384 ended above our follow of it. Two on 6153de8e found nothing.
- Held rows by rule 6d: 17 seeds, 10 raw finds, all within 3e-11 of the bar (inside the 1e-10 margin). Quench claimed 19 of the 29 rows we walked first. By 04:15Z every held row with board room was named in a handoff line of rounds 34 to 37, so the list was empty.
- Join donors under rule 6c: 5 seeds, 2 raw finds, 0 steps. 367 and 911 fell back to the bar, within 6e-11. Most donors were skipped for a held share of 0.5 or more (972 0.55, 976 0.69, 965 0.85).
- Claims: forensics claimed each of its own fresh 683 rows within a second of posting them. Our follow of those rows waited until our next certified step gave us a row to follow.
- A setup gap cost 6 minutes: `work/scripts/share32.py` was not copied, so the share gate read -1 and refused the first 683 find. Controls after the copy: that find read 0.123 and 0.283 (in), and the prvsiyan 1105 row of 683 itself read 1.0 and 1.0 (out).

### Next

1. Keep the 180 s follow of every fresh row. It gave all 3 steps of this round from 5 runs, and in round 36 it gave 7 of 12.
2. Copy the whole `work/scripts` folder of the last round at setup, then retarget it. The missing `share32.py` refused a good find.
3. Keep audit notes out of records, and write every path in full. One relative name in a quoted deep25 note made every row of the round's best tree walk unclean.
4. Drop held-row seeds by rule 6d: 17 seeds, 0 steps, and the list was empty by 04:15Z.
5. Keep join donors on rule 6c with one seed each: 5 seeds, 0 steps. Most donors share 0.5 or more of the held row.

## Round 38 (2026-11-18 07:55Z to 13:55Z)

Bar: round38-briefs/bar38.tsv, the gate of the held round 37 a file (Kaggle ref 58500381, public 22.1125387121).
Slots: boxB 2, boxC 3, boxE 1. The lane ran only the 180 s follow of fresh rows, our own follow of each find, and k123 near donors within 1e-7 of the bar.

| n | gain on bar | source |
| --- | --- | --- |
| 210 | 1.236e-04 | our 180 s follow of quench's 210 (the fq loop and own follow of the public jazivxt/boxed-in-sub row, Apache 2.0), 1.45e-9 below quench's row |

Our 937 row (7.9e-6 below the bar, 5.6e-10 below quench's row) left the take at the end. Forensics' 900 s seed of it went 2.1e-7 lower, and our follow of that row was dry. Forensics' composer row of 210 sits 1.3e-13 below ours. Neither row is 1e-10 below the other, so our 210 stays in the take as a fallback and the assembler takes the lower one. Both per-n files stay in place with unchanged bytes, because forensics' records name them.

### Tool changes (backlog_ctl.py, R 38 and later)

- The follow of a fresh row of another lane starts at once. The 10-minute wait for self-chaining lanes is gone, because the producer now follows its own row before its line.
- No 900 s seeds of fresh rows. Forensics owns the composer and the first 900 s seed.
- Our own find goes to take.tsv at once. Its certified line waits until our own 180 s follow of it ends, or 20 minutes, or the search end.
- A claim line of the producer lane on its own fresh row no longer drops our follow. Our follow waits until that claim is 7 minutes old. At 09:10Z the old rule dropped our follow of quench's 937.
- Donors count by geometry and endpoint, not by score. A donor within 1e-11 of score of a donor we queued is the same endpoint. At most two of our donor seeds of one n run at once, and a queued donor is dropped once a donor of its n fell back.
- Donors only within 1e-7 of score above the bar (JOIN_MAX), and none at the spent n 367, 372, 591 and 642.

### What was measured

- 12 runs and 2 certified steps.
- 180 s follows of other lanes' rows: 7 runs, 2 raw finds, 2 certified steps (210 1.45e-9 and 937 5.6e-10 below the row they started from). 272, the first 210 row, the first 937 row and forensics' 937 were dry.
- Own 180 s follows of our finds: 2 runs, 0 finds.
- k123 donors at 973 (the only donor n of the round): 4 seeds. Two from different endpoints (1.0e-10 and 2.8e-9 above the bar) both ended at 0.015882820402733, 4e-11 below the bar, which is the held geometry. Classfill's seed fell back to the same score. The other two seeds were stopped by rule 6d with no find.
- k123 posted 19 donors at 973 with pair share under 0.9 between them. Five of them share one side value, 31.688379939339.
- From 10:15Z to 13:45Z no lane posted a fresh row without a follow, and no donor was eligible, so the slots stood idle.
- Walks: 210 and 937 clean at repo HEAD, 14 and 16 files, not capped. share32 of both public-first trees 0.000 at 1e-3 and at 1e-2.
- Controls: guard38_control.py passed its four cases. held_share reads 1.0 for the held 683 and 793 rows against themselves, and 0.20 to 0.22 for three k123 793 donors. The hold control kept the line while the own follow waited and ran, and posted it after the follow ended.

### Next

1. Keep the 180 s follow of every fresh row at once. It gave both steps of this round from 7 runs, and all 3 steps of round 37.
2. Hold our own line until our own follow ends. The first 210 line went out before its follow because of a bug, fixed at 09:30Z. The 937 line then waited 4 minutes as planned.
3. Stop donor seeds at an n after the first fallback. At 973 two seeds from different endpoints ended at the same held score, and so did classfill's.
4. Give fresh public rows to the follow lane within minutes. Every step of rounds 37 and 38 came from quench's hourly harvest of jazivxt/boxed-in-sub.
