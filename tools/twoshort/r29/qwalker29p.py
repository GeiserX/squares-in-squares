"""Priority walker (round 29): walk queued top-level take csv files of live r29 lanes first, then forensics and k123
near files, newest first; the two plain walkers had 206 files to walk at 08:00Z and fresh take rows waited behind them."""
from pathlib import Path
import sys, time, re
W = Path(__file__).parent; sys.path.insert(0, str(W))
import qgate29
TAKE = re.compile(r'/take-[a-z0-9-]+-r29/\d+\.csv$'); FK = re.compile(r'/take-(?:forensics|k123)-r29/near/')
while time.time() < int((W / 'deadline').read_text()) + 300 and not (W / 'STOP-COLLECT').exists():
    lines = qgate29.queue_path.read_text().splitlines() if qgate29.queue_path.exists() else []
    todo = []
    for x in reversed(lines):
        if x not in todo and (TAKE.search(x) or FK.search(x)):
            todo.append(x)
    todo.sort(key=lambda x: 0 if TAKE.search(x) else 1)
    worked = False
    for x in todo:
        p = Path(x)
        if not p.is_file() or qgate29.lookup(p) is not None:
            continue
        try:
            res = qgate29.check(p); worked = True
            print(time.strftime('%FT%TZ', time.gmtime()), 'clean' if res.get('clean') else 'REFUSED', p, flush=True)
        except Exception as ex:
            print('ERROR', p, repr(ex), flush=True)
        break
    if not worked:
        time.sleep(10)
