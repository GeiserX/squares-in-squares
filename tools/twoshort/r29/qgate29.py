"""Second ancestry gate for the take: the quench lane's full-tree walker must also find each row clean.

Round 26: our own walk passed 932, 415 and 501, while quench_walk.py (which follows the
assembler's held-row resolution and refuses gone records) found the Samanyu-dev seed 503
behind a held 813 reference in 932 and a gone kmmmvs merge_report.json in 415 and 501.
A row that fails either walker leaves the take for near/, with the walker's hits recorded.
Results are cached by file hash for 20 minutes, because live ancestors can change.
"""
from pathlib import Path
import csv, json, fcntl, time, sys, subprocess, hashlib, os
csv.field_size_limit(16000000)
W = Path(__file__).parent; T = W.parent; B = T.parent
PY = str(B / 'venv/bin/python'); QW = str(W / 'qwalk29.py')  # round 27: quench_walk.py without the Samanyu-dev checks
cache_path = W / 'qgate-cache.json'
queue_path = W / 'qwalk-queue.txt'
cache = {}


def _load():
    try:
        return json.load(open(cache_path))
    except (ValueError, OSError):
        return {}


def lookup(p):
    """Cached result for this file version, or None. Clean results live 20 minutes, refusals 60."""
    c = _load().get(str(p))
    if not c or c['sha256'] != hashlib.sha256(Path(p).read_bytes()).hexdigest():
        return None
    ttl = 1200 if c['result'].get('clean') else 3600
    return c['result'] if time.time() - c['time'] < ttl else None


def _save(p, key, res):
    with open(W / 'locks/qgate-cache.lock', 'a') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        d = _load(); d[str(p)] = dict(sha256=key, time=time.time(), result=res)
        t = cache_path.with_name('qgate-cache.' + str(os.getpid()) + '.tmp'); t.write_text(json.dumps(d)); t.replace(cache_path)


def check(p):
    if '--fresh' not in sys.argv:
        res = lookup(p)
        if res is not None:
            return res
    key = hashlib.sha256(Path(p).read_bytes()).hexdigest()
    out = subprocess.run([PY, '-I', QW, str(p)], capture_output=True, text=True, timeout=1500)
    try:
        res = json.loads(out.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'clean': False, 'hits': ['quench_walk gave no result: ' + out.stderr[-300:]]}
    _save(p, key, res)
    return res


def enqueue(p):
    with open(queue_path, 'a') as f:
        f.write(str(p) + '\n')


def main():
    lock = open(W / 'locks/certify.lock', 'a'); fcntl.flock(lock, fcntl.LOCK_EX)
    rows = list(csv.DictReader(open(T / 'take.tsv'), delimiter='\t')); keep = []; dropped = []
    for r in rows:
        p = T / (r['n'] + '.csv')
        res = check(p) if p.exists() else {'clean': False, 'hits': ['missing take file']}
        if res.get('clean'):
            keep.append(r); continue
        q = T / 'near' / (r['n'] + '-qwalk-refused.csv')
        if p.exists():
            q.write_bytes(p.read_bytes()); p.unlink()
        q.with_suffix('.json').write_text(json.dumps(dict(source=r['source'], licence=r['licence'], certified=True, counted=False,
                                                          score=float(r['new']), refused_by='quench_walk.py', hits=res.get('hits', [])[:20]), indent=1))
        dropped.append((r['n'], res.get('hits', [])[:2]))
    if dropped:
        with open(T / 'take.tsv.tmp', 'w', newline='') as f:
            cw = csv.DictWriter(f, fieldnames=['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t'); cw.writeheader(); cw.writerows(keep)
        (T / 'take.tsv.tmp').replace(T / 'take.tsv')
        stamp = time.strftime('%FT%TZ', time.gmtime())
        with open(B / 'handoff-r29.log', 'a') as f:
            for n, hits in dropped:
                f.write(stamp + ' twoshort -> all: DROP n=' + n + ' from take, quench_walk.py finds its ancestry not clean: ' + ' | '.join(h[:160] for h in hits) + ', ' + str(T / 'near' / (n + '-qwalk-refused.json')) + '\n')
        with open(T / 'STATE.txt', 'a') as f:
            for n, hits in dropped:
                f.write(stamp + ' boxA DROP n=' + n + ' by the second gate (quench_walk.py): ' + ' | '.join(h[:200] for h in hits) + '\n')
    print('qgate kept', [r['n'] for r in keep], 'dropped', [n for n, _ in dropped], flush=True)


if __name__ == '__main__':
    main()
    sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
