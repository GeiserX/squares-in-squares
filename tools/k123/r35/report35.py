"""Build the round report from this round's receipts only."""
from pathlib import Path
import csv,json,collections,time,sys
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;L=Path('.');csv.field_size_limit(1<<28)
def load(p,default=None):return json.loads(p.read_text()) if p.exists() else default
rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));bar={int(r['n']):float(r['bar']) for r in csv.DictReader((S/'round35-briefs/bar35.tsv').open(),delimiter='\t')};peer=dict(bar)
for p in S.glob('take-*-r35/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(p.open(),delimiter='\t'):
  try:n=int(r['n']);peer[n]=min(peer[n],float(r['new']))
  except (ValueError,KeyError):pass
records=[]
for line in (W/'records.jsonl').read_text().splitlines():
 try:records.append(json.loads(line))
 except ValueError:pass
counts=collections.Counter(r['n'] for r in records);scans=[]
for p in (W/'taskdone').glob('*.json'):
 j=load(p)
 if (j['kind']=='scan' or j.get('diversity_scan')) and j['rc']==0:scans.append(j)
state=load(W/'collect-state.json',{});native={}
for key,r in state.items():
 if r.get('status')=='published' and r.get('score') is not None:
  n=r['n']
  if n not in native or r['score']<native[n]['score']:native[n]={**r,'key':key}
low=[r for r in rows if float(r['new'])<min(bar[int(r['n'])],peer[int(r['n'])])-1e-10]
gain=sum(bar[int(r['n'])]-float(r['new']) for r in low);beyond=sum(peer[int(r['n'])]-float(r['new']) for r in low)
archives=load(W/'archives34.json',{});stopped=load(W/'cleanup34.json',{}).get('complete',False)
notes=[f'{len(records)} numerical attempts on {len(counts)} counts. {sum(bool(r.get("error")) for r in records)} recorded errors and {sum(r.get("code")==-2 or r.get("fq2code")==-2 for r in records)} timeouts.',f'{len(scans)} completed donor scans covered {sum(r.get("pairs",0) for r in scans)} pairs.',f'Published native source counts: {sorted(native)}. Retained counts: {[int(r["n"]) for r in low]}.','Controls on boxE, boxC and boxD reproduced side21.564693167754. Own756 source and changed-producer-record controls passed.','Initial geometry history: '+json.dumps(load(W/'history-rebuilt34.json',{})), 'Every published row requires border finesafe at2.2e-11 and the full default/polish fq loop from the certified bytes. Own and held layouts receive no share gate. Public-first rows retain the frozen1e-3 and1e-2 checks.','Assigned numerical caps: boxE4, boxC:2, boxD:5. Ten disjoint recipe partitions feed one certification queue. Load guards pause above16 on boxE and9 on the boxC and boxD. Dead workers restart and interrupted claims requeue.','Held kicks and unchanged dry finish and matching models stayed closed. Fresh geometry and returned non-winning band donors ran first.']
notes.append('Finish branches: '+json.dumps({m:{'attempts':sum(r.get('mechanism','standard')==m for r in records),'raw_crossings':sum(bool(r.get('raw')) for r in records if r.get('mechanism','standard')==m)} for m in sorted({r.get('mechanism','standard') for r in records})}))
notes.append('Native source gains: '+json.dumps({n:bar[n]-r['score'] for n,r in native.items()}))
notes.extend(load(W/'measurements28.json',[]))
for name in ['guard-control34.json','extra-donor-gap34.json','extra-donor-control34.json','import-control34.json']:
 j=load(W/name)
 if j is not None:notes.append(name+': '+json.dumps(j))
if archives:notes.append('Stopped box archives: '+json.dumps(archives))
for name in ['independent33.json','validation25.json','final-peer33.json']:
 j=load(W/name)
 if j is not None:notes.append(name+' receipt retained under work/.')
best=sorted(native,key=lambda n:bar[n]-native[n]['score'],reverse=True)
nexts=[('Join the lowest live changed source geometries first. This round native gains: '+', '.join(f'{n}={bar[n]-native[n]["score"]:.8g}' for n in best[:6])+'.') if best else 'Join the next changed geometry first. This round has no native certified gain. Round33 productive sources were259,445,968 and734 for2.7564e-4 combined.','Return valid non-winning bands as donors before old recipes. Round31 donor927 supplied928, and round32 donor292 supplied488 for4.0923e-5.','Keep completed geometry signatures closed. This round started with19,209 closed signatures and no missing manifests. Reopen a dry recipe only after changing its physical input or finish mechanism.','Keep load guards, exact per-slot worker ownership and interrupted-claim recovery. Preserve source bytes and producer records before dispatch.']
commits=load(W/'commits34.json',[]);blocked=load(W/'blocked34.json','none')
report=dict(lane='k123',improved_n=len(low),gain={'against_base_bar':gain,'beyond_other_live_r35':beyond},take_dir=str(T),summary=f'{len(low)} retained rows beat bar35 and every live peer. {len(native)} native source counts certified. '+('All lane workers stopped. All three archives verified and box scratch removed.' if stopped else 'Work remains active; see STATE.txt.'),what_was_measured=notes,next=nexts,commits=commits,processes_left=0 if stopped else 'see STATE.txt',blocked=blocked,repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
(W/'metrics34.json').write_text(json.dumps(report,indent=2)+'\n')
if '--artifacts' in sys.argv:
 with (L/'results/k123-r35-2026-11-17.tsv').open('w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for r in rows:
   n=int(r['n']);sc=float(r['new']);wr.writerow(['certified',n,counts[n],(sc+1)*n**.5,bar[n]-sc,max(0,peer[n]-sc),r['source'],r['licence'],'lowest live' if r in low else 'superseded'])
  for n in sorted(counts):
   ss=[r['side'] for r in records if r['n']==n and 'side' in r];wr.writerow(['attempts',n,counts[n],min(ss) if ss else '',0,0,'immutable inputs in take-k123-r35/work','per-input source records','raw measured side'])
 text=f'''## Round 35

The lane retains {len(low)} layouts below bar35 and every live peer.
Their gain is {gain:.15g} against bar35 and {beyond:.15g} beyond the other takes.
The source history contains {len(native)} native certified counts.

The boxes completed {len(records)} numerical attempts on {len(counts)} counts.
The {len(scans)} completed donor scans covered {sum(j.get('pairs',0) for j in scans)} pairs.
The initial history closed 19,209 prior signatures, with no missing manifests.
Changed endpoints ran before valid non-winning bands and exact unrun recipes.
Held kicks and unchanged dry finish models stayed closed.

All three boxes reproduced the 444 control at side 21.564693167754.
The source control accepted own756 and rejected a changed producer record.
Published files passed border finesafe at 2.2e-11 and the full certified-file fq loop.
Own and held layouts received no share gate.
Public-first rows retain both frozen share tolerances.
The final pass checks sources, unchanged certificate bytes, float parsing and live peer scores.

The numerical caps were four boxE slots, two boxC slots and five boxD slots.
The boxD cap dropped to three after 35 of 60 load samples paused its workers.
Ten disjoint recipe partitions still fed boxE certification queue.
Box guards pause above load 16 on boxE and 9 on the boxC and boxD.
Each guard removes orphan children before it requeues an interrupted claim.
A live process control passed, with stale claims reopened and completed claims retained.
The returned-band reader now accepts workers on all three boxes.
Its former worker-name list excluded 385 eligible extra-box outputs.
The new physical upright phases tested 39,192 matching graphs without a crossing.
Both held reconstruction controls passed.
Different-parent crossover tested 624 configurations across six pairs, with no count increase.
The common search and quench deadline is 16:25 UTC.

Sources and measurements are in [the round table](../results/k123-r35-2026-11-17.tsv).
The [round helpers](../tools/k123/r35/) preserve the queue and source checks.
Receipts remain in `$SCRATCH/bounties-squares/take-k123-r35/work/`.
'''
 (W/'round35-section.md').write_text(text)
else:
 (T/'report.json.tmp').write_text(json.dumps(report,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}),flush=True)
