"""Walk queued intake files with quench_walk.py off the collector's path, filling the shared cache (round 26)."""
from pathlib import Path
import sys, time, os
W = Path(__file__).parent; sys.path.insert(0, str(W))
import qgate29
done_upto = 0
while time.time() < int((W / 'deadline').read_text()) + 300 and not (W / 'STOP-COLLECT').exists():
    lines = qgate29.queue_path.read_text().splitlines() if qgate29.queue_path.exists() else []
    todo = []
    for x in lines:
        if x not in todo:
            todo.append(x)
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
    if not worked:
        time.sleep(10)
