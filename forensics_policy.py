"""Separate Samanyu seed descendants from recorded public and original roots."""
import json
import re

RELAXED = {228,459,503,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990}


def classify_text(text):
    text = re.sub(r'Samanyu(?:-dev)?(?:\s+seed)?\s+ancestry:\s*(?:none|no)\b(?:\s*\([^)]*\))?', '', text, flags=re.I)
    text = re.sub(r'no\s+(?:known\s+)?Samanyu(?:-dev)?(?:\s+ancestry)?|Samanyu[- ]free', '', text, flags=re.I)
    seeds = set()
    patterns = [r'n\s*=\s*(\d+)\s+of\s+Samanyu',
                r'Samanyu-dev/squares_in_squares\s*\(donor n\s*=\s*(\d+)\)',
                r'Samanyu[^;\n]{0,110}?seed\s+n\s*=\s*(\d+)']
    for pattern in patterns:
        seeds.update(int(n) for n in re.findall(pattern, text, flags=re.I))
    for group in re.findall(r'Samanyu(?:-dev)?(?:\s+seed)?\s+ancestry:\s*(?:yes\s*;?\s*)?seeds?\s+n\s*=\s*([\d, ]+)', text, flags=re.I):
        seeds.update(int(n) for n in re.findall(r'\d+', group))
    status = 'seeds' if seeds else ('unknown' if re.search(r'\bSamanyu(?:-dev)?\b', text, flags=re.I) else 'none')
    return dict(status=status, seeds=sorted(seeds))


def classify(parts, scratch):
    import forensics_watch
    notices = forensics_watch.ancestry_notices(parts, scratch)
    import forensics_sources
    proofs = [forensics_sources.trace_part(parts[tag], scratch)[1] for tag in ('A','B','C') if tag in parts]
    result = classify_text(json.dumps(parts) + json.dumps(notices) + json.dumps(proofs))
    declared = []
    def visit(value):
        if isinstance(value, dict):
            if 'seed_policy' in value:
                declared.append(value['seed_policy'])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(proofs)
    if any(p['status'] == 'unknown' for p in declared):
        result['status'] = 'unknown'
    elif any(p['status'] == 'seeds' for p in declared):
        result['seeds'] = sorted(set(result['seeds']) | {n for p in declared for n in p['seeds']})
        result['status'] = 'seeds'
    result['root_n'] = sorted({int(r['n']) for r in notices})
    if result['status'] == 'none' and any(r.get('source','').strip() == 'seed merged0' for r in notices):
        result['status'] = 'unknown'
    return result


def label(policy):
    if policy['status'] == 'none':
        return 'Samanyu ancestry: none (recorded public/own roots)'
    if policy['status'] == 'seeds':
        return 'Samanyu ancestry: seeds n=' + ','.join(map(str, policy['seeds'])) + '; Samanyu-dev/squares_in_squares, no licence stated upstream'
    return 'Samanyu ancestry: unresolved; not eligible for publication'


def reference(n, policy, candidate, held22):
    return held22[n] if n in RELAXED and policy['status'] == 'none' else candidate[n]
