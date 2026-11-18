"""Free two complete stacks while modeling three following stacks explicitly."""
import datetime,hashlib,json,pickle,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H.parents[2])]
import modules as M
import expanded as E
from provenance import clean
W=Path('$SCRATCH/bounties-squares/take-stair-c-r32/work')
receipt=json.load(open(W/'two-stacks-control.json'));assert receipt['passed']
assert receipt['helper_sha256']==hashlib.sha256((H/'corner_stacks.py').read_bytes()).hexdigest()
results=[]
for n,prefix in[(805,'2a93eff46ae9'),(812,'3cae09abbddd'),(871,'af840f2eb936'),(997,'d894cab8829f')]:
    p=W/'donors'/f'r30-{n}-{prefix}.csv';meta=json.load(open(str(p)+'.json'));assert clean(meta['source'],meta['licence'])
    digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest.startswith(prefix)
    sq=M.np.asarray(M.read_layouts(str(p))[n],float);d,why=M.cut(sq,n);assert d is not None,why
    mods=[];failed=[]
    for a,b in[(2,0),(0,2),(2,2)]:
        try:
            e=E.expand(d,a,b);assert e['s1']>=4 and e['s2']>=4
            q,_,_=E.corner(e,meta['source']+'; two-stack corner transfer '+str((a,b)),meta['licence'],'r30stacks2'+digest[:12]+str(a)+str(b));q.update(turn=True,ours=True,extra_stacks=3);mods.append(q)
        except (AssertionError,ValueError)as ex:failed.append(dict(variant=[a,b],reason=str(ex)))
    item=dict(n=n,sha256=digest,staged=[q['id']for q in mods],failed=failed);results.append(item)
    if mods:
        raw=pickle.dumps(dict(mods=mods,lens={},origin='two complete stacks freed after one-stack loss floors'));out=W/'donors'/f'r32-priority-stacks-two-{n}-{digest[:12]}.pkl';out.write_bytes(raw)
        for host in['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(out),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
    print('TWO STACKS STAGE',json.dumps(item),flush=True)
    with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA TWO STACKS '+json.dumps(item)+'; variants20/02/22 move more free squares after one-stack measured floors. Three975 source controls and incomplete-stack mutant passed first. Serial workers, deadline17:15Z on November16.\n')
(W/'two-stacks-stage.json').write_text(json.dumps(results,indent=2))
