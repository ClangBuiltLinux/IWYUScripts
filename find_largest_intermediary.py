import argparse
import json
import subprocess
from pathlib import Path

def main(commands, output, expansion):
    sizes = []
    with open (commands) as file:
        data = json.load(file)
        for part in data:
            filename = Path(part["file"]).with_suffix('.i')
            res = int(str(subprocess.check_output(['wc', str(filename)]), 'UTF-8').strip().split()[0])
            
            if expansion:
                res = res//int(str(subprocess.check_output(['wc', part["file"]]), 'UTF-8').strip().split()[0])
            
            sizes.append((res, filename))
            
    sizes.sort(reverse=True)
    with open(output, 'w') as outfile:
        for i in sizes:
            outfile.write(str(i))
            outfile.write("\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''This script attempts to refactor multiple
                                    include lists without touching the headers themselves.''')

    parser.add_argument('-c', '--commands', type=Path, help='Path to compile_commands.json')
    parser.add_argument('-o', '--output', type=Path, help='Path to output text file')
    parser.add_argument('-e', action='store_true',
                        help='Calculate size increase instead of total size.')
    args = parser.parse_args()
    main(args.commands, args.output, args.e)
