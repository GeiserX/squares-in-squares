import argparse,csv,glob,json,math,os,pathlib,sys,time
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r23'
sys.path.insert(0,'.');import floatsafe
ap=argparse.ArgumentParser();ap.add_argument('stage');ap.add_argument('--exclude',default='');ap.add_argument('--out',default=str(T));a=ap.parse_args();out=pathlib.Path(a.out);out.mkdir(exist_ok=True)
held={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round21-1113a/details.csv'))};bar=dict(held);who={}
for p in sorted(list(B.glob('take-*-r22/take.tsv'))+list(B.glob('take-*-r23/take.tsv'))):
 if p.parent==T or p.parent.name==a.exclude:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);s=float(r['new'])
  except:continue
  if s<bar[n]:bar[n]=s;who[n]=p.parent.name
cur={}
if (out/'take.tsv').exists():cur={int(r['n']):r for r in csv.DictReader(open(out/'take.tsv'),delimiter='\t')}
for p in sorted(pathlib.Path(a.stage).glob('*.csv')):
 n=int(p.stem.split('-')[0]); rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
 if len(rows)!=n:print('DROP count',n,len(rows));continue
 _,fr,s,e=floatsafe.work((n,rows))
 if fr is None or s>=held[n]-1e-10 or s>=bar[n]-1e-10:
  print('DROP',n,s,'bar',bar[n],who.get(n),'reason',e);continue
 if n in cur and s>=float(cur[n]['new']):continue
 meta=json.load(open(p.with_suffix('.json')));temp=out/(str(n)+'.csv.tmp')
 with open(temp,'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(fr)
 temp.replace(out/(str(n)+'.csv'))
 cur[n]=dict(n=n,held=held[n],new=s,gain=held[n]-s,source=meta['source'],licence=meta['licence'])
 print('KEEP',n,'gain21',held[n]-s,'gain_others',bar[n]-s)
 if out==T:
  with open(B/'handoff-r23.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: certified '+str(n)+' by lkick chain then fq; '+str(T/(str(n)+'.csv'))+'\n')
with open(out/'take.tsv.tmp','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(cur[n] for n in sorted(cur))
(out/'take.tsv.tmp').replace(out/'take.tsv')
print('rows',len(cur),'gain21',sum(held[n]-float(r['new']) for n,r in cur.items()),'gain_others',sum(max(0,bar[n]-float(r['new'])) for n,r in cur.items()))
