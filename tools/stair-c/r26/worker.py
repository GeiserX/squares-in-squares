"""One serial remote worker: fresh modules, bounded ranking, builds and quenches."""
import csv,glob,hashlib,importlib.util,json,math,os,pickle,subprocess,sys,time,traceback
sys.path[:0]=['lane','.']
os.environ['SQ_FQ']=os.path.abspath('fq')
assert os.path.isfile(os.environ['SQ_FQ']) and os.access(os.environ['SQ_FQ'],os.X_OK)
import modules as M
from prepare import fingerprint
spec=importlib.util.spec_from_file_location('rank','lane/stair-c_rank.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
open('worker.pid','w').write(str(os.getpid()))
DEAD=float(open('deadline').read());PART=int(sys.argv[1]);H={int(r['n']):r for r in csv.DictReader(open('details.csv'))}
BOARD={int(r['n']):float(r['board_L']) for r in csv.DictReader(open('gap.tsv'),delimiter='\t')}
TARGETS=[n for n in H if 28<=math.isqrt(n-1)<=31 and 17<=n-math.isqrt(n-1)**2<=45 and n%3==PART]
for d in ['raw-a','final','cert-in','logs','done','tables']:os.makedirs(d,exist_ok=True)
def stamp():return time.strftime('%FT%TZ',time.gmtime())
def save(p,data):
    with open(p+'.tmp','wb') as h:pickle.dump(data,h)
    os.replace(p+'.tmp',p)
def log(*a):print(stamp(),*a,flush=True)
def state():return pickle.load(open('state.pkl','rb')) if os.path.exists('state.pkl') else dict(imported=set(),rank=[],build=[],fresh=set(),recipes=set(),fingerprints=set(),built=0)
def checkpoint():save('state.pkl',S)
def run(cmd,name,limit):
    end=DEAD if name.startswith('quench-') else min(DEAD,float(open('search-deadline').read()))
    remain=end-time.time()
    if remain<5:return False
    with open('logs/'+name+'.log','a') as h:
        p=subprocess.Popen(cmd,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
        try:rc=p.wait(timeout=min(limit,remain))
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            rc=124
    log('COMMAND',name,'rc',rc);return rc==0

def control():
    # A control with nonempty exact geometry, plus a changed packing that must fail.
    spec=importlib.util.spec_from_file_location('border','lane/stair-c_border.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
    B.control('libbase')
    a=M.Library('libbase');b=R.FreshLibrary('libbase')
    l=next(x for x in a.layouts if x['n']==975 and x['tag']=='tw17');need={l['ids_slide'][0]}
    corners={l['ids_slide'][2]};only=lambda q:q['kind']=='far' or q['id'] in corners
    a=M.Library('libbase',only=only);b=R.FreshLibrary('libbase',only=only)
    key=lambda rs:[(r[0],r[1],r[2]['id'],r[3]['id'],r[4]['id'],r[5],r[6]) for r in rs]
    x=a.best(975,top=2,below=.78,need=need,depth=.10);y=b.best(975,top=2,below=.78,need=need,depth=.10)
    assert x and key(x)==key(y)
    assert b.best(975,need={'missing-state'},below=.78,depth=.10)==[]
    q=M.np.asarray(M.read_layouts('control975.csv')[975],float);q[1]=q[0]
    assert M.layout_state(q)[1]<-.99
    log('CONTROL exact975/974 passed; fresh join identical',len(x),'rows; missing module rejected; duplicate square rejected')

def import_patch(p):
    log('IMPORT START',p,'deadline',DEAD)
    if p.endswith('.csv'):
        import numpy as np
        meta=json.load(open(p+'.json'));n=meta['n'];d,why=M.cut(np.asarray(M.read_layouts(p)[n],float),n)
        if d is None:
            S['imported'].add(os.path.basename(p));checkpoint();log('UNREADABLE',p,why);return
        tag='r26d'+hashlib.sha256(open(p,'rb').read()).hexdigest()[:12]
        data=dict(mods=M.modules_of(d,meta['source'],meta['licence'],tag),lens={},origin='round25')
    else:data=pickle.load(open(p,'rb'))
    remaining=[q for q in data['mods'] if fingerprint(q) not in S['fingerprints']]
    if len(remaining)>3:
        rest=remaining[3:];name='r26-cont-'+hashlib.sha256((p+str(len(rest))).encode()).hexdigest()[:12]+'.pkl'
        save('inbox/'+name,dict(data,mods=rest,lens={q['id']:data.get('lens',{}).get(q['id']) for q in rest if data.get('lens',{}).get(q['id']) is not None}))
        os.utime('inbox/'+name,(1,1))
        data=dict(data,mods=remaining[:3])
    ids=[]
    data['mods']=[q for q in data['mods'] if not any(x in q['src'] for x in EXCLUDED)]
    for q in data['mods']:
        fp=fingerprint(q)
        if fp in S['fingerprints']:continue
        q=dict(q,ours=True);ids.append(q['id']);S['fingerprints'].add(fp)
        L['mods'].append(q)
        t=data.get('lens',{}).get(q['id'])
        if t is None:
            start=time.time();t=M.tabulate(q);log('TABLE',q['id'],'seconds',time.time()-start)
        E[q['id']]=dict(t,id=q['id'])
    save('libbase/library.pkl',L);save('libbase/lens.pkl',E)
    save('tables/'+os.path.basename(p).replace('.csv','.pkl'),dict(mods=[q for q in L['mods'] if q['id'] in ids],lens={k:E[k] for k in ids},origin=data.get('origin')))
    if data.get('origin')!='candidate' or os.path.basename(p).startswith(('a-','r26-priority-')):S['fresh'].update(ids)
    need=set(ids)
    # Initial accepted donors may combine with every clean base module. Later base
    # additions must use a fresh donor, so an old-only combination never enters.
    if data.get('origin')=='candidate' and os.path.basename(p).startswith('b-'):need=set(S['fresh'])
    mid=data['mods'][0]['f0'] if data['mods'] else .85
    ns=sorted(TARGETS,key=lambda n:(abs((float(H[n]['L'])-math.isqrt(n-1))-mid),-(float(H[n]['L'])-BOARD[n])/math.sqrt(n)))
    if need:S['rank'].insert(0,dict(need=need,ns=ns,patch=os.path.basename(p)))
    S['imported'].add(os.path.basename(p));checkpoint();log('IMPORTED',p,len(ids),'fresh total',len(S['fresh']))
    if need:rank_chunk()

def rank_chunk():
    index=next((i for i,q in enumerate(S['rank']) if q['patch']=='r26-priority-935.pkl'),0)
    task=S['rank'].pop(index);S['rank'].append(task);lib=R.FreshLibrary('libbase',only=M.usable);start=time.time();processed=0
    while task['ns'] and time.time()-start<40 and time.time()<DEAD-30:
        n=task['ns'].pop(0);m=math.isqrt(n-1);held=float(H[n]['L']);bar=held
        if os.path.exists('bar.json'):bar=min(bar,float(json.load(open('bar.json')).get(str(n),held)))
        rows=lib.best(n,top=2,below=bar-m+.014,need=task['need'],distinct=True,depth=.035)
        for f,stop,C,F1,F2,s1,s2 in rows:
            if m+f>bar+.008:continue
            qs=[C['q'],F1['q'],F2['q']]
            recipe=(n,*[fingerprint(q) for q in qs],s1,s2)
            if recipe in S['recipes']:continue
            S['recipes'].add(recipe);name=str(n)+'-r26-'+hashlib.sha256(repr(recipe).encode()).hexdigest()[:12]
            S['build'].append(dict(n=n,ids=[q['id'] for q in qs],stacks=[s1,s2],f=f,name=name,predicted=m+f,bar=bar,patch=task['patch']))
        log('RANK',task['patch'],n,'rows',len(rows),'pending builds',len(S['build']));processed+=1
    if not task['ns']:S['rank'].remove(task)
    S['build'].sort(key=lambda j: (j['predicted']-j['bar'],-(float(H[j['n']]['L'])-BOARD[j['n']])/math.sqrt(j['n'])))
    checkpoint()

CAP=8;CLOSE=.002
def build():
    # Round 26: round 25 spent about 200 builds each on 921, 985 and 922 at one floor.
    # After CAP builds of one n that end with no gain, drop its rows unless they
    # predict a side within CLOSE of the bar. Rows of fresh donors at 805, 934 and
    # 997 sit within 0.001 of the bar and must keep their builds.
    nogain=S.setdefault('nogain',{})
    # After 3 CAP no-gain builds of one n, only rows that predict a side below the bar
    # build. At 15:15Z boxC had built 873 42 times with no gain on rows +6e-5 to +1e-4.
    def stale(j):
        k=nogain.get(j['n'],0);d=j['predicted']-j['bar']
        return (k>=CAP and d>CLOSE) or (k>=3*CAP and d>=0)
    while S['build'] and stale(S['build'][0]):
        k=S['build'].pop(0);log('SKIP floor',k['name'],'builds without gain',nogain[k['n']])
    if not S['build']:checkpoint();return
    j=S['build'].pop(0);checkpoint();name=j['name'];n=j['n']
    cmd=[sys.executable,'-I','lane/stair-c_job.py','lane/modules.py','job','libbase','raw-a','details.csv',name,str(n),*j['ids'],*map(str,j['stacks']),repr(j['f']),'--fq','./fq','--squeeze','family']
    log('BUILD',name,'delta',j['predicted']-j['bar'],'patch',j['patch']);run(cmd,name,600);S['built']+=1
    sides=[]
    for p in glob.glob('raw-a/'+name+'*.json'):
        try:sides.append(json.load(open(p))['built'])
        except (OSError,ValueError,KeyError,TypeError):pass
    sides=[x for x in sides if x is not None]
    if not sides or min(sides)>j['bar']-1e-8:nogain[n]=nogain.get(n,0)+1
    checkpoint()

def quench():
    for p in sorted(glob.glob('cert-in/*.csv')):
        name=os.path.basename(p)[:-4]
        if os.path.exists('done/quench-'+name):continue
        run([sys.executable,'-I','quench22.py',p,'final/'+name+'.csv'],'quench-'+name,250)
        open('done/quench-'+name,'w').write(stamp());return True
    return False

S=state();L=pickle.load(open('libbase/library.pkl','rb'));E=pickle.load(open('libbase/lens.pkl','rb'))
fixture=pickle.load(open('control-fixture.pkl','rb'));controlids={q['id'] for q in fixture['mods']}
by={q['id']:q for q in L['mods']};by.update({q['id']:q for q in fixture['mods']});L['mods']=list(by.values());E.update(fixture['lens'])
DROP=('921-29e12ff3','921r25c921','921mo16.F1d','985-r25-ba842328a07b','Samanyu-dev','squares_in_squares','verified-best-of-1105','joegun-boxed')
allowed=[]
for q in L['mods']:
    src=q['src']
    independent='held' not in src and 'take-' not in src and not src.startswith('stair-c')
    current='clean held gather/round23-2026-11-13b.csv' in src or 'clean held gather/round25-2026-11-14b.csv' in src or 'immutable sha256' in src
    if any(t in src or t in q.get('tag','') or t in q['id'] for t in DROP):continue
    if independent or current or q['id'] in controlids:allowed.append(q)
log('SOURCE FILTER',len(L['mods']),'to',len(allowed),'explicit roots or current accepted donors')
L['mods']=allowed;allowedids={q['id'] for q in allowed};E={k:v for k,v in E.items() if k in allowedids}
S['build']=[j for j in S['build'] if set(j['ids'])<=allowedids]
save('libbase/library.pkl',L);save('libbase/lens.pkl',E)
S['fingerprints']={fingerprint(q) for q in L['mods']}
S['fresh'].update(q['id'] for q in L['mods'] if q.get('tag','').startswith('r26c'))
if os.path.exists('prior-recipes.pkl'):
    history=pickle.load(open('prior-recipes.pkl','rb'));by={q['id']:q for q in L['mods']};old=len(S['build'])
    def prior(j):return (j['n'],*[fingerprint(by[k]) for k in j['ids']],*j['stacks']) in history
    S['build']=[j for j in S['build'] if not prior(j)];S['recipes'].update(history)
    log('PRIOR RECIPES',len(history),'completed exclusions;',old-len(S['build']),'queued repeats removed')
if not os.path.exists('CONTROL_PASS'):
    control();open('CONTROL_PASS','w').write(stamp())
EXCLUDED=[]
def apply_exclusions():
    global EXCLUDED
    paths=json.load(open('excluded-paths.json')) if os.path.exists('excluded-paths.json') else []
    if paths==EXCLUDED:return
    EXCLUDED=paths;bad={q['id'] for q in L['mods'] if any(x in q['src'] for x in paths)}
    S['fingerprints'].difference_update(fingerprint(q) for q in L['mods'] if q['id'] in bad)
    L['mods']=[q for q in L['mods'] if q['id'] not in bad]
    for k in bad:E.pop(k,None)
    S['fresh'].difference_update(bad);S['build']=[j for j in S['build'] if not bad.intersection(j['ids'])]
    for j in S['rank']:j['need'].difference_update(bad)
    S['rank']=[j for j in S['rank'] if j['need']]
    save('libbase/library.pkl',L);save('libbase/lens.pkl',E);checkpoint();log('WITHDRAW FILTER',len(bad),'module states removed')
def fresh_first(paths,builds):
    if not paths or not os.path.basename(paths[0]).startswith(('r26-priority-','r26-live-')):return False
    return not builds or builds[0]['predicted']-builds[0]['bar']>CLOSE
turn=0
while time.time()<DEAD and not os.path.exists('STOP'):
    try:
        apply_exclusions()
        if quench():continue
        if time.time()>float(open('search-deadline').read()):time.sleep(3);continue
        commands=[p for p in sorted(glob.glob('requests/*.json')) if not os.path.exists('done/'+os.path.basename(p))]
        if commands and turn%3==0:
            p=commands[0];j=json.load(open(p));run(j['command'],j['name'],j.get('limit',300));open('done/'+os.path.basename(p),'w').write(stamp());turn+=1;continue
        paths=[p for p in sorted(glob.glob('inbox/*.pkl')+glob.glob('inbox/*.csv')) if os.path.basename(p) not in S['imported']]
        # New handoffs always precede saved accepted donors and older ranking.
        paths.sort(key=lambda p:(0 if os.path.basename(p).startswith('r26-priority-') else 1 if os.path.basename(p).startswith('r26-live-') else 2 if os.path.basename(p).startswith('r26-') else 3 if os.path.basename(p).startswith('a-') else 4, {'r26-priority-935.pkl':0,'r26-priority-876.pkl':1,'a-935.pkl':0,'a-876.pkl':1,'a-503.pkl':2}.get(os.path.basename(p),3),-os.path.getmtime(p)))
        # Round 26 (second agent): on 13:45Z each box held 35 to 37 unimported fresh
        # packages, because imports ran on 2 turns of 12 while the queue built rows
        # predicted 0.003 to 0.008 above the bar (29 such builds, none closer than
        # +1.0e-3). A fresh package now goes first unless the top build is close.
        if fresh_first(paths,S['build']):
            import_patch(paths[0])
        elif paths and (turn%4==0 or not S['rank'] and not S['build']):
            import_patch(paths[0])
        elif S['build'] and turn%3!=0:build()
        elif S['rank']:rank_chunk()
        elif S['build']:build()
        elif paths:import_patch(paths[0])
        else:time.sleep(5)
        turn+=1
    except Exception:
        traceback.print_exc();checkpoint();time.sleep(5)
log('STOPPED','builds',S['built'],'pending',len(S['build']),'rank',len(S['rank']));checkpoint()
