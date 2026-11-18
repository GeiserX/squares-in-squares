"""Reject the excluded roots and preserve the metadata used to select a module."""
import re,json
BANNED=re.compile(r'(?<![A-Za-z0-9])(?:639|691|745|801|858|918|980|981)(?!\d)|squares-verified-best-of-1105|penguin069/squares-joegun-boxed')
def allowed(source,lic):
 return bool(source) and bool(lic) and not lic.startswith(('see ','unresolved')) and not BANNED.search(source+' '+lic)
def allowed_module(m):
 return not re.match(r'^(?:639|691|745|801|858|918|980|981)(?!\d)',m['id']) and allowed(m.get('src',m.get('source','')),m.get('licence',''))
