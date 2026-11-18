import argparse,csv,json,math,pathlib,sys,time,fcntl,hashlib
csv.field_size_limit(16000000)
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r24';W=T/'work'
sys.path.insert(0,'.');sys.path.insert(0,str(W));import floatsafe
from bar24 import bars,policy,label,reference,FP
ap=argparse.ArgumentParser();ap.add_argument('stage');ap.add_argument('--paths',nargs='*');ap.add_argument('--exclude',default='');ap.add_argument('--out',default=str(T));a=ap.parse_args();out=pathlib.Path(a.out);out.mkdir(exist_ok=True)
(W/'locks').mkdir(exist_ok=True);take_lock=open(W/'locks'/('certify-'+hashlib.sha256(str(out).encode()).hexdigest()[:16]+'.lock'),'a');fcntl.flock(take_lock,fcntl.LOCK_EX)
held,held22,sam_bar,free_bar=bars(T)
cur={int(r['n']):r for r in csv.DictReader(open(out/'take.tsv'),delimiter='\t')} if (out/'take.tsv').exists() else {}
paths=sorted(map(pathlib.Path,a.paths)) if a.paths is not None else sorted(pathlib.Path(a.stage).glob('*.csv'))
for p in paths:
 meta=json.load(open(p.with_suffix('.json')))
 if not meta.get('ancestry_checked'):print('DROP unproved ancestry',p);continue
 pol=policy(meta['source'],meta['licence'])
 if pol['status']=='unknown':print('DROP unresolved Samanyu seed',p);continue
 n=int(p.stem.split('-')[0]);rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
 if len(rows)!=n:print('DROP count',n,len(rows));continue
 _,fr,s,e=floatsafe.work((n,rows));ref=reference(n,pol,held,held22);bar=free_bar[n] if pol['status']=='none' else sam_bar[n]
 if fr is None or s>=ref-1e-10 or s>=bar-1e-10:print('DROP',n,s,'bar',bar,'reason',e);continue
 if n in cur:
  oldpol=policy(cur[n]['source'],cur[n]['licence'])
  prefer_free=n in FP.RELAXED and pol['status']=='none' and oldpol['status']!='none'
  if n in FP.RELAXED and oldpol['status']=='none' and pol['status']!='none':continue
  if not prefer_free and s>=float(cur[n]['new']):continue
 temp=out/(str(n)+'.csv.tmp')
 with temp.open('w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
 temp.replace(out/(str(n)+'.csv'))
 cur[n]=dict(n=n,held=ref,new=s,gain=ref-s,source=meta['source'],licence=label(meta['source'],meta['licence']))
 print('KEEP',n,'gain23a',held[n]-s,'gain_policy',ref-s,'gain_others',bar-s)
 if out==T:
  with (B/'handoff-r24.log').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: certified '+str(n)+' by raw kick then fq; '+str(T/(str(n)+'.csv'))+'\n')
with (out/'take.tsv.tmp').open('w',newline='') as f:
 cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
(out/'take.tsv.tmp').replace(out/'take.tsv')
print('rows',len(cur),'gain23a',sum(held[n]-float(r['new']) for n,r in cur.items()))
