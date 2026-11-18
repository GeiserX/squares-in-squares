"""band lane: aim the four-grid band model at the puzzles with k <= 8 at m >= 20 where we trail the board.

  band_scan.py OUT.tsv [--jobs 3] [--steps 60000] [--kmax 8] [--mmin 20]

For every such n it reads the main angle and the upright cells off the layout we hold (free cells on the four grids), then
  1. counts the model at the held side (does the model hold this layout at all?),
  2. anneals the cells at sides 0.0005 and 0.003 below ours, with the held angle and with the angle turned by
     +-0.5 and +-1.5 degrees. A count of n there is a smaller side than ours; it is written out for certification.
"""
import sys, os, csv, math, argparse, time
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from band_ctl import held, clusters, fam_of
from band_model import Cells, cells_from_uprights
HERE=os.path.dirname(os.path.abspath(__file__))
def job(arg):
    n,steps,out=arg; t0=time.time()
    L0,up,til=held(n)
    if not til: return n,L0,None,None,[],time.time()-t0
    cl=clusters(til,1); best=None
    for turn in (0,1):
        f=fam_of(cl[0][0],cl[0][1],turn)
        for da in np.arange(0,1,0.05):
            C=Cells(L0+1e-9,f['phi'],(f['a0']+da)%1.0); C.load(cells_from_uprights(C,up)); c=C.count()
            if best is None or c>best[0]: best=(c,f['phi'],(f['a0']+da)%1.0)
    c0,phi,a0=best; res=[]
    for dl in (-0.0005,-0.003):
        for dphi in (0.0,0.5,-0.5,1.5,-1.5):
            top=0
            for seed in range(2):
                C=Cells(L0+dl,phi+dphi,a0); C.load(cells_from_uprights(C,up)); c=C.anneal(steps,T0=0.25,seed=seed,stop_at=n); top=max(top,c)
                if c>=n:
                    sq=C.squares()
                    with open(os.path.join(out,'hit-%d-%g-%g.txt'%(n,dl,dphi)),'w') as h:
                        h.write('%d %r\n'%(len(sq),L0+dl))
                        for x,y,t in sq: h.write('%r %r %r\n'%(x,y,math.degrees(t)))
                    break
            res.append((dl,dphi,top))
    return n,L0,round(cl[0][0],3),c0,res,time.time()-t0
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--steps',type=int,default=60000)
    ap.add_argument('--kmax',type=int,default=8); ap.add_argument('--mmin',type=int,default=20); ap.add_argument('--targets',default=os.path.join(HERE,'tools','targets-2026-11-09.tsv'))
    a=ap.parse_args(); os.makedirs(a.out+'.d',exist_ok=True)
    ns=[]
    for r in csv.DictReader(open(a.targets),delimiter='\t'):
        n=int(r['n']); m=int(float(r['ours_L'])+1e-9); k=n-m*m
        if m>=a.mmin and 0<k<=a.kmax and float(r['ours_L'])-float(r['target_L'])>1e-9: ns.append(n)
    from multiprocessing import Pool
    with Pool(a.jobs) as pool, open(a.out,'w') as h:
        h.write('n\tours_L\tangle\theld_count\tbest_at_-0.0005\tbest_at_-0.003\thit\tsecs\n')
        for n,L0,phi,c0,res,dt in pool.imap_unordered(job,[(n,a.steps,a.out+'.d') for n in ns]):
            b1=max([c for dl,dp,c in res if dl==-0.0005],default='')
            b2=max([c for dl,dp,c in res if dl==-0.003],default='')
            hit=any(c>=n for dl,dp,c in res)
            h.write('%d\t%r\t%s\t%s\t%s\t%s\t%d\t%.0f\n'%(n,L0,phi,c0,b1,b2,hit,dt)); h.flush()
            print(n,L0,phi,'held count',c0,'of',n,'| best below ours',b1,b2,'HIT' if hit else '','%.0fs'%dt,flush=True)
