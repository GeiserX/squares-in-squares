import copy,glob,importlib.util,json
p='tools/stair-c/r24/coordinator.py'
spec=importlib.util.spec_from_file_location('coord',p);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
base=dict(n=935,modules=[dict(id='candidate935',source='round23 candidate gather/round23-2026-11-13a.csv n=935; results/round23-best-2026-11-13.tsv',licence='source table')])
assert C.manifest(base)['source']
a=copy.deepcopy(base);a['modules'][0]['source']+=' penguin069/squares-joegun-boxed-certified-union'
try:C.manifest(a);raise AssertionError('excluded ancestor accepted')
except ValueError:pass
a=copy.deepcopy(base);a['modules'][0]['source']='held: own soft-box search from the held packing'
try:C.manifest(a);raise AssertionError('unresolved ancestor accepted')
except ValueError:pass
result=dict(accepted_candidate=True,rejected_unavailable_upstream=True,rejected_unresolved_held=True)
json.dump(result,open('$SCRATCH/bounties-squares/take-stair-c-r24/work/source-control.json','w'),indent=2)
print('CONTROL source gate accepted candidate935; unavailable upstream rejected; unresolved held ancestor rejected')
