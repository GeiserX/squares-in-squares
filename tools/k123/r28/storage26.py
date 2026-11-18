"""Archive finished numerical outputs before pruning large no-find CSVs on boxE."""
import pathlib,subprocess,time,json,resource
W=pathlib.Path(__file__).resolve().parent
import fcntl,os,sys,runpy
try:runpy.run_path(str(W/'intermediate28.py'),run_name='__main__')
except SystemExit:pass
if (W/'restart-stage28').exists():
 (W/'restart-stage28').unlink();os.execv(sys.executable,[sys.executable,str(W/'resident25.py'),'stage'])
# Bound warm source caches on the 16 GB collector. Restart only at a collection boundary.
try:
 pid=int((W/'collect.pid').read_text());rss=int(subprocess.check_output(['ps','-p',str(pid),'-o','rss='],text=True).strip() or 0)
 if rss>1500000 and not (W/'restart-collect25').exists():
  (W/'restart-collect25').touch()
  with (W.parent/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA QUEUE collector cache restart at RSS{rss}KB, boundary marker work/restart-collect25; numeric slots unchanged. Deadline05:45Z.\n')
except (OSError,ValueError,subprocess.CalledProcessError):pass
with open(W/'storage26.lock','a') as storage_lock:
 try:fcntl.flock(storage_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise SystemExit
 expiry=W/'priority199-expiry'
 if expiry.exists() and time.time()>float(expiry.read_text()):
  (W/'priority-reset26.json').write_text('{}')
  subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r28-ssh',str(W/'priority-reset26.json'),'boxE:scratch/squares-k123/prior-trials.reset'],check=True)
  subprocess.run(['ssh','-S','/tmp/squares-k123-r28-ssh','boxE','cd $SCRATCH/squares-k123 && mv prior-trials.reset prior-trials.json'],check=True)
  expiry.unlink()
  with (W.parent/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH temporary199 priority window; restored ordinary trial balance. Deadline05:45Z.\n')
 marker=W/'storage-last26'
 if marker.exists() and time.time()-marker.stat().st_mtime<300:raise SystemExit
 marker.touch()
 cmd=['ssh','-S','/tmp/squares-k123-r28-ssh','boxE']
 size=int(subprocess.check_output(cmd+['du -sk $SCRATCH/squares-k123'],text=True).split()[0])*1024
 if size<1400000000:print('storage bytes',size);raise SystemExit
 D=W/'boxE-checkpoint';D.mkdir(exist_ok=True)
 text=subprocess.check_output(cmd+['cd $SCRATCH/squares-k123 && cat out/j22*/done.jsonl'],text=True)
 keys=[]
 for line in text.splitlines():
  try:r=json.loads(line)
  except ValueError:continue
  if r.get('raw') or r.get('error'):continue
  keys.append(r['worker']+'/'+r['pool']+'-'+str(r['n'])+'-'+r['tag'])
 keys=sorted(set(keys));(W/'archive-dry-keys26.json').write_text(json.dumps(keys));(W/'archive-dry-list26.txt').write_text(chr(10).join(k+'/' for k in keys)+chr(10))
 assert len((W/'archive-dry-list26.txt').read_text().splitlines())==len(keys),'bad archive list separators'
 (D/('dry-records-'+str(int(time.time()))+'.jsonl')).write_text(text)
 soft,hard=resource.getrlimit(resource.RLIMIT_NOFILE)
 resource.setrlimit(resource.RLIMIT_NOFILE,(max(soft,4096 if hard==resource.RLIM_INFINITY else min(4096,hard)),hard))
 for offset in range(0,len(keys),16):
  batch=keys[offset:offset+16];listing=W/'archive-batch26.txt';listing.write_text(chr(10).join(k+'/' for k in batch)+chr(10))
  subprocess.run(['rsync','-azr','--rsync-path=ulimit -n 4096; rsync','-e','ssh -S /tmp/squares-k123-r28-ssh','--files-from='+str(listing),'boxE:scratch/squares-k123/out/',str(D/'out')+'/'],check=True)
 assert all((D/'out'/k).is_dir() for k in keys),'missing archived completed directory'
 # The pruning list was frozen before copying. No newly completed job is eligible.
 script="import pathlib,json\nR=pathlib.Path.home()/'scratch/squares-k123';removed=0\nfor key in json.load(open(R/'archive-dry-keys26.json')):\n for p in (R/'out'/key).rglob('*.csv'):\n  removed+=p.stat().st_size;p.unlink()\nprint(removed)\n"
 job=W/'prune-dry26.py';job.write_text(script)
 for path in [job,W/'archive-dry-keys26.json']:
  subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r28-ssh',str(path),'boxE:scratch/squares-k123/'+path.name],check=True)
 result=subprocess.check_output(cmd+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I prune-dry26.py'],text=True).strip()
 with (W.parent/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA ARCHIVE frozen set of{len(keys)} completed dry boxE jobs at{size} bytes, pruned{result} bytes only after successful copy and local directory checks. New completions remain untouched. Log work/boxE-checkpoint; deadline05:45Z.\n')
 print('storage',size,'frozen jobs',len(keys),'pruned',result)
