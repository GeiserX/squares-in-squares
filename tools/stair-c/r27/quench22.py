"""Run the box-local fq from a certified input and record actual completion."""
import hashlib,json,math,os,subprocess,sys,time
sys.path.insert(0,'lane')
import family_step as F
p,out=sys.argv[1:3];n=int(os.path.basename(p).split('-')[0]);binary=os.path.abspath('fq')
assert os.path.isfile(binary) and os.access(binary,os.X_OK),'missing executable fq'
F.FQ=binary
receipt=dict(binary=binary,binary_sha256=hashlib.sha256(open(binary,'rb').read()).hexdigest(),input_sha256=hashlib.sha256(open(p,'rb').read()).hexdigest(),invoked=False,completed=False)
original=subprocess.run

def observed(cmd,*args,**kwargs):
    assert cmd[0]==binary,'unexpected quench executable'
    receipt['invoked']=True;receipt['command']=cmd;start=time.time()
    try:
        r=original(cmd,*args,**kwargs);receipt['returncode']=r.returncode
        receipt['stderr_tail']=r.stderr[-1000:] if isinstance(r.stderr,str) else ''
        return r
    except subprocess.TimeoutExpired:
        receipt['timeout']=True;raise
    finally:receipt['seconds']=time.time()-start

L,X=F.canon(F.load(p)[n]);receipt['start']=L
subprocess.run=observed
try:s,Y=F.fq_quench(L,X,(),timeout=240)
finally:subprocess.run=original
receipt['end']=s;receipt['completed']=receipt['invoked'] and receipt.get('returncode')==0 and s is not None and math.isfinite(s)
j=json.load(open(p[:-4]+'.json'));j['certified_file_quench']=receipt
os.makedirs(os.path.dirname(out) or '.',exist_ok=True)
with open(out[:-4]+'.json.tmp','w') as h:json.dump(j,h)
os.replace(out[:-4]+'.json.tmp',out[:-4]+'.json')
assert receipt['completed'],'fq did not complete successfully'
if s<L:X=Y
F.write_rows(out,n,X)
print(n,'actual certified-file fq',L,s,'rc',receipt.get('returncode'),'seconds',receipt.get('seconds'),'sha256',receipt['binary_sha256'],flush=True)
