#!/usr/bin/env python3
"""Run the modules growth, build, fresh-kick and certification queues for round 28.

Made from modules_round27.py by take-modules-r28/work/setup28.py. Round 28 keeps the Samanyu-dev rule lifted,
adds the ancestor share, seed share and WITHDRAW-line checks (modules_policy28.py), reads the bar from
round28-briefs/bar28.tsv and the live takes take-*-r28.

One local CPU slot cuts and tabulates new layouts, certifies box results and
builds while the box generates rows. The box has one generator/build slot and
one fresh-kick/quench slot. Historical files are read from copied snapshots.
"""
import csv
csv.field_size_limit(2**30)
import glob
import hashlib
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import time

ROOT = Path('$SCRATCH/bounties-squares')
LANE = Path('.')
TAKE = ROOT / 'take-modules-r28'
WORK = TAKE / 'work'
REMOTE = 'boxD:scratch/squares-modules/'
REMOTE2 = 'boxB:$SCRATCH/squares-modules/'
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
           VECLIB_MAXIMUM_THREADS='1', LANE=str(LANE))
PY = '$SCRATCH/bounties-squares/venv/bin/python'
DL = 1794721500  # 2026-11-15 05:45 UTC
NEAR_SLACK = 0.015


def near_candidate(n, side, bar):
    return side < bar[n] + NEAR_SLACK


CLOSED_CORNERS = {'803fa19.Ct', '803in20.Ct', '549mi19.Ct', 'zc7x7-78f9944br.Ct'}


def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def state(message):
    p = TAKE / 'STATE.txt' if MODE in ('local', 'collect') else Path('logs/STATE.txt')
    with p.open('a') as h:
        h.write(f'{stamp()} {MODE}: {message}; deadline 2026-11-15T05:45:00Z\n')


def run(args, log, timeout=900):
    if time.time() >= DL:
        return 124
    with open(log, 'a') as h:
        p = subprocess.Popen(list(map(str, args)), stdout=h, stderr=subprocess.STDOUT,
                             env=ENV, start_new_session=True)
        try:
            rc = p.wait(timeout=max(1, min(timeout, DL - time.time())))
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(p.pid, signal.SIGTERM)
            p.wait()
            rc = 124
        if rc:
            h.write(f'\n{stamp()} returncode {rc}\n')
            state(f'command failed with returncode {rc}, log {log}')
        return rc


def command(script, *args):
    return ['nice', '-n', '5', PY, '-I', script, *args]


def atomic(path, text):
    p = Path(path)
    p.with_suffix(p.suffix + '.tmp').write_text(text)
    os.replace(str(p) + '.tmp', p)


def rsync(src, dst):
    rc = subprocess.run(['rsync', '-az', str(src), str(dst)], capture_output=True)
    if rc.returncode:
        state(f'rsync failed {src} to {dst}: {rc.stderr.decode()[-300:]}')
    return rc.returncode == 0


def ssh(text):
    # -n preserves the input of the local build-row reader.
    return subprocess.run(['ssh', '-n', 'boxD', text], capture_output=True)


def scores(path):
    return {int(r['n']): float(r['L']) for r in csv.DictReader(open(path))}


def no_start_states():
    counts = {}
    good = set()
    states = {}
    for d in ('hist', 'raw', 'boxAraw', 'boxD-raw'):
        for p in list(Path(d).glob('*.json')) + list(Path(d).glob('*.nostart')):
            try:
                j = json.loads(p.read_text())
                c = (j.get('ids') or [q['id'] for q in j.get('modules', [])])[0]
            except (ValueError, IndexError, KeyError):
                continue
            if j.get('built') is not None:
                good.add(c)
            elif p.suffix == '.nostart':
                counts[c] = counts.get(c, 0) + 1
                if j.get('predicted'):
                    states.setdefault(c, []).append(j['predicted'] - math.isqrt(j['n'] - 1))
    blocked = CLOSED_CORNERS | {c for c, count in counts.items() if count >= 2 and c not in good}
    return blocked, states


def refresh_bar():
    rows = list(csv.DictReader(open('ship/details.csv')))
    best = {int(r['n']): float(r['score']) for r in rows}
    for d in sorted(glob.glob(str(ROOT / 'take-*-r24'))):
        p = Path(d) / 'take.tsv'
        if not p.exists():
            continue
        for r in csv.DictReader(p.open(), delimiter='\t'):
            if r.get('n', '').isdigit() and r.get('new'):
                n = int(r['n'])
                best[n] = min(best[n], float(r['new']))
    with open('bar.csv.tmp', 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=rows[0].keys())
        w.writeheader()
        for r in rows:
            n = int(r['n'])
            r.update(score=repr(best[n]), L=repr((1 + best[n]) * math.sqrt(n)))
            w.writerow(r)
    os.replace('bar.csv.tmp', 'bar.csv')
    rsync('bar.csv', REMOTE + 'bar.csv')


def rank(remote=False):
    qs = sorted(glob.glob('qz/*.tsv*') + ([] if remote else glob.glob('boxD-qz/*.tsv*')))
    stable = []
    Path('rankinputs').mkdir(exist_ok=True)
    for q in qs:
        if q.endswith('.tmp'):
            data = Path(q).read_bytes()
            # A generator flushes after each n. Exclude an unfinished final row.
            data = data[:data.rfind(b'\n') + 1]
            p = Path('rankinputs', hashlib.sha1(q.encode()).hexdigest() + '.tsv')
            p.write_bytes(data)
            stable.append(str(p))
        else:
            stable.append(q)
    env = ENV.get('MODULES_RESULTS')
    ENV['MODULES_RESULTS'] = str(Path('results').resolve()) + '/' if remote else str(LANE / 'results') + '/'
    rc = run(command('rank21.py' if remote else 'tools/rank21.py', 'bar.csv', 'G',
                     'glist.next', '0.001', *stable, '--per-n', '3', '--done', 'hist',
                     'raw', 'boxAraw' if remote else 'boxD-raw'), 'logs/rank.out', 60)
    if rc == 0:
        os.replace('glist.next', 'glist.txt')
        os.replace('glist.next.why', 'glist.txt.why')
    else:
        state(f'rank failed with returncode {rc}, previous glist preserved; log logs/rank.out')
    if env is None:
        ENV.pop('MODULES_RESULTS', None)
    else:
        ENV['MODULES_RESULTS'] = env


