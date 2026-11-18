"""r37 (brief 6h, item 8): uncapped rewalk (cap 100000) of the three r36 donors refused only through take-forensics-r35
walk reports, with walk reports left out: a work/walks/*.json is not followed (FOLLOW_MAP extended), as the walker
already skips a follow lane's seen map. Writes walks/<sha16>-rewalk.json (never named in any sidecar)."""
import sys, json, re, hashlib, time
sys.path.insert(0, '.')
import quench_walk as q
q.FOLLOW_MAP = re.compile(q.FOLLOW_MAP.pattern + r'|/work/walks/[^/]*\.json$')
from pathlib import Path
W = Path(__file__).parent
for p in sys.argv[1:]:
    sha = hashlib.sha256(open(p, 'rb').read()).hexdigest(); t = time.time()
    r = q.check(p, cap=100000)
    out = {k: r.get(k) for k in ('clean', 'capped', 'files', 'hits')}; out.update(path=p, sha256=sha, seconds=round(time.time() - t), walk_reports='left out')
    (W / 'walks' / f'{sha[:16]}-rewalk.json').write_text(json.dumps(out))
    print(json.dumps(out)[:600], flush=True)
