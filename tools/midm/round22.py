#!/usr/bin/env python3
"""Round 22 snapshots, collection and handoffs. No heavy search runs on the local box."""
import csv
import glob
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r22'
W = T / 'work'
L = Path('.')
PY = str(B / 'venv/bin/python')
REMOTE = 'boxE:scratch/squares-midm/'
SD = 'scratch/squares-midm'
END = 1794583200  # 2026-11-13 15:20 UTC
ENV = dict(os.environ, MIDM_CACHE=str(W / 'floatsafe-cache.pkl'),
           MIDM_LIVE=str(B / 'take-*-r21') + ' ' + str(B / 'take-*-r22'),
           MIDM_SNAPS=str(W), MIDM_TAGSDIR=str(W), MIDM_RAWBASE=str(W / 'raw-in'))


def run(args, **kw):
    return subprocess.run(args, check=True, **kw)


def state(s):
    with (T / 'STATE.txt').open('a') as f:
        f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ boxA ', time.gmtime()) + s + '\n')
    print(s, flush=True)


def rows(p):
    return list(csv.DictReader(p.open(), delimiter='\t')) if p.exists() else []


def atomic(p, s):
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(s)
    tmp.replace(p)


def historical():
    hist = []
    for rnd, low in ((20, 43), (21, 21)):
        ww = B / ('take-midm-r%d/work' % rnd)
        for tab in ww.glob('r*.tsv'):
            try:
                k = int(tab.stem[1:])
            except ValueError:
                continue
            if k < low:
                continue
            for r in rows(tab):
                scans = list((ww / ('r%d-boxE/run/s%d' % (rnd, k))).glob('scan-%s-*.tsv' % r['n']))
                if any(sum(l[:1].isdigit() for l in p.open()) >= 6 for p in scans):
                    hist.append((int(r['n']), float(r['score']), Path(r['dir']).name))
    return hist


