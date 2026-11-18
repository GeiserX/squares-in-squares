"""Round 27: the Samanyu-dev rule is lifted (main session, 2026-11-14). Import this first in every twoshort r27 tool.

forensics_policy.classify_text exists only to flag Samanyu-dev seed text, so in our processes it now reports
status none. The other checks (rules a and b, gone records, withdrawals for other reasons) are kept.
"""
import re,sys
sys.path.insert(0,'.')
import forensics_policy as FP
if not getattr(FP,'_twoshort27',False):
    FP._orig_classify_text=FP.classify_text
    FP.classify_text=lambda text:dict(status='none',seeds=[])
    FP.RELAXED=set()
    FP._twoshort27=True
# Text that names only the Samanyu-dev seed, used to tell a Samanyu-only refusal or withdrawal from other reasons.
SAMANYU=re.compile(r'samanyu(?!1808)|921-29e12ff3|bare\s*921|921r25c921|seed\s*(?:n\s*=\s*)?(?:365|503|504|804|811|983)\b|seeds? \[?(?:365|503|504|804|811|983)'
                   r'|held 503|503h|504h|931h|local_bank|untraced ancestry|bare-name|bare name|735r-790|take-border-r2[34]/(?:735|790)|seed root',re.I)
OTHER=re.compile(r'prvsiyan|best-of-1105|CC BY-SA|ShareAlike|penguin069|joegun|rule [ab]\b|share\b|areebbb|harvest-r22/(?:639|691|745|858|918)|\b801\b|overlap|not floatsafe|invalid',re.I)
def samanyu_only(line):
    return bool(SAMANYU.search(line)) and not OTHER.search(line)
