#!/usr/bin/env python3
"""Carry the new 51-square infill corner to useful side fractions."""
import os,pickle,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import zone_corner as Z


def control(path):
    b=pickle.load(open(path,'rb'))[0]
    m=Z.cmod(b['c1'],b['c2'],b['lean1'],b['lean2'])
    g=Z.exact(b['P'],m,b['f'],b['y0'],b['x0'])
    assert b['count']==51 and len(b['P'])==51 and min(g[:3])>=-1e-8 and g[3]==0
    bad=np.vstack([b['P'],b['P'][0]])
    rejected=Z.exact(bad,m,b['f'],b['y0'],b['x0'])
    assert rejected[0]<-.9
    print('CONTROL infill51',b['id'],'count',len(b['P']),'gap',g,'duplicate',rejected[0],flush=True)
    return b,m


def carry(path,out,f):
    b,m=control(path)
    q=Z.as_module(b['P'],m,b['f'],b['y0'],b['x0'],b['id'],'51-square infill seed',b)
    r=Z.carry(q,f,soft=True,log=lambda s:print(s,flush=True))
    if r is None:
        pickle.dump([],open(out,'wb')); print('REFUSED carry',f,flush=True);return
    y,x,P=r[:3];g=Z.exact(P,m,f,y,x)
    assert len(P)==51 and min(g[:3])>=-1e-8 and g[3]==0
    v=dict(b,id='sc23zip51f%04d'%round(10000*f),f=f,y0=y,x0=x,P=P)
    v['loss']=Z.loss_of(m,f,51,y,x)
    pickle.dump([v],open(out,'wb'))
    print('CARRIED',v['id'],'loss',v['loss'],'lengths',y,x,'gap',g,flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control(sys.argv[2])
    else:carry(sys.argv[2],sys.argv[3],float(sys.argv[4]))
