#!/usr/bin/env python3
"""Round 25 snapshots, collection and handoffs. No heavy search runs on the local box."""
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
csv.field_size_limit(16 * 1024 * 1024)

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r25'
W = T / 'work'
L = Path('.')
PY = str(B / 'venv/bin/python')
REMOTE = 'boxE:scratch/squares-midm/'
SD = 'scratch/squares-midm'
END = 1794624300  # 2026-11-14 02:45 UTC
SEARCH_END = END - 1800
ENV = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', MIDM_CACHE=str(W / 'floatsafe-cache.pkl'),
           MIDM_LIVE=str(B / 'take-*-r25'),
           MIDM_FREE_DETAILS='', MIDM_FREE_COUNTS='', MIDM_SNAPS=str(W), MIDM_TAGSDIR=str(W), MIDM_RAWBASE=str(W / 'raw-in'))


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
    for rnd in (25,):
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
                if not clean_declared(row.get('source','')+' '+row.get('licence','')):
                    seen.add(digest);state('REFUSE forbidden ancestry '+str(f));continue
                proof=source_evidence(f,n)
                if proof is None:continue
                if not unchanged(payload,f):
                    state('DEFER source changed while tracing '+str(f));continue
                captured=pinned_record(proof)
                if isinstance(captured,dict) and captured.get('source'):row=dict(row,source=captured['source'],licence=captured.get('licence',row.get('licence','')))
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
                priority = (0 if isfor else (.1 if n < 640 else .2)) if rnd == 25 else 3
                if rnd==25 and recent_slice(n,f.stat().st_mtime):
                    priority=-.5
                candidates.append((priority, -f.stat().st_mtime, n, sc, d, f, row, digest,payload,proof))
    for priority, stamp, n, sc, d, f, row, digest,payload,proof in sorted(candidates, key=lambda x:x[:2]):
        if digest in seen:
            continue
        k = next_key(db)
        rd = W / ('r%d' % k); rd.mkdir(exist_ok=True)
        (rd/f.name).write_bytes(payload)
        source = '%s; exact start %s; %s/take.tsv; held ancestry: results/round23-best-2026-11-13.tsv; pinned ancestry %s' % (row.get('source',''), f, d, proof)
        atomic(W / ('r%d.tsv'%k), 'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\t%s\t%s\t%s\t%g\n' % (n,sc,d.name,source.replace('\t',' '),row.get('licence','').replace('\t',' '),priority))
        j = dict(k=k,n=n,sub='r%d/%d.csv'%(k,n),seed=n+2300,seconds=150 if n<700 else (225 if n<800 else 450),sigma=.04,priority=priority,created=-stamp,leg=0,source=d.name,slot=1)
        atomic(W/'jobs'/('%d-%d.json'%(k,n)),json.dumps(j))
        transfer.append(str(rd));seen.add(digest);db['previous'].append([n,sc,d.name])
        state('QUEUE boxE slot1 k=%d n=%d source=%s priority=%g deadline02:45Z logs=work/boxE/logs/worker.log'%(k,n,d.name,priority))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE])
        run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])
    db['seen'] = sorted(seen);atomic(dbp,json.dumps(db))




def raw_seconds(n,score,bar):
    if n>=640 and score>bar+2e-5:
        return 75
    return 150 if n<700 else (225 if n<800 else 450)


