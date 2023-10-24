import json
import subprocess
import os
import sys
import shutil

def main(commands, fixer_path, filter):
    with open (commands) as file:
        cursed = []
        data = json.load(file)
        dump = []
        count = 0
        for part in data:
            count +=1
            if any([badfile in part["file"] for badfile in cursed]): continue
            print(count)
            if len(dump) == 10:
                build_check()
                while dump:
                    os.remove(dump.pop())
            backup = perform_iwyu(fixer_path, part, filters)
            if backup:
                dump.append(backup)

def perform_iwyu(fixer_path, part, filters):
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
        "--no_fwd_decls",
        "-Xiwyu",
        "--prefix_header_includes=keep",
    ]
    for filter in filters:
        include.append("-Xiwyu")
        include.append(f"--mapping_file={filter}")
    include_command = include + command[1:] + [f'2>&1 | {fixer_path}']

    #two passes

    os.system(' '.join(include_command))

    os.system(' '.join(include_command))

    command[-2] = nname
    build_command = command + ['-E']
    subprocess.check_call(' '.join(build_command), shell=True)
    try:
        output = subprocess.check_output(f"wc -l ./{nname}", shell=True)
        new_size = int(output.decode().strip().split()[0])
        if new_size >= old_size:
            print(new_size, old_size)
            raise ValueError
        subprocess.run(f"wc -l ./{nname} >> changes.txt", shell=True)

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
        subprocess.check_output("make ARCH=arm64 LLVM=1 -j 128 defconfig all", shell=True)
        print("arm64 works")
        subprocess.check_output("make ARCH=riscv LLVM=1 -j 128 defconfig all", shell=True)
        print("riscv works")
        
    except:
        exit()

if __name__ == '__main__':
    commands = sys.argv[1]
    fixer_path = sys.argv[2]
    filters = sys.argv[3:]
    main(commands, fixer_path, filters)
