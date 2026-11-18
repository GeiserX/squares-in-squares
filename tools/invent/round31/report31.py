"""Write the report at the take deadline even if cleanup hits an external delay."""
import pathlib,time,json,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import finish31 as F
D=float((W/'report-deadline').read_text())-.9
while time.time()<D-2:time.sleep(min(15,max(.01,D-2-time.time())))
source=W/'report.pending.json';pending=W/'timed-report.pending.json'
if source.exists():pending.write_bytes(source.read_bytes())
else:pending.write_text(json.dumps(F.report_object(),indent=2)+'\n')
while time.time()<D:time.sleep(min(.1,max(.001,D-time.time())))
pending.replace(W.parent/'report.json')
