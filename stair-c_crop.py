#!/usr/bin/env python3
"""Shorten a dense same-lean elbow by deleting one unit row and column.

The public 981 elbow has two arms of 10. A one-unit cross cut removes a
column and row from its upright core, then compresses both coordinates.
The two arms become 9 wide. Settle against the new flush stacks and grid.

  stair-c_crop.py control LIB
  stair-c_crop.py run LIB OUT.pkl F [--seconds 900]
"""
import argparse, math, os, pickle, sys, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import zone_corner as ZC


def crop(P, x, y, width=1., axes="both"):
    if width == 0:return P.copy()
    wx=width if axes in ('x','both') else 0.
    wy=width if axes in ('y','both') else 0.
    keep=(np.abs(P[:,0]-x)>=wx/2)&(np.abs(P[:,1]-y)>=wy/2)
    Q=P[keep].copy()
    Q[:,0]-=wx*(Q[:,0]>x);Q[:,1]-=wy*(Q[:,1]>y)
    return Q


def source(lib):
    q=dict(next(q for q in pickle.load(open(lib+'/library.pkl','rb'))['mods'] if q['id']=='981h.C'))
    mod=ZC.cmod(q['c1'],q['c2'],q['lean1'],q['lean2'])
    r=ZC.settle_zone(q['P'],mod,q['f0'],q['y0']+.02,q['x0']+.02)
    if r is None:raise RuntimeError('source cannot settle')
    q['y0'],q['x0'],q['P']=r
    q['stored_loss']=q['loss0'];q['loss0']=ZC.loss_of(mod,q['f0'],len(q['P']),q['y0'],q['x0'])
    return q


def control(lib):
    q=source(lib);P=q['P'];Q=crop(P,4.5,4.5,0)
    assert np.array_equal(P,Q)
    mod=ZC.cmod(q['c1'],q['c2'],q['lean1'],q['lean2'])
    loss=ZC.loss_of(mod,q['f0'],len(Q),q['y0'],q['x0'])
    print('CONTROL identity',len(Q),'loss',loss,'stored',q['loss0'],'exact',ZC.check_corner(q),flush=True)
    assert abs(loss-q['loss0'])<1e-10 and ZC.check_corner(q)[0]
    print('CONTROL source settle',q['stored_loss'],'to',q['loss0'],flush=True)
    assert q['loss0']<q['stored_loss']+.2
    A=np.array([[.5,.5,0],[1.5,.5,0],[2.5,.5,0],[.5,1.5,0],[1.5,1.5,0],[2.5,1.5,0],[.5,2.5,0],[1.5,2.5,0],[2.5,2.5,0]])
    B=crop(A,1.5,1.5);expected=np.array([[.5,.5,0],[1.5,.5,0],[.5,1.5,0],[1.5,1.5,0]])
    print('CONTROL grid 3x3 ->',len(B),'matches',np.array_equal(B,expected),flush=True)
    assert np.array_equal(B,expected)


def run(a):
    t0=time.time();q=source(a.lib);wx=int(a.axes in ('x','both'));wy=int(a.axes in ('y','both'))
    c1,c2=10-wx,10-wy;mod=ZC.cmod(c1,c2,q['lean1'],q['lean2']);B=[]
    y0,x0=q['y0']-wy,q['x0']-wx
    # Upright centres at half integers make cuts between their neighbours.
    candidates=[]
    for x in ([2.5,3.5,4.5,5.5,6.5,7.5,8.5] if wx else [0.]):
        for y in ([2.5,3.5,4.5,5.5,6.5,7.5,8.5] if wy else [0.]):
            P=crop(q['P'],x,y,axes=a.axes);loss=ZC.loss_of(mod,a.f,len(P),y0,x0)
            candidates.append((loss,x,y,P))
    candidates.sort(key=lambda r:r[0])
    print('START count',q['count'],'loss',q['loss0'],'candidates',[(round(float(r[0]),5),r[1],r[2],len(r[3])) for r in candidates],flush=True)
    for rank,(loss,x,y,P) in enumerate(candidates):
        if time.time()-t0>a.seconds:break
        r=ZC.settle_zone(P,mod,a.f,y0+.03,x0+.03)
        if r is None:print('REFUSED',rank,x,y,len(P),'predicted loss',loss,flush=True);continue
        ys,xs,Q=r;ls=ZC.loss_of(mod,a.f,len(Q),ys,xs)
        b=dict(id='sc22crop%s-%dx%d-%df%04d-%d'%(a.axes,c1,c2,len(Q),round(a.f*1e4),rank),src='stair-c_crop.py: one-unit '+a.axes+' cut of '+q['id']+' <'+q['src']+'>',
               licence=q['licence'],c1=c1,c2=c2,lean1=q['lean1'],lean2=q['lean2'],f=a.f,count=len(Q),y0=ys,x0=xs,P=Q,loss=ls,cuts=[x,y])
        B.append(b);print('SETTLE',b['id'],'cuts',x,y,'count',len(Q),'class',len(Q)%c1,'loss',loss,'to',ls,'seconds',time.time()-t0,flush=True)
        pickle.dump(B,open(a.out+'.tmp','wb'));os.replace(a.out+'.tmp',a.out)
    print('DONE',len(B),'lowest',min((b['loss'] for b in B),default=None),'seconds',time.time()-t0,flush=True)


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    c=sp.add_parser('control');c.add_argument('lib')
    r=sp.add_parser('run');r.add_argument('lib');r.add_argument('out');r.add_argument('f',type=float);r.add_argument('--seconds',type=float,default=900);r.add_argument('--axes',choices=('both','x','y'),default='both')
    a=ap.parse_args()
    if a.cmd=='control':control(a.lib)
    else:run(a)
if __name__=='__main__':main()
