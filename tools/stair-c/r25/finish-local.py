"""Measure this round and verify final copies without touching other lanes."""
import csv,glob,hashlib,importlib.util,json,math,os,pickle,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),'.']
import coordinator as C
S=Path(C.ROOT);T=Path(C.TAKE);W=Path(C.WORK);L=Path(C.LANE)

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def verify(path,receipt,expected):
    assert sha(path)==expected
    r=json.load(open(receipt));seen=set()
    with tarfile.open(path) as tf:
        for item in tf:
            assert item.isfile() and not item.name.startswith('/') and '..' not in item.name.split('/')
            data=tf.extractfile(item).read()
            if item.name=='receipt.json':assert hashlib.sha256(data).hexdigest()==sha(receipt);continue
            assert hashlib.sha256(data).hexdigest()==r['files'][item.name],item.name
            seen.add(item.name)
    assert seen==set(r['files'])
    print('VERIFIED',path,len(seen),'files')
    return dict(archive=str(path),files=len(seen),archive_sha256=expected,receipt_sha256=sha(receipt))

def measure():
    base=C.basebar();rows=[];nostarts=[];counts={};classes=[]
    for p in sorted(W.glob('boxcopy/*/raw-a/*.json')):
        j=json.load(open(p));n=j['n'];v=j.get('built')
        if v is None:continue
        try:C.manifest(j);status='traced source screen passed'
        except ValueError as e:status=str(e)
        ids=[q['id'] for q in j['modules']]
        rows.append(dict(n=n,phase='SLP' if j.get('early_stage') else 'full',corner=ids[0],far1=ids[1],far2=ids[2],stacks1=j['stacks'][0],stacks2=j['stacks'][1],predicted_side=j['predicted'],built_side=v,base_side=(1+base[n])*math.sqrt(n),built_minus_base=v-(1+base[n])*math.sqrt(n),source_status=status,seconds=sum(j.get('seconds',{}).values()),record=str(p)))
    fields=['n','phase','corner','far1','far2','stacks1','stacks2','predicted_side','built_side','base_side','built_minus_base','source_status','seconds','record']
    out=L/'results/stair-c-r25-2026-11-14.tsv'
    with open(str(out)+'.tmp','w') as f:
        w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['n'],r['built_side'],r['phase'])))
    os.replace(str(out)+'.tmp',out)
    for p in W.glob('archive/*/final-copy.tar.gz'):
        with tarfile.open(p) as tf:
            state=pickle.loads(tf.extractfile('state.pkl').read())
            counts[str(p)]=dict(build_attempts=state['built'],pending_builds=len(state['build']),pending_rank_requests=len(state['rank']),imported_inputs=len(state['imported']))
            for m in tf.getmembers():
                if m.name.startswith('logs/class') and m.name.endswith('.log'):
                    text=tf.extractfile(m).read().decode();lines=[x for x in text.splitlines() if x.startswith(('DONE','SCAN','CONTROL'))]
                    classes.append(dict(box=p.parent.name,log=m.name,lines=lines))
    nostarts=list(W.glob('boxcopy/*/raw-a/*.nostart'))
    contributions=[]
    for p in S.glob('take-*-r25/take.tsv'):
        if p==T/'take.tsv':continue
        for r in csv.DictReader(open(p),delimiter='\t'):
            if 'take-stair-c-r25/' not in r.get('source',''):continue
            n=int(r['n']);gain=base[n]-float(r['new'])
            if gain>1e-10:contributions.append(dict(n=n,take=str(p),score=float(r['new']),gain=gain))
    result=dict(full_builds=sum(r['phase']=='full' for r in rows),slp_exports=sum(r['phase']=='SLP' for r in rows),n_values=len({r['n'] for r in rows}),ineligible_stages=sum(r['source_status']!='traced source screen passed' for r in rows),refused_starts=len(nostarts),queues=counts,independent_classes=classes,contributions=contributions)
    (W/'measurements-final.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result

def final_take():
    base=C.basebar();b=C.bar();retained=[];gain=0.;beyond=0.
    for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
        n=int(r['n']);assert C.clean(r['source'],r['licence'])
        _,fr,score,why=C.floatsafe.work((n,C.rows(str(T/f'{n}.csv'))))
        if fr is None or score>=base[n]-1e-10 or score>=b[n]-1e-10:continue
        # Publication already requires a remote certified-file quench. Find
        # its immutable receipt again before the final retained row is counted.
        evidence=[]
        for p in W.glob('boxcopy/*/final/*.json'):
            j=json.load(open(p))
            if j['n']==n and j.get('certified_file_quench',{}).get('completed'):
                C.manifest(j);evidence.append(str(p))
        assert evidence,(n,'missing remote quench receipt')
        C.write(str(T/f'{n}.csv'),fr);r.update(held=repr(base[n]),new=repr(score),gain=repr(base[n]-score));retained.append(r)
        gain+=base[n]-score;beyond+=b[n]-score
    with open(T/'take.tsv.tmp','w') as f:
        w=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(retained)
    os.replace(T/'take.tsv.tmp',T/'take.tsv')
    keep={int(r['n']) for r in retained}
    for p in T.glob('*.csv'):
        if int(p.stem) not in keep:p.unlink()
    result=dict(improved_n=len(retained),against_base_bar=gain,beyond_other_live_r25=beyond)
    (W/'final-take-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result
if __name__=='__main__':
    if sys.argv[1]=='verify':verify(*sys.argv[2:5])
    elif sys.argv[1]=='measure':measure()
    elif sys.argv[1]=='take':final_take()
