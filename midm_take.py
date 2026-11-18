#!/usr/bin/env python3
"""midm: certify the raw results of the midm tools the lane's way and write the take dir.

The rule is the one of methods_take.py: floatsafe.work (2.2e-11 clearance, the official metric as written and
after a pandas read), and a result is kept only when its score is below the held score by more than 1e-10.
Each per-n csv is written first; take.tsv is then replaced by a rename.

Usage: midm_take.py HELD_DETAILS.csv TAKEDIR RESULTS_DIR RAWDIR [RAWDIR ...] [--stage DIR]
  RESULTS_DIR  the lane's results/ dir: its round*-best and harvest-best tables name the source and licence
               of the held packing of each n
  RAWDIR       files <n>-<tag>.csv. The tag names the method (kick, lkick, drop1, drop2, grow1, seed, best, sq, ftmc);
               a tag that starts with fq+ is the fq quench of the certified file of another tag
  --stage DIR  write the per-n files and take.tsv there instead of TAKEDIR (the first pass, before the fq quench)
Env MIDM_R16 names a table (n, score, dir, source, licence) of round 16 files of other lanes. A result whose raw
name ends in s10 started from such a file: it is kept only when it is also more than 1e-10 below that file's score,
and take.tsv names that file as its start. MIDM_R17 names the same kind of table for the round 17 files of other
lanes (raw names that end in s17), and MIDM_R18 for a later snapshot of those files (s18). MIDM_SNAPS names a dir
that holds one table r<K>.tsv for each later snapshot (raw names that end in s<K>, K from 19 up). A per-n csv of an
earlier pass that this pass no longer keeps is removed.
Env MIDM_HELD2 names the details.csv of a later held file (round 16). A result is kept only when it is also more
than 1e-10 below that file's score for its n, whatever it started from. The held column stays the first file's.
Env MIDM_LIVE names a glob (or several, split by spaces) of the take dirs of the other lanes of the round (take-*-r17). A result is kept only
when it is also more than 1e-10 below the lowest score those dirs hold for its n at the time of the call. A row
that TAKEDIR/take.tsv already holds at the same score stays: it was certified before the other lane's file came.
Env MIDM_TAGSDIR names the dir that gets TAGS.tsv (default: the dir the per-n files go to).
Env MIDM_CACHE names a pickle that keeps the floatsafe answer of every raw file by the hash of its bytes, so a
second call certifies only the files that are new.
"""
import csv, glob, hashlib, os, pickle, re, sys
csv.field_size_limit(16 * 1024 * 1024)

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402

TABLES = ['round21-best-2026-11-13', 'round20-best-2026-11-13', 'round19-best-2026-11-12', 'round18-best-2026-11-12', 'round17-best-2026-11-12', 'round16-best-2026-11-12', 'round15-best-2026-11-12', 'round14-best-2026-11-12', 'round13-best-2026-11-12', 'round12-best-2026-11-12',
          'round11-best-2026-11-11', 'round10-best-2026-11-11', 'round9-best-2026-11-11', 'round8-best-2026-11-11',
          'round7-best-2026-11-11', 'harvest-best-2026-11-11', 'harvest-best-2026-11-09c', 'harvest-best-2026-11-09',
          'harvest-best-2026-11-07']


def held_sources(results):
    """n -> (source, licence, table) of the held packing: the newest table that names n."""
    src = {}
    for t in TABLES:
        p = '%s/%s.tsv' % (results, t)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p), delimiter='\t'):
            n = int(r['n'])
            if n not in src:
                src[n] = (r.get('source', ''), r.get('licence', ''), t + '.tsv')
    return src


