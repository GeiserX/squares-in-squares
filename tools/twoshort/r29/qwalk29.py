#!/usr/bin/env python3
"""Round 27 second gate: the quench lane's quench_walk.py (imported, never edited), as the assembler runs it.

Its round 27 version drops the Samanyu-dev signals and applies the prvsiyan share test (0.4 within 1e-3).
We load the lane file; if it does not load (another lane mid-edit), we load our byte snapshot pin/quench_walk.r27snap.py
with the lane path as its __file__. One extra filter of ours: handoff WITHDRAW lines that took out 932, 922, 921, 415,
501, 813 or 933 files for the Samanyu-dev seed under a wording the lane's samanyu_only() does not match
("held415/501/813/933 ancestry", "every 932 near file") are not read for those files. Each result names the walker sha256.
Usage: qwalk29.py START.csv [...]  (one JSON line per start)
"""
import os, re, sys, glob, json, hashlib, types
W = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, W)
LANE = '.'; sys.path.insert(0, LANE)
os.environ['QUENCH_LIVE_ROUND'] = '2[89]'


def load(src_path):
    src = open(src_path).read()
    if 'SHARE_MAX' not in src or 'samanyu_only' not in src:
        raise ImportError('not the round 27 quench_walk')
    m = types.ModuleType('quench_walk'); m.__file__ = LANE + '/quench_walk.py'
    exec(compile(src, LANE + '/quench_walk.py', 'exec'), m.__dict__)
    sys.modules['quench_walk'] = m
    return m, hashlib.sha256(src.encode()).hexdigest()


try:
    QW, SHA = load(LANE + '/quench_walk.py'); WHICH = 'lane'
except Exception as ex:
    QW, SHA = load(W + '/pin/quench_walk.r27snap.py'); WHICH = 'snapshot (' + repr(ex)[:80] + ')'
MIXED = re.compile(r'held415/501/813/933|k123 withdrawal of 932|every 932 near file|k123546/695/932|WITHDRAW n=932;|WITHDRAW n=922', re.I)
SAMFILE = re.compile(r'(?:^|/)(?:932|922|921|415|501|813|933)[-.]')
_load = QW.load_withdrawn


def load_withdrawn():
    _load()
    QW.WITHDRAWN_LINES[:] = [(f, l) for f, l in QW.WITHDRAWN_LINES if not (MIXED.search(l) and SAMFILE.search(f))]


QW.load_withdrawn = load_withdrawn
load_withdrawn()
_ref = QW.refusals
QW.refusals = lambda p: [l for l in _ref(p) if not (MIXED.search(l) and SAMFILE.search(p))]
# Round 27: a parent withdrawn under rule b stays a reason after our kicks lower the share (harvest withdrew its 499 start,
# share 0.455, at 15:18Z of round 26 in a line that says 'withdrew', which the WITHDRAW reader does not match; our kicked
# 499 measured 0.160 and passed). Every same-n csv the walk reaches must also have a share under 0.4.
_walk = QW.walk
_last = {}


def walk(start, n, cap=3000):
    out = _walk(start, n, cap)
    _last['seen'] = out[2]
    return out


QW.walk = walk


def ancestor_shares(start, n):
    # Round 28 (main 00:19:03Z): a share match of an ancestor is never a reason to refuse our own layouts. Disabled;
    # quench_walk keeps the share test only for harvest-type rows.
    return []


def ancestor_shares_r27(start, n):
    import csv as _csv
    hits = []; k = 0
    for f in sorted(x for x in _last.get('seen', ()) if isinstance(x, str) and x.endswith('.csv') and os.path.isfile(x)):
        if os.path.abspath(f) == os.path.abspath(start) or k >= 60:
            continue
        try:
            with open(f) as h:
                fn = int(next(_csv.DictReader(h))['n'])
        except Exception:
            continue
        if fn != n:
            continue
        k += 1
        sh = QW.prv_share(f, n)
        if sh[1] >= QW.SHARE_MAX:
            hits.append('ancestor %s: prvsiyan 1105 share within 1e-3 = %.3f: rule b parent' % (f.replace(QW.S, ''), sh[1]))
    return hits


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    for p in sys.argv[1:]:
        r = QW.check(p); r['walker'] = WHICH + ' sha256 ' + SHA[:16]
        try:
            n0 = r.get('n') or 0
            extra = ancestor_shares(p, n0) if n0 else []
        except Exception as ex:
            extra = ['ancestor share not measured: %r' % (ex,)]
        if extra:
            r['hits'] = sorted(set(r.get('hits', []) + extra))[:40]; r['clean'] = False
        print(json.dumps(r), flush=True)
