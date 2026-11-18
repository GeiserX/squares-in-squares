#!/usr/bin/env python3
"""Round 23 snapshots, collection and handoffs. No heavy search runs on the local box."""
import csv
import glob
import hashlib
import json
import io
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r23'
W = T / 'work'
L = Path('.')
PY = str(B / 'venv/bin/python')
REMOTE = 'boxE:scratch/squares-midm/'
SD = 'scratch/squares-midm'
END = 1794594600  # 2026-11-13 18:30 UTC
ENV = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', MIDM_CACHE=str(W / 'floatsafe-cache.pkl'),
           MIDM_LIVE=str(B / 'take-*-r22') + ' ' + str(B / 'take-*-r23'),
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


def next_key(db):
    key=int(db['k'])
    while (W/('r%d'%key)).exists() or (W/('r%d.tsv'%key)).exists():
        key+=1
    db['k']=key+1
    return key


def recent_slice(n, created):
    return 257<=n<=440 and created>=time.time()-600


def certified_backup_tag(tag):
    stem,separator,where=tag.partition('@')
    return stem+'-certified'+separator+where


def packing_score(payload, n):
    data=list(csv.DictReader(io.StringIO(payload.decode())))
    if len(data)!=n or any(int(row['n'])!=n for row in data):
        raise ValueError('incomplete packing')
    lo=[math.inf,math.inf];hi=[-math.inf,-math.inf]
    for row in data:
        angle=float(row['angle']);half=.5*(abs(math.cos(angle))+abs(math.sin(angle)))
        for axis,key in enumerate(('x','y')):
            value=float(row[key]);lo[axis]=min(lo[axis],value-half);hi[axis]=max(hi[axis],value+half)
    score=max(hi[i]-lo[i] for i in (0,1))/math.sqrt(n)-1
    if not math.isfinite(score):raise ValueError('nonfinite packing')
    return score


def snapshot():
    dbp = W / 'queue-state.json'
    db = json.loads(dbp.read_text())
    seen = set(db['seen'])
    bars = live_bars()
    transfer = []
    candidates = []
    for rnd in (22, 23):
        for d in B.glob('take-*-r%d' % rnd):
            if d == T or d.name.startswith('take-assemble'):
                continue
            lane = d.name[5:-4]
            for row in rows(d / 'take.tsv'):
                try:
                    n, sc = int(row['n']), float(row['new'])
                    f = d / ('%d.csv' % n)
                    payload=f.read_bytes()
                    digest = hashlib.sha256(payload).hexdigest()
                    actual=packing_score(payload,n)
                    if abs(actual-sc)>5e-11 or f.stat().st_mtime_ns>(d/'take.tsv').stat().st_mtime_ns:
                        continue
                    sc=min(sc,actual)
                except (OSError, KeyError, ValueError):
                    continue
                if digest in seen:
                    continue
                head = row.get('source', '').lower()[:110]
                kicked = lane in ('midm', 'invent', 'classfill') or head.startswith(('fq kick', 'fq quench of fq kick', 'lkick', 'kick', 'invent_rest'))
                # Preserve near-to-bar and tiny improvements. Older rows clearly
                # superseded by a different layout have a separate backlog.
                if kicked or (rnd == 22 and sc > bars[n] + 1e-6):
                    seen.add(digest)
                    continue
                if any(pn == n and pd == d.name and abs(ps-sc) < 1e-10 for pn,ps,pd in db['previous']):
                    seen.add(digest)
                    continue
                isfor = lane == 'forensics' or (lane in ('harvest','polish') and re.match(r'^(?:fq quench of )*forensics_rect[.]py', head) is not None)
                priority = (0 if isfor else (1 if n < 640 else 1.5)) if rnd == 23 else 3
                if rnd==23 and recent_slice(n,f.stat().st_mtime):
                    priority=-.5
                candidates.append((priority, -f.stat().st_mtime, n, sc, d, f, row, digest,payload))
    for priority, stamp, n, sc, d, f, row, digest,payload in sorted(candidates, key=lambda x:x[:2]):
        if digest in seen:
            continue
        k = next_key(db)
        rd = W / ('r%d' % k); rd.mkdir(exist_ok=True)
        (rd/f.name).write_bytes(payload)
        source = '%s; %s/take.tsv; held ancestry: results/round21-best-2026-11-13.tsv' % (row.get('source',''), d)
        atomic(W / ('r%d.tsv'%k), 'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\t%s\t%s\t%s\t%g\n' % (n,sc,d.name,source.replace('\t',' '),row.get('licence','').replace('\t',' '),priority))
        j = dict(k=k,n=n,sub='r%d/%d.csv'%(k,n),seed=n+2300,seconds=150 if n<700 else (225 if n<800 else 450),sigma=.04,priority=priority,created=-stamp,leg=0,source=d.name,slot=1)
        atomic(W/'jobs'/('%d-%d.json'%(k,n)),json.dumps(j))
        transfer.append(str(rd));seen.add(digest);db['previous'].append([n,sc,d.name])
        state('QUEUE boxE slot1 k=%d n=%d source=%s priority=%g deadline18:30Z logs=work/boxE/logs/worker.log'%(k,n,d.name,priority))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE])
        run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])
    db['seen'] = sorted(seen);atomic(dbp,json.dumps(db))



