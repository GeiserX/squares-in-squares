"""Stop this lane's processes without touching another scratch root."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time


def select(table, root, ignore=()):
    boundary = re.compile(re.escape(str(root))+r'(?=/|\s|$)')
    relative = re.compile(r'(?<![\w-])scratch/'+re.escape(root.name)+r'(?=/|\s|$)')
    names = ('forensics_watch31.py worker ', 'forensics_scan25.py ',
             'forensics_guard26.py ', 'forensics_probe26.py ', 'reload-workers26.py',
             'forensics_tight28.py ', 'reload-workers28.py', 'forensics_insert31.py ')
    chosen = {pid for pid, (parent, cmd) in table.items()
              if pid not in ignore and (boundary.search(cmd) or relative.search(cmd)) and
              (any(name in cmd for name in names) or 'fq quench ' in cmd or 'rsync --server ' in cmd)}
    while True:
        children = {pid for pid, (parent, cmd) in table.items() if parent in chosen and pid not in ignore}
        if children <= chosen:
            return chosen
        chosen |= children


def processes():
    table = {}
    for line in subprocess.check_output(['ps', '-axo', 'pid,ppid,command'], text=True).splitlines():
        row = line.split(None, 2)
        if len(row) == 3 and row[0].isdigit():
            table[int(row[0])] = (int(row[1]), row[2])
    return table



def select_local(table, work, ignore=()):
    """Select this round's named local helpers and their children."""
    import shlex
    work=Path(work)
    names={'pulse31.py','supervisor31.py','kickfeed31.py','claims-watch31.py',
           'partners31.py','partners30-v2.py','partners30-v3.py','recover-held31.py'}
    chosen=set()
    for pid,(parent,command) in table.items():
        if pid in ignore:continue
        try:args=shlex.split(command)
        except ValueError:continue
        if not args or not Path(args[0]).name.lower().startswith('python'):continue
        if any(Path(arg).parent==work and Path(arg).name in names for arg in args[1:]):chosen.add(pid)
    while True:
        children={pid for pid,(parent,cmd) in table.items() if parent in chosen and pid not in ignore}
        if children<=chosen:return chosen
        chosen|=children


def stop_local_helpers(work):
    table=processes();ignore={os.getpid()};chosen=select_local(table,work,ignore)
    for pid in chosen:
        try:os.kill(pid,signal.SIGTERM);os.kill(pid,signal.SIGCONT)
        except ProcessLookupError:pass
    time.sleep(.3)
    current=processes()
    for pid in chosen:
        if pid in current and current[pid][1]==table[pid][1]:
            try:os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:pass
    time.sleep(.2)
    left=select_local(processes(),work,ignore)
    receipt=dict(asof=dt.datetime.now(dt.timezone.utc).isoformat(),selected=sorted(chosen),processes_left=sorted(left))
    (Path(work)/'local-process-stop.json').write_text(json.dumps(receipt,indent=2));assert not left,receipt
    return receipt


def control():
    root = Path('/scratch/squares-forensics-r31')
    table = {11: (1, 'python '+str(root)+'/code/forensics_watch31.py worker '+str(root)),
             12: (11, 'fq quench --in '+str(root)+'/tmp/a.txt'),
             13: (1, 'python /scratch/squares-other/code/forensics_watch31.py worker /scratch/squares-other'),
             14: (1, 'python '+str(root)+'-other/code/forensics_watch31.py worker '+str(root)+'-other'),
             15: (1, 'python '+str(root)+'/code/forensics_tight28.py '+str(root)),
             16: (1, 'python /scratch/squares-other/code/forensics_tight28.py /scratch/squares-other'),
             17: (1, 'python '+str(root)+'/code/reload-workers28.py'),
             18: (1, 'rsync --server -az . scratch/squares-forensics-r31/tasks/'),
             19: (1, 'rsync --server -az . scratch/squares-other/tasks/'),
             20: (1, 'rsync --server -az . scratch/squares-forensics-r31-other/tasks/'),
             21: (1, 'rsync --server --sender -az . '+str(root)+'/')}
    assert select(table, root) == {11, 12, 15, 17, 18, 21}
    assert select(table, root, {11, 12, 15, 17, 18, 21}) == set()
    print('CONTROL owned worker and child selected; unrelated and longer-prefix roots preserved', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--control', action='store_true')
    args = parser.parse_args()
    if args.control:
        control()
        return
    if not args.root:
        parser.error('root required')
    root = Path(args.root).resolve()
    assert root.is_dir() and root.name in ('squares-forensics-r31', 'squares-forensics')
    table = processes()
    ignore = set()
    pid = os.getpid()
    while pid in table and pid not in ignore:
        ignore.add(pid)
        pid = table[pid][0]
    chosen = select(table, root, ignore)
    if not args.dry_run:
        (root/'STOP').touch()
        for pid in chosen:
            try:
                os.kill(pid, signal.SIGTERM)
                os.kill(pid, signal.SIGCONT)
            except ProcessLookupError:
                pass
        time.sleep(.3)
        current = processes()
        for pid in chosen:
            if pid in current and current[pid][1] == table[pid][1]:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        time.sleep(.2)
    left = select(processes(), root, ignore)
    receipt = dict(asof=dt.datetime.now(dt.timezone.utc).isoformat(), root=str(root),
                   selected=sorted(chosen), dry_run=args.dry_run, processes_left=sorted(left))
    if not args.dry_run:
        assert not left, receipt
        (root/'process-stop-receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
