#!/usr/bin/env python3
"""quench (round 28): fill idle boxB quench slots with kick jobs on the current best rows.

Usage: quench_kickfeed.py TAKEDIR DEADLINE_EPOCH [--seconds 180] [--per-n 3]

Every 2 minutes, until 40 minutes before the deadline: when a boxA or boxB queue (q-boxB.txt, q-boxA.txt) has no job
waiting, add one kick job to it. A target is a finished plain quench job whose certified final.csv sits within
1e-9 of score of the live bar of its n (work/bar-collect.tsv) and whose start the follow walked clean. Fresh rows
go first: an n whose bar comes from a round 27 or 28 take before an n whose bar is the held file. Each n gets at
most PER_N kick seeds (2800 + k). The kick job is quench_kick.sh on the box (invent_rest.py lkick, then the fq
loop); its source.txt embeds the source of the plain job, so quench_publish.py walks the same start copy again.
Measured reason: backlog kicks of fresh rows gave rows in round 27 (743 by 6.6e-6 of score, 642 by 8.0e-6), and the
quench slots sat idle once the follow queue drained.
"""
import csv, glob, hashlib, json, math, os, re, shutil, subprocess, sys, time

LANE = os.path.dirname(os.path.abspath(__file__))
S = '$SCRATCH/bounties-squares/'
PY = S + 'venv/bin/python'
RECT_WIN = 1e-4  # round 29: side window of a forensics rectangle target
FQKICK = False  # round 29: quench_fqkick.sh is off (r28: 0 of 22 moved)


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def walk_now(J):
    """The current quench_walk.py on the job's start copy, cached in J/walk-kick.json by walk sha (the follow's walk.json
    can be older than a withdrawal or a name the walk learned later: backlog r27 642, dropped by the r27 assembler)."""
    import re
    sys.path.insert(0, LANE)
    import quench_walk as qw
    ver = hashlib.sha256(open(LANE + '/quench_walk.py', 'rb').read()).hexdigest()[:16]
    mark = J + '/walk-kick.json'
    if os.path.exists(mark):
        m = json.load(open(mark))
        if m.get('walk_sha') == ver and time.time() - m.get('t', 0) < 3600:
            return m['clean']
    st = re.search(r'of (take-[a-z0-9-]+-r\d+/work/starts/[0-9a-f]{16}/\S+?\.csv) ', open(J + '/source.txt').read())
    if not st:
        return False
    w = qw.check(S + st.group(1))
    if getattr(qw, '_kf_ver', ver) != ver:
        return False  # the walk changed after this process imported it
    qw._kf_ver = ver
    json.dump({'walk_sha': ver, 'clean': w['clean'], 'hits': w['hits'][:4], 't': time.time()}, open(mark, 'w'))
    return w['clean']


def scope_ok(J):
    """Round 32 (QUENCH_KICK_SCOPE=public): kick only our own fq outputs of public-first starts (harvest files and rows whose
    walk reached no held row), and only after the output share gate passed them (audit-ok). Round 31 measured: every large row
    came from fresh public-first harvest files (741 791 852 743), while 108 of 115 probes of polished held rows were dry; backlog
    and midm follow other lanes' fresh rows."""
    if os.environ.get('QUENCH_KICK_SCOPE') != 'public':
        return True
    if not os.path.exists(J + '/audit-ok'):
        return False
    try:
        w = json.load(open(J + '/walk.json'))
    except Exception:
        return False
    own = open(J + '/source.txt').read(6000).split(' | recorded source', 1)[0]  # the job's own start, not a quoted older record
    return bool(w.get('pubfirst')) or 'that the harvest lane wrote' in own


