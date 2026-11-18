"""Copy fresh designs, publish near starts and certify the remote worker outputs."""
import signal,csv,datetime,glob,hashlib,json,math,os,pickle,re,shutil,subprocess,sys,time,traceback,faulthandler
faulthandler.register(signal.SIGUSR1,all_threads=True)
ROOT='$SCRATCH/bounties-squares';TAKE=ROOT+'/take-stair-c-r32';WORK=TAKE+'/work';LANE='.'
sys.path[:0]=[str(__import__('pathlib').Path(__file__).resolve().parent),LANE]
import fine as floatsafe
import modules as M
from provenance import clean, audit, held_record, pin, upstream_notices, derive_credit
from prepare import fingerprint
import share27
import cert_cache
import whole
import withdrawals
import rectangle3
import public_roots
public_roots.warm()
from ancestors import audit as ancestor_shares
csv.field_size_limit(64*1024*1024)
HOSTS=[('boxC','n'),('boxD','m'),('boxE','s')]
# Round 30: the fixed bar combines held round28 b and certified round29 rows.
H={int(r['n']):float(r['bar']) for r in csv.DictReader(open(ROOT+'/round32-briefs/bar32.tsv'),delimiter='\t')}
END=datetime.datetime(2026,11,16,17,14,tzinfo=datetime.timezone.utc).timestamp();FEEDEND=datetime.datetime(2026,11,16,16,55,tzinfo=datetime.timezone.utc).timestamp()
# Round 27: Samanyu markers out (override 2); the other roots stay out.
BAD=re.compile(r'verified-best-of-1105|penguin069/squares-joegun-boxed-certified-union|take-harvest-r22/(?:near/)?(?:639|691|745|858|918)(?!\d)|take-forensics-r23[^\n]*980|take-forensics-r2[123][^\n]*918')
STATE=WORK+'/coord-state.json'
S=json.load(open(STATE)) if os.path.exists(STATE) else dict(seen=[],handed=[],feed=[],queued=[],published=[])
for k in S:S[k]=set(S[k])
S.setdefault('native',set())
S.setdefault('native_refused',set())
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def state(text):
    with open(TAKE+'/STATE.txt','a') as h:h.write(stamp()+' boxA '+text+'\n')
def hand(text):
    with open(ROOT+'/handoff-r32.log','a') as h:h.write(stamp()+' stair-c -> all: '+text+'\n')
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
    path=WORK+'/withdrawal-pins.json'
    cache=json.load(open(path))if os.path.exists(path)else{}
    lines=[]
    for round_id in (31,32):
        log=ROOT+f'/handoff-r{round_id}.log'
        if os.path.exists(log):lines+=open(log).read().splitlines()
    # Preserve every pinned withdrawal from both logs.
    result=withdrawals.tokens(lines,cache,ROOT)
    library=WORK+'/library-public-exclusions.json'
    if os.path.exists(library):result+=json.load(open(library))
    json.dump(cache,open(path+'.tmp','w'));os.replace(path+'.tmp',path)
    return result

def direct_public(path,source):
    if not source.lstrip().lower().startswith('samanyu-dev/squares_in_squares') and re.match(r'^[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+',source.lstrip()):return True
    if re.search(r'own construction|own design|independent|stair-c|Samanyu-dev|seed merged0',source,re.I):return False
    return 'take-harvest-' in path or bool(re.search(r'/(?:data/(?:nb|ds)|public)/',path))

