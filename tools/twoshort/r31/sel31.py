"""Round 31: pick held round 30 c rows to kick. Drop rows named by a kick line of rounds 28 to 31, rows changed in
rounds 28 to 30, rows whose side is a closed form a + b*sqrt(2) (quarter steps), rows whose last source is a plain
public file, and rows whose source names the prvsiyan 1105 file. Rank the rest by board score gap."""
import csv, re, math, json, glob, sys
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares'); R=Path('results')
L={int(r['n']):float(r['L']) for r in csv.DictReader(open(B/'gate/cand-round30-1115c/details.csv'))}
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round31-briefs/bar31.tsv'),delimiter='\t')}
gap={int(r['n']):r for r in csv.DictReader(open(B/'main-r17/gap-by-n.tsv'),delimiter='\t')}
kicked={}
for lg in ['handoff-r28.log','handoff-r29.log','handoff-r30.log','handoff-r31.log']:
  for line in open(B/lg,errors='replace'):
    if re.search(r'kick',line,re.I):
      for m in re.findall(r'\bn ?= ?(\d+)',line): kicked.setdefault(int(m),lg)
      for m in re.findall(r'held\w*/(\d+)\.csv',line): kicked.setdefault(int(m),lg)
changed=set()
for k in (28,29,30):
  for f in glob.glob(str(R/('round%d-best-*.tsv'%k))):
    for r in csv.DictReader(open(f),delimiter='\t'): changed.add(int(r['n']))
# latest source per n
src={}
tabs=sorted(glob.glob(str(R/'round*-best-*.tsv')),key=lambda f:int(re.search(r'round(\d+)-best',f)[1]))
for f in tabs:
  for r in csv.DictReader(open(f),delimiter='\t'):
    try: src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
    except: pass
S2=math.sqrt(2)
def closed(x):
  best=9
  for b4 in range(0,161):
    a=x-b4/4*S2; d=abs(a*8-round(a*8))/8; best=min(best,d)
  return best
out=[]
for n in range(30,1001):
  why=[]
  if n in kicked: why.append('kick line '+kicked[n])
  if n in changed: why.append('changed r28-30')
  c=closed(L[n])
  if c<2e-9: why.append('closed form %.1e'%c)
  s=src.get(n,('','',''))
  st=s[1]
  if 'squares-verified-best-of-1105' in st and 'own Samanyu' not in st: why.append('names prvsiyan 1105')
  if st.startswith('harvest') and 'kick' not in st: why.append('plain public source')
  g=gap.get(n); sg=float(g['score_gap']) if g else 0.0
  # current gap: board score against our bar
  if g:
    bl=float(g['board_L']); sg=bar[n]-(bl/math.sqrt(n)-1)
  out.append(dict(n=n,L=L[n],bar=bar[n],gap=sg,closed=c,src_table=s[0],why=why))
ok=[o for o in out if not o['why']]
ok.sort(key=lambda o:-o['gap'])
json.dump(dict(ok=ok,all=out),open(sys.argv[1],'w'),indent=1)
print('rows',len(out),'ok',len(ok),'kicked',len(kicked),'changed',len(changed),'closed',sum(1 for o in out if o['closed']<2e-9))
for o in ok[:40]: print(o['n'],'%.6f'%o['L'],'gap %.3e'%o['gap'],'closed %.1e'%o['closed'],o['src_table'])
