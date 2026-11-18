"""Seed the remote archive using only byte-identical copies already collected locally."""
from pathlib import Path
import json,hashlib,shutil,os,time
W=Path(__file__).resolve().parent;D=W/'boxD-final';manifest=json.load((W/'boxCD-pre-manifest33.json').open());cache={};matched=0;copied=0;total=0;missing=[]
def same(p,r):
 if not p.is_file() or p.stat().st_size!=r['bytes']:return False
 st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns)
 if key not in cache:cache[key]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
 return cache[key]==r['sha256']
for name,r in manifest.items():
 target=D/name
 if same(target,r):matched+=1;total+=r['bytes'];continue
 pool=name.removeprefix('sources-').removeprefix('bars-').removesuffix('.json').removesuffix('.tsv').removesuffix('.csv')
 candidates=[W/'boxD-bridge33'/name,W/'boxE-final'/name,W/name,W/pool/name]
 if name=='fq':candidates.insert(0,W/'fq-boxCD33')
 p=next((p for p in candidates if same(p,r)),None)
 if p is None:missing.append(name);continue
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);os.utime(target,ns=(r['mtime_ns'],r['mtime_ns']));assert same(target,r);matched+=1;copied+=1;total+=r['bytes']
receipt={'time':time.strftime('%FT%TZ',time.gmtime()),'inventory_files':len(manifest),'inventory_bytes':sum(r['bytes'] for r in manifest.values()),'matched_files':matched,'copied_files':copied,'matched_bytes':total,'missing_files':missing,'final_manifest_still_required':True};(W/'boxCD-preseed33.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k!='missing_files'}));print('missing',missing[:12])
