"""Use border's bisected dilation at the same 2.2e-11 clearance."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('border_finesafe28',Path('tools/border/r28/finesafe.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
work=module.work
