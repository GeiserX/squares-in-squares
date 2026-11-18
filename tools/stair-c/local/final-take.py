import csv,glob,json,math,os,sys,datetime
S='$SCRATCH/bounties-squares';T=S+'/take-stair-c-r23';W=T+'/work';sys.path.insert(0,'.')
import floatsafe as F
H={int(r['n']):float(r['score']) for r in csv.DictReader(open(S+'/gate/cand-round21-1113a/details.csv'))};B=dict(H);who={n:'round21' for n in H}
for p in glob.glob(S+'/take-*-r2[23]/take.tsv'):
 if p==T+'/take.tsv':continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  n=int(r['n']);sc=float(r['new'])
  if sc<B[n]:B[n]=sc;who[n]=p
rows=list(csv.DictReader(open(T+'/take.tsv'),delimiter='\t'));keep=[];proof=[]
for r in rows:
 n=int(r['n']);fr=list(csv.DictReader(open(T+'/'+str(n)+'.csv')));c=F.clearance(fr);sc,why=F.check(n,fr);pr=F.via_pandas(fr);sp,wp=F.check(n,pr)
 ok=len(fr)==n and c>=F.MIN_CLEARANCE and why==wp=='ok' and abs(sc-float(r['new']))<1e-13 and sc<H[n]-1e-10 and sc<B[n]-1e-10
 proof.append(dict(n=n,rows=len(fr),score=sc,min_clearance=c,pandas_min_clearance=F.clearance(pr),metric=why,pandas_metric=wp,held_gain=H[n]-sc,bar_gain=B[n]-sc,bar_source=who[n],accepted=ok))
 if ok:keep.append(r)
 else:os.unlink(T+'/'+str(n)+'.csv')
cols=['n','held','new','gain','source','licence']
with open(T+'/take.tsv.tmp','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols,delimiter='\t');w.writeheader();w.writerows(keep)
os.replace(T+'/take.tsv.tmp',T+'/take.tsv')
result=dict(asof=datetime.datetime.now(datetime.timezone.utc).isoformat(),improved_n=len(keep),gain_against_round21=math.fsum(H[int(r['n'])]-float(r['new']) for r in keep),gain_over_r22_and_other_r23=math.fsum(B[int(r['n'])]-float(r['new']) for r in keep),proof=proof)
json.dump(result,open(W+'/final-take-check.json','w'),indent=2);print(json.dumps(result,indent=2))
