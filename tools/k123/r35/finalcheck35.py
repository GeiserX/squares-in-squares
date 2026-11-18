"""Revived final pass: re-check each take.tsv row as written: clearance >= 2.2e-11, metric ok as written and via pandas, score == take.tsv new."""
import sys,csv,json
from pathlib import Path
sys.path.insert(0,'.')
import floatsafe as fs
csv.field_size_limit(1<<28)
T=Path(__file__).resolve().parent.parent
for r in csv.DictReader((T/'take.tsv').open(),delimiter='\t'):
    n=int(r['n']);rows=[x for x in csv.DictReader((T/f'{n}.csv').open()) if int(x['n'])==n]
    cl=fs.clearance(rows);s,why=fs.check(n,rows);s2,why2=fs.check(n,fs.via_pandas(rows))
    print(json.dumps(dict(n=n,rows=len(rows),clearance=cl,clear_ok=cl>=fs.MIN_CLEARANCE,why=why,why_pandas=why2,score=s,take_new=float(r['new']),match=abs(s-float(r['new']))<1e-15)),flush=True)
