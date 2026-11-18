"""Apply round29 source rules in imported validators without editing their files."""
def apply():
 import quench_audit as qa
 qa.RULES=[(name,r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8' if name=='r22 745/858 join' else rx) for name,rx in qa.RULES]
