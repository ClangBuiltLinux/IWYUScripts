#!/usr/bin/env python
'''Calls include-what-you-use on a kernel .c file'''

import argparse
import itertools
import json
import os
from pathlib import Path
import subprocess
from typing import List

from lib.utils import build, build_check, warn

def main(commands: Path, fixer_path: Path, filters: List[Path], specific: str):
    '''Chooses a specific file to call perform_iwyu on'''

    current_dir = Path(__file__).resolve().parent
    filters += [Path(current_dir, 'filter.imp'), Path(current_dir, 'symbol.imp')]

    with open(commands, encoding='utf-8') as file:
        eligible = [x for x in json.load(file) if specific in x['file']]
        if len(eligible) == 0:
            warn("NO FILE WITH IDENTIFIER FOUND")
        for part in eligible:
            perform_iwyu(fixer_path, part, filters, current_dir)

def linecount(file_path: Path) -> int:
    '''Returns the number of lines in a file'''
    return len(file_path.open().readlines())

def run_cleaned_iwyu (iwyu: List[str], cleaner: List[str], fix_includes: List[str]) -> bool:
    '''Spawns subprocesses to run the IWYU command,
    remove the quotes, and transform the original file'''
    try:
        _, err = subprocess.Popen(iwyu, stderr=subprocess.PIPE, text=True).communicate()
        out, _ = subprocess.Popen(cleaner, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True).communicate(input=err)
        subprocess.Popen(fix_includes, stdin=subprocess.PIPE, text=True).communicate(out)
    except subprocess.CalledProcessError:
        warn("IWYU FAILED TO RUN")
        return False
    return True

def perform_iwyu(fixer_path: Path, part: json, filters: List[Path], current_path: Path) -> bool:
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
    Path.unlink(preprocess_file)

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
    quote_cleaner = ['python', f'{current_path}/lib/remove_quotes.py']
    fix_includes = [f'{fixer_path}', '--noreorder']

    #Runs twice to fix include list once and a second time to catch bad includes
    if not all(run_cleaned_iwyu(iwyu_cmd, quote_cleaner, fix_includes) for _ in range(2)):
        return False

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
        Path.unlink(preprocess_file)

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''This script attempts to automatically refactor a
                                    include list without touching the headers themselves.''')

    parser.add_argument('-c', '--commands', type=Path, required=True,
                        help='Path to compile_commands.json')
    parser.add_argument('-f', '--fixer_path', type=Path,
                        help='Path to the fix_includes.py',
                        default=Path(Path(__file__).resolve().parent,
                                    'include-what-you-use/fix_includes.py'))
    parser.add_argument('-s', '--specific_command', required=True,
                        help='Name of the .c file to refactor')
    parser.add_argument('-fi', '--filters', nargs='*',
                        help='List of additional filters',
                        default=[])

    args = parser.parse_args()
    main(args.commands, args.fixer_path, args.filters, args.specific_command)
