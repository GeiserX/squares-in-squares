#!/usr/bin/env python3
"""The chain from a staircase corner to a certified layout, for the stair-b slice (m 24 to 27, k 4 to 20).

  stair-b_chain.py pick  BASE.pkl OUT.pkl [--counts N,N] [--per-class K] [--max-loss X]
                         the corners of a `twoshort_corner.py stair` base file worth a table: the K of lowest loss in
                         every count class of arm 1 (default 2), or the named counts
  stair-b_chain.py lib   LIB NEWLIB WORKDIR TAG BASE.pkl [BASE.pkl ...] [--per 1] [--max-loss 5.0]
                         `zone_corner.py adopt`, `table` and `merge`: NEWLIB is LIB with the corners added, and
                         NEWLIB/new-ids.txt lists them
  stair-b_chain.py union BASELIB NEWLIB LIB [LIB ...]
                         NEWLIB is BASELIB with the staircase corners of every LIB (libraries that `lib` made) and
                         their tables, so that one generator run pairs every corner with the far zones of BASELIB;
                         NEWLIB/new-ids.txt lists them. A module of BASELIB that has no table is left out
  stair-b_chain.py queue NEWLIB DETAILS.csv OUT.tsv --ns N,N,... [--slack 0.003] [--top 3] [--depth 0.05]
                         `modules.py queue` over the named n, only the choices that hold a new corner
  stair-b_chain.py run   LIST NEWLIB RAWDIR DETAILS.csv --fq FQ --deadline FILE [--part I/K]
                         `modules.py job` for every line of LIST ("HOW NAME N CORNER FAR1 FAR2 S1 S2 F", from
                         `stair-b_plan.py rows`), one at a time, until the time in FILE (epoch seconds); a name
                         that another runner took (RAWDIR/seen/NAME) is skipped, so several runners share one list
  stair-b_chain.py quench TAKEDIR QDIR
                         the fq quench of `zone_corner.quench` on a copy of every certified file of TAKEDIR, as
                         QDIR/<n>-fq.csv with the build's record beside it, for one more `modules.py take`

Every step runs a tool of this lane as it is (`python -I`): twoshort_corner.py, zone_corner.py and modules.py are
imported or called and not changed. Our own code. Reads pickles of our own tools only.
"""
import glob, json, os, pickle, shutil, subprocess, sys, time

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
PY = sys.executable


def opt(a, name, default, kind=str):
    return kind(a[a.index(name) + 1]) if name in a else default


def tool(name, *args, log=None):
    cmd = [PY, '-I', os.path.join(LANE, name)] + [str(x) for x in args]
    if log:
        with open(log, 'a') as h:
            return subprocess.call(cmd, stdout=h, stderr=subprocess.STDOUT)
    return subprocess.call(cmd)


def cmd_pick(a):
    import zone_corner as ZC
    base = pickle.load(open(a[0], 'rb'))
    counts = [int(x) for x in opt(a, '--counts', '').split(',') if x]
    per = opt(a, '--per-class', 2, int); cut = opt(a, '--max-loss', 9e9, float)
    rows = []
    for b in base:
        mod = ZC.cmod(b['c1'], b['c2'], b['lean1'], b['lean2'])
        rows.append((ZC.loss_of(mod, b['f'], b['count'], b['y0'], b['x0']), b))
    rows.sort(key=lambda t: t[0]); keep = []; seen = {}
    for loss, b in rows:
        cl = b['count'] % b['c1']
        if counts:
            if b['count'] in counts: keep.append(b)
        elif loss <= cut and seen.get(cl, 0) < per:
            seen[cl] = seen.get(cl, 0) + 1; keep.append(b)
        else: continue
        print('%s count %d class %d (class of arm 2: %d) loss %.4f y0 %.5f x0 %.5f' % (b['id'], b['count'], cl, b['count'] % b['c2'], loss, b['y0'], b['x0']))
    pickle.dump(keep, open(a[1] + '.tmp', 'wb')); os.replace(a[1] + '.tmp', a[1])
    print('kept %d of %d corners' % (len(keep), len(base)))
    return 0


def cmd_lib(a):
    lib, new, work, tag = a[:4]
    bases = [x for x in a[4:] if not x.startswith('--') and x.endswith('.pkl')]
    per = opt(a, '--per', 1, int); cut = opt(a, '--max-loss', 5.0, float)
    states, zones = work + '/states-' + tag, work + '/zones-' + tag
    os.makedirs(states, exist_ok=True); log = work + '/lib-%s.log' % tag
    for b in bases:
        tool('zone_corner.py', 'adopt', b, states, log=log)
    tool('zone_corner.py', 'table', states, zones, work + '/corners-%s.tsv' % tag, '--per', per, '--tag', tag, log=log)
    rc = tool('zone_corner.py', 'merge', lib, zones, new, '--max-loss', cut, log=log)
    have = {q['id'] for q in pickle.load(open(lib + '/library.pkl', 'rb'))['mods']}
    L = pickle.load(open(new + '/library.pkl', 'rb')); ids = []
    for q in L['mods']:                              # a staircase corner is our own design: modules.usable takes a module
        if q['id'] not in have:                      # of a zone search only with this mark (the queue of modules.py)
            ids.append(q['id'])
            if q['licence'] == 'our own': q['ours'] = True
    pickle.dump(L, open(new + '/library.pkl.tmp', 'wb')); os.replace(new + '/library.pkl.tmp', new + '/library.pkl')
    with open(new + '/new-ids.txt', 'w') as h: h.write('\n'.join(ids) + '\n')
    print('%d new corners in %s (merge exit %d)' % (len(ids), new, rc))
    for i in ids: print(' ', i)
    return 0


