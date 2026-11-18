import pathlib,json,csv,fcntl,os
from ancestry24 import expand
from provenance24 import W
T=W.parent;lock=open(W/'collect.lock','w');fcntl.flock(lock,fcntl.LOCK_EX)
take=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));state=json.load(open(W/'collect-state.json'))
for r in take:
 n=int(r['n']);pool,donors={985:('fresh10028',[923,985]),755:('defer00027',[597,755])}[n];m=json.load(open(W/pool/('sources-'+pool+'.json')));cc=[expand(m[str(nn)]) for nn in donors];assert all(c['clean'] for c in cc)
 r['source']=r['source'].split('; pinned donor ancestry:')[0]+'; pinned donor ancestry: '+json.dumps(cc,separators=(',',':'));r['licence']='ours, on: '+' | '.join(c['licence'] for c in cc)
 for s in state.values():
  if s.get('status')=='published' and s['n']==n:s['source']=r['source'];s['licence']=r['licence'];s['ancestry_expanded']=True
 print('expanded',n,'records',sum(c['expanded_records'] for c in cc),'source chars',len(r['source']),flush=True)
with open(T/'take.tsv.tmp','w',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(take)
os.replace(T/'take.tsv.tmp',T/'take.tsv');(W/'collect-state.tmp').write_text(json.dumps(state,indent=2));(W/'collect-state.tmp').replace(W/'collect-state.json')
