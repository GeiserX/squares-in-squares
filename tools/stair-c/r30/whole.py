"""Give close whole rectangles one certified-file fq pass when they have no arm cut."""
import csv,hashlib,json,math,os,re

def eligible(n,side,bar):
    m=math.isqrt(n-1)
    return 28<=m<=31 and 17<=n-m*m<=45 and side<bar+.0016

def offer(C,path,n,payload):
    packing=C.M.np.asarray(C.M.read_layouts(path)[n],float)
    side=C.M.layout_state(packing)[0]
    if not eligible(n,side,(1+C.bar()[n])*math.sqrt(n)):return False
    meta=None
    for f in [path+'.json',path[:-4]+'.json']:
        if os.path.exists(f):
            try:meta=json.load(open(f));break
            except ValueError:pass
    if not meta or not meta.get('parts'):return False
    record=C.bounded_audit(C.rectangle3.audit,path,n,meta)
    if record is None:return False
    digest=hashlib.sha256(payload).hexdigest()
    if hashlib.sha256(open(path,'rb').read()).hexdigest()!=digest:return False
    snapshot=C.WORK+'/donors/whole-'+str(n)+'-'+digest[:12]+'.csv'
    open(snapshot,'wb').write(payload)
    _,rows,score,reason=C.floatsafe.work((n,C.rows(snapshot)))
    if rows is None:return False
    name=f'{n}-whole-{digest[:12]}'
    dest=C.WORK+'/cert-in/'+name+'.csv';os.makedirs(os.path.dirname(dest),exist_ok=True)
    C.write(dest,rows)
    j=dict(n=n,built=side,predicted=side,stacks=[0,0],whole_layout_follow=True,source_snapshot=path,source_sha256=digest,
           modules=[dict(id=str(n)+'-whole-layout',source=record['source'],licence=record['licence'])])
    with open(dest[:-4]+'.json','w')as f:json.dump(j,f)
    host=C.HOSTS[n%3][0]
    r=C.run(['rsync','-a',dest,dest[:-4]+'.json',host+':scratch/squares-stair-c/cert-in/'])
    if r.returncode:return False
    C.state('QUENCH whole readable CSV without arm cut '+path+' pinned '+digest+' on '+host+' side margin '+repr(side-(1+C.bar()[n])*math.sqrt(n))+'; deadline17:45Z')
    return True
if __name__=='__main__':
    assert eligible(986,31.8477,31.8475)
    assert not eligible(986,31.85,31.8475)
    assert not eligible(915,30.74,30.75)
    print('CONTROL whole follow: close986 admitted; far986 and count915 outside slice refused')
