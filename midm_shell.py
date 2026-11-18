#!/usr/bin/env python3
"""midm: the shell step of the family lane where its sweeps stop, at donors and targets under n = 300.

family_step.py and family_readers.py take a layout one shell up or down its line k - 2m: 2m + 3 squares more, or
2m + 1 less. Their sweeps skip every n under 300. This driver imports their reader, build, squeeze and finish, and
runs the steps that bound left out: a donor under 300 in both directions, and a donor from 300 up whose target is
under 300. A pair with donor and target from 300 up is left to those lanes.

  midm_shell.py list SUB.csv BARS.tsv OUT.tsv [--lo 222] [--hi 340]
        every pair that reads and builds, as built: donor, direction, target, the side as built, the reader, the bar
  midm_shell.py run  LIST.tsv SUB.csv OUTDIR [--deadline FILE] [--iters 60] [--buildsec 420] [--order gap]
        each step: build, the sequential LP, then fq and the LP (family_step.finish). One line per step goes to
        OUTDIR/rows.tsv. A result below its bar goes to OUTDIR/raw/<t>-<dir>from<donor>.csv, and one within 2e-3
        above it to OUTDIR/near/.
  midm_shell.py bandlist SUB.csv BARS.tsv OUT.tsv [--lo 222] [--hi 444]
        every band step of family_readers.band_step (1 to 3 shells, both ways) with its side as built and its bar
  midm_shell.py bandrun  LIST.tsv SUB.csv OUTDIR [--deadline FILE] [--within 0.03] [--mingap 2e-5]
        the band steps that start within 0.03 of side above the bar of a target that trails the board: the step,
        the sequential LP, then fq and the LP. Set SQ_APART=3e-2 so that a start with a small overlap is repaired.

SUB.csv holds rows n,square_id,x,y,angle (radians). BARS.tsv holds n, bar (a side) and gap (the gap of score to the
board, for the order of the run). Our own code; it reads packings as data only (run with python -I) and calls the
fq binary named by SQ_FQ through family_step.
"""
import argparse, csv, math, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_step as fs  # noqa: E402
import family_readers as fr  # noqa: E402


def bars_of(path):
    return {int(r['n']): (float(r['bar']), float(r['gap'])) for r in csv.DictReader(open(path), delimiter='\t')}


def cmd_list(a):
    P = fs.load(a.sub, set(range(a.lo, a.hi + 1))); bars = bars_of(a.bars)
    rows = ['donor\tdirection\ttarget\tbuilt\treader\tbar\tgap\tdonor_f']
    reads = 0
    for n in sorted(P):
        one = False
        for di in ('up', 'down'):
            try:
                G, info, R, who = fr.read_build(P[n], n, di, mine_first=True)
            except fr.Unreadable:
                continue
            except Exception as ex:
                print('error', n, di, str(ex)[:80]); continue
            one = True; t = len(G)
            if (n >= 300 and t >= 300) or t not in bars:
                continue
            s = fs.canon(P[n])[0]
            rows.append('%d\t%s\t%d\t%.9f\t%s\t%.9f\t%.3e\t%.6f' % (n, di, t, info['side'], who, bars[t][0], bars[t][1], s - math.floor(s + 1e-9)))
        reads += one
    open(a.out, 'w').write('\n'.join(rows) + '\n')
    print('%d layouts, %d read and build one way or both, %d steps listed' % (len(P), reads, len(rows) - 1))


def cmd_run(a):
    os.makedirs(a.out + '/raw', exist_ok=True); os.makedirs(a.out + '/near', exist_ok=True)
    jobs = list(csv.DictReader(open(a.list), delimiter='\t'))
    if a.order == 'gap':
        jobs.sort(key=lambda r: -float(r['gap']))
    P = fs.load(a.sub, {int(r['donor']) for r in jobs})
    tsv = a.out + '/rows.tsv'; done = set()
    if os.path.exists(tsv):
        done = {tuple(l.split('\t')[:2]) for l in open(tsv).read().splitlines()[1:]}
    else:
        open(tsv, 'w').write('donor\tdirection\ttarget\tbuilt\tlp\tfinal\tbar\tseconds\tstate\treader\n')

    def dead():
        try:
            return bool(a.deadline) and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False
    for r in jobs:
        n = int(r['donor']); di = r['direction']; bar = float(r['bar'])
        if (r['donor'], di) in done or dead():
            continue
        t0 = time.time(); built = lp = final = float('nan'); state = 'ok'; who = ''; t = int(r['target'])
        fs.set_limit(a.buildsec)
        try:
            G, info, R, who = fr.read_build(P[n], n, di, mine_first=True)
            built = info['side']
            X, L, trace = fs.squeeze(G, iters=a.iters, fq=False, stop=dead)
            lp = L
            X, L = fs.finish(X, L, bar, di, 2e-3, dead)
            final = L
            if final < bar - 1e-9:
                fs.write_rows('%s/raw/%d-%sfrom%d.csv' % (a.out, t, di, n), t, X); state = 'below the bar'
            elif final < bar + 2e-3:
                fs.write_rows('%s/near/%d-%sfrom%d.csv' % (a.out, t, di, n), t, X); state = 'near'
        except fr.Unreadable as ex:
            state = 'refused: %s' % str(ex)[:200]
        except Exception as ex:
            state = 'error: %s' % str(ex)[:80]
        if fs._over() and state == 'ok':
            state = 'time limit'
        fs.set_limit(None)
        with open(tsv, 'a') as h:
            h.write('%d\t%s\t%d\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\t%s\n' % (n, di, t, built, lp, final, bar, time.time() - t0, state, who))
        print(n, di, t, 'built %.6f lp %.6f final %.9f bar %.9f %+.2e' % (built, lp, final, bar, final - bar), state, who, '%.0fs' % (time.time() - t0), flush=True)


