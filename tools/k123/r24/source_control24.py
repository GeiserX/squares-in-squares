import json,pathlib
from provenance24 import credit,mlp,banned,W,S
p=S/'take-forensics-r24/near/791-rect.csv';A=mlp.load(str(p),{791})[791];c=credit(791,A,str(p));assert c and c['clean'] and c['licence'];print('positive forensics source control: accepted two recorded rectangle parents')
assert banned(json.dumps({'parts':{'A':{'source':['candidate.csv',801]}}}));assert banned(json.dumps({'source':json.dumps({'A':{'source':['candidate.csv',801]}})}));assert banned('take-harvest-r22/639.csv');assert banned('prvsiyan/squares-verified-best-of-1105');assert banned('n = 801');print('negative source controls: rejected banned 639, BY-SA file and held 801')
r=dict(positive=True,negative=True,source_evidence=c['evidence']);(W/'source-controls24.json').write_text(json.dumps(r,indent=2))
