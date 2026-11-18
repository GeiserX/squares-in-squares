#!/usr/bin/env python3
"""A full upright wall column beside a two-arm rectangle.

The wide reader finds this geometry in held 982: a 9-arm starts one column
inside the left wall. The inner rectangle has width L-1 and height L.
At m=floor(L), its grid loses m-c2+1 cells and the wall adds m cells.
For two arms of 9, rank n-8 with the corner's x length increased by one.
The exact assembler and the full square squeeze then check each prediction.

  stair-c_border.py control POOL
  stair-c_border.py queue POOL DETAILS.csv PREFIX
  stair-c_border.py seams POOL DETAILS.csv PREFIX
  stair-c_border.py alt POOL DETAILS.csv PREFIX
  stair-c_border.py repair POOL OUTPOOL
  stair-c_border.py repaired OUTPOOL DETAILS.csv PREFIX
  stair-c_border.py job POOL RAW DETAILS.csv NAME N C F1 F2 S1 S2 F SPLIT
"""
import csv,hashlib,json,math,os,pickle,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import modules as M
from modules_round22 import CLOSED_CORNERS, no_start_states
from modules import flush_tilt,far_at,corner_at,stack_squares,corner_slide,SLIDE
os.environ.setdefault('SQ_TMP',os.path.abspath('tmp'))
os.makedirs(os.environ['SQ_TMP'],exist_ok=True)

def wall_column(P,m,f,mode):
    if mode not in (-2,-3):
        return np.array([(.5,j+.5+(f*j/(m-1) if mode==-1 else f if j>=mode else 0.),0.) for j in range(m)])
    eps=.025 if mode==-2 else .0125
    points=[]
    for x,y,deg in P:
        if abs(deg)<.5:continue
        a=math.radians(deg);c,ss=math.cos(a),math.sin(a)
        v=np.array([(x+.5*(u*c-v*ss),y+.5*(u*ss+v*c)) for u,v in ((-1,-1),(1,-1),(1,1),(-1,1))])
        k=int(v[:,0].argmin())
        if abs(v[k,0]-1.)>1e-6:continue
        t=float(v[k,1]);i=math.floor(t)-1;phase=t-(i+1)
        if 0<=i<m-1 and eps<=phase<=f-eps:points.append((t,i,phase))
    points=sorted(set(points));paths=[]
    for k,(t,i,ph) in enumerate(points):
        prev=[j for j in range(k) if points[j][1]<i and points[j][2]+2*eps<=ph+1e-12]
        j=max(prev,key=lambda j:len(paths[j])) if prev else None
        paths.append((paths[j] if j is not None else [])+[k])
    pick=max(paths,key=len) if paths else []
    phase=np.zeros(m)
    for k in pick:
        _,i,ph=points[k];phase[i+1:]=np.maximum(phase[i+1:],ph+eps)
    phase[-1]=f
    col=np.c_[np.full(m,.5),np.arange(m)+.5+phase,np.zeros(m)]
    assert np.diff(col[:,1]).min()>=1.-1e-10 and col[:,1].max()<=m+f-.5+1e-10
    print('COLUMN',mode,'protected contacts',len(pick),'of',len(points),'epsilon',eps,'points',[round(points[k][0],6) for k in pick],flush=True)
    return col


