"""Move whole flush stacks into a corner before tabulation."""
import copy,hashlib,json,math,os,pickle,sys
sys.path[:0]=['lane','.']
import modules as M

def expand(d,a,b):
    out=copy.deepcopy(d)
    for arm,amount,axis in [(1,a,'y'),(2,b,'x')]:
        if not amount:continue
        assert out['s'+str(arm)]>amount,'no run left'
        start=d[axis+'0'];pitch=d['p'+str(arm)]
        take=(d['zone']=='S'+str(arm))&(d['sig'+str(arm)]<start+amount*pitch)
        assert int(take.sum())==amount*d['c'+str(arm)],'incomplete transferred stack'
        out['zone'][take]='C';out[axis+'0']=start+amount*pitch
        out['s'+str(arm)]-=amount
    assert len(out['zone'])==d['n']
    return out

def corner(d,source,licence,tag):
    mods=M.modules_of(d,source,licence,tag);twins,ids=M.slid(d,mods)
    by={q['id']:q for q in mods+twins}
    return by[ids[2]],by[ids[0]],by[ids[1]]

def control():
    n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
    for a,b in [(0,0),(1,0),(0,1),(1,1)]:
        e=expand(d,a,b);C,F1,F2=corner(e,'own construction: expansion control','our own','r31-control')
        P,why=M.assemble(None,n,dict(q=C),dict(q=F1),dict(q=F2),e['s1'],e['s2'],e['f'])
        assert P is not None,why
        side,gap=M.layout_state(P)
        assert gap>=-1e-7 and side<=d['s']+2e-6,(a,b,side,gap,d['s'])
        print('CONTROL expanded975',a,b,'side',side,'gap',gap,'corner squares',len(C['P']),flush=True)
    bad=copy.deepcopy(d);bad['zone'][M.np.nonzero(bad['zone']=='S1')[0][0]]='C'
    try:expand(bad,1,0)
    except AssertionError:pass
    else:raise AssertionError('partial-stack mutant passed')
    print('CONTROL partial-stack mutant refused',flush=True)
    open('expanded-control.json','w').write(json.dumps(dict(passed=True,n=975,variants=4)))

if __name__=='__main__':
    if sys.argv[1]=='--control':control();raise SystemExit
    assert json.load(open('expanded-control.json'))['passed'],'control not passed'
    path=sys.argv[1];meta=json.load(open(path+'.json'));n=meta['n'];payload=open(path,'rb').read();digest=hashlib.sha256(payload).hexdigest()
    sq=M.np.asarray(M.read_layouts(path)[n],float);d,why=M.cut(sq,n);assert d is not None,why
    folder='inbox';os.makedirs(folder,exist_ok=True)
    for a,b in [(1,0),(0,1),(1,1),(2,0),(0,2)]:
        try:e=expand(d,a,b)
        except AssertionError:continue
        C,_,_=corner(e,meta['source']+'; whole-stack transfer to corner '+str((a,b)),meta['licence'],'r30expand'+digest[:12]+str(a)+str(b))
        C['turn']=True;C['ours']=True
        name=f'r31-live-expanded-{n}-{digest[:12]}-{a}{b}.pkl'
        pickle.dump(dict(mods=[C],lens={},origin='expanded corner from pinned packing'),open(folder+'/'+name,'wb'))
        print('EXPANDED',n,a,b,'corner',C['id'],'squares',len(C['P']),'loss',C['loss0'],flush=True)
