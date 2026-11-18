"""Copy fresh designs, publish near starts and certify the remote worker outputs."""
import signal,csv,datetime,glob,hashlib,json,math,os,pickle,re,shutil,subprocess,sys,time,traceback
ROOT='$SCRATCH/bounties-squares';TAKE=ROOT+'/take-stair-c-r28';WORK=TAKE+'/work';LANE='.'
sys.path[:0]=[str(__import__('pathlib').Path(__file__).resolve().parent),LANE]
import floatsafe
import modules as M
from provenance import clean, audit, held_record, pin, upstream_notices, derive_credit
from prepare import fingerprint
import share27
import cert_cache
import whole
import rectangle3
from ancestors import audit as ancestor_shares
csv.field_size_limit(64*1024*1024)
HOSTS=[('boxC','n'),('boxD','m'),('boxE','s')]
# Round 27: the base bar is round28-briefs/bar28.tsv (held r25 b or the best certified r26 take row).
H={int(r['n']):float(r['bar']) for r in csv.DictReader(open(ROOT+'/round28-briefs/bar28.tsv'),delimiter='\t')}
END=datetime.datetime(2026,11,15,5,44,tzinfo=datetime.timezone.utc).timestamp();FEEDEND=datetime.datetime(2026,11,15,5,25,tzinfo=datetime.timezone.utc).timestamp()
# Round 27: Samanyu markers out (override 2); the other roots stay out.
BAD=re.compile(r'verified-best-of-1105|penguin069/squares-joegun-boxed-certified-union|take-harvest-r22/(?:near/)?(?:639|691|745|858|918)(?!\d)|take-forensics-r23[^\n]*980|take-forensics-r2[123][^\n]*918')
STATE=WORK+'/coord-state.json'
S=json.load(open(STATE)) if os.path.exists(STATE) else dict(seen=[],handed=[],feed=[],queued=[],published=[])
for k in S:S[k]=set(S[k])
S.setdefault('native',set())
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def state(text):
    with open(TAKE+'/STATE.txt','a') as h:h.write(stamp()+' boxA '+text+'\n')
def hand(text):
    with open(ROOT+'/handoff-r28.log','a') as h:h.write(stamp()+' stair-c -> all: '+text+'\n')
def save():
    json.dump({k:sorted(v) for k,v in S.items()},open(STATE+'.tmp','w'));os.replace(STATE+'.tmp',STATE)
def run(args):
    # Round 26: a slow box must not stop the collection of the other two.
    try:return subprocess.run(args,capture_output=True,text=True,timeout=50)
    except subprocess.TimeoutExpired:return subprocess.CompletedProcess(args,124,'','timeout')
