"""Test changed close compositions with identical seeds and both input boxes."""
import csv,datetime,hashlib,json,math,subprocess,sys,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
from own_kicks import recent_claim
from paired_fresh import copy
from geometry_key import key as geometry_key,control as geometry_control
W=Path(C.WORK);END=datetime.datetime(2026,11,16,16,45,tzinfo=datetime.timezone.utc).timestamp()
STATE=W/'pair-driver-state.json'
def main():
 seen=json.loads(STATE.read_text())if STATE.exists()else{}
 (W/'cert-in').mkdir(exist_ok=True)
 geometry_control()
 old_geometry=set()
 prior=W.parents[1]/'take-stair-c-r31/work/cert-in'
 for p in prior.glob('805*.csv'):
  side=p.with_suffix('.json')
  if not side.exists()or not json.loads(side.read_text()).get('whole_kick'):continue
  points=C.M.np.asarray(C.M.read_layouts(str(p))[805],float);old_geometry.add(geometry_key(points))
 held=W/'held31/805.csv'
 if held.exists():old_geometry.add(geometry_key(C.M.np.asarray(C.M.read_layouts(str(held))[805],float)))
 C.state(f'PRELOAD {len(old_geometry)} completed n805 whole geometries; changed paired starts must differ at1e-8 after symmetry and translation.')
 control_dir=W/'paired-fresh';control_dir.mkdir(exist_ok=True)
 for host,key in C.HOSTS:
  p=W/'cert-in'/f'975-000-bar-control-{key}.csv'
  p.write_bytes((W/'box/cert-in/975-control-real.csv').read_bytes())
  p.with_suffix('.json').write_text(json.dumps(dict(n=975,control_only=True,whole_kick=True,kick_bar_control=True,modules=[],built=31.7141)))
  copy([p,p.with_suffix('.json')],host)
 while time.time()<END:
  try:
   ready=set()
   for part,(host,key)in enumerate(C.HOSTS):
    receipt=control_dir/f'{host}-bar-control.json'
    if not receipt.exists():
     subprocess.run(['rsync','-a',host+':scratch/squares-stair-c/bar-kick-control.json',str(receipt)],capture_output=True,timeout=35)
    if receipt.exists()and json.loads(receipt.read_text()).get('passed'):ready.add(part)
   occupied=set()
   for record in seen.values():
    if record.get('status')!='queued':continue
    folder=W/'boxcopy'/C.HOSTS[record['part']][1]/'final'
    if all((folder/(name+'.json')).exists()for name in record['jobs']):record['status']='returned'
    else:occupied.add(record['part'])
   bars=C.bar()
   for row in csv.DictReader(open(Path(C.TAKE)/'take.tsv'),delimiter='\t'):
    count=int(row['n']);bars[count]=min(bars[count],float(row['new']))
   options=[]
   for p in W.glob('boxcopy/*/raw-a/*.json'):
    j=json.loads(p.read_text());n=j['n'];part=n%3
    if n!=805 or part not in ready or part in occupied or j.get('early_stage')or j.get('built')is None:continue
    raw=p.with_suffix('.csv')
    if not raw.is_file():continue
    if not C.withdrawals.allowed_bytes(raw,C.ROOT):continue
    sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    if sha in seen or recent_claim([sha]):continue
    gkey=geometry_key(C.M.np.asarray(C.M.read_layouts(str(raw))[n],float))
    if gkey in old_geometry or any(v.get('geometry_key')==gkey for v in seen.values()):continue
    margin=j['built']-(1+bars[n])*math.sqrt(n)
    if margin>.0002:continue
    options.append((margin,p,j,sha))
   for margin,p,j,rawsha in sorted(options,key=lambda x:x[0]):
    n=j['n'];part=n%3
    if part in occupied:continue
    meta=C.manifest(j);proof=C.full_admission(str(p.with_suffix('.csv')),n,meta)
    if proof is None:seen[rawsha]=dict(status='source deferred',n=n);continue
    _,fr,score,why=C.cert_cache.certify(str(p.with_suffix('.csv')),n)
    if fr is None:seen[rawsha]=dict(status='numerically refused',n=n,reason=str(why));continue
    count=sum(v.get('n')==n and v.get('status')in {'queued','returned'}for v in seen.values())
    seed=46300+n+count*1000;side=(1+score)*math.sqrt(n);target=(1+bars[n])*math.sqrt(n)
    jobs=[];paths=[]
    for order,mode in enumerate(['input','bar']if count%2==0 else['bar','input']):
     name=f'{n}-paired-fresh-r32-{count}-{order}-{mode}-s{seed}'
     dest=W/'cert-in'/(name+'.csv');C.write(str(dest),fr)
     sha=hashlib.sha256(dest.read_bytes()).hexdigest()
     detail=dict(meta,n=n,whole_layout_follow=True,whole_kick=True,paired_experiment=True,pair_mode=mode,pair_seed=seed,pair_input_sha256=sha,kick_seed=seed,built=side,source_snapshot=str(p.with_suffix('.csv')),source_sha256=rawsha)
     for field in ['source_kick','certified_file_quench','bar_input_follow','kick_target_side']:detail.pop(field,None)
     if mode=='bar':detail['kick_target_side']=target
     dest.with_suffix('.json').write_text(json.dumps(detail));jobs.append(name);paths.append([dest,dest.with_suffix('.json')])
    if recent_claim([rawsha,sha]):continue
    C.hand(f'CLAIM matched fresh own pair n={n}, source sha256 {rawsha}, certified sha256 {sha}, seed{seed}, target{target}, {p.with_suffix(".csv")}; two variants on {C.HOSTS[part][0]}')
    for paths0 in paths:copy(paths0,C.HOSTS[part][0])
    seen[rawsha]=dict(n=n,part=part,geometry_key=geometry_key(C.M.np.asarray(C.M.read_layouts(str(p.with_suffix('.csv')))[n],float)),status='queued',jobs=jobs,seed=seed,margin=margin,input_sha256=sha)
    C.state(f'START fresh matched pair n={n} seed{seed} input{sha} margin{margin}; same bytes and cap900s probe120s, target{target}. Worker deadline17:15Z.')
    occupied.add(part)
   temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(seen,indent=2));temp.replace(STATE)
  except Exception:traceback.print_exc()
  time.sleep(45)
if __name__=='__main__':main()
