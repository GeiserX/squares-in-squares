"""Re-certify completed quenches and find any winning raw file missing its quench."""
import csv,json,math,pathlib,sys,os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r23';W=T/'work';R=W/'boxE23'
sys.path.insert(0,str(W));from shape974 import load
sys.path.insert(0,'.');import floatsafe
held={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round21-1113a/details.csv'))};bar=dict(held)
for p in list(B.glob('take-*-r22/take.tsv'))+list(B.glob('take-*-r23/take.tsv')):
 if p.parent==T:continue
 for rr in csv.DictReader(open(p),delimiter='\t'):n=int(rr['n']);bar[n]=min(bar[n],float(rr['new']))
own={int(r['n']):float(r['new']) for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')};qrows=[];missed=[];bad=[];qtags=set()
for p in R.glob('q/*/meta.json'):
 j=json.load(open(p));qtags.add((j['tag'],j['seed']))
 if j.get('quench_rc')!=0:continue
 n=j['n'];src=p.parent/pathlib.Path(j['quenched_file']).name
 _,fr,score,error=floatsafe.work((n,[{k:r[k] for k in ['n','square_id','x','y','angle']} for r in csv.DictReader(open(src))]))
 record=dict(n=n,score=score,file=str(src),qualifies=fr is not None and score<bar[n]-1e-10)
 if fr is None:bad.append(dict(record,error=error))
 elif score<bar[n]-1e-10 and score<own.get(n,1e9)-1e-10:missed.append(record)
 qrows.append(record);print('QUENCH',n,'score',score,'qualifies',record['qualifies'],flush=True)
raw_missing=[];screened=0
for p in R.glob('done/*.json'):
 j=json.load(open(p))
 if 'best_file' not in j or j.get('tag','').startswith('control'):continue
 n=j['n'];screened+=1;side=j['best']
 if side>=(1+bar[n])*math.sqrt(n)-1e-10*math.sqrt(n) or (j['tag'],j['seed']) in qtags:continue
 raw_missing.append(dict(n=n,side=side,file=j['best_file'],tag=j['tag'],seed=j['seed']))
summary=dict(completed_quenches=len(qrows),invalid_quenches=bad,unpublished_qualifying=missed,raw_scans_screened=screened,winning_raw_missing_quench=raw_missing,records=qrows)
(W/'audit23.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2),flush=True)
assert not bad
