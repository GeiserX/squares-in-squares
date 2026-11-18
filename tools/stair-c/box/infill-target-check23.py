import csv,sys
sys.path.insert(0,'lane');import modules as M
pool='lib-zip51f0.7558';need=set(open(pool+'/need.txt').read().split());lib=M.Library(pool,only=M.usable)
held=next(float(r['L']) for r in csv.DictReader(open('details.csv')) if r['n']=='978')
rows=lib.best(978,top=2,below=1.,need=need,depth=.3)
for f,stop,C,F1,F2,s1,s2 in rows:print('TARGET',31+f,'bar',held,'margin',31+f-held,'stop',stop,'ids',C['id'],F1['id'],F2['id'],'stacks',s1,s2,flush=True)
if rows:
 f,stop,C,F1,F2,s1,s2=rows[0]
 if 31+f-held<.014:
  name='978-zip51-currentf-probe'
  with open('q.txt','a') as h:h.write(f'{name} ./py -I lane/modules.py job {pool} raw-a details-r21.csv {name} 978 {C["id"]} {F1["id"]} {F2["id"]} {s1} {s2} {f!r} --fq ./fq --squeeze family\n')
  print('PROBE queued, exact full assembly required',flush=True)
