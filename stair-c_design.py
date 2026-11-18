#!/usr/bin/env python3
"""Interleaved tilted strips with upright infill, for the stair-c slice.

Build the two tilted strips before filling upright wall pockets. Same-lean arms
make a fan seam. Counter-lean arms meet without a protected upright staircase.
The control reconstructs a stored staircase with the shared row-placement code.
Imports the existing geometry and settle tools without changing them.

  stair-c_design.py control BASE.pkl
  stair-c_design.py scan F LEAN2 OUT.pkl [--step 0.12] [--top 24] [--seconds 1200]
"""
import argparse, math, os, pickle, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import twoshort_corner as TC
import zone_corner as ZC


def build(c1, c2, f, y0, x0, lean2=-1, order=(1, 2), seed=None, infill=True, reverse=False):
    mod = ZC.cmod(c1, c2, 1, lean2)
    t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    a1, a2 = t1, lean2 * t2
    s1 = np.arange(c1) - (c1 - 1) / 2
    s2 = np.arange(c2) - (c2 - 1) / 2
    P = np.zeros((0, 3)) if seed is None else np.array(seed, float)
    Wl = np.vstack([np.c_[W1 / 2 + s1 * math.cos(a1), y0 + p1 / 2 + s1 * math.sin(a1), np.full(c1, a1)],
                    np.c_[x0 + p2 / 2 - s2 * math.sin(a2), W2 / 2 + s2 * math.cos(a2), np.full(c2, a2)]])
    def rows(which, j):
        out = []
        for sh in TC.SHIFTS:
            if which == 1:
                C = np.c_[W1 / 2 + (s1 + sh) * math.cos(a1), y0 + p1 / 2 - j * p1 + (s1 + sh) * math.sin(a1), np.full(c1, a1)]
                C = C[C[:, 0] + .5 * (math.cos(t1) + math.sin(t1)) <= W1 + 1e-9]
            else:
                C = np.c_[x0 + p2 / 2 - j * p2 - (s2 + sh) * math.sin(a2), W2 / 2 + (s2 + sh) * math.cos(a2), np.full(c2, a2)]
                C = C[C[:, 1] + .5 * (math.cos(t2) + math.sin(t2)) <= W2 + 1e-9]
            d1 = -math.sin(a1) * (C[:, 0] - W1 / 2) + math.cos(a1) * (C[:, 1] - (y0 + p1 / 2))
            d2 = math.cos(a2) * (C[:, 0] - (x0 + p2 / 2)) + math.sin(a2) * (C[:, 1] - W2 / 2)
            C = C[(d1 <= 1e-10) & (d2 <= 1e-10)]
            out.append(C)
        return out
    if reverse:
        # Grow from the wall towards the flush stacks, instead of from the stacks.
        js = range(int(max(y0 / p1, x0 / p2)) + 5, 0, -1)
    else:
        js = range(1, 40)
    empty = {1: 0, 2: 0}
    for j in js:
        for which in order:
            if not reverse and empty[which] >= 2: continue
            R = TC.best_run(rows(which, j), np.vstack([P, Wl]))
            if len(R): P = np.vstack([P, R]); empty[which] = 0
            else: empty[which] += 1
        if not reverse and min(empty.values()) >= 2: break
    if infill:
        # Fixed unit cells at both walls fill only genuine vacancies in the fan.
        cells = np.array([(i + .5, j + .5, 0.) for i in range(int(max(W1, x0)) + 2)
                          for j in range(int(max(W2, y0)) + 2)], float)
        cells = cells[(cells[:, 0] + .5 <= W1 + 1e-9) | (cells[:, 1] + .5 <= W2 + 1e-9)]
        cells = cells[np.argsort(cells[:, 0] + cells[:, 1], kind='stable')]
        for C in cells:
            R = C.reshape(1, 3)
            if TC.gaps(R, np.vstack([P, Wl])).min() < -1e-9: continue
            # A square beyond either flush face is outside this corner.
            deg = R.copy(); deg[:, 2] = np.degrees(deg[:, 2])
            if max(ZC.face_dist(deg, mod, f, y0, x0)[0][0], ZC.face_dist(deg, mod, f, y0, x0)[1][0]) > -0.49: continue
            P = np.vstack([P, R])
    P[:, 2] = np.degrees(P[:, 2])
    return P


