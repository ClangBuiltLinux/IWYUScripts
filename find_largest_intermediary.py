import json
import subprocess
import os
import sys

def main(commands, output, expansion):
    sizes = []
    with open (commands) as file:
        data = json.load(file)
        for part in data:
            filename = part["file"][:-1] + 'i'
            res = int(str(subprocess.check_output(['wc', filename]), 'UTF-8').strip().split()[0])
            
            if expansion:
                res = res//int(str(subprocess.check_output(['wc', part["file"]]), 'UTF-8').strip().split()[0])
            
            sizes.append((res, filename))
            
    sizes.sort(reverse=True)
    with open(output, 'w') as outfile:
        for i in sizes:
            outfile.write(str(i))
            outfile.write("\n")



if __name__ == '__main__':
    commands = sys.argv[1]
    output = sys.argv[2]
    expand = False
    for i in range(2, len(sys.argv)):
        match sys.argv[i]:
            case "-m":
                expand = True
    main(commands, output, expand)
