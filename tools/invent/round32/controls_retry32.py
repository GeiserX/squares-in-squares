"""Reopen a source refusal only when its metadata bytes change."""
import pathlib,sys,json,tempfile,os
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));from campaign32 import source_signature
with tempfile.TemporaryDirectory(dir=W)as d:
 p=pathlib.Path(d)/'2.csv';p.write_text('n,x,y,angle\n');meta=pathlib.Path(str(p)+'.json');meta.write_text('{"source":"before"}')
 before=source_signature(p);st=meta.stat();os.utime(meta,ns=(st.st_atime_ns,st.st_mtime_ns+1000000));assert source_signature(p)==before
 meta.write_text('{"source":"repaired"}');assert source_signature(p)!=before
result=dict(timestamp_only_change_stays_closed=True,changed_source_bytes_reopen=True);(W/'controls-retry32.json').write_text(json.dumps(result));print(json.dumps(result))