def rows(p):return [{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
def write(p,rr):
    with open(p+'.tmp','w') as h:
        w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rr)
    os.replace(p+'.tmp',p)
def exclusions():
    lines=[x for x in open(ROOT+'/handoff-r28.log') if re.search(r'->[^:]+:\s*(?:WITHDRAW|WITHHOLD)\b',x,re.I)] if os.path.exists(ROOT+'/handoff-r28.log') else []
    lines=[x for x in lines if not re.search(r'share|seed|own',x,re.I) or re.search(r'verified-best-of-1105|CC BY-SA|missing|rewrit|changed',x,re.I)]
    return sorted({p for x in lines for p in re.findall(r'$SCRATCH/bounties-squares/take-[^\s,;]+\.csv',x)})
def direct_public(path,source):
    if not source.lstrip().lower().startswith('samanyu-dev/squares_in_squares') and re.match(r'^[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+',source.lstrip()):return True
    if re.search(r'own construction|own design|independent|stair-c|Samanyu-dev|seed merged0',source,re.I):return False
    return 'take-harvest-' in path or bool(re.search(r'/(?:data/(?:nb|ds)|public)/',path))

def manifest(j):
    mods=j['modules']
    if not mods or not all(clean(q['source'],q['licence']) for q in mods):raise ValueError('excluded or unresolved ancestry')
    src=('stair-c round28 whole-layout kick and fq follow: ' if j.get('source_kick',{}).get('invoked') else 'stair-c round28 whole-layout fq follow: ' if j.get('whole_layout_follow') else 'stair-c round28 composition: ')+', '.join(q['id']+' <'+q['source']+'>' for q in mods)
    lic='; '.join(sorted({q['licence'] for q in mods}))
    try:actual=upstream_notices(src,lic)
    except ValueError:
        extra=derive_credit(src+' '+lic)
        if not extra:raise
        src+='; '+' | '.join(extra);lic+='; '+' | '.join(extra);actual=upstream_notices(src,lic)
    if actual:
        credit=' | '.join(actual);src+='; Upstream per-n records: '+credit;lic+='; Upstream per-n records: '+credit
    return dict(j,source=src,licence=lic)

def basebar():
    global H
    b=dict(H)
    lines=[x for x in open(ROOT+'/handoff-r28.log') if 'main -> all: BASE ' in x] if os.path.exists(ROOT+'/handoff-r28.log') else []
    if lines:
        for p in re.findall(r'(?:$SCRATCH/bounties-squares/)?gate/[^\s,;]+',lines[-1]):
            p=p.rstrip('.');p=p if p.startswith('/') else ROOT+'/'+p
            if os.path.isdir(p):p+='/details.csv'
            if os.path.exists(p):
                for r in csv.DictReader(open(p)):
                    n=int(r['n']);b[n]=min(b[n],float(r['score']))
                break
    return b

PEER_CACHE={}
def peer_scores(path):
    st=os.stat(path);token=(st.st_mtime_ns,st.st_size)
    prior=PEER_CACHE.get(path)
    if prior and prior[0]==token:return prior[1]
    values=[]
    for r in csv.DictReader(open(path),delimiter='\t'):
        try:values.append((int(r['n']),float(r['new'])))
        except (ValueError,KeyError):pass
    PEER_CACHE[path]=(token,values)
    return values

def bar():
    b=basebar()
    for p in glob.glob(ROOT+'/take-*-r28/take.tsv'):
        if p==TAKE+'/take.tsv':continue
        try:
            for n,score in peer_scores(p):b[n]=min(b[n],score)
        except FileNotFoundError:continue
    return b

def admission_timeout(*args):raise TimeoutError('source admission20s')
signal.signal(signal.SIGALRM,admission_timeout)
def bounded_audit(function,*args):
    signal.setitimer(signal.ITIMER_REAL,20)
    try:return function(*args)
    except TimeoutError:
        state('DEFER bounded full source walk '+str(args[0])[:240]);return None
    finally:signal.setitimer(signal.ITIMER_REAL,0)

FULL_ADMISSIONS={}
def full_admission(path,n,meta):
    payload=open(path,'rb').read()
    key=hashlib.sha256(payload+meta['source'].encode()+meta['licence'].encode()).hexdigest()
    cached=FULL_ADMISSIONS.get(key)
    if cached and (cached[1] is not None or time.time()-cached[0]<600):return cached[1]
    record=bounded_audit(audit,path,n,meta['source'],meta['licence'])
    FULL_ADMISSIONS[key]=(time.time(),record)
    if len(FULL_ADMISSIONS)>64:FULL_ADMISSIONS.pop(next(iter(FULL_ADMISSIONS)))
    if record is None:state('DEFER unresolved full CSV ancestry '+path)
    return record

def source_retry_key(path,key):
    files=[path+'.json',path[:-4]+'.json',os.path.dirname(os.path.dirname(path) if os.path.basename(os.path.dirname(path))=='near' else path)+'/take.tsv']
    versions=[]
    for f in files:
        try:st=os.stat(f);versions.append((f,st.st_mtime_ns,st.st_size))
        except OSError:pass
    return 'source-retry:'+key+':'+hashlib.sha256(repr((versions,int(time.time()/600))).encode()).hexdigest()[:16]

def feed():
    if time.time()>FEEDEND:return
    feed_started=time.time();feed_bar=bar()
    excluded=exclusions()
    json.dump(excluded,open(WORK+'/excluded-paths.json','w'))
    for host,_ in HOSTS:run(['rsync','-az',WORK+'/excluded-paths.json',host+':scratch/squares-stair-c/excluded-paths.json'])
    admitted=0
    # Hash versions so a changed geometry is fresh even if its side is unchanged.
    handoff=open(ROOT+'/handoff-r28.log').read() if os.path.exists(ROOT+'/handoff-r28.log') else ''
    direct=re.findall(r'$SCRATCH/bounties-squares/take-[^\s,;]+-r28/[^\s,;]+\.csv',handoff)
    paths=set(glob.glob(ROOT+'/take-*-r28/*.csv')+glob.glob(ROOT+'/take-*-r28/near/*.csv')+direct)
    # Round 27 override 2: layouts refused or deferred in round 26 (frozen files) are fed again, slice counts first.
    reopen=[x.strip() for x in open(WORK+'/reopen.txt')] if os.path.exists(WORK+'/reopen.txt') else []
    rank={p:i for i,p in enumerate(reopen)}
    def age(p):
        try:return os.path.getmtime(p)
        except FileNotFoundError:return 0
    live=sorted(paths,key=age,reverse=True);old=[p for p in reopen if p not in paths]
    for p in live+old:
        if time.time()-feed_started>90:break
        if admitted>=6:break
        if '/take-stair-c-r28/' in p or '/take-stair-c-r26/' in p:continue
        try:n=int(os.path.basename(p).split('-')[0].split('.')[0])
        except ValueError:
            try:n=int(next(csv.DictReader(open(p)))['n'])
            except (OSError,KeyError,StopIteration,ValueError):continue
        if n<100:continue
        try:donorbytes=open(p,'rb').read()
        except FileNotFoundError:continue
        digest=hashlib.sha256(donorbytes).hexdigest();key=str(n)+digest
        if key in S['feed']:continue
        retry_key=source_retry_key(p,key)
        if retry_key in S['handed']:continue
        # Scan the pinned geometry before walking a source tree.
        early_packing=None
        early=WORK+'/donors/screen-'+str(n)+'-'+digest[:12]+'.csv'
        os.makedirs(os.path.dirname(early),exist_ok=True);open(early,'wb').write(donorbytes)
        try:
            early_packing=M.np.asarray(M.read_layouts(early)[n],float);early_cut,early_reason=M.cut(early_packing,n)
        except (OSError,ValueError,KeyError):early_cut=None;early_reason='unreadable layout'
        if early_cut is None:
            offered=False
            try:
                candidate=early_packing is not None and whole.eligible(n,M.layout_state(early_packing)[0],(1+feed_bar[n])*math.sqrt(n))
                offered=whole.offer(sys.modules[__name__],p,n,donorbytes) if candidate else False
            except (OSError,ValueError,KeyError,TimeoutError) as ex:
                candidate=True;state('WHOLE follow deferred '+p+' '+str(ex))
            if offered or not candidate:S['feed'].add(key)
            else:S['handed'].add(retry_key)
            save();state('SCREEN unreadable '+p+' reason='+str(early_reason));continue
        parent=os.path.dirname(p)
        if os.path.basename(parent)=='near':parent=os.path.dirname(parent)
        meta=None
        for side in [p+'.json',p[:-4]+'.json']:
            if os.path.exists(side):
                try:meta=json.load(open(side));break
                except ValueError:pass
        source=None;lic=None;rectangle_record=None
        if meta and meta.get('parts'):
            try:rectangle_record=bounded_audit(rectangle3.audit,p,n,meta)
            except (OSError,ValueError,KeyError,RecursionError):rectangle_record=None
            if rectangle_record:
                # The full walk can take seconds. Refuse a producer rewrite in that interval.
                if hashlib.sha256(open(p,'rb').read()).hexdigest()!=digest:continue
                source=rectangle_record['source'];lic=rectangle_record['licence']
        if meta and not source:
            source=meta.get('source_override') or meta.get('source');lic=meta.get('licence_override') or meta.get('licence')
            if not source and meta.get('modules'):
                source='; '.join(q.get('source',q.get('src','')) for q in meta['modules']);lic='; '.join(q.get('licence','') for q in meta['modules'])
        if not source and meta and meta.get('backlog_ancestry'):
            ancestry=meta['backlog_ancestry']
            if all(q.get('admitted') for q in ancestry):
                source='rectangle parts; '+json.dumps(ancestry,sort_keys=True)
                lic='; '.join(sorted({q.get('record',{}).get('licence','') for q in ancestry}))
        if not source and os.path.exists(parent+'/work/sources-all.tsv'):
            records=list(csv.DictReader(open(parent+'/work/sources-all.tsv'),delimiter='\t'))
            name=os.path.basename(p)
            hits=[r for r in records if r.get('donor','') and (r['donor'] in name or name.endswith('-'+r['donor']+'.csv'))]
            if len(hits)==1:source=hits[0].get('source');lic=hits[0].get('licence')
        if not source and os.path.exists(parent+'/take.tsv'):
            r=next((r for r in csv.DictReader(open(parent+'/take.tsv'),delimiter='\t') if r['n']==str(n)),None)
            if r:source=r.get('source');lic=r.get('licence')
        if not source or not lic or not clean(source,lic) or any(x in source or x==p for x in excluded):
            marker='missing:'+key
            if marker not in S['handed']:
                state('DEFER donor '+p+' missing or excluded recorded ancestry');S['handed'].add(marker)
            if source and lic and BAD.search(source+' '+lic):S['feed'].add(key)
            continue
        tag='r28-'+str(n)+'-'+digest[:12];out=WORK+'/donors';os.makedirs(out,exist_ok=True)
        dest=out+'/'+tag+'.csv';open(dest,'wb').write(donorbytes)
        packing=M.np.asarray(M.read_layouts(dest)[n],float);cut,reason=M.cut(packing,n)
        if cut is None:
            S['feed'].add(key);save();state('SCREEN unreadable '+p+' reason='+str(reason));continue
        sh=share27.share(n,packing[:,:2]) if direct_public(p,source) else 0.
        if sh>=share27.LIMIT:
            S['feed'].add(key);save();state(f'REFUSE prvsiyan share {sh:.3f} '+p);continue
        record=rectangle_record or bounded_audit(audit,p,n,source,lic)
        if record is None:
            S['handed'].add(retry_key);state('DEFER untraced full ancestry '+p);save();continue
        if hashlib.sha256(open(p,'rb').read()).hexdigest()!=digest:
            state('DEFER rewritten donor during audit '+p);continue
        json.dump(record,open(dest+'.json','w'),indent=2)
        packing=M.np.asarray(M.read_layouts(dest)[n],float);cut,reason=M.cut(packing,n)
        if cut is None:
            S['feed'].add(key);save();state('SCREEN unreadable '+p+' reason='+str(reason)+'; no remote table/build queued');continue
        mods=M.modules_of(cut,record['source'],record['licence'],'r28d'+digest[:12])
        package=out+'/r28-live-'+str(n)+'-'+digest[:12]+'.pkl'
        pickle.dump(dict(mods=mods,lens={},origin='round26 readable layout'),open(package,'wb'))
        for host,_ in HOSTS:
            r=run(['rsync','-az',package,host+':scratch/squares-stair-c/inbox/'])
            if r.returncode:print('copy failed',host,r.stderr,flush=True)
        admitted+=1
        S['feed'].add(key);save();state(('REOPEN' if p in rank else 'FOLLOW')+' fresh donor '+p+' sha256 '+digest+' copied to the three workers, logs worker.log; deadline05:45Z')
    # Native table handoffs from the module and corner lanes are data only.
    log=open(ROOT+'/handoff-r28.log').read() if os.path.exists(ROOT+'/handoff-r28.log') else ''
    dirs=set(re.findall(r'$SCRATCH/bounties-squares/take-(?!stair-c)[^\s,;]+/work/[^\s,;]+',log))
    for d in sorted(dirs):
        if time.time()-feed_started>50:break
        d=d.rstrip('.');lp=d+'/library.pkl';ep=d+'/lens.pkl';corners=d+'/corners.pkl'
        if not os.path.exists(lp) and os.path.exists(corners):lp=corners
        if not os.path.exists(lp):continue
        key=d+str(os.stat(lp).st_mtime_ns)+str(os.stat(ep).st_mtime_ns if os.path.exists(ep) else 0)
        if key in S['feed']:continue
        a=pickle.load(open(lp,'rb'));a={'mods':a} if isinstance(a,list) else a;e=pickle.load(open(ep,'rb')) if os.path.exists(ep) else {}
        need=set(open(d+'/need.txt').read().split()) if os.path.exists(d+'/need.txt') else set()
        if lp.endswith('/corners.pkl'):need={q['id'] for q in a['mods']}
        if d.endswith('/take-modules-r28/work/lib24'):
            for p in glob.glob(os.path.dirname(d)+'/need-j*.txt'):need.update(open(p).read().split())
        # Full inherited libraries are not clean donor pools. Only named states
        # with self-contained source metadata are admitted.
        mods=[]
        for q in a.get('mods',[]):
            if q['id'] not in need:continue
            fp=fingerprint(q)
            if fp in S['native']:continue
            if not clean(q['src'],q['licence']) or any(x in q['src'] for x in excluded):continue
            mods.append(dict(q,src=d+' module '+q['id']+' immutable sha256 '+hashlib.sha256(pickle.dumps(q)).hexdigest()+'; '+q['src']))
        if not mods:S['feed'].add(key);continue
        supported=[]
        for q in mods:
            try:
                q['src'],q['licence']=pin(q['src'],q['licence'])
            except ValueError:continue
            supported.append(q)
        mods=supported
        if not mods:S['feed'].add(key);continue
        tag=('r28-live-corner-' if len(mods)<=3 else 'r28-patch-')+hashlib.sha256(key.encode()).hexdigest()[:12];dest=WORK+'/donors/'+tag+'.pkl'
        pickle.dump(dict(mods=mods,lens={q['id']:e[q['id']] for q in mods if q['id'] in e},origin=d),open(dest,'wb'))
        for host,_ in HOSTS:
            r=run(['rsync','-az',dest,host+':scratch/squares-stair-c/inbox/'])
            if r.returncode:print('copy failed',host,r.stderr,flush=True)
        S['native'].update(fingerprint(q) for q in mods)
        S['feed'].add(key);save();state('FOLLOW module handoff '+d+' named states='+str(len(mods))+'; deadline05:45Z')

def spread():
    # Round 27: an exact-f package serves every box (the r26 860 corner built 921 on another
    # box only through a near recut). Copy each finished one to the other two inboxes.
    os.makedirs(WORK+'/exactf-pkgs',exist_ok=True)
    for host,key in HOSTS:run(['rsync','-a','--include','r28-priority-exactf-*.pkl','--exclude','*',host+':scratch/squares-stair-c/inbox/',WORK+'/exactf-pkgs/'])
    for host,key in HOSTS:run(['rsync','-a','--ignore-existing',WORK+'/exactf-pkgs/',host+':scratch/squares-stair-c/inbox/'])

def collect():
    try:spread()
    except Exception:traceback.print_exc()
    publish()
    b=bar();admit=dict(b)
    own=TAKE+'/take.tsv'
    if os.path.exists(own):
        for r in csv.DictReader(open(own),delimiter='\t'):
            n=int(r['n']);admit[n]=min(admit[n],float(r['new']))
    for marker in S['handed']:
        if marker.startswith('certbest:'):
            _,n,value=marker.split(':');admit[int(n)]=min(admit[int(n)],float(value))
    json.dump({str(n):(1+v)*math.sqrt(n) for n,v in b.items()},open(WORK+'/bar.json','w'))
    for host,key in HOSTS:
        base=WORK+'/boxcopy/'+key;os.makedirs(base,exist_ok=True)
        for folder in ['raw-a','final','logs','tables','whole-kicks','kick-cert']:
            os.makedirs(base+'/'+folder,exist_ok=True)
            r=run(['rsync','-az',host+':scratch/squares-stair-c/'+folder+'/',base+'/'+folder+'/'])
            if r.returncode:print('copy failed',host,folder,r.stderr,flush=True)
        run(['rsync','-az',host+':scratch/squares-stair-c/worker.log',base+'/worker.log'])
        for package in glob.glob(base+'/tables/*.pkl'):
            marker='class-handoff:'+os.path.basename(package)
            if marker in S['handed']:continue
            data=pickle.load(open(package,'rb'))
            if not data['mods'] or not all('independent staircase with equal-area core-step transfer' in q['src'] for q in data['mods']):continue
            target=WORK+'/classes/'+os.path.basename(package)[:-4]
            os.makedirs(target,exist_ok=True)
            pickle.dump(dict(mods=data['mods'],layouts=[]),open(target+'/library.pkl','wb'))
            pickle.dump(data['lens'],open(target+'/lens.pkl','wb'))
            open(target+'/need.txt','w').write('\n'.join(q['id'] for q in data['mods'])+'\n')
            hand('independent core-step corner classes, states='+str(len(data['mods']))+', '+target)
            S['handed'].add(marker)

        cursor=WORK+'/worker-cursor-'+key+'.json'
        done=json.load(open(cursor)) if os.path.exists(cursor) else 0
        if os.path.exists(base+'/worker.log'):
            lines=open(base+'/worker.log').read().splitlines()
            for line in lines[done:]:
                if re.match(r'\d{4}-.*(?: IMPORTED | STOPPED |WITHDRAW FILTER|COMMAND quench-)',line):
                    with open(TAKE+'/STATE.txt','a') as h:h.write(line[:20]+' '+host+' REMOTE '+line[21:]+'; worker.py '+({'n':'0','m':'1','s':'2'}[key])+'; log '+base+'/worker.log; deadline05:45Z\n')
            json.dump(len(lines),open(cursor,'w'))
        run(['rsync','-az',WORK+'/bar.json',host+':scratch/squares-stair-c/bar.json'])
        rawpaths=sorted(glob.glob(base+'/raw-a/*.json'));nearmin={};rawmeta={}
        for rp in rawpaths:
            try:rj=json.load(open(rp))
            except (OSError,ValueError):continue
            rawmeta[rp]=rj
            if rj.get('built') is not None:nearmin[rj['n']]=min(nearmin.get(rj['n'],math.inf),rj['built'])
        rawpaths.sort(key=lambda p:(((rawmeta.get(p,{}).get('built') or math.inf)-(1+admit.get(rawmeta.get(p,{}).get('n',0),0))*math.sqrt(rawmeta.get(p,{}).get('n',1)))/math.sqrt(rawmeta.get(p,{}).get('n',1)),p))
        raw_started=time.time()
        for p in rawpaths:
            if time.time()-raw_started>30:break
            if p not in rawmeta:continue
            tag=key+os.path.basename(p)
            if tag in S['seen'] or not os.path.exists(p[:-5]+'.csv'):continue
            j=rawmeta[p];n=j['n'];built=j.get('built')
            if built is None:continue
            rr=rows(p[:-5]+'.csv')
            if len(rr)!=n:continue
            try:
                meta=bounded_audit(manifest,j)
                if meta is None:continue
            except ValueError:state('REJECT raw excluded ancestry '+p);S['seen'].add(tag);continue
            name=os.path.basename(p)[:-5]+'-'+key
            # Round 26: only builds within 0.005 of side of the live bar are near misses.
            close=built<(1+b[n])*math.sqrt(n)+.005
            out=(TAKE+'/near/' if close else WORK+'/far/')+name+'.csv';os.makedirs(os.path.dirname(out),exist_ok=True)
            write(out,rr);json.dump(meta,open(out+'.json','w'),indent=2)
            if close:hand(f'fresh build n={n}, side={built:.12f}, base delta={built-(1+H[n])*math.sqrt(n):+.9g}, '+out)
            S['seen'].add(tag)
            # Recut a new best near layout immediately. This uses the complete
            # module ancestry just checked above, without re-expanding it.
            if time.time()<FEEDEND and built<=nearmin[n]+1e-12 and built<(1+b[n])*math.sqrt(n)+.003:
                marker='self:'+str(n)
                prior=[float(x.split(':',2)[2]) for x in S['handed'] if x.startswith(marker+':')]
                if not prior or built<min(prior)-1e-7:
                    d,why=M.cut(M.np.asarray(M.read_layouts(out)[n],float),n)
                    if d is not None:
                        digest=hashlib.sha256(open(out,'rb').read()).hexdigest()
                        src,notice=pin(meta['source'],meta['licence'])
                        src=out+' immutable sha256 '+digest+'; '+src
                        mods=M.modules_of(d,src,notice,'r28self'+digest[:12])
                        package=WORK+'/donors/r28-live-self-'+str(n)+'-'+digest[:12]+'.pkl'
                        os.makedirs(WORK+'/donors',exist_ok=True)
                        pickle.dump(dict(mods=mods,lens={},origin='round26 near recut'),open(package,'wb'))
                        for target,_ in HOSTS:
                            result=run(['rsync','-az',package,target+':scratch/squares-stair-c/inbox/'])
                            if result.returncode:print('copy failed',target,result.stderr,flush=True)
                        S['handed'].add(marker+':'+repr(built))
                        state('RECUT new best near '+out+' three states staged both serial workers; deadline05:45Z')
            if built>=(1+admit[n])*math.sqrt(n)-1e-9:continue
            _,fr,score,why=floatsafe.work((n,rr))
            if fr is None or score>=H[n]-1e-10 or score>=admit[n]-1e-10:continue
            admit[n]=score
            cp=WORK+'/cert-in/'+name+'.csv';os.makedirs(os.path.dirname(cp),exist_ok=True)
            write(cp,fr);json.dump(meta,open(cp[:-4]+'.json','w'),indent=2)
            for attempt in range(3):
                r=run(['rsync','-az',cp,cp[:-4]+'.json',host+':scratch/squares-stair-c/cert-in/'])
                if not r.returncode:break
            if r.returncode:state('QUENCH copy failed '+cp+' on '+host+'; cert-in kept locally for a retry');print('copy failed',host,r.stderr,flush=True)
            S['handed'].add('certbest:'+str(n)+':'+repr(score))
            S['queued'].add(tag);state('QUENCH certified '+str(n)+' on '+host+' deadline05:45Z')
        save()
    publish()

def publish():
    if '--no-publish' in sys.argv:return
    best={};b=bar();base=basebar()
    for p in glob.glob(WORK+'/boxcopy/*/final/*.csv'):
        n=int(os.path.basename(p).split('-')[0])
        try:j=json.load(open(p[:-4]+'.json'))
        except (OSError,ValueError):continue
        if j.get('control_only') or not j.get('certified_file_quench',{}).get('completed'):continue
        try:meta=manifest(j)
        except ValueError:continue
        rr=rows(p)
        if len(rr)!=n:continue
        _,fr,score,why=cert_cache.certify(p,n)
        if fr is None:continue
        if j.get('own_near_follow') or (score<H[n]-1e-10 and score<b[n]-1e-10):
            complete=full_admission(p,n,meta)
            if complete is None:continue
            meta['source']+='; full-input source walk '+complete['source']
        current_side=(1+score)*math.sqrt(n)
        kick=j.get('source_kick',{})
        if j.get('whole_layout_follow') and kick.get('invoked') and kick.get('start',current_side)-current_side>1e-6:
            stage=WORK+'/near-stage/'+os.path.basename(p);os.makedirs(os.path.dirname(stage),exist_ok=True);write(stage,fr)
            payload=open(stage,'rb').read();digest=hashlib.sha256(payload).hexdigest();key='whole-near:'+digest
            if key not in S['handed']:
                out=TAKE+'/near/'+str(n)+'-whole-kick-'+digest[:12]+'.csv';os.replace(stage,out)
                near_meta=dict(meta,built=current_side,predicted=current_side,source_sha256=digest)
                json.dump(near_meta,open(out+'.json','w'),indent=2)
                hand(f'certified whole-kick near n={n}, side={current_side:.12f}, shortening={kick["start"]-current_side:.9g}, '+out)
                if j.get('kick_leg',0)==0:
                    follow=WORK+'/cert-in/'+str(n)+'-whole-leg1-'+digest[:12]+'.csv';write(follow,fr)
                    follow_meta=dict(near_meta,whole_kick=False,kick_leg=1,kick_seed=2900+n,previous_kick=kick,source_snapshot=out)
                    json.dump(follow_meta,open(follow[:-4]+'.json','w'),indent=2)
                S['handed'].add(key)
            elif os.path.exists(stage):os.remove(stage)
        if score>=H[n]-1e-10 or score>=b[n]-1e-10:continue
        # RULE001903: this lane's constructed outputs have no share refusal.
        proof=hashlib.sha256(json.dumps(meta['modules'],sort_keys=True).encode()).hexdigest()
        approved=json.load(open(WORK+'/approved-ancestry.json')) if os.path.exists(WORK+'/approved-ancestry.json') else []
        if not all(clean(q['source'],q['licence']) for q in meta['modules']):
            os.makedirs(WORK+'/pending-ancestry',exist_ok=True)
            json.dump(dict(n=n,score=score,gain=H[n]-score,path=p,proof=proof,metadata=meta),open(WORK+'/pending-ancestry/'+str(n)+'.json','w'),indent=2)
            continue
        if n not in best or score<best[n][0]:best[n]=(score,fr,meta,p)
    with open(TAKE+'/take.tsv.tmp','w') as h:
        w=csv.writer(h,delimiter='\t');w.writerow(['n','held','new','gain','source','licence'])
        for n,(score,fr,meta,p) in sorted(best.items()):
            write(TAKE+'/'+str(n)+'.csv',fr)
            w.writerow([n,repr(base[n]),repr(score),repr(base[n]-score),meta['source']+('; fq from certified whole layout' if meta.get('whole_layout_follow') else '; family squeeze then fq from certified file'),meta['licence']])
            key=str(n)+repr(score)
            if key not in S['published']:hand(f'certified n={n} gain={base[n]-score:.12g}, '+TAKE+'/'+str(n)+'.csv');S['published'].add(key)
    os.replace(TAKE+'/take.tsv.tmp',TAKE+'/take.tsv')
    for p in glob.glob(TAKE+'/*.csv'):
        if int(os.path.basename(p)[:-4]) not in best:os.remove(p)
    print(stamp(),'fresh files',len(S['feed']),'raw',len(S['seen']),'quench',len(S['queued']),'retained',len(best),'gain',sum(base[n]-x[0] for n,x in best.items()),flush=True)

def main():
    while time.time()<END:
        try:feed()
        except Exception:traceback.print_exc()
        save()
        try:collect()
        except Exception:traceback.print_exc()
        save()
        if '--once' in sys.argv:break
        time.sleep(30)
if __name__=='__main__':main()
