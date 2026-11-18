#!/usr/bin/env python3
"""Replace whole n in a float-safe submission with certified per-n files (n,square_id,x,y,angle as floatsafe wrote
them). The rows of every other n are copied as text, unchanged.   engine_assemble.py BASE.csv OUT.csv DIR [DIR...]"""
import csv, sys, os, glob
base,out,dirs=sys.argv[1],sys.argv[2],sys.argv[3:]
rep={}
for d in dirs:
    for f in glob.glob(os.path.join(d,'*.csv')):
        rows=list(csv.DictReader(open(f))); n=int(rows[0]['n']); assert len(rows)==n and all(int(r['n'])==n for r in rows)
        rep[n]=rows
P={}
for r in csv.DictReader(open(base)): P.setdefault(int(r['n']),[]).append(r)
with open(out,'w',newline='') as h:
    w=csv.writer(h); w.writerow(['id','n','square_id','x','y','angle']); i=0
    for n in range(1,1001):
        for r in sorted(rep.get(n,P[n]),key=lambda r:int(r['square_id'])):
            w.writerow([i,n,r['square_id'],r['x'],r['y'],r['angle']]); i+=1
print('replaced',len(rep),'n:',sorted(rep))
