import csv,json,pathlib,sys,math,hashlib,subprocess,statistics
csv.field_size_limit(16*1024*1024)
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.')
sys.path.insert(0,str(W));from policy24 import classify,bars,RELAXED
from ancestry24 import clean
js=json.load(open(W/'jobs.json'));done={p.parent.name:json.load(open(p))for p in(W/'boxE-raw').glob('*/done.json')}
rs=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));a,b,bar,freebar,who,freewho=bars(T)
search=[j for j in js if j['kind']not in('control','rescue') and j['id']in done];rescues=[j for j in js if j['kind']=='rescue'and j['id']in done]
measurement=list(csv.DictReader(open(R/'results/invent-r24-2026-11-13.tsv'),delimiter='\t'))
tries=sum(int(r['tries']) for r in measurement if r['kind']not in('control','rescue'))
original=sum(a[int(r['n'])]-float(r['new'])for r in rs);net=accepted=0;groups={'none':[],'seeds':[]};proof=[]
for r in rs:
 n=int(r['n']);p=classify(r['source'],r['licence']);assert clean(r['source'],r['licence'])[0] and p['status']!='unknown',(n,p)
 free=n in RELAXED and p['status']=='none';limit=freebar[n] if free else bar[n];ref=b[n] if free else a[n]
 assert float(r['new'])<limit-1e-10 and float(r['new'])<ref-1e-10,(n,r['new'],limit,ref)
 net+=limit-float(r['new']);accepted+=ref-float(r['new']);groups[p['status']].append(n)
 proof.append(dict(n=n,policy=p,original_candidate=a[n],accepted_reference=ref,eligible_bar=limit,score=float(r['new']),sha256=hashlib.sha256((T/f'{n}.csv').read_bytes()).hexdigest()))
(W/'source-groups-final.json').write_text(json.dumps(proof,indent=2))
pending=[j for j in js if j['kind']!='control' and j['id']not in done]
(W/'pending-final.json').write_text(json.dumps(pending,indent=2))
eligible=[j for j in pending if clean(j['source'],j['licence'])[0] and classify(j['source'],j['licence'])['status']!='unknown']
saved_done=sum(j.get('backlog',False) and j['id']in done for j in js)
errors=[j for j in search if done[j['id']].get('error')];cancel=[j for j in errors if j['id']=='s2x577' or 'censored:' in done[j['id']].get('error','')];bounded=[j for j in errors if j not in cancel]
controls=[done[j['id']] for j in js if j['kind']=='control' and j['id']in done]
verification=json.load(open(W/'verification.json'));clearance=min((r['clearance']for r in verification),default=None)
cleanup=json.load(open(W/'cleanup.json'))if(W/'cleanup.json').exists()else{'processes_left':'Running; draft only.'}
commits=[]
for h in (W/'commits.txt').read_text().splitlines():
 if h.strip():commits.append(subprocess.check_output(['git','rev-parse',h.strip()],cwd=R.parent.parent,text=True).strip())
