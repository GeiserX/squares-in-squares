import csv,glob,math,os,sys
S='$SCRATCH/bounties-squares'
H={int(r['n']):r for r in csv.DictReader(open(S+'/gate/cand-round21-1113a/details.csv'))}
for p in glob.glob(S+'/take-*-r2[23]/take.tsv'):
 if '/take-stair-c-r23/' in p:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  n=int(r['n']); L=(1+float(r['new']))*math.sqrt(n)
  if L<float(H[n]['L']):H[n]['L']=repr(L);H[n]['score']=r['new']
p=sys.argv[1]
with open(p+'.tmp','w') as h:
 w=csv.DictWriter(h,fieldnames=['n','L','score','min_gap']);w.writeheader();w.writerows(H.values())
os.replace(p+'.tmp',p)
