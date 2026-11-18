"""Copy fresh designs, publish near starts and certify the remote worker outputs."""
import csv,datetime,glob,hashlib,json,math,os,pickle,re,shutil,subprocess,sys,time,traceback
ROOT='$SCRATCH/bounties-squares';TAKE=ROOT+'/take-stair-c-r24';WORK=TAKE+'/work';LANE='.'
sys.path.insert(0,LANE)
import floatsafe
import modules as M
csv.field_size_limit(64*1024*1024)
HOSTS=[('boxC','n'),('boxE','s')]
H={int(r['n']):float(r['score']) for r in csv.DictReader(open(ROOT+'/gate/cand-round23-1113a/details.csv'))}
END=datetime.datetime(2026,11,13,22,24,tzinfo=datetime.timezone.utc).timestamp();FEEDEND=END-9*60
BAD=re.compile(r'verified-best-of-1105|penguin069/squares-joegun-boxed-certified-union|take-harvest-r22/(?:near/)?(?:639|691|745|858|918)(?!\d)|take-forensics-r23[^\n]*980|take-forensics-r2[123][^\n]*918')
STATE=WORK+'/coord-state.json'
S=json.load(open(STATE)) if os.path.exists(STATE) else dict(seen=[],handed=[],feed=[],queued=[],published=[])
for k in S:S[k]=set(S[k])
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def state(text):
    with open(TAKE+'/STATE.txt','a') as h:h.write(stamp()+' boxA '+text+'\n')
def hand(text):
    with open(ROOT+'/handoff-r24.log','a') as h:h.write(stamp()+' stair-c -> all: '+text+'\n')
def save():
    json.dump({k:sorted(v) for k,v in S.items()},open(STATE+'.tmp','w'));os.replace(STATE+'.tmp',STATE)
