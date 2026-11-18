"""Review immutable public terminal rows before numerical admission."""
from common29 import *
import io,zipfile
from light29 import key,load
from prvsim29 import check
OWN={'Samanyu-dev/squares_in_squares','franciscouzo/square-packing'}
def review_ref(ref,n,preferred=()):
 tag=hashlib.sha256((ref+':'+str(n)+':member-v3:'+json.dumps(sorted(preferred))).encode()).hexdigest();cache=W/'public-root-cache'/(tag+'.json')
 old=read(cache,{})
 if old:return old
 folders=set(S.glob('harvest*/nb/'+ref.replace('/','__')))|set(S.glob('harvest*/ds/'+ref.replace('/','__')))
 folders|=set(S.glob('take-harvest-r*/work/public*/data/nb/'+ref.replace('/','__')))|set(S.glob('take-harvest-r*/work/public*/data/ds/'+ref.replace('/','__')))
 if preferred:folders={Path(q).parent for q in preferred}
 found=[];pins=[];errors=[];archive_hashes=set()
 for folder in sorted(folders):
  notice=folder/'meta.json'
  for archive in list(folder.glob('submission.csv'))+list(folder.glob('data.zip')):
   if preferred and str(archive) not in preferred:continue
   digest=hashlib.sha256(archive.read_bytes()).hexdigest()
   if digest in archive_hashes:continue
   archive_hashes.add(digest)
   z=None;stream=None
   try:
    if archive.suffix=='.zip':
     z=zipfile.ZipFile(archive)
     member={'kmmmvs/squares-in-squares-private-packings':'local_bank.csv','busyaprime/squares-in-squares-fq-quenched-packings':'packings.csv'}.get(ref,'submission.csv')
     if member not in z.namelist():continue
     stream=io.TextIOWrapper(z.open(member),encoding='utf-8-sig')
    else:stream=archive.open(encoding='utf-8-sig')
    reader=csv.DictReader(stream)
    if not {'x','y','angle'}<=set(reader.fieldnames or []):continue
    selected=[]
    for r in reader:
     k=int(r['n']) if 'n' in r else int(r['id'].split('_')[0])
     if k==n:selected.append(dict(n=str(n),square_id=str(len(selected)),x=r['x'].lstrip('s'),y=r['y'].lstrip('s'),angle=r['angle'].lstrip('s')))
    if len(selected)!=n:continue
    dest=W/'public-root-rows'/f'{tag}-{digest[:12]}.csv';dest.parent.mkdir(exist_ok=True)
    with dest.open('w',newline='') as h:wr=csv.DictWriter(h,fieldnames=CSV);wr.writeheader();wr.writerows(selected)
    rowpin=blob(dest);ap=blob(archive);pins.extend([rowpin,ap])
    if notice.is_file():pins.append(blob(notice))
    geom=key(load(dest,{n})[n],10);measure=check(dest,n)
    found.append(dict(n=n,share=measure['share'],geometry=geom,member=(member if archive.suffix=='.zip' else archive.name),row=rowpin,archive=ap,notice=blob(notice) if notice.is_file() else None))
   except (ValueError,KeyError,OSError,zipfile.BadZipFile) as e:errors.append(repr(e))
   finally:
    if stream:stream.close()
    if z:z.close()
 result=dict(ref=ref,n=n,variants=found,pins=pins,errors=errors,complete=bool(found) and len({q['geometry'] for q in found})==1,excluded=bool(found) and all(q['share']>=.4 for q in found),time=now())
 # Multiple historical variants cannot be bound from a bare ref alone.
 atomic(cache,result);return result

def pinned_root(a,ref,n,ancestor):
 pins=a.get('snapshots',[])+a.get('expanded',{}).get('history',{}).get('snapshots',[])
 pinmap={q['path']:q for q in pins};variants=[];outpins=[]
 for q in pins:
  if not q['path'].endswith('.csv.json'):continue
  meta=read(q['snapshot'],{});src=meta.get('source','') if isinstance(meta,dict) else ''
  if not isinstance(src,str) or meta.get('public_first') is False:continue
  m=re.match(r'\s*(?:public\s+)?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\s*::',src)
  if not m or m[1]!=ref:continue
  original=q['path'][:-5]
  for check in ancestor['checks']:
   if check['n']!=n or check.get('original')!=original:continue
   row=dict(path=original,snapshot=check['snapshot'],sha256=check['sha256'])
   if meta.get('input_sha256') and meta['input_sha256']!=row['sha256']:continue
   variants.append(dict(n=n,share=check['share'],row=row,notice=q,kind='pinned public-first row'))
   outpins.extend([row,q])
 if not variants:return None
 return dict(ref=ref,n=n,complete=True,excluded=any(v['share']>=.4 for v in variants),variants=variants,pins=outpins,errors=[],binding='exact public-first packing and its source sidecar',time=now())

def review(closure):
 a=read(closure,{});sha=hashlib.sha256(Path(closure).read_bytes()).hexdigest();path=W/'public-root-reviews'/(sha+'.json');old=read(path,{})
 if old and old.get('policy')=='pinned-root-v4':return old
 h=a.get('expanded',{}).get('history',{});refs=sorted({(r,int(n)) for r,n in h.get('public',[]) if r not in OWN});roots=[];pins=[]
 from ancestor_share29 import inspect
 ancestor=inspect(closure)
 for ref,n in refs:
  tag=ref.replace('/','__');texts=[a.get('source','')]+h.get('parts',[])
  preferred=sorted({m for text in texts for m in re.findall(r'$DATA/[^\s<>\";,()]+/(?:submission\.csv|data\.zip)',text) if '/'+tag+'/' in m and Path(m).is_file()})
  root=pinned_root(a,ref,n,ancestor) or review_ref(ref,n,preferred);roots.append(root);pins+=root['pins']
  if root['excluded']:break
 result=dict(policy='pinned-root-v4',source_proof_sha256=sha,public_refs=refs,roots=roots,pins=pins,complete=not ancestor['errors'] and not ancestor['excluded'] and all(r['complete'] and not r['excluded'] for r in roots),excluded=bool(ancestor['excluded']) or any(r['excluded'] for r in roots),ancestor=ancestor,time=now())
 atomic(path,result);return result

if __name__=='__main__':
 for closure in sys.argv[1:]:
  result=review(closure);print(json.dumps(dict(proof=closure,complete=result['complete'],excluded=result['excluded'],roots=[(r['ref'],r['n'],len(r['variants']),r['excluded']) for r in result['roots']])),flush=True)
