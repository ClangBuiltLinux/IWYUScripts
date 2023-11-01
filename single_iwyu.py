import json
import subprocess
import os
import argparse
from pathlib import Path

def main(commands, fixer_path, filter, specific):
    dir = os.path.dirname(os.path.abspath(__file__))
    filter.append(dir + '/filter.imp')
    filter.append(dir + '/symbol.imp')

    file_used = ""
    with open (commands) as file:
        data = json.load(file)
        for part in data:
            if specific not in part['file']: continue
            output = perform_iwyu(fixer_path, part, filters)
            file_used = part["file"]
            break
    with open(file_used, 'r') as file:
        if os.path.exists(file_used[:-1] + 'h'):
            print("WARNING: HEADER POTENTIALLY MODIFIED")
        
        match output:
            case 0:
                for line in file:
                    if 'asm-generic' in line:
                        print(f'''WARNING: ASM-GENERIC PRESENT IN LINE: {line}
                                CONSIDER REMOVING''')
            case 1: 
                print("WARNING: DOES NOT BUILD")
            case 2:
                print("WARNING: NO .i FILE. RUN build_intermediary.py")
                return
            case 3:
                print("WARNING: CHANGES DID NOT LEAD TO REDUCTION IN PREPROCESSING SIZE")

def perform_iwyu(fixer_path, part, filters):

    command = part['command'].split()
    os.chdir(part["directory"])

    orig = command[-1]
    nname = orig[:-1] + 'i'

    try:
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        old_size = int(output.decode().strip().split()[0])
    except: #this has already been tried
        return 2
    
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

    os.system(' '.join(include_command))
    os.system(' '.join(include_command))

    command[-2] = nname
    build_command = command + ['-E']
    subprocess.check_call(' '.join(build_command), shell=True)
    try:
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        new_size = int(output.decode().strip().split()[0])
        if new_size >= old_size:
            print(new_size, old_size)
            return 3
        subprocess.run(f"wc -l ./{nname} >> changes.txt", shell=True)

    except:
        subprocess.run(f"rm ./{nname}", shell=True)
        return 1
    
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
        
        
    except:
        exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This script attempts to automatically refactor headers.")

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
