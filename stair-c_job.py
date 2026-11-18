#!/usr/bin/env python3
"""Export the legal family SLP before bounded fq passes.

Publication still needs a separate quench of the certified file. The early
layout lets follow lanes work while the builder finishes its two fq passes.
"""
import json,math,os,pickle,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import modules as M
import family_step as F


def run(args):
    pool,raw,details,name=args[:4];n=int(args[4]);ids=args[5:8]
    s1,s2=int(args[8]),int(args[9]);f=float(args[10]);start=time.time()
    library=pickle.load(open(pool+'/library.pkl','rb'))
    by={q['id']:q for q in library['mods']}
    parents=[dict(id=k,source=by[k]['src'],licence=by[k]['licence']) for k in ids]
    held=next(float(r['L']) for r in __import__('csv').DictReader(open(details)) if int(r['n'])==n)
    original=F.fq_quench;exported=False

    def quench(side,P,flags=(),timeout=900):
        nonlocal exported
        if not exported:
            os.makedirs(raw,exist_ok=True);stem=raw+'/'+name+'-slp'
            Q=M.np.asarray(P,float);actual,gap=M.layout_state(Q)
            if len(Q)!=n or gap < -1e-7:raise ValueError('illegal early family layout')
            M.write_layout(stem+'.csv',n,Q)
            record=dict(library=pool,n=n,built=actual,predicted=math.isqrt(n-1)+f,start=actual,held=held,stacks=[s1,s2],squeeze='family-slp-before-fq',seconds={'family_slp':time.time()-start},modules=parents,early_stage=True)
            json.dump(record,open(stem+'.json.tmp','w'));os.replace(stem+'.json.tmp',stem+'.json')
            print('EARLY SLP',n,actual,'gap',gap,'seconds',time.time()-start,flush=True);exported=True
        return original(side,P,flags,timeout=min(timeout,120))

    F.fq_quench=quench
    try:
        result=M.cmd_job(args);path=raw+'/'+name+'.json'
        if os.path.exists(path):
            record=json.load(open(path));record['library']=pool
            json.dump(record,open(path+'.tmp','w'));os.replace(path+'.tmp',path)
        return result
    finally:F.fq_quench=original


if __name__=='__main__':
    a=sys.argv[1:]
    if a and a[0].endswith('/modules.py'):a=a[2:]
    run(a)
