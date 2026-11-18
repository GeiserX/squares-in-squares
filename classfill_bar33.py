"""Run the imported kick search with each incoming fq box capped at the bar."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import midm_scan as M
index=sys.argv.index('--input-side');bar=float(sys.argv[index+1]);del sys.argv[index:index+2]
original=M.quench
first=True
def quench(fq,tmp,s,X,flags,timeout=180):
 global first
 cap=min(s,bar)
 if first:print('BAR_INPUT_CONTROL actual_side',repr(s),'fq_input_side',repr(cap),'bar',repr(bar),flush=True);first=False
 return original(fq,tmp,cap,X,flags,timeout)
M.quench=quench
if any('xstop6control30' in q for q in sys.argv) or Path('STOP6.enabled').exists():
 sys.argv.append('--stop6')
 print('STOP6_ENABLED',flush=True)
M.main()
