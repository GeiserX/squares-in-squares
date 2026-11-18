"""Run Evan Daniel's pk pool (search/packer/pk/tasks.py, MIT) on macOS without editing his clone.

pk/tasks.py reads /proc/loadavg, which macOS lacks. With this directory on PYTHONPATH,
every Python process (the pool dispatcher and its units too) answers that one read from
os.getloadavg(), in the Linux format: "l1 l5 l15 running/total lastpid". running is
the 1-minute load rounded, plus one for the reader itself. Nothing else changes.
"""
import builtins
import io
import os

if not os.path.exists('/proc/loadavg'):
    _open = builtins.open

    def open(file, *args, **kwargs):  # noqa: A001
        if file == '/proc/loadavg':
            l1, l5, l15 = os.getloadavg()
            return io.StringIO(f'{l1:.2f} {l5:.2f} {l15:.2f} {round(l1) + 1}/1000 {os.getpid()}\n')
        return _open(file, *args, **kwargs)

    builtins.open = open
