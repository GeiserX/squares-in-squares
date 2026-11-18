"""Compare the relevant producer row while retaining full byte snapshots."""
import pathlib,csv,io
def same_producer_records(before,after,n):
 if set(before)!=set(after):return False
 for name,body in before.items():
  if body==after[name]:continue
  if pathlib.Path(name).name!='take.tsv':return False
  def row(raw):return next((z for z in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter='\t') if z.get('n')==str(n)),None)
  if row(body)!=row(after[name]):return False
 return True

