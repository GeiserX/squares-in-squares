"""Keep each recorded licence term once without dropping attribution text."""
import re
def unique(text):
 return ' | '.join(dict.fromkeys(x.strip() for x in re.split(r'\s*[|;]\s*',text) if x.strip()))
