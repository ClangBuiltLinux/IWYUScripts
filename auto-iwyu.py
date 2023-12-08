import argparse
import json
from pathlib import Path

from lib.utils import perform_iwyu

def main(commands, fixer_path, filters):
    current_dir = Path(__file__).resolve().parent
    filters += [Path(current_dir, 'filter.imp'), Path(current_dir, 'symbol.imp')]

    with open (commands, encoding='utf-8') as file:
        data = json.load(file)
        count = 0
        for part in data:
            count += 1
            print(count)
            if not perform_iwyu(fixer_path, part, filters, current_dir):
                return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''This script attempts to refactor multiple
                                    include lists without touching the headers themselves.''')

    parser.add_argument('-c', '--commands', type=Path, help='Path to compile_commands.json')
    parser.add_argument('-f', '--fixer_path', type=Path,
                        help='Path to the fix_includes.py',
                        default=Path(Path(__file__).resolve().parent,
                                    'include-what-you-use/fix_includes.py'))
    parser.add_argument('-fi', '--filters', nargs='*',
                        help='List of additional filters',
                        default=[])
    args = parser.parse_args()

    main(args.commands, args.fixer_path, args.filters)
