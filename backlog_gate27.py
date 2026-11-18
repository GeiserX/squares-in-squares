#!/usr/bin/env python3
"""backlog_gate27: the source gate of the backlog lane in round 27 (avenues/backlog.md, Round 27).

Round 27 lifts the Samanyu-dev rule: the layouts that match the Samanyu-dev/squares_in_squares seed were found by
our own code first, so ancestry through that seed no longer refuses anything. The other rules stay:
  (a) n = 639, 691, 745, 858, 918 as they stand in take-harvest-r22 and the areebbb union (penguin069 upstream),
      and everything built from them; (c) the older forensics 918;
  (b) prvsiyan/squares-verified-best-of-1105 (CC BY-SA 4.0) and the held 801: a layout is out when 0.4 or more of
      its squares lie within 1e-3 of the prvsiyan row of that n (the share test of harvest share_ac.py and classfill
      prvsim26.py), or when its recorded ancestry names that file. The 0.55 and 0.5 distance cuts are dropped.
check(path) runs, on one per-n csv:
  1. floatsafe at 2.2e-11 (the certified score);
  2. the share test against every excluded layout audit_ac.excluded(n) knows (prvsiyan, and the rule a files);
  3. the round 26 assembler walk quench_walk.check (imported, never edited), with the hits that only name the
     Samanyu-dev seed, its bare files, the trees withdrawn for it, or the dropped distance cut taken out.
Every other hit (a gone file, a pinned parent changed, a producer refusal or withdrawal for another reason, a
CC BY-SA or penguin069 name, no root) still refuses.

  python -I backlog_gate27.py FILE [FILE ...]      one JSON line per file
"""
import csv, json, os, re, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.dont_write_bytecode = True
import floatsafe  # noqa: E402
csv.field_size_limit(1 << 30)
S = '$SCRATCH/bounties-squares'
HV = LANE + '/tools/harvest26'
if HV not in sys.path:
    sys.path.insert(0, HV)

# a hit that names only the Samanyu-dev seed, its files, the trees withdrawn for it, or the dropped distance cut
LIFT = re.compile(r'samanyu(?!1808)|921-29e12ff3|921r25c921|/near/921|near miss of n = 921|seed ?811|811h\b|931h\b|local_bank'
                  r'|927-reclassified|take-border-r2[34]/(?:735|790)\.csv|take-k123-r24/(?:968|489)\.csv|deferred-(?:certified-)?995'
                  r'|ba68ed617629eeb9|forensics_policy|\(below 0\.55?\)|max centre distance|bare seed|seed (?:365|503|504|804|983|861)\b'
                  r'|747r|rebuild audit', re.I)
# words that keep a hit even when it also names the seed: the rules that still hold
KEEP = re.compile(r'prvsiyan|best-of-1105|CC BY-SA|ShareAlike|penguin069|joegun|areebbb|share(?:d)? (?:of|within)|801h|held 801'
                  r'|rule ?b\b|rule ?a\b|copy of', re.I)
OUTN = (639, 691, 745, 858, 918)
_EXC = {}

# round 29 (main -> all 07:34:54Z, a trap found by the round 28 skeptic): quench_audit's rule 'r22 745/858 join' matched
# take-forensics-r23/work/donors/(745|858)- by directory name and so caught the readers donors 858-c82b5be2 and
# 858-bc8896e9 (up1from799) and 858-c43df5d7 (family r23); only 858-ec97a452 (the k123 r22 745r-858r join) and
# 745-64c4b4f8 are the join. The rule is narrowed here, in memory, for every walk this process runs (quench_walk and
# the ctl's deep_check read quench_audit.RULES at call time); quench_audit.py itself is not edited.
NARROW_JOIN = r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8'
if int(os.environ.get('BACKLOG_ROUND', '27')) >= 29:
    import quench_audit as _qa  # noqa: E402
    _qa.RULES = [(nm, NARROW_JOIN if nm == 'r22 745/858 join' else rx) for nm, rx in _qa.RULES]


