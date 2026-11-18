"""Check original-source classification and immutable graph binding on recorded inputs."""
import json,pathlib,sys
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r28/work')
sys.path.insert(0,str(W))
import source_gate28 as G
owned=dict(root='r',nodes={'r':dict(source='Samanyu-dev/squares_in_squares',licence='own construction')})
public=dict(root='r',nodes={'r':dict(source='other/public-file',licence='CC0')})
assert not G.public_first('/x/take-harvest-r28/503.csv',owned)
assert G.public_first('/x/take-harvest-r28/503.csv',public)
assert G.banned('prvsiyan/squares-verified-best-of-1105 CC BY-SA 4.0')
job=next(j for j in json.load(open(W/'jobs.json'))if j['id']=='q014434x982x26')
path=W/'boxE-raw'/job['id']/'final/982.csv'
evidence=json.load(open(job['evidence']))
job['ancestry']=next(v['path']for v in evidence['snapshots']if v['sha256']==evidence['ancestry_sha256'])
job['graph_pin_ok']=True
positive=G.check(job,path);assert positive['clean'],positive
bad=dict(job,ancestry=str(W/'public-classification-controls.json'))
negative=G.check(bad,path)
assert not negative['clean']and 'source graph differs from frozen evidence'in negative['hits']
assert G.check(job,path)['clean']
result=dict(owned_original_source_exempt=True,fetched_public_still_share_gated=True,actual_forbidden_source_refused=True,frozen_graph_accepted=True,changed_graph_refused=True)
(W/'source-binding-controls.json').write_text(json.dumps(result));print(json.dumps(result))