def assemble(n, C, F1, F2, s1, s2, f, border=1, split=0):
    """The layout of one choice at f: modules at their LP positions, flush stacks, the rest. -> (array x, y, radians) or (None, why)"""
    m = math.isqrt(n - 1); L = m + f; width = L - border
    qc, q1, q2 = C['q'], F1['q'], F2['q']
    c1, c2 = qc['c1'], qc['c2']
    W1, W2 = c1 - 1 + f, c2 - 1 + f
    t1, t2 = flush_tilt(c1, f), flush_tilt(c2, f); p1, p2 = 1 / math.cos(t1), 1 / math.cos(t2)
    f1 = far_at(q1, f); f2 = far_at(q2, f)
    if f1 is None or f2 is None: return None, 'a far zone does not exist at f'
    co = corner_at(qc, f, L - f1[0] - s1 * p1, width - f2[0] - s2 * p2)
    if co is None: return None, 'the corner does not fit under both arms'
    y0, x0, Pc = co
    parts = [Pc]
    parts += [stack_squares(c1, qc['lean1'] * math.degrees(t1), W1 / 2, y0 + (j + .5) * p1) for j in range(s1)]
    parts += [stack_squares(c2, qc['lean2'] * math.degrees(t2), x0 + (j + .5) * p2, W2 / 2, along_x=False) for j in range(s2)]
    ni, nj = m - c1 + 1 - border, m - c2 + 1
    gone = set(map(tuple, qc['miss']))
    a = f1[1].copy()
    if q1['lean'] != -qc['lean1']: a[:, 0] = W1 - a[:, 0]; a[:, 2] = -a[:, 2]
    parts.append(np.c_[a[:, 0], L - a[:, 1], -a[:, 2]]); gone |= {(i, nj - 1 - j) for i, j in q1['miss']}
    a = f2[1].copy()
    if q2['lean'] != qc['lean2']: a[:, 0] = W2 - a[:, 0]; a[:, 2] = -a[:, 2]
    parts.append(np.c_[width - a[:, 1], a[:, 0], a[:, 2]]); gone |= {(ni - 1 - i, j) for j, i in q2['miss']}
    # the rest: on the grid, but row 0 and column 0 keep the slide of the corner (its found places, then its grant
    # all along the run) and, beside a far zone that pokes, the found places of that zone
    cs = corner_slide(qc)
    off = {(i, 0): cs(i, 0) for i in range(ni)}; off.update({(0, j): cs(0, j) for j in range(1, nj)})
    if SLIDE:
        for far, arm, fl, nn, grant in ((q2, 2, f2[0], ni, qc.get('g2', 0.0)), (q1, 1, f1[0], nj, qc.get('g1', 0.0))):
            if far.get('slide') is None: continue
            sl = far['slide']
            reach = int(math.ceil(fl + far['c'] * math.sin(flush_tilt(far['c'], f)) + 2.5))     # the cells far_state holds
            for j in range(min(len(sl), nn - 1, reach)):
                if arm == 2: off[(ni - 1 - j, 0)] = (-float(sl[j]), 0.0)
                else: off[(0, nj - 1 - j)] = (0.0, -float(sl[j]))
        # along the row (the column) no cell may stand further towards the corner than the cell before it
        if any(off[(i + 1, 0)][0] < off[(i, 0)][0] - 1e-9 for i in range(ni - 1) if (i, 0) not in gone and (i + 1, 0) not in gone) or \
           any(off[(0, j + 1)][1] < off[(0, j)][1] - 1e-9 for j in range(nj - 1) if (0, j) not in gone and (0, j + 1) not in gone):
            return None, 'the corner grants a far zone no slide'
    parts.append(np.array([(W1 + .5 + i + off.get((i, j), (0.0, 0.0))[0], W2 + .5 + j + off.get((i, j), (0.0, 0.0))[1], 0.0)
                           for i in range(ni) for j in range(nj) if (i, j) not in gone]))
    P = np.vstack(parts)
    if border:
        P[:, 0] += border
        col = wall_column(P,m,f,split)
        P = np.vstack([P, col])
    P[:, 2] = np.radians(P[:, 2])
    if len(P) != n: return None, 'holds %d squares' % len(P)
    return P, None


