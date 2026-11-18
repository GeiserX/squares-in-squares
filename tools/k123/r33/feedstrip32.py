"""Run a finite strip pilot in the existing verification slot and return changed donors."""
from pathlib import Path
import sys,json,subprocess,time,hashlib,csv,fcntl,math
import numpy as np
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;sys.path[:0]=[str(W),str(W/'lane')];sys.dont_write_bytecode=True
lock=(W/'strip-feed32.lock').open('a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit
SSH=['ssh','-S','/tmp/squares-k123-r33-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r33-ssh'];sf=W/'strip-feed32.json';state=json.load(sf.open()) if sf.exists() else {'jobs':[]}
def save():
 p=sf.with_suffix('.tmp');p.write_text(json.dumps(state,indent=2));p.replace(sf)
def note(s):
 with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA STRIP32 '+s+'; cutoff00:15Z.\n')
def geom(A):
 xy=A[:,:2];th=A[:,2];cs=np.cos(th);sn=np.sin(th);corners=np.concatenate([xy+np.column_stack((cs*dx-sn*dy,sn*dx+cs*dy)) for dx,dy in [(.5,.5),(.5,-.5),(-.5,.5),(-.5,-.5)]])
 xy=xy-(corners.min(0)+corners.max(0))/2;axes=np.column_stack((cs,sn));out=[]
 for swap in [False,True]:
  for sx in [-1,1]:
   for sy in [-1,1]:
    X=(xy[:,::-1] if swap else xy)*[sx,sy];U=(axes[:,::-1] if swap else axes)*[sx,sy];angle=np.arctan2(U[:,1],U[:,0])%(np.pi/2);angle[np.abs(angle-np.pi/2)<1e-10]=0;angle[np.abs(angle)<1e-10]=0
    Q=np.round(np.column_stack((X,angle)),11);Q[np.abs(Q)<1e-12]=0;Q=Q[np.lexsort((Q[:,2],Q[:,1],Q[:,0]))];out.append(hashlib.sha256(Q.tobytes()).hexdigest())
 return min(out)
for tag in ['verify-strip32-engine-control','verify-strip32-bounds-control','verify-strip32v2-engine-control','verify-strip32v2-bounds-control']:
 p=W/'taskdone'/(tag+'.json')
 if not p.exists():raise SystemExit
 if json.load(p.open()).get('rc')!=0:note('STOP control failed '+tag);state['halted']=tag;save();raise SystemExit
if len(state['jobs'])>=15:
 for control_tag32 in ['verify-strip32v3-engine-control','verify-strip32v3-bounds-control']:
  cp32=W/'taskdone'/(control_tag32+'.json')
  if not cp32.exists() or json.load(cp32.open()).get('rc')!=0:raise SystemExit
for j in state['jobs']:
 if j.get('collected'):continue
 p=W/'taskdone'/(j['tag']+'.json')
 if not p.exists():continue
 D=W/'strip-results32';D.mkdir(exist_ok=True);out=D/(j['tag']+'.json');r=subprocess.run(SCP+['boxE:scratch/squares-k123/out/slidestrip32/'+j['tag']+'/result.json',str(out)],text=True,capture_output=True,timeout=30)
 result=json.load(out.open()) if r.returncode==0 else {'result_unavailable':True};j['result']=result
 if result.get('S') is not None and result.get('learned_reference'):
  ref=result['learned_reference'];fixedS=[abs(x-y) for k,(x,y) in enumerate(zip(result['S'],ref['S'])) if k not in j['free_rows32']];fixedR=[abs(x-y) for k,(x,y) in enumerate(zip(result['R'],ref['R'])) if k not in j['free_columns32']];error=max(fixedS+fixedR,default=0.)
  selected=set(map(tuple,result['sites_selected']));halo=j['halo'];aa=result['a'];bb=result['b'];outside_ok=all(((ii,jj) in selected)==(halo<=ii<aa-halo and halo<=jj<bb-halo) for ii in range(aa) for jj in range(bb) if ii not in j['free_columns32'] and jj not in j['free_rows32'])
  width=j['a'];whole=19 if width==13 else 25;corridor=17 if width==13 else 23;phi=math.radians(j['phi']);analytic=whole+((2**.5*width+math.sin(phi))/math.cos(phi)-corridor)/2
  holes_ok=not(set(map(tuple,j.get('forced_holes32',[])))&selected)
  if j.get('explicit_mask32'):holes_ok=holes_ok and selected==set(map(tuple,j['explicit_mask32']))
  origin_error32=0.
  if result.get('origin32'):
   angle=math.pi/4+math.radians(j['phi']);u32=np.array([math.cos(angle),math.sin(angle)]);v32=np.array([-u32[1],u32[0]]);want32=np.array(ref['O'])+(result['L']-ref['side'])/2+j.get('origin_shift_u32',0.)*u32+j.get('origin_shift_v32',0.)*v32;origin_error32=float(np.max(abs(want32-np.array(result['origin32']))))
  holes_ok=holes_ok and origin_error32<1e-9
  good=error<1e-7 and outside_ok and holes_ok and abs(ref['side']-analytic)<1e-6
  result['independent_strip_scope32']={'fixed_parent_max_error':error,'outside_cells_match_core':outside_ok,'forced_holes_absent':holes_ok,'origin_error':origin_error32,'analytic_reference':analytic,'passed':good}
  if not good:state['halted']='strip scope verification failed '+j['tag'];save();note(state['halted']);raise SystemExit
 j['collected']=True;j['rc']=json.load(p.open())['rc'];save();note('FINISH '+j['tag']+' status='+str(result.get('status'))+' count='+str(result.get('output_count',result.get('count')))+' side='+str(result.get('output_side',result.get('side'))))
 if j.get('learned_control') and (j['rc']!=0 or not result.get('learned_positive_control_passed')):state['halted']='full367 baseline control';save();raise SystemExit
 if (not j.get('learned_control') or j.get('export_control32')) and result.get('output_count'):
  from provenance24 import mlp
  raw=D/(j['tag']+'.csv');r=subprocess.run(SCP+['boxE:scratch/squares-k123/out/slidestrip32/'+j['tag']+'/model-output.csv',str(raw)],text=True,capture_output=True,timeout=30)
  if r.returncode==0:
   n=int(result['output_count']);A=mlp.load(str(raw),{n})[n];identity=geom(A);old=[]
   for q in (S/'take-k123-r31/near').glob(f'{n}-slide31-*.csv'):
    old.append(geom(mlp.load(str(q),{n})[n]))
   if identity in old or identity in state.get('exported_geometry',[]):note('SKIP unchanged prior slide geometry '+j['tag']);continue
   data=raw.read_bytes();h=hashlib.sha256(data).hexdigest();target=T/'near'/f'{n}-strip32-{h[:16]}.csv';row={'n':str(n),'source':'own slide_strip32.py constructive strip MILP; parameters '+json.dumps({k:v for k,v in j.items() if k not in {'result','collected','rc'}},sort_keys=True)+'; immutable calibration pool '+str(W/j['pool']/(j['pool']+'.csv'))+'; source manifest '+str(W/j['pool']/('sources-'+j['pool']+'.json'))+'; held n = 261 of round 15 and held n = '+str(j['n'])+' of round 15; output sha256 '+h,'licence':'own mathematical construction; source terms in the pinned held calibration manifest'}
   Path(str(raw)+'.json').write_text(json.dumps(row));from publication_source26 import check
   proof=check(raw,row)
   if proof['clean']:
    Path(str(target)+'.json').write_text(json.dumps(row));target.write_bytes(data);state.setdefault('exported_geometry',[]).append(identity);save();line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: constructive strip donor n={n}, side={result["output_side"]:.14g}, fixed outside selected small row/column strips during MILP, finite learned domains, {target}, model receipt {out}\n'
    with (S/'handoff-r33.log').open('a') as f:f.write(line)
    note('EXPORT '+str(target))
if state.get('halted') or any(not j.get('collected') for j in state['jobs']):raise SystemExit
if time.time()>float((W/'search-deadline').read_text())-700 or state.get('last',0)>time.time()-60:raise SystemExit
index=len(state['jobs'])
if index>=21:raise SystemExit
if index<4:
 n=367;width=13;pool='strippool32';control=index==0;region=0 if control else index-1
elif index<8:
 if not (W/'strip626-ready32').exists():raise SystemExit
 n=626;width=17;pool='strippool62632';control=index==4;region=0 if control else index-5
else:
 n=367;width=13;pool='strippool32';control=index==8;region=0
size=width+2;center=size//2;ranges=[list(range(3)),[center-1,center,center+1],list(range(size-3,size))];free=ranges[region];cols=free if n==626 else []
tag=f'verify-strip32-baseline{n}' if control else f'verify-strip32-target{n}-{region+1}'
whole=19 if width==13 else 25;corridor=17 if width==13 else 23;phi=math.radians(.4);L=whole+((2**.5*width+math.sin(phi))/math.cos(phi)-corridor)/2+5e-7
j={'kind':'verify','tag':tag,'slide_strip32':True,'strip32':True,'n':n,'pool':pool,'phi':.4,'a':width,'b':width,'halo':1,'L':L,'anchor_reference':5e-7,'learned_reference':True,'continuous_refine':True,'local_choices':7,'free_rows32':free,'free_columns32':cols,'max_drop':size*size-width*width+(0 if control else 2),'max_tilted':width*width+(0 if control else 3),'seconds':60 if control else 120,'exact_count':control,'force_halo_absent':control,'learned_control':control}
if 8<=index<15:
 holes=[[3,1],[1,3],[2,1],[1,2],[13,11],[11,13]];hole=holes[0 if control else index-9];end=hole[0]>7 or hole[1]>7;free=list(range(size-3,size)) if end else list(range(3))
 j.update(tag='verify-strip32-hole-control367' if control else f'verify-strip32-outline367-{index-9}',free_rows32=free,free_columns32=free,max_drop=58 if control else 56,max_tilted=172 if control else 169,exact_count=True,requires_outside_core32=not control,force_halo_absent=False,forced_holes32=[hole],seconds=60 if control else 120,learned_control=control,export_control32=control)
 tag=j['tag']
if index>=15:
 from doublejog32 import double
 mask=double(13,13,2,1);core={(i,k) for i in range(1,14) for k in range(1,14)};free=list(range(4));assert len(mask)==171
 assert all(((i,k) in mask)==((i,k) in core) for i in range(15) for k in range(15) if i not in free and k not in free)
 holes=[[i,k] for i in range(15) for k in range(15) if (i in free or k in free) and (i,k) not in mask];trial=index-15;phi=[.8,1.6,3.11801833][trial%3];centered=trial<3
 j.update(tag=f'verify-strip32-doublejog-{trial}',phi=phi,free_rows32=free,free_columns32=free,max_drop=54,max_tilted=171,exact_count=True,force_halo_absent=False,forced_holes32=holes,explicit_mask32=[list(x) for x in sorted(mask)],seconds=120,learned_control=False,export_control32=False,origin_shift_u32=-.5 if centered else 0.,origin_shift_v32=.5 if centered else 0.,requires_outside_core32=True)
 tag=j['tag']
 j['L']=19+((2**.5*13+math.sin(math.radians(phi)))/math.cos(math.radians(phi))-17)/2+5e-7
p=W/(tag+'.json');p.write_text(json.dumps(j));subprocess.run(SCP+[str(p),'boxE:scratch/squares-k123/tasks/'+p.name+'.tmp'],check=True,timeout=30);subprocess.run(SSH+[f'cd $SCRATCH/squares-k123 && mv tasks/{p.name}.tmp tasks/{p.name}'],check=True,timeout=30);state['jobs'].append(j);state['last']=time.time();save();note('START '+tag+' free_rows='+str(free)+' in fourth boxE slot, 60/120s solver cap, known core feasible by construction')
