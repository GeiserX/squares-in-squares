# Round 29: rename pending jobs to change their order on boxE (old name locked there, new name written here
# and pushed by the next manage30 rsync). Usage: reorder30.py OLDNAME=NEWPREFIX ... (NEWPREFIX like 050 or 000-00)
import json,pathlib,subprocess,sys,time
W=pathlib.Path('$SCRATCH/bounties-squares/take-twoshort-r30/work')
done=[];cmd=''
for a in sys.argv[1:]:
 old,_,pre=a.partition('=');f=W/'jobs'/old
 if not f.exists():print('missing',old);continue
 j=json.load(open(f));j['priority']=int(pre[:3]);rest=old.split('-',1)[1]
 if rest.startswith('00-') and not rest.startswith('00-leg'):rest=rest[3:]
 new=pre+'-'+rest;(W/'jobs'/new).write_text(json.dumps(j));f.unlink();cmd+='mkdir -p locks/%s; rm -f jobs/%s;'%(old,old);done.append(old+' -> '+new)
if cmd:subprocess.run(['ssh','boxE','cd $SCRATCH/squares-twoshort; '+cmd],check=True)
subprocess.run(['rsync','-az',str(W/'jobs')+'/','boxE:scratch/squares-twoshort/jobs/'],check=True)
if done:open(W.parent/'STATE.txt','a').write('%s QUEUE reorder30: %s\n'%(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'; '.join(done)))
print('\n'.join(done))
