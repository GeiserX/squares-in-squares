import fcntl,glob,hashlib,json,os,shutil,subprocess,tarfile,time
if not os.path.exists('LAZY_ARCHIVE_READY'):raise SystemExit('lazy archive control pending')
os.makedirs('pool-archive',exist_ok=True);os.makedirs('pool-locks',exist_ok=True)
cmds=subprocess.check_output(['ps','-axo','command'],text=True).splitlines()
for pool in sorted(glob.glob('lib-don-*')+glob.glob('lib-mod-*'),key=lambda p:os.stat(p).st_mtime):
 if not os.path.exists(pool+'/library.pkl'):continue
 if any((' '+pool+' ') in (' '+c+' ') for c in cmds):continue
 lock=open('pool-locks/'+pool+'.lock','a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:lock.close();continue
 archive='pool-archive/'+pool+'.tar.gz';manifest={}
 try:
  with tarfile.open(archive+'.tmp','w:gz',compresslevel=2) as tf:
   for root,dirs,files in os.walk(pool):
    for fn in files:
     src=os.path.join(root,fn);data=open(src,'rb').read();manifest[src]=hashlib.sha256(data).hexdigest();tf.add(src,arcname=src)
  with tarfile.open(archive+'.tmp','r:gz') as tf:
   for m in tf.getmembers():
    if m.isfile():assert hashlib.sha256(tf.extractfile(m).read()).hexdigest()==manifest[m.name]
  os.replace(archive+'.tmp',archive);json.dump(manifest,open(archive+'.sha256.json','w'));shutil.rmtree(pool)
  print(time.strftime('%FT%TZ',time.gmtime()),'ARCHIVE',pool,'verified members',len(manifest),'bytes',os.path.getsize(archive),'queued work retained; guard restores on demand',flush=True)
 finally:lock.close()
 break
