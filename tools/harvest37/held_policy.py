"""Apply main's12:40:55 UTC ruling to withdrawn ancestor-share diagnostics."""
import re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))

def void_share(line):
    if re.search(r'CC.BY.SA|penguin|joegun|missing|changed since|incomplete|node.cap|unresolved|capture race',line,re.I):return False
    return bool(re.search(r'public.first (?:held )?ancestor|held.ancestor.{0,60}share|share.{0,60}held.ancestor|source proof fails archived.public audit|tree reaches.{0,180}share|SOURCE_NOTICES,.{0,100}share',line,re.I))


def control():
    import csv,hashlib,tempfile
    from pathlib import Path
    from common import W,S
    from policy import prvsiyan
    import public_sources as P
    with tempfile.TemporaryDirectory(dir=W) as folder:
        p=Path(folder)/'858.csv'
        with p.open('w') as f:
            out=csv.DictWriter(f,fieldnames=['n','x','y']);out.writeheader()
            out.writerows(dict(n=858,x=x,y=y) for x,y in prvsiyan()[858])
        j=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),kind='fresh-public',source='example/public-file :: submission.csv',n=858)
        try:P.check_job(j)
        except ValueError:pass
        else:raise AssertionError('public-first root share passed')
        own=dict(j,kind='fresh-follow',source='own construction',public_first=False)
        assert P.check_job(own)==[]
        try:P.check_job(dict(j,walk=dict(helds=['801@None'])))
        except ValueError:pass
        else:raise AssertionError('unrelated held branch suppressed a direct public root')
        from held_paths import audit
        root=str(Path(folder)/'owned.csv')
        node=(str(p),str(p),j['sha256'])
        meta=str(p)+'.source.json'
        text={root:'own construction from held801', 'held 801 None':'parent '+str(p),str(p):'',meta:'{"source":"example/public-file :: submission.csv"}'}
        assert audit(root,text,{str(p):str(p)},[node])[0]==[]
        text[root]+='; direct parent '+str(p)
        try:audit(root,text,{str(p):str(p)},[node])
        except ValueError:pass
        else:raise AssertionError('direct bad public parent passed beside held branch')
        import json
        boundary=dict(path=str(S/'gather/round28-2026-11-15b.csv'),n=858,upstream=str(p))
        text[root]=json.dumps(dict(parents=[boundary]))
        assert audit(root,text,{str(p):str(p)},[node])[0]==[]
        text[root]=json.dumps(dict(parents=[boundary],direct_parent=str(p)))
        try:audit(root,text,{str(p):str(p)},[node])
        except ValueError:pass
        else:raise AssertionError('direct sibling of submitted held JSON node passed')
        text[root]=json.dumps(dict(parents=[dict(boundary,path=str(W/'unregistered.csv'))]))
        try:audit(root,text,{str(p):str(p)},[node])
        except ValueError:pass
        else:raise AssertionError('unregistered held JSON-node claim passed')
        origin=dict(boundary,source='example/public-file :: submission.csv')
        assert not P.source_record_public(origin,858)
        origins={str(p)+'.origin.json':json.dumps(origin)}
        assert not P.public_node(str(p),858,origins,{str(p):str(p)})
        origins[str(p)+'.source.json']=json.dumps(dict(kind='fresh-public',source=origin['source']))
        assert P.public_node(str(p),858,origins,{str(p):str(p)})
    assert void_share('WITHDRAW376: public-first held ancestors376/547 share0.755/1.0')
    assert not void_share('WITHDRAW376: public-first ancestor share0.755 and missing parent')
    assert not void_share('WITHDRAW source prvsiyan/squares-verified-best-of-1105')
    print('CONTROL public-first root858 rejected; own and held-only paths exempt; direct bad parent beside held branch rejected; missing parent and actual1105 source remain excluded',flush=True)

if __name__=='__main__':control()
