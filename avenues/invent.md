# Avenue: invent (2026-11-12, rounds 17, 19 and 20)

**Result: one n certified, 464, for 1.370e-05 of score. Ten measurements stay.**

**Round 19: one n certified, 969, for 4.628e-04 of score. Section 14 has it.**

- **A kick opens one layout that no kick had touched.** The scan of the midm lane ran on 25 such layouts and on 979. It found on 464, and kick legs from that find took it to 1.370e-05 of score. A second seed on 19 public layouts found nothing. 20 first scans on a third list found nothing.
- **Six kick tries tell whether a scan can find.** A pool of 15,692 kick tries says so. They are the tries of the midm lane and of this lane. In half of the scans, 3 or more of the first 6 tries came back to the start side. The later tries of those scans took 21% of the seconds and gave 3.6% of the gain. After a find the same scan finds at 6 times the first rate. 11 of the 15 largest steps came from the full kick at sigma 0.02 or 0.04, on 36% of the seconds.
- **The soft chain does not pay on public held layouts.** 40 passes ran 2,042,723 children on public layouts and our fq quenches of them. None found. That is the kill line. It puts the hit rate under 7.2% at 95%, below the 8.3% of the family and readers layouts.
- **The census is dead as a predictor, by its own kill line.** It left one lead. The board at m = 31, k = 10 to 17 sits on the design of 979 with 979's own end loss, within 0.3 squares. The same design fits the board at m = 28 to 30. After the takes of rounds 16 and 17 we are still 0.7 to 0.9 squares behind on those 44 n, 0.0207 of score.
- **The design of 979 has no corner zone.** Its two arms end at a plain block in the corner and never meet. The zone cut refuses it, with 82 other arm layouts. The 83 hold 64% of the gap at m 28 to 31.
- **The far ends cost more than the corner, in every design.** A new split reads the end loss of 199 layouts with no cut. The two far ends cost 4.7 to 7.5 squares and the corner 2.2 to 4.1. The far ends of 979 cost what ours cost.
- **The block of 979 is a corner of 4.13 squares.** The twoshort avenue put that pair at 4.70. A count from the parts gives 4.14. The same count puts a block corner within 0.5 squares of our staircase corners, so it is not the square that the board is ahead by.
- **One removed square opens a slide but never reaches held.** 979 less the end square of its arm of 9 slid by 0.0060. It ended 7.3e-4 above the held 978. Of 37 starts on 12 n, 5 slid and none ended below held. The idea is dead by its kill line.
- **The follow within the round was a second copy.** 4 passes on the new twoshort files found nothing. The soft lane of round 17 runs the same 14 files.
- **No larger n sits below a smaller one.** The monotone check ran over the held file and every live take dir. It found no n that can take the layout of n + 1.

This avenue has no slice. It reads what the other avenues measured, lists the five ideas with the largest expected gain that nobody has run, and runs the best one.

Words used here: "held" is `gather/round15-2026-11-12a.csv` (22.1672602051, gate dir `gate/cand-round15-1112a`). "The board" is the per-puzzle board of 2026-11-09. The side is `L = m + f` with `m` whole, and `k = n - m²`. A "stack" is a row of `c` tilted squares in a strip of width `c - 1 + f`, and its tilt `t` solves `c cos t + sin t = c - 1 + f`. An arm of such stacks gains `g = f - sin t` squares per unit of wall over the plain grid. "The soft chain" is the chain of `tools/softround/chain.sh`: two islands of the soft-box search (`methods_soft.py`) at box steps 2e-4 and 1e-4, then the fq quench of a find. A "pass" is one run of the two islands on one layout. "A square's worth" is the change of `f` that one more square costs, about 0.017 at m = 31. "The zone cut" is `modules.cut`, the reader that the modules, zones and classfill avenues build their libraries with. The one certified result is measured against the round 16 file (`gate/cand-round16-1112a`), which holds the same 464 as the round 15 file.

## 0. Kill lines and controls (each written before its first long run, from 13:41 UTC on)

### The coverage ledger (idea 1 of section 1), the one that runs

**The measurement.** The soft chain runs on the held layouts that never had a pass. The ledger of section 2 lists them: 62 public layouts and 37 fq quenches of public layouts from n = 300 up. 84 of them pass three tests. They are at n = 441 or more. They are more than 1e-6 of score from the board. They have no file in a round 16 or 17 take dir. They run in the order of how far the layout moved its n when it came in, the largest first. A find is a legal side below the start. A result counts only when it certifies.

**Kill line.** The idea is dead when the first 40 passes give no find. Zero of 40 puts the hit rate below 7.2% at 95%. The family and readers layouts hit at 8.3% (13 finds in 156 starts, rounds 11 to 15). The rule the soft lane uses today (start only family and readers layouts) is then right for public layouts too.

