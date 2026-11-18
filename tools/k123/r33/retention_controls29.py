from pathlib import Path
import sys,json,time
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from current_walk29 import retention_note
line=next(l for l in (W.parent.parent/'handoff-r33.log').read_text().splitlines() if l.startswith('2026-11-15T08:40:36Z rebuild -> main:'))
assert retention_note(line)
assert retention_note(line.replace('not withdrawn',' '))
assert not retention_note(line.replace('will withdraw them if you rule otherwise','WITHDRAW these exact bytes now'))
assert not retention_note(line.replace('2026-11-15T08:40:36Z','2026-11-15T09:00:00Z'))
(W/'retention-controls29.json').write_text(json.dumps({'conditional_note_ignored':True,'explicit_action_preserved':True,'later_entry_preserved':True},indent=2));print('retention note control green; explicit and later actions preserved',flush=True)
