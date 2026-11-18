import csv,datetime,glob,hashlib,importlib.util,json,os,pickle,shutil,sys
W='$SCRATCH/bounties-squares/take-stair-c-r24/work';S='$SCRATCH/bounties-squares';L='.';B=W+'/box'
sys.path.insert(0,L+'/tools/stair-c/r24');from prepare import fingerprint
cache={}
for root in [S+'/take-stair-c-r23/work/box/libbase',S+'/take-stair-c-r23/work/archive/s/cache23']:
 a=pickle.load(open(root+'/library.pkl','rb'));e=pickle.load(open(root+'/lens.pkl','rb'))
 for q in a['mods']:
  if q['id'] in e:cache[fingerprint(q)]=e[q['id']]
reused=0
for p in glob.glob(B+'/inbox/*.pkl'):
 a=pickle.load(open(p,'rb'))
 for q in a['mods']:
  if fingerprint(q) in cache:a['lens'][q['id']]=dict(cache[fingerprint(q)],id=q['id']);reused+=1
 pickle.dump(a,open(p,'wb'))
print('cached exact geometry tables',reused)
os.makedirs(B+'/lane',exist_ok=True)
for p in glob.glob(L+'/*.py'):shutil.copy2(p,B+'/lane/')
for name in ['prepare.py','worker.py']:shutil.copy2(L+'/tools/stair-c/r24/'+name,B+'/'+name)
for name in ['guard.py','quench22.py']:shutil.copy2(S+'/take-stair-c-r23/work/box/'+name,B+'/'+name)
shutil.copy2(S+'/take-stair-c-r23/work/box/fq',B+'/fq')
shutil.copy2(S+'/gate/cand-round23-1113a/details.csv',B+'/details.csv')
shutil.copy2(S+'/main-r17/gap-by-n.tsv',B+'/gap.tsv')
rows=[r for r in csv.DictReader(open(S+'/gather/round23-2026-11-13a.csv')) if int(r['n'])==975]
with open(B+'/control975.csv','w') as h:
 w=csv.DictWriter(h,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
open(B+'/deadline','w').write(str(datetime.datetime(2026,11,13,22,15,tzinfo=datetime.timezone.utc).timestamp()))
for tag in ['n','s']:shutil.copy2(S+'/take-stair-c-r23/work/box/py-'+tag,B+'/py-'+tag)

a=pickle.load(open(B+'/libbase/library.pkl','rb'));e=pickle.load(open(B+'/libbase/lens.pkl','rb'));l=a['layouts'][0];by={q['id']:q for q in a['mods']};mods=[by[k] for k in l['ids_slide']]
pickle.dump(dict(mods=mods,lens={q['id']:e[q['id']] for q in mods}),open(B+'/control-fixture.pkl','wb'))
