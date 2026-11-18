#!/usr/bin/env python3
"""backlog_worker: one slot of the backlog lane on a compute box (avenues/backlog.md, Rounds 25 and 26).

Runs in DIR (the box scratch) with lane/ beside it (a copy of lanes/squares code). It waits for SLOT/next.json,
written by backlog_ctl.py after it claimed the item in the handoff log, and runs it with the owner lane's tool:
  owner invent   lane/invent_rest.py N START RUN --seconds S --seed K --modes lkick --bar SIDE --deadline deadline
                 [--fq FQ]  (the settings of take-invent-r24/work/worker24.py)
  owner midm     lane/midm_scan.py --n N --sub START --out RUN --fq FQ --seconds S --seed K --modes kick,lkick
                 --ref 0 --deadline deadline --kicks SIGMA --stop6  (the settings of take-midm-r25 worker25.py, no bank)
  owner harvest  FQ quench --in START --out RUN/raw/<n>-fq.csv --no-alm --loosen 1.0 --pit 40 --flip-top 8,
                 120 s (take-harvest-r24/work/remote_run.py)
Then the step every lane runs: floatsafe at 2.2e-11 of the lowest raw file, and one fq quench from that certified
file (lane/midm_fqonce.py). RUN/final/<n>.csv is the lower of the two; RUN/done.json says what happened.
The slot stops at the deadline file or at SLOT/STOP.

  backlog_worker.py DIR SLOT
"""
import csv, json, os, signal, subprocess, sys, time, traceback

D = os.path.abspath(sys.argv[1]); SLOT = sys.argv[2]
os.chdir(D); sys.path.insert(0, os.path.join(D, 'lane'))
import floatsafe  # noqa: E402
try:                                    # round 29: border's bisected dilation, 3e-10 to 9e-10 of side lower
    import backlog_finesafe
    FSAFE = backlog_finesafe.work
except ImportError:
    FSAFE = floatsafe.work

BASE = '$SCRATCH/squares-base'
PY = BASE + '/venv/bin/python'; FQ = BASE + '/fq'
if os.path.exists('box.json'):          # round 26: a box without the shared base names its own python and fq
    _b = json.load(open('box.json')); PY = _b.get('py', PY); FQ = _b.get('fq', FQ)
DEADLINE = float(open('deadline').read())
HFLAGS = ['--no-alm', '--loosen', '1.0', '--pit', '40', '--flip-top', '8']
KILL = [None]                           # round 34: RUN/KILL of the running job (the ctl writes it when a lower row came in)


def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def log(s):
    with open('slot%s.log' % SLOT, 'a') as h:
        h.write(stamp() + ' ' + s + '\n')


