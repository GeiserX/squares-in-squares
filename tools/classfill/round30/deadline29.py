"""Load the latest finisher from disk shortly before the common cutoff."""
from common29 import *
note(f'START disk-backed finisher loader pid{os.getpid()}, command deadline29.py, log work/end29.log, load11:40Z cleanup17:45Z take11:55Z')
while time.time()<END-300:time.sleep(min(15,END-300-time.time()))
note('ADOPT latest end29.py from disk at11:40Z; no numerical restart')
os.execv(sys.executable,[sys.executable,'-u',str(W/'end29.py')])