def control(path):
    B = pickle.load(open(path, 'rb'))
    b = next(q for q in B if 'H' in q)
    c1, c2, f, H = b['c1'], b['c2'], b['f'], b['H']
    y0, x0 = H + 2.3, max(H + 2.7, c1 + f)
    seed = [(i + .5, j + .5, 0.) for i in range(H) for j in range(H - i)]
    P = build(c1, c2, f, y0, x0, seed=seed, infill=False)
    Q = TC.stair(c1, c2, f, H, y0, x0, walls=True)
    same = P.shape == Q.shape and np.max(np.abs(P - Q)) < 1e-12
    print('CONTROL count', len(P), len(Q), 'same', same, 'maxdiff', np.max(np.abs(P-Q)) if P.shape == Q.shape else None, flush=True)
    assert same
    mod = ZC.cmod(c1, c2)
    g = ZC.exact(P, mod, f, y0 + .02, x0 + .02)
    print('CONTROL exact', g, flush=True)
    assert min(g[:3]) >= -1e-8 and g[3] == 0
    seed=[(i+.5,j+.5,0.) for i in range(8) for j in range(8)]
    R=build(9,9,.8,12.,16.,1,seed=seed)
    rg=ZC.exact(R,ZC.cmod(9,9,1,1),.8,12.02,16.02)
    print('CONTROL rectangular core',len(R),rg,flush=True)
    assert min(rg[:3])>=-1e-8 and rg[3]==0
    seed=[(i+.5,j+.5,0.) for i in range(8) for j in range(12)]
    R=build(9,9,.8,16.,14.,1,seed=seed)
    rg=ZC.exact(R,ZC.cmod(9,9,1,1),.8,16.02,14.02)
    print('CONTROL long rectangle',len(R),rg,flush=True)
    assert min(rg[:3])>=-1e-8 and rg[3]==0
    for lean in (-1, 1):
        Q = build(9, 9, .8, 10.6, 12.8, lean)
        g = ZC.exact(Q, ZC.cmod(9, 9, 1, lean), .8, 10.62, 12.82)
        print('CONTROL infill', lean, len(Q), g, flush=True)
        assert min(g[:3]) >= -1e-8 and g[3] == 0
        bad = np.vstack([Q, [9.3, 9.3, 0.]])
        gb = ZC.exact(bad, ZC.cmod(9, 9, 1, lean), .8, 10.62, 12.82)
        print('CONTROL forbidden rest cell', lean, gb, flush=True)
        assert min(gb[:3]) < -.1


def scan(a):
    t0 = time.time(); c1 = c2 = 9; mod = ZC.cmod(9, 9, 1, a.lean2)
    p = ZC.geom(mod, a.f)[2]; best = {}
    for y0 in np.arange(6.5, 14.51, a.step):
        for x0 in np.arange(8.9, 16.01, a.step):
            for order in ((1, 2), (2, 1)):
                for rev in (False, True):
                    P = build(9, 9, a.f, float(y0), float(x0), a.lean2, order, reverse=rev)
                    N = len(P); loss = ZC.loss_of(mod, a.f, N, y0, x0)
                    key = (N, order, rev)
                    if key not in best or loss < best[key][0]: best[key] = (loss, float(y0), float(x0), order, rev, N)
        print('PROGRESS',float(y0),'candidates',len(best),'seconds',time.time()-t0,flush=True)
        if time.time() - t0 > a.seconds * .45: break
    candidates = sorted(best.values()); selected = []; seen = set()
    for q in candidates:
        if q[-1] % 9 not in seen: selected.append(q); seen.add(q[-1] % 9)
    selected += [q for q in candidates if q not in selected]
    selected = selected[:a.top]
    print('SCAN f', a.f, 'lean2', a.lean2, 'candidates', len(candidates), 'seconds', time.time()-t0, 'lowest', candidates[:5], flush=True)
    B = []
    for rank, (loss, y0, x0, order, rev, N) in enumerate(selected):
        if time.time() - t0 > a.seconds: break
        P = build(9, 9, a.f, y0, x0, a.lean2, order, reverse=rev)
        r = ZC.settle_zone(P, mod, a.f, y0 + .02, x0 + .02)
        if r is None:
            print('SETTLE refused', rank, N, loss, flush=True); continue
        ys, xs, Q = r; ls = ZC.loss_of(mod, a.f, N, ys, xs)
        b = dict(id='sc22%s-%df%04d-%d' % ('fan' if a.lean2==1 else 'zip',N,round(a.f*1e4),rank), src='stair-c_design.py: tilted strips with upright infill (own construction)',
                 licence='our own', c1=9, c2=9, lean1=1, lean2=a.lean2, f=a.f, count=N, y0=ys, x0=xs, P=Q, loss=ls, order=order, reverse=rev)
        B.append(b)
        print('SETTLE', b['id'], 'count',N,'class',N%9,'loss',loss,'to',ls,'lengths',ys,xs,'seconds',time.time()-t0, flush=True)
        pickle.dump(B,open(a.out+'.tmp','wb')); os.replace(a.out+'.tmp',a.out)
    print('DONE corners',len(B),'lowest',min((b['loss'] for b in B),default=None),'seconds',time.time()-t0, flush=True)


