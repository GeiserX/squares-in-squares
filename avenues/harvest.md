# Avenue: harvest and polish (2026-11-12)

The harvest lane reads every public source of the competition at regular times and takes each n that beats our held file under an accepted licence. Its polish slot runs the `fq` quench on new files of the other lanes. This page starts at round 17. The earlier rounds are in the results tables `results/harvest-best-*.tsv` and in [docs/LANE-LOG.md](../docs/LANE-LOG.md).

## Round 17 (2026-11-12)

**Result: the lane ends the round with 2 n, 7.41e-5 below the held file.** Both are `fq` quenches of files of other lanes. Each is just under that lane's own file. The quench of the midm lane's 593 is 1.933e-5 below the held file and 3.5e-9 below the midm file. The quench of the family lane's 860 is 5.481e-5 below the held file and 1.7e-10 below the family file. The public sources gave no new layout below the takes of the other lanes. Seven more quenches certified for a time, among them 973 at 2.198e-4. In each case a builder lane then certified a lower file. Rows certified after 17:42 UTC go to round 18.

The held file is `gather/round16-2026-11-12a.csv` (22.1664224426). Every row was certified against `gate/cand-round16-1112a/details.csv`. A row had to beat the same n in every `take-*-r17` dir by more than 1e-10.

### What ran

boxA rebooted at 15:08 and 16:15 UTC, and the agent hit a usage limit at 17:52 and 19:05 UTC. The lane ran in four parts. They were 15:13 to 16:08, 17:43 to 17:52, 18:03 to 19:05 and 19:08 to 20:10 UTC. The jobs on the box ran on through the last two cuts. One harvest process and one polish process ran on boxA. From 19:18 UTC a second polish slot ran the fq quench on the five newest builder files. Other lanes kept its load at 20 to 250 on 10 cores.

| pass | time (UTC) | notebooks and datasets new or re-run | kept |
|---|---|---|---|
| p | 15:16 to 15:22 | 41 and 2 | 370 from jazivxt/boxed-in (Apache 2.0). It ties the midm lane's 370 to 1.1e-15. |
| q | 16:00 to 16:08 | 38 and 0, one failed download | none |
| r | 17:44 to 17:51 | 40 and 1 | the same 370. Eight wins of about 1e-10 each stay out, because alexchilton/squares-in-squares-starter-kit has the licence "Other". |
| s | 18:24 to 18:31 | 38 and 0 | none |
| t | 19:03 to 19:17 | 40 and 2 | the same 370. Seven wins of 5e-11 each stay out under the 1e-10 rule. |

In pass s, GitHub refused the account list of kenaznia-doga with a rate limit (HTTP 403). The pass read the 21 clones it already had, so a new repo of that account would not show.

The polish slot (`tools/polish_follow.sh`, one slot, `take-polish-r17`) ran one `fq` quench on each new certified file of the other lanes:

| n | file the quench started from | polish gain on that file | then passed by |
|---|---|---|---|
| 973 | twoshort, modules corner | 8.2e-9 | family at 16:02 |
| 911 | modules corner | 7.9e-10 | family |
| 910 | family, one shell down | 9.5e-8 | family at 16:08 |
| 982 | stair-c corner, modules | 5.0e-10 | corners at 18:06, then readers |
| 863 | readers, one shell up | 1.7e-9 | readers |
| 921 | corners, modules | 4.1e-10 | readers at 19:05 |
| 593 | midm, kick and quench | 3.5e-9 | not passed, in the take |
| 860 | family, one shell down (second slot, 19:18 to 19:53 UTC) | 8.3e-10 | not passed, in the take |

A new trap: the 860 run hung from 18:35 to 19:09 UTC. Its `engine_polish.py` pool worker used 0.3 s of CPU in 33 minutes, and the slot waited for it. The lane killed the worker by hand, and the slot went on to the next n. `daily_polish.sh` has no time limit per n, only the deadline of the whole run.

### How to read round 17

- **The public sources have stopped moving below us.** Five passes in four hours found one tie and no real win. The only other wins were 1e-10 or less, eight of them under a licence we do not accept. One pass every 90 minutes is enough now.
- **The builders quench their own files.** Since round 16 each builder lane runs `fq` before it certifies. A second quench finds 1e-9 or less. Of 70 polish runs, 8 certified lower and 2 still stood at 20:00 UTC. The two that stood are worth 7.4e-5 to the take, but only 3.7e-9 to the score, because the other lane's file is nearly as low. A polish slot that only follows certified files is worth little.
- **The `--seen` check of `polish_follow.sh` works.** After the reboots it did not run any start file twice.

### Not run yet

- A polish slot with the soft-box search of `methods_soft.py` after `fq`, on the near files of the family and readers lanes. The 19:18 UTC run had the soft step on, but the deadline came before it.
- A licence read of the alexchilton starter-kit description. Its eight wins are worth about 8e-10 in total, so it waits.
- A time limit per n in `daily_polish.sh`, so a hung pool worker costs minutes, not a whole slot.

## Round 19 (2026-11-12)

**Result: the lane ends the round with 5 n.** They are 4.790e-4 below the round 17 file and about 3.1e-5 below every other take. All five are `fq` quenches of new files of other lanes. 980 counts in full (2.095e-5), because no other take holds it at 22:20 UTC. 858 is 9.9e-6 under the family r17 file. 986, 982 and 860 are 6.9e-8, 6.0e-10 and 3.8e-10 under the files they started from. The public sources gave nothing new.

The held file is `gather/round17-2026-11-12a.csv` (22.1635211736). Each row was certified against `gate/cand-round17-1112a/details.csv`. It also had to beat every `take-*-r17` dir and every live `take-*-r19` dir by more than 1e-10.

### The time limit per n

`engine_polish.py` now runs each n in its own process group. With `--n-limit SECONDS`, an n still in its quench at that time is killed with its `fq` call, and the run goes on to the next n. That n keeps nothing. `daily_polish.sh` passes `N_LIMIT`, which is 1200 s by default. A SIGTERM to `engine_polish.py` also kills the running `fq` calls.

The controls, at 20:17 UTC:

- n = 498 with no hang still certifies the win of the docstring: 22.803808951 to 22.803695436 in 26 s.
- n = 498 with its `fq` process stopped by SIGSTOP stands at 0 CPU, as the 860 run of round 17 did. With `--n-limit 20` the run printed `LIMIT n=498 killed after 20s` and ended with exit 0. No worker and no `fq` process stayed behind.
- A SIGTERM to the parent ended it with exit 1, and no `fq` process stayed behind.

The limit did not fire in the real runs of this round. The longest `fq` step on one n took about 6 minutes.

### What ran

Two processes ran on boxA from 20:15 to 22:21 UTC. The load of the box was 19 to 25.

| step | time (UTC) | result |
|---|---|---|
| harvest pass u | 20:17 to 20:25 | 38 notebooks and 0 datasets re-run. Merge gain 3e-10 on 692, 810 and 869, 5e-11 each, all under the 1e-10 rule. 0 n kept. |
| harvest pass v | 21:46 to 21:58 | 40 notebooks and 0 datasets re-run, 1 failed download. The same three rows of 5e-11. 0 n kept. |
| follow polish, one slot, `fq` only | 20:19 to 22:16 | 68 runs, 9 certified lower on their start file by 1e-10 to 9.5e-8. At 22:20 UTC 982, 986 and 860 still beat every take. |
| soft slot 1 | 20:25 to 21:03 | `fq` then 150 s of soft-box search on 800, 861, 919, 922 and 982. `fq` lowered 919 and 982. The soft step found nothing. |
| soft slot 2 | 21:12 to 21:41 | the same on 858, 910, 980 and 987. `fq` lowered 858, 980 and 987. The soft step found 987: 1.63e-5. |
| soft then `fq` | 21:41 to 22:16 | `fq` on the soft 987 gave 1.19e-5 more. Soft first on 907, 859, 295, 700, 332 and 147: one find, 295 at 7.24e-5, and `fq` on it gave 1.21e-5 more. A second soft search on 987 and on 295 found nothing. |
| final take | 22:16 to 22:21 | `finalize.py` against 32 take dirs: 858, 860, 980, 982 and 986 kept |

The two soft finds did not hold. At 22:20 UTC the family lane held a 987 2.8e-5 lower and the midm lane held a 295 2.8e-6 lower.

The first look of the follow polish took 29 minutes. `near_starts.py` scored all 751 files under the `near/` folders of the r17 and r19 take dirs, and the slot did no `fq` work in that time. It queued 489 near starts, and the slot reached only a few of them.

### How to read round 19

- **The public sources are still dry.** Passes q to v (six passes in six hours) found no row worth 1e-10 under an accepted licence.
- **A soft-box search of 150 s found 2 of 15 new files.** Then `fq` gave about 1.2e-5 more on each find. The finds were on a modules corner (987, after `fq`) and a k123 join (295, before `fq`). It found nothing on the 9 family and readers files. A second search on each find found nothing.
- **The follow polish pays only when no builder runs `fq` on its own file.** 980 is the only large row of the follow and soft slots, 2.1e-5. Its start file left the border take before the round ended.

### The licences of two sources

- **alexchilton/squares-in-squares-starter-kit** (dataset, Kaggle licence "Other"). The description says the kit's own code is CC0, except `metric.py`, which is Kaggle's. The record packings in `records.json` are David Ellsworth's, and the kit does not relicense them. `best_current.csv` merges the kit's own packings with the public outputs of about twelve named notebooks, and it gives no licence for that data. So the dataset stays out. The same author's notebooks (`squares-101-the-starter-kit-*`, `fault-line-dp-basin-hopping-*`, `certified-merge-of-public-packings-*`) carry Apache 2.0. The merge already takes them, and in pass t it took the second choice from `fault-line-dp-basin-hopping-lb-22-2620` for all 8 rows that the dataset lost on its licence. `certified-merge-of-public-packings-lb-22-5978` ships a per-n `submission_sources.csv`, so a row from it can name its upstream notebook.
- **lucifer19/think-select-reclose** (notebook, Apache 2.0, the Kaggle default). Its snapshot datasets carry "Other (specified in description)". The description of the v41 snapshot says every block comes from the public output of kirilltym's notebook "22.2212 CPU/CUDA/MPS EDA+Module LP" (Apache 2.0). The notebook names the source of each stage in its code, with URL, author and licence, for example 204 from Doga Ozden's s204-upper-bound under CC BY 4.0. So its rows are Apache 2.0 through the notebook, with the upstream named. The snapshot data adds nothing that the upstream notebooks do not hold already.

### Next

