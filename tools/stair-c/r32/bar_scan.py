"""Use the live bar for fq's input box while retaining measured output sides."""
import importlib.util,json,math,os,sys
from pathlib import Path
sys.path[:0]=['lane','.']
spec=importlib.util.spec_from_file_location('bar_scan_engine','lane/midm_scan.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
ORIGINAL=M.quench

def install(target,logfile):
    calls=[]
    def quench(fq,tmp,side,X,flags,timeout=180):
        requested=min(side,target);result=ORIGINAL(fq,tmp,requested,X,flags,timeout)
        calls.append(dict(original_side=side,requested_side=requested,returned_side=result[0]))
        Path(logfile).write_text(json.dumps(calls,indent=2));return result
    M.quench=quench

def control(path):
    held=M.mlp.load(path,{975})[975];side,X=M.to_fq(held);target=side
    observed=[];original_run=M.subprocess.run
    def run(cmd,*args,**kwargs):
        requested=float(Path(cmd[cmd.index('--in')+1]).read_text().splitlines()[0].split()[1]);observed.append(requested)
        return original_run(cmd,*args,**kwargs)
    install(target,'bar-control-starts.json');M.subprocess.run=run
    Path('bar-control-tmp').mkdir(exist_ok=True)
    try:value,Q=M.quench(os.path.abspath('fq'),'bar-control-tmp',side+.01,X,[],timeout=90)
    finally:M.subprocess.run=original_run
    assert observed==[target]and target<side+.009
    assert value is not None and Q is not None and len(Q)==975
    P=M.from_fq(Q);actual=M.mlp.side(P);gap=M.mlp.min_gap(P)
    assert math.isfinite(actual)and gap>=-1e-7,(actual,gap)
    bad=P.copy();bad[1]=bad[0];assert M.mlp.min_gap(bad)<-.99
    receipt=dict(passed=True,n=975,requested_side=target,uncapped_side=side+.01,returned_side=value,actual_side=actual,gap=gap)
    Path('bar-kick-control.json').write_text(json.dumps(receipt));print('CONTROL bar input',json.dumps(receipt),flush=True)
    return receipt

if __name__=='__main__':
    at=sys.argv.index('--target-side');target=float(sys.argv[at+1]);del sys.argv[at:at+2]
    out=sys.argv[sys.argv.index('--out')+1];install(target,str(Path(out)/'bar-starts.json'));M.main()
