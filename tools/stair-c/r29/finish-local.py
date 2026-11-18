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
    base=C.basebar();rows=[];nostarts=[];counts={};classes=[];experiments={}
    for p in sorted(W.glob('boxcopy/*/raw-a/*.json')):
        j=json.load(open(p));n=j['n'];v=j.get('built')
        if v is None:continue
        try:C.manifest(j);status='module source screen passed'
        except ValueError as e:status=str(e)
        ids=[q['id'] for q in j['modules']]
        rows.append(dict(n=n,phase='SLP' if j.get('early_stage') else 'full',corner=ids[0],far1=ids[1],far2=ids[2],stacks1=j['stacks'][0],stacks2=j['stacks'][1],predicted_side=j['predicted'],built_side=v,base_side=(1+base[n])*math.sqrt(n),built_minus_base=v-(1+base[n])*math.sqrt(n),source_status=status,seconds=sum(j.get('seconds',{}).values()),record=str(p)))
    fields=['n','phase','corner','far1','far2','stacks1','stacks2','predicted_side','built_side','base_side','built_minus_base','source_status','seconds','record']
    out=L/'results/stair-c-r29-2026-11-15.tsv'
    with open(str(out)+'.tmp','w') as f:
        w=csv.DictWriter(f,fields,delimiter='\t');w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['n'],r['built_side'],r['phase'])))
    os.replace(str(out)+'.tmp',out)
    for p in W.glob('archive/*/final-copy.tar.gz'):
        with tarfile.open(p) as tf:
            state=pickle.loads(tf.extractfile('state.pkl').read())
            counts[str(p)]=dict(build_attempts=state['built'],pending_builds=len(state['build']),deferred_builds=len(state.get('deferred',[])),pending_rank_requests=len(state['rank']),imported_inputs=len(state['imported']))
            for name in ['corner-paths-control.json','corner-paths-probes.json','native-direct-control.json','grid-probes.json','corner-guard-control.json','guard-grid-probes.json','corner-stacks-control.json','stacks-grid-probes.json','two-stacks-control.json','bar-kick-control.json','bar-control-starts.json']:
                try:raw=tf.extractfile(name).read()
                except KeyError:continue
                key=hashlib.sha256(raw).hexdigest();values=experiments.setdefault(name,{})
                if key not in values:values[key]=dict(receipt_sha256=key,boxes=[],result=json.loads(raw))
                values[key]['boxes'].append(p.parent.name)
            for m in tf.getmembers():
                if m.name.startswith('logs/class') and m.name.endswith('.log'):
                    text=tf.extractfile(m).read().decode();lines=[x for x in text.splitlines() if x.startswith(('DONE','SCAN','CONTROL'))]
                    classes.append(dict(box=p.parent.name,log=m.name,lines=lines))
    nostarts=list(W.glob('boxcopy/*/raw-a/*.nostart'))
    contributions=[]
    for p in S.glob('take-*-r29/take.tsv'):
        if p==T/'take.tsv':continue
        for r in csv.DictReader(open(p),delimiter='\t'):
            if 'take-stair-c-r29/' not in r.get('source',''):continue
            n=int(r['n']);gain=base[n]-float(r['new'])
            if gain>1e-10:contributions.append(dict(n=n,take=str(p),score=float(r['new']),gain=gain))
    close={}
    for row in rows:
        n=row['n'];delta=row['built_minus_base']
        if row['phase']=='full' and row['source_status']=='module source screen passed' and delta>1e-8:
            if n not in close or delta<close[n]['side_margin']:close[n]=dict(n=n,side_margin=delta,score_margin=delta/math.sqrt(n),record=row['record'])
    closest=[];closest_unresolved=[]
    for item in sorted(close.values(),key=lambda q:q['score_margin'])[:8]:
        p=Path(item['record']);j=json.load(open(p))
        full=C.full_admission(str(p.with_suffix('.csv')),j['n'],C.manifest(j))
        (closest if full is not None else closest_unresolved).append(item)
        if len(closest)>=5:break
    whole=[];controls=[]
    for p in W.glob('boxcopy/*/final/*.json'):
        j=json.load(open(p));r=j.get('certified_file_quench',{})
        if j.get('whole_layout_follow') or j.get('control_only'):
            item=dict(n=j['n'],path=str(p),completed=r.get('completed',False),seconds=r.get('seconds'),start=r.get('start'),end=r.get('end'),returncode=r.get('returncode'),input_sha256=r.get('input_sha256'),kick=j.get('source_kick'))
            if item['completed']:
                _,certified,score,_=C.cert_cache.certify(str(p.with_suffix('.csv')),j['n'])
                if certified is not None:item['certified_side']=(1+score)*math.sqrt(j['n'])
            (controls if j.get('control_only') else whole).append(item)
    result=dict(closest_full=closest,whole_requested=sum(bool(json.load(open(p)).get('whole_layout_follow'))for p in (W/'cert-in').glob('*.json')),whole_follows=whole,fq_controls=controls,full_builds=sum(r['phase']=='full' for r in rows),slp_exports=sum(r['phase']=='SLP' for r in rows),n_values=len({r['n'] for r in rows}),ineligible_stages=sum(r['source_status']!='module source screen passed' for r in rows),refused_starts=len(nostarts),queues=counts,independent_classes=classes,contributions=contributions)
    result['whole_completed']=sum(v['completed'] for v in whole)
    result['closest_unresolved']=closest_unresolved
    if (W/'own-near-full-audits.json').exists():
        result['own_near_audits']=[dict(name=k,ok=v['ok'],proof=(v.get('record') or {}).get('proof')) for k,v in json.load(open(W/'own-near-full-audits.json')).items()]
    expanded=[];guarded=[];following=[];probed=[];failed_probes=0
    for p in W.glob('boxcopy/*/raw-a/*.json'):
        j=json.load(open(p))
        if j.get('early_stage')or j.get('built')is None:continue
        item=dict(n=j['n'],side=j['built'],margin=j['built']-(1+base[j['n']])*math.sqrt(j['n']),record=str(p))
        if j.get('native_direct_geometry')or any('r29expand'in q.get('id','')or'r29native'in q.get('id','')for q in j.get('modules',[])):expanded.append(item)
        if any('r29guard'in q.get('id','')for q in j.get('modules',[])):guarded.append(item)
        if any('r29stacks'in q.get('id','')for q in j.get('modules',[])):following.append(item)
        if j.get('bar_start_probe'):probed.append(item)
    for p in W.glob('boxcopy/*/raw-a/*.nostart'):
        j=json.load(open(p))
        if j.get('bar_start_probe')and not p.with_suffix('.json').exists():failed_probes+=1
    result['expanded_corner_full']=expanded;result['bar_probe_full']=probed;result['bar_probe_failed']=failed_probes
    result['guarded_corner_full']=guarded
    result['following_stacks_full']=following
    result['two_stack_transfer_full']=[r for r in following if 'r29stacks2' in Path(r['record']).read_text()]
    result['experimental_receipts']={name:list(values.values())for name,values in experiments.items()}
    result['native_direct_full']=[str(p)for p in W.glob('boxcopy/*/raw-a/*.json')if (lambda j:j.get('native_direct_geometry')and not j.get('early_stage')and j.get('built')is not None)(json.load(open(p)))]
    if(W/'byte-recovery-all.json').exists():
        recovered=json.load(open(W/'byte-recovery-all.json'));ids=set(recovered['modules'])
        result['byte_recovery']=dict(restored=recovered['restored'],approved_versions=sum(r['passed']for r in recovered['roots']),paths=len(recovered['aliases']),deferred=len(recovered['deferred']),receipt=str(W/'byte-recovery-all.json'))
        result['recovered_module_full']=[r for r in rows if r['phase']=='full'and any(r[k]in ids for k in['corner','far1','far2'])]
    if(W/'saved-all-receipt.json').exists():result['saved_recovery']=json.load(open(W/'saved-all-receipt.json'))
    if(W/'follow-repair-control.json').exists():
        before=json.load(open(W/'follow-state-before-repair.json'));after=json.load(open(W/'follow-driver-state.json'))
        result['follow_repair']=dict(control=json.load(open(W/'follow-repair-control.json')),new_offers=[dict(key=k,**v)for k,v in after.items()if v.get('ok')and not before.get(k,{}).get('ok')])
    if(W/'kick-phase-control.json').exists():result['kick_phase']=json.load(open(W/'kick-phase-control.json'))
    if(W/'bar-kick-control.json').exists():result['bar_input_control']=json.load(open(W/'bar-kick-control.json'))
    if(W/'bar-leg-queued.json').exists():result['bar_input_leg']=json.load(open(W/'bar-leg-queued.json'))
    (W/'measurements-final.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result

def final_take():
    base=C.basebar();b=C.bar();retained=[];gain=0.;beyond=0.
    for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
        n=int(r['n'])
        if not C.clean(r['source'],r['licence']):
            C.hand('WITHDRAW n='+str(n)+' after final source proof revalidation, '+str(T/f'{n}.csv'))
            continue
        _,fr,score,why=C.floatsafe.work((n,C.rows(str(T/f'{n}.csv'))))
        if fr is None or score>=base[n]-1e-10 or score>=b[n]-1e-10:continue
        # Publication already requires a remote certified-file quench. Find
        # its immutable receipt again before the final retained row is counted.
        evidence=[]
        for p in W.glob('boxcopy/*/final/*.json'):
            j=json.load(open(p))
            if j['n']==n and not j.get('control_only') and j.get('certified_file_quench',{}).get('completed'):
                try:meta=C.manifest(j)
                except ValueError:continue
                if C.full_admission(str(p.with_suffix('.csv')),n,meta) is None:continue
                _,other,other_score,_=C.floatsafe.work((n,C.rows(str(p.with_suffix('.csv')))))
                coordinates=lambda rr:[(r['square_id'],r['x'],r['y'],r['angle']) for r in rr]
                if other is not None and coordinates(other)==coordinates(fr):evidence.append(str(p))
        if not evidence:
            C.hand('WITHDRAW n='+str(n)+' because no matching quench receipt passed the full source check, '+str(T/f'{n}.csv'))
            continue
        C.write(str(T/f'{n}.csv'),fr);r.update(held=repr(base[n]),new=repr(score),gain=repr(base[n]-score));retained.append(r)
        gain+=base[n]-score;beyond+=b[n]-score
    with open(T/'take.tsv.tmp','w') as f:
        w=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(retained)
    os.replace(T/'take.tsv.tmp',T/'take.tsv')
    keep={int(r['n']) for r in retained}
    for p in T.glob('*.csv'):
        if int(p.stem) not in keep:p.unlink()
    result=dict(improved_n=len(retained),against_base_bar=gain,beyond_other_live_r29=beyond)
    (W/'final-take-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return result
if __name__=='__main__':
    if sys.argv[1]=='verify':verify(*sys.argv[2:5])
    elif sys.argv[1]=='measure':measure()
    elif sys.argv[1]=='take':final_take()
