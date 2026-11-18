"""Check whether every retained row carries its recorded areebbb notices inline."""
import pathlib,re,csv,json
W=pathlib.Path(__file__).resolve().parent;csv.field_size_limit(20000000)
for row in csv.DictReader((W.parent/'take.tsv').open(),delimiter='\t'):
 queue=[row['source']+' '+row['licence']];seen=set();found=False;records=[]
 while queue:
  text=queue.pop()
  if 'areebbb/' in text:found=True
  for name in re.findall(r'$DATA/[^\s,;<>"\\]+\.json',text):
   if name in seen:continue
   seen.add(name);p=pathlib.Path(name)
   if not p.exists():continue
   try:j=json.loads(p.read_text())
   except (ValueError,OSError):continue
   t=json.dumps(j);queue.append(t)
   if 'areebbb/' in t:records.append(name)
 result={'n':int(row['n']),'areeb_in_tree':found,'source_inline':'areebbb/' in row['source'],'licence_inline':'areebbb/' in row['licence'],'json_files':len(seen),'matched_records':records}
 print(json.dumps(result),flush=True)
