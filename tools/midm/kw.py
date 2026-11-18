#!/usr/bin/env python3
"""kw.py: the one kick worker of the midm lane, rounds 19 and 20 (on the box that runs the scans).

It takes one unclaimed line at a time from legs.q and then from the queue files q<K>-c<class>.q (class 1 first),
runs midm_scan.py with --stop6 and --bank bank.txt, and after a find of 3e-8 of score or more appends one leg from
the find to legs.q (seed + 100; a leg of a leg once more, never a third). Between two scans it runs the fq quench
that the collect asks for (fqin/GO -> fqout/DONE), so the lane stays at one process here.
A line is: scan N SUB SECONDS SEED MODES REF. The out dir is run/s<K>, K read from SUB (r<K>/.. or run/s<K>/..).
Round 20: env KW_KICKS (a comma list) goes to midm_scan.py --kicks; KW_ORDER sets the order of the classes.
Round 21: a leg follows every find of 1e-6 of score or more, with no cap on the chain (round 20 item 1: on 554 the
third to fifth legs, queued by hand, gave 3.5e-5, and on 809 the third leg found 3.7e-5 in 97 s). A find of 3e-8 or
more still gets the first two legs. Legs under n = 640 go to legs.q and the others to legsB.q. KW_ORDER may name
them: S is legs.q, B is legsB.q (default S,B,<classes>, the order of round 20).
"""
import glob, math, os, re, subprocess, sys, time
D = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.expanduser('$SCRATCH/squares-base'); PY = BASE + '/venv/bin/python'; FQ = BASE + '/fq'


def log(s):
    open('logs/kw.log', 'a').write(time.strftime('%H:%M:%S ', time.gmtime()) + s + '\n')


def leg_queue(n, seed, finds, gain):
    """The leg file a find goes to, or None (round 21: no cap while a leg finds 1e-6 or more)."""
    if not finds or not (gain >= 1e-6 or (gain >= 3e-8 and seed < 200)):
        return None
    return 'legs.q' if n < 640 else 'legsB.q'


def queues():
    order = os.environ.get('KW_ORDER', '2,3,1,4' if os.environ.get('KW_NOFQ') else '1,3,2,4').split(',')      # the classes of snap19.py, in the order this worker takes them
    if 'S' not in order:
        order = ['S', 'B'] + order
    qs = []
    for c in order:
        if c == 'S':
            qs.append('legs.q')
        elif c == 'B':
            qs.append('legsB.q')
        else:
            qs += sorted(glob.glob('q*-c%d.q' % int(c)), key=lambda p: int(re.search(r'q(\d+)-', p).group(1)), reverse=True)
    return qs


def nextline():
    qs = queues()
    for q in qs:
        if not os.path.exists(q):
            continue
        for l in open(q):
            f = l.split()
            if len(f) < 7:
                continue
            try:
                os.mkdir('claims/%s-%s' % (f[1], f[4]))
            except FileExistsError:
                continue
            return q, f
    return None, None


def main():
  os.chdir(D); os.makedirs('claims', exist_ok=True); os.makedirs('logs', exist_ok=True)
  while True:
      left = float(open('deadline').read()) - time.time()
      if os.path.exists('STOP') or left < 45:
          break
      if os.path.exists('fqin/GO') and not os.environ.get('KW_NOFQ'):
          subprocess.run('rm -rf fqout; nice -n 5 %s midm_fqonce.py fqin fqout %s x > logs/fqonce.out 2>&1; rm -f fqin/GO; touch fqout/DONE' % (PY, FQ), shell=True)
          log('fq quench of fqin done'); continue
      q, f = nextline()
      if f is None:
          time.sleep(15); continue
      kind, n, sub, secs, seed, modes, ref = f[:7]; n = int(n); seed = int(seed); secs = float(secs)
      K = int(re.match(r'(?:run/s|r)(\d+)/', sub).group(1)); out = 'run/s%d' % K; os.makedirs(out, exist_ok=True)
      if left < secs + 30:
          secs = left - 30
      log('%s scan %d %s secs %.0f seed %d' % (q, n, sub, secs, seed))
      cmd = [PY, 'midm_scan.py', '--n', str(n), '--sub', sub, '--out', out, '--fq', FQ, '--seconds', '%.0f' % secs, '--seed', str(seed),
             '--modes', modes, '--ref', ref, '--deadline', 'deadline']
      if os.environ.get('KW_KICKS'):
          cmd += ['--kicks', os.environ['KW_KICKS']]
      if not os.path.exists('NOSTOP6'):
          cmd += ['--stop6', '--bank', 'bank.txt']
      subprocess.run(cmd, stdout=open(out + '/worker.log', 'a'), stderr=subprocess.STDOUT)
      t = '%s/scan-%d-%d.tsv' % (out, n, seed); end = None
      if os.path.exists(t):
          for l in open(t):
              if l.startswith('# END'):
                  end = l
      if end:
          m = re.search(r'finds (\d+) best ([0-9.]+) held ([0-9.]+)', end)
          finds = int(m.group(1)); gain = (float(m.group(3)) - float(m.group(2))) / math.sqrt(n)
          log('END %d seed %d finds %d gain %.3e' % (n, seed, finds, gain))
          lq = leg_queue(n, seed, finds, gain)
          if lq:
              raws = [p for p in glob.glob('%s/raw/%d-*-%d-%d.csv' % (out, n, seed, finds))]
              if raws:
                  open(lq, 'a').write('scan %d %s %.0f %d kick,lkick 0\n' % (n, raws[0], float(f[3]), seed + 100))
                  log('leg queued for %d from %s' % (n, raws[0]))
  log('worker ends')


if __name__ == '__main__':
    main()
