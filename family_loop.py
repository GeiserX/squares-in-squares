#!/usr/bin/env python3
"""The follow loop of the family step: while a round runs, every new certified layout of every lane is
walked up and down its line, and every near miss is built a second time at another cut and trust radius.

  family_loop.py cycle WORK --details D.csv --held H.csv --gate G.json --best B.tsv [--every 300]
                       [--until EPOCH] [--once] [--nearprio 200] [--draws] [--logs NAME ...] [--first LANE ...]
                       [--misses 2]
  family_loop.py left  WORK PREVWORK      round PREVWORK's unrun jobs into WORK's queues (5xxx; public 8xxx)
  family_loop.py ctake CACHE.tsv DETAILS TAKE OUT... [--table T] [--sources S] [--beat B...]
                                          family_step.py take with the floatsafe scores cached by the hash of the rows
  family_loop.py fill  OUT.tsv BOX FILE.csv ...   score raw files for the cache (run on the box with the lowest load)

WORK is the work dir of the take dir (TAKE/work). It holds:
  deploy/        what the boxes run: family_step.py and its imports, fq, worker.sh, details.csv, deadline,
                 donors/, jobs/ and beat-*.tsv
  boxes.tsv      box, ssh host ('-' for this box), remote dir, slots, speed
  sources.tsv    donor, source, licence (family_step.py take reads it)
  seen-*.txt     what each pass has already made jobs for

One cycle collects the rows of every box and certifies them into TAKE (family_step.py take, against
D.csv and the take.tsv of every other lane's take dir of the round, and of every take dir that a line of
the handoff log names). Since round 16 the floatsafe score of a raw file is cached in WORK/certcache.tsv
by the hash of its rows; the files not in the cache are scored first on the box with the lowest load, and
a score from another box that beats its bar is scored again here before it is kept. Each new certified
layout gets one line in the handoff log and one fq quench from its certified csv (jobs 01xx). It copies
the take.tsv files to the boxes as beat files. Then it makes jobs:
  02xx  (--nearprio) second builds of the near misses (1e-9 to 2e-4 above the bar) from the layout the step began at:
        a walk step at cut 0.3 and trust radius 1e-3, a single build at cut 0.7 and 5e-4
  1150 to 1750 (--draws) the near misses 1e-7 to 2e-4 above the bar built again with SQ_DRAW=1, 2 and 3
        (other HiGHS solver orders), ranked by the distance to the bar over the weight of n (draw_rank)
  1xxx  walks from the new designs: the n of G.json (held layout in H.csv) and the n of every other
        lane's take dir, up and down, ranked by gain (a down walk counts as a tenth of its gain; the
        direction the family walk of the round before already went counts a millionth); the near/ folders
        of the take dirs and the csv files named in the handoff log count as a gain of 1e-6. One layout
        (by the hash of its rows) gets one walk, whichever lane names it. The take dir layouts of a --first
        lane (round 17: twoshort, a new design) walk up and down at jobs 1000 to 1099, before the rest.
        --logs names more handoff logs to read beside handoff-ROUND.log (round 17: handoff-d5.log)
and deals each one to the box whose queue is shortest for its slots and speed. Workers take the lowest
name first. A layout that reads only with SQ_WALLTOL=4e-2 gets its walk with that option.
Our own code; reads data only. Run with python -I.
"""
import argparse, collections, csv, glob, hashlib, json, math, os, re, shutil, subprocess, sys, time
csv.field_size_limit(50_000_000)

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import family_step as fs  # noqa: E402
import numpy as np  # noqa: E402

PY = sys.executable
HEAD = 'rank\ttarget\tdonor\tdirection\tshells\tpred_board\tpred_formula\theld\tboard\tpred_gain_score\n'
TAGS = {'harvest-m': 'hm', 'readers': 'rd', 'polish': 'p', 'border': 'b', 'modules': 'm', 'zones': 'z', 'zones-corner': 'zc',
        'zones-lowf': 'zl', 'soft': 'o', 'gadget': 'g', 'harvest': 'hv', 'inflate': 'i',
        'twoshort': 'ts', 'rigidsoft': 'rs', 'k123': 'k', 'midm': 'mm', 'classfill': 'cf', 'forensics': 'fo', 'invent': 'iv',
        'farend': 'fe', 'corners': 'c'}


def hlogs(a):
    """The handoff logs the loop reads: handoff-ROUND.log and every --logs name (round 17: handoff-d5.log of
    the new-idea lanes on boxE)."""
    return ['%s/handoff-%s.log' % (a.scratch, a.round)] + ['%s/%s' % (a.scratch, x) for x in (getattr(a, 'logs', None) or [])]


def log(work, msg):
    line = '%s %s' % (time.strftime('%H:%M:%S', time.gmtime()), msg)
    print(line, flush=True)
    with open(work + '/loop.log', 'a') as h:
        h.write(line + '\n')


def sh(cmd, timeout=120):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return ''


def boxes(work):
    out = []
    for l in open(work + '/boxes.tsv').read().splitlines()[1:]:
        name, host, d, slots, speed = l.split('\t')
        out.append(dict(name=name, host=host, dir=d, slots=int(slots), speed=float(speed)))
    return out


def seen(work, kind):
    p = '%s/seen-%s.txt' % (work, kind)
    return set(open(p).read().split()) if os.path.exists(p) else set()


def save_seen(work, kind, s):
    p = '%s/seen-%s.txt' % (work, kind)
    open(p + '.tmp', 'w').write('\n'.join(sorted(s)) + '\n'); os.replace(p + '.tmp', p)


def sources(work):
    p = work + '/sources.tsv'
    return {l.split('\t')[0]: l for l in open(p).read().splitlines()[1:]} if os.path.exists(p) else {}


def save_sources(work, src):
    p = work + '/sources.tsv'
    with open(p + '.tmp', 'w') as h:
        h.write('donor\tsource\tlicence\n')
        for d in sorted(src):
            h.write(src[d] + '\n')
    os.replace(p + '.tmp', p)


def other_takes(take, rnd, scratch):
    """{lane: take dir} of every other lane's take dir of the round (the assembler's merge is left out)."""
    out = {}
    for d in sorted(glob.glob('%s/take-*-%s' % (scratch, rnd))):
        lane = os.path.basename(d)[5:-len(rnd) - 1]
        if os.path.abspath(d) != os.path.abspath(take) and not lane.startswith('assemble') and os.path.exists(d + '/take.tsv'):
            out[lane] = d
    return out


def handoff_takes(a, takes, take):
    """Round 16: the take dirs that a line of the handoff log names by their take.tsv and that are not a
    take-*-ROUND dir (the harvest passes): {lane: dir}. Their n are bars and starts like any take dir."""
    out = {}
    text = ''.join(open(hl).read() for hl in hlogs(a) if os.path.exists(hl))
    known = {os.path.abspath(d) for d in takes.values()} | {os.path.abspath(take)}
    for p in re.findall(r'(/\S+?/take\.tsv)\b', text):
        d = os.path.dirname(p); b = os.path.basename(d)
        if os.path.abspath(d) in known or not os.path.isfile(p) or 'assemble' in b or not b.startswith('take-'):
            continue
        m = re.match(r'take-(\w+)-\d{4}-\d\d-\d\d(\w*)$', b)
        out[('%s-%s' % m.groups()) if m else b[5:]] = d
    return out


# ---------------------------------------------------------------- collect and certify

def collect(work, bx):
    for b in bx:
        if b['host'] == '-':
            for d in glob.glob(b['dir'] + '/out-*'):
                dst = '%s/%s-%s' % (work, b['name'], os.path.basename(d))
                os.makedirs(dst, exist_ok=True); sh('rsync -a %s/ %s/' % (d, dst))
            continue
        cache = '%s/collect-%s' % (work, b['name'])
        os.makedirs(cache, exist_ok=True)
        sh("rsync -a --include='out-*/' --include='out-*/***' --include='log-*.txt' --exclude='*' %s:%s/ %s/" % (
            b['host'], b['dir'], cache), 300)
        for path in sorted(glob.glob(cache + '/out-*')):
            if not os.path.isdir(path):
                continue
            d = os.path.basename(path)
            dst = '%s/%s-%s' % (work, b['name'], d)
            shutil.copytree(path, dst, dirs_exist_ok=True)
        os.makedirs('%s/logs-%s' % (work, b['name']), exist_ok=True)
        for path in glob.glob(cache + '/log-*.txt'):
            shutil.copy2(path, '%s/logs-%s/%s' % (work, b['name'], os.path.basename(path)))


