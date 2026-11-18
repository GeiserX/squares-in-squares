from common29 import *
from ancestor_share29 import inspect
bad=set(read(W/'prohibited-tags.json',[]));found=[]
for p in (W/'jobs').glob('*.json'):
 j=read(p,{});tag=j.get('tag','')
 if not tag.startswith('x') or 'control' in tag:continue
 proof=next((W/'ancestry').glob(tag[1:13]+'*.json'),None)
 if proof is None:proof=read(W/'audited'/f'{tag}.json',{}).get('input_proof')
 if not proof:continue
 r=inspect(proof)
 if r['excluded'] or r['errors']:
  bad.add(tag);found.append(dict(tag=tag,source=j.get('source'),check=r))
atomic(W/'prohibited-tags.json',sorted(bad));atomic(W/'public-root-job-review.json',found)
for host in ['boxE','boxD']:
 cmd(['scp','-q',str(W/'cancel_prohibited29.py'),str(W/'prohibited-tags.json'),host+':'+REMOTE+'/'])
 interpreter='$SCRATCH/squares-base/venv/bin/python' if host=='boxE' else '$SCRATCH/squares-readers/venv/bin/python'
 result=cmd(['ssh',host,'cd '+REMOTE+' && '+interpreter+' -I cancel_prohibited29.py'])
 note('CANCEL_PUBLIC_ROOT '+host+' '+result.strip())
note(f'PUBLIC_ROOT_RECHECK {len(found)} rejected jobs across {len(list((W/"jobs").glob("*.json")))} job records; own geometry never share-tested. Completed dry work remains measured separately.')
print('REJECTED',len(found),flush=True)