def newdesigns():
    """Explicit new-design handoffs override the exclusion of old near layouts."""
    hand = B / 'handoff-r25.log'
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
    for line in reversed(hand.read_text().splitlines()):
        key = hashlib.sha256(line.encode()).hexdigest()
        # A new generation of strip or rounded-band layouts changes the old near-start experiment.
        if not ('midm' in line or '-> all:' in line or 'new build n=' in line):
            continue
        for name in re.findall(r'$SCRATCH/bounties-squares/[^ ,;]+\.csv', line):
            f = Path(name.rstrip(').'))
            if '/work/interior/' in str(f):
                continue  # A component library is not a whole target layout.
            if f.parent == T or T in f.parents:
                continue
            if f.parent.name.startswith('take-') and f.parent.name.endswith('-r25'):
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
            d = next((p for p in f.parents if p.name.startswith('take-') and p.name.endswith('-r25')), None)
            if d is None:
                continue
            metadata=[Path(str(f)+'.json'),f.with_suffix('.json'),d/'take.tsv',d/'near/near.tsv',d/'work/sources-all.tsv']
            stamps=[(str(p),p.stat().st_mtime_ns) for p in metadata if p.exists()]
            casekey=hashlib.sha256((key+str(f)+digest+repr(stamps)).encode()).hexdigest()
            if casekey in handled:continue
            proof=raw_provenance(f,line)
            if proof is None:
                handled.add(casekey)
                state('DEFER unresolved raw source until producer metadata changes or a new handoff: '+str(f))
                continue
            if not unchanged(payload,f):
                state('DEFER raw source changed while tracing '+str(f));continue
            handled.add(casekey)
            k = next_key(db)
            rd = W / ('r%d' % k); rd.mkdir(exist_ok=True)
            (rd/('%d.csv'%n)).write_bytes(payload)
            notice,licence = raw_notice(proof)
            source = 'new-design raw start: %s; handoff: %s; ancestry: %s; recorded source: %s' % (f,line.replace('\t',' '),proof,notice)
            table = 'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\t%s\t%s\t%s\t1\n' % (n, sc, d.name, source, licence+'; pinned ancestry '+proof)
            atomic(W / ('r%d.tsv' % k), table)
            j = dict(k=k, n=n, sub='r%d/%d.csv' % (k,n), seed=n+6200, seconds=raw_seconds(n,sc,bars[n]), sigma=0.04, slot=1, priority=-.4 if recent_slice(n,f.stat().st_mtime) else (1.25 if n<640 else 1.75), created=f.stat().st_mtime, leg=0, source=d.name, raw_design=True)
            atomic(W / 'jobs' / ('%d-%d.json' % (k,n)), json.dumps(j))
            transfer.append(str(rd))
            seen.add(digest)
            db['previous'].append([n,sc,d.name])
            state('QUEUE NEW-DESIGN exception n=%d k=%d raw=%s; old near failures used old geometry; deadline02:45Z' % (n,k,f))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE])
        run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])
    db['seen'] = sorted(seen)
    db['design_lines'] = sorted(handled)
    atomic(dbp, json.dumps(db))



def leg_priority(j):
    if j.get('owed_leg'):
        return -.5 if j['n'] in (693,416) else 2.5
    return .4 if j.get('public') else .5


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
    state('START reserved frozen backlog window n%d: closest remaining score gap%+.6g, budget%gs. Prior round23 backlog869 gained6.7e-5. boxE slot1 only; deadline02:45Z.'%(job['n'],gap,job['seconds']))


def certify(rawdirs, target, stage=False):
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import revoke25
    revoke25.apply(sys.modules[__name__])
    env = dict(ENV, MIDM_TAGSDIR=str(target if stage else W))
    cmd = [PY, '-I', str(L / 'midm_take.py'), str(W / 'base-details.csv'), str(T), str(L / 'results')]
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
        with (B / 'handoff-r25.log').open('a') as f:
            f.write('%s midm -> all: n=%s certified score %.12f gain %.3e over round23, raw kicks followed by fq on boxE, %s/%s.csv\n' % (
                time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sc, float(r['held']) - sc, T, n))
        state('RESULT n=%s score=%.12f gain_round23=%.6e' % (n, sc, float(r['held']) - sc))
    atomic(p, json.dumps(seen))



