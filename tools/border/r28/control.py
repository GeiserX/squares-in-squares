import sys,json,time,shutil
sys.path.insert(0,'.')
import border_sweep as bs
mode=sys.argv[1]
s0=bs.read_txt('control-870.start.txt')[0]
if mode=='plain':
 side,dt=bs.fq_call('./fq','control-870.start.txt','control-870.d0.txt',[],600)
 print(json.dumps(dict(mode=mode,start=s0,side=side,seconds=dt)),flush=True)
else:
 shutil.copyfile('control-870.start.txt','ctlk-870.start.txt')
 res=bs.quench_one(('ctlk-870.start.txt','./fq',600,1,0.01,1,time.time()+900))
 print(json.dumps(dict(mode=mode,start=s0,result=res)),flush=True)
