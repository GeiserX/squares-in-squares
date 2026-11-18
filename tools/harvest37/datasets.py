"""Read changed, explicitly licensed public dataset archives as data only."""
import hashlib
import json
from pathlib import Path
import urllib.parse
import zipfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch import H
import rpc
from angle_take import accepted


def fetch(data,cache):
    refs={};changed=[]
    for query in ['squares in squares','square packing','squares-in-squares']:
        try:
            for item in rpc.get(H.API+'/datasets/list?search='+urllib.parse.quote(query)+'&page=1'):
                ref=item.get('ref','')
                if any(word in ref.lower() for word in ['square','packing','sis-']):refs[ref]=item
        except Exception as e:print('DATASET list error',type(e).__name__,flush=True)
    versions=cache.setdefault('_datasets',{})
    for ref,item in sorted(refs.items()):
        licence=item.get('licenseName','');updated=item.get('lastUpdated','')
        if not accepted(licence) or ref=='prvsiyan/squares-verified-best-of-1105':continue
        if str(updated)<'2026-11-14' or versions.get(ref)==updated:continue
        if int(item.get('totalBytes',0))>100_000_000:continue
        root=Path(data)/'ds'/ref.replace('/','__');root.mkdir(parents=True,exist_ok=True)
        try:
            archive=root/'data.zip';rpc.download_dataset(ref,archive)
            got=[]
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    name=Path(info.filename).name
                    if name not in ['submission.csv','best.csv','best_current.csv','submission_merged.csv','per_n.csv','per_n_source_table.csv','submission_sources.csv','sources.csv']:continue
                    if info.file_size>100_000_000:continue
                    out=root/name;out.write_bytes(z.read(info))
                    got.append(dict(file=info.filename,bytes=info.file_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
            (root/'meta.json').write_text(json.dumps(dict(ref=ref,kind='dataset',license=licence,updated=updated,files=got,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest()),indent=2)+'\n')
            versions[ref]=updated;changed.append(ref)
            print('DATASET fetched',ref,licence,updated,[(x['file'],x['bytes']) for x in got],flush=True)
        except Exception as e:
            status=getattr(getattr(e,'response',None),'status_code',None)
            print('DATASET error',ref,type(e).__name__,status or 'transport failure',flush=True)
            if status==429:break
    print('DATASET listed',len(refs),'changed licensed',len(changed),flush=True)
    return changed
