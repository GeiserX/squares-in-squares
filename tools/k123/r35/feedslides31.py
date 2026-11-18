"""Feed one controlled slide model at a time without adding a numerical slot."""
from pathlib import Path
import sys,subprocess,time,json,csv,hashlib,math
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;sys.path[:0]=[str(W),str(W/'lane')]
import fcntl
feedlock=(W/'slide-feed31.lock').open('a')
try:fcntl.flock(feedlock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit
SSH=['ssh','-S','/tmp/squares-k123-r35-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-ssh']
if time.time()>float((W/'search-deadline').read_text())-700:raise SystemExit
for control_tag in ['verify-slide-control31-v8','verify-slide-rigid31-v1','verify-slide-learned-control31-v1']:
 task=W/'taskdone'/(control_tag+'.json')
 if not task.exists() or json.load(task.open()).get('rc')!=0:raise SystemExit
control=W/'slide-control31.json'
if not control.exists():subprocess.run(SCP+['boxE:scratch/squares-k123/slide-control31.json',str(control)],check=True)
if not json.load(control.open()).get('positive_control_passed'):raise SystemExit
sf=W/'slide-feed31.json';state=json.load(sf.open()) if sf.exists() else {'jobs':[]}
for oldjob in state['jobs']+state.get('independent',[]):
 if oldjob.get('collected') or not (W/'taskdone'/(oldjob['tag']+'.json')).exists():continue
 dest=W/'slide-results31';dest.mkdir(exist_ok=True);out=dest/(oldjob['tag']+'.json')
 cp=subprocess.run(SCP+['boxE:scratch/squares-k123/out/slidemilp31/'+oldjob['tag']+'/result.json',str(out)],capture_output=True,text=True,timeout=30)
 oldjob['collected']=True;oldjob['result']=json.load(out.open()) if cp.returncode==0 else {'task_rc':json.load((W/'taskdone'/(oldjob['tag']+'.json')).open()).get('rc'),'result_unavailable':True}
 if oldjob['result'].get('output_count'):
  from publication_source26 import check as source_check
  raw=W/'slide-results31'/(oldjob['tag']+'.csv')
  got=subprocess.run(SCP+['boxE:scratch/squares-k123/out/slidemilp31/'+oldjob['tag']+'/model-output.csv',str(raw)],capture_output=True,text=True,timeout=30)
  if got.returncode==0:
   data=raw.read_bytes();digest=hashlib.sha256(data).hexdigest();nn=int(oldjob['result']['output_count']);dest=T/'near'/f'{nn}-slide31-{digest[:16]}.csv'
   row={'n':str(nn),'source':'own slide_milp31.py constructive row/column model; parameters '+json.dumps(oldjob,sort_keys=True)+'; calibration on held packings of n = 261 and n = '+str(oldjob['n'])+' of round 15; immutable calibration pool '+str(W/oldjob['pool']/(oldjob['pool']+'.csv'))+'; source records '+str(W/oldjob['pool']/('sources-'+oldjob['pool']+'.json'))+'; output sha256 '+digest,'licence':'own mathematical construction; terms of the named held calibrations are in the source manifest'}
   Path(str(raw)+'.json').write_text(json.dumps(row));proof=source_check(raw,row)
   if proof['clean'] and not dest.exists():
    Path(str(dest)+'.json').write_text(json.dumps(row));dest.write_bytes(data)
    line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: constructive slide donor n={nn}, side={oldjob["result"]["output_side"]:.14g}, continuous-fit model geometry, parameters {out}, {dest}\n'
    with (S/'handoff-r35.log').open('a') as f:f.write(line)
    with (T/'STATE.txt').open('a') as f:f.write(line.rstrip()+'; common deadline16:25Z.\n')
 sf.write_text(json.dumps(state,indent=2))
active=[j for j in state['jobs']+state.get('independent',[]) if not (W/'taskdone'/(j['tag']+'.json')).exists()]
if active:raise SystemExit
if (W/'slide-intake-closed31').exists():raise SystemExit
# Keep fresh scans ahead of the next pilot after each short model.
if state.get('last',0)>time.time()-60:raise SystemExit
from provenance24 import mlp,credit
from geometry23 import key
p=W/'control261.csv';sidecar=Path(str(p)+'.json')
if not sidecar.exists():sidecar.write_text(json.dumps({'n':'261','source':'own mathematical block model, calibrated on the held packing of n = 261 of round 15; gather/round15-2026-11-12a.csv n = 261; no public file input','licence':'own mathematical layouts; historical source in results/round15-best-2026-11-12.tsv'}))
A=mlp.load(str(p),{261})[261];c=credit(261,A,str(p));assert c,'slide control source admission failed'
pool='slidepool31';D=W/pool;D.mkdir(exist_ok=True)
if not (D/(pool+'.csv')).exists():
 raw=p.read_bytes();producer=sidecar.read_bytes();digest=hashlib.sha256(raw).hexdigest();record_sha=hashlib.sha256(producer).hexdigest();snap=W/'input-snapshots';snap.mkdir(exist_ok=True);q=snap/('261-'+digest+'.csv');q.write_bytes(raw);r=snap/(record_sha+'.json');r.write_bytes(producer)
 c={**c,'input_file_snapshot':str(q),'input_file_sha256':digest,'input_file_mtime':p.stat().st_mtime,'input_record_snapshots':{str(sidecar):{'snapshot':str(r),'sha256':record_sha}}}
 (D/(pool+'.csv')).write_bytes(raw);(D/('sources-'+pool+'.json')).write_text(json.dumps({'261':c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text());(D/(pool+'.json')).write_text(json.dumps({'kind':'slide-model-pool','source':'own constructive slide model; held261 is the mathematical calibration reference','tag':pool}))
 for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']:subprocess.run(SCP+[str(D/name),'boxE:scratch/squares-k123/'+name],check=True)
bars={int(f[0]):float(f[1]) for line in (W/'bars.tsv').read_text().splitlines() if len(f:=line.split('\t'))>=2}
# The old outline tool fixes uprights with greedy refill. This model rechooses them globally.
def outline(A,B,kind,p,c):
 base=[]
 for jj in range(B):
  lo=1 if kind!='rect' and jj<p else 0
  hi=A+lo+(1 if kind!='rect' and jj==p else 0)
  base.extend((ii,jj) for ii in range(lo,hi))
 if kind=='double':
  out=set()
  for ii,jj in base:
   out.add((ii,jj-1) if ii<=c else (ii,jj))
   if ii==c+1:out.add((ii,jj-1))
  base=sorted(out)
 lo0=min(i for i,j in base);lo1=min(j for i,j in base)
 return [[i-lo0,j-lo1] for i,j in base]
plan=[(n,A,phi,opening,True,0,3) for opening in [.02,.0,-.00001] for n,A,phis in [(367,13,[.8,1.6,2.4,3.11801833]),(626,17,[.4,.8,1.6,2.385])] for phi in phis]
plan[8:8]=[(626,17,.4,.01,False,0,3),(626,17,.8,.01,False,0,3)]
plan[10:10]=[(626,17,.4,.01,False,2,3),(626,17,.8,.01,False,2,3),(626,17,.4,.0,False,2,3),(626,17,.8,.0,False,2,3),(367,13,.8,.0,True,2,3),(367,13,1.6,.0,True,2,3),(367,13,.8,-.00001,True,4,3),(626,17,1.6,.01,False,2,3)]
plan[18:18]=[(626,17,.4,-.00001,False,4,7),(626,17,.8,-.00001,False,4,7),(367,13,.8,-.00001,True,4,7),(367,13,1.6,-.00001,True,4,7)]
plan[22:22]=[(626,17,.4,.005,False,74,3),(626,17,.8,.005,False,74,3),(367,13,.8,-.00001,True,58,3),(626,17,2.385,-.00001,False,76,7)]
index=len(state['jobs'])
if index>=len(plan):raise SystemExit
n,A,phi,opening,exact,max_drop,choices=plan[index];halo=1 if 22<=index<=25 else 0
if halo:
 halo_task=W/'taskdone/verify-slide-halo-control31-v1.json'
 if not halo_task.exists() or json.load(halo_task.open()).get('rc')!=0:raise SystemExit
if max_drop:
 optional_task=W/'taskdone/verify-slide-optional-control31-v2.json'
 if not optional_task.exists() or json.load(optional_task.open()).get('rc')!=0:raise SystemExit
 if choices>=7:
  combined_task=W/'taskdone/verify-slide-learned-control31-v2.json'
  if not combined_task.exists() or json.load(combined_task.open()).get('rc')!=0:raise SystemExit
ou=ov=0.;K=9;L=bars[n]+opening;tag=f'verify-slide31v{9 if halo else 8 if choices>=7 else 7 if max_drop else 6}-n{n}-p{index:03d}';kind='learned rectangle';pool='slidelearn31';D=W/pool
j={'kind':'verify','tag':tag,'slide_milp31':True,'n':n,'pool':pool,'L':L,'bar':bars[n],'phi':phi,'offset_u':ou,'offset_v':ov,'K':K,'seconds':120 if halo else 60,'a':A,'b':A,'halo':halo,'max_tilted':A*A+4 if halo else None,'scheme':'sine','opening':opening,'exact_count':exact,'continuous_refine':True,'local_choices':choices,'learned_reference':True,'max_drop':max_drop}
path=D/(tag+'.json');path.write_text(json.dumps(j));subprocess.run(SCP+[str(path),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True);subprocess.run(SSH+['cd $SCRATCH/squares-k123 && mv tasks/'+tag+'.json.tmp tasks/'+tag+'.json'],check=True)
state['jobs'].append(j);state['last']=time.time();sf.write_text(json.dumps(state,indent=2))
with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA START slide MILP{n} {kind} p{index} phi{phi}, axialoffsets({ou},{ov}), levelsK{K}, L{L},60s HiGHS threads1; existing boxE verification slot, log out/{tag}.log, deadline16:25Z.\n')
print('slide pilot staged',j,flush=True)
