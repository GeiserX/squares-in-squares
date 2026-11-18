"""Audit the final take and write this round's measurements and lane note."""
import argparse,csv,hashlib,json,math,pathlib,shutil,subprocess,sys,datetime
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r23';W=T/'work';R=W/'boxE23';REPO=pathlib.Path('$PRIVATE_REPO');LANE=REPO/'lanes/squares'
sys.path.insert(0,str(LANE));import floatsafe
ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args()
held={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round21-1113a/details.csv'))};bar=dict(held);who={}
for p in list(B.glob('take-*-r22/take.tsv'))+list(B.glob('take-*-r23/take.tsv')):
 if p.parent==T:continue
 for row in csv.DictReader(open(p),delimiter='\t'):
  n=int(row['n']);score=float(row['new'])
  if score<bar[n]:bar[n]=score;who[n]=str(p)
keep=[];removed=[]
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);p=T/(str(n)+'.csv');rows=[{k:r[k] for k in ['n','square_id','x','y','angle']} for r in csv.DictReader(open(p))]
 _,fr,score,error=floatsafe.work((n,rows));assert fr is not None,(n,error);assert abs(score-float(row['new']))<5e-13,(n,score,row['new'])
 if score>=held[n]-1e-10 or score>=bar[n]-1e-10:
  removed.append(dict(n=n,score=score,bar=bar[n],winner=who.get(n)))
  if a.write:
   shutil.copy2(p,T/'near'/(str(n)+'-superseded-final.csv'));(T/'near'/(str(n)+'-superseded-final.json')).write_text(json.dumps(dict(row,reason='superseded by '+who.get(n,'held file')),indent=2));p.unlink()
 else:keep.append(row)
