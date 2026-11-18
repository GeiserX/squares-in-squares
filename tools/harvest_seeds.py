"""Name seed roots and retain source-qualified alternatives for round 24."""
import csv
from functools import lru_cache
import re
from pathlib import Path

SPECIAL = {228,459,503,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990}
MARK = re.compile(r'\s*\[Samanyu seed ancestry:[^\]]*\]')


@lru_cache(maxsize=256)
def source_table(path, stamp):
    with Path(path).open() as stream:
        return {int(row['n']): row for row in csv.DictReader(stream, delimiter='\t') if row.get('n','').isdigit()}


def seed_origins(scratch):
    best = {}
    for name in ('samanyu_22249', 'samanyu_bestfit', 'couzo'):
        path = Path(scratch)/'seeds'/(name+'.tsv')
        if not path.exists():
            continue
        with path.open() as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                if row.get('reason') != 'ok':
                    continue
                n, score = int(row['n']), float(row['score'])
                if n not in best or score < best[n][0]:
                    best[n] = score, 'samanyu' if name.startswith('samanyu') else 'couzo'
    return {n: origin for n, (score, origin) in best.items()}


def classify(text, origins):
    was_unknown = '[Samanyu seed ancestry: unknown' in text
    retained = {int(n) for group in re.findall(r'\[Samanyu seed ancestry: yes \(seed n=([0-9,]+)\)\]', text) for n in group.split(',')}
    text = MARK.sub('', text)
    if 'unresolved archived parent' in text:
        return 'unknown', ()
    # A negative label is metadata, not a source notice.
    text = re.sub(r'(?:no Samanyu(?:-dev)?(?: seed)? ancestry|Samanyu(?:-dev)?(?: seed)? ancestry\s*[:=]\s*(?:no|none|false))', '', text, flags=re.I)
    explicit = set(int(n) for n in re.findall(r'n\s*=\s*(\d+)\s+of\s+Samanyu', text, re.I))
    explicit.update(int(n) for n in re.findall(r'Samanyu[^;|\n]{0,100}?\b(?:donor|seed)\s+n\s*=\s*(\d+)', text, re.I))
    seed_ids = set(int(n) for n in re.findall(r'(\d+)[A-Za-z0-9_-]*\.F[12]\s*<held:\s*seed merged0', text, re.I))
    seed_ids.update(int(n) for n in re.findall(r'\bseed\s+n\s*=\s*(\d+)', text, re.I))
    roots = retained | explicit | {n for n in seed_ids if origins.get(n) == 'samanyu'}
    if roots:
        return 'yes', tuple(sorted(roots))
    if was_unknown:
        return 'unknown', ()
    if re.search(r'Samanyu', text, re.I):
        return 'unknown', ()
    lower = text.casefold()
    if any(term in lower for term in ('see source', 'each donor source', 'held source notices', 'named round table')):
        return 'unknown', ()
    if not seed_ids and 'see readme' in lower:
        return 'unknown', ()
    if 'seed merged0' in lower and (not seed_ids or any(n not in origins for n in seed_ids)):
        return 'unknown', ()
    rooted_public = bool(re.search(r'(?:Apache|CC0|CC BY|MIT)', text, re.I) and re.search(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+', text))
    rooted_own = any(term in lower for term in ('our own design','own grid','our own construction','lattice taper'))
    rooted_catalogue = bool(seed_ids) and all(origins.get(n)=='couzo' for n in seed_ids)
    if not (rooted_public or rooted_own or rooted_catalogue):
        return 'unknown', ()
    return 'no', ()


def annotate(row, text, origins):
    flag, seeds = classify(text, origins)
    licence = MARK.sub('', row.get('licence', '')).strip()
    suffix = ('yes (seed n=' + ','.join(map(str,seeds)) + ')') if flag == 'yes' else ('no (recorded roots)' if flag == 'no' else 'unknown (seed root needs a record)')
    return dict(row, licence=licence+' [Samanyu seed ancestry: '+suffix+']'), flag, seeds


class SeedPolicy:
    def __init__(self, scratch, take, text, table, rows_write):
        self.s, self.t = Path(scratch), Path(take)
        self.w = self.t/'work'
        self.text, self.table, self.rows_write = text, table, rows_write
        self.origins = seed_origins(self.s)
        baseline = self.s/'gate/cand-round22-1113b/details.csv'
        self.relaxed = {}
        if baseline.exists():
            with baseline.open() as stream:
                self.relaxed = {int(row['n']):float(row['score']) for row in csv.DictReader(stream)}
        self.clean_counts = set()
        self.results = Path(__file__).resolve().parents[1]/'results'

    def held_record(self, n, rnd):
        choices=[]
        for path in self.results.glob('round*-best-*.tsv'):
            match=re.match(r'round(\d+)-best',path.name)
            if match and int(match[1])<=rnd:
                choices.append((int(match[1]),path))
        for number,path in sorted(choices,reverse=True):
            row=source_table(str(path),path.stat().st_mtime_ns).get(n)
            if row:
                return row,str(path)
        baseline=self.results/'harvest-best-2026-11-09.tsv'
        if rnd>=9 and baseline.exists():
            row=source_table(str(baseline),baseline.stat().st_mtime_ns).get(n)
            if row and row.get('source')=='seed merged0' and n in self.origins:
                source=('n = '+str(n)+' of Samanyu-dev/squares_in_squares (original seed, no licence)'
                        if self.origins[n]=='samanyu' else 'n = '+str(n)+' of franciscouzo/square-packing (original seed, MIT)')
                return dict(row,source=source),str(baseline)
            if row:return row,str(baseline)
        return None,''

    def archived_text(self, text):
        seen=set(re.findall(r'\[archived parent ([^\]]+)\]',text))
        held_seen=set(re.findall(r'\[held parent ([^\]]+)\]',text))
        for _ in range(32):
            added=[]
            for lane,count in dict.fromkeys(re.findall(r'(take-[a-z0-9-]+-r23)/(\d+)\.csv',text)):
                key=lane+'/'+count+'.csv'
                if key in seen:continue
                seen.add(key);ledger=self.s/lane/'take.tsv'
                row=source_table(str(ledger),ledger.stat().st_mtime_ns).get(int(count)) if ledger.exists() else None
                if row:
                    added.append('[archived parent '+key+'] '+row.get('source','')+' '+row.get('licence',''))
                else:added.append('unresolved archived parent '+key)
            refs=list(re.findall(r'n\s*=\s*(\d+)\s+from\s+held\s+round\s*(\d+)',text,re.I))
            refs+=re.findall(r'held n\s*=\s*(\d+)\s+of round\s*(\d+)',text,re.I)
            for count,rnd in dict.fromkeys(refs):
                key=count+'@'+rnd
                if key in held_seen:continue
                held_seen.add(key);row,ledger=self.held_record(int(count),int(rnd))
                if row:
                    added.append('[held parent '+key+'] '+row.get('source','')+' '+row.get('licence','')+' ('+ledger+')')
                else:added.append('unresolved archived parent held '+key)
            if not added:break
            text+=' | '+' | '.join(added)
        return text

    def mark(self, row):
        text=self.text(row,self.s)
        expanded=self.archived_text(text)
        if expanded!=text:
            row=dict(row,source=row.get('source','')+' | expanded recorded parents: '+expanded[len(text):].strip())
        return annotate(row,expanded,self.origins)

    def prepare(self, collector):
        strict = collector.strict_held
        choices = {}
        for folder in (self.w/'candidates', self.w/'clean-candidates'):
            for row in self.table(folder/'take.tsv'):
                n = int(row['n']);path = folder/f'{n}.csv'
                if not path.exists():
                    continue
                row, flag, seeds = self.mark(row)
                if flag == 'unknown':
                    continue
                clean = n in SPECIAL and flag == 'no'
                threshold = self.relaxed[n] if clean else strict[n]
                score = float(row['new'])
                if score >= threshold-1e-10:
                    continue
                rank = (not clean, score)
                if n not in choices or rank < choices[n][0]:
                    choices[n] = rank, path, row, clean
        self.clean_counts = {n for n, item in choices.items() if item[3]}
        collector.held = dict(strict)
        for n in self.clean_counts:
            collector.held[n] = self.relaxed[n]
        selected = self.w/'policy-candidates'
        selected.mkdir(exist_ok=True)
        rows=[]
        for n, (rank, path, row, clean) in sorted(choices.items()):
            with path.open() as stream:
                self.rows_write(selected/f'{n}.csv', list(csv.DictReader(stream)))
            rows.append(dict(row, held=repr(collector.held[n]), gain=repr(collector.held[n]-float(row['new']))))
        temp=selected/'take.tsv.tmp'
        cols=('n','held','new','gain','source','licence','start','polish_gain')
        with temp.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=cols,delimiter='\t',extrasaction='ignore');writer.writeheader();writer.writerows(rows)
        temp.replace(selected/'take.tsv')
        collector.args.own=[str(selected)]

    def peer_allowed(self, row):
        n=int(row['n'])
        return n not in self.clean_counts or self.mark(row)[1]=='no'
