"""Hold a Windows "system required" request (no idle sleep) while process PID is alive; the request ends with this process.
It changes no power setting (same API media players use). A closed lid or a manual Sleep still sleeps.
Usage: python -I tools/keep_awake_while.py <pid> [max_hours]"""
import ctypes
import sys
import time

ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
pid, max_h = int(sys.argv[1]), float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
k32 = ctypes.windll.kernel32


def alive(p):
    h = k32.OpenProcess(0x1000, False, p)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return code.value == 259                        # STILL_ACTIVE


k32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
t0 = time.time()
try:
    while alive(pid) and time.time() - t0 < max_h * 3600:
        time.sleep(60)
finally:
    k32.SetThreadExecutionState(ES_CONTINUOUS)
print(f"released after {(time.time() - t0) / 3600:.2f} h (pid {pid} alive: {alive(pid)})")
