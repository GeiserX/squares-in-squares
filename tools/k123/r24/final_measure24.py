"""Write the round table, doc and report after workers stop and archive verification."""
import pathlib,json,csv,collections,math,sys,os,shutil
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));T=W.parent;S=T.parent;R=pathlib.Path('$PRIVATE_REPO');csv.field_size_limit(20000000)
draft='--draft' in sys.argv
if not draft:assert (W/'processes-stopped24.json').exists() and (W/'copy-verified24.json').exists()
from eligible24 import SPECIAL,B
from seed_notice24 import notice
held22={int(r['n']):float(r['score']) for r in csv.DictReader(open(B))}
held={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round23-1113a/details.csv'))}
take=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));other=dict(held)
for p in S.glob('take-*-r24/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);other[n]=min(other[n],float(r['new']))
  except (ValueError,KeyError):pass
no_seed={int(r['n']) for r in take if notice(r['source'],r['licence'])[1] is False}
for n in no_seed&SPECIAL:
 other[n]=held22[n]
 for p in S.glob('take-*-r24/take.tsv'):
  if p.parent==T:continue
  for q in csv.DictReader(open(p),delimiter='\t'):
   if int(q['n'])==n and notice(q.get('source',''),q.get('licence',''))[1] is False:other[n]=min(other[n],float(q['new']))
best=[r for r in take if float(r['new'])<other[int(r['n'])]-1e-10];gain=sum(held[int(r['n'])]-float(r['new']) for r in take);extra=sum(other[int(r['n'])]-float(r['new']) for r in best)
records=[]
for line in (W/'records.jsonl').read_text().splitlines():
 try:records.append(json.loads(line))
 except ValueError:pass
def kind(r):
 p=r['pool']
 if r.get('licensed_reconstruction'):return 'licensed'
 return 'fresh' if p.startswith('fresh') and int(p[5:])>=10000 else 'deferred' if p.startswith('defer') else 'saved'
bykind=collections.Counter(kind(r) for r in records);by_n=collections.defaultdict(list)
for r in records:by_n[r['n']].append(r)
state=json.load(open(W/'collect-state.json'));wins=collections.defaultdict(list)
for r in take:
 n=int(r['n']);hit=next((q for q in records if any(v.get('status')=='published' and v.get('n')==n and abs(float(v.get('score',math.inf))-float(r['new']))<1e-13 and key==q['worker']+'-'+q['pool']+'-'+q['tag'] for key,v in state.items())),None)
 if hit:wins[kind(hit)].append(float(r['held'])-float(r['new']))
scans=[]
for p in (W/'taskdone').glob('*.json'):
 try:j=json.load(open(p))
 except ValueError:continue
 if j.get('kind')=='scan' and j.get('rc')==0:scans.append(j)
errors=sum(bool(r.get('error')) for r in records);timeouts=sum(r.get('code')==-2 for r in records)
licensed_extra=sum(other[int(r['n'])]-float(r['new']) for r in best if int(r['n']) in no_seed)
metrics=dict(source_rows=len(take),lowest_rows=len(best),gain_against_round23=gain,gain_beyond_other_live_r24=extra,without_samanyu_beyond_other_live_r24=licensed_extra,lowest_n=[int(r['n']) for r in best],attempts=len(records),counts=len(by_n),scans=len(scans),pairs=sum(j.get('pairs',0) for j in scans),by_kind=dict(bykind),wins_by_kind={k:dict(rows=len(v),gain=sum(v)) for k,v in wins.items()},rebuild_errors=errors,timeouts=timeouts)
(W/'final-metrics24.json').write_text(json.dumps(metrics,indent=2))
# Final table follows the existing lane table format.
result=R/'lanes/squares/results/k123-r24-2026-11-13.tsv'
with open(result,'w',newline='') as f:
 wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','source','tries','side','bar','side_minus_bar','note'])
 wr.writerow(['control',444,'680 down5 rows and7 chains',1,21.564693167754,21.564693168782,21.564693167754-21.564693168782,'known side reproduced within1.1e-9'])
 for n,rr in sorted(by_n.items()):
  sides=[float(r['side']) for r in rr if r.get('side') is not None];side=min(sides) if sides else '';bar=(held[n]+1)*math.sqrt(n)
  wr.writerow(['joins',n,'immutable pools and recipes in take-k123-r24/work/records.jsonl',len(rr),side,bar,side-bar if side!='' else '',json.dumps(collections.Counter(kind(r) for r in rr))])
 for r in take:
  n=int(r['n']);side=(float(r['new'])+1)*math.sqrt(n);bar=(float(r['held'])+1)*math.sqrt(n)
  wr.writerow(['certified',n,r['source'],1,side,bar,side-bar,'gain_round23='+repr(held[n]-float(r['new']))+'; gain_beyond_other_live_r24='+repr(max(0.,other[n]-float(r['new'])))+'; licence='+r['licence']])
# Archive the helpers that ran. Run these copies from the take work directory.
D=R/'lanes/squares/tools/k123/r24';D.mkdir(parents=True,exist_ok=True)
files=sorted(p.name for p in W.glob('*.py'))
for name in files:shutil.copy(W/name,D/name)
text=f'''\n## 17. Round 24\n\nThe lane certified {len(take)} source rows against the eligible baseline. Their combined score gain against the scientific round 23 candidate is {gain:.12g}. Seed-free rows can also recover the 20 restored counts against the eligible round 22 cutoff. At the final comparison, {len(best)} rows beat every other live take under the same source rule. They add {extra:.12g} beyond those takes.\n\nThe four boxE slots ran {len(records)} joins on {len(by_n)} counts. There were {errors} rebuild errors and {timeouts} timed out joins. Completed donor scans numbered {len(scans)}, over {metrics['pairs']} pairs.\n\nThe saved queue came first, with unused counts ahead of repeats. The expanded source audit retained 8,617 of 15,172 saved starts. The next pass removed completed recipes and identical input pairs. Every retained pool has its own geometry and source record.\n\nFresh layouts stayed ahead of saved starts. Deferred partners used their saved full catalogs. The trial counts were {bykind.get('fresh',0)} fresh, {bykind.get('deferred',0)} deferred and {bykind.get('saved',0)} saved. Samanyu-derived rows retained the candidate cutoff. Seed-free results at the 20 held counts used the round 22 cutoff after the main session's notice.\n\nThe 444 control printed side 21.564693167754. It matches the known side within 1.1e-9. Source controls accepted recorded rectangle parents and rejected forbidden 639, the BY-SA file and held 801. Nested 801 source arrays were also rejected.\n\nThe scratch cap keeps productive partners when use reaches 1.7 GB. It preserves each full input locally. Its control kept donor 928 where selection by side alone dropped it. SSH connection reuse reduced the measured command time from 2.836 to 0.504 seconds.\n\nEach published row passed floatsafe at 2.2e-11 clearance. Each also received a boxE fq quench from its certified file before publication. Saved reader ledgers and sidecars expand the ancestry. The source and licence cells carry any areebbb per-n upstream chain. Withdrawn inputs were checked again before publication.\n\n| n | side | gain over eligible baseline |\n|---|---|---|\n'''
for r in take:
 n=int(r['n']);text+=f"| {n} | {(float(r['new'])+1)*math.sqrt(n):.12f} | {float(r['held'])-float(r['new']):.9g} |\n"
text+=f'\nThree licensed reconstructions recover the held counts without using GitHub seed files as packing inputs. They start from actual CC0 public inputs. The other source rows carry their Samanyu seed numbers for the owner decision.\n\nThe 365 fault control reached 19.610439666400, within 4e-10 of its recorded side. A 300-second kick then reached 19.608277773041. Its rectangle and join supplied licensed 581. The self-join supplied licensed 228.\n\nThe historical 734 polish control remained at 27.600801734814. Its expected side was 27.591378146833, so that replay failed. The different, unpolished legal 734 was joined with the Apache 630 instead. That independent join reached the prior 847 floor and passed certification.\n\nOne 927 source row was withdrawn after its older ledger revealed seed 811. It did not beat the stricter candidate cutoff. The 907 source audit also excluded one earlier no-win trial and removed 39 queued starts. None of the retained rows uses 907.\n'
text+='\nThe [round table](../results/k123-r24-2026-11-13.tsv) records each count and source row. The [helpers](../tools/k123/r24/) preserve the queue and source checks. They run from the take work directory.\n\nAll lane processes stopped. boxE archive was copied and verified before its scratch directory was removed. The shared boxE base was preserved.\n'
if draft:text=text.replace('All lane processes stopped. boxE archive was copied and verified before its scratch directory was removed. The shared boxE base was preserved.','Search continues until 22:15 UTC. Final validation and archive verification follow that cutoff.')
(W/'round24-doc.md').write_text(text)
doc=R/'lanes/squares/avenues/k123.md';old=doc.read_text().split('\n## 17. Round 24')[0];doc.write_text(old+text)
ranked=sorted(['licensed','fresh','deferred','saved'],key=lambda k:sum(wins[k])/max(1,bykind[k]),reverse=True)
nexts=[]
for k in ranked:
 nexts.append(f"Resume {k} joins on changed inputs. This pass measured {bykind[k]} attempts, {len(wins[k])} source rows and {sum(wins[k]):.12g} score gain. Preserve full input and licence snapshots.")
if any(int(r['n'])==968 for r in take):
 nexts.insert(1,'Rebuild the 735 and 790 parents from licensed public inputs before trying the 968 recipe again. The provisional 735/790 join gained 0.0001435782 at 968, and its child gained 0.0000434269 at 489.')
nexts+=['Run every fresh certified layout and near design before repeated starts. The source rows and their reader returns remain in the take directory.','Resume any omitted cap partners from work/cap-deferred24.jsonl. The cap retains donor 928 and stores every complete input locally.']
verified=json.load(open(W/'copy-verified24.json')) if (W/'copy-verified24.json').exists() else {'status':'pending'}
measured=[f"Licensed rows without GitHub seed inputs: {sorted(no_seed)}. Their eligible gain is {sum(float(r['held'])-float(r['new']) for r in take if int(r['n']) in no_seed):.12g}. Remaining rows name their Samanyu seeds and are provisional.",'Historical 734 replay control failed at 27.600801734814 versus 27.591378146833. The unpolished licensed 734 join was a separate tested input.','Withdrew 927 after resolving seed 811. Excluded one prior no-win 907 trial and 39 queued starts. No retained row uses 907.',f"{len(records)} joins on {len(by_n)} counts, {errors} rebuild errors and {timeouts} timeouts.",f"{len(scans)} completed donor scans over {metrics['pairs']} pairs.",f"Expanded saved-input audit retained 8,617 of 15,172 starts. Conservative completed-recipe exclusion and exact-input deduplication kept immutable pools.",'Control 444 printed 21.564693167754 and matched the known side within 1.1e-9.','Source controls accepted recorded rectangle parents and rejected forbidden 639, BY-SA and held 801, including nested source arrays.','The cap control retained 928 while the old side-only control dropped it. SSH command time measured 2.836s versus 0.504s with reuse.',f"{len(take)} source rows passed floatsafe at 2.2e-11 and certified-file boxE quenches. Final gains were recomputed against every live take under the same source rule.",f"Archive verification: {verified['files']} files, {verified['bytes']} bytes, no checksum differences." if not draft else "Archive verification pending."]
report=dict(lane='k123',improved_n=len(best),gain=dict(against_round23=gain,against_eligible_baseline=sum(float(r['held'])-float(r['new']) for r in take),without_samanyu_eligible_gain=sum(float(r['held'])-float(r['new']) for r in take if int(r['n']) in no_seed),over_other_live_r24=extra,without_samanyu_over_other_live_r24=licensed_extra),take_dir=str(T),summary=f"{len(take)} certified source rows, {len(no_seed)} rebuilt without GitHub seed inputs; {len(best)} remain lowest under the eligible comparison. The other {len(take)-len(no_seed)} rows retain explicit Samanyu seed notices and are provisional. All workers stopped. Sources and licences are recorded per row, and boxE archive is verified.",what_was_measured=measured,next=nexts,commits=[],processes_left='none; boxE search and certificate workers and local controllers stopped. Lane scratch removed after verification. Shared base preserved. boxC and boxD were not used.',blocked='',repo=str(R)+' (private repo)',branch='main',worktree=str(R),pr='')
if draft:print(json.dumps(metrics));sys.exit(0)
(T/'report.json.tmp').write_text(json.dumps(report,indent=2));(T/'report.json.tmp').replace(T/'report.json');print(json.dumps(metrics))