def live_bars():
    low={int(x['n']):float(x['score']) for x in csv.DictReader((B/'gate/cand-round21-1113a/details.csv').open())}
    for pat in ('take-*-r22','take-*-r23'):
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
    hand = B / 'handoff-r23.log'
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
        if not ('midm' in line or '-> all:' in line or 'new build n=' in line):
            continue
        for name in re.findall(r'$SCRATCH/bounties-squares/[^ ,;]+\.csv', line):
            f = Path(name.rstrip(').'))
            if '/work/interior/' in str(f):
                continue  # A component library is not a whole target layout.
            if f.parent == T or T in f.parents:
                continue
            if f.parent.name.startswith('take-') and f.parent.name.endswith('-r23'):
                continue  # Certified files use snapshot provenance and kick-history checks.
            if not f.exists():
                continue
            try:
                payload=f.read_bytes()
                digest=hashlib.sha256(payload).hexdigest()
                if digest in seen:
                    continue
                n=int(next(csv.DictReader(io.StringIO(payload.decode())))['n'])
                sc=packing_score(payload,n)
            except (OSError,KeyError,ValueError,StopIteration):
                state('SKIP incomplete handoff CSV '+str(f))
                continue
            d = next((p for p in f.parents if p.name.startswith('take-') and p.name.endswith('-r23')), None)
            if d is None:
                continue
            handled.add(key)
            k = next_key(db)
            rd = W / ('r%d' % k); rd.mkdir(exist_ok=True)
            (rd/('%d.csv'%n)).write_bytes(payload)
            source = 'new-design raw start: %s; handoff: %s; %s/take.tsv and results/round21-best-2026-11-13.tsv give ancestry' % (f, line.replace('\t', ' '), d.name)
            table = 'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\t%s\t%s\t%s\t1\n' % (n, sc, d.name, source, 'ours on the named donor; its lane take.tsv and round20 source table give upstream licences')
            atomic(W / ('r%d.tsv' % k), table)
            j = dict(k=k, n=n, sub='r%d/%d.csv' % (k,n), seed=n+6200, seconds=raw_seconds(n,sc,bars[n]), sigma=0.04, slot=1, priority=-.4 if recent_slice(n,f.stat().st_mtime) else (1.25 if n<640 else 1.75), created=f.stat().st_mtime, leg=0, source=d.name, raw_design=True)
            atomic(W / 'jobs' / ('%d-%d.json' % (k,n)), json.dumps(j))
            transfer.append(str(rd))
            seen.add(digest)
            db['previous'].append([n,sc,d.name])
            state('QUEUE NEW-DESIGN exception n=%d k=%d raw=%s; old near failures used old geometry; deadline18:30Z' % (n,k,f))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE])
        run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])
    db['seen'] = sorted(seen)
    db['design_lines'] = sorted(handled)
    atomic(dbp, json.dumps(db))



