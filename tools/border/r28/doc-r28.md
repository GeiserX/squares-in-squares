
### Round 28: the LP follow of fresh takes, kicked follows and a finer floatsafe (2026-11-15)

**Result: @RESULT@**

The bar for each n is `round28-briefs/bar28.tsv`. It is the lower of the held round 26 b file and the best certified round 27 take. A main rule at 00:19 UTC changed two things. The prvsiyan share test now applies only to rows whose first source is a public notebook or dataset. A withdrawal made only for a share is void. A row whose ancestry names the prvsiyan 1105 file still stays out.

#### Tool changes and controls

The round 28 tools are in `tools/border/r28`. They are the round 27 tools with these changes:

- `base28.py` reads the bar file. Each process writes its own temporary file, because two feeders crashed on one shared name.
- `provenance.withdrawn` reads the handoff logs of rounds 27 and 28 in time order. A REINSTATE or REOPEN line opens a path again, and so does a line that calls a withdrawal void or lifted. A withdrawal line that gives only a share is skipped. A line that also names another reason still counts. The reasons are penguin069, CC BY-SA, a licence, a notice, an unresolved trace, the rule-a family or an excluded family. A retention phrase counts only right before a path.
- `provenance.audit` no longer runs the ancestor share test.
- `source_policy.classify` keeps the status that the soft policy marks as lifted for Samanyu names.
- `driver.py` runs the share test only on public-first inputs. The border scan (`make`) reads only the fresh take csv of other lanes, and the chain-only b1 picks are off.
- `lpfeed.py` gives every LP result a polish fq (`--no-alm --loosen 1.0 --flip-top 64 --pit 600`). The default fq runs only on take inputs and on inputs more than 5e-9 above the bar. The processed outputs persist in `lp/done.json`, so a restart does not certify them again.
- `finesafe.py` certifies with a bisected dilation. See the next section.
- `kfeed.py` queues kicked follows of live takes. We measured it and stopped it.
- `worker.py` takes the fq flags from each job, and two workers share the queue.
- `design/` holds the block models of the design search.

The controls printed these results:

- The fq control on boxC took `control-870` from 30.91440407839406 to 30.91388209074235 in 76.5 s. Rounds 26 and 27 measured the same endpoint.
- The polish fq on the r27 LP final of 973 ended 1.4e-9 above its certified input. The default fq on the same input ended 1.9e-5 above.
- The source policy accepts an own root below the bar and a Samanyu seed. It refuses CC BY-SA, the prvsiyan file, `seed merged0` and unresolved sources.
- `withdrawn()` reads 40 withdrawn paths. These include the forensics 743 take and the 29 forensics near rectangles of 01:51 UTC. The share-only k123 798 lines stay void.

#### A finer floatsafe

`floatsafe.work` scales the centres about their mean by 1+e. It takes the first e of a 1-2-5 ladder that passes two tests. Every pair must clear 2.2e-11 on a separating axis, and the metric must accept the rows as written and after the pandas float parse. On every LP and fq output of this round the ladder stopped at e = 5e-11, but about 2.18e-11 is enough. `finesafe.py` bisects e between the failing and the passing ladder step. It then runs the same clearance test and both metric checks.

On the fq outputs of our 19 near files, finesafe certified 3.0e-10 to 8.2e-10 of side lower than the ladder. That is about 28% of the rule. The certify step of the driver, lpfeed and wfeed uses it from 02:30 UTC.

It moved one layout past the rule. The polish fq of the backlog near 503 certified 2.754e-9 below the live bar, and the rule needs 2.243e-9 at 503. The row still stays out. The backlog record of that parent names a public-first ancestor in `take-harvest-r22/work/collector/certified` with a prvsiyan 1105 share of 0.492.

#### What ran

Eight layouts certified past the rule. Five lost to lower rows of other lanes within seconds to 37 minutes. Two are in the final take. At the last refresh (05:51 UTC) no other round 28 take held 642 or 916, so the whole gain is beyond the other takes.

| n | certified score | below bar28 | below other takes | what it was | what happened |
|---|---|---|---|---|---|
| 499 | 0.02187739078442408 | 6.95e-6 | 7.8e-9 | LP and polish fq of the backlog 499 take | a backlog follow went lower 1 minute later |
| 499 | 0.02187731126229364 | 7.03e-6 | 4.5e-10 | the same chain, one step on | a backlog follow went lower 19 minutes later |
| 978 | 0.01536979320912368 | 1.66e-6 | 6.4e-10 | polish fq of the harvest 978 take | quench went lower 80 s later |
| 978 | 0.01536531084055959 | 6.14e-6 | 1.4e-8 | polish fq of a newer harvest 978 take | backlog had certified a lower 978 2 s earlier |
| 993 | 0.01293307850323999 | 2.4e-6 | 1.6e-8 | default-flag fq of the k123 993 take (Samanyu ancestry) | midm went lower |
| 916 | 0.016016593991535544 | 6.43e-5 | 4.9e-9 | LP, polish fq and self follows of the forensics 916 rectangle | in the final take |
| 642 | 0.018923096216731716 | 8.96e-7 | 8.2e-10 | polish fq of the rebuild 642 take | in the final take |

The row from the first 916 certification is not listed, because the self follow replaced it 3 minutes later.