def writecsv(p, rows):
    with open(p, 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader(); w.writerows(rows)


def bounded(cmd, h, seconds):
    t = min(seconds, DEADLINE - time.time())
    if t <= 0:
        raise TimeoutError('deadline')
    p = subprocess.Popen(cmd, stdout=h, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        t0 = time.time()
        while True:                          # round 34 (brief 6e): poll every 5 s for the ctl's RUN/KILL file
            try:
                p.wait(timeout=min(5, max(0.1, t - (time.time() - t0))))
                return p.returncode
            except subprocess.TimeoutExpired:
                if time.time() - t0 >= t:
                    raise
                if KILL[0] and os.path.exists(KILL[0]):
                    log('KILL file %s: stopping the search, the raw files so far still certify' % KILL[0])
                    raise subprocess.TimeoutExpired(cmd, t)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGTERM)
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait()
        return 124


def probed(cmd, h, seconds, rd, n, probe, res):
    """Round 31 (brief 6c): run a long midm kick, but stop it when no try improved after PROBE seconds. A try that
    improves writes RUN/raw/<n>-*.csv; the scan log RUN/scan-<n>-<seed>.tsv has one line per try. The probe waits
    for at least 3 tries (a big n takes 20 to 40 s a try) and gives up waiting at 2 * PROBE."""
    t = min(seconds, DEADLINE - time.time())
    if t <= 0:
        raise TimeoutError('deadline')
    p = subprocess.Popen(cmd, stdout=h, stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time(); decided = False
    while True:
        try:
            p.wait(timeout=5)
            return p.returncode
        except subprocess.TimeoutExpired:
            pass
        el = time.time() - t0
        if el >= t or (KILL[0] and os.path.exists(KILL[0])):
            break
        if not decided and el >= probe:
            finds = [f for f in os.listdir(rd + '/raw') if f.endswith('.csv') and f.startswith('%d-' % n) and '-start' not in f]
            tries = 0
            for f in os.listdir(rd):
                if f.startswith('scan-') and f.endswith('.tsv'):
                    tries += sum(1 for line in open(os.path.join(rd, f)) if line[:1].isdigit())
            if finds:
                decided = True; res['probe'] = 'kept: %d finds after %.0f s' % (len(finds), el)
            elif tries >= 3 or el >= 2 * probe:
                decided = True; res['probe'] = 'stopped: no find in %d tries after %.0f s' % (tries, el)
                break
    os.killpg(p.pid, signal.SIGTERM)
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.wait()
    return 124


def run(j):
    n = j['n']; rd = os.path.join(D, 'runs', j['rid']); os.makedirs(rd + '/raw', exist_ok=True)
    start = os.path.join(rd, 'start.csv'); KILL[0] = os.path.join(rd, 'KILL')
    res = {'id': j['id'], 'rid': j['rid'], 'n': n, 'owner': j['owner'], 'slot': SLOT, 'started': stamp()}
    if j.get('include_start') and os.path.exists(start):
        # round 27 re-open: the start itself is a raw file, so floatsafe and the fq quench certify it as it is
        # when the kick finds nothing lower
        import shutil
        shutil.copy(start, rd + '/raw/%d-start.csv' % n)
    with open(rd + '/run.log', 'a') as h:
        if j['owner'] == 'invent':
            sec = int(min(j['seconds'], DEADLINE - time.time() - 300))
            cmd = [PY, '-I', 'lane/invent_rest.py', str(n), start, rd, '--seconds', str(sec), '--seed', str(j.get('seed', 123)),
                   '--modes', 'lkick', '--bar', repr(j['bar_side']), '--deadline', 'deadline']
            if j.get('fq'):
                cmd += ['--fq', FQ]
            res['rc'] = bounded(cmd, h, sec + 100)
        elif j['owner'] == 'midm':
            sec = int(min(j['seconds'], DEADLINE - time.time() - 300))
            cmd = [PY, '-I', 'lane/midm_scan.py', '--n', str(n), '--sub', start, '--out', rd, '--fq', FQ, '--seconds', str(sec),
                   '--seed', str(j.get('seed', 1)), '--modes', j.get('modes', 'kick,lkick'), '--ref', '0', '--deadline', 'deadline',
                   '--kicks', str(j.get('sigma', 0.04)), '--stop6']
            if j.get('probe'):
                res['rc'] = probed(cmd, h, sec + 100, rd, n, float(j['probe']), res)
            else:
                res['rc'] = bounded(cmd, h, sec + 100)
        elif j['owner'] == 'harvest':
            # harvest's remote_run.py: one fq quench with its flags, 120 s, on the start in fq's text format
            import methods_lp as mlp
            from midm_scan import to_fq, from_fq, quench
            P = mlp.load(start, {n})[n]; s0, X = to_fq(P)
            tmp = rd + '/tmp'; os.makedirs(tmp, exist_ok=True)
            s2, X2 = quench(FQ, tmp, s0, X, HFLAGS, timeout=max(1, min(120, DEADLINE - time.time())))
            h.write('harvest fq %r -> %r\n' % (s0, s2))
            res['rc'] = 0 if s2 is not None else 1
            if s2 is not None and s2 < s0 - 1e-12:
                Q = from_fq(X2)
                writecsv(rd + '/raw/%d-fq.csv' % n, [dict(n=n, square_id=i, x=repr(float(x)), y=repr(float(y)), angle=repr(float(a)))
                                                      for i, (x, y, a) in enumerate(Q)])
        elif j['owner'] == 'readers':
            # readers' run25.sh: one walk of family_readers.py from a copy of its box (code, donors, details, beat)
            rdir = os.path.join(D, 'readers')
            env = dict(os.environ, SQ_TMP=rd + '/tmp', SQ_FQ=FQ, SQ_APART='3e-2', SQ_TWIN='5.5e-2',
                       OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
            os.makedirs(rd + '/tmp', exist_ok=True)
            beat = sorted(os.path.join(rdir, 'beat', b) for b in os.listdir(rdir + '/beat') if b.endswith('.tsv'))
            maxsteps = '2' if j['spec'].endswith('-return.tsv') else '6'
            # the walk file keeps its queue name: readers' defer.tsv lets a walk run only when the name has its prefix
            wf = os.path.join(rd, os.path.basename(j['spec']))
            if not os.path.exists(wf):
                os.link(rd + '/spec.tsv', wf)
            cmd = [PY, '-I', '-u', 'family_readers.py', 'walk', wf, 'donors', 'details.csv', rd,
                   '--deadline', os.path.join(D, 'deadline'), '--misses', '2', '--min-progress', '1e-7', '--nearout', '0.015',
                   '--maxsteps', maxsteps, '--beat'] + beat
            t = min(j.get('seconds', 1200), DEADLINE - time.time() - 300)
            p = subprocess.Popen(cmd, cwd=rdir, env=env, stdout=h, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                p.wait(timeout=max(1, t)); res['rc'] = p.returncode
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL); p.wait()
                res['rc'] = 124
        else:
            raise ValueError('no adapter for ' + j['owner'])
    killed = KILL[0] if KILL[0] and os.path.exists(KILL[0]) else None
    KILL[0] = None                          # the KILL file stops the search only, never the floatsafe and fq step below
    groups = {}
    for p in os.listdir(rd + '/raw'):
        if p.endswith('.csv'):
            try:
                m = int(p.split('-')[0])
                rows = list(csv.DictReader(open(os.path.join(rd, 'raw', p))))
                _, fr, sc, e = FSAFE((m, rows))
                if fr is not None and (m not in groups or sc < groups[m][0]):
                    groups[m] = (sc, fr, p)
            except Exception as ex:  # a raw file left half written
                log('raw unreadable %s %s' % (p, ex))
    try:
        _, fr0, s0, _ = floatsafe.work((n, list(csv.DictReader(open(start))))) if os.path.exists(start) else (0, None, None, 0)
    except Exception:
        s0 = None
    res['start_score'] = s0
    res['raw'] = len(groups)
    finals = {}
    for m, (sc, fr, p) in sorted(groups.items()):
        ind = rd + '/certin/%d' % m; out = rd + '/quench/%d' % m; os.makedirs(ind, exist_ok=True); os.makedirs(out, exist_ok=True)
        writecsv('%s/%d.csv' % (ind, m), fr)
        open(ind + '/take.tsv', 'w').write('n\theld\tnew\tgain\tsource\tlicence\n')
        with open(rd + '/fq.log', 'a') as h:
            rc = bounded([PY, '-I', 'lane/midm_fqonce.py', ind, out, FQ, ind + '/take.tsv'], h, 240)
        best = (sc, fr, '%s/%d.csv' % (ind, m))
        for q in os.listdir(out):
            if q.endswith('.csv'):
                _, qr, s2, _ = FSAFE((m, list(csv.DictReader(open(os.path.join(out, q))))))
                if qr is not None and s2 < best[0]:
                    best = (s2, qr, os.path.join(out, q))
        os.makedirs(rd + '/final', exist_ok=True)
        writecsv('%s/final/%d.csv' % (rd, m), best[1])
        finals[str(m)] = dict(prequench=sc, new=best[0], fq_rc=rc, selected=best[2])
        if os.path.exists(os.path.join(D, 'ref', 'excl-ref.pkl')):
            # round 27: the share test runs here, so the controller on the loaded boxA only walks the sources
            try:
                os.environ['BACKLOG_EXCL_REF'] = os.path.join(D, 'ref', 'excl-ref.pkl')
                import backlog_gate27 as G
                finals[str(m)]['shares'] = [(l, a, b, d) for l, a, b, d in G.shares(m, best[1])]
            except Exception as ex:
                finals[str(m)]['shares_error'] = str(ex)
    res['finals'] = finals
    if killed:
        res['note'] = 'stopped by KILL: ' + open(killed).read()[:300]
    if n and str(n) in finals:
        res.update(prequench=finals[str(n)]['prequench'], new=finals[str(n)]['new'], quench_from_certified=True)
    return res


def main():
    sd = os.path.join(D, 'slot' + SLOT); os.makedirs(sd, exist_ok=True)
    log('slot START pid %d' % os.getpid())
    open(sd + '/pid', 'w').write(str(os.getpid()))   # round 34 (brief 6g): the ctl checks this pid every loop
    while time.time() < DEADLINE - 200 and not os.path.exists(sd + '/STOP'):
        nx = sd + '/next.json'
        if not os.path.exists(nx):
            time.sleep(5); continue
        try:
            j = json.load(open(nx))
        except ValueError:                    # a next.json still being written (round 26: boxC died on one)
            time.sleep(3); continue
        os.replace(nx, sd + '/current.json')
        log('START %s %s n=%d' % (j['rid'], j['id'], j['n']))
        try:
            res = run(j)
        except Exception as ex:
            res = {'id': j['id'], 'rid': j['rid'], 'n': j['n'], 'owner': j['owner'], 'error': str(ex)}
            traceback.print_exc()
        res['ended'] = stamp()
        rd = os.path.join(D, 'runs', j['rid']); os.makedirs(rd, exist_ok=True)
        open(rd + '/done.json.tmp', 'w').write(json.dumps(res)); os.replace(rd + '/done.json.tmp', rd + '/done.json')
        os.remove(sd + '/current.json')
        log('END %s %s' % (j['rid'], json.dumps({k: v for k, v in res.items() if k in ('raw', 'prequench', 'new', 'error', 'rc')})))
    log('slot STOP')


if __name__ == '__main__':
    main()
