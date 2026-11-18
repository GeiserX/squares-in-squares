# r35 positive control of the worker.py loop: the same loop code on control-870 (plain default fq ends 30.91388209074235)
import sys,time,json,os
sys.path.insert(0,'.')
import border_sweep as bs
inp='control-870.start.txt';out='control-870.loop.txt';END=time.time()+1500
cur=inp;s_cur=bs.read_txt(cur)[0];best=(s_cur,cur);steps=[];k=0;t0=time.time()
for rnd in range(3):
 imp=False
 for fl in ([],list(bs.POLISH)):
  k+=1;o=out+f'.l{k}';s2,_=bs.fq_call('./fq',cur,o,fl,600);steps.append((len(fl)>0,s2))
  if s2 is not None and s2<best[0]:best=(s2,o)
  if s2 is not None and s2<s_cur-3e-9:cur,s_cur,imp=o,s2,True
 if not imp or time.time()>END-60:break
print(json.dumps(dict(start=bs.read_txt(inp)[0],end=best[0],steps=steps,seconds=time.time()-t0)),flush=True)
