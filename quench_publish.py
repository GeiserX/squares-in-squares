#!/usr/bin/env python3
"""quench: write the take dir from the finished quench jobs.

Usage: quench_publish.py TAKEDIR BAR.tsv SCRATCH [ROUND]
  TAKEDIR/work/jobs/<id>/  result.json (quench_once.py take), final.csv,
                           source.txt and licence.txt (written at queue time)
  BAR.tsv                  quench_bar.py output; the rule is score < bar - 1e-10
  SCRATCH                  the dir holding the live take-*-ROUND dirs
  ROUND                    r25 (the default) or r26: the live takes a row must beat

Writes <n>.csv for each kept n, then take.tsv by rename (n, held, new, gain,
source, licence, other_ROUND), and prints the sum against the bar and the sum
beyond the other live takes of the round.
"""
import csv, glob, json, math, os, shutil, sys, time

csv.field_size_limit(1 << 30)


def withdraw_key(scratch):
    """The number of withdrawal lines in the live handoff logs (a new one invalidates every cached clean walk)."""
    import re
    k = 0
    for h in sorted(glob.glob(scratch + '/handoff-r2[7-9].log') + glob.glob(scratch + '/handoff-r3[0-9].log')):  # round 30: r3x too
        k += sum(1 for l in open(h, errors='replace') if re.search(r'withdr|withh[eo]ld|reclassif', l, re.I))
    return k


def walk_ok(job, scratch):
    """True when the current quench_walk.py reads the job's start copy as clean; cached in walk-current.json."""
    import hashlib, re
    lane = os.path.dirname(os.path.abspath(__file__))
    ver = hashlib.sha256(open(lane + '/quench_walk.py', 'rb').read()).hexdigest()[:16]
    mark = job + '/walk-current.json'
    if os.path.exists(mark):
        m = json.load(open(mark))
        # A cached refusal stands. A cached clean read is walked again: a lane can withdraw a file in the
        # tree after the job was walked (harvest 988-pubfq at 16:36 UTC, under our published 926).
        if m.get('walk_sha') == ver and not m.get('clean'):
            return False
        # Round 27: boxA ran at load 100 and one walk took minutes, so a clean read is kept for 60 minutes
        # while no new withdrawal line appears in the live handoff log; any new line walks it again.
        if (m.get('walk_sha') == ver and m.get('clean') and m.get('wkey') == withdraw_key(scratch)
                and time.time() - m.get('t', 0) < 3600):
            return True
    src = open(job + '/source.txt').read()
    # r37: a new start record of the same bytes (rule 6n) sits in starts/<sha16>-rK/; r38 (rule 6e): the start may be named by its
    # absolute path (os.path.join below keeps an absolute path as it is)
    st = re.search(r'of ((?:/\S*/)?take-[a-z0-9-]+-r\d+/work/starts/[0-9a-f]{16}(?:-r\d+)?/\S+?\.csv) ', src)
    if not st:
        return False  # no start copy: the record cannot be walked again
    sys.path.insert(0, lane)
    if 'quench_walk' not in sys.modules:
        v0 = hashlib.sha256(open(lane + '/quench_walk.py', 'rb').read()).hexdigest()[:16]
        import quench_walk as qw
        qw.LOADED_SHA = v0 if v0 == hashlib.sha256(open(lane + '/quench_walk.py', 'rb').read()).hexdigest()[:16] else 'changed'
    import quench_walk as qw
    # Round 28 trap: a publish that imported the walk before an edit labelled the old code's clean read with the
    # new sha (416 at 00:42Z). A walk whose code is not the file on disk now is not trusted and not cached.
    if getattr(qw, 'LOADED_SHA', None) != ver:
        return False
    # Round 36 (rule 6g): walk to 100000 files; a walk that still hits its cap is not proof and does not publish
    cap = int(os.environ.get('QUENCH_WALK_CAP', '100000'))
    w = qw.check(os.path.join(scratch, st.group(1)), cap=cap)
    if w['clean'] and w.get('capped'):
        w['clean'] = False
        w['hits'] = ['walk capped at %d files: the tree beyond the cap is unread (rule 6g)' % cap] + w['hits']
    # Round 27: a start whose only hits are answered in TAKEDIR/work/resolved/<sha256>.json (a gone path whose
    # version in the tree is pinned as a byte copy, and the withdrawal that cites only that path) passes while
    # every pinned file still has its sha256 and the walk finds no other hit.
    res = os.path.join(os.path.dirname(os.path.dirname(job)), 'resolved',
                       hashlib.sha256(open(os.path.join(scratch, st.group(1)), 'rb').read()).hexdigest() + '.json')
    resolved = False
    if not w['clean'] and os.path.exists(res):
        r = json.load(open(res))
        pins_ok = all(os.path.exists(p) and hashlib.sha256(open(p, 'rb').read()).hexdigest() == s
                      for p, s in r['pins'].items())
        resolved = pins_ok and all(any(h.startswith(a) for a in r['allow']) for h in w['hits'])
        if resolved:
            w['clean'] = True
    json.dump({'walk_sha': ver, 'clean': w['clean'], 'helds': w.get('helds', []), 'hits': w['hits'][:6],
               'resolved': res if resolved else None,
               'files': w.get('files'), 'capped': w.get('capped'), 't': time.time(), 'wkey': withdraw_key(scratch)}, open(mark + '.tmp', 'w'))
    os.replace(mark + '.tmp', mark)
    if not w['clean']:
        open(job + '/withdrawn', 'w').write('the current quench_walk.py (sha %s) reads the start as not clean: %s\n'
                                            % (ver, '; '.join(h[:160] for h in w['hits'][:3])))
    return bool(w['clean'])


