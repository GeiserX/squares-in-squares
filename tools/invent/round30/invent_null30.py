"""Explore a fixed-side contact polytope with random LP objectives, then squeeze."""
import argparse,math,pathlib,sys,time
D=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(D/'lane'))
import numpy as np
import methods_lp as M
import family_step as F

def proposal(p,limit,step,angle,rng):
 original=M.linprog
 def solve(cost,*args,**kwargs):
  bounds=list(kwargs['bounds']);bounds[-1]=(0,limit)
  cost=rng.normal(size=len(cost));cost[-3:]=0
  # Limit angular preference so translation remains a useful free direction.
  if angle:cost[2*len(p):3*len(p)]*=.2
  kwargs['bounds']=bounds
  return original(cost,*args,**kwargs)
 M.linprog=solve
 try:return M.solve(p,step,angle)
 finally:M.linprog=original

def controls():
 rng=np.random.default_rng(30)
 p=np.array([[.5,.5,0.],[1.5001,.5,0.]])
 q=proposal(p,2.0001,.02,0,rng)
 assert q is not None and M.side(q)<=2.0001+1e-9 and M.min_gap(q)>-1e-9
 assert not np.allclose(q,p,atol=1e-7)
 bad=np.array([[.5,.5,0.],[.5,.5,0.]])
 assert proposal(bad,1.1,.02,0,rng) is None
 print('CONTROL fixed-side random contact LP moved a legal pair and refused the coincident pair',flush=True)

if __name__=='__main__':
 controls()
 if '--controls' in sys.argv:raise SystemExit(0)
 ap=argparse.ArgumentParser();ap.add_argument('n',type=int);ap.add_argument('start');ap.add_argument('out')
 ap.add_argument('--seconds',type=float,default=900);ap.add_argument('--seed',type=int,default=123);ap.add_argument('--bar',type=float,default=0)
 ap.add_argument('--deadline');ap.add_argument('--fq');ap.add_argument('--modes');ap.add_argument('--walk',type=float,default=1e-6)
 a=ap.parse_args();rng=np.random.default_rng(a.seed);start,p=F.canon(F.load(a.start,{a.n})[a.n]);best=start;bestp=p.copy();cur=p.copy()
 if a.fq:
  import os
  os.environ['SQ_FQ']=a.fq
 out=pathlib.Path(a.out);(out/'raw').mkdir(parents=True,exist_ok=True)
 end=time.time()+a.seconds
 if a.deadline:end=min(end,float(pathlib.Path(a.deadline).read_text())-60)
 log=(out/f'slide-{a.n}-{a.seed}.tsv').open('a')
 log.write(f'# n={a.n} random contact LP start={start:.12f} bar={a.bar:.12f}\n');log.flush()
 k=0;since=0
 while time.time()<end:
  k+=1;t=time.time();step=float(rng.choice([.003,.006,.012,.02]));angle=step*float(rng.choice([.05,.1,.2]))
  limit=min(M.side(cur),best)+a.walk
  q=proposal(cur,limit,step,angle,rng)
  if q is None:
   log.write(f'{k}\tinfeasible\t{step}\t{best:.12f}\tinf\t{time.time()-t:.1f}\t\n');log.flush();continue
  try:
   q,L,trace=F.squeeze(q,log=None,fq=bool(a.fq),apart=.05);q=M.normal(q);L=float(M.side(q))
   if M.min_gap(q)<-1e-9:L=math.inf
  except Exception as error:
   log.write(f'{k}\tfail\t{step}\t{best:.12f}\tinf\t{time.time()-t:.1f}\t{str(error)[:80]}\n');log.flush();continue
  mark='';since+=1
  if L<best-1e-9:
   best=L;bestp=q.copy();cur=q.copy();since=0;mark='BEST';F.write_rows(str(out/'raw'/f'{a.n}-{k}.csv'),a.n,q)
  elif L<best+a.walk:
   cur=q.copy();mark='walk'
  if since>=20:cur=bestp.copy();since=0
  log.write(f'{k}\tnull\t{step}\t{best:.12f}\t{L:.12f}\t{time.time()-t:.1f}\t{mark}\n');log.flush()
 log.write(f'# end best {best:.12f} tries {k}\n');log.close()
 print(f'n={a.n} start {start:.12f} best {best:.12f} tries {k}',flush=True)
