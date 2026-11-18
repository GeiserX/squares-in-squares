"""Write the round 33 measurements from numerical and source receipts."""
from pathlib import Path
import json,csv,collections,time,sys
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=Path('.');csv.field_size_limit(1<<28)
rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));base={int(r['n']):float(r['bar']) for r in csv.DictReader((S/'round33-briefs/bar33.tsv').open(),delimiter='\t')};other=dict(base)
for p in S.glob('take-*-r33/take.tsv'):
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
gain=sum(base[int(r['n'])]-float(r['new']) for r in rows);beyond=sum(other[int(r['n'])]-float(r['new']) for r in rows if int(r['n']) in low)
tasks=[json.load(p.open()) for p in (W/'taskdone').glob('*.json')];scans=[j for j in tasks if (j['kind']=='scan' or j.get('diversity_scan')) and j['rc']==0];errors=sum(bool(r.get('error')) for r in records);timeouts=sum(r.get('code')==-2 or r.get('fq2code')==-2 for r in records)
archive=json.load((W/'copy-verified25.json').open()) if (W/'copy-verified25.json').exists() else None
stopped=(W/'processes-stopped-local25.json').exists() and (W/'boxE-final/processes-stopped25.json').exists() and (not (W/'boxCD-owned33').exists() or (W/'boxD-final/processes-stopped25.json').exists() and (W/'boxCD-scratch-removed33.json').exists())
notes=[f'{len(records)} numerical attempts on {len(counts)} counts, {errors} rebuild errors and {timeouts} timeouts.',f'{len(scans)} completed donor scans covered {sum(j.get("pairs",0) for j in scans)} pairs.',f'Retained counts: {[int(r["n"]) for r in rows]}. Lowest live counts: {low}.','The 444 control reproduced side 21.564693167754 before worker launch. The own503 control passed with zero share calls.','Published files require border finesafe at 2.2e-11, the full default/polish fq loop from certified bytes, and final source and peer checks.','Fresh changed endpoints and valid non-winning donors precede exact unrun recipes. Held kicks, the dry 1.010 and 1.003 finishes, and unchanged slide masks stayed closed.','Public-first certificates retain both share tolerances and all harvested reference versions. Own and held layouts bypass share checks. Withdrawals remain tied to pinned bytes.']
for name in ['history-rebuilt33.json','held33-control.json','certloop33-control.json','public33-control.json','source-scope33-control.json','withdrawal-controls33.json','held-record-control33.json','independent33.json','wide33-control.json','boxD-control33.json','partition-audit33.json','boxCD-copy-verified33.json','strict-validation32.json','history28.json','final-peer33.json']:
 if (W/name).exists():notes.append(name+': '+json.dumps(json.load((W/name).open()),sort_keys=True))
if (W/'held-chain-controls33.json').exists():
 held_tests=json.load((W/'held-chain-controls33.json').open());notes.append('Held-path source controls: '+json.dumps([{'case':v['case'],'clean':v['clean'],'files':v.get('files'),'hits':len(v['hits'])} for v in held_tests])+'. Full receipts in work/held-chain-controls33.json.')
if (W/'admission-held-path33.json').exists():
 admitted=json.load((W/'admission-held-path33.json').open());notes.append('Full admission of forensics911 held-path control: '+str(admitted['accepted'])+f", {admitted['seconds']:.3f}s; work/admission-held-path33.json.")
if (W/'measurements28.json').exists():notes.extend(json.load((W/'measurements28.json').open()))
if archive:notes.append(f'Archive verified {archive["files"]} files and {archive["bytes"]} bytes, with {len(archive["checksum_differences"])} checksum differences.')
notes.append('Finish branches: '+json.dumps({m:{'attempts':sum(r.get('mechanism','standard')==m for r in records),'raw_crossings':sum(bool(r.get('raw')) for r in records if r.get('mechanism','standard')==m)} for m in sorted({r.get('mechanism','standard') for r in records})}))
if (W/'phase-feed33.json').exists():
 phase=json.load((W/'phase-feed33.json').open());phase_summary=[{'tag':j['tag'],**j.get('result',{})} for j in phase['jobs']]
 notes.append('Integer parent phase pilot: '+json.dumps(phase_summary))
if (W/'phase-control33.json').exists():notes.append('Integer-phase controls: '+json.dumps(json.load((W/'phase-control33.json').open())))
if (W/'phase-witness-optimized33.json').exists():
 witness=json.load((W/'phase-witness-optimized33.json').open());notes.append('Fixed phase witness: '+json.dumps({k:v for k,v in witness.items() if k not in {'S','R'}}))
for name in ['phase-prefix-sweep33.json','phase-prefix-exact33.json','phase-mask-fixed33.json','phase-mask-fq33.json','phase-mask-bar33.json','phase-mask-strip33.json']:
 if (W/name).exists():
  m=json.load((W/name).open())
  if 'results' in m:m={k:v for k,v in m.items() if k in {'best_count','seconds','results'}}
  elif 'S' in m:m={k:v for k,v in m.items() if k not in {'S','R'}}
  notes.append(name+': '+json.dumps(m))
