import argparse
import json
from pathlib import Path
import threading
import itertools
from lib.utils import build, warn

def execute_command(command, directory, semaphore, file):
    with semaphore:
        print(f"BUILDING: {file}")
        build(command, directory)

def main(commands, threads, extension, additional_arg):
    with open(commands, encoding='utf-8') as file:
        data = json.load(file)

        semaphore = threading.Semaphore(threads)

        threads = []
        for part in data:
            command = part['command'].split()

            for i, statement in enumerate(itertools.islice(command, len(command) - 1)):
                if statement == '-o':
                    command[i+1] = str(Path(command[i + 1]).with_suffix(extension))
                    break
            else:
                warn(f"NO FILE FOUND IN COMMAND {part['file']}")
                return False

            command.append(additional_arg)

            thread = threading.Thread(target=execute_command,
                                      args=(command, part["directory"], semaphore, part["file"]))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='''This script automatically generates an extension
                                     for all files in compile_commands.json.''')

    parser.add_argument('-c', '--commands', type=Path, required=True,
                        help='Path to compile_commands.json')
    parser.add_argument('-j', '--threads', type=int,
                        help='Number of threads',
                        default=1)
    parser.add_argument('-e', '--extension', type=str,
                        help='File extension type .i, .ll, .s, or .bc',
                        default='.i')

    args = parser.parse_args()
    arg_mapping = {
        '.i': '-E',
        '.s': '-S',
        '.bc': '-emit-llvm',
        '.ll': '-emit-llvm -S',
    }
    main(args.commands, args.threads, args.extension, arg_mapping[args.extension])