def outs(work):
    """The out dirs of family_step.py. Out dirs of family_readers.py walks (out-j*, round 15) hold rows with
    other columns: family_readers.py take certifies them."""
    return sorted(d for d in glob.glob(work + '/*-out*') if os.path.isdir(d) and '-cmp-' not in d and '-out-j' not in d)


def certify(work, take, details, beats, bx=None, outdirs=None, table=None):
    """family_step.py take, run through ctake: the floatsafe score of every raw file is cached by the hash
    of its rows (round 16). The raw files not in the cache are scored first on the box with the lowest
    load (fill)."""
    if bx is not None:
        prefill(work, bx)
    cmd = '%s -I %s/family_loop.py ctake %s/certcache.tsv %s %s %s --table %s/family-table.tsv --sources %s/sources.tsv' % (
        PY, LANE, work, details, take, ' '.join(outs(work) if outdirs is None else outdirs), work, work)
    if table is not None:
        cmd = cmd.replace(work + '/family-table.tsv', table)
    if beats:
        cmd += ' --beat ' + ' '.join(beats)
    out = sh(cmd + ' > %s/take.log.tmp 2>&1; mv %s/take.log.tmp %s/take.log' % (work, work, work), 1800)
    keep = [l for l in open(work + '/take.log') if l.startswith('keep')] if os.path.exists(work + '/take.log') else []
    return keep


# ---------------------------------------------------------------- the certification cache (round 16)
# The floatsafe verdict of a file depends on its rows only: floatsafe.work gives the score and the dilation
# e, and the rows as written are as_float_rows(rows, e). The bar only decides whether that score is a win,
# a float compare made again at every cycle. So the cache holds, per hash of the rows, the score and e, and
# the box that scored it. A score from another box that beats the bar is scored again here before it is
# kept ('local'); every other entry is taken as it is.

KEYS = ('n', 'square_id', 'x', 'y', 'angle')
_memo = {}                                      # path -> (mtime, size, key): the loop hashes a file once


def rows_of(p):
    return [{k: r[k] for k in KEYS} for r in csv.DictReader(open(p))]


def rows_key(n, rows):
    h = hashlib.sha256(('%d\n' % n).encode())
    for r in rows:
        h.update((','.join(r[k] for k in KEYS) + '\n').encode())
    return h.hexdigest()


def load_cache(path):
    c = {}
    if os.path.exists(path):
        for l in open(path).read().splitlines():
            q = l.split('\t')
            if len(q) == 5 and q[0] != 'key':
                c[q[0]] = (float(q[2]), None if q[3] == 'None' else (0 if q[3] == '0' else float(q[3])), q[4])
    return c


def cache_line(key, n, score, e, where):
    return '%s\t%d\t%r\t%r\t%s\n' % (key, n, score, e, where)


def raw_files(work):
    for d in outs(work):
        for p in sorted(glob.glob(d + '/raw/*.csv')):
            yield p


def file_key(p):
    st = os.stat(p); m = _memo.get(p)
    if m and m[0] == st.st_mtime and m[1] == st.st_size:
        return m[2]
    n = int(os.path.basename(p).split('-')[0]); rows = rows_of(p)
    k = rows_key(n, rows) if len(rows) == n else None
    _memo[p] = (st.st_mtime, st.st_size, k)
    return k


def load_of(b):
    """Load average over cores of a box ('-' is this box)."""
    if b['host'] == '-':
        return os.getloadavg()[0] / (os.cpu_count() or 1)
    q = sh("ssh -o ConnectTimeout=8 %s 'sysctl -n hw.ncpu vm.loadavg'" % b['host'], 30).split()
    try:
        return float(q[2]) / float(q[0])
    except (IndexError, ValueError):
        return float('inf')


def prefill(work, bx):
    """Score the raw files the cache does not hold yet, on the box with the lowest load (one process). On
    this box, ctake scores them itself. A box lent for one worker (slots 1, round 17: boxE) gets no
    fill, so the lane never runs a second process there."""
    cpath = work + '/certcache.tsv'; have = load_cache(cpath)
    miss = {}
    for p in raw_files(work):
        k = file_key(p)
        if k and k not in have and k not in miss:
            miss[k] = p
    if not miss or FILL_HERE:
        return
    here = dict(name=os.uname()[1].split('.')[0], host='-', dir=work)
    loads = [(load_of(b), b['name'], b) for b in bx if b['host'] != '-' and b['slots'] > 1] + [(load_of(here), 'here', here)]
    ld, name, b = min(loads, key=lambda t: t[0])
    log(work, 'fill: %d files, loads %s, on %s' % (len(miss), ' '.join('%s %.2f' % (t[1], t[0]) for t in loads), name))
    if b['host'] == '-':
        return
    q = '%s/certq' % work; shutil.rmtree(q, ignore_errors=True); os.makedirs(q)
    for k, p in miss.items():
        shutil.copy(p, '%s/%s-%s.csv' % (q, os.path.basename(p).split('-')[0], k[:16]))
    t0 = time.time()
    sh("ssh %s 'rm -rf %s/certq'" % (b['host'], b['dir']), 60)
    sh('rsync -a %s/ %s:%s/certq/' % (q, b['host'], b['dir']), 300)
    sh("ssh %s 'cd %s && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 nice -n 5 venv/bin/python -I family_loop.py fill "
       "certq/fill.tsv %s certq/*.csv > certq/fill.log 2>&1'" % (b['host'], b['dir'], b['name']), 900)
    got = sh("ssh %s 'cat %s/certq/fill.tsv'" % (b['host'], b['dir']), 120)
    lines = [l + '\n' for l in got.splitlines() if len(l.split('\t')) == 5 and l.split('\t')[0] in miss]
    with open(cpath, 'a') as h:
        h.writelines(lines)
    log(work, 'fill: %d of %d scored on %s in %.0fs' % (len(lines), len(miss), name, time.time() - t0))


def cmd_fill(a):
    """Score raw files with floatsafe.work and write cache lines (run on the box with the lowest load)."""
    import floatsafe
    with open(a.out + '.tmp', 'w') as h:
        for p in a.files:
            n = int(os.path.basename(p).split('-')[0]); rows = rows_of(p)
            if len(rows) != n:
                continue
            _, fr, score, e = floatsafe.work((n, rows))
            h.write(cache_line(rows_key(n, rows), n, score, e, a.where)); h.flush()
    os.replace(a.out + '.tmp', a.out)


def cmd_ctake(a):
    """family_step.py take with floatsafe.work answered from the cache CACHE. A miss, and a score from
    another box that beats its bar, are scored here and written to the cache as 'local'."""
    import floatsafe
    argv = a.rest
    details = argv[0]; beat = []
    if '--beat' in argv:
        i = argv.index('--beat'); beat = [x for x in argv[i + 1:] if not x.startswith('--')]
    bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(details))}
    for fn in beat:
        for r in csv.DictReader(open(fn), delimiter='\t'):
            bar[int(r['n'])] = min(bar[int(r['n'])], float(r['new']))
    cache = load_cache(a.cache); real = floatsafe.work; stat = collections.Counter()
    h = open(a.cache, 'a')

    def work(arg):
        n, rows = arg
        k = rows_key(n, rows); c = cache.get(k)
        if c is not None:
            score, e, where = c
            if where == 'local' or not score < bar[n] - 1e-10:
                stat['hit'] += 1
                if e is None or not score < bar[n] - 1e-10:
                    return n, None, score, e
                return n, floatsafe.as_float_rows(rows, e), score, e
        stat['scored'] += 1
        r = real(arg)
        cache[k] = (r[2], r[3], 'local'); h.write(cache_line(k, n, r[2], r[3], 'local')); h.flush()
        return r
    floatsafe.work = work
    sys.argv = ['family_step.py', 'take'] + argv
    fs.main()
    print('cache: %d hits, %d scored here' % (stat['hit'], stat['scored']))


