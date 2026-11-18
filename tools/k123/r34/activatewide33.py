from pathlib import Path
import os,subprocess,signal,time
R=Path.home()/"scratch/squares-k123"
ps=subprocess.check_output(["ps","-axo","pid,ppid,command"],text=True)
rows=[l.strip().split(None,2) for l in ps.splitlines()[1:]]
ids=[int(a[0]) for a in rows if len(a)==3 and a[2].endswith("python -I qrun22.py j22d")]
assert len(ids)==1,ids
pid=ids[0];assert not [a for a in rows if len(a)==3 and a[1]==str(pid)],"worker has an active child"
os.kill(pid,signal.SIGTERM);time.sleep(.5)
with (R/"out/j22d.log").open("a") as f:p=subprocess.Popen(["nohup","nice","-n","5",str(Path.home()/"scratch/squares-base/venv/bin/python"),"-I","qrun22.py","j22d"],cwd=R,stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
(R/"j22d.pid").write_text(str(p.pid));print("replaced idle j22d",pid,"with",p.pid)
