"""Recover completed round 23 recipes as exclusions, never as donor layouts."""
import glob,json,os,pickle,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from prepare import fingerprint
S='$SCRATCH/bounties-squares';W=S+'/take-stair-c-r24/work';OLD=S+'/take-stair-c-r23/work'
by={}
for root in [OLD+'/box/libbase',OLD+'/archive/n/cache23',OLD+'/archive/s/cache23']:
    if not os.path.exists(root+'/library.pkl'):continue
    for q in pickle.load(open(root+'/library.pkl','rb'))['mods']:
        by.setdefault(q['id'],[]).append(q)
recipes=set();missing=0;count=0
for p in glob.glob(OLD+'/archive/*/raw-a/*.json')+glob.glob(OLD+'/box/hist/*.json'):
    j=json.load(open(p))
    if j.get('built') is None:continue
    mods=[]
    for parent in j.get('modules',[]):
        matches=[q for q in by.get(parent['id'],[]) if q['src']==parent['source']]
        if not matches or len({fingerprint(q) for q in matches})!=1:break
        mods.append(matches[0])
    if len(mods)!=3:missing+=1;continue
    recipe=(j['n'],*[fingerprint(q) for q in mods],*j['stacks'])
    recipes.add(recipe);count+=1
assert recipes and count>10
out=W+'/prior-recipes.pkl';pickle.dump(recipes,open(out,'wb'))
json.dump(dict(records_matched=count,unique_recipes=len(recipes),records_unresolved=missing),open(W+'/history-control.json','w'),indent=2)
print('CONTROL prior recipe ledger recovered',count,'records and',len(recipes),'unique completed recipes; unresolved',missing,'not used',flush=True)
