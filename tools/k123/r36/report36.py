"""Report measured round36 results and preserve the lane's reproducible helpers."""
from pathlib import Path
import json,csv,sys,collections
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;L=Path('.');csv.field_size_limit(1<<28)
def load(p,d=None):return json.load(open(p)) if p.exists() else d
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round36-briefs/bar36.tsv'),delimiter='\t')};peer=dict(bar)
for p in S.glob('take-*-r36/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);peer[n]=min(peer[n],float(r['new']))
  except (ValueError,KeyError):pass
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));low=[r for r in rows if float(r['new'])<min(bar[int(r['n'])],peer[int(r['n'])])-1e-10]
records=[]
for l in (W/'records.jsonl').read_text().splitlines():
 try:records.append(json.loads(l))
 except ValueError:pass
scans=[j for p in (W/'taskdone').glob('*.json') if (j:=load(p)).get('rc')==0 and (j.get('kind')=='scan' or j.get('diversity_scan'))]
state=load(W/'collect-state.json',{});native={}
for r in state.values():
 if r.get('status')=='published' and r.get('score') is not None and (r['n'] not in native or r['score']<native[r['n']]['score']):native[r['n']]=r
near=[j for j in load(W/'near-state36.json',{}).values() if j['status']=='published'];gain=sum(bar[int(r['n'])]-float(r['new']) for r in low);beyond=sum(peer[int(r['n'])]-float(r['new']) for r in low)
stopped=load(W/'cleanup34.json',{}).get('complete',False);hist=load(W/'history-rebuilt36.json',{});archives=load(W/'archives34.json',{})
measure=[f'{len(records)} numerical attempts on {len({r["n"] for r in records})} counts. Errors {sum(bool(r.get("error")) for r in records)}. Timeouts {sum(r.get("code")==-2 or r.get("fq2code")==-2 for r in records)}.',f'{len(scans)} completed donor scans covered {sum(j.get("pairs",0) for j in scans)} pairs.',f'Native certified counts {sorted(native)}. Retained counts {[int(r["n"]) for r in low]}. Certified near donors {len(near)}.',f'Closed geometry history: {json.dumps(hist)}.','boxE and boxD reproduced side 21.564693167754 in the 444 control. Own756 and changed producer record controls passed.','boxE 3 numerical slots and boxD initially 3, then 2 and 1 slots during load trials share atomic claims on boxE. Each guard restarts dead slots and recovers interrupted claims. Load limits are 16 and 9.','Every take and near donor requires finesafe clearance >=2.2e-11 and the full default/polish fq loop from certified bytes. Source walks use cap100000 and reject capped completion. Own and held descendants receive no share gate.','Near donors are ranked by board room and report gap to bar, board room, file count and cap status. Public-first sources retain the frozen share31 1e-3 and 1e-2 checks.']
peer_descendants=[]
for table in S.glob('take-*-r36/take.tsv'):
 if table.parent==T:continue
 for row in csv.DictReader(open(table),delimiter='\t'):
  try:n=int(row['n']);sc=float(row['new'])
  except (ValueError,KeyError):continue
  if 'take-k123-r36/' in row.get('source','') and sc<bar[n]-1e-10 and sc<=peer[n]+1e-13:
   peer_descendants.append({'lane':table.parent.name,'n':n,'score':sc,'gain_base':bar[n]-sc})
