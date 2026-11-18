"""Run the box-local fq from a certified input and record actual completion."""
import hashlib,json,math,os,subprocess,sys,time
sys.path.insert(0,'lane')
import family_step as F
p,out=sys.argv[1:3];original_input=p;j=json.load(open(p[:-4]+'.json'))
if j.get('whole_kick'):
    sys.path.insert(0,'.');from kick_whole import prepare
    p,j['source_kick']=prepare(p,int(os.path.basename(p).split('-')[0]),j)
    if p!=original_input:
        with open(p[:-4]+'.json','w')as h:json.dump(j,h)
n=int(os.path.basename(p).split('-')[0]);binary=os.path.abspath('fq')
assert os.path.isfile(binary) and os.access(binary,os.X_OK),'missing executable fq'
F.FQ=binary
receipt=dict(input_file=p,initial_input_file=original_input,initial_input_sha256=hashlib.sha256(open(original_input,'rb').read()).hexdigest(),binary=binary,binary_sha256=hashlib.sha256(open(binary,'rb').read()).hexdigest(),input_sha256=hashlib.sha256(open(p,'rb').read()).hexdigest(),invoked=False,completed=False)
original=subprocess.run
receipt['calls']=[]
def observed(cmd,*args,**kwargs):
    assert cmd[0]==binary,'unexpected quench executable'
    receipt['invoked']=True;start=time.time();call=dict(command=cmd)
    try:
        r=original(cmd,*args,**kwargs);call['returncode']=r.returncode
        receipt['returncode']=r.returncode
        return r
    except subprocess.TimeoutExpired:
        call['timeout']=True;raise
    finally:
        call['seconds']=time.time()-start;receipt['calls'].append(call)
L,X=F.canon(F.load(p)[n]);receipt['start']=L;s=L;Y=X;began=time.time();successful=False
subprocess.run=observed
try:
    for rnd in range(3):
        improved=False
        for flags in ((),F.POLISH):
            remain=float(open('deadline').read())-time.time()-2
            if remain<1:break
            value,points=F.fq_quench(s,Y,flags,timeout=min(145,remain))
            successful=successful or value is not None
            if value is not None and value<s-3e-9:s,Y,improved=value,points,True
        if not improved:break
finally:subprocess.run=original
receipt['seconds']=time.time()-began;receipt['end']=s
receipt['completed']=successful and math.isfinite(s)
receipt['full_loop']=True;receipt['rounds']=rnd+1
j['certified_file_quench']=receipt
os.makedirs(os.path.dirname(out) or '.',exist_ok=True)
with open(out[:-4]+'.json.tmp','w') as h:json.dump(j,h)
os.replace(out[:-4]+'.json.tmp',out[:-4]+'.json')
assert receipt['completed'],'fq did not complete successfully'
if s<L:X=Y
F.write_rows(out,n,X)
print(n,'actual certified-file fq',L,s,'rc',receipt.get('returncode'),'seconds',receipt.get('seconds'),'sha256',receipt['binary_sha256'],flush=True)
