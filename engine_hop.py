#!/usr/bin/env python3
"""engine E3: lattice-coordinate basin hopping.

Each tilted patch of a held packing is read as a square lattice (angle, origin, occupied cells). One hop changes
lattice coordinates, which moves tens of squares at once: turn the whole patch, snap it to a perfect lattice at a
new angle, shift it, or add / remove a lattice line or cell. The uprights are then discarded and refilled by Evan
Daniel's fillfast with an overlap tolerance, and his fq quench (all squares free) relaxes the result. A hop wins
when the quenched side is below the held side and the lane's floatsafe certifies it.

  engine_hop.py N OUTDIR [--secs 600] [--seed 0] [--chain]
"""
import argparse, math, random, json, time, os, csv, sys
from engine_lib import *
from engine_patch import corners, pen_matrix, cluster
from engine_fq import quench, POLISH
import fillfast

def _off(z):
    return np.angle(np.exp(2j*np.pi*z).mean())/(2*np.pi)

def lattice(Tg):
    """rows model: squares stack on a lattice along one axis (the stacking axis), each row slides freely along the
    other. -> (theta of the row axis in deg, u row axis, v stacking axis, b0, rows {j: (a_j, [i...])}, residual rms)"""
    th0=float(np.median(Tg[:,2])); best=None
    for th in (th0,th0+90.0):
        a=math.radians(th); u=np.array([math.cos(a),math.sin(a)]); v=np.array([-u[1],u[0]])
        A=Tg[:,:2]@u; B=Tg[:,:2]@v; b0=_off(B); J=np.round(B-b0).astype(int); rb=B-b0-J
        rows={}; ra=[]
        for j in np.unique(J):
            m=J==j; aj=_off(A[m]); I=np.round(A[m]-aj).astype(int); ra.append(A[m]-aj-I); rows[int(j)]=(float(aj),sorted(I.tolist()))
        ra=np.concatenate(ra); res=float(np.sqrt((rb**2).mean()+(ra**2).mean()))
        dup=any(len(set(r[1]))<len(r[1]) for r in rows.values())
        if not dup and (best is None or res<best[-1]): best=(th,u,v,float(b0),rows,res)
    return best

def relattice(Tg,dth,dx,dy,edit,rng):
    L_=lattice(Tg)
    if L_ is None: return None
    th,u,v,b0,rows,res=L_; rows={j:(a,list(I)) for j,(a,I) in rows.items()}
    js=sorted(rows)
    if edit=='addline':
        if rng.random()<0.5:                         # a new row on top or below, same slip rule as its neighbour
            top=rng.random()<0.5; j=js[-1] if top else js[0]; a,I=rows[j]
            rows[j+(1 if top else -1)]=(a+rng.choice((0.0,0.5,rng.uniform(0,1))),list(I))
        else:                                        # one more square on every row end
            e=rng.random()<0.5
            for j in js: a,I=rows[j]; I.append(max(I)+1 if e else min(I)-1)
    elif edit=='delline':
        if rng.random()<0.5 and len(js)>1: del rows[js[-1] if rng.random()<0.5 else js[0]]
        else:
            e=rng.random()<0.5
            for j in js:
                a,I=rows[j]
                if len(I)>1: I.remove(max(I) if e else min(I))
    elif edit=='addcell':
        for _ in range(rng.randint(1,3)):
            j=rng.choice(js); a,I=rows[j]; I.append(max(I)+1 if rng.random()<0.5 else min(I)-1)
    elif edit=='delcell':
        for _ in range(rng.randint(1,3)):
            j=rng.choice(js); a,I=rows[j]
            if len(I)>1: I.remove(max(I) if rng.random()<0.5 else min(I))
    elif edit=='slip':
        j=rng.choice(js); a,I=rows[j]; rows[j]=(a+rng.gauss(0,10**rng.uniform(-2,-0.3)),I)
    c0=Tg[:,:2].mean(0); ac,bc=c0@u,c0@v-b0
    a_=math.radians(th+dth); u2=np.array([math.cos(a_),math.sin(a_)]); v2=np.array([-u2[1],u2[0]])
    out=[]
    for j,(a,I) in rows.items():
        for i in I: out.append(c0+(i+a-ac)*u2+(j-bc)*v2+np.array([dx,dy]))
    if not out: return None
    d=(th+dth)%90.0
    if d>45: d-=90
    return np.c_[np.array(out),np.full(len(out),d)]

