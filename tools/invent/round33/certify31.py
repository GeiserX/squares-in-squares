"""Certify a packing with clearance preserved through pandas parsing."""
import csv
import floatsafe,finesafe

def certify(p,n):
 rows=list(csv.DictReader(open(p)))
 assert len(rows)==n
 v=finesafe.work((n,rows))
 if v[1]is None:return None
 gap=min(floatsafe.clearance(v[1]),floatsafe.clearance(floatsafe.via_pandas(v[1])))
 if gap>=2.2e-11:return v
 # A small buffer covers decimal parsing at the bisection boundary.
 for epsilon in floatsafe.EPS:
  repaired=floatsafe.as_float_rows(v[1],epsilon)
  parsed=floatsafe.via_pandas(repaired)
  if min(floatsafe.clearance(repaired),floatsafe.clearance(parsed))<2.21e-11:continue
  score,why=floatsafe.check(n,repaired)
  if why=='ok'and floatsafe.check(n,parsed)[1]=='ok':return n,repaired,score,epsilon
 return None
