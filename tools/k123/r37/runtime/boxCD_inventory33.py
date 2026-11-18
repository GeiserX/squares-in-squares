"""Acknowledge only fully installed immutable pools."""
from pathlib import Path
import json
R=Path.home()/'scratch/squares-k123'
manifest=R/'boxD-pools33.json'
pools=json.load(manifest.open()) if manifest.exists() else []
print(json.dumps([p for p in pools if all((R/n).is_file() for n in [p+'.csv','sources-'+p+'.json','bars-'+p+'.tsv'])]))
