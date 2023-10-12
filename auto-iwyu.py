import json
import subprocess
import os
import sys
import shutil

def main(commands, specific, fixer_path):
    with open (commands) as file:
        cursed = ["vma.c", "setup.c", "nmi.c"]
        data = json.load(file)
        dump = []
        for part in data:
            if any([badfile in part["file"] for badfile in cursed]): continue
            if len(dump) == 5:
                build_check()
                while dump:
                    os.remove(dump.pop())
            backup = perform_iwyu(fixer_path, part)
            if backup:
                dump.append(backup)

def perform_iwyu(fixer_path, part):
    command = part['command'].split()
    orig = command[-1]
    nname = orig[:-1] + 'i'
    backup_file_path = './' + orig[:-2] + '_backup.c'

    try:
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        old_size = int(output.decode().strip().split()[0])
    except: #this has already been tried
        return
    
    orig_path = './' + orig
    shutil.copy(orig_path, backup_file_path)

    include = [
        "include-what-you-use",
        "-Xiwyu",
        "--no_default_mappings",
        "-Xiwyu",
        "--max_line_length=30",
        "-Xiwyu",
        "--mapping_file=./filter.imp",
        "-Xiwyu",
        "--no_fwd_decls"
    ]
    include_command = include + command[1:] + [f'2>&1 | {fixer_path}']
    # print(include_command)
    os.system(' '.join(include_command))

    command[-2] = nname
    build_command = command + ['-E']
    # print(part)
    try:
        subprocess.check_call(' '.join(build_command), shell=True)
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        new_size = int(output.decode().strip().split()[0])
        if new_size >= old_size:
            print(new_size, old_size)
            raise ValueError
        subprocess.run(f"wc -l ./{nname} >> changes.txt", shell=True)
        # subprocess.run(f"rm ./{nname}")
        # subprocess.run("echo ??? >> changes.txt", shell=True)

    except:
        shutil.copy(backup_file_path, orig_path)
        subprocess.run(f"rm ./{nname}", shell=True)
        subprocess.run(f"rm ./{backup_file_path}", shell=True)
        subprocess.run(f"echo 'copying {backup_file_path} to {orig_path} due to bugs' >> change_bugs.txt", shell=True)
        return

    return backup_file_path

def build_check():
    try:
        subprocess.check_output("make ARCH=arm LLVM=1 -j 128 defconfig all", shell=True)
        print("arm works")
        subprocess.check_output("make LLVM=1 -j 128 defconfig all", shell=True)
        print("x86 works")
        # subprocess.check_output("make ARCH=arm64 LLVM=1 -j 128 defconfig all", shell=True)
        # print("arm64 works")
        # subprocess.check_output("make ARCH=riscv LLVM=1 -j 128 defconfig all", shell=True)
        # print("riscv works")
        
    except:
        exit()

if __name__ == '__main__':
    commands = sys.argv[1]
    specific_file = sys.argv[2]
    fixer_path = sys.argv[3]
    main(commands, specific_file, fixer_path)
