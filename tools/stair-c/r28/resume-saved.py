"""Stage exact pending recipes and replace workers only after their current job ends."""
import datetime,json,os,pickle,subprocess,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;W=Path('$SCRATCH/bounties-squares/take-stair-c-r28/work');R=W.parents[1];sys.path.insert(0,str(H));sys.path.insert(0,'.')
from prepare import fingerprint
jobs={};completed=set();pending=set()
for key in ['n','m','s']:
 with tarfile.open(R/'take-stair-c-r27/work/archive'/key/'final-copy.tar.gz')as tf:
  lib=pickle.loads(tf.extractfile('libbase/library.pkl').read());by={q['id']:q for q in lib['mods']};st=pickle.loads(tf.extractfile('state.pkl').read());history=pickle.loads(tf.extractfile('prior-recipes.pkl').read())
  completed.update(st['recipes']);completed.update(history)
  for j in st['build']:
   if not set(j['ids'])<=set(by):continue
   recipe=(j['n'],*[fingerprint(by[k])for k in j['ids']],*j['stacks']);pending.add(recipe)
   jobs[recipe]=dict(j,recipe=recipe,name=j['name'].replace('-r27-','-r28-'),patch='restored unrun r27 '+j['patch'])
completed.difference_update(pending)
file=W/'saved-jobs.pkl';pickle.dump(dict(jobs=list(jobs.values()),completed=completed),open(file,'wb'))
print('SAVED',len(jobs),'pending and',len(completed),'completed',flush=True)
for host,part in [('boxC',0),('boxD',1),('boxE',2)]:
 subprocess.run(['rsync','-a',str(H/'worker.py'),str(H/'saved.py'),str(file),host+':scratch/squares-stair-c/'],check=True,timeout=60)
 script='''cd "$HOME/scratch/squares-stair-c"
previous=$(cat worker.pid)
touch STOP
while kill -0 "$previous" 2>/dev/null; do sleep 2; done
rm -f STOP
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
exec nice -n 5 venv/bin/python -I worker.py PART >> worker.log 2>&1 < /dev/null
'''.replace('PART',str(part))
 with (W/f'resume-{part}.sh').open('w')as f:f.write(script)
 subprocess.run(['rsync','-a',str(W/f'resume-{part}.sh'),host+':scratch/squares-stair-c/'],check=True,timeout=60)
 cmd='cd $SCRATCH/squares-stair-c && nohup sh resume-PART.sh > resume.log 2>&1 < /dev/null &'.replace('PART',str(part))
 # Keep the launching shell until nohup has inherited its files.
 subprocess.run(['ssh',host,cmd+' sleep 2'],check=True,timeout=20)
 print('RESTART AFTER CURRENT JOB',host,flush=True)
with (W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA STAGE saved recipes '+str(len(jobs))+' exact unrun, '+str(len(completed))+' completed. Workers adopt saved.py after current job ends, then restore matching admitted geometry incrementally. Log work/resume-saved.log; same hard deadline05:45Z. Controls rejected completed, missing modules, changed recipe and duplicate.\n')
