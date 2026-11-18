"""Queue certification in the existing fourth slot and collect its exact output."""
import pathlib,json,subprocess
W=pathlib.Path(__file__).resolve().parent
SSH=['ssh','-S','/tmp/squares-k123-r36-ssh','boxE']
def verify(key,phase,source,raws):
 control=W/'taskdone/verify-control26-580.json'
 if not control.exists():return None
 assert json.load(open(control))['rc']==0,'boxE verifier positive control failed'
 D=W/'certs'/key;tag='verify-'+phase+'-'+key;out=f'certs/{key}/'+('out' if phase=='initial' else 'final');local=D/('out' if phase=='initial' else 'final');done=W/'taskdone'/f'{tag}.json';marker=D/(tag+'.json')
 if done.exists():
  j=json.load(open(done))
  if j['rc']!=0:raise RuntimeError('boxE verifier failed: '+tag)
  local.mkdir(exist_ok=True)
  subprocess.run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r36-ssh','boxE:scratch/squares-k123/'+out+'/',str(local)+'/'],check=True)
  return subprocess.CompletedProcess([],0,stdout='boxE methods_take.py complete; receipt '+str(done)+'\n',stderr='')
 if marker.exists():return None
 remote=[]
 for i,raw in enumerate(raws):
  dest=f'certs/{key}/verify-{phase}-{i}';remote.append(dest)
  subprocess.run(SSH+['mkdir -p $SCRATCH/squares-k123/'+dest],check=True)
  subprocess.run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r36-ssh','--include=*.csv','--exclude=*',str(raw)+'/',f'boxE:scratch/squares-k123/{dest}/'],check=True)
 job=dict(kind='verify',tag=tag,out=out,source=source,raws=remote);marker.write_text(json.dumps(job))
 subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r36-ssh',str(marker),f'boxE:scratch/squares-k123/tasks/{tag}.json.tmp'],check=True)
 subprocess.run(SSH+[f'cd $SCRATCH/squares-k123 && mv tasks/{tag}.json.tmp tasks/{tag}.json'],check=True)
 return None
