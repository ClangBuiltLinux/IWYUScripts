import os
from pathlib import Path
import subprocess
import sys
from typing import List

def warn(msg: str) -> None:
    '''Raises warning message to stderr'''
    print(f"\n\033[01;33mWARNING: {msg}\033[0m", flush=True, file=sys.stderr)

def build(command: List[str], directory: str):
    '''Builds .i file'''
    try:
        os.chdir(directory)
        subprocess.check_call(' '.join(command), shell=True)
    except KeyboardInterrupt:
        warn("Keyboard Interrupt occurred.")
        return False
    except Exception as e:
        warn(f"Unknown Error: {e}")
        return False

def build_check(out: Path) -> bool:
    '''Checks if the linux kernel builds properly'''

    num_cpus = len(os.sched_getaffinity(0))
    try:
        data = ["make", "ARCH=arm", "LLVM=1", "-j", str(num_cpus), "defconfig", out]
        subprocess.check_output(data)
        print("arm works")
        data[1] = "ARCH=arm64"
        subprocess.check_output(data)
        print("arm64 works")
        data[1] = "ARCH=riscv"
        subprocess.check_output(data)
        print("riscv works")
        data[1] = "ARCH=x86"
        subprocess.check_output(data)
        print("x86 works")
        return True

    except subprocess.CalledProcessError:
        warn("WARNING: BUILD ERROR WITH ONE OR MORE ARCHITECTURES")
        return False