_build_source_cache = {}
_build_deferred = set()


def build_source_ids(remote):
    """Recheck old ranked choices against the current source policy."""
    import pickle
    from modules_policy24 import piece
    path = Path('g24' if remote else 'lib24') / 'library.pkl'
    key = (str(path.resolve()), path.stat().st_mtime_ns)
    if key not in _build_source_cache:
        lib = pickle.load(path.open('rb'))
        ids = {q['id'] for q in lib['mods'] if piece(q)['status'] == 'none'}
        _build_source_cache.clear()
        _build_source_cache[key] = ids
    return _build_source_cache[key]


def build(remote=False):
    if not remote and Path('LOCAL_TABLES_FIRST').exists():
        return False
    if time.time() >= DL - 60:
        return False
    if not Path('glist.txt').exists():
        return False
    allowed = build_source_ids(remote)
    for l in Path('glist.txt').read_text().splitlines():
        w = l.split()
        if len(w) != 9:
            continue
        how, name, n, c, f1, f2, s1, s2, f = w
        if 'f93h5' in c:
            continue  # Round 21 measured this family dry; reserve slots for fresh designs.
        if any(Path(d, name + ext).exists() for d in ('raw', 'boxAraw' if remote else 'boxD-raw')
               for ext in ('.json', '.nostart')):
            continue
        if not {c, f1, f2} <= allowed:
            if name not in _build_deferred:
                state(f'defer old ranked build {name}: source group is not recorded clean')
                _build_deferred.add(name)
            continue
        if remote:
            try:
                fd = os.open('claim/g-' + name, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
            except FileExistsError:
                continue
        elif ssh('cd $SCRATCH/squares-modules && set -C && : > ' + shlex.quote('claim/g-' + name)).returncode:
            continue
        log = 'blog/' + name + '.log'
        state(f'start build {name} {c} stacks {s1},{s2}, log {log}')
        run(command('modules.py' if remote else LANE / 'modules.py', 'job',
                    'g24' if remote else 'lib24', 'raw', 'details.csv' if remote else 'ship/details.csv',
                    name, n, c, f1, f2, s1, s2, f, '--fq', './fq' if remote else 'ship/fq',
                    '--squeeze', how), log, 600 if remote else 180)
        if not remote and Path('raw', name + '.csv').exists():
            for ext in ('.csv', '.json'):
                rsync('raw/' + name + ext, REMOTE + 'boxAraw/' + name + ext)
        state(f'finish build {name}, log {log}')
        return True
    return False


def box_table():
    jobs = sorted((p for p in Path('tabjobs').glob('*.ready') if not p.with_suffix('.done').exists()),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    want = os.environ.get('MODULES_TABLE_KIND')
    for job in jobs:
        if want:
            import pickle
            try:
                turn = bool(pickle.load(job.open('rb')).get('turn'))
            except Exception:
                continue
            if turn != (want == 'turn'):
                continue
        claimed = job.with_suffix('.running')
        try:
            job.rename(claimed)
        except FileNotFoundError:
            continue
        output = Path('tabulated', job.stem + '.pkl')
        state(f'start remote table {job.name}, log logs/table-{job.stem}.out')
        rc = run(command('modules_tablejob24.py', str(claimed), str(output)),
                 f'logs/table-{job.stem}.out', 120)
        claimed.rename(job.with_suffix('.done'))
        state(f'finish remote table {job.name}, returncode {rc}')
        return True
    return False


def box_build():
    batch_count = 0
    while time.time() < DL - 30 and not Path('STOP').exists():
        for lost in Path('tasks').glob('*.running'):
            lost.rename(lost.with_suffix('.ready'))
        tasks = sorted(Path('tasks').glob('*.ready'), reverse=True)
        if tasks:
            p = tasks[0]
            tag = p.stem
            task = json.loads(p.read_text())
            p.rename(p.with_suffix('.running'))
            if task.get('tabs') and not task.get('offset', 0):
                run(command('addtab.py', 'g24', *task['tabs']), f'logs/add-{tag}.out', 60)
            if not Path(task['lib'], 'library.pkl').exists():
                Path(task['lib']).mkdir(parents=True, exist_ok=True)
                for f in ('library.pkl', 'lens.pkl'):
                    shutil.copy2(Path('g24', f), Path(task['lib'], f))
            ns = Path(task['ns']).read_text().split()
            offset = task.get('offset', 0)
            batch = f'{tag}-{offset:04d}'
            batchns = Path('tasks', batch + '.ns')
            batchns.write_text('\n'.join(ns[offset:offset + 12]) + '\n')
            state(f'start generator {batch}, log logs/queue-{batch}.out')
            rc = run(command('modules_round28.py', 'queue', task['lib'], 'bar.csv', f'qz/q-{batch}.tsv',
                             '--top', '3', '--slack', '0.012', '--depth', '0.05',
                             '--need', task['need'], '--ns', str(batchns), '--checkpoint', f'tasks/{batch}.checkpoint.json'),
                     f'logs/queue-{batch}.out', 180)
            state(f'finish generator {batch}, returncode {rc}, log logs/queue-{batch}.out')
            cp = Path(f'tasks/{batch}.checkpoint.json')
            done = len(json.loads(cp.read_text())['done']) if cp.exists() else 0
            state(f'checkpoint {batch}: {done} completed targets of {len(ns[offset:offset+12])}')
            if rc == 124 and done == 0 and offset < len(ns):
                # Round 27: target 997 took more than 180 s and the batch repeated it seven times; skip such a target.
                state(f'skip target {ns[offset]} of {tag}: no target completed within the batch limit')
                done = 1
            if rc in (0, 124) and offset + done < len(ns):
                task['offset'] = offset + done
                p.with_suffix('.running').write_text(json.dumps(task))
                p.with_suffix('.running').rename(p)
            else:
                p.with_suffix('.running').rename(p.with_suffix('.done' if rc == 0 else '.failed'))
                shutil.rmtree(task['lib'])
            rank(True)
            batch_count += 1
            if batch_count % 2 or not box_table():
                build(True)
        elif not build(True):
            time.sleep(10)
            rank(True)
    state('finish box generator/build worker')


def box_kick():
    BASE = {int(r['n']): float(r['score']) for r in csv.DictReader(open('details.csv'))}
    while time.time() < DL - 30 and not Path('STOP').exists():
        certs = sorted(Path('qa').glob('*.ready'),
                       key=lambda p: json.loads(p.read_text())['precert_score'])
        if certs:
            p = certs[0]
            name = p.stem
            j = json.loads(p.read_text())
            shutil.copy2('qa/' + name + '.csv', 'qd/' + name + '.csv')
            shutil.copy2('qa/' + name + '.json', 'qd/' + name + '.json')
            state(f'start certified-file quench {name}, log logs/quench-{name}.out')
            one = Path('qa', name + '.work')
            one.mkdir(exist_ok=True)
            shutil.copy2('qa/' + name + '.csv', one / f"{j['n']}-1.csv")
            rc = run(command('zone_corner.py', 'quench', str(one), str(j['n'])),
                     f'logs/quench-{name}.out', 500)
            if rc == 0:
                shutil.copy2(one / f"{j['n']}-1.csv", 'qd/' + name + '.csv')
            if rc == 0:
                Path('qd/' + name + '.done').touch()
            p.rename(p.with_suffix('.done' if rc == 0 else '.failed'))
            state(f'finish certified-file quench {name}, returncode {rc}')
            continue
        if os.environ.get('MODULES_DRAIN_ONLY') == '1':
            time.sleep(5)
            continue
        bar = scores('bar.csv')
        choices = []
        for d in ('raw', 'boxAraw'):
            for p in Path(d).glob('*.json'):
                name = p.stem
                if Path('kicks', name + '.started').exists() or not p.with_suffix('.csv').exists():
                    continue
                j = json.loads(p.read_text())
                from modules_policy24 import ancestry
                if ancestry(j)['status'] != 'none':
                    Path('kicks', name + '.started').write_text('deferred source group')
                    continue
                # Round 28: the window starts from the higher of the live bar and the base bar (a lower live row of
                # another lane must not shut out builds near the base bar; the 805 siblings were shut out so).
                if j.get('built') is not None and j['built'] < max(bar[j['n']], (1 + BASE[j['n']]) * math.sqrt(j['n'])) + 2e-4:
                    # Rounds 25 and 26 measured: kicks of builds within 1e-5 of side of the base layout fall back
                    # into its basin (one row of 6.4e-9 in fourteen); the rows of size (805, 911) and the 748 build
                    # started 2.6e-5 to 1.0e-3 of side away. Such a build leaves the slot to the next build.
                    # Injected re-kicks carry a note and still run.
                    n = j['n']
                    if not j.get('note') and abs(j['built'] - (1 + BASE[n]) * math.sqrt(n)) < 1e-5:
                        Path('kicks', name + '.started').write_text('skipped: within 1e-5 of side of the base layout')
                        state(f'skip kick {name}: the build is within 1e-5 of side of the base layout')
                        continue
                    # The same for the live bar layout of another lane (two 932 builds sat 2e-7 of side from
                    # the forensics 932 row).
                    if not j.get('note') and abs(j['built'] - bar[n]) < 1e-5:
                        Path('kicks', name + '.started').write_text('skipped: within 1e-5 of side of the live bar layout')
                        state(f'skip kick {name}: the build is within 1e-5 of side of the live bar layout')
                        continue
                    choices.append((p.stat().st_mtime, name, p, j))
        if not choices:
            # Use the second box slot for a fresh build until a kick or quench arrives.
            if not build(True):
                if not box_table():
                    time.sleep(5)
            continue
        _, name, p, j = max(choices)
        from modules_geometry24 import key as geometry_key
        geometry = geometry_key(p.with_suffix('.csv'))
        marker = Path('kicks', f'geometry-{j["n"]}-{geometry}.json')
        Path('kicks', name + '.started').touch()
        if marker.exists():
            state(f'skip duplicate kick {name}, geometry {geometry}')
            continue
        marker.write_text(json.dumps(dict(source=str(p), n=j['n'], geometry=geometry)))
        out = 'kicks/' + name
        state(f'start fresh kick {name}, log logs/kick-{name}.out')
        engine = os.environ.get('MODULES_KICK_ENGINE', 'family')
        seconds = 420 if engine == 'family' else 450
        if engine == 'family':
            cmd = command('invent_rest.py', str(j['n']), str(p.with_suffix('.csv')), out,
                          '--fq', './fq', '--seconds', str(seconds), '--seed', '28', '--modes', 'lkick',
                          '--sigs', '0.003,0.006,0.01,0.02', '--deadline', 'deadline')
        else:
            cmd = command('midm_scan.py', '--n', str(j['n']), '--sub', str(p.with_suffix('.csv')),
                          '--out', out, '--fq', './fq', '--seconds', str(seconds), '--seed', '28',
                          '--modes', 'lkick,kick', '--kicks', '0.02', '--deadline', 'deadline')
        rc = run(cmd, f'logs/kick-{name}.out', 600)
        # Preserve the design's sources beside every kick result for certification.
        for q in Path(out, 'raw').glob('*.csv'):
            r = dict(j, kick_source=str(p), kick_seconds=seconds, kick_engine=engine,
                     kick_sigmas='0.003,0.006,0.01,0.02' if engine == 'family' else '0.02')
            q.with_suffix('.json').write_text(json.dumps(r))
            dst = Path('familyraw' if engine == 'family' else 'kickraw', f'{j["n"]}-{name}-{q.stem}.csv')
            dst.parent.mkdir(exist_ok=True)
            shutil.copy2(q, dst)
            shutil.copy2(q.with_suffix('.json'), dst.with_suffix('.json'))
        state(f'finish fresh kick {name}, returncode {rc}, finds {len(list(Path(out, "raw").glob("*.csv")))}')
    state('finish box kick/quench worker')


def collect():
    for src, dst in [('raw', 'boxD-raw'), ('blog', 'boxD-blog'), ('qz', 'boxD-qz'),
                     ('qd', 'boxD-qd'), ('kickraw', 'kickraw'), ('familyraw', 'familyraw'), ('tabulated', 'tabulated'), ('logs', 'boxlogs')]:
        Path(dst).mkdir(exist_ok=True)
        rsync(REMOTE + src + '/', dst + '/')
    Path('mm-logs').mkdir(exist_ok=True)
    rsync(REMOTE2 + 'tabulated/', 'tabulated/')
    rsync(REMOTE2 + 'logs/', 'mm-logs/')
    p = Path('boxlogs/STATE.txt')
    if p.exists():
        n = int(Path('state.offset').read_text()) if Path('state.offset').exists() else 0
        lines = p.read_text().splitlines(True)
        with (TAKE / 'STATE.txt').open('a') as h:
            h.writelines(lines[n:])
        Path('state.offset').write_text(str(len(lines)))
    rsync('raw/', REMOTE + 'boxAraw/')



def certificate_cache(original):
    import pickle
    import numpy
    import pandas
    import mpmath
    directory = Path('certificate-cache')
    directory.mkdir(exist_ok=True)
    version = sys.version + numpy.__version__ + pandas.__version__ + mpmath.__version__
    salt = hashlib.sha256(version.encode() + (LANE / 'floatsafe.py').read_bytes() +
                          (LANE / 'kaggle_metric.py').read_bytes()).digest()
    def cached(item):
        key = hashlib.sha256(salt + json.dumps(item, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        path = directory / (key + '.pkl')
        if path.exists():
            try:
                record = pickle.load(path.open('rb'))
                if record['key'] == key:
                    return record['result']
            except (OSError, EOFError, pickle.UnpicklingError, KeyError):
                pass
        result = original(item)
        with path.with_suffix('.tmp').open('wb') as h:
            pickle.dump(dict(key=key, result=result), h)
        os.replace(path.with_suffix('.tmp'), path)
        return result
    return cached


def bounding_score(path, n):
    lo = [math.inf, math.inf]
    hi = [-math.inf, -math.inf]
    for r in csv.DictReader(Path(path).open()):
        x, y, a = (float(str(r[k]).lstrip('s')) for k in ('x', 'y', 'angle'))
        e = .5 * (abs(math.cos(a)) + abs(math.sin(a)))
        for axis, value in enumerate((x, y)):
            lo[axis] = min(lo[axis], value - e)
            hi[axis] = max(hi[axis], value + e)
    score = max(hi[0] - lo[0], hi[1] - lo[1]) / math.sqrt(n) - 1
    return score


def publish_completed():
    sys.path.insert(0, str(LANE))
    import modules
    import floatsafe
    # Only completed box quenches may enter the public take.
    for p in Path('boxD-qd').glob('*.done'):
        cp = p.with_suffix('.csv')
        jp = p.with_suffix('.json')
        if cp.exists() and jp.exists():
            from modules_sources24 import normalize_record, clean_record
            record = normalize_record(json.loads(jp.read_text()))
            if not clean_record(record):
                continue
            jp.write_text(json.dumps(record))
            shutil.copy2(cp, Path('cand', cp.name))
            shutil.copy2(jp, Path('cand', jp.name))
    beat = [d for d in sorted(glob.glob(str(ROOT / 'take-*-r24'))) if d != str(TAKE)]
    bars = {int(r['n']): float(r['score']) for r in csv.DictReader(open('ship/details.csv'))}
    for d in beat:
        p = Path(d, 'take.tsv')
        if p.exists():
            for r in csv.DictReader(p.open(), delimiter='\t'):
                if r.get('n', '').isdigit() and r.get('new'):
                    n = int(r['n'])
                    bars[n] = min(bars[n], float(r['new']))
    Path('publish').mkdir(exist_ok=True)
    for p in Path('publish').iterdir():
        p.unlink()
    # The bounding side can discard an obsolete candidate, but acceptance still
    # requires the full certificate. Keep a wider margin than the final rule.
    for p in Path('cand').glob('*.csv'):
        n = int(p.name.split('-')[0])
        score = bounding_score(p, n)
        if score < bars[n] - 5e-11:
            shutil.copy2(p, Path('publish', p.name))
            shutil.copy2(p.with_suffix('.json'), Path('publish', p.with_suffix('.json').name))
    before = (TAKE / 'take.tsv').read_text() if (TAKE / 'take.tsv').exists() else ''
    original = floatsafe.work
    floatsafe.work = certificate_cache(original)
    try:
        with open('logs/take.out', 'w') as h:
            from contextlib import redirect_stdout
            with redirect_stdout(h):
                modules.cmd_take(['ship/details.csv', str(TAKE), 'publish', '--beat', *beat])
    finally:
        floatsafe.work = original
    # Keep the upstream register and the kick operation in each published source.
    sources = {}
    for line in Path('logs/take.out').read_text().splitlines():
        if line.startswith('keep '):
            parts = line.split()
            jp = Path(parts[-1]).with_suffix('.json')
            if jp.exists():
                sources[parts[1]] = json.loads(jp.read_text())
    rows = list(csv.DictReader((TAKE / 'take.tsv').open(), delimiter='\t'))
    for r in rows:
        j = sources.get(r['n'], {})
        if j.get('kick_source'):
            operation = ('invent_rest.py lkick, family squeeze and fq, 420 s' if j.get('kick_engine') == 'family'
                         else 'midm_scan lkick,kick sigma 0.02, 450 s')
            r['source'] = operation + ' on ' + j['kick_source'] + '; ' + r['source']
        r['source'] += '; held source register results/round23-best-2026-11-13.tsv; certified-file fq quench on boxD'
    with (TAKE / 'take.tsv.tmp').open('w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t')
        w.writeheader()
        w.writerows(rows)
    os.replace(TAKE / 'take.tsv.tmp', TAKE / 'take.tsv')
    after = (TAKE / 'take.tsv').read_text()
    if after != before:
        state('take.tsv replaced after certified-file box quench, log logs/take.out')
        for r in csv.DictReader(after.splitlines(), delimiter='\t'):
            if r['n'] + '\t' + r['held'] + '\t' + r['new'] + '\t' in before:
                continue
            with (ROOT / 'handoff-r28.log').open('a') as h:
                h.write(f'{stamp()} modules -> all: certified n={r["n"]}, score={r["new"]}, gain={r["gain"]} on round23; box quench complete, {TAKE}/{r["n"]}.csv\n')


def certify():
    sys.path.insert(0, str(LANE))
    import floatsafe
    import modules
    publish_completed()
    bar = scores('bar.csv')
    # Cache the raw certification: unchanged rows do not need another metric pass.
    cachepath = Path('certcache.json')
    cache = json.loads(cachepath.read_text()) if cachepath.exists() else {}
    for d in ('raw', 'boxD-raw', 'kickraw', 'familyraw'):
        for p in Path(d).glob('*.csv'):
            jp = p.with_suffix('.json')
            if not jp.exists():
                continue
            j = json.loads(jp.read_text())
            from modules_sources24 import clean_record, normalize_record
            j = normalize_record(j)
            from modules_policy24 import ancestry
            if ancestry(j)['status'] != 'none':
                continue
            if not clean_record(j):
                continue
            n = j['n']
            j['source'] = '; '.join(q['id'] + ' <' + q['source'] + '>' for q in j['modules']) + '; results/round26-best-2026-11-14.tsv; results/round25-best-2026-11-14.tsv'
            j['licence'] = '; '.join(sorted({q['licence'] for q in j['modules']}))
            if d not in ('kickraw', 'familyraw') and not near_candidate(n, j.get('built', 1e9), bar):
                continue
            key = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
            if key in cache:
                continue
            rows = list(csv.DictReader(p.open()))
            _, fr, score, error = floatsafe.work((n, rows))
            cache[key] = [n, score, error]
            if fr is None:
                atomic(cachepath, json.dumps(cache))
                continue
            side = (score + 1) * math.sqrt(n)
            # Make fresh near builds available before a kick or a later certification.
            if near_candidate(n, side, bar):
                np = TAKE / 'near' / f'{n}-{p.stem}-{key}.csv'
                if not np.exists():
                    shutil.copy2(p, np)
                    shutil.copy2(jp, np.with_suffix('.json'))
                    with (ROOT / 'handoff-r28.log').open('a') as h:
                        h.write(f'{stamp()} modules -> all: fresh build n={n}, side={side:.12f}, margin={side-bar[n]:+.3e}; new module design available, {np}\n')
            from modules_policy24 import ancestry
            j['samanyu_ancestry'] = ancestry(j)
            if j['samanyu_ancestry']['status'] != 'none':
                atomic(cachepath, json.dumps(cache))
                continue
            if score >= bar[n] / math.sqrt(n) - 1 - 1e-10:
                atomic(cachepath, json.dumps(cache))
                continue
            name = f'{n}-{key}'
            out = Path('precert', name + '.csv')
            with out.open('w', newline='') as h:
                w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle'])
                w.writeheader()
                w.writerows({k: r[k] for k in w.fieldnames} for r in fr)
            j.update(precert_source=str(p), precert_score=score, built=side)
            out.with_suffix('.json').write_text(json.dumps(j))
            atomic(cachepath, json.dumps(cache))
            state(f'stage certified-file quench {name}, source {p}, score {score}')
    atomic(cachepath, json.dumps(cache))
    pending_certs = []
    for out in Path('precert').glob('*.csv'):
        meta = out.with_suffix('.json')
        if meta.exists():
            record = json.loads(meta.read_text())
            pending_certs.append((record['precert_score'], record['n'], out))
    best_certs = {}
    for score, n, out in sorted(pending_certs):
        best_certs.setdefault(n, out)
    for out in best_certs.values():
        sent = out.with_suffix('.sent')
        meta = out.with_suffix('.json')
        if sent.exists() or not meta.exists():
            continue
        if Path('boxD-qd', out.stem + '.done').exists():
            sent.touch()
            continue
        rc = subprocess.run(['rsync', '-az', str(out), str(meta), REMOTE + 'qa/'], capture_output=True)
        if rc.returncode:
            continue
        name = out.stem
        result = ssh('cd $SCRATCH/squares-modules && (test -f ' + shlex.quote('qa/' + name + '.done') +
                     ' || test -f ' + shlex.quote('qa/' + name + '.ready') + ' || cp ' +
                     shlex.quote('qa/' + name + '.json') + ' ' + shlex.quote('qa/' + name + '.ready') + ')')
        if result.returncode == 0:
            sent.touch()
            state(f'queue certified-file quench {name}, input {out}')
    publish_completed()


def available_ids(work, ids):
    import pickle
    lens = pickle.load((Path(work) / 'lens.pkl').open('rb'))
    return [i for i in dict.fromkeys(ids) if i in lens and
            (lens[i].get('tab') is not None or lens[i].get('knots') is not None)]


def grow(k):
    import pickle
    if time.time() > DL - 300:
        return
    dirs = ([d for d in sorted(glob.glob(str(ROOT / 'take-*-r28'))) if d != str(TAKE)] + sorted(glob.glob(str(ROOT / 'take-*-r27')))
            + sorted(glob.glob(str(ROOT / 'take-*-r26'))))
    run(command(LANE / 'modules_near27.py', 'nears', *dirs), f'logs/near-{k}.out', 300)
    from modules_near27 import stage_take_cached
    staged = [stage_take_cached(Path(d), Path('clean-takes')) for d in dirs]
    specs = []
    # Round 27: at load 76-112 on boxA a cut over all 3,200 near dirs did not finish in 900 s. Pass only dirs
    # whose take.tsv changed since a cut that ended with returncode 0 (grow-seen27.json), newest first, 120 a step.
    # Dirs copied unchanged from round 26 (take.tsv older than the round 27 start) were cut in round 26.
    seenp = Path('grow-seen28.json')
    def gsig(d):
        t = Path(d) / 'take.tsv'
        return f'{t.stat().st_mtime_ns}:{t.stat().st_size}' if t.exists() else ''
    if seenp.exists():
        gseen = json.loads(seenp.read_text())
    else:
        gseen = {str(p): gsig(p) for p in list(Path('nears').iterdir()) + list(Path('clean-takes').iterdir())
                 if p.is_dir() and (p / 'take.tsv').exists() and (p / 'take.tsv').stat().st_mtime < 1794686640}
        atomic(seenp, json.dumps(gseen))
    cand = [str(p) for p in staged if p] + sorted((str(p) for p in Path('nears').iterdir() if p.is_dir()),
                                                   key=lambda d: -Path(d).stat().st_mtime)
    gbatch = [d for d in cand if gseen.get(d) != gsig(d)][:120]
    for d in gbatch:
        b = Path(d).name
        tag = ''.join(x for x in b.replace('take-', '').split('-r')[0] if x.isalnum())[:2] + b.rsplit('-r', 1)[-1]
        specs.append(tag + '=' + d)
    tag = f'j{k:04d}'
    log = f'logs/grow-{tag}.out'
    # Round 27: boxA ran at load 76-112 and the first growth step hit its 120 s limit, so the cut gets 900 s.
    if run(command(LANE / 'modules.py', 'grow', 'lib24', LANE / 'results', '--label', tag, *specs), log, 900) == 0:
        gseen.update({x: gsig(x) for x in gbatch})
        atomic(seenp, json.dumps(gseen))
        state(f'growth cut {len(gbatch)} changed dirs, log {log}')
    ids = Path('lib24', 'new-' + tag + '.txt')
    from modules_sources24 import filter_library
    filter_library(Path('lib24'))
    external = import_handoffs()
    from modules_tables24 import collect as collect_tables
    recovered = collect_tables(Path('lib24'), Path('tabulated'), Path('remote-tables-seen.json'))
    if recovered:
        pairs = pickle.load(open('external-tabs.pkl', 'rb')) if external else []
        Path('external-tabs.pkl').write_bytes(pickle.dumps(pairs + recovered))
        external.extend(q['id'] for q, t in recovered)
        state(f'import {len(recovered)} spare-slot tables')
    if external:
        with ids.open('a') as h:
            h.write(''.join(i + '\n' for i in external))
    import pickle
    byid = {q['id']: q for q in pickle.load(open('lib24/library.pkl', 'rb'))['mods']}
    pendingfile = Path('turn-pending.txt')
    pending = pendingfile.read_text().split() if pendingfile.exists() else []
    freshids = [i for i in ids.read_text().split() if i in byid] if ids.exists() else []
    # Recover available fresh tables whose dispatch was interrupted.
    dispatched = set()
    for old_need in Path('.').glob('need-j*.txt'):
        dispatched.update(old_need.read_text().split())
    current_lens = pickle.load(open('lib24/lens.pkl', 'rb'))
    # Round 28: the cuts of this round also read round 25 to 27 near dirs, whose modules carry those rounds' tags, so
    # a module listed in any lib24/new-jNNNN.txt of this round (j0207 on) counts as fresh until a need list holds it.
    round28_new = set()
    for q in Path('lib24').glob('new-j*.txt'):
        if q.stem[5:].isdigit() and int(q.stem[5:]) >= 207:
            round28_new.update(q.read_text().split())
    unhanded = [i for i, q in byid.items() if i not in dispatched and i in current_lens
                and ('28' in q.get('tag', '') or '-r28/' in q.get('src', '') or 'hd28' in i or 'grow28' in i
                     or i in round28_new)]
    freshids = list(dict.fromkeys(freshids + unhanded))
    pending = list(dict.fromkeys([i for i in freshids if byid[i]['kind'] == 'corner' and not byid[i].get('turn')] + pending))
    pending = [i for i in pending if i in byid and i + 't' not in byid]
    bar_now = scores('bar.csv')
    turn_scores = {}
    for qp in sorted(Path('boxD-qz').glob('*.tsv*')):
        try:
            for row in csv.DictReader(qp.open(), delimiter='\t'):
                c = row['corner']
                margin = float(row['predicted_side']) - bar_now[int(row['n'])]
                if -0.005 <= margin <= 0.012:
                    turn_scores[c] = min(turn_scores.get(c, 1e9), margin)
        except (KeyError, ValueError):
            continue
    fresh_set = set(freshids)
    pending.sort(key=lambda i: (i not in fresh_set, turn_scores.get(i, 1.0), i))
    selected = []
    pendingfile.write_text(''.join(i + '\n' for i in pending))
    if not freshids and not selected:
        return
    ids.write_text(''.join(i + '\n' for i in dict.fromkeys(freshids + selected)))
    state(f'start growth step {tag}, new modules {len(ids.read_text().split())}, log {log}')
    # tabsome imports modules from its working directory.
    pass  # round 25: tables of new cuts run on the boxes through tabjobs
    tab = Path('tab-' + tag + '.pkl')
    if tab.exists():
        run(command('ship/addtab.py', 'lib24', str(tab)), f'logs/tab-{tag}.out', 60)
    corners = Path('needc-' + tag + '.txt')
    corners.write_text(''.join(i + '\n' for i in selected))
    turn = Path('turn-' + tag + '.pkl')
    if False and corners.read_text().strip():
        run(command('tools/turnify.py', 'lib24', str(corners), str(turn)), f'logs/turn-{tag}.out', 60)
    if turn.exists():
        run(command('ship/addtab.py', 'lib24', str(turn)), f'logs/addturn-{tag}.out', 60)
        import pickle
        extra = [q['id'] for q, t in pickle.load(turn.open('rb'))]
    else:
        extra = []
    unfinished_turns = [i for i in selected if i + 't' not in extra]
    if unfinished_turns:
        with pendingfile.open('a') as h:
            h.write(''.join(i + '\n' for i in unfinished_turns))
    need = Path('need-' + tag + '.txt')
    from modules_policy24 import piece
    usable_ids = available_ids('lib24', ids.read_text().split() + extra)
    updated_byid = {q['id']:q for q in pickle.load(open('lib24/library.pkl','rb'))['mods']}
    need.write_text(''.join(i + '\n' for i in usable_ids if piece(updated_byid[i])['status']=='none'))
    from modules_tables24 import enqueue
    count = enqueue(Path('lib24'), Path('tabjobs'))
    rsync('tabjobs/', REMOTE + 'tabjobs/')
    rsync('tabjobs/', REMOTE2 + 'tabjobs/')
    state(f'spare-slot table backlog {count}')
    if not need.read_text().strip():
        state(f'growth {tag} has no valid new tables; generator skipped')
        return
    # Search all eligible n, with those nearest the fresh modules' f first.
    import pickle
    fresh = set(need.read_text().split())
    libdata = pickle.load(open('lib24/library.pkl', 'rb'))
    fs = [q['f0'] for q in libdata['mods'] if q['id'] in fresh]
    bar = scores('bar.csv')
    ns = [n for n in bar if n >= 300 and bar[n] < math.isqrt(n - 1) + 1 - 1e-9]
    ns.sort(key=lambda n: (min(abs(bar[n] - math.isqrt(n - 1) - f) for f in fs), n))
    nsp = Path('ns-' + tag + '.txt')
    nsp.write_text('\n'.join(map(str, ns)) + '\n')
    lib = 'libs/' + tag
    external_tab = Path('external-' + tag + '.pkl')
    if external:
        shutil.copy2('external-tabs.pkl', external_tab)
    tabs = [str(p) for p in (tab, turn, external_tab) if p.exists()]
    if (all(rsync(p, REMOTE + p) for p in tabs)
            and rsync(str(need), REMOTE + str(need)) and rsync(str(nsp), REMOTE + str(nsp))):
        # The box build slot merges these tables before making its fixed snapshot.
        task = Path('task-' + tag + '.json')
        task.write_text(json.dumps(dict(lib=lib, need=str(need), ns=str(nsp), tabs=tabs)))
        if rsync(task, REMOTE + 'tasks/' + tag + '.tmp'):
            ssh('cd $SCRATCH/squares-modules && mv tasks/' + tag + '.tmp tasks/' + tag + '.ready')
            state(f'queue generator {tag} on boxD, log logs/queue-{tag}.out')
        with (ROOT / 'handoff-r28.log').open('a') as h:
            h.write(f'{stamp()} modules -> all: new cut library and turned corners {tag}, {WORK}/lib24; ids {WORK}/{need}\n')


def handed_tables(path):
    """Read the two modules-library formats used by the corner lanes."""
    import pickle
    p = Path(path)
    if p.is_dir() and (p / 'library.pkl').exists() and (p / 'lens.pkl').exists():
        lib = pickle.load((p / 'library.pkl').open('rb'))
        lens = pickle.load((p / 'lens.pkl').open('rb'))
        return [(q, lens[q['id']]) for q in lib['mods'] if q['id'] in lens]
    if p.is_dir() and (p / 'corners.pkl').exists():
        return handed_tables(p / 'corners.pkl')
    if p.is_file() and p.suffix == '.pkl':
        value = pickle.load(p.open('rb'))
        if isinstance(value, dict) and value.get('kind') in ('corner', 'far'):
            return [(value, None)]
        if isinstance(value, list) and all(isinstance(q, dict) and q.get('kind') in ('corner', 'far') for q in value):
            return [(q, None) for q in value]
        if isinstance(value, list) and value and all(isinstance(q, dict) and {'P', 'c1', 'c2', 'f', 'y0', 'x0', 'src', 'licence'} <= q.keys() for q in value):
            import zone_corner as zc
            return [(zc.as_module(q['P'], zc.cmod(q['c1'], q['c2'], q.get('lean1', 1), q.get('lean2', 1)),
                                  q['f'], q['y0'], q['x0'], q['id'] + '.C', 'direct design corner', q), None)
                    for q in value]
        if isinstance(value, list) and all(isinstance(x, tuple) and len(x) == 2 for x in value):
            return value
    return []


def import_handoffs():
    import pickle
    import re
    hp = ROOT / 'handoff-r28.log'
    if not hp.exists():
        return []
    p = Path('external-seen.json')
    seen = json.loads(p.read_text()) if p.exists() else {}
    lib = pickle.load(open('lib24/library.pkl', 'rb'))
    lens = pickle.load(open('lib24/lens.pkl', 'rb'))
    have = {q['id'] for q in lib['mods']}
    added = []
    for line in hp.read_text().splitlines():
        if ' modules -> ' in line:
            continue
        for s in re.findall(r'$SCRATCH/[^\s,;<>]+', line):
            source = Path(s.rstrip('.:)'))
            if '-r28/' not in str(source):
                continue
            if source.name in ('library.pkl', 'lens.pkl'):
                source = source.parent
            target = source / 'lens.pkl' if source.is_dir() else source
            if source.is_dir() and not target.exists():
                target = source / 'corners.pkl'
            if not target.exists() or (not source.is_dir() and source.suffix != '.pkl'):
                continue
            fingerprint = f'{target.stat().st_mtime_ns}:{target.stat().st_size}'
            if seen.get(str(source)) == fingerprint:
                continue
            try:
                pairs = handed_tables(source)
            except (KeyError, TypeError, ValueError, EOFError, pickle.UnpicklingError, OSError, IndexError):
                continue
            if not pairs:
                continue
            seen[str(source)] = fingerprint
            new = []
            for q, t in pairs:
                if not isinstance(q, dict) or q.get('kind') not in ('corner', 'far') or q.get('id') in have:
                    continue
                valid = t is None or (t.get('tab') is not None if q['kind'] == 'corner' else t.get('knots') is not None)
                if not valid:
                    continue
                from modules_sources24 import clean_module
                if not clean_module(q):
                    continue
                q = dict(q, ours=True)
                lib['mods'].append(q)
                if t is not None:
                    lens[q['id']] = t
                have.add(q['id'])
                new.append(q['id'])
            if new:
                added.extend(new)
                state(f'import standalone handoff {source}, {len(new)} modules')
    if added:
        for name, value in [('library', lib), ('lens', lens)]:
            with open('lib24/' + name + '.pkl.tmp', 'wb') as h:
                pickle.dump(value, h)
            os.replace('lib24/' + name + '.pkl.tmp', 'lib24/' + name + '.pkl')
        # Imported tables also travel through the next incremental box update.
        Path('external-tabs.pkl').write_bytes(pickle.dumps([(q, lens[q['id']]) for q in lib['mods'] if q['id'] in set(added) and q['id'] in lens]))
    atomic(p, json.dumps(seen))
    return added


def local():
    os.chdir(WORK)
    Path('tmp').mkdir(exist_ok=True)
    ENV.update(TMPDIR=str(WORK / 'tmp'), SQ_TMP=str(WORK / 'tmp'))
    os.environ.update(TMPDIR=str(WORK / 'tmp'), SQ_TMP=str(WORK / 'tmp'))
    sys.path.insert(0, str(LANE))
    existing = [int(p.stem.split('-j')[-1]) for p in Path('.').glob('need-j*.txt')]
    k = max(existing, default=0) + 1
    state('start local growth/certification/build loop')
    while time.time() < DL - 30 and not Path('STOP').exists():
        collect()
        refresh_bar()
        certify()
        # Read each handoff on the next growth pass, even if its layout is refused.
        hp = ROOT / 'handoff-r28.log'
        if hp.exists():
            Path('logs/handoff-last.txt').write_text(hp.read_text())
        grow(k)
        rank()
        rsync('glist.txt', REMOTE + 'glist.txt')
        build()
        k += 1
        time.sleep(20)
    collect()
    refresh_bar()
    certify()
    state('finish local loop')


def fast_collect():
    """Collect between table solves, while the table helper waits in the local slot."""
    os.chdir(WORK)
    for src, dst in [('raw', 'boxD-raw'), ('qd', 'boxD-qd'), ('kickraw', 'kickraw'), ('familyraw', 'familyraw')]:
        Path(dst).mkdir(exist_ok=True)
        rsync(REMOTE + src + '/', dst + '/')
    Path('livekicks').mkdir(exist_ok=True)
    subprocess.run(['rsync', '-az', '--exclude=tmp/', '--include=*/', '--include=*.csv', '--include=*.tsv',
                    '--exclude=*', REMOTE + 'kicks/', 'livekicks/'], capture_output=True, timeout=25)
    for d in Path('livekicks').iterdir():
        if not d.is_dir():
            continue
        meta = next((p for p in (Path('raw', d.name + '.json'), Path('boxD-raw', d.name + '.json')) if p.exists()), None)
        if meta is None:
            continue
        j = json.loads(meta.read_text())
        family = bool(list(d.glob('slide-*.tsv')))
        dest = Path('familyraw' if family else 'kickraw')
        for p in (d / 'raw').glob('*.csv'):
            # A still-running tool may be writing a file. Only expose complete rows.
            try:
                rows = list(csv.DictReader(p.open()))
                if len(rows) != j['n']:
                    continue
                for r in rows:
                    for key in ('x', 'y', 'angle'):
                        float(r[key])
            except (ValueError, TypeError, KeyError):
                continue
            out = dest / f'{j["n"]}-{d.name}-{p.stem}.csv'
            if out.exists() and out.read_bytes() == p.read_bytes():
                continue
            shutil.copy2(p, str(out) + '.tmp')
            os.replace(str(out) + '.tmp', out)
            record = dict(j, kick_source=str(meta.with_suffix('.csv')), kick_engine='family' if family else 'midm',
                          kick_seconds=420 if family else 450)
            out.with_suffix('.json').write_text(json.dumps(record))
    refresh_bar()
    certify()
    print(stamp(), 'fast collection complete', flush=True)


from modules_policy28 import bind as bind_policy
refresh_bar, publish_completed = bind_policy(globals())


if __name__ == '__main__':
    MODE = sys.argv[1]
    if MODE == 'queue':
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import modules
        blocked, states = no_start_states()
        usable = modules.usable
        from modules_policy24 import piece
        modules.usable = lambda q: q['id'] not in blocked and usable(q) and piece(q)['status'] == 'none'
        best = modules.Library.best
        def filtered_best(self, *args, **kwargs):
            kwargs['accept'] = lambda c, f: not any(abs(f - bad) < 3e-3 for bad in states.get(c['id'], ()))
            return best(self, *args, **kwargs)
        modules.Library.best = filtered_best
        from modules_queue24 import queue
        sys.exit(queue(sys.argv[2:]) or 0)
    elif MODE == 'collect':
        # A helper launches this collector in its own group. Bound that whole
        # group even if the helper reaches its deadline while waiting for it.
        import signal
        if os.getpid() == os.getpgrp():
            signal.signal(signal.SIGALRM, lambda *_: os.killpg(os.getpgrp(), signal.SIGTERM))
            signal.alarm(max(1, min(50, int(DL - time.time()))))
        fast_collect()
    elif MODE == 'local':
        local()
    else:
        os.chdir(os.environ.get('MODULES_BOX_DIR', str(Path.home() / 'scratch/squares-modules')))
        PY = str(Path.cwd() / 'venv/bin/python')
        binary_link = Path('ext/evand/search/packer/target/release/fq')
        binary_link.parent.mkdir(parents=True, exist_ok=True)
        if not binary_link.exists():
            binary_link.symlink_to(Path('fq').resolve())
        ENV.update(LANE='.', SQ_BOX=str(Path.cwd()), SQ_TMP=str(Path.cwd() / 'tmp'),
                   TMPDIR=str(Path.cwd() / 'tmp'), ZC_FQ_TIMEOUT='180')
        def box_tables():
            while time.time() < DL - 30 and not Path('STOP').exists():
                if not box_table():
                    time.sleep(10)
            state('finish box table worker')
        {'build': box_build, 'kick': box_kick, 'tables': box_tables}[MODE]()
