"""Count the plan rows the collector would still queue now (same filters as manage32.queue_next)."""
import json,collections
src=open('manage32.py').read().split("if __name__=='__main__':")[0]
g={'__file__':'manage32.py'};exec(src,g)
cl=g['others_claimed']();lv=g['live']()
sent={(json.load(open(p))['n'],json.load(open(p))['seed']) for p in (g['W']/'jobsent').glob('*.json')}
c=collections.Counter();elig=collections.defaultdict(list)
for n,seed,o in g['plan']():
  if (n,seed) in sent: c['sent']+=1;continue
  if n in g['OUT'] or n in lv: c['live/out']+=1;continue
  if n in cl and (n,seed) not in g['EXTRA']: c['claimed']+=1;continue
  elig[str(o.get('tier'))].append(n)
print(dict(c),{k:len(v) for k,v in elig.items()})
for k,v in elig.items(): print(k,v)
