"""Claim untouched held starts, queue serial probes and chain useful own returns."""
import csv,datetime,hashlib,json,math,os,re,subprocess,sys,time,traceback
from pathlib import Path
csv.field_size_limit(64*1024*1024)
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H.parents[3])]
from held_proof import HELD,held_rows,held_sha,coords,check
S=HELD.parents[1];W=S/'take-stair-c-r32/work';TAKE=W.parent
END=datetime.datetime(2026,11,16,17,10,tzinfo=datetime.timezone.utc).timestamp()
INITIAL_END=datetime.datetime(2026,11,16,11,0,tzinfo=datetime.timezone.utc).timestamp()
STATE=W/'held-driver-state.json';LOG=S/'handoff-r32.log';HOSTS=['boxC','boxD','boxE']
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def state(s):
 with(TAKE/'STATE.txt').open('a')as f:f.write(stamp()+' boxA '+s+'\n')
def source(n):
 paths=sorted(Path('results').glob('round*-best-*.tsv'),key=lambda p:int(re.search(r'round(\d+)',p.name)[1]),reverse=True)
 for p in paths:
  for r in csv.DictReader(p.open(),delimiter='\t'):
   if int(r['n'])==n:return dict(n=n,table=str(p),source=r.get('source',''),licence=r.get('licence','own held layout'))
 return dict(n=n,table='results/round30-best-2026-11-15.tsv',source='own submitted held row',licence='own held layout')
def claims(digest):
 now=time.time()
 for line in LOG.read_text().splitlines():
  if digest not in line and digest[:12]not in line:continue
  if not re.search(r'claim',line,re.I):continue
  try:t=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
  except ValueError:continue
  if now-t<3600:return True
 return False
def queue(n,seen):
 out=W/'held31';out.mkdir(exist_ok=True)
 p=out/f'{n}.csv'
 with p.open('w')as f:
  w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(held_rows()[n])
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if claims(sha):return False
 rec=out/f'{n}-source.json';r=source(n);rec.write_text(json.dumps(r,sort_keys=True))
 origin=dict(n=n,held_path=str(HELD),held_sha256=held_sha(),snapshot=str(p),snapshot_sha256=sha,record=str(rec),record_sha256=hashlib.sha256(rec.read_bytes()).hexdigest())
 check(origin)
 # Claim exact original held bytes before certification or numerical dispatch.
 with LOG.open('a')as f:f.write(stamp()+f' stair-c -> all: CLAIM held first kick n={n} sha256 {sha}, {p}, host={HOSTS[n%3]}, probe120s cap900s\n')
 import fine
 _,rr,score,eps=fine.work((n,held_rows()[n]));assert rr is not None
 dest=W/'cert-in'/f'{n}-held31-seed{42000+n}.csv'
 with dest.open('w')as f:
  w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(rr)
 j=dict(n=n,built=(1+score)*math.sqrt(n),predicted=(1+score)*math.sqrt(n),stacks=[0,0],whole_layout_follow=True,whole_kick=True,kick_seed=42000+n,held31_origin=origin,source_sha256=sha,source_snapshot=str(p),modules=[dict(id=f'{n}-held31',source=f'own submitted held n={n} in {HELD}; source record {rec}; '+r['table'],licence=r['licence'])])
 dest.with_suffix('.json').write_text(json.dumps(j));host=HOSTS[n%3]
 result=subprocess.run(['rsync','-a',str(dest),str(dest.with_suffix('.json')),host+':scratch/squares-stair-c/cert-in/'],capture_output=True,timeout=40);result.check_returncode()
 seen[str(n)]=dict(n=n,host=host,sha256=sha,queued=time.time(),name=dest.stem)
 state('START held first-kick '+str(n)+' '+host+' '+str(dest)+' claim '+sha+'; probe120s cap900s, final certified-file fq; deadline17:15Z')
 return True