def cmd_union(a):
    base, new = a[:2]
    L = pickle.load(open(base + '/library.pkl', 'rb')); T = pickle.load(open(base + '/lens.pkl', 'rb'))
    n0 = len(L['mods']); L['mods'] = [q for q in L['mods'] if q['id'] in T]
    if len(L['mods']) < n0: print('%d modules of %s have no table and are left out' % (n0 - len(L['mods']), base))
    have = {q['id'] for q in L['mods']}; ids = []
    for lib in a[2:]:
        l2 = pickle.load(open(lib + '/library.pkl', 'rb')); t2 = pickle.load(open(lib + '/lens.pkl', 'rb')); k = 0
        for q in l2['mods']:
            if q['id'] in have or q['id'] not in t2 or q['kind'] != 'corner': continue
            if q['licence'] != 'our own' or 'staircase corner' not in q['src']: continue
            q['ours'] = True; L['mods'].append(q); T[q['id']] = t2[q['id']]; have.add(q['id']); ids.append(q['id']); k += 1
        print('%d staircase corners from %s' % (k, lib), flush=True)
    os.makedirs(new, exist_ok=True)
    for name, obj in (('library.pkl', L), ('lens.pkl', T)):
        pickle.dump(obj, open('%s/%s.tmp' % (new, name), 'wb')); os.replace('%s/%s.tmp' % (new, name), '%s/%s' % (new, name))
    with open(new + '/new-ids.txt', 'w') as h: h.write('\n'.join(ids) + '\n')
    print('%d staircase corners in %s, %d modules' % (len(ids), new, len(L['mods'])))
    return 0


def cmd_queue(a):
    new, details, out = a[:3]
    ns = [x for x in opt(a, '--ns', '').split(',') if x]
    nsf = out + '.ns'
    with open(nsf, 'w') as h: h.write('\n'.join(ns) + '\n')
    args = ['queue', new, details, out, '--top', opt(a, '--top', '3'), '--slack', opt(a, '--slack', '0.003'),
            '--need', new + '/new-ids.txt', '--ns', nsf]
    if '--depth' in a: args += ['--depth', opt(a, '--depth', '0.05')]
    return tool('modules.py', *args)


def cmd_run(a):
    lst, lib, raw, details = a[:4]
    fq = opt(a, '--fq', None); dl = opt(a, '--deadline', None)
    pi, pk = (int(v) for v in opt(a, '--part', '0/1').split('/'))
    os.makedirs(raw + '/seen', exist_ok=True); os.makedirs(raw + '/log', exist_ok=True)
    done = 0
    for j, ln in enumerate(open(lst).read().splitlines()):
        w = ln.split()
        if len(w) != 9 or j % pk != pi: continue
        how, name = w[0], w[1]
        if dl and time.time() >= float(open(dl).read().split()[0]): print('deadline'); break
        if os.path.exists(raw + '/STOP'): print('STOP'); break
        try: os.mkdir('%s/seen/%s' % (raw, name))          # one runner per name
        except FileExistsError: continue
        args = ['job', lib, raw, details] + w[1:] + ['--squeeze', how] + (['--fq', fq] if fq else [])
        tool('modules.py', *args, log='%s/log/%s.log' % (raw, name)); done += 1
    print('ran %d builds of %s' % (done, lst))
    return 0


def cmd_quench(a):
    import csv
    import zone_corner as ZC
    take, qdir = a[:2]
    os.makedirs(qdir, exist_ok=True)
    for r in csv.DictReader(open(take + '/take.tsv'), delimiter='\t'):
        n = int(r['n']); src = '%s/%d.csv' % (take, n); dst = '%s/%d-fq.csv' % (qdir, n)
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): continue
        shutil.copy(src, dst)
        side = (1.0 + float(r['new'])) * n ** 0.5    # the record of the build this file came from: the one whose built side
        rec = None; work = os.path.dirname(qdir.rstrip('/'))   # is the side of the take file, in every raw dir of the work dir
        for p in glob.glob(work + '/raw*/%d-*.json' % n) + glob.glob(work + '/*/raw*/%d-*.json' % n):
            j = json.load(open(p))
            if j.get('built') is not None and (rec is None or abs(j['built'] - side) < abs(rec['built'] - side)): rec = j
        if rec is not None and abs(rec['built'] - side) > 1e-6:
            print('n=%d: no build record within 1e-6 of side %.9f, not quenched' % (n, side), flush=True); os.remove(dst); continue
        if rec is not None: json.dump(rec, open(dst[:-4] + '.json', 'w'))
        ZC.quench(n, dst, None)
    return 0


if __name__ == '__main__':
    cmds = dict(pick=cmd_pick, lib=cmd_lib, union=cmd_union, queue=cmd_queue, run=cmd_run, quench=cmd_quench)
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__); sys.exit(2)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]) or 0)
