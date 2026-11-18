"""Use the current shared walk without changing another lane's tool."""
import importlib,sys
sys.path.insert(0,'.')
import walker30 as quench_walk
importlib.reload(quench_walk)
from walker30 import *

from current_walk29 import configure
configure(quench_walk)

from current_walk29 import configure
configure(quench_walk)
