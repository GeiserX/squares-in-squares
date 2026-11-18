"""Round 28 source checks of the soft lane, on top of provenance.trace.

Main session rule change of 00:19:03Z on 2026-11-15: our own layouts are ours (the held 801, every Samanyu-seed layout
including seeds 503 and 983, and what was built from them). A share match with prvsiyan 1105 is never a reason to refuse
them, and what was withdrawn only for a share match is open again. The share test stays only for rows whose first source
is a public notebook or dataset we fetched; a row whose recorded ancestry names the prvsiyan 1105 file stays out (the
FORBIDDEN markers of provenance.r26_check). So: share-only WITHDRAW lines are skipped, publish_check no longer runs the
ancestor and seed share gates, and public_first() says when the output share test of ctl.prv_share_out still applies.

  withdrawn_in(proof, path)       a reason when the trace names a withdrawn file, or a byte copy of one, else None
  publish_check(proof, path, W)   withdrawn_in, then the prvsiyan share test over every complete per-n csv the trace names
                                  and over every original seed it names (seeds/merged0.csv), else None
  python -I r28check.py control   the positive and negative controls

Withdrawn files come from the WITHDRAW lines of handoff-r27.log and handoff-r28.log (a REINSTATE or "withdrawal lifted"
line of the same file or hash cancels it), plus the files the round 28 brief names. A file at a withdrawn path counts as
withdrawn only when it is not newer than the withdrawal line (a lane may write a new file at the same path). A byte copy
counts by sha256 (full hash or a prefix of 12 or more hex digits in the line, or the hash of the named file).
The share test is rule b of round 26: a layout is out when 0.4 or more of its square centres lie within 1e-3 of the
prvsiyan best-of-1105 row of the same n, under the 8 symmetries of the square, centred on the bounding box.
"""
import calendar
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile

S = '$SCRATCH/bounties-squares'
LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log', S + '/handoff-r29.log', S + '/handoff-r30.log', S + '/handoff-r31.log',
        S + '/handoff-r32.log', S + '/handoff-r33.log')   # round 33 adds its own log
PRV = S + '/take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
SEEDS = S + '/seeds/merged0.csv'
# Named by the round 28 brief: invent withdrew both n910 near files and their descendants at 23:50:47Z.
BRIEF = []   # the brief's 684 donor was withdrawn for a share match only: open again under the rule change of 00:19:03Z
LIFTED_SINCE = 1794702000.0   # 00:20:00Z on 2026-11-15: a share-only withdrawal before this time is skipped
# A WITHDRAW line that names one of these reasons stays in force even when it also mentions a share.
STILL_OUT = re.compile(r'unresolved|source trace|lineage|penguin|CC BY-SA|SOURCE_NOTICES|names squares-verified|'
                       r'take-harvest-r26 499|n=499|n916|n639|n918', re.I)
SHARE_MAX = 0.4
# Round 30: main's 12:40:55Z ruling voids the public-first held-ancestor gate of forensics (08:32Z r29 on 376) and the
# withdrawals made under it. The 08:36Z r29 batch (154 near files, 'a recorded public-first ancestor fails the
# allowed-source check') is that gate applied to near files; forensics r30 builds on those files again (752 from 458).
VOID_R30 = re.compile(r'public-first ancestor fails the allowed-source check|public-first held ancestors', re.I)
csv.field_size_limit(1 << 28)

_W = {'key': None}
_SHA = {}
_SHARE = {}
_PRV = {}
_BIG = {}


def _sha(path):
    try:
        st = os.stat(path)
    except OSError:
        return None
    k = (path, st.st_mtime_ns, st.st_size)
    if k not in _SHA:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for b in iter(lambda: f.read(1 << 20), b''):
                h.update(b)
        _SHA[k] = h.hexdigest()
    return _SHA[k]


def _when(line):
    m = re.match(r'(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)', line)
    if not m:
        return time.time()
    return calendar.timegm(time.strptime(m[1] + ' ' + m[2], '%Y-%m-%d %H:%M:%S'))