def others():
    """Round 29: the counts other lanes already kick this round. rebuild: every n in its queue log with a kick
    (900 s midm_scan lkick,kick, the same kick as our kick 1); backlog: every n it claims in the handoff log (its follow
    runs the 180 s lkick and the midm kick). Our kick feeder does not repeat a 900 s midm kick that rebuild queued."""
    reb, bl, shas = set(), set(), set()
    # round 30 (16:15Z): a claim covers its n for QUENCH_CLAIM_TTL_MIN minutes only (default 60), as the round 30 comment
    # below meant ("no second kick of the same row in the same hour"). A claim has no end time, so stair-c's fresh 995
    # rows (16:08Z) stayed out of our kicks behind border's two 12:14Z claims on an older 995 row.
    ttl = float(os.environ.get('QUENCH_CLAIM_TTL_MIN', '60')) * 60
    day = time.strftime('%Y-%m-%d', time.gmtime())

    def fresh_claim(ts):
        m = re.match(r'(\d{4}-\d\d-\d\d)?T?(\d\d):(\d\d):(\d\d)', ts)
        if not m:
            return True
        try:
            t0 = time.mktime(time.strptime('%s %s:%s:%s' % (m.group(1) or day, m.group(2), m.group(3), m.group(4)), '%Y-%m-%d %H:%M:%S')) - time.timezone
        except ValueError:
            return True
        return time.time() - t0 < ttl
    try:
        for l in open(S + 'take-rebuild-%s/work/queue-log.tsv' % os.environ.get('QUENCH_ROUND', 'r32'), errors='replace'):
            t = l.rstrip('\n').split('\t')
            if len(t) > 7 and t[7].startswith('kick') and t[3].isdigit() and fresh_claim(t[0]):
                reb.add(int(t[3]))
    except OSError:
        pass
    try:
        for l in open(S + 'handoff-%s.log' % os.environ.get('QUENCH_ROUND', 'r32'), errors='replace'):
            if not fresh_claim(l[:19]):
                continue
            m = re.search(r' backlog -> \S+: claims \S+, start \S*?/(\d+)-', l)
            if m:
                bl.add(int(m.group(1)))
            # border claims 900 s midm kicks too (07:27Z: the items rebuild skipped with full queues)
            m = re.search(r' (?:border|rebuild) -> [^:]*: claim: \d+ s midm\S* [^\n]*? of n=(\d+)', l)
            if m:
                reb.add(int(m.group(1)))
            # round 30: any other lane's claim line covers its n for us (no second kick of the same row in the same hour)
            lm = re.match(r'\S+\s+([a-z0-9-]+)\s+->', l)
            if lm and lm.group(1) != 'quench' and re.search(r'claim', l, re.I):
                # round 31: the exact bytes a claim names (sha256 prefixes of 12 or more hex digits)
                for m in re.finditer(r'sha256[=:\s]+([0-9a-f]{12,64})', l):
                    shas.add(m.group(1))
                for m in re.finditer(r'\bn\s*=\s*(\d+)', l):
                    reb.add(int(m.group(1))); bl.add(int(m.group(1)))
                m = re.search(r'start \S*?/(\d+)-', l)
                if m:
                    reb.add(int(m.group(1))); bl.add(int(m.group(1)))
    except OSError:
        pass
    return reb, bl, shas


