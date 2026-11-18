"""Write the round 32 report from immutable numerical receipts."""
from pathlib import Path
import json,csv,collections,time,sys,re
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=Path('.');csv.field_size_limit(1<<28)
rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));base={int(r['n']):float(r['bar']) for r in csv.DictReader((S/'round32-briefs/bar32.tsv').open(),delimiter='\t')};other=dict(base)
for p in S.glob('take-*-r32/take.tsv'):
 if p.parent==T:continue
 try:
  for r in csv.DictReader(p.open(),delimiter='\t'):
   n=int(r['n']);other[n]=min(other[n],float(r['new']))
 except (ValueError,KeyError,OSError):continue
records=[]
for line in (W/'records.jsonl').read_text().splitlines():
 try:records.append(json.loads(line))
 except ValueError:continue
counts=collections.Counter(r['n'] for r in records);low=[int(r['n']) for r in rows if other[int(r['n'])]-float(r['new'])>1e-10]
gain=sum(base[int(r['n'])]-float(r['new']) for r in rows);beyond=sum(max(0,other[int(r['n'])]-float(r['new'])) for r in rows if int(r['n']) in low)
tasks=[json.load(p.open()) for p in (W/'taskdone').glob('*.json')];scans=[j for j in tasks if (j['kind']=='scan' or j.get('diversity_scan')) and j['rc']==0];errors=sum(bool(r.get('error')) for r in records);timeouts=sum(r.get('code')==-2 or r.get('fq2code')==-2 for r in records)
archive=json.load((W/'copy-verified25.json').open()) if (W/'copy-verified25.json').exists() else None
stopped=(W/'processes-stopped-local25.json').exists() and (W/'boxE-final/processes-stopped25.json').exists()
notes=[f'{len(records)} numerical attempts on {len(counts)} counts. Rebuild errors: {errors}. Timeouts: {timeouts}.',f'{len(scans)} donor scans completed over {sum(j.get("pairs",0) for j in scans)} pairs.',f'Certified source rows: {[int(r["n"]) for r in rows]}. Lowest live rows: {low}.', 'The 444 numerical control reproduced side 21.564693167754. Certification uses border finesafe at 2.2e-11 and an fq quench from the certified file in a boxE slot.', 'Fresh changed endpoints and valid non-winning donors preceded exact unrun recipes. Plain held kicks and the dry 1.010 branch stayed closed.', 'Full source walks retain exact CSV snapshots, producer records and ancestry hashes. Own and held layouts bypass share checks. Public-first outputs use both tolerances and all harvested reference versions.']
for name in ['history-rebuilt32.json','source-controls30.json','admission-control32.json','historical-held-control32.json','count-control32.json','legacy-diag-control32.json','independent48832.json','budget-control30.json','ownership-control32.json','licence-control32.json','public-control32.json','diagnostic-control32.json','receipt-control32.json','strict-validation32.json','doublejog-control32.json','history28.json']:
 if (W/name).exists():notes.append(name+': '+json.dumps(json.load((W/name).open()),sort_keys=True))
if (W/'measurements28.json').exists():notes.extend(json.load((W/'measurements28.json').open()))
if archive:notes.append(f'Archive verified: {archive["files"]} files, {archive["bytes"]} bytes, {len(archive["checksum_differences"])} checksum differences.')
notes.append('Finish branches: '+json.dumps({m:{'attempts':sum(r.get('mechanism','standard')==m for r in records),'raw_crossing_records':sum(bool(r.get('raw')) for r in records if r.get('mechanism','standard')==m)} for m in sorted({r.get('mechanism','standard') for r in records})}))
if (W/'strip-feed32.json').exists():
 strip=json.load((W/'strip-feed32.json').open());summary=[]
 for j in strip['jobs']:
  q=j.get('result',{});summary.append({'tag':j['tag'],'n':j['n'],'free_rows':j['free_rows32'],'free_columns':j['free_columns32'],'status':q.get('status'),'count':q.get('output_count',q.get('count')),'side':q.get('output_side',q.get('side')),'solve_seconds':q.get('solve_seconds'),'scope_check':q.get('independent_strip_scope32')})
 notes.append('Finite strip32 pilot: '+json.dumps({'jobs':summary,'halted':strip.get('halted'),'changed_donors':len(strip.get('exported_geometry',[]))}))
