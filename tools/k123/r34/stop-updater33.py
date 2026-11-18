import subprocess,os,signal
for l in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:
 a=l.strip().split(None,1)
 if len(a)==2 and a[1].endswith('python -I update_boxE33.py'):os.kill(int(a[0]),signal.SIGTERM)