def prune(work, take):
    """Round 17: a per-n csv at the top of TAKE with no take.tsv row (another lane went lower, so the take
    dropped it) moves to WORK/dropped/, so the top level holds only take.tsv and the files it names."""
    rows = {l.split('\t')[0] for l in open(take + '/take.tsv').read().splitlines()[1:]} if os.path.exists(take + '/take.tsv') else set()
    for p in glob.glob(take + '/*.csv'):
        n = os.path.basename(p)[:-4]
        if n not in rows:
            os.makedirs(work + '/dropped', exist_ok=True)
            os.replace(p, '%s/dropped/%s-%s.csv' % (work, n, time.strftime('%H%M', time.gmtime())))
            log(work, 'prune: %s.csv has no take.tsv row, moved to dropped/' % n)


def announce(work, take, a, keep):
    """One line in the handoff log of the round for each layout that certifies here for the first time."""
    p = work + '/announced.txt'; done = set(open(p).read().split()) if os.path.exists(p) else set()
    new = []
    for l in keep:
        q = l.split()                       # keep n held new gain tag
        k = '%s:%s' % (q[1], q[3])
        if k not in done:
            new.append('%s family -> all: certified n = %s, score %s (gain %s on held), %s/%s.csv\n' % (
                time.strftime('%H:%M', time.gmtime()), q[1], q[3], q[4], take, q[1]))
            done.add(k)
    if new:
        with open('%s/handoff-%s.log' % (a.scratch, a.round), 'a') as h:
            h.writelines(new)
        open(p, 'w').write('\n'.join(sorted(done)) + '\n')


NEAR_OUT = 0.0     # cycle --nearout (round 21): near misses within this of the bar go to TAKE/near/ for the kick lanes
NEAR_FROM = []     # cycle --nearfrom (round 21): more out dirs (the frozen work dir of the round before) for near_out only


def near_out(work, take, a, beats):
    """Round 21: the best layout of each n that a walk or a draw of this round built less than NEAR_OUT above
    the bar of now goes to TAKE/near/<n>-<step>.csv, with one row in TAKE/near/near.tsv (n, side, bar, over,
    file, source, licence). Other lanes read near/ every 10 minutes and kick or quench those layouts. A layout
    that falls below the bar or goes over NEAR_OUT leaves near/. The first file gets one handoff line."""
    if NEAR_OUT <= 0:
        return 0
    own = take + '/take.tsv'
    bars = fs._bars(work + '/deploy/details.csv', list(beats) + ([own] if os.path.exists(own) else []))
    src = sources(work); best = {}
    for d in outs(work) + [x for g in NEAR_FROM for x in sorted(glob.glob(g)) if os.path.isdir(x)]:
        for fn in glob.glob(d + '/rows-*.tsv'):
            walk = 'walk' in os.path.basename(fn)
            for r in csv.DictReader(open(fn), delimiter='\t'):
                if r['state'].startswith(('refused', 'error', 'wrong')):
                    continue
                try:
                    t = int(r['target']); sd = float(r['after_squeeze']); dv = sd - bars[t]
                except (ValueError, KeyError):
                    continue
                if not (0 < dv <= NEAR_OUT) or (t in best and best[t][0] <= sd):
                    continue
                stem = '%d-%s%sfrom%s' % (t, r['direction'], r['shells'], r['donor'])
                p = '%s/steps/%s.csv' % (d, stem) if walk else (sorted(glob.glob('%s/near/%s-w*.csv' % (d, stem))) or [''])[0]
                if p and os.path.exists(p):
                    so = src.get(r['donor'].split('+')[0], '\t%s\t' % r['donor']).split('\t')
                    best[t] = (sd, dv, p, stem, 'family_step.py %s shell(s) %s from %s' % (r['shells'], r['direction'], so[1]),
                               so[2] if len(so) > 2 else '')
    N = take + '/near'; os.makedirs(N, exist_ok=True)
    have = {os.path.basename(p) for p in glob.glob(N + '/*.csv')}
    want = {'%s.csv' % v[3] for v in best.values()}
    for f in have - want:
        os.remove('%s/%s' % (N, f))
    changed = []
    for t, (sd, dv, p, stem, so, lic) in best.items():
        dst = '%s/%s.csv' % (N, stem)
        digest = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        if stem + '.csv' not in have or hashlib.sha256(open(dst, 'rb').read()).hexdigest() != digest:
            shutil.copy(p, '%s/%s.csv.tmp' % (N, stem)); os.replace('%s/%s.csv.tmp' % (N, stem), '%s/%s.csv' % (N, stem))
            changed.append((t, sd, dv, dst, stem + '@' + digest))
    with open(N + '/near.tsv.tmp', 'w') as h:
        h.write('n\tside\tbar\tover\tfile\tsource\tlicence\n')
        for t in sorted(best):
            sd, dv, p, stem, so, lic = best[t]
            h.write('%d\t%.9f\t%.9f\t%.3e\t%s.csv\t%s\t%s\n' % (t, sd, bars[t], dv, stem, so, lic))
    os.replace(N + '/near.tsv.tmp', N + '/near.tsv')
    flag = work + '/near-announced'
    if best and not os.path.exists(flag):
        with open('%s/handoff-%s.log' % (a.scratch, a.round), 'a') as h:
            h.write('%s family -> all: near misses of the family walks (best layout per n, 0 to %.0e of side above the bar of now, '
                    'refreshed every 3 minutes; near.tsv names each source) for kicks and quenches, %s/near/near.tsv\n' % (
                        time.strftime('%H:%M:%SZ', time.gmtime()), NEAR_OUT, take))
        open(flag, 'w').write(time.strftime('%H:%M:%SZ', time.gmtime()) + '\n')
    announced = seen(work, 'nearout')
    for t, sd, dv, path, key in changed:
        if key not in announced:
            with open('%s/handoff-%s.log' % (a.scratch, a.round), 'a') as h:
                h.write('%s family -> all: fresh near n=%d, side %.10f, %.3e above the bar; source in near.tsv, %s\n' % (
                    time.strftime('%H:%M:%SZ', time.gmtime()), t, sd, dv, path))
            announced.add(key)
    save_seen(work, 'nearout', announced)
    return len(best)


def quench_pass(work, take, keep, versioned=False):
    """One fq quench of each certified file from the certified csv (near_polish.py: fq default and polish
    flags, then the exact LP), jobs 01xx at the head of the queues. A quench result is not quenched again."""
    D = work + '/deploy'; done = seen(work, 'quench'); new = []
    os.makedirs(D + '/qin', exist_ok=True)
    for l in keep:
        q = l.split(); n, tag = q[1], q[5]
        path = '%s/%s.csv' % (take, n)
        version = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16] if versioned else ''
        key = tag + '@' + version if versioned else tag
        if key in done or not re.match(r'\d+-(up|down)\d+from.+$', tag):
            continue
        done.add(key)
        sub = 'qin/' + version if versioned else 'qin'
        out = 'out-quench-' + version if versioned else 'out-quench'
        os.makedirs('%s/%s' % (D, sub), exist_ok=True)
        shutil.copy(path, '%s/%s/%s.csv' % (D, sub, tag))
        j = '%04d-quench-%s%s' % (100 + min(len(done), 99), tag, '-' + version if versioned else '')
        open('%s/jobs/%s.job' % (D, j), 'w').write(
            '$PY -I -u near_polish.py %s details.csv 150 %s/%s.csv --beat $BEAT\n' % (out, sub, tag))
        new.append(j + '.job')
    save_seen(work, 'quench', done)
    return new


def certify_after_quench(work, take, details, beats, bx=None):
    """Stage certified candidates, then publish only the remote quenches of their certified csv files."""
    stage = work + '/certified'
    candidates = [d for d in outs(work) if '-out-quench-' not in d]
    empty = work + '/empty-quench'
    os.makedirs(empty, exist_ok=True)
    staged = certify(work, stage, details, beats, bx, outdirs=candidates or [empty])
    shutil.copy(work + '/take.log', work + '/stage.log')
    qj = quench_pass(work, stage, staged, versioned=True)
    quenched = [d for d in outs(work) if '-out-quench-' in d]
    keep = certify(work, take, details, beats, outdirs=quenched or [empty], table=work + '/published-table.tsv')
    return keep, qj


