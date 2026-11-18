"""Merge admitted exact module/lens pairs and version conflicting module IDs."""
from pathlib import Path
import pickle,hashlib,json,sys,copy

def merge(paths,out):
 mods={};tabs={};index={};versions=[]
 for path in paths:
  lib=pickle.load(open(path/'library.pkl','rb'));lens=pickle.load(open(path/'lens.pkl','rb'))
  for module in lib['mods']:
   name=module['id']
   if name not in lens:continue
   md=hashlib.sha256(pickle.dumps(module,protocol=5)+pickle.dumps(lens[name],protocol=5)).hexdigest()
   key=(name,md)
   if key in index:continue
   newname=name if name not in mods else name+'-v25'+md[:10]
   m=copy.deepcopy(module);t=copy.deepcopy(lens[name]);m['id']=newname;t['id']=newname
   mods[newname]=m;tabs[newname]=t;index[key]=newname
   versions.append(dict(id=name,versioned_id=newname,pair_sha256=md,library=str(path)))
 out.mkdir(parents=True,exist_ok=True);pickle.dump(dict(mods=list(mods.values()),layouts=[]),open(out/'library.pkl','wb'));pickle.dump(tabs,open(out/'lens.pkl','wb'));(out/'pairs.json').write_text(json.dumps(versions,indent=2));return versions
if __name__=='__main__':print('pairs',len(merge([Path(p) for p in sys.argv[2:]],Path(sys.argv[1]))))
