#!/usr/bin/env python3
"""Add the packings published outside Kaggle to a harvest dir, in the layout harvest_merge.py reads.

  python3 -I harvest_register.py CLONES_DIR NEW_HARVEST

Sources, fetched with git as data (nothing in a clone is run, and git runs no hook of a fresh clone):
- the Squares Project register, https://github.com/jlevy/squares: every packet under
  packing/resources/web/<packet>/ (a copy of someone's published packing, with its own licence file) and the
  register's own witnesses under packing/witnesses/;
- every repo of the GitHub account kenaznia-doga (Doga Ozden's upper-bound repos), which reach the register a
  few hours after he publishes them.
CLONES_DIR keeps the shallow clones between runs; a later run fetches only what moved. When GitHub refuses the
account's repo list (rate limit), the run reads the clones of that account already in CLONES_DIR and says so.

Each packet becomes NEW_HARVEST/gh/<packet>/ with one csv per packing (n, square_id, x, y, angle in radians)
and a meta.json: ref (repo, commit, path), license, upstream (the first github.com link of the packet's README).
The licence is read per packet from its own LICENSE file: third-party packets of the register are not under
the register's licence. No licence file gives "no licence file", which the take step's allow-list refuses.
Formats read: Witness/v2 YAML (centre and angle in degrees or radians, four corners, or centre and basis vector; decimal or rational),
and through literature_take.py's readers .cert (Evan Daniel's rational format), .sqpk and Casson .txt layouts; a .csv with submission columns is copied as it
is. A .cert states its side: the count of certs whose bounding box does not give that side is printed, as a
check on the reader. harvest_merge.py scores every candidate with the official metric, so a misread file
cannot win; it can only be missed.
"""
import json, math, os, pathlib, re, subprocess, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                    # -I drops the script dir
import literature_take as T  # noqa: E402
import mpmath  # noqa: E402  (literature_take sets 40 digits)
from fractions import Fraction  # noqa: E402
from literature_scan import side_cert  # noqa: E402

REGISTER = 'jlevy/squares'
ACCOUNT = 'kenaznia-doga'
REGISTER_LICENCE = 'CC BY 4.0 (jlevy/squares LICENSE: data and records; credit Joshua Levy, the squares project)'


def git(*a, cwd=None):
    return subprocess.run(('git', '-c', 'core.hooksPath=/dev/null') + a, cwd=cwd, check=True, capture_output=True,
                          text=True, timeout=1800).stdout.strip()


def sync(clones, ref):
    """Shallow clone of github.com/<ref> under clones, moved to the remote head. Returns (dir, commit, moved)."""
    d = clones / ref.replace('/', '__')
    old = None
    if (d / '.git').exists():
        old = git('rev-parse', 'HEAD', cwd=d)
        git('fetch', '-q', '--depth', '1', 'origin', 'HEAD', cwd=d)
        if git('rev-parse', 'FETCH_HEAD', cwd=d) != old:
            git('checkout', '-q', '--detach', 'FETCH_HEAD', cwd=d)
    else:
        git('clone', '-q', '--depth', '1', f'https://github.com/{ref}', str(d))
    new = git('rev-parse', 'HEAD', cwd=d)
    return d, new, new != old


def account_repos(user):
    req = urllib.request.Request(f'https://api.github.com/users/{user}/repos?per_page=100&sort=pushed',
                                 headers={'User-Agent': 'squares-harvest'})   # public list, no token
    with urllib.request.urlopen(req, timeout=60) as r:
        return [x['full_name'] for x in json.load(r) if not x.get('fork')]


def licence(dirs):
    """The licence of a packet, from the first LICENSE/COPYING file in dirs. CC BY 4.0 is looked for first:
    Ozden's file gives CC BY 4.0 for the packing and MIT for his checker, and the packing is what we take."""
    for d in dirs:
        for f in sorted(d.glob('*')):
            if f.is_file() and f.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYING')) and 'evand' not in f.name:
                t = ' '.join(f.read_text(errors='replace').split())
                for words, name in ((('Attribution-ShareAlike', 'BY-SA'), 'CC BY-SA'),
                                    (('Attribution-NonCommercial', 'BY-NC'), 'CC BY-NC'),
                                    (('Attribution 4.0', 'CC BY 4.0', 'CC-BY-4.0'), 'CC BY 4.0'),
                                    (('CC0', 'Public Domain Dedication'), 'CC0'),
                                    (('Apache License',), 'Apache 2.0'),
                                    (('MIT License', 'Permission is hereby granted, free of charge'), 'MIT')):
                    if any(w in t for w in words):
                        return f'{name} ({f.name} of the packet)'
                return f'unrecognised licence file {f.name}'
    return 'no licence file'


