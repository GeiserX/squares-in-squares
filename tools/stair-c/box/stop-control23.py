import json,pathlib,subprocess,sys,time
root=pathlib.Path('cleanup-control').resolve();root.mkdir(exist_ok=True)
child=subprocess.Popen(['/bin/sleep','30'],cwd=root)
try:
 helper=str(pathlib.Path('stop23.py').resolve())
 audit=subprocess.run([sys.executable,'-I',helper,'--root',str(root)],cwd=pathlib.Path.home(),capture_output=True,text=True,check=True)
 assert child.pid in json.loads(audit.stdout)['before']
 stopped=subprocess.run([sys.executable,'-I',helper,'--root',str(root),'--kill'],cwd=pathlib.Path.home(),capture_output=True,text=True,check=True)
 result=json.loads(stopped.stdout);child.wait(timeout=3)
 assert child.pid in result['signalled'] and not result['left'] and child.returncode<0
 print('CONTROL cleanup detected and stopped only the fixture child; parent search directory remains active',flush=True)
finally:
 if child.poll() is None:child.kill();child.wait()
