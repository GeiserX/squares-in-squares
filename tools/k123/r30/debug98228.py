from pathlib import Path
import sys,json,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,legacy_credit
from source25 import audit_text
p=W/'reopened/982-final-own-r25.csv';c=legacy_credit(982,mlp.load(str(p),{982})[982],str(p));out={'legacy':bool(c)}
def trace(frame,event,arg):
 if frame.f_code.co_filename.endswith('/source25.py') and frame.f_code.co_name=='audit_text' and event=='return' and arg is None:
  d=frame.f_locals;out.update(line=frame.f_lineno,path=str(d.get('p','')),bare=d.get('bare',''),implicit_n=d.get('nn'),implicit_round=d.get('kk'),text_flags={x:x in str(d.get('t','')) for x in ['original clean seed','source credited in README','CC BY-SA','squares-verified-best-of-1105','Samanyu']})
 return trace
sys.settrace(trace);result=audit_text(json.dumps(c,sort_keys=True,default=str)) if c else None;sys.settrace(None);out['accepted']=bool(result);(W/'old982-audit28.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA TRACE old982 admission '+json.dumps(out)+'; original source file unchanged; deadline17:45Z.\n')