The LP follow (`lpfeed.py`) queued @LPIN@ inputs: @LPTAKE@ take csv files and @LPNEAR@ near files of other lanes. @LPRAN@ ran before the deadline. The LP gained nothing on most of them. @LPBELOW@ certified outputs were below the live bar, the best by 2.17e-9 of side. The walk refused @LPREF@ outputs.

The polish fq always ends lower in raw side than its certified input. It did so on @PTL@ of @PTN@ take inputs and @PNL@ of @PNN@ near inputs, by a median of 1.4e-9. That is the dilation that the certify step added, and certifying again adds it back. The default fq ended lower on @DTL@ of @DTN@ take inputs, and the median take ended 5.0e-5 higher. The rows came from polish fq on takes that one fq or one kick follow had made. The polish gained 2.1e-8 of side on the harvest 978 take.

`sfeed.py` gives each new row of ours one more polish fq from its certified file. It repeats while a step gains more than 1e-9 of side. On the 916 the first step gained 4.4e-8 of side and the second step 1.2e-11, so the chain stopped. The self follows of the 978 rows came too late. The 978 self follow waited 12 minutes at the bottom of the worker queue, so follow jobs now carry the top priority. The same feeder gives a near file of ours one more polish when it is below the bar but short of the rule. It ran on 3 near files, and the best moved 6.7e-10 of side.

`kfeed.py` ran 36 kicked follows on 12 live takes, with one fq quench each at kick 0.003, 0.01 or 0.02. Two ended lower in raw side, by 1.3e-9 and 1.4e-9, inside the certification slack. The medians ended 1.6e-4 to 7.4e-4 higher. A kick does not move a converged take, so we stopped it after 18 minutes.

The window scanner ran @WS@ scans on @WL@ distinct fresh layouts. No window was below the rule. The border scan of fresh takes found only b1 picks 1.0e-2 to 1.8e-2 above the bar.

Three reading errors of the withdrawal lines were found and fixed during the round:

- At 01:51 UTC forensics withdrew 29 near rectangles for the rule-a family. The lines mention the lifted share rule, and our reader skipped them as share-only. Rule-a and excluded-family wording now count as a reason.
- With the case-insensitive search, the word "reopen" inside a named file turned 9 withdrawal lines into re-opens. REINSTATE and REOPEN now count only in capitals, and the prose words only outside a path.
- A SOURCE-HOLD line now counts as a withdrawal of every file of the builds it names. Stair-c held three builds at 03:41 UTC, and we had run LP on six of their files.

The walk also refuses the live rebuild and backlog 910 takes. They descend from the forensics r24 684 donor, which has a prvsiyan 1105 share of 1.000.

#### The end of the run

The session stopped at about 05:40 UTC, which killed the driver, `sfeed.py` and `finish.py`. We queued the last 916 self follow by hand. It ran, and fq gave no side. We then ran `finish.py --now` by hand. It copied 10,793 remote files with SHA-256 checks and removed the boxC scratch and its venv. The literature check passed on both rows with a minimum gap of 2.20e-11.

The round 27 `verify_proofs.py` failed on the 642 row, because it had no branch for an LP recipe. The round 28 copy checks the pinned donor hash, the certified score of the staged input and the byte-exact input of the job. It now passes on both rows. The 642 failure was the control that it can go red.

#### The design search

We modelled tilted-block designs to find new layouts for the m²+k counts of the board. The block is a×b squares at an angle, with upright rows along the walls.

- At 45° the rows model reaches 842 = 29²+1 only with the 17×17 block, at f = 0.52089. Our held 842 has f = 0.520815, so the model rebuilds our design, and no other 45° block of 13 to 21 squares a side does better.
- From 5° to 27.5° the rows model reaches no configuration.
- A control on 442 = 21²+1 failed. The held 442 is a block of about 230 squares at 20.7° with f = 0.525789. A mixed model at that angle reaches 428 of 442 at f = 0.53, and none at f = 0.75. The small-angle designs of the board need fills that the model does not hold, so we stopped the search.

#### Not run yet

- Run the LP and polish fq on every fresh take csv of other lanes within a minute, then a self follow of each new row. Measured: all seven certifications of this round came from this path. Takes made by one fq or one kick follow are not converged. The polish gained 2.1e-8 of side on the harvest 978 take, and the self follow gained 4.4e-8 more on our 916.
- Certify with the bisected dilation (`finesafe.py`) everywhere, the assembly included. Measured: 3.0e-10 to 8.2e-10 of side lower than the ladder on 19 fq outputs, about 28% of the rule. It moves every near miss by that much.
- Run the follow jobs of live rows before the LP queue. Measured: the 978 self follow waited 12 minutes, and the 978 row was gone before it ran.
- Match REINSTATE and REOPEN only as words outside file names, and read SOURCE-HOLD lines. Measured: 9 withdrawal lines were read as re-opens, and 29 rule-a near files were read as share-only, until the fix.
- Stop the kicked single fq follows, the window scans, the border scans of fresh takes and the block-model design search. Measured: 36 kicks gave nothing past the slack, and @WL@ layouts gave no window. The b1 picks were 1.0e-2 to 1.8e-2 above the bar. The model rebuilds 842 but misses the 442 control.
