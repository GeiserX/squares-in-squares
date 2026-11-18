"""rule19.py RUNDIR [OUT.tsv]: what the stop rule and the sigma 0.04 bank did in the kick scans of round 19.

Reads every RUNDIR/s<K>/scan-<n>-<seed>.tsv (K from 30 up) of midm_scan.py --stop6 --bank. One row per scan goes to
OUT.tsv: n, seed, kind (first scan or leg), seconds, tries, the tries of the first 6 that came back, stopped,
seconds saved, finds and gain of the standard tries, seconds, tries, finds and gain of the bank tries (sigma 0.04).
MIDM_OWED names the legs owed from round 17 as n-seed (default 875-30): such a scan counts as a leg.
MIDM_RUNGLOB names the run dirs to read (default s[3-4][0-9]; round 20: s[5-9][0-9] with MIDM_OWED empty).
OUT-kinds.tsv gets the tries, seconds, finds and gain by kind of try (the full kick by sigma, and the local kick).
Prints the sums and the same lines priced at the old schedule (every scan runs to its budget).
A scan in RUNDIR/s<K+20> is the scan of s<K> with the same n and seed run again on the old schedule (no --stop6, no
--bank). Those are left out of the tables above; OUT-ab.tsv and the last lines pair each with the stopped scan.
"""
import glob, math, os, re, sys

OWED = {tuple(int(v) for v in x.split('-')) for x in os.environ.get('MIDM_OWED', '875-30').split(',') if x}     # (n, seed) of a leg owed from round 17: it runs in a first-scan slot
run = sys.argv[1]; rows = []; kinds = {}      # kinds: 'kick sig0.04', ..., 'lkick' -> [tries, seconds, finds, gain]
for p in sorted(glob.glob(run + '/' + os.environ.get('MIDM_RUNGLOB', 's[3-4][0-9]') + '/scan-*.tsv')):
    n, seed = (int(x) for x in re.match(r'scan-(\d+)-(\d+)\.tsv', os.path.basename(p)).groups())
    held = None; best = None; cur = None
    for l in open(p):
        if l.startswith('# n='):
            held = float(re.search(r'held=([0-9.]+)', l).group(1)); best = held
            cur = dict(n=n, seed=seed, held=held, sec=[0.0, 0.0], tries=[0, 0], finds=[0, 0], gain=[0.0, 0.0], back=0, stopped=0, saved=0.0, ph=0, end=0, wall=0.0)
        elif cur is None:
            continue
        elif l.startswith('# FIND'):
            s = float(re.search(r'side ([0-9.]+)', l).group(1)); m = re.search(r'mode (\w+) flags \w+ what (\S+)', l)
            kd = kinds.setdefault('kick ' + m.group(2) if m.group(1) == 'kick' else m.group(1), [0, 0.0, 0, 0.0])
            kd[2] += 1; kd[3] += (best - s) / math.sqrt(n)
            cur['finds'][cur['ph']] += 1; cur['gain'][cur['ph']] += (best - s) / math.sqrt(n); best = s
        elif l.startswith('# BANK04'):
            cur['ph'] = 1
        elif l.startswith('# STOP6'):
            cur['stopped'] = 1; cur['saved'] = float(re.search(r': (\d+) s saved', l).group(1))
        elif l.startswith('# END'):
            cur['end'] = 1; cur['wall'] = float(re.search(r'seconds (\d+)', l).group(1)); rows.append(cur); cur = None
        elif l[:1].isdigit():
            v = l.rstrip('\n').split('\t'); k = int(v[0]); cur['tries'][cur['ph']] += 1; cur['sec'][cur['ph']] += float(v[5])
            kd = kinds.setdefault('kick ' + v[3] if v[1] == 'kick' else v[1], [0, 0.0, 0, 0.0]); kd[0] += 1; kd[1] += float(v[5])
            if k <= 6 and v[4] != 'nan' and abs(float(v[4]) - cur['held']) <= 5e-9:
                cur['back'] += 1
    if cur is not None:
        rows.append(cur)        # a scan cut by the deadline or still running
head = 'n\tseed\tkind\tseconds\ttries\tback_of_6\tstopped\tsaved_s\tstd_seconds\tstd_tries\tstd_finds\tstd_gain\tbank_seconds\tbank_tries\tbank_finds\tbank_gain'
out = [head]
for r in rows:
    out.append('%d\t%d\t%s\t%.0f\t%d\t%d\t%d\t%.0f\t%.0f\t%d\t%d\t%.3e\t%.0f\t%d\t%d\t%.3e' % (
        r['n'], r['seed'], 'leg' if r['seed'] >= 100 or (r['n'], r['seed']) in OWED else 'first', r['wall'], sum(r['tries']), r['back'], r['stopped'], r['saved'],
        r['sec'][0], r['tries'][0], r['finds'][0], r['gain'][0], r['sec'][1], r['tries'][1], r['finds'][1], r['gain'][1]))
