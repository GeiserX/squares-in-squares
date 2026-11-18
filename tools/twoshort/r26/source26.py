"""Conservative intake filter. Every accepted input also needs an ancestry walk."""
import re,sys
sys.path.insert(0,'.')
import forensics_policy as FP
BANNED=re.compile(r'(?<![A-Za-z0-9])(?:639|691|745|801|858|918|980|981)(?!\d)|squares-verified-best-of-1105|penguin069/squares-joegun-boxed')
def allowed(source,lic):
 text=source+' '+lic
 if 'sis-certified-union-micro-shrink' in text and not any(t in text.lower() for t in ['per_n.csv','per-n origin','upstream per-n']):return False
 return bool(source) and bool(lic) and not lic.startswith(('see ','unresolved')) and FP.classify_text(source+' '+lic)['status']=='none' and not re.search(r'take-harvest-r22(?:/| n=)(?:639|691|745|858|918)\b|take-forensics-r(?:22|23)(?:/| n=)918\b',source+' '+lic)
def allowed_module(m):
 return allowed(m.get('src',m.get('source','')),m.get('licence',''))

def credited_cells(source,lic):
 if 'sis-certified-union-micro-shrink' not in source+' '+lic:return True
 refs=set(re.findall(r'(?:notebooks/|datasets/|upstream\s+|->\s*)([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)',source))
 refs={r for r in refs if not r.startswith('areebbb/')}
 return bool(refs) and all(r in lic for r in refs)
