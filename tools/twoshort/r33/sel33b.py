"""Round 33 twoshort screen b (main 18:58Z answer: n 400 to 1000). From sel33.py (override 8): held round 32 a rows of n 1 to 399 whose current geometry no lane has lkicked.
Current geometry: the round in which the held row last changed (the last results/roundK-best-*.tsv that lists n; 0 if none).
An lkick line (invent_rest lkick, or a backlog/invent claim) in a handoff log of round K or later counts as an lkick of it
(midm_scan lines do not: a 150 s invent_rest lkick moved 12% of held rows a midm probe found dry in round 31).
Out: the five out n, rows whose source names a banned file, closed-form sides a+b*sqrt2/8, 45-degree lattice rows
(every angle at 45 degrees), plain public rows, rows at or below the 2026-11-09 board side for n under 200 (round 32: 0 of 6),
rows whose side fraction another held n shares or is p/q with q <= 40 (round 31 and 32: 0 of about 41).
Order: rows above the board side first (largest score gap first), then the rest by gap."""
import csv, re, math, json, glob, sys
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares'); R=Path('results')
L={int(r['n']):float(r['L']) for r in csv.DictReader(open(B/'gate/cand-round32-1116a/details.csv'))}
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round33-briefs/bar33.tsv'),delimiter='\t')}
gap={int(r['n']):r for r in csv.DictReader(open(B/'main-r17/gap-by-n.tsv'),delimiter='\t')}
OUT={639,691,745,858,918}
def rnd_of(lg): return int(re.search(r'r(\d+)',lg)[1])
def lklines():
  k={}
  for p in sorted(B.glob('handoff-r*.log'),key=lambda p:rnd_of(p.name)):
    rd=rnd_of(p.name)
    for line in open(p,errors='replace'):
      if 'midm_scan' in line: continue
      if re.search(r'claims (near|seed|reopen):',line): continue
      if re.search(r'invent_rest|invent lkick|\blkick\b',line) or re.match(r'\S+ (backlog|invent) -> \S+ claims? ',line):
        ns=set()
        for m in re.findall(r'\bn ?= ?(\d+)',line): ns.add(int(m))
        for m in re.findall(r'(?:held\w*|take-[\w-]+-r\d+)/(\d+)\.csv',line): ns.add(int(m))
        for m in re.findall(r'starts/(\d+)-',line): ns.add(int(m))
        for m in re.findall(r'\bn=((?:\d+,)+\d+)',line):
          for x in m.split(','): ns.add(int(x))
        tm=re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)',line); tm=tm[1] if tm else ''
        for n in ns: k.setdefault(n,[]).append((rd,p.name+': '+line[:160].strip(),tm))
  return k
kicked=lklines()
cert32={}
for line in open(B/'handoff-r32.log',errors='replace'):
  m=re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\S* (\S+) -> .*certified n=(\d+)',line,re.I)
  if m: cert32[int(m[3])]=m[1]
changed={}
for f in glob.glob(str(R/'round*-best-*.tsv')):
  k=int(re.search(r'round(\d+)-best',f)[1])
  for r in csv.DictReader(open(f),delimiter='\t'):
    try: n=int(r['n'])
    except (ValueError,TypeError): continue
    changed[n]=max(changed.get(n,0),k)
src={}
def _tkey(f):
  b=Path(f).name;d=re.search(r'(\d{4}-\d\d-\d\d)([a-z]?)',b);r=re.search(r'round(\d+)-best',b)
  return (d[1],1 if r else 0,int(r[1]) if r else 0,d[2])
for f in sorted(glob.glob(str(R/'round*-best-*.tsv'))+glob.glob(str(R/'harvest-best-*.tsv')),key=_tkey):
  for r in csv.DictReader(open(f),delimiter='\t'):
    try: src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
    except (ValueError,TypeError): pass
ang={}
with open(B/'gather/round32-2026-11-16a.csv') as f:
  for r in csv.DictReader(f):
    n=int(r['n'])
    ang.setdefault(n,[]).append(float(r['angle']))
def lattice45(n):
  t=[math.degrees(x)%90 for x in ang[n]]; t=[x for x in t if min(x,90-x)>1e-7]
  return bool(t) and all(abs(x-45)<1e-7 for x in t)
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
def rational(f): return min(abs(f-round(f*q)/q) for q in range(1,41))<3e-9
BAD=('squares-verified-best-of-1105','986b3b6d','5a4c0cdb','take-harvest-r26/695','joegun-boxed-certified-union')
def gapof(n):
  g=gap.get(n)
  return bar[n]-(float(g['board_L'])/math.sqrt(n)-1) if g else 0.0
out=[]
for n in range(400,1001):
  why=[];s=src.get(n,('','',''));st=s[1];K=changed.get(n,0)
  if n in OUT: why.append('out n')
  if any(b in st for b in BAD) and 'own Samanyu' not in st: why.append('names a banned source')
  c=closed(L[n])
  if c<2e-9: why.append('closed form %.1e'%c)
  if lattice45(n): why.append('45-degree lattice')
  if st.startswith('harvest') and 'kick' not in st: why.append('plain public source')
  lk=[x for x in kicked.get(n,[]) if x[0]>=K and not (K==32 and x[0]==32 and x[2]<=cert32.get(n,''))]
  if lk: why.append('lkick of current geometry (round %d) '%K+lk[0][1][:80])
  g=gapof(n)
  if g<=1e-9 and n<200: why.append('at the board, n<200')
  if n in shared or rational(frac[n]): why.append('shared or p/q fraction')
  out.append(dict(n=n,L=L[n],bar=bar[n],gap=g,closed=c,changed=K,src_table=s[0],why=why,
                  older_lk=[x[1][:100] for x in kicked.get(n,[]) if x[0]<K][:2]))
ok=[o for o in out if not o['why']]
hi=[o for o in ok if o['n']>=700];lo=[o for o in ok if o['n']<700]
def order(xs): return sorted(xs,key=lambda o:(o['gap']<=1e-9,-o['n']))
hi,lo=order(hi),order(lo);ok=[]
while hi or lo:
  for xs in (hi,lo):
    if xs: ok.append(xs.pop(0))
ok.sort(key=lambda o:o['gap']<=1e-9)
json.dump(dict(ok=ok,all=out),open(sys.argv[1],'w'),indent=1)
import collections
c=collections.Counter(w.split(' ')[0]+' '+w.split(' ')[1] for o in out for w in o['why'][:1])
print('rows',len(out),'ok',len(ok),'first-why',dict(c))
for o in ok[:120]: print(o['n'],'%.9f'%o['L'],'gap %.3e'%o['gap'],'chg r%d'%o['changed'],o['src_table'],'older-lk',len(o['older_lk']))
