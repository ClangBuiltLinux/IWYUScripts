# IWYUScripts
Miscellaneous scripts used to automated include-what-you-use on the linux kernel will be found here

Run in the kernal repository
```bash
make LLVM=1 defconfig all compile_commands.json -j 128
```
This should give the appropriate compile_commands.json. Use this to build the .i files for the compile commands:

```bash
python build_intermediary.py compile_commands.json
```

Replace with the acutual location of compile_commands.json




Once that is finished run

```bash
python single_iwyu.py compile_commands.json ~/include-what-you-use/fix_includes.py specific_file.c
```

Replace with the with the actual locations of compile_commands.json and fix_includes.py. 
Change specific_file.c to be the file you want to change.

To contribute to building out the symbol table run this and propose symbol mappings to symbol.imp or header mappings to filter.imp:

```bash
python auto-iwyu.py compile_commands.json ~/include-what-you-use/fix_includes.py
```
Update accordingly with the location of compile_commands.json and fix_includes.py.
