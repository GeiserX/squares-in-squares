import csv, math
from pathlib import Path
W = Path(__file__).parent; T = W.parent
s = (W / 'driver.py').read_text(); s = s[:s.index("log('start round32 collector/scanner")]
s = s.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)", "")
ns = {'__name__': 'border_beyond', '__file__': str(W / 'driver.py')}; exec(compile(s, str(W / 'driver.py'), 'exec'), ns)
ns['refresh'](); cur = ns['current']; tot = 0
for r in csv.DictReader(open(T / 'take.tsv'), delimiter='\t'):
    n = int(r['n']); o = float(cur[n]['new']); d = o - float(r['new']); tot += d
    print(n, 'best other', repr(o), cur[n].get('take', cur[n]['source'])[:90], 'ours', r['new'], 'beyond score', repr(d), 'side', d * math.sqrt(n), 'rule side', math.sqrt(n) * 1e-10)
print('total beyond', repr(tot))