def side(sq):
    xs, ys = [], []
    for x, y, a in sq:
        x, y, a = float(x), float(y), float(a)
        e = 0.5 * (abs(math.cos(a)) + abs(math.sin(a)))
        xs += [x - e, x + e]; ys += [y - e, y + e]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def num(t):
    """A decimal or p/q text as an mpf."""
    f = Fraction(str(t))
    return mpmath.mpf(f.numerator) / mpmath.mpf(f.denominator)


def scalar_reader(spec):
    """Evaluate rational scalars, field coefficients or narrow enclosures.

    Field coordinates list coefficients from the constant term upwards. The
    minimal polynomial lists its leading coefficient first. Interval midpoints
    supply numerical starts only. The metric and floatsafe still certify them.
    """
    kind = spec.get('kind', 'rational')
    if kind in ('rational', 'decimal'):
        return num
    if kind == 'interval-enclosure':
        def enclosure(v):
            if not isinstance(v, list):
                return num(v)
            if len(v) != 2:
                raise ValueError('enclosure must have two bounds')
            lo, hi = map(num, v)
            if not (lo <= hi and hi - lo <= mpmath.mpf('1e-12')):
                raise ValueError('coordinate enclosure is reversed or too wide')
            return (lo + hi) / 2
        return enclosure
    if kind != 'algebraic-number-field':
        raise ValueError('scalar kind ' + str(kind))
    precision = min(1000, max(80, 2 * max(len(str(v)) for v in spec['isolating_interval']) + 30))
    with mpmath.workdps(precision):
        coefficients = [num(v) for v in spec['minimal_polynomial']]
        lo, hi = map(num, spec['isolating_interval'])
        def polynomial(x):
            value = mpmath.mpf(0)
            for coefficient in coefficients:
                value = value * x + coefficient
            return value
        pl, ph = polynomial(lo), polynomial(hi)
        if lo >= hi or pl * ph > 0:
            raise ValueError('field root is not bracketed')
        if pl == 0:
            root = lo
        elif ph == 0:
            root = hi
        else:
            for _ in range(300):
                mid = (lo + hi) / 2
                pm = polynomial(mid)
                if mid == lo or mid == hi or pm == 0:
                    lo = hi = mid
                    break
                if pl * pm < 0:
                    hi = mid
                else:
                    lo, pl = mid, pm
            root = (lo + hi) / 2
    def field(v):
        if not isinstance(v, list):
            return num(v)
        value = mpmath.mpf(0)
        for coefficient in reversed(v):
            value = value * root + num(coefficient)
        return value
    return field


def read_witness(path):
    """A Witness/v2 file of the register: centre and angle (degrees or radians), or four corners per square
    (decimal or rational), or centre and basis vector. Corners give the centre as their mean and the angle of
    the first edge."""
    import yaml
    data = yaml.safe_load(pathlib.Path(path).read_text())
    if not isinstance(data, dict) or 'witness' not in data:
        return None
    w = data['witness']
    value = scalar_reader(w.get('scalar', {}))
    text = lambda v: mpmath.nstr(value(v), 40)
    if str(w['square_size']) != '1':
        raise ValueError('square_size is not 1')
    out = []
    if w['representation'] == 'center-angle':
        unit = w['coordinates']['angle_unit']
        if unit not in ('degrees', 'radians'):
            raise ValueError('angle unit ' + str(unit))
        for s in w['squares']:
            a = text(s['angle'])
            out.append((text(s['center'][0]), text(s['center'][1]), T.rad(a) if unit == 'degrees' else a))
    elif w['representation'] == 'corners':
        for s in w['squares']:
            c = [(value(x), value(y)) for x, y in s['corners']]
            if len(c) != 4:
                raise ValueError('a square without four corners')
            out.append((mpmath.nstr(sum(x for x, _ in c) / 4, 30), mpmath.nstr(sum(y for _, y in c) / 4, 30),
                        mpmath.nstr(mpmath.atan2(c[1][1] - c[0][1], c[1][0] - c[0][0]), 30)))
    elif w['representation'] == 'center-basis':     # basis = (cos, sin) of the square's first edge
        for s in w['squares']:
            bx, by = map(value, s['basis'])
            if abs(bx * bx + by * by - 1) > mpmath.mpf('1e-12'):
                raise ValueError('basis does not describe a unit square')
            out.append((text(s['center'][0]), text(s['center'][1]),
                        mpmath.nstr(mpmath.atan2(by, bx), 40)))
    else:
        raise ValueError('representation ' + str(w['representation']))
    return int(w['n']), out


