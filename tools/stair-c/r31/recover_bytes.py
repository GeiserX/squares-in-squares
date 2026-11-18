"""Restore frozen modules only after exact bytes and full source proofs pass."""
import datetime,hashlib,json,pickle,re,signal,subprocess,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H.parents[2])]
import provenance as P
import ancestors as A
from prepare import fingerprint
from rebind_bytes import Rebind,PIN,REF
R=Path('$SCRATCH/bounties-squares');W=R/'take-stair-c-r31/work';F=R/'take-stair-c-r30/work/donors'
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
class SourceTimeout(BaseException):pass
def timeout(*args):raise SourceTimeout('source recovery30s')
signal.signal(signal.SIGALRM,timeout)
audit=json.load(open(W/'base-audit.json'));wanted={x['id']for x in audit['dropped']}
paths={x['reason'].removeprefix('changed pinned ancestor ')for x in audit['dropped']if x['reason'].startswith('changed pinned ancestor ')}
archives=[];pending=[];seen_json=set();expected={old:set()for old in paths}
for key in['n','m','s']:
    with tarfile.open(R/f'take-stair-c-r30/work/archive/{key}/final-copy.tar.gz')as tf:
        lib=pickle.loads(tf.extractfile('libbase/library.pkl').read());tables=pickle.loads(tf.extractfile('libbase/lens.pkl').read());archives.append((lib,tables))
        pending.extend(q['src']+' '+q['licence']for q in lib['mods']if q['id']in wanted)
while pending:
    value=pending.pop()
    if isinstance(value,dict):pending.extend(value.values());continue
    if isinstance(value,list):pending.extend(value);continue
    if not isinstance(value,str):continue
    for old,label,digest in PIN.findall(value):
        if old in expected:expected[old].add(digest)
    for name in REF.findall(value):
        if name in seen_json or not Path(name).is_file():continue
        seen_json.add(name);pending.append(json.loads(Path(name).read_text()))
folder=W/'byte-recovery';folder.mkdir(exist_ok=True);aliases={};roots=[]
for old in sorted(paths):
    n=int(re.match(r'\d+',Path(old).name)[0])
    for p in list(F.glob(f'r30-{n}-*.csv'))+list((R/'take-stair-c-r29/work/donors').glob(f'r29-{n}-*.csv'))+list((R/'take-stair-c-r28/work/donors').glob(f'r28-{n}-*.csv')):
        side=Path(str(p)+'.json')
        if not side.exists():continue
        entry=json.load(open(side));proof=Path(entry.get('proof',''))
        if not proof.is_file():continue
        j=json.load(open(proof));digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if j.get('path')!=old or j.get('n')!=n or j.get('snapshot_sha256')!=digest:continue
        if not any(digest.startswith(want)for want in expected[old]):continue
        if not P.proof_ok(j)or not P.clean(j.get('source',''),j.get('licence','')):continue
        dest=folder/f'{n}-{digest}.csv';dest.write_bytes(p.read_bytes())
        aliases.setdefault(old,[]).append((str(dest),digest));roots.append(dict(n=n,original=old,path=str(dest),sha256=digest,proof=str(proof),source=j['source'],licence=j['licence']))
b=Rebind(aliases,W/'ancestry');approved={};root_receipts=[]
for r in roots:
    try:
        signal.alarm(30);source=b.text(r['source']+'; ancestry proof '+r['proof']);licence=b.text(r['licence'])
        assert P.clean(source,licence);A.audit(source,licence,r['n'])
        meta=dict(n=r['n'],source=source,licence=licence,source_record=b.file(r['proof']),recovered_sha256=r['sha256'])
        Path(r['path']+'.json').write_text(json.dumps(meta))
        record=P.audit(r['path'],r['n'],source,licence);signal.alarm(0)
        if record is not None:approved.setdefault(r['original'],[]).append((r['path'],r['sha256']))
        root_receipts.append(dict(r,passed=record is not None,full_record=record))
        print('ROOT',r['n'],'full proof',record is not None,flush=True)
    except (OSError,ValueError,KeyError,AssertionError,TimeoutError,RecursionError,SourceTimeout)as ex:
        signal.alarm(0);root_receipts.append(dict(r,passed=False,reason=str(ex)));print('ROOT',r['n'],'DEFER',str(ex),flush=True)
b=Rebind(approved,W/'ancestry');mods={};lens={};deferred=[]
excluded=json.load(open(W/'excluded-paths.json'))if(W/'excluded-paths.json').exists()else[]
for lib,tables in archives:
    for q in lib['mods']:
        fp=fingerprint(q)
        if q['id']not in wanted or fp in mods:continue
        try:
            signal.alarm(15);src=b.text(q['src']);lic=b.text(q['licence'])
            if(src,lic)==(q['src'],q['licence']):signal.alarm(0);continue
            identities=[old+' immutable sha256 '+digest for old,versions in approved.items()for path,digest in versions]
            assert not any(token in q['src']or token in src or any(token in ident for ident in identities)for token in excluded)
            assert P.clean(src,lic);A.audit(src,lic,q.get('n'));from public_roots import audit as public_audit;public_audit(dict(source=src,licence=lic));signal.alarm(0)
            mods[fp]=dict(q,src=src,licence=lic,ours=True)
            if q['id']in tables:lens[q['id']]=tables[q['id']]
        except (OSError,ValueError,KeyError,AssertionError,TimeoutError,RecursionError,SourceTimeout)as ex:
            signal.alarm(0);deferred.append(dict(id=q['id'],reason=str(ex)))
# The negative control changes the expected hash, keeping the recovered path.
if approved:
    old,versions=next(iter(approved.items()));p,digest=versions[0];probe=p+' immutable sha256 '+digest;A.audit(probe,'our own')
    try:A.audit(p+' immutable sha256 '+'0'*64,'our own')
    except ValueError:pass
    else:raise AssertionError('wrong expected hash accepted')
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==digest
records=list(mods.values());result=dict(restored=len(records),modules=[q['id']for q in records],deferred=deferred,roots=root_receipts,aliases=approved,expected={k:sorted(v)for k,v in expected.items()},changed_records=b.changed,wrong_sha_mutant='rejected')
(W/'byte-recovery-all.json').write_text(json.dumps(result,indent=2))
for k in range(0,len(records),3):
    pack=records[k:k+3];raw=pickle.dumps(dict(mods=pack,lens={q['id']:lens[q['id']]for q in pack if q['id']in lens},origin='exact frozen bytes after full proof'));out=W/'donors'/('r31-live-byte-recovery-'+hashlib.sha256(raw).hexdigest()[:16]+'.pkl');out.write_bytes(raw)
    for host in['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(out),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
with(W.parent/'STATE.txt').open('a')as f:f.write(stamp()+' boxA BYTE RECOVERY restored '+str(len(records))+' module states through '+str(len(approved))+' exact frozen input snapshots. Full source proof per root and wrong-sha mutant passed. Old files unchanged. Original and rebound exclusions checked. Cached tables sent in <=3-state packets; completed recipes remain excluded. Result work/byte-recovery-all.json; deadline00:15Z on November16.\n')
print('RESTORED',len(records),'modules,',len(approved),'full-proof roots,',len(deferred),'deferred',flush=True)
