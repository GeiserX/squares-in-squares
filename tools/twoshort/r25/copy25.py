"""Copy the stopped boxE workspace and verify every remote file and link."""
from pathlib import Path
import hashlib,json,subprocess,shlex,os,time,datetime
W=Path(__file__).parent;R=W/'boxE25'
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(root,m):
 for name,want in m['files'].items():assert (root/name).is_file() and not (root/name).is_symlink() and digest(root/name)==want,name
 for name,want in m['symlinks'].items():assert (root/name).is_symlink() and os.readlink(root/name)==want,name
 for name in m.get('dirs',[]):assert (root/name).is_dir(),name
if __name__=='__main__':
 assert time.time()>=int((W/'deadline').read_text()),'wait for the common deadline'
 assert (W/'STOP-COLLECT').exists(),'stop the collector first'
 code='''from pathlib import Path
import hashlib,json,os
r=Path.home()/"scratch/squares-twoshort";files={};links={};dirs=[]
for p in sorted(r.rglob("*")):
 name=str(p.relative_to(r))
 if name in ["final-manifest.json","final-manifest.json.tmp"]:continue
 if p.is_symlink():links[name]=os.readlink(p)
 elif p.is_file():
  with p.open("rb") as f:files[name]=hashlib.file_digest(f,"sha256").hexdigest()
 elif p.is_dir():dirs.append(name)
m=dict(files=files,symlinks=links,dirs=dirs)
p=r/"final-manifest.json";q=p.with_suffix(".json.tmp");q.write_text(json.dumps(m,sort_keys=True,indent=2));q.replace(p)
with p.open("rb") as f:d=hashlib.file_digest(f,"sha256").hexdigest()
print(json.dumps(dict(sha256=d,files=len(files),symlinks=len(links),dirs=len(dirs))))'''
 run=subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(code)],capture_output=True,text=True,check=True,timeout=120);expected=json.loads(run.stdout);(W/'remote-manifest-expected.json').write_text(json.dumps(expected,indent=2))
 subprocess.run(['rsync','-az','boxE:scratch/squares-twoshort/',str(R)+'/'],check=True,timeout=300)
 assert digest(R/'final-manifest.json')==expected['sha256'];m=json.load(open(R/'final-manifest.json'));verify(R,m)
 archives=json.load(open(W/'archive-checks.json')) if (W/'archive-checks.json').exists() else []
 for row in archives:
  for name,h in row['files'].items():assert digest(R/'designs'/row['tag']/'lib'/name)==h,(row['tag'],name)
 result=dict(verified=True,files=expected['files']+1,symlinks=expected['symlinks'],dirs=expected['dirs'],archived_libraries=len(archives),archived_files=sum(len(row['files']) for row in archives),manifest_sha256=expected['sha256'],at=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ'))
 (W/'copy-verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