REF = os.environ.get('BACKLOG_EXCL_REF', S + '/take-backlog-r27/work/excl-ref.pkl')


def excluded(n):
    """The excluded layouts of n as centred centres: the prvsiyan best-of-1105 row and the rule a files (the layouts
    audit_ac.excluded(n) reads), from REF, a one-pass cache of those files (scripts/mkref.py) when it exists."""
    if not _EXC and os.path.exists(REF):
        import pickle
        import numpy as np
        for m, v in pickle.load(open(REF, 'rb')).items():
            _EXC[m] = [(l, a - (a.min(0) + a.max(0)) / 2) for l, a in v]
        _EXC['ref'] = True
    if n not in _EXC:
        if _EXC.get('ref'):
            return []
        import audit_ac
        _EXC[n] = [(l, audit_ac.centres(r)) for l, r in audit_ac.excluded(n)]
    return _EXC[n]


def share(a, b):
    """share_ac.share of harvest (tools/harvest26/share_ac.py), copied so a box needs no harvest module: over the 8
    symmetries, the shares of a's centres within 1e-6, 1e-3 and 1e-2 of b's nearest centre, and the max distance."""
    import numpy as np
    best = None
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                c = a[:, ::-1] if sw else a
                c = c * np.array([sx, sy])
                d = np.sqrt(((c[:, None, :] - b[None, :, :]) ** 2).sum(-1)).min(1)
                r = (float((d < 1e-6).mean()), float((d < 1e-3).mean()), float((d < 1e-2).mean()), float(d.max()))
                if best is None or r[1:3] > best[1:3]:
                    best = r
    return best


def shares(n, rows):
    """[(label, share within 1e-6, within 1e-3, max distance)] against each excluded layout of n."""
    import numpy as np
    a = np.array([[float(r['x']), float(r['y'])] for r in rows])
    c = a - (a.min(0) + a.max(0)) / 2
    out = []
    for l, b in excluded(n):
        if len(b) != len(c):
            continue
        s = share(c, b)
        out.append((l, s[0], s[1], s[3]))
    return out


# a measurement that names the prvsiyan file only as the layout a share or a distance was measured to: the share test
# on the result decides instead (modules records 'prvsiyan 1105 (CC BY-SA) share 0.005 within 1e-3')
MEAS = re.compile(r'(?:prvsiyan|CC BY-SA)[^;|]{0,60}(?:share|distance|=\s*[0-9.]+)|share[^;|]{0,60}(?:prvsiyan|CC BY-SA)', re.I)
FILEREF = re.compile(r'squares-verified-best-of-1105/|best-of-1105\.csv|data\.zip|submission\.csv', re.I)


def lifted(h):
    if h.startswith(('gone: ', 'no root')):
        return False
    if int(os.environ.get('BACKLOG_ROUND', '27')) >= 28 and h.startswith('withdrawn in a handoff line') \
            and re.search(r'share', h, re.I) and not re.search(r'harvest|public|untraced|unresolved|trace|licen|notice|499|916|918|639', h, re.I):
        return True          # main -> all 00:19:03Z: a withdrawal for a prvsiyan share of our own layout or its ancestor is void
    if 'changed since pinned' in h:
        return False
    if int(os.environ.get('BACKLOG_ROUND', '27')) >= 28 and 'rule b on a harvest-type row' in h:
        return False         # quench_walk round 28 applies the share test to harvest-type and rootless trees itself
    if MEAS.search(h) and not FILEREF.search(h) and not re.search(r'penguin069|joegun|areebbb', h, re.I):
        return True
    return bool(LIFT.search(h)) and not KEEP.search(h)


def quick(n, rows):
    """The side score of the layout as it stands (bounding box of the turned unit squares), no overlap check."""
    import math
    import numpy as np
    a = np.array([[float(r['x']), float(r['y']), float(r['angle'])] for r in rows])
    h = 0.5 * (np.abs(np.cos(a[:, 2])) + np.abs(np.sin(a[:, 2])))
    side = max((a[:, 0] + h).max() - (a[:, 0] - h).min(), (a[:, 1] + h).max() - (a[:, 1] - h).min())
    return side / math.sqrt(n) - 1