def chains(seen):
 import fine
 for part,key in enumerate(['n','m','s']):
  for p in (W/'boxcopy'/key/'final').glob('*.json'):
   j=json.loads(p.read_text())
   if (not j.get('held31_origin')and not j.get('own_kick_dispatch')and not j.get('paired_experiment'))or not j.get('certified_file_quench',{}).get('completed'):continue
   digest=hashlib.sha256(p.read_bytes()).hexdigest();marker='chain:'+digest
   if marker in seen:continue
   kick=j.get('source_kick',{});n=j['n'];csvpath=p.with_suffix('.csv')
   _,rr,score,_=fine.work((n,list(csv.DictReader(csvpath.open()))))
   if rr is None:continue
   side=(1+score)*math.sqrt(n);progress=kick.get('start',side)-side
   baseline={int(r['n']):float(r['bar'])for r in csv.DictReader((S/'round32-briefs/bar32.tsv').open(),delimiter='\t')}
   if score<baseline[n]-1e-10:
    seen[marker]=dict(n=n,status='certified row handed to backlog',progress=progress,queued=0);continue
   if claims(hashlib.sha256(csvpath.read_bytes()).hexdigest()):
    seen[marker]=dict(n=n,status='peer claimed current output',progress=progress,queued=0);continue
   leg=j.get('kick_leg',0);first=j.get('first_kick_shortening',progress)
   # Every useful find gets a leg. A first shortening>=1e-5 gets at least two more seeds.
   if progress<=1e-6 and not(first>=1e-5 and leg<2):
    seen[marker]=dict(n=n,status='chain closed',progress=progress,queued=0);continue
   seed=42000+n+(leg+1)*1000;label='held31'if j.get('held31_origin')else'own'
   dest=W/'cert-in'/f'{n}-{label}-leg{leg+1}-seed{seed}-{digest[:10]}.csv'
   with dest.open('w')as f:
    w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(rr)
   meta=dict(j,whole_kick=True,kick_leg=leg+1,kick_seed=seed,previous_kick=kick,first_kick_shortening=first,built=side,source_snapshot=str(csvpath))
   meta.pop('source_kick',None);meta.pop('certified_file_quench',None)
   dest.with_suffix('.json').write_text(json.dumps(meta))
   result=subprocess.run(['rsync','-a',str(dest),str(dest.with_suffix('.json')),HOSTS[part]+':scratch/squares-stair-c/cert-in/'],capture_output=True,timeout=40);result.check_returncode()
   seen[marker]=dict(n=n,host=HOSTS[part],name=dest.stem,queued=time.time(),progress=progress,leg=leg+1)
   state('CHAIN held own n='+str(n)+' leg'+str(leg+1)+' seed'+str(seed)+' shortening'+repr(progress)+' on '+HOSTS[part]+'; log worker.log; deadline17:15Z')

def order():
 # Prefer the unspent r30 list and the lane's slice, then spill into other untouched counts.
 d=json.loads((S/'take-border-r30/work/held30/order3.json').read_text())
 recent='\n'.join((S/f'handoff-r{k}.log').read_text()for k in [28,29,30])
 used=set()
 for line in recent.splitlines():
  if not re.search(r'kick',line,re.I):continue
  for x in re.findall(r'\bn\s*[=:]\s*(\d+)\b|/(\d{3})[^/ ]*\.csv',line):
   used.update(int(v)for v in x if v)
 ns=[int(n)for n in d if int(n)not in used]
 if not ns:ns=list(map(int,d))
 slice=lambda n:28<=math.isqrt(n-1)<=31 and 17<=n-math.isqrt(n-1)**2<=45
 return sorted(ns,key=lambda n:(not slice(n),-d[str(n)]))
def main():
 seen=json.loads(STATE.read_text())if STATE.exists()else{}
 ns=order();(W/'held-order.json').write_text(json.dumps(ns))
 while time.time()<END:
  try:
   if not(W/'coordinator.pid').exists():time.sleep(10);continue
   chains(seen)
   for part in range(3):
    if time.time()>=INITIAL_END:break
    own=[v for v in seen.values()if v['n']%3==part and v.get('queued',0)>0];last=max((v['queued']for v in own),default=0)
    # Initial held probes first; keep time for the composition lane afterwards.
    if time.time()-last<600:continue
    pending=[v for v in own if not(W/'boxcopy'/['n','m','s'][part]/'final'/(v.get('name','closed')+'.json')).exists()]
    if pending:continue
    for n in ns:
     if n%3!=part or str(n)in seen:continue
     if queue(n,seen):break
   tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(seen,indent=2));tmp.replace(STATE)
  except Exception:traceback.print_exc()
  time.sleep(30)
 state('STOP held feeder; queued'+str(len(seen))+' exact claimed starts')
if __name__=='__main__':main()
