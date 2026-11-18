import csv,json,pathlib,subprocess,math,collections,time
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
R=pathlib.Path('.')
js=json.load(open(W/'jobs.json'));done={p.parent.name:json.load(open(p))for p in(W/'boxE-raw').glob('*/done.json')}
subprocess.run([str(S/'venv/bin/python'),str(W/'measure23.py'),str(R/'results/invent-r23-2026-11-13.tsv')],check=True)
measured=list(csv.DictReader(open(R/'results/invent-r23-2026-11-13.tsv'),delimiter='\t'));prod=[r for r in measured if r['kind']!='control'];errors=[r for r in prod if r.get('error')];moved=[r for r in prod if not r.get('error') and float(r['final_side_gain'])>1e-8]
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
held={int(r['n']):float(r['score'])for r in csv.DictReader(open(S/'gate/cand-round21-1113a/details.csv'))};bar=dict(held)
for p in list(S.glob('take-*-r22/take.tsv'))+list(S.glob('take-*-r23/take.tsv')):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
desc=[]
for p in S.glob('take-*-r23/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  if 'take-invent-r23' in r.get('source',''):desc.append({'owner':p.parent.name,**r})
(W/'descendant-rows.json').write_text(json.dumps(desc,indent=2))
gain=sum(held[int(r['n'])]-float(r['new'])for r in rows);net=sum(bar[int(r['n'])]-float(r['new'])for r in rows)
back=sum(j.get('backlog',False)and j['id']in done for j in js)
trials=sum(int(r['tries'])for r in prod);pending=[j for j in js if j['id']not in done]
ctl=next((r for r in measured if r['kind']=='control'),None)
best=sorted(moved,key=lambda r:-float(r['final_side_gain']))
summary=f'{len(prod)} production runs on three boxE slots, {trials} tries. {len(rows)} n remain below every other take. {back}/13 saved starts finished.'
if best:summary+=f' Largest measured side step: n={best[0]["n"]}, {float(best[0]["final_side_gain"]):.9g}, from {best[0]["name"]}.'
what=[f'{len(prod)} production runs, {len(moved)} moved more than 1e-8 of final side. {trials} search tries. Runs, exact starts, source chains and licences are in results/invent-r23-2026-11-13.tsv.',f'Third boxE slot completed {back} of the 13 round22 pending starts. Original seeds and flags were retained; each start was compared with the round21, frozen round22 and other live round23 bar.', 'Positive control 907: try4 printed side30.619564100215 below the30.6195806 stop. Try9 reproduced30.618227092836. The control also completed its certified-file fq quench.', 'New rectangle starts use fq after every squeeze. Round22 tested four squeeze-only rectangle scans and found no raw result. Other fresh shell and join starts use the family squeeze; every find gets floatsafe and a quench from that certified file before publication.', 'Filter audit removed the n300 floor, widened the near margin to0.0031 of side and changed the geometry key from1e-5 to1e-7. Translation, quarter-turn and reflection controls pass; a0.001 centre move changes the key.', 'The worker bounds search and postquench process groups by one common18:30UTC deadline. Starts transfer before queues. Cached certification reads specs from JSON to preserve long source chains.']
what += [f'{len(errors)} bounded worker errors are excluded from move statistics. The913 attempt hit400seconds before completing its first try and wrote no raw CSV, so no recovery or unchanged retry was queued.']
(W/'failed-final.json').write_text(json.dumps([j for j in js if (W/'boxE-raw'/j['id']/'done.json').exists() and json.load(open(W/'boxE-raw'/j['id']/'done.json')).get('error')],indent=2))
what += ['Certification cache control on an isolated442 copy passed: cached output stayed byte-identical, duplicate-square overlap was dropped, restoring the file restored identical output.', 'Offline plateau audit:45 eligible round22 traces,15 would stop after six completed tries with at least three end sides within5e-9 of their minimum and no step over1e-8. This frees4861.9seconds and loses one2.945e-8 side move on340. The first ten moving traces remain intact. New seeds123/172 use this rule; saved starts retain their original behavior.']
what += [f'{len(desc)} current rows in other round23 takes name this lane in their source chain. These rows are not counted in improved_n or gain. The border530 descendant of our442 kick supplied lower442 and485 rows; exact current records are in work/descendant-rows.json.']
stops=sum('plateau stop after' in p.read_text() for p in (W/'boxE-raw').glob('*/slide-*.tsv'))
what += [f'The live six-try policy stopped {stops} scans. At16:54UTC the common-end predicate added one further dry full trace in replay,358.8seconds, with no further measured loss. Existing stop traces are censored and do not prove future gain is zero.']
what += ['Deadline failure control used the actual worker timeout function: a child and grandchild both stopped in0.517seconds with a0.5second common deadline. The result is in work/deadline-control-result.json.', 'Queue fairness control: already-claimed jobs are removed before interleaving. Fresh530 started at16:25UTC after the fix; historical locked entries had delayed it behind new near442 files.']
unadmitted=json.load(open(W/'unadmitted-fresh.json'))if(W/'unadmitted-fresh.json').exists()else[]
what += [f'Fresh admission audit found53 eligible unseen take layouts at17:31UTC, including kicked copies. A reserved fresh entry then started379 at17:32UTC and442 at17:34UTC. {len(unadmitted)} unadmitted fresh layouts are preserved with exact CSV hashes and provenance in work/unadmitted-fresh.json.']
nexts=[]
if best:
 nexts.append('Kick fresh shell and join builds immediately and reserve fresh admission. The first border442 and485 scans each moved0.00046844 of side. The442 kick then fed the border530 build and lower442/485 descendants. Give new round-trip near layouts space too: the round22 family855 near moved0.002536 of side.')
 b=best[0]
if pending:nexts.append(f'Reconsider {len(pending)} unfinished starts in work/pending-final.json against the next bar. They retain exact inputs and flags; {back}/13 saved round22 starts completed this round.')
legs=[r for r in prod if r['kind']=='leg' and not r.get('error')];lm=[r for r in legs if float(r['final_side_gain'])>1e-8]
nexts.append(f'Give useful new finds one leg, then measure whether it pays. This round {len(lm)}/{len(legs)} completed legs moved more than1e-8 of side. Round22 805 gained another1.00147e-4 on its leg, while855 and two698 legs were dry.')
rect=[r for r in prod if r['fq']=='True' and not r.get('error')];rm=[r for r in rect if float(r['final_side_gain'])>1e-8]
nexts.append(f'Keep the explicit fq branch for polished starts under measurement. This round {len(rm)}/{len(rect)} fq runs moved more than1e-8 of side; the unchanged squeeze-only rectangle scans of round22 were dry.')
nexts.append('Keep exact build provenance and drain every certified-input quench before freezing. The907 control completed both stages; the round22 postquench exceeded the old search deadline by9seconds, so use one common hard deadline.')
if unadmitted:nexts.insert(1,f'Reconsider the {len(unadmitted)} immutable inputs in work/unadmitted-fresh.json before resuming old near copies. The17:31 audit found53 eligible unseen take layouts under near-first admission. Reserve fresh admission from the handoff minute;379 and442 started after that fix.')
nexts=[s.replace('; ','. ')for s in nexts]
commits=(W/'commits.txt').read_text().splitlines()if(W/'commits.txt').exists()else[]
cleanup=json.load(open(W/'cleanup.json'))if(W/'cleanup.json').exists()else{}
report=dict(lane='invent',improved_n=len(rows),gain={'against_round21':gain,'against_frozen_r22_and_other_r23':net},take_dir=str(T),summary=summary,what_was_measured=what,next=nexts,commits=commits,processes_left=cleanup.get('processes_left','Three bounded boxE workers and the local collector are active.'),blocked=f'No access block. {len(pending)} queued starts and {len(unadmitted)} unadmitted fresh snapshots remain for the next round. Exact inputs and flags are preserved under work; search stops at the common deadline.',repo='private repo',branch='main',worktree=str(R.parent.parent),pr='none')
p=T/'report.json.tmp';p.write_text(json.dumps(report,indent=2)+'\n');p.replace(T/'report.json')
(W/'pending-final.json').write_text(json.dumps(pending,indent=2))
parts=['## 18. Round 23 (2026-11-13)','',summary,'',f'The take gains {gain:.12g} on round 21 and {net:.12g} below frozen round 22 and every other live take.','The bar uses gate/cand-round21-1113a and all frozen round 22 and live round 23 takes.','Each result must clear both bars by more than 1e-10 of score.','','### 18.1 Runs and controls','',f'{len(errors)} bounded worker errors are excluded from the move table.','The stopped 907 control passed at try 4, side 30.619564100215.','Try 9 reached 30.618227092836 and reproduced the known slide.','The control completed floatsafe and the quench from its certified file.','', '[The run table](../results/invent-r23-2026-11-13.tsv) records every completed scan and its source chain.','', '| Start | fq after each squeeze | Runs | Moved by more than 1e-8 | Largest final side step |','| --- | --- | --- | --- | --- |']
for kind in ['near','fresh','leg']:
 for fq in ['False','True']:
  rs=[r for r in prod if r['kind']==kind and r['fq']==fq and not r.get('error')]
  if rs:parts.append(f'| {kind} | {"yes"if fq=="True"else"no"} | {len(rs)} | {sum(float(r["final_side_gain"])>1e-8 for r in rs)} | {max(float(r["final_side_gain"])for r in rs):.6g} |')
parts += ['',f'{len(desc)} rows in other live takes name this lane in their source chain.','They are excluded from this take count and gain.','The border lane used our 442 kick through its 530 build, then lowered 442 and 485.','Exact current records remain in work/descendant-rows.json.']
parts+=['','The six-try plateau rule applies only to new seeds 123 and 172.','It stops when at least three end sides match their minimum within 5e-9 and none moves more than 1e-8.','An offline replay of 45 round 22 traces would stop 15 scans and free 4861.9 seconds.','It loses one side move of 2.945e-8 on 340.','The first ten moving traces retain their full result.','Equal end sides slightly above the input now stop too, while an early 0.001 slide keeps running.','Saved starts keep their original flags and seeds.','','### 18.2 What changed','','Three boxE slots ran at nice 5.','The third slot drains the 13 saved round 22 starts, then takes new near layouts.','The other slots interleave fresh builds, near starts and useful legs.','The saved backlog has its own capacity, so it cannot fill the fresh queue.','A later audit found 53 eligible unseen take layouts, including kicked copies.','Fresh admission now has one reserved entry while fewer than three fresh jobs wait.','The control started fresh 379 at 17:32 UTC and fresh 442 at 17:34 UTC.',f'{len(unadmitted)} eligible unadmitted layouts are saved in work/unadmitted-fresh.json with exact input hashes.','', 'Rectangle starts now get fq after every squeeze.','Round 22 tested four rectangle starts with the squeeze alone and found no raw result.','Fresh shell builds retain the family squeeze before their first quench.','', 'The near margin is 0.0031 of side, and the old floor at n = 300 is removed.','The geometry key rounds at 1e-7 instead of 1e-5.','This retains small changes in shell builds.','The key passes translation, quarter-turn and reflection controls.','A centre move of 0.001 gives another key.','', 'Every find passes floatsafe on boxE, then gets fq from that certified file.','Publication uses the lower safe file after the quench completes.','The per-n file is written before take.tsv is replaced by rename.','Search and postquench use one common hard deadline of 18:30 UTC.','The worker terminates a child process group that exceeds its bound.','The deadline control stopped a child and grandchild in 0.517 seconds against a 0.5-second bound.','', 'Input files transfer before their queue entries.','Certification reads its specs from a JSON file, so long source records fit.','Near provenance resolves to the exact module build record or donor source table.','', '### 18.3 Retained rows','', '| n | Round 21 score | Final score | Gain on round 21 | Gain below every other take |','| --- | --- | --- | --- | --- |']
for r in rows:
 n=int(r['n']);v=float(r['new']);parts.append(f'| {n} | {held[n]:.12f} | {v:.12f} | {held[n]-v:.9g} | {bar[n]-v:.9g} |')
if not rows:parts.append('| none | | | | |')
parts+=['','Sources and licences are in take-invent-r23/take.tsv.','Held ancestry names results/round21-best-2026-11-13.tsv.','Other inputs retain their donor take.tsv or exact near build record.','','### 18.4 Next','']
for i,s in enumerate(nexts,1):parts.append(f'{i}. {s}')
parts+=['','The deployed scripts and exact starts remain in take-invent-r23/work.','Saved tools are in [tools/invent/round23](../tools/invent/round23/).','']
section='\n'.join(parts);(W/'round23-doc.md').write_text(section)
p=R/'avenues/invent.md';text=p.read_text();a=text.find('## 18. Round 23');b=text.find('## Summary',a if a>=0 else 0)
if a>=0:text=text[:a]+section+'\n'+text[b:]
else:text=text[:b]+section+'\n'+text[b:]
p.write_text(text)
print(json.dumps({'runs':len(prod),'tries':trials,'retained':len(rows),'gain':gain,'net':net,'backlog_done':back,'pending':len(pending)}))