# round 28 (main -> all 00:19:03Z): a share match with the prvsiyan 1105 row refuses only a row whose first source is a
# public notebook or dataset we fetched (a harvest-type row); our own layouts and their descendants are ours. A row
# whose recorded ancestry names the prvsiyan file itself stays out (the walk hits and the deep25 bysa signal).
PUBLIC_FIRST = re.compile(r'take-harvest-r\d+|/data/nb/|/public\d*/|^\s*public |harvested|kaggle\.com|kaggle notebook', re.I)
ROUND = int(os.environ.get('BACKLOG_ROUND', '27'))


def record_text(path, limit=3000):
    """The first words of the file's own record: its sidecar json, or its take.tsv row when it is a per-n file of a
    take dir. The lineage starts there, so a public first source shows in it."""
    for side in (path + '.json', path[:-4] + '.json', path + '.origin.json'):
        if os.path.exists(side):
            return open(side, errors='replace').read()[:limit]
    m = re.match(re.escape(S) + r'/(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$', path)
    if m and os.path.exists(S + '/' + m.group(1) + '/take.tsv'):
        for row in csv.DictReader(open(S + '/' + m.group(1) + '/take.tsv'), delimiter='\t'):
            if row.get('n') == m.group(2):
                return (row.get('source') or '')[:limit]
    return ''


def public_first(path, text=None):
    return bool(PUBLIC_FIRST.search(path) or PUBLIC_FIRST.search(text if text is not None else record_text(path)))


def check(path, n=None, rows=None, walk=True, cert=True, share=True):
    """cert=False skips floatsafe (the box worker certifies the result): the score is the side as it stands."""
    path = os.path.abspath(path)
    if rows is None:
        rows = list(csv.DictReader(open(path)))
    n = n or int(rows[0]['n'])
    rows = [r for r in rows if int(r.get('n', n)) == n]
    if cert:
        _, fr, sc, e = floatsafe.work((n, rows))
    else:
        fr, sc, e = rows, quick(n, rows), None
    out = dict(path=path, n=n, score=sc, eps=e, ok=False, hits=[], lifted=[], shares=[])
    if fr is None:
        out['hits'].append('floatsafe failed: %s' % e); return out
    sh = shares(n, fr) if share else []
    out['shares'] = [(l[:40], round(a, 4), round(b, 4), round(d, 4)) for l, a, b, d in sh]
    pub = public_first(path) if ROUND >= 28 else True
    out['public_first'] = pub
    for l, a, b, d in sh:
        if b >= 0.4:
            (out['hits'] if pub else out['lifted']).append('share test: %.3f of the squares within 1e-3 of the excluded layout %s%s'
                                                          % (b, 'prvsiyan 1105 row' if 'prvsiyan' in l else 'rule a file',
                                                             '' if pub else ' (not applied: no public first source)'))
    if walk:
        import quench_walk
        r = quench_walk.check(path)
        out['files'] = r.get('files')
        for h in r['hits']:
            (out['lifted'] if lifted(h) else out['hits']).append(h)
    out['ok'] = not out['hits']
    return out


def note(res):
    sh = '; '.join('%s share 1e-3 %.3f' % ('prvsiyan 1105 row' if 'prvsiyan' in l else 'rule a file', b) for l, a, b, d in res['shares'])
    return ('gate27 (backlog_gate27.py): floatsafe %.17g; share test (0.4 at 1e-3): %s; assembler walk quench_walk.check: '
            '%d files, %d hits kept, %d lifted under the round 27 rule (Samanyu-dev seed ancestry allowed)'
            % (res['score'], sh or 'no excluded layout of this n', res.get('files') or 0, len(res['hits']), len(res['lifted'])))


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    for p in sys.argv[1:]:
        try:
            print(json.dumps(check(p)), flush=True)
        except Exception as ex:
            print(json.dumps(dict(path=p, ok=False, hits=['error %s' % ex])), flush=True)
