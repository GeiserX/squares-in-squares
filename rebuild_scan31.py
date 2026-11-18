import csv, sys, math, glob, os
import numpy as np
csv.field_size_limit(1<<28)
S='$SCRATCH/bounties-squares'
bar={}
for r in csv.DictReader(open(S+'/take-rebuild-r31/work/bar31.tsv'),delimiter='\t'): bar[int(r['n'])]=float(r['bar'])
pats=sys.argv[2:] or ['take-*-r2[0-8]/*.csv','take-*-r2[0-8]/near/*.csv','take-*-r2[0-8]/near/*/*.csv','take-*-r2[0-8]/work/certs/*/final/*.csv']
files=[]
for p in pats: files+=glob.glob(S+'/'+p)
files=sorted(set(files))
out=open(sys.argv[1],'w')
MARGIN=float(os.environ.get('MARGIN','2e-5'))   # also list rows up to MARGIN (score) above the bar
for p in files:
    try:
        if os.path.getsize(p)>3_000_000: continue
        with open(p) as h:
            rd=csv.DictReader(h)
            if not rd.fieldnames or 'x' not in rd.fieldnames or 'angle' not in rd.fieldnames: continue
            rows=list(rd)
        ns=set(r.get('n') for r in rows)
        if len(ns)!=1: continue
        n=int(list(ns)[0])
        if len(rows)!=n: continue
        A=np.array([[float(r['x']),float(r['y']),float(r['angle'])] for r in rows])
        t=A[:,2]; h=0.5*(np.abs(np.cos(t))+np.abs(np.sin(t)))
        side=max((A[:,0]+h).max()-(A[:,0]-h).min(),(A[:,1]+h).max()-(A[:,1]-h).min())
        sc=side/math.sqrt(n)-1
        if sc < bar[n]+MARGIN:
            out.write('%d\t%.12f\t%.4e\t%s\n'%(n,side,bar[n]-sc,p.replace(S+'/',''))); out.flush()
    except Exception as e:
        pass
out.write('DONE\n')
