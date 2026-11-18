"""Deploy the round 34 stage to boxE and boxD and start the three serial worker slots."""
import sys, tarfile
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common34 import *

for host in dict(HOSTS):
    note('REMOTE_PROCESS_CHECK ' + host + ' ' + cmd(['ssh', host, 'ps -axo pid,command | grep "[s]quares-classfill" || true']).strip())
p = W / 'bundle34.tar.gz'
with tarfile.open(p, 'w:gz') as tf:
    for q in (W / 'stage').iterdir():
        tf.add(q, arcname=q.name)
for host in dict(HOSTS):
    cmd(['ssh', host, 'mkdir -p ' + ROOT])
    cmd(['scp', '-q', str(p), host + ':' + ROOT + '/bundle.tar.gz'])
    cmd(['ssh', host, 'cd ' + ROOT + ' && tar xzf bundle.tar.gz && rm bundle.tar.gz'])
writebar()
for host, slot in HOSTS:
    out = cmd(['ssh', host, 'cd ' + ROOT + ' && nohup nice -n 5 ' + PY[host] + ' -u worker34.py ' + slot +
               ' > logs/worker-' + slot + '.log 2>&1 < /dev/null & echo $!'])
    pid = int(out.strip().splitlines()[-1])
    atom(W / f'owned-{host}-{slot}.json', dict(pid=pid, host=host, slot=slot))
    note(f'START_WORKER {host} {slot} pid{pid} {ROOT}/worker34.py log {ROOT}/logs/worker-{slot}.log deadline 07:25Z')
