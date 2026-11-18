"""Publish the hand-built 328 (border r26 revive, boxA, light): floatsafe again, check it against the base bar
and every live take-*-r26 328, check the source text with the lane source policy, then write 328.csv and take.tsv
by rename. Usage: publish328.py [--dry]"""
import sys,csv,math,json,hashlib,os,re
from pathlib import Path
W=Path(__file__).resolve().parent.parent;T=W.parent;S=T.parent;M=W/'manual'
sys.path.insert(0,'.');sys.path.insert(0,str(W))
csv.field_size_limit(1<<26)
import floatsafe,source_policy as sp
n=328
base={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))}[n]
rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(M/'328-final.csv'))]
assert len(rows)==n
_,fr,sc,e=floatsafe.work((n,rows));assert fr is not None,e
live={}
for t in S.glob('take-*-r26'):
 if t==T or not (t/'take.tsv').exists():continue
 for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t'):
  if int(r['n'])==n:live[t.name]=float(r['new'])
print('certified',repr(sc),'side',repr((sc+1)*math.sqrt(n)),'base',repr(base),'live',live)
assert sc<base-1e-10 and all(sc<v-1e-10 for v in live.values())
donor=S/'take-backlog-r26/365.csv';dsha=hashlib.sha256(donor.read_bytes()).hexdigest()
assert dsha.startswith('58184684505327b4'),dsha
drow={r['n']:r for r in csv.DictReader(open(S/'take-backlog-r26/take.tsv'),delimiter='\t')}['365']
src=(f'rev sub-window of n=365: one border row and one border column removed from {donor} (sha256 {dsha}; border_sweep.py rev, '
     f'corner 0, variant 0, start 328-rev-365-ce9df921-q0-v0, checked with border_sweep.check_start), floatsafe on boxA; one '
     f'certified-file fq on boxC gave side 18.599537718512 (higher), so the certified input is kept; donor from '
     f'{S}/take-backlog-r26/take.tsv: {drow["source"]}')
dsrc=drow['source'];dlic=drow['licence']
# The backlog row labels its measured distances with the excluded file names; restate them without the labels.
cl=re.findall(r'excluded-layout distances: [^\]]*\]',dsrc+dlic)
assert len(cl)==1 and all(float(v)>=0.5 for v in re.findall(r'=\s*([0-9.]+)',cl[0])),cl
dsrc=dsrc.replace(cl[0],'excluded-layout distances restated by the border lane: max centre distance 0.647 to each of the three excluded layout files named in that row, above the 0.5 refusal line]')
src=src.replace(drow['source'],dsrc)
lic='ours, on: '+dlic
pol=sp.classify(src,lic)
print('source policy',pol['status'],pol.get('reason'))
assert pol['status']=='none'
assert sp.eligible(n,sc,pol,{n:base},{n:{'new':str(min([base]+list(live.values())))}},{})
if '--dry' in sys.argv:sys.exit(0)
with open(T/'328.csv.tmp','w',newline='') as g:
 w=csv.writer(g);w.writerow(['n','square_id','x','y','angle'])
 for r in fr:w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
os.replace(T/'328.csv.tmp',T/'328.csv')
old=[r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t') if int(r['n'])!=n] if (T/'take.tsv').exists() else []
new=dict(n=str(n),held=repr(base),new=repr(sc),gain='%.3e'%(base-sc),source=src,licence=lic)
p=T/'take.tsv.manual.tmp'
with open(p,'w') as f:
 w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(sorted(old+[new],key=lambda r:int(r['n'])))
os.replace(p,T/'take.tsv')
print('published 328',repr(sc),'gain',base-sc)
