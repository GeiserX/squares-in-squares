from pathlib import Path
import sys,json,re
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from forensic_pin30 import row
p=Path('$SCRATCH/bounties-squares/take-midm-r28/978.csv');origin='$SCRATCH/bounties-squares/take-forensics-r28/work/feed/take-midm-r28/978-36ff301e7600fe0f74d53a8e.csv.origin.json'
r=row(p,{'source':origin});assert r and r['producer_csv_sha256']=='36ff301e7600fe0f74d53a8e87457f1c9cede4e6fdab3c9f9cd40aa01e746584'
assert row(p,{'source':origin.replace('36ff301e7600fe0f74d53a8e','deadbeef')}) is None
rx=re.compile(r'(?<![A-Za-z0-9_./-])([0-9]+-[0-9a-f]{8,}\.csv)')
assert rx.findall('source bare 921-29e12ff3.csv')==['921-29e12ff3.csv']
assert not rx.findall('/scratch/978-c9x19-31.753653881-55fd2226.csv')
(W/'controls-pin30.json').write_text(json.dumps({'real978_producer_recovered':True,'missing_binding_rejected':True,'bare921_recognized':True,'decimal_path_suffix_ignored':True,'snapshot':r},indent=2));print('exact978 producer recovery passed; missing binding rejected; genuine bare921 kept; decimal path suffix ignored',flush=True)
