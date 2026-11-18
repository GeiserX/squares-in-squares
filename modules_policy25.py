"""Apply the round 25 base bar: the held round 23b file, clean round 24 rows and every live round 25 take."""
import csv
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil

csv.field_size_limit(2**30)
HELD = set()  # round 23b already holds these counts at their clean values
local = Path('$SCRATCH/bounties-squares/take-modules-r24/work/seed-origins24.json')
seed_file = local if local.exists() else Path(__file__).resolve().parent / 'seed-origins24.json'
SEEDS = json.loads(seed_file.read_text()) if seed_file.exists() else {}


@functools.lru_cache(maxsize=32768)
def _origin(source, licence, root):
    text = source + ' ' + licence
    sam = set()
    couzo = set()
    unresolved = set()
    for match in re.finditer(r'n\s*=\s*(\d+)\s+of\s+Samanyu', text, re.I):
        sam.add(int(match[1]))
    for match in re.finditer(r'Samanyu(?:-dev)?[^;|\[\]]{0,110}?(?:seed|donor)\s+n\s*=\s*([\d, ]+)', text, re.I):
        sam.update(map(int, re.findall(r'\d+', match[1])))
    old_seeds = {int(m[1]) for m in re.finditer(r'(\d+)[\w~^.-]*\s*<held:\s*seed merged0', text)}
    if source.strip().startswith('held: seed merged0') and root:
        old_seeds.add(root)
    for n in old_seeds:
        if SEEDS.get(str(n)) == 'samanyu': sam.add(n)
        elif SEEDS.get(str(n)) == 'couzo': couzo.add(n)
        else: unresolved.add(n)
    notes = list(re.finditer(r'Samanyu(?:-dev)?(?: seed)? ancestry\s*:\s*(no|none|yes)\b', licence, re.I))
    explicit_no = bool(notes and notes[-1][1].lower() in ('no','none'))
    if not sam and not explicit_no:
        if 'seed merged0' in text and not old_seeds:
            unresolved.add(root or 0)
        if re.search(r'held packing of n\s*=', text) and not old_seeds:
            unresolved.add(root or 0)
        if 'Samanyu' in text and not old_seeds:
            unresolved.add(root or 0)
    if explicit_no and sam:
        unresolved.update(sam)
    status = 'unknown' if unresolved else ('samanyu' if sam else 'none')
    return dict(status=status, seeds=sorted(sam), couzo=sorted(couzo), unresolved=sorted(unresolved))


def piece(q):
    match = re.match(r'(\d+)', str(q.get('id', '')))
    root = int(match[1]) if match else int(q.get('n', 0) or 0)
    return _origin(str(q.get('src', q.get('source', ''))), str(q.get('licence', '')), root)


def ancestry(record):
    parts = record.get('modules')
    if not parts:
        return piece(record)
    records = [piece(p) for p in parts]
    sam = sorted({n for r in records for n in r['seeds']})
    couzo = sorted({n for r in records for n in r['couzo']})
    unknown = sorted({n for r in records for n in r['unresolved']})
    return dict(status='unknown' if any(r['status']=='unknown' for r in records) else ('samanyu' if sam else 'none'), seeds=sam, couzo=couzo, unresolved=unknown)


def notice(a):
    if a['status'] == 'none':
        out = 'Samanyu-dev seed ancestry: no (recorded source chain)'
        if a['couzo']: out += '; Couzo MIT seed n=' + ','.join(map(str,a['couzo']))
        return out
    if a['status'] == 'samanyu':
        return 'Samanyu-dev seed ancestry: yes, seed n=' + ','.join(map(str,a['seeds']))
    return 'Samanyu-dev seed ancestry: unresolved, held donor n=' + ','.join(map(str,a['unresolved']))


