"""Summarise round 31 boxE runs by kind: runs, tries, moved (>1e-8 of side), best side removed."""
import json, glob, collections
from pathlib import Path
W=Path(__file__).parent;S=collections.defaultdict(lambda:[0,0,0,0.0,[]])
for p in sorted((W/'boxE31/done').glob('*.json')):
 j=json.load(open(p))
 if 'start_side' not in j or j.get('control'):continue
 k=('lkick after dry midm' if j['tag'].startswith('ab-') and not j.get('legs') else ('lkick leg' if j.get('legs') else 'lkick first pass (held row)') if j.get('tool')=='lkick' else 'midm leg' if j.get('legs') else 'midm probe 900 s')
 if j['tag'].startswith('own31'):k='lkick of our certified row'
 m=j['start_side']-j['best'];s=S[k];s[0]+=1;s[1]+=j['tries'];s[2]+=m>1e-8;s[3]=max(s[3],m)
 if m>1e-8:s[4].append(j['n'])
for k,s in S.items():print('%-28s runs %3d tries %5d moved %2d best %.2e %s'%(k,s[0],s[1],s[2],s[3],s[4]))
