"""Stage new cut-constrained corner IDs after the physical guard control."""
import datetime,hashlib,json,pickle,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;L=H.parents[2]
W=Path('$SCRATCH/bounties-squares/take-stair-c-r30/work')
sys.path[:0]=[str(H),str(L)]
import modules as M
import expanded as E
import corner_guard as G
from provenance import clean
receipt=json.load(open(W/'corner-guard-control.json'));assert receipt['passed']
digest_helper=hashlib.sha256((H/'corner_guard.py').read_bytes()).hexdigest()
assert receipt['helper_sha256']==digest_helper
p=W/'donors/r30-997-d894cab8829f.csv';meta=json.load(open(str(p)+'.json'))
assert clean(meta['source'],meta['licence'])
digest=hashlib.sha256(p.read_bytes()).hexdigest()
assert digest=='d894cab8829f65daa0f49923960c96de1e00b4b311ae9f5b09a3215b1c977e22'
sq=M.np.asarray(M.read_layouts(str(p))[997],float);d,why=M.cut(sq,997);assert d is not None,why
mods=[]
for a,b in[(1,0),(0,1),(1,1)]:
    e=E.expand(d,a,b)
    q,_,_=E.corner(e,meta['source']+'; local cut guard '+str((a,b)),meta['licence'],'r30guard'+digest[:12]+str(a)+str(b))
    q['turn']=True;q['ours']=True;q=G.tag(q)
    assert G.valid(q,e['f'],q['P'],q['y0'],q['x0'])
    mods.append(q)
out=W/'donors'/('r30-priority-guarded-997-'+digest[:12]+'.pkl')
pickle.dump(dict(mods=mods,lens={},origin='new guard after measured corner escape'),open(out,'wb'))
for host in['boxC','boxD','boxE']:
    subprocess.run(['rsync','-a',str(out),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
line='GUARDED CORNERS n997 variants10/01/11 new IDs; helper sha256 '+digest_helper+'; source sha256 '+digest+'; control975 all four assembled and observed .995 escaped state refused. Single workers tabulate and assemble; deadline17:45Z.'
with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA '+line+'\n')
print(line,flush=True)
