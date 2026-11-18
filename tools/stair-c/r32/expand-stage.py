"""Stage three larger corner cuts from each closest fully admitted packing."""
import datetime,hashlib,json,pickle,sys,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;L=H.parents[2];W=Path('$SCRATCH/bounties-squares/take-stair-c-r32/work');sys.path[:0]=[str(H),str(L)]
import expanded as E
import modules as M
from provenance import clean
for n in [805,812,871,997]:
    choices=[]
    for p in(W/'donors').glob(f'r30-{n}-*.csv'):
        meta=Path(str(p)+'.json')
        if not meta.exists():continue
        record=json.load(open(meta))
        if not clean(record['source'],record['licence']):continue
        sq=M.np.asarray(M.read_layouts(str(p))[n],float);d,why=M.cut(sq,n)
        if d is not None:choices.append((d['s'],p,record,d))
    if not choices:continue
    side,p,record,d=min(choices,key=lambda x:x[0]);digest=hashlib.sha256(p.read_bytes()).hexdigest();mods=[]
    for a,b in[(1,0),(0,1),(1,1)]:
        e=E.expand(d,a,b);C,_,_=E.corner(e,record['source']+'; whole-stack transfer to corner '+str((a,b)),record['licence'],'r30expand'+digest[:12]+str(a)+str(b));C['turn']=True;C['ours']=True;mods.append(C)
    out=W/'donors'/f'r32-live-expanded-{n}-{digest[:12]}.pkl'
    pickle.dump(dict(mods=mods,lens={},origin='expanded corner from pinned packing'),open(out,'wb'))
    for host in['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(out),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
    line=f'EXPAND n={n} source={p} sha256={digest} side={side:.12f}; transferred(1,0),(0,1),(1,1), turn=True. Positive975 same side31.714095652247682 and gap>=-2.6e-12; partial-stack mutant failed;3 serial workers table/rank these packets; deadline17:15Z on November16.'
    with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA '+line+'\n')
    print(line,flush=True)