def leg_priority(j):
    if j.get('owed_leg'):
        return -.5 if j['n'] in (693,416) else 2.5
    return (0.4 if j.get('public') else 0.5) if j['n']<640 else 1.6


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
        if (W/'boxE/done'/p.name).exists():
            continue
        j = json.loads(p.read_text())
        tab=W/('r%d.tsv'%j['k'])
        source=W/'boxE'/j['sub']
        if source.exists():
            P=mlp.load(str(source),{j['n']})[j['n']]
            sc=float(mlp.side(P)/math.sqrt(j['n'])-1)
            margin=2e-5 if tab.exists() and 'new-design raw start:' in tab.read_text() else 1e-6
            if sc>bars[j['n']]+margin:
                (W/'cancel').mkdir(exist_ok=True)
                marker=W/'cancel'/p.stem
                if not marker.exists():
                    marker.touch();state('CANCEL obsolete raw leg '+p.stem+'; over live bar by %.6g score'%(sc-bars[j['n']]))
                canceled.append(marker)
                continue
        j['slot']=1
        j['priority'] = leg_priority(j)
        atomic(changed / p.name, json.dumps(j))
    if canceled:
        run(['rsync','-a']+[str(p) for p in canceled]+[REMOTE+'cancel/'])
    if list(changed.glob('*.json')):
        run(['rsync','-a',str(changed)+'/',REMOTE+'jobs/'])


def backlog_window():
    flag=W/'backlog-window.json'
    if flag.exists():
        data=json.loads(flag.read_text())
        finished=W/'boxE/done'/data['job_file']
        if finished.exists() and not data.get('finished'):
            job=json.loads(finished.read_text());data['finished']=True
            atomic(flag,json.dumps(data))
            state('FINISH reserved frozen backlog n%d: %.1fs, raw gain%.6g; certification and quench remain separate'%(job['n'],job.get('elapsed',0),job.get('gain',0)))
        return
    if time.time()<1794591000:  # 17:30 UTC
        return
    bars=live_bars();options=[]
    for path in (W/'jobs').glob('*.json'):
        job=json.loads(path.read_text())
        if not job.get('backlog') or job.get('leg') or (W/'boxE/done'/path.name).exists():
            continue
        if (W/'cancel'/path.stem).exists():
            continue
        source=rows(W/('r%d.tsv'%job['k']))[0]
        gap=float(source['score'])-bars[job['n']]
        options.append((max(0,gap),job['seconds'],job['n'],path,job,gap))
    if not options:
        return
    _,_,_,path,job,gap=min(options,key=lambda x:x[:3])
    job['priority']=-.25;atomic(path,json.dumps(job))
    run(['rsync','-a',str(path),REMOTE+'jobs/'])
    atomic(flag,json.dumps(dict(job_file=path.name,n=job['n'],gap=gap,finished=False)))
    state('START reserved frozen backlog window n%d: closest remaining score gap%+.6g, budget%gs. Prior round21 backlog869 gained6.7e-5. boxE slot1 only; deadline18:30Z.'%(job['n'],gap,job['seconds']))


def certify(rawdirs, target, stage=False):
    env = dict(ENV, MIDM_TAGSDIR=str(target if stage else W))
    cmd = [PY, str(L / 'midm_take.py'), str(B / 'gate/cand-round21-1113a/details.csv'), str(T), str(L / 'results')]
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
        with (B / 'handoff-r23.log').open('a') as f:
            f.write('%s midm -> all: n=%s certified score %.12f gain %.3e over round21, raw kicks followed by fq on boxE, %s/%s.csv\n' % (
                time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sc, float(r['held']) - sc, T, n))
        state('RESULT n=%s score=%.12f gain_round21=%.6e' % (n, sc, float(r['held']) - sc))
    atomic(p, json.dumps(seen))



