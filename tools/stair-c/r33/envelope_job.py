"""Build a native recipe only after the core-slide repair passes its real control."""
import hashlib,json,runpy,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import slide_envelope as S
receipt=json.loads(Path('slide-envelope-control.json').read_text());assert receipt['passed']and receipt.get('certified805_witnesses',0)>0
assert receipt['helper_sha256']==hashlib.sha256(Path('slide_envelope.py').read_bytes()).hexdigest()
S.install();path,a,b=sys.argv[1:4];n=json.loads(Path(path+'.json').read_text())['n'];sha=hashlib.sha256(Path(path).read_bytes()).hexdigest();sys.argv=['native_direct.py',path,a,b]
runpy.run_path('native_direct.py',run_name='__main__')
for suffix in ['.json','-slp.json']:
 p=Path('raw-a')/(f'{n}-native-direct-{sha[:12]}-{a}{b}'+suffix)
 if p.exists():
  j=json.loads(p.read_text());j['core_slide_envelope']=dict(control_sha256=hashlib.sha256(Path('slide-envelope-control.json').read_bytes()).hexdigest(),helper_sha256=receipt['helper_sha256']);p.write_text(json.dumps(j))