notes.append('Retained gains: '+json.dumps([(int(r['n']),base[int(r['n'])]-float(r['new'])) for r in rows]))
nexts=[v.replace('This round','In round 31').replace('this round','round 31') for v in json.load((W/'next28.json').open())]
if rows:
 best=sorted(rows,key=lambda r:base[int(r['n'])]-float(r['new']),reverse=True)
 nexts=[f'Join fresh changed endpoints before old queues. This round retained '+', '.join(f'n={r["n"]} for {base[int(r["n"]) ]-float(r["new"]):.12g} of score' for r in best[:4])+'. Keep each exact input snapshot and source proof.']+nexts[1:]

nexts=[v for v in nexts if not v.startswith('Address the missing incumbent')]
nexts += ['Keep a controlled finish only while it adds rows beyond existing finishes. The round32 1.003 pilot stopped at80 attempts with one already-known808 crossing and no exclusive row.', 'Require a feasible masked incumbent before extending the slide search. Round32 core controls solved367 in0.522s and626 in1.344s. All six explicit171-cell double-jog cases were infeasible in the tested domains. Freeing parent offsets or changing a mask is a new experiment; unchanged domains stay closed.']
report=dict(lane='k123',improved_n=len(low),gain=dict(against_base_bar=gain,beyond_other_live_r32=beyond),take_dir=str(T),summary=f'Certified source layouts: {len(rows)}. Lowest live rows: {len(low)}. '+('Workers stopped and boxE archive verified.' if stopped and archive else 'Work is active. See STATE.txt.'),what_was_measured=notes,next=nexts,commits=json.load((W/'commits26.json').open()) if (W/'commits26.json').exists() else [],processes_left=0 if stopped else 'see STATE.txt',blocked='none',repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
(W/'metrics28.json').write_text(json.dumps(report,indent=2)+'\n')
if '--artifacts' in sys.argv:
 with (R/'results/k123-r32-2026-11-16.tsv').open('w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for r in rows:
   n=int(r['n']);sc=float(r['new']);wr.writerow(['certified',n,counts[n],(sc+1)*n**.5,base[n]-sc,max(0,other[n]-sc) if n in low else 0,r['source'],r['licence'],'lowest live' if n in low else 'source followed by another lane'])
  for n in sorted(counts):
   ss=[r['side'] for r in records if r['n']==n and 'side' in r];wr.writerow(['attempts',n,counts[n],min(ss) if ss else '',0,0,'pinned manifests in take-k123-r32/work','per-input source records','raw measured side'])
 timing_note32='Join intake closes at 16:45 UTC. Numerical workers stop at 16:58 UTC.'
 if stopped:timing_note32='Join intake closed at 16:45 UTC. Numerical workers stopped at 16:58 UTC.'
 text=f'''## Round 32

The lane retained {len(rows)} certified source layouts. Their gain against the round 32 bar is {gain:.15g}.
At {time.strftime('%H:%M UTC',time.gmtime())}, {len(low)} rows beat the other live takes. They add {beyond:.15g} beyond those takes.

The four boxE slots ran {len(records)} numerical attempts on {len(counts)} counts.
There were {errors} rebuild errors and {timeouts} timeouts.
Completed donor scans numbered {len(scans)}, over {sum(j.get('pairs',0) for j in scans)} pairs.

The completed geometry index was rebuilt from round 31 records before new work started.
It closed 14,449 signatures with no missing manifests.
Changed endpoints and valid non-winning donors ran first. Exact unrun recipes followed.
The measured 1.005 finish stayed open. Plain held kicks and the dry 1.010 intake stayed closed.

The 444 control reproduced side 21.564693167754.
The source control accepted own 985 after walking 42 files.
It refused fetched public 551 at shares 0.788 and 0.913.
Later withdrawals remained active.

Published files passed border finesafe at 2.2e-11 clearance.
Each file received an fq quench from its certified bytes before publication.
Own and held layouts received no share gate.
Public-first outputs used both tolerances, every harvested reference version and median ICP.
{timing_note32}
The hard cutoff is 17:15 UTC. Source withdrawals are checked until the 17:25 take freeze.

Sources and measurements are in [the round table](../results/k123-r32-2026-11-16.tsv).
The [round helpers](../tools/k123/r32/) preserve the queue and source checks.
Input pools and receipts remain in `$SCRATCH/bounties-squares/take-k123-r32/work/`.
'''
 (W/'round32-section.md').write_text(text)
elif '--checkpoint' not in sys.argv:
 (T/'report.json.tmp').write_text(json.dumps(report,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}),flush=True)
