import fcntl,glob,os,pickle,sys
sys.path.insert(0,'lane')

def merge(L,E,a):
 ids={q['id'] for q in a['mods'] if q['id'] in a['lens']};D={q['id']:q for q in L['mods']}
 for q in a['mods']:
  if q['id'] in ids:D[q['id']]=dict(q,ours=True)
 L['mods']=list(D.values());E.update({k:v for k,v in a['lens'].items() if k in ids});return ids

def load(root):return pickle.load(open(root+'/library.pkl','rb')),pickle.load(open(root+'/lens.pkl','rb'))
def save(root,L,E):
 os.makedirs(root,exist_ok=True)
 for name,data in [('library',L),('lens',E)]:
  p=root+'/'+name+'.pkl';pickle.dump(data,open(p+'.tmp','wb'));os.replace(p+'.tmp',p)

if __name__=='__main__':
 os.makedirs('cache23',exist_ok=True)
 with open('cache23/LOCK','a') as h:
  fcntl.flock(h,fcntl.LOCK_EX);L,E=load('libbase');ids=set()
  for p in sorted(glob.glob('patches/*.pkl')):ids.update(merge(L,E,pickle.load(open(p,'rb'))))
  save('cache23',L,E)
  assert ids<={q['id'] for q in L['mods']} and ids<=set(E)
  import importlib.util
  spec=importlib.util.spec_from_file_location('border_control','lane/stair-c_border.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);B.control('cache23')
  open('cache23/READY','w').write(str(len(ids)))
  print('CONTROL cumulative cache retained',len(ids),'patch states and their tables;',len(L['mods']),'total modules; square975 and bordered974 controls passed',flush=True)
