"""Keep explicit source edges and omit stored walker diagnostics from recursive walks."""
import json,re,pathlib,sys
_READER=None

def reader_records():
 global _READER
 if _READER is None:
  sys.path.insert(0,"tools/harvest30")
  import reader_records as module
  module.W=pathlib.Path(__file__).resolve().parent/"reader-work"
  _READER=module
 return _READER

def reset_records():reader_records().EXTRA_PINS.clear()
def extra_records():return reader_records().EXTRA_PINS


def pruned(value):
 if isinstance(value,dict):
  source=value.get('source')
  explicit=isinstance(source,str) and bool(re.search(r'take-[a-z0-9-]+-r\d+/[^\s;,]+\.csv',source))
  return {k:pruned(v) for k,v in value.items() if not(k=='walk' and explicit)}
 if isinstance(value,list):return [pruned(v) for v in value]
 return value

def wrap(reader):
 def read(path,n):
  text=reader(path,n)
  try:value=json.loads(text)
  except ValueError:return text
  return json.dumps(pruned(reader_records().transform(value)))
 return read

def controls():
 v={'source':'own construction, take-test-r30/near/640-a.csv','walk':{'missing':['take-other-r1/missing.csv']},'licence':'our own construction'}
 assert 'walk' not in pruned(v) and pruned(v)['source']==v['source']
 assert pruned({'source':'unresolved root','walk':{'source':'actual root'}})['walk']
 assert pruned({'source':v['source'],'parent':'take-parent-r30/640.csv'})['parent']=='take-parent-r30/640.csv'
 print('CONTROL explicit source edge preserved; stored walk omitted; unresolved-source evidence retained',flush=True)

if __name__=='__main__':controls()
