"""Give a changed physical-model corner one early build, then restore bar order."""
import ast,glob,json,os,pathlib,sys,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent));ns=dict(sys=sys,glob=glob,json=json,os=os,L={'mods':[]})
for node in ast.parse(pathlib.Path(sys.argv[1]).read_text()).body:
    if isinstance(node,ast.Assign)and any(getattr(t,'id',None)in('CAP','CLOSE')for t in node.targets):exec(compile(ast.Module([node],[]),'worker','exec'),ns)
    if isinstance(node,ast.FunctionDef)and node.name=='build':exec(compile(ast.Module([node],[]),'worker','exec'),ns)
built=[];skipped=[]
ns.update(checkpoint=lambda:None,run=lambda cmd,name,limit:built.append(name),log=lambda *a:skipped.append(a[1])if a[0]=='SKIP floor'else None)
def job(name,c,pred,patch):return dict(n=819,ids=[c,'f1','f2'],stacks=[1,1],f=.9,name=name,predicted=pred,bar=29.,patch=patch)
ns['H']={819:{'L':29.}};ns['S']=dict(built=0,nogain={819:24},fresh={'changed'},build=[job('old','old',28.999,'live'),job('changed','changed',29.004,'r30-priority-stacks-example'),job('repeat','changed',29.0041,'r30-priority-stacks-example')])
old=os.getcwd()
try:
    with tempfile.TemporaryDirectory()as d:
        os.chdir(d);ns['build']();assert built==['changed']
        ns['build']();assert built==['changed','old']
        ns['build']();assert skipped==['repeat']and len(ns['S']['deferred'])==1
        built.clear();skipped.clear()
        ns['S']=dict(built=0,nogain={},fresh={'changed'},build=[job('old','old',29.0001,'live'),job('changed','changed',29.004,'r30-priority-stacks-example'),job('repeat','changed',29.0041,'r30-priority-stacks-example')])
        ns['build']();ns['build']();ns['build']();assert built==['changed','old','repeat']and not skipped
finally:os.chdir(old)
print('CONTROL changed physical corner: one early build despite24 count failures; then live-bar order restored; repeat deferred')
