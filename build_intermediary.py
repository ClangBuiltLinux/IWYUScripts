import json
import subprocess
import os
import sys

def main(commands):
    with open (commands) as file:
        data = json.load(file)  
        for part in data:
            command = part['command'].split()
            command[-2] = command[-2][:-1] + 'i'
            command.append('-E')
            try:
                os.chdir(part["directory"])
                subprocess.check_call(' '.join(command), shell=True)
            except KeyboardInterrupt:
                print("Keyboard Interrupt occurred.")
                break
            except:
                print("Unkown Error")
                break

if __name__ == '__main__':
    commands = sys.argv[1]
    main(commands)
