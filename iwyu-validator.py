import json
import subprocess
import os
import sys
def main(commands, specific):
    filename = f'prop_changes-{specific.replace("/", "")}.txt'
    with open (commands) as file:
        data = json.load(file)
        for part in data:
            if part["file"][-len(specific):] == specific:
                command = part['command'].split()
                command[-2] = command[-2][:-1] + 'i' # o to i file extension
                include = ["include-what-you-use", "-Xiwyu", "--no_default_mappings"]
                command = include + command[1:] + [f'2>{filename}']
                os.system(' '.join(command))

            remove_recommendations = []
            add_recommendations = []

    with open(filename) as file:
        first_add = file.readline()
        while "#include" not in first_add:
            first_add = file.readline()
        while "#include" in first_add:
            add_recommendations.append(first_add)
            first_add = file.readline()

        while "#include" not in first_add:
            first_add = file.readline()

        while "#include" in first_add:
            remove_recommendations.append(first_add)
            first_add = file.readline()

    suggest = []
    # TODO: all the numbers below are eyeballed, 5, 3, 4 are arbitrary 
    # and a better way of determinging architectures is necessary in the future
    for i in add_recommendations:
        incl, statement = i.split()[:2]
        statement = statement[1:-1]
        source, header = statement.split('/')
        if source == "asm-generic":
            res = str(subprocess.check_output(['find', '.', '-name', header]), 'UTF-8')
            
            if "asm-generic" in res and len(res.split('\n')) > 5:
                suggest.append('asm/' + header + ' PROBABLY OKAY')
            elif "asm-generic" in res and len(res.split('\n')) > 3:
                suggest.append('asm/' + header + ' PROBABLY BAD')

        elif source == "asm":
            res = str(subprocess.check_output(['find', '.', '-name', header]), 'UTF-8')
            # print(res.split('\n'))
            if len(res.split('\n')) > 4:
                suggest.append('asm/' + header + ' PROBABLY OKAY')
            else:
                suggest.append('asm/' + header + ' PROBABLY BAD')

        else:
            suggest.append(source + '/' + header)

    with open(filename, "a") as file:
        for suggestion in suggest:
            file.write(suggestion)
            file.write("\n")

if __name__ == '__main__':
    commands = sys.argv[1]
    specific_file = sys.argv[2]
    main(commands, specific_file)
