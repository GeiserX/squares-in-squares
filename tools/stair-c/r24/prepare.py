"""Prepare a conservative clean library and fresh candidate donors for round 24."""
import csv,hashlib,json,os,pickle,re,shutil,sys
import numpy as np
ROOT='$SCRATCH/bounties-squares'
LANE='.'
WORK=ROOT+'/take-stair-c-r24/work'
sys.path.insert(0,LANE)
import modules as M

def fingerprint(q):
    def norm(x):
        if isinstance(x,np.ndarray):return ('array',x.shape,str(x.dtype),np.round(x,11).tolist())
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,dict):return {k:norm(v) for k,v in sorted(x.items())}
        if isinstance(x,(list,tuple)):return [norm(v) for v in x]
        return x
    skip={'id','src','licence','tag','n','m','k','ours','sig','loss0','tilt0'}
    return hashlib.sha256(json.dumps(norm({k:v for k,v in q.items() if k not in skip}),sort_keys=True).encode()).hexdigest()

def main():
    box=WORK+'/box';os.makedirs(box+'/libbase',exist_ok=True);os.makedirs(box+'/inbox',exist_ok=True)
    old=ROOT+'/take-stair-c-r23/work/box/libbase'
    a=pickle.load(open(old+'/library.pkl','rb'));e=pickle.load(open(old+'/lens.pkl','rb'))
    # Keep only independent procedural designs and public roots with explicit ancestry.
    banned=re.compile(r'(?<!\d)(639|691|745|801|858|918|980|981)(?!\d)|verified-best-of-1105|penguin069/squares-joegun|areebbb')
    keep=[];rejected=[]
    for q in a['mods']:
        src=q['src'];text=src+' '+q['id']+' '+q['licence']
        if banned.search(text) or q['n'] in {639,691,745,801,858,918,980,981}:
            rejected.append(q['id']);continue
        # All inherited metadata remains attached. Generic seed ancestry stays out.
        if 'seed merged0' in text or 'see README' in text:continue
        q=dict(q,ours=True);keep.append(q)
    ids={q['id'] for q in keep};layouts=[l for l in a['layouts'] if set(l.get('ids_slide',[]))<=ids]
    # The independent 975/974 control uses three procedural modules already in keep.
    control=next(l for l in a['layouts'] if l['n']==975 and l['tag']=='tw17')
    by={q['id']:q for q in a['mods']}
    for k in control['ids_slide']:
        if k not in ids:
            q=dict(by[k],ours=True)
            assert not banned.search(q['src']+' '+q['licence'])
            keep.append(q);ids.add(k)
    layouts=[control]
    pickle.dump(dict(mods=keep,layouts=layouts),open(box+'/libbase/library.pkl','wb'))
    pickle.dump({k:v for k,v in e.items() if k in ids},open(box+'/libbase/lens.pkl','wb'))
    json.dump(dict(kept=len(keep),rejected_banned=len(rejected),rejected_ids=rejected),open(WORK+'/base-audit.json','w'),indent=2)
    srcs={int(r['n']):r for r in csv.DictReader(open(LANE+'/results/round23-best-2026-11-13.tsv'),delimiter='\t')}
    candidate=M.read_layouts(ROOT+'/gather/round23-2026-11-13a.csv')
    # Candidate changed rows first. Each is an explicitly clean donor in the brief.
    counts=sorted(srcs)+sorted(set(candidate)-set(srcs))
    seen={fingerprint(q) for q in keep};rows=[]
    for n in counts:
        if n<100:continue
        d,why=M.cut(np.asarray(candidate[n],float),n)
        if d is None:continue
        r=srcs.get(n,{})
        src='round23 candidate gather/round23-2026-11-13a.csv n='+str(n)+'; results/round23-best-2026-11-13.tsv; '+r.get('source','accepted held ancestry in prior round results tables')
        lic=r.get('licence','accepted held packing; source and licence in prior round results tables')
        tag='r24c'+str(n);mods=M.modules_of(d,src,lic,tag)
        fresh=[]
        for q in mods:
            fp=fingerprint(q)
            if fp in seen:continue
            seen.add(fp);fresh.append(dict(q,ours=True))
        if not fresh:continue
        patch=dict(mods=fresh,lens={},origin='candidate',n=n)
        name=('a' if n in srcs else 'b')+'-'+str(n)
        pickle.dump(patch,open(box+'/inbox/'+name+'.pkl','wb'));rows.append(dict(n=n,modules=len(fresh),changed=n in srcs))
    json.dump(rows,open(WORK+'/candidate-donors.json','w'),indent=2)
    print('PREP clean base',len(keep),'banned exclusions',len(rejected),'candidate readable patches',len(rows),'changed',sum(r['changed'] for r in rows),flush=True)
if __name__=='__main__':main()
