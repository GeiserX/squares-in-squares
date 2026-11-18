import hashlib,json,os,pathlib,shlex,subprocess,sys
host,key=sys.argv[1:];root=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r23/work/archive')/key;root.mkdir(parents=True,exist_ok=True)
code='''import hashlib,json,os
from pathlib import Path
R=Path('.');d={}
for path,dirs,files in os.walk(R,followlinks=False):
 if path=='.':dirs[:]=[x for x in dirs if x not in ('venv','libbase','tmp')]
 for name in files+dirs:
  p=Path(path)/name;s=str(p)
  if s=='archive-manifest.json':continue
  if p.is_symlink():d[s]={'link':os.readlink(p)}
  elif p.is_file():
   h=hashlib.sha256()
   with open(p,'rb') as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
   d[s]={'size':p.stat().st_size,'sha256':h.hexdigest()}
Path('archive-manifest.json').write_text(json.dumps(d,sort_keys=True,indent=2))
print(len(d),'manifest entries')
'''
subprocess.run(['ssh','-n',host,'cd $SCRATCH/squares-stair-c && ./py -I -c '+shlex.quote(code)],check=True)
subprocess.run(['rsync','-az','--exclude=venv','--exclude=libbase','--exclude=tmp',host+':scratch/squares-stair-c/',str(root)+'/'],check=True)
d=json.loads((root/'archive-manifest.json').read_text());bad=[]
for name,r in d.items():
 p=root/name
 if 'link' in r:
  if not p.is_symlink() or os.readlink(p)!=r['link']:bad.append(name)
 elif not p.is_file() or p.stat().st_size!=r['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:bad.append(name)
assert not bad,bad
result={'host':host,'entries':len(d),'bytes':sum(r.get('size',0) for r in d.values()),'verified':True,'excluded':['venv','libbase','tmp']}
(root/'copy-verified.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
