'''Utility functions used in other IWYU Scripts'''
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List
import json
import itertools

def warn(msg: str) -> None:
    '''Raises warning message to stderr'''
    print(f"\n\033[01;33mWARNING: {msg}\033[0m", flush=True, file=sys.stderr)

def build(command: List[str], directory: str):
    '''Runs a command as a subprocess to build a .i file in the target directory'''
    os.chdir(directory)
    try:
        subprocess.check_call(' '.join(command), shell=True)
    except KeyboardInterrupt:
        warn("Keyboard Interrupt occurred.")
        return False
    except Exception as e:
        warn(f"Unknown Error: {e}")
        return False
    return True

def build_check(target: Path) -> bool:
    '''Checks if the linux kernel builds properly'''

    num_cpus = len(os.sched_getaffinity(0))
    shutil.copy('.config', '.tmp.config')
    try:
        print("Building arm")
        data = ["make", "ARCH=arm", "LLVM=1", "-j", str(num_cpus), "defconfig", target]
        subprocess.check_output(data)
        print("arm works")

        print("Building arm64")
        data[1] = "ARCH=arm64"
        subprocess.check_output(data)
        print("arm64 works")

        print("Building riscv")
        data[1] = "ARCH=riscv"
        subprocess.check_output(data)
        print("riscv works")

        print("Building x86")
        data[1] = "ARCH=x86"
        subprocess.check_output(data)
        print("x86 works")

    except subprocess.CalledProcessError:
        warn("WARNING: BUILD ERROR WITH ONE OR MORE ARCHITECTURES")
        return False

    finally:
        shutil.copy('.tmp.config', '.config')
        Path.unlink('.tmp.config')

    return True

def linecount(file_path: Path) -> int:
    '''Returns the number of lines in a file'''
    return len(file_path.open().readlines())

def run_cleaned_iwyu (iwyu: List[str], cleaner: List[str],
                      fix_includes: List[str], debug: bool) -> bool:
    '''Spawns subprocesses to run the IWYU command,
    remove the quotes, and transform the original file'''
    try:
        _, err = subprocess.Popen(iwyu, stderr=subprocess.PIPE, text=True).communicate()
        out, _ = subprocess.Popen(cleaner, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True).communicate(input=err)
        if debug:
            print("debug")
            print(out)
        change, _ = subprocess.Popen(fix_includes, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True).communicate(out)
    except subprocess.CalledProcessError:
        warn("IWYU FAILED TO RUN")
        return False

    print(change)

    if "IWYU edited 0 files on your behalf." in change:
        return False
    return True

def perform_iwyu(fixer_path: Path, part: json, filters: List[Path],
                 current_path: Path, debug: bool = False) -> bool:
    '''Given a path, a clang build command and filters, this function 
    calls include-what-you-use and validates the efficacy of the changes'''

    command = part['command'].split()
    os.chdir(part["directory"])

    for i, statement in enumerate(itertools.islice(command, len(command) - 1)):
        if statement == '-o':
            outfile = Path(command[i + 1])
            found_index = i + 1
            break
    else:
        warn("NO .o FILE FOUND IN COMMAND")
        return False

    preprocess_file = outfile.with_suffix('.i')

    new_commands = command + ['-E']
    new_commands[found_index] = str(preprocess_file)
    if not build(new_commands, part["directory"]):
        warn("Build Failure")
        return False

    old_size = linecount(preprocess_file)
    preprocess_file.unlink()

    iwyu_opts = [
    '--no_default_mappings',
    f'--max_line_length={3000 if debug else 30}',
    '--no_fwd_decls',
    '--prefix_header_includes=keep',
    ]

    for imp_file in filters:
        iwyu_opts.append(f"--mapping_file={imp_file}")

    iwyu_cmd = ['include-what-you-use'] + command[1:]
    iwyu_cmd += [flag for opt in iwyu_opts for flag in ('-Xiwyu', opt)]
    quote_cleaner = ['python', f'{current_path}/lib/remove_quotes.py']
    fix_includes = [f'{fixer_path}', '--noreorder']

    # Runs twice to fix include list once and a second time to catch bad includes
    if not run_cleaned_iwyu(iwyu_cmd, quote_cleaner, fix_includes, debug=debug):
        warn("NO CHANGES")
        return False

    if run_cleaned_iwyu(iwyu_cmd, quote_cleaner, fix_includes, debug=debug):
        warn("X-MACRO OR HEADER MODIFICATION MAY BE PRESENT ")

    if outfile.with_suffix('.h').exists():
        warn("HEADER POTENTIALLY MODIFIED")

    command[-2] = str(preprocess_file)
    subprocess.check_call(command + ['-E'])
    try:
        new_size = linecount(preprocess_file)
        if new_size >= old_size:
            warn("CHANGES LEAD TO NO REDUCTION IN PREPROCESSING SIZE")
            warn(f"OLD SIZE: {old_size} vs NEW SIZE: {new_size}")
            return False

    except subprocess.CalledProcessError:
        if preprocess_file:
            warn("DOES NOT BUILD")
        return False

    finally:
        preprocess_file.unlink(missing_ok=True)

    with open(outfile.with_suffix('.c'), encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if 'asm-generic' in line:
                warn(f'''ASM-GENERIC PRESENT IN LINE: {line}
                        CONSIDER REMOVING''')

    if not build_check(outfile):
        return False

    print(f"Preprocessed size shrank from: {old_size} lines to {new_size} lines")
    return True
