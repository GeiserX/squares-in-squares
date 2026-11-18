"""Bind a withdrawal to named packing bytes, never to every later file at its path."""
import datetime,hashlib,json,os,re
from pathlib import Path

def tokens(lines,cache,root):
    out=set()
    for line in lines:
        if not re.search(r'->[^:]+:\s*(?:WITHDRAW(?:N)?|WITHHOLD|SOURCE-HOLD)\b',line,re.I):continue
        try:when=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
        except(ValueError,IndexError):continue
        paths=set(re.findall(r'(?:'+re.escape(root)+r'/)?take-[a-z0-9-]+-r\d+/[^\s,;()]+\.csv',line))
        for value in paths:
            p=value if value.startswith('/')else root+'/'+value
            key=hashlib.sha256((line+'\0'+p).encode()).hexdigest();entry=cache.get(key)
            pin=re.search(re.escape(value)+r'[^;\n]{0,40}?sha256(?: prefix)?\s*[:=]?\s*([0-9a-f]{12,64})\b',line,re.I)
            digest=pin[1]if pin else entry.get('sha256')if entry else None
            if digest is None:
                q=Path(p)
                # A later timestamp is ambiguous. It may already be a replacement build.
                if q.exists()and q.stat().st_mtime<=when:digest=hashlib.sha256(q.read_bytes()).hexdigest()
            if digest:
                cache[key]=dict(path=p,sha256=digest,withdrawn_at=when,line=line)
                for path in[p,p.removeprefix(root+'/')]:
                    out.add(path+' immutable sha256 '+digest);out.add(path+' sha256 '+digest)
    return sorted(out)

if __name__=='__main__':
    import tempfile
    with tempfile.TemporaryDirectory()as folder:
        root=Path(folder);q=root/'take-control-r30/805.csv';q.parent.mkdir();q.write_bytes(b'old packing');os.utime(q,(1,1));cache={}
        line='2026-11-15T07:00:00Z control -> all: WITHDRAW '+str(q)
        old=hashlib.sha256(q.read_bytes()).hexdigest();t=tokens([line],cache,folder)
        assert str(q)+' immutable sha256 '+old in t
        q.write_bytes(b'new packing');new=hashlib.sha256(q.read_bytes()).hexdigest();t=tokens([line],cache,folder)
        assert str(q)+' immutable sha256 '+new not in t and str(q)+' immutable sha256 '+old in t
        assert tokens(['2026-11-15T07:00:00Z control -> all: certified805 keeps '+str(q)+'; not the withheld X'],{},folder)==[]
        assert tokens([line],{},folder)==[],'a replacement seen after the withdrawal must not be pinned as old'
    print('CONTROL withdrawal: old byte pin retained; replacement admitted; retention note ignored; late ambiguous path left unpinned')