def publish_near(raw):
    """Hand improved new-design raw layouts back while they still miss the live bar."""
    import re
    import math
    sys.path.insert(0,str(L))
    import methods_lp as mlp
    seenp = W / 'near-seen.json'
    seen = json.loads(seenp.read_text()) if seenp.exists() else {}
    low = {int(x['n']):float(x['score']) for x in csv.DictReader((B/'gate/cand-round21-1113a/details.csv').open())}
    for pat in ('take-*-r22','take-*-r23'):
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
        with (B/'handoff-r23.log').open('a') as f:
            f.write('%s midm -> all: new-design raw kick near n=%d score=%.12f margin=+%.6g over live bar; source/ancestry %s; not certified, %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),n,sc,sc-low[n],tab,target))
        state('NEAR n=%d raw score=%.12f margin=+%.6g handoff=%s' % (n,sc,sc-low[n],target))
        seen[str(n)]=sc
    atomic(seenp,json.dumps(seen))


def collect(final=False):
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
        batch = W / 'fq-batch'; batch.mkdir(exist_ok=True)
        run(['rsync','-a','--exclude','tmp','--exclude','*.tmp',REMOTE+'fqout/',str(batch)+'/'])
        is_done = (batch/'DONE').exists()
        done = set(json.loads((W/'fq-done.json').read_text())) if (W/'fq-done.json').exists() else set()
        tags = dict(l.split('\t')[:2] for l in (W/'fq-send/TAGS.tsv').read_text().splitlines())
        added = []
        for p in (W/'fq-send').glob('*.csv'):
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            marker = batch/(p.stem+'.done')
            complete = (marker.exists() and marker.read_text().strip()==digest) if (batch/'PER_FILE').exists() else is_done
            if not complete or digest in done:
                continue
            tag=tags[p.stem]
            backup=fq/(p.stem+'-fq+'+certified_backup_tag(tag)+'.csv')
            temporary=backup.with_suffix('.tmp');shutil.copyfile(p,temporary);temporary.replace(backup)
            target=fq/(p.stem+'-fq+'+tag+'.csv')
            improved=batch/target.name
            temporary=target.with_suffix('.tmp')
            shutil.copyfile(improved if improved.exists() else p,temporary)
            temporary.replace(target)
            done.add(digest);added.append(p.stem)
        if added:
            atomic(W/'fq-done.json',json.dumps(sorted(done)))
            certify([fq], T);handoff()
            state('FINISH certified-file fq per-file drain n='+','.join(added)+' on boxE; completion digests matched')
        if not set(json.loads(pending.read_text())).issubset(done):
            return
        if not final:
            # The worker removes GO after it returns from the quench child.
            # Keep the batch until that parent releases its input directory.
            released=subprocess.run(['ssh','boxE','test ! -e %s/fqin/GO'%SD]).returncode==0
            if not released:
                return
        pending.unlink()
        state('FINISH certified-file fq batch on boxE, all inputs drained')
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
        if (W/'fq-batch').exists():
            shutil.rmtree(W/'fq-batch')
        run(['ssh', 'boxE', 'cd %s && rm -rf fqin fqout && mkdir fqin fqout' % SD])
        run(['rsync', '-a', str(send) + '/', REMOTE + 'fqin/'])
        atomic(pending, json.dumps(inputs))
        run(['ssh', 'boxE', 'touch %s/fqin/GO' % SD])
        state('START certified-file fq batch n=%s on boxE slot1, logs=work/boxE/logs/quench.log deadline=18:30Z' % ','.join(p.stem for p in send.glob('*.csv')))
    else:
        certify([fq], T)


def public_starts():
    dbp=W/'queue-state.json';db=json.loads(dbp.read_text());seen=set(db['seen'])
    transfer=[]
    old=B/'take-midm-r22/work'
    wanted={int(x['n']) for x in rows(old/'public-pending.tsv')}
    starts=[]
    for n in wanted:
        p=old/('r%d.tsv'%(2000+n))
        if p.exists():
            row=rows(p)[0];starts.append((old/('r%d'% (2000+n))/('%d.csv'%n),row,n,True))
    for d in (B/'take-harvest-r23/work').glob('**/starts/*'):
        for row in rows(d/'take.tsv'):
            n=int(row['n']);row=dict(row,score=row.get('new'),dir='take-harvest-r23')
            starts.append((d/('%d.csv'%n),row,n,False))
    for f,row,n,old_public in sorted(starts,key=lambda x:(not x[3],x[2])):
        if not f.exists():continue
        payload=f.read_bytes();digest=hashlib.sha256(payload).hexdigest()
        actual=packing_score(payload,n)
        if abs(actual-float(row['score']))>5e-11:continue
        row=dict(row,score=repr(min(actual,float(row['score']))))
        if digest in seen:continue
        k=next_key(db);rd=W/('r%d'%k);rd.mkdir(exist_ok=True);(rd/f.name).write_bytes(payload)
        atomic(W/('r%d.tsv'%k),'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%s\t%s\t%s; exact source %s\t%s\t.25\n'%(n,row['score'],row['dir'],row['source'],f,row['licence']))
        j=dict(k=k,n=n,sub='r%d/%d.csv'%(k,n),seed=n+2300,seconds=150 if n<700 else (225 if n<800 else 450),sigma=.04,priority=.25 if n<700 else (.5 if n<800 else .75),created=f.stat().st_mtime,leg=0,source=row['dir'],public=True,slot=2)
        atomic(W/'jobs'/('%d-%d.json'%(k,n)),json.dumps(j));transfer.append(str(rd));seen.add(digest);db['previous'].append([n,float(row['score']),row['dir']])
        state('QUEUE public boxE slot2 k=%d n=%d source=%s deadline18:30Z logs=work/boxE/logs/worker.log'%(k,n,row['source']))
    db['seen']=sorted(seen);atomic(dbp,json.dumps(db))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE]);run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])


