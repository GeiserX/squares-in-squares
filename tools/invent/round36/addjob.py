"""addjob.py N PATH SEED [SEED...] : copy the start, add one 900 s invent_barretain lkick job per seed to boxE/queue.json."""
import sys,json,hashlib,shutil,math,csv,glob,pathlib,time
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r36/work');S='$SCRATCH/bounties-squares/'
sys.path.insert(0,'.');import methods_lp as mlp
n=int(sys.argv[1]);p=pathlib.Path(sys.argv[2]);seeds=[int(s) for s in sys.argv[3:]]
data=p.read_bytes();dg=hashlib.sha256(data).hexdigest();P=mlp.load(str(p),{n})[n];side=float(mlp.side(P))
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S+'round36-briefs/bar36.tsv'),delimiter='\t')}
live=bar[n]
for t in glob.glob(S+'take-*-r36/take.tsv'):
 try:
  for r in csv.DictReader(open(t),delimiter='\t'):
   if int(r['n'])==n:live=min(live,float(r['new']))
 except Exception:pass
q=json.load(open(W/'boxE/queue.json'));jobs=json.load(open(W/'jobs.json')) if (W/'jobs.json').exists() else []
for s in seeds:
 jid=f'inv{n}-{dg[:10]}-s{s}';rel=f'starts/{jid}.csv';(W/'boxE'/rel).write_bytes(data)
 j=dict(id=jid,n=n,start=rel,program='invent_barretain_budget30.py',modes='lkick',seconds=900,seed=s,bar=(live+1)*math.sqrt(n),side=side,input_sha256=dg,priority=len(q))
 q.append(j);jobs.append(dict(j,origin=str(p),added=time.strftime('%FT%TZ',time.gmtime())))
 print(jid,side,(side/math.sqrt(n)-1)-bar[n])
json.dump(q,open(W/'boxE/queue.json.tmp','w'));pathlib.Path(W/'boxE/queue.json.tmp').replace(W/'boxE/queue.json');json.dump(jobs,open(W/'jobs.json','w'),indent=0)
