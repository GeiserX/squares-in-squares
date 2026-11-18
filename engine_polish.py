#!/usr/bin/env python3
"""engine: re-quench every held packing with Evan Daniel's fq (all squares free) and keep what the lane's
floatsafe + official metric certify as smaller. Positive control: n=498 (22.80381 -> 22.80370).

  engine_polish.py OUTDIR [--ns a,b,c | --all] [--jobs 3] [--sub SUB.csv] [--n-limit SECONDS]
"""
import argparse, csv, math, os, sys, json, time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *
from engine_fq import quench, POLISH
import floatsafe
SUB=BEST
def to_rows(n,X):
    return [{'n':str(n),'square_id':str(i),'x':repr(float(x)),'y':repr(float(y)),'angle':repr(math.radians(float(a)))} for i,(x,y,a) in enumerate(X)]
def certify(n,X):
    _,fr,score,e=floatsafe.work((n,to_rows(n,X)))
    if fr is None: return None,None
    return (score+1.0)*math.sqrt(n),fr
def job(a):
    n,sq,out,passes=a
    s0,A=normalize(sq); cur=s0; best=None; log=[]
    X=A
    for k in range(passes):
        improved=False
        for name,fl in (('default',()),('polish',POLISH)):
            s2,X2,dt=quench(cur,X,fl)
            log.append((name,s2,round(dt,1)))
            if s2 is not None and s2<cur-3e-9:
                L,fr=certify(n,X2)
                if L is not None and L<cur-1e-10:
                    cur,X,best=L,X2,fr; improved=True
        if not improved: break
    if best is not None and cur<s0-1e-9:
        with open(os.path.join(out,'%d.csv'%n),'w',newline='') as h:
            w=csv.writer(h); w.writerow(['n','square_id','x','y','angle'])
            for r in best: w.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
        return n,s0,cur,log
    return n,s0,None,log
def _child(a,conn):
    os.setpgrp()   # its own process group, so a kill on the limit also ends the fq it runs
    conn.send(job(a)); conn.close()
def run_limited(args,jobs,limit):
    """job() on each item, jobs at a time, each in its own process. An item still running after limit seconds
    (0: no limit) is killed with its fq call and yields (n,s0,None,[('limit',None,limit)]): a hung worker costs
    limit seconds, not the run. On SIGTERM or SIGINT the running items are killed and the run ends."""
    import multiprocessing as mp, signal
    ctx=mp.get_context('spawn'); todo=list(args); run={}
    def stop(*_):
        for pr,_c,_t,_a in run.values():
            try: os.killpg(pr.pid,signal.SIGKILL)
            except OSError: pass
        sys.exit(1)
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    while todo or run:
        while todo and len(run)<jobs:
            a=todo.pop(0); r,w=ctx.Pipe(False); pr=ctx.Process(target=_child,args=(a,w)); pr.start(); w.close()
            run[a[0]]=(pr,r,time.time(),a)
        time.sleep(0.5)
        for n,(pr,r,t,a) in list(run.items()):
            res=None
            if r.poll():
                try: res=r.recv()
                except EOFError: res=(n,normalize(a[1])[0],None,[('died',None,None)])
            elif not pr.is_alive():
                res=(n,normalize(a[1])[0],None,[('died',None,pr.exitcode)])
            elif limit and time.time()-t>limit:
                try: os.killpg(pr.pid,signal.SIGKILL)
                except OSError: pass
                print('LIMIT n=%d killed after %.0fs (--n-limit %g)'%(n,time.time()-t,limit),flush=True)
                res=(n,normalize(a[1])[0],None,[('limit',None,limit)])
            if res is not None:
                pr.join(5); r.close(); del run[n]; yield res
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--ns'); ap.add_argument('--all',action='store_true'); ap.add_argument('--jobs',type=int,default=3); ap.add_argument('--sub',default=SUB); ap.add_argument('--passes',type=int,default=3)
    ap.add_argument('--n-limit',type=float,default=0,help='seconds per n before its worker and fq are killed (0: none)')
    a=ap.parse_args(); os.makedirs(a.out,exist_ok=True); P=load(a.sub)
    ns=[int(x) for x in a.ns.split(',')] if a.ns else sorted(P)
    tot=0.0; wins=0; t0=time.time(); limited=[]
    with open(os.path.join(a.out,'polish.tsv'),'a') as h:
        for n,s0,s1,log in run_limited([(n,P[n],a.out,a.passes) for n in ns],a.jobs,a.n_limit):
            if log and log[-1][0] in ('limit','died'): limited.append(n)
            if s1 is not None:
                g=(s0-s1)/math.sqrt(n); tot+=g; wins+=1
                h.write('%d\t%r\t%r\t%.3e\n'%(n,s0,s1,g)); h.flush()
                print('WIN n=%d %.9f -> %.9f score gain %.3e (total %.3e, %d wins, %.0fs)'%(n,s0,s1,g,tot,wins,time.time()-t0),flush=True)
    print(json.dumps(dict(n_tried=len(ns),wins=wins,total_gain=tot,secs=round(time.time()-t0),limited=limited)))
