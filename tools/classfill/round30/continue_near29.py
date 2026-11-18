"""Continue changed certified near endpoints from short first scans, once each."""
from common29 import *
from light29 import load,key,side
from ancestor_share29 import inspect
if time.time()>=SEARCH_END:raise SystemExit()
closed=read(W/'continued-near.json',{});scanned=set(read(W/'scanned.json',[]));geometries=read(W/'geometry-scanned.json',{});base,live=writebar();candidates=[]
handoff=(S/'handoff-r30.log').read_text()
for repaired in read(W/'source-repairs.json',{}):
 if closed.get(repaired)=='incomplete source':closed.pop(repaired)
for host in ['boxE','boxD']:
 for p in (W/host/'out').glob('near-*/*.json'):
  if p.name=='quench-receipt.json':continue
  j=read(p,{});n=int(p.stem) if p.stem.isdigit() else 0;tag=p.parent.name.removeprefix('near-');job=read(W/'jobs'/f'{tag}.json',{})
  if n<100 or tag in closed or '; leg ' in job.get('source',''):continue
  score=j.get('finish_score');start=j.get('finish_start_side');f=p.with_suffix('.csv')
  if score is None or start is None or not f.is_file():continue
  move=start-(1+score)*math.sqrt(n);excess=(1+score)*math.sqrt(n)-(1+live[n])*math.sqrt(n)
  competitive=excess < -1e-10*math.sqrt(n)
  if not competitive and (move<1e-5 or excess>0.0005 or job.get('seconds',0)>300):continue
  sha=hashlib.sha256(f.read_bytes()).hexdigest();gkey=key(load(f,{n})[n]);proof=read(W/'source-repairs.json',{}).get(tag) or next((W/'ancestry').glob(tag[1:13]+'*.json'),None)
  if sha in scanned or gkey in geometries:closed[tag]='closed geometry';continue
  if any(sha[:12] in line for line in handoff.splitlines() if re.search(r'backlog ->[^:]*: claims ',line)):closed[tag]='claimed bytes';continue
  a=read(proof,{}) if proof else {};h=a.get('expanded',{}).get('history',{})
  if not h or h.get('issues') or h.get('excluded') or not a.get('source') or not a.get('licence'):closed[tag]='incomplete source';continue
  anc=inspect(proof)
  if anc['errors'] or anc['excluded'] or hold_hit(a):closed[tag]='source check';continue
  candidates.append((-move,n,f,sha,gkey,tag,proof,a,h,competitive))
atomic(W/'continued-near.json',closed)
if not candidates:raise SystemExit()
loads=[]
for host,slots in [('boxE',['A','B']),('boxD',['C'])]:
 for slot in slots:
  lines=cmd(['ssh',host,'find '+REMOTE+'/queue/'+slot+' -type f \\( -name "*.json" -o -name "*.active" \\)']).splitlines();loads.append((len(lines),host,slot))
count,host,slot=min(loads)
if count>=2:raise SystemExit()
move,n,original,sha,gkey,parent_tag,proof,a,h,competitive=sorted(candidates)[0];move=-move
p=W/'inputs'/f'{n}-x{sha[:12]}.csv';shutil.copy2(original,p);assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
tag='x'+sha[:12];rec=dict(accepted=True,n=n,tag=tag,input=str(original),input_sha256=sha,input_proof=str(proof),walked=h,leg=2,parent_tag=parent_tag,queue_snapshot=blob(original),source=f'classfill r30 changed certified near endpoint of {parent_tag}; first short scan moved {move:.12g} of side; before it: '+a['source'],licence='Own search; '+a['licence'],time_utc=now())
atomic(W/'audited'/f'{tag}.json',rec)
job=dict(tag=tag,kind='scan',input='data/'+p.name,source=str(original)+f'; leg 2 changed near endpoint from {parent_tag}; immutable ancestry '+str(proof),licence=rec['licence'],priority=-6,seed=int(sha[:6],16)+29000,seconds=(0 if competitive else 900),wall=(600 if competitive else 1200),kicks='0.02,0.04')
publish_job(job,p,host,slot);closed[parent_tag]=dict(child=tag,source_move=move);atomic(W/'continued-near.json',closed);scanned.add(sha);atomic(W/'scanned.json',sorted(scanned));geometries[gkey]=str(p);atomic(W/'geometry-scanned.json',geometries)
note(f'START changed near leg n{n} from {parent_tag}; side move{move:.12g}, competitive{competitive}, new scan seconds{job["seconds"]}. Complete source proof {proof}, queue bytes {sha}.')
