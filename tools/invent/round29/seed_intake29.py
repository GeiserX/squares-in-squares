"""Pin unclaimed original seed layouts exposed in the round29 handoff."""
import csv,datetime,hashlib,json,math,pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import controller28 as C
S=W.parents[1];folder=S/'take-quench-r29/work/held27';claimed={int(pathlib.Path(p).stem)for p in(S/'take-quench-r29/work/starts-seed29.txt').read_text().splitlines()};jobs=json.load(open(W/'jobs.json'));seen=set(C.load(W/'historical-fingerprints.json',[]))|set(C.load(W/'seen.json',[]));lines=(S/'handoff-r29.log').read_text().splitlines();bar,peer=C.bars();board={int(r['n']):float(r['board_L'])for r in csv.DictReader(open(S/'main-r17/gap-by-n.tsv'),delimiter='\t')};out=[];notes=[]
paths=sorted((p for p in folder.glob('*.csv')if int(p.stem)not in claimed),key=lambda p:-((bar[int(p.stem)]+1)*math.sqrt(int(p.stem))-board[int(p.stem)]))
for p in paths:
 if len(out)>=4:break
 n,L,fp,data=C.shape(p);digest=hashlib.sha256(data).hexdigest()
 if n<300:continue
 if fp in seen:notes.append(dict(n=n,skip='completed canonical geometry'));continue
 if C.claimed_input(n,digest,lines):notes.append(dict(n=n,skip='exact bytes claimed'));continue
 if any(j.get('input_sha256')==digest for j in jobs):notes.append(dict(n=n,skip='already queued'));continue
 meta=json.load(open(str(p)+'.json'));proof=C.A.audit(p,n,meta['source'],meta['licence']);notes.append(dict(n=n,source=proof))
 if not proof['ok']:continue
 evidence=C.G.freeze(p,n,proof['proof']);notes[-1]['independent']=evidence
 if not evidence['clean']:continue
 ident='o'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')+'x'+str(n)+'x'+str(len(out));start='starts/'+ident+'.csv';(W/start).write_bytes(data)
 out.append(dict(id=ident,n=n,start=start,kind='seed',seconds=900,seed=2963,fq=True,priority=-2.4,bar=(peer[n]+1)*math.sqrt(n),side=L,order=L-(peer[n]+1)*math.sqrt(n),input_sha256=digest,ancestry=proof['proof'],evidence=evidence['path'],evidence_sha256=evidence['sha256'],options=[],seed_original=True))
 C.handoff('claim: 900 s invent lkick and family squeeze seed2963 of own original held n='+str(n)+', exact start sha256 '+digest+', '+str(W/start)+'; source '+str(p)+'.json')
 C.state('QUEUE original-own-seed '+ident+' exposed by09:15Z quench note, gap to earlier board '+str((bar[n]+1)*math.sqrt(n)-board[n])+', not in completed geometry ledger; no share gate; common11:45Z')
existing=C.load(W/'extra-ready.json',[]);C.atomic(W/'extra-ready.json',existing+out);C.atomic(W/'seed-intake.json',dict(jobs=out,notes=notes));print(json.dumps(dict(queued=[j['n']for j in out],skips=notes)))
