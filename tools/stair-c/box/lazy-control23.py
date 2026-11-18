import fcntl,hashlib,json,os,pathlib,subprocess,sys,tarfile,time
root=pathlib.Path('lazy-control');root.mkdir(exist_ok=True)
for name in ['lib-don-a','lib-mod-b']:
 p=root/name;p.mkdir(exist_ok=True);(p/'library.pkl').write_bytes(b'packing control\n');(p/'lens.pkl').write_bytes(b'length control\n')
(root/'pool-locks').mkdir(exist_ok=True);h=open(root/'pool-locks/lib-mod-b.lock','a');fcntl.flock(h,fcntl.LOCK_SH)
(root/'LAZY_ARCHIVE_READY').write_text('fixture');(root/'deadline').write_text(str(time.time()+60))
(root/'q.txt').write_text('queued-build ./py -I lane/modules.py job lib-don-a raw details test 975 rest\n')
subprocess.run([sys.executable,'-I',str(pathlib.Path('storage23.py').resolve())],cwd=root,check=True)
a=root/'pool-archive/lib-don-a.tar.gz';assert a.exists() and not (root/'lib-don-a').exists() and (root/'lib-mod-b/library.pkl').exists()
manifest=json.load(open(str(a)+'.sha256.json'))
with tarfile.open(a) as tf:
 for m in tf.getmembers():
  data=tf.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==manifest[m.name];assert hashlib.sha256(data+b'bad').hexdigest()!=manifest[m.name]
subprocess.run([sys.executable,'-I',str(pathlib.Path('guard.py').resolve()),sys.executable,'-c',"from pathlib import Path; assert Path('lib-don-a/library.pkl').read_bytes()==b'packing control\\n'",'lib-don-a'],cwd=root,check=True)
assert (root/'lib-don-a/lens.pkl').read_bytes()==b'length control\n' and 'queued-build' in (root/'q.txt').read_text()
pathlib.Path('LAZY_ARCHIVE_READY').write_text('verified')
print('CONTROL lazy archive verified2 members; changed bytes rejected; active pool kept; pending queue retained; guard restored exact library before command',flush=True)
