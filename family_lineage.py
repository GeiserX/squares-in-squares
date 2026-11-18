"""Label the saved family ancestry for the round24 seed decision."""
import csv,hashlib,json,re
from pathlib import Path
from functools import lru_cache

def declared_status(licence):
    matches=list(re.finditer(r'Samanyu(?:-dev)?\s+(?:seed\s+)?ancestry:\s*(none|no|absent|yes|present|seeds?)\b',licence,re.I))
    if not matches:return None
    return 'no' if matches[-1][1].lower() in ('none','no','absent') else 'yes'

@lru_cache(None)
def seed_origins(scratch):
    s=Path(scratch);best={}
    for name in ['samanyu_22249','samanyu_bestfit','couzo']:
        for r in csv.DictReader(open(s/'seeds'/f'{name}.tsv'),delimiter='\t'):
            if r['reason']!='ok':continue
            n=int(r['n']);score=float(r['score'])
            if n not in best or score<best[n][0]:best[n]=(score,name)
    return {n:name for n,(_,name) in best.items()}

class Lineage:
    def __init__(self,scratch,work):
        self.s=Path(scratch);self.w=Path(work);self.cache={};self.origins=seed_origins(str(self.s))
    def classify(self,n,source,licence):
        licence=re.sub(r'(?:\s*\|\s*)?Samanyu(?:-dev)?\s+(?:seed\s+)?ancestry:\s*(?:(?:none|no|absent)\b|yes(?:,\s*seed n=[\d,]+)?|unknown)','',licence,flags=re.I)
        key=hashlib.sha256((str(n)+source+licence).encode()).hexdigest()
        if key in self.cache:return self.cache[key]
        text=source+' '+licence
        graph=dict(text=text,records=[],note='Classifies the saved source record. Mutable live sidecars can describe a newer layout.')
        text=re.sub(r'Samanyu(?:-dev)?\s+(?:seed\s+)?ancestry:\s*(?:none|no|absent)\b','',text,flags=re.I)
        seeds=set();unknown=[]
        for m in re.finditer(r'seed merged0',text,re.I):
            before=text[max(0,m.start()-1600):m.start()]
            refs=list(re.finditer(r'\bn\s*=\s*(\d+)\b|\bheld\s+(\d+)\b|(?<!\d)(\d+)[a-z][\w-]*\.(?:C|F\d)',before))
            sn=int(next((v for v in refs[-1].groups() if v),str(n))) if refs else n
            if sn not in self.origins:unknown.append(sn)
            elif self.origins[sn].startswith('samanyu'):seeds.add(sn)
        for m in re.finditer(r'(?:n\s*=\s*|seed\s+)(\d+)[^.;<>]{0,60}Samanyu',text,re.I):
            sn=int(m[1])
            if self.origins.get(sn,'').startswith('samanyu'):seeds.add(sn)
        if re.search(r'Samanyu',text,re.I) and not seeds:unknown.append(n)
        status='unknown' if unknown else ('yes' if seeds else 'no')
        label='Samanyu ancestry: '+status+(', seed n='+','.join(map(str,sorted(seeds))) if seeds else '')
        result=dict(status=status,seeds=sorted(seeds),unknown=unknown,licence=licence+' | '+label,source=source,graph=graph)
        self.cache[key]=result
        return result
