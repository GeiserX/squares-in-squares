"""Freeze verified, traced ends against the latest base and live peers."""
import csv,hashlib,json,math,pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import controller26 as C
import source_gate26 as G
A=C.A;T=W.parent;S=T.parent

def passes(score,base,peer,verified,clean):
 return verified and clean and score<base-1e-10 and score<peer-1e-12

def controls():
 assert passes(.1,.2,.15,True,True)
 assert not passes(.15,.2,.15,True,True)
 assert not passes(.1,.2,.15,False,True)
 assert not passes(.1,.2,.15,True,False)
 assert not passes(.2-1e-11,.2,.3,True,True)
 print('CONTROL lower verified clean row accepted; tied peer, missing verification, bad source and tiny base gain refused',flush=True)

controls()
if '--controls' in sys.argv:raise SystemExit(0)
verification=json.load(open(W/'boxE-raw/verification26.json'))
assert all(verification['controls'].values()) and not verification['errors']
bar,peer=C.bars();best={};refused=[];ends=0
for j in json.load(open(W/'jobs.json')):
 if j['kind']=='control':continue
 folder=W/'boxE-raw'/j['id'];p=folder/'final'/f'{j["n"]}.csv'
 if not p.exists()or not(folder/'done.json').exists():continue
 d=json.load(open(folder/'done.json'));n=j['n'];key=j['id']+'/final/'+str(n)+'.csv'
 ap=json.load(open(j['ancestry']))if j.get('ancestry')else{}
 clean=ap.get('policy')=='strict26v5'and ap.get('ok')and all(A.rejected(v['source'],v['licence'],terminal=not v.get('parents'))is None for v in ap.get('nodes',{}).values())
 vp=verification['verified'].get(key);verified=False
 if vp and d.get('quench_from_certified'):
  digest=hashlib.sha256(p.read_bytes()).hexdigest()
  cp=folder/'certin'/f'{n}.csv';done=folder/'quench'/f'{n}.done'
  verified=digest==d['sha256']==vp['sha256']and cp.exists()and done.exists()
  if verified:
   ch=hashlib.sha256(cp.read_bytes()).hexdigest()
   verified=ch==d['quench_input_sha256']==done.read_text().strip()and vp['clearance']>=2.2e-11 and abs(vp['score']-d['new'])<1e-12
 ends+=1
 if passes(d['new'],bar[n],peer[n],verified,clean):
  if n not in best or d['new']<best[n][1]['new']:best[n]=(j,d,p)
 else:refused.append(dict(id=j['id'],n=n,clean=bool(clean),verified=bool(verified),base=bar[n],peer=peer[n],new=d['new']))
for n,(j,d,p)in list(best.items()):
 if not G.check(j,p)['clean']:del best[n]
rows=[];comparison=[]
for n,(j,d,p)in sorted(best.items()):
 src,lic=A.published(dict(proof=j['ancestry']))
 row=dict(n=n,held=bar[n],new=d['new'],gain=bar[n]-d['new'],source='invent_rest.py local kick and family squeeze, floatsafe, completed certified-file fq; '+src,licence=lic)
 rows.append(row);tmp=T/f'{n}.csv.tmp';tmp.write_bytes(p.read_bytes());tmp.replace(T/f'{n}.csv')
 peers=[]
 for table in S.glob('take-*-r26/take.tsv'):
  if table.parent==T:continue
  for r in A.rows(table):
   if r.get('n')==str(n):peers.append(dict(table=str(table),new=float(r['new'])))
 comparison.append(dict(n=n,id=j['id'],base=bar[n],peer_bar=peer[n],new=d['new'],gain_base=bar[n]-d['new'],gain_peer=peer[n]-d['new'],sha256=d['sha256'],ancestry=j['ancestry'],peers=peers))
q=T/'take.tsv.tmp'
with q.open('w',newline='')as h:
 w=csv.DictWriter(h,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(rows)
q.replace(T/'take.tsv')
for p in T.glob('*.csv'):
 if int(p.stem)not in best:p.unlink()
result=dict(time=C.now(),improved_n=len(best),gain=dict(against_base_bar=sum(v['gain_base']for v in comparison),beyond_other_live_r26=sum(v['gain_peer']for v in comparison)),selected=comparison,final_files_examined=ends,refused=refused,base=json.load(open(W/'base.json')))
C.atomic(W/'final-comparison.json',result)
C.state('FINAL COMPARE '+json.dumps({k:v for k,v in result.items()if k in ('time','improved_n','gain','final_files_examined')})+'; local verified immutable ends, current base and every live peer; work/final-comparison.json')
print(json.dumps(dict(time=result['time'],improved_n=len(best),gain=result['gain'],n=sorted(best))))