def manifest(j):
    mods=j['modules']
    if j.get('held31_origin'):
        from held_proof import check
        from provenance import held_identity,upstream_rows
        check(j['held31_origin'])
        assert len(mods)==1
        q=mods[0];identity=held_identity(q['source'],q['licence'])
        if identity is None or identity['n']!=j['n']or not clean(q['source'],q['licence']):raise ValueError('held source binding refused')
        record=identity['record'];text=record['source']+' '+record['licence'];notices=[]
        if 'sis-certified-union-micro-shrink'in text:
            counts=set(map(int,re.findall(r'areebbb/sis-certified-union-micro-shrink-lb-22-17479\s*::\s*per_n\.csv,\s*donor n\s*=\s*(\d+)',text)))
            if not counts:raise ValueError('held record lacks specific areebbb per-n notices')
            for n in sorted(counts):
                row=upstream_rows().get(n)
                if row is None:raise ValueError('held per-n notice missing')
                notices.append('areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n='+str(n)+', record='+json.dumps(row,sort_keys=True)+'; upstream '+row['src']+'; original licence notices retained in '+identity['path'])
        credit=' | '.join(notices)
        source='stair-c round32 numerical follow: '+q['source']+'; inherited source record '+identity['path']
        if credit:source+='; Upstream per-n records: '+credit
        return dict(j,source=source,licence=q['licence']+('; Upstream per-n records: '+credit if credit else''))
    if not mods or not all(clean(q['source'],q['licence']) for q in mods):raise ValueError('excluded or unresolved ancestry')
    src=('stair-c round32 whole-layout kick and fq follow: ' if j.get('source_kick',{}).get('invoked') else 'stair-c round32 whole-layout fq follow: ' if j.get('whole_layout_follow') else 'stair-c round32 composition: ')+', '.join(q['id']+' <'+q['source']+'>' for q in mods)
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
    return dict(H)

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
    for p in glob.glob(ROOT+'/take-*-r32/take.tsv'):
        if p==TAKE+'/take.tsv':continue
        try:
            for n,score in peer_scores(p):b[n]=min(b[n],score)
        except FileNotFoundError:continue
    return b

class AdmissionTimeout(BaseException):pass
def admission_timeout(*args):raise AdmissionTimeout('source admission20s')
signal.signal(signal.SIGALRM,admission_timeout)
def bounded_audit(function,*args):
    signal.setitimer(signal.ITIMER_REAL,20)
    try:return function(*args)
    except AdmissionTimeout:
        state('DEFER bounded full source walk '+str(args[0])[:240]);return None
    finally:signal.setitimer(signal.ITIMER_REAL,0)

