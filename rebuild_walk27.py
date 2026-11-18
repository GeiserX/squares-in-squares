#!/usr/bin/env python3
"""rebuild_walk27.py: the round 27 source walk of the rebuild lane.

  rebuild_walk27.py START.csv [START.csv ...]      (one JSON line per start)

Round 27 lifted the Samanyu-dev rule: the layouts that match the Samanyu-dev/squares_in_squares seed
were found by our own code, so that ancestry is no reason to refuse a layout any more. This walk is the
walk of quench_walk.py (imported, unchanged) with that one check removed and the other checks kept:
  - kept: penguin069 joegun union (n 639 691 745 858 918), areebbb and harvest r22 rows of those n,
    the round 23 639, the 745/858 join, the round 23 forensics 980, the older forensics 918, the
    best-of-1105 file named in the record, CC BY-SA or ShareAlike text, the held 801, a sha-pinned parent
    that changed, a refusal or a withdrawal by a lane (reason shown), a gone file, no root.
  - removed: Samanyu-dev seed signals (POS, the seed names of NAMES, forensics_policy.classify_text),
    and the 0.55 prvsiyan distance cut (dropped in round 27).
  - added: the share test of round 27. The start is out when 0.4 or more of its squares lie within 1e-3
    of the prvsiyan best-of-1105 row of its n (harvest share_ac.share, best of 8 symmetries).
A refusal or a withdrawal whose text names only the Samanyu seed is listed under 'lifted', not as a hit.
Our own code; it imports quench_walk, quench_audit and the harvest share tools and changes none of them."""
import csv, json, os, re, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.path.insert(0, LANE + '/tools/harvest26')
import quench_walk as qw  # noqa: E402
import quench_audit  # noqa: E402
import audit_ac  # noqa: E402
from share_ac import share  # noqa: E402

S = qw.S
PRVZIP = S + 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
# the NAMES patterns of quench_walk that are not about the Samanyu seed
KEEP_NAMES = re.compile(r'squares-joegun-boxed|squares-verified-best-of-1105|CC BY-SA|ShareAlike|801h\b|held n = 801\b|held 801\b'
                        r'|areebbb[^|]{0,160}?donor n = (?:639|691|745|858|918)\b|per_n\.csv, donor n = (?:639|691|745|858|918)\b', re.I)
SEEDWORDS = re.compile(r'samanyu|seed|921-29e12ff3|921r25c921|near/921|local_bank|931h|811h|merged0|bare921|bare 921', re.I)
_prv = {}


def prv_share(start, n):
    if n not in _prv:
        got = audit_ac.read(PRVZIP, [n]) if os.path.isfile(PRVZIP) else {}
        _prv[n] = audit_ac.centres(got[n]) if len(got.get(n, [])) == n else None
    if _prv[n] is None:
        return None
    s = share(audit_ac.centres(list(csv.DictReader(open(start)))), _prv[n])
    return {'share1e6': round(s[0], 4), 'share1e3': round(s[1], 4), 'share1e2': round(s[2], 4), 'maxd': s[3]}


def check(start):
    try:
        n = int(next(csv.DictReader(open(start)))['n'])
    except Exception:
        return {'start': start, 'clean': False, 'hits': ['unreadable start']}
    texts, missing, seen, helds, refused = qw.walk(start, n)
    hits, lifted = [], []
    for label, t in texts:
        lab = (label if isinstance(label, str) else str(label)).replace(S, '')[:90]
        for m in qw.PIN.finditer(t):
            path, want = m.group(1), m.group(2).lower()
            path = path if path.startswith('/') else S + path
            have = qw.file_sha(path)
            if have and not have.startswith(want):
                hits.append('%s: changed since pinned: %s (sha256 %s, now %s)' % (lab, path.replace(S, ''), want[:16], have[:16]))
        c = qw.NEG.sub(' ', t)
        for m in KEEP_NAMES.finditer(c):
            hits.append('%s: %s' % (lab, c[max(0, m.start() - 60):m.end() + 30].replace('\n', ' ')))
        for rx in (getattr(qw, 'POS', None), getattr(qw, 'NAMES', None)):  # quench may set POS to None in round 27
            for m in (rx.finditer(c) if rx is not None else ()):
                if not KEEP_NAMES.search(m.group(0)):
                    lifted.append('%s: %s' % (lab, m.group(0)))
    alltext = '\n'.join(t for _, t in texts)
    for name, rx in quench_audit.RULES:
        m = re.search(rx, alltext, flags=re.I)
        if m:
            hits.append('%s: %s' % (name, alltext[max(0, m.start() - 60):m.end() + 20].replace('\n', ' ')))
    for r in refused:
        # quench_walk's REFUSE reads the word 'out' inside a log path (out-boxD-1/run.log) as a refusal: test the line
        # again with every path token removed, and keep only a real refusal word
        if not qw.REFUSE.search(re.sub(r'\S*/\S*', ' ', r.split(':', 3)[-1])):
            continue
        (lifted if SEEDWORDS.search(r) and not KEEP_NAMES.search(r) else hits).append('refused by its lane: ' + r[:300])

    def superseded(x):
        m = re.match(r'(take-[a-z0-9-]+-r%s/\d+\.csv) ' % qw.LIVE, x)
        return bool(m) and not any(m.group(1) == w for w, _ in qw.WITHDRAWN_LINES)
    gone = [x for x in missing if not x.startswith(('held ', 'held-chain ')) and not superseded(x)]
    for w, line in qw.WITHDRAWN_LINES:
        for f in seen:
            if isinstance(f, str) and f.endswith('/' + w) and os.path.isfile(f) and os.path.getmtime(f) <= qw.withdraw_time(line):
                (lifted if SEEDWORDS.search(line) and not KEEP_NAMES.search(line) else hits).append('withdrawn in a handoff line: ' + line[:300])
    if not helds and not qw.ROOT.search(alltext):
        hits.append('no root: no held reference and no public file reached')
    sh = prv_share(start, n)
    if sh and sh['share1e3'] >= 0.4:
        hits.append('prvsiyan share within 1e-3: %.3f (0.4 or more is out)' % sh['share1e3'])
    return {'start': start, 'n': n, 'clean': not hits and not gone, 'hits': sorted(set(hits))[:40], 'gone': sorted(set(gone))[:40],
            'lifted': len(set(lifted)), 'lifted_sample': sorted(set(lifted))[:6], 'prvsiyan_share': sh, 'files': len(seen),
            'helds': sorted('%d@%s' % h for h in helds)[:60]}


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    for p in sys.argv[1:]:
        print(json.dumps(check(p)), flush=True)