def publish_near(raw):
    """Hand improved new-design raw layouts back while they still miss the live bar."""
    import re
    import math
    sys.path.insert(0,str(L))
    import methods_lp as mlp
    seenp = W / 'near-seen.json'
    seen = json.loads(seenp.read_text()) if seenp.exists() else {}
    low = live_bars()
    for pat in ('take-*-r25',):
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
        target=T/'near'/('%d-raw-kick-%s-%s.csv'%(n,tab.stem,hashlib.sha256(p.read_bytes()).hexdigest()[:12]))
        tmp=target.with_suffix('.tmp');shutil.copyfile(p,tmp);tmp.replace(target)
        parent=rows(tab)[0]
        atomic(Path(str(target)+'.json'),json.dumps(dict(n=n,source_key=int(tab.stem[1:]),source='midm raw kick; '+parent['source'],licence=parent['licence'],input_sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2))
        proof=captured_proof(parent['source'])
        if proof:
            origin=dict(snapshot_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),verified_ancestry=True,ancestry=json.loads(Path(proof).read_text()),method='midm raw kick of pinned input')
            atomic(Path(str(target)+'.origin.json'),json.dumps(origin))
        with (B/'handoff-r25.log').open('a') as f:
            f.write('%s midm -> all: new-design raw kick near n=%d score=%.12f margin=+%.6g over live bar; source/ancestry %s; not certified, %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),n,sc,sc-low[n],tab,target))
        state('NEAR n=%d raw score=%.12f margin=+%.6g handoff=%s' % (n,sc,sc-low[n],target))
        seen[str(n)]=sc
    atomic(seenp,json.dumps(seen))



def collect_raw(local,raw,revoked):
    for p in (local/'run').glob('s*/raw/*.csv'):
        key=int(p.parent.parent.name[1:])
        if key in revoked:continue
        target=raw/(p.stem+'@run_'+p.parent.parent.name+'.csv')
        if target.exists() and target.stat().st_size==p.stat().st_size:continue
        temporary=target.with_suffix('.tmp');shutil.copyfile(p,temporary);temporary.replace(target)

def collect(final=False):
    local = W / 'boxE'; local.mkdir(exist_ok=True)
    run(['rsync', '-a', '--exclude', 'r*', '--exclude', 'fqin', '--exclude', 'fqout', '--exclude', '*.tmp', REMOTE, str(local) + '/'])
    run(['rsync', '-a', '--exclude', 'tmp', '--exclude', '*.tmp', REMOTE + 'run/', str(local / 'run') + '/'])
    raw = W / 'raw-in'; raw.mkdir(exist_ok=True)
    revoked=set(json.loads((W/'revoked-keys.json').read_text())) if (W/'revoked-keys.json').exists() else set()
    collect_raw(local,raw,revoked)
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import revoke25
    revoke25.apply(sys.modules[__name__])
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
    if final or time.time() >= END - 90:
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
        if (W/'fq-batch').exists():
            shutil.rmtree(W/'fq-batch')
        run(['ssh', 'boxE', 'cd %s && rm -rf fqin fqout && mkdir fqin fqout' % SD])
        run(['rsync', '-a', str(send) + '/', REMOTE + 'fqin/'])
        atomic(pending, json.dumps(inputs))
        run(['ssh', 'boxE', 'touch %s/fqin/GO' % SD])
        state('START certified-file fq batch n=%s on boxE slot1, logs=work/boxE/logs/quench.log deadline=02:45Z' % ','.join(p.stem for p in send.glob('*.csv')))
    else:
        certify([fq], T)



def unchanged(payload,path):
    try:return hashlib.sha256(payload).digest()==hashlib.sha256(path.read_bytes()).digest()
    except OSError:return False


def captured_proof(source):
    pattern=r'$SCRATCH/bounties-squares/take-midm-r25/work/provenance/[0-9a-f-]+\.json'
    raw=re.search(r'; ancestry: ('+pattern+')',source)
    if source.startswith('new-design raw start:') and raw:return raw[1]
    matches=re.findall(r'; pinned ancestry ('+pattern+')',source)
    return matches[-1] if matches else None


def pinned_record(proof):
    data=json.loads(Path(proof).read_text())
    if 'fallback' in data:return data['fallback']
    return data.get('record',data)


def raw_provenance(f,line):
    n=int(next(csv.DictReader(f.open()))['n'])
    proof=source_evidence(f,n)
    if not proof:return None
    record=pinned_record(proof)
    return proof



def raw_notice(proof):
    sys.path.insert(0,str(L/'tools'))
    from harvest_follow import provenance_text
    record = pinned_record(proof)
    notices = set()
    def collect(v):
        if isinstance(v, dict):
            for key, value in v.items():
                if key in ('licence','license','licences','licenses','donor_licence') and isinstance(value, str):
                    notices.add(value)
                elif isinstance(value, (dict,list)):
                    collect(value)
        elif isinstance(v,list):
            for value in v:collect(value)
    collect(record)
    source = record.get('source') if isinstance(record,dict) else None
    if not isinstance(source,str):source=provenance_text(record)
    return source.replace('\t',' ').replace('\n',' '), '; '.join(sorted(notices)) or 'own construction on recorded licensed parents; '+proof

def public_starts():
    dbp=W/'queue-state.json';db=json.loads(dbp.read_text());seen=set(db['seen'])
    transfer=[]
    publicbase=B/'take-harvest-r25/work/public/starts'
    publicrows=[]
    for f in publicbase.glob('*.csv'):
        side=Path(str(f)+'.json')
        if side.exists():publicrows.append((f.parent,json.loads(side.read_text())))
    for d in (B/'take-harvest-r25/work').glob('**/starts/*'):
        for row in rows(d/'take.tsv'):publicrows.append((d,row))
    for d,row in publicrows:
        if True:
            n=int(row['n']);f=d/('%d.csv'%n)
            if not f.exists() or not clean_declared(row.get('source','')+' '+row.get('licence','')):continue
            payload=f.read_bytes();digest=hashlib.sha256(payload).hexdigest()
            if digest in seen:
                for jobpath in (W/'jobs').glob('*.json'):
                    job=json.loads(jobpath.read_text())
                    start=W/job['sub']
                    if job.get('leg') or not start.exists() or hashlib.sha256(start.read_bytes()).hexdigest()!=digest:continue
                    if job.get('public'):continue
                    job.update(public=True,slot=2,priority=.25)
                    atomic(jobpath,json.dumps(job));run(['rsync','-a',str(jobpath),REMOTE+'jobs/'])
                    state('PROMOTE fresh public n%d to reserved boxE slot2 k%d'%(n,job['k']))
                continue
            proof=source_evidence(f,n)
            if proof is None or not unchanged(payload,f):continue
            captured=pinned_record(proof)
            if isinstance(captured,dict) and captured.get('source'):row=dict(row,source=captured['source'],licence=captured.get('licence',row.get('licence','')))
            actual=packing_score(payload,n);sc=float(row['new'])
            if abs(actual-sc)>5e-11:continue
            k=next_key(db);rd=W/('r%d'%k);rd.mkdir();(rd/f.name).write_bytes(payload)
            source=row['source']+'; exact public start '+str(f)+'; '+str(d/'take.tsv')
            atomic(W/('r%d.tsv'%k),'n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\ttake-harvest-r25\t%s\t%s\t.25\n'%(n,min(actual,sc),source,row['licence']))
            j=dict(k=k,n=n,sub='r%d/%d.csv'%(k,n),seed=n+2400,seconds=150 if n<700 else (225 if n<800 else 450),sigma=.04,priority=.25,created=f.stat().st_mtime,leg=0,source='take-harvest-r25',public=True,slot=2)
            atomic(W/'jobs'/('%d-%d.json'%(k,n)),json.dumps(j));transfer.append(str(rd));seen.add(digest);db['previous'].append([n,sc,'take-harvest-r25'])
            state('QUEUE fresh public n=%d k=%d source=%s deadline02:45Z'%(n,k,row['source']))
    db['seen']=sorted(seen);atomic(dbp,json.dumps(db))
    if transfer:
        run(['rsync','-a']+transfer+[REMOTE]);run(['rsync','-a',str(W/'jobs')+'/',REMOTE+'jobs/'])


def main():
    update_base()
    mode = sys.argv[1]
    if mode == 'snap':
        public_starts()
        snapshot()
        newdesigns()
        promote_legs()
    elif mode == 'collect':
        collect()
    elif mode in ('loop-snap', 'loop-collect'):
        state('START %s pid=%d deadline=%s logs=work/%s.log' % (mode, os.getpid(), '02:45Z' if mode == 'loop-snap' else '02:44Z', mode))
        loaded=Path(__file__).stat().st_mtime_ns
        end = END - (300 if mode == 'loop-snap' else 60)
        while time.time() < end:
            try:
                update_base()
                if mode == 'loop-snap':
                    sys.path.insert(0,str(Path(__file__).resolve().parent))
                    import revoke25
                    revoke25.apply(sys.modules[__name__])
                    if time.time() < SEARCH_END:
                        public_starts()
                        snapshot()
                        newdesigns()
                        promote_legs()
                    sys.path.insert(0,str(Path(__file__).resolve().parent))
                    import order24
                    order24.apply(sys.modules[__name__])
                    prioritize_raw_winners()
                    # Round 20 backlog stays closed.
                else:
                    collect()
                if mode == 'loop-snap' and (B / 'handoff-r25.log').exists():
                    lines = (B / 'handoff-r25.log').read_text().splitlines()
                    atomic(W / 'handoff-latest.txt', '\n'.join(lines[-80:]) + '\n')
                    inv = W / 'near-inventory.json'
                    if not inv.exists() or time.time() - inv.stat().st_mtime >= 600:
                        near = {d.name: [str(p) for p in (d / 'near').glob('*.csv')] for d in B.glob('take-*-r25')}
                        atomic(inv, json.dumps(near))
                        state('READ handoff-r25.log and live near folders; new-design CSV handoffs queued, old near repeats skipped (r20 0/17).')
            except Exception as e:
                state('ERROR %s %r' % (mode, e))
            if Path(__file__).stat().st_mtime_ns!=loaded:
                os.execv(PY,[PY,str(Path(__file__).resolve()),mode])
            time.sleep(60)
        state('FINISH %s' % mode)




def clean_declared(text):
    import sources25
    return sources25.clean_text(text)


def source_evidence(f,n):
    import sources25
    return sources25.capture(f,n)


def update_base():
    import sources25
    sources25.update_base()


def live_bars():
    update_base()
    low={int(x['n']):float(x['score']) for x in csv.DictReader((W/'base-details.csv').open())}
    for d in B.glob('take-*-r25'):
        for row in rows(d/'take.tsv'):
            if clean_declared(row.get('source','')+' '+row.get('licence','')):
                low[int(row['n'])]=min(low[int(row['n'])],float(row['new']))
    return low


def prioritize_raw_winners():
    bars=live_bars();changed=[]
    for p in (W/'jobs').glob('*.json'):
        j=json.loads(p.read_text())
        if not j.get('raw_design') or j.get('leg') or (W/'cancel'/p.stem).exists():continue
        if (W/'boxE/claims'/p.stem).exists():continue
        table=rows(W/('r%d.tsv'%j['k']))
        if table and float(table[0]['score'])<bars[j['n']]-1e-10 and j['priority']!=.3:
            j['priority']=.3;atomic(p,json.dumps(j));changed.append(p)
    if changed:
        run(['rsync','-a']+[str(p) for p in changed]+[REMOTE+'jobs/'])
        state('ORDER %d fresh raw builds below live bar promoted ahead of continuations and above-bar near starts'%len(changed))


if __name__ == '__main__':
    main()
