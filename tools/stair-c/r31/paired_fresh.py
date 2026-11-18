"""Compare two input boxes on changed, source-complete own compositions."""
import csv,datetime,hashlib,json,math,subprocess,sys,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
from own_kicks import recent_claim
W=Path(C.WORK);END=float((W/'box/kick-deadline').read_text())-1800
STARTS=[('boxC','873-r31-d439efc5d3bb-n.csv'),('boxD','805-r31-8a8219bdf2ae-m.csv'),('boxE','812-r31-d28a0242b99c-s.csv')]
def copy(paths,host):
 r=subprocess.run(['rsync','-a',*[str(p)for p in paths],host+':scratch/squares-stair-c/cert-in/'],capture_output=True,timeout=40);r.check_returncode()
def main():
 out=W/'paired-fresh';out.mkdir(exist_ok=True);states=[]
 for host,name in STARTS:
  p=Path(C.TAKE)/'near'/name;n=int(name.split('-')[0]);raw=p.read_bytes();rawsha=hashlib.sha256(raw).hexdigest()
  if recent_claim([rawsha]):states.append(dict(n=n,status='peer claimed'));continue
  j=json.loads(Path(str(p)+'.json').read_text());meta=C.manifest(j);assert C.full_admission(str(p),n,meta)is not None
  _,fr,score,why=C.floatsafe.work((n,C.rows(str(p))));assert fr is not None,why
  cert=out/f'{n}-shared.csv';C.write(str(cert),fr);sha=hashlib.sha256(cert.read_bytes()).hexdigest()
  target=(1+C.bar()[n])*math.sqrt(n);seed=34300+n
  # The actual uncapped-box mutant goes through fq before any production pair.
  control=W/'cert-in'/f'975-000-bar-control-{n}.csv';control.write_bytes((W/'box/cert-in/975-control-real.csv').read_bytes())
  control.with_suffix('.json').write_text(json.dumps(dict(n=975,control_only=True,whole_kick=True,kick_bar_control=True,modules=[],built=31.7141)))
  copy([control,control.with_suffix('.json')],host)
  states.append(dict(n=n,status='control queued',host=host,source=str(p),source_sha256=rawsha,input=str(cert),input_sha256=sha,target=target,seed=seed,metadata=meta,certified_side=(1+score)*math.sqrt(n)))
  C.state(f'START changed pair control n={n} on {host}; source{rawsha}, certified{sha}; real975 bar-input test precedes production. Deadline00:15Z.')
 for s in states:
  if s['status']!='control queued':continue
  host=s['host'];n=s['n'];receipt=out/f'{host}-bar-control.json'
  while time.time()<END:
   r=subprocess.run(['rsync','-a',host+':scratch/squares-stair-c/bar-kick-control.json',str(receipt)],capture_output=True,timeout=40)
   if r.returncode==0:break
   time.sleep(15)
  assert receipt.exists()and json.loads(receipt.read_text())['passed']
  if recent_claim([s['source_sha256'],s['input_sha256']]):s['status']='claimed before dispatch';continue
  variants=['input','bar']if n%2 else['bar','input']
  jobs=[]
  for order,mode in enumerate(variants):
   name=f'{n}-paired-fresh-{order}-{mode}-s{s["seed"]}';dest=W/'cert-in'/(name+'.csv');dest.write_bytes(Path(s['input']).read_bytes())
   assert hashlib.sha256(dest.read_bytes()).hexdigest()==s['input_sha256']
   meta=dict(s['metadata'],n=n,whole_layout_follow=True,whole_kick=True,paired_experiment=True,pair_mode=mode,pair_seed=s['seed'],pair_input_sha256=s['input_sha256'],kick_seed=s['seed'],built=s['certified_side'],source_snapshot=s['source'],source_sha256=s['source_sha256'])
   meta.pop('source_kick',None);meta.pop('certified_file_quench',None)
   if mode=='bar':meta['kick_target_side']=s['target']
   else:meta.pop('kick_target_side',None)
   meta.pop('bar_input_follow',None)
   dest.with_suffix('.json').write_text(json.dumps(meta));jobs.append((dest,dest.with_suffix('.json')))
  with(Path(C.ROOT)/'handoff-r31.log').open('a')as f:f.write(C.stamp()+f' stair-c -> all: CLAIM matched own pair n={n}, source sha256 {s["source_sha256"]}, certified sha256 {s["input_sha256"]}, seed{s["seed"]}, fixed target{s["target"]}; two input-box variants on {host}, {s["source"]}\n')
  for paths in jobs:copy(paths,host)
  s['status']='pair queued';s['jobs']=[str(p[0])for p in jobs];s.pop('metadata',None)
  print('PAIRED_FRESH',n,host,s['input_sha256'],s['target'],flush=True)
 (W/'paired-fresh-queued.json').write_text(json.dumps(states,indent=2))
if __name__=='__main__':main()
