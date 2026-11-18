# Quench lane

Other lanes leave certified results and near files that never got their final fq quench. The quench lane gives each one fq quench, certifies the output, and keeps it when it beats the base bar and every live take of the round. It runs no search of its own.

## Tools

| File | What it does |
| --- | --- |
| `quench_bar.py` | Writes the per-n bar: the gate details of the base, lowered by every take row it is given. |
| `quench_once.py` | `prep` writes a job (the start as fq text). `take` reads the fq output, certifies it with floatsafe at 2.2e-11 and keeps the lower of the certified input and the quench. |
| `quench_box.sh` | Runs on a compute box. fq with default flags, then the deep flags, up to three rounds while a round gains more than 3e-9 of side (the `midm_fqonce.py` loop). |
| `quench_drive.sh` | One driver per box slot. It sends each queued job to the box, waits for it and copies the output back. |
| `quench_near.py` | Lists the near files whose bounding side sits within a window of the bar. |
| `quench_audit.py` | A first ancestry check of a sidecar: Samanyu seeds and the named sources that are out. |
| `quench_walk.py` | The full walk of a start's recorded tree (round 26). |
| `quench_follow.py` | The follow loop (round 26): it reads the live takes every 10 minutes, walks each start and queues it. |
| `quench_publish.py` | Writes the per-n files and `take.tsv` by rename from the finished jobs. It walks each start copy again with the current walk before its row goes out. |
| `quench_collect.sh` | The collect loop (round 26): every 30 s it certifies each finished job against the live bar, republishes and posts one handoff line per new n. |

## Round 25

The agent died on a usage limit at about 23:50 UTC on 2026-11-13. Its drivers ran on to the 02:45 UTC deadline, and its STATE.txt is the record.

- Control: the held 120, inflated by 1e-3, came back from fq at side 11.0000000000023. `take` refused it at margin -1.9e-13. The tools work and the bar rule can say no.
- The lane published 13 counts with a gain of 0.00095 against the round 25 strict bar.
- The skeptic kept 8 of them in the round 25 b file: 228, 365, 534, 542, 548, 750, 802 and 873 (0.00091).
- It dropped 860 and 921, because a deeper walk reached the Samanyu-dev seed 983. It dropped 911 and 975, because their ancestry could not be walked to the end. The 911 start was refused by its own lane and then removed. The 975 start named `take-twoshort-r25/975.csv`, a version that twoshort withheld and replaced.

What made those four rows fail: the audit read the start's sidecar and the files it named by full path. It did not follow bare file names, held rows or ledger lines, and it trusted a start file that its lane could still change or remove.

## Round 26

### What changed

- `quench_walk.py` walks the whole recorded tree before a start is queued. It follows the sidecars and the ledger lines that name a file by its whole name. It follows the `take.tsv` rows of per-n take files and the `ancestry/<sha256>.json` records. It follows bare csv names, and held references through the results tables. It also reads the producing lane's STATE.txt for a refusal of the start, and the WITHDRAW and WITHHOLD lines of the handoff logs.
- It refuses a start for a Samanyu-dev seed signal or a withdrawn tree. It refuses a name from the round 25 skeptic's list (`921-29e12ff3` among them) and the CC BY-SA or penguin069 sources. It refuses a start with no record, and a gone file. A gone file under a held row is the held row's business and does not refuse. Any other gone file does: in round 24 a gone `take-harvest-r23/866.csv` hid the seed 811 behind the 927 tree.
- The follow copies the start, its sidecars and its ledger lines byte for byte to `work/starts/<sha16>/`, and the job names that copy. A lane that replaces its file later cannot break the record.
- The bar is live. Each pass lowers the base details by every other `take-*-r26` row.

### Controls

- Positive: the walk refuses all 12 starts that the round 25 skeptic dropped or that descend from them. These are invent 860, 921, 911 and 985, family 860, modules 975 and 911, and k123 982. They also include readers 860 and 921, stair-c 921 and invent-r24 927.
- Negative: of six starts whose rows the round 25 skeptic kept, the walk reads 228, 750, 365 and 534 as clean. It refuses 873 and 542 for gone files. The walk is stricter than the round 25 skeptic on gone files, and we keep it that way.

### What the quench found

The quench pays only on a start that no lane ran fq on with the default flags. In round 26 three kinds of start had that slack.

| n | Start | What one quench did | What happened next |
| --- | --- | --- | --- |
| 910 | forensics' certified rectangle composition (held 684 and harvest's 972) | side 30.666008793 to 30.663520679 in one default-flag pass, 8.25e-5 below the forensics row | midm and backlog kicked our row and took 910 lower |
| 850 | forensics' composition of the same design | 1.39e-4 below the forensics row, then 3.29e-5 below its next row | classfill and backlog took 850 lower |
| 748 | forensics' near file `748-rect.csv` (held 694 and harvest's 695) | 4.41e-6 below the modules row | forensics quenched its own copy 3.4e-9 lower at 14:38 UTC. The 695 donor is out (see below) |
| 818 | harvest's public row (lucifer19/think-select-reclose) | 8.4e-7 below the harvest row | classfill took 818 lower. The start is out (see below) |
| 646 | harvest's public row (lucifer19/think-select-reclose) | 2.48e-9 below the harvest row | withdrawn at 15:01 UTC. The start is out (see below) |
| 909 | forensics' near file `909-rect.csv` (forensics 909 and harvest's 850), queued 8.4e-4 above the bar | side 30.642444586 to 30.641490576 in two default-flag rounds, 3.83e-6 below the bar | midm kicked the same near file lower at 15:23 UTC |
| 684 | midm's 684 take (a kick of forensics' `684-rect.csv`) | 1.74e-8 below the base | withdrawn at 15:50 UTC. Midm withdrew its start (see below) |

### Rows close to the prvsiyan set

Harvest's copy check (`tools/harvest26/share_ac.py`) records the largest centre distance from each public layout to the prvsiyan best-of-1105 layout of the same n. That source is CC BY-SA 4.0, so rule b keeps it out. Backlog refused the harvest 695 row at 0.238 and named 0.55 to 0.85 as the range of the rows it keeps. Nine more harvest rows sit below 0.55: 654 (0.165), 646 (0.185), 814 (0.231), 416 and 499 (0.279), 453 (0.338), 818 (0.471), 761 (0.499) and 706 (0.542).

The distance alone does not prove descent: harvest's held 375 and 453 equal prvsiyan layouts through older public files. We keep these rows out anyway. `quench_walk.py` refuses any record with a prvsiyan 1105 distance below 0.55. Our 646 row left the take, and the near copies of 748 and 818 carry a withdrawn note in their sidecars.

Forensics quenched its compositions with the polish flags only (`"flags": "p"`). After our handoff line at 13:33 UTC, it runs the default flags itself. Each follow lane kicks a new row within minutes, so a quench row holds only until the next kick.

### Measured dead ends

- Old near files of rounds 10 to 25: 1227 sit within 2e-6 of the live bar. A margin above -1e-8 is the floatsafe dilation of a raw file (about 1.5e-9 of side), not a gain. Every file below -1e-8 is on an out list, or the walk refuses it.
- Near files that a lane already kicked and quenched: 16 probes over 9 lanes. No pass moved one by more than 1.8e-8 of side.
- Frozen forensics files of rounds 23 to 25: about 40 sit at the held side and moved 1e-13 or less.
- Fresh builds of stair-c and modules that had only an `slp` squeeze: the polish moved 5 of them by 7e-12 to 3.8e-7. The default flags made all 5 worse, by 1.8e-6 to 2.2e-3. The squeeze already converges them, so the window stays at 2e-6 for these lanes. The walk refused 4 more for gone files.
- The default flags make a converged layout worse at the 180 s cap: the ALM pass starts from a loosened layout. `take` keeps the lower of the input and the quench, so this costs time, not score.

### Fixes during the round

- The follow died twice. The first time, a walk error stopped it. The second time, a lane removed its per-n file between the listing and the hash. Each start now runs under its own guard, and a vanished file waits for the next pass.
- The walk missed a held reference written as JSON (`"path": ".../gather/round23-2026-11-13a.csv", "n": 694`). That is how the forensics donor records name a held row. The pattern now reads it. Since then, `quench_publish.py` walks each start copy again with the current walk before its row goes out.
- The walk read harvest's geometry note (`max centre distance: ... samanyu_bestfit=0.859`) as a Samanyu signal. That note says the layout is no copy, so the walk now drops it before it matches.
- A start whose file name says refused, withdrawn, withheld or excluded is refused. The follow queued backlog's `695-...-ancestry-refused.csv` once. Its job was withdrawn before it could publish.
- `quench_follow.py --starts FILE` runs a probe list through the same walk, copy and prep.

### Parents that change after a lane traces them

Midm withdrew its 684 at 15:48 UTC. Its record pins the forensics start as `near/684-rect.csv (sha256 52a68b1649543384)`, and forensics rewrote that file afterwards. No record of the old version is left, so nobody can show which donors made it. Our walk had read the rewritten file and passed it. The walk now compares each `path (sha256 hex)` in a record with the file on disk and refuses the start on a mismatch.

The walk still reads the current version of every parent it reaches by path. That can refuse a clean start: the 909 tree names `take-forensics-r26/850.csv`, which is now a later composition built on midm's 684. It can also pass a start whose old parent was refused and replaced. Only a record that pins every parent by sha256 closes this.

