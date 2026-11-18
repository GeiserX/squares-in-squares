"""A new corner gets one build after the count cap, then repeats are skipped."""
import ast,pathlib,sys,glob,json,os
ns=dict(sys=sys,glob=glob,json=json,os=os);tree=ast.parse(pathlib.Path(sys.argv[1]).read_text())
for node in tree.body:
    if isinstance(node,ast.Assign) and any(getattr(t,'id',None) in ('CAP','CLOSE') for t in node.targets):exec(compile(ast.Module([node],[]),'worker','exec'),ns)
    if isinstance(node,ast.FunctionDef) and node.name=='build':exec(compile(ast.Module([node],[]),'worker','exec'),ns)
built=[];skipped=[]
ns.update(checkpoint=lambda:None,run=lambda cmd,name,limit:built.append(name),log=lambda *a:skipped.append(a[1]) if a[0]=='SKIP floor' else None)
def row(name,corner,side=30.001):return dict(n=921,ids=[corner,'far1','far2'],stacks=[1,1],f=.8,name=name,predicted=side,bar=30.,patch='live')
ns['S']=dict(built=0,nogain={921:24},fresh={'sc27new'},build=[row('first','sc27new'),row('repeat','sc27new'),row('below','old',29.999)])
ns['build']();assert built==['first'] and not skipped
ns['build']();assert built==['first','below'] and skipped==['repeat']
print('CONTROL novel corner: first live corner built after24 failures; repeated corner skipped; below-bar recipe preserved')
