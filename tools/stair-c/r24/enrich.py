import csv,glob,json,math,os,pickle,re
S='$SCRATCH/bounties-squares';W=S+'/take-stair-c-r24/work';L='.'
H={int(r['n']):float(r['L']) for r in csv.DictReader(open(S+'/gate/cand-round23-1113a/details.csv'))}
records={}
for p in sorted(glob.glob(L+'/results/round*-best-*.tsv'),key=lambda p:int(re.search(r'round(\d+)',p)[1])):
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);side=float(r['L'])
  except (ValueError,KeyError):continue
  if abs(side-H[n])<2e-7:records[n]=(p,r)
proof=[]
for p in glob.glob(W+'/box/inbox/b-*.pkl'):
 a=pickle.load(open(p,'rb'));n=a['n']
 if n not in records:
  proof.append(dict(n=n,resolved=False));continue
 table,r=records[n]
 for q in a['mods']:
  q['src']='round23 candidate gather/round23-2026-11-13a.csv n='+str(n)+'; results/round23-best-2026-11-13.tsv; '+os.path.relpath(table,L)+': '+r['source']
  q['licence']=r['licence']
 pickle.dump(a,open(p,'wb'));proof.append(dict(n=n,resolved=True,table=table))
json.dump(proof,open(W+'/candidate-source-proof.json','w'),indent=2)
print('matched source records',sum(x['resolved'] for x in proof),'of',len(proof));print('unresolved',[x['n'] for x in proof if not x['resolved']])

# Saved merge inputs resolve the four remaining seed rows. Their side tables
# and build_seed.sh preserve the minimum-side selection rule.
for n in [304,338,461,759]:
 p=W+'/box/inbox/b-'+str(n)+'.pkl'
 if not os.path.exists(p):continue
 a=pickle.load(open(p,'rb'));root='franciscouzo/square-packing' if n==304 else 'Samanyu-dev/squares_in_squares'
 lic='MIT' if n==304 else 'no licence stated upstream (inherited seed coordinates; source credited)'
 for q in a['mods']:
  q['src']='round23 candidate gather/round23-2026-11-13a.csv n='+str(n)+'; held seed merged0 (gather/assembled-2026-11-09d-prov.tsv); '+root+'; build_seed.sh minimum-side merge; seeds/'+('couzo.tsv' if n==304 else 'samanyu_bestfit.tsv')+' n='+str(n)
  q['licence']=lic
 pickle.dump(a,open(p,'wb'))