def describe(n, tag, src):
    def held(k):
        s = src.get(k, ('seed merged0, see README', 'see README, Files', ''))
        return '%s%s' % (s[0], ', ' + s[2] if s[2] else ''), s[1]
    fq = tag.startswith('fq+'); t = tag[3:] if fq else tag
    t, _, where = t.partition('@')
    kind = t.split('-')[0]
    pre = 'fq quench of ' if fq else ''
    R, rnd = start_table(where)
    if n in R:
        sc, d, so, lic = R[n]
        d = os.path.basename(d)
        if d[-4:-2] == '-r' and d[-2:].isdigit():
            rnd = int(d[-2:])       # a relay from a find on a round 16 file runs in the round 17 queue: the dir names the round
        return '%sfq kick and quench (midm_scan.py, %s) from the round %d file of n = %d in %s (%s)' % (pre, kind, rnd, n, d, so), lic
    if kind in ('kick', 'lkick'):
        h, lic = held(n)
        return '%sfq kick and quench (midm_scan.py, %s) from the held packing of n = %d (%s)' % (pre, kind, n, h), lic
    if kind in ('drop1', 'drop2', 'grow1'):
        d = {'drop1': n + 1, 'drop2': n + 2, 'grow1': n - 1}[kind]; h, lic = held(d)
        what = {'drop1': 'minus one square', 'drop2': 'minus two squares', 'grow1': 'plus one square'}[kind]
        tool = 'own soft-box search (methods_soft.py)' if 'soft' in where else 'fq quench (midm_scan.py)'
        return '%s%s from the held packing of n = %d %s (%s)' % (pre, tool, d, what, h), 'ours, on the held n=%d; the held %d is %s' % (d, d, lic)
    h, lic = held(n)
    if 'softrelay' in where:
        return '%sown soft-box search (methods_soft.py) from the fq kick find (midm_scan.py) on the held packing of n = %d (%s)' % (pre, n, h), lic
    if kind == 'seed' or 'chain' in where:
        return ('%sseeded soft-box island (midm_soft.py%s: the held packings of n = %d, %d and %d pressed into a box under the held side of n = %d (%s))' % (
            pre, ', then methods_soft.py' if 'chain' in where else '', n + 1, n + 2, n - 1, n, h), 'ours, on held packings; the held %d is %s' % (n, lic))
    return '%sown soft-box search (methods_soft.py) from the held packing of n = %d (%s)' % (pre, n, h), lic



def samanyu_ancestry(source, licence):
    """Name explicit seed counts. A missing count stays unresolved."""
    text=source+' '+licence
    root='Samanyu-dev/squares_in_squares'
    if root.lower() not in text.lower():
        return 'Samanyu seed ancestry: no (checked retained source chain)'
    seeds=set()
    for match in re.finditer(re.escape(root),text,re.I):
        before=text[max(0,match.start()-160):match.start()]
        after=text[match.end():match.end()+200]
        direct=re.search(r'n\s*[=:]?\s*(\d+)\s+of\s*$',before,re.I)
        donor=re.search(r'\(donor n\s*[=:]?\s*(\d+)\)',after,re.I)
        explicit=re.search(r'seed n\s*[=:]?\s*(\d+)[^.;]{0,40}$',before,re.I)
        for item in (direct,donor,explicit):
            if item:seeds.add(int(item[1]))
    if not seeds:return None
    return 'Samanyu seed ancestry: yes; seed n = '+','.join(map(str,sorted(seeds)))


R16 = {}       # n -> (score, take dir, source, licence) of the round 16 files that a kick started from (MIDM_R16 names the table)
R17 = {}       # the same for the round 17 files of other lanes (MIDM_R17)
R18 = {}       # a later snapshot of the round 17 files of other lanes (MIDM_R18)
SNAP = {}      # K -> the same table for snapshot K of the round 17 files (MIDM_SNAPS/r<K>.tsv, K from 19 up)