- Run the soft-box search for 150 s on each new certified file of the modules, k123 and midm lanes, then `fq` after a find. The two finds plus `fq` gave 2.8e-5 (987) and 8.4e-5 (295) on their start files. A builder held a lower file of both by 22:20 UTC, so a soft slot must reach a new file within minutes.
- Carry `seen-near.txt` from one round to the next, or set `NEAR_MAX=0` on the first look. The first look of this round cost the polish slot 29 minutes.
- Keep one harvest pass every 90 minutes, or fewer. Six passes in a row found nothing.

## Round 20 (2026-11-12 to 2026-11-13)

The base was the round 18 file (`gate/cand-round18-1112a`). A result had to beat it and also every frozen `take-*-r19` dir and every live `take-*-r20` dir. The budget was 2 processes on boxA, from 22:36 to 00:55 UTC. The box rebooted at about 22:48 UTC and killed both queues. They ran again from 22:51 UTC.

### What ran

| step | time (UTC) | result |
|---|---|---|
| follow polish, `fq` only, slot w1 | 22:36 to 00:55 | `tools/polish_follow.sh` on `take-*-r20` and `take-*-r19`, with `seen.tsv` and `seen-near.txt` carried from round 19. The first look took 7 s, not 29 minutes. |
| soft box, then `fq` on a find | 22:39 to 23:25 | 150 s of `methods_soft.py` on each new certified file of round 20 within 2 minutes of its write, then on the per-n lowest file of the frozen r19 takes. |
| second `fq` worker, slot w2 | 23:25 to 00:55 | `work/worker2.sh` takes lines from the same queues as the follow, with the same lock and the same `daily_polish.sh` call. |
| near starts at 1e-4 | 00:10 | `tools/near_starts.py --max 1e-4` on the `near/` folders of six r20 lanes: 16 starts. 11 were new and went to the near queue. |
| take | 22:52, 23:27, 00:05, 00:56 | `work/finalize.py` of round 19 against 31 take dirs. |

### How to read round 20

- **The soft box found nothing.** It made 42 searches of 150 s with 0 finds. In round 19 it found 2 in 15. The new files of round 20 come out of an `fq` quench or a kick scan, and the soft box does not move them.
- **The `fq` follow pays a little on each new file.** The follow made 119 runs and kept 22 files lower than their start, by 1e-10 to 1.3e-5. Most of the kept files lost to a later file of their own lane.
- **Wider near starts gave nothing.** None of the 11 near starts between 2e-5 and 8.8e-5 above the round 18 file went lower with one `fq` quench. Each run ended in under 10 s.
- **A lane drops a row when a polish of it wins.** The start files of 700 and 811 left the takes of corners and family. Our `fq` file had beaten them. So the gain of this lane over the other takes is the margin of the polish, not the gain over the round 18 file.
- **Trap: kill by pid.** At 23:25 UTC `pkill -f 'take-harvest-r20/work/sf/run.sh'` matched nothing, because `run.sh` was started as `./run.sh`. So from 23:25 to 00:31 UTC the lane ran 3 processes on a budget of 2.

### Results

The take holds 9 n, 8.81e-4 under the round 18 file. Over the lowest file of another lane that the follow saw for the same n, the margin is only 6.0e-8 in sum. The full rows are in `results/harvest-r20-2026-11-13.tsv`.

| n | gain on round 18 | margin on the start file | start |
|---|---|---|---|
| 601 | 1.184e-4 | 5.8e-10 | take-midm-r20 |
| 700 | 2.813e-5 | 9.9e-10 | take-corners-r20 |
| 793 | 2.442e-5 | 1.7e-8 | take-family-r20 |
| 811 | 6.894e-5 | 2.1e-9 | take-family-r20 |
| 859 | 4.392e-5 | 4.2e-10 | take-readers-r20 |
| 869 | 1.138e-4 | 1.3e-10 | take-readers-r20 |
| 969 | 4.628e-4 | 1.7e-10 | take-invent-r20 |
| 980 | 2.096e-5 | 3.8e-8 | take-polish-r19 |
| 982 | 9.4e-10 | 3.4e-10 | take-polish-r19 |

The output contract asked for a second `fq` quench on a box other than boxA. That did not happen: the budget named boxA only. Every row is itself the output of an `fq` quench that ran until it made no more gain.

### Next

- Drop the soft box from this lane. It made 0 finds in 42 searches this round.
- Run the `fq` follow with 2 workers from the first minute. From 23:25 UTC two workers kept the queue short, and the queue ran empty at 00:04 UTC.
- Keep `NEAR_MAX` at 2e-5. The 11 starts between 2e-5 and 8.8e-5 gave nothing.

## Round 21 (2026-11-13)

The base was the round 19 file (`gate/cand-round19-1112a`). A result had to beat it, every frozen `take-*-r20` dir and every live `take-*-r21` dir. The budget was 2 processes on boxA.

### What ran

| step | time (UTC) | result |
|---|---|---|
| follow polish, `fq` only, 2 slots | 01:04 to 03:25 | `tools/polish_follow.sh` on `take-*-r21` and `take-*-r20`, with `seen.tsv` and `seen-near.txt` carried from round 20. The agent died at about 01:27 UTC on a usage limit. The follow ran on to its deadline and left 8 n in `take-polish-r21`. |
| follow polish again | 09:53 to 12:10 | The same command with a new deadline. boxA had rebooted at 05:36 UTC. A second agent started it and died 5 minutes later. The third agent adopted it. |
| take | 01:16, then every 30 minutes from 09:50 | `work/fin.sh` runs the round 20 `finalize.py` against the frozen r20 dirs and the live r21 dirs. |

### How to read round 21

- **The follow keeps a file on most new layouts, but by very little.** From 09:53 UTC it made 77 runs and kept 18 files. Most margins over the start file were 1e-10 to 7e-7.
- **The take shows the gain of other lanes.** Each row is an `fq` quench of a file that another lane made in round 21. That lane then drops its own row, because our file is lower. So the gain over the round 19 file belongs to the lane that made the layout. The real gain of this lane is the polish margin over the start file.
- **The take changes with every look.** Between 10:32 and 11:05 UTC, rows 640, 752 and 929 left the take, because other lanes went lower. Rows 415 and 992 came in, and 809 came in at 11:53 UTC.

### Results

The take holds 9 n, 7.586e-4 under the round 19 file. The margin over the lowest file of another take for the same n is 2.56e-4 in sum. That number is too high, because some lanes dropped the row that our file beat. The polish margin over the start files is about 1.7e-6 in sum, and 992 holds most of it. The full rows are in `results/harvest-r21-2026-11-13.tsv`.

| n | gain on round 19 | margin on the other takes | lowest other take |
|---|---|---|---|
| 415 | 1.816e-05 | 4.3e-10 | take-midm-r21 |
| 698 | 1.993e-05 | 2.0e-05 | none |
| 809 | 1.741e-04 | 6.7e-06 | take-midm-r21 |
| 810 | 2.591e-04 | 7.4e-05 | take-readers-r20 |
| 853 | 1.880e-07 | 1.8e-07 | take-family-r20 |
| 930 | 1.548e-04 | 6.1e-05 | take-readers-r20 |
| 931 | 9.309e-05 | 9.3e-05 | none |
| 980 | 8.215e-09 | 5.3e-10 | take-harvest-r20 |
| 992 | 3.925e-05 | 1.7e-06 | take-midm-r21 |

The output contract asked for a second `fq` quench on a box other than boxA. That did not happen, because the budget named boxA only. Every row is the output of an `fq` quench that ran until it made no more gain.

### Next

- Keep the `fq` follow with 2 slots. It is cheap, and it puts a floor under every new file of the round.
- Count this lane's gain as the polish margin, not as the gain over the held file.
- Run the follow next to the design lanes, not in place of them. The large gains of round 21 came from the kick scans and the readers.

## Round 22 (2026-11-13)

The final take holds 49 n, 0.0061126668 below round 20. Its margin over the frozen round 21 and other live round 22 takes is 0.0058508063.
The base is `gate/cand-round20-1113a/details.csv`. Every row passed `floatsafe` at 2.2e-11 and an `fq` quench on boxD.
The [result table](../results/harvest-r22-2026-11-13.tsv) records each source, licence, start score and remote proof.

### Public output

A bounded public check ran from 14:20 to 14:26 UTC. It listed 100 recent competition notebooks and checked 30 output lists.
It marked 15 output sessions as new or unmatched. Thirteen notebooks supplied 114 selected data files. It read data only and ran no notebook code.
The metric merge found 72 candidate wins. The clearance and score filters kept 69, worth 0.0083863002 against the score bar captured at 14:22.
The omitted n were 495, 535 and 697.

The 69 starts came from three notebook outputs:

| source | starts | licence |
|---|---:|---|
| `areebbb/sis-certified-union-micro-shrink-lb-22-17479` | 59 | Apache 2.0, the Kaggle default for public notebooks |
| `kmmmvs/squares-public-merge-daily` | 9 | Apache 2.0, the Kaggle default for public notebooks |
| `alexchilton/fault-line-dp-basin-hopping-lb-22-2620` | 1 | Apache 2.0, the Kaggle default for public notebooks |

All 69 starts were matched or beaten in the live takes at 15:06 UTC. Other lanes received the starts before the whole batch finished.
This check covered the latest 100 competition entries. It did not cover every dataset, register entry or GitHub repository.
The next full delta can use `take-harvest-r22/work/public/data` as its previous harvest. Older metadata there is marked as carried and not rechecked.

### Follow work

Two local worker slots followed fresh takes and near files. One slot ran the public check while the other continued its quench.
The completed local runs are below. An fq find is a certified solver decrease. A raw update also passed the held-file and start-file cuts.

| input | completed fq runs | fq finds | raw take updates |
|---|---:|---:|---:|
| certified takes | 51 | 7 | 5 |
| generic near | 66 | 12 | 1 |
| handed designs | 46 | 13 | 9 |
| public starts | 37 | 26 | 24 |

The first useful near find was 502. It gained 5.32e-6 on a forensics rectangle start and briefly led the live bar by 3.49e-6.
An unquenched reader walk from 640 to 693 gained 2.17e-5 on its start. It led the live bar by 7.04e-6 before another lane went lower.
The already quenched 911 copy ran for about 15 minutes and found no gain.
The take also forwards 28 per-run near files. Their sidecars retain the supplied notices and mark inherited notices that still need resolution.

The result table gives both score margins. `polish_gain` measures the change from each start.
Other lanes remove rows that lose, so the margin over their remaining rows can grow. The current take has 0.0001765942 of change from its start files.

### Collector and controls

[harvest_collect.py](../tools/harvest_collect.py) caches certificates by file content and checks the current competing files.
A cache shortcut requires that the exact competing file still exists. Removing that peer admits the result again.
It writes each result after its remote quench, with the csv before the atomic table update.
It preserves a better published packing while a newer input waits.
Two 900-second collector timeouts occurred during the public batch. Completed remote proofs survived both cuts.

