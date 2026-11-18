"""Freeze reviewed takes, measure every stage, and verify copied box archives."""
import csv,glob,hashlib,importlib.util,json,math,os,pickle,sys,tarfile
csv.field_size_limit(64*1024*1024)
S='$SCRATCH/bounties-squares';T=S+'/take-stair-c-r24';W=T+'/work';L='.'
spec=importlib.util.spec_from_file_location('coordinator',L+'/tools/stair-c/r24/coordinator.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify(path,receipt,expected):
    assert sha(path)==expected
    r=json.load(open(receipt));seen=set()
    with tarfile.open(path) as tf:
        for item in tf.getmembers():
            assert item.isfile() and not item.name.startswith('/') and '..' not in item.name.split('/')
            data=tf.extractfile(item).read()
            if item.name=='receipt.json':assert hashlib.sha256(data).hexdigest()==sha(receipt);continue
            assert hashlib.sha256(data).hexdigest()==r['files'][item.name],item.name
            seen.add(item.name)
    assert seen==set(r['files'])
    print('VERIFIED',path,len(seen),'members; all SHA256 match')
    return dict(archive=path,files=len(seen),archive_sha256=expected,receipt_sha256=sha(receipt))

def publish():
    approved=set(json.load(open(W+'/approved-ancestry.json'))) if os.path.exists(W+'/approved-ancestry.json') else set()
    bar=C.bar();best={}
    for p in glob.glob(W+'/boxcopy/*/final/*.csv'):
        n=int(os.path.basename(p).split('-')[0])
        try:j=json.load(open(p[:-4]+'.json'))
        except (ValueError,FileNotFoundError):continue
        if 'certified_file_quench' not in j:continue
        proof=hashlib.sha256(json.dumps(j['modules'],sort_keys=True).encode()).hexdigest()
        if proof not in approved:continue
        try:meta=C.manifest(j)
        except ValueError:continue
        _,fr,score,error=C.floatsafe.work((n,C.rows(p)))
        if fr is None or score>=C.H[n]-1e-10 or score>=bar[n]-1e-10:continue
        if n not in best or score<best[n][0]:best[n]=(score,fr,meta,p)
    with open(T+'/take.tsv.tmp','w') as f:
        writer=csv.writer(f,delimiter='\t');writer.writerow(['n','held','new','gain','source','licence'])
        for n,(score,fr,meta,p) in sorted(best.items()):
            C.write(T+'/'+str(n)+'.csv',fr)
            writer.writerow([n,repr(C.H[n]),repr(score),repr(C.H[n]-score),meta['source']+'; family squeeze then fq from certified file',meta['licence']])
    os.replace(T+'/take.tsv.tmp',T+'/take.tsv')
    for p in glob.glob(T+'/*.csv'):
        if int(os.path.basename(p)[:-4]) not in best:os.remove(p)
    result=dict(improved_n=len(best),against_round23=sum(C.H[n]-v[0] for n,v in best.items()),beyond_other_live_r24=sum(bar[n]-v[0] for n,v in best.items()))
    json.dump(result,open(W+'/final-take-check.json','w'),indent=2);print(json.dumps(result));return result

def measure():
    H={int(r['n']):float(r['L']) for r in csv.DictReader(open(S+'/gate/cand-round23-1113a/details.csv'))};records=[]
    for p in sorted(glob.glob(W+'/boxcopy/*/raw-a/*.json')):
        try:j=json.load(open(p))
        except ValueError:continue
        n=j['n']
        if j.get('built') is None:continue
        try:C.manifest(j);status='source screen passed'
        except ValueError as e:status=str(e)
        records.append(dict(n=n,phase='SLP' if j.get('early_stage') else 'full',corner=j['modules'][0]['id'],far1=j['modules'][1]['id'],far2=j['modules'][2]['id'],stacks1=j['stacks'][0],stacks2=j['stacks'][1],predicted_side=j['predicted'],built_side=j['built'],candidate_side=H[n],built_minus_candidate=j['built']-H[n],source_status=status,seconds=sum(j.get('seconds',{}).values()),record=p))
    fields=['n','phase','corner','far1','far2','stacks1','stacks2','predicted_side','built_side','candidate_side','built_minus_candidate','source_status','seconds','record']
    out=L+'/results/stair-c-r24-2026-11-13.tsv'
    with open(out+'.tmp','w') as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter='\t');writer.writeheader();writer.writerows(sorted(records,key=lambda r:(r['n'],r['built_side'],r['phase'])))
    os.replace(out+'.tmp',out)
    pool={}
    for p in glob.glob(S+'/take-*-r24/take.tsv'):
        for r in csv.DictReader(open(p),delimiter='\t'):
            n=int(r['n']);score=float(r['new'])
            if n not in pool or score<pool[n]['score']:pool[n]=dict(n=n,score=score,take=p,source=r.get('source',''))
    contributions=[dict(n=n,score=r['score'],gain=C.H[n]-r['score'],take=r['take']) for n,r in sorted(pool.items()) if 'take-stair-c-r24/' in r['source'] and C.H[n]-r['score']>1e-10 and r['take']!=T+'/take.tsv']
    queues={}
    for path in glob.glob(W+'/archive/*/final-copy.tar.gz'):
        with tarfile.open(path) as tf:
            state=pickle.loads(tf.extractfile('state.pkl').read())
        queues[path]=dict(pending_builds=len(state['build']),pending_rank_requests=len(state['rank']),pending_rank_targets=sum(len(r['ns']) for r in state['rank']),imported_inputs=len(state['imported']))
    result=dict(full_builds=sum(r['phase']=='full' for r in records),slp_exports=sum(r['phase']=='SLP' for r in records),n_values=len({r['n'] for r in records}),screened_full_builds=sum(r['phase']=='full' and r['source_status']=='source screen passed' for r in records),ineligible_stages=sum(r['source_status']!='source screen passed' for r in records),no_starts=len(glob.glob(W+'/boxcopy/*/raw-a/*.nostart')),contributions=contributions,queues=queues)
    json.dump(result,open(W+'/measurements-final.json','w'),indent=2);print(json.dumps(result));return result
if __name__=='__main__':
    if sys.argv[1]=='verify':verify(*sys.argv[2:5])
    elif sys.argv[1]=='publish':publish()
    elif sys.argv[1]=='measure':measure()
