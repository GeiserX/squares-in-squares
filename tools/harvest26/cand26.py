"""Round 26 harvest candidate: certify a start, run one local fq quench, stage the better file for the collector.

  python -I cand26.py N SRCFILE SOURCE LICENCE [--limit 180] [--flags fast|default] [--no-fq]

SRCFILE is a csv in the submission layout (n, x, y, angle; many n or one n). It is data: read only.
The certified start is written once under work/starts/<n>-<sha16>.csv (immutable). The fq output, when
certified and smaller, replaces it as the candidate. The candidate goes to work/cand/<n>.csv and
work/cand/take.tsv (n, held, new, gain, source, licence, start, polish_gain), replaced by rename, keeping
the lower row per n. tools/harvest_collect.py then runs the remote proof and publishes the take.
"""
import argparse, csv, hashlib, json, os, subprocess, sys, time
from pathlib import Path
L = Path('.')
sys.path.insert(0, str(L)); sys.path.insert(0, str(L / 'tools'))
import floatsafe  # noqa: E402
from engine_lib import normalize  # noqa: E402
from engine_fq import FQ, write_txt, read_txt  # noqa: E402
from engine_polish import to_rows  # noqa: E402
from harvest_collect import rows_write, table  # noqa: E402

S = Path('$SCRATCH/bounties-squares')
W = S / 'take-harvest-r26/work'
csv.field_size_limit(1 << 26)
COLS = ('n', 'held', 'new', 'gain', 'source', 'licence', 'start', 'polish_gain')
FAST = ['--no-alm', '--loosen', '1.0', '--pit', '80', '--flip-top', '8']


def rows_of(path, n):
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            k = {str(a).strip().lower(): v for a, v in r.items()}
            m = str(k.get('n') or '').lstrip('s')
            if not m and k.get('id') and '_' in str(k['id']):
                m = str(k['id']).split('_')[0]
            if m.isdigit() and int(m) == n:
                out.append({'n': str(n), 'square_id': str(len(out)), 'x': str(k['x']).lstrip('s'),
                            'y': str(k['y']).lstrip('s'), 'angle': str(k.get('angle', k.get('deg'))).lstrip('s')})
    return out


def state(msg):
    with open(W.parent / 'STATE.txt', 'a') as f:
        f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' boxA ' + msg + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int)
    ap.add_argument('src')
    ap.add_argument('source')
    ap.add_argument('licence')
    ap.add_argument('--limit', type=int, default=180)
    ap.add_argument('--flags', default='fast')
    ap.add_argument('--no-fq', action='store_true')
    ap.add_argument('--only-gain', action='store_true', help='stage only when fq beats the start by 1e-12 (follow-up of a proved file)')
    a = ap.parse_args()
    n = a.n
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(S / 'gate/cand-round25-1114b/details.csv'))}
    rows = rows_of(a.src, n)
    if len(rows) != n:
        print('rows', len(rows), 'for n', n); return 2
    _, fr, s0, e = floatsafe.work((n, rows))
    if fr is None:
        print('start does not certify'); return 3
    (W / 'starts').mkdir(exist_ok=True)
    tmp = W / 'starts' / f'{n}.tmp.csv'
    rows_write(tmp, fr)
    key = hashlib.sha256(tmp.read_bytes()).hexdigest()[:16]
    start = W / 'starts' / f'{n}-{key}.csv'
    if not start.exists():
        os.replace(tmp, start)
    else:
        tmp.unlink()
    Path(str(start) + '.json').write_text(json.dumps(dict(n=n, src=a.src, source=a.source, licence=a.licence,
                                                          score=s0, eps=e), indent=1) + '\n')
    print('start', n, s0, 'bar', held[n], 'gap', s0 - held[n], start, flush=True)
    best, best_path, how = s0, start, 'certified start'
    if not a.no_fq:
        run = W / 'runs' / f'{n}-{key}'
        run.parent.mkdir(exist_ok=True)
        side, arr = normalize([(float(r['x']), float(r['y']), float(r['angle'])) for r in fr])
        write_txt(run.with_suffix('.txt'), side, arr)
        flags = FAST if a.flags == 'fast' else []
        cmd = ['nice', '-n', '5', FQ, 'quench', '--in', str(run.with_suffix('.txt')), '--out', str(run.with_suffix('.out'))] + flags
        t0 = time.time()
        with run.with_suffix('.log').open('w') as log:
            p = subprocess.Popen(cmd, stdout=log, stderr=log, start_new_session=True)
            state(f'START fq pid={p.pid} n={n} limit={a.limit}s flags={a.flags} start={start} log={run}.log deadline 17:15Z')
            try:
                rc = p.wait(timeout=a.limit)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, 9); rc = p.wait()
        s1 = None
        if rc == 0 and run.with_suffix('.out').exists():
            _, arr2 = read_txt(run.with_suffix('.out'))
            cand = run.with_suffix('.csv')
            _, fr2, s1, e2 = floatsafe.work((n, to_rows(n, arr2)))
            if fr2 is not None:
                rows_write(cand, fr2)
                if s1 < best:
                    best, best_path, how = s1, cand, 'fq quench (' + ' '.join(flags or ['default']) + ') of the certified start'
        state(f'FINISH fq n={n} exit={rc} start={s0!r} fq={s1!r} gain_on_start={(s0 - s1) if s1 is not None else None} seconds={time.time() - t0:.0f}')
        print('fq', n, rc, s1, 'gain on start', (s0 - s1) if s1 is not None else None, flush=True)
    if a.only_gain and not best < s0 - 1e-12:
        print('no gain on start', s0, best); return 0
    cdir = W / 'cand'
    cdir.mkdir(exist_ok=True)
    old = {int(r['n']): r for r in table(cdir / 'take.tsv')} if (cdir / 'take.tsv').exists() else {}
    if n in old and float(old[n]['new']) <= best:
        print('kept older candidate', old[n]['new']); return 0
    if not best < held[n] - 1e-10:
        print('not below bar', best, held[n]); return 0
    with open(best_path) as f:
        rows_write(cdir / f'{n}.csv', list(csv.DictReader(f)))
    old[n] = dict(n=n, held=repr(held[n]), new=repr(best), gain=repr(held[n] - best),
                  source=f'{how}; start {start.name} from {a.source}', licence=a.licence,
                  start=repr(s0), polish_gain=repr(s0 - best))
    tmp = cdir / 'take.tsv.tmp'
    with tmp.open('w') as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter='\t')
        w.writeheader()
        w.writerows(old[k] for k in sorted(old))
    os.replace(tmp, cdir / 'take.tsv')
    print('candidate', n, best, 'gain', held[n] - best, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
