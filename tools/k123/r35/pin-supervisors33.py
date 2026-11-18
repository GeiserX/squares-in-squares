from pathlib import Path
import subprocess,json
R=Path.home()/'scratch/squares-k123';out={}
for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:
 a=line.strip().split(None,1)
 if len(a)!=2:continue
 for name in ['third22.py','boxCD_guard33.py']:
  if a[1].endswith('python -I '+name):
   (R/(name+'.pid')).write_text(a[0]);out[name]=int(a[0])
print(json.dumps(out))
