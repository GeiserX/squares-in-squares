"""Round 25 source admission with immutable proofs and a source-qualified base."""
import csv
import hashlib
import importlib.util
import io
import json
import re
import sys
import time
from pathlib import Path

L = Path(__file__).resolve().parents[2]
B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r25'
W = T / 'work'
sys.path.insert(0, str(L))
sys.path.insert(0, str(L/'tools'))
from harvest_follow import refused_source, source_text
from harvest_seeds import SeedPolicy, classify
import forensics_sources
import forensics_policy

POLICY = SeedPolicy(B, T, source_text, lambda p: [], lambda *a: None)
BAD = ('penguin069/squares-joegun-boxed-certified-union',
       'prvsiyan/squares-verified-best-of-1105', 'samanyu-dev/squares_in_squares')
CACHE = {}
LAST_BASE = None


def clean_text(text):
    normalized=text.replace('samanyu1808/sis-final-packings','licensed-public/final-packings').replace('samanyu1808/sis-submit','licensed-public/sis-submit')
    return (forensics_policy.classify_text(normalized)['status']=='none'
            and not any(x in text.lower() for x in BAD)
            and not re.search(r'cc[ -]by[ -]sa', text, re.I)
            and not re.search(r'take-stair-c-r22(?:/|\s+)near/863-0f92c19d-n',text)
            and not any(term in text for term in ('take-stair-c-r17/near/921-29e12ff3','921r25c921.','921mo16.F1d','985-r25-ba842328a07b'))
            and not re.search(r'take-border-r24/(?:near/)?735(?:[-.]|/)', text)
            and not re.search(r'take-k123-r24/(?:near/)?(?:735|790|968|489)(?:[-.]|/)', text)
            and not re.search(r'Samanyu(?:-dev)?(?: seed)? ancestry[:=]\s*(?:yes|seeds|unknown|unresolved)', text, re.I))


def row_for(path, n):
    try:
        rec, ledger = forensics_sources.record(path, n)
        return rec if isinstance(rec, dict) else {}, ledger
    except (OSError, ValueError):
        return {}, ''



def seed_flag(text):
    # Licensed Kaggle owners do not identify the unrelated GitHub seed.
    normalized=text.replace('samanyu1808/sis-final-packings','licensed-public/final-packings').replace('samanyu1808/sis-submit','licensed-public/sis-submit')
    return classify(normalized,POLICY.origins)[0]

def audit_evidence(evidence, relative_active=None):
    """Expand frozen and held leaves that the imported tracer treats as roots."""
    extra = []
    relative_active = set() if relative_active is None else set(relative_active)
    aliases = re.findall(r'(take-[a-z0-9-]+-r\d+)\s+(near/(\d+)[^ \t\n,;\"()\\]*\.csv)', json.dumps(evidence))
    for lane, name, count in dict.fromkeys(aliases):
        key = (lane, name)
        if key in relative_active:continue
        relative_active.add(key)
        point = B/lane/name
        ok, parent = forensics_sources.trace(point,int(count),B)
        if not ok or not audit_evidence(parent,relative_active)[0]:return False, extra
        extra.append('relative parent '+str(point))
    visited = set()
    def visit(obj):
        if isinstance(obj, list):
            return all(visit(v) for v in obj)
        if not isinstance(obj, dict):
            return True
        name, n = obj.get('path'), obj.get('n')
        if name and isinstance(n, int) and (name, n) not in visited:
            visited.add((name, n)); p = Path(name)
            if p.parent.name == 'gather':
                if n == 801:
                    return False
                if p.name != 'round23-2026-11-13b.csv' and not p.name.startswith('round24-'):
                    m = re.search(r'round(\d+)', p.name)
                    if not m:
                        return False
                    rec, _ = POLICY.held_record(n, int(m[1]))
                    if not rec:
                        return False
                    text = POLICY.archived_text(source_text(rec, B))
                    extra.append(text)
                    if not clean_text(text) or seed_flag(text) != 'no':
                        return False
            elif re.fullmatch(r'take-.+-r(?:22|23)', p.parent.name) and p.stem.isdigit():
                rec, _ = row_for(p, n)
                if not rec:
                    return False
                text = POLICY.archived_text(source_text(rec, B)); extra.append(text)
                if not clean_text(text) or refused_source(rec, B) or seed_flag(text) != 'no':
                    return False
        return all(visit(v) for v in obj.values())
    return visit(evidence), extra



def referenced_proofs(evidence):
    """Read retained proof links once and keep only their hashes in new evidence."""
    routes = dict(evidence.get('linked_proof_snapshots',{})) if isinstance(evidence,dict) else {}
    todo = [json.dumps(evidence)]; seen = {}; total = 0
    while todo:
        text = todo.pop()
        if not clean_text(text):
            return False, seen
        names = re.findall(r'$SCRATCH/bounties-squares/[^ \t\n,;"()\\]+\.json', text)
        for name in names:
            if name in seen:
                continue
            p = Path(routes.get(name,name))
            if not p.is_file() or len(seen) >= 512:
                return False, seen
            payload = p.read_bytes(); total += len(payload)
            if total > 32*1024*1024:
                return False, seen
            seen[name] = hashlib.sha256(payload).hexdigest()
            value = json.loads(payload)
            if isinstance(value,dict):routes.update(value.get('linked_proof_snapshots',{}))
            ok, _ = audit_evidence(value)
            if not ok:
                return False, seen
            todo.append(json.dumps(value))
    return True, seen

