from common29 import *
from collections import defaultdict
records=[];groups=defaultdict(lambda:dict(scans=0,completed=0,tries=0,moved_over_1e8=0,entered=0,best_side_move=0,searched_score_gain=0.0))
entered=set();previous={}
for m in re.finditer(r'CERTIFIED n(\d+) (x\w+) score([0-9.]+)',(T/'STATE.txt').read_text()):
 n=int(m[1]);score=float(m[3])
 if n not in previous or score<previous[n]-1e-10:entered.add(m[2])
 previous[n]=min(previous.get(n,score),score)
for host in ['boxE','boxD']:
 for p in list((W/host/'out').glob('finish-*/kick/scan-*.tsv'))+list((W/host/'out').glob('finish-*/kick/slide-*.tsv')):
  text=p.read_text();start=re.search(r'(?:held|start)=([0-9.]+)',text);found=[float(x) for x in re.findall(r'# FIND .*? side ([0-9.]+)',text)];tag=p.parents[1].name.removeprefix('finish-');j=read(W/'jobs'/f'{tag}.json',{});src=j.get('source','');n=int(p.name.split('-')[1]);side=float(start[1]) if start else None
  if 'control' in tag:continue  # Keep positive controls separate from production yield.
  kind='own certified leg' if re.search(r'; leg\s*\d',src) else ('fresh public' if 'take-harvest-r30/' in src and '/near/' not in src.split(';')[0] else ('fresh rectangle' if 'take-forensics-r30/' in src else ('fresh k123' if 'take-k123-r30/' in src else (re.search(r'take-([a-z0-9-]+)-r\d+',src)[0] if re.search(r'take-([a-z0-9-]+)-r\d+',src) else 'other'))))
  if j.get('prequench'):kind='pre-quench own seed'
  if '/take-classfill-r30/near/' in src:
   proof=next((W/'ancestry').glob(tag[1:13]+'*.json'),None)
   if '/work/preq-seeds/' in read(proof,{}).get('source',''):kind='prepared endpoint follow'
  if j.get('search_method')=='invent':kind='family local prepared endpoint'
  if 'reopened own endpoint' in src:kind='restored own endpoint'
  if 'changed-method larger kicks' in src:kind='larger kicks on own endpoint'
  if 'changed-method smaller kicks' in src:kind='smaller kicks on own endpoint'
  if kind=='fresh public':
   from share_policy29 import public_start
   proof=next((W/'ancestry').glob(tag[1:13]+'*.json'),None);a=read(proof,{}) if proof else {}
   if not public_start(a.get('input',''),a.get('source','')):kind='restored own harvest take'
  status=read(W/host/'out'/f'{tag}-status.json',{});rec=dict(n=n,tag=tag,host=host,kind=kind,tries=len([l for l in text.splitlines() if re.match(r'\d+\t',l)]),side_move=side-min(found) if found and side else 0,completed=bool(status) and status.get('returncode')==0,returncode=status.get('returncode'),entered=tag in entered)
  finish=read(W/host/'out'/f'near-{tag}'/f'{n}.json',{}) or read(W/host/'out'/f'final-{tag}'/f'{n}.json',{})
  if finish and rec['completed']:rec['side_move']=max(0.0,finish['finish_start_side']-(1+finish['finish_score'])*math.sqrt(n))
  if j.get('prequench'):
   finish=read(W/host/'out'/f'near-{tag}'/f'{n}.json',{}) or read(W/host/'out'/f'final-{tag}'/f'{n}.json',{})
   if finish.get('finish_prequench'):
    rec['side_move']=max(0.0,finish['finish_start_side']-(1+finish['finish_score'])*math.sqrt(n));rec['prequench_move']=(finish['finish_prequench']['before_score']-finish['finish_prequench']['after_score'])*math.sqrt(n)
  accepted=read(W/'accepted-candidates'/f'{n}-{tag}.json',{})
  rec['searched_score_gain']=max(0.0,min(accepted['base'],accepted['finish']['finish_start_side']/math.sqrt(n)-1)-accepted['score']) if rec['entered'] and accepted else 0.0
  if rec['searched_score_gain']<=1e-10:rec['searched_score_gain']=0.0
  records.append(rec);g=groups[kind];g['scans']+=1;g['completed']+=rec['completed'];g['tries']+=rec['tries'];g['moved_over_1e8']+=rec['side_move']>1e-8;g['entered']+=rec['entered'];g['best_side_move']=max(g['best_side_move'],rec['side_move']);g['searched_score_gain']+=rec['searched_score_gain']
