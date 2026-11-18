"""Round 26 request: staircase corners at the exact fraction of a target, then the
round 17 step on them (one square out of each class 1 corner, then hops).

Round 25 built plain exact-f corners for 866 and 935 and gave them no deletion and
no hop pass; none of their 27 states closed a target. Round 17 found its corner by
the deletion and hops. This request runs both at the target's own f, for the arm
pair of the held layout, and hands the lowest states to the worker as a priority
package. Usage: python exactf.py N C1 C2 [SECONDS [SEED [HOP_MINUTES]]]

Round 26 (second agent): seed 26 and 4 minutes of hops gave the 860 corner that built
860 to 1.41e-4 of side above the base. A new seed and longer hops search the same class
0 corner further. A seed other than 26 gets its own tag, folder and package name."""
import argparse,csv,json,math,os,pickle,sys,time
sys.path[:0]=['lane','.']
import numpy as np
import modules as M
import zone_corner as Z
import twoshort_corner as T

def control():
    # The constructor's own exact check passes, and a duplicated square fails.
    c=9;f=.86;mod=Z.cmod(c,c);P=T.stair(c,c,f,8,11.2,12.3,walls=True)
    g=Z.exact(P,mod,f,11.2+.02,12.3+.02)
    assert min(g[:3])>=-1e-8 and g[3]==0
    bad=Z.exact(np.vstack([P,P[0]]),mod,f,11.2+.02,12.3+.02)
    assert min(bad[:3])<-.99
    print('CONTROL exactf staircase exact check passed; duplicated square rejected',flush=True)

n,c1,c2=map(int,sys.argv[1:4]);budget=float(sys.argv[4]) if len(sys.argv)>4 else 600.
seed=int(sys.argv[5]) if len(sys.argv)>5 else 26;hop=float(sys.argv[6]) if len(sys.argv)>6 else 4.
suffix='' if seed==26 else f's{seed}'
start=time.time();control()
H={int(r['n']):float(r['L']) for r in csv.DictReader(open('details.csv'))}
bar=json.load(open('bar.json')) if os.path.exists('bar.json') else {}
f=min(H[n],float(bar.get(str(n),H[n])))-math.isqrt(n-1)
end=min(start+budget,float(open('search-deadline').read())-20)
tag=f'sc26x{n}{suffix}';out=f'exactf/{n}-{c1}x{c2}{suffix}';os.makedirs(out+'/runs',exist_ok=True);os.makedirs(out+'/zones',exist_ok=True)
hs=','.join(str(h) for h in sorted({min(c1,c2)-2,min(c1,c2)-1,min(c1,c2),max(c1,c2)-1,max(c1,c2),max(c1,c2)+1}))
a=argparse.Namespace(c1=c1,c2=c2,f=f,out=out+'/base.pkl',h=hs,step=.2,per=2,top=9,walls=True,keep=0,seconds=min(150.,end-time.time()),tag=tag)
print('START exactf',n,c1,c2,'f',f,'heights',hs,'until',end,flush=True)
T.cmd_stair(a)
if not os.path.exists(a.out):print('DONE no staircase corners',n,flush=True);sys.exit()
Z.cmd_adopt([a.out,out+'/runs'])
base=pickle.load(open(a.out,'rb'))
ones=sorted((b for b in base if b['count']%c1==1),key=lambda b:b['count'])
print('BASE',[(b['count'],b['count']%c1) for b in base],'class1',[b['count'] for b in ones],flush=True)
for b in ones:
    left=end-time.time()-60
    if left<90:break
    Z.cmd_search([a.out,out+'/runs','--id',b['id'],'--moves','self,delete,hop','--down','1','--beam','2','--minutes',str(min(hop,left/60)),'--slot','40','--tail','10','--no-trade','--seed',str(seed)])
Z.cmd_table([out+'/runs',out+'/zones',out+'/zones.tsv','--all','--tag',tag])
mods=pickle.load(open(out+'/zones/corners.pkl','rb'))
best={}
for q in mods:
    k=q['count']%c1
    best.setdefault(k,[]).append(q)
keep=[]
for k,v in best.items():keep+=sorted(v,key=lambda q:q['loss0'])[:2]
keep.sort(key=lambda q:q['loss0']);lens={}
for q in keep:q['ours']=True;lens[q['id']]=M.tabulate(q)
name=f'inbox/r26-priority-exactf-{n}-{c1}x{c2}{suffix}.pkl'
pickle.dump(dict(mods=keep,lens=lens,origin='staircase at exact target f with class 1 deletion and hops'),open(name+'.tmp','wb'));os.replace(name+'.tmp',name)
print('DONE exactf',n,c1,c2,'f',f,'states',len(keep),'losses',[(q['count'],round(q['loss0'],4)) for q in keep],'seconds',time.time()-start,flush=True)