def push_beats(work, bx, takes):
    D = work + '/deploy'
    for lane, d in takes.items():
        shutil.copy(d + '/take.tsv', '%s/beat-%s.tsv.tmp' % (D, lane)); os.replace('%s/beat-%s.tsv.tmp' % (D, lane), '%s/beat-%s.tsv' % (D, lane))
    for b in bx:
        if b['host'] == '-':
            sh('cp %s/beat-*.tsv %s/ 2>/dev/null' % (D, b['dir']))
        else:
            sh('rsync -a %s/beat-*.tsv %s:%s/' % (D, b['host'], b['dir']))


# ---------------------------------------------------------------- jobs

def readable(P, n):
    """-> '' when read_any takes the layout, the env prefix that makes it read, or None."""
    try:
        fs.read_any(P, n); return ''
    except fs.Unreadable:
        pass
    os.environ['SQ_WALLTOL'] = '4e-2'
    try:
        fs.read_any(P, n); return 'SQ_WALLTOL=4e-2 SQ_APART=6e-2 '
    except fs.Unreadable:
        return None
    finally:
        del os.environ['SQ_WALLTOL']


WALK_MISSES = 2     # cycle --misses: a walk ends after this many steps in a row that do not win
DRAW_SHIFT = 0      # cycle --drawshift (round 19): added to the job number of every draw, so draws run after the walks
FILL_HERE = False   # cycle --fillhere (round 19): the loop scores new raw files itself, so a box runs only its workers


DRAW_KEEP = False  # cycle --drawkeep (round 21): with --drawidle, queued walks do not stop running draws
STAIR_ENV = ''     # cycle --staircut (round 21): every job may cut beside a staircase run (family_step.py SQ_STAIRCUT)


def walk_job(D, prio, name, direction, env, kind='fol'):
    nm = '%04d-%s-%s-%s' % (prio, kind, name, direction)
    open('%s/jobs/%s.tsv' % (D, nm), 'w').write('donor\tdirection\n%s\t%s\n' % (name, direction))
    open('%s/jobs/%s.job' % (D, nm), 'w').write(
        '%s%s$PY -I -u family_step.py walk jobs/%s.tsv donors details.csv out-%s --mod 1,0 --deadline deadline --misses %d '
        '--maxsteps 8 --buildsec 600 --beat $BEAT\n' % (STAIR_ENV, env, nm, kind, WALK_MISSES))
    return nm + '.job'


def rank(gain):
    return int(min(899, max(0, (-math.log10(max(gain, 1e-12)) - 3) * 150)))


def near_pass(work, first=200):
    """Second builds of the near misses of this round (mknear12.py of round 12, as a pass)."""
    D = work + '/deploy'; done = seen(work, 'near'); src = sources(work); new = []
    i = len(done)
    own = os.path.dirname(work) + '/take.tsv'      # an n this lane already certified is not built again
    mine = {r['n'] for r in csv.DictReader(open(own), delimiter='\t')} if os.path.exists(own) else set()
    for d in outs(work):
        if d.endswith('-out-near2') or '-out-draw' in d:   # a second build or a draw is not built again: the
            continue                                         # near miss it came from has its own second build
        li = os.path.basename(d)
        for fn in glob.glob(d + '/rows-*.tsv'):
            rows = list(csv.DictReader(open(fn), delimiter='\t'))
            walk = 'walk' in os.path.basename(fn)
            for r in rows:
                if r['state'].startswith(('refused', 'error', 'wrong', 'below')):
                    continue
                try:
                    dv = float(r['after_squeeze']) - float(r['held'])
                except ValueError:
                    continue
                if not (1e-9 < dv <= 2e-4) or r['target'] in mine:
                    continue
                k = int(r['shells']); key = '%s|%s|%s|%s|%s' % (li, r['target'], r['donor'], r['direction'], k)
                if key in done:
                    continue
                if walk and k > 1:
                    prev = [p for p in rows if p['donor'] == r['donor'] and p['direction'] == r['direction'] and int(p['shells']) == k - 1]
                    if not prev:
                        continue
                    f = '%s/steps/%s-%s%dfrom%s.csv' % (d, prev[0]['target'], r['direction'], k - 1, r['donor'])
                    if not os.path.exists(f):
                        continue
                    nd = int(prev[0]['target'])
                    name = '%d-k%s' % (nd, hashlib.sha1(f.encode()).hexdigest()[:6])
                    fs.write_rows('%s/donors/%s.csv' % (D, name), nd, fs.load(f)[nd])
                    base = r['donor'].split('+')[0]
                    so = src.get(base, '%s\t%s\t' % (base, base)).split('\t')
                    src[name] = '%s\t%d shell(s) %s from %s\t%s' % (name, k - 1, r['direction'], so[1], so[2] if len(so) > 2 else '')
                else:
                    name = r['donor'].split('+')[0]
                    if not os.path.exists('%s/donors/%s.csv' % (D, name)):
                        continue
                where, tra = ('0.3', '1e-3') if walk else ('0.7', '5e-4')
                env = 'SQ_LOOSE=1 ' + ('SQ_APART=3e-2 ' if r['direction'] == 'up' else '')   # run reads as a walk does
                dn = int(name.split('-')[0])
                if readable(fs.load('%s/donors/%s.csv' % (D, name))[dn], dn) not in ('', None):
                    env = 'SQ_LOOSE=1 SQ_WALLTOL=4e-2 SQ_APART=6e-2 '
                env = STAIR_ENV + env           # round 21: a near miss of a stair walk builds again at the same cut
                nm = '%04d-near2-%s-%s-%s' % (first + min(i, 799), r['target'], name, r['direction'])
                open('%s/jobs/%s.tsv' % (D, nm), 'w').write(HEAD + '0\t%s\t%s\t%s\t1\tnan\tnan\t%s\tnan\t0\n' % (r['target'], name, r['direction'], r['held']))
                open('%s/jobs/%s.job' % (D, nm), 'w').write(
                    '%s$PY -I -u family_step.py run jobs/%s.tsv donors details.csv out-near2 --mod 1,0 --deadline deadline '
                    '--buildsec 600 --shells 1 --where %s --tra %s --beat $BEAT\n' % (env, nm, where, tra))
                new.append(nm + '.job'); done.add(key); i += 1
    save_seen(work, 'near', done); save_sources(work, src)
    return new


def draw_rank(dv, n):
    """Job number of a draw (round 15): 1150 for a near miss 1e-7 above its bar at n = 300, up to 1750 at
    2e-4. The distance counts as dv / w, with w = sqrt(300 / n) the weight of n in the score relative to
    n = 300, so a light n ranks as if it were farther away."""
    key = dv / math.sqrt(300.0 / max(n, 300))
    return 1150 + int(min(600, max(0, 600 * math.log10(max(key, 1e-7) / 1e-7) / math.log10(2e-4 / 1e-7))))