def snapshot():
    dbp = W / 'queue-state.json'
    db = json.loads(dbp.read_text()) if dbp.exists() else {'k': 200, 'seen': [], 'previous': [], 'ab': 0}
    seen = set(db['seen'])
    hist = historical() if not (W / 'history.json').exists() else json.loads((W / 'history.json').read_text())
    if not (W / 'history.json').exists():
        atomic(W / 'history.json', json.dumps(hist))
    held = {int(r['n']): float(r['score']) for r in csv.DictReader((B / 'gate/cand-round20-1113a/details.csv').open())}
    own = {int(r['n']): float(r['new']) for r in rows(T / 'take.tsv')}
    candidates = []
    low = dict(held)
    for pat in ('take-*-r21', 'take-*-r22'):
        for dp in B.glob(pat):
            for rr in rows(dp / 'take.tsv'):
                try:
                    nn, ss = int(rr['n']), float(rr['new'])
                    low[nn] = min(low[nn], ss)
                except (KeyError, ValueError):
                    pass
    own21 = {int(rr['n']): float(rr['new']) for rr in rows(B / 'take-midm-r21/take.tsv')}
    for rnd in (20, 21, 22):
        for dstr in glob.glob(str(B / ('take-*-r%d' % rnd))):
            d = Path(dstr)
            if d == T or d.name.startswith('take-assemble'):
                continue
            lane = d.name[5:-4]
            for r in rows(d / 'take.tsv'):
                try:
                    n = int(r['n'])
                    sc = float(r['new'])
                    f = d / ('%d.csv' % n)
                    digest = hashlib.sha256(f.read_bytes()).hexdigest()
                except (ValueError, KeyError, OSError):
                    continue
                if digest in seen:
                    continue
                isfor = rnd == 22 and (lane == 'forensics' or (lane in ('polish','harvest') and re.match(r'^(?:fq quench of )*forensics_rect[.]py',r.get('source','').lower()) is not None))
                if lane == 'midm' or sc >= held[n] - 1e-10 or (not isfor and n in own and sc >= own[n] - 1e-10):
                    seen.add(digest)
                    continue
                if not isfor and rnd < 22 and sc > low[n] + 1e-10 and not (rnd == 20 and n in (646, 649, 754, 852, 933, 982, 995)):
                    seen.add(digest)
                    continue
                if (n in own21 and abs(sc - own21[n]) < 1e-8) or (not isfor and n in own and abs(sc-own[n])<1e-8):
                    seen.add(digest)
                    continue
                # Historical scans and posted kick finds have already had their first kick.
                kicked = any(hn == n and (hd == d.name or lane in ('polish', 'harvest')) and abs(hs - sc) < 1e-6 for hn, hs, hd in hist)
                if rnd == 21 and lane == 'k123' and n in (494, 851):
                    kicked = False
                source_head = r.get('source', '').lower()[:110]
                kicked = kicked or lane in ('invent', 'classfill') or source_head.startswith(('fq kick', 'fq quench of fq kick', 'lkick', 'kick', 'invent_rest'))
                if kicked and (rnd < 22 or lane in ('polish', 'harvest')):
                    seen.add(digest)
                    continue
                if any(pn == n and abs(ps - sc) < 1e-6 and (pd == d.name or lane in ('polish', 'harvest')) for pn, ps, pd in db['previous']) and (not isfor or lane in ('polish', 'harvest')):
                    seen.add(digest)
                    continue
                priority = 0 if isfor else ((1 if n < 640 else 1.5) if rnd == 22 and not kicked else (3 if rnd == 21 else (4 if rnd == 20 else 5)))
                candidates.append((priority, -f.stat().st_mtime, n, sc, d, f, r, digest, kicked))
    transfer = []
    for priority, stamp, n, sc, d, f, r, digest, kicked in sorted(candidates, key=lambda x: x[:2]):
        if digest in seen:
            continue
        k = db['k']
        while (W / ('r%d.tsv' % k)).exists():
            k += 1
        db['k'] = k + 1
        rd = W / ('r%d' % k); rd.mkdir(exist_ok=True)
        shutil.copyfile(f, rd / f.name)
        source = '%s; %s/take.tsv; held ancestry: results/round20-best-2026-11-13.tsv' % (r.get('source', ''), d.name)
        table = 'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\t%s\t%s\t%s\t%g\n' % (
            n, sc, d.name, source.replace('\t', ' '), r.get('licence', '').replace('\t', ' '), priority)
        atomic(W / ('r%d.tsv' % k), table)
        transfer.append(str(rd))
        secs = 150 if n < 700 else (225 if n < 800 else 450)
        j = dict(k=k, n=n, sub='r%d/%d.csv' % (k, n), seed=n+2200, seconds=secs, sigma=0.04,
                 priority=priority, created=-stamp, leg=0, source=d.name)
        if priority == 0:
            j['slot']=1
        pending = []
        # The first six fresh round 22 builds get equal-time, same-seed paired scans.
        if d.name.endswith('-r22') and not kicked and db['ab'] < 6:
            db['ab'] += 1
            j.update(ab=True, slot=2)
            k2 = db['k']; db['k'] += 1
            atomic(W / ('r%d.tsv' % k2), table)
            j2 = dict(j, k=k2, sigma=0.02, slot=1)
            pending.append(j2)
        pending.append(j)
        jd = W / 'jobs'; jd.mkdir(exist_ok=True)
        for task in pending:
            atomic(jd / ('%d-%d.json' % (task['k'], n)), json.dumps(task))

        seen.add(digest)
        db['previous'].append([n, sc, d.name])
        state('QUEUE boxE k=%d n=%d source=%s priority=%g%s deadline=15:20Z logs=work/boxE/logs/worker.log' % (
            k, n, d.name, priority, ' paired sigma=0.02/0.04 same seed' if j.get('ab') else ' sigma=0.04'))
    if transfer:
        run(['rsync', '-a'] + transfer + [REMOTE])
        run(['rsync', '-a', str(W / 'jobs') + '/', REMOTE + 'jobs/'])
    db['seen'] = sorted(seen)
    atomic(dbp, json.dumps(db))



def live_bars():
    low={int(x['n']):float(x['score']) for x in csv.DictReader((B/'gate/cand-round20-1113a/details.csv').open())}
    for pat in ('take-*-r21','take-*-r22'):
        for d in B.glob(pat):
            for x in rows(d/'take.tsv'):
                low[int(x['n'])]=min(low[int(x['n'])],float(x['new']))
    return low


