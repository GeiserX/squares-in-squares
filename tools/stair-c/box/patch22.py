import os,pickle,sys,fcntl
sys.path.insert(0,'.')
from cache23 import load,save,merge
name=sys.argv[1];a=pickle.load(open('patches/'+name+'.pkl','rb'))
if os.path.exists('cache23/READY'):
 with open('cache23/LOCK','a') as h:
  fcntl.flock(h,fcntl.LOCK_EX);L,E=load('cache23');ids=merge(L,E,a);save('cache23',L,E)
else:L,E=load('libbase');ids=merge(L,E,a)
out='lib-'+name;save(out,L,E);open(out+'/need.txt','w').write('\n'.join(sorted(ids))+'\n')
print('imported',name,len(ids),'fresh states among',len(L['mods']),'cumulative modules',flush=True)