def control(pool):
    lib=M.Library(pool);D=pickle.load(open(pool+'/library.pkl','rb'))
    l=next(l for l in D['layouts'] if l['n']==975 and l['tag']=='tw17')
    F1,F2,C=[lib.byid[k] for k in l['ids_slide']];f=l['f']+.0001
    P,why=assemble(975,C,F1,F2,l['s1'],l['s2'],f,border=0)
    Q,why0=M.assemble(None,975,C,F1,F2,l['s1'],l['s2'],f)
    if P is None or Q is None:raise RuntimeError(('square control',why,why0))
    delta=float(np.max(np.abs(P-Q)));side,gap=M.layout_state(P)
    print('CONTROL square975',len(P),'source',l['s'],'side',side,'gap',gap,'maxdiff',delta,flush=True)
    assert len(P)==975 and delta<1e-10 and gap>=-1e-7 and side<l['s']+.0015
    for split in (0,l['m'],-1,-2,-3):
        P,why=assemble(974,C,F1,F2,l['s1'],l['s2']-1,f,border=1,split=split)
        if P is None:raise RuntimeError(('rectangle control',why))
        side,gap=M.layout_state(P)
        print('CONTROL bordered974',len(P),'split',split,'side',side,'gap',gap,flush=True)
        assert len(P)==974 and gap>=-1e-7 and side<l['s']+.0015


def queue(pool,details,prefix,seams=False,alternate=False,repaired=False):
    held={int(r['n']):float(r['L']) for r in csv.DictReader(open(details))}
    blocked,_=no_start_states()
    print('REFUSED corner states',len(blocked),sorted(CLOSED_CORNERS),flush=True)
    lib=M.Library(pool,only=lambda q:q['id'] not in blocked and M.usable(q) and (q['kind']=='far' and q['c']==9 or q['kind']=='corner' and q['c1']==q['c2']==9 and (not repaired or q['id'].startswith('sc22repaired-'))))
    for C in lib.corners:
        C['X']=C['X']+1.
        C['kin']=(C['kin'],C['lean1'],C['lean2'])
    rows=[];jobs=[]
    ns=[803,804,860,863,919,921,924,982,984,987] if alternate else [921,860,919,982,984] if seams else [803,804,860,863,919,921,924,982,984,987]
    for n in ns:
        m=math.isqrt(n-1);fbar=held[n]-m
        got=lib.best(n-8,top=32 if alternate else 1,below=fbar+.025,distinct=True,depth=.065)
        if alternate and got:
            seen=set();chosen=[];limit=got[0][0]+.008
            for row in got:
                q=row[2]['q'];kin=(M.kin(q),q['lean1'],q['lean2'])
                if kin in seen or row[0]>limit:continue
                seen.add(kin);chosen.append(row)
                if len(chosen)==3:break
            got=chosen
        for f,stop,C,F1,F2,s1,s2 in got:
            r=dict(n=n,predicted=m+f,held=held[n],margin=m+f-held[n],corner=C['id'],far1=F1['id'],far2=F2['id'],s1=s1,s2=s2,f=f)
            rows.append(r);print('ROW',r,flush=True)
            for split in ((-1,) if alternate or repaired else (-2,-3) if seams else (0,m,-1)):
                key=repr((n,C['id'],F1['id'],F2['id'],s1,s2,f,split))
                name='%d-brect%s'%(n,hashlib.sha256(key.encode()).hexdigest()[:9])
                cmd='./py -I lane/stair-c_border.py job %s raw-a details-r20.csv %s %d %s %s %s %d %d %r %d'%(pool,name,n,C['id'],F1['id'],F2['id'],s1,s2,f,split)
                jobs.append('follow-'+name+' '+cmd+'\n')
    with open(prefix+'.tsv','w') as h:
        w=csv.DictWriter(h,fieldnames=['n','predicted','held','margin','corner','far1','far2','s1','s2','f'],delimiter='\t');w.writeheader();w.writerows(rows)
    margins={r['n']:r['margin'] for r in rows}
    jobs.sort(key=lambda s:(margins[int(s.split()[0].split('-')[1])],int(s.split()[-1])!=-1))
    open(prefix+'-jobs.txt','w').writelines(jobs)
    print('QUEUED',len(rows),'rows',len(jobs),'builds',flush=True)


