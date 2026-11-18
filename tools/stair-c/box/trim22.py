import glob,os,pickle,sys
for d in sys.argv[1:]:
 if not os.path.exists(d+'/need.txt'):continue
 ids=set(open(d+'/need.txt').read().split());p=d+'/library.pkl';t=d+'/lens.pkl'
 L=pickle.load(open(p,'rb'));E=pickle.load(open(t,'rb'));by={q['id']:q for q in L['mods']};new=[by[k] for k in ids if k in by]
 if any(q['kind']!='corner' for q in new):
  # A patch with a new far zone still needs the old corners that can use it.
  cs={q['c'] for q in new if q['kind']=='far'}
  keep=[q for q in L['mods'] if q['kind']=='far' or q['id'] in ids or (q['kind']=='corner' and (q['c1'] in cs or q['c2'] in cs))]
 else:
  cs={q[c] for q in new for c in ('c1','c2')}
  keep=[q for q in L['mods'] if q['id'] in ids or (q['kind']=='far' and q['c'] in cs)]
 have={q['id'] for q in keep};L['mods']=keep;L['layouts']=[];E={k:v for k,v in E.items() if k in have}
 pickle.dump(L,open(p+'.tmp','wb'));os.replace(p+'.tmp',p)
 pickle.dump(E,open(t+'.tmp','wb'));os.replace(t+'.tmp',t)
 print(d,'trimmed',len(by),'to',len(keep),flush=True)