def withdrawals():
    """{'paths': {path: time}, 'hashes': set of hex prefixes} from the logs, cached on their sizes."""
    key = tuple(os.path.getsize(p) if os.path.exists(p) else -1 for p in LOGS)
    if _W['key'] == key:
        return _W['val']
    paths, hashes, lifted_p, lifted_h = {}, set(), set(), set()
    for lp in LOGS:
        if not os.path.exists(lp):
            continue
        for line in open(lp, errors='replace'):
            lifts = re.search(r'REINSTATE|withdrawal lifted|lifted for this exact hash', line)
            if not lifts and 'WITHDRAW' not in line:
                continue
            ps = [p.rstrip('.,;)') for p in re.findall(r'$DATA/[^\s,;<>()]+\.csv', line)]
            hs = {h.lower() for h in re.findall(r'(?<![0-9a-fA-F])[0-9a-f]{12,64}(?![0-9a-fA-F])', line)}
            if lifts:
                lifted_p.update(ps); lifted_h.update(hs); continue
            t = _when(line)
            if re.search(r'share', line, re.I) and not STILL_OUT.search(line):
                continue          # rule change of 00:19:03Z: a share match never withdraws our own layouts
            if VOID_R30.search(line):
                continue          # main 12:40:55Z ruling (round 30): the public-first held-ancestor gate is void
            for p in ps:
                paths[p] = min(paths.get(p, t), t)
            hashes.update(hs)
    for p, h, t in BRIEF:
        paths[p] = min(paths.get(p, t), t); hashes.add(h)
    for p in lifted_p:
        paths.pop(p, None)
    hashes -= lifted_h
    for p in list(paths):
        h = _sha(p)
        if h and os.path.getmtime(p) <= paths[p] + 60:
            hashes.add(h)
    val = dict(paths=paths, hashes=hashes)
    _W['key'] = key; _W['val'] = val
    return val


def _pairs(proof, path=None):
    """(path, n) of every dict in the trace that names both, and the input."""
    out = []
    def walk(v):
        if isinstance(v, dict):
            q = v.get('path')
            if isinstance(q, str) and isinstance(v.get('n'), int):
                out.append((q, v['n']))
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(proof)
    if path:
        m = re.search(r'(\d+)', os.path.basename(path))
        n = proof.get('n') if isinstance(proof, dict) and isinstance(proof.get('n'), int) else None
        out.append((path, n))
    seen = set(); uniq = []
    for p, n in out:
        if (p, n) not in seen:
            seen.add((p, n)); uniq.append((p, n))
    return uniq


def _all_paths(proof, path=None):
    text = json.dumps(proof, default=str) + ' ' + (path or '')
    return set(p.rstrip('.,;)') for p in re.findall(r'$DATA/[^\s,;<>()"\\]+\.csv', text))


# Round 29 (07:10Z): the round 28 assembler marked the r24 donor 800-7a2b family OUT (a 639 and r23 858-c82b5be2 donor chain);
# backlog's walk found it under the forensics r24 803 donor that our r29 747 start used. A start whose proof or input record
# names one of these files is refused at admission, before box time is spent (the publication walk gate stays).
# 07:40Z: emptied. main's 07:34:54Z note: that OUT mark rested on a false match of quench_audit's 745/858 rule (858-c82b5be2
# is a readers up1from799 donor, not the join), and main counts 540 and 743 of the family as clean.
TAINTED = ()
# Round 30 (main 13:32:00Z clarification): a tree that takes a withdrawn public-first file directly stays out even when it
# also reaches held rows. These are the files main named; a held row of the same n reaches us as the held file path.
DIRECT_OUT = ('take-harvest-r26/695.csv', 'take-harvest-r26/work/collector/certified/5a4c0cdb',
              'take-forensics-r22/work/donors/799-986b3b6d')


