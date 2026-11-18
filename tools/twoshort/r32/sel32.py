"""Round 32 twoshort screen: held round 31 b rows for a 150 s invent_rest lkick.
Tier 0: the 18 round 31 jobs that never ran (their held row unchanged in round 31, no other lane's kick line names them in r31 or r32).
Tier 1: held rows that no invent_rest lkick line of rounds 29 to 32 names (any lane; midm_scan and other 900 s kicks do not count,
because a 150 s invent_rest lkick moved 12% of the held rows our midm probe found dry in round 31), board score gap over 1e-9,
side not a closed form a+b*sqrt2, last source not a plain public file, source not naming the prvsiyan 1105 file. Rank by board gap.
Tier 2 (last): tier 1 rows whose side fraction another held n shares (within 3e-9) or is p/q with q <= 40 (0 finds in about 20 r31 probes)."""
import csv, re, math, json, glob, sys
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares'); R=Path('results')
L={int(r['n']):float(r['L']) for r in csv.DictReader(open(B/'gate/cand-round31-1116b/details.csv'))}
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round32-briefs/bar32.tsv'),delimiter='\t')}
gap={int(r['n']):r for r in csv.DictReader(open(B/'main-r17/gap-by-n.tsv'),delimiter='\t')}
UNRUN=[751,753,801,803,816,847,849,850,853,861,866,915,921,929,936,981,989,992]
OUT={639,691,745,858,918}
def kicklines(logs,skip_twoshort):
  k={}
  for lg in logs:
    p=B/lg
    if not p.exists(): continue
    for line in open(p,errors='replace'):
      if skip_twoshort and re.match(r'\S+ twoshort ->',line): continue
      if re.search(r'kick',line,re.I):
        for m in re.findall(r'\bn ?= ?(\d+)',line): k.setdefault(int(m),lg+': '+line[:160].strip())
        for m in re.findall(r'held\w*/(\d+)\.csv',line): k.setdefault(int(m),lg+': '+line[:160].strip())
  return k
def lklines(logs,skip_twoshort=False):
  k={}
  for lg in logs:
    p=B/lg
    if not p.exists(): continue
    for line in open(p,errors='replace'):
      if 'midm_scan' in line: continue
      if skip_twoshort and re.match(r'\S+ twoshort ->',line): continue
      if re.search(r'invent_rest|invent lkick|\blkick \(',line) or re.match(r'\S+ (backlog|invent) -> \S+ claims? ',line):
        for m in re.findall(r'\bn ?= ?(\d+)',line): k.setdefault(int(m),lg+': '+line[:160].strip())
        for m in re.findall(r'(?:held\w*|take-[\w-]+-r\d+)/(\d+)\.csv',line): k.setdefault(int(m),lg+': '+line[:160].strip())
        for m in re.findall(r'starts/(\d+)-',line): k.setdefault(int(m),lg+': '+line[:160].strip())
        for m in re.findall(r'\bn=((?:\d+,)+\d+)',line):
          for x in m.split(','): k.setdefault(int(x),lg+': '+line[:160].strip())
  return k
kicked=lklines(['handoff-r29.log','handoff-r30.log','handoff-r31.log','handoff-r32.log'])
kicked_other=lklines(['handoff-r31.log','handoff-r32.log'],True)
changed={};ch31=set()
for k in (29,30,31):
  for f in glob.glob(str(R/('round%d-best-*.tsv'%k))):
    for r in csv.DictReader(open(f),delimiter='\t'):
      changed.setdefault(int(r['n']),k)
      if k==31: ch31.add(int(r['n']))
src={}
def _tkey(f):
  b=Path(f).name;d=re.search(r'(\d{4}-\d\d-\d\d)([a-z]?)',b);r=re.search(r'round(\d+)-best',b)
  return (d[1],1 if r else 0,int(r[1]) if r else 0,d[2])
for f in sorted(glob.glob(str(R/'round*-best-*.tsv'))+glob.glob(str(R/'harvest-best-*.tsv')),key=_tkey):
  for r in csv.DictReader(open(f),delimiter='\t'):
    try: src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
    except (ValueError,TypeError): pass
S2=math.sqrt(2)
def closed(x):
  best=9
  for b4 in range(0,161):
    a=x-b4/4*S2; d=abs(a*8-round(a*8))/8; best=min(best,d)
  return best
frac={n:L[n]-math.floor(L[n]) for n in L}
fs=sorted((f,n) for n,f in frac.items() if n>=30)
shared=set()
for i in range(len(fs)-1):
  if fs[i+1][0]-fs[i][0]<3e-9: shared.add(fs[i][1]); shared.add(fs[i+1][1])
def rational(f):
  return min(abs(f-round(f*q)/q) for q in range(1,41))<3e-9
BAD=('squares-verified-best-of-1105','986b3b6d','5a4c0cdb','take-harvest-r26/695')
def gapof(n):
  g=gap.get(n)
  return bar[n]-(float(g['board_L'])/math.sqrt(n)-1) if g else 0.0
out=[]
for n in range(30,1001):
  why=[]
  s=src.get(n,('','',''));st=s[1]
  if n in OUT: why.append('out n')
  if any(b in st for b in BAD) and 'own Samanyu' not in st: why.append('names a banned source')
  c=closed(L[n])
  if c<2e-9: why.append('closed form %.1e'%c)
  if st.startswith('harvest') and 'kick' not in st: why.append('plain public source')
  t0 = n in UNRUN and n not in ch31 and n not in kicked_other
  if not t0:
    if n in kicked: why.append('lkick line '+kicked[n][:60])
    if gapof(n)<=1e-9: why.append('at the board')
  sh = n in shared or rational(frac[n])
  tier=2 if sh else (0 if t0 else 1)
  out.append(dict(n=n,L=L[n],bar=bar[n],gap=gapof(n),closed=c,src_table=s[0],shared=sh,tier=tier,why=why))
ok=[o for o in out if not o['why']]
ok.sort(key=lambda o:(o['tier'],-o['gap']))
json.dump(dict(ok=ok,all=out),open(sys.argv[1],'w'),indent=1)
print('rows',len(out),'ok',len(ok),'tiers',[sum(1 for o in ok if o['tier']==t) for t in (0,1,2)],'kicked',len(kicked),'changed',len(changed),'shared',len(shared))
print('unrun dropped:',[(o['n'],o['why']) for o in out if o['n'] in UNRUN and o['why']])
for o in ok[:60]: print(o['tier'],o['n'],'%.9f'%o['L'],'gap %.3e'%o['gap'],o['src_table'])
