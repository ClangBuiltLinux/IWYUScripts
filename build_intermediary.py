import json
import sys
import threading

from lib.utils import build

def execute_command(command, directory, semaphore):
    with semaphore:
        build(command, directory)

def main(commands, threads):
    with open(commands) as file:
        data = json.load(file)
        
        semaphore = threading.Semaphore(threads)
        
        threads = []
        for part in data:
            command = part['command'].split()
            command[-2] = command[-2][:-1] + 'i'
            command.append('-E')

            thread = threading.Thread(target=execute_command, args=(command, part["directory"], semaphore))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

if __name__ == '__main__':
    commands = sys.argv[1]

    threads = 1

    if len(sys.argv) > 2:
        threads = int(sys.argv[2])
    
    main(commands, threads)
