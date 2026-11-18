"""Deploy the round 38 stage to boxE, boxC and boxB and run the worker controls once per host.
Workers start on demand from the controller (6h). On boxB the stage lives on $DATA; $SCRATCH/squares-classfill-r38
is a symlink to it so ROOT is the same relative path on every host."""
import sys, tarfile
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common38 import *

for host in dict(HOSTS):
    note('REMOTE_PROCESS_CHECK ' + host + ' ' + cmd(['ssh', host, 'ps -axo pid,command | grep "[s]quares-classfill" || true']).strip())
p = W / 'bundle38.tar.gz'
with tarfile.open(p, 'w:gz') as tf:
    for q in (W / 'stage').iterdir():
        tf.add(q, arcname=q.name)
for host in dict(HOSTS):
    if host == 'boxB':
        cmd(['ssh', host, 'mkdir -p $SCRATCH/squares-classfill-r38 $SCRATCH && ln -sfn $SCRATCH/squares-classfill-r38 ~/' + ROOT])
    cmd(['ssh', host, 'mkdir -p ' + ROOT])
    cmd(['scp', '-q', str(p), host + ':' + ROOT + '/bundle.tar.gz'])
    cmd(['ssh', host, 'cd ' + ROOT + ' && tar xzf bundle.tar.gz && rm bundle.tar.gz && mkdir -p ' + ' '.join('queue/' + s for h, s in HOSTS if h == host)])
writebar()
for host in dict(HOSTS):
    out = cmd(['ssh', host, 'cd ' + ROOT + ' && export OMP_NUM_THREADS=1 && ' + PY[host] + ' -I control24.py 2>&1 | tail -2; ' + PY[host] + ' -I finecontrol29.py 2>&1 | tail -2; '
               + PY[host] + ' -I loopcontrol33.py 2>&1 | tail -3'], timeout=300)
    note('CONTROLS ' + host + ' ' + ' | '.join(l.strip() for l in out.splitlines())[:600])
