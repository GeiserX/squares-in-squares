"""Keep complete audits by hash and expose a path-free diagnostic summary."""
from pathlib import Path
import json,hashlib,os
W=Path(__file__).resolve().parent

def write(path,result,raw=None):
 path=Path(path);raw=raw if raw is not None else json.dumps(result,indent=2).encode();h=hashlib.sha256(raw).hexdigest();D=W/'source-audit-archive32';D.mkdir(exist_ok=True);archive=D/(h+'.json')
 if not archive.exists():archive.write_bytes(raw)
 summary={'record_kind':'source audit diagnostic, no packing ancestry edges','n':result.get('n'),'clean':result.get('clean'),'checked_files':result.get('files'),'csv_sha256':result.get('csv_sha256'),'full_audit_sha256':h}
 q=path.with_name(path.name+'.'+str(os.getpid())+'.tmp');q.write_text(json.dumps(summary,indent=2));q.replace(path);return h

def main():
 changed=[]
 for p in (W/'admission-probes32').glob('*/admission-check32.json'):
  raw=p.read_bytes();r=json.loads(raw)
  if r.get('record_kind')=='source audit diagnostic, no packing ancestry edges':continue
  h=write(p,r,raw);changed.append({'receipt':str(p),'full_audit_sha256':h})
 (W/'diagnostic-normalized32.json').write_text(json.dumps(changed,indent=2));print(json.dumps({'diagnostic_receipts_normalized':len(changed),'packing_and_producer_bytes_changed':0}))
if __name__=='__main__':main()