def raw_seconds(n,score,bar):
    if n>=640 and score>bar+2e-5:
        return 75
    return 150 if n<700 else (225 if n<800 else 450)


def newdesigns():
    """Explicit new-design handoffs override the exclusion of old near layouts."""
    hand = B / 'handoff-r22.log'
    if not hand.exists():
        return
    dbp = W / 'queue-state.json'
    db = json.loads(dbp.read_text())
    seen = set(db['seen'])
    handled = set(db.get('design_lines', []))
    import re
    sys.path.insert(0, str(L))
    import methods_lp as mlp
    import math
    transfer = []
    bars = live_bars()
    for line in hand.read_text().splitlines():
        key = hashlib.sha256(line.encode()).hexdigest()
        if key in handled:
            continue
        # A new generation of strip or rounded-band layouts changes the old near-start experiment.
        if not ('new build n=' in line or ('fresh rounded' in line and 'midm' in line)):
            continue
        for name in re.findall(r'$SCRATCH/bounties-squares/[^ ,;]+\.csv', line):
            f = Path(name)
            if not f.exists():
                continue
            handled.add(key)
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            if digest in seen:
                continue
            loaded = mlp.load(str(f), None)
            if len(loaded) != 1:
                continue
            n, packing = next(iter(loaded.items()))
            if len(packing) != n:
                continue
            sc = float(mlp.side(packing) / math.sqrt(n) - 1)
            d = next((p for p in f.parents if p.name.startswith('take-') and p.name.endswith('-r22')), None)
            if d is None:
                continue
            k = db['k']
            while (W / ('r%d.tsv' % k)).exists():
                k += 1
            db['k'] = k + 1
            rd = W / ('r%d' % k); rd.mkdir(exist_ok=True)
            shutil.copyfile(f, rd / ('%d.csv' % n))
            source = 'new-design raw start: %s; handoff: %s; %s/take.tsv and results/round20-best-2026-11-13.tsv give ancestry' % (f, line.replace('\t', ' '), d.name)
            table = 'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\t%s\t%s\t%s\t1\n' % (n, sc, d.name, source, 'ours on the named donor; its lane take.tsv and round20 source table give upstream licences')
            atomic(W / ('r%d.tsv' % k), table)
            j = dict(k=k, n=n, sub='r%d/%d.csv' % (k,n), seed=n+6200, seconds=raw_seconds(n,sc,bars[n]), sigma=0.04, priority=1.25 if n<640 else 1.75, created=f.stat().st_mtime, leg=0, source=d.name, raw_design=True)
            atomic(W / 'jobs' / ('%d-%d.json' % (k,n)), json.dumps(j))
            transfer.append(str(rd))
            seen.add(digest)
            db['previous'].append([n,sc,d.name])
            state('QUEUE NEW-DESIGN exception n=%d k=%d raw=%s; old near failures used old geometry; deadline15:20Z' % (n,k,f))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE])
        run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])
    db['seen'] = sorted(seen)
    db['design_lines'] = sorted(handled)
    atomic(dbp, json.dumps(db))



def promote_legs():
    """Keep raw-find legs in their small/large classes without starting another worker."""
    local = W / 'remote-jobs'
    local.mkdir(exist_ok=True)
    run(['rsync','-a',REMOTE+'jobs/',str(local)+'/'])
    changed = W / 'leg-priorities'; changed.mkdir(exist_ok=True)
    for p in changed.glob('*.json'):
        p.unlink()
    bars=live_bars()
    sys.path.insert(0,str(L))
    import methods_lp as mlp
    import math
    canceled=[]
    for p in local.glob('*-L*.json'):
        j = json.loads(p.read_text())
        tab=W/('r%d.tsv'%j['k'])
        if j['n']>=640 and tab.exists() and 'new-design raw start:' in tab.read_text():
            source=W/'boxE'/j['sub']
            if not source.exists():
                continue
            P=mlp.load(str(source),{j['n']})[j['n']]
            sc=float(mlp.side(P)/math.sqrt(j['n'])-1)
            if sc>bars[j['n']]+2e-5:
                (W/'cancel').mkdir(exist_ok=True)
                marker=W/'cancel'/p.stem
                if not marker.exists():
                    marker.touch();state('CANCEL far raw-design leg '+p.stem+'; still over live bar by %.6g score'% (sc-bars[j['n']]))
                canceled.append(marker)
                continue
        j['priority'] = 0.5 if j['n'] < 640 else 1.6
        atomic(changed / p.name, json.dumps(j))
    if canceled:
        run(['rsync','-a']+[str(p) for p in canceled]+[REMOTE+'cancel/'])
    if list(changed.glob('*.json')):
        run(['rsync','-a',str(changed)+'/',REMOTE+'jobs/'])


