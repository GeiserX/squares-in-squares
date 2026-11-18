"""Bound a local walk by its macOS physical footprint, including compressed memory."""
import ctypes
import json
import os
import threading
import time


class Usage(ctypes.Structure):
    _fields_ = [('uuid', ctypes.c_ubyte * 16)] + [(f'u{i}', ctypes.c_uint64) for i in range(18)]


lib = ctypes.CDLL('/usr/lib/libproc.dylib')
lib.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
lib.proc_pid_rusage.restype = ctypes.c_int
peak = 0


def footprint():
    data = Usage()
    if lib.proc_pid_rusage(os.getpid(), 2, ctypes.byref(data)):
        raise OSError('proc_pid_rusage failed')
    return data.u7


def start_guard(start, limit=3_200_000_000):
    def check():
        global peak
        while True:
            value = footprint()
            peak = max(peak, value)
            if value >= limit:
                print(json.dumps(dict(start=start, clean=False, capped=False, files=0,
                                      hits=['physical memory limit reached'], physical_peak_bytes=peak)), flush=True)
                os._exit(3)
            time.sleep(0.25)
    threading.Thread(target=check, daemon=True).start()
