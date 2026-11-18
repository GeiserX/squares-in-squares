from common29 import *
import signal
class WalkTimeout(BaseException):pass
def timed(a,b):raise WalkTimeout()
signal.signal(signal.SIGALRM,timed)
import quench_walk as qw
for label,p in [('valid793',S/'take-classfill-r28/793.csv'),('excluded747',S/'take-soft-r29/work/starts/747-xfor.csv')]:
 start=time.time();signal.alarm(60)
 try:r=qw.check(str(p))
 except WalkTimeout:r=dict(clean=False,hits=['control walk timeout60s'])
 finally:signal.alarm(0)
 atomic(W/f'walker-control-{label}.json',r);print(label,time.time()-start,r.get('clean'),r.get('files'),r.get('hits',[])[:8],r.get('gone',[])[:4],flush=True)
