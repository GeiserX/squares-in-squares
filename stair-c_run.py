#!/usr/bin/env python3
"""The long-arm slice (m 28 to 31, k 17 to 45): staircase corners into a library, the build jobs, and the table of builds.

  stair-c_run.py add   BASELIB NEWLIB ZDIR BASE.pkl [BASE.pkl ...] [--per-class 2] [--within 0.8] [--max-loss 6.0] [--tag T]
  stair-c_run.py mark  NEWLIB ZDIR
  stair-c_run.py ns    DETAILS.csv GAP.tsv F OUT.txt [--span 0.065] [--m 28-31] [--k 17-45]
  stair-c_run.py jobs  LIB QUEUE.tsv RAW DETAILS.csv GAP.tsv FQ [--max 0.003] [--per 1] [--done RAW,RAW] [--py PY] [--lane DIR] [--source-key LABEL]
  stair-c_run.py best  DETAILS.csv OUT.tsv RAW [RAW ...]

add    The corners of staircase base files (twoshort_corner.py stair) as modules of a new library: for every count class
       of arm 1 the --per-class corners of lowest loss, and only those within --within squares of the lowest loss of the
       file. Then zone_corner.py adopt, table and merge, in this process. Writes NEWLIB/need.txt (the ids of the new
       corners) for `modules.py queue --need`.
mark   After `zone_corner.py table` and `merge` (for corners that hops lowered): marks the zone-search modules of our
       own as usable by the generator and writes NEWLIB/need.txt.
ns     The n of the slice that are behind the board and whose held side fraction is within --span of F.
jobs   The rows of a queue file as `modules.py job` lines: rows up to --max of side above held, the n with the largest
       score gap to the board first, then the lowest prediction, at most --per rows for each (n, corner).
best   Every build of the raw dirs as one table, the lowest side of each n marked.

Our own code. Reads pickles and tables as data only. Imports zone_corner.py, modules.py and twoshort.py of this lane;
it changes no file of another lane.
"""
import collections, csv, glob, hashlib, json, math, os, pickle, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def opt(a, name, default, kind=float):
    return kind(a[a.index(name) + 1]) if name in a else default


def cmd_add(a):
    import zone_corner as ZC
    base, new, zdir = a[0], a[1], a[2]
    pkls = [p for p in a[3:] if p.endswith('.pkl')]
    per = opt(a, '--per-class', 2, int); within = opt(a, '--within', 0.8); cut = opt(a, '--max-loss', 6.0); tag = opt(a, '--tag', '', str)
    os.makedirs(zdir + '/runs', exist_ok=True); os.makedirs(zdir + '/zones', exist_ok=True)
    for p in pkls:
        B = pickle.load(open(p, 'rb'))
        for b in B: b['loss'] = ZC.loss_of(ZC.cmod(b['c1'], b['c2'], b['lean1'], b['lean2']), b['f'], b['count'], b['y0'], b['x0'])
        lo = min(b['loss'] for b in B); seen = collections.Counter(); keep = []
        for b in sorted(B, key=lambda b: b['loss']):
            cl = b['count'] % b['c1']
            if b['loss'] > lo + within or seen[cl] >= per: continue
            seen[cl] += 1; keep.append(b)
        sel = '%s/%s.sel.pkl' % (zdir, os.path.basename(p)[:-4])
        pickle.dump(keep, open(sel, 'wb'))
        print('%s: %d of %d corners kept, loss %.3f to %.3f, classes %s' % (os.path.basename(p), len(keep), len(B), lo, max(b['loss'] for b in keep),
              sorted(seen)), flush=True)
        ZC.cmd_adopt([sel, zdir + '/runs'])
    ZC.cmd_table([zdir + '/runs', zdir + '/zones', zdir + '/zones.tsv', '--all', '--tag', tag])
    ZC.cmd_merge([base, zdir + '/zones', new, '--max-loss', str(cut)])
    cmd_mark([new, zdir])


def cmd_mark(a):
    new, zdir = a[0], a[1]
    lib = pickle.load(open(new + '/library.pkl', 'rb')); k = 0
    for q in lib['mods']:                                # a zone-search module of our own may be used by the generator
        if q['tag'] == 'z' and q['licence'] == 'our own' and not q.get('ours'): q['ours'] = True; k += 1
    pickle.dump(lib, open(new + '/library.pkl', 'wb'))
    have = {q['id'] for q in lib['mods']}
    ids = [q['id'] for q in pickle.load(open(zdir + '/zones/corners.pkl', 'rb')) if q['id'] in have]
    open(new + '/need.txt', 'w').write('\n'.join(ids) + '\n')
    print('%s: %d new corners in the library, %d marked ours' % (new, len(ids), k), flush=True)


