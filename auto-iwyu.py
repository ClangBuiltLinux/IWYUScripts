import json
import subprocess
import os
import sys
import shutil

def main(commands, specific, fixer_path):
    with open (commands) as file:
        data = json.load(file)
        for part in data:
            if part["file"][-len(specific):] != specific: continue
            perform_iwyu(fixer_path, part)

def perform_iwyu(fixer_path, part):
    command = part['command'].split()
    orig = command[-2]
    nname = orig[:-1] + 'i'
    backup_file_path = './' + orig[:-2] + '_backup.c'
    shutil.copy('./'+orig, backup_file_path)
    subprocess.run(["wc", "-l", f"./{nname}"])

    include = [
        "include-what-you-use",
        "-Xiwyu",
        "--no_default_mappings",
        "-Xiwyu",
        "--max_line_length=30",
        "-Xiwyu",
        "--mapping_file=./filter.imp"
    ]
    include_command = include + command[1:] + [f'2>&1 | {fixer_path}']
    # print(include_command)
    os.system(' '.join(include_command))

    command[-2] = nname
    build_command = command + ['-E']
    

    try:
        subprocess.run(' '.join(build_command), shell=True)
        subprocess.run(f"wc -l ./{nname} >> changes.txt", shell=True)

    except subprocess.CalledProcessError:
        shutil.copy(backup_file_path, './' + orig)

    os.remove(backup_file_path)

if __name__ == '__main__':
    commands = sys.argv[1]
    specific_file = sys.argv[2]
    fixer_path = sys.argv[3]
    main(commands, specific_file, fixer_path)
