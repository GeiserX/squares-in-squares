"""Probe changed returned-module compositions with both validated input boxes."""
import csv,datetime,hashlib,json,math,subprocess,sys,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
from own_kicks import recent_claim
from paired_fresh import copy
W=Path(C.WORK);END=datetime.datetime(2026,11,15,22,55,tzinfo=datetime.timezone.utc).timestamp()
STATE=W/'paired-returns-state.json'
def save(state):
 temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2));temp.replace(STATE)
def dispatch(record):
 for name in record['jobs']:
  p=Path(name);copy((p,p.with_suffix('.json')),record['host'])
 record['dispatch_complete']=True
def completed_dry(record):
 if not record.get('dispatch_complete'):return False
 folder=W/'boxcopy'/['n','m','s'][record['part']]/'final'
 for name in record['jobs']:
  p=folder/Path(name).with_suffix('.json').name
  if not p.exists():return False
  j=json.loads(p.read_text());kick=j.get('source_kick',{})
  if not j.get('certified_file_quench',{}).get('completed')or kick.get('start',0)-kick.get('end',0)>1e-6:return False
 return True
def main():
 state=json.loads(STATE.read_text())if STATE.exists()else{}
 while time.time()<END:
  try:
   for record in state.values():
    if record.get('status')=='queued'and not record.get('dispatch_complete'):dispatch(record);save(state)
   queued=[v for v in state.values()if v.get('status')=='queued']
   occupied={v['part']for v in queued}
   m=[v for v in queued if v['part']==1]
   # The first transfer to748 measured zero. Reserve a second pair for the
   # home count805 that supplied this round's matched gain.
   if len(m)==1 and m[0]['n']==748 and completed_dry(m[0]):occupied.discard(1)
   bars=C.bar();choices=[]
   for row in csv.DictReader(open(Path(C.TAKE)/'take.tsv'),delimiter='\t'):
    n=int(row['n']);bars[n]=min(bars[n],float(row['new']))
   for p in W.glob('boxcopy/*/raw-a/*.json'):
    j=json.loads(p.read_text());n=j['n'];part=n%3
    if part in occupied or j.get('early_stage')or j.get('built')is None:continue
    if any(v['part']==part for v in queued)and n!=805:continue
    if not any('r31returnstacks'in q['id']or'r31feedback'in q['id']for q in j['modules']):continue
    data=p.with_suffix('.csv').read_bytes();sha=hashlib.sha256(data).hexdigest()
    previous=state.get(sha,{})
    if previous.get('status')=='queued'or previous.get('retry_at',0)>time.time():continue
    margin=j['built']-(1+bars[n])*math.sqrt(n)
    if margin>.0002 or recent_claim([sha]):continue
    choices.append((margin,p,j,sha))
   for margin,p,j,rawsha in sorted(choices,key=lambda x:x[0]):
    n=j['n'];part=n%3
    if part in occupied:continue
    host=C.HOSTS[part][0]
    control=json.loads((W/'paired-fresh'/f'{host}-bar-control.json').read_text());assert control['passed']and control['actual_side']>control['requested_side']+.0001
    try:
     meta=C.manifest(j);proof=C.full_admission(str(p.with_suffix('.csv')),n,meta)
     if proof is None:raise ValueError('full source admission deferred')
     _,fr,score,reason=C.cert_cache.certify(str(p.with_suffix('.csv')),n)
     if fr is None:raise ValueError(reason)
    except(ValueError,OSError,KeyError)as ex:
     state[rawsha]=dict(n=n,part=part,status='deferred',reason=str(ex),retry_at=time.time()+600);continue
    cert=W/'cert-in'/f'{n}-paired-return-input-{rawsha[:12]}.csv';C.write(str(cert),fr);sha=hashlib.sha256(cert.read_bytes()).hexdigest()
    if recent_claim([rawsha,sha]):continue
    seed=35300+n;target=(1+bars[n])*math.sqrt(n);jobs=[]
    for order,mode in enumerate(['input','bar']if n%2 else['bar','input']):
     dest=W/'cert-in'/f'{n}-paired-fresh-return-{order}-{mode}-{sha[:10]}.csv';dest.write_bytes(cert.read_bytes())
     assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
     detail=dict(meta,n=n,whole_layout_follow=True,whole_kick=True,paired_experiment=True,paired_return=True,pair_mode=mode,pair_seed=seed,pair_input_sha256=sha,kick_seed=seed,built=(1+score)*math.sqrt(n),source_snapshot=str(p.with_suffix('.csv')),source_sha256=rawsha)
     detail.pop('source_kick',None);detail.pop('certified_file_quench',None);detail.pop('bar_input_follow',None);detail.pop('kick_target_side',None)
     if mode=='bar':detail['kick_target_side']=target
     dest.with_suffix('.json').write_text(json.dumps(detail));jobs.append((dest,dest.with_suffix('.json')))
    C.hand(f'CLAIM matched changed-return pair n={n}, source sha256 {rawsha}, certified sha256 {sha}, seed{seed}, fixed target{target}, {p.with_suffix(".csv")}; two variants on {host}')
    record=dict(n=n,part=part,status='queued',host=host,source=str(p),input_sha256=sha,margin=margin,seed=seed,target=target,jobs=[str(q[0])for q in jobs],dispatch_complete=False)
    state[rawsha]=record;save(state)
    dispatch(record)
    cert.unlink()
    save(state);occupied.add(part)
    C.state(f'START matched changed-return pair n={n} {host} source{rawsha}, certified{sha}, margin{margin}. Reuses actual975 input-box control. Two900s caps and120s probes, existing serial worker; deadline00:15Z.')
    print('RETURN PAIR',n,host,margin,sha,flush=True)
   save(state)
   if len(occupied)==3:return
  except Exception:traceback.print_exc()
  time.sleep(45)
if __name__=='__main__':main()
