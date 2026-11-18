import subprocess,os,signal
rows=[]
for l in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 a=l.strip().split(None,2)
 if len(a)==3:rows.append((int(a[0]),int(a[1]),a[2]))
ids=[p for p,pp,c in rows if c.endswith('python -I qrun22.py j22e')];assert len(ids)==1,ids
assert not any(pp==ids[0] for p,pp,c in rows),'j22e has an active child'
os.kill(ids[0],signal.SIGTERM);print('idle j22e released for guard restart as1.005')
