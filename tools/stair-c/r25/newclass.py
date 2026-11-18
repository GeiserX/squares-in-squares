"""Build independent staircase classes by moving a core step before arm placement."""
import argparse,glob,hashlib,json,math,os,pickle,sys,time
sys.path.insert(0,'lane')
import numpy as np
import modules as M
import zone_corner as Z
import twoshort_corner as T

def stair(c,f,H,y,x,profile):
    mod=Z.cmod(c,c);t1,t2,p1,p2,W1,W2=Z.geom(mod,f)
    P=np.array([(i+.5,j+.5,0.) for i,h in enumerate(profile) for j in range(h)],float).reshape(-1,3)
    a=np.arange(c)-(c-1)/2
    walls=np.vstack([np.c_[W1/2+a*math.cos(t1),y+p1/2+a*math.sin(t1),np.full(c,t1)],np.c_[x+p2/2+a*math.sin(t2),W2/2+a*math.cos(t2),np.full(c,-t2)]])
    empty=[0,0]
    for j in range(1,40):
        for arm in (0,1):
            if empty[arm]>=2:continue
            runs=[]
            for sh in T.SHIFTS:
                if arm==0:
                    R=np.c_[W1/2+(a+sh)*math.cos(t1),y+p1/2-j*p1+(a+sh)*math.sin(t1),np.full(c,t1)]
                    R=R[R[:,0]+.5*(math.cos(t1)+math.sin(t1))<=W1+1e-9]
                else:
                    R=np.c_[x+p2/2-j*p2+(a+sh)*math.sin(t2),W2/2+(a+sh)*math.cos(t2),np.full(c,-t2)]
                    R=R[R[:,1]+.5*(math.cos(t2)+math.sin(t2))<=W2+1e-9]
                runs.append(R)
            R=T.best_run(runs,np.vstack([P,walls]))
            if len(R):P=np.vstack([P,R]);empty[arm]=0
            else:empty[arm]+=1
        if min(empty)>=2:break
    P[:,2]=np.degrees(P[:,2]);return P

def control():
    c=9;f=.86;H=8;y=11.2;x=12.3;profile=list(range(H,0,-1))
    P=stair(c,f,H,y,x,profile);Q=T.stair(c,c,f,H,y,x,walls=True)
    assert P.shape==Q.shape and np.max(np.abs(P-Q))<1e-12
    mod=Z.cmod(c,c);g=Z.exact(P,mod,f,y+.02,x+.02)
    assert min(g[:3])>=-1e-8 and g[3]==0
    bad=Z.exact(np.vstack([P,P[0]]),mod,f,y+.02,x+.02)
    assert min(bad[:3])<-.99
    print('CONTROL changed-core builder matches regular staircase exactly; count',len(P),'maxdiff',np.max(np.abs(P-Q)),'duplicate gap',min(bad[:3]),flush=True)

def main():
    control()
    n=int(sys.argv[1]);start=time.time();limit=min(float(sys.argv[2]),float(open('search-deadline').read())-start-15)
    Hbar={int(r['n']):float(r['L']) for r in __import__('csv').DictReader(open('details.csv'))}
    f=Hbar[n]-math.isqrt(n-1);c=9;mod=Z.cmod(c,c);best={}
    # Equal-area core profiles move a boundary cell. This changes the tilted
    # row contacts and therefore the final corner count class.
    for H in (7,8,9,10):
        original=list(range(H,0,-1))
        for src,dst in ((0,H-1),(H-1,0),(1,H-2),(H-2,1)):
            profile=original.copy();profile[src]-=1;profile[dst]+=1
            for y in np.arange(H+1.5,H+4.01,.35):
                for x in np.arange(max(H+1.5,c+f+.2),H+4.01,.35):
                    if time.time()-start>limit*.45:break
                    P=stair(c,f,H,float(y),float(x),profile);N=len(P);loss=Z.loss_of(mod,f,N,y,x)
                    key=N
                    if key not in best or loss<best[key][0]:best[key]=(loss,H,float(y),float(x),profile,P)
                if time.time()-start>limit*.45:break
            if time.time()-start>limit*.45:break
        if time.time()-start>limit*.45:break
    selected=sorted(best.items(),key=lambda kv:kv[1][0]);seen=set();pick=[]
    for N,row in selected:
        if N%c not in seen:seen.add(N%c);pick.append((N,row))
    print('SCAN target',n,'fraction',f,'counts',len(best),'classes',sorted(seen),'seconds',time.time()-start,flush=True)
    mods=[];lens={};base=[]
    for N,(loss,H,y,x,profile,P) in pick:
        if time.time()-start>limit:break
        g=Z.exact(P,mod,f,y+.02,x+.02)
        if min(g[:3])< -1e-8 or g[3]:continue
        r=Z.settle_zone(P,mod,f,y+.02,x+.02)
        if r is None:continue
        yy,xx,Q=r;g=Z.exact(Q,mod,f,yy+1e-7,xx+1e-7)
        if min(g[:3])< -1e-7 or g[3]:continue
        b=dict(id=f'sc25step-{n}-{N}',src='stair-c r25 newclass.py: independent staircase with equal-area core-step transfer; profile '+repr(profile),licence='our own',c1=c,c2=c,lean1=1,lean2=-1,f=f,count=N,y0=yy,x0=xx,P=Q,H=H)
        base.append(b)
        # Use the shared adoption and tabulation path without changing it.
        out=f'classes/{n}';os.makedirs(out+'/runs',exist_ok=True);os.makedirs(out+'/zones',exist_ok=True)
        pickle.dump([b],open(out+'/base.pkl','wb'));Z.cmd_adopt([out+'/base.pkl',out+'/runs'])
        Z.cmd_table([out+'/runs',out+'/zones',out+'/zones.tsv','--all','--tag',f'sc25n{n}'])
        qs=pickle.load(open(out+'/zones/corners.pkl','rb'))
        for q in qs:
            q['ours']=True
            if q['id'] not in lens:mods.append(q);lens[q['id']]=M.tabulate(q)
        print('CLASS',n,'count',N,'modclass',N%c,'loss',loss,'settled',Z.loss_of(mod,f,N,yy,xx),'states',len(mods),'seconds',time.time()-start,flush=True)
        pickle.dump(dict(mods=mods,lens=lens,origin='independent core-step transfer'),open(f'inbox/r25-priority-class-{n}.pkl.tmp','wb'));os.replace(f'inbox/r25-priority-class-{n}.pkl.tmp',f'inbox/r25-priority-class-{n}.pkl')
    print('DONE new independent classes',n,len(mods),'seconds',time.time()-start,flush=True)
if __name__=='__main__':main()