FULL_ADMISSIONS={}
def full_admission(path,n,meta):
    payload=open(path,'rb').read()
    pins=sorted({(r['path'],r['sha256'])for r in withdrawals.current(ROOT)})
    policy=json.dumps(pins,separators=(',',':')).encode()
    key=hashlib.sha256(payload+meta['source'].encode()+meta['licence'].encode()+policy).hexdigest()
    cached=FULL_ADMISSIONS.get(key)
    if cached and (cached[1] is not None or time.time()-cached[0]<600):return cached[1]
    try:record=bounded_audit(audit,path,n,meta['source'],meta['licence'])
    except (OSError,ValueError,KeyError,RecursionError)as ex:
        state('DEFER full source proof '+path+' '+str(ex)[:300]);record=None
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
    handoff=open(ROOT+'/handoff-r32.log').read() if os.path.exists(ROOT+'/handoff-r32.log') else ''
    direct=re.findall(r'$SCRATCH/bounties-squares/take-[^\s,;]+-r30/[^\s,;]+\.csv',handoff)
    paths=set(glob.glob(ROOT+'/take-*-r31/*.csv')+glob.glob(ROOT+'/take-*-r31/near/*.csv')+direct)
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
        if '/take-stair-c-r32/' in p or '/take-stair-c-r26/' in p:continue
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
                candidate='-r31/'not in p and early_packing is not None and whole.eligible(n,M.layout_state(early_packing)[0],(1+feed_bar[n])*math.sqrt(n))
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
        if not source or not lic or not clean(source,lic) or any(x in source or x in p+' immutable sha256 '+digest for x in excluded):
            marker='missing:'+key
            if marker not in S['handed']:
                state('DEFER donor '+p+' missing or excluded recorded ancestry');S['handed'].add(marker)
            if source and lic and BAD.search(source+' '+lic):S['feed'].add(key)
            continue
        tag='r32-'+str(n)+'-'+digest[:12];out=WORK+'/donors';os.makedirs(out,exist_ok=True)
        dest=out+'/'+tag+'.csv';open(dest,'wb').write(donorbytes)
        packing=M.np.asarray(M.read_layouts(dest)[n],float);cut,reason=M.cut(packing,n)
        if cut is None:
            S['feed'].add(key);save();state('SCREEN unreadable '+p+' reason='+str(reason));continue
        # Public checks run only on the direct graph's public roots.
        # A harvest transport path does not change ownership of a held descendant.
        try:record=rectangle_record or bounded_audit(audit,p,n,source,lic)
        except (OSError,ValueError,KeyError,RecursionError)as ex:
            S['handed'].add(retry_key);state('DEFER donor source proof '+p+' '+str(ex)[:240]);save();continue
        if record is None:
            S['handed'].add(retry_key);state('DEFER untraced full ancestry '+p);save();continue
        if hashlib.sha256(open(p,'rb').read()).hexdigest()!=digest:
            state('DEFER rewritten donor during audit '+p);continue
        json.dump(record,open(dest+'.json','w'),indent=2)
        packing=M.np.asarray(M.read_layouts(dest)[n],float);cut,reason=M.cut(packing,n)
        if cut is None:
            S['feed'].add(key);save();state('SCREEN unreadable '+p+' reason='+str(reason)+'; no remote table/build queued');continue
        mods=M.modules_of(cut,record['source'],record['licence'],'r32d'+digest[:12])
        package=out+'/r31-live-'+str(n)+'-'+digest[:12]+'.pkl'
        pickle.dump(dict(mods=mods,lens={},origin='round26 readable layout'),open(package,'wb'))
        for host,_ in HOSTS:
            r=run(['rsync','-az',package,host+':scratch/squares-stair-c/inbox/'])
            if r.returncode:print('copy failed',host,r.stderr,flush=True)
        admitted+=1
        S['feed'].add(key);save();state(('REOPEN' if p in rank else 'FOLLOW')+' fresh donor '+p+' sha256 '+digest+' copied to the three workers, logs worker.log; deadline17:15Z on November16')
    feed_native(excluded)

