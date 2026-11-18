"""Changed-method family lkick on certified prepared endpoints, spare boxE slots."""
from common29 import *
from public_review30 import review,OWN
from light29 import load,side
import fcntl
lock=open(W/'invent-campaign.lock','a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit('campaign already active')
if (W/'STOP_INVENT_CAMPAIGN').exists():raise SystemExit('campaign admission closed')
assert read(W/'invent-control30.json',{}).get('passed')
end=SEARCH_END
note(f'START invent_campaign30.py pid{os.getpid()}, log work/invent_campaign30.log, control passed,180s local family lkick without fq inside; boxE slots only, admission ends17:35Z')
while time.time()<end and not (W/'STOP').exists():
 try:
  done=read(W/'invent-followed30.json',{});candidates=[];_,live,_=bar()
  for p in (T/'near').glob('*-classfill-x*.csv'):
   meta=read(str(p)+'.json',{})
   if not meta.get('prepared_geometry_changed'):continue
   n=int(p.name.split('-')[0]);sha=hashlib.sha256(p.read_bytes()).hexdigest()
   if sha in done or float(meta['score'])>live[n]+2e-6:continue
   proof=next((q for q in (W/'ancestry').glob(sha+'*.json') if read(q,{}).get('input_sha256')==sha),None)
   if not proof:continue
   a=read(proof,{});h=a.get('expanded',{}).get('history',{})
   if h.get('issues') or h.get('excluded') or not h:continue
   if any(ref not in OWN for ref,n_ in h.get('public',[])):continue
   if hold_hit(a) or not review(proof).get('complete'):continue
   candidates.append((0 if n==653 else 1,float(meta['score'])-live[n],n,p,sha,proof,a))
  # Also compare the certified first-quench checkpoints that scalar tie-breaking
  # kept out of near/. They are owned transformations with exact receipts.
  existing={q[4] for q in candidates}
  for host in ['boxE','boxD']:
   for folder in (W/host/'out').glob('finish-x*'):
    original_tag=folder.name.removeprefix('finish-');recipe=read(W/'jobs'/f'{original_tag}.json',{});status=read(W/host/'out'/f'{original_tag}-status.json',{})
    if not recipe.get('prequench') or status.get('returncode')!=0:continue
    match=re.match(r'data/(\d+)',recipe.get('input',''));n=int(match[1]) if match else 0
    if n<300:continue
    p=folder/f'{n}-pre.csv';receipt=folder/'pre-quench/quench-receipt.json'
    if not p.is_file() or not receipt.is_file():continue
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    if sha in done or sha in existing or read(receipt,{}).get('output_sha256')!=sha:continue
    P=load(p,{n}).get(n,[])
    if len(P)!=n:continue
    score=side(P)/math.sqrt(n)-1
    if score>live[n]+2e-6:continue
    original=next((q for q in (W/'ancestry').glob(original_tag[1:13]+'*.json')),None)
    a=read(original,{}) if original else {};h=a.get('expanded',{}).get('history',{})
    if not h or h.get('issues') or h.get('excluded') or any(ref not in OWN for ref,n_ in h.get('public',[])):continue
    proof=next((q for q in (W/'ancestry').glob(sha+'*.json') if read(q,{}).get('input_sha256')==sha),None)
    if proof is None:
     source='certified fq preparation of '+str(a['input'])+'; before it: '+a['source']
     atomic(Path(str(p)+'.json'),dict(n=n,source=source,licence=a['licence'],input_sha256=sha,ancestry=str(original),preparation_receipt=str(receipt)))
     resolved=dict(a,input=str(p),input_sha256=sha,source=source,metadata=dict(n=n,source=source,licence=a['licence'],parent_proof=str(original),preparation_receipt=str(receipt)),snapshots=a.get('snapshots',[])+[blob(p),blob(str(p)+'.json'),blob(receipt),blob(original)])
     proof=W/'ancestry'/(sha+'-precheckpoint.json');atomic(proof,resolved);a=resolved
    else:a=read(proof,{})
    if hold_hit(a) or not review(proof).get('complete'):continue
    candidates.append((0 if n==653 else 2,score-live[n],n,p,sha,proof,a));existing.add(sha)
  if candidates:
   loads=[]
   for slot in ['A','B']:
    lines=cmd(['ssh','boxE','find '+REMOTE+'/queue/'+slot+' -type f \\( -name "*.json" -o -name "*.active" \\)']).splitlines();loads.append((len(lines),slot))
   count,slot=min(loads)
   if count<2:
    _,_,n,p,sha,proof,a=sorted(candidates,key=lambda q:q[:2])[0];tag='x'+sha[:12]+'i30';copy=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(p,copy)
    assert hashlib.sha256(copy.read_bytes()).hexdigest()==sha
    job=dict(tag=tag,n=n,kind='scan',input='data/'+copy.name,source=str(p)+'; changed method invent_rest local family squeeze, no fq inside; immutable ancestry '+str(proof),licence='Own changed-method search; '+a['licence'],priority=-4.5,seed=11,seconds=180,wall=900,kicks='0.02,0.04',search_method='invent',prepared_follow=True)
    try:
     publish_job(job,copy,'boxE',slot);done[sha]=dict(tag=tag,n=n,time=now(),method='family lkick180s without fq inside');note(f'START_CHANGED_METHOD n{n} {tag} family lkick180s, earlier midm method closed separately; source only owned roots')
    except RuntimeError as e:
     done[sha]=dict(n=n,reason=str(e));note('INVENT_RESERVATION_SKIP '+str(n)+' '+str(e))
    atomic(W/'invent-followed30.json',done)
 except Exception as e:note('INVENT_CAMPAIGN_RETRY '+repr(e));print(repr(e),flush=True)
 time.sleep(20)
note('FINISH invent campaign admission')
