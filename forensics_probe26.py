"""Bounded interior probes on changed bands, within the scanner's CPU slot."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import forensics_interior as fi
import forensics_rect as fr
import forensics_compose as fc


def main(jobfile):
    job = json.loads(Path(jobfile).read_text())
    root = Path(job['root'])
    deadline = float((root / 'deadline.txt').read_text())
    signal.setitimer(signal.ITIMER_REAL, max(.01, deadline-time.time()))
    ps = subprocess.check_output(['ps', '-axo', 'pid,ppid,command'], text=True)
    assert not any('forensics_scan25.py ' in line and str(root) in line for line in ps.splitlines())
    (root / 'scanner.pid').write_text(str(os.getpid()))
    fi.control(root / 'control/686.csv')
    measurements = []
    started = time.time()
    for host in job['hosts']:
        source = root / 'feed' / host['relative']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == host['sha256']
        side, q = fc.frame(fr.layouts(source)[host['n']])
        fraction = float(side-int(side+1e-9))
        for w, h in host['shapes']:
            tag = '%d-%dx%d-host' % (host['n'], w, h)
            out = root / 'interior' / tag
            before = time.time()
            rows = fi.scan(out, source, w, h, fraction, 2)
            for row in rows:
                _, expected = fc.frame(dict(fr.sym8(q, side))[row['sym']][row['indices']])
                path = Path(row['path'])
                _, actual = fc.frame(fr.layouts(path)[row['n']])
                assert np.max(np.abs(actual-expected)) < 1e-11
                local = Path(job['local_work']) / 'interior' / tag
                row.update(path=str(local/path.name), source=host['canonical'],
                           source_snapshot=str(local/'sources'/Path(row['source_snapshot']).name),
                           parents=[[host['canonical'], host['n']]])
                Path(str(path)+'.json').write_text(json.dumps(row))
            measurements.append(dict(host=host['canonical'], n=host['n'], w=w, h=h,
                                     fraction=fraction, parts=len(rows), seconds=time.time()-before))
    result = dict(cases=measurements, seconds=time.time()-started,
                  parts=sum(r['parts'] for r in measurements), crops_verified=True)
    (root/'interior26-measurement.json').write_text(json.dumps(result, indent=2))
    print('FINISH interior', len(measurements), result['parts'], result['seconds'], flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