The controls passed:

- A known 502 improvement was accepted. A live tie was rejected with cold and warm caches. Removing the peer admitted 502 again.
- The near exporter wrote one 502 near file and no accepted row. The small 813 change produced no near file.
- The n=798 control kept score 0.01740337376048 when given a weaker input at 0.01741290264046.
- An excluded directory stayed byte for byte unchanged.
- The shorter quench reduced a loosened n=10 from 3.7245209949 to a certified 3.7071067813.

Remote quenches began with the default flags. The final passes used `--no-alm --loosen 1.0 --pit 40 --flip-top 8` on certified inputs.
The best certified packing stays when the remote output is worse. Each proof records its input hash, host, output score and chosen file.

### Next

- Run a public delta at the start of the next round. This check found 69 starts and 0.0083863 of score after a 16-hour gap.
- Quench fresh unquenched reader ends first. The 693 walk gave 2.17e-5 on its start and 7.04e-6 on the live bar.
- Keep forwarding distinct per-run near files. The 502 rectangle gave 5.32e-6 on its start before another lane passed it.
- Cap a repeat quench of an already quenched file sooner. The 911 copy used about 15 minutes for no gain.

## Round 23 (2026-11-13)

The final take holds 13 n, 0.0019719865 below round 21.
Its margin over frozen round 22 and other live round 23 takes is 0.0005530111.
The [result table](../results/harvest-r23-2026-11-13.tsv) records sources, licences and remote proofs.

### Public delta

The full delta started first, from `take-harvest-r22/work/public/data`.
Public passes: 2.
The passes downloaded 8 notebook output sessions and 10 datasets. Fetch logs have 83 failure lines.
Register listing or clone failures: 0.
The register pass and metric merge read downloaded files as data.
The scalar reader recovered 12 witnesses with field coefficients or interval coordinates. None passed the 1e-10 gain threshold.
Three regression tests cover narrow root brackets, coefficient order, interval bounds and unit bases.
Four follow tests cover ancestry fields, public credits, winning inputs and owned process identity.
New public starts went to the handoff log as soon as they certified.

### Follow

[harvest_follow.py](../tools/harvest_follow.py) checks new takes and handed layouts between quenches, with a 60-second scan interval.
The full slot gives fresh reader ends priority. The short slot first drains certified copies.
Queue age raises older starts, and every handoff recipient is scanned. Distinct layouts retain immutable starts and source metadata.
The full slot limits a local quench to 180 seconds. The short slot uses 45 seconds. Search and remote quenches share the 18:30 UTC deadline.
It retains the better certified start when fq worsens a file.
Each accepted result passes floatsafe at 2.2e-11 and a certified-input quench on boxD.
A winning build enters the remote proof queue before its optional local search.
The source filter excludes the five rejected round 22 ancestors and SA donors. Metadata snapshots retain content hashes.

| input | recorded local attempts | decreases on start |
|---|---:|---:|
| design | 213 | 30 |
| fast-design | 376 | 116 |
| fast-take | 94 | 12 |
| public | 4 | 0 |

The lane recovered 6 outputs during a drained restart. Their process exit status is not claimed.
The lane forwarded 50 per-run certified near layouts. It saved 277 waiting starts under `work/pending.json`.
The final take has 0.0000000030 of change from its start files.
Peer lanes can remove rows after a lower harvest result arrives. This can raise the reported margin over their remaining takes.

### Controls

The feasible n=10 control shrank from side 3.724521 to certified side 3.707107.
A known n=502 improvement passed. A live tie failed.
A decimal-only copy queued once, and a weaker replacement preserved the better original.
An expired remote quench failed before SSH.

### Next

- Stage fresh winning designs before their optional local quench. The remote proof keeps each valid layout available to the follow lanes.
- Recheck the 277 saved starts against the next bar. Fresh designs gave 30 decreases in 213 recorded attempts.
- Keep public checks spaced apart. The passes downloaded 8 notebook sessions, but only the first pass supplied qualifying starts.
- Keep immutable starts and source notices. The n=502 control preserved the better original against a weaker replacement.

## Round 24 (2026-11-13)

The final take holds 4 n, 0.0000059186 below the round 23 candidate.
Its margin over other live round 24 takes is 0.0000059183.
The [result table](../results/harvest-r24-2026-11-13.tsv) records sources, licences and remote proofs.
The signed change from the immutable starts is 0.0000000003.
After the main handoff at 20:05 UTC, licence cells also state Samanyu seed ancestry and seed n.
For twenty named counts, clean alternatives use the round 22 held threshold and compare with clean peers.
The reported candidate gain remains a signed comparison against round23a.
Both source classes remain saved under `work/`. Unknown seed roots stay out of the take.
A producer can remove a beaten row, which raises the margin over the remaining takes.

### Public delta

The first full delta used `take-harvest-r23/work/public/data` as its previous harvest.
The second started no earlier than 21:00 UTC. Public passes: 2.
They downloaded 9 notebook output sessions and 7 datasets.
Fetch logs contain 5 failure lines. Register listing or clone failures: 1.
The merge read downloaded files as data. Public starts require a check of the supplied per-n source records.
The first pass supplied three clean public starts: 416, 542 and 634.
Five public rows matched excluded side families through a changed source wrapper and stayed out.
Their centred coordinates differ from the excluded starts by at most 6.6e-6.
Their source records leave that ancestry unresolved. The measurements are in `work/public-source-audit.json`.
The public source reader now follows the baseline credits of a polished output.

### Follow

[harvest_follow.py](../tools/harvest_follow.py) uses the round 23 candidate and compares only live round 24 takes.
Fresh designs get priority over the 277 saved starts from round 23.
At 19:46 UTC the short slot also switched to fresh designs first.
The preceding sample had three decreases in ten design attempts and none in eleven short take attempts.
The fresh admission and near output windows are 0.015 of side. Backlog keeps the 2e-5 score window.
The old output cutoff hid the certified 595 and 690 quenches.
They gained 3.77e-5 and 3.66e-5 of score on their starts but remained above the live bar.
The full slot allows 180 seconds for a fresh design. Backlog and short-slot quenches allow 45 seconds.
The first 911 backlog quench was stopped without an output during a drained reload.
The lane then applied the shorter backlog limit.
The follow checks handoffs between quenches. Each published row has a certified-input quench on boxD.
Search and remote quenches share the 22:15 UTC deadline.

| input | recorded attempts | smaller than start estimate |
|---|---:|---:|
| backlog | 1 | 0 |
| design | 95 | 16 |
| fast-design | 158 | 48 |
| fast-take | 15 | 0 |
| recovered | 1 | 0 |

The lane retains 25 distinct certified near layouts and saved 1484 pending starts.
Recovered outcomes without a claimed exit status: 5. Explicit source-audit interruptions: 2.

### Controls

The feasible n=10 control reached certified side 3.707106781322462.
Ten regression controls passed. They check source ancestry, public credits, winning inputs, process identity, round scope and the second public start time.
The nested-source control exposed a field that the earlier reader omitted.
The source reader now follows nested metadata and reads `finish_source` and `finish_licence`.
Policy fields stay separate from actual ancestry.
The final restart spent 17 minutes and 11 seconds on its first source scan.
Some fresh handoffs waited beyond the requested few minutes.
The pending list preserves starts that did not run.
The parent audit withdrew 228, 790 and 847 from relaxed eligibility.
Their frozen border 735 parent reaches Samanyu seed 365.
The source reader now expands frozen take ledgers and dated held records before assigning a seed flag.

### Next

- Keep a worker on fresh starts while source discovery runs in bounded steps. Full design attempts decreased 16 of 95 recorded starts.
- Recheck the 1484 saved starts against the next candidate after fresh handoffs.
- Space public deltas by new sessions or at least 90 minutes. This round downloaded 9 notebook sessions.
- Keep recursive source checks and certified-input remote proofs.

## Round 26 (2026-11-14)

At the end the take holds one n, 375. It is 4.53e-5 below the round 25 b file and below every other live round 26 take.
We published 17 rows at 14:11 UTC, worth 0.0018615 below the round 25 b file.
We withdrew six of them at 15:18 UTC under rule b. Other lanes then went lower on the other ten n, mostly from our files.
At 16:05 UTC, 11 live rows of other lanes cite a harvest r26 file, and they hold 0.00254 below the round 25 b file.
The [result table](../results/harvest-r26-2026-11-14.tsv) records the sources, licences, remote proofs and the end status of each published row.
The first agent of the lane died at 13:24 UTC on a usage limit. A second agent took over from its STATE.txt at 13:31 UTC.
The second agent lost its connection at about 16:29 UTC. A third agent took over at 16:36 UTC.

### Public delta

The first delta ran from 12:50 to 13:19 UTC, 13.5 hours after the round 25 fetch.
It brought 8 datasets and 10 notebook sessions.
The merge against the round 25 b file found 22 n below the bar, worth 0.0025577 before the live bars.
Every winning layout is new on 2026-11-14. None of them is in a public file we fetched up to 23:21 UTC on 2026-11-13.
The same layouts pass between public merge notebooks. The first are lucifer19/think-select-reclose (07:30 UTC) and jazivxt/boxed-in-sub (07:51 UTC).
Later copies are in the jazivxt/boxed-in dataset, amirhezekiahespanto/debut (09:12 UTC), the alexchilton fault-line notebook (09:31 UTC) and the starter kit.
[origin_scan.py](../tools/harvest26/origin_scan.py) lists every public copy of each layout with its date.
Three notebooks record per-n credits: lucifer19 in `validation_v54.json` and `validation_v55.json`, kmmmvs in `merge_report.json`, and alexchilton in `merged_sources.csv`.
Every credited upstream is a public notebook output under Apache 2.0.
The starter-kit `best_current.csv` that kmmmvs credits has the same sha256 as the alexchilton fault-line notebook output that lucifer19 credits.
So each row names lucifer19/think-select-reclose as its file, or jazivxt/boxed-in-sub for 971 and 972, and lists the credits in its source cell.

### Excluded layouts

[share_ac.py](../tools/harvest26/share_ac.py) compares a layout with every layout of rules a to d for the same n.
It reports the share of squares within 1e-6, 1e-3 and 1e-2 of an excluded layout, and the largest centre distance.
Its positive control is 858. The public 858 is the prvsiyan 1105 layout (share 1.000 at 1e-6), so 858 stays out.
The other 19 winners are no copy. Their largest centre distance to an excluded layout is 0.165 to 0.87.
Their share within 1e-3 of the prvsiyan 1105 layout is 0.0 to 0.76.
Their share with our own held layout of the same n is in the same range, so that share alone does not show a descendant.
Our held 375 and 453 are identical to the prvsiyan 1105 layouts. Their recorded sources are older public files (the starter kit and jonathan1506), which prvsiyan's best-of merge also took.
The second delta (14:22 to 14:35 UTC) added new winners only on 639, 691, 745, 858 and 918.
These are the five counts of rule a. For 639 and 918, 0.94 and 0.96 of the squares lie within 1e-3 of the excluded layouts.
For 691, 745 and 858 the share is 0.73 to 0.79. They stay out.