def feed_native(excluded):
    native_started=time.time()
    # Native table handoffs from the module and corner lanes are data only.
    log=open(ROOT+'/handoff-r32.log').read() if os.path.exists(ROOT+'/handoff-r32.log') else ''
    dirs=set(re.findall(r'$SCRATCH/bounties-squares/take-(?!stair-c)[^\s,;]+/work/[^\s,;]+',log))
    def modified(d):
        return max((os.path.getmtime(d+'/'+name)for name in ('library.pkl','corners.pkl','lens.pkl')if os.path.exists(d+'/'+name)),default=0)
    for d in sorted(dirs,key=modified,reverse=True):
        if time.time()-native_started>50:break
        d=d.rstrip('.');lp=d+'/library.pkl';ep=d+'/lens.pkl';corners=d+'/corners.pkl'
        if not os.path.exists(lp) and os.path.exists(corners):lp=corners
        if not os.path.exists(lp):continue
        a=pickle.load(open(lp,'rb'));a={'mods':a} if isinstance(a,list) else a;e=pickle.load(open(ep,'rb')) if os.path.exists(ep) else {}
        need=set(open(d+'/need.txt').read().split()) if os.path.exists(d+'/need.txt') else set()
        priority={}
        if lp.endswith('/corners.pkl'):need={q['id'] for q in a['mods']}
        if d.endswith('/take-modules-r30/work/lib24'):
            for p in sorted(glob.glob(os.path.dirname(d)+'/need-j*.txt'),key=os.path.getmtime,reverse=True):
                for ident in open(p).read().split():
                    need.add(ident);priority.setdefault(ident,len(priority))
        key=d+str(os.stat(lp).st_mtime_ns)+str(os.stat(ep).st_mtime_ns if os.path.exists(ep) else 0)+hashlib.sha256('\n'.join(sorted(need)).encode()).hexdigest()
        if key in S['feed']:continue
        # Full inherited libraries are not clean donor pools. Only named states
        # with self-contained source metadata are admitted.
        mods=[];scanned_all=True
        refusal_prefix=key+':'+str(int(time.time()/600))+':'
        for q in sorted(a.get('mods',[]),key=lambda q:priority.get(q['id'],len(priority))):
            if time.time()-native_started>50:scanned_all=False;break
            if q['id'] not in need:continue
            fp=fingerprint(q)
            if fp in S['native']or refusal_prefix+fp in S['native_refused']:continue
            if not bounded_audit(clean,q['src'],q['licence']) or any(x in q['src'] for x in excluded):
                S['native_refused'].add(refusal_prefix+fp);continue
            mods.append(dict(q,src=d+' module '+q['id']+' immutable sha256 '+hashlib.sha256(pickle.dumps(q)).hexdigest()+'; '+q['src']))
        if not mods:
            if scanned_all:S['feed'].add(key)
            continue
        supported=[];checked_all=True
        for q in mods:
            if time.time()-native_started>80:checked_all=False;break
            fp=fingerprint(q)
            try:
                from public_roots import audit as public_audit
                if bounded_audit(public_audit,dict(source=q['src'],licence=q['licence']))is None:
                    S['native_refused'].add(refusal_prefix+fp);continue
                result=bounded_audit(pin,q['src'],q['licence'])
                if result is None:S['native_refused'].add(refusal_prefix+fp);continue
                q['src'],q['licence']=result
            except ValueError:S['native_refused'].add(refusal_prefix+fp);continue
            supported.append(q)
        mods=supported
        if not mods:
            if scanned_all and checked_all:S['feed'].add(key)
            continue
        packet=key+'|'+','.join(fingerprint(q)for q in mods)
        tag=('r32-live-corner-' if len(mods)<=3 else 'r32-patch-')+hashlib.sha256(packet.encode()).hexdigest()[:12];dest=WORK+'/donors/'+tag+'.pkl'
        pickle.dump(dict(mods=mods,lens={q['id']:e[q['id']] for q in mods if q['id'] in e},origin=d),open(dest,'wb'))
        for host,_ in HOSTS:
            r=run(['rsync','-az',dest,host+':scratch/squares-stair-c/inbox/'])
            if r.returncode:print('copy failed',host,r.stderr,flush=True)
        S['native'].update(fingerprint(q) for q in mods)
        if scanned_all and checked_all:S['feed'].add(key)
        save();state('FOLLOW module handoff '+d+' named states='+str(len(mods))+'; deadline17:15Z on November16')

def spread():
    # Round 27: an exact-f package serves every box (the r26 860 corner built 921 on another
    # box only through a near recut). Copy each finished one to the other two inboxes.
    os.makedirs(WORK+'/exactf-pkgs',exist_ok=True)
    for host,key in HOSTS:run(['rsync','-a','--include','r32-priority-exactf-*.pkl','--exclude','*',host+':scratch/squares-stair-c/inbox/',WORK+'/exactf-pkgs/'])
    for host,key in HOSTS:run(['rsync','-a','--ignore-existing',WORK+'/exactf-pkgs/',host+':scratch/squares-stair-c/inbox/'])

