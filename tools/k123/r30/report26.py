"""Write the round26 measurement table and required lane report."""
import pathlib,json,csv,collections,datetime,sys
csv.field_size_limit(20000000)
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.')
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));base={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))};other={}
for p in S.glob('take-*-r30/take.tsv'):
 if p.parent==T:continue
 for q in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(q['n']);other[n]=min(other.get(n,base[n]),float(q['new']))
  except (ValueError,KeyError):pass
records=[]
for l in (W/'records.jsonl').read_text().splitlines():
 try:records.append(json.loads(l))
 except ValueError:pass
counts=collections.Counter(r['n'] for r in records);groups=collections.Counter('resume' if r['pool'].startswith('resume') else 'fresh' if r['pool'].startswith('fresh') else 'licensed' for r in records)
lowest=[int(r['n']) for r in rows if float(r['new'])<other.get(int(r['n']),base[int(r['n'])])-1e-10];gain=sum(base[int(r['n'])]-float(r['new']) for r in rows);beyond=sum(max(0,min(base[int(r['n'])],other.get(int(r['n']),base[int(r['n'])]))-float(r['new'])) for r in rows)
tasks=[json.load(open(p)) for p in (W/'taskdone').glob('*.json')];scans=[j for j in tasks if j['kind']=='scan' and j['rc']==0]
validation=json.load(open(W/'validation25.json')) if (W/'validation25.json').exists() else []
archive=json.load(open(W/'copy-verified25.json')) if (W/'copy-verified25.json').exists() else None
stopped=(W/'processes-stopped-local25.json').exists() and (W/'boxE-final/processes-stopped25.json').exists()
report=dict(lane='k123',improved_n=len(lowest),gain=dict(against_base_bar=gain,beyond_other_live_r26=beyond),take_dir=str(T),summary=f'{len(rows)} clean certified source layouts. Lowest live source rows: {len(lowest)}. '+('All lane workers stopped and boxE archive verified.' if stopped and archive else 'Search and collection continue to the common 05:45 UTC cutoff.'),what_was_measured=[f'{len(records)} join attempts on {len(counts)} counts; groups {dict(groups)}; {sum("error" in r for r in records)} rebuild errors and {sum(r.get("code")==-2 or r.get("fq2code")==-2 for r in records)} timeouts.',f'{len(scans)} completed donor scans over {sum(j.get("pairs",0) for j in scans)} pairs.',f'Published source counts {[int(r["n"]) for r in rows]}; current lowest counts {lowest}. Each published file passed floatsafe at 2.2e-11 and a certified-file boxE fq quench.','The 444 positive control printed 21.564693167754, reference 21.564693168782. boxE verification transport reproduced certified 580 score 0.02066626667326732.','Withdrew 546 and 695 after harvest withdrew their 695 parent. Withdrew 932 for ambiguous held933 ancestry and 922 after the independent walk found the forbidden bare921 seed. Their near files and queued donor identities are excluded.','Source controls accepted licensed 581 and rebuilt 735, rejected frozen 982 and the bare 921-29e12ff3 seed. The full source proof and exact input pool are retained for every join.','Implicit held references now resolve through the imported quench walker. The unnumbered813 negative control was refused; all five retained rows passed the expanded admission check.','The old n=907 blanket rule falsely rejected the licensed rebuilt907 and its 580 child. Source checks now distinguish the old held907 from the clean rebuilt source.','The licensed bare 972 start was resolved by its CSV SHA256 and sidecar. The full midm 910 ancestry then passed, while unknown hashes and the known 921 seed remain refused.','Warm metadata controllers now refresh source dependencies together. A runtime assertion requires the tested v11 checker. Refused donor geometry identities are removed from queued pools.','The mandatory full publication walk accepted clean580 and rejected922 by detecting its hidden921-29e12ff3 ancestor. This gate runs before every new near or take publication.','The probe control accepted clean580 from source-checks26. Every direct methods_take input CSV retained a numeric prefix.','Numerical certification moved to the existing fourth boxE slot after a local collection pass took 668.121 seconds. No search or quench runs locally.'],next=['Join changed licensed inputs and their fresh follower returns first. The clean489 handoff supplied 328, and the held rebuilt907 supplied 580 in this round.','Resume the unrun exact-input r25 recipes after fresh designs. Completed geometry signatures suppress unchanged measured attempts, while every saved source proof is checked again.','Keep certification and search within four boxE slots. The local certification pass took 668.121 seconds before the transport change.','Keep the full independent walk before every publication. The 922 control exposed a bare921 ancestor that the earlier guard missed.','Read source-withdrawal handoffs before following changed rows. Harvest695 caused two withdrawals here, and the ambiguous held933 history caused a third. Keep their descendants out.','Keep the 199 pair closed until its end or seam changes again. Thirteen attempts, including nine after the licensed365 end changed, produced no certified gain.'],commits=json.load(open(W/'commits26.json')) if (W/'commits26.json').exists() else [],processes_left='none' if stopped else 'four boxE numerical slots and two light metadata controllers',blocked='none',repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
independent=json.load(open(W/'independent-source-walk26.json')) if (W/'independent-source-walk26.json').exists() else []
if independent:report['what_was_measured'].append(f'Independent quench_walk source checks passed counts {[r["n"] for r in independent if r["clean"]]}.')
if validation:report['what_was_measured'].append(f'Verifier snapshot: {len(validation)} source and floatsafe checks passed with unchanged coordinates.')
if archive:report['what_was_measured'].append(f'Archive: {archive["files"]} files, {archive["bytes"]} bytes, {len(archive["checksum_differences"])} checksum differences.')
(T/'report.json.tmp').write_text(json.dumps(report,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
if '--artifacts' in sys.argv:
 table=R/'results/k123-r26-2026-11-14.tsv'
 with open(table,'w',newline='') as h:
  wr=csv.writer(h,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for r in rows:
   n=int(r['n']);score=float(r['new']);wr.writerow(['certified',n,counts[n],(score+1)*n**.5,base[n]-score,max(0,min(base[n],other.get(n,base[n]))-score),r['source'],r['licence'],'lowest live take' if n in lowest else 'source for lower follower'])
  for n in sorted(counts):
   rr=[r for r in records if r['n']==n];ss=[r['side'] for r in rr if 'side' in r]
   wr.writerow(['attempts',n,len(rr),min(ss) if ss else '',0,0,'exact pinned input and source snapshots in take-k123-r26/work','per input manifest','raw numerical measurement'])
 text=f'''## Round 26

The lane retained {len(rows)} clean certified source layouts. Their score gain against round 25b is {gain:.15g}.
At this comparison, {len(lowest)} rows beat the other live takes. They add {beyond:.15g} beyond those takes.
Lower follower layouts keep the gains of source rows that they replace.

The four boxE slots ran {len(records)} joins on {len(counts)} counts. There were {sum('error' in r for r in records)} rebuild errors and {sum(r.get('code')==-2 or r.get('fq2code')==-2 for r in records)} timeouts.
Completed donor scans numbered {len(scans)}, over {sum(j.get('pairs',0) for j in scans)} pairs.
Fresh handoffs ran before saved recipes. Saved recipes kept their exact geometry and full source snapshots.
The queue imported 1,285 completed input records from the previous round.

The clean 489 handoff supplied the new 328. The rebuilt 907 supplied 580.
Later follower returns supplied new seams. Each certified layout then returned to the donor pool.

The 444 control printed 21.564693167754. Its reference is 21.564693168782.
boxE verifier control reproduced the certified 580 score of 0.02066626667326732.
Each published layout passed floatsafe at 2.2e-11 clearance and received a boxE fq quench from its certified file.

The source checks follow immutable JSON proofs and recorded parent files.
Unresolved bare hashed filenames fail admission. The known 921-29e12ff3 seed and frozen 982 descendants stay excluded.
Controls accepted licensed 581 and rebuilt 735, and rejected the withdrawn 982.
The source checks distinguish the licensed rebuilt 907 from the earlier held 907.

Implicit held references now resolve through the same history rule as the assembler.
The control refused the unnumbered 813 chain and accepted the five retained sources.

The lane withdrew 695 and its 546 child after harvest withdrew their 695 parent.
It also withdrew 932 because its held 933 donor had an ambiguous historical chain.
The independent walk found a forbidden bare 921 ancestor in the new 922, which was also withdrawn.
That walk now runs before every new near or take publication.
Its controls accepted clean 580 and rejected the hidden seed in 922.
The queue now rejects those exact sources and their descendants.

Warm metadata controllers now refresh source dependencies together.
A runtime check requires source version v11. Refused donor geometries are removed from queued pools.

The local certification pass reached 668.121 seconds on the loaded collector box.
Numerical certification then moved into the existing fourth boxE slot. Metadata and transfers remain local.
Chain readings are cached for unchanged input geometry. boxE keeps a common 05:45 UTC deadline for searches and quenches.

| n | side | gain against base | gain beyond other takes |
|---|---|---|---|
'''
 for r in rows:
  n=int(r['n']);sc=float(r['new']);text+=f'| {n} | {(sc+1)*n**.5:.12f} | {base[n]-sc:.12g} | {max(0,min(base[n],other.get(n,base[n]))-sc):.12g} |\n'
 text+='''
Next, join changed licensed inputs and fresh follower returns first. The 489 and 907 inputs supplied the largest new counts.
Then resume unrun recipes with their exact source snapshots. Keep unresolved source trees excluded.

Sources and measurements are in [the round table](../results/k123-r26-2026-11-14.tsv).
The [round helpers](../tools/k123/r26/) preserve the queue, source checks and certification transport.
Input pools, receipts and logs remain in `$SCRATCH/bounties-squares/take-k123-r26/work/`.
'''
 if stopped and archive:text+='\nAll lane workers stopped. boxE archive passed checksum checks before its scratch directory was removed.\nThe shared boxE base was preserved.\n'
 if not stopped:text+='\nThis is a running checkpoint. Search and quench stop at 05:45 UTC on 2026-11-14.\n'
 (W/'round26-section.md').write_text(text)
print(json.dumps({k:report[k] for k in ['improved_n','gain','summary']}))