### Rule b check by shared squares

The backlog and quench lanes flagged 10 of our rows at 15:00 UTC.
Each of those rows has a largest centre distance of 0.165 to 0.542 to the prvsiyan 1105 row of its n.
The other rows sit at 0.55 to 0.85.
A largest distance does not show descent, because one moved square sets it.
[nearest_old.py](../tools/harvest26/nearest_old.py) measures the share of squares within 1e-3 instead.
It compares each row with the prvsiyan row, with our held row, and with every older public layout whose side is within 2e-3.
The [table](../results/harvest-r26-nearest-old.tsv) holds the result.

- 453, 706, 761 and 818 share 0.001 to 0.016 of their squares with the prvsiyan row. They are other designs, so they stay.
- 416, 499, 646, 654, 695 and 814 share 0.42 to 0.76 with the prvsiyan row.
  The nearest older public layouts are the alexchilton fault-line `c0.csv` of 21:16 UTC on 2026-11-13 and a submission file of 18:32 UTC.
  These hold the prvsiyan rows unchanged, so a descent through a rule b row stays possible.
  We withdrew the six rows at 15:18 UTC. They were worth 2.0e-5.

We then measured the other kept rows the same way. 459, 595, 791, 850, 909 and 971 share 0.000 to 0.003 with the prvsiyan row.
Our new 375 shares 0.168 with it. That prvsiyan row is our held 375, which the alexchilton starter kit held on 2026-11-09.
The prvsiyan dataset dates from 2026-11-13, so prvsiyan copied that layout. The new 375 is not built on a rule b row, so it stays.

### Publication

[cand26.py](../tools/harvest26/cand26.py) certifies each start. [harvest_collect.py](../tools/harvest_collect.py) runs one fq quench on boxC from the certified file and publishes against every live round 26 take.
The collector now proves the largest held margin first. Before this round it went by ascending n.
19 starts went in. 910 and 972 fell out because the midm lane held lower rows (0.0162821 and 0.0155037).
The boxC quenches took 11 to 23 seconds each and moved the 17 rows by 2.2e-8 in all. The public layouts are already fq-converged.

### End of the round

The second delta at 14:22 UTC and the third at 15:18 UTC brought no new layout outside rule a.
The third delta added the malyshevdanil living atlas output of 14:29 UTC. It wins 26 n, each with a layout of an earlier public winner.
The last collector pass ran at 16:05 UTC against every live round 26 take. It kept only 375.

- 453, 459, 595, 706, 761, 791, 818 and 971: midm, backlog, classfill and soft hold lower rows grown from our file of the same n.
- 909: midm holds a lower row built with our 850 file.
- 850: forensics holds a lower row of its own, 3.3e-9 below ours.
- 910 and 972 never entered the take. The invent lane holds lower rows built with our 972 file.
- The forensics 654 row takes one window from our withdrawn 654. We handed that to forensics and main.

A second collector pass at 16:37 UTC kept 375 again.

### Near-miss starts and the excluded layouts

near_scan.py filtered its starts by licence and by their share with our held layout. It did not compare them with the layouts of rules a to d.
[nearpub_excl.py](../tools/harvest26/nearpub_excl.py) does that for every start. It takes the best of 8 symmetries and reports the share of squares within 1e-6 and 1e-3 of each excluded layout.
Its positive controls are the exact copies in the queue. The starts of 535, 540, 696, 737 and 988 print a share of 1.000 at 1e-6 with the prvsiyan 1105 row.

- 276 of the 338 starts share 0.4 or more of their squares within 1e-3 with an excluded layout. They are out.
- 62 starts are clean. [clean_queue.py](../tools/harvest26/clean_queue.py) keeps only them in `queue-fresh.tsv`. The full queue stays in `queue-fresh-all.tsv`.
- We withdrew our four near files 127, 971, 988 and 998. Each one was a single fq of an out start, and no live take cites them.
- The backlog lane claimed 30 near-pub starts by 16:56 UTC. 28 of them are out starts, and it went on claiming them after our stop lines. None of its take rows comes from a near-pub start at 17:17 UTC.

### Late public check

At 16:38 UTC [moved_since.py](../tools/harvest26/moved_since.py) listed the sources that moved after the third fetch. It needs 20 seconds, while a full delta needs 23 minutes.
Four competition notebooks had run again. [fetch_some.py](../tools/harvest26/fetch_some.py) fetched only their outputs.
Only jazivxt/boxed-in-sub (run 16:08 UTC) listed a csv. Its merge took 68 seconds.
It is lower than the earlier public winners on 850, 909 and 910 and on the rule a counts.
The live round 26 takes are lower on 850, 909 and 910. So nothing new entered the take.
Four more notebooks ran between 16:13 and 16:55 UTC: nilanjansaha123/its-a-secret, amirhezekiahespanto/debut v34, the starter kit notebook and the malyshevdanil living atlas.
None of them listed an output file by 17:00 UTC, so the next round fetches them first.
The starter kit dataset also moved at 16:31 UTC. Its licence is "Other", which the allow-list does not take.

### Measured dead ends

- A local fq on boxA under load 30 to 40 gave no output in 180 seconds. The lane now skips it and proves on boxC.
- Public near misses. [near_scan.py](../tools/harvest26/near_scan.py) found 345 starts on 182 n, 2e-10 to 6e-5 above the bar, in the new public files. 338 of them differ from our held layout.
  [near_fq.py](../tools/harvest26/near_fq.py) ran one boxC fq on 12 of them, one per n. None crossed the bar. Four converged onto the held optimum within 1.7e-8, and eight moved by less than 1e-8.
- Kicks of public near misses. midm_scan.py ran lkick and kick, 400 seconds each, on three fresh public designs unlike our held layout.
  856 took 14 tries and stopped 1.1e-7 over the bar. 789 took 35 tries and tied the bar (-1.8e-15). 372 took 44 tries and stopped 2.6e-12 over it.
  These designs are other optima of the same depth as the held one.

### Next

- Run moved_since.py every 20 minutes and fetch only the moved outputs with fetch_some.py. Then audit each winner the same day. The 13.5-hour gap before this round held 0.0026 of new public layouts. The late check fetched and merged a moved notebook in under 2 minutes, while a full delta needs 23 minutes.
- Measure rule b by shared squares before publishing, with nearest_old.py. This round we measured after publishing, and the withdrawal reached one row of another lane.
- Measure every public start against rules a to d with nearpub_excl.py before it enters a queue or a handoff. 276 of 338 fresh near-pub starts were out, and 28 of the 30 starts the backlog lane claimed were out starts.
- Publish fresh public layouts at once for the kick lanes. Other lanes went lower on 10 of our 11 kept n within two hours, mostly from our files.
- Do not fq or kick public near misses again. Twelve fq runs and three kicks stayed on or above the bar. The backlog lane's 30 kicks of near-pub starts put no row in its take.

## Round 27 (2026-11-14)

The round uses `<scratch>/bounties-squares/round27-briefs/bar27.tsv` (work folder, not published).
It compares each certified row with every live round 27 take.
The Samanyu ancestry exclusion is lifted. The prvsiyan rule excludes shares of at least 0.4 within 1e-3.
The penguin union exclusions and the public licence rules still apply.

[The round 27 tools](../tools/harvest27/) keep fetched outputs and queued inputs as byte snapshots with SHA-256 hashes.
The proof worker runs one fq quench on boxC from each certified input.
Fresh follow inputs also retain the source walk and snapshots of its reachable files.
Search and proof jobs share the 23:45 UTC deadline. The take is due at 23:55 UTC.

### Recovery and controls

The lane rechecked 45 public near starts whose old worst-match label named a Samanyu seed.
37 were excluded in round 26. Of those, 19 now pass and 18 still fail the remaining share exclusions.
The queue also includes eight starts that were already eligible. All 27 entered before fresh public rows.
Older certified harvest takes enter the next source scan.

The positive control rejects the exact prvsiyan 858 at share 1.000.
It accepts the independent harvest 453 at share 0.006622516556291391.
The new coordinate cache stores numpy arrays instead of 500500 row dictionaries.
This reduces memory use during the shared machine's paging stalls.
At load 51, each driver used about 11 CPU seconds over 16 wall minutes.

### Public checks

The first targeted fetch checks its-a-secret, debut v34, the starter kit and the living atlas.
The starter kit supplies its output. The other three initially list no output.
The driver repeats changed-output checks every 20 minutes and reads live handoffs every five minutes.
It reads public files as data and runs no fetched code.
The [result table](../results/harvest-r27-2026-11-14.tsv) records the final take.
The full measurements and exclusions remain in the take directory's work folder.

### Source snapshots and the second pass

The n=990 recovery passed its remote proof at score 0.013529713828686063.
It recovered 0.00015622368679957255 against the round's bar. The proof added no quench gain.
It remains subject to the final live comparison.

The second fetch supplied six notebooks, including the living atlas output that was unavailable earlier.
Its full merge exceeded the 900-second limit while reading archived research checkpoints.
The retry selects final submission CSVs first. The raw archives remain available as data.

Two n=499 follows lost their producer paths after queueing.
The worker now checks the complete recorded source walk and every pinned byte hash.
It also checks later withdrawals. It can retain a superseded source whose pinned evidence remains intact.
Controls accept a missing producer path and a REINSTATE line. They reject changed snapshot bytes and a new hard withdrawal.
Source proofs now include their own content hash, so identical packing bytes cannot overwrite another source record.

### Bounded public reader

The final-CSV metric retry also exceeded 900 seconds on the shared box.
[quick.py](../tools/harvest27/quick.py) now reads four columns and computes bounding sides with numpy.
It checks the live bar and excluded-layout shares before queueing a candidate.
The proof worker still runs floatsafe and the remote quench before publication.
Its positive control reads 1000 puzzles and matches the real public 972 score within 1e-12.

The finalizer also passed a control with a real n972 certificate.
It retained the certificate against the base and removed it when a lower live peer appeared.
It rejected changed certificate bytes. The control wrote only an isolated work fixture.

### Public ancestry withdrawals

The quick reader found public rows whose shared-square measures pass but whose donor chains do not.
We withdrew 639 and 918. The atlas 639 names only a local merged file.
The 918 recipe names a donor745 from the boxed50 union, at the side of the public745 measured out at share0.667.
Its own share0.062 with the old918 did not clear that ancestor.

