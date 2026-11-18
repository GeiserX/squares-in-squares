"""Read changed public register witnesses with bounded, unauthenticated requests."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import time
import requests
import subprocess
import shutil
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import W,S,L,state,write_json
sys.path.insert(0,str(L))
import harvest_register as R
from angle_take import accepted

API='https://api.github.com'
RAW='https://raw.githubusercontent.com'
DATA_SUFFIX={'.yaml','.yml','.cert','.sqpk','.txt','.csv'}


def get(url,binary=False):
    if not binary and url.startswith(API+'/') and shutil.which('gh'):
        result=subprocess.run(['gh','api',url[len(API)+1:]],cwd=L.parents[1],capture_output=True,timeout=45)
        if result.returncode:raise requests.HTTPError('GitHub metadata CLI request failed')
        if len(result.stdout)>15_000_000:raise ValueError('GitHub metadata exceeds15MB')
        return json.loads(result.stdout)
    r=requests.get(url,headers={'User-Agent':'squares-public-data-reader'},timeout=(10,25))
    if r.status_code==403 and r.headers.get('X-RateLimit-Remaining')=='0':
        (W/'github-api-retry.txt').write_text(str(int(r.headers.get('X-RateLimit-Reset',time.time()+1800))+30))
    r.raise_for_status()
    if len(r.content)>15_000_000:raise ValueError('GitHub data response exceeds15MB')
    return r.content if binary else r.json()


def changed_files(old,new):
    if old.get('truncated') or new.get('truncated'):raise ValueError('truncated source tree')
    prior={r['path']:r['sha'] for r in old['tree'] if r['type']=='blob'}
    return [r for r in new['tree'] if r['type']=='blob' and prior.get(r['path'])!=r['sha']]


def fetch(root):
    cache=W/'github-cache.json';prior_root=S/'take-harvest-r30/work/github-delta'
    if cache.exists():old=json.loads(cache.read_text())
    else:
        summary=json.loads((prior_root/'summary.json').read_text())
        repos=json.loads((prior_root/'doga.json').read_text())
        old=dict(register=summary['register']['sha'],doga={r['full_name']:r['pushed_at'] for r in repos})
    retry=W/'github-api-retry.txt'
    api_ready=bool(shutil.which('gh')) or not retry.exists() or float(retry.read_text())<time.time()
    if api_ready:
        try:head=get(API+'/repos/jlevy/squares/commits?per_page=1')[0]['sha']
        except requests.HTTPError:
            head=subprocess.run(['git','-c','core.hooksPath=/dev/null','ls-remote','https://github.com/jlevy/squares.git','HEAD'],cwd=L.parents[1],check=True,capture_output=True,text=True,timeout=30).stdout.split()[0]
            api_ready=False
    else:
        head=subprocess.run(['git','-c','core.hooksPath=/dev/null','ls-remote','https://github.com/jlevy/squares.git','HEAD'],cwd=L.parents[1],check=True,capture_output=True,text=True,timeout=30).stdout.split()[0]
    try:repos=get(API+'/users/kenaznia-doga/repos?per_page=100&sort=pushed') if api_ready else []
    except Exception as exc:
        state('GITHUB account metadata deferred '+type(exc).__name__);repos=[]
    changed=[r for r in repos if old['doga'].get(r['full_name'])!=r['pushed_at']]
    metadata=dict(utc=time.time(),register=head,register_changed=head!=old['register'],changed_doga=[r['full_name'] for r in changed])
    root.mkdir(exist_ok=True);write_json(root/'github-status.json',metadata)
    state('GITHUB metadata '+json.dumps(metadata,sort_keys=True))
    if head==old['register'] and not changed:
        write_json(cache,old);return 0
    total=0
    if head!=old['register']:
        base_tree=W/'github-tree.json'
        old_tree=json.loads((base_tree if base_tree.exists() else prior_root/'tree-new.json').read_text())
        tree=get(API+'/repos/jlevy/squares/git/trees/'+head+'?recursive=1')
        delta=changed_files(old_tree,tree);write_json(root/'github-tree.json',tree)
        groups=collections.defaultdict(list)
        for item in delta:
            path=Path(item['path'])
            if path.suffix.lower() not in DATA_SUFFIX:continue
            parts=path.parts
            if parts[:3]==('packing','resources','web') and len(parts)>4:groups['/'.join(parts[:4])].append(item)
            elif parts[:2]==('packing','witnesses'):groups['packing/witnesses'].append(item)
        for prefix,items in groups.items():
            if len(items)>100:raise ValueError('changed packet exceeds100 data files; needs a separate bounded pass')
            src=root/'github-source'/prefix;src.mkdir(parents=True,exist_ok=True)
            # Witnesses carry the register data licence. Packets keep their own.
            notices=['LICENSE','README.md'] if prefix=='packing/witnesses' else [r['path'][len(prefix)+1:] for r in tree['tree'] if r['type']=='blob' and r['path'].startswith(prefix+'/') and Path(r['path']).name.upper().startswith(('LICENSE','LICENCE','COPYING','README'))]
            for notice in notices:
                path=notice if prefix=='packing/witnesses' else prefix+'/'+notice
                try:raw=get(RAW+'/jlevy/squares/'+head+'/'+path,True)
                except requests.HTTPError:continue
                dest=src/notice;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            lic=R.licence([src/'source',src])
            if not accepted(lic):
                state(f'GITHUB excluded packet {prefix}: {lic}');continue
            for item in items:
                if int(item.get('size',0))>8_000_000:continue
                raw=get(RAW+'/jlevy/squares/'+head+'/'+item['path'],True)
                # Git blob identity is pinned independently of the HTTPS path.
                identity=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                if identity!=item['sha']:raise ValueError('Git blob identity differs')
                dest=src/Path(item['path']).relative_to(prefix);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            out=root/'data/gh'/('jlevy__squares__'+prefix.replace('/','__'))
            stats=collections.defaultdict(int)
            total+=R.packet(src,out,f'github.com/jlevy/squares@{head} {prefix}',lic,stats)
            state(f'GITHUB changed packet {prefix} stats={dict(stats)}')
        write_json(base_tree,tree);old['register']=head
    for repo in changed:
        ref=repo['full_name']
        state('GITHUB changed author repository '+ref+' pushed='+repo['pushed_at'])
        try:
            commit=get(API+'/repos/'+ref+'/commits?per_page=1')[0]['sha']
            tree=get(API+'/repos/'+ref+'/git/trees/'+commit+'?recursive=1')
            if tree.get('truncated'):raise ValueError('truncated author tree')
            src=root/'github-source'/ref;src.mkdir(parents=True,exist_ok=True)
            notices=[r for r in tree['tree'] if r['type']=='blob' and Path(r['path']).name.upper().startswith(('LICENSE','LICENCE','COPYING','README'))]
            for item in notices:
                if int(item.get('size',0))>1_000_000:continue
                dest=src/item['path'];dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(get(RAW+'/'+ref+'/'+commit+'/'+item['path'],True))
            lic=R.licence([src])
            if accepted(lic):
                items=[r for r in tree['tree'] if r['type']=='blob' and Path(r['path']).suffix.lower() in DATA_SUFFIX and int(r.get('size',0))<8_000_000]
                if len(items)>100:raise ValueError('changed author repository exceeds100 data files')
                for item in items:
                    raw=get(RAW+'/'+ref+'/'+commit+'/'+item['path'],True)
                    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=item['sha']:raise ValueError('author blob identity differs')
                    dest=src/item['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
                stats=collections.defaultdict(int)
                total+=R.packet(src,root/'data/gh'/ref.replace('/','__'),f'github.com/{ref}@{commit}',lic,stats)
                state(f'GITHUB author packet {ref} stats={dict(stats)}')
            else:state(f'GITHUB excluded author packet {ref}: {lic}')
            old['doga'][ref]=repo['pushed_at']
        except Exception as exc:state('GITHUB author packet deferred '+ref+' '+type(exc).__name__)
    write_json(cache,old)
    return total


def control():
    prior={'tree':[dict(path='a',sha='1',type='blob')]}
    new={'tree':[dict(path='a',sha='2',type='blob'),dict(path='b',sha='3',type='blob')]}
    assert [r['path'] for r in changed_files(prior,new)]==['a','b']
    assert changed_files(new,new)==[]
    try:changed_files(prior,dict(new,truncated=True))
    except ValueError:pass
    else:raise AssertionError('truncated source tree passed')
    path=S/'take-harvest-r30/work/github-delta/register-data/packing/witnesses'
    print('CONTROL changed and unchanged Git trees distinguished; truncated tree refused',flush=True)

if __name__=='__main__':control()
