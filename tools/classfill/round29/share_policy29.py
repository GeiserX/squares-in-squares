"""Round28 00:19 handoff: share gates apply to fetched public starts only."""
import re
POLICY='r28-own-layouts-exempt-001903'
def public_start(path,source):
 return bool(re.search(r'take-harvest-r\d+/',str(path)) and (re.match(r'\s*(?:public\s+)?[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*::',source) or re.search(r'original source public\s+[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*::',source)))
