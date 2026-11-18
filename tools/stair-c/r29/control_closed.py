"""Close one measured cross-target corner without closing its native count."""
import ast,glob,json,os,pathlib,sys,tempfile
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent));src=pathlib.Path(sys.argv[1]).read_text();ns=dict(sys=sys,glob=glob,json=json,os=os)
for node in ast.parse(src).body:
    if isinstance(node,ast.Assign)and any(getattr(t,'id',None)in('CAP','CLOSE')for t in node.targets):exec(compile(ast.Module([node],[]),'worker','exec'),ns)
    if isinstance(node,ast.FunctionDef)and node.name=='build':exec(compile(ast.Module([node],[]),'worker','exec'),ns)
built=[];skipped=[];ns.update(checkpoint=lambda:None,run=lambda cmd,name,limit:built.append(name),log=lambda *a:skipped.append(a[1])if a[0]=='SKIP floor'else None)
def job(n,name,c,bar,pred):return dict(n=n,ids=[c,'f1','f2'],stacks=[1,1],f=.99,name=name,predicted=pred,bar=bar,patch='live')
ns['H']={819:{'L':29.},997:{'L':32.}};ns['S']=dict(built=0,nogain={},fresh=set(),build=[job(819,'cross','closed',29.,28.99),job(997,'native','closed',32.,31.999),job(819,'other','other',29.,29.001)])
old=os.getcwd()
try:
    with tempfile.TemporaryDirectory()as d:
        os.chdir(d);pathlib.Path('closed-corners.json').write_text(json.dumps({'closed':{'source_n':997}}))
        ns['build']();ns['build']()
        assert skipped==['cross']and built==['native','other']
        assert len(ns['S']['deferred'])==1 and ns['S']['deferred'][0]['name']=='cross'
finally:os.chdir(old)
print('CONTROL closed corner: dry cross-target deferred; native count and other corner built; unrun recipe retained')