def rectscan(a):
    t0=time.time();mod=ZC.cmod(9,9,1,1);best={}
    cores=[tuple(map(int,v.split('x'))) for v in a.rects.split(',')] if a.rects else [(8,8),(7,8),(8,7),(7,7),(6,8),(8,6),(6,7),(7,6)]
    for hx,hy in cores:
        seed=[(i+.5,j+.5,0.) for i in range(hx) for j in range(hy)]
        for y in np.arange(hy+1.5,a.ymax+.01,a.step):
            for x in np.arange(max(hx+1.5,9.),a.xmax+.01,a.step):
                for order in ((1,2),(2,1)):
                    for rev in (False,True):
                        P=build(9,9,a.f,float(y),float(x),1,order,seed=seed,reverse=rev)
                        N=len(P);loss=ZC.loss_of(mod,a.f,N,y,x);key=(N,order,rev,hx,hy)
                        if key not in best or loss<best[key][0]:best[key]=(loss,float(y),float(x),order,rev,N,hx,hy)
            if time.time()-t0>a.seconds*.65:break
        print('CORE',hx,hy,'candidates',len(best),'seconds',time.time()-t0,flush=True)
        if time.time()-t0>a.seconds*.65:break
    candidates=sorted(best.values());selected=[];seen=set()
    for q in candidates:
        if q[5]%9 not in seen:selected.append(q);seen.add(q[5]%9)
    selected += [q for q in candidates if q not in selected]
    print('RECTSCAN',len(candidates),'lowest',candidates[:5],flush=True);B=[]
    for rank,(loss,y,x,order,rev,N,hx,hy) in enumerate(selected[:a.top]):
        if time.time()-t0>a.seconds:break
        seed=[(i+.5,j+.5,0.) for i in range(hx) for j in range(hy)]
        P=build(9,9,a.f,y,x,1,order,seed=seed,reverse=rev)
        r=ZC.settle_zone(P,mod,a.f,y+.02,x+.02)
        if r is None:print('REFUSED',rank,N,hx,hy,loss,flush=True);continue
        ys,xs,Q=r;ls=ZC.loss_of(mod,a.f,N,ys,xs)
        b=dict(id='sc22rect-%df%04d-%d'%(N,round(a.f*1e4),rank),src='stair-c_design.py: equal-lean strips around a rectangular upright core (own construction)',
               licence='our own',c1=9,c2=9,lean1=1,lean2=1,f=a.f,count=N,y0=ys,x0=xs,P=Q,loss=ls,core=[hx,hy])
        B.append(b);print('SETTLE',b['id'],'core',hx,hy,'count',N,'class',N%9,'loss',loss,'to',ls,'seconds',time.time()-t0,flush=True)
        pickle.dump(B,open(a.out+'.tmp','wb'));os.replace(a.out+'.tmp',a.out)
    print('DONE rectangular cores',len(B),'lowest',min((b['loss'] for b in B),default=None),'seconds',time.time()-t0,flush=True)


def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    c=sp.add_parser('control'); c.add_argument('base')
    s=sp.add_parser('scan'); s.add_argument('f',type=float); s.add_argument('lean2',type=int,choices=(-1,1)); s.add_argument('out')
    s.add_argument('--rects',default='');s.add_argument('--ymax',type=float,default=14.5);s.add_argument('--xmax',type=float,default=16.5);s.add_argument('--core',choices=('empty','rect'),default='empty'); s.add_argument('--step',type=float,default=.12); s.add_argument('--top',type=int,default=24); s.add_argument('--seconds',type=float,default=1200)
    a=ap.parse_args()
    if a.cmd=='control':control(a.base)
    elif a.core=='rect':rectscan(a)
    else:scan(a)
if __name__=='__main__':main()
