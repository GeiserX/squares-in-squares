"""Control of the round 26 fresh-first import rule in worker.py, run without the worker.

It takes fresh_first out of worker.py by its source, then checks four cases. Two must
choose the import, and two must not. A rule that always or never imports fails here."""
import ast,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
src=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).with_name('worker.py')).read_text()
tree=ast.parse(src);ns={'os':__import__('os'),'L':{'mods':[]}}
for node in tree.body:
    if isinstance(node,ast.Assign) and any(getattr(t,'id',None)=='CLOSE' for t in node.targets):exec(compile(ast.Module([node],[]),'worker','exec'),ns)
    if isinstance(node,ast.FunctionDef) and node.name=='fresh_first':exec(compile(ast.Module([node],[]),'worker','exec'),ns)
f=ns['fresh_first']
far=[dict(predicted=31.0+.004,bar=31.0)];close=[dict(predicted=31.0+.0008,bar=31.0)]
cases=[(['inbox/r32-live-934-x.pkl'],far,True),(['inbox/r32-priority-exactf-862-9x9.pkl'],[],True),
       (['inbox/r32-live-997-y.pkl'],close,False),(['inbox/a-922.pkl'],far,False),([],far,False)]
for paths,builds,want in cases:
    got=f(paths,builds);assert got==want,(paths,builds,got)
print('CONTROL fresh_first: fresh live/priority package before a build 0.004 above the bar; build 0.0008 above the bar keeps its turn; saved a- donor and empty inbox keep the old cadence (5 cases)')
# The scoped CAP: after CAP no-gain builds of an n, a row 0.004 above the bar is skipped
# and a row 0.0008 above the bar is built.
for node in tree.body:
    if isinstance(node,ast.Assign) and any(getattr(t,'id',None)=='CAP' for t in node.targets):exec(compile(ast.Module([node],[]),'worker','exec'),ns)
    if isinstance(node,ast.FunctionDef) and node.name=='build':exec(compile(ast.Module([node],[]),'worker','exec'),ns)
built=[];skipped=[]
ns.update(sys=sys,glob=__import__('glob'),json=__import__('json'),checkpoint=lambda:None,
          run=lambda cmd,name,limit:built.append(name),log=lambda *a:skipped.append(a[1]) if a[0]=='SKIP floor' else None)
ns['S']=dict(built=0,nogain={813:ns['CAP'],997:ns['CAP']},build=[
    dict(n=813,ids=['a','b','c'],stacks=[1,1],f=.9,name='813-far',predicted=29.004,bar=29.0,patch='p'),
    dict(n=997,ids=['a','b','c'],stacks=[1,1],f=.9,name='997-close',predicted=32.0008,bar=32.0,patch='p')])
ns['H']={j['n']:{'L':j['bar']}for j in ns['S']['build']};ns['build']();ns['build']()
assert skipped==['813-far'] and built==['997-close'],(skipped,built)
print('CONTROL scoped CAP: far 813 row skipped after',ns['CAP'],'no-gain builds; close 997 row built')
# Second level: after 3 CAP no-gain builds, a close row above the bar is skipped and a
# row below the bar is built.
built.clear();skipped.clear()
ns['S']=dict(built=0,nogain={873:3*ns['CAP']},build=[
    dict(n=873,ids=['a','b','c'],stacks=[1,1],f=.9,name='873-close',predicted=30.0001,bar=30.0,patch='p'),
    dict(n=873,ids=['a','b','c'],stacks=[1,1],f=.9,name='873-below',predicted=29.9999,bar=30.0,patch='p')])
ns['H']={j['n']:{'L':j['bar']}for j in ns['S']['build']};ns['build']();ns['build']()
assert skipped==['873-close'] and built==['873-below'],(skipped,built)
print('CONTROL second CAP level: 873 row +1e-4 skipped after',3*ns['CAP'],'no-gain builds; row below the bar built')