def main():
    T, DL = sys.argv[1].rstrip('/'), int(sys.argv[2])
    sec = int(sys.argv[sys.argv.index('--seconds') + 1]) if '--seconds' in sys.argv else 180
    per_n = int(sys.argv[sys.argv.index('--per-n') + 1]) if '--per-n' in sys.argv else 2
    W = T + '/work'
    fresh, base = {}, {}
    # round 29: the round's bar file (bar29.tsv: the held round 27 b file lowered by the round 28 takes)
    for r in csv.DictReader(open(os.environ.get('QUENCH_BAR_FILE', S + 'round32-briefs/bar32.tsv')), delimiter='\t'):
        fresh[int(r['n'])] = 'take-' in r['source']
        base[int(r['n'])] = float(r['bar'])
    # round 29: 30 min (was 40); QUENCH_FEED_STOP_MIN lowers it for short kicks (quench_kick.sh caps the kick at the deadline less 60 s)
    while time.time() < DL - int(os.environ.get('QUENCH_FEED_STOP_MIN', '30')) * 60:
        try:
            bar = {int(r['n']): (float(r['score']), float(r['side']), r['origin']) for r in csv.DictReader(open(W + '/bar-collect.tsv'), delimiter='\t')}
        except OSError:
            time.sleep(60); continue
        kicks, fqk = {}, {}
        ff = os.environ.get('QUENCH_KICK_FIRST')
        first = [int(x) for x in open(ff).read().split()] if ff and os.path.exists(ff) else []
        reb, bl, cl_sha = others()
        for k in glob.glob(W + '/jobs/fk-*/kick.json'):
            n = json.load(open(k))['n']; kicks[n] = kicks.get(n, 0) + 1
        for k in glob.glob(W + '/jobs/fx-*/fqkick.txt'):
            n = int(open(k).read().split()[0]); fqk[n] = fqk.get(n, 0) + 1
        targets = []
        for rj in glob.glob(W + '/jobs/fo-*/result.json'):
            J = os.path.dirname(rj)
            try:
                r = json.load(open(rj)); w = json.load(open(J + '/walk.json'))
            except Exception:
                continue
            n = r['n']
            if not w.get('clean') or os.path.exists(J + '/withdrawn') or not os.path.exists(J + '/final.csv') or n not in bar:
                continue
            if not scope_ok(J):
                continue
            # round 29: a forensics rectangle within RECT_WIN of side of the bar side is a target too (rebuild r28: one
            # 900 s kick of the 684 rectangle at the bar side gave 9.0e-5 of score; 18 of 88 such rectangles had a slot)
            rect = '/take-forensics-r' in open(J + '/source.txt').read()[:2000]
            lim = RECT_WIN / math.sqrt(n) if rect else 1e-9
            if not math.isfinite(r['final_score']) or r['final_score'] > bar[n][0] + lim:
                continue
            fr = fresh.get(n, False) or bar[n][2] != 'base' or rect
            # round 31 lesson b: backlog is the follow lane for fresh certified rows of other lanes; we kick such a row only
            # when backlog has not claimed it within 10 minutes (round 30 lost about 30 jobs per lane to duplicate kicks)
            msrc = re.search(r'of the file (\S+) that the ([a-z0-9-]+) lane wrote at or before (\S+?);', open(J + '/source.txt').read(4000))
            if msrc and msrc.group(2) not in ('quench', 'another') and re.fullmatch(r'\d+\.csv', msrc.group(1)):
                try:
                    tq = time.mktime(time.strptime(msrc.group(3), '%Y-%m-%dT%H:%M:%SZ')) - time.timezone
                except ValueError:
                    tq = 0
                if time.time() - tq < 600:
                    continue
            if n in reb and (n in bl or kicks.get(n, 0) >= 1):
                continue  # rebuild kicks it 900 s and backlog follows it, or we gave it our one lkick already
            # round 29: QUENCH_KICK_FIRST lists counts whose kick 1 goes before every other target, in file order (the held
            # Samanyu-seed rows: parked by the seed rule through round 28, so no lane kicked them; override 2 lifts it)
            targets.append((first.index(n) if n in first and kicks.get(n, 0) == 0 else len(first), not fr, kicks.get(n, 0), r['final_score'] - bar[n][0], n, J))
        # round 29: no fq kicks on boxD (r28: 0 of 22 quench_fqkick.sh jobs moved the side); boxD runs kick jobs with its venv
        targets = [t[1:] + (t[0],) for t in sorted(targets)]  # back to (not fr, kicks, margin, n, J), first-list order kept
        fxt = [] if not FQKICK else sorted((t[0], fqk.get(t[3], 0)) + t[2:5] for t in targets if fqk.get(t[3], 0) < per_n)
        targets = [t[:5] for t in targets if t[1] < per_n]
        # round 30: chain a kick on our own fresh kick find, first in the order (r29 next item 2: backlog and rebuild took
        # four of our five seed-row finds with a second kick within minutes; 587 improved on 38 of its first 50 tries)
        chain, chainJ, big = [], set(), set()
        for rj in glob.glob(W + '/jobs/fk-*/result.json') + glob.glob(W + '/jobs/fo-*/result.json'):
            J = os.path.dirname(rj)
            try:
                r = json.load(open(rj))
            except Exception:
                continue
            n = r['n']
            # round 30: a plain fq job that counts by 1e-7 or more (a raw near file of another lane, certified by us: 694 and
            # 814 at 12:20Z) is a fresh row too, and its first kick goes before the held list
            if '/fo-' in J and not (r.get('counts') and r.get('margin', 0) >= 1e-7):
                continue
            # round 31: a kick find of ours that moved its start by more than QUENCH_CHAIN_SIDE chains even when another
            # lane's follow of an earlier find sits a little lower (21:18Z: backlog's 180 s lkick of our 741 find took 741
            # 2.7e-7 lower, and our next leg landed 3.4e-8 above it with the chain stopped): it must be below the round bar
            # and within QUENCH_CHAIN_WIN of score of the live bar
            near_live = ('/fk-' in J and math.isfinite(r.get('final_score', math.inf)) and n in base and n in bar
                         and r['final_score'] < base[n] - 1e-10 and r['final_score'] <= bar[n][0] + float(os.environ.get('QUENCH_CHAIN_WIN', '1e-6')))
            if not (r.get('counts') or near_live) or os.path.exists(J + '/withdrawn') or not os.path.exists(J + '/final.csv') or n not in bar:
                continue
            if not scope_ok(J):
                continue
            if '/fk-' in J:
                # round 30: chain a kick only while the kick moved its start by more than 1e-8 of side (12:58Z: 694 chained
                # six times on certify-level byte changes, each kick 0 to 5e-10 of side from its start)
                m0 = re.search(r'from the certified output of (\S+/jobs/f[ko]-[^ ]+) ', open(J + '/source.txt').read(3000))
                try:
                    s0 = json.load(open(S + m0.group(1) + '/result.json'))['final_score']
                except Exception:
                    continue
                # round 31: chain only a find that moved more than QUENCH_CHAIN_SIDE of side (default 1e-6; round 30 lesson a:
                # chain a leg from every find that moves more than 1e-6 of side). A find that gained 1e-5 of score or more
                # gets at least two more seeds on the same row (midm r30: 412 seeds gained 1.6e-7, 7.0e-6, 7e-11 and 0).
                if (s0 - r['final_score']) * math.sqrt(n) <= float(os.environ.get('QUENCH_CHAIN_SIDE', '1e-6')):
                    continue
                if s0 - r['final_score'] >= 1e-5:
                    big.add(J)
            if not math.isfinite(r['final_score']) or (r['final_score'] > bar[n][0] + 1e-9 and not near_live) or kicks.get(n, 0) >= 10:
                continue
            if os.environ.get('QUENCH_KICK_SCOPE') == 'public' and kicks.get(n, 0) >= per_n:
                continue  # round 32: one kick per n (harvest hands up to 12 byte versions of one public row; each fq output differs)
            csha = hashlib.sha256(open(J + '/final.csv', 'rb').read()).hexdigest()
            if '/fk-' in J and any(csha.startswith(x) for x in cl_sha):
                continue  # round 31: another lane claimed these exact bytes within the hour
            if (n in reb or n in bl) and '/fk-' not in J:
                continue  # round 30: another lane claimed this n (backlog follows our take rows within minutes: 655 584 339);
                # round 31: a kick find of ours is new bytes, so only a claim of those exact bytes stops its chain (brief 6b)
            if len(glob.glob(W + '/jobs/fk-%d-%s-s*' % (n, csha[:10]))) >= (3 if J in big else 1):
                continue
            chain.append((r['final_score'] - bar[n][0], n, J)); chainJ.add(J)
        chain.sort()
        cn = {c[1] for c in chain}
        targets = [(False, kicks.get(n, 0), m, n, J) for m, n, J in chain] + [t for t in targets if t[3] not in cn]
        # boxD has no python: its idle slot gets quench_fqkick.sh (fq's own kick and the polish, 300 s)
        q = W + '/q-boxD.txt'
        waiting = [j for j in open(q).read().split() if not os.path.exists(j + '/done') and not os.path.exists(j + '/claimed')]
        while not waiting and fxt:
            _, kn, _, n, J = fxt.pop(0)
            seed = 2900 + kn
            data = open(J + '/final.csv', 'rb').read()
            sha = hashlib.sha256(data).hexdigest()
            K = W + '/jobs/fx-%d-%s-s%d' % (n, sha[:10], seed)
            if os.path.exists(K):
                continue
            os.makedirs(K)
            open(K + '/start.csv', 'wb').write(data)
            p = subprocess.run([PY, '-I', LANE + '/quench_once.py', 'prep', K + '/start.csv', K, '--no-cert'], capture_output=True, text=True)
            if p.returncode:
                shutil.rmtree(K); continue
            open(K + '/fqkick.txt', 'w').write('%d %d 300\n' % (n, seed))
            src = open(J + '/source.txt').read().strip()
            open(K + '/source.txt', 'w').write(
                'quench lane fq kick: quench_fqkick.sh (fq --kick 0.003 to 0.04, loosen 1.0 or 1.005, then the deep polish, 300 s, '
                'seed %d), from the certified output of %s (final.csv, sha256 %s); that job: %s' % (seed, J.replace(S, ''), sha[:16], src))
            shutil.copyfile(J + '/licence.txt', K + '/licence.txt')
            shutil.copyfile(J + '/walk.json', K + '/walk.json')
            open(q, 'a').write(K + '\n')
            open(T + '/STATE.txt', 'a').write('%s boxA KICKFEED QUEUE fqkick n=%d seed %d from %s -> q-boxD.txt\n' % (now(), n, seed, os.path.basename(J)))
            break
        for q in sorted(x for x in glob.glob(W + '/q-*.txt') if 'deferred' not in x):  # round 31: every slot queue (boxD has two)
            waiting = [j for j in open(q).read().split() if not os.path.exists(j + '/done') and not os.path.exists(j + '/claimed')]
            # round 29: walk the targets lazily, in queue order, only when a queue is empty. The feeder walked all
            # 248 targets first (a walk change voids every cached walk), 45 minutes with the three slots idle (09:05Z).
            pick = None
            while not waiting and targets and pick is None:
                t = targets.pop(0)
                if walk_now(t[4]):
                    pick = t
            if pick is None:
                continue
            _, kn, _, n, J = pick
            targets = [t for t in targets if t[3] != n]
            seed = 2800 + kn
            data = open(J + '/final.csv', 'rb').read()
            sha = hashlib.sha256(data).hexdigest()
            K = W + '/jobs/fk-%d-%s-s%d' % (n, sha[:10], seed)
            if os.path.exists(K):
                continue
            os.makedirs(K)
            open(K + '/start.csv', 'wb').write(data)
            p = subprocess.run([PY, '-I', LANE + '/quench_once.py', 'prep', K + '/start.csv', K, '--no-cert'], capture_output=True, text=True)
            if p.returncode:
                shutil.rmtree(K); continue
            # kick 1 of an n is the invent lkick, kick 2 midm_scan's fq kicks, kick 3 midm_scan melt and hop (round 28:
            # the first 8 invent lkicks found nothing, so the later seeds change the kind of move)
            # round 29: kick 1 is rebuild's 900 s midm_scan lkick,kick (r28: 684 rectangle 9.0e-5, 748 3.1e-5, 910 8.4e-6 on
            # first kicks); kick 2 the 180 s invent lkick (r28: 6 of 64 of our kicks moved over 1e-8 of side, all of them lkicks).
            # r28 measured the 300 s midm kick,lkick,bkick and melt,hop kicks: none moved past the certify slack.
            tool, modes = [('midm', 'lkick,kick'), ('lkick', '')][min(kn, 1)]
            if J in chainJ:
                tool, modes = 'midm', 'lkick,kick'  # round 30: a chained kick of our own find is the midm kick again
            elif n in reb:
                tool, modes = 'lkick', ''  # rebuild runs the 900 s midm kick of this n: ours is the 180 s lkick, once
            ksec = 900 if tool == 'midm' else sec
            if tool == 'midm' and (n in first or J in chainJ) and os.environ.get('QUENCH_FIRST_SECONDS'):
                # round 29: a shorter kick covers more parked seed rows; 587 (a loose seed row) improved on 38 of its
                # first 50 lkick tries, the tight ones (150, 203, 204, 107, 406, 537) on none of 100 to 4813
                ksec = int(os.environ['QUENCH_FIRST_SECONDS'])
            if not os.environ.get('QUENCH_NO_CLAIM'):
                # round 31 lesson b: the claim names the sha256 of the start we kick (the other lane's file or the held row copy)
                mst = re.search(r'of (take-quench-r\d+/work/starts/[0-9a-f]{16}/\S+?\.csv) ', open(J + '/source.txt').read(3000))
                ssha = hashlib.sha256(open(S + mst.group(1), 'rb').read()).hexdigest() if mst and os.path.exists(S + mst.group(1)) else '?'
                open(S + 'handoff-%s.log' % os.environ.get('QUENCH_ROUND', 'r32'), 'a').write('%s quench -> all: claim: %d s %s kick (seed %d) of n=%d, start sha256 %s, job %s (kick bytes sha256 %s, our certified fq of %s)\n' % (
                    now(), ksec, 'midm_scan lkick,kick' if tool == 'midm' else 'invent lkick', seed, n, ssha, K.replace(S, ''), sha[:16],
                    (re.search(r'of the file (\S+) that the (\S+) lane', open(J + '/source.txt').read()) or ['', 'a start'])[0][12:] or J.replace(S, '')))
            # round 31: a 900 s midm kick runs a probe first (quench_kick.sh stops it when no try comes 1e-9 of side below the
            # start in about 120 s); the extra seeds of a find that gained 1e-5 of score or more run without the probe
            nprior = len(glob.glob(W + '/jobs/fk-%d-%s-s*' % (n, sha[:10])))
            probe = 0 if (tool != 'midm' or (J in big and nprior >= 2)) else int(os.environ.get('QUENCH_PROBE', '120'))  # nprior counts K itself
            json.dump({'n': n, 'seed': seed, 'seconds': ksec, 'bar_side': bar[n][1], 'tool': tool, 'modes': modes, 'probe': probe}, open(K + '/kick.json', 'w'))
            src = open(J + '/source.txt').read().strip()
            open(K + '/source.txt', 'w').write(
                'quench lane kick: %s (%d s, seed %d), then the fq loop of '
                'quench_box.sh, from the certified output of %s (final.csv, sha256 %s); that job: %s' % (
                    'invent_rest.py lkick' if tool == 'lkick' else 'midm_scan.py --modes ' + modes, ksec, seed, J.replace(S, ''), sha[:16], src))
            shutil.copyfile(J + '/licence.txt', K + '/licence.txt')
            shutil.copyfile(J + '/walk.json', K + '/walk.json')
            open(q, 'a').write(K + '\n')
            open(T + '/STATE.txt', 'a').write('%s boxA KICKFEED QUEUE n=%d seed %d from %s -> %s\n' % (now(), n, seed, os.path.basename(J), os.path.basename(q)))
        time.sleep(120)


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
