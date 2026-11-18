"""Copy upstream notices from the immutable, per-input source walk into cells."""
import hashlib
import json
from pathlib import Path
import re
from walk import Q

SKIP=re.compile(r'(?:^|_)(?:excluded?|rejected?|control|policy|diagnostic|comparison|prvsim|shares?|audit)(?:_|$)',re.I)
SKIP_KEYS={'walk','walked_texts','what_was_measured','next','coordinates','points','rows','squares','P'}


def clean(text):
    return Q.CMP.sub(Q._cmp,Q.NEG.sub(' ',text))


def fields(value,mode=None):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in SKIP_KEYS or SKIP.search(key):continue
            kind=mode
            if key in ('source','src','source_record','source_ref','source_name','source_file','donor_source','dataset','dataset_ref','notebook','notebook_ref','ref') or key.endswith('_source'):kind='source'
            if key in ('licence','license','licences','licenses','license_name','licence_name','licenseName','licenceName') or key.endswith(('_licence','_license')):kind='licence'
            yield from fields(child,kind)
    elif isinstance(value,list):
        for child in value:yield from fields(child,mode)
    elif isinstance(value,str) and mode:
        yield mode,clean(value)


def recorded_notices(job):
    source=job.get('source','')
    match=re.findall(r'walked source snapshot ($SCRATCH/bounties-squares/take-harvest-r\d+/work/source-proofs/[^ ;]+\.json)',source)
    if not match:return [],[]
    path=Path(match[-1]);data=json.loads(path.read_text())
    original=job.get('inherited_job',job)
    assert path.stem.split('-',1)[0]==original['sha256'],'source proof belongs to another input'
    digest=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    assert path.stem.rsplit('-',1)[-1]==digest[:16],'source proof bytes changed'
    sources=set();licences=set()
    for label,text in data.get('walked_texts',[]):
        try:items=list(fields(json.loads(text)))
        except (ValueError,TypeError):
            items=[]
            if ' || ' in text:
                src,lic=text.rsplit(' || ',1);items=[('source',clean(src)),('licence',clean(lic))]
        for kind,value in items:
            if kind=='source' and any(s in value for s in ['areebbb/','kmmmvs/','Upstream per-n records:','Other']):sources.add(value)
            if kind=='licence' and any(s in value for s in ['Apache','CC0','CC BY','MIT','Other']):licences.add(value)
    return sorted(sources),sorted(licences)


def compact_notices(sources,licences):
    refs=set();chains=set();terms=set();contexts=set()
    texts=sources+licences
    for text in texts:
        text=text.replace('\\','')
        for match in re.finditer(r'(?<![\w/.-])([\w.-]+/[\w.-]+)\s*::\s*([^\s;<>" ]+)',text):
            ref,name=match.groups()
            if ref.split('/')[0] not in {'results','seeds','gather','work','near','notebooks','datasets'} and not ref.startswith('take-'):
                refs.add(ref+' :: '+name.rstrip('),]}'))
        bare=re.match(r'^([\w.-]+/[\w.-]+)(?=$|[ ;(])',text)
        if bare and bare[1].split('/')[0] not in {'results','seeds','gather','work','near','notebooks','datasets'} and not bare[1].startswith('take-'):refs.add(bare[1])
        refs.update(re.findall(r'kaggle\.com/(?:code|datasets)/([\w.-]+/[\w.-]+)',text))
        refs.update(re.findall(r'(?:^|[ =])(?:notebooks|datasets)/([\w.-]+/[\w.-]+)',text))
        refs.update(ref+' (GitHub)' for ref in re.findall(r'([\w.-]+/[\w.-]+)\s*\(GitHub\)',text))
        for match in re.finditer(r'areebbb/sis-certified-union-micro-shrink-lb-22-17479\s*::\s*per_n\.csv,\s*donor n\s*=\s*(\d+),\s*src=([^\s;<>" ]+)',text):
            chains.add('areebbb/sis-certified-union-micro-shrink-lb-22-17479 -> per_n.csv, donor n='+match[1]+', src='+match[2].rstrip('),]}'))
    for text in licences:
        for pattern,label in [(r'Apache[ -]+2(?:\.0)?','Apache 2.0'),(r'CC0','CC0'),(r'CC[ -]+BY[ -]+4(?:\.0)?|Attribution 4\.0','CC BY 4.0'),(r'\bMIT\b','MIT')]:
            if re.search(pattern,text,re.I):terms.add(label)
        if 'Other' in text:
            match=re.search(r'Other(?:\s*\([^)]{0,120}\))?',text)
            if match:terms.add(match[0])
    return sorted(refs),sorted(chains),sorted(terms)


def enrich(row,job):
    sources,licences=recorded_notices(job)
    source_mark='; harvest29 pinned upstream source notices: '
    licence_mark=' | harvest29 pinned upstream licence notices: '
    row=dict(row)
    row['source']=row['source'].split(source_mark,1)[0]
    row['licence']=row['licence'].split(licence_mark,1)[0]
    refs,chains,terms=compact_notices(sources,licences)
    public_notes=' | '.join(chains+refs)
    if public_notes:row['source']+=source_mark+public_notes
    if terms or public_notes:row['licence']+=licence_mark+'; '.join(terms)+(' | '+public_notes if public_notes else '')
    if max(len(row['source']),len(row['licence']))>120_000:raise ValueError('upstream notice field exceeds portable TSV field size')
    return row
