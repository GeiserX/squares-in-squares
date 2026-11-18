"""Resolve a removed invent output from its exact frozen job and receipt."""
import json,pathlib,re
S=pathlib.Path('$SCRATCH/bounties-squares');_jobs={}

def metadata(p,n):
 p=str(p);m=re.fullmatch(re.escape(str(S))+r'/take-invent-r(2[3-7])/near/(\d+)-([a-z0-9]+)\.csv',p)
 if not m:return '','',''
 rnd=int(m[1]);w=S/f'take-invent-r{rnd}/work'
 if rnd not in _jobs:
  try:_jobs[rnd]={j['id']:j for j in json.load(open(w/'jobs.json'))}
  except (OSError,ValueError):_jobs[rnd]={}
 j=_jobs[rnd].get(m[3]);
 if not j or int(m[2])!=j['n']:return '','',''
 try:
  proof=pathlib.Path(j['ancestry']);d=json.load(open(proof));root=d['nodes'][d['root']]
  receipt=json.load(open(w/'boxE-raw'/j['id']/'done.json'))
  final=w/'boxE-raw'/j['id']/'final'/f'{j["n"]}.csv'
  import hashlib
  if not receipt.get('quench_from_certified')or hashlib.sha256(final.read_bytes()).hexdigest()!=receipt['sha256']:return '','',''
 except (OSError,ValueError,KeyError):return '','',''
 return 'invent_rest.py completed local kick and fq; '+root['source'],root['licence'],str(proof)