if a.write:
 shutil.copy2(T/'take.tsv',W/'published-before-final.tsv')
 with open(T/'take.tsv.tmp','w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(keep)
 (T/'take.tsv.tmp').replace(T/'take.tsv')
done=[json.load(open(p)) for p in R.glob('done/*.json')];kicks=[j for j in done if 'start_side' in j and not j.get('tag','').startswith('control')];designs=[json.load(open(p)) for p in R.glob('designs/*/summary.json')];builds=[json.load(open(p)) for p in R.glob('designs/*/builds/*.json')]
manifest=json.load(open(R/'final-manifest.json')) if (R/'final-manifest.json').exists() else None
completed_keys={(j.get('tag'),j.get('seed')) for j in done if j.get('seed') is not None}
pending=[];ignored=[]
for p in R.glob('jobs/*json'):
 if (R/'locks'/p.name).exists():continue
 j=json.load(open(p));reason=None
 if manifest is not None and str(p.relative_to(R)) not in manifest['files']:reason='deleted remote alias retained by rsync cache'
 elif j.get('kind')=='design' and (R/'designs'/j['tag']/'summary.json').exists():reason='completed design under another queue alias'
 elif j.get('seed') is not None and (j.get('tag'),j.get('seed')) in completed_keys:reason='completed scan under another queue alias'
 if reason:ignored.append(dict(file=p.name,reason=reason));continue
 pending.append(j)
(W/'queue-alias-audit.json').write_text(json.dumps(ignored,indent=2))
joint=[json.load(open(p)) for p in R.glob('designs/*/joint-summary.json')]
stats=dict(at=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ'),improved_n=len(keep),gain=dict(round21=sum(held[int(r['n'])]-float(r['new']) for r in keep),frozen_r22_and_other_r23=sum(bar[int(r['n'])]-float(r['new']) for r in keep)),rows=keep,removed=removed,kick_scans=len(kicks),tries=sum(j['tries'] for j in kicks),design_screens=len(designs),builds=len(builds),completed_quenches=len(list(R.glob('q/*/meta.json'))),archived_libraries=len(list(R.glob('designs/*/lib/copy-check.json'))),pending_jobs=len(pending),pending_designs=sum(j.get('kind')=='design' for j in pending),joint_attempted=sum(j['attempted'] for j in joint),joint_settled=sum(j['settled'] for j in joint),timeouts=sum(len(p.read_text().splitlines()) for p in R.glob('designs/*/timeouts.log')))
(W/'final-stats.json').write_text(json.dumps(stats,indent=2));(W/'pending-final.json').write_text(json.dumps(pending,indent=2))
if a.write:
 subprocess.run([str(B/'venv/bin/python'),str(W/'results23.py'),str(LANE/'results/twoshort-r23-2026-11-13.tsv')],check=True)
 lines=['## 13. Round 23 (2026-11-13)','',f"Final snapshot at {stats['at']}: {len(keep)} n remain below every frozen round 22 take and every other live round 23 take.",f"The gain is {stats['gain']['round21']:.12g} against round 21 and {stats['gain']['frozen_r22_and_other_r23']:.12g} beyond the other takes.",'','| n | certified side | gain against round 21 | gain beyond the other takes |','|---|---|---|---|']
 for r in keep:
  n=int(r['n']);s=float(r['new']);lines.append(f"| {n} | {(s+1)*math.sqrt(n):.12f} | {held[n]-s:.9e} | {bar[n]-s:.9e} |")
 if not keep:lines.append('| none | | | |')
 lines+=['','Each retained file passed floatsafe at 2.2e-11 after a boxE fq quench from a certified input.','The source records are in `take-twoshort-r23/take.tsv` in the scratch directory.','','### 13.1 Raw kicks and handoffs','',f"The lane completed {stats['kick_scans']} kick scans with {stats['tries']} tries, {stats['design_screens']} design screens and {stats['builds']} full builds.",'The [result table](../results/twoshort-r23-2026-11-13.tsv) records the measurements.','Runs used three boxE processes with one common deadline at 18:30 UTC.','','The first raw kick on a fresh forensics 969 removes 0.000578033 of side in 15 tries.','Its first quench certifies a gain of 1.856934485e-5 against round 21 and the other takes at that time.','Both rectangle donors match their original packings exactly.','Their source records name our own designs.','A late fresh forensics 799 removes 0.001586312 of side in 13 tries.','Its completed quench ties the harvest result from our raw file, so it does not count here.','Five exact geometry matches resolve its source through a border, a rectangle composition and a k123 join.','The public source records name the areebbb and kmmmvs public notebooks under Apache 2.0.','','A carried round 22 raw 793 certifies before invent supersedes it.','Two raw branches remove another 4.58e-8 and 4.44e-8 of side.','The later 427 branch is dry in 23 tries.','Four byte-equality checks trace the input through a reader step and a family return to our own 793.','','The closest direct module builds receive raw kicks before fq.','The 911 kick removes 1.253e-6 of side.','Invent then certifies a lower descendant of that raw file.','The classfill 852 probe removes 0.001859 of side but remains 0.000983 above the bar.','The classfill 912 and 854 probes are dry.','','### 13.2 Joint column heights and row offsets','',f"The joint tests try {stats['joint_attempted']} altered starts at f = 0.6730, 0.6948 and 0.7067. {stats['joint_settled']} settle.",'Each changes upright column heights and offsets of whole tilted rows together.','The control reconstructs the known corner and recovers loss 2.9914105035.','An overlapping copy has gap -1.0 and fails.','','The lowest losses are 4.55790, 3.77493 and 3.93629.','The f = 0.6948 state builds 852 at 0.002844 of side above the bar.','None of these transfers gives a qualifying row.','','### 13.3 Queue and source checks','','The design queue now keeps each full module and stack specification.','The old key kept only n and corner.','On j0016, the corrected key keeps ten specifications instead of three.','The extra 915 far-zone builds remain 0.002553 above the bar.','','Fresh imported designs use prediction slack 0.012.','The earlier 0.006 screen would reject the measured winning prediction of 0.007921 from the corners lane.','Individual builds stop after 120 seconds.','Later build batches stop after six minutes and save `unstarted.json`.','Two cancelled calls were 1:44 and 0:39 old.','Their pipelines had run for more than eight minutes, which caused the initial timing mistake.','','A foreign pickle containing tuples stopped the collector.','The repaired importer keeps readable dictionary entries and skips unsupported entries.','Its control keeps one valid entry and rejects two unsupported entries.','Source lookup reads `.json` and `.csv.json` sidecars and rectangle part records.','','Raw module builds initially waited behind polished copies.','The audit promoted the closest original builds for 911, 973 and 976.','Future queues need that priority from the first handoff.','Numerical copies share a geometry check, while direct raw legs keep their own runs.','The geometry control accepts distance 2.17e-9 and rejects a square moved by 1e-4.','The final audit re-certifies 31 completed quenches and finds no unpublished qualifying row.','The certificate control rejects the frozen 793 tie and accepts it when that reference is omitted.','','### 13.4 Next','','1. Kick fresh whole layouts before polished copies. The 799 and 969 scans remove 0.001586312 and 0.000578033 of side.','2. Put original module builds first when they arrive. The promoted 911 raw file feeds a lower invent result.','3. Resume the saved new design specifications by predicted fit and completed build history.','   Keep the two-minute call limit and the six-minute batch limit.','4. Preserve immutable source records for every raw branch. The 793 chain needed four byte-equality checks.','5. Stop unchanged joint transfers. They settle altered corners but produce no qualifying row.','',f"The final archive holds {stats['archived_libraries']} verified library copies. {stats['pending_jobs']} unstarted jobs remain in `work/pending-final.json`.",'All 2217 remote files and one symlink match the final manifest.','The remote and local manifest hashes match.','Cleanup removes the lane scratch after those checks and preserves `squares-base`.','']
 section='\n'.join(lines);(W/'round23-section.md').write_text(section)
 doc=LANE/'avenues/twoshort.md';text=doc.read_text();start=text.find('## 13. Round 23');end=text.find('## Files')
 if start>=0:text=text[:start]+section+'\n'+text[end:]
 else:text=text[:end]+section+'\n'+text[end:]
 doc.write_text(text)
 for name in ['setup23.py','worker23.py','manage23.py','certify23.py','design23.py','joint23.py','results23.py','finish23.py','audit23.py']:shutil.copy2(W/name,LANE/'tools/twoshort'/name)
print(json.dumps({k:v for k,v in stats.items() if k not in ['rows']},indent=2))
