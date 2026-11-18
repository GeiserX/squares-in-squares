"""Remote scanner: preserve local donor identities while reading box copies."""
import json
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_rect as rect

job = json.loads(Path(sys.argv[1]).read_text())
root = Path(__file__).resolve().parents[1]
(root/'scanner.pid').write_text(str(os.getpid()))
remaining = job['deadline'] - time.time()
if remaining <= 0:
    raise SystemExit('search deadline reached')
signal.setitimer(signal.ITIMER_REAL, remaining)
read = rect.layouts
mapping = json.loads((root/'feed-map.json').read_text())
def layouts(path):
    key = str(path)
    return read(root/'feed'/mapping[key]) if key in mapping else read(path)
rect.layouts = layouts
rect.main(job['args'])
