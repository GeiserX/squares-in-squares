"""Resume scanner helpers when their bounded probe client no longer exists."""
from pathlib import Path
import json
import os
import shlex
import signal
import subprocess
import sys

PILOTS={'angle-pilot34.py','rotate-pilot34.py','focused-mesh34.py','slide-pilot34.py','slide-pilot34b.py','slide-pilot34c.py','tip-pilot34.py','tip-pilot34b.py'}


def select(table,work):
    work=Path(work);helpers=set();pilots=set()
    for pid,(state,command) in table.items():
        try:words=shlex.split(command)
        except ValueError:continue
        if not words or not Path(words[0]).name.lower().startswith('python'):continue
        for i,word in enumerate(words[1:],1):
            path=Path(word)
            if path.parent==work and path.name in PILOTS:pilots.add(pid)
            partner=path.parent==work and path.name=='partners34.py'
            watcher=path.name=='forensics_watch34.py' and words[i+1:i+3]==['local',str(work.parent.parent)]
            if (partner or watcher) and 'T' in state:helpers.add(pid)
    return set() if pilots else helpers


def repair(work):
    work=Path(work);table={}
    for line in subprocess.check_output(['ps','-ww','-axo','pid,state,command'],text=True).splitlines():
        row=line.split(None,2)
        if len(row)==3 and row[0].isdigit():table[int(row[0])]=(row[1],row[2])
    candidates=select(table,work)
    if candidates:
        remote=subprocess.run(['ssh','-o','ConnectTimeout=5','boxB','ps -ww -axo pid,command'],capture_output=True,text=True,timeout=10)
        if remote.returncode or seat_busy(remote.stdout):
            receipt=dict(resumed=[],remote_busy_or_unknown=True)
            (work/'pause-health.json').write_text(json.dumps(receipt))
            return receipt
    resumed=[]
    for pid in candidates:
        current=subprocess.run(['ps','-ww','-p',str(pid),'-o','state=,command='],capture_output=True,text=True).stdout.strip().split(None,1)
        if len(current)==2 and 'T' in current[0] and current[1]==table[pid][1]:
            try:os.kill(pid,signal.SIGCONT);resumed.append(pid)
            except ProcessLookupError:pass
    if resumed:(work/'PAUSE_SCAN').unlink(missing_ok=True)
    receipt=dict(resumed=resumed)
    (work/'pause-health.json').write_text(json.dumps(receipt))
    return receipt


def seat_busy(commands):
    root='$SCRATCH/squares-forensics-r34/code/'
    names=['forensics_scan25.py','forensics_probe26.py','forensics_angle34.py','forensics_rotate34.py','forensics_slide34.py','forensics_tip34.py']
    return any(root+name+' ' in commands for name in names)


def control():
    work=Path('/scratch/take-forensics-r34/work');scratch=work.parent.parent
    table={11:('T',f'python -I /code/forensics_watch34.py local {scratch} 999'),12:('T',f'python -I {work}/partners34.py'),13:('T',f'python -I {work}/publish34.py'),14:('T',f'python -I {work}-other/partners34.py')}
    assert select(table,work)=={11,12}
    table[15]=('S',f'python -I {work}/slide-pilot34c.py')
    assert select(table,work)==set()
    del table[15];table[11]=('S',table[11][1]);assert select(table,work)=={12}
    assert seat_busy('python -I $SCRATCH/squares-forensics-r34/code/forensics_slide34.py run job')
    assert not seat_busy('python -I $SCRATCH/squares-forensics-r34-other/code/forensics_slide34.py run job')
    print('CONTROL abandoned scanner and partner pauses recover; live probe, publisher and other root preserved',flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control()
    else:print(json.dumps(repair(Path(sys.argv[1]))),flush=True)
