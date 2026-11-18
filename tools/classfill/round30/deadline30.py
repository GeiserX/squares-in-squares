from common29 import *
note(f"START deadline loader30 pid{os.getpid()}; adopt disk finisher17:40Z, numerical cutoff17:45Z")
while time.time()<END-300:time.sleep(min(15,END-300-time.time()))
os.execv(sys.executable,[sys.executable,"-u",str(W/"end30.py")])
