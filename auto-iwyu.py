import json
import subprocess
import os
import sys

def main(commands, specific, fixer_path):
    with open (commands) as file:
        data = json.load(file)
        for part in data:
            if part["file"][-len(specific):] != specific: continue
            command = part['command'].split()
            nname = command[-2][:-1] + 'i' # o to i file extension
            os.system("wc -l ./" + nname)
            include = ["include-what-you-use", "-Xiwyu", "--no_default_mappings", "-Xiwyu","--max_line_length=30", "-Xiwyu", "--mapping_file=./filter.imp"] #"-Xiwyu", "--verbose=7"
            include_command = include + command[1:] + [f'2>&1 | {fixer_path}']
            os.system(' '.join(include_command))
            command[-2] = nname
            build_command = command + ['-E']
            os.system(' '.join(build_command))
            os.system("wc -l ./" + nname)

if __name__ == '__main__':
    commands = sys.argv[1]
    specific_file = sys.argv[2]
    fixer_path = sys.argv[3]
    main(commands, specific_file, fixer_path)