We also withdrew the penguin-sourced916. Its same-session source notice names excluded inputs but gives no per-n916 separation from them.
The three rows and their immutable proofs remain under work/. The handoff log names the withdrawals.
The Samanyu rule does not cause these withdrawals.
The public132,157,793 and851 remain eligible under Apache2.0 and the share checks.

The atlas later republished the same916 geometry with another local merged-file credit.
It was withdrawn again. The public gate now covers these916 aliases until their specific source chain is clear.
Independent local constructions can still pass a complete source walk.

### Final take

The final take holds 132,157 and851, all from jazivxt/boxed-in-sub under Apache2.0.
They passed floatsafe at2.2e-11 and a certified-input fq proof on boxC.
The gain against bar27 and the other live round27 takes is0.001547021143061711.
The finalizer wrote the take at23:54:40 UTC and the report at23:55:02 UTC.
The recovered990 and the499642 follows did not remain in the final take.

The closing feed read handoffs through23:40 UTC. The proof worker stopped at23:42:37 UTC.
The remote audit found no owned solver. All350 remote files matched their local SHA-256 copies.
The hash control rejected a wrong hash. The lane then removed its boxC r27 scratch directory.

The next round should start with the four-column public reader and complete each source-specific audit before publication.
Both full metric merges timed out at900 seconds. The smaller reader delivered the new public132157793851.
Unchanged public near misses gave no crossing in the initial20 attempts. Certified snapshots and fresh geometry should precede them.

## Round 28 (2026-11-15)

The round uses `<scratch>/bounties-squares/round28-briefs/bar28.tsv` (work folder, not published).
Search ends at 05:45 UTC. The final take is due at 05:55 UTC.
The report follows that deadline.

[The round 28 tools](../tools/harvest28/) read changed public final CSVs first.
One proof worker quenches certified inputs on boxC.
The feed follows fresh rectangle compositions and k123 joins before older snapshots.
It keeps input bytes, hashes and source records at queue time.

The source adapter checks complete CSV ancestors and original seed rows against the remaining share exclusions.
It ignores retention notes that mention a withheld file and keeps explicit withdrawals.
A parked file reopens only when its record gives a Samanyu-only reason.
The original source walker remains unchanged.

The controls rejected exact prvsiyan858 at share1.0 and accepted independent453 at share0.006622516556291391.
The withdrawn n684 ancestor also measured share1.0.
Repeated adapter reloads passed after fixing an early recursion error.
The finalizer retained a real certificate and rejected a lower peer and changed certificate bytes.

Twelve prior certified snapshots remained below the new bar.
One passed the current source checks. Eleven failed ancestry or complete-ancestor checks.
The first public pass supplied n499, certified6.681e-6 below the bar.
These are interim results. The [result table](../results/harvest-r28-2026-11-14.tsv) records the final retained rows.

### Policy update at 00:19 UTC

The main session relayed a change in the round handoff log.
Own layouts and their descendants are exempt from share tests.
This includes held801 and original seeds503 and983.
The lane removed ancestor and original-seed share gates and reopened affected starts.
Fetched public rows still pass the share test.
Explicit ancestry to the prvsiyan file stays excluded.
The earlier seed and ancestor measurements remain as historical measurements.

The public archive reader passed an offline control with 1000 real puzzles.
It extracted data from a licensed archive and matched the n499 score.
It skipped the unchanged archive version on the next pass.

### Fair queues and source diagnostics

Rectangle arrivals exceeded proof throughput and delayed other lanes.
The feed now interleaves changed files from the live lanes.
The proof worker rotates lanes and takes each lane's newest input.
Public inputs and restored certificates keep first priority.
A live check reached backlog, classfill and rebuild inputs after this change.

A source record for the own n934 layout quotes its old share-test refusal.
The quoted test says that the refusal is lifted because the row has no public first source.
The walker had matched the licence text inside that diagnostic sentence.
Its adapter now removes that specific diagnostic before matching source names.
The real n934 control walks 303 recorded files and passes.
A separate control with an explicit prvsiyan-file source still fails.

The hourly dataset delta fetched a changed CC0 archive from samanyu1808.
It also fetched the living atlas's newly available outputs.
Their first four CSV screens held 39 candidate entries and no eligible public input.
The initial public n499 remains the only new public input at this checkpoint.

### Binding a queue entry

The feeder now copies the input before walking its source tree.
It checks the input hash and root source record again before admission.
It also binds referenced parent hashes to their snapshots.
A changed input or source record returns to the next scan.
The withdrawal check uses the time of the first snapshot.
A vanished take file no longer crashes the directory scan.

Controls reject mixed input versions and accept matching versions.
They detect a changed source record and handle a vanished file.
Fresh per-n follows copy the producing take's source and licence into their record.

### Worker recovery

A variable collision in queue rotation overwrote one completed n863 job record.
Its pinned input sidecar and full hash restored the record.
The take and packing data remained intact.
The worker now keeps the results path separate and validates queue records.
An idle-publication control writes twice and preserves the exact job bytes.
The worker also saves its certificate cache after each completed outcome.

A failed public listing page no longer aborts the pass.
Known notebook outputs remain in the targeted checks.
A control preserves the first listing page and cached targets when the second page fails.
Source matching now selects the row's own job and rejects nested producer references.

### Ranking fresh inputs

The feed and proof queues now rank each lane's inputs by their estimated gap to the live bar.
The rotation still gives each lane a turn.
This keeps a new below-bar build ahead of a newer near miss.
The control uses real n805 and n985 layouts.
It selects the older n805, then reverses that choice when the live n805 bar moves lower.

The first retained fresh follow is n995 from a modules layout.
Its initial certificate gained about 5.74e-6 against the round bar.
The required quench added only 4.4e-13. The module build supplied the gain.

### Final source cells

The finalizer copies public source references and per-n credits from each pinned source walk.
It keeps the donor counts and source labels of the areebbb credit table.
It also names the recorded upstream licence terms, including Other terms.
The full source record stays linked for the assembler.
The compact cells stay below the default TSV reader's field limit.

Controls check every current row's owner binding and repeated enrichment.
The n995 control retains donor462, donor703 and Other notices.
A changed canonical source proof fails its hash check.
Numeric comparison fields do not become source notices.

### Resolved seed records

Two old withdrawals say that a missing sidecar or intermediate was found.
The source adapter had treated the word missing as an unresolved source.
It now recognises those two resolved phrases before applying the lifted seed rule.
The real n985 control passes its 11-file source walk with no missing files.
A separate control still refuses a missing parent with no root.
The adapter also filters cached withdrawal records after a reload.

### Equal input rewrites

The feed logged 285 admissions for 189 immutable jobs.
Repeated source walks caused the 96 duplicate events.
The feed now skips a known clean follow job before walking the same bytes again.
The immutable queue already kept the first record for that key.
A real n499 control detects the existing job.
Public input priority and an unknown hash still reach inspection.
The proof worker and finalizer continue to check pins and withdrawals.

### Round 28 close

The final take holds n = 372, 416, 640, 646, 812, 860 and 995.
Its gain is 0.000006865997930871615 against both the round bar and other live takes.
The retained quenches added 0.00000000019778201298947806.
Most gain came from the producer layouts.
All 213 queued proof jobs completed with no worker errors.
They produced 19 provisional admission events before live comparisons.
The new public n499 first gained about 6.681e-6, then other lanes improved it further.

The host rebooted at 05:39:32 UTC after the proof queue had drained.
The finisher was restored at 05:42:06 UTC.
No search restarted after the feed cutoff.
Recursive scp timed out after 180 seconds.
An archive stream recovered the copy and matched all 430 file hashes.
The remote scratch was then removed.
The final audit retained all seven rows at 05:54:47 UTC.
The report was written after 05:55 UTC.
No lane process remains.

## Round 29 (2026-11-15)

The round uses `<scratch>/bounties-squares/round29-briefs/bar29.tsv` (work folder, not published).
Search and remote quenches end at 11:45 UTC. The final take is due at 11:55 UTC.
The report follows that deadline.

[The round 29 tools](../tools/harvest29/) check changed public final CSVs and fresh layouts first.
One proof worker runs each required quench on boxC from its certified input.
Each queue entry keeps its input bytes, source record and parent snapshots with SHA-256 hashes.
Own layouts retain their exemption from share checks. Fetched public rows retain the remaining source and share checks.
The five original penguin union rows stay excluded, including their old harvest copies.

Certification imports border's [finesafe.py](../tools/border/r28/finesafe.py) without changing it.
Its first n503 control matched the ladder certificate and passed both the pandas metric and 2.2e-11 clearance.
Source controls rejected the original union858, exact public prvsiyan858, changed snapshots and later hard withdrawals.
They accepted independent453, missing producer paths with complete pins and retention notes.
Repeated source adapter reloads passed.

The bar files now use atomic replacement.
An early worker read during setup saw a partial bar and stopped before any remote search.
The worker restarted after the full 1000-row bar was available.
The first public pass returned HTTP404 for listings and cached targets.
The driver retains those targets for later checks.

[The result table](../results/harvest-r29-2026-11-15.tsv) records the final retained rows.

### Reader source selection

Old reader records name one donor inside a shared state file.
Walking every job in that file introduced unrelated missing parents.
[reader_records.py](../tools/harvest29/reader_records.py) selects the named donor and checks both its credit hash and packing hash.
The original admission tools hash the credit tuple separately from the CSV.
The adapter pins the complete state bytes and the selected source record.
It also retains areebbb's per-n donor notices and pins that credit table.
The real n813 source walk now passes. Missing donors and changed credit hashes fail.
The original excluded reader858 still fails through its recorded penguin union source.

Canonical ancestry records can cover a vanished original when their content hash, packing hash and source evidence match.
The n850 record passed this control. A wrong path, changed proof bytes and an unhashed record failed.
The n684 and n911 walks still fail on other missing parents and valid withdrawals.

Backlog claims now follow the exact input hash across queueing and dispatch.
The control skips matching bytes at a moved path and admits changed bytes at a reused path.

### Exact n805 parent recovery

The frozen stair-c donor copy retains the requested n805 bytes, SHA-256 `3905b3f6064dcafa…`.
Its source walk passes. [versions.py](../tools/harvest29/versions.py) resolves references that request this exact version.
It keeps the archived source record and records the original path's byte pin.
The current file at that path keeps its later `6cccf736fa1621f6…` bytes.
The affected n748 module now passes its 161-file source walk.
A different requested hash does not resolve. A hard withdrawal of the exact recovered bytes still fails.

Fresh inputs estimated below every live bar enter the urgent proof queue.
Other fresh inputs keep their lane rotation and gap ranking.

