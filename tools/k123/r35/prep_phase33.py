"""Pin held calibration inputs and queue finite-domain controls in boxE slot."""
from pathlib import Path
import shutil,sys,json,csv,subprocess,time,hashlib
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,credit,key
O=S/'take-k123-r32/work';pool='phasepool33';D=W/pool;D.mkdir(exist_ok=True);manifest={}
for n in [261,367]:
 p=W/('control'+str(n)+'.csv');shutil.copy(O/p.name,p);shutil.copy(Path(str(O/p.name)+'.json'),Path(str(p)+'.json'));A=mlp.load(str(p),{n})[n];c=credit(n,A,str(p));assert c,('calibration source refused',n);manifest[str(n)]={**c,'input_file_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'input_file_snapshot':str(p)}
with (D/(pool+'.csv')).open('w') as f:
 wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
 for n in [261,367]:
  for i,row in enumerate(mlp.load(str(W/('control'+str(n)+'.csv')),{n})[n]):wr.writerow([n,i,*row])
(D/('sources-'+pool+'.json')).write_text(json.dumps(manifest));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text())
for p in [W/'slide_phase33.py',W/'verify26.py',W/'control261.csv',W/'control367.csv',D/(pool+'.csv'),D/('sources-'+pool+'.json'),D/('bars-'+pool+'.tsv')]:subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-ssh',str(p),'boxE:scratch/squares-k123/'],check=True)
base={'kind':'verify','slide_phase33':True,'pool':pool}
jobs=[{**base,'tag':'verify-phase33-bounds','strip_bound_control32':True},{**base,'tag':'verify-phase33-omission','optional_control31':True},{**base,'tag':'verify-phase33-gauge','n':367,'a':13,'b':13,'halo':1,'L':19.7,'phi':.4,'learned_reference':True,'learned_control':True,'anchor_reference':5e-7,'strip32':True,'free_rows32':list(range(15)),'free_columns32':list(range(15)),'max_drop':56,'max_tilted':169,'exact_count':True,'force_halo_absent':True,'local_choices':3,'parent_phases33':[-1.,0.,1.],'force_phases33':[-1.,1.],'origin_shift_u32':1.,'origin_shift_v32':-1.,'seconds':30}]
for j in jobs:
 p=W/(j['tag']+'.json');p.write_text(json.dumps(j));subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-ssh',str(p),'boxE:scratch/squares-k123/tasks/'+p.name+'.tmp'],check=True);subprocess.run(['ssh','-S','/tmp/squares-k123-r35-ssh','boxE','cd $SCRATCH/squares-k123 && mv tasks/'+p.name+'.tmp tasks/'+p.name],check=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START integer-parent-phase constructive model controls in existing boxE verification slot. R32 double-jog domain had learned S range[-.157,.021], no unit phase jumps; explicit mask shifts sites by1. New domain allows nearest3 levels around phases-1/0/1 for every parent, with auxiliary product states only on allowed pairs. Changed offset domain, not another unchanged mask trial. Controls: fixed-parent positive/negative bounds, forced omission, and367 gauge witness forcedS-1/R+1 with compensating O+u-v. Keep targets blocked until controls pass. Logs out/verify-phase33*.log; hard16:25Z.\n')
print('phase33 controls queued',flush=True)
