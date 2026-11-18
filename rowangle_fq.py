#!/usr/bin/env python3
"""rowangle: Evan Daniel's fq with flags the engine sweep did not use, on held packings. Each flag set runs from the
current best state of that n; a smaller side counts only after floatsafe + the official metric certify it.

  rowangle_fq.py OUTDIR [--ns a,b | --trail] [--jobs 3] [--sets name,name] [--seeds 3] [--pilot]
--pilot: every flag set runs from the held packing (not chained) and nothing is certified; the table of raw sides
says which sets are worth a sweep.
"""
import argparse, csv, json, math, os, sys, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *
from engine_fq import quench, POLISH
NOALM=['--no-alm','--loosen','1.0']
SETS={
 'default':[()],
 'deep':[POLISH],
 'loose005':[['--loosen','1.005']],
 'loose05':[['--loosen','1.05']],
 'sqp':[NOALM+['--sqp','--pit','600','--flip-top','64']],
 'finish':[NOALM+['--finish','--pit','600','--flip-top','64']],
 'flip256':[NOALM+['--flip-top','256','--pit','1500','--stag-w','60']],
 'kick1e-4':[NOALM+['--kick','1e-4','--seed','%d','--flip-top','64','--pit','600']],
 'kick1e-3':[NOALM+['--kick','1e-3','--seed','%d','--flip-top','64','--pit','600']],
 'kick1e-2':[['--loosen','1.0','--kick','1e-2','--seed','%d']],
 'kick3e-2':[['--loosen','1.005','--kick','3e-2','--seed','%d']],
 'shrink':[['--loosen','1.0','--shrink','--hops','20','--seed','%d']],
}
def runs(name,seeds):
    for fl in SETS[name]:
        if '%d' in fl:
            for k in range(1,seeds+1): yield '%s#%d'%(name,k),[str(k) if f=='%d' else f for f in fl]
        else: yield name,list(fl)
def job(a):
    n,sq,out,sets,seeds,pilot=a
    s0,A=normalize(sq); cur=s0; X=A; best=None; log=[]
    for name in sets:
        for tag,fl in runs(name,seeds):
            s2,X2,dt=quench(cur,X,fl,timeout=900)
            log.append((tag,None if s2 is None else s2-s0,round(dt,1)))
            if pilot or s2 is None or s2>=cur-3e-9: continue
            from engine_polish import certify
            L,fr=certify(n,X2)
            if L is not None and L<cur-1e-10: cur,X,best=L,X2,(fr,tag)
    if best is not None and cur<s0-1e-9:
        with open(os.path.join(out,'%d.csv'%n),'w',newline='') as h:
            w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
            for r in best[0]: w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
        return n,s0,cur,best[1],log
    return n,s0,None,None,log
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--ns'); ap.add_argument('--trail',action='store_true'); ap.add_argument('--jobs',type=int,default=3)
    ap.add_argument('--sets',default=','.join(SETS)); ap.add_argument('--seeds',type=int,default=3); ap.add_argument('--pilot',action='store_true'); ap.add_argument('--sub',default=BEST)
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True); P=load(a.sub); sets=a.sets.split(',')
    if a.ns: ns=[int(x) for x in a.ns.split(',')]
    elif a.trail: ns=[int(r['n']) for r in csv.DictReader(open(os.path.join(LANE,'tools/targets-2026-11-09.tsv')),delimiter='\t') if int(r['short'])>0]
    else: ns=sorted(P)
    from multiprocessing import Pool
    tot=0.0; wins=0; t0=time.time()
    with Pool(a.jobs) as pool, open(os.path.join(a.out,'fq.tsv'),'a') as h, open(os.path.join(a.out,'fq-log.jsonl'),'a') as hl:
        for n,s0,s1,tag,log in pool.imap_unordered(job,[(n,P[n],a.out,sets,a.seeds,a.pilot) for n in ns]):
            hl.write(json.dumps(dict(n=n,s0=s0,log=log))+'\n'); hl.flush()
            if s1 is not None:
                g=(s0-s1)/math.sqrt(n); tot+=g; wins+=1
                h.write('%d\t%r\t%r\t%.3e\t%s\n'%(n,s0,s1,g,tag)); h.flush()
                print('WIN n=%d %.9f -> %.9f (%s) gain %.3e (total %.3e, %d wins, %.0fs)'%(n,s0,s1,tag,g,tot,wins,time.time()-t0),flush=True)
    print(json.dumps(dict(n_tried=len(ns),wins=wins,total_gain=tot,secs=round(time.time()-t0))))