The deadline finisher also writes the final doc section and commits the measured result table.
It checks the readable rules and restricts that commit to the harvest doc and table.
The early-close control refuses before 11:55 UTC.

### Continuations of moved near files

The first n498 quench gained 6.02166035923446e-6 of score.
It ended 2.7611246622427643e-11 below the bar, short of the 1e-10 admission margin.
Fresh own near outputs now enter the same rotating proof queue for a continuation.
A step must gain more than 1e-9 of side to create another continuation file.
This also applies to a published result whose last step passed that threshold.

The n498 saved-job walk first expanded a full reader-state byte pin as ancestry and reached the 3000-file cap.
The adapter now keeps that pin separate from the named donor's source edges.
The corrected source walk passes with 46 files.
The original full-state bytes still verify. A changed-byte control still fails.
Source revision checks now include both adapters and refresh their loaded code.

### First certification

A fresh k123 near layout supplied n454, 5.120337287500831e-8 of score below the bar and current live takes.
Its required certified-input quench added zero. The urgent queue handled the winning input before other near misses.
Its actual receipt passed the finalizer control. A lower peer and changed certificate bytes failed.
The first continuation of n498 added only 8.881784197001252e-16 and stopped.
These are interim measurements. The deadline audit decides the final take.

### Restored public transport

