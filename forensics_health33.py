"""Recover this round's three boxE workers without starting duplicate seats."""
from pathlib import Path
import datetime
import fcntl
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time


def table():
    result = {}
    for line in subprocess.check_output(['ps','-ww','-axo','pid,ppid,command'], text=True).splitlines():
        row = line.split(None,2)
        if len(row) == 3 and row[0].isdigit():
            result[int(row[0])] = (int(row[1]),row[2])
    return result


def args(command):
    try:
        return shlex.split(command)
    except ValueError:
        return []


def seats(processes, root):
    result = {}
    for pid,(parent,command) in processes.items():
        words = args(command)
        for i,word in enumerate(words):
            if (Path(word) == root/'code/forensics_watch33.py' and
                    words[i+1:i+3] == ['worker',str(root)] and len(words)>i+3):
                result.setdefault(words[i+3],[]).append(pid)
    return result


def descendants(processes, seeds):
    chosen = set(seeds)
    while True:
        more = {pid for pid,(parent,command) in processes.items() if parent in chosen}
        if more <= chosen:
            return chosen
        chosen |= more


def orphan_fq(processes, root, base, workers):
    live = descendants(processes, workers)
    selected = []
    for pid,(parent,command) in processes.items():
        words = args(command)
        if (pid not in live and len(words)>1 and Path(words[0]) == base/'fq' and words[1]=='quench' and
                any(word == str(root) or word.startswith(str(root)+'/') for word in words[2:])):
            selected.append(pid)
    return selected


def control():
    root=Path('/scratch/squares-forensics-r33');base=Path('/scratch/squares-base')
    processes={11:(1,f'python -I {root}/code/forensics_watch33.py worker {root} 0 999 fq'),
               12:(11,f'{base}/fq quench --in {root}/tmp/a.txt'),
               21:(1,f'python -I {root}/code/forensics_watch33.py worker {root} 1 999 fq'),
               31:(1,f'python -I {root}-other/code/forensics_watch33.py worker {root}-other 2 999 fq'),
               41:(1,f'{base}/fq quench --in {root}/tmp/orphan.txt'),
               42:(1,f'{base}/fq quench --in {root}-other/tmp/a.txt')}
    assert seats(processes,root)=={'0':[11],'1':[21]}
    assert orphan_fq(processes,root,base,{11,21})==[41]
    print('CONTROL two owned seats found; missing seat remains absent. Owned orphan selected; live children and other roots preserved',flush=True)


def repair(root, base):
    assert root.is_dir() and root.name=='squares-forensics-r33'
    lock=(root/'worker-health.lock').open('a+')
    try:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        return dict(busy=True)
    deadline=float((root/'deadline.txt').read_text())
    if (root/'STOP').exists() or time.time()>=deadline-2:
        return dict(stopped=True)
    processes=table();found=seats(processes,root)
    assert set(found)<= {'0','1','2'} and all(len(v)==1 for v in found.values()),found
    workers={pid for group in found.values() for pid in group}
    killed=orphan_fq(processes,root,base,workers)
    for pid in killed:
        try:os.kill(pid,signal.SIGTERM)
        except ProcessLookupError:pass
    if killed:
        time.sleep(.2);current=table()
        for pid in killed:
            if pid in current and current[pid][1]==processes[pid][1]:
                try:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass
    reclaimed=[]
    for claim in (root/'claims').iterdir():
        if not claim.is_dir() or claim.is_symlink() or (root/'results'/(claim.name+'.json')).exists():continue
        ownerfile=claim/'owner.json';owner=json.loads(ownerfile.read_text()) if ownerfile.exists() else None
        stale=(owner is not None and owner.get('pid') not in workers) or (owner is None and not workers)
        if stale:
            shutil.rmtree(claim);reclaimed.append(claim.name)
    started=[]
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    for seat in ['0','1','2']:
        if (root/'STOP').exists():break
        if seat in found:
            (root/f'worker{seat}.pid').write_text(str(found[seat][0]));continue
        with (root/f'worker{seat}.log').open('a') as out:
            proc=subprocess.Popen(['nohup','nice','-n','5',str(base/'venv/bin/python'),'-I',str(root/'code/forensics_watch33.py'),'worker',str(root),seat,str(deadline),str(base/'fq')],stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True,env=env)
        (root/f'worker{seat}.pid').write_text(str(proc.pid));found[seat]=[proc.pid];started.append(dict(seat=seat,pid=proc.pid))
    guard=[]
    for pid,(parent,command) in processes.items():
        words=args(command)
        if any(Path(word)==root/'code/forensics_guard26.py' and words[i+1:i+2]==[str(root)] for i,word in enumerate(words)):
            guard.append(pid)
    guard_started=None
    if not guard and not (root/'STOP').exists():
        with (root/'guard.log').open('a') as out:
            proc=subprocess.Popen(['nohup','nice','-n','5',str(base/'venv/bin/python'),'-I',str(root/'code/forensics_guard26.py'),str(root)],stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True,env=env)
        (root/'guard.pid').write_text(str(proc.pid));guard_started=proc.pid
    receipt=dict(asof=datetime.datetime.now(datetime.UTC).isoformat(),workers=found,started=started,orphan_fq_stopped=killed,reclaimed=reclaimed,guard_started=guard_started,worker_code_sha256=hashlib.sha256((root/'code/forensics_watch33.py').read_bytes()).hexdigest())
    (root/'worker-health.json.tmp').write_text(json.dumps(receipt,indent=2));(root/'worker-health.json.tmp').replace(root/'worker-health.json')
    return receipt


if __name__=='__main__':
    if sys.argv[1]=='control':control()
    else:print(json.dumps(repair(Path(sys.argv[1]),Path(sys.argv[2]))),flush=True)
