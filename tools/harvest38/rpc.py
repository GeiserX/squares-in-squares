"""Read-only Kaggle SDK transport; public downloads stay bounded data files."""
import json
import hashlib
import time
import re
from pathlib import Path
import urllib.parse
import requests
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import harvest_fetch as H
BASE='https://api.kaggle.com/v1/'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import W
LISTING_ROOT=W/'listing-checkpoints'

class RPCError(RuntimeError):
    def __init__(self,code):
        from types import SimpleNamespace
        self.response=SimpleNamespace(status_code=int(code))
        super().__init__('Kaggle RPC error code '+str(code))


def call(service,method,body):
    response=requests.post(BASE+service+'/'+method,json=body,
        headers={'Authorization':'Bearer '+H.TOK,'User-Agent':'kaggle-api/v1.7.0'},
        timeout=(10,30),allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect:raise ValueError('unexpected metadata RPC redirect')
    data=response.json()
    if isinstance(data,dict) and int(data.get('code',0))>=400:raise RPCError(data['code'])
    return data


def get(url):
    parsed=urllib.parse.urlsplit(url)
    args={k:v[-1] for k,v in urllib.parse.parse_qs(parsed.query).items()}
    if parsed.path.endswith('/kernels/list'):
        body=dict(args,page=int(args.get('page',1)),pageSize=int(args.get('pageSize',100)),sortBy=3)
        return call('kernels.KernelsApiService','ListKernels',body).get('kernels',[])
    if parsed.path.endswith('/kernels/output'):
        stamp=args.pop('harvestRun',None)
        body=dict(args,pageSize=100)
        return output_pages(body,stamp)
    if parsed.path.endswith('/datasets/list'):
        body=dict(args,page=int(args.get('page',1)),pageSize=100,sortBy=2)
        return call('datasets.DatasetApiService','ListDatasets',body).get('datasets',[])
    raise ValueError('unsupported read-only RPC route')


def download(url,path,limit=120_000_000):
    path=Path(path);temp=Path(str(path)+'.part')
    try:
        with requests.get(url,stream=True,timeout=(10,30)) as response:
            response.raise_for_status();total=0
            with temp.open('wb') as f:
                for block in response.iter_content(1<<20):
                    total+=len(block)
                    if total>limit:raise ValueError('public file exceeds bounded download')
                    f.write(block)
        temp.replace(path)
    finally:
        if temp.exists():temp.unlink()


def download_dataset(ref,path):
    owner,slug=ref.split('/')
    response=requests.post(BASE+'datasets.DatasetApiService/DownloadDataset',
        json=dict(ownerSlug=owner,datasetSlug=slug,raw=False),
        headers={'Authorization':'Bearer '+H.TOK,'User-Agent':'kaggle-api/v1.7.0'},
        timeout=(10,30),allow_redirects=False)
    response.raise_for_status()
    url=response.headers.get('Location') if response.is_redirect else response.json().get('url')
    if not url:raise ValueError('dataset RPC supplied no download redirect')
    # The signed file URL receives no Kaggle Authorization header.
    download(url,path)


def output_pages(body,stamp=None):
    body=dict(body);files=[];tokens=set();pages=0;checkpoint=None
    if stamp:
        key=hashlib.sha256(json.dumps([body.get('userName'),body.get('kernelSlug'),stamp]).encode()).hexdigest()
        LISTING_ROOT.mkdir(parents=True,exist_ok=True);checkpoint=LISTING_ROOT/(key+'.json')
        if checkpoint.exists():
            saved=json.loads(checkpoint.read_text());expected=saved.pop('sha256')
            if hashlib.sha256(json.dumps(saved,sort_keys=True).encode()).hexdigest()!=expected:
                raise ValueError('output listing checkpoint changed')
            if saved['stamp']!=stamp:raise ValueError('output listing checkpoint version changed')
            files=saved['files'];tokens=set(saved['tokens']);pages=saved['pages']
            body['pageToken']=saved['next']
    for _ in range(pages,200):
        data=call('kernels.KernelsApiService','ListKernelSessionOutput',body)
        files.extend(data.get('files',[]));pages+=1
        sessions=set(m[1] for f in files if (m:=re.search(r'/kf/(\d+)/',f.get('url') or '')))
        if len(sessions)>1:raise ValueError('output session changed during pagination')
        token=data.get('nextPageToken')
        if not token:
            if checkpoint is not None and checkpoint.exists():checkpoint.unlink()
            return dict(data,files=files)
        if token in tokens:raise ValueError('kernel output pagination repeated token')
        tokens.add(token);body['pageToken']=token
        if checkpoint is not None:
            saved=dict(stamp=stamp,files=files,tokens=sorted(tokens),pages=pages,next=token)
            saved['sha256']=hashlib.sha256(json.dumps(saved,sort_keys=True).encode()).hexdigest()
            temp=checkpoint.with_suffix('.json.tmp');temp.write_text(json.dumps(saved)+'\n');temp.replace(checkpoint)
        time.sleep(1.0)
    raise ValueError('kernel output pagination exceeded200 pages')


def control():
    from unittest.mock import patch
    pages=[dict(files=[dict(fileName=f'page{i}.csv')],nextPageToken=str(i+1)) for i in range(24)]
    pages.append(dict(files=[dict(fileName='submission.csv')]))
    with patch.object(time,'sleep') as pace,patch.dict(globals(),call=lambda *args:pages.pop(0)):
        result=output_pages(dict(pageSize=100))
        assert len(result['files'])==25 and result['files'][-1]['fileName']=='submission.csv' and not pages
        assert pace.call_count==24 and all(call.args==(1.0,) for call in pace.call_args_list)
    with patch.object(time,'sleep'),patch.dict(globals(),call=lambda *args:dict(files=[],nextPageToken='same')):
        try:output_pages({})
        except ValueError as exc:assert 'repeated token' in str(exc)
        else:raise AssertionError('cyclic pagination was accepted')
    with patch.object(time,'sleep'),patch.dict(globals(),call=lambda *args:dict(files=[],nextPageToken=str(args[-1].get('pageToken',''))+'a')):
        try:output_pages({})
        except ValueError as exc:assert 'exceeded200' in str(exc)
        else:raise AssertionError('listing bound was ignored')
    import tempfile
    with tempfile.TemporaryDirectory(dir=W) as directory:
        with patch.dict(globals(),LISTING_ROOT=Path(directory)),patch.object(time,'sleep'):
            first=dict(files=[dict(fileName='first.csv',url='https://data.invalid/kf/1/first')],nextPageToken='second')
            with patch.dict(globals(),call=lambda *args:first) as unused:
                calls=0
                def interrupt(*args):
                    nonlocal calls
                    calls+=1
                    if calls==2:raise TimeoutError('forced interruption')
                    return first
                with patch.dict(globals(),call=interrupt):
                    try:output_pages(dict(userName='example',kernelSlug='source'),'run1')
                    except TimeoutError:pass
                    else:raise AssertionError('forced interruption did not run')
            saved_file=next(Path(directory).glob('*.json'));saved_bytes=saved_file.read_bytes()
            bad=json.loads(saved_bytes);bad['files'][0]['fileName']='tampered.csv';saved_file.write_text(json.dumps(bad))
            try:output_pages(dict(userName='example',kernelSlug='source'),'run1')
            except ValueError as exc:assert 'checkpoint changed' in str(exc)
            else:raise AssertionError('tampered listing checkpoint accepted')
            saved_file.write_bytes(saved_bytes)
            seen=[]
            def finish(*args):
                seen.append(args[-1].get('pageToken'))
                return dict(files=[dict(fileName='submission.csv',url='https://data.invalid/kf/1/last')])
            with patch.dict(globals(),call=finish):
                result=output_pages(dict(userName='example',kernelSlug='source'),'run1')
                assert seen==['second'] and len(result['files'])==2
            seen.clear()
            with patch.dict(globals(),call=finish):
                output_pages(dict(userName='example',kernelSlug='source'),'run2')
                assert seen==[None]
            requests=[]
            def route(*args):requests.append(args[-1]);return dict(files=[])
            with patch.dict(globals(),call=route):
                get('https://www.kaggle.com/api/v1/kernels/output?userName=example&kernelSlug=source&harvestRun=private-run')
                assert len(requests)==1 and 'harvestRun' not in requests[0]
    print('CONTROL output file beyond page20 retained; repeated tokens refused; listing stops at200 pages',flush=True)
    print('CONTROL interrupted listing resumes its next token; changed run starts fresh; tampered checkpoint refused; private stamp stays local; metadata requests paced one second apart',flush=True)

if __name__=='__main__':control()