The legacy metadata GET routes returned HTTP404 in five passes.
The installed [Kaggle SDK client](https://github.com/Kaggle/kaggle-sdk-python/blob/main/kagglesdk/kaggle_http_client.py) uses RPC calls on `api.kaggle.com`.
[rpc.py](../tools/harvest29/rpc.py) uses that read-only transport and keeps the existing version signatures.
Its controls returned 100 notebooks and the known starter-kit files with HTTP200.
Bounded downloads read 1000 detail rows and a valid 7,237,193-byte CC0 archive.
A failed sources download leaves its completed CSV outside the selected data tree and does not advance the cache.
Public checks now precede source walks. Source admission has a 60-second limit and writes snapshots atomically.

The first restored pass screened seven CSVs. It found 70 candidate entries and 20 eligible entries before proof.
The public n90 and n848 first gained 0.00018160257913657496 and 0.0004928715156369279 against the bar.
The public n907 also certified before a peer superseded it.
Urgent proofs now rank by live margin. The real n848/n582 control reverses its choice when n848's bar moves lower.

### Public-first source correction

Main's 07:34 note and border's 07:45 audit exposed a missing check on public-first ancestor nodes.
The earlier n454 intake does not count. Its retained source tree contains a public-first n498 with share1.000 against1105.
The lane withdrew n454 and 25 exact near versions. Some near versions also reached the source-walk node limit.
[public_sources.py](../tools/harvest29/public_sources.py) classifies each recorded node before measuring its share.
It uses the queued source text and pinned CSV snapshots. It does not compare own construction nodes.
A pure fq continuation preserves its first origin. A constructed row keeps its own origin and still checks its actual public ancestors.
Controls keep own503,983 and801 exempt. Identical503 bytes fail under public-first origin.
Public90 and848 measured0.000. Public582 measured0.130584. These remain below the0.4 exclusion threshold.

The source walker now refuses a node-limit result as incomplete.
The 745/858 rule matches only the true join identifiers named by main.
The three readers/family donor identifiers pass that rule's control.
Only the exact r28 01:51:44 withdrawals corrected by main are lifted, subject to the other source checks.
Eight-character withdrawal prefixes bind matching bytes and leave a different version at the same path eligible.

### Public coverage and source formats

At the coverage check, the cache held 13 public references.
It found 88 uncovered references. Of these, 87 predated the delta cutoff.
The feeder now screens 20 older references per pass as well as changed recent outputs.
Each output has a 90-second read limit. The pass stops starting references after 300 seconds.
The batch control screened 20 of 25 older references and left five for another pass.

Prior round29 outputs also return through exact version links when new source metadata arrives.
The control kept a per-n parent and its CC0 notice through a carried metadata chain.
It left a fresh output version unchanged.

The wider sweep found merge reports and inherited source receipts outside the legacy reader's formats.
Those records stay out until an adapter can trace them.
[public_records.py](../tools/harvest29/public_records.py) pins known per-n credit files and public metadata before queueing.
Controls accepted vanished originals with intact pins.
Unknown source formats, actual1105 source names and changed pins failed.
The existing n412, n582 and n848 pinned source proofs still pass.

Fresh twoshort n412 crossed the bar after its certified-input quench added 1.70e-10 of score.
Its queued proof pins 44 parents. Its public n372 ancestor has share0.3387096774 against1105.
A later live-path walk reaches changed producer records. The queued snapshots govern the retained bytes.

The n871 profile reached 1184 files and expanded 174,920,400 bytes of source text.
Its walk alone took 34.06 seconds. Full admission exceeded the 60-second limit.
An early public-refusal trial still exceeded that limit and was reverted.
The unchanged input remains deferred.

Invent's note promoting its new n641 build mentioned older withdrawn bytes.
The source walker first misread that retention note as a refusal of the new build.
The corrected filter ignores this promotion note and preserves actual withdrawals.
The new n641 then passed its full 46-file walk without a share gate on own geometry.

### Certified continuations

The first continuation reader could reach later records at reused producer paths.
[continuations.py](../tools/harvest29/continuations.py) now uses the saved parent proof and the certified output receipt.
It checks that the near file equals the receipt's output bytes.
It pins the parent input, near file, sidecar, receipt and certificate.
Valid source withdrawals still apply to these exact pins.
The queue also checks that the records stayed unchanged while their snapshots were written.
The real n499 control passes. Changed parents, hard withdrawals and changed certificate bytes fail.

The side threshold replaces the earlier 1e-8 score threshold.
A saved-outcome pass found 110 steps above the side threshold and created 38 continuation files under the checks then in force.
Existing files and claimed inputs were skipped. Invalid source trees stayed held.
The feeder gives three continuation inputs a place before slower source checks and keeps its lane rotation.
The worker checks the source proof again after remote fq.
The corrected n641 follow added only 8.88e-16 of score and stopped.

### Archived public donors

An old n934 branch reaches held n550, whose record names an archived public n703 donor.
The per-n n703 file was gone. The earlier source check missed that public ancestor.
The original round22 areebbb CSV still holds it at the recorded side26.94021853054266.
Its share against1105 is0.47368421052631576, so that public source stays out.

[archived_sources.py](../tools/harvest29/archived_sources.py) recovers only the declared public donor row from its original frozen round.
It pins the selected row and its source metadata.
It also keeps the full archive as an audit byte pin without adding the archive's other counts as parents.
The actual archived public n462 control passes at share0.3268398268.
Own n703 and the original seed503 controls are not measured. A missing original public source fails.
An ambiguous original round also fails.
Source declarations in JSON records receive the same check. Policy examples do not create parents.

The later audit held 18 of 59 own near files under their exact hashes.
The retained n412, n582 and n848 source proofs still pass.

### Round29 close

The final take retains 3 rows. Its gain against the round bar is 0.0005132748248506402.
The gain beyond the other live takes is 0.0005132748248506402.
The queue recorded 392 outcomes and 19 provisional admission events.
It recorded 13 errors or pre-search refusals.
Every retained row passed the final source, receipt, byte and live-bar checks.
Search stopped by 11:45 UTC. The final report followed 11:55 UTC.

## Round 30 (2026-11-15)

The round uses `<scratch>/bounties-squares/round30-briefs/bar30.tsv` (work folder, not published).
Search and remote quenches stop by 17:45 UTC. The take is final at 17:55 UTC.
The report follows that deadline.

[The round 30 tools](../tools/harvest30/) start with changed public outputs through SDK RPC.
The other worker follows fresh layouts and keeps the exact input and parent bytes.
Certified continuations stop when side progress falls below 1e-9.
Every retained result requires a certified-input fq quench on boxC.
Own layouts keep their share exemption. Recorded excluded sources and public-first source checks still apply.

The source adapter now reads handoff withdrawals through the live round.
Its control found a synthetic round 30 withdrawal. The original parser stopped at round 29.
The source and pin controls also passed. They reject excluded public858 and changed snapshots and accept independent453.
The finalizer audits source pins, receipt bytes and every live take before closing.

### Source admission cost

The feeder reuses the complete walk captured by its source check.
The n686 control preserved the original 23-file walk exactly.
It previously expanded the same graph twice.

The initial walker checked declared archived public donors as it reached them.
A known excluded n703 donor stopped the real n995 branch in 3.84 seconds.
That branch previously timed out after 60 seconds.
The permitted n686 control still matches the original walk and passes.
Full source checks and byte snapshots still govern every admitted input.

### Held branches and direct public parents

Main voided share checks on public files reached only through a submitted held row at 12:40:55 UTC.
The 13:32 clarification keeps checks on a directly used public parent that was never held.
Another held branch does not exempt that direct parent.

The source-path walk stops at held nodes for this check. It still follows direct parent paths.
A synthetic control rejects a bad direct public parent beside an unrelated held branch.
It permits the same public file when reached only through a held node.
The named n799 frozen donor also passes only on the held route. Its exact direct bytes remain withdrawn.

Pinned n376 and n814 pass the clarified path check.
The lane withdrew its exact n646 output after finding a direct public parent at share0.6640866873.
The feeder audits earlier near outputs under the same path rule and binds each withdrawal to its bytes.
Missing parents and recorded ancestry to the actual1105 source still receive their separate checks.

### Public metadata backoff

The fetcher now skips a notebook when its listed run matches the pinned output version.
Frozen round29 metadata supplied 221 exact-version run times. Changed runs still reach the output RPC.
An HTTP429 stops the pass until the next 20-minute refresh.
Controls query a changed run and skip an unchanged run. A rate-limit control stops after one request.
A partial source download preserves the prior signature and run time, so a retry remains eligible.

### Repricing restored certificates

The reopened n814 and n646 snapshots crossed the live bar.
Repeated n995 restores reached the existing floor with zero fq gain.
The lane stopped five pending n995 copies after those measurements.
Restored certificates now compare with the current live bar before dispatch. Fresh geometry keeps its follow queue.

### Referenced held nodes

A control exposed a missing boundary in the path reader.
The public row appeared inside a JSON node that referenced an actual submitted held file.
The reader now imports the forensics lane's SHA-verified held-file predicate without changing that tool.
It removes only that node's children from the public-parent walk.

The fixed control permits the held-only node. A direct public sibling and an unregistered held claim still fail.
Retained n376 and n814 pass the revised check. The two direct n685 near holds remain valid.

### Changed public layouts

A changed jazivxt/boxed-in-sub output supplied n228 at score0.03287318752927715.
It passed the public share check at0.000 and the required certified-input quench.
That quench added zero. The provisional gain against the round bar is about6.90e-5.
The public notebook's own output and metadata are pinned under work/public10.

The GitHub register changed by 79 commits. Its compare endpoint stopped at 300 files.
A full tree comparison covered 39,996 old and 40,472 new nodes without truncation.
It found 36 candidate data files across seven packets and three changed canonical witnesses.
Canonical n90 and n147 were above the bar. Canonical n228 was below it.
The take's n228 came through the separately fetched Apache2.0 notebook output.
The register licence and original Ono receipt remain pinned for provenance review.

Doga Ozden's new CC BY4.0 n228 design is another layout at share0.000.
It is 0.0037168 of side above the fixed bar. One certified-input fq made zero progress.
The lane handed it on as an uncounted diversity donor with its source and receipt.
No gain is claimed for that donor.

The changed kmmmvs merge credits n639 and n918 to a starter-kit dataset.
Its exact best_current hash matches a provenance-only archive read. The archive has no per-count source file.
Those two counts still lack an independent source chain and remain out of the solver queue.

### Held origin credits

An origin control found another false public classification.
A submitted held row still carried its historical public credit in the copy metadata.
The public classifier now stops at the same SHA-verified held origin used by the path reader.
It also ignores that origin's old credit when checking a copied row.
The control permits the held origin and still detects a direct public metadata sibling.
The direct public n858 control, bad sibling control and unregistered held claim all keep their refusals.

### Repeated ancestry lookups

A fresh n812 source walk still reached its 45-second diagnostic deadline.
It asked for 17,382 ancestry hashes across 305 texts. Only 643 were unique within their text.
The reader now keeps the first reference to each hash in a text.
A control reduced 50 identical references to one lookup.
The current n686 tree retained all 141 files and every text, held reference and refusal in the same order.

This removes repeated lookups. It does not solve the large-source admission limit.
The changed walk also reached 45 seconds on n812.
A 20-second profile spent 17.1 seconds in regular-expression reads.
A separate pattern profile reached source texts as large as 26.6 MB.
Those measurements point to compact source records as the next step for such trees.

A changed-method check also ran contact LP on the certified Doga n228 donor.
The positive control closed an inflated four-square grid from side2.001 to2.00000000004.
The donor itself made zero side progress in nine iterations and 0.832 seconds.
No further fq or take row was queued. Changed corner or band transfers remain the next use for this geometry.

The subwindow control finds three squares at side2 when the test bar is2.1. It refuses them at1.9.
The new Doga n228 donor had no qualifying window among 227 smaller counts.
Scans of 34 Doga orientations and 59 current public n228 orientations also found no live crossing.
Each orientation covered 227 smaller counts. The two scans took 13 seconds in total.
No solver jobs were queued. A future use of these donors needs a changed join design.

A late changed Living Atlas output supplied n401 at share0.0598503741.
Its certified input scored0.02536970562207075. The required fq reached0.025369693201232613.
That fq added1.24208e-8 of score. The provisional gain against the round bar is3.80397e-7.
The output, metadata and per-count credit in submission_sources.csv are pinned under work/public15.

A final changed-method check ran contact LP on the best n934 certified continuation.
Nine iterations took 57.62 seconds and made zero side progress.
Its input and parent receipt remain pinned. No extra fq was queued.

The late k123 n693 follow added3.0404e-8 of score through fq.
It crossed the fixed bar by about1.01558e-7 before final peer repricing.

### Nested source notices

The closing audit found a source-credit assertion on the saved n640 result.
Its restored record wrapped a continuation record, which wrapped the original source proof.
The notice reader now reaches the original record before it checks that proof's input hash.
The actual nested record passes. A changed root hash still fails.
The metric audit also checks source pins at every inherited level.

### Round30 close

The final take retains 5 rows. Its gain against the round bar is 9.253026560718247e-05.
The gain beyond the other live takes is 9.245911170574495e-05.
The queue recorded 447 outcomes and 26 provisional admission events.
It recorded 4 errors or pre-search refusals.
Every retained row passed the final source, receipt, byte and live-bar checks.
Search stopped by 17:45 UTC. The final report followed 17:55 UTC.

## Round 31 (2026-11-15 to 2026-11-16)

The round uses `<scratch>/bounties-squares/round31-briefs/bar31.tsv` (work folder, not published).
Search stops at 00:15 UTC. The take is final at 00:25 UTC, and the report follows immediately.
[The round 31 tools](../tools/harvest31/) retain immutable source bytes and deadline logs.
The [result table](../results/harvest-r31-2026-11-16.tsv) counts rows only after every live comparison and the required off-box quench.

The first delta fetched the 18:48 UTC jazivxt submission, with 43,682,640 bytes.
It supplied nine preliminary certificates. Backlog's assembler check rejected public n851 and n972 under rule3.
The seven remaining starts are n405,588,635,741,791,852 and974.
Their certificates total0.001716059873171361 against the fixed bar, before other lanes' follows.
Quench finished the inputs on its assigned boxes. Harvest counts no duplicate row held by another live lane.

### Public source controls

The initial rigid ICP missed the assembler's corner-box and median-offset alignments.
The corrected policy imports the frozen assembler's share30.py without changing that file.
It checks centre and corner bounding boxes, eight symmetries, and median-offset ICP at1e-3 and1e-2.
The actual public851 control refuses at0.46415981198589895 within1e-2. Public972 refuses at0.45267489711934156.
Public852 passes at0.3615023474178404. Exact858 and a moved-copy control refuse, and a spaced453 control passes.
The old rigid-ICP measurements are superseded by these controls.

Own layouts retain their exemption. The equality check includes square angles and every centre under all eight symmetries.
Every harvested comparison at n405,588,635,741 and974 equals the own Samanyu seed.
At n791 and972 only the oldest comparison is own. Later comparisons still run.
The current comparison dataset is version24 and matches the pinned archive's update time.

Sixteen exact public851/972 source files and near aliases were pinned for exclusion after the corrected check.
Their record is work/assembler-source-withdrawals.json in the take directory. Independent held851/972 inputs remain valid.
The take was empty at this correction. Other lanes received the source hold through the round handoff log.

### Source records and closing

Comparison archive labels initially looked like ancestry to the shared reader.
New public transport records keep diagnostics under its excluded key and preserve every real parent and the same coordinates.
A complete n741 walk passes. An actual forbidden source still refuses.
Fresh follow certificates preserve the original input pins inside an inherited record.

The adapter recognises the exact held round30c file named by the brief, with SHA starting883b1c6.
An unregistered path, an untyped count and a direct bad public sibling still fail the controls.
The private adapter also matches the shared source reader's four-field result. A complete public405 walk passes.

The authenticated local gh API recovered register headf46b0537 after an anonymous HTTP403 limit.
Its complete tree has40,478 nodes. Eight paths changed, with no changed packing data.
The author list has24 repositories and no changed pushed versions. Downloaded code was never run.

The lane has two local download and light Python processes, including its sleeping finisher.
It hands certified inputs to an assigned off-box quench lane. Every accepted output still needs its full source and metric checks.
Virtual-clock controls keep the fourteen-key report absent before the deadline and publish strictly after it.
The same control passes after a forced audit failure. Closing audits stop at least40 seconds before publication.

Repricing stored public files with the corrected measure recovered n743 and n911.
Their first certified live margins are about4.850e-5 and3.612e-4. Both were handed to quench before another public fetch.
A later Samanyu output supplied the same two geometries with bare source slugs in per_puzzle_L.csv.
The source guard now recognises that table and detects source columns in unknown filenames.
The actual untraced table refuses, while a matched declared trace pins in the control.
The other44 below-bar Samanyu candidates fail the source geometry check.
Two Samanyu aliases reached handoff before the guard took effect. Their exact source aliases are held until traced.
The independent direct jazivxt743/911 certificates remain valid.

A second revival adopted the live driver and finalizer without starting copies.
Rebuild claimed the independent direct743/911 roots for off-box work at21:26 UTC.
Two unselected contact reconstruction CSVs supplied2,000 layouts and22 below-bar candidates.
All22 failed source or share checks. The screen created no solver jobs.
The quick reader control contained a stale expected value.
The official metric and reader agree at0.015593904057188412 on the frozen972 fixture.
The corrected assertion passes.

Intake ended at00:10:18 UTC with273 completed jobs and none pending.
The outcomes contain196 certified handoffs for off-box fq and77 certificates above the live bar.
Harvest retains no duplicate row from those handoffs.

The original911 certificate passes the public share check at0.341 within1e-2.
Its first fq output fails at0.490, and a later backlog output fails at0.429.
The clean original remains a fallback. Each held output keeps its exact byte exclusion.
A lighter retry reached0.016197228767541594 but did not beat the live backlog row.

## Round 32 (2026-11-16)

The round uses `<scratch>/bounties-squares/round32-briefs/bar32.tsv` (work folder, not published), which includes every valid round 31 take.
[The round 32 tools](../tools/harvest32/) screen changed public files before source admission.
The [result table](../results/harvest-r32-2026-11-16.tsv) counts only certificates with a completed quench on an assigned remote box.
Search stops at 17:15 UTC. The take is final at 17:25 UTC.

The startup controls import the frozen assembler's share31.py.
They reject public n851 at 0.464159811986 and n972 at 0.452674897119 within 1e-2.
Public n852 passes at 0.361502347418. The exact n858 copy and the moved-copy control fail.
The spaced n453 control passes. Own n588 and n228 keep their exemptions.
The held boundary now verifies round31b, with SHA starting 1eda9d26.

The lane keeps two local processes for downloads and light Python work.
It hands certificates to the quench lane for the required quench on its assigned boxes.
Every handoff names exact bytes and both public share measurements.
No unquenched input counts in the take.

Historical replay is closed because bar32 already holds every valid prior take.
Fresh follows must beat the live bar by more than 1e-10 before dispatch.
The driver retains source snapshots and reads the current handoff log.
The finalizer preserves superseded CSV paths for other lanes' source references.

The first refresh fetched changed notebook outputs and one CC0 dataset.
GitHub supplied ten licensed packet packings and six canonical witnesses.
Four changed packets lacked a licence file and stayed out.
These are raw intake counts. Certification and final gains are separate measurements.

### Intake and recovery

The first pass supplied six distinct certified public counts: 442, 485, 530, 577, 585 and 911.
Their certified margin against bar32 totals 0.000341537262325886 before the required quench.
All six completed that quench through the quench lane.
At 11:41 UTC, their best live rows totalled 0.000352209917246826 against bar32.
Backlog held lower rows at 530 and 577. Harvest counts no duplicate row.

The current comparison dataset remains version 24, updated 2026-11-13 at 18:12 UTC.
It matches the pinned archive. Both share tolerances remain in use.

Initial screening delayed dispatch for about four minutes behind later files.
Dispatch now runs after each screened CSV. A saved checkpoint prevents completed files from repeating after an interruption.
The forced-interruption control resumes at the unfinished second file.
An unchanged delta now carries metadata without copying old raw packings for another screen.

The pose control preserves changed centres and angles. Two real n577 exports differ at a tolerance of 1e-8.
Only equal poses with equal scores share a handoff. Distinct layouts keep their runs.
New public handoffs use a single transport record, with comparison diagnostics under its excluded field.
Existing published aliases remain in place for source references.

The finalizer restarts an absent driver with a one-minute backoff and a three-per-hour limit.
The runtime control proves that a live driver is never duplicated and the deadline prevents a restart.
Intake stops at 17:10 UTC. The driver stops at 17:13 UTC for a bounded commit and push before 17:15 UTC.
The final report follows the take deadline at 17:25 UTC.

### Packing filenames

A header check found one unselected merged.csv from the changed fault-line notebook.
It held 1,000 layouts, with 43 raw sides below the live bar.
Every one failed the public share check. The screen created no solver jobs.
The selector now recognises the official packing columns in any CSV filename.
Its control accepts an unfamiliar filename and a UTF8 byte-order mark. It rejects a credit-only CSV.

### Repeated geometry checks

A later changed-source screen examined 611 candidates below the live bar. None passed the public share check.
The geometry cache now binds each candidate pose, every reference pose, and the measurement code.
Changing an input or reference forces a new measurement. Source and withdrawal checks still run separately.
On the frozen n851 control, an uncached check took 0.200875 seconds with references already loaded.
The cached check took 0.000666 seconds and kept the same refusal at 0.464159811986.
The full startup control suite passed with the cache enabled.

### Windows of the new public layouts

The bounded crop check used the six new public roots instead of round 30's Doga n228 layout.
It imported the unchanged literature_window.py reader, with SHA starting a9c80aa0.
The positive control finds three squares at side 2 under a bar of 2.1. It refuses them under 1.9.
Each input passed its source and public share checks before the scan.

The scan tried eight frames per root, starting with each original frame.
The other frames follow the most frequent square angles. The side margin was 5e-9.
All 48 scans completed in 89.683591 seconds and returned zero raw crossings.
No certificate, solver job or take row came from this check.
The sleeping finalizer resumed after the scan and its process was verified.
This crop pass stays closed until the input geometry changes.

### Published public descendants

At 16:06 UTC, five published engine descendants of the public roots passed both share tolerances.
They are n442, n485, n530, n577 and n585. Their CSV bytes and ledger rows stayed fixed during the audit.
The largest share within 1e-2 is 0.38461538461538464 at n585.
The current n911 winner is an independent held-row rebuild. It kept its exemption and received no share gate.

The audit resolves public aliases from the immutable source jobs.
This includes the Living Atlas aliases at n530 and n577.
Each result records the source row, exact bytes, snapshot and per-version measurements.
Every later changed output still needs its own check.
The comparison dataset remained version 24, with the same update time as the pinned archive.

### Late n292

A changed CC BY 4.0 repository from Doga Ozden supplied n292 at 16:34 UTC.
Its certified input gains 7.45509554e-5 against bar32. Quench finished the required certified-file fq by 16:38 UTC.
The second export has the same pose and score. It received no duplicate quench request.

The seven distinct public roots total 0.00041608821769467674 of certified input margin before peer follows.
A k123 join from the new n292 supplied n488, with a reported gain of 4.0922995468983814e-5 before peer follows.
That lane fixed its ancestor count cache and passed the n292-to-n488 source control.

The 17:00 UTC output check covered six current public engine descendants, including n292.
Every one passed both tolerances on fixed CSV and ledger bytes. The owned n911 rebuild stayed exempt.
The comparison dataset still matched version 24.

One original-frame crop of the new n292 checked 291 smaller counts at 17:05 UTC. It found no raw crossing.
The earlier 48-frame crop pass did not include this new input.

### Round 32 close

The screen recorded 6939 candidate decisions and 21 dispatch outcomes.
Certified handoffs cover 7 distinct counts before other lanes follow them.
Their fixed-bar margin totals 0.00041608821769467674.
The harvest take retains 0 rows after the required quench and live comparison.
Unquenched handoffs do not count as harvest gains.

## Round 33 (2026-11-16)

The round uses `<scratch>/bounties-squares/round33-briefs/bar33.tsv` (work folder, not published), which includes every valid round 32 take.
[The round 33 tools](../tools/harvest33/) fetch changed licensed public final files first.
The [result table](../results/harvest-r33-2026-11-17.tsv) counts only completed, certified-file quenches below every live round 33 take.
Search and closing work stop at 00:15 UTC on 2026-11-17. The take is final at 00:25 UTC.

The startup controls passed with the frozen assembler share check.
Public n851 fails at 0.464159811986 and n972 fails at 0.452674897119 within 1e-2.
Public n852 passes at 0.361502347418. Own n588 and n228 retain their exemptions.
The held boundary verifies the round 32 a file by its SHA-256 hash.
Source pins, changed-byte refusal, restart limits and interrupted-file recovery also passed.

The lane uses two local processes for downloads and light Python work.
Each passing file goes to quench immediately after screening, with both share measurements and exact source bytes.
Quench owns the required offbox fq loop and its output share check.
Unquenched handoffs do not count as harvest gains.

The fetch and GitHub checkpoints start from round 32.
Unchanged crop and public near-miss queues stay closed after their measured dry runs.
Live take follows belong to the assigned follow lanes. Harvest runs no held kicks.
The driver reads the current handoff log and records progress in STATE.txt.
Its finalizer can restart an absent driver within the process budget and closes the lane before the deadline.

### First source pass

The first pass screened 10 packing CSVs and recorded 336 raw candidates below the live bar.
None passed the public share check. No solver work was requested.

Two interrupted notebook downloads left completed packing files.
A diagnostic found two raw crossings in atlas143 and six in public152.
All eight failed the frozen share check. Their source records remain unproved, so none entered the queue.
The output list for atlas143 completes in one page with 18 files.
A request for 1,000 entries returns HTTP 400. The reader keeps its 100-entry pages.

The changed Apache 2.0 Explorer dataset holds frontier credits and viewer caches without packing coordinates.
Its frontier table lists 42 sides below bar33. Those side values cannot supply a packing certificate.
Downloaded code remains data and is never executed.

The driver reads every live ledger and inventories near files each ten minutes.
It also checks published public engine descendants when a new public root exists.
These reads do not claim the work assigned to backlog or quench.

### Bounded fetch recovery

Three notebook versions repeatedly hit the 120 MB download limit.
Final packing CSVs now precede diagnostic tables and archives.
A completed file keeps a byte receipt, so a later pass resumes without fetching that file again.
An unchanged version that reached the size limit stays closed. Changed runs and output sessions retry.

The controls preserve a final CSV before a large diagnostic file fails.
They refuse incomplete source admission and avoid another download of the unchanged version.
A changed signed URL reuses the completed bytes. A changed output version downloads new bytes.
The changed-byte control refuses a tampered completed file.

The recovery inspected 26 complete partial packing files.
Their 50 raw crossings all failed the frozen share check. No incomplete source entered the queue.
The four completed normal screens recorded 1,215 candidate decisions, with none eligible.
These diagnostics supplied no certificate or harvest gain.

### Output listing recovery

A newly published recovered-grain notebook exceeded the 20-page output-list limit.
The bounded reader now allows 200 pages and rejects repeated continuation tokens.
The first expanded attempt hit HTTP 429. The driver kept its 20-minute backoff.

Metadata calls now wait one second between pages.
A version-specific checkpoint retains completed pages after an interruption.
The controls resume at the next token, start fresh for a changed run and refuse changed checkpoint bytes.
The local checkpoint stamp never enters a Kaggle request.
The 25-page positive control returns its last packing file. The 200-page negative control refuses more pages.
This listing change has supplied no packing certificate yet.

The held boundary also retains the exact round 31 b file beside round 32 a.
Its hash comes from the frozen round 32 ownership receipt.
Both held-file controls pass. Unregistered paths and untyped counts fail.
These ownership checks preserve the exemption from public share checks.

### Main export of the large listing

The saved listing advanced from 13 to 75 pages across an interrupted fetch.
A bounded diagnostic read its completed main export before the listing finished.
All 43 raw crossings failed the public share check. No source or solver admission followed.
One sampled certification-cache record held four verdict fields and no coordinates.

The same measured dry run now follows fresh sources in the fetch order.
Its saved listing still resumes. A changed run regains its original priority.
The ordering control checks both cases.

### Fresh n812 and n907

The changed jazivxt boxed-in-sub file supplied two certified counts at 21:42 UTC.
Their margin against bar33 totals 1.126700124087776e-6 before the required offbox quench.
Both completed the midm_fqonce.py loop through the quench lane.
Backlog then improved n812 further.
At 22:07 UTC, the best live peer rows totalled 3.948451829716149e-6 below bar33.
These peer rows do not count again in the harvest take.

The 22:05 UTC output audit passed the current n907 output at 0.3164277839029768 within 1e-2.
The n812 comparison references are owned layouts, so they receive no share measurement.
Source pins and both public tolerances remain on each fresh certificate and applicable output.

A bounded crop pass used these two new certificates, replacing round 32's six old inputs.
Its grid control accepted three squares under side 2.1 and refused side 1.9.
All 16 frames completed in 61.329054 seconds. They returned zero raw crossings.
The crop queue stays closed on these bytes. No unquenched crop counts as a gain.

### Closing checks

At 23:03 UTC, both public certificate trees passed the full source walk and their exact byte checks.
Neither walk found an excluded ancestor.
The n907 input shares remain 0.239250275634 within 1e-3 and 0.316427783903 within 1e-2.
The n812 reference layouts retain their ownership exemption.

The full startup and recovery control suites passed again.
The report preview has exactly the 14 required keys. It counts no duplicate peer row as a harvest gain.
The large output listing reached 200 pages and 20,000 entries. Its already checked main export had no allowed crossing.
The source reader remains active until its cutoff. The finalizer closes the take and publishes the report at the required time.

### Round 33 close

The screen recorded 4064 candidate decisions and 2 dispatch outcomes.
Certified handoffs cover 2 distinct counts before other lanes follow them.
Their fixed-bar margin totals 1.1267001240877761e-06.
The harvest take retains 0 rows after the required quench and live comparison.
Unquenched handoffs do not count as harvest gains.

### Round 34 close

The screen recorded 2356 candidate decisions and 0 dispatch outcomes.
Certified handoffs cover 0 distinct counts before other lanes follow them.
Their fixed-bar margin totals 0.
The harvest take retains 0 rows after the required quench and live comparison.
Unquenched handoffs do not count as harvest gains.
