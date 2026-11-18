"""Use the existing midm engine for one bounded kick of a close whole layout."""
import csv,hashlib,json,math,os,signal,subprocess,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import floatsafe
import methods_lp as M

def kick_end(start,phase_end,numeric_end):return min(start+900,phase_end,numeric_end-150)

def stop_tree(child):
    edges=[tuple(map(int,line.split()))for line in subprocess.check_output(['ps','-axo','pid=,ppid='],text=True).splitlines()if len(line.split())==2]
    own={child.pid}
    while True:
        more={p for p,parent in edges if parent in own}
        if more<=own:break
        own.update(more)
    for sig in [signal.SIGTERM,signal.SIGKILL]:
        for p in own:
            try:os.kill(p,sig)
            except ProcessLookupError:pass
        time.sleep(.1)
    child.wait()

def prepare(path,n,j):
    if j.get('kick_bar_control'):
        from bar_scan import control
        return path,dict(control(path),invoked=True,control_only=True)
    start=time.time();root=Path('whole-kicks')/Path(path).stem;root.mkdir(parents=True,exist_ok=True)
    phase=Path('kick-deadline')if Path('kick-deadline').exists()else Path('search-deadline')
    deadline=kick_end(start,float(phase.read_text()),float(Path('deadline').read_text()))
    seed=int(j.get('kick_seed',2800+n));initial=M.side(M.load(path,{n})[n]);receipt=dict(initial_input=path,initial_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),start=initial,seed=seed,budget=900,invoked=False)
    (root/'deadline').write_text(str(deadline))
    cmd=[sys.executable,'-I','lane/midm_scan.py','--n',str(n),'--sub',path,'--out',str(root),'--fq',os.path.abspath('fq'),'--seconds','900','--seed',str(seed),'--modes','kick,lkick','--kicks','0.02','--flagsets','d,t','--max-tries','60','--stop6','--deadline',str(root/'deadline')]
    if j.get('kick_target_side')is not None:
        assert json.load(open('bar-kick-control.json'))['passed']
        cmd[2]='bar_scan.py';cmd.extend(['--target-side',repr(float(j['kick_target_side'])),'--ref',repr(float(j['kick_target_side']))]);receipt['target_side']=float(j['kick_target_side'])
    if deadline-time.time()>10:
        receipt.update(command=cmd,invoked=True)
        with (root/'driver.log').open('ab')as log:
            child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            try:rc=child.wait(timeout=max(1,deadline-time.time()+3))
            except subprocess.TimeoutExpired:stop_tree(child);rc=124
        receipt['returncode']=rc
    best=initial;chosen=path;best_rows=None
    for p in sorted((root/'raw').glob('*.csv')):
        rows=list(csv.DictReader(open(p)));_,fr,score,error=floatsafe.work((n,rows))
        if fr is not None and (1+score)*math.sqrt(n)<best:
            best=(1+score)*math.sqrt(n);chosen=str(p);best_rows=fr
    receipt.update(end=best,raw_source=chosen,seconds=time.time()-start,finds=len(list((root/'raw').glob('*.csv'))))
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2))
    if j.get('kick_control'):
        assert receipt['invoked'] and receipt.get('returncode')==0,'kick engine did not complete'
        assert initial-best>.001,'inflated positive control did not recover .001 side'
    if best_rows is None:return path,receipt
    out=Path('kick-cert')/Path(path).name;out.parent.mkdir(exist_ok=True)
    with out.open('w')as f:w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(best_rows)
    receipt['certified_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();receipt['certified_file']=str(out)
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2));return str(out),receipt
