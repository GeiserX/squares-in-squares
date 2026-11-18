#!/usr/bin/env python3
"""Rank fresh module combinations in bounded chunks, with primary targets first."""
import csv,os,pickle,sys,time,hashlib,glob,json,math
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import modules as M
from modules_round22 import CLOSED_CORNERS

class FreshLibrary(M.Library):
    def best(self, n, top=3, below=None, need=None, distinct=False, foreign=False, depth=None, above=None, accept=None):
        """The choices of modules with the smallest f for n. -> [(f, stop, corner, far 1, far 2, s1, s2)]
        need: a set of module ids; only choices that hold one of them count (the others were tried before).
        distinct: two choices that differ only by a module of the same family count once (the lower f).
        foreign: only corners cut from a layout of another n (a design this n does not hold yet).
        depth: with below, search only f in [below - depth, below] (see window); a choice that fits at the low end
        of that window comes back with the stop 'edge'. above: reject a choice whose first fit is below this f,
        before it can occupy a top slot. The default leaves every choice eligible."""
        m = math.isqrt(n - 1); res = []
        if depth is not None and below is not None: self.window(below - depth, below)
        else: self.window()
        def key(t):
            return (t[2]['kin'], t[3]['kin'], t[4]['kin'], t[5], t[6]) if distinct else id(t)
        needc = None if need is None else {e['q']['c'] for c in self.far for e in self.far[c] if e['id'] in need}
        nmask = {}
        for C in self.corners:
            if m - C['c1'] + 1 < 5 or m - C['c2'] + 1 < 5: continue
            if foreign and C['q']['n'] == n: continue
            Q = n - (m - C['c1'] + 1) * (m - C['c2'] + 1) - C['count']
            cnew = need is None or C['id'] in need
            if not cnew and C['c1'] not in needc and C['c2'] not in needc: continue   # no far zone of the list fits either arm
            # the pairs of options of the two arms that hold Q squares, as a join on the count (round 16); the same
            # candidates in the same order as the loop over arm 1 then arm 2 of rounds 1 to 15, sorted stably by f
            Fa, i1, sa, la, na = self.opt_arrays(C, 1, m); Fb, i2, sb, lb2, nb2 = self.opt_arrays(C, 2, m)
            if not len(na) or not len(nb2): continue
            def join(aa, bb):
                if not len(aa) or not len(bb):return np.zeros(0,int),np.zeros(0,int)
                o2=bb[np.argsort(nb2[bb],kind='stable')];srt=nb2[o2]
                tg=Q-na[aa];a0=np.searchsorted(srt,tg,'left');a1=np.searchsorted(srt,tg,'right');cntp=a1-a0
                pa=aa[np.repeat(np.arange(len(aa)),cntp)]
                pb=o2[np.repeat(a0-np.cumsum(cntp)+cntp,cntp)+np.arange(cntp.sum())]
                return pa,pb
            if cnew:
                P1,P2=join(np.arange(len(na)),np.arange(len(nb2)))
            else:
                for cc in (C['c1'],C['c2']):
                    if cc not in nmask:nmask[cc]=np.array([F['id'] in need for F in self.far[cc]],bool)
                anew=nmask[C['c1']][i1];bnew=nmask[C['c2']][i2]
                # Disjoint branches preserve every eligible pair exactly once.
                a,b=join(np.flatnonzero(anew),np.arange(len(nb2)))
                c,d=join(np.flatnonzero(~anew),np.flatnonzero(bnew))
                P1=np.r_[a,c];P2=np.r_[b,d]
            if not len(P1):continue
            lbp = np.maximum(la[P1], lb2[P2])
            if below is not None:
                keep = lbp < below; P1, P2, lbp = P1[keep], P2[keep], lbp[keep]
            od = np.lexsort((P2, P1, lbp)); P1, P2, lbp = P1[od], P2[od], lbp[od]
            cand = [(float(l), Fa[i1[p]], int(sa[p]), Fb[i2[q]], int(sb[q])) for l, p, q in zip(lbp, P1, P2)]
            k0 = 0
            while k0 < len(cand):                           # in blocks, so the bound of the best found so far still prunes
                if len(res) >= top: cand = [t for t in cand[k0:] if t[0] < res[top - 1][0]]; k0 = 0
                blk = cand[k0:k0 + 256]; k0 += 256
                if not blk: break
                for (lb, F1, s1, F2, s2), r in zip(blk, self.fit_many(C, blk, m)):
                    if r is not None and (above is None or r[0] >= above) and (accept is None or accept(C, r[0])):
                        res.append((r[0], r[1], C, F1, F2, s1, s2))
                res.sort(key=lambda t: t[0])
                seen = set(); keep = []
                for t in res:
                    if key(t) not in seen: seen.add(key(t)); keep.append(t)
                res = keep[:max(top, 1)]
        return res[:top]

