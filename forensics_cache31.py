"""Retire a source only after its identity and geometry hashes both match."""
from pathlib import Path
import hashlib,json,pickle,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))


def retire(cache,request):
    index=int(request['index']);key,side,q=cache['src'][index]
    digest=hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
    if list(key)!=request['source'] or digest!=request['geometry_sha256']:
        raise ValueError('cache source identity or geometry differs')
    ids=cache['TI'];bad=(ids>=0)&(ids//8==index)
    removed=int(bad.sum());first=int(bad[...,0].sum())
    remap=np.arange(len(cache['src']));remap[index]=-1;remap[index+1:]-=1
    valid=ids>=0;old=ids[valid];mapped=remap[old//8]
    next_ids=np.where(mapped>=0,mapped*8+old%8,-1);ids[valid]=next_ids
    cache['TF'][ids<0]=np.inf
    order=np.argsort(cache['TF'],axis=-1,kind='stable')
    cache['TF']=np.take_along_axis(cache['TF'],order,axis=-1)
    cache['TI']=np.take_along_axis(ids,order,axis=-1)
    cache['src']=[v for i,v in enumerate(cache['src']) if i!=index]
    seen=(int(key[1]),hashlib.sha256(np.round(q,12).tobytes()).hexdigest())
    cache['seen'].discard(seen)
    return dict(source=list(key),geometry_sha256=digest,removed_slots=removed,removed_first_slots=first,sources_left=len(cache['src']))


def control():
    import copy
    q=np.array([[.5,.5,0.],[1.5,.5,0.]])
    other=q.copy();other[1,0]+=.02
    cache=dict(src=[(('old',2),2.,q),(('keep',2),2.02,other)],
        TF=np.array([[.1,.2,.3]]),TI=np.array([[0,8,9]]),
        seen={(2,hashlib.sha256(np.round(a,12).tobytes()).hexdigest()) for a in [q,other]})
    request=dict(index=0,source=['old',2],geometry_sha256=hashlib.sha256(q.tobytes()).hexdigest())
    untouched=copy.deepcopy(cache);before=pickle.dumps(untouched)
    try:retire(untouched,dict(request,geometry_sha256='0'*64))
    except ValueError:pass
    else:raise AssertionError('wrong geometry accepted')
    assert pickle.dumps(untouched)==before
    result=retire(cache,request)
    assert result['removed_slots']==1 and cache['TI'].tolist()==[[0,1,-1]]
    assert len(cache['src'])==1 and cache['src'][0][0]==('keep',2) and len(cache['seen'])==1
    print('CONTROL exact source retired; kept source and symmetries remapped; wrong hash preserves cache',flush=True)


if __name__=='__main__':
    if len(sys.argv)==1:control()
    else:
        import forensics_rect
        path=Path(sys.argv[1]);assert str(path)=='$SCRATCH/squares-forensics-r31/windows.pkl'
        request=json.loads(Path(sys.argv[2]).read_text());cache=pickle.load(path.open('rb'))
        result=retire(cache,request);forensics_rect.write_cache(path,cache)
        Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
