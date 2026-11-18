"""Rebind old byte pins to recovered snapshots while retaining source checks."""
import hashlib,json,re
from pathlib import Path
PIN=re.compile(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.csv) ((?:immutable )?sha256) ([0-9a-f]{12,64})')
REF=re.compile(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.json)')

class Rebind:
    def __init__(self,aliases,folder):
        self.aliases=aliases;self.folder=Path(folder);self.folder.mkdir(exist_ok=True);self.cache={};self.active=set();self.changed=[]
    def text(self,value):
        def csv_pin(m):
            replacement=self.aliases.get(m[1])
            if not replacement:return m[0]
            candidates=[replacement]if isinstance(replacement[0],(str,Path))else replacement
            for path,digest in candidates:
                if not digest.startswith(m[3]):continue
                assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
                return str(path)+' '+m[2]+' '+digest
            return m[0]
        value=PIN.sub(csv_pin,value)
        for old in set(REF.findall(value)):
            new=self.file(old)
            if new!=old:
                value=value.replace(old,new)
                # Compact ancestry records name the hash of their JSON bytes.
                value=re.sub(re.escape(new)+r' ((?:immutable )?sha256) [0-9a-f]{12,64}',lambda m:new+' '+m[1]+' '+Path(new).stem,value)
        return value
    def walk(self,value):
        if isinstance(value,str):return self.text(value)
        if isinstance(value,list):return [self.walk(v)for v in value]
        if isinstance(value,dict):return {k:self.walk(v)for k,v in value.items()}
        return value
    def file(self,path):
        if path in self.cache:return self.cache[path]
        if path in self.active or not Path(path).is_file():return path
        self.active.add(path)
        try:
            original=json.loads(Path(path).read_text());changed=self.walk(original)
            if changed==original:new=path
            else:
                raw=json.dumps(changed,sort_keys=True,separators=(',',':')).encode();digest=hashlib.sha256(raw).hexdigest();dest=self.folder/(digest+'.json')
                if dest.exists():assert dest.read_bytes()==raw
                else:dest.write_bytes(raw)
                new=str(dest);self.changed.append(dict(old=path,new=new,sha256=digest))
            self.cache[path]=new;return new
        finally:self.active.remove(path)
