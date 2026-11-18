"""Start from the actual owned seed, rather than a public-derived held row."""
import csv,hashlib,io,json,pathlib,sys,time
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import controller28 as C
source=W.parents[1]/'seeds/samanyu_bestfit.csv';folder=W/'own-originals';folder.mkdir(exist_ok=True);path=folder/'808.csv'
with source.open()as stream:
 reader=csv.DictReader(stream);fields=reader.fieldnames;rows=[r for r in reader if int(r['n'])==808]
assert len(rows)==808
with path.open('w',newline='')as stream:
 writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
n,L,fp,data=C.shape(path);seen=set(C.load(W/'historical-fingerprints.json',[]))|set(C.load(W/'seen.json',[]));digest=hashlib.sha256(data).hexdigest();bar,peer=C.bars();lines=(W.parents[1]/'handoff-r29.log').read_text().splitlines()
result=dict(n=n,source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),input_sha256=digest,side=L,bar=(peer[n]+1)*n**.5)
if fp in seen:result['skip']='completed canonical original-seed geometry'
elif C.claimed_input(n,digest,lines):result['skip']='claimed exact bytes'
else:
 src='original owned seed n=808 of Samanyu-dev/squares_in_squares, seeds/samanyu_bestfit.csv; exact original-seed aggregate sha256 '+result['source_sha256'];lic='our own layout (Samanyu-dev original seed, round29 override3)'
 proof=C.A.audit(path,n,src,lic);result['source_proof']=proof
 if proof['ok']:
  ev=C.G.freeze(path,n,proof['proof']);result['independent']=ev
  if ev['clean']:
   ident='v'+time.strftime('%H%M%S',time.gmtime())+'x808xown';start='starts/'+ident+'.csv';(W/start).write_bytes(data)
   j=dict(id=ident,n=n,start=start,kind='ownseed',seconds=900,seed=2963,fq=True,priority=-2.3,bar=(peer[n]+1)*n**.5,side=L,order=L-(peer[n]+1)*n**.5,input_sha256=digest,ancestry=proof['proof'],evidence=ev['path'],evidence_sha256=ev['sha256'],options=[],true_original_seed=True)
   C.atomic(W/'extra-ready.json',C.load(W/'extra-ready.json',[])+[j]);result['job']=j
   C.handoff('claim: actual owned original808 from seeds/samanyu_bestfit.csv, not the public-derived held808. Its first source is the owned Samanyu-dev seed, no share gate.900 s invent lkick+family squeeze seed2963, input sha256 '+digest+', '+str(W/start))
   C.state('QUEUE actual original808 '+ident+' from owned seed aggregate, replacing the source of the public-derived held808 that failed. New source and start geometry, absent from completed ledger. No numeric share on owned input. Common11:45Z.')
C.atomic(W/'original808-intake.json',result);print(json.dumps(result))
