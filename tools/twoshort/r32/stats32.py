"""Summarise round 32 boxE runs by kind: runs, tries, moved (>1e-8 of side), best side removed.
Tiers come from sel32.json (0: r31 unrun jobs, 1: held rows with no lkick line of r29 to r32, 2: shared or p/q side fraction,
3a/3b: second seed of a row whose last lkick line is in r29-30 / r31, 4: 3a or 3b with a shared fraction, 5: rows at the board).
--md prints a markdown table."""
import json, collections, sys
from pathlib import Path
W=Path(__file__).parent;S=collections.defaultdict(lambda:[0,0,0,0.0,[]])
sel={o['n']:o for o in json.load(open(W/'sel32.json'))['ok']}
for p in sorted((W/'boxE32/done').glob('*.json')):
 j=json.load(open(p))
 if 'start_side' not in j:continue
 w=', wide steps' if j.get('sigs') else ''
 t='900 s midm kick, no probe' if j.get('tool')!='lkick' else '150 s lkick'
 if j.get('control'):k='60 s control, '+('midm kick, no probe' if j.get('tool')!='lkick' else 'lkick')+w
 elif j.get('legs'):k='leg, '+t+w
 elif j['seed'] in (3301,3302):k='150 s lkick, extra seed of our r31 row (999)'
 elif j.get('tool')!='lkick':k=t+', held row with the largest board gap'
 else:k='150 s lkick, tier %s'%sel.get(j['n'],{}).get('tier','?')+w
 m=j['start_side']-j['best'];s=S[k];s[0]+=1;s[1]+=j['tries'];s[2]+=m>1e-8;s[3]=max(s[3],m)
 if m>1e-8:s[4].append(j['n'])
if '--md' in sys.argv:
 print('| kind | runs | tries | moved | best side removed | n that moved |\n|---|---|---|---|---|---|')
 for k,s in sorted(S.items()):print('| %s | %d | %d | %d | %.2e | %s |'%(k,s[0],s[1],s[2],s[3],', '.join(map(str,s[4])) or 'none'))
else:
 for k,s in sorted(S.items()):print('%-58s runs %3d tries %5d moved %2d best %.2e %s'%(k,s[0],s[1],s[2],s[3],s[4]))
