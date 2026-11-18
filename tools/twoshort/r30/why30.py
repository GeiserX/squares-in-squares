"""Print why our ancestry gate defers each file. Usage: why30.py FILE..."""
import sys,json,csv;sys.path.insert(0,'$SCRATCH/bounties-squares/take-twoshort-r30/work')
from admit30 import trace_input_lenient
for p in sys.argv[1:]:
    n=int(next(csv.DictReader(open(p)))['n'])
    try:ok,d=trace_input_lenient(p,n)
    except Exception as e:print(p,'EXC',repr(e));continue
    cl=d.get('closure') or d.get('fresh_closure') or {}
    print(p.split('bounties-squares/')[-1],'OK' if ok else 'NO',d.get('reason') or '',json.dumps(cl.get('errors',[]))[:700])
