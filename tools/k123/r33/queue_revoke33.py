"""Apply a new source refusal to pending scans and cancel only affected numerical children."""
from pathlib import Path
import os,json,subprocess,re,signal
R=Path.home()/'scratch/squares-k123';bad=json.load((R/'refused-inputs26.json').open());filtered=[]
for p in (R/'tasks').glob('*.json'):
 try:j=json.load(p.open())
 except (ValueError,OSError):continue
 if j.get('kind')!='scan' and not j.get('diversity_scan'):continue
 pool=j['tag'];ns=set(bad.get(pool,[]));f=R/('pairs-'+pool+'.txt')
 if not ns or not f.exists():continue
 keep=[s for s in f.read_text().split() if not set(s.split(','))&ns];tmp=f.with_suffix('.tmp');tmp.write_text(' '.join(keep));tmp.replace(f);filtered.append(pool)
 if not keep:p.unlink(missing_ok=True)
killed=[]
for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:
 a=line.strip().split(None,1)
 if len(a)!=2 or str(R)+'/out/' not in a[1]:continue
 pid=int(a[0]);cmd=a[1]
 for pool,ns in bad.items():
  m=re.search(re.escape(pool)+r'-\d+-(\d+)r?-(\d+)r?-j',cmd)
  if m and set(m.groups())&set(ns):
   # Numerical children start their own process group in qrun22.py.
   if os.getpgid(pid)==pid:
    try:os.killpg(pid,signal.SIGTERM);killed.append(pid)
    except ProcessLookupError:pass
   break
(R/'queue-revocations33.json').write_text(json.dumps({'filtered_scans':filtered,'cancelled_children':killed}));print(json.dumps({'filtered_scans':len(filtered),'cancelled_children':killed}))