(W/'peer-descendants36.json').write_text(json.dumps(peer_descendants,indent=2))
measure.append('Lowest live peer rows whose recorded ancestry reaches this lane: '+json.dumps(peer_descendants)+'. These are peer gains, not own retained gain.')
measure+=load(W/'measurements28.json',[])
measure+=['Native source gains '+json.dumps({n:bar[n]-r['score'] for n,r in native.items()})]
if archives:measure+=['Verified archives '+json.dumps(archives)]
if (W/'finalwalk36.json').exists():measure+=['Final walk receipt: '+json.dumps(load(W/'finalwalk36.json'))]
nexts=['Join the next lowest live changed geometry first. Fresh band donors fed 693, 803, 549 and 790 in round35. This round native counts: '+str(sorted(native))+'.','Return certified near donors in board-room order before old recipes. This round published '+str(len(near))+' such donors.','Keep completed geometry signatures closed. '+str(hist.get('total',0))+' signatures were closed before dispatch. Reopen only after changing the physical input or finish mechanism.','Preserve one central atomic claim queue and start final walks early. Keep boxE at three slots and boxD at one. The one-worker trial paused3/60 samples, versus51/60 with two and45/60 with three. Both have independent load guards.']
nexts.insert(1,'Keep direct third-seam prejoins after a changed input. Private793 supplied native911 and private972 supplied native972 (1.43183e-5 against bar36). The unquenched starts stay private until a final certificate. Certified near donors feed the kick pool; one supplied border698 for2.83706e-5.')
if peer_descendants:
 best_desc=sorted(peer_descendants,key=lambda r:-r['gain_base'])
 nexts.insert(0,'Join newly changed lowest live descendants first. Measured live peer gains with this lane in their recorded ancestry: '+', '.join(str(r['n'])+'='+format(r['gain_base'],'.8g') for r in best_desc)+'. These gains remain credited to their producing lanes.')
report=dict(lane='k123',improved_n=len(low),gain={'against_base_bar':gain,'beyond_other_live_r36':beyond},take_dir=str(T),summary=f'{len(low)} retained rows beat bar36 and every live peer. {len(native)} native counts and {len(near)} near donors certified. '+('All lane workers stopped and box archives verified.' if stopped else 'Drivers active until the stated deadlines.'),what_was_measured=measure,next=nexts,commits=load(W/'commits34.json',[]),processes_left=0 if stopped else 'active; see STATE.txt',blocked=load(W/'blocked34.json','none'),repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
if '--artifacts' in sys.argv:
 counts=collections.Counter(r['n'] for r in records)
 with open(L/'results/k123-r36-2026-11-17.tsv','w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','score','gain_base','gain_other','source','licence'])
  for r in rows:
   n=int(r['n']);sc=float(r['new']);wr.writerow(['certified',n,counts[n],sc,bar[n]-sc,max(0,peer[n]-sc),r['source'],r.get('licence','')])
  for j in near:wr.writerow(['near',j['n'],counts[j['n']],j['score'],-j['gap'],0,j['source'],j['licence']])
  for n in sorted(counts):
   ss=[r['side']/n**.5-1 for r in records if r['n']==n and 'side' in r];wr.writerow(['attempts',n,counts[n],min(ss) if ss else '',0,0,'immutable inputs in take-k123-r36/work','per-input source records'])
 text=f'''## Round 36

The lane retains {len(low)} layouts below bar36 and every live peer.
The gain is {gain:.15g} against bar36 and {beyond:.15g} beyond the other takes.
It certified {len(native)} native counts and {len(near)} near donors.

The boxes completed {len(records)} numerical attempts on {len(counts)} counts.
The {len(scans)} donor scans covered {sum(j.get('pairs',0) for j in scans)} pairs.
The initial history closed {hist.get('total',0)} signatures, with {hist.get('missing',0)} missing manifests.
Changed held endpoints ran before valid near bands and old recipes.

boxE and boxD each ran at most three numerical slots.
One central atomic claim queue assigned recipes across both boxes.
Guards paused above load 16 on boxE and 9 on boxD.
The 444 controls reproduced side 21.564693167754 on both boxes.
The source control accepted own756 and rejected a changed producer record.

Each published layout passed finesafe at clearance 2.2e-11.
The full default and polish fq loop started from the certified file.
Source walks used a 100000-file cap and rejected unfinished walks.
Own and held layouts received no share gate.
Public-first rows retained the frozen share31 checks at 1e-3 and 1e-2.
The common search and quench deadline was 23:45 UTC.

Sources and measurements are in [the round table](../results/k123-r36-2026-11-17.tsv).
The [round helpers](../tools/k123/r36/) preserve the queue and source checks.
Receipts remain in `$SCRATCH/bounties-squares/take-k123-r36/work/`.
'''
 (W/'round36-section.md').write_text(text)
else:
 p=T/'report.json.tmp';p.write_text(json.dumps(report,indent=2)+'\n');p.replace(T/'report.json')
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}),flush=True)
