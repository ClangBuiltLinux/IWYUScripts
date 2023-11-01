import json
import subprocess
import os
import argparse
import sys
from pathlib import Path

def main(commands, fixer_path, filter, specific):
    dir = os.path.dirname(os.path.abspath(__file__))
    filter.append(dir + '/filter.imp')
    filter.append(dir + '/symbol.imp')

    with open (commands) as file:
        data = json.load(file)
        for part in data:
            if specific not in part['file']: continue
            perform_iwyu(fixer_path, part, filters)
            break

def perform_iwyu(fixer_path, part, filters):

    command = part['command'].split()
    os.chdir(part["directory"])

    for i in range(len(command)):
        if command[i] == '-o':
            orig = command[i+1]
            break
    nname = orig[:-1] + 'i'

    try:
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        old_size = int(output.decode().strip().split()[0])
    except: #this has already been tried
        print("WARNING: NO .i FILE. RUN build_intermediary.py", file=sys.stderr)
        return 1
    
    include = [
        "include-what-you-use",
        "-Xiwyu",
        "--no_default_mappings",
        "-Xiwyu",
        "--max_line_length=30",
        "-Xiwyu",
        "--no_fwd_decls",
        "-Xiwyu",
        "--prefix_header_includes=keep",
    ]
    for filter in filters:
        include.append("-Xiwyu")
        include.append(f"--mapping_file={filter}")
    include_command = include + command[1:] + [f'2>&1 | {fixer_path}']

    #two passes

    subprocess.run(' '.join(include_command))
    subprocess.run(' '.join(include_command))

    if os.path.exists(orig[:-1] + 'h'):
        print("WARNING: HEADER POTENTIALLY MODIFIED", file=sys.stderr)

    command[-2] = nname
    build_command = command + ['-E']
    subprocess.check_call(' '.join(build_command), shell=True)

    try:
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        new_size = int(output.decode().strip().split()[0])
        if new_size >= old_size:
            print("WARNING: CHANGES DID NOT LEAD TO REDUCTION IN PREPROCESSING SIZE", file=sys.stderr)
            return 1
        subprocess.run(f"wc -l ./{nname} >> changes.txt", shell=True)

    except:
        subprocess.run(f"rm ./{nname}", shell=True)
        print("WARNING: DOES NOT BUILD", file=sys.stderr)
        return 1

    with open(orig, 'r') as file:
        for line in file:
            if 'asm-generic' in line:
                print(f'''WARNING: ASM-GENERIC PRESENT IN LINE: {line}
                        CONSIDER REMOVING''', file=sys.stderr)
                
    if build_check(): return 1

    return 0


def build_check():
    try:
        subprocess.check_output("make ARCH=arm LLVM=1 -j 128 defconfig all", shell=True)
        print("arm works")
        # subprocess.check_output("make ARCH=arm64 LLVM=1 -j 128 defconfig all", shell=True)
        # print("arm64 works")
        # subprocess.check_output("make ARCH=riscv LLVM=1 -j 128 defconfig all", shell=True)
        # print("riscv works")
        subprocess.check_output("make LLVM=1 -j 128 defconfig all", shell=True)
        print("x86 works")
        return 0
        
    except:
        return 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''This script attempts to automatically refactor one 
                                    include list without touching the headers themselves.''')

    parser.add_argument('commands', type=Path, help='Path to compile_commands.json')
    parser.add_argument('fixer_path', type=Path, help='Path to the fix_includes.py')
    parser.add_argument('specific_command', help='Name of the .c file to refactor')
    parser.add_argument('filters', nargs='*', help='List of additional filters')

    args = parser.parse_args()

    commands = args.commands
    fixer_path = args.fixer_path
    filters = args.filters
    specific = args.specific_command

    main(commands, fixer_path, filters, specific)
