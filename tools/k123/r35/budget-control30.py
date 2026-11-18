from pathlib import Path
import sys,json,time
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));from admission_budget30 import run,Deferred
assert run(lambda text:json.loads(text)['clean'],'{"clean":true}','budget-control-fast',seconds=.05)
def slow(text):time.sleep(.2);return True
try:run(slow,'{"control":"timeout"}','budget-control-slow',seconds=.05)
except Deferred:deferred=True
else:deferred=False
assert deferred
(W/'budget-control30.json').write_text(json.dumps({'fast_check_preserved':True,'timed_check_deferred':True,'no_admission_on_timeout':True}));print('budget control passed: fast proof returned; timed proof deferred without admission',flush=True)