def slice_gap(details, gap, ms=(28, 31), ks=(17, 45)):
    """-> {n: (m, k, held f, board f, score gap)} for the n of the slice"""
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    board = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open(gap), delimiter='\t')}
    out = {}
    for n in sorted(held):
        m = math.isqrt(n - 1); k = n - m * m
        if ms[0] <= m <= ms[1] and ks[0] <= k <= ks[1]: out[n] = (m, k, held[n] - m, board[n] - m, (held[n] - board[n]) / math.sqrt(n))
    return out


def cmd_ns(a):
    from twoshort import span
    f = float(a[2]); sp = opt(a, '--span', 0.065)
    G = slice_gap(a[0], a[1], span(opt(a, '--m', '28-31', str)), span(opt(a, '--k', '17-45', str)))
    ns = [n for n, g in G.items() if g[4] > 1e-7 and abs(g[2] - f) <= sp]
    open(a[3], 'w').write('\n'.join(map(str, ns)) + '\n')
    print('%d n within %.3f of f = %.2f: %s' % (len(ns), sp, f, ' '.join(map(str, ns))))


def job_name(r, source_key=''):
    fields = ('corner', 'far1', 'far2', 'stacks1', 'stacks2')
    identity = ''.join(r[k] for k in fields) + '\n'
    if source_key:
        identity += 'source=' + source_key + '\n'
    return '%s-%s' % (r['n'], hashlib.md5(identity.encode()).hexdigest()[:8])


def cmd_jobs(a):
    lib, rows, raw, details, gap, fq = a[:6]
    mx = opt(a, '--max', 0.003); per = opt(a, '--per', 1, int)
    py = opt(a, '--py', sys.executable, str); lane = opt(a, '--lane', os.path.dirname(os.path.abspath(__file__)), str)
    G = slice_gap(details, gap)
    done = set()
    for d in [raw] + [v for v in opt(a, '--done', '', str).split(',') if v]:
        done |= {os.path.basename(p).rsplit('.', 1)[0] for p in glob.glob(d + '/*.json') + glob.glob(d + '/*.nostart') + glob.glob(d + '/*.lock')}
    R = [r for r in csv.DictReader(open(rows), delimiter='\t') if r['n'] != 'n' and int(r['n']) in G and float(r['predicted_minus_held']) <= mx]
    R.sort(key=lambda r: (-G[int(r['n'])][4], float(r['predicted_minus_held'])))
    cnt = collections.Counter()
    source_key = opt(a, '--source-key', '', str)
    for r in R:
        name = job_name(r, source_key); k = (r['n'], r['corner'])
        if name in done or cnt[k] >= per: cnt[k] += name in done; continue
        cnt[k] += 1
        print('%s %s -I %s/modules.py job %s %s %s %s %s %s %s %s %s %s %s --fq %s --squeeze family' % (
            name, py, lane, lib, raw, details, name, r['n'], r['corner'], r['far1'], r['far2'], r['stacks1'], r['stacks2'], r['f'], fq))


def cmd_best(a):
    details, out, raws = a[0], a[1], a[2:]
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    J = []
    for d in raws:
        for p in sorted(glob.glob(d + '/*.json')):
            j = json.load(open(p))
            if j.get('built') is None: continue
            j['name'] = os.path.basename(p)[:-5]; J.append(j)
    best = {}
    for j in J:
        if j['n'] not in best or j['built'] < best[j['n']]['built']: best[j['n']] = j
    with open(out + '.tmp', 'w') as h:
        h.write('n\tm\tk\tcorner\tfar1\tfar2\tstacks1\tstacks2\tpredicted_side\tbuilt_side\theld_side\tbuilt_minus_held\tbest_of_n\tseconds\n')
        for j in sorted(J, key=lambda j: (j['n'], j['built'])):
            n = j['n']; m = math.isqrt(n - 1)
            h.write('%d\t%d\t%d\t%s\t%s\t%s\t%d\t%d\t%.6f\t%.9f\t%.9f\t%+.6f\t%s\t%.0f\n' % (
                n, m, n - m * m, j['modules'][0]['id'], j['modules'][1]['id'], j['modules'][2]['id'], j['stacks'][0], j['stacks'][1], j['predicted'],
                j['built'], held[n], j['built'] - held[n], 'yes' if best[n] is j else '', sum(j.get('seconds', {}).values())))
    os.replace(out + '.tmp', out)
    below = [j for j in best.values() if j['built'] < held[j['n']] - 1e-9]
    print('%d builds on %d n; %d n below held: %s' % (len(J), len(best), len(below), ' '.join('%d (%+.6f)' % (j['n'], j['built'] - held[j['n']]) for j in sorted(below, key=lambda j: j['n']))))


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ('add', 'mark', 'ns', 'jobs', 'best'): print(__doc__); return 1
    return {'add': cmd_add, 'mark': cmd_mark, 'ns': cmd_ns, 'jobs': cmd_jobs, 'best': cmd_best}[a[0]](a[1:])


if __name__ == '__main__':
    sys.exit(main() or 0)
