"""Publish one contact-LP result of the fresh near-miss batch (border r26 revive, boxA, light).
Usage: publish_lp.py BATCHID [--dry]. Steps: floatsafe the LP output; one certified-file fq on boxC (keep the smaller);
check against the base bar and every live take-*-r26 row by more than 1e-10; walk the start with provenance.audit;
check the source text with the lane source policy; write N.csv, then take.tsv by rename; one handoff line."""
import sys,csv,math,json,hashlib,os,subprocess,time
from pathlib import Path
W=Path(__file__).resolve().parent.parent;T=W.parent;S=T.parent;D=W/'lpnear'
sys.path.insert(0,'.');sys.path.insert(0,str(W))
csv.field_size_limit(1<<26)
import border_sweep as bs
bs.lib()
import floatsafe,source_policy as sp,provenance as pv
bid=sys.argv[1];row=next(r for r in csv.reader(open(D/'batch.tsv'),delimiter='\t') if r[0]==bid)
n=int(row[1]);start=Path(row[3]);b=f'{bid}_{n}';copy=D/'in'/f'{b}.csv'
h=hashlib.sha256(copy.read_bytes()).hexdigest()
assert start.exists() and hashlib.sha256(start.read_bytes()).hexdigest()==h,'start changed since the copy'
assert pv.audit(str(start)),'audit refused '+str(start)
md=pv.metadata(start)
def cert(rows):
 _,fr,sc,e=floatsafe.work((n,[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in rows]));return fr,sc,e
fr,sc,e=cert(list(csv.DictReader(open(D/'out'/b/'raw'/f'{n}.csv'))));assert fr is not None,e
lp_sc=sc
s,A=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr]);bs.write_txt(str(D/f'{b}.input.txt'),s,A)
R='scratch/squares-border-r26/lp/'
subprocess.run(['scp','-q',str(D/f'{b}.input.txt'),f'boxC:{R}{b}.input.txt'],check=True)
o=subprocess.run(['ssh','boxC',f'cd $SCRATCH/squares-border-r26 && nice -n 5 venv/bin/python -c "import border_sweep as bs; print(bs.fq_call(\'./fq\',\'lp/{b}.input.txt\',\'lp/{b}.output.txt\',[],600))"'],capture_output=True,text=True,check=True).stdout.strip()
subprocess.run(['scp','-q',f'boxC:{R}{b}.output.txt',str(D/f'{b}.output.txt')],check=True)
_,A2=bs.read_txt(str(D/f'{b}.output.txt'))
fr2,sc2,e2=cert([{'n':str(n),'square_id':str(i),'x':repr(x),'y':repr(y),'angle':repr(math.radians(a))} for i,(x,y,a) in enumerate(A2)])
fqnote=f'one certified-file fq on boxC ({o}): '
if fr2 is not None and sc2<sc:fr,sc=fr2,sc2;fqnote+=f'kept the fq output, score {sc2!r}'
else:fqnote+='its output was not smaller, so the certified LP result is kept'
base={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))}[n]
live={}
for t in S.glob('take-*-r26'):
 if t==T or not (t/'take.tsv').exists():continue
 for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t'):
  if int(r['n'])==n:live[t.name]=float(r['new'])
print(b,'LP certified',repr(lp_sc),'final',repr(sc),'side',repr((sc+1)*math.sqrt(n)),'base',repr(base),'live',live,fqnote)
assert sc<base-1e-10 and all(sc<v-1e-10 for v in live.values()),'not below every bar by 1e-10'
msrc=md.get('source','');mlic=md.get('licence','')
if not isinstance(msrc,str):msrc=json.dumps(msrc,sort_keys=True)
src=(f'contact LP reclose with free angles (lane methods_lp.py, --iters 40, boxC) of the fresh near miss {start} '
     f'(sha256 {h}), whose recorded source is: {msrc}; floatsafe on boxA; {fqnote}')
lic='ours, on: '+(mlic if isinstance(mlic,str) else json.dumps(mlic))
pol=sp.classify(src,lic);print('policy',pol['status'],pol.get('reason'))
assert pol['status']=='none'
if '--dry' in sys.argv:sys.exit(0)
with open(T/f'{n}.csv.tmp','w',newline='') as g:
 w=csv.writer(g);w.writerow(['n','square_id','x','y','angle'])
 for r in fr:w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
os.replace(T/f'{n}.csv.tmp',T/f'{n}.csv')
old=[r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t') if int(r['n'])!=n] if (T/'take.tsv').exists() else []
new=dict(n=str(n),held=repr(base),new=repr(sc),gain='%.3e'%(base-sc),source=src,licence=lic)
p=T/f'take.tsv.lp{os.getpid()}.tmp'
with open(p,'w') as f:
 w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(sorted(old+[new],key=lambda r:int(r['n'])))
os.replace(p,T/'take.tsv')
ts=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
gl=min([base]+list(live.values()))-sc
with open(T/'STATE.txt','a') as f:f.write(f'{ts} boxA PUBLISH {n} score {sc!r} (base gain {base-sc:.3e}, {gl:.3e} below the best live take), contact LP reclose of {start}; take.tsv by rename\n')
with open(S/'handoff-r26.log','a') as f:f.write(f'{ts} border -> all: certified n={n} score {sc!r}, {gl:.3e} below the best live take, contact LP reclose of a fresh near miss, {T}/{n}.csv; source in {T}/take.tsv\n')
print('published',n,repr(sc))
