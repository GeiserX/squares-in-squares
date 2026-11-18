"""Round 27: stage the held rows that the Samanyu rule kept out (921, 415, 501) as fresh
donors, with the source record that matches their held side in any round table."""
import pickle,sys
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');L=Path('.')
B=S/'take-stair-c-r27/work/box'
sys.path[:0]=[str(L),str(L/'tools'),str(L/'tools/stair-c/r27')]
from prepare import fingerprint
from provenance import clean,held_record
import share27
import modules as M
held=M.read_layouts(str(S/'gather/round25-2026-11-14b.csv'))
lib=pickle.load(open(B/'libbase/library.pkl','rb'));seen={fingerprint(q) for q in lib['mods']}
for n in map(int,sys.argv[1:]):
    r=held_record(n)
    if r is None:print('REFUSED',n,'no clean record');continue
    src='clean held gather/round25-2026-11-14b.csv; '+r['source'];lic=r['licence']
    s=share27.share(n,M.np.asarray(held[n],float)[:,:2])
    if s>=share27.LIMIT:print('REFUSED',n,'share',s);continue
    cut,why=M.cut(M.np.asarray(held[n],float),n)
    if cut is None:print('UNREADABLE',n,why);continue
    fresh=[dict(q,ours=True) for q in M.modules_of(cut,src,lic,'r27c'+str(n)) if fingerprint(q) not in seen]
    if not fresh:print('NO NEW GEOMETRY',n);continue
    pickle.dump(dict(mods=fresh,lens={},origin='candidate'),open(B/f'inbox/a-{n}.pkl','wb'))
    print('DONOR',n,'states',len(fresh),'share',round(s,4),'source',src[:160])
