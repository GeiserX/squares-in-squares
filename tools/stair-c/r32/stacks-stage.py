"""Stage corners whose physical model includes three following flush stacks."""
import datetime,hashlib,json,pickle,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;L=H.parents[2]
W=Path('$SCRATCH/bounties-squares/take-stair-c-r32/work');sys.path[:0]=[str(H),str(L)]
import modules as M
import expanded as E
from provenance import clean
receipt=json.load(open(W/'corner-stacks-control.json'));assert receipt['passed']
assert receipt['helper_sha256']==hashlib.sha256((H/'corner_stacks.py').read_bytes()).hexdigest()
for n,prefix in[(871,'af840f2eb936'),(997,'d894cab8829f')]:
    p=W/'donors'/f'r30-{n}-{prefix}.csv';meta=json.load(open(str(p)+'.json'));assert clean(meta['source'],meta['licence'])
    digest=hashlib.sha256(p.read_bytes()).hexdigest();assert digest.startswith(prefix)
    sq=M.np.asarray(M.read_layouts(str(p))[n],float);d,why=M.cut(sq,n);assert d is not None,why
    mods=[]
    for a,b in[(1,0),(0,1),(1,1)]:
        e=E.expand(d,a,b);assert e['s1']>=4 and e['s2']>=4
        q,_,_=E.corner(e,meta['source']+'; corner with three following stacks '+str((a,b)),meta['licence'],'r30stacks'+digest[:12]+str(a)+str(b));q.update(turn=True,ours=True,extra_stacks=3);mods.append(q)
    out=W/'donors'/f'r32-priority-stacks-{n}-{digest[:12]}.pkl'
    pickle.dump(dict(mods=mods,lens={},origin='following stacks after measured corner escape'),open(out,'wb'))
    for host in['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(out),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
    line=f'FOLLOWING STACKS n={n} variants10/01/11; source sha256 {digest}; extra_stacks=3 are actual future run bodies, preserving first4 stacks in source control. Four975 controls passed side31.714095652247682 gap>=-2.6e-12; duplicate ghost mutant rejected. Serial workers table and assemble, deadline17:15Z on November16.'
    with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA '+line+'\n')
    print(line,flush=True)
