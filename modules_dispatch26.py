"""Round 26: give the boxB kick slot the fresh boxD builds that the boxD kick slot has not reached.

Every 90 s, when the boxB queue (r26q) is empty: read the boxD builds in raw/ that have no kicks/<name>.started,
keep those of fresh geometry (more than 1e-5 of side from the base layout) and below the live bar plus 1e-5
of score, claim the best one on boxD by writing kicks/<name>.started (the boxD worker
then skips it), and queue it on boxB as <name>-mmk with an inject record, so mmcollect.py brings the finds back
with their sources. Light work only: ssh, rsync and small reads. Deadline: 500 s before 17:15Z, as the kick loop.
Usage: dispatch26.py [--once]"""
import csv, json, math, os, subprocess, sys, time
from pathlib import Path
W = Path('$SCRATCH/bounties-squares/take-modules-r26/work')
DL = 1794676500
os.chdir(W)
BASE = {int(r['n']): float(r['score']) for r in csv.DictReader(open('ship/details.csv'))}
MM = '$SCRATCH/squares-modules/'
LIST = r'''cd $SCRATCH/squares-modules && for j in raw/*.json; do b=$(basename $j .json); [ -e kicks/$b.started ] || [ ! -e raw/$b.csv ] || echo $b; done'''


def stamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def state(msg):
    with open('../STATE.txt', 'a') as h:
        h.write(f'{stamp()} dispatch: {msg}; deadline 2026-11-14T17:15:00Z\n')


def once():
    q = subprocess.run(['ssh', 'boxB', f'ls {MM}r26q/ | grep -c csv$'], capture_output=True, text=True, timeout=60)
    if q.returncode not in (0, 1) or q.stdout.strip() not in ('0', ''):
        return 'queue busy'
    r = subprocess.run(['ssh', 'boxD', LIST], capture_output=True, text=True, timeout=60)
    bar = {int(x['n']): float(x['score']) for x in csv.DictReader(open('bar.csv'))}
    best = []
    for name in r.stdout.split():
        p = Path('boxD-raw', name + '.json')
        if not p.exists() or not Path('boxD-raw', name + '.csv').exists():
            continue  # not yet collected here; the next pass sees it
        j = json.loads(p.read_text())
        if j.get('built') is None or j.get('note'):
            continue
        n = int(j['n'])
        s = j['built'] / math.sqrt(n) - 1
        # Fresh geometry only: rounds 25 and 26 measured no row from starts within 1e-5 of side of the base
        # layout (they fall back into its basin); the rows came from starts 2.6e-5 to 1.0e-3 of side away.
        # The same holds for the live bar layout of another lane: two 932 builds on a forensics corner sat 2e-7 of
        # side from forensics' 932 row, so a kick would only return to that row.
        L = (1 + bar[n]) * math.sqrt(n)
        if abs(j['built'] - (1 + BASE[n]) * math.sqrt(n)) < 1e-5 or abs(j['built'] - L) < 1e-5 or s > bar[n] + 1e-5:
            continue
        best.append((s - bar[n], name, n, j))
    if not best:
        return 'no fresh build'
    margin, name, n, j = min(best)
    c = subprocess.run(['ssh', 'boxD', f'cd $SCRATCH/squares-modules && set -C && echo "dispatched to boxB by take-modules-r26/work/tools/dispatch26.py" > kicks/{name}.started'],
                       capture_output=True, text=True, timeout=60)
    if c.returncode:
        return f'claim of {name} failed (boxD started it)'
    tag = name + '-mmk'
    j = dict(j, note=f'round 26 boxB kick of the fresh build take-modules-r26/work/boxD-raw/{name}.csv, dispatched by tools/dispatch26.py while the boxD kick slot was busy')
    Path('inject', tag + '.json').write_text(json.dumps(j))
    Path('inject', tag + '.csv').write_bytes(Path('boxD-raw', name + '.csv').read_bytes())
    s = subprocess.run(['scp', '-q', f'inject/{tag}.csv', f'boxB:{MM}r26q/{tag}.csv'], capture_output=True, timeout=120)
    if s.returncode:
        subprocess.run(['ssh', 'boxD', f'rm -f $SCRATCH/squares-modules/kicks/{name}.started'], timeout=60)
        return f'copy of {tag} failed, claim released'
    state(f'queue {tag} on boxB (n={n}, built score {margin:+.3e} against the live bar, fresh geometry); boxD marked {name} started')
    return 'queued ' + tag


if __name__ == '__main__':
    if '--once' in sys.argv:
        print(once())
        sys.exit(0)
    while time.time() < DL - 500 and not Path('STOP-dispatch').exists():
        try:
            print(stamp(), once(), flush=True)
        except Exception as e:  # keep the loop alive through a dropped ssh
            print(stamp(), 'error', repr(e), flush=True)
        time.sleep(90)
    print(stamp(), 'dispatch ends', flush=True)
