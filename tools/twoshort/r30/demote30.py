# Round 29: with 2 boxE slots, a pending job of an n that another lane is kicking with midm_scan on boxE
# right now waits (priority 20) behind the n nobody kicks. 09:05Z: rebuild and midm both ran 916 while 5 of our
# priority-0 jobs were 916.
import json,re,pathlib,subprocess,sys,time
W=pathlib.Path('$SCRATCH/bounties-squares/take-twoshort-r30/work')
ps=subprocess.run(['ssh','boxE','ps -axo command | grep midm_scan | grep -v squares-twoshort | grep -v grep; echo ---; ls $SCRATCH/squares-twoshort/locks'],capture_output=True,text=True).stdout.split('---\n')
busy={int(m) for m in re.findall(r'--n (\d+)',ps[0])};locks=set(ps[1].split())
moved=[]
for f in sorted(W.glob('jobs/00[0-4]-*.json')):
 if f.name in locks or f.name.startswith('000-00-'):continue
 try:j=json.load(open(f))
 except ValueError:continue
 if j.get('n') not in busy:continue
 j['priority']=20;new=W/'jobs'/('020-'+f.name.split('-',1)[1])
 if '--dry' not in sys.argv:
  new.write_text(json.dumps(j));f.unlink()
 moved.append(f.name)
if moved and '--dry' not in sys.argv:
 subprocess.run(['ssh','boxE','cd $SCRATCH/squares-twoshort; '+''.join('mkdir -p locks/%s; rm -f jobs/%s;'%(m,m) for m in moved)])
 open(W.parent/'STATE.txt','a').write('%s QUEUE demote30: %d pending jobs to priority 20, their n kicked by another lane on boxE now (n %s): %s\n'%(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),len(moved),' '.join(map(str,sorted(busy))),' '.join(moved)))
print('busy',sorted(busy),'moved',moved)