def draw_pass(work, beats, floor=1e-7):
    """Second draws of the near misses on the same scipy (round 14): the same step with SQ_DRAW=1, 2 and 3,
    other HiGHS solver orders. A near miss is FLOOR (1e-7 since round 15: closer gave 1e-9 of score at most)
    to 2e-4 above its bar of now; jobs 1150 to 1750 by draw_rank, so they mix with the follow walks."""
    D = work + '/deploy'; done = seen(work, 'draw'); src = sources(work); new = []
    own = os.path.dirname(work) + '/take.tsv'      # an n this lane already certified is not drawn again
    bars = fs._bars(D + '/details.csv', list(beats) + ([own] if os.path.exists(own) else []))
    for d in outs(work):
        li = os.path.basename(d)
        if '-out-draw' in li:                   # a draw is not drawn again
            continue
        for fn in glob.glob(d + '/rows-*.tsv'):
            rows = list(csv.DictReader(open(fn), delimiter='\t')); walk = 'walk' in os.path.basename(fn)
            for r in rows:
                if r['state'].startswith(('refused', 'error', 'wrong')):
                    continue
                try:
                    dv = float(r['after_squeeze']) - bars[int(r['target'])]
                except (ValueError, KeyError):
                    continue
                k = int(r['shells']); key = '%s|%s|%s|%s|%s' % (li, r['target'], r['donor'], r['direction'], k)
                if not (floor <= dv <= 2e-4) or key in done:
                    continue
                if walk and k > 1:
                    prev = [p for p in rows if p['donor'] == r['donor'] and p['direction'] == r['direction'] and int(p['shells']) == k - 1]
                    f = prev and '%s/steps/%s-%s%dfrom%s.csv' % (d, prev[0]['target'], r['direction'], k - 1, r['donor'])
                    if not f or not os.path.exists(f):
                        continue
                    nd = int(prev[0]['target']); name = '%d-k%s' % (nd, hashlib.sha1(f.encode()).hexdigest()[:6])
                    if not os.path.exists('%s/donors/%s.csv' % (D, name)):
                        fs.write_rows('%s/donors/%s.csv' % (D, name), nd, fs.load(f)[nd])
                    base = r['donor'].split('+')[0]; so = src.get(base, '%s\t%s\t' % (base, base)).split('\t')
                    src.setdefault(name, '%s\t%d shell(s) %s from %s\t%s' % (name, k - 1, r['direction'], so[1], so[2] if len(so) > 2 else ''))
                else:
                    name = r['donor'].split('+')[0]
                    if not os.path.exists('%s/donors/%s.csv' % (D, name)):
                        continue
                done.add(key)
                env = 'SQ_LOOSE=1 ' + ('SQ_APART=3e-2 ' if r['direction'] == 'up' else '')
                dn = int(name.split('-')[0])
                if readable(fs.load('%s/donors/%s.csv' % (D, name))[dn], dn) not in ('', None):
                    env = 'SQ_LOOSE=1 SQ_WALLTOL=4e-2 SQ_APART=6e-2 '
                env = STAIR_ENV + env           # round 21: a near miss of a stair walk draws again at the same cut
                pr = draw_rank(dv, int(r['target'])) + DRAW_SHIFT
                for draw in (1, 2, 3):
                    nm = '%04d-draw%d-%s-%s-%s' % (pr, draw, r['target'], name, r['direction'])
                    open('%s/jobs/%s.tsv' % (D, nm), 'w').write(HEAD + '0\t%s\t%s\t%s\t1\tnan\tnan\t%s\tnan\t0\n' % (r['target'], name, r['direction'], r['held']))
                    open('%s/jobs/%s.job' % (D, nm), 'w').write(
                        'SQ_DRAW=%d SQ_KEEPNEAR=1e-4 %s$PY -I -u family_step.py run jobs/%s.tsv donors details.csv out-draw%d --mod 1,0 '
                        '--deadline deadline --buildsec 600 --shells 1 --beat $BEAT\n' % (draw, env, nm, draw))
                    new.append(nm + '.job')
    save_seen(work, 'draw', done); save_sources(work, src)
    return new


def _ns_of(path):
    try:
        return sorted({int(r['n']) for r in csv.DictReader(open(path))})
    except (KeyError, ValueError, OSError, csv.Error):
        return []


def near_metadata(path, n):
    """Read provenance from a near layout's JSON sidecar when it has no TSV ledger row."""
    sidecars = [path + '.json', os.path.splitext(path)[0] + '.json']
    stair = re.match(r'(.+/take-stair-c-r\d+)/near/(.+)-([ns])\.csv$', path)
    if stair:
        sidecars.append('%s/work/boxcopy/%s/raw-a/%s.json' % (stair[1], stair[3], stair[2]))
    for sidecar in sidecars:
        try:
            meta = json.load(open(sidecar))
        except (OSError, ValueError):
            continue
        if not isinstance(meta, dict) or meta.get('n', n) not in (n, str(n)):
            continue
        if isinstance(meta.get('source_override'), str) and isinstance(meta.get('licence_override'), str):
            return meta['source_override'], meta['licence_override']
        modules = meta.get('modules')
        if isinstance(modules, list) and modules and all(
                isinstance(m, dict) and all(isinstance(m.get(k), str) for k in ('id', 'source', 'licence')) for m in modules):
            return ('module build: ' + ', '.join(m['id'] + ' <' + m['source'] + '>' for m in modules) +
                    '; manifest ' + sidecar, '; '.join(sorted({m['licence'] for m in modules})))
        parts = meta.get('parts', {})
        if isinstance(parts, dict) and all(isinstance(parts.get(k), dict) for k in ('A', 'B')):
            descriptions = []; licences = []
            for k in ('A', 'B'):
                part = parts[k]; donor = part.get('source', [])
                if not isinstance(donor, list) or len(donor) != 2:
                    break
                descriptions.append('%sx%s+%s window of n=%s in %s (source ledger %s)' % (
                    part.get('w', '?'), part.get('h', '?'), part.get('excess', '?'), donor[1], donor[0], part.get('ledger', sidecar)))
                if part.get('source_record'):
                    descriptions[-1] += ' (recorded source: %s; original file %s)' % (
                        part['source_record'], part.get('original_file', donor[0]))
                licences.append(part.get('licence', 'see ' + sidecar))
            if len(descriptions) == 2:
                return ('forensics_rect.py pair: %s and %s; then fq flags %s; manifest %s' % (
                    descriptions[0], descriptions[1], meta.get('flags', '?'), sidecar), '; '.join(licences))
        if isinstance(meta.get('source'), str):
            return meta['source'], meta.get('licence', 'see ' + sidecar)
    reader = re.match(r'(.+/take-readers-r\d+)/near/(\d+)-(up|down)(\d+)(?:c([0-9.]+))?from(.+)\.csv$', path)
    if reader and int(reader[2]) == n:
        ledger = reader[1] + '/work/sources-all.tsv'
        try:
            parents = {r['donor']: r for r in csv.DictReader(open(ledger), delimiter='\t')}
        except (OSError, KeyError, csv.Error):
            parents = {}
        parent = parents.get(reader[6])
        if parent and parent.get('source') and parent.get('licence'):
            cut = ' at cut ' + reader[5] if reader[5] else ''
            return ('family_readers.py %s shell(s) %s%s from %s; source ledger %s' % (
                reader[4], reader[3], cut, parent['source'], ledger), parent['licence'])
    return '', ''


def extra_cands(a, takes):
    """Round 16: the layouts other lanes leave in the near/ folder of their take dir (near misses), and the
    csv files that a line of the handoff log addressed to family, follow or all names. Each walks as if it
    gained 1e-6 (after the moved n and the take rows that gain more)."""
    out = []; rnd = a.round
    nears = [(d, r) for r in [rnd] + list(getattr(a, 'fresh', None) or []) for d in sorted(glob.glob('%s/take-*-%s/near' % (a.scratch, r)))]
    for d, r in nears:              # round 20: the near/ folders of a --fresh round (r19, frozen) are starts too
        lane = os.path.basename(os.path.dirname(d))[5:-len(r) - 1]
        if lane == 'family' or lane.startswith('assemble'):
            continue
        tag = TAGS.get(lane, ''.join(w[0] for w in lane.split('-'))) + 'n' + r[1:]
        notes = {}
        for t in glob.glob(d + '/*.tsv'):
            try:
                for r in csv.DictReader(open(t), delimiter='\t'):
                    if r.get('n'):
                        notes[int(r['n'])] = (r.get('source', ''), r.get('licence', ''))
            except (ValueError, OSError, csv.Error):
                pass
        for p in sorted(glob.glob(d + '/*.csv')):
            for n in _ns_of(p)[:20]:
                so, lic = notes.get(n, ('', ''))
                if not so:
                    so, lic = near_metadata(p, n)
                out.append((1e-6, n, tag, ('file', p), 'the %s near miss of n = %d (%s%s)' % (lane, n, os.path.basename(p), ', ' + so if so else ''),
                            'ours, on: %s' % (lic or 'see %s' % d), set()))
    for hl in hlogs(a):
        if not os.path.exists(hl):
            continue
        lr = re.search(r'handoff-(?:r(\d+)|(\w+))\.log$', hl)  # round 19: a csv of an earlier log keeps that log's name
        lr = (lr.group(1) or lr.group(2)) if lr else rnd[1:]
        for l in open(hl):
            m = re.search(r'(\S+)\s*->\s*([^:]+):(.*)$', l)       # '<time> <lane> -> <lanes>: <what>, <path>'
            if not m or m.group(1) == 'family' or not re.search(r'\b(family|follow\w*|all)\b', m.group(2)):
                continue
            lane = m.group(1); tag = TAGS.get(lane, lane[:2]) + 'x' + lr
            for p in re.findall(r'(/\S+?\.csv)\b', m.group(3)):
                if not os.path.isfile(p):
                    continue
                ns = _ns_of(p)
                if len(ns) > 20:            # a whole submission: its moved n come through gate.json or the take dirs
                    continue
                if hl == hlogs(a)[0]:       # round 19: named in this round's log, so a new design of the round
                    NOW_PATHS.add(p)
                for n in ns:
                    so, lic = handoff_metadata(p, n)
                    detail = p + (', ' + so if so else '')
                    out.append((1e-6, n, tag, ('file', p), 'the %s layout of n = %d named in the handoff log (%s)' % (lane, n, detail),
                                'ours, on: ' + (lic or 'see the %s take dir' % lane), set()))
    return out


