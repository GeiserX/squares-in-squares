"""Check the failed bar-probe cap and preserve the first new corner."""
import ast,glob,json,os,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
ns=dict(sys=sys,glob=glob,json=json,os=os);tree=ast.parse(pathlib.Path(sys.argv[1]).read_text())
for node in tree.body:
    if isinstance(node,ast.Assign)and any(getattr(t,'id',None)in('CAP','CLOSE')for t in node.targets):exec(compile(ast.Module([node],[]),'worker','exec'),ns)
    if isinstance(node,ast.FunctionDef)and node.name=='build':exec(compile(ast.Module([node],[]),'worker','exec'),ns)
built=[];skipped=[]
ns.update(checkpoint=lambda:None,run=lambda cmd,name,limit:built.append(name),log=lambda *a:skipped.append(a[1])if a[0]=='SKIP floor'else None)
def job(name,c,pred=28.99):return dict(n=819,ids=[c,'far1','far2'],stacks=[12,10],f=.99,name=name,predicted=pred,bar=29.,patch='live')
ns['H']={819:{'L':29.}}
ns['S']=dict(built=0,nogain={},fresh={'new'},tested_corners={(819,'failed')},nofit={(819,'failed'):4},build=[job('failed','failed'),job('new','new',28.991)])
ns['build']();assert skipped==['failed']and built==['new']
ns['S']['nofit'][(819,'new')]=4;ns['S']['build']=[job('new-repeat','new')]
ns['build']();assert skipped==['failed','new-repeat']and built==['new']
print('CONTROL nofit: four failed bar probes cap one count/corner; first fresh corner still builds; repeated corner keeps cap')
