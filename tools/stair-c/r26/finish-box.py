"""Stop only this lane's processes, archive its scratch, then verify before removal."""
import hashlib,json,os,pathlib,shutil,signal,subprocess,sys,tarfile,time
def payload_files(root):
    return [p for p in sorted(root.rglob('*')) if p.is_file() and p.relative_to(root).parts[0]!='venv']

if '--control' in sys.argv:
    import tempfile
    parent=pathlib.Path(sys.argv[sys.argv.index('--control')+1])
    with tempfile.TemporaryDirectory(prefix='receipt-control-',dir=parent) as d:
        root=pathlib.Path(d);(root/'packing.csv').write_text('n,x,y\n1,0,0\n');(root/'tool.py').write_text('fixture\n')
        (root/'venv').mkdir();(root/'venv/python').symlink_to('../tool.py')
        expected={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in payload_files(root)}
        assert set(expected)=={'packing.csv','tool.py'}
        with tarfile.open(root/'copy.tar.gz','w:gz') as tf:
            for name in expected:tf.add(root/name,arcname=name)
        with tarfile.open(root/'copy.tar.gz') as tf:
            for item in tf.getmembers():
                data=tf.extractfile(item).read()
                assert hashlib.sha256(data).hexdigest()==expected[item.name]
                assert hashlib.sha256(data+b'changed').hexdigest()!=expected[item.name]
        ownroot='/scratch/squares-stair-c'
        assert not '/scratch/squares-stair-c-base'.startswith(ownroot+'/')
    print('CONTROL receipt verified2 archived files; changed bytes rejected; sibling scratch excluded')
    sys.exit()
ROOT=pathlib.Path.home()/'scratch/squares-stair-c'
assert ROOT.name=='squares-stair-c' and ROOT.is_dir() and not ROOT.is_symlink()
assert 'One serial remote worker' in (ROOT/'worker.py').read_text()
protect={os.getpid()};p=os.getppid()
parents={int(r[0]):int(r[1]) for r in (x.split() for x in subprocess.check_output(['ps','-ax','-o','pid=,ppid='],text=True).splitlines()) if len(r)==2}
while p and p not in protect:protect.add(p);p=parents.get(p,0)
def own():
    proc=subprocess.Popen(['/usr/sbin/lsof','-n','-d','cwd','-F','pn'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    output,_=proc.communicate()
    pid=None;out=set()
    for line in output.splitlines():
        if line.startswith('p'):pid=int(line[1:])
        if line.startswith('n') and pid not in protect and pid!=proc.pid:
            cwd=line[1:]
            if cwd==str(ROOT) or cwd.startswith(str(ROOT)+'/'):out.add(pid)
    # Include children even if fq changed its working directory.
    rows=subprocess.check_output(['ps','-ax','-o','pid=,ppid='],text=True).splitlines()
    edges=[tuple(map(int,x.split())) for x in rows if len(x.split())==2]
    live={pid for pid,parent in edges};out.intersection_update(live)
    changed=True
    while changed:
        changed=False
        for child,parent in edges:
            if parent in out and child not in out and child not in protect:out.add(child);changed=True
    return out

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            if '--remove' not in sys.argv and (ROOT/'pack-deadline').exists() and time.time()>float((ROOT/'pack-deadline').read_text()):raise TimeoutError('packing deadline')
            h.update(b)
    return h.hexdigest()

if '--scope-control' in sys.argv:
    active=own();worker=int((ROOT/'worker.pid').read_text())
    assert worker in active and os.getpid() not in active
    print('CONTROL process scope found own worker',worker,'and',len(active),'lane processes; self and parent session excluded')
    sys.exit()

if '--remove' in sys.argv:
    expected=sys.argv[sys.argv.index('--remove')+1]
    assert sha(ROOT/'receipt.json')==expected and not own()
    shutil.rmtree(ROOT);print(json.dumps(dict(removed=str(ROOT),processes_left=[])));sys.exit()
(ROOT/'STOP').touch();stopped=set();commands={}
for _ in range(3):
    active=own();stopped.update(active)
    if active:
        result=subprocess.run(['ps','-ww','-p',','.join(map(str,sorted(active))),'-o','pid=,ppid=,pgid=,command='],capture_output=True,text=True)
        for line in result.stdout.splitlines():
            fields=line.strip().split(None,3)
            if len(fields)==4:commands[fields[0]]=dict(ppid=int(fields[1]),pgid=int(fields[2]),command=fields[3])
    for pid in active:
        try:os.kill(pid,signal.SIGTERM)
        except ProcessLookupError:pass
    time.sleep(.5)
for pid in own():
    try:os.kill(pid,signal.SIGKILL)
    except ProcessLookupError:pass
assert not own()
(ROOT/'stopped-commands.json').write_text(json.dumps(commands,indent=2))
archive=ROOT/'final-copy.tar.gz';receipt=ROOT/'receipt.json'
files=[p for p in payload_files(ROOT) if p not in [archive,receipt]]
assert not any(p.is_symlink() for p in files)
manifest={str(p.relative_to(ROOT)):sha(p) for p in files}
receipt.write_text(json.dumps(dict(files=manifest,stopped=sorted(stopped),processes_left=[],omitted=['venv (copied runtime, not result payload)']),indent=2))
with tarfile.open(archive,'w:gz') as tf:
    for p in files+[receipt]:
        if (ROOT/'pack-deadline').exists() and time.time()>float((ROOT/'pack-deadline').read_text()):raise TimeoutError('packing deadline')
        tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
print(json.dumps(dict(archive=str(archive),files=len(files),bytes=sum(p.stat().st_size for p in files),archive_sha256=sha(archive),receipt_sha256=sha(receipt),processes_left=[])),flush=True)