def clip(Tnew,Told,s,tau):
    P=corners(Tnew); ok=(P.min((1,2))>=-tau)&(P.max((1,2))<=s+tau); Tnew=Tnew[ok]
    if len(Told) and len(Tnew):
        d=((Tnew[:,None,:2]-Told[None,:,:2])**2).sum(-1); bad=np.zeros(len(Tnew),bool)
        for a_,t_ in zip(*np.nonzero(d<2.0)):
            if not bad[a_] and pen_matrix(Tnew[a_:a_+1],Told[t_:t_+1])[0,0]>tau: bad[a_]=True
        Tnew=Tnew[~bad]
    return Tnew

def hop(T,groups,s,n,rng):
    big=[k for k,g in enumerate(groups) if len(g)>=6]
    if not big: return None,None
    k=rng.choice(big); g=groups[k]; rest=np.delete(T,g,axis=0)
    r=rng.random(); dth=dx=dy=0.0; edit=None
    if r<0.30: dth=rng.choice((-1,1))*10**rng.uniform(-0.7,0.6); kind='turn'
    elif r<0.45: dx,dy=rng.gauss(0,0.3),rng.gauss(0,0.3); kind='shift'
    elif r<0.60: dth=rng.gauss(0,1.0); dx,dy=rng.gauss(0,0.2),rng.gauss(0,0.2); kind='turnshift'
    else:
        edit=rng.choice(('addline','delline','addcell','delcell','slip','slip')); kind=edit
        if rng.random()<0.5: dth=rng.gauss(0,0.7)
    Tg=relattice(T[g],dth,dx,dy,edit,rng)
    if Tg is None: return None,kind
    return (rest,Tg),kind

def trial(T,groups,s,n,rng,taus=(0.03,0.08,0.15)):
    h,kind=hop(T,groups,s,n,rng)
    if h is None: return None,kind,None
    rest,Tg=h
    for tau in taus:
        Tn=clip(Tg,rest,s,tau); T2=np.r_[rest,Tn]
        R=fillfast.fill(s,T2,'greedy',tau=tau)
        if len(R)>=n: break
    else:
        return None,kind,len(R)
    X=R
    if len(R)>n:                                   # drop the uprights nearest to the moved patch
        U=np.arange(len(T2),len(R)); c=Tn[:,:2].mean(0) if len(Tn) else np.array([s/2,s/2])
        d=((R[U,:2]-c)**2).sum(1); drop=U[np.argsort(d)[:len(R)-n]]
        X=np.delete(R,drop,axis=0)
    s2,X2,dt=quench(s,X,())
    return (s2,X2),kind,len(R)

def run(n,out,secs,seed,chain,P):
    from engine_polish import certify
    rng=random.Random(seed); os.makedirs(out,exist_ok=True)
    s0,A=normalize(P[n]); cur_s,curA=s0,A; t0=time.time(); stats={}; best=s0; nq=0; wins=0; sides=[]
    while time.time()-t0<secs:
        T=curA[np.abs(curA[:,2])>5]; groups=cluster(T)
        res,kind,cnt=trial(T,groups,cur_s,n,rng)
        st=stats.setdefault(kind,[0,0,0]); st[0]+=1
        if res is None or res[0] is None: continue
        st[1]+=1; nq+=1; s2,X2=res; sides.append(s2)
        if s2<best-1e-9:
            L,fr=certify(n,X2)
            if L is not None and L<best-1e-9:
                st[2]+=1; wins+=1; best=L
                with open(os.path.join(out,'%d.csv'%n),'w',newline='') as h:
                    w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
                    for r in fr: w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
                print('WIN n=%d %s %.9f -> %.9f t=%.0fs'%(n,kind,s0,L,time.time()-t0),flush=True)
                cur_s,curA=L,X2
                continue
        if chain and s2<cur_s+0.002*rng.random(): cur_s,curA=s2,X2
    q=np.quantile(sides,[0,0.1,0.5]).tolist() if sides else []
    r=dict(n=n,s0=s0,best=best,gain=s0-best,wins=wins,quenches=nq,secs=round(time.time()-t0),moves=stats,side_q0_q10_q50=q)
    print(json.dumps(r),flush=True); return r

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('n',type=int); ap.add_argument('out'); ap.add_argument('--secs',type=float,default=600)
    ap.add_argument('--seed',type=int,default=0); ap.add_argument('--chain',action='store_true'); ap.add_argument('--sub',default=BEST)
    a=ap.parse_args(); run(a.n,a.out,a.secs,a.seed,a.chain,load(a.sub))
