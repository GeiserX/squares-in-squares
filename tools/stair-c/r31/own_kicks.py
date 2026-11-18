"""Give fresh own close geometry its first claimed probe, then preserve useful legs."""
import datetime,hashlib,json,math,os,re,subprocess,sys,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
W=Path(C.WORK);S=Path(C.ROOT);STATE=W/'own-kicks-state.json';END=min(float((W/'box/kick-deadline').read_text())-300,datetime.datetime(2026,11,15,23,30,tzinfo=datetime.timezone.utc).timestamp())

def recent_claim(digests):
 now=time.time()
 for line in (S/'handoff-r31.log').read_text().splitlines():
  if not re.search('claim',line,re.I)or not any(x and x[:12]in line for x in digests):continue
  try:t=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
  except(ValueError,IndexError):continue
  if now-t<3600:return True
 return False

def main():
 seen=json.loads(STATE.read_text())if STATE.exists()else{}
 while time.time()<END:
  try:
   pending={};last={};bars=C.bar()
   for key,v in seen.items():
    part=v['n']%3
    if v.get('status')=='queued':last[part]=max(last.get(part,0),v.get('time',0))
    if v.get('status')=='queued'and not(W/'boxcopy'/['n','m','s'][part]/'final'/(v['name']+'.json')).exists():pending[part]=True
   candidates=[]
   for p in (W/'cert-in').glob('*.json'):
    j=json.loads(p.read_text());n=j['n'];part=n%3
    if not j.get('whole_layout_follow')or j.get('whole_kick')or j.get('control_only')or j.get('held31_origin')or j.get('after_kick')or j.get('kick_leg',0)>0:continue
    path=p.with_suffix('.csv');sha=hashlib.sha256(path.read_bytes()).hexdigest();key=str(n)+sha
    prior=seen.get(key,{})
    if prior.get('status')=='queued'or prior.get('retry_at',0)>time.time()or pending.get(part)or time.time()-last.get(part,0)<600:continue
    side=j['built'];margin=side-(1+bars[n])*math.sqrt(n)
    if margin>.0002:continue
    original=Path(j.get('source_snapshot',''));rawsha=j.get('source_sha256','')
    own=bool(j.get('own_near_follow'))or str(original).startswith(C.TAKE+'/')
    if not own and (not original.is_file()or time.time()-original.stat().st_mtime<600):continue
    if recent_claim([sha,rawsha]):continue
    candidates.append((margin,p,j,sha,key))
   for margin,p,j,sha,key in sorted(candidates,key=lambda q:q[0]):
    n=j['n'];part=n%3
    if pending.get(part):continue
    try:
     meta=C.manifest(j)
     if C.full_admission(str(p.with_suffix('.csv')),n,meta)is None:raise ValueError('full source admission deferred')
    except(ValueError,OSError,KeyError)as ex:
     seen[key]=dict(n=n,status='deferred',retry_at=time.time()+600,reason=str(ex),path=str(p))
     C.state('DEFER own kick source '+str(p)+' '+str(ex)+'. Continue to other admitted candidates.')
     continue
    # Exact source pins are checked before a whole kick is offered to the worker.
    if recent_claim([sha,j.get('source_sha256','')]):continue
    name=f'{n}-own-first-kick-{sha[:12]}';dest=W/'cert-in'/(name+'.csv');dest.write_bytes(p.with_suffix('.csv').read_bytes())
    meta.update(whole_layout_follow=True,whole_kick=True,own_kick_dispatch=True,kick_seed=33100+n,kick_leg=j.get('kick_leg',0),built=j['built'])
    meta.pop('source_kick',None);meta.pop('certified_file_quench',None)
    dest.with_suffix('.json').write_text(json.dumps(meta));host=C.HOSTS[part][0]
    with(S/'handoff-r31.log').open('a')as f:f.write(C.stamp()+f' stair-c -> all: CLAIM own close n={n} sha256 {sha}, source sha256 {j.get("source_sha256","")}, {dest}; cap900s probe120s on {host}\n')
    r=subprocess.run(['rsync','-a',str(dest),str(dest.with_suffix('.json')),host+':scratch/squares-stair-c/cert-in/'],capture_output=True,timeout=40);r.check_returncode()
    seen[key]=dict(n=n,status='queued',name=name,sha256=sha,time=time.time(),margin=margin);pending[part]=True
    C.state('START own close kick n='+str(n)+' '+host+' input'+sha+' margin'+repr(margin)+'; inherited source fully admitted. Worker log; deadline00:15Z.');print('QUEUED',n,margin,flush=True)
   temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(seen,indent=2));temp.replace(STATE)
  except Exception:traceback.print_exc()
  time.sleep(30)
if __name__=='__main__':main()
