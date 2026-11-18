#!/usr/bin/env python3
"""Conservative source admission for family follow queues. Reads local data only."""
import csv, hashlib, json, re
from pathlib import Path
import family_step as fs
import family_loop as fl

class Audit:
    def archived_public(self,n):
        if n in {639,691,745,801,858,918,980,981}:raise ValueError('excluded archive alias')
        from readers_sources import archived_polish
        return archived_polish(str(self.s),n)

    BASE = 'gather/round23-2026-11-13a.csv'

    def __init__(self, scratch, lane, work):
        self.s = Path(scratch); self.l = Path(lane); self.w = Path(work)
        self.cache = {}; self.proofs = {}; self.rejected = {}
        override=self.w/'notice-overrides.json'
        self.overrides=json.loads(override.read_text()) if override.exists() else {}
        self.base = fs.load(str(self.s/self.BASE))
        self.tables = {}
        for p in self.l.glob('results/round*-best-*.tsv'):
            m = re.search(r'round(\d+)-', p.name)
            if m and int(m[1]) <= 23:
                self.tables[int(m[1])] = (p, {int(r['n']):r for r in csv.DictReader(open(p),delimiter='\t')})
        self.initial = {int(r['n']):r for r in csv.DictReader(open(self.l/'results/harvest-best-2026-11-09.tsv'),delimiter='\t')}
        self.public = {int(r['n']):r for r in csv.DictReader(open(self.s/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'))}

    def base_source(self, n):
        for rnd,(p,tab) in sorted(self.tables.items(),reverse=True):
            if n in tab:
                r=tab[n]; return 'candidate round23 n=%d, %s: %s'%(n,p.name,r['source']),r['licence']
        r=self.initial[n]
        so=r['source'];lic=r['licence']
        if so=='seed merged0':
            so='original seed, franciscouzo/square-packing (MIT) and Samanyu-dev/squares_in_squares (no licence stated), results/harvest-best-2026-11-09.tsv n=%d'%n
            lic='seed coordinates; MIT and no licence stated upstream; sources credited'
        return so,lic

    def __call__(self,n,path,source,licence):
        path=str(path); p=Path(path)
        try: stamp=(p.stat().st_mtime_ns,p.stat().st_size)
        except OSError:return None
        key=(n,path,stamp,source,licence)
        if key in self.cache:return self.cache[key]
        try:
            P=self.base[n] if p == self.s/self.BASE else fs.load(path,{n})[n]
            trusted_override=path in self.overrides
            if trusted_override:
                record=self.overrides[path]
                if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('notice override geometry changed')
                source,licence=record['source'],record['licence']
            if n in self.base and (P==self.base[n]).all():
                source,licence=self.base_source(n)
                # The brief names this exact candidate as the clean donor pool. Its
                # source table remains usable when an intermediate take row vanished.
                if any(x in source for x in ['squares-verified-best-of-1105','squares-joegun-boxed-certified-union']):
                    raise ValueError('excluded candidate source notice')
            elif not trusted_override:
                source,licence=self.expand(n,source,licence)
            if any(x in source+' '+licence for x in ['squares-verified-best-of-1105','squares-joegun-boxed-certified-union']):
                raise ValueError('excluded source notice')
            result=(source,licence)
            digest=hashlib.sha256(P.tobytes()).hexdigest()
            self.proofs[digest]=dict(n=n,path=path,source=source,licence=licence)
        except (ValueError,KeyError,OSError,AssertionError) as ex:
            self.rejected[path+'#'+str(n)]=str(ex);result=None
        if result is not None:self.cache[key]=result
        return result

    def expand(self,n,source,licence,trail=()):
        if not source or not licence:raise ValueError('missing source or licence')
        source=re.sub(r'(?<![\w/-])(take-[\w-]+-r\d+/near/[^\s<>"(),;]+\.csv)',lambda m:str(self.s/m[1]),source)
        text=source+' '+licence
        if 'squares-verified-best-of-1105' in text or 'squares-joegun-boxed-certified-union' in text:
            raise ValueError('excluded upstream')
        if re.search(r'(?:held|packing of|donor)\s*(?:packing of\s*)?n\s*=\s*801\b',text):
            raise ValueError('excluded held801')
        for match in re.finditer(r'take-(harvest|forensics|midm|invent)-r(\d+)/(?:near/|work/donors/)?(\d+)',text):
            lane,rnd,dn=match[1],int(match[2]),int(match[3])
            if (lane=='harvest' and rnd==22 and dn in {639,691,745,858,918}) or (rnd==23 and dn==639) or (lane=='forensics' and rnd<=23 and dn==918) or (lane=='forensics' and rnd==23 and dn==980):
                raise ValueError('excluded frozen ancestor '+match[0])
        # Resolve every explicit near-file parent, not the current file's descriptive basename.
        extra=[]; notices=[]
        for pp in dict.fromkeys(re.findall(r'($SCRATCH/bounties-squares/take-[^\s<>"(),;]+/near/[^\s<>"(),;]+\.csv)',text)):
            m=re.match(r'(\d+)',Path(pp).name)
            if not m:continue
            pn=int(m[1]); so,li=fl.near_metadata(pp,pn)
            if pp in self.overrides:
                record=self.overrides[pp]
                if hashlib.sha256(Path(pp).read_bytes()).hexdigest()!=record['sha256']:raise ValueError('notice override geometry changed')
                so,li=record['source'],record['licence']
            if not so:
                nearledger=Path(pp).parent/'near.tsv'
                if nearledger.exists():
                    for row in csv.DictReader(open(nearledger),delimiter='\t'):
                        if row.get('file')==Path(pp).name and int(row.get('n',0))==pn:
                            so,li=row.get('source',''),row.get('licence','');break
            if not so:raise ValueError('untraced near ancestor '+pp)
            if so and so not in text:
                if pp in trail or len(trail)>=20:raise ValueError('unresolved near ancestry cycle '+pp)
                if pp not in self.overrides and not so.startswith('candidate round23 n='):
                    so,li=self.expand(pn,so,li,trail+(pp,))
                extra.append('parent '+pp+': '+so);notices.append(li)
        # A per-n take file is an input too. Read its own source row rather than infer it
        # from the source of the target. Immutable inline records take precedence.
        for match in re.finditer(r'(?:$SCRATCH/bounties-squares/)?(take-[\w-]+-r\d+)/(\d+)\.csv',text):
            pp=str(self.s/match[1]/(match[2]+'.csv'));pn=int(match[2])
            archived=False
            so,li=fl.handoff_metadata(pp,pn)
            if not so:
                ledger=Path(pp).parent/'take.tsv'
                if ledger.exists():
                    for row in csv.DictReader(open(ledger),delimiter='\t'):
                        if row.get('n')==str(pn):so,li=row.get('source',''),row.get('licence','');break
            if not so:
                try:
                    P=fs.load(pp,{pn})[pn]
                    if pn in self.base and (P==self.base[pn]).all():so,li=self.base_source(pn)
                except (OSError,KeyError,ValueError):pass
            if not so and match[1] in ('take-harvest-r22','take-polish-r22'):
                try:
                    archive=self.archived_public(pn)
                    so='verified retained public input '+json.dumps(archive,sort_keys=True);li=archive['licence'];archived=True
                except (OSError,KeyError,ValueError,StopIteration):pass
            if not so:raise ValueError('untraced take ancestor '+pp)
            if so not in text:
                if pp in trail or len(trail)>=20:raise ValueError('unresolved take ancestry cycle '+pp)
                if not archived and not so.startswith('candidate round23 n='):
                    so,li=self.expand(pn,so,li,trail+(pp,))
                extra.append('parent '+pp+': '+so);notices.append(li)
        # Frozen source records name the donor n next to each public source occurrence.
        for m in re.finditer(r'areebbb/sis-certified-union-micro-shrink-lb-22-17479',text):
            before=text[:m.start()]
            nums=re.findall(r'\bn\s*=\s*(\d+)\b|from(\d+)-',before)
            pn=int(next((a or b for a,b in reversed(nums)),n))
            if pn in {639,691,745,858,918}:raise ValueError('excluded areeb donor n='+str(pn))
            row=self.public.get(pn)
            if not row:raise ValueError('missing public per-n record')
            if 'squares-joegun-boxed-certified-union' in row['src']:raise ValueError('excluded public chain')
            # The round22 assembler recorded upstream terms for every accepted public donor.
            record=self.tables.get(22,(None,{}))[1].get(pn)
            if not record or 'per_n.csv' not in record['source']:
                try:
                    archive=self.archived_public(pn)
                    record=dict(source='verified retained public input '+json.dumps(archive,sort_keys=True),licence=archive['licence'])
                except (OSError,KeyError,ValueError,StopIteration):
                    raise ValueError('public upstream terms unresolved n='+str(pn))
            extra.append('upstream n=%d: %s'%(pn,record['source']));notices.append(record['licence'])
        # Basename-only handoffs and generic source notices cannot establish ancestry.
        if re.search(r'(?:near miss|handoff log) of n',source) and ', ' not in source:
            raise ValueError('untraced handoff')
        if 'see the ' in licence and not extra and not any(x in text for x in ['module build:', 'held packing', 'family_readers.py','k123_join.py','border_sweep.py']):
            raise ValueError('untraced source notice')
        source+=''.join(' | '+x for x in dict.fromkeys(extra))
        licence+=''.join(' | '+x for x in dict.fromkeys(notices) if x)
        # Recheck all expanded records for the two prohibited public sources.
        if any(x in source+' '+licence for x in ['squares-verified-best-of-1105','squares-joegun-boxed-certified-union']):raise ValueError('excluded expanded upstream')
        return source,licence

    def save(self):
        (self.w/'source-admission.json.tmp').write_text(json.dumps(dict(accepted=list(self.proofs.values()),rejected=self.rejected),indent=2)+'\n')
        (self.w/'source-admission.json.tmp').replace(self.w/'source-admission.json')
