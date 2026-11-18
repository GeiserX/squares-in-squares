"""r36 (rule 6g): uncapped walk (cap 100000) of one start; writes walks/<sha16>-full.json (never named in any sidecar)."""
import sys, json, hashlib, time
sys.path.insert(0, '.')
import quench_walk as q
from pathlib import Path
W = Path(__file__).parent
for path in sys.argv[1:]:
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    t = time.time(); r = q.check(path, cap=100000)
    j = {k: r.get(k) for k in ('start', 'n', 'clean', 'capped', 'files', 'hits')}; j['seconds'] = round(time.time() - t)
    (W / 'walks' / f'{sha[:16]}-full.json').write_text(json.dumps(j)); print(json.dumps(j), flush=True)
