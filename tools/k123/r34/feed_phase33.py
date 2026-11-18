"""Run a finite six-case integer-phase scout after its controls, one boxE task at a time."""
from pathlib import Path
import json,sys,time,subprocess,hashlib,math,fcntl,shutil
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W),str(W/'lane')];D=W/'phase-results33';D.mkdir(exist_ok=True)
SSH=['ssh','-S','/tmp/squares-k123-r34-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh'];sf=W/'phase-feed33.json';state=json.load(sf.open()) if sf.exists() else {'jobs':[]}
def run(args,**kw):return subprocess.run(args,check=True,timeout=30,**kw)
def save():
 p=sf.with_suffix('.tmp');p.write_text(json.dumps(state,indent=2));p.replace(sf)
def note(s):
 with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA PHASE33 '+s+'; log out/verify-phase33*.log; common07:25Z.\n')
controls=['verify-phase33-bounds','verify-phase33-omission','verify-phase33-gauge2','verify-phase33-phase-absent']
if not all((W/'taskdone'/(tag+'.json')).exists() for tag in controls):raise SystemExit
if not (W/'phase-control33.json').exists():
 result={};code=hashlib.sha256((W/'slide_phase33.py').read_bytes()).hexdigest()
 for tag in controls:
  rc=json.load((W/'taskdone'/(tag+'.json')).open())['rc']
  if tag.endswith('phase-absent'):
   log=run(SSH+['tail -n 5 $SCRATCH/squares-k123/out/'+tag+'.log'],capture_output=True,text=True).stdout;assert rc!=0 and 'requested integer S phase absent from domain' in log,log
   result[tag]={'expected_refusal':True,'rc':rc};continue
  assert rc==0,(tag,rc)
  p=D/(tag+'.json');run(SCP+['boxE:scratch/squares-k123/out/phase33/'+tag+'/result.json',str(p)]);r=json.load(p.open())
  if tag.endswith('bounds'):assert r['strip_bound_control_passed32']
  if tag.endswith('omission'):assert r['optional_positive_control_passed']
  if tag.endswith('gauge2'):assert r['learned_positive_control_passed'] and r['code_sha256']==code and r['output_count']==367
  result[tag]={k:r.get(k) for k in ['status','count','output_count','output_side','variables','active_joint_states33','solve_seconds']}
 receipt={'passed':True,'code_sha256':code,'controls':result};(W/'phase-control33.json').write_text(json.dumps(receipt,indent=2));run(SCP+[str(W/'phase-control33.json'),'boxE:scratch/squares-k123/']);note('CONTROL PASS '+json.dumps(result))
for j in state['jobs']:
 if j.get('collected'):continue
 p=W/'taskdone'/(j['tag']+'.json')
 if not p.exists():continue
 rc=json.load(p.open())['rc'];out=D/(j['tag']+'.json');run(SCP+['boxE:scratch/squares-k123/out/phase33/'+j['tag']+'/result.json',str(out)]);r=json.load(out.open());j['collected']=True;j['rc']=rc;j['result']={k:r.get(k) for k in ['status','message','count','output_count','output_side','output_gap','dual_bound','variables','constraints','active_joint_states33','solve_seconds','continuous_fit','Slevels','Rlevels']};save();note('FINISH '+j['tag']+' '+json.dumps(j['result']))
 if rc==0 and r.get('output_count'):
  n=int(r['output_count']);p=D/(j['tag']+'.csv');run(SCP+['boxE:scratch/squares-k123/out/phase33/'+j['tag']+'/model-output.csv',str(p)]);raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();target=T/'near'/f'{n}-phase33-{sha[:16]}.csv'
  manifest=json.load((W/'phasepool33/sources-phasepool33.json').open());from compact_source28 import credits
  row={'n':str(n),'source':'own slide_phase33.py constructive integer-parent-phase model; parameters '+json.dumps({k:v for k,v in j.items() if k not in {'result','collected','rc'}},sort_keys=True)+'; calibrated on held n = 261 of round 15 and held n = 367 of round 15; input pool '+str(W/'phasepool33/phasepool33.csv')+'; pinned calibration ancestry: '+credits(list(manifest.values()))+'; output sha256 '+sha,'licence':'own mathematical construction; historical held calibration terms in the pinned ancestry'}
  Path(str(p)+'.json').write_text(json.dumps(row));from publication_source26 import check
  proof=check(p,row)
  if proof['clean'] and not target.exists():
   Path(str(target)+'.json').write_text(json.dumps(row));target.write_bytes(raw);line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: uncounted integer-parent-phase donor n={n}, side={r["output_side"]:.14g}, max-count scout from new phase domain, {target}; receipt {out}\n'
   for q in [T/'STATE.txt',T.parent/'handoff-r34.log']:
    with q.open('a') as f:f.write(line)
 if rc:state['halted']='model task error '+j['tag'];save();raise SystemExit
if state.get('halted') or any(not j.get('collected') for j in state['jobs']):raise SystemExit
index=len(state['jobs'])
if index>=6 or time.time()>float((W/'search-deadline').read_text())-300:raise SystemExit
from doublejog32 import double
mask=double(13,13,2,1);assert len(mask)==171
phi=[.8,1.6,3.11801833][index%3];centered=index>=3
j={'kind':'verify','tag':'verify-phase33-scout'+str(index),'slide_phase33':True,'pool':'phasepool33','n':365,'calibration_n33':367,'desired_n33':367,'a':13,'b':13,'halo':1,'phi':phi,'L':19+((2**.5*13+math.sin(math.radians(phi)))/math.cos(math.radians(phi))-17)/2+5e-7,'learned_reference':True,'continuous_refine':True,'strip32':True,'free_rows32':list(range(15)),'free_columns32':list(range(15)),'max_drop':54,'max_tilted':171,'exact_count':False,'local_choices':3,'parent_phases33':[-1.,0.,1.],'forced_holes32':[[i,k] for i in range(15) for k in range(15) if (i,k) not in mask],'explicit_mask33':[list(x) for x in sorted(mask)],'origin_shift_u32':-.5 if centered else 0.,'origin_shift_v32':.5 if centered else 0.,'seconds':30}
p=W/(j['tag']+'.json');p.write_text(json.dumps(j));run(SCP+[str(p),'boxE:scratch/squares-k123/tasks/'+p.name+'.tmp']);run(SSH+['cd $SCRATCH/squares-k123 && mv tasks/'+p.name+'.tmp tasks/'+p.name]);state['jobs'].append(j);save();note('START '+j['tag']+' goal365/maximize, desired367, phi'+str(phi)+', parents all free with integer phases, offset'+str((j['origin_shift_u32'],j['origin_shift_v32'])))