def main():
    pool,out=sys.argv[1:3];need=set(open(pool+'/need.txt').read().split())
    held={int(r['n']):float(r['L']) for r in csv.DictReader(open('details.csv'))}
    blocked=set(CLOSED_CORNERS);bad={};good=set()
    for path in glob.glob('raw-a/*.json')+glob.glob('raw-a/*.nostart'):
     try:
      j=json.load(open(path));c=(j.get('ids') or [q['id'] for q in j.get('modules',[])])[0]
      if j.get('built') is not None:good.add(c)
      elif path.endswith('.nostart'):bad[c]=bad.get(c,0)+1
     except (ValueError,IndexError,KeyError):continue
    blocked.update(c for c,v in bad.items() if v>=2 and c not in good)
    kind=FreshLibrary if os.path.exists('FRESH_JOIN_READY') else M.Library
    lib=kind(pool,only=lambda q:M.usable(q) and q['id'] not in blocked)
    print('REFUSED corner states',sorted(blocked),flush=True)
    fs=[q['q']['f0'] for q in lib.byid.values() if q['id'] in need];mid=sorted(fs)[len(fs)//2] if fs else .84
    primary=[803,804,860,863,919,921,924,982,984,987]
    allns=list(map(int,open('ns-all.txt').read().split()));ns=sorted(primary,key=lambda n:abs(held[n]-int(n**.5)-mid))+sorted(set(allns)-set(primary),key=lambda n:abs(held[n]-int(n**.5)-mid))
    fields=['n','m','held_side','predicted_side','predicted_minus_held','stop','rank','corner','far1','far2','stacks1','stacks2','f']
    prior=list(csv.DictReader(open(out),delimiter='\t')) if os.path.exists(out) else []
    done=set(map(int,open(out+'.done').read().split())) if os.path.exists(out+'.done') else set()
    t=time.time()
    with open(out,'a') as h:
     w=csv.DictWriter(h,fieldnames=fields,delimiter='\t',lineterminator='\n')
     if not prior and not os.path.getsize(out):w.writeheader()
     for n in ns:
      if n in done:continue
      if time.time()-t>150 or time.time()>float(open('deadline').read())-30:break
      m=int((n-1)**.5)
      rows=lib.best(n,top=2,below=held[n]-m+.014,need=need,distinct=True,depth=.025,above=held[n]-m-.005)
      for rk,(f,stop,C,F1,F2,s1,s2) in enumerate(rows,1):
       w.writerow(dict(n=n,m=m,held_side=held[n],predicted_side=m+f,predicted_minus_held=m+f-held[n],stop=stop,rank=rk,corner=C['id'],far1=F1['id'],far2=F2['id'],stacks1=s1,stacks2=s2,f=f))
      h.flush();done.add(n);open(out+'.done','w').write('\n'.join(map(str,sorted(done))));print('RANK',n,len(rows),len(done),'of',len(ns),'seconds',time.time()-t,flush=True)
    if len(done)<len(ns) and time.time()<float(open('deadline').read())-120:
     tag=hashlib.sha256((pool+str(len(done))).encode()).hexdigest()[:12]
     with open('q.txt','a') as h:h.write(f'ranktail-{tag} ./ranktail23.sh {pool} {out}\n')

if __name__=='__main__':main()
