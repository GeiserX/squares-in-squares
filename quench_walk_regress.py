#!/usr/bin/env python3
"""quench (round 33): regression checks of quench_walk.py, each with a control that must still refuse.

Usage: quench_walk_regress.py   (prints one line per case, exits 1 when a case fails)
  green  take-forensics-r33/near/911-rect.csv: it reaches gone files below take-rebuild-r32/551.csv and 811.csv, both
         held rows of round 32 a, and a claim line and a priority line that say 'withdrawn' about something else. It must
         come back clean, or with no gone or withdrawn hit (main 20:55Z of round 33).
  red    a synthetic start whose sidecar names a gone file outside any held chain: must report 'gone:'.
  red    take-stair-c-r32/near/812-r32-aac32f1102ed-s.csv, withdrawn by its exact bytes at 12:42:23Z of round 32: must
         report 'withdrawn in a handoff line'.
  green  (round 35) take-classfill-r35/work/starts/925-held34a.csv, byte-equal to the 925 rows of the submitted round 34 a
         file: a held root, clean, with 925@34 among its held references.
  red    (round 35) the jazivxt 925 public rows with one x moved 1e-12, sidecar naming the public file: refused as public-first.
"""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import quench_walk as qw  # noqa: E402
S = qw.S
bad = 0


def case(name, path, ok):
    global bad
    r = qw.check(path)
    good = ok(r)
    bad += not good
    print('%s %s: clean=%s hits=%s' % ('PASS' if good else 'FAIL', name, r['clean'], [h[:120] for h in r['hits']][:4]), flush=True)


case('green 911-rect (held-chain gone files, claim and priority lines)', S + 'take-forensics-r33/near/911-rect.csv',
     lambda r: r['clean'] or not any(h.startswith(('gone:', 'withdrawn')) for h in r['hits']))
d = tempfile.mkdtemp(prefix='qwregress-')
try:
    src = S + 'take-forensics-r33/near/911-rect.csv'
    p = d + '/911-gonecontrol.csv'
    shutil.copyfile(src, p)
    json.dump({'source': 'invent_rest.py lkick of take-backlog-r31/near/911-gonecontrol-zz.csv (sha256 0123456789abcdef)',
               'licence': 'as its start'}, open(p + '.json', 'w'))
    case('red gone file outside a held chain', p, lambda r: any(h.startswith('gone: take-backlog-r31/near/911-gonecontrol-zz.csv') for h in r['hits']))
finally:
    shutil.rmtree(d)
case('red withdrawn exact bytes (stair-c r32 812)', S + 'take-stair-c-r32/near/812-r32-aac32f1102ed-s.csv',
     lambda r: any(h.startswith('withdrawn in a handoff line') for h in r['hits']))
# round 35 (main 12:04:54Z ruling): a start whose rows equal the n rows of a submitted gather file is a held root
case('green 925 start equal to the submitted round 34 a row (classfill r35)', S + 'take-classfill-r35/work/starts/925-held34a.csv',
     lambda r: r['clean'] and (qw.held_gather(S + 'take-classfill-r35/work/starts/925-held34a.csv', 925) or (0,))[0] == 34)
d = tempfile.mkdtemp(prefix='qwregress-')
try:
    import csv as _csv
    pub = S + 'take-harvest-r29/work/public06/data/nb/jazivxt__boxed-in-sub/submission.csv'
    rows = [r for r in _csv.DictReader(open(pub)) if r['n'] == '925']
    rows[0]['x'] = repr(float(rows[0]['x'].lstrip('s')) + 1e-12)  # not byte-equal to any submitted row: a public-first start
    p = d + '/925-pubcontrol.csv'
    with open(p, 'w') as f:
        f.write('n,square_id,x,y,angle\n')
        for i, r in enumerate(rows):
            f.write('925,%d,%s,%s,%s\n' % (i, r['x'].lstrip('s'), r['y'].lstrip('s'), r['angle'].lstrip('s')))
    json.dump({'source': 'jazivxt/boxed-in-sub :: submission.csv, n = 925 (%s)' % pub, 'licence': 'Apache 2.0'}, open(p + '.json', 'w'))
    case('red synthetic public-first 925 start (jazivxt rows, one x moved 1e-12)', p,
         lambda r: not r['clean'] and any('public-first' in h for h in r['hits']))
finally:
    shutil.rmtree(d)
sys.exit(1 if bad else 0)
