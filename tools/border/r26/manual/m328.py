"""Hand path for the 328 window of the backlog r26 365 take (border r26, boxA, light).
Step 1 (no args): certify the rev start (one border row and column removed from take-backlog-r26/365.csv),
check it against its donor copy with border_sweep.check_start, write manual/328-cert.csv and manual/328.input.txt.
Step 2 (arg 'back'): floatsafe the boxC fq output manual/328.output.txt and keep the smaller certified packing."""
import sys,csv,math,json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent.parent;M=W/'manual'
sys.path.insert(0,'.')
csv.field_size_limit(1<<26)
import border_sweep as bs
bs.lib()
import floatsafe
ident='328-rev-365-ce9df921-q0-v0'
r=next(x for x in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t') if x['id']==ident)
def rows_of(txt):
 _,A=bs.read_txt(str(txt))
 return [{'n':'328','square_id':str(i),'x':repr(x),'y':repr(y),'angle':repr(math.radians(a))} for i,(x,y,a) in enumerate(A)]
def out(path,fr):
 with open(path,'w') as f:
  w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows({k:q[k] for k in w.fieldnames} for q in fr)
if len(sys.argv)==1:
 bs.check_start(str(W/'q'),r)
 print('check_start ok; donor copy sha256',hashlib.sha256(Path(r['near']).read_bytes()).hexdigest())
 _,fr,sc,e=floatsafe.work((328,rows_of(W/'q'/(ident+'.start.txt'))))
 assert fr is not None,e
 side=(sc+1)*math.sqrt(328);print('certified start side',repr(side),'score',repr(sc))
 out(M/'328-cert.csv',fr)
 s,A=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr]);bs.write_txt(str(M/'328.input.txt'),s,A)
 json.dump({'score':sc,'side':side},open(M/'328-cert.json','w'))
else:
 c=json.load(open(M/'328-cert.json'))
 _,fr,sc,e=floatsafe.work((328,rows_of(M/'328.output.txt')))
 print('fq output certifies:',fr is not None,e if fr is None else repr((sc+1)*math.sqrt(328)))
 if fr is not None and sc<c['score']:
  out(M/'328-final.csv',fr);print('keep fq output',repr(sc))
 else:
  M.joinpath('328-final.csv').write_bytes((M/'328-cert.csv').read_bytes());print('keep certified input',repr(c['score']))
