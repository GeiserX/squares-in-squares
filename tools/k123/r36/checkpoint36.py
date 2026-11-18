from pathlib import Path
import sys
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from finalutil36 import artifacts,commit,run,PY
artifacts();commit();run([PY,str(W/'report36.py')])
