import json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(W));import run32 as C
with tempfile.TemporaryDirectory(dir=W) as td:
 root=Path(td);digest='badbadba'+'1'*56
 (root/'handoff-r31.log').write_text('2026-11-16T00:00:00Z test -> all: WITHDRAW n=3 sha256 '+digest[:16]+' old.csv\n')
 (root/'handoff-r32.log').touch()
 with patch.object(C,'S',root):
  assert C.withdrawn(digest)
  assert not C.withdrawn('2'*64)
C.atom(W/'byte-admission-controls.json',dict(withdrawn_pin_rejected=True,later_bytes_allowed=True))
print('WITHDRAWAL_CONTROL_PASS withdrawn byte pin refused; later bytes allowed')
