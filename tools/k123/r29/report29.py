"""Write measured round 29 artifacts and the report after the take deadline."""
import pathlib,json,csv,collections,time,sys,datetime
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.');csv.field_size_limit(1<<28)
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));base={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round29-briefs/bar29.tsv'),delimiter='\t')};other={}
for p in S.glob('take-*-r29/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);other[n]=min(other.get(n,base[n]),float(r['new']))
  except (ValueError,KeyError):pass
records=[]
if (W/'records.jsonl').exists():
 for line in (W/'records.jsonl').read_text().splitlines():
  try:records.append(json.loads(line))
  except ValueError:pass
counts=collections.Counter(r['n'] for r in records);groups=collections.Counter('resume' if r['pool'].startswith('resume') else 'fresh' if r['pool'].startswith('fresh') else 'other' for r in records)
low=[int(r['n']) for r in rows if float(r['new'])<other.get(int(r['n']),base[int(r['n'])])-1e-10]
gain=sum(base[int(r['n'])]-float(r['new']) for r in rows);beyond=sum(other.get(int(r['n']),base[int(r['n'])])-float(r['new']) for r in rows if other.get(int(r['n']),base[int(r['n'])])-float(r['new'])>1e-10)
tasks=[json.load(open(p)) for p in (W/'taskdone').glob('*.json')];scans=[j for j in tasks if (j['kind']=='scan' or j.get('diversity_scan')) and j['rc']==0]
archive=json.load(open(W/'copy-verified25.json')) if (W/'copy-verified25.json').exists() else None
stopped=(W/'processes-stopped-local25.json').exists() and (W/'boxE-final/processes-stopped25.json').exists()
errors=sum('error' in r for r in records);timeouts=sum(r.get('code')==-2 or r.get('fq2code')==-2 for r in records)
notes=[f'{len(records)} join attempts on {len(counts)} counts, groups {dict(groups)}; {errors} rebuild errors and {timeouts} timeouts.',f'{len(scans)} completed donor scans over {sum(j.get("pairs",0) for j in scans)} pairs.',f'Certified source counts {[int(r["n"]) for r in rows]}; lowest live counts {low}. Published files passed floatsafe at 2.2e-11 and a boxE fq quench from the certified file.','The 444 numerical control printed side 21.564693167754 against 21.564693168782. boxE verifier control checks frozen 580 against round25b.','Fresh round28 and round29 endpoints precede exact unrun recipes. Inherited completed geometry signatures remain closed.','Source gates retain the complete source walk, excluded publication checks and live withdrawals. Under the main 00:19:03Z update, a share match does not refuse own layouts or their descendants.','Queue inputs and producer records are byte snapshots with SHA256. Four boxE numerical slots share the search and quench deadline 11:45 UTC.', 'Certification uses border finesafe bisected dilation, with 2.2e-11 clearance and official metric checks before and after pandas parsing.']
if archive:notes.append(f'Archive verified: {archive["files"]} files, {archive["bytes"]} bytes, {len(archive["checksum_differences"])} checksum differences.')
if (W/'measurements28.json').exists():notes.extend(json.load(open(W/'measurements28.json')))
if (W/'history28.json').exists():
 history=json.load(open(W/'history28.json'));notes.append(f'Closed geometry history: {history["total"]} signatures, {history["new"]} added, no missing source manifests.')
third=[];pool_cache={}
for r in records:
 pool=r['pool']
 if pool not in pool_cache:
  p=W/pool/('sources-'+pool+'.json');pool_cache[pool]=json.load(p.open()) if p.exists() else {}
 import re
 match=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if match and any('-threeway28-' in pool_cache[pool].get(n,{}).get('origin','') for n in match.groups()):third.append(r)
notes.append(f'Third-band donor joins: {len(third)} attempts in {len(set(r["pool"] for r in third))} pools; raw crossings {[(r["n"],r["side"]) for r in third if r.get("raw")]}.')
notes.append('Retained source gains by count: '+str([(int(r['n']),base[int(r['n'])]-float(r['new'])) for r in rows]))
nexts=json.load(open(W/'next28.json')) if (W/'next28.json').exists() else ['Join source-cleared fresh endpoints first. Round27 retained 753/868 and 698/752 joins with gains 2.5533592418192086e-7 and 1.0002231021211117e-7.','Resume exact unrun recipes after fresh endpoints, keeping the completed geometry signatures closed. Repeat a measured recipe only after changing its geometry or failure condition.','Keep exact original-seed and full CSV ancestor checks before dispatch. Round27 withdrew 699/932 for seed503 share 1.0 and 798 for ancestor742 share 0.454178.','Keep metadata batches bounded and numerical work in the four boxE slots. Round27 full partner walks stalled over 20 minutes before the 12-partner admission cap.']
report=dict(lane='k123',improved_n=len(low),gain=dict(against_base_bar=gain,beyond_other_live_r29=beyond),take_dir=str(T),summary=f'Certified source layouts: {len(rows)}. Lowest live rows: {len(low)}. '+('All lane workers stopped and boxE archive verified.' if stopped and archive else 'See STATE.txt for current worker and archive status.'),what_was_measured=notes,next=nexts,commits=json.load(open(W/'commits26.json')) if (W/'commits26.json').exists() else [],processes_left='none' if stopped else 'see STATE.txt',blocked='none',repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
(W/'metrics28.json').write_text(json.dumps(report,indent=2)+'\n')
if '--artifacts' in sys.argv:
 table=R/'results/k123-r29-2026-11-15.tsv'
 with open(table,'w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for r in rows:
   n=int(r['n']);sc=float(r['new']);wr.writerow(['certified',n,counts[n],(sc+1)*n**.5,base[n]-sc,(other.get(n,base[n])-sc if other.get(n,base[n])-sc>1e-10 else 0),r['source'],r['licence'],'lowest live' if n in low else 'lower follower source'])
  for n in sorted(counts):
   rr=[r for r in records if r['n']==n];ss=[r['side'] for r in rr if 'side' in r];wr.writerow(['attempts',n,len(rr),min(ss) if ss else '',0,0,'pinned input pools in take-k123-r29/work','per-input manifests','raw measured side'])
 text=f'''## Round 29

The lane retained {len(rows)} certified source layouts. Their gain against the round 29 bar is {gain:.15g}.
At this comparison, {len(low)} {'row beats' if len(low)==1 else 'rows beat'} the other live takes.
The gain beyond those takes is {beyond:.15g}.

Fresh endpoints and non-winning two-band outputs returned as donors for another cut.
A separate controller admits intermediate donors so a slow source walk cannot delay fresh scans.

The four boxE slots ran {len(records)} joins on {len(counts)} counts.
There were {errors} rebuild errors and {timeouts} timeouts.
Completed donor scans numbered {len(scans)}, over {sum(j.get('pairs',0) for j in scans)} pairs.

Fresh endpoints ran before exact unrun recipes. Completed geometry signatures remained closed.
Queue inputs and producer records have byte snapshots and SHA256 hashes.
The source checks follow the complete recorded ancestry and live withdrawals.
The main 00:19:03Z rule allows own layouts and descendants despite a public share match.
Fetched public starts still meet the share gate. Recorded excluded-file ancestry remains out.
Samanyu-matching ancestry remains allowed. The remaining excluded publications and withdrawn ancestors stay out.

The 444 control printed side 21.564693167754. Its reference is 21.564693168782.
Published files passed floatsafe at 2.2e-11 clearance and an fq quench from the certified file.
The common search and quench deadline was 11:45 UTC.

Sources and measurements are in [the round table](../results/k123-r29-2026-11-15.tsv).
The [round helpers](../tools/k123/r29/) preserve the queue and source checks.
Input pools and receipts remain in `$SCRATCH/bounties-squares/take-k123-r29/work/`.
'''
 (W/'round29-section.md').write_text(text)
else:
 assert time.time()>=datetime.datetime(2026,11,15,11,55,1,tzinfo=datetime.timezone.utc).timestamp(),'report must follow take deadline'
 (T/'report.json.tmp').write_text(json.dumps(report,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}),flush=True)