for name in ['phase-matching33.json','phase-matching-signed33.json','phase-matching-uprights33.json','phase-matching-seed261-33.json','phase-matching-seed261-tail33.json']:
 if (W/name).exists():
  j=json.load((W/name).open());notes.append(name+': '+json.dumps({k:v for k,v in j.items() if k!='improvements'}))
if (W/'phase-lattice33.json').exists():
 j=json.load((W/'phase-lattice33.json').open());notes.append('Held368 lattice mask controls: '+json.dumps([{k:r.get(k) for k in ['phi','target_n','status','count','solve_seconds']} for r in j['results']])+'. Full receipt work/phase-lattice33.json.')
if (W/'guard-adoption33.json').exists():notes.append('boxD workers adopted without numeric restarts; intake23:45Z, drain under hard00:15Z. Receipt work/guard-adoption33.json.')
if (W/'interrupted-recovery33.json').exists():notes.append('boxE workers exited early without a stop receipt. A four-slot supervisor restored them after a zero-orphan check. One unreported wide866 recipe was reopened; no completed geometry or raw find was repeated. Receipt work/interrupted-recovery33.json.')
if (W/'boxCD-preseed33.json').exists():
 j=json.load((W/'boxCD-preseed33.json').open());notes.append(f'Pre-copy boxD seed: {j["matched_files"]}/{j["inventory_files"]} files and {j["matched_bytes"]}/{j["inventory_bytes"]} bytes matched SHA256. Final stopped-worker manifest remains authoritative.')
notes.append('The expanded free-mask MILP failed its368 positive control and added no take. The exact bipartite reformulation passed512 exhaustive small graphs and the known368 layout.')
if (W/'crossover33-result.json').exists():notes.append('Whole-layout self crossover: '+json.dumps(json.load((W/'crossover33-result.json').open())))
notes.append('Retained score gains: '+json.dumps([(int(r['n']),base[int(r['n'])]-float(r['new'])) for r in rows]))
state=json.load((W/'collect-state.json').open()) if (W/'collect-state.json').exists() else {}
source_steps=[{'n':v['n'],'score':v['score'],'gain_base':base[v['n']]-v['score'],'recipe':k,'status':v['status']} for k,v in state.items() if v.get('score') is not None and v.get('status')=='published']
notes.append('Published source history, including later peer supersession: '+json.dumps(source_steps))

nexts=[f'Join changed source-cleared endpoints first. This round completed {len(scans)} donor scans and retained {len(rows)} counts. Keep exact snapshots and source proofs.','Return valid non-winning bands as donors before old recipes. Round31 non-winning927 supplied retained928, and the fresh round32 donor292 supplied488 for4.0923e-5.','Keep completed geometry signatures closed and use exact unrun recipes after fresh joins. Round33 began with15660 closed signatures and no missing manifests.','Use a new constructive phase or mask before more joint solver time. Fixed225-cell occupancy models reached368, but fq returned the held368 score. Six fixed-phase bar scouts and two boundary-phase bar scouts were infeasible in their bounded models after the368 positive control passed. The signed/count-specific matching sweep covered10504 graphs without a crossing. Diverse upright completions added8241 dry graphs. The held261 rectangular seed also stayed dry. Use a different physical phase family before more of these mask searches.']
nexts.append('Use different donor layouts before another whole-layout crossover. All1440 self-D4/translation configurations retained the source count despite passing the identity and512small-graph controls.')
if source_steps:
 best_by_n={}
 for step in source_steps:
  if step['n'] not in best_by_n or step['score']<best_by_n[step['n']]['score']:best_by_n[step['n']]=step
 best_steps=sorted(best_by_n.values(),key=lambda v:v['gain_base'],reverse=True)
 nexts[0]='Join changed source-cleared endpoints first. Measured source steps: '+', '.join(f'n={v["n"]} gain {v["gain_base"]:.12g}' for v in best_steps[:5])+'. Preserve byte snapshots and return these source shapes to the donor pool.'
