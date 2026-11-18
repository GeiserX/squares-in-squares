"""Read-only Kaggle SDK transport; public downloads stay bounded data files."""
import json
from pathlib import Path
import urllib.parse
import requests
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import harvest_fetch as H
BASE='https://api.kaggle.com/v1/'


def call(service,method,body):
    response=requests.post(BASE+service+'/'+method,json=body,
        headers={'Authorization':'Bearer '+H.TOK,'User-Agent':'kaggle-api/v1.7.0'},
        timeout=(10,30),allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect:raise ValueError('unexpected metadata RPC redirect')
    data=response.json()
    if isinstance(data,dict) and int(data.get('code',0))>=400:raise ValueError('Kaggle RPC error code '+str(data['code']))
    return data


def get(url):
    parsed=urllib.parse.urlsplit(url)
    args={k:v[-1] for k,v in urllib.parse.parse_qs(parsed.query).items()}
    if parsed.path.endswith('/kernels/list'):
        body=dict(args,page=int(args.get('page',1)),pageSize=int(args.get('pageSize',100)),sortBy=3)
        return call('kernels.KernelsApiService','ListKernels',body).get('kernels',[])
    if parsed.path.endswith('/kernels/output'):
        body=dict(args,pageSize=100);files=[]
        for _ in range(20):
            data=call('kernels.KernelsApiService','ListKernelSessionOutput',body)
            files.extend(data.get('files',[]))
            token=data.get('nextPageToken')
            if not token:return dict(data,files=files)
            body['pageToken']=token
        raise ValueError('kernel output pagination exceeded20 pages')
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