**Positive control.** The round 15 start `802-rea15.csv` (the readers lane's 802 before the soft search). On boxD the island at 2e-4 with seed 11 ran dry in 23,300 children, and the island at 1e-4 with seed 12 found twice, 2.139e-5 of score. The same two islands run on boxE from the same file. The control passes when they end at least 1e-5 of score below the start. It can fail: a wrong kernel build, a wrong start file or a slower box gives no find.

### The design census (idea 2 of section 1), the second to run

**The measurement.** The census takes every held layout of m = 28 to 31 that is two arms. It reads the two arm sizes from the tilts and computes one number, the end loss `E = (m - c2 + 1) g(c1, f) + (m - c1 + 1) g(c2, f) - k`. It then asks, for every n of the same m, at which f each held design would hold that n with its own E.

**Kill line.** Take the n of m = 28 to 31 that have a gap to the board. The idea is dead when no held design of another n predicts a side more than 0.3 squares' worth below held on any of them. It is also dead when E moves by more than 1 square inside one design class at one m: the prediction then says nothing.

**Positive control.** The census must place the design of each held n on its own n: predicted f equal to held f to 1e-9. The second control takes two held layouts of one class at neighbouring k and the same m. The prediction from one must hit the other's held f within 0.5 squares' worth.

### The plateau drop (idea 4 of section 1), added at 13:50 UTC before its first run

**The measurement.** In a plateau pair the held side of n is less than half a square's worth below the held n + 1. The board is far below both. Several of the largest single gaps are of this kind (791, 969, 973, 793, 796). The layout of n + 1 is then the better design, and n needs it with one square less. `invent_drop.py` takes one tilted square out of the held n + 1, quenches the start with fq, and does that for the tilted squares nearest each corner of the box. The best end gets one pass of the soft chain.

**Kill line.** The idea is dead when, on the first 6 pairs, no end is below the held side of n after the quench and the pass.

**Controls.** The tool control: the quench of the held n with no square removed must return the held side within 1e-7. It fails when the reader or the writer of the fq format is wrong. There is no positive control of the idea itself: we hold no pair where a single drop is known to pay. So a dry result says only that this scan with this quench does not reach the slide.

### The follow within the round (a part of idea 5), added at 15:20 UTC before its first run

**The measurement.** This round has no soft lane (that was wrong at 15:20 UTC: see section 7). The twoshort and classfill lanes certified new layouts on 14 n from 14:04 UTC on: 703, 796, 851, 852, 910 to 914, 973 to 976 and 978. None of them had a pass of the soft chain. Each gets one short pass from its certified file. A find counts only when it certifies below the score of its start. Below held is not enough.

**Kill line.** The follow is dead when the 14 passes give no certified find. Zero of 14 puts the hit rate under 19% at 95%.

**Positive control.** The round 16 start `700-mod16.csv`, the modules lane's 700 before the soft search, at score 0.016754413. The soft lane of round 16 took 9.15e-5 of score off it. The same short pass runs on boxE from the same file. The control passes when it ends at least 1e-5 of score below the start. It can fail: the short legs may not reach what the longer chain of round 16 found.

### The kick on the layouts no kick touched (idea 1 with another engine), added at 15:48 UTC before its first run

**The measurement.** The midm lane found that a small kick before the fq quench opens public files that no kick had touched ([midm](midm.md), section 5). `work/kick-list.tsv` in the take dir has the 85 held n from 441 up that its table and its claims do not cover. Each has 20 or more squares at a tilt of 1 to 43 degrees. Each has a gap of more than 2e-5 to the board, and no file in a take dir of round 16 or 17. 979 is one of them. Each gets one scan of `midm_scan.py --modes kick,lkick`, 75 s. 979 runs first, then the layouts of the first merged file by their gap, then our own builds.

**Kill line.** The idea is dead when the first 20 scans give no certified find.

**Positive control.** The held 374, a public file. The midm lane took 7.25e-5 of score off it with this scan. The same scan runs from the same layout in this lane's dir on boxE. The control passes when it ends at least 1e-5 of score below held. It can fail: the find may need a seed or a time that this scan does not have.

### The second seed of the kick, added at 16:04 UTC before its first run

**The measurement.** The control above was dry at seed 1 and found at seed 2. The midm lane ran one seed on most n. `work/kick-seed2.tsv` in the take dir has 74 public layouts where its one scan was dry. Each has a gap of more than 2e-5 to the board and no file in a take dir of round 16 or 17. Each gets one scan at seed 2, 75 s, the smallest n first.

**Kill line.** The idea is dead when the first 15 scans give no certified find.

**Positive control.** The scan of the held 374 at seed 2, which is green (section 8).

### The split of the end loss (section 9), added at 18:13 UTC before its first run

**The measurement.** It is a reading of layouts, not a search, so it has controls and no kill line. `invent_parts.py` splits the end loss E of a two-arm layout into the corner and the two far ends.

**Controls.** The parts must add to E within 1e-6 on every layout. The lowest corner of two 8-arms must be near the library's lowest, 2.47 squares. The far ends must agree with the far zone table of the [twoshort](twoshort.md) avenue. Each can fail: a wrong cut or a wrong arm size moves a part by whole squares.

### The monotone check (section 10), added at 18:15 UTC before its first run

**The measurement.** A layout of n + j with j squares removed is a layout of n. `invent_mono.py` lists every n whose best side is above the best side of a larger n, over the held file and every live take dir. There is no kill line: the check costs seconds and runs before each assembly.

**Control.** There is none that we hold: the held file has no such pair. The tool was read by hand on the pairs with equal sides (350 and 351, both at 19).

### The pooled kick tries (section 11), added at 19:14 UTC before its numbers were read

**The idea.** Every kick scan writes one row for each try: the mode, the flag set, the kick size, the end side and the seconds. The midm lane and this lane hold over 600 such tables on boxE. Nobody pooled the rows. A pooled table says which try pays for its seconds, and when a scan can stop.

**What a find is.** It is a try that ends below the side its scan holds at that moment. The scan must end more than 1e-10 of score below its start. The scans that end 4.9e-11 below their start only lose the padding of the held file. They count as dry.

**Control.** The table is split in two halves, the scans of odd n and the scans of even n. The cell (mode and flag set) with the most finds per 1,000 s on one half must be first or second on the other half. A ranking that changes between the halves is noise. The control can fail: with about 60 scans with a find, two halves can disagree.

**Kill line.** The pooled table is dead as a predictor when both of these hold. No cell with 300 tries or more finds at twice the pooled rate per second in both halves. And no rule on the first 6 tries splits the scans into two groups with find rates a factor of 3 apart. The better group must hold 5 finds or more.

## 1. The five ideas

The gap to the board is 0.1165 of score. 0.0513 of it is on m = 28 to 31 (217 layouts). The numbers below are from held and the board of 2026-11-09.

| # | Idea | Attacks | Expected gain | Cost | Kill line | State |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Coverage ledger.** One table says which held layouts each engine already ran on. The soft chain then runs on the ones it never saw. | how the lanes work together | 2e-4: 84 layouts at the 8.3% hit rate and 3e-5 a find | 2 boxE processes for 2.5 hours | no find in the first 40 passes | ran: 40 passes, no find. Dead by its kill line (section 3) |
| 2 | **Design census.** One number per two-arm layout, the end loss E, says what each held design would hold on every other n of its m. | the layouts two squares short, m 28 to 31 | none by itself: it names the design to build | seconds on one process | section 0 | ran: dead as a general predictor. One lead is left, the slide of 979 (section 4) |
| 3 | **A reader for the layouts the zone cut refuses.** The zone cut reads 35 of the 143 tilted layouts at m 28 to 31. A cut that takes sheared stacks and arms that stand off the wall gives the zone solver the other 108. | the layouts two squares short, m 28 to 31 | 0.0025: one chance in four of 0.010 (section 5) | one lane for two rounds | The new cut must rebuild 979 from its own modules to 1e-6. Dead when it reads fewer than 30 of the 83 refused arm layouts, or when the larger library certifies nothing in two rounds | not run as a tool. The split of section 9 reads the refused layouts with no cut: three of them hold the lowest corner of their pair, so the gain is smaller than this row says |
| 4 | **Plateau drop.** Where n and n + 1 hold nearly the same side, take one square out of n + 1. | the layouts two squares short, m 28 to 31 | 5e-4: one pair in six closes half of its gap of 1e-3 | 15 minutes of one process a pair | no end below held on 6 pairs | ran on 12 n: 5 of 37 starts slid, none ended below held. Dead by its kill line (section 6) |
| 5 | **Rounds in two phases.** The lanes that build new layouts end first. The lanes that only improve a layout (soft, polish, border, family steps) start after, from the certified takes of the first phase. | how the lanes work together | 3e-4 a round, one round sooner: the soft lane alone took 6e-5 to 6e-4 a round in rounds 11 to 16 | no cpu: the same lanes in another order | dead when, after two rounds, the followers certify no more on fresh layouts than on the held file | already in place for the soft and family lanes since round 16 (section 7). A part of it ran here: 4 passes, no find |

Idea 3 has the largest expected gain. It did not exist when the run started: it is what the census found. Idea 1 ran first because it had a certain price, a real positive control and no overlap with the six other lanes of this round.

**A correction on idea 5.** The row was written at 13:41 UTC. It said that the soft lane found only on layouts of the round before. The plan of round 16 says otherwise (section 7). So idea 5 is not new for the soft lane, and its expected gain is already in the rounds.

**Killed on paper, with the reason.**

- **Arms on opposite walls, and rings of four arms.** The two strips across one direction must add to the side. So their fractions add to f or to 1 + f. Each stack then pays its tilt, sin t of at least about 2 / (c + 1), on a smaller fraction. Both cases hold fewer squares than two arms on walls that meet.
- **One stacked arm with a shell step on the other wall.** The stacked arm binds the side as in the family step. The result is the family step's f with one square more to place. `family.md` section 1 already has that f.
- **Donors above n = 1000.** A chain back to 1000 and below goes through the same steps as our chains from inside. Or it loses a square on the way.
- **Tapered arms and fan corners.** A stack that changes c along the arm leaves a wedge at each change. The wedge is larger than the gain of the change at every f above 0.5.
- **A two-square drop.** Taking one square out of each arm of a two-arm layout frees about 0.1 of wall in each arm. Over 20 stacks that lets the tilt grow by 0.009 rad and f fall by about 0.024. Two squares are worth 0.034 on the normal slide, so the layout ends above the held side of its n.
- **Padded copies as the cause of the two squares.** A layout copied up one shell keeps f and k. It leaves 2 g of new wall unused, 0.33 squares a shell at f = 0.61. The line 631, 682, 735, 790 is such a copy and its E grows by 0.33 a shell. But only 20 of the 143 layouts at m 28 to 31 with f under 1 are copies of a smaller m. They hold 0.0086 of the 0.0513. The other 123 have their own f.

## 2. The ledger

`invent_ledger.py` reads three things. The first is the newest step of each held n (the `results/round*-best-*.tsv` tables). The second is how far that step moved its n (the gate details of the rounds). The third is every start of the soft lane in rounds 11 to 16 (`take-soft-r*/work/plan.json`). A layout "had a pass" when a soft start has the held score to 2e-9. The table is `results/round17-invent-ledger.tsv`, 209 held n from 335 to 999.

| Newest step of the held n | Layouts | Had a pass | Gap to the board | Gap on the layouts with no pass |
| --- | --- | --- | --- | --- |
| public file (harvest) | 66 | 4 | 0.0186 | 0.0177 |
| fq quench of a public file | 47 | 10 | 0.0124 | 0.0097 |
| family step | 33 | 33 | 0.0070 | 0 |
| readers | 26 | 26 | 0.0048 | 0 |
| modules | 17 | 9 | 0.0062 | 0.0023 |
| corners | 9 | 1 | 0.0028 | 0.0022 |
| border | 7 | 2 | 0.0035 | 0.0024 |
| soft | 4 | 1 | 0.0008 | 0.0007 |

The cause is one line of the soft lane, `KINDS = ('family', 'readers')` in `tools/softround/ctl.py`. A held layout whose newest step is a public file never starts. That rule was a choice of round 11 and no round measured it. 99 layouts with 0.0274 of gap had no pass. 62 of the 84 queued layouts come from the fault-dp files of one public author, jonathan1506, which gave about 0.0103 of score in round 13.

## 3. The sweep (idea 1)

**Set-up.** The workers on boxE ran the queue of 84 with the chain of the soft lane in its short mode. That is one island at 2e-4 with seed 11, one at 1e-4 with seed 12, then fq on a find. boxE is 1.45 times as fast per core as boxD (33,693 children against 23,300 in 140 s). So a leg is 100 s, the same number of children as the 140 s leg of the soft lane. The first pass (496) ran at 140 s.

**Control: green.** `802-rea15.csv` on boxE: the island at 2e-4 ran dry in 33,693 children. The island at 1e-4 found 3 times, 2.688e-5 of score. Then fq ended at 28.794880646, the side round 15 certified.

**Result: 40 full passes, no find. The idea is dead by its kill line.** The passes ran 2,042,723 children on 40 layouts and found nothing. 40 dry passes put the hit rate under 7.2% at 95%. The family and readers layouts hit at 8.3%. So the rule `KINDS` of the soft lane is right. A pass on a public layout, or on our fq quench of one, does not pay. The table is `results/round17-invent-sweep.tsv`.

**How it ran.** boxE has 18 cores and seven lanes ran on it. The load cap of 18 left this lane one process for most of the first hour, and 9 passes ran by 14:13 UTC. From 14:13 to 15:12 UTC that process ran the slide of section 6. The sweep ran again from 15:14 UTC, with two workers from 15:27 to 15:43 UTC and one after that. From 15:59 UTC that worker ran only under the load cap, and the kick scans of section 8 had the other process. The lane was cut twice, at 16:09 and at 17:52 UTC. The sweep stood at 33 passes at the first cut, and two workers ran the 7 last passes from 17:44 to 17:58 UTC. 7 of the 84 queued layouts got a file from another lane during the round and went to the end of the queue. 44 layouts did not run.

**The same layouts open under another engine.** In the same hours the midm lane gave public layouts a small kick before the fq quench ([midm](midm.md), section 5). A public file as published opened on 12 of 81 n. So the gap that the ledger showed is real. The engine that closes it is the kick, not the soft chain.

## 4. The census (idea 2)

`invent_census.py` reads 59 of the 146 held layouts in its table (m 28 to 31, side not whole) as two arms.

**Control 1: green.** Each design lands on its own n to 0.0.

**Control 2: red.** On 50 pairs of one class at neighbouring k, the prediction from one hits the other within 0.5 squares on 60%. The median error is 0.29 squares and the worst is 1.0.

**Kill line: dead by its second clause.** E is not a number of the class. In class (8, 8) it goes from -2.77 to 1.57 at m = 31, from -3.00 to 1.53 at m = 30 and from -2.66 to 0.87 at m = 28. It follows f: the far zones and the corner change with f, as `zones.md` says. The first clause is then empty. Some design predicts a side more than 0.3 squares below held on all 146 n. Each of those sides is also more than 0.005 below the board. A predictor that beats the board on every n says nothing.

**What I looked at after the kill line.** These are readings made after the data, so they are leads, not results.

- **The slide of 979 follows the board.** 979 (class (11, 9), E = 1.109, source the kmmmvs local bank) is the one wide layout near the board. With its own E held fixed, its design predicts these f at m = 31:

| n | k | held f | board f | 979's design | held is behind by |
| --- | --- | --- | --- | --- | --- |
| 969 | 8 | 0.6340 | 0.6056 | 0.5980 | 2.07 squares |
| 970 | 9 | 0.6390 | 0.6292 | 0.6153 | 1.37 |
| 971 | 10 | 0.6612 | 0.6368 | 0.6325 | 1.66 |
| 972 | 11 | 0.6772 | 0.6514 | 0.6497 | 1.61 |
| 973 | 12 | 0.6966 | 0.6666 | 0.6667 | 1.76 |
| 974 | 13 | 0.7034 | 0.6884 | 0.6836 | 1.17 |
| 975 | 14 | 0.7210 | 0.7016 | 0.7005 | 1.22 |
| 976 | 15 | 0.7340 | 0.7218 | 0.7172 | 1.01 |
| 977 | 16 | 0.7456 | 0.7343 | 0.7338 | 0.72 |
| 978 | 17 | 0.7599 | 0.7489 | 0.7502 | 0.59 |
| 979 | 18 | 0.7665 | 0.7636 | 0.7665 | 0 |
| 980 | 19 | 0.7841 | 0.7705 | 0.7827 | 0.09 |
| 981 | 20 | 0.7950 | 0.7810 | 0.7988 | -0.23 |

  From k = 10 to 17 the prediction is within 0.005 of the board on all 8 n, and within 0.002 on 5 of them. No number was fitted: E is 979's own. The two curves are smooth, so this is an agreement of one slope and one offset, not of 8 free numbers. The offset is the part that counts: it agrees to 0.3 squares, and held is 0.6 to 1.8 squares behind. The reading: the board at m = 31, k = 10 to 17, holds what the (11, 9) design of 979 holds. The gap on those 8 n is 0.0048 of score.
- **The same class fits the board at m = 28 to 30.** Take class (10, 9) with E = 1.109 and board f from 0.60 to 0.77. Its mean residual to the board is within 0.06 squares at each m of 28 to 31. Class (8, 8) with the E of our best layouts is 0.94 to 1.19 squares behind there.
- **The other reading is still open.** The board's sides also fit 8-arms with E near 0.1 at every m from 20 to 31. Our own 8-arm layouts at f 0.60 to 0.77 have `E = 0.15 + 0.197 (m - 25)` over 13 layouts. Part of that slope is padded copies (section 1). The census cannot tell the two readings apart: only a built layout can.

**The takes of rounds 16 and 17 against this lead (15:33 UTC).** `invent_now.py` takes 44 n: m = 28 to 31, board f from 0.60 to 0.77. For each n it gives four values of f: held, the best take of round 16 or 17, the board, and the design of 979. The design is class (11, 9) at m = 31 and (10, 9) at m = 28 to 30, with E = 1.109. The table is `results/round17-invent-now-m28-31.tsv`.

| m | n | Held behind the board (squares, mean) | Best take behind the board | Design of 979 minus the board (mean, and mean of the absolute values) | Gap of the best take |
| --- | --- | --- | --- | --- | --- |
| 28 | 10 | 0.70 | 0.68 | +0.06 (0.24) | 0.0046 |
| 29 | 11 | 0.70 | 0.68 | -0.03 (0.31) | 0.0046 |
| 30 | 12 | 0.99 | 0.91 | +0.02 (0.31) | 0.0062 |
| 31 | 11 | 1.02 | 0.87 | -0.18 (0.23) | 0.0052 |

17 of the 44 n have a smaller take since round 15, 11 of them from the twoshort lane. The gap on the 44 fell from 0.0224 to 0.0207. The board is still 0.7 to 0.9 squares ahead, and the design of 979 is at the board within 0.31 squares at every m.

**What the design of 979 is.** `results/round17-invent-979-map.txt` is a map of the held 979, one character for each unit cell (`invent_map.py`). The reading:

- The arm of 9 has 118 squares at 21 degrees. It is on the left wall from y = 12.5 to 30, in a strip 8.77 wide.
- The arm of 11 has 192 squares at 18 degrees. It is on the bottom wall from x = 10 to 31, in a strip 10.77 high. From x = 12 to 22 its stacks stand one unit above the wall, on a row of plain squares.
- A plain block of about 10 by 12 squares fills the bottom left corner, flush on both walls. Its top and right edges are staircases: it is 12 or 13 squares high and 10 to 12 wide. So the two arms never meet: each arm ends at an edge of that block and at a far wall.
- The other 462 plain squares are one block, flush in the top right corner.

Our two-arm layouts put a corner zone where the two strips cross. This design has no corner zone. It has four arm ends. Each end is against a wall or against a staircase of plain squares, and never against the other arm.

## 5. What the zone cut reads at m 28 to 31

This came out of the census and is the base of idea 3. `results/round17-invent-readable-m28-31.tsv` has one row for each of the 217 held layouts: the main tilt, the kind, the answer of `modules.cut` at tolerances 3e-3 and 1e-2, and the gap.

| Kind (by the main tilt) | Layouts | Gap | Read by the zone cut | Gap on the read ones |
| --- | --- | --- | --- | --- |
| no tilted square (side is whole) | 74 | 0.0003 | 0 | 0 |
| arms, tilt under 33 degrees | 118 | 0.0421 | 35 | 0.0094 |
| fault line, 33 to 44 degrees | 9 | 0.0011 | 0 | 0 |
| 45-degree block | 16 | 0.0078 | 0 | 0 |

- **83 arm layouts with 0.0327 of gap are refused.** That is 64% of the gap at m 28 to 31. The refusal is "no two flush arms" on 177 of 182 layouts, at every tolerance from 3e-3 to 6e-2. The cut needs three stacks of one size on each of two walls, each stack whole from wall to strip edge and within 0.05 of the wall.
- **By f.** From f = 0.6 to 0.9 the cut reads 11 arm layouts (gap 0.0058) and refuses 72 (gap 0.0296). From 0.9 up it reads 24 and refuses 10.
- **What the refused ones are.** In 979 and 976 to 981 the stacks are sheared: the chain finder breaks them into runs of 4, 7, 8 and 11. The two arms of 979 also do not meet in a corner zone. The arm of 9 is on the left wall from y = 12 up. The arm of 11 is on the bottom wall from x = 10 on. A plain block of about 10 by 12 squares fills the corner between them. In 790 the stacks stand off the wall, in a block of 170 tilted squares that does not grow with m. In 791, 908 and 910 the runs are short and of many sizes. The library of round 16 (`lib16b`, 306 layouts, 9,044 modules) has no module from 979.
- **The gain of idea 3.** A refused arm layout has 3.9e-4 of gap and a read one 2.7e-4. If the zone solver brings the 83 down to the read level, that is 83 x 1.2e-4 = 0.010. I put the chance at one in four, because nobody knows that the refused layouts cut into the same zones.

## 6. The plateau drop (idea 4)

**Version 1, the quench scan: dead.** `invent_drop.py` ran on the pair (791, 792). It took one tilted square out of the held 792, for the 12 tilted squares nearest each corner. It quenched each start with fq. All 48 ends are at or above the side of 792. The best is 28.637030, the side of 792 is 28.637029 and the held 791 is 28.634071. The pass on the best end ran dry in 44,489 children.

**The tool control: red, and it explains version 1.** The control ran on the pair (978, 979). The fq quench of the held 978 with no square removed ended at 31.759864943, which is 1.39e-5 above its side of 31.759851005. The format is right, but the default quench loosens the layout by 2% and does not find the way back on a sheared layout. On 979 with one square removed it ended 1.5e-3 above its start. So the scan of version 1 could not see a slide. I stopped it.

**Version 2, the plain start: the slide opens.** `invent_slide.py` writes the held n + 1 with one arm-end square removed and leaves the start alone. The soft search runs on it first, and fq runs only after a find. On 979 with square 117 removed (the last square of the arm of 9, on the side of the other arm, tilt -32.8 degrees):

| Step | Side of the 978 squares |
| --- | --- |
| start (the side of 979) | 31.766536608 |
| soft island at 2e-4, 100 s, 2 finds in 2,704 children | 31.763411407 |
| soft island at 1e-4, 100 s, 2 finds in 4 children | 31.762628662 |
| fq quench, 6 s | 31.760578450 |
| fq with the polish flags | 31.760576641 |
| held 978 | 31.759851005 |

The layout slid by 0.00596. The step down to the held 978 is 0.00669, so it ends 7.3e-4 above held and does not certify. An island at 4e-4 from the end ran dry in 23,609 children. The same start with the last square of the arm of 11 removed (377) was dry in 31,078 children.

**What the slide says.** One square pays 0.0060 of side here. The census model with E fixed says 0.0165. So this cheap slide keeps the arms and loses 0.64 squares of end zone a step. It can win only where the held step from n + 1 down to n is under about 0.006. 32 held n from 300 up have a step under 0.0075 and a gap of more than 1.5e-4 to the board. Their gap adds to 0.0152.

**The screens.** A screen is one start: the 100 s island at 2e-4, then fq on a find. The starts are the last tilted square at each end of each arm of the held n + 1. Seven pairs with wide sheared arms got the odd-tilt squares nearest the arm ends (tag w). A slide is the fall of the side from the start. The step is how far the start is above the held n. The run made 37 starts on 12 n. 5 starts slid, on 3 n. None ended below held. Each start is one row of `results/round17-invent-slides.tsv`.

| n | Starts | With a slide | Best slide | Step down to held | End minus held |
| --- | --- | --- | --- | --- | --- |
| 591 | 4 | 0 | 0.00000 | 0.00000 | +0.00000 |
| 736 | 7 | 0 | 0.00000 | 0.00186 | +0.00186 |
| 754 | 2 | 0 | 0.00000 | 0.00479 | +0.00479 |
| 791 | 1 | 0 | 0.00000 | 0.00296 | +0.00296 |
| 800 | 2 | 0 | 0.00000 | 0.00476 | +0.00476 |
| 805 | 2 | 0 | 0.00000 | 0.00548 | +0.00548 |
| 812 | 6 | 1 | 0.00314 | 0.00548 | +0.00234 |
| 866 | 2 | 0 | 0.00000 | 0.00452 | +0.00452 |
| 927 | 2 | 0 | 0.00000 | 0.00500 | +0.00500 |
| 977 | 2 | 1 | 0.00574 | 0.01496 | +0.00922 |
| 978 | 6 | 3 | 0.00596 | 0.00669 | +0.00073 |
| 982 | 1 | 0 | 0.00000 | 0.00579 | +0.00579 |

**Reading.** One removed square frees one arm, and the slide stops when the other arm binds.

- Both ends of the arm of 9 in 979 slid to the same side, 31.760577. So the stop is not in that arm. Six more islands from the two ends, with two seeds and two box steps, ran dry in 101,967 children.
- The second square confirms it. The stalled 978 with the inner end square of the arm of 11 removed slid by 0.0057, to 31.754836. That is 977 squares, and the held 977 is 31.745619, so it ends 0.0092 above held.
- 812 is the one other n that slid. The held 813 with an odd-tilt square at the bottom wall removed fell by 0.0031 of the 0.0055 it needed. A second pass from its end ran dry in 36,743 children.
- A square pays about 0.006 of side in this design. The held steps from 979 down are 0.007, 0.014 and 0.012. So the chain of single squares falls behind held after the first step.
- 591 has a step of zero: the held 591 is the held 592 with one square less. Its four starts say only that the search does not move that layout.
- The twoshort lane certified 978 at 31.75946 in this round, by its own build. So the 978 of the slide is behind that too.

**Kill line: dead.** 12 n ran and none ended below held. Version 2 changed the tool, not the kill line. The 59 screens that were still in the queue did not run.

## 7. The follow within the round (a part of idea 5)

**Control: green.** `700-mod16.csv` on boxE: the island at 2e-4 found 3 times, 5.956e-5 of score. The island at 1e-4 found 4 times, 2.461e-5. Together that is 8.42e-5 of the 9.15e-5 that the chain of round 16 took from this start. The fq polish of the control held one worker for 6 minutes, so it was stopped by hand: the control was already green.

**Result: 4 of 14 passes, no find, stopped before its kill line.** The files were the twoshort 912, 976, 973 and 911. They have the largest gain on held. The passes ran 140,738 children and found nothing. Zero of 4 says little: it puts the hit rate under 53% at 95%.

**Why it stopped.** The soft lane of round 17 started at about 15:15 UTC. Its plan lists the same 14 files and 6 files of the midm lane, with the full chain on three boxes. The family lane of round 17 walks the twoshort layouts one shell up and down too. A second copy of the same search on the same files buys nothing. The other 10 starts left the queue at 15:27 UTC and the two workers went back to the sweep.

**What it says about idea 5.** The plan of the soft lane of round 16 (`take-soft-r16/work/plan.json`) has 45 starts. 35 of them are files that another lane certified in the same round, and its two finds (596 and 700) came from such files. So the soft lane already works in two phases inside a round, and the family lane does the same. Nobody measured it for the polish and border lanes.

## 8. The kick on the layouts no kick touched

**Control: red at seed 1, green at seed 2.** The held 374 at seed 1 made 33 tries in 76 s, and none was below held. The scan of the midm lane at seed 1 was dry too: its find came at seed 2. The same scan at seed 2 found 4 times in 30 tries. It ended at 19.826147190, the side of the midm find, 7.251e-5 of score below held. So the tool is right, and one seed of 75 s sees this opening one time in two.

**What changed after the control.** A try costs 2.3 s at n = 374 and 25 s at n = 979. The first scan of 979, 75 s at seed 1, made 3 tries. So 979 got one scan of 300 s at seed 2.

**Result on 979: 17 tries in 355 s, none below held.** The best try came back 9.1e-07 of side above held: the kick does not move this layout.

**Result on the first list: 25 scans, 452 tries, one certified find.** Three scans (456, 582 and 499) ran at 15:59 UTC, before the first cut. By 18:07 UTC the midm lane had scanned or queued all but 23 of the other n, and the border lane held one of those, 919. Two loops then ran the 22 n that no lane had kicked. A scan was 75 s up to n = 660 and 150 to 180 s above. boxE was at a load of 50 to 70 on 18 cores, so a scan made 3 to 23 tries.

- **464 opened.** Its scan was the 17th of the list. It found twice in 9 tries and took the side from 21.982157262 to 21.982077364, 3.709e-06 of score. The held 464 is our fq polish of 2026-11-10 of the seed layout.
- **The relay.** One fq quench of the certified file gave nothing. Then kick legs of 150 s ran from the newest find, as `tools/midm/relay.py` does. 1 of 2 legs found, in 36 tries, for 9.990e-06 more. The side is now 21.981862174, and the take holds 464 at 1.370e-05 of score below held.
- **The two other modes.** One leg of 328 s ran the large kick and the melt of the same tool from the certified file. It made 29 tries, and the best one ended 1.2e-03 of side above the file. So 464 stops here.
- **The certificate.** 464 certified against the round 16 file with floatsafe at 2.2e-11. No take dir of round 17 holds a 464.
- **The other scans.** 12 scans ended below held by about 5e-11 of score, which is under the bar of the take. Those layouts come back to their own side: 456 did so on 78 of its 81 tries.
- **The kill line.** The list is not dead: it has 1 find in its first 20 scans. The hit rate is 1 in 25. The midm lane had 13 in 119 on public files as published.

**A second scan of the short scans: 9 scans, 174 tries, finds on none.** 9 n of the list had fewer than 14 tries in their first scan. Each got 150 s more at seed 2.

**A third list: 20 scans, 640 tries, finds on none.** It came from a count at 18:50 UTC. 104 n with a gap to the board had no scan file of any lane on boxE. 60 of them are rigid layouts at 45 degrees, the slice of the rigidsoft lane. The 44 others have tilted squares, and 20 of those hold a claim of the midm lane.

- **13 layouts that are on no list.** 15 of the 44 are not on the list of 85. 13 of them got one scan at seed 1: 199, 232, 450, 451, 494, 536, 537, 540, 583, 584, 847, 850, 907. The 2 others, 204 and 737, have a board gap under 2e-5. No round table and no polish table names them, so they are the seed layouts as published.
- **7 layouts that the midm lane had queued.** 9 of the 44 are on the list of 85. They sit in a queue file of the midm lane, with no claim and no scan file at 18:58 UTC. 919 is in two takes. Of the 8 others, 7 got one scan at seed 1: 445, 455, 488, 681, 734, 798, 967. The midm lane scanned 997 first, so this lane left it out.
- **The result.** 18 of the 20 scans ended below held by about 5e-11 of score, under the bar of the take. None certified.

**Result of the second seed: 19 scans, 489 tries, no find. The idea is dead by its kill line.** These are public layouts whose one scan of the midm lane was dry. 6 of the scans ended below held by less than 1e-10 of score. Each scan is one row of `results/round17-invent-kick.tsv`.

## 9. Where the end loss is

`invent_parts.py` splits the end loss E of a two-arm layout over its parts. It asks for no stack and no cut, so it also reads the layouts that the zone cut refuses.

- It turns the layout so that the arms are on the left and bottom walls, and takes each arm size from the main tilt on its wall.
- It cuts each arm near the middle of its wall, along a line between two stacks. The far end of an arm is what a flush arm would hold beyond the cut, less what the layout holds there.
- The corner is all the rest of E. The numbers are in the frame of `modules.k_flush` with the narrower arm first: `k_flush - k = corner + far end 1 + far end 2`.

**Controls: green.** The parts add to E within 4.3e-14 on all 199 layouts that the tool reads, of the 560 n from 441 up. The lowest corner of two 8-arms is 2.50 squares (740, f = 0.707), and the library's lowest below f = 0.8 is 2.47. The median far ends are 2.85, 3.27 and 4.27 squares for arms of 8, 9 and 11. The far zone table of the [twoshort](twoshort.md) avenue has 2.50 to 2.85, 2.91 to 3.26 and 4.23 to 4.47.

**A filter.** 77 of the 199 rows have both far ends between 0.5 and 6 squares, arms of 6 or more and f from 0.55 to 0.90. The other rows are layouts that the tilt alone reads wrong. The table below uses the 77. Every row is in `results/round17-invent-parts.tsv`.

| Pair of arms | Layouts | Lowest corner (n) | Median corner | Median of the two far ends |
| --- | --- | --- | --- | --- |
| 7 and 7 | 8 | 1.35 (922) | 2.16 | 4.73 |
| 8 and 8 | 12 | 2.50 (740) | 3.06 | 5.70 |
| 8 and 11 | 4 | 3.12 (687) | 3.34 | 7.01 |
| 9 and 9 | 21 | 3.52 (793) | 3.81 | 6.54 |
| 9 and 11 | 1 | 4.13 (979) | 4.13 | 7.53 |

- **The far ends are the larger loss.** In every pair the two far ends cost 1.7 to 2.2 times the corner.
- **A far end costs the same in every design.** The far ends of 979 cost 3.27 squares (arm of 9) and 4.26 (arm of 11). Those are the medians of our own layouts and the public ones. So 979 is not ahead at its far walls.
- **The near ends of 979.** Its arm of 9 starts on the block at y = 12, and its arm of 11 at x = 10. Against a flush arm from there, the near ends lose 2.98 and 3.33 squares. So an arm end on the block costs 0.3 to 0.9 squares less than the same arm's end at a wall. The block is one row and one column larger than the smallest block that fits, which costs 0.41 and 0.46 squares of arm.
- **The block as a corner.** In the frame of the library, the block and the two near ends are one corner of 9 and 11. It loses 4.13 squares. The twoshort avenue had no corner for that pair and used its line, 4.70. With 4.13 its best margin for 9 and 11 goes from -0.20 to +0.37 squares (914), and its median from -1.00 to -0.43.
- **A count of the block corner.** Take a plain block of c1 by c2 squares in the corner, less the one square that meets the plain grid. Arm 1 starts on its top edge and arm 2 on its right edge. With near-end losses v1 and v2 the corner loses `v1 + v2 + r1 c2 + r2 (1 - f) - c1 c2 + 1` squares. Here `r = c - 1 + g` is what a flush arm holds per unit of wall. A larger block loses one square for each cell of the plain grid that it meets.
- **The control of the count is 979.** Its block is 10 by 12. The rule gives 4 lost squares where it meets the plain grid, and the layout has 4: 2 of the block and 2 of the grid. With them the count gives 4.14, and the split measured 4.13. The near-end losses in the count are 979's own. So the control tests the frame and the rule of the lost squares, not the near ends.
- **What the count says.** These are block corners at f = 0.7665. Arms of 9 and 11 lose 4.0 to 4.5 squares. Two 11-arms lose 5.0 to 6.0, and two 9-arms 4.2 to 4.4. Our staircase corners of two 9-arms lose 3.8 to 4.7 at f = 0.74 to 0.81 (860, 921, 977, 978). The staircase corner of two 11-arms loses 5.37 at f = 0.68. So the block corner is within 0.5 squares of the staircase corner. It is cheaper only where an arm of 11 ends on it.
- **What the refused layouts would add (idea 3).** At m 28 to 31 three refused layouts hold the lowest corner of their pair. 922 holds 1.35 for 7 and 7, against 1.83 on the next layout. 920 holds 2.44 for 7 and 9, against 2.86 on the first layout that is not refused. 979 is the only layout of 9 and 11. A reader for the refused layouts would add these three corners, 0.4 to 0.6 squares on three pairs. That is less than section 1 gave idea 3.

**Reading.** This answers point 3 of the first Next list. The ends of 979 on the block are tapers like its far ends, and a little cheaper. The design of 979 is not a new kind of zone. Its lead over our layouts is a corner that is 0.6 squares under the line, on one pair. The board is 0.3 to 0.8 squares ahead of our best takes at m = 31, k = 13 to 17. No part of 979 holds that much.

## 10. The monotone check

`invent_mono.py` ran at 18:17 UTC and at 19:33 UTC, over the round 16 file and the 18 take dirs of round 17. It found 0 n whose best side is above the best side of a larger n, for j up to 4. So no lane's new layout gives a neighbour below it for free. The check costs seconds. It belongs before each assembly, because each lane looks only at its own n.

## 11. Which kick try pays

**Result: six tries tell whether a scan can find. Take the scans where 3 or more of the first 6 tries came back to the start side. Their later tries took 21% of the seconds and gave 3.6% of the gain. A scan that found keeps finding at 6 times the first rate. The gain sits in a few steps, and 11 of the 15 largest came from the large full kick.**

`invent_kickrows.py` read 602 complete scan tables of `midm_scan.py` at 19:17 UTC. They are the tables of the midm lane on boxE, less its controls, and the 80 of this lane. Two tables were second copies of the same n, seed and start, and are left out. The pool holds 15,692 tries and 59,407 s of fq time. 123 tries stepped down by more than 1e-10 of score, in 81 scans. The steps add to 4.396e-04. The table of every cell is [`results/round17-invent-kickrows.tsv`](../results/round17-invent-kickrows.tsv).

| Start of the scan | Scans | n | Tries | Seconds | Scans with a find |
| --- | --- | --- | --- | --- | --- |
| a held layout | 503 | 457 | 14,052 | 42,284 | 49 (10%) |
| a new file of a lane in this round | 50 | 41 | 749 | 8,707 | 13 (26%) |
| a leg from a find | 49 | 31 | 891 | 8,416 | 19 (39%) |

**Control: green one way, red the other.** By finds per 1,000 s, the local kick with fq's default flags (`lkick d`) is first on the odd n, at 3.93. It is second on the even n, at 3.09. The pooled rate is 2.07. The other way fails. The first cell on the even n is the local kick with the flag set K, at 3.26, and it is last on the odd n, at 0.92. So the order of the cells is noise below `lkick d`. The rules further down do not use the cells, and each has its own split in two halves.

**The flag sets do not predict.** `lkick d` is at 2.1 times the pooled rate on the odd n and at 1.4 times on the even n. No cell of mode and flag set is at twice the pooled rate in both halves. One cell is slow in both. The full kick with the default flags (`kick d`) finds 1.18 and 1.05 times per 1,000 s, half the pooled rate, and takes 21% of the seconds. It also holds two of the five largest steps, so it stays.

**One kick size finds often, and its steps are small.** It is the local kick of radius 1.2 at sigma 0.06. It found 17 times in 1,923 s, 8.8 per 1,000 s. That is 12.6 on the odd n and 5.2 on the even n, more than twice the pooled rate in both. Its 17 steps add to 1.07e-05. That is 5.6e-06 per 1,000 s, under the pooled 7.4e-06. The full kick at sigma 0.04 is the other end. It found 8 times in 12,371 s, 0.65 per 1,000 s, and its steps add to 2.04e-04. It holds 5 of the 10 largest steps.

**The gain sits in a few steps.** The median step is 2.1e-07. The 5 largest of the 123 steps hold 62% of the gain, and the 15 largest hold 82%. 37 steps are 1e-06 or more. 21 come from the full kick, 0.60 per 1,000 s, and 16 from the local kick, 0.66 per 1,000 s. So no mode, flag set or kick size can be dropped for gain.

**The large steps come from the large full kick.** The 15 largest steps hold 82% of the gain. 11 of them, on 8 n, came from the full kick at sigma 0.02 or 0.04. Those tries took 36% of the seconds. That is 0.52 large steps per 1,000 s, against 0.10 for every other try. The two halves agree in sign: 0.19 against 0.10 on the odd n, on 2 steps each, and 0.83 against 0.11 on the even n. Every one of the 8 finds at sigma 0.04 is a step of 1e-06 or more. That size gives 1.65e-05 of score per 1,000 s, 2.2 times the pooled rate in both halves. Without its largest step it gives 9.4e-06, and the pool without its largest step gives 5.9e-06. The evidence is 8 finds on 21% of the seconds. It is a lead, not a result.

**Where the seconds pay.**

| Phase of a scan | Tries | Seconds | Finds | n with a find | Gain | Finds per 1,000 s | Gain per 1,000 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| held layout, tries 1 to 10, no find yet | 4,268 | 25,361 | 44 | 43 | 9.62e-05 | 1.73 | 3.8e-06 |
| held layout, after 10 dry tries | 9,326 | 14,068 | 5 | 5 | 1.02e-04 | 0.36 | 7.2e-06 |
| held layout, after a find of the same scan | 458 | 2,855 | 31 | 18 | 1.10e-04 | 10.86 | 3.9e-05 |
| new file, tries 1 to 10, no find yet | 340 | 5,361 | 13 | 11 | 8.11e-05 | 2.43 | 1.5e-05 |
| new file, after 10 dry tries | 314 | 2,071 | 0 | 0 | 0 | 0 | 0 |
| new file, after a find of the same scan | 95 | 1,276 | 4 | 2 | 7.1e-07 | 3.14 | 5.6e-07 |
| a leg from a find | 891 | 8,416 | 26 | 14 | 4.96e-05 | 3.09 | 5.9e-06 |

- **The first find comes early.** In the 81 scans with a find, the first find is at try 3 in the median. 80% have it by try 7 and 95% by try 12. In fq time that is 38 s, 82 s and 131 s.
- **After 10 dry tries a scan finds at a fifth of the first rate.** 390 scans passed 10 tries with no find. 7 of them found later, 1.8%. Their tries after the tenth are 10,092 of the 15,692 in the pool. On the held layouts that phase took 14,068 s, a third of the seconds, for 5 finds.
- **One of those 5 is the largest step of the pool.** 986 stepped by 8.749e-05 at try 17, after 16 dry tries. It is 86% of the gain of that phase. Without it the phase gives 1.0e-06 per 1,000 s. So by the count of finds, the tries after 10 dry ones are the worst seconds of a scan. By gain the pool cannot tell, because one step decides it. The new files show the same: one step on 647 is 84% of their gain.
- **A scan that found keeps finding.** After a find on a held layout, the tries of the same scan find 10.9 times per 1,000 s. That is 6 times the first rate and 10 times the gain per second. 31 finds on 18 n hold that.
- **The clock ends the scans that find.** 63 of the 81 scans with a find ended fewer than 10 dry tries after their last find. 46 ended fewer than 5 after it. The 63 are on 47 n.
- **A leg from a find pays less than the same scan.** The legs find 3.1 times per 1,000 s and give 5.9e-06 per 1,000 s. By gain that is 1.6 times the first tries on a held layout, and a seventh of the tries that follow a find inside a scan. The tries after a find on a held layout and the legs together find 5.1 times per 1,000 s and give 1.4e-05. That is 2.9 times the first tries by count and 3.7 times by gain.
- **The legs are already run.** `mkrelay.sh` of the midm lane queues a leg after each find of 3e-8 of score or more. At 19:22 UTC, 56 n had a find. On 17 of them the newest scan ended fewer than 10 tries after its last find. 13 of those finds are under 3e-8. Of the 4 others, the midm lane holds 374 and runs legs on 986, and a take of the readers lane is below 921. The one left is 875, a find of 2.1e-07 with no leg.
- **The first 6 tries split the scans.** Take the scans with a find in their first 6 tries. Their later tries find 6.5 times per 1,000 s: 19 finds in 2,934 s on 43 scans. With no find in the first 6, they find 0.92 times: 25 finds in 27,188 s on 458 scans. The factor is 7. The scans where 3 or more of the 6 tries came back to the start side find least. They find 0.48 times per 1,000 s, on 258 scans.

**A stop rule that keeps the gain.** A try comes back when it ends within 5e-09 of the start side. The kick and the quench then found the same layout again. 517 scans have 6 tries or more. In 258 of them, 3 or more of the first 6 tries came back. Those 258 hold 5 of the 65 scans with a find. Their tries after the sixth took 12,508 s, 21% of the seconds of the pool. They gave 6 finds and 1.59e-05 of score. The 259 other scans gave 38 finds and 3.03e-04 in 17,615 s after the sixth try. That is 0.48 against 2.16 finds per 1,000 s, and 1.3e-06 against 1.7e-05 of score per 1,000 s. The halves agree. On the odd n the scans that came back gave nothing in 6,241 s. On the even n they gave a tenth of the gain rate of the others. The rule keeps 986, where no try came back. A second scan at another seed helps neither group. After a dry first scan it found on 0 of 14 n where the tries came back, and on 1 of 26 where they did not. [`results/round17-invent-kickrows-scans.tsv`](../results/round17-invent-kickrows-scans.tsv) has one row for each scan, with its count of tries that came back. Of the first scans, 219 have fewer than 3 and 44 of them found. 254 have 3 or more and 4 of them found. The split holds on the new files of the round. There 9 of 24 scans found where fewer than 3 tries came back, and 0 of 12 where 3 or more did.

**The same count splits the gap to the board.** 415 n have a first scan of 6 tries or more. On 185 of them fewer than 3 tries came back. Those n hold 0.0442 of gap to the board, by the held file and the takes of 19:34 UTC. [`results/round17-invent-bigkick-list.tsv`](../results/round17-invent-bigkick-list.tsv) ranks them by that gap. On the 230 other n, 3 or more tries came back. They hold 0.0273 of gap, on 95 n. A kick does not move those layouts, so that part of the gap needs another design. [`results/round17-invent-kick-rigid-list.tsv`](../results/round17-invent-kick-rigid-list.tsv) lists the 95, and its 20 largest hold 0.0128. The whole gap to the board is 0.1102 at that time. The n with no first scan of 6 tries hold the other 0.0387.

**Kill line: not met.** The first clause holds for the flag sets and fails for one kick size. The second clause fails twice. A find in the first 6 tries splits the find rate by a factor of 7, with 19 finds in the better group. The count of tries that came back splits it by 4.5, with 38 finds in the better group, and splits the gain rate by 13. So the pooled table predicts the count of finds. For the gain it leaves one lead, the large full kick.

**What it changes.** The midm lane already kicks every held layout and every new file of a lane, and it runs a leg after each find. The table backs that order of work with rates. It adds one rule: end a scan after 6 tries when 3 or more of them came back to the start side. On this pool the rule frees 21% of the seconds. It gives up 6 of the 123 finds and 1.59e-05 of the 4.40e-04 of gain. A stop after 10 dry tries frees more, a third of the seconds on held layouts. But it gives up a third of the gain there, 1.02e-04 of 3.08e-04, through 986. Nothing ran with a stop rule yet: every number here is from scans of fixed length.

## 12. Next

1. **Block corners for pairs with an arm of 11.** The count of section 9 puts them up to 0.7 squares under the staircase corner. Build the block with far zones of the library, turned by a half turn, as near ends. The control is the count of 979's own block, 4.14 against 4.13. The kill line: dead when `zone_corner.loss_of` of the settled corner is not 0.3 squares under the staircase corner of the same pair and f.
2. **The far end is the place to look.** Two far ends cost 4.7 to 7.5 squares. Every design that we read pays the same for its arm size. All of them are tapers. A far end of another kind is the open question. Section 9 gives the bar: 2.85, 3.27 and 4.27 squares for arms of 8, 9 and 11.
3. **Test two changes to the kick scan (section 11).** The first is a stop after 6 tries. It applies when 3 or more of them came back to the start side. On the pool it frees 21% of the seconds for 3.6% of the gain, and both halves agree. Give the freed seconds to the scans where fewer tries came back, and to the new files of the round. Those scans gave 1.7e-05 per 1,000 s after the sixth try. The control runs on 10 n of this round with a find. There the scan with the stop, at the same seed, must reach the side of the fixed scan. The kill line: one list of 100 n, split by odd and even n. Dead when the half with the stop certifies no more n per 1,000 s than the half with scans of 150 s. The second test is a larger share of the full kick at sigma 0.04, which gave 2.2 times the pooled gain per second on 8 finds. `invent_bigkick.py --kicks 0.04 --modes kick` runs that size only. Its kill line needs 20,000 s on each half of one list. Dead when the half at sigma 0.04 has no more steps of 5e-06 or more than the standard half. The list for both tests is `results/round17-invent-bigkick-list.tsv`. Also run one leg on 875. The first scans need no other lane now. The loop of the midm lane scans every n to 1000 at seed 1, and every new file of a lane.
4. **A reader for the layouts the zone cut refuses (idea 3)** is worth three corners (section 9). It comes after points 1 and 2.
5. **Run the monotone check before each assembly** (section 10). It found nothing at 18:17, 18:41, 19:12 and 19:33 UTC.
6. **Do not run these again.** The soft chain on public held layouts: 40 passes, no find. A second kick seed where one scan was dry: 19 scans, no find. A leg of the large kick and the melt on a find: 29 tries on 464, none below. The single-square slide: 37 starts on 12 n, none below held. The fq quench of a held n + 1 less one square: 48 ends, none below. A generator that slides 979: the design pays 0.0165 of side for a square and a slide pays 0.0060.
7. **The soft lane keeps its rule.** `KINDS` stays as it is. It already follows the take dirs of its own round, so the rounds need no second phase for it.

## 13. Files

- Tools, all new files of this avenue: `invent_ledger.py` (the ledger), `invent_census.py` (the census) and `invent_readable.py` (the table of section 5). `invent_drop.py` is the quench scan, version 1, and `invent_slide.py` writes the plain starts, version 2. `invent_map.py` and `invent_now.py` give the map and the second table of section 4. The kick scans use `midm_scan.py` of the midm avenue. `invent_parts.py` is the split of section 9 and `invent_mono.py` the check of section 10.
- Tables: `results/round17-invent-ledger.tsv`, `results/round17-invent-sweep.tsv` (the passes of sections 3 and 7 and the two controls), `results/round17-invent-979-slide.tsv`, `results/round17-invent-readable-m28-31.tsv`, `results/round17-invent-slides.tsv`, `results/round17-invent-now-m28-31.tsv` (the second table of section 4) and `results/round17-invent-979-map.txt`.
- Tables of the last attempt: `results/round17-invent-kick.tsv` (the scans of section 8) and `results/round17-invent-parts.tsv` (the split of section 9).
- The pooled kick tries of section 11: `invent_kickrows.py`, `results/round17-invent-kickrows.tsv` (one row for each cell) and `results/round17-invent-kickrows-scans.tsv` (one row for each scan). It reads the scan tables as text, copied to `work/scans/` and `work/boxE/run/`.
- `invent_bigkick.py` runs a kick scan with chosen kick sizes, for the second test of point 3 of the Next list. It had one check of 2 tries and no search yet. `results/round17-invent-bigkick-list.tsv` is its list: the 185 n where fewer than 3 of the first 6 tries came back, by gap to the board. `results/round17-invent-kick-rigid-list.tsv` is the other side: the 95 n where 3 or more came back and the board is ahead.
- Take dir: `<scratch>/bounties-squares/take-invent-r17` (`take.tsv`, `464.csv`, `STATE.txt` with the log of the last attempt, and `work/` with the starts, the queue and the logs of boxE run).

## 14. Round 19 (2026-11-12, 20:15 to 22:40 UTC)

**Result: one n certified, 969, for 4.628e-04 of score against the round 17 file. That is 5.277e-05 below every other take. It is two 9-arms on a block corner, a new corner that this round built. The block corner is under the staircase corner at low f only. It is rigid, so it gives a row on few n.**

"The bar" of an n is the lower of the round 17 file (`gate/cand-round17-1112a`) and every take dir of rounds 17 and 19. A result counts when it certifies below the bar.

### 14.1 Kill line and controls (from section 12, before the first run)

**The idea.** Point 1 of section 12. A plain block stands in the corner, and each arm ends on an edge of the block. The two arms never meet, as in the held 979.

**Kill line.** We compare `zone_corner.loss_of` of the settled block corner with the staircase corner of the same pair and f. The pair is dead at that f when the block is not 0.3 squares under the staircase.

**The bar of the kill line.** The staircase corner comes from `twoshort_corner.py stair` with the options of its second pass and 540 s. Where this round had no run, the bar is the number of the [twoshort](twoshort.md) avenue.

**Control 1, the count.** The count of section 9 must give the corner of 979 from 979's own near ends. `invent_block.py count 9 11 0.7665 --v 2.98,3.33` gives 4.1340 for a block of 10 by 12. The split measured 4.13.

**Control 2, the build.** Each built corner must settle at its count, `v1 + v2 + T`. A wrong mirror or a wrong transpose of a near end makes squares overlap. The squeeze then moves the stacks out, and the settled loss is above the count. For 9 and 11 at f = 0.7665, 71 of 72 corners settled within 1e-4 of their count, and one settled 0.17 lower. The round built 1,384 corners. 1,149 settled at their count, 234 settled lower by up to 0.48, and one settled 0.0003 higher.

### 14.2 The tool

`invent_block.py` builds the corner in the frame of `zone_corner.py`. The block has A by B plain squares, less the cells that would meet the plain grid. An arm end on a flat edge is what a far zone is. So the near end of each arm is a far zone of the library at this f, moved to the edge of the block. Only our own far zones with no missing cell are used, because such a zone can be mirrored.

With the lengths `lam1` and `lam2` of the two far zones, the first flush stacks stand at `y0 = B + lam1` and `x0 = A + lam2`. The corner then loses `v1 + v2 + T(A, B)`. Here v is the loss of a far zone, and `T = r1 B + r2 (A - W1) - cells` with `r = c cos t`. One more row of the block costs `g1` squares, and one more column `g2`.

**The smallest block is one column narrower than section 9 said.** The near ends do not meet when the block is `c1 - 1` by `c2`, or `c1` by `c2 - 1`. Such a block meets no cell of the plain grid. Its fixed term is `T = c2 g1 - r2 f`. For 9 and 11 at f = 0.7665 that is -3.50, against -3.04 for 9 by 11 and -2.18 for the 10 by 12 of 979. So the block of 979 is 1.32 squares larger than it needs to be.

**A block corner is two far zones less a fixed term.** It is cheap where the far zones are cheap. The far zone of an arm of 9 loses 2.90 squares at f = 0.63 and 3.24 at f = 0.68.

### 14.3 Block against staircase

Lowest loss of a settled corner, in squares.

| Pair | f | Block corner | Staircase corner | Block less staircase | Kill line |
| --- | --- | --- | --- | --- | --- |
| 9 and 11 | 0.7665 | 3.90 | 3.73 (this round, 119 settled) | +0.17 | dead |
| 11 and 11 | 0.68 | 5.48 | 5.37 (twoshort, first pass) | +0.10 | dead |
| 8 and 11 | 0.74 | 3.01 | 3.62 (this round, 130 settled) | -0.62 | passes |
| 8 and 8 | 0.64 | 2.15 | 2.80 (twoshort) | -0.65 | passes |
| 9 and 9 | 0.63 | 2.63 | 3.81, and 3.03 after hops (twoshort) | -1.18, -0.40 | passes |
| 9 and 9 | 0.64 | 2.69 | 3.71, and 3.46 after hops | -1.02, -0.77 | passes |
| 9 and 9 | 0.68 | 3.47 | 3.49, and 3.40 after hops | -0.02, +0.07 | dead |
| 9 and 9 | 0.72 | 3.61 | 3.65, and 3.56 after hops | -0.04, +0.05 | dead |
| 9 and 9 | 0.76 | 3.54 | 3.59 | -0.05 | dead |
| 8 and 9 | 0.68 | 2.64 | 2.72 | -0.08 | dead |
| 8 and 9 | 0.72 | 2.70 | 2.79 | -0.09 | dead |
| 8 and 9 | 0.64 | 2.05 | no run at this f | | |

- **Pairs with an arm of 11.** The block is dead for 9 and 11 and for two 11-arms. It passes for 8 and 11. The staircase run for 9 and 11 is new: its 3.73 is 0.97 under the line that the twoshort avenue used, 4.70.
- **The block passes at low f.** For two 9-arms it is 0.4 to 1.2 squares under the staircase at f = 0.63 and 0.64. From f = 0.68 up the two designs are level. Two 9-arms on a block lose 2.66, 2.63, 2.69, 2.98 and 3.29 squares at f = 0.62, 0.63, 0.64, 0.65 and 0.66.
- **8 and 11 at other f.** The block loses 2.97, 3.08, 3.19 and 3.57 squares at f = 0.70, 0.72, 0.76 and 0.78.
- **The block numbers hold no hops.** Every block number is a settled corner. The twoshort numbers after hops are in the table because they are the lowest staircase corners we hold.

### 14.4 What the generator finds

`zone_corner.py adopt`, `table` and `merge` put the corners into a copy of the twoshort library. `modules.py queue` then lists the rows that hold a new corner, against the bar, with a slack of 0.012 of side.

| Corners in the library | n searched | Rows within 0.012 | n with a row | Best row |
| --- | --- | --- | --- | --- |
| 8 and 11, block, f 0.70 to 0.78, 94 corners | 530 to 1000 | 0 | 0 | +0.0131 (855, from a search with a slack of 0.04) |
| 9 and 11, staircase, f 0.7665, 9 corners | 530 to 1000 | 10 | 3 | +0.0102 (978) |
| 9 and 9, block, f 0.63 to 0.68, 101 corners | 300 to 1000 | 32 | 8 | -0.0102 (969) |
| 9 and 9, block, f 0.62 and 0.65, 35 corners | 530 to 1000 | 16 | 4 | -0.0104 (969) |
| 9 and 9, block, f 0.63, six far zones for each near end, 50 corners | 530 to 1000 | 21 | 6 | -0.0102 (969) |
| 8 and 8, block, f 0.64, 46 corners | 300 to 1000 | 8 | 2 | +0.0029 (910) |
| 8 and 9, block, f 0.64 to 0.72, 43 corners | 530 to 1000 | 68 | 17 | +0.0029 (972) |
| 9 and 9, block with a swept zone as near end, f 0.62 and 0.6227, 48 corners | 300 to 1000 | 24 | 6 | -0.0144 (969) |

The corner counts are the corners that the library took after the cut on loss. "Best row" is the predicted side less the bar.

**A block corner is rigid.** A staircase corner trades the length of one arm for the length of the other, because the arms meet on its diagonal. A block corner has one y0 and one x0. An arm then fits only when the block, its near end, its stacks and its far end add to the side. With one length that does not fit, the arm keeps a slack, and a slack of 0.1 costs 0.8 squares. So a block corner that is 0.6 squares under the staircase gave no row for 8 and 11.

**More far zones do not give more n.** One run took six far zones for each near end in place of three. The generator found rows on 6 n, and it had every one of them before.

**The squeeze moves a block layout little.** The builds of 910 and 970 ended within 2e-5 of their predicted side. The builds of 969 ended 0.0002 to 0.0023 under it.

**Hops did not move a block corner.** `zone_corner.py sweep` ran 60 s of hops on each of 4 block corners. Three are corners of 8 and 9 at f = 0.68, and one is a corner of 8 and 8 at f = 0.64. No corner got a state under its start. No positive control of the hops ran this round, so this is a measurement of 4 corners and not a kill.

### 14.5 The builds of 969

| Step | Side of 969 |
| --- | --- |
| the round 17 file | 31.633982504 |
| predicted row, corner made at f = 0.68 | 31.625549 |
| its build, with the family squeeze and fq | 31.623256278 |
| build with a corner made at f = 0.63, family squeeze | 31.622748526 |
| one fq quench from that certified file | 31.621681634 |
| the 969 of the classfill lane: our corner, with far zones from their kind sweep | 31.621219526 |
| build with the swept zone as the two near ends of the corner too | 31.619580678 |
| one fq quench from that certified file | 31.619580671 |
| build from a start 0.012 above the predicted side, family squeeze | 31.619576788 |
| one fq quench from that certified file | 31.619576783 |
| the board of 2026-11-09 | 31.605570899 |

- **The layout.** The block is 8 by 10. All four arm ends are one far zone of a 9-arm in count class 0. The first builds used the library zone `z9-54f640.F1`, 54 squares with a loss of 2.90. With 8 flush stacks on each arm that is 80 + 4 x 54 + 144 + 529 = 969 squares. The certified build holds the same squares: its zone has 72 squares, which is the 54 and two flush stacks.
- **The swept zone.** The classfill lane ran its kind sweep on the far zones of our first 969. The zone lost 0.0796 squares, from 2.914 to 2.834, and they certified a 969 with it. A block corner holds the same zone twice as its near ends. So we rebuilt the corner with the swept zone, `cf9-72f6227.F1`. The corner went from a loss of 2.857 to 2.694, and the side from 31.622749 to 31.619581.
- **The certificate.** 969 certified with floatsafe at 2.2e-11, at a score of 0.015767151525601708. That is 4.628e-04 below the round 17 file, and 5.277e-05 below the 969 of the classfill lane. No other take dir holds a 969.
- **Sources.** The corner, the far zones and the tools are our own. No public layout is in the build.
- **The lengths set the side, not the count.** Each arm is a block edge, a near zone, flush stacks and a far zone. 30 of the 31 builds of 969 with the swept zone stop at f = 0.619580678. 19 of them are builds from 16 rows and 6 corners, and 11 are builds from looser starts. One build from a start 0.012 above the predicted side ended 3.9e-06 lower, and that one is certified. Three of the four builds of 907 stop there too. They all hold one arm: the swept zone at both ends, with 3 or 4 flush stacks between. The second fq quench gave 2e-10 of score. The first one had given 3.4e-05, from the slack that the kind sweep then took.
- **For 969 that stop holds under three methods.** The family squeeze, `methods_lp.slp` and fq all end at 31.619580671.
- **One build of 907 went past the stop, to f = 0.618227, and it slid rows of the plain rest.** `modules.py grow` refuses that layout with "rest broken". 18 upright squares stand 0.019 off the lattice in x, and 13 stand 0.024 off in y. So the stop is the arm against a rigid rest. The two rows of 907 built with `methods_lp.slp` stop at 0.619580671 like the others.
- **Nine builds with the library zone ended between 31.622749 and 31.623285.** They use nine corners. So the first gain did not hang on one corner.
- **907 is a near miss.** The same design one shell down ended at 30.618227087. That is 0.000139 under the round 17 file and 0.000307 above the 907 that the rigidsoft lane certified in this round. The layout is `take-invent-r19/near/907-block-cf.csv`.
- **What is left on 969.** It is 0.0140 of side above the board, which is 0.89 squares of area. The round 17 file was 0.0284 above, 1.80 squares.

**The kind sweep on the other near ends.** We ran the sweep of the classfill lane (`classfill.py own --f`) on six more far zones that block corners hold.

| Zone | Arm | f | Loss before | Loss after |
| --- | --- | --- | --- | --- |
| `z9-53f640.F1` | 9, class 8 | 0.62 | 3.169 | 3.060 |
| `z9-46f640.F1` | 9, class 1 | 0.62 | 3.290 | 3.290 |
| `z8-41f700.F1` and `z8-25f650.F1` | 8, class 1 | 0.68 | 2.697 | 2.697 |
| `z8-40f700.F1` | 8, class 0 | 0.68 | 2.957 | 2.957 |
| `z9-36f680.F1` | 9, class 0 | 0.68 | 3.243 | 3.243 |

- One zone of six got shorter, by 0.109 squares. It gave no new n: the rows of 907 hold it on the arm that does not set the side.
- The four zones at f = 0.68 are the near ends of the rows of 910 and 972. Those rows stay 0.0029 above the bar.
- **Hops gave nothing more on the swept zone.** 180 s of the hops of `zone_search.py` on `cf9-72f6227.F1` at f = 0.6196 tried 143 moves, and none made the zone shorter.
- The classfill lane swept three 8-arm near ends at f = 0.64 in the same hour. None moved.

### 14.6 The two handoffs

- **The 20 largest n where a kick comes back.** One line in `handoff-r19.log` went to the rigidsoft, k123 and forensics lanes at 20:26 UTC. It names the block that each layout holds. 8 hold a block or a band at 45 degrees (367, 366, 847, 401, 330, 850, 365, 262). 8 are two arms with no block (634, 646, 379, 340, 333, 793, 796, 851). 2 hold an arm and steep blocks at 36 to 39 degrees (491, 848). 790 holds twin blocks at 26 degrees that stand off the walls. 456 holds a fault from wall to wall. The reading of each layout is in [`results/invent-r19-2026-11-12-rigid20.tsv`](../results/invent-r19-2026-11-12-rigid20.tsv).
- **The kick tests of section 11.** One line went to the midm lane at 20:27 UTC with the paths of the three lists and of `invent_bigkick.py`. This lane ran no kick in round 19.

### 14.7 A reader for the refused layouts (idea 3 of section 1)

Idea 3 is the one idea of the five that nobody had run.

**The tool.** `invent_reader.py` cuts each arm along a line between two stacks, a few stacks from the corner. It keeps what lies before the two cuts. It then settles that corner against the first flush stack of each arm with `zone_corner.settle_zone`. A lattice cell of the plain grid with no square on it is a missing cell. The loss is in the frame of the library.

**Control.** On a layout that the zone cut accepts, the reader must give the corner of the split of section 9 within 0.1 squares. On 979 it must give 4.13 within 0.3.

**Kill line (section 1).** Dead when it reads fewer than 30 of the 83 refused arm layouts at m = 28 to 31.

**Control result: red in part.** The control ran on 12 layouts that the zone cut accepts. The reader read 8 of them. The table has the 7 that have a split to compare with.

| n | Arms | Reader | Split of section 9 | Reader less split | Inside 0.1 |
| --- | --- | --- | --- | --- | --- |
| 911 | 9 and 9 | 3.52 | 3.57 | -0.05 | yes |
| 974 | 9 and 9 | 3.65 | 3.66 | -0.01 | yes |
| 975 | 9 and 9 | 3.56 | 3.58 | -0.02 | yes |
| 993 | 8 and 11 | 3.78 | 3.81 | -0.03 | yes |
| 812 | 8 and 8 | 3.32 | 3.43 | -0.12 | no |
| 921 | 9 and 9, 9 missing cells | 3.76 | 3.96 | -0.20 | no |
| 930 | 8 and 11 | 4.13 | 3.80 | +0.33 | no |

- **979 fails.** The reader gives 5.41 with 7 missing cells, and only with the cut 6.5 stacks out. The split says 4.13.
- **The loss depends on the cut.** For 993 it is 4.61, 3.99 and 3.78 with the cut at 2.5, 3.5 and 4.5 stacks. A near end is longer than the first cuts, so a short cut reads a loss that is too high. 930 was read at 3.5 stacks only.
- **4 control layouts were not read.** 912, 803 and 863 had no legal settle. 983 has an arm that is not a whole number of squares wide.

**Kill line result: dead.** The reader read 20 of the 83 refused layouts, 12 of them with no missing cell. That is under 30.

| Why a refused layout is not read | Layouts |
| --- | --- |
| an arm is not a whole number of squares wide | 37 |
| cells of the rest are off the lattice | 11 |
| no legal settle | 10 |
| no line between two stacks | 5 |

- **Most refusals are not a problem of the cut.** 37 of the 83 layouts have an arm whose width fits no whole stack size. The held 969 and 908 are two of them: each arm is 8.67 squares wide. Another cut does not read them. They need a model of an arm that is sheared or has stacks of two sizes.
- **The corners that were read give no new low corner.** The lowest is 797, two 8-arms at f = 0.73 with a loss of 2.50. Then come 915 (8 and 9, 2.72 with 2 missing cells) and 805 (two 7-arms, 2.73). The twoshort avenue holds 2.47 for two 8-arms, and its line for two 7-arms is 1.40.
- **The 12 corners did not go into a library.** Each comes from a layout of another source, and its licence must be read from that source first.
- The tables are [`results/invent-r19-2026-11-12-reader.tsv`](../results/invent-r19-2026-11-12-reader.tsv).

### 14.8 Next

Best first. Each line has the number that puts it there.

1. **Sweep the far zones that block corners hold, then rebuild the corners.** The sweep is the kind sweep of the classfill lane. A block layout holds one far zone up to four times. One sweep of 60 s took 0.0796 squares from the zone of 969. That moved 969 by 0.0021 of side, which is 6.7e-05 of score. We swept 7 zones and 2 moved. The library holds far zones for arms of 7 to 11 at f = 0.60 to 0.66 that no sweep has seen. The loop is `classfill.py own --f`, `classfill.py merge`, `invent_block.py block`, then `zone_corner.py adopt`, `table` and `merge`. It took 4 minutes for 969.
2. **Slide rows of the rest beside a block layout.** One build of 907 did it by chance and went 0.00135 of side under the stop of the squeeze. The same step on 969 is 4.3e-05 of score, and 31 builds of 969 did not find it. A kick or a band move can. The near layout of 907 is 0.000307 of side above the bar, in `take-invent-r19/near/907-block-cf.csv`.
3. **Give the block corner near ends of more lengths.** For two 9-arms the block is 0.4 to 1.2 squares under the staircase at f = 0.62 to 0.64. For 8 and 11 it is 0.6 under. It gave a row on 17 n at most, and one row under the bar. Every row stops on the lengths. More far zones from the library did not help: six for each near end gave no new n. A swept zone has a new length, so point 1 serves this too. A near end with a slid row is the other source of lengths.
4. **Put hops on the staircase corner of 9 and 11.** This round's corner at f = 0.7665 loses 3.73. That is 0.40 under the corner that the held 979 has, 4.13. Its best row is 0.0102 above the bar, on 978. Hops took 0.1 to 0.8 squares from the staircase corners of two 9-arms in the twoshort avenue.
5. **Leave the reader as it is.** It read 20 of 83 refused layouts and its control is red in part. 37 of the 83 need a model of an arm that is not a whole number of squares wide, and this tool has no such model.

### 14.9 Files of round 19

- `invent_block.py`: the count of a block corner (`count`) and the builder (`block`).
- `invent_reader.py`: the reader of section 14.7 (`corner`).
- [`results/invent-r19-2026-11-12.tsv`](../results/invent-r19-2026-11-12.tsv): every number of sections 14.3 to 14.7.
- [`results/invent-r19-2026-11-12-rigid20.tsv`](../results/invent-r19-2026-11-12-rigid20.tsv): the reading of the 20 layouts of section 14.6.
- [`results/invent-r19-2026-11-12-reader.tsv`](../results/invent-r19-2026-11-12-reader.tsv): the reader on the 12 control layouts and the 83 refused ones.
- The take dir is `take-invent-r19` on boxA, under `<scratch>/bounties-squares`. It holds `969.csv`, `take.tsv`, the log `STATE.txt`, two layouts of 907 in `near/` (the one that slid and one at the stop), and the libraries, corners and logs of boxE in `work/boxE/`.

## 15. Round 20 (2026-11-12, 22:36 to 01:10 UTC)

**Result: one n is in the take, 754. It is 1.35e-10 of score below the 754 of the corners lane, and 3.751e-05 below the round 18 file, nearly all of it theirs. The corners lane then took its 754 out of its take, so at 00:54 UTC ours is 4.37e-06 below every other take. The new move is a local kick, then the family squeeze. It found on purpose the drop of 1.35e-3 of side that one build of 907 found by chance in round 19. In 22 other runs it took 1e-9 to 6.3e-5 of side, and other lanes went lower on every n but 754.**

"The bar" of an n is the lower of the round 18 file (`gate/cand-round18-1112a`), every take dir of round 19 and every other take dir of round 20. A result counts when it certifies below the bar.

### 15.1 Why a block layout stops

In round 19, 30 of 31 builds of 969 stopped at f = 0.619580678. Five of six builds of 907 stopped at the same f. One build of 907 went on to 30.618227. We compared that build with its twin, which stopped (`raw-e1/907-eb43e435` against `raw-e1/907-a546dc1b`). The twin holds the same layout turned over its diagonal: 859 of 907 squares lie within 0.05 of their place. 416 squares moved by 0.002 to 0.1. Most of them are upright squares of the block in the corner, which went down by 0.01 to 0.1. A few turned by 1 to 3 degrees.

So the slide is the corner block giving way. It is not a slide of the far rows of the rest, as round 19 said.

### 15.2 Three moves and their controls

The control for each move is the same. The move starts from the twin that stopped, at 30.619580679. It is green when one try ends below 30.6195806, the stop of the squeeze.

| Move | Tool | Tries | Lowest side | Control |
| --- | --- | --- | --- | --- |
| fq kick: kick, melt and bkick of `midm_scan.py`, then fq | `midm_scan.py` | 23 in 8 min | 30.6187 (start 30.618227) | dead |
| slide of row segments that touch the arms, then the family squeeze | `invent_rest.py --modes seg` | 83 in 4 min, 17 of them legal | 30.619580677305 | red |
| local kick near the arms, then the family squeeze | `invent_rest.py --modes lkick` | 31 in 10 min | 30.618227092836 | green |

- **The fq kick does not come back.** The kick scan of the midm lane started from the 907 that slid. No try ended at or below the start. Kicks of sigma 0.003 to 0.04 ended at 30.6187 to 30.6196. Melt ended at 30.630 to 30.834. The block kick ended at 30.78 or gave no layout. fq does not reach the side that the family squeeze reaches on a block layout, so a kick with fq cannot do the slide. The scan started on the slid layout and not on the twin, so it is a measurement and not a control.
- **The rows have no room.** Most segment moves were refused: no shift of a row or a column that touches the arms stays legal. The others shifted by 0.000 to 0.027, and the squeeze came back to the stop every time.
- **The local kick finds the slid layout on purpose.** A kick picks the squares within 1.2 to 3.0 of one square near the arms. Each moves by a normal draw of sigma 0.003 to 0.02. It also turns by half of that, in radians. The squeeze then repairs the overlap of the start. Try 4 passed the stop (30.6195641). Try 9 (21 squares, sigma 0.003) ended at 30.618227092836. That is the side of the build that slid in round 19, to 1e-12. The 22 tries after it stayed there, at a second stop.
- **The fq kick and the local kick differ in one thing:** what settles the layout after the kick. The squeeze that built the layout comes back to it, and fq does not.

### 15.3 More arm pairs on the block corner

`chain-g.sh` built the block corners of 7 more arm pairs at f = 0.62 and 0.64 (`invent_block.py block`, 45 corners each). It then ran the generator against the bar, for n = 530 to 1000.

| Pair | f | Lowest settled loss | Rows within 0.012 | Best row |
| --- | --- | --- | --- | --- |
| 10 and 10 | 0.64 | 4.79 | 0 | |
| 9 and 10 | 0.64 | 3.41 | 0 | |
| 9 and 10 | 0.62 | 3.65 | 0 | |
| 10 and 10 | 0.62 | 5.40 | none: no corner under the loss cut of 5.0 | |
| 8 and 10 | 0.64 | 2.74 | 0 | |
| 7 and 9 | 0.62 | 1.48 | 0 | |
| 8 and 9 | 0.62 | 1.86 | 12 | 910 +0.0034 |
| 8 and 8 | 0.62 | 1.97 | 4 | 910 +0.0034 |

No row came within 0.002 of the bar, so nothing was built. We stopped the chain at 23:06 UTC for the local kick, which had a green control. Four pairs did not run: 8 and 10 at 0.62, 7 and 9 at 0.64, 7 and 8 at 0.62, 10 and 11 at 0.66.

### 15.4 The local kick on other layouts

The local kick passed the stop of the squeeze on 907. So we ran it, for 300 to 600 s each, on the layouts that hold the bar of other n. These are layouts that the family squeeze built: the family, readers, modules, classfill, stair-c and corners lanes made them. We took first the new layouts of round 20 and the near layouts that other lanes handed off. The n with the largest gap to the board came next, and the round ended before them. `refresh.sh` set the start of each run to the layout of the bar when the run began, because the other lanes lowered the bar during the round.

| Run | n | Start from | fq | Tries | Finds | Start side | Lowest side | Side taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `near793a` | 793 | take-twoshort-r20 near/793-d7c0ef24 | yes | 6 | 2 | 28.672769876 | 28.672764987 | 4.889e-06 |
| `near793b` | 793 | take-twoshort-r20 near/793-cb1206a4 | yes | 2 | 2 | 28.672808496 | 28.672779654 | 2.884e-05 |
| `near793c` | 793 | the find of near793a | yes | 6 | 1 | 28.672764987 | 28.672762802 | 2.184e-06 |
| `near794a` | 794 | take-twoshort-r20 near/794-4c50630e | yes | 5 | 1 | 28.684006473 | 28.684005940 | 5.328e-07 |
| `rest598` | 598 | take-corners-r20 | yes | 19 | 1 | 24.900450067 | 24.900450065 | 1.196e-09 |
| `rest703` | 703 | take-corners-r20 | yes | 8 | 1 | 26.941702257 | 26.941702256 | 1.297e-09 |
| `rest754` | 754 | take-corners-r20 | yes | 9 | 2 | 27.900113404 | 27.900113398 | 5.067e-09 |
| `rest803` | 803 | take-family-r19 | no | 38 | 5 | 28.814544149 | 28.814543968 | 1.813e-07 |
| `rest803b` | 803 | take-family-r20 | yes | 5 | 1 | 28.813499076 | 28.813499075 | 1.391e-09 |
| `rest810` | 810 | take-stair-c-r20 | no | 33 | 5 | 28.904091916 | 28.904081346 | 1.057e-05 |
| `rest810b` | 810 | take-polish-r20 | yes | 8 | 2 | 28.902453734 | 28.902449575 | 4.159e-06 |
| `rest862` | 862 | take-modules-r20 | no | 17 | 0 | 29.825745981 | 29.825745981 | 0.000e+00 |
| `rest870` | 870 | take-classfill-r20 | no | 18 | 0 | 29.916956559 | 29.916956559 | 0.000e+00 |
| `rest914` | 914 | take-corners-r20 | yes | 5 | 1 | 30.724353122 | 30.724353120 | 1.487e-09 |
| `rest969b` | 969 | take-invent-r19 | no | 9 | 2 | 31.619576784 | 31.619576681 | 1.032e-07 |
| `rest969k` | 969 | take-invent-r19 | no | 68 | 4 | 31.619576784 | 31.619576675 | 1.096e-07 |
| `stc869a` | 869 | take-stair-c-r20 near/869-62637b47 | no | 34 | 2 | 29.911598886 | 29.911598768 | 1.173e-07 |
| `stc870a` | 870 | take-stair-c-r20 near/870-d7d188d0 | no | 22 | 0 | 29.916971020 | 29.916971020 | 0.000e+00 |
| `stc931a` | 931 | take-stair-c-r20 near/931-ab507b69 | no | 40 | 4 | 30.924135007 | 30.924071659 | 6.335e-05 |
| `stc931b` | 931 | take-stair-c-r20 near/931-d0151ff3 | no | 30 | 0 | 30.924209214 | 30.924209214 | 0.000e+00 |
| `stc931c` | 931 | the find of stc931a (walk 1e-4) | no | 38 | 0 | 30.924072112 | 30.924072112 | 0.000e+00 |
| `stc993a` | 993 | take-stair-c-r20 near/993-7b2fcaf6 | no | 29 | 1 | 31.924324476 | 31.924323588 | 8.882e-07 |

- **A start that fq polished does not move with the squeeze alone.** 862 of the modules lane went through fq after its squeeze. 17 tries ended 4.3e-9 of side above it: the squeeze stops above the optimum of fq. From 23:35 UTC every run on a polished layout got `--fq`, so two fq passes follow the squeeze, as in `modules.py job`. Then 810 from the polished file of the polish lane went 4.2e-6 lower in 3 tries.
- **The large steps come from builds that fq never touched.** Outside 907, the largest step was 6.3e-5 of side, on the near layout 931 of the stair-c lane. That layout is a family build with no fq. Next come 2.9e-5 on a near 793 of the twoshort lane and 1.06e-5 on 810. Most runs took 1e-9 to 1e-6 of side, which is under 4e-8 of score.
- **No near layout crossed the bar.** The 931 stopped 1.13e-4 of side above it, and the 793 stopped 6.6e-6 above it.
- **The bar moved under the runs.** Our finds on 803, 810 and 969 certified for a time. Then the family, polish and harvest lanes went lower on the same n. At the end only 754 is below the bar.
- **969 has no step like the one of 907 within reach.** Two runs on 969 tried 77 kicks. 9 of them had the centre in the corner block and turns twice as large. The lowest is 1.1e-7 of side under the start.

### 15.5 What certified

| n | Round 18 file | Certified | Gain on the round 18 file | Start of the run |
| --- | --- | --- | --- | --- |
| 754 | 0.016099707640 | 0.016062201595 | 3.751e-05 | invent_rest.py lkick (a local kick of the squares near the arms, then family_step.squeeze and two fq passes) from the layout of n = 754 in take-corners-r20 |

The source and the licence of each row name the layout that the run started from, in `take-invent-r20/take.tsv`.

The two last runs, on the stair-c near layouts 930 and 994 (no fq, to 00:54 UTC), took 4.2e-8 and 7.2e-5 of side. Both stay more than 1.6e-3 above the bar.

### 15.6 Next

Best first. Each line has the number that puts it there.

1. **Run the local kick on each build before its first fq pass.** Use the family squeeze and no fq. On the stopped twin of 907 it found the drop of 1.35e-3 of side in 9 tries. On the near layout of 931 of the stair-c lane, a family build with no fq, it took 6.3e-5 in 2 tries. On layouts that fq had polished it took nothing with the squeeze alone (862: 17 tries, 870: 18 tries), and 1e-9 to 4.2e-6 with fq after the squeeze. The builders are `modules.py job` and the build steps of the stair-c, twoshort and classfill lanes. The step costs 5 to 30 s per try under load.
2. **Keep the kick steps small and the walk off.** The finds came from kicks of 4 to 25 squares at sigma 0.003 to 0.02. A walk that accepts results up to 1e-4 of side worse went back to the old stop of 931 and found nothing in 38 tries. Kicks with the centre in the corner block and turns twice as large found nothing on 969 in 9 tries.
3. **Leave 969 and the block pairs.** Two runs of 77 kicks moved 969 by 1.1e-7 of side. The 7 new block pairs gave no row within 0.002 of the bar. The polish lane holds 969 now, 3.7e-9 of score under our round 19 file.

### 15.7 Files of round 20

- `invent_rest.py`: the slide of row segments (`--modes seg`) and the local kick (`--modes lkick`), each followed by `family_step.squeeze`, with `--fq` for two fq passes after it.
- [`results/invent-r20-2026-11-13.tsv`](../results/invent-r20-2026-11-13.tsv): one row per run of `invent_rest.py`, and the block pairs of section 15.3.
- The take dir is `take-invent-r20` on boxA, under `<scratch>/bounties-squares`. It holds the per-n files, `take.tsv` and `STATE.txt`. `work/` holds the scripts of the round (`slotq.sh`, `refresh.sh`, `certrest.py`, `cert20b.sh`), the starts of every run (`starts/`, `runs.tsv`) and the runs pulled from boxE (`boxE-raw/`).

## 16. Round 21 (2026-11-13, 01:03 to 12:20 UTC)

**Result: Four n are in the take: 549, 813, 869 and 929. They gain 4.783e-04 of score on the round 19 file, and 6.16e-05 under the bar. Most of it is 929, where the chase of the readers 929 took 5.2e-5 of side in one run. During the round the local kick took 8 more n below the bar: 853, 794, 993, 796, 810, 930, 811 and 698. Other lanes then went lower on each. On 9 of the 12 n we certified, the lowest row of any lane now holds a step of our kick.**

"The bar" of an n is the lowest row of that n in three places. These are the round 19 file (`gate/cand-round19-1112a`), every frozen take dir of round 20, and every other live take dir of round 21. A result counts when it certifies below the bar.

The lane ran in three attempts. The first ran from 01:03 to 01:22 UTC and stopped on a usage limit. Its queue on boxE went on to 02:20 and its cert loop to 03:33. boxA rebooted at 05:36. The second attempt ran from 09:50 to 09:55 and started a new queue. The third took that queue over at 09:59.

### 16.1 The runs

Every run is `invent_rest.py --modes lkick` on boxE, two at a time, 300 to 420 s each. There are three kinds of start:

- A near start is a near layout that another lane handed off, within 2.5e-5 of side of the bar.
- A bar start is the layout that held the bar of its n when the run began.
- A leg starts from the last find of an earlier run (section 16.4).

| Start | fq | Runs | Moved | Median step of those that moved | Largest step |
| --- | --- | --- | --- | --- | --- |
| near | no | 13 | 10 | 2.8e-07 | 3.4e-05 (793) |
| near | yes | 6 | 4 | 7.6e-06 | 4.0e-05 (549) |
| bar | no | 27 | 12 | 2.2e-07 | 5.2e-05 (929) |
| bar | yes | 2 | 2 | 1.5e-08 | 2.7e-08 (796) |
| leg | no | 6 | 3 | 7.5e-07 | 4.0e-06 (793) |
| leg | yes | 2 | 2 | 4.8e-06 | 9.6e-06 (549) |

Steps are in units of side. The table has 56 runs. The results table has one row per run (section 16.8).

The near lines handed off by the lanes of round 20 ran first, from 01:09 to 02:20 UTC. From 10:03 the chase (section 16.4) took most of the time, so 29 runs started from bar layouts. From 11:40 the chase waited, so the near lines closest to the bar ran again.

### 16.2 One fq quench takes our find

At 09:58 UTC the local kick certified 810 and 930. Both started from the new layouts of the readers lane. By 10:13 the polish lane held both. Each of its rows is one fq quench of our certified file, 1.6e-10 of score lower than ours. The same happened to 811 and 698. The harvest lane holds the same rows.

Our own fq quench of the same file gives the same number to the last digit, because fq is deterministic. So it ties the row of the polish lane, and the certifier drops it, since a row must be 1e-10 lower than every other take.

The total of the round does not change: the merge takes the lowest row of every lane. But the step of the kick then shows in another lane, and the contract asks for the quench before the file is written.

So from 10:18 UTC a slot quenches the last find of each run without `--fq` before boxA sees it (`slotq21b.sh`). boxA certifies such a run only from that quench (`cert21.sh`, `fqout-<run>/`). The control: the leg `gt811nn` certified 811 at 2.75e-10 under the polish row, at 10:25.

### 16.3 What the steps say

- **Layouts that the family squeeze built in round 19 or 20 do not move.** We ran five such bar layouts: 931, 804, 987, 852 and 794. Each took 0 in 21 to 48 tries, except 6.2e-9 on 794.
- **New builds of round 21 move.** The readers 810 went 6.5e-6 of side lower in 43 tries. The readers 752 went 2.5e-6 lower, and the family 811 went 3.3e-8 lower.
- **`--fq` on a polished near layout takes the largest steps.** The modules near 549 went 4.0e-5 lower, the near 652 9.7e-6 and the classfill near 993 5.6e-6.
- **The follow lanes go lower within minutes.** Our finds on 853, 794, 993, 796, 810, 930, 811 and 698 certified. Then the family, readers, k123, polish and harvest lanes went lower on each of them, mostly by a walk or a quench of our file.

### 16.4 The chase queue and legs

`autoq21.py` runs after each cert pass, every 3 minutes. It puts two kinds of line at the top of the queue:

- **Chase.** Each new round 21 bar layout of another lane gets one run, if this lane does not hold that n lower. Layouts that fq polished get `--fq` and 300 s. Family builds get no fq and 420 s. At most 4 such lines wait unrun, so the near lines below still run.
- **Leg.** A run gets a second run from its last find when three things hold. It found 3 times or more. Its last find came in the last 40% of its tries. Its best side is closer to the bar than the step it took. At most 2 legs wait. The reason: in this round, 8 of the 16 runs that moved were still finding at their last tries.

Eight legs ran. The leg of 549 took 9.6e-6 of side at tries 1 and 2 of 23. A second leg from that find took 1.2e-9. The leg of 793 took 4.0e-6 and the leg of 929 took 7.5e-7. The legs of 810, 930 and 698 took nothing, and the leg of 811 took 5.8e-9. So a leg pays on a start that the run has just moved a long way, and one leg is enough.

The chase found the largest step of the round. Four runs chased the 929 of the readers lane as it walked lower. They took 0, 5.5e-7, 1.3e-5 and 5.2e-5 of side. The readers 929 is a family walk with one fq quench, so it is a fresh build each time.

`autoq21.sh` also sends one fq quench for each new row of `take.tsv`, the contract quench, and never a second one for a row that already came out of a quench.

### 16.5 What certified

| n | Round 19 file | Certified | Gain on the round 19 file | Run and start |
| --- | --- | --- | --- | --- |
| 549 | 0.019640606991 | 0.019600860849 | 3.975e-05 | a549f, then the leg g549tf, from the modules near 549 of round 20 |
| 813 | 0.014580042046 | 0.014575370774 | 4.671e-06 | u1109x813n, from the family 813 of round 21 |
| 869 | 0.014664787233 | 0.014483521103 | 1.813e-04 | r869n, from the readers near 869 of round 21 |
| 929 | 0.014070357950 | 0.013817737857 | 2.526e-04 | u1140x929n, then the leg gu1140x929nn, from the readers 929 of round 21 |

The source and the licence of each row name the layout that the run started from, in `take-invent-r21/take.tsv`.

### 16.6 Traps of this round

- **A loop reads its script while you edit it.** At 10:18 the cert loop ran `cert21.sh` while it was being rewritten in place. It ran a mix of the old and the new script and published 698 before its quench. Write the new script to a new file and `mv` it over the old one.
- **A request with several n gave every file the source of the first n.** `fqreq.sh` now writes one spec per n (`fqout-<tag>#<n>`), and `certrest21.py` reads only the files of that n.
- **The cert pass took 2 to 6 minutes** at a boxA load of 22, because it ran floatsafe on every run each time. `certrest21.py` now keeps a cache of the scores (`work/fs-cache.json`): 82 s became 16 s, with the same rows.

### 16.7 Next

Best first. Each line has the number that puts it there.

1. **Quench each find once before it is published.** This holds for every lane that publishes squeeze-only finds. The polish and harvest lanes took 810, 930, 811 and 698 from our take with one fq quench of our own file, 1.6e-10 of score lower. A quench of the same file by us ties theirs to the last digit. After `slotq21b.sh` quenched before the publish, our 811, 813, 869 and 929 certified with the quench already in them.
2. **Kick each fresh build at once.** The lane that builds a layout by a walk or a join should run the local kick on it. The readers builds moved by 6.5e-6 (810), 2.5e-6 (752) and up to 5.2e-5 (929). The classfill lane took 1.13e-4 on a fresh modules build of 994 at 10:59. Layouts that the family squeeze built in round 19 or 20 moved in 0 of 5 runs.
3. **Chase only the lanes that hand on fresh builds: readers, family, stair-c, corners.** The chase moved 12 of 27 bar layouts without fq, with a median of 2.2e-7. The midm and polish layouts moved by 0 to 3e-9 (868, 918).
4. **Give a find one leg, with `--fq` if the run had it.** The 549 leg took 9.6e-6 of side, the 793 leg 4.0e-6 and the 929 leg 7.5e-7. A second leg on 549 took 1.2e-9.
5. **Keep the near lines in the queue.** Near layouts within 1e-5 of the bar moved in 14 of 19 runs. The median step was 2.8e-7 without fq and 7.6e-6 with fq. A chase that refills the top of the queue every 3 minutes keeps them out: none ran from 10:06 to 11:45.

### 16.8 Files of round 21

- [`results/invent-r21-2026-11-13.tsv`](../results/invent-r21-2026-11-13.tsv): one row per run of `invent_rest.py`, with its kind (near, bar or leg).
- The take dir is `take-invent-r21` on boxA, under `<scratch>/bounties-squares`. Its `work/` holds the scripts of the round:
  - `slotq21b.sh`: boxE slot, with the quench of each run.
  - `cert21.sh` and `certrest21.py`: the certifier.
  - `autoq21.py` and `autoq21.sh`: the chase queue, the legs and the contract quench.
  - `fqreq.sh`: one fq quench of chosen take files. `mkres21.py`: the run table.
- `work/` also holds the starts (`starts/`, `runs21.tsv`) and the runs pulled from boxE (`boxE-raw/`).

## 17. Round 22 (2026-11-13)

The take at 15:27 UTC holds 6 n: 340, 698, 753, 805, 868, 931.
They gain 1.112150594e-03 on round 20 and 6.911935945e-04 below every other take.
The bar is the lowest score in round 20, every frozen round 21 take, and every other live round 22 take.
Each row must clear that bar by more than 1e-10 of score.

### 17.1 Results and starts

The family lane's round-trip near 855 from round 21 gave the first 855 find.
It took 0.002536380 of side, from 29.732009009 to 29.729472629.
That is 0.001159 below the per-puzzle board of November 9 (29.730631585).
The one leg from that find was dry.
The readers lane walked our 855 down and back up, then wrote a row 9.6e-14 of score lower.
Our 855 left the take because it no longer clears every other row by 1e-10.
The readers row keeps the kick and its source chain.

Fresh builds also moved.
The readers 698 took 5.27e-5 of side.
The k123 join at 805 took 5.37e-5, then its one leg took another 1.00e-4.
A kick of the family 999 took 2.84e-5 but stayed above the bar.
Four early scans of quenched rectangle layouts (641, 640 and two 458) found nothing with the squeeze alone.
These four runs do not test kicks with fq after every squeeze.

[The run table](../results/invent-r22-2026-11-13.tsv) records 46 production runs and the positive control.
The production runs made 2769 tries.
A move in this table means more than 1e-8 of final side, after the contract quench.

| Start | fq after each squeeze | Runs | Moved | Largest side step |
| --- | --- | --- | --- | --- |
| near | no | 10 | 7 | 2.536e-03 |
| near | yes | 4 | 2 | 2.318e-06 |
| fresh | no | 26 | 13 | 5.375e-05 |
| leg | no | 5 | 1 | 1.001e-04 |
| leg | yes | 1 | 1 | 1.691e-08 |

### 17.2 What certifies

Every published layout first passes floatsafe on boxE.
Its certified file then gets one fq quench there, before boxA scores it and publishes it.
The take uses the lower safe result of that quench and its certified input.
Each per-n CSV is written first, and take.tsv is replaced by rename.
The source and licence of every row are in take.tsv.
Held inputs refer to results/round20-best-2026-11-13.tsv.
Other inputs name their lane, exact near file or take.tsv, and the source it records.

| n | Round 20 score | Final score | Gain on round 20 | Gain below every other take |
| --- | --- | --- | --- | --- |
| 340 | 0.026455210934 | 0.025890913758 | 5.643e-04 | 5.643e-04 |
| 698 | 0.017464513749 | 0.017323684555 | 1.408e-04 | 1.209e-04 |
| 753 | 0.016366943583 | 0.016250810523 | 1.161e-04 | 4.872e-08 |
| 805 | 0.016591129926 | 0.016571910455 | 1.922e-05 | 5.424e-06 |
| 868 | 0.014753293831 | 0.014575213235 | 1.781e-04 | 2.778e-08 |
| 931 | 0.013491830725 | 0.013398239630 | 9.359e-05 | 4.997e-07 |

### 17.3 Controls and collection

The positive control was the stopped block build of 907, at side 30.619580679.
Try 4 passed its stop, and try 9 reached 30.618227092836.
This reproduces the slide measured in round 20.
The first launch failed before search because frontier_read.py was missing from the copied code.
The retry used the same file, seed and flags after that dependency was copied.

Two boxE slots ran at nice 5 with a deadline file for 15:20 UTC.
The local collector polled every 90 seconds between passes.
It kept at most one fresh chase waiting and reserved a near start after two fresh starts.
The first cap of eight waiting jobs delayed legs, so it grew to fourteen.
An unstarted copy of an already kicked 851 was removed from the queue.
New shell walks and joins still count as fresh builds when their donors had kicks.

The score cache now reuses unchanged certified files and skips candidates that cannot beat the row already held.
Positive control: the old and cached passes kept six identical rows, byte for byte.
Negative control: changing the cached 698 file to overlap made the certifier drop it.
Restoring the file restored the same take.tsv.
The cached control pass took 0.706 seconds.
A transient rsync failure stopped one collection pass.
Excluding temporary solver files fixed the transfer, and stderr is now kept on failure.
boxE search slots continued through that failure.
Search ended at 15:19:26 UTC.
The final postquench ended at 15:20:09, nine seconds after the search deadline.
The next worker must apply the same deadline to its postquench.

The deployed files are in take-invent-r22/work.
The saved tools are [the collector](../tools/invent/round22/controller22.py),
[the worker](../tools/invent/round22/worker22.py),
[the certifier](../tools/invent/round22/certrest22.py),
[the layout key](../tools/invent/round22/invent_shape22.py), and
[the measurement writer](../tools/invent/round22/measure22.py).
The layout key has a positive control for translations, quarter turns and reflections.
A centre move of 0.001 must give another key.

### 17.4 Next

1. Kick round-trip near layouts from new joins before repeating kicks on bar layouts.
   The round 21 family near 855 gave 0.002536 of side this round.
   Keep close near layouts flowing beside the fresh chase.
2. Kick each fresh shell or join build, then give a useful find one leg.
   The readers 698 and k123 805 gave 5.27e-5 and 5.37e-5 of side.
   The 805 leg gave another 1.00e-4, while the 855 and two 698 legs were dry.
3. Keep the certified-file quench before publication and retain the score cache.
   It preserves the six-row control exactly and rejects a changed overlapping file.
   Record near provenance from the exact near.tsv, rectangle sidecar or join record before a result is handed on.
4. Resume the unrun queue from work/jobs.json only after comparing each input with the new round's bar.
   The two slots could not finish every waiting near layout and leg before the deadline.
   Do not treat the four dry rectangle scans without fq as a test of the fq branch.

## 18. Round 23 (2026-11-13)

89 production attempts on three boxE slots, 3127 completed tries. The take retains 14 n: 639, 648, 650, 692, 698, 736, 753, 793, 806, 866, 868, 916, 927, 989. All 13/13 saved starts finished. The first 442 and 485 kicks each removed 0.00046844 of side. The 442 result fed lower border descendants.

The take gains 0.00141435541848 on round 21 and 0.00037590454652 below frozen round 22 and every other live take.
The bar uses gate/cand-round21-1113a and all frozen round 22 and live round 23 takes.
Each result must clear both bars by more than 1e-10 of score.

### 18.1 Runs and controls

1 bounded worker errors are excluded from the move table.
The stopped 907 control passed at try 4, side 30.619564100215.
Try 9 reached 30.618227092836 and reproduced the known slide.
The control completed floatsafe and the quench from its certified file.

[The run table](../results/invent-r23-2026-11-13.tsv) records every completed scan and its source chain.

| Start | fq after each squeeze | Runs | Moved by more than 1e-8 | Largest final side step |
| --- | --- | --- | --- | --- |
| near | no | 26 | 9 | 0.000469792 |
| near | yes | 28 | 6 | 6.18561e-07 |
| fresh | no | 20 | 11 | 0.000468443 |
| leg | no | 14 | 6 | 3.6747e-05 |

10 rows in other live takes name this lane in their source chain.
They are excluded from this take count and gain.
The border lane used our 442 kick through its 530 build, then lowered 442 and 485.
Exact current records remain in work/descendant-rows.json.

The six-try plateau rule applies only to new seeds 123 and 172.
It stops when at least three end sides match their minimum within 5e-9 and none moves more than 1e-8.
An offline replay of 45 round 22 traces would stop 15 scans and free 4861.9 seconds.
It loses one side move of 2.945e-8 on 340.
The first ten moving traces retain their full result.
Equal end sides slightly above the input now stop too, while an early 0.001 slide keeps running.
Saved starts keep their original flags and seeds.

### 18.2 What changed

Three boxE slots ran at nice 5.
The third slot drains the 13 saved round 22 starts, then takes new near layouts.
The other slots interleave fresh builds, near starts and useful legs.
The saved backlog has its own capacity, so it cannot fill the fresh queue.
A later audit found 53 eligible unseen take layouts, including kicked copies.
Fresh admission now has one reserved entry while fewer than three fresh jobs wait.
The control started fresh 379 at 17:32 UTC and fresh 442 at 17:34 UTC.
38 eligible unadmitted layouts are saved in work/unadmitted-fresh.json with exact input hashes.

Rectangle starts now get fq after every squeeze.
Round 22 tested four rectangle starts with the squeeze alone and found no raw result.
Fresh shell builds retain the family squeeze before their first quench.

The near margin is 0.0031 of side, and the old floor at n = 300 is removed.
The geometry key rounds at 1e-7 instead of 1e-5.
This retains small changes in shell builds.
The key passes translation, quarter-turn and reflection controls.
A centre move of 0.001 gives another key.

Every find passes floatsafe on boxE, then gets fq from that certified file.
Publication uses the lower safe file after the quench completes.
The per-n file is written before take.tsv is replaced by rename.
Search and postquench use one common hard deadline of 18:30 UTC.
The worker terminates a child process group that exceeds its bound.
The deadline control stopped a child and grandchild in 0.517 seconds against a 0.5-second bound.

Input files transfer before their queue entries.
Certification reads its specs from a JSON file, so long source records fit.
Near provenance resolves to the exact module build record or donor source table.

### 18.3 Retained rows

| n | Round 21 score | Final score | Gain on round 21 | Gain below every other take |
| --- | --- | --- | --- | --- |
| 639 | 0.019855809178 | 0.019448369647 | 0.000407439531 | 1.97641681e-09 |
| 648 | 0.017583370206 | 0.017446134897 | 0.000137235309 | 0.000137235309 |
| 650 | 0.017168642756 | 0.017050594311 | 0.000118048445 | 2.04056394e-09 |
| 692 | 0.018469741075 | 0.018467059451 | 2.68162461e-06 | 1.72138992e-09 |
| 698 | 0.017444580634 | 0.017323607914 | 0.00012097272 | 7.66407593e-08 |
| 736 | 0.018714419375 | 0.018616114342 | 9.83050332e-05 | 4.9429929e-09 |
| 753 | 0.016358734532 | 0.016250582190 | 0.000108152342 | 2.28332197e-07 |
| 793 | 0.018199210438 | 0.018197286623 | 1.92381534e-06 | 2.60330864e-08 |
| 806 | 0.016159886173 | 0.016159886009 | 1.64362968e-10 | 1.64362968e-10 |
| 866 | 0.015330062506 | 0.015148788996 | 0.000181273509 | 3.29618579e-08 |
| 868 | 0.014575241010 | 0.014575211396 | 2.96145153e-08 | 1.83915794e-09 |
| 916 | 0.016080950360 | 0.016080929873 | 2.04867554e-08 | 2.04867554e-08 |
| 927 | 0.014461013550 | 0.014325110886 | 0.000135902664 | 0.000135902664 |
| 989 | 0.013875667814 | 0.013773297653 | 0.00010237016 | 0.000102369434 |

Sources and licences are in take-invent-r23/take.tsv.
Held ancestry names results/round21-best-2026-11-13.tsv.
Other inputs retain their donor take.tsv or exact near build record.

Final uncached checks passed the metric and pandas parse on all 14 retained rows. Minimum clearance was 5.01962915678e-11. All 335 remote CSV hashes matched local copies before removing the lane scratch.

### 18.4 Next

1. Kick each new shell or join at its handoff and reserve fresh admission. The first 442 and 485 scans each removed 0.00046844 of side. Keep new round-trip near layouts beside them: round 22 family 855 gained 0.002536 of side.
2. Reconsider 38 snapshots in work/unadmitted-fresh.json and 16 queued starts in work/pending-final.json against the next bar. Their exact inputs, sources and flags are saved. The 53-layout admission backlog showed why fresh builds need reserved capacity.
3. Give a useful find one leg. Saved 698 and 753 gained 3.6747e-5 and 6.2656e-6 of side. 6/14 completed legs moved more than 1e-8. The first 442 and 485 legs were dry, so require new geometry before repeating them.
4. Keep measuring the fq-enabled repair separately. 6/28 completed fq-enabled scans moved more than 1e-8 of side. Change the layout or repair budget before repeating 913: its first try exceeded 400 seconds without output.
5. Keep positive controls on the rule that stops repeated end sides. Replay saves 4861.9 seconds on 45 full traces and loses one tiny move. 30 live stops do not prove later gain is impossible. Measure both time and lost gain.
6. Retain exact near provenance and quench certified inputs before publication. The overlap cache control rejects changed bad input. Round 22 postquench exceeded its search deadline by nine seconds, so preserve the tested common bound.

The deployed scripts and exact starts remain in take-invent-r23/work.
Saved tools are in [tools/invent/round23](../tools/invent/round23/).

## Summary

- One n certified: 464, 1.370e-05 of score below held. It is in the take dir with its row in `take.tsv`.
- The find came from a kick before the fq quench, on a layout that no kick had touched, and from 2 relay legs after it. 25 such layouts had a scan and one opened. 20 more first scans on a third list opened none.
- The soft chain is dead on public held layouts: 40 passes and 2,042,723 children with no find. The rule of the soft lane is right. A second kick seed is dead too: 19 scans with no find.
- The census is dead as a predictor. Its lead was the design of 979, two arms that never meet and a plain block in the corner.
- A new split of the end loss reads 199 layouts with no cut. The two far ends cost 1.7 to 2.2 times the corner in every pair of arm sizes. The far ends of 979 cost what ours cost.
- The block of 979 is a corner of 4.13 squares for arms of 9 and 11, 0.6 under the line of the twoshort avenue. A count from the parts gives 4.14. A block corner is within 0.5 squares of our staircase corners, so it does not close the gap to the board.
- The plateau drop is dead: 5 of 37 starts slid and none ended below held. The monotone check found no n that can take a larger n's layout.
- A pool of 15,692 kick tries says where the seconds pay. In half of the scans, 3 or more of the first 6 tries came back to the start side. The later tries of those scans took 21% of the seconds for 3.6% of the gain, and both halves of the pool agree. A scan that found keeps finding at 6 times the first rate. 5 steps hold 62% of the gain, and 11 of the 15 largest came from the full kick at sigma 0.02 or 0.04. The midm lane already runs a leg after each find. At 19:22 UTC one n with a find of 3e-8 or more had no leg, 875.
- Round 19 certified 969 at 4.628e-04 of score below the round 17 file, 5.277e-05 below every other take. It is two 9-arms on a block corner. The block corner is 0.4 to 1.2 squares under the staircase corner at f = 0.62 to 0.64, and dead from f = 0.68 up and for 9 and 11. It is rigid: the lengths set the side, and it gave a row under the bar on one n.
- The kind sweep of the classfill lane took 0.08 squares from the far zone of 969. A block layout holds that zone four times, so the rebuilt corner moved 969 by 0.0021 of side. 907 is a near miss, 0.000307 of side above the bar.
- The reader for refused layouts is dead: it read 20 of 83, under its line of 30, and its control is red in part.
- **Next:** sweep every far zone that a block corner can hold and rebuild the corners. Then slide rows of the rest beside 969, as one build of 907 did. Then put hops on the staircase corner of 9 and 11, which loses 3.73 and has its best row 0.0102 above the bar.
- Round 20 certified 754 at 1.35e-10 of score below the 754 of the corners lane, which then left their take. At 00:54 UTC it is 4.37e-06 below every other take. Our finds on 803, 810 and 969 went into the take and out again when other lanes went lower.
- A block layout stops where its corner block cannot give way. A local kick followed by the family squeeze passes that stop: on 907 it found the drop of 1.35e-3 of side in 9 tries. A kick with fq does not, because fq does not reach the side of the squeeze.
- **Next:** run the local kick on each family build before its first fq pass. The large steps came only from builds that fq never touched.
- Round 21 certified 549, 813, 869 and 929, for 4.783e-04 of score on the round 19 file and 6.16e-05 under every other take. The polish and harvest lanes took 810, 930, 811 and 698 from our take with one fq quench of our own file. So from 10:18 UTC each run is quenched before it is published.
- The chase of new bar layouts gave the largest steps on fresh builds of the readers lane (929: 5.2e-5 of side). Layouts that the family squeeze built in round 19 or 20 did not move.
- **Next:** quench each find before it is published, and kick each fresh build at once in the lane that built it.

## 19. Round 24 (2026-11-13)

The final take holds 16 counts and gains 0.000151092877637 on the original round 23 candidate.
It gains 0.000322100377394 below the other eligible live takes.
108 production search attempts and 1 finish-only rescues ended on three boxE slots.
The search attempts completed 2657 tries.

### 19.1 Controls and search

The full 907 control passed the squeeze stop at try 4.
Try 9 reproduced side 30.618227092836.
The 180-second probe also passed the stop and completed its certified-input quench.
It did not reproduce the full control drop.

Replay placed ten material fresh/control first moves within 180 seconds.
The 985 join first moved at 337.7 seconds, so joins kept 420 seconds.
New starts without joins or per-try fq received shorter first probes after the control passed.
Saved starts retained their original budgets, and legs kept 420 seconds.
Search and quench shared the 22:15 UTC deadline.

One slot reserved fresh layouts.
Saved 577 initially occupied that slot after the control.
Its early cancellation has a censored trace and no raw result.
The corrected queue gives fresh take and near layouts priority.
New counts get a first pass before further versions, with seed-free inputs first among equal groups.
Two admission places remain available when the pending queue is full.
The near window grew to 0.015 of side.
Exact public handoff paths now feed the queue even when a kick lane owns their count.

35 of 47 eligible saved starts ended.
Four initial inputs failed source checks, and three more lacked exact ancestry.
The saved 978, 599 and 645 snapshots removed 0.000211607, 0.000144773 and 0.000030911 of side.

### 19.2 Source groups and certification

The main session changed the source-group rule at 20:05 UTC.
This lane applied it late and recorded the correction in STATE.txt.
Every retained licence now names its Samanyu seed counts or states that no such seed occurs.
Seed descendants must beat the original candidate.
On twenty held counts, seed-free rows can instead beat the round 22 reference.
Their live comparison also uses seed-free peers.
The reported original-candidate gain stays separate from that permitted-reference gain.

The fallback control accepted a clean row above a fixed candidate bar and below its permitted reference.
Seeded and unresolved copies failed.
A lower seeded peer did not mask the clean row.
The cache control retained identical output, rejected an overlapping file, and restored identical output after repair.
Changed source metadata gives another classification-cache key.
Exact near sidecars preserve upstream notices, including Other terms.

Each published file passed floatsafe at 2.2e-11 and received fq from its certified input on boxE.
Per-n files preceded an atomic replacement of take.tsv.
Final uncached metric and pandas checks covered 16 files.
Minimum clearance was 5.019629156777228e-11.
The bounded 985 search left four raw finds.
A finish-only job certified and quenched them without another search try.
The timed-out 871 quench produced no completed output and stayed out.

### 19.3 Measurements

| Start | Normal runs | Moved by more than 1e-8 of side |
| --- | --- | --- |
| Fresh | 59 | 30 |
| Near | 33 | 4 |
| Leg | 12 | 3 |

The newer 595 fresh build removed 0.000121654 of side.
Its one leg removed another 0.000848757, then ended with 36 dry tries.
The first 985 join removed 0.000069120.
The 542 scan removed 0.000790177 but stayed above the live bar.
4 external live rows retain invent ancestry and are excluded from this take count.

| n | Final score | Gain on original candidate | Source group |
| --- | --- | --- | --- |
| 548 | 0.019746730018 | 3.67027611e-05 | Seed 811 |
| 551 | 0.019071297251 | 9.53896007e-09 | No Samanyu seed |
| 595 | 0.019085039838 | 4.34868615e-05 | No Samanyu seed |
| 599 | 0.018079282848 | -4.07433409e-07 | No Samanyu seed |
| 645 | 0.018346870865 | 1.21710298e-06 | No Samanyu seed |
| 647 | 0.017694836280 | 1.51007285e-06 | Seed 503,504 |
| 699 | 0.017008599046 | 3.85373887e-05 | No Samanyu seed |
| 755 | 0.015671357510 | 6.93985047e-07 | Seed 503,504 |
| 809 | 0.015533702350 | 5.9663393e-07 | Seed 811 |
| 871 | 0.014111171584 | 5.77122989e-06 | Seed 504 |
| 926 | 0.014471005403 | 1.70883512e-07 | No Samanyu seed |
| 927 | 0.014325110459 | 4.26715552e-10 | No Samanyu seed |
| 935 | 0.013063540710 | 9.5706933e-06 | Seed 934 |
| 978 | 0.015381033591 | 6.76644923e-06 | No Samanyu seed |
| 985 | 0.014322617691 | 6.46393214e-06 | Seed 804,983 |
| 990 | 0.013529711478 | 2.35114683e-09 | Seed 811 |

### 19.4 Next

1. Kick fresh shell and join builds first. The newer 595 build and its one leg removed 0.000121654 and 0.000848757 of side. The first 985 join removed 0.000069120.
2. Give a useful new find one leg. The successful 595 leg ended with 36 dry tries, so it received no unchanged extra leg. Other legs are measured separately in the run table.
3. Reconsider 102 eligible pending immutable starts against the next bar. The saved 978, 599 and 645 snapshots removed 0.000211607, 0.000144773 and 0.000030911 of side.
4. Keep 420 seconds for joins. Replay placed the first 985 move at 337.7 seconds. Ten other material fresh/control traces first moved within 180 seconds.
5. Change geometry before repeating the tested near layouts. 4 of 33 normal near runs moved more than 1e-8 of side.
6. Retain exact source-group evidence and read all main handoffs. The delayed 20:05 amendment changed the permitted bar for twenty seed-free counts. Source labels and fallback controls now cover it.

[The run table](../results/invent-r24-2026-11-13.tsv) retains every completed trace and its source records.
[The round tools](../tools/invent/round24/controller24.py) retain the collector, worker and source checks.
Exact starts, pending manifests and proofs remain in take-invent-r24/work.

## 20. Round 25 (2026-11-14)

Three boxE slots follow fresh shell and join builds before saved starts.
New non-join starts receive 180 seconds and joins receive 420 seconds.
Each useful find receives one leg.
The stopped 907 control reproduced side 30.618227092836 at try 9.
Its completed certified-file quench passed both metric reads.
Minimum clearance was 5.019984428145108e-11.
Search starts stop at 02:15 UTC, forty minutes before the final take.
Search and quench share the hard deadline of 02:45 UTC.

The saved manifest contains 112 entries, compared with 102 in the brief.
The first audit admitted 34 and refused 78 on source or side checks.
The second admitted 33 after source and bar corrections.
The backlog lane received the ranked manifest.
Its later claims remove those jobs from the waiting queue.
Every waiting start is ranked against the current base and live peer rows.
A priority audit found 144 stale side deltas before this correction.
A start 0.016 above the bar fails the margin check.
A start 0.001 above it passes.

The strict source walk stores parent nodes once by hash.
Queues retain proof paths rather than expanded source strings.
It resolves archived classfill source proofs only when their input hashes match.
That control accepted original bytes, refused changed bytes, and accepted the restored file.
The final policy also resolves spaced legacy paths and bare filenames with recorded folders.
It reads each module's source and licence separately.
Missing parents, source cycles, and unlicensed roots fail admission.

The source audit withdrew the provisional 985 result.
Its old 921 parent reaches unlicensed merged0 seed 983.
The apparently clean sibling at old 863 does not clear the other branch.
The 863 control passes with its original construction and licensed atlas source.
The actual 985 control fails on seed 983.
A missing-parent control also fails.
All earlier near publications were withdrawn for this audit.
Only files that pass the final source policy return.
Earlier 860 and 911 publications also fail the final source check.
The handoff log records the withdrawal and tells followers to check descendants.
At 01:44 UTC, the take was empty.
Later clean legs at 542 and 922 reached the live bar.

Each count has at most one active search across the three slots.
An equal side alone does not prove that two starts have the same geometry.
The two 921 leg starts differed by only 7.5e-10 in side.
Their best matched centres still differed by 0.1946859, so both remained distinct.
The comparison accepts a translated control and detects a moved square.

Every published CSV must match its boxE receipt hash.
The receipt covers floatsafe at 2.2e-11, both metric reads, and a completed certified-file quench.
Per-n CSVs precede atomic replacement of take.tsv.
The final verifier checks immutable ends without a metric cache.
Guarded cleanup requires a checked CSV transfer before it can remove the lane scratch.
The verifier accepted all 26 admitted end files.
Its separated-square control passed, while overlap and wrong hashes failed.
All 1,077 boxE CSVs matched their copied hashes.
Cleanup found no owned process and removed the lane scratch after acknowledgement.

The first detached worker exited while its search child survived.
The retry uses an absolute script path and a recorded PID.
The first imported quench tool lacked the completion marker required by the worker.
The corrected control certified and quenched saved raw finds without another search.
These failed attempts remain in the logs.

The run table is [invent-r25-2026-11-14.tsv](../results/invent-r25-2026-11-14.tsv).
It separates final source admissions from withdrawn results.
The scripts are in [tools/invent/round25](../tools/invent/round25/).

The final production archive contains 131 completed job records and 1659 logged kick trials.
The final source policy admits 58 of those records, with 57 normal ends.
Near runs produced 23 clean side reductions in 45 normal ends.
Fresh whole layouts moved in 1 of 6 clean normal ends.
Clean legs moved in 2 of 6 normal ends.
Five bounded quench failures produced no published row.

At the 02:33 UTC comparison, 542 and 922 retain score gain 5.16871478728e-07 against the base.
Their gain beyond the other live takes is 4.37935076203e-07.
Both rows match their certified-quench receipts and independent metric checks.
The final comparator reads the latest base and peer files again before the take closes.

Next, kick fresh licensed shell and join geometry, then give each useful find one leg.
Keep 420 seconds for joins.
Change geometry at 812 and 685 before another kick.
Their clean side reductions were 2.949605e-5 and 2.394461e-5.
They still lay 0.00242612 and 0.00255925 above the measured live bar.
Only six saved snapshots pass the final source policy.
Run those after fresh work, with new bars and backlog claims checked.

## 21. Round 26 (2026-11-14)

Three boxE slots follow fresh licensed shell and join builds.
Non-join starts receive 180 seconds and joins receive 420 seconds.
Each useful find receives one continuation.
Search starts stop at 16:55 UTC.
Search, certification and quench share the 17:15 UTC deadline.
The base is round25b, in gate/cand-round25-1114b/details.csv.

Source admission walks recorded parents before a job enters the queue.
Bare filenames resolve through named producer folders and exact source tables.
The control accepts the saved clean 703 shell build.
It rejects the excluded bare 921 ancestor and a missing bare parent.
Unresolved parents and unlicensed seed descendants stay out.
Old completed geometry stays closed unless the input changes.

The collector reads handoffs and fresh takes, then pauses for 35 seconds.
A completed boxE receipt permits immediate publication before the full archive audit.
Each receipt binds the final file hash and the certified input used by fq.
Per-n files precede an atomic replacement of take.tsv.

The scripts are in [tools/invent/round26](../tools/invent/round26/).
The measured run table will be [invent-r26-2026-11-14.tsv](../results/invent-r26-2026-11-14.tsv).

The 907 control reproduced side 30.618227092836 at try 9.
Its certified-file quench completed at 12:58:11 UTC.
Minimum clearance was 5.019984428145108e-11.

Hash-bound origin snapshots supply recorded roots for archived rectangle inputs.
The controls accept the fresh 365, 489 and 580 closures.
Changed proof hashes, changed snapshot bytes and the old 921 tree fail.
The archived 847 export resolves to its existing local-parent proof only when both files have identical bytes.
Pinned parent groups select actual donors before inherited notices.

Fresh backlog claims match the count and exact input hash prefix.
The control skips the claimed 365 bytes and admits changed bytes or another count.
Saved starts remain below fresh work.
Four of six saved clean starts passed the current bar and full source checks.

The independent source walk found a gap in the local graph.
External proofs retained pins to parent paths whose bytes changed or disappeared.
The local graph kept the source notices and missed those pins.
The independent walk rejected provisional 910 and 972, which were withdrawn.
It accepted the distinct module chain at 748 and the 805 and 934 rows.
The gate now runs quench_walk.py before publication and final selection.
It caches checked file timestamps and invalidates results when withdrawal notices change.

The compact monitor initially watched only main and addressed notices.
It missed withdrawals that other lanes sent to all.
The corrected monitor reads withdrawal notices from every lane.
The source gate also checks the producer's withdrawal records.
64 earlier near files moved to a private hold directory pending that gate.
The proven near parent for the accepted module chain remains available.

### 21.1 Final measurements

215 production jobs completed with 4325 logged kick trials.
4 certified-input quenches reached their bounds and stayed unpublished.
The movement totals in the run table use the initial local source admission.
They include provisional rows that the later independent walk excluded.

Uncached boxE verification accepted 10 candidate ends.
The separated-square control passed.
Overlap and changed receipt hashes failed.
Minimum clearance was 5.01962915678e-11.
All 1,249 boxE CSVs matched their copied hashes.
All owned processes stopped before the lane scratch directory was removed.

| n | Certified score | Gain on round25b | Gain below other live takes |
| --- | --- | --- | --- |
| 328 | 0.026987542959049 | 0.000719949048198 | 0.000117673023082 |
| 805 | 0.016561519770223 | 1.0390684535e-05 | 1.31186644192e-06 |
| 934 | 0.013177706693147 | 4.41192327116e-09 | 4.41192327116e-09 |

The comparison at 2026-11-14T17:08:17Z retains 3 rows.
Gain on round25b is 0.000730344144656.
Gain below other live takes is 0.000118989301447.
Sources and licences remain in take-invent-r26/take.tsv and the named ancestry proofs.

The 328 start was a licensed border window from a newer 365.
Its final kick and quench shortened side by only 7.23828819105e-9.
The new window accounts for most of its gain.
The retained 805 module follow shortened side by 3.7219567254e-5.
The retained 934 continuation shortened side by 4.22586197146e-8.

Next, certify fresh licensed border windows and kick changed module geometry.
Keep the independent source walk before either step.
Reprice 570 unstarted immutable inputs against the next bar and exact backlog claims.
Require changed geometry before another run of a completed dead end.

## 22. Round 27 (2026-11-14)

Three boxE slots run the local kick and the required quench.
Search starts end at 23:25 UTC.
Search, certification and quench share the hard deadline of 23:45 UTC.
The take closes at 23:55 UTC.
The bar comes from round27-briefs/bar27.tsv and every live round 27 take.

Samanyu ancestry is permitted this round.
The source checks retain the other exclusions and reject unresolved parents.
The prvsiyan test rejects a share of 0.4 or more within 1e-3.
An exact excluded 907 measured 1.0 and failed the control.
The original construction of 907 measured 0.3627342888643881 and passed that cutoff.
Its kick reproduced side 30.618227092836 at try 9.
The certified-file quench completed with clearance 5.019984428145108e-11.

Each admitted input receives a byte snapshot and a hash.
The full source walk also retains its records and parent snapshots.
Publication checks those frozen bytes and later source withdrawals.
A producer rewrite therefore remains distinct from the version admitted earlier.
Archived invent outputs resolve through exact job records and completed receipt hashes.
Missing unrelated parents remain deferred.

boxA reached load 101.16 during the initial audit.
A full archive scan and repeated historical ledger scans delayed the first queue.
The resolver now uses exact job lookups.
Native thread pools use one thread.
Every admitted job is checkpointed before the next source walk.

The scripts are in [tools/invent/round27](../tools/invent/round27/).
The run table is [invent-r27-2026-11-14.tsv](../results/invent-r27-2026-11-14.tsv).

The initial scan admitted five saved sources per pass.
That still delayed dispatch while the collector read hundreds of fresh near files.
Each pass now audits one saved source and at most two fresh or near sources.
Source graphs have a 30-second cap, and the independent walk has a 120-second cap.
Larger trees remain deferred.
A separate bounded audit recovered one complete 328 source record.

Withdrawal controls accept actual count withdrawals and reject narrative references to withdrawn floors.
Exact hash reinstatements cancel earlier temporary withdrawals.
Every queued start currently matches its frozen input hash.
A producer rewrite during the full audit now defers the candidate.

The finalizer imports its source tools before the search cutoff.
It reuses those imports for the final comparison, then freezes the take at 23:51 UTC.
The report writer refuses to write before 23:55 UTC.

### 22.1 Closing measurements

19 production jobs completed 241 kick trials.
The stopped 907 control is separate from those totals.
A move in this table means more than 1e-8 of final side.
The table records initial source admissions.
The later complete-ancestor audit excluded the 910 tree.

| Input | Jobs | Normal ends | Moved |
| --- | --- | --- | --- |
| Saved | 10 | 9 | 3 |
| Fresh | 2 | 2 | 1 |
| Near | 3 | 3 | 0 |
| Continuation | 4 | 4 | 1 |

One certified-input quench of 997 reached its 240-second bound.
It supplied no published row.
Every published result had a completed quench from its certified input.

The fresh 860 follow shortened its start by 1.4594332142792155e-7 of side.
Most of its gain against the bar comes from the upstream twoshort layout.
The saved 910 scan shortened side by 0.0026190850541567556.
Its one continuation added 2.7830080963298087e-5 and still missed the live bar.
Both 910 near files were withdrawn after their complete n684 ancestor measured prvsiyan share 1.0.
They remain under work/withdrawn-near and must not supply another build.
The ten available complete CSV ancestors of retained 860 all passed.
Their maximum share was 0.026058631921824105.

Uncached verification accepted one candidate with native and pandas reads.
Its minimum clearance was 5.019629156777228e-11.
Separated squares passed the control.
Overlap and changed receipt hashes failed.
All 117 boxE CSVs matched their copied hashes.
All owned boxE processes stopped before cleanup removed the lane scratch at 23:26:37 UTC.

The comparison at 2026-11-14T23:54:16Z retains 1 row.
Gain against the round 27 bar is 3.17340901179186e-06.
Gain below the other live takes is 3.17340901179186e-06.
The source gate now tests each available complete CSV ancestor before admission and publication.
Its control rejected the excluded 684 donor at share 1.0 and accepted the ten retained 860 ancestors.

## 23. Round 28 (2026-11-15)

Three boxE slots follow changed shell, join and rectangle layouts.
Round 27 supplied one retained row at 860.
That follow shortened its fresh input by 1.45943321428e-7 of side.
Fresh geometry therefore runs before saved starts.
Non-join starts receive 180 seconds and joins receive 420 seconds.
Each useful find receives one continuation.
Search starts stop at 05:25 UTC.
Search, certification and quench share the 05:45 UTC deadline.
The take closes at 05:55 UTC.
The report writer refuses to run before that deadline.

Each queued input has an immutable byte snapshot and a SHA-256 hash.
A complete source walk pins the available records and CSV ancestors.
The initial source control measured share 1.0 on the archived 684 donor.
The exact excluded 907 also measured 1.0.
Our original 907 construction measured 0.3627342888643881 and passed the share cutoff.
Retention notes remain distinct from withdrawal notices.

The main-session handoff changed the source rule at 00:19 UTC.
Numeric similarity no longer excludes our own layouts or their descendants.
The share cutoff applies to fetched public rows.
Literal ancestry to the forbidden public file remains excluded.
The own-source walker disables both complete-ancestor and original-seed numeric gates.
Held 801 is allowed under the updated rule.
Source controls distinguish own ancestors from fetched public inputs.

The two frozen 910 near files were withdrawn only for ancestor similarity.
Exact copies now sit under work/reinstated in the current take.
Their complete source walk passed under the updated policy.
The new 910 probe uses per-try fq after the squeeze and seed 281.
That changes the repair from the previous plain-squeeze continuation.
No frozen take directory was changed.

An exact staircase build record resolves the old 863 parent.
Its raw CSV and the named near CSV have identical bytes.
The control accepts those bytes and refuses changed bytes or a different count.
Each module retains its separate source and licence.

The initial collector imported current round 28 rows and untested round 27 rows.
At 00:45 UTC, current rows and fresh near layouts took priority over old table walks.
It reads fresh near files in newest-first order.
An exact-hash ledger keeps 361 completed historical inputs closed.
The initial repriced saved shortlist had 65 exact untried inputs.
A later canonical audit read 609 completed starts and closed 603 distinct geometries.
Each pass audits at most one saved source and two current sources.
At least one current-source place is reserved for a fresh near layout.
CSV and source bytes define the intake cache key.
Producer rewrites of identical bytes no longer force another source walk.
The source graph and full walk retain their 30-second and 120-second bounds.
The three workers and finalizer use deadline files and survive a lost session.

The scripts are in [tools/invent/round28](../tools/invent/round28/).
The measured run table is [invent-r28-2026-11-14.tsv](../results/invent-r28-2026-11-14.tsv).
Closing measurements follow after final verification.

The retired harvest 793 row resolves through its exact captured ledger.
Its certified input hash is 9f87f0f65f1d0079e409bcf0e3df673f9c023da9ffd88e9439fce01da36bd211.
The source and licence match that ledger row exactly.
The recovery control accepts the archived row and refuses changed pins or a different count.
This repairs a missing producer record and retains the complete source gate.

The first fresh 499 scan shortened its input by 2.9559749e-6 of side.
It briefly held a row 6.8133729e-6 below the bar.
A lower live peer superseded it.
The changed-repair 910 scan completed its certificate and quench above the bar.
It receives no unchanged repeat.

The wider-kick control shortened 907 to side 30.6182270884610.
Its completed certified-file quench had clearance 5.01980679246e-11.
The changed profile uses radius 5, sigmas 0.01, 0.02 and 0.04, and separation repair 0.08.
Eight production runs made 946 trials and no side reduction above 1e-8.
That profile receives no unchanged repeat.

A second selector restricts kick centers to an orientation junction.
The selector measures local angle diversity and chooses a box around its highest score.
Its 907 control made eight raw finds and reached side 30.6182270928362.
The certified-file quench had clearance 5.01998442815e-11.
Up to eight distinct admitted geometries receive this changed selector.
Four completed production runs have made 1,352 trials with no material move so far.

The current 982 row is 7.90593265743e-7 below the round 28 bar.
It comes from the source-cleared classfill input and the changed per-try fq repair.
Its own side reduction is only 1.14937392937e-10.
Nearly all of its gain therefore comes from certifying the upstream geometry.
The final peer comparison can still remove this provisional row.
A direct finish queue now certifies competitive admitted inputs even when their search finds nothing.
Each such input still needs a complete source walk and a completed certified-file quench.

Verified origin records now take priority over weaker inferred metadata.
Their input hash, count and full-proof hash must match.
Numeric comparison fields are diagnostics and do not create ancestry roots.
The actual 416 control changed from three inferred roots to one recorded root.
Changed bytes and a different count failed.
A separate archive adapter recovers missing public-certifier credit from its exact published row.
A different source, count or producer path fails that control.
Other upstream terms retain the source names from the held packing.

The canonical held 801 passes both source walks under the updated ownership rule.
A direct forbidden public-file record still fails.
An unrelated held 802 record remains unchanged.
Raw fetched public inputs retain their numeric share gate.
Explicit original Samanyu source records pass the ownership control.
The ancestry graph used for publication is its captured content-addressed copy.
All 70 queued source graphs had a captured copy at the checkpoint.
The retained 982 graph passes.
Replacing that graph with unrelated JSON fails.

At 03:39 UTC, 60 production jobs had completed.
Fresh, saved and changed-repair runs remain distinct in the measured table.
Movement totals describe local source admission and do not replace the final full source check.

The withdrawal adapter also reads explicit source holds with bare near-file names.
A changed live path cannot clear an older captured version.
Snapshots written after a hold remain separate when their recorded timestamp proves the order.
An explicit hash applies only to its matching bytes.
The six version controls pass.

The final selector now tries valid alternatives in score order.
A lower result with a failed source proof cannot hide a higher valid result.
The real 982 fallback control passes, and an all-invalid group fails.
Uncached verification covers every competitive certified end.
Five ends across 499, 982 and 971 qualified at the checkpoint.

Explicit stair-c proof references now expand through their recorded hashes.
The control follows a valid record and refuses a wrong hash or missing record.
The fresh 933 diagnostic reached 119 nodes after this change.
It still had real missing parents and an ancestry cycle, so it supplied no numerical job.

The next changed probe uses a junction walk with tolerance 1e-6.
The round 20 global walk at 1e-4 returned to an older basin in 38 trials.
The probe restricts centers to a junction and reduces the allowed worsening.
A real 907 control must pass before up to four production runs can start.
Fresh source-cleared layouts retain queue priority.

Published-row references now retain their historical round.
The previous parser used round 23 for an unversioned held reference inside an older table.
The actual round 10 record for 756 now follows round 9, then round 8.
An implicit held reference must match the exact published source text and count.
Changed source text, the wrong row and a record outside the published tables all fail.
This resolves the source version without substituting another packing.

The first four tight walks improved two prior results on their exact inputs.
They added 4.12260657434e-5 of side reduction at 922 and 9.54097693295e-7 at 508.
The 299 result reproduced its old floor, and 921 found no raw result.
This measured yield expanded the profile to eight distinct starts.

The new 922 near result received one plain-squeeze continuation.
That continuation reached side 30.821388414217356 and score 0.015048369694771191.
Its gain against the round 28 bar is 9.4407244644e-7.
It completed the certified-file quench with clearance 5.01962915678e-11.
Its full frozen source check passed before publication.
This is a new geometric improvement.
The provisional 982 row still mainly restores upstream geometry.
Both rows remain subject to the final peer check.

Two layouts that moved under the plain squeeze now receive the controlled tight walk once.
They are 922 and 707, each copied as a new byte snapshot with a new full source walk.
This changes the mechanism on improved geometry and caps the extra follows at two.
It uses the completed 907 control and keeps fresh layouts first.
All new starts still stop at 05:25 UTC.

The retained 922 source graph has 22 nodes and 25 pinned files.
Its Other root is alexchilton/squares-in-squares-starter-kit, data.zip!best_current.csv.
It is reached through held 984 of round 9, as the held-packing exception permits.
The upstream name was initially present only in the source cell.
The formatter now names that Other source in the licence cell too.
The actual 922 credit control passes, and the unrelated 982 licence text stays unchanged.
Each job's side reduction is relative to its own start.
Those totals can reproduce earlier gains and must not be added as score gains.

The second fresh 993 follow completed its certified-file quench.
It shortened the midm input by 3.63068318521e-6 of side.
Its score is 0.012932452828232632, with gain 7.37482335866e-7 against bar 28.
Part of that bar gain comes from its upstream input.
The earlier 993 quench reached its 240-second limit and supplied no published end.
Its certified input was handed to the quench lane.
The timeout left no orphan numerical process.

All three boxE slots finished before uncached verification began.
Uncached checks accepted nine competitive files with native and pandas reads.
Their minimum clearance was 5.01962915678e-11.
The separated-square control passed, while overlap and a changed receipt hash failed.
All 409 boxE CSV copies matched their manifest hashes.
Owned boxE scratch was removed at 05:33:12 UTC after that transfer check.

Publication retains the captured source walks and verifies their immutable pins.
It rereads current withdrawal logs without rebuilding the unused historical ancestry index.
The comparison at 05:33:21 UTC retains 922, 982 and 993.
Its base-bar gain is 2.47214804805e-6 and its gain beyond live peers is 1.64613850817e-6.
The final peer and source comparison remains scheduled for 05:54:35 UTC.
The report still waits until after 05:55 UTC.

The tool host restarted after cleanup and killed the waiting finalizer and monitor.
The revive ledger control passed at 05:47:37 UTC.
This run has no agent workflow records, so the saved receipts supply the lane ledger.
Searches and quenches are done, as are uncached verification, transfer and boxE cleanup.
Only the final comparison and report remained unfinished.
The replacement close28.py became ready at 05:47:05 UTC.
It resumes those two steps and starts no numerical job or new source walk.
The ready marker and process check prove that completed stages were not replayed.

The final closer is close28-v2.py.
It refreshed peers and warmed source reference data at 05:49:29 UTC.
That refresh retains three rows with the same verified files.
The final timed check can reuse the warm data and still reread current withdrawal logs.
The original closer was stopped before it wrote a final comparison or report.

The revive ledger at 2026-11-15T05:52:44Z still has no workflow reruns.
The three completed lane units remain done, and only the timed closer is running.

Final comparison: 2026-11-15T05:54:35Z.
Retained counts: 922, 982, 993.
Gain against bar 28: 2.472148048049405e-06.
Gain beyond the other live round 28 takes: 1.646138508171191e-06.
The report was written at 05:55:05 UTC, after the deadline.
The restored closer ended, and no owned background process remains.

## 24. Round 29 (2026-11-15)

Three boxE slots follow fresh layouts and the measured round 28 next list.
Tight junction walks run on inputs that moved under the ordinary squeeze.
Each useful end receives one plain continuation.
The unchanged dry end walks at 922 and 707 remain closed.
Wide kicks and ordinary junction kicks also remain closed.
Their round 28 trials produced no material move.

Every unstarted fresh design receives one 900-second run.
Early non-rectangle screens used 180 or 420 seconds.
The run table retains those actual durations.
Each queued input has a byte snapshot and a SHA-256 hash.
The imported border finesafe tool bisects the dilation used for certification.
Every published file still requires a completed quench from its certified input.
Native and pandas metric reads must pass, with clearance at least 2.2e-11.

The source controls keep owned layouts separate from fetched public rows.
Our layouts and their descendants have no numeric share gate.
Actual forbidden public ancestry remains excluded.
Withdrawals apply to the captured versions they name.
Source controls pass for retention notes, actual withdrawals and public-source classification.
The geometry history control accepts translation, reflection and quarter turns.
A moved square produces a different key.
The history closes 672 distinct geometries from 714 completed starts.

A separate experimental kick moves a connected domain by one rigid transform.
It preserves internal contacts while the squeeze repairs the domain boundary.
The algebra control preserves pairwise distances and changes positions and angles.
Different orientations remain outside the selected domain.
Production use requires a numerical control on the stopped 907 packing first.
This changes the movement mechanism before another kick experiment.

Search admission stops at 11:20 UTC.
Search, certification and quench share the 11:45 UTC deadline.
The final take closes at 11:55 UTC.
The report writer refuses to run before that time.
Restartable workers and local drivers retain deadline files and progress receipts.

The scripts are in [tools/invent/round29](../tools/invent/round29/).
The run table is [invent-r29-2026-11-15.tsv](../results/invent-r29-2026-11-15.tsv).

The initial 907 search reached side 30.618227092834 before certification.
Its fine dilation failed the pandas clearance assertion, and it supplied no published row.
Certification now checks both clearances and falls back to the ladder when needed.
The retry uses the saved raw find and repeats its certified-file quench.
The rigid-domain control independently reached the same smaller basin at try 3.
Production still waits for a completed certified-file quench.

Both 907 controls completed their certified-file quenches.
The saved tight-walk find passed with clearance 5.01998442815e-11.
The rigid-domain result passed with clearance 5.01962915678e-11.
The first fresh 749 scan shortened side by 0.00286253484403 and remained above the bar.
The first saved 963 and 906 scans returned no raw find.
Tight walks now precede saved starts while fresh layouts retain priority.

The round 8 held 756 record resolves through the retained round 7 polish.
Every numeric coordinate matches its gathered round 8 packing exactly.
The gate score matches the polish result, and the polish start matches its public ledger row.
Wrong counts, rounds, file hashes and producer rows fail the recovery control.

Exact frozen output copies can retain an older complete source proof.
Those copies now take priority over a recipe that points at a rewritten producer path.
The fresh 421 result passes both source walks after this correction.
Changed bytes and a different count fail alias selection.
The source reader also accepts an explicit Couzo MIT original and still refuses an unknown root.
Other missing parents continue to exclude the actual 503 follow.

Legacy gathered references now require their accepted gate file and exact CSV hash.
The versioned source row must match the per-count gate score within 1e-10.
This allowance covers the existing certification padding, including 338 at 4.8621e-11 of score.
Wrong file hashes, filenames and counts fail the control.

Compact source proofs retain a captured historical table when its source cells match exactly.
The 454 chain repeated the same source text in rounds 18 and 17.
Each version now has its own graph node and follows its own earlier held record.
The actual fresh 454 passes both complete source walks.
Wrong counts, source text and licence text fail the record control.
A real two-file metadata cycle also fails.

An early queue checkpoint briefly reintroduced a claimed 991 input.
That exact numerical child was cancelled after the backlog claim was confirmed.
Both queue filters now omit claimed inputs.

The next controlled profile combines rigid-domain motion with a walk tolerance of 1e-6.
It starts from moved certified ends and permits one end per count, at most six counts.
Its 907 numerical control must complete certification and quench first.
Ordinary domain kicks reproduced the 539 plain-squeeze floor and timed out once at 906.
Four completed plain continuations produced no raw find at the checkpoint.
This profile changes the acceptor before those ends receive another experiment.

The current-round claim parser now reads round 29 identifiers.
Its control matches the actual 991 claim and refuses different bytes.
Early checkpoints and final queues use the same priority order and claim filter.
The handoff scanner also reads current-round work paths.
A compact harvest wrapper hid the join origin of 454 from the duration selector.
The selector now reads its admitted source graph and preserves the 420-second join budget.
At most two already-dry short joins receive that corrected budget.

The main handoff identified a false exclusion for three clean 858 readers donors.
The local source adapter now names only the actual 745/858 join identifiers.
Its control accepts those readers donors and rejects the actual joins.
The exact 01:51:44 withdrawal reason is discarded during a new complete source walk.
Actual forbidden ancestry still fails that walk.
Other withdrawals retain their version and hash checks.

The independent public-share reader measures 0.6514423076923077 on the archived public 416 control.
It rejects that input at the 0.4 cutoff, including during publication.
An ownership fixture with the same bytes retains no numeric gate.
The actual public 907 input and final file both have share 0.0.
Its recorded licence is Apache 2.0.

The provisional 641 and 907 rows no longer count.
A better peer superseded 907.
The 641 rectangle kick shortened its input by 0.000487716774476 of side.
A plain continuation shortened another 2.8956015967e-6.
Its exact 591 ancestor was withdrawn after a public-source audit.
A separate trace confirms a recorded public 498 root with share 1.0 against 1105.
The owned 641 layout itself receives no numeric share test.
Its gain and descendant near files are withdrawn.

The public-root reader checks captured source bytes and source metadata.
It compares only nodes recorded as first fetched from a public source.
An owned fixture passes with the share function forced to fail.
The public 416 control fails at 0.6514423076923077.
The actual 907 public roots pass with Apache 2.0 credit.
Queued sources are checked again when policy or withdrawal records change.
Affected numerical children are cancelled without stopping their workers.

The six small rigid-domain walks found only a tiny move at the withdrawn 641.
The next control uses radius 8 and angular noise 0.15 times the translation noise.
This expands the contact-preserving patch and keeps the 1e-6 walk acceptor.
At most four source-valid counts can follow a successful numerical control.

The quench handoff exposed held inputs outside its claimed set.
Counts 924, 377, 920 and 808 passed the initial source walks.
Their geometries are absent from the completed-start ledger.
Each now has a 900-second kick queued from a byte snapshot.
The known 758 geometry remains closed.
Other candidates with missing parents remain out for that separate reason.
The public-source control also preserves an ancestor across a later path rewrite.
Changing its captured bytes fails the check.

The radius 8 control shortened stopped 907 by 0.00135359125104 of side.
Its certified-input quench passed at clearance 2.20019558128e-11.
The four production counts are 991, 499, 457 and 376.
Every slot now follows the same priority order.
This lets original seeds and changed domain experiments reach any free slot.

The original 920 run timed out after its bounded 1000 seconds.
Its saved raw file beats the bar by only 4.91434e-11 of score before certification.
It cannot meet the required improvement of more than 1e-10.
A future timeout with a competitive saved raw file receives certification and quench.
That uses the zero-search path already exercised by the recovered 907 control.
Repeated source failures pause only identical CSV bytes for five minutes.
A changed CSV bypasses that pause.

The producer's original-seed label was wrong for the held 377 and 808 rows.
The historical angle-harvest table identifies their actual public source.
The held-record adapter now reads that table before the older public baseline.
For 377, the table score matches the held bar exactly.
Its actual archived public input has share 0.33687002652519893 and Apache 2.0 credit.
The notebook's own source table names the malyshevdanil living-atlas input.
The corrected take credits both and preserves the packing bytes.
No share test was applied to the held or output packing.

The archived public 808 input has share 0.6571782178217822 and fails the source rule.
That public-derived held run was cancelled.
A separate rebuild starts from the actual owned 808 seed in samanyu_bestfit.csv.
It has different input geometry and was absent from the completed ledger.
Both source walks accept it without a numeric share gate.
Its 900-second search is queued with an immutable input hash.
The public-root control also runs the actual owned seed with share forced to fail.
It passes without calling that function.

The fresh 988 follow shortened the border input by 0.000235816422801 of side.
Its input-to-output score reduction is 7.5023198344e-6, including the certified-input quench.
The provisional gain against the round bar is 5.1475778251e-5.
The upstream border construction supplies the rest of that bar gain.
The source check accepts its complete 30-file snapshot.
One plain continuation follows the useful new end.

The four radius 8 production runs produced no score win.
Only 991 moved more than 1e-8 of side, by 8.50429842103e-8.
The actual owned 808 rebuild shortened side by 3.69089192986e-7 and stayed above the bar.
A final test rotates that entire packing while preserving its internal geometry.
Its rotated two-square control fell from 2.11285708624 to 2.0001 before quench.
The control preserved pair distances and kept an already optimal packing unchanged.
It also completed the certified-input quench.
The owned 808 test selected rotation zero and produced no smaller file.
This closes the whole-packing rotation test for that geometry.

Historical source rechecks briefly left two numerical slots idle.
The controller now checks active and next-to-run jobs first.
It refills queues from complete current checks while older archive checks continue.
The early dispatch log confirms the accepted inputs before their searches start.
Published source cells also link the immutable supplemental public-source receipt.

The last 499 rectangle job beat the round bar by 1.90214917595e-7 of score.
It shortened its new input by 0.000161180511871 of side and completed certified-input fq.
Earlier 499 walks and domain runs had stayed above the bar.
The new rectangle geometry produced 24 raw finds during its 900-second run.
The 988 plain continuation produced no raw find, and a rebuild peer passed its provisional row.

All boxE workers ended by 11:32:12 UTC.
Uncached native and pandas verification accepted nine source-valid candidate files.
All 515 copied boxE CSV files matched the manifest before scratch removal.
A partial 454 file exposed a missing completed-score guard in the final reader.
That reader now rejects incomplete and NaN receipts before comparing scores.
Its controls accept a completed receipt and reject those incomplete receipts.
The finalizer resumes from saved progress after removal and leaves the collector stopped.
Peer comparison uses strict lower score and retains the 1e-10 base-gain threshold.
The final source and peer comparison still runs just before 11:55 UTC.


## Round 30 (2026-11-15)

Fresh rectangles and joins receive the first search slots.
Round 29 source-valid rectangles moved in 17 of 23 normal jobs.
The final new 499 geometry crossed the bar after older 499 starts stayed above it.
Completed geometry stays closed, including the dry rigid-domain and whole-packing profiles.
The history reader records 805 completed immutable starts and 743 distinct geometries.

[The round 30 tools](../tools/invent/round30) retain the frozen source graph and byte pins.
The source controls preserve retention notes and reject changed pins.
The public 416 fixture fails at share 0.6514423076923077.
The owned fixture passes with the share function forced to fail.
Historical 756 resolves only with its matching round and pinned hashes.
The completed-receipt control rejects missing and NaN scores.

The original stopped-907 control completed its certified-input fq.
Its side reached 30.618227092834 and its clearance is 5.019984428145108e-11.
The new bar-side wrapper compresses only the initial centres and preserves square angles.
Its algebra controls reach the requested side and retain already smaller inputs.
Its numerical stopped-907 control must pass before production uses that wrapper.
The older tool's `--bar` option only labels the reporting target.
This wrapper changes the actual initial side.

Three boxE slots share the 17:45 UTC hard deadline.
Search admission closes at 17:20 UTC to reserve quench and verification time.
The collector publishes each certified result before the final batch audit.
The finalizer refreshes sources and peers before 17:55 UTC and writes the report after that deadline.

The compressed-side numerical control also passed its certified-input fq.
Its clearance is 5.019629156777228e-11.
Measured moving round 29 ends can now receive this changed initial-side mechanism.
The first two admitted counts are 376 and 539.
The ordinary fresh-rectangle queue retains priority over these older ends.

The stored-walk prototype omits diagnostic traces only beside an explicit CSV source edge.
It preserves that edge and keeps evidence attached to unresolved sources.
Its full 640 source check still fails at the historical source cap.
That input remains deferred, with no recovered result.

The [run table](../results/invent-r30-2026-11-15.tsv) records the queued jobs and their completed receipts.

The first 500 rectangle kick shortened side by 4.7811369828565375e-5.
It completed its certified-input quench and stayed above the bar.
Compressed-side retries of the 376 and 539 ends gave no raw find in 395 logged tries.

A separate prototype uses a random objective in the contact LP at a fixed side.
The family squeeze then repairs the proposal.
This explores contact directions instead of independent Gaussian perturbations.
Its small control moves a legal pair and rejects coincident squares.
A stopped-907 numerical control is queued before any production use.
The queue now preserves pending controls during source refresh.
A dispatch control accepts numerical controls and blocks unproved contact-LP production.
Cleanup checks the controller command before sending a signal to its recorded PID.

The main 12:40:55 UTC ruling makes held descendants owned layouts.
Numeric shares no longer gate owned inputs or held ancestors.
Own-first 376 and held 598 pass with the share function forced to fail.
Both also pass with stale public-first labels in the saved evidence.
Fetched public 416 still fails at share 0.6514423076923077.
Literal forbidden-source checks and all byte pins remain active.

The 641 recovery uses the original complete 192-pin source walk.
A fresh path walk expanded unrelated later plan entries and reached the cap.
The frozen walk binds the earlier source bytes and the worker endpoint receipt.
The captured 498 transport origin supplies the missing Apache 2.0 notice.
Its source is jazivxt/boxed-in-sub through the recorded held packing.
That resolves the duplicate transport notice without a numeric share gate.
Only the exact 591 parent bytes implicated by the superseded gate were reinstated.
An altered input hash fails the recovery control.
The new certified-input fq kept score 0.018867152281702104 at clearance 2.2001178656694265e-11.
The provisional bar gain is 1.1586797161733386e-6.
Publication followed its completed quench by 67 seconds.
Backlog claimed the published bytes, so this lane skips the duplicate follow.

The five compressed-start retries gave no raw find below the bar.
The next acceptor keeps the original legal side as its best baseline.
It can retain a legal improvement above the bar and continue from that end.
Its two-square control records side 2.000000000200 above the deliberately impossible 1.99 target.
The control completed certified-input fq.
A separate stopped-907 control must also pass before production.

The contact-LP control produced 18 raw improvements and completed certified-input fq.
It shortened the stopped start without reaching the earlier deep basin.
The first production run, 376, was dry.
The second, 539, is still measured separately.
A program-label race in early dispatch affected the dry 594 job.
Credit and measurements now use the actual worker receipt.
Both mismatched-label directions pass their controls.
The stale duplicate zero-search rescue ran once and returned identical 641 bytes.
Further zero-search duplicates are disabled.

The first legal-baseline stopped-907 control accepted padding and missed the deep basin.
The revised acceptor ignores steps below 1e-7 of side while above the bar.
It retains the 1e-9 threshold below the bar.
Both the pair control and the revised stopped-907 control passed certified-input fq.
The revised 907 side reached 30.618227088461005.
Two matched-input trials then retained improvements that the old bar baseline had discarded.
The 539 trial shortened side by 2.7093832063229684e-5 in 110 tries.
The 598 trial shortened side by 3.709966662768238e-7 in 205 tries.
Both stayed above the bar.
The two production contact-LP trials were dry in 559 tries.
That unchanged profile is closed.

The main 13:32 UTC clarification applies ownership to each source path.
A held parent exempts only the ancestry reached through that parent.
A direct public parent still needs its own licence and numeric share check.
The new reader cuts held paths while preserving direct public siblings.
Its held-only fixture and actual 641 pass with the share function forced to fail.
A direct 416 sibling fails at share 0.6514423076923077.
Named direct 695 and 799 fixtures also fail beside a held sibling.
Their held-only paths pass without a share call.
An allowed public 907 passes with Apache notices bound to its frozen bytes.
Removing its public byte pin fails even while the live file remains present.
The completed 539 and 598 trials also pass the revised source check.
The 446 ancestry still lacks two explicit public transport licence notices.
Those rows remain withheld, and no 446 row was published.

Some compact origins leave a parent source blank and name a proof for another count.
The exact-root resolver reads that frozen parent's own record.
It rejects the wrong count, a wrong hash, and a current-round replacement.
An older reopened-held record can take its terms from its exact accepted held parent.
Historical record cycles still need a path to a real source root.
A closed cycle and a cycle whose only anchor was refused both fail the controls.
The source reader also imports harvest30's selected-donor resolver.
It pins the full reader state and follows only the named donor.
Wrong donor-credit and packing hashes fail.

The current 376 closes after those metadata fixes.
Its full frozen walk has 248 pins.
Its branch audit follows the explicit graph once.
An own root's sidecar no longer opens a second raw route around that graph's held cuts.
The direct-public sibling and missing-pin controls still fail as required.
The held-only 641 and allowed-public 907 controls still pass.
This establishes source admission and does not count as a numerical gain.

Intake records the actual ledger or named metadata file as the source record.
This avoids making a current output CSV its own source record.
Exact claims are checked before source walks.
Queue admission also suppresses an unstarted duplicate with the same input and numerical options.
The first fresh 376 trial was admitted after the full source controls passed.

Fresh rectangle inputs take priority over module variants with unresolved historical records.
Useful ends receive another controlled continuation while each completed step gains at least 1e-9 of side.
The 17:20 UTC admission deadline still applies to those continuations.

Continuations use the same proven legal-baseline acceptor as fresh starts.
This retains progress from an improved end that still lies above the bar.
The original bar-baseline runs had discarded such legal progress.

The fresh 376 and 702 bar-entry trials were dry.
The 547 rectangle shortened side by about 1.09e-7 and completed certified-input fq.
Its score finished 9.992007221626409e-15 above the bar, so it adds no score gain.
The 234 rectangle shortened side by 0.00031066804 and completed certified-input fq.
It remains above the bar and has a continuation queued.
Source refresh skips completed dry or failed jobs without a certified end.
Pending jobs, active jobs, and completed certified ends retain the full current source check.

Self-follows can now extend the complete frozen input walk.
The helper verifies every prior pin before adding the endpoint and worker receipt.
It also binds the certified input and the completed fq marker.
The original source graph stays intact beneath a new own operation.
Current source policy still checks every direct public path.
The full 547 and 234 controls retain 63 and 18 prior pins.
Wrong endpoint, quench-input, parent-evidence, and count identities fail.
Unfinished and NaN receipts also fail.
Replaying the extension produces identical evidence.
This applies the 641 recovery method to future numerical endpoints without reopening live producer paths.

The older 539 trace contains 41 legal steps between 1e-8 and 1e-7 that the coarse acceptor discarded.
The largest is about 8.68e-8 of side.
The 598 trace contains one such step of about 3.03e-8.
A finer profile lowers only the above-bar threshold to 1e-8.
It still rejects the measured 6.07e-9 padding step.
The below-bar threshold stays at 1e-9.
Both the pair and deep-907 controls passed certified-input fq.
The 907 clearance is 5.019629156777228e-11.
A separate queue control blocks unproved production and preserves numerical controls.
Two 900-second trials start from the prior certified 539 and 598 ends.
Their complete source walks extend through the verified endpoint receipts.
Those starts differ from the earlier matched-input trials.
Fresh source-valid inputs retain priority over these two trials.

The finer 539 trial shortened its certified start by 8.807962359469457e-8 of side.
It remains above the bar.
The finer and coarse 598 trials were both dry.
The 539 coarse reference hit its 1,000-second watchdog after only 15 completed tries.
That comparison is inconclusive.

A separate retention version saves smaller candidates without changing the coarse search state.
It retains every coarse winner.
The unit control keeps small candidates above and below the bar without advancing the search.
An unbounded prototype passed the pair and deep-907 controls but enters no production run.
The bounded version gives each try the smaller of 90 seconds and the remaining run budget.
It uses the existing family solver limit and clears it in a finally block.
A control verifies that the native LP receives that limit and that it resets.
Both bounded numerical controls completed certified-input fq.
The 907 side is 30.618227088461005 at clearance 5.019629156777228e-11.
New gates require that known deep basin, below side 30.6183.
Two 420-second trials are queued for 539 and 702.
The 702 trace had discarded one below-bar step of about 5.72e-10 of side.
Native certification can erase such clearance changes, so raw steps do not count as score gains.

At the 17:35 UTC comparison, only the recovered 641 row qualified.
Its score is 0.018867152281702104, a gain of 1.1586797161733386e-6 against the round 30 bar.
The 46 completed production jobs logged 7,840 kick trials.
There were two job errors: the deliberate 446 cancellation and the 539 coarse-reference watchdog.
Independent source checks accepted 43 normal production ends.
Sixteen of those ends shortened side by more than 1e-8.
Those movements compare each end with its own start and are not additive score gains.
The complete receipts are in [the round 30 results](../results/invent-r30-2026-11-15.tsv).

The bounded 702 trial completed 12 tries and saved one small candidate.
Certification and fq left a gain of 6.742717495455963e-11 against the bar.
That is below the required 1e-10, so it adds no qualifying row.
The bounded 539 job did not start before the 17:27 UTC claim cutoff.
Only these two previously admitted jobs could claim work after general intake closed at 17:20 UTC.
The 17:45 UTC common hard deadline stayed in place.

The last numerical job ended at 17:34:08 UTC.
Uncached boxE verification accepted both byte-identical 641 endpoints at 17:34:45 UTC.
Native and pandas reads agreed, with clearance of at least 2.2e-11.
All 255 copied boxE CSV files matched their manifest hashes.
The owned boxE scratch was then removed.
The finalizer keeps the take open for the final source and live-peer comparison at 17:54:35 UTC.
It writes the report after 17:55 UTC.

The worker finishes the last saved raw candidate.
A future version should compare every retained candidate and the certified start after certification and fq.
Small raw improvements can disappear during certification, as the bounded 702 result showed.
Fresh geometry remains the first numerical priority.
Three of six fresh production ends shortened side by more than 1e-8 this round.

A final audit found regex syntax in a glob used to select withdrawal logs.
The corrected selector reads all nine handoff logs from rounds 22 through 30.
Both withdrawal caches refresh when a selected log changes.
A new exact-byte withdrawal fails, a wrong-hash notice passes, and a later exact reinstatement passes.
The control also verifies that each log change reloads the withdrawal reader.
All 46 completed production jobs received a fresh source check.
Forty-four passed, and the same two 446 jobs remained excluded.
The real 641 source still passes.
The local finalizer restarted with the corrected reader and its completed cleanup receipts.
No numerical work restarted.

## Round 31 (2026-11-15 to 2026-11-16)

The lane retained 604, 643 and 989 for a total score gain of 5.711295540944406e-7.
The last responsive live comparison ran at 00:11:38 UTC.
Each retained file completed fq from its certified input on boxE.
Native and pandas reads required at least 2.2e-11 of clearance.
Three boxE slots completed 210 production jobs.
Each dry probe stopped after about 120 seconds. Productive searches could use 900 seconds.

The 989 endpoint shortened side by 6.148449259057998e-6 and ended at 00:09:09 UTC.
It missed the admission cutoff and received no continuation.
Changed geometry supplied 604 and 989. The held queue supplied 643.
The restored 539 recipe stayed 4.0692166550782005e-5 of score above the bar.
That geometry stays closed.

The revised finisher quenched each distinct certified candidate before comparing completed endpoints.
A decimal buffer repaired a pandas clearance miss at 984.
Its control reached 2.219735506514553e-11 of clearance and still refused coincident squares.
Shared starts carried exact SHA-256 claims.
Source controls accepted held-only ancestry and refused the withdrawn direct 814 input.

Filesystem waits blocked the original archive transfer, final audit and push.
Round 32 recovered 134 missing CSV files.
All 1,212 CSV hashes match both the frozen manifest and the remote manifest.
The owned boxE scratch was removed after verification on 2026-11-16.
No old lane processes remained on either box.
The round 31 take remains frozen.

The [results table](../results/invent-r31-2026-11-16.tsv) records each completed job.
The [saved tools](../tools/invent/round31) preserve the source reader and numerical campaign.

## Round 32 (2026-11-16)

The lane recovered the round 31 archive before starting production. All 1,212 CSV hashes matched.
It removed the owned round 31 boxE scratch and pushed the saved code and measured results.
The late 989 endpoint was already claimed by rebuild. The lane skipped that duplicate start.
Fresh changed rectangles and joins received priority.
The lane published 2 provisional rows. Their maximum per-n gains sum to 0.000139521215131833 before peer follows.
Unchanged held kicks and the unchanged 539 retention profile stayed closed.
Three boxE slots completed 64 production jobs and logged 7372 family-kick trials.
The fresh queue completed 36 jobs. 23 shortened side by more than 1e-8.
The leg queue completed 26 jobs. 2 shortened side by more than 1e-8.
The wide queue completed 2 jobs. 2 shortened side by more than 1e-8.
A planned two-start pilot uses radius 8 with angular noise factor 0.15. Its stopped 907 control gates admission.
The older radius 8 trials stay closed on their unchanged geometry. This pilot uses new rectangle and join bytes.
Movement compares each endpoint with its start. It is not additive score gain.
The archive comparison retained 0 rows for 0 against bar32.
Search and quench share a 17:00 UTC cutoff, leaving time for the archive and push before 17:15.
The take remains open for the final comparison before 17:25 UTC.
Every retained endpoint completed fq from its certified input and cleared native and pandas reads by at least 2.2e-11.
The stopped 907 control reached the known deep basin below side 30.6183 before production opened.
The four-candidate control quenched every distinct certified input before selecting its winner.
Production compares the certified start with every saved raw candidate after their separate quenches.
An immutable checkpoint now exports after each completed candidate quench. The batch keeps comparing later candidates.
Checkpoint controls accept a completed candidate and refuse overlaps and wrong quench markers.
Source controls accepted held ancestry without a share call and rejected changed evidence.
The exact-byte withdrawal control reads the current round log and ignores a notice for different bytes.
A direct withdrawn 814 parent still fails beside a held sibling. Its held-only ancestry passes.
Held roots verify a known submitted file and its GREEN gate. Exact exports also verify their coordinates.
An unsubmitted round 23 candidate needs identical coordinates in the submitted b file. Its changed 228 fails.
The 367 source control accepts its SHA-bound held wrapper and rejects a wrong ancestry hash.
Changed source sidecars can reopen a deferred start. Unchanged source failures stay closed.
The 970 control passes without a share call. Changed exports, forged row hashes and nonheld leaves fail.
All 701 archived CSV hashes matched before removing the owned round 32 boxE scratch.
The [results table](../results/invent-r32-2026-11-16.tsv) records each completed production job.
The [saved tools](../tools/invent/round32) preserve the controller, source policy and numerical worker.

## Round 33 (2026-11-16 to 2026-11-17)

Fresh changed rectangles and joins received priority. Four boxE slots ran with a 120-second dry probe.
Plain held kicks, unchanged539 and the completed broad-radius pilot stayed closed.
The lane completed 25 production jobs and logged 1269 family-kick trials.
The fresh queue completed 24 jobs. 9 shortened side by more than 1e-8.
The leg queue completed 1 jobs. 0 shortened side by more than 1e-8.
Movement compares each endpoint with its start. It is not additive score gain.
Archived. Published 1 provisional rows. Retained 1 after the latest bar33 and live-peer comparison.
The archive comparison gain against bar33 is 5.13690366732433e-06. The take remains open for the final live comparison.
Each distinct certified candidate completed the full default and polish fq loop before comparison.
Completed candidate checkpoints exported while the batch compared later candidates.
Production required the pair and stopped907 controls, plus checkpoint controls that refused overlaps and wrong quench markers.
The startup order now waits for control2 before its checkpoint control. The initial workers exited before any search.
Source controls accepted submitted round32 coordinates without a share call and refused changed coordinates or evidence.
A k123 catalogue leaf now resolves held ownership through its accepted gate and exact float64 geometry hash.
The actual789 mixed held and original-seed graph passed without a share call. A changed seed hash failed.
The actual259 control passed. Wrong geometry hashes, wrong counts and mixed-parent records failed.
The exact-byte withdrawal control selected the current log and ignored notices for different bytes.
The historical970 source fixture failed closed because its forensics849 parent had been superseded. It supplied no production input.
All 422 archived CSV hashes matched before removing the owned boxE scratch.
The [results table](../results/invent-r33-2026-11-17.tsv) records each completed job.
The [saved tools](../tools/invent/round33) preserve the campaign and source checks.

## Round 34 (2026-11-17)

Fresh changed rectangles and joins received priority. Four boxE slots ran with a 120-second dry probe.
Plain held kicks, unchanged539 and the completed broad-radius pilot stayed closed.
The lane completed 125 production jobs and logged 14263 family-kick trials.
The fresh queue completed 100 jobs. 56 shortened side by more than 1e-8.
The leg queue completed 25 jobs. 0 shortened side by more than 1e-8.
Movement compares each endpoint with its start. It is not additive score gain.
Archived. Published 2 provisional rows. Retained 2 after the latest bar34 and live-peer comparison.
The archive comparison gain against bar34 is 0.000115413327914649. The take remains open for the final live comparison.
Each distinct certified candidate completed the full default and polish fq loop before comparison.
Completed candidate checkpoints exported while the batch compared later candidates.
Production required the pair and stopped907 controls, plus checkpoint controls that refused overlaps and wrong quench markers.
The startup order ran control2 before the checkpoint control. Production waited for every control.
Source controls accepted a submitted round33 row without a share call. They refused changed coordinates, wrong evidence and exact withdrawn bytes.
A watchdog restarted dead boxE slots and released their job locks. Its control killed and restarted an idle slot.
The watchdog also stopped a running job once a live peer row passed its dispatch bar by more than 1e-6.
All 1725 archived CSV hashes matched before removing the owned boxE scratch.
The [results table](../results/invent-r34-2026-11-17.tsv) records each completed job.
The [saved tools](../tools/invent/round34) preserve the campaign and source checks.

Three source checks refused clean fresh starts. We fixed each one in our own copy and proved it with controls.

1. A k123 held leaf can name its parent as plain "held" or as a file path. The producer table check failed on both. The check now accepts such a leaf only when its float64 geometry hash equals the submitted row of the round it names. A wrong hash, count, round or parent still fails.
2. The source walk stopped at 3000 nodes and deferred large fresh graphs. The cap is now 20000. The 977 rectangle then closed in 98 seconds and failed for a real reason, because its tree reaches the withdrawn backlog 972 file.
3. Backlog claims bytes with 12-hex prefixes. The claim reader now accepts prefixes from 12 to 64 hex digits.

The k123 band joins mostly settled on the held geometry, within 6e-11 of the bar.
The fresh 790 join certified at 0.017455447042680206. That is 1.154e-4 below bar34, but only 2.8e-11 below the k123 row from the same join family.
The fresh 925 join certified 1.17e-10 below bar34.

## Round 35 (2026-11-17)

Fresh changed rectangles and joins received priority. Three boxE slots ran with a 120-second dry probe.
Plain held kicks, unchanged539 and the completed broad-radius pilot stayed closed.
The lane completed 41 production jobs and logged 3607 family-kick trials.
The fresh queue completed 41 jobs. 23 shortened side by more than 1e-8.
Movement compares each endpoint with its start. It is not additive score gain.
Two finds certified below bar35 by more than 1e-10. Both lost to a lower live round 35 take at the same n.
Our 746 row was 8.3e-10 below bar35. The classfill 746 row built from it was 3.05e-9 below bar35.
Our 925 row was 4.8e-8 below bar35. The backlog 925 row was 1.98e-5 below bar35.
The lane take holds 0 rows. Five fresh jobs queued after 15:25Z never started before the close.
Each distinct certified candidate completed the full default and polish fq loop before comparison.
Completed candidate checkpoints exported while the batch compared later candidates.
Production required the pair and stopped907 controls, plus checkpoint controls that refused overlaps and wrong quench markers.
The startup order ran control2 before the checkpoint control. Production waited for every control.
Source controls accepted a submitted round34 row without a share call. They refused changed coordinates, wrong evidence and exact withdrawn bytes.
A watchdog restarted dead boxE slots and released their job locks. Its control killed and restarted an idle slot.
The watchdog also stopped a running job once a live peer row passed its dispatch bar by more than 1e-6.
All 586 archived CSV hashes matched before removing the owned boxE scratch.
The [results table](../results/invent-r35-2026-11-17.tsv) records each completed job.
The [saved tools](../tools/invent/round35) preserve the campaign and source checks.

## Round 36 (2026-11-17)

The lane started late, at 19:17Z, with two boxE slots. We replaced the round 35 campaign with a small worker and driver.
Each job ran 900 seconds without a dry probe. Every certified candidate then ran the full fq loop from its certified file.
The driver synced every 90 seconds, checked the stop rule and compared each final row with bar36 and the live round 36 takes.
The stop rule passed the four cases of the brief. A mutant that compared only with the bar failed them.
Every start was walked before or during its search with the 100000-file walker. All 27 walked starts were clean and uncapped.

The lane completed 26 jobs. No row certified below bar36 by more than 1e-10, so the take holds 0 rows.
The near donors gave a clear result. We ran 14 jobs on 12 donors that started 1.6e-10 to 6.3e-7 of score over bar36.
11 jobs ended within 4e-10 of bar36. The other 3 hardly moved (750, 802 and 807 under invent_barretain). Example: 998 went from 4.8e-7 to 6e-12 over the bar.
583 went from 6.3e-7 to 2.8e-11 under it, and 707 went from 2.1e-7 to 1e-12 under it.
Both search programs gave the same result: invent_barretain lkick and midm_scan lkick,kick.

We measured why with a new triage tool, heldshare.py. It reports the share of a layout's square centres that lie within 1e-3 of the held row of the same n.
10 of our 12 donors shared 0.53 to 0.97 of their squares with the held row. They are the held optimum with a few squares moved.
The other two shared less. 305 (0.38) still returned to the bar, and the 750 rectangle row (0.30) moved only 1.1e-8.
The border 698 donor shared only 0.125 and paid 3.7e-5. We then measured the 104 donors that the lanes claimed by path in round 36.
56 donors shared less than 0.5. Their n include 4 of the 7 n that certified in round 36 (698, 793, 911 and 972).
48 donors shared 0.5 or more. Only 972 paid among their n, and 972 also had donors with a low share.
All twenty 965 claims used donors that shared 0.79 to 0.90. No 965 row certified.

After that we ran single midm seeds on twelve held rows. Each had a large board room, no claim on its n in rounds 33 to 36 and a side that is not closed form.
All twelve ended within 3.4e-11 of bar36 (333 694 545 969 500 795 499 643 587 924 341 915). That is fq polish noise, not a find.
We released 747 and 861 before they started. Their held sides share the fraction 0.796130877 with 860, so lesson 6e applies.
The [results table](../results/invent-r36-2026-11-17.tsv) records each completed job with the held share of its start.
The [saved tools](../tools/invent/round36) hold the worker, the driver and the triage tool.
