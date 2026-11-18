"""structure lane: rigid 45-degree blocks in a two-phase grid.

An a x b block of unit squares at 45 degrees sits where four corner-anchored grids meet. With side m + f and
A = ceil(a*sqrt2 - 2f), B = ceil(b*sqrt2 - 2f) the block changes the count by

    g(a, b, f) = a*b - ceil((A*B + A + B) / 2)

and it fits when m >= (A + B)/2 + 2. So a block only helps at f >= (a*sqrt2 - A)/2 for its own integer A.

  structure_rigid45.py check          # the formula against the exact fill on 14 cases
  structure_rigid45.py hits SLACK     # every block that would beat a held side, with m >= (A+B)/2 + SLACK, fill-checked
"""
import sys, os, csv, math, json
import numpy as np
from structure_slot import count
S2=math.sqrt(2)
def block(a,b,cx,cy):
    d1=np.array([1,1])/S2; d2=np.array([-1,1])/S2
    return [tuple(np.array([cx,cy])+(-b/2+0.5+k)*d1+(-a/2+0.5+l)*d2)+(45.0,) for k in range(b) for l in range(a)]
def best_gain(m,f,a,b):
    L=m+f; best=None
    for i in range(0,2*m+2):
        for j in range(-m,m+1):
            cx=(i+b/S2-f-j+a/S2)/2; cy=(i+b/S2+f+j-a/S2)/2
            ext=(a+b)/(2*S2)
            if cx-ext<-1e-9 or cy-ext<-1e-9 or cx+ext>L+1e-9 or cy+ext>L+1e-9: continue
            n=count(L,block(a,b,cx,cy))
            if best is None or n>best[0]: best=(n,cx,cy)
    return None if best is None else best[0]-m*m
def pred(a,b,f):
    A=math.ceil(a*S2-2*f-1e-12); B=math.ceil(b*S2-2*f-1e-12)
    return a*b-math.ceil((A*B+A+B)/2),A,B
CASES=[(8,5,5),(12,8,8),(25,17,17),(19,13,13),(22,15,15),(9,6,6),(17,5,17),(13,5,12),(14,8,8),(20,5,10)]
def check():
    for m,a,b in CASES:
        ths=sorted(set(round(((s*S2)%1)/2+h,9) for s in (a,b) for h in (0,0.5)))
        for f0 in ths:
            for f in (f0+1e-7,f0-0.004):
                if not 0<f<1: continue
                g,A,B=pred(a,b,f)
                if g<-3: continue
                got=best_gain(m,f,a,b)
                print(json.dumps({'m':m,'a':a,'b':b,'f':round(f,6),'A':A,'B':B,'pred':g,'fill':got,'ok':got==g}),flush=True)
def hits(slack,targets):
    R={int(r['n']):(float(r['ours_L']),float(r['target_L'])) for r in csv.DictReader(open(targets),delimiter='\t')}
    blocks=[]
    for a in range(1,45):
        for b in range(a,45):
            for A in range(max(0,math.ceil(a*S2-2)),math.ceil(a*S2)+1):
                fa=(a*S2-A)/2
                if not (0<=fa<1): continue
                for B in range(max(0,math.ceil(b*S2-2)),math.ceil(b*S2)+1):
                    fb=(b*S2-B)/2
                    if not (0<=fb<1): continue
                    g=a*b-math.ceil((A*B+A+B)/2)
                    if g>0: blocks.append((max(fa,fb),g,(A+B)/2,a,b,A,B))
    cand={}
    for m in range(8,32):
        for k in range(1,2*m+1):
            n=m*m+k
            if n>1000: break
            fo=R[n][0]-m
            for f,g,half,a,b,A,B in blocks:
                if g>=k and half+slack<=m and f<fo-1e-6:
                    cand.setdefault((m,a,b,round(f,9)),[]).append((n,k,fo))
    print(len(blocks),'blocks with a positive gain;',len(cand),'designs would beat a held side at slack',slack,flush=True)
    for (m,a,b,f),lst in sorted(cand.items()):
        got=best_gain(m,f+1e-7,a,b)
        wins=[(n,k) for n,k,fo in lst if got is not None and got>=k]
        print(json.dumps({'m':m,'a':a,'b':b,'f':f,'pred':pred(a,b,f+1e-7)[0],'fill':got,'wins':wins}),flush=True)
if __name__=='__main__':
    here=os.path.dirname(os.path.abspath(__file__))
    if sys.argv[1]=='check': check()
    else: hits(float(sys.argv[2]), sys.argv[3] if len(sys.argv)>3 else os.path.join(here,'tools','targets-2026-11-09.tsv'))
