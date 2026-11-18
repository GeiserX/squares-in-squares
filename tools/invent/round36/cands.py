"""List fresh starts from handoff-r36 (near rows, certified near donors, certified rows) with live bar, board room and claims."""
import re,csv,math,sys,glob,os,time,hashlib
S='$SCRATCH/bounties-squares/'
sys.path.insert(0,'.')
import methods_lp as mlp
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S+'round36-briefs/bar36.tsv'),delimiter='\t')}
board={int(r['n']):float(r['board_L'])/math.sqrt(int(r['n']))-1 for r in csv.DictReader(open(S+'main-r17/gap-by-n.tsv'),delimiter='\t')}
live=dict(bar);who={}
for p in glob.glob(S+'take-*-r36/take.tsv'):
 lane=p.split('take-')[1].split('-r36')[0]
 try:
  for r in csv.DictReader(open(p),delimiter='\t'):
   n=int(r['n']);v=float(r['new'])
   if v<live[n]:live[n]=v;who[n]=lane
 except Exception:pass
L=open(S+'handoff-r36.log').read().splitlines()
claims={}
for l in L:
 if 'claim' in l.lower() and 'release' not in l.lower():
  m=re.search(r'n=(\d+)',l)
  if m:claims.setdefault(int(m[1]),[]).append(l[:20]+l[21:].split(' ->')[0])
seen={}
for l in L:
 for p in re.findall(r'($SCRATCH/bounties-squares/take-[a-z0-9-]+-r36/(?:near/)?\d+[^ ,]*\.csv)',l):
  if 'claim' in l.lower():continue
  seen[p]=l[:20]
out=[]
for p,t in seen.items():
 if not os.path.exists(p):continue
 n=int(os.path.basename(p).split('-')[0].split('.')[0])
 try:P=mlp.load(p,{n})[n];sc=mlp.side(P)/math.sqrt(n)-1
 except Exception as e:continue
 room=(bar[n]-board.get(n,bar[n]))-(sc-bar[n])
 out.append((room,n,sc-bar[n],live[n]-bar[n],who.get(n,''),t,p,hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]))
out.sort(reverse=True)
for o in out:
 cl=claims.get(o[1],[])
 print('room %.3e n=%d dsc %.3e live %.3e %s %s %s %s claims=%d last=%s'%(o[0],o[1],o[2],o[3],o[4],o[5],o[6].replace(S,''),o[7],len(cl),cl[-1] if cl else ''))