def job(a):
    pool,raw,details,name=a[:4];n=int(a[4]);ic,i1,i2=a[5:8];s1,s2=int(a[8]),int(a[9]);f=float(a[10]);split=int(a[11]);lib=M.Library(pool)
    C,F1,F2=[lib.byid[k] for k in (ic,i1,i2)];H={int(r['n']):float(r['L']) for r in csv.DictReader(open(details))};os.makedirs(raw,exist_ok=True)
    P=None;why=''
    for up in (.0002,.0006,.0015,.003):
        P,why=assemble(n,C,F1,F2,s1,s2,f+up,split=split)
        if P is not None:
            side,gap=M.layout_state(P)
            if gap>=-1e-7 and side<=math.isqrt(n-1)+f+up+1e-6:break
            why='side %r gap %r'%(side,gap);P=None
    if P is None:
        print('NO START',n,why,flush=True);json.dump(dict(n=n,built=None,why=why,predicted=math.isqrt(n-1)+f,ids=[ic,i1,i2]),open(raw+'/'+name+'.nostart','w'));return
    print('START',n,'side',side,'gap',gap,'held',H[n],flush=True);t=time.time()
    Q,L=M._squeeze_family(n,P,os.environ.get('SQ_FQ'),log=lambda s:print(s,flush=True))
    M.write_layout(raw+'/'+name+'.csv',n,Q)
    mods=[dict(id=q['id'],source='one upright wall column and a two-arm rectangle: '+q['q']['src'],licence=q['q']['licence']) for q in (C,F1,F2)]
    json.dump(dict(n=n,predicted=math.isqrt(n-1)+f,start=side,built=L,held=H[n],stacks=[s1,s2],squeeze='family',seconds={'family':time.time()-t},modules=mods,construction='bordered rectangle',border_split=split),open(raw+'/'+name+'.json','w'))
    print('BUILT',n,L,'held delta',L-H[n],flush=True)


def repair(pool,out):
    import zone_corner as Z
    L=pickle.load(open(pool+'/library.pkl','rb'));E=pickle.load(open(pool+'/lens.pkl','rb'));new=[];records=[]
    for q in list(L['mods']):
        if q['id'] not in ('803fa19.Ct','803in20.Ct'):continue
        if q['miss'] or len(q['P'])!=q['count']:raise RuntimeError('repair needs a plain corner')
        before=Z.check_corner(q);mod=Z.cmod(q['c1'],q['c2'],q['lean1'],q['lean2'])
        r=Z.settle_zone(q['P'],mod,q['f0'],q['y0']+.02,q['x0']+.02)
        if r is None:print('REPAIR REFUSED',q['id'],before,flush=True);continue
        y,x,P=r;v=Z.as_module(P,mod,q['f0'],y,x,'sc22repaired-'+q['id'],'repair the stored turned corner at its own f',q);v['ours']=True
        after=Z.check_corner(v)
        print('REPAIR',q['id'],'count',len(P),'loss',q['loss0'],'to',v['loss0'],'before',before,'after',after,flush=True)
        if not after[0] or len(P)!=q['count'] or v['loss0']>q['loss0']+.2:
            print('REPAIR distortion refused',q['id'],flush=True);continue
        t=M.tabulate(v);L['mods'].append(v);E[v['id']]=t;new.append(v['id']);records.append(dict(source=q['id'],new=v['id'],count=len(P),loss=v['loss0']))
    os.makedirs(out,exist_ok=True);pickle.dump(L,open(out+'/library.pkl','wb'));pickle.dump(E,open(out+'/lens.pkl','wb'));json.dump(records,open(out+'/repair-results.json','w'),indent=2)
    print('REPAIRED strict corner modules',new,flush=True)


def main():
    a=sys.argv[1:]
    if not a:
        print(__doc__);return
    if a[0]=='control':control(a[1])
    elif a[0]=='queue':queue(*a[1:])
    elif a[0]=='seams':queue(*a[1:],seams=True)
    elif a[0]=='alt':queue(*a[1:],alternate=True)
    elif a[0]=='repair':repair(*a[1:])
    elif a[0]=='repaired':queue(*a[1:],repaired=True)
    elif a[0]=='job':job(a[1:])
    else:raise ValueError(a[0])
if __name__=='__main__':main()
