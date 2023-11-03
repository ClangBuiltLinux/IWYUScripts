'''Calls include-what-you-use on a kernel file'''
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

def main(commands, fixer_path, filters, specific):
    '''Chooses a specific file to call perform_iwyu on'''

    current_dir = Path(__file__).resolve().parent
    filters += [Path(current_dir, 'filter.imp'), Path(current_dir, 'symbol.imp')]

    with open (commands, encoding='utf-8') as file:
        for part in json.load(file):
            if specific not in part['file']:
                continue
            perform_iwyu(fixer_path, part, filters)
            break
        else:
            print("WARNING: NO FILE WITH IDENTIFIER FOUND", file=sys.stderr)

def linecount(filename):
    '''Counts the number of lines in a file'''

    with filename.open(encoding='utf-8') as file:
        for count, line in enumerate(file):
            pass
    return count + 1

def perform_iwyu(fixer_path, part, filters):
    '''Given a path, a clang build command and filters, this function 
    calls include-what-you-use and validates the efficacy of the changes'''

    command = part['command'].split()
    os.chdir(part["directory"])

    for i, statement in enumerate(command):
        if statement == '-o' and i != len(command)-1:
            outfile = Path(command[i+1])
            break
    else:
        print("WARNING: NO .o FILE FOUND IN COMMAND", file=sys.stderr)
    preprocess_file = outfile.with_suffix('.i')

    if not preprocess_file.exists():
        print("WARNING: NO .i FILE. RUN build_intermediary.py", file=sys.stderr)
        return False

    old_size = linecount(preprocess_file)

    iwyu_opts = [
    '--no_default_mappings',
    '--max_line_length=30',
    '--no_fwd_decls',
    '--prefix_header_includes=keep',
    ]

    for imp_file in filters:
        iwyu_opts.append(f"--mapping_file={imp_file}")

    iwyu_cmd = ['include-what-you-use'] + command[1:]
    iwyu_cmd += [flag for opt in iwyu_opts for flag in ('-Xiwyu', opt)]
    iwyu_cmd += [f'2>&1 | {fixer_path}']

    try:
        subprocess.check_call(' '.join(iwyu_cmd), shell=True)
        subprocess.check_call(' '.join(iwyu_cmd), shell=True)

    except subprocess.CalledProcessError:
        print("WARNING: IWYU FAILED TO RUN", file=sys.stderr)
        return False

    if outfile.with_suffix('.h').exists():
        print("WARNING: HEADER POTENTIALLY MODIFIED", file=sys.stderr)

    command[-2] = str(preprocess_file)
    subprocess.check_call(command + ['-E'])

    try:
        if linecount(preprocess_file) >= old_size:
            print("WARNING: CHANGES LEAD TO NO REDUCTION IN PREPROCESSING SIZE", file=sys.stderr)
            return False

    except subprocess.CalledProcessError:
        if preprocess_file:
            print("WARNING: DOES NOT BUILD", file=sys.stderr)
        return False

    with open(outfile.with_suffix('.c'), encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if 'asm-generic' in line:
                print(f'''WARNING: ASM-GENERIC PRESENT IN LINE: {line}
                        CONSIDER REMOVING''', file=sys.stderr)

    if build_check(outfile):
        return False

    return True


def build_check(out):
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
        print("WARNING: BUILD ERROR WITH ONE OR MORE ARCHITECTURES", file=sys.stderr)
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''This script attempts to automatically refactor a
                                    include list without touching the headers themselves.''')

    parser.add_argument('-c', '--commands', type=Path, required=True,
                        help='Path to compile_commands.json')
    parser.add_argument('-f', '--fixer_path', type=Path, required=True,
                        help='Path to the fix_includes.py')
    parser.add_argument('-s', '--specific_command', required=True,
                        help='Name of the .c file to refactor')
    parser.add_argument('-fi', '--filters', nargs='*',
                        help='List of additional filters')

    args = parser.parse_args()
    args.filters = [] if not args.filters else args.filters
    main(args.commands, args.fixer_path, args.filters, args.specific_command)