def cmd_bandlist(a):
    """Every band step (family_readers.band_step, 1 to 3 shells, both ways) of every layout that reads as a band."""
    P = fs.load(a.sub, set(range(a.lo, a.hi + 1))); bars = bars_of(a.bars)
    rows = ['donor\tdirection\tshells\ttarget\tbuilt\tgapbuilt\tbar\tgap\tcuts']; nb = 0
    for n in sorted(P):
        try:
            fr.band_frame(P[n])
        except Exception:
            continue
        one = False
        for di in ('down', 'up'):
            for k in (1, 2, 3):
                try:
                    G, info = fr.band_step(P[n], n, k, di)
                except Exception:
                    continue
                one = True; t = len(G)
                if t in bars:
                    rows.append('%d\t%s\t%d\t%d\t%.9f\t%.2e\t%.9f\t%.3e\t%d' % (n, di, k, t, info['side'], info['gap'], bars[t][0], bars[t][1], info['cuts']))
        nb += one
    open(a.out, 'w').write('\n'.join(rows) + '\n')
    print('%d layouts step as bands, %d steps listed' % (nb, len(rows) - 1))


def cmd_bandrun(a):
    """The band steps of LIST.tsv whose side as built is within --within of the bar and whose target trails the board
    by --mingap or more: band_step, the sequential LP, then fq and the LP. Rows go to OUTDIR/rows-band.tsv."""
    os.makedirs(a.out + '/raw', exist_ok=True); os.makedirs(a.out + '/near', exist_ok=True)
    jobs = [r for r in csv.DictReader(open(a.list), delimiter='\t')
            if float(r['built']) < float(r['bar']) + a.within and float(r['gap']) >= a.mingap and float(r['built']) > float(r['bar']) + 1e-9]
    jobs.sort(key=lambda r: (int(r['donor']) >= 300, float(r['built']) - float(r['bar'])))
    P = fs.load(a.sub, {int(r['donor']) for r in jobs})
    tsv = a.out + '/rows-band.tsv'
    if not os.path.exists(tsv):
        open(tsv, 'w').write('donor\tdirection\tshells\ttarget\tbuilt\tlp\tfinal\tbar\tseconds\tstate\n')

    def dead():
        try:
            return bool(a.deadline) and time.time() > float(open(a.deadline).read().split()[0])
        except Exception:
            return False
    for r in jobs:
        if dead():
            break
        n = int(r['donor']); di = r['direction']; k = int(r['shells']); t = int(r['target']); bar = float(r['bar'])
        t0 = time.time(); built = lp = final = float('nan'); state = 'ok'
        fs.set_limit(a.buildsec)
        try:
            G, info = fr.band_step(P[n], n, k, di)
            built = info['side']
            X, L, trace = fs.squeeze(G, iters=a.iters, fq=False, stop=dead)
            lp = L
            X, L = fs.finish(X, L, bar, di, 2e-3, dead)
            final = L
            if final < bar - 1e-9:
                fs.write_rows('%s/raw/%d-band%s%dfrom%d.csv' % (a.out, t, di, k, n), t, X); state = 'below the bar'
            elif final < bar + 2e-3:
                fs.write_rows('%s/near/%d-band%s%dfrom%d.csv' % (a.out, t, di, k, n), t, X); state = 'near'
        except fr.Unreadable as ex:
            state = 'refused: %s' % str(ex)[:200]
        except Exception as ex:
            state = 'error: %s' % str(ex)[:80]
        if fs._over() and state == 'ok':
            state = 'time limit'
        fs.set_limit(None)
        with open(tsv, 'a') as h:
            h.write('%d\t%s\t%d\t%d\t%.9f\t%.9f\t%.9f\t%.9f\t%.0f\t%s\n' % (n, di, k, t, built, lp, final, bar, time.time() - t0, state))
        print(n, di, k, t, 'built %.6f lp %.6f final %.9f bar %.9f %+.2e' % (built, lp, final, bar, final - bar), state, '%.0fs' % (time.time() - t0), flush=True)


def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    q = sp.add_parser('list'); q.add_argument('sub'); q.add_argument('bars'); q.add_argument('out')
    q.add_argument('--lo', type=int, default=222); q.add_argument('--hi', type=int, default=340); q.set_defaults(fn=cmd_list)
    q = sp.add_parser('run'); q.add_argument('list'); q.add_argument('sub'); q.add_argument('out'); q.add_argument('--deadline')
    q.add_argument('--iters', type=int, default=60); q.add_argument('--buildsec', type=float, default=420.0)
    q.add_argument('--order', default='gap'); q.set_defaults(fn=cmd_run)
    q = sp.add_parser('bandlist'); q.add_argument('sub'); q.add_argument('bars'); q.add_argument('out')
    q.add_argument('--lo', type=int, default=222); q.add_argument('--hi', type=int, default=444); q.set_defaults(fn=cmd_bandlist)
    q = sp.add_parser('bandrun'); q.add_argument('list'); q.add_argument('sub'); q.add_argument('out'); q.add_argument('--deadline')
    q.add_argument('--iters', type=int, default=60); q.add_argument('--buildsec', type=float, default=420.0)
    q.add_argument('--within', type=float, default=0.03); q.add_argument('--mingap', type=float, default=2e-5); q.set_defaults(fn=cmd_bandrun)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