def read(path):
    """(n, squares) or None; squares are (x, y, angle in radians) texts."""
    name = path.name.lower()
    if name.endswith(('.yaml', '.yml')):
        if path.stat().st_size > 8e6 or 'Witness/v' not in path.read_text(errors='replace')[:400]:
            return None
        return read_witness(str(path))
    if name.endswith('.cert'):
        return T.read_cert(str(path))
    if name.endswith('.sqpk'):
        return T.read_sqpk(str(path))
    if name.endswith('.txt') and path.stat().st_size < 5e6 and 'Square 1:' in path.read_text(errors='replace')[:400]:
        return T.read_txt(str(path))
    return None


def packet(src, out, ref, lic, stats):
    """Convert every packing under src into out/; write meta.json when at least one was read."""
    wrote = 0
    for p in sorted(src.rglob('*')):
        if not p.is_file() or '.git' in p.parts:
            continue
        rel = '__'.join(p.relative_to(src).parts)
        try:
            if p.suffix.lower() == '.csv':
                head = p.open(errors='replace').readline().lower()
                if all(c in head for c in ('x', 'y', 'angle')) and ('n' in [h.strip() for h in head.split(',')]):
                    out.mkdir(parents=True, exist_ok=True)
                    (out / rel).write_bytes(p.read_bytes()); wrote += 1; stats['csv'] += 1
                continue
            got = read(p)
        except Exception as e:
            stats['unread'] += 1
            print('unread', p, type(e).__name__, str(e)[:60], flush=True)
            continue
        if not got:
            continue
        n, sq = got
        if not (1 <= n <= 1000) or len(sq) != n:
            continue
        if p.suffix == '.cert':
            st = side_cert(str(p))
            ok = st is not None and abs(side(sq) - st[1]) < 1e-9
            stats['cert side agrees' if ok else 'cert side differs'] += 1
        out.mkdir(parents=True, exist_ok=True)
        with open(out / (rel + '.csv'), 'w') as h:
            h.write('n,square_id,x,y,angle\n')
            for i, (x, y, a) in enumerate(sq):
                h.write(f'{n},{i},{x},{y},{a}\n')
        wrote += 1; stats['packings'] += 1
    if wrote:
        up = ''
        for rd in (src / 'README.md',):
            if rd.exists():
                m = re.search(r'https://github\.com/[\w.-]+/[\w.-]+', rd.read_text(errors='replace'))
                up = m.group(0) if m else ''
        (out / 'meta.json').write_text(json.dumps({'ref': ref, 'kind': 'register', 'license': lic, 'upstream': up,
                                                   'files': wrote}, indent=1))
    return wrote


def main():
    clones, new = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    clones.mkdir(parents=True, exist_ok=True)
    gh = new / 'gh'
    stats = dict.fromkeys(('packings', 'csv', 'unread', 'cert side agrees', 'cert side differs'), 0)
    reg, commit, moved = sync(clones, REGISTER)
    print('register', REGISTER, commit, 'moved' if moved else 'unchanged since the last run', flush=True)
    web = reg / 'packing' / 'resources' / 'web'
    lics = {}
    for d in sorted(p for p in web.iterdir() if p.is_dir()):
        lic = licence([d / 'source', d])
        k = packet(d, gh / f'jlevy__squares__{d.name}', f'github.com/{REGISTER}@{commit[:8]} packing/resources/web/{d.name}',
                   lic, stats)
        if k:
            lics[lic] = lics.get(lic, 0) + 1
    packet(reg / 'packing' / 'witnesses', gh / 'jlevy__squares__witnesses',
           f'github.com/{REGISTER}@{commit[:8]} packing/witnesses', REGISTER_LICENCE, stats)
    try:
        repos = account_repos(ACCOUNT)
    except Exception as e:
        # GitHub allows 60 unsigned list calls an hour per address, and other runs share ours. The clones we
        # hold still fetch with git, which has no such limit; only a repo he created since the last list is missed.
        repos = sorted(p.name.replace('__', '/', 1) for p in clones.glob(ACCOUNT + '__*') if (p / '.git').exists())
        print('account list fail', ACCOUNT, e, '- reading the', len(repos), 'clones already held; a new repo is not seen',
              flush=True)
    for ref in repos:
        try:
            d, c, moved = sync(clones, ref)
        except Exception as e:
            print('clone fail', ref, str(e)[:80], flush=True); continue
        lic = licence([d])
        k = packet(d, gh / ref.replace('/', '__'), f'github.com/{ref}@{c[:8]}', lic, stats)
        print('repo', ref, c[:8], 'moved' if moved else 'unchanged', k, 'packings', lic, flush=True)
        if k:
            lics[lic] = lics.get(lic, 0) + 1
    print('packets by licence:', json.dumps(lics, sort_keys=True))
    print('files:', json.dumps(stats))


if __name__ == '__main__':
    main()
