"""Write measured round27 artifacts; the final report is written after 05:55 UTC."""
import pathlib,json,csv,collections,time,sys
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.');csv.field_size_limit(1<<28)
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));base={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round35-briefs/bar35.tsv'),delimiter='\t')};other={}
for p in S.glob('take-*-r31/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);other[n]=min(other.get(n,base[n]),float(r['new']))
  except (ValueError,KeyError):pass
records=[]
if (W/'records.jsonl').exists():
 for line in (W/'records.jsonl').read_text().splitlines():
  try:records.append(json.loads(line))
  except ValueError:pass
counts=collections.Counter(r['n'] for r in records);groups=collections.Counter('resume' if r['pool'].startswith('resume') else 'fresh' if r['pool'].startswith('fresh') else 'reopened' for r in records)
low=[int(r['n']) for r in rows if float(r['new'])<other.get(int(r['n']),base[int(r['n'])])-1e-10]
gain=sum(base[int(r['n'])]-float(r['new']) for r in rows);beyond=sum(max(0,other.get(int(r['n']),base[int(r['n'])])-float(r['new'])) for r in rows)
tasks=[json.load(open(p)) for p in (W/'taskdone').glob('*.json')];scans=[j for j in tasks if j['kind']=='scan' and j['rc']==0]
archive=json.load(open(W/'copy-verified25.json')) if (W/'copy-verified25.json').exists() else None
stopped=(W/'processes-stopped-local25.json').exists() and (W/'boxE-final/processes-stopped25.json').exists()
notes=[f'{len(records)} join and recertification attempts on {len(counts)} counts, groups {dict(groups)}; {sum("error" in r for r in records)} rebuild errors and {sum(r.get("code")==-2 or r.get("fq2code")==-2 for r in records)} timeouts.',f'{len(scans)} completed donor scans over {sum(j.get("pairs",0) for j in scans)} pairs.',f'Certified source counts {[int(r["n"]) for r in rows]}; lowest live counts {low}. Each file received floatsafe at 2.2e-11 and a boxE fq quench from its certified file.','The 444 numerical control printed side21.564693167754 against21.564693168782. boxE verifier control reproduced580 score0.02066626667326732.','Initial tests reopened r25 982 at start share0.0, before the added ancestor-share gate. Samanyu-name restrictions stay lifted; actual excluded ancestor layouts stay out.','The r26 922 walk still found missing invent860 and921 parent files after the seed restriction was lifted. It remained excluded for those missing records.','Fixed a missing board.tsv in the new boxE scratch. The first two scan selectors were rerun and38 queue starts recovered.','Every input pool has a SHA256. Direct input CSVs and producer records were pinned as byte snapshots at staging. Search, quench and numerical certification ran only in four boxE slots.']
if archive:notes.append(f'Archive verified: {archive["files"]} files, {archive["bytes"]} bytes, {len(archive["checksum_differences"])} checksum differences.')
notes.extend(['Fresh quench647 joined with held699 and certified699 with gain6.269774701106456e-05. A later lane lowered699 further. Fresh quench753 joined with held868 and certified753 with gain2.5533592418192086e-07.', 'The old signature file held1280 older geometries. Added2041 exact measured r26 signatures, total3321, and restarted three join workers at natural job boundaries.', 'Snapshotted22 explicitly reopened held and round23a roots, including415,501,503,921. Their parent packing SHA256 and source records are retained.', 'Local paging pushed a full metadata partner walk past20 minutes. Partner selection now happens before source expansion, with12 first partners and the remaining pairs preserved.', 'Exact prvsiyan760 share control printed1.0; accepted932 printed0.003218884120171674. The intake reference now reads only submission.csv, matching the canonical publication gate.'])
notes.append('Withdrew699 and932 after the exact original-seed ancestor audit found merged0 seed503 at prvsiyan share1.0. This is a geometry exclusion independent of the lifted Samanyu-name restriction. Original-seed983 control share0.5503560528992879 is excluded;811 and861 controls share0.0 remain allowed.')
notes.append('Installed source gatev5 in numerical workers. Pools without the completed original-seed ancestor gate cannot dispatch. Added current-round completed geometry signatures, bringing the history to4021 before restart.')
notes.append('Withdrew798 after complete CSV ancestor742, byte SHA256 b890df05302fbe1450ec08fc9731872f171d4ceb837a2bff08799f1fea1eeec0, measured prvsiyan share0.45417789757412397. Version6 also checks complete per-n CSV ancestors before dispatch and publication.')
notes.append('Retained source gains by count: '+str([(int(r['n']),base[int(r['n'])]-float(r['new'])) for r in rows]))
nexts=['Join source-cleared fresh quench ends first. The retained753/868 and698/752 joins gained2.5533592418192086e-07 and1.0002231021211117e-07 against the bar. Their walked original-seed811 control has share0.0.', 'Check exact original-seed and public ancestors before dispatch, even after the Samanyu-name rule was lifted. Seed503 has share1.0 and cost699/932; seed983 has share0.550356. These stay out under the share rule until rebuilt from allowed ancestors.', 'Check complete per-n CSV ancestors as well as original seeds. The798/855 result had no original-seed reference, but its742 ancestor had share0.454178 and caused withdrawal. Rebuild the parent from allowed layouts before any replay.', 'Resume exact unrun recipes and deferred partners after fresh designs, keeping4021 completed geometry signatures closed. Source replacement requires exact arrays and a complete new proof; none is granted by a matching count alone.', 'Bound local metadata batches and source-cache memory. A full partner walk stalled for over20 minutes under paging; choosing12 first partners before admission restored short batches. Keep numerical certification within the four boxE slots.']

report=dict(lane='k123',improved_n=len(low),gain=dict(against_base_bar=gain,beyond_other_live_r27=beyond),take_dir=str(T),summary=f'Certified source layouts: {len(rows)}. Lowest live rows: {len(low)}. '+('All lane workers stopped and boxE archive verified.' if stopped and archive else 'Work continues to the round27 deadline.'),what_was_measured=notes,next=nexts,commits=json.load(open(W/'commits26.json')) if (W/'commits26.json').exists() else [],processes_left='none' if stopped else 'see STATE.txt',blocked='none',repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
(W/'metrics27.json').write_text(json.dumps(report,indent=2)+'\n')
if '--artifacts' in sys.argv:
 table=R/'results/k123-r27-2026-11-14.tsv'
 with open(table,'w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for r in rows:
   n=int(r['n']);sc=float(r['new']);wr.writerow(['certified',n,counts[n],(sc+1)*n**.5,base[n]-sc,max(0,other.get(n,base[n])-sc),r['source'],r['licence'],'lowest live' if n in low else 'lower follower source'])
  for n in sorted(counts):
   rr=[r for r in records if r['n']==n];ss=[r['side'] for r in rr if 'side' in r];wr.writerow(['attempts',n,len(rr),min(ss) if ss else '',0,0,'pinned input pools in take-k123-r27/work','per-input manifests','raw measured side'])
 text=f'''## Round 27

The lane retained {len(rows)} certified source layouts. Their gain against the round 27 bar is {gain:.15g}.
At this comparison, {len(low)} rows beat the other live takes. They add {beyond:.15g} beyond those takes.

The four boxE slots ran {len(records)} join and recertification attempts on {len(counts)} counts.
There were {sum('error' in r for r in records)} rebuild errors and {sum(r.get('code')==-2 or r.get('fq2code')==-2 for r in records)} timeouts.
Completed donor scans numbered {len(scans)}, over {sum(j.get('pairs',0) for j in scans)} pairs.

The source checks now accept the independently discovered layouts that match the Samanyu repository.
The initial 982 check measured a start share of 0.0.
Original-seed ancestors now receive their own share checks.
The checks reject CC BY-SA, excluded penguin layouts, missing parents and other withdrawn source trees.
Seed 503 has share 1.0 and seed 983 has share 0.550356. Both are excluded ancestors.
The lane withdrew 699 and 932 for seed 503 ancestry. Seeds 811 and 861 have share 0.0.
It also withdrew 798 for the complete 742 ancestor, whose share is 0.454178.
The checks cover complete per-n CSV ancestors as well as original seeds.
The prvsiyan test uses a shared fraction of at least 0.4 within 1e-3.
It checks all eight square symmetries. The former maximum-distance test is removed.

The 444 control printed side 21.564693167754. Its reference is 21.564693168782.
boxE verifier control reproduced the 580 score of 0.02066626667326732.
Every published layout passed floatsafe at 2.2e-11 clearance and a quench from its certified file.
Input CSVs and records have byte snapshots and SHA256 hashes.
The common search and quench deadline was 05:45 UTC.

The initial reopened 922 walk found missing invent parent files. That admission was refused.
A missing board file blocked early selectors. Their saved scan logs were replayed after the board file was restored.

Sources and measurements are in [the round table](../results/k123-r27-2026-11-14.tsv).
The [round helpers](../tools/k123/r27/) preserve the queue and policy changes.
The input pools and receipts remain in `$SCRATCH/bounties-squares/take-k123-r27/work/`.

Fresh quench753 and held868 supplied753. Fresh quench698 and held752 supplied752.
The 647/699 result was withdrawn after its seed 503 ancestor failed the share rule.
The 798/855 result was withdrawn after its complete 742 ancestor failed the same rule.
Next, join changed bands and fresh returned layouts first. Then run the saved recipes with their exact source snapshots.
Keep missing-parent records closed until their evidence is recovered.
'''
 (W/'round27-section.md').write_text(text)
else:
 assert time.time()>=1794700500,'report must be written after05:55 UTC'
 (T/'report.json.tmp').write_text(json.dumps(report,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}),flush=True)
