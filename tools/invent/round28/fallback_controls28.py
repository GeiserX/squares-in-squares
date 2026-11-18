"""Use a failed lower source proof to check selection of a valid recorded fallback."""
import json,pathlib,sys
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r28/work');sys.path.insert(0,str(W))
import source_gate28 as G
from selection28 import first_clean
job=next(j for j in json.load(open(W/'jobs.json'))if j['id']=='q014434x982x26')
path=W/'boxE-raw'/job['id']/'final/982.csv';receipt=json.load(open(path.parents[1]/'done.json'))
evidence=json.load(open(job['evidence']));job['ancestry']=next(v['path']for v in evidence['snapshots']if v['sha256']==evidence['ancestry_sha256'])
job['graph_pin_ok']=True
bad=dict(job,id='fallback-control-invalid',ancestry=str(W/'public-classification-controls.json'))
chosen,rejected=first_clean([(bad,dict(receipt,new=receipt['new']-1e-6),path),(job,receipt,path)],G.check)
assert chosen and chosen[0]['id']==job['id']and len(rejected)==1
empty,rejected=first_clean([(bad,receipt,path)],G.check);assert empty is None and len(rejected)==1
assert G.check(job,path)['clean']
result=dict(invalid_lower_skipped=True,valid_recorded_fallback_selected=True,all_invalid_refused=True)
(W/'fallback-controls.json').write_text(json.dumps(result));print(json.dumps(result))