### Base rows that reach a Samanyu-dev seed

The walk reads the held reference `the round 19 packing of n = 501 (gather/round19-2026-11-12a.csv ...)` in the round 21 records of 415 and 501. At round 19, n = 501 was harvest's `seed merged0`, and seedsrc gives Samanyu-dev/squares_in_squares as its source. So the base rows 415 and 501, and every layout built on them, reach a Samanyu-dev seed (rule d). We sent this to main and forensics at 15:24 UTC. The base is not ours to change.


### Rows withdrawn after they were published

A row can lose its ancestry after it goes out. Another lane can withdraw a file in its tree an hour later. In round 26 this happened to our 926.

- We published 926 at 16:22 UTC. The start was twoshort's kick of forensics' `near/926-rect.csv`, a composition of the held 865 and invent's 988 near file. One quench took it 8.3e-8 below twoshort's row and 1.83e-6 below the base.
- At 16:36 UTC harvest withdrew `near/988-pubfq-d0fdd626abfb.csv`. Its public start (lucifer19 `v52_anchor`) puts every square within 1e-6 of the prvsiyan 1105 row of 988, so rule b keeps it out. Invent's 988 near file descends from it, and that file is part B of `926-rect.csv`.
- The record of the 988 file gave no prvsiyan distance, so our 0.55 cut could not see it. Our walk found the file gone at 16:39 UTC, and the row left the take then. A handoff line asks every lane to drop the descendants.

`quench_publish.py` cached a clean walk per job and trusted it. Now it walks a cached clean start again at each publish, and only a cached refusal stands. Positive control: a copy of the 926 job, with its cached clean read, now reads not clean. Negative control: a copy of a clean 457 job reads clean on the first walk and on the second.

### The final take

All three rows of the final take are results of other lanes. Two came back to our take when the lower row that beat them was withdrawn. A fourth row, 972, was in the take from 17:06 to 17:20 UTC. Then classfill reinstated its own 972, 1.04e-6 lower.