def collect():
    publish()
    b=bar();admit=dict(b);search=dict(b)
    own=TAKE+'/take.tsv'
    if os.path.exists(own):
        for r in csv.DictReader(open(own),delimiter='\t'):
            n=int(r['n']);admit[n]=min(admit[n],float(r['new']));search[n]=min(search[n],float(r['new']))
    for marker in S['handed']:
        if marker.startswith('certbest:'):
            _,n,value=marker.split(':');admit[int(n)]=min(admit[int(n)],float(value))
    json.dump({str(n):(1+v)*math.sqrt(n) for n,v in search.items()},open(WORK+'/bar.json','w'))
    for host,key in HOSTS:
        base=WORK+'/boxcopy/'+key;os.makedirs(base,exist_ok=True)
        folders=['raw-a','final','logs','tables','whole-kicks','kick-cert']
        args=['rsync','-az','--exclude','/whole-kicks/*/tmp/***']
        for folder in folders:args.extend(['--include','/'+folder+'/***'])
        args.extend(['--include','/worker.log','--exclude','*',host+':scratch/squares-stair-c/',base+'/'])
        r=run(args)
        if r.returncode:print('copy failed',host,r.stderr,flush=True)
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
                    with open(TAKE+'/STATE.txt','a') as h:h.write(line[:20]+' '+host+' REMOTE '+line[21:]+'; worker.py '+({'n':'0','m':'1','s':'2'}[key])+'; log '+base+'/worker.log; deadline17:15Z on November16\n')
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
                        mods=M.modules_of(d,src,notice,'r32self'+digest[:12])
                        package=WORK+'/donors/r32-live-self-'+str(n)+'-'+digest[:12]+'.pkl'
                        os.makedirs(WORK+'/donors',exist_ok=True)
                        pickle.dump(dict(mods=mods,lens={},origin='round26 near recut'),open(package,'wb'))
                        for target,_ in HOSTS:
                            result=run(['rsync','-az',package,target+':scratch/squares-stair-c/inbox/'])
                            if result.returncode:print('copy failed',target,result.stderr,flush=True)
                        S['handed'].add(marker+':'+repr(built))
                        state('RECUT new best near '+out+' three states staged both serial workers; deadline17:15Z on November16')
            if built>=(1+admit[n])*math.sqrt(n):continue
            _,fr,score,why=floatsafe.work((n,rr))
            if fr is None or score>=H[n]-1e-10 or score>=admit[n]:continue
            admit[n]=score
            cp=WORK+'/cert-in/'+name+'.csv';os.makedirs(os.path.dirname(cp),exist_ok=True)
            write(cp,fr);json.dump(meta,open(cp[:-4]+'.json','w'),indent=2)
            for attempt in range(3):
                r=run(['rsync','-az',cp,cp[:-4]+'.json',host+':scratch/squares-stair-c/cert-in/'])
                if not r.returncode:break
            if r.returncode:state('QUENCH copy failed '+cp+' on '+host+'; cert-in kept locally for a retry');print('copy failed',host,r.stderr,flush=True)
            S['handed'].add('certbest:'+str(n)+':'+repr(score))
            S['queued'].add(tag);state('QUENCH certified '+str(n)+' on '+host+' deadline17:15Z on November16')
        save()
    publish()

def eligible_score(n,score,base,peers):
    return score<base[n]-1e-10 and score<peers[n]