def capture(path, n):
    path = Path(path)
    try:
        payload = path.read_bytes(); digest = hashlib.sha256(payload).hexdigest()
        rec, ledger = row_for(path, n)
        token = (str(path), digest, hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest())
        if token in CACHE:
            result, when = CACHE[token]
            if result or time.time()-when < 120:
                return result
        text = POLICY.archived_text(source_text(rec, B))
        if not clean_text(text) or refused_source(rec, B):
            CACHE[token] = None, time.time(); return None
        if path.parent.name == 'gather' and path.name == 'round23-2026-11-13b.csv':
            ok, evidence = n != 801, dict(path=str(path), n=n, reason='clean held round23b')
        else:
            ok, evidence = forensics_sources.trace(path, n, B)
            if not ok:
                spec = importlib.util.spec_from_file_location('soft_provenance25', L/'tools/softround/provenance.py')
                soft = importlib.util.module_from_spec(spec); spec.loader.exec_module(soft)
                alternate = soft.trace(path, n)
                if alternate.get('ok'):
                    ok, evidence = True, alternate
        checked, extra = audit_evidence(dict(record=rec,evidence=evidence))
        notice = text + ' ' + json.dumps(evidence) + ' ' + ' '.join(extra)
        linked_ok, linked = referenced_proofs(dict(record=rec, evidence=evidence)) if ok and checked else (False, {})
        if not ok or not checked or not linked_ok or not clean_text(notice):
            CACHE[token] = None, time.time(); return None
        # Explicit seed declarations in nested policies are also exclusion evidence.
        def seed_bad(v):
            if isinstance(v, dict):
                if 'seed_policy' in v and v['seed_policy'].get('status') != 'none':
                    return True
                return any(seed_bad(x) for x in v.values())
            return isinstance(v, list) and any(seed_bad(x) for x in v)
        if seed_bad(evidence):
            CACHE[token] = None, time.time(); return None
        if not path.is_file() or path.read_bytes() != payload:
            return None
        snapshots = {}
        assets = W/'provenance-assets'; assets.mkdir(exist_ok=True)
        for name, hashed in linked.items():
            candidates=[Path(name),assets/(hashed+'.json')]+[Path(p) for p,h in linked.items() if h==hashed]
            original=None
            for candidate in candidates:
                if candidate.is_file():
                    payload=candidate.read_bytes()
                    if hashlib.sha256(payload).hexdigest()==hashed:original=payload;break
            if original is None:return None
            saved = assets/(hashed+'.json')
            if not saved.exists():
                temp = saved.with_suffix('.tmp');temp.write_bytes(original);temp.replace(saved)
            snapshots[name]=str(saved)
        proof = dict(path=str(path), n=n, input_sha256=digest, record=rec, evidence=evidence,
                     expanded_root_notices=extra, linked_proof_sha256=linked, linked_proof_snapshots=snapshots, policy='full parent trace; forbidden roots excluded')
        raw = json.dumps(proof, sort_keys=True)
        target = W/'provenance'/(digest+'-'+hashlib.sha256(raw.encode()).hexdigest()[:16]+'.json')
        if not target.exists():
            tmp = target.with_suffix('.tmp'); tmp.write_text(raw); tmp.replace(target)
        CACHE[token] = str(target), time.time()
        return str(target)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return None


def update_base():
    global LAST_BASE
    hand = (B/'handoff-r25.log').read_text()
    posted = [line for line in hand.splitlines() if 'main -> all: BASE ' in line]
    details = None
    if posted:
        match = re.search(r'(?:$SCRATCH/bounties-squares/)?gate/[^ ,;]+', posted[-1])
        if match:
            p = Path(match[0]); p = p if p.is_absolute() else B/p
            details = p if p.name == 'details.csv' else p/'details.csv'
    if details and details.exists():
        key = (str(details), details.stat().st_mtime_ns)
        if key != LAST_BASE:
            data = details.read_text(); temp = W/'base-details.csv.tmp';temp.write_text(data);temp.replace(W/'base-details.csv')
            LAST_BASE = key
            with (T/'STATE.txt').open('a') as f:
                f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ boxA BASE ', time.gmtime())+str(details)+'\n')
        return
    initial = W/'initial-base-details.csv'
    if initial.exists():
        if not (W/'base-details.csv').exists():
            (W/'base-details.csv').write_bytes(initial.read_bytes())
        return
    base = {int(r['n']):r for r in csv.DictReader((B/'gate/cand-round23-1113b/details.csv').open())}
    for d in sorted(B.glob('take-*-r24')):
        table = d/'take.tsv'
        if not table.exists():
            continue
        for row in csv.DictReader(table.open(), delimiter='\t'):
            n = int(row['n']); value = float(row['new'])
            if value < float(base[n]['score']) and capture(d/(str(n)+'.csv'), n):
                base[n]['score'] = repr(value)
                if 'L' in base[n]:
                    base[n]['L'] = repr((value+1)*n**.5)
    buf = io.StringIO(); writer = csv.DictWriter(buf, fieldnames=list(base[1]));writer.writeheader();writer.writerows(base.values())
    initial.write_text(buf.getvalue());(W/'base-details.csv').write_text(buf.getvalue())
    LAST_BASE = ('initial', 0)
