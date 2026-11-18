from pathlib import Path
import hashlib,json,time
W=Path(__file__).resolve().parent;L=Path('.')
s=(L/'quench_walk.py').read_text().replace("LANE = os.path.dirname(os.path.abspath(__file__))",f'LANE = {str(L)!r}')
s=s.replace("'QUENCH_LIVE_ROUND', '30'","'QUENCH_LIVE_ROUND', '31'")
# Keep the measured historical bound on implicit references. Explicit rounds stay exact.
needle="nn, k = int(a), (int(b) if b else None)\n                if 1 <= nn"
rep="""nn, k = int(a), (int(b) if b else None)
                if k is None:
                    context_round = p[2] if isinstance(p,tuple) else None
                    if not isinstance(p,tuple):
                        mr = re.search(r'/take-[a-z0-9-]+-r(\\d+)/', p)
                        if mr:context_round=int(mr[1])
                    if context_round is not None:k=context_round
                if 1 <= nn"""
assert needle in s;s=s.replace(needle,rep)
# Preserve positive path lookups within a source walk. New proofs have new hashes.
needle="LIVE = os.environ.get('QUENCH_LIVE_ROUND', '31')"
s=s.replace(needle,"""_ancestor_path_cache31={}
def ancestor_paths31(h):
    if h not in _ancestor_path_cache31:
        found=[d+'/'+h+'.json' for d in ANCDIRS if os.path.isfile(d+'/'+h+'.json')]
        if found:_ancestor_path_cache31[h]=found
        return found
    return _ancestor_path_cache31[h]
"""+needle)
a=s.index('        for h in ANC.findall(t):');b=s.index('        if not isinstance(p, tuple):',a)
s=s[:a]+"        for h in set(ANC.findall(t)):\n            for ancestor_path in ancestor_paths31(h):\n                queue.append(ancestor_path); via.setdefault(ancestor_path,parent)\n"+s[b:]
(W/'walker30.py').write_text(s)
(W/'restart-stage28').touch();(W/'restart-collect25').touch();(W/'restart-third29').touch()
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA ADOPT shared r31 quench source reader sha256='+hashlib.sha256((L/'quench_walk.py').read_bytes()).hexdigest()+'. Keep historical held cap and positive ancestry path cache. Full public audit now uses harvest31 policy with every archive version and own-seed references excluded. Source controls rerun before counting rows. Deadline17:15Z.\n')
print('adopted',hashlib.sha256(s.encode()).hexdigest())
