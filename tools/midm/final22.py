#!/usr/bin/env python3
"""Finish round 22 even if its interactive session ends. All search stops by 15:20Z."""
import csv
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import round22 as r

STOP = 1794583020  # 15:17 UTC: leave three minutes for the last certified-file quench.
HARD = 1794583200
REPO = '$PRIVATE_REPO'


def stop_local():
    output = subprocess.check_output(['ps', '-Ao', 'pid=,ppid=,command='], text=True)
    ps = {}
    roots = set()
    for line in output.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        pid, parent, command = int(parts[0]), int(parts[1]), parts[2]
        ps[pid] = parent
        argv = command.split()
        module = str(r.L / 'tools/midm/round22.py')
        monitor = str(r.W / 'monitor.py')
        if (len(argv) in (3,4) and 'python' in Path(argv[0]).name.lower() and argv[-2] == module and argv[-1] in ('loop-snap', 'loop-collect')) or (len(argv) == 2 and argv[1] == monitor):
            roots.add(pid)
    while True:
        new = {pid for pid, parent in ps.items() if parent in roots} - roots
        if not new:
            break
        roots |= new
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in roots:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(0.2)
    r.state('STOP local snapshot, collector and monitor trees: %s' % sorted(roots))


def remote_stop():
    code = '''import os,subprocess,signal,time,pathlib
D=pathlib.Path.home()/'scratch/squares-midm'
roots=set(map(int,(D/'workers.pids').read_text().split()))
ps={}
for l in subprocess.check_output(['ps','-Ao','pid=,ppid='],text=True).splitlines():
 a,b=map(int,l.split());ps[a]=b
while True:
 new={p for p,q in ps.items() if q in roots}-roots
 if not new:break
 roots|=new
for sig in (signal.SIGTERM,signal.SIGKILL):
 for p in roots:
  try:os.kill(p,sig)
  except ProcessLookupError:pass
 time.sleep(.2)
print('stopped own remote tree',sorted(roots))
'''
    r.run(['ssh', 'boxE', '$SCRATCH/squares-base/venv/bin/python', '-'], input=code, text=True)


def last_collect():
    # There are no kick workers now. Quench pending certified files on the free first slot.
    for _ in range(4):
        r.collect()
        if not (r.W / 'fq-pending.json').exists():
            return
        left = int(HARD - time.time() - 5)
        if left <= 0:
            break
        code = '''import pathlib,subprocess,os,signal,sys,time
D=pathlib.Path.home()/'scratch/squares-midm';os.chdir(D)
if (D/'fqout/DONE').exists():sys.exit(0)
if time.time()>=1794583198:sys.exit(3)
with open('logs/final-quench.log','a') as out:
 p=subprocess.Popen(['nice','-n','5',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'),'midm_fqonce.py','fqin','fqout',str(pathlib.Path.home()/'scratch/squares-base/fq'),'x'],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=p.wait(timeout=max(1,min(%d,1794583200-time.time()-1)))
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.wait();sys.exit(3)
if rc==0:(D/'fqout/DONE').touch()
sys.exit(rc)
''' % left
        result = subprocess.run(['ssh', 'boxE', '$SCRATCH/squares-base/venv/bin/python', '-'], input=code, text=True)
        if result.returncode:
            r.state('STOP final quench at hard deadline; incomplete batch stays out of take')
            break
    # A timed-out batch is withheld. Existing fq rows remain available.
    r.certify([r.W / 'raw-fq'], r.T)
    r.handoff()


def git_run(args):
    cmd = ['git'] + args
    for attempt in range(2):
        result = subprocess.run(cmd, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end='', flush=True)
        if result.returncode == 0:
            return
        if attempt == 0 and 'index.lock' in result.stdout:
            time.sleep(3)
            continue
        result.check_returncode()


def text_output(args):
    return subprocess.check_output(args, text=True, cwd=REPO).strip()


