"""Stop the running job of one slot when its tag matches (whole process tree), or drop it from the queue."""
import os, sys, json, signal, subprocess
from pathlib import Path
B = Path(__file__).resolve().parent
slot, tag = sys.argv[1], sys.argv[2]
q = B / 'queue' / slot / (tag + '.json')
if q.exists():
    q.rename(q.with_suffix('.cancelled')); print('DEQUEUED', tag); sys.exit(0)
a = B / f'active-{slot}.json'
try:
    j = json.loads(a.read_text())
except Exception:
    print('NOT_ACTIVE', tag); sys.exit(0)
if tag not in ' '.join(j['cmd']):
    print('OTHER_ACTIVE', tag); sys.exit(0)
pairs = [list(map(int, l.split())) for l in subprocess.check_output(['ps', '-axo', 'pid,ppid'], text=True).splitlines()[1:] if l.strip()]
ids = {j['pid']}
for _ in range(8):
    ids |= {x for x, y in pairs if y in ids}
for pid in sorted(ids, reverse=True):
    try: os.kill(pid, signal.SIGTERM)
    except ProcessLookupError: pass
print('KILLED', tag, sorted(ids))
