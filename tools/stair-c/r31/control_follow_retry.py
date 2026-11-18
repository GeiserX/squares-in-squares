"""Retry a failed offer and let an inadmissible best row yield to a valid row."""
import hashlib,importlib.util,pathlib,sys,tempfile,time
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H))
s=importlib.util.spec_from_file_location('follow_retry_control',H/'follow_driver.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
with tempfile.TemporaryDirectory(prefix='stair-c-retry-')as folder:
    p=pathlib.Path(folder)/'first.csv';q=pathlib.Path(folder)/'second.csv';p.write_text('first');q.write_text('second')
    key='812'+hashlib.sha256(p.read_bytes()).hexdigest();seen={key:dict(n=812,side=29.,ok=False,reason='old missing parent')};calls=[]
    assert D.offer_options(812,[(29.,p),(29.000001,q)],seen,offer=lambda p:calls.append(p),log=lambda x:None)
    assert calls==[p]and seen[key]['ok']
    seen={};calls=[]
    def offer(path):
        calls.append(path)
        if path==p:raise ValueError('unresolved source')
    assert D.offer_options(812,[(29.,p),(29.000001,q)],seen,offer=offer,log=lambda x:None)
    assert calls==[p,q]and not seen[key]['ok']and seen[key]['retry_at']>time.time()
    calls.clear();assert not D.offer_options(812,[(29.,p),(29.000001,q)],seen,offer=offer,log=lambda x:None)
    assert not calls
print('CONTROL follow retry: failed offer retried; unresolved closest row did not hide admitted fallback; failure backoff and successful-count cap preserved')
