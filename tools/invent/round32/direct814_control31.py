import pathlib,sys,ast,json,csv,hashlib
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import public_branch30 as B
S=W.parents[1];D=W/'direct814-control';D.mkdir(exist_ok=True);root=D/'owned2.csv';root.write_text('n,x,y,angle\n2,.5,.5,0\n2,1.5001,.5,0\n')
tree=ast.parse((W/'branch_controls30.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='named_fixture');exec(compile(ast.Module(body=[fn],type_ignores=[]),'fixture','exec'))
original=S/'take-harvest-r26/work/starts/814-5a4c0cdb48b0893b.csv';logical=str(S/'take-harvest-r26/814.csv')
assert hashlib.sha256(original.read_bytes()).hexdigest().startswith('5a4c0cdb')
results={}
for direct in(False,True):
 e,g=named_fixture(814,logical,direct);packing=D/'named814.csv';packing.write_bytes(original.read_bytes());d=json.load(open(e))
 for pin in d['snapshots']:
  if pin['original']==logical:pin['sha256']=hashlib.sha256(packing.read_bytes()).hexdigest()
 e.write_text(json.dumps(d))
 try:r=B.audit(e,g);accepted=r['clean'];reason=str(r.get('public_roots',[]))[:100]
 except (ValueError,AssertionError)as error:accepted=False;reason=str(error)
 results['direct'if direct else'held_only']=dict(accepted=accepted,reason=reason)
assert not results['direct']['accepted'],results
assert results['held_only']['accepted'],results
(W/'direct814-control31.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
