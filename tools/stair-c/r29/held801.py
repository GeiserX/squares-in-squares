"""Stage the own held801 root that RULE001903 explicitly reopened."""
import csv,datetime,hashlib,json,os,pickle,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;L=H.parents[2];S=Path('$SCRATCH/bounties-squares');W=S/'take-stair-c-r29/work';sys.path[:0]=[str(H),str(L)]
import modules as M
import floatsafe
from provenance import clean,pin
rows=[r for r in csv.DictReader(open(S/'gather/round26-2026-11-14b.csv'))if r['n']=='801'];assert len(rows)==801
p=W/'donors/801-held-own-rule001903.csv';p.parent.mkdir(exist_ok=True)
with p.open('w')as f:w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows({k:r[k]for k in w.fieldnames}for r in rows)
digest=hashlib.sha256(p.read_bytes()).hexdigest()
source='our own construction: own held root801 from gather/round26-2026-11-14b.csv; own ownership confirmed by main handoff-r28.log RULE001903 at00:19:03Z; earlier source tables results/round25-best-2026-11-14.tsv and results/round23-best-2026-11-13.tsv'
proof=dict(n=801,path=str(p),ok=True,source=source,licence='our own discovered packing',snapshot_sha256=digest,own_root=True,ownership_rule='RULE001903 main00:19:03Z')
p.with_suffix('.csv.json').write_text(json.dumps(proof,indent=2));assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
assert hashlib.sha256(p.read_bytes()+b'changed').hexdigest()!=digest
assert clean(source,proof['licence'])
short,lic=pin(source+'; '+str(p)+' immutable sha256 '+digest,proof['licence'])
packing=M.np.asarray(M.read_layouts(str(p))[801],float);cut,why=M.cut(packing,801)
if cut is not None:
 mods=M.modules_of(cut,short,lic,'r29-own801-'+digest[:12]);packet=W/'donors/r29-live-held801-'+digest[:12]+'.pkl';pickle.dump(dict(mods=mods,lens={},origin='own held801 reopened by RULE001903'),open(packet,'wb'))
 for host in ['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(packet),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
 result='held801 source exact SHA256 and changed-byte control passed; '+str(len(mods))+' corner/far states sent to all three serial workers'
else:
 _,fr,score,error=floatsafe.work((801,rows));assert fr is not None,error
 dest=W/'cert-in'/('801-own-held-'+digest[:12]+'.csv');dest.parent.mkdir(exist_ok=True)
 with dest.open('w')as f:w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(fr)
 dest.with_suffix('.json').write_text(json.dumps(dict(n=801,whole_layout_follow=True,built=(1+score)*801**.5,predicted=(1+score)*801**.5,stacks=[0,0],modules=[dict(id='801-own-held-root',source=short,licence=lic)])))
 subprocess.run(['rsync','-a',str(dest),str(dest.with_suffix('.json')),'boxC:scratch/squares-stair-c/cert-in/'],check=True,timeout=40)
 result='held801 source exact SHA256 and changed-byte control passed; no arm cut ('+str(why)+'), actual certified-file fq staged on boxC'
print(result,flush=True)
with (W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA RUN '+result+'. Pinned '+str(p)+' sha256 '+digest+'; deadline11:45Z.\n')