def start_table(where):
    """The table of starts for a raw dir name, and its round: s10 holds kicks of round 16 files, s17 of round 17 files."""
    if where.endswith('s10'):
        return R16, 16
    if where.endswith('s17'):
        return R17, 17
    if where.endswith('s18'):
        return R18, 17
    m = re.search(r's(\d+)$', where)
    if m and int(m.group(1)) >= 19:
        k = int(m.group(1))
        if k not in SNAP:
            SNAP[k] = {}; p = '%s/r%d.tsv' % (os.environ.get('MIDM_SNAPS', ''), k)
            if os.path.exists(p):
                for r in csv.DictReader(open(p), delimiter='\t'):
                    SNAP[k][int(r['n'])] = (float(r['score']), r['dir'], r['source'], r['licence'])
            else:
                raise SystemExit('no start table %s for the raw dir %s' % (p, where))
        return SNAP[k], 17
    return {}, 0


def main():
    args = sys.argv[1:]; stage = None
    for env, R in (('MIDM_R16', R16), ('MIDM_R17', R17), ('MIDM_R18', R18)):
        if os.environ.get(env) and os.path.exists(os.environ[env]):
            for r in csv.DictReader(open(os.environ[env]), delimiter='\t'):
                R[int(r['n'])] = (float(r['score']), r['dir'], r['source'], r['licence'])
    held2 = {}
    if os.environ.get('MIDM_HELD2'):
        held2 = {int(r['n']): float(r['score']) for r in csv.DictReader(open(os.environ['MIDM_HELD2']))}
    if '--stage' in args:
        i = args.index('--stage'); stage = args[i + 1]; del args[i:i + 2]
    held_csv, take, results, raws = args[0], args[1], args[2], args[3:]
    live = {}; live_free={}; prev = {}
    if os.environ.get('MIDM_LIVE'):
        for d in sorted(x for pat in os.environ['MIDM_LIVE'].split() for x in glob.glob(pat)):
            if os.path.realpath(d) == os.path.realpath(take) or not os.path.exists(d + '/take.tsv'):
                continue
            for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
                try:
                    k, v = int(r['n']), float(r['new'])
                except (KeyError, TypeError, ValueError):
                    continue
                ancestry=(r.get('source','')+' '+r.get('licence','')).lower()
                if 'samanyu-dev/squares_in_squares' not in ancestry and (k not in live_free or v<live_free[k][0]):
                    live_free[k]=(v,os.path.basename(d))
                if k not in live or v < live[k][0]:
                    live[k] = (v, os.path.basename(d))
    if os.path.exists(take + '/take.tsv'):
        prev = {int(r['n']): float(r['new']) for r in csv.DictReader(open(take + '/take.tsv'), delimiter='\t')}
    out = stage or take; os.makedirs(out, exist_ok=True)
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(held_csv))}
    src = held_sources(results)
    free={}
    if os.environ.get('MIDM_FREE_DETAILS'):
        counts={int(x) for x in os.environ.get('MIDM_FREE_COUNTS','').split(',') if x}
        free={int(r['n']):float(r['score']) for r in csv.DictReader(open(os.environ['MIDM_FREE_DETAILS'])) if int(r['n']) in counts}
    best = {}; first = {}
    cpath = os.environ.get('MIDM_CACHE'); cache = {}
    if cpath and os.path.exists(cpath):
        cache = pickle.load(open(cpath, 'rb'))
    fresh = 0
    for d in raws:
        for p in sorted(glob.glob(d + '/*.csv')):
            base = os.path.basename(p)[:-4]; n = int(base.split('-')[0]); tag = base[len(str(n)) + 1:]
            rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
            if len(rows) != n:
                print('drop', n, 'rows', len(rows), p); continue
            key = hashlib.sha1(open(p, 'rb').read()).hexdigest()
            if key not in cache:
                cache[key] = floatsafe.work((n, rows))[1:]; fresh += 1
            fr, score, e = cache[key]
            origin,licence=describe(n,tag,src)
            ancestry=samanyu_ancestry(origin,licence)
            bar=free.get(n,held[n]) if ancestry and ': no ' in ancestry else held[n]
            if fr is None or not (score < bar - 1e-10):
                print('drop', n, score, bar, e, p); continue
            if n in held2 and not (score < held2[n] - 1e-10):
                print('drop', n, score, 'the later held file has', held2[n], p); continue
            comparison=live_free if n in free and ancestry and ': no ' in ancestry else live
            if n in comparison and not (score < comparison[n][0] - 1e-10) and not (n in prev and abs(score - prev[n]) < 1e-13):
                print('drop', n, score, 'the live take dir %s has' % comparison[n][1], comparison[n][0], p); continue
            R, rnd = start_table(tag.partition('@')[2])
            if n in R and not (score < R[n][0] - 1e-10):
                # started from another lane's file and no better than it: that gain is the other lane's, not ours
                print('drop', n, score, 'round %d start' % rnd, R[n][0], p); continue
            origin,licence=describe(n,tag,src)
            if samanyu_ancestry(origin,licence) is None:
                print('drop',n,'Samanyu seed count unresolved in source record',p);continue
            if not tag.startswith('fq+') and (n not in first or score < first[n]):
                first[n] = score
            prefer_free=(n in free and ancestry and ': no ' in ancestry)
            old_free=False
            if n in best:
                old_source,old_licence=describe(n,best[n][2],src)
                old_note=samanyu_ancestry(old_source,old_licence)
                old_free=n in free and old_note and ': no ' in old_note
            if n not in best or (prefer_free and not old_free) or (bool(prefer_free)==bool(old_free) and score < best[n][0]):
                best[n] = (score, fr, tag, p)
    if cpath and fresh:
        pickle.dump(cache, open(cpath + '.tmp', 'wb')); os.rename(cpath + '.tmp', cpath)
    lines = ['n\theld\tnew\tgain\tsource\tlicence\tstart\tpolish_gain']; tot = 0.0
    for n in sorted(best):
        score, fr, tag, p = best[n]
        tmp = '%s/.%d.csv.tmp' % (out, n)
        with open(tmp, 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr:
                w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.rename(tmp, '%s/%d.csv' % (out, n))
        s, lic = describe(n, tag, src)
        lic += '; '+samanyu_ancestry(s,lic)
        ancestry=samanyu_ancestry(s,lic)
        bar=free.get(n,held[n]) if ': no ' in ancestry else held[n]
        tot += bar - score
        pg = (first[n] - score) if (tag.startswith('fq+') and n in first) else 0.0
        if tag.startswith('fq+') and os.environ.get('MIDM_RAWBASE'):
            original = os.path.join(os.environ['MIDM_RAWBASE'], '%d-%s.csv' % (n, tag[3:]))
            if os.path.exists(original):
                original_key = hashlib.sha1(open(original, 'rb').read()).hexdigest()
                if original_key in cache:
                    pg = max(0.0, cache[original_key][1] - score)
        R, _ = start_table(tag.partition('@')[2])
        st = R[n][0] if n in R else held[n]
        lines.append('%d\t%r\t%r\t%.3e\t%s\t%s\t%r\t%.3e' % (n, bar, score, bar - score, s, lic, st, pg))
        print('keep', n, bar, score, '%.3e' % (bar - score), tag)
    open(os.environ.get('MIDM_TAGSDIR', out) + '/TAGS.tsv', 'w').write(''.join('%d\t%s\n' % (n, best[n][2]) for n in sorted(best)))
    tmp = out + '/.take.tsv.tmp'
    open(tmp, 'w').write('\n'.join(lines) + '\n'); os.rename(tmp, out + '/take.tsv')
    for p in glob.glob(out + '/*.csv'):      # a per-n file of an earlier pass that this pass no longer keeps
        b = os.path.basename(p)[:-4]
        if b.isdigit() and int(b) not in best:
            os.remove(p); print('removed', p)
    print('kept', len(best), 'gain', repr(tot))


if __name__ == '__main__':
    main()