def handoff_metadata(path, n):
    """Use a sidecar or the certified file's own take ledger, when it is already present."""
    so, lic = near_metadata(path, n)
    if so and isinstance(lic, str) and lic:
        return so, lic
    if os.path.basename(path) != '%d.csv' % n:
        return '', ''
    ledger = os.path.join(os.path.dirname(path), 'take.tsv')
    try:
        if os.stat(ledger).st_mtime_ns < os.stat(path).st_mtime_ns:
            return '', ''
        for row in csv.DictReader(open(ledger), delimiter='\t'):
            if row.get('n') == str(n) and row.get('source') and row.get('licence'):
                return row['source'] + '; source ledger ' + ledger, row['licence']
    except (OSError, csv.Error):
        pass
    return '', ''


def enrich_handoff_sources(work):
    """Resolve a ledger that arrived after its handoff, only while the donor geometry still matches."""
    src = sources(work); changed = 0
    for name, line in list(src.items()):
        fields = line.split('\t')
        m = re.fullmatch(r'the (\S+) layout of n = (\d+) named in the handoff log \((/\S+\.csv)\)', fields[1])
        if not m:
            continue
        lane, number, path = m.groups(); n = int(number)
        so, lic = handoff_metadata(path, n)
        if not so:
            continue
        try:
            donor = fs.load('%s/deploy/donors/%s.csv' % (work, name))[n]
            current = fs.load(path)[n]
        except (OSError, KeyError, ValueError):
            continue
        if not np.array_equal(donor, current):
            continue
        fields[1] = 'the %s layout of n = %d named in the handoff log (%s, %s)' % (lane, n, path, so)
        fields[2] = 'ours, on: ' + lic
        src[name] = '\t'.join(fields); changed += 1
    if changed:
        save_sources(work, src)
    return changed


_HELD = {}
NOW_PATHS = set()       # csv files named in this round's handoff log (extra_cands)


def lane_tag(lane, rnd):
    """Tag of a lane's layouts: 'ts19' for twoshort in round 19; a take dir of an earlier round (--also,
    key 'twoshort-r17') keeps its own round number, 'ts17'."""
    m = re.match(r'(.+)-r(\d+)$', lane)
    base, num = (m.group(1), m.group(2)) if m else (lane, rnd[1:])
    return TAGS.get(base, ''.join(w[0] for w in base.split('-'))) + num


def unread_line(work, a, n, tag, P):
    """Round 19: a layout at n 790 and above that read_any does not take goes to the readers lane, with
    its rows in WORK/unread/, once per layout."""
    p = '%s/unread/%d-%s.csv' % (work, n, tag)
    if n < 790 or os.path.exists(p):
        return
    os.makedirs(work + '/unread', exist_ok=True)
    fs.write_rows(p, n, P)
    with open('%s/handoff-%s.log' % (a.scratch, a.round), 'a') as h:
        h.write('%s family -> readers: n = %d (%s) does not read with read_any, so its family walk cannot start; '
                'a layer reader can take it, %s\n' % (time.strftime('%H:%M', time.gmtime()), n, tag, p))


NEAR_COPY = 0.0     # cycle --nearcopy (round 20): a near/ or handoff layout within this of the side of a walked layout of its n is skipped
FOLLOW_AUDIT = None  # Optional admission hook: (n, path, source, licence) -> notices or None.


def walked_sides(done):
    """{n: [side]} of the layouts a walk already started from (round 20: 'S|n|side' lines in seen-follow)."""
    out = collections.defaultdict(list)
    for e in done:
        if e.startswith('S|'):
            _, n, sd = e.split('|'); out[int(n)].append(float(sd))
    return out


def donor_suffix(index):
    """Positive version numbers as a, b, ..., z, aa, ab, ... ."""
    suffix = ''
    while index:
        index, digit = divmod(index - 1, 26)
        suffix = chr(ord('a') + digit) + suffix
    return suffix