if len(sys.argv) > 2:
    open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
    open(sys.argv[2][:-4] + '-kinds.tsv', 'w').write('kind\ttries\tseconds\tfinds\tgain\n' + ''.join(
        '%s\t%d\t%.0f\t%d\t%.3e\n' % (k, v[0], v[1], v[2], v[3]) for k, v in sorted(kinds.items())))
for k, v in sorted(kinds.items()):
    print('%-14s tries %4d seconds %6.0f finds %2d gain %.3e per 1,000 s %.3e' % (k, v[0], v[1], v[2], v[3], 1000 * v[3] / max(v[1], 1)))
S = lambda f: sum(f(r) for r in rows)
st = [r for r in rows if r['stopped']]; op = [r for r in rows if not r['stopped']]
six = [r for r in rows if sum(r['tries']) >= 6 or r['stopped']]
print('scans %d (first %d, legs %d); with 6 tries or more %d; stopped by the rule %d' % (len(rows), sum(not (r['seed'] >= 100 or (r['n'], r['seed']) in OWED) for r in rows), sum(r['seed'] >= 100 or (r['n'], r['seed']) in OWED for r in rows), len(six), len(st)))
print('seconds: all %.0f; standard tries %.0f; bank tries (sigma 0.04) %.0f; saved by the stops %.0f' % (S(lambda r: r['wall']), S(lambda r: r['sec'][0]), S(lambda r: r['sec'][1]), S(lambda r: r['saved'])))
for name, i in (('standard', 0), ('bank 0.04', 1)):
    sec = S(lambda r: r['sec'][i]); g = S(lambda r: r['gain'][i]); f = S(lambda r: r['finds'][i])
    print('%s: tries %d, finds %d, gain %.3e, per 1,000 s: %.2f finds, %.3e of score' % (name, S(lambda r: r['tries'][i]), f, g, 1000 * f / max(sec, 1), 1000 * g / max(sec, 1)))
sec_open = sum(r['sec'][0] for r in op); g_open = sum(r['gain'][0] for r in op)
print('open scans, standard tries: %.0f s, gain %.3e, %.3e per 1,000 s; the old schedule would have spent the %.0f saved seconds on the %d stopped scans' % (
    sec_open, g_open, 1000 * g_open / max(sec_open, 1), S(lambda r: r['saved']), len(st)))
old = S(lambda r: r['wall'] + r['saved'] - r['sec'][1])
print('old schedule (no stop, no bank) for the same lines: %.0f s; this run: %.0f s; gain before the certifier %.3e (%.3e of it from the bank tries)' % (
    old, S(lambda r: r['wall']), S(lambda r: sum(r['gain'])), S(lambda r: r['gain'][1])))


def scan(p):
    """tries, seconds, finds, gain of score, the sides of the first 6 tries, stopped, the try of the last find"""
    n = int(re.match(r'scan-(\d+)-', os.path.basename(p)).group(1)); held = best = None; t = sec = f = 0; g = 0.0; six = []; st = 0; last = 0
    for l in open(p):
        if l.startswith('# n='):
            held = best = float(re.search(r'held=([0-9.]+)', l).group(1))
        elif l.startswith('# FIND'):
            x = float(re.search(r'side ([0-9.]+)', l).group(1)); f += 1; g += (best - x) / math.sqrt(n); best = x
            last = int(re.search(r'FIND try (\d+)', l).group(1))
        elif l.startswith('# STOP6'):
            st = 1
        elif l[:1].isdigit():
            v = l.rstrip('\n').split('\t'); t += 1; sec += float(v[5])
            if len(six) < 6:
                six.append(v[4])
    return dict(n=n, tries=t, sec=sec, finds=f, gain=g, six=six, stopped=st, last=last)


ab = ['n\tseed\tstopped_tries\tstopped_seconds\told_tries\told_seconds\told_finds\told_gain\tlast_find_try\tfirst6_equal']
for p in sorted(glob.glob(run + '/s[5-6][0-9]/scan-*.tsv')):
    K = int(re.search(r'/s(\d+)/scan-', p).group(1)); q = '%s/s%d/%s' % (run, K - 20, os.path.basename(p))
    if not os.path.exists(q):
        continue
    o = scan(p); c = scan(q); seed = int(re.match(r'scan-\d+-(\d+)', os.path.basename(p)).group(1))
    same = 'yes' if o['six'][:len(c['six'])] == c['six'] and c['six'] else 'no'
    ab.append('%d\t%d\t%d\t%.0f\t%d\t%.0f\t%d\t%.3e\t%d\t%s' % (o['n'], seed, c['tries'], c['sec'], o['tries'], o['sec'], o['finds'], o['gain'], o['last'], same))
    print('old schedule on a stopped scan: n %d seed %d: stopped at %d tries, %.0f s; old schedule %d tries, %.0f s, %d finds, gain %.3e (last find at try %d); first 6 tries equal: %s' % (
        o['n'], seed, c['tries'], c['sec'], o['tries'], o['sec'], o['finds'], o['gain'], o['last'], same))
if len(sys.argv) > 2:
    open(sys.argv[2][:-4] + '-ab.tsv', 'w').write('\n'.join(ab) + '\n')

