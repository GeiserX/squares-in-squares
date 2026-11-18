"""Survive an agent restart, stop at the deadline, verify remote copies, then report."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
S=Path('$SCRATCH/bounties-squares');T=S/'take-harvest-r30';W=T/'work'
L=Path(__file__).resolve().parent
END=dt.datetime(2026,11,15,17,45,tzinfo=dt.timezone.utc).timestamp()

def state(message):
    with (T/'STATE.txt').open('a') as f:f.write(dt.datetime.now(dt.timezone.utc).isoformat()+' boxA '+message+'\n')

def run(cmd,timeout=120):return subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=timeout)

def copy_remote(copy):
    p=subprocess.Popen(['ssh','-n','-o','BatchMode=yes','-o','ConnectTimeout=10','boxC','tar -cf - -C scratch/squares-harvest r30'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        res=subprocess.run(['tar','-xf','-','-C',str(copy)],stdin=p.stdout,capture_output=True,timeout=180)
        p.stdout.close();err=p.communicate(timeout=30)[1]
        if res.returncode or p.returncode:raise RuntimeError(repr((res.stderr,err)))
    finally:
        if p.poll() is None:p.kill();p.wait()


def cleanup():
    for name in ['driver','worker']:
        try:
            pid=int((W/(name+'.pid')).read_text())
            cmd=run(['ps','-p',str(pid),'-o','command=']).stdout
            if '/harvest30/'+name+'.py' in cmd:
                os.killpg(pid,signal.SIGTERM);state('STOP deadline '+name+' pid='+str(pid))
        except (OSError,subprocess.SubprocessError):pass
    info=json.loads((W/'final-run-info.json').read_text()) if (W/'final-run-info.json').exists() else {}
    try:
        remote='scratch/squares-harvest/r30'
        run(['scp','-O','-q',str(W/'audit_owned_remote.py'),'boxC:'+remote+'/audit_owned_remote.py'])
        output=run(['ssh','-n','-o','BatchMode=yes','-o','ConnectTimeout=10','boxC','cd '+remote+' && /usr/bin/python3 audit_owned_remote.py']).stdout
        copy=W/'remote-final';copy.mkdir(exist_ok=True)
        copy_remote(copy)
        root=copy/'r30';manifest=json.loads((root/'file-manifest.json').read_text())
        mismatches=[name for name,sha in manifest.items() if not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha]
        if mismatches:raise ValueError('remote copy hash mismatch '+repr(mismatches))
        (W/'remote-copy-verified.json').write_text(json.dumps(dict(files=len(manifest),audit=output,sha256_manifest=manifest),indent=2)+'\n')
        run(['ssh','-n','-o','BatchMode=yes','-o','ConnectTimeout=10','boxC','rm -rf '+remote])
        info['measurements']=info.get('measurements',[])+[f'Remote cleanup verified SHA256 for {len(manifest)} files, then removed only boxC r30 scratch. Audit: '+output.strip()]
        info['processes_left']='none (deadline stopped local workers; remote audit and verified cleanup completed)'
        state(f'CLEANUP remote files={len(manifest)} all SHA256 match; boxC r30 scratch removed')
    except Exception as e:
        info['processes_left']='remote cleanup needs inspection: '+repr(e)
        info['blocked']='remote cleanup failed: '+repr(e)
        state('CLEANUP ERROR '+repr(e))
    tmp=W/'final-run-info.json.tmp';tmp.write_text(json.dumps(info,indent=2)+'\n');tmp.replace(W/'final-run-info.json')

if __name__=='__main__':
    if '--cleanup' not in sys.argv:
        while time.time()<END:time.sleep(min(30,END-time.time()))
    cleanup()
    if '--cleanup' not in sys.argv:
        state('START finalizer --wait; search stopped, report follows17:55Z')
        subprocess.run([sys.executable,'-I',str(L/'finalize.py'),'--wait'],check=True)
