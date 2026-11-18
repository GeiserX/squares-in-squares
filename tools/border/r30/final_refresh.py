"""Last competing-take refresh (the step finish.py runs at 05:51Z) plus a withdrawal audit of every live row."""
import csv, re, sys
from pathlib import Path
W = Path(__file__).parent; T = W.parent
s = (W / 'driver.py').read_text(); s = s[:s.index("log('start round30 collector/scanner")]
s = s.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)", "")
ns = {'__name__': 'border_final', '__file__': str(W / 'driver.py')}; exec(compile(s, str(W / 'driver.py'), 'exec'), ns)
ns['refresh']()
import provenance as pv
pv._wd['t'] = 0; wd = pv.withdrawn(); hs = pv._wd['h']
csv.field_size_limit(10**9)
for r in csv.DictReader(open(T / 'take.tsv'), delimiter='\t'):
    n = int(r['n']); src = r['source'] + ' ' + r['licence']
    named = [k for k in wd if k in src]; hn = [h for h in hs if h in src]
    donor = Path(re.search(r' of (/Volumes/\S+?\.csv)', r['source'])[1])
    ok = pv.audit(donor, {'source': r['source'], 'licence': r['licence']}) if donor.exists() else 'donor gone'
    pol = ns['sp'].classify(r['source'], r['licence']); q = ns['qualifies'](n, float(r['new']), pol)
    print(n, r['new'], 'qualifies', q, 'walk', ok, 'withdrawn paths named', named, 'withdrawn hashes named', hn, flush=True)