def bind(c):
    def effective():
        rows = list(csv.DictReader(open('ship/details.csv')))
        r22 = {int(r['n']): float(r['score']) for r in csv.DictReader(open('ship/details-r22.csv'))}
        for r in rows:
            n=int(r['n'])
            if n in HELD:
                r['score']=repr(r22[n]);r['L']=repr((1+r22[n])*math.sqrt(n))
        return rows

    def comparisons(rows):
        best={int(r['n']):float(r['score']) for r in rows}
        dirs=[]
        Path('policy-beat').mkdir(exist_ok=True)
        from modules_sources24 import clean_text
        for d in sorted(list(c['ROOT'].glob('take-*-r24')) + list(c['ROOT'].glob('take-*-r25'))):
            if d==c['TAKE'] or not (d/'take.tsv').exists():continue
            eligible=[]
            for r in csv.DictReader((d/'take.tsv').open(),delimiter='\t'):
                if not r.get('n','').isdigit() or not r.get('new'):continue
                n=int(r['n'])
                if d.name.endswith('-r24') and (piece(r)['status']=='samanyu' or not clean_text(r.get('source','')+' '+r.get('licence',''))):continue
                best[n]=min(best[n],float(r['new']));eligible.append(dict(n=n,new=r['new']))
            out=Path('policy-beat')/d.name;out.mkdir(exist_ok=True)
            with (out/'take.tsv').open('w',newline='') as h:
                w=csv.DictWriter(h,['n','new'],delimiter='\t');w.writeheader();w.writerows(eligible)
            dirs.append(str(out))
        return best,dirs

    def refresh_bar():
        rows=effective();best,_=comparisons(rows)
        with open('ship/details-effective.csv','w',newline='') as h:
            w=csv.DictWriter(h,rows[0].keys());w.writeheader();w.writerows(rows)
        with open('bar.csv.tmp','w',newline='') as h:
            w=csv.DictWriter(h,rows[0].keys());w.writeheader()
            for r in rows:
                n=int(r['n']);r.update(score=repr(best[n]),L=repr((1+best[n])*math.sqrt(n)));w.writerow(r)
        os.replace('bar.csv.tmp','bar.csv');c['rsync']('bar.csv',c['REMOTE']+'bar.csv')

    def publish_completed():
        import sys
        sys.path.insert(0,str(c['LANE']))
        import modules, floatsafe
        from modules_sources24 import normalize_record,clean_record
        for p in Path('boxD-qd').glob('*.done'):
            cp=p.with_suffix('.csv');jp=p.with_suffix('.json')
            if not cp.exists() or not jp.exists():continue
            j=normalize_record(json.loads(jp.read_text()))
            if not clean_record(j) or ancestry(j)['status']!='none':continue
            jp.write_text(json.dumps(j));shutil.copy2(cp,Path('cand',cp.name));shutil.copy2(jp,Path('cand',jp.name))
        rows=effective();best,beat=comparisons(rows)
        with open('ship/details-effective.csv','w',newline='') as h:
            w=csv.DictWriter(h,rows[0].keys());w.writeheader();w.writerows(rows)
        Path('publish').mkdir(exist_ok=True)
        for p in Path('publish').iterdir():p.unlink()
        for p in Path('cand').glob('*.csv'):
            jp=p.with_suffix('.json');j=normalize_record(json.loads(jp.read_text()));n=j['n']
            if ancestry(j)['status']!='none' or not clean_record(j):continue
            if c['bounding_score'](p,n)<best[n]-5e-11:
                shutil.copy2(p,Path('publish',p.name));Path('publish',jp.name).write_text(json.dumps(j))
        before=(c['TAKE']/'take.tsv').read_text() if (c['TAKE']/'take.tsv').exists() else ''
        original=floatsafe.work;floatsafe.work=c['certificate_cache'](original)
        from contextlib import redirect_stdout
        try:
            with open('logs/take.out','w') as h:
                with redirect_stdout(h):modules.cmd_take(['ship/details-effective.csv',str(c['TAKE']),'publish','--beat',*beat])
        finally:floatsafe.work=original
        meta={}
        for line in Path('logs/take.out').read_text().splitlines():
            if line.startswith('keep '):
                bits=line.split();meta[bits[1]]=json.loads(Path(bits[-1]).with_suffix('.json').read_text())
        retained=list(csv.DictReader((c['TAKE']/'take.tsv').open(),delimiter='\t'))
        for r in retained:
            a=ancestry(meta[r['n']]);assert a['status']=='none'
            r['licence']+='; '+notice(a)
            r['source']+='; certified-file fq quench on boxD; round 25 source rule, base gate/cand-round23-1113b plus clean round 24 rows'
            if int(r['n']) in HELD:r['source']+='; no-Samanyu comparison base gate/cand-round22-1113b/details.csv'
        with (c['TAKE']/'take.tsv.tmp').open('w',newline='') as h:
            w=csv.DictWriter(h,['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(retained)
        os.replace(c['TAKE']/'take.tsv.tmp',c['TAKE']/'take.tsv')
        if before!=(c['TAKE']/'take.tsv').read_text():
            for r in retained:
                if r['n']+'\t'+r['held']+'\t'+r['new']+'\t' in before:continue
                with (c['ROOT']/'handoff-r25.log').open('a') as h:h.write(f'{c["stamp"]()} modules -> all: certified no-Samanyu n={r["n"]}, score={r["new"]}, policy gain={r["gain"]}; box quench complete, {c["TAKE"]}/{r["n"]}.csv\n')
    return refresh_bar,publish_completed
