"""Round 29 kick counts for the doc: runs, tries, runs that moved, best side removed, by tool and by input lane."""
from pathlib import Path
import json,re,collections
W=Path(__file__).parent;R=W/'boxE29'
g=collections.defaultdict(lambda:[0,0,0,0.0])
for p in R.glob('done/*.json'):
 d=json.load(open(p))
 if 'start_side' not in d or d.get('tag','').startswith('control'):continue
 tool=('midm_scan lkick,kick %d s' if d.get('tool')=='midm' else 'invent_rest lkick %d s')%d.get('seconds',180)
 lane=re.sub(r'-\d+-[0-9a-f]{8}$','',d['tag']);lane='held27 seed rows' if lane=='reopen-held27' else lane
 gain=d['start_side']-d['best']
 for k in (('tool',tool),('lane',lane),('all','all')):
  r=g[k];r[0]+=1;r[1]+=d['tries'];r[2]+=gain>1e-12;r[3]=max(r[3],gain)
for kind in ('all','tool','lane'):
 print('|',kind,'| runs | tries | moved | best side removed |');print('|---|---|---|---|---|')
 for k,r in sorted(g.items(),key=lambda x:-x[1][0]):
  if k[0]==kind:print('| %s | %d | %d | %d | %.1e |'%(k[1],r[0],r[1],r[2],r[3]))
 print()