def run(args):return subprocess.run(args,capture_output=True,text=True,timeout=50)
def rows(p):return [{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
def write(p,rr):
    with open(p+'.tmp','w') as h:
        w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rr)
    os.replace(p+'.tmp',p)
def exclusions():
    lines=[x for x in open(ROOT+'/handoff-r24.log') if 'WITHDRAW' in x]
    return sorted({p for x in lines for p in re.findall(r'$SCRATCH/bounties-squares/take-[^\s,;]+\.csv',x)})
def manifest(j):
    mods=j['modules']
    for q in mods:
        parent=q['source']
        independent='held' not in parent and 'take-' not in parent and not parent.startswith('stair-c')
        current='round23 candidate gather/round23-2026-11-13a.csv' in parent or 'immutable sha256' in parent
        control=parent.startswith('take-twoshort-r17 n=975:') and q['licence']=='our own' and 'held' not in parent
        if not (independent or current or control):raise ValueError('unresolved inherited ancestry')
    src='stair-c round24 fresh composition: '+', '.join(q['id']+' <'+q['source']+'>' for q in mods)
    lic='; '.join(sorted({q['licence'] for q in mods}))
    if BAD.search(src+' '+lic) or any(x in src for x in exclusions()):raise ValueError('excluded ancestry')
    proof=hashlib.sha256(json.dumps(mods,sort_keys=True).encode()).hexdigest()
    annotations=json.load(open(WORK+'/ancestry-annotations.json')) if os.path.exists(WORK+'/ancestry-annotations.json') else {}
    if proof in annotations:
        src+='; '+annotations[proof]['source_appendix'];lic=annotations[proof]['licence']
    return dict(j,source=src,licence=lic)
def bar():
    b=dict(H)
    for p in glob.glob(ROOT+'/take-*-r24/take.tsv'):
        if p==TAKE+'/take.tsv':continue
        for r in csv.DictReader(open(p),delimiter='\t'):
            try:n=int(r['n']);b[n]=min(b[n],float(r['new']))
            except (ValueError,KeyError):pass
    return b

def feed():
    if time.time()>FEEDEND:return
    excluded=exclusions()
    json.dump(excluded,open(WORK+'/excluded-paths.json','w'))
    for host,_ in HOSTS:run(['rsync','-az',WORK+'/excluded-paths.json',host+':scratch/squares-stair-c/excluded-paths.json'])
    admitted=0
    # Hash versions so a changed geometry is fresh even if its side is unchanged.
    for p in sorted(glob.glob(ROOT+'/take-*-r24/*.csv')+glob.glob(ROOT+'/take-*-r24/near/*.csv'),key=os.path.getmtime,reverse=True):
        if admitted>=4:break
        if '/take-stair-c-r24/' in p:continue
        try:n=int(os.path.basename(p).split('-')[0].split('.')[0])
        except ValueError:continue
        if n<100:continue
        donorbytes=open(p,'rb').read();digest=hashlib.sha256(donorbytes).hexdigest();key=str(n)+digest
        if key in S['feed']:continue
        parent=os.path.dirname(p)
        if os.path.basename(parent)=='near':parent=os.path.dirname(parent)
        meta=None
        for side in [p+'.json',p[:-4]+'.json']:
            if os.path.exists(side):
                try:meta=json.load(open(side));break
                except ValueError:pass
        source=None;lic=None
        if meta:
            source=meta.get('source');lic=meta.get('licence')
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
        if not source or not lic or BAD.search(source+' '+lic) or any(x in source or x==p for x in excluded):
            marker='missing:'+key
            if marker not in S['handed']:
                state('DEFER donor '+p+' missing or excluded recorded ancestry');S['handed'].add(marker)
            if source and lic and BAD.search(source+' '+lic):S['feed'].add(key)
            continue
        tag='r24-'+str(n)+'-'+digest[:12];out=WORK+'/donors';os.makedirs(out,exist_ok=True)
        dest=out+'/'+tag+'.csv';open(dest,'wb').write(donorbytes)
        record=dict(n=n,source=p+' immutable sha256 '+digest+'; '+source,licence=lic)
        json.dump(record,open(dest+'.json','w'),indent=2)
        packing=M.np.asarray(M.read_layouts(dest)[n],float);cut,reason=M.cut(packing,n)
        if cut is None:
            S['feed'].add(key);save();state('SCREEN unreadable '+p+' reason='+str(reason)+'; no remote table/build queued');continue
        mods=M.modules_of(cut,record['source'],record['licence'],'r24d'+digest[:12])
        package=out+'/r24-live-'+str(n)+'-'+digest[:12]+'.pkl'
        pickle.dump(dict(mods=mods,lens={},origin='round24 readable layout'),open(package,'wb'))
        for host,_ in HOSTS:
            r=run(['rsync','-az',package,host+':scratch/squares-stair-c/inbox/'])
            if r.returncode:raise RuntimeError(r.stderr)
        admitted+=1
        S['feed'].add(key);save();state('FOLLOW fresh donor '+p+' copied both assigned single workers, logs worker.log; deadline22:15Z')
    # Native table handoffs from the module and corner lanes are data only.
    log=open(ROOT+'/handoff-r24.log').read()
    dirs=set(re.findall(r'$SCRATCH/bounties-squares/take-(?!stair-c)[^\s,;]+/work/[^\s,;]+',log))
    dirs.add(ROOT+'/take-modules-r24/work/lib24')
    for d in sorted(dirs):
        d=d.rstrip('.');lp=d+'/library.pkl';ep=d+'/lens.pkl';corners=d+'/corners.pkl'
        if not os.path.exists(lp) and os.path.exists(corners):lp=corners
        if not os.path.exists(lp):continue
        key=d+str(os.stat(lp).st_mtime_ns)+str(os.stat(ep).st_mtime_ns if os.path.exists(ep) else 0)
        if key in S['feed']:continue
        a=pickle.load(open(lp,'rb'));a={'mods':a} if isinstance(a,list) else a;e=pickle.load(open(ep,'rb')) if os.path.exists(ep) else {}
        need=set(open(d+'/need.txt').read().split()) if os.path.exists(d+'/need.txt') else set()
        if lp.endswith('/corners.pkl'):need={q['id'] for q in a['mods']}
        if d.endswith('/take-modules-r24/work/lib24'):
            for p in glob.glob(os.path.dirname(d)+'/need-j*.txt'):need.update(open(p).read().split())
        # Full inherited libraries are not clean donor pools. Only named states
        # with self-contained source metadata are admitted.
        mods=[dict(q,src=d+' module '+q['id']+' immutable sha256 '+hashlib.sha256(pickle.dumps(q)).hexdigest()+'; '+q['src']) for q in a.get('mods',[]) if q['id'] in need and not BAD.search(q['src']+' '+q['licence']) and not any(x in q['src'] for x in excluded)]
        if not mods:S['feed'].add(key);continue
        tag=('r24-live-corner-' if len(mods)<=3 else 'r24-patch-')+hashlib.sha256(key.encode()).hexdigest()[:12];dest=WORK+'/donors/'+tag+'.pkl'
        pickle.dump(dict(mods=mods,lens={q['id']:e[q['id']] for q in mods if q['id'] in e},origin=d),open(dest,'wb'))
        for host,_ in HOSTS:
            r=run(['rsync','-az',dest,host+':scratch/squares-stair-c/inbox/'])
            if r.returncode:raise RuntimeError(r.stderr)
        S['feed'].add(key);save();state('FOLLOW module handoff '+d+' named states='+str(len(mods))+'; deadline22:15Z')

def collect():
    b=bar();json.dump({str(n):(1+v)*math.sqrt(n) for n,v in b.items()},open(WORK+'/bar.json','w'))
    for host,key in HOSTS:
        base=WORK+'/boxcopy/'+key;os.makedirs(base,exist_ok=True)
        for folder in ['raw-a','final','logs','tables']:
            os.makedirs(base+'/'+folder,exist_ok=True)
            r=run(['rsync','-az',host+':scratch/squares-stair-c/'+folder+'/',base+'/'+folder+'/'])
            if r.returncode:print('copy failed',host,folder,r.stderr,flush=True)
        run(['rsync','-az',host+':scratch/squares-stair-c/worker.log',base+'/worker.log'])
        cursor=WORK+'/worker-cursor-'+key+'.json'
        done=json.load(open(cursor)) if os.path.exists(cursor) else 0
        if os.path.exists(base+'/worker.log'):
            lines=open(base+'/worker.log').read().splitlines()
            for line in lines[done:]:
                if re.match(r'\d{4}-.*(?: BUILD | COMMAND | IMPORTED | STOPPED |WITHDRAW FILTER| TABLE |IMPORT START)',line):
                    with open(TAKE+'/STATE.txt','a') as h:h.write(line[:20]+' '+host+' REMOTE '+line[21:]+'; worker.py '+('0' if key=='n' else '1')+'; log '+base+'/worker.log; deadline22:15Z\n')
            json.dump(len(lines),open(cursor,'w'))
        run(['rsync','-az',WORK+'/bar.json',host+':scratch/squares-stair-c/bar.json'])
        for p in sorted(glob.glob(base+'/raw-a/*.json')):
            tag=key+os.path.basename(p)
            if tag in S['seen'] or not os.path.exists(p[:-5]+'.csv'):continue
            j=json.load(open(p));n=j['n'];built=j.get('built')
            if built is None:continue
            rr=rows(p[:-5]+'.csv')
            if len(rr)!=n:continue
            try:meta=manifest(j)
            except ValueError:state('REJECT raw excluded ancestry '+p);S['seen'].add(tag);continue
            name=os.path.basename(p)[:-5]+'-'+key;out=TAKE+'/near/'+name+'.csv'
            write(out,rr);json.dump(meta,open(out+'.json','w'),indent=2)
            hand(f'fresh build n={n}, side={built:.12f}, candidate delta={built-(1+H[n])*math.sqrt(n):+.9g}, '+out)
            S['seen'].add(tag)
            if built>=(1+b[n])*math.sqrt(n)-1e-9:continue
            _,fr,score,why=floatsafe.work((n,rr))
            if fr is None or score>=H[n]-1e-10 or score>=b[n]-1e-10:continue
            cp=WORK+'/cert-in/'+name+'.csv';os.makedirs(os.path.dirname(cp),exist_ok=True)
            write(cp,fr);json.dump(meta,open(cp[:-4]+'.json','w'),indent=2)
            r=run(['rsync','-az',cp,cp[:-4]+'.json',host+':scratch/squares-stair-c/cert-in/'])
            if r.returncode:raise RuntimeError(r.stderr)
            S['queued'].add(tag);state('QUENCH certified '+str(n)+' on '+host+' deadline22:15Z')
    best={};b=bar()
    for p in glob.glob(WORK+'/boxcopy/*/final/*.csv'):
        n=int(os.path.basename(p).split('-')[0]);j=json.load(open(p[:-4]+'.json'));meta=manifest(j)
        if 'certified_file_quench' not in j:continue
        _,fr,score,why=floatsafe.work((n,rows(p)))
        if fr is None or score>=H[n]-1e-10 or score>=b[n]-1e-10:continue
        proof=hashlib.sha256(json.dumps(meta['modules'],sort_keys=True).encode()).hexdigest()
        approved=json.load(open(WORK+'/approved-ancestry.json')) if os.path.exists(WORK+'/approved-ancestry.json') else []
        if proof not in approved:
            os.makedirs(WORK+'/pending-ancestry',exist_ok=True)
            json.dump(dict(n=n,score=score,gain=H[n]-score,path=p,proof=proof,metadata=meta),open(WORK+'/pending-ancestry/'+str(n)+'.json','w'),indent=2)
            continue
        if n not in best or score<best[n][0]:best[n]=(score,fr,meta,p)
    with open(TAKE+'/take.tsv.tmp','w') as h:
        w=csv.writer(h,delimiter='\t');w.writerow(['n','held','new','gain','source','licence'])
        for n,(score,fr,meta,p) in sorted(best.items()):
            write(TAKE+'/'+str(n)+'.csv',fr)
            w.writerow([n,repr(H[n]),repr(score),repr(H[n]-score),meta['source']+'; family squeeze then fq from certified file',meta['licence']])
            key=str(n)+repr(score)
            if key not in S['published']:hand(f'certified n={n} gain={H[n]-score:.12g}, '+TAKE+'/'+str(n)+'.csv');S['published'].add(key)
    os.replace(TAKE+'/take.tsv.tmp',TAKE+'/take.tsv')
    for p in glob.glob(TAKE+'/*.csv'):
        if int(os.path.basename(p)[:-4]) not in best:os.remove(p)
    print(stamp(),'fresh files',len(S['feed']),'raw',len(S['seen']),'quench',len(S['queued']),'retained',len(best),'gain',sum(H[n]-x[0] for n,x in best.items()),flush=True)

def main():
    while time.time()<END:
        try:feed();collect();save()
        except Exception:traceback.print_exc();save()
        if '--once' in sys.argv:break
        time.sleep(45)
if __name__=='__main__':main()
