from pathlib import Path
import json,csv,hashlib,subprocess,fcntl,sys,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];S=W.parent.parent
key='j22a-fresh10238-551r-599-j8-10-s-1';D=W/'certs'/key;row=json.load((D/'repair29/row.json').open());proof=json.load((D/'repair29/repair-proof29.json').open());assert proof['clean']
assert (D/'out/551.csv').read_bytes()==(D/'repair29/551.csv').read_bytes()
snapshots={}
for q in [*W.glob('input-snapshots/*.csv'),*S.glob('take-k123-r28/work/input-snapshots/*.csv')]:
 snapshots.setdefault(hashlib.sha256(q.read_bytes()).hexdigest(),q)
for e in proof['edits']:
 if not e['from'].endswith('.csv'):continue
 to=Path(e['to']);data=to.read_bytes();sha=hashlib.sha256(data).hexdigest();src=Path(e['from'])
 if src.exists() and src.read_bytes()==data:continue
 # An exact frozen certificate or queue byte snapshot resolves a removed producer copy.
 if sha not in snapshots:
  candidates=list(S.glob('take-k123-r28/work/certs/*/out/551.csv'))
  found=next((q for q in candidates if hashlib.sha256(q.read_bytes()).hexdigest()==sha),None)
  assert found,e;snapshots[sha]=found
 assert snapshots[sha].read_bytes()==data,e
# Both pinned files reject a wrong checksum. Originals stay unchanged.
SHA='d02848915270cc38efe67cb1a657213913a184b1ce0de378501aee6d1614d495';LSHA='c39c34a38e0ffb48c242c17c1b47dc2874f73f2f261756046f3eb5424855b2ac'
SNAP=S/('take-k123-r28/work/input-snapshots/551-'+SHA+'.csv');LEDGER=S/('take-k123-r28/work/input-snapshots/'+LSHA+'.tsv')
def verified_bytes(p,sha):
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;return raw
for p,sha in [(SNAP,SHA),(LEDGER,LSHA)]:
 assert verified_bytes(p,sha)
 try:verified_bytes(p,'0'*64)
 except AssertionError:pass
 else:raise AssertionError('checksum negative control failed')
from terms26 import unique
meta=json.load((W/'fresh10238/sources-fresh10238.json').open());lic=unique('ours, on: '+' | '.join(meta[n]['licence'] for n in ['551','599']))
row['licence']=lic;(D/'repair29/row.json').write_text(json.dumps(row))
# Own normalized sources stop changing once referenced by a certificate.
(W/'normalized29/FROZEN').write_text('Pinned historical CSV/record graph adopted '+time.strftime('%FT%TZ',time.gmtime())+'\n')
lock=(W/'collect.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
state=json.load((W/'collect-state.json').open());assert state[key]['status']=='source-refused'
tag='cert-'+key;job=dict(kind='cert',tag=tag,**{'in':f'certs/{key}/in','out':f'certs/{key}/fq','take':f'certs/{key}/take.tsv'})
SSH=['ssh','-S','/tmp/squares-k123-r33-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r33-ssh']
subprocess.run(SSH+[f'mkdir -p $SCRATCH/squares-k123/certs/{key}/in'],check=True)
subprocess.run(SCP+[str(D/'out/551.csv'),f'boxE:scratch/squares-k123/{job["in"]}/'],check=True)
subprocess.run(SCP+[str(D/'out/take.tsv'),f'boxE:scratch/squares-k123/{job["take"]}'],check=True)
p=D/(tag+'.json');p.write_text(json.dumps(job));subprocess.run(SCP+[str(p),f'boxE:scratch/squares-k123/tasks/{tag}.json.tmp'],check=True);subprocess.run(SSH+[f'mv $SCRATCH/squares-k123/tasks/{tag}.json.tmp $SCRATCH/squares-k123/tasks/{tag}.json'],check=True)
state[key]=dict(status='quench-pending',n=551,source=row['source'],licence=lic,tag=tag,pool='fresh10238',donors=[551,599],ancestry_expanded=True,samanyu_seed_n=[],samanyu=False,baseline=str(W/'details-base25.csv'),restored_producer_proof=str(D/'repair29/repair-proof29.json'))
p=W/'collect-state.tmp';p.write_text(json.dumps(state));p.replace(W/'collect-state.json')
(W/'repair-controls29.json').write_text(json.dumps({'canonical_walk_clean':True,'exact_certificate_bytes':True,'exact_relocated_csv_bytes':True,'wrong_csv_hash_rejected':True,'wrong_ledger_hash_rejected':True,'snapshot_sha256':SHA,'ledger_sha256':LSHA},indent=2))
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA ADOPT best551 certificate after exact missing-producer reconstruction. Full canonical walk green; all relocated CSV bytes identical, wrong CSV/ledger hashes red. Source graph frozen in work/normalized29. Required certified-file fq queued in existing fourth slot '+tag+'; no numerical change, common deadline00:15Z.\n')
print('restored551 queued required certified-file quench',flush=True)
