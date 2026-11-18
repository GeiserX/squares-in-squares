"""Recheck every retained row with the complete independent source walker."""
import pathlib,sys,json,csv,time,signal
W=pathlib.Path(__file__).resolve().parent
end=float((W/'deadline').read_text());signal.signal(signal.SIGALRM,lambda *args:sys.exit('source recheck deadline'));signal.alarm(max(1,int(end-time.time())))
sys.dont_write_bytecode=True;sys.path.insert(0,'.');import quench_walk
from current_walk29 import configure
quench_walk=configure(quench_walk)
csv.field_size_limit(20000000);out=[]
for row in csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t'):
 result=quench_walk.check(str(W.parent/(row['n']+'.csv')));out.append(result)
 print(json.dumps({k:result[k] for k in ['n','clean','files','hits']}),flush=True)
p=W/'independent-source-walk26.json';p.with_suffix('.tmp').write_text(json.dumps(out,indent=2));p.with_suffix('.tmp').replace(p)
with open(W.parent/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH recheck_full26.py: '+str([(r['n'],r['clean']) for r in out])+'; work/independent-source-walk26.json; deadline00:15Z.\n')
signal.alarm(0);raise SystemExit(0 if all(r['clean'] for r in out) else 1)
