"""Exercise the real share fixtures and pinned ancestry before public intake."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import setup
setup()
from policy import control
control()
from pins import control
control()
from walk import control
control()
from held_boundary import control
control()
from geometry_cache import control
control()
from poses import control
control()
from runtime_control import control
control()
from geometry_cache import flush
flush()
print('CONTROL round34 startup: all passed',flush=True)
