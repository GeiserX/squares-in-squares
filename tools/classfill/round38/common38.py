"""Classfill round 38: shared helpers for the controller, the boot and the finisher."""
import csv, json, hashlib, math, os, re, subprocess, time
from pathlib import Path
csv.field_size_limit(100000000)
S = Path('$SCRATCH/bounties-squares')
T = S / 'take-classfill-r38'
W = T / 'work'
R = Path('.')
ROOT = 'scratch/squares-classfill-r38'
HOSTS = [('boxE', 'A'), ('boxE', 'B'), ('boxC', 'F'), ('boxC', 'G'), ('boxC', 'H'), ('boxB', 'M'), ('boxB', 'N')]  # r38 budget (override 8): boxE 2, boxC 3, boxB 2; none on boxA
PY = {'boxE': '$SCRATCH/squares-base/venv/bin/python', 'boxD': '$SCRATCH/squares-readers/venv/bin/python', 'boxC': '$SCRATCH/squares-readers/venv/bin/python',
      'boxB': '$SCRATCH/squares-base/venv/bin/python'}
LOCALBASE = '$DATA'  # host 'local' = boxA: ROOT resolves under $DATA
END = float((W / 'stage/deadline').read_text())  # 13:45Z
HANDOFF = S / 'handoff-r38.log'
COL = ['n', 'held', 'new', 'gain', 'source', 'licence']


def now():
    return time.strftime('%FT%TZ', time.gmtime())


def note(x):
    with (T / 'STATE.txt').open('a') as f:
        f.write(now() + ' ' + x + '\n')


def hand(to, x):
    with HANDOFF.open('a') as f:
        f.write(now() + ' classfill -> ' + to + ': ' + x + '\n')


def read(p, d=None):
    try:
        return json.loads(Path(p).read_text())
    except (ValueError, OSError, TypeError):
        return d


def atom(p, j):
    p = Path(p)
    p.parent.mkdir(exist_ok=True, parents=True)
    q = p.with_name(p.name + '.tmp')
    q.write_text(json.dumps(j, indent=1) + '\n')
    q.replace(p)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cmd(a, timeout=60):
    if a[0] == 'ssh' and a[1] == 'local':
        import tempfile  # a file, not a pipe: a backgrounded '&&' list keeps a subshell on the pipe
        with tempfile.TemporaryFile('w+') as f:
            subprocess.run(['bash', '-c', a[2]], cwd=LOCALBASE, check=True, stdout=f, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, timeout=timeout)
            f.seek(0)
            return f.read()
    a = [LOCALBASE + '/' + x[6:] if x.startswith('local:') else x for x in a]
    if a[0] == 'ssh':
        a = a[:1] + ['-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2'] + a[1:]
    if a[0] == 'scp':
        a = a[:1] + ['-O', '-o', 'ConnectTimeout=10'] + a[1:]
    return subprocess.run(a, check=True, capture_output=True, text=True, timeout=timeout).stdout


def rows(p):
    try:
        return list(csv.DictReader(open(p), delimiter='\t'))
    except OSError:
        return []


def bars():
    """base = bar38; live = min over bar38 and every other live r37 take; src = (dir, value) of the lowest take."""
    base = {int(r['n']): float(r['bar']) for r in rows(S / 'round38-briefs/bar38.tsv')}
    live = dict(base)
    src = {}
    for p in S.glob('take-*-r38/take.tsv'):
        if p.parent == T or 'assemble' in p.parent.name:
            continue
        for r in rows(p):
            try:
                n = int(r['n'])
                v = float(r['new'])
            except (ValueError, KeyError, TypeError):
                continue
            if n in live and v < live[n]:
                live[n] = v
                src[n] = (p.parent, v)
    return base, live, src


def own():
    return {int(r['n']): r for r in rows(T / 'take.tsv')}


def table(take):
    with (T / 'take.tsv.tmp').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COL, delimiter='\t')
        w.writeheader()
        w.writerows(take[n] for n in sorted(take))
    os.replace(T / 'take.tsv.tmp', T / 'take.tsv')


def writebar():
    base, live, _ = bars()
    mine = {n: float(r['new']) for n, r in own().items()}
    p = W / 'stage/bar.csv'
    with p.open('w') as f:
        w = csv.writer(f)
        w.writerow(['n', 'L', 'score', 'min_gap'])
        for n, v in live.items():
            v = min(v, mine.get(n, v))
            w.writerow([n, repr((1 + v) * math.sqrt(n)), repr(v), 2.2e-11])
    for host in dict(HOSTS):
        cmd(['scp', '-q', str(p), host + ':' + ROOT + '/bar.csv.new'])  # local: a plain cp through the shim
        cmd(['ssh', host, 'mv ' + ROOT + '/bar.csv.new ' + ROOT + '/bar.csv'])
    return base, live


CLAIM = re.compile(r'claim|reserv', re.I)


def claim_lines(n, since):
    """Handoff lines of OTHER lanes after `since` that claim work on n."""
    out = []
    rx = re.compile(r'(?<![\d.])n\s*=\s*%d(?!\d)|\bn%d\b|\bof %d\b|/%d\.csv|/%d-' % (n, n, n, n, n))
    for l in HANDOFF.read_text(errors='replace').splitlines():
        if ' classfill -> ' in l or not CLAIM.search(l) or not rx.search(l):
            continue
        try:
            t = __import__('datetime').datetime.fromisoformat(l.split()[0].replace('Z', '+00:00')).timestamp()
        except ValueError:
            continue
        if t >= since:
            out.append((t, l))
    return out


def withdrawn_hit(digest):
    for l in HANDOFF.read_text(errors='replace').splitlines():
        if 'WITHDRAW' in l.upper() and (digest[:12] in l or digest[:16] in l):
            return l
    return None