def main():
    mode = sys.argv[1]
    if mode == 'snap':
        public_starts()
        snapshot()
        newdesigns()
        promote_legs()
    elif mode == 'collect':
        collect()
    elif mode in ('loop-snap', 'loop-collect'):
        state('START %s pid=%d deadline=%s logs=work/%s.log' % (mode, os.getpid(), '18:25Z' if mode == 'loop-snap' else '18:29Z', mode))
        end = END - (300 if mode == 'loop-snap' else 60)
        while time.time() < end:
            try:
                if mode == 'loop-snap':
                    public_starts()
                    snapshot()
                    newdesigns()
                    promote_legs()
                    backlog_window()
                else:
                    collect()
                if mode == 'loop-snap' and (B / 'handoff-r23.log').exists():
                    lines = (B / 'handoff-r23.log').read_text().splitlines()
                    atomic(W / 'handoff-latest.txt', '\n'.join(lines[-80:]) + '\n')
                    inv = W / 'near-inventory.json'
                    if not inv.exists() or time.time() - inv.stat().st_mtime >= 600:
                        near = {d.name: [str(p) for p in (d / 'near').glob('*.csv')] for d in B.glob('take-*-r23')}
                        atomic(inv, json.dumps(near))
                        state('READ handoff-r23.log and live near folders; new-design CSV handoffs queued, old near repeats skipped (r20 0/17).')
            except Exception as e:
                state('ERROR %s %r' % (mode, e))
            time.sleep(60)
        state('FINISH %s' % mode)


if __name__ == '__main__':
    main()
