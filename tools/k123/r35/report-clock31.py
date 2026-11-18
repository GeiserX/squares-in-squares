"""Publish the prepared final report as the first action after the take deadline."""
from pathlib import Path
import subprocess,time,json,os
W=Path(__file__).resolve().parent;PY=str(W.parent.parent/'venv/bin/python');cutoff=float((W/'deadline').read_text())+600
while time.time()<cutoff-15:time.sleep(min(30,cutoff-15-time.time()))
subprocess.run([PY,str(W/'report31.py'),'--prepare-report'],check=True,timeout=12)
raw=(W/'report-ready31.json').read_bytes();tmp=W.parent/'report-clock31.tmp';tmp.write_bytes(raw)
while time.time()<cutoff:time.sleep(min(.1,cutoff-time.time()))
tmp.replace(W.parent/'report.json')
