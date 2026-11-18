"""Recheck sources and exact bytes of boxE-certified result at shutdown."""
import pathlib,csv,json,hashlib
W=pathlib.Path(__file__).resolve().parent;T=W.parent
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'.')
import quench_walk as policy_walk27
state=json.load(open(W/'collect-state.json')) if (W/'collect-state.json').exists() else {};out=[]
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);p=T/f'{n}.csv';sha=hashlib.sha256(p.read_bytes()).hexdigest();match=[]
 for key,r in state.items():
  q=W/'certs'/key/'final'/f'{n}.csv'
  if r.get('status')=='published' and q.exists() and hashlib.sha256(q.read_bytes()).hexdigest()==sha:match.append(key)
 assert match,(n,'no unchanged boxE certified file')
 check=policy_walk27.check(str(p))
 from seed_rule27 import file_checks
 checks=file_checks(p,policy_walk27);check['original_seed_checks']=checks
 if any(z['excluded'] for z in checks):check['clean']=False
 from csv_rule27 import file_checks as csv_checks
 whole=csv_checks(p,policy_walk27);check['complete_csv_ancestor_checks']=whole
 if any(z['excluded'] for z in whole):check['clean']=False
 assert check['clean'],(n,check)
 out.append({'n':n,'csv_sha256':sha,'source_clean':True,'floatsafe':True,'certificate':match,'source_walk':check})
(W/'validation25.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