summary=dict(time=now(),returncodes={str(c):sum(q['returncode']==c for q in records) for c in {q['returncode'] for q in records}},scans=len(records),completed_scans=sum(q['completed'] for q in records),tries=sum(q['tries'] for q in records),moved_over_1e8=sum(q['side_move']>1e-8 for q in records),take=len(rows(T/'take.tsv')),groups=dict(groups),best_moves=sorted(records,key=lambda q:-q['side_move'])[:6])
atomic(W/'measurements.json',dict(summary=summary,scans=records));print(json.dumps(summary,indent=1))
# Keep source-excluded and incomplete histories out of next-round yield ranking.
prohibited=set(read(W/'prohibited-tags.json',[]));eligible_groups={};source_cache=read(W/'stats-source-cache.json',{})
for rec in records:
 tag=rec['tag'];proof=next((W/'ancestry').glob(tag[1:13]+'*.json'),None)
 if proof is None:proof=read(W/'audited'/f'{tag}.json',{}).get('input_proof')
 stat=Path(proof).stat() if proof and Path(proof).exists() else None
 version=[str(proof),stat.st_mtime_ns,stat.st_size] if stat else None
 cached=source_cache.get(tag,{})
 if cached.get('version')==version and 'complete' in cached:complete=cached['complete']
 else:
  a=read(proof,{}) if proof else {};h=a.get('expanded',{}).get('history',{});complete=bool(h) and not h.get('issues') and not h.get('excluded')
  source_cache[tag]=dict(version=version,complete=complete);atomic(W/'stats-source-cache.json',source_cache)
 rec['source_excluded']=tag in prohibited;rec['source_complete']=complete
 if rec['source_excluded'] or not rec['source_complete']:continue
 g=eligible_groups.setdefault(rec['kind'],dict(completed=0,tries=0,moved_over_1e8=0,best_side_move=0.0,searched_score_gain=0.0))
 if rec['completed']:
  g['completed']+=1;g['tries']+=rec['tries'];g['moved_over_1e8']+=rec['side_move']>1e-8;g['best_side_move']=max(g['best_side_move'],rec['side_move']);g['searched_score_gain']+=rec['searched_score_gain']
summary['eligible_groups']=eligible_groups;summary['source_excluded_scans']=sum(q['source_excluded'] for q in records);summary['source_incomplete_scans']=sum(not q['source_complete'] for q in records)
atomic(W/'measurements.json',dict(summary=summary,scans=records))

from collections import Counter
summary['intake_dispositions']=dict(Counter(v.get('reason','unknown') for v in read(W/'intake-seen.json',{}).values()))
control_hashes={hashlib.sha256(p.read_bytes()).hexdigest() for p in W.glob('*-public-control.json')}
preflight=dict(proofs=0,complete=0,excluded=0,unresolved=0)
for review_path in (W/'public-root-reviews').glob('*.json'):
 if review_path.stem in control_hashes:continue
 q=read(review_path,{})
 if q.get('policy')!='pinned-root-v4':continue
 preflight['proofs']+=1;preflight['complete']+=bool(q.get('complete'));preflight['excluded']+=bool(q.get('excluded'));preflight['unresolved']+=not q.get('complete') and not q.get('excluded')
summary['public_preflight']=preflight
summary['bar_input_controls']=dict(bar=read(W/'bar-control-result.json',{}).get('passed'),stop6=read(W/'stop6-control-result.json',{}).get('passed'))
atomic(W/'measurements.json',dict(summary=summary,scans=records))