| n | Start | Gain on the base | Why it is ours |
| --- | --- | --- | --- |
| 501 | twoshort's raw kick `s727-t33` of forensics' `near/501-rect.csv` (forensics' 501 take and harvest's 375, with the held 457 of round 23 as root) | 4.96e-5 | Our quench certified it 4.6e-10 below forensics' 501, which forensics then dropped as superseded. Forensics had kept its 501 through its final purge at 16:48 UTC. |
| 748 | invent's `748.csv`, a kick of the modules design `g8b1f3b4` (invent's 805 near file, the modules 805 take and a zone of `zone_search.py`) | 4.23e-5 | Forensics withdrew its lower 748 at 16:11 UTC. Invent held its own 748 from 16:34 UTC for an audit. Our walk reads 47 files with no forensics file in them. |
| 850 | twoshort's raw kick `s725-t12` of harvest's 850 (lucifer19/think-select-reclose, Apache 2.0). Our quench certified it 1.1e-9 below backlog's kick `b078` of the same harvest row | 4.90e-4 | Forensics withdrew its lower 850 at 16:40 UTC. Harvest measured a share of 0.000 to 0.003 of the squares within 1e-3 of the prvsiyan 1105 row. |
| 972 | forensics' `near/972-rect.csv` as it stood at 13:35 UTC (our copy, sha256 `d48e4e901bfaee0d`). Its parts are pinned snapshots: forensics' 850 of that time (the held 684 of round 23 and harvest's 972) and harvest's 972 (alexchilton fault-line, Apache 2.0) | 4.18e-4 | Backlog withdrew its 972 at 17:06 UTC. Its row sat on a later version of `972-rect.csv`, which forensics withdrew at 16:39 UTC for invent's withdrawn 972 part. No withdrawal list names our snapshots. |

Our quench did not move invent's 748. It certified twoshort's raw kicks of 850 and 501, 1.1e-9 and 4.6e-10 below the best certified copies. On 972 it moved the side by 5e-14, because forensics had already run fq with the default flags on that composition. Nearly all of the gain belongs to the lanes that built the layouts. What the quench lane added is a finished job that was ready when the lower row left.

We measured each row's share with the layouts of rules a to d with harvest's `tools/nearpub_excl.py`. 972 and 850 share 0.000. 501 shares 0.020 within 1e-3 with a Samanyu seed. 748 shares 0.471 within 1e-3 with the prvsiyan 1105 row of 748. The held 748 shares 1.000 with that row, and modules' own 748 shares 0.469. Our 748 tree reaches neither the held 748 nor a prvsiyan best-of-1105 file. So we read the 0.47 as the region that every layout of this design shares with the held 748, and we keep the row.

### What the next round should run

1. Read harvest's share tables in the walk (`work/origin/nearest-old*.tsv` and `work/near-pub/excl-share.tsv`) in place of the 0.55 distance cut. The cut refused 453, 706, 761 and 818, which harvest kept at a share of 0.001 to 0.016. It also passed the 988 file at a share of 1.000, because that record gave no distance.
2. On every WITHDRAW line, take the best clean finished result of that n again at once. All three final rows came from finished jobs that were ready when a lower row left.
3. Ask every lane to pin each parent by sha256 in its records. The walk can then check a parent that a lane rewrote or replaced after the trace.
4. Keep the follow on raw kicks (twoshort) and on polish-only builds. A default-flag pass on a converged layout is wasted time. Old near files and kicked near files stay dry.

## Round 27

### What changed

The main session lifted the Samanyu-dev rule on 2026-11-14: the layouts that match that GitHub seed came from our own code. The walk no longer refuses on that seed, and the inputs it kept out became the first work of the round.

- `quench_walk.py` drops the Samanyu-dev signals and the seed classifier of `forensics_policy`. It also drops the names that stood for that seed: `921-29e12ff3`, the 747r joins, the 735, 790, 968 and 489 trees, seeds 811, 983 and 504, `931h` and `deferred-995`. A refusal or withdrawal line whose only reason is that seed is not read. `quench_audit.py` drops its seed classifier too.
- Rule b is now the share test. A start is out when 0.4 or more of its squares lie within 1e-3 of the prvsiyan best-of-1105 row of its n. It is also out when its record names that file. The row comes from `submission.csv` in the harvest data zip. The 0.55 distance cut is gone.
- penguin069 refuses only its joegun boxed certified union. Its boxed public certified union is a distinct source, as the round 26 assembler read it.
- A gone file is still walked in three cases. Its lane moved it to another folder of the same take dir (invent r25 `work/near-held-v6`). Its lane ledger still records it (family r22 `near.tsv`). Or the record that names it is its own ancestry node tree (invent `strict25v4`). A gone per-n take file of rounds 22 to 27 counts as superseded, unless a withdrawal line names it or its lane refused it for another reason.
- Withdrawal lines are read in any case, and a withdrawn file name refuses wherever its copy sits. Harvest wrote "withdrawn near file 988-pubfq" in lower case and moved the file to `work/near-out`. The first version of the moved-copy step passed it, and the positive control caught that.
- The certification runs on the box. boxA ran at load 100 and paged: one `take` took 4 minutes 22 seconds there for 4.6 seconds of CPU, and 3 seconds on boxB. `quench_drive.sh` now certifies each boxB job on the box in the same slot. boxD has no numpy, so its jobs are still certified on boxA.
- `quench_publish.py` keeps a clean walk for 60 minutes while no new withdrawal line appears. Any new withdrawal line walks every row again.
- A REINSTATE line cancels the earlier withdrawal of the paths it names, or of the same lane and n. Classfill reinstated 982 at 20:06Z, and our walk read it as withdrawn until this change.
- A withdrawal line that lists counts and no paths withdraws `take-<lane>-<round>/<n>.csv`. Harvest withdrew 416 499 646 654 695 814 this way in round 26, and midm withdrew 546 642 694 684. Before this change our follow queued twoshort kicks of the withdrawn harvest 499.
- A text that compares a layout with the prvsiyan row is a measure, not ancestry. "prvsiyan 1105 (CC BY-SA) share 0.002" no longer refuses modules 597. A share of 0.4 or more in such a text still refuses, and so does a record that names the file as a source.
- A row can come back from pinned byte snapshots. `work/resolved/<sha256>.json` lists every parent with its sha256 and the walk hits it answers. The publish passes the row only while every pin keeps its sha256 and the walk finds no other hit.

### Controls

- Pipeline: the held 120, inflated by 1e-3, came back from fq at side 11.0000000000023. `take` refused it at margin -1.9e-13 against the round 27 bar.
- Positive: the held 748 of round 25 b (share 1.000) and `take-harvest-r22/639.csv` are refused for rule b. The round 26 926 start, which descends from the withdrawn harvest 988 file, is refused. `take-classfill-r22/981.csv` (the held 801) is refused.
- Negative: 599, 812, 648, 871, 866, 990, 927, 935 and 860, dropped in round 25 only for the seed, read clean. Their shares are 0.000 to 0.102.
- Positive, added later: our byte copy of the twoshort r26 kick of the withdrawn harvest 499 is refused. Its start share is 0.174, and the count list withdraws `take-harvest-r26/499.csv`. Negative, added later: classfill r27 982 (share 0.000) and invent r23 866 read clean.

### 972 came back from pinned snapshots

The backlog r26 row of 972 (0.015421398998118452, 1.84e-4 below the round 27 bar) is the largest gain of the round. Backlog withdrew it at 17:06Z of round 26 because its tree reaches `take-forensics-r26/near/972-rect.csv`, which forensics withdrew at 16:40Z.

- The row is a backlog kick of midm's 972 (sha256 c126db9a). Midm's 972 is a kick of the 13:44Z build of `near/972-rect.csv` (sha256 db36d277).
- Two byte copies of that build are on disk: `take-forensics-r26/work/received/raw-be6286af2249de2cd3599bc5.csv` and `take-border-r26/work/wq/in/db36d2772385847c-972.csv`. Its raw record names two parts, both pinned feed snapshots. Part A is harvest r26 972 (1cc8b04d, the alexchilton fault-line notebook, Apache 2.0). Part B is midm r26 910 (978b80db, built on the held 684 of round 23 and harvest r26 972).
- Forensics withdrew the path when it held a later build, made at 15:06Z on invent's 972 (355de762). `withdrawal-purge-1639.json` lists that invent 972 as the withdrawn packing identity. The 13:44Z build does not use it or any other identity the purge lists.
- The round 26 assembler read the 13:35Z build (d48e4e90) the same way for classfill 972, which is the round 27 bar row.
- The share with the prvsiyan row of 972 is 0.000. One fq quench left the row unchanged: it had converged.

`work/bin/reopen972.py` pins the eight files of the chain, and `work/resolved/00921ac0....json` answers the four walk hits: the gone path and the backlog withdrawal line, each seen twice. The same record format reopened 501 and 818. Backlog refused those two rows by file name only. It refused 501 at 0.453 from a Samanyu-dev seed layout, and 818 at 0.473 from the prvsiyan row under the old 0.5 cut. Their shares are 0.000 and 0.0012.

632 came back the same way (2.5e-6 below the bar). Its tree reaches the forensics 684-rect build 52a68b16, whose part A is the forensics 850 snapshot 71776b19. Forensics withdrew its 850 row at 16:40Z, but that row was a later build on midm's withdrawn 684 (`quarantine-withdrawals-1639/withdrawn-850.json`). Classfill showed the same for its 684 at 16:48Z, and the round 26 assembler kept classfill 684. `work/bin/reopen632.py` pins 16 files and answers 12 hits.

### Traps

- A long-running helper that imports the walk keeps the old code. `prewalk.py` walked with the old `quench_publish.py` after the 21:30Z edits, labelled the result with the new walk sha and wrote a refusal for 972. Restart every importer after a change to the walk or the publish, and drop the caches it wrote since the change.
- A handoff line that cites another lane's withdrawal as evidence is read as a withdrawal of every path in it. Our 972 line named the byte copies and our own `972.csv`. A REINSTATE note with the same paths cancels that reading.

## Round 28

The agent died at about 02:25 UTC on 2026-11-15, and its drivers ran on to the 05:45 UTC deadline. Its STATE.txt is the record. The take held 4 rows at the end (499, 551, 814 and 978), 4.36e-6 against the round 28 bar.

- Plain fq quenches: 289 jobs. 27 moved the side by more than 1e-8, and 26 counted when they finished. Most of those rows then lost to a lower row of another lane.
- Kicks: 64 jobs. 6 moved the side by more than 1e-8, and all six were the 180 s invent lkick (752 by 5.7e-6 of side, 978 by 1.0e-6). The 300 s midm kicks moved it by less than the certify slack.
- fq kicks on boxD (`quench_fqkick.sh`): 22 jobs, and none moved the side.

## Round 29

The take holds 2 rows at the end: 556 and 907. Together they are 9.452e-5 below the round 29 bar, and below every other round 29 take by the same amount. Five of our seed-row kicks moved the side past the rule: 420, 587, 593, 594 and 556, 1.545e-4 of score in all. Backlog then took 420, 587 and 594 a little lower. Rebuild kicked our 593 from 1.9481e-2 to 1.9439e-2 at 11:47 UTC, 5.08e-5 below the bar. 907 is soft's island find. Soft's walk stopped at a parent it had refused, so it handed the find to us. Our walk passed it, and we certified it. We withdrew our 503 (1.2e-10) when the walk learned to read public files by the start's own n.

- Plain fq quenches: 337 jobs. 4 counted when they finished: 907 and three versions of 916, which backlog took within minutes.
- Kicks: 61 jobs. 40 were on parked seed rows and 5 of those moved the side past the rule. None of the other 21 did.

### What changed

- `quench_once.py` certifies with the border lane's bisected dilation (`tools/border/r28/finesafe.py`, imported unchanged). On three round 28 outputs it certified 2.8e-11 of score lower than the ladder, about 28% of the 1e-10 rule.
- `quench_box.sh` keeps the lowest raw side of every fq try in `best.txt`, and `take` certifies it as well as the loop output. The loop keeps a try only when it gains more than 3e-9 of side. The polish of a certified file ends about 1e-9 lower, which is the dilation it removes, so the loop dropped it every time. Our round 28 503 sat 9.686e-11 below the round 29 bar, short of the rule. The same input, with the lowest try certified by finesafe, came out 1.228e-10 below it.
- `bin/refinish.py` (in the take dir) queues that refinish for every job of rounds 28 and 29 that ended short of the rule by less than 7e-11.
- boxD has a venv now (a copy of the corners lane venv: pandas 2.2.3, numpy 2.5.4, scipy 1.18.1). Its jobs certify on the box, and it can run kicks.
- The follow reads the live round every 60 s (was 5 minutes). Its window for forensics files is 2e-6 of side, like the others (was 2e-4). Its first pass queued 103 forensics round 28 near files, and round 27 measured that none of 68 forensics starts above 2e-6 crossed.
- The kick feeder runs the 900 s `midm_scan.py --modes lkick,kick` first, the kick that gave rebuild its round 28 rows, then the 180 s invent lkick. It reads rebuild's queue log and backlog's claim lines. A count that rebuild kicks gets only our lkick, and a count that both lanes cover gets no kick from us. Each kick posts one claim line in the handoff log.
- The fq kicks on boxD are off (0 of 22 in round 28).
- `q-boxA.txt` is the kick slot. The follow queues plain jobs to the other two slots only, because a full plain queue kept every kick waiting.
- `quench_walk.py`, three fixes:
  - The rule for the round 22 745/858 join matches the join files only (`745r-858r`, `858r-745r`, `858-ec97a452`, `745-64c4b4f8`). The directory pattern also caught three reader donors that are not the join.
  - A lane line that hands a find over ("near-only find", "walk it and publish it yourselves") is not a refusal. Soft handed its 907 to midm, quench and backlog this way, and our walk refused it.
  - A start can have a public file in its tree (a harvest `public`, `collector` or `data` folder). The start is out when that file's row of the same n has a prvsiyan 1105 share of 0.4 or more. The test reads the rows of the start's own n, because a `submission.csv` holds every n.
- `quench_kickfeed.py` walks a target only when a slot is free, in queue order. It used to walk all targets first. A walk change voids every cached walk, so after the 08:46 UTC change it walked 248 targets for about 45 minutes while the three slots sat idle.
- `quench_kickfeed.py` reads `QUENCH_KICK_FIRST`, a list of n whose first kick goes before every other target.

### New starts for idle slots

From about 08:45 UTC every queue was empty: the follow had run every near file in its window. Two new kinds of start filled the slots.

- Held rows that no lane touched this round. `bin/heldstarts.py` (in the take dir) lists the bar rows whose source is the held round 27 b file. It keeps the n that are in no lane's queue, claim or take of round 29 (290 n were covered). It ranks them by score above the median of their 20 neighbours. 28 rows have a take file in the round tables, and the walk refused 10 of them (public-first ancestors and the prvsiyan share). 18 got one fq each and then a kick.
- Held rows from the Samanyu-dev seed. 681 held rows have no round table entry, so no lane improved them in any round. 596 are Couzo seeds, which lanes could kick in every round. 85 are Samanyu-dev seeds, and the seed rule kept every lane off them through round 28. The start files `work/held27/<n>.csv` are the rows of `gather/round27-2026-11-15b.csv` (the held round 27 b packing) with a sidecar that names `held n = X of round 27`, and the walk passes them. 30 of them got one fq each, and their first kick goes before every other target.

What the seed-row kicks found (40 kicks by the end):

- 587: the 900 s midm lkick,kick improved on 38 of its first 50 lkick tries and gave 3.915e-5 of score. We published it at 10:09 UTC. Backlog kicked our row 9.2e-9 lower at 10:13 UTC and holds it.
- 593: the 300 s kick found one move in 10 tries and gave 9.153e-6 of score (published 10:47 UTC). Rebuild's 900 s kick of our row went 4.2e-5 lower at 11:47 UTC.
- 594 (3.383e-6) and 556 (6.187e-7) came from 300 s kicks too. The other 35 seed kicks found nothing past the rule.
- Seed rows whose side has a closed form (a + b*sqrt(2): 150, 203, 406 and 536) found nothing, in 400 to 3862 tries. The feeder skips them now.
- A loose row shows on its first tries. That is why the seed kicks run 300 s from 10:19 UTC: more rows get one kick before the deadline.
- Backlog and invent took the open seed rows from our 10:19 UTC list.

### Controls

- finesafe: 916, 743 and 499 of round 28 certified at 0.016016601458744617, 0.018189197417287195 and 0.021877612562809512, against the ladder's 0.016016601486470883, 0.01818919744496572 and 0.02187761259036569. finesafe returns the ladder's refusal when the ladder refuses, so it cannot pass an overlap.
- Lowest try: fr-503 ran with the old box script and came back at 9.686e-11 below the bar. fr2-503 ran on the same input with the new script and came back at 1.228e-10, past the rule.

### Measured dead ends

- Shrink: scaling the centres by 1-e gives back the clearance above 2.2e-11, and the score gain is about e. The held round 27 b rows have a minimum pair clearance of 9.0e-11 at most (756), and all but two are at 5.2e-11 or less. No held row has the 1.2e-10 of extra clearance that the rule needs.

### Rows that other lanes took over

Backlog follows our take rows. It kicked our 916 (08:07 UTC), 587 (10:13 UTC), 420 and 594 lower within minutes, each time by a small step on top of our find. Rebuild kicked our 593 lower at 11:47 UTC. Those rows still count in the round, from backlog's take. Our feeder never kicks our own rows, so a second kick on a fresh find of ours is the step that we leave open.

### What the next round should run

1. Kick every parked Samanyu-seed held row that no lane has kicked yet: one 300 s `midm_scan.py --modes lkick,kick` each. Skip sides with a closed form (a + b*sqrt(2)) and n under 300. Measured this round: 5 of 40 seed kicks gave rows (420 1.023e-4, 587 3.915e-5, 593 9.153e-6, 594 3.383e-6, 556 6.187e-7 of score). Backlog took the bottom of the open list and we took the top. The rows between them, and the ones whose kick was cut by the deadline, are open.
2. Kick our own fresh kick rows again within minutes, before another lane does. A loose row improved on most of its early tries (587 on 38 of 50, 420 on 13 of 22). Backlog kicked our 587, 420 and 594 a little lower within minutes and took them.
3. Kick the Couzo-seed held rows that no round improved, the same way, n 400 and up first: 596 rows. This is not measured. They were open to every lane in every round, so expect a lower yield than the parked seed rows.
4. Keep the plain fq follow of near files, with finesafe and the lowest-try certify. It made 337 jobs this round, and 4 counted when they finished (907 from soft's hand-over, and 916 three times, lost within minutes).
5. Never let a walk change stall the feeder: walk at pick time only (done this round).

## Round 30

The take holds 4 rows at the end: 462, 510, 694 and 991. Together they are 9.016e-6 below the round 30 bar, and below every other round 30 take by the same amount. Eight more rows counted during the round. Other lanes took six of them lower (968, 655, 584, 546, 376 and 339), round 29 b already held one (503), and we withdrew 814.

Our agent hit a usage limit at about 16:05 UTC. A new agent took over the same lane, and the background drivers ran on through the change.

- Plain fq quenches: 285 jobs. All 13 rows that counted before 14:50 UTC started at or below the bar. The 68 jobs that started above it gave no row.
- Kicks: 94 jobs. 10 of them improved on at least one try, and 6 gave a row that counted (339, 462, 510, 584, 968 and 991). After 16:00 UTC, 16 kicks of tight rows found nothing (995, 906, 874, 752, 705, 702, 655, 587, 546, 502, 498, 454, 420, 327, 295 and 90).

### What changed

- `quench_walk.py` reads the round 30 rules. It walks the r3x take dirs and handoff logs. A gone per-n take file of rounds 22 to 39 counts as superseded, because the r29 files moved to `near/` at the end of round 29. "keeps X" is a retention note, not a withdrawal. A `CERT` line is a certify note, not a refusal. "out at 0.4" is a share-only reason.
- The share tests changed four times, each time after a main ruling:
  - 12:14 UTC: the share and ancestor-share tests ran only on a public-first start (harvest-type, or no held root).
  - 12:31 UTC: the r28 skeptic had dropped our r28 814 and rebuild's 694, 695 and 546. They descend from public-first rows at a share of 0.4 or more. We ran the ancestor test on every start again, and withdrew our r30 814.
  - 12:40 UTC: main ruled that a row built on a held row is built on our own layout. We went back to the 12:14 scope and reinstated 814.
  - 13:32 UTC: main clarified that a tree that takes a withdrawn public-first file directly stays out, even when it also reaches held rows. The walk now tests every start whose n is not one of our own layouts. It skips a public ancestor only when its first-found path from the start passes through a held reference. A withdrawal line skips a file reached through a held row too. We withdrew 814 again: its start takes the harvest r26 814 collector file `5a4c0cdb` (share 0.536) directly.
- `OWN_N` in `quench_walk.py` lists our own layouts' counts: 801, 503, 983, the Samanyu-dev seed counts, and the held rows that resolve to that seed. The ancestor test never runs on them.
- `quench_kickfeed.py`:
  - A kick of ours that counts gets the next kick first, while the kick moved its start by more than 1e-8 of side. The first version chained 694 six times on certify-level byte changes.
  - A plain fq job that counts by 1e-7 or more is a chain target too.
  - No chain kick runs on an n that another lane claimed. Backlog follows every take row of ours within 5 minutes.
  - `QUENCH_CLAIM_TTL_MIN` (60): a claim covers its n for one hour only. A claim line has no end time. So stair-c's fresh 995 row of 16:08 UTC had no kick: border had claimed an older 995 row at 12:14 UTC. Control: with no limit the claims covered 187 n, 995 among them. With 60 minutes they covered 52, and 968 and 791 (claimed after 15:50 UTC) stayed covered.
- `quench_follow.py`:
  - `QUENCH_WINDOW` (1e-9 of side) replaces the 2e-6 windows. A start that cannot go 1e-9 below our own take row of n is not queued.
  - `QUENCH_NEAR_WINDOW` (-2e-9): a near file must start 2e-9 of side below the bar. Per-n take files keep the 1e-9 window. After a restart at 14:52 UTC, the first pass spent 70 minutes on near files at the bar side (copies of bar rows, about -7e-10). Fresh files below the bar waited.
- `work/base30.csv` is the lower of `bar30.tsv` and the round 29 b details. Round 29 b added 376 and our r29 503 below bar30, so our r30 503 row (the same score) left the take at 13:34 UTC.

### Measured

- 694: one fq of a twoshort raw near file (a forensics rectangle that twoshort kicked) gave 8.685e-6 of score. Six chained 300 s kicks of it moved the side by 0 to 5e-10.
- 968: one fq of a backlog near file, then one 900 s `midm_scan.py --modes lkick,kick`. It improved on 11 of 75 tries and moved the side by 2.08e-5 (6.70e-7 of score). Rebuild kicked our row another 2.65e-7 lower within 30 minutes and holds 968.
- 991: k123's round 29 take row (at the bar), one fq, then one 900 s kick at 17:21 UTC. It moved the side by 6.78e-6 (2.155e-7 of score).
- 510: the first 300 s kick of a held row that no lane had kicked: 1.159e-7.
- 462: the 180 s invent lkick of a backlog near file: 1.686e-10.
- 339 (3.9e-7) and 584 (1.76e-6) came from first kicks of held rows too. Backlog kicked both of our rows lower within minutes.
- 655, 546 and 376 counted from plain fq jobs and then lost to lower rows of rebuild, backlog and harvest.
- 814 (4.353e-6) is withdrawn, as above.

### Dead ends

- A kick of a tight row finds nothing. The 900 s kick of stair-c's 995 row ran 44 tries and none came within 2e-4 of side of the bar. Fifteen more kicks of rows at the bar after 16:00 UTC found nothing either. A loose start shows on its first tries (968: 11 of 75).
- Plain fq of a start above the bar gave no row in 68 jobs. The follow now queues only starts at or below the bar.
- `quench_walk.py` refuses 9 to 25 take rows of other lanes in each follow pass. Most of them fail on a gone file: a per-n file that its lane moved to `near/` under another name. Others fail on a withdrawal line whose reason names a donor that the tree reaches only through a held row. Backlog traced four of these by hand (594, 687, 791 and 972) and keeps them.

### What the next round should run

1. Fix the false refusals of `quench_walk.py` before the round starts, each with a control. Accept a gone per-n file when a file with the same sha256 sits in that lane's `near/`. Accept "changed since pinned" when a byte copy with the pinned sha256 exists. Skip a withdrawal line whose reason names a donor that the tree reaches only through a held row. Measured: the walk refused 9 to 25 take rows of other lanes in each follow pass. Among them were rebuild's 968 (built on our 968) and backlog's 594, 687, 791 and 972, which backlog traced by hand and keeps. Our follow cannot quench or kick a refused row. The control that must stay red: our 814 start, which takes the harvest r26 814 collector file `5a4c0cdb` directly.
2. Gate each 900 s kick on a short probe. Run the first lkick tries for about 120 s, and go on only when a try improves. Measured: 10 of 89 kicks improved on any try, and every row that paid improved early (968 on 11 of 75 tries, r29 587 on 38 of 50). The 995 kick ran all 44 tries with no find. A probe would give about five times more rows one kick in the same slot time.
3. Kick fresh layouts within minutes, before other lanes polish them tight. These are other lanes' fresh take rows and near files of compositions (forensics rectangles, backlog near files, twoshort kicks of rectangles). Measured: 694 (8.7e-6), 968 (6.7e-7) and 991 (2.2e-7) all came from such starts. The first kicks of held rows gave 3 counted rows in 51.
4. Keep the claim limit of one hour (`QUENCH_CLAIM_TTL_MIN`) and the near-file window of -2e-9. Keep the plain fq follow at or below the bar only: 68 jobs above the bar gave no row.

## Round 31

Seven n are in the final take, 8.881e-04 below bar31 in sum and 8.517e-04 below the other live r31 takes. They are 791 (5.518e-04), 852 (1.714e-04), 635, 743, 588 (3.1e-05 to 4.9e-05 each), 812 (3.6e-05 below bar31, 6.0e-10 below the backlog 812) and 991 (4.2e-10). The biggest row of the round, 741 (7.607e-04 below bar31), is in the backlog take. It is backlog's 180 s lkick of our 741 kick find, and it is 5e-09 below the best leg of our own chain. Our fq quench of public-first harvest files gave 741, 743, 791 and 852.

- Plain fq quenches: 197 jobs. 19 counted when they finished (17 n) of them counted, and every one started below the bar.
- Kicks of held rows: 115 jobs with the 120 s probe. 5 of them improved on a try.
- Cross-n jobs (drop1, drop2 and grow1 from a fresh row): 10 jobs, no row.

### What changed

- `quench_walk.py` reads the round 31 rules:
  - The share test is the harvest31 `policy.audit`. It compares the file with every harvested 1105 version by bounding box and ICP, at 1e-3 and 1e-2, and fails at 0.4. It skips a 1105 version that equals our own Samanyu seed. A single-version share of 0.2 or more sends a file to this test. Only a public-first start, and the public-first ancestors of a start, get the test.
  - A held reference is followed only through the held chain. Our held-row sidecars name the held row, not its tree.
  - A withdrawal that names exact bytes applies only to those bytes.
  - A pin passes when a byte copy with the pinned sha256 exists.
  - A withdrawal line does not withdraw a path that it names as a parent ("a lkick of X", "built on X", "from X").
  - A line that withdraws X and retains n in the same text does not withdraw a tree of n.
  - The `checked_paths` list of another lane's audit record is not a source claim. An elided name such as `554a2d38....json` is not a gone file.
- `quench_kick.sh` probes each 900 s midm kick. After 120 s and at least two tries with no find, it stops the scan and runs the fq loop on the best try.
- `quench_kickfeed.py`:
  - It chains a kick only on a find that moved the side by more than 1e-6.
  - A find that gained 1e-5 of score gets two more seeds, with no probe.
  - It allows up to 10 kicks per n, and it feeds every slot queue.
  - It waits 10 minutes before it kicks a fresh take row of another lane, so backlog can claim it first.
  - Its claim lines name the full sha256 of the start.
- `quench_publish.py` walks a row again when an older walk version refused it. It keeps a cross-n job (`fx-`) only after the policy audit of its rows passes.
- `quench_audit.py` drops harvest's share-evidence lists before its rule match.

### Controls

The red controls stayed refused after every walk change:

- the r30 814 start, which takes the harvest r26 814 collector file `5a4c0cdb` (share 0.570 at 1e-3, 0.860 at 1e-2).
- harvest r28 416 (0.748 at 1e-3).
- our soft-r30 972, which reaches the harvest r26 972 collector file `0e563140` (0.402 at 1e-2).

The green controls walked clean. They are backlog r30 594, 687 and 791, midm r30 412 and 854, and rebuild r30 968. They also include our held31 995, the harvest cert31 588 start, harvest 972-public31 and backlog r31 910. The outputs are in `take-quench-r31/work/ctl/`.

### Measured

- The fq quench of fresh public-first harvest files paid most. 791 went 5.5e-04 below the bar, 852 went 1.7e-04 below, and 741 went 7.6e-04 below after one kick find and the backlog lkick.
- The 120 s probe stopped 108 of 115 kicks with no find. The five finds were 741, 761 (1.9e-06, which went to the backlog lkick), 812 (6.0e-10), 991 (4.2e-10) and 990 (4.0e-10, which went to backlog).
- The share test now runs on the rows we publish. Five fq outputs failed it (851 twice, 911, 972 twice) at 0.453 to 0.490 at 1e-2. Some of their starts read under 0.4, so fq can move a public-first row toward the 1105 layout.
- The 741 share test: all 10 harvested versions of the 1105 row at 741 equal our own Samanyu seed. So the gate leaves no 1105 target at 741. Controls: at 972 only the oldest version is ours (1 of 10), and at 228 all 10 are ours.
- Eleven rows that we published were lost or withdrawn. Other lanes went lower at 204, 405, 601, 654, 695, 741, 761, 818, 974 and 990. The share test withdrew 851, 911 and 972.
- The agent died at about 23:14Z on a usage limit. Its drivers ran on to the 00:15Z deadline. A revived agent took over at about 00:07Z.

### Dead ends

- Cross-n moves with fq alone. Our fresh rows are denser than the bars of the next counts. For example, the new 741 is only 1.9e-3 of side above the 740 bar side with one square to spare, and an ideal squeeze would give 1.9e-2. One fq try after drop1 or drop2 squeezed the donor side by only 5e-4 to 1.1e-3. We tried 970 from 971 (19 tries, 1.7e-3 short), 587 from 588 and 998 from 999. We also tried 789 and 739 from 791 and 741. One fq try after grow1 grew the side by 3 to 5 times an ideal insert. 636 from 635 grew 6.6e-2 against 2.2e-2 of room. 687 from 686 grew 9.8e-2.
- Kicks of polished held rows. 108 of 115 probes found nothing in 120 s, and no find on a held row moved the score by 1e-09.

### What the next round should run

1. Run the fq quench on each fresh public-first harvest file within minutes of its line. Then run the policy audit of the output and one kick with the 120 s probe. This gave every large row of round 31 (741, 791, 852, 743).
2. Hand a fresh kick find to backlog for its 180 s lkick before a second 900 s leg. Backlog's lkick beat our 741 chain by 5e-09 and our 761 by 1.1e-07.
3. Keep the policy audit on every published row that descends from a harvest file. Five fq outputs failed it when some of their starts passed.
4. Stop 900 s kicks of polished held rows (108 of 115 probes dry, finds under 1e-09) and the cross-n fq moves (10 jobs, no row).

## Round 32

Seven n are in the final take, 3.252e-04 below bar32 in sum. No other live r32 take holds any of the seven, so the gain beyond the other takes is the same. Two rows carry 99.7% of it. 585 (2.485e-04) is one fq quench of harvest's public 585 file, `585-cert31-3f2b1f52e8387c87.csv` (jazivxt/boxed-in-sub, Apache 2.0). 292 (7.455e-05) is one fq quench of harvest's public 292 file (kenaznia-doga/s292-upper-bound, CC BY 4.0), then one 900 s kick that found nothing more. The other five are 992 (1.9e-06), 378 (2.1e-07), 934, 854 and 800 (7e-09 to 2e-08 each). The drivers stopped at the 17:14Z deadline. The take was last written at 16:55Z. The results table is `results/quench-r32-2026-11-16.tsv`.

### What changed

- `xaudit32.py` (in the take dir, `work/bin/`) is the output share gate. It uses the assembler's frozen `share31.share`, read only from `take-assemble-r31/scripts/`. It reads the 11 distinct 1105 tables of the 10 harvested zips once. It skips a table that equals our own Samanyu seed. A public-first row fails at a share of 0.4 or more at 1e-3 or at 1e-2. A row whose walk reached a held row gets `audit-ok` with no share test (rule 2).
- `quench_publish.py` with `QUENCH_AUDIT_ALL=1` waits for that mark on every job. It prunes a lost row by copy and never by move.
- `quench_walk.py` reports `pubfirst` and `own_n` in its result.
- `quench_kickfeed.py` with `QUENCH_KICK_SCOPE=public` kicks only our fq outputs of public-first starts, after `audit-ok`, one kick per n. Our kick finds get no chained legs, because backlog follows them.
- The harvest test of the gate and the kick feeder reads only the job's own start text. A recorded source can quote an older quench record "that the harvest lane wrote". Forensics r32 973 does that for its held 974 window, and the first version gated our fq of that held-ancestry row.

### Controls

- Walk, red (still out): the r30 814 start, harvest r28 416 and our soft-r30 972.
- Walk, green (clean): backlog r31 910, the harvest r31 791 cert31 file and backlog r31 741.
- Share gate, synthetic: a mirrored and shifted 1105 row reads 1.0. A moved copy reads 0.114 at 1e-3 and 1.0 at 1e-2. Rows jittered by 5e-2 read under 0.4.
- Share gate on round 31 outputs: our fq rows of 911 (0.490 at 1e-2) and 972 (0.453) fail. Our fq rows of 791 (0.348) and 852 (0.362) pass. These are the round 31 verdicts.

### Measured

- Plain fq quenches: 71 jobs on 30 n. 24 of them counted when they finished, on 15 n.
- Fresh public-first harvest files: 13 files on 7 n (442, 485, 530, 577, 585 and 911 at 11:31Z to 11:33Z, 292 at 16:37Z). All seven n counted after fq. Only 585 and 292 stayed ours. Follow lanes went lower on the other five.
- The output share gate ran on 30 public-first outputs. All 30 passed. The highest share was 0.227 at 1e-3 and 0.385 at 1e-2, both on 585. One more FAIL (973, 0.511 at 1e-2) was a held-ancestry row that the first gate version read as public-first. The fix is in "What changed".
- Kicks of our public fq outputs: 6 jobs (900 s, 120 s probe). One find, on 442 (3.3e-07 below our fq row). Backlog then went 2.9e-09 lower.
- Held deep kicks (900 s, no probe, seeds 3300 and 3301, from rank 56 of border's deep order): 35 jobs on 19 n gave 1 row. 707 went 2.7e-07 below bar32. Classfill then went 2.5e-09 lower. 451, 460, 461 and 547 ended 2.75e-11 below the held row on both seeds. That is under the 1e-10 rule.
- 180 s lkicks of held rows certified late in round 31, which no lkick had touched: 10 jobs, 1 row (800, 6.9e-09).
- Ten rows that we published left the take. Backlog went lower at 442, 530, 864, 866 and 910. Forensics went lower at 485 and 577. k123 went lower at 911, and classfill at 707. Four of these margins were 2.9e-09 or less (442, 707, 864, 866).
- Withdrawals: our fo-812-f481913fc0 left the take at 12:12Z and was withdrawn at 12:43Z, because stair-c withdrew its start by exact bytes at 12:42Z. Our fo-812-76738079d6 was never published. We marked it withdrawn at 12:48Z because its start reaches stair-c's withdrawn r31 997 near file.
- Every box job file was copied back and checked by sha256 (1712 from boxB, 840 from boxD) before the box scratch was removed.

### What the next round should run

1. Run the fq quench on each fresh licensed public-first harvest file within minutes of its line, then the output share gate. This gave 585 and 292, 99.7% of our round 32 gain. In round 31 it gave every large row.
2. Hand every counted fq output to the follow lanes at once, and do not kick it again ourselves. Backlog, forensics, k123 and classfill went lower on 9 of our rows, four of them by 2.9e-09 or less. Our one public kick find (442) was passed within minutes.
3. Stop the unprobed 900 s held deep kicks (35 jobs on 19 n, 1 row, which classfill then passed). Also stop the 180 s lkicks of late-certified held rows (10 jobs, 1 row of 6.9e-09).
4. Keep the output share gate on every public-first output. It costs about 60 s to load the 1105 tables, and it caught the share rise on fq outputs in round 31.

## Round 33

At 00:17Z one n is in our final take: 805, 1.8e-10 below bar33. It is one fq quench of another lane's near-bar 805 file. We published six versions of three other n (812, 701 and 907) during the round, and a follow lane went lower on each of them. Harvest posted two fresh public files, 812 and 907, at 21:42Z, after five dry hours of screens. Our fq quench certified both within two minutes, and both passed the share gate. Our fq of a later 812 file reached 3.92e-6 below bar33, and backlog went 3.8e-9 lower. Forensics went to 1.1e-4 below bar33 on 907. One idle-slot held kick paid: 701 went 4.0e-7 below bar33, and backlog then went 2.6e-8 lower.

### What changed

- `quench_walk.py` (fix of a report by the main session at 20:55Z). A gone file below an ancestor path that a round table holds is now a held-chain file. Before, only a held reference counted. Forensics r33 911-rect reached gone files below the held round 32 a rows 551 and 811 of rebuild, and the walk refused it.
- `quench_walk.py`: a claim, priority or retention line is not a withdrawal, even when it says "withdrawn" about something else. An upper-case WITHDRAW or WITHHOLD in the line still withdraws. Five lines left the withdrawal list: four claims and the harvest r31 PRIORITY line for 911.
- `quench_walk.py`: the pinned bytes of a held row are never withdrawn.
- `quench_walk_regress.py` is new. It checks that 911-rect comes back clean. Two red controls must still refuse: a synthetic gone file outside a held chain, and the stair-c r32 812 file withdrawn by exact bytes. All three cases passed.
- `quench_follow.py` knows round 33 and fills a fourth queue, `q-boxDb`, when it exists (the second boxD slot of this round).
- `heldtail33.py` (in the take dir, `work/bin/`) runs one unprobed 900 s held kick per row, only on idle slots. It takes rows from the tail of the border deep order. A row is taken only when border's two workers can no longer reach it before 00:05Z.

### Controls

- Walk, red (still out): the r30 814 start, harvest r28 416, our soft-r30 972 and harvest r26 695.
- Walk, green (clean): backlog r31 910, the harvest r31 791 cert31 file, backlog r31 741 and our r32 585. These are the verdicts of round 32.
- Share gate, synthetic: a mirrored and shifted 1105 row reads 1.0, and a moved copy reads under 0.4 at 1e-3 and 1.0 at 1e-2.

### Measured

- Plain fq quenches: 35 jobs. Box job files copied back and checked by sha256: 582 from boxB and 131 from boxD. The follow queued each start within a minute of its file.
- Fresh public-first harvest files: 2 files on 2 n (812 and 907, both Apache 2.0). Both counted after fq. The share gate read 0.000 on 812 (every 1105 version is our own seed) and 0.316 at 1e-2 on 907.
- Kicks of our two public fq outputs (900 s, 120 s probe): both stopped at the probe with nothing found.
- Idle-slot held kicks: 13 jobs on 13 n gave 1 row (701, 4.0e-7). 594, 463, 407, 501, 589, 504, 339, 985, 543, 983, 869 and 414 were dry.
- Harvest's hourly status lines from 19:16Z to 21:18Z said every packing screen was refused (more than 1,900 decisions). Our four slots were idle for most of the round.

### What the next round should run

1. Keep the fq quench of each fresh licensed public-first harvest file within minutes of its line, then the share gate. It gave our only rows above 1e-7 again (812 and 907), though the follow lanes passed both.
2. Keep the idle-slot held kicks on the tail of the border deep order, one seed per row. They gave 1 row in 13 (701), against 1 in 19 n in round 32.
3. Do not chain our own finds. Backlog and forensics went lower on every row we published above 1e-8, within minutes.
4. Run `quench_walk_regress.py` after every walk change. A walk bug refused held descendants for part of this round.

## Round 34

At 07:20Z two n are in our take: 811, 1.80e-7 below bar34, and 687, 1.3e-10 below. Both came from our own deep-kick class. Round 34 gave every held row one owner by n mod 4, and quench owns n mod 4 = 3 on idle slots. Border handed us 811 from its list of rows that changed in round 32 a. Seed 4400 of the unprobed 900 s midm lkick,kick was dry, and seed 4401 paid. This is the second-seed pattern of rounds 31 to 33 again. Backlog took the follow within a minute. Harvest posted no fresh public file all round, so the slot we keep for public files ran only plain fq quenches of other lanes' files.

### What changed

- `quench_follow.py` knows round 34.
- The kick feeder of round 33 (one seed per row, from the tail of the border deep order) is replaced by `heldmod34.py` in the take dir (`work/bin/`). It reads its rows from `screen34.py`. That file is the screen of border's `tools/border/r34/build_held34.py`, set to class n mod 4 = 3, and it also counts the claim lines of this round. List 1 holds the held rows with a board gap of 1e-5 of score or more, largest gap first. Each has fewer than two unprobed 900 s kicks since its current geometry. A row gets seeds until it has two. Each claim waits 5 s and reads the log again, and it is released when another lane claimed the n first.
- The feeder stops a running kick when a live r34 take goes more than 1e-6 of score below the held row. No kick needed this.
- Legs: a kick output that moves below its start but does not count gets a 900 s leg from that output. Since 03:31Z a leg needs a move of more than 2e-10 of score. The fq polish alone moves a held row by 3e-11 to 6e-11 of score, the same on every seed (367, 923, 987). The legs of 367 and 987 from such moves did not move.
- The kick feeder of round 33 queued a public-first fq output for a 120 s probed kick. We do not run that now: we hand the output to backlog.
- Classfill offered its idle slots at 01:38Z. We handed it 14 rows from the tail of our list 1 (583 983 339 995 407 463 503 755, then 991 655 743 815 699 555). A handed row stays classfill's once it claims it. A row it had not claimed went back to the end of our list 1 at 03:12Z.

### Controls

- `quench_walk_regress.py` with live round 34: PASS 3 of 3. The green 911-rect is clean, and both red controls still refuse.
- The share gate controls of round 33 were not run again. No public-first file reached us, so the gate had nothing to judge.

### Measured

- Deep kicks of our class: 56 unprobed 900 s seeds on 35 n gave 2 rows: 811 (1.80e-7) and 687 (1.3e-10). 687 already had two kicks, and its four list 2 seeds ran after list 1 was spent. Every other row was dry, among them the five largest board gaps of the class (367, 747, 299, 303 and 911).
- Legs: 4 legs from outputs that moved 3e-11 to 6e-11 of score. None moved.
- Handed rows: classfill ran six of our handed rows with two seeds each and certified 995 (2.29e-7, seed 3693). 583, 983, 339, 407 and 463 were dry. We ran 991 655 743 815 699 555 503 755 ourselves when classfill had not claimed them, and all of them were dry. Classfill then claimed 991 and 655 at 06:29Z and 06:39Z, after our seeds of 05:11Z to 05:21Z. So a row we take back needs its own handoff line as well as our claim line.
- Plain fq quenches of other lanes' take and near files: 24 jobs, none counted. The largest move was 5.9e-10 of side on twoshort's 753, which is 2.1e-11 of score.
- Fresh public-first harvest files: none this round.

### What the next round should run

1. Keep two unprobed 900 s seeds per held row of the class, largest board gap first. 811 paid on the second seed after a dry first, and so did border's 753 and 998 in round 33.
2. Hand the tail of the list to a lane with idle slots on the first day. Classfill's 995 came from one of our handed rows.
3. Do not leg a move of the fq polish alone (under 2e-10 of score). Four legs moved nothing.
4. Keep the fq quench of fresh licensed public-first files within minutes of their line, and hand the outputs to backlog. No such file came this round.

## Round 35

At the end of the round our take is empty, and backlog's rows hold all our gains. At 16:12Z our take held 812 and 871, 1.035e-4 of score below bar35 together. Both came from one fresh public file. Backlog's follows went 4.6e-6 lower at 812 and 2.0e-6 lower at 871. Deep kicks gave one more row: twoshort's 807 kicked on the second seed (4601), 1.226e-7 of score below twoshort's live row and 3.43e-7 below bar35. Backlog took the follow 2.1e-10 lower within minutes, so the gain is in backlog's row. Our class n mod 4 = 3 was dry on every held row. The hourly harvest pass found its first real public candidates at 15:13Z. Rosswade's `engine_improvements.csv` (Apache 2.0) holds 812 and 871, 4.0e-5 and 1.1e-5 below the live bar. The full fq loop on boxD took 2 to 4 minutes per file and lowered them further, to 6.17e-5 and 4.18e-5 below bar35. Both pass the share31 gate with a share of 0.000 at 1e-3 and at 1e-2. Backlog claimed the follows at 16:01Z.

### What changed

- `quench_walk.py` treats a start whose rows equal the n rows of a submitted gather as a held root. A submitted gather is a `gather/roundK` file that a `bar*.tsv` names as its `held roundK-…` source. Before this, a held row copied to a new file had no root, and the walk refused it.
- `harvest35` in `tools/harvest35/` is the harvest34 pass for round 35: one fetch an hour, end at 16:25Z, live round 35, held34a pinned. Its controls pass.
- `harvest35/transports.py` creates `near/` before it writes the first public candidate.
- `xaudit35.py` and `results35.py` in the take dir also read the plain fq jobs (`pq-*`).
- The take dir holds the round's feeders in `work/bin/`. `heldmod35.py` gives two unprobed 900 s seeds to each held row of the class. `takekick35.py` kicks the class-3 rows that other lanes certified this round. `nearkick35.py` kicks k123 near donors of any class within 2e-5 of side of bar35, closest first, two seeds each.
- The stop rule (rule 6e) compares a live take against the kick's own start score, not against the held row. Border's live 803 is far below the held row, so the old rule stopped our kick of border's own 803 row.
- A claim of another lane closes our kick only when it names our start's sha. A claim by n alone released our 687 seed by mistake.
- No third seeds on held rows: the main session vetoed them at 12:54Z.

### Controls

- `quench_walk_regress.py`: PASS 5 of 5. The green new case is a classfill r35 925 start equal to the submitted round 34 a row. The red new case is a 925 start of jazivxt's public rows with one x moved by 1e-12.
- The share31 gate controls hold at the gate's start. The positive reads 0.4 or more at both tolerances. The moved copy reads under 0.4 at 1e-3 and 0.4 or more at 1e-2. The negative reads under 0.4.
- `nearkick35.py` measures the side from the bounding box of the rows. On held 735, 995 and 687 it gives bar35 within 1e-14.

### Measured

- 58 unprobed 900 s kicks on 28 n. One counted: 807, seed 4601, on twoshort's row. Four stopped early. Two freed boxD for the public candidates. The old stop rule stopped one (803). We stopped one on our own 807 row after backlog's follow went lower.
- Public candidates: 812 and 871 from rosswade's `engine_improvements.csv`. The certified inputs were 4.0e-5 and 1.1e-5 of score below the live bar. After the fq loop they are 6.17e-5 and 4.18e-5 below bar35.
- Held rows of the class (583, 735, 995, 811, 635, 791, 687, and the extra rows 423, 647, 507, 855, 127): all dry.
- Closed-form rows (635, 791, 937, 485, 605): 0 of 10 seeds. These rows have integer or shared-fraction sides, and a kick does not move them.
- k123 near donors (365, 583, 372, 492, 965, 870, 993, 330, 966, 640): 0 of 19 seeds.
- Take rows of other lanes: 865 (k123) and 803 (border) were dry. 807 (twoshort) paid on the second seed. Seed 4603 on backlog's follow 807 moved it by 2e-16, which does not count.
- Harvest passes: 10:41Z, 11:55Z, 13:02Z and 14:07Z found nothing eligible. At 15:13Z the quick screen counted 4 eligible rows, and the queue step kept 2 (812 and 871). The dispatch refused 812 and 871 for 36 minutes because the pass had no `near/` dir. With the dir in place, both certified at once.

### What the next round should run

1. Kick the rows other lanes certify this round, two seeds each. The only row that counted came from such a row, on its second seed.
2. Drop the closed-form rows and the k123 near donors from the kick list. Together they gave 0 of 29 seeds.
3. Add a dispatch control to the harvest pass that writes one public candidate into an empty take dir. A missing `near/` dir cost the public candidates 36 minutes, and no control caught it.
4. Give a public candidate a slot at once, and stop a kick for it if needed. The public file gave 99.7% of the round's gain.
5. Write the source of a plain fq job in the form `of take-…/work/starts/<sha16>/<n>.csv `. `quench_publish.py` walks the start again only through that path, and without it the rows stay out of take.tsv.

## Round 36

Our take holds two rows, both certified against bar36. Row 597 is 4.079e-5 below the bar. Row 976 is 5.98e-8 below the bar. The 597 row came from the first unprobed 900 s seed on k123's fresh 597 row (seed 4700), which went 2.50e-5 below k123's row. A second kick, from our own row, moved it only 4.5e-11 more. The 976 row came from one seed on a held round 35 a row. Five hourly harvest passes found no eligible public row.

### What changed

- `quench_walk.py` reads a `held roundK-….csv` name in a bar file with its `.csv` ending. Before this, round 35 a was not a submitted gather for the walk.
- `quench_publish.py` walks to 100000 files and refuses a walk that still stops at its cap (rule 6g).
- `tools/harvest36` is the harvest35 pass for round 36: one fetch an hour, end at 23:45Z, the round 35 a file pinned.
- The take dir feeder (`work/bin/feed36.py`) gives two unprobed 900 s seeds to each fresh row of another lane, then to k123 near donors by board room. It runs one walk for each start sha, and a second process walks the next candidates ahead.
- From 21:15Z the feeder counts the seeds on a fresh row differently. It counts our seeds on that row. It also counts the claims of other lanes that name the row's sha, or that name its n after the row was written. Before, it counted every claim on the n in the whole round. Older geometries filled the count, the scan came back empty, and two slots sat idle for 10 minutes. A row 1e-5 or more below the bar now takes our two seeds while all its seeds stay under 4. The claim re-check uses the same cap.
- From 22:47Z the feeder also takes our own fresh rows under the same caps. Held rows went to the boxB slots through `work/bin/heldpick36.py`. It picks one seed per row, by board room, and skips any n that a round 33 to 36 handoff line names. It also skips any n with a live take. It skips closed-form sides too: a rational with q up to 40, or a side with a sqrt(2) or sqrt(3) term.

### Controls

- `quench_walk_regress.py` with `QUENCH_LIVE_ROUND=36`: PASS 5 of 5.
- `feed36.py control`: PASS 6 of 6 after each change. Case 1 is a donor with the live row at the bar (no stop). Case 2 is a donor with a live row 2e-6 below (stop). Case 3 is a held start with a live row 2e-6 below (stop). Case 4 is a held start alone (no stop). Two more cases test a fresh take.
- The share31 gate controls held at the start: the positive read 1.0 at both tolerances. The moved copy read under 0.4 at 1e-3 and 1.0 at 1e-2. The negative read under 0.06.
- Both rows certified again with border's finesafe and kept the same score. The walks at cap 100000 read 7361 files for 597 and 2 files for 976 (held root 976@27), neither capped.

### Measured

- About 64 unprobed 900 s kicks ran. The queue lines give 39 on k123 near donors, on 12 n (367 448 491 634 698 746 794 865 904 910 911 965). They give 19 on fresh rows (539 597 692 698 793 812 972 976) and 4 on held rows (460 461 816 976). The near donors gave 0. The fresh rows gave 597. The held rows gave 976.
- The feeder stopped three kicks when another lane's row at that n went more than 1e-6 below the kick's start (698 once, 972 twice).
- The finds that stayed above the bar did not move enough for a leg. On 910 the donor moved 5e-5 of side and stayed 2.1e-5 above the bar.
- Harvest passes at 18:02Z, 19:10Z, 20:17Z, 21:24Z and 22:31Z found 0 eligible rows in 80 files.
- The closed-form filter dropped the top 12 held rows by board room (963 902 962 901 842 843 785 853 786 964 731 796). Their sides are k plus a multiple of sqrt(2) over 2, or a fraction over 17.

### What the next round should run

1. Kick each fresh row of another lane with our own first seed within minutes of its certified line. In round 36 the first seed on k123's 597 paid 2.5e-5, the only fresh-row find in 19 seeds.
2. Count seeds per geometry, not per n. The per-n count left two slots idle for 10 minutes and nearly missed the 597 window.
3. Give idle slots to held rows that are not closed form and have no claim in four rounds, one seed each. 1 of 4 paid (976, small).
4. Drop k123 near donors below the top room ranks: 0 of 39 this round and 0 of 19 in round 35.
5. Keep the hourly harvest pass. It costs little, and in round 35 it gave 99.7% of the gain.

## Round 37

Our take is empty at the end of round 37. One row certified: 683, from the hourly harvest pass, 5.85e-6 below bar37. It came from the public notebook jazivxt/boxed-in-sub (Apache 2.0). Its share31 read was 0.117 at 1e-3 and 0.384 at 1e-2. Backlog's 180 s follow went 1.25e-8 lower within 11 minutes, so our row left the take. The 683 tree then grew to 4.22e-5 below the bar through the follows of backlog and forensics. Our own 900 s seeds on that tree gave nothing.

### What changed

- `tools/harvest37` is the harvest36 pass for round 37, on the round 36 b held file, with one fetch an hour until 06:45Z.
- The feeder (`work/bin/feed37.py`) gives each fresh row of another lane our first 900 s seed, one seed for each geometry. A geometry is the start sha, or one of our jobs whose start score is within 1e-6 of the row. Then it gives one seed to the top three k123 near donors under rule 6c. Then it gives one seed to each held row that no round 34 to 37 handoff line names.
- `quench_publish.py` accepts a start copy in `work/starts/<sha16>-rK/`. That folder holds a new start record for the same bytes (rule 6n).
- `work/bin/walkalias37.py` walks a 683 start again with one alias. Our first 683 record named the harvest candidate by a path relative to our take dir: `harvest/near/683-public34-502b5af49b6fe836.csv`. That path sat inside a quoted deep25 walk note. The forensics 683 records copied that note, and our start sidecars copied it from them. The walker reads a relative name from the scratch top, so it finds nothing there and calls the file gone. The file exists at `take-quench-r37/work/harvest/near/`. Its bytes (sha256 5a1aa967) are the clean public start. The alias maps that one name to the full path, and only while the bytes keep that sha. `work/bin/rec683.py` writes a new start record, without audit text, for the lowest live 683 row. Then it walks the record with the alias and writes a `work/resolved/<sha>.json` for the publisher. We edited no published sidecar.

### Controls

- `quench_walk_regress.py` with `QUENCH_LIVE_ROUND=37`: all PASS. The walker did not change this round.
- `feed37.py control`: PASS 6 of 6. That covers the four cases of rule 6o and two fresh-take cases.
- The alias walk of the new 683 record (backlog 99670d22): clean, 34 files, not capped. Without the alias: not clean. The one hit is that relative name, reached through the forensics 683 record.
- `quench_publish.walk_ok` on copies of the 683 job: False without the resolved record, True with it.

### Measured

- 30 held rows got one unprobed 900 s seed each: 308 409 450 456 534 631 638 651 680 695 700 737 739 749 757 759 801 813 817 848 867 872 873 912 931 933 981 994 996 997. The kicks of 737, 757 and 931 were stopped to give their slot to the 683 work. All 27 completed seeds returned to the held bar within 6.1e-11 (0 of 27).
- k123 near donors: seven seeds (793 twice, 910, 367, 491, 904, 965). Both 793 donors moved from 2.78e-5 to 1.65e-5 above the bar, less than the 1e-3 of side a leg needs. 910 stayed 1.5e-8 above, and 367 fell back to the bar. 491 and 904 did not move. 965 moved 1.30e-3 of side to 1.85e-4 above the bar. Its leg (rule 6q) ended exactly on the bar, in the held geometry (0 of 7, and 0 for the leg).
- Fresh rows of other lanes: 793 twice (classfill rows 216121e8 and 28126480), 683 twice (backlog 99670d22, forensics df9ca86c). On 216121e8 the kick moved 1.25e-6 of score but stayed above the lower live row. The feeder stopped that kick, and the 683 kick on 99670d22, when another lane's row went more than 1e-6 below their starts. The other two returned to their starts (0 of 4).
- Harvest passes ran every hour. The 03:04Z pass gave the 683 row. The other passes admitted 0 rows.
- From 04:33Z to 05:02Z, all five slots were idle by rule 8. After that, at most two ran, on new k123 near donors. heldpick37 found no unnamed held row that is not closed form. The near donors left failed rule 6c: they sat within 2e-6 of the held side, or had held share above 0.5, or their n had fallen back.

### What the next round should run

1. Keep the hourly harvest pass and give a fresh public row its fq and first seed at once. It gave our only row this round, as it gave 99.7% of our gain in round 35.
2. Write every record with full paths and leave all audit output out of it. One relative path inside a quoted walk note blocked the 683 tree for every walker for about an hour. It kept our seed off the hottest n of the round until 04:08Z.
3. Drop held-row seeds and near donors as slot fillers: 0 of 27 held seeds and 0 of 7 donors this round. Lend the idle slots to a lane with fresh rows, or stop them.
4. On a hot fresh tree, 900 s midm seeds on another lane's lowest row added nothing (0 of 4). The 180 s follows and the composer made all the 683 steps. Leave such a tree to those lanes, and give our slot to the next fresh n.

## Round 38

Our take holds one row at the end of round 38: 272, 5.17e-6 below bar38. All three of our rows came from one harvest pass. At 09:03Z the pass read a new version of the public notebook jazivxt/boxed-in-sub (Apache 2.0). It gave 210 (1.233e-4 below the bar), 272 (5.17e-6) and 937 (6.75e-6). All three are our own Samanyu-seed geometry, so no share gate applied (rule 2). Each one got its fq loop, our own 180 s follow and one 900 s seed before its certified line (rule 6b). Then backlog and forensics took 210 and 937 lower. Across the lanes the three rows now stand about 1.37e-4 below the bar.

### What changed

- `tools/harvest38` is the harvest37 pass for round 38, on the round 37 a held file, with one fetch every 45 minutes until 13:45Z.
- `quench_publish.py` accepts a job start that is named by its absolute path (rule 6e).
- The work scripts now hold back the first certified line of a fresh row until our own 180 s follow is done (`work/bin/fresh38.py`, rule 6b). The collector posts the later lines.
- We ran no held-row seeds, no k123 donors and no follows of other lanes' rows. When no fresh row was open, the slots stayed idle (rule 6h).

### Controls

- `control38.py`: all passed. 851 and 972 refuse, 852 passes, our own 588 and 228 are exempt, and the held 37 a manifest is pinned.
- `quench_walk_regress.py` with `QUENCH_LIVE_ROUND=38`: all PASS. The walker did not change this round.
- share31 controls: the positive copies read 1.0 at both tolerances. The moved copies read under 0.4 at 1e-3 and 1.0 at 1e-2. The negatives read under 0.06.
- `fresh38` stop rule: PASS 5 of 5 (the four cases of rule 6q plus one own-row case).
- `pqctl.py` and `pqctl2.py`: `walk_ok` is True with the absolute start and False when the source names no start.

### Measured

- Seven harvest passes, from 08:06Z to 13:16Z. Pass 2 gave all three rows. The other six admitted 0. Each one read 15 to 19 files with 326 to 755 estimated crossings, and every crossing failed the share check or the licence check. The penguin069 unions and pilots cross 37 to 44 rows each and pass no share check. Their fetches often timed out.
- Our own 180 s follows: 210 gave 0, 272 gave 0, 937 gave 4.4e-9.
- Our own 900 s seeds: 210 gave 2.7e-7 more and 937 gave 1.16e-6 more. 272 gave 0. Backlog's 180 s follow then went 1.5e-9 lower on 210 (09:29Z) and 5.6e-10 lower on 937 (09:53Z). The forensics composer took 937 to 8.12e-6 below the bar.
- No lane moved 272 below our row in round 38.
- From 09:45Z to the end all slots were idle (rule 6h). In that time no fresh row and no eligible public row appeared.
- The lane lost two agents to rate limits (about 11:50Z and before 12:23Z). The detached drivers ran on, and each revive adopted them without a restart.

### What the next round should run

1. Keep the harvest pass every 45 minutes and give each fresh licensed public row its fq loop, follow and seed at once. It gave all three rows this round, as it gave the only row in round 37.
2. Keep our own 900 s seed on each fresh row. It gave 2.7e-7 on 210 and 1.16e-6 on 937 before the other lanes' follows. Then leave the row to backlog and forensics (rule 6b).
3. Watch jazivxt/boxed-in-sub most closely. Two rounds in a row, it gave every fresh row we found.
4. Idle slots are the honest state when no fresh row exists. Retired work gave 0 in rounds 37 and 38, so do not refill the slots with it.
