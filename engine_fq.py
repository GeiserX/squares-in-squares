import os, subprocess, time, tempfile
from engine_lib import *
FQ=os.path.join(BOX,'ext/evand/search/packer/target/release/fq')
POLISH=['--no-alm','--loosen','1.0','--flip-top','64','--pit','600']
def write_txt(path,s,X):
    with open(path,'w') as h:
        h.write('%d %r\n'%(len(X),float(s)))
        for x,y,d in X: h.write('%r %r %r\n'%(float(x),float(y),float(d)))
def read_txt(path):
    L=[l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    n=int(L[0][0]); return float(L[0][1]),np.array([[float(v) for v in q[:3]] for q in L[1:n+1]])
def quench(s,X,flags=(),timeout=600,tag=''):
    d=tempfile.mkdtemp(prefix='fq',dir=os.environ.get('SQ_TMP')); a,b=d+'/a.txt',d+'/b.txt'
    write_txt(a,s,X); t=time.time()
    try:
        r=subprocess.run([FQ,'quench','--in',a,'--out',b]+list(flags),capture_output=True,text=True,timeout=timeout)
        out=read_txt(b) if (r.returncode==0 and os.path.exists(b)) else (None,None)
    except subprocess.TimeoutExpired:
        out=(None,None)
    for f in (a,b):
        if os.path.exists(f): os.remove(f)
    os.rmdir(d)
    return out[0],out[1],time.time()-t
if __name__=='__main__':
    import sys, random
    P=load(); n=int(sys.argv[1]); s,A=normalize(P[n])
    for name,fl in (('default',()),('polish',POLISH)):
        s2,X,dt=quench(s,A,fl); print(n,name,'incumbent',repr(s),'->',s2,'%.1fs'%dt,flush=True)
    rng=np.random.default_rng(0); J=A.copy(); J[:,:2]+=rng.normal(0,0.02,(len(A),2)); J[:,2]+=rng.normal(0,0.5,len(A))
    for name,fl in (('default',()),('polish',POLISH)):
        s2,X,dt=quench(s*1.0,J,fl); print(n,name,'jittered ->',s2,'%.1fs'%dt,flush=True)
