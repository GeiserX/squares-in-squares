"""Check the bounded live-import cadence without launching the worker."""
import ast,os,pathlib,sys
p=pathlib.Path(sys.argv[1]);tree=ast.parse(p.read_text());ns={'os':os}
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name=='live_due':exec(compile(ast.Module([node],[]),'worker2','exec'),ns)
cases=[(['inbox/r29-live-921-x.pkl'],0,True),(['inbox/r29-live-921-x.pkl'],1,False),(['inbox/r29-priority-reopen-x.pkl'],0,False),([],0,False)]
for paths,turn,want in cases:assert ns['live_due'](paths,turn)==want,(paths,turn,want)
print('CONTROL bounded live import: due live wins at turn0, other turns and reopened/empty queues preserve their cadence (4 cases)')