report=dict(lane='k123',improved_n=len(low),gain=dict(against_base_bar=gain,beyond_other_live_r33=beyond),take_dir=str(T),summary=f'Retained {len(rows)} certified source layouts, with {len(low)} below every live peer. '+('Workers stopped and both box archives verified.' if stopped and archive else 'Work remains active; see STATE.txt.'),what_was_measured=notes,next=nexts,commits=json.load((W/'commits26.json').open()) if (W/'commits26.json').exists() else [],processes_left=0 if stopped else 'see STATE.txt',blocked='none',repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
(W/'metrics28.json').write_text(json.dumps(report,indent=2)+'\n')
if '--artifacts' in sys.argv:
 with (R/'results/k123-r33-2026-11-17.tsv').open('w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for r in rows:
   n=int(r['n']);sc=float(r['new']);wr.writerow(['certified',n,counts[n],(sc+1)*n**.5,base[n]-sc,max(0,other[n]-sc) if n in low else 0,r['source'],r['licence'],'lowest live' if n in low else 'superseded'])
  for n in sorted(counts):
   ss=[r['side'] for r in records if r['n']==n and 'side' in r];wr.writerow(['attempts',n,counts[n],min(ss) if ss else '',0,0,'pinned manifests in take-k123-r33/work','per-input source records','raw measured side'])
 text=f'''## Round 33

The lane retains {len(rows)} certified layouts, with gain {gain:.15g} against bar33.
At {time.strftime('%H:%M UTC',time.gmtime())}, {len(low)} counts beat every live peer. Their added gain is {beyond:.15g}.

boxE slots and any extra boxD slots completed {len(records)} numerical attempts on {len(counts)} counts.
There were {errors} rebuild errors and {timeouts} timeouts.
The {len(scans)} completed donor scans covered {sum(j.get('pairs',0) for j in scans)} pairs.
The starting geometry index closed 15,660 prior signatures with no missing manifests.
Fresh changed endpoints and valid returned bands ran before exact unrun recipes.
The measured 1.005 finish remained open. Dry finish branches and unchanged slide masks remained closed.

The 444 control printed side 21.564693167754. The own503 control passed with zero share calls.
Published files require border finesafe at 2.2e-11 clearance and the full fq loop from their certified bytes.
Each certificate receives a final source walk and a comparison against live takes.
Own and held layouts bypass share checks. Public-first outputs use both tolerances and all harvested reference versions.
Withdrawals apply to the pinned bytes they name.

The integer-phase prototype passed its367 gauge control and the expected absent-phase refusal.
Six30-second scouts found no primal incumbent.
One fixed assignment kept171 tilted squares and an exact maximum of184 uprights on the four wall lattices.
Its355-square model is12 below the367 target. Continuous refit kept355 at side19.70026605070549.
The prefix-phase sweep tested1536 assignments, with470 valid, and reached363 squares in21.798 seconds.
Its fixed0/0 phase had an exact maximum of192 uprights, for363 total.
Free occupancy on225 tilted sites reached368 with fixed parent phases.
The best368 layout quenched to the held score and failed the required gain threshold.
Six below-bar fixed-phase models were infeasible in their bounded domains.
A boundary-phase model passed its368 control, then refused both below-bar targets.
The held368 reference passed its control and refused four smaller-angle369 targets in the tested domain.
The expanded free-mask MILP failed its368 positive control and added no take.
Exact bipartite matching passed512 exhaustive small-graph cases and the known368 layout.
The first404 graph tests and the signed/count-specific10504 tests found no crossing.
The latter sweep took22.215 seconds. A further8241 upright-completion tests found no crossing.
The rectangular held261 seed passed its control and completed its bounded graph search.
The whole-layout self crossover tested1440 D4 and translation configurations across five fresh layouts.
All identity controls passed. No count increased. These models added no take.

The source walker scopes the shared assembler registry to its contextual count.
The fresh533 control passed with55 source files, where the old walk reached3000 unrelated records.
The public-first911 negative control still fails at0.4072448 within1e-2.
Walks that reach their cap fail with an explicit unresolved-edge reason.
The shared held-path fix passed the full admission check for fresh forensics911.
A gone file outside held ancestry and the exact withdrawn stair812 bytes still fail.
Claim and retention notes do not withdraw rows without an uppercase withdrawal verb.

Four extra boxD slots can run fresh geometry. A load guard pauses them above 9.
Both boxes use disjoint hashes for fresh recipes, and completed prior claims remain closed.
Incremental bundles send new pools after confirmed admission on the extra box.
Both archives are copied in advance and checked by SHA256 after their workers stop.
Each box scratch is removed only after that check passes.
A preliminary boxD copy matched more than99% of its bytes against a box-local SHA256 inventory.
boxE pool now has a four-slot supervisor after an unexplained early worker exit.
One interrupted recipe was reopened, with completed geometry kept closed.
The boxD guard adopted all four workers and lets active jobs drain after intake closes.

Join intake closes at 23:45 UTC. Finalization starts at 23:55 UTC, before the 00:15 UTC hard cutoff.
Source withdrawals and peer comparisons remain active until the 00:25 UTC take freeze.

Sources and measurements are in [the round table](../results/k123-r33-2026-11-17.tsv).
The [round helpers](../tools/k123/r33/) preserve the queue and source checks.
Inputs and receipts remain in `$SCRATCH/bounties-squares/take-k123-r33/work/`.
'''
 (W/'round33-section.md').write_text(text)
elif '--checkpoint' not in sys.argv:
 (T/'report.json.tmp').write_text(json.dumps(report,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}),flush=True)
