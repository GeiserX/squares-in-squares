"""Resolve a retired public certifier only from an explicit published donor credit."""
import csv,pathlib,re
S=pathlib.Path('$SCRATCH/bounties-squares')
R=pathlib.Path('results')
def resolve(source,terms,record,reference,count):
 relative=str(reference).removeprefix(str(S)+'/')
 if not re.fullmatch(r'take-(?:harvest|polish)-r\d+/'+str(count)+r'\.csv',relative):return None
 path=pathlib.Path(record.split(' n=',1)[0]);which=re.search(r'\bn=(\d+)\b',record)
 if path.parent!=R or not re.fullmatch(r'round\d+-best-[\w-]+\.tsv',path.name)or not which:return None
 try:
  row=next(v for v in csv.DictReader(open(path),delimiter='\t')if int(v['n'])==int(which[1]))
 except (OSError,ValueError,KeyError,StopIteration):return None
 if not source.startswith(row['source'])or not terms.startswith(row['licence'])or relative not in row['source']:return None
 match=re.search(r'archived public donor n\s*=\s*'+str(count)+r':\s*([^|]+)',row['source'])
 if not match:return None
 result=match[1].strip()
 if 'Upstream per-n records:'in row['source']:result+='; Upstream per-n records: '+row['source'].split('Upstream per-n records:',1)[1]
 result+='; exact archived donor credit in '+str(path)+' row '+which[1]
 return result,row['licence'],str(path)+' n='+str(count)