def main():
    take, bar_tsv, scratch = sys.argv[1:4]
    rnd = sys.argv[4] if len(sys.argv) > 4 else 'r25'
    bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(bar_tsv), delimiter='\t')}
    other = {}
    for t in glob.glob(scratch + '/take-*-%s/take.tsv' % rnd):
        if os.path.dirname(os.path.abspath(t)) == os.path.abspath(take):
            continue
        try:
            for r in csv.DictReader(open(t), delimiter='\t'):
                n, s = int(r['n']), float(r['new'])
                if n not in other or s < other[n]:
                    other[n] = s
        except (OSError, ValueError, KeyError):
            continue
    cands = {}
    import hashlib as _h
    ver = _h.sha256(open(os.path.dirname(os.path.abspath(__file__)) + '/quench_walk.py', 'rb').read()).hexdigest()[:16]
    for rj in glob.glob(take + '/work/jobs/*/result.json'):
        job = os.path.dirname(rj); r = json.load(open(rj)); n = r['n']; s = r['final_score']
        if os.path.exists(job + '/withdrawn') and r.get('counts') and os.path.exists(job + '/walk-current.json'):
            # round 31: a refusal by an older walk is read again by the current one (the r31 walk changes freed rows the
            # older walks refused, harvest 588 among them); a withdrawn mark written by hand has no walk-current.json
            try:
                if json.load(open(job + '/walk-current.json')).get('walk_sha') != ver and 'quench_walk.py (sha' in open(job + '/withdrawn').read():
                    os.replace(job + '/withdrawn', job + '/withdrawn.old')
            except (OSError, ValueError):
                pass
        if not os.path.exists(job + '/source.txt') or os.path.exists(job + '/withdrawn'):
            continue
        if (os.path.basename(job).startswith('fx-') or 'that the harvest lane wrote' in open(job + '/source.txt').read()
                or os.environ.get('QUENCH_AUDIT_ALL')) and not os.path.exists(job + '/audit-ok'):
            # round 32 (QUENCH_AUDIT_ALL): every job waits for the output gate (xaudit32.py), which runs the assembler's frozen
            # share31 measure on each public-first row and marks a held-ancestry row audit-ok with no share test (rule 2)
            # round 31: a cross-n result, and every row whose start is or descends from a harvest file, goes out only after
            # the harvest31 policy.audit of its own rows (rule 3 reads the row: our fq of harvest's public 851, 911 and 972
            # read 0.463, 0.490 and 0.453 at 1e-2 while their public starts read under 0.4)
            continue
        if not s < bar[n] - 1e-10:
            continue
        cands.setdefault(n, []).append((s, job))
    # The best job of each n is kept only when the current quench_walk.py reads its start copy as clean.
    # The walk changed during the round (a held reference written as JSON was missed until 14:40 UTC),
    # so a job walked by an older walk is walked again here before its row goes out.
    best = {}
    for n in cands:
        for s, job in sorted(cands[n]):
            if walk_ok(job, scratch):
                best[n] = (s, job)
                break
    rows = []
    for n in sorted(best):
        s, job = best[n]
        shutil.copyfile(job + '/final.csv', '%s/%d.csv.tmp' % (take, n))
        os.replace('%s/%d.csv.tmp' % (take, n), '%s/%d.csv' % (take, n))
        src = open(job + '/source.txt').read().strip().replace('\t', ' ').replace('\n', ' ')
        lic = open(job + '/licence.txt').read().strip().replace('\t', ' ').replace('\n', ' ')
        rows.append((n, bar[n], s, src, lic, other.get(n)))
    # A row another take has beaten leaves take.tsv. Its per-n file moves to near/ with its last row as
    # the sidecar, because other lanes may have built on it and named it.
    last = {}
    if os.path.exists(take + '/take.tsv'):
        for r in csv.DictReader(open(take + '/take.tsv'), delimiter='\t'):
            last[int(r['n'])] = r
    for p in glob.glob(take + '/[0-9]*.csv'):
        n0 = int(os.path.basename(p)[:-4])
        if n0 not in best:
            import hashlib
            h = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
            os.makedirs(take + '/near', exist_ok=True)
            q = '%s/near/%d-superseded-%s.csv' % (take, n0, h)
            # round 32: prune by copy, never by move (twoshort r31 lesson: a row of another lane can name our per-n path);
            # the per-n file stays in place, out of take.tsv, until a later row of its n replaces it
            if os.path.exists(q):
                continue
            shutil.copyfile(p, q)
            r = last.get(n0, {})
            json.dump({'n': n0, 'score': r.get('new'), 'source': r.get('source'), 'licence': r.get('licence'),
                       'was': p, 'record': 'the take.tsv row of this file when it left the take'},
                      open(q + '.json', 'w'), indent=1)
    with open(take + '/take.tsv.tmp', 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\tother_%s\n' % rnd)
        for n, b, s, src, lic, o in rows:
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\t%s\n' % (n, b, s, b - s, src, lic, '' if o is None else repr(o)))
    os.replace(take + '/take.tsv.tmp', take + '/take.tsv')
    gain = math.fsum(b - s for n, b, s, *_ in rows)
    beyond = math.fsum(max(0.0, min(b, o if o is not None else b) - s) for n, b, s, _, _, o in rows)
    print(json.dumps({'kept': [r[0] for r in rows], 'gain': gain, 'beyond_other_' + rnd: beyond}))


if __name__ == '__main__':
    main()