def tainted_in(proof, path=None):
    text = json.dumps(proof, default=str)
    if path and os.path.exists(path + '.json'):
        try:
            text += open(path + '.json').read()
        except OSError:
            pass
    for m in TAINTED:
        if m in text:
            return 'round 29: the r24 donor 800-7a2b family (r28 assembler OUT) in the record: ' + m
    for m in DIRECT_OUT:
        if m in text:
            return 'round 30 (main 13:32:00Z): a withdrawn public-first file taken directly: ' + m
    return None


def withdrawn_in(proof, path=None):
    why = tainted_in(proof, path)
    if why:
        return why
    w = withdrawals()
    for p in sorted(_all_paths(proof, path)):
        if p in w['paths']:
            if not os.path.exists(p) or os.path.getmtime(p) <= w['paths'][p] + 60:
                return 'withdrawn file in ancestry: ' + p
        h = _sha(p) if os.path.exists(p) else None
        if h and any(h.startswith(x) for x in w['hashes']):
            return 'byte copy of a withdrawn file in ancestry: %s (sha256 %s)' % (p, h[:16])
    return None


# ------------------------------------------------------------------------------------------------ the share test
def _rows_of_text(text, n):
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        k = {str(a).strip().lower(): v for a, v in r.items()}
        if 'x' not in k or 'y' not in k:
            continue
        m = str(k['n']).lstrip('s') if 'n' in k else str(k.get('id', '')).split('_')[0]
        if m.isdigit() and int(m) == n:
            out.append((float(str(k['x']).lstrip('s')), float(str(k['y']).lstrip('s'))))
    return out


def _rows(path, n):
    if path.endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist(), key=lambda name: name != 'submission.csv'):
                if name.endswith('.csv'):
                    r = _rows_of_text(z.read(name).decode('utf-8-sig'), n)
                    if r:
                        return r
        return []
    if os.path.getsize(path) > 4e6:
        # a whole-file csv (held files, seeds): index its lines by n once per file version
        key = (path, os.stat(path).st_mtime_ns)
        if key not in _BIG:
            idx = {}
            with open(path, errors='replace') as f:
                head = f.readline()
                cols = [c.strip().lower() for c in head.split(',')]
                i = cols.index('n') if 'n' in cols else None
                for line in f:
                    k = line.split(',', i + 1)[i] if i is not None else line.split('_', 1)[0]
                    idx.setdefault(k.lstrip('s').lstrip('0') or '0', []).append(line)
            _BIG.clear(); _BIG[key] = (head, idx)
        head, idx = _BIG[key]
        return _rows_of_text(head + ''.join(idx.get(str(n), [])), n)
    return _rows_of_text(open(path, errors='replace').read(), n)


def _prv(n):
    if n not in _PRV:
        _PRV[n] = _rows(PRV, n)
    return _PRV[n]


def share(n, xy):
    import numpy as np
    from scipy.spatial import cKDTree
    ref = np.asarray(_prv(n), dtype=float)
    a = np.asarray(xy, dtype=float)
    if len(ref) != n or len(a) != n:
        return 0.0
    a = a - (a.min(0) + a.max(0)) / 2; b = ref - (ref.min(0) + ref.max(0)) / 2
    tree = cKDTree(b); best = 0.0
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                x = (a[:, ::-1] if sw else a) * [sx, sy]
                best = max(best, float((tree.query(x)[0] < 1e-3).mean()))
    return best


def file_share(path, n):
    h = _sha(path)
    if h is None:
        return None
    k = (h, n)
    if k not in _SHARE:
        try:
            r = _rows(path, n)
            _SHARE[k] = share(n, r) if len(r) == n else None
        except (OSError, ValueError, KeyError, UnicodeDecodeError, zipfile.BadZipFile):
            _SHARE[k] = None
    return _SHARE[k]


def seeds_of(proof):
    text = json.dumps(proof, default=str)
    out = set()
    for a, b in re.findall(r'original seed:\s*n\s*=\s*(\d+)\s+of|n\s*=\s*(\d+)\s+of\s+(?:Samanyu-dev/squares_in_squares|franciscouzo/square-packing)', text, re.I):
        out.add(int(a or b))
    for m in re.findall(r'seeds n=([\d,]+)', text):
        out.update(int(x) for x in m.split(',') if x)
    return sorted(out)


