import os,subprocess,time
p='q.txt';st=os.stat(p);a=open(p).readlines()
a=[s for s in a if s.strip() and not os.path.exists('blog/'+s.split()[0]+'.lock')]
urgent=[s for s in a if s.startswith(('quench-','design-'))]
prep=[s for s in a if s.startswith('follow-')]
tail=[s for s in a if s.startswith('ranktail-')]
build=[s for s in a if s not in urgent and s not in prep and s not in tail]
# Alternate preparation and completed-row builds to avoid a perpetual feed starving builds.
new=[s for s in build if ' job libbase ' not in s];old=[s for s in build if ' job libbase ' in s]
build=[]
while new or old:
 build+=new[:2];del new[:2]
 build+=old[:1];del old[:1]
used=int(subprocess.check_output(['du','-sk','.'],text=True).split()[0])*1024
limited=used>1800*1024*1024
if limited:
 for j in range(4):
  name='design-storage-'+str(int(time.time())//120)+'-'+str(j)
  urgent.insert(0,name+' ./py -I storage23.py\n')
out=urgent[:]
while prep or build:
 out+=prep[:1];del prep[:1]
 out+=build[:2];del build[:2]
out+=tail
now=os.stat(p)
if (st.st_mtime_ns,st.st_size)==(now.st_mtime_ns,now.st_size):
 open(p+'.priority','w').writelines(out);os.replace(p+'.priority',p)
print('PRIORITY pending',len(out),'urgent',len(urgent),'tail',len(tail),'usedMB',used//1048576,'storageLimited',limited,flush=True)