def publish():
    if '--no-publish' in sys.argv:return
    best={};b=bar();base=basebar()
    for p in glob.glob(WORK+'/boxcopy/*/final/*.csv'):
        n=int(os.path.basename(p).split('-')[0])
        try:j=json.load(open(p[:-4]+'.json'))
        except (OSError,ValueError):continue
        if j.get('control_only') or not j.get('certified_file_quench',{}).get('completed'):continue
        rr=rows(p)
        if len(rr)!=n:continue
        _,fr,score,why=cert_cache.certify(p,n)
        if fr is None:continue
        current_side=(1+score)*math.sqrt(n)
        kick=j.get('source_kick',{})
        candidate=eligible_score(n,score,H,b)
        changed_near=bool(j.get('whole_layout_follow')and kick.get('invoked')and kick.get('start',current_side)-current_side>1e-6)
        near_marker='near-final:'+hashlib.sha256(open(p,'rb').read()+json.dumps(j,sort_keys=True).encode()).hexdigest()
        if not candidate and(not changed_near or near_marker in S['handed']):continue
        try:meta=bounded_audit(manifest,j)
        except ValueError:continue
        if meta is None:continue
        complete=full_admission(p,n,meta)
        if complete is None:continue
        if complete.get('public_roots') and not complete.get('owned_ancestry') and not complete.get('held_boundaries'):
            packing=M.np.asarray([[float(r[k]) for k in ('x','y','angle')]for r in fr])
            shares=public_roots.compare(n,hashlib.sha256(open(p,'rb').read()).hexdigest(),tuple(map(tuple,packing)))
            if max(shares[1:])>=.4:
                state(f'REFUSE public output n={n} shares={shares} path={p}');continue
        meta['source']+='; full-input source walk '+complete['source']
        if changed_near:
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
            S['handed'].add(near_marker)
        if not eligible_score(n,score,H,b):continue
        # RULE001903: this lane's constructed outputs have no share refusal.
        proof=hashlib.sha256(json.dumps(meta['modules'],sort_keys=True).encode()).hexdigest()
        approved=json.load(open(WORK+'/approved-ancestry.json')) if os.path.exists(WORK+'/approved-ancestry.json') else []
        if not all(clean(q['source'],q['licence']) for q in meta['modules']):
            os.makedirs(WORK+'/pending-ancestry',exist_ok=True)
            json.dump(dict(n=n,score=score,gain=H[n]-score,path=p,proof=proof,metadata=meta),open(WORK+'/pending-ancestry/'+str(n)+'.json','w'),indent=2)
            continue
        if n not in best or score<best[n][0]or(score==best[n][0]and not meta.get('whole_layout_follow')and best[n][2].get('whole_layout_follow')):best[n]=(score,fr,meta,p)
    with open(TAKE+'/take.tsv.tmp','w') as h:
        w=csv.writer(h,delimiter='\t');w.writerow(['n','held','new','gain','source','licence'])
        for n,(score,fr,meta,p) in sorted(best.items()):
            write(TAKE+'/'+str(n)+'.csv',fr)
            payload=open(TAKE+'/'+str(n)+'.csv','rb').read();digest=hashlib.sha256(payload).hexdigest()
            source_digest=hashlib.sha256((meta['source']+'\0'+meta['licence']).encode()).hexdigest()
            archive=WORK+'/published/'+str(n)+'-'+digest+'-'+source_digest+'.csv';os.makedirs(os.path.dirname(archive),exist_ok=True)
            if not os.path.exists(archive):
                open(archive,'wb').write(payload)
                retained=dict(meta,built=(1+score)*math.sqrt(n),immutable_published_copy=True,packing_sha256=digest,source_record_sha256=source_digest,parent_final=p,parent_final_sha256=hashlib.sha256(open(p,'rb').read()).hexdigest())
                json.dump(retained,open(archive+'.json','w'),indent=2)
            else:assert open(archive,'rb').read()==payload
            source=meta['source']+'; published byte snapshot '+archive+' immutable sha256 '+digest
            w.writerow([n,repr(base[n]),repr(score),repr(base[n]-score),source+('; fq from certified whole layout' if meta.get('whole_layout_follow') else '; family squeeze then fq from certified file'),meta['licence']])
            key=str(n)+repr(score)
            if key not in S['published']:hand(f'certified n={n} gain={base[n]-score:.12g}, '+archive+'; take '+TAKE+'/'+str(n)+'.csv');S['published'].add(key)
    os.replace(TAKE+'/take.tsv.tmp',TAKE+'/take.tsv')
    for p in glob.glob(TAKE+'/*.csv'):
        if int(os.path.basename(p)[:-4]) not in best:continue  # Keep every published byte path for descendants.
    print(stamp(),'fresh files',len(S['feed']),'raw',len(S['seen']),'quench',len(S['queued']),'retained',len(best),'gain',sum(base[n]-x[0] for n,x in best.items()),flush=True)

def main():
    while time.time()<END:
        try:collect()
        except Exception:traceback.print_exc()
        save()
        try:feed()
        except Exception:traceback.print_exc()
        save()
        if '--once' in sys.argv:break
        time.sleep(30)
if __name__=='__main__':main()
