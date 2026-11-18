"""Use the existing midm engine for one bounded kick of a close whole layout."""
import csv,hashlib,json,math,os,signal,subprocess,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import stair_finesafe as floatsafe
import methods_lp as M

def probe_stop(elapsed,has_raw):return elapsed>=120 and not has_raw

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
    if not j.get('kick_control'):
        points=M.load(path,{n})[n];side=M.side(points)
        live=json.load(open('bar.json'))if Path('bar.json').exists()else{}
        limit=float(live.get(str(n),float('inf')))
        angles=__import__('numpy').mod(points[:,2],math.pi/2)
        tilted=angles[__import__('numpy').minimum(angles,math.pi/2-angles)>1e-7]
        lattice=n in {626,677,678,730,731,785,786,842,843,901,902,962,963,964}or len(tilted)>0 and bool((abs(tilted-math.pi/4)<1e-7).all())
        if side>limit+8*math.ulp(limit) or lattice:
            return path,dict(invoked=False,start=side,end=side,refused='45-degree lattice'if lattice else'above lowest live row',live_side=limit)
    start=time.time();root=Path('whole-kicks')/Path(path).stem;root.mkdir(parents=True,exist_ok=True)
    phase=Path('kick-deadline')if Path('kick-deadline').exists()else Path('search-deadline')
    budget=int(j.get('kick_seconds',900));deadline=min(start+budget,kick_end(start,float(phase.read_text()),float(Path('deadline').read_text())))
    seed=int(j.get('kick_seed',2800+n));initial=M.side(M.load(path,{n})[n]);receipt=dict(initial_input=path,initial_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),start=initial,seed=seed,budget=budget,invoked=False)
    (root/'deadline').write_text(str(deadline))
    cmd=[sys.executable,'-I','lane/midm_scan.py','--n',str(n),'--sub',path,'--out',str(root),'--fq',os.path.abspath('fq'),'--seconds',str(budget),'--seed',str(seed),'--modes','kick,lkick','--kicks','0.02','--flagsets','d,t','--max-tries','60','--stop6','--deadline',str(root/'deadline')]
    if j.get('kick_target_side')is not None:
        assert json.load(open('bar-kick-control.json'))['passed']
        target=float(j['kick_target_side'])
        if j.get('bar_input_follow')and Path('bar.json').exists():target=min(target,float(json.load(open('bar.json')).get(str(n),target)))
        cmd[2]='bar_scan.py';cmd.extend(['--target-side',repr(target),'--ref',repr(target)]);receipt['target_side']=target
    if deadline-time.time()>10:
        receipt.update(command=cmd,invoked=True)
        with (root/'driver.log').open('ab')as log:
            child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            probe_end=min(start+120,deadline)
            while child.poll() is None and time.time()<deadline+3:
                if probe_stop(time.time()-start,bool(list((root/'raw').glob('*.csv')))):
                    stop_tree(child);receipt['probe_stopped']=True;break
                time.sleep(min(2,max(.01,deadline+3-time.time())))
            if child.poll() is None:stop_tree(child)
            rc=child.returncode
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
