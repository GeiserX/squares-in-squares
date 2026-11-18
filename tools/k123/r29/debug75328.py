from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import *
from source25 import audit_text
p=S/'take-k123-r27/753.csv';c=legacy_credit(753,mlp.load(str(p),{753})[753],str(p));print('legacy',json.dumps(c),flush=True)
def trace(frame,event,arg):
 if frame.f_code.co_filename.endswith('/source25.py') and frame.f_code.co_name=='audit_text' and event=='return' and arg is None:
  print('REFUSED LINE',frame.f_lineno,flush=True)
  for k in ['t','p','bare','text','c','nn','kk','record','jp']:
   print(k,str(frame.f_locals.get(k,''))[:14000],flush=True)
 return trace
sys.settrace(trace);z=audit_text(json.dumps(c,sort_keys=True,default=str));print('RESULT',bool(z),flush=True)
