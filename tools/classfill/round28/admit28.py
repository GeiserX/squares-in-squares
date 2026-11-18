from common28 import *
note(f'START light admission driver pid{os.getpid()}, work/admit.log, deadline05:35Z. Collection now runs independently to avoid five-minute dispatch stalls.')
while time.time()<SEARCH_END and not (W/'STOP').exists():
 try:subprocess.run([sys.executable,str(W/'withdraw28.py')],timeout=20,check=True)
 except Exception as e:print('WITHDRAW_ERROR',repr(e),flush=True)
 try:subprocess.run([sys.executable,str(W/'intake28.py')],timeout=300,check=False)
 except Exception as e:print('ADMIT_ERROR',repr(e),flush=True)
 for i in range(10):
  if (W/'STOP').exists():break
  time.sleep(3)
note('FINISH admission driver')
