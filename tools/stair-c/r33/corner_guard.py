"""Reject local corner states that escape beyond their declared cuts."""
import math
import numpy as np
import modules as M
import corner_paths as C
ORIGINAL_LEN=M.corner_len
ORIGINAL_AT=M.corner_at
INSTALLED=False

def upper(P):
    a=np.radians(P[:,2]);h=.5*(abs(np.cos(a))+abs(np.sin(a)))
    return float(np.max(P[:,0]+h)),float(np.max(P[:,1]+h))

def slab(mod,P,f,arm):
    a=mod['lean1'if arm==1 else'lean2']*M.flush_tilt(mod['c1'if arm==1 else'c2'],f)
    W=mod['c1'if arm==1 else'c2']-1+f
    t=np.radians(P[:,2])-a;h=.5*(abs(np.cos(t))+abs(np.sin(t)))/math.cos(a)
    return P[:,1]-(P[:,0]-W/2)*math.tan(a)+h if arm==1 else P[:,0]+(P[:,1]-W/2)*math.tan(a)+h

def tag(mod):
    q=dict(mod);P=q['P'];x,y=upper(P);f=q['f0'];g=dict(dx=x-q['x0'],dy=y-q['y0'])
    for arm in[1,2]:
        W=q['c1'if arm==1 else'c2']-1+f;axis=0 if arm==1 else 1
        idx=np.flatnonzero(P[:,axis]<W+.02);v=slab(q,P,f,arm)-q['y0'if arm==1 else'x0']
        g['indices'+str(arm)]=idx.tolist();g['allow'+str(arm)]=np.maximum(v[idx],0).tolist()
    q['cut_guard']=g;return q

def valid(mod,f,P,y0,x0):
    g=mod.get('cut_guard')
    if not g:return True
    x,y=upper(P)
    if x>x0+g['dx']+.5 or y>y0+g['dy']+.5:return False
    for arm in[1,2]:
        idx=g['indices'+str(arm)];allow=np.asarray(g['allow'+str(arm)])
        if len(idx)and np.max(slab(mod,P,f,arm)[idx]-(y0 if arm==1 else x0)-allow)>1e-7:return False
    return True

def corner_len(mod,f,Pm,y0,x0,cost=(1.,1.),caps=(None,None)):
    result=ORIGINAL_LEN(mod,f,Pm,y0,x0,cost,caps)
    if not mod.get('cut_guard')or result is not None and valid(mod,f,result[2],result[0],result[1]):return result
    if mod.get('turn'):
        fixed=dict(mod,turn=False);other=ORIGINAL_LEN(fixed,f,Pm,y0,x0,cost,caps)
        if other is not None and valid(mod,f,other[2],other[0],other[1]):return other
    # Retain a feasible upper bound when minimization crossed a cut.
    angles=[mod['lean1']*math.degrees(M.flush_tilt(mod['c1'],f))if mod['grp'][g[0]]==1 else mod['lean2']*math.degrees(M.flush_tilt(mod['c2'],f))for g in mod['rig']]
    Q=M.retilt(Pm,mod['rig'],angles);P,mode=M.corner_state(mod,f,Q,y0,x0)
    if all(v is None or v>=0 for v in caps)and valid(mod,f,Q,y0,x0)and M.legal(P,mode):return y0,x0,Q
    return None

def corner_at(mod,f,cap_y,cap_x):
    return C.corner_at(mod,f,cap_y,cap_x)if mod.get('cut_guard')else ORIGINAL_AT(mod,f,cap_y,cap_x)

def install():
    global INSTALLED
    if INSTALLED:return
    M.corner_len=corner_len;M.corner_at=corner_at;INSTALLED=True
