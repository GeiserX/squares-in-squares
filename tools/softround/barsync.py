#!/usr/bin/env python3
"""barsync.py [once]: round 30. Write the all-lane bar of every n (held round 28 b, bar30 rows of r29 takes, every live
r30 take.tsv) to W/box/bars.txt and copy it to each box scratch, checking the md5 there (round 29 trap: scp -q left a
stale tool on a box). kickleg.py and qorder.py read it. Loops every 300 s until the search deadline."""
import hashlib, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctl, follow


def once():
    b = follow.bars()
    p = ctl.W + '/box/bars.txt'
    open(p + '.tmp', 'w').write(''.join('%d %.17g\n' % (n, b[n]) for n in sorted(b))); os.rename(p + '.tmp', p)
    md5 = hashlib.md5(open(p, 'rb').read()).hexdigest()
    for box, host in ctl.REMOTE.items():
        subprocess.run('cat %s | ssh -o ConnectTimeout=10 %s "cat > %s/bars.tmp && mv %s/bars.tmp %s/bars.txt"' % (p, host, ctl.RDIR, ctl.RDIR, ctl.RDIR), shell=True)
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', host, 'md5 -q %s/bars.txt' % ctl.RDIR], capture_output=True, text=True)
        if r.stdout.strip() != md5:
            print('BARSYNC md5 mismatch on', box, r.stdout.strip(), md5, flush=True)
    print('BARSYNC %s %d n' % (time.strftime('%H:%M:%SZ', time.gmtime()), len(b)), flush=True)


if __name__ == '__main__':
    once()
    if 'once' not in sys.argv:
        dl = float(open(ctl.W + '/deadline').read())
        while time.time() < dl:
            time.sleep(300)
            try:
                once()
            except Exception as ex:
                print('BARSYNC error', ex, flush=True)
