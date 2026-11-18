from pathlib import Path
import time,os
w=Path(__file__).resolve().parent;cut=float((w/'deadline').read_text())+600;tmp=w/'report-fallback31.tmp';tmp.write_bytes((w/'report-fallback-ready31.json').read_bytes())
while time.time()<cut:time.sleep(max(0,min(.1,cut-time.time())))
try:os.link(tmp,w.parent/'report.json')
except FileExistsError:pass