def public_first(proof, path=None):
    """True when the layout comes from a public notebook or dataset we fetched: the input or a file of its trace is a
    harvest take or near file, or a fetched public file (the share test still applies to those rows)."""
    return any(re.search(r'/take-harvest-r\d+/|/work/public/|/near-pub/', p) for p in _all_paths(proof, path))


def publish_check(proof, path, work=None, log=True, shares=False):
    why = withdrawn_in(proof, path)
    if why or not shares:
        if log and work:
            with open(work + '/r28check.tsv', 'a') as f:
                f.write('%s\t%s\t%s\tpublic_first=%s\n' % (time.strftime('%H:%M:%SZ', time.gmtime()), path, why or 'clean',
                                                         public_first(proof, path)))
        return why
    measured = []
    for p, n in _pairs(proof, path):
        if n is None or not p.endswith(('.csv', '.zip')) or not os.path.exists(p):
            continue
        v = file_share(p, n)
        measured.append((p, n, v))
        if v is not None and v >= SHARE_MAX:
            why = 'ancestor n=%d %s has prvsiyan 1105 share %.3f >= 0.4' % (n, p, v)
            break
    if not why:
        for k in seeds_of(proof):
            v = file_share(SEEDS, k)
            measured.append((SEEDS, k, v))
            if v is not None and v >= SHARE_MAX:
                why = 'original seed n=%d (seeds/merged0.csv) has prvsiyan 1105 share %.3f >= 0.4' % (k, v)
                break
    if log and work:
        with open(work + '/r28check.tsv', 'a') as f:
            f.write('%s\t%s\t%s\t%s\n' % (time.strftime('%H:%M:%SZ', time.gmtime()), path, why or 'clean',
                                          '; '.join('%d:%s:%s' % (n, os.path.basename(p), 'na' if v is None else '%.3f' % v)
                                                    for p, n, v in measured)))
    return why


def control():
    donor = S + '/take-forensics-r24/work/donors/684-6d78315914dc85da2cb4.csv'
    print('share-only withdrawn donor 684 in a trace (open again):', withdrawn_in(dict(path='/x/910.csv', n=910, parent=dict(path=donor, n=684))))
    w8 = S + '/take-forensics-r28/near/798-rect.csv'
    print('k123 798 tree (share-only, open again):', withdrawn_in(dict(path=w8, n=798, parent=dict(path=S + '/take-forensics-r27/work/feed/take-k123-r27/798-92c67427e245f48aa5a79709.csv', n=798))))
    h9 = S + '/take-harvest-r27/639.csv'
    print('harvest 639 (unresolved trace, still out):', withdrawn_in(dict(path='/x/1.csv', n=639, parent=dict(path=h9, n=639))))
    print('donor 684 share:', file_share(donor, 684))
    print('seed shares 503 983 861 811:', [file_share(SEEDS, k) for k in (503, 983, 861, 811)])
    fake = dict(path='/x/699.csv', n=699, source='original seed: n = 503 of Samanyu-dev/squares_in_squares')
    print('seed 503 trace, share gates on:', publish_check(fake, None, log=False, shares=True))
    print('seed 503 trace, round 28 rule (share gates off):', publish_check(fake, None, log=False))
    print('public_first harvest input:', public_first({}, S + '/take-harvest-r28/499.csv'), 'forensics input:',
          public_first({}, S + '/take-forensics-r28/near/641-rect.csv'))
    print('clean trace (no files):', publish_check(dict(path='/x/1.csv', n=1), None, log=False))
    w = withdrawals()
    print('withdrawn paths %d hashes %d' % (len(w['paths']), len(w['hashes'])))


if __name__ == '__main__':
    if sys.argv[1:] == ['control']:
        control()