def certify(rawdirs, target, stage=False):
    env = dict(ENV, MIDM_TAGSDIR=str(target if stage else W))
    cmd = [PY, str(L / 'midm_take.py'), str(B / 'gate/cand-round20-1113a/details.csv'), str(T), str(L / 'results')]
    cmd += [str(d) for d in rawdirs]
    if stage:
        cmd += ['--stage', str(target)]
    log = W / ('cert-%s.log' % ('stage' if stage else 'final'))
    with log.open('w') as f:
        run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT)


def handoff():
    p = W / 'handoff.json'
    seen = json.loads(p.read_text()) if p.exists() else {}
    for r in rows(T / 'take.tsv'):
        n = r['n']; sc = float(r['new'])
        if n in seen and sc >= seen[n] - 1e-13:
            continue
        seen[n] = sc
        with (B / 'handoff-r22.log').open('a') as f:
            f.write('%s midm -> all: n=%s certified score %.12f gain %.3e over round20, raw kicks followed by fq on boxE, %s/%s.csv\n' % (
                time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sc, float(r['held']) - sc, T, n))
        state('RESULT n=%s score=%.12f gain_round20=%.6e' % (n, sc, float(r['held']) - sc))
    atomic(p, json.dumps(seen))



def publish_near(raw):
    """Hand improved new-design raw layouts back while they still miss the live bar."""
    import re
    import math
    sys.path.insert(0,str(L))
    import methods_lp as mlp
    seenp = W / 'near-seen.json'
    seen = json.loads(seenp.read_text()) if seenp.exists() else {}
    low = {int(x['n']):float(x['score']) for x in csv.DictReader((B/'gate/cand-round20-1113a/details.csv').open())}
    for pat in ('take-*-r21','take-*-r22'):
        for d in B.glob(pat):
            for x in rows(d/'take.tsv'):
                low[int(x['n'])]=min(low[int(x['n'])],float(x['new']))
    best = {}
    for p in raw.glob('*.csv'):
        match = re.search(r'@run_s(\d+)$',p.stem)
        if not match:
            continue
        tab = W / ('r%s.tsv' % match[1])
        if not tab.exists() or 'new-design raw start:' not in tab.read_text():
            continue
        n=int(p.stem.split('-')[0]);P=mlp.load(str(p),{n})[n]
        sc=float(mlp.side(P)/math.sqrt(n)-1)
        if not (low[n]+1e-10 < sc < low[n]+1e-4):
            continue
        if n not in best or sc<best[n][0]:
            best[n]=(sc,p,tab)
    for n,(sc,p,tab) in best.items():
        if str(n) in seen and sc>=seen[str(n)]-1e-8:
            continue
        target=T/'near'/('%d-raw-kick.csv'%n)
        tmp=target.with_suffix('.tmp');shutil.copyfile(p,tmp);tmp.replace(target)
        with (B/'handoff-r22.log').open('a') as f:
            f.write('%s midm -> all: new-design raw kick near n=%d score=%.12f margin=+%.6g over live bar; source/ancestry %s; not certified, %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),n,sc,sc-low[n],tab,target))
        state('NEAR n=%d raw score=%.12f margin=+%.6g handoff=%s' % (n,sc,sc-low[n],target))
        seen[str(n)]=sc
    atomic(seenp,json.dumps(seen))


def collect():
    local = W / 'boxE'; local.mkdir(exist_ok=True)
    run(['rsync', '-a', '--exclude', 'r*', '--exclude', 'fqin', '--exclude', 'fqout', '--exclude', '*.tmp', REMOTE, str(local) + '/'])
    run(['rsync', '-a', '--exclude', 'tmp', '--exclude', '*.tmp', REMOTE + 'run/', str(local / 'run') + '/'])
    raw = W / 'raw-in'; raw.mkdir(exist_ok=True)
    for p in (local / 'run').glob('s*/raw/*.csv'):
        shutil.copyfile(p, raw / (p.stem + '@run_' + p.parent.parent.name + '.csv'))
    publish_near(raw)
    fq = W / 'raw-fq'; fq.mkdir(exist_ok=True)
    pending = W / 'fq-pending.json'
    if pending.exists():
        result = subprocess.run(['ssh', 'boxE', 'test -e %s/fqout/DONE' % SD]).returncode
        if result == 0:
            run(['rsync', '-a', '--exclude', 'tmp', '--exclude', 'DONE', REMOTE + 'fqout/', str(fq) + '/'])
            # Keep the certified input too: fq may find no reduction.
            for p in (W / 'fq-send').glob('*.csv'):
                tag = dict(l.split('\t')[:2] for l in (W / 'fq-send/TAGS.tsv').read_text().splitlines())[p.stem]
                shutil.copyfile(p, fq / (p.stem + '-fq+' + tag + '.csv')) if not (fq / (p.stem + '-fq+' + tag + '.csv')).exists() else None
            done = json.loads((W / 'fq-done.json').read_text()) if (W / 'fq-done.json').exists() else []
            done += json.loads(pending.read_text())
            atomic(W / 'fq-done.json', json.dumps(done))
            pending.unlink()
            certify([fq], T)
            handoff()
            state('FINISH certified-file fq batch on boxE, published only after DONE')
        else:
            return
    stage = W / 'stage'; stage.mkdir(exist_ok=True)
    certify([raw], stage, stage=True)
    done = set(json.loads((W / 'fq-done.json').read_text())) if (W / 'fq-done.json').exists() else set()
    tags = dict(l.split('\t')[:2] for l in (stage / 'TAGS.tsv').read_text().splitlines())
    inputs = []
    send = W / 'fq-send'
    if send.exists():
        shutil.rmtree(send)
    send.mkdir()
    for p in stage.glob('*.csv'):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest not in done:
            shutil.copyfile(p, send / p.name)
            inputs.append(digest)
    if inputs:
        shutil.copyfile(stage / 'TAGS.tsv', send / 'TAGS.tsv')
        run(['ssh', 'boxE', 'cd %s && rm -rf fqin fqout && mkdir fqin fqout' % SD])
        run(['rsync', '-a', str(send) + '/', REMOTE + 'fqin/'])
        atomic(pending, json.dumps(inputs))
        run(['ssh', 'boxE', 'touch %s/fqin/GO' % SD])
        state('START certified-file fq batch n=%s on boxE slot1, logs=work/boxE/logs/quench.log deadline=15:20Z' % ','.join(p.stem for p in send.glob('*.csv')))
    else:
        certify([fq], T)


def main():
    mode = sys.argv[1]
    if mode == 'snap':
        snapshot()
        newdesigns()
        promote_legs()
    elif mode == 'collect':
        collect()
    elif mode in ('loop-snap', 'loop-collect'):
        state('START %s pid=%d deadline=%s logs=work/%s.log' % (mode, os.getpid(), '15:15Z' if mode == 'loop-snap' else '15:19Z', mode))
        end = END - (300 if mode == 'loop-snap' else 60)
        while time.time() < end:
            try:
                if mode == 'loop-snap':
                    snapshot()
                    newdesigns()
                    promote_legs()
                else:
                    collect()
                if mode == 'loop-snap' and (B / 'handoff-r22.log').exists():
                    lines = (B / 'handoff-r22.log').read_text().splitlines()
                    atomic(W / 'handoff-latest.txt', '\n'.join(lines[-80:]) + '\n')
                    inv = W / 'near-inventory.json'
                    if not inv.exists() or time.time() - inv.stat().st_mtime >= 600:
                        near = {d.name: [str(p) for p in (d / 'near').glob('*.csv')] for d in B.glob('take-*-r22')}
                        atomic(inv, json.dumps(near))
                        state('READ handoff-r22.log and live near folders; near starts stay unqueued (r20 0/17, r21 921/328 dry).')
            except Exception as e:
                state('ERROR %s %r' % (mode, e))
            time.sleep(60)
        state('FINISH %s' % mode)


if __name__ == '__main__':
    main()