normal=[r for r in measurement if r['kind']not in('control','rescue')and not r['error']]
fresh=[r for r in normal if r['kind']=='fresh'];near=[r for r in normal if r['kind']=='near'];legs=[r for r in normal if r['kind']=='leg']
moving=lambda rows:[r for r in rows if float(r['final_side_gain'])>1e-8]
external={}
for p in S.glob('take-*-r24/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  n=int(r['n']);score=float(r['new'])
  if 'take-invent-r24' in r['source'] and (n not in external or score<float(external[n]['new'])):external[n]=dict(r,take=str(p))
(W/'descendant-rows.json').write_text(json.dumps(external,indent=2))
nexts=[
 'Kick fresh shell and join builds first. The newer 595 build and its one leg removed 0.000121654 and 0.000848757 of side. The first 985 join removed 0.000069120.',
 'Give a useful new find one leg. The successful 595 leg ended with 36 dry tries, so it received no unchanged extra leg. Other legs are measured separately in the run table.',
 f'Reconsider {len(eligible)} eligible pending immutable starts against the next bar. The saved 978, 599 and 645 snapshots removed 0.000211607, 0.000144773 and 0.000030911 of side.',
 'Keep 420 seconds for joins. Replay placed the first 985 move at 337.7 seconds. Ten other material fresh/control traces first moved within 180 seconds.',
 f'Change geometry before repeating the tested near layouts. {len(moving(near))} of {len(near)} normal near runs moved more than 1e-8 of side.',
 'Retain exact source-group evidence and read all main handoffs. The delayed 20:05 amendment changed the permitted bar for twenty seed-free counts. Source labels and fallback controls now cover it.'
]
report=dict(lane='invent',improved_n=len(rs),gain=dict(against_round23_candidate=original,beyond_other_live_r24=net),take_dir=str(T),summary=f'{len(search)} production search attempts and {len(rescues)} finish-only rescues on three boxE slots, {tries} completed search tries. {len(rs)} retained counts. Seed-free counts: '+','.join(map(str,groups['none']))+'. Seed descendants are labelled separately.',what_was_measured=[
 f'{len(search)} production search attempts ended, with {len(bounded)} bounded errors and {len(cancel)} early manual cancellations. The run table records exact starts, flags, source groups and tries.',
 f'{len(moving(fresh))}/{len(fresh)} normal fresh runs, {len(moving(near))}/{len(near)} normal near runs and {len(moving(legs))}/{len(legs)} normal legs moved more than 1e-8 of final side.',
 f'{saved_done}/47 eligible saved starts ended. Four initial starts failed source checks and three more remained quarantined for missing exact ancestry. Pending inputs and metadata are saved in work/pending-final.json.',
 'The full 907 control passed at try 4 and reproduced side 30.618227092836 at try 9. The 180-second probe passed the squeeze stop and its certified-input quench, but did not reproduce the full control drop.',
 'Fresh capacity was reserved, then corrected after saved 577 occupied it. New counts and seed-free starts gained priority. The admission window widened to 0.015 of side, and exact public handoff paths became a direct feed.',
 'The original broad count filter also hid clean new public starts at excluded old counts. A control accepts new public639 and rejects old harvest639, old forensics980 and candidate801.',
 'The bounded 985 search left four completed raw finds. A zero-search finish-only job certified them and completed fq from the certified file. The separate timed-out 871 quench had no completed output and was not published.',
 f'Original candidate gain is {original:.12g}. Gain against the permitted source-group references is {accepted:.12g}. Seed-free exceptions use round22 for the twenty held counts and compare with seed-free live peers. Seed descendants keep the original candidate bar.',
 'Source-group controls accepted a clean layout above a fixed original-candidate bar and below its fallback. A lower seeded peer did not mask it. Seeded and unknown copies failed. Changed metadata changes the source-cache key.',
 f'Every published result passed floatsafe at 2.2e-11 and completed a boxE fq quench from its certified input. Final uncached metric/pandas checks covered {len(verification)} retained files; minimum clearance {clearance}. CSVs preceded atomic take.tsv replacements.',
 f'{len(external)} external live rows retain invent-r24 ancestry and are excluded from this take count. Their exact records are in work/descendant-rows.json.',
 cleanup['processes_left']
 ],next=nexts,commits=commits,processes_left=cleanup['processes_left'],blocked=f'No access block. {len(eligible)} eligible queued starts remain unrun within the three-slot budget. Unresolved or excluded source records remain quarantined.',repo='private repo',branch='main',worktree=str(R.parent.parent),pr='none')
assert set(report)=={'lane','improved_n','gain','take_dir','summary','what_was_measured','next','commits','processes_left','blocked','repo','branch','worktree','pr'}
(W/'report-draft.json').write_text(json.dumps(report,indent=2))
if '--final' in sys.argv:
 q=T/'report.json.tmp';q.write_text(json.dumps(report,indent=2)+'\n');q.replace(T/'report.json')
if '--doc' in sys.argv:
 text=f'''\n## 19. Round 24 (2026-11-13)\n\nThe final take holds {len(rs)} counts and gains {original:.12g} on the original round 23 candidate.\nIt gains {net:.12g} below the other eligible live takes.\n{len(search)} production search attempts and {len(rescues)} finish-only rescues ended on three boxE slots.\nThe search attempts completed {tries} tries.\n\n### 19.1 Controls and search\n\nThe full 907 control passed the squeeze stop at try 4.\nTry 9 reproduced side 30.618227092836.\nThe 180-second probe also passed the stop and completed its certified-input quench.\nIt did not reproduce the full control drop.\n\nReplay placed ten material fresh/control first moves within 180 seconds.\nThe 985 join first moved at 337.7 seconds, so joins kept 420 seconds.\nNew starts without joins or per-try fq received shorter first probes after the control passed.\nSaved starts retained their original budgets, and legs kept 420 seconds.\nSearch and quench shared the 22:15 UTC deadline.\n\nOne slot reserved fresh layouts.\nSaved 577 initially occupied that slot after the control.\nIts early cancellation has a censored trace and no raw result.\nThe corrected queue gives fresh take and near layouts priority.\nNew counts get a first pass before further versions, with seed-free inputs first among equal groups.\nTwo admission places remain available when the pending queue is full.\nThe near window grew to 0.015 of side.\nExact public handoff paths now feed the queue even when a kick lane owns their count.\n\n{saved_done} of 47 eligible saved starts ended.\nFour initial inputs failed source checks, and three more lacked exact ancestry.\nThe saved 978, 599 and 645 snapshots removed 0.000211607, 0.000144773 and 0.000030911 of side.\n\n### 19.2 Source groups and certification\n\nThe main session changed the source-group rule at 20:05 UTC.\nThis lane applied it late and recorded the correction in STATE.txt.\nEvery retained licence now names its Samanyu seed counts or states that no such seed occurs.\nSeed descendants must beat the original candidate.\nOn twenty held counts, seed-free rows can instead beat the round 22 reference.\nTheir live comparison also uses seed-free peers.\nThe reported original-candidate gain stays separate from that permitted-reference gain.\n\nThe fallback control accepted a clean row above a fixed candidate bar and below its permitted reference.\nSeeded and unresolved copies failed.\nA lower seeded peer did not mask the clean row.\nThe cache control retained identical output, rejected an overlapping file, and restored identical output after repair.\nChanged source metadata gives another classification-cache key.\nExact near sidecars preserve upstream notices, including Other terms.\n\nEach published file passed floatsafe at 2.2e-11 and received fq from its certified input on boxE.\nPer-n files preceded an atomic replacement of take.tsv.\nFinal uncached metric and pandas checks covered {len(verification)} files.\nMinimum clearance was {clearance}.\nThe bounded 985 search left four raw finds.\nA finish-only job certified and quenched them without another search try.\nThe timed-out 871 quench produced no completed output and stayed out.\n\n### 19.3 Measurements\n\n| Start | Normal runs | Moved by more than 1e-8 of side |\n| --- | --- | --- |\n| Fresh | {len(fresh)} | {len(moving(fresh))} |\n| Near | {len(near)} | {len(moving(near))} |\n| Leg | {len(legs)} | {len(moving(legs))} |\n\nThe newer 595 fresh build removed 0.000121654 of side.\nIts one leg removed another 0.000848757, then ended with 36 dry tries.\nThe first 985 join removed 0.000069120.\nThe 542 scan removed 0.000790177 but stayed above the live bar.\n{len(external)} external live rows retain invent ancestry and are excluded from this take count.\n\n| n | Final score | Gain on original candidate | Source group |\n| --- | --- | --- | --- |\n'''
 for r in rs:
  n=int(r['n']);p=classify(r['source'],r['licence']);group='No Samanyu seed' if p['status']=='none' else 'Seed '+','.join(map(str,p['seeds']))
  text+=f"| {n} | {float(r['new']):.12f} | {a[n]-float(r['new']):.9g} | {group} |\n"
 text+='\n### 19.4 Next\n\n'
 for i,item in enumerate(nexts,1):text+=str(i)+'. '+item+'\n'
 text+='\n[The run table](../results/invent-r24-2026-11-13.tsv) retains every completed trace and its source records.\n[The round tools](../tools/invent/round24/controller24.py) retain the collector, worker and source checks.\nExact starts, pending manifests and proofs remain in take-invent-r24/work.\n'
 (W/'round24-doc.md').write_text(text)
 doc=R/'avenues/invent.md';base=doc.read_text().split('\n## 19. Round 24')[0];doc.write_text(base+text)
print(json.dumps({'retained':len(rs),'original_gain':original,'eligible_net':net,'search_attempts':len(search),'rescues':len(rescues),'tries':tries,'pending_eligible':len(eligible),'groups':groups}))