def finish():
    stop_local()
    remote_stop()
    last_collect()
    r.run(['rsync', '-a', r.REMOTE, str(r.W / 'boxE-final') + '/'])
    # A second checksum pass must show no changed or missing file before removal.
    check = subprocess.check_output(['rsync', '-ani', '--checksum', r.REMOTE, str(r.W / 'boxE-final') + '/'], text=True)
    if check.strip():
        raise RuntimeError('remote copy checksum mismatch: ' + check)
    r.run(['ssh', 'boxE', 'rm -rf $SCRATCH/squares-midm'])
    for p in r.T.glob('.*.tmp'):
        p.unlink()
    r.state('FINISH all boxE files copied and checksum-verified; own boxE scratch removed; squares-base unchanged')
    r.state('WAIT final comparison at15:29Z; take is final and all search processes are stopped')
    while time.time() < 1794583740:
        time.sleep(min(30, 1794583740 - time.time()))
    cutoff=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    table = r.L / 'results/midm-r22-2026-11-13.tsv'
    sums = json.loads(text_output([r.PY, str(r.L / 'tools/midm/table22.py'), str(table)]))
    stats = json.loads(text_output([r.PY, str(r.L / 'tools/midm/stats22.py')]))
    results = r.rows(table)
    take = r.rows(r.T / 'take.tsv')
    quench_gain = sum(float(x.get('polish_gain',0)) for x in take)
    gain_on_starts=sum(float(x['start'])-float(x['new']) for x in take)
    done = [json.loads(p.read_text()) for p in (r.W / 'boxE-final/done').glob('*.json')]
    rawkeys = {int(p.stem[1:]) for p in r.W.glob('r*.tsv') if 'new-design raw start:' in p.read_text()}
    fresh = [j for j in done if not j.get('leg') and j['source'].endswith('-r22') and j['k'] not in (200, 201) and not j.get('raw_design') and j['k'] not in rawkeys]
    legs = [j for j in done if j.get('leg')]
    raw_starts = [j for j in done if not j.get('leg') and j['k'] in rawkeys]
    raw_wins = [x for x in take if 'new-design raw start:' in x['source']]
    public_jobs=[json.loads(p.read_text()) for p in (r.W/'jobs').glob('*.json') if json.loads(p.read_text()).get('public')]
    public_done=[j for j in done if j.get('public') and not j.get('leg')]
    final_bars=r.live_bars()
    public_obsolete=[j['n'] for j in public_jobs if not any(x['k']==j['k'] and not x.get('leg') for x in done) and ((r.W/'cancel'/('%d-%d'%(j['k'],j['n']))).exists() or float(r.rows(r.W/('r%d.tsv'%j['k']))[0]['score'])>final_bars[j['n']]+1e-6)]
    public_pending=[j['n'] for j in public_jobs if j['n'] not in public_obsolete and not any(x['k']==j['k'] and not x.get('leg') for x in done)]
    backlog=[n for k,n in enumerate((646,649,754,852,933,982,995),900) if not any(j['k']==k and not j.get('leg') for j in done)]
    fresh_gain = sum(j.get('gain', 0) for j in fresh)
    leg_gain = sum(j.get('gain', 0) for j in legs)
    ab = r.rows(r.W / 'ab22.tsv')
    pair_gain = {s: sum(float(x['gain_before_cert']) for x in ab if x['sigma'] == s and x['class'] == 'fresh pair') for s in ('0.02', '0.04')}
    next_items = [
        'Kick late fresh builds before their first merge, newest first. Initial round 22 source scans: %d, gain %.6g before certification. Keep every new forensics rectangle corner ahead of the backlog.' % (len(fresh), fresh_gain),
        'Give late round 21 finds their owed raw legs. The 693 control gained 4.076e-5 at sigma 0.04. Sigma 0.02 gained 9.077e-6 first, then 3.168e-5 on its raw leg.',
        'Use the paired sigma measurements before changing the default. Fresh paired gains before certification were %.6g at 0.02 and %.6g at 0.04. Both used the same seeds and time allowances.' % (pair_gain['0.02'], pair_gain['0.04']),
        'Continue legs from raw finds while they gain 1e-6 of score. This round %d legs found %.6g before certification. Quench certified files before publishing.' % (len(legs), leg_gain),
        'Leave near starts out unless a new design changes the reason they failed. Round 20 had no win from 17 starts. Round 21 starts 921 and 328 stayed above the bar.'
    ]
    if fresh_gain < 4.076e-5:
        next_items[0], next_items[1] = next_items[1], next_items[0]
    measurements = [
        '%d completed jobs. %s' % (len(done), json.dumps(stats, sort_keys=True)),
        'Take: %d rows, gain %.12g against round20; %d rows below every frozen round21 and other live round22 take, gain %.12g.' % (sums['rows'], sums['gain_round20'], sums['live_rows'], sums['gain_all']),
        'Old 370 control: six kicks, one find, side 19.756747264363 to 19.756683828751. Queue and claim controls passed. The certifier rejected frozen 693 and accepted improved 693. Published 693 rescored without error.',
        'Initial polish 693 is a repeat-kick control, separate from the six requested fresh pairs. It found 4.0760386e-5 at 0.04 and 9.0770152e-6 at 0.02. Its next 0.02 raw leg gained 3.1683357e-5.',
        'Fresh pair gains before certification: sigma0.02 %.12g, sigma0.04 %.12g. Files, seeds, wall times and gains are in work/ab22.tsv.' % (pair_gain['0.02'], pair_gain['0.04']),
        'Every published row was certified at 2.2e-11, quenched from its certified file on boxE, then certified again. An incomplete final quench batch was never published.'
    ]
    measurements.append('The second 693 source take row was already 7.04042e-06 below our first published 693 (the polish lane supplied that margin). Our final row was6.36522e-06 below that source take row; its final quench added 0. This is an improved-source restart, not an unchanged-copy restart.')
    if backlog:
        next_items.insert(2,'Reserve a window for the unfinished frozen backlog: '+str(backlog)+'. Round 21 backlog start 869 gained 6.7e-5 in one of four scans.')
    measurements.append('Public sources canceled as obsolete after a newer live layout beat them by more than1e-6 score: '+str(public_obsolete))
    measurements.append('Fresh public handoff: %d queued, %d completed initial scans. Unfinished n: %s. Sources and Apache2.0 notices are preserved in the start tables.' % (len(public_jobs),len(public_done),public_pending))
    if public_pending:
        r.atomic(r.W/'public-pending.tsv','n\n'+''.join(str(n)+'\n' for n in public_pending))
        next_items.insert(0,'Kick the %d unfinished public layouts in work/public-pending.tsv. These certified layouts arrived at 14:28Z. The old public 370 control gained 3.298e-6 in six tries.' % len(public_pending))
    next_items.append('Reserve a public slot from the handoff minute. This batch waited at least 18 minutes without a completed public scan. Ancestor names had also boosted seven kicked descendants into the direct-corner class.')
    measurements.append('Margin over the exact source take rows: %.12g across final rows. This separates inherited layout gains from the added kick and quench margin.' % gain_on_starts)
    measurements.append('Comparison time: '+cutoff)
    measurements.append('Unfinished frozen round20 backlog: '+str(backlog))
    measurements.append('Certified-file quench margin over the cached raw certified inputs: %.12g across the final take.' % quench_gain)
    measurements.append('Explicit new-design raw starts: %d scans, %d certified rows. Raw gains are reported separately from certified gains.' % (len(raw_starts),len(raw_wins)))
    next_items.append('Require another geometry change before repeating dry raw designs. This round %d new strip or rounded-band starts produced %d certified rows.' % (len(raw_starts),len(raw_wins)))
    if (r.W/'fq-pending.json').exists():
        next_items.insert(0,'Finish the withheld certified-stage quench batch in work/fq-send. The stage passed certification, but its final quench did not finish before the hard deadline.')
        measurements.append('An unfinished final certified-file quench batch remains in work/fq-send and was withheld from the take.')
    lines = ['Comparisons: '+cutoff+'.', '', 'The final take has %d rows, %.6g below the round 20 file.' % (sums['rows'], sums['gain_round20']),
             '%d rows remain below every other take, by %.6g in total.' % (sums['live_rows'], sums['gain_all']),
             'The [results table](../results/midm-r22-2026-11-13.tsv) gives both comparisons.', '',
             '| n | gain on round 20 | gain on every take | start |', '|---|---|---|---|']
    for x in results:
        lines.append('| %s | %.6g | %.6g | `%s` |' % (x['n'], float(x['gain_on_round20_file']), float(x['gain_on_all']), x['start_dir']))
    measures = ['Completed jobs: %d.' % len(done),
                'Initial round 22 source scans gave %.6g before certification. Raw legs gave %.6g.' % (fresh_gain, leg_gain),
                'Fresh paired scans gave %.6g at sigma 0.02 and %.6g at sigma 0.04.' % (pair_gain['0.02'], pair_gain['0.04']),
                'The old 693 control gave 4.076e-5 at sigma 0.04.',
                'At sigma 0.02 it gave 9.077e-6, then 3.168e-5 on its first raw leg.',
                'All jobs ended before cleanup. The copy from boxE passed a checksum comparison.', '',
                'Next round:', '',
                '1. Kick fresh builds first. Initial round 22 source scans gained %.6g before certification.' % fresh_gain,
                '2. Give late finds their owed raw legs. The 693 control and its leg gave about 4.076e-5 at either sigma.',
                '3. Keep comparing sigmas on fresh files. The paired gains were %.6g at 0.02 and %.6g at 0.04.' % (pair_gain['0.02'], pair_gain['0.04']),
                '4. Keep the raw-leg rule. The %d legs found %.6g before certification.' % (len(legs), leg_gain),
                '5. Keep near files out. Round 20 had no certified result from 17 near starts.']
    section = (r.W / 'doc22.md').read_text().replace('FINAL_RESULTS', '\n'.join(lines)).replace('FINAL_MEASUREMENTS', '\n'.join(measures))
    (r.W / 'doc22-final.md').write_text(section)
    checker = ['/opt/homebrew/bin/python3', '$STYLE_CHECK/check.py', '--level', 'default', str(r.W / 'doc22-final.md')]
    r.run(checker)
    doc = r.L / 'avenues/midm.md'
    text = doc.read_text()
    if '## 13. Round 22 ' not in text:
        text = text.replace('\n## Summary\n', '\n' + section + '\n## Summary\n', 1)
        doc.write_text(text)
    paths = ['lanes/squares/avenues/midm.md', 'lanes/squares/results/midm-r22-2026-11-13.tsv',
             'lanes/squares/tools/midm/round22.py', 'lanes/squares/tools/midm/final22.py', 'lanes/squares/tools/midm/stats22.py', 'lanes/squares/midm_take.py', 'lanes/squares/midm_scan.py', 'lanes/squares/midm_fqonce.py', 'lanes/squares/tools/midm/public22.py']
    git_run(['add'] + paths)
    try:
        git_run(['commit', '-m', 'docs(squares): record round 22 midm kick results', '--only', '--'] + paths)
    except subprocess.CalledProcessError:
        if subprocess.run(['git','diff','--quiet','HEAD','--']+paths,cwd=REPO).returncode:
            raise
        r.state('Own final paths already committed by a concurrent checkout transaction')
    commit = text_output(['git', 'rev-parse', 'HEAD'])
    push = 'pushed'
    try:
        git_run(['pull', '--rebase', '--autostash'])
        git_run(['push', 'origin', 'HEAD:main'])
    except subprocess.CalledProcessError:
        if subprocess.run(['git', 'push', 'origin', 'HEAD:main'], cwd=REPO).returncode:
            push = 'not pushed'
    commit = text_output(['git','log','-1','--format=%H','--','lanes/squares/results/midm-r22-2026-11-13.tsv'])
    report = dict(lane='midm', improved_n=sums['rows'], gain=dict(against_round20=sums['gain_round20'], against_frozen_r21_and_other_live_r22=sums['gain_all'], live_improved_n=sums['live_rows']),
                  take_dir=str(r.T), summary='Round 22 used two boxE slots for kicks and raw legs. Every published file received a quench from its certified copy. Comparison time: '+cutoff+'. '+push+'.',
                  what_was_measured=measurements, next=next_items, commits=(json.loads((r.W / 'commits.json').read_text()) if (r.W / 'commits.json').exists() else ['74e39a0', '6b81d75']) + [commit],
                  processes_left='None. Local loops and boxE workers stopped. boxE scratch was copied, checked by checksum and removed.', blocked='nothing' if push == 'pushed' else 'not pushed',
                  repo='private repo', branch='main', worktree=REPO, pr='none')
    r.atomic(r.T / 'report.json', json.dumps(report, indent=2) + '\n')
    r.state('FINISH report.json written; take.tsv final; results/doc committed '+commit+' '+push)


def main():
    r.state('START finalizer pid=%d; wait to15:17Z, hard search/quench cutoff15:20Z, log=work/final22.log' % os.getpid())
    while time.time() < STOP:
        time.sleep(min(30, STOP - time.time()))
    if '--now' not in sys.argv:
        os.execv(r.PY, [r.PY, '-I', str(Path(__file__).resolve()), '--now'])
    finish()


if __name__ == '__main__':
    main()
