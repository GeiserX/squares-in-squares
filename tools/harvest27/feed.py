"""Read late handoffs and takes until fifteen minutes before the take deadline."""
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import END,S,W,state
from follow import scan
stop=END-300  # 23:40 UTC; public fetching stops earlier
while time.time()<stop:
    p=S/'handoff-r27.log'
    if p.exists():(W/'handoff-last-read.txt').write_text(p.read_text())
    state('SCAN closing feed: live takes and handoffs; stop23:40Z, proof deadline23:45Z')
    scan()
    time.sleep(max(0,min(60,stop-time.time())))
state('STOP closing feed at23:40Z; no more inputs queued')