def follow_pass(work, take, a, takes):
    """Walks from every new design: the n that moved in the round before and every other lane's results."""
    D = work + '/deploy'; done = seen(work, 'follow'); src = sources(work); new = []
    sides = walked_sides(done)
    cand = []                       # (gain, n, tag, layout path, source, licence, directions already walked)
    if a.gate and os.path.exists(a.gate):
        best = {int(r['n']): r for r in csv.DictReader(open(a.best), delimiter='\t')} if a.best else {}
        for mv in json.load(open(a.gate))['moved']:
            n = mv['n']; b = best.get(n, {}); so = b.get('source', '')
            went = {'up'} if ' shell(s) up from' in so[:60] else ({'down'} if ' shell(s) down from' in so[:60] else set())
            if not so.startswith('family_step.py'):
                went = set()
            cand.append((mv['old'] - mv['new'], n, 'h' + a.round[1:], ('held', a.held), 'the held packing of n = %d (%s)' % (n, so),
                         'ours, on: %s' % b.get('licence', ''), went))
    for lane, d in takes.items():
        tag = lane_tag(lane, a.round)
        for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
            n = int(r['n']); p = '%s/%d.csv' % (d, n)
            if os.path.exists(p):
                cand.append((float(r['gain']), n, tag, ('file', p), 'the %s result of n = %d (%s)' % (lane, n, r.get('source', '')),
                             'ours, on: %s' % r.get('licence', ''), set()))
    if os.path.exists(take + '/take.tsv'):          # our own results: the walk that made one went on by itself
        for r in csv.DictReader(open(take + '/take.tsv'), delimiter='\t'):
            n = int(r['n']); went = {'up'} if ' shell(s) up from' in r['source'] else ({'down'} if ' shell(s) down from' in r['source'] else set())
            cand.append((float(r['gain']), n, 'f' + a.round[1:], ('file', '%s/%d.csv' % (take, n)), r['source'], r['licence'], went))
    cand += extra_cands(a, takes)
    for gain, n, tag, (how, path), so, lic, went in sorted(cand, key=lambda c: -c[0]):
        if FOLLOW_AUDIT is not None:
            notices = FOLLOW_AUDIT(n, path, so, lic)
            if notices is None:
                continue
            so, lic = notices
        key = '%d-%s:%r' % (n, tag, gain) + ('' if how == 'held' else '@' + path)
        if how == 'file':
            try:
                st = os.stat(path)
                key += '@%d:%d' % (st.st_mtime_ns, st.st_size)
            except OSError:
                continue
        if n < 1:
            continue
        if how == 'held':
            if path not in _HELD:
                _HELD[path] = fs.load(path, {mv['n'] for mv in json.load(open(a.gate))['moved']})
            P = _HELD[path][n]
        elif key not in done:
            try:
                P = fs.load(path)[n]
            except (KeyError, ValueError, OSError) as ex:
                log(work, 'follow %d-%s: %s does not load (%s)' % (n, tag, path, ex)); done.add(key); continue
        ck = '%d=%s' % (n, hashlib.sha1(np.ascontiguousarray(P).tobytes()).hexdigest()[:12]) if how == 'held' or key not in done else None
        if key in done:                     # ran before; a held start still notes its layout hash
            if ck:
                done.add(ck)
            continue
        done.add(key)
        if ck in done:                      # one layout, one walk, whoever names it
            continue
        done.add(ck)
        if NEAR_COPY > 0:               # round 20: one walk per layout within NEAR_COPY of side (take rows: 1e-8)
            sd = fs.canon(P)[0]; tol = NEAR_COPY if how == 'file' and ('/near/' in path or gain == 1e-6) else 1e-8
            twin = [x for x in sides[n] if abs(x - sd) < tol]
            if twin:
                log(work, 'follow %d-%s is a near copy: side %.10f is %.1e from a walked layout, skipped' % (n, tag, sd, abs(twin[0] - sd)))
                continue
        env = readable(P, n)
        if env is None:
            log(work, 'follow %d-%s does not read' % (n, tag))
            if getattr(a, 'newall', False):
                unread_line(work, a, n, tag, P)
            continue
        name = '%d-%s' % (n, tag); x = 0
        while os.path.exists('%s/donors/%s.csv' % (D, name)):
            x += 1; name = '%d-%s%s' % (n, tag, donor_suffix(x))
        fs.write_rows('%s/donors/%s.csv' % (D, name), n, P)
        src[name] = '%s\t%s\t%s' % (name, so, lic)
        if NEAR_COPY > 0:
            sides[n].append(sd); done.add('S|%d|%.12f' % (n, sd))
        fresh = [a.round] + list(getattr(a, 'fresh', None) or [])     # round 20: --fresh r19 counts as this round
        first = how == 'file' and '/near/' not in path and any(
            '/take-%s-%s' % (ln, r) in path for ln in (getattr(a, 'first', None) or []) for r in fresh)
        newall = getattr(a, 'newall', False)
        now = how == 'file' and '/near/' not in path and (any(('-%s/' % r) in path for r in fresh) or path in NOW_PATHS)
        for di in ('up', 'down'):
            pr = 1000 + rank(gain if di == 'up' else gain / 10)
            if first and newall:            # round 19: the --first lanes at 1000 to 1049
                pr = 1000 + min(49, rank(gain) // 20)
            elif first:                     # round 17: a new design (--first LANE) walks both ways before the rest
                pr = 1000 + min(99, rank(gain) // 10)
            elif di in went:                # the walk that made our own result goes on that way by itself
                pr = 1000 + rank(gain * 1e-6)
            elif newall and now:            # round 19: every other new design of the round, both ways, 1050 to 1099
                pr = 1050 + min(49, rank(gain) // 20)
            elif newall:                    # round 19: a layout of an earlier round (--also) waits for the new ones
                pr = max(1100, pr)
            new.append(walk_job(D, pr, name, di, env))
    save_seen(work, 'follow', done); save_sources(work, src)
    return new


# ---------------------------------------------------------------- dealing

def deal(work, bx, jobs):
    """Send donors and job tables to every box, then each job to the box with the shortest queue for its
    slots and speed (near builds and fault jobs to the boxes with speed 1 only)."""
    if not jobs:
        return {}
    D = work + '/deploy'
    load = {}
    for b in bx:
        if b['host'] == '-':
            sh('rsync -a --exclude "*.job" %s/donors %s/jobs %s/qin %s/' % (D, D, D, b['dir']))
            q = len([j for j in os.listdir(b['dir'] + '/queue') if '-draw' not in j]) if os.path.isdir(b['dir'] + '/queue') else 0
        else:
            sh('rsync -a --exclude "*.job" %s/donors %s/jobs %s/qin %s:%s/' % (D, D, D, b['host'], b['dir']), 300)
            # queued draws do not count: they run only after every walk (job names sort) and --drawidle stops them
            q = int((sh("ssh %s 'ls %s/queue | grep -vc -- -draw'" % (b['host'], b['dir'])) or '0').strip() or 0)
        load[b['name']] = q
    got = {}
    for j in sorted(jobs):
        fast = '-near2-' in j or '-fault-' in j
        b = min((b for b in bx if b['speed'] >= 1 or not fast), key=lambda b: (load[b['name']] + 1) / (b['slots'] * b['speed']))
        load[b['name']] += 1; got.setdefault(b['name'], []).append(j)
        with open(work + '/assign.tsv', 'a') as h:
            h.write('%s\t%s\n' % (j, b['name']))
    for b in bx:
        js = got.get(b['name'])
        if not js:
            continue
        if b['host'] == '-':
            for j in js:
                shutil.copy('%s/jobs/%s' % (D, j), '%s/queue/%s' % (b['dir'], j))
        else:
            sh('cd %s/jobs && rsync -a %s %s:%s/queue/' % (D, ' '.join(js), b['host'], b['dir']), 300)
    return {k: len(v) for k, v in got.items()}


def box_state(bx):
    """{box: (queued jobs that are not draws, running job names, queued draws)} (round 20)."""
    out = {}
    for b in bx:
        if b['host'] == '-':
            qs = os.listdir(b['dir'] + '/queue') if os.path.isdir(b['dir'] + '/queue') else []
            q = len([j for j in qs if '-draw' not in j]); qd = len(qs) - q
            run = sorted(os.listdir(b['dir'] + '/run')) if os.path.isdir(b['dir'] + '/run') else []
        else:
            t = sh("ssh -o ConnectTimeout=8 %s 'cd %s; ls queue | grep -vc -- -draw; ls queue | grep -c -- -draw; ls run'" % (
                b['host'], b['dir']), 60).split()
            if len(t) < 2:
                out[b['name']] = (10 ** 6, [], 0); continue
            q = int(t[0]); qd = int(t[1]); run = t[2:]
        out[b['name']] = (q, run, qd)
    return out


DRAW_DEPTH = 3


def idle_draws(work, bx, walks, dj):
    """Round 20 (--drawidle): draws wait in WORK/pending-draw.txt and go out to the free slots of a box after
    this cycle's walks were dealt, plus DRAW_DEPTH per slot queued behind its walks. In a cycle that deals
    walks, a box with walks in its queue first stops as many running draws (the python of the job and its
    children) and puts them back in the pending list. (Until 23:15 on 2026-11-13 draws went out only in a cycle that dealt no walk at all, so
    with new layouts in every cycle a free slot on the other box stayed idle.)"""
    p = work + '/pending-draw.txt'
    pend = set(open(p).read().split()) if os.path.exists(p) else set()
    pend |= set(dj)
    st = box_state(bx); got = {}; stopped = []
    for b in bx:
        q, run, qd = st[b['name']]
        draws = [j for j in run if '-draw' in j]
        if walks and q > 0 and draws and not DRAW_KEEP:     # round 21 (--drawkeep): the walk waits for a free slot
            kill = sorted(draws, reverse=True)[:q]
            sh("ssh %s 'for j in %s; do for p in $(pgrep -f \"[j]obs/${j%%.job}.tsv\"); do pkill -P $p; kill $p; done; done'" % (
                b['host'], ' '.join(kill)), 60)
            stopped += kill; pend |= set(kill); run = [j for j in run if j not in kill]
        # a draw takes 20 s to 5 min and a cycle 3 min: keep DRAW_DEPTH draws per slot queued behind the walks
        # (the queued walks of the box take their share first; a box that just stopped draws is topped up too)
        free = b['slots'] - len(run) - q + DRAW_DEPTH * b['slots'] - qd
        js = sorted(pend)[:max(0, free)]
        if js:
            got.update(deal(work, [b], js)); pend -= set(js)
    open(p + '.tmp', 'w').write('\n'.join(sorted(pend)) + '\n'); os.replace(p + '.tmp', p)
    if stopped:
        log(work, 'drawidle: stopped %d running draws for walks: %s' % (len(stopped), ' '.join(stopped)))
    return got, len(pend)


# ---------------------------------------------------------------- commands

def cmd_cycle(a):
    global WALK_MISSES, DRAW_SHIFT, FILL_HERE, NEAR_COPY, NEAR_OUT, STAIR_ENV, DRAW_KEEP
    WALK_MISSES = a.misses; DRAW_SHIFT = a.drawshift; FILL_HERE = a.fillhere; NEAR_COPY = a.nearcopy; NEAR_OUT = a.nearout
    STAIR_ENV = 'SQ_CUTREACH=9 SQ_STAIRCUT=1 ' if a.staircut else ''
    DRAW_KEEP = a.drawkeep
    NEAR_FROM[:] = a.nearfrom
    work = os.path.abspath(a.work); take = os.path.dirname(work); bx = boxes(work)
    while True:
        t0 = time.time()
        takes = other_takes(take, a.round, a.scratch)
        for r in a.also:                # round 19: the frozen take dirs of an earlier round are bars and starts too
            takes.update({'%s-%s' % (ln, r): d for ln, d in other_takes(take, r, a.scratch).items()})
        takes.update(handoff_takes(a, takes, take))
        beats = [d + '/take.tsv' for d in takes.values()]
        enriched = enrich_handoff_sources(work)
        if enriched:
            log(work, 'enriched %d handoff sources from matching donor files' % enriched)
        collect(work, bx)
        t1 = time.time()
        if a.quenchfirst:
            keep, qj = certify_after_quench(work, take, a.details, beats, bx)
        else:
            keep = certify(work, take, a.details, beats, bx)
            qj = quench_pass(work, take, keep)
        t2 = time.time()
        prune(work, take)
        announce(work, take, a, keep)
        try:
            nnear = near_out(work, take, a, beats)
        except Exception as ex:          # the export is a handoff: it never stops the loop
            nnear = -1; log(work, 'nearout: %s' % ex)
        push_beats(work, bx, takes)
        nj = near_pass(work, a.nearprio)
        dj = draw_pass(work, beats) if a.draws else []
        fj = follow_pass(work, take, a, takes)
        if a.drawidle:                  # round 20: draws only to free slots, and walks stop running draws
            got = deal(work, bx, qj + nj + fj)
            gd, npend = idle_draws(work, bx, qj + nj + fj, dj)
            got = {k: got.get(k, 0) + gd.get(k, 0) for k in set(got) | set(gd)}
        else:
            got = deal(work, bx, qj + nj + dj + fj); npend = 0
        log(work, 'cycle: %d kept (%s), %d quench, %d near, %d draws (%d pending), %d follow, %d in near/, dealt %s, beats %s, certify %.0fs, %.0fs' % (
            len(keep), ' '.join(l.split()[1] for l in keep), len(qj), len(nj), len(dj), npend, len(fj), nnear, got, ','.join(sorted(takes)),
            t2 - t1, time.time() - t0))
        if a.once or (a.until and time.time() > a.until) or os.path.exists(work + '/STOPLOOP'):
            break
        time.sleep(max(10, a.every - (time.time() - t0)))


def cmd_left(a):
    """Round PREVWORK's jobs that never ran (its queue and run lists) into WORK, renamed 5xxx (walks) and
    8xxx (public donor pairs), with their donors and sources."""
    work = os.path.abspath(a.work); prev = os.path.abspath(a.prev); D = work + '/deploy'; P = prev + '/deploy'
    src = sources(work)
    psrc = {l.split('\t')[0]: l for l in open(prev + '/' + a.prevsources).read().splitlines()[1:]}
    names = []
    for fn in glob.glob(prev + '/jobs-*.txt'):
        for l in open(fn):
            st, j = l.split()
            if st in ('queue', 'run'):
                names.append(j)
    new = []
    for i, j in enumerate(sorted(names)):
        base = j[:-4]; kind = base.split('-')[1]
        pr = (8000 if kind.startswith('raw') else 5000) + i
        nm = '%04d-left%s' % (pr, base[4:])
        jf = '%s/jobs/%s' % (P, j)
        if not os.path.exists(jf):                  # a job renamed in its queue only: the file of the same pair
            jf = (glob.glob('%s/jobs/*%s' % (P, j[4:])) or [None])[0]
            if jf is None:
                continue
        line = open(jf).read()
        tb = re.search(r'jobs/(\S+)\.tsv', line).group(1)
        tsv = open('%s/jobs/%s.tsv' % (P, tb)).read()
        rows = list(csv.DictReader(tsv.splitlines(), delimiter='\t'))
        for r in rows:
            dn = r['donor'].split('+')[0]
            if not os.path.exists('%s/donors/%s.csv' % (D, dn)) and os.path.exists('%s/donors/%s.csv' % (P, dn)):
                shutil.copy('%s/donors/%s.csv' % (P, dn), '%s/donors/%s.csv' % (D, dn))
            if dn in psrc and dn not in src:
                src[dn] = psrc[dn]
        open('%s/jobs/%s.tsv' % (D, nm), 'w').write(tsv)
        line = line.replace('jobs/%s.tsv' % tb, 'jobs/%s.tsv' % nm)
        open('%s/jobs/%s.job' % (D, nm), 'w').write(line)
        new.append(nm + '.job')
    save_sources(work, src)
    got = deal(work, boxes(work), new)
    log(work, 'left: %d jobs from %s, dealt %s' % (len(new), prev, got))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('cycle'); q.add_argument('work'); q.add_argument('--details', required=True); q.add_argument('--held')
    q.add_argument('--gate'); q.add_argument('--best'); q.add_argument('--round', default='r13')
    q.add_argument('--scratch', default='$SCRATCH/bounties-squares'); q.add_argument('--every', type=float, default=300)
    q.add_argument('--until', type=float); q.add_argument('--once', action='store_true')
    q.add_argument('--nearprio', type=int, default=200, help='first job number of the near builds (200: before every walk)')
    q.add_argument('--draws', action='store_true', help='second draws of every near miss with SQ_DRAW=1, 2 and 3 (jobs 1150 to 1750)')
    q.add_argument('--logs', nargs='*', default=[], help='more handoff logs in SCRATCH to read (round 17: handoff-d5.log)')
    q.add_argument('--first', nargs='*', default=[], help='lanes whose take dir layouts walk first, both ways (jobs 1000 to 1099)')
    q.add_argument('--misses', type=int, default=2, help='a walk ends after this many steps in a row that do not win (round 17: '
                   'after a miss, 121 steps gave 2 below the bar; 1 stops a walk at its first miss)')
    q.add_argument('--also', nargs='*', default=[], help='earlier rounds whose take dirs are bars and starts too (round 19: r17)')
    q.add_argument('--newall', action='store_true', help='round 19: every layout of this round walks both ways at 1050 to 1099, '
                   'after the --first lanes (1000 to 1049); an earlier round starts at 1100; a layout at n >= 790 that does not '
                   'read gets a handoff line to the readers lane')
    q.add_argument('--drawshift', type=int, default=0, help='added to the job number of every draw (round 19: 800, after the walks)')
    q.add_argument('--fillhere', action='store_true', help='score new raw files in the loop, never on a worker box')
    q.add_argument('--fresh', nargs='*', default=[], help='round 20: --also rounds whose take dirs and near/ folders count as '
                   'new designs of this round (--first and --newall order)')
    q.add_argument('--nearcopy', type=float, default=0.0, help='round 20: skip a near/ or handoff layout within this of the side '
                   'of a layout a walk already started from (take rows: 1e-8); 0 is off')
    q.add_argument('--drawidle', action='store_true', help='round 20: draws go out only to free slots in a cycle with no walk, '
                   'and walks in a queue stop running draws (they go back to WORK/pending-draw.txt)')
    q.add_argument('--nearout', type=float, default=0.0, help='round 21: the best near miss of each n within this of the bar '
                   'goes to TAKE/near/ (with near.tsv) for the kick lanes; 0 is off')
    q.add_argument('--nearfrom', nargs='*', default=[], help='round 21: more out dirs (globs) that only --nearout reads, '
                   'such as the frozen work dir of the round before')
    q.add_argument('--staircut', action='store_true', help='round 21: every walk, near build and draw job gets SQ_CUTREACH=9 SQ_STAIRCUT=1, so a '
                   'staircase corner opens; both act only where the plain cut would refuse')
    q.add_argument('--drawkeep', action='store_true', help='round 21: with --drawidle, a running draw is never stopped; '
                   'a queued walk takes the next free slot (walks sort before draws)')
    q.add_argument('--quenchfirst', action='store_true', help='round 22: stage certified candidates under work/, then '
                   'publish only remote fq quenches of those certified csv files')
    q.set_defaults(fn=cmd_cycle)
    q = sp.add_parser('left'); q.add_argument('work'); q.add_argument('prev'); q.add_argument('--prevsources', default='sources-r12.tsv')
    q.set_defaults(fn=cmd_left)
    q = sp.add_parser('fill'); q.add_argument('out'); q.add_argument('where'); q.add_argument('files', nargs='+')
    q.set_defaults(fn=cmd_fill)
    if len(sys.argv) > 2 and sys.argv[1] == 'ctake':    # the rest goes to family_step.py take as it is
        a = argparse.Namespace(cache=sys.argv[2], rest=sys.argv[3:]); return cmd_ctake(a)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
