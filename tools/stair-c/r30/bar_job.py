"""Probe near the live bar when an optimistic recipe has no legal start."""
import csv,importlib.util,json,math,os,pickle,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import corner_guard as G
assert json.load(open('corner-guard-control.json'))['passed']
G.install()
import corner_stacks as K
assert json.load(open('corner-stacks-control.json'))['passed']
K.install()
spec=importlib.util.spec_from_file_location('stair_job29','lane/stair-c_job.py');J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)

def run(a):
    original=M.cmd_job
    def broaden(args):
        n=int(args[4]);raw=Path(args[1]);name=args[3];pred=float(args[10]);m=math.isqrt(n-1)
        rc=original(args)
        if(raw/(name+'.csv')).exists()or not(raw/(name+'.nostart')).exists():return rc
        bar={int(r['n']):float(r['L'])for r in csv.DictReader(open(args[2]))}
        if Path('bar.json').exists():bar.update({int(k):v for k,v in json.load(open('bar.json')).items()})
        probe=min(.9995,bar[n]-m-.0002)
        if pred+.003>=probe:return rc
        next_args=list(args);next_args[10]=repr(probe)
        print('BAR PROBE',n,'table prediction',m+pred,'probe',m+probe,'bar',bar[n],flush=True)
        rc=original(next_args)
        for suffix in['.json','-slp.json','.nostart']:
            p=raw/(name+suffix)
            if p.exists():
                j=json.load(open(p));j['table_predicted']=m+pred;j['bar_start_probe']=m+probe
                p.write_text(json.dumps(j))
        return rc
    M.cmd_job=broaden
    try:return J.run(a)
    finally:M.cmd_job=original

def control():
    import expanded as E
    n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
    mods=M.modules_of(d,'own construction: bar probe control','our own','r30-bar-control');twins,ids=M.slid(d,mods);mods+=twins
    pool=Path('bar-probe-control');pool.mkdir(exist_ok=True)
    pickle.dump(dict(mods=mods,layouts=[]),open(pool/'library.pkl','wb'));pickle.dump({q['id']:M.tabulate(q)for q in mods},open(pool/'lens.pkl','wb'))
    by={q['id']:q for q in mods};C,F1,F2=[dict(q=by[k])for k in[ids[2],ids[0],ids[1]]]
    P,why=M.assemble(None,n,C,F1,F2,d['s1'],d['s2'],d['f']-.009)
    assert P is None,'the changed prediction must fail the old start budget'
    run([str(pool),str(pool/'raw'),'details.csv','975-bar-control',str(n),ids[2],ids[0],ids[1],str(d['s1']),str(d['s2']),repr(float(d['f']-.012)),'--fq','./fq','--squeeze','family'])
    p=pool/'raw/975-bar-control.json';j=json.load(open(p));rows=M.np.asarray(M.read_layouts(str(p.with_suffix('.csv')))[n],float);side,gap=M.layout_state(rows)
    assert j.get('bar_start_probe')and gap>=-1e-7 and side<=d['s']+2e-6,(side,gap)
    print('CONTROL bar probe975 passed; false low prediction had no old start; side',side,'gap',gap,flush=True)
    Path('bar-probe-control.json').write_text(json.dumps(dict(passed=True,n=n,side=side,gap=gap,predicted=d['s']-.012)))
if __name__=='__main__':
    a=sys.argv[1:]
    if a==['--control']:control()
    else:
        if a and a[0].endswith('/modules.py'):a=a[2:]
        assert json.load(open('bar-probe-control.json'))['passed']
        run(a)
