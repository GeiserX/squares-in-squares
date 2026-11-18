"""Find the lowest source-cleared result and retain valid fallback candidates."""
def first_clean(options,check):
 refused=[]
 for job,receipt,path in sorted(options,key=lambda v:v[1]['new']):
  proof=check(job,path)
  if proof['clean']:return (job,receipt,path),refused
  refused.append((job,proof))
 return None,refused
