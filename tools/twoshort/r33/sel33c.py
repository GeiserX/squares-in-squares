"""Round 33 twoshort screen c (main 21:46Z SHARED DEEP-KICK QUEUE): held round 32 a rows above the 2026-11-09 board side
with no unprobed 900 s kick since their current geometry, largest board gap first. Row facts come from border's
held33/info.json (gap, rigid, bad source, 45-degree lattice, spent, unprobed 900 s kick lines of rounds 31 and 32,
changed in round 32). Out: border's reach (the next RESERVE rows of border's deep order after the rows it already queued),
rows whose bar33 source is not the held file, n named by a 900 s line of handoff-r33.log. The collector rechecks claims
right before each queue."""
import json, csv, re, sys
from pathlib import Path
B=Path('$SCRATCH/bounties-squares');BW=B/'take-border-r33/work'
RESERVE=int(sys.argv[2]) if len(sys.argv)>2 else 8
info={int(k):v for k,v in json.load(open(BW/'held33/info.json')).items()}
src={int(r['n']):r['source'] for r in csv.DictReader(open(B/'round33-briefs/bar33.tsv'),delimiter='\t')}
SKIP={639,691,745,858,918,980,494,626,677,678,730,731,842,843,901,902,962,963,964,785,786}
CLOSED={692,746,643,341,926,863,695,686,859,989,812,416,634,912,588}   # border's two-dry-seed rows (lesson 6b)
r33=set()
for line in open(B/'handoff-r33.log',errors='replace'):
  if re.search(r'\b900\s*s|900s',line) and re.search(r'kick|claim',line,re.I):
    r33.update(int(m) for m in re.findall(r'\bn\s*=\s*(\d+)',line))
bq=set(int(m) for m in re.findall(r'DEEP queue (\d+)',open(BW/'deepfeed33.log').read()))
border=sorted((-v['gap'],n) for n,v in info.items() if v['gap'] and v['gap']>=1e-5 and not (v['rigid'] or v['bad'] or v['lattice'] or v['spent'] or v['unprobed3132']) and n not in SKIP)
border_left=[n for g,n in border if n not in bq and n not in r33]
reach=set(border_left[:RESERVE])
ok=[]
for n,v in sorted(info.items(),key=lambda x:-(x[1]['gap'] or 0)):
  if not v['gap'] or v['gap']<=1e-9:continue
  why=[]
  if v['rigid'] or v['bad'] or v['lattice'] or v['spent']:why.append('rigid/bad/lattice/spent')
  if v['unprobed3132']:why.append('unprobed 900 s kick in r31/r32')
  if n in SKIP or n in CLOSED:why.append('skip/closed')
  if not src.get(n,'').startswith('held round32'):why.append('bar source '+src.get(n,'')[:30])
  if n in r33:why.append('900 s line in r33')
  if n in reach:why.append('border reach')
  if not why:ok.append(dict(n=n,gap=v['gap'],changed32=v['changed32']))
json.dump(dict(ok=ok,reach=sorted(reach),border_left=border_left[:20]),open(sys.argv[1],'w'),indent=1)
print('ok',len(ok),'border next',border_left[:RESERVE+4],'reserve',RESERVE)
print([(o['n'],'%.2e'%o['gap']) for o in ok[:40]])